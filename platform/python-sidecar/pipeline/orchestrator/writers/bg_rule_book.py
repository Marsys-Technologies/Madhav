"""
bg_rule_book writer — the L0 rule-book store (Rule Book engine, packet E2).

AUTHORITY: OWNER-APPROVAL-ENGINE-NATIVE-ITEMS-20261028 item (1); ENGINE_PLAN_v0_2
§1. Tables, freeze trigger and asset_registry row: migration 1413. All logic
lives in brahmagyan.l0_rule_book; this module is the registered adapter.

FROZEN ORCHESTRATOR CONTRACT (§N.2), conformed to, not extended:
  * ``@register('bg_rule_book')`` on a ``WriterBase`` subclass, discovered by
    ``_auto_discover()`` — no orchestrator file is edited;
  * LIGHT shape: ``run(ctx) -> WriterResult``;
  * runs on ``ctx.db_conn`` and NEVER commits, rolls back or closes it;
  * never writes ``asset_throughput``;
  * L0 is chart-agnostic: ``ctx.config['chart_id']`` / ``birth_params`` are
    never read.

Writer-specific config (``ctx.config``, all optional):
  * ``rule_book_manifest`` — path to a version manifest (default
    brahmagyan/rule_book/rule_book_manifest.json, not committed yet);
  * ``rule_book_allow_fixture`` — True only in tests; a FIXTURE version is
    refused otherwise, and the DB forbids a FIXTURE version from becoming current.

Idempotency (§N.3, L0): ON CONFLICT DO UPDATE on (rulebook_version, card_id)
while the version is unfrozen; the version's class rows are replaced and cards
dropped from the manifest are deleted. A FROZEN version raises
RuleBookFrozenError before any write (and the migration-1413 trigger refuses
any write that slips past).
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

from pipeline.orchestrator.writers import ContextSpec, WriterBase, WriterResult, register
from brahmagyan.l0_rule_book import seed_rule_book

logger = logging.getLogger(__name__)


@register('bg_rule_book')
class RuleBookWriter(WriterBase):
    asset_id = 'bg_rule_book'
    has_substeps = False

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        cfg = ctx.config or {}
        manifest = cfg.get('rule_book_manifest')
        src, counts = seed_rule_book(
            ctx.db_conn,
            manifest_path=Path(manifest) if manifest else None,
            build_id=ctx.build_id,
            dry_run=ctx.dry_run,
            allow_fixture=cfg.get('rule_book_allow_fixture') is True,
        )
        by_status: dict[str, int] = {}
        for r in src.rows:
            by_status[r.status] = by_status.get(r.status, 0) + 1
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=counts['inserted'],
            rows_updated=counts['updated'],
            duration_seconds=time.time() - t0,
            notes=(
                f"rule book {src.rulebook_version} (manifest {src.manifest_sha256[:12]}): "
                f"{len(src.rows)} cards {dict(sorted(by_status.items()))}, "
                f"{counts['class_rows']} class rows, {counts['deleted']} dropped"
                + (" [dry run]" if ctx.dry_run else "")
            ),
        )
