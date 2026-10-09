"""
ONE_AYANAMSHA P2-1: migrations 1344 (charts.build_ayanamshas) and 1345-1348 (chart-aware integrity_check_sql for
bo_pratijna, ga_vargas, ph_rectification, ga_nakshatra).

Two tiers:
  * STATIC (always runs, no psycopg, no database): md5/length of the OLD live texts (kept verbatim under
    tests/fixtures/ayanamsha_integrity_old/) and of the NEW texts embedded in the migrations, guard shape, one UPDATE per file,
    lock_timeout first, no BEGIN/COMMIT, headers carry the trigger fact and the Phase 4 timing.
  * LIVE (needs psycopg + PostgreSQL server binaries): applies the REAL on-disk migrations to a DISPOSABLE cluster (initdb in a temp
    dir, own port, trust auth, removed at session end). Skipped, loudly, when psycopg or initdb is absent. For every check the OLD text
    and the NEW text are run on the SAME fixture and compared:
      (a) NULL build_ayanamshas + full five-ayanamsha data -> NEW == OLD (green), and with one cell missing -> both red;
      (b) ['lahiri_chitrapaksha'] + Lahiri-only data -> NEW green where OLD is red;
      (c) a one-ayanamsha chart missing its Lahiri rows -> NEW red;
      (d) a mixed database (a five-chart + a one-chart) -> green only if both are complete;
      (e) the CHECK constraint rejects invalid values, accepts NULL and valid subsets.
    Also: migration idempotency, foreign-text NO-OP with NOTICE, silent no-op caught by the post-check, and the staling trigger (the
    REAL function/trigger text extracted from migration 596) fires on integrity_check_sql: it stales the asset's freshness receipts
    on every chart and touches no other asset.
It does NOT prove production state (read from production structure after the apply; Trap 103).
"""
from __future__ import annotations

import glob
import hashlib
import os
import re
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_MIG = _REPO / "platform" / "migrations"
_OLD_DIR = Path(__file__).resolve().parent / "fixtures" / "ayanamsha_integrity_old"
_M596 = _REPO / "platform" / "supabase" / "migrations" / "596_nirmana_provenance_receipts.sql"

FIVE = ["lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"]
CANON = "482012f1-710e-4a25-994a-93821f5871aa"
FIVE_CHART = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
ONE_CHART = "cb73cd3d-0000-4000-8000-0000000000c1"

SPECS = {
    "bo_pratijna": dict(num=1345, file="1345_bo_pratijna_integrity_chart_aware.sql",
                        old="145bac545d0808c46d6d929f9dc58153", old_len=1586,
                        new="55b0f65453ca8a5d9f7fdf56c15cc7ec", new_len=1966),
    "ga_vargas": dict(num=1346, file="1346_ga_vargas_integrity_chart_aware.sql",
                      old="d2f897535c8c6237f464c81f11624701", old_len=5804,
                      new="51e04fbaf5b60e4b2f89d9463aaac93d", new_len=6302),
    "ph_rectification": dict(num=1347, file="1347_ph_rectification_integrity_chart_aware.sql",
                             old="08d0d48159cdd942376277a37d4f69b6", old_len=1692,
                             new="fc036a2d3e9e75a6f1a5ce6ebfb4c494", new_len=2498),
    "ga_nakshatra": dict(num=1348, file="1348_ga_nakshatra_integrity_chart_aware.sql",
                         old="c2612c48b7d192977a1331db0ea2f7e7", old_len=4376,
                         new="45561c60ecb90e95450aba776337f47a", new_len=4898),
}
M1344 = _MIG / "1344_charts_build_ayanamshas_column.sql"


def _md5(t: str) -> str:
    return hashlib.md5(t.encode()).hexdigest()


def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("--"))


def _old(asset: str) -> str:
    return (_OLD_DIR / f"{asset}.sql").read_text()


def _new(asset: str) -> str:
    return re.search(r"\$chk\$(.*?)\$chk\$", (_MIG / SPECS[asset]["file"]).read_text(), re.S).group(1)


# -- STATIC tier --------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("asset", sorted(SPECS))
def test_static_old_and_new_text_hash_to_the_named_md5s(asset):
    s = SPECS[asset]
    assert _md5(_old(asset)) == s["old"] and len(_old(asset)) == s["old_len"]
    assert _md5(_new(asset)) == s["new"] and len(_new(asset)) == s["new_len"]


