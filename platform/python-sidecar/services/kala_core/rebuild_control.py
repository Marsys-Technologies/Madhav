"""K9 rebuild control: cancel a Kāla rebuild run, tear down the candidate it left (SR-PREBUILD-ALL, SR-TEARDOWN-AUTHORITY-GATE 2).

Both operations take ONE argument, the run id, and are scoped to the canonical chart and to an explicit Kāla rebuild plan
(``ka_*`` assets only, never the issued-forecast writer), the same scope ``publication._run`` enforces for the layer operations.

* ``cancel`` records the orchestrator's own stop signal. ``runner.check_signals`` stops a run whose ``stop_requested_at`` is set
  and ``mark_run_state`` terminalizes it as ``stopped``; the cockpit route ``/api/cockpit/runs/[id]/stop`` issues the same UPDATE.
  Only the REQUEST is made here: the returned ``state_after`` is what the database says, never a presumed ``CANCELLED``.
* ``teardown`` deletes the unpublished candidate of a TERMINAL run and every row that references it. The referencing tables
  are read from ``pg_constraint`` at run time, never from a list kept here (B.10); a dependent whose key is not
  ``(chart_id, generation)`` is refused rather than guessed at. A dependent that is itself referenced by another table whose rows
  outlive the candidate generation (the production ``issued_forecast``, referenced by ``issued_forecast_outcome`` through
  ``issue_id``, migration 1351) is never deleted from and never cascaded into: with no rows for the candidate it is left alone,
  with any it REFUSES the teardown naming it (SR-K9-PUBLISHABLE D8: delivered forecasts are append-only history). A dependent
  referenced only by tables keyed by the same ``(chart_id, generation)`` (the vedha writer's ``kala_vedha_gochara_candidate`` and
  its ``kala_vedha_gochara_interval``, migration 1383) is the failed run's OWN candidate output: those referencing rows go first,
  then the dependent (K9 round 3 D8). ``kala_activation_predicates`` carries the candidate generation without a foreign key, so
  its rows of the run's generation and chart are removed too (round 3 N1), as are the ``kala_f1_*`` rows the resonance writer's candidate path leaves and the ``kala_obstruction`` rows of the run's generation (never the legacy NULL partition or a served generation)
(W5/W6 N8). ``gochara_resonance_map`` carries the generation (migration 1404): the legacy resonance path writes the run's candidate generation, so the teardown
  removes the run's own partition by ``(chart_id, generation)`` and never a served row, and the result records the rows removed with the writer run id. A published
  candidate, the head generation and a candidate whose retained previous head is gone are refused. The head is read before and
  after and must be equal. The caller owns the transaction: nothing here commits.
* SR-K9-PUBLISHABLE D8: a teardown of a FAILED run also restores the asset states that run wrote. A failed rebuild leaves
  assets ``stale`` (``staleness.propagate_downstream_staleness``) and ``error`` (the failing asset and its blocked dependents);
  nothing else marks which ones, so the orchestrator's own audit trail (``asset_throughput_state_audit``, written by trigger for
  every state change made through ``pipeline.orchestrator.db.connect``) is read for the run's own window on this chart. An
  asset is restored to the state it held before the run ONLY IF it is still ``stale``/``error`` from that window's last change, that
  change is still the LATEST audit row of the asset (no later run or hand edit changed it since: round 3 N3), and its first change
  in the window came from a settled state; anything changed since, or by anyone else, is left alone and reported. A role that
  cannot read the audit trail refuses the teardown rather than guess (N.7.6). Never touches a published head or another chart.
"""
from __future__ import annotations

from datetime import timezone
from typing import Any

import psycopg
from psycopg import sql

from services.kala_core.manifest import Candidate, lock_candidate_inputs
from services.kala_core.publication import CANONICAL_CHART

