"""
Migration 1254: ga_sensitive integrity_check_sql conjunct (a) vocabulary relaxation
({two_pass_verified, floored} -> {two_pass_verified, floored, single, computed_extension}).
HELD: it merges only in the S-L1 window W1 (it must apply BEFORE the ga_sensitive rebuild in W4/W6).

Two tiers:
  * STATIC (always runs, DB-free): file shape, guards, header sections, the md5 of the base text (= migration
    743's body) and of the target text, and the proof that the target differs from the base ONLY inside
    conjunct (a) (the vocabulary list and the comment sentence that would otherwise be false).
  * LIVE (needs PostgreSQL server binaries): applies the REAL on-disk migration file to DISPOSABLE clusters this
    module creates with initdb in a temp dir (own port, trust auth, removed at session end), once per available
    major version (PostgreSQL 15 and 17 when both are installed; production is 15). It never connects to
    anything else. Skipped, loudly, when no `initdb`/`pg_ctl` is found (looked up via $PG_BIN, PATH, homebrew,
    /usr/lib/postgresql/*/bin).

The LIVE fixture carries the REAL trigger function body and trigger definition of
`nirmana_registry_receipt_invalidation` (read from production 2026-10-02 as suvarna_reader with
pg_get_functiondef / pg_get_triggerdef) and the live column set, constraints and indexes of asset_registry and
asset_freshness, so what is proved is the serving effect the migration header states: ga_sensitive freshness goes
stale on EVERY chart and nothing else moves. It does NOT prove production state (that is read from production
structure after deploy; Trap 103).

MUTATIONS: every guard of the migration has a mutant (pre-guard neutered, UPDATE without the md5 WHERE, vocabulary
widened, vocabulary narrowed, lock_timeout removed, post-check neutered); each mutant must turn the specific check
that guards against it RED, while the same check is GREEN on the real file.
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
_M1254 = _MIG / "1254_nirmana_l1_ga_sensitive_integrity_tier_vocabulary.sql"
_M743 = _MIG / "743_nirmana_l1_ga_sensitive_integrity_contract.sql"

BASE_MD5 = "77099c39ae07a2dfb18c8812d9345c2d"
NEW_MD5 = "d6dc29259125e4007c3506a42d983296"
OLD_LIST = "AND verification_pass_status NOT IN ('two_pass_verified', 'floored')"
NEW_LIST = "AND verification_pass_status NOT IN ('two_pass_verified', 'floored', 'single', 'computed_extension')"
ALLOWED = ["two_pass_verified", "floored", "single", "computed_extension"]
# every tier in the production CHECK vocabulary of chart_facts.verification_pass_status that is NOT one of the four
REFUSED = ["classical_match", "divergent_flagged", "single_pass", "documented_approximation",
           "not_defined_for_nodes", "scope_cap_sentinel", "skipped_malformed_source",
           "external_computation_required", "pending_w3_verification"]
EXPLICIT_CATEGORIES = [
    "upagraha_position", "saturn_derived_point", "saham_position", "karaka_chara_position", "karakamsa_position",
    "swamsa_position", "arudha_pada", "midpoint", "aprakasha_position", "lal_kitab_special_point",
    "maharsi_specific_point", "bhrigu_nadi_point", "sensitive_point_gulika_mandi", "sun_derived_upagraha",
    "special_lagna", "nakshatra_pada_sensitive", "kp_ruling_planets_natal", "kp_cuspal_significators",
]
FAMILY_CATEGORIES = ["esoteric_point_mrityu", "tajik_hadda_lord", "bhava_arudha"]
IN_SCOPE = EXPLICIT_CATEGORIES + FAMILY_CATEGORIES
CANON = "482012f1-710e-4a25-994a-93821f5871aa"


# ── helpers ──────────────────────────────────────────────────────────────────

def _code(text: str) -> str:
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("--"))


def _flat(text: str) -> str:
    """Header comments with the `-- ` prefixes removed and whitespace collapsed (needles span wrapped lines)."""
    return re.sub(r"\s+", " ", re.sub(r"^--", " ", text, flags=re.M))


def _file() -> str:
    return _M1254.read_text(encoding="utf-8")


def _base_check() -> str:
    return re.search(r"\$ck\$(.*?)\$ck\$", _M743.read_text(encoding="utf-8"), re.S).group(1)


def _new_check(text: str | None = None) -> str:
    return re.search(r"\$ck\$(.*)\$ck\$", _file() if text is None else text, re.S).group(1)


def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


# ── STATIC tier ──────────────────────────────────────────────────────────────

def test_file_does_not_own_the_transaction_and_starts_with_lock_timeout():
    text = _file()
    code = _code(text)
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code), "migrate.ts owns the transaction"
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';"), code.strip()[:80]
    outside = code.split("$ck$")[0] + code.split("$ck$")[-1]
    assert not re.search(r"^\s*(DROP|TRUNCATE|DELETE\s+FROM|REVOKE|GRANT|ALTER|CREATE|INSERT)\b", outside, re.I | re.M)
    flat = _flat(text)
    for needle in ("SERVING EFFECT AT APPLY", "ORDERING", "HELD", "BEFORE the ga_sensitive rebuild in W4/W6",
                   "VERIFICATION BY PRODUCTION STRUCTURE", "IDEMPOTENT SHAPE", "ROLLBACK", "suvarna_reader",
                   "S-L1 window W1", "NEVER EDIT THIS FILE AFTER IT HAS BEEN APPLIED", "nirmana_registry_receipt_invalidation",
                   "ON EVERY CHART", "UNRESOLVED", "receipt_not_fresh", "1219", "1221", "1222", "1223", "1226",
                   "{ga_structural (1221), ga_vargas (1222, 1223, 1226), ga_dashas (1226), ga_yoga (1226), ga_sensitive (1254)}",
                   "FIVE assets", "two_pass_verified MUST stay", "single_pass is NOT needed",
                   "divergent_flagged, pending_*, classical_match and documented_approximation are NOT in the vocabulary"):
        assert needle.lower() in flat.lower(), f"1254 header no longer states: {needle}"
    assert "$pre$" in text and "$post$" in text
    assert text.count("$ck$") == 2, "$ck$ must appear exactly twice (the body delimiters), never in comments"


def test_base_text_is_migration_743s_body_and_the_target_is_pinned():
    base, new = _base_check(), _new_check()
    assert _md5(base) == BASE_MD5 and len(base) == 3069
    assert _md5(new) == NEW_MD5 and len(new) == 3303
    code = _code(_file())
    assert code.count(BASE_MD5) == 3, "pre-check (accept) + UPDATE guard + post-check name the base md5"
    assert code.count(NEW_MD5) == 2, "pre-check (already applied) + post-check name the target md5"


def test_target_differs_from_the_base_only_inside_conjunct_a():
    base, new = _base_check(), _new_check()
    assert base.count(OLD_LIST) == 1 and new.count(NEW_LIST) == 1 and OLD_LIST not in new
    # (b) and (c) are byte-identical: everything from the end of conjunct (a) onward
    tail = lambda s: s[s.index("  -- (b) special_lagna's sign_lord"):]
    assert tail(base) == tail(new), "conjuncts (b) and (c) must be byte-identical"
    # the head before conjunct (a) is byte-identical too
    head = lambda s: s[:s.index("  -- (a) verification_pass_status vocabulary")]
    assert head(base) == head(new)
    # undoing exactly the two (a) fragments reproduces the base
    post = re.search(r"\$post\$.*\$post\$", _file(), re.S).group(0)
    frags = re.findall(r"\$f\$(.*?)\$f\$", post, re.S)
    assert len(frags) == 4 and frags[0] == NEW_LIST and frags[1] == OLD_LIST
    assert new.replace(frags[0], frags[1]).replace(frags[2], frags[3]) == base
    # the (a) vocabulary is an explicit list of exactly four tiers
    listed = re.search(r"verification_pass_status NOT IN \(([^)]*)\)", new).group(1)
    assert re.findall(r"'([a-z_]+)'", listed) == ALLOWED
    for refused in REFUSED:
        assert refused not in listed


def test_is_one_guarded_update_of_one_column_of_one_row():
    code = _code(_file())
    assert len(re.findall(r"\bUPDATE asset_registry\b", code)) == 1
    assert re.findall(r"\bSET\s+([a-z_]+)\s*=", code.split("$ck$")[0], re.I) == ["integrity_check_sql"]
    tail = code.split("$ck$")[-1]
    assert "WHERE asset_id = 'ga_sensitive'" in tail and f"md5(integrity_check_sql) = '{BASE_MD5}'" in tail


def test_the_number_1254_file_follows_the_pattern():
    # No sibling-uniqueness assertion (always-armed); migration_number_guard.test.ts owns number uniqueness.
    assert _M1254.name.startswith("1254_")
    assert _M1254.is_file()


# ── LIVE tier: disposable PostgreSQL (every available major version) ──────────

def _pg_bins() -> list[tuple[str, Path]]:
    cands: list[Path] = []
    if os.environ.get("PG_BIN"):
        cands.append(Path(os.environ["PG_BIN"]))
    which = shutil.which("initdb")
    if which:
        cands.append(Path(which).parent)
    cands += [Path(p) for p in sorted(glob.glob("/opt/homebrew/opt/postgresql@*/bin"), reverse=True)]
    cands += [Path(p) for p in sorted(glob.glob("/usr/lib/postgresql/*/bin"), reverse=True)]
    seen: dict[str, Path] = {}
    for c in cands:
        if (c / "initdb").exists() and (c / "pg_ctl").exists():
            out = subprocess.run([str(c / "postgres"), "--version"], capture_output=True, text=True).stdout
            m = re.search(r"\)\s*(\d+)", out) or re.search(r"(\d+)\.\d+", out)
            major = m.group(1) if m else str(c)
            seen.setdefault(major, c)
    keep = [(v, p) for v, p in sorted(seen.items()) if v in ("15", "17")] or list(sorted(seen.items()))[:1]
    return keep


_BINS = _pg_bins()


@pytest.fixture(scope="session", params=[v for v, _ in _BINS] or ["none"], ids=lambda v: f"pg{v}")
def pg_cluster(request):
    psycopg = pytest.importorskip("psycopg")
    if not _BINS:
        pytest.skip("no PostgreSQL server binaries (initdb/pg_ctl) found; set PG_BIN")
    binp = dict(_BINS)[request.param]
    root = Path(tempfile.mkdtemp(prefix="m1254pg"))
    data = root / "data"
    # unix socket paths are length-limited (104 bytes on macOS): keep the socket directory short
    sockdir = root if len(str(root)) < 60 else Path(tempfile.mkdtemp(prefix="m54", dir="/tmp"))
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([str(binp / "initdb"), "-D", str(data), "-U", "postgres", "-A", "trust", "-E", "UTF8",
                    "--no-sync"], check=True, capture_output=True)
    opts = f"-p {port} -c listen_addresses=127.0.0.1 -c unix_socket_directories={sockdir} -c fsync=off"
    subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-o", opts, "-w", "-l", str(root / "log"), "start"],
                   check=True, capture_output=True)
    try:
        yield {"port": port, "psycopg": psycopg, "major": request.param}
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


def _apply_text(connect, text: str):
    """Run migration text the way migrate.ts does: one transaction around the whole file."""
    conn = connect()
    try:
        conn.execute(text)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _apply(connect):
    _apply_text(connect, _file())


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
-- the two relations the ga_sensitive check reads (live column names; only the columns the text touches)
CREATE TABLE chart_facts (
    fact_id bigserial PRIMARY KEY,
    chart_id uuid NOT NULL,
    ayanamsha_id text NOT NULL DEFAULT 'lahiri_chitrapaksha',
    fact_category text NOT NULL,
    fact_subject text NOT NULL,
    fact_key text NOT NULL,
    fact_value_text text,
    fact_value_num numeric,
    verification_pass_status text
);
CREATE TABLE reference_signs (canonical_name_en text PRIMARY KEY, lord text NOT NULL);
INSERT INTO reference_signs VALUES ('Aries', 'Mars'), ('Taurus', 'Venus'), ('Gemini', 'Mercury'), ('Cancer', 'Moon'),
  ('Leo', 'Sun'), ('Virgo', 'Mercury'), ('Libra', 'Venus'), ('Scorpio', 'Mars'), ('Sagittarius', 'Jupiter'),
  ('Capricorn', 'Saturn'), ('Aquarius', 'Saturn'), ('Pisces', 'Jupiter');
"""

