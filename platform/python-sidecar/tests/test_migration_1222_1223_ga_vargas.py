"""
Migrations 1222 (ga_vargas integrity clause (e), non-vacuity) and 1223 (ga_vargas output-digest spec,
seven-column key). HELD: they merge only in the S-L1 window W1 together with 1221 and 1226 (one deploy,
numeric apply order 1221, 1222, 1223, 1226).

Two tiers:
  * STATIC (always runs, DB-free): file shape, guards, header sections, the md5 of the check text, the
    spec sha recomputed with the repository's own `canonical_digest`, the new spec = the live (883) spec with
    `fact_subject` appended to key_columns and nothing else, and the real `compute_output_digest` SQL
    generation (ORDER BY the seven key columns, key preflight on all seven).
  * LIVE (needs PostgreSQL server binaries): applies the REAL on-disk migration files to a DISPOSABLE cluster
    this module creates with initdb in a temp dir (own port, trust auth, removed at session end). It never
    connects to anything else. Skipped, loudly, when no `initdb`/`pg_ctl` is found (looked up via $PG_BIN, PATH,
    homebrew, /usr/lib/postgresql/*/bin). Set $PG_BIN to pin a version (production is PostgreSQL 15).

The LIVE fixture carries the REAL trigger function body and trigger definition of
`nirmana_registry_receipt_invalidation` (read from production 2026-10-02 as suvarna_reader with
pg_get_functiondef / pg_get_triggerdef) and the live column set, constraints and indexes of
asset_registry, asset_freshness and asset_output_digest_specs, so what is proved is the serving effect the
migration headers state: ga_vargas freshness goes stale on EVERY chart for 1222, and nothing else moves.
It does NOT prove production state (that is read from production structure after deploy; Trap 103).
"""
from __future__ import annotations

import glob
import hashlib
import itertools
import json
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
_M1222 = _MIG / "1222_nirmana_l1_ga_vargas_integrity_nonvacuity.sql"
_M1223 = _MIG / "1223_nirmana_l1_ga_vargas_output_digest_spec_seven_column_key.sql"
_M883 = _MIG / "883_nirmana_l1_ga_vargas_output_digest_spec.sql"
_M884 = _MIG / "884_nirmana_l1_ga_vargas_integrity_check_scope.sql"

CANON = "482012f1-710e-4a25-994a-93821f5871aa"
OLD_CHECK_MD5 = "255af7c5194553e19f7009c1e8774d8a"
NEW_CHECK_MD5 = "d2f897535c8c6237f464c81f11624701"
OLD_SPEC_SHA = "5f332a4889cb465f317fe7f2315bd59a7aee9d53df58e283b436040403a9bb51"
NEW_SPEC_SHA = "9c278d217f045f140596b452aa3c929bc83632bf96f0a266a2532dfe2ee60862"
SIX = ["chart_id", "graha", "ayanamsha_id", "varga", "fact_category", "fact_key"]
SEVEN = SIX + ["fact_subject"]


# ── helpers ──────────────────────────────────────────────────────────────────

def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("--"))


def _flat(path: Path) -> str:
    """Header comments with the `-- ` prefixes removed and whitespace collapsed (needles span wrapped lines)."""
    return re.sub(r"\s+", " ", re.sub(r"^--", " ", path.read_text(), flags=re.M))


def _old_check() -> str:
    return re.search(r"\$SQL\$(.*?)\$SQL\$", _M884.read_text(), re.S).group(1)


def _new_check() -> str:
    return re.search(r"\$ck\$(.*)\$ck\$", _M1222.read_text(), re.S).group(1)


def _old_spec() -> dict:
    return json.loads(re.search(r"'(\{\"version\".*?\})'::jsonb", _M883.read_text(), re.S).group(1))


def _new_spec() -> dict:
    return json.loads(re.search(r"'(\{\"version\".*?\})'::jsonb", _M1223.read_text(), re.S).group(1))


