"""K3 → G1 synthetic producer/storage integration, never a live-seal claim."""
from copy import deepcopy
import json
from datetime import datetime, timezone

import pytest
from psycopg.types.json import Jsonb

from services.ka_kshetra.g1_inputs import load_suppression
from tests.l3.kala_db.ka_vighnakara.test_sealed_storage import (
    database, conn, settled_fixture_chart, setup, context, api,
)
from tests.l3.ka_vighnakara.test_sealed import CHART, GEN, data


@pytest.fixture
def stored(conn, tmp_path):
    setup(conn)
    api().write_sealed_candidate(context(conn, tmp_path))
    # The K3 fixture owns the real obstruction schema; these empty sibling
    # stores make absence visible without inventing vedha/murti evidence.
    conn.execute('CREATE TABLE kala_vedha_gochara_interval (chart_id uuid, generation text, '
                 'ayanamsha_id text, vedha_kind text, graha text, t_in timestamptz)')
    conn.execute('CREATE TABLE kala_moorti_nirnaya_candidate (chart_id uuid, generation text, '
                 'ayanamsha_id text, payload jsonb, upstream_fingerprint text)')
    return conn


def envelope_index(primitives):
    from services.ka_kshetra.stage4_field import EnvelopeIndex, Primitive
    return EnvelopeIndex([Primitive(p.primitive_kind,p.subject,p.object_ref,p.polarity,
        p.class_label,tuple(p.envelope),p.source_pk,p.source_fact_id,p.source_table)
        for p in primitives],31.)


def consume(conn):
    return load_suppression(conn, CHART, GEN, datetime(2026, 1, 1, tzinfo=timezone.utc))


def test_stored_sealed_producer_reaches_g1_without_fixture_relabelling(stored):
    prims, gaps = consume(stored)
    active = [p for p in prims if p.primitive_kind == 'negative_space']
    assert len(active) == 1, gaps
    assert active[0].envelope == [(0., 0.), (0., 1.), (14., 1.), (14., 0.)]
    assert active[0].class_label == 'event_class:career_change'
    assert active[0].source_table == 'kala_obstruction'
    assert active[0].source_pk.startswith('k3:')
    envelope = envelope_index(prims)
    assert list(envelope.obstructions_at(7.).values()) == [1.]
    assert envelope.obstructions_at(20.) == {}
    stored.execute("SET LOCAL TimeZone='Asia/Kolkata'")
    assert [vars(p) for p in consume(stored)[0]] == [vars(p) for p in prims]
    masks = [p for p in prims if p.primitive_kind == 'input_mask']
    assert len(masks) == 1 and masks[0].class_label == 'evaluated_silent'
    assert masks[0].envelope == [(14., 0.), (31., 0.)]
    assert not any(g['reason'] == 'negative_space_binding_not_admitted' for g in gaps)
    assert any('measurement_not_estimated_here' in g['reason'] for g in gaps)
    conventions = stored.execute('SELECT conventions FROM kala_layer_candidate').fetchone()[0]
    assert conventions.get('fixture') is not True


@pytest.mark.parametrize('pin', list(data()['pins']))
def test_mismatched_candidate_producer_pin_never_admits_scalar(stored, pin):
    pins = deepcopy(data()['pins']); pins[pin] = 'wrong'
    stored.execute('UPDATE kala_layer_candidate SET conventions=%s', (Jsonb({'negative_space': pins}),))
    prims, gaps = consume(stored)
    assert not any(p.primitive_kind == 'negative_space' for p in prims)
    assert any(g['reason'] == 'negative_space_binding_not_admitted' for g in gaps)


@pytest.mark.parametrize('mutation', ['fixture', 'unpinned', 'wrong_generation', 'wrong_chart'])
def test_candidate_identity_and_nonfixture_binding_are_required(stored, mutation):
    if mutation == 'fixture':
        stored.execute("UPDATE kala_layer_candidate SET conventions=conventions || '{\"fixture\":true}'::jsonb")
    elif mutation == 'unpinned':
        stored.execute("UPDATE kala_layer_candidate SET conventions='{}'")
    else:
        # Tamper the assertion payload while keeping indexed SQL identity.
        key, value = ('generation', 'candidate:other') if mutation == 'wrong_generation' else ('chart_id', 'other')
        stored.execute("UPDATE kala_obstruction SET negative_space_contract_version='test:forged', assertion=jsonb_set(assertion, %s, %s)",
                       ([key], Jsonb(value)))
    prims, gaps = consume(stored)
    assert not any(p.primitive_kind == 'negative_space' for p in prims)
    assert any(g['reason'] == 'negative_space_binding_not_admitted' for g in gaps)


