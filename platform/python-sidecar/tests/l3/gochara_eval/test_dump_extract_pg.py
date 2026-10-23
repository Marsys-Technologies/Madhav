"""dump_extract's SQL against a REAL PostgreSQL (disposable database created and dropped by the test).

Runs only when GOCHARA_EVAL_TEST_ADMIN_DSN points at a LOCAL server (loopback or Unix socket) — the test creates its own database,
never touches any other, and refuses a non-local host. The fake-cursor tests cannot catch SQL/driver errors (an earlier
`DATE %s` parameter failed under psycopg3 server-side binding and was invisible to them).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import uuid

import pytest
from psycopg.conninfo import make_conninfo

from services.gochara_eval import dump_extract as dx

from . import _disposable_guard as guard

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
DASHA_BUILD = "00000000-0000-4000-8000-000000000901"

ADMIN = os.environ.get("GOCHARA_EVAL_TEST_ADMIN_DSN")
pytestmark = pytest.mark.skipif(not ADMIN, reason="GOCHARA_EVAL_TEST_ADMIN_DSN not set")

SCHEMA = """
CREATE TABLE kala_gochara_windows (chart_id uuid, generation text, event_class text, window_start date, window_end date,
  peak_date date, signed_intensity numeric NOT NULL, raw_intensity numeric NOT NULL, valence text, is_adverse boolean,
  resolution text, temporal_shape text);
-- the governed eval-window columns the extractor reads, with the types migration 1156 / 1240 declare (constraints omitted: this is the read path)
CREATE TABLE ka_gochara_eval_window (window_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid NOT NULL, event_class text NOT NULL,
  generation text NOT NULL, path_id text NOT NULL, rule_version text NOT NULL DEFAULT '1.0.0', interval tstzrange NOT NULL, peak_instant timestamptz,
  score real, evidence_for real, evidence_against real, outcome_valence_for_native text NOT NULL, severity real, qualification jsonb);
CREATE TABLE kala_gochara_publication (chart_id uuid, generation text, status text, input_generation_vector jsonb);
CREATE TABLE chart_facts (fact_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid, ayanamsha_id text, fact_category text, fact_subject text,
  fact_key text, fact_value_num double precision);
CREATE TABLE chart_dashas (dasha_row_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid, ayanamsha_id text, system_id text, level_n int,
  verification_pass_status text, build_id uuid);
CREATE TABLE kala_gochara_coverage (chart_id uuid, generation text, partition_kind text, partition_key text,
  requested_horizon tstzrange, completed_horizon tstzrange, targets_requested int, targets_resolved int,
  targets_unresolved int, unsearched_reason text);
