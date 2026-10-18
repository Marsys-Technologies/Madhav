#!/usr/bin/env python3
"""rollback_head (J-6r): restore the canonical chart's RETAINED previous head after a publish_head. Never DELETE-to-v1.

Executor binding: `rollback_head` runs `--execute --generation P --expected-head C`;
`rollback_head_dryrun` runs the same script with `--dry-run` (read-only transaction, zero writes).
`C` is the head that must be current (compare-and-swap); `P` must be the previous head that the current head's
`evidence_ref` records (`...;previous:P`, written by publish_head) and must still hold rows. A head with no such record
(a rollback already done, or a head not set by publish_head) is refused. Contract: head_ops.py.
Exit 0 done, 8 refused (nothing committed), 2 bad arguments.

(I) INTERPRETATION: the restored row carries fresh audit values (flipped_at/by, `evidence_ref = rollback-from:<C>;...`);
the previous row's original audit values stay in the publish receipt. Alternative: persist them in a retained-head table.
(I) INTERPRETATION: a rollback to a LEGACY generation (3.0, v1) cannot read back through the serving reader here (the
legacy transport is not in this script), so `served` is null with a stated reason, never a fabricated check; a governed
target is read back through the J-6a reader.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from . import head_ops as ops      # imported as scripts.kala_gochara_cutover.<name> (tests)
except ImportError:                    # run as a file by the executor: the sibling module is next to this script
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import head_ops as ops  # noqa: E402

KIND = 'rollback_head'


def build_parser(parser):
    parser.add_argument('--generation', required=True)
    parser.add_argument('--expected-head', required=True)
    return parser


def _manifest_of(evidence_ref):
    return (evidence_ref or '').partition(';')[0].removeprefix('manifest:') or None


def perform(conn, args, mode, op_id):
    chart = ops.CANONICAL_CHART
    if not (ops.GENERATION.fullmatch(args.generation) and ops.GENERATION.fullmatch(args.expected_head)):
        raise ops.HeadRefused('arguments_invalid', 'generation and expected-head must be plain identifiers')
    dry = mode == 'dry_run'
    ops.lock_chart(conn, chart)
    head = ops.read_head(conn, chart, lock=not dry)
    ops.check_expected(head, args.expected_head, args.generation)
    recorded = ops.previous_marker(head.evidence_ref)
    if recorded != args.generation:
        raise ops.HeadRefused('target_is_not_the_recorded_previous_head',
                              f'the current head records previous={recorded!r}, the request names {args.generation!r}')
    retained = ops.retained_target(conn, chart, args.generation)
    before = ops.retained_counts(conn, chart)
    new_by, new_ref = f'{KIND}:{op_id}', f'rollback-from:{head.generation};{head.evidence_ref.partition(";")[0]}'
    record = {'schema': ops.SCHEMA, 'kind': KIND, 'mode': mode, 'operation_id': op_id, 'chart_id': chart,
              'target': {'generation': args.generation, 'retained': retained}, 'expected_head': args.expected_head,
              'previous_head': head.record(), 'retained_row_counts': before}
    if dry:
        record.update(status='DRY_RUN_NO_WRITE', writes=0,
                      read_only_confirmed=conn.execute('SHOW transaction_read_only').fetchone()[0] == 'on',
                      would_write={'authoritative_generation': args.generation, 'flipped_by': new_by, 'evidence_ref': new_ref})
        return record
    new = ops.swap_head(conn, chart, head, args.generation, new_by, new_ref)
    if ops.GOVERNED.fullmatch(args.generation):
        manifest = conn.execute("SELECT manifest_id::text FROM public.kala_gochara_publication WHERE chart_id=%s"
                                " AND generation=%s AND status='published' ORDER BY manifest_id LIMIT 1", (chart, args.generation)).fetchone()
        served = ops.served_identity(conn, chart, args.generation, manifest[0] if manifest else '')
    else:
        served = None
    after = ops.retained_counts(conn, chart)
    if after != before:
        raise ops.HeadRefused('retained_rows_changed', 'chart-scoped row counts differ after the head change')
    record.update(status='HEAD_RESTORED', writes=1, new_head=new.record(), served=served,
                  served_reason=None if served else 'legacy generation: the legacy transport is outside this operation',
                  retained_rows_equal=True, retained_row_counts_after=after)
    return record


def run(argv=None, *, environ=None, conn=None):
    return ops.run_operation(KIND, argv, environ, conn, build_parser, perform)


if __name__ == '__main__':
    raise SystemExit(run())
