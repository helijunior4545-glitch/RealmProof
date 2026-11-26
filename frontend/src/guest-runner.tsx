import {useRef, useState} from "react";
import {createPortal} from "react-dom";
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

const workflowHost = document.getElementById("lp-workflow-live");
const reportHost = document.getElementById("lp-report-live");
const describe = (status: Outcome["status"]) => status === "success" ? "Accepted" : "Rejected";

function GuestRunner({scenarios, endpoint, csrf, enabled}: {
  scenarios: Scenario[]; endpoint: string; csrf: string; enabled: boolean;
}) {
  const [scenario, select] = useState(scenarios.find(item => item.id === "insufficient") ?? scenarios[0]);
  const [result, setResult] = useState<Result>();
  const [reportView, setReportView] = useState("Overview");
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

  return <>
  <div className="lp-runner">
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
      <p className="lp-run-note">Compare the expected and observed values in the <a href="#workflow">workflow</a>.</p>
    </div>
  </div>
  {workflowHost && createPortal(<div className="lp-workflow-grid">
    <div className="lp-deck">
      <h3><i className="lp-icon lp-file" aria-hidden="true" /> Scenario</h3>
      <p>{scenario.name}</p>
      <dl className="lp-scenario-code">
        <dt>Initial balance</dt><dd>{scenario.inputs.balance}</dd>
        <dt>Amount</dt><dd>{scenario.inputs.amount}</dd>
        <dt>Sender</dt><dd>{scenario.inputs.authorized ? "Authorized" : "Unauthorized"}</dd>
        <dt>Expect</dt><dd>{describe(scenario.expected.status)}</dd>
      </dl>
    </div>
    <div className="lp-workflow-output">
      <ol className="lp-stage">
        <li><i className="lp-icon lp-terminal" aria-hidden="true" /><div><strong>Execute</strong><small>{pending ? "Running locally" : "Local Gno"}</small></div></li>
        <li><i className="lp-icon lp-file" aria-hidden="true" /><div><strong>Observe</strong><small>{result ? "Result available" : "Capture output"}</small></div></li>
        <li><i className="lp-icon lp-shield" aria-hidden="true" /><div><strong>Compare</strong><small>{result ? `Test ${result.verdict}` : "Check expectations"}</small></div></li>
      </ol>
      <div className="lp-deck">
        <h3>State comparison</h3>
        <table className="lp-compare">
          <thead><tr><th scope="col">Assertion</th><th scope="col">Expected</th><th scope="col">Observed</th><th scope="col">Result</th></tr></thead>
          <tbody>{rows.map(row => {
            const failed = result?.mismatches.includes(row.key);
            return <tr key={row.key}><th scope="row">{row.label}</th><td>{row.expected}</td><td>{row.observed ?? "—"}</td>
              <td className={result ? (failed ? "lp-failed" : "lp-passed") : undefined}>{result ? (failed ? "Mismatch" : "Match") : "—"}</td></tr>;
          })}</tbody>
        </table>
      </div>
    </div>
  </div>, workflowHost)}
  {reportHost && createPortal(<div className="lp-deck lp-report">
    <h3><i className="lp-icon lp-file" aria-hidden="true" /> Execution report <small>Local Gno</small></h3>
    <div className="lp-report-switch" role="group" aria-label="Report view">
      {["Overview", "Evidence"].map(view => <button type="button" key={view} aria-pressed={reportView === view}
        onClick={() => setReportView(view)}>{view}</button>)}
    </div>
    {!result ? <p>Run the selected scenario to populate this report.</p> : reportView === "Overview" ?
      <dl className="lp-scenario-code">
        <dt>Scenario</dt><dd>{scenario.name}</dd>
        <dt>Transfer</dt><dd>{describe(result.observed.status)}</dd>
        <dt>Test</dt><dd>{result.verdict}</dd>
        <dt>Duration</dt><dd>{result.duration_ms} ms</dd>
      </dl> :
      <dl className="lp-fingerprints"><dt>Source SHA-256</dt><dd>{result.source_sha256}</dd>
        <dt>Harness SHA-256</dt><dd>{result.harness_sha256}</dd></dl>}
  </div>, reportHost)}
  </>;
}

const host = document.getElementById("lp-runner");
const csrf = host?.querySelector<HTMLInputElement>("[name=csrfmiddlewaretoken]")?.value;
const data = document.getElementById("lp-scenarios")?.textContent;
if (host?.dataset.endpoint && csrf && data) {
  const scenarios: Scenario[] = JSON.parse(data);
  if (scenarios.length) {
    workflowHost?.replaceChildren();
    reportHost?.replaceChildren();
    createRoot(host).render(<GuestRunner scenarios={scenarios} endpoint={host.dataset.endpoint} csrf={csrf}
      enabled={host.dataset.enabled === "true"} />);
  }
}
