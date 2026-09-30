"""A5.4 resonance_rebuild_R1_R6 — disposable-DB rehearsal of the WP3c (R-1..R-6)
resonance-map rebuild (FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0 T0-12, finding #9),
reworked per ASTRA_REVIEW_A5_4 P1-7 / P1-8 into a FAILING acceptance check.

NEVER production. Disposable identity is established in two steps, BEFORE
any cluster DDL (ASTRA_REVIEW_A5_4 v1.1 P1-7):
  * the DESTINATION CLUSTER is named by the operator: `--expect-cluster-id`
    (mandatory) must equal `SELECT system_identifier FROM
    pg_control_system()` on the maintenance connection — read before
    CREATE DATABASE; a mismatch or an unreadable identifier refuses. A
    forwarded production endpoint carries production's identifier and is
    therefore refused even over loopback with permissive credentials (the
    loopback check alone never established that — it only excluded remote
    hosts);
  * the DATABASE is created by this run (`<prefix>_<utc-stamp>_<hex>`),
    verified as the connected database and empty of user tables before any
    DDL/DML, used for everything, and DROPPED at the end (--keep-database
    retains it for inspection).

What it does, and what makes it FAIL (exit 1, failures listed):
  1. Applies the REAL migrations 459 + 1080 verbatim (plus minimal faithful
     DDL for the writer's inputs).
  2. Seeds the finding-#9 fixture on the canonical chart id (176
     sensitive-degree checks, 154 negative-result; a pre-WP3c legacy map
     partition keying them; a stopped prior-build yoga) AND a foreign
     chart's partition (the rollback must leave it untouched).
  3. Takes the runbook's uniquely named snapshot (resonance_rebuild_backup_
     sql.create_snapshot_sql) and records its count + content digest — the
     same statements the production runbook quotes.
  4. Runs the REAL writer (KaGocharaResonanceWriter.run(ctx); the harness
     owns commit) and evaluates the R-1..R-6 postconditions as ASSERTIONS
     with positive controls (an empty output cannot pass); dangling / NULL /
     out-of-vocabulary references are detected with NOT EXISTS; and the
     IDENTITIES are compared as exact sets against the fixture — the lord
     rows (class, token), the afflicted qualifiers (class, token), the
     positive sensitive fact ids, the arudha fact ids per cited house, the
     live yoga ids — so a transferred qualifier or a substituted input with
     the same totals fails; the runbook's R-5 EXCEPT pair is executed too.
  5. Re-runs the writer: the partition content digest must be identical
     (idempotent rebuild).
  6. Rehearses the rollback: (a) the runbook's rollback block with a WRONG
     recorded digest must REFUSE before deleting anything; (b) with the
     recorded values it must restore the exact preimage (digest equality)
     while the foreign partition's digest is unchanged; (c) a rebuild after
     the rollback must reproduce the post-rebuild digest.

Usage:
  python3 resonance_rebuild_disposable_rehearsal.py \
      --maintenance-dsn postgresql://wp6:local@127.0.0.1:55435/postgres \
      --expect-cluster-id <system_identifier of the DISPOSABLE cluster> \
      [--database-prefix rehearsal_a54] [--keep-database] [--json-out PATH]
"""
from __future__ import annotations

import argparse
import json
import re
import secrets
import sys
import uuid
from pathlib import Path
from urllib.parse import urlparse, urlunparse

