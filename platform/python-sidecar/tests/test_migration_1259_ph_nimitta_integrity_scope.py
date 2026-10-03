"""
Migration 1259 (Suvarna, SS ruling N-99 / Q-L4-02): ph_nimitta's registry integrity_check_sql loses its one GLOBAL
term over the L5 table mimamsa_predictions ("an integrity check must claim only what its own writer produces").
HELD: own draft PR, merges only after S-L1 and only on SS's review.

Two tiers:
  * STATIC (always runs, DB-free): file shape, guards, header sections; the OLD text rebuilt from migrations 680 + 683
    must hash to the live md5; the NEW text must hash to the md5 the migration names AND must equal the OLD text
    minus exactly the one mimamsa_predictions line (comments aside); the other conjuncts must all still be there.
  * LIVE (needs PostgreSQL server binaries): applies the REAL migration file to a DISPOSABLE cluster this module
    creates with initdb in a temp dir (unix socket only, trust auth, removed at session end). It never connects to
    anything else. Skipped, loudly, when no initdb/pg_ctl (or no uuid-ossp) is found; REQUIRE_PG_BINARIES=1 turns
    that skip into a failure. Set PG_BIN to pin a version (production is PostgreSQL 15).

The LIVE fixture carries the REAL trigger function body and trigger definition of
nirmana_registry_receipt_invalidation (read from production 2026-10-03 with pg_get_functiondef /
pg_get_triggerdef), the registry columns that trigger names, the production definition of
phala_anchor_identity() and a minimal copy of every table the check reads. What it proves: the apply/guard/
idempotency behaviour, the serving effect the header states (ph_nimitta freshness stale on every chart row it
has, nothing else moves), and the SEMANTICS: the OLD text is false on 135 dangling frozen predictions while the
NEW text is true, and the NEW text still goes false on every other kind of corruption (so nothing but the one
term was weakened), including the phala_phaladesa.top_anchor_id dangling that is still false in production.
A mutation section rewrites the real SQL (guards neutered, wrong target text, term removal widened, lock_timeout
removed) and requires every mutant to be caught.
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
import time
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_MIG = _REPO / "platform" / "migrations"
_M1259 = _MIG / "1259_nirmana_l4_ph_nimitta_integrity_scope_own_family.sql"
_M680 = _MIG / "680_phala_anchor_deterministic_identity.sql"
_M683 = _MIG / "683_phala_anchor_signal_id_disposition.sql"

OLD_MD5 = "658ffdbcb6d531e8cf5eed6c5260a966"  # live production text, read 2026-10-03
NEW_MD5 = "45192b2752989dc4398d81c0135e1473"
OLD_LEN, NEW_LEN = 3063, 3167
MIMAMSA_TERM = ("AND (SELECT count(*) FROM mimamsa_predictions p LEFT JOIN phala_anchors a ON "
                "a.anchor_id::text = p.source_pramana_id WHERE p.source_pramana_id IS NOT NULL AND a.anchor_id IS NULL) = 0")
CANON = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
CHARTS = [CANON, OTHER, "00000000-0000-4000-8000-0000000000a1"]


# -- helpers ----------------------------------------------------------------

def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("--"))


def _flat(path: Path) -> str:
    return re.sub(r"\s+", " ", re.sub(r"^--", " ", path.read_text(), flags=re.M))


def _old_check() -> str:
    """Migration 680's check body + migration 683's appended C13 conjunct = the live production text."""
    a = re.search(r"\$check\$(.*?)\$check\$", _M680.read_text(), re.S).group(1)
    b = re.search(r"\$add\$(.*?)\$add\$", _M683.read_text(), re.S).group(1)
    return a + b


def _new_check(path: Path = _M1259) -> str:
    return re.search(r"\$ck\$(.*)\$ck\$", path.read_text(), re.S).group(1)


def _exec_only(sql: str) -> str:
    """Executable text: SQL comments dropped, whitespace collapsed."""
    return re.sub(r"\s+", " ", re.sub(r"--[^\n]*", "", sql)).strip()


# -- STATIC tier --------------------------------------------------------------

def test_old_text_rebuilt_from_680_and_683_is_the_live_production_text():
    old = _old_check()
    assert hashlib.md5(old.encode()).hexdigest() == OLD_MD5 and len(old) == OLD_LEN


def test_new_text_has_the_named_md5_and_length():
    new = _new_check()
    assert hashlib.md5(new.encode()).hexdigest() == NEW_MD5 and len(new) == NEW_LEN


def test_new_text_is_the_old_text_minus_exactly_the_mimamsa_term():
    old, new = _exec_only(_old_check()), _exec_only(_new_check())
    assert old.count(MIMAMSA_TERM) == 1 and MIMAMSA_TERM not in new
    assert new == old.replace(" " + MIMAMSA_TERM, "", 1), "executable text differs by more than the one term"
    assert "mimamsa_predictions" not in new
    # nothing else was weakened: every other conjunct is still there
    for table in ("phala_suddha_sodhana", "phala_sodhana", "phala_pramana", "phala_sankrama", "phala_muhurta",
                  "phala_mitigation", "phala_phaladesa", "bodha_msr_signals"):
        assert table in new, table
    assert "phala_anchor_identity(" in new and "<= 4" in new and "HAVING count(*) > 1" in new
    assert new.count("(SELECT count(*) FROM") == _exec_only(_old_check()).count("(SELECT count(*) FROM") - 1
    assert "7 columns THIS ASSET'S OWN FAMILY" in _new_check() and "8 columns" not in _new_check()


def test_migration_does_not_own_the_transaction_and_starts_with_lock_timeout():
    code = _code(_M1259)
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code), "migrate.ts owns the transaction"
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert not re.search(r"^\s*(DROP|TRUNCATE|DELETE\s+FROM|REVOKE|GRANT|ALTER|CREATE|INSERT)\b", code, re.I | re.M)
    assert "$pre$" in code and "$post$" in code


def test_migration_is_one_guarded_update_of_one_column_of_one_row():
    code = _code(_M1259)
    assert len(re.findall(r"\bUPDATE asset_registry\b", code)) == 1
    assert re.findall(r"\bSET\s+([a-z_]+)\s*=", code.split("$ck$")[0], re.I) == ["integrity_check_sql"]
    tail = code.split("$ck$")[-1]
    assert "WHERE asset_id = 'ph_nimitta'" in tail and f"md5(integrity_check_sql) = '{OLD_MD5}'" in tail
    assert code.count(OLD_MD5) == 2, "pre-check (accept) + UPDATE guard name the base md5"
    assert code.count(NEW_MD5) == 2, "pre-check (already applied) + post-check name the target md5"
    assert "ph_nimitta" in code and "ga_" not in code and "ph_rectification" not in code


def test_header_states_serving_effect_trigger_ordering_readbacks_and_what_is_not_done():
    sql = _flat(_M1259)
    for needle in ("SERVING EFFECT AT APPLY", "nirmana_registry_receipt_invalidation",
                   "AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, "
                   "target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table",
                   "old.* IS DISTINCT FROM new.*", "Affected asset: ph_nimitta ONLY", "0 of them belong to any ph_* asset",
                   "HELD", "AFTER S-L1", "on SS's review", "IDEMPOTENT SHAPE", "ROLLBACK", "suvarna_reader",
                   "VERIFICATION BY PRODUCTION STRUCTURE", "NOT DONE HERE", "0 ACTIVE RUNS AT APPLY",
                   "no EXECUTE on phala_anchor_identity", "STILL FALSE", "phala_phaladesa.top_anchor_id",
                   "135", "OLD text: FALSE", "NEW text: STILL FALSE", "(a7)", "migration 680", "Q-L4-02", NEW_MD5, OLD_MD5):
        assert needle in sql, f"header no longer states: {needle}"


def test_number_and_name_follow_the_pattern_and_are_free_of_siblings():
    assert _M1259.name.startswith("1259_")
    assert len(list(_MIG.glob("1259_*.sql"))) == 1
    assert 1200 <= int(_M1259.name[:4]) <= 1299


# -- LIVE tier: disposable PostgreSQL ----------------------------------------------

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
    root = Path(tempfile.mkdtemp(prefix="m1259pg"))
    data = root / "data"
    sockdir = Path(tempfile.mkdtemp(prefix="m59", dir="/tmp"))  # unix socket paths are length-limited
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
            try:
                c.execute("CREATE DATABASE probe")
                with psycopg.connect(host=str(sockdir), port=port, user="postgres", dbname="probe", autocommit=True) as p:
                    p.execute('CREATE EXTENSION "uuid-ossp"')
            except Exception:  # noqa: BLE001
                if os.environ.get("REQUIRE_PG_BINARIES") == "1":
                    raise
                pytest.skip("uuid-ossp extension is not available in this PostgreSQL install")
        yield {"port": port, "sock": str(sockdir), "psycopg": psycopg}
    finally:
        subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(sockdir, ignore_errors=True)


_db_counter = 0


@pytest.fixture()
def db(pg_cluster):
    """A fresh database per test; yields a connect() factory (autocommit off)."""
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


def _apply(connect, sql: str):
    """Run a migration the way migrate.ts does: one transaction around the whole file."""
    conn = connect()
    try:
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


# Real trigger function body + definition (production 2026-10-03, pg_get_functiondef / pg_get_triggerdef).
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

# Production definition of the identity function (read 2026-10-03).
_IDENTITY_FN = """
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE OR REPLACE FUNCTION phala_anchor_identity_namespace()
RETURNS uuid LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$ SELECT 'a5f7c1e2-0b3d-5e88-9c41-6d2f8a7b4e10'::uuid $$;
CREATE OR REPLACE FUNCTION phala_anchor_identity(
  p_chart_id uuid, p_anchor_source text, p_event_type text, p_direction text, p_domain text,
  p_horizon_tier text, p_window_start date, p_peak_date date, p_window_end date, p_falsifier text
) RETURNS uuid LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$
  SELECT uuid_generate_v5(phala_anchor_identity_namespace(), jsonb_build_array(
      p_chart_id::text, p_anchor_source, p_event_type, p_direction, p_domain,
      p_horizon_tier, p_window_start::text, p_peak_date::text, p_window_end::text, p_falsifier)::text)
