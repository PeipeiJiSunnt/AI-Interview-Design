# Validation status — 2026-11-07

- Python 3.13.7, Streamlit 1.67.0, OpenAI SDK 2.54.0.
- `python -m unittest -v test_engine`: 11 tests passed.
- `.venv\Scripts\python.exe -m unittest -v test_app`: 3 tests passed, including B/C × Yes/No combinations.
- UI tests use Streamlit AppTest with a fake backend. They required local loopback access outside the restricted execution sandbox.
- Compilation checked for app, engine, and test modules.
- Real OpenAI requests: NOT performed. No API key supplied to this work.
- GitHub access: rechecked successfully after repository authorization; read and push permissions confirmed. This report accompanies the source upload.
- Streamlit Cloud deployment: NOT performed.
- Old Library ZIP: not recovered; implementation rebuilt from the user's confirmed protocol.

Passing offline tests does not establish model accuracy, bias reduction, real API compatibility, or a deployed application.

## 2026-11-08 diagnostic update

The user supplied a screenshot of the deployed UI reaching the first dynamic follow-up and displaying a generic error. Deployment has therefore been observed through that screenshot. No successful live response or precise failure cause has yet been verified. This update adds safe diagnostic categories and makes retries explicit, while preserving cached C candidates. API key, billing, model access, and returned format must be distinguished using actual diagnostic evidence.