SIDECAR = Path(__file__).resolve().parents[2]
# The production runner's two migration roots (platform/scripts/migrate.ts:834-835).
MIGRATION_ROOTS = (SIDECAR.parent / "migrations", SIDECAR.parent / "supabase" / "migrations")
MIGRATIONS = MIGRATION_ROOTS[0]
sys.path.insert(0, str(SIDECAR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import resonance_rebuild_backup_sql as B  # noqa: E402

LOOPBACK = {"localhost", "127.0.0.1", "::1"}

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER_CHART_ID = "11111111-1111-4111-8111-111111111111"  # foreign partition control
AYANAMSHA = "lahiri_chitrapaksha"

NEGATIVE_VALUES = list(B.NEGATIVE_VALUES)
POSITIVE_VALUES = list(B.POSITIVE_VALUES)
SENSITIVE_KEYS = ["mrityu_bhaga", "gandanta", "kartari", "pushkara"]
FIXTURE_SENSITIVE_TOTAL = 176
FIXTURE_SENSITIVE_NEGATIVE = 154
PRIOR_STOPPED_YOGA = "yoga_demo_stopped"

_DB_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,40}_[0-9]{14}_[0-9a-f]{6}$")

# (subject, sign_num) — graha_sign_attributes; LAGNA anchors whole-sign houses.
SIGN_NUMS = {
    "LAGNA": 1, "SUN": 5, "MOON": 4, "MAR": 8, "MER": 6, "JUP": 9,
    "VEN": 7, "SAT": 10, "RAH_MEAN": 11, "KET_MEAN": 5,
}

# Mirror of the migration seed (388 + 456) for the writer's 26 eligible classes,
# used by the DB-free tests; the live rehearsal loads the REAL seeded ontology and
# FAILS if this mirror drifts from it (verify_acceptance: mirror_matches_migration_seed).
# birth_anchor (migration 456, retained ontology row) is deliberately absent — N6.
SIGNATURE_MODELS = {
    "marriage": ([7, 2], ["7L"], ["Venus"]),
    "major_gain": ([2, 11], ["2L", "11L"], ["Jupiter", "Mercury"]),
    "career_advancement": ([10, 11], ["10L", "11L"], ["Sun"]),
    "illness_acute": ([6, 8], ["6L", "8L"], ["Mars", "Saturn"]),
    "chronic_onset": ([6, 8], ["6L", "8L"], ["Saturn"]),
    "surgery": ([6, 8], ["6L", "8L"], ["Mars"]),
    "career_entry": ([10, 6, 1], ["10L", "6L"], ["Sun", "Saturn"]),
    "career_change": ([10, 3, 9], ["10L"], ["Rahu"]),
    "career_setback": ([10, 6, 8, 12], ["10L afflicted"], ["Saturn", "Rahu"]),
    "business_launch": ([7, 10, 11], ["7L", "10L", "11L"], ["Mercury", "Jupiter"]),
    "education_milestone": ([4, 5, 9], ["4L", "5L", "9L"], ["Mercury", "Jupiter"]),
    "exam_outcome": ([5, 9], ["5L"], ["Mercury"]),
    "romantic_start": ([5, 7], ["5L", "7L"], ["Venus"]),
    "separation": ([6, 8, 12], ["7L afflicted"], ["Rahu", "Saturn", "Mars"]),
    "childbirth": ([5, 1], ["5L"], ["Jupiter"]),
    "parental_event": ([4, 9], ["4L", "9L"], ["Moon", "Sun"]),
    "bereavement": ([8, 12, 2], ["8L", "maraka lords (2L/7L)"], ["Saturn", "Ketu"]),
    "major_loss": ([2, 11, 12], ["2L/11L afflicted", "12L active"], ["Saturn", "Rahu"]),
    "property_acquisition": ([4], ["4L"], ["Mars"]),
    "relocation": ([4, 3, 12], ["4L", "3L"], ["Moon", "Rahu"]),
    "foreign_settlement": ([12, 9, 7], ["12L", "9L"], ["Rahu"]),
    "spiritual_turn": ([9, 12, 5], ["9L", "12L"], ["Jupiter", "Ketu"]),
    "achievement_recognition": ([10, 11, 5], ["10L", "11L", "5L"], ["Sun", "Mercury"]),
    "financial_deception": ([2, 11, 12], ["2L/11L afflicted", "12L active"], ["Rahu", "Saturn"]),
    "psychological_arc": ([1, 6, 12], ["1L", "6L"], ["Moon", "Mercury", "Saturn"]),
    "travel_event": ([3, 9, 12], ["3L", "9L"], ["Moon"]),
}

# ASTRA v1.3 amendment 1: every input table the writer reads is created from
# the CHECKED-IN MIGRATIONS, never hand-declared (the previous stub declared
# brahma_event_ontology.citations JSONB and chart_facts.fact_id UUID, masking
# the production TEXT[] / TEXT types). Only asset_registry — bookkeeping the
# ontology migrations INSERT/UPDATE into, never read by the writer — is a stub
# wide enough for those statements.
STUB_DDL = """
CREATE TABLE IF NOT EXISTS asset_registry (
    asset_id TEXT PRIMARY KEY, layer TEXT, sort_order INT,
    sanskrit_name TEXT, english_name TEXT, english_description TEXT,
    storage_type TEXT, target_table TEXT, count_sql TEXT, size_sql TEXT,
    target_floor INT, scope TEXT, is_active BOOLEAN, has_writer BOOLEAN,
    layer_name TEXT, layer_index TEXT, catalog_status TEXT, depends_on TEXT[],
    display_name TEXT, asset_type TEXT, has_substeps BOOLEAN
);
"""

# Tables whose DDL is EXTRACTED statement-by-statement from every migration
# that creates or alters them (CREATE TABLE / ALTER TABLE / CREATE INDEX ON /
# DO-blocks that ALTER them), in migration order — the seeds and
# asset_registry bookkeeping those files also carry are not applied.
DERIVED_TABLES = ("chart_facts", "chart_dashas", "ga_yoga_firings", "reference_signs",
                  "bg_transit_rules")
# Migrations applied VERBATIM: the ontology (its real 27-class seed — including
# the retained birth_anchor row — and citations TEXT[]) and the resonance map
# (459 table, 550 event_class FK to the ontology, 1080 resolution state).
VERBATIM_MIGRATIONS = ("388_brahma_ghatana_ontology.sql", "456_brahma_event_ontology_dr13_shapes.sql")
VERBATIM_MAP_MIGRATIONS = ("459_gochara_resonance_map.sql",
                           "550_gochara_resonance_map_event_class_fk.sql",
                           "1080_nirmana_l3_gochara_resonance_target_resolution_state.sql")


def find_migration(name: str) -> Path:
    for root in MIGRATION_ROOTS:
        p = root / name
        if p.is_file():
            return p
    raise FileNotFoundError(f"migration {name!r} not found under {MIGRATION_ROOTS}")


def _migration_sort_key(p: Path):
    m = re.match(r"^(\d+)_", p.name)
    return (1, int(m.group(1)), p.name) if m else (0, 0, p.name)


def split_sql_statements(text: str) -> list[str]:
    """Top-level SQL statements: comments stripped, ';' inside quoted strings
    and dollar-quoted (DO $$…$$) blocks never splits."""
    stmts, buf, i, n = [], [], 0, len(text)
    while i < n:
        if text.startswith("--", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        ch = text[i]
        if ch == "'":
            j = i + 1
            while j < n:
                if text[j] == "'" and text[j + 1:j + 2] == "'":
                    j += 2
                    continue
                if text[j] == "'":
                    break
                j += 1
            buf.append(text[i:j + 1])
            i = j + 1
            continue
        m = re.match(r"\$[A-Za-z_]*\$", text[i:])
        if m:
            tag = m.group(0)
            j = text.find(tag, i + len(tag))
            j = n if j < 0 else j + len(tag)
            buf.append(text[i:j])
            i = j
            continue
        if ch == ";":
            st = "".join(buf).strip()
            if st:
                stmts.append(st)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    st = "".join(buf).strip()
    if st:
        stmts.append(st)
    return stmts


def table_ddl_statements(text: str, table: str) -> list[str]:
    """The statements of one migration that define TABLE's schema: its
    CREATE TABLE, ALTER TABLE, CREATE [UNIQUE] INDEX … ON it, and DO blocks
    that ALTER it. Seeds, COMMENTs, other tables and bookkeeping are left."""
    keep = []
    T = re.escape(table)
    for st in split_sql_statements(text):
        head = re.sub(r"\s+", " ", st[:240])
        if re.match(rf"(?i)CREATE TABLE (IF NOT EXISTS )?(public\.)?{T}\b", head):
            keep.append(st)
        elif re.match(rf"(?i)ALTER TABLE (ONLY )?(public\.)?{T}\b", head):
            keep.append(st)
        elif (re.match(r"(?i)CREATE (UNIQUE )?INDEX", head)
              and re.search(rf"(?i)\bON (public\.)?{T}\b", head)):
            keep.append(st)
        elif (re.match(r"(?i)DO\s+\$", head)
              and re.search(rf"(?i)ALTER TABLE (ONLY )?(public\.)?{T}\b", st)):
            keep.append(st)
    return keep


def rehearsal_schema_plan() -> dict:
    """{table: [(migration file name, [statements])]} for every DERIVED
    table, scanned from BOTH migration roots in migration order — derived
    from the checked-in migrations, not hand-picked."""
    plan: dict = {}
    for table in DERIVED_TABLES:
        files = []
        for root in MIGRATION_ROOTS:
            for p in root.glob("*.sql"):
                if re.search(rf"\b{re.escape(table)}\b", p.read_text()):
                    files.append(p)
        entries = []
        for p in sorted(set(files), key=_migration_sort_key):
            stmts = table_ddl_statements(p.read_text(), table)
            if stmts:
                entries.append((p.name, stmts))
        plan[table] = entries
    return plan


def apply_rehearsal_schema(cur) -> dict:
    """Stub bookkeeping → ontology migrations verbatim → derived input-table
    DDL → resonance-map migrations verbatim. Returns what was applied."""
    applied: dict = {"stub_tables": ["asset_registry"], "verbatim": [], "derived": {}}
    cur.execute(STUB_DDL)
    for name in VERBATIM_MIGRATIONS:
        cur.execute(find_migration(name).read_text())
        applied["verbatim"].append(name)
    for table, entries in rehearsal_schema_plan().items():
        applied["derived"][table] = []
        for fname, stmts in entries:
            for st in stmts:
                cur.execute(st)
            applied["derived"][table].append({"migration": fname, "statements": len(stmts)})
    for name in VERBATIM_MAP_MIGRATIONS:
        cur.execute(find_migration(name).read_text())
        applied["verbatim"].append(name)
    return applied


def load_ontology_models(cur) -> dict:
    """The eligible classes' signature models as the WRITER reads them from
    the real (migration-seeded) ontology: {class: (houses[int], lords[raw],
    karakas[raw], citation|None)}; also the retained non-eligible classes
    present in the table."""
    rows = cur.execute(
        "SELECT event_class_id, signature_model, citations FROM brahma_event_ontology"
        " ORDER BY event_class_id").fetchall()
    models, others = {}, []
    for cls, sm, cites in rows:
        if cls not in B.ELIGIBLE_EVENT_CLASSES:
            others.append(cls)
            continue
        houses = sorted({int(str(h).strip()) for h in (sm.get("houses") or []) if str(h).strip().isdigit()})
        models[cls] = (houses, list(sm.get("lords") or []), list(sm.get("karakas") or []),
                       "; ".join(cites) if cites else None)
    return {"models": models, "non_eligible_present": others}


SIGN_LORDS = [
    (1, "Mars"), (2, "Venus"), (3, "Mercury"), (4, "Moon"), (5, "Sun"),
    (6, "Mercury"), (7, "Venus"), (8, "Mars"), (9, "Jupiter"), (10, "Saturn"),
    (11, "Saturn"), (12, "Jupiter"),
]


def expected_lord_identities(signature_models: dict = SIGNATURE_MODELS):
    """(lord_set, afflicted_set) of (event_class, '<n>L') pairs exactly as
    the writer tokenises them (_LORD_TOKEN_RE r'\\d+L' per entry; the
    'afflicted' qualifier rides the entry; tokens deduplicated per class)."""
    lords: set = set()
    afflicted: set = set()
    for cls, (_houses, entries, _karakas) in signature_models.items():
        for entry in entries:
            for token in re.findall(r"\d+L", entry):
                lords.add((cls, token))
                if "afflicted" in entry:
                    afflicted.add((cls, token))
    return lords, afflicted


KARAKA_SUBJECT = {"sun": "SUN", "moon": "MOON", "mars": "MAR", "mercury": "MER",
                  "jupiter": "JUP", "venus": "VEN", "saturn": "SAT", "rahu": "RAH_MEAN",
                  "ketu": "KET_MEAN"}
KARAKA_TITLE_NAMES = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
SIGN_NAMES = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
              "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def expected_row_tuples(fixture: dict, signature_models: dict = SIGNATURE_MODELS) -> set:
    """The writer's expected output as FULL tuples (event_class, target_type,
    target_ref, weight, resolution_state, qualifier, uncited, citation) for
    every type the fixture determines exactly (ASTRA v1.2 P1-3): sensitive
    facts by the class's kārakas (canonical ayanāṃśa, positive pairs),
    arudha / bhava_arudha by the class's houses (A12 invalid ⇒ unavailable),
    yoga ids by constituent_houses ∩ houses or constituent_planets ∩ kārakas
    with the bhanga qualifier, lords (tokens + afflicted qualifier), kārakas,
    bhavas with the ontology citation. Class association and retained values
    are part of the identity — a swap between classes or a changed weight
    with the same totals fails."""
    out = set()
    for cls, (houses, lords, karakas) in signature_models.items():
        cite = fixture["citation_by_class"][cls]
        kl = {str(k).lower() for k in karakas}
        for h in houses:
            out.add((cls, "bhava", str(h), 1.0, "resolved", None, False, cite))
            fid = fixture["arudha_fact_ids_by_house"].get(h)
            state = "resolved" if fixture["arudha_sign_by_house"].get(h) in SIGN_NAMES else "unavailable"
            if fid:
                out.add((cls, "arudha", fid, 0.6, state, None, True, None))
            out.add((cls, "bhava_arudha", f"BHAVA_ARUDHA_A{h}", 0.6, state, None, True, None))
        for entry in lords:
            q = "afflicted" if "afflicted" in entry else None
            for token in re.findall(r"\d+L", entry):
                out.add((cls, "lord", token, 1.0, "resolved", q, False, cite))
        for k in karakas:
            out.add((cls, "karaka", str(k), 1.0, "resolved", None, False, cite))
        # the writer keys _KARAKA_FACT_SUBJECT by the EXACT title-case name
        subjects = {KARAKA_SUBJECT[str(k).lower()] for k in karakas
                    if str(k) in KARAKA_TITLE_NAMES}
        for fid, subj in fixture["positive_facts"]:
            if subj in subjects:
                out.add((cls, "sensitive_degree", fid, 0.5, "resolved", None, True, None))
        for yid, y_houses, y_planets, bhanga in fixture["live_yogas"]:
            if set(y_houses) & set(houses) or set(y_planets) & kl:
                out.add((cls, "yoga_constituent", yid, 0.7, "resolved",
                         "bhanga_active" if bhanga else None, True, None))
    return out


EXACT_TYPES = ("bhava", "lord", "karaka", "sensitive_degree", "arudha", "bhava_arudha",
               "yoga_constituent")


def expected_afflicted_lord_rows(signature_models: dict = SIGNATURE_MODELS) -> int:
    """R-5 positive control: every '<n>L afflicted' lord reference in the
    seeded signature models must survive as a lord row with
    target_qualifier='afflicted' (e.g. '2L/11L afflicted' ⇒ 2 rows)."""
    total = 0
    for _cls, (_houses, lords, _karakas) in signature_models.items():
        for entry in lords:
            if "afflicted" in entry:
                total += len(re.findall(r"\d+L", entry))
    return total


# ── acceptance (pure; unit-tested) ───────────────────────────────────────────

def verify_acceptance(ver: dict) -> list[str]:
    """R-1..R-6 + rerun + rollback as FAILING assertions. Returns the list
    of violated checks (empty ⇒ accepted). Every zero-count check carries a
    positive control so an empty or no-op build cannot pass."""
    f: list[str] = []
    b, a = ver["before"], ver["after"]
    if (b["sensitive_total"], b["sensitive_negative"]) != (
            FIXTURE_SENSITIVE_TOTAL, FIXTURE_SENSITIVE_NEGATIVE):
        f.append(f"fixture control: expected {FIXTURE_SENSITIVE_NEGATIVE}/"
                 f"{FIXTURE_SENSITIVE_TOTAL} negative sensitive targets before, "
                 f"got {b['sensitive_negative']}/{b['sensitive_total']}")
    if a["total"] <= 0:
        f.append("R-6 control: rebuilt partition is empty")
    if a["sensitive_negative"] != 0:
        f.append(f"R-1: {a['sensitive_negative']} negative-result sensitive targets remain")
    if a["sensitive_total"] <= 0:
        f.append("R-1 control: no sensitive_degree rows kept (positive facts exist)")
    if a["sensitive_total"] != ver["sensitive_keyed_to_positive_facts"]:
        f.append("R-1: kept sensitive rows are not all keyed to positive-result facts")
    if ver["dangling_or_null_refs"] != 0:
        f.append(f"refs: {ver['dangling_or_null_refs']} NULL / dangling / non-uuid target refs")
    if ver["rows_missing_or_bad_resolution_state"] != 0:
        f.append(f"R-6: {ver['rows_missing_or_bad_resolution_state']} rows with NULL/invalid state")
    if ver["arudha_rows"] <= 0 or not ver["arudha_all_keyed_to_sign_facts"]:
        f.append("R-2: arudha rows absent or not all keyed to fact_key='sign' facts")
    if ver["arudha_invalid_sign_unavailable"] <= 0:
        f.append("R-2 control: the invalid ARUDHA_A12 sign did not surface as 'unavailable'")
    if ver["yoga_rows"] <= 0 or ver["yoga_refs_not_live_fired"] != 0:
        f.append("R-3: yoga rows absent or a ref is not backed by a live fired firing")
    dropped = ver["writer_notes"].get("yoga_constituent", {}).get("dropped_since_prior_build")
    if dropped != [PRIOR_STOPPED_YOGA]:
        f.append(f"R-3 drift: dropped_since_prior_build={dropped!r}, expected [{PRIOR_STOPPED_YOGA!r}]")
    if ver["lord_rows"] <= 0 or set(ver["lord_states"]) != {"resolved"}:
        f.append(f"R-4: lord rows {ver['lord_rows']} states {ver['lord_states']} (expected all resolved)")
    if ver["expected_afflicted_rows"] <= 0 or ver["afflicted_qualifier_rows"] != ver["expected_afflicted_rows"]:
        f.append(f"R-5: afflicted qualifier rows {ver['afflicted_qualifier_rows']} != expected "
                 f"{ver['expected_afflicted_rows']}")
    ids = ver.get("identities") or {}
    for name in ("lord_rows", "afflicted_rows", "sensitive_rows", "arudha_rows",
                 "yoga_rows", "exact_row_tuples"):
        exp = ids.get(name, {}).get("expected")
        act = ids.get(name, {}).get("actual")
        if exp is None or act is None:
            f.append(f"identity: {name} not measured")
            continue
        exp_l, act_l = sorted(map(str, exp)), sorted(map(str, act))
        if not exp_l:
            f.append(f"identity control: expected {name} set is empty")
        if exp_l != act_l:
            missing = sorted(set(exp_l) - set(act_l))[:5]
            extra = sorted(set(act_l) - set(exp_l))[:5]
            f.append(f"identity: {name} differs (missing {missing}, extra {extra})")
    if ver.get("value_invariant_violations", 1) != 0:
        f.append(f"values: {ver.get('value_invariant_violations')} rows violate the writer's "
                 "declared weight/provenance/state/qualifier invariants")
    for name in ("r1_identity_sql", "r2_identity_sql", "r3_identity_sql", "r4_identity_sql"):
        pair = ver.get(name) or {}
        if pair.get("actual_not_expected") != 0 or pair.get("expected_not_actual") != 0:
            f.append(f"{name}: EXCEPT rows {pair} (both directions must be 0)")
    dc = ver.get("detector_controls")
    if not dc:
        f.append("detector controls: not run")
    else:
        for name, c in dc.items():
            if name in ("clean", "restored_after_controls"):
                continue
            if c.get("count_preservation_expected", True):
                if not (c.get("counts_preserved") and c.get("global_id_sets_preserved")):
                    f.append(f"detector control {name}: mutation did not preserve per-class counts "
                             "and global id sets (control invalid)")
            elif not c.get("mutation_applied"):
                f.append(f"detector control {name}: mutation was not applied (control invalid)")
            if not c.get("detected"):
                f.append(f"detector control {name}: NOT detected by the identity/value checks")
        if dc.get("restored_after_controls") is not True:
            f.append("detector controls: map not restored after the rolled-back mutations")
    if ver.get("map_unchanged_after_detector_controls") is not True:
        f.append("detector controls: post-control digest differs from the rerun digest")
    if ver.get("negative_fact_ids_referenced", 1) != 0:
        f.append("identity: a negative-result sensitive fact id is referenced")
    onto = ver.get("ontology") or {}
    if onto.get("birth_anchor_present_in_ontology") is not True:
        f.append("ontology control: the retained birth_anchor row is absent from the fixture ontology")
    if onto.get("birth_anchor_rows_in_map", 1) != 0:
        f.append(f"N6: {onto.get('birth_anchor_rows_in_map')} birth_anchor rows in the map")
    if onto.get("map_classes_equal_eligible") is not True:
        f.append("class universe: map classes differ from the writer's TARGET_EVENT_CLASSES")
    if onto.get("mirror_matches_migration_seed") is not True:
        f.append(f"ontology: SIGNATURE_MODELS mirror differs from the migration seed for {onto.get('mirror_diff')}")
    if onto.get("citations_type") != "ARRAY" or onto.get("chart_facts_fact_id_type") != "text":
        f.append(f"schema: citations {onto.get('citations_type')!r} / fact_id {onto.get('chart_facts_fact_id_type')!r}"
                 " — not the migrations' TEXT[] / TEXT")
    r5 = ver.get("r5_identity_sql") or {}
    if r5.get("qualified_not_in_ontology") != 0 or r5.get("ontology_not_qualified") != 0:
        f.append(f"R-5 SQL identity: EXCEPT rows {r5} (both must be 0)")
    sd = ver["writer_notes"].get("sensitive_degree", {})
    if not isinstance(sd.get("negative_dropped_zero_rows"), int) or sd["negative_dropped_zero_rows"] <= 0:
        f.append("notes: sensitive_degree.negative_dropped_zero_rows absent or zero (per-class exclusion counter)")
    if ver.get("rerun_digest_equal") is not True:
        f.append("idempotency: second writer run changed the partition content digest")
    snap = ver.get("snapshot") or {}
    if snap.get("full_row_matches_live_preimage") is not True or snap.get("recorded_count", 0) <= 0:
        f.append("snapshot: the full-row certificate of the snapshot does not equal the live "
                 "preimage (or the snapshot is empty) — the destructive phase must not run")
    rb = ver.get("rollback") or {}
    pre, post = rb.get("pre_refusal_full_certificate"), rb.get("post_refusal_full_certificate")
    if pre is None or post is None:
        f.append("refuse: pre-/post-refusal full certificates not recorded (the untouched claim "
                 "must rest on two recorded certificates, never on one digest compared to itself)")
    elif list(pre) != list(post) or not pre[0] or pre[1] in ("empty", "", None):
        f.append(f"refuse: partition changed across the refusal probe (pre {pre}, post {post})")
    if rb.get("refused_on_stale_snapshot") is not True or rb.get("partition_untouched_after_refusal") is not True:
        f.append("rollback: the refuse-unless-verified block did not refuse a stale snapshot before deleting")
    if rb.get("restored_full_row_digest_equal") is not True:
        f.append("rollback: restored partition is not the exact preimage (full-row certificate)")
    if rb.get("other_chart_untouched") is not True:
        f.append("rollback: the foreign chart's partition changed")
    if rb.get("rebuild_after_rollback_digest_equal") is not True:
        f.append("rollback: rebuild after rollback did not reproduce the post-rebuild digest")
    return f


# ── disposable identity by construction ──────────────────────────────────────

def _require_loopback(dsn: str) -> None:
    parsed = urlparse(dsn)
    if (parsed.hostname or "") not in LOOPBACK:
        raise SystemExit(f"REFUSED: maintenance DSN {dsn!r} is not loopback.")


def assert_cluster_identity(conn, expect_cluster_id: str) -> dict:
    """BEFORE any cluster DDL: the destination cluster's system_identifier
    (pg_control_system) must equal the operator-stated disposable id."""
    try:
        actual = str(conn.execute(
            "SELECT system_identifier FROM pg_control_system()").fetchone()[0])
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"REFUSED: cannot read the cluster identifier "
                         f"(pg_control_system): {exc}")
    if str(expect_cluster_id).strip() != actual:
        raise SystemExit(f"REFUSED: cluster system_identifier {actual} is not the "
                         f"expected disposable cluster {expect_cluster_id}")
    return {"system_identifier": actual}


def establish_disposable_database(maintenance_dsn: str, prefix: str,
                                  expect_cluster_id: str | None = None):
    """Create a fresh database this run owns; return (dsn, name). The
    cluster identity is asserted on the maintenance connection BEFORE the
    CREATE DATABASE."""
    import psycopg
    _require_loopback(maintenance_dsn)
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,40}", prefix):
        raise SystemExit(f"REFUSED: bad database prefix {prefix!r}")
    if not expect_cluster_id:
        raise SystemExit("REFUSED: --expect-cluster-id is required (the disposable "
                         "cluster's pg_control_system() system_identifier)")
    name = f"{prefix}_{B.new_stamp_utc()}_{secrets.token_hex(3)}"
    assert _DB_NAME_RE.match(name)
    with psycopg.connect(maintenance_dsn, autocommit=True) as m:
        assert_cluster_identity(m, expect_cluster_id)
        m.execute(f'CREATE DATABASE "{name}"')
    parsed = urlparse(maintenance_dsn)
    dsn = urlunparse(parsed._replace(path=f"/{name}"))
    return dsn, name


