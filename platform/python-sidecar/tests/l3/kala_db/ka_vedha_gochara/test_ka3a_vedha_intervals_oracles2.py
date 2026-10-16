"""KA-3a vedha_intervals: source-derived provider and persistence oracles.

Sources: Phaladipika XXVI.3-8, PG322-323 (house pairs/exceptions), and
XXVI.42-44, PG338-339 (inclusive forward/rear latta). The latter's exported
corpus fixture supplies source rows, not expected computed answers.

All dates, residences, UUIDs and moon-ref=300 degrees are PLANTED algebra/DB
fixtures from test_overlays and the guarded conn fixture, never native chart
claims (B.10). The supplied moon-ref implies sign 11 and nakshatra 23.
Every expectation below is a literal rule consequence, not a captured output
or a call to the production/judge algorithm (B.3).

Persistence/lifecycle assertions additionally implement PACKET_KA-3a_v1.md
§4 lines 28-34 and §6 line 40; classical texts do not specify SQL or dry runs.
CI: kala-db-tests-5-0 already collects the enclosing kala_db directory.
"""
from datetime import datetime
import json
from pathlib import Path
from types import SimpleNamespace

import psycopg
from psycopg.types.json import Jsonb
import pytest

from services.ka_vedha_gochara.storage import replace_candidate
from services.ka_vedha_gochara.writer import KaVedhaGocharaWriter
from services.kala_core.sky.coverage import coverage_of
from tests.l3.ka_vedha_gochara.test_overlays import A, B, C, D, bundle
from tests.l3.kala_db.ka_vedha_gochara.conftest import BUILD, CHART, NATAL


SUN_CITATION = ('Phaladipika Adh. XXVI, Sloka 3 — '
                'phaladeepika:PG322:C1 (Sastri trans. 1950)')
LATTA_CITATION = ('[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, '
                  '2nd Ed. 1950 (archive.org: '
                  'Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG339')
LATTA_VERSE = 'Adh.XXVI PG338-339 Sloka 42-44'
MOON_SCOPE = 'excluding_on_demand_moon_obstruction'
CORPUS = json.loads((Path(__file__).resolve().parents[5] /
    'scripts/governance/__tests__/fixtures/phaladeepika_latta_d1_fixture.json').read_text())


def context(conn, payload=None, *, dry_run=False):
    config = {'chart_id': CHART}
    if payload is not None:
        config['vedha_candidate_payload'] = payload
    return SimpleNamespace(db_conn=conn, build_id=BUILD, config=config, dry_run=dry_run)


def house_payload():
    """XXVI.3: Sun h3 is obstructed at h9; no other primary is favourable."""
    from tests.l3.ka_vedha_gochara.test_overlays import residence
    r = residence()
    r.update(Sun=[(1, A, D)], Mars=[(2, A, B), (7, B, C), (2, C, D)],
             Mercury=[(11, A, D)], Jupiter=[(11, A, D)], Venus=[(5, A, D)])
    return bundle(residence=r)


def latta_rule(graha):
    row = next(r for r in CORPUS['bg_phaladeepika_latta'] if r['graha'] == graha)
    citation = next(r['source_citation'] for r in CORPUS['classical_text_chunks']
                    if r['chunk_id'] == 'phaladeepika_pg0339_c01')
    return {**{k: row[k] for k in ('graha', 'count_from_graha', 'direction', 'verse_ref')},
            'source_citation': citation}


def latta_payload(graha='Sun', cell=12, **kw):
    return bundle(latta_rules=[latta_rule(graha)],
                  nakshatra_residence={graha: [(cell, A, D)]}, **kw)


def narrow_coverage():
    # Request [B,C) inside the sky's [A,D): neither mechanism may extrapolate.
    return coverage_of((2460678.5, 2460680.5), (2460676.5, 2460682.5),
                       backend='swieph', convention_id='test')


def snapshot(conn, table):
    return conn.execute(f'SELECT to_jsonb(t) FROM {table} t ORDER BY to_jsonb(t)::text').fetchall()


