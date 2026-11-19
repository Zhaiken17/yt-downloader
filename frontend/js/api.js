// Point this to your live Render backend
export const API = "https://youtube-video-downloader-cmpg.onrender.com";

async function post(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data;
}

export async function getFormats(url) {
  return post("/api/formats", { url });
}

export async function startDownload(url, mode, resolution) {
  return post("/api/download", { url, mode, resolution });
}

export async function pollStatus(jobId) {
  const res = await fetch(`${API}/api/status/${jobId}`);
  return res.json();
}

export function fileUrl(jobId) {
  return `${API}/api/file/${jobId}`;
}
