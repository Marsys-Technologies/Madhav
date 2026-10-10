"""test_n430_hygiene_cap.py: SS N-430 T2, the CONFIGURABLE STATEMENT CAP, OFF BY DEFAULT.

SUVARNA_CENSUS_STATEMENT_CAP_SECS: unset / empty = exactly today's psql command line; a positive integer N = every census psql session starts with
`SET statement_timeout = N*1000` and `SET lock_timeout = 5000`; anything else refuses loudly before any read; the integrity runner is EXEMPT.

Offline (a fake psql records the argv) plus ONE real statement-timeout test on a disposable PostgreSQL (pg_sleep under a 1 s cap).
"""
from __future__ import annotations

import pathlib
import re
import sys
import time

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401  (the session fixture)
from _n430_fakes import FakePsql, ok  # noqa: E402

ENV = ac.CENSUS_STATEMENT_CAP_ENV
SEP = "\x1f"
TODAY = ["psql", "-tAX", "-F", SEP, "-v", "ON_ERROR_STOP=1", "-c", "SELECT 1"]       # the command line before N-430, byte for byte


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.delenv(ENV, raising=False)
    ac.drain_read_log()
    yield
    ac.drain_read_log()


# ───────────────────────── OFF by default: zero change ─────────────────────────

@pytest.mark.parametrize("value", [None, ""])
def test_unset_or_empty_is_exactly_todays_command_line(monkeypatch, value):
    if value is not None:
        monkeypatch.setenv(ENV, value)
    fake = FakePsql(monkeypatch, ac)
    assert ac.census_statement_cap_secs() is None
    assert ac.psql("SELECT 1") == [["1"]]
    assert fake.calls == [TODAY]


def test_off_keeps_the_quiet_flag_exactly_as_the_caller_asked(monkeypatch):
    fake = FakePsql(monkeypatch, ac)
    ac._psql_run(["SELECT 1"], SEP, 30, None, quiet=True)
    assert fake.calls[0][1] == "-qtAX" and fake.commands() == ["SELECT 1"]


# ───────────────────────── ON: the session commands come first, in the same session ─────────────────────────

def test_a_positive_integer_prepends_the_two_session_commands(monkeypatch):
    monkeypatch.setenv(ENV, "60")
    fake = FakePsql(monkeypatch, ac)
    assert ac.census_statement_cap_secs() == 60
    assert ac.psql("SELECT 1") == [["1"]]
    assert fake.calls == [["psql", "-qtAX", "-F", SEP, "-v", "ON_ERROR_STOP=1",
                           "-c", "SET statement_timeout = 60000", "-c", "SET lock_timeout = 5000", "-c", "SELECT 1"]]


def test_the_cap_value_is_used_in_milliseconds(monkeypatch):
    monkeypatch.setenv(ENV, "7")
    fake = FakePsql(monkeypatch, ac)
    ac.psql("SELECT 1")
    assert fake.commands()[:2] == ["SET statement_timeout = 7000", "SET lock_timeout = 5000"]


def test_the_cap_reaches_the_stdin_script_form_too(monkeypatch):
    monkeypatch.setenv(ENV, "9")
    fake = FakePsql(monkeypatch, ac)
    ac._psql_run(["SELECT 1"], SEP, 30, None, cap=1000, via_stdin=True)
    assert fake.calls[0][-1] == "<<stdin:SET statement_timeout = 9000;\nSET lock_timeout = 5000;\nSELECT 1;\n>>"
    assert "-c" not in fake.calls[0]


def test_a_client_timeout_message_still_names_the_statement_not_the_prelude(monkeypatch):
    monkeypatch.setenv(ENV, "5")
    FakePsql(monkeypatch, ac, ["timeout"])
    with pytest.raises(ac.CheckTimeout, match="SELECT 1"):
        ac.psql("SELECT 1")


# ───────────────────────── malformed: refuse loudly, never ignore ─────────────────────────

BAD = ["0", "-5", "+5", "5.0", "abc", " 5", "5 ", "007", "1e3", "5s", "86401", "9999999", "٣", "5\n"]


@pytest.mark.parametrize("value", BAD)
def test_a_malformed_cap_refuses_before_psql_is_started(monkeypatch, value):
    monkeypatch.setenv(ENV, value)
    fake = FakePsql(monkeypatch, ac)
    with pytest.raises(SystemExit) as ei:
        ac.psql("SELECT 1")
    assert isinstance(ei.value, ac.CensusCapRefused) and ENV in str(ei.value.code)
    assert fake.calls == [], "a malformed cap must refuse BEFORE any psql run"
    with pytest.raises(SystemExit):
        ac.psql_read_only("SELECT true")                       # the exempt runner is not a way round a bad setting: it refuses too


def test_the_refusal_is_not_swallowed_by_a_per_check_guard(monkeypatch):
    """CensusCapRefused is a SystemExit: the `except Exception` / `except Unknown` guards around the checks cannot turn a bad setting into an ERRORED cell."""
    monkeypatch.setenv(ENV, "nope")
    FakePsql(monkeypatch, ac)
    assert not issubclass(ac.CensusCapRefused, Exception)
    try:
        try:
            ac.psql("SELECT 1")
        except Exception:                                       # noqa: BLE001
            pytest.fail("swallowed by an except Exception")
    except SystemExit:
        pass


