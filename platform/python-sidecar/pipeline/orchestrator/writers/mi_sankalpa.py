"""
mi_sankalpa — Unified Intervention Ledger (L5 Mīmāṃsā, registry item 42)
=========================================================================
Spec: `KALA_W4_UPAYA_DESIGN_v1_0.md` (v1.1) §4 (Lane S), §4.3 (this writer's contract),
§8.2 (the asset_registry seed row, migration 532). Execution contract:
`SHAD_DARSHANA_BRIEF_v2_0.md` §3 W4, §2.5.

`mimamsa_intervention_ledger` rows are FILED live, at serve time, through the sanctioned
HTTP action (`platform-mcp/src/lib/intervention_filing.ts`'s `fileInterventionFalsifier`) —
never inserted by this writer (ruling S-1: the prediction spine is
`brahma_prospective_ledger`; this table only REFERENCES it, by FK). This writer's per-build
job over the rows that already exist:

  1. FALSIFIER RESOLUTION FIRST (§4.3) — before any arm transition: score every
     `elected_pending` row with no `outcome_event_id` yet against the chart's LEL, reusing
     `services/mi_bhara/living_lel.py`'s `score_predictions_against_event` (the design's own
     binding "reuse, don't write a second matcher" instruction). A HIT links
     `outcome_event_id` / `outcome_linked_at`.
  2. STUDY-ARM RECLASSIFICATION — every already-attested row (`performed IS NOT NULL`) is
     re-derived deterministically from its own `performed`/`performed_at` fields
     (`services/mi_sankalpa/arms.py::classify_study_arm`). Never touches `performed` itself
     (native-attested only).
  3. ARM-4 ORIGINATION — an LEL event whose class already appears among this chart's own
     filed interventions, with no existing `elected_window` covering it, becomes a new
     `acted_without_election` row (idempotent, additive, `ON CONFLICT DO NOTHING`).

PER-CHART scope, STATUS-PRESERVING idempotency (§4.3, load-bearing — NOT a blanket
`DELETE WHERE chart_id = %s`): only rows matching
`study_arm = 'elected_pending' AND performed IS NULL AND outcome_event_id IS NULL` are ever
deleted, and every one of them is READ before the delete and RE-INSERTED (verbatim, or with
a freshly-resolved `outcome_event_id`) in the same pass — a loss-free round trip. Adjudicated
and native-attested rows never match that predicate and are therefore never touched by the
delete at all.

FROZEN orchestrator contract: @register, run(ctx) -> WriterResult. NEVER commits, rolls
back, or closes ctx.db_conn. Never writes `asset_throughput`.
"""
from __future__ import annotations

import logging
import time
from datetime import date, datetime, timedelta, timezone

from pipeline.orchestrator.writers import ContextSpec, WriterBase, WriterResult, register

logger = logging.getLogger(__name__)

ASSET_ID = "mi_sankalpa"
ENGINE_VERSION = "mi_sankalpa_v1.0"

#: Reported on the result when an upstream is legitimately absent or the chart has nothing
#: to process — honest, named degradation, mirroring `mi_bhara`'s `NOTE_*` precedent.
NOTE_LEDGER_TABLE_ABSENT = "mimamsa_intervention_ledger_table_absent"
NOTE_NO_INTERVENTIONS = "no_filed_interventions"
NOTE_NO_LEL = "no_lel_events"


def _birth_date(ctx: ContextSpec) -> date:
    """The chart's birth DATE, from `ctx.config['birth_params']` — read, never recomputed
    from an ephemeris (§N.5). Local to this writer (not imported from `mi_bhara.py`) to
    keep the two lanes' files independent; the derivation itself is intentionally identical
    to `mi_bhara.py::_birth_iso` so the two packages' days-since-birth axes agree."""
    bp = ctx.config.get("birth_params") or {}
    raw = bp.get("datetime_iso") or bp.get("birth_datetime_utc") or bp.get("date")
    if not raw:
        raise ValueError(
            "mi_sankalpa requires ctx.config['birth_params'] with a datetime — LEL dates "
            "must be converted onto a days-since-birth axis, and inventing a birth instant "
            "here would silently misalign every event (§N.5)."
        )
    if isinstance(raw, (datetime, date)):
        return raw.date() if isinstance(raw, datetime) else raw
    return date.fromisoformat(str(raw)[:10])