@pytest.mark.parametrize("asset", sorted(SPECS))
def test_static_guard_shape_one_update_lock_timeout_first_no_txn_control(asset):
    s = SPECS[asset]
    text = (_MIG / s["file"]).read_text()
    code = _code(_MIG / s["file"])
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert len(re.findall(r"^UPDATE\s+asset_registry\b", code, re.M)) == 1
    assert f"AND md5(integrity_check_sql) = '{s['old']}';" in code
    assert f"WHERE asset_id = '{asset}'" in code
    assert re.findall(r"\bSET\s+([a-z_]+)\s*=", code.replace("SET LOCAL lock_timeout =", ""), re.I) == ["integrity_check_sql"]
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code)
    assert not re.search(r"\bCREATE\b", code, re.I)
    # header facts the apply procedure depends on
    assert "nirmana_registry_receipt_invalidation" in text and "STALES" in text
    assert "PHASE 4" in text and "1c826d5a" in text and "cb73cd3d" in text
    assert "update did not take" in text and "NO-OP" in text and "RAISE EXCEPTION" in text


@pytest.mark.parametrize("asset", sorted(SPECS))
def test_static_new_text_takes_scope_from_charts_not_chart_facts_and_keeps_one_default_literal(asset):
    new = _new(asset)
    assert "build_ayanamshas" in new and "charts ch ON ch.id" in new
    assert "COALESCE(ch.build_ayanamshas" in new
    # exactly one literal of the five per text: the COALESCE default (NULL meaning); no second global constant
    n_lists = len(re.findall(r"'lahiri_chitrapaksha'", new))
    assert n_lists == 1, n_lists
    assert "5/5" not in re.sub(r"--[^\n]*", "", new) if asset == "ga_nakshatra" else True


def test_static_1344_shape():
    code = _code(M1344)
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert "ADD COLUMN IF NOT EXISTS build_ayanamshas text[]" in code
    assert "charts_build_ayanamshas_check" in code and "IF NOT EXISTS (SELECT 1 FROM pg_constraint" in code
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code)
    assert not re.search(r"\bCREATE\s+(OR\s+REPLACE\s+)?(UNIQUE\s+)?(TABLE|INDEX|FUNCTION|TRIGGER|VIEW|TYPE)\b", code, re.I)
    assert not re.search(r"\bGRANT\b", code, re.I)


def test_static_public_schema_guard_reports_zero_findings():
    out = subprocess.run(["python3", str(_REPO / "platform/scripts/governance/check_public_schema_migration_privilege.py")],
                         capture_output=True, text=True, cwd=_REPO)
    assert out.returncode == 0, out.stdout + out.stderr


# -- LIVE tier: disposable PostgreSQL -------------------------------------------------------------------------------------

def _find_pg_bin() -> Path | None:
    cands: list[Path] = []
    if os.environ.get("PG_BIN"):
        cands.append(Path(os.environ["PG_BIN"]))
    which = shutil.which("initdb")
    if which:
        cands.append(Path(which).parent)
    cands += [Path(p) for p in sorted(glob.glob("/opt/homebrew/opt/postgresql@*/bin"), reverse=True)]
    cands += [Path(p) for p in sorted(glob.glob("/usr/lib/postgresql/*/bin"), reverse=True)]
    for c in cands:
        if (c / "initdb").exists() and (c / "pg_ctl").exists():
            return c
    return None


@pytest.fixture(scope="session")
def pg_cluster():
    psycopg = pytest.importorskip("psycopg")
    binp = _find_pg_bin()
    if binp is None:
        pytest.skip("no PostgreSQL server binaries (initdb/pg_ctl) found; set PG_BIN")
    root = Path(tempfile.mkdtemp(prefix="m1344pg"))
    data = root / "data"
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([str(binp / "initdb"), "-D", str(data), "-U", "postgres", "-A", "trust", "-E", "UTF8", "--no-sync"],
                   check=True, capture_output=True)
    opts = f"-p {port} -c listen_addresses=127.0.0.1 -c unix_socket_directories={root} -c fsync=off"
    subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-o", opts, "-w", "-l", str(root / "log"), "start"],
                   check=True, capture_output=True)
    try:
        yield {"port": port, "psycopg": psycopg}
    finally:
        subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)


