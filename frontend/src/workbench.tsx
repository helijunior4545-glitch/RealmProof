import { useEffect, useRef, useState, type FormEvent } from "react";
import { createRoot } from "react-dom/client";

type Fields = Record<string, unknown>;
type Scenario = { id: string; name: string; family: string; objective: string; inputs: Fields; expected: Fields; execute: string };
type Run = {
  id: string; scenario: string; name: string; status: string; execution: string; started: string;
  reason: string; inputs: Fields; expected: Fields; observed: Fields; mismatches: Fields;
  duration: number | null; digest: string | null; report: string; download: string | null;
};
type WorkbenchData = { scenarios: Scenario[]; runs: Run[]; canWrite: boolean; history: string; suite: string; catalog: string; universal: string; create: string; network: string; ledger: string; icons: Record<string, string> };
type ResponseData = { error?: string; run?: Run; runs?: Run[]; queued?: number };
const tabs = ["Configure", "Result", "Compare", "History", "Suites"] as const;
type Tab = typeof tabs[number];
type Selection = { tab: Tab; scenario: string; run: string };

const fieldNames: Record<string, string> = { status: "Transfer outcome", balance: "Remaining balance", state_changed: "State changed" };
const executionNames: Record<string, string> = { local_error: "Execution unavailable", local_running: "Execution in progress", queued: "Queued", external_evidence: "User-supplied evidence", not_executed: "No execution recorded", local_gno: "Local Gno CLI" };
const statusNames: Record<string, string> = { passed: "Passed", failed: "Failed", inconclusive: "Inconclusive", pending: "Pending", error: "Infrastructure error" };

