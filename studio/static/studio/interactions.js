/* Native POST feedback. Set UI state synchronously before the browser suspends the page during navigation. */
(() => {
  const pending = new Map();
  document.addEventListener("submit", event => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || event.defaultPrevented) return;
    const button = event.submitter;
    if ((button?.getAttribute("formmethod") || form.method).toLowerCase() !== "post") return;
    if ((button?.getAttribute("formtarget") || form.target || "_self") !== "_self") return;
    if (pending.has(form)) { event.preventDefault(); return; }
    // The native request may freeze timers before setTimeout callbacks can paint.
    // Mark the DOM now, without disabling or renaming the submitter (which affects serialization).
    const state = {button, indicator: null};
    pending.set(form, state);
    form.setAttribute("aria-busy", "true");
    if (button) button.classList.add("rp-action-pending");
    const indicator = document.createElement("span");
    indicator.className = "rp-request-feedback";
    indicator.setAttribute("role", "status");
    indicator.textContent = form.dataset.pendingLabel || "Submitting request…";
    form.append(indicator);
    state.indicator = indicator;
    queueMicrotask(() => { if (event.defaultPrevented) reset(form); });
  });
  function reset(form) {
    const state = pending.get(form);
    if (!state) return;
    state.button?.classList.remove("rp-action-pending");
    state.indicator?.remove();
    form.removeAttribute("aria-busy");
    pending.delete(form);
  }
  window.addEventListener("pageshow", () => {
    for (const form of pending.keys()) reset(form);
  });
})();