_n = 0


@pytest.fixture()
def db(pg_cluster):
    global _n
    _n += 1
    name = f"t{_n}"
    psycopg, port = pg_cluster["psycopg"], pg_cluster["port"]
    with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"CREATE DATABASE {name}")

    def connect():
        return psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname=name)

    yield connect
    with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")


def _trigger_ddl() -> str:
    """The PRODUCTION trigger function + trigger text, extracted from migration 596 (not a replica)."""
    t = _M596.read_text()
    fn = re.search(r"CREATE OR REPLACE FUNCTION nirmana_invalidate_registry_receipts\(\).*?\$\$;", t, re.S).group(0)
    trg = re.search(r"CREATE TRIGGER nirmana_registry_receipt_invalidation.*?EXECUTE FUNCTION nirmana_invalidate_registry_receipts\(\);", t, re.S).group(0)
    return fn + "\n" + trg


_DDL = """
CREATE TABLE charts (id uuid PRIMARY KEY, name text);
CREATE TABLE asset_registry (
    asset_id text PRIMARY KEY, layer text NOT NULL DEFAULT 'x', depends_on text[], is_active boolean NOT NULL DEFAULT true,
    target_table text, count_sql text, target_floor integer, size_sql text, volume_explanation text,
    natural_key_partition text, health_probe text, integrity_check_sql text, asset_kind text, asset_type text,
    scope text, has_writer boolean);
CREATE TABLE asset_freshness (
    asset_id text NOT NULL REFERENCES asset_registry(asset_id) ON DELETE CASCADE,
    chart_id uuid NULL REFERENCES charts(id) ON DELETE CASCADE,
    scope_key text GENERATED ALWAYS AS (COALESCE(chart_id::text, '__global__')) STORED,
    partition_key text NOT NULL DEFAULT 'p',
    freshness_state text NOT NULL CHECK (freshness_state IN ('fresh', 'stale', 'unknown')),
    reasons jsonb NOT NULL DEFAULT '[]'::jsonb, receipt_version text NOT NULL DEFAULT 'v',
    observed_at timestamptz NOT NULL DEFAULT '2026-10-01T00:00:00Z',
    PRIMARY KEY (asset_id, scope_key, partition_key));
CREATE TABLE bodha_pratijna (pratijna_id serial PRIMARY KEY, chart_id uuid NOT NULL, ayanamsha_id text NOT NULL,
    event_class_id text NOT NULL, status text NOT NULL DEFAULT 'promised', grade numeric DEFAULT 5,
    UNIQUE (chart_id, ayanamsha_id, event_class_id));
CREATE TABLE chart_divisionals (id serial PRIMARY KEY, chart_id uuid, graha text, ayanamsha_id text, varga text,
    fact_category text, fact_key text, fact_subject text, sign text, sign_number int, vargottama boolean);
CREATE TABLE chart_facts (id serial PRIMARY KEY, chart_id uuid, ayanamsha_id text, fact_category text, fact_subject text,
    fact_key text, fact_value_num numeric, fact_value_text text, verification_pass_status text DEFAULT 'single');
CREATE TABLE phala_rectification (id serial PRIMARY KEY, chart_id uuid NOT NULL, offset_minutes int NOT NULL,
    ayanamsha_id text NOT NULL, lagna_stable boolean DEFAULT true, UNIQUE (chart_id, offset_minutes, ayanamsha_id));
CREATE TABLE phala_rectification_best (chart_id uuid PRIMARY KEY, best_candidate_id int);
"""

_ASSET_ROWS = ["bo_pratijna", "ga_vargas", "ph_rectification", "ga_nakshatra", "bo_other"]


def _setup(connect, *, with_old: bool = True, with_1344: bool = True):
    with connect() as c:
        c.execute(_DDL)
        c.execute(_trigger_ddl())
        for a in _ASSET_ROWS:
            txt = _old(a) if (a in SPECS and with_old) else "SELECT true"
            c.execute("INSERT INTO asset_registry (asset_id, integrity_check_sql) VALUES (%s, %s)", (a, txt))
        for ch in (CANON, FIVE_CHART, ONE_CHART):
            c.execute("INSERT INTO charts (id, name) VALUES (%s, 'x')", (ch,))
            for a in _ASSET_ROWS:
                c.execute("INSERT INTO asset_freshness (asset_id, chart_id, freshness_state) VALUES (%s, %s, 'fresh')", (a, ch))
        c.commit()
    if with_1344:
        _apply(connect, M1344)


