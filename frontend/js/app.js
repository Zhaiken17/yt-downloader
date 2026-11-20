import { getFormats, startDownload, pollStatus, fileUrl } from "./api.js";
import { renderVideoFormats, renderAudioFormats } from "./formats.js";

const $ = (id) => document.getElementById(id);
const urlInput = $("url");
const modeSel = $("mode");
const formatSel = $("format");
const goBtn = $("go");
const jobsContainer = $("jobs-container");
const emptyMsg = $("empty-msg");

let debounceTimer;
let currentFormats = [];

urlInput.addEventListener("input", () => {
  clearTimeout(debounceTimer);
  goBtn.disabled = true;
  formatSel.innerHTML = "<option>Loading…</option>";
  formatSel.disabled = true;

  const url = urlInput.value.trim();
  if (!url || (!url.includes("youtube.com") && !url.includes("youtu.be"))) return;

  debounceTimer = setTimeout(async () => {
    try {
      const data = await getFormats(url);
      
      // Defensive check: If the backend returns no formats, show an error
      if (!data.formats || data.formats.length === 0) {
        formatSel.innerHTML = "<option>No video formats found</option>";
        return;
      }
      
      currentFormats = data.formats;
      renderSelects();
      goBtn.disabled = false;
    } catch (err) {
      // Show the actual error message from api.js
      formatSel.innerHTML = `<option>${err.message}</option>`;
    }
  }, 800);
});

modeSel.addEventListener("change", renderSelects);

function renderSelects() {
  formatSel.disabled = false;
  if (modeSel.value === "audio") {
    renderAudioFormats(formatSel);
  } else {
    renderVideoFormats(currentFormats, formatSel);
  }
}

goBtn.addEventListener("click", async () => {
  const url = urlInput.value.trim();
  if (!url) return;

  goBtn.disabled = true;
  goBtn.textContent = "Starting...";

  try {
    const { job_id } = await startDownload(
      url, modeSel.value, formatSel.value || "best"
    );
    
    if (emptyMsg) emptyMsg.style.display = "none";

    createJobCard(job_id, url);
    
    urlInput.value = "";
    formatSel.innerHTML = "<option>Paste a link first…</option>";
    formatSel.disabled = true;
  } catch (err) {
    alert(`Error: ${err.message}`);
  } finally {
    goBtn.textContent = "Download";
  }
});

function createJobCard(jobId, url) {
  const card = document.createElement("div");
  card.className = "job-card";
  card.id = `job-${jobId}`;

  const shortUrl = url.length > 40 ? url.substring(0, 40) + "..." : url;

  card.innerHTML = `
    <div class="job-header">
      <span class="job-title" id="title-${jobId}">${shortUrl}</span>
      <button class="job-close" id="close-${jobId}" title="Remove from list">✕</button>
    </div>
    <div class="job-status" id="status-${jobId}">Queued...</div>
    <div class="job-progress-wrap" id="wrap-${jobId}">
      <div class="job-progress-bar" id="bar-${jobId}"></div>
    </div>
    <div id="action-${jobId}"></div>
  `;
  jobsContainer.prepend(card);

  const titleEl = document.getElementById(`title-${jobId}`);
  const statusEl = document.getElementById(`status-${jobId}`);
  const barEl = document.getElementById(`bar-${jobId}`);
  const wrapEl = document.getElementById(`wrap-${jobId}`);
  const actionEl = document.getElementById(`action-${jobId}`);
  const closeBtn = document.getElementById(`close-${jobId}`);

  closeBtn.onclick = () => card.remove();

  const timer = setInterval(async () => {
    try {
      const s = await pollStatus(jobId);
      
      if (s.title && s.title !== "Fetching title...") {
        titleEl.textContent = s.title;
        titleEl.title = s.title;
      }

      if (s.status === "downloading") {
        statusEl.textContent = `Downloading… ${s.progress}%`;
        barEl.style.width = `${s.progress}%`;
      } else if (s.status === "queued") {
        statusEl.textContent = `Waiting in queue…`;
      } else if (s.status === "done") {
        clearInterval(timer);
        statusEl.textContent = "Ready to save!";
        statusEl.style.color = "#22c55e";
        
        wrapEl.style.display = "none";
        actionEl.innerHTML = `<a class="job-download" href="${fileUrl(jobId)}">⬇ Save to device</a>`;
      } else if (s.status === "error") {
        clearInterval(timer);
        statusEl.textContent = `Error: ${s.error}`;
        statusEl.classList.add("error");
        wrapEl.style.display = "none";
      }
    } catch (err) {
      clearInterval(timer);
      statusEl.textContent = `Lost connection to server`;
      statusEl.classList.add("error");
    }
  }, 2000);
}