# ── STATIC tier ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("path", [_M1222, _M1223])
def test_files_do_not_own_the_transaction_and_start_with_lock_timeout(path):
    code = _code(path)
    sql = _flat(path)
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code), "migrate.ts owns the transaction"
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';"), code.strip()[:80]
    assert not re.search(r"^\s*(DROP|TRUNCATE|DELETE\s+FROM|REVOKE|GRANT|ALTER|CREATE)\b", code, re.I | re.M)
    for needle in ("SERVING EFFECT AT APPLY", "ORDERING", "HELD", "back to back", "1221", "1226",
                   "VERIFICATION BY PRODUCTION STRUCTURE", "IDEMPOTENT SHAPE", "ROLLBACK",
                   "suvarna_reader", "S-L1 window W1", "F-A2 ga_vargas rebuild",
                   "{ga_structural", "ga_dashas", "ga_yoga"):
        assert needle.lower() in sql.lower(), f"{path.name} header no longer states: {needle}"
    assert "$pre$" in sql and "$post$" in sql
    if path is _M1223:
        assert "71,476" in sql and "0 of" in sql, "the live NULL-key count belongs in the 1223 header"


def test_1222_serving_effect_names_the_live_trigger_and_every_chart():
    sql = _flat(_M1222)
    for needle in ("nirmana_registry_receipt_invalidation", "AFTER UPDATE OF depends_on, natural_key_partition, "
                   "health_probe, integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, "
                   "is_active, target_table", "old.* IS DISTINCT FROM new.*", "ON EVERY CHART",
                   "UNRESOLVED", "receipt_not_fresh"):
        assert needle in sql, needle


def test_1223_serving_effect_names_receipt_spec_retired_and_the_degraded_set():
    sql = _flat(_M1223)
    for needle in ("receipt_spec_retired", "served_generation.ts:200-206", ":265", "UNRESOLVED",
                   "{ga_structural, ga_vargas, ga_dashas,", "1221, 1222, 1223, 1226", "NEVER after", "24,392"):
        assert needle in sql, needle


def test_1222_check_text_is_unchanged_from_2858_and_adds_exactly_conjunct_e():
    new, old = _new_check(), _old_check()
    assert hashlib.md5(old.encode()).hexdigest() == OLD_CHECK_MD5
    assert hashlib.md5(new.encode()).hexdigest() == NEW_CHECK_MD5
    code = _code(_M1222)
    assert code.count(OLD_CHECK_MD5) == 2, "pre-check (accept) + UPDATE guard name the base md5"
    assert code.count(NEW_CHECK_MD5) == 2, "pre-check (already applied) + post-check name the target md5"
    assert "(e) NON-VACUITY" in new and "(e) NON-VACUITY" not in old
    assert "(f)" not in new and not re.search(r"<> *(12|96|60)\b", new), "no bare count pins in integrity_check_sql"
    assert new.rstrip().endswith("AS integrity_passed") and "< 9" in new
    for tag in ("(a) sign / sign_number", "(b) vargottama correctness", "(c) §N.5 D1 authority", "(d) identity range guard"):
        assert tag in new and tag in old


def test_1222_is_one_guarded_update_of_one_column_of_one_row():
    code = _code(_M1222)
    assert len(re.findall(r"\bUPDATE asset_registry\b", code)) == 1
    assert re.findall(r"\bSET\s+([a-z_]+)\s*=", code.split("$ck$")[0], re.I) == ["integrity_check_sql"]
    tail = code.split("$ck$")[-1]
    assert "WHERE asset_id = 'ga_vargas'" in tail and f"md5(integrity_check_sql) = '{OLD_CHECK_MD5}'" in tail


def test_1223_new_spec_is_the_883_spec_with_fact_subject_appended_and_nothing_else():
    from pipeline.orchestrator.provenance import canonical_digest
    old, new = _old_spec(), _new_spec()
    assert canonical_digest(old) == OLD_SPEC_SHA, "migration 883 literal reproduces the live sha"
    assert canonical_digest(new) == NEW_SPEC_SHA, "the 1223 literal reproduces the sha it carries"
    assert _M1223.read_text().count(NEW_SPEC_SHA) >= 4
    assert old["components"][0]["key_columns"] == SIX and new["components"][0]["key_columns"] == SEVEN
    derived = json.loads(json.dumps(old))
    derived["components"][0]["key_columns"].append("fact_subject")
    assert canonical_digest(derived) == NEW_SPEC_SHA, "new == old + fact_subject on key_columns, no other change"
    c = new["components"][0]
    assert "fact_subject" in c["value_columns"] and c["where_equals"] == {"chart_id": CANON}
    assert len(c["value_columns"]) == 26 and c["relation"] == "chart_divisionals" and len(new["components"]) == 1


