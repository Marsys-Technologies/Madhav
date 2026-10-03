"""
Migration 1259 (Suvarna, SS rulings N-99 / Q-L4-02, widened by N-104): the registry integrity_check_sql of BOTH
ph_nimitta (L4) and mi_bhavisya (L5) loses its one global dangling-anchor term ("an integrity check must claim only
what its own writer produces"). HELD: own draft PR, merges only after S-L1 and only on SS's review.

Two tiers:
  * STATIC (always runs, DB-free): file shape, guards, header sections; each OLD text is rebuilt from the repository's
    own migrations (ph_nimitta: 680 + 683; mi_bhavisya: 691) and must hash to the live production md5; each NEW text must
    hash to the md5 the migration names AND must equal its OLD text minus exactly the one term (comments aside); every
    other conjunct must still be there.
  * LIVE (needs PostgreSQL server binaries): applies the REAL migration file to a DISPOSABLE cluster this module
    creates with initdb in a temp dir (unix socket only, trust auth, removed at session end). It never connects to
    anything else. Skipped, loudly, when no initdb/pg_ctl (or no uuid-ossp) is found; REQUIRE_PG_BINARIES=1 turns
    that skip into a failure. Set PG_BIN to pin a version (production is PostgreSQL 15).

The LIVE fixture carries the REAL trigger function body and trigger definition of nirmana_registry_receipt_invalidation
(read from production 2026-10-03), the production definition of phala_anchor_identity(), and a minimal copy of every
table either check reads. What it proves: apply/guard/idempotency behaviour; the serving effect the header states
(only the two assets' freshness rows go stale, nothing else moves); and the SEMANTICS for both assets: the OLD text is
false on 135 dangling frozen predictions while the NEW text is true, and each NEW text still goes false on every other
kind of corruption (only the one term was weakened). A mutation section rewrites the real SQL and requires every
mutant to be caught. It does NOT prove production state (read from production structure after deploy; Trap 103).
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
_M1259 = _MIG / "1259_integrity_checks_claim_only_own_family_ph_nimitta_mi_bhavisya.sql"
_M680 = _MIG / "680_phala_anchor_deterministic_identity.sql"
_M683 = _MIG / "683_phala_anchor_signal_id_disposition.sql"
_M691 = _MIG / "691_nirmana_l5_w3_integrity_contracts.sql"

PH_OLD_MD5, PH_NEW_MD5, PH_OLD_LEN, PH_NEW_LEN = "658ffdbcb6d531e8cf5eed6c5260a966", "45192b2752989dc4398d81c0135e1473", 3063, 3167
MI_OLD_MD5, MI_NEW_MD5, MI_OLD_LEN, MI_NEW_LEN = "19b5ea334236eaffa493069a7d4b318b", "8e88e9d4ed07f47cdcecc7861fc8516d", 2186, 1951
PH_TERM = ("AND (SELECT count(*) FROM mimamsa_predictions p LEFT JOIN phala_anchors a ON "
           "a.anchor_id::text = p.source_pramana_id WHERE p.source_pramana_id IS NOT NULL AND a.anchor_id IS NULL) = 0")
MI_TERM = ("OR count(*) FILTER (WHERE p.prediction_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM phala_anchors a "
           "WHERE a.chart_id = p.chart_id AND a.anchor_id::text = p.source_pramana_id)) > 0")
CANON = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
THIRD = "00000000-0000-4000-8000-0000000000a1"
CHARTS = [CANON, OTHER, THIRD]
ASSETS = ["ph_nimitta", "mi_bhavisya"]
NEW_MD5 = {"ph_nimitta": PH_NEW_MD5, "mi_bhavisya": MI_NEW_MD5}
OLD_MD5 = {"ph_nimitta": PH_OLD_MD5, "mi_bhavisya": MI_OLD_MD5}


# -- helpers ----------------------------------------------------------------

def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("--"))


def _flat(path: Path) -> str:
    return re.sub(r"\s+", " ", re.sub(r"^--", " ", path.read_text(), flags=re.M))


def _ph_old() -> str:
    """Migration 680's check body + migration 683's appended C13 conjunct = the live production text."""
    a = re.search(r"\$check\$(.*?)\$check\$", _M680.read_text(), re.S).group(1)
    b = re.search(r"\$add\$(.*?)\$add\$", _M683.read_text(), re.S).group(1)
    return a + b


def _mi_old() -> str:
    for m in re.finditer(r"\$check\$(.*?)\$check\$", _M691.read_text(), re.S):
        if "FULL JOIN mimamsa_manifestation_sets" in m.group(1):
            return m.group(1)
    raise AssertionError("mi_bhavisya check not found in migration 691")


def _ph_new(sql: str | None = None) -> str:
    return re.search(r"\$ck\$(.*)\$ck\$", sql or _M1259.read_text(), re.S).group(1)


def _mi_new(sql: str | None = None) -> str:
    return re.search(r"\$mk\$(.*)\$mk\$", sql or _M1259.read_text(), re.S).group(1)


def _exec_only(sql: str) -> str:
    """Executable text: SQL comments dropped, whitespace collapsed."""
    return re.sub(r"\s+", " ", re.sub(r"--[^\n]*", "", sql)).strip()


# -- STATIC tier --------------------------------------------------------------

def test_old_texts_rebuilt_from_the_repo_migrations_are_the_live_production_texts():
    for old, md5, n in ((_ph_old(), PH_OLD_MD5, PH_OLD_LEN), (_mi_old(), MI_OLD_MD5, MI_OLD_LEN)):
        assert hashlib.md5(old.encode()).hexdigest() == md5 and len(old) == n


def test_new_texts_have_the_named_md5_and_length():
    for new, md5, n in ((_ph_new(), PH_NEW_MD5, PH_NEW_LEN), (_mi_new(), MI_NEW_MD5, MI_NEW_LEN)):
        assert hashlib.md5(new.encode()).hexdigest() == md5 and len(new) == n


def test_ph_nimitta_new_text_is_the_old_text_minus_exactly_the_mimamsa_term():
    old, new = _exec_only(_ph_old()), _exec_only(_ph_new())
    assert old.count(PH_TERM) == 1 and PH_TERM not in new
    assert new == old.replace(" " + PH_TERM, "", 1), "executable text differs by more than the one term"
    assert "mimamsa_predictions" not in new
    for table in ("phala_suddha_sodhana", "phala_sodhana", "phala_pramana", "phala_sankrama", "phala_muhurta",
                  "phala_mitigation", "phala_phaladesa", "bodha_msr_signals"):
        assert table in new, table
    assert "phala_anchor_identity(" in new and "<= 4" in new and "HAVING count(*) > 1" in new
    assert new.count("(SELECT count(*) FROM") == old.count("(SELECT count(*) FROM") - 1
    assert "7 columns THIS ASSET'S OWN FAMILY" in _ph_new() and "8 columns" not in _ph_new()


def test_mi_bhavisya_new_text_is_the_old_text_minus_exactly_the_dangling_anchor_branch():
    old, new = _exec_only(_mi_old()), _exec_only(_mi_new())
    assert old.count(MI_TERM) == 1 and MI_TERM not in new
    assert new == old.replace(" " + MI_TERM, "", 1), "executable text differs by more than the one branch"
    assert "phala_anchors" not in new and "source_pramana_id" not in new
    assert _mi_new() == _mi_old().replace(
        "        OR count(*) FILTER (WHERE p.prediction_id IS NOT NULL\n               AND NOT EXISTS (SELECT 1 FROM phala_anchors a\n"
        "                                WHERE a.chart_id = p.chart_id AND a.anchor_id::text = p.source_pramana_id)) > 0\n", "")
    # every other mi_bhavisya conjunct survives
    for needle in ("FULL JOIN mimamsa_manifestation_sets", "LEFT JOIN charts c", "observation_window", "confidence_band",
                   "frozen_bundle_hash", "bundle_formula_version", "outcome_claim", "falsifier_jsonb", "driving_signals",
                   "m.domain IS DISTINCT FROM p.domain", "citation_ref", "channel_id",
                   "count(DISTINCT prediction_id) <> count(*)", "count(DISTINCT (prediction_id, channel_id)) <> count(*)"):
        assert needle in new, needle


def test_migration_does_not_own_the_transaction_and_starts_with_lock_timeout():
    code = _code(_M1259)
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code), "migrate.ts owns the transaction"
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert not re.search(r"^\s*(DROP|TRUNCATE|DELETE\s+FROM|REVOKE|GRANT|ALTER|CREATE|INSERT)\b", code, re.I | re.M)
    assert "$pre$" in code and "$post$" in code


def test_migration_is_two_guarded_updates_of_one_column_each_of_exactly_two_rows():
    code = _code(_M1259)
    assert len(re.findall(r"\bUPDATE asset_registry\b", code)) == 2
    assert re.findall(r"\bSET integrity_check_sql\s*=", code) == ["SET integrity_check_sql ="] * 2
    assert not re.search(r"\bSET\s+(?!integrity_check_sql)[a-z_]+\s*=", code.split("$pre$")[-1].split("$post$")[0].replace(_ph_new(), "").replace(_mi_new(), ""), re.I)
    for asset in ASSETS:
        assert f"WHERE asset_id = '{asset}'" in code
        assert f"AND md5(integrity_check_sql) = '{OLD_MD5[asset]}';" in code
        assert code.count(OLD_MD5[asset]) == 2, "pre-check list + UPDATE guard name the base md5"
        assert code.count(NEW_MD5[asset]) == 2, "pre-check list + post-check list name the target md5"
    assert "ga_" not in code and "ph_rectification" not in code


def test_header_states_serving_effect_for_both_assets_trigger_ordering_readbacks_and_what_is_not_done():
    sql = _flat(_M1259)
    for needle in ("SERVING EFFECT AT APPLY", "nirmana_registry_receipt_invalidation",
                   "AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, "
                   "target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table",
                   "old.* IS DISTINCT FROM new.*", "Affected assets: ph_nimitta and mi_bhavisya, and no others",
                   "0 belong to any ph_* asset", "mi_jivanaghatana, mi_kula, mi_vistara",
                   "HELD", "AFTER S-L1", "on SS's review", "IDEMPOTENT SHAPE", "ROLLBACK", "suvarna_reader",
                   "VERIFICATION BY PRODUCTION STRUCTURE", "NOT DONE HERE", "0 ACTIVE RUNS AT APPLY",
                   "no EXECUTE on phala_anchor_identity", "STILL FALSE", "phala_phaladesa.top_anchor_id",
                   "135", "OLD text: FALSE", "NEW text: STILL FALSE", "(a7)", "migration 680", "migration 691",
                   "Q-L4-02", "N-104", "#3023",
                   "OLD (md5 19b5ea33...) = false; NEW (md5 8e88e9d4...) = true",
                   PH_NEW_MD5, PH_OLD_MD5, MI_NEW_MD5, MI_OLD_MD5):
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
CREATE TABLE charts (id uuid PRIMARY KEY);
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

_LIVE_CHECK_ASSETS = {"ph_nimitta": "ph", "mi_bhavisya": "mi"}


def _make_fixture(connect, *, ph_text: str | None = None, mi_text: str | None = None, with_rows: bool = True):
    texts = {"ph_nimitta": _ph_old() if ph_text is None else ph_text,
             "mi_bhavisya": _mi_old() if mi_text is None else mi_text}
    with connect() as c:
        c.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public")  # scenarios reuse one database
        c.execute(_DDL)
        c.execute(_IDENTITY_FN)
        if with_rows:
            for i, aid in enumerate(("ph_nimitta", "mi_bhavisya", "ph_pramana", "mi_kula", "ga_vargas")):
                check = texts.get(aid, f"SELECT true -- {aid}")
                c.execute("INSERT INTO asset_registry (asset_id, layer, sort_order, english_name, integrity_check_sql) "
                          "VALUES (%s, %s, %s, %s, %s)", (aid, aid.split("_")[0], i, aid.upper(), check))
        c.execute(_TRIGGER_FN)
        c.execute(_TRIGGER_DEF)
        if with_rows:
            for aid in ("ph_nimitta", "mi_bhavisya", "ph_pramana", "mi_kula", "ga_vargas"):
                for chart in CHARTS:
                    c.execute("INSERT INTO asset_freshness (asset_id, chart_id, scope_key, partition_key, freshness_state, "
                              "receipt_version, observed_at) VALUES (%s, %s, %s, 'default', 'fresh', 'v1', '2026-10-01T00:00:00Z')",
                              (aid, chart, f"chart:{chart}"))
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
    """A consistent L4/L5 family: 3 anchors per chart (ids = phala_anchor_identity), one pramana + sodhana per anchor,
    one prediction (+ manifestation set) per anchor, all resolving; optionally N valid predictions citing anchors that do
    not exist (the 135 case)."""
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


def _registry_other_than_the_two(connect):
    return _q(connect, "SELECT asset_id, to_jsonb(r)::text FROM asset_registry r WHERE asset_id NOT IN ('ph_nimitta','mi_bhavisya') ORDER BY 1")


def _md5(connect, aid):
    return _q(connect, "SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id=%s", (aid,))[0][0]


def test_fixture_both_old_checks_are_true_on_clean_data_and_both_new_checks_agree(db):
    _make_fixture(db)
    _seed_clean_data(db)
    assert _check_value(db, "ph_nimitta") is True and _check_value(db, "mi_bhavisya") is True
    _apply(db, _M1259.read_text())
    assert _check_value(db, "ph_nimitta") is True and _check_value(db, "mi_bhavisya") is True


def test_old_texts_are_false_on_135_dangling_frozen_predictions_new_texts_are_true(db):
    """The production situation: 135 frozen L5 predictions cite vanished anchors; everything else is consistent."""
    _make_fixture(db)
    _seed_clean_data(db, dangling_predictions=135)
    assert _check_value(db, "ph_nimitta") is False, "OLD ph_nimitta text must be false on dangling L5 references"
    assert _check_value(db, "mi_bhavisya") is False, "OLD mi_bhavisya text must be false on dangling L4 references"
    assert _q(db, "SELECT count(*) FROM mimamsa_predictions p LEFT JOIN phala_anchors a ON a.anchor_id::text = p.source_pramana_id "
                  "WHERE a.anchor_id IS NULL")[0][0] == 135
    _apply(db, _M1259.read_text())
    assert _md5(db, "ph_nimitta") == PH_NEW_MD5 and _md5(db, "mi_bhavisya") == MI_NEW_MD5
    assert _check_value(db, "ph_nimitta") is True, "NEW ph_nimitta text must not be judged by frozen L5 rows"
    assert _check_value(db, "mi_bhavisya") is True, "NEW mi_bhavisya text must not be judged by L4's anchors"


def test_mi_bhavisya_old_text_is_also_false_when_the_anchor_exists_on_another_chart_only(db):
    """The removed branch is chart-scoped (a.chart_id = p.chart_id): an anchor id that exists only on another chart
    counts as dangling for the prediction. The new text does not look at phala_anchors at all."""
    _make_fixture(db)
    _seed_clean_data(db)
    with db() as c:
        other_anchor = c.execute("SELECT anchor_id::text FROM phala_anchors WHERE chart_id=%s LIMIT 1", (OTHER,)).fetchone()[0]
        _add_prediction(c, CANON, other_anchor)
        c.commit()
    assert _check_value(db, "mi_bhavisya") is False
    _apply(db, _M1259.read_text())
    assert _check_value(db, "mi_bhavisya") is True


# Every other kind of corruption must still turn the NEW texts false: only the one term was removed.
_PH_STILL_RED = {
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
def test_ph_nimitta_new_text_still_goes_false_on_every_other_corruption(db, name):
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


def test_apply_installs_both_new_texts_and_stales_exactly_those_two_assets_rows(db):
    _make_fixture(db)
    other_before = _registry_other_than_the_two(db)
    fresh_before = {(a, c): (s, r, o) for a, c, s, r, o in _freshness(db)}
    _apply(db, _M1259.read_text())
    assert _md5(db, "ph_nimitta") == PH_NEW_MD5 and _md5(db, "mi_bhavisya") == MI_NEW_MD5
    assert _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ph_nimitta'")[0][0] == _ph_new()
    assert _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='mi_bhavisya'")[0][0] == _mi_new()
    rows = _freshness(db)
    stale = {(a, c) for a, c, s, r, o in rows if s == "stale"}
    assert stale == {(a, ch) for a in ASSETS for ch in CHARTS}, "both assets stale on EVERY chart row they have, nothing else"
    for a, c, s, r, o in rows:
        if a in ASSETS:
            assert "registry_changed" in r
        else:
            assert (s, r, o) == fresh_before[(a, c)], f"{a} freshness changed"
    assert _registry_other_than_the_two(db) == other_before, "another registry row changed"
    for aid in ASSETS:
        row = _q(db, "SELECT to_jsonb(r) - 'integrity_check_sql' FROM asset_registry r WHERE asset_id=%s", (aid,))[0][0]
        assert row["is_active"] is True and row["layer"] == aid.split("_")[0], "only integrity_check_sql changed"


def test_apply_with_no_freshness_rows_for_the_two_assets_changes_no_freshness(db):
    """Production today: asset_freshness has no row for any ph_* asset nor for mi_bhavisya, so the trigger updates nothing."""
    _make_fixture(db)
    _exec(db, "DELETE FROM asset_freshness WHERE asset_id IN ('ph_nimitta', 'mi_bhavisya')")
    before = _freshness(db)
    _apply(db, _M1259.read_text())
    assert _freshness(db) == before
    assert _md5(db, "ph_nimitta") == PH_NEW_MD5 and _md5(db, "mi_bhavisya") == MI_NEW_MD5


@pytest.mark.parametrize("bad", ASSETS)
def test_md5_guard_refuses_an_unexpected_text_for_either_asset_and_changes_nothing(db, bad):
    kw = {"ph_text": "SELECT false AS integrity_passed"} if bad == "ph_nimitta" else {"mi_text": "SELECT false AS integrity_passed"}
    _make_fixture(db, **kw)
    fresh, reg = _freshness(db), _registry_other_than_the_two(db)
    before = {a: _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id=%s", (a,))[0][0] for a in ASSETS}
    with pytest.raises(Exception) as ei:
        _apply(db, _M1259.read_text())
    assert "1259" in str(ei.value) and bad in str(ei.value) and "not the text this migration was written against" in str(ei.value), str(ei.value)
    after = {a: _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id=%s", (a,))[0][0] for a in ASSETS}
    assert after == before, "the OTHER asset must not be updated when one is refused"
    assert _freshness(db) == fresh and _registry_other_than_the_two(db) == reg


@pytest.mark.parametrize("asset", ASSETS)
def test_refuses_a_missing_registry_row(db, asset):
    _make_fixture(db)
    _exec(db, "DELETE FROM asset_registry WHERE asset_id=%s", (asset,))
    with pytest.raises(Exception) as ei:
        _apply(db, _M1259.read_text())
    assert f"expected exactly one {asset} registry row" in str(ei.value), str(ei.value)


def test_partial_state_one_asset_already_applied_applies_the_other(db):
    _make_fixture(db, ph_text=_ph_new())
    _apply(db, _M1259.read_text())
    assert _md5(db, "ph_nimitta") == PH_NEW_MD5 and _md5(db, "mi_bhavisya") == MI_NEW_MD5


def test_idempotent_second_run_rewrites_nothing_and_does_not_fire_the_trigger(db):
    _make_fixture(db)
    _apply(db, _M1259.read_text())
    _exec(db, "UPDATE asset_freshness SET freshness_state='fresh', reasons='[]'::jsonb, observed_at='2026-10-02T00:00:00Z' "
              "WHERE asset_id IN ('ph_nimitta', 'mi_bhavisya')")
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

_REAL = _M1259.read_text()


def _scenario(db, sql: str) -> list[str]:
    """Violations of the contract when `sql` (a possibly mutated migration) is applied to a fresh production-shaped fixture."""
    v: list[str] = []
    _make_fixture(db)
    _seed_clean_data(db, dangling_predictions=135)
    fresh_other = [r for r in _freshness(db) if r[0] not in ASSETS]
    try:
        _apply(db, sql)
    except Exception as exc:  # noqa: BLE001
        return [f"apply failed: {str(exc).splitlines()[0]}"]
    for aid in ASSETS:
        if _md5(db, aid) != NEW_MD5[aid]:
            v.append(f"{aid}: new md5 not installed ({_md5(db, aid)})")
        if _check_value_safe(db, aid) is not True:
            v.append(f"{aid}: new check is not true on the 135-dangling case")
    if [r for r in _freshness(db) if r[0] not in ASSETS] != fresh_other:
        v.append("another asset's freshness moved")
    # corruptions each new text must still see
    _exec(db, "INSERT INTO phala_phaladesa VALUES (gen_random_uuid())")
    if _check_value_safe(db, "ph_nimitta") is not False:
        v.append("ph_nimitta: no longer detects a dangling phala_phaladesa.top_anchor_id")
    _exec(db, "UPDATE mimamsa_predictions SET confidence_band = '[0.2,1.5]'::numrange WHERE chart_id = %s", (OTHER,))
    if _check_value_safe(db, "mi_bhavisya") is not False:
        v.append("mi_bhavisya: no longer detects an out-of-range confidence band")
    _exec(db, "UPDATE mimamsa_manifestation_sets SET domain = 'health' WHERE chart_id = %s", (CANON,))
    return v


def _guard_scenarios(db, sql: str) -> list[str]:
    """An unexpected base text (either asset) must be refused BY THE PRE-CHECK and left alone."""
    v: list[str] = []
    for kw in ({"ph_text": "SELECT false AS integrity_passed"}, {"mi_text": "SELECT false AS integrity_passed"}):
        _make_fixture(db, **kw)
        before = {a: _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id=%s", (a,))[0][0] for a in ASSETS}
        try:
            _apply(db, sql)
            v.append(f"accepted an unexpected base text ({list(kw)[0]})")
        except Exception as exc:  # noqa: BLE001
            if "not the text this migration was written against" not in str(exc):
                v.append(f"refused, but not by the pre-check: {str(exc).splitlines()[0]}")
        after = {a: _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id=%s", (a,))[0][0] for a in ASSETS}
        if after != before:
            v.append("overwrote a text while refusing")
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


def _post_scenario(db, sql: str) -> list[str]:
    """The post-check is the only thing that notices an embedded target text whose md5 is not the one the file names
    (someone edited a text and forgot the md5). Edit each target in turn: the real post-check refuses both."""
    v: list[str] = []
    edits = {
        "ph": ("(SELECT count(*) FROM phala_sodhana c LEFT JOIN phala_anchors a USING (anchor_id) WHERE c.anchor_id IS NOT NULL "
               "AND a.anchor_id IS NULL) = 0", "(SELECT count(*) FROM phala_sodhana c LEFT JOIN phala_anchors a USING (anchor_id) "
               "WHERE c.anchor_id IS NOT NULL AND a.anchor_id IS NULL) >= 0"),
        "mi": ("m.domain IS DISTINCT FROM p.domain) > 0", "m.domain IS DISTINCT FROM p.domain) >= 0"),
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


_MUTANTS = {
    # name: (mutated SQL, which scenario must catch it)
    "ph_update_guard_removed": (re.sub(r"\n  AND md5\(integrity_check_sql\) = '%s';" % PH_OLD_MD5, ";", _REAL), "guard"),
    "mi_update_guard_removed": (re.sub(r"\n  AND md5\(integrity_check_sql\) = '%s';" % MI_OLD_MD5, ";", _REAL), "guard"),
    "pre_check_neutered": (_REAL.replace("ELSIF v_md5 IS DISTINCT FROM r.old_md5 THEN", "ELSIF false THEN"), "guard"),
    "post_check_neutered": (_REAL.replace("IF v_md5 IS DISTINCT FROM r.new_md5 THEN\n      RAISE EXCEPTION '1259: the new", "IF false THEN\n      RAISE EXCEPTION '1259: the new"), "post"),
    "lock_timeout_removed": (_REAL.replace("SET LOCAL lock_timeout = '5s';", "", 1), "lock"),
    "lock_timeout_session_wide": (_REAL.replace("SET LOCAL lock_timeout = '5s';", "SET lock_timeout = '0';", 1), "lock"),
    "ph_removal_widened_to_phaladesa": (
        _REAL.replace("  AND (SELECT count(*) FROM phala_phaladesa c LEFT JOIN phala_anchors a ON a.anchor_id = c.top_anchor_id "
                      "WHERE c.top_anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0\n", ""), "scenario"),
    "mi_removal_widened_to_confidence_band": (
        _REAL.replace("        OR count(*) FILTER (WHERE p.prediction_id IS NOT NULL\n               AND (p.confidence_band IS NULL OR isempty(p.confidence_band)\n"
                      "                    OR lower(p.confidence_band) < 0 OR upper(p.confidence_band) > 1)) > 0\n", ""), "scenario"),
    "mi_update_removed": (re.sub(r"UPDATE asset_registry\nSET integrity_check_sql = \$mk\$.*?\$mk\$\nWHERE asset_id = 'mi_bhavisya'\n  AND md5\(integrity_check_sql\) = '%s';\n" % MI_OLD_MD5, "", _REAL, flags=re.S), "scenario"),
    "ph_update_removed": (re.sub(r"UPDATE asset_registry\nSET integrity_check_sql = \$ck\$.*?\$ck\$\nWHERE asset_id = 'ph_nimitta'\n  AND md5\(integrity_check_sql\) = '%s';\n" % PH_OLD_MD5, "", _REAL, flags=re.S), "scenario"),
}


def test_mutants_are_real_mutations_of_the_real_file():
    for name, (sql, _) in _MUTANTS.items():
        assert sql != _REAL, f"mutant {name} did not change the file (the mutation pattern is stale)"


def test_the_real_file_produces_no_violations(db):
    assert _scenario(db, _REAL) == []
    assert _guard_scenarios(db, _REAL) == []
    assert _rerun_scenario(db, _REAL) == []
    assert _lock_scenario(db, _REAL) == []
    assert _post_scenario(db, _REAL) == []


@pytest.mark.parametrize("name", sorted(_MUTANTS))
def test_every_mutant_is_caught(db, name):
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


@pytest.mark.parametrize("asset", ASSETS)
def test_a_file_whose_target_is_the_old_text_is_refused_by_the_post_check(db, asset):
    """A file that swapped a target text for the OLD one (the term still present) cannot apply: the post-check names the NEW md5."""
    new, old = (_ph_new(), _ph_old()) if asset == "ph_nimitta" else (_mi_new(), _mi_old())
    bad = _REAL.replace(new, old)
    assert bad != _REAL
    _make_fixture(db)
    _seed_clean_data(db, dangling_predictions=135)
    with pytest.raises(Exception) as ei:
        _apply(db, bad)
    assert "did not take" in str(ei.value) and asset in str(ei.value)
