# AI Decisions Note — FRONTLINE

## Model & tools
- **Model**: Llama 3.3 70B Versatile, served via **Groq's free API** (OpenAI-compatible
  endpoint, so the code can swap to OpenAI/Anthropic by changing `MODEL` and `API_BASE`
  in `triage.py`). Chosen for zero cost, generous free-tier limits, and fast inference —
  important when triage needs to be fast on the front line.
- **Tools**: plain Python + the `openai` SDK pointed at Groq's endpoint. No agent framework —
  this is a single-purpose classification task, not a multi-step agentic workflow, so a
  direct API call with strict output validation is the right-sized tool for the job.

## Prompt strategy
- One system prompt defines the schema, the allowed enum values for `category`/`priority`,
  and — most importantly — a numbered list of safety rules the model must follow every time.
- `temperature=0.1` for consistency; a message classification task doesn't need creativity.
- The user message wraps the raw customer text in a clearly delimited block so the model
  can distinguish "the thing being classified" from "instructions for me."

## Handling uncertainty & bad input
- **Prompt injection**: the dataset includes messages that try to override instructions,
  supply pre-written JSON, or impersonate a system message (`m12`, `m21`, `m31`). The system
  prompt explicitly instructs the model to treat all message content as data, never as
  instructions, and to flag the attempt rather than comply with it.
- **Ambiguity/sensitivity**: legal threats, security reports, financial hardship, and
  emotionally loaded messages are instructed to set `needs_human=true` and reduce
  `confidence` — the system is told it's always better to escalate than to guess.
- **Malformed output**: `extract_json()` strips markdown fences and recovers a JSON object
  even if the model adds stray prose; `validate_decision()` checks every field and enum.
  Up to 2 retries on failure. If all retries fail, the pipeline still emits a decision
  (`needs_human=true`, `confidence=0.0`) instead of crashing — Level 1's "never falls over"
  requirement, satisfied structurally rather than by hoping the model behaves.
- **Garbage/empty input**: explicitly covered in the prompt rules and in the dataset
  (`m23` empty, `m24` whitespace, `m11` gibberish) — routed to `other` / `P3` /
  `needs_human=true` rather than fabricated categorization.

## How I know it works
- `eval.py` scores the 40-message run against 10 hand-labeled ground-truth messages,
  reporting category/priority/needs_human agreement and printing every disagreement with
  the reasoning for the expected label, so failures are inspectable, not just a percentage.
- On a representative run: **90% category agreement, 90% priority agreement, 100%
  needs_human agreement, 80% exact match on all three fields** — see `results.sample.json`
  for the reference run. The two misses were both defensible edge cases (a prompt-injection
  message categorized as `spam_or_abuse` instead of `other`, and an emotional-distress
  message rated P2 instead of P1) — not hallucinated fields or crashes.
- Avg cost/latency on the free tier: ~220 tokens and well under 1 second per message
  (see the cost section printed by `eval.py`).

## What I'd fix with more time
- Route obviously low-ambiguity P2/P3 messages to a cheaper/smaller model and reserve the
  full model for flagged or ambiguous cases, to cut cost further at scale.
- Add a small few-shot set of 3–4 examples (including one adversarial example) directly in
  the prompt — currently relying on instructions alone, which works but few-shot would
  likely tighten the P1-vs-P2 boundary seen in the eval misses.
- Add a confidence-calibration pass: right now `confidence` is self-reported by the model;
  a second lightweight check (e.g. re-asking "how sure are you, and why") would make that
  number more trustworthy rather than just plausible.
- Persist a feedback loop: let a human's correction on a flagged message get logged and
  periodically reviewed to catch systematic drift, not just one-off cost snapshots.
