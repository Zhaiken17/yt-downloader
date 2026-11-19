import os
import time
import threading
from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
from config import DOWNLOAD_DIR, JOB_TTL_SECONDS, PORT
from jobs import start_job, jobs
from downloader import probe_formats

app = Flask(__name__)
CORS(app)

# --- 1. Handle Cookies for Render ---
# We save the cookies to a file inside the app directory so yt-dlp can find it
COOKIE_FILE_PATH = os.path.join(os.path.dirname(__file__), "cookies.txt")
if os.environ.get("YT_COOKIES"):
    with open(COOKIE_FILE_PATH, "w") as f:
        f.write(os.environ["YT_COOKIES"])

@app.get("/")
def health():
    return {"ok": True}

@app.post("/api/formats")
def formats():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "url required"}), 400
    try:
        return jsonify(probe_formats(url))
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.post("/api/download")
def download():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "url required"}), 400
    job_id = start_job(
        url,
        data.get("mode", "video"),
        data.get("resolution", "best"),
    )
    return jsonify({"job_id": job_id})

@app.get("/api/status/<job_id>")
def status(job_id):
    j = jobs.get(job_id)
    if not j:
        abort(404)
    return jsonify({
        "status": j["status"],
        "progress": j["progress"],
        "error": j["error"],
        "title": j.get("title", "Fetching title..."),
    })

@app.get("/api/file/<job_id>")
def file(job_id):
    j = jobs.get(job_id)
    if not j or j["status"] != "done" or not j["filepath"]:
        abort(404)
    if not os.path.exists(j["filepath"]):
        abort(404)
    
    return send_file(j["filepath"], as_attachment=True)

def _cleaner():
    """Background thread to delete old files so the disk doesn't fill up."""
    while True:
        time.sleep(300) # Check every 5 minutes
        now = time.time()
        for jid, j in list(jobs.items()):
            fp = j.get("filepath")
            if fp and os.path.exists(fp):
                if now - os.path.getctime(fp) > JOB_TTL_SECONDS:
                    try:
                        os.remove(fp)
                    except OSError:
                        pass

if __name__ == "__main__":
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    # Start the background cleanup thread
    threading.Thread(target=_cleaner, daemon=True).start()
    
    # Run Flask
    app.run(host="0.0.0.0", port=PORT)