def test_1223_spec_passes_the_servers_own_validator_and_orders_by_all_seven_columns():
    from pipeline.orchestrator import output_digest as od
    new = _new_spec()
    od._validate_spec("ga_vargas", new, NEW_SPEC_SHA)
    comp = new["components"][0]
    stmt = od._component_statement(comp)
    assert stmt.rstrip().endswith('ORDER BY ' + ", ".join(f'source."{c}"' for c in SEVEN))
    pre = od._component_key_preflight(comp)
    assert 'source."fact_subject" IS NULL' in pre


def test_1223_retires_before_it_inserts_and_uses_on_conflict_do_nothing():
    code = _code(_M1223)
    upd = code.index("UPDATE asset_output_digest_specs")
    ins = code.index("INSERT INTO asset_output_digest_specs")
    assert upd < ins, "the one-current partial unique index needs the retire first"
    assert "ON CONFLICT (asset_id, spec_sha256) DO NOTHING;" in code
    assert len(re.findall(r"INSERT INTO asset_output_digest_specs", code)) == 1
    assert len(re.findall(r"UPDATE asset_output_digest_specs", code)) == 1
    assert f"spec_sha256 = '{OLD_SPEC_SHA}'" in code.split("INSERT INTO")[0]


def test_numbers_and_names_follow_the_pattern_and_are_free_of_siblings():
    assert _M1222.name.startswith("1222_") and _M1223.name.startswith("1223_")
    assert len(list(_MIG.glob("1222_*.sql"))) == 1 and len(list(_MIG.glob("1223_*.sql"))) == 1


# ── LIVE tier: disposable PostgreSQL ─────────────────────────────────────────

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
    root = Path(tempfile.mkdtemp(prefix="m1222pg"))
    data = root / "data"
    # unix socket paths are length-limited (104 bytes on macOS): keep the socket directory short
    sockdir = root if len(str(root)) < 60 else Path(tempfile.mkdtemp(prefix="m22", dir="/tmp"))
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([str(binp / "initdb"), "-D", str(data), "-U", "postgres", "-A", "trust", "-E", "UTF8",
                    "--no-sync"], check=True, capture_output=True)
    opts = f"-p {port} -c listen_addresses=127.0.0.1 -c unix_socket_directories={sockdir} -c fsync=off"
    subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-o", opts, "-w", "-l", str(root / "log"), "start"],
                   check=True, capture_output=True)
    try:
        yield {"port": port, "psycopg": psycopg}
    finally:
        subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)
        if sockdir != root:
            shutil.rmtree(sockdir, ignore_errors=True)


_db_counter = 0


@pytest.fixture()
def db(pg_cluster):
    """A fresh database per test; yields a connect() factory (autocommit off)."""
    global _db_counter
    _db_counter += 1
    name = f"t{_db_counter}"
    psycopg, port = pg_cluster["psycopg"], pg_cluster["port"]
    with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"CREATE DATABASE {name}")

    def connect(**kw):
        return psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname=name, **kw)

    yield connect
    with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")


def _apply(connect, path: Path):
    """Run a migration file the way migrate.ts does: one transaction around the whole file."""
    conn = connect()
    try:
        conn.execute(path.read_text())
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


