"""Backup / verification / rollback SQL for the R-1..R-6 resonance-map rebuild
(A5.4 resonance_rebuild_R1_R6; ASTRA_REVIEW_A5_4 P1-7).

ONE source for the statements the production runbook
(resonance_rebuild_R1_R6_runbook.md) quotes and the disposable rehearsal
(resonance_rebuild_disposable_rehearsal.py) executes — a drift guard in
tests/l3/test_resonance_rebuild_rehearsal.py asserts the runbook carries
them verbatim. Properties:

  * the snapshot table is UNIQUELY named per (chart, UTC stamp) and created
    with plain CREATE TABLE — never IF NOT EXISTS, so a stale table from an
    earlier attempt is an error, not a silently reused rollback anchor;
  * TWO digests, kept apart (ASTRA_REVIEW_A5_4 v1.1 P1-6):
      - the PREIMAGE CERTIFICATE (`full_row_digest_sql`): md5 over every
        column of every row — id and computed_at included — serialised as
        typed JSON (`row_to_json(t)::text`, where SQL NULL renders as JSON
        null and can never collide with a string), ordered by id. Equality
        between the snapshot and the live partition, and between the
        restored partition and the recorded value, certifies the COMPLETE
        preimage;
      - the CONTENT digest (`partition_digest_sql`): the same typed JSON
        serialisation over the content columns only (id / computed_at
        excluded), ordered canonically — the ID-independent comparison for
        a rerun of the rebuild, never used for the restore certificate;
  * the rollback is a single transaction whose DO block REFUSES to delete
    when the snapshot is absent, EMPTY, carries another chart, or does not
    match the recorded count/full-row digest; the restore is verified
    afterwards by the same full-row digest. The generator itself refuses a
    zero recorded count.
"""
from __future__ import annotations

import re
import sys
import uuid
from pathlib import Path

# The writer's EXACT eligible class universe (ASTRA v1.3 amendment 1): the
# resonance writer enumerates TARGET_EVENT_CLASSES — 26 classes, birth_anchor
# excluded structurally (N6) although migration 456 keeps its ontology row.
# Every identity below is scoped to this set, never to "every ontology row".
_SIDECAR = Path(__file__).resolve().parents[2]
if str(_SIDECAR) not in sys.path:
    sys.path.insert(0, str(_SIDECAR))
from services.ka_gochara_resonance.writer import (  # noqa: E402
    TARGET_EVENT_CLASSES, _MECHANISM_WEIGHTS)
from services.gochara_grammar.derived_points import (  # noqa: E402
    M6_EVENT_CLASSES, MANDI_DISTANCE_AGENT, MANDI_DISTANCE_CITATION, MANDI_DISTANCE_REF,
    YAMAKANTAKA_FORMULAS)

ELIGIBLE_EVENT_CLASSES: tuple[str, ...] = tuple(TARGET_EVENT_CLASSES)

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_TABLE_RE = re.compile(r"^gochara_resonance_map_snap_[0-9a-f]{8}_[0-9]{14}$")
_MD5_RE = re.compile(r"^[0-9a-f]{32}$|^empty$")

CONTENT_COLUMNS = (
    "event_class", "target_type", "target_ref", "weight", "classical_citation",
    "uncited_extension", "source_rule_id", "target_resolution_state",
    "target_qualifier",
)

# Typed, unambiguous serialisations: JSON null is distinct from any string
# (the earlier concat_ws('|', …, coalesce(x, '<null>')) collided SQL NULL with
# the literal '<null>'); numerics/booleans render typed.
_CONTENT_JSON = (
    "json_build_object('event_class', event_class, 'target_type', target_type, "
    "'target_ref', target_ref, 'weight', weight, 'classical_citation', "
    "classical_citation, 'uncited_extension', uncited_extension, "
    "'source_rule_id', source_rule_id, 'target_resolution_state', "
    "target_resolution_state, 'target_qualifier', target_qualifier)::text"
)
_ROW_TEXT = _CONTENT_JSON  # content-digest row text (rerun comparison)
_FULL_ROW_TEXT = "row_to_json(t)::text"  # every column, typed (preimage certificate)


def snapshot_table_name(chart_id: str, stamp_utc: str) -> str:
    """gochara_resonance_map_snap_<chart8>_<YYYYMMDDHHMMSS> — unique per run."""
    cid = _check_uuid(chart_id)
    if not re.fullmatch(r"[0-9]{14}", stamp_utc):
        raise ValueError("stamp_utc must be YYYYMMDDHHMMSS")
    return f"gochara_resonance_map_snap_{cid[:8]}_{stamp_utc}"


def _check_uuid(chart_id: str) -> str:
    cid = str(chart_id).lower()
    if not _UUID_RE.match(cid):
        raise ValueError(f"not a chart uuid: {chart_id!r}")
    return cid


def _check_table(table: str) -> str:
    if not _TABLE_RE.match(table):
        raise ValueError(f"not a snapshot table name: {table!r}")
    return table


def create_snapshot_sql(table: str, chart_id: str) -> str:
    """[NATIVE ACTION — production write] Plain CREATE TABLE: fails loudly if
    the name exists (no silent reuse of a stale backup)."""
    return (f"CREATE TABLE {_check_table(table)} AS\n"
            f"SELECT * FROM gochara_resonance_map\n"
            f" WHERE chart_id = '{_check_uuid(chart_id)}';")


