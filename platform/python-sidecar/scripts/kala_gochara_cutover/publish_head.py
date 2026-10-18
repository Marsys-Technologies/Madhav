#!/usr/bin/env python3
"""publish_head (J-6m): switch the canonical chart's served head to ONE sealed governed generation, keeping the previous head.

Executor binding: `publish_head` runs `--execute --generation G --manifest-id M --expected-head E`;
`publish_head_dryrun` runs the same script with `--dry-run` (read-only transaction, zero writes).
`E` is the generation the head must be right now (compare-and-swap); the previous head is recorded on the new row
(`evidence_ref = manifest:<M>;previous:<E>`) and its whole row is in the printed receipt. Rollback is `rollback_head`.
Contract, interpretations and the refusal codes: head_ops.py. Exit 0 done, 8 refused (nothing committed), 2 bad arguments.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from . import head_ops as ops      # imported as scripts.kala_gochara_cutover.<name> (tests)
except ImportError:                    # run as a file by the executor: the sibling module is next to this script
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import head_ops as ops  # noqa: E402

KIND = 'publish_head'


def build_parser(parser):
    parser.add_argument('--generation', required=True)
    parser.add_argument('--manifest-id', required=True)
    parser.add_argument('--expected-head', required=True)
    return parser


def perform(conn, args, mode, op_id):
    chart = ops.CANONICAL_CHART
    if not (ops.GENERATION.fullmatch(args.generation) and ops.GENERATION.fullmatch(args.expected_head)
            and ops.UUID.fullmatch(args.manifest_id)):
        raise ops.HeadRefused('arguments_invalid', 'generation, expected-head and manifest-id must be plain identifiers')
    dry = mode == 'dry_run'
    ops.lock_chart(conn, chart)
    head = ops.read_head(conn, chart, lock=not dry)
    ops.check_expected(head, args.expected_head, args.generation)
    ops.sealed_target(conn, chart, args.generation, args.manifest_id)
    before = ops.retained_counts(conn, chart)
    new_by, new_ref = f'{KIND}:{op_id}', f'manifest:{args.manifest_id};previous:{head.generation}'
    record = {'schema': ops.SCHEMA, 'kind': KIND, 'mode': mode, 'operation_id': op_id, 'chart_id': chart,
              'target': {'generation': args.generation, 'manifest_id': args.manifest_id},
              'expected_head': args.expected_head, 'previous_head': head.record(), 'retained_row_counts': before}
    if dry:
        record.update(status='DRY_RUN_NO_WRITE', writes=0,
                      read_only_confirmed=conn.execute('SHOW transaction_read_only').fetchone()[0] == 'on',
                      would_write={'authoritative_generation': args.generation, 'flipped_by': new_by, 'evidence_ref': new_ref},
                      served_preview=ops.served_preview(conn, chart, args.generation, args.manifest_id))
        return record
    new = ops.swap_head(conn, chart, head, args.generation, new_by, new_ref)
    served = ops.served_identity(conn, chart, args.generation, args.manifest_id)
    after = ops.retained_counts(conn, chart)
    if after != before:
        raise ops.HeadRefused('retained_rows_changed', 'chart-scoped row counts differ after the head change')
    record.update(status='HEAD_PUBLISHED', writes=1, new_head=new.record(), served=served,
                  retained_rows_equal=True, retained_row_counts_after=after)
    return record


def run(argv=None, *, environ=None, conn=None):
    return ops.run_operation(KIND, argv, environ, conn, build_parser, perform)


if __name__ == '__main__':
    raise SystemExit(run())