# The REAL trigger function body and trigger definition, read from production 2026-10-02 (suvarna_reader,
# pg_get_functiondef / pg_get_triggerdef). The registry columns named in the trigger exist in the fixture.
_TRIGGER_FN = """
CREATE OR REPLACE FUNCTION public.nirmana_invalidate_registry_receipts()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
  UPDATE asset_freshness
     SET freshness_state = 'stale',
         reasons = CASE
           WHEN reasons ? 'registry_changed' THEN reasons
           ELSE reasons || '["registry_changed"]'::jsonb
         END,
         observed_at = now()
   WHERE asset_id = NEW.asset_id;
  RETURN NEW;
END;
$function$
"""
_TRIGGER_DEF = ("CREATE TRIGGER nirmana_registry_receipt_invalidation AFTER UPDATE OF depends_on, "
                "natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind, asset_type, "
                "scope, has_writer, is_active, target_table ON public.asset_registry FOR EACH ROW WHEN "
                "((old.* IS DISTINCT FROM new.*)) EXECUTE FUNCTION nirmana_invalidate_registry_receipts()")

_DDL = """
CREATE TABLE asset_registry (
    asset_id text PRIMARY KEY,
    layer text NOT NULL,
    sort_order integer NOT NULL,
    english_name text NOT NULL,
    target_table text,
    target_floor integer,
    depends_on text[] DEFAULT ARRAY[]::text[],
    scope text NOT NULL DEFAULT 'per_chart' CHECK (scope IN ('global', 'per_chart')),
    is_active boolean DEFAULT true,
    asset_type text NOT NULL DEFAULT 'data',
    health_probe jsonb,
    integrity_check_sql text,
    asset_kind text NOT NULL DEFAULT 'data',
    has_writer boolean NOT NULL DEFAULT false,
    natural_key_partition text,
    meta jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE TABLE asset_freshness (
    asset_id text NOT NULL REFERENCES asset_registry(asset_id) ON DELETE CASCADE,
    chart_id uuid,
    scope_key text NOT NULL,
    partition_key text NOT NULL CHECK (btrim(partition_key) <> ''),
    freshness_state text NOT NULL CHECK (freshness_state IN ('fresh', 'stale', 'unknown')),
    reasons jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(reasons) = 'array'),
    receipt_version text NOT NULL,
    observed_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (asset_id, scope_key, partition_key)
);
CREATE TABLE asset_output_digest_specs (
    asset_id text NOT NULL REFERENCES asset_registry(asset_id) ON DELETE RESTRICT,
    spec_sha256 text NOT NULL CHECK (spec_sha256 ~ '^[a-f0-9]{64}$'),
    spec jsonb NOT NULL CHECK (jsonb_typeof(spec) = 'object'),
    reviewed_at timestamptz NOT NULL DEFAULT now(),
    retired_at timestamptz,
    PRIMARY KEY (asset_id, spec_sha256),
    CHECK (retired_at IS NULL OR retired_at >= reviewed_at)
);
CREATE UNIQUE INDEX asset_output_digest_specs_one_current ON asset_output_digest_specs (asset_id) WHERE retired_at IS NULL;
"""

# Live production `depends_on` (read 2026-10-02 via suvarna_reader) for the assets involved in 1226 + neighbours.
LIVE_BEFORE: dict[str, list[str]] = {
    "ga_positions": [],
    "bg_reference": [],
    "ga_sensitive": ["ga_positions", "bg_reference"],
    "ga_vargas": ["ga_positions"],
    "ga_dashas": ["ga_positions"],
    "ga_structural": ["ga_dashas", "ga_nakshatra", "ga_panchanga", "ga_positions", "ga_sensitive",
                      "ga_strength", "ga_vargas"],
    "ga_yoga": ["ga_structural", "ga_dashas"],
    "ga_nakshatra": [], "ga_panchanga": [], "ga_strength": [],
    "bo_laksana": ["ga_positions", "ga_vargas"],
    "bo_upaya": ["bo_laksana", "ga_structural", "ga_dashas"],
}
CHARTS = [CANON, "00000000-0000-4000-8000-0000000000a1", "00000000-0000-4000-8000-0000000000a2"]
STRUCTURAL_CHECK = "SELECT true AS integrity_passed  -- ga_structural base text (stand-in for 1221's guard)"