def partition_digest_sql(table: str, chart_id: str) -> str:
    """(row_count, content_digest) of one chart's partition in `table` —
    the ID-INDEPENDENT rerun comparison: typed JSON over the content
    columns (id / computed_at excluded), canonically ordered. NOT the
    restore certificate (see full_row_digest_sql)."""
    if table != "gochara_resonance_map":
        _check_table(table)
    return (f"SELECT COUNT(*) AS row_count,\n"
            f"       COALESCE(md5(string_agg({_ROW_TEXT}, E'\\n' ORDER BY {_ROW_TEXT})), 'empty') AS content_digest\n"
            f"  FROM {table}\n"
            f" WHERE chart_id = '{_check_uuid(chart_id)}';")


def full_row_digest_sql(table: str, chart_id: str) -> str:
    """(row_count, full_row_digest) of one chart's partition in `table` —
    the PREIMAGE CERTIFICATE: every column of every row (id and computed_at
    included) as typed JSON, ordered by id. Snapshot == live at the moment
    of taking, and restored == recorded after a rollback, certify the
    complete preimage."""
    if table != "gochara_resonance_map":
        _check_table(table)
    return (f"SELECT COUNT(*) AS row_count,\n"
            f"       COALESCE(md5(string_agg({_FULL_ROW_TEXT}, E'\\n' ORDER BY t.id)), 'empty') AS full_row_digest\n"
            f"  FROM {table} t\n"
            f" WHERE t.chart_id = '{_check_uuid(chart_id)}';")


def rollback_sql(table: str, chart_id: str, recorded_count: int,
                 recorded_full_row_digest: str) -> str:
    """One transaction: refuse-unless-verified (absent / empty / foreign
    chart / count or FULL-ROW digest mismatch), then DELETE + INSERT the
    exact preimage (all columns, ids and computed_at included), then verify
    the restore by the same full-row certificate. A zero recorded count is
    refused here, before any SQL exists."""
    tbl = _check_table(table)
    cid = _check_uuid(chart_id)
    n = int(recorded_count)
    if n <= 0:
        raise ValueError("rollback refused: the recorded snapshot count must be "
                         "positive — an empty snapshot is never a rollback anchor")
    if not re.fullmatch(r"[0-9a-f]{32}", recorded_full_row_digest):
        raise ValueError("recorded_full_row_digest must be an md5 hex (a nonempty "
                         "partition never digests to 'empty')")
    return f"""BEGIN;
DO $rollback$
DECLARE
  snap_count BIGINT;
  snap_digest TEXT;
  foreign_rows BIGINT;
BEGIN
  IF to_regclass('{tbl}') IS NULL THEN
    RAISE EXCEPTION 'ROLLBACK REFUSED: snapshot table {tbl} is absent';
  END IF;
  SELECT COUNT(*) INTO foreign_rows FROM {tbl} WHERE chart_id <> '{cid}';
  IF foreign_rows <> 0 THEN
    RAISE EXCEPTION 'ROLLBACK REFUSED: snapshot {tbl} carries % rows of another chart', foreign_rows;
  END IF;
  SELECT COUNT(*),
         COALESCE(md5(string_agg({_FULL_ROW_TEXT}, E'\\n' ORDER BY t.id)), 'empty')
    INTO snap_count, snap_digest
    FROM {tbl} t WHERE t.chart_id = '{cid}';
  IF snap_count = 0 THEN
    RAISE EXCEPTION 'ROLLBACK REFUSED: snapshot {tbl} is EMPTY — never a rollback anchor';
  END IF;
  IF snap_count <> {n} OR snap_digest <> '{recorded_full_row_digest}' THEN
    RAISE EXCEPTION 'ROLLBACK REFUSED: snapshot {tbl} is stale or incomplete (count % full-row digest % vs recorded {n} {recorded_full_row_digest})', snap_count, snap_digest;
  END IF;
  DELETE FROM gochara_resonance_map WHERE chart_id = '{cid}';
  INSERT INTO gochara_resonance_map SELECT * FROM {tbl} WHERE chart_id = '{cid}';
  SELECT COUNT(*),
         COALESCE(md5(string_agg({_FULL_ROW_TEXT}, E'\\n' ORDER BY t.id)), 'empty')
    INTO snap_count, snap_digest
    FROM gochara_resonance_map t WHERE t.chart_id = '{cid}';
  IF snap_count <> {n} OR snap_digest <> '{recorded_full_row_digest}' THEN
    RAISE EXCEPTION 'ROLLBACK FAILED VERIFICATION: restored count % full-row digest % vs recorded {n} {recorded_full_row_digest}', snap_count, snap_digest;
  END IF;
END
$rollback$;
COMMIT;"""


NEGATIVE_VALUES = ("not_fired", "not_gandanta", "not_pushkara", "none")
POSITIVE_VALUES = ("fired", "gandanta", "papa_kartari", "shubha_kartari", "pushkara")


