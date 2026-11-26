/* Native POST feedback with paint-before-navigation for the guest launch. */
(() => {
  const pending = new Map();
  document.addEventListener("submit", event => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || event.defaultPrevented) return;
    const button = event.submitter;
    if ((button?.getAttribute("formmethod") || form.method).toLowerCase() !== "post") return;
    if ((button?.getAttribute("formtarget") || form.target || "_self") !== "_self") return;
    if (pending.has(form)) { event.preventDefault(); return; }
    // This form has no named submitter or method/action overrides; preserve browser
    // validation and CSRF data while allowing the pending state a frame to paint.
    const deferNavigation = form.classList.contains("jury-launch") &&
      !button?.name && !button?.hasAttribute("formaction") &&
      !button?.hasAttribute("formenctype") && !button?.hasAttribute("formmethod");
    if (deferNavigation) event.preventDefault();
    const indicator = document.createElement("span");
    indicator.className = "rp-request-feedback";
    indicator.setAttribute("role", "status");
    indicator.textContent = form.dataset.pendingLabel || "Submitting request…";
    pending.set(form, {button, indicator});
    form.setAttribute("aria-busy", "true");
    button?.classList.add("rp-action-pending");
    form.append(indicator);
    if (deferNavigation) {
      requestAnimationFrame(() => requestAnimationFrame(() => {
        if (!form.isConnected) { reset(form); return; }
        HTMLFormElement.prototype.submit.call(form);
      }));
    } else {
      queueMicrotask(() => { if (event.defaultPrevented) reset(form); });
    }
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