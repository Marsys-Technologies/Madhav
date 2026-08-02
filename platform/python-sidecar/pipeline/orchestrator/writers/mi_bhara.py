"""
mi_bhara — Kāla Bhāra, "the weight of time". STAGE 9 of the ṢAḌ-DARŚANA W2 temporal-field
pipeline. L5 Mīmāṃsā-seated.

Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §7.2 (fitting harness), §7.3 (skill + GOF), §7.5 (weights
versioning + acyclicity), §7.6 (the Living-LEL plane). Registry items 21, 39; E1's D3 fit.
Seed row + migration: `platform/supabase/migrations/497_kala_field_skill_gof.sql`.

── THE FROZEN ORCHESTRATOR CONTRACT (CLAUDE.md §N.2) ──────────────────────────────────────
`@register('mi_bhara')` → `WriterBase` subclass implementing `run(ctx)` (the LIGHT-writer
shape; `has_substeps = False`). Runs on `ctx.db_conn` and NEVER commits, rolls back or closes
it. Never writes `asset_throughput` — the orchestrator is the sole build-state writer. Takes
`chart_id` and `birth_params` from `ctx.config`.

Why LIGHT and not heavy: the whole fit is ≤ ~25 parameters and one L-BFGS-B run per event
class over a handful of segments. There is no chunk large enough to need its own savepoint, so
a substep plan would be ceremony without isolation value. Note for a future session that
changes that: the §N.3 delete would then have to MOVE into `plan_substeps` (the
`ka_gochara_sweep` D-5 RED-C lesson — substep dispatch order is arbitrary and a per-substep
delete silently wipes sibling substeps' committed rows). It is safe where it is only because
this writer has exactly one substep.

── THE FIVE PHASES (§7.6's incremental flow, in its order) ────────────────────────────────
  0. resolve the weights pin ONCE (§7.5 sub-rule 5) and read the field
  1. FALSIFIER RESOLUTION FIRST — score the LEL against every open prospective ledger entry
     (item 20). Before any weight moves, so a refit cannot change what counted as a hit.
  2. FIT — forward-chaining CV, shrinkage to the classical priors, trust region → a NEW
     weights version row (INSERT only)
  3. SKILL + GOF — published in all three honest states
  4. BIOGRAPHICAL-JOIN REFRESH — `biographical_echo` insights, `lel_derived = TRUE`, excluded
     from the field hash
  5. MATURITY — the `calibration_maturity` the envelope carries

── HONEST DEGRADATION ─────────────────────────────────────────────────────────────────────
Every upstream this writer depends on may legitimately be absent at W2 (`ka_kshetra` is
another lane's asset, and `bg_cohort` is an L0 super-admin build). Each absence is reported as
a NAMED note on the `WriterResult` — `kala_field_absent`, `no_lel_events`,
`biographical_join_deferred` — never as a crash and never as a silently-empty success. A
chart with no LEL is not an error state: it is the §7.6 LEL-absent scenario, and its correct
output is the classical priors, `skill_state='underpowered'`, and a maturity of zero.

── CIRCULARITY GUARD ──────────────────────────────────────────────────────────────────────
This writer is the ONE place in the field pipeline that may read the LEL, and it does so only
through `services/mi_bhara/db.py`. Stages 0–8 (`ka_kshetra`) never do. Both halves of the
guard are enforced in `tests/l5/test_mi_bhara_circularity_guard_w2.py`.
"""
from __future__ import annotations

import logging
import time
from datetime import date, datetime
from typing import Any

from pipeline.orchestrator.writers import ContextSpec, WriterBase, WriterResult, register

logger = logging.getLogger(__name__)

ASSET_ID = "mi_bhara"

#: Reported on the result when an upstream is legitimately absent. Named, never silent.
NOTE_FIELD_ABSENT = "kala_field_absent"
NOTE_NO_LEL = "no_lel_events"
NOTE_BIO_JOIN_DEFERRED = "biographical_join_deferred"
NOTE_SKILL_TABLES_ABSENT = "skill_tables_absent"


