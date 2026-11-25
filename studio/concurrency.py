"""Real PostgreSQL concurrency probes on isolated disposable fixture tables."""
import os
import random
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from time import monotonic
from .services import evaluate

GROUPS = {"race": 60, "isolation": 60, "tenant": 50, "duplicate": 50,
          "contention": 40, "rollback": 40}
COUNT = sum(GROUPS.values())
SEED = 4501

def plan():
    rng = random.Random(SEED)
    return [(group, i, rng.randint(1, 1000)) for group, count in GROUPS.items() for i in range(count)]

def probe(dsn, table, group, amount):
    import psycopg
    from psycopg import sql
    from psycopg.errors import LockNotAvailable
    name = sql.Identifier(table)
    def query(template):
        return sql.SQL(template).format(name)
    def connect():
        return psycopg.connect(dsn, connect_timeout=5,
            options="-c statement_timeout=3000 -c lock_timeout=1500 -c idle_in_transaction_session_timeout=10000")
    with connect() as c:
        c.execute(query("TRUNCATE {}"))
        c.execute(query("INSERT INTO {} (tenant, key, balance) VALUES (1,1,%s),(2,1,%s)"), (amount, amount))
    ready = threading.Barrier(2, timeout=5)
    written = threading.Event()
    checked = threading.Event()
    def wait(event):
        if not event.wait(5):
            raise RuntimeError("Concurrency synchronization timeout.")
    def actor(index):
        with connect() as c:
            c.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
            pid = c.info.backend_pid
            ready.wait()
            if group == "race":
                result = c.execute(query("UPDATE {} SET balance=balance-%s WHERE tenant=1 AND key=1 AND balance >= %s"), (amount, amount)).rowcount
            elif group == "tenant":
                result = c.execute(query("UPDATE {} SET balance=balance+%s WHERE tenant=%s AND key=1"), (amount, index+1)).rowcount
            elif group == "duplicate":
                result = c.execute(query("INSERT INTO {} VALUES (1,2,%s) ON CONFLICT DO NOTHING"), (amount,)).rowcount
            elif index == 0:
                c.execute(query("UPDATE {} SET balance=balance+%s WHERE tenant=1 AND key=1"), (amount,))
                written.set()
                wait(checked)
                if group == "rollback":
                    c.rollback()
                result = 1
            else:
                wait(written)
                try:
                    if group == "contention":
                        try:
                            c.execute(query("SELECT balance FROM {} WHERE tenant=1 AND key=1 FOR UPDATE NOWAIT"))
                            result = 0
                        except LockNotAvailable:
                            c.rollback()
                            result = 1
                    else:
                        result = c.execute(query("SELECT balance FROM {} WHERE tenant=1 AND key=1")).fetchone()[0]
                finally:
                    checked.set()
            return pid, result
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(actor, i) for i in range(2)]
        observations = [f.result() for f in futures]
    with connect() as c:
        balances = [list(row) for row in c.execute(query("SELECT tenant,key,balance FROM {} ORDER BY tenant,key")).fetchall()]
    expected_balances = [[1,1,amount],[2,1,amount]]
    if group == "race":
        expected_balances[0][2] = 0
        expected_results = [0,1]
    elif group == "tenant":
        expected_balances = [[1,1,amount*2],[2,1,amount*2]]
        expected_results = [1,1]
    elif group == "duplicate":
        expected_balances.insert(1,[1,2,amount])
        expected_results = [0,1]
    else:
        if group != "rollback":
            expected_balances[0][2] = amount*2
        expected_results = [1,1] if group == "contention" else sorted([1,amount])
    expected = {"distinct_connections": True, "results": expected_results, "balances": expected_balances}
    observed = {"distinct_connections": observations[0][0] != observations[1][0],
                "results": sorted(x[1] for x in observations), "balances": balances}
    return expected, observed

def run(progress=None):
    import psycopg
    from psycopg import sql
    dsn = os.environ.get("REALMPROOF_CONCURRENCY_DSN")
    if not dsn:
        raise RuntimeError("Dedicated PostgreSQL fixture DSN required: REALMPROOF_CONCURRENCY_DSN.")
    table = "rp_probe_" + uuid.uuid4().hex
    name = sql.Identifier(table)
    rows = []
    start = monotonic()
    try:
        with psycopg.connect(dsn, connect_timeout=5, options="-c statement_timeout=3000") as c:
            c.execute(sql.SQL("CREATE TABLE {} (tenant integer NOT NULL, key integer NOT NULL, balance integer NOT NULL CHECK(balance>=0), PRIMARY KEY(tenant,key))").format(name))
            version = c.info.server_version
        try:
            for group, index, amount in plan():
                if monotonic()-start > 480:
                    raise RuntimeError("Concurrency campaign deadline exceeded.")
                expected, observed = probe(dsn, table, group, amount)
                rows.append({"name": f"Concurrency / {group} / {index}", "expected": expected,
                             "observed": observed, "verdict": evaluate(expected, observed).status,
                             "evidence": {"type": "postgresql_fixture", "verified_on_chain": False,
                                          "category": group, "amount": amount, "seed": SEED,
                                          "server_version": version, "isolation": "read committed"}})
                if progress:
                    progress(len(rows))
        finally:
            with psycopg.connect(dsn, connect_timeout=5, options="-c statement_timeout=3000") as c:
                c.execute(sql.SQL("DROP TABLE {}").format(name))
    except (psycopg.Error, threading.BrokenBarrierError) as exc:
        raise RuntimeError("PostgreSQL concurrency infrastructure error: " + type(exc).__name__) from exc
    return rows