$$;
"""

_DDL = """
CREATE TABLE asset_registry (
    asset_id text PRIMARY KEY, layer text NOT NULL, sort_order integer NOT NULL, english_name text NOT NULL,
    target_table text, target_floor integer, depends_on text[] DEFAULT ARRAY[]::text[],
    scope text NOT NULL DEFAULT 'per_chart' CHECK (scope IN ('global', 'per_chart')),
    is_active boolean DEFAULT true, asset_type text NOT NULL DEFAULT 'data', health_probe jsonb,
    integrity_check_sql text, asset_kind text NOT NULL DEFAULT 'data', has_writer boolean NOT NULL DEFAULT false,
    natural_key_partition text, volume_explanation text
);
CREATE TABLE asset_freshness (
    asset_id text NOT NULL REFERENCES asset_registry(asset_id) ON DELETE CASCADE,
    chart_id uuid, scope_key text NOT NULL, partition_key text NOT NULL CHECK (btrim(partition_key) <> ''),
    freshness_state text NOT NULL CHECK (freshness_state IN ('fresh', 'stale', 'unknown')),
    reasons jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(reasons) = 'array'),
    receipt_version text NOT NULL, observed_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (asset_id, scope_key, partition_key)
);
CREATE TABLE phala_anchors (
    anchor_id uuid PRIMARY KEY, chart_id uuid NOT NULL, anchor_source text, event_type text, direction text,
    domain text, horizon_tier text, window_start date, peak_date date, window_end date, falsifier text, signal_id uuid
);
CREATE TABLE phala_suddha_sodhana (anchor_id uuid);
CREATE TABLE phala_sodhana (anchor_id uuid);
CREATE TABLE phala_pramana (anchor_id uuid);
CREATE TABLE phala_sankrama (source_anchor_id uuid);
CREATE TABLE phala_muhurta (linked_anchor_id uuid);
CREATE TABLE phala_mitigation (linked_anchor_id uuid);
CREATE TABLE phala_phaladesa (top_anchor_id uuid);
CREATE TABLE mimamsa_predictions (prediction_id serial PRIMARY KEY, chart_id uuid, source_pramana_id text);
CREATE TABLE bodha_msr_signals (signal_id uuid PRIMARY KEY, chart_id uuid NOT NULL);
"""


def _make_fixture(connect, *, check_text: str | None = None, with_row: bool = True):
    old = _old_check() if check_text is None else check_text
    with connect() as c:
        c.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public")  # scenarios reuse one database
        c.execute(_DDL)
        c.execute(_IDENTITY_FN)
        if with_row:
            for i, aid in enumerate(("ph_nimitta", "ph_pramana", "ph_phaladesa", "ga_vargas")):
                check = old if aid == "ph_nimitta" else f"SELECT true -- {aid}"
                c.execute("INSERT INTO asset_registry (asset_id, layer, sort_order, english_name, integrity_check_sql) "
                          "VALUES (%s, %s, %s, %s, %s)", (aid, aid.split("_")[0], i, aid.upper(), check))
        c.execute(_TRIGGER_FN)
        c.execute(_TRIGGER_DEF)
        if with_row:
            for aid in ("ph_nimitta", "ph_pramana", "ga_vargas"):
                for chart in CHARTS:
                    c.execute("INSERT INTO asset_freshness (asset_id, chart_id, scope_key, partition_key, freshness_state, "
                              "receipt_version, observed_at) VALUES (%s, %s, %s, 'default', 'fresh', 'v1', '2026-10-01T00:00:00Z')",
                              (aid, chart, f"chart:{chart}"))
        c.commit()


def _seed_clean_data(connect, *, dangling_predictions: int = 0):
    """A consistent L4 family: 3 anchors per chart (ids = phala_anchor_identity), one pramana + sodhana per anchor,
    predictions that all resolve; optionally N predictions citing anchors that do not exist (the 135 case)."""
    with connect() as c:
        for chart in (CANON, OTHER):
            for k in range(3):
                c.execute(
                    "INSERT INTO phala_anchors (anchor_id, chart_id, anchor_source, event_type, direction, domain, horizon_tier, "
                    "window_start, peak_date, window_end, falsifier) SELECT phala_anchor_identity(%s::uuid, 'msr', %s, 'up', "
                    "'career', 'near', '2026-11-01', '2026-11-15', '2026-12-01', 'f'||%s), %s::uuid, 'msr', %s, 'up', "
                    "'career', 'near', '2026-11-01', '2026-11-15', '2026-12-01', 'f'||%s",
                    (chart, f"e{k}", k, chart, f"e{k}", k))
        c.execute("INSERT INTO phala_pramana SELECT anchor_id FROM phala_anchors")
        c.execute("INSERT INTO phala_sodhana SELECT anchor_id FROM phala_anchors")
        c.execute("INSERT INTO phala_suddha_sodhana SELECT anchor_id FROM phala_anchors")
        c.execute("INSERT INTO phala_phaladesa SELECT anchor_id FROM phala_anchors LIMIT 2")
        c.execute("INSERT INTO phala_phaladesa VALUES (NULL)")  # NULL top_anchor_id is legal and must not count
        c.execute("INSERT INTO mimamsa_predictions (chart_id, source_pramana_id) SELECT chart_id, anchor_id::text FROM phala_anchors")
        for _ in range(dangling_predictions):
            c.execute("INSERT INTO mimamsa_predictions (chart_id, source_pramana_id) VALUES (%s, gen_random_uuid()::text)", (CANON,))
        c.commit()


def _check_value(connect, aid="ph_nimitta"):
    sql = _q(connect, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id=%s", (aid,))[0][0]
    return _q(connect, sql)[0][0]


def _freshness(connect):
    return _q(connect, "SELECT asset_id, chart_id::text, freshness_state, reasons::text, observed_at::text "
                       "FROM asset_freshness ORDER BY 1, 2")


def _registry_other_than_ph_nimitta(connect):
    return _q(connect, "SELECT asset_id, to_jsonb(r)::text FROM asset_registry r WHERE asset_id <> 'ph_nimitta' ORDER BY 1")


def _md5(connect):
    return _q(connect, "SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id='ph_nimitta'")[0][0]


def test_fixture_old_check_is_true_on_clean_data_and_new_check_agrees(db):
    _make_fixture(db)
    _seed_clean_data(db)
    assert _check_value(db) is True
    _apply(db, _M1259.read_text())
    assert _check_value(db) is True


def test_old_text_is_false_on_135_dangling_frozen_predictions_new_text_is_true(db):
    """The production situation: 135 frozen L5 predictions cite vanished anchors; everything else is consistent."""
    _make_fixture(db)
    _seed_clean_data(db, dangling_predictions=135)
    assert _check_value(db) is False, "OLD text must be false on dangling L5 references"
    assert _q(db, "SELECT count(*) FROM mimamsa_predictions p LEFT JOIN phala_anchors a ON a.anchor_id::text = p.source_pramana_id "
                  "WHERE a.anchor_id IS NULL")[0][0] == 135
    _apply(db, _M1259.read_text())
    assert _md5(db) == NEW_MD5
    assert _check_value(db) is True, "NEW text must not be judged by frozen L5 rows"


# Every other kind of corruption must still turn the NEW text false: only the one term was removed.
_STILL_RED = {
    "phaladesa_top_anchor_dangling (the 6 in production)": "INSERT INTO phala_phaladesa VALUES (gen_random_uuid())",
    "suddha_sodhana_dangling": "INSERT INTO phala_suddha_sodhana VALUES (gen_random_uuid())",
    "sodhana_dangling": "INSERT INTO phala_sodhana VALUES (gen_random_uuid())",
    "pramana_dangling": "INSERT INTO phala_pramana VALUES (gen_random_uuid())",
    "sankrama_dangling": "INSERT INTO phala_sankrama VALUES (gen_random_uuid())",
    "muhurta_dangling": "INSERT INTO phala_muhurta VALUES (gen_random_uuid())",
    "mitigation_dangling": "INSERT INTO phala_mitigation VALUES (gen_random_uuid())",
    "pramana_not_1_to_1": "INSERT INTO phala_pramana SELECT anchor_id FROM phala_anchors LIMIT 1",
    "identity_mismatch_over_allowance": ("INSERT INTO phala_anchors (anchor_id, chart_id) SELECT gen_random_uuid(), %s::uuid FROM generate_series(1,5)" % repr(CANON)),
    "cross_chart_signal": ("INSERT INTO bodha_msr_signals VALUES ('11111111-1111-4111-8111-111111111111', %s); "
                           "UPDATE phala_anchors SET signal_id='11111111-1111-4111-8111-111111111111' WHERE chart_id=%s" % (repr(OTHER), repr(CANON))),
}


@pytest.mark.parametrize("name", sorted(_STILL_RED))
def test_new_text_still_goes_false_on_every_other_corruption(db, name):
    _make_fixture(db)
    _seed_clean_data(db)
    _apply(db, _M1259.read_text())
    assert _check_value(db) is True
    _exec(db, _STILL_RED[name])
    assert _check_value(db) is False, f"NEW text no longer detects: {name}"


def test_identity_allowance_of_four_is_preserved(db):
    _make_fixture(db)
    _seed_clean_data(db)
    _apply(db, _M1259.read_text())
    _exec(db, "INSERT INTO phala_anchors (anchor_id, chart_id) SELECT gen_random_uuid(), %s::uuid FROM generate_series(1,4)" % repr(CANON))
    assert _check_value(db) is True, "<= 4 identity mismatches stay allowed (issue #1748)"


def test_apply_installs_the_new_text_and_stales_exactly_ph_nimitta_rows(db):
    _make_fixture(db)
    other_before = _registry_other_than_ph_nimitta(db)
    fresh_before = {(a, c): (s, r, o) for a, c, s, r, o in _freshness(db)}
    _apply(db, _M1259.read_text())
    assert _md5(db) == NEW_MD5
    assert _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ph_nimitta'")[0][0] == _new_check()
    rows = _freshness(db)
    stale = {(a, c) for a, c, s, r, o in rows if s == "stale"}
    assert stale == {("ph_nimitta", ch) for ch in CHARTS}, "ph_nimitta stale on EVERY chart row it has, nothing else"
    for a, c, s, r, o in rows:
        if a == "ph_nimitta":
            assert "registry_changed" in r
        else:
            assert (s, r, o) == fresh_before[(a, c)], f"{a} freshness changed"
    assert _registry_other_than_ph_nimitta(db) == other_before, "another registry row changed"
    row = _q(db, "SELECT to_jsonb(r) - 'integrity_check_sql' FROM asset_registry r WHERE asset_id='ph_nimitta'")[0][0]
    assert row["layer"] == "ph" and row["is_active"] is True, "only integrity_check_sql changed"


def test_apply_with_no_ph_nimitta_freshness_rows_changes_no_freshness(db):
    """Production today: asset_freshness has 0 rows for any ph_* asset, so the trigger updates nothing."""
    _make_fixture(db)
    _exec(db, "DELETE FROM asset_freshness WHERE asset_id = 'ph_nimitta'")
    before = _freshness(db)
    _apply(db, _M1259.read_text())
    assert _freshness(db) == before
    assert _md5(db) == NEW_MD5


def test_md5_guard_refuses_an_unexpected_text_and_changes_nothing(db):
    _make_fixture(db, check_text="SELECT false AS integrity_passed")
    fresh, reg = _freshness(db), _registry_other_than_ph_nimitta(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _M1259.read_text())
    assert "1259" in str(ei.value) and "not the text this migration was written against" in str(ei.value), str(ei.value)
    assert _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ph_nimitta'")[0][0] == "SELECT false AS integrity_passed"
    assert _freshness(db) == fresh and _registry_other_than_ph_nimitta(db) == reg


def test_refuses_a_missing_ph_nimitta_row(db):
    _make_fixture(db)
    _exec(db, "DELETE FROM asset_registry WHERE asset_id='ph_nimitta'")
    with pytest.raises(Exception) as ei:
        _apply(db, _M1259.read_text())
    assert "expected exactly one ph_nimitta registry row" in str(ei.value), str(ei.value)


def test_idempotent_second_run_rewrites_nothing_and_does_not_fire_the_trigger(db):
    _make_fixture(db)
    _apply(db, _M1259.read_text())
    _exec(db, "UPDATE asset_freshness SET freshness_state='fresh', reasons='[]'::jsonb, observed_at='2026-10-02T00:00:00Z' "
              "WHERE asset_id='ph_nimitta'")
    snap_fresh = _freshness(db)
    snap_reg = _q(db, "SELECT asset_id, xmin::text, integrity_check_sql FROM asset_registry ORDER BY 1")
    _apply(db, _M1259.read_text())
    assert _q(db, "SELECT asset_id, xmin::text, integrity_check_sql FROM asset_registry ORDER BY 1") == snap_reg, "row rewritten"
    assert _freshness(db) == snap_fresh, "the trigger fired on a no-op re-run"
    assert _md5(db) == NEW_MD5


def test_lock_timeout_fails_fast_when_the_registry_is_locked(db):
    _make_fixture(db)
    blocker = db()
    blocker.execute("LOCK TABLE asset_registry IN ACCESS EXCLUSIVE MODE")
    try:
        t0 = time.monotonic()
        victim = db(options="-c statement_timeout=20000")
        with pytest.raises(Exception) as ei:
            victim.execute(_M1259.read_text())
        elapsed = time.monotonic() - t0
        victim.rollback()
        victim.close()
    finally:
        blocker.rollback()
        blocker.close()
    assert "lock timeout" in str(ei.value).lower(), str(ei.value)
    assert elapsed < 15, f"did not fail fast ({elapsed:.1f}s)"


# -- MUTATION proof ---------------------------------------------------------------

def _scenario(db, sql: str) -> list[str]:
    """Violations of the contract when `sql` (a possibly mutated migration) is applied to a fresh fixture."""
    v: list[str] = []
    # 1. apply on production-shaped data: new md5 lands, check true on the 135-dangling case, trigger staled only ph_nimitta
    _make_fixture(db)
    _seed_clean_data(db, dangling_predictions=135)
    fresh_other = [r for r in _freshness(db) if r[0] != "ph_nimitta"]
    try:
        _apply(db, sql)
    except Exception as exc:  # noqa: BLE001
        return [f"apply failed: {str(exc).splitlines()[0]}"]
    if _md5(db) != NEW_MD5:
        v.append(f"new md5 not installed ({_md5(db)})")
    if _check_value_safe(db) is not True:
        v.append("new check is not true on the 135-dangling case")
    if [r for r in _freshness(db) if r[0] != "ph_nimitta"] != fresh_other:
        v.append("another asset's freshness moved")
    # 2. a corruption the new text must still see
    _exec(db, "INSERT INTO phala_phaladesa VALUES (gen_random_uuid())")
    if _check_value_safe(db) is not False:
        v.append("new check no longer detects a dangling phala_phaladesa.top_anchor_id")
    return v


def _check_value_safe(connect):
    try:
        return _check_value(connect)
    except Exception:  # noqa: BLE001
        return None


def _guard_scenarios(db, sql: str) -> list[str]:
    v: list[str] = []
    # (1) an unexpected base text must be refused BY THE PRE-CHECK and left alone
    _make_fixture(db, check_text="SELECT false AS integrity_passed")
    try:
        _apply(db, sql)
        v.append("accepted an unexpected base text")
    except Exception as exc:  # noqa: BLE001
        if "not the text this migration was written against" not in str(exc):
            v.append(f"refused, but not by the pre-check: {str(exc).splitlines()[0]}")
    if _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ph_nimitta'")[0][0] != "SELECT false AS integrity_passed":
        v.append("overwrote an unexpected base text")
    return v


def _rerun_scenario(db, sql: str) -> list[str]:
    """(2) on the already-applied state the file must rewrite nothing (the UPDATE's own md5 guard)."""
    _make_fixture(db)
    _apply(db, _REAL)
    snap = _q(db, "SELECT asset_id, xmin::text FROM asset_registry ORDER BY 1")
    try:
        _apply(db, sql)
    except Exception as exc:  # noqa: BLE001
        return [f"re-run failed: {str(exc).splitlines()[0]}"]
    if _q(db, "SELECT asset_id, xmin::text FROM asset_registry ORDER BY 1") != snap:
        return ["re-run rewrote the already-applied row"]
    return []


def _lock_scenario(db, sql: str) -> list[str]:
    _make_fixture(db)
    blocker = db()
    blocker.execute("LOCK TABLE asset_registry IN ACCESS EXCLUSIVE MODE")
    try:
        victim = db(options="-c statement_timeout=8000")
        try:
            victim.execute(sql)
            return ["did not fail while the registry was locked"]
        except Exception as exc:  # noqa: BLE001
            return [] if "lock timeout" in str(exc).lower() else [f"failed for another reason (no lock_timeout): {str(exc).splitlines()[0]}"]
        finally:
            victim.rollback()
            victim.close()
    finally:
        blocker.rollback()
        blocker.close()



_EDITED_TARGET = ("(SELECT count(*) FROM phala_sodhana c LEFT JOIN phala_anchors a USING (anchor_id) WHERE c.anchor_id IS NOT NULL "
                  "AND a.anchor_id IS NULL) = 0")


def _post_scenario(db, sql: str) -> list[str]:
    """The post-check is the only thing that notices an embedded target text whose md5 is not the one the file names
    (someone edited the text and forgot the md5). Apply the file with that edit: the real post-check refuses it."""
    edited = sql.replace(_EDITED_TARGET, _EDITED_TARGET.replace("= 0", ">= 0"), 1)
    assert edited != sql
    _make_fixture(db)
    try:
        _apply(db, edited)
    except Exception:  # noqa: BLE001
        return []
    return ["a target text that does not hash to the named md5 was installed silently"]


_REAL = _M1259.read_text()
_MUTANTS = {
    # name: (mutated SQL, which scenario must catch it)
    "update_guard_removed": (re.sub(r"\n  AND md5\(integrity_check_sql\) = '%s';" % OLD_MD5, ";", _REAL), "guard"),
    "pre_check_neutered": (_REAL.replace("IS DISTINCT FROM '%s' THEN" % OLD_MD5, "IS DISTINCT FROM v_md5 THEN"), "guard"),
    "post_check_neutered": (_REAL.replace("IF v_md5 IS DISTINCT FROM '%s' THEN" % NEW_MD5, "IF false THEN"), "post"),
    "lock_timeout_removed": (_REAL.replace("SET LOCAL lock_timeout = '5s';", "", 1), "lock"),
    "lock_timeout_session_wide": (_REAL.replace("SET LOCAL lock_timeout = '5s';", "SET lock_timeout = '0';", 1), "lock"),
    "term_removal_widened_to_phaladesa": (
        _REAL.replace("  AND (SELECT count(*) FROM phala_phaladesa c LEFT JOIN phala_anchors a ON a.anchor_id = c.top_anchor_id "
                      "WHERE c.top_anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0\n", ""), "scenario"),
    "term_not_removed": (_REAL.replace("$ck$", "$ck$", 1), "scenario_text"),
}


def test_mutants_are_real_mutations_of_the_real_file():
    for name, (sql, _) in _MUTANTS.items():
        if name == "term_not_removed":
            continue
        assert sql != _REAL, f"mutant {name} did not change the file (the mutation pattern is stale)"


def test_the_real_file_produces_no_violations(db):
    assert _scenario(db, _REAL) == []
    assert _guard_scenarios(db, _REAL) == []
    assert _rerun_scenario(db, _REAL) == []
    assert _lock_scenario(db, _REAL) == []
    assert _post_scenario(db, _REAL) == []


@pytest.mark.parametrize("name", ["update_guard_removed", "pre_check_neutered", "post_check_neutered",
                                  "lock_timeout_removed", "lock_timeout_session_wide",
                                  "term_removal_widened_to_phaladesa"])
def test_every_guard_mutant_is_caught(db, name):
    sql, kind = _MUTANTS[name]
    if kind == "guard":
        v = _guard_scenarios(db, sql) + _rerun_scenario(db, sql)
    elif kind == "lock":
        v = _lock_scenario(db, sql)
    elif kind == "post":
        v = _post_scenario(db, sql)
    else:
        v = _scenario(db, sql)
    assert v, f"mutant {name} was NOT caught"


def test_term_not_removed_mutant_is_caught(db):
    """A file that carries the OLD text as its target (the term still present) must fail the semantic scenario."""
    old_target = _REAL.replace(_new_check(), _old_check())
    assert old_target != _REAL
    _make_fixture(db)
    _seed_clean_data(db, dangling_predictions=135)
    with pytest.raises(Exception):  # post-check names the NEW md5, so even a swapped-in old text is refused
        _apply(db, old_target)