@pytest.mark.parametrize('state', ['obstruction_cancelled', 'obstruction_partly_cancelled',
                                  'obstruction_contested', 'information_unavailable'])
def test_sealed_nonactive_states_keep_edges_and_never_gain_scalar(stored, state):
    # Use the real producer's licensed protection/coverage cases, then persist
    # through the same storage operation rather than forging an active state.
    from tests.l3.ka_vighnakara.test_sealed import export, with_protection
    value = with_protection({'obstruction_cancelled':'defeats',
        'obstruction_partly_cancelled':'partly_defeats', 'obstruction_contested':'contests'}.get(state, 'defeats'))
    if state == 'information_unavailable':
        value = data(); value['coverage'][0]['unavailable_inputs'] = {'source':'missing'}
    # Both schema versions are exercised through conn's parametrization.
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as folder:
        receipt, expected = export(Path(folder), value)
        from tests.l3.ka_vighnakara.test_sealed import BUILD
        from types import SimpleNamespace
        api().write_sealed_candidate(SimpleNamespace(db_conn=stored, build_id=BUILD, dry_run=False,
            config={'chart_id':CHART, 'negative_space_sealed':{'receipt':receipt,'expected':expected}}))
    prims, gaps = consume(stored)
    assert not any(p.primitive_kind == 'negative_space' for p in prims)
    assert any(p.class_label == state for p in prims)
    assert all(envelope_index(prims).obstructions_at(t) == {} for t in (0.,7.,14.,20.,31.))
    assert {0.,14.,31.} <= {edge for p in prims for edge,_ in p.envelope}
    if state != 'obstruction_cancelled':
        assert any(g['reason'] == state for g in gaps)


@pytest.mark.parametrize('path,value', [
    (('provenance','correspondence','record_id'), 'other'),
    (('provenance','correspondence','contact_id'), 'other'),
    (('provenance','correspondence','event_class_id'), 'other'),
    (('provenance','correspondence','assertion_id'), 'other'),
    (('provenance','correspondence','f1_id'), 'other'),
    (('provenance','record','fixture'), True),
    (('provenance','record','chart_id'), 'other'),
    (('provenance','record','generation'), '5.1'),
    (('provenance','record','event_class'), 'other'),
    (('provenance','F1','id'), 'other'),
    (('provenance','F1','generation'), 'candidate:other'),
    (('provenance','F1','chart_id'), 'other'),
    (('provenance','F1','ayanamsha_id'), 'other'),
    (('provenance','header','chart_id'), 'other'),
    (('provenance','header','generation'), 'candidate:other'),
    (('provenance','header','natal_build_id'), 'other'),
    (('provenance','header','upstream_fingerprint'), {}),
    (('provenance','coverage','chart_id'), 'other'),
    (('provenance','coverage','generation'), 'other'),
    (('provenance','coverage','build_id'), 'other'),
    (('provenance','coverage','targets_unresolved'), 1),
    (('provenance','coverage','unavailable_inputs'), {'clock':'missing'}),
    (('provenance','F2','build_id'), 'other'),
    (('provenance','F2','ayanamsha_id'), 'other'),
    (('provenance','F2','scenario_id'), 'other'),
    (('provenance','F2','tier'), 'single'),
    (('provenance','F2','applicability'), 'unknown'),
    (('roots','fact_ids'), []),
    (('roots','record_ids'), ['other']),
    (('roots','contact_ids'), ['other']),
    (('source','locator'), ''),
    (('source','text'), ''),
])
def test_corrupt_stored_correspondence_is_not_an_in_force_input(stored, path, value):
    identity, payload = stored.execute("SELECT assertion_id,assertion FROM kala_obstruction "
        "WHERE effective_state='obstruction_in_force'").fetchone()
    target = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    stored.execute('UPDATE kala_obstruction SET assertion=%s,roots=%s WHERE assertion_id=%s',
                   (Jsonb(payload), Jsonb(payload['roots']), identity))
    prims, gaps = consume(stored)
    assert not any(p.primitive_kind == 'negative_space' for p in prims)
    assert any(g['reason'] == 'negative_space_binding_not_admitted' for g in gaps)


