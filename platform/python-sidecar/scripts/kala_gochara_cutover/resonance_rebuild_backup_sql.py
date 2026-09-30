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
  * the partition digest is a canonical md5 over the CONTENT columns
    (id / computed_at excluded), computed identically for the live table and
    the snapshot so equality means "same rows";
  * the rollback is a single transaction whose DO block REFUSES to delete
    when the snapshot is absent, empty, carries another chart, or does not
    match the recorded count/digest; the restore is verified afterwards by
    the same digest.
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

_ROW_TEXT = (
    "concat_ws('|', event_class, target_type, target_ref, weight::text, "
    "coalesce(classical_citation, '<null>'), uncited_extension::text, "
    "coalesce(source_rule_id::text, '<null>'), "
    "coalesce(target_resolution_state, '<null>'), "
    "coalesce(target_qualifier, '<null>'))"
)


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
    """(row_count, content_digest) of one chart's partition in `table`.
    Deterministic: rows canonicalised over the content columns and sorted."""
    if table != "gochara_resonance_map":
        _check_table(table)
    return (f"SELECT COUNT(*) AS row_count,\n"
            f"       COALESCE(md5(string_agg({_ROW_TEXT}, E'\\n' ORDER BY {_ROW_TEXT})), 'empty') AS content_digest\n"
            f"  FROM {table}\n"
            f" WHERE chart_id = '{_check_uuid(chart_id)}';")


def rollback_sql(table: str, chart_id: str, recorded_count: int,
                 recorded_digest: str) -> str:
    """One transaction: refuse-unless-verified, then DELETE + INSERT the exact
    preimage (all columns, ids included), then verify the restore."""
    tbl = _check_table(table)
    cid = _check_uuid(chart_id)
    if not _MD5_RE.match(recorded_digest):
        raise ValueError("recorded_digest must be an md5 hex or 'empty'")
    n = int(recorded_count)
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
         COALESCE(md5(string_agg({_ROW_TEXT}, E'\\n' ORDER BY {_ROW_TEXT})), 'empty')
    INTO snap_count, snap_digest
    FROM {tbl} WHERE chart_id = '{cid}';
  IF snap_count <> {n} OR snap_digest <> '{recorded_digest}' THEN
    RAISE EXCEPTION 'ROLLBACK REFUSED: snapshot {tbl} is stale or incomplete (count % digest % vs recorded {n} {recorded_digest})', snap_count, snap_digest;
  END IF;
  DELETE FROM gochara_resonance_map WHERE chart_id = '{cid}';
  INSERT INTO gochara_resonance_map SELECT * FROM {tbl} WHERE chart_id = '{cid}';
  SELECT COUNT(*),
         COALESCE(md5(string_agg({_ROW_TEXT}, E'\\n' ORDER BY {_ROW_TEXT})), 'empty')
    INTO snap_count, snap_digest
    FROM gochara_resonance_map WHERE chart_id = '{cid}';
  IF snap_count <> {n} OR snap_digest <> '{recorded_digest}' THEN
    RAISE EXCEPTION 'ROLLBACK FAILED VERIFICATION: restored count % digest % vs recorded {n} {recorded_digest}', snap_count, snap_digest;
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


__all__ = [
    "CONTENT_COLUMNS", "NEGATIVE_VALUES", "POSITIVE_VALUES",
    "snapshot_table_name", "create_snapshot_sql", "partition_digest_sql",
    "rollback_sql", "negative_sensitive_targets_sql", "dangling_fact_refs_sql",
    "new_stamp_utc",
]
