"""SR-K9-WAVE-ORDER (strong form): the K9 closed plan's order is DERIVED from asset_registry depends_on, never hand-listed.

The defect. ``rehearsal.WAVES`` was a hand-written tuple. It put ``ka_vighnakara`` ahead of ``ka_sangam`` (the writer reads
``kala_convergence``, which ``ka_sangam`` produces) and ``ka_sangam`` ahead of ``ka_muhurta_seva`` (declared upstream of
``ka_sangam``, registry migration 1392), so the plan the rehearsal froze and the audit that judged it both disagreed with the
registry the orchestrator reads. The order is now computed from ``depends_on`` (levels, ties by asset id) in
``publication_admission.derived_waves`` and consumed by ``rehearsal`` and ``final_rebuild``.

Claims, one doctrine-grounded oracle each (the sources are the registry rows migration 1392 / the seed declare, and the
orchestrator's readiness rule ``asset_runner.deps_unsatisfied``: a writer runs only when every DECLARED dependency is lit; B.3, B.10):
  O1 the order is a function of the registry only: the caller's order and the registry's key order do not change it, and ties
     are broken by asset id
  O2 a plan listing a writer ahead of a declared upstream is refused, naming the pair (the retired hand list is that plan)
  O3 the K9 roster's prepared waves put every declared upstream before its dependent (ka_muhurta_seva < ka_sangam <
     ka_vighnakara < ka_kshetra) and the request scope_target carries that order
  O4 a registry that cannot order the roster (a missing roster row, or a dependency cycle) refuses the preparation
  O5 ka_vighnakara declares ka_sangam (the producer of kala_convergence): in the seed and in migration 1392, so the effective
     registry holds the edge and no migration 1407 is needed; and dag_edge_guard FAILS a registry that drops it
"""
import copy
import json
from pathlib import Path
import re

import pytest

from pipeline.orchestrator import dag_edge_guard
from services.kala_core import publication_admission as admission
from services.kala_core import rehearsal
from tests.l3.kala_db.rehearsal.test_rehearsal import EDGES, WAVES, ROSTER, spec

REPO = Path(__file__).resolve().parents[6]
SEED = REPO / 'platform/scripts/seed/asset_registry_seed.ts'
WRITER = REPO / 'platform/python-sidecar/pipeline/orchestrator/writers/ka_vighnakara.py'

# The order rehearsal.WAVES listed by hand before SR-K9-WAVE-ORDER (kept here only as the plan that must be refused). The two
# unplanned assets the registry puts between roster members (ka_gochara, ka_gochara_v3_century_materialize) are added after
# ka_gochara_resonance, so the refusal under test is the ORDER one and not the closure one.
RETIRED_HAND_LIST = [
    'ka_dasha_kala', 'ka_vedha_gochara', 'ka_moorti_nirnaya', 'ka_kota_chakra', 'ka_tithi_pravesha', 'ka_sudarshana_varsha',
    'ka_yojaka', 'ka_gochara_resonance', 'ka_gochara', 'ka_gochara_v3_century_materialize',
    'ka_avadhi', 'ka_gochara_v5', 'ka_vighnakara', 'ka_sangam', 'ka_kshetra',
    'ka_kalasutra', 'ka_kala_darshana', 'ka_taranga', 'ka_jivana_parva', 'ka_tulana', 'ka_muhurta_seva', 'ka_graha_sancara',
]


# ---------------------------------------------------------------- O1: derived, not listed


def test_o1_the_derived_order_ignores_the_callers_order_and_the_registrys_key_order_and_breaks_ties_by_asset_id():
    edges = {'z_top': ['b_mid'], 'b_mid': ['a_base'], 'a_base': [], 'q_peer': [], 'c_peer': []}
    expected = [['a_base', 'c_peer', 'q_peer'], ['b_mid'], ['z_top']]
    assert admission.derived_waves(edges, ['z_top', 'q_peer', 'b_mid', 'a_base', 'c_peer']) == expected
    assert admission.derived_waves(dict(reversed(list(edges.items()))), ['c_peer', 'a_base', 'b_mid', 'q_peer', 'z_top']) == expected
    assert admission.closed_plan(edges, ['z_top', 'b_mid', 'a_base', 'q_peer', 'c_peer']) == [
        'a_base', 'c_peer', 'q_peer', 'b_mid', 'z_top']


def test_o1_the_level_follows_a_dependency_through_an_unplanned_asset():
    # x -> m -> y with m unplanned: y must still come after x (staleness.py stales the out-of-plan m and the race is real)
    edges = {'y': ['m'], 'm': ['x'], 'x': []}
    assert admission.derived_waves(edges, ['y', 'x'], close=False) == [['x'], ['y']]


# ---------------------------------------------------------------- O2: a writer before its declared upstream is refused


def test_o2_the_retired_hand_list_is_refused_on_the_real_registry_for_the_two_pairs_it_got_wrong():
    reason = admission.assets_refusal(EDGES, RETIRED_HAND_LIST)
    assert reason and 'plan order breaks a dependency' in reason
    assert 'ka_sangam must precede ka_vighnakara' in reason          # vighnakara reads kala_convergence, sangam writes it
    assert 'ka_muhurta_seva must precede ka_sangam' in reason        # declared upstream of ka_sangam (1392)
    assert reason.split('ordered plan: ')[1] == ','.join(admission.closed_plan(EDGES, RETIRED_HAND_LIST))


def test_o2_the_refusal_names_a_writer_ahead_of_its_upstream_and_the_derived_plan_is_admitted():
    plan = ['ka_yojaka', 'ka_gochara_resonance', 'ka_gochara', 'ka_vighnakara', 'ka_sangam']
    reason = admission.assets_refusal(EDGES, plan)
    assert reason and 'ka_sangam must precede ka_vighnakara' in reason
    closed = admission.closed_plan(EDGES, plan)
    assert closed.index('ka_sangam') < closed.index('ka_vighnakara')
    assert admission.assets_refusal(EDGES, closed) is None


