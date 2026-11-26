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

const browserDemo = document.getElementById("lp-browser-demo");
const simulationStatus = document.getElementById("lp-simulation-status");
const demoPresets = {
  insufficient: {amount: 150, authorized: true, outcome: "Rejected", balance: 100},
  valid: {amount: 25, authorized: true, outcome: "Accepted", balance: 75},
  exact: {amount: 100, authorized: true, outcome: "Accepted", balance: 0},
  permission: {amount: 25, authorized: false, outcome: "Rejected", balance: 100},
};

if (browserDemo && simulationStatus) {
  const scenario = browserDemo.elements.namedItem("scenario");
  const amountField = browserDemo.elements.namedItem("amount");
  const initialBalance = 100;
  browserDemo.hidden = false;

  scenario.addEventListener("change", () => {
    amountField.value = demoPresets[scenario.value].amount;
  });

  browserDemo.addEventListener("submit", event => {
    event.preventDefault();
    const preset = demoPresets[scenario.value];
    const amount = amountField.valueAsNumber;
    const accepted = preset.authorized && amount > 0 && amount <= initialBalance;
    const resultBalance = accepted ? initialBalance - amount : initialBalance;
    const outcome = accepted ? "Accepted" : "Rejected";
    const expectedChanged = preset.balance !== initialBalance ? "Yes" : "No";
    const actualChanged = resultBalance !== initialBalance ? "Yes" : "No";
    const matches = {
      Outcome: outcome === preset.outcome,
      Balance: resultBalance === preset.balance,
      Changed: actualChanged === expectedChanged,
    };
    const verdict = Object.values(matches).every(Boolean) ? "Test passed" : "Test failed";
    const operation = "Transfer " + outcome.toLowerCase();
    const values = {
      scenarioName: scenario.selectedOptions[0].textContent,
      amount,
      expectedOutcome: preset.outcome,
      expectedBalance: preset.balance,
      expectedChanged,
      actualOutcome: outcome,
      actualBalance: resultBalance,
      actualChanged,
      operation,
      verdict,
      mode: "Browser simulation",
      outputLabel: "Simulated",
      traceLabel: "simulate",
      call: `Transfer(${initialBalance}, ${amount}, ${preset.authorized})`,
      expectedTrace: `${preset.outcome.toLowerCase()} · balance ${preset.balance}`,
      actualTrace: `${outcome.toLowerCase()} · balance ${resultBalance}`,
      balanceChange: resultBalance - initialBalance,
    };

    for (const cell of document.querySelectorAll("[data-demo-value]")) {
      cell.textContent = values[cell.dataset.demoValue];
    }
    for (const cell of document.querySelectorAll("[data-demo-match]")) {
      const match = matches[cell.dataset.demoMatch];
      cell.textContent = match ? "Match" : "Mismatch";
      cell.classList.toggle("lp-passed", match);
      cell.classList.toggle("lp-failed", !match);
    }
    const operationBadge = exampleReport.querySelector("[data-demo-value=operation]").parentElement;
    operationBadge.classList.toggle("lp-passed", accepted);
    operationBadge.classList.toggle("lp-rejected", !accepted);
    operationBadge.querySelector(".lp-icon").classList.toggle("lp-shield", accepted);
    operationBadge.querySelector(".lp-icon").classList.toggle("lp-warning", !accepted);

    document.dispatchEvent(new Event("realmproof:browser-demo"));
    // Reveal the simulation even if the browser still has an older React bundle.
    for (const panel of document.querySelectorAll(".lp-examples")) {
      panel.classList.add("lp-show-browser-demo");
    }
    simulationStatus.hidden = false;
    simulationStatus.textContent = `${operation} · ${verdict} · Remaining balance ${resultBalance}`;
  });

  document.getElementById("lp-demo-runner")?.addEventListener("click", () => {
    for (const panel of document.querySelectorAll(".lp-show-browser-demo")) {
      panel.classList.remove("lp-show-browser-demo");
    }
    simulationStatus.hidden = true;
  });
}

// Delegation keeps the same controls working when the live report replaces the example.
function activateWorkflowStage(event) {
  if (event.type === "pointerover" && event.pointerType !== "mouse") return;
  const button = event.target.closest("button[data-workflow-stage]");
  if (!button || button.getAttribute("aria-pressed") === "true") return;
  const workflow = button.closest("[data-workflow-stages]");
  for (const control of workflow.querySelectorAll("button[data-workflow-stage]")) {
    const active = control === button;
    control.setAttribute("aria-pressed", String(active));
    document.getElementById(control.getAttribute("aria-controls")).hidden = !active;
  }
}
for (const eventName of ["pointerover", "focusin", "click"]) {
  document.addEventListener(eventName, activateWorkflowStage);
}