# What 1221 and 1226 do to this fixture, as stand-ins (the real files are other held PRs and are not in
# this tree): 1221 = md5-guarded UPDATE of ga_structural.integrity_check_sql; 1226 = append the four
# L1 edges. Both fire the same live trigger, so the combined stale set is exactly what the header states.
_STANDIN_1221 = f"""
SET LOCAL lock_timeout = '5s';
DO $$ BEGIN
  IF (SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id = 'ga_structural') IS DISTINCT FROM
     '{hashlib.md5(STRUCTURAL_CHECK.encode()).hexdigest()}' THEN RAISE EXCEPTION '1221-like guard tripped'; END IF; END $$;
UPDATE asset_registry SET integrity_check_sql = integrity_check_sql || E'\\n-- (a29) stand-in' WHERE asset_id = 'ga_structural';
"""
_STANDIN_1226 = """
SET LOCAL lock_timeout = '5s';
UPDATE asset_registry r
   SET depends_on = COALESCE(r.depends_on, '{}'::text[]) || n.deps
  FROM (SELECT e.asset_id, array_agg(e.dep ORDER BY e.dep) AS deps
          FROM (VALUES ('ga_dashas','ga_sensitive'),('ga_dashas','ga_vargas'),('ga_yoga','ga_vargas'),
                       ('ga_vargas','ga_sensitive')) e(asset_id, dep)
          JOIN asset_registry c ON c.asset_id = e.asset_id
         WHERE e.dep <> ALL (COALESCE(c.depends_on, '{}'::text[]))
         GROUP BY e.asset_id) n
 WHERE r.asset_id = n.asset_id;
"""


def _make_fixture(connect, *, check_text: str | None = None, with_spec: bool = True, spec_row: tuple | None = None):
    old_check = _old_check() if check_text is None else check_text
    with connect() as c:
        c.execute(_DDL)
        for i, (aid, deps) in enumerate(LIVE_BEFORE.items()):
            check = old_check if aid == "ga_vargas" else (STRUCTURAL_CHECK if aid == "ga_structural" else f"SELECT true -- {aid}")
            c.execute("INSERT INTO asset_registry (asset_id, layer, sort_order, english_name, depends_on, integrity_check_sql) "
                      "VALUES (%s, %s, %s, %s, %s, %s)", (aid, aid.split("_")[0], i, aid.upper(), deps, check))
        c.execute(_TRIGGER_FN)
        c.execute(_TRIGGER_DEF)
        for aid in LIVE_BEFORE:
            for k, chart in enumerate(CHARTS):
                c.execute("INSERT INTO asset_freshness (asset_id, chart_id, scope_key, partition_key, freshness_state, "
                          "receipt_version, observed_at) VALUES (%s, %s, %s, 'default', 'fresh', 'v1', '2026-10-01T00:00:00Z')",
                          (aid, chart, f"chart:{chart}"))
        if with_spec:
            if spec_row is None:
                c.execute("INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec, reviewed_at) "
                          "VALUES ('ga_vargas', %s, %s::jsonb, '2026-09-07T10:56:35Z')",
                          (OLD_SPEC_SHA, json.dumps(_old_spec())))
            else:
                c.execute("INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec, reviewed_at) "
                          "VALUES ('ga_vargas', %s, %s::jsonb, '2026-09-07T10:56:35Z')", spec_row)
            for aid in ("ga_dashas", "ga_positions"):
                c.execute("INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec) VALUES (%s, %s, %s::jsonb)",
                          (aid, hashlib.sha256(aid.encode()).hexdigest(), json.dumps({"version": "x", "for": aid})))
        c.commit()


def _freshness(connect):
    return _q(connect, "SELECT asset_id, chart_id::text, freshness_state, reasons::text, observed_at::text "
                       "FROM asset_freshness ORDER BY 1, 2")


def _registry_other_than_ga_vargas(connect):
    return _q(connect, "SELECT asset_id, to_jsonb(r)::text FROM asset_registry r WHERE asset_id <> 'ga_vargas' ORDER BY 1")


def _check_md5(connect, aid="ga_vargas"):
    return _q(connect, "SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id=%s", (aid,))[0][0]


