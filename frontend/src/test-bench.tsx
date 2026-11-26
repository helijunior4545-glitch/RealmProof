import {useRef, useState, type FormEvent} from "react";
import {createRoot} from "react-dom/client";

type Outcome = "success" | "rejected";
type Run = {
  inputs: {balance: number; amount: number; authorized: boolean};
  expected: {status: Outcome; balance: number};
  observed: {status: Outcome; balance: number};
  verdict: "passed" | "failed";
  mismatches: string[];
  evidence: {duration_ms: number; source_sha256: string; harness_sha256: string};
};

const presets = [
  {label: "Valid transfer", balance: "100", amount: "25", authorized: true, status: "success", final_balance: "75"},
  {label: "Insufficient balance", balance: "100", amount: "150", authorized: true, status: "rejected", final_balance: "100"},
  {label: "Exact balance", balance: "100", amount: "100", authorized: true, status: "success", final_balance: "0"},
] as const;
type Fields = {balance: string; amount: string; authorized: boolean; status: Outcome; final_balance: string};
const limit = 1_000_000_000_000;
const outcome = (status: Outcome) => status === "success" ? "Accepted" : "Rejected";

function Bench({endpoint, csrf, enabled}: {endpoint: string; csrf: string; enabled: boolean}) {
  const [fields, setFields] = useState<Fields>(presets[0]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const inFlight = useRef(false);
  const [current, previous] = runs;

  function edit<K extends keyof Fields>(key: K, value: Fields[K]) {
    setFields(old => ({...old, [key]: value}));
  }

  async function execute(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (inFlight.current || !enabled) return;
    const body = new FormData(event.currentTarget);
    inFlight.current = true;
    setPending(true);
    setError("");
    try {
      const response = await fetch(endpoint, {method: "POST", headers: {"X-CSRFToken": csrf}, body});
      if (!response.headers.get("content-type")?.includes("application/json")) {
        throw new Error("Could not reach the runner. Reload the page and try again.");
      }
      const result = await response.json();
      if (!response.ok) throw new Error(result.error);
      setRuns(old => [result, ...old.slice(0, 1)]);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not complete the run.");
    } finally {
      inFlight.current = false;
      setPending(false);
    }
  }

  function numberField(key: "balance" | "amount" | "final_balance", label: string) {
    return <label>{label}<input required name={key} type="number" step="1"
      min={key === "amount" ? -limit : 0} max={limit} value={fields[key]}
      onChange={event => edit(key, event.target.value)} /></label>;
  }

  return <>
    <div className="bench-grid">
      <section className="bench-panel">
        <h2><span className="bench-input-icon" aria-hidden="true">▤</span> Scenario</h2>
        <div className="bench-presets" role="group" aria-label="Scenario presets">
          {presets.map(({label, ...preset}) => <button type="button" key={label} disabled={pending}
            aria-pressed={Object.entries(preset).every(([key, value]) => fields[key as keyof Fields] === value)}
            onClick={() => setFields(preset)}>{label}</button>)}
        </div>
        <form onSubmit={execute}>
          <fieldset disabled={pending}>
            <legend>Inputs</legend>
            <div className="bench-fields">
              {numberField("balance", "Initial balance")}
              {numberField("amount", "Transfer amount")}
              <label>Authorization<select name="authorized" value={String(fields.authorized)}
                onChange={event => edit("authorized", event.target.value === "true")}>
                <option value="true">Authorized</option>
                <option value="false">Unauthorized</option>
              </select></label>
            </div>
          </fieldset>
          <fieldset disabled={pending}>
            <legend>Expected behavior</legend>
            <div className="bench-fields">
              <label>Outcome<select name="status" value={fields.status}
                onChange={event => edit("status", event.target.value as Outcome)}>
                <option value="success">Accepted</option>
                <option value="rejected">Rejected</option>
              </select></label>
              {numberField("final_balance", "Remaining balance")}
            </div>
          </fieldset>
          <button className="bench-run" type="submit" disabled={pending || !enabled}>
            <span aria-hidden="true">{pending ? "◌" : "▸"}</span> {pending ? "Running Gno…" : "Run transfer test"}
          </button>
          {!enabled && <p className="bench-muted">Guest execution is unavailable in this deployment.</p>}
          {error && <p className="bench-error" role="alert">{error}</p>}
        </form>
      </section>
      <section className="bench-panel">
        <h2><span className="bench-result-icon" aria-hidden="true">⌁</span> Latest result</h2>
        <p className="bench-run-status" role="status">
          {pending ? "Executing the Gno fixture…" : current ? `Transfer ${outcome(current.observed.status).toLowerCase()} · Test ${current.verdict}` : "Run the scenario to inspect what Gno returns."}
        </p>
        {current && <>
          <p className={`bench-verdict is-${current.verdict}`}>
            <span aria-hidden="true">{current.verdict === "passed" ? "✓" : "×"}</span> Test {current.verdict}
          </p>
          <table className="bench-table">
            <thead><tr><th scope="col">Assertion</th><th scope="col">Expected</th><th scope="col">Observed</th></tr></thead>
            <tbody>
              <tr><th scope="row">Outcome</th><td>{outcome(current.expected.status)}</td><td>{outcome(current.observed.status)} <Check run={current} field="status" /></td></tr>
              <tr><th scope="row">Remaining balance</th><td>{current.expected.balance}</td><td>{current.observed.balance} <Check run={current} field="balance" /></td></tr>
            </tbody>
          </table>
          <details className="bench-evidence"><summary>Execution evidence · {current.evidence.duration_ms} ms</summary>
            <dl>
              <dt>Source SHA-256</dt><dd><code>{current.evidence.source_sha256}</code></dd>
              <dt>Harness SHA-256</dt><dd><code>{current.evidence.harness_sha256}</code></dd>
            </dl>
          </details>
        </>}
      </section>
    </div>
    {current && previous && <section className="bench-panel bench-comparison">
      <h2><span aria-hidden="true">⇄</span> Compare runs</h2>
      <table className="bench-table">
        <thead><tr><th scope="col">Field</th><th scope="col">Previous</th><th scope="col">Latest</th></tr></thead>
        <tbody>{[
          ["Initial balance", previous.inputs.balance, current.inputs.balance],
          ["Transfer amount", previous.inputs.amount, current.inputs.amount],
          ["Authorization", previous.inputs.authorized ? "Authorized" : "Unauthorized", current.inputs.authorized ? "Authorized" : "Unauthorized"],
          ["Outcome", outcome(previous.observed.status), outcome(current.observed.status)],
          ["Remaining balance", previous.observed.balance, current.observed.balance],
          ["Test verdict", previous.verdict, current.verdict],
        ].map(([label, before, after]) => <tr key={label}><th scope="row">{label}</th><td>{before}</td>
          <td className={before === after ? undefined : "bench-changed"}>{after}{before !== after && <span className="bench-sr-only"> (changed)</span>}</td></tr>)}</tbody>
      </table>
    </section>}
  </>;
}

function Check({run, field}: {run: Run; field: string}) {
  const failed = run.mismatches.includes(field);
  return <span className={failed ? "is-failed" : "is-passed"}>
    <span aria-hidden="true">{failed ? "×" : "✓"}</span>
    <span className="bench-sr-only">{failed ? " failed" : " passed"}</span>
  </span>;
}

const host = document.getElementById("rp-test-bench");
const csrf = host?.querySelector<HTMLInputElement>("[name=csrfmiddlewaretoken]")?.value;
if (host?.dataset.endpoint && csrf) {
  createRoot(host).render(<Bench endpoint={host.dataset.endpoint} csrf={csrf} enabled={host.dataset.enabled === "true"} />);
}
