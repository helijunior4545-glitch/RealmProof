"""Execute only bundled, trusted Gno fixtures. Never execute tenant source."""
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

CASES = (
    ("Valid transfer", "valid", 100, 25, True, "success", 75),
    ("Insufficient balance", "invalid", 100, 150, True, "rejected", 100),
    ("Unauthorized transfer", "permission", 100, 25, False, "rejected", 100),
    ("Exact balance", "boundary", 100, 100, True, "success", 0),
    ("Zero amount", "boundary", 100, 0, True, "rejected", 100),
    ("Negative amount", "invalid", 100, -1, True, "rejected", 100),
)

class GnoExecutionError(RuntimeError):
    def __init__(self, output, evidence):
        super().__init__("Gno execution did not produce a valid result: " + output[-2000:])
        self.evidence = evidence


def transfer_files(inputs):
    balance, amount, authorized = (inputs.get(k) for k in ("balance", "amount", "authorized"))
    if type(balance) is not int or type(amount) is not int or type(authorized) is not bool:
        raise ValueError("Expected integer balance and amount, and boolean authorized.")
    if not 0 <= balance <= 10**12 or not -10**12 <= amount <= 10**12:
        raise ValueError("Inputs exceed demo limits.")
    source = (Path(__file__).resolve().parent.parent / "realms" / "transfer" / "transfer.gno").read_text()
    harness = """package transfer
import "testing"
import "fmt"
func TestScenario(t *testing.T) {
    status, balance := Transfer(%d, %d, %s)
    fmt.Println("REALMPROOF_RESULT", status, balance)
}
""" % (balance, amount, str(authorized).lower())
    return source, harness


def execute(inputs):
    binary = shutil.which(os.environ.get("REALMPROOF_GNO_BINARY", "gno"))
    if not binary:
        raise RuntimeError("Gno CLI is unavailable. Install gno and restart the server.")
    source, harness = transfer_files(inputs)
    balance = inputs["balance"]
    env = os.environ.copy()
    local_root = Path.home() / '.gno' / 'source'
    if not env.get('GNOROOT') and (local_root / 'gnovm' / 'stdlibs').is_dir():
        env['GNOROOT'] = str(local_root)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="realmproof-") as directory:
        root = Path(directory)
        (root / "transfer.gno").write_text(source)
        (root / "transfer_test.gno").write_text(harness)
        (root / "gno.mod").write_text("module gno.land/p/realmproof/transfer\n")
        (root / "gnomod.toml").write_text('module = "gno.land/p/realmproof/transfer"\n')
        result = subprocess.run([binary, "test", "-v", "."], cwd=root, env=env, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20,
                                text=True, errors="replace")
    output = result.stdout
    matches = re.findall(r"(?m)^\s*REALMPROOF_RESULT (success|rejected) (-?\d+)\s*$", output)
    evidence = {
        "type": "local_gno", "verified_on_chain": False, "duration_ms": round((time.monotonic()-started)*1000),
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "harness_sha256": hashlib.sha256(harness.encode()).hexdigest(), "output": output[-12000:],
        "initial_balance": balance, "exit_code": result.returncode,
    }
    if result.returncode or len(matches) != 1:
        raise GnoExecutionError(output, evidence)
    status, final = matches[0]
    return {"status": status, "balance": int(final), "state_changed": int(final) != balance}, evidence