def _specs(connect):
    return _q(connect, "SELECT asset_id, spec_sha256, spec::text, reviewed_at::text, retired_at::text, xmin::text "
                       "FROM asset_output_digest_specs ORDER BY asset_id, spec_sha256")


def test_fixture_old_check_is_the_live_base_text():
    assert hashlib.md5(_old_check().encode()).hexdigest() == OLD_CHECK_MD5


# ── 1222 ─────────────────────────────────────────────────────────────────────

def test_1222_applies_the_new_text_and_stales_exactly_ga_vargas_on_every_chart(db):
    _make_fixture(db)
    other_before = _registry_other_than_ga_vargas(db)
    fresh_before = {(a, c): (s, r, o) for a, c, s, r, o in _freshness(db)}
    _apply(db, _M1222)
    assert _check_md5(db) == NEW_CHECK_MD5
    assert _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ga_vargas'")[0][0] == _new_check()
    rows = _freshness(db)
    stale = {(a, c) for a, c, s, r, o in rows if s == "stale"}
    assert stale == {("ga_vargas", ch) for ch in CHARTS}, "ga_vargas stale on EVERY chart, nothing else"
    for a, c, s, r, o in rows:
        if a == "ga_vargas":
            assert "registry_changed" in r
        else:
            assert (s, r, o) == fresh_before[(a, c)], f"{a} freshness changed"
    assert _registry_other_than_ga_vargas(db) == other_before, "another registry row changed"
    row = _q(db, "SELECT to_jsonb(r) - 'integrity_check_sql' FROM asset_registry r WHERE asset_id='ga_vargas'")[0][0]
    assert row["depends_on"] == ["ga_positions"] and row["is_active"] is True, "only integrity_check_sql changed"


def test_1222_md5_guard_refuses_an_unexpected_text_and_changes_nothing(db):
    _make_fixture(db, check_text="SELECT false AS integrity_passed")
    fresh, reg = _freshness(db), _registry_other_than_ga_vargas(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _M1222)
    assert "1222" in str(ei.value) and "not the text this migration was written against" in str(ei.value), str(ei.value)
    assert _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ga_vargas'")[0][0] == "SELECT false AS integrity_passed"
    assert _freshness(db) == fresh and _registry_other_than_ga_vargas(db) == reg


def test_1222_refuses_a_missing_ga_vargas_row(db):
    _make_fixture(db, with_spec=False)
    _exec(db, "DELETE FROM asset_registry WHERE asset_id='ga_vargas'")
    with pytest.raises(Exception) as ei:
        _apply(db, _M1222)
    assert "expected exactly one ga_vargas registry row" in str(ei.value), str(ei.value)


def test_1222_is_idempotent_second_run_rewrites_nothing_and_does_not_fire_the_trigger(db):
    _make_fixture(db)
    _apply(db, _M1222)
    # an operator/rebuild marks the asset fresh again; a re-run must not stale it
    _exec(db, "UPDATE asset_freshness SET freshness_state='fresh', reasons='[]'::jsonb, observed_at='2026-10-02T00:00:00Z' "
              "WHERE asset_id='ga_vargas'")
    snap_fresh = _freshness(db)
    snap_reg = _q(db, "SELECT asset_id, xmin::text, integrity_check_sql FROM asset_registry ORDER BY 1")
    _apply(db, _M1222)
    assert _q(db, "SELECT asset_id, xmin::text, integrity_check_sql FROM asset_registry ORDER BY 1") == snap_reg, "row rewritten"
    assert _freshness(db) == snap_fresh, "the trigger fired on a no-op re-run"
    assert _check_md5(db) == NEW_CHECK_MD5


def test_1222_lock_timeout_fails_fast_when_the_registry_is_locked(db):
    _make_fixture(db)
    blocker = db()
    blocker.execute("LOCK TABLE asset_registry IN ACCESS EXCLUSIVE MODE")
    try:
        t0 = time.monotonic()
        victim = db(options="-c statement_timeout=20000")
        with pytest.raises(Exception) as ei:
            victim.execute(_M1222.read_text())
        elapsed = time.monotonic() - t0
        victim.rollback()
        victim.close()
    finally:
        blocker.rollback()
        blocker.close()
    assert "lock timeout" in str(ei.value).lower(), str(ei.value)
    assert elapsed < 15, f"did not fail fast ({elapsed:.1f}s)"


