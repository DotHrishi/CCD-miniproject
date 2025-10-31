from flask import Flask, request, jsonify, send_from_directory
import os, uuid, time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
STORAGE_DIR = "/data/storage"
os.makedirs(STORAGE_DIR, exist_ok=True)
SERVICE = os.getenv("SERVICE_NAME", "storage-service")

# --- Unified Prometheus metrics ---
REQUEST_COUNT = Counter('app_requests_total', 'Total HTTP requests', ['service', 'method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request latency (s)', ['service', 'endpoint'])
IN_PROGRESS = Gauge('app_inprogress_requests', 'In-progress requests', ['service'])
FILE_COUNT = Gauge('storage_file_count', 'Number of files stored', ['service'])

def update_file_count():
    try:
        count = len([f for f in os.listdir(STORAGE_DIR) if os.path.isfile(os.path.join(STORAGE_DIR, f))])
        FILE_COUNT.labels(SERVICE).set(count)
    except Exception as e:
        print(f"[WARN] Could not update file count: {e}")
        FILE_COUNT.labels(SERVICE).set(0)

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
    update_file_count()
    return jsonify({"service": SERVICE, "status": "running"})

@app.route('/store', methods=['POST'])
def store_file():
    f = request.files.get('file')
    if not f:
        return jsonify({'error': 'No file provided'}), 400
    fid = str(uuid.uuid4())
    save_path = os.path.join(STORAGE_DIR, fid)
    f.save(save_path)
    update_file_count()
    return jsonify({'message': 'File stored', 'file_id': fid}), 200

@app.route('/retrieve/<fid>', methods=['GET'])
def retrieve(fid):
    file_path = os.path.join(STORAGE_DIR, fid)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    return send_from_directory(STORAGE_DIR, fid, as_attachment=True)

@app.route('/metrics')
def metrics():
    update_file_count()
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': SERVICE}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002)
