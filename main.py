from flask import Flask, request, jsonify
import pg8000
import os

app = Flask(__name__)

# Подключение к БД
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # Парсим DATABASE_URL вручную
    import re
    match = re.match(r'postgres://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
    if match:
        user, password, host, port, database = match.groups()
        conn = pg8000.connect(
            user=user,
            password=password,
            host=host,
            port=int(port),
            database=database
        )
    else:
        conn = None
else:
    conn = None

# Создание таблицы при старте
if conn:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
    conn.commit()

@app.route('/save', methods=['POST'])
def save_message():
    if not conn:
        return jsonify({"error": "DB not connected"}), 500

    data = request.get_json()
    message = data.get('message', '') if data else ''

    with conn.cursor() as cur:
        cur.execute("INSERT INTO messages (content) VALUES (%s)", (message,))
    conn.commit()

    return jsonify({"status": "saved", "message": message})

@app.route('/messages')
def get_messages():
    if not conn:
        return jsonify({"error": "DB not connected"}), 500

    with conn.cursor() as cur:
        cur.execute("SELECT id, content, created_at FROM messages ORDER BY id DESC LIMIT 10")
        rows = cur.fetchall()

    messages = [{"id": r[0], "text": r[1], "time": r[2].isoformat()} for r in rows]
    return jsonify(messages)

@app.route('/')
def health_check():
    return jsonify({"status": "ok", "db_connected": conn is not None})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