def _apply(connect, path: Path, notices: list[str] | None = None):
    conn = connect()
    if notices is not None:
        conn.add_notice_handler(lambda d: notices.append(d.message_primary))
    try:
        conn.execute(path.read_text())
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _apply_asset(connect, asset, notices=None):
    _apply(connect, _MIG / SPECS[asset]["file"], notices)


def _q(connect, sql, params=None):
    with connect() as c:
        return c.execute(sql, params).fetchall()


def _run_check(connect, sql: str) -> bool:
    """Run an integrity text the way asset_runner._probe_asset does: cur.execute(sql) with no parameters, first column of row 1."""
    with connect() as c:
        return bool(c.execute(sql).fetchone()[0])


def _set_scope(connect, chart, scope):
    with connect() as c:
        c.execute("UPDATE charts SET build_ayanamshas = %s WHERE id = %s", (scope, chart))
        c.commit()


# -- data builders (one per asset) ----------------------------------------------------------------------------------

_EC = None


def _event_classes() -> list[str]:
    global _EC
    if _EC is None:
        m = re.search(r"unnest\(ARRAY\[\s*('achievement_recognition'.*?)\]\)", _old("bo_pratijna"), re.S)
        _EC = re.findall(r"'([a-z_]+)'", m.group(1))
        assert len(_EC) == 27
    return _EC


VARGAS = re.findall(r"'(D\d+)'", re.search(r"unnest\(ARRAY\[('D1'.*?)\]\)", _old("ga_vargas"), re.S).group(1))
GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
SUBJ = dict(Sun="SUN", Moon="MOON", Mars="MAR", Mercury="MER", Jupiter="JUP", Venus="VEN", Saturn="SAT", Rahu="RAH_MEAN", Ketu="KET_MEAN")


def _add_pratijna(connect, chart, ayas, skip: tuple[str, str] | None = None):
    with connect() as c:
        for a in ayas:
            for ec in _event_classes():
                if skip == (a, ec):
                    continue
                c.execute("INSERT INTO bodha_pratijna (chart_id, ayanamsha_id, event_class_id) VALUES (%s,%s,%s)", (chart, a, ec))
        c.commit()


def _add_vargas(connect, chart, ayas, skip: tuple[str, str] | None = None):
    with connect() as c:
        for a in ayas:
            for v in VARGAS:
                for g in GRAHAS[: (8 if skip == (a, v) else 9)]:
                    c.execute("INSERT INTO chart_divisionals (chart_id, graha, ayanamsha_id, varga, fact_category, fact_key, "
                              "fact_subject, sign, sign_number) VALUES (%s,%s,%s,%s,'varga_position','sign','x','Aries',1)",
                              (chart, g, a, v))
            if chart == CANON:  # conjunct (c): the D1 sign must match chart_facts graha_position/sign
                for g in GRAHAS:
                    c.execute("INSERT INTO chart_facts (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_text) "
                              "VALUES (%s,%s,'graha_position',%s,'sign','Aries')", (chart, a, SUBJ[g]))
        c.commit()


def _add_rect(connect, chart, ayas, skip: tuple[str, int] | None = None):
    with connect() as c:
        for a in ayas:
            for off in range(-90, 91, 5):
                if skip == (a, off):
                    continue
                c.execute("INSERT INTO phala_rectification (chart_id, offset_minutes, ayanamsha_id) VALUES (%s,%s,%s)", (chart, off, a))
        c.commit()


def _add_nak(connect, chart, consistency: str | None, subjects=("MOON", "SUN")):
    with connect() as c:
        for s in subjects:
            c.execute("INSERT INTO chart_facts (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_num) "
                      "VALUES (%s,'INVARIANT','nakshatra_cross_ayanamsha',%s,'stable_nakshatra_id',25)", (chart, s))
            if consistency is not None:
                c.execute("INSERT INTO chart_facts (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_text) "
                          "VALUES (%s,'INVARIANT','nakshatra_cross_ayanamsha',%s,'nak_5ay_consistency',%s)", (chart, s, consistency))
        c.commit()


