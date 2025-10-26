import os, time, requests
from flask import Flask, request, jsonify
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

SERVICE = os.environ.get("SERVICE_NAME", "api-service")
AUTH_URL = os.environ.get("AUTH_URL", "http://auth-service:5001")
STORAGE_URL = os.environ.get("STORAGE_URL", "http://storage-service:5002")

app = Flask(__name__)

REQ_CNT = Counter('app_requests_total', 'Total HTTP requests', ['service','method','endpoint','http_status'])
LATENCY = Histogram('app_request_latency_seconds', 'Request latency', ['service','endpoint'])
INPROG = Gauge('app_inprogress_requests', 'In-progress', ['service'])

@app.route('/upload', methods=['POST'])
def upload():
    start = time.time()
    INPROG.labels(SERVICE).inc()
    try:
        token = request.headers.get('Authorization')
        # optional auth check: call auth-service
        if token:
            r = requests.post(f"{AUTH_URL}/validate", headers={'Authorization': token}, timeout=3)
            if r.status_code != 200:
                REQ_CNT.labels(SERVICE, request.method, '/upload', str(r.status_code)).inc()
                return jsonify({'error':'unauthorized'}), 401
        # forward file to storage-service
        files = {'file': request.files.get('file')}
        r = requests.post(f"{STORAGE_URL}/store", files=files, timeout=20)
        REQ_CNT.labels(SERVICE, request.method, '/upload', str(r.status_code)).inc()
        return (r.content, r.status_code, r.headers.items())
    except Exception as e:
        REQ_CNT.labels(SERVICE, request.method, '/upload', '500').inc()
        return jsonify({'error': str(e)}), 500
    finally:
        LATENCY.labels(SERVICE, '/upload').observe(time.time()-start)
        INPROG.labels(SERVICE).dec()

@app.route('/download/<fid>', methods=['GET'])
def download(fid):
    start = time.time()
    INPROG.labels(SERVICE).inc()
    try:
        token = request.headers.get('Authorization')
        # validate token if present
        if token:
            r = requests.post(f"{AUTH_URL}/validate", headers={'Authorization': token}, timeout=3)
            if r.status_code != 200:
                REQ_CNT.labels(SERVICE, request.method, '/download', str(r.status_code)).inc()
                return jsonify({'error':'unauthorized'}), 401
        r = requests.get(f"{STORAGE_URL}/fetch/{fid}", stream=True, timeout=20)
        REQ_CNT.labels(SERVICE, request.method, '/download', str(r.status_code)).inc()
        return (r.raw.read(), r.status_code, r.headers.items())
    except Exception as e:
        REQ_CNT.labels(SERVICE, request.method, '/download', '500').inc()
        return jsonify({'error': str(e)}), 500
    finally:
        LATENCY.labels(SERVICE, '/download').observe(time.time()-start)
        INPROG.labels(SERVICE).dec()

@app.route('/health')
def health():
    return jsonify({'status':'ok'}), 200

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
