/* Native details own capability interactions in both frontend modes. */
(() => {
  for (const explorer of document.querySelectorAll(".rp-cap-explorer")) {
    const items = Array.from(explorer.querySelectorAll(".rp-cap-item"));
    if (!items.length) continue;
    const desktop = matchMedia("(hover: hover) and (min-width: 761px)");
    const activate = item => {
      for (const other of items) other.open = other === item;
    };
    explorer.classList.add("is-enhanced");
    for (const item of items) {
      const summary = item.querySelector("summary");
      if (!summary) continue;
      item.addEventListener("pointerenter", event => {
        if (event.pointerType === "mouse" && desktop.matches &&
            !explorer.querySelector(".rp-cap-content :focus")) activate(item);
      });
      summary.addEventListener("focus", () => {
        if (desktop.matches) activate(item);
      });
      summary.addEventListener("click", event => {
        event.preventDefault();
        if (!desktop.matches && item.open) item.open = false;
        else activate(item);
      });
    }
  }
})();