def negative_sensitive_targets_sql(chart_id: str) -> str:
    """R-1: sensitive_degree targets keyed to a negative-result (or
    out-of-vocabulary) check — MUST be 0 after the rebuild."""
    cid = _check_uuid(chart_id)
    neg = ", ".join(f"'{v}'" for v in NEGATIVE_VALUES)
    pos = ", ".join(f"'{v}'" for v in POSITIVE_VALUES)
    return (f"SELECT COUNT(*) FROM gochara_resonance_map m\n"
            f"  JOIN chart_facts f ON f.fact_id::text = m.target_ref\n"
            f" WHERE m.chart_id = '{cid}' AND m.target_type = 'sensitive_degree'\n"
            f"   AND f.fact_category = 'sensitive_degree_check'\n"
            f"   AND (f.fact_value_text IN ({neg})\n"
            f"        OR f.fact_value_text IS NULL\n"
            f"        OR f.fact_value_text NOT IN ({pos}));")


# Target types whose target_ref IS a chart_facts.fact_id (of the same chart).
FACT_BACKED_TARGET_TYPES: tuple[str, ...] = ("sensitive_degree", "arudha")


def dangling_fact_refs_sql(chart_id: str) -> str:
    """NULL / blank refs, plus fact-backed refs (sensitive_degree, arudha)
    that resolve to no chart_facts row of THIS chart — MUST be 0.

    chart_facts.fact_id is TEXT (migration 204) and the producers mint
    16-hex SEMANTIC ids (ga_writers/*._fact_id — sha256 of
    category|subject|key|chart|ayanāṃśa, never a UUID). The previous
    predicate counted every non-UUID fact-backed ref as dangling, i.e. it
    rejected every id a producer actually mints (ASTRA v1.4 amendment 1).
    Resolution is a chart-scoped NOT EXISTS on the text identity itself
    (NULL-safe; SQL NOT IN never rejects nulls) — an existing id of this
    chart passes, a missing id or the SAME id minted for another chart
    fails."""
    cid = _check_uuid(chart_id)
    types = ", ".join(f"'{t}'" for t in FACT_BACKED_TARGET_TYPES)
    return (f"SELECT COUNT(*) FROM gochara_resonance_map m\n"
            f" WHERE m.chart_id = '{cid}'\n"
            f"   AND (m.target_ref IS NULL OR btrim(m.target_ref) = ''\n"
            f"        OR (m.target_type IN ({types})\n"
            f"            AND NOT EXISTS (SELECT 1 FROM chart_facts f\n"
            f"                             WHERE f.fact_id = m.target_ref\n"
            f"                               AND f.chart_id = m.chart_id)));")


def new_stamp_utc() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def r5_qualifier_identity_sql(chart_id: str) -> tuple[str, str]:
    """R-5 as an IDENTITY comparison (ASTRA v1.1 P1-7): the exact set of
    (event_class, lord token) rows carrying target_qualifier='afflicted'
    must EQUAL the set of '<n>L' tokens inside '…afflicted…' lord entries of
    brahma_event_ontology.signature_model->'lords' — the writer's own
    tokenisation (a `\\d+L` token per entry; the qualifier rides the entry). Two
    EXCEPT queries; BOTH must return zero rows (a missing, an extra or a
    transferred qualifier surfaces in one direction). The raw-label
    comparison the previous runbook printed could never match its own
    fixture."""
    cid = _check_uuid(chart_id)
    rows = (f"SELECT event_class, target_ref FROM gochara_resonance_map\n"
            f" WHERE chart_id = '{cid}' AND target_type = 'lord' AND target_qualifier = 'afflicted'")
    expected = ("SELECT o.event_class_id AS event_class, m[1] AS target_ref\n"
                "  FROM brahma_event_ontology o,\n"
                "       jsonb_array_elements_text(o.signature_model->'lords') AS l(value),\n"
                "       regexp_matches(l.value, '(\\d+L)', 'g') AS m\n"
                f" WHERE o.event_class_id = ANY({eligible_classes_array()})\n"
                "   AND l.value ILIKE '%afflicted%'")
    return (f"-- rows with the qualifier that the ontology does not name (MUST be 0 rows):\n"
            f"{rows}\nEXCEPT\n{expected};",
            f"-- ontology-named afflicted lords missing the qualifier (MUST be 0 rows):\n"
            f"{expected}\nEXCEPT\n{rows};")


# The writer's own eligibility contract (services/ka_gochara_resonance/writer.py):
#   sensitive_degree: chart_facts sensitive_degree_check rows of the CANONICAL
#     ayanāṃśa whose fact_subject is a class kāraka's subject code and whose
#     (fact_key, value) is a positive pair; weight 0.5, uncited, no citation;
#   arudha: arudha_pada fact_key='sign' rows for the class's houses (ARUDHA_A{h});
#     weight 0.6; state resolved iff the sign value is one of the 12 signs;
#   yoga_constituent: live fired ga_yoga_firings of the canonical ayanāṃśa whose
#     constituent_houses ∩ class houses or constituent_planets ∩ class kārakas
#     (lower-case) is non-empty; weight 0.7; qualifier bhanga_active.
CANONICAL_AYANAMSHA = "lahiri_chitrapaksha"
# _KARAKA_FACT_SUBJECT in the writer: EXACT title-case kāraka names → subject
KARAKA_SUBJECT_VALUES = ("(VALUES ('Sun','SUN'),('Moon','MOON'),('Mars','MAR'),('Mercury','MER'),"
                         "('Jupiter','JUP'),('Venus','VEN'),('Saturn','SAT'),('Rahu','RAH_MEAN'),"
                         "('Ketu','KET_MEAN')) AS ks(karaka, subject)")


def eligible_classes_array() -> str:
    """The writer's TARGET_EVENT_CLASSES as a SQL text[] literal."""
    return "ARRAY[" + ", ".join(f"'{c}'" for c in ELIGIBLE_EVENT_CLASSES) + "]::text[]"
