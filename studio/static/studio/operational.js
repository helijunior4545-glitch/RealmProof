(() => {
  const root = document.getElementById("rp-monitor");
  if (!root) return;
  const status = document.getElementById("rp-monitor-status");
  const pause = document.getElementById("rp-monitor-pause");
  let paused = false, busy = false;
  async function refresh(force = false) {
    if (busy || (!force && (paused || document.hidden || root.contains(document.activeElement) || root.querySelector("details[open]")))) return;
    busy = true;
    try {
      const response = await fetch(root.dataset.url, {cache: "no-store", credentials: "same-origin"});
      if (!response.ok || response.redirected) throw new Error("Monitor unavailable");
      const html = await response.text();
      if (!paused && !root.contains(document.activeElement) && !root.querySelector("details[open]")) root.innerHTML = html;
      status.textContent = paused ? "Updates paused" : "Monitor updated";
    } catch (_) { status.textContent = "Refresh unavailable; retrying when active."; }
    finally { busy = false; }
  }
  pause.addEventListener("click", () => {
    paused = !paused;
    pause.setAttribute("aria-pressed", String(paused));
    pause.textContent = paused ? "Resume updates" : "Pause updates";
    status.textContent = paused ? "Updates paused" : "Automatic refresh enabled";
    if (!paused) refresh();
  });
  document.getElementById("rp-monitor-refresh").addEventListener("click", () => refresh(true));
  setInterval(refresh, 3000);
})();
