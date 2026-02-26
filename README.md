# 🤖 AI Chatbot with Redis Memory & Smart Session Handling

A production-style AI chatbot built with Groq LLM and Redis-based smart caching.  
Designed to optimize token usage, reduce API cost, and maintain isolated user sessions with TTL-based memory management.

---

## 🚀 Project Overview

This project implements a Generative AI chatbot with:

- 🔁 Cache-based memory architecture
- 🧠 Conversation history stored as summaries
- ⏳ TTL-based auto-expiry using Redis
- 👤 Session-based user isolation
- ⚡ Smart repeat question detection
- 💬 Minimal SaaS-style UI (Streamlit)

Instead of storing full conversations, the system stores compact summaries to ensure efficient memory handling and lower storage cost.

---

## 🧩 How It Works

### 🔐 Authentication
- User logs in with a unique username
- Each username acts as a Session ID

### 🧠 First-Time Question
- Full answer generated via Groq LLM
- Short summary created from full response
- Summary stored in Redis with TTL
- “Seen” flag saved for repeat detection

### 🔁 Repeat Question
- System detects same query using hash
- Returns cached summary instantly
- No new LLM API call
- Saves tokens & reduces latency

### 📂 Session Reuse
- If same Session ID (username) is used
- User can access previous conversation summaries

---

## 🏗 Redis Architecture

cache:{user}:summary:{hash}
cache:{user}:seen:{hash}
history:{user}

- 🔑 Query hash ensures repeat detection
- ⏳ TTL auto-cleans inactive cache
- 📊 Sorted history using timestamps

---

## ⚙ Tech Stack

- **Groq LLM (Llama 3.3)**
- **Redis**
- **Streamlit**
- **Python**
- **TTL-based caching**
- **Hash-based query matching**