function display(value: unknown): string {
  if (value === undefined) return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function readSelection(data: WorkbenchData): Selection {
  const params = new URLSearchParams(window.location.search);
  const run = data.runs.find(item => item.id === params.get("run"));
  return {
    tab: tabs.find(item => item.toLowerCase() === params.get("view")) ?? "Configure",
    scenario: params.get("scenario") ?? run?.scenario ?? data.scenarios[0]?.id ?? "",
    run: run?.id ?? "",
  };
}

function runTime(run: Run) {
  return new Date(run.started).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function Verdict({ run }: { run: Run }) {
  return <span className="wb-verdict" data-status={run.status}>{statusNames[run.status] ?? run.status}</span>;
}

function FieldsList({ title, fields }: { title: string; fields: Fields }) {
  return <div className="wb-subpanel">
    <h3>{title}</h3>
    <dl className="wb-fields">{Object.entries(fields).map(([key, value]) =>
      <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{display(value)}</dd></div>)}</dl>
    {!Object.keys(fields).length && <p>No values recorded.</p>}
  </div>;
}

function Configuration({ scenario, writable, busy, arrow, submit }: {
  scenario: Scenario; writable: boolean; busy: boolean; arrow: string; submit: (url: string, payload: Fields) => Promise<void>;
}) {
  const transfer = scenario.inputs.engine === "transfer";
  const editable = transfer && [scenario.inputs.balance, scenario.inputs.amount, scenario.expected.balance].every(value => typeof value === "number")
    && typeof scenario.inputs.authorized === "boolean" && typeof scenario.expected.state_changed === "boolean"
    && (scenario.expected.status === "success" || scenario.expected.status === "rejected");
  const [formError, setFormError] = useState("");
  const [revision, setRevision] = useState(0);

  function run(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError("");
    const form = new FormData(event.currentTarget);
    const payload: Fields = {};
    if (editable) {
      payload.draft = {
        balance: Number(form.get("balance")), amount: Number(form.get("amount")), remaining: Number(form.get("remaining")),
        authorized: form.get("authorized") === "yes", changed: form.get("changed") === "yes", outcome: form.get("outcome"),
      };
    } else if (!transfer) {
      try {
        const observed: unknown = JSON.parse(String(form.get("observed")));
        if (!observed || typeof observed !== "object" || Array.isArray(observed)) throw new Error();
        payload.observed = observed;
      } catch {
        setFormError("Enter observed evidence as a valid JSON object.");
        return;
      }
    }
    void submit(scenario.execute, payload);
  }

  const numeric = (label: string, name: string, value: unknown, min = 0) => <label>{label}
    <input name={name} type="number" step="1" min={min} max={1e12} required defaultValue={String(value)} />
  </label>;
  const boolean = (label: string, name: string, value: unknown) => <label>{label}
    <select name={name} defaultValue={value ? "yes" : "no"}><option value="yes">Yes</option><option value="no">No</option></select>
  </label>;

  return <>
    <div className="wb-panel-title">
      <div><span className="wb-label">{scenario.family}</span><h2>{scenario.name}</h2><p>{scenario.objective}</p></div>
      <span className="wb-engine">{transfer ? "Local Gno CLI" : "External evidence"}</span>
    </div>
    <form key={revision} onSubmit={run}>
      {editable ? <div className="wb-form-grid">
        <fieldset className="wb-subpanel" disabled={!writable || busy}>
          <legend>Execution inputs</legend>
          {numeric("Initial balance", "balance", scenario.inputs.balance)}
          {numeric("Transfer amount", "amount", scenario.inputs.amount, -1e12)}
          {boolean("Sender authorized", "authorized", scenario.inputs.authorized)}
        </fieldset>
        <fieldset className="wb-subpanel" disabled={!writable || busy}>
          <legend>Expected behavior</legend>
          <label>Transfer outcome<select name="outcome" defaultValue={String(scenario.expected.status)}>
            <option value="success">Accepted</option><option value="rejected">Rejected</option>
          </select></label>
          {numeric("Remaining balance", "remaining", scenario.expected.balance)}
          {boolean("State changed", "changed", scenario.expected.state_changed)}
        </fieldset>
      </div> : <div className="wb-form-grid">
        <FieldsList title="Saved inputs" fields={scenario.inputs} />
        <FieldsList title="Expected behavior" fields={scenario.expected} />
      </div>}
      {!transfer && <label className="wb-payload">Observed evidence (JSON)
        <textarea name="observed" placeholder="{}" rows={5} required disabled={!writable || busy} />
      </label>}
      {formError && <p className="wb-error" role="alert">{formError}</p>}
      <div className="wb-actions">
        {writable ? <>
          <button className="wb-primary" disabled={busy}>{busy ? "Running…" : transfer ? "Run scenario" : "Evaluate evidence"} <img className="wb-arrow" alt="" src={arrow} /></button>
          {editable && <button type="button" disabled={busy} onClick={() => setRevision(revision + 1)}>Reset inputs</button>}
        </> : <p>Read-only access. An editor can run scenarios.</p>}
        {transfer && <small>Drafts apply to this run. Execution takes place off-chain.</small>}
      </div>
    </form>
  </>;
}

function Assertions({ run }: { run: Run }) {
  const keys = Object.keys(run.expected);
  if (!keys.length) return <p>This run has no saved assertions.</p>;
  return <div className="wb-table-wrap" tabIndex={0} role="region" aria-label="Assertion results">
    <table><thead><tr><th>Assertion</th><th>Expected</th><th>Observed</th><th>Result</th></tr></thead>
      <tbody>{keys.map(key => {
        const observed = run.observed[key];
        const mismatch = Object.hasOwn(run.mismatches, key);
        return <tr key={key}><th scope="row">{fieldNames[key] ?? key}</th>
          <td>{display(run.expected[key])}</td><td>{display(observed)}</td>
          <td>{(run.status === "pending" || run.status === "error") ? "—" :
            <span className={mismatch ? "wb-negative" : "wb-positive"}>{mismatch ? "Mismatch" : "Match"}</span>}</td>
        </tr>;
      })}</tbody>
    </table>
  </div>;
}

function Result({ run }: { run: Run }) {
  const details = useRef<HTMLDialogElement>(null);
  const outcome = run.execution === "local_gno" && (run.observed.status === "success" || run.observed.status === "rejected")
    ? (run.observed.status === "success" ? "Transfer accepted" : "Transfer rejected") : null;
  return <>
    <div className="wb-panel-title"><div><span className="wb-label">Execution report</span><h2>{run.name}</h2><p>{runTime(run)}</p></div><Verdict run={run} /></div>
    <div className="wb-result-meta"><span>{outcome ?? executionNames[run.execution] ?? run.execution.replaceAll("_", " ")}</span><span>{run.duration === null ? "—" : `${run.duration} ms`}</span></div>
    {run.reason && <p>{run.reason}</p>}
    <Assertions run={run} />
    <div className="wb-actions">
      <button type="button" onClick={() => details.current?.showModal()}>Inspect evidence</button>
      <a href={run.report}>Full report</a>
      {run.download && <a href={run.download}>Download JSON</a>}
    </div>
    <dialog className="wb-dialog" ref={details} aria-labelledby="wb-evidence-title">
      <div className="wb-panel-title"><h2 id="wb-evidence-title">Execution evidence</h2>
        <form method="dialog"><button autoFocus aria-label="Close evidence">Close</button></form>
      </div>
      {run.digest && <div className="wb-subpanel"><h3>Report SHA-256</h3><code>{run.digest}</code></div>}
      <FieldsList title="Input snapshot" fields={run.inputs} />
      <FieldsList title="Observed values" fields={run.observed} />
    </dialog>
  </>;
}

function Compare({ runs }: { runs: Run[] }) {
  const comparable = runs.filter(run => run.status !== "error" && run.status !== "pending" && Object.keys(run.observed).length);
  const [baseline, setBaseline] = useState("");
  const [candidate, setCandidate] = useState("");
  const first = comparable.find(run => run.id === baseline) ?? comparable[1];
  const second = comparable.find(run => run.id === candidate) ?? comparable[0];
  const keys = first && second ? [...new Set([...Object.keys(first.observed), ...Object.keys(second.observed)])] : [];

  return <>
    <div className="wb-panel-title"><div><span className="wb-label">Regression analysis</span><h2>Compare runs</h2><p>Inspect changes in observed values across two saved executions.</p></div></div>
    {!first || !second ? <div className="wb-empty">Run two scenarios with recorded evidence to enable comparisons.</div> : <>
      <div className="wb-form-grid wb-compare-controls">
        {([["Baseline", first, setBaseline], ["Candidate", second, setCandidate]] as const).map(([label, run, select]) => <label key={label}>{label}
          <select value={run.id} onChange={event => select(event.target.value)}>{comparable.map(item =>
            <option key={item.id} value={item.id}>{item.name} · {runTime(item)} · {item.id.slice(0, 8)}</option>)}</select>
        </label>)}
      </div>
      {first.id === second.id ? <p className="wb-empty">Choose two different runs.</p> : <div className="wb-table-wrap" tabIndex={0} role="region" aria-label="Difference between runs">
        <table><thead><tr><th>Observed field</th><th>Baseline <Verdict run={first} /></th><th>Candidate <Verdict run={second} /></th><th>Difference</th></tr></thead>
          <tbody>{keys.map(key => {
            const left = first.observed[key], right = second.observed[key];
            return <tr key={key}><th scope="row">{fieldNames[key] ?? key}</th><td>{display(left)}</td><td>{display(right)}</td>
              <td>{JSON.stringify(left) === JSON.stringify(right) ? "Unchanged" : <span className="wb-changed">Changed</span>}</td></tr>;
          })}</tbody>
        </table>
      </div>}
    </>}
  </>;
}

function Workbench({ data, csrf }: { data: WorkbenchData; csrf: string }) {
  const [selection, setSelection] = useState(() => readSelection(data));
  const [runs, setRuns] = useState(data.runs);
  const [search, setSearch] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const activeRequest = useRef(false);
  const scenario = data.scenarios.find(item => item.id === selection.scenario) ?? data.scenarios[0];
  const result = runs.find(item => item.id === selection.run) ?? runs.find(item => item.scenario === scenario?.id);
  const visible = data.scenarios.filter(item => `${item.name} ${item.family}`.toLowerCase().includes(search.trim().toLowerCase()));

  useEffect(() => {
    const restore = () => setSelection(readSelection({ ...data, runs }));
    window.addEventListener("popstate", restore);
    return () => window.removeEventListener("popstate", restore);
  }, [data, runs]);

  function navigate(tab: Tab, scenarioId = scenario?.id ?? "", runId = "") {
    const url = new URL(window.location.href);
    url.searchParams.set("view", tab.toLowerCase());
    if (scenarioId) url.searchParams.set("scenario", scenarioId);
    if (runId) url.searchParams.set("run", runId);
    else url.searchParams.delete("run");
    if (url.href !== window.location.href) window.history.pushState(null, "", url);
    setSelection({ tab, scenario: scenarioId, run: runId });
  }

  async function request(url: string, payload?: Fields) {
    if (activeRequest.current) return;
    activeRequest.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const response = await fetch(url, payload === undefined ? {
        headers: { Accept: "application/json" },
      } : {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json", "X-CSRFToken": csrf },
        body: JSON.stringify(payload),
      });
      if (!response.headers.get("Content-Type")?.includes("application/json")) {
        throw new Error("The workspace could not complete the request. Reload the page and try again.");
      }
      const body: ResponseData = await response.json();
      if (!response.ok) throw new Error(body.error ?? "The request failed.");
      const run = body.run;
      if (run) {
        setRuns(current => [run, ...current.filter(item => item.id !== run.id)]);
        navigate("Result", run.scenario, run.id);
        setNotice("Run recorded.");
      }
      if (body.runs) {
        setRuns(body.runs);
        setNotice(body.queued === undefined ? "Run history updated." :
          body.queued ? `${body.queued} runs queued for the background worker.` : "No new runs queued. The suite may already be pending.");
      }
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "The request failed.");
    } finally {
      activeRequest.current = false;
      setBusy(false);
    }
  }

  const tools = [
    ["Native test catalog", "Explore native Gno test packs.", data.catalog, "file-code"],
    ["Universal test engine", "Run predefined verification suites.", data.universal, "terminal-window"],
    ["Network explorer", "Inspect chain status and source.", data.network, "arrow-square-out"],
    ["Ledger validation lab", "Check ledger evidence and commitments.", data.ledger, "shield-check"],
  ];

  return <div className="wb-layout">
    <aside className="wb-panel wb-library" aria-labelledby="wb-library-title">
      <div className="wb-library-header"><div><span className="wb-label">Test library</span><h2 id="wb-library-title">Scenarios</h2></div><span className="wb-count">{data.scenarios.length}</span></div>
      <label className="wb-search"><span>Filter scenarios</span><input type="search" placeholder="Search by name or category" value={search} onChange={event => setSearch(event.target.value)} /></label>
      <div className="wb-scenarios">{visible.map(item =>
        <button key={item.id} type="button" className="wb-scenario" aria-pressed={scenario?.id === item.id}
          onClick={() => navigate("Configure", item.id)}>
          <img alt="" src={data.icons[item.inputs.engine === "transfer" ? "terminal-window" : "file-code"]} />
          <span><strong>{item.name}</strong><small>{item.family}</small></span>
        </button>)}
        {!visible.length && <p className="wb-empty">{search ? "No matching scenarios." : "This project has no scenarios yet."}</p>}
      </div>
      {data.canWrite && <a className="wb-new" href={data.create}>+ New scenario</a>}
    </aside>
    <section className="wb-panel wb-console" aria-label="Test console">
      <nav className="wb-tabs" aria-label="Workbench views">{tabs.map(tab =>
        <button key={tab} type="button" aria-pressed={selection.tab === tab}
          onClick={() => navigate(tab, scenario?.id, tab === "Result" ? result?.id : "")}>{tab}</button>)}</nav>
      <div className="wb-console-body" aria-busy={busy}>
        {error && <p role="alert" className="wb-error">{error}</p>}
        <div role="status" className={notice ? "wb-notice" : "wb-silent"}>{notice}</div>
        <div hidden={selection.tab !== "Configure"}>{scenario ?
          <Configuration key={scenario.id} scenario={scenario} writable={data.canWrite} busy={busy} arrow={data.icons["arrow-right"]} submit={request} /> :
          <p className="wb-empty">Create a scenario to start testing.</p>}</div>
        {selection.tab === "Result" && (result ? <Result key={result.id} run={result} /> :
          <p className="wb-empty">Run the selected scenario to see its verdict and evidence.</p>)}
        {selection.tab === "Compare" && <Compare runs={runs} />}
        {selection.tab === "History" && <>
          <div className="wb-panel-title"><div><span className="wb-label">Recorded evidence</span><h2>Run history</h2><p>Recent executions in this project.</p></div>
            <button type="button" disabled={busy} onClick={() => void request(data.history)}>Refresh runs</button>
          </div>
          {runs.length ? <ul className="wb-history">{runs.map(run => <li key={run.id}>
            <button type="button" onClick={() => navigate("Result", run.scenario, run.id)}><span><strong>{run.name}</strong><small>{runTime(run)}</small></span><Verdict run={run} /><img className="wb-arrow" alt="" src={data.icons["arrow-right"]} /></button>
          </li>)}</ul> : <p className="wb-empty">No runs recorded yet.</p>}
        </>}
        {selection.tab === "Suites" && <>
          <div className="wb-panel-title"><div><span className="wb-label">Batch execution</span><h2>Suites and tools</h2><p>Queue a regression suite or open a specialized verification tool.</p></div></div>
          <div className="wb-subpanel wb-suite"><div><h3>Transfer regression</h3><p>Queue the saved transfer scenarios for the background worker. Review results in History.</p></div>
            {data.canWrite && <button className="wb-primary" disabled={busy} type="button" onClick={() => void request(data.suite, {})}>{busy ? "Queuing…" : "Queue suite"}</button>}
          </div>
          <div className="wb-tools">{tools.map(([title, description, href, icon]) => <a className="wb-subpanel" key={href} href={href}>
            <img alt="" src={data.icons[icon]} /><span><strong>{title}</strong><small>{description}</small></span><img className="wb-arrow" alt="" src={data.icons["arrow-right"]} />
          </a>)}</div>
        </>}
      </div>
    </section>
  </div>;
}

const mount = document.getElementById("realmproof-workbench");
const payload = document.getElementById("realmproof-workbench-data")?.textContent;
const csrf = mount?.querySelector<HTMLInputElement>('[name="csrfmiddlewaretoken"]')?.value;
if (mount && payload && csrf) createRoot(mount).render(<Workbench data={JSON.parse(payload)} csrf={csrf} />);
