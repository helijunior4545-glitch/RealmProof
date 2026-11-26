(() => {
  const root = document.getElementById("rp-monitor");
  if (!root) return;
  const status = document.getElementById("rp-monitor-status");
  const pause = document.getElementById("rp-monitor-pause");
  const button = document.getElementById("rp-monitor-refresh");
  let paused = false, busy = false;
  const inspecting = () => root.contains(document.activeElement) || !!root.querySelector("details[open]") || !!root.querySelector("form[aria-busy=true]");
  async function refresh(force = false) {
    if (busy || document.hidden || (!force && paused)) return;
    if (inspecting()) { if (force) status.textContent = "Close expanded details before refreshing."; return; }
    busy = true;
    button.disabled = true;
    if (force) { button.classList.add("rp-action-pending"); status.textContent = "Refreshing results…"; }
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 12000);
    try {
      const response = await fetch(root.dataset.url, {cache:"no-store", credentials:"same-origin", signal:controller.signal});
      if (!response.ok || response.redirected) throw new Error("Monitor unavailable");
      const html = await response.text();
      if ((!paused || force) && !inspecting()) {
        root.innerHTML = html;
        status.textContent = paused ? "Updated manually · automatic updates paused" : "Monitor updated";
      } else status.textContent = paused ? "Updates paused" : "Update deferred while inspecting";
    } catch (_) { status.textContent = "Refresh unavailable; existing results retained."; }
    finally { clearTimeout(timeout); busy = false; button.disabled = false; button.classList.remove("rp-action-pending"); }
  }
  pause.addEventListener("click", () => {
    paused = !paused;
    pause.setAttribute("aria-pressed", String(paused));
    pause.textContent = paused ? "Resume updates" : "Pause updates";
    status.textContent = paused ? "Updates paused" : "Automatic refresh enabled";
    if (!paused) refresh();
  });
  button.addEventListener("click", () => refresh(true));
  setInterval(() => refresh(), 3000);
})();
