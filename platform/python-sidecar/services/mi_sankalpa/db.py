"""
db.py — THE ONLY MODULE IN `services/mi_sankalpa/` THAT TOUCHES A DATABASE.

Mirrors `services/mi_bhara/db.py`'s own convention (one named module per package that may
touch the database, so a source census can state "which files read the LEL / write the
ledger" as a one-line whitelist rather than a judgement call) — but this is `mi_sankalpa`'s
OWN module, not a reuse of `mi_bhara`'s: `mi_bhara.db` is scoped, by its own docstring, to
the temporal-field pipeline's Circularity Guard, and importing it here would blur that
lane's file boundary for no benefit (`services/mi_bhara/living_lel.py`'s pure functions ARE
shared — see `arms.py` — because that module is explicitly DB-free and reuse-sanctioned by
KALA_W4_UPAYA_DESIGN_v1_0.md §4.3).

FROZEN WRITER CONTRACT (CLAUDE.md §N.2): every function here takes a caller-owned
connection and NEVER commits, rolls back, or closes it. Nothing here writes
`asset_throughput`.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Any, Mapping, Sequence

from services.mi_bhara.living_lel import LelEventRef, OpenPrediction

logger = logging.getLogger(__name__)


def _rows(cur) -> list[dict]:
    fetched = cur.fetchall()
    if not fetched:
        return []
    if isinstance(fetched[0], Mapping):
        return [dict(r) for r in fetched]
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in fetched]


def table_exists(conn: Any, table: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass(%s) IS NOT NULL AS present", (table,))
        row = cur.fetchone()
    if row is None:
        return False
    return bool(row["present"] if isinstance(row, Mapping) else row[0])


# ── reads: the LEL (sanctioned — §4.3 names the LEL read explicitly) ───────────────────────

def fetch_lel_events(conn: Any, chart_id: str, birth_iso: str) -> list[LelEventRef]:
    """The chart's recorded life events, as days since birth. Same `event_class` derivation
    (`COALESCE(event_type, category)`) as `mi_bhara.db.fetch_lel_events`, so a LEL event
    this writer sees and one `mi_bhara` sees resolve to the identical `event_class` string
    — BUT `LelEventRef.event_id` is populated from `life_events.id` (the UUID primary key),
    NOT the human-readable `event_id` text column `mi_bhara`'s own reader selects: this
    writer's `mimamsa_intervention_ledger.outcome_event_id` is a hard
    `REFERENCES life_events(id)` FK, and only the UUID PK satisfies it."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id,
                   COALESCE(event_type, category) AS event_class,
                   (event_date - %s::date)::double precision AS t_days
              FROM life_events
             WHERE chart_id = %s
             ORDER BY event_date, id
            """,
            (birth_iso, chart_id),
        )
        return [
            LelEventRef(event_id=str(r["id"]), event_class=str(r["event_class"]), t=float(r["t_days"]))
            for r in _rows(cur)
        ]


# ── reads: mimamsa_intervention_ledger ──────────────────────────────────────────────────────

def fetch_unresolved_rows(conn: Any, chart_id: str, birth_iso: str) -> list[dict]:
    """Rows matching the writer's exact idempotency predicate (§4.3):
    `study_arm = 'elected_pending' AND performed IS NULL AND outcome_event_id IS NULL`.

    Returned as full dicts (every column) so the writer can round-trip them verbatim —
    this is the READ half of the "read before delete, write back after" loss-free
    round trip; the days-since-birth fields are ADDED (not substituted) so the same row can
    also be scored via `arms.score_ledger_rows_against_lel_event` without a second query.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT intervention_id, chart_id, intent, intervention_class,
                   rite_or_activity_class, event_class,
                   lower(elected_window) AS window_start, upper(elected_window) AS window_end,
                   precision_regime, precision_basis, adjudication_record, score_vector,
                   efficacy_tier, source_citation, paddhati_version, predicted_differential,
                   prediction_id, study_arm, performed, performed_at, performed_attested_by,
                   outcome_event_id, outcome_linked_at, authority_basis, filed_by,
                   adoption_basis, engine_version, build_id, created_at,
                   (lower(elected_window)::date - %s::date)::double precision AS w_start_t,
                   (upper(elected_window)::date - %s::date)::double precision AS w_end_t,
                   (created_at::date - %s::date)::double precision            AS filed_at_t
              FROM mimamsa_intervention_ledger
             WHERE chart_id = %s
               AND study_arm = 'elected_pending'
               AND performed IS NULL
               AND outcome_event_id IS NULL
             ORDER BY intervention_id
            """,
            (birth_iso, birth_iso, birth_iso, chart_id),
        )
        return _rows(cur)


def to_open_predictions(rows: Sequence[dict]) -> list[OpenPrediction]:
    """Adapts `fetch_unresolved_rows` output into the shape
    `living_lel.score_predictions_against_event` expects. `prediction_id` here is the
    ledger's OWN `intervention_id` (a ledger row, not a `brahma_prospective_ledger` row, is
    what is being scored against the LEL) — a row with no `event_class` (nullable in the
    schema) is excluded, since it can never match a LEL event's own always-concrete class.
    """
    out: list[OpenPrediction] = []
    for r in rows:
        if not r.get("event_class"):
            continue
        out.append(
            OpenPrediction(
                prediction_id=str(r["intervention_id"]),
                event_class=str(r["event_class"]),
                window_start=float(r["w_start_t"]),
                window_end=float(r["w_end_t"]),
                filed_at_t=float(r["filed_at_t"]),
                window_id=None,
                claim_shape="interval",
            )
        )
    return out


def fetch_attested_rows(conn: Any, chart_id: str) -> list[dict]:
    """Rows carrying a native attestation (`performed IS NOT NULL`) — candidates for the
    study-arm RECLASSIFICATION pass (arms.classify_study_arm). Never candidates for
    deletion (they fail the idempotency predicate by construction)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT intervention_id, study_arm, performed, performed_at,
                   lower(elected_window) AS window_start, upper(elected_window) AS window_end
              FROM mimamsa_intervention_ledger
             WHERE chart_id = %s
               AND performed IS NOT NULL
            """,
            (chart_id,),
        )
        return _rows(cur)


def fetch_known_event_classes(conn: Any, chart_id: str) -> list[str]:
    """DISTINCT `event_class` already present among this chart's OWN filed interventions —
    the arm-4 scoping decision (`arms.find_unelected_lel_events`'s `known_event_classes`)."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT DISTINCT event_class FROM mimamsa_intervention_ledger "
            "WHERE chart_id = %s AND event_class IS NOT NULL",
            (chart_id,),
        )
        return [str(r["event_class"]) for r in _rows(cur)]


