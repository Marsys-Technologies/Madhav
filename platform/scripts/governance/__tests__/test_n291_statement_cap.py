"""test_n291_statement_cap.py: every census psql statement carries a server-side statement_timeout / lock_timeout (SS N-291, from the N-249 patch).

`_psql_run` is the ONE place the census starts psql. It now (a) prepends `SET statement_timeout = min(60 s, 90% of the client limit)` and `SET lock_timeout = 5 s` as the first `-c` commands of the
same session, (b) always passes `-q` so those SETs' command tags never reach the rows, (c) runs the subprocess under `_PSQL_LOCK` (one psql / one connection at a time). A statement that hits the cap is an
`Unknown` carrying the server's text, which every census grader reads as unread / NO_DETECTOR / ERRORED, never PASS.

All tests use fakes for the psql subprocess: no database, no production, no psql binary needed.
"""
from __future__ import annotations

import ast
import pathlib
import re
import subprocess
import sys
import threading
import time

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_n256_walk_budget as wb  # noqa: E402  (its table / prose_none fixtures: the closure read path whose cells must read NO_DETECTOR)

TIMEOUT_ERR = "ERROR:  canceling statement due to statement timeout"
LOCK_ERR = "ERROR:  canceling statement due to lock timeout"


class _P:
    def __init__(self, returncode=0, stdout=b"", stderr=b""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


class _Fake:
    """A stand-in for subprocess.run / ac._run_capped that records every call (argv, the stdin script, whether the psql lock was held)."""
    def __init__(self, monkeypatch, result=None, raises=None):
        self.argvs: list[list[str]] = []
        self.scripts: list = []
        self.locked: list[bool] = []
        self.result, self.raises = result or _P(), raises
        monkeypatch.setattr(ac.subprocess, "run", self._run)
        monkeypatch.setattr(ac, "_run_capped", self._capped)

    def _go(self, argv, script):
        self.argvs.append(list(argv))
        self.scripts.append(script)
        self.locked.append(ac._PSQL_LOCK.locked())
        if self.raises is not None:
            raise self.raises
        return self.result

    def _run(self, argv, *a, **k):
        return self._go(argv, None)

    def _capped(self, argv, env, limit, cap, stdin=None):
        r = self._go(argv, stdin)
        return ac._Capped(r.returncode, r.stdout, r.stderr, False)


def _c_args(argv):
    return [argv[i + 1] for i, x in enumerate(argv) if x == "-c"]


def _timeouts_ms(texts):
    """Every `statement_timeout = N` value (SET or SET LOCAL) in the given command texts, in milliseconds."""
    return [int(m.group(1)) for t in texts for m in re.finditer(r"statement_timeout\s*=\s*(\d+)", t)]


# ───────────────────────── the prelude ─────────────────────────

def test_the_constants_are_the_n249_values():
    assert ac.CENSUS_STATEMENT_TIMEOUT_SECONDS == 60 and ac.CENSUS_LOCK_TIMEOUT_SECONDS == 5


def test_prelude_without_a_limit_is_the_full_cap_and_the_lock_timeout():
    assert ac.census_session_prelude(None) == ["SET statement_timeout = 60000", "SET lock_timeout = 5000"]
    assert ac.census_session_prelude() == ["SET statement_timeout = 60000", "SET lock_timeout = 5000"]


@pytest.mark.parametrize("limit,ms", [(180, 60000), (67, 60000), (66, 59400), (30, 27000), (10, 9000), (2, 1800), (1, 900), (0, 1)])
def test_prelude_is_the_smaller_of_the_cap_and_ninety_percent_of_the_client_limit(limit, ms):
    assert ac.census_session_prelude(limit) == [f"SET statement_timeout = {ms}", "SET lock_timeout = 5000"]


@pytest.mark.parametrize("limit", [1, 2, 5, 30, 66, 180, 900, 10 ** 6])
def test_the_prelude_never_exceeds_the_cap_nor_the_client_limit(limit):
    (stmt, _lock) = ac.census_session_prelude(limit)
    ms = int(stmt.rsplit("=", 1)[1])
    assert 1 <= ms <= ac.CENSUS_STATEMENT_TIMEOUT_SECONDS * 1000
    assert ms < limit * 1000, "the server must fire before the client kill"


# ───────────────────────── _psql_run: prelude first, one lock, -q ─────────────────────────

def test_psql_puts_the_prelude_before_the_statement_in_the_same_session(monkeypatch):
    fake = _Fake(monkeypatch, _P(0, b"1\n"))
    assert ac.psql("SELECT 1") == [["1"]]
    (argv,) = fake.argvs
    assert _c_args(argv) == ["SET statement_timeout = 60000", "SET lock_timeout = 5000", "SELECT 1"]     # the default 180 s client limit: 90% = 162 s, capped at 60 s
    assert argv[:2] == ["psql", "-qtAX"] and "ON_ERROR_STOP=1" in argv


def test_the_prelude_uses_the_calls_own_client_limit(monkeypatch):
    fake = _Fake(monkeypatch, _P(0, b"1\n"))
    ac.psql("SELECT 1", timeout=10)
    assert _c_args(fake.argvs[0])[:2] == ["SET statement_timeout = 9000", "SET lock_timeout = 5000"]


def test_quiet_is_always_on_even_when_a_caller_asks_for_it_off(monkeypatch):
    fake = _Fake(monkeypatch, _P(0, b"x\n"))
    ac._psql_run(["SELECT 'x'"], "\x1f", 30, None, quiet=False)
    assert fake.argvs[0][1] == "-qtAX", "without -q the prelude's `SET` tags would be read as result rows"


def test_every_statement_of_a_multi_command_session_follows_the_prelude(monkeypatch):
    fake = _Fake(monkeypatch, _P(0, b"none\n"))
    ac.psql_read_only("SELECT true")
    cmds = _c_args(fake.argvs[0])
    assert cmds[:2] == ac.census_session_prelude(ac.INTEGRITY_TIMEOUT_SECONDS)
    assert cmds[2] == "SET default_transaction_read_only = on" and cmds[3] == "BEGIN READ ONLY" and cmds[-1] == "ROLLBACK"
    assert cmds.index("BEGIN READ ONLY") > cmds.index("SET lock_timeout = 5000")


def test_the_stdin_script_also_starts_with_the_prelude(monkeypatch):
    fake = _Fake(monkeypatch, _P(0, b"none\n"))
    big = "SELECT '" + "x" * (ac.INTEGRITY_ARG_MAX_BYTES + 10) + "' <> ''"
    ac.psql_read_only(big)
    (argv,), (script,) = fake.argvs, fake.scripts
    assert _c_args(argv) == [], "an oversize statement must travel on stdin, not as -c"
    text = script.decode("utf-8")
    assert text.startswith("SET statement_timeout = 60000;\nSET lock_timeout = 5000;\nSET default_transaction_read_only = on;\n")


def test_psql_runs_under_the_one_lock(monkeypatch):
    fake = _Fake(monkeypatch, _P(0, b"1\n"))
    assert not ac._PSQL_LOCK.locked()
    ac.psql("SELECT 1")
    fake.result = _P(0, b"none\n")
    ac.psql_read_only("SELECT true")
    assert fake.locked == [True, True]
    assert not ac._PSQL_LOCK.locked(), "the lock must be released after every run"


def test_the_lock_is_released_when_the_run_fails_or_times_out(monkeypatch):
    _Fake(monkeypatch, raises=subprocess.TimeoutExpired("psql", 1))
    with pytest.raises(ac.CheckTimeout):
        ac.psql("SELECT 1", timeout=1)
    assert not ac._PSQL_LOCK.locked()
    _Fake(monkeypatch, _P(3, b"", TIMEOUT_ERR.encode()))
    with pytest.raises(ac.Unknown):
        ac.psql("SELECT 1")
    assert not ac._PSQL_LOCK.locked()


def test_two_threads_never_run_psql_at_the_same_time(monkeypatch):
    state = {"now": 0, "max": 0}
    guard = threading.Lock()

    def run(argv, *a, **k):
        with guard:
            state["now"] += 1
            state["max"] = max(state["max"], state["now"])
        time.sleep(0.05)
        with guard:
            state["now"] -= 1
        return _P(0, b"1\n")
    monkeypatch.setattr(ac.subprocess, "run", run)
    threads = [threading.Thread(target=lambda: ac.psql("SELECT 1")) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(10)
    assert state["max"] == 1


def test_psql_is_started_in_exactly_one_place():
    """The audit claim behind 'every statement carries the cap': one `["psql", ...]` argv in the whole module, and it is inside `_psql_run`."""
    tree = ast.parse(pathlib.Path(ac.__file__).read_text(encoding="utf-8"))
    hits = []
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for n in ast.walk(fn):
                if isinstance(n, ast.List) and n.elts and isinstance(n.elts[0], ast.Constant) and n.elts[0].value == "psql":
                    hits.append(fn.name)
    assert hits == ["_psql_run"], hits


# ───────────────────────── a statement that hits the cap is an Unknown, never a PASS ─────────────────────────

@pytest.mark.parametrize("err", [TIMEOUT_ERR, "ERROR:  57014: canceling statement due to statement timeout", LOCK_ERR])
def test_a_server_timeout_is_an_unknown_that_names_the_cause(monkeypatch, err):
    _Fake(monkeypatch, _P(3, b"", (err + "\nCONTEXT:  x\n").encode()))
    with pytest.raises(ac.Unknown) as ei:
        ac.scalar("SELECT count(*) FROM big")
    assert ac._is_statement_timeout(ei.value) and ("timeout" in str(ei.value))


def test_a_timeout_never_comes_back_as_rows_or_an_empty_answer(monkeypatch):
    """The `scalar(...) or 'f'` / `psql(...) or []` readings in the census are only safe because a cancelled statement RAISES rather than returning no rows."""
    _Fake(monkeypatch, _P(3, b"", TIMEOUT_ERR.encode()))
    for call in (lambda: ac.psql("SELECT 1"), lambda: ac.scalar("SELECT 1"), lambda: ac.psql_read_only("SELECT true")):
        with pytest.raises(ac.Unknown):
            call()


def test_is_statement_timeout_reads_the_server_text_lock_waits_and_the_client_kill():
    assert ac._is_statement_timeout(ac.Unknown(TIMEOUT_ERR))
    assert ac._is_statement_timeout(ac.Unknown(LOCK_ERR))
    assert ac._is_statement_timeout(ac.CheckTimeout("client-side timeout after 5s"))
    assert not ac._is_statement_timeout(ac.Unknown("ERROR:  permission denied for table t"))
    assert not ac._is_statement_timeout(ac.Unknown("ERROR:  division by zero"))


def test_a_client_kill_names_the_statement_not_the_prelude(monkeypatch):
    _Fake(monkeypatch, raises=subprocess.TimeoutExpired("psql", 5))
    with pytest.raises(ac.CheckTimeout, match="SELECT pg_sleep"):
        ac.psql("SELECT pg_sleep(100)", timeout=5)
    with pytest.raises(ac.CheckTimeout) as ei:
        ac.psql_read_only("SELECT true")
    assert "SET statement_timeout" not in str(ei.value) and "SET lock_timeout" not in str(ei.value)
    assert "DO $" in str(ei.value), "label=3 must still point at the stored statement (the DO block), not at the prepended SETs"


def test_a_closure_walk_chunk_that_hits_the_cap_reads_no_detector_through_the_real_transport(monkeypatch):
    """A chunk of the prose_none closure walk is cancelled by the 60 s cap: the real psql() / scalar() raise, the column is UNREAD, all six cells read NO_DETECTOR."""
    _Fake(monkeypatch, _P(3, b"", TIMEOUT_ERR.encode()))
    monkeypatch.setattr(ac, "source_estimate_rows", lambda t: 10 ** 7)
    out = ac.prose_none_fetch_outside(wb.TABLES, "t", wb.PN)
    assert "statement timeout" in out[("t", "c")]["unread"] and "neither a PASS nor a FAIL" in out[("t", "c")]["unread"]
    cells = wb._cells(out)
    assert all(v["v"] == ac.NO_DET for v in cells.values()), {k: v["v"] for k, v in cells.items()}
    assert not any(v["v"] in (ac.PASS, ac.NA, ac.ERRORED) for v in cells.values())


def test_a_lock_timeout_in_the_walk_is_equally_unread(monkeypatch):
    _Fake(monkeypatch, _P(3, b"", LOCK_ERR.encode()))
    monkeypatch.setattr(ac, "source_estimate_rows", lambda t: 10 ** 7)
    out = ac.prose_none_fetch_outside(wb.TABLES, "t", wb.PN)
    assert all(v["v"] == ac.NO_DET for v in wb._cells(out).values())


def test_the_walk_budget_is_still_600_and_a_cap_sized_chunk_cannot_hide_inside_it():
    """The 600 s walk budget and the 60 s statement cap are different bounds: ten capped chunks exhaust the budget, they never close the walk."""
    assert ac.PROSE_NONE_WALK_BUDGET_SECS == 600 and ac.PROSE_NONE_WALK_BUDGET_SECS > ac.CENSUS_STATEMENT_TIMEOUT_SECONDS
    assert ac.PROSE_NONE_CHUNK_TARGET_SECS * 2 < ac.CENSUS_STATEMENT_TIMEOUT_SECONDS, "a chunk shrinks past 8 s, far inside the cap"


# ───────────────────────── psql_read_only never exceeds the cap ─────────────────────────

@pytest.mark.parametrize("timeout", [None, 1, 2, 10, 66, 67, 180, 1000, 10 ** 6])
def test_psql_read_only_never_exceeds_the_cap(monkeypatch, timeout):
    fake = _Fake(monkeypatch, _P(0, b"none\n"))
    ac.psql_read_only("SELECT true", timeout=timeout)
    ms = _timeouts_ms(_c_args(fake.argvs[0]))
    assert len(ms) == 2, "the prelude's session cap and the transaction's SET LOCAL"
    assert all(1 <= m <= ac.CENSUS_STATEMENT_TIMEOUT_SECONDS * 1000 for m in ms), ms
    limit = timeout if timeout is not None else ac.INTEGRITY_TIMEOUT_SECONDS
    assert all(m < limit * 1000 for m in ms), "the server must fire before the client kill"


def test_psql_read_only_on_stdin_never_exceeds_the_cap_either(monkeypatch):
    fake = _Fake(monkeypatch, _P(0, b"none\n"))
    ac.psql_read_only("SELECT '" + "x" * (ac.INTEGRITY_ARG_MAX_BYTES + 10) + "' <> ''", timeout=10 ** 6)
    ms = _timeouts_ms([fake.scripts[0].decode("utf-8")])
    assert ms == [60000, 60000]


def test_a_read_only_timeout_is_partial_not_pass(monkeypatch):
    """The Build.completion integrity outcome for a cancelled integrity SQL: unrunnable (PARTIAL), never `holds`."""
    _Fake(monkeypatch, _P(3, b"", TIMEOUT_ERR.encode()))
    out = ac._integrity_outcome("SELECT true")
    assert out["state"] != "holds", out
