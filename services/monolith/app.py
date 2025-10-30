from flask import Flask, render_template, request, send_from_directory, jsonify
import os, uuid, time, hashlib
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/data/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__, template_folder="templates")

SERVICE = os.environ.get("SERVICE_NAME", "file-monolith")

REQUEST_COUNT = Counter('app_requests_total', 'Total HTTP requests', ['service','method','endpoint','http_status'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request latency', ['service','endpoint'])
IN_PROGRESS = Gauge('app_inprogress_requests', 'In-progress requests', ['service'])
UPLOAD_BYTES = Counter('app_upload_bytes_total', 'Uploaded bytes', ['service'])
FILE_COUNT = Gauge('app_file_count', 'File count', ['service'])

def update_file_count():
    try:
        FILE_COUNT.labels(SERVICE).set(len(os.listdir(UPLOAD_DIR)))
    except:
        FILE_COUNT.labels(SERVICE).set(0)

@app.route('/')
def home():
    return render_template('index.html')
