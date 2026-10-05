"""
Migration 1299 (Suvarna S-L2 fast path, owner-surrogate ruling option (a)): bo_sangati's registered integrity_check_sql conjunct 3
("shared_signal_count != shared_factor_count") is replaced by the relation that actually holds: both counts >= 0 and
(shared_signal_count > 0) = (shared_factor_count > 0). The writer sets shared_factor_count to the number of DISTINCT constituent-fact roots
across the shared signals, which legitimately differs from the signal count.

Two tiers:
  * STATIC (always runs): OLD text rebuilt from migration 712 hashes to the live production md5; NEW text hashes to the md5 the file
    names and is the OLD text with exactly the one conjunct block replaced; guard shape; the writer still sets the two columns from
    two different expressions (the premise of this migration).
  * LIVE (needs PostgreSQL server binaries): applies the REAL on-disk migration to a DISPOSABLE cluster this module creates with
    initdb in a temp dir (own port, trust auth, removed at session end). Skipped, loudly, when no initdb/pg_ctl is found.

LIVE proves, with synthetic bodha_cdlm_cells rows and the FULL registry SQL: equal counts PASS; unequal counts with both > 0 PASS
(and the OLD text FAILS on them: the defect); signal > 0 with factor = 0 FAILS; signal = 0 with factor > 0 FAILS (isolated term, since
conjunct 4 also catches it in the full text); negative counts FAIL; every OTHER conjunct still bites on a mutated fixture; the
UPDATE is guarded (foreign text untouched, NOTICE, no failure), idempotent (xmin unchanged), changes no other column, stales ONLY
bo_sangati's asset_freshness rows through the production trigger body, and a silent no-op is caught by the post-check.
It does NOT prove production state (read from production structure after deploy; Trap 103).
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
_M1299 = _MIG / "1299_bo_sangati_integrity_conjunct3_invariant.sql"
_M712 = _MIG / "712_bo_sangati_integrity_check.sql"
_WRITER = _REPO / "platform" / "python-sidecar" / "pipeline" / "orchestrator" / "writers" / "bo_sangati.py"

OLD_MD5 = "0fb89ae68f370d02bada11f492f662f7"
NEW_MD5 = "222188fd9a48644176f34311fd3ea5f6"
OLD_LEN, NEW_LEN = 2455, 2539

OLD_C3 = """  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_cells WHERE shared_signal_count != shared_factor_count
  )
"""
NEW_C3 = """  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_cells
    WHERE shared_signal_count < 0
       OR shared_factor_count < 0
       OR (shared_signal_count > 0) != (shared_factor_count > 0)
  )
"""
CANON = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"


def _md5(t: str) -> str:
    return hashlib.md5(t.encode()).hexdigest()


def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("--"))


def _ic(path: Path) -> str:
    return re.search(r"\$ic\$(.*?)\$ic\$", path.read_text(), re.S).group(1)


OLD_TEXT = _ic(_M712)
NEW_TEXT = _ic(_M1299)


# -- STATIC tier --------------------------------------------------------------------------------------------------------

def test_static_old_text_is_the_live_production_text():
    assert _md5(OLD_TEXT) == OLD_MD5 and len(OLD_TEXT) == OLD_LEN


def test_static_new_text_has_the_named_md5_and_length():
    assert _md5(NEW_TEXT) == NEW_MD5 and len(NEW_TEXT) == NEW_LEN


def test_static_new_text_is_the_old_text_with_exactly_conjunct_3_replaced():
    assert OLD_TEXT.count(OLD_C3) == 1
    assert NEW_TEXT == OLD_TEXT.replace(OLD_C3, NEW_C3)
    assert "shared_signal_count != shared_factor_count" not in NEW_TEXT


def test_static_one_guarded_update_of_integrity_check_sql_only_lock_timeout_first():
    code = _code(_M1299)
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert code.count("UPDATE asset_registry") == 1
    assert f"AND md5(integrity_check_sql) = '{OLD_MD5}';" in code
    assert "WHERE asset_id = 'bo_sangati'" in code
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code)
    assert not re.search(r"^\s*(CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|INSERT|DELETE)\b", code, re.I | re.M)


def test_static_the_writer_sets_the_two_counts_from_two_different_expressions():
    w = _WRITER.read_text()
    assert '"shared_signal_count": len(shared_ids)' in w
    assert '"shared_factor_count": len(shared_root_groups)' in w


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


@pytest.fixture(scope="module")
def pg_cluster():
    psycopg = pytest.importorskip("psycopg")
    binp = _find_pg_bin()
    if binp is None:
        if os.environ.get("REQUIRE_PG_BINARIES") == "1":
            pytest.fail("no PostgreSQL server binaries and REQUIRE_PG_BINARIES=1")
        pytest.skip("no PostgreSQL server binaries (initdb/pg_ctl) found; set PG_BIN")
    root = Path(tempfile.mkdtemp(prefix="m1299pg"))
    data = root / "data"
    sockdir = Path(tempfile.mkdtemp(prefix="m99", dir="/tmp"))
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([str(binp / "initdb"), "-D", str(data), "-U", "postgres", "-A", "trust", "-E", "UTF8", "--no-sync"],
                   check=True, capture_output=True)
    opts = f"-p {port} -c listen_addresses='' -c unix_socket_directories={sockdir} -c fsync=off"
    subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-o", opts, "-w", "-l", str(root / "log"), "start"],
                   check=True, capture_output=True)
    try:
        yield {"port": port, "sock": str(sockdir), "psycopg": psycopg}
    finally:
        subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(sockdir, ignore_errors=True)


_n = 0


@pytest.fixture()
def db(pg_cluster):
    global _n
    _n += 1
    name = f"t{_n}"
    psycopg, port, sock = pg_cluster["psycopg"], pg_cluster["port"], pg_cluster["sock"]
    with psycopg.connect(host=sock, port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"CREATE DATABASE {name}")

    def connect():
        return psycopg.connect(host=sock, port=port, user="postgres", dbname=name)

    yield connect
    with psycopg.connect(host=sock, port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")


# bodha_cdlm_cells / bodha_convergence: only the columns the check reads, with the production types and NOT NULLs for the two counts.
_FIXTURE_DDL = """
CREATE TABLE asset_registry (
    asset_id text PRIMARY KEY, layer text NOT NULL, depends_on text[], is_active boolean NOT NULL DEFAULT true,
    target_table text, count_sql text, target_floor integer, size_sql text, volume_explanation text,
    natural_key_partition text, health_probe text, integrity_check_sql text, asset_kind text, asset_type text,
    scope text, has_writer boolean);