# ── 1223 ─────────────────────────────────────────────────────────────────────

def test_1223_retires_the_883_spec_and_installs_exactly_one_new_current_spec(db):
    _make_fixture(db)
    before = {(a, s): (sp, rv, rt) for a, s, sp, rv, rt, _ in _specs(db)}
    fresh = _freshness(db)
    reg = _q(db, "SELECT asset_id, to_jsonb(r)::text FROM asset_registry r ORDER BY 1")
    _apply(db, _M1223)
    rows = _q(db, "SELECT spec_sha256, spec, reviewed_at, retired_at FROM asset_output_digest_specs "
                  "WHERE asset_id='ga_vargas' ORDER BY retired_at NULLS LAST")
    assert len(rows) == 2
    (old_sha, _, old_rev, old_ret), (new_sha, new_spec, new_rev, new_ret) = rows
    assert old_sha == OLD_SPEC_SHA and old_ret is not None and old_ret >= old_rev, "old spec retired, CHECK holds"
    assert new_sha == NEW_SPEC_SHA and new_ret is None and new_rev is not None
    assert new_spec == _new_spec() and new_spec["components"][0]["key_columns"] == SEVEN
    assert _q(db, "SELECT count(*) FROM asset_output_digest_specs WHERE asset_id='ga_vargas' AND retired_at IS NULL")[0][0] == 1
    # no other asset's spec changed; no registry row; no freshness (1223 has no registry trigger: staleness is 1222/1226's)
    after = {(a, s): (sp, rv, rt) for a, s, sp, rv, rt, _ in _specs(db) if a != "ga_vargas"}
    assert after == {k: v for k, v in before.items() if k[0] != "ga_vargas"}
    assert _freshness(db) == fresh
    assert _q(db, "SELECT asset_id, to_jsonb(r)::text FROM asset_registry r ORDER BY 1") == reg


@pytest.mark.parametrize("scenario", ["other_sha_current", "no_current", "883_sha_wrong_key_columns", "no_spec_rows"])
def test_1223_guard_refuses_when_the_live_spec_is_not_the_883_spec(db, scenario):
    if scenario == "other_sha_current":
        _make_fixture(db, spec_row=("a" * 64, json.dumps({"version": "other"})))
    elif scenario == "883_sha_wrong_key_columns":
        bad = _old_spec()
        bad["components"][0]["key_columns"] = SIX[:5]
        _make_fixture(db, spec_row=(OLD_SPEC_SHA, json.dumps(bad)))
    else:
        _make_fixture(db)
        if scenario == "no_current":
            _exec(db, "UPDATE asset_output_digest_specs SET retired_at = now() WHERE asset_id='ga_vargas'")
        else:
            _exec(db, "DELETE FROM asset_output_digest_specs WHERE asset_id='ga_vargas'")
    before = _specs(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _M1223)
    assert "1223" in str(ei.value) and "neither the 883 spec nor this migration" in str(ei.value), str(ei.value)
    assert _specs(db) == before, "a refused migration must change nothing"


def test_1223_is_idempotent_second_run_changes_no_row(db):
    _make_fixture(db)
    _apply(db, _M1223)
    snap = _specs(db)
    _apply(db, _M1223)
    assert _specs(db) == snap, "second run rewrote a spec row (retired_at / xmin / new row)"
    assert _q(db, "SELECT count(*) FROM asset_output_digest_specs WHERE asset_id='ga_vargas'")[0][0] == 2


def test_1223_on_conflict_do_nothing_cannot_fake_a_current_row_the_post_check_catches_it(db):
    """The new sha already exists but RETIRED, the 883 spec is current: the retire succeeds, the INSERT's
    ON CONFLICT DO NOTHING inserts nothing, and the post-check refuses (rollback): no silent no-op."""
    _make_fixture(db)
    _exec(db, "INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec, reviewed_at, retired_at) "
              "VALUES ('ga_vargas', %s, %s::jsonb, '2026-09-08T00:00:00Z', '2026-09-09T00:00:00Z')",
          (NEW_SPEC_SHA, json.dumps(_new_spec())))
    before = _specs(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _M1223)
    assert "not the single current row" in str(ei.value), str(ei.value)
    assert _specs(db) == before


