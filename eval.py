#!/usr/bin/env python3
"""
Evaluate a Frontline run against the hand-labelled reference set.

The reference labels score category, priority and human escalation. Optional
summary_must_mention/action_must_mention keyword rubrics check coverage of the
human-authored reference expectations; they are not semantic truth detectors.
"""
import argparse
import json
import sys


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise ValueError("File not found: " + path)
    except json.JSONDecodeError as exc:
        raise ValueError("{} is not valid JSON (line {}, column {}).".format(path, exc.lineno, exc.colno))


def pct(numerator, denominator):
    return "{}/{} ({:.1f}%)".format(numerator, denominator, 100.0 * numerator / denominator) if denominator else "n/a (0 labelled examples)"


def text_value(value):
    return value.strip().lower() if isinstance(value, str) else ""


def keyword_coverage(value, required):
    """All required terms are simple case-insensitive substrings; no semantic claim."""
    if not required:
        return None, []
    normalized = text_value(value)
    missing = [term for term in required if text_value(term) not in normalized]
    return len(required) - len(missing), missing


def main():
    parser = argparse.ArgumentParser(description="Evaluate Frontline results against labelled examples.")
    parser.add_argument("--results", default="results.json")
    parser.add_argument("--truth", default="data/ground_truth.json")
    args = parser.parse_args()

    try:
        results_data = load_json(args.results)
        truth_data = load_json(args.truth)
    except ValueError as exc:
        print("EVALUATION ERROR: " + str(exc), file=sys.stderr)
        return 2

    if not isinstance(results_data, dict) or not isinstance(results_data.get("results"), list):
        print("EVALUATION ERROR: results file must contain a 'results' array.", file=sys.stderr)
        return 2
    if not isinstance(truth_data, list):
        print("EVALUATION ERROR: ground truth must be a JSON array.", file=sys.stderr)
        return 2

    results_by_id = {}
    malformed_results = []
    for index, row in enumerate(results_data["results"], 1):
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not isinstance(row.get("decision"), dict):
            malformed_results.append(index)
            continue
        if row["id"] in results_by_id:
            malformed_results.append(index)
            continue
        results_by_id[row["id"]] = row

    truth_by_id = {}
    for row in truth_data:
        if isinstance(row, dict) and isinstance(row.get("id"), str):
            truth_by_id[row["id"]] = row
    if not truth_by_id:
        print("EVALUATION ERROR: no valid labelled examples found.", file=sys.stderr)
        return 2

    counts = {"category": 0, "priority": 0, "needs_human": 0, "exact": 0}
    summary_checks = {"checked": 0, "passed": 0, "missing": []}
    action_checks = {"checked": 0, "passed": 0, "missing": []}
    missing_ids = []
    mismatches = []

    for message_id, truth in truth_by_id.items():
        row = results_by_id.get(message_id)
        if row is None:
            missing_ids.append(message_id)
            continue
        decision = row["decision"]
        category_ok = decision.get("category") == truth.get("category")
        priority_ok = decision.get("priority") == truth.get("priority")
        human_ok = decision.get("needs_human") == truth.get("needs_human")
        counts["category"] += int(category_ok)
        counts["priority"] += int(priority_ok)
        counts["needs_human"] += int(human_ok)
        counts["exact"] += int(category_ok and priority_ok and human_ok)
        if not (category_ok and priority_ok and human_ok):
            mismatches.append((message_id, truth, decision))

        for rubric_key, field, bucket in (
            ("summary_must_mention", "summary", summary_checks),
            ("action_must_mention", "suggested_action", action_checks),
        ):
            required = truth.get(rubric_key, [])
            if required:
                found, missing = keyword_coverage(decision.get(field), required)
                bucket["checked"] += 1
                bucket["passed"] += int(not missing)
                if missing:
                    bucket["missing"].append((message_id, missing))

    total = len(truth_by_id)
    print("FRONTLINE EVALUATION")
    print("Labelled examples: {} | Matched results: {} | Missing: {}".format(total, total-len(missing_ids), len(missing_ids)))
    print("Category agreement:     " + pct(counts["category"], total-len(missing_ids)))
    print("Priority agreement:     " + pct(counts["priority"], total-len(missing_ids)))
    print("needs_human agreement:  " + pct(counts["needs_human"], total-len(missing_ids)))
    print("Exact match (3 fields): " + pct(counts["exact"], total-len(missing_ids)))
    print("\nSUMMARY / ACTION QUALITY RUBRIC")
    print("Summary keyword coverage: " + pct(summary_checks["passed"], summary_checks["checked"]))
    print("Suggested-action keyword coverage: " + pct(action_checks["passed"], action_checks["checked"]))
    print("Note: keyword coverage is a transparent checklist, not a semantic or hallucination detector.")

    if mismatches:
        print("\nCLASSIFICATION DISAGREEMENTS")
        for message_id, truth, decision in mismatches:
            print("[{}] expected category/priority/human: {}/{}/{}; got: {}/{}/{}".format(
                message_id, truth.get("category"), truth.get("priority"), truth.get("needs_human"),
                decision.get("category"), decision.get("priority"), decision.get("needs_human")))
            if truth.get("note"):
                print("  Reference rationale: " + str(truth["note"]))
    for label, bucket in (("summary", summary_checks), ("action", action_checks)):
        for message_id, missing in bucket["missing"]:
            print("{} rubric [{:s}] missing terms: {}".format(label, message_id, ", ".join(missing)))
    if missing_ids:
        print("\nMissing labelled IDs: " + ", ".join(missing_ids))
    if malformed_results:
        print("Malformed/duplicate result rows at positions: " + ", ".join(map(str, malformed_results)))

    all_rows = results_data["results"]
    usable_meta = [row.get("meta", {}) for row in all_rows if isinstance(row, dict) and isinstance(row.get("meta"), dict)]
    total_tokens = sum(meta.get("tokens", 0) for meta in usable_meta if isinstance(meta.get("tokens", 0), (int, float)))
    latencies = [meta.get("latency_sec", 0) for meta in usable_meta if isinstance(meta.get("latency_sec", 0), (int, float))]
    fallback_count = sum(meta.get("route") == "fallback" for meta in usable_meta)
    human_count = sum(isinstance(row, dict) and isinstance(row.get("decision"), dict) and row["decision"].get("needs_human") is True for row in all_rows)
    print("\nRUN HEALTH")
    print("Results: {} | Human review: {} | Fallback routes: {}".format(len(all_rows), human_count, fallback_count))
    print("Total tokens: {} | Average tokens/result: {}".format(total_tokens, round(total_tokens / len(all_rows)) if all_rows else "n/a"))
    print("Average measured latency: {:.3f}s/result".format(sum(latencies) / len(latencies) if latencies else 0.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
