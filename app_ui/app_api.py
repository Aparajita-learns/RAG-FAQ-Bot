import os
import sys
import uuid
import sqlite3
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

# Add parent directory to sys.path for internal imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline_retrieval.query_processor import QueryProcessor

load_dotenv()

app = FastAPI(title="Mutual Fund FAQ API")

# Mount static files and setup templates
app.mount("/static", StaticFiles(directory="app_ui/static"), name="static")
templates = Jinja2Templates(directory="app_ui/templates")

# Initialize AI Engine
processor = QueryProcessor()

# --- DATABASE LOGIC ---
DB_PATH = "chat_history.db"

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (thread_id TEXT, role TEXT, content TEXT, timestamp DATETIME)''')
    c.execute('''CREATE TABLE IF NOT EXISTS threads
                 (thread_id TEXT PRIMARY KEY, title TEXT, created_at DATETIME)''')
    conn.commit()
    conn.close()

init_db()

# --- MODELS ---
class ChatRequest(BaseModel):
    message: str
    thread_id: str

class ChatResponse(BaseModel):
    response: str
    thread_id: str

class ThreadInfo(BaseModel):
    thread_id: str
    title: str

# --- ENDPOINTS ---

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/threads", response_model=List[ThreadInfo])
async def list_threads():
    conn = get_db()
    c = conn.cursor()
    # Only return threads that have at least one message
    c.execute("""
        SELECT t.thread_id, t.title 
        FROM threads t 
        JOIN messages m ON t.thread_id = m.thread_id 
        GROUP BY t.thread_id 
        ORDER BY t.created_at DESC
    """)
    rows = c.fetchall()
    conn.close()
    return [{"thread_id": r[0], "title": r[1]} for r in rows]

@app.post("/api/threads/new", response_model=ThreadInfo)
async def create_new_thread():
    thread_id = str(uuid.uuid4())
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO threads VALUES (?, ?, ?)", (thread_id, "Empty Chat", datetime.now()))
    conn.commit()
    conn.close()
    return {"thread_id": thread_id, "title": "Empty Chat"}

@app.get("/api/history/{thread_id}")
async def get_chat_history(thread_id: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE thread_id = ? ORDER BY timestamp ASC", (thread_id,))
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in rows]

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Get response from RAG processor
        ai_response = processor.get_answer(request.message)
        
        # Persist to DB
        conn = get_db()
        c = conn.cursor()
        
        # Save User Message
        c.execute("INSERT INTO messages VALUES (?, ?, ?, ?)", (request.thread_id, "user", request.message, datetime.now()))
        
        # Update thread title if first message
        c.execute("SELECT COUNT(*) FROM messages WHERE thread_id = ?", (request.thread_id,))
        count = c.fetchone()[0]
        if count == 1:
            title = request.message[:30] + "..."
            c.execute("UPDATE threads SET title = ? WHERE thread_id = ?", (title, request.thread_id))
            
        # Save Assistant Message
        c.execute("INSERT INTO messages VALUES (?, ?, ?, ?)", (request.thread_id, "assistant", ai_response, datetime.now()))
        
        conn.commit()
        conn.close()
        
        return {"response": ai_response, "thread_id": request.thread_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
