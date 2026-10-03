"""
Migration 1260 (Suvarna, SS ruling N-99, Q-L4-03, widened to cross-ASSET): seven ON DELETE CASCADE foreign keys are
dropped (a rebuild of asset A must never silently delete asset B's rows) and a read-only DETECTOR (two views)
reports orphans per reference. HELD: own draft PR, merges only after S-L1 and only on SS's review.

Two tiers:
  * STATIC (always runs, DB-free): file shape, the ONE reference list, guards, header sections.
  * LIVE (needs PostgreSQL server binaries): applies the REAL migration file to a DISPOSABLE cluster this module
    creates with initdb in a temp dir (unix socket only, trust auth, removed at session end). It never connects to
    anything else. Skipped, loudly, when no initdb/pg_ctl is found; REQUIRE_PG_BINARIES=1 turns the skip into a
    failure. Set PG_BIN to pin a version (production is PostgreSQL 15).

The LIVE fixture reproduces the seven foreign keys with their production names and definitions (read from
production 2026-10-03 with pg_get_constraintdef), the production child-side indexes, and the SET NULL links that
must NOT be touched. What it proves: after apply a parent delete does NOT delete child rows and the detector
reports exactly those orphans; before apply (precondition) the same delete DID cascade; idempotent re-run;
guards (different constraint definition, missing table/column) refuse and change nothing; lock_timeout fails fast;
the views are SECURITY INVOKER and the migration grants nothing; the ka_sangam-style delete + re-insert flow.
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
OUT_OF_SCOPE = ["kala_bhavishya_convergence_id_fkey", "phala_anchors_bhavishya_id_fkey", "phala_muhurta_linked_anchor_id_fkey"]
CHART_A = "482012f1-710e-4a25-994a-93821f5871aa"
CHART_B = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"


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


def test_schema_only_no_data_no_ownership_of_the_transaction_lock_timeout_first():
    code = _code(_M1260)
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert not re.search(r"^\s*(BEGIN|COMMIT|ROLLBACK)\s*;", code, re.M)
    assert not re.search(r"\b(INSERT INTO|UPDATE\s+\w+\s+SET|DELETE FROM|TRUNCATE|GRANT|REVOKE|DROP (TABLE|INDEX|COLUMN|VIEW|SCHEMA))\b", code, re.I)
    assert "SET NULL" not in code and not re.search(r"ON DELETE (RESTRICT|NO ACTION)", code)
    assert code.count("DROP CONSTRAINT") == 1 and "DROP CONSTRAINT IF EXISTS" not in code, "drops are guarded one by one, never blanket IF EXISTS"
    assert "security_invoker = true" in code and code.count("CREATE OR REPLACE VIEW") == 2
    assert "ON DELETE CASCADE" in code, "the expected-definition guard names the cascade it removes"


def test_guards_and_post_checks_are_present():
    code = _code(_M1260)
    for needle in ("does not exist", "is not an ordinary table", "is not the constraint this migration was written against",
                   "pg_get_constraintdef", "is already absent", "still exists on public", "a cascading foreign key from",
                   "something else changed", "not security_invoker", "does not return exactly"):
        assert needle in code, needle


def test_header_states_the_design_choice_effects_trigger_scan_serving_effect_and_what_is_not_done():
    sql = _flat(_M1260)
    for needle in ("DESIGN CHOICE: DROP", "RESTRICT / NO ACTION would make the parent's delete-then-insert rebuild FAIL",
                   "DEFERRABLE INITIALLY DEFERRED does not help", "bigserial", "migration 363", "migration 680", "F-3",
                   "EFFECT ON THE EXISTING WRITERS", "ka_sangam", "ph_nimitta", "ORPHANS TODAY", "0 on all seven references",
                   "TRIGGER SCAN", "phala_anchors_identity_biu", "BLIND SPOTS", "SERVING EFFECT AT APPLY: none expected",
                   "nirmana_registry_receipt_invalidation does not fire", "SECURITY INVOKER", "NON-VACUITY", "LOCK-WAIT RISK",
                   "HELD", "AFTER S-L1", "on SS's review", "NOT DONE HERE", "VERIFICATION BY PRODUCTION STRUCTURE", "ROLLBACK",
                   "217 foreign keys", "vw_cross_asset_reference_orphans", "Q-L4-03", "suvarna_reader",
                   "SET NULL links", "chart_fact_identity", "charts-row-delete"):
        assert needle in sql, f"header no longer states: {needle}"
    for con in CONS:
        assert con in sql


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
            c.execute("CREATE ROLE viewer_all NOLOGIN")
            c.execute("CREATE ROLE viewer_part NOLOGIN")
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

    def connect(**kw):
        return psycopg.connect(host=sock, port=port, user="postgres", dbname=name, **kw)

    yield connect
    with psycopg.connect(host=sock, port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")


def _apply(connect, sql: str, notices: list[str] | None = None):
    """Run a migration the way migrate.ts does: one transaction around the whole file."""
    conn = connect()
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


# The production definitions (pg_get_constraintdef, 2026-10-03), production child-side indexes, and the SET NULL links.
_DDL = """
CREATE TABLE kala_convergence (convergence_id bigserial PRIMARY KEY, chart_id uuid);
CREATE INDEX idx_kala_convergence_chart_id ON kala_convergence (chart_id);
CREATE TABLE kala_bhavishya (id bigserial PRIMARY KEY, chart_id uuid NOT NULL, convergence_id bigint,
    CONSTRAINT kala_bhavishya_convergence_id_fkey FOREIGN KEY (convergence_id) REFERENCES kala_convergence(convergence_id) ON DELETE SET NULL);