POSITIVE_PAIRS = ("(VALUES ('mrityu_bhaga','fired'),('gandanta','gandanta'),('kartari','papa_kartari'),"
                  "('kartari','shubha_kartari'),('pushkara','pushkara')) AS pp(fact_key, value)")
EXPECTED_WEIGHTS = {"bhava": 1.0, "lord": 1.0, "karaka": 1.0, "sensitive_degree": 0.5,
                    "arudha": 0.6, "bhava_arudha": 0.6, "yoga_constituent": 0.7,
                    "dasha_lord_portfolio": 0.8,
                    # M-6 derived rows (writer._build_m6_derived_rows): 0.5 each
                    "gulika_mandi_distance": 0.5, "yamakantaka_difference": 0.5}
# mechanism_node: the weight is the CITED bg_transit_rules row's rule_type mapped
# through the writer's own contract (writer._MECHANISM_WEIGHTS — favourable 1.0,
# unfavourable -1.0, vedha 0.3, double_transit 0.75); a rule_type outside the
# contract would be the writer's 0.5 default — not accepted here (ASTRA v1.4 am. 2).
MECHANISM_WEIGHTS: dict[str, float] = dict(_MECHANISM_WEIGHTS)
# EVERY target type the writer emits (its _base_row calls) is checked by name —
# a type outside this tuple is a 'type:unknown' violation, never a silent
# fall-through (the previous CASE degraded to `m.weight <> m.weight` for a type
# absent from EXPECTED_WEIGHTS — mechanism_node — so a sign flip passed).
CHECKED_TARGET_TYPES: tuple[str, ...] = tuple(sorted(list(EXPECTED_WEIGHTS) + ["mechanism_node"]))
M6_CONSTANT_ROWS: tuple[tuple[str, str, str, str], ...] = tuple(
    [("gulika_mandi_distance", MANDI_DISTANCE_REF, MANDI_DISTANCE_CITATION, f"agent:{MANDI_DISTANCE_AGENT}")]
    + [("yamakantaka_difference", f["ref"], f["citation"], f"agent:{f['agent']}") for f in YAMAKANTAKA_FORMULAS])


def _sql_str(v: str) -> str:
    return "'" + str(v).replace("'", "''") + "'"


def mechanism_identity_sql(chart_id: str) -> tuple[str, str]:
    """mechanism_node rows as an identity, both directions: the exact set of
    (event_class, source_rule_id) rows must EQUAL the bg_transit_rules rows
    eligible for each class as the writer fetches them (lower(graha) ∈ the
    class's kārakas AND primary_house ∈ its houses). A row's target_ref and
    weight are checked against ITS rule by value_invariants_sql."""
    cid = _check_uuid(chart_id)
    cte = f"WITH {_class_houses_cte(cid)}\n"
    expected = ("SELECT DISTINCT o.event_class_id AS event_class, r.id AS source_rule_id\n"
                "  FROM eligible o\n"
                "  JOIN class_karakas ck ON ck.event_class = o.event_class_id\n"
                "  JOIN class_houses ch ON ch.event_class = o.event_class_id\n"
                "  JOIN bg_transit_rules r ON lower(btrim(r.graha)) = ck.karaka_lower AND r.primary_house = ch.house")
    actual = (f"SELECT event_class, source_rule_id FROM gochara_resonance_map\n"
              f" WHERE chart_id = '{cid}' AND target_type = 'mechanism_node'")
    return (f"-- mechanism identity: mechanism_node rows not backed by an eligible rule (MUST be 0 rows):\n"
            f"{cte}{actual}\nEXCEPT\n{expected};",
            f"-- mechanism identity: eligible rules MISSING from the map (MUST be 0 rows):\n"
            f"{cte}{expected}\nEXCEPT\n{actual};")


def _class_houses_cte(chart_id: str) -> str:
    """The class universe and its houses / kārakas EXACTLY as the writer
    reads them: only TARGET_EVENT_CLASSES (birth_anchor's retained ontology
    row is never eligible); houses = plain-digit entries only
    (_parse_house_ints drops glosses); kārakas kept verbatim (title-case, as
    _KARAKA_FACT_SUBJECT keys them) with a lower-cased alias (as the yoga
    fetch compares them)."""
    return ("eligible AS (SELECT o.event_class_id, o.signature_model FROM brahma_event_ontology o\n"
            f"  WHERE o.event_class_id = ANY({eligible_classes_array()})),\n"
            "class_houses AS (SELECT o.event_class_id AS event_class, (btrim(h.value))::int AS house\n"
            "  FROM eligible o, jsonb_array_elements_text(o.signature_model->'houses') AS h(value)\n"
            "  WHERE btrim(h.value) ~ '^[0-9]+$'),\n"
            "class_karakas AS (SELECT o.event_class_id AS event_class, k.value AS karaka,\n"
            "                         lower(k.value) AS karaka_lower\n"
            "  FROM eligible o, jsonb_array_elements_text(o.signature_model->'karakas') AS k(value))")


