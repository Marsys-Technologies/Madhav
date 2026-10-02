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
                 (dx.CHART_ID, json.dumps({"orb_max_deg": 5.0, "orb_ruling": "M-1 fallback no-box × 5.0° (unratified)"})))
    m = dx.read_manifest_orb(conn, "4.1")
    assert m["orb_max_deg"] == 5.0 and m["orb_ruling"].endswith("(unratified)") and m["manifest_status"] == "candidate"
    for key, req, comp, un in (("saturn:karaka", H, H, None), ("saturn:interval", H, H, None), ("sun:karaka", H, "[1998-01-01T00:00:00+00:00,2020-01-01T00:00:00+00:00)", "x")):
        conn.execute("INSERT INTO kala_gochara_coverage VALUES (%s,'4.1','body_target',%s,%s,%s,10,9,1,%s)", (dx.CHART_ID, key, req, comp, un))
    s = dx.read_coverage_summary(conn, "4.1")["partition_kinds"]["body_target"]
    assert (s["partitions"], s["full_horizon"], s["unsearched"], s["targets_requested"], s["targets_unresolved"]) == (3, 2, 1, 30, 3)
    assert s["first_key_segment"] == ["saturn", "sun"]
    assert dx.read_coverage_summary(conn, "4.1")["event_class_partitions"] == 0
