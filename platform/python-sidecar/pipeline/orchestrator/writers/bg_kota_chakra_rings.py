"""
bg_kota_chakra_rings writer — populates the bg_kota_chakra_rings L0 reference
table (27 rows: the Kota-Chakra fort-chakra ring partition).

ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md): moves the ring
partition out of services/ka_kota_chakra/logic.py's inline dict into this
versioned L0 asset. See brahmagyan.l0_kota_chakra_rings for the full
disclosure (citation tier, row-count note, versioning discipline) and the
byte-identity proof (tests/l3/test_ka_kota_chakra.py).

L0 global asset. ON CONFLICT DO UPDATE idempotency (no chart_id), per §N.3.
§N.2: Frozen orchestrator contract — run(ctx) → WriterResult, never commits.

depends_on: [] — pure reference data, no upstream dependency.
Downstream: ka_kota_chakra (L3 Kāla) depends on this asset.
"""
from __future__ import annotations

import logging
import time

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_kota_chakra_rings import seed_kota_chakra_rings

logger = logging.getLogger(__name__)


@register('bg_kota_chakra_rings')
class KotaChakraRingsWriter(WriterBase):
    asset_id = 'bg_kota_chakra_rings'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        counts = seed_kota_chakra_rings(
            ctx.db_conn,
            build_id=ctx.build_id,
            dry_run=ctx.dry_run,
            autocommit=False,
        )
        total = counts.get("bg_kota_chakra_rings", 0)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total,
            duration_seconds=time.time() - t0,
            notes=f"bg_kota_chakra_rings: {total} rows (27-position ring partition, "
                  "tier-(iii) secondary-source citation, ADJUDICATION-9)",
        )
