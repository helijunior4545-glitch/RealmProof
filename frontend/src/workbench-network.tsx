import { useRef, useState, type FormEvent } from "react";

type Step = { id: number; name: string; actor: string; hash: string; height: string; expected: "passed" | "failed" };
type StepResult = Omit<Step, "id" | "height"> & {
  height: number; verdict: string; observed?: string; ordered?: boolean; receipt?: object; reason?: string;
};
type Report = { chain_id: string; verdict: string; steps: StepResult[] };
const blank = (id: number): Step => ({ id, name: "", actor: "", hash: "", height: "", expected: "passed" });

export function NetworkExperiment({ endpoint, csrf }: { endpoint: string; csrf: string }) {
  const [steps, setSteps] = useState(() => [blank(1)]);
  const [report, setReport] = useState<Report>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const nextId = useRef(2);
  const download = useRef<HTMLAnchorElement>(null);

  function update(id: number, change: Partial<Step>) {
    setSteps(current => current.map(step => step.id === id ? { ...step, ...change } : step));
  }

  async function verify(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    setReport(undefined);
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json", "X-CSRFToken": csrf },
        body: JSON.stringify({ steps: steps.map(({ id, ...step }) => ({ ...step, height: Number(step.height) })) }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error ?? "Verification request failed.");
      setReport(body);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Verification request failed.");
    } finally {
      setBusy(false);
    }
  }

  function exportReport() {
    if (!report || !download.current) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: "application/json" }));
    download.current.href = url;
    download.current.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return <>
    <div className="wb-panel-title">
      <div><span className="wb-label">Network evidence</span><h2>Onyx experiments</h2>
        <p>Verify the execution outcomes and order of transactions already submitted to Onyx.</p></div>
      <span className="wb-engine">onyx-1</span>
    </div>
    <form className="wb-network-form" onSubmit={verify}>
      {steps.map((step, index) => <fieldset className="wb-subpanel wb-network-step" key={step.id} disabled={busy}>
        <legend>Step {index + 1}</legend>
        <label>Step name<input value={step.name} maxLength={96} required onChange={e => update(step.id, { name: e.target.value })} /></label>
        <label>Actor label<input value={step.actor} maxLength={96} required onChange={e => update(step.id, { actor: e.target.value })} /></label>
        <label>Transaction hash<input value={step.hash} maxLength={96} required spellCheck={false} onChange={e => update(step.id, { hash: e.target.value })} /></label>
        <label>Block height<input value={step.height} type="number" min="1" max={Number.MAX_SAFE_INTEGER} step="1" required onChange={e => update(step.id, { height: e.target.value })} /></label>
        <label>Expected execution<select value={step.expected} onChange={e => update(step.id, { expected: e.target.value === "passed" ? "passed" : "failed" })}>
          <option value="passed">Accepted</option><option value="failed">Failed</option>
        </select></label>
        {steps.length > 1 && <button aria-label={`Remove step ${index + 1}`} type="button" onClick={() => setSteps(current => current.filter(item => item.id !== step.id))}>Remove</button>}
      </fieldset>)}
      <p>Sign and submit each operation with your own Gno wallet or CLI. Actor labels document your plan. Verification uses the public Onyx RPC.</p>
      <div className="wb-actions">
        <button className="wb-primary" disabled={busy}>{busy ? "Verifying…" : "Verify experiment"}</button>
        <button type="button" disabled={busy || steps.length >= 6} onClick={() => setSteps(current => [...current, blank(nextId.current++)])}>Add step</button>
      </div>
    </form>
    {error && <p className="wb-error" role="alert">{error}</p>}
    {report && <section className="wb-subpanel wb-network-result" aria-label="Experiment result">
      <div className="wb-panel-title">
        <h3>Experiment result</h3><span className="wb-verdict" data-status={report.verdict} role="status">{report.verdict}</span>
      </div>
      <ol>{report.steps.map(step => <li key={step.hash}>
        <details>
          <summary><strong>{step.name}</strong> · {step.actor} · block {step.height} · <span className="wb-verdict" data-status={step.verdict}>{step.verdict}</span></summary>
          <p>Expected {step.expected} · observed {step.observed ?? "unavailable"}</p>
          {step.reason && <p>{step.reason}</p>}
          {step.ordered === false && <p>This transaction precedes another step on-chain.</p>}
          {step.receipt && <pre className="wb-terminal-buffer" tabIndex={0}>{JSON.stringify(step.receipt, null, 2)}</pre>}
        </details>
      </li>)}</ol>
      <button type="button" onClick={exportReport}>Download experiment JSON</button>
      <a ref={download} hidden download="realmproof-onyx-experiment.json" />
    </section>}
  </>;
}
