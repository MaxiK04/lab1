from flask import Flask, request, jsonify
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

# Подключение к БД
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# Инициализация БД при старте
def init_db():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.commit()
            cur.close()
            conn.close()
            print("✅ Database initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return False
    return False

# Инициализируем БД при импорте
db_initialized = init_db()

@app.route('/save', methods=['POST'])
def save_message():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database not connected"}), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data"}), 400
            
        message = data.get('message', '')
        
        cur = conn.cursor()
        cur.execute("INSERT INTO messages (content) VALUES (%s)", (message,))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"status": "saved", "message": message})
        
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/messages')
def get_messages():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database not connected"}), 500

    try:
        cur = conn.cursor()
        cur.execute("SELECT id, content, created_at FROM messages ORDER BY id DESC LIMIT 10")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        messages = [
            {
                "id": row[0],
                "text": row[1], 
                "time": row[2].isoformat() if row[2] else datetime.now().isoformat()
            }
            for row in rows
        ]
        
        return jsonify(messages)
        
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/')
def health_check():
    conn = get_db_connection()
    db_connected = conn is not None
    if conn:
        conn.close()
    
    return jsonify({
        "status": "ok", 
        "db_connected": db_connected,
        "db_initialized": db_initialized
    })

@app.route('/test-db')
def test_db():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database not connected"}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT version()")
        db_version = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        return jsonify({
            "database_test": "success", 
            "postgres_version": db_version
        })
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"database_test": "failed", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
