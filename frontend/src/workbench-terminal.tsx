import { useEffect, useRef, useState } from "react";

export type TerminalRun = {
  id: string;
  name: string;
  status: string;
  execution: string;
  console: string;
  report: string;
  inputs: Record<string, unknown>;
  expected: Record<string, unknown>;
  observed: Record<string, unknown>;
};

type ConsoleData = {
  output: string | null;
  exitCode: number | null;
  files: { source?: string; harness?: string };
  evidence: Record<string, unknown>;
};

const views = ["Output", "Contract", "Test harness", "Run JSON"] as const;
const filenames = { Output: "gno-output.txt", Contract: "transfer.gno", "Test harness": "transfer_test.gno", "Run JSON": "run-snapshot.json" };

function outputTone(line: string) {
  if (/^REALMPROOF_RESULT\s+rejected\b/.test(line)) return "rejected";
  if (/^(--- PASS:|ok\b|REALMPROOF_RESULT\s+success\b)/.test(line)) return "pass";
  if (/^(--- FAIL:|FAIL\b|panic:|error:)/i.test(line)) return "error";
  if (/^--- GAS:/.test(line)) return "gas";
  if (/^=== RUN/.test(line)) return "run";
  return undefined;
}

export function Terminal({ run, execution, liveOutput, liveStage, onToggle, onExpand, open, expanded, icon }: {
  run?: TerminalRun; execution: string; liveOutput: string; liveStage: string; onToggle: () => void; onExpand: () => void; open: boolean; expanded: boolean; icon: string;
}) {
  const [view, setView] = useState<typeof views[number]>("Output");
  const [data, setData] = useState<ConsoleData>();
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [copyState, setCopyState] = useState("");
  const buffer = useRef<HTMLPreElement>(null);
  const url = run?.status === "pending" ? undefined : run?.console;

  useEffect(() => {
    if (!open || !url) return;
    const controller = new AbortController();
    fetch(url, { signal: controller.signal, headers: { Accept: "application/json" } })
      .then(response => {
        if (!response.ok) throw new Error("Unable to load capture");
        return response.json() as Promise<ConsoleData>;
      })
      .then(response => { if (!controller.signal.aborted) setData(response); })
      .catch(() => { if (!controller.signal.aborted) setError(true); });
    return () => controller.abort();
  }, [url, open, attempt]);

  const snapshot = run && (data || run.status === "pending") ? JSON.stringify({
    run_id: run.id, scenario: run.name, execution_status: run.execution, verdict: run.status,
    inputs: run.inputs, expected: run.expected, observed: run.observed, evidence: data?.evidence,
  }, null, 2) : undefined;
  const selectedView = execution ? "Output" : view;
  const content = execution ? liveOutput : {
    Output: data?.output, Contract: data?.files.source, "Test harness": data?.files.harness, "Run JSON": snapshot,
  }[selectedView];
  const outputLines = selectedView === "Output" ? content?.split("\n") : undefined;
  const local = run?.execution === "local_gno" || data?.exitCode != null;
  const loading = open && !!url && !data && !error;
  let message = "Run a scenario to inspect its captured output and execution files.";
  if (run) {
    if (run.status === "pending") message = "Execution is pending. Refresh History after the worker processes this run.";
    else if (run.status === "error") message = "Execution ended with an infrastructure error. Open the full report for diagnostics.";
    else if (!local) message = "This run evaluates supplied evidence. Its recorded inputs and observations are available in Run JSON.";
    else message = "This run has no verified capture for the selected view.";
  }
  if (loading) message = "Loading execution capture…";
  if (error) message = "Could not load this capture.";
  if (execution) message = "Waiting for output from the runner…";

  useEffect(() => {
    if (execution && buffer.current) buffer.current.scrollTop = buffer.current.scrollHeight;
  }, [execution, liveOutput]);

  async function copy() {
    if (!content) return;
    try {
      await navigator.clipboard.writeText(content);
      setCopyState("Copied");
    } catch {
      setCopyState("Copy unavailable");
    }
  }

  return <section className="wb-terminal" aria-label="Execution terminal">
    <header className="wb-terminal-header">
      <button type="button" className="wb-terminal-toggle" aria-expanded={open} aria-controls="wb-terminal-body" onClick={onToggle}>
        <img alt="" src={icon} /> Terminal <kbd>Alt Shift T</kbd>
      </button>
      <span className="wb-terminal-status">
        <i data-active={!!execution} aria-hidden="true" />
        {execution ? "Running" : run?.status === "pending" ? "Pending" : local ? "Local Gno" : "Capture"}
      </span>
      {open && <button type="button" className="wb-terminal-expand" aria-pressed={expanded} onClick={onExpand}>{expanded ? "Restore height" : "Expand"}</button>}
    </header>
    {open && <div id="wb-terminal-body">
      <div className="wb-terminal-toolbar">
        <nav aria-label="Terminal views">{views.map(item => <button type="button" key={item} aria-pressed={selectedView === item} disabled={!!execution}
          onClick={() => { setView(item); setCopyState(""); }}>{item}</button>)}</nav>
        <div className="wb-terminal-actions">
          {content && !execution && <><button type="button" onClick={() => void copy()}>Copy</button>
            <a href={`data:text/plain;charset=utf-8,${encodeURIComponent(content)}`} download={filenames[view]}>Download</a></>}
          {error && <button type="button" onClick={() => { setError(false); setAttempt(value => value + 1); }}>Retry</button>}
          <span role="status">{copyState}</span>
        </div>
      </div>
      {local && !execution && view === "Output" && <div className="wb-terminal-meta">
        <code>gno test -v .</code>
        {data?.exitCode != null && <span>Exit {data.exitCode}</span>}
        {run && <span className="wb-verdict" data-status={run.status}>Assertions {run.status}</span>}
      </div>}
      {execution && <div className="wb-terminal-meta wb-live" role="status"><i aria-hidden="true" /><strong>{liveStage}</strong><span>{execution}</span></div>}
      {content ? <pre ref={buffer} className="wb-terminal-buffer" data-expanded={expanded} tabIndex={0} aria-label={filenames[selectedView]}>{selectedView === "Output"
        ? outputLines?.map((line, index) => <span key={index} className="wb-output-line" data-tone={outputTone(line)}>{line}{index < outputLines.length - 1 ? "\n" : ""}</span>)
        : content}</pre>
        : <p className="wb-terminal-empty" role="status">{message}{run?.status === "error" && !execution && <> <a href={run.report}>Full report</a></>}</p>}
    </div>}
  </section>;
}
