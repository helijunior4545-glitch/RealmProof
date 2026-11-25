"""Fixed, trusted stateful Gno laboratory. No tenant code or chain writes."""
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

CASES = [["fund","Funding","Deposit","Deposit(100)","true"],["zero","Funding","Zero deposit","Deposit(0)","false"],["negative","Funding","Negative deposit","Deposit(-1)","false"],["balance","Funding","Balance after funding","Balance()","100"],["unauth","Access control","Unauthorized reserve","Reserve(30, false)","false"],["over","Reservations","Insufficient available funds","Reserve(101, true)","false"],["reserve","Reservations","Reserve funds","Reserve(40, true)","true"],["available","Reservations","Available after reserve","Balance()","60"],["held","Reservations","Reserved balance","Held()","40"],["badrelease","Reservations","Excess release","Release(41, true)","false"],["denyrelease","Access control","Unauthorized release","Release(10, false)","false"],["release","Reservations","Partial release","Release(10, true)","true"],["afterrelease","Reservations","Available after release","Balance()","70"],["denysettle","Access control","Unauthorized settlement","Settle(30, false)","false"],["oversettle","Settlement","Excess settlement","Settle(31, true)","false"],["settle","Settlement","Complete settlement","Settle(30, true)","true"],["settled","Settlement","Settled amount","Paid()","30"],["emptyheld","Settlement","Reservation cleared","Held()","0"],["replay","Settlement","Repeated settlement rejected","Settle(30, true)","false"],["conserve","Invariants","Conservation of funds","Balance()+Held()+Paid()","100"],["final","Invariants","Final available funds","Balance()","70"],["freeze","Access control","Freeze account","Freeze(true)","true"],["frozenreserve","Access control","Frozen reservation rejected","Reserve(1, true)","false"],["frozendeposit","Access control","Frozen deposit rejected","Deposit(1)","false"],["unfreeze","Access control","Unfreeze account","Freeze(false)","true"],["exact","Boundaries","Reserve exact available balance","Reserve(70, true)","true"],["empty","Boundaries","Available exhausted","Balance()","0"],["restore","Boundaries","Release full reservation","Release(70, true)","true"],["finalconserve","Invariants","Final conservation","Balance()+Held()+Paid()","100"]]
def run():
    binary = shutil.which(os.environ.get("REALMPROOF_GNO_BINARY", "gno"))
    if not binary:
        raise RuntimeError("Gno CLI unavailable.")
    source = (Path(__file__).resolve().parent.parent / "realms/ledger/ledger.gno").read_text()
    harness = 'package ledger\nimport "testing"\nimport "fmt"\nfunc TestLifecycle(t *testing.T) {\n'
    for key, group, title, expression, expected in CASES:
        harness += 'fmt.Println("RP_CHECK %s", %s)\n' % (key, expression)
    harness += '}\n'
    env = os.environ.copy()
    root = Path.home() / ".gno/source"
    if not env.get("GNOROOT") and (root / "gnovm/stdlibs").is_dir():
        env["GNOROOT"] = str(root)
    with tempfile.TemporaryDirectory(prefix="rp-ledger-") as directory:
        path = Path(directory)
        (path / "ledger.gno").write_text(source)
        (path / "ledger_test.gno").write_text(harness)
        (path / "gnomod.toml").write_text('module = "gno.land/p/realmproof/ledger"\n')
        (path / "gno.mod").write_text("module gno.land/p/realmproof/ledger\n")
        result = subprocess.run([binary, "test", "-v", "."], cwd=path, env=env,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, timeout=30)
    matches = re.findall(r"(?m)^\s*RP_CHECK ([a-z]+) (true|false|-?[0-9]+)\s*$", result.stdout)
    if result.returncode or [k for k,v in matches] != [c[0] for c in CASES]:
        raise RuntimeError("Incomplete Gno execution: " + result.stdout[-1500:])
    return dict(matches), hashlib.sha256(source.encode()).hexdigest(), hashlib.sha256(harness.encode()).hexdigest(), result.stdout[-12000:]