def r1_identity_sql(chart_id: str) -> tuple[str, str]:
    """R-1 as a CLASS-ASSOCIATED identity (ASTRA v1.2 P1-3): the set of
    (event_class, fact_id) sensitive_degree rows must EQUAL the writer's
    eligible set — positive-result checks of the CANONICAL ayanāṃśa whose
    subject is one of the class's kārakas. Both EXCEPT directions must be
    empty (a swap of fact ids between classes, or a foreign-ayanāṃśa fact,
    surfaces in one direction)."""
    cid = _check_uuid(chart_id)
    cte = f"WITH {_class_houses_cte(cid)}\n"
    expected = (f"SELECT ck.event_class, f.fact_id::text AS target_ref\n"
                f"  FROM class_karakas ck\n"
                f"  JOIN {KARAKA_SUBJECT_VALUES} ON ks.karaka = ck.karaka\n"
                f"  JOIN chart_facts f ON f.chart_id = '{cid}' AND f.ayanamsha_id = '{CANONICAL_AYANAMSHA}'\n"
                f"   AND f.fact_category = 'sensitive_degree_check' AND f.fact_subject = ks.subject\n"
                f"  JOIN {POSITIVE_PAIRS} ON pp.fact_key = f.fact_key AND pp.value = f.fact_value_text")
    actual = (f"SELECT event_class, target_ref FROM gochara_resonance_map\n"
              f" WHERE chart_id = '{cid}' AND target_type = 'sensitive_degree'")
    return (f"-- R-1 identity: rows the eligibility contract does not name (MUST be 0 rows):\n"
            f"{cte}{actual}\nEXCEPT\n{expected};",
            f"-- R-1 identity: eligible (class, fact) pairs MISSING from the map (MUST be 0 rows):\n"
            f"{cte}{expected}\nEXCEPT\n{actual};")


def r3_identity_sql(chart_id: str) -> tuple[str, str]:
    """R-3 as a CLASS-ASSOCIATED identity, BOTH directions: the set of
    (event_class, yoga id) rows must EQUAL the live fired firings of the
    canonical ayanāṃśa eligible for the class (constituent_houses ∩ class
    houses, or constituent_planets ∩ class kārakas). The previous runbook
    printed only actual − live, so a MISSING eligible yoga passed."""
    cid = _check_uuid(chart_id)
    cte = f"WITH {_class_houses_cte(cid)}\n"
    expected = (f"SELECT DISTINCT o.event_class_id AS event_class, y.yoga_canonical_id AS target_ref\n"
                f"  FROM eligible o\n"
                f"  JOIN ga_yoga_firings y ON y.chart_id = '{cid}' AND y.ayanamsha_id = '{CANONICAL_AYANAMSHA}' AND y.fired\n"
                f" WHERE EXISTS (SELECT 1 FROM jsonb_array_elements(y.constituent_houses) e\n"
                f"                 JOIN class_houses ch ON ch.event_class = o.event_class_id AND ch.house = (e::text)::int)\n"
                f"    OR EXISTS (SELECT 1 FROM jsonb_array_elements_text(y.constituent_planets) e\n"
                f"                 JOIN class_karakas ck ON ck.event_class = o.event_class_id AND ck.karaka_lower = e)")
    actual = (f"SELECT event_class, target_ref FROM gochara_resonance_map\n"
              f" WHERE chart_id = '{cid}' AND target_type = 'yoga_constituent'")
    return (f"-- R-3 identity: yoga rows not backed by an eligible live firing (MUST be 0 rows):\n"
            f"{cte}{actual}\nEXCEPT\n{expected};",
            f"-- R-3 identity: eligible live firings MISSING from the map (MUST be 0 rows):\n"
            f"{cte}{expected}\nEXCEPT\n{actual};")


def r2_identity_sql(chart_id: str) -> tuple[str, str]:
    """R-2 as a CLASS-ASSOCIATED identity: (event_class, arudha fact_id)
    rows must EQUAL the ARUDHA_A{h} sign facts (canonical ayanāṃśa) of the
    class's houses; both EXCEPT directions empty."""
    cid = _check_uuid(chart_id)
    cte = f"WITH {_class_houses_cte(cid)}\n"
    expected = (f"SELECT ch.event_class, f.fact_id::text AS target_ref\n"
                f"  FROM class_houses ch\n"
                f"  JOIN chart_facts f ON f.chart_id = '{cid}' AND f.ayanamsha_id = '{CANONICAL_AYANAMSHA}'\n"
                f"   AND f.fact_category = 'arudha_pada' AND f.fact_key = 'sign'\n"
                f"   AND f.fact_subject = 'ARUDHA_A' || ch.house::text")
    actual = (f"SELECT event_class, target_ref FROM gochara_resonance_map\n"
              f" WHERE chart_id = '{cid}' AND target_type = 'arudha'")
    return (f"-- R-2 identity: arudha rows the class's houses do not name (MUST be 0 rows):\n"
            f"{cte}{actual}\nEXCEPT\n{expected};",
            f"-- R-2 identity: class-house arudha facts MISSING from the map (MUST be 0 rows):\n"
            f"{cte}{expected}\nEXCEPT\n{actual};")