def assert_disposable_identity(conn, expected_name: str) -> dict:
    """Before any DDL/DML: the connected database IS the one this run
    created (name equality + the run's naming pattern) and holds no user
    tables. Together with the loopback maintenance DSN these establish the
    identity by construction. `inet_server_addr()` is recorded as a
    diagnostic only: a containerised disposable reports its container
    address (e.g. 172.17.0.x) even when the client connected over loopback,
    so it is not a discriminating test."""
    cur_db = conn.execute("SELECT current_database()").fetchone()[0]
    addr = conn.execute("SELECT host(inet_server_addr())").fetchone()[0]
    user_tables = conn.execute(
        "SELECT COUNT(*) FROM pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema')"
    ).fetchone()[0]
    if cur_db != expected_name or not _DB_NAME_RE.match(cur_db):
        raise SystemExit(f"REFUSED: connected to {cur_db!r}, not the created database {expected_name!r}")
    if user_tables != 0:
        raise SystemExit(f"REFUSED: database {cur_db!r} already has {user_tables} user tables — not fresh")
    return {"database": cur_db, "server_addr_diagnostic": addr,
            "user_tables_before": user_tables,
            "identity_basis": "created by this run over a loopback maintenance DSN; "
                              "name equality; zero user tables"}


def drop_disposable_database(maintenance_dsn: str, name: str) -> None:
    import psycopg
    assert _DB_NAME_RE.match(name)
    with psycopg.connect(maintenance_dsn, autocommit=True) as m:
        m.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


