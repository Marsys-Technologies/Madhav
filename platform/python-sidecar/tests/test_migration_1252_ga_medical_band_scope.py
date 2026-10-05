"""
Migration 1252: the ga_medical integrity_check_sql accepts the NEW band cuts of the band lane (#2890), scoped to
the canonical chart. HELD: merges only in the S-L1 window W1 (after the band-lane writer deploy, before the
ga_medical rebuild in W6; order-independent versus 1221/1222/1223/1226/1254).

Two tiers:
  * STATIC (always runs, DB-free): file shape, guards, header sections, the md5 of the base and target texts, the
    base text = migration 740's body, and the EXACT base -> target diff: after removing comments and collapsing
    whitespace, target == base with exactly three code edits (the canonical scope on clause (b), the cut
    `<= 0.6` -> `< 0.7`, Saturn `'mild'` -> `'moderate'`) and nothing else.
  * LIVE (needs PostgreSQL server binaries): applies the REAL on-disk migration file to a DISPOSABLE cluster this
    module creates with initdb in a temp dir (own port, trust auth, removed at session end). It never connects to
    anything else. Skipped, loudly, when no `initdb`/`pg_ctl` is found (looked up via $PG_BIN, PATH, homebrew,
    /usr/lib/postgresql/*/bin). Set $PG_BIN to pin a version (production is PostgreSQL 15). $PG_SOCKDIR_BASE
    optionally pins the (short) directory for the unix socket.

The LIVE fixture carries the REAL trigger function body and trigger definition of
`nirmana_registry_receipt_invalidation` (read from production 2026-10-02 as suvarna_reader with
pg_get_functiondef / pg_get_triggerdef; the function text was re-compared byte-for-byte on 2026-10-02) and the
live column set of asset_registry / asset_freshness, so what is proved is the serving effect the header states:
ga_medical freshness goes stale on EVERY chart for 1252 and nothing else moves. The data tables
(ga_medical, ga_condition_composite) carry the columns the clause reads, with SYNTHETIC scores and labels (no
production values). It does NOT prove production state (that is read from production structure after deploy;
Trap 103).

THE FOUR-STATE PROOF (the pre-window sweep's, reproduced on the fixture; production values were read separately,
read-only, and are in the migration header):
  (i)   old rows + the live (740) clause                                     = true
  (ii)  canonical rebuilt under the new cuts + the live clause                = FALSE   (why 1252 exists)
  (iii) canonical rebuilt + 1252, the stale other chart still holding 'mild'  = true    (why 1252 is canonical-scoped)
  (iv)  every chart rebuilt + 1252                                            = true
MUTATIONS (each must turn a proof red): pre-guard neutered, UPDATE without the md5 WHERE, scope clause dropped,
Saturn conjunct left 'mild', lock_timeout removed, post-check neutered.
"""
from __future__ import annotations

import difflib
import glob
import hashlib
import itertools
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
_M1252 = _MIG / "1252_nirmana_l1_ga_medical_integrity_band_cut_canonical_scope.sql"
_M740 = _MIG / "740_nirmana_l1_ga_medical_integrity_contract.sql"

CANON = "482012f1-710e-4a25-994a-93821f5871aa"
STALE_CH = "00000000-0000-4000-8000-0000000000b2"   # stands for the chart whose rows S-L1 does not rebuild (N-78)
OTHER_CH = "00000000-0000-4000-8000-0000000000b3"
CHARTS = [CANON, STALE_CH, OTHER_CH]
OLD_CHECK_MD5 = "0b5d65e4933f10ec95b2db2e7d82289d"
NEW_CHECK_MD5 = "ae453edf2afeeaba086a444c66681676"
OLD_CHECK_LEN, NEW_CHECK_LEN = 2811, 3862

AYANAMSHAS = ["lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"]
GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
# SYNTHETIC scores. Canonical: Jupiter, Saturn, Rahu lie in (0.6, 0.7) -> 15 rows change label (old 'mild' -> new
# 'moderate'), the production shape. STALE_CH: Venus lies in (0.6, 0.7) -> 5 rows. OTHER_CH: none.
SCORES = {
    CANON: dict(Sun=0.30, Moon=0.55, Mars=0.45, Mercury=0.50, Jupiter=0.62, Venus=0.75, Saturn=0.68, Rahu=0.66, Ketu=0.35),
    STALE_CH: dict(Sun=0.20, Moon=0.50, Mars=0.45, Mercury=0.48, Jupiter=0.75, Venus=0.65, Saturn=0.85, Rahu=0.30, Ketu=0.90),
    OTHER_CH: dict(Sun=0.10, Moon=0.52, Mars=0.41, Mercury=0.55, Jupiter=0.80, Venus=0.90, Saturn=0.45, Rahu=0.20, Ketu=0.35),
}


def old_label(s: float | None) -> str:
    if s is None:
        return "unknown"
    return "strong" if s < 0.4 else ("moderate" if s <= 0.6 else "mild")


def new_label(s: float | None) -> str:
    if s is None:
        return "unknown"
    return "strong" if s < 0.4 else ("moderate" if s < 0.7 else "mild")


