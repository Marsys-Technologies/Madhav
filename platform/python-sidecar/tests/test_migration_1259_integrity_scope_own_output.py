"""
Migration 1259 (Suvarna, SS rulings N-99 / Q-L4-02, widened by N-104 and N-105): an integrity check claims ONLY facts
about its own writer's output. ph_nimitta keeps only facts about phala_anchors; mi_bhavisya loses its reference into
phala_anchors; every moved term has an owner (ph_phaladesa, ph_pramana, ph_sodhana, ph_suddha_sodhana, ph_muhurta already
carry theirs; ph_sankrama and ph_pratikara get theirs added). HELD: own draft PR, merges only after S-L1 and only on SS's
review.

Two tiers:
  * STATIC (always runs, DB-free): file shape, guards, header sections; each OLD text is rebuilt from the repository's own
    migrations (ph_nimitta: 680+683; mi_bhavisya: 691; ph_sankrama, ph_pratikara and the five owners: 681) and must hash to
    the live production md5; each NEW text must hash to the md5 the migration names AND have the exact relation to its OLD
    text the header states (executable text, comments aside).
  * LIVE (needs PostgreSQL server binaries): applies the REAL migration file to a DISPOSABLE cluster this module creates with
    initdb in a temp dir (unix socket only, trust auth, removed at session end). It never connects to anything else. Skipped,
    loudly, when no initdb/pg_ctl (or no uuid-ossp) is found; REQUIRE_PG_BINARIES=1 turns that skip into a failure. Set PG_BIN
    to pin a version (production is PostgreSQL 15). The migration is applied as a superuser here; the amjis_app-owned,
    production-shaped proof of the same statement shape is migration 1255's/1261's role harness, and this file touches only
    asset_registry (UPDATE), which the runner's owner role owns.

The LIVE fixture carries the REAL trigger function body and trigger definition of nirmana_registry_receipt_invalidation (read
from production 2026-10-03), the production definition of phala_anchor_identity(), and a minimal copy of every table the
checks read. What it proves: apply/guard/idempotency; the serving effect the header states (only the four touched assets'
freshness rows go stale); the SEMANTICS: ph_nimitta's new check is TRUE when children/L5 rows dangle (their terms left) and
still false on its own corruptions; mi_bhavisya the same; ph_sankrama's and ph_pratikara's NEW terms bite; and the ownership
precondition refuses when an owner has lost its term. A mutation section rewrites the real SQL and requires every mutant to
be caught. It does NOT prove production state (read from production structure after deploy; Trap 103).
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
_M1259 = _MIG / "1259_integrity_checks_claim_only_own_output.sql"
_M680 = _MIG / "680_phala_anchor_deterministic_identity.sql"
_M683 = _MIG / "683_phala_anchor_signal_id_disposition.sql"
_M691 = _MIG / "691_nirmana_l5_w3_integrity_contracts.sql"
_M681 = _MIG / "681_l4_phala_c12_registry_contracts.sql"

OLD_MD5 = {"ph_nimitta": "658ffdbcb6d531e8cf5eed6c5260a966", "mi_bhavisya": "19b5ea334236eaffa493069a7d4b318b",
           "ph_sankrama": "298b2259cda7bd5b4759061e74d75d17", "ph_pratikara": "c00c6c88e3a9fc74489bde3988870ef0"}
NEW_MD5 = {"ph_nimitta": "a32f6d86553f67458dfd8373e4fdbe39", "mi_bhavisya": "8e88e9d4ed07f47cdcecc7861fc8516d",
           "ph_sankrama": "e97e797678f23c673d962b7c6cbb74ee", "ph_pratikara": "fac43b4e3117b30efb93aa87aaf80f5f"}
OLD_LEN = {"ph_nimitta": 3063, "mi_bhavisya": 2186, "ph_sankrama": 823, "ph_pratikara": 1108}
NEW_LEN = {"ph_nimitta": 2100, "mi_bhavisya": 1951, "ph_sankrama": 1409, "ph_pratikara": 1703}
OWNER_MD5 = {"ph_phaladesa": "4d1ce38724a9f1088d7c62feaf13038a", "ph_pramana": "45f89d4853b157e22507ffccdb9af0e0",
             "ph_sodhana": "942a0fee2b734f56ffaeb60ab0b4907c", "ph_suddha_sodhana": "b8d0cfb828166e67b74b3c18517d55ea",
             "ph_muhurta": "6c1a797cc4a94b770e2f4ea463abf671"}
TOUCHED = list(OLD_MD5)
OWNERS = list(OWNER_MD5)

# ph_nimitta terms that LEFT (whitespace-collapsed), in the order they stood in the base text
PH_REMOVED = [
    "(SELECT count(*) FROM phala_suddha_sodhana c LEFT JOIN phala_anchors a USING (anchor_id) WHERE c.anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0",
    "AND (SELECT count(*) FROM phala_sodhana c LEFT JOIN phala_anchors a USING (anchor_id) WHERE c.anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0",
    "AND (SELECT count(*) FROM phala_pramana c LEFT JOIN phala_anchors a USING (anchor_id) WHERE c.anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0",
    "AND (SELECT count(*) FROM phala_sankrama c LEFT JOIN phala_anchors a ON a.anchor_id = c.source_anchor_id WHERE c.source_anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0",
    "AND (SELECT count(*) FROM phala_muhurta c LEFT JOIN phala_anchors a ON a.anchor_id = c.linked_anchor_id WHERE c.linked_anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0",
    "AND (SELECT count(*) FROM phala_mitigation c LEFT JOIN phala_anchors a ON a.anchor_id = c.linked_anchor_id WHERE c.linked_anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0",
    "AND (SELECT count(*) FROM phala_phaladesa c LEFT JOIN phala_anchors a ON a.anchor_id = c.top_anchor_id WHERE c.top_anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0",
    "AND (SELECT count(*) FROM mimamsa_predictions p LEFT JOIN phala_anchors a ON a.anchor_id::text = p.source_pramana_id WHERE p.source_pramana_id IS NOT NULL AND a.anchor_id IS NULL) = 0",
    "AND (SELECT count(*) FROM (SELECT anchor_id FROM phala_pramana GROUP BY anchor_id HAVING count(*) > 1) d) = 0",
]
MI_TERM = ("OR count(*) FILTER (WHERE p.prediction_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM phala_anchors a "
           "WHERE a.chart_id = p.chart_id AND a.anchor_id::text = p.source_pramana_id)) > 0")
SK_TERM = ("AND NOT EXISTS (SELECT 1 FROM phala_sankrama s LEFT JOIN phala_anchors a ON a.anchor_id = s.source_anchor_id "
           "WHERE s.source_anchor_id IS NOT NULL AND a.anchor_id IS NULL GROUP BY s.chart_id HAVING count(*) > 0)")
PR_TERM = ("AND NOT EXISTS (SELECT 1 FROM phala_mitigation m LEFT JOIN phala_anchors a ON a.anchor_id = m.linked_anchor_id "
           "WHERE m.linked_anchor_id IS NOT NULL AND a.anchor_id IS NULL GROUP BY m.chart_id HAVING count(*) > 0)")
OWNER_FRAGMENTS = [
    ("ph_phaladesa", "a.anchor_id = pd.top_anchor_id"),
    ("ph_pramana", "FULL OUTER JOIN phala_pramana p ON p.anchor_id = a.anchor_id"),
    ("ph_pramana", "count(*) <> count(DISTINCT anchor_id)"),
    ("ph_sodhana", "LEFT JOIN phala_anchors a ON a.anchor_id = s.anchor_id"),
    ("ph_suddha_sodhana", "FULL OUTER JOIN phala_suddha_sodhana s ON s.anchor_id = a.anchor_id"),
    ("ph_muhurta", "LEFT JOIN phala_anchors a ON a.anchor_id = m.linked_anchor_id"),
]
CANON = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
THIRD = "00000000-0000-4000-8000-0000000000a1"
CHARTS = [CANON, OTHER, THIRD]


# -- helpers ----------------------------------------------------------------

def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("--"))


def _flat(path: Path) -> str:
    return re.sub(r"\s+", " ", re.sub(r"^--", " ", path.read_text(), flags=re.M))


def _exec_only(sql: str) -> str:
    """Executable text: SQL comments dropped, whitespace collapsed."""
    return re.sub(r"\s+", " ", re.sub(r"--[^\n]*", "", sql)).strip()


def _md5(t: str) -> str:
    return hashlib.md5(t.encode()).hexdigest()


def _681_blocks() -> list[str]:
    return [m.group(1) for m in re.finditer(r"\$check\$(.*?)\$check\$", _M681.read_text(), re.S)]


def _681_by_md5(md5: str) -> str:
    for b in _681_blocks():
        if _md5(b) == md5:
            return b
    raise AssertionError(f"no migration-681 check hashes to {md5}")


def _old(asset: str) -> str:
    if asset == "ph_nimitta":
        a = re.search(r"\$check\$(.*?)\$check\$", _M680.read_text(), re.S).group(1)
        b = re.search(r"\$add\$(.*?)\$add\$", _M683.read_text(), re.S).group(1)
        return a + b
    if asset == "mi_bhavisya":
        for m in re.finditer(r"\$check\$(.*?)\$check\$", _M691.read_text(), re.S):
            if "FULL JOIN mimamsa_manifestation_sets" in m.group(1):
                return m.group(1)
        raise AssertionError("mi_bhavisya check not found in migration 691")
    return _681_by_md5(OLD_MD5[asset])


_TAG = {"ph_nimitta": "ck", "mi_bhavisya": "mk", "ph_sankrama": "sk", "ph_pratikara": "rk"}


def _new(asset: str, sql: str | None = None) -> str:
    t = _TAG[asset]
    return re.search(r"\$%s\$(.*)\$%s\$" % (t, t), sql or _M1259.read_text(), re.S).group(1)


# -- STATIC tier --------------------------------------------------------------

@pytest.mark.parametrize("asset", TOUCHED)
def test_old_text_rebuilt_from_the_repo_migrations_is_the_live_production_text(asset):
    old = _old(asset)
    assert _md5(old) == OLD_MD5[asset] and len(old) == OLD_LEN[asset]


@pytest.mark.parametrize("asset", OWNERS)
def test_owner_texts_rebuilt_from_migration_681_are_the_live_production_texts(asset):
    assert _681_by_md5(OWNER_MD5[asset])


@pytest.mark.parametrize("asset", TOUCHED)
def test_new_text_has_the_named_md5_and_length(asset):
    new = _new(asset)
    assert _md5(new) == NEW_MD5[asset] and len(new) == NEW_LEN[asset]


def test_ph_nimitta_new_text_is_the_old_text_minus_exactly_the_nine_cross_asset_terms():
    old, new = _exec_only(_old("ph_nimitta")), _exec_only(_new("ph_nimitta"))
    expected = old
    for term in PH_REMOVED:
        assert expected.count(term) == 1, term[:80]
        expected = expected.replace(" " + term if not term.startswith("(") else term, "", 1)
    expected = re.sub(r"SELECT\s+AND \(", "SELECT (", re.sub(r"\s+", " ", expected)).strip()
    assert new == expected, "executable text differs from base-minus-the-nine-terms"
    for gone in ("phala_pramana", "phala_sodhana", "phala_suddha_sodhana", "phala_sankrama", "phala_muhurta", "phala_mitigation",
                 "phala_phaladesa", "mimamsa_predictions"):
        assert gone not in new, gone
    assert "phala_anchor_identity(" in new and "<= 4" in new and "bodha_msr_signals" in new and "s.chart_id <> a.chart_id" in new
    assert new.count("(SELECT count(*) FROM") == 1


def test_mi_bhavisya_new_text_is_the_old_text_minus_exactly_the_dangling_anchor_branch():
    old, new = _exec_only(_old("mi_bhavisya")), _exec_only(_new("mi_bhavisya"))
    assert old.count(MI_TERM) == 1 and MI_TERM not in new
    assert new == old.replace(" " + MI_TERM, "", 1)
    assert "phala_anchors" not in new and "source_pramana_id" not in new
    for needle in ("FULL JOIN mimamsa_manifestation_sets", "LEFT JOIN charts c", "observation_window", "confidence_band",
                   "frozen_bundle_hash", "m.domain IS DISTINCT FROM p.domain", "citation_ref",
                   "count(DISTINCT prediction_id) <> count(*)", "count(DISTINCT (prediction_id, channel_id)) <> count(*)"):
        assert needle in new, needle


@pytest.mark.parametrize("asset,term", [("ph_sankrama", SK_TERM), ("ph_pratikara", PR_TERM)])
def test_owner_additions_are_the_base_plus_exactly_one_appended_conjunct(asset, term):
    old, new = _exec_only(_old(asset)), _exec_only(_new(asset))
    assert new == old + " " + term
    assert _new(asset).startswith(_old(asset)), "the base text is a strict prefix: nothing before the appended term changed"


def test_no_moved_term_is_duplicated_where_the_owner_already_has_it():
    for asset, fragment in OWNER_FRAGMENTS:
        assert fragment in _681_by_md5(OWNER_MD5[asset]), (asset, fragment)
    code = _code(_M1259)
    for asset in OWNERS:
        assert not re.search(r"WHERE asset_id = '%s'\s+AND md5" % asset, code), f"{asset} must not be UPDATEd"
    # and the two assets that DID lack a term really lacked it
    assert "source_anchor_id" not in _exec_only(_old("ph_sankrama")).replace("source_anchor_id, cdlm_cell_id", "")
    assert "linked_anchor_id" not in _old("ph_pratikara")


def test_migration_does_not_own_the_transaction_and_starts_with_lock_timeout():
    code = _code(_M1259)
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code), "migrate.ts owns the transaction"
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert not re.search(r"^\s*(DROP|TRUNCATE|DELETE\s+FROM|REVOKE|GRANT|ALTER|CREATE|INSERT)\b", code, re.I | re.M)
    for tag in ("$runs$", "$pre$", "$own$", "$post$"):
        assert tag in code


def test_migration_is_four_guarded_updates_of_one_column_each_of_exactly_four_rows():
    code = _code(_M1259)
    assert len(re.findall(r"\bUPDATE asset_registry\b", code)) == 4
    assert re.findall(r"\bSET integrity_check_sql\s*=", code) == ["SET integrity_check_sql ="] * 4
    for asset in TOUCHED:
        assert f"WHERE asset_id = '{asset}'\n  AND md5(integrity_check_sql) = '{OLD_MD5[asset]}';" in code
        assert code.count(OLD_MD5[asset]) == 2, "pre-check list + UPDATE guard name the base md5"
        assert code.count(NEW_MD5[asset]) == 2, "pre-check list + post-check list name the target md5"
    assert "ga_" not in code and "ph_rectification" not in code


def test_ownership_precondition_lists_exactly_the_five_owners_fragments():
    code = _code(_M1259)
    block = code.split("DO $own$")[1].split("$own$;")[0]
    got = re.findall(r"\('(ph_[a-z_]+)',\s*'([^']+)'\)", block)
    assert got == OWNER_FRAGMENTS
    assert "no longer carries its own anchor-reference term" in block


def test_header_states_every_touched_asset_the_moves_the_readbacks_and_what_is_not_done():
    sql = _flat(_M1259)
    for needle in ("SERVING EFFECT AT APPLY", "nirmana_registry_receipt_invalidation",
                   "AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, "
                   "target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table",
                   "old.* IS DISTINCT FROM new.*", "Assets touched, and no others: ph_nimitta, mi_bhavisya, ph_sankrama, ph_pratikara",
                   "0 belong to any ph_* asset", "mi_jivanaghatana, mi_kula, mi_vistara", "The five owners are NOT updated",
                   "WHAT MOVES WHERE", "ph_phaladesa already has it", "ph_pramana already has it", "ph_sodhana already has it",
                   "ph_suddha_sodhana already has it", "ph_muhurta already has it", "had NONE: this migration ADDS it",
                   "REFUSES to apply if any of those five owners", "READBACKS", "NO EXECUTE on it", "FALSE, honestly",
                   "anchor_count drift", "HELD", "AFTER S-L1", "on SS's review", "IDEMPOTENT SHAPE", "ROLLBACK", "suvarna_reader",
                   "VERIFICATION BY PRODUCTION STRUCTURE", "NOT DONE HERE", "0 ACTIVE RUNS AT APPLY (ENFORCED", "N-99", "N-104", "N-105",
                   "#3023", "migration 1260", "never build-blocking", "NEVER build-blocking", *NEW_MD5.values(), *OLD_MD5.values()):
        if needle == "never build-blocking":
            continue
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
    """A fresh database per test; yields a connect() factory (autocommit off)."""
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


def _apply(connect, sql: str):
    """Run a migration the way migrate.ts does: one transaction around the whole file."""
    conn = connect(user="amjis_app")  # the migration runner's identity; owns the tables, has NO CREATE on public
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
CREATE TABLE build_runs (id bigserial PRIMARY KEY, state text NOT NULL);
CREATE TABLE build_run_assets (run_id bigint NOT NULL REFERENCES build_runs(id), asset_id text NOT NULL);
CREATE TABLE charts (id uuid PRIMARY KEY);
CREATE TABLE phala_anchors (
    anchor_id uuid PRIMARY KEY, chart_id uuid NOT NULL, anchor_source text, event_type text, direction text,
    domain text, horizon_tier text, window_start date, peak_date date, window_end date, falsifier text, signal_id uuid
);
CREATE TABLE phala_suddha_sodhana (anchor_id uuid);
CREATE TABLE phala_sodhana (anchor_id uuid);
CREATE TABLE phala_pramana (anchor_id uuid);
CREATE TABLE phala_sankrama (sankrama_id bigserial PRIMARY KEY, chart_id uuid NOT NULL, source_anchor_id uuid, cdlm_cell_id bigint,
    linkage_strength numeric, target_domain text, projected_window_start date, projected_window_end date);
CREATE TABLE bodha_cdlm_cells (cell_id bigint PRIMARY KEY, chart_id uuid NOT NULL, net_linkage_strength numeric, domain_col text);
CREATE TABLE phala_muhurta (linked_anchor_id uuid);
CREATE TABLE kala_obstruction (id bigint PRIMARY KEY, chart_id uuid NOT NULL, severity text);
CREATE TABLE phala_mitigation (mitigation_id bigserial PRIMARY KEY, chart_id uuid NOT NULL, obstruction_id bigint,
    obstruction_severity text, linked_anchor_id uuid);
CREATE TABLE phala_phaladesa (top_anchor_id uuid);
CREATE TABLE mimamsa_predictions (
    prediction_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid NOT NULL, source_pramana_id text,
    observation_window daterange, eval_date date, confidence_band numrange, frozen_bundle_hash text,
    bundle_formula_version text, outcome_claim text, domain text, falsifier_jsonb jsonb, driving_signals jsonb
);
CREATE TABLE mimamsa_manifestation_sets (
    chart_id uuid NOT NULL, prediction_id uuid NOT NULL, domain text, citation_ref text, channel_id text, source text
);
CREATE TABLE bodha_msr_signals (signal_id uuid PRIMARY KEY, chart_id uuid NOT NULL);
"""

