"""Governed Gochara authority-head operations: the shared core of publish_head (J-6m) and rollback_head (J-6r).

The head is the one `public.kala_gochara_authority` row of the canonical chart. Publishing moves it to a SEALED
governed generation (migration 1379's `ka_gochara_authority_admissible`, the same predicate the database enforces);
rolling back moves it back to the explicit retained previous head recorded by that publish. Neither operation ever
DELETEs, TRUNCATEs or touches a generation's content rows (migrations 1379/1382 refuse those even for the table owner).

Contract, in order (a failed step aborts the transaction and leaves the head untouched):
  1. chart lock (`ka_gochara_lock_chart`) then the head row `FOR UPDATE`; an absent row is refused, never defaulted;
  2. compare-and-swap: the head must equal the request's `expected-head` (the executor request pins it);
  3. publish only: the target (generation AND manifest id) must be published, non-test-slice and sealed;
     rollback only: the target must be the previous head the current head's `evidence_ref` records, and still hold rows;
  4. one UPDATE of the whole audit row, readback of that row, chart-scoped retained-row counts equal before/after;
  5. publish only: the serving reader (J-6a) must resolve the chart to the new generation and manifest without refusal.
A dry run performs 1-3 on a READ ONLY transaction (the database refuses any write) and prints what would be written.

(I) INTERPRETATION: retention evidence is per-table row COUNTS of the chart-scoped relations the J-6r rehearsal
fingerprints, not full-content hashes: hashing every century row inside the production write transaction is
unbounded, and 1379/1382 already make content deletion impossible. Alternative: the rehearsal's sha256 of every row.
(I) INTERPRETATION: the previous head is retained (a) in the new head's `evidence_ref` (`...;previous:<generation>`),
which rollback requires, and (b) as the complete previous row in the receipt. Alternative: a new retained-head table
(needs an allocated migration).
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SIDECAR = Path(__file__).resolve().parents[2]
if str(SIDECAR) not in sys.path:      # standalone script: the serving reader lives in the sidecar's packages
    sys.path.insert(0, str(SIDECAR))

CANONICAL_CHART = '482012f1-710e-4a25-994a-93821f5871aa'
SCHEMA = 'ky.head_operation/1'
GOVERNED = re.compile(r'([5-9]|[1-9][0-9]+)\.[0-9]+')            # the pattern of migrations 1236/1379
GENERATION = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.]{0,31}')
UUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
OPERATION_ID = re.compile(r'[A-Za-z0-9_.-]{1,80}')
# The chart-scoped relations the J-6r rehearsal fingerprints; fixed identifiers, never caller input.
RETAINED_TABLES = (
    'kala_gochara_publication', 'ka_gochara_generation_seal', 'kala_gochara_windows',
    'kala_gochara_coverage', 'ka_gochara_eval_window', 'ka_gochara_eval_window_record',
    'ka_gochara_relationship_record', 'ka_gochara_contact', 'ka_gochara_search_inventory',
)
EXIT_REFUSED = 8


class HeadRefused(Exception):
    """A precondition or measured postcondition failed; `code` is machine-readable, nothing was committed."""

    def __init__(self, code: str, detail: str = ''):
        super().__init__(code if not detail else f'{code}: {detail}')
        self.code = code


@dataclass(frozen=True)
class Head:
    generation: str
    flipped_at: Any
    flipped_by: str | None
    evidence_ref: str | None

    def record(self) -> dict:
        row = asdict(self)
        row['flipped_at'] = None if self.flipped_at is None else self.flipped_at.isoformat()
        return row


def operation_id(environ: dict) -> str:
    """The executor's request names the operation; a head change with no operation to bind is refused."""
    try:
        value = json.loads(environ['KY_OPERATION_REQUEST'])['operation_id']
    except (KeyError, TypeError, ValueError):
        raise HeadRefused('operation_id_missing', 'KY_OPERATION_REQUEST must carry operation_id') from None
    if not isinstance(value, str) or not OPERATION_ID.fullmatch(value):
        raise HeadRefused('operation_id_missing', 'operation_id is not a safe identifier')
    return value


def lock_chart(conn: Any, chart_id: str) -> None:
    conn.execute('SELECT public.ka_gochara_lock_chart(%s::uuid)', (chart_id,))


