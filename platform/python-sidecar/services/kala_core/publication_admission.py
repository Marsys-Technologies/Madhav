"""K9-23 admission layer in front of ``services.kala_core.publication`` (SR-PREBUILD-ALL, SR-BOLD-04).

``publication.py`` stays the one reviewed, byte-pinned operation module (NB-KALA ``source_imports.json``); this module
adds only what the executor kinds need on top of it and delegates every real operation to it:

* ``rebuild`` / ``rebuild-dryrun`` -- the SR-BOLD-04 split. ``--phase pre`` admits only assets that do not depend on the
  gochara surface the flip changes, ``--phase post`` only assets that are that surface or depend on it. The set is read
  from ``asset_registry.depends_on`` at run time, never from a list kept here. The orchestrator's probe mode is its
  default delta-skip gate (``asset_runner.py`` ``_run_data_writer``); it is switched off only by ``NIRMANA_FORCE_EXECUTE``,
  so a rebuild that would force is refused.
* ``verify-dryrun`` / ``publish-dryrun`` / ``rollback-dryrun`` -- the layer operations run for real inside a transaction
  that is then rolled back, with the rollback read back. ``dry_run_passed`` is true only when the operation ran, its
  write was observed inside the transaction, and the state read after the rollback equals the state read before it.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
from typing import Any, Callable, Iterable, Mapping
from uuid import UUID

import psycopg

from services.kala_core import publication
from services.kala_core.publication import CANONICAL_CHART

# SR-BOLD-04 reading (J-bold04 GRAPH.json split_rule_used): "gochara-dependent" is one of the four gochara producers
# OR a transitive dependent of one. The literal "depends on ka_gochara_v5" test is vacuous: nothing declares that edge.
GOCHARA_SURFACE = frozenset({'ka_gochara', 'ka_gochara_v3_century_materialize',
                             'ka_gochara_v4_41_candidate', 'ka_gochara_v5'})
PHASES = ('pre', 'post')
# runner.py execute_run: ``os.environ.get("NIRMANA_FORCE_EXECUTE", "").strip().lower() in ("1", "true", "yes")``
FORCE_ENV = 'NIRMANA_FORCE_EXECUTE'
FORCING_VALUES = ('1', 'true', 'yes')
REBUILD_OPERATIONS = ('rebuild', 'rebuild-dryrun')
REHEARSALS = ('verify-dryrun', 'publish-dryrun', 'rollback-dryrun')


def force_refusal(environ: Mapping[str, str]) -> str | None:
    """A reason when the environment would switch the orchestrator's delta-skip (probe) gate off, else None."""
    if environ.get(FORCE_ENV, '').strip().lower() in FORCING_VALUES:
        return FORCE_ENV + ' is set: the rebuild kind runs in probe mode and never forces every writer'
    return None


def gochara_closure(edges: Mapping[str, Iterable[str]]) -> frozenset[str]:
    """The gochara surface plus every asset that depends on a member of it, directly or transitively."""
    members = set(GOCHARA_SURFACE)
    grew = True
    while grew:
        grew = False
        for asset, deps in edges.items():
            if asset not in members and any(dep in members for dep in deps):
                members.add(asset)
                grew = True
    return frozenset(members)


def phase_refusal(edges: Mapping[str, Iterable[str]], assets: list[str], phase: str) -> str | None:
    """A reason when ``assets`` does not belong to ``phase`` of the K9 rebuild split, else None."""
    if phase not in PHASES:
        return 'phase must be one of ' + ', '.join(PHASES)
    if not assets or any(not a for a in assets) or len(set(assets)) != len(assets):
        return 'assets must be a non-empty list without blanks or duplicates'
    unknown = [a for a in assets if a not in edges]
    if unknown:
        return 'not in asset_registry: ' + ', '.join(unknown)
    closure = gochara_closure(edges)
    if phase == 'pre':
        offenders = [a for a in assets if a in closure]
        if offenders:
            return 'pre-flip rebuild may not include gochara-dependent assets: ' + ', '.join(offenders)
    else:
        offenders = [a for a in assets if a not in closure]
        if offenders:
            return 'post-flip rebuild is limited to gochara-dependent assets; not dependent: ' + ', '.join(offenders)
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
    for operation in REBUILD_OPERATIONS + REHEARSALS:
        p = sub.add_parser(operation)
        if operation != 'rollback-dryrun':
            p.add_argument('--run-id', required=True, type=UUID)
        if operation in REBUILD_OPERATIONS:
            p.add_argument('--assets', required=True)
            p.add_argument('--phase', required=True, choices=PHASES)
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


def _admit_rebuild(dsn: str, args: argparse.Namespace) -> str | None:
    forced = force_refusal(os.environ)
    if forced:
        return forced
    with psycopg.connect(dsn, connect_timeout=5) as conn:
        conn.read_only = True
        return phase_refusal(registry_edges(conn), args.assets.split(','), args.phase)


def _delegate_rebuild(args: argparse.Namespace) -> int:
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        code = publication.main([args.operation, '--run-id', str(args.run_id), '--assets', args.assets])
    text = captured.getvalue().strip()
    try:
        document = json.loads(text)
    except ValueError:
        print(text)
        return code
    if code == 0:
        document['admission'] = {'phase': args.phase, 'assets': args.assets.split(','),
                                 'probe_mode': 'delta_skip_gate', 'force_execute': False}
    print(json.dumps(document, sort_keys=True))
    return code


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    dsn = os.environ.get('DATABASE_URL')
    if not dsn:
        return _refuse('operation-specific DATABASE_URL is required')
    try:
        if args.operation in REBUILD_OPERATIONS:
            reason = _admit_rebuild(dsn, args)
            return _refuse(reason) if reason else _delegate_rebuild(args)
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