# generic adapters: add(chart, ayas, missing_one) -> data for the chart
def _adder(asset):
    if asset == "bo_pratijna":
        return lambda cn, ch, ayas, miss=False: _add_pratijna(cn, ch, ayas, (ayas[-1], _event_classes()[3]) if miss else None)
    if asset == "ga_vargas":
        return lambda cn, ch, ayas, miss=False: _add_vargas(cn, ch, ayas, (ayas[-1], "D9") if miss else None)
    if asset == "ph_rectification":
        return lambda cn, ch, ayas, miss=False: _add_rect(cn, ch, ayas, (ayas[-1], 35) if miss else None)
    raise AssertionError(asset)


GRID_ASSETS = ["bo_pratijna", "ga_vargas", "ph_rectification"]


def _full_chart(asset):
    """The chart the check measures: ga_vargas is pinned to the canonical chart by literal; the others cover every chart."""
    return CANON if asset == "ga_vargas" else FIVE_CHART


@pytest.mark.parametrize("asset", GRID_ASSETS)
def test_live_a_null_scope_five_ayanamsha_data_new_equals_old_green_and_red(db, asset):
    _setup(db)
    ch = _full_chart(asset)
    add = _adder(asset)
    add(db, ch, FIVE)
    assert _run_check(db, _old(asset)) is True
    assert _run_check(db, _new(asset)) is True
    # one cell missing: both red
    with db() as c:
        c.execute("DELETE FROM bodha_pratijna; DELETE FROM chart_divisionals; DELETE FROM chart_facts; DELETE FROM phala_rectification;")
        c.commit()
    add(db, ch, FIVE, True)
    assert _run_check(db, _old(asset)) is False
    assert _run_check(db, _new(asset)) is False
    # a whole ayanamsha missing: both red
    with db() as c:
        c.execute("DELETE FROM bodha_pratijna; DELETE FROM chart_divisionals; DELETE FROM chart_facts; DELETE FROM phala_rectification;")
        c.commit()
    add(db, ch, FIVE[:4])
    assert _run_check(db, _old(asset)) is False
    assert _run_check(db, _new(asset)) is False


@pytest.mark.parametrize("asset", GRID_ASSETS)
def test_live_b_lahiri_only_chart_with_lahiri_only_data_new_green_old_red(db, asset):
    _setup(db)
    ch = _full_chart(asset)
    _set_scope(db, ch, ["lahiri_chitrapaksha"])
    _adder(asset)(db, ch, ["lahiri_chitrapaksha"])
    assert _run_check(db, _old(asset)) is False
    assert _run_check(db, _new(asset)) is True


@pytest.mark.parametrize("asset", GRID_ASSETS)
def test_live_c_lahiri_only_chart_missing_its_lahiri_rows_new_red(db, asset):
    _setup(db)
    ch = _full_chart(asset)
    _set_scope(db, ch, ["lahiri_chitrapaksha"])
    # (1) a cell of its Lahiri grid missing
    _adder(asset)(db, ch, ["lahiri_chitrapaksha"], True)
    assert _run_check(db, _new(asset)) is False
    # (2) no Lahiri rows at all, only another ayanamsha's rows: a bare count would let this through
    with db() as c:
        c.execute("DELETE FROM bodha_pratijna; DELETE FROM chart_divisionals; DELETE FROM chart_facts; DELETE FROM phala_rectification;")
        c.commit()
    _adder(asset)(db, ch, ["true_chitra"])
    assert _run_check(db, _new(asset)) is False
    # (3) the scope still leads the data: configured for five, holding only Lahiri rows, is red (checked via NULL)
    with db() as c:
        c.execute("DELETE FROM bodha_pratijna; DELETE FROM chart_divisionals; DELETE FROM chart_facts; DELETE FROM phala_rectification;")
        c.commit()
    _set_scope(db, ch, None)
    _adder(asset)(db, ch, ["lahiri_chitrapaksha"])
    assert _run_check(db, _new(asset)) is False