def read_head(conn: Any, chart_id: str, *, lock: bool) -> Head:
    row = conn.execute('SELECT authoritative_generation, flipped_at, flipped_by, evidence_ref'
                       ' FROM public.kala_gochara_authority WHERE chart_id=%s' + (' FOR UPDATE' if lock else ''),
                       (chart_id,)).fetchone()
    if row is None:
        raise HeadRefused('head_missing', 'no authority row: the absent-row default is never invented')
    return Head(*row)


def check_expected(head: Head, expected: str, target: str) -> None:
    if head.generation != expected:
        raise HeadRefused('head_compare_and_swap_conflict',
                          f'current head is {head.generation!r}, the request expects {expected!r}')
    if target == expected:
        raise HeadRefused('target_is_current_head', 'the target already is the expected head')


def sealed_target(conn: Any, chart_id: str, generation: str, manifest_id: str) -> None:
    """The exact (generation, manifest) must be published, non-test-slice and sealed - the columns of 1379's predicate -
    AND the database's own predicate must agree."""
    if not GOVERNED.fullmatch(generation):
        raise HeadRefused('target_not_admissible', 'publish_head serves governed (major >= 5) generations only')
    row = conn.execute(
        'SELECT 1 FROM public.kala_gochara_publication p'
        ' JOIN public.ka_gochara_generation_seal s ON s.chart_id=p.chart_id'
        ' AND s.generation=p.generation AND s.manifest_id=p.manifest_id'
        " WHERE p.chart_id=%s AND p.generation=%s AND p.manifest_id=%s::uuid AND p.status='published'"
        " AND coalesce(p.input_generation_vector->>'stored_scope','') <> 'test_slice'"
        " AND NOT (p.input_generation_vector ? 'test_slice')", (chart_id, generation, manifest_id)).fetchone()
    admissible = conn.execute('SELECT public.ka_gochara_authority_admissible(%s::uuid, %s)',
                              (chart_id, generation)).fetchone()[0]
    if row is None or admissible is not True:
        raise HeadRefused('target_not_admissible', 'no published, non-test-slice, sealed manifest for this generation')


def previous_marker(evidence_ref: str | None) -> str | None:
    match = re.search(r';previous:([^;]+)(?:;|\Z)', evidence_ref or '')
    return match.group(1) if match else None


def retained_target(conn: Any, chart_id: str, generation: str) -> dict:
    """A rollback target must still be serveable: legacy generations hold windows; governed ones a sealed manifest."""
    if GOVERNED.fullmatch(generation):
        admissible = conn.execute('SELECT public.ka_gochara_authority_admissible(%s::uuid, %s)',
                                  (chart_id, generation)).fetchone()[0]
        if admissible is not True:
            raise HeadRefused('retained_head_not_admissible', f'{generation} no longer has a sealed published manifest')
        return {'generation': generation, 'basis': 'sealed_manifest'}
    rows = conn.execute('SELECT count(*) FROM public.kala_gochara_windows WHERE chart_id=%s AND generation=%s',
                        (chart_id, generation)).fetchone()[0]
    if rows == 0:
        raise HeadRefused('retained_head_has_no_rows', f'no kala_gochara_windows rows at {generation}: not a rollback target')
    return {'generation': generation, 'basis': 'windows', 'windows_rows': rows}


def retained_counts(conn: Any, chart_id: str) -> dict:
    return {table: conn.execute(f'SELECT count(*) FROM public.{table} WHERE chart_id=%s', (chart_id,)).fetchone()[0]
            for table in RETAINED_TABLES}


def swap_head(conn: Any, chart_id: str, expected: Head, generation: str, flipped_by: str, evidence_ref: str) -> Head:
    """Change the whole audit row or refuse; the old row is matched in full so a concurrent writer is never overwritten."""
    row = conn.execute(
        'UPDATE public.kala_gochara_authority SET authoritative_generation=%s, flipped_at=now(), flipped_by=%s,'
        ' evidence_ref=%s WHERE chart_id=%s AND (authoritative_generation,flipped_at,flipped_by,evidence_ref)'
        ' IS NOT DISTINCT FROM (%s,%s::timestamptz,%s,%s)'
        ' RETURNING authoritative_generation, flipped_at, flipped_by, evidence_ref',
        (generation, flipped_by, evidence_ref, chart_id,
         expected.generation, expected.flipped_at, expected.flipped_by, expected.evidence_ref)).fetchone()
    if row is None:
        raise HeadRefused('head_compare_and_swap_conflict', 'the head row changed under the lock')
    new = Head(*row)
    if read_head(conn, chart_id, lock=False) != new or new.generation != generation:
        raise HeadRefused('head_readback_mismatch', 'the row read back is not the row written')
    return new


