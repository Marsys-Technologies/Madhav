"""
bg_medical_mappings writer — seeds bg_medical_mappings, bg_nakshatra_medical and bg_sign_medical.

L0 brahmagyan light writer. Delegates to brahmagyan.l0_medical.seed_medical_mappings()
for all INSERT logic. ON CONFLICT DO UPDATE idempotency (L0 standard per §N.3).

ZERO LLM use. ZERO computed values. Pure deterministic data from classical texts
(BPHS Ch.18, Ashtanga Hridayam, Charaka Samhita).

MEDICAL DISCLAIMER: This writer seeds Jyotish reference data only.
All ga_medical rows built from this reference carry indication_tier='jyotish_indication'
and not_diagnosis=TRUE. NOT a medical diagnostic system.
"""
from __future__ import annotations

import logging
import time

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_medical import seed_medical_mappings

logger = logging.getLogger(__name__)


@register('bg_sign_medical')       # sub-table seeded by this writer (WP-2.5 / LCA-16 Kalapurusha)
@register('bg_nakshatra_medical')  # sub-table seeded by this writer (see class docstring)
@register('bg_medical_mappings')
class BgMedicalMappingsWriter(WriterBase):
    """
    Seeds bg_medical_mappings (9 graha rows), bg_nakshatra_medical (27 nakshatra rows)
    AND bg_sign_medical (12 Kalapurusha sign→body-part rows, WP-2.5 / LCA-16).

    bg_nakshatra_medical and bg_sign_medical are sub-tables of this writer's build scope —
    they have no independent writer. The @register decorators above ensure the orchestrator
    marks those assets built when this writer runs successfully.
    """
    asset_id = 'bg_medical_mappings'
    source_paths = ['platform/python-sidecar/brahmagyan/l0_medical.py']

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        # autocommit=False: orchestrator owns the transaction boundary
        counts = seed_medical_mappings(
            conn=ctx.db_conn,
            build_id=ctx.build_id,
            dry_run=ctx.dry_run,
            autocommit=False,
        )
        # TI-L0-32 (CF-02): this class is registered for THREE asset ids and writes three tables
        # every time. The build record's `rows_written` must be the partition of the asset that was
        # dispatched (counts[ctx.asset_id]), not the sum of all three (60 = 21 + 27 + 12) against a
        # count_sql that sees 21. Record-only: no row, no table, no seed changes. An id this class is
        # not registered for is a wiring defect and fails loudly rather than reporting a total.
        if ctx.asset_id not in counts and not ctx.dry_run:
            raise RuntimeError(
                f'bg_medical_mappings writer dispatched as {ctx.asset_id!r}; it owns '
                f'{sorted(counts)} - refusing to report another asset\'s total'
            )
        total = sum(counts.values())
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=counts.get(ctx.asset_id, 0),
            duration_seconds=time.time() - t0,
            notes=(f'3 medical reference tables written (shared writer): {counts}; '
                   f'rows_written reports the dispatched asset {ctx.asset_id!r} = {counts.get(ctx.asset_id, 0)} '
                   f'of {total} total'),
        )
