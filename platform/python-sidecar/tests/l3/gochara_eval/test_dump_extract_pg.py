"""dump_extract's SQL against a REAL PostgreSQL (disposable database created and dropped by the test).

Runs only when GOCHARA_EVAL_TEST_ADMIN_DSN points at a LOCAL server (127.0.0.1/localhost) — the test creates its own database,
never touches any other, and refuses a non-local host. The fake-cursor tests cannot catch SQL/driver errors (an earlier
`DATE %s` parameter failed under psycopg3 server-side binding and was invisible to them).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import uuid
from urllib.parse import urlparse

import pytest

from services.gochara_eval import dump_extract as dx

ADMIN = os.environ.get("GOCHARA_EVAL_TEST_ADMIN_DSN")
pytestmark = pytest.mark.skipif(not ADMIN, reason="GOCHARA_EVAL_TEST_ADMIN_DSN not set")

SCHEMA = """
CREATE TABLE kala_gochara_windows (chart_id uuid, generation text, event_class text, window_start date, window_end date,
  peak_date date, signed_intensity numeric NOT NULL, raw_intensity numeric NOT NULL, valence text, is_adverse boolean,
  resolution text, temporal_shape text);
CREATE TABLE kala_gochara_publication (chart_id uuid, generation text, status text, input_generation_vector jsonb);
CREATE TABLE chart_facts (fact_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid, ayanamsha_id text, fact_category text, fact_subject text,
  fact_key text, fact_value_num double precision);
CREATE TABLE chart_dashas (dasha_row_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid, ayanamsha_id text, system_id text, level_n int,
  verification_pass_status text);
CREATE TABLE kala_gochara_coverage (chart_id uuid, generation text, partition_kind text, partition_key text,
  requested_horizon tstzrange, completed_horizon tstzrange, targets_requested int, targets_resolved int,
  targets_unresolved int, unsearched_reason text);
