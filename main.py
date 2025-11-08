from flask import Flask, request, jsonify
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

# Функция для подключения к БД
def get_db_connection():
    try:
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if not DATABASE_URL:
            print("❌ DATABASE_URL not found")
            return None
        
        # Для Render PostgreSQL
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        print("✅ Database connected successfully")
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

# Функция для инициализации БД
def init_db():
    conn = get_db_connection()
    if not conn:
        return False
        
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
        print("✅ Database table created successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        if conn:
            conn.close()
        return False

# Инициализируем БД при старте приложения
print("🚀 Starting application...")
db_initialized = init_db()

@app.route('/')
def health_check():
    conn = get_db_connection()
    if conn:
        conn.close()
        return jsonify({
            "status": "ok", 
            "db_connected": True,
            "db_initialized": db_initialized
        })
    else:
        return jsonify({
            "status": "ok", 
            "db_connected": False,
            "db_initialized": False
        })

@app.route('/save', methods=['POST'])
def save_message():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database not connected"}), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data"}), 400
            
        message = data.get('message', '').strip()
        if not message:
            return jsonify({"error": "Message is empty"}), 400
        
        cur = conn.cursor()
        cur.execute("INSERT INTO messages (content) VALUES (%s)", (message,))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "status": "saved", 
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
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
        cur.execute("""
            SELECT id, content, created_at 
            FROM messages 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
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
        
        return jsonify({
            "status": "success",
            "count": len(messages),
            "messages": messages
        })
        
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/test-db')
def test_db():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database not connected"}), 500
    
    try:
        cur = conn.cursor()
        
        # Тест 1: Проверка версии PostgreSQL
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        
        # Тест 2: Проверка таблицы
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'messages'
        """)
        table_exists = cur.fetchone()[0] > 0
        
        # Тест 3: Количество сообщений
        cur.execute("SELECT COUNT(*) FROM messages")
        message_count = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return jsonify({
            "status": "success",
            "postgres_version": version,
            "table_exists": table_exists,
            "message_count": message_count
        })
        
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/clear', methods=['POST'])
def clear_messages():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database not connected"}), 500

    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM messages")
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"status": "cleared", "message": "All messages deleted"})
        
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