@pytest.mark.parametrize("value", ["abc", "0", "-1", "5.5"])
def test_main_exits_14_before_any_read(monkeypatch, tmp_path, capsys, value):
    monkeypatch.setenv(ENV, value)
    fake = FakePsql(monkeypatch, ac)
    monkeypatch.setattr(ac, "measure", lambda *a, **k: pytest.fail("measure ran"))
    monkeypatch.setattr(ac, "census_stamp", lambda: pytest.fail("census_stamp ran"))
    out = tmp_path / "c.json"
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", "L1", "--out", str(out)])
    assert ac.main() == ac.EXIT_STATEMENT_CAP_REFUSED == 14
    assert fake.calls == [] and not out.exists()
    err = capsys.readouterr().err
    assert ENV in err and "refused" in err


def test_main_with_a_valid_cap_says_so_and_records_it(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv(ENV, "45")
    fake = FakePsql(monkeypatch, ac)
    monkeypatch.setattr(ac, "census_stamp", lambda: dict(registry_revision=1, registry_fingerprint="f" * 64))
    from test_n430_hygiene_timings import _fake_measure
    monkeypatch.setattr(ac, "measure", _fake_measure)
    out = tmp_path / "c.json"
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", "L1", "--out", str(out)])
    assert ac.main() == 0
    import json
    assert json.loads(out.read_text())["L1"]["read_timings"]["statement_cap_secs"] == 45
    assert "statement cap ACTIVE" in capsys.readouterr().err
    assert all(c[6:10] == ["-c", "SET statement_timeout = 45000", "-c", "SET lock_timeout = 5000"] for c in fake.calls)


def test_main_without_a_cap_records_none_and_prints_no_notice(monkeypatch, tmp_path, capsys):
    fake = FakePsql(monkeypatch, ac)
    monkeypatch.setattr(ac, "census_stamp", lambda: dict(registry_revision=1, registry_fingerprint="f" * 64))
    from test_n430_hygiene_timings import _fake_measure
    monkeypatch.setattr(ac, "measure", _fake_measure)
    out = tmp_path / "c.json"
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", "L1", "--out", str(out)])
    assert ac.main() == 0
    import json
    assert json.loads(out.read_text())["L1"]["read_timings"]["statement_cap_secs"] is None
    assert "statement cap" not in capsys.readouterr().err
    assert fake.calls and all("SET statement_timeout" not in " ".join(c) for c in fake.calls)


# ───────────────────────── the integrity runner is EXEMPT ─────────────────────────

def test_the_integrity_runner_keeps_its_own_budget_whatever_the_cap_is(monkeypatch):
    fake_off = FakePsql(monkeypatch, ac, [ok(b"none\n")])
    ac.psql_read_only("SELECT true", timeout=180)
    nonce = lambda xs: [re.sub(r"n99\.i_[0-9a-f]{24}", "n99.i_NONCE", x) for x in xs]        # the read-back setting's name is a per-run random nonce
    cmds_off, argv_off = nonce(fake_off.commands()), nonce(fake_off.calls[0])
    monkeypatch.setenv(ENV, "1")                                # a 1 s cap must not touch the integrity run
    fake_on = FakePsql(monkeypatch, ac, [ok(b"none\n")])
    ac.psql_read_only("SELECT true", timeout=180)
    assert nonce(fake_on.commands()) == cmds_off and nonce(fake_on.calls[0]) == argv_off, "the integrity run's command line is identical with and without the cap"
    assert "SET LOCAL statement_timeout = 162000" in cmds_off          # 90% of the 180 s client limit: unchanged
    assert not any(c.startswith("SET statement_timeout") or c.startswith("SET lock_timeout") for c in cmds_off)


def test_the_integrity_runner_default_budget_is_not_capped_by_a_small_cap(monkeypatch):
    monkeypatch.setenv(ENV, "1")
    fake = FakePsql(monkeypatch, ac, [ok(b"none\n")])
    ac.psql_read_only("SELECT true")
    assert f"SET LOCAL statement_timeout = {int(ac.INTEGRITY_TIMEOUT_SECONDS * 900)}" in fake.commands()


# ───────────────────────── REAL: one statement-timeout test on a disposable PostgreSQL ─────────────────────────

@pytest.fixture
def pg(disposable_pg, monkeypatch):
    point_psql_at(disposable_pg, monkeypatch)
    ident = ac.psql("SELECT inet_server_port()::text, current_database()")
    assert ident == [[str(disposable_pg.port), disposable_pg.dbname]], f"refusing to run: not the disposable cluster ({ident!r})"
    ac.drain_read_log()
    return disposable_pg


def test_real_a_one_second_cap_cancels_pg_sleep_and_the_integrity_run_is_not_capped(pg, monkeypatch):
    t0 = time.monotonic()
    assert ac.psql("SELECT 'no cap'") == [["no cap"]]                  # off: the plain read still works and returns its rows
    monkeypatch.setenv(ENV, "1")
    assert ac.psql("SELECT 'rows stay clean'") == [["rows stay clean"]]    # the SET command tags never leak into the rows
    t1 = time.monotonic()
    with pytest.raises(ac.Unknown, match="statement timeout") as ei:
        ac.psql("SELECT pg_sleep(4)")
    assert time.monotonic() - t1 < 3.5, "the server cancelled the sleep at ~1 s, not at 4 s"
    assert ac._read_timeout_kind(ei.value) == "statement"
    assert [e["outcome"] for e in ac.drain_read_log()][-1] == "timeout"
    # the integrity runner, same 1 s cap in the environment: a 2.5 s statement still completes (its own budget is 90% of its client limit)
    t2 = time.monotonic()
    assert ac.psql_read_only("SELECT true FROM (SELECT pg_sleep(2.5)) s") == [["t"]]
    assert time.monotonic() - t2 >= 2.4
    assert time.monotonic() - t0 < 30
