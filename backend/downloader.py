import os
import yt_dlp
from config import DOWNLOAD_DIR

def _base_opts():
    opts = {
        "quiet": True,
        "noplaylist": True,
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 30,
        # The 'tv' client bypasses most datacenter IP blocks
        "extractor_args": {
            "youtube": {
                "player_client": ["tv"]
            }
        },
        # Tell yt-dlp to ignore broken formats and try the next one
        "ignoreerrors": True,
    }
    
    cookies = os.path.join(os.path.dirname(__file__), "cookies.txt")
    if os.path.exists(cookies):
        opts["cookiefile"] = cookies
        
    return opts

def probe_formats(url):
    opts = _base_opts()
    opts["skip_download"] = True

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"Error probing formats: {e}")
        raise e

    formats = []
    seen = set()
    for f in info.get("formats", []):
        h = f.get("height")
        if h and f.get("vcodec") not in (None, "none") and h not in seen:
            seen.add(h)
            formats.append({
                "height": h,
                "ext": f.get("ext", "mp4"),
                "filesize": int(f.get("filesize") or 0), 
                "fps": f.get("fps"),
            })

    formats.sort(key=lambda x: x["height"], reverse=True)
    
    return {
        "title": info.get("title", "Unknown Title"),
        "duration": info.get("duration", 0),
        "thumbnail": info.get("thumbnail", ""),
        "formats": formats,
    }

def download_media(url, mode, resolution, progress_cb=None):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    outtmpl = os.path.join(DOWNLOAD_DIR, "%(title).120s-%(id)s.%(ext)s")

    base = _base_opts()
    base["outtmpl"] = outtmpl
    base["progress_hooks"] = [_hook(progress_cb)]

    if mode == "audio":
        opts = {
            **base,
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
    else:
        fmt = (
            f"bestvideo[height<={resolution}]+bestaudio/best"
            if str(resolution) != "best"
            else "bestvideo+bestaudio/best"
        )
        opts = {**base, "format": fmt, "merge_output_format": "mp4"}

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

    base_name = ydl.prepare_filename(info)
    stem = os.path.splitext(base_name)[0]
    expected_ext = ".mp3" if mode == "audio" else ".mp4"

    for f in os.listdir(DOWNLOAD_DIR):
        if f.startswith(os.path.basename(stem)) and f.endswith(expected_ext):
            return os.path.join(DOWNLOAD_DIR, f)

    raise FileNotFoundError("Output file not found after download")

def _hook(cb):
    def h(d):
        if cb and d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
            pct = int(d.get("downloaded_bytes", 0) / total * 100)
            cb(min(pct, 99))
    return h
