"""Why a Kāla layer is empty (SR-EMPTY-REASON; root CLAUDE.md §N.6 rule 4, §N.7.6, §N.8).

The Python twin of `platform/src/lib/retrieval/registry/layers/L3_kala/empty_layer_reason.ts`; the vocabulary is
pinned against it by `tests/l3/kala_core/test_empty_layer_reason.py`.

An empty `kala_convergence` / `kala_obstruction` layer is four different facts, and a consumer that cannot tell them
apart turns "nobody looked" into "nothing there" (a window "with no obstruction", a muhurta "with no overlap"):

  layer_not_computed              no rows in any partition and the writer asset is not lit
  computed_found_none             no rows in any partition and the writer asset IS lit (it ran and found nothing)
  rows_outside_served_generation  rows exist in the table, none in the partition readers are served
  filters_excluded_all_rows       the served partition holds rows, the reader's own condition dropped them all
  layer_state_unreadable          a count or the asset state could not be measured (an honest null, never a guess)

Every input is a count or an `asset_throughput.state` read from the database, never a constant.
"""
from __future__ import annotations

from typing import Optional

import psycopg

from services.kala_core.served_generation import served_obstruction_predicate

EMPTY_LAYER_REASONS = (
    'layer_not_computed',
    'computed_found_none',
    'rows_outside_served_generation',
    'filters_excluded_all_rows',
    'layer_state_unreadable',
)

# table -> (writer asset whose asset_throughput.state says "built", FROM..WHERE of the SERVED partition for chart_id = %s)
LAYERS: dict[str, tuple[str, str]] = {
    'kala_convergence': ('ka_sangam', 'kala_convergence_served WHERE chart_id = %s'),
    'kala_obstruction': ('ka_vighnakara',
                         'kala_obstruction o WHERE o.chart_id = %s AND ' + served_obstruction_predicate('o')),
}


def classify_empty_layer(rows_any_partition: Optional[int], rows_served: Optional[int],
                         asset_state: Optional[str]) -> str:
    """Pure classification of an empty result from measured counts (None = not measured)."""
    if rows_any_partition is None or rows_served is None:
        return 'layer_state_unreadable'
    if rows_served > 0:
        return 'filters_excluded_all_rows'
    if rows_any_partition > 0:
        return 'rows_outside_served_generation'
    return 'computed_found_none' if asset_state == 'lit' else 'layer_not_computed'


def read_empty_layer(conn, chart_id: str, table: str, *, savepoint: str) -> dict:
    """Measure and classify one layer. Runs on the caller's connection inside a SAVEPOINT (a failed probe must not
    abort the writer's transaction) and never raises: a failed measurement is `layer_state_unreadable`.

    Returns {'empty_reason': <EMPTY_LAYER_REASONS>, 'layer_state': {rows_any_partition, rows_served_unfiltered, asset_state}}.
    """
    asset_id, served_from_where = LAYERS[table]  # KeyError on an unknown table is a programming error, not a data state
    state: dict = {'rows_any_partition': None, 'rows_served_unfiltered': None, 'asset_state': None}
    try:
        with conn.cursor() as sp:
            sp.execute(f'SAVEPOINT {savepoint}')
        try:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    f'SELECT (SELECT COUNT(*) FROM {table} WHERE chart_id = %s) AS any_rows, '
                    f'(SELECT COUNT(*) FROM {served_from_where}) AS served_rows, '
                    '(SELECT state FROM asset_throughput WHERE chart_id = %s AND asset_id = %s LIMIT 1) AS asset_state',
                    (chart_id, chart_id, chart_id, asset_id),
                )
                row = cur.fetchone()
            with conn.cursor() as sp:
                sp.execute(f'RELEASE SAVEPOINT {savepoint}')
        except Exception:
            with conn.cursor() as sp:
                sp.execute(f'ROLLBACK TO SAVEPOINT {savepoint}')
            raise
    except Exception:
        return {'empty_reason': 'layer_state_unreadable', 'layer_state': state}
    if row is not None:
        state = {'rows_any_partition': None if row['any_rows'] is None else int(row['any_rows']),
                 'rows_served_unfiltered': None if row['served_rows'] is None else int(row['served_rows']),
                 'asset_state': row['asset_state']}
    return {'empty_reason': classify_empty_layer(state['rows_any_partition'], state['rows_served_unfiltered'],
                                                 state['asset_state']),
            'layer_state': state}