"""
H = "[1998-01-01T00:00:00+00:00,2026-04-18T00:00:00+00:00)"


@pytest.fixture(scope="module")
def conn():
    import psycopg
    host = urlparse(ADMIN).hostname
    assert host in ("127.0.0.1", "localhost"), "refusing a non-local server"
    name = "ge_test_" + uuid.uuid4().hex[:10]
    admin = psycopg.connect(ADMIN, autocommit=True)
    admin.execute(f'CREATE DATABASE "{name}"')
    try:
        c = psycopg.connect(ADMIN.rsplit("/", 1)[0] + "/" + name, autocommit=True)
        c.execute(SCHEMA)
        yield c
        c.close()
    finally:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


def add(conn, gen, rows):
    for r in rows:
        conn.execute("INSERT INTO kala_gochara_windows VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (dx.CHART_ID, gen, *r))


def test_dump_rows_runs_the_real_sql_in_total_order_and_si_is_the_unsigned_magnitude(conn):
    D = dt.date
    add(conn, "4.1", [
        ("marriage", D(2010, 5, 1), D(2010, 6, 1), D(2010, 5, 10), -0.4, 0.4, "adverse", True, "day", "interval"),   # adverse: negative signed
        ("marriage", D(2010, 5, 1), D(2010, 5, 20), D(2010, 5, 3), 0.7, 0.7, "gain", False, "day", "interval"),
        ("bereavement", D(2012, 1, 1), D(2012, 1, 9), D(2012, 1, 4), -0.2, 0.2, "adverse", True, "era", "interval")])
    add(conn, "3.0", [("marriage", D(2000, 1, 1), D(2000, 2, 1), D(2000, 1, 9), 0.5, 0.5, "gain", False, "day", "interval")])
    rows = dx.dump_rows(conn, "4.1", horizon_check=True)
    assert [(r["event_class"], r["ws"], r["we"]) for r in rows] == [
        ("bereavement", "2012-01-01", "2012-01-09"), ("marriage", "2010-05-01", "2010-05-20"), ("marriage", "2010-05-01", "2010-06-01")]
    assert [r["si"] for r in rows] == [0.2, 0.7, 0.4]            # raw_intensity, never the negative signed value
    assert all(r["si"] >= 0 for r in rows) and rows[0]["adv"] is True and rows[0]["pk"] == "2012-01-04"
    assert dx.render("4.1", "2026-10-05", rows) == dx.render("4.1", "2026-10-05", dx.dump_rows(conn, "4.1", True))   # deterministic
    assert len(dx.dump_rows(conn, "3.0", horizon_check=False)) == 1                                                # other generation not mixed in


def test_sign_reconciliation_and_horizon_stop_on_real_data(conn):
    D = dt.date
    add(conn, "9.9", [("marriage", D(2010, 1, 1), D(2010, 2, 1), D(2010, 1, 9), 0.9, 0.5, "gain", False, "day", "interval")])
    with pytest.raises(RuntimeError, match=r"\|signed_intensity\| != raw_intensity"):
        dx.dump_rows(conn, "9.9", horizon_check=True)
    add(conn, "8.8", [("marriage", D(2030, 1, 1), D(2030, 2, 1), D(2030, 1, 9), 0.5, 0.5, "gain", False, "day", "interval")])
    with pytest.raises(RuntimeError, match="outside the scored horizon"):
        dx.dump_rows(conn, "8.8", horizon_check=True)


def test_manifest_orb_and_coverage_summary_read_back(conn):
    conn.execute("INSERT INTO kala_gochara_publication VALUES (%s,'4.1','candidate',%s)",
                 (dx.CHART_ID, json.dumps({"orb_max_deg": 5.0, "orb_ruling": "M-1 fallback no-box × 5.0° (unratified)",
                             "ephemeris": {"backend": "swieph", "swe_version": "2.10.03", "library_sha256": "ab" * 32, "platform": "Linux-x86_64",
                                           "files": {"sepl_18.se1": "cd" * 32}, "probe_digest": "ef" * 32}})))
    m = dx.read_manifest_orb(conn, "4.1")
    assert m["orb_max_deg"] == 5.0 and m["orb_ruling"].endswith("(unratified)") and m["manifest_status"] == "candidate"
    assert m["ephemeris_problems"] == [] and m["ephemeris"]["files"] == {"sepl_18.se1": "cd" * 32}
    for key, req, comp, un in (("saturn:karaka", H, H, None), ("saturn:interval", H, H, None), ("sun:karaka", H, "[1998-01-01T00:00:00+00:00,2020-01-01T00:00:00+00:00)", "x")):
        conn.execute("INSERT INTO kala_gochara_coverage VALUES (%s,'4.1','body_target',%s,%s,%s,10,9,1,%s)", (dx.CHART_ID, key, req, comp, un))
    s = dx.read_coverage_summary(conn, "4.1")["partition_kinds"]["body_target"]
    assert (s["partitions"], s["full_horizon"], s["unsearched"], s["targets_requested"], s["targets_unresolved"]) == (3, 2, 1, 30, 3)
    assert s["first_key_segment"] == ["saturn", "sun"]
    assert dx.read_coverage_summary(conn, "4.1")["event_class_partitions"] == 0


def test_av_donor_identity_runs_the_real_sql_counts_and_digests_per_ayanamsha(conn):
    """Zero donor rows is a real answer (count 0, digest NULL) for every ayanamsha that has any fact; once rows exist the digest is a function of their content."""
    conn.execute("INSERT INTO chart_facts(chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_num) VALUES "
                 "(%s,'lahiri_chitrapaksha','graha_position','SUN','longitude_sidereal',291.9),(%s,'raman','graha_position','SUN','longitude_sidereal',291.2)",
                 (dx.CHART_ID, dx.CHART_ID))
    absent = dx.read_av_donor_identity(conn)
    assert absent["per_ayanamsha"] == {"lahiri_chitrapaksha": {"row_count": 0, "digest": None}, "raman": {"row_count": 0, "digest": None}}
    for subj, v in (("SUN-CONTRIBUTOR_MOON-SIGN_1", 1.0), ("SUN-CONTRIBUTOR_MAR-SIGN_1", 0.0)):
        conn.execute("INSERT INTO chart_facts(chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_num) "
                     "VALUES (%s,'lahiri_chitrapaksha','ashtakavarga_bindu_contributor',%s,'bindus',%s)", (dx.CHART_ID, subj, v))
    first = dx.read_av_donor_identity(conn)["per_ayanamsha"]
    assert first["lahiri_chitrapaksha"]["row_count"] == 2 and len(first["lahiri_chitrapaksha"]["digest"]) == 64
    assert first["raman"] == {"row_count": 0, "digest": None}
    conn.execute("UPDATE chart_facts SET fact_value_num = 1.0 WHERE fact_subject = 'SUN-CONTRIBUTOR_MAR-SIGN_1'")
    assert dx.read_av_donor_identity(conn)["per_ayanamsha"]["lahiri_chitrapaksha"]["digest"] != first["lahiri_chitrapaksha"]["digest"]


def test_dasha_tiers_runs_the_real_sql_per_system_level_and_tier(conn):
    """Only the eight DR-14 systems, only the candidate's ayanamsha, grouped by (system, level, tier) with counts (vimshottari_kp and other ayanamshas excluded)."""
    rows = ([("vimshottari", 1, "two_pass_verified")] * 3 + [("mudda", 1, "classical_match")] * 2 + [("mudda", 2, "single")] * 5 + [("vimshottari_kp", 2, "single")])
    for sysid, lv, tier in rows:
        conn.execute("INSERT INTO chart_dashas(chart_id, ayanamsha_id, system_id, level_n, verification_pass_status) VALUES (%s,'lahiri_chitrapaksha',%s,%s,%s)",
                     (dx.CHART_ID, sysid, lv, tier))
    conn.execute("INSERT INTO chart_dashas(chart_id, ayanamsha_id, system_id, level_n, verification_pass_status) VALUES (%s,'raman','vimshottari',1,'single')", (dx.CHART_ID,))
    assert dx.read_dasha_tiers(conn) == [{"system": "mudda", "level": 1, "tier": "classical_match", "count": 2},
                                         {"system": "mudda", "level": 2, "tier": "single", "count": 5},
                                         {"system": "vimshottari", "level": 1, "tier": "two_pass_verified", "count": 3}]
