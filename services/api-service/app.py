from flask import Flask, request, jsonify
import requests, os, time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
SERVICE = os.environ.get("SERVICE_NAME", "api-service")
STORAGE_URL = os.environ.get("STORAGE_URL", "http://storage-service:5002")

# --- Unified Prometheus metrics ---
REQUEST_COUNT = Counter('app_requests_total', 'Total HTTP requests', ['service', 'method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request latency (s)', ['service', 'endpoint'])
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

@app.route('/')
def home():
    return jsonify({"service": SERVICE, "status": "running"})

@app.route('/upload', methods=['POST'])
def upload():
    f = request.files.get('file')
    if not f:
        return jsonify({'error': 'No file provided'}), 400
    files = {'file': (f.filename, f.read())}
    res = requests.post(f"{STORAGE_URL}/store", files=files)
    return res.json(), res.status_code

@app.route('/download/<fid>', methods=['GET'])
def download(fid):
    res = requests.get(f"{STORAGE_URL}/retrieve/{fid}")
    if res.status_code != 200:
        return jsonify(res.json()), res.status_code
    return res.content

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