CONTROL = ["ga_vargas"]


def _mirror_production(c):
    """Production shape: schema public is owned by data_plane_schema_owner; amjis_app has USAGE only (NO CREATE) and owns
    every table and function. Called after the DDL, as the superuser."""
    c.execute("ALTER SCHEMA public OWNER TO data_plane_schema_owner")
    c.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")
    c.execute("GRANT USAGE ON SCHEMA public TO amjis_app")
    for (t,) in c.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'").fetchall():
        c.execute(f'ALTER TABLE public."{t}" OWNER TO amjis_app')
    for (sq,) in c.execute("SELECT sequencename FROM pg_sequences WHERE schemaname = 'public'").fetchall():
        c.execute(f'ALTER SEQUENCE public."{sq}" OWNER TO amjis_app')
    c.execute("ALTER FUNCTION public.nirmana_invalidate_registry_receipts() OWNER TO amjis_app")


def _make_fixture(connect, *, texts: dict | None = None, with_rows: bool = True, owner_texts: dict | None = None):
    base = {a: _old(a) for a in TOUCHED}
    base.update(texts or {})
    owners = {a: _681_by_md5(OWNER_MD5[a]) for a in OWNERS}
    owners.update(owner_texts or {})
    with connect() as c:
        c.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public")  # scenarios reuse one database
        c.execute(_DDL)
        c.execute(_IDENTITY_FN)
        if with_rows:
            for i, aid in enumerate(TOUCHED + OWNERS + CONTROL):
                check = base.get(aid) or owners.get(aid) or f"SELECT true -- {aid}"
                c.execute("INSERT INTO asset_registry (asset_id, layer, sort_order, english_name, integrity_check_sql) "
                          "VALUES (%s, %s, %s, %s, %s)", (aid, aid.split("_")[0], i, aid.upper(), check))
        c.execute(_TRIGGER_FN)
        c.execute(_TRIGGER_DEF)
        if with_rows:
            for aid in TOUCHED + OWNERS + CONTROL:
                for chart in CHARTS:
                    c.execute("INSERT INTO asset_freshness (asset_id, chart_id, scope_key, partition_key, freshness_state, "
                              "receipt_version, observed_at) VALUES (%s, %s, %s, 'default', 'fresh', 'v1', '2026-10-01T00:00:00Z')",
                              (aid, chart, f"chart:{chart}"))
        _mirror_production(c)
        c.commit()


