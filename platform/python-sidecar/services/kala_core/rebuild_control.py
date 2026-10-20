"""K9 rebuild control: cancel a Kāla rebuild run, tear down the candidate it left (SR-PREBUILD-ALL, SR-TEARDOWN-AUTHORITY-GATE 2).

Both operations take ONE argument, the run id, and are scoped to the canonical chart and to an explicit Kāla rebuild plan
(``ka_*`` assets only, never the issued-forecast writer), the same scope ``publication._run`` enforces for the layer operations.

* ``cancel`` records the orchestrator's own stop signal. ``runner.check_signals`` stops a run whose ``stop_requested_at`` is set
  and ``mark_run_state`` terminalizes it as ``stopped``; the cockpit route ``/api/cockpit/runs/[id]/stop`` issues the same UPDATE.
  Only the REQUEST is made here: the returned ``state_after`` is what the database says, never a presumed ``CANCELLED``.
* ``teardown`` deletes the unpublished candidate of a TERMINAL run and every row that references it. The referencing tables
  are read from ``pg_constraint`` at run time, never from a list kept here (B.10); a dependent whose key is not
  ``(chart_id, generation)`` is refused rather than guessed at. A dependent that is itself referenced by another table (the
  production ``issued_forecast``, referenced by ``issued_forecast_outcome``, migration 1351) is never deleted from and never
  cascaded into: with no rows for the candidate it is left alone, with any it REFUSES the teardown naming it (SR-K9-PUBLISHABLE
  D8: delivered forecasts are append-only history). A published
  candidate, the head generation and a candidate whose retained previous head is gone are refused. The head is read before and
  after and must be equal. The caller owns the transaction: nothing here commits.
* SR-K9-PUBLISHABLE D8: a teardown of a FAILED run also restores the asset states that run wrote. A failed rebuild leaves
  assets ``stale`` (``staleness.propagate_downstream_staleness``) and ``error`` (the failing asset and its blocked dependents);
  nothing else marks which ones, so the orchestrator's own audit trail (``asset_throughput_state_audit``, written by trigger for
  every state change made through ``pipeline.orchestrator.db.connect``) is read for the run's own window on this chart. An
  asset is restored to the state it held before the run ONLY IF it is still ``stale``/``error`` from that window's last change and
  its first change in the window came from a settled state; anything changed since, or by anyone else, is left alone. A role that
  cannot read the audit trail refuses the teardown rather than guess (N.7.6). Never touches a published head or another chart.
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
AUDIT_TABLE = 'asset_throughput_state_audit'
WRITTEN_BY_A_FAILED_RUN = ('stale', 'error')
SETTLED_BEFORE = ('lit', 'service_ok', 'mature', 'dormant')     # runner.py's settled states: what a stale/error row can be restored to
ORCHESTRATOR = 'asset_runner'                                   # pipeline/orchestrator/db.py: marsys.triggered_by on every build connection


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
    """Every table with a foreign key to ``kala_layer_candidate``, read from the catalog, with the tables that reference it in turn."""
    rows = conn.execute("""
        SELECT n.nspname, c.relname, con.conrelid,
               (SELECT array_agg(a.attname ORDER BY k.ord) FROM unnest(con.conkey) WITH ORDINALITY k(attnum, ord)
                 JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = k.attnum),
               (SELECT array_agg(a.attname ORDER BY k.ord) FROM unnest(con.confkey) WITH ORDINALITY k(attnum, ord)
                 JOIN pg_attribute a ON a.attrelid = con.confrelid AND a.attnum = k.attnum),
               (SELECT array_agg(DISTINCT dc.relname ORDER BY dc.relname) FROM pg_constraint down
                 JOIN pg_class dc ON dc.oid = down.conrelid WHERE down.contype = 'f' AND down.confrelid = con.conrelid)
          FROM pg_constraint con
          JOIN pg_class c ON c.oid = con.conrelid
          JOIN pg_namespace n ON n.oid = c.relnamespace
         WHERE con.contype = 'f' AND con.confrelid = 'kala_layer_candidate'::regclass
         ORDER BY n.nspname, c.relname, con.conname""").fetchall()
    found: dict[tuple, dict] = {}
    for schema, table, _oid, columns, referenced, referenced_by_others in rows:
        if referenced != CANDIDATE_KEY or len(columns) != 2:
            raise ValueError(f'{table} references the candidate by {referenced}: only (chart_id, generation) can be torn down')
        found[(schema, table, tuple(columns))] = {'schema': schema, 'table': table, 'columns': list(columns),
                                                  'referenced_by': list(referenced_by_others or [])}
    return list(found.values())


def _where(dep: dict) -> sql.Composed:
    return sql.SQL('{} = %s AND {} = %s').format(sql.Identifier(dep['columns'][0]), sql.Identifier(dep['columns'][1]))


def _table(dep: dict) -> sql.Composed:
    return sql.SQL('{}.{}').format(sql.Identifier(dep['schema']), sql.Identifier(dep['table']))


def protected_rows(conn: Any, deps: list[dict], chart_id: str, generation: str) -> list[tuple[str, int, list[str]]]:
    """(table, rows of this candidate, tables referencing it) for each referenced dependent that holds rows of the candidate."""
    held = []
    for dep in deps:
        if dep['referenced_by']:
            n = conn.execute(sql.SQL('SELECT count(*) FROM {} WHERE ').format(_table(dep)) + _where(dep), (chart_id, generation)).fetchone()[0]
            if n:
                held.append((dep['table'], n, dep['referenced_by']))
    return held


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


def asset_state_census(conn: Any, chart_id: str = CANONICAL_CHART) -> list[tuple]:
    """The readback of a restore: every (asset, state) of the chart, as the database now holds them."""
    return [tuple(r) for r in conn.execute('SELECT asset_id, state FROM asset_throughput WHERE chart_id = %s ORDER BY asset_id',
                                           (chart_id,)).fetchall()]


def failed_run_asset_states(conn: Any, run_id: str, chart_id: str = CANONICAL_CHART) -> list[tuple]:
    """(asset_id, current state, state before the run) for each stale/error row the run's own window left behind."""
    if conn.execute('SELECT to_regclass(%s)', (AUDIT_TABLE,)).fetchone()[0] is None:
        raise ValueError('the asset state audit trail is absent: the failed run\'s asset states cannot be identified')
    if not conn.execute('SELECT has_table_privilege(current_user, %s, %s)', (AUDIT_TABLE, 'SELECT')).fetchone()[0]:
        raise ValueError('this role cannot read the asset state audit trail: the failed run\'s asset states cannot be identified')
    return [tuple(r) for r in conn.execute("""
        WITH win AS (SELECT started_at, COALESCE(ended_at, now()) AS ended_at FROM build_runs WHERE id = %(run)s AND started_at IS NOT NULL),
             span AS (SELECT a.asset_id,
                             (array_agg(a.old_state ORDER BY a.id ASC))[1] AS first_old,
                             (array_agg(a.new_state ORDER BY a.id DESC))[1] AS last_new
                        FROM asset_throughput_state_audit a, win
                       WHERE a.chart_id = %(chart)s AND a.triggered_by = %(by)s
                         AND a.changed_at >= win.started_at AND a.changed_at <= win.ended_at
                       GROUP BY a.asset_id)
        SELECT t.asset_id, t.state, span.first_old
          FROM span JOIN asset_throughput t ON t.chart_id = %(chart)s AND t.asset_id = span.asset_id
         WHERE t.state = ANY(%(written)s) AND t.state = span.last_new AND span.first_old = ANY(%(settled)s)
         ORDER BY t.asset_id""", {'run': run_id, 'chart': chart_id, 'by': ORCHESTRATOR, 'written': list(WRITTEN_BY_A_FAILED_RUN),
                                  'settled': list(SETTLED_BEFORE)}).fetchall()]


