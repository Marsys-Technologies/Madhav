"""K9-4a/b offline preparation and executor readback inspection.

No connections, subprocesses, request submission, verification writes or authority
switches. K9-23 owns execution. An imported readback is inspection evidence, not
an authenticated executor receipt or independent semantic acceptance.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from uuid import UUID

from pipeline.orchestrator.runner import validate_frozen_run_manifest
from services.kala_core.rehearsal import ASSETS, WAVES, _INPUTS, prepare_rehearsal

CANONICAL_CHART = '482012f1-710e-4a25-994a-93821f5871aa'
PUBLICATION_MODULE = 'services.kala_core.publication'
PUBLICATION_SOURCE = 'bc590494f9a1f4db69cae23f8f935462832fd9a5'
G8_MISSING = ['live exclusive lease', 'backup snapshot receipt', 'verified restore receipt',
              'accepted execution dry run (PLAN_ONLY does not qualify)', 'single build slot',
              'request-bound independent pre-acceptance', 'reviewed head merged on main',
              'complete K9-5 census and independently authored full expectations',
              'independent semantic verification for every writer']


def _require(test, message):
    if not test:
        raise ValueError(message)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _generation(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', value) and value not in {'NONE', 'current'}


def prepare(plan: dict, frozen_run: dict) -> dict:
    """Pin exact K9-1 scope and every K9-23 publication grain; generate inert templates.

    (I) INTERPRETATION: services/adapters also need caller-supplied publication
    grains because K9-23 requires one plan entry per frozen writer. No observed
    row or guessed default can supply a missing plan.
    """
    _require(prepare_rehearsal(**{key: plan[key] for key in _INPUTS}) == plan,
             'K9-1 preparation was modified')
    _require(plan['chart_id'] == CANONICAL_CHART, 'canonical chart only')
    _require(_generation(plan['generation']), 'candidate generation is reserved or unsafe')
    previous = plan['expected_head_generation']
    _require(previous is None or _generation(previous), 'previous head is reserved or unsafe')
    frozen = validate_frozen_run_manifest(frozen_run)
    _require(len(frozen.plan) == len(ASSETS) and set(frozen.plan) == set(ASSETS), 'complete full-layer roster required')
    _require(str(frozen_run['id']) == plan['build_id'] and str(frozen_run['chart_id']) == CANONICAL_CHART
             and frozen_run['action'] == 'rebuild' and frozen_run['scope'] == 'asset_set'
             and frozen_run['scope_target'] == plan['request']['scope_target'], 'frozen run identity/scope differs')
    grains = plan['conventions'].get('publication_grains')
    _require(isinstance(grains, dict) and set(grains) == set(ASSETS), 'publication grains must cover all 20 writers')
    keys = []
    for aid, values in grains.items():
        _require(isinstance(values, list) and bool(values), 'every writer needs explicit publication grains')
        _require(all(isinstance(key, str) and (key == aid or key.startswith(aid + ':')) for key in values),
                 'publication grain must identify its own writer')
        keys.extend(values)
    _require(len(keys) == len(set(keys)), 'publication grains must be unique')
    for aid, values in plan['grains_by_asset'].items():
        _require(values == grains[aid], 'materialized grain plan differs from publication plan')
    # validate_frozen_run_manifest checks each wave/asset binding. Additionally
    # prohibit a valid digest over a different semantic ordering.
    levels = {aid: i for i, wave in enumerate(WAVES) for aid in wave}
    observed = [[levels[aid] for aid in wave] for wave in frozen_run['plan_manifest']['waves'] if wave]
    _require(all(len(set(wave)) == 1 for wave in observed)
             and all(max(a) <= min(b) for a, b in zip(observed, observed[1:])), 'frozen waves violate stage order')
    # (I) INTERPRETATION: preserve the actual frozen order within a dependency
    # wave; K9-1 imposes stage order, not a second scheduler for peer writers.
    expected_head = previous if previous is not None else 'NONE'
    common = {'run-id': plan['build_id']}
    operations = []
    for kind, operation, args, needs, missing in [
        ('backup_snapshot', None, {}, 'owner', ['backup label']),
        ('backup_restore_verify', None, {}, 'owner', ['backup label']),
        ('orchestrator_rebuild_dryrun', 'rebuild-dryrun', dict(common, assets=','.join(frozen.plan)), 'builder', []),
        ('orchestrator_rebuild', 'rebuild', dict(common, assets=','.join(frozen.plan)), 'builder', []),
        ('readback_sql', None, {}, 'pgenv', ['executor sql_file path']),
        ('layer_verify', 'verify', dict(common, generation=plan['generation']), 'layer_verifier', ['independently-derived-digest']),
        ('layer_publish', 'publish', dict(common, generation=plan['generation'], **{'expected-head': expected_head}), 'builder', []),
        ('publication_readback', None, {}, 'pgenv', ['executor sql_file path']),
    ]:
        operations.append(dict(kind=kind, executor_kind='readback_sql' if kind == 'publication_readback' else kind,
            enabled=False, request=None, module=PUBLICATION_MODULE if operation else None,
            operation=operation, args=args, needs=needs, missing_inputs=missing,
            admission_missing=list(G8_MISSING) if needs != 'pgenv' else ['independent readback request identity']))
    bundle = dict(schema='kala.final_rebuild/1', status='PREPARATION_ONLY',
        assets=list(frozen.plan), plan=deepcopy(plan), frozen_run=deepcopy(frozen_run),
        candidate={key: deepcopy(plan[key]) for key in ('chart_id','generation','build_id','expected_head_generation',
                                                       'model_digest','rule_registry_version','conventions')},
        publication_grains=deepcopy(grains), operations=operations,
        publication_interface=dict(module=PUBLICATION_MODULE, source_commit=PUBLICATION_SOURCE,
                                   branch='origin/kalayantra/k9-23', binding_status='BRANCH_INTERFACE_REQUIRES_REQUALIFICATION'),
        dry_run_passed=None, production_acceptance=None,
        rollback=dict(enabled=False, request=None, module=PUBLICATION_MODULE, operation='rollback',
                      args=None if previous is None else {'generation': previous, 'expected-head': plan['generation']},
                      missing='no previous head exists' if previous is None else 'G8 admission and retained-head readback'))
    bundle['readback_sql'] = _readback_sql(bundle)
    bundle['preparation_sha256'] = _digest(bundle)
    return bundle


def _readback_sql(bundle):
    """One read-only SELECT for executor readback_sql; no psql commands or binds."""
    candidate = bundle['candidate']
    run = str(UUID(candidate['build_id']))
    generation = candidate['generation']  # bounded by prepare(), never raw SQL input
    chart = CANONICAL_CHART
    previous = candidate['expected_head_generation']
    previous_sql = 'NULL' if previous is None else "'" + previous + "'"
    return f"""SELECT jsonb_build_object(
      'run', (SELECT to_jsonb(r) FROM build_runs r WHERE r.id='{run}'::uuid),
      'writers', COALESCE((SELECT jsonb_agg(to_jsonb(w) ORDER BY w.asset_id)
          FROM build_run_assets w WHERE w.run_id='{run}'::uuid), '[]'::jsonb),
      'candidate', (SELECT to_jsonb(c) FROM kala_layer_candidate c
          WHERE c.chart_id='{chart}'::uuid AND c.generation='{generation}'),
      'grains', COALESCE((SELECT jsonb_agg(to_jsonb(g) ORDER BY g.grain_key)
          FROM kala_layer_candidate_grain g WHERE g.chart_id='{chart}'::uuid AND g.generation='{generation}'), '[]'::jsonb),
      'verification', (SELECT to_jsonb(v) FROM kala_layer_verification v
          WHERE v.chart_id='{chart}'::uuid AND v.generation='{generation}'),
      'head', (SELECT generation FROM kala_layer_head WHERE chart_id='{chart}'::uuid),
      'retained', (SELECT to_jsonb(c) FROM kala_layer_candidate c
          WHERE c.chart_id='{chart}'::uuid AND c.generation={previous_sql})
    ) AS evidence"""


def inspect_readback(bundle: dict, evidence: dict, *, phase: str) -> dict:
    """Compare a captured executor SQL payload with its pre-build pins.

    Does not authenticate the file or issue acceptance. Input verification and
    writer completion remain distinct from all-writer semantic verification.
    """
    _require(prepare(bundle['plan'], bundle['frozen_run']) == bundle, 'preparation binding differs')
    _require(phase in {'rebuilt', 'verified', 'published'}, 'unknown readback phase')
    plan = bundle['plan']
    run = evidence.get('run')
    _require(isinstance(run, dict), 'run readback is absent')
    validate_frozen_run_manifest(run)
    for key in ('id', 'chart_id', 'scope', 'scope_target', 'action', 'plan', 'plan_manifest', 'plan_manifest_digest'):
        _require(run.get(key) == bundle['frozen_run'][key], 'run identity or frozen plan changed: ' + key)
    _require(run.get('state') == 'completed', 'build run is not completed')
    writers = evidence.get('writers')
    _require(isinstance(writers, list) and len(writers) == len(ASSETS)
             and {row['asset_id'] for row in writers} == set(ASSETS), 'per-writer population incomplete')
    indexed = {row['asset_id']: row for row in writers}
    previous_end = None
    for wave in WAVES:
        ends = []
        for aid in wave:
            row = indexed[aid]
            _require(row.get('run_id') == plan['build_id'] and row.get('state') == 'complete'
                     and row.get('error') is None, aid + ': writer failed, skipped or belongs to another run')
            try:
                start, end = (datetime.fromisoformat(row[key]) for key in ('started_at', 'ended_at'))
                valid = start.utcoffset() is not None and end.utcoffset() is not None and start <= end
            except (TypeError, ValueError, KeyError):
                valid = False
            _require(valid, aid + ': missing or invalid measured writer interval')
            _require(previous_end is None or previous_end <= start, aid + ': writer overlapped an upstream wave')
            ends.append(end)
        previous_end = max(ends + ([previous_end] if previous_end else []))
    candidate = evidence.get('candidate')
    _require(isinstance(candidate, dict) and all(candidate.get(key) == value for key, value in bundle['candidate'].items()),
             'candidate or its pinned inputs differs')
    _require(candidate.get('state') == ('published' if phase == 'published' else 'building'), 'candidate state differs')
    grains = evidence.get('grains')
    expected = {key for keys in bundle['publication_grains'].values() for key in keys}
    _require(isinstance(grains, list) and len(grains) == len(expected)
             and {row['grain_key'] for row in grains} == expected, 'grain population differs')
    _require(all(row.get('chart_id') == CANONICAL_CHART and row.get('generation') == plan['generation']
                 and row.get('result_state') in {'rows','zero_rows'} and isinstance(row.get('input_vector'),str)
                 and bool(row['input_vector']) for row in grains), 'failed, unbound or unmeasured grain')
    digest = _digest([(row['grain_key'], row['input_vector']) for row in sorted(grains,key=lambda row: row['grain_key'])])
    verification = evidence.get('verification')
    verified = (isinstance(verification, dict) and verification.get('chart_id') == CANONICAL_CHART
        and verification.get('generation') == plan['generation'] and verification.get('verifier_principal') == 'verifier_principal'
        and verification.get('result') == 'accepted' and isinstance(verification.get('detail'), dict)
        and verification['detail'].get('input_digest') == digest)
    _require(verification is None or verified, 'verification is rejected, stale or not independent')
    _require(phase == 'rebuilt' or verified, 'independent current-input verification is absent')
    published = phase == 'published'
    _require(evidence.get('head') == (plan['generation'] if published else plan['expected_head_generation']),
             'publication head differs')
    if published and plan['expected_head_generation'] is not None:
        retained = evidence.get('retained')
        _require(isinstance(retained, dict) and retained.get('chart_id') == CANONICAL_CHART
                 and retained.get('generation') == plan['expected_head_generation'] and retained.get('state') == 'published',
                 'previous head is not retained')
    return dict(schema='kala.final_readback/1', status='OBSERVED_COMPLETE', phase=phase,
        preparation_sha256=bundle['preparation_sha256'], evidence_sha256=_digest(evidence),
        chart_id=CANONICAL_CHART, run_id=plan['build_id'], generation=plan['generation'],
        writers=deepcopy(writers), writer_results_complete=True, grain_results_complete=True,
        candidate_input_digest=digest, independent_verification=bool(verified), head_unchanged=not published,
        publication_observed=published, semantic_verification=None, production_acceptance=None)


def _strict_object(pairs):
    obj = {}
    for key, value in pairs:
        _require(key not in obj, 'duplicate JSON key')
        obj[key] = value
    return obj


def inspect_census(census_path, expectations_path, *, repo=None):
    """Require the full K9-5 population, measured cells and independent predictions.

    Matching a predicted failure remains a failure; it cannot authorize a build,
    certification or publication. Separate authored expectations are never filled
    from observed cells. Their authorship still needs independent review.
    """
    repo = Path(repo) if repo else Path(__file__).resolve().parents[4]
    governance = repo / 'platform/scripts/governance'
    sys.path.insert(0, str(governance))
    try:
        import kala_rehearsal_census as census
        import asset_census as ac
    finally:
        sys.path.pop(0)
    predictions = _read(expectations_path)
    _require(predictions.get('schema') == 'kala.final_expectations/1'
             and isinstance(predictions.get('author'), str) and bool(predictions['author'].strip())
             and isinstance(predictions.get('basis'), list) and bool(predictions['basis'])
             and all(isinstance(basis, str) and basis.strip() for basis in predictions['basis']),
             'independently authored expectations and source basis are required')
    expected = predictions.get('expectations')
    report = census.build_report(repo, census_path, expected)
    ids = {row['asset'] for row in report['assets']}
    _require(report['summary']['observed_assets'] == len(ids) and report['summary']['missing_assets'] == 0,
             'complete K9-5 measured population required, including retained historical assets')
    _require(isinstance(expected, dict) and set(expected) == ids
             and all(set(gates) == set(ac.CELL_GATES) and all(value is not None for value in gates.values())
                     for gates in expected.values()), 'independent expectations must cover every asset and gate')
    for row in report['assets']:
        measurements = row['measurements']
        _require(set(report['criteria']) <= set(measurements)
                 and all(measurements[name]['v'] != 'ERRORED' for name in report['criteria']),
                 row['asset'] + ': missing or errored measurement')
    _require(not report['mismatches'] and not report['certifier_refusals'],
             'K9-5 census disagrees with independent expectations or claims an unearned verdict')
    non_passing = [dict(asset=row['asset'], gate=gate, observed=cell['observed'])
                   for row in report['assets'] for gate, cell in row['gates'].items()
                   if cell['observed'] not in {'PASS', 'N/A'}]
    return dict(schema='kala.final_census_inspection/1', population_complete=True,
                expectations_match=True, observed_assets=len(ids), observed_gates=len(ids)*len(ac.CELL_GATES),
                census_sha256=hashlib.sha256(Path(census_path).read_bytes()).hexdigest(),
                expectations_sha256=hashlib.sha256(Path(expectations_path).read_bytes()).hexdigest(),
                author=predictions['author'], basis=predictions['basis'], bindings=report['bindings'],
                non_passing_gates=non_passing, production_acceptance=None)


def _read(path):
    def refuse(value):
        raise ValueError('non-finite JSON')
    data = json.loads(Path(path).read_bytes(), object_pairs_hook=_strict_object, parse_constant=refuse)
    _digest(data)  # also refuses overflowing finite-looking numbers
    return data


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--run', type=Path, required=True)
    p = sub.add_parser('inspect')
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--readback', type=Path, required=True)
    p.add_argument('--phase', choices=['rebuilt','verified','published'], required=True)
    p = sub.add_parser('census')
    p.add_argument('--census', type=Path, required=True)
    p.add_argument('--expectations', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'prepare':
            result = prepare(_read(args.plan), _read(args.run))
        elif args.command == 'inspect':
            result = inspect_readback(_read(args.bundle), _read(args.readback), phase=args.phase)
        else:
            result = inspect_census(args.census, args.expectations)
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        return 0
    except (ValueError, TypeError, KeyError, OSError):
        print(json.dumps({'status':'REFUSED','reason':'invalid or incomplete preparation/readback evidence'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
