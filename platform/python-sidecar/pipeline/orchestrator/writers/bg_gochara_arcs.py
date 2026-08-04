"""bg_gochara_arcs writer — W2G's chart-independent monotone-arc substrate.

ṢAḌ-DARŚANA wave W2G (GOCHARA-2.0, item 19). Builds the global
`bg_gochara_arcs` table: every graha's longitude history over the stored
ephemeris epoch, decomposed into arcs on which longitude is strictly monotone
and confined to one 360° band. See migration 538's header for the full
architectural account and the live measured row counts.

WHY THIS IS AN L0 (bg_*) ASSET AND NOT AN L3 ONE. When Saturn reaches 123.45°
does not depend on anybody's birth data. The century of arcs is therefore
computed ONCE, globally, and every chart joins the same rows — which is what
makes W2G the production-scalability keystone rather than a faster sweep.

FROZEN ORCHESTRATOR CONTRACT (§N.2), conformed to, not extended:
  * `@register('bg_gochara_arcs')` on a `WriterBase` subclass;
  * HEAVY shape — `plan_substeps` (one substep per body, 9) + `run_substep`,
    so each body is its own savepoint + heartbeat and a crash resumes at the
    failed body rather than at the start;
  * runs on `ctx.db_conn` and NEVER commits or closes it;
  * never writes `asset_throughput` — the orchestrator is the sole build-state
    writer;
  * no orchestrator change of any kind is required or proposed.

IDEMPOTENCY. DELETE-then-INSERT scoped to (substrate_version × body) — §N.3's
"a rebuild REPLACES, never accretes", applied to a DERIVED global asset where a
bare upsert would strand orphan arcs from a longer previous run. The scope is
exactly one substep, so a crash cannot half-replace a body.

NIRMĀṆA (brief §2.5). Global asset, `scope='global'`, built only via an
explicit super-admin L0 trigger — never auto-pulled into a per-chart build. Its
`asset_registry` seed row lands in the same PR as this file (§2.5.1).

UNTOUCHABLES. This writer never reads or writes `kala_gochara_windows`, and
never writes `build_substep_progress`.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from pipeline.orchestrator.writers import (
    ContextSpec,
    SubStep,
    WriterBase,
    WriterResult,
    register,
)
from services.w2g import (
    ARC_ENGINE_VERSION,
    arc_fingerprint,
    build_arcs_for_body,
)
from services.w2g.db_source import AYANAMSHA_ID

logger = logging.getLogger(__name__)

# The nine bodies `brahmagyan.l0_ephemeris.DAILY_BODIES` stores. Listed slowest
# first so the cheap, high-value Tier-A bodies land before the expensive ones if
# a build is cut short — the arcs that DO land are then the ones the eager tier
# needs (ADJUDICATION-14).
BODIES: tuple[str, ...] = (
    "Saturn", "Jupiter", "Rahu", "Ketu", "Mars",
    "Sun", "Mercury", "Venus", "Moon",
)

# Zero-padded per the ne_vNN / kota_chakra_rings_vNN precedent: a bare `v10`
# string-sorts below `v2`. A revision is a NEW version's row set, never an
# in-place edit of an existing one.
SUBSTRATE_VERSION = "arcs_v01"

TABLE = "bg_gochara_arcs"
INSERT_BATCH = 2000

INSERT_SQL = f"""
    INSERT INTO {TABLE}
      (substrate_version, body, arc_index, start_jd, end_jd,
       start_lon_unwrapped_deg, end_lon_unwrapped_deg,
       lon_lo_deg, lon_hi_deg, direction, wrap_index,
       arc_fingerprint, engine_version, ayanamsha_id, build_id, computed_at)
    VALUES
      (%(substrate_version)s, %(body)s, %(arc_index)s, %(start_jd)s, %(end_jd)s,
       %(start_lon_unwrapped_deg)s, %(end_lon_unwrapped_deg)s,
       %(lon_lo_deg)s, %(lon_hi_deg)s, %(direction)s, %(wrap_index)s,
       %(arc_fingerprint)s, %(engine_version)s, %(ayanamsha_id)s, %(build_id)s, NOW())
