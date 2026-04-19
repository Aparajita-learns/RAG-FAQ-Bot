import streamlit as st
import sys
import os
import uuid
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# Add the parent directory to sys.path so we can import from pipeline_retrieval
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline_retrieval.query_processor import QueryProcessor

# Load environment variables
load_dotenv()

# --- DATABASE SETUP (Thread Management) ---
def init_db():
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (thread_id TEXT, role TEXT, content TEXT, timestamp DATETIME)''')
    c.execute('''CREATE TABLE IF NOT EXISTS threads
                 (thread_id TEXT PRIMARY KEY, title TEXT, created_at DATETIME)''')
    conn.commit()
    return conn

def get_threads(conn):
    c = conn.cursor()
    c.execute("SELECT thread_id, title FROM threads ORDER BY created_at DESC")
    return c.fetchall()

def create_thread(conn, title="New Conversation"):
    thread_id = str(uuid.uuid4())
    c = conn.cursor()
    c.execute("INSERT INTO threads VALUES (?, ?, ?)", (thread_id, title, datetime.now()))
    conn.commit()
    return thread_id

def save_message(conn, thread_id, role, content):
    c = conn.cursor()
    c.execute("INSERT INTO messages VALUES (?, ?, ?, ?)", (thread_id, role, content, datetime.now()))
    conn.commit()

def get_history(conn, thread_id):
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE thread_id = ? ORDER BY timestamp ASC", (thread_id,))
    return c.fetchall()

# --- PAGE CONFIG ---
st.set_page_config(page_title="MF FAQ Assistant", page_icon="📈", layout="wide")

# Initialize DB and Session State
conn = init_db()

if "processor" not in st.session_state:
    with st.spinner("Initializing AI Engine... (Downloading embeddings model ~90MB)"):
        st.session_state.processor = QueryProcessor()

if "current_thread_id" not in st.session_state:
    threads = get_threads(conn)
    if threads:
        st.session_state.current_thread_id = threads[0][0]
    else:
        st.session_state.current_thread_id = create_thread(conn)

# --- SIDEBAR (Thread Management) ---
with st.sidebar:
    st.title("🧵 Conversations")
    
    st.divider()
    
    all_threads = get_threads(conn)
    for tid, title in all_threads:
        btn_type = "primary" if tid == st.session_state.current_thread_id else "secondary"
        if st.button(f"💬 {title[:25]}...", key=tid, use_container_width=True, type=btn_type):
            st.session_state.current_thread_id = tid
            st.rerun()

# --- MAIN UI ---
st.title("📈 Mutual Fund FAQ Assistant")
st.info("💡 **Welcome!** I am your factual HDFC Mutual Fund assistant. I only provide data from official sources.")

# Mandatory Disclaimer Banner
st.warning("⚠️ **Disclaimer:** Facts-only. No investment advice or recommendations provided.")

# Example Questions Section
st.subheader("Example Questions")
col1, col2, col3 = st.columns(3)
if col1.button("What is the exit load for HDFC Mid-Cap fund?"):
    st.session_state.temp_input = "What is the exit load for HDFC Mid-Cap fund?"
if col2.button("Minimum SIP amount for HDFC Large Cap?"):
    st.session_state.temp_input = "What is the minimum SIP amount for HDFC Large Cap Fund?"
if col3.button("Lock-in period for HDFC ELSS Tax Saver?"):
    st.session_state.temp_input = "What is the lock-in period for HDFC ELSS Tax Saver fund?"

# --- CHAT INTERFACE ---
chat_container = st.container()

# Display history
history = get_history(conn, st.session_state.current_thread_id)
with chat_container:
    for role, content in history:
        with st.chat_message(role):
            st.markdown(content)

# Chat Input
user_input = st.chat_input("Ask about HDFC Mutual Funds (e.g., Expense ratio, Exit load, Lock-in)...")

# If user clicked an example question, override input
if "temp_input" in st.session_state:
    user_input = st.session_state.temp_input
    del st.session_state.temp_input

if user_input:
    # 1. Display and Save User Message
    with chat_container:
        with st.chat_message("user"):
            st.markdown(user_input)
    save_message(conn, st.session_state.current_thread_id, "user", user_input)
    
    # Update thread title if it's the first message
    if len(history) == 0:
        c = conn.cursor()
        c.execute("UPDATE threads SET title = ? WHERE thread_id = ?", (user_input[:40], st.session_state.current_thread_id))
        conn.commit()

    # 2. Generate and Save Assistant Message
    with chat_container:
        with st.chat_message("assistant"):
            with st.spinner("Retrieving facts..."):
                try:
                    response = st.session_state.processor.get_answer(user_input)
                    st.markdown(response)
                    save_message(conn, st.session_state.current_thread_id, "assistant", response)
                except Exception as e:
                    st.error(f"Error connecting to AI service: {e}")
                    st.info("Check if your GROQ_API_KEY is correctly set in your environment.")

# --- FOOTER ---
st.divider()
st.caption("Powered by RAG Stack: LangChain + Groq (Llama 3) + Chroma Cloud.")
