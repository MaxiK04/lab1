from flask import Flask, request, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Используем SQLite для начала
DB_PATH = 'messages.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route('/save', methods=['POST'])
def save_message():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data"}), 400
        
    message = data.get('message', '')
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (content) VALUES (?)", (message,))
    conn.commit()
    conn.close()

    return jsonify({"status": "saved", "message": message})

@app.route('/messages')
def get_messages():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, content, created_at FROM messages ORDER BY id DESC LIMIT 10")
    rows = cur.fetchall()
    conn.close()

    messages = [{"id": r[0], "text": r[1], "time": r[2]} for r in rows]
    return jsonify(messages)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