"""
H = "[1998-01-01T00:00:00+00:00,2026-04-18T00:00:00+00:00)"


@pytest.fixture(scope="module")
def conn():
    import psycopg
    guard.assert_disposable_dsn(ADMIN)                             # steward eb38: libpq's own parse, one explicit loopback host, no env overrides
    name = "ge_test_" + uuid.uuid4().hex[:10]
    admin = psycopg.connect(ADMIN, autocommit=True)
    guard.assert_connected_to(admin)
    admin.execute(f'CREATE DATABASE "{name}"')
    try:
        c = psycopg.connect(make_conninfo(ADMIN, dbname=name), autocommit=True)
        guard.assert_connected_to(c, expected_db=name)
        c.execute(SCHEMA)
        yield c
        c.close()
    finally:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


_OPEN: list = []


def reader(conn):
    """A reader connection exactly as the CLI gets one: psycopg's DEFAULT (autocommit=False), configured ONCE by `_connect`'s own function (Codex R11-5 —
    the autocommit fixture connection hid the ProgrammingError that setting `read_only` inside an open transaction raises)."""
    import psycopg
    c = psycopg.connect(conn.info.dsn)
    assert c.autocommit is False
    dx.configure_read_only_snapshot(c)
    _OPEN.append(c)
    return c


@pytest.fixture(autouse=True)
def _close_readers():
    yield
    while _OPEN:
        _OPEN.pop().close()


def add(conn, gen, rows):
    for r in rows:
        conn.execute("INSERT INTO kala_gochara_windows VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (CHART_ID, gen, *r))


def test_dump_rows_runs_the_real_sql_in_total_order_and_si_is_the_unsigned_magnitude(conn):
    D = dt.date
    add(conn, "4.1", [
        ("marriage", D(2010, 5, 1), D(2010, 6, 1), D(2010, 5, 10), -0.4, 0.4, "adverse", True, "day", "interval"),   # adverse: negative signed
        ("marriage", D(2010, 5, 1), D(2010, 5, 20), D(2010, 5, 3), 0.7, 0.7, "gain", False, "day", "interval"),
        ("bereavement", D(2012, 1, 1), D(2012, 1, 9), D(2012, 1, 4), -0.2, 0.2, "adverse", True, "era", "interval")])
    add(conn, "3.0", [("marriage", D(2000, 1, 1), D(2000, 2, 1), D(2000, 1, 9), 0.5, 0.5, "gain", False, "day", "interval")])
    rows = dx.dump_rows(reader(conn), "4.1", horizon_check=True, chart_id=CHART_ID)
    assert [(r["event_class"], r["ws"], r["we"]) for r in rows] == [
        ("bereavement", "2012-01-01", "2012-01-09"), ("marriage", "2010-05-01", "2010-05-20"), ("marriage", "2010-05-01", "2010-06-01")]
    assert [r["si"] for r in rows] == [0.2, 0.7, 0.4]            # raw_intensity, never the negative signed value
    assert all(r["si"] >= 0 for r in rows) and rows[0]["adv"] is True and rows[0]["pk"] == "2012-01-04"
    assert dx.render("4.1", "2026-10-05", rows, chart_id=CHART_ID) == dx.render("4.1", "2026-10-05", dx.dump_rows(reader(conn), "4.1", True, chart_id=CHART_ID), chart_id=CHART_ID)   # deterministic
    assert len(dx.dump_rows(reader(conn), "3.0", horizon_check=False, chart_id=CHART_ID)) == 1                                                # other generation not mixed in


def test_sign_reconciliation_and_horizon_stop_on_real_data(conn):
    D = dt.date
    add(conn, "9.9", [("marriage", D(2010, 1, 1), D(2010, 2, 1), D(2010, 1, 9), 0.9, 0.5, "gain", False, "day", "interval")])
    with pytest.raises(RuntimeError, match=r"\|signed_intensity\| != raw_intensity"):
        dx.dump_rows(reader(conn), "9.9", horizon_check=True, chart_id=CHART_ID)
    add(conn, "8.8", [("marriage", D(2030, 1, 1), D(2030, 2, 1), D(2030, 1, 9), 0.5, 0.5, "gain", False, "day", "interval")])
    with pytest.raises(RuntimeError, match="outside the scored horizon"):
        dx.dump_rows(reader(conn), "8.8", horizon_check=True, chart_id=CHART_ID)


def test_manifest_orb_and_coverage_summary_read_back(conn):
    conn.execute("INSERT INTO kala_gochara_publication VALUES (%s,'4.1','candidate',%s)",
                 (CHART_ID, json.dumps({"orb_max_deg": 5.0, "orb_ruling": "M-1 fallback no-box × 5.0° (unratified)",
                             "ephemeris": {"backend": "swieph", "swe_version": "2.10.03", "library_sha256": "ab" * 32, "platform": "Linux-x86_64",
                                           "files": {"sepl_18.se1": "cd" * 32}, "probe_digest": "ef" * 32}})))
    m = dx.read_manifest_orb(reader(conn), "4.1", chart_id=CHART_ID)
    assert m["orb_max_deg"] == 5.0 and m["orb_ruling"].endswith("(unratified)") and m["manifest_status"] == "candidate"
    assert m["ephemeris_problems"] == [] and m["ephemeris"]["files"] == {"sepl_18.se1": "cd" * 32}
    for key, req, comp, un in (("saturn:karaka", H, H, None), ("saturn:interval", H, H, None), ("sun:karaka", H, "[1998-01-01T00:00:00+00:00,2020-01-01T00:00:00+00:00)", "x")):
        conn.execute("INSERT INTO kala_gochara_coverage VALUES (%s,'4.1','body_target',%s,%s,%s,10,9,1,%s)", (CHART_ID, key, req, comp, un))
    s = dx.read_coverage_summary(reader(conn), "4.1", chart_id=CHART_ID)["partition_kinds"]["body_target"]
    assert (s["partitions"], s["full_horizon"], s["unsearched"], s["targets_requested"], s["targets_unresolved"]) == (3, 2, 1, 30, 3)
    assert s["first_key_segment"] == ["saturn", "sun"]
    assert dx.read_coverage_summary(reader(conn), "4.1", chart_id=CHART_ID)["event_class_partitions"] == 0


def test_av_donor_identity_runs_the_real_sql_counts_and_digests_per_ayanamsha(conn):
    """Zero donor rows is a real answer (count 0, digest NULL) for every ayanamsha that has any fact; once rows exist the digest is a function of their content."""
    conn.execute("INSERT INTO chart_facts(chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_num) VALUES "
                 "(%s,'lahiri_chitrapaksha','graha_position','SUN','longitude_sidereal',291.9),(%s,'raman','graha_position','SUN','longitude_sidereal',291.2)",
                 (CHART_ID, CHART_ID))
    absent = dx.read_av_donor_identity(reader(conn), chart_id=CHART_ID)
    assert absent["per_ayanamsha"] == {"lahiri_chitrapaksha": {"row_count": 0, "digest": None}, "raman": {"row_count": 0, "digest": None}}
    for subj, v in (("SUN-CONTRIBUTOR_MOON-SIGN_1", 1.0), ("SUN-CONTRIBUTOR_MAR-SIGN_1", 0.0)):
        conn.execute("INSERT INTO chart_facts(chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_num) "
                     "VALUES (%s,'lahiri_chitrapaksha','ashtakavarga_bindu_contributor',%s,'bindus',%s)", (CHART_ID, subj, v))
    first = dx.read_av_donor_identity(reader(conn), chart_id=CHART_ID)["per_ayanamsha"]
    assert first["lahiri_chitrapaksha"]["row_count"] == 2 and len(first["lahiri_chitrapaksha"]["digest"]) == 64
    assert first["raman"] == {"row_count": 0, "digest": None}
    conn.execute("UPDATE chart_facts SET fact_value_num = 1.0 WHERE fact_subject = 'SUN-CONTRIBUTOR_MAR-SIGN_1'")
    assert dx.read_av_donor_identity(reader(conn), chart_id=CHART_ID)["per_ayanamsha"]["lahiri_chitrapaksha"]["digest"] != first["lahiri_chitrapaksha"]["digest"]


def test_dasha_tiers_runs_the_real_sql_per_system_level_and_tier(conn, tmp_path, monkeypatch):
    from tests.l3._dasha_settlement import settle_fixture_chart
    settle_fixture_chart(tmp_path, monkeypatch, chart_id=CHART_ID, build_id=DASHA_BUILD)
    """Only the eight DR-14 systems, only the candidate's ayanamsha, grouped by (system, level, tier) with counts (vimshottari_kp and other ayanamshas excluded)."""
    rows = ([("vimshottari", 1, "two_pass_verified")] * 3 + [("mudda", 1, "classical_match")] * 2 + [("mudda", 2, "single")] * 5 + [("vimshottari_kp", 2, "single"), ("mudda", 5, "unknown")])
    for sysid, lv, tier in rows:
        conn.execute("INSERT INTO chart_dashas(chart_id, ayanamsha_id, system_id, level_n, verification_pass_status) VALUES (%s,'lahiri_chitrapaksha',%s,%s,%s)",
                     (CHART_ID, sysid, lv, tier))
    conn.execute("INSERT INTO chart_dashas(chart_id, ayanamsha_id, system_id, level_n, verification_pass_status) VALUES (%s,'raman','vimshottari',1,'single')", (CHART_ID,))
    conn.execute("UPDATE chart_dashas SET build_id=%s", (DASHA_BUILD,))
    assert dx.read_dasha_tiers(reader(conn), chart_id=CHART_ID) == [{"system": "mudda", "level": 1, "tier": "classical_match", "count": 2},
                                         {"system": "mudda", "level": 2, "tier": "single", "count": 5},
                                         {"system": "mudda", "level": 5, "tier": "unknown", "count": 1},
                                         {"system": "vimshottari", "level": 1, "tier": "two_pass_verified", "count": 3}]


