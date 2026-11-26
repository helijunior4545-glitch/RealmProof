if (navigator.clipboard?.writeText) {
  const status = document.querySelector("[data-run-copy-status]");
  for (const button of document.querySelectorAll("[data-copy-run-hash]")) {
    button.hidden = false;
    button.addEventListener("click", async () => {
      const digest = document.getElementById(button.dataset.copyRunHash).textContent;
      try {
        await navigator.clipboard.writeText(digest);
        status.textContent = "Fingerprint copied.";
      } catch {
        status.textContent = "Clipboard unavailable. Select and copy the fingerprint above.";
      }
    });
  }
}