# ---------------------------------------------------------------- O3: the prepared K9 plan


def declared_pairs():
    """(upstream, dependent) for every roster pair the registry declares directly, or through unplanned assets."""
    out = set()
    for asset in ROSTER:
        seen, stack = set(), list(EDGES[asset])
        while stack:
            dep = stack.pop()
            if dep not in seen:
                seen.add(dep)
                stack.extend(EDGES.get(dep, ()))
        out |= {(dep, asset) for dep in seen & ROSTER}
    return out


def test_o3_every_declared_upstream_of_the_prepared_roster_precedes_its_dependent():
    plan = rehearsal.prepare_rehearsal(**spec())
    order = plan['request']['scope_target'].split(',')
    assert order == [asset for wave in plan['waves'] for asset in wave] and set(order) == ROSTER and len(order) == 20
    assert plan['waves'] == WAVES
    pairs = declared_pairs()
    assert ('ka_sangam', 'ka_vighnakara') in pairs and ('ka_muhurta_seva', 'ka_sangam') in pairs
    assert ('ka_vighnakara', 'ka_kshetra') in pairs and ('ka_gochara_resonance', 'ka_sangam') in pairs
    for upstream, dependent in sorted(pairs):
        assert order.index(upstream) < order.index(dependent), (upstream, dependent)


def test_o3_the_pinned_edges_are_idempotent_so_the_audit_can_re_prepare_the_plan():
    plan = rehearsal.prepare_rehearsal(**spec())
    assert rehearsal.order_edges(plan['registry_edges']) == plan['registry_edges']
    assert rehearsal.prepare_rehearsal(**{key: plan[key] for key in rehearsal._INPUTS}) == plan


# ---------------------------------------------------------------- O4: no order, no plan


def test_o4_a_registry_missing_a_roster_asset_refuses_the_preparation():
    args = spec()
    del args['registry_edges']['ka_sangam']
    with pytest.raises(ValueError, match='ka_sangam'):
        rehearsal.prepare_rehearsal(**args)


def test_o4_a_dependency_cycle_among_roster_assets_refuses_the_preparation_and_the_admission():
    args = spec()
    args['registry_edges']['ka_sangam'] = args['registry_edges']['ka_sangam'] + ['ka_vighnakara']   # sangam <-> vighnakara
    with pytest.raises(ValueError, match='cycle'):
        rehearsal.prepare_rehearsal(**args)
    reason = admission.assets_refusal(args['registry_edges'], ['ka_sangam', 'ka_vighnakara'])
    assert reason and 'cycle' in reason and 'ka_sangam' in reason and 'ka_vighnakara' in reason


# ---------------------------------------------------------------- O5: ka_vighnakara declares ka_sangam


def seed_depends_on(asset):
    body = re.search(r"asset_id: '%s',(.*?)\n  \}," % asset, SEED.read_text(), re.S).group(1)
    return re.findall(r"'([a-z0-9_]+)'", re.search(r"depends_on: \[(.*?)\]", body).group(1))


def seed_field(asset, field):
    body = re.search(r"asset_id: '%s',(.*?)\n  \}," % asset, SEED.read_text(), re.S).group(1)
    return re.search(field + r": '([^']*)'", body).group(1)


def test_o5_ka_vighnakara_declares_ka_sangam_in_the_seed_and_in_migration_1392():
    assert 'ka_sangam' in seed_depends_on('ka_vighnakara')
    corrections = json.loads((REPO / 'platform/migrations/1392_k8_registry_truth.sql').read_text().split('$k8_rows$')[1])
    assert 'ka_sangam' in next(row for row in corrections if row['asset_id'] == 'ka_vighnakara')['depends_on']
    assert 'ka_sangam' in EDGES['ka_vighnakara']                       # the effective registry (reconstruction + 1392)
    # premise: ka_sangam is the producer of kala_convergence, which the ka_vighnakara writer reads
    assert seed_field('ka_sangam', 'target_table') == 'kala_convergence'
    assert re.search(r'FROM\s+kala_convergence', WRITER.read_text())


def guard_registry(edges):
    """The asset_registry columns dag_edge_guard reads: per-chart producers carry the table they own."""
    owns = {'ka_sangam': 'kala_convergence', 'ka_vighnakara': 'kala_obstruction'}
    return {asset: dict(asset_id=asset, scope='per_chart', target_table=owns.get(asset),
                        count_sql=f'SELECT count(*) FROM {owns[asset]}' if asset in owns else None, depends_on=list(deps))
            for asset, deps in edges.items()}


def test_o5_dag_edge_guard_fails_a_registry_that_drops_the_vighnakara_sangam_edge_and_passes_the_real_one():
    # Base-table read: PR #3869 (fix-3869b) widens the guard to the served views; the table reads are what this asserts.
    tables = {'kala_convergence', 'kala_obstruction'}
    item = [('pipeline/orchestrator/writers/ka_vighnakara.py', WRITER.read_text())]
    assert dag_edge_guard.evaluate(guard_registry(EDGES), tables, item)['hard'] == []
    broken = copy.deepcopy(EDGES)
    broken['ka_vighnakara'] = [dep for dep in broken['ka_vighnakara'] if dep != 'ka_sangam']
    result = dag_edge_guard.evaluate(guard_registry(broken), tables, item)
    assert result['checked_assets'] == 1
    assert len(result['hard']) == 1
    assert 'ka_vighnakara' in result['hard'][0] and 'kala_convergence' in result['hard'][0] and 'ka_sangam' in result['hard'][0]
