import csv
import hmac
import io
import json
import os

import streamlit as st
from openai import APIError, AuthenticationError, RateLimitError

from engine import QUESTIONS, add_question, answer, new_session, now, process_pending

st.set_page_config(page_title="Student AI Interview", page_icon="💬", layout="centered")
st.markdown("""<style>.block-container{max-width:850px;padding-top:2.5rem}
[data-testid="stChatMessage"]{border-radius:14px}
</style>""", unsafe_allow_html=True)


def setting(name, default=""):
    try:
        return str(st.secrets.get(name, os.environ.get(name, default)))
    except FileNotFoundError:
        return os.environ.get(name, default)


def downloads(session):
    st.caption("Download your record before closing or refreshing this page. Records are held in this browser session; there is no central research database in this version.")
    payload = json.dumps(session, ensure_ascii=False, indent=2)
    rows = []
    for item in session["messages"]:
        rows.append({"session_id": session["session_id"], "condition": session["condition"],
                     "demo": session["demo"], **item})
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["session_id", "condition", "demo", "role", "content", "topic", "kind", "time"])
    writer.writeheader()
    writer.writerows(rows)
    name = session["session_id"][:8]
    left, right = st.columns(2)
    left.download_button("Download full record (JSON)", payload, f"interview_{name}.json", "application/json", key="json_download")
    right.download_button("Download transcript (CSV)", buffer.getvalue().encode("utf-8-sig"), f"transcript_{name}.csv", "text/csv", key="csv_download")


st.caption("GEORGETOWN STUDENT AI INTERVIEW · RESEARCH PROTOTYPE")
st.title("Your experience with AI")
st.write("A conversation about AI in academic work, your learning, and your perspective.")
api_key = setting("OPENAI_API_KEY")
access_code = setting("ACCESS_CODE")

if "interview" not in st.session_state:
    st.info("This interview uses AI to generate questions. In live mode, your responses are sent to OpenAI. The researcher will receive your record only if you download and share it. You may end the interview at any time.")
    with st.form("setup"):
        participant = st.text_input("Participant code (use a nickname or code)", max_chars=60)
        condition = st.radio("Interview version", ["B", "C"], horizontal=True)
        ai_user = st.radio("Have you used AI tools for academic work?", ["Yes", "No"], horizontal=True)
        demo = st.checkbox("Demo mode — simulated questions, no API calls", value=not bool(api_key))
        entered_code = st.text_input("Study access code", type="password") if access_code else ""
        consent = st.checkbox("I agree to participate and understand how my responses are handled.")
        start = st.form_submit_button("Start interview", type="primary")
    if start:
        if not consent:
            st.warning("Please confirm participation before starting.")
        elif not demo and not api_key:
            st.error("The researcher needs to configure OPENAI_API_KEY in the app's Secrets first.")
        elif access_code and not hmac.compare_digest(entered_code, access_code):
            st.error("The study access code is incorrect.")
        else:
            session = new_session(condition, demo, ai_user == "Yes", setting("OPENAI_MODEL", "gpt-5-mini"), participant.strip())
            add_question(session)
            st.session_state.interview = session
            st.rerun()
    st.caption("The selected AI-use answer controls which core questions are shown. Background is collected without follow-up questions. Other topics allow up to two follow-ups.")
    st.stop()

session = st.session_state.interview
if session["demo"]:
    st.warning("DEMO MODE · Questions and checker decisions are simulated. Do not use these records as model results.")
completed = session["status"] != "active"
st.progress(1.0 if completed else session["question_index"] / len(QUESTIONS))
for message in session["messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if completed:
    st.success("Thank you. Your interview has ended.")
    downloads(session)
else:
    if session["pending"]:
        st.caption("Your answer has been saved. Generating the next question…")
        try:
            with st.spinner("Preparing the next question"):
                process_pending(session, api_key)
            st.rerun()
        except AuthenticationError:
            st.error("The configured API key was rejected. Ask the researcher to check the app's Secrets.")
        except RateLimitError:
            st.error("The API quota or rate limit was reached. Your answer is saved; retry after checking quota.")
        except (APIError, ValueError):
            st.error("The model request failed or returned an incomplete result. Your answer is saved. You can retry the current step.")
        if st.button("Retry current step"):
            st.rerun()
    else:
        reply = st.chat_input("Type your answer…", max_chars=12000)
        if reply and reply.strip():
            answer(session, reply.strip())
            st.rerun()
    if st.button("End interview early"):
        session["status"] = "ended_early"
        session["ended_at"] = now()
        session["pending"] = False
        st.rerun()
    with st.expander("Save current progress"):
        downloads(session)