def test_changed_physical_assertion_identity_is_refused(stored):
    stored.execute("UPDATE kala_obstruction SET assertion_id='substituted', "
        "assertion=jsonb_set(assertion,'{assertion_id}','\"substituted\"') "
        "WHERE effective_state='obstruction_in_force'")
    prims, gaps = consume(stored)
    assert not any(p.primitive_kind == 'negative_space' for p in prims)
    assert any(g['reason'] == 'negative_space_binding_not_admitted' for g in gaps)


def test_published_candidate_cannot_be_used_as_a_private_prebuild_binding(stored):
    stored.execute("UPDATE kala_layer_candidate SET state='published'")
    prims, gaps = consume(stored)
    assert not any(p.primitive_kind == 'negative_space' for p in prims)
    assert any(g['reason'] == 'negative_space_binding_not_admitted' for g in gaps)


# K3's own CHECK already rejects the divergent rows below. G1 re-checks the stored
# projection (g1_inputs.py `_sealed_binding_matches`), so these oracles simulate a
# damaged or hand-edited store by dropping that CHECK in the disposable database.
def damaged_store(conn):
    conn.execute('ALTER TABLE kala_obstruction DROP CONSTRAINT kala_obstruction_k3_sealed_check')
    return conn


def refused(conn):
    prims, gaps = consume(conn)
    assert not any(p.primitive_kind == 'negative_space' for p in prims)
    assert any(g['reason'] == 'negative_space_binding_not_admitted' for g in gaps)


@pytest.mark.parametrize('column,value', [
    ('effective_state', 'obstruction_cancelled'), ('event_class_id', 'other'),
    ('exposure', 'outside_risk_set'), ('knowledge', 'unsearched'),
    ('rule_conclusion', 'supportive'), ('defeat_state', 'cancelled'),
    ('null_reason', 'forged'), ('measurement', 'estimated')])
def test_indexed_column_disagreeing_with_sealed_assertion_is_refused(stored, column, value):
    damaged_store(stored).execute(f'UPDATE kala_obstruction SET {column}=%s', (value,))
    refused(stored)


@pytest.mark.parametrize('column,shift', [('interval_start', '-1 day'), ('interval_end', '1 day')])
def test_interval_column_disagreeing_with_sealed_assertion_is_refused(stored, column, shift):
    damaged_store(stored).execute(f"UPDATE kala_obstruction SET {column}={column}+%s::interval", (shift,))
    refused(stored)


@pytest.mark.parametrize('field,value', [
    ('exposure', 'outside_risk_set'), ('knowledge', 'unsearched'), ('rule_conclusion', 'supportive'),
    ('defeat_state', 'contested'), ('null_reason', 'forged'), ('measurement', 'estimated')])
def test_consistently_rewritten_in_force_qualifier_is_not_an_obstruction(stored, field, value):
    # Column and assertion agree, effective_state still claims in force: the
    # in-force qualifiers must hold on their own, not only agree with each other.
    damaged_store(stored).execute(f"UPDATE kala_obstruction SET {field}=%s, "
        f"assertion=jsonb_set(assertion,%s,%s)", (value, [field], Jsonb(value)))
    refused(stored)


@pytest.mark.parametrize('target', ['row', 'assertion'])
def test_contract_version_must_match_on_both_row_and_assertion(stored, target):
    damaged_store(stored)
    if target == 'row':
        stored.execute("UPDATE kala_obstruction SET negative_space_contract_version='k3-negative-space/2.0.1'")
    else:
        stored.execute("UPDATE kala_obstruction SET assertion=jsonb_set(assertion,'{contract_version}','\"k3-negative-space/2.0.1\"')")
    refused(stored)


@pytest.mark.parametrize('old,new', [('lahiri_chitrapaksha', 'other_ayanamsha'), ('5.0', '5.1')])
def test_canonical_ayanamsha_and_judge_generation_are_required_even_if_consistently_rebound(stored, old, new):
    # Rewrite every occurrence in the stored assertion and the candidate
    # convention together, so the sub-pins still agree; only the canonical-value
    # requirement itself can refuse this.
    damaged_store(stored)
    swap = lambda value: json.loads(json.dumps(value).replace(json.dumps(old), json.dumps(new)))
    ident, payload = stored.execute('SELECT assertion_id,assertion FROM kala_obstruction').fetchone()
    stored.execute('UPDATE kala_obstruction SET assertion=%s WHERE assertion_id=%s', (Jsonb(swap(payload)), ident))
    conventions = stored.execute('SELECT conventions FROM kala_layer_candidate').fetchone()[0]
    stored.execute('UPDATE kala_layer_candidate SET conventions=%s', (Jsonb(swap(conventions)),))
    refused(stored)
