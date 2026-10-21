"""K9-23 admission layer in front of ``services.kala_core.publication`` (SR-PREBUILD-ALL, SR-BOLD-04).

``publication.py`` stays the one reviewed, byte-pinned operation module (NB-KALA ``source_imports.json``); this module
adds only what the executor kinds need on top of it and delegates every real operation to it:

* ``rebuild`` / ``rebuild-dryrun`` -- ONE single-phase run over the whole in-scope plan (SR-K9-PUBLISHABLE D1: the SR-BOLD-04
  pre/post split is withdrawn and its ``--phase`` code path is gone; a plan that mixes assets on both sides of the gochara flip
  is the normal K9 rebuild). The kind admits a non-empty list of distinct assets that all exist in ``asset_registry``; the
  delegated ``publication`` operation then requires them to equal the run's frozen plan. The orchestrator's probe mode is its
  default delta-skip gate (``asset_runner.py`` ``_run_data_writer``); it is switched off only by ``NIRMANA_FORCE_EXECUTE``.
  An ambient forcing environment is refused. SR-BOLD-04-WITHDRAWN / U-K9P-01 (option B): the executor's ``rebuild`` kind passes
  the explicit ``--force-execute`` flag, which makes this module -- not the caller's environment -- turn the gate off for
  the one in-process run, so every planned writer executes and attests its grain under the new generation. A probe-skipped
  writer cannot be admitted instead: its rows live only under the lit build's generation and serving reads the head
  generation, so carrying its old grain forward would publish a layer silently missing that writer's rows (N.7.6, N.8).
  The delegated operation's stdout is ONE JSON document (SR-K9-PUBLISHABLE D5): the orchestrator's ``[event]`` lines and any
  import-time print go to stderr (``PUBSUB_DISABLED`` is set for the run, so the events are printed, never published to Pub/Sub),
  and the ``admission`` block (``probe_mode`` / ``force_execute``) is added to the result
  document, so a receipt shows whether the run was forced.
* ``verify-dryrun`` / ``publish-dryrun`` / ``rollback-dryrun`` -- the layer operations run for real inside a transaction
  that is then rolled back, with the rollback read back. ``dry_run_passed`` is true only when the operation ran, its
  write was observed inside the transaction, and the state read after the rollback equals the state read before it.
* ``cancel`` / ``teardown`` (+ ``-dryrun``) -- ``rebuild_control``: the orchestrator's stop request for a run, and the deletion of
  an unpublished candidate of a terminal run (a FAILED run also has the asset states it wrote restored, SR-K9-PUBLISHABLE D8).
  Each is read back from the database after its commit; the ``-dryrun`` twin is the same rehearsal as the layer ones.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
from datetime import timezone
from typing import Any, Callable, Iterable, Mapping
from uuid import UUID

import psycopg

from services.kala_core import publication, rebuild_control
from services.kala_core.publication import CANONICAL_CHART

# runner.py execute_run: ``os.environ.get("NIRMANA_FORCE_EXECUTE", "").strip().lower() in ("1", "true", "yes")``
FORCE_ENV = 'NIRMANA_FORCE_EXECUTE'
FORCING_VALUES = ('1', 'true', 'yes')
# events.py emit(): ``if os.environ.get("PUBSUB_DISABLED") or not os.environ.get("PUBSUB_TOPIC")`` prints the ``[event]`` line, otherwise publishes it
PUBSUB_ENV = 'PUBSUB_DISABLED'
REBUILD_OPERATIONS = ('rebuild', 'rebuild-dryrun')
REHEARSALS = ('verify-dryrun', 'publish-dryrun', 'rollback-dryrun')
CONTROL_OPERATIONS = ('cancel', 'teardown')
CONTROL_REHEARSALS = ('cancel-dryrun', 'teardown-dryrun')


def force_refusal(environ: Mapping[str, str]) -> str | None:
    """A reason when the environment would switch the orchestrator's delta-skip (probe) gate off, else None."""
    if environ.get(FORCE_ENV, '').strip().lower() in FORCING_VALUES:
        return FORCE_ENV + ' is set: the rebuild kind runs in probe mode and never forces every writer'
    return None


@contextlib.contextmanager
def forced_execution():
    """Switch the orchestrator's delta-skip gate off for the duration of one in-process run, then restore the environment."""
    previous = os.environ.get(FORCE_ENV, '')    # restored by assignment: an unset and an empty value both read as "not forcing"
    os.environ[FORCE_ENV] = '1'
    try:
        yield
    finally:
        os.environ[FORCE_ENV] = previous