def test_live_c_ph_rectification_extra_ayanamsha_beyond_scope_stays_red(db):
    """The old <> 5 was exact (more than five also failed); the new check keeps that: a one-chart holding two ayanamshas is red."""
    _setup(db)
    _set_scope(db, FIVE_CHART, ["lahiri_chitrapaksha"])
    _add_rect(db, FIVE_CHART, ["lahiri_chitrapaksha", "true_chitra"])
    assert _run_check(db, _new("ph_rectification")) is False


def test_live_missing_charts_row_falls_back_to_the_five(db):
    """A chart_id with no charts row keeps today's meaning (five) for the table-wide checks; ga_vargas stays red on an absent charts row."""
    _setup(db)
    ghost = "0b0b0b0b-0000-4000-8000-00000000dead"
    _add_pratijna(db, ghost, ["lahiri_chitrapaksha"])
    _add_rect(db, ghost, ["lahiri_chitrapaksha"])
    assert _run_check(db, _new("bo_pratijna")) is False and _run_check(db, _old("bo_pratijna")) is False
    assert _run_check(db, _new("ph_rectification")) is False and _run_check(db, _old("ph_rectification")) is False
    with db() as c:
        c.execute("DELETE FROM charts WHERE id = %s", (CANON,))
        c.commit()
    assert _run_check(db, _new("ga_vargas")) is False and _run_check(db, _old("ga_vargas")) is False  # empty table + no charts row: red


@pytest.mark.parametrize("asset", ["bo_pratijna", "ph_rectification"])
def test_live_d_mixed_database_green_only_if_both_charts_complete(db, asset):
    _setup(db)
    add = _adder(asset)
    _set_scope(db, ONE_CHART, ["lahiri_chitrapaksha"])  # FIVE_CHART stays NULL
    add(db, FIVE_CHART, FIVE)
    add(db, ONE_CHART, ["lahiri_chitrapaksha"])
    assert _run_check(db, _new(asset)) is True
    assert _run_check(db, _old(asset)) is False   # the old text cannot see a one-ayanamsha chart as complete
    # five-chart loses a cell -> red
    with db() as c:
        c.execute("DELETE FROM bodha_pratijna WHERE chart_id=%s AND ayanamsha_id='raman' AND event_class_id=%s", (FIVE_CHART, _event_classes()[0])) if asset == "bo_pratijna" else \
            c.execute("DELETE FROM phala_rectification WHERE chart_id=%s AND ayanamsha_id='raman' AND offset_minutes=0", (FIVE_CHART,))
        c.commit()
    assert _run_check(db, _new(asset)) is False
    # restore that one cell, then the one-chart loses a cell -> red
    with db() as c:
        if asset == "bo_pratijna":
            c.execute("INSERT INTO bodha_pratijna (chart_id, ayanamsha_id, event_class_id) VALUES (%s,'raman',%s)", (FIVE_CHART, _event_classes()[0]))
        else:
            c.execute("INSERT INTO phala_rectification (chart_id, offset_minutes, ayanamsha_id) VALUES (%s,0,'raman')", (FIVE_CHART,))
        c.commit()
    assert _run_check(db, _new(asset)) is True
    with db() as c:
        c.execute("DELETE FROM bodha_pratijna WHERE chart_id=%s AND event_class_id=%s", (ONE_CHART, _event_classes()[0])) if asset == "bo_pratijna" else \
            c.execute("DELETE FROM phala_rectification WHERE chart_id=%s AND offset_minutes=0", (ONE_CHART,))
        c.commit()
    assert _run_check(db, _new(asset)) is False


def test_live_d_ga_vargas_mixed_database_measures_the_canonical_chart_only(db):
    """ga_vargas is pinned to the canonical chart by literal (the disclosed tradeoff, unchanged): the other chart is not measured."""
    _setup(db)
    _set_scope(db, CANON, ["lahiri_chitrapaksha"])
    _add_vargas(db, CANON, ["lahiri_chitrapaksha"])
    _add_vargas(db, FIVE_CHART, ["lahiri_chitrapaksha"])  # an incomplete five-chart: not measured by (e)
    assert _run_check(db, _new("ga_vargas")) is True and _run_check(db, _old("ga_vargas")) is False
    with db() as c:
        c.execute("DELETE FROM chart_divisionals WHERE chart_id=%s AND varga='D150'", (CANON,))
        c.commit()
    assert _run_check(db, _new("ga_vargas")) is False