def test_1223_lock_timeout_fails_fast_when_the_specs_table_is_locked(db):
    _make_fixture(db)
    blocker = db()
    blocker.execute("LOCK TABLE asset_output_digest_specs IN ACCESS EXCLUSIVE MODE")
    try:
        t0 = time.monotonic()
        victim = db(options="-c statement_timeout=20000")
        with pytest.raises(Exception) as ei:
            victim.execute(_M1223.read_text())
        elapsed = time.monotonic() - t0
        victim.rollback()
        victim.close()
    finally:
        blocker.rollback()
        blocker.close()
    assert "lock timeout" in str(ei.value).lower(), str(ei.value)
    assert elapsed < 15, f"did not fail fast ({elapsed:.1f}s)"


# ── combined: the S-L1 W1 window (1221, 1222, 1223, 1226 in one deploy) ─────

_FILES = {"1221": None, "1222": _M1222, "1223": _M1223, "1226": None}


def _apply_named(connect, name: str):
    if name == "1221":
        conn = connect()
        try:
            conn.execute(_STANDIN_1221); conn.commit()
        except Exception:
            conn.rollback(); raise
        finally:
            conn.close()
    elif name == "1226":
        conn = connect()
        try:
            conn.execute(_STANDIN_1226); conn.commit()
        except Exception:
            conn.rollback(); raise
        finally:
            conn.close()
    else:
        _apply(connect, _FILES[name])


@pytest.mark.parametrize("order", [("1221", "1222", "1223", "1226")])
def test_window_numeric_order_applies_cleanly_and_degrades_exactly_the_stated_set(db, order):
    _make_fixture(db)
    for name in order:
        _apply_named(db, name)
    assert _check_md5(db) == NEW_CHECK_MD5
    assert _q(db, "SELECT count(*) FROM asset_output_digest_specs WHERE asset_id='ga_vargas' AND retired_at IS NULL "
                  "AND spec_sha256=%s", (NEW_SPEC_SHA,))[0][0] == 1
    assert _q(db, "SELECT depends_on FROM asset_registry WHERE asset_id='ga_vargas'")[0][0] == ["ga_positions", "ga_sensitive"]
    stale = {a for a, c, s, r, o in _freshness(db) if s == "stale"}
    assert stale == {"ga_structural", "ga_vargas", "ga_dashas", "ga_yoga"}, stale
    assert all(s == "stale" for a, c, s, r, o in _freshness(db) if a in stale), "every chart"


@pytest.mark.parametrize("order", list(itertools.permutations(["1221", "1222", "1223", "1226"])))
def test_no_apply_order_of_the_four_trips_a_guard(db, order):
    """The guards read only their own row/column, so the window never depends on file order. Numeric order
    is what the runner uses; every other permutation is proved clean as well (e.g. a re-run after a partial)."""
    _make_fixture(db)
    for name in order:
        _apply_named(db, name)
    assert _check_md5(db) == NEW_CHECK_MD5
    assert _q(db, "SELECT count(*) FROM asset_output_digest_specs WHERE asset_id='ga_vargas' AND retired_at IS NULL")[0][0] == 1


def test_window_rerun_of_all_four_after_apply_is_a_noop(db):
    _make_fixture(db)
    for name in ("1221", "1222", "1223"):
        _apply_named(db, name)
    snap_specs = _specs(db)
    snap_reg = _q(db, "SELECT asset_id, xmin::text FROM asset_registry WHERE asset_id IN ('ga_vargas') ORDER BY 1")
    _apply_named(db, "1222"); _apply_named(db, "1223")
    assert _specs(db) == snap_specs
    assert _q(db, "SELECT asset_id, xmin::text FROM asset_registry WHERE asset_id IN ('ga_vargas') ORDER BY 1") == snap_reg
