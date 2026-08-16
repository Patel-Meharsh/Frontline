# FRONTLINE — One-Day AI Build Challenge

A triage system that reads raw, messy customer messages and turns each one into a
structured decision: `{category, priority, summary, suggested_action, needs_human, confidence}`.

## 1. Get a free API key (2 minutes)

1. Go to https://console.groq.com and sign up (no credit card required).
2. Create an API key.
3. In your terminal:
   ```bash
   export GROQ_API_KEY=your_key_here
   ```

Groq's free tier runs Llama 3.3 70B fast and at no cost — well within the limits of a
40-message demo.

## 2. Install & run

```bash
pip install -r requirements.txt

# Run triage on the full 40-message dataset
python triage.py

# Evaluate against the 10 hand-labeled ground-truth messages
python eval.py

# Build the demo dashboard (opens directly in a browser, no server needed)
python dashboard_generator.py
open dashboard.html   # or just double-click it
```

## 3. What's in here

| File | Purpose |
|---|---|
| `data/messages.json` | The 40-message messy dataset (clear, vague, angry, sarcastic, multi-issue, non-English, garbage input, prompt-injection attempts) |
| `data/ground_truth.json` | 10 hand-labeled messages used for Level 3 evaluation |
| `triage.py` | Core engine: calls the model, validates/repairs JSON, retries on failure, never crashes, fails safe to `needs_human=true` |
| `eval.py` | Compares `results.json` against ground truth, reports agreement %, shows exactly where it disagrees, reports tokens/latency |
| `dashboard_generator.py` | Builds a single self-contained `dashboard.html` from `results.json` |
| `results.sample.json` / `dashboard.sample.html` | A pre-generated example run (simulated, for reference) so you can see the shape of the output before you've added your own key |
| `AI_DECISIONS.md` | The one-page submission note |

## 4. Design notes (short version — see AI_DECISIONS.md for the full note)

- **Guardrails against prompt injection**: the system prompt explicitly tells the model that
  message content is data, not instructions, and the dataset includes messages that try to
  hijack the output (`m12`, `m21`, `m31`) to prove it holds.
- **Never invents details**: the prompt forbids fabricating order numbers, names, etc. not
  present in the message.
- **Fails safe, never crashes**: malformed JSON triggers up to 2 retries; if all retries fail,
  the message is still emitted with `needs_human=true` and `confidence=0.0` instead of
  crashing the pipeline.
- **Uncertainty routing**: ambiguous, legal, security, financial-hardship, or emotionally
  loaded messages are instructed to set `needs_human=true` and lower `confidence`, rather
  than guess.