def test_live_ga_vargas_null_scope_canonical_five_data_same_as_old(db):
    _setup(db)
    _add_vargas(db, CANON, FIVE)
    assert _run_check(db, _old("ga_vargas")) is True and _run_check(db, _new("ga_vargas")) is True


# -- ga_nakshatra (d) -----------------------------------------------------------------------------------------------------

def test_live_ga_nakshatra_null_scope_requires_5_of_5_exactly_like_old(db):
    _setup(db)
    _add_nak(db, FIVE_CHART, "5/5")
    assert _run_check(db, _old("ga_nakshatra")) is True and _run_check(db, _new("ga_nakshatra")) is True
    for bad in ("4/5", "1/1", None):
        with db() as c:
            c.execute("DELETE FROM chart_facts")
            c.commit()
        _add_nak(db, FIVE_CHART, bad)
        assert _run_check(db, _old("ga_nakshatra")) is False, bad
        assert _run_check(db, _new("ga_nakshatra")) is False, bad


def test_live_ga_nakshatra_lahiri_only_chart_requires_1_of_1(db):
    _setup(db)
    _set_scope(db, ONE_CHART, ["lahiri_chitrapaksha"])
    _add_nak(db, ONE_CHART, "1/1")
    assert _run_check(db, _old("ga_nakshatra")) is False
    assert _run_check(db, _new("ga_nakshatra")) is True
    for bad in ("5/5", "0/1", None):
        with db() as c:
            c.execute("DELETE FROM chart_facts")
            c.commit()
        _add_nak(db, ONE_CHART, bad)
        assert _run_check(db, _new("ga_nakshatra")) is False, bad


def test_live_ga_nakshatra_mixed_database(db):
    _setup(db)
    _set_scope(db, ONE_CHART, ["lahiri_chitrapaksha"])
    _add_nak(db, FIVE_CHART, "5/5")
    _add_nak(db, ONE_CHART, "1/1")
    assert _run_check(db, _new("ga_nakshatra")) is True
    with db() as c:
        c.execute("DELETE FROM chart_facts WHERE chart_id=%s AND fact_key='nak_5ay_consistency' AND fact_subject='SUN'", (FIVE_CHART,))
        c.commit()
    assert _run_check(db, _new("ga_nakshatra")) is False


def test_live_ga_nakshatra_no_stable_rows_is_green_for_a_one_chart(db):
    _setup(db)
    _set_scope(db, ONE_CHART, ["lahiri_chitrapaksha"])
    assert _run_check(db, _new("ga_nakshatra")) is True   # NOT EXISTS-shaped: nothing to contradict (the writer decides what it emits)


# -- (e) the CHECK constraint ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("value,ok", [
    (None, True), (["lahiri_chitrapaksha"], True), (FIVE, True), (["raman", "true_chitra"], True),
    (["x"], False), ([], False), (["lahiri_chitrapaksha", "bogus"], False), ([None], False), (["lahiri"], False),
])
def test_live_e_check_constraint(db, value, ok):
    _setup(db)
    with db() as c:
        if ok:
            c.execute("UPDATE charts SET build_ayanamshas = %s::text[] WHERE id = %s", (value, CANON))
            c.commit()
        else:
            with pytest.raises(Exception) as ei:
                c.execute("UPDATE charts SET build_ayanamshas = %s::text[] WHERE id = %s", (value, CANON))
            assert "charts_build_ayanamshas_check" in str(ei.value)


def test_live_1344_idempotent_and_adds_only_a_nullable_column(db):
    _setup(db, with_1344=False)
    before = _q(db, "SELECT column_name FROM information_schema.columns WHERE table_name='charts' ORDER BY 1")
    _apply(db, M1344)
    _apply(db, M1344)  # second run: no error, no second constraint
    after = [r[0] for r in _q(db, "SELECT column_name FROM information_schema.columns WHERE table_name='charts' ORDER BY 1")]
    assert after == sorted([r[0] for r in before] + ["build_ayanamshas"])
    assert _q(db, "SELECT count(*) FROM pg_constraint WHERE conname='charts_build_ayanamshas_check'")[0][0] == 1
    assert _q(db, "SELECT count(*) FROM charts WHERE build_ayanamshas IS NOT NULL")[0][0] == 0


# -- migrations 1345-1348: apply, guard, idempotency, trigger ----------------------------------------------------------------

