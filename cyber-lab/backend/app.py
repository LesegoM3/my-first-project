from flask import Flask, jsonify, request
from datetime import datetime, timezone

app = Flask(__name__)

# Training-only in-memory event store. No real credentials or personal data.
events = []

@app.get('/api/health')
def health():
    return jsonify({'status': 'ok', 'service': 'cybersec-lab-api'})

@app.get('/api/events')
def get_events():
    return jsonify({'events': events[-50:]})

@app.post('/api/events')
def create_event():
    data = request.get_json(silent=True) or {}
    event_type = str(data.get('type', 'LAB_TEST'))[:50]
    severity = str(data.get('severity', 'LOW')).upper()[:10]
    if severity not in {'LOW', 'MEDIUM', 'HIGH'}:
        severity = 'LOW'

    event = {
        'id': len(events) + 1,
        'type': event_type,
        'severity': severity,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    events.append(event)
    return jsonify(event), 201

if __name__ == '__main__':
    # Local lab only. Do not expose this development server to the internet.
    app.run(host='127.0.0.1', port=5000, debug=False)