_PRED_COLS = ("(chart_id, source_pramana_id, observation_window, eval_date, confidence_band, frozen_bundle_hash, "
              "bundle_formula_version, outcome_claim, domain, falsifier_jsonb, driving_signals)")


def _add_prediction(c, chart: str, source_pramana_id: str | None, *, manifest: bool = True):
    pid = c.execute(
        f"INSERT INTO mimamsa_predictions {_PRED_COLS} VALUES (%s, %s, '[2026-11-01,2026-12-01)'::daterange, '2026-12-01', "
        "'[0.2,0.8]'::numrange, 'h', 'v1', 'o', 'career', '{}'::jsonb, '[]'::jsonb) RETURNING prediction_id",
        (chart, source_pramana_id)).fetchone()[0]
    if manifest:
        c.execute("INSERT INTO mimamsa_manifestation_sets (chart_id, prediction_id, domain, citation_ref, channel_id, source) "
                  "VALUES (%s, %s, 'career', 'c', 'ch', 's')", (chart, pid))
    return pid


def _seed_clean_data(connect, *, dangling_predictions: int = 0):
    """A consistent L4/L5 family: 3 anchors per chart (ids = phala_anchor_identity), one child row per anchor, one sankrama
    row (+ cdlm cell) and one obstruction+mitigation pair on CANON, one prediction (+ manifestation set) per anchor;
    optionally N valid predictions citing anchors that do not exist (the 135 case)."""
    with connect() as c:
        for chart in CHARTS:
            c.execute("INSERT INTO charts VALUES (%s)", (chart,))
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
        c.execute("INSERT INTO bodha_cdlm_cells VALUES (1, %s, 0.5, 'career')", (CANON,))
        c.execute("INSERT INTO phala_sankrama (chart_id, source_anchor_id, cdlm_cell_id, linkage_strength, target_domain) "
                  "SELECT chart_id, anchor_id, 1, 0.5, 'career' FROM phala_anchors WHERE chart_id = %s LIMIT 1", (CANON,))
        c.execute("INSERT INTO kala_obstruction VALUES (1, %s, 'mild')", (CANON,))
        c.execute("INSERT INTO phala_mitigation (chart_id, obstruction_id, obstruction_severity, linked_anchor_id) "
                  "SELECT chart_id, 1, 'low', anchor_id FROM phala_anchors WHERE chart_id = %s LIMIT 1", (CANON,))
        for chart, aid in c.execute("SELECT chart_id, anchor_id::text FROM phala_anchors").fetchall():
            _add_prediction(c, chart, aid)
        for _ in range(dangling_predictions):
            _add_prediction(c, CANON, c.execute("SELECT gen_random_uuid()::text").fetchone()[0])
        c.commit()