# Live production `depends_on` / checks are stand-ins; only ga_sensitive's check text is the REAL one.
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
    "ga_sensitive_degree": ["ga_positions"],
    "bo_laksana": ["ga_positions", "ga_vargas"],
    "bo_upaya": ["bo_laksana", "ga_structural", "ga_dashas"],
}
CHARTS = [CANON, "00000000-0000-4000-8000-0000000000a1", "00000000-0000-4000-8000-0000000000a2"]
STRUCTURAL_CHECK = "SELECT true AS integrity_passed  -- ga_structural base text (stand-in for 1221's guard)"
VARGAS_CHECK = "SELECT true AS integrity_passed  -- ga_vargas base text (stand-in for 1222's guard)"
STANDIN_SPEC = {"version": "x", "for": "ga_vargas"}
STANDIN_SPEC_SHA = hashlib.sha256(b"ga_vargas-old").hexdigest()
STANDIN_SPEC_NEW_SHA = hashlib.sha256(b"ga_vargas-new").hexdigest()


def _make_fixture(connect, *, check_text: str | None = None, delete_sensitive: bool = False):
    base = _base_check() if check_text is None else check_text
    with connect() as c:
        c.execute(_DDL)
        for i, (aid, deps) in enumerate(LIVE_BEFORE.items()):
            if aid == "ga_sensitive":
                check = base
            elif aid == "ga_structural":
                check = STRUCTURAL_CHECK
            elif aid == "ga_vargas":
                check = VARGAS_CHECK
            else:
                check = f"SELECT true -- {aid}"
            c.execute("INSERT INTO asset_registry (asset_id, layer, sort_order, english_name, depends_on, integrity_check_sql) "
                      "VALUES (%s, %s, %s, %s, %s, %s)", (aid, aid.split("_")[0], i, aid.upper(), deps, check))
        c.execute(_TRIGGER_FN)
        c.execute(_TRIGGER_DEF)
        for aid in LIVE_BEFORE:
            for chart in CHARTS:
                c.execute("INSERT INTO asset_freshness (asset_id, chart_id, scope_key, partition_key, freshness_state, "
                          "receipt_version, observed_at) VALUES (%s, %s, %s, 'default', 'fresh', 'v1', '2026-10-01T00:00:00Z')",
                          (aid, chart, f"chart:{chart}"))
        c.execute("INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec, reviewed_at) "
                  "VALUES ('ga_vargas', %s, %s::jsonb, '2026-09-07T10:56:35Z')", (STANDIN_SPEC_SHA, json.dumps(STANDIN_SPEC)))
        if delete_sensitive:
            c.execute("DELETE FROM asset_registry WHERE asset_id = 'ga_sensitive'")
        c.commit()