@pytest.fixture()
def fresh():
    """A second, function-scoped database (the same schema) so the CLI tests do not depend on rows other tests inserted."""
    import psycopg
    guard.assert_disposable_dsn(ADMIN)
    name = "ge_cli_" + uuid.uuid4().hex[:10]
    admin = psycopg.connect(ADMIN, autocommit=True)
    guard.assert_connected_to(admin)
    admin.execute(f'CREATE DATABASE "{name}"')
    try:
        dsn = make_conninfo(ADMIN, dbname=name)
        c = psycopg.connect(dsn, autocommit=True)
        guard.assert_connected_to(c, expected_db=name)
        c.execute(SCHEMA)
        yield c, dsn
        c.close()
    finally:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


def test_the_cli_read_backs_and_the_baseline_extraction_run_on_psycopgs_default_connection(fresh, monkeypatch, tmp_path, capsys):
    """Codex R11-5: the REAL `_connect` (psycopg.connect(dsn), autocommit=False) through main(): every read-back and the extraction (here the baseline
    re-dump) complete in one read-only transaction — they raised ProgrammingError before the transaction characteristics were configured once up front."""
    from tests.l3._dasha_settlement import settle_fixture_chart
    settle_fixture_chart(tmp_path, monkeypatch, chart_id=CHART_ID, build_id=DASHA_BUILD)
    c, dsn = fresh
    D = dt.date
    add(c, "3.0", [("marriage", D(2000, 1, 1), D(2000, 2, 1), D(2000, 1, 9), 0.5, 0.5, "gain", False, "day", "interval")])
    c.execute("INSERT INTO kala_gochara_publication VALUES (%s,'4.1','candidate',%s)", (CHART_ID, json.dumps({"orb_max_deg": 5.0, "orb_ruling": "x", "ephemeris": None})))
    c.execute("INSERT INTO chart_facts(chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_num) VALUES (%s,'lahiri_chitrapaksha','graha_position','SUN','longitude_sidereal',291.9)", (CHART_ID,))
    c.execute("INSERT INTO chart_dashas(chart_id, ayanamsha_id, system_id, level_n, verification_pass_status) VALUES (%s,'lahiri_chitrapaksha','mudda',1,'classical_match')", (CHART_ID,))
    c.execute("UPDATE chart_dashas SET build_id=%s", (DASHA_BUILD,))
    monkeypatch.setenv(dx.DSN_ENV, dsn)
    for flag in ("--read-manifest-orb", "--read-coverage-summary", "--read-av-donor-rows", "--read-dasha-tiers"):
        assert dx.main(["--chart-id", CHART_ID] + ["--generation", "4.1", flag]) == 0, flag
        capsys.readouterr()
    # ALL read-backs in ONE invocation = four helpers in ONE transaction (the second helper raised ProgrammingError when each one assigned `read_only`)
    assert dx.main(["--chart-id", CHART_ID] + ["--generation", "4.1", "--read-manifest-orb", "--read-coverage-summary", "--read-av-donor-rows", "--read-dasha-tiers"]) == 0
    assert len(capsys.readouterr().out.strip().splitlines()) == 4
    out = tmp_path / "o.json"
    rc = dx.main(["--chart-id", CHART_ID] + ["--generation", "3.0", "--requalify-3-0", "0" * 64, "--pinned-at", "2026-10-05", "--out", str(out)])
    assert out.exists() and json.loads(out.read_bytes())["row_count"] == 1 and rc in (0, 1)
    assert "rows=1" in capsys.readouterr().out


