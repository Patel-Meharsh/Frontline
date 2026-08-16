#!/usr/bin/env python3
"""
Evaluate triage results.json against data/ground_truth.json.
Reports agreement rate on category, priority, and needs_human, plus where it fails.

Usage:
    python eval.py
    python eval.py --results results.json --truth data/ground_truth.json
"""

import json
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results.json")
    parser.add_argument("--truth", default="data/ground_truth.json")
    args = parser.parse_args()

    with open(args.results, "r", encoding="utf-8") as f:
        results_data = json.load(f)
    with open(args.truth, "r", encoding="utf-8") as f:
        truth_data = json.load(f)

    results_by_id = {r["id"]: r for r in results_data["results"]}
    truth_by_id = {t["id"]: t for t in truth_data}

    total = 0
    category_match = 0
    priority_match = 0
    human_match = 0
    all_three_match = 0
    mismatches = []

    for tid, truth in truth_by_id.items():
        if tid not in results_by_id:
            print(f"WARNING: {tid} missing from results, skipping")
            continue
        total += 1
        decision = results_by_id[tid]["decision"]

        cat_ok = decision["category"] == truth["category"]
        pri_ok = decision["priority"] == truth["priority"]
        human_ok = decision["needs_human"] == truth["needs_human"]

        category_match += cat_ok
        priority_match += pri_ok
        human_match += human_ok
        if cat_ok and pri_ok and human_ok:
            all_three_match += 1
        else:
            mismatches.append({
                "id": tid,
                "text": results_by_id[tid]["input_text"][:80],
                "expected": {"category": truth["category"], "priority": truth["priority"], "needs_human": truth["needs_human"]},
                "got": {"category": decision["category"], "priority": decision["priority"], "needs_human": decision["needs_human"]},
                "note": truth.get("note", ""),
            })

    print(f"Evaluated {total} hand-labeled messages\n")
    print(f"Category agreement:     {category_match}/{total} ({100*category_match/total:.0f}%)")
    print(f"Priority agreement:     {priority_match}/{total} ({100*priority_match/total:.0f}%)")
    print(f"needs_human agreement:  {human_match}/{total} ({100*human_match/total:.0f}%)")
    print(f"Exact match (all 3):    {all_three_match}/{total} ({100*all_three_match/total:.0f}%)")

    if mismatches:
        print(f"\n--- Where it fails ({len(mismatches)}) ---")
        for m in mismatches:
            print(f"\n[{m['id']}] \"{m['text']}...\"")
            print(f"  expected: {m['expected']}")
            print(f"  got:      {m['got']}")
            print(f"  why it matters: {m['note']}")

    # cost / latency summary
    all_results = results_data["results"]
    total_tokens = sum(r["meta"]["tokens"] for r in all_results)
    total_time = sum(r["meta"]["latency_sec"] for r in all_results)
    n = len(all_results)
    print(f"\n--- Cost / latency (full {n}-message run) ---")
    print(f"Avg tokens/message: {total_tokens/n:.0f}")
    print(f"Avg latency/message: {total_time/n:.2f}s")
    print(f"Total tokens: {total_tokens} (Groq free tier: $0 - well within free limits)")
    print(f"Cost-cutting idea: batch similar short messages into one prompt call, or route")
    print(f"obviously-simple P2/P3 messages to a smaller/faster model and reserve the")
    print(f"current model only for ambiguous or flagged cases.")


if __name__ == "__main__":
    main()
