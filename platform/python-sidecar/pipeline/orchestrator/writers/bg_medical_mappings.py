"""
bg_medical_mappings writer — seeds bg_medical_mappings and bg_nakshatra_medical.

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


@register('bg_medical_mappings')
class BgMedicalMappingsWriter(WriterBase):
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
        total = sum(counts.values())
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total,
            duration_seconds=time.time() - t0,
            notes=f'2 medical reference tables: {counts}',
        )