# ── helpers ──────────────────────────────────────────────────────────────────

def _code(text: str) -> str:
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("--"))


def _flat(text: str) -> str:
    """Header comments with the `-- ` prefixes removed and whitespace collapsed (needles span wrapped lines)."""
    return re.sub(r"\s+", " ", re.sub(r"^--", " ", text, flags=re.M))


def _old_check() -> str:
    return re.search(r"\$ck\$(.*?)\$ck\$", _M740.read_text(), re.S).group(1)


def _new_check(text: str | None = None) -> str:
    return re.search(r"\$ck\$(.*)\$ck\$", _M1252.read_text() if text is None else text, re.S).group(1)


def _norm_code(sql: str) -> str:
    """The clause with comment lines removed and whitespace collapsed."""
    return re.sub(r"\s+", " ", _code(sql)).strip()


# ── STATIC tier ──────────────────────────────────────────────────────────────

def test_file_does_not_own_the_transaction_starts_with_lock_timeout_and_states_its_sections():
    text = _M1252.read_text()
    code = _code(text)
    sql = _flat(text)
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code), "migrate.ts owns the transaction"
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';"), code.strip()[:80]
    assert not re.search(r"^\s*(DROP|TRUNCATE|DELETE\s+FROM|REVOKE|GRANT|ALTER|CREATE)\b", code, re.I | re.M)
    for needle in ("SERVING EFFECT AT APPLY", "ORDERING", "HELD", "EXPECTED STATE AT APPLY", "IDEMPOTENT SHAPE",
                   "VERIFICATION BY PRODUCTION STRUCTURE", "ROLLBACK", "suvarna_reader", "S-L1 window W1",
                   "AFTER the writer deploy", "BEFORE the ga_medical rebuild in W6",
                   "1221, 1222, 1223, 1226 and 1254", "WHY THE CLAUSE IS CANONICAL-SCOPED", "N-78",
                   "WIDENING (b) BACK TO TABLE-WIDE IS AN S-L1b TASK", "cb73cd3d", "WHY ga_vastu IS NOT TOUCHED",
                   "FALSE (expected)", "do not apply it earlier", "ga_medical (1252)", "ga_sensitive (1254)"):
        assert needle.lower() in sql.lower(), f"header no longer states: {needle}"
    assert "$pre$" in sql and "$post$" in sql


def test_serving_effect_names_the_live_trigger_and_every_chart():
    sql = _flat(_M1252.read_text())
    for needle in ("nirmana_registry_receipt_invalidation", "AFTER UPDATE OF depends_on, natural_key_partition, "
                   "health_probe, integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, "
                   "is_active, target_table", "old.* IS DISTINCT FROM new.*", "ON EVERY CHART",
                   "UNRESOLVED", "receipt_not_fresh", "{ga_structural (1221), ga_vargas (1222, 1223, 1226), "
                   "ga_dashas (1226), ga_yoga (1226), ga_sensitive (1254), ga_medical (1252)}"):
        assert needle in sql, needle


def test_base_text_is_migration_740s_body_and_the_target_md5_is_pinned():
    old, new = _old_check(), _new_check()
    assert hashlib.md5(old.encode()).hexdigest() == OLD_CHECK_MD5 and len(old) == OLD_CHECK_LEN
    assert hashlib.md5(new.encode()).hexdigest() == NEW_CHECK_MD5 and len(new) == NEW_CHECK_LEN
    code = _code(_M1252.read_text())
    assert code.count(OLD_CHECK_MD5) == 2, "pre-check (accept) + UPDATE guard name the base md5"
    assert code.count(NEW_CHECK_MD5) == 2, "pre-check (already applied) + post-check name the target md5"
    assert new.rstrip().endswith("AS integrity_passed") and old.rstrip().endswith("AS integrity_passed")


def test_the_new_text_is_the_base_text_plus_exactly_three_code_edits():
    """The base -> target diff, as code (comments removed, whitespace collapsed): ONLY the canonical scope on
    clause (b), the cut `<= 0.6` -> `< 0.7`, and Saturn's pinned label. Conjunct (a) and the Sun conjunct are
    byte-identical, and the nested block's parentheses balance."""
    old, new = _old_check(), _new_check()
    expect = _norm_code(old)
    anchor = "WHERE NOT EXISTS ( SELECT 1 FROM ga_condition_composite c"
    assert expect.count(anchor) == 1
    expect = expect.replace(anchor, f"WHERE m.chart_id = '{CANON}' AND NOT EXISTS ( SELECT 1 FROM ga_condition_composite c")
    assert expect.count("WHEN c.condition_score <= 0.6 THEN 'moderate'") == 1
    expect = expect.replace("WHEN c.condition_score <= 0.6 THEN 'moderate'", "WHEN c.condition_score < 0.7 THEN 'moderate'")
    assert expect.count("graha = 'Saturn' AND indication_strength <> 'mild'") == 1
    expect = expect.replace("graha = 'Saturn' AND indication_strength <> 'mild'", "graha = 'Saturn' AND indication_strength <> 'moderate'")
    assert _norm_code(new) == expect, "the new text differs from base + the three declared code edits"
    assert new.count("(") == new.count(")")
    # (a) and the Sun conjunct are carried verbatim
    for frag in ("SELECT 1 FROM ga_medical WHERE indication_tier <> 'jyotish_indication'",
                 "SELECT 1 FROM ga_medical WHERE not_diagnosis IS DISTINCT FROM true",
                 "graha = 'Sun' AND indication_strength <> 'strong'"):
        assert frag in old and frag in new


