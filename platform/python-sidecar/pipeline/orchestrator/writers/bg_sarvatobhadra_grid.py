"""
bg_sarvatobhadra_grid writer (TI-L0-20, SS Q21) - asserts and REPORTS the ruled empty state; it deletes NOTHING.

ADJUDICATION-11 (migration 529): the table is DELIBERATELY EMPTY. An empty school-keyed table honestly states that Sarvatobhadra-chakra
grid variants exist and none is currently held or selected, rather than seating one tradition's grid as an unqualified L0 fact (a B.1
violation). This writer makes Build measurable (a dispatchable writer) without seeding anything: it inserts no row.

PROTECTION (SS N-113 b + independent review L0C LOW): the table is the activation path for a native-approved, source-verified school's
grid (migration 529) - rows that land in it are human-entered or human-staged (N-46). `native_confirmed = TRUE` rows are never deleted
(SS-confirmed). Staged rows (`native_confirmed = FALSE`) are ALSO never deleted: the first version of this writer deleted them on every
rebuild, which would silently destroy a half-entered grid. The writer therefore has NO writer-owned partition and removes nothing; it
reports the table's state in the build notes ({total, native_confirmed, staged}) so the departure from the ruled empty state is
visible rather than overwritten. (To restore the stricter first behaviour for staged rows, re-add the single DELETE ... WHERE
native_confirmed IS NOT TRUE; SS to rule.)

Build.completion: the writer reports rows_written = 0 (it writes none). While the table is empty that equals the live count (0). If a
human later seats rows, live count > 0 against rows_written = 0: the CF-01 changed-rows convention (a converged rerun with rows_written = 0
reads PASS when count_integrity passes) is the declared reading for such an asset; scoping count_sql to a writer-owned partition is not
possible because there is none. Recorded in the wave plan; not hidden.
"""
from __future__ import annotations

import time

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult


@register('bg_sarvatobhadra_grid')
class SarvatobhadraGridWriter(WriterBase):
    asset_id = 'bg_sarvatobhadra_grid'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        if ctx.dry_run:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0, notes='dry_run: would report the ruled empty state')
        with ctx.db_conn.cursor() as cur:
            cur.execute("SELECT count(*) AS total, count(*) FILTER (WHERE native_confirmed IS TRUE) AS confirmed FROM bg_sarvatobhadra_grid")
            row = cur.fetchone()
            total, confirmed = (row['total'], row['confirmed']) if isinstance(row, dict) else (row[0], row[1])
        staged = total - confirmed
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=0,
            duration_seconds=time.time() - t0,
            notes=(f'ADJUDICATION-11 ruled empty state reported: {total} row(s) in the table '
                   f'({confirmed} native-confirmed, {staged} staged); 0 inserted, 0 deleted'
                   + ('' if total == 0 else ' - the table is NOT in the ruled empty state (human-entered rows are preserved untouched)')),
        )
