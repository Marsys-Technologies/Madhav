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
import uuid

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


def dangling_fact_refs_sql(chart_id: str) -> str:
    """Rows whose target_ref is (or must be) a chart_facts fact_id of THIS
    chart but resolves to none — MUST be 0. Uses NOT EXISTS (a NULL-safe
    form; SQL NOT IN never rejects nulls)."""
    cid = _check_uuid(chart_id)
    return (f"SELECT COUNT(*) FROM gochara_resonance_map m\n"
            f" WHERE m.chart_id = '{cid}'\n"
            f"   AND (m.target_ref IS NULL\n"
            f"        OR (m.target_type IN ('sensitive_degree', 'arudha')\n"
            f"            AND m.target_ref !~ '^[0-9a-f]{{8}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{12}}$')\n"
            f"        OR (m.target_ref ~ '^[0-9a-f]{{8}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{12}}$'\n"
            f"            AND NOT EXISTS (SELECT 1 FROM chart_facts f\n"
            f"                             WHERE f.fact_id::text = m.target_ref\n"
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
                " WHERE l.value ILIKE '%afflicted%'")
    return (f"-- rows with the qualifier that the ontology does not name (MUST be 0 rows):\n"
            f"{rows}\nEXCEPT\n{expected};",
            f"-- ontology-named afflicted lords missing the qualifier (MUST be 0 rows):\n"
            f"{expected}\nEXCEPT\n{rows};")


__all__ = [
    "CONTENT_COLUMNS", "NEGATIVE_VALUES", "POSITIVE_VALUES",
    "snapshot_table_name", "create_snapshot_sql", "partition_digest_sql",
    "full_row_digest_sql", "rollback_sql", "negative_sensitive_targets_sql",
    "dangling_fact_refs_sql", "r5_qualifier_identity_sql", "new_stamp_utc",
]