def test_the_comment_hunks_are_the_declared_ones_and_leave_no_stale_line_reference():
    old, new = _old_check(), _new_check()
    ops = [o for o in difflib.SequenceMatcher(None, old.splitlines(), new.splitlines(), autojunk=False).get_opcodes()
           if o[0] != "equal"]
    assert 4 <= len(ops) <= 8, ops
    assert "ga_medical_writer.py:71-90" in old and "ga_medical_writer.py:71-90" not in new
    assert "ga_medical_writer.py:275-300" in old and "ga_medical_writer.py:275-300" not in new
    assert "SCOPED to the canonical chart (migration 1252)" in new and "S-L1b" in new and "N-78" in new
    assert "condition_score>0.6 -> 'mild'" in old and "condition_score>0.6 -> 'mild'" not in new


def test_new_text_scope_and_cut_facts():
    new = _new_check()
    assert f"WHERE m.chart_id = '{CANON}'" in new
    assert "WHEN c.condition_score < 0.7 THEN 'moderate'" in new and "<= 0.6" not in new
    assert "graha = 'Saturn' AND indication_strength <> 'moderate'" in new
    assert not re.search(r"indication_strength <> 'mild'", new)


def test_is_one_guarded_update_of_one_column_of_one_row():
    code = _code(_M1252.read_text())
    assert len(re.findall(r"\bUPDATE asset_registry\b", code)) == 1
    assert re.findall(r"\bSET\s+([a-z_]+)\s*=", code.split("$ck$")[0], re.I) == ["integrity_check_sql"]
    tail = code.split("$ck$")[-1]
    assert "WHERE asset_id = 'ga_medical'" in tail and f"md5(integrity_check_sql) = '{OLD_CHECK_MD5}'" in tail
    assert "ga_vastu" not in code, "ga_vastu is deliberately not touched"


