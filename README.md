# Student AI interview

A Streamlit prototype for B and C semi-structured interviews. The interface and questions are in English.

## Deploy to Streamlit Community Cloud

1. Unzip this project. Create a GitHub repository and upload `app.py`, `engine.py`, `requirements.txt`, `.gitignore`, and this README. Keep the files together at the repository root.
2. Open https://share.streamlit.io and create an app from that repository. Set the main file to `app.py` and use Python 3.11 or 3.12.
3. Open Advanced settings and paste the contents of `secrets.example.toml` into Secrets. Replace the API-key placeholder, choose an access code, and keep `OPENAI_MODEL` set to a model your OpenAI project can access. The starting model is `gpt-5-mini`.
4. Deploy. Open the app, choose B or C, enter the access code, and uncheck Demo mode for real model calls.
5. Give participants the app URL and access code. Ask them to download the full JSON record after the interview and send it to you. The JSON includes C's original candidate and checker result. CSV contains the displayed transcript only.

The app can be deployed and explored in Demo mode without an API key. Demo questions are fixed placeholders, and all exports label them as simulated. A missing or invalid real API key does not cause a silent switch to demo.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

For real calls, create `.streamlit/secrets.toml` locally using the example, or set `OPENAI_API_KEY` in the environment. Do not commit real secrets.

## Interview design

Both conditions ask the same five core topics in the same order. Background has no follow-ups. Each subsequent topic permits zero to two follow-ups, asked one at a time. The full preceding interview, including actual displayed follow-ups and answers, is passed to the model. Follow-up functions are not predefined.

The participant reports AI use before starting. Participants selecting No receive background, usage/non-use reasons, and overall attitude. Experience and learning-influence questions are skipped. This routing choice is explicit rather than automatically inferred from a free-text answer.

B displays the generated question unless it is SKIP. C reviews that exact candidate for unsupported presuppositions and leading wording. KEEP preserves the exact wording, REWRITE changes the wording, and SKIP advances to the next topic. A rejected or skipped candidate is logged. A C retry reuses its cached B candidate.

Human condition A is conducted outside this app. Model checker flags in C are provisional model judgments. Establish human reference labels separately.

## Records and limitations

Records are kept in per-user Streamlit session state. Refreshing, disconnecting, or restarting the server can lose them. This version has no central database and does not collect downloads automatically. Download JSON during or after the interview and send it to the researcher. Export a partial record before closing if an API request fails.

JSON includes the condition, demo flag, requested and actual model IDs, prompts, transcript, original candidates, review decisions, usage, and timestamps. It does not include API keys or access codes. The same configured model is used for B and the C checker in separate requests. Changing models requires editing OPENAI_MODEL before a new session. Model availability depends on your API project.

Do not use the prototype participation text as a replacement for any course-approved consent wording. The access code is a shared study gate, not an individual account system. Condition selection is manual and visible, suitable for pilots. Freeze prompts/model and plan assignment before a formal study.

API errors leave the submitted answer saved and allow an explicit retry. There are no automatic retries of paid requests. A connection timeout can occur after a provider has processed a request, so manual retries can incur an additional charge.

## Validation

See the delivered run report for the executed checks. The prototype has been tested with simulated model responses. A live OpenAI request requires your API key and has not been verified in the build environment.
