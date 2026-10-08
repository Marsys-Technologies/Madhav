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
        total = sum(counts.values())
        # WFIX-A: rows PRESENT in the asset being built's own produced tables. The seeder's sum was
        # reported verbatim for all three registered ids, so bg_sign_medical recorded 60 against its
        # own 12 rows. ctx.asset_id names the registered id this run was started for: the primary
        # declares all three tables (bg_medical_mappings 21 + bg_nakshatra_medical 27 + bg_sign_medical
        # 12 = 60), each sibling only its own.
        present = total
        if not ctx.dry_run:
            from pipeline.orchestrator.writers._rows_present import present_count
            with ctx.db_conn.cursor() as cur:
                if ctx.asset_id == 'bg_sign_medical':
                    cur.execute(ROWS_PRESENT_SQL_SIGN)
                elif ctx.asset_id == 'bg_nakshatra_medical':
                    cur.execute(ROWS_PRESENT_SQL_NAKSHATRA)
                else:
                    cur.execute(ROWS_PRESENT_SQL_PRIMARY)
                present = present_count(cur.fetchone())
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=present,
            duration_seconds=time.time() - t0,
            notes=f'medical reference tables: {counts}; present for {ctx.asset_id}: {present}',
        )


# WFIX-A: the rows-present statement is a literal at the module end (resolved at call time) so no line above it shifts and
# the writer-line citations in the declarations keep pointing at the same code; the census scans it as the asset's own read.
ROWS_PRESENT_SQL_PRIMARY = (
    "SELECT (SELECT count(*) FROM bg_medical_mappings) + (SELECT count(*) FROM bg_nakshatra_medical)"
    " + (SELECT count(*) FROM bg_sign_medical) AS n"
)
ROWS_PRESENT_SQL_NAKSHATRA = "SELECT count(*) AS n FROM bg_nakshatra_medical"
ROWS_PRESENT_SQL_SIGN = "SELECT count(*) AS n FROM bg_sign_medical"