def insert_row(conn, table, row):
    keys = list(row)
    conn.execute(f'INSERT INTO {table} (' + ','.join(keys) + ') VALUES (' +
                 ','.join(['%s'] * len(keys)) + ')',
                 [Jsonb(v) if isinstance(v, dict) else v for v in row.values()])


def store_house(conn):
    count = replace_candidate(context(conn), house_payload())
    assert count == 3  # inactive [A,B), active [B,C), inactive [C,D), XXVI.3


def test_house_intersection_stops_at_both_accepted_sky_edges():
    """Phaladipika XXVI.3 + packet §4: house intersections require sky coverage."""
    from tests.l3.ka_vedha_gochara.test_overlays import residence
    r = residence()
    r['Sun'] = [(1, A, D)]
    rows = [r for r in bundle(residence=r, coverage=narrow_coverage()).intervals
            if r['graha'] == 'Sun']
    assert [(r['t_in'], r['t_out']) for r in rows] == [
        (datetime.fromisoformat(B), datetime.fromisoformat(C))]


@pytest.mark.parametrize('graha,cell,count,direction', [
    ('Sun', 12, 12, 'forward'), ('Mars', 21, 3, 'forward'),
    ('Jupiter', 18, 6, 'forward'), ('Saturn', 16, 8, 'forward'),
    ('Venus', 27, 5, 'backward'), ('Mercury', 2, 7, 'backward'),
    ('Rahu', 4, 9, 'backward'), ('Moon', 17, 22, 'backward'),
])
def test_latta_inclusive_source_counts_and_provenance(graha, cell, count, direction):
    """XXVI.42-44 PG338-339: count inclusively, rear backwards, wrap at 27."""
    rows = latta_payload(graha, cell).intervals
    assert len(rows) == 1
    row = rows[0]
    assert (row['vedha_kind'], row['graha'], row['state'], row['source_qualification'],
            row['classical_citation'], row['t_in'], row['t_out']) == (
        'latta', graha, 'active', 'verse_cited', LATTA_CITATION,
        datetime.fromisoformat(A), datetime.fromisoformat(D))
    assert row['detail'] == {'source_nakshatra': cell, 'target_nakshatra': 23,
        'janma_reference_fact_id': 'moon-ref', 'verse_ref': LATTA_VERSE,
        'count_from_graha': count, 'direction': direction}


@pytest.mark.parametrize('change', [
    {'count_from_graha': 0}, {'count_from_graha': 28},
    {'count_from_graha': True}, {'count_from_graha': 12.5},
    {'direction': 'sideways'}, {'source_citation': ''}, {'verse_ref': ''},
])
def test_latta_rejects_invalid_or_uncited_rule_even_without_residence(change):
    """XXVI.42-44 + B.3/B.10: no count or source may be guessed for latta."""
    with pytest.raises(ValueError, match='count/direction/verse locator'):
        bundle(latta_rules=[{**latta_rule('Sun'), **change}], nakshatra_residence={})


def test_latta_intersection_stops_at_both_accepted_sky_edges():
    """XXVI.42-44 + packet §4: natal-star hits are limited to accepted coverage."""
    rows = latta_payload(coverage=narrow_coverage()).intervals
    assert len(rows) == 1
    assert (rows[0]['t_in'], rows[0]['t_out']) == (
        datetime.fromisoformat(B), datetime.fromisoformat(C))


def test_moon_house_primary_remains_on_demand_only():
    """XXVI.4 is cited, but ALGO 3.12/packet §4 exclude stored Moon testimony."""
    from tests.l3.ka_vedha_gochara.test_overlays import residence
    r = residence()
    r.update(Moon=[(1, A, D)], Mercury=[(11, A, D)],
             Jupiter=[(11, A, D)], Venus=[(5, A, D)])
    got = bundle(residence=r)
    assert got.intervals == ()
    assert {h['vedha_kind'] for h in got.headers} == {'house_vedha', 'latta', 'sarvatobhadra'}


