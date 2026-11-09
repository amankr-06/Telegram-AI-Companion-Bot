import os
import psycopg
from pathlib import Path
from typing import List
from google.genai import types
from dotenv import load_dotenv


load_dotenv()
DB = os.getenv("DB_URL")


#Initialize DataBase
def init_db():
    conn = psycopg.connect(DB)
    conn.close()

    with psycopg.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Creates a sorted lookup index on user_id to fetch chat history in O(log N) time instead of scanning every row.
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON messages(user_id);")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_memories (
                user_id BIGINT PRIMARY KEY,
                summary TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

#Save chats in database
def save_chat(user_id: int, role: str, content: str):
    with psycopg.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages(user_id, role, content) VALUES(%s,%s,%s)",(user_id, role, content))
        conn.commit()

#Retrieve past chats for context in Gemini format
def get_chat(user_id: int, limit: int = 12) -> List[types.Content]:
    with psycopg.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content FROM (
                SELECT id, role, content FROM messages
                WHERE user_id = %s
                ORDER BY id DESC
                LIMIT %s
            ) ORDER BY id ASC
        """,(user_id,limit))

        rows = cursor.fetchall()

        #Format into SDK content objects
        history = []
        for role, text in rows:
            history.append(
                types.Content(
                    role = role,
                    parts = [types.Part.from_text(text=text)]
                )
            )
        return history

#Clear User History
def clear_user_history(user_id: int):
    with psycopg.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE user_id = %s",(user_id,))
        cursor.execute("DELETE FROM user_memories WHERE user_id = %s", (user_id,))
        conn.commit()


def summarize_history(user_id: int): 
    with psycopg.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role, content FROM messages WHERE user_id=%s AND id NOT IN(SELECT id FROM messages WHERE user_id = %s ORDER BY id DESC LIMIT 10) ORDER BY id ASC",(user_id, user_id))
        n = cursor.fetchall()
        if not n:
            return ""
        #n = [('a','we'),('b','they')] # Format of fetchall 
        context_messages = [f"{role.capitalize()}: {content}" for role, content in n]

        cursor.execute("SELECT summary FROM user_memories WHERE user_id = %s",(user_id,)) #Fetching summary from user_memories
        row = cursor.fetchone() #We are fetching summary from user_memories table also so that the model summarize the new 10 messages as well as old summary itself so that the new summary being made have full context and occupies only 1 row in user_memories table
        context_user_memories = row[0] if row and row[0] else "No Past Summary"
        data = "\n".join(context_messages) + f"\n\n Past Summazrized History \n{context_user_memories}"
        return data

def add_user_memories(user_id: int, summary: str):
    with psycopg.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO user_memories(user_id, summary) VALUES(%s,%s) ON CONFLICT(user_id) DO UPDATE SET summary = excluded.summary, updated_at = CURRENT_TIMESTAMP",(user_id, summary))
        cursor.execute("DELETE FROM messages WHERE user_id = %s AND id NOT IN (SELECT id FROM messages WHERE user_id = %s ORDER BY id DESC LIMIT 10)",(user_id,user_id))
        conn.commit()

def get_past_memory(user_id: int):
    with psycopg.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT summary FROM user_memories WHERE user_id=%s",(user_id,))
        memory = cursor.fetchone()
        return memory[0] if memory else ""

def count_history(user_id: int):
    with psycopg.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM messages WHERE user_id = %s",(user_id,))
        row = cursor.fetchone()
        return row[0] if row else 0
            