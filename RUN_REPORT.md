# Prototype run report

Validated on 2026-11-07 using Python 3, Streamlit 1.67.0, OpenAI SDK 2.54.0.

Passed syntax compilation and full B/C demo interviews for both AI users and non-users.
Passed a full 13-answer Streamlit AppTest interview, completion view, and JSON/CSV export controls.
Verified the two-follow-up limit, non-user question routing, SKIP routing, and reuse of the original B candidate when retrying a failed C request with simulated model responses.
Started the Streamlit server on port 8501 and received a successful health response.

No OpenAI API key was supplied. Live B generation and C structured review require the deployer's API key and remain unverified against the live service. Demo content is labeled and must not be used as experimental results.

Design choices for this first version: no follow-ups on the demographic background question; participant explicitly selects AI-user status; condition selected manually; same configured model in two separate calls for generation and review; full prior conversation supplied; session-only records downloaded by participants.
