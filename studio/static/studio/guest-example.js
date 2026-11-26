const exampleReport = document.querySelector("[data-demo-report]");

if (exampleReport) {
  const controls = exampleReport.querySelector(".lp-report-switch");
  const buttons = controls.querySelectorAll("button");

  controls.hidden = false;
  controls.addEventListener("click", event => {
    const selected = event.target.closest("button");
    if (!selected) return;
    for (const button of buttons) {
      const active = button === selected;
      button.setAttribute("aria-pressed", String(active));
      document.getElementById(button.getAttribute("aria-controls")).hidden = !active;
    }
  });
}