def test_number_and_name_follow_the_pattern():
    # No sibling-uniqueness assertion (always-armed); migration_number_guard.test.ts owns number uniqueness.
    assert _M1252.name.startswith("1252_")
    assert _M1252.is_file()


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
CREATE TABLE ga_condition_composite (
    chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, graha text NOT NULL, condition_score numeric,
    PRIMARY KEY (chart_id, ayanamsha_id, graha)
);
CREATE TABLE ga_medical (
    chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, graha text NOT NULL,
    indication_tier text NOT NULL DEFAULT 'jyotish_indication',
    not_diagnosis boolean NOT NULL DEFAULT true,
    indication_strength text,
    PRIMARY KEY (chart_id, ayanamsha_id, graha)
);
"""

# Assets of the combined window (production depends_on read 2026-10-02 for the ones 1226 touches) + ga_medical/ga_vastu.
ASSETS: dict[str, list[str]] = {
    "ga_positions": [], "bg_reference": [],
    "ga_sensitive": ["ga_positions", "bg_reference"],
    "ga_vargas": ["ga_positions"], "ga_dashas": ["ga_positions"],
    "ga_structural": ["ga_dashas", "ga_nakshatra", "ga_panchanga", "ga_positions", "ga_sensitive", "ga_strength", "ga_vargas"],
    "ga_yoga": ["ga_structural", "ga_dashas"],
    "ga_nakshatra": [], "ga_panchanga": [], "ga_strength": [],
    "ga_condition": ["ga_positions"], "ga_medical": ["ga_condition"], "ga_vastu": ["ga_condition"],
}
STAND_IN_CHECKS = {a: f"SELECT true AS integrity_passed -- {a} base text (stand-in)" for a in ASSETS}
VASTU_TEXT = "SELECT true AS integrity_passed -- ga_vastu (untouched by 1252)"


def _insert_rows(c, chart: str, labeller) -> None:
    for ay in AYANAMSHAS:
        for g in GRAHAS:
            s = SCORES[chart][g]
            c.execute("INSERT INTO ga_condition_composite VALUES (%s, %s, %s, %s)", (chart, ay, g, s))
            c.execute("INSERT INTO ga_medical (chart_id, ayanamsha_id, graha, indication_strength) VALUES (%s, %s, %s, %s)",
                      (chart, ay, g, labeller(s)))


@pytest.fixture(scope="session")
def pg_cluster():
    psycopg = pytest.importorskip("psycopg")
    binp = _find_pg_bin()
    if binp is None:
        pytest.skip("no PostgreSQL server binaries (initdb/pg_ctl) found; set PG_BIN")
    root = Path(tempfile.mkdtemp(prefix="m1252pg"))
    data = root / "data"
    # unix socket paths are length-limited (104 bytes on macOS): keep the socket directory short
    base = os.environ.get("PG_SOCKDIR_BASE")
    sockdir = Path(tempfile.mkdtemp(prefix="m52", dir=base or "/tmp")) if (base or len(str(root)) >= 60) else root
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([str(binp / "initdb"), "-D", str(data), "-U", "postgres", "-A", "trust", "-E", "UTF8",
                    "--no-sync"], check=True, capture_output=True)
    opts = f"-p {port} -c listen_addresses=127.0.0.1 -c unix_socket_directories={sockdir} -c fsync=off"
    subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-o", opts, "-w", "-l", str(root / "log"), "start"],
                   check=True, capture_output=True)
    try:
        # one TEMPLATE database holding the fixture (DDL, the real trigger, registry, freshness); every test clones it
        with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
            c.execute("CREATE DATABASE tmpl")
        with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="tmpl") as c:
            c.execute(_DDL)
            for i, (aid, deps) in enumerate(ASSETS.items()):
                check = _old_check() if aid == "ga_medical" else (VASTU_TEXT if aid == "ga_vastu" else STAND_IN_CHECKS[aid])
                c.execute("INSERT INTO asset_registry (asset_id, layer, sort_order, english_name, depends_on, integrity_check_sql) "
                          "VALUES (%s, %s, %s, %s, %s, %s)", (aid, aid.split("_")[0], i, aid.upper(), deps, check))
            c.execute(_TRIGGER_FN)
            c.execute(_TRIGGER_DEF)
            for aid in ASSETS:
                for chart in CHARTS:
                    c.execute("INSERT INTO asset_freshness (asset_id, chart_id, scope_key, partition_key, freshness_state, "
                              "receipt_version, observed_at) VALUES (%s, %s, %s, 'default', 'fresh', 'v1', '2026-10-01T00:00:00Z')",
                              (aid, chart, f"chart:{chart}"))
            c.commit()
        yield {"port": port, "psycopg": psycopg}
    finally:
        subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)
        if sockdir != root:
            shutil.rmtree(sockdir, ignore_errors=True)


_db_counter = 0


@pytest.fixture()
def db(pg_cluster):
    """A fresh database per test, cloned from the template; yields a connect() factory (autocommit off)."""
    global _db_counter
    _db_counter += 1
    name = f"t{_db_counter}"
    psycopg, port = pg_cluster["psycopg"], pg_cluster["port"]
    with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"CREATE DATABASE {name} TEMPLATE tmpl")

    def connect(**kw):
        return psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname=name, **kw)

    yield connect
    with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")


def _apply(connect, src, *, text: str | None = None):
    """Run a migration the way migrate.ts does: one transaction around the whole file."""
    sql = text if text is not None else Path(src).read_text()
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


def _seed(connect, canon: str, stale: str, other: str) -> None:
    """Fill ga_condition_composite + ga_medical; each chart's labels are 'old' (<=0.6 cut), 'new' (<0.7) or absent."""
    lab = {"old": old_label, "new": new_label}
    with connect() as c:
        for chart, mode in ((CANON, canon), (STALE_CH, stale), (OTHER_CH, other)):
            _insert_rows(c, chart, lab[mode])
        c.commit()