CANCELLABLE = ('planned', 'running', 'paused')
TERMINAL = ('completed', 'stopped', 'failed')       # build_runs_state_check: planned, running, paused + these three
CANDIDATE_KEY = ['chart_id', 'generation']
AUDIT_TABLE = 'asset_throughput_state_audit'
WRITTEN_BY_A_FAILED_RUN = ('stale', 'error')
SETTLED_BEFORE = ('lit', 'service_ok', 'mature', 'dormant')     # runner.py's settled states: what a stale/error row can be restored to
# Carry (chart_id, generation) with no foreign key to kala_layer_candidate, listed child first (the delete runs in this order). Derived from the write targets of the
# closed K9 plan's writers (W5/W6 N8): ka_yojaka writes kala_activation_predicates; ka_gochara_resonance's candidate path (relationship_storage.store_projection, migration
# 1342) writes kala_f1_relationship, whose foreign key points at kala_f1_target_object, both keyed by (chart_id, ayanamsha_id, generation) with generation LIKE 'candidate:%'.
# ka_vighnakara's candidate path (SR-K9-WRITE-SCOPE) writes kala_obstruction rows under the candidate generation; the table carries NO foreign key to the candidate and its served rows
# (the head's generation, the legacy NULL partition) share the table, so the delete is aimed at (chart_id, this run's generation) and can never match a NULL or a served generation.
# kala_obstruction is listed ahead of kala_convergence (child first).
UNLINKED_CANDIDATE_TABLES = ('kala_activation_predicates', 'kala_f1_relationship', 'kala_f1_target_object', 'gochara_resonance_map', 'kala_obstruction', 'kala_convergence')
# gochara_resonance_map (migration 1404): ka_gochara_resonance writes the rows of its bound candidate generation (services/ka_gochara_resonance/writer.py), so the unlinked-table
# delete above removes exactly that run's partition and never the served one (the retained partition is 'legacy', refused below). The receipt names each plan writer whose rows were
# removed, with the count and the writer's run id (a candidate is bound to one build run: ``kala_layer_candidate.build_id``), so the removal is an honest report, not a silent pass (N.7.6).
GENERATION_SCOPED_WRITES = {'ka_gochara_resonance': 'gochara_resonance_map'}
# kala_convergence (migration 1405, ka_sangam's candidate output) is one of the unlinked tables above, and the only one other tables reference: its foreign keys cascade
# (kala_darshana, kala_obstruction, phala_anchors) or null (kala_bhavishya), so `cascade_reach` must show that the candidate's rows are referenced by nothing
# but rows of the candidate itself before they are deleted (K9-WRITE-SCOPE F1).
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


def _referrers(conn: Any, oid: int) -> list[tuple]:
    """(schema, table, table oid, referencing columns, referenced columns) of every foreign key onto the table ``oid``."""
    return conn.execute("""
        SELECT n.nspname, c.relname, con.conrelid,
               (SELECT array_agg(a.attname ORDER BY k.ord) FROM unnest(con.conkey) WITH ORDINALITY k(attnum, ord)
                 JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = k.attnum),
               (SELECT array_agg(a.attname ORDER BY k.ord) FROM unnest(con.confkey) WITH ORDINALITY k(attnum, ord)
                 JOIN pg_attribute a ON a.attrelid = con.confrelid AND a.attnum = k.attnum)
          FROM pg_constraint con
          JOIN pg_class c ON c.oid = con.conrelid
          JOIN pg_namespace n ON n.oid = c.relnamespace
         WHERE con.contype = 'f' AND con.confrelid = %s::oid
         ORDER BY n.nspname, c.relname, con.conname""", (oid,)).fetchall()


def _owned(conn: Any, oid: int, key: list[str], seen: frozenset) -> tuple[list[dict], list[str]]:
    """The tables below the table ``oid`` (keyed by the candidate key columns ``key``): (candidate-scoped ones, deepest first; the others).

    A referrer is candidate-scoped when its foreign key carries both candidate-key columns, so its rows of one candidate generation are
    exactly the rows that hang from that generation's rows: the run's own output (migration 1383: ``kala_vedha_gochara_interval`` ->
    ``kala_vedha_gochara_candidate``). Any other referrer (migration 1351: ``issued_forecast_outcome`` -> ``issued_forecast`` by
    ``issue_id``) holds rows that outlive the generation: issued history. A table met again on the way down is treated as that too."""
    owned: list[dict] = []
    foreign: list[str] = []
    for schema, table, child_oid, columns, referenced in _referrers(conn, oid):
        if child_oid in seen or not set(key) <= set(referenced):
            foreign.append(table)
            continue
        child_key = [columns[referenced.index(k)] for k in key]
        below, below_foreign = _owned(conn, child_oid, child_key, seen | {child_oid})
        owned += [t for t in below if t not in owned] + [{'schema': schema, 'table': table, 'columns': child_key}]
        foreign += below_foreign
    return owned, foreign