# ── the rehearsal ─────────────────────────────────────────────────────────────

def _digest(cur, table: str, chart_id: str):
    """(count, CONTENT digest) — the ID-independent rerun comparison."""
    n, d = cur.execute(B.partition_digest_sql(table, chart_id)).fetchone()
    return int(n), str(d)


def _full_digest(cur, table: str, chart_id: str):
    """(count, FULL-ROW digest) — the typed preimage certificate (every
    column, ids and computed_at included)."""
    n, d = cur.execute(B.full_row_digest_sql(table, chart_id)).fetchone()
    return int(n), str(d)


def _seed(cur) -> dict:
    """Seed the fixture; return its identities (fact ids by role) for the
    exact-set acceptance checks."""
    # The ontology is the REAL migration seed (388 + 456): 27 classes including
    # the retained, never-eligible birth_anchor row; citations TEXT[].
    onto = load_ontology_models(cur)
    identities: dict = {"positive_fact_ids": [], "negative_fact_ids": [],
                        "positive_facts": [],  # (fact_id, subject)
                        "arudha_fact_ids_by_house": {}, "arudha_sign_by_house": {},
                        "live_yoga_ids": ["yoga_demo_gajakesari", "yoga_demo_bhanga"],
                        "live_yogas": [("yoga_demo_gajakesari", [7, 11], ["venus", "jupiter"], False),
                                       ("yoga_demo_bhanga", [10], ["sun"], True)],
                        "citation_by_class": {c: m[3] for c, m in onto["models"].items()},
                        "db_signature_models": {c: (m[0], m[1], m[2]) for c, m in onto["models"].items()},
                        "non_eligible_classes_present": onto["non_eligible_present"]}
    cur.executemany(
        "INSERT INTO bg_transit_rules (rule_type, graha, primary_house, phala, classical_citation)"
        " VALUES (%s, %s, %s, %s, %s)",
        [("favourable", "venus", 7, "gain (synthetic rehearsal)", "BPHS ch.29 (synthetic rehearsal)"),
         ("favourable", "jupiter", 11, "gain (synthetic rehearsal)", "BPHS ch.29 (synthetic rehearsal)"),
         ("unfavourable", "saturn", 8, "loss (synthetic rehearsal)", "Phaladeepika ch.26 (synthetic rehearsal)")],
    )
    cur.executemany(
        "INSERT INTO reference_signs (sign_id, canonical_name_en, canonical_name_sa, lord, element,"
        " modality, natural_house, is_odd, is_biped, source_citation)"
        " VALUES (%s, %s, %s, %s, 'fire', 'movable', %s, %s, TRUE, 'BPHS ch.1 (synthetic rehearsal)')",
        [(n, SIGN_NAMES[n - 1], SIGN_NAMES[n - 1], lord, n, n % 2 == 1) for n, lord in SIGN_LORDS])

    fact_rows = []
    build_id = str(uuid.uuid4())

    def add_fact(category, subject, key, text=None, num=None, formula_id=None):
        fid = uuid.uuid4()
        fact_rows.append((str(fid), CHART_ID, AYANAMSHA, build_id, category, subject, key, text,
                          num, formula_id))
        return fid

    for subject, sign_num in SIGN_NUMS.items():
        add_fact("graha_sign_attributes", subject, "sign_num", num=sign_num)
        add_fact("graha_position", subject, "longitude_sidereal",
                 num=(sign_num - 1) * 30 + 12.3456)

    # Finding-#9 shape: 176 sensitive-degree checks, 154 negative-result.
    subjects = [s for s in SIGN_NUMS if s != "LAGNA"]
    sensitive_fact_ids: list[tuple[str, str]] = []
    vocab = {"mrityu_bhaga": ("fired", "not_fired"),
             "gandanta": ("gandanta", "not_gandanta"),
             "kartari": ("papa_kartari", "none"),
             "pushkara": ("pushkara", "not_pushkara")}
    for i in range(FIXTURE_SENSITIVE_TOTAL):
        subject = subjects[i % len(subjects)]
        key = SENSITIVE_KEYS[i % len(SENSITIVE_KEYS)]
        pos, neg = vocab[key]
        value = neg if i < FIXTURE_SENSITIVE_NEGATIVE else pos
        # migration 215's dedup index admits one (subject, key, build) per
        # formula variant: 176 rows = 5 variant families × 36 (subject, key) pairs
        fid = add_fact("sensitive_degree_check", subject, key, text=value,
                       formula_id=f"rehearsal_variant_{i // (len(subjects) * len(SENSITIVE_KEYS))}")
        sensitive_fact_ids.append((str(fid), value))
        (identities["negative_fact_ids"] if i < FIXTURE_SENSITIVE_NEGATIVE
         else identities["positive_fact_ids"]).append(str(fid))
        if i >= FIXTURE_SENSITIVE_NEGATIVE:
            identities["positive_facts"].append((str(fid), subject))

    for h in range(1, 13):
        sign_name = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                     "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius",
                     "not_a_sign"][h - 1]  # A12 deliberately invalid (R-2 honesty)
        identities["arudha_fact_ids_by_house"][h] = str(
            add_fact("arudha_pada", f"ARUDHA_A{h}", "sign", text=sign_name))
        identities["arudha_sign_by_house"][h] = sign_name

    add_fact("sensitive_point_gulika_mandi", "MANDI", "sign", text="Aries")
    add_fact("sensitive_point_gulika_mandi", "GULIKA", "sign", text="Taurus")
    add_fact("sensitive_point_gulika_mandi", "YAMAKANTAKA", "sign", text="Gemini")
    add_fact("panchanga_nakshatra_moon", "NAKSHATRA_MOON_BIRTH", "number", num=4)

    cur.executemany(
        "INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id, build_id, fact_category,"
        " fact_subject, fact_key, fact_value_text, fact_value_num, formula_id,"
        " citation_ref, citation_human, source_calculation, verification_pass_status,"
        " engine_version, computed_at)"
        " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'rehearsal', 'synthetic rehearsal fact',"
        " 'fixture', 'two_pass_verified', 'rehearsal-0', NOW())",
        fact_rows,
    )
    cur.executemany(
        "INSERT INTO ga_yoga_firings (chart_id, ayanamsha_id, yoga_canonical_id, fired,"
        " constituent_fact_ids, constituent_planets, constituent_houses, bhanga_active)"
        " VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s)",
        [(CHART_ID, AYANAMSHA, "yoga_demo_gajakesari", True, '["f1","f2"]',
          '["venus","jupiter"]', "[7, 11]", False),
         (CHART_ID, AYANAMSHA, "yoga_demo_bhanga", True, '["f3"]',
          '["sun"]', "[10]", True),
         (CHART_ID, AYANAMSHA, PRIOR_STOPPED_YOGA, False, '["f4"]',
          '["moon"]', "[4]", False)],
    )
    cur.executemany(
        "INSERT INTO chart_dashas (chart_id, ayanamsha_id, build_id, system_id, level_n, lord_graha,"
        " start_date, end_date, start_iso, end_iso, duration_days, verification_pass_status,"
        " verification_method, citation_ref, citation_human, engine_version)"
        " VALUES (%s, %s, %s, 'vimshottari', 1, %s, %s, %s, %s, %s, %s, 'two_pass_verified',"
        " 'fixture', 'rehearsal', 'synthetic rehearsal dasha', 'rehearsal-0')",
        [(CHART_ID, AYANAMSHA, build_id, lord, f"{1984 + 10 * i}-01-01", f"{1994 + 10 * i}-01-01",
          f"{1984 + 10 * i}-01-01T00:00:00Z", f"{1994 + 10 * i}-01-01T00:00:00Z", 3652)
         for i, lord in enumerate(("venus", "jupiter", "saturn", "sun", "moon", "mars", "mercury",
                                   "rahu", "ketu"))],
    )
    # the BEFORE partition (pre-WP3c legacy map, finding #9 verbatim shape)
    for fid, _value in sensitive_fact_ids:
        cur.execute(
            "INSERT INTO gochara_resonance_map (chart_id, event_class, target_type,"
            " target_ref, weight, classical_citation, uncited_extension)"
            " VALUES (%s, 'marriage', 'sensitive_degree', %s, 0.5, NULL, TRUE)",
            (CHART_ID, fid),
        )
    cur.execute(
        "INSERT INTO gochara_resonance_map (chart_id, event_class, target_type,"
        " target_ref, weight, classical_citation, uncited_extension)"
        " VALUES (%s, 'marriage', 'yoga_constituent', %s, 0.7, NULL, TRUE)",
        (CHART_ID, PRIOR_STOPPED_YOGA),
    )
    # the FOREIGN partition (must survive the rebuild AND the rollback untouched)
    cur.executemany(
        "INSERT INTO gochara_resonance_map (chart_id, event_class, target_type,"
        " target_ref, weight, classical_citation, uncited_extension)"
        " VALUES (%s, %s, %s, %s, %s, %s, TRUE)",
        [(OTHER_CHART_ID, "marriage", "karaka", "Venus", 0.9, None),
         (OTHER_CHART_ID, "career_entry", "bhava", "10", 0.6, None),
         (OTHER_CHART_ID, "childbirth", "lord", "5L", 0.7, None)],
    )
    return identities