@pytest.mark.parametrize("asset", sorted(SPECS))
def test_live_migration_applies_replaces_old_text_with_new_md5(db, asset):
    _setup(db)
    _apply_asset(db, asset)
    txt = _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id=%s", (asset,))[0][0]
    assert _md5(txt) == SPECS[asset]["new"] and len(txt) == SPECS[asset]["new_len"]
    # the other asset rows are untouched
    for other in SPECS:
        if other != asset:
            assert _md5(_q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id=%s", (other,))[0][0]) == SPECS[other]["old"]
    assert _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bo_other'")[0][0] == "SELECT true"


@pytest.mark.parametrize("asset", sorted(SPECS))
def test_live_migration_idempotent_foreign_text_noop_and_missing_column_raises(db, asset):
    _setup(db)
    _apply_asset(db, asset)
    x1 = _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id=%s", (asset,))
    notes: list[str] = []
    _apply_asset(db, asset, notes)
    assert _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id=%s", (asset,)) == x1
    assert any("already chart-aware" in n for n in notes)

    foreign = _old(asset) + "\n-- edited meanwhile\n"
    with db() as c:
        c.execute("UPDATE asset_registry SET integrity_check_sql=%s WHERE asset_id=%s", (foreign, asset))
        c.commit()
    notes = []
    _apply_asset(db, asset, notes)  # must not raise
    assert _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id=%s", (asset,))[0][0] == foreign
    assert any("not the text this migration was written against" in n and "NO-OP" in n for n in notes)


@pytest.mark.parametrize("asset", sorted(SPECS))
def test_live_migration_raises_when_the_column_is_missing(db, asset):
    _setup(db, with_1344=False)
    with pytest.raises(Exception) as ei:
        _apply_asset(db, asset)
    assert "build_ayanamshas is missing" in str(ei.value)
    assert _md5(_q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id=%s", (asset,))[0][0]) == SPECS[asset]["old"]


def test_live_empty_registry_row_is_a_noop(db):
    _setup(db)
    with db() as c:
        c.execute("DELETE FROM asset_registry WHERE asset_id='ga_vargas'")
        c.commit()
    notes: list[str] = []
    _apply_asset(db, "ga_vargas", notes)
    assert any("no ga_vargas registry row" in n for n in notes)


def test_live_post_check_catches_a_silent_noop(db):
    _setup(db)
    with db() as c:
        c.execute("CREATE RULE swallow AS ON UPDATE TO asset_registry WHERE OLD.asset_id = 'bo_pratijna' DO INSTEAD NOTHING")
        c.commit()
    with pytest.raises(Exception) as ei:
        _apply_asset(db, "bo_pratijna")
    assert "update did not take" in str(ei.value)


@pytest.mark.parametrize("asset", sorted(SPECS))
def test_live_trigger_stales_this_assets_receipts_on_every_chart_and_nothing_else(db, asset):
    """integrity_check_sql IS a column of the production staling trigger (migration 596): the apply stales the asset on EVERY chart."""
    _setup(db)
    before_other = _q(db, "SELECT asset_id, chart_id::text, freshness_state, reasons::text, observed_at::text FROM asset_freshness "
                          "WHERE asset_id <> %s ORDER BY 1,2", (asset,))
    _apply_asset(db, asset)
    rows = _q(db, "SELECT chart_id::text, freshness_state, reasons::text FROM asset_freshness WHERE asset_id=%s ORDER BY 1", (asset,))
    assert len(rows) == 3 and all(r[1] == "stale" and "registry_changed" in r[2] for r in rows)
    assert {r[0] for r in rows} == {CANON, FIVE_CHART, ONE_CHART}
    assert _q(db, "SELECT asset_id, chart_id::text, freshness_state, reasons::text, observed_at::text FROM asset_freshness "
                  "WHERE asset_id <> %s ORDER BY 1,2", (asset,)) == before_other
    # the 1344 column add did not stale anything (checked via the other assets above being fresh after _setup applied 1344)
    assert all(r[2] == "fresh" for r in before_other)


def test_live_1344_does_not_fire_the_staling_trigger(db):
    _setup(db, with_1344=False)
    _apply(db, M1344)
    assert {r[0] for r in _q(db, "SELECT DISTINCT freshness_state FROM asset_freshness")} == {"fresh"}