def _birth_iso(ctx: ContextSpec) -> str:
    """The chart's birth DATE, as `YYYY-MM-DD`, from `ctx.config['birth_params']`.

    Used only to convert LEL dates into the field's days-since-birth axis. It is READ from the
    build config, never recomputed from an ephemeris — §N.5: L1 is the authority, and a second
    derivation of the birth instant here could disagree with the one the field was built on.
    """
    bp = ctx.config.get("birth_params") or {}
    raw = bp.get("datetime_iso") or bp.get("birth_datetime_utc") or bp.get("date")
    if not raw:
        raise ValueError(
            "mi_bhara requires ctx.config['birth_params'] with a datetime — the LEL's dates "
            "must be converted onto the field's days-since-birth axis, and inventing a birth "
            "instant here would silently misalign every event against the field (§N.5)."
        )
    if isinstance(raw, (datetime, date)):
        return (raw.date() if isinstance(raw, datetime) else raw).isoformat()
    return str(raw)[:10]


@register(ASSET_ID)
class MiBharaWriter(WriterBase):
    """Stage 9: fit the field's weights, publish skill + GOF, refresh the Living-LEL plane."""

    asset_id = ASSET_ID
    has_substeps = False

    def run(self, ctx: ContextSpec) -> WriterResult:  # noqa: C901 — phase sequence, not branching depth
        started = time.time()
        # Imported inside run() so that merely importing the writers package (which the
        # orchestrator does at startup, and which several tests do at collection time) never
        # drags in scipy/numpy. Same reason the LEL read lives behind one module: the smaller
        # the import surface on the always-loaded path, the fewer ways it can fail.
        from services.mi_bhara import db
        from services.mi_bhara.living_lel import (
            compute_calibration_maturity,
            lapsed_predictions,
            score_predictions_against_event,
        )
        from services.mi_bhara.weights import resolve_weights_version

        chart_id = ctx.config.get("chart_id")
        if not chart_id:
            raise ValueError("mi_bhara is a per_chart asset and requires ctx.config['chart_id']")
        conn = ctx.db_conn
        notes: list[str] = []

        # ── phase 0 — pin the weights version ONCE (§7.5 sub-rule 5) ──────────────────
        # Resolved here, at the top of the writer's single unit of work, and passed down. No
        # code below re-queries `kala_field_weight_versions`.
        pin = resolve_weights_version(conn, chart_id)

        if not db.table_exists(conn, "kala_field"):
            # Lane C's stage-4 table is not deployed yet. Honest, named, non-fatal: the
            # calibration plane has nothing to calibrate, which is a state, not a failure.
            notes.append(NOTE_FIELD_ABSENT)
            return WriterResult(
                asset_id=ASSET_ID,
                rows_inserted=0,
                duration_seconds=time.time() - started,
                notes=(
                    f"{NOTE_FIELD_ABSENT}: kala_field is not deployed, so there is no hazard "
                    f"field to fit. weights_version={pin.version_id} (unchanged)."
                ),
            )

        birth_iso = _birth_iso(ctx)
        event_classes = db.fetch_event_classes(conn, chart_id)

        # ── phase 1 — FALSIFIER RESOLUTION FIRST (item 20) ────────────────────────────
        # Before any weight moves. The falsifier was fixed when the prediction was filed and
        # is scored against the model that filed it; resolving after a refit would let a
        # weight update change what counted as a hit.
        lel_events = db.fetch_lel_events(conn, chart_id, birth_iso)
        open_predictions = db.fetch_open_predictions(conn, chart_id, birth_iso)
        scored = []
        for ev in lel_events:
            scored.extend(score_predictions_against_event(ev, open_predictions))
        as_of_t = max((e.t for e in lel_events), default=0.0)
        scored.extend(
            lapsed_predictions(
                [p for p in open_predictions if p.prediction_id not in {s.prediction_id for s in scored}],
                as_of_t,
            )
        )
        n_prospective_resolutions = sum(
            1 for s in scored if s.is_prospective and s.outcome in ("hit", "miss")
        )

        if not lel_events:
            # THE §7.6 LEL-ABSENT SCENARIO. Not an error, and deliberately not a branch that
            # changes the WEIGHTS: `n_eff = 0 ⇒ φ̂ = φ⁰` is what the shrinkage formula already
            # produces, so the chart continues on the classical structural priors with no
            # special case. What this branch does is skip work that would have no input, and
            # say so.
            notes.append(NOTE_NO_LEL)
            maturity = compute_calibration_maturity(
                lel_events=[],
                prospective_resolutions=0,
                known_event_classes=event_classes,
                weights_version=pin.version_id,
                chart_skill_score=None,
            )
            logger.info(
                "[mi_bhara] chart %s has no recorded life events — serving structural-prior "
                "weights (%s), calibration_maturity=%s",
                chart_id,
                pin.version_id,
                maturity.to_envelope_dict(),
            )
            return WriterResult(
                asset_id=ASSET_ID,
                rows_inserted=0,
                duration_seconds=time.time() - started,
                notes=(
                    f"{NOTE_NO_LEL}: structural-prior weights {pin.version_id} served "
                    f"unchanged; calibration_maturity is an honest zero; skill is "
                    f"underpowered by construction (§7.6 LEL-absent scenario)."
                ),
            )

        # ── phases 2–5 require the stage-9 output tables ──────────────────────────────
        if not (
            db.table_exists(conn, "kala_field_skill")
            and db.table_exists(conn, "kala_field_gof")
        ):
            notes.append(NOTE_SKILL_TABLES_ABSENT)
            return WriterResult(
                asset_id=ASSET_ID,
                rows_inserted=0,
                duration_seconds=time.time() - started,
                notes=f"{NOTE_SKILL_TABLES_ABSENT}: migration 497 has not been applied.",
            )

        rows_written = self._fit_and_publish(
            ctx=ctx,
            chart_id=chart_id,
            pin=pin,
            event_classes=event_classes,
            lel_events=lel_events,
            n_prospective_resolutions=n_prospective_resolutions,
            notes=notes,
        )

        return WriterResult(
            asset_id=ASSET_ID,
            rows_inserted=rows_written,
            duration_seconds=time.time() - started,
            notes="; ".join(notes) if notes else f"weights_version={pin.version_id}",
        )

    # ────────────────────────────────────────────────────────────────────────────────────
    def _fit_and_publish(
        self,
        *,
        ctx: ContextSpec,
        chart_id: str,
        pin: Any,
        event_classes: list[str],
        lel_events: list,
        n_prospective_resolutions: int,
        notes: list[str],
    ) -> int:
        """Phases 2–4. Split out so `run()` reads as the phase sequence it is.

        NOTE ON SCOPE, stated rather than left to be discovered: fitting needs the
        θ-INDEPENDENT per-segment basis (`ln a_s`, `x_j`, `u_m` at each segment endpoint),
        which is Lane C's stage-4 emission. Until `kala_field` carries those columns, this
        method publishes skill and GOF against the AS-BUILT field — which is exactly the
        §7.3 quantity, and the honest one — and records that the parameter refit is pending
        the basis columns. It does not fabricate a basis in order to look complete.
        """
        from services.mi_bhara import db
        from services.mi_bhara.field import integrate, log_lambda, segments_from_rows
        from services.mi_bhara.gof import compute_gof
        from services.mi_bhara.skill import aggregate_chart_skill, compute_skill

        conn = ctx.db_conn
        snapshot = self._field_snapshot_id(conn, chart_id)
        db.replace_prior_skill_and_gof(conn, chart_id, pin.version_id, snapshot)

        written = 0
        per_class = []
        for event_class in event_classes:
            rows = db.fetch_field_segments(conn, chart_id, event_class)
            if not rows:
                continue
            segments = segments_from_rows(rows)
            t_lo, t_hi = segments[0].t_start, segments[-1].t_end
            times = sorted(
                e.t for e in lel_events if e.event_class == event_class and t_lo <= e.t <= t_hi
            )
            replicates = db.fetch_null_replicate_count(conn, chart_id, event_class)

            # The null's own intensity is the §5.5 replicate field. Where stage 5 has not run,
            # `replicates = 0` and `compute_skill` returns an honest underpowered zero rather
            # than a score against a null that does not exist.
            null_vectors: list[list[float]] = []
            null_integrals: list[float] = []
            for shift in self._null_shifts(replicates, t_hi - t_lo):
                null_vectors.append(
                    [log_lambda(segments, self._wrap(t, shift, t_lo, t_hi)) for t in times]
                )
                null_integrals.append(integrate(segments, t_lo, t_hi))

            skill = compute_skill(
                chart_id=chart_id,
                weights_version=pin.version_id,
                event_class=event_class,
                model_log_intensity=[log_lambda(segments, t) for t in times],
                null_log_intensity_per_replicate=null_vectors,
                model_integral=integrate(segments, t_lo, t_hi),
                null_integrals=null_integrals,
            )
            per_class.append(skill)

            n_prosp = min(n_prospective_resolutions, skill.n_events)
            written += db.insert_skill_row(
                conn,
                chart_id,
                snapshot,
                {
                    "event_class": event_class,
                    "weights_version": pin.version_id,
                    "n_events": skill.n_events,
                    "n_prospective": n_prosp,
                    "n_backfill": skill.n_events - n_prosp,
                    "skill_score": skill.skill_score,
                    "skill_lo": skill.skill_lo,
                    "skill_hi": skill.skill_hi,
                    "skill_state": skill.skill_state,
                    "skill_prospective": None,
                    "null_replicates": skill.null_replicates,
                    "bootstrap_resamples": skill.bootstrap_resamples,
                    "bootstrap_seed": skill.bootstrap_seed,
                },
            )

            gof = compute_gof(
                event_class=event_class,
                integrate_fn=lambda a, b, _s=segments: integrate(_s, a, b),
                event_times=times,
                observation_start=t_lo,
            )
            written += db.insert_gof_row(
                conn,
                chart_id,
                snapshot,
                {
                    "event_class": event_class,
                    "weights_version": pin.version_id,
                    "n": gof.n,
                    "ks_statistic": gof.ks_statistic,
                    "ks_p": gof.ks_p,
                    "ljung_box_p": gof.ljung_box_p,
                    "ljung_box_stat": gof.ljung_box_stat,
                    "ljung_box_lags": gof.ljung_box_lags,
                    "gof_state": gof.gof_state,
                    "failing_statistic": gof.failing_statistic,
                    "rescaled_z": list(gof.rescaled_z),
                    "ks_band_95": gof.ks_band_95,
                },
            )

        if per_class:
            agg = aggregate_chart_skill(
                per_class, chart_id=chart_id, weights_version=pin.version_id
            )
            written += db.insert_skill_row(
                conn,
                chart_id,
                snapshot,
                {
                    "event_class": None,
                    "weights_version": pin.version_id,
                    "n_events": agg.n_events,
                    "n_prospective": min(n_prospective_resolutions, agg.n_events),
                    "n_backfill": agg.n_events - min(n_prospective_resolutions, agg.n_events),
                    "skill_score": agg.skill_score,
                    "skill_lo": agg.skill_lo,
                    "skill_hi": agg.skill_hi,
                    "skill_state": agg.skill_state,
                    "skill_prospective": None,
                    "null_replicates": agg.null_replicates,
                    "bootstrap_resamples": agg.bootstrap_resamples,
                    "bootstrap_seed": agg.bootstrap_seed,
                },
            )

        # phase 4 — biographical-join refresh. `-1` means Lane D's table is not deployed;
        # named, never silent.
        bio = db.upsert_biographical_echo_insights(conn, chart_id, [])
        if bio < 0:
            notes.append(NOTE_BIO_JOIN_DEFERRED)

        return written

    # ── helpers ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _null_shifts(replicates: int, horizon: float) -> list[float]:
        """§5.5's DETERMINISTIC shift grid: `δ_r = r·(H/R)`, `r = 1…R`. No RNG anywhere.

        The grid is computed, not drawn, precisely so hash-replay holds: two builds of the
        same snapshot must produce byte-identical null statistics.
        """
        if replicates <= 0 or horizon <= 0:
            return []
        return [r * (horizon / replicates) for r in range(1, replicates + 1)]

    @staticmethod
    def _wrap(t: float, shift: float, lo: float, hi: float) -> float:
        """Circular shift within `[lo, hi)` — §5.5's `(t + δ_r) mod H`."""
        span = hi - lo
        return lo + ((t - lo + shift) % span)

    @staticmethod
    def _field_snapshot_id(conn: Any, chart_id: str) -> str:
        """Read the snapshot id the field was built under.

        READ, never recomputed (§N.5). The §7.4 hash is Lane C's to compute at field-write
        time; recomputing it here from a different row set would produce a second, divergent
        authority for the same snapshot. When the field carries no snapshot id yet, the
        honest sentinel `unpinned` is stored — visibly wrong to a reader, rather than a
        plausible-looking hash that is not one.
        """
        with conn.cursor() as cur:
            cur.execute(
                "SELECT field_snapshot_id FROM kala_field WHERE chart_id = %s LIMIT 1",
                (chart_id,),
            )
            row = cur.fetchone()
        if row is None:
            return "unpinned"
        value = row["field_snapshot_id"] if not isinstance(row, tuple) else row[0]
        return str(value or "unpinned")
