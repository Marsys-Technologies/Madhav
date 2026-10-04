"""The lock and statement limits, pinned INDEPENDENTLY of the executor-sha pin (the plan-txt/sha test is deselected by the mutation harness, so these tests
kill the 'cap raised' and 'lock_timeout 5s -> 500s' mutants on their own)."""
from __future__ import annotations

import re
import threading
import time

import pytest

import conftest as cf


@pytest.fixture()
def runner(cluster, mod, db, tmp_path):
    return cf.Runner(cluster, mod, db, tmp_path)


def test_the_limits_are_the_documented_values(mod):
    assert (mod.LOCK_TIMEOUT, mod.STATEMENT_TIMEOUT, mod.WINDOW_STATEMENT_BOUND) == ("5s", "120s", 100)
    plan = mod.render_plan()
    assert "SET LOCAL lock_timeout = '5s'" in plan and "SET LOCAL statement_timeout = '120s'" in plan


def test_the_session_really_sets_lock_timeout_5s_and_statement_timeout_120s_and_the_window_stays_within_100_statements(runner, mod, monkeypatch):
    seen = []
    orig = mod.fa2.CountingCursor.execute

    def spy(self, sql, *a, **k):
        seen.append(sql if isinstance(sql, str) else str(sql))
        return orig(self, sql, *a, **k)
    monkeypatch.setattr(mod.fa2.CountingCursor, "execute", spy)
    code, res = runner.run("apply")
    assert code == 0, res["details"]
    assert "SET LOCAL lock_timeout = '5s'" in seen and "SET LOCAL statement_timeout = '120s'" in seen
    m = re.search(r"ACCESS EXCLUSIVE window \(UTC\): \S+ -> \S+; statements inside it: (\d+)", "\n".join(res["log"]))
    n = int(m.group(1))
    assert 40 <= n <= 100, n                                         # measured 63-65 in the rehearsals on this plan; the cap is 100
    assert res["checks"]["post_exclusive_window_statements_bounded"] is True


def test_a_concurrent_reader_of_chart_vichara_makes_the_plan_fail_clean_after_the_lock_timeout(runner, cluster, db, mod):
    """chart_vichara ALSO takes the exclusive lock (at DROP TRIGGER). A reader holding it open blocks the plan, which gives up after lock_timeout and rolls back clean."""
    pre = runner.state()
    _, dry = runner.execute(runner.args("dry-run"))
    holder = cluster.conn(db)                                         # superuser reader, transaction left open
    holder.cursor().execute("SELECT count(*) FROM public.chart_vichara")
    out = {}

    def go():
        t0 = time.time()
        try:
            out["res"] = runner.execute(runner.args("apply", expect_evidence=dry["evidence_digest"]))
        except Exception as exc:                                      # a lock timeout surfaces as an error the executor records as failed
            out["exc"] = exc
        out["t"] = time.time() - t0
    th = threading.Thread(target=go, daemon=True)
    th.start()
    th.join(25)
    alive = th.is_alive()
    holder.rollback()
    holder.close()
    th.join(10)
    assert not alive, "the plan did not give up within 25 s: lock_timeout is not the bounded 5 s"
    assert 4 <= out["t"] <= 20, out["t"]
    assert "exc" in out or out["res"][0] != 0
    assert runner.state() == pre                                      # rolled back clean