def _no_legacy_reader(*_args, **_kwargs):
    raise HeadRefused('legacy_reader_reached', 'a governed head must never dispatch to the legacy reader')


def _identity(served: Any, generation: str, manifest_id: str) -> dict:
    if (not isinstance(served, dict) or served.get('refusal') is not None
            or served.get('generation') != generation or served.get('manifest_id') != manifest_id):
        refusal = served.get('refusal') if isinstance(served, dict) else None
        code = refusal.get('code') if isinstance(refusal, dict) else None
        raise HeadRefused('served_identity_or_admission_failed', f'reader refusal {code!r}')
    return {'generation': generation, 'manifest_id': manifest_id, 'refusal': None}


def served_identity(conn: Any, chart_id: str, generation: str, manifest_id: str) -> dict:
    """The J-6a reader, on this transaction, must resolve the chart (via the authority row) to the new head."""
    from services.gochara_kernel import serving_reader
    served = serving_reader.read_authoritative(conn, chart_id, legacy_reader=_no_legacy_reader)
    if isinstance(served, dict) and served.get('chart_id') not in (None, chart_id):
        raise HeadRefused('served_identity_or_admission_failed', 'reader answered for another chart')
    return _identity(served, generation, manifest_id)


def served_preview(conn: Any, chart_id: str, generation: str, manifest_id: str) -> dict:
    """Dry run: the explicit-generation read of the target on the read-only snapshot (no flip needed)."""
    from services.gochara_kernel import serving_reader
    return _identity(serving_reader.read_v5(conn, chart_id, generation), generation, manifest_id)


def connect(environ: dict, *, read_only: bool) -> Any:
    import psycopg
    dsn = environ.get('DATABASE_URL')
    if not dsn:
        raise HeadRefused('database_url_missing', 'the executor supplies DATABASE_URL')
    conn = psycopg.connect(dsn, autocommit=True)
    conn.read_only = read_only      # the database itself refuses any write of a dry run
    return conn


def emit(record: dict) -> None:
    print(json.dumps(record, sort_keys=True, indent=1, allow_nan=False))


def refusal_record(kind: str, mode: str, exc: HeadRefused, op_id: str | None) -> dict:
    return {'schema': SCHEMA, 'kind': kind, 'mode': mode, 'status': 'REFUSED', 'refusal': exc.code,
            'detail': str(exc), 'writes': 0, 'operation_id': op_id, 'chart_id': CANONICAL_CHART}


def parse_common(parser: Any, argv: list[str] | None, environ: dict | None):
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args(argv)
    if args.dry_run == args.execute:      # exactly one: a write is only ever asked for explicitly
        parser.error('exactly one of --dry-run and --execute is required')
    return args, ('execute' if args.execute else 'dry_run'), dict(os.environ if environ is None else environ)


def run_operation(kind: str, argv: list[str] | None, environ: dict | None, conn: Any, build_parser, perform) -> int:
    """Shared CLI shell: parse, connect (read-only for a dry run), run `perform(conn, args, mode, op_id)` in one
    transaction, print one JSON record. A refusal prints a REFUSED record and exits 8; nothing is committed."""
    import argparse
    parser = build_parser(argparse.ArgumentParser(description=__doc__, allow_abbrev=False))
    args, mode, env = parse_common(parser, argv, environ)
    op_id = None
    own = conn is None
    previous_read_only = None if own else conn.read_only
    try:
        op_id = operation_id(env)
        if own:
            conn = connect(env, read_only=(mode == 'dry_run'))
        else:
            conn.read_only = (mode == 'dry_run')
        with conn.transaction():
            record = perform(conn, args, mode, op_id)
        emit(record)
        return 0
    except HeadRefused as exc:
        emit(refusal_record(kind, mode, exc, op_id))
        return EXIT_REFUSED
    except Exception as exc:      # a database-side refusal (trigger / CHECK) is a refusal too; anything else propagates
        sqlstate = getattr(exc, 'sqlstate', None)
        if sqlstate is None:
            raise
        emit(refusal_record(kind, mode, HeadRefused('database_refused', f'SQLSTATE {sqlstate}'), op_id))
        return EXIT_REFUSED
    finally:
        if own and conn is not None:
            conn.close()
        elif not own:
            conn.read_only = previous_read_only
