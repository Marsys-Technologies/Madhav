"""
bg_class_lifetime_counts writer — N_e structural priors for the Kāla Kṣetra field.

ṢAḌ-DARŚANA W2 · lane `l0-ne-priors` · governing ruling:
`00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md` § ADJUDICATION-2 item 3.

Writes `brahma_class_priors` rows at the RESERVED COORDINATE that
`services/ka_kshetra/stage4_field.py::load_class_lifetime_count` reads:

    fact_kind         = 'lifetime_count_per_100y'
    signal_type_class = <brahma_event_ontology.event_class_id>
    source_subsystem  = '*'
    signal_tradition  = '*'
    prior_version     = 'ne_v01'   (ZERO-PADDED — see l0_class_lifetime_counts)

Source data: `brahmagyan.l0_class_lifetime_counts` — a literal, reviewable table of
Tier N-i published demographic statistics, each carrying all six citation elements
plus its conversion arithmetic.

§N.2: FROZEN orchestrator contract — `@register`, `WriterBase`, `run(ctx) ->
      WriterResult`, runs on `ctx.db_conn` and NEVER commits or closes it, never
      writes `asset_throughput`.
§N.3: L0 idempotency — ON CONFLICT DO UPDATE (global reference data, not per-chart).

── WHAT THIS WRITER DELIBERATELY DOES NOT DO (§N.8) ─────────────────────────────
It does not floor, clamp, interpolate, or default any value. A class absent from the
seed module is absent from the table, and `require_baseline` then raises
`ClassSkipped(e, 'no_class_prior_row')` for it — the honest per-class skip
ADJUDICATION-2 designates as a shippable outcome. `CHECK (class_prior > 0)` is
respected by NOT SEEDING, never by flooring to epsilon.
"""
from __future__ import annotations

import logging
import time

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_class_lifetime_counts import seed_class_lifetime_counts

logger = logging.getLogger(__name__)


@register('bg_class_lifetime_counts')
class ClassLifetimeCountsWriter(WriterBase):
    asset_id = 'bg_class_lifetime_counts'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        counts = seed_class_lifetime_counts(
            ctx.db_conn,
            build_id=ctx.build_id,
            dry_run=ctx.dry_run,
            autocommit=False,
        )
        total = counts.get('brahma_class_priors', 0)
        skipped = counts.get('classes_not_seeded', 0)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total,
            duration_seconds=time.time() - t0,
            notes=(
                f'brahma_class_priors @ fact_kind=lifetime_count_per_100y: {total} rows '
                f'(prior_version=ne_v01). {skipped} ontology class(es) NOT seeded — no '
                f'Tier N-i source; ka_kshetra skips each honestly with no_class_prior_row.'
            ),
        )
