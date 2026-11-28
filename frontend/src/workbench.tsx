import { useEffect, useRef, useState, type FormEvent } from "react";
import { NetworkExperiment } from "./workbench-network";
import { createRoot } from "react-dom/client";
import { Terminal, type TerminalRun } from "./workbench-terminal";

type Fields = Record<string, unknown>;
type Scenario = { id: string; name: string; family: string; objective: string; inputs: Fields; expected: Fields; execute: string };
type Run = TerminalRun & {
  id: string; scenario: string; name: string; status: string; execution: string; started: string;
  reason: string; inputs: Fields; expected: Fields; observed: Fields; mismatches: Fields;
  duration: number | null; digest: string | null; onyx: string | null; report: string; download: string | null;
};
type WorkbenchData = { scenarios: Scenario[]; runs: Run[]; canWrite: boolean; guidedDemo?: boolean; history: string; suite: string; catalog: string; universal: string; create: string; experiment: string; network: string; ledger: string; icons: Record<string, string> };
type ResponseData = { error?: string; run?: Run; runs?: Run[]; queued?: number };
type SuiteRow = { scenario: Scenario; state: "waiting" | "running" | "finished" | "unavailable"; run?: Run; error?: string };
type LiveEvent = ResponseData & { stage?: string; output?: string };

async function readEvents(response: Response, onEvent: (event: LiveEvent) => void): Promise<ResponseData> {
  if (!response.body) throw new Error("The runner returned no stream.");
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let pending = "";
  let result: ResponseData | undefined;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        if (result) return result;
        throw new Error("The live feed closed before a result arrived. Check History.");
      }
      const lines = (pending + value).split("\n");
      pending = lines.pop() ?? "";
      for (const line of lines) {
        if (!line) continue;
        const event: LiveEvent = JSON.parse(line);
        if (event.run || event.error) result = event;
        else onEvent(event);
      }
    }
  } finally {
    await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}

const tabs = ["Configure", "Result", "Compare", "History", "Suites", "Network"] as const;
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

function demoScenario(data: WorkbenchData, name: string) {
  return data.guidedDemo && data.canWrite
    ? data.scenarios.find(item => item.name === name && item.inputs.engine === "transfer")
    : undefined;
}

