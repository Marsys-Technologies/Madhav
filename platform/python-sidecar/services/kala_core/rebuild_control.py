"""K9 rebuild control: cancel a Kāla rebuild run, tear down the candidate it left (SR-PREBUILD-ALL, SR-TEARDOWN-AUTHORITY-GATE 2).

Both operations take ONE argument, the run id, and are scoped to the canonical chart and to an explicit Kāla rebuild plan
(``ka_*`` assets only, never the issued-forecast writer), the same scope ``publication._run`` enforces for the layer operations.

* ``cancel`` records the orchestrator's own stop signal. ``runner.check_signals`` stops a run whose ``stop_requested_at`` is set
  and ``mark_run_state`` terminalizes it as ``stopped``; the cockpit route ``/api/cockpit/runs/[id]/stop`` issues the same UPDATE.
  Only the REQUEST is made here: the returned ``state_after`` is what the database says, never a presumed ``CANCELLED``.
* ``teardown`` deletes the unpublished candidate of a TERMINAL run and every row that references it. The referencing tables
  are read from ``pg_constraint`` at run time, never from a list kept here (B.10); a dependent whose key is not
  ``(chart_id, generation)``, or that is itself referenced by another table, is refused rather than guessed at. A published
  candidate, the head generation and a candidate whose retained previous head is gone are refused. The head is read before and
  after and must be equal. The caller owns the transaction: nothing here commits.
"""
from __future__ import annotations

from datetime import timezone
from typing import Any

from psycopg import sql

from services.kala_core.manifest import Candidate, lock_candidate_inputs
from services.kala_core.publication import CANONICAL_CHART

CANCELLABLE = ('planned', 'running', 'paused')
TERMINAL = ('completed', 'stopped', 'failed')       # build_runs_state_check: planned, running, paused + these three
CANDIDATE_KEY = ['chart_id', 'generation']


def _scoped_run(conn: Any, run_id: str, chart_id: str) -> dict:
    row = conn.execute('SELECT id, chart_id, action, plan, state, stop_requested_at FROM build_runs WHERE id = %s',
                       (run_id,)).fetchone()
    if row is None:
        raise ValueError('build run is absent')
    run = dict(zip(('id', 'chart_id', 'action', 'plan', 'state', 'stop_requested_at'), row))
    if str(run['chart_id']) != chart_id:
        raise ValueError('executor operation is canonical-chart scoped')
    plan = run['plan']
    if (run['action'] != 'rebuild' or not isinstance(plan, list) or not plan
            or any(not isinstance(a, str) or not a.startswith('ka_') for a in plan)):
        raise ValueError('only an explicit Kāla rebuild plan is permitted')
    if 'ka_bhavishya_lekha' in plan:
        raise ValueError('issued forecasts are outside the replaceable rebuild set')
    return run


# ---------------------------------------------------------------------------------------------------------------------
# cancel


def cancel_state(conn: Any, run_id: str) -> tuple:
    """What a cancel changes: the run state and the stop request time."""
    return conn.execute('SELECT state, stop_requested_at FROM build_runs WHERE id = %s', (run_id,)).fetchone()


def cancel(conn: Any, *, run_id: str, chart_id: str = CANONICAL_CHART) -> dict:
    run = _scoped_run(conn, run_id, chart_id)
    if run['state'] not in CANCELLABLE:
        raise ValueError(f"run is {run['state']}: only a planned, running or paused run can be cancelled")
    # Same UPDATE as platform/src/app/api/cockpit/runs/[id]/stop/route.ts, except that a first stop request keeps its time.
    row = conn.execute(
        "UPDATE build_runs SET stop_requested_at = COALESCE(stop_requested_at, NOW()), "
        "state = CASE WHEN state = 'planned' THEN 'stopped' ELSE state END "
        "WHERE id = %s AND chart_id = %s AND state IN ('planned','running','paused') "
        "RETURNING state, stop_requested_at", (run_id, chart_id)).fetchone()
    if row is None:
        raise ValueError('run changed state before the stop request')
    return {'status': 'CANCEL_REQUESTED', 'run_id': run_id, 'state_before': run['state'], 'state_after': row[0],
            'stop_requested_at': row[1].astimezone(timezone.utc).isoformat(), 'terminal': row[0] in TERMINAL}


# ---------------------------------------------------------------------------------------------------------------------
# teardown


def dependents(conn: Any) -> list[dict]:
    """Every table with a foreign key to ``kala_layer_candidate``, read from the catalog."""
    rows = conn.execute("""
        SELECT n.nspname, c.relname, con.conrelid,
               (SELECT array_agg(a.attname ORDER BY k.ord) FROM unnest(con.conkey) WITH ORDINALITY k(attnum, ord)
                 JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = k.attnum),
               (SELECT array_agg(a.attname ORDER BY k.ord) FROM unnest(con.confkey) WITH ORDINALITY k(attnum, ord)
                 JOIN pg_attribute a ON a.attrelid = con.confrelid AND a.attnum = k.attnum),
               EXISTS (SELECT 1 FROM pg_constraint down WHERE down.contype = 'f' AND down.confrelid = con.conrelid)
          FROM pg_constraint con
          JOIN pg_class c ON c.oid = con.conrelid
          JOIN pg_namespace n ON n.oid = c.relnamespace
         WHERE con.contype = 'f' AND con.confrelid = 'kala_layer_candidate'::regclass
         ORDER BY n.nspname, c.relname, con.conname""").fetchall()
    found: dict[tuple, dict] = {}
    for schema, table, _oid, columns, referenced, referenced_by_others in rows:
        if referenced != CANDIDATE_KEY or len(columns) != 2:
            raise ValueError(f'{table} references the candidate by {referenced}: only (chart_id, generation) can be torn down')
        if referenced_by_others:
            raise ValueError(f'{table} is itself referenced by another table: its dependents are not covered')
        found[(schema, table, tuple(columns))] = {'schema': schema, 'table': table, 'columns': list(columns)}
    return list(found.values())


