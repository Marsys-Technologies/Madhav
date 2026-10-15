"""J-6r transactional pre-build rehearsal; never an executor or acceptance receipt.

PLAN (KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1) §4.4.6 requires compare-and-swap
back to a retained head. G6 additionally requires actual serving/rollback and
independent, exact-generation acceptance. This module prepares the local DB
probe, not that acceptance: it neither connects, writes an artifact, commits,
nor enables a production operation. The caller supplies a guarded lane/test
connection and its real legacy reader. All probes use that connection, so this
does not attest to an HTTP/deployed-image cutover across committed snapshots.

(I) INTERPRETATION: under SR-A4-01 a rolled-back local rehearsal is preparation;
the cockpit still owes the separately accepted J6R_REHEARSAL.json, executor
binding, G8 checks and production enablement in dependency order.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import os
import re
from typing import Any, Callable

from services.gochara_kernel import serving_reader


class RehearsalRefused(RuntimeError):
    """A measured rehearsal pre/postcondition failed; no acceptance is emitted."""


@dataclass(frozen=True)
class Head:
    generation: str
    flipped_at: datetime | None
    flipped_by: str | None
    evidence_ref: str | None


def _require_lane(conn: Any) -> None:
    # A name alone is insufficient (a local proxy can reach production).
    name, address = conn.execute('SELECT current_database(), inet_server_addr()').fetchone()
    if not re.fullmatch(r'(?:a53t_j6r_[0-9a-f]{8}|ky_[a-z0-9_]+)', name):
        raise RehearsalRefused('not_a_lane_database')
    addr = ipaddress.ip_address(str(address)) if address is not None else None
    addr = getattr(addr, 'ipv4_mapped', None) or addr
    ci_bridge = (os.environ.get('GITHUB_ACTIONS') == 'true' and addr is not None and addr.version == 4
                 and any(addr in ipaddress.ip_network(net) for net in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')))
    if addr is not None and not addr.is_loopback and not ci_bridge:
        raise RehearsalRefused('not_a_local_lane_server')


def read_head(conn: Any, chart_id: str) -> Head:
    row = conn.execute('SELECT authoritative_generation, flipped_at, flipped_by, evidence_ref'
                       ' FROM public.kala_gochara_authority WHERE chart_id=%s FOR UPDATE', (chart_id,)).fetchone()
    if row is None:
        raise RehearsalRefused('previous_head_missing')
    return Head(*row)


def compare_and_swap(conn: Any, chart_id: str, expected: Head, replacement: Head) -> None:
    """Change one explicit head, including its audit metadata, or refuse.

    No DELETE/default fallback and no generation-content DML. The caller owns
    the transaction; rollback uses the complete previously observed row.
    """
    _require_lane(conn)
    row = conn.execute(
        'UPDATE public.kala_gochara_authority SET authoritative_generation=%s, flipped_at=%s,'
        ' flipped_by=%s, evidence_ref=%s WHERE chart_id=%s AND'
        ' (authoritative_generation,flipped_at,flipped_by,evidence_ref)'
        ' IS NOT DISTINCT FROM (%s,%s::timestamptz,%s,%s) RETURNING chart_id',
        (replacement.generation, replacement.flipped_at, replacement.flipped_by, replacement.evidence_ref,
         chart_id, expected.generation, expected.flipped_at, expected.flipped_by, expected.evidence_ref)).fetchone()
    if row is None:
        raise RehearsalRefused('head_compare_and_swap_conflict')


# Fingerprint the listed chart-scoped relations, including legacy rows and
# both generations' manifests, seals and stored grains. This is not a database
# backup or an attestation about relations outside this explicit set.
_RETAINED_TABLES = (
    'kala_gochara_publication', 'ka_gochara_generation_seal', 'kala_gochara_windows',
    'kala_gochara_coverage', 'ka_gochara_eval_window', 'ka_gochara_eval_window_record',
    'ka_gochara_relationship_record', 'ka_gochara_contact', 'ka_gochara_search_inventory',
)


def _retained(conn: Any, chart_id: str) -> dict:
    snapshot = {}
    for table in _RETAINED_TABLES:  # fixed identifiers, never caller input
        rows = conn.execute(f'SELECT to_jsonb(t)::text FROM public.{table} t'
                            ' WHERE chart_id=%s ORDER BY to_jsonb(t)::text', (chart_id,)).fetchall()
        digest = hashlib.sha256()
        for (row,) in rows:
            raw = row.encode('utf-8')
            digest.update(len(raw).to_bytes(8, 'big'))
            digest.update(raw)
        snapshot[table] = {'rows': len(rows), 'sha256': digest.hexdigest()}
    return snapshot


def _wire(response: Any) -> bytes:
    # Preserve a legacy transport's exact bytes, including whitespace. V5's
    # JSON envelope has a deterministic encoding for this in-process probe.
    if isinstance(response, bytes) and response:
        return response
    if isinstance(response, dict) and response.get('refusal') is None:
        return json.dumps(response, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    raise RehearsalRefused('reader_refused_or_invalid_response')


def _observed(response: Any, generation: str) -> dict:
    raw = _wire(response)
    return {'generation': generation, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def rehearse(conn: Any, *, chart_id: str, expected_previous: str, generation: str,
             manifest_id: str, legacy_reader: Callable, request: dict | None = None) -> dict:
    """Flip, serve, explicitly CAS back, compare bytes/retention; roll back all.

    Success and failure both discard ONLY this scope via a transaction or
    savepoint, preserving a caller's earlier work. Seals/admission come from
    deployed SQL, never a readiness-only Python substitute for verification.
    """
    _require_lane(conn)
    request = dict(request or {})
    with conn.transaction(force_rollback=True):
        conn.execute('SELECT public.ka_gochara_lock_chart(%s::uuid)', (chart_id,))
        previous = read_head(conn, chart_id)
        if previous.generation != expected_previous or previous.generation == generation:
            raise RehearsalRefused('previous_head_changed')
        target = conn.execute(
            'SELECT p.manifest_id::text, upper(p.horizon) FROM public.kala_gochara_publication p'
            ' JOIN public.ka_gochara_generation_seal s ON s.chart_id=p.chart_id'
            ' AND s.generation=p.generation AND s.manifest_id=p.manifest_id'
            " WHERE p.chart_id=%s AND p.generation=%s AND p.manifest_id=%s::uuid AND p.status='published'"
            " AND coalesce(p.input_generation_vector->>'stored_scope','') <> 'test_slice'"
            " AND NOT (p.input_generation_vector ? 'test_slice')",
            (chart_id, generation, manifest_id)).fetchone()
        if target is None or not re.fullmatch(r'([5-9]|[1-9][0-9]+)\.[0-9]+', generation):
            raise RehearsalRefused('target_not_admissible')
        retained_before = _retained(conn, chart_id)
        before = serving_reader.read_authoritative(conn, chart_id, legacy_reader=legacy_reader, **request)
        before_bytes = _wire(before)
        flipped = Head(generation, datetime.now(timezone.utc), 'J-6r-prebuild', f'manifest:{target[0]}')
        compare_and_swap(conn, chart_id, previous, flipped)
        served = serving_reader.read_authoritative(conn, chart_id, legacy_reader=legacy_reader, **request)
        if (not isinstance(served, dict) or served.get('refusal') is not None
                or served.get('chart_id') != chart_id or served.get('generation') != generation
                or served.get('manifest_id') != target[0]):
            raise RehearsalRefused('flipped_reader_identity_or_admission_failed')
        # The manifest's exclusive upper edge is outside; never invent a date.
        outside = serving_reader.read_authoritative(conn, chart_id, legacy_reader=legacy_reader,
                                                    at_instant=target[1])
        if (outside.get('refusal') or {}).get('code') != 'outside_served_horizon':
            raise RehearsalRefused('outside_horizon_probe_failed')
        retained_after_flip = _retained(conn, chart_id)
        if retained_after_flip != retained_before:
            raise RehearsalRefused('retained_rows_changed')
        compare_and_swap(conn, chart_id, flipped, previous)
        after = serving_reader.read_authoritative(conn, chart_id, legacy_reader=legacy_reader, **request)
        bytes_equal = _wire(after) == before_bytes
        if not bytes_equal:
            raise RehearsalRefused('rollback_response_bytes_changed')
        retained_after_rollback = _retained(conn, chart_id)
        retained_equal = retained_before == retained_after_flip == retained_after_rollback
        if not retained_equal:
            raise RehearsalRefused('retained_rows_changed')
        if read_head(conn, chart_id) != previous:
            raise RehearsalRefused('previous_head_not_restored')
        return {
            'schema': 'ky.j6r_prebuild_rehearsal/1', 'acceptance': None, 'production_activated': False,
            'chart_id': chart_id, 'target': {'generation': generation, 'manifest_id': target[0]},
            'before': _observed(before, previous.generation),
            'flipped': {**_observed(served, generation), 'manifest_id': served['manifest_id'],
                        'class_completeness': {c['event_class']: c['completeness'] for c in served['classes']}},
            'after': _observed(after, previous.generation), 'rollback_bytes_equal': bytes_equal,
            'retained_rows_equal': retained_equal, 'outside_horizon_refusal': outside['refusal']['code'],
            'retained_before': retained_before, 'retained_after_flip': retained_after_flip,
            'retained_after_rollback': retained_after_rollback,
        }