def _counts(cur, label):
    out = {"label": label}
    out["total"] = cur.execute(
        "SELECT COUNT(*) FROM gochara_resonance_map WHERE chart_id=%s", (CHART_ID,)).fetchone()[0]
    out["by_type"] = dict(cur.execute(
        "SELECT target_type, COUNT(*) FROM gochara_resonance_map WHERE chart_id=%s"
        " GROUP BY target_type ORDER BY target_type", (CHART_ID,)).fetchall())
    out["sensitive_negative"] = cur.execute(B.negative_sensitive_targets_sql(CHART_ID)).fetchone()[0]
    out["sensitive_total"] = out["by_type"].get("sensitive_degree", 0)
    return out


def _map_shape(cur) -> tuple[list, dict]:
    """(per-class-per-type counts, per-type GLOBAL DISTINCT target_ref sets)
    — the two quantities a count-only or global-DISTINCT acceptance sees."""
    counts = cur.execute(
        "SELECT event_class, target_type, COUNT(*) FROM gochara_resonance_map"
        " WHERE chart_id=%s GROUP BY 1, 2 ORDER BY 1, 2", (CHART_ID,)).fetchall()
    ids: dict = {}
    for ty, ref in cur.execute(
            "SELECT DISTINCT target_type, target_ref FROM gochara_resonance_map"
            " WHERE chart_id=%s", (CHART_ID,)).fetchall():
        ids.setdefault(ty, set()).add(ref)
    return [tuple(map(str, c)) for c in counts], {k: sorted(v) for k, v in ids.items()}