@contextlib.contextmanager
def pubsub_disabled():
    """Keep the orchestrator's events off Pub/Sub for the duration of one in-process run, then restore the environment.

    ``events.emit`` reads the variable at emit time and, when it is set, prints each ``[event]`` line instead of publishing it, so a
    rebuild launched where ``PUBSUB_TOPIC`` is present still leaves its events as evidence on stderr and the two-source gates' log source
    is populated (W5/W6 M-W56-17). Restored by assignment, like ``forced_execution``: an unset and an empty value both read as "not disabled".
    """
    previous = os.environ.get(PUBSUB_ENV, '')
    os.environ[PUBSUB_ENV] = '1'
    try:
        yield
    finally:
        os.environ[PUBSUB_ENV] = previous


def assets_refusal(edges: Mapping[str, Iterable[str]], assets: list[str]) -> str | None:
    """A reason when ``assets`` is not an admissible single-phase K9 rebuild list, else None."""
    if not assets or any(not a for a in assets) or len(set(assets)) != len(assets):
        return 'assets must be a non-empty list without blanks or duplicates'
    unknown = [a for a in assets if a not in edges]
    if unknown:
        return 'not in asset_registry: ' + ', '.join(unknown)
    return None


def registry_edges(conn: Any) -> dict[str, list[str]]:
    rows = conn.execute("SELECT asset_id, COALESCE(depends_on, '{}') FROM asset_registry").fetchall()
    return {row[0]: list(row[1]) for row in rows}


# ---------------------------------------------------------------------------------------------------------------------
# rollback rehearsal of the layer operations


def _expected_head(value: str) -> str | None:
    return None if value == 'NONE' else value


def _canonical_candidate_refusal(conn: Any, run_id: str, generation: str) -> None:
    row = conn.execute('SELECT chart_id FROM kala_layer_candidate WHERE build_id=%s AND generation=%s',
                       (run_id, generation)).fetchone()
    if row is None or str(row[0]) != CANONICAL_CHART:
        raise ValueError('candidate is absent or outside canonical chart')


def _plan(conn: Any, args: argparse.Namespace) -> tuple[Callable[[], Any], Callable[[], dict]]:
    """(observe, act) for one rehearsal: what the operation changes, and the operation itself."""
    op = args.operation
    if op == 'rollback-dryrun':
        observe = lambda: conn.execute('SELECT generation FROM kala_layer_head WHERE chart_id=%s',
                                       (CANONICAL_CHART,)).fetchone()
        return observe, lambda: publication.rollback(conn, generation=args.generation, expected_head=args.expected_head)
    run_id = str(args.run_id)
    if op == 'cancel-dryrun':
        return (lambda: rebuild_control.cancel_state(conn, run_id),
                lambda: rebuild_control.cancel(conn, run_id=run_id))
    if op == 'teardown-dryrun':
        return (lambda: rebuild_control.census(conn, run_id),
                lambda: rebuild_control.teardown(conn, run_id=run_id))
    _canonical_candidate_refusal(conn, run_id, args.generation)
    if op == 'verify-dryrun':
        observe = lambda: conn.execute('SELECT count(*) FROM kala_layer_verification WHERE chart_id=%s AND generation=%s',
                                       (CANONICAL_CHART, args.generation)).fetchone()
        return observe, lambda: publication.verify(conn, run_id=run_id, generation=args.generation,
                                                   independently_derived_digest=args.independently_derived_digest)
    observe = lambda: conn.execute(
        'SELECT (SELECT generation FROM kala_layer_head WHERE chart_id=%s), '
        '(SELECT state FROM kala_layer_candidate WHERE chart_id=%s AND generation=%s)',
        (CANONICAL_CHART, CANONICAL_CHART, args.generation)).fetchone()
    return observe, lambda: publication.publish(conn, run_id=run_id, generation=args.generation,
                                                expected_head=_expected_head(args.expected_head))


def rehearse(conn: Any, args: argparse.Namespace) -> dict:
    """Run the operation inside a transaction, roll it back, and report what was observed (never commits)."""
    observe, act = _plan(conn, args)
    before = observe()
    result = act()
    inside = observe()
    conn.rollback()
    after = observe()
    conn.rollback()
    confirmed = after == before
    changed = inside != before
    return {'status': 'ROLLED_BACK', 'operation': args.operation, 'rollback_confirmed': confirmed,
            'write_observed_in_transaction': changed, 'dry_run_passed': bool(confirmed and changed),
            'operation_result': result}


# ---------------------------------------------------------------------------------------------------------------------
# command line


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='operation', required=True)
    for operation in REBUILD_OPERATIONS + REHEARSALS + CONTROL_OPERATIONS + CONTROL_REHEARSALS:
        p = sub.add_parser(operation)
        if operation != 'rollback-dryrun':
            p.add_argument('--run-id', required=True, type=UUID)
        if operation in CONTROL_OPERATIONS + CONTROL_REHEARSALS:
            continue
        if operation in REBUILD_OPERATIONS:
            p.add_argument('--assets', required=True)
            if operation == 'rebuild':
                p.add_argument('--force-execute', action='store_true')
        else:
            p.add_argument('--generation', required=True)
        if operation in ('publish-dryrun', 'rollback-dryrun'):
            p.add_argument('--expected-head', required=True)
        if operation == 'verify-dryrun':
            p.add_argument('--independently-derived-digest', required=True)
    return parser