def fetch_covered_windows_by_class(conn: Any, chart_id: str) -> dict[str, list[tuple[datetime, datetime]]]:
    """Every existing ledger row's `elected_window`, by class — of ANY `study_arm` (an
    event already covered by a prior election, resolved or not, is not "without
    election")."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT event_class, lower(elected_window) AS window_start, upper(elected_window) AS window_end
              FROM mimamsa_intervention_ledger
             WHERE chart_id = %s AND event_class IS NOT NULL
            """,
            (chart_id,),
        )
        out: dict[str, list[tuple[datetime, datetime]]] = {}
        for r in _rows(cur):
            out.setdefault(str(r["event_class"]), []).append((r["window_start"], r["window_end"]))
        return out


def fetch_existing_outcome_linked_event_ids(conn: Any, chart_id: str) -> set[str]:
    """`outcome_event_id`s already linked (any study_arm) — so a re-run of the arm-4 origin
    step, or a re-run of falsifier resolution, never double-links the same LEL event."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT outcome_event_id FROM mimamsa_intervention_ledger "
            "WHERE chart_id = %s AND outcome_event_id IS NOT NULL",
            (chart_id,),
        )
        return {str(r["outcome_event_id"]) for r in _rows(cur)}


# ── writes ───────────────────────────────────────────────────────────────────────────────

def delete_unresolved(conn: Any, chart_id: str) -> int:
    """THE exact idempotency predicate (§4.3) — never a blanket per-chart delete. Returns
    the row count deleted, purely for the writer's own logging; the caller is responsible
    for having already READ every one of these rows (see `fetch_unresolved_rows`) so the
    round trip is loss-free."""
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM mimamsa_intervention_ledger
             WHERE chart_id = %s
               AND study_arm = 'elected_pending'
               AND performed IS NULL
               AND outcome_event_id IS NULL
            """,
            (chart_id,),
        )
        return cur.rowcount


_REINSERT_SQL = """
    INSERT INTO mimamsa_intervention_ledger (
        intervention_id, chart_id, intent, intervention_class, rite_or_activity_class,
        event_class, elected_window, precision_regime, precision_basis,
        adjudication_record, score_vector, efficacy_tier, source_citation, paddhati_version,
        predicted_differential, prediction_id, study_arm, performed, performed_at,
        performed_attested_by, outcome_event_id, outcome_linked_at, authority_basis,
        filed_by, adoption_basis, engine_version, build_id, created_at
    ) VALUES (
        %(intervention_id)s, %(chart_id)s, %(intent)s, %(intervention_class)s,
        %(rite_or_activity_class)s, %(event_class)s,
        tstzrange(%(window_start)s, %(window_end)s), %(precision_regime)s,
        %(precision_basis)s, %(adjudication_record)s, %(score_vector)s, %(efficacy_tier)s,
        %(source_citation)s, %(paddhati_version)s, %(predicted_differential)s,
        %(prediction_id)s, %(study_arm)s, %(performed)s, %(performed_at)s,
        %(performed_attested_by)s, %(outcome_event_id)s, %(outcome_linked_at)s,
        %(authority_basis)s, %(filed_by)s, %(adoption_basis)s, %(engine_version)s,
        %(build_id)s, %(created_at)s
    )
"""