CREATE TABLE bodha_cdlm_cells (
    cell_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid NOT NULL, ayanamsha_id text NOT NULL,
    domain_row text NOT NULL, domain_col text NOT NULL,
    shared_signal_count integer NOT NULL, shared_factor_count integer NOT NULL,
    net_linkage_strength numeric NOT NULL, computed_linkage_strength numeric NOT NULL,
    shared_signal_ids_array uuid[], top_k_rank_in_snapshot integer, domain_relationship_class text);
CREATE TABLE bodha_convergence (
    chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, domain text NOT NULL,
    convergence_count integer NOT NULL, top_signal_ids_array uuid[]);
CREATE TABLE asset_freshness (
    asset_id text NOT NULL, chart_id uuid NOT NULL, freshness_state text NOT NULL,
    reasons jsonb NOT NULL DEFAULT '[]'::jsonb, observed_at timestamptz NOT NULL DEFAULT '2026-10-01T00:00:00Z',
    PRIMARY KEY (asset_id, chart_id));
CREATE OR REPLACE FUNCTION nirmana_invalidate_registry_receipts() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  UPDATE asset_freshness SET freshness_state = 'stale',
         reasons = CASE WHEN reasons ? 'registry_changed' THEN reasons ELSE reasons || '["registry_changed"]'::jsonb END,
         observed_at = now()
   WHERE asset_id = NEW.asset_id;
  RETURN NEW;
END; $$;
CREATE TRIGGER nirmana_registry_receipt_invalidation
AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind, asset_type,
                scope, has_writer, is_active, target_table ON asset_registry
