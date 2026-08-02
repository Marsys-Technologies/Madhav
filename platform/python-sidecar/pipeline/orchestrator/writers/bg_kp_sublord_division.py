"""
bg_kp_sublord_division writer — populates the canonical 249-fold KP sub-lord
division of the sidereal zodiac.

ṢAḌ-DARŚANA W3K Lane 1 · ANTARYĀMIN ADJUDICATION-7 Part 1.

See `brahmagyan.l0_kp_sublord_division` for the full disclosure: the derivation
(R1 Vimśottarī proportional sub-division + R2 rāśi cut → 243 + 6 = 249), the
citation tier, the sub-sub/pāda scope disclosure, and the star-lord cross-check.

L0 global asset. ON CONFLICT DO UPDATE idempotency (no chart_id), per §N.3.
Stored in SIDEREAL longitude space with NO ayanamsha key — the division of the
sidereal circle is ayanāṃśa-invariant (ADJUDICATION-7's binding sub-ruling); the
ayanāṃśa enters only when a chart's longitude is projected into it, which is an
L1 (`ga_nakshatra`) concern, not this table's.

§N.2: FROZEN orchestrator contract — run(ctx) -> WriterResult, runs on
ctx.db_conn and never commits or closes it.

depends_on: [] — pure reference geometry, no upstream dependency. (The star-lord
cross-check READS `reference_nakshatra` when present, but does not require it:
an absent reference table yields an honest `unverified` status, never a pass.)
Downstream: `ga_nakshatra` (L1 natal KP projection + KP significators).
"""
from __future__ import annotations

import logging
import time

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_kp_sublord_division import seed_kp_sublord_division, TABLE_VERSION

logger = logging.getLogger(__name__)


@register('bg_kp_sublord_division')
class KpSublordDivisionWriter(WriterBase):
    asset_id = 'bg_kp_sublord_division'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        counts = seed_kp_sublord_division(ctx.db_conn, dry_run=ctx.dry_run, autocommit=False)
        total = counts.get("bg_kp_sublord_division", 0)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total,
            duration_seconds=time.time() - t0,
            notes=(
                f"bg_kp_sublord_division: {total} divisions "
                f"(version={TABLE_VERSION}; 243 Vimshottari sub segments + 6 rashi-boundary "
                "splits = 249, derived not asserted; ADJUDICATION-7 Part 1)"
            ),
        )