"""


@register('bg_gochara_arcs')
class GocharaArcsWriter(WriterBase):
    asset_id = 'bg_gochara_arcs'
    has_substeps = True

    # ── FROZEN CONTRACT: plan_substeps + run_substep ─────────────────────────

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        bodies = tuple(ctx.config.get("bodies") or BODIES)
        return [SubStep(key=body, label=f"arcs: {body}") for body in bodies]

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        t0 = time.time()
        body = step.key
        substrate_version = str(ctx.config.get("substrate_version") or SUBSTRATE_VERSION)
        start_date = ctx.config.get("start_date")
        end_date = ctx.config.get("end_date")

        def query(sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
            cur = ctx.db_conn.execute(sql, params or [])
            rows = cur.fetchall()
            return [dict(r) if not isinstance(r, dict) else r for r in rows]

        arcs, knot_count = build_arcs_for_body(query, body, start_date, end_date)
        if not arcs:
            # Unreachable given build_arcs_for_body's own honest raise on too
            # few knots, but stated rather than assumed: an empty arc set is a
            # silently-dropped body, never a successful build.
            raise ValueError(
                f"{body}: arc decomposition produced zero arcs from {knot_count} knots"
            )

        fingerprint = arc_fingerprint(
            body=body,
            epoch_start_jd=arcs[0].start_jd,
            epoch_end_jd=arcs[-1].end_jd,
            knot_count=knot_count,
            engine_version=ARC_ENGINE_VERSION,
        )

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                rows_skipped=len(arcs),
                duration_seconds=time.time() - t0,
                notes=(
                    f"DRY RUN {body}: {len(arcs)} arcs from {knot_count} knots "
                    f"(fingerprint {fingerprint}, {substrate_version}) — nothing written"
                ),
            )

        # §N.3 replace-not-accrete, scoped to exactly this substep's key.
        ctx.db_conn.execute(
            f"DELETE FROM {TABLE} WHERE substrate_version = %s AND body = %s",
            [substrate_version, body],
        )

        rows = [
            {
                "substrate_version": substrate_version,
                "arc_fingerprint": fingerprint,
                "engine_version": ARC_ENGINE_VERSION,
                "ayanamsha_id": AYANAMSHA_ID,
                "build_id": ctx.build_id,
                **arc.as_row(),
            }
            for arc in arcs
        ]

        inserted = 0
        with ctx.db_conn.cursor() as cur:
            for offset in range(0, len(rows), INSERT_BATCH):
                batch = rows[offset:offset + INSERT_BATCH]
                cur.executemany(INSERT_SQL, batch)
                inserted += len(batch)
                if offset and offset % (INSERT_BATCH * 5) == 0:
                    logger.info(
                        "[bg_gochara_arcs] %s: %d/%d arcs inserted", body, inserted, len(rows)
                    )

        retrograde = sum(1 for a in arcs if a.direction == -1)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=inserted,
            duration_seconds=time.time() - t0,
            notes=(
                f"{body}: {inserted} monotone arcs ({retrograde} retrograde) from "
                f"{knot_count} ephemeris knots; substrate_version={substrate_version}, "
                f"arc_fingerprint={fingerprint}, engine={ARC_ENGINE_VERSION}"
            ),
        )

    def run(self, ctx: ContextSpec) -> WriterResult:
        """CLI / direct-use path: drive this writer's own substeps.

        The orchestrator normally drives them itself (savepoint + heartbeat per
        body); this exists so a standalone run is possible, exactly as the
        frozen contract's heavy-writer shape intends.
        """
        t0 = time.time()
        total = 0
        notes: list[str] = []
        for step in self.plan_substeps(ctx):
            result = self.run_substep(ctx, step)
            total += result.rows_inserted
            notes.append(result.notes)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total,
            duration_seconds=time.time() - t0,
            notes=" | ".join(notes),
        )


__all__ = ["BODIES", "SUBSTRATE_VERSION", "GocharaArcsWriter"]
