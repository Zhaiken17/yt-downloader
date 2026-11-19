export function renderVideoFormats(formats, selectEl) {
  const heights = [...new Set(
    formats.filter(f => f.height).map(f => f.height)
  )].sort((a, b) => b - a);

  if (!heights.length) {
    selectEl.innerHTML = `<option value="best">best available</option>`;
    return;
  }

  selectEl.innerHTML = heights
    .map(h => `<option value="${h}">${h}p</option>`)
    .join("");
}

export function renderAudioFormats(selectEl) {
  selectEl.innerHTML = `<option value="best">best → MP3</option>`;
}
