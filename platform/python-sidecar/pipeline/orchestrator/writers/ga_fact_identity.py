"""Orchestrator writer for the L1 Gaṇita `ga_fact_identity` asset (light): the Fact Identity Index.

`chart_fact_identity` (migration 552) is a pure derived cache: every column is a function of ONE
`chart_facts` row, parsed by the single deterministic parser `brahmagyan/fact_identity_parser.py`.
Its `fact_id` is a FOREIGN KEY ... ON DELETE CASCADE to `chart_facts`, so any ga_* delete-then-insert
of `chart_facts` rows silently empties the index for the replaced facts. Until migration 1333 nothing
rebuilt it (it was filled only by the hand-run script G-IDX), which is exactly how the canonical
chart's index was emptied by a forced rebuild (FACTID_RESTORE, 2026-10-07).

This writer closes that: it is a REAL registered asset that depends on every ga_* asset that writes
`chart_facts`, so it runs after all of them and re-derives the chart's index from the facts as they
stand at that moment. The FK cascade is deliberately kept (it is what stops stale rows from pointing at
facts that no longer exist).

Contract (CLAUDE.md N.2, FROZEN, unchanged): `@register`, `WriterBase`, light `run(ctx) -> WriterResult`,
runs on `ctx.db_conn` and NEVER commits / rolls back / closes it, does not write `asset_throughput`,
`chart_id` comes from `ctx.config`. Idempotency (N.3): per-chart delete-then-insert inside
`build_index_for_chart`. Deterministic-first: no LLM, no clock-dependent value in the row content
(`computed_at` is the DB `now()`).

The corrected G-IDX check (`brahmagyan/fact_identity_check.check_identity_index`) runs INSIDE `run()`
and is FATAL here, the equivalent of the script's `--check`: if any clause FAILS the writer raises, the
orchestrator rolls the sub-step's savepoint back, and the prior index (and thus the chart's prior
state) is left untouched. NOT_EVALUATED clauses (only `rows_equal_parsed` in a dry-run, where nothing is
written) never count as a pass and never as a failure.

`ctx.config['fact_identity_reasons_mode']` selects the identity_free reason-set rule: `'subset'`
(DEFAULT, SS N-232: observed reasons <= the 14 measured + scope_cap_sentinel; a chart may lack a known reason such as scope_cap_sentinel) or `'exact'`
(observed == allowed). A NEW reason fails in both.

This adapter is NOT decorated with `@l1_producer_contract`: that boundary belongs to the 19 writers
that PRODUCE L1 data-plane generations (`CONTRACTED_L1_ASSETS`); this asset derives an index from
them and produces no generation partition.
"""
from __future__ import annotations

import time

from . import register, WriterBase, ContextSpec, WriterResult

_REASONS_MODES = ('exact', 'subset')


@register('ga_fact_identity')
class GaFactIdentityWriter(WriterBase):
    asset_id = 'ga_fact_identity'
    source_paths = [
        'platform/python-sidecar/pipeline/orchestrator/writers/ga_fact_identity.py',
        'platform/python-sidecar/brahmagyan/fact_identity_index.py',
        'platform/python-sidecar/brahmagyan/fact_identity_check.py',
        'platform/python-sidecar/brahmagyan/fact_identity_parser.py',
    ]

    def run(self, ctx: ContextSpec) -> WriterResult:
        from brahmagyan.fact_identity_check import check_identity_index
        from brahmagyan.fact_identity_index import build_index_for_chart

        t0 = time.time()
        chart_id = str(ctx.config['chart_id'])
        # DEFAULT 'subset' (SS N-232): charts 1c826d5a and cb73cd3d lack the scope_cap_sentinel reason, and a MISSING known reason cannot empty or
        # half-fill the table; every other check stays fatal (rows==parsed, gap==0, partition sum, coverage) and a NEW unexpected reason still fails.
        mode = ctx.config.get('fact_identity_reasons_mode', 'subset')
        if mode not in _REASONS_MODES:
            raise ValueError(
                f"ga_fact_identity: fact_identity_reasons_mode must be one of {_REASONS_MODES}, got {mode!r}")

        summary = build_index_for_chart(ctx.db_conn, chart_id, dry_run=ctx.dry_run)
        result = check_identity_index(summary, exact_reasons=(mode == 'exact'))
        if result.failed:
            # Raise (never commit/rollback here): the orchestrator owns the savepoint and rolls the
            # delete-then-insert back, so a failed check leaves the prior index untouched.
            raise RuntimeError(
                f"ga_fact_identity: corrected G-IDX check FAILED for chart {chart_id} "
                f"({', '.join(i.name for i in result.failed)}); sub-step rolled back, nothing written.\n"
                f"{result.render()}\n"
                f"gap_examples={dict(list(summary['gap_examples'].items())[:10])}"
            )

        rows = int(summary['rows_in_table'] or 0)
        notes = (f"total_facts={summary['total_facts']} parsed={summary['parsed']} "
                 f"identity_free={summary['identity_free']} gap={summary['gap']} "
                 f"deleted_prior_rows={summary['deleted_prior_rows']} mode={mode}"
                 + (' (dry-run: nothing written)' if ctx.dry_run else ''))
        return WriterResult(asset_id=self.asset_id, rows_inserted=rows, notes=notes,
                            duration_seconds=round(time.time() - t0, 3))
