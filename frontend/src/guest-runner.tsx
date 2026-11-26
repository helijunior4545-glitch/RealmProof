import {useRef, useState} from "react";
import {createRoot} from "react-dom/client";

type Outcome = {status: "success" | "rejected"; balance: number; state_changed: boolean};
type Scenario = {id: string; name: string; inputs: {balance: number; amount: number; authorized: boolean}; expected: Outcome};
type Result = {
  observed: Outcome;
  verdict: "passed" | "failed";
  mismatches: string[];
  duration_ms: number;
  source_sha256: string;
  harness_sha256: string;
};

const describe = (status: Outcome["status"]) => status === "success" ? "Accepted" : "Rejected";

function GuestRunner({scenarios, endpoint, csrf, enabled}: {
  scenarios: Scenario[]; endpoint: string; csrf: string; enabled: boolean;
}) {
  const [scenario, select] = useState(scenarios.find(item => item.id === "insufficient") ?? scenarios[0]);
  const [result, setResult] = useState<Result>();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const inFlight = useRef(false);

  function choose(next: Scenario) {
    if (inFlight.current || scenario.id === next.id) return;
    select(next);
    setResult(undefined);
    setError("");
  }

  async function run() {
    if (!enabled || inFlight.current) return;
    inFlight.current = true;
    setPending(true);
    setResult(undefined);
    setError("");
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {"X-CSRFToken": csrf},
        body: new URLSearchParams({scenario: scenario.id}),
      });
      if (!response.headers.get("content-type")?.includes("application/json")) {
        setError("Could not reach the runner. Reload the page and try again.");
        return;
      }
      const payload = await response.json();
      if (response.ok) setResult(payload);
      else setError(payload.error);
    } catch {
      setError("Could not connect to the runner. Try again.");
    } finally {
      inFlight.current = false;
      setPending(false);
    }
  }

  const rows = [
    {label: "Outcome", key: "status", expected: describe(scenario.expected.status), observed: result && describe(result.observed.status)},
    {label: "Remaining balance", key: "balance", expected: scenario.expected.balance, observed: result?.observed.balance},
    {label: "State changed", key: "state_changed", expected: scenario.expected.state_changed ? "Yes" : "No",
      observed: result && (result.observed.state_changed ? "Yes" : "No")},
  ];

  return <div className="lp-runner">
    <div className="lp-scenarios" role="group" aria-label="Scenarios">
      <span>Scenarios</span>
      {scenarios.map(item => <button key={item.id} type="button" disabled={pending} aria-pressed={scenario.id === item.id}
        onClick={() => choose(item)}><i className="lp-icon lp-file" aria-hidden="true" />{item.name}</button>)}
    </div>
    <div className="lp-run-panel">
      <dl className="lp-inputs">
        <div><dt>Initial balance</dt><dd>{scenario.inputs.balance}</dd></div>
        <div><dt>Amount</dt><dd>{scenario.inputs.amount}</dd></div>
        <div><dt>Sender</dt><dd>{scenario.inputs.authorized ? "Authorized" : "Unauthorized"}</dd></div>
      </dl>
      <button className="lp-run-button" type="button" disabled={pending || !enabled} onClick={run}>
        <i className={`lp-icon ${pending ? "lp-spinner" : "lp-terminal"}`} aria-hidden="true" />
        {pending ? "Running in Gno…" : "Run scenario"}
      </button>
      <div className="lp-result" role="status" aria-label="Execution result">
        {result && <>
          <span className={result.observed.status === "rejected" ? "lp-rejected" : "lp-passed"}>
            <i className={`lp-icon ${result.observed.status === "rejected" ? "lp-warning" : "lp-shield"}`} aria-hidden="true" />
            Transfer {describe(result.observed.status).toLowerCase()}
          </span>
          <span className={result.verdict === "passed" ? "lp-passed" : "lp-failed"}>
            <i className={`lp-icon ${result.verdict === "passed" ? "lp-shield" : "lp-warning"}`} aria-hidden="true" />
            Test {result.verdict}
          </span>
        </>}
      </div>
      {error && <p className="lp-error" role="alert">{error}</p>}
      {!enabled && <p className="lp-message">Public execution is unavailable on this deployment.</p>}
      <table className="lp-compare">
        <thead><tr><th scope="col">Assertion</th><th scope="col">Expected</th><th scope="col">Observed</th></tr></thead>
        <tbody>{rows.map(row => <tr key={row.key}><th scope="row">{row.label}</th><td>{row.expected}</td>
          <td className={result?.mismatches.includes(row.key) ? "lp-failed" : undefined}>{row.observed ?? "—"}</td></tr>)}</tbody>
      </table>
      {result && <details className="lp-fingerprints">
        <summary>Execution evidence <span>{result.duration_ms} ms</span></summary>
        <dl><dt>Source SHA-256</dt><dd>{result.source_sha256}</dd><dt>Harness SHA-256</dt><dd>{result.harness_sha256}</dd></dl>
      </details>}
    </div>
  </div>;
}

const host = document.getElementById("lp-runner");
const csrf = host?.querySelector<HTMLInputElement>("[name=csrfmiddlewaretoken]")?.value;
const data = document.getElementById("lp-scenarios")?.textContent;
if (host?.dataset.endpoint && csrf && data) {
  const scenarios: Scenario[] = JSON.parse(data);
  if (scenarios.length) {
    createRoot(host).render(<GuestRunner scenarios={scenarios} endpoint={host.dataset.endpoint} csrf={csrf}
      enabled={host.dataset.enabled === "true"} />);
  }
}