function readSelection(data: WorkbenchData): Selection {
  const params = new URLSearchParams(window.location.search);
  const run = data.runs.find(item => item.id === params.get("run"));
  return {
    tab: tabs.find(item => item.toLowerCase() === params.get("view")) ?? "Configure",
    scenario: params.get("scenario") ?? run?.scenario ?? demoScenario(data, "Insufficient balance")?.id ?? data.scenarios[0]?.id ?? "",
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
  scenario: Scenario; writable: boolean; busy: boolean; arrow: string; submit: (url: string, payload: Fields) => void;
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
    <form key={revision} id="wb-scenario-form" onSubmit={run}>
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
  const evaluated = run.status === "passed" || run.status === "failed";
  const matched = keys.filter(key => !Object.hasOwn(run.mismatches, key)).length;
  return <section className="wb-assertions" aria-labelledby="wb-assertions-title">
    <h3 id="wb-assertions-title">Assertions {evaluated && <span>{matched}/{keys.length} matched</span>}</h3>
    <div className="wb-table-wrap" tabIndex={0} role="region" aria-label="Assertion results">
    <table><thead><tr><th>Assertion</th><th>Expected</th><th>Observed</th><th>Result</th></tr></thead>
      <tbody>{keys.map(key => {
        const observed = run.observed[key];
        const mismatch = Object.hasOwn(run.mismatches, key);
        return <tr key={key}><th scope="row">{fieldNames[key] ?? key}</th>
          <td><code>{display(run.expected[key])}</code></td><td><code>{display(observed)}</code></td>
          <td>{(run.status === "pending" || run.status === "error") ? "—" :
            <span className={mismatch ? "wb-negative" : "wb-positive"}><i aria-hidden="true">{mismatch ? "×" : "✓"}</i>{mismatch ? "Mismatch" : "Match"}</span>}</td>
        </tr>;
      })}</tbody>
    </table>
    </div>
  </section>;
}

const onyxRegistry = "https://onyx.testnets.gno.land/r/g16e6lg37nhkznu9vtzqka6amks6esgkaxe6x6vt/verification";
// Public example documented in README.md and docs/TESTNET_EVIDENCE.md.
const publishedExampleDigest = "2cafb80e0d13096b37eb3278f9c2607be7524fd3cdaca2c1191281459821ccfd";

const onyxChain = "onyx-1";
const onyxRpc = "https://rpc.onyx.testnets.gno.land";
const onyxRealm = onyxRegistry.replace("https://onyx.testnets.gno.land/", "gno.land/");

type AdenaResponse = { status: string; type?: string; data?: { chainId?: string; address?: string } };
type Adena = {
  AddEstablish(name: string): Promise<AdenaResponse>;
  GetNetwork(): Promise<AdenaResponse>;
  GetAccount(): Promise<AdenaResponse>;
  DoContract(params: {
    networkInfo: { chainId: string; rpcUrl: string };
    messages: { type: "/vm.m_call"; value: { pkg_path: string; func: string; args: string[]; caller: string; send: string } }[];
  }): Promise<AdenaResponse>;
};

async function lookupOnyx(url: string, signal: AbortSignal): Promise<boolean> {
  const response = await fetch(url, { signal, redirect: "error" });
  if (!response.ok) throw new Error("Onyx lookup is temporarily unavailable.");
  const result = await response.json();
  if (typeof result.registered !== "boolean") throw new Error("Unexpected Onyx lookup response.");
  return result.registered;
}

function EvidenceLinks({ digest, lookup }: { digest: string; lookup: string }) {
  const [copyStatus, setCopyStatus] = useState("");
  const [registered, setRegistered] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState("");
  const operation = useRef<AbortController | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    lookupOnyx(lookup, controller.signal).then(
      result => { if (!controller.signal.aborted && !operation.current) setRegistered(result); },
      () => {},
    );
    return () => {
      controller.abort();
      operation.current?.abort();
    };
  }, [lookup]);

  async function verifyOrRegister(register: boolean) {
    if (operation.current) return;
    const controller = new AbortController();
    operation.current = controller;
    const { signal } = controller;
    setBusy(true);
    setFeedback("Checking the Onyx registry…");
    try {
      const exists = await lookupOnyx(lookup, signal);
      setRegistered(exists);
      if (signal.aborted) return;
      if (exists || !register) {
        setFeedback(exists ? "Registration confirmed by the Onyx registry." : "This hash is not registered on Onyx yet.");
        return;
      }
      const wallet = (window as Window & { adena?: Adena }).adena;
      if (!wallet) throw new Error("Open this page in a browser with the Adena wallet extension installed, or use the CLI guide below.");
      setFeedback("Connect Adena to RealmProof.");
      const connection = await wallet.AddEstablish("RealmProof");
      if (connection.status !== "success" && connection.type !== "ALREADY_CONNECTED") throw new Error("Adena did not authorize the connection.");
      const network = await wallet.GetNetwork();
      if (network.status !== "success" || network.data?.chainId !== onyxChain) throw new Error("Select the Onyx testnet (onyx-1) in Adena, then retry.");
      const account = await wallet.GetAccount();
      const caller = account.data?.address;
      if (account.status !== "success" || account.data?.chainId !== onyxChain || !caller) throw new Error("Select a funded Onyx testnet account in Adena.");
      if (signal.aborted) return;
      setFeedback("Review the hash and testnet fee in Adena, then approve the transaction.");
      const transaction = await wallet.DoContract({
        networkInfo: { chainId: onyxChain, rpcUrl: onyxRpc },
        messages: [{ type: "/vm.m_call", value: { pkg_path: onyxRealm, func: "RegisterEvidence", args: [digest], caller, send: "" } }],
      });
      if (signal.aborted) return;
      setFeedback("Waiting for the Onyx registry to reflect the transaction…");
      const attempts = transaction.status === "success" ? 5 : 1;
      for (let attempt = 0; attempt < attempts && !signal.aborted; attempt++) {
        if (attempt) await new Promise(resolve => setTimeout(resolve, 3000));
        if (signal.aborted) return;
        if (await lookupOnyx(lookup, signal)) {
          setRegistered(true);
          setFeedback("Registration confirmed by the Onyx registry.");
          return;
        }
      }
      setFeedback(transaction.status === "success"
        ? "Adena submitted the transaction. Check registration again in a moment."
        : "Adena did not confirm submission. Review the wallet and check registration before retrying.");
    } catch (error) {
      if (!signal.aborted) setFeedback(error instanceof Error ? error.message : "Registration could not be verified.");
    } finally {
      operation.current = null;
      if (!signal.aborted) setBusy(false);
    }
  }

  async function copyDigest() {
    try {
      await navigator.clipboard.writeText(digest);
      setCopyStatus("SHA-256 copied.");
    } catch {
      setCopyStatus("Copy unavailable. Select the hash to copy it.");
    }
  }
  return <section className="wb-subpanel wb-evidence-links" aria-labelledby="wb-onyx-title">
    <div className="wb-evidence-heading">
      <div><span className="wb-label">Report SHA-256</span><h3 id="wb-onyx-title">Verify evidence on Gno.land</h3></div>
      <span className="wb-verdict" data-status={registered ? "passed" : undefined}>
        {registered ? "Registered on Onyx" : registered === false ? "Not registered on Onyx" : "Onyx registration unconfirmed"}
      </span>
    </div>
    <div className="wb-evidence-digest"><code>{digest}</code>
      <button type="button" onClick={() => void copyDigest()}>Copy hash</button>
    </div>
    <p>{registered
      ? "Onyx stores this report hash. The execution took place outside the chain."
      : "Running a test generates a report hash locally. Onyx can display it after a registration transaction is confirmed."}</p>
    <div className="wb-actions">
      {registered ? (
        <a className="wb-onyx-link" href={`${onyxRegistry}:${digest}`} target="_blank" rel="noopener noreferrer">Verify registered hash on Onyx ↗</a>
      ) : <>
        <button type="button" className="wb-primary" disabled={busy} onClick={() => void verifyOrRegister(true)}>Register on Onyx</button>
        <button type="button" disabled={busy} onClick={() => void verifyOrRegister(false)}>Check registration</button>
        <a className="wb-onyx-link" href="https://github.com/helijunior4545-glitch/RealmProof/blob/main/docs/TESTNET_EVIDENCE.md" target="_blank" rel="noopener noreferrer">How to register this hash ↗</a>
        <a href={`${onyxRegistry}:${digest}`} target="_blank" rel="noopener noreferrer">Check registration on Onyx ↗</a>
        <a href={`${onyxRegistry}:${publishedExampleDigest}`} target="_blank" rel="noopener noreferrer">View a registered example ↗</a>
      </>}
    </div>
    <p role="status" className={feedback ? "wb-evidence-feedback" : "wb-silent"}>{feedback}</p>
    <span role="status" className={copyStatus ? "wb-evidence-feedback" : "wb-silent"}>{copyStatus}</span>
  </section>;
}