def r4_lord_identity_sql(chart_id: str) -> tuple[str, str]:
    """R-4 as an ALL-LORD identity (ASTRA v1.3 amendment 3): the exact set of
    (event_class, lord token) rows must EQUAL the '<n>L' tokens of every
    lords entry of the writer's eligible classes — the writer's own
    tokenisation (a `\\d+L` token per entry, deduplicated per class). Both
    EXCEPT directions: a valid-but-wrong token (marriage:7L → marriage:2L,
    weight / state / citation / qualifier preserved) surfaces in BOTH; a
    missing token surfaces in the second. R-5 compares only the afflicted
    subset and R-1/R-2/R-3 never look at lord rows."""
    cid = _check_uuid(chart_id)
    rows = (f"SELECT event_class, target_ref FROM gochara_resonance_map\n"
            f" WHERE chart_id = '{cid}' AND target_type = 'lord'")
    expected = ("SELECT DISTINCT o.event_class_id AS event_class, m[1] AS target_ref\n"
                "  FROM brahma_event_ontology o,\n"
                "       jsonb_array_elements_text(o.signature_model->'lords') AS l(value),\n"
                "       regexp_matches(l.value, '(\\d+L)', 'g') AS m\n"
                f" WHERE o.event_class_id = ANY({eligible_classes_array()})")
    return (f"-- R-4 identity: lord rows the eligible ontology entries do not name (MUST be 0 rows):\n"
            f"{rows}\nEXCEPT\n{expected};",
            f"-- R-4 identity: ontology-named lord tokens MISSING from the map (MUST be 0 rows):\n"
            f"{expected}\nEXCEPT\n{rows};")


