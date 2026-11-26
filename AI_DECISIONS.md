# AI Decisions Note — FRONTLINE

## Goal and architecture

Frontline turns one raw customer message at a time into a structured support-triage decision:

`category`, `priority`, `summary`, `suggested_action`, `needs_human`, and `confidence`.

The implementation uses Python and the OpenAI Python SDK pointed at Groq's OpenAI-compatible API. The selected model is Llama 3.3 70B Versatile. A direct API call is intentionally used instead of an agent framework because the task is a single classification step, not a multi-tool workflow.

## Prompt and model settings

- Temperature is 0.1 to favour consistent classification over creative output.
- The system prompt defines the allowed category and priority values and requests exactly six JSON fields.
- Customer content is passed as untrusted data. Instructions embedded in a customer message must not override the classifier's system instructions.
- The model is told not to invent names, identifiers, causes, promises or completed actions.
- It is asked to summarise in English and to escalate ambiguous, legal, security/privacy, financial-hardship and distress-related cases.

Prompt instructions are not a security boundary by themselves. The implementation therefore combines them with deterministic local checks and post-response policy enforcement.

## Reliability and guardrails

### Input validation

`load_messages()` verifies that the input is a JSON list and checks each row's object shape, ID, uniqueness, text type and maximum length. Invalid rows are retained as explicit human-review fallback results instead of being passed to the model. Invalid JSON and an invalid top-level structure stop the run with a clear error.

### Local handling and escalation

- Empty/whitespace-only messages are handled locally as `other / P3`, human review required, confidence 0.
- Clear prompt-manipulation patterns are handled locally as `other / P3`, human review required. This prevents the model from receiving those known challenge examples as instructions.
- Security/privacy, legal, financial-hardship and selected distress patterns are enforced after the model response. The model cannot set `needs_human=false` for these matched cases.
- Pattern matching is conservative and incomplete: paraphrases can evade it and benign messages can match. It is defence in depth, not a guarantee.

### Output validation and confidence

`validate_decision()` requires exactly the six expected fields. It rejects missing/extra fields, unknown enum values, empty or oversized summary/action strings, wrong boolean types, string/boolean confidence values and confidence outside 0.0–1.0.

A valid model confidence below 0.65 forces `needs_human=true`. This is a routing threshold, not a calibrated probability: the confidence value is still self-reported by the model.

### Retry and fallback

Malformed or unusable responses and API exceptions are retried up to two times after the initial attempt. Backoff occurs only between attempts. If all attempts fail, Frontline emits an explicit `other / P1` fallback with human review required and confidence 0.0. The fallback makes the failure visible rather than presenting an uncertain result as an automatic decision.

## Evaluation strategy

The repository has 10 hand-labelled examples in `data/ground_truth.json`, selected from the 40-message challenge dataset. `eval.py` measures agreement for category, priority and `needs_human`, plus exact agreement across those three fields. It reports missing IDs, malformed/duplicate result rows, mismatches, token usage, latency and fallback counts.

The reference examples also carry `summary_must_mention` and `action_must_mention` keyword rubrics. The evaluator reports whether the generated summary and suggested action contain those required terms. This is deliberately described as keyword coverage only; it does not prove semantic correctness, factual grounding or absence of hallucinations. Human review remains necessary for those qualities.

**No live accuracy or latency result is asserted in this note.** Earlier sample metrics in the repository referred to a simulated `results.sample.json` fixture and must not be represented as a fresh measured model run. Run `python triage.py` followed by `python eval.py` to produce current evidence, and record the actual terminal output when available.

## Tests

Offline unit tests in `tests/test_triage.py` cover schema validation, confidence escalation, JSON extraction, empty and injection handling, risk escalation, fail-safe fallback, malformed input rows and invalid JSON. Run them with:

```bash
python -m unittest discover -s tests -v
```

These tests exercise local logic without a Groq API key. They do not replace an end-to-end live run against the challenge dataset.

## Limitations and next steps

- Expand the labelled set beyond 10 examples and review labels independently.
- Have human reviewers score summary faithfulness and suggested-action appropriateness; keyword checks are only a first lightweight rubric.
- Measure confidence calibration against labelled outcomes before treating confidence as a probability.
- Expand adversarial tests with paraphrases, encoding tricks and indirect prompt injection.
- Consider a feedback workflow for recording human corrections.
- Keep the system as decision support: it does not execute refunds, account changes, messages or other customer operations.
