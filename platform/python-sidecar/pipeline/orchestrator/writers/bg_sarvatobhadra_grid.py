"""
bg_sarvatobhadra_grid writer (TI-L0-20, SS Q21) - asserts the RULED EMPTY STATE.

ADJUDICATION-11 (migration 529): the table is DELIBERATELY EMPTY. An empty school-keyed table
honestly states that Sarvatobhadra-chakra grid variants exist and none is currently held or
selected, rather than seating one tradition's grid as an unqualified L0 fact (a B.1 violation).
This writer makes Build measurable (a dispatchable writer, count_sql expecting 0) without seeding
anything: delete-then-insert of NOTHING.

The one deliberate deviation from a literal "delete everything": rows with native_confirmed = TRUE
are NEVER deleted. The activation path migration 529 documents is "a native-approved,
source-verified school's grid lands in the table with zero code change"; a writer that wiped
those rows on the next rebuild would destroy exactly the native-entered data the table exists to
receive (N-46). Such rows are preserved and reported; the writer-owned partition is the rows that
are NOT native-confirmed, and that partition is asserted empty. SS to confirm this scoping of Q21.
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
            return WriterResult(asset_id=self.asset_id, rows_inserted=0, notes='dry_run: would assert the ruled empty state')
        with ctx.db_conn.cursor() as cur:
            cur.execute("DELETE FROM bg_sarvatobhadra_grid WHERE native_confirmed IS NOT TRUE")
            removed = cur.rowcount
            cur.execute("SELECT count(*) AS n FROM bg_sarvatobhadra_grid WHERE native_confirmed IS TRUE")
            row = cur.fetchone()
            confirmed = row['n'] if isinstance(row, dict) else row[0]
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=0,
            duration_seconds=time.time() - t0,
            notes=(f'ADJUDICATION-11 ruled empty state asserted: {removed} non-native-confirmed row(s) removed, '
                   f'0 inserted; {confirmed} native-confirmed row(s) preserved untouched'),
        )