def reinsert_rows(conn: Any, rows: Sequence[dict]) -> int:
    """The re-insert half of the loss-free round trip. Each row is exactly what
    `fetch_unresolved_rows` read (verbatim), OPTIONALLY with `outcome_event_id` /
    `outcome_linked_at` populated by this same build's falsifier-resolution pass — never any
    other field. `adjudication_record` / `score_vector` are re-serialized to JSON text
    (psycopg accepts a JSON-shaped string for a jsonb column) since they were read back as
    already-parsed Python objects."""
    if not rows:
        return 0
    params = []
    for r in rows:
        p = dict(r)
        for jsonb_field in ("adjudication_record", "score_vector"):
            if not isinstance(p.get(jsonb_field), str):
                p[jsonb_field] = json.dumps(p.get(jsonb_field) or {})
        params.append(p)
    with conn.cursor() as cur:
        cur.executemany(_REINSERT_SQL, params)
    return len(rows)


def upsert_acted_without_election(
    conn: Any,
    *,
    chart_id: str,
    event_class: str,
    rite_or_activity_class: str,
    outcome_event_id: str,
    outcome_linked_at: datetime,
    window_start: date,
    window_end: date,
    engine_version: str,
    build_id: str | None,
) -> int:
    """Originates ONE `acted_without_election` row (§4.3 arm 4 — "the only arm the writer
    originates rather than records"). `ON CONFLICT DO NOTHING` on the natural key
    `(chart_id, intervention_class, rite_or_activity_class, elected_window)` — additive,
    idempotent, never destructive; a re-run over the same LEL event and the same derived
    window is a no-op, never a duplicate.

    `prediction_id` is NULL by construction (§4.3: "there was no election to record" — and
    the `_inferred_never_sealed` CHECK requires `adoption_basis = 'session_inferred'`
    whenever `prediction_id IS NULL`, which is exactly the honest state here: nothing was
    ever native-directed-filed for an event nobody elected)."""
    adjudication_record = json.dumps({"derived_from_lel": True, "outcome_event_id": outcome_event_id})
    params = {
        "chart_id": chart_id,
        "intent": (
            "derived from the LEL: an event of an already-elected class occurred with no "
            "covering election on record"
        ),
        "intervention_class": "elected_activity",
        "rite_or_activity_class": rite_or_activity_class,
        "event_class": event_class,
        "window_start": window_start,
        "window_end": window_end,
        "precision_regime": "day_grade",
        "precision_basis": "derived_from_lel_no_covering_election",
        "adjudication_record": adjudication_record,
        "score_vector": "{}",
        "efficacy_tier": "traditional",
        "source_citation": "derived from LEL event linkage — no classical prescription to cite",
        "paddhati_version": "derived_v01",
        "predicted_differential": "no election on record for this event — nothing to compare against a baseline",
        "prediction_id": None,
        "study_arm": "acted_without_election",
        "outcome_event_id": outcome_event_id,
        "outcome_linked_at": outcome_linked_at,
        "filed_by": "mi_sankalpa_writer",
        "adoption_basis": "session_inferred",
        "engine_version": engine_version,
        "build_id": build_id,
    }
    # Named parameters, one per column, in the SAME order as the column list -- explicit
    # rather than positional so a future edit to either list cannot silently misalign them
    # (the defect class this function shipped with and fixed before merge: a missing
    # `predicted_differential` value shifted every later column by one).
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO mimamsa_intervention_ledger (
                chart_id, intent, intervention_class, rite_or_activity_class, event_class,
                elected_window, precision_regime, precision_basis, adjudication_record,
                score_vector, efficacy_tier, source_citation, paddhati_version,
                predicted_differential, prediction_id, study_arm, outcome_event_id,
                outcome_linked_at, filed_by, adoption_basis, engine_version, build_id
            ) VALUES (
                %(chart_id)s, %(intent)s, %(intervention_class)s, %(rite_or_activity_class)s,
                %(event_class)s, tstzrange(%(window_start)s, %(window_end)s),
                %(precision_regime)s, %(precision_basis)s, %(adjudication_record)s::jsonb,
                %(score_vector)s::jsonb, %(efficacy_tier)s, %(source_citation)s,
                %(paddhati_version)s, %(predicted_differential)s, %(prediction_id)s,
                %(study_arm)s, %(outcome_event_id)s, %(outcome_linked_at)s, %(filed_by)s,
                %(adoption_basis)s, %(engine_version)s, %(build_id)s
            )
            ON CONFLICT (chart_id, intervention_class, rite_or_activity_class, elected_window)
            DO NOTHING
            """,
            params,
        )
        return cur.rowcount


def update_study_arm(conn: Any, intervention_id: str, study_arm: str) -> None:
    """Reclassifies ONE already-attested row's `study_arm` — never touches `performed`,
    `performed_at`, `adjudication_record`, `score_vector`, `predicted_differential`, or
    `paddhati_version` (§5.5 pre-registration integrity)."""
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE mimamsa_intervention_ledger SET study_arm = %s WHERE intervention_id = %s",
            (study_arm, intervention_id),
        )
