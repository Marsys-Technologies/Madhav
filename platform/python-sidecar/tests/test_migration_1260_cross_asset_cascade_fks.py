"""
Migration 1260 (Suvarna, SS ruling N-99, Q-L4-03, widened to cross-ASSET; SS migration review): seven cross-asset ON DELETE
CASCADE foreign keys are dropped (a rebuild of asset A must never silently delete asset B's rows), the five L4 tables that
thereby lose their only chart-deletion path get an OWNERSHIP link (chart_id -> charts(id) ON DELETE CASCADE), and the orphan
detector ships as plain read-only SQL (no DB object). HELD: own draft PR, merges only after S-L1 and only on SS's review.

Two tiers:
  * STATIC (always runs, DB-free): file shape, the two lists, guards, header sections; the detector files.
  * LIVE (needs PostgreSQL server binaries): applies the REAL migration file, AS amjis_app, to a DISPOSABLE cluster this module
    creates with initdb in a temp dir (unix socket only, trust auth, removed at session end). It never connects to anything
    else. Skipped, loudly, when no initdb/pg_ctl is found; REQUIRE_PG_BINARIES=1 turns the skip into a failure.
    The cluster MIRRORS production's privilege layout (read 2026-10-03): schema public is owned by data_plane_schema_owner and
    amjis_app has USAGE only (NO CREATE), while amjis_app owns every table. A migration that tried to CREATE a view or
    function in public fails here exactly as it would in production (test_a_create_view_in_public_fails_as_amjis_app).
The fixture reproduces the seven foreign keys with their production names and definitions, the production child-side indexes,
the SET NULL links that must NOT be touched, and the charts links that exist in production (kala_convergence, kala_darshana,
kala_obstruction -> charts ON DELETE CASCADE) and DO NOT exist for the five L4 tables.
What it proves: before apply a parent delete cascades; after apply it does not, children become orphans, and the plain-SQL
detector (cross_asset_reference_orphans.sql, run the way the .py runs it) reports exactly them; THE DELETE-ROUTE SCENARIO: delete a
throwaway chart (as platform/src/app/api/charts/[id]/route.ts does) and every row of the five L4 tables, including anchors
with a NULL convergence_id, is gone with the other chart untouched; idempotent re-run; guards; lock_timeout; active-run guard.
A mutation section rewrites the real SQL and requires every mutant to be caught.
It does NOT prove production state (read from production structure after deploy; Trap 103).
"""
from __future__ import annotations

import glob
import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_MIG = _REPO / "platform" / "migrations"
_M1260 = _MIG / "1260_cross_asset_cascade_fks_to_detector.sql"
_DET_SQL = _REPO / "platform" / "scripts" / "nirmana" / "cross_asset_reference_orphans.sql"
_DET_PY = _REPO / "platform" / "scripts" / "nirmana" / "cross_asset_reference_orphans.py"
_REAL = _M1260.read_text()

# constraint | child | child column | parent | parent column
REFS = [
    ("phala_anchors_convergence_id_fkey", "phala_anchors", "convergence_id", "kala_convergence", "convergence_id"),
    ("kala_darshana_convergence_id_fkey", "kala_darshana", "convergence_id", "kala_convergence", "convergence_id"),
    ("kala_obstruction_convergence_id_fkey", "kala_obstruction", "convergence_id", "kala_convergence", "convergence_id"),
    ("phala_pramana_anchor_id_fkey", "phala_pramana", "anchor_id", "phala_anchors", "anchor_id"),
    ("phala_sankrama_source_anchor_id_fkey", "phala_sankrama", "source_anchor_id", "phala_anchors", "anchor_id"),
    ("phala_sodhana_anchor_id_fkey", "phala_sodhana", "anchor_id", "phala_anchors", "anchor_id"),
    ("phala_suddha_sodhana_anchor_id_fkey", "phala_suddha_sodhana", "anchor_id", "phala_anchors", "anchor_id"),
]
CONS = [r[0] for r in REFS]
CHART_LINKS = [("phala_anchors_chart_id_fkey", "phala_anchors"), ("phala_pramana_chart_id_fkey", "phala_pramana"),
               ("phala_sankrama_chart_id_fkey", "phala_sankrama"), ("phala_sodhana_chart_id_fkey", "phala_sodhana"),
               ("phala_suddha_sodhana_chart_id_fkey", "phala_suddha_sodhana")]
L4_FIVE = [t for _, t in CHART_LINKS]
# deleted with the chart after 1260 (kala_* by their production chart links, the five L4 tables by the new ones). phala_muhurta
# has NO chart link in production, before or after (pre-existing gap, reported in the PR, not fixed here).
CHART_DELETE_REACHES = ["kala_convergence", "kala_bhavishya", "kala_darshana", "kala_obstruction"] + L4_FIVE
OUT_OF_SCOPE = ["kala_bhavishya_convergence_id_fkey", "phala_anchors_bhavishya_id_fkey", "phala_muhurta_linked_anchor_id_fkey"]
CHART_A = "482012f1-710e-4a25-994a-93821f5871aa"
CHART_B = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
ACTIVE_ASSETS = ["ka_sangam", "ka_kala_darshana", "ka_vighnakara", "ka_bhavishya_lekha", "ph_nimitta", "ph_pramana", "ph_sodhana",
                 "ph_suddha_sodhana", "ph_sankrama"]


def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("--"))


def _flat(path: Path) -> str:
    return re.sub(r"\s+", " ", re.sub(r"^--", " ", path.read_text(), flags=re.M))


# -- STATIC tier --------------------------------------------------------------------

def test_the_reference_list_appears_once_and_is_exactly_the_seven_approved_references():
    code = _code(_M1260)
    arr = re.findall(r"refs text\[\] := ARRAY\[(.*?)\];", code, re.S)
    assert len(arr) == 1
    got = [tuple(m.split("|")) for m in re.findall(r"'([a-z_]+\|[a-z_]+\|[a-z_]+\|[a-z_]+\|[a-z_]+)'", arr[0])]
    assert got == REFS
    for con in CONS:
        assert code.count(con) == 1, f"{con} must appear only in the list"


def test_the_chart_link_list_appears_once_and_is_exactly_the_five_l4_tables():
    code = _code(_M1260)
    arr = re.findall(r"chart_links text\[\] := ARRAY\[(.*?)\];", code, re.S)
    assert len(arr) == 1
    assert [tuple(m.split("|")) for m in re.findall(r"'([a-z_]+\|[a-z_]+)'", arr[0])] == CHART_LINKS
    assert "chart_def constant text := 'FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE'" in code


