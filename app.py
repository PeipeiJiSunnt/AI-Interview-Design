import json
import hmac
import os
import streamlit as st
from engine import Interview, OpenAIBackend, TITLE, INTRO, DEFAULT_MODEL, safe_diagnostic

st.set_page_config(page_title=TITLE, page_icon="💬", layout="centered")


def setting(name, default=""):
    try:
        return st.secrets.get(name, os.getenv(name, default))
    except FileNotFoundError:
        return os.getenv(name, default)


st.title(TITLE)
st.write(INTRO)
st.caption("Please avoid names or other identifying details. Responses are sent to OpenAI to generate interview questions. "
           "Records stay in this browser session; refreshing may lose them. Download your record and send it to the researcher.")

condition = str(setting("INTERVIEW_CONDITION", "C")).upper()
model = str(setting("OPENAI_MODEL", DEFAULT_MODEL))
checker_model = str(setting("CHECKER_MODEL", model))
api_key = setting("OPENAI_API_KEY")
access_code = str(setting("ACCESS_CODE"))

if condition not in {"B", "C"}:
    st.error("The researcher must configure INTERVIEW_CONDITION as B or C.")
    st.stop()

if "interview" not in st.session_state:
    st.session_state.interview = None
if st.session_state.interview is None:
    entered_code = st.text_input("Study access code", type="password") if access_code else ""
    consent = st.checkbox("I agree to participate and to have my responses processed as described above.")
    if st.button("Start interview", disabled=not consent):
        if access_code and not hmac.compare_digest(entered_code, access_code):
            st.error("The study access code is incorrect.")
        elif not api_key:
            st.error("The researcher must configure the OpenAI API connection before this interview can start.")
        else:
            st.session_state.interview = Interview(condition=condition, model=model, checker_model=checker_model)
            st.rerun()
    st.stop()

session = st.session_state.interview
for message in session.messages:
    with st.chat_message("assistant" if message["role"] == "interviewer" else "user"):
        st.write(message["text"])

if session.stage == "decide":
    if not st.session_state.get("request_error"):
        with st.spinner("Preparing the next question…"):
            try:
                if not api_key:
                    st.session_state.request_error = dict(code="MISSING_API_KEY", http_status=None,
                                                         message="The researcher must configure the API key in Secrets.")
                else:
                    session.decide(OpenAIBackend(api_key))
            except Exception as exc:
                st.session_state.request_error = safe_diagnostic(exc)
    if st.session_state.get("request_error"):
        diagnostic = st.session_state.request_error
        st.error("We couldn't prepare the next question. Your answer is saved in this session. Please retry or download your record.")
        st.warning(diagnostic["message"])
        st.caption("Diagnostic code: " + diagnostic["code"] +
                   (f' · HTTP {diagnostic["http_status"]}' if diagnostic["http_status"] else ""))
        if st.button("Retry next question"):
            st.session_state.request_error = None
            st.rerun()
    else:
        st.rerun()
elif session.stage == "done":
    st.success("Thank you for sharing your perspectives. Please download your record and send it to the researcher.")
elif session.topic == "usage" and session.stage == "core":
    with st.form("usage_answer"):
        answer = st.radio("Your answer", ["Yes", "No"], index=None)
        if st.form_submit_button("Continue"):
            if answer:
                session.answer(answer)
                st.rerun()
            else:
                st.error("Please select Yes or No.")
else:
    answer = st.chat_input("Share your answer", max_chars=12000)
    if answer and answer.strip():
        session.answer(answer)
        st.rerun()

st.divider()
st.download_button("Download full record (JSON)", json.dumps(session.record(), ensure_ascii=False, indent=2),
                   file_name=f"interview_{session.session_id}.json", mime="application/json")
st.download_button("Download conversation (CSV)", session.csv_record().encode("utf-8-sig"),
                   file_name=f"interview_{session.session_id}.csv", mime="text/csv")
with st.expander("Copy conversation"):
    st.code("\n\n".join(f'{m["role"]}: {m["text"]}' for m in session.messages), language=None)
if st.button("Start over"):
    st.session_state.confirm_reset = True
if st.session_state.get("confirm_reset"):
    st.warning("Download your record first. Starting over clears this interview from the session.")
    left, right = st.columns(2)
    if left.button("Confirm start over"):
        st.session_state.clear()
        st.rerun()
    if right.button("Keep interview"):
        st.session_state.confirm_reset = False
        st.rerun()
