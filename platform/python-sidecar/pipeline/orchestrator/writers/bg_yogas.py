"""
bg_yogas writer — populates brahma_yoga_catalog, brahma_ontology (yoga class),
and reference_yogas with classical yoga definitions.

Source data: brahmagyan.l0_yogas — 144 inline core yogas + 4 governed
detector-registry yogas + corpus-verse structured extraction from
classical_text_chunks (Saravali/BPHS/Phaladeepika).

Per holistic design v1.1: ZERO LLM use.
Floor policy (Tier 1 campaign 2026-06-09): target_floor set to ACHIEVED count.
"""
from __future__ import annotations

import logging
import time

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_yogas import seed_yogas

logger = logging.getLogger(__name__)


@register('bg_yogas')
class YogasWriter(WriterBase):
    asset_id = 'bg_yogas'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        counts = seed_yogas(
            ctx.db_conn,
            build_id=ctx.build_id,
            dry_run=ctx.dry_run,
            autocommit=False,  # caller (asset_runner) owns the transaction boundary
        )
        catalog_inserted = counts.get("catalog_inserted", 0)
        ontology_inserted = counts.get("ontology_inserted", 0)
        ref_inserted = counts.get("ref_inserted", 0)
        source_links_inserted = counts.get("source_links_inserted", 0)
        total_inserted = (
            catalog_inserted + ontology_inserted + ref_inserted + source_links_inserted
        )
        warnings = counts.get("warnings", [])
        notes = (
            f"brahma_yoga_catalog: {catalog_inserted} rows "
            f"(inline={counts.get('inline_count', 0)}, "
            f"detector={counts.get('detector_count', 0)}, "
            f"extracted={counts.get('extracted_count', 0)}); "
            f"ontology={ontology_inserted}; "
            f"ref={ref_inserted}; source_links={source_links_inserted}; "
            f"total_owned={total_inserted}; "
            f"replaced={counts.get('catalog_replaced', 0)}/"
            f"{counts.get('ontology_replaced', 0)}/"
            f"{counts.get('ref_replaced', 0)}"
        )
        if warnings:
            notes += f"; WARNINGS({len(warnings)}): {warnings[:3]}"
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total_inserted,
            duration_seconds=time.time() - t0,
            notes=notes,
        )
