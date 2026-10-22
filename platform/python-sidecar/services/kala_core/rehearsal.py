"""Passive K9-1 preparation and local, read-only rehearsal evidence inspection.

No dispatch, writer execution, verification receipt, publication or activation is
performed here. The frozen orchestrator and manifest APIs retain those duties.
Grain keys must come from the real upstream plans; this module invents none.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from uuid import UUID

import psycopg
from psycopg.pq import TransactionStatus
from psycopg.rows import dict_row, tuple_row

from pipeline.orchestrator.runner import validate_frozen_run_manifest
from pipeline.orchestrator.service_probes import run_health_probe
from services.kala_core.publication_admission import derived_waves, merge_edges, order_violations, plan_gaps, upstream_of


# PLAN §4.1 / §6.4: the replaceable layer roster. The chart-independent sky has no separate registry id: the judge owns its
# grains. Registrar issuance is delivery-only and is never in this replaceable set.
# K9 r4: ka_gochara_resonance sits between ka_yojaka (its dependency) and the writers that read it
# (ka_gochara_v5, ka_sangam, ka_vighnakara, ka_kshetra); leaving it out of the plan lets the transit
# writers run against a stale resonance map. The registry edges are in migration 1392.
# SR-K9-WAVE-ORDER: this is a SET. The order and the waves are derived from the registry ``depends_on`` (``derived_waves``) and
# pinned into the plan as ``registry_edges``; there is no hand-listed order here to disagree with the registry (the old list
# placed ka_vighnakara ahead of ka_sangam, and ka_sangam ahead of ka_muhurta_seva, against both declared edges).
ROSTER = frozenset((
    'ka_dasha_kala', 'ka_vedha_gochara', 'ka_moorti_nirnaya', 'ka_kota_chakra', 'ka_tithi_pravesha', 'ka_sudarshana_varsha',
    'ka_yojaka', 'ka_gochara_resonance', 'ka_avadhi', 'ka_gochara_v5', 'ka_vighnakara', 'ka_sangam', 'ka_kshetra',
    'ka_kalasutra', 'ka_kala_darshana', 'ka_taranga', 'ka_jivana_parva',
    'ka_tulana', 'ka_muhurta_seva', 'ka_graha_sancara',
))
# The stages and read models that need an explicit grain plan: the roster less the first-level readers and the delivery tail.
MATERIALIZED = frozenset((
    'ka_yojaka', 'ka_gochara_resonance', 'ka_avadhi', 'ka_gochara_v5', 'ka_vighnakara', 'ka_sangam', 'ka_kshetra',
    'ka_kalasutra', 'ka_kala_darshana', 'ka_taranga', 'ka_jivana_parva',
))
_INPUTS = ('lane', 'chart_id', 'generation', 'build_id', 'expected_head_generation',
           'model_digest', 'rule_registry_version', 'conventions', 'grains_by_asset', 'registry_edges')


def order_edges(edges: dict) -> dict[str, list[str]]:
    """The registry ``depends_on`` that bears on the roster's order: the roster and every unplanned asset between two of its
    members, each with its dependencies among those. Idempotent, so a pinned copy re-prepares to itself."""
    if (not isinstance(edges, dict) or any(not isinstance(deps, list) or any(not isinstance(dep, str) for dep in deps)
                                           for deps in edges.values())):
        raise ValueError('registry_edges must map each asset id to its depends_on list')
    if not ROSTER <= set(edges):
        raise ValueError('registry_edges lacks roster assets: ' + ', '.join(sorted(ROSTER - set(edges))))
    relevant = set(ROSTER) | {middle for middle, _, _ in plan_gaps(edges, sorted(ROSTER))}
    return {asset: sorted(dep for dep in set(edges[asset]) if dep in relevant) for asset in sorted(relevant)}


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def prepare_rehearsal(*, lane: str, chart_id: str, generation: str, build_id: str,
                      expected_head_generation: str | None, model_digest: str,
                      rule_registry_version: str, conventions: dict,
                      grains_by_asset: dict[str, list[str]], registry_edges: dict[str, list[str]]) -> dict:
    """Prepare an inert request for the existing cockpit runs API.

    The request is NOT submitted. Candidate opening and its pins remain a
    separately gated prerequisite; the request API has no candidate arguments.
    """
    if not re.fullmatch(r'[a-z][a-z0-9_]{0,39}', lane):
        raise ValueError('lane must be a bounded database suffix')
    UUID(chart_id)
    UUID(build_id)
    if (not generation or generation == 'current' or generation == expected_head_generation
            or not model_digest or not rule_registry_version or not conventions):
        raise ValueError('new candidate identity and all input pins are required')
    edges = order_edges(registry_edges)
    waves = derived_waves(edges, sorted(ROSTER), close=False)
    if set(grains_by_asset) != MATERIALIZED:
        raise ValueError('every materialized stage/read model needs its explicit grain plan')
    if any(not isinstance(values, list) or not values for values in grains_by_asset.values()):
        raise ValueError('each grain plan must be a nonempty list')
    grains = [grain for values in grains_by_asset.values() for grain in values]
    if (any(not isinstance(grain, str) or not grain.strip() for grain in grains)
            or len(set(grains)) != len(grains)):
        raise ValueError('grain keys must be nonempty and unique across the layer')
    pins = dict(lane=lane, chart_id=chart_id, generation=generation, build_id=build_id,
                expected_head_generation=expected_head_generation, model_digest=model_digest,
                rule_registry_version=rule_registry_version, conventions=conventions,
                grains_by_asset=grains_by_asset, registry_edges=edges)
    return deepcopy(dict(
        schema='kala.rehearsal/1', status='prepared', **pins,
        request=dict(chart_id=chart_id, scope='asset_set', scope_target=','.join(asset for wave in waves for asset in wave),
                     action='rebuild', clear_before=False),
        waves=waves,
        operational_rehearsal_passed=None, publication_path_verified=None,
    ))


def _local_target(conn: Any, plan: dict, allow_fixture: bool) -> tuple[str, bool]:
    # Check the connection endpoint before querying even metadata. No DSN is
    # accepted, logged, resolved from environment, or opened by this module.
    host, port = conn.info.host, conn.info.port
    if (host, port) not in {('127.0.0.1', 55433), ('localhost', 5432)}:
        raise ValueError('rehearsal requires the local lane or CI endpoint')
    name = conn.info.dbname
    fixture = allow_fixture and re.fullmatch(r'kala_ci_[0-9a-f]{32}', name) is not None
    if not fixture and (name != 'ky_' + plan['lane'] or port != 55433):
        raise ValueError('connection does not name the requested lane database')
    return name, bool(fixture)


def audit_rehearsal(conn: Any, plan: dict, *, allow_fixture: bool = False) -> dict:
    """Measure a committed local build in one repeatable, read-only snapshot.

    Registry detectors run inside savepoints, so a missing relation or a
    mutating detector yields an explicit failure, never a green fallback.
    The caller must supply an idle connection; its existing transaction is
    never committed or rolled back. Historical dispatch/publish code execution
    cannot be established from table readback and stays honestly null.
    """
    if prepare_rehearsal(**{key: plan[key] for key in _INPUTS}) != plan:
        raise ValueError('prepared rehearsal contract was changed')
    if conn.info.transaction_status != TransactionStatus.IDLE:
        raise ValueError('audit requires an idle connection, not a caller transaction')
    database, fixture = _local_target(conn, plan, allow_fixture)
    with conn.transaction():
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        with conn.cursor(row_factory=dict_row) as cur:
            return _audit_snapshot(conn, cur, plan, database, fixture)


def _audit_snapshot(conn: Any, cur: Any, plan: dict, database: str, fixture: bool) -> dict:
    failures: list[str] = []
    lineage: list[dict] = []

    def fail(message: str) -> None:
        failures.append(message)

    cur.execute('''SELECT id, chart_id, scope, scope_target, action, state, plan,
                          plan_manifest, plan_manifest_digest FROM build_runs WHERE id=%s''',
                (plan['build_id'],))
    run = cur.fetchone()
    frozen = None
    if run is None:
        fail('build run missing')
    else:
        try:
            frozen = validate_frozen_run_manifest(run)
        except ValueError as exc:
            fail(str(exc))
        if (str(run['chart_id']) != plan['chart_id'] or run['action'] != 'rebuild'
                or run['state'] != 'completed' or run['scope'] != 'asset_set'
                or run['scope_target'] != plan['request']['scope_target']):
            fail('run identity, rebuild scope or completion does not match')
        if frozen is not None:
            flattened = frozen.plan
            if set(flattened) != set(ROSTER):
                fail('frozen plan does not contain exactly the replaceable layer roster')
            else:
                # Order truth is the registry depends_on: the pinned preparation edges and the edges the run was frozen with.
                wrong = order_violations(merge_edges(plan['registry_edges'], frozen.asset_deps), flattened)
                if wrong:
                    fail('frozen plan violates stage order: ' + ', '.join(f'{dep} must precede {asset}' for dep, asset in wrong))

    cur.execute('''SELECT * FROM kala_layer_candidate
                   WHERE chart_id=%s AND generation=%s''', (plan['chart_id'], plan['generation']))
    candidate = cur.fetchone()
    if candidate is None or any(
        (str(candidate[key]) if key == 'build_id' else candidate[key]) != plan[key]
        for key in ('build_id', 'expected_head_generation', 'model_digest', 'rule_registry_version', 'conventions')
    ):
        fail('candidate binding or pinned inputs do not match')
    if candidate is not None and candidate['state'] not in {'building', 'complete', 'verified', 'published'}:
        fail('candidate is rejected')

    cur.execute('SELECT * FROM build_run_assets WHERE run_id=%s', (plan['build_id'],))
    runs = cur.fetchall()
    by_asset = {row['asset_id']: row for row in runs}
    if len(runs) != len(ROSTER) or set(by_asset) != set(ROSTER):
        fail('per-run writer results are missing, duplicated or extra')
    union = merge_edges(plan['registry_edges'], frozen.asset_deps if frozen is not None else {})
    for asset in sorted(ROSTER):
        observed = by_asset.get(asset)
        if (observed is None or observed['state'] != 'complete'
                or observed['started_at'] is None or observed['ended_at'] is None
                or observed['ended_at'] < observed['started_at']):
            fail(asset + ': writer did not complete with measured timestamps')
            continue
        for upstream in sorted(upstream_of(union, asset) & set(ROSTER)):
            before = by_asset.get(upstream)
            if (before is not None and before['ended_at'] is not None
                    and observed['started_at'] < before['ended_at']):
                fail(asset + ': writer started before its upstream ' + upstream + ' completed')

    for asset in sorted(ROSTER):
        cur.execute('SELECT asset_kind, integrity_check_sql, health_probe FROM asset_registry WHERE asset_id=%s', (asset,))
        registry = cur.fetchone()
        service = registry is not None and registry['asset_kind'] == 'service'
        scope_chart = None if frozen is not None and frozen.asset_scopes.get(asset) == 'global' else plan['chart_id']
        cur.execute('SELECT state FROM asset_throughput WHERE chart_id IS NOT DISTINCT FROM %s AND asset_id=%s',
                    (scope_chart, asset))
        throughput = cur.fetchone()
        if throughput is None or throughput['state'] not in ({'lit', 'service_ok'} if service else {'lit'}):
            fail(asset + ': throughput is not built')
        detector: dict = dict(passed=None)
        try:
            if registry is None:
                fail(asset + ': registry detector missing')
            elif service:
                measured = run_health_probe(asset, registry['health_probe'])
                checks = measured.get('checks')
                detector = dict(kind='health_probe', contract_digest=_digest(registry['health_probe']),
                                measured=measured, passed=measured.get('status') == 'GREEN'
                                and bool(checks) and all(check.get('passed') is True for check in checks))
            elif registry['integrity_check_sql']:
                with conn.transaction():
                    # Unparameterised first-column truth is the frozen registry
                    # integrity contract (PLAN §4.3), not a row-presence proxy.
                    with conn.cursor(row_factory=tuple_row) as detector_cursor:
                        detector_cursor.execute(registry['integrity_check_sql'])
                        result = detector_cursor.fetchone()
                detector = dict(kind='integrity_sql', contract_digest=_digest(registry['integrity_check_sql']),
                                passed=result is not None and bool(result[0]))
        except (psycopg.Error, ValueError, TypeError) as exc:
            # Do not serialize DB exception text: it can contain query values.
            detector = dict(passed=False, error_type=type(exc).__name__)
        if detector['passed'] is not True:
            fail(asset + ': own detector is absent or did not pass')
        cur.execute('''SELECT partition_key, code_digest, config_digest, upstream_digest,
                              partition_digest, output_digest, upstream_receipts, receipt_state, unknown_reasons
                       FROM asset_provenance_receipts
                       WHERE chart_id IS NOT DISTINCT FROM %s AND asset_id=%s AND build_id=%s ORDER BY partition_key''',
                    (scope_chart, asset, plan['build_id']))
        receipts = cur.fetchall()
        if not receipts or any(
            row['receipt_state'] != 'proven' or row['unknown_reasons']
            or any(not row[key] for key in ('partition_key', 'code_digest', 'config_digest',
                                            'upstream_digest', 'partition_digest', 'output_digest'))
            or frozen is None or row['code_digest'] != frozen.expected_code_digests.get(asset)
            for row in receipts
        ):
            fail(asset + ': current build lineage is missing, unknown or uses another code digest')
        freshness = []
        if not service:
            cur.execute('''SELECT partition_key, freshness_state, reasons FROM asset_freshness
                           WHERE chart_id IS NOT DISTINCT FROM %s AND asset_id=%s ORDER BY partition_key''',
                        (scope_chart, asset))
            freshness = cur.fetchall()
            if ({row['partition_key'] for row in freshness} != {row['partition_key'] for row in receipts}
                    or any(row['freshness_state'] != 'fresh' or row['reasons'] for row in freshness)):
                fail(asset + ': data freshness does not attest the current lineage partitions')
        lineage.append(dict(asset_id=asset, detector=detector, receipts=receipts, freshness=freshness))

    cur.execute('''SELECT grain_key, result_state, input_vector FROM kala_layer_candidate_grain
                   WHERE chart_id=%s AND generation=%s ORDER BY grain_key''',
                (plan['chart_id'], plan['generation']))
    grains = cur.fetchall()
    expected = {grain for values in plan['grains_by_asset'].values() for grain in values}
    if ({row['grain_key'] for row in grains} != expected
            or any(row['result_state'] not in {'rows', 'zero_rows'} or not row['input_vector'] for row in grains)):
        fail('candidate grain plan is incomplete, failed or changed')
    input_digest = _digest([(row['grain_key'], row['input_vector']) for row in grains])
    cur.execute('''SELECT verifier_principal, result, detail FROM kala_layer_verification
                   WHERE chart_id=%s AND generation=%s''', (plan['chart_id'], plan['generation']))
    verification = cur.fetchone()
    accepted = (verification is not None and verification['verifier_principal'] == 'verifier_principal'
                and verification['result'] == 'accepted'
                and verification['detail'].get('input_digest') == input_digest)
    if verification is not None and not accepted:
        fail('verification is rejected or does not attest current grain inputs')
    cur.execute('SELECT generation FROM kala_layer_head WHERE chart_id=%s', (plan['chart_id'],))
    head = cur.fetchone()
    published = None if head is None else head['generation']
    is_published = candidate is not None and candidate['state'] == 'published'
    if published != (plan['generation'] if is_published else plan['expected_head_generation']):
        fail('published head moved outside the expected candidate transition')
    if is_published and not accepted:
        fail('published candidate lacks current independent verification')
    # SR-W56-S3: the named L1 mudda boundary overlaps the dasha readers blank, counted from the governed read (disclosure only: not a gate)
    from services.gochara_kernel.dasha_read import mudda_overlap_disclosure
    status = ('incomplete' if failures else
              ('fixture_passed' if fixture else 'published') if is_published else
              'awaiting_publication' if accepted else 'awaiting_verification')
    return dict(schema='kala.rehearsal/1', status=status, database=database, fixture=fixture,
                chart_id=plan['chart_id'], build_id=plan['build_id'], generation=plan['generation'],
                request=plan['request'], failures=failures, lineage=lineage, grains=grains,
                candidate_input_digest=input_digest, published_generation=published,
                verification=verification, operational_rehearsal_passed=None,
                publication_path_verified=None, clear_before_verified=None,
                mudda_boundary_overlap=mudda_overlap_disclosure(conn, plan['chart_id']))


def main() -> int:
    """Offline preparation only: caller chooses files; no database or network."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path, required=True, help='explicit input pins and upstream grain plans')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = prepare_rehearsal(**json.loads(args.prepare.read_text()))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
