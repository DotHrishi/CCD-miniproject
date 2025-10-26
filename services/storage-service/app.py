import os, time
from flask import Flask, request, send_from_directory, jsonify
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import uuid, hashlib

STORAGE_DIR = os.environ.get("STORAGE_DIR", "/data/storage")
os.makedirs(STORAGE_DIR, exist_ok=True)
SERVICE = os.environ.get("SERVICE_NAME", "storage-service")

app = Flask(__name__)
REQ = Counter('app_requests_total', 'Total HTTP requests', ['service','method','endpoint','http_status'])
LAT = Histogram('app_request_latency_seconds', 'Request latency', ['service','endpoint'])
INP = Gauge('app_inprogress_requests', 'In-progress', ['service'])
BYTES = Counter('app_storage_bytes_total', 'Bytes stored', ['service'])
FILE_COUNT = Gauge('app_file_count', 'Stored files', ['service'])

def update_count():
    try:
        n = len(os.listdir(STORAGE_DIR))
    except:
        n = 0
    FILE_COUNT.labels(SERVICE).set(n)

@app.route('/store', methods=['POST'])
def store():
    start = time.time()
    INP.labels(SERVICE).inc()
    try:
        f = request.files.get('file')
        if not f:
            REQ.labels(SERVICE, request.method, '/store', '400').inc()
            return jsonify({'error':'no file'}), 400
        fid = str(uuid.uuid4())
        path = os.path.join(STORAGE_DIR, fid)
        f.save(path)
        size = os.path.getsize(path)
        BYTES.labels(SERVICE).inc(size)
        # optional: compute hash
        with open(path,'rb') as fh:
            hashlib.sha256(fh.read()).hexdigest()
        update_count()
        REQ.labels(SERVICE, request.method, '/store', '200').inc()
        return jsonify({'id': fid}), 200
    except Exception as e:
        REQ.labels(SERVICE, request.method, '/store', '500').inc()
        return jsonify({'error':str(e)}), 500
    finally:
        LAT.labels(SERVICE, '/store').observe(time.time()-start)
        INP.labels(SERVICE).dec()

@app.route('/fetch/<fid>', methods=['GET'])
def fetch(fid):
    start = time.time()
    INP.labels(SERVICE).inc()
    try:
        p = os.path.join(STORAGE_DIR, fid)
        if not os.path.exists(p):
            REQ.labels(SERVICE, request.method, '/fetch', '404').inc()
            return jsonify({'error':'not found'}), 404
        REQ.labels(SERVICE, request.method, '/fetch', '200').inc()
        return send_from_directory(STORAGE_DIR, fid, as_attachment=True)
    finally:
        LAT.labels(SERVICE, '/fetch').observe(time.time()-start)
        INP.labels(SERVICE).dec()

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/health')
def health():
    return jsonify({'ok':True}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5002)))
