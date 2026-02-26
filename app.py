import streamlit as st
import os
from dotenv import load_dotenv
from groq import Groq
import redis
import json
import time
from datetime import datetime
import hashlib

load_dotenv()

# ───────── CONFIG ─────────
GROQ_MODEL = "llama-3.3-70b-versatile"
CACHE_TTL_SECONDS = 30 * 60
SEEN_TTL_SECONDS = 24 * 60 * 60
HISTORY_TTL_SECONDS = 7 * 24 * 60 * 60

st.set_page_config(page_title="Query Bot", page_icon="🤖", layout="wide")

# ───────── MODERN MINIMAL UI FIXED ─────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: #0f172a;
}

body {
    background-color: #f1f5f9;
}

.main {
    background-color: #f1f5f9;
}

/* Header card */
.header-card {
    background: #ffffff;
    padding: 2rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    text-align: center;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
}

/* Chat bubbles base */
[data-testid="stChatMessage"] {
    padding: 1rem 1.2rem;
    border-radius: 18px;
    margin-bottom: 14px;
    font-size: 0.95rem;
    line-height: 1.6;
}

/* USER bubble */
[data-testid="stChatMessage"][data-author="user"] {
    background: #2563eb;
    color: white !important;
}

/* ASSISTANT bubble */
[data-testid="stChatMessage"][data-author="assistant"] {
    background: #e2e8f0;
    color: #0f172a !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
}

/* Buttons */
.stButton>button {
    border-radius: 10px;
    font-weight: 500;
}

/* Input box */
[data-testid="stChatInput"] textarea {
    border-radius: 12px !important;
}

/* Expander */
.stExpander {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 8px;
}

/* Caption */
.stCaption {
    color: #64748b;
    font-size: 0.8rem;
}
</style>
""", unsafe_allow_html=True)

# ───────── HEADER ─────────
st.markdown("""
<div class="header-card">
    <h1 style="margin:0; font-size: 2.3rem; font-weight:600; color:#1f2937;">
        Query Bot
    </h1>
    <p style="margin-top:8px; color:#6b7280;">
        Fast answers • Smart caching • Powered by Groq
    </p>
</div>
""", unsafe_allow_html=True)

# ───────── GROQ CLIENT ─────────
@st.cache_resource
def get_groq_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

groq_client = get_groq_client()

# ───────── REDIS CLIENT ─────────
@st.cache_resource
def get_redis_client():
    client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        decode_responses=True
    )
    try:
        client.ping()
        return client
    except Exception as e:
        st.error(f"Redis connection failed: {e}")
        st.stop()

redis_client = get_redis_client()

# ───────── HASH ─────────
def make_query_hash(q: str) -> str:
    return hashlib.sha256(q.strip().encode()).hexdigest()[:16]

def summary_cache_key(username, q_hash):
    return f"cache:{username}:summary:{q_hash}"

def seen_key(username, q_hash):
    return f"cache:{username}:seen:{q_hash}"

def history_key(username):
    return f"history:{username}"

# ───────── HISTORY ─────────
def save_to_history(username, question, summary):
    key = history_key(username)
    ts = time.time()
    msg = {
        "ts": ts,
        "time": datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M"),
        "question": question,
        "summary": summary,
    }
    redis_client.zadd(key, {json.dumps(msg): ts})
    redis_client.expire(key, HISTORY_TTL_SECONDS)

def load_history(username):
    key = history_key(username)
    items = redis_client.zrevrange(key, 0, 49)
    return [json.loads(item) for item in items if item]

def clear_history(username):
    redis_client.delete(history_key(username))

# ───────── AUTH ─────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None

VALID_USERS = {
    "dashrath": "Dash1234",
    "demo": "demo2025",
}

def authenticate(username, password):
    return VALID_USERS.get(username.strip().lower()) == password

# ───────── SIDEBAR ─────────
with st.sidebar:
    st.markdown("### Controls")

    if st.session_state.authenticated:
        st.success(f"Logged in as **{st.session_state.username}**")

        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

        if st.button("Clear History"):
            clear_history(st.session_state.username)
            st.success("History cleared")
            time.sleep(0.8)
            st.rerun()
    else:
        st.info("Please sign in")

# ───────── LOGIN ─────────
if not st.session_state.authenticated:
    st.title("Sign In")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.form_submit_button("Sign In"):
            if authenticate(username, password):
                st.session_state.username = username.strip().lower()
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid credentials")
    st.stop()

USERNAME = st.session_state.username
st.subheader(f"Hi {USERNAME.capitalize()}, ask anything…")

# ───────── HISTORY DISPLAY ─────────
history = load_history(USERNAME)
if history:
    with st.expander("Recent conversations"):
        for item in history:
            with st.chat_message("user"):
                st.caption(item["time"])
                st.markdown(item["question"])
            with st.chat_message("assistant"):
                st.caption(item["time"] + " • Summary")
                st.markdown(item["summary"])

# ───────── CHAT INPUT ─────────
question = st.chat_input("Your question…")

if question:
    question = question.strip()
    if not question:
        st.rerun()

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with st.chat_message("user"):
        st.caption(current_time)
        st.markdown(question)

    q_hash = make_query_hash(question)
    summary_key = summary_cache_key(USERNAME, q_hash)
    seen_flag_key = seen_key(USERNAME, q_hash)

    cached_summary = redis_client.get(summary_key)
    has_seen_full = redis_client.exists(seen_flag_key)

    # Repeat → show summary
    if cached_summary and has_seen_full:
        with st.chat_message("assistant"):
            st.caption(f"{current_time} • Summary (repeat)")
            st.markdown(cached_summary)

        save_to_history(USERNAME, question, cached_summary)

    # First time → full answer
    else:
        with st.spinner("Generating answer..."):
            full_resp = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": question}],
                temperature=0.7,
                max_tokens=2048,
            )
            full_text = full_resp.choices[0].message.content.strip()

            summary_prompt = "Summarize in 1–3 short sentences:\n\n" + full_text
            summary_resp = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": summary_prompt}],
                temperature=0.4,
                max_tokens=120,
            )
            summary_text = summary_resp.choices[0].message.content.strip()

            redis_client.setex(summary_key, CACHE_TTL_SECONDS, summary_text)
            redis_client.setex(seen_flag_key, SEEN_TTL_SECONDS, "1")

        with st.chat_message("assistant"):
            st.caption(f"{current_time} • Full answer")
            st.markdown(full_text)

        save_to_history(USERNAME, question, summary_text)