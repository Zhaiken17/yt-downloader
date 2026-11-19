import os

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
JOB_TTL_SECONDS = 3600
MAX_DURATION_SECONDS = 8 * 3600
PORT = int(os.environ.get("PORT", 7860))