def test_bound_dispatch_persists_literal_house_derivation_and_count(conn):
    """XXVI.3 PG322: Sun h3→h9, only Mars in h9 on [B,C); packet §4 dispatch."""
    result = KaVedhaGocharaWriter().run(context(conn, house_payload()))
    assert result.rows_inserted == 3
    assert conn.execute('SELECT count(*) FROM kala_vedha_gochara_candidate').fetchone() == (3,)
    rows = conn.execute('SELECT graha,t_in,t_out,state,classical_citation,detail,'
                        'obstructors,moon_scope,source_qualification '
                        'FROM kala_vedha_gochara_interval ORDER BY t_in').fetchall()
    assert rows == [
        ('Sun', datetime.fromisoformat(a), datetime.fromisoformat(b), state,
         SUN_CITATION, {'primary_house': 3, 'vedha_house': 9}, obstructors, scope, 'verse_cited')
        for a, b, state, obstructors, scope in [
            (A, B, 'inactive', [], MOON_SCOPE), (B, C, 'active', ['Mars'], None),
            (C, D, 'inactive', [], MOON_SCOPE)]]


def test_bound_latta_persists_source_metadata(conn):
    """XXVI.42-44 PG338-339: persisted forward 12th from 12 is janma star 23."""
    rule = latta_rule('Sun')
    conn.execute('INSERT INTO bg_phaladeepika_latta VALUES (%s,%s,%s,%s,%s)',
                 tuple(rule[k] for k in ('graha', 'count_from_graha', 'direction',
                                         'source_citation', 'verse_ref')))
    assert KaVedhaGocharaWriter().run(context(conn, latta_payload())).rows_inserted == 1
    assert conn.execute("SELECT classical_citation,detail FROM kala_vedha_gochara_interval WHERE vedha_kind='latta'").fetchone() == (
        LATTA_CITATION, {'source_nakshatra': 12, 'target_nakshatra': 23,
        'janma_reference_fact_id': 'moon-ref', 'verse_ref': LATTA_VERSE,
        'count_from_graha': 12, 'direction': 'forward'})


def test_bound_dry_run_dispatch_requires_no_database():
    """XXVI.3 derivation + packet §4: dry-run dispatch never enters persistence."""
    result = KaVedhaGocharaWriter().run(context(None, house_payload(), dry_run=True))
    assert result.rows_inserted == 0


def test_bound_dispatch_requires_typed_payload_before_storage(conn):
    """XXVI.3 source ledger + packet §4 typed v1 contract: reject untyped input."""
    with pytest.raises(TypeError, match='typed VedhaPayload'):
        KaVedhaGocharaWriter().run(context(conn, {'headers': house_payload().headers}))
    assert snapshot(conn, 'kala_vedha_gochara_candidate') == []


def test_direct_storage_dry_run_writes_neither_rows_headers_nor_attestations(conn):
    """XXVI.3 derivation + packet §4 dry run: validation conveys no write authority."""
    assert replace_candidate(context(conn, dry_run=True), house_payload()) == 0
    for table in ('kala_vedha_gochara_candidate', 'kala_vedha_gochara_interval',
                  'kala_layer_candidate_grain'):
        assert snapshot(conn, table) == []


def test_empty_families_attest_zero_rows_without_claiming_a_finding(conn):
    """XXVI.3-8/42-44 + packet §4: no favourable/hit input gives zero, not rows."""
    assert replace_candidate(context(conn), bundle()) == 0
    assert conn.execute('SELECT grain_key,result_state FROM kala_layer_candidate_grain ORDER BY grain_key').fetchall() == [
        ('ka_vedha_gochara:lahiri_chitrapaksha:house_vedha', 'zero_rows'),
        ('ka_vedha_gochara:lahiri_chitrapaksha:latta', 'zero_rows'),
        ('ka_vedha_gochara:lahiri_chitrapaksha:sarvatobhadra', 'zero_rows')]
    assert conn.execute('SELECT count(*) FROM kala_vedha_gochara_candidate').fetchone() == (3,)
    assert snapshot(conn, 'kala_vedha_gochara_interval') == []


