from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
import os
from datetime import datetime

app = Flask(__name__)

# Подключение к БД
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Исправляем URL для SQLAlchemy
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Проверяем подключение и создаем таблицу
        with engine.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.commit()
        
        db_connected = True
        print("✅ Database connected successfully")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        engine = None
        db_connected = False
else:
    engine = None
    db_connected = False
    print("⚠️  DATABASE_URL not found")

@app.route('/save', methods=['POST'])
def save_message():
    if not engine:
        return jsonify({"error": "Database not connected"}), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data"}), 400
            
        message = data.get('message', '')
        
        with engine.connect() as conn:
            conn.execute(
                "INSERT INTO messages (content) VALUES (%s)",
                message
            )
            conn.commit()
        
        return jsonify({"status": "saved", "message": message})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/messages')
def get_messages():
    if not engine:
        return jsonify({"error": "Database not connected"}), 500

    try:
        with engine.connect() as conn:
            result = conn.execute(
                "SELECT id, content, created_at FROM messages ORDER BY id DESC LIMIT 10"
            )
            rows = result.fetchall()
        
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
        return jsonify({"error": str(e)}), 500

@app.route('/')
def health_check():
    return jsonify({
        "status": "ok", 
        "db_connected": db_connected
    })

@app.route('/test-db')
def test_db():
    if not engine:
        return jsonify({"error": "Database not connected"}), 500
    
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            test_result = result.scalar()
        
        return jsonify({"database_test": "success", "result": test_result})
    except Exception as e:
        return jsonify({"database_test": "failed", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