def _swap_refs(cur, target_type: str, a: tuple[str, str], b: tuple[str, str]) -> None:
    """Exchange target_ref between (class_a, ref_a) and (class_b, ref_b) of one
    type — per-class counts and the global id set are unchanged; only the
    CLASS ASSOCIATION moves (the mutation a global-DISTINCT identity cannot see)."""
    (ca, ra), (cb, rb_) = a, b
    key = "chart_id=%s AND event_class=%s AND target_type=%s AND target_ref=%s"
    cur.execute(f"UPDATE gochara_resonance_map SET target_ref='__swap__' WHERE {key}",
                (CHART_ID, ca, target_type, ra))
    cur.execute(f"UPDATE gochara_resonance_map SET target_ref=%s WHERE {key}",
                (ra, CHART_ID, cb, target_type, rb_))
    cur.execute(f"UPDATE gochara_resonance_map SET target_ref=%s WHERE {key}",
                (rb_, CHART_ID, ca, target_type, "__swap__"))


def _detector_controls(cur) -> dict:
    """ASTRA v1.2 P1-3 positive controls, run INSIDE a savepoint and rolled
    back: each mutation preserves every per-class count and every global
    target_ref set (so a totals-only or global-DISTINCT acceptance would
    still pass) and MUST be caught by the identity / value checks the
    runbook prints. A control that is not detected is an acceptance failure
    — the detectors are proven live on this run, not assumed."""
    def first_ref(cls, ty):
        row = cur.execute(
            "SELECT target_ref FROM gochara_resonance_map WHERE chart_id=%s AND event_class=%s"
            " AND target_type=%s ORDER BY target_ref LIMIT 1", (CHART_ID, cls, ty)).fetchone()
        return row[0] if row else None

    def measure():
        out = {"value_violations": len(cur.execute(B.value_invariants_sql(CHART_ID)).fetchall())}
        for nm, fn in (("r1", B.r1_identity_sql), ("r2", B.r2_identity_sql), ("r3", B.r3_identity_sql),
                       ("r4", B.r4_lord_identity_sql)):
            fwd, rev = fn(CHART_ID)
            out[nm] = (len(cur.execute(fwd).fetchall()), len(cur.execute(rev).fetchall()))
        q1, q2 = B.r5_qualifier_identity_sql(CHART_ID)
        out["r5"] = (len(cur.execute(q1).fetchall()), len(cur.execute(q2).fetchall()))
        return out

    upd = "UPDATE gochara_resonance_map SET {} WHERE chart_id=%s AND event_class=%s AND target_type=%s AND target_ref=%s"
    controls = {
        # class association moved, ids and counts intact:
        "sensitive_class_swap": (
            lambda: _swap_refs(cur, "sensitive_degree",
                               ("marriage", first_ref("marriage", "sensitive_degree")),
                               ("surgery", first_ref("surgery", "sensitive_degree"))),
            lambda m: m["r1"][0] >= 1 and m["r1"][1] >= 1),
        "arudha_class_swap": (
            lambda: _swap_refs(cur, "arudha",
                               ("marriage", first_ref("marriage", "arudha")),
                               ("surgery", first_ref("surgery", "arudha"))),
            lambda m: m["r2"][0] >= 1 and m["r2"][1] >= 1),
        "yoga_class_swap": (
            lambda: _swap_refs(cur, "yoga_constituent",
                               ("marriage", "yoga_demo_gajakesari"),
                               ("career_entry", "yoga_demo_bhanga")),
            lambda m: m["r3"][0] >= 1 and m["r3"][1] >= 1),
        # retained values changed, identity intact:
        "weight_changed": (
            lambda: cur.execute(upd.format("weight=0.9"), (CHART_ID, "marriage", "bhava", "7")),
            lambda m: m["value_violations"] >= 1),
        "qualifier_transferred": (
            lambda: (cur.execute(upd.format("target_qualifier=NULL"),
                                 (CHART_ID, "career_setback", "lord", "10L")),
                     cur.execute(upd.format("target_qualifier='afflicted'"),
                                 (CHART_ID, "marriage", "lord", "7L"))),
            lambda m: m["r5"][0] >= 1 and m["r5"][1] >= 1 and m["value_violations"] >= 2),
        "resolution_state_flipped": (
            lambda: (cur.execute(upd.format("target_resolution_state='unavailable'"),
                                 (CHART_ID, "marriage", "sensitive_degree",
                                  first_ref("marriage", "sensitive_degree"))),
                     cur.execute(upd.format("target_resolution_state='unqualified'"),
                                 (CHART_ID, "marriage", "lord", "7L"))),
            lambda m: m["value_violations"] >= 2),
        "provenance_flipped": (
            lambda: (cur.execute(upd.format("uncited_extension=TRUE, classical_citation=NULL"),
                                 (CHART_ID, "marriage", "karaka", "Venus")),
                     cur.execute(upd.format("classical_citation='fabricated'"),
                                 (CHART_ID, "marriage", "sensitive_degree",
                                  first_ref("marriage", "sensitive_degree")))),
            lambda m: m["value_violations"] >= 2),
        # ASTRA v1.3 amendment 3: the reviewer's replay — marriage:7L → marriage:2L with
        # weight / state / citation / qualifier preserved (2L is a valid token elsewhere,
        # so per-class counts AND the global lord id set are unchanged): R-4 both directions
        "lord_token_wrong": (
            lambda: cur.execute(upd.format("target_ref='2L'"), (CHART_ID, "marriage", "lord", "7L")),
            lambda m: m["r4"][0] >= 1 and m["r4"][1] >= 1),
        # a MISSING token (marriage:7L deleted): the second direction; count changes by design
        "lord_token_missing": (
            lambda: cur.execute("DELETE FROM gochara_resonance_map WHERE chart_id=%s AND event_class=%s"
                                " AND target_type='lord' AND target_ref=%s", (CHART_ID, "marriage", "7L")),
            lambda m: m["r4"][0] == 0 and m["r4"][1] >= 1),
        # ASTRA v1.3 amendment 1: a birth_anchor row (its ontology row exists, so the FK admits
        # it) is outside the writer's universe — flagged, never expected
        "birth_anchor_row_injected": (
            lambda: cur.execute(
                "INSERT INTO gochara_resonance_map (chart_id, event_class, target_type, target_ref,"
                " weight, classical_citation, uncited_extension, target_resolution_state)"
                " VALUES (%s, 'birth_anchor', 'bhava', '1', 1.0,"
                " 'n/a — defines the natal epoch, not a classically-timed event', FALSE, 'resolved')",
                (CHART_ID,)),
            lambda m: m["value_violations"] >= 1),
    }
    # controls whose mutation necessarily changes a count (a deletion / an insertion): the
    # validity criterion is that the mutation was APPLIED (shape changed), not preserved
    count_changing = {"lord_token_missing", "birth_anchor_row_injected"}
    clean = measure()
    shape0 = _map_shape(cur)
    results: dict = {"clean": clean}
    for name, (mutate, detected_by) in controls.items():
        cur.execute("SAVEPOINT detector_control")
        try:
            mutate()
            shape1 = _map_shape(cur)
            m = measure()
        finally:
            cur.execute("ROLLBACK TO SAVEPOINT detector_control")
            cur.execute("RELEASE SAVEPOINT detector_control")
        results[name] = {
            "count_preservation_expected": name not in count_changing,
            "counts_preserved": shape1[0] == shape0[0],
            "global_id_sets_preserved": shape1[1] == shape0[1],
            "mutation_applied": shape1 != shape0 or m != clean,
            "measured": m,
            "detected": bool(detected_by(m)),
        }
    results["restored_after_controls"] = _map_shape(cur) == shape0
    return results


def _run_writer(conn):
    from pipeline.orchestrator.writers import ContextSpec  # noqa: E402
    from services.ka_gochara_resonance.writer import KaGocharaResonanceWriter
    ctx = ContextSpec.__new__(ContextSpec)
    ctx.db_conn = conn
    ctx.config = {"chart_id": CHART_ID}
    ctx.dry_run = False
    result = KaGocharaResonanceWriter().run(ctx)
    conn.commit()  # the harness owns commit; the writer never does
    return result