def test_drops_and_chart_links_only_no_db_object_no_data_no_grant_no_transaction_control():
    code = _code(_M1260)
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert not re.search(r"^\s*(BEGIN|COMMIT|ROLLBACK)\s*;", code, re.M)
    assert not re.search(r"\b(CREATE\s+(OR\s+REPLACE\s+)?(VIEW|FUNCTION|TABLE|INDEX|TRIGGER|SCHEMA|EXTENSION)|INSERT INTO|UPDATE\s+\w+\s+SET|DELETE FROM|TRUNCATE|GRANT|REVOKE|DROP (TABLE|INDEX|COLUMN|VIEW|SCHEMA))\b", code, re.I)
    assert "security_invoker" not in code and "COMMENT ON" not in code
    assert code.count("DROP CONSTRAINT") == 1 and "DROP CONSTRAINT IF EXISTS" not in code
    assert code.count("ADD CONSTRAINT") == 1
    assert "SET NULL" not in code and not re.search(r"ON DELETE (RESTRICT|NO ACTION)", code)


def test_guards_and_post_checks_are_present():
    code = _code(_M1260)
    for needle in ("does not exist", "is not an ordinary table", "is not the constraint this migration was written against",
                   "pg_get_constraintdef", "is already absent", "still exists on public", "a cascading foreign key from",
                   "something else changed", "has no chart_id column", "chart_id is nullable", "has no charts row; report, do not backfill",
                   "is missing, not validated, not ON DELETE CASCADE", "c.convalidated AND c.confdeltype = 'c'", "$runs$",
                   "r.state NOT IN ('completed', 'failed', 'stopped')", "active build run(s)", "already present on public"):
        assert needle in code, needle
    assert code.index("ADD CONSTRAINT") < code.index("DROP CONSTRAINT"), "the chart links are added before the cascades are dropped"


def test_header_states_the_design_choice_effects_trigger_scan_serving_effect_chart_deletion_and_what_is_not_done():
    sql = _flat(_M1260)
    for needle in ("DESIGN CHOICE: DROP", "RESTRICT / NO ACTION would make the parent's delete-then-insert rebuild FAIL",
                   "DEFERRABLE INITIALLY DEFERRED does not help", "bigserial", "migration 363", "migration 680", "F-3",
                   "EFFECT ON THE EXISTING WRITERS", "ka_sangam", "ph_nimitta", "ORPHANS TODAY", "0 on all seven references",
                   "TRIGGER SCAN", "phala_anchors_identity_biu", "BLIND SPOTS", "SERVING EFFECT AT APPLY",
                   "nirmana_registry_receipt_invalidation does not fire", "CHART DELETION", "PRIVACY regression",
                   "charts/[id]/route.ts:87-107", "OWNERSHIP link", "7 anchors with a NULL convergence_id",
                   "THE DETECTOR (no DB object; read-only; REPORTED, NEVER BUILD-BLOCKING)", "cross_asset_reference_orphans.sql",
                   "NON-VACUITY" if "NON-VACUITY" in sql else "visibly vacuous", "LOCK-WAIT RISK", "ACTIVE RUNS (ENFORCED",
                   "HELD", "AFTER S-L1", "on SS's review", "NOT DONE HERE", "VERIFICATION BY PRODUCTION STRUCTURE", "ROLLBACK",
                   "222 foreign keys", "Q-L4-03", "suvarna_reader", "SET NULL links", "chart_fact_identity", "charts-row-delete",
                   "phala_muhurta, phala_mitigation and phala_phaladesa also have no FK to charts", "PR #3019"):
        assert needle in sql, f"header no longer states: {needle}"
    for con in CONS + [c for c, _ in CHART_LINKS]:
        assert con in sql


def test_detector_files_are_plain_read_only_sql_with_two_statements_and_seven_references():
    sql = _code(_DET_SQL)
    assert not re.search(r"\b(INSERT|UPDATE|DELETE|TRUNCATE|CREATE|ALTER|DROP|GRANT|REVOKE)\b", sql, re.I)
    stmts = [s for s in sql.split(";") if s.strip()]
    assert len(stmts) == 2
    for con in CONS:
        assert sql.count(f"'{con}'") >= 2
    py = _DET_PY.read_text()
    assert "conn.read_only = True" in py and "never build-blocking" in py.lower() and "EXPECTED_REFERENCES = 7" in py


def test_number_and_name_follow_the_pattern_and_are_free_of_siblings():
    assert _M1260.name.startswith("1260_") and len(list(_MIG.glob("1260_*.sql"))) == 1
    assert 1200 <= int(_M1260.name[:4]) <= 1299


# -- LIVE tier: disposable PostgreSQL ------------------------------------------------

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


@pytest.fixture(scope="module")
def pg_cluster():
    psycopg = pytest.importorskip("psycopg")
    binp = _find_pg_bin()
    if binp is None:
        if os.environ.get("REQUIRE_PG_BINARIES") == "1":
            pytest.fail("no PostgreSQL server binaries and REQUIRE_PG_BINARIES=1")
        pytest.skip("no PostgreSQL server binaries (initdb/pg_ctl) found; set PG_BIN")
    root = Path(tempfile.mkdtemp(prefix="m1260pg"))
    data = root / "data"
    sockdir = Path(tempfile.mkdtemp(prefix="m60", dir="/tmp"))  # unix socket paths are length-limited
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([str(binp / "initdb"), "-D", str(data), "-U", "postgres", "-A", "trust", "-E", "UTF8",
                    "--no-sync"], check=True, capture_output=True)
    opts = f"-p {port} -c listen_addresses='' -c unix_socket_directories={sockdir} -c fsync=off"
    subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-o", opts, "-w", "-l", str(root / "log"), "start"],
                   check=True, capture_output=True)
    try:
        with psycopg.connect(host=str(sockdir), port=port, user="postgres", dbname="postgres", autocommit=True) as c:
            c.execute("CREATE ROLE amjis_app LOGIN")
            c.execute("CREATE ROLE data_plane_schema_owner NOLOGIN")
        yield {"port": port, "sock": str(sockdir), "psycopg": psycopg}
    finally:
        subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(sockdir, ignore_errors=True)


_db_counter = 0