def test_sql_partition_identity_immutable_even_with_valid_destination(conn):
    """XXVI.3-8 ledger + packet §4: valid alternate parents cannot rekey history."""
    replace_candidate(context(conn), bundle())
    conn.execute("INSERT INTO kala_layer_candidate SELECT chart_id,'candidate-2',build_id,state,conventions FROM kala_layer_candidate")
    with pytest.raises(psycopg.errors.RaiseException, match='identity is immutable'), conn.transaction():
        conn.execute("UPDATE kala_vedha_gochara_candidate SET generation='candidate-2' WHERE vedha_kind='sarvatobhadra'")


@pytest.mark.parametrize('pin', ['build', 'ayanamsha'])
def test_sql_rejects_valid_fact_in_wrong_natal_partition(conn, pin):
    """XXVI.3-8 are from janma Moon; B.3/packet §4 require its exact build/convention."""
    replace_candidate(context(conn), bundle())
    if pin == 'build':
        # The alternative build exists for this chart AND the alternative fact
        # matches it. Only the candidate's natal-build pin should reject this.
        conn.execute("INSERT INTO chart_facts SELECT 'other-moon',chart_id,%s,ayanamsha_id,fact_category,fact_subject,fact_key,fact_value_num FROM chart_facts", (BUILD,))
        with pytest.raises(psycopg.errors.RaiseException, match='natal pin'), conn.transaction():
            conn.execute("UPDATE kala_vedha_gochara_candidate SET natal_build_id=%s,janma_reference_fact_id='other-moon' WHERE vedha_kind='sarvatobhadra'", (BUILD,))
    else:
        conn.execute("INSERT INTO chart_facts SELECT 'other-moon',chart_id,build_id,'raman',fact_category,fact_subject,fact_key,fact_value_num FROM chart_facts")
        header = dict(bundle().headers[0], ayanamsha_id='raman', janma_reference_fact_id='other-moon')
        with pytest.raises(psycopg.errors.RaiseException, match='natal pin'), conn.transaction():
            insert_row(conn, 'kala_vedha_gochara_candidate', header)


@pytest.mark.parametrize('field,value', [('score', 1), ('segments', []), ('concurrent_latta_count', 2)])
def test_sql_refuses_uncalculated_scores_segments_and_latta_severity(conn, field, value):
    """XXVI.47-48 is enrichment only; packet §4 prohibits severity and JSON intervals."""
    store_house(conn)
    with pytest.raises(psycopg.errors.CheckViolation), conn.transaction():
        conn.execute("UPDATE kala_vedha_gochara_interval SET detail=detail || %s WHERE state='active'", (Jsonb({field: value}),))


@pytest.mark.parametrize('obstructor', ['Moon', 'Rahu', 'Ketu'])
def test_sql_refuses_moon_or_node_as_cited_house_obstructor(conn, obstructor):
    """XXVI.3-8 + ALGO 3.12: Moon on demand; node-only obstruction is unqualified."""
    store_house(conn)
    with pytest.raises(psycopg.errors.CheckViolation), conn.transaction():
        conn.execute("UPDATE kala_vedha_gochara_interval SET obstructors=%s WHERE state='active'", ([obstructor],))


@pytest.mark.parametrize('primary,obstructor,vedha_house', [('Sun', 'Saturn', 9), ('Saturn', 'Sun', 12)])
def test_sql_refuses_both_sun_saturn_exception_directions(conn, primary, obstructor, vedha_house):
    """Phaladipika XXVI.3/5 PG322-323: Sun and Saturn do not obstruct each other."""
    store_house(conn)
    with pytest.raises(psycopg.errors.CheckViolation), conn.transaction():
        conn.execute("UPDATE kala_vedha_gochara_interval SET graha=%s,obstructors=%s,detail=%s WHERE state='active'",
                     (primary, [obstructor], Jsonb({'primary_house': 3, 'vedha_house': vedha_house})))