def _registry_text(connect, aid="ga_medical") -> str:
    return _q(connect, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id=%s", (aid,))[0][0]


def _passes(connect, text: str) -> bool:
    return bool(_q(connect, text)[0][0])


def _check_md5(connect, aid="ga_medical"):
    return _q(connect, "SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id=%s", (aid,))[0][0]


def _freshness(connect):
    return _q(connect, "SELECT asset_id, chart_id::text, freshness_state, reasons::text, observed_at::text "
                       "FROM asset_freshness ORDER BY 1, 2")


def _registry_other_than(connect, aid="ga_medical"):
    return _q(connect, "SELECT asset_id, to_jsonb(r)::text FROM asset_registry r WHERE asset_id <> %s ORDER BY 1", (aid,))


# ── mutation machinery: a mutated copy of the migration, with its md5 constants kept self-consistent ──────────

def _mutated(kind: str) -> str:
    """The migration text with ONE defect injected. Clause mutations recompute the target md5 everywhere so the
    mutated migration still applies cleanly: the defect must be caught by the BEHAVIOUR proofs, not by the md5."""
    text = _M1252.read_text()
    if kind == "pre_guard_neutered":
        out = text.replace("ELSIF v_md5 IS DISTINCT FROM '%s' THEN" % OLD_CHECK_MD5, "ELSIF false THEN")
    elif kind == "already_applied_branch_dropped":
        out = text.replace("IF v_md5 = '%s' THEN" % NEW_CHECK_MD5, "IF false THEN")
    elif kind == "update_without_md5_where":
        out = text.replace("  AND md5(integrity_check_sql) = '%s';" % OLD_CHECK_MD5, ";")
    elif kind == "lock_timeout_removed":
        out = text.replace("SET LOCAL lock_timeout = '5s';\n", "", 1)
    elif kind == "post_check_neutered":
        out = text.replace("IF v_md5 IS DISTINCT FROM '%s' THEN\n    RAISE EXCEPTION '1252: the new" % NEW_CHECK_MD5,
                           "IF false THEN\n    RAISE EXCEPTION '1252: the new")
    elif kind in ("scope_dropped", "saturn_left_mild", "cut_left_old"):
        body = _new_check(text)
        if kind == "scope_dropped":
            mut = body.replace(f"    WHERE m.chart_id = '{CANON}'\n      AND NOT EXISTS (", "    WHERE NOT EXISTS (")
        elif kind == "saturn_left_mild":
            mut = body.replace("graha = 'Saturn' AND indication_strength <> 'moderate'", "graha = 'Saturn' AND indication_strength <> 'mild'")
        else:
            mut = body.replace("WHEN c.condition_score < 0.7 THEN 'moderate'", "WHEN c.condition_score <= 0.6 THEN 'moderate'")
        assert mut != body, kind
        out = text.replace(body, mut).replace(NEW_CHECK_MD5, hashlib.md5(mut.encode()).hexdigest())
    else:  # pragma: no cover
        raise AssertionError(kind)
    assert out != text, f"mutation {kind} did not change the file"
    return out


# ── behaviour proofs, parameterised by the migration text (real file: all True; mutated copies: red) ──────────

def prop_applies_and_stales_exactly_ga_medical(connect, text) -> bool:
    other_before = _registry_other_than(connect)
    fresh_before = {(a, c): (s, r, o) for a, c, s, r, o in _freshness(connect)}
    _apply(connect, None, text=text)
    if _check_md5(connect) != NEW_CHECK_MD5 or _registry_text(connect) != _new_check():
        return False
    rows = _freshness(connect)
    stale = {(a, c) for a, c, s, r, o in rows if s == "stale"}
    if stale != {("ga_medical", ch) for ch in CHARTS}:
        return False
    for a, c, s, r, o in rows:
        if a != "ga_medical" and (s, r, o) != fresh_before[(a, c)]:
            return False
    row = _q(connect, "SELECT to_jsonb(r) - 'integrity_check_sql' FROM asset_registry r WHERE asset_id='ga_medical'")[0][0]
    return _registry_other_than(connect) == other_before and row["depends_on"] == ["ga_condition"] and row["is_active"] is True


def prop_refuses_an_unexpected_base(connect, text) -> bool:
    _exec(connect, "UPDATE asset_registry SET integrity_check_sql = 'SELECT false AS integrity_passed' WHERE asset_id='ga_medical'")
    fresh, reg = _freshness(connect), _registry_other_than(connect)
    try:
        _apply(connect, None, text=text)
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        return ("1252" in msg and "not the text this migration was written against" in msg
                and _registry_text(connect) == "SELECT false AS integrity_passed"
                and _freshness(connect) == fresh and _registry_other_than(connect) == reg)
    return False


def prop_idempotent(connect, text) -> bool:
    try:
        _apply(connect, None, text=text)
    except Exception:  # noqa: BLE001
        return False
    _exec(connect, "UPDATE asset_freshness SET freshness_state='fresh', reasons='[]'::jsonb, observed_at='2026-10-02T00:00:00Z' "
                   "WHERE asset_id='ga_medical'")
    snap_fresh = _freshness(connect)
    snap_reg = _q(connect, "SELECT asset_id, xmin::text, integrity_check_sql FROM asset_registry ORDER BY 1")
    try:
        _apply(connect, None, text=text)
    except Exception:  # noqa: BLE001
        return False
    return (_q(connect, "SELECT asset_id, xmin::text, integrity_check_sql FROM asset_registry ORDER BY 1") == snap_reg
            and _freshness(connect) == snap_fresh and _check_md5(connect) == NEW_CHECK_MD5)


def prop_lock_timeout_fails_fast(connect, text) -> bool:
    blocker = connect()
    blocker.execute("LOCK TABLE asset_registry IN ACCESS EXCLUSIVE MODE")
    err = None
    try:
        t0 = time.monotonic()
        victim = connect(options="-c statement_timeout=20000")
        try:
            victim.execute(text)
        except Exception as e:  # noqa: BLE001
            err = str(e)
        elapsed = time.monotonic() - t0
        victim.rollback()
        victim.close()
    finally:
        blocker.rollback()
        blocker.close()
    return err is not None and "lock timeout" in err.lower() and elapsed < 15


def prop_post_check_catches_a_silent_noop(connect, text) -> bool:
    """A BEFORE UPDATE trigger cancels the row update silently (UPDATE ... 0 rows): the post-check must refuse."""
    _exec(connect, "CREATE FUNCTION cancel_it() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NULL; END $$")
    _exec(connect, "CREATE TRIGGER aaa_cancel BEFORE UPDATE ON asset_registry FOR EACH ROW EXECUTE FUNCTION cancel_it()")
    try:
        _apply(connect, None, text=text)
    except Exception as e:  # noqa: BLE001
        return "did not take" in str(e)
    return False


def prop_scope_holds(connect, text) -> bool:
    """State (iii): canonical rebuilt, the other charts still on the OLD labels (stale 'mild' rows present)."""
    _seed(connect, canon="new", stale="old", other="old")
    _apply(connect, None, text=text)
    return _passes(connect, _registry_text(connect))


def prop_saturn_conjunct_is_moderate(connect, text) -> bool:
    """Every chart rebuilt under the new cuts: the clause is true only if Saturn's pin agrees with the writer."""
    _seed(connect, canon="new", stale="new", other="new")
    _apply(connect, None, text=text)
    return _passes(connect, _registry_text(connect))


def prop_new_cut_is_enforced(connect, text) -> bool:
    """A canonical row carrying the OLD band label (Rahu, 0.66, 'mild'; Saturn kept right) must FAIL the clause."""
    _seed(connect, canon="new", stale="new", other="new")
    _exec(connect, "UPDATE ga_medical SET indication_strength='mild' WHERE chart_id=%s AND graha='Rahu' AND ayanamsha_id='raman'", (CANON,))
    _apply(connect, None, text=text)
    return not _passes(connect, _registry_text(connect))


# ── real-file tests ──────────────────────────────────────────────────────────

def test_applies_the_new_text_and_stales_exactly_ga_medical_on_every_chart(db):
    assert prop_applies_and_stales_exactly_ga_medical(db, _M1252.read_text())


def test_ga_vastu_and_every_other_registry_row_are_untouched(db):
    _apply(db, _M1252)
    assert _registry_text(db, "ga_vastu") == VASTU_TEXT
    stale_assets = {a for a, c, s, r, o in _freshness(db) if s == "stale"}
    assert stale_assets == {"ga_medical"}


def test_md5_guard_refuses_an_unexpected_text_and_changes_nothing(db):
    assert prop_refuses_an_unexpected_base(db, _M1252.read_text())


def test_refuses_a_missing_ga_medical_row(db):
    _exec(db, "DELETE FROM asset_registry WHERE asset_id='ga_medical'")
    with pytest.raises(Exception) as ei:
        _apply(db, _M1252)
    assert "expected exactly one ga_medical registry row" in str(ei.value), str(ei.value)


def test_is_idempotent_second_run_rewrites_nothing_and_does_not_fire_the_trigger(db):
    assert prop_idempotent(db, _M1252.read_text())


def test_lock_timeout_fails_fast_when_the_registry_is_locked(db):
    assert prop_lock_timeout_fails_fast(db, _M1252.read_text())


def test_post_check_refuses_a_silent_noop_update(db):
    assert prop_post_check_catches_a_silent_noop(db, _M1252.read_text())


# ── the four-state proof ─────────────────────────────────────────────────────

def test_fixture_shape_matches_the_production_shape():
    n_canon = sum(1 for ay in AYANAMSHAS for g in GRAHAS if old_label(SCORES[CANON][g]) != new_label(SCORES[CANON][g]))
    n_stale = sum(1 for ay in AYANAMSHAS for g in GRAHAS if old_label(SCORES[STALE_CH][g]) != new_label(SCORES[STALE_CH][g]))
    n_other = sum(1 for ay in AYANAMSHAS for g in GRAHAS if old_label(SCORES[OTHER_CH][g]) != new_label(SCORES[OTHER_CH][g]))
    assert (n_canon, n_stale, n_other) == (15, 5, 0), "15 canonical rows and 5 on the not-rebuilt chart, as in production"
    assert old_label(SCORES[CANON]["Saturn"]) == "mild" and new_label(SCORES[CANON]["Saturn"]) == "moderate"
    assert new_label(SCORES[CANON]["Sun"]) == "strong"


def test_four_state_proof_i_old_rows_with_the_live_clause_is_true(db):
    _seed(db, canon="old", stale="old", other="old")
    assert _passes(db, _registry_text(db)) is True
    assert _registry_text(db) == _old_check()


def test_four_state_proof_ii_canonical_rebuilt_with_the_live_clause_is_false(db):
    _seed(db, canon="new", stale="old", other="old")
    assert _passes(db, _registry_text(db)) is False, "the live clause rejects the new writer's labels (why 1252 exists)"
    # both the band cut (b) and the Saturn pin (c) are broken, independently: fixing Saturn alone does not help
    live = _registry_text(db)
    _exec(db, "UPDATE ga_medical SET indication_strength='mild' WHERE chart_id=%s AND graha='Saturn' AND ayanamsha_id='lahiri_chitrapaksha'", (CANON,))
    assert _passes(db, live) is False, "(b) still fails on the other 14 rows"


def test_four_state_proof_iii_canonical_rebuilt_with_1252_while_the_stale_chart_holds_mild_is_true(db):
    assert prop_scope_holds(db, _M1252.read_text())
    stale_mild = _q(db, "SELECT count(*) FROM ga_medical WHERE chart_id=%s AND indication_strength='mild' AND graha='Venus'", (STALE_CH,))[0][0]
    assert stale_mild == 5, "the not-rebuilt chart's five old-band rows are still there"
    # control: the TABLE-WIDE variant (scope dropped) is FALSE on exactly this state
    wide = _mutated("scope_dropped")
    other_db_text = _new_check(wide)
    assert _passes(db, other_db_text) is False


def test_four_state_proof_iv_every_chart_rebuilt_with_1252_is_true(db):
    assert prop_saturn_conjunct_is_moderate(db, _M1252.read_text())


def test_a_canonical_row_with_the_old_band_label_is_false_under_the_new_clause(db):
    assert prop_new_cut_is_enforced(db, _M1252.read_text())


def test_saturn_pinned_mild_is_false_and_sun_pinned_other_than_strong_is_false(db):
    _seed(db, canon="new", stale="new", other="new")
    _apply(db, _M1252)
    text = _registry_text(db)
    assert _passes(db, text) is True
    _exec(db, "UPDATE ga_medical SET indication_strength='mild' WHERE chart_id=%s AND ayanamsha_id='lahiri_chitrapaksha' AND graha='Saturn'", (CANON,))
    assert _passes(db, text) is False
    _exec(db, "UPDATE ga_medical SET indication_strength='moderate' WHERE chart_id=%s AND ayanamsha_id='lahiri_chitrapaksha' AND graha='Saturn'", (CANON,))
    assert _passes(db, text) is True
    _exec(db, "UPDATE ga_medical SET indication_strength='moderate' WHERE chart_id=%s AND ayanamsha_id='lahiri_chitrapaksha' AND graha='Sun'", (CANON,))
    assert _passes(db, text) is False


@pytest.mark.parametrize("score,label,expect", [
    (None, "unknown", True), (None, "moderate", False), (None, "mild", False),
    (0.0, "strong", True), (0.3999, "strong", True), (0.4, "moderate", True), (0.4, "strong", False),
    (0.6, "moderate", True), (0.6001, "moderate", True), (0.6999, "moderate", True), (0.6999, "mild", False),
    (0.7, "mild", True), (0.7, "moderate", False), (1.0, "mild", True),
])
def test_the_band_boundaries_of_clause_b_on_a_canonical_row(db, score, label, expect):
    """Lahiri Sun/Saturn stay golden so only the probed row (raman Mars) varies."""
    _seed(db, canon="new", stale="new", other="new")
    _apply(db, _M1252)
    _exec(db, "UPDATE ga_condition_composite SET condition_score=%s WHERE chart_id=%s AND ayanamsha_id='raman' AND graha='Mars'", (score, CANON))
    _exec(db, "UPDATE ga_medical SET indication_strength=%s WHERE chart_id=%s AND ayanamsha_id='raman' AND graha='Mars'", (label, CANON))
    assert _passes(db, _registry_text(db)) is expect


def test_a_canonical_row_with_no_composite_partner_fails_clause_b(db):
    _seed(db, canon="new", stale="new", other="new")
    _apply(db, _M1252)
    _exec(db, "DELETE FROM ga_condition_composite WHERE chart_id=%s AND ayanamsha_id='raman' AND graha='Mars'", (CANON,))
    assert _passes(db, _registry_text(db)) is False


def test_scope_is_canonical_only_other_charts_are_not_measured_and_the_live_clause_was_table_wide(db):
    """Documents the disclosed tradeoff (and the S-L1b widening task): a wrong label on a NON-canonical chart is not
    seen by the 1252 clause, and WAS seen by the live (740) clause. Conjunct (a) stays table-wide."""
    _seed(db, canon="new", stale="old", other="old")
    _exec(db, "UPDATE ga_medical SET indication_strength='strong' WHERE chart_id=%s AND graha='Venus' AND ayanamsha_id='raman'", (OTHER_CH,))
    live = _registry_text(db)
    _apply(db, _M1252)
    new = _registry_text(db)
    assert _passes(db, live) is False
    assert _passes(db, new) is True, "not measured by design (N-78)"
    _exec(db, "UPDATE ga_medical SET indication_tier='other' WHERE chart_id=%s AND graha='Venus' AND ayanamsha_id='raman'", (OTHER_CH,))
    assert _passes(db, new) is False, "(a) the disclosure-tier constant stays table-wide"


# ── mutations: each defect turns the matching proof red ──────────────────────

@pytest.mark.parametrize("kind,prop", [
    ("pre_guard_neutered", prop_refuses_an_unexpected_base),
    ("already_applied_branch_dropped", prop_idempotent),
    ("update_without_md5_where", prop_idempotent),
    ("scope_dropped", prop_scope_holds),
    ("saturn_left_mild", prop_saturn_conjunct_is_moderate),
    ("cut_left_old", prop_saturn_conjunct_is_moderate),
    ("lock_timeout_removed", prop_lock_timeout_fails_fast),
    ("post_check_neutered", prop_post_check_catches_a_silent_noop),
])
def test_mutation_is_caught(db, kind, prop):
    mutated = _mutated(kind)
    assert mutated != _M1252.read_text()
    assert prop(db, mutated) is False, f"mutation {kind!r} was NOT caught by {prop.__name__}"


def test_the_unmutated_file_passes_every_proof_the_mutations_are_judged_by(pg_cluster):
    """Sanity pairing for the mutation table: the same proofs, real file, each on a fresh clone."""
    psycopg, port = pg_cluster["psycopg"], pg_cluster["port"]
    text = _M1252.read_text()
    for i, prop in enumerate([prop_refuses_an_unexpected_base, prop_idempotent, prop_scope_holds,
                              prop_saturn_conjunct_is_moderate, prop_lock_timeout_fails_fast,
                              prop_post_check_catches_a_silent_noop]):
        name = f"sanity{i}"
        with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
            c.execute(f"CREATE DATABASE {name} TEMPLATE tmpl")
        try:
            def connect(_n=name, **kw):
                return psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname=_n, **kw)
            assert prop(connect, text) is True, prop.__name__
        finally:
            with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
                c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")