def value_invariants_sql(chart_id: str) -> str:
    """Retained VALUES, each checked INDEPENDENTLY against the source it is
    derived from (ASTRA v1.2 P1-3) — a row whose class/type/ref are right
    but whose weight, provenance, resolution state or qualifier is wrong
    is listed here. MUST return 0 rows. Mirrors the writer's own rules
    (services/ka_gochara_resonance/writer.py):
      weight        — the declared per-type weight (EXPECTED_WEIGHTS);
      provenance    — bhava/lord/karaka: uncited_extension=false and
                      classical_citation = the ontology's citations joined
                      by '; ' (NULL when it has none); mechanism_node:
                      uncited=false and citation = the cited bg_transit_rules
                      row's; own-synthesis types: uncited=true, citation NULL;
      state         — lord: the R-4 chain (LAGNA sign → whole-sign house →
                      reference_signs lord → lord's graha_position row:
                      unavailable / unqualified / resolved); bhava: LAGNA
                      present; karaka + dasha_lord_portfolio: the ref's
                      graha_position row present; sensitive_degree: the
                      cited fact's subject graha_position row present;
                      arudha: the cited fact names one of the 12 signs;
                      bhava_arudha: the class-house ARUDHA_A{h} sign fact
                      exists and names a sign; yoga_constituent: resolved;
                      gulika_mandi_distance / yamakantaka_difference: the
                      stored state is accepted within the closed enum (their
                      operand chain is derived_points arithmetic the runbook
                      does NOT re-derive — an explicit limit, not a silent
                      fall-through); their ref / citation / qualifier /
                      provenance and M6 class scope ARE checked;
      mechanism     — weight = the cited rule's rule_type through the
                      writer's contract (MECHANISM_WEIGHTS), target_ref =
                      graha:rule_type:h<house> of that rule, and the rule is
                      eligible for the class (kāraka ∧ house);
      type          — every emitted type is enumerated (CHECKED_TARGET_TYPES);
                      anything else is 'type:unknown', never m.weight <> m.weight;
      qualifier     — lord: 'afflicted' iff an ontology lord entry naming
                      the token says so; yoga_constituent: 'bhanga_active'
                      iff a live fired firing of that id has bhanga_active."""
    cid = _check_uuid(chart_id)
    cases = " ".join(f"WHEN '{t}' THEN {w}" for t, w in EXPECTED_WEIGHTS.items())
    checked = "ARRAY[" + ", ".join(f"'{t}'" for t in CHECKED_TARGET_TYPES) + "]::text[]"
    mech_values = ", ".join(f"('{rt}', {w})" for rt, w in MECHANISM_WEIGHTS.items())
    m6_values = ", ".join(f"({_sql_str(t)}, {_sql_str(r)}, {_sql_str(c)}, {_sql_str(q)})"
                          for t, r, c, q in M6_CONSTANT_ROWS)
    m6_classes = "ARRAY[" + ", ".join(f"'{c}'" for c in M6_EVENT_CLASSES) + "]::text[]"
    return (f"WITH {_class_houses_cte(cid)},\n"
            f"lagna AS (SELECT (fact_value_num)::int AS n FROM chart_facts\n"
            f"  WHERE chart_id = '{cid}' AND ayanamsha_id = '{CANONICAL_AYANAMSHA}'\n"
            f"    AND fact_category = 'graha_sign_attributes' AND fact_subject = 'LAGNA' AND fact_key = 'sign_num'\n"
            f"  ORDER BY fact_value_num LIMIT 1),\n"
            f"present AS (SELECT DISTINCT fact_subject FROM chart_facts\n"
            f"  WHERE chart_id = '{cid}' AND ayanamsha_id = '{CANONICAL_AYANAMSHA}'\n"
            f"    AND fact_category = 'graha_position' AND fact_key = 'longitude_sidereal'),\n"
            f"lords_complete AS (SELECT COUNT(*) = 12 AS ok FROM reference_signs WHERE sign_id BETWEEN 1 AND 12),\n"
            f"graha AS (SELECT * FROM (VALUES ('Sun','SUN'),('Moon','MOON'),('Mars','MAR'),('Mercury','MER'),\n"
            f"  ('Jupiter','JUP'),('Venus','VEN'),('Saturn','SAT'),('Rahu','RAH_MEAN'),('Ketu','KET_MEAN')) AS g(name, subject)),\n"
            # migration 388: citations TEXT[] — the writer joins the list with '; '
            # and stores NULL when the list is NULL or empty
            f"ontology_cite AS (SELECT o.event_class_id,\n"
            f"  CASE WHEN o.citations IS NULL OR cardinality(o.citations) = 0 THEN NULL\n"
            f"       ELSE array_to_string(o.citations, '; ') END AS citation\n"
            f"  FROM brahma_event_ontology o),\n"
            f"signs AS (SELECT unnest(ARRAY['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio',\n"
            f"  'Sagittarius','Capricorn','Aquarius','Pisces']) AS name),\n"
            f"mechanism_weights AS (SELECT * FROM (VALUES {mech_values}) AS mw(rule_type, weight)),\n"
            f"m6_constants AS (SELECT * FROM (VALUES {m6_values}) AS x(target_type, ref, citation, qualifier))\n"
            f"SELECT m.event_class, m.target_type, m.target_ref, v.violation\n"
            f"  FROM gochara_resonance_map m\n"
            f"  CROSS JOIN LATERAL (SELECT CASE\n"
            f"    WHEN m.event_class <> ALL({eligible_classes_array()}) THEN 'class:not_eligible'\n"
            f"    WHEN m.target_type <> ALL({checked}) THEN 'type:unknown'\n"
            f"    WHEN m.target_type = 'mechanism_node' AND m.weight IS DISTINCT FROM (\n"
            f"         SELECT mw.weight FROM bg_transit_rules r JOIN mechanism_weights mw ON mw.rule_type = r.rule_type\n"
            f"          WHERE r.id = m.source_rule_id) THEN 'weight:mechanism_rule_type'\n"
            f"    WHEN m.target_type = 'mechanism_node' AND m.target_ref IS DISTINCT FROM (\n"
            f"         SELECT lower(btrim(r.graha)) || ':' || r.rule_type || ':h' || r.primary_house::text\n"
            f"           FROM bg_transit_rules r WHERE r.id = m.source_rule_id) THEN 'identity:mechanism_ref'\n"
            f"    WHEN m.target_type = 'mechanism_node' AND NOT EXISTS (\n"
            f"         SELECT 1 FROM bg_transit_rules r\n"
            f"           JOIN class_karakas ck ON ck.event_class = m.event_class AND ck.karaka_lower = lower(btrim(r.graha))\n"
            f"           JOIN class_houses ch ON ch.event_class = m.event_class AND ch.house = r.primary_house\n"
            f"          WHERE r.id = m.source_rule_id) THEN 'eligibility:mechanism_rule'\n"
            f"    WHEN m.target_type <> 'mechanism_node' AND m.weight <> (CASE m.target_type {cases} END) THEN 'weight'\n"
            f"    WHEN m.target_type IN ('gulika_mandi_distance','yamakantaka_difference')\n"
            f"         AND m.event_class <> ALL({m6_classes}) THEN 'class:m6_scope'\n"
            f"    WHEN m.target_type IN ('gulika_mandi_distance','yamakantaka_difference')\n"
            f"         AND (m.uncited_extension IS TRUE OR NOT EXISTS (SELECT 1 FROM m6_constants x\n"
            f"              WHERE x.target_type = m.target_type AND x.ref = m.target_ref\n"
            f"                AND x.citation = m.classical_citation AND x.qualifier = m.target_qualifier))\n"
            f"         THEN 'provenance:m6_constant'\n"
            f"    WHEN m.target_type IN ('bhava','lord','karaka') AND (m.uncited_extension IS TRUE\n"
            f"         OR m.classical_citation IS DISTINCT FROM (SELECT citation FROM ontology_cite oc\n"
            f"                                                     WHERE oc.event_class_id = m.event_class))\n"
            f"         THEN 'provenance:ontology_citation'\n"
            f"    WHEN m.target_type = 'mechanism_node' AND (m.uncited_extension IS TRUE OR m.source_rule_id IS NULL\n"
            f"         OR m.classical_citation IS DISTINCT FROM (SELECT r.classical_citation FROM bg_transit_rules r\n"
            f"                                                     WHERE r.id = m.source_rule_id))\n"
            f"         THEN 'provenance:transit_rule_citation'\n"
            f"    WHEN m.target_type IN ('sensitive_degree','arudha','bhava_arudha','yoga_constituent','dasha_lord_portfolio')\n"
            f"         AND (m.uncited_extension IS NOT TRUE OR m.classical_citation IS NOT NULL)\n"
            f"         THEN 'provenance:own_synthesis'\n"
            f"    WHEN m.target_type = 'lord' AND m.target_resolution_state IS DISTINCT FROM (\n"
            f"         CASE WHEN (SELECT n FROM lagna) IS NULL THEN 'unavailable'\n"
            f"              WHEN m.target_ref !~ '^[0-9]+L$' OR (substring(m.target_ref from '^([0-9]+)L$'))::int NOT BETWEEN 1 AND 12\n"
            f"                   THEN 'unavailable'\n"
            f"              WHEN NOT (SELECT ok FROM lords_complete) THEN 'unqualified'\n"
            f"              WHEN NOT EXISTS (SELECT 1 FROM reference_signs rs JOIN graha g ON g.name = rs.lord\n"
            f"                                 JOIN present p ON p.fact_subject = g.subject\n"
            f"                                WHERE rs.sign_id = (((SELECT n FROM lagna) - 1)\n"
            f"                                     + ((substring(m.target_ref from '^([0-9]+)L$'))::int - 1)) % 12 + 1)\n"
            f"                   THEN 'unavailable'\n"
            f"              ELSE 'resolved' END) THEN 'state:lord_chain'\n"
            f"    WHEN m.target_type = 'bhava' AND m.target_resolution_state IS DISTINCT FROM\n"
            f"         (CASE WHEN (SELECT n FROM lagna) IS NULL THEN 'unavailable' ELSE 'resolved' END) THEN 'state:bhava_lagna'\n"
            f"    WHEN m.target_type IN ('karaka','dasha_lord_portfolio') AND m.target_resolution_state IS DISTINCT FROM\n"
            f"         (CASE WHEN EXISTS (SELECT 1 FROM graha g JOIN present p ON p.fact_subject = g.subject\n"
            f"                             WHERE g.name = m.target_ref) THEN 'resolved' ELSE 'unavailable' END)\n"
            f"         THEN 'state:graha_position'\n"
            f"    WHEN m.target_type = 'sensitive_degree' AND m.target_resolution_state IS DISTINCT FROM\n"
            f"         (CASE WHEN EXISTS (SELECT 1 FROM chart_facts f JOIN present p ON p.fact_subject = f.fact_subject\n"
            f"                             WHERE f.fact_id::text = m.target_ref AND f.chart_id = m.chart_id)\n"
            f"               THEN 'resolved' ELSE 'unavailable' END) THEN 'state:sensitive_subject_position'\n"
            f"    WHEN m.target_type = 'arudha' AND m.target_resolution_state IS DISTINCT FROM\n"
            f"         (CASE WHEN EXISTS (SELECT 1 FROM chart_facts f JOIN signs s ON s.name = btrim(f.fact_value_text)\n"
            f"                             WHERE f.fact_id::text = m.target_ref AND f.chart_id = m.chart_id)\n"
            f"               THEN 'resolved' ELSE 'unavailable' END) THEN 'state:arudha_sign'\n"
            f"    WHEN m.target_type = 'bhava_arudha' AND m.target_resolution_state IS DISTINCT FROM\n"
            f"         (CASE WHEN EXISTS (SELECT 1 FROM chart_facts f JOIN signs s ON s.name = btrim(f.fact_value_text)\n"
            f"                             WHERE f.chart_id = m.chart_id AND f.ayanamsha_id = '{CANONICAL_AYANAMSHA}'\n"
            f"                               AND f.fact_category = 'arudha_pada' AND f.fact_key = 'sign'\n"
            f"                               AND f.fact_subject = replace(m.target_ref, 'BHAVA_', ''))\n"
            f"               THEN 'resolved' ELSE 'unavailable' END) THEN 'state:bhava_arudha_sign'\n"
            f"    WHEN m.target_type = 'yoga_constituent' AND m.target_resolution_state <> 'resolved' THEN 'state:yoga'\n"
            f"    WHEN m.target_type = 'lord' AND m.target_qualifier IS DISTINCT FROM\n"
            f"         (CASE WHEN EXISTS (SELECT 1 FROM brahma_event_ontology o,\n"
            f"                                 jsonb_array_elements_text(o.signature_model->'lords') AS l(value)\n"
            f"                             WHERE o.event_class_id = m.event_class AND l.value ILIKE '%afflicted%'\n"
            f"                               AND l.value ~ ('(^|[^0-9])' || m.target_ref || '([^0-9]|$)'))\n"
            f"               THEN 'afflicted' END) THEN 'qualifier:lord_afflicted'\n"
            f"    WHEN m.target_type = 'yoga_constituent' AND NOT EXISTS (SELECT 1 FROM ga_yoga_firings y\n"
            f"         WHERE y.chart_id = m.chart_id AND y.ayanamsha_id = '{CANONICAL_AYANAMSHA}' AND y.fired\n"
            f"           AND y.yoga_canonical_id = m.target_ref\n"
            f"           AND (CASE WHEN y.bhanga_active IS TRUE THEN 'bhanga_active' END) IS NOT DISTINCT FROM m.target_qualifier)\n"
            f"         THEN 'qualifier:yoga_bhanga'\n"
            f"    END AS violation) v\n"
            f" WHERE m.chart_id = '{cid}' AND v.violation IS NOT NULL\n"
            f" ORDER BY m.event_class, m.target_type, m.target_ref;")


__all__ = [
    "CONTENT_COLUMNS", "NEGATIVE_VALUES", "POSITIVE_VALUES", "EXPECTED_WEIGHTS",
    "ELIGIBLE_EVENT_CLASSES", "eligible_classes_array", "FACT_BACKED_TARGET_TYPES",
    "r1_identity_sql", "r2_identity_sql", "r3_identity_sql", "r4_lord_identity_sql",
    "mechanism_identity_sql", "value_invariants_sql", "MECHANISM_WEIGHTS", "CHECKED_TARGET_TYPES",
    "M6_CONSTANT_ROWS",
    "snapshot_table_name", "create_snapshot_sql", "partition_digest_sql",
    "full_row_digest_sql", "rollback_sql", "negative_sensitive_targets_sql",
    "dangling_fact_refs_sql", "r5_qualifier_identity_sql", "new_stamp_utc",
]
