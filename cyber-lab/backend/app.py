from flask import Flask, jsonify, request
from datetime import datetime, timezone
import sqlite3

app = Flask(__name__)
DB_PATH = 'cybersec_lab.db'


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        conn.commit()


@app.get('/api/health')
def health():
    return jsonify({'status': 'ok', 'service': 'cybersec-lab-api', 'database': 'sqlite'})


@app.get('/api/events')
def get_events():
    with get_db() as conn:
        rows = conn.execute('''
            SELECT id, event_type AS type, severity, created_at AS timestamp
            FROM security_events
            ORDER BY id DESC
            LIMIT 50
        ''').fetchall()
    return jsonify({'events': [dict(row) for row in rows]})


@app.post('/api/events')
def create_event():
    data = request.get_json(silent=True) or {}
    event_type = str(data.get('type', 'LAB_TEST'))[:50]
    severity = str(data.get('severity', 'LOW')).upper()[:10]
    if severity not in {'LOW', 'MEDIUM', 'HIGH'}:
        severity = 'LOW'

    timestamp = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cursor = conn.execute(
            'INSERT INTO security_events (event_type, severity, created_at) VALUES (?, ?, ?)',
            (event_type, severity, timestamp)
        )
        conn.commit()
        event_id = cursor.lastrowid

    return jsonify({
        'id': event_id,
        'type': event_type,
        'severity': severity,
        'timestamp': timestamp
    }), 201


init_db()

if __name__ == '__main__':
    # Local lab only. Do not expose this development server to the internet.
    app.run(host='127.0.0.1', port=5000, debug=False)
