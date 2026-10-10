"""test_n431_integrity_budget.py -- N-431 (W8): the census integrity runner has its OWN explicit, recorded statement budget.

Before: a registry-stored `integrity_check_sql` ran under 90% of PSQL_TIMEOUT_SECONDS (162 s of the 180 s default), so a CORRECT but slow check
(ga_structural's, ~208 KB) was cancelled by the server (SQLSTATE 57014) and the Build.completion cell read PARTIAL 'could NOT be run'.
Now: INTEGRITY_BUDGET_SECS = 600 (env SUVARNA_CENSUS_INTEGRITY_BUDGET_SECS, a positive integer, malformed = refused before any read) is the
`SET LOCAL statement_timeout` of the integrity transaction ONLY, the psql wall-clock kill is budget + INTEGRITY_CLIENT_MARGIN_SECS, and the cell text
states the budget and the elapsed seconds on success and on timeout.

No database: psql is FAKED (the capped runner and subprocess.run are replaced), so every assertion is on the exact commands, settings and time limit
sent. Deliberate breaks are exercised by the mutation runs recorded in the report, not by in-test source surgery.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import census_postprocess as cp  # noqa: E402

ENV = "SUVARNA_CENSUS_INTEGRITY_BUDGET_SECS"
REAL = json.loads((HERE / "n268_real_cells.json").read_text(encoding="utf-8"))
SQL = "SELECT count(*) = 3 FROM t_guard"
SHA = hashlib.sha256(SQL.encode()).hexdigest()[:12]


class FakeClock:
    """time.monotonic() that only moves when the fake psql says so; every other `time` attribute is the real one."""
    def __init__(self):
        self.now = 1000.0

    def monotonic(self):
        return self.now

    def __getattr__(self, name):
        import time
        return getattr(time, name)


class FakePsql:
    """Replaces both psql entry points of the census: ordinary reads (`subprocess.run`) and the capped integrity path (`_run_capped`).
    Records, per call, the exact `-c` commands (or stdin script) and the wall-clock limit handed to the subprocess."""
    def __init__(self, monkeypatch, *, ran=0.0, outcome="holds"):
        self.calls: list[dict] = []
        self.ran, self.outcome = ran, outcome
        self.clock = FakeClock()
        monkeypatch.setattr(ac, "time", self.clock)
        monkeypatch.setattr(ac, "_run_capped", self._capped)
        monkeypatch.setattr(ac.subprocess, "run", self._run)

    @staticmethod
    def _cmds(argv, stdin):
        cmds = [argv[i + 1] for i, x in enumerate(argv) if x == "-c" and i + 1 < len(argv)]
        if stdin is not None:
            cmds += [c for c in stdin.decode("utf-8").split(";\n") if c]
        return cmds

    def _capped(self, argv, env, limit, cap, stdin=None):
        self.calls.append(dict(kind="integrity", cmds=self._cmds(argv, stdin), limit=limit))
        self.clock.now += self.ran
        if self.outcome == "client_kill":
            raise subprocess.TimeoutExpired(argv, limit)
        if self.outcome == "server_timeout":
            return ac._Capped(1, b"", b"ERROR:  57014: canceling statement due to statement timeout\n", False)
        if self.outcome == "denied":
            return ac._Capped(1, b"", b"ERROR:  42501: permission denied for function bodha_signal_identity\n", False)
        if self.outcome == "broken":
            return ac._Capped(1, b"", b'ERROR:  42P01: relation "no_such_table" does not exist\n', False)
        if self.outcome == "false":
            return ac._Capped(0, b"row 5 false\n", b"", False)
        return ac._Capped(0, b"row 4 true\n", b"", False)

    def _run(self, argv, *a, **k):
        self.calls.append(dict(kind="ordinary", cmds=self._cmds(argv, None), limit=k.get("timeout")))
        return subprocess.CompletedProcess(argv, 0, b"1\n", b"")

    def of(self, kind):
        return [c for c in self.calls if c["kind"] == kind]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv(ENV, raising=False)


def _rec():
    return dict(v=ac.PASS, measured="rows_written=5 = live=5 (count_sql over the target table; chart 482012f1)")


def _cell(sql=SQL):
    return ac._completion_integrity(_rec(), dict(integrity_sql=sql))


# ───────────────────────── the budget: constant, env override, refusal ─────────────────────────

def test_the_default_budget_is_600_seconds():
    assert ac.INTEGRITY_BUDGET_SECS == 600 and ac.integrity_budget_secs() == 600


def test_the_budget_is_independent_of_the_ordinary_read_timeout(monkeypatch):
    monkeypatch.setattr(ac, "PSQL_TIMEOUT_SECONDS", 7)
    assert ac.integrity_budget_secs() == 600


def test_the_env_override_is_honoured(monkeypatch):
    monkeypatch.setenv(ENV, "900")
    assert ac.integrity_budget_secs() == 900
    fake = FakePsql(monkeypatch)
    ac.psql_read_only("SELECT true")
    (call,) = fake.of("integrity")
    assert "SET LOCAL statement_timeout = 900000" in call["cmds"] and call["limit"] == 900 + ac.INTEGRITY_CLIENT_MARGIN_SECS


@pytest.mark.parametrize("bad", ["", " ", "abc", "0", "-5", "+600", "1.5", "1e3", "6_0", "600s", "0x10", "٣٠٠", "99999999", "600\n", " 600"])
def test_a_malformed_override_is_refused(monkeypatch, bad):
    monkeypatch.setenv(ENV, bad)
    with pytest.raises(ac.IntegrityBudgetRefused):
        ac.integrity_budget_secs()


def test_a_malformed_override_is_refused_before_any_psql_is_run(monkeypatch):
    monkeypatch.setenv(ENV, "ten")
    fake = FakePsql(monkeypatch)
    with pytest.raises(ac.IntegrityBudgetRefused):
        ac.psql_read_only("SELECT true")
    with pytest.raises(ac.IntegrityBudgetRefused):
        ac._integrity_outcome(SQL)                     # not swallowed into a PARTIAL 'could NOT be run': a bad budget is the operator's error
    with pytest.raises(ac.IntegrityBudgetRefused):
        _cell()
    assert fake.calls == []


def test_main_refuses_a_malformed_override_before_any_read(monkeypatch, capsys):
    monkeypatch.setenv(ENV, "-1")

    def boom(*a, **k):
        raise AssertionError("a read happened before the budget was validated")
    for name in ("registry", "validate_scope", "census_stamp", "measure", "psql", "scalar"):
        monkeypatch.setattr(ac, name, boom)
    monkeypatch.setattr(ac.subprocess, "run", boom)
    monkeypatch.setattr(ac.subprocess, "Popen", boom)
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", "L4"])
    assert ac.main() == ac.EXIT_INTEGRITY_BUDGET == 15
    err = capsys.readouterr().err
    assert "integrity budget refused" in err and ENV in err


# ───────────────────────── what is sent, and to which statement ─────────────────────────

def test_the_budget_is_the_server_statement_timeout_of_the_integrity_transaction_only(monkeypatch):
    fake = FakePsql(monkeypatch)
    ac.psql_read_only("SELECT true")
    (call,) = fake.of("integrity")
    assert call["cmds"][:3] == ["SET default_transaction_read_only = on", "BEGIN READ ONLY", "SET LOCAL statement_timeout = 600000"], call["cmds"]
    assert call["cmds"][-1] == "ROLLBACK"
    assert sum("statement_timeout" in c for c in call["cmds"]) == 1


def test_the_client_wall_clock_kill_is_never_shorter_than_the_budget(monkeypatch):
    fake = FakePsql(monkeypatch)
    ac.psql_read_only("SELECT true")
    (call,) = fake.of("integrity")
    assert ac.INTEGRITY_CLIENT_MARGIN_SECS >= 10
    assert call["limit"] >= ac.integrity_budget_secs() + ac.INTEGRITY_CLIENT_MARGIN_SECS
    assert call["limit"] > 600


def test_an_oversize_integrity_text_goes_on_stdin_with_the_same_budget_and_limit(monkeypatch):
    fake = FakePsql(monkeypatch)
    big = "SELECT true /* " + "x" * 150_000 + " */"
    ac.psql_read_only(big)
    (call,) = fake.of("integrity")
    assert "SET LOCAL statement_timeout = 600000" in call["cmds"] and call["limit"] == 600 + ac.INTEGRITY_CLIENT_MARGIN_SECS


def test_ordinary_reads_never_receive_the_integrity_budget(monkeypatch):
    monkeypatch.setenv(ENV, "900")
    fake = FakePsql(monkeypatch)
    assert ac.psql("SELECT 1") == [["1"]]
    assert ac.scalar("SELECT 1") == "1"
    ac.psql("SELECT 2", timeout=45)
    ordinary = fake.of("ordinary")
    assert [c["cmds"] for c in ordinary] == [["SELECT 1"], ["SELECT 1"], ["SELECT 2"]]
    assert [c["limit"] for c in ordinary] == [ac.PSQL_TIMEOUT_SECONDS, ac.PSQL_TIMEOUT_SECONDS, 45]
    assert not any("statement_timeout" in c for call in ordinary for c in call["cmds"])
    assert fake.of("integrity") == []


def test_an_ordinary_read_and_an_integrity_run_in_one_process_keep_their_own_limits(monkeypatch):
    fake = FakePsql(monkeypatch)
    ac.psql("SELECT 1")
    ac.psql_read_only("SELECT true")
    ac.psql("SELECT 3")
    assert [c["kind"] for c in fake.calls] == ["ordinary", "integrity", "ordinary"]
    assert fake.calls[0]["limit"] == fake.calls[2]["limit"] == ac.PSQL_TIMEOUT_SECONDS
    assert fake.calls[1]["limit"] == 600 + ac.INTEGRITY_CLIENT_MARGIN_SECS
    assert all("statement_timeout" not in c for i in (0, 2) for c in fake.calls[i]["cmds"])


def test_the_outcome_runs_the_statement_with_the_budget_it_records(monkeypatch):
    monkeypatch.setenv(ENV, "777")
    fake = FakePsql(monkeypatch, ran=3.0)
    o = ac._integrity_outcome(SQL)
    (call,) = fake.of("integrity")
    assert o["budget"] == 777 and "SET LOCAL statement_timeout = 777000" in call["cmds"]


# ───────────────────────── what is recorded ─────────────────────────

def test_success_records_the_budget_and_the_elapsed_seconds(monkeypatch):
    FakePsql(monkeypatch, ran=211.4)
    c = _cell()
    assert c["v"] == ac.PASS
    assert f"[integrity_check_sql sha256:{SHA}, 211.4s]" in c["measured"]
    assert "[integrity budget 600s; ran 211.4s]" in c["measured"] and "cut off" not in c["measured"]
    assert "the declared integrity_check_sql holds" in c["measured"]


def test_a_server_timeout_still_reads_partial_and_records_budget_and_elapsed(monkeypatch):
    FakePsql(monkeypatch, ran=600.3, outcome="server_timeout")
    c = _cell()
    assert c["v"] == ac.PARTIAL
    assert "the declared integrity_check_sql could NOT be run" in c["measured"] and "57014" in c["measured"]
    assert "[integrity budget 600s; ran 600.3s; cut off at the budget]" in c["measured"]
    assert c["measured"].endswith("— count equality alone is not a completion when the asset declares an integrity check (N-99)")


def test_a_client_kill_still_reads_partial_and_records_budget_and_elapsed(monkeypatch):
    FakePsql(monkeypatch, ran=630.0, outcome="client_kill")
    c = _cell()
    assert c["v"] == ac.PARTIAL and "CheckTimeout" in c["measured"] and "client-side timeout after 630s" in c["measured"]
    assert "[integrity budget 600s; ran 630.0s; cut off at the budget]" in c["measured"]


def test_a_broken_check_is_not_labelled_as_cut_off_by_the_budget(monkeypatch):
    FakePsql(monkeypatch, ran=0.4, outcome="broken")
    c = _cell()
    assert c["v"] == ac.PARTIAL and "could NOT be run" in c["measured"]
    assert "[integrity budget 600s; ran 0.4s]" in c["measured"] and "cut off" not in c["measured"]


def test_a_false_check_records_the_budget_too(monkeypatch):
    FakePsql(monkeypatch, ran=12.0, outcome="false")
    c = _cell()
    assert c["v"] == ac.PARTIAL and "does NOT hold" in c["measured"] and "[integrity budget 600s; ran 12.0s]" in c["measured"]


def test_the_recorded_budget_follows_the_override(monkeypatch):
    monkeypatch.setenv(ENV, "1200")
    FakePsql(monkeypatch, ran=5.0)
    assert "[integrity budget 1200s; ran 5.0s]" in _cell()["measured"]


def test_a_cell_with_no_declared_integrity_sql_is_untouched_and_runs_nothing(monkeypatch):
    fake = FakePsql(monkeypatch)
    rec = _rec()
    assert ac._completion_integrity(rec, dict(integrity_sql=None)) == rec and fake.calls == []


# ───────────────────────── census_postprocess still classifies every cell text as before ─────────────────────────

def _named(text, v="NO_DETECTOR"):
    return cp.named_item("bo_laksana", "Build.completion", dict(v=v, cause=text, state="MEASURED"))


def test_the_old_census_role_denied_text_still_matches_its_matcher():
    r = _named(REAL["not-measurable:Build.completion:census-role-denied"]["text"])
    assert r and r["kind"] == "ceiling" and r["reason"].startswith("not measurable: ")


def test_the_new_census_role_denied_text_matches_its_matcher(monkeypatch):
    FakePsql(monkeypatch, ran=2.59, outcome="denied")
    c = ac._completion_integrity(dict(v=ac.PASS, measured="rows_written=126769 = live=126769 (count_sql over the target table; chart 482012f1)"),
                                 dict(integrity_sql=SQL))
    assert c["v"] == ac.NO_DET and "[integrity budget 600s; ran 2.59s]; counts:" in c["measured"]
    r = _named(c["measured"])
    assert r and r["kind"] == "ceiling" and r["pattern"] == "not-measurable:Build.completion:census-role-denied", r


def test_a_forged_budget_note_does_not_widen_the_matcher():
    real = REAL["not-measurable:Build.completion:census-role-denied"]["text"]
    for forged in (real.replace("2.59s];", "2.59s] [integrity budget abc; ran 1s];"),
                   real.replace("2.59s];", "2.59s] [integrity budget 600s; ran 1s] [x];"),
                   real.replace("live=126769 (", "live=126000 (")):
        assert forged != real and _named(forged) is None


def test_the_holds_cell_is_still_recognised_as_an_integrity_statement_and_as_an_empty_by_design_completion(monkeypatch):
    FakePsql(monkeypatch, ran=211.4)
    c = _cell()
    assert cp.INTEGRITY_HOLDS in c["measured"]
    assert not cp.is_counts_only_completion({cp.BUILD_COMPLETION: dict(v="PASS", cause=c["measured"])})
    zero = ("rows_written=0 = live=0 (count_sql over the target table; chart 482012f1); zero rows by declared convention (zero_row_convention, N-12), verified: chart 482012f1 "
            "has no row in public.prashna_charts; the declared integrity_check_sql holds (first column of the first row = 't') " + re.search(r"\[.*", c["measured"]).group(0))
    assert cp._E_COMPLETION.fullmatch(zero)


def test_the_partial_cells_have_no_named_partial_matcher_so_their_classification_is_unchanged(monkeypatch):
    """No NAMED_PARTIALS pattern reads a Build.completion integrity text, before or after this change: a timed-out check stays an unnamed PARTIAL (a blocker)."""
    assert not [p for p in cp.NAMED_PARTIALS if p[1] == "Build.completion" and "integrity" in p[0]]
    FakePsql(monkeypatch, ran=600.3, outcome="server_timeout")
    c = _cell()
    assert cp.named_item("ga_structural", "Build.completion", dict(v="PARTIAL", cause=c["measured"], state="MEASURED")) is None
