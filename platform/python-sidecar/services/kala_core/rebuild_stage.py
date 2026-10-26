"""K9-4b production staging: the frozen ``build_runs`` row and the ONE open candidate that ``orchestrator_rebuild`` requires.

``publication.rebuild`` (via ``inspect_rebuild`` -> ``_run``) refuses unless ``build_runs`` already holds a frozen plan manifest for the run, and
``publication._candidate`` refuses unless ``kala_layer_candidate`` holds a ``building`` candidate bound to that run whose ``conventions.publication_grains`` cover
every planned writer exactly. Nothing else in the executor table creates them; this module is the governed executor kind ``k9_rebuild_stage`` (ruling SR-PREP-LANES-1 (2),
"K9-4b: ROUTE = Mac executor child under memguard. STAGING = a new governed executor op kind k9_rebuild_stage ... admitted only under owner_go + absence/exposure gates"):

* ``stage``        -- ONE transaction: freeze the ordered closed plan (the registry's own ``derived_waves``), insert the ``planned`` run and its queued assets, open the
                      candidate (``manifest.open_candidate``, which pins the live head as ``expected_head_generation``), prove ``publication.inspect_rebuild`` accepts exactly
                      what was staged, commit, then READ IT BACK from the database. A second staging never happens: whatever exists is refused BY NAME, and a repeat of the
                      identical request writes nothing and reports ``ALREADY_STAGED``.
* ``stage-dryrun`` -- the same transaction, rolled back, and the rollback read back (``rollback_confirmed``); it persists nothing.

It consumes the frozen orchestrator contract (CLAUDE.md N.2) and changes none of it: it calls ``validate_frozen_run_manifest`` / ``get_writer_source_hash`` / ``discover_all`` and
writes the rows the dispatch API itself writes. It never writes ``asset_throughput``, never publishes, never touches a served (head-generation) row, and never runs a writer.

(I) INTERPRETATIONS, each with its alternative in the PR:
* ``natal-build`` is an argument (bound by the request digest), not a constant: the cockpit names the settled build whose chart facts the candidate pins, and this module only
  checks that ``chart_facts`` holds rows of that build. Alternative: derive it from ``chart_facts`` (ambiguous when several builds exist, so refused as an invention, B.10).
* ``model_digest`` is the frozen manifest digest (it binds every writer's code digest) and ``rule_registry_version`` the fixed text ``RULE_REGISTRY_VERSION``; the kit used
  fixture strings. No other component reads either value.
* Only a run that is not yet ``completed`` blocks a staging (``planned``/``running``/``paused`` rebuild runs, or any ``building`` candidate of the chart): a finished earlier
  run is history, not a second frozen row.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from typing import Any, Callable, Mapping
from uuid import UUID

import psycopg

from services.kala_core import publication
from services.kala_core.manifest import open_candidate
from services.kala_core.publication import CANONICAL_CHART
from services.kala_core.publication_admission import (
    assets_refusal, closed_plan, convergence_scope_refusal, derived_waves, registry_edges)

SCHEMA = 'ky.k9_rebuild_stage/1'
TRIGGERED_BY = 'k9-rebuild-stage'
RULE_REGISTRY_VERSION = 'k9-rebuild-stage/1'
MANIFEST_VERSION = 'nirmana-run-manifest/v1'
# conventions.natal.ayanamsha_id: the grain key of ka_vedha_gochara embeds it (services/ka_vedha_gochara/storage.py:120), and the kit stages the same value.
AYANAMSHA_ID = 'lahiri_chitrapaksha'
VEDHA_KINDS = ('house_vedha', 'latta', 'sarvatobhadra')      # services/ka_vedha_gochara/storage.py:100,120 -- the three header kinds the writer attests
OPEN_RUN_STATES = ('planned', 'running', 'paused')           # migration 359: the states build_runs treats as active
GENERATION_PREFIX = 'candidate:'


class Refused(ValueError):
    """A named refusal: nothing was written."""


def generation_of(run_id: str) -> str:
    return GENERATION_PREFIX + run_id


def grains_for(plan: list[str]) -> dict[str, list[str]]:
    """The explicit publication grain plan: every writer's own attested grain keys (``writer_grain.grain_key``; ka_vedha_gochara's three).
    ``publication._candidate`` requires exactly this set; nothing is inferred from rows."""
    from services.kala_core.writer_grain import grain_key
    return {a: ([f'ka_vedha_gochara:{AYANAMSHA_ID}:{k}' for k in VEDHA_KINDS] if a == 'ka_vedha_gochara' else [grain_key(a)]) for a in plan}


def canonical_digest(manifest: Mapping[str, Any]) -> str:
    """The dispatch API's digest (runner._canonical_manifest_digest): key-sorted canonical JSON, array order kept."""
    return hashlib.sha256(json.dumps(manifest, ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


def writer_digests(assets: list[str]) -> dict[str, str]:
    """get_writer_source_hash per asset, from the tree this child runs in (what runner.validate_frozen_run_manifest's executor-side check compares)."""
    from pipeline.orchestrator.asset_runner import get_writer_source_hash
    from pipeline.orchestrator.writers import discover_all
    discover_all()
    return {a: get_writer_source_hash(a) for a in assets}


def _registry_rows(conn: Any, plan: list[str]) -> dict[str, tuple]:
    rows = conn.execute(
        """SELECT ar.asset_id, ar.scope, COALESCE(ar.depends_on, '{}'), ar.natural_key_partition,
                  EXISTS (SELECT 1 FROM asset_registry peer WHERE peer.target_table = ar.target_table AND ar.target_table IS NOT NULL
                          AND peer.asset_id <> ar.asset_id AND peer.is_active AND peer.has_writer)
           FROM asset_registry ar WHERE ar.asset_id = ANY(%s)""", (plan,)).fetchall()
    return {r[0]: r for r in rows}


def build_manifest(conn: Any, plan: list[str], digests: Mapping[str, str]) -> dict:
    rows = _registry_rows(conn, plan)
    missing = [a for a in plan if a not in rows]
    if missing:
        raise Refused('not in asset_registry: ' + ', '.join(missing))
    waves = derived_waves(registry_edges(conn), plan, close=False)
    if [a for wave in waves for a in wave] != plan:
        raise Refused('assets are not the registry-derived order')
    return dict(version=MANIFEST_VERSION, chart_id=CANONICAL_CHART, scope='asset_set', scope_target=','.join(plan), action='rebuild', waves=waves,
                assets=[dict(asset_id=a, scope=rows[a][1], depends_on=sorted(rows[a][2]), natural_key_partition=rows[a][3],
                             has_cowriters=bool(rows[a][4]), expected_code_digest=digests[a]) for a in plan])


def existing_problem(conn: Any, run_id: str) -> str | None:
    """What already exists that forbids a staging, BY NAME (never a second frozen row or candidate); None when nothing does."""
    row = conn.execute('SELECT state, action, plan_manifest_digest FROM build_runs WHERE id = %s', (run_id,)).fetchone()
    if row is not None:
        return f'build run {run_id} already exists (state {row[0]}, action {row[1]}, manifest {row[2]})'
    cand = conn.execute('SELECT generation, build_id, state FROM kala_layer_candidate WHERE build_id = %s', (run_id,)).fetchone()
    if cand is not None:
        return f'a candidate is already bound to {run_id}: {cand[0]} (state {cand[2]})'
    open_runs = conn.execute('SELECT id, state FROM build_runs WHERE chart_id = %s AND action = %s AND state = ANY(%s) ORDER BY id',
                             (CANONICAL_CHART, 'rebuild', list(OPEN_RUN_STATES))).fetchall()
    if open_runs:
        return 'an open rebuild run of the chart exists: ' + ', '.join(f'{r[0]} ({r[1]})' for r in open_runs)
    building = conn.execute("SELECT generation, build_id FROM kala_layer_candidate WHERE chart_id = %s AND state = 'building' ORDER BY generation",
                            (CANONICAL_CHART,)).fetchall()
    if building:
        return 'a building candidate of the chart exists: ' + ', '.join(f'{r[0]} (run {r[1]})' for r in building)
    return None


def _read_back(conn: Any, run_id: str) -> dict | None:
    run = conn.execute('SELECT state, action, chart_id, plan, plan_manifest_digest FROM build_runs WHERE id = %s', (run_id,)).fetchone()
    if run is None:
        return None
    cand = conn.execute('SELECT generation, state, expected_head_generation, model_digest, conventions FROM kala_layer_candidate WHERE build_id = %s', (run_id,)).fetchone()
    queued = conn.execute("SELECT count(*) FROM build_run_assets WHERE run_id = %s AND state = 'queued'", (run_id,)).fetchone()[0]
    return dict(run_state=run[0], action=run[1], chart_id=str(run[2]), plan=list(run[3]), manifest_digest=run[4], queued_assets=queued,
                candidate=None if cand is None else dict(generation=cand[0], state=cand[1], expected_head=cand[2], model_digest=cand[3],
                                                         publication_grains=(cand[4] or {}).get('publication_grains'), natal=(cand[4] or {}).get('natal')))


def stage(conn: Any, *, run_id: str, assets: list[str], natal_build: str, expected_head: str | None, commit: bool,
          digest_fn: Callable[[list[str]], Mapping[str, str]] = writer_digests) -> dict:
    """Stage inside ONE transaction. ``commit`` False rolls everything back (the dry run). Raises ``Refused`` with nothing written."""
    UUID(run_id), UUID(natal_build)
    if expected_head == 'NONE' or expected_head == '':
        expected_head = None
    conn.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (TRIGGERED_BY + ':' + CANONICAL_CHART,))      # two stagings of the chart serialise
    edges = registry_edges(conn)
    why = assets_refusal(edges, assets) or convergence_scope_refusal(conn, assets)
    if why:
        raise Refused(why)
    if closed_plan(edges, assets) != assets:
        raise Refused('assets must be the ordered closed plan: ' + ','.join(closed_plan(edges, assets)))
    if any(not a.startswith('ka_') for a in assets) or 'ka_bhavishya_lekha' in assets:
        raise Refused('only an explicit Kāla rebuild plan is permitted (publication._run)')
    digests = dict(digest_fn(assets))
    manifest = build_manifest(conn, assets, digests)
    digest = canonical_digest(manifest)
    if conn.execute('SELECT 1 FROM chart_facts WHERE chart_id = %s AND build_id::text = %s LIMIT 1', (CANONICAL_CHART, natal_build)).fetchone() is None:
        raise Refused(f'chart_facts holds no rows of natal build {natal_build}')
    conventions = {'publication_grains': grains_for(assets), 'natal': {'build_id': natal_build, 'ayanamsha_id': AYANAMSHA_ID}}
    prior = _read_back(conn, run_id)
    if prior is not None and prior['candidate'] is not None:      # the identical request again (e.g. after an unknown commit): idempotent, writes nothing
        same = (prior['run_state'] == 'planned' and prior['candidate']['state'] == 'building'      # still exactly what staging left: a run that has started or a candidate that moved on is not "staged"
                and prior['manifest_digest'] == digest and prior['candidate']['publication_grains'] == conventions['publication_grains']
                and prior['candidate']['natal'] == conventions['natal'] and prior['candidate']['expected_head'] == expected_head
                and prior['candidate']['generation'] == generation_of(run_id))
        if same:
            conn.rollback()
            return dict(status='ALREADY_STAGED', schema=SCHEMA, run_id=run_id, generation=generation_of(run_id), written=False, staged=prior)
    problem = existing_problem(conn, run_id)
    if problem:
        raise Refused(problem)
    head = conn.execute('SELECT generation FROM kala_layer_head WHERE chart_id = %s', (CANONICAL_CHART,)).fetchone()
    live = None if head is None else head[0]
    if live != expected_head:
        raise Refused(f'the served head is {live!r}, not the expected {expected_head!r}: the exposure readback is stale')
    conn.execute("INSERT INTO build_runs (id, chart_id, scope, scope_target, action, state, plan, plan_manifest, plan_manifest_digest, triggered_by) "
                 "VALUES (%s,%s,'asset_set',%s,'rebuild','planned',%s::jsonb,%s::jsonb,%s,%s)",
                 (run_id, CANONICAL_CHART, ','.join(assets), json.dumps(assets), json.dumps(manifest), digest, TRIGGERED_BY))
    for position, a in enumerate(assets):
        conn.execute("INSERT INTO build_run_assets (run_id, asset_id, position, state) VALUES (%s,%s,%s,'queued')", (run_id, a, position))
    cand = open_candidate(conn, chart_id=CANONICAL_CHART, generation=generation_of(run_id), build_id=run_id, model_digest=digest,
                          rule_registry_version=RULE_REGISTRY_VERSION, conventions=conventions)
    if cand.expected_head_generation != expected_head:
        raise Refused('the candidate pinned a different head than the request expects')
    accepted = publication.inspect_rebuild(conn, run_id=run_id, assets=','.join(assets))      # exactly the check orchestrator_rebuild makes first
    if accepted.get('status') != 'PLAN_ONLY' or accepted.get('planned_assets') != assets:
        raise Refused('orchestrator_rebuild would not accept what was staged')
    if not commit:
        conn.rollback()
        after = _read_back(conn, run_id)
        conn.rollback()
        return dict(status='ROLLED_BACK', schema=SCHEMA, run_id=run_id, generation=generation_of(run_id), written=False, plan=assets,
                    manifest_digest=digest, expected_head=expected_head, rollback_confirmed=after is None)
    conn.commit()
    staged = _read_back(conn, run_id)
    conn.rollback()
    if (staged is None or staged['manifest_digest'] != digest or staged['run_state'] != 'planned' or staged['plan'] != assets
            or staged['queued_assets'] != len(assets) or staged['candidate'] is None or staged['candidate']['state'] != 'building'):
        raise Refused('read-back after commit does not show the staged run and building candidate')
    return dict(status='STAGED', schema=SCHEMA, run_id=run_id, generation=generation_of(run_id), written=True, staged=staged)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='operation', required=True)
    for operation in ('stage', 'stage-dryrun'):
        p = sub.add_parser(operation)
        p.add_argument('--run-id', required=True, type=UUID)
        p.add_argument('--assets', required=True)
        p.add_argument('--natal-build', required=True, type=UUID)
        p.add_argument('--expected-head', required=True)
    return parser


def main(argv=None, *, digest_fn: Callable[[list[str]], Mapping[str, str]] = writer_digests) -> int:
    args = _parser().parse_args(argv)
    dsn = os.environ.get('DATABASE_URL')
    if not dsn:
        print(json.dumps({'status': 'REFUSED', 'reason': 'operation-specific DATABASE_URL is required'}))
        return 2
    try:
        with psycopg.connect(dsn, connect_timeout=5) as conn:
            result = stage(conn, run_id=str(args.run_id), assets=args.assets.split(','), natal_build=str(args.natal_build),
                           expected_head=args.expected_head, commit=args.operation == 'stage', digest_fn=digest_fn)
        print(json.dumps(result, sort_keys=True, default=str))
        return 0 if result['status'] != 'ROLLED_BACK' or result['rollback_confirmed'] else 3
    except (Refused, ValueError) as exc:
        print(json.dumps({'status': 'REFUSED', 'reason': str(exc)}))
        return 2
    except psycopg.Error:
        # Connection diagnostics may contain secrets: do not echo libpq errors.
        print(json.dumps({'status': 'REFUSED', 'reason': 'database operation failed; transaction rolled back'}))
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
