"""Which partition of `kala_obstruction` is SERVED (SR-K9-WRITE-SCOPE).

The table holds up to three kinds of rows for one chart: the legacy partition (`generation IS NULL`,
rewritten in place by an ordinary `ka_vighnakara` rebuild), the published head's generation, and the
private `candidate:<build>` generations a K9 build is still writing. A reader consumes ONE of them:
the head generation when it holds rows, otherwise the legacy partition. Never a candidate, and never
both (the head replaces the legacy rows, it does not add to them).

The same rule is written in TypeScript for the served tools
(`platform/src/lib/retrieval/registry/layers/L3_kala/served_obstruction.ts`); the two are pinned
against each other by `tests/l3/kala_db/ka_vighnakara/test_obstruction_served_partition.py`.
"""
from __future__ import annotations


def served_obstruction_predicate(alias: str) -> str:
    """SQL predicate over `<alias>` (a `kala_obstruction` row) true exactly for the served partition."""
    if not alias.isidentifier():
        raise ValueError('alias must be a plain identifier')
    return (f'{alias}.generation IS NOT DISTINCT FROM ('
            f'SELECT h.generation FROM kala_layer_head h WHERE h.chart_id = {alias}.chart_id '
            f'AND EXISTS (SELECT 1 FROM kala_obstruction x WHERE x.chart_id = h.chart_id AND x.generation = h.generation))')