@pytest.fixture()
def db(pg_cluster):
    global _db_counter
    _db_counter += 1
    name = f"t{_db_counter}"
    psycopg, port, sock = pg_cluster["psycopg"], pg_cluster["port"], pg_cluster["sock"]
    with psycopg.connect(host=sock, port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"CREATE DATABASE {name}")

    def connect(user="postgres", **kw):
        return psycopg.connect(host=sock, port=port, user=user, dbname=name, **kw)

    yield connect
    with psycopg.connect(host=sock, port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")


def _apply(connect, sql: str, notices: list[str] | None = None):
    """Run a migration the way migrate.ts does (one transaction around the whole file), AS amjis_app: it owns the tables and
    has NO CREATE privilege on schema public."""
    conn = connect(user="amjis_app")
    try:
        if notices is not None:
            conn.add_notice_handler(lambda d: notices.append(d.message_primary or ""))
        conn.execute(sql)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _exec(connect, sql: str, params=None):
    with connect() as c:
        c.execute(sql, params)


def _q(connect, sql: str, params=None):
    with connect() as c:
        return c.execute(sql, params).fetchall()


# The production definitions (pg_get_constraintdef, 2026-10-03), production child-side indexes, the SET NULL links, and the
# production charts links (kala_* -> charts CASCADE exist; the five L4 tables have NONE).
_DDL = """
CREATE TABLE charts (id uuid PRIMARY KEY);
CREATE TABLE build_runs (id bigserial PRIMARY KEY, state text NOT NULL);
CREATE TABLE build_run_assets (run_id bigint NOT NULL REFERENCES build_runs(id), asset_id text NOT NULL);
CREATE TABLE kala_convergence (convergence_id bigserial PRIMARY KEY,
    chart_id uuid, CONSTRAINT kala_convergence_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE);
CREATE INDEX idx_kala_convergence_chart_id ON kala_convergence (chart_id);
CREATE TABLE kala_bhavishya (id bigserial PRIMARY KEY, chart_id uuid NOT NULL, convergence_id bigint,
    CONSTRAINT kala_bhavishya_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE,
    CONSTRAINT kala_bhavishya_convergence_id_fkey FOREIGN KEY (convergence_id) REFERENCES kala_convergence(convergence_id) ON DELETE SET NULL);
CREATE TABLE kala_darshana (id bigserial PRIMARY KEY, chart_id uuid NOT NULL, convergence_id bigint,
    CONSTRAINT kala_darshana_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE,
    CONSTRAINT kala_darshana_convergence_id_fkey FOREIGN KEY (convergence_id) REFERENCES kala_convergence(convergence_id) ON DELETE CASCADE);
CREATE UNIQUE INDEX idx_kala_darshana_convergence ON kala_darshana (convergence_id) WHERE (convergence_id IS NOT NULL);
CREATE TABLE kala_obstruction (id bigserial PRIMARY KEY, chart_id uuid NOT NULL, convergence_id bigint,
    CONSTRAINT kala_obstruction_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE,
    CONSTRAINT kala_obstruction_convergence_id_fkey FOREIGN KEY (convergence_id) REFERENCES kala_convergence(convergence_id) ON DELETE CASCADE);
CREATE INDEX idx_kala_obstruction_convergence ON kala_obstruction (convergence_id) WHERE (convergence_id IS NOT NULL);
CREATE TABLE phala_anchors (anchor_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid NOT NULL, convergence_id bigint, bhavishya_id bigint,
    CONSTRAINT phala_anchors_convergence_id_fkey FOREIGN KEY (convergence_id) REFERENCES kala_convergence(convergence_id) ON DELETE CASCADE,
    CONSTRAINT phala_anchors_bhavishya_id_fkey FOREIGN KEY (bhavishya_id) REFERENCES kala_bhavishya(id) ON DELETE SET NULL);
CREATE INDEX idx_phala_anchors_convergence_id_fk ON phala_anchors (convergence_id);
CREATE TABLE phala_pramana (pramana_id bigserial PRIMARY KEY, chart_id uuid NOT NULL, anchor_id uuid NOT NULL,
    CONSTRAINT phala_pramana_anchor_id_fkey FOREIGN KEY (anchor_id) REFERENCES phala_anchors(anchor_id) ON DELETE CASCADE);
CREATE INDEX phala_pramana_anchor_id ON phala_pramana (anchor_id);
CREATE TABLE phala_sankrama (sankrama_id bigserial PRIMARY KEY, chart_id uuid NOT NULL, source_anchor_id uuid,
    CONSTRAINT phala_sankrama_source_anchor_id_fkey FOREIGN KEY (source_anchor_id) REFERENCES phala_anchors(anchor_id) ON DELETE CASCADE);
CREATE INDEX phala_sankrama_source_anchor_idx ON phala_sankrama (source_anchor_id);
CREATE TABLE phala_sodhana (sodhana_id bigserial PRIMARY KEY, chart_id uuid NOT NULL, anchor_id uuid NOT NULL,
    CONSTRAINT phala_sodhana_anchor_id_fkey FOREIGN KEY (anchor_id) REFERENCES phala_anchors(anchor_id) ON DELETE CASCADE);
CREATE INDEX phala_sodhana_anchor_id ON phala_sodhana (anchor_id);
CREATE TABLE phala_suddha_sodhana (entry_id bigserial PRIMARY KEY, chart_id uuid NOT NULL, anchor_id uuid NOT NULL,
    CONSTRAINT phala_suddha_sodhana_anchor_id_fkey FOREIGN KEY (anchor_id) REFERENCES phala_anchors(anchor_id) ON DELETE CASCADE);
CREATE INDEX idx_phala_suddha_sodhana_anchor_id_fk ON phala_suddha_sodhana (anchor_id);
CREATE TABLE phala_muhurta (id bigserial PRIMARY KEY, chart_id uuid NOT NULL, linked_anchor_id uuid,
    CONSTRAINT phala_muhurta_linked_anchor_id_fkey FOREIGN KEY (linked_anchor_id) REFERENCES phala_anchors(anchor_id) ON DELETE SET NULL);
"""
_TABLES = ["charts", "kala_convergence", "kala_bhavishya", "kala_darshana", "kala_obstruction", "phala_anchors", "phala_pramana",
           "phala_sankrama", "phala_sodhana", "phala_suddha_sodhana", "phala_muhurta"]
_DATA_TABLES = [t for t in _TABLES if t != "charts"]


def _mirror_production(c):
    c.execute("ALTER SCHEMA public OWNER TO data_plane_schema_owner")
    c.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")
    c.execute("GRANT USAGE ON SCHEMA public TO amjis_app")
    for (t,) in c.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'").fetchall():
        c.execute(f'ALTER TABLE public."{t}" OWNER TO amjis_app')
    for (sq,) in c.execute("SELECT sequencename FROM pg_sequences WHERE schemaname = 'public'").fetchall():
        c.execute(f'ALTER SEQUENCE public."{sq}" OWNER TO amjis_app')


def _make_fixture(connect, *, extra_ddl: str = ""):
    with connect() as c:
        c.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public")  # scenarios reuse one database
        c.execute(_DDL)
        if extra_ddl:
            c.execute(extra_ddl)
        _mirror_production(c)
        c.commit()


def _seed(connect):
    """Charts A and B. Convergence 1,2 (A), 3 (B). Anchors a1 (conv 1), a2 (conv 2), a3 (conv 3), a4 (NULL conv: reachable by
    NO deletion path today). One child row per child table per anchor (sankrama also one NULL source), darshana/obstruction on
    conv 1..3 (+ one obstruction with a NULL convergence)."""
    with connect() as c:
        c.execute("INSERT INTO charts VALUES (%s), (%s)", (CHART_A, CHART_B))
        c.execute("INSERT INTO kala_convergence (chart_id) VALUES (%s), (%s), (%s)", (CHART_A, CHART_A, CHART_B))
        c.execute("INSERT INTO kala_bhavishya (chart_id, convergence_id) VALUES (%s, 1)", (CHART_A,))
        for cid, chart in ((1, CHART_A), (2, CHART_A), (3, CHART_B)):
            c.execute("INSERT INTO kala_darshana (chart_id, convergence_id) VALUES (%s, %s)", (chart, cid))
            c.execute("INSERT INTO kala_obstruction (chart_id, convergence_id) VALUES (%s, %s)", (chart, cid))
        c.execute("INSERT INTO kala_obstruction (chart_id, convergence_id) VALUES (%s, NULL)", (CHART_A,))
        for cid, chart in ((1, CHART_A), (2, CHART_A), (3, CHART_B), (None, CHART_A)):
            c.execute("INSERT INTO phala_anchors (chart_id, convergence_id) VALUES (%s, %s)", (chart, cid))
        c.execute("INSERT INTO phala_pramana (chart_id, anchor_id) SELECT chart_id, anchor_id FROM phala_anchors")
        c.execute("INSERT INTO phala_sodhana (chart_id, anchor_id) SELECT chart_id, anchor_id FROM phala_anchors")
        c.execute("INSERT INTO phala_suddha_sodhana (chart_id, anchor_id) SELECT chart_id, anchor_id FROM phala_anchors")
        c.execute("INSERT INTO phala_sankrama (chart_id, source_anchor_id) SELECT chart_id, anchor_id FROM phala_anchors")
        c.execute("INSERT INTO phala_sankrama (chart_id, source_anchor_id) VALUES (%s, NULL)", (CHART_A,))
        c.execute("INSERT INTO phala_muhurta (chart_id, linked_anchor_id) SELECT chart_id, anchor_id FROM phala_anchors LIMIT 2")
        c.commit()


def _fk_defs(connect):
    return dict(_q(connect, "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
                            "WHERE contype='f' AND connamespace='public'::regnamespace ORDER BY 1"))


def _counts(connect):
    return {t: _q(connect, f"SELECT count(*) FROM {t}")[0][0] for t in _TABLES}


def _chart_counts(connect, chart):
    out = {}
    for t in _DATA_TABLES:
        col = "chart_id"
        out[t] = _q(connect, f"SELECT count(*) FROM {t} WHERE {col} = %s", (chart,))[0][0]
    return out


def _data_digest(connect):
    return {t: _q(connect, f"SELECT md5(string_agg(to_jsonb(x)::text, '|' ORDER BY to_jsonb(x)::text)) FROM {t} x")[0][0] for t in _TABLES}


def _structure(connect):
    cols = _q(connect, "SELECT table_name, column_name, data_type, is_nullable FROM information_schema.columns "
                       "WHERE table_schema='public' AND table_name = ANY(%s) ORDER BY 1, ordinal_position", (_TABLES,))
    idx = _q(connect, "SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY 1, 2")
    return cols, idx


# The detector, run exactly the way cross_asset_reference_orphans.py runs it.
def _detector(connect):
    body = "\n".join(l for l in _DET_SQL.read_text().splitlines() if not l.lstrip().startswith("--"))
    s1, s2 = [s.strip() for s in body.split(";") if s.strip()]
    with connect() as c:
        summary = {r[0]: (r[5], r[6], r[7]) for r in c.execute(s1).fetchall()}
        by_chart = c.execute(s2).fetchall()
        n = len(c.execute(s1).fetchall())
    return summary, by_chart, n


# -- apply ---------------------------------------------------------------------------

def test_fixture_mirrors_production_amjis_app_has_usage_only_and_owns_the_tables(db):
    _make_fixture(db)
    r = _q(db, "SELECT has_schema_privilege('amjis_app','public','CREATE'), has_schema_privilege('amjis_app','public','USAGE'), "
               "(SELECT relowner::regrole::text FROM pg_class WHERE oid='phala_anchors'::regclass)")[0]
    assert r == (False, True, "amjis_app")


def test_a_create_view_in_public_fails_as_amjis_app(db):
    """The class of defect SS's review found (H1): under the mirrored layout a CREATE VIEW cannot be applied by the runner."""
    _make_fixture(db)
    with pytest.raises(Exception) as ei:
        _apply(db, "CREATE OR REPLACE VIEW public.vw_x AS SELECT 1 AS a")
    assert "permission denied for schema public" in str(ei.value)


def test_precondition_before_apply_a_parent_delete_cascades_through_all_levels_and_a_chart_delete_misses_the_null_convergence_anchor(db):
    _make_fixture(db)
    _seed(db)
    before = _counts(db)
    _exec(db, "DELETE FROM kala_convergence WHERE chart_id = %s", (CHART_A,))
    after = _counts(db)
    assert after["phala_anchors"] < before["phala_anchors"] and after["kala_darshana"] < before["kala_darshana"]
    assert after["phala_pramana"] < before["phala_pramana"] and after["phala_sodhana"] < before["phala_sodhana"]
    # and the existing leak: the NULL-convergence anchor of chart A survived the cascade and is reached by NO deletion path
    assert _q(db, "SELECT count(*) FROM phala_anchors WHERE chart_id = %s AND convergence_id IS NULL", (CHART_A,))[0][0] == 1


def test_apply_changes_exactly_the_seven_drops_and_five_chart_links_and_no_data_column_or_index(db):
    _make_fixture(db)
    _seed(db)
    fks_before, data_before, struct_before = _fk_defs(db), _data_digest(db), _structure(db)
    _apply(db, _REAL)
    fks_after = _fk_defs(db)
    assert set(fks_before) - set(fks_after) == set(CONS)
    assert set(fks_after) - set(fks_before) == {c for c, _ in CHART_LINKS}
    for c, _ in CHART_LINKS:
        assert fks_after[c] == "FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE"
    assert len(fks_after) == len(fks_before) - 7 + 5
    for name in OUT_OF_SCOPE:
        assert fks_after[name] == fks_before[name], f"out-of-scope FK {name} changed"
    assert _data_digest(db) == data_before, "a data row changed"
    cols_b, idx_b = struct_before
    cols_a, idx_a = _structure(db)
    assert cols_a == cols_b and idx_a == idx_b, "a column or index changed (the child-side indexes stay)"
    rows = _q(db, "SELECT conname, convalidated, confdeltype, condeferrable FROM pg_constraint WHERE conname = ANY(%s) ORDER BY 1",
              ([c for c, _ in CHART_LINKS],))
    assert rows == [(c, True, "c", False) for c in sorted(c for c, _ in CHART_LINKS)]
    assert _q(db, "SELECT count(*) FROM pg_views WHERE schemaname='public'")[0][0] == 0, "no view was created"
    assert _q(db, "SELECT count(*) FROM pg_proc WHERE pronamespace='public'::regnamespace")[0][0] == 0, "no function was created"


def test_after_apply_deleting_a_parent_deletes_no_child_and_the_plain_sql_detector_reports_the_orphans(db):
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    base, _, n = _detector(db)
    assert n == 7 and all(v[1] == 0 for v in base.values()), "no orphans before any delete"
    assert base["phala_anchors_convergence_id_fkey"][0] == 3 and base["kala_obstruction_convergence_id_fkey"][0] == 3
    assert base["phala_sankrama_source_anchor_id_fkey"][0] == 4, "NULL references are not counted as references"
    counts = _counts(db)
    _exec(db, "DELETE FROM kala_convergence WHERE chart_id = %s", (CHART_A,))  # convergence 1 and 2
    after = _counts(db)
    assert {k: v for k, v in after.items() if k != "kala_convergence"} == {k: v for k, v in counts.items() if k != "kala_convergence"}, \
        "no child row may be deleted by a parent delete"
    s, _, _ = _detector(db)
    assert s["kala_darshana_convergence_id_fkey"] == (3, 2, 1)
    assert s["kala_obstruction_convergence_id_fkey"] == (3, 2, 1)
    assert s["phala_anchors_convergence_id_fkey"] == (3, 2, 1)
    assert _q(db, "SELECT convergence_id FROM kala_bhavishya") == [(None,)], "the out-of-scope SET NULL link still nulls its child"
    _exec(db, "DELETE FROM phala_anchors WHERE chart_id = %s", (CHART_A,))
    s, by_chart, _ = _detector(db)
    for ref in ("phala_pramana_anchor_id_fkey", "phala_sodhana_anchor_id_fkey", "phala_suddha_sodhana_anchor_id_fkey"):
        assert s[ref] == (4, 3, 1), (ref, s[ref])
    assert s["phala_sankrama_source_anchor_id_fkey"] == (4, 3, 1)
    got = sorted((r[0], str(r[1]), r[2], r[3]) for r in by_chart if r[0] == "phala_pramana_anchor_id_fkey")
    assert got == sorted([("phala_pramana_anchor_id_fkey", CHART_B, 1, 0), ("phala_pramana_anchor_id_fkey", CHART_A, 3, 3)])


def test_the_delete_route_scenario_a_chart_delete_removes_every_row_of_the_five_l4_tables_after_1260(db):
    """platform/src/app/api/charts/[id]/route.ts deletes the chart row and relies on cascades for the derived data. A throwaway
    chart (A) with a full L4 family, including an anchor with a NULL convergence_id, is deleted; chart B must be untouched."""
    _make_fixture(db)
    _seed(db)
    b_before = _chart_counts(db, CHART_B)
    _apply(db, _REAL)
    assert all(v > 0 for k, v in _chart_counts(db, CHART_A).items() if k in L4_FIVE), "precondition: chart A has rows in all five"
    _exec(db, "DELETE FROM charts WHERE id = %s", (CHART_A,))  # the route's final statement
    a_after = _chart_counts(db, CHART_A)
    left = {t: n for t, n in a_after.items() if n and t in CHART_DELETE_REACHES}
    assert left == {}, f"rows left behind after chart deletion: {left}"
    assert a_after["phala_muhurta"] == 2, "phala_muhurta has no chart link in production either (pre-existing gap)"
    assert _chart_counts(db, CHART_B) == b_before, "another chart's rows were touched"


def test_without_the_chart_links_the_same_delete_would_leave_the_l4_rows_behind(db):
    """The regression the chart links prevent (SS review H2): only the seven drops, no chart links."""
    drops_only = re.sub(r"    -- Add pass FIRST.*?(?=    FOREACH r IN ARRAY refs LOOP\n        f := string_to_array\(r, '\|'\);\n        con := f\[1\]; child := f\[2\];\n        IF EXISTS)", "", _REAL, flags=re.S)
    assert drops_only != _REAL
    drops_only = drops_only.replace("fk_before - dropped + added", "fk_before - dropped").replace("IF NOT EXISTS (SELECT 1 FROM pg_constraint c\n                        WHERE c.conrelid = format('public.%I', child)::regclass AND c.conname = con AND c.contype = 'f'\n                          AND c.confrelid = 'public.charts'::regclass", "IF false AND NOT EXISTS (SELECT 1 FROM pg_constraint c\n                        WHERE c.conrelid = format('public.%I', child)::regclass AND c.conname = con AND c.contype = 'f'\n                          AND c.confrelid = 'public.charts'::regclass")
    _make_fixture(db)
    _seed(db)
    _apply(db, drops_only)
    _exec(db, "DELETE FROM charts WHERE id = %s", (CHART_A,))
    left = {t: v for t, v in _chart_counts(db, CHART_A).items() if t in L4_FIVE and v > 0}
    assert left, "expected leftovers without the chart links (otherwise the links prove nothing)"


def test_a_child_with_a_missing_parent_can_now_be_inserted_and_the_detector_sees_it(db):
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    _exec(db, "INSERT INTO phala_sodhana (chart_id, anchor_id) VALUES (%s, gen_random_uuid())", (CHART_A,))
    assert _detector(db)[0]["phala_sodhana_anchor_id_fkey"] == (5, 1, 1)


def test_chart_links_refuse_an_insert_for_a_missing_chart(db):
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    with pytest.raises(Exception) as ei:
        _exec(db, "INSERT INTO phala_anchors (chart_id) VALUES (gen_random_uuid())")
    assert "phala_anchors_chart_id_fkey" in str(ei.value)


def test_ka_sangam_style_delete_then_reinsert_then_children_rebuilt(db):
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    _exec(db, "DELETE FROM kala_convergence WHERE chart_id = %s", (CHART_A,))
    _exec(db, "INSERT INTO kala_convergence (chart_id) VALUES (%s), (%s)", (CHART_A, CHART_A))  # ids 4, 5
    s = _detector(db)[0]
    assert s["phala_anchors_convergence_id_fkey"][1] == 2 and s["kala_darshana_convergence_id_fkey"][1] == 2
    _exec(db, "DELETE FROM kala_darshana WHERE chart_id = %s", (CHART_A,))
    _exec(db, "INSERT INTO kala_darshana (chart_id, convergence_id) VALUES (%s, 4), (%s, 5)", (CHART_A, CHART_A))
    _exec(db, "DELETE FROM kala_obstruction WHERE chart_id = %s", (CHART_A,))
    _exec(db, "INSERT INTO kala_obstruction (chart_id, convergence_id) VALUES (%s, 4)", (CHART_A,))
    _exec(db, "DELETE FROM phala_anchors WHERE chart_id = %s", (CHART_A,))
    _exec(db, "INSERT INTO phala_anchors (chart_id, convergence_id) VALUES (%s, 4), (%s, 5)", (CHART_A, CHART_A))
    for t in ("phala_pramana", "phala_sodhana", "phala_suddha_sodhana"):
        _exec(db, f"DELETE FROM {t} WHERE chart_id = %s", (CHART_A,))
        _exec(db, f"INSERT INTO {t} (chart_id, anchor_id) SELECT chart_id, anchor_id FROM phala_anchors WHERE chart_id = %s", (CHART_A,))
    _exec(db, "DELETE FROM phala_sankrama WHERE chart_id = %s", (CHART_A,))
    _exec(db, "INSERT INTO phala_sankrama (chart_id, source_anchor_id) SELECT chart_id, anchor_id FROM phala_anchors WHERE chart_id = %s", (CHART_A,))
    assert all(v[1] == 0 for v in _detector(db)[0].values()), _detector(db)[0]


# -- detector ---------------------------------------------------------------------------

def test_detector_always_returns_seven_rows_even_when_every_child_table_is_empty(db):
    _make_fixture(db)
    _apply(db, _REAL)
    s, by_chart, n = _detector(db)
    assert n == 7 and sorted(s) == sorted(CONS)
    assert all(v == (0, 0, 0) for v in s.values()), "empty children read 0 references, so a zero orphan count is visibly vacuous"
    assert by_chart == []


def test_detector_does_not_flag_a_parent_that_exists_on_another_chart(db):
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    _exec(db, "UPDATE kala_obstruction SET chart_id = %s WHERE convergence_id = 3", (CHART_A,))
    assert _detector(db)[0]["kala_obstruction_convergence_id_fkey"][1] == 0


def test_detector_python_runner_exits_zero_with_orphans_and_reports_them(db, pg_cluster, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location("cross_asset_reference_orphans", _DET_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    _exec(db, "DELETE FROM kala_convergence WHERE chart_id = %s", (CHART_A,))
    dsn = f"host={pg_cluster['sock']} port={pg_cluster['port']} user=postgres dbname={db().info.dbname}"
    monkeypatch.setenv("DATABASE_URL", dsn)
    assert mod.main([]) == 0, "orphans must never change the exit code (reported, never build-blocking)"
    with pg_cluster["psycopg"].connect(dsn) as conn:
        res = mod.run(conn)
        assert res["orphan_rows_total"] == 6 and res["vacuous_references"] == []
    monkeypatch.delenv("DATABASE_URL")
    assert mod.main([]) == 2


# -- idempotency and guards -------------------------------------------------------------

def test_idempotent_second_run_changes_nothing(db):
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    snap = (_fk_defs(db), _data_digest(db), _structure(db))
    notices: list[str] = []
    _apply(db, _REAL, notices)
    assert sum("is already absent" in n for n in notices) == 7 and sum("already present on" in n for n in notices) == 5
    assert snap == (_fk_defs(db), _data_digest(db), _structure(db))


def test_partial_state_drops_and_adds_only_the_remaining(db):
    _make_fixture(db)
    _exec(db, "ALTER TABLE phala_pramana DROP CONSTRAINT phala_pramana_anchor_id_fkey; "
              "ALTER TABLE phala_sodhana DROP CONSTRAINT phala_sodhana_anchor_id_fkey; "
              "ALTER TABLE phala_anchors ADD CONSTRAINT phala_anchors_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE")
    notices: list[str] = []
    _apply(db, _REAL, notices)
    assert not (set(CONS) & set(_fk_defs(db)))
    assert sum("is already absent" in n for n in notices) == 2 and sum("already present on" in n for n in notices) == 1
    assert {c for c, _ in CHART_LINKS} <= set(_fk_defs(db))


@pytest.mark.parametrize("con", CONS)
def test_guard_refuses_a_constraint_that_is_not_the_expected_definition_and_changes_nothing(db, con):
    _make_fixture(db)
    _, child, ccol, parent, pcol = next(r for r in REFS if r[0] == con)
    _exec(db, f"ALTER TABLE {child} DROP CONSTRAINT {con}; "
              f"ALTER TABLE {child} ADD CONSTRAINT {con} FOREIGN KEY ({ccol}) REFERENCES {parent}({pcol}) ON DELETE RESTRICT")
    before = _fk_defs(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert "1260" in str(ei.value) and "not the constraint this migration was written against" in str(ei.value), str(ei.value)
    assert _fk_defs(db) == before, "a refused migration must change nothing"


def test_guard_refuses_an_existing_chart_link_that_is_not_the_expected_definition(db):
    _make_fixture(db)
    _exec(db, "ALTER TABLE phala_sodhana ADD CONSTRAINT phala_sodhana_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES charts(id)")
    before = _fk_defs(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert "is not the expected chart link" in str(ei.value), str(ei.value)
    assert _fk_defs(db) == before


def _insert_row_with_missing_chart(connect, table):
    """A row in `table` whose chart_id has no charts row, built so every OTHER constraint (the anchor FK) is satisfied."""
    with connect() as c:
        c.execute("INSERT INTO charts VALUES (%s)", (CHART_A,))
        if table == "phala_anchors":
            c.execute("INSERT INTO phala_anchors (chart_id) VALUES (%s)", (CHART_B,))  # CHART_B has no charts row
        else:
            c.execute("INSERT INTO phala_anchors (chart_id) VALUES (%s)", (CHART_A,))
            aid = c.execute("SELECT anchor_id FROM phala_anchors").fetchone()[0]
            cols, vals = (("chart_id, source_anchor_id", "%s, %s") if table == "phala_sankrama" else ("chart_id, anchor_id", "%s, %s"))
            c.execute(f"INSERT INTO {table} ({cols}) VALUES ({vals})", (CHART_B, aid))
        c.commit()


@pytest.mark.parametrize("table", L4_FIVE)
def test_stop_when_a_l4_table_lacks_chart_id_or_it_is_nullable_or_holds_a_missing_chart(db, table):
    _make_fixture(db)
    _exec(db, f"ALTER TABLE {table} DROP COLUMN chart_id")
    before = _fk_defs(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert f"public.{table} has no chart_id column; cannot add the ownership link and will not invent a derivation" in str(ei.value), str(ei.value)
    assert _fk_defs(db) == before
    _make_fixture(db)
    _exec(db, f"ALTER TABLE {table} ALTER COLUMN chart_id DROP NOT NULL")
    before = _fk_defs(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert f"public.{table}.chart_id is nullable" in str(ei.value), str(ei.value)
    assert _fk_defs(db) == before
    _make_fixture(db)
    _insert_row_with_missing_chart(db, table)
    before = _fk_defs(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert f"public.{table} holds 1 row(s) whose chart_id has no charts row; report, do not backfill" in str(ei.value), str(ei.value)
    assert _fk_defs(db) == before


def test_guard_refuses_a_missing_table_and_a_missing_column(db):
    _make_fixture(db)
    _exec(db, "DROP TABLE phala_muhurta; DROP TABLE phala_sankrama")
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert "does not exist" in str(ei.value), str(ei.value)
    _make_fixture(db)
    _exec(db, "ALTER TABLE phala_sodhana DROP CONSTRAINT phala_sodhana_anchor_id_fkey; ALTER TABLE phala_sodhana RENAME COLUMN anchor_id TO anchor_x")
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert "column public.phala_sodhana.anchor_id does not exist" in str(ei.value), str(ei.value)


@pytest.mark.parametrize("asset", ACTIVE_ASSETS)
@pytest.mark.parametrize("state", ["running", "planned", "paused"])
def test_active_build_run_guard_refuses_and_changes_nothing(db, asset, state):
    _make_fixture(db)
    _exec(db, "INSERT INTO build_runs (state) VALUES (%s)", (state,))
    _exec(db, "INSERT INTO build_run_assets (run_id, asset_id) SELECT max(id), %s FROM build_runs", (asset,))
    before = _fk_defs(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert "active build run" in str(ei.value) and asset in str(ei.value), str(ei.value)
    assert _fk_defs(db) == before


def test_finished_runs_and_runs_of_other_assets_do_not_block(db):
    _make_fixture(db)
    for st, aid in (("completed", "ka_sangam"), ("failed", "ph_nimitta"), ("stopped", "ph_pramana"), ("running", "ga_vargas")):
        _exec(db, "INSERT INTO build_runs (state) VALUES (%s)", (st,))
        _exec(db, "INSERT INTO build_run_assets (run_id, asset_id) SELECT max(id), %s FROM build_runs", (aid,))
    _apply(db, _REAL)
    assert not (set(CONS) & set(_fk_defs(db)))


def test_search_path_without_public_does_not_break_the_definition_guard(db):
    _make_fixture(db)
    _apply(db, "SET LOCAL search_path = pg_catalog;\n" + _REAL)
    assert not (set(CONS) & set(_fk_defs(db))) and {c for c, _ in CHART_LINKS} <= set(_fk_defs(db))


def test_lock_timeout_fails_fast_when_a_target_table_is_locked(db):
    _make_fixture(db)
    blocker = db()
    blocker.execute("LOCK TABLE phala_anchors IN ACCESS EXCLUSIVE MODE")
    try:
        t0 = time.monotonic()
        victim = db(user="amjis_app", options="-c statement_timeout=20000")
        with pytest.raises(Exception) as ei:
            victim.execute(_REAL)
        elapsed = time.monotonic() - t0
        victim.rollback()
        victim.close()
    finally:
        blocker.rollback()
        blocker.close()
    assert "lock timeout" in str(ei.value).lower(), str(ei.value)
    assert elapsed < 15, f"did not fail fast ({elapsed:.1f}s)"
    assert set(CONS) <= set(_fk_defs(db)), "nothing was dropped"


# -- MUTATION proof ------------------------------------------------------------------------

def _scenario(db, sql: str) -> list[str]:
    """Violations of the contract when `sql` (a possibly mutated migration) is applied, as amjis_app, to a fresh seeded fixture."""
    v: list[str] = []
    _make_fixture(db)
    _seed(db)
    fks_before, data_before = _fk_defs(db), _data_digest(db)
    b_before = _chart_counts(db, CHART_B)
    try:
        _apply(db, sql)
    except Exception as exc:  # noqa: BLE001
        return [f"apply failed: {str(exc).splitlines()[0]}"]
    fks_after = _fk_defs(db)
    if set(CONS) & set(fks_after):
        v.append(f"constraints remain: {sorted(set(CONS) & set(fks_after))}")
    for c, _ in CHART_LINKS:
        if fks_after.get(c) != "FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE":
            v.append(f"chart link {c} missing or wrong")
    for name in OUT_OF_SCOPE:
        if fks_after.get(name) != fks_before.get(name):
            v.append(f"out-of-scope FK {name} changed")
    if _data_digest(db) != data_before:
        v.append("a data row changed")
    try:
        _exec(db, "DELETE FROM kala_convergence WHERE chart_id = %s", (CHART_A,))
        _exec(db, "DELETE FROM phala_anchors WHERE chart_id = %s", (CHART_A,))
        s, _, n = _detector(db)
        if n != 7:
            v.append(f"detector returns {n} rows")
        want = {"kala_darshana_convergence_id_fkey": (3, 2, 1), "kala_obstruction_convergence_id_fkey": (3, 2, 1),
                "phala_pramana_anchor_id_fkey": (4, 3, 1), "phala_sodhana_anchor_id_fkey": (4, 3, 1),
                "phala_suddha_sodhana_anchor_id_fkey": (4, 3, 1), "phala_sankrama_source_anchor_id_fkey": (4, 3, 1)}
        for ref, exp in want.items():
            if s.get(ref) != exp:
                v.append(f"detector {ref} = {s.get(ref)}, expected {exp}")
    except Exception as exc:  # noqa: BLE001
        v.append(f"detector/delete failed: {str(exc).splitlines()[0]}")
    _exec(db, "DELETE FROM charts WHERE id = %s", (CHART_A,))
    left = {t: n for t, n in _chart_counts(db, CHART_A).items() if n and t in CHART_DELETE_REACHES}
    if left:
        v.append(f"chart deletion left rows behind: {left}")
    if _chart_counts(db, CHART_B) != b_before:
        v.append("chart deletion touched another chart")
    return v


def _guard_scenario(db, sql: str) -> list[str]:
    _make_fixture(db)
    _exec(db, "ALTER TABLE phala_pramana DROP CONSTRAINT phala_pramana_anchor_id_fkey; ALTER TABLE phala_pramana ADD CONSTRAINT "
              "phala_pramana_anchor_id_fkey FOREIGN KEY (anchor_id) REFERENCES phala_anchors(anchor_id) ON DELETE RESTRICT")
    before = _fk_defs(db)
    try:
        _apply(db, sql)
        return ["accepted a constraint with an unexpected definition"]
    except Exception as exc:  # noqa: BLE001
        v = [] if "not the constraint this migration was written against" in str(exc) else [f"refused for another reason: {str(exc).splitlines()[0]}"]
    if _fk_defs(db) != before:
        v.append("a refused migration changed a constraint")
    return v


def _stop_scenario(db, sql: str) -> list[str]:
    """STOP rather than invent: a missing chart_id / nullable chart_id / orphan chart row must be refused BY ITS OWN GUARD with
    nothing changed (the later statements would also fail, so the message is what proves the guard is there)."""
    v: list[str] = []
    for label, setup, message in (
            ("no chart_id", lambda: _exec(db, "ALTER TABLE phala_sodhana DROP COLUMN chart_id"), "has no chart_id column"),
            ("nullable chart_id", lambda: _exec(db, "ALTER TABLE phala_pramana ALTER COLUMN chart_id DROP NOT NULL"), "chart_id is nullable"),
            ("missing chart", lambda: _insert_row_with_missing_chart(db, "phala_anchors"), "has no charts row; report, do not backfill")):
        _make_fixture(db)
        setup()
        before = _fk_defs(db)
        try:
            _apply(db, sql)
            v.append(f"{label}: applied")
        except Exception as exc:  # noqa: BLE001
            if message not in str(exc):
                v.append(f"{label}: refused, but not by its own guard: {str(exc).splitlines()[0]}")
        if _fk_defs(db) != before:
            v.append(f"{label}: changed constraints while refusing")
    return v


def _runs_scenario(db, sql: str) -> list[str]:
    _make_fixture(db)
    _exec(db, "INSERT INTO build_runs (state) VALUES ('running')")
    _exec(db, "INSERT INTO build_run_assets (run_id, asset_id) VALUES (1, 'ka_sangam')")
    before = _fk_defs(db)
    try:
        _apply(db, sql)
        return ["applied during an active run"]
    except Exception as exc:  # noqa: BLE001
        v = [] if "active build run" in str(exc) else [f"refused for another reason: {str(exc).splitlines()[0]}"]
    if _fk_defs(db) != before:
        v.append("changed constraints while refusing")
    return v


def _lock_scenario(db, sql: str) -> list[str]:
    _make_fixture(db)
    blocker = db()
    blocker.execute("LOCK TABLE phala_anchors IN ACCESS EXCLUSIVE MODE")
    try:
        victim = db(user="amjis_app", options="-c statement_timeout=8000")
        try:
            victim.execute(sql)
            return ["did not fail while a target table was locked"]
        except Exception as exc:  # noqa: BLE001
            return [] if "lock timeout" in str(exc).lower() else [f"failed for another reason (no lock_timeout): {str(exc).splitlines()[0]}"]
        finally:
            victim.rollback()
            victim.close()
    finally:
        blocker.rollback()
        blocker.close()


_EXTRA_DROP = "    EXECUTE 'ALTER TABLE public.kala_bhavishya DROP CONSTRAINT kala_bhavishya_convergence_id_fkey';\n"
_MUT_ANCHOR = "    -- Post-check: never trust a silent no-op."
_MUTANTS = {
    "list_missing_one_reference": (_REAL.replace("        'phala_sodhana_anchor_id_fkey|phala_sodhana|anchor_id|phala_anchors|anchor_id',\n", ""), "scenario"),
    "drop_pass_removed": (_REAL.replace("EXECUTE format('ALTER TABLE public.%I DROP CONSTRAINT %I', child, con);", "NULL;"), "scenario"),
    "chart_link_list_missing_one": (_REAL.replace("        'phala_pramana_chart_id_fkey|phala_pramana',\n", ""), "scenario"),
    "chart_links_not_added": (_REAL.replace("EXECUTE format('ALTER TABLE public.%I ADD CONSTRAINT %I FOREIGN KEY (chart_id) REFERENCES public.charts(id) ON DELETE CASCADE', child, con);", "NULL;"), "scenario"),
    "chart_link_without_cascade": (_REAL.replace("FOREIGN KEY (chart_id) REFERENCES public.charts(id) ON DELETE CASCADE', child, con);", "FOREIGN KEY (chart_id) REFERENCES public.charts(id)', child, con);"), "scenario"),
    "chart_link_not_valid": (_REAL.replace("FOREIGN KEY (chart_id) REFERENCES public.charts(id) ON DELETE CASCADE', child, con);", "FOREIGN KEY (chart_id) REFERENCES public.charts(id) ON DELETE CASCADE NOT VALID', child, con);"), "scenario"),
    "guard_definition_check_neutered": (_REAL.replace("ELSIF cdef IS DISTINCT FROM expected THEN", "ELSIF false THEN"), "guard"),
    "guard_cascade_expected_def_widened": (_REAL.replace("ELSIF cdef IS DISTINCT FROM expected THEN", "ELSIF cdef IS NULL THEN"), "guard"),
    "stop_no_chart_id_neutered": (_REAL.replace("IF NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = child_oid AND attname = 'chart_id' AND NOT attisdropped) THEN", "IF false THEN"), "stop"),
    "stop_nullable_neutered": (_REAL.replace("AND NOT attisdropped AND attnotnull) THEN", "AND NOT attisdropped) THEN"), "stop"),
    "stop_orphan_chart_row_neutered": (_REAL.replace("IF bad > 0 THEN", "IF false THEN"), "stop"),
    "active_runs_guard_neutered": (_REAL.replace("IF n_active > 0 THEN", "IF false THEN"), "runs"),
    "lock_timeout_removed": (_REAL.replace("SET LOCAL lock_timeout = '5s';", "", 1), "lock"),
    "lock_timeout_session_wide": (_REAL.replace("SET LOCAL lock_timeout = '5s';", "SET lock_timeout = '0';", 1), "lock"),
    "extra_drop_caught_by_post_check": (_REAL.replace(_MUT_ANCHOR, _EXTRA_DROP + _MUT_ANCHOR), "scenario"),
    "extra_drop_with_post_check_neutered": (
        _REAL.replace(_MUT_ANCHOR, _EXTRA_DROP + _MUT_ANCHOR).replace("IF fk_after <> fk_before - dropped + added THEN", "IF false THEN"), "scenario"),
}


def test_mutants_are_real_mutations_of_the_real_file():
    for name, (sql, _) in _MUTANTS.items():
        assert sql != _REAL, f"mutant {name} did not change the file (the mutation pattern is stale)"


def test_the_real_file_produces_no_violations(db):
    assert _scenario(db, _REAL) == []
    assert _guard_scenario(db, _REAL) == []
    assert _stop_scenario(db, _REAL) == []
    assert _runs_scenario(db, _REAL) == []
    assert _lock_scenario(db, _REAL) == []


@pytest.mark.parametrize("name", sorted(_MUTANTS))
def test_every_mutant_is_caught(db, name):
    sql, kind = _MUTANTS[name]
    v = {"scenario": _scenario, "guard": _guard_scenario, "stop": _stop_scenario, "runs": _runs_scenario, "lock": _lock_scenario}[kind](db, sql)
    assert v, f"mutant {name} was NOT caught"