function Result({ run, showTerminal }: { run: Run; showTerminal: () => void }) {
  const details = useRef<HTMLDialogElement>(null);
  const outcome = run.execution === "local_gno" && (run.observed.status === "success" || run.observed.status === "rejected")
    ? (run.observed.status === "success" ? "Transfer accepted" : "Transfer rejected") : null;
  return <>
    <div className="wb-panel-title wb-report-header">
      <div><span className="wb-label">Execution report</span><h2>{run.name}</h2>
        <p>{runTime(run)}{run.duration !== null && <> · {run.duration} ms</>}</p>
      </div>
      <div className="wb-result-badges">
        <span className="wb-outcome" data-outcome={outcome ? String(run.observed.status) : undefined}>
          {outcome ?? executionNames[run.execution] ?? run.execution.replaceAll("_", " ")}
        </span>
        <span className="wb-verdict" data-status={run.status}>
          {run.status === "passed" ? "Assertions passed" : run.status === "failed" ? "Assertions failed" : statusNames[run.status] ?? run.status}
        </span>
      </div>
    </div>
    {run.reason && run.status !== "passed" && <p>{run.reason}</p>}
    <Assertions run={run} />
    {run.onyx && run.digest && /^[a-f0-9]{64}$/.test(run.digest) && <EvidenceLinks key={run.id} digest={run.digest} lookup={run.onyx} />}
    <div className="wb-actions">
      <button type="button" onClick={() => details.current?.showModal()}>Inspect evidence</button>
      <button type="button" onClick={showTerminal}>Open in terminal</button>
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

function Compare({ runs, pair }: { runs: Run[]; pair?: [string, string] }) {
  const comparable = runs.filter(run => run.status !== "error" && run.status !== "pending" && Object.keys(run.observed).length);
  const [baseline, setBaseline] = useState(pair?.[0] ?? "");
  const [candidate, setCandidate] = useState(pair?.[1] ?? "");
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
      <div className="wb-actions">
        <a href={first.report}>Baseline evidence</a>
        <a href={second.report}>Candidate evidence</a>
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
  const [requestBusy, setRequestBusy] = useState(false);
  const [suiteBusy, setSuiteBusy] = useState(false);
  const [suiteRows, setSuiteRows] = useState<SuiteRow[]>([]);
  const runningSuite = useRef(false);
  const busy = requestBusy || suiteBusy;
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const activeRequest = useRef(false);
  const searchInput = useRef<HTMLInputElement>(null);
  const terminalDock = useRef<HTMLDivElement>(null);
  const [terminalOpen, setTerminalOpen] = useState(!data.guidedDemo);
  const [terminalExpanded, setTerminalExpanded] = useState(false);
  const [executing, setExecuting] = useState("");
  const [liveOutput, setLiveOutput] = useState("");
  const [liveStage, setLiveStage] = useState("");
  const [demoPair, setDemoPair] = useState<[string, string]>();
  const insufficient = demoScenario(data, "Insufficient balance");
  const valid = demoScenario(data, "Valid transfer");
  const exact = demoScenario(data, "Exact balance");
  const demoSuite = insufficient && valid && exact ? [valid, insufficient, exact] : [];

  const scenario = data.scenarios.find(item => item.id === selection.scenario) ?? data.scenarios[0];
  const result = runs.find(item => item.id === selection.run) ?? runs.find(item => item.scenario === scenario?.id);
  const baseline = insufficient && runs.find(item =>
    item.scenario === insufficient?.id && item.execution === "local_gno" &&
    item.status === "passed" && item.observed.status === "rejected" &&
    item.inputs.balance === insufficient.inputs.balance &&
    item.inputs.amount === insufficient.inputs.amount &&
    item.inputs.authorized === insufficient.inputs.authorized
  );
  const showGuide = !!(insufficient && valid && (selection.tab === "Configure" || selection.tab === "Result"));
  const visible = data.scenarios.filter(item => `${item.name} ${item.family}`.toLowerCase().includes(search.trim().toLowerCase()));

  useEffect(() => {
    const restore = () => setSelection(readSelection({ ...data, runs }));
    window.addEventListener("popstate", restore);
    return () => window.removeEventListener("popstate", restore);
  }, [data, runs]);

  useEffect(() => {
    function handleShortcut(event: KeyboardEvent) {
      if (event.defaultPrevented || event.repeat || document.querySelector("dialog[open]")) return;
      if (event.altKey && event.shiftKey && event.code === "KeyT") {
        event.preventDefault();
        setTerminalOpen(value => !value);
      }
      if (event.altKey && event.shiftKey && event.code === "KeyF") {
        event.preventDefault();
        searchInput.current?.focus();
      }
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter" && selection.tab === "Configure" && data.canWrite && !busy) {
        event.preventDefault();
        const form = document.getElementById("wb-scenario-form");
        if (form instanceof HTMLFormElement) form.requestSubmit();
      }
    }
    window.addEventListener("keydown", handleShortcut);
    return () => window.removeEventListener("keydown", handleShortcut);
  }, [selection.tab, data.canWrite, busy]);

  function navigate(tab: Tab, scenarioId = scenario?.id ?? "", runId = "") {
    const url = new URL(window.location.href);
    url.searchParams.set("view", tab.toLowerCase());
    if (scenarioId) url.searchParams.set("scenario", scenarioId);
    if (runId) url.searchParams.set("run", runId);
    else url.searchParams.delete("run");
    if (url.href !== window.location.href) window.history.pushState(null, "", url);
    setSelection({ tab, scenario: scenarioId, run: runId });
    setNotice("");
  }

  async function request(url: string, payload?: Fields, guide?: { baseline?: string; batch?: boolean }) {
    if (activeRequest.current || (runningSuite.current && !guide?.batch)) return;
    activeRequest.current = true;
    setRequestBusy(true);
    const runRequest = data.scenarios.find(item => item.execute === url);
    const live = runRequest?.inputs.engine === "transfer";
    if (runRequest) {
      setLiveOutput("");
      setLiveStage(live ? "Connecting to Gno runner" : "Evaluating supplied evidence");
      setExecuting(runRequest.name);
      if (!guide) {
        setTerminalOpen(true);
        requestAnimationFrame(() => terminalDock.current?.scrollIntoView({ block: "nearest" }));
      }
    }
    setError("");
    setNotice("");
    try {
      const response = await fetch(url, payload === undefined ? {
        headers: { Accept: "application/json" },
      } : {
        method: "POST",
        headers: { Accept: live ? "application/x-ndjson" : "application/json", "Content-Type": "application/json", "X-CSRFToken": csrf },
        body: JSON.stringify(payload),
      });
      const contentType = response.headers.get("Content-Type") ?? "";
      let body: ResponseData;
      if (contentType.includes("application/x-ndjson")) {
        body = await readEvents(response, event => {
          if (event.stage) setLiveStage(event.stage);
          if (event.output) setLiveOutput(current => (current + event.output).slice(-12000));
        });
      } else if (contentType.includes("application/json")) {
        body = await response.json();
      } else {
        throw new Error("The workspace could not complete the request. Reload the page and try again.");
      }
      if (!response.ok || body.error) throw new Error(body.error ?? "The request failed.");
      const run = body.run;
      if (run) {
        setRuns(current => [run, ...current.filter(item => item.id !== run.id)]);
        if (guide?.batch) return { run };
        if (guide?.baseline && run.execution === "local_gno" && run.status === "passed" && run.observed.status === "success") {
          setDemoPair([guide.baseline, run.id]);
          navigate("Compare", run.scenario, run.id);
        } else {
          navigate("Result", run.scenario, run.id);
        }
        setNotice("Run recorded.");
      }
      if (body.runs) {
        setRuns(body.runs);
        setNotice(body.queued === undefined ? "Run history updated." :
          body.queued ? `${body.queued} runs queued for the background worker.` : "No new runs queued. The suite may already be pending.");
      }
    } catch (failure) {
      const message = failure instanceof Error ? failure.message : "The request failed.";
      if (guide?.batch) return { error: message };
      setError(message);
    } finally {
      activeRequest.current = false;
      setRequestBusy(false);
      setExecuting("");
    }
  }

  async function runTransferSuite() {
    if (!demoSuite.length || runningSuite.current || activeRequest.current) return;
    runningSuite.current = true;
    setSuiteBusy(true);
    setSuiteRows(demoSuite.map(scenario => ({ scenario, state: "waiting" })));
    try {
      for (const item of demoSuite) {
        setSuiteRows(rows => rows.map(row => row.scenario.id === item.id ? { ...row, state: "running" } : row));
        const response = await request(item.execute, {}, { batch: true });
        setSuiteRows(rows => rows.map(row => row.scenario.id === item.id
          ? { ...row, state: response?.run ? "finished" : "unavailable", run: response?.run, error: response?.error }
          : row));
      }
    } finally {
      runningSuite.current = false;
      setSuiteBusy(false);
    }
  }

  const tools = [
    ["Native test catalog", "Explore native Gno test packs.", data.catalog, "file-code"],
    ["Universal test engine", "Run predefined verification suites.", data.universal, "terminal-window"],
    ["Network explorer", "Inspect chain status and source.", data.network, "arrow-square-out"],
    ["Ledger validation lab", "Check ledger evidence and commitments.", data.ledger, "shield-check"],
  ];

  function showTerminal() {
    setTerminalOpen(true);
    requestAnimationFrame(() => {
      terminalDock.current?.scrollIntoView({ block: "nearest" });
      terminalDock.current?.querySelector("button")?.focus({ preventScroll: true });
    });
  }

  return <div className="wb-layout">
    <aside className="wb-panel wb-library" aria-labelledby="wb-library-title">
      <div className="wb-library-header"><div><h2 id="wb-library-title">Scenario library</h2></div><span className="wb-count">{data.scenarios.length}</span></div>
      <label className="wb-search"><span>Filter scenarios <kbd>Alt Shift F</kbd></span><input ref={searchInput} type="search" placeholder="Search by name or category" value={search} onChange={event => setSearch(event.target.value)} /></label>
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
    <div className="wb-main">
    <section className="wb-panel wb-console" aria-label="Test console">
      <header className="wb-context">
        <span><img alt="" src={data.icons["terminal-window"]} /> Workbench <span aria-hidden="true">/</span> <strong>{scenario?.name ?? "No scenario"}</strong></span>
        <span><i data-active={!!executing} aria-hidden="true" /> {executing ? "Executing" : "Off-chain workspace"}</span>
      </header>
      <nav className="wb-tabs" aria-label="Workbench views">{tabs.map(tab =>
        <button key={tab} type="button" aria-pressed={selection.tab === tab}
          onClick={() => navigate(tab, scenario?.id, tab === "Result" ? result?.id : "")}>{tab}</button>)}</nav>
      <div className="wb-console-body" aria-busy={busy}>
        {error && <p role="alert" className="wb-error">{error}</p>}
        <div role="status" className={notice ? "wb-notice" : "wb-silent"}>{notice}</div>
        {showGuide && insufficient && valid && <section className="wb-subpanel wb-jury-guide" aria-labelledby="wb-jury-title">
          <div>
            <h2 id="wb-jury-title">{baseline ? "Compare a valid transfer" : "Run the insufficient balance scenario"}</h2>
            <p>{baseline
              ? "Run a valid transfer in Gno and compare it with the recorded rejection."
              : "The contract should reject the saved transfer and preserve the balance."}</p>
          </div>
          <button type="button" className="wb-primary" disabled={busy}
            onClick={() => void request(baseline ? valid.execute : insufficient.execute, {}, { baseline: baseline?.id })}>
            {busy ? "Running…" : baseline ? "Try a valid transfer" : "Run in Gno"}
          </button>
          {executing && liveStage && <p className="wb-jury-progress" role="status">{liveStage}</p>}
        </section>}
        {demoSuite.length > 0 && (selection.tab === "Compare" || suiteBusy) &&
          <section className="wb-subpanel wb-transfer-suite" aria-labelledby="wb-transfer-suite-title">
            <div className="wb-evidence-heading">
              <div><h2 id="wb-transfer-suite-title">Transfer suite</h2>
                <p>Compare expected and observed outcomes across three Gno scenarios.</p></div>
              <button type="button" className="wb-primary" disabled={busy} onClick={() => void runTransferSuite()}>
                {suiteBusy ? "Running suite…" : suiteRows.length ? "Run suite again" : "Run transfer suite"}
              </button>
            </div>
            {suiteRows.length > 0 && <>
              <div className="wb-suite-progress" role="status">
                {suiteRows.filter(row => row.state === "finished" || row.state === "unavailable").length} of {suiteRows.length} completed
                {suiteBusy && executing ? ` · ${executing}${liveStage ? ` · ${liveStage}` : ""}` : ""}
              </div>
              <div className="wb-table-wrap" tabIndex={0} role="region" aria-label="Transfer suite results">
                <table><thead><tr><th>Scenario</th><th>Expected outcome / balance</th><th>Observed outcome / balance</th><th>Result</th></tr></thead>
                  <tbody>{suiteRows.map(({ scenario: item, state, run, error: rowError }) => {
                    const expected = run?.expected ?? item.expected;
                    return <tr key={item.id}>
                      <th scope="row">{item.name}</th>
                      <td>{display(expected.status)} / {display(expected.balance)}</td>
                      <td>{run ? `${display(run.observed.status)} / ${display(run.observed.balance)}` : "—"}</td>
                      <td>{run ? <><Verdict run={run} /> <button type="button" disabled={suiteBusy} onClick={() => navigate("Result", run.scenario, run.id)}>View evidence</button></>
                        : state === "unavailable" ? <span>{rowError || "Execution unavailable"}</span> : state === "running" ? "Running" : "Waiting"}</td>
                    </tr>;
                  })}</tbody>
                </table>
              </div>
              {!suiteBusy && <button type="button" onClick={() => navigate("Configure", insufficient?.id)}>Edit inputs and rerun</button>}
            </>}
          </section>}
        <div hidden={selection.tab !== "Configure"}>{scenario ?
          <Configuration key={scenario.id} scenario={scenario} writable={data.canWrite} busy={busy} arrow={data.icons["arrow-right"]} submit={request} /> :
          <p className="wb-empty">Create a scenario to start testing.</p>}</div>
        {selection.tab === "Result" && (result ? <Result key={result.id} run={result} showTerminal={showTerminal} /> :
          <p className="wb-empty">Run the selected scenario to see its verdict and evidence.</p>)}
        {selection.tab === "Compare" && <Compare key={demoPair?.join(":")} runs={runs} pair={demoPair} />}
        {selection.tab === "History" && <>
          <div className="wb-panel-title"><div><span className="wb-label">Recorded evidence</span><h2>Run history</h2><p>Recent executions in this project.</p></div>
            <button type="button" disabled={busy} onClick={() => void request(data.history)}>Refresh runs</button>
          </div>
          {runs.length ? <ul className="wb-history">{runs.map(run => <li key={run.id}>
            <button type="button" onClick={() => navigate("Result", run.scenario, run.id)}><span><strong>{run.name}</strong><small>{runTime(run)}</small></span><Verdict run={run} /><img className="wb-arrow" alt="" src={data.icons["arrow-right"]} /></button>
          </li>)}</ul> : <p className="wb-empty">No runs recorded yet.</p>}
        </>}
        <div hidden={selection.tab !== "Network"}><NetworkExperiment endpoint={data.experiment} csrf={csrf} /></div>
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
    <div ref={terminalDock}>
      <Terminal key={result?.id ?? "empty"} run={result} execution={executing} liveOutput={liveOutput} liveStage={liveStage} open={terminalOpen} expanded={terminalExpanded}
        icon={data.icons["terminal-window"]} onToggle={() => setTerminalOpen(value => !value)} onExpand={() => setTerminalExpanded(value => !value)} />
    </div>
    <div className="wb-statusbar"><span>{data.canWrite ? "Editor access" : "Read only"}</span><span>{runs.length} recent runs</span>
      {selection.tab === "Configure" && data.canWrite && <span>Run scenario <kbd>Ctrl / ⌘ Enter</kbd></span>}
    </div>
    </div>
  </div>;
}

const mount = document.getElementById("realmproof-workbench");
const payload = document.getElementById("realmproof-workbench-data")?.textContent;
const csrf = mount?.querySelector<HTMLInputElement>('[name="csrfmiddlewaretoken"]')?.value;
if (mount && payload && csrf) createRoot(mount).render(<Workbench data={JSON.parse(payload)} csrf={csrf} />);