def test_sql_parent_delete_requires_child_first_replacement(conn):
    """XXVI.3 provenance + packet §4: intervals retain a parent; never cascade history."""
    store_house(conn)
    before = snapshot(conn, 'kala_vedha_gochara_interval')
    with pytest.raises(psycopg.errors.ForeignKeyViolation), conn.transaction():
        conn.execute("DELETE FROM kala_vedha_gochara_candidate WHERE vedha_kind='house_vedha'")
    assert snapshot(conn, 'kala_vedha_gochara_interval') == before
    conn.execute('DELETE FROM kala_vedha_gochara_interval')
    conn.execute("DELETE FROM kala_vedha_gochara_candidate WHERE vedha_kind='house_vedha'")


@pytest.mark.parametrize('qualification', ['algorithmic_approximation', 'unsourced'])
def test_sql_only_accepts_verse_cited_interval_findings(conn, qualification):
    """XXVI.3-8/42-44 + packet §4: no approximation may masquerade as a cited interval."""
    store_house(conn)
    with pytest.raises(psycopg.errors.CheckViolation), conn.transaction():
        conn.execute('UPDATE kala_vedha_gochara_interval SET source_qualification=%s', (qualification,))


@pytest.mark.parametrize('patch', [
    "obstructors=ARRAY[]::text[]",
    "unknown_obstructors=ARRAY['Venus']",
    "reasons=ARRAY['obstructor_residence_unknown']",
    "state='inactive',obstructors=ARRAY[]::text[],moon_scope=NULL",
    "state='unqualified',obstructors=ARRAY[]::text[]",
    "state='unqualified',obstructors=ARRAY[]::text[],reasons=ARRAY['node_obstruction_undecided'],unqualified_reason='obstructor_residence_unknown'",
])
def test_sql_state_reason_scope_and_obstructor_must_agree(conn, patch):
    """XXVI.3-8 + ALGO 3.12: active requires a witness; uncertainty/scope stay explicit."""
    store_house(conn)
    with pytest.raises(psycopg.errors.CheckViolation), conn.transaction():
        conn.execute("UPDATE kala_vedha_gochara_interval SET " + patch + " WHERE state='active'")


@pytest.mark.parametrize('detail', [{}, {'primary_house': 0, 'vedha_house': 9},
    {'primary_house': 3, 'vedha_house': 13}, {'primary_house': 3, 'vedha_house': 3}])
def test_sql_house_detail_requires_distinct_zodiac_houses(conn, detail):
    """XXVI.3-8 + packet §4: house vedha needs two distinct houses in 1..12."""
    store_house(conn)
    with pytest.raises(psycopg.errors.CheckViolation), conn.transaction():
        conn.execute("UPDATE kala_vedha_gochara_interval SET detail=%s WHERE state='active'", (Jsonb(detail),))


@pytest.mark.parametrize('primary', ['Moon', 'Rahu', 'Ketu'])
def test_sql_house_primary_domain_cannot_store_on_demand_or_uncited_grahas(conn, primary):
    """XXVI.3-8 + ALGO 3.12: nodes lack cited pairs; Moon stays on demand."""
    store_house(conn)
    with pytest.raises(psycopg.errors.CheckViolation), conn.transaction():
        conn.execute("UPDATE kala_vedha_gochara_interval SET graha=%s WHERE state='active'", (primary,))


def test_sql_orphan_interval_cannot_outlive_missing_family_header(conn):
    """XXVI.3 ledger + packet §4: the family coverage/source header is mandatory."""
    store_house(conn)
    row = conn.execute("SELECT to_jsonb(t) FROM kala_vedha_gochara_interval t WHERE state='active'").fetchone()[0]
    conn.execute('DELETE FROM kala_vedha_gochara_interval')
    conn.execute("DELETE FROM kala_vedha_gochara_candidate WHERE vedha_kind='house_vedha'")
    with pytest.raises(psycopg.errors.ForeignKeyViolation), conn.transaction():
        insert_row(conn, 'kala_vedha_gochara_interval', row)