def _freshness(connect):
    return _q(connect, "SELECT asset_id, chart_id::text, freshness_state, reasons::text, observed_at::text "
                       "FROM asset_freshness ORDER BY 1, 2")


def _registry_other_than_sensitive(connect):
    return _q(connect, "SELECT asset_id, to_jsonb(r)::text FROM asset_registry r WHERE asset_id <> 'ga_sensitive' ORDER BY 1")


def _check_md5(connect, aid="ga_sensitive"):
    return _q(connect, "SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id=%s", (aid,))[0][0]


def _stored_check(connect) -> str:
    return _q(connect, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ga_sensitive'")[0][0]


def test_fixture_base_check_is_the_live_base_text():
    assert _md5(_base_check()) == BASE_MD5


# ── apply / idempotence / guards / lock ──────────────────────────────────────

def test_1254_applies_the_new_text_and_stales_exactly_ga_sensitive_on_every_chart(db):
    _make_fixture(db)
    other_before = _registry_other_than_sensitive(db)
    fresh_before = {(a, c): (s, r, o) for a, c, s, r, o in _freshness(db)}
    _apply(db)
    assert _check_md5(db) == NEW_MD5
    assert _stored_check(db) == _new_check()
    rows = _freshness(db)
    stale = {(a, c) for a, c, s, r, o in rows if s == "stale"}
    assert stale == {("ga_sensitive", ch) for ch in CHARTS}, "ga_sensitive stale on EVERY chart, nothing else"
    for a, c, s, r, o in rows:
        if a == "ga_sensitive":
            assert "registry_changed" in r
        else:
            assert (s, r, o) == fresh_before[(a, c)], f"{a} freshness changed"
    assert _registry_other_than_sensitive(db) == other_before, "another registry row changed"
    row = _q(db, "SELECT to_jsonb(r) - 'integrity_check_sql' FROM asset_registry r WHERE asset_id='ga_sensitive'")[0][0]
    assert row["depends_on"] == ["ga_positions", "bg_reference"] and row["is_active"] is True, "only integrity_check_sql changed"


def test_1254_md5_guard_refuses_an_unexpected_text_and_changes_nothing(db):
    _make_fixture(db, check_text="SELECT false AS integrity_passed")
    fresh, reg = _freshness(db), _registry_other_than_sensitive(db)
    with pytest.raises(Exception) as ei:
        _apply(db)
    assert "1254" in str(ei.value) and "not the text this migration was written against" in str(ei.value), str(ei.value)
    assert _stored_check(db) == "SELECT false AS integrity_passed"
    assert _freshness(db) == fresh and _registry_other_than_sensitive(db) == reg


def test_1254_refuses_a_missing_ga_sensitive_row(db):
    _make_fixture(db, delete_sensitive=True)
    with pytest.raises(Exception) as ei:
        _apply(db)
    assert "expected exactly one ga_sensitive registry row" in str(ei.value), str(ei.value)


def test_1254_is_idempotent_second_run_rewrites_nothing_and_does_not_fire_the_trigger(db):
    _make_fixture(db)
    _apply(db)
    # an operator/rebuild marks the asset fresh again; a re-run must not stale it
    _exec(db, "UPDATE asset_freshness SET freshness_state='fresh', reasons='[]'::jsonb, observed_at='2026-10-02T00:00:00Z' "
              "WHERE asset_id='ga_sensitive'")
    snap_fresh = _freshness(db)
    snap_reg = _q(db, "SELECT asset_id, xmin::text, integrity_check_sql FROM asset_registry ORDER BY 1")
    _apply(db)
    assert _q(db, "SELECT asset_id, xmin::text, integrity_check_sql FROM asset_registry ORDER BY 1") == snap_reg, "row rewritten"
    assert _freshness(db) == snap_fresh, "the trigger fired on a no-op re-run"
    assert _check_md5(db) == NEW_MD5


def _lock_probe(connect, text: str, statement_timeout_ms: int) -> tuple[str, float]:
    """Hold ACCESS EXCLUSIVE on asset_registry, run `text` in a victim; return (error message, seconds)."""
    blocker = connect()
    blocker.execute("LOCK TABLE asset_registry IN ACCESS EXCLUSIVE MODE")
    try:
        t0 = time.monotonic()
        victim = connect(options=f"-c statement_timeout={statement_timeout_ms}")
        try:
            victim.execute(text)
            msg = ""
        except Exception as exc:  # noqa: BLE001 - the message is the observation
            msg = str(exc)
        elapsed = time.monotonic() - t0
        victim.rollback()
        victim.close()
    finally:
        blocker.rollback()
        blocker.close()
    return msg, elapsed


def test_1254_lock_timeout_fails_fast_when_the_registry_is_locked(db):
    _make_fixture(db)
    msg, elapsed = _lock_probe(db, _file(), 20000)
    assert "lock timeout" in msg.lower(), msg
    assert elapsed < 15, f"did not fail fast ({elapsed:.1f}s)"


# ── the new text: semantics on synthetic chart_facts ─────────────────────────

def _insert_facts(connect, rows):
    with connect() as c:
        for cat, subj, key, text, num, status in rows:
            c.execute("INSERT INTO chart_facts (chart_id, fact_category, fact_subject, fact_key, fact_value_text, "
                      "fact_value_num, verification_pass_status) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                      (CANON, cat, subj, key, text, num, status))
        c.commit()


def _truthy_rows(status: str):
    """One valid row per in-scope category with the given tier, including one valid special_lagna pair
    (conjunct b) and one valid bhava_arudha house_d1 (conjunct c)."""
    rows = []
    for cat in IN_SCOPE:
        if cat == "bhava_arudha":
            rows.append((cat, "BHAVA_ARUDHA_A3", "house_d1", None, 5, status))   # origin 3, 7th-from-origin is 9
        elif cat == "special_lagna":
            rows.append((cat, "BHAVA_LAGNA", "sign", "Aries", None, status))
            rows.append((cat, "BHAVA_LAGNA", "sign_lord", "Mars", None, status))
        else:
            rows.append((cat, f"{cat.upper()}_X", "value", "v", 1.5, status))
    return rows


def _evaluate(connect, text: str):
    with connect() as c:
        row = c.execute(text).fetchone()
        c.rollback()
        return row[0]


def _both(connect):
    return _evaluate(connect, _base_check()), _evaluate(connect, _new_check())


@pytest.mark.parametrize("status", ALLOWED)
def test_new_text_is_true_for_each_of_the_four_allowed_tiers_in_every_in_scope_category(db, status):
    _make_fixture(db)
    _insert_facts(db, _truthy_rows(status))
    old, new = _both(db)
    assert new is True
    assert old is (status in ("two_pass_verified", "floored")), "the base text refuses single / computed_extension"


def test_new_text_is_true_for_a_mix_of_all_four_tiers_across_the_scope(db):
    _make_fixture(db)
    rows = []
    for i, status in enumerate(itertools.islice(itertools.cycle(ALLOWED), len(IN_SCOPE))):
        rows += [r for r in _truthy_rows(status) if r[0] == IN_SCOPE[i]]
    _insert_facts(db, rows)
    assert _evaluate(db, _new_check()) is True


@pytest.mark.parametrize("status", REFUSED)
def test_new_text_is_false_for_any_tier_outside_the_four_in_every_in_scope_category(db, status):
    """Explicit list means exactly four: one refused row anywhere in the scope turns the check FALSE."""
    _make_fixture(db)
    _insert_facts(db, _truthy_rows("two_pass_verified"))
    assert _evaluate(db, _new_check()) is True
    with db() as c:
        for cat in IN_SCOPE:
            # flip exactly one category at a time to the refused tier, evaluate, flip back
            c.execute("UPDATE chart_facts SET verification_pass_status=%s WHERE fact_category=%s", (status, cat))
            assert c.execute(_new_check()).fetchone()[0] is False, f"{status} in {cat} must fail (a)"
            assert c.execute(_base_check()).fetchone()[0] is False
            c.execute("UPDATE chart_facts SET verification_pass_status='two_pass_verified' WHERE fact_category=%s", (cat,))
        c.rollback()


def test_scope_is_unchanged_out_of_scope_categories_and_null_tiers_do_not_matter(db):
    _make_fixture(db)
    _insert_facts(db, [("graha_position", "SUN", "sign", "Capricorn", None, "classical_match"),
                       ("graha_position", "MOON", "sign", "Pisces", None, "divergent_flagged"),
                       ("upagraha_position", "DHUMA", "sign", "Leo", None, None)])
    old, new = _both(db)
    assert old is True and new is True


def test_conjuncts_b_and_c_behave_exactly_as_before(db):
    _make_fixture(db)
    # (b): special_lagna sign_lord that disagrees with reference_signs -> FALSE for both texts, tier irrelevant
    _insert_facts(db, [("special_lagna", "L1", "sign", "Aries", None, "two_pass_verified"),
                       ("special_lagna", "L1", "sign_lord", "Venus", None, "two_pass_verified")])
    assert _both(db) == (False, False)
    _exec(db, "UPDATE chart_facts SET fact_value_text='Mars' WHERE fact_key='sign_lord'")
    assert _both(db) == (True, True)
    # (c): bhava_arudha landing in its own origin house (A3 -> 3) or the 7th from it (9) -> FALSE for both
    _insert_facts(db, [("bhava_arudha", "BHAVA_ARUDHA_A3", "house_d1", None, 3, "two_pass_verified")])
    assert _both(db) == (False, False)
    _exec(db, "UPDATE chart_facts SET fact_value_num=9 WHERE fact_category='bhava_arudha'")
    assert _both(db) == (False, False)
    _exec(db, "UPDATE chart_facts SET fact_value_num=5 WHERE fact_category='bhava_arudha'")
    assert _both(db) == (True, True)
    # (b)/(c) violations stay FALSE under the newly-allowed tiers: the relaxation does not mask them
    _exec(db, "UPDATE chart_facts SET verification_pass_status='single'")
    _exec(db, "UPDATE chart_facts SET fact_value_text='Venus' WHERE fact_key='sign_lord'")
    assert _both(db)[1] is False
    _exec(db, "UPDATE chart_facts SET fact_value_text='Mars' WHERE fact_key='sign_lord'")
    _exec(db, "UPDATE chart_facts SET fact_value_num=3 WHERE fact_category='bhava_arudha'")
    assert _both(db)[1] is False


def test_the_stored_text_after_apply_is_the_one_evaluated_here(db):
    _make_fixture(db)
    _apply(db)
    _insert_facts(db, _truthy_rows("single"))
    assert _evaluate(db, _stored_check(db)) is True
    _exec(db, "UPDATE chart_facts SET verification_pass_status='classical_match' WHERE fact_category='midpoint'")
    assert _evaluate(db, _stored_check(db)) is False


# ── combined: the S-L1 W1 window (1221, 1222, 1223, 1226 and 1254 in one deploy) ──

# What 1221, 1222, 1223 and 1226 do to this fixture, as stand-ins (the real files are other held PRs and are not
# in this tree): 1221 = md5-guarded UPDATE of ga_structural.integrity_check_sql; 1222 = md5-guarded UPDATE of
# ga_vargas.integrity_check_sql; 1223 = retire + insert of the ga_vargas output-digest spec (no registry trigger);
# 1226 = append the four L1 edges. Every registry UPDATE fires the same live trigger, so the combined stale set is
# exactly what the 1254 header states.
_STANDIN_1221 = f"""
SET LOCAL lock_timeout = '5s';
DO $$ BEGIN
  IF (SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id = 'ga_structural') IS DISTINCT FROM
     '{_md5(STRUCTURAL_CHECK)}' THEN RAISE EXCEPTION '1221-like guard tripped'; END IF; END $$;
UPDATE asset_registry SET integrity_check_sql = integrity_check_sql || E'\\n-- (a29) stand-in' WHERE asset_id = 'ga_structural';
"""
_STANDIN_1222 = f"""
SET LOCAL lock_timeout = '5s';
DO $$ BEGIN
  IF (SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id = 'ga_vargas') IS DISTINCT FROM
     '{_md5(VARGAS_CHECK)}' THEN RAISE EXCEPTION '1222-like guard tripped'; END IF; END $$;
UPDATE asset_registry SET integrity_check_sql = integrity_check_sql || E'\\n-- (e) stand-in' WHERE asset_id = 'ga_vargas';
"""
_STANDIN_1223 = f"""
SET LOCAL lock_timeout = '5s';
UPDATE asset_output_digest_specs SET retired_at = now() WHERE asset_id = 'ga_vargas' AND spec_sha256 = '{STANDIN_SPEC_SHA}';
INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec) VALUES ('ga_vargas', '{STANDIN_SPEC_NEW_SHA}', '{{"version":"y"}}'::jsonb)
  ON CONFLICT (asset_id, spec_sha256) DO NOTHING;
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
_WINDOW = {"1221": _STANDIN_1221, "1222": _STANDIN_1222, "1223": _STANDIN_1223, "1226": _STANDIN_1226}


def _apply_named(connect, name: str):
    _apply_text(connect, _file() if name == "1254" else _WINDOW[name])


def _final_state(connect):
    """Everything an order could change, without wall-clock columns."""
    return {
        "registry": _q(connect, "SELECT asset_id, to_jsonb(r)::text FROM asset_registry r ORDER BY 1"),
        "freshness": _q(connect, "SELECT asset_id, chart_id::text, freshness_state, reasons::text FROM asset_freshness ORDER BY 1, 2"),
        "specs": _q(connect, "SELECT asset_id, spec_sha256, retired_at IS NULL FROM asset_output_digest_specs ORDER BY 1, 2"),
    }


_NUMERIC = ("1221", "1222", "1223", "1226", "1254")
_reference: dict[str, dict] = {}


def _reference_state(pg_cluster):
    """The final state of the numeric order (1221, 1222, 1223, 1226, 1254), built once per cluster in its own database."""
    major = pg_cluster["major"]
    if major not in _reference:
        psycopg, port = pg_cluster["psycopg"], pg_cluster["port"]
        name = f"ref{major}"
        with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
            c.execute(f"CREATE DATABASE {name}")

        def connect(**kw):
            return psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname=name, **kw)

        _make_fixture(connect)
        for step in _NUMERIC:
            _apply_named(connect, step)
        _reference[major] = _final_state(connect)
        with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")
    return _reference[major]


def test_window_numeric_order_applies_cleanly_and_degrades_exactly_the_five_assets(db):
    _make_fixture(db)
    for name in _NUMERIC:
        _apply_named(db, name)
    assert _check_md5(db) == NEW_MD5
    assert _q(db, "SELECT depends_on FROM asset_registry WHERE asset_id='ga_vargas'")[0][0] == ["ga_positions", "ga_sensitive"]
    rows = _freshness(db)
    stale = {a for a, c, s, r, o in rows if s == "stale"}
    assert stale == {"ga_structural", "ga_vargas", "ga_dashas", "ga_yoga", "ga_sensitive"}, stale
    assert all(s == "stale" for a, c, s, r, o in rows if a in stale), "every chart"
    assert all(s == "fresh" for a, c, s, r, o in rows if a not in stale), "nothing else moved"


@pytest.mark.parametrize("order", list(itertools.permutations(_NUMERIC)), ids=lambda o: "-".join(o))
def test_no_apply_order_of_the_five_trips_a_guard_and_every_order_ends_in_one_state(db, pg_cluster, order):
    """The guards read only their own row/column, so the window never depends on file order: all 120 orders end
    in the SAME final state as the numeric order (registry rows, freshness, specs)."""
    reference = _reference_state(pg_cluster)
    _make_fixture(db)
    for step in order:
        _apply_named(db, step)
    assert _check_md5(db) == NEW_MD5
    assert _final_state(db) == reference


def test_window_rerun_after_apply_is_a_noop(db):
    _make_fixture(db)
    for name in _NUMERIC:
        _apply_named(db, name)
    snap_specs = _final_state(db)["specs"]
    snap_reg = _q(db, "SELECT asset_id, xmin::text FROM asset_registry WHERE asset_id IN ('ga_sensitive') ORDER BY 1")
    _apply_named(db, "1254")
    assert _final_state(db)["specs"] == snap_specs
    assert _q(db, "SELECT asset_id, xmin::text FROM asset_registry WHERE asset_id IN ('ga_sensitive') ORDER BY 1") == snap_reg


# ── MUTATIONS: each guard has a mutant, and the check that guards it must turn RED ──────────────────────────

def _mutant_pre_guard_neutered(text: str) -> str:
    needle = (f"  ELSIF v_md5 IS DISTINCT FROM '{BASE_MD5}' THEN\n"
              "    RAISE EXCEPTION '1254: ga_sensitive integrity_check_sql is not the text this migration was written against (md5 %)', v_md5;\n")
    assert needle in text
    return text.replace(needle, "")


def _mutant_update_without_md5_where(text: str) -> str:
    needle = f"\n  AND md5(integrity_check_sql) = '{BASE_MD5}';"
    assert needle in text
    return text.replace(needle, ";")


def _retarget(text: str, old_body: str, new_body: str) -> str:
    """Replace the vocabulary list everywhere (the UPDATE body AND the post-check fragment) and re-pin the md5."""
    assert old_body in text
    mutated = text.replace(old_body, new_body)
    new_md5 = _md5(_new_check(mutated))
    return mutated.replace(NEW_MD5, new_md5)


def _mutant_vocab_widened(text: str) -> str:
    return _retarget(text, "'single', 'computed_extension')", "'single', 'computed_extension', 'classical_match')")


def _mutant_vocab_narrowed(text: str) -> str:
    return _retarget(text, "'single', 'computed_extension')", "'single')")


def _mutant_lock_timeout_removed(text: str) -> str:
    assert "SET LOCAL lock_timeout = '5s';" in text
    return text.replace("SET LOCAL lock_timeout = '5s';\n", "", 1)


def _mutant_post_check_neutered(text: str) -> str:
    start = text.index("DO $post$")
    return text[:start]


def _check_refuses_unexpected_base(connect, text: str) -> bool:
    _make_fixture(connect, check_text="SELECT false AS integrity_passed")
    try:
        _apply_text(connect, text)
    except Exception as exc:  # noqa: BLE001
        return "not the text this migration was written against" in str(exc)
    return False


def _check_rerun_rewrites_nothing(connect, text: str) -> bool:
    _make_fixture(connect)
    _apply_text(connect, text)
    snap = _q(connect, "SELECT xmin::text, integrity_check_sql FROM asset_registry WHERE asset_id='ga_sensitive'")
    _apply_text(connect, text)
    return _q(connect, "SELECT xmin::text, integrity_check_sql FROM asset_registry WHERE asset_id='ga_sensitive'") == snap


def _check_vocabulary_is_exactly_the_four(connect, text: str) -> bool:
    _make_fixture(connect)
    try:
        _apply_text(connect, text)
    except Exception:  # noqa: BLE001
        return False
    stored = _stored_check(connect)
    cat = "midpoint"
    _insert_facts(connect, [(cat, "M1", "value", "v", 1.0, "two_pass_verified")])
    ok = True
    with connect() as c:
        for status in ALLOWED:
            c.execute("UPDATE chart_facts SET verification_pass_status=%s", (status,))
            ok &= c.execute(stored).fetchone()[0] is True
        for status in REFUSED:
            c.execute("UPDATE chart_facts SET verification_pass_status=%s", (status,))
            ok &= c.execute(stored).fetchone()[0] is False
        c.rollback()
    return bool(ok)


def _check_lock_timeout_fails_fast(connect, text: str) -> bool:
    _make_fixture(connect)
    # the migration's own lock_timeout is 5s: a statement_timeout of 12s must never be the one that fires
    msg, elapsed = _lock_probe(connect, text, 12000)
    return "lock timeout" in msg.lower() and "statement timeout" not in msg.lower() and elapsed < 8


def _check_post_check_refuses_a_body_that_did_not_take(connect, text: str) -> bool:
    """The body is altered but the md5 constants are not: the UPDATE lands a text whose md5 is not the pinned one."""
    _make_fixture(connect)
    body = _new_check(text)
    altered = text.replace(body, body.rstrip("\n") + "\n  -- tampered\n")
    try:
        _apply_text(connect, altered)
    except Exception as exc:  # noqa: BLE001
        return "did not take" in str(exc)
    return False


def _check_post_check_refuses_a_change_outside_conjunct_a(connect, text: str) -> bool:
    """A body that changes conjunct (b) AND is re-pinned in every md5 constant still applies cleanly up to the
    structural check, which must refuse it: the stored text differs from the base outside conjunct (a)."""
    _make_fixture(connect)
    body = _new_check(text)
    altered_body = body.replace("lower(r.lord) = lower(l.fact_value_text)", "lower(r.lord) <> lower(l.fact_value_text)")
    assert altered_body != body
    altered = text.replace(body, altered_body).replace(NEW_MD5, _md5(altered_body))
    try:
        _apply_text(connect, altered)
    except Exception as exc:  # noqa: BLE001
        return "outside conjunct (a)" in str(exc)
    return False


_CHECKS = {
    "refuses_unexpected_base": _check_refuses_unexpected_base,
    "rerun_rewrites_nothing": _check_rerun_rewrites_nothing,
    "vocabulary_is_exactly_the_four": _check_vocabulary_is_exactly_the_four,
    "lock_timeout_fails_fast": _check_lock_timeout_fails_fast,
    "post_check_refuses_body_that_did_not_take": _check_post_check_refuses_a_body_that_did_not_take,
    "post_check_refuses_change_outside_conjunct_a": _check_post_check_refuses_a_change_outside_conjunct_a,
}

_MUTANTS = {
    "pre_guard_neutered": (_mutant_pre_guard_neutered, "refuses_unexpected_base"),
    "update_without_md5_where": (_mutant_update_without_md5_where, "rerun_rewrites_nothing"),
    "vocabulary_widened_classical_match": (_mutant_vocab_widened, "vocabulary_is_exactly_the_four"),
    "vocabulary_narrowed_computed_extension_dropped": (_mutant_vocab_narrowed, "vocabulary_is_exactly_the_four"),
    "lock_timeout_removed": (_mutant_lock_timeout_removed, "lock_timeout_fails_fast"),
    "post_check_neutered_body": (_mutant_post_check_neutered, "post_check_refuses_body_that_did_not_take"),
    "post_check_neutered_structure": (_mutant_post_check_neutered, "post_check_refuses_change_outside_conjunct_a"),
}


@pytest.mark.parametrize("check", sorted(_CHECKS))
def test_every_mutation_check_is_green_on_the_real_file(db, check):
    assert _CHECKS[check](db, _file()) is True, f"{check} must hold for the real migration"


@pytest.mark.parametrize("mutant", sorted(_MUTANTS))
def test_each_mutant_turns_its_guarding_check_red(db, mutant):
    transform, check = _MUTANTS[mutant]
    mutated = transform(_file())
    assert mutated != _file()
    assert _CHECKS[check](db, mutated) is False, f"mutant {mutant} was NOT detected by {check}"
