import os
import uuid
import sqlite3
from datetime import datetime
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

class UIServer:
    def __init__(self, processor, db_path="chat_history.db"):
        self.app = FastAPI(title="Mutual Fund FAQ API")
        
        # Enable CORS for Vercel deployment
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"], # In production, replace with your Vercel URL
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self.processor = processor
        self.db_path = db_path
        
        self.init_db()
        self.setup_routes()

    def get_db(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def init_db(self):
        conn = self.get_db()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (thread_id TEXT, role TEXT, content TEXT, timestamp DATETIME)''')
        c.execute('''CREATE TABLE IF NOT EXISTS threads
                     (thread_id TEXT PRIMARY KEY, title TEXT, created_at DATETIME)''')
        conn.commit()
        conn.close()

    def setup_routes(self):
        app = self.app

        @app.get("/")
        async def root():
            return {"status": "Backend is running", "api_version": "v1"}

        @app.get("/api/threads")
        async def list_threads():
            conn = self.get_db()
            c = conn.cursor()
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

        @app.post("/api/threads/new")
        async def create_new_thread():
            thread_id = str(uuid.uuid4())
            conn = self.get_db()
            c = conn.cursor()
            c.execute("INSERT INTO threads VALUES (?, ?, ?)", (thread_id, "Empty Chat", datetime.now()))
            conn.commit()
            conn.close()
            return {"thread_id": thread_id, "title": "Empty Chat"}

        @app.post("/api/chat")
        async def chat_endpoint(request: dict):
            try:
                # Use the passed processor logic
                ai_response = self.processor.get_answer(request["message"])
                
                conn = self.get_db()
                c = conn.cursor()
                c.execute("INSERT INTO messages VALUES (?, ?, ?, ?)", (request["thread_id"], "user", request["message"], datetime.now()))
                
                # Title generation logic
                c.execute("SELECT COUNT(*) FROM messages WHERE thread_id = ?", (request["thread_id"],))
                if c.fetchone()[0] == 1:
                    title = request["message"][:30] + "..."
                    c.execute("UPDATE threads SET title = ? WHERE thread_id = ?", (title, request["thread_id"]))
                    
                c.execute("INSERT INTO messages VALUES (?, ?, ?, ?)", (request["thread_id"], "assistant", ai_response, datetime.now()))
                conn.commit()
                conn.close()
                return {"response": ai_response, "thread_id": request["thread_id"]}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/api/history/{thread_id}")
        async def get_history(thread_id: str):
            conn = self.get_db()
            c = conn.cursor()
            c.execute("SELECT role, content FROM messages WHERE thread_id = ? ORDER BY timestamp ASC", (thread_id,))
            rows = c.fetchall()
            conn.close()
            return [{"role": r[0], "content": r[1]} for r in rows]
