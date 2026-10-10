"""test_n430_hygiene_timings.py: SS N-430 T1, PER-READ ELAPSED RECORDING (verdict-neutral).

Every psql read the census makes is timed and attributed (asset, read label, elapsed seconds, retries, outcome) and the layer head carries a bounded
`read_timings` summary, so a person can set a statement cap from evidence. These tests prove, offline with a fake psql and a fake clock:
  * the entry carries the exact elapsed seconds, the asset and the explicit read label; else the statement's first 60 characters with every literal stripped;
  * no value, host, credential or full statement is ever stored;
  * a failed read and a timed-out read are recorded too (outcome error / timeout);
  * the summary is bounded per asset and carries per-asset totals and the overall maximum;
  * `main()` writes `read_timings` into the layer head and NOTHING ELSE of the head changes (verdict-neutral); a rollup computed over a head that carries it is identical;
  * `read_timings_report` (and `--read-timings-report`) print the slowest reads.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _n430_fakes import FakeClock, FakePsql, fail, ok  # noqa: E402


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.delenv("SUVARNA_CENSUS_STATEMENT_CAP_SECS", raising=False)
    ac.drain_read_log()
    ac.set_read_asset(None)
    yield
    ac.drain_read_log()
    ac.set_read_asset(None)


def test_an_entry_carries_the_exact_elapsed_seconds_and_the_asset(monkeypatch):
    clock = FakeClock()
    monkeypatch.setattr(ac, "time", clock)
    FakePsql(monkeypatch, ac, [ok(b"1\n")], clock=clock, elapsed=2.5)
    ac.set_read_asset("ga_alpha")
    ac.psql("SELECT 1")
    (e,) = ac.drain_read_log()
    assert e == dict(asset="ga_alpha", label="SELECT ?", seconds=2.5, retries=0, outcome="ok")


def test_an_explicit_read_label_wins_over_the_statement_head(monkeypatch):
    FakePsql(monkeypatch, ac)
    ac.set_read_asset("bo_x")
    with ac.read_label("Vocab.identity"):
        ac.psql("SELECT 1")
    ac.psql("SELECT 2 FROM chart_facts")                       # outside the block: back to the statement head
    a, b = ac.drain_read_log()
    assert (a["asset"], a["label"]) == ("bo_x", "Vocab.identity")
    assert (b["asset"], b["label"]) == ("bo_x", "SELECT ? FROM chart_facts")


def test_read_label_nests_and_restores(monkeypatch):
    FakePsql(monkeypatch, ac)
    with ac.read_label("outer", asset="a1"):
        with ac.read_label("inner"):
            ac.psql("SELECT 1")
        ac.psql("SELECT 1")
    ac.psql("SELECT 1")
    inner, outer, after = ac.drain_read_log()
    assert (inner["asset"], inner["label"]) == ("a1", "inner")
    assert (outer["asset"], outer["label"]) == ("a1", "outer")
    assert (after["asset"], after["label"]) == (None, "SELECT ?")


def test_the_statement_label_strips_every_literal_and_is_at_most_60_chars():
    secret = "Abhisek-Secret-Value-1984"
    stmts = [f"SELECT x FROM t WHERE name = '{secret}' AND n = 42 AND r = 3.14",
             f"SELECT x FROM t WHERE name = 'it''s {secret}'",
             f"SELECT $q${secret}$q$ FROM t",
             f"SELECT x FROM t WHERE name = '{secret}",                 # an unterminated quote: its tail is dropped too
             "DO $n99d0$ BEGIN PERFORM 1; END $n99d0$"]
    for sql in stmts:
        lab = ac._statement_label(sql)
        assert secret not in lab and len(lab) <= 60, (sql, lab)
    assert ac._statement_label(stmts[0]) == "SELECT x FROM t WHERE name = ? AND n = ? AND r = ?"
    assert ac._statement_label("SELECT\n  a,\n\tb   FROM t") == "SELECT a, b FROM t"
    assert ac._statement_label("x" * 200) == "x" * 60


def test_no_host_credential_value_or_full_statement_is_stored(monkeypatch):
    monkeypatch.setenv("PGHOST", "db.internal.example")
    monkeypatch.setenv("PGPASSWORD", "hunter" + "2")
    FakePsql(monkeypatch, ac, [fail("psql: error: connection to server at db.internal.example failed: FATAL: password authentication failed for user bob")])
    secret = "Abhisek-Secret-Value-1984"
    with pytest.raises(ac.Unknown):
        ac.psql(f"SELECT '{secret}', pg_sleep(12345), a_very_long_column_name_to_push_past_sixty_characters_of_text FROM some_table")
    blob = json.dumps(ac.drain_read_log())
    for forbidden in (secret, "db.internal.example", "hunter", "bob", "12345", "some_table"):
        assert forbidden not in blob, (forbidden, blob)


def test_a_failed_read_and_a_timed_out_read_are_recorded_with_their_outcome(monkeypatch):
    FakePsql(monkeypatch, ac, [fail("ERROR:  relation \"x\" does not exist")])
    with pytest.raises(ac.Unknown):
        ac.psql("SELECT 1 FROM x")
    FakePsql(monkeypatch, ac, [fail("ERROR:  canceling statement due to statement timeout")])
    with pytest.raises(ac.Unknown):
        ac.psql("SELECT 1 FROM x")
    FakePsql(monkeypatch, ac, ["timeout"])
    with pytest.raises(ac.CheckTimeout):
        ac.psql("SELECT 1 FROM x")
    assert [e["outcome"] for e in ac.drain_read_log()] == ["error", "timeout", "timeout"]


def test_a_malformed_output_is_recorded_as_an_error(monkeypatch):
    FakePsql(monkeypatch, ac, [ok(b"unterminated")])            # no trailing newline: a ReadError
    with pytest.raises(ac.ReadError):
        ac.psql("SELECT 1")
    assert [e["outcome"] for e in ac.drain_read_log()] == ["error"]


def test_the_summary_is_bounded_per_asset_with_totals_and_the_overall_maximum():
    entries = [dict(asset="ga_a", label=f"r{i}", seconds=float(i), retries=0, outcome="ok") for i in range(1, 21)]
    entries += [dict(asset="ga_b", label="only", seconds=100.0, retries=1, outcome="ok"), dict(asset=None, label="registry", seconds=0.25, retries=0, outcome="ok")]
    s = ac.read_timings_summary(entries)
    assert s["n_reads"] == 22 and s["total_seconds"] == round(210.0 + 100.0 + 0.25, 3)
    assert s["max_seconds"] == 100.0 and s["max_read"] == dict(asset="ga_b", label="only")
    by = {p["asset"]: p for p in s["per_asset"]}
    assert list(by) == ["(layer)", "ga_a", "ga_b"]                                  # sorted by asset id; no asset = (layer)
    a = by["ga_a"]
    assert a["n_reads"] == 20 and a["total_seconds"] == 210.0 and a["max_seconds"] == 20.0
    assert [r["label"] for r in a["slowest"]] == ["r20", "r19", "r18", "r17", "r16"]      # bounded to the slowest 5
    assert by["ga_b"]["slowest"] == [dict(label="only", seconds=100.0, retries=1, outcome="ok")]
    json.dumps(s)                                                                   # plain JSON
    empty = ac.read_timings_summary([])
    assert empty["n_reads"] == 0 and empty["max_read"] is None and empty["per_asset"] == []


def test_read_timings_report_prints_the_slowest_reads(tmp_path):
    entries = [dict(asset="ga_a", label=f"r{i}", seconds=float(i), retries=0, outcome="ok") for i in range(1, 8)]
    entries.append(dict(asset="ga_b", label="slowpoke", seconds=74.29, retries=1, outcome="ok"))
    census = {"L1": {"layer": "L1", "read_timings": ac.read_timings_summary(entries)}, "rollup": {"x": 1}}
    text = ac.read_timings_report(census, top=3)
    lines = text.splitlines()
    assert lines[0].startswith("L1: 8 read(s)") and "slowest 74.29 s (ga_b: slowpoke)" in lines[0]
    assert len(lines) == 4                                                           # the header + the 3 slowest
    assert "74.290 s  ga_b  slowpoke  [ok, retries 1]" in lines[1]
    assert lines[2].split()[0] == "7.000" and lines[3].split()[0] == "6.000"
    f = tmp_path / "c.json"
    f.write_text(json.dumps(census))
    assert ac.read_timings_report(str(f), top=3) == text                             # a path works too
    assert ac.read_timings_report({"L1": {"layer": "L1"}}) == "no read_timings in this census"


# ───────────────────────── main(): the head key, and nothing else moves ─────────────────────────

def _fake_measure(k, assets=None):
    ac.set_read_asset("ga_alpha")
    ac.psql("SELECT 1 FROM chart_facts WHERE chart_id = 'c'")
    ac.set_read_asset("ga_beta")
    with ac.read_label("Vocab.identity"):
        ac.psql("SELECT 2")
    ac.set_read_asset(None)
    return dict(layer=k, layer_name="Test", scoring="x", n_assets=2, registered_ids=2, registry_has_writer=2, population_registry_total=2, population_active=2,
                never_exercised_with_writer=[], phantom_registered=[],
                assets=[dict(asset_id="ga_alpha", measurements={"Build.registered": dict(v="PASS", measured="m")}),
                        dict(asset_id="ga_beta", measurements={"Build.registered": dict(v="PASS", measured="m")})])


def _run_main(monkeypatch, tmp_path, clock_step, extra_argv=()):
    clock = FakeClock()
    monkeypatch.setattr(ac, "time", clock)
    FakePsql(monkeypatch, ac, [ok()], clock=clock, elapsed=clock_step)
    monkeypatch.setattr(ac, "measure", _fake_measure)
    monkeypatch.setattr(ac, "census_stamp", lambda: (ac.psql("SELECT current_database()"), dict(registry_revision=1, registry_fingerprint="f" * 64))[1])
    out = tmp_path / "census.json"
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", "L1", "--out", str(out), *extra_argv])
    rc = ac.main()
    return rc, json.loads(out.read_text())


def test_main_writes_read_timings_into_the_layer_head_and_changes_nothing_else(monkeypatch, tmp_path):
    rc1, c1 = _run_main(monkeypatch, tmp_path, 1.5)
    rc2, c2 = _run_main(monkeypatch, tmp_path, 7.0)                   # a very different clock: the only difference may be read_timings
    assert rc1 == rc2 == 0
    head1, head2 = dict(c1["L1"]), dict(c2["L1"])
    rt1, rt2 = head1.pop("read_timings"), head2.pop("read_timings")
    assert head1 == head2, "the head (verdicts, cells, stamp) must not depend on how long reads took"
    assert rt1 != rt2
    expect = dict(_fake_measure("L1"), registry_revision=1, registry_fingerprint="f" * 64)
    ac.drain_read_log()
    assert head1 == json.loads(json.dumps(expect)), "the head is exactly measure() + the stamp, plus read_timings"
    by = {p["asset"]: p for p in rt1["per_asset"]}
    assert set(by) == {"(run)", "ga_alpha", "ga_beta"}                # the stamp's read is (run), each asset's is its own
    assert by["ga_alpha"]["slowest"][0]["label"] == "SELECT ? FROM chart_facts WHERE chart_id = ?"
    assert by["ga_beta"]["slowest"][0]["label"] == "Vocab.identity"
    assert rt1["n_reads"] == 3 and rt1["max_seconds"] == 1.5


def test_main_report_flag_prints_the_slowest_reads(monkeypatch, tmp_path, capsys):
    _, _ = _run_main(monkeypatch, tmp_path, 2.0)
    capsys.readouterr()
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--read-timings-report", str(tmp_path / "census.json")])
    assert ac.main() == 0
    text = capsys.readouterr().out
    assert text.startswith("L1: 3 read(s)") and "ga_alpha" in text


def test_a_head_carrying_read_timings_rolls_up_exactly_like_one_without(monkeypatch):
    head = dict(layer="L1", assets=[])
    with_rt = dict(head, read_timings=ac.read_timings_summary([dict(asset="a", label="l", seconds=9.9, retries=0, outcome="ok")]))
    assert ac.build_rollup_output({"L1": with_rt}, declarations={}) == ac.build_rollup_output({"L1": head}, declarations={})