def restore_asset_states(conn: Any, found: list[tuple], chart_id: str) -> list[dict]:
    """Restore each (asset_id, state, state before the run) of ``failed_run_asset_states`` to the state it held before the run."""
    restored = []
    for asset_id, state, before in found:
        changed = conn.execute("UPDATE asset_throughput SET state = %s, last_error = CASE WHEN state = 'error' THEN NULL ELSE last_error END "
                               "WHERE chart_id = %s AND asset_id = %s AND state = %s",
                               (before, chart_id, asset_id, state)).rowcount
        if changed != 1:
            raise ValueError(f'{asset_id} changed state before it could be restored')
        restored.append({'asset_id': asset_id, 'from': state, 'to': before})
    return restored


def teardown(conn: Any, *, run_id: str, chart_id: str = CANONICAL_CHART) -> dict:
    run = _scoped_run(conn, run_id, chart_id)
    if run['state'] not in TERMINAL:
        raise ValueError(f"run is {run['state']}, not terminal: a running rebuild's candidate is not torn down")
    cand = candidate_of(conn, run_id, chart_id)
    if cand is None:
        raise ValueError('this run has no candidate rows: nothing to tear down')
    to_restore = failed_run_asset_states(conn, run_id, chart_id) if run['state'] == 'failed' else []     # refuses before anything is deleted
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
    deps = dependents(conn)
    held = protected_rows(conn, deps, chart_id, generation)
    if held:      # delivered history is append-only: refuse before anything is deleted, never delete it, never cascade
        raise ValueError('; '.join(f"{table} is itself referenced by {', '.join(by)} and holds {n} row(s) of this candidate: "
                                   f'issued history is never torn down' for table, n, by in held))
    deleted: dict[str, int] = {}
    for dep in deps:
        if dep['referenced_by']:
            deleted[dep['table']] = 0     # referenced dependent with no rows of this candidate (checked above): not touched
            continue
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
    restored = restore_asset_states(conn, to_restore, chart_id)
    return {'status': 'TORN_DOWN', 'run_id': run_id, 'generation': generation, 'candidate_state': cand[1], 'deleted': deleted,
            'head_generation': head_after, 'retained_previous_present': True, 'asset_states_restored': restored}
