# Your Perspectives on AI in Education

Streamlit implementation of the Georgetown Dialogue Systems course interview.
Rebuilt from the confirmed protocol on 2026-11-07; the earlier Library ZIP was not available locally.
The existing Sites page remains a separate static mockup.

## Protocol

- Automated conditions B and C only. A remains a researcher-led human interview using the same outline; this app does not simulate a human interviewer.
- Background: major, degree program, year; no follow-ups.
- Usage: one Yes/No question, followed by the appropriate fixed tools/frequency or non-use-reasons branch. Only then start dynamic follow-ups.
- Specific usage and influence are asked only of AI users. Overall attitude is asked of everyone.
- Zero to two dynamic follow-ups per topic, one at a time. After the first answer, call the generator again. SKIP advances immediately.
- B's confirmed prompt is preserved in `engine.B_PROMPT`. B and C use the same generator pipeline. The fixed usage branch is included in the core context.
- C makes a separate stateless API call to check unsupported presupposition and leading wording. KEEP displays the exact original. REWRITE displays the rewrite. SKIP advances. Failed checker calls retain the same candidate and record each attempt.
- The checker prompt and JSON format are this implementation's operational specification, not human reference labels. Review and freeze them before data collection.

## Run locally

Use Python 3.12 or 3.13:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit the ignored secrets.toml locally; never commit it.
.venv\Scripts\python -m streamlit run app.py
```

## Deploy to Streamlit Community Cloud

1. Upload these project files to `PeipeiJiSunnt/AI-Interview-Design`. Include `.streamlit/secrets.toml.example`, never the real `secrets.toml` or interview data.
2. At https://share.streamlit.io choose Create app and select the repository, actual branch, and entrypoint `app.py`.
3. In Advanced settings choose Python 3.13 (the local validation version), and paste the example TOML into Secrets. Replace only the placeholder key there.
4. Set `INTERVIEW_CONDITION = "B"` or `"C"`. Deploy separate apps with separate Secrets for B and C; participants do not select their condition in the UI. Keep generator/checker models fixed throughout a study batch.
5. Deploy. For later changes use the app settings to update Secrets.

```toml
OPENAI_API_KEY = "YOUR_KEY_IN_STREAMLIT_ONLY"
OPENAI_MODEL = "gpt-5.4-mini-2026-03-17"
CHECKER_MODEL = "gpt-5.4-mini-2026-03-17"
INTERVIEW_CONDITION = "C"
```

Model decision: the official GPT-5 Mini page marked the old model deprecated when checked on 2026-11-07. This version explicitly switches to the documented GPT-5.4 Mini snapshot above. This is a configurable implementation choice, not a claim of account availability or a silent automatic fallback. An unavailable model produces an error. No API key is embedded, exported, or entered through the participant UI.

## Verification: distinguish offline tests from real calls

```powershell
python -m unittest -v test_engine
python -m unittest -v test_app
```

These use fake model outputs and establish state-machine/UI behavior only. They do not validate question quality, checker accuracy, or real API compatibility.

The failure view shows a safe diagnostic code rather than the raw exception, which may contain credentials. `AUTHENTICATION_FAILED` means check Secrets; `QUOTA_EXCEEDED` means check API billing/limits; `RATE_LIMITED` means wait; `MODEL_OR_RESOURCE_UNAVAILABLE` means check the configured model and project access; `MODEL_OUTPUT_INVALID` means an incomplete response or malformed checker result. Failure does not establish which cause applies until the diagnostic is observed. After a failure, only the explicit Retry button initiates another call; downloading or expanding UI does not retry. Use `python -m unittest -v test_diagnostics` to test the error mapping and redaction offline.

After deployment, complete one Yes interview and one No interview in each condition with synthetic answers. Download JSON and check:

- `mode` is `live`; `calls` contains completed generator responses with response IDs, returned models and usage.
- B has no checker calls; C has completed separate checker calls for every displayed follow-up.
- C's audit contains original candidate, attempts, final decision, rewrite, and displayed question. KEEP matches verbatim.
- Non-users never receive specific usage/influence questions; fixed branches do not consume the two-follow-up allowance.
- Download works before and after completion. Confirmed Start over clears the session.

Only after those actual calls succeed should real API verification be recorded as passed. Raw model output and call metadata are preserved in full JSON, but model audit judgments are not shown in the conversation. Calls use `store=False`; this does not make claims about provider retention policies.

## Records and evaluation

No database or central collection exists. Session state can be lost on refresh/disconnection/restart. Participants must download and send records to the researcher. JSON is authoritative and includes protocol/prompts/models, conversation, audit, timestamps, call usage, and errors by type. CSV contains conversation only and neutralizes spreadsheet formulas. Do not publish downloaded research records to this repo.

An optional `ACCESS_CODE` in Secrets preserves the earlier prototype's shared study gate. It is not exported. This revised participant app has no demo toggle or participant-facing condition selector; offline simulation is in the test suite.

For human annotation, prepare context + question items for two independent raters, with condition, checker output, and source hidden. Include A's human follow-ups. Label each bias dimension separately; report raw agreement and Cohen's kappa before discussing disagreements to produce reference labels. Preserve the independent labels. Randomize item order and do not show before/after pairs together. C's labels are model outputs, never gold labels. Candidate/rewrite comparisons at the same context measure wording changes; actual downstream answer effects need another experiment.

## Official references checked

- https://developers.openai.com/api/docs/models/gpt-5-mini
- https://developers.openai.com/api/docs/models/gpt-5.4-mini
- https://developers.openai.com/api/docs/quickstart
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