@pytest.mark.parametrize('damage,code', [
    ('missing_receipt', 'settlement_missing'),
    ('malformed_receipt', 'settlement_malformed'),
    ('other_chart', 'chart_not_settled'),
    ('wrong_build', 'settled_build_absent'),
    ('null_build', 'dasha_build_null'),
    ('mixed_build', 'settled_build_ambiguous'),
])
def test_dasha_tier_readback_refuses_ungoverned_population(fresh, tmp_path, monkeypatch, damage, code):
    from services.gochara_kernel.dasha_read import DashaBuildRefused
    from tests.l3._dasha_settlement import settle_fixture_chart

    conn, _ = fresh
    receipt = settle_fixture_chart(tmp_path, monkeypatch, chart_id=CHART_ID, build_id=DASHA_BUILD)
    conn.execute("INSERT INTO chart_dashas(chart_id,ayanamsha_id,system_id,level_n,verification_pass_status,build_id) "
                 "VALUES (%s,'lahiri_chitrapaksha','mudda',2,'single',%s)", (CHART_ID, DASHA_BUILD))
    if damage == 'missing_receipt': receipt.unlink()
    elif damage == 'malformed_receipt': receipt.write_text('{}')
    elif damage == 'wrong_build': conn.execute("UPDATE chart_dashas SET build_id=gen_random_uuid()")
    elif damage == 'null_build': conn.execute("UPDATE chart_dashas SET build_id=NULL")
    elif damage == 'mixed_build':
        conn.execute("INSERT INTO chart_dashas SELECT gen_random_uuid(),chart_id,ayanamsha_id,system_id,5,'unknown',gen_random_uuid() FROM chart_dashas")
    requested_chart = '00000000-0000-4000-8000-000000000902' if damage == 'other_chart' else CHART_ID
    with pytest.raises(DashaBuildRefused, match=code):
        dx.read_dasha_tiers(reader(conn), chart_id=requested_chart)