def _refuse(reason: str, code: int = 2) -> int:
    print(json.dumps({'status': 'REFUSED', 'reason': reason}))
    return code


def _forces(args: argparse.Namespace) -> bool:
    return bool(getattr(args, 'force_execute', False))


def _admit_rebuild(dsn: str, args: argparse.Namespace) -> str | None:
    # The explicit flag is the only way to force; an ambient forcing environment is still refused.
    forced = force_refusal(os.environ)
    if forced:
        return forced
    with psycopg.connect(dsn, connect_timeout=5) as conn:
        conn.read_only = True
        return assets_refusal(registry_edges(conn), args.assets.split(','))


def split_output(text: str) -> tuple[dict | None, list[str]]:
    """(the delegated operation's own result, every other line): the result is the last stdout line that is a JSON object."""
    lines = text.splitlines()
    for index in range(len(lines) - 1, -1, -1):
        try:
            document = json.loads(lines[index])
        except ValueError:
            continue
        if isinstance(document, dict):
            return document, lines[:index] + lines[index + 1:]
    return None, lines


def _delegate_rebuild(args: argparse.Namespace) -> int:
    captured = io.StringIO()
    # --force-execute applies to the real rebuild only; the dry run executes nothing.
    forcing = _forces(args) and args.operation == 'rebuild'
    code = 3
    try:
        with contextlib.redirect_stdout(captured), pubsub_disabled(), (forced_execution() if forcing else contextlib.nullcontext()):
            code = publication.main([args.operation, '--run-id', str(args.run_id), '--assets', args.assets])
    finally:
        document, rest = split_output(captured.getvalue())
        # Orchestrator [event] lines and import-time prints are evidence on stderr, never part of the proof on stdout.
        if rest:
            print('\n'.join(rest), file=sys.stderr)
    if document is None:
        print(json.dumps({'status': 'FAILED', 'reason': 'the delegated rebuild produced no JSON result document'}))
        return code or 3
    if code == 0:
        document['admission'] = {'assets': args.assets.split(','),
                                 'probe_mode': 'force_execute' if forcing else 'delta_skip_gate', 'force_execute': forcing}
    print(json.dumps(document, sort_keys=True))
    return code


def _control(dsn: str, args: argparse.Namespace) -> int:
    """``cancel`` / ``teardown``: commit, then read the outcome back from the database (never from an exit code)."""
    run_id = str(args.run_id)
    with psycopg.connect(dsn, connect_timeout=5) as conn:
        try:
            if args.operation == 'cancel':
                result = rebuild_control.cancel(conn, run_id=run_id)
            else:
                result = rebuild_control.teardown(conn, run_id=run_id)
        except ValueError as exc:
            conn.rollback()
            return _refuse(str(exc))
        conn.commit()
        if args.operation == 'cancel':
            state, requested = rebuild_control.cancel_state(conn, run_id)
            result['readback'] = {'state': state, 'stop_requested_at': requested.astimezone(timezone.utc).isoformat() if requested else None}
        else:
            states = dict(rebuild_control.asset_state_census(conn))
            result['readback'] = {'remaining_rows': rebuild_control.row_counts(conn, rebuild_control.CANONICAL_CHART, result['generation']),
                                  'head_generation': rebuild_control.head_of(conn, rebuild_control.CANONICAL_CHART),
                                  'asset_states': {r['asset_id']: states.get(r['asset_id']) for r in result['asset_states_restored']}}
        conn.rollback()
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    dsn = os.environ.get('DATABASE_URL')
    if not dsn:
        return _refuse('operation-specific DATABASE_URL is required')
    try:
        if args.operation in REBUILD_OPERATIONS:
            reason = _admit_rebuild(dsn, args)
            return _refuse(reason) if reason else _delegate_rebuild(args)
        if args.operation in CONTROL_OPERATIONS:
            return _control(dsn, args)
        with psycopg.connect(dsn, connect_timeout=5) as conn:
            try:
                result = rehearse(conn, args)
            except ValueError as exc:
                conn.rollback()
                print(json.dumps({'status': 'REFUSED', 'reason': str(exc), 'dry_run_passed': False}))
                return 2
            finally:
                conn.rollback()
        print(json.dumps(result, sort_keys=True))
        return 0
    except psycopg.Error:
        # Connection diagnostics may contain secrets: do not echo libpq errors.
        return _refuse('database operation failed; transaction rolled back', 3)


if __name__ == '__main__':
    raise SystemExit(main())
