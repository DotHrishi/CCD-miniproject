from flask import Flask, request, jsonify
import requests, os, time, uuid, hashlib
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
SERVICE = os.environ.get("SERVICE_NAME", "api-service")

STORAGE_URL = os.environ.get("STORAGE_URL", "http://storage-service:5002")

REQUEST_COUNT = Counter('app_requests_total', 'Total HTTP requests', ['service','method','endpoint','http_status'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request latency', ['service','endpoint'])
IN_PROGRESS = Gauge('app_inprogress_requests', 'In-progress requests', ['service'])

@app.route('/')
def home():
    return jsonify({"service": SERVICE, "status": "running"})

@app.route('/upload', methods=['POST'])
def upload():
    start = time.time()
    IN_PROGRESS.labels(SERVICE).inc()
    try:
        f = request.files.get('file')
        if not f:
            REQUEST_COUNT.labels(SERVICE, request.method, '/upload', '400').inc()
            return jsonify({'error': 'No file provided'}), 400
        
        # Forward file to storage-service
        files = {'file': (f.filename, f.read())}
        res = requests.post(f"{STORAGE_URL}/store", files=files)

        REQUEST_COUNT.labels(SERVICE, request.method, '/upload', str(res.status_code)).inc()
        return res.json(), res.status_code
    except Exception as e:
        REQUEST_COUNT.labels(SERVICE, request.method, '/upload', '500').inc()
        return jsonify({'error': str(e)}), 500
    finally:
        REQUEST_LATENCY.labels(SERVICE, '/upload').observe(time.time() - start)
        IN_PROGRESS.labels(SERVICE).dec()

@app.route('/download/<fid>', methods=['GET'])
def download(fid):
    try:
        res = requests.get(f"{STORAGE_URL}/retrieve/{fid}", stream=True)
        if res.status_code != 200:
            return jsonify(res.json()), res.status_code
        return res.content
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