# ── combined: the S-L1 W1 window (1221, 1222, 1223, 1226, 1252, 1254 in one deploy) ──────────────────────────

# Stand-ins (the real files are other held PRs / not yet written, and are not in this tree). Each does what the
# real one does to the REGISTRY, through the same live trigger: 1221/1222/1254 = md5-guarded UPDATE of another
# asset's integrity_check_sql; 1223 = a spec-table-only change (no registry trigger); 1226 = append edges.
def _guarded_update(aid: str, tag: str) -> str:
    base_md5 = hashlib.md5(STAND_IN_CHECKS[aid].encode()).hexdigest()
    return f"""
SET LOCAL lock_timeout = '5s';
DO $$ BEGIN
  IF (SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id = '{aid}') IS DISTINCT FROM
     '{base_md5}' THEN RAISE EXCEPTION '{tag}-like guard tripped'; END IF; END $$;
UPDATE asset_registry SET integrity_check_sql = integrity_check_sql || E'\\n-- ({tag}) stand-in' WHERE asset_id = '{aid}';
"""


_STANDINS = {
    "1221": _guarded_update("ga_structural", "1221"),
    "1222": _guarded_update("ga_vargas", "1222"),
    "1223": "SET LOCAL lock_timeout = '5s'; CREATE TABLE IF NOT EXISTS standin_1223_specs (asset_id text); "
            "INSERT INTO standin_1223_specs SELECT 'ga_vargas' WHERE NOT EXISTS (SELECT 1 FROM standin_1223_specs);",
    "1226": """
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
""",
    "1254": _guarded_update("ga_sensitive", "1254"),
}
_WINDOW = ["1221", "1222", "1223", "1226", "1252", "1254"]
_DEGRADED = {"ga_structural", "ga_vargas", "ga_dashas", "ga_yoga", "ga_sensitive", "ga_medical"}
_final_snapshots: dict[str, tuple] = {}


