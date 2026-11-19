import uuid
import threading
from datetime import datetime

jobs = {}

# NO Semaphore here anymore. Multiple downloads run in parallel threads.

def create_job():
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "filepath": None,
        "error": None,
        "created": datetime.utcnow(),
    }
    return job_id

def _run(job_id, url, mode, resolution):
    from downloader import download_media
    jobs[job_id]["status"] = "downloading"
    try:
        path = download_media(
            url, mode, resolution,
            progress_cb=lambda p: jobs[job_id].update(progress=p),
        )
        jobs[job_id].update(status="done", progress=100, filepath=path)
    except Exception as e:
        jobs[job_id].update(status="error", error=str(e))

def start_job(url, mode, resolution):
    job_id = create_job()
    threading.Thread(
        target=_run, args=(job_id, url, mode, resolution), daemon=True
    ).start()
    return job_id
