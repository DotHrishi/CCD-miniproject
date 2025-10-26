import os, time
from flask import Flask, request, jsonify
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
SERVICE = os.environ.get("SERVICE_NAME", "auth-service")

REQ = Counter('app_requests_total', 'Total HTTP requests', ['service','method','endpoint','http_status'])
LAT = Histogram('app_request_latency_seconds', 'Request latency', ['service','endpoint'])
INP = Gauge('app_inprogress_requests', 'In-progress', ['service'])

# very simple: token is "Bearer secret-token"
VALID_TOKEN = os.environ.get("VALID_TOKEN", "Bearer secret-token")

@app.route('/login', methods=['POST'])
def login():
    start = time.time()
    INP.labels(SERVICE).inc()
    try:
        data = request.json or {}
        # for demo allow any username/password => return token
        token = VALID_TOKEN
        REQ.labels(SERVICE, request.method, '/login', '200').inc()
        return jsonify({'token': token}), 200
    finally:
        LAT.labels(SERVICE, '/login').observe(time.time()-start)
        INP.labels(SERVICE).dec()

@app.route('/validate', methods=['POST'])
def validate():
    start = time.time()
    INP.labels(SERVICE).inc()
    try:
        token = request.headers.get('Authorization','')
        if token == VALID_TOKEN:
            REQ.labels(SERVICE, request.method, '/validate', '200').inc()
            return jsonify({'valid':True}), 200
        REQ.labels(SERVICE, request.method, '/validate', '401').inc()
        return jsonify({'valid':False}), 401
    finally:
        LAT.labels(SERVICE, '/validate').observe(time.time()-start)
        INP.labels(SERVICE).dec()

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/health')
def health():
    return jsonify({'ok':True}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5001)))