def _apply_named(connect, name: str):
    if name == "1252":
        _apply(connect, _M1252)
    else:
        _apply(connect, None, text=_STANDINS[name])


def _final_state(connect):
    reg = _q(connect, "SELECT asset_id, depends_on::text, md5(integrity_check_sql) FROM asset_registry ORDER BY 1")
    fresh = [(a, c, s, r) for a, c, s, r, o in _freshness(connect)]
    return reg, fresh


def test_window_numeric_order_applies_cleanly_and_degrades_exactly_the_stated_set(db):
    for name in _WINDOW:
        _apply_named(db, name)
    assert _check_md5(db) == NEW_CHECK_MD5
    stale = {a for a, c, s, r, o in _freshness(db) if s == "stale"}
    assert stale == _DEGRADED, stale
    assert all(s == "stale" for a, c, s, r, o in _freshness(db) if a in stale), "every chart"
    assert all(s == "fresh" for a, c, s, r, o in _freshness(db) if a not in stale), "ga_vastu et al. untouched"
    assert _registry_text(db, "ga_vastu") == VASTU_TEXT


@pytest.mark.parametrize("order", list(itertools.permutations(_WINDOW)))
def test_no_apply_order_of_the_six_trips_a_guard_and_all_orders_reach_one_final_state(db, order):
    """All 720 permutations: every guard reads only its own row/column, so the window never depends on file order.
    Numeric order is what the runner uses; the rest also prove a re-run after a partial. One final state."""
    for name in order:
        _apply_named(db, name)
    state = _final_state(db)
    first = _final_snapshots.setdefault("state", state)
    assert state == first, f"order {order} reached a different final state"
    assert _check_md5(db) == NEW_CHECK_MD5
    assert {a for a, c, s, r in state[1] if s == "stale"} == _DEGRADED


def test_window_rerun_of_all_after_apply_is_a_noop_for_1252(db):
    for name in _WINDOW:
        _apply_named(db, name)
    snap = _q(db, "SELECT asset_id, xmin::text FROM asset_registry WHERE asset_id='ga_medical'")
    _apply_named(db, "1252")
    assert _q(db, "SELECT asset_id, xmin::text FROM asset_registry WHERE asset_id='ga_medical'") == snap