FOR EACH ROW WHEN (OLD IS DISTINCT FROM NEW) EXECUTE FUNCTION nirmana_invalidate_registry_receipts();
"""

_PAIRS = [("career", "wealth"), ("education", "health"), ("family", "general"), ("progeny", "travel"),
          ("relationship", "residence"), ("character", "spirituality")]


def _cell(c, i: int, sig: int, fac: int, *, chart: str = CANON, strength: int = 3000):
    """One valid cell: ranks 1..N (i is the 1-based rank), strengths non-increasing, class matching the ladder."""
    a, b = _PAIRS[i - 1]
    ids = "{" + ",".join("00000000-0000-4000-8000-%012d" % (i * 100 + k) for k in range(sig)) + "}"
    c.execute("INSERT INTO bodha_cdlm_cells (chart_id, ayanamsha_id, domain_row, domain_col, shared_signal_count, "
              "shared_factor_count, net_linkage_strength, computed_linkage_strength, shared_signal_ids_array, "
              "top_k_rank_in_snapshot, domain_relationship_class) VALUES (%s,'lahiri',%s,%s,%s,%s,%s,%s,%s::uuid[],%s,'positive_strong')",
              (chart, a, b, sig, fac, strength, strength - i, ids if sig else "{}", i))


def _setup(connect, cells: list[tuple[int, int]] | None = None, text: str = OLD_TEXT, with_row: bool = True):
    with connect() as c:
        c.execute(_FIXTURE_DDL)
        if with_row:
            c.execute("INSERT INTO asset_registry (asset_id, layer, integrity_check_sql, target_table, scope, has_writer) "
                      "VALUES ('bo_sangati','bodha',%s,'bodha_cdlm_cells','per_chart',true)", (text,))
            c.execute("INSERT INTO asset_registry (asset_id, layer, integrity_check_sql) VALUES ('bo_other','bodha','SELECT true')")
            c.execute("INSERT INTO asset_freshness (asset_id, chart_id, freshness_state) VALUES "
                      "('bo_sangati', %s, 'fresh'), ('bo_sangati', %s, 'fresh'), ('bo_other', %s, 'fresh')", (CANON, OTHER, CANON))
        for i, (s, f) in enumerate(cells or [], start=1):
            _cell(c, i, s, f)
        c.commit()


def _apply(connect, notices: list[str] | None = None):
    conn = connect()
    if notices is not None:
        conn.add_notice_handler(lambda d: notices.append(d.message_primary))
    try:
        conn.execute(_M1299.read_text())
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _q(connect, sql, params=None):
    with connect() as c:
        return c.execute(sql, params).fetchall()


def _check(connect, text: str) -> bool:
    return _q(connect, text)[0][0]


def _txt(connect) -> str:
    return _q(connect, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bo_sangati'")[0][0]


_EQ = [(1, 1), (2, 2), (3, 3)]
_UNEQ = [(1, 1), (2, 5), (3, 2), (4, 9)]          # unequal in both directions, all > 0: the writer's real outcome
_TERM_ONLY = ("SELECT NOT EXISTS (SELECT 1 FROM bodha_cdlm_cells WHERE shared_signal_count < 0 OR shared_factor_count < 0 "
              "OR (shared_signal_count > 0) != (shared_factor_count > 0))")


def test_live_fixture_sanity_old_text_passes_on_equal_counts_and_on_empty_tables(db):
    _setup(db, _EQ)
    assert _check(db, OLD_TEXT) is True
    assert _check(db, NEW_TEXT) is True
    with db() as c:
        c.execute("DELETE FROM bodha_cdlm_cells")
        c.commit()
    assert _check(db, OLD_TEXT) is True and _check(db, NEW_TEXT) is True


def test_live_equal_counts_pass(db):
    _setup(db, _EQ)
    assert _check(db, NEW_TEXT) is True


def test_live_unequal_counts_with_both_positive_pass_and_the_old_text_fails_on_them(db):
    _setup(db, _UNEQ)
    assert _check(db, OLD_TEXT) is False, "the defect: the old conjunct 3 rejects a correct build"
    assert _check(db, NEW_TEXT) is True


def test_live_signal_positive_with_zero_factors_fails(db):
    _setup(db, [(1, 1), (2, 0), (3, 3)])
    assert _check(db, NEW_TEXT) is False
    assert _check(db, _TERM_ONLY) is False


def test_live_zero_signals_with_positive_factors_fails_in_the_term_and_in_the_full_text(db):
    _setup(db, [(1, 1), (0, 4), (3, 3)])
    assert _check(db, _TERM_ONLY) is False          # conjunct 3 alone catches it
    assert _check(db, NEW_TEXT) is False            # (conjunct 4 and 5 also do)


@pytest.mark.parametrize("sig,fac", [(-1, 0), (0, -1), (2, -1), (-2, 3)])
def test_live_negative_counts_fail(db, sig, fac):
    _setup(db, [(1, 1), (sig, fac)])
    assert _check(db, _TERM_ONLY) is False
    assert _check(db, NEW_TEXT) is False


def test_live_all_zero_cell_is_left_to_conjunct_4(db):
    """(0,0) satisfies the new term (no shared roots exactly when no shared signals) but never a stored cell: conjunct 4 still bites."""
    _setup(db, [(1, 1), (0, 0)])
    assert _check(db, _TERM_ONLY) is True
    assert _check(db, NEW_TEXT) is False


def test_live_every_other_conjunct_still_bites_on_a_mutated_valid_fixture(db):
    _setup(db, _UNEQ)
    assert _check(db, NEW_TEXT) is True
    mutants = {
        "c1_order": "UPDATE bodha_cdlm_cells SET domain_row='wealth', domain_col='career' WHERE top_k_rank_in_snapshot=1",
        "c2_vocab": "UPDATE bodha_cdlm_cells SET domain_col='zzz' WHERE top_k_rank_in_snapshot=1",
        "c5_array": "UPDATE bodha_cdlm_cells SET shared_signal_ids_array='{}' WHERE top_k_rank_in_snapshot=2",
        "c6_class": "UPDATE bodha_cdlm_cells SET domain_relationship_class='inverse' WHERE top_k_rank_in_snapshot=1",
        "c7_rank": "UPDATE bodha_cdlm_cells SET top_k_rank_in_snapshot=7 WHERE top_k_rank_in_snapshot=4",
        "c8_monotone": "UPDATE bodha_cdlm_cells SET computed_linkage_strength=0 WHERE top_k_rank_in_snapshot=1",
        "c9_conv_vocab": "INSERT INTO bodha_convergence VALUES ('%s','lahiri','zzz',1,'{}')" % CANON,
        "c10_conv_count": "INSERT INTO bodha_convergence VALUES ('%s','lahiri','career',0,'{}')" % CANON,
        "c11_conv_top5": "INSERT INTO bodha_convergence VALUES ('%s','lahiri','career',6,'{%s}')" % (
            CANON, ",".join("00000000-0000-4000-8000-0000000000%02d" % k for k in range(6))),
        "c12_conv_dup": "INSERT INTO bodha_convergence VALUES ('%s','lahiri','career',1,'{}'),('%s','lahiri','career',1,'{}')" % (CANON, CANON),
    }
    for name, sql in mutants.items():
        with db() as c:
            c.execute("SAVEPOINT m")
            c.execute(sql)
            assert c.execute(NEW_TEXT).fetchone()[0] is False, f"mutant {name} was not caught"
            c.execute("ROLLBACK TO SAVEPOINT m")
            assert c.execute(NEW_TEXT).fetchone()[0] is True, f"fixture not restored after {name}"


def test_live_apply_installs_the_new_text_and_the_installed_text_judges_like_the_file(db):
    _setup(db, _UNEQ)
    assert _check(db, _txt(db)) is False
    _apply(db)
    assert _md5(_txt(db)) == NEW_MD5 and len(_txt(db)) == NEW_LEN
    assert _check(db, _txt(db)) is True


def test_live_apply_touches_only_integrity_check_sql_and_stales_only_bo_sangati(db):
    _setup(db, _UNEQ)
    before = _q(db, "SELECT to_jsonb(r) - 'integrity_check_sql' FROM asset_registry r ORDER BY asset_id")
    _apply(db)
    assert _q(db, "SELECT to_jsonb(r) - 'integrity_check_sql' FROM asset_registry r ORDER BY asset_id") == before
    assert _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bo_other'")[0][0] == "SELECT true"
    fr = {(a, c): (s, r) for a, c, s, r in _q(db, "SELECT asset_id, chart_id::text, freshness_state, reasons::text FROM asset_freshness")}
    assert fr[("bo_sangati", CANON)][0] == "stale" and "registry_changed" in fr[("bo_sangati", CANON)][1]
    assert fr[("bo_sangati", OTHER)][0] == "stale"
    assert fr[("bo_other", CANON)] == ("fresh", "[]")


def test_live_idempotent_second_run_rewrites_nothing_and_does_not_fire_the_trigger(db):
    _setup(db, _UNEQ)
    _apply(db)
    x1 = _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id='bo_sangati'")
    with db() as c:
        c.execute("UPDATE asset_freshness SET freshness_state='fresh', reasons='[]' WHERE asset_id='bo_sangati'")
        c.commit()
    notes: list[str] = []
    _apply(db, notes)
    assert _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id='bo_sangati'") == x1
    assert any("already carries the invariant conjunct 3" in n for n in notes)
    assert {s for (s,) in _q(db, "SELECT freshness_state FROM asset_freshness WHERE asset_id='bo_sangati'")} == {"fresh"}


def test_live_foreign_text_is_left_untouched_notice_and_no_failure(db):
    foreign = OLD_TEXT + "\n-- edited by hand\n"
    _setup(db, text=foreign)
    notes: list[str] = []
    _apply(db, notes)
    assert _txt(db) == foreign
    assert any("not the text this migration was written against" in n and "NO-OP" in n for n in notes)
    assert {s for (s,) in _q(db, "SELECT freshness_state FROM asset_freshness")} == {"fresh"}


def test_live_empty_registry_is_a_noop(db):
    _setup(db, with_row=False)
    notes: list[str] = []
    _apply(db, notes)
    assert any("no bo_sangati registry row" in n for n in notes)


def test_live_post_check_catches_a_silent_noop(db):
    _setup(db)
    with db() as c:
        c.execute("CREATE RULE swallow AS ON UPDATE TO asset_registry WHERE OLD.asset_id = 'bo_sangati' DO INSTEAD NOTHING")
        c.commit()
    with pytest.raises(Exception) as ei:
        _apply(db)
    assert "update did not take" in str(ei.value)
    assert _txt(db) == OLD_TEXT