@register(ASSET_ID)
class MiSankalpaWriter(WriterBase):
    """LIGHT writer — the whole per-build pass in one unit (`run(ctx)`)."""

    asset_id = ASSET_ID
    has_substeps = False

    def run(self, ctx: ContextSpec) -> WriterResult:
        started = time.time()
        # Imported inside run() so merely importing the writers package (which the
        # orchestrator does at startup) never drags in this package's dependency surface —
        # same reasoning as mi_bhara.py.
        from services.mi_bhara.living_lel import OUTCOME_HIT
        from services.mi_sankalpa import db
        from services.mi_sankalpa.arms import (
            STUDY_ARM_ACTED_WITHOUT_ELECTION,
            classify_study_arm,
            find_unelected_lel_events,
            score_ledger_rows_against_lel_event,
        )

        chart_id = ctx.config.get("chart_id")
        if not chart_id:
            raise ValueError("mi_sankalpa is a per_chart asset and requires ctx.config['chart_id']")
        conn = ctx.db_conn
        build_id = ctx.build_id
        notes: list[str] = []

        if not db.table_exists(conn, "mimamsa_intervention_ledger"):
            return WriterResult(
                asset_id=ASSET_ID,
                rows_inserted=0,
                duration_seconds=time.time() - started,
                notes=(
                    f"{NOTE_LEDGER_TABLE_ABSENT}: mimamsa_intervention_ledger not found — "
                    "ensure migration 532 has been applied."
                ),
            )

        birth_date = _birth_date(ctx)
        birth_iso = birth_date.isoformat()

        rows_updated = 0
        rows_inserted = 0

        # ── phase 1 — FALSIFIER RESOLUTION FIRST (§4.3) ────────────────────────────────
        # Score every currently-unresolved row against the LEL BEFORE any arm transition,
        # so a later reclassification pass cannot change what counted as a match.
        unresolved_rows = db.fetch_unresolved_rows(conn, chart_id, birth_iso)
        lel_events = db.fetch_lel_events(conn, chart_id, birth_iso)

        if not lel_events:
            notes.append(NOTE_NO_LEL)

        outcome_links: dict[str, str] = {}  # intervention_id -> life_events.id (as string)
        if lel_events and unresolved_rows:
            open_predictions = db.to_open_predictions(unresolved_rows)
            for ev in lel_events:
                for scored in score_ledger_rows_against_lel_event(ev, open_predictions):
                    if scored.outcome == OUTCOME_HIT and scored.matched_event_id:
                        # First hit wins; a row already linked this pass is not re-scored.
                        outcome_links.setdefault(scored.prediction_id, scored.matched_event_id)

        # ── phase 2 — the loss-free, status-preserving round trip ─────────────────────
        # Delete-then-reinsert, scoped EXACTLY to §4.3's predicate. Every row read above is
        # written back — verbatim, or with a freshly-resolved outcome link applied — so the
        # round trip never silently drops a row. This IS the writer's rebuildable output;
        # rows outside this predicate (attested or already outcome-linked) are never read
        # here and therefore can never be deleted here either.
        if unresolved_rows:
            now = datetime.now(timezone.utc)
            reinsert_payload = []
            for r in unresolved_rows:
                row = dict(r)
                link = outcome_links.get(str(row["intervention_id"]))
                if link:
                    row["outcome_event_id"] = link
                    row["outcome_linked_at"] = now
                    rows_updated += 1
                reinsert_payload.append(row)

            db.delete_unresolved(conn, chart_id)
            db.reinsert_rows(conn, reinsert_payload)

        if not unresolved_rows and not lel_events:
            notes.append(NOTE_NO_INTERVENTIONS)

        # ── phase 3 — study-arm RECLASSIFICATION for already-attested rows ────────────
        # Never touches performed/performed_at (native-attested only) or any §5.5-frozen
        # field — only study_arm, and only when classify_study_arm resolves a disposition
        # (None ⇒ leave unchanged; the one combination §4.3's table left unspecified).
        for r in db.fetch_attested_rows(conn, chart_id):
            new_arm = classify_study_arm(
                performed=r["performed"],
                performed_at=r["performed_at"],
                window_start=r["window_start"],
                window_end=r["window_end"],
            )
            if new_arm is not None and new_arm != r["study_arm"]:
                db.update_study_arm(conn, r["intervention_id"], new_arm)
                rows_updated += 1

        # ── phase 4 — ARM-4 ORIGINATION from the LEL ───────────────────────────────────
        # The one arm this writer originates rather than records (§4.3). Scoped to event
        # classes this chart has ALREADY filed at least one intervention for — never a
        # class this writer has no basis to know is intervention-relevant.
        if lel_events:
            known_classes = db.fetch_known_event_classes(conn, chart_id)
            if known_classes:
                covered = db.fetch_covered_windows_by_class(conn, chart_id)
                already_linked = db.fetch_existing_outcome_linked_event_ids(conn, chart_id)
                already_linked |= set(outcome_links.values())
                unelected = find_unelected_lel_events(
                    lel_events=lel_events,
                    known_event_classes=known_classes,
                    birth_date=birth_date,
                    covered_windows_by_class=covered,
                )
                for ev in unelected:
                    if ev.event_id in already_linked:
                        continue
                    inserted = db.upsert_acted_without_election(
                        conn,
                        chart_id=chart_id,
                        event_class=ev.event_class,
                        rite_or_activity_class=f"lel_derived::{ev.event_class}",
                        outcome_event_id=ev.event_id,
                        outcome_linked_at=datetime.now(timezone.utc),
                        # elected_window is TSTZRANGE with default '[)' bounds -- a
                        # start==end range is EMPTY (lower()/upper() both NULL), which broke
                        # the NEXT rebuild's arm-4 containment check. One calendar day wide.
                        window_start=ev.event_date,
                        window_end=ev.event_date + timedelta(days=1),
                        engine_version=ENGINE_VERSION,
                        build_id=build_id,
                    )
                    rows_inserted += inserted
                    if inserted:
                        notes.append(STUDY_ARM_ACTED_WITHOUT_ELECTION)

        logger.info(
            "[mi_sankalpa] chart=%s round-tripped=%d updated=%d originated=%d",
            chart_id, len(unresolved_rows), rows_updated, rows_inserted,
        )

        return WriterResult(
            asset_id=ASSET_ID,
            rows_inserted=rows_inserted,
            rows_updated=rows_updated,
            duration_seconds=time.time() - started,
            notes="; ".join(dict.fromkeys(notes)) if notes else "",
        )
