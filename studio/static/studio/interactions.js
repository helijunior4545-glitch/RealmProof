/* Native POST feedback. Preserve submitter name/value and browser validation. */
(() => {
  const pending = new Map();
  document.addEventListener("submit", event => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || event.defaultPrevented) return;
    const button = event.submitter;
    if ((button?.getAttribute("formmethod") || form.method).toLowerCase() !== "post") return;
    if ((button?.getAttribute("formtarget") || form.target || "_self") !== "_self") return;
    if (pending.has(form)) { event.preventDefault(); return; }
    const state = {button, timer: null, indicator: null};
    pending.set(form, state);
    // Do not disable or rename the submitter: native form serialization needs its value.
    state.timer = setTimeout(() => {
      if (event.defaultPrevented) { reset(form); return; }
      form.setAttribute("aria-busy", "true");
      if (button) button.classList.add("rp-action-pending");
      const indicator = document.createElement("span");
      indicator.className = "rp-request-feedback";
      indicator.setAttribute("role", "status");
      indicator.textContent = "Submitting request…";
      form.append(indicator);
      state.indicator = indicator;
    }, 180);
    queueMicrotask(() => { if (event.defaultPrevented) reset(form); });
  });
  function reset(form) {
    const state = pending.get(form);
    if (!state) return;
    clearTimeout(state.timer);
    state.button?.classList.remove("rp-action-pending");
    state.indicator?.remove();
    form.removeAttribute("aria-busy");
    pending.delete(form);
  }
  window.addEventListener("pageshow", () => { for (const form of pending.keys()) reset(form); });
})();