def dependents(conn: Any) -> list[dict]:
    """Every table with a foreign key to ``kala_layer_candidate``, read from the catalog, with what hangs below it: ``owned`` (tables
    scoped to the same candidate generation, deleted first) and ``referenced_by`` (tables holding issued history: the dependent is protected)."""
    found: dict[tuple, dict] = {}
    for schema, table, oid, columns, referenced in _referrers(conn, conn.execute("SELECT 'kala_layer_candidate'::regclass::oid").fetchone()[0]):
        if referenced != CANDIDATE_KEY or len(columns) != 2:
            raise ValueError(f'{table} references the candidate by {referenced}: only (chart_id, generation) can be torn down')
        owned, foreign = _owned(conn, oid, columns, frozenset({oid}))
        found[(schema, table, tuple(columns))] = {'schema': schema, 'table': table, 'columns': list(columns),
                                                  'referenced_by': sorted(set(foreign)), 'owned': owned}
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


def unlinked_tables(conn: Any) -> list[str]:
    """The ``UNLINKED_CANDIDATE_TABLES`` this database has."""
    return [t for t in UNLINKED_CANDIDATE_TABLES if conn.execute('SELECT to_regclass(%s)', (t,)).fetchone()[0] is not None]


def generation_scoped_writes(plan: list[str], deleted: dict[str, int], generation: str, run_id: str) -> list[dict]:
    """The plan's writers whose rows are held per candidate generation, with the rows the teardown removed and the id of the run that wrote them."""
    return [{'asset_id': asset, 'table': table, 'generation': generation, 'rows_deleted': deleted[table], 'writer_run_id': run_id}
            for asset, table in GENERATION_SCOPED_WRITES.items() if asset in plan and table in deleted]


def cascade_reach(conn: Any, chart_id: str, generation: str) -> list[tuple[str, str, int]]:
    """(table, action, rows) of every row OUTSIDE the candidate that a delete of the candidate's kala_convergence rows would delete or null.

    Read from ``pg_constraint`` (the live foreign keys onto kala_convergence, never a list kept here). A referencing row is the candidate's own when its
    table carries a ``generation`` column equal to the candidate's; any other referencing row (another generation, or a table that cannot say) is served or
    unattributable and would be destroyed by the cascade, so the teardown refuses (N.7.6)."""
    oid = conn.execute("SELECT to_regclass('kala_convergence')::oid").fetchone()[0]
    if oid is None:
        return []
    reach = []
    for schema, table, child_oid, columns, referenced in _referrers(conn, oid):
        if referenced != ['convergence_id'] or len(columns) != 1:
            raise ValueError(f'{table} references kala_convergence by {columns}: only convergence_id can be torn down safely')
        action = conn.execute('SELECT confdeltype FROM pg_constraint WHERE contype = %s AND conrelid = %s AND confrelid = %s',
                              ('f', child_oid, oid)).fetchone()[0]
        if action not in ('c', 'n', 'd'):      # cascade, set null, set default: the delete reaches the referencing row
            continue
        has_generation = conn.execute("SELECT 1 FROM pg_attribute WHERE attrelid = %s AND attname = 'generation' AND NOT attisdropped",
                                      (child_oid,)).fetchone() is not None
        outside = sql.SQL(' AND generation IS DISTINCT FROM %s') if has_generation else sql.SQL('')
        n = conn.execute(sql.SQL('SELECT count(*) FROM {}.{} WHERE {} IN (SELECT convergence_id FROM kala_convergence '
                                 'WHERE chart_id = %s AND generation = %s)').format(
                             sql.Identifier(schema), sql.Identifier(table), sql.Identifier(columns[0])) + outside,
                         (chart_id, generation, *((generation,) if has_generation else ()))).fetchone()[0]
        if n:
            reach.append((table, {'c': 'cascade', 'n': 'set null', 'd': 'set default'}[action], n))
    return reach


