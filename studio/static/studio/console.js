/* RealmProof progressive enhancement: all controls stay usable without JavaScript. */
(() => {
  "use strict";

  function validateJSON(element, feedback, required) {
    if (!element) return true;
    const value = element.value.trim();
    if (!value) {
      if (feedback) { feedback.textContent = required ? "A JSON object is required." : "Empty input"; feedback.className = "json-feedback" + (required ? " invalid" : ""); }
      element.setCustomValidity(required ? "Enter a JSON object." : "");
      return !required;
    }
    try {
      const object = JSON.parse(value);
      if (!object || Array.isArray(object) || typeof object !== "object") throw new Error("Expected a JSON object.");
      if (feedback) { feedback.textContent = "✓ Valid JSON object"; feedback.className = "json-feedback valid"; }
      element.setCustomValidity("");
      return true;
    } catch (error) {
      if (feedback) { feedback.textContent = "Invalid JSON: " + error.message; feedback.className = "json-feedback invalid"; }
      element.setCustomValidity("Enter a valid JSON object.");
      return false;
    }
  }

  const builder = document.querySelector("[data-scenario-builder]");
  if (builder) {
    const form = builder.querySelector("[data-wizard-form]");
    const pages = Array.from(builder.querySelectorAll("[data-step-panel]"));
    const steps = Array.from(builder.querySelectorAll("[data-step-link]"));
    const back = builder.querySelector("[data-wizard-back]");
    const next = builder.querySelector("[data-wizard-next]");
    const submit = builder.querySelector("[data-wizard-submit]");
    const counter = builder.querySelector("[data-step-count]");
    const jsonFields = ["id_input_data", "id_expected"];
    let current = 0;

    const fieldsInPage = (page) => Array.from(page.querySelectorAll("input,select,textarea"));
    const checkPage = (index) => {
      const fields = fieldsInPage(pages[index]);
      for (const field of fields) {
        if (jsonFields.includes(field.id)) {
          const indicator = builder.querySelector('[data-json-feedback="' + field.id + '"]');
          validateJSON(field, indicator, field.id === "id_expected");
        }
        if (!field.checkValidity()) { field.reportValidity(); field.focus(); return false; }
      }
      return true;
    };
    const navigate = (index, enforce = true) => {
      if (index < 0 || index >= pages.length) return;
      if (enforce && index > current) {
        for (let i = current; i < index; i += 1) if (!checkPage(i)) return;
      }
      current = index;
      pages.forEach((page, i) => { page.hidden = i !== index; });
      steps.forEach((step, i) => {
        step.classList.toggle("is-active", i === index);
        step.setAttribute("aria-current", i === index ? "step" : "false");
      });
      back.hidden = index === 0;
      next.hidden = index === pages.length - 1;
      submit.hidden = index !== pages.length - 1;
      counter.textContent = "STEP " + (index + 1) + " OF " + pages.length;
    };
    builder.dataset.enhanced = "true";
    for (const id of jsonFields) {
      const field = document.getElementById(id);
      const feedback = builder.querySelector('[data-json-feedback="' + id + '"]');
      if (field) field.addEventListener("input", () => validateJSON(field, feedback, id === "id_expected"));
    }
    next.addEventListener("click", () => navigate(current + 1));
    back.addEventListener("click", () => navigate(current - 1, false));
    steps.forEach((step, index) => step.addEventListener("click", () => navigate(index)));
    const examples = {
      insufficient: {
        name: "Reject transfer above available balance",
        family: "invalid",
        objective: "A transfer exceeding the available balance must be rejected without changing the balance.",
        input_data: { balance: 100, amount: 150 },
        expected: { status: "reverted", balance: 100 }
      },
      permission: {
        name: "Reject unauthorized withdrawal",
        family: "permission",
        objective: "A viewer must not withdraw assets or change the balance.",
        input_data: { role: "viewer", balance: 100, amount: 25 },
        expected: { status: "reverted", balance: 100 }
      },
      valid: {
        name: "Accept valid transfer",
        family: "valid",
        objective: "A valid transfer must succeed and deduct the transferred amount.",
        input_data: { balance: 100, amount: 25 },
        expected: { status: "success", balance: 75 }
      }
    };
    for (const button of builder.querySelectorAll("[data-preset]")) {
      button.addEventListener("click", () => {
        const data = examples[button.dataset.preset];
        if (!data) return;
        for (const [key, value] of Object.entries(data)) {
          const field = document.getElementById("id_" + key);
          if (!field) continue;
          field.value = typeof value === "object" ? JSON.stringify(value, null, 2) : value;
          field.setCustomValidity("");
          field.dispatchEvent(new Event("input", { bubbles: true }));
        }
      });
    }
    form.addEventListener("submit", (event) => {
      for (let i = 0; i < pages.length; i += 1) {
        if (!checkPage(i)) { event.preventDefault(); navigate(i, false); return; }
      }
    });
    let errorPage = pages.findIndex((page) => page.querySelector(".errorlist"));
    if (errorPage < 0) errorPage = 0;
    navigate(errorPage, false);
  }

  const evidenceForm = document.querySelector("[data-evidence-form]");
  if (evidenceForm) {
    const field = evidenceForm.querySelector("#observed-json");
    const feedback = evidenceForm.querySelector('[data-json-feedback="observed-json"]');
    if (field) {
      field.addEventListener("input", () => validateJSON(field, feedback, true));
      evidenceForm.addEventListener("submit", (event) => {
        if (!validateJSON(field, feedback, true)) { event.preventDefault(); field.reportValidity(); }
      });
    }
  }
})();
