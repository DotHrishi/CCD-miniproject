# app.py (very short)
from flask import Flask, request, send_file, jsonify
import sqlite3, os
app = Flask(__name__)
UPLOAD_DIR = '/data/uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload():
    f = request.files['file']
    path = os.path.join(UPLOAD_DIR, f.filename)
    f.save(path)
    # store metadata in sqlite
    return jsonify({'status':'ok','filename':f.filename}), 201

@app.route('/download/<name>')
def download(name):
    return send_file(os.path.join(UPLOAD_DIR, name), as_attachment=True)