CREATE TABLE kala_darshana (id bigserial PRIMARY KEY, chart_id uuid NOT NULL, convergence_id bigint,
    CONSTRAINT kala_darshana_convergence_id_fkey FOREIGN KEY (convergence_id) REFERENCES kala_convergence(convergence_id) ON DELETE CASCADE);
CREATE UNIQUE INDEX idx_kala_darshana_convergence ON kala_darshana (convergence_id) WHERE (convergence_id IS NOT NULL);
CREATE TABLE kala_obstruction (id bigserial PRIMARY KEY, chart_id uuid NOT NULL, convergence_id bigint,
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
_TABLES = ["kala_convergence", "kala_bhavishya", "kala_darshana", "kala_obstruction", "phala_anchors", "phala_pramana",
           "phala_sankrama", "phala_sodhana", "phala_suddha_sodhana", "phala_muhurta"]


def _make_fixture(connect, *, extra_ddl: str = ""):
    with connect() as c:
        c.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public")  # scenarios reuse one database
        c.execute(_DDL)
        if extra_ddl:
            c.execute(extra_ddl)
        c.commit()


def _seed(connect):
    """Two charts. Convergence 1,2 (chart A), 3 (chart B). Anchors a1 (conv 1), a2 (conv 2), a3 (conv 3), a4 (NULL conv).
    One child row per child table per anchor (sankrama also one NULL source), darshana/obstruction on conv 1..3."""
    with connect() as c:
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


def _data_digest(connect):
    return {t: _q(connect, f"SELECT md5(string_agg(to_jsonb(x)::text, '|' ORDER BY to_jsonb(x)::text)) FROM {t} x")[0][0] for t in _TABLES}


def _structure(connect):
    cols = _q(connect, "SELECT table_name, column_name, data_type, is_nullable FROM information_schema.columns "
                       "WHERE table_schema='public' AND table_name = ANY(%s) ORDER BY 1, ordinal_position", (_TABLES,))
    idx = _q(connect, "SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY 1, 2")
    return cols, idx


def _summary(connect):
    return {r[0]: (r[1], r[2], r[3]) for r in _q(connect, "SELECT reference_name, child_rows_with_reference, orphan_rows, "
                                                           "orphan_chart_count FROM vw_cross_asset_reference_orphans")}


# -- apply ---------------------------------------------------------------------------

def test_precondition_before_apply_a_parent_delete_cascades_through_all_levels(db):
    """The problem is real: this is what a ka_sangam DELETE does today."""
    _make_fixture(db)
    _seed(db)
    before = _counts(db)
    _exec(db, "DELETE FROM kala_convergence WHERE chart_id = %s", (CHART_A,))
    after = _counts(db)
    assert after["phala_anchors"] < before["phala_anchors"] and after["kala_darshana"] < before["kala_darshana"]
    assert after["phala_pramana"] < before["phala_pramana"] and after["phala_sodhana"] < before["phala_sodhana"]


def test_apply_drops_exactly_the_seven_and_changes_no_data_column_index_or_other_fk(db):
    _make_fixture(db)
    _seed(db)
    fks_before, data_before, struct_before = _fk_defs(db), _data_digest(db), _structure(db)
    _apply(db, _REAL)
    fks_after = _fk_defs(db)
    assert set(fks_before) - set(fks_after) == set(CONS)
    assert set(fks_after) == set(fks_before) - set(CONS), "nothing new, nothing else removed"
    for name in OUT_OF_SCOPE:
        assert fks_after[name] == fks_before[name], f"out-of-scope FK {name} changed"
    assert _data_digest(db) == data_before, "a data row changed"
    cols_b, idx_b = struct_before
    cols_a, idx_a = _structure(db)
    assert cols_a == cols_b, "a column changed"
    assert idx_a == idx_b, "an index changed (the child-side indexes stay)"


def test_after_apply_deleting_a_parent_deletes_no_child_and_the_detector_reports_the_orphans(db):
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    base = _summary(db)
    assert all(v[1] == 0 for v in base.values()), "no orphans before any delete"
    assert base["phala_anchors_convergence_id_fkey"][0] == 3 and base["kala_obstruction_convergence_id_fkey"][0] == 3
    assert base["phala_sankrama_source_anchor_id_fkey"][0] == 4, "NULL references are not counted as references"
    counts = _counts(db)
    _exec(db, "DELETE FROM kala_convergence WHERE chart_id = %s", (CHART_A,))  # convergence 1 and 2
    after = _counts(db)
    assert {k: v for k, v in after.items() if k != "kala_convergence"} == {k: v for k, v in counts.items() if k != "kala_convergence"} \
        | {"kala_bhavishya": counts["kala_bhavishya"]}, "no child row may be deleted by a parent delete"
    s = _summary(db)
    assert s["kala_darshana_convergence_id_fkey"] == (3, 2, 1)
    assert s["kala_obstruction_convergence_id_fkey"] == (3, 2, 1)
    assert s["phala_anchors_convergence_id_fkey"] == (3, 2, 1)
    # the SET NULL link (out of scope) still nulls its child: kala_bhavishya keeps its row, loses the pointer
    assert _q(db, "SELECT convergence_id FROM kala_bhavishya") == [(None,)]
    # now an anchor delete
    _exec(db, "DELETE FROM phala_anchors WHERE chart_id = %s", (CHART_A,))
    s = _summary(db)
    for ref in ("phala_pramana_anchor_id_fkey", "phala_sodhana_anchor_id_fkey", "phala_suddha_sodhana_anchor_id_fkey"):
        assert s[ref] == (4, 3, 1), (ref, s[ref])
    assert s["phala_sankrama_source_anchor_id_fkey"] == (4, 3, 1)
    assert _counts(db)["phala_pramana"] == 4 and _counts(db)["phala_sankrama"] == 5
    by_chart = _q(db, "SELECT reference_name, chart_id::text, child_rows_with_reference, orphan_rows "
                      "FROM vw_cross_asset_reference_orphans_by_chart WHERE reference_name='phala_pramana_anchor_id_fkey' ORDER BY 2")
    assert sorted(by_chart) == sorted([("phala_pramana_anchor_id_fkey", CHART_B, 1, 0), ("phala_pramana_anchor_id_fkey", CHART_A, 3, 3)])


def test_a_child_with_a_missing_parent_can_now_be_inserted_and_the_detector_sees_it(db):
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    _exec(db, "INSERT INTO phala_sodhana (chart_id, anchor_id) VALUES (%s, gen_random_uuid())", (CHART_A,))
    assert _summary(db)["phala_sodhana_anchor_id_fkey"] == (5, 1, 1)


def test_ka_sangam_style_delete_then_reinsert_then_children_rebuilt(db):
    """ka_sangam deletes the chart's kala_convergence and re-inserts (new bigserial ids); each child asset then clears
    and re-inserts its own rows. Order and effect after 1260."""
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    _exec(db, "DELETE FROM kala_convergence WHERE chart_id = %s", (CHART_A,))
    _exec(db, "INSERT INTO kala_convergence (chart_id) VALUES (%s), (%s)", (CHART_A, CHART_A))  # ids 4, 5
    s = _summary(db)
    assert s["phala_anchors_convergence_id_fkey"][1] == 2 and s["kala_darshana_convergence_id_fkey"][1] == 2
    # downstream rebuilds in wave order: each clears ITS OWN rows for the chart, then inserts against the new parents
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
    assert all(v[1] == 0 for v in _summary(db).values()), _summary(db)


# -- detector --------------------------------------------------------------------------

def test_summary_view_always_has_seven_rows_even_when_every_child_table_is_empty(db):
    _make_fixture(db)
    _apply(db, _REAL)
    rows = _q(db, "SELECT reference_name, child_rows_with_reference, orphan_rows, orphan_chart_count "
                  "FROM vw_cross_asset_reference_orphans ORDER BY 1")
    assert [r[0] for r in rows] == sorted(CONS)
    assert all(r[1:] == (0, 0, 0) for r in rows), "empty children read 0 references, so a zero orphan count is visibly vacuous"
    assert _q(db, "SELECT count(*) FROM vw_cross_asset_reference_orphans_by_chart")[0][0] == 0


def test_detector_does_not_flag_a_parent_that_exists_on_another_chart(db):
    """Documented scope: an orphan is a MISSING parent row; a parent on a different chart is not reported."""
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    _exec(db, "UPDATE kala_obstruction SET chart_id = %s WHERE convergence_id = 3", (CHART_A,))
    assert _summary(db)["kala_obstruction_convergence_id_fkey"][1] == 0


def test_views_are_security_invoker_and_the_migration_grants_nothing(db):
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    for v in ("vw_cross_asset_reference_orphans_by_chart", "vw_cross_asset_reference_orphans"):
        assert _q(db, "SELECT reloptions::text[] FROM pg_class WHERE oid = %s::regclass", (v,))[0][0] == ["security_invoker=true"]
        assert _q(db, "SELECT relacl FROM pg_class WHERE oid = %s::regclass", (v,))[0][0] is None, "no ACL entry was created"
    _exec(db, "GRANT USAGE ON SCHEMA public TO viewer_all, viewer_part")
    for t in _TABLES:
        _exec(db, f"GRANT SELECT ON {t} TO viewer_all")
        if t != "kala_obstruction":
            _exec(db, f"GRANT SELECT ON {t} TO viewer_part")

    def read_as(role: str) -> str:
        with db() as c:
            c.execute(f"SET ROLE {role}")
            try:
                c.execute("SELECT * FROM vw_cross_asset_reference_orphans").fetchall()
                return "ok"
            except Exception as exc:  # noqa: BLE001
                return str(exc).splitlines()[0]
            finally:
                c.rollback()

    # the migration granted nothing: table privileges alone do not let a role read the view
    assert "permission denied for view" in read_as("viewer_all")
    # a later explicit grant on the view is still limited by the CALLER's table privileges (security_invoker)
    _exec(db, "GRANT SELECT ON vw_cross_asset_reference_orphans, vw_cross_asset_reference_orphans_by_chart TO viewer_all, viewer_part")
    assert read_as("viewer_all") == "ok"
    assert "permission denied for table kala_obstruction" in read_as("viewer_part")


# -- idempotency and guards -------------------------------------------------------------

def test_idempotent_second_run_changes_nothing(db):
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    snap = (_fk_defs(db), _data_digest(db), _structure(db),
            _q(db, "SELECT pg_get_viewdef('vw_cross_asset_reference_orphans'::regclass), "
                   "pg_get_viewdef('vw_cross_asset_reference_orphans_by_chart'::regclass)"))
    notices: list[str] = []
    _apply(db, _REAL, notices)
    assert sum("is already absent" in n for n in notices) == 7
    assert snap == (_fk_defs(db), _data_digest(db), _structure(db),
                    _q(db, "SELECT pg_get_viewdef('vw_cross_asset_reference_orphans'::regclass), "
                           "pg_get_viewdef('vw_cross_asset_reference_orphans_by_chart'::regclass)"))


def test_partial_state_drops_only_the_remaining(db):
    _make_fixture(db)
    _exec(db, "ALTER TABLE phala_pramana DROP CONSTRAINT phala_pramana_anchor_id_fkey; "
              "ALTER TABLE phala_sodhana DROP CONSTRAINT phala_sodhana_anchor_id_fkey")
    notices: list[str] = []
    _apply(db, _REAL, notices)
    assert not (set(CONS) & set(_fk_defs(db)))
    assert sum("is already absent" in n for n in notices) == 2


@pytest.mark.parametrize("con", CONS)
def test_guard_refuses_a_constraint_that_is_not_the_expected_definition_and_changes_nothing(db, con):
    _make_fixture(db)
    child = next(r[1] for r in REFS if r[0] == con)
    ccol = next(r[2] for r in REFS if r[0] == con)
    parent = next(r[3] for r in REFS if r[0] == con)
    pcol = next(r[4] for r in REFS if r[0] == con)
    _exec(db, f"ALTER TABLE {child} DROP CONSTRAINT {con}; "
              f"ALTER TABLE {child} ADD CONSTRAINT {con} FOREIGN KEY ({ccol}) REFERENCES {parent}({pcol}) ON DELETE RESTRICT")
    before = _fk_defs(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert "1260" in str(ei.value) and "not the constraint this migration was written against" in str(ei.value), str(ei.value)
    assert _fk_defs(db) == before, "a refused migration must change nothing"
    assert _q(db, "SELECT to_regclass('vw_cross_asset_reference_orphans')")[0][0] is None


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


def test_search_path_without_public_does_not_break_the_definition_guard(db):
    _make_fixture(db)
    _apply(db, "SET LOCAL search_path = pg_catalog;\n" + _REAL)
    assert not (set(CONS) & set(_fk_defs(db)))


def test_lock_timeout_fails_fast_when_a_target_table_is_locked(db):
    _make_fixture(db)
    blocker = db()
    blocker.execute("LOCK TABLE phala_anchors IN ACCESS EXCLUSIVE MODE")
    try:
        t0 = time.monotonic()
        victim = db(options="-c statement_timeout=20000")
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
    """Violations of the contract when `sql` (a possibly mutated migration) is applied to a fresh seeded fixture."""
    v: list[str] = []
    _make_fixture(db)
    _seed(db)
    fks_before, data_before = _fk_defs(db), _data_digest(db)
    try:
        _apply(db, sql)
    except Exception as exc:  # noqa: BLE001
        return [f"apply failed: {str(exc).splitlines()[0]}"]
    fks_after = _fk_defs(db)
    if set(CONS) & set(fks_after):
        v.append(f"constraints remain: {sorted(set(CONS) & set(fks_after))}")
    for name in OUT_OF_SCOPE:
        if fks_after.get(name) != fks_before.get(name):
            v.append(f"out-of-scope FK {name} changed")
    if _data_digest(db) != data_before:
        v.append("a data row changed")
    try:
        s = _summary(db)
        if sorted(s) != sorted(CONS):
            v.append(f"summary view does not list the seven references: {sorted(s)}")
        _exec(db, "DELETE FROM kala_convergence WHERE chart_id = %s", (CHART_A,))
        _exec(db, "DELETE FROM phala_anchors WHERE chart_id = %s", (CHART_A,))
        s = _summary(db)
        want = {"kala_darshana_convergence_id_fkey": (3, 2, 1), "kala_obstruction_convergence_id_fkey": (3, 2, 1),
                "phala_pramana_anchor_id_fkey": (4, 3, 1), "phala_sodhana_anchor_id_fkey": (4, 3, 1),
                "phala_suddha_sodhana_anchor_id_fkey": (4, 3, 1), "phala_sankrama_source_anchor_id_fkey": (4, 3, 1)}
        for ref, exp in want.items():
            if s.get(ref) != exp:
                v.append(f"detector {ref} = {s.get(ref)}, expected {exp}")
    except Exception as exc:  # noqa: BLE001
        v.append(f"detector/delete failed: {str(exc).splitlines()[0]}")
    for view in ("vw_cross_asset_reference_orphans_by_chart", "vw_cross_asset_reference_orphans"):
        opts = _q(db, "SELECT reloptions::text[] FROM pg_class WHERE oid = to_regclass(%s)", (view,))
        if not opts or opts[0][0] != ["security_invoker=true"]:
            v.append(f"{view} is not security_invoker")
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


def _lock_scenario(db, sql: str) -> list[str]:
    _make_fixture(db)
    blocker = db()
    blocker.execute("LOCK TABLE phala_anchors IN ACCESS EXCLUSIVE MODE")
    try:
        victim = db(options="-c statement_timeout=8000")
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
_MUTANTS = {
    "list_missing_one_reference": (_REAL.replace("        'phala_sodhana_anchor_id_fkey|phala_sodhana|anchor_id|phala_anchors|anchor_id',\n", ""), "scenario"),
    "drop_pass_removed": (_REAL.replace("EXECUTE format('ALTER TABLE public.%I DROP CONSTRAINT %I', child, con);", "NULL;"), "scenario"),
    "security_invoker_removed": (_REAL.replace(" WITH (security_invoker = true)", ""), "scenario"),
    "detector_orphan_filter_inverted": (_REAL.replace("FILTER (WHERE p.%I IS NULL)", "FILTER (WHERE p.%I IS NOT NULL)"), "scenario"),
    "detector_counts_null_references": (_REAL.replace("WHERE c.%I IS NOT NULL GROUP BY c.chart_id", "GROUP BY c.chart_id"), "scenario"),
    "guard_definition_check_neutered": (_REAL.replace("ELSIF cdef IS DISTINCT FROM expected THEN", "ELSIF false THEN"), "guard"),
    "lock_timeout_removed": (_REAL.replace("SET LOCAL lock_timeout = '5s';", "", 1), "lock"),
    "lock_timeout_session_wide": (_REAL.replace("SET LOCAL lock_timeout = '5s';", "SET lock_timeout = '0';", 1), "lock"),
    "extra_drop_caught_by_post_check": (_REAL.replace("    -- The detector. Built from the same list", _EXTRA_DROP + "    -- The detector. Built from the same list"), "scenario"),
    "extra_drop_with_post_check_neutered": (
        _REAL.replace("    -- The detector. Built from the same list", _EXTRA_DROP + "    -- The detector. Built from the same list")
             .replace("IF fk_after <> fk_before - dropped THEN", "IF false THEN"), "scenario"),
    "cascade_expected_def_widened_to_any": (_REAL.replace("ELSIF cdef IS DISTINCT FROM expected THEN", "ELSIF cdef IS NULL THEN"), "guard"),
}


def test_mutants_are_real_mutations_of_the_real_file():
    for name, (sql, _) in _MUTANTS.items():
        assert sql != _REAL, f"mutant {name} did not change the file (the mutation pattern is stale)"


def test_the_real_file_produces_no_violations(db):
    assert _scenario(db, _REAL) == []
    assert _guard_scenario(db, _REAL) == []
    assert _lock_scenario(db, _REAL) == []


@pytest.mark.parametrize("name", sorted(_MUTANTS))
def test_every_mutant_is_caught(db, name):
    sql, kind = _MUTANTS[name]
    v = {"scenario": _scenario, "guard": _guard_scenario, "lock": _lock_scenario}[kind](db, sql)
    assert v, f"mutant {name} was NOT caught"