def _check_value(connect, aid):
    sql = _q(connect, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id=%s", (aid,))[0][0]
    return _q(connect, sql)[0][0]


def _check_value_safe(connect, aid):
    try:
        return _check_value(connect, aid)
    except Exception:  # noqa: BLE001
        return None


def _freshness(connect):
    return _q(connect, "SELECT asset_id, chart_id::text, freshness_state, reasons::text, observed_at::text "
                       "FROM asset_freshness ORDER BY 1, 2")


def _registry_untouched(connect):
    return _q(connect, "SELECT asset_id, to_jsonb(r)::text FROM asset_registry r WHERE asset_id <> ALL(%s) ORDER BY 1", (TOUCHED,))


def _md5_of(connect, aid):
    return _q(connect, "SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id=%s", (aid,))[0][0]


def _texts(connect):
    return {a: _q(connect, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id=%s", (a,))[0][0] for a in TOUCHED + OWNERS}


def test_fixture_mirrors_production_the_runner_has_usage_only_and_owns_the_tables(db):
    _make_fixture(db)
    r = _q(db, "SELECT has_schema_privilege('amjis_app','public','CREATE'), has_schema_privilege('amjis_app','public','USAGE'), "
               "(SELECT relowner::regrole::text FROM pg_class WHERE oid='asset_registry'::regclass), "
               "(SELECT nspowner::regrole::text FROM pg_namespace WHERE nspname='public')")[0]
    assert r == (False, True, "amjis_app", "data_plane_schema_owner")


def test_fixture_all_four_old_checks_are_true_on_clean_data_and_all_new_checks_agree(db):
    _make_fixture(db)
    _seed_clean_data(db)
    for a in TOUCHED:
        assert _check_value(db, a) is True, a
    _apply(db, _M1259.read_text())
    for a in TOUCHED:
        assert _check_value(db, a) is True, a


def test_old_texts_are_false_on_135_dangling_frozen_predictions_new_texts_are_true(db):
    _make_fixture(db)
    _seed_clean_data(db, dangling_predictions=135)
    assert _check_value(db, "ph_nimitta") is False and _check_value(db, "mi_bhavisya") is False
    _apply(db, _M1259.read_text())
    assert [_md5_of(db, a) for a in TOUCHED] == [NEW_MD5[a] for a in TOUCHED]
    assert _check_value(db, "ph_nimitta") is True, "ph_nimitta must not be judged by frozen L5 rows"
    assert _check_value(db, "mi_bhavisya") is True, "mi_bhavisya must not be judged by L4's anchors"


def test_mi_bhavisya_old_text_is_also_false_when_the_anchor_exists_on_another_chart_only(db):
    _make_fixture(db)
    _seed_clean_data(db)
    with db() as c:
        other_anchor = c.execute("SELECT anchor_id::text FROM phala_anchors WHERE chart_id=%s LIMIT 1", (OTHER,)).fetchone()[0]
        _add_prediction(c, CANON, other_anchor)
        c.commit()
    assert _check_value(db, "mi_bhavisya") is False
    _apply(db, _M1259.read_text())
    assert _check_value(db, "mi_bhavisya") is True


# Corruptions of OTHER assets' rows: the OLD ph_nimitta text went false on each; the NEW one must stay TRUE (their terms left).
_LEFT_TERMS = {
    "phaladesa_top_anchor_dangling (the 6 in production)": "INSERT INTO phala_phaladesa VALUES (gen_random_uuid())",
    "suddha_sodhana_dangling": "INSERT INTO phala_suddha_sodhana VALUES (gen_random_uuid())",
    "sodhana_dangling": "INSERT INTO phala_sodhana VALUES (gen_random_uuid())",
    "pramana_dangling": "INSERT INTO phala_pramana VALUES (gen_random_uuid())",
    "sankrama_dangling": "INSERT INTO phala_sankrama (chart_id, source_anchor_id) VALUES ('%s', gen_random_uuid())" % CANON,
    "muhurta_dangling": "INSERT INTO phala_muhurta VALUES (gen_random_uuid())",
    "mitigation_dangling": "INSERT INTO phala_mitigation (chart_id, linked_anchor_id) VALUES ('%s', gen_random_uuid())" % CANON,
    "pramana_not_1_to_1": "INSERT INTO phala_pramana SELECT anchor_id FROM phala_anchors LIMIT 1",
}


@pytest.mark.parametrize("name", sorted(_LEFT_TERMS))
def test_ph_nimitta_is_no_longer_judged_by_other_assets_dangling_rows(db, name):
    _make_fixture(db)
    _seed_clean_data(db)
    _exec(db, _LEFT_TERMS[name])
    assert _check_value(db, "ph_nimitta") is False, f"precondition: the OLD text must go false on: {name}"
    _apply(db, _M1259.read_text())
    assert _check_value(db, "ph_nimitta") is True, f"NEW ph_nimitta text is still judged by: {name}"


# Corruptions of ph_nimitta's OWN output: the NEW text must still go false.
_PH_STILL_RED = {
    "identity_mismatch_over_allowance": ("INSERT INTO phala_anchors (anchor_id, chart_id) SELECT gen_random_uuid(), %s::uuid FROM generate_series(1,5)" % repr(CANON)),
    "cross_chart_signal": ("INSERT INTO bodha_msr_signals VALUES ('11111111-1111-4111-8111-111111111111', %s); "
                           "UPDATE phala_anchors SET signal_id='11111111-1111-4111-8111-111111111111' WHERE chart_id=%s" % (repr(OTHER), repr(CANON))),
}
_MI_STILL_RED = {
    "prediction_without_manifestation_set": "INSERT INTO mimamsa_predictions (chart_id, source_pramana_id, observation_window, eval_date, confidence_band, frozen_bundle_hash, bundle_formula_version, outcome_claim, domain, falsifier_jsonb, driving_signals) VALUES ('%s', NULL, '[2026-11-01,2026-12-01)', '2026-12-01', '[0.2,0.8]', 'h', 'v1', 'o', 'career', '{}', '[]')" % CANON,
    "manifestation_set_without_prediction": "INSERT INTO mimamsa_manifestation_sets VALUES ('%s', gen_random_uuid(), 'career', 'c', 'ch', 's')" % CANON,
    "chart_row_missing": "DELETE FROM charts WHERE id = '%s'" % OTHER,
    "eval_date_not_window_upper": "UPDATE mimamsa_predictions SET eval_date = '2027-01-01' WHERE chart_id = '%s'" % OTHER,
    "empty_window": "UPDATE mimamsa_predictions SET observation_window = 'empty'::daterange WHERE chart_id = '%s'" % OTHER,
    "confidence_band_above_one": "UPDATE mimamsa_predictions SET confidence_band = '[0.2,1.5]'::numrange WHERE chart_id = '%s'" % OTHER,
    "blank_frozen_hash": "UPDATE mimamsa_predictions SET frozen_bundle_hash = '  ' WHERE chart_id = '%s'" % OTHER,
    "null_falsifier": "UPDATE mimamsa_predictions SET falsifier_jsonb = NULL WHERE chart_id = '%s'" % OTHER,
    "manifestation_domain_mismatch": "UPDATE mimamsa_manifestation_sets SET domain = 'health' WHERE chart_id = '%s'" % OTHER,
    "manifestation_null_citation": "UPDATE mimamsa_manifestation_sets SET citation_ref = NULL WHERE chart_id = '%s'" % OTHER,
    "duplicate_manifestation_channel": "INSERT INTO mimamsa_manifestation_sets SELECT * FROM mimamsa_manifestation_sets WHERE chart_id = '%s' LIMIT 1" % OTHER,
}


@pytest.mark.parametrize("name", sorted(_PH_STILL_RED))
def test_ph_nimitta_new_text_still_goes_false_on_its_own_corruptions(db, name):
    _make_fixture(db)
    _seed_clean_data(db)
    _apply(db, _M1259.read_text())
    assert _check_value(db, "ph_nimitta") is True
    _exec(db, _PH_STILL_RED[name])
    assert _check_value(db, "ph_nimitta") is False, f"NEW ph_nimitta text no longer detects: {name}"


@pytest.mark.parametrize("name", sorted(_MI_STILL_RED))
def test_mi_bhavisya_new_text_still_goes_false_on_every_other_corruption(db, name):
    _make_fixture(db)
    _seed_clean_data(db)
    _apply(db, _M1259.read_text())
    assert _check_value(db, "mi_bhavisya") is True
    _exec(db, _MI_STILL_RED[name])
    assert _check_value(db, "mi_bhavisya") is False, f"NEW mi_bhavisya text no longer detects: {name}"


def test_identity_allowance_of_four_is_preserved(db):
    _make_fixture(db)
    _seed_clean_data(db)
    _apply(db, _M1259.read_text())
    _exec(db, "INSERT INTO phala_anchors (anchor_id, chart_id) SELECT gen_random_uuid(), %s::uuid FROM generate_series(1,4)" % repr(CANON))
    assert _check_value(db, "ph_nimitta") is True, "<= 4 identity mismatches stay allowed (issue #1748)"


def test_ph_sankrama_new_term_bites_a_dangling_source_anchor_the_old_text_could_not_see_and_allows_null(db):
    _make_fixture(db)
    _seed_clean_data(db)
    _exec(db, "INSERT INTO phala_sankrama (chart_id, source_anchor_id, cdlm_cell_id) VALUES (%s, NULL, 7)", (CANON,))  # NULL is legal
    _apply(db, _M1259.read_text())
    assert _check_value(db, "ph_sankrama") is True
    _exec(db, "INSERT INTO phala_sankrama (chart_id, source_anchor_id, cdlm_cell_id) VALUES (%s, gen_random_uuid(), 8)", (CANON,))
    assert _check_value(db, "ph_sankrama") is False
    # and the OLD text was blind to it (the reason the term is added)
    old = _old("ph_sankrama")
    assert _q(db, old)[0][0] is True


def test_ph_pratikara_new_term_bites_a_dangling_linked_anchor_the_old_text_could_not_see(db):
    _make_fixture(db)
    _seed_clean_data(db)
    _exec(db, "INSERT INTO phala_mitigation (chart_id, obstruction_id, obstruction_severity, linked_anchor_id) VALUES (%s, 1, 'low', NULL)", (CANON,))
    _apply(db, _M1259.read_text())
    # duplicate obstruction pair removed from tiling concerns: use a fresh pair
    _exec(db, "DELETE FROM phala_mitigation WHERE linked_anchor_id IS NULL")
    assert _check_value(db, "ph_pratikara") is True
    _exec(db, "INSERT INTO kala_obstruction VALUES (2, %s, 'mild')", (CANON,))
    _exec(db, "INSERT INTO phala_mitigation (chart_id, obstruction_id, obstruction_severity, linked_anchor_id) VALUES (%s, 2, 'low', gen_random_uuid())", (CANON,))
    assert _check_value(db, "ph_pratikara") is False
    assert _q(db, _old("ph_pratikara"))[0][0] is True


def test_apply_installs_the_four_new_texts_and_stales_exactly_those_assets_rows(db):
    _make_fixture(db)
    other_before = _registry_untouched(db)
    fresh_before = {(a, c): (s, r, o) for a, c, s, r, o in _freshness(db)}
    owners_before = {a: _texts(db)[a] for a in OWNERS}
    _apply(db, _M1259.read_text())
    for a in TOUCHED:
        assert _md5_of(db, a) == NEW_MD5[a]
        assert _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id=%s", (a,))[0][0] == _new(a)
    rows = _freshness(db)
    stale = {(a, c) for a, c, s, r, o in rows if s == "stale"}
    assert stale == {(a, ch) for a in TOUCHED for ch in CHARTS}, "the four touched assets stale on EVERY chart row, nothing else"
    for a, c, s, r, o in rows:
        if a in TOUCHED:
            assert "registry_changed" in r
        else:
            assert (s, r, o) == fresh_before[(a, c)], f"{a} freshness changed"
    assert _registry_untouched(db) == other_before, "another registry row changed"
    assert {a: _texts(db)[a] for a in OWNERS} == owners_before, "an owner's text changed"
    for aid in TOUCHED:
        row = _q(db, "SELECT to_jsonb(r) - 'integrity_check_sql' FROM asset_registry r WHERE asset_id=%s", (aid,))[0][0]
        assert row["is_active"] is True and row["layer"] == aid.split("_")[0], "only integrity_check_sql changed"


def test_apply_with_no_freshness_rows_for_the_touched_assets_changes_no_freshness(db):
    """Production today: asset_freshness has no row for any ph_* asset nor for mi_bhavisya, so the trigger updates nothing."""
    _make_fixture(db)
    _exec(db, "DELETE FROM asset_freshness WHERE asset_id = ANY(%s)", (TOUCHED,))
    before = _freshness(db)
    _apply(db, _M1259.read_text())
    assert _freshness(db) == before
    assert [_md5_of(db, a) for a in TOUCHED] == [NEW_MD5[a] for a in TOUCHED]


@pytest.mark.parametrize("bad", TOUCHED)
def test_md5_guard_refuses_an_unexpected_text_for_any_of_the_four_and_changes_nothing(db, bad):
    _make_fixture(db, texts={bad: "SELECT false AS integrity_passed"})
    fresh, reg, before = _freshness(db), _registry_untouched(db), _texts(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _M1259.read_text())
    assert "1259" in str(ei.value) and bad in str(ei.value) and "not the text this migration was written against" in str(ei.value), str(ei.value)
    assert _texts(db) == before, "no asset may be updated when one is refused"
    assert _freshness(db) == fresh and _registry_untouched(db) == reg


@pytest.mark.parametrize("asset", TOUCHED)
def test_refuses_a_missing_registry_row(db, asset):
    _make_fixture(db)
    _exec(db, "DELETE FROM asset_registry WHERE asset_id=%s", (asset,))
    with pytest.raises(Exception) as ei:
        _apply(db, _M1259.read_text())
    assert f"expected exactly one {asset} registry row" in str(ei.value), str(ei.value)


@pytest.mark.parametrize("asset,fragment", OWNER_FRAGMENTS, ids=[f"{a}:{f[:30]}" for a, f in OWNER_FRAGMENTS])
def test_ownership_precondition_refuses_when_an_owner_has_lost_its_term(db, asset, fragment):
    stripped = _681_by_md5(OWNER_MD5[asset]).replace(fragment, "/*removed*/")
    _make_fixture(db, owner_texts={asset: stripped})
    before = _texts(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _M1259.read_text())
    assert asset in str(ei.value) and "no longer carries its own anchor-reference term" in str(ei.value), str(ei.value)
    assert _texts(db) == before


@pytest.mark.parametrize("asset", TOUCHED)
@pytest.mark.parametrize("state", ["running", "planned", "paused"])
def test_active_build_run_guard_refuses_and_changes_nothing(db, asset, state):
    _make_fixture(db)
    _exec(db, "INSERT INTO build_runs (state) VALUES (%s)", (state,))
    _exec(db, "INSERT INTO build_run_assets (run_id, asset_id) SELECT max(id), %s FROM build_runs", (asset,))
    before, fresh = _texts(db), _freshness(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _M1259.read_text())
    assert "active build run" in str(ei.value) and asset in str(ei.value), str(ei.value)
    assert _texts(db) == before and _freshness(db) == fresh


def test_finished_runs_and_runs_of_other_assets_do_not_block(db):
    _make_fixture(db)
    for st, aid in (("completed", "ph_nimitta"), ("failed", "mi_bhavisya"), ("stopped", "ph_sankrama"), ("running", "ga_vargas")):
        _exec(db, "INSERT INTO build_runs (state) VALUES (%s)", (st,))
        _exec(db, "INSERT INTO build_run_assets (run_id, asset_id) SELECT max(id), %s FROM build_runs", (aid,))
    _apply(db, _M1259.read_text())
    assert [_md5_of(db, a) for a in TOUCHED] == [NEW_MD5[a] for a in TOUCHED]


def test_partial_state_one_asset_already_applied_applies_the_others(db):
    _make_fixture(db, texts={"ph_nimitta": _new("ph_nimitta")})
    _apply(db, _M1259.read_text())
    assert [_md5_of(db, a) for a in TOUCHED] == [NEW_MD5[a] for a in TOUCHED]


def test_idempotent_second_run_rewrites_nothing_and_does_not_fire_the_trigger(db):
    _make_fixture(db)
    _apply(db, _M1259.read_text())
    _exec(db, "UPDATE asset_freshness SET freshness_state='fresh', reasons='[]'::jsonb, observed_at='2026-10-02T00:00:00Z' "
              "WHERE asset_id = ANY(%s)", (TOUCHED,))
    snap_fresh = _freshness(db)
    snap_reg = _q(db, "SELECT asset_id, xmin::text, integrity_check_sql FROM asset_registry ORDER BY 1")
    _apply(db, _M1259.read_text())
    assert _q(db, "SELECT asset_id, xmin::text, integrity_check_sql FROM asset_registry ORDER BY 1") == snap_reg, "row rewritten"
    assert _freshness(db) == snap_fresh, "the trigger fired on a no-op re-run"


def test_lock_timeout_fails_fast_when_the_registry_is_locked(db):
    _make_fixture(db)
    blocker = db()
    blocker.execute("LOCK TABLE asset_registry IN ACCESS EXCLUSIVE MODE")
    try:
        t0 = time.monotonic()
        victim = db(user="amjis_app", options="-c statement_timeout=20000")
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

_REAL = _M1259.read_text()


def _scenario(db, sql: str) -> list[str]:
    """Violations of the contract when `sql` (a possibly mutated migration) is applied, as amjis_app, to a production-shaped
    fixture that carries the 135-dangling L5 rows AND dangling children AND a NULL source anchor."""
    v: list[str] = []
    _make_fixture(db)
    _seed_clean_data(db, dangling_predictions=135)
    _exec(db, "INSERT INTO phala_phaladesa VALUES (gen_random_uuid())")
    _exec(db, "INSERT INTO phala_pramana VALUES (gen_random_uuid())")
    _exec(db, "INSERT INTO phala_sankrama (chart_id, source_anchor_id, cdlm_cell_id) VALUES (%s, NULL, 7)", (CANON,))
    fresh_other = [r for r in _freshness(db) if r[0] not in TOUCHED]
    owners_before = {a: _texts(db)[a] for a in OWNERS}
    try:
        _apply(db, sql)
    except Exception as exc:  # noqa: BLE001
        return [f"apply failed: {str(exc).splitlines()[0]}"]
    for aid in TOUCHED:
        if _md5_of(db, aid) != NEW_MD5[aid]:
            v.append(f"{aid}: new md5 not installed ({_md5_of(db, aid)})")
    for aid in ("ph_nimitta", "mi_bhavisya", "ph_sankrama"):
        if _check_value_safe(db, aid) is not True:
            v.append(f"{aid}: new check is not true on the production-shaped case")
    if [r for r in _freshness(db) if r[0] not in TOUCHED] != fresh_other:
        v.append("another asset's freshness moved")
    if {a: _texts(db)[a] for a in OWNERS} != owners_before:
        v.append("an owner's text changed")
    # each new term / retained term must still bite
    _exec(db, "INSERT INTO phala_sankrama (chart_id, source_anchor_id, cdlm_cell_id) VALUES (%s, gen_random_uuid(), 8)", (CANON,))
    if _check_value_safe(db, "ph_sankrama") is not False:
        v.append("ph_sankrama: new term does not detect a dangling source_anchor_id")
    _exec(db, "INSERT INTO kala_obstruction VALUES (2, %s, 'mild')", (CANON,))
    _exec(db, "INSERT INTO phala_mitigation (chart_id, obstruction_id, obstruction_severity, linked_anchor_id) VALUES (%s, 2, 'low', gen_random_uuid())", (CANON,))
    if _check_value_safe(db, "ph_pratikara") is not False:
        v.append("ph_pratikara: new term does not detect a dangling linked_anchor_id")
    _exec(db, "UPDATE mimamsa_predictions SET confidence_band = '[0.2,1.5]'::numrange WHERE chart_id = %s", (OTHER,))
    if _check_value_safe(db, "mi_bhavisya") is not False:
        v.append("mi_bhavisya: no longer detects an out-of-range confidence band")
    _exec(db, "INSERT INTO bodha_msr_signals VALUES ('11111111-1111-4111-8111-111111111111', %s); "
              "UPDATE phala_anchors SET signal_id='11111111-1111-4111-8111-111111111111' WHERE chart_id=%s" % (repr(OTHER), repr(CANON)))
    if _check_value_safe(db, "ph_nimitta") is not False:
        v.append("ph_nimitta: no longer detects a cross-chart signal citation (C13)")
    _exec(db, "UPDATE phala_anchors SET signal_id = NULL")
    _exec(db, "INSERT INTO phala_anchors (anchor_id, chart_id) SELECT gen_random_uuid(), %s::uuid FROM generate_series(1,5)" % repr(CANON))
    if _check_value_safe(db, "ph_nimitta") is not False:
        v.append("ph_nimitta: no longer detects identity mismatches over the allowance")
    return v


def _guard_scenarios(db, sql: str) -> list[str]:
    """An unexpected base text (any of the four) must be refused BY THE PRE-CHECK and every text left alone."""
    v: list[str] = []
    for bad in TOUCHED:
        _make_fixture(db, texts={bad: "SELECT false AS integrity_passed"})
        before = _texts(db)
        try:
            _apply(db, sql)
            v.append(f"accepted an unexpected base text ({bad})")
        except Exception as exc:  # noqa: BLE001
            if "not the text this migration was written against" not in str(exc):
                v.append(f"{bad}: refused, but not by the pre-check: {str(exc).splitlines()[0]}")
        if _texts(db) != before:
            v.append(f"{bad}: overwrote a text while refusing")
    return v


def _rerun_scenario(db, sql: str) -> list[str]:
    """On the already-applied state the file must rewrite nothing (each UPDATE's own md5 guard)."""
    _make_fixture(db)
    _apply(db, _REAL)
    snap = _q(db, "SELECT asset_id, xmin::text FROM asset_registry ORDER BY 1")
    try:
        _apply(db, sql)
    except Exception as exc:  # noqa: BLE001
        return [f"re-run failed: {str(exc).splitlines()[0]}"]
    if _q(db, "SELECT asset_id, xmin::text FROM asset_registry ORDER BY 1") != snap:
        return ["re-run rewrote an already-applied row"]
    return []


def _owner_scenario(db, sql: str) -> list[str]:
    v: list[str] = []
    for asset, fragment in OWNER_FRAGMENTS:
        _make_fixture(db, owner_texts={asset: _681_by_md5(OWNER_MD5[asset]).replace(fragment, "/*removed*/")})
        before = _texts(db)
        try:
            _apply(db, sql)
            v.append(f"applied although {asset} lost its term")
        except Exception as exc:  # noqa: BLE001
            if "no longer carries its own anchor-reference term" not in str(exc):
                v.append(f"{asset}: refused for another reason: {str(exc).splitlines()[0]}")
        if _texts(db) != before:
            v.append(f"{asset}: texts changed while refusing")
    return v


def _runs_scenario(db, sql: str) -> list[str]:
    v: list[str] = []
    for asset in TOUCHED:
        _make_fixture(db)
        _exec(db, "INSERT INTO build_runs (state) VALUES ('running')")
        _exec(db, "INSERT INTO build_run_assets (run_id, asset_id) SELECT max(id), %s FROM build_runs", (asset,))
        before = _texts(db)
        try:
            _apply(db, sql)
            v.append(f"applied during an active run of {asset}")
        except Exception as exc:  # noqa: BLE001
            if "active build run" not in str(exc):
                v.append(f"{asset}: refused for another reason: {str(exc).splitlines()[0]}")
        if _texts(db) != before:
            v.append(f"{asset}: texts changed while refusing")
    return v


def _lock_scenario(db, sql: str) -> list[str]:
    _make_fixture(db)
    blocker = db()
    blocker.execute("LOCK TABLE asset_registry IN ACCESS EXCLUSIVE MODE")
    try:
        victim = db(user="amjis_app", options="-c statement_timeout=8000")
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


def _post_scenario(db, sql: str) -> list[str]:
    """The post-check is the only thing that notices an embedded target text whose md5 is not the one the file names
    (someone edited a text and forgot the md5). Edit each target in turn: the real post-check refuses all four."""
    v: list[str] = []
    edits = {
        "ph_nimitta": ("a.window_end, a.falsifier)) <= 4\n  -- C13", "a.window_end, a.falsifier)) <= 5\n  -- C13"),
        "mi_bhavisya": ("m.domain IS DISTINCT FROM p.domain) > 0", "m.domain IS DISTINCT FROM p.domain) >= 0"),
        "ph_sankrama": ("WHERE s.source_anchor_id IS NOT NULL AND a.anchor_id IS NULL\n     GROUP BY s.chart_id HAVING count(*) > 0)\n$sk$",
                        "WHERE s.source_anchor_id IS NOT NULL AND a.anchor_id IS NULL\n     GROUP BY s.chart_id HAVING count(*) > 1)\n$sk$"),
        "ph_pratikara": ("WHERE m.linked_anchor_id IS NOT NULL AND a.anchor_id IS NULL\n     GROUP BY m.chart_id HAVING count(*) > 0)\n$rk$",
                         "WHERE m.linked_anchor_id IS NOT NULL AND a.anchor_id IS NULL\n     GROUP BY m.chart_id HAVING count(*) > 1)\n$rk$"),
    }
    for tag, (needle, repl) in edits.items():
        edited = sql.replace(needle, repl, 1)
        assert edited != sql, tag
        _make_fixture(db)
        try:
            _apply(db, edited)
            v.append(f"{tag}: a target text that does not hash to the named md5 was installed silently")
        except Exception:  # noqa: BLE001
            pass
    return v


def _strip_update(sql: str, tag: str, asset: str, old: str) -> str:
    return re.sub(r"UPDATE asset_registry\nSET integrity_check_sql = \$%s\$.*?\$%s\$\nWHERE asset_id = '%s'\n  AND md5\(integrity_check_sql\) = '%s';\n"
                  % (tag, tag, asset, old), "", sql, flags=re.S)


_PH_TERM_PHALADESA_LINE = ("  AND (SELECT count(*) FROM phala_phaladesa c LEFT JOIN phala_anchors a ON a.anchor_id = c.top_anchor_id "
                           "WHERE c.top_anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0\n")
_MUTANTS = {
    # name: (mutated SQL, which scenario(s) must catch it)
    **{f"{a}_update_guard_removed": (re.sub(r"\n  AND md5\(integrity_check_sql\) = '%s';" % OLD_MD5[a], ";", _REAL), "guard") for a in TOUCHED},
    "pre_check_neutered": (_REAL.replace("ELSIF v_md5 IS DISTINCT FROM r.old_md5 THEN", "ELSIF false THEN"), "guard"),
    "owner_precondition_neutered": (_REAL.replace("IF v_txt IS NULL OR position(r.fragment IN v_txt) = 0 THEN", "IF false THEN"), "owner"),
    "active_runs_guard_neutered": (_REAL.replace("IF n_active > 0 THEN", "IF false THEN"), "runs"),
    "post_check_neutered": (_REAL.replace("IF v_md5 IS DISTINCT FROM r.new_md5 THEN\n      RAISE EXCEPTION '1259: the new", "IF false THEN\n      RAISE EXCEPTION '1259: the new"), "post"),
    "lock_timeout_removed": (_REAL.replace("SET LOCAL lock_timeout = '5s';", "", 1), "lock"),
    "lock_timeout_session_wide": (_REAL.replace("SET LOCAL lock_timeout = '5s';", "SET lock_timeout = '0';", 1), "lock"),
    "ph_update_removed": (_strip_update(_REAL, "ck", "ph_nimitta", OLD_MD5["ph_nimitta"]), "scenario"),
    "mi_update_removed": (_strip_update(_REAL, "mk", "mi_bhavisya", OLD_MD5["mi_bhavisya"]), "scenario"),
    "sk_update_removed": (_strip_update(_REAL, "sk", "ph_sankrama", OLD_MD5["ph_sankrama"]), "scenario"),
    "pr_update_removed": (_strip_update(_REAL, "rk", "ph_pratikara", OLD_MD5["ph_pratikara"]), "scenario"),
    "ph_new_text_swapped_for_the_old": (_REAL.replace(_new("ph_nimitta"), _old("ph_nimitta")), "post_or_scenario"),
}


def test_mutants_are_real_mutations_of_the_real_file():
    for name, (sql, _) in _MUTANTS.items():
        assert sql != _REAL, f"mutant {name} did not change the file (the mutation pattern is stale)"


def test_the_real_file_produces_no_violations(db):
    assert _scenario(db, _REAL) == []
    assert _guard_scenarios(db, _REAL) == []
    assert _rerun_scenario(db, _REAL) == []
    assert _owner_scenario(db, _REAL) == []
    assert _runs_scenario(db, _REAL) == []
    assert _lock_scenario(db, _REAL) == []
    assert _post_scenario(db, _REAL) == []


@pytest.mark.parametrize("name", sorted(_MUTANTS))
def test_every_mutant_is_caught(db, name):
    sql, kind = _MUTANTS[name]
    if kind == "guard":
        v = _guard_scenarios(db, sql) + _rerun_scenario(db, sql)
    elif kind == "owner":
        v = _owner_scenario(db, sql)
    elif kind == "runs":
        v = _runs_scenario(db, sql)
    elif kind == "lock":
        v = _lock_scenario(db, sql)
    elif kind == "post":
        v = _post_scenario(db, sql)
    else:
        v = _scenario(db, sql)
    assert v, f"mutant {name} was NOT caught"


def test_a_widened_ph_nimitta_text_is_caught_by_the_semantic_scenario(db):
    """Mutating the TARGET text itself (not just the file's guards): if the new ph_nimitta text dropped its identity check or
    kept the phaladesa term, the scenario must say so."""
    for label, mutate in (("identity check dropped", lambda t: re.sub(r"\(SELECT count\(\*\) FROM phala_anchors a\s+WHERE a\.anchor_id <> phala_anchor_identity.*?<= 4\n  -- C13", "(SELECT 1) = 1\n  -- C13", t, flags=re.S)),
                          ("phaladesa term kept", lambda t: t.replace("  -- C13 /", _PH_TERM_PHALADESA_LINE + "  -- C13 /", 1))):
        new_t = _new("ph_nimitta")
        mut_t = mutate(new_t)
        assert mut_t != new_t, label
        mutated_sql = _REAL.replace(new_t, mut_t).replace(NEW_MD5["ph_nimitta"], _md5(mut_t))
        assert mutated_sql != _REAL
        v = _scenario(db, mutated_sql)
        assert v, f"mutated target text ({label}) was NOT caught"
