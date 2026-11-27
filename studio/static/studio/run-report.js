if (navigator.clipboard?.writeText) {
  for (const button of document.querySelectorAll("[data-copy-run-hash]")) {
    button.hidden = false;
    button.addEventListener("click", async () => {
      const status = button.closest("section").querySelector("[data-run-copy-status]");
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
