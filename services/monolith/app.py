import os
import uuid
import time
import hashlib
from flask import Flask, request, send_from_directory, jsonify
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/data/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
SERVICE = os.environ.get("SERVICE_NAME", "file-monolith")

REQUEST_COUNT = Counter('app_requests_total', 'Total HTTP requests', ['service','method','endpoint','http_status'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request latency', ['service','endpoint'])
IN_PROGRESS = Gauge('app_inprogress_requests', 'In-progress requests', ['service'])
UPLOAD_BYTES = Counter('app_upload_bytes_total', 'Uploaded bytes', ['service'])
FILE_COUNT = Gauge('app_file_count', 'File count', ['service'])

def update_file_count():
    try:
        n = len(os.listdir(UPLOAD_DIR))
    except:
        n = 0
    FILE_COUNT.labels(SERVICE).set(n)

@app.route('/upload', methods=['POST'])
def upload():
    start = time.time()
    IN_PROGRESS.labels(SERVICE).inc()
    try:
        f = request.files.get('file')
        if not f:
            REQUEST_COUNT.labels(SERVICE, request.method, '/upload', '400').inc()
            return jsonify({'error':'no file provided'}), 400
        fid = str(uuid.uuid4())
        path = os.path.join(UPLOAD_DIR, fid)
        f.save(path)
        size = os.path.getsize(path)
        UPLOAD_BYTES.labels(SERVICE).inc(size)
        # cpu work
        with open(path,'rb') as fh:
            hashlib.sha256(fh.read()).hexdigest()
        REQUEST_COUNT.labels(SERVICE, request.method, '/upload', '200').inc()
        update_file_count()
        return jsonify({'id': fid}), 200
    except Exception as e:
        REQUEST_COUNT.labels(SERVICE, request.method, '/upload', '500').inc()
        return jsonify({'error': str(e)}), 500
    finally:
        REQUEST_LATENCY.labels(SERVICE, '/upload').observe(time.time()-start)
        IN_PROGRESS.labels(SERVICE).dec()

@app.route('/download/<fid>', methods=['GET'])
def download(fid):
    start = time.time()
    IN_PROGRESS.labels(SERVICE).inc()
    try:
        p = os.path.join(UPLOAD_DIR, fid)
        if not os.path.exists(p):
            REQUEST_COUNT.labels(SERVICE, request.method, '/download', '404').inc()
            return jsonify({'error':'not found'}), 404
        REQUEST_COUNT.labels(SERVICE, request.method, '/download', '200').inc()
        return send_from_directory(UPLOAD_DIR, fid, as_attachment=True)
    except Exception as e:
        REQUEST_COUNT.labels(SERVICE, request.method, '/download', '500').inc()
        return jsonify({'error':str(e)}), 500
    finally:
        REQUEST_LATENCY.labels(SERVICE, '/download').observe(time.time()-start)
        IN_PROGRESS.labels(SERVICE).dec()

@app.route('/list', methods=['GET'])
def list_files():
    start = time.time()
    IN_PROGRESS.labels(SERVICE).inc()
    try:
        files = os.listdir(UPLOAD_DIR)
        REQUEST_COUNT.labels(SERVICE, request.method, '/list', '200').inc()
        update_file_count()
        return jsonify({'files': files}), 200
    finally:
        REQUEST_LATENCY.labels(SERVICE, '/list').observe(time.time()-start)
        IN_PROGRESS.labels(SERVICE).dec()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status':'ok'}), 200

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8081))
    app.run(host='0.0.0.0', port=port)
