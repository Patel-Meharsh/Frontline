# FRONTLINE — One-Day AI Build Challenge

Frontline converts messy customer messages into structured triage decisions:

`{category, priority, summary, suggested_action, needs_human, confidence}`.

It uses Python and the Groq-hosted Llama 3.3 70B model through the OpenAI-compatible SDK. Clear empty messages, obvious gibberish and instruction-manipulation attempts are handled by local safeguards; other messages are sent to the model and validated before being accepted.

## 1. Setup

1. Create a Groq API key at https://console.groq.com.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set the key in your terminal.

   **Windows PowerShell**
   ```powershell
   $env:GROQ_API_KEY="your_api_key"
   ```

   **Git Bash / macOS / Linux**
   ```bash
   export GROQ_API_KEY="your_api_key"
   ```

Do not commit your API key to the repository.

## 2. Run the complete workflow

```bash
python triage.py
python eval.py
python dashboard_generator.py
```

Open `dashboard.html` in a browser. The dashboard reads `results.json` and works without a web server.

Useful options:

```bash
python triage.py --input data/messages.json --output results.json --limit 5
python eval.py --results results.json --truth data/ground_truth.json
python dashboard_generator.py --results results.json --output dashboard.html
```

The triage command processes locally handled empty/injection messages without an API request. Other valid messages require `GROQ_API_KEY`.

## 3. Reliability safeguards

- **Input validation:** checks the JSON root, row shape, IDs, duplicate IDs, message type and maximum message length. Obvious keyboard-mash text is conservatively caught by a simple heuristic. Invalid rows become explicit human-review fallback results; malformed JSON produces a clear CLI error.
- **Prompt-injection defence:** the customer text is treated as untrusted data in the system instructions. A conservative local pattern guard intercepts clear instruction-manipulation phrases. This is defence in depth, not a guarantee against every possible attack.
- **High-risk escalation:** security/privacy, legal, financial-hardship and selected distress indicators force human review; the model cannot turn these flags off.
- **Strict output validation:** requires exactly the six schema fields, allowed category/priority values, non-empty bounded strings, a real boolean and a numeric confidence between 0 and 1.
- **Confidence policy:** confidence below 0.65 forces `needs_human=true`. Model confidence is self-reported and is not a calibrated probability.
- **Retries and fallback:** malformed model output or API errors are retried up to two times after the first attempt. If all attempts fail, Frontline emits a P1, human-review fallback with confidence 0 rather than pretending the message was classified successfully.
- **No unsupported claims:** the prompt asks for summaries grounded in the message and suggested actions phrased as next steps, not completed actions. Human review is still needed to assess factual grounding.

## 4. Evaluation

`data/ground_truth.json` contains 10 hand-labelled reference messages. `eval.py` reports category, priority, human-review and exact three-field agreement.

The reference examples also include `summary_must_mention` and `action_must_mention` keyword checklists. These produce transparent summary/action coverage scores. They are lightweight rubric checks, not semantic correctness or hallucination detection; a human should review the actual wording.

The evaluator also reports missing labels, malformed result rows, token usage, latency and fallback counts. Only metrics from a real run of `python triage.py` should be presented as measured results. `results.sample.json` is a simulated demonstration fixture, not evidence of live model performance.

Run unit tests without a Groq key:

```bash
python -m unittest discover -s tests -v
```

## 5. Project files

| File | Purpose |
|---|---|
| `triage.py` | Input validation, local safeguards, model call, schema validation, escalation, retry and fallback |
| `eval.py` | Compares model decisions with hand labels and checks summary/action rubric coverage |
| `dashboard_generator.py` | Generates the self-contained interactive dashboard |
| `data/messages.json` | The 40-message challenge dataset |
| `data/ground_truth.json` | Ten hand-labelled examples and transparent text-quality rubrics |
| `tests/test_triage.py` | Offline unit tests for validation and safety behaviour |
| `AI_DECISIONS.md` | Model, guardrail, evaluation and limitation notes |
| `results.sample.json` | Simulated example output only; not a live evaluation |

## 6. Known limitations

- Regex-based prompt-injection and risk detection can miss paraphrases and can occasionally flag benign text. It is a guardrail, not a complete security boundary.
- A self-reported confidence value is not calibrated. The 0.65 threshold is a conservative routing rule, not a measured probability of correctness.
- Keyword rubrics do not establish semantic accuracy, factual grounding or whether an action is operationally appropriate.
- Ten labelled examples are a small evaluation sample. Expand the labelled set and have humans review summaries/actions before using this for real customer operations.
- The application proposes decisions only. It does not issue refunds, change accounts, contact customers or perform other support actions.