def test_dump_rows_isolates_the_requested_chart_even_with_same_generation_and_dates(fresh):
    conn, _ = fresh
    other_chart = "11111111-1111-4111-8111-111111111111"
    D = dt.date
    row = ("marriage", D(2010, 5, 1), D(2010, 6, 1), D(2010, 5, 10), 0.7, 0.7, "gain", False, "day", "interval")
    add(conn, "4.1", [row])
    conn.execute("INSERT INTO kala_gochara_windows VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                 (other_chart, "4.1", *row))
    # Check both directions and an absent chart: chart_id parameter binding
    # alone cannot prove isolation if SQL broadens the predicate with OR TRUE.
    for chart in (CHART_ID, other_chart):
        result = dx.dump_rows(reader(conn), "4.1", True, chart_id=chart)
        assert len(result) == 1 and result[0]["si"] == 0.7
    assert dx.dump_rows(reader(conn), "4.1", True,
                        chart_id="22222222-2222-4222-8222-222222222222") == []


# ── J-5q: the governed ('5.0') extract and the per-(class, year) coverage cells, on a REAL PostgreSQL ────────────────────────────────────

def gov(conn, gen, rows, chart=CHART_ID):
    """rows: (event_class, path, lower, upper, peak, evidence_for, valence, qualification-or-None) with IST-aware instants."""
    for cls, path, lo, hi, pk, ev, val, q in rows:
        conn.execute("INSERT INTO ka_gochara_eval_window(chart_id, event_class, generation, path_id, interval, peak_instant, evidence_for, "
                     "outcome_valence_for_native, qualification) VALUES (%s,%s,%s,%s,tstzrange(%s,%s,'[)'),%s,%s,%s,%s)",
                     (chart, cls, gen, path, lo, hi, pk, ev, val, None if q is None else json.dumps(q)))


IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def ist(y, m, d, h=0, mi=0):
    return dt.datetime(y, m, d, h, mi, tzinfo=IST)


def test_governed_dump_maps_the_stored_columns_to_the_adapter_row_on_real_sql(fresh):
    """FIXTURE (not a measurement). The day convention is the only thing a fake cursor cannot check: a half-open interval whose upper bound is exactly
    00:00 IST ends the DAY BEFORE (the same convention as density_extract._day_span); an upper bound one minute later reaches the next day."""
    c, _ = fresh
    q_null = {"policy": "window_qualification/1", "unqualified_reason": "dynamic_objective_solver_guarantee_not_available",
              "unresolved": {}, "affected_channels": [], "members": 1, "qualified_members": 0}
    q_ok = {**q_null, "unqualified_reason": None, "qualified_members": 1}
    gov(c, "5.0", [
        ("marriage", "P3", ist(2010, 5, 1), ist(2010, 5, 20), ist(2010, 5, 7, 13), 0.75, "favourable", q_ok),             # upper = 00:00 IST -> we = 05-19
        ("marriage", "P4", ist(2010, 5, 1), ist(2010, 5, 20, 0, 1), None, None, "unqualified", q_null),                    # one minute later -> we = 05-20
        ("bereavement", "P1", ist(2012, 1, 1), ist(2012, 1, 9), None, None, "unqualified", None)])                         # null without a stored reason
    gov(c, "3.0", [("marriage", "P3", ist(2000, 1, 1), ist(2000, 2, 1), None, 0.5, "mixed", None)])                          # another generation: not mixed in
    gov(c, "5.0", [("marriage", "P3", ist(2010, 5, 1), ist(2010, 5, 3), None, 0.1, "mixed", None)], chart="11111111-1111-4111-8111-111111111111")
    rows, extra = dx.dump_governed(reader(c), "5.0", chart_id=CHART_ID)
    assert [(r["event_class"], r["path_id"], r["ws"], r["we"], r["pk"], r["si"], r["outcome_valence_for_native"], r["null_reason"]) for r in rows] == [
        ("bereavement", "P1", "2012-01-01", "2012-01-08", None, None, "unqualified", None),
        ("marriage", "P3", "2010-05-01", "2010-05-19", "2010-05-07", 0.75, "favourable", None),
        ("marriage", "P4", "2010-05-01", "2010-05-20", None, None, "unqualified", "dynamic_objective_solver_guarantee_not_available")]
    assert extra["null_census"] == {"si_null": 2, "pk_null": 2, "si_null_without_reason": 1,
                                    "si_null_reasons": {"dynamic_objective_solver_guarantee_not_available": 1},
                                    "valence": {"favourable": 1, "unqualified": 2}, "paths": {"P1": 1, "P3": 1, "P4": 1}}
    assert dx.render("5.0", "2026-10-21", rows, chart_id=CHART_ID, extra=extra) == dx.render(
        "5.0", "2026-10-21", dx.dump_rows(reader(c), "5.0", True, chart_id=CHART_ID), chart_id=CHART_ID, extra=extra)         # deterministic


def test_governed_dump_keeps_a_window_that_overlaps_the_scored_horizon_whole_and_counts_the_rest(fresh):
    c, _ = fresh
    gov(c, "5.0", [
        ("marriage", "P3", ist(1990, 1, 1), ist(1997, 12, 31, 23, 59), None, 0.1, "mixed", None),       # ends before 1998-01-01 IST: excluded
        ("marriage", "P3", ist(1997, 12, 31), ist(1998, 1, 2), ist(1998, 1, 1), 0.2, "mixed", None),     # touches 1998-01-01: kept
        ("marriage", "P3", ist(2026, 4, 17), ist(2090, 1, 1), ist(2026, 4, 17, 6), 0.3, "mixed", None),  # starts on the last scored day, ends in 2090: kept whole
        ("marriage", "P3", ist(2026, 4, 18), ist(2026, 4, 19), None, 0.4, "mixed", None),                # starts after the scored horizon: excluded
        ("marriage", "P3", ist(2060, 1, 1), ist(2060, 2, 1), None, 0.5, "mixed", None)])                 # century tail: excluded
    rows, extra = dx.dump_governed(reader(c), "5.0", chart_id=CHART_ID)
    assert [r["si"] for r in rows] == [pytest.approx(0.2), pytest.approx(0.3)] and rows[1]["we"] == "2089-12-31"
    assert extra["windows_stored"] == 5 and extra["windows_outside_scored_horizon_excluded"] == 3


def test_governed_dump_isolates_the_requested_chart(fresh):
    c, _ = fresh
    other = "11111111-1111-4111-8111-111111111111"
    gov(c, "5.0", [("marriage", "P3", ist(2010, 5, 1), ist(2010, 5, 3), None, 0.7, "mixed", None)])
    gov(c, "5.0", [("marriage", "P3", ist(2010, 5, 1), ist(2010, 5, 3), None, 0.2, "mixed", None)], chart=other)
    for chart, want in ((CHART_ID, 0.7), (other, 0.2)):
        got = dx.dump_governed(reader(c), "5.0", chart_id=chart)[0]
        assert len(got) == 1 and got[0]["si"] == pytest.approx(want)
    assert dx.dump_governed(reader(c), "5.0", chart_id="22222222-2222-4222-8222-222222222222")[0] == []


def test_governed_manifest_readback_on_real_jsonb(fresh):
    c, _ = fresh
    eph = {"backend": "swieph", "swe_version": "2.10.03", "library_sha256": "ab" * 32, "platform": "Linux-x86_64",
           "files": {"sepl_18.se1": "cd" * 32}, "probe_digest": "ef" * 32}
    vec = {"result_policy": "window_qualification/1", "ephemeris": eph, "orb_policy": {"admission_digest": "01" * 32, "activity": {"x": 1}},
           "registry": {"digest": "02" * 32, "census": []}, "implementation": {"geometry": "03" * 32, "evaluation": "04" * 32}}
    c.execute("INSERT INTO kala_gochara_publication VALUES (%s,'5.0','candidate',%s)", (CHART_ID, json.dumps(vec)))
    m = dx.read_governed_manifest(reader(c), "5.0", chart_id=CHART_ID)
    assert (m["manifest_status"], m["result_policy"], m["registry_digest"]) == ("candidate", "window_qualification/1", "02" * 32)
    assert m["implementation"] == vec["implementation"] and m["orb_policy"] == vec["orb_policy"] and m["ephemeris_problems"] == []
    c.execute("UPDATE kala_gochara_publication SET input_generation_vector = jsonb_set(input_generation_vector, '{result_policy}', '\"made_up/9\"')")
    assert any("result_policy" in p for p in dx.read_governed_manifest(reader(c), "5.0", chart_id=CHART_ID)["ephemeris_problems"])


def test_coverage_cells_read_the_event_class_ledger_on_real_sql(fresh):
    from services.gochara_eval import coverage_cells as cc
    c, _ = fresh
    full = "[1998-01-01T00:00:00+05:30,2084-12-31T00:00:00+05:30)"
    c.execute("INSERT INTO kala_gochara_coverage VALUES (%s,'5.0','event_class','marriage',%s,%s,1,1,0,NULL)", (CHART_ID, full, full))
    c.execute("INSERT INTO kala_gochara_coverage VALUES (%s,'5.0','event_class','bereavement',%s,%s,1,1,0,'Moon-agent edges are on-demand (AM-4)')",
              (CHART_ID, full, full))
    c.execute("INSERT INTO kala_gochara_coverage VALUES (%s,'5.0','body_target','saturn:karaka',%s,%s,1,1,0,NULL)", (CHART_ID, full, full))
    c.execute("INSERT INTO kala_gochara_coverage VALUES (%s,'5.1','event_class','childbirth',%s,%s,1,1,0,NULL)", (CHART_ID, full, full))
    doc = cc.read_cells(reader(c), chart_id=CHART_ID, generation="5.0")
    by = {(x["event_class"], x["year"]): x for x in doc["cells"]}
    assert len(doc["cells"]) == 2 * 29 and "marriage" not in doc["classes_without_partition"] and "childbirth" in doc["classes_without_partition"]
    assert by[("marriage", 1998)]["computed"] is True and by[("marriage", 2026)]["computed"] is True
    assert by[("bereavement", 2010)]["computed"] is False and by[("bereavement", 2010)]["horizon_covers_year"] is True      # strict: unsearched part
    assert cc.read_cells(reader(c), chart_id=CHART_ID, generation="5.0", unsearched_policy="horizon_only")["cells"][0]["computed"] is True
