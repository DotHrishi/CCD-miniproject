from flask import Flask, request, jsonify
import os, time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
SERVICE = os.environ.get("SERVICE_NAME", "auth-service")
VALID_TOKEN = os.environ.get("VALID_TOKEN", "Bearer secret-token")

# --- Unified metrics ---
REQUEST_COUNT = Counter('app_requests_total', 'Total HTTP requests', ['service','method','endpoint','http_status'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request latency (s)', ['service','endpoint'])
IN_PROGRESS = Gauge('app_inprogress_requests', 'In-progress requests', ['service'])

@app.before_request
def before_request():
    request.start_time = time.time()
    IN_PROGRESS.labels(SERVICE).inc()

@app.after_request
def after_request(response):
    REQUEST_COUNT.labels(SERVICE, request.method, request.path, response.status_code).inc()
    REQUEST_LATENCY.labels(SERVICE, request.path).observe(time.time() - request.start_time)
    IN_PROGRESS.labels(SERVICE).dec()
    return response

@app.route('/login', methods=['POST'])
def login():
    return jsonify({'token': VALID_TOKEN}), 200

@app.route('/validate', methods=['POST'])
def validate():
    token = request.headers.get('Authorization','')
    return jsonify({'valid': token == VALID_TOKEN}), (200 if token == VALID_TOKEN else 401)

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