def _where(dep: dict) -> sql.Composed:
    return sql.SQL('{} = %s AND {} = %s').format(sql.Identifier(dep['columns'][0]), sql.Identifier(dep['columns'][1]))


def _table(dep: dict) -> sql.Composed:
    return sql.SQL('{}.{}').format(sql.Identifier(dep['schema']), sql.Identifier(dep['table']))


def candidate_of(conn: Any, run_id: str, chart_id: str):
    return conn.execute('SELECT generation, state, expected_head_generation FROM kala_layer_candidate '
                        'WHERE build_id = %s AND chart_id = %s', (run_id, chart_id)).fetchone()


def head_of(conn: Any, chart_id: str):
    row = conn.execute('SELECT generation FROM kala_layer_head WHERE chart_id = %s', (chart_id,)).fetchone()
    return None if row is None else row[0]


def row_counts(conn: Any, chart_id: str, generation: str) -> dict[str, int]:
    """Rows of one candidate generation in the candidate table and in every table that references it."""
    counts = {'kala_layer_candidate': conn.execute('SELECT count(*) FROM kala_layer_candidate WHERE chart_id = %s AND generation = %s',
                                                   (chart_id, generation)).fetchone()[0]}
    for dep in dependents(conn):
        counts[dep['table']] = conn.execute(sql.SQL('SELECT count(*) FROM {} WHERE ').format(_table(dep)) + _where(dep),
                                            (chart_id, generation)).fetchone()[0]
    return counts


def census(conn: Any, run_id: str, chart_id: str = CANONICAL_CHART) -> dict:
    """Row counts of the run's candidate (empty when the run has none)."""
    cand = candidate_of(conn, run_id, chart_id)
    return {} if cand is None else row_counts(conn, chart_id, cand[0])


def retained_previous_present(conn: Any, chart_id: str, expected_head: str | None) -> bool:
    """The candidate was opened against a head; that previous generation must still be published and retained."""
    if expected_head is None:
        return True
    return conn.execute("SELECT 1 FROM kala_layer_candidate WHERE chart_id = %s AND generation = %s AND state = 'published'",
                        (chart_id, expected_head)).fetchone() is not None


def teardown(conn: Any, *, run_id: str, chart_id: str = CANONICAL_CHART) -> dict:
    run = _scoped_run(conn, run_id, chart_id)
    if run['state'] not in TERMINAL:
        raise ValueError(f"run is {run['state']}, not terminal: a running rebuild's candidate is not torn down")
    cand = candidate_of(conn, run_id, chart_id)
    if cand is None:
        raise ValueError('this run has no candidate rows: nothing to tear down')
    generation = cand[0]
    lock_candidate_inputs(conn, Candidate(chart_id, generation, run_id, cand[2]))    # serialises with a publish of the same candidate
    cand = conn.execute('SELECT generation, state, expected_head_generation FROM kala_layer_candidate '
                        'WHERE build_id = %s AND chart_id = %s FOR UPDATE', (run_id, chart_id)).fetchone()
    if cand is None:
        raise ValueError('the candidate disappeared before the teardown')
    head_before = head_of(conn, chart_id)
    if cand[1] == 'published' or cand[0] == head_before:
        raise ValueError('a published candidate or the head generation is never torn down')
    if not retained_previous_present(conn, chart_id, cand[2]):
        raise ValueError('the retained previous generation is not present: refusing to delete beside an unreadable head')
    deleted: dict[str, int] = {}
    for dep in dependents(conn):
        deleted[dep['table']] = conn.execute(sql.SQL('DELETE FROM {} WHERE ').format(_table(dep)) + _where(dep),
                                             (chart_id, generation)).rowcount
    removed = conn.execute("DELETE FROM kala_layer_candidate WHERE chart_id = %s AND generation = %s AND build_id = %s "
                           "AND state <> 'published'", (chart_id, generation, run_id)).rowcount
    if removed != 1:
        raise ValueError('the candidate row was not removed')
    deleted['kala_layer_candidate'] = removed
    head_after = head_of(conn, chart_id)
    if head_after != head_before:
        raise ValueError('the head moved during the teardown')
    if not retained_previous_present(conn, chart_id, cand[2]):
        raise ValueError('the retained previous generation is not present after the teardown')
    return {'status': 'TORN_DOWN', 'run_id': run_id, 'generation': generation, 'candidate_state': cand[1], 'deleted': deleted,
            'head_generation': head_after, 'retained_previous_present': True}
