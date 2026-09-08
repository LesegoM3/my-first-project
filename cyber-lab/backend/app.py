from flask import Flask, jsonify, request
from datetime import datetime, timezone
import hashlib
import hmac
import secrets
import sqlite3

app = Flask(__name__)
DB_PATH = 'cybersec_lab.db'
SESSION_TTL_SECONDS = 3600
sessions = {}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200_000)
    return salt.hex() + ':' + derived.hex()


def verify_password(password, stored):
    try:
        salt_hex, digest_hex = stored.split(':', 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200_000)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


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
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        user = conn.execute('SELECT id FROM users WHERE username = ?', ('lab-admin',)).fetchone()
        if not user:
            conn.execute(
                'INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)',
                ('lab-admin', hash_password('training-only'), datetime.now(timezone.utc).isoformat())
            )
        conn.commit()


def log_event(event_type, severity='LOW'):
    timestamp = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cursor = conn.execute(
            'INSERT INTO security_events (event_type, severity, created_at) VALUES (?, ?, ?)',
            (event_type[:50], severity if severity in {'LOW', 'MEDIUM', 'HIGH'} else 'LOW', timestamp)
        )
        conn.commit()
        return cursor.lastrowid


@app.get('/api/health')
def health():
    return jsonify({'status': 'ok', 'service': 'cybersec-lab-api', 'database': 'sqlite'})


@app.get('/api/events')
def get_events():
    with get_db() as conn:
        rows = conn.execute('''
            SELECT id, event_type AS type, severity, created_at AS timestamp
            FROM security_events ORDER BY id DESC LIMIT 50
        ''').fetchall()
    return jsonify({'events': [dict(row) for row in rows]})


@app.post('/api/events')
def create_event():
    data = request.get_json(silent=True) or {}
    event_type = str(data.get('type', 'LAB_TEST'))[:50]
    severity = str(data.get('severity', 'LOW')).upper()[:10]
    event_id = log_event(event_type, severity)
    return jsonify({'id': event_id, 'type': event_type, 'severity': severity}), 201


@app.post('/api/login')
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get('username', ''))[:100]
    password = str(data.get('password', ''))[:200]

    with get_db() as conn:
        user = conn.execute(
            'SELECT id, username, password_hash FROM users WHERE username = ?',
            (username,)
        ).fetchone()

    if not user or not verify_password(password, user['password_hash']):
        log_event('LOGIN_FAILED', 'MEDIUM')
        return jsonify({'error': 'Invalid lab credentials'}), 401

    token = secrets.token_urlsafe(32)
    sessions[token] = {
        'user_id': user['id'],
        'username': user['username'],
        'created': datetime.now(timezone.utc).timestamp()
    }
    log_event('LOGIN_SUCCESS', 'LOW')
    return jsonify({'message': 'Lab login successful', 'token': token, 'expires_in': SESSION_TTL_SECONDS})


@app.get('/api/me')
def me():
    auth = request.headers.get('Authorization', '')
    token = auth.removeprefix('Bearer ').strip()
    session = sessions.get(token)
    if not session:
        return jsonify({'error': 'Authentication required'}), 401
    if datetime.now(timezone.utc).timestamp() - session['created'] > SESSION_TTL_SECONDS:
        sessions.pop(token, None)
        return jsonify({'error': 'Session expired'}), 401
    return jsonify({'authenticated': True, 'username': session['username']})


init_db()

if __name__ == '__main__':
    # Local lab only. Do not expose this development server to the internet.
    app.run(host='127.0.0.1', port=5000, debug=False)
