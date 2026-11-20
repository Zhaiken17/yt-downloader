export const API = "https://youtube-video-downloader-cmpg.onrender.com";

async function post(path, body) {
  try {
    const res = await fetch(`${API}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    
    // If the server returns an error (like 400 or 500), catch it here
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.error || `Server error: ${res.status}`);
    }
    
    return await res.json();
  } catch (err) {
    // This catches network errors (like Render being asleep)
    if (err.name === "TypeError" && err.message.includes("fetch")) {
      throw new Error("Backend is waking up (takes 50s) or is offline. Please wait and try again.");
    }
    throw err;
  }
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