def row_counts(conn: Any, chart_id: str, generation: str) -> dict[str, int]:
    """Rows of one candidate generation in the candidate table, in every table that references it, in what hangs below those and in the unlinked tables."""
    counts = {'kala_layer_candidate': conn.execute('SELECT count(*) FROM kala_layer_candidate WHERE chart_id = %s AND generation = %s',
                                                   (chart_id, generation)).fetchone()[0]}
    for dep in dependents(conn):
        for table in [*dep['owned'], dep]:
            counts[table['table']] = conn.execute(sql.SQL('SELECT count(*) FROM {} WHERE ').format(_table(table)) + _where(table),
                                                  (chart_id, generation)).fetchone()[0]
    for table in unlinked_tables(conn):
        counts[table] = conn.execute(sql.SQL('SELECT count(*) FROM {} WHERE chart_id = %s AND generation = %s').format(sql.Identifier(table)),
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


def failed_run_asset_states(conn: Any, run_id: str, chart_id: str = CANONICAL_CHART) -> tuple[list[tuple], list[dict]]:
    """(restorable, left alone) for the stale/error rows the run's own window wrote.

    restorable: (asset_id, current state, state before the run, id of the run's last audit row of the asset), only where that audit row is
    still the LATEST one of the asset on this chart: nothing, no later run and no hand edit, changed the asset after the failed run (N3).
    left alone: the assets the run staled/errored that are no longer in that condition, with what changed them afterwards."""
    if conn.execute('SELECT to_regclass(%s)', (AUDIT_TABLE,)).fetchone()[0] is None:
        raise ValueError('the asset state audit trail is absent: the failed run\'s asset states cannot be identified')
    if not conn.execute('SELECT has_table_privilege(current_user, %s, %s)', (AUDIT_TABLE, 'SELECT')).fetchone()[0]:
        raise ValueError('this role cannot read the asset state audit trail: the failed run\'s asset states cannot be identified')
    rows = conn.execute("""
        WITH win AS (SELECT started_at, COALESCE(ended_at, now()) AS ended_at FROM build_runs WHERE id = %(run)s AND started_at IS NOT NULL),
             span AS (SELECT a.asset_id,
                             (array_agg(a.old_state ORDER BY a.id ASC))[1] AS first_old,
                             (array_agg(a.new_state ORDER BY a.id DESC))[1] AS last_new,
                             max(a.id) AS last_id
                        FROM asset_throughput_state_audit a, win
                       WHERE a.chart_id = %(chart)s AND a.triggered_by = %(by)s
                         AND a.changed_at >= win.started_at AND a.changed_at <= win.ended_at
                       GROUP BY a.asset_id)
        SELECT t.asset_id, t.state, span.first_old, span.last_id, span.last_new, later.id, later.new_state, later.triggered_by
          FROM span JOIN asset_throughput t ON t.chart_id = %(chart)s AND t.asset_id = span.asset_id
          LEFT JOIN LATERAL (SELECT l.id, l.new_state, l.triggered_by FROM asset_throughput_state_audit l
                              WHERE l.chart_id = %(chart)s AND l.asset_id = span.asset_id AND l.id > span.last_id
                              ORDER BY l.id DESC LIMIT 1) later ON true
         WHERE span.last_new = ANY(%(written)s) AND span.first_old = ANY(%(settled)s)
         ORDER BY t.asset_id""", {'run': run_id, 'chart': chart_id, 'by': ORCHESTRATOR, 'written': list(WRITTEN_BY_A_FAILED_RUN),
                                  'settled': list(SETTLED_BEFORE)}).fetchall()
    restorable = [(asset, state, before, last_id) for asset, state, before, last_id, last_new, later_id, _ns, _by in rows
                  if later_id is None and state == last_new]
    # a later write outside the orchestrator is audited with triggered_by '': no attribution, so null
    left = [{'asset_id': asset, 'state_now': state, 'state_before_run': before, 'run_wrote': last_new,
             'changed_since_by': (later_by or None) if later_id is not None else None, 'changed_since_to': later_state if later_id is not None else None}
            for asset, state, before, last_id, last_new, later_id, later_state, later_by in rows
            if not (later_id is None and state == last_new)]
    return restorable, left


def restore_asset_states(conn: Any, found: list[tuple], chart_id: str) -> list[dict]:
    """Restore each (asset_id, state, state before the run, last audit id) of ``failed_run_asset_states`` to the state it held before the run,
    only while that audit row is still the asset's latest (the same condition that selected it)."""
    restored = []
    for asset_id, state, before, last_id in found:
        changed = conn.execute("UPDATE asset_throughput t SET state = %s, last_error = CASE WHEN t.state = 'error' THEN NULL ELSE t.last_error END "
                               "WHERE t.chart_id = %s AND t.asset_id = %s AND t.state = %s "
                               f"AND NOT EXISTS (SELECT 1 FROM {AUDIT_TABLE} l WHERE l.chart_id = t.chart_id AND l.asset_id = t.asset_id AND l.id > %s)",
                               (before, chart_id, asset_id, state, last_id)).rowcount
        if changed != 1:
            raise ValueError(f'{asset_id} changed state before it could be restored')
        restored.append({'asset_id': asset_id, 'from': state, 'to': before})
    return restored


def _delete_of_generation(conn: Any, table: dict, chart_id: str, generation: str) -> int:
    """Delete one candidate generation's rows of ``table``; a database refusal (a guard trigger) is a named refusal of the teardown."""
    try:
        return conn.execute(sql.SQL('DELETE FROM {} WHERE ').format(_table(table)) + _where(table), (chart_id, generation)).rowcount
    except psycopg.Error as exc:
        raise ValueError(f"{table['table']} refused the deletion of this candidate's rows: {exc}")


def teardown(conn: Any, *, run_id: str, chart_id: str = CANONICAL_CHART) -> dict:
    run = _scoped_run(conn, run_id, chart_id)
    if run['state'] not in TERMINAL:
        raise ValueError(f"run is {run['state']}, not terminal: a running rebuild's candidate is not torn down")
    cand = candidate_of(conn, run_id, chart_id)
    if cand is None:
        raise ValueError('this run has no candidate rows: nothing to tear down')
    to_restore, left_alone = failed_run_asset_states(conn, run_id, chart_id) if run['state'] == 'failed' else ([], [])     # refuses before anything is deleted
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
    if generation == 'legacy':      # the unlinked tables default every row to 'legacy': never aim a delete at the retained partition
        raise ValueError('the legacy partition is not a candidate generation')
    reached = cascade_reach(conn, chart_id, generation) if 'kala_convergence' in unlinked_tables(conn) else []
    if reached:       # the foreign keys onto kala_convergence would destroy rows that are not this candidate's: refuse before anything is deleted
        raise ValueError('; '.join(f"deleting this candidate's kala_convergence rows would {action} {n} row(s) of {table} that are not this candidate's"
                                   for table, action, n in reached))
    deleted: dict[str, int] = {}
    for dep in deps:
        if dep['referenced_by']:
            deleted[dep['table']] = 0     # referenced dependent with no rows of this candidate (checked above): not touched
            continue
        for table in [*dep['owned'], dep]:     # the run's own output below the dependent goes first
            deleted[table['table']] = deleted.get(table['table'], 0) + _delete_of_generation(conn, table, chart_id, generation)
    for table in unlinked_tables(conn):        # no foreign key to find them by: scoped to this chart and this run's generation only
        deleted[table] = conn.execute(sql.SQL('DELETE FROM {} WHERE chart_id = %s AND generation = %s').format(sql.Identifier(table)),
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
            'head_generation': head_after, 'retained_previous_present': True, 'asset_states_restored': restored,
            'asset_states_left_alone': left_alone, 'chart_scoped_writes_left_alone': [],      # kept for the receipt's shape: no writer's rows are left alone any more
            'generation_scoped_writes_removed': generation_scoped_writes(run['plan'], deleted, generation, run_id)}