def _run_sql_script(dsn: str, script: str) -> str | None:
    """Execute a BEGIN…COMMIT script on its own autocommit connection (the
    runbook's psql shape). Returns None on success, the error text on
    refusal/failure (the aborted transaction is rolled back)."""
    import psycopg
    with psycopg.connect(dsn, autocommit=True) as c:
        try:
            c.execute(script)
            return None
        except psycopg.Error as exc:
            try:
                c.execute("ROLLBACK")
            except psycopg.Error:
                pass
            return str(exc)


class _StopBeforeDestructive(Exception):
    """Raised when the snapshot certificate fails: the run stops before the
    writer, reports the failure and exits 1."""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maintenance-dsn", required=True,
                        help="loopback DSN of a maintenance database (e.g. .../postgres); "
                             "the rehearsal CREATES its own database from here")
    parser.add_argument("--expect-cluster-id", required=True,
                        help="pg_control_system() system_identifier of the DISPOSABLE "
                             "cluster; asserted on the maintenance connection before "
                             "CREATE DATABASE")
    parser.add_argument("--database-prefix", default="rehearsal_a54")
    parser.add_argument("--keep-database", action="store_true")
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    import psycopg

    dsn, name = establish_disposable_database(
        args.maintenance_dsn, args.database_prefix, args.expect_cluster_id)
    report: dict = {"database": name, "expect_cluster_id": args.expect_cluster_id,
                    "acceptance": None}
    try:
        conn = psycopg.connect(dsn, autocommit=False)
        cur = conn.cursor()
        report["identity"] = assert_disposable_identity(conn, name)

        # 1. schema from the checked-in migrations (ASTRA v1.3 amendment 1)
        report["schema"] = apply_rehearsal_schema(cur)
        # 2. seed (the ontology is the migrations' own seed)
        fixture = _seed(cur)
        conn.commit()

        before = _counts(cur, "before_rebuild")
        other_before = _digest(cur, "gochara_resonance_map", OTHER_CHART_ID)
        other_before_full = _full_digest(cur, "gochara_resonance_map", OTHER_CHART_ID)

        # 3. snapshot (the runbook's §1 statements, verbatim from the module):
        #    the FULL-ROW certificate of the snapshot must equal the live
        #    preimage BEFORE any destructive step — otherwise stop here.
        snap = B.snapshot_table_name(CHART_ID, B.new_stamp_utc())
        cur.execute(B.create_snapshot_sql(snap, CHART_ID))
        conn.commit()
        live_pre_full = _full_digest(cur, "gochara_resonance_map", CHART_ID)
        snap_full = _full_digest(cur, snap, CHART_ID)
        live_pre = _digest(cur, "gochara_resonance_map", CHART_ID)
        snapshot_block = {"table": snap,
                          "recorded_count": snap_full[0],
                          "recorded_full_row_digest": snap_full[1],
                          "recorded_content_digest": _digest(cur, snap, CHART_ID)[1],
                          "full_row_matches_live_preimage": snap_full == live_pre_full,
                          "content_matches_live_preimage": _digest(cur, snap, CHART_ID) == live_pre}
        report["snapshot"] = snapshot_block
        if not snapshot_block["full_row_matches_live_preimage"] or snap_full[0] <= 0:
            report["verification"] = {"snapshot": snapshot_block}
            report["acceptance"] = {"passed": False, "failures": [
                "snapshot: full-row certificate does not equal the live preimage (or "
                "the snapshot is empty) — destructive phase NOT run"]}
            conn.close()
            raise _StopBeforeDestructive()

        # 4. the REAL writer, then the postconditions
        result = _run_writer(conn)
        after = _counts(cur, "after_rebuild")
        post = _digest(cur, "gochara_resonance_map", CHART_ID)
        ver: dict = {"before": before, "after": after, "snapshot": snapshot_block}
        ver["sensitive_keyed_to_positive_facts"] = cur.execute(
            "SELECT COUNT(*) FROM gochara_resonance_map m JOIN chart_facts f"
            " ON f.fact_id::text = m.target_ref AND f.chart_id = m.chart_id"
            " WHERE m.chart_id=%s AND m.target_type='sensitive_degree'"
            " AND f.fact_category='sensitive_degree_check'"
            " AND f.fact_value_text = ANY(%s)", (CHART_ID, POSITIVE_VALUES)).fetchone()[0]
        ver["dangling_or_null_refs"] = cur.execute(B.dangling_fact_refs_sql(CHART_ID)).fetchone()[0]
        ver["rows_missing_or_bad_resolution_state"] = cur.execute(
            "SELECT COUNT(*) FROM gochara_resonance_map WHERE chart_id=%s"
            " AND (target_resolution_state IS NULL"
            "      OR target_resolution_state NOT IN ('resolved','unavailable','unqualified'))",
            (CHART_ID,)).fetchone()[0]
        ver["resolution_state_counts"] = dict(cur.execute(
            "SELECT target_resolution_state, COUNT(*) FROM gochara_resonance_map"
            " WHERE chart_id=%s GROUP BY 1 ORDER BY 1", (CHART_ID,)).fetchall())
        ver["arudha_rows"] = after["by_type"].get("arudha", 0)
        ver["arudha_all_keyed_to_sign_facts"] = cur.execute(
            "SELECT COUNT(*) = (SELECT COUNT(*) FROM gochara_resonance_map"
            "  WHERE chart_id=%s AND target_type='arudha')"
            " FROM gochara_resonance_map m JOIN chart_facts f"
            " ON f.fact_id::text = m.target_ref AND f.chart_id = m.chart_id"
            " WHERE m.chart_id=%s AND m.target_type='arudha' AND f.fact_key='sign'",
            (CHART_ID, CHART_ID)).fetchone()[0]
        ver["arudha_invalid_sign_unavailable"] = cur.execute(
            "SELECT COUNT(*) FROM gochara_resonance_map m JOIN chart_facts f"
            " ON f.fact_id::text = m.target_ref AND f.chart_id = m.chart_id"
            " WHERE m.chart_id=%s AND m.target_type='arudha'"
            " AND f.fact_subject='ARUDHA_A12' AND m.target_resolution_state='unavailable'",
            (CHART_ID,)).fetchone()[0]
        ver["yoga_rows"] = after["by_type"].get("yoga_constituent", 0)
        ver["yoga_refs_not_live_fired"] = cur.execute(
            "SELECT COUNT(*) FROM gochara_resonance_map m"
            " WHERE m.chart_id=%s AND m.target_type='yoga_constituent'"
            " AND NOT EXISTS (SELECT 1 FROM ga_yoga_firings y"
            "   WHERE y.chart_id=m.chart_id AND y.ayanamsha_id=%s"
            "   AND y.yoga_canonical_id=m.target_ref AND y.fired)",
            (CHART_ID, AYANAMSHA)).fetchone()[0]
        ver["lord_rows"] = after["by_type"].get("lord", 0)
        ver["lord_states"] = dict(cur.execute(
            "SELECT target_resolution_state, COUNT(*) FROM gochara_resonance_map"
            " WHERE chart_id=%s AND target_type='lord' GROUP BY 1 ORDER BY 1",
            (CHART_ID,)).fetchall())
        ver["afflicted_qualifier_rows"] = cur.execute(
            "SELECT COUNT(*) FROM gochara_resonance_map WHERE chart_id=%s"
            " AND target_type='lord' AND target_qualifier='afflicted'",
            (CHART_ID,)).fetchone()[0]
        ver["expected_afflicted_rows"] = expected_afflicted_lord_rows()
        # exact IDENTITY sets (ASTRA v1.1 P1-7): totals can be preserved by a
        # transferred qualifier or a substituted input — the sets cannot.
        exp_lords, exp_afflicted = expected_lord_identities()
        act_lords = {(c, r) for c, r in cur.execute(
            "SELECT event_class, target_ref FROM gochara_resonance_map"
            " WHERE chart_id=%s AND target_type='lord'", (CHART_ID,)).fetchall()}
        act_afflicted = {(c, r) for c, r in cur.execute(
            "SELECT event_class, target_ref FROM gochara_resonance_map"
            " WHERE chart_id=%s AND target_type='lord' AND target_qualifier='afflicted'",
            (CHART_ID,)).fetchall()}
        # CLASS-ASSOCIATED identities and FULL retained values (ASTRA v1.2
        # P1-3): every row of the exactly-determined types as a tuple.
        exp_tuples = expected_row_tuples(fixture, fixture["db_signature_models"])
        act_tuples = {
            (c, ty, r, float(wt), st, q, bool(u), ci) for c, ty, r, wt, st, q, u, ci in cur.execute(
                "SELECT event_class, target_type, target_ref, weight, target_resolution_state,"
                " target_qualifier, uncited_extension, classical_citation"
                " FROM gochara_resonance_map WHERE chart_id=%s AND target_type = ANY(%s)",
                (CHART_ID, list(EXACT_TYPES))).fetchall()}
        def _pairs(ty):
            return {f"{tp[0]}:{tp[2]}" for tp in exp_tuples if tp[1] == ty}, \
                   {f"{tp[0]}:{tp[2]}" for tp in act_tuples if tp[1] == ty}
        exp_sens, act_sens = _pairs("sensitive_degree")
        exp_aru, act_aru = _pairs("arudha")
        exp_yog, act_yog = _pairs("yoga_constituent")
        ver["identities"] = {
            "lord_rows": {"expected": sorted(f"{c}:{r}" for c, r in exp_lords),
                          "actual": sorted(f"{c}:{r}" for c, r in act_lords)},
            "afflicted_rows": {"expected": sorted(f"{c}:{r}" for c, r in exp_afflicted),
                               "actual": sorted(f"{c}:{r}" for c, r in act_afflicted)},
            "sensitive_rows": {"expected": sorted(exp_sens), "actual": sorted(act_sens)},
            "arudha_rows": {"expected": sorted(exp_aru), "actual": sorted(act_aru)},
            "yoga_rows": {"expected": sorted(exp_yog), "actual": sorted(act_yog)},
            "exact_row_tuples": {"expected": sorted("|".join(map(str, tp)) for tp in exp_tuples),
                                 "actual": sorted("|".join(map(str, tp)) for tp in act_tuples)},
        }
        act_sensitive = {tp[2] for tp in act_tuples if tp[1] == "sensitive_degree"}
        ver["negative_fact_ids_referenced"] = len(act_sensitive & set(fixture["negative_fact_ids"]))
        # the class universe: the writer's TARGET_EVENT_CLASSES, never every ontology row
        map_classes = {c for (c,) in cur.execute(
            "SELECT DISTINCT event_class FROM gochara_resonance_map WHERE chart_id=%s",
            (CHART_ID,)).fetchall()}
        mirror = {c: (sorted(h), list(l), list(k)) for c, (h, l, k) in SIGNATURE_MODELS.items()}
        db_models = {c: (sorted(h), list(l), list(k)) for c, (h, l, k) in fixture["db_signature_models"].items()}
        ver["ontology"] = {
            "eligible_classes": sorted(B.ELIGIBLE_EVENT_CLASSES),
            "non_eligible_classes_present_in_ontology": sorted(fixture["non_eligible_classes_present"]),
            "birth_anchor_present_in_ontology": "birth_anchor" in fixture["non_eligible_classes_present"],
            "birth_anchor_rows_in_map": sum(1 for c in map_classes if c == "birth_anchor"),
            "map_classes_equal_eligible": map_classes == set(B.ELIGIBLE_EVENT_CLASSES),
            "mirror_matches_migration_seed": mirror == db_models,
            "mirror_diff": sorted(c for c in set(mirror) | set(db_models) if mirror.get(c) != db_models.get(c)),
            "citations_type": cur.execute(
                "SELECT data_type FROM information_schema.columns WHERE table_name='brahma_event_ontology'"
                " AND column_name='citations'").fetchone()[0],
            "chart_facts_fact_id_type": cur.execute(
                "SELECT data_type FROM information_schema.columns WHERE table_name='chart_facts'"
                " AND column_name='fact_id'").fetchone()[0],
        }
        _viol = cur.execute(B.value_invariants_sql(CHART_ID)).fetchall()
        ver["value_invariant_violations"] = len(_viol)
        ver["value_invariant_violation_rows"] = [list(map(str, r)) for r in _viol[:25]]
        for check_name, fn in (("r1_identity_sql", B.r1_identity_sql), ("r2_identity_sql", B.r2_identity_sql),
                               ("r3_identity_sql", B.r3_identity_sql),
                               ("r4_identity_sql", B.r4_lord_identity_sql)):
            fwd_sql, rev_sql = fn(CHART_ID)
            ver[check_name] = {"actual_not_expected": len(cur.execute(fwd_sql).fetchall()),
                         "expected_not_actual": len(cur.execute(rev_sql).fetchall())}
        fwd, rev = B.r5_qualifier_identity_sql(CHART_ID)
        ver["r5_identity_sql"] = {
            "qualified_not_in_ontology": len(cur.execute(fwd).fetchall()),
            "ontology_not_qualified": len(cur.execute(rev).fetchall()),
        }
        ver["writer_rows_inserted"] = result.rows_inserted
        ver["writer_notes"] = json.loads(result.notes)
        ver["post_rebuild_digest"] = {"count": post[0], "digest": post[1]}
        ver["negative_dropped_zero_rows_semantics"] = (
            "per-class exclusion counter (each negative fact is excluded once per "
            "event class that would have cited it), NOT the map-level count; the "
            "map-level R-1 assertion is after.sensitive_negative == 0")

        # 5. idempotent rerun
        _run_writer(conn)
        rerun = _digest(cur, "gochara_resonance_map", CHART_ID)
        ver["rerun_digest_equal"] = rerun == post

        # 5b. detector positive controls (rolled back; the map is unchanged after)
        ver["detector_controls"] = _detector_controls(cur)
        ver["map_unchanged_after_detector_controls"] = (
            _digest(cur, "gochara_resonance_map", CHART_ID) == rerun)

        # 6. rollback rehearsal
        conn.commit()
        rb: dict = {"snapshot_table": snap}
        # (a) a WRONG full-row certificate must be refused before any DELETE:
        #     the FULL certificate recorded BEFORE the probe must equal the one
        #     recorded AFTER it (ids and computed_at included — a delete+
        #     reinsert with the same content would change it)
        pre_refusal_full = _full_digest(cur, "gochara_resonance_map", CHART_ID)
        refusal = _run_sql_script(dsn, B.rollback_sql(snap, CHART_ID, snap_full[0], "0" * 32))
        post_refusal_full = _full_digest(cur, "gochara_resonance_map", CHART_ID)
        rb["refused_on_stale_snapshot"] = refusal is not None and "ROLLBACK REFUSED" in refusal
        rb["refusal_message"] = refusal
        rb["pre_refusal_full_certificate"] = pre_refusal_full
        rb["post_refusal_full_certificate"] = post_refusal_full
        rb["partition_untouched_after_refusal"] = (pre_refusal_full == post_refusal_full
                                                  and _digest(cur, "gochara_resonance_map", CHART_ID) == rerun)
        # (b) the recorded full-row certificate restores the EXACT preimage
        err = _run_sql_script(dsn, B.rollback_sql(snap, CHART_ID, snap_full[0], snap_full[1]))
        rb["rollback_error"] = err
        restored_full = _full_digest(cur, "gochara_resonance_map", CHART_ID)
        rb["restored_full_row_digest_equal"] = err is None and restored_full == live_pre_full
        rb["restored_content_digest_equal"] = _digest(cur, "gochara_resonance_map", CHART_ID) == live_pre
        rb["other_chart_untouched"] = (
            _full_digest(cur, "gochara_resonance_map", OTHER_CHART_ID) == other_before_full
            and _digest(cur, "gochara_resonance_map", OTHER_CHART_ID) == other_before)
        _run_writer(conn)
        rb["rebuild_after_rollback_digest_equal"] = _digest(cur, "gochara_resonance_map", CHART_ID) == post
        ver["rollback"] = rb

        failures = verify_acceptance(ver)
        report["verification"] = ver
        report["acceptance"] = {"passed": not failures, "failures": failures}
        conn.close()
    except _StopBeforeDestructive:
        pass
    finally:
        if args.keep_database:
            report["database_kept"] = True
        else:
            drop_disposable_database(args.maintenance_dsn, name)
            report["database_dropped"] = True

    text = json.dumps(report, indent=2, sort_keys=True, default=str)
    print(text)
    if args.json_out:
        Path(args.json_out).write_text(text)
    if report["acceptance"] is None or not report["acceptance"]["passed"]:
        print("REHEARSAL FAILED: " + "; ".join((report.get("acceptance") or {}).get("failures", ["no acceptance block"])),
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
