from flask import Flask, request, jsonify, send_from_directory
import os, uuid

app = Flask(__name__)
STORAGE_DIR = "/data/storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

@app.route('/')
def home():
    return jsonify({"service": "storage-service", "status": "running"})

@app.route('/store', methods=['POST'])
def store_file():
    f = request.files.get('file')
    if not f:
        return jsonify({'error': 'No file provided'}), 400

    fid = str(uuid.uuid4())
    filename = f"{fid}_{f.filename}"
    save_path = os.path.join(STORAGE_DIR, filename)
    f.save(save_path)

    return jsonify({'message': 'File stored', 'file_id': filename}), 200

@app.route('/retrieve/<fid>', methods=['GET'])
def retrieve(fid):
    # Find matching file
    for fname in os.listdir(STORAGE_DIR):
        if fname.startswith(fid):
            return send_from_directory(STORAGE_DIR, fname, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002)
