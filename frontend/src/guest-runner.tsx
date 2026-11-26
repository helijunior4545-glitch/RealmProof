import {useEffect, useRef, useState} from "react";
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

function GuestRunner({scenarios, endpoint, csrf, enabled, selected, initialResult, initialError}: {
  scenarios: Scenario[]; endpoint: string; csrf: string; enabled: boolean; selected?: string;
  initialResult: Result | null; initialError: string | null;
}) {
  const [scenario, select] = useState(scenarios.find(item => item.id === selected) ?? scenarios[0]);
  const [result, setResult] = useState<Result | undefined>(initialResult ?? undefined);
  const [showLive, setShowLive] = useState(Boolean(initialResult || initialError));
  const [reportView, setReportView] = useState("Trace");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState(initialError ?? "");
  const inFlight = useRef(false);

  useEffect(() => {
    const showBrowserDemo = () => setShowLive(false);
    document.addEventListener("realmproof:browser-demo", showBrowserDemo);
    return () => document.removeEventListener("realmproof:browser-demo", showBrowserDemo);
  }, []);

  function choose(next: Scenario) {
    if (inFlight.current || scenario.id === next.id) return;
    setShowLive(true);
    select(next);
    setResult(undefined);
    setError("");
  }

  async function run() {
    if (!enabled || inFlight.current) return;
    inFlight.current = true;
    setShowLive(true);
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

  const displayed = result?.observed ?? scenario.expected;
  const executionSteps = <ol className="lp-execution-lines">
    <li><b>call</b><code>Transfer({scenario.inputs.balance}, {scenario.inputs.amount}, {String(scenario.inputs.authorized)})</code></li>
    <li><b>expect</b><code>{scenario.expected.status} · balance {scenario.expected.balance}</code></li>
    <li><b>{result ? "return" : "example"}</b><code>{displayed.status} · balance {displayed.balance}</code></li>
    <li><b>verify</b><code>{result ? `Test ${result.verdict}` : "Run to verify expectations"}</code></li>
  </ol>;

  return <>
  <div className="lp-runner lp-demo-stack">
    <section className="lp-scenarios lp-demo-card" aria-label="Scenarios">
      <h3><i className="lp-icon lp-file" aria-hidden="true" /> Scenarios ({scenarios.length})</h3>
      {scenarios.map(item => <button key={item.id} type="button" disabled={pending} aria-pressed={scenario.id === item.id}
        onClick={() => choose(item)}><i className={`lp-icon ${item.expected.status === "rejected" ? "lp-warning" : "lp-shield"}`} aria-hidden="true" />{item.name}</button>)}
    </section>
    <section className="lp-run-panel lp-demo-card" aria-labelledby="lp-demo-report-title">
      <h3 id="lp-demo-report-title"><i className="lp-icon lp-file" aria-hidden="true" /> Report</h3>
      <p className="lp-demo-mode">{pending ? "Running in Gno…" : result ? "Observed run" : "Example · expected values"}</p>
      <div className="lp-demo-summary">
        <div className="lp-result" role="status" aria-label="Execution result">
          <span className={displayed.status === "rejected" ? "lp-rejected" : "lp-passed"}>
            <i className={`lp-icon ${displayed.status === "rejected" ? "lp-warning" : "lp-shield"}`} aria-hidden="true" />
            {result ? "Transfer" : "Expected"} {describe(displayed.status).toLowerCase()}
          </span>
          <span className={result?.verdict === "failed" ? "lp-failed" : "lp-passed"}>
            <i className="lp-icon lp-shield" aria-hidden="true" />
            {result ? `Test ${result.verdict}` : "Awaiting run"}
          </span>
        </div>
        <dl className="lp-demo-balance" aria-label="Remaining balance">
          <div><dt>Expected</dt><dd>{scenario.expected.balance}</dd></div>
          <div><dt>Observed</dt><dd>{result?.observed.balance ?? "—"}</dd></div>
        </dl>
      </div>
      <button className="lp-run-button" type="button" disabled={pending || !enabled} onClick={run}>
        <i className={`lp-icon ${pending ? "lp-spinner" : "lp-terminal"}`} aria-hidden="true" />
        {pending ? "Running in Gno…" : "Run scenario"}
      </button>
      {error && <p className="lp-error" role="alert">{error}</p>}
      {!enabled && <p className="lp-message">Public execution is unavailable on this deployment.</p>}
    </section>
    <section className="lp-demo-card lp-demo-trace" aria-labelledby="lp-demo-trace-title">
      <h3 id="lp-demo-trace-title"><i className="lp-icon lp-terminal" aria-hidden="true" /> Trace <small>Execution summary</small></h3>
      {executionSteps}
    </section>
  </div>
  {showLive && workflowHost && createPortal(<div className="lp-workflow-grid">
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
  {showLive && reportHost && createPortal(<div className="lp-deck lp-report">
    <h3><i className="lp-icon lp-file" aria-hidden="true" /> Execution report <small>Local Gno</small></h3>
    <div className="lp-report-highlight">
      <div>
        <strong className={displayed.status === "rejected" ? "lp-rejected" : "lp-passed"}>
          <i className={`lp-icon ${displayed.status === "rejected" ? "lp-warning" : "lp-shield"}`} aria-hidden="true" />
          {result ? "Transfer" : "Expected"} {describe(displayed.status).toLowerCase()}
        </strong>
        <small>{result ? `Test ${result.verdict}` : "Example · expected values"}</small>
      </div>
      <dl className="lp-demo-balance" aria-label="Report balance comparison">
        <div><dt>Expected</dt><dd>{scenario.expected.balance}</dd></div>
        <div><dt>Observed</dt><dd>{result?.observed.balance ?? "—"}</dd></div>
      </dl>
    </div>
    <div className="lp-report-switch" role="group" aria-label="Report view">
      {["Trace", "State", "Diff", "Evidence"].map(view => <button type="button" key={view} aria-pressed={reportView === view}
        onClick={() => setReportView(view)}>{view}</button>)}
    </div>
    {reportView === "Trace" && executionSteps}
    {reportView === "State" && <dl className="lp-scenario-code">
      <dt>Initial balance</dt><dd>{scenario.inputs.balance}</dd>
      <dt>Expected balance</dt><dd>{scenario.expected.balance}</dd>
      <dt>Observed balance</dt><dd>{result?.observed.balance ?? "Awaiting run"}</dd>
    </dl>}
    {reportView === "Diff" && <dl className="lp-scenario-code">
      {rows.map(row => <div className="lp-diff-row" key={row.key}>
        <dt>{row.label}</dt><dd>{row.expected} → {row.observed ?? "—"}</dd>
      </div>)}
    </dl>}
    {reportView === "Evidence" && (result ?
      <dl className="lp-fingerprints"><dt>Source SHA-256</dt><dd>{result.source_sha256}</dd>
        <dt>Harness SHA-256</dt><dd>{result.harness_sha256}</dd><dt>Duration</dt><dd>{result.duration_ms} ms</dd></dl> :
      <p>Run the selected scenario to generate fingerprints.</p>)}
  </div>, reportHost)}
  </>;
}

const host = document.getElementById("lp-demo-runner");
const csrf = host?.querySelector<HTMLInputElement>("[name=csrfmiddlewaretoken]")?.value;
const data = document.getElementById("lp-scenarios")?.textContent;
if (host?.dataset.endpoint && csrf && data) {
  const scenarios: Scenario[] = JSON.parse(data);
  if (scenarios.length) {
    createRoot(host).render(<GuestRunner scenarios={scenarios} endpoint={host.dataset.endpoint} csrf={csrf}
      enabled={host.dataset.enabled === "true"} selected={host.dataset.selected}
      initialResult={JSON.parse(document.getElementById("lp-initial-result")?.textContent ?? "null")}
      initialError={JSON.parse(document.getElementById("lp-initial-error")?.textContent ?? "null")} />);
  }
}
