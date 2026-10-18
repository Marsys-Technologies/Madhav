"""KA-3a coverage_and_qualification: source-led, non-golden regression oracles.

Authority: PACKET_KA-3a_v1.md §4 (coverage, qualification, fingerprint and
legacy compatibility); KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md §3.12.
Classical locators: Phaladipika XXVI.3-8 (PG322-323), PG338-339 slokas
42-44 (latta), XXVI.47-48 (enrichment). B.3 requires their input ledger;
B.10 and CLAUDE.md N.7.6 forbid a judgment outside established coverage.

The existing bundle's moon-ref/300 and residence dates are planted protocol
fixtures, NOT observations or recomputations of any native's chart. Source
passages below come from the raw, provenance-only corpus export, never an
implementation-output/golden capture. DB fixtures own create/drop/rollback.
"""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from psycopg.types.json import Jsonb

from services.ka_vedha_gochara import candidate
from services.ka_vedha_gochara.storage import replace_candidate
from services.kala_core.sky.coverage import coverage_of
from tests.l3.ka_vedha_gochara.test_overlays import A, B, C, D, ROWS, bundle
from tests.l3.kala_db.conftest import kala_db_dsn  # noqa: F401 -- guarded fixture
from tests.l3.kala_db.ka_vedha_gochara.conftest import BUILD, CHART, conn  # noqa: F401


HOUSE_SOURCE = 'Phaladipika XXVI.3-8, phaladeepika:PG322:C1 / PG323:C1'
LATTA_SOURCE = 'Phaladipika Adh.XXVI PG338-339 Sloka 42-44'
ENRICHMENT_SOURCE = 'Phaladipika XXVI.47-48, phaladeepika_pg0339_c01'
FAMILIES = ('house_vedha', 'sarvatobhadra', 'latta')
SOURCE_FIXTURE = (Path(__file__).resolve().parents[4] /
                  'scripts/governance/__tests__/fixtures/phaladeepika_latta_d1_fixture.json')
SOURCE_CHUNKS = json.loads(SOURCE_FIXTURE.read_text())['classical_text_chunks']
SUN_RULE = {'graha': 'Sun', 'count_from_graha': 12, 'direction': 'forward',
            'source_citation': SOURCE_CHUNKS[1]['source_citation'],
            'verse_ref': 'Adh.XXVI PG338-339 Sloka 42-44'}
ENRICHMENT = {'passage': SOURCE_CHUNKS[1]['content_en'],
              'locator': 'phaladeepika_pg0339_c01', 'verses': 'XXVI.47-48'}


def covered(**changes):
    args = dict(requested=(2460676.5, 2460682.5),
                source_interval=(2460676.5, 2460682.5),
                backend='swieph', convention_id='test')
    args.update(changes)
    return coverage_of(**args)


def header(value, family):
    return next(h for h in value.headers if h['vedha_kind'] == family)


def digests(value):
    return {h['vedha_kind']: h['upstream_fingerprint']['digest'] for h in value.headers}


def store(db, value):
    return replace_candidate(SimpleNamespace(db_conn=db, build_id=BUILD,
        config={'chart_id': CHART}, dry_run=False), value)


def stored(db):
    return {table: db.execute(f'SELECT to_jsonb(t) FROM {table} t ORDER BY to_jsonb(t)::text').fetchall()
            for table in ('kala_vedha_gochara', 'kala_vedha_gochara_candidate',
                          'kala_vedha_gochara_interval', 'kala_layer_candidate_grain')}


@pytest.mark.parametrize('requested', [(2460000.5, 2460006.5), (2460682.5, 2460688.5)])
@pytest.mark.parametrize('family', FAMILIES)
def test_every_family_outside_sky_horizon_is_unsearched(requested, family):
    """XXVI.3-8 / PG338-339: no established residence => no searched judgment (§3.12)."""
    value = bundle(coverage=covered(requested=requested))
    h = header(value, family)
    assert h['coverage']['search_state'] == 'unsearched'
    assert h['coverage']['covered'] is None
    assert h['coverage']['complete'] is False
    assert h['coverage']['gaps'] == [list(requested)]
    assert h['method_qualification'] is None
    assert h['null_reason'] == 'information_unavailable'
    assert value.intervals == ()


@pytest.mark.parametrize('family', FAMILIES)
def test_partial_sky_horizon_is_never_searched_as_complete(family):
    """XXVI.3-8 / PG338-339 with packet §4: coverage is the source/request intersection."""
    value = bundle(coverage=covered(requested=(2460674.5, 2460680.5)))
    cov = header(value, family)['coverage']
    assert cov['search_state'] == 'partial'
    assert cov['covered'] == [2460676.5, 2460680.5]
    assert cov['gaps'] == [[2460674.5, 2460676.5]]
    assert cov['complete'] is False


def test_latta_without_cited_counting_rules_cannot_be_qualified():
    """PG338-339 slokas 42-44: no source rule means absence, never qualified zero latta."""
    h = header(bundle(latta_rules=[]), 'latta')
    assert h['method_qualification'] is None
    assert h['null_reason'] == 'information_unavailable'
    assert h['payload']['ketu_gap'] == 'information_unavailable'


@pytest.mark.parametrize('field,value', [('passage', None), ('passage', ''),
    ('locator', None), ('locator', ''), ('verses', None), ('verses', 'XXVI.42-44'),
    ('verses', 'XXV.47-48')])
def test_enrichment_requires_passage_locator_and_exact_verses(field, value):
    """XXVI.47-48 is enrichment only; B.3 refuses an absent/misattributed source."""
    invalid = {**ENRICHMENT, field: value}
    with pytest.raises(ValueError, match='passage.*47-48'):
        bundle(enrichment=invalid)


def test_cited_enrichment_is_preserved_without_computing_severity():
    """XXVI.47-48 / packet §4: preserve verbatim evidence, never compute multipliers."""
    h = header(bundle(enrichment=ENRICHMENT), 'latta')
    assert h['payload']['enrichment'] == {**ENRICHMENT, 'applied_to_computation': False}


@pytest.mark.parametrize('dependency', ['nakshatra_residence', 'l0_pair_authority',
    'latta_source_rules', 'enrichment_passage', 'enrichment_locator',
    'natal_moon_fact_id', 'natal_moon_value', 'sky_coverage', 'sky_convention',
    'ayanamsha_identity', 'formula_version'])
def test_fingerprint_changes_for_each_consumed_input(dependency, monkeypatch):
    """B.3 ledger for XXVI.3-8 / PG338-339 / XXVI.47-48; packet §4 freshness rule.

    Change exactly one input, without pinning any implementation digest.
    The natal-value case uses an actual Swiss computation, not an invented
    observation. It tests ledger sensitivity, not the native's birth chart.
    """
    args = dict(latta_rules=[SUN_RULE], nakshatra_residence={'Sun': [(12, A, D)]},
                enrichment=ENRICHMENT)
    baseline = bundle(**args)
    if dependency == 'nakshatra_residence':
        args['nakshatra_residence'] = {'Sun': [(12, A, B), (12, C, D)]}
    elif dependency == 'l0_pair_authority':
        pairs = deepcopy(ROWS)
        # Same cited doctrine, changed source annotation: still changes authority identity.
        pairs[0][3] += ' [source annotation revision]'
        args['pairs_rows'] = pairs
    elif dependency == 'latta_source_rules':
        args['latta_rules'] = []
    elif dependency == 'enrichment_passage':
        args['enrichment'] = {**ENRICHMENT, 'passage': SOURCE_CHUNKS[0]['content_en']}
    elif dependency == 'enrichment_locator':
        args['enrichment'] = {**ENRICHMENT, 'locator': SOURCE_CHUNKS[0]['chunk_id']}
    elif dependency == 'natal_moon_fact_id':
        args['janma_fact'] = {**baseline.janma_fact, 'fact_id': 'other-moon-source'}
    elif dependency == 'natal_moon_value':
        from services.kala_core.sky.ephemeris import ephemeris_at
        answer = ephemeris_at(2460676.5, bodies=('Moon',))
        args['janma_fact'] = {**baseline.janma_fact, 'fact_value_num': answer.values[0].positions[0].longitude_deg}
    elif dependency == 'sky_coverage':
        args['coverage'] = covered(source_interval=(2460676.5, 2460680.5))
    elif dependency == 'sky_convention':
        args['coverage'] = covered(convention_id='different-source-convention')
    elif dependency == 'ayanamsha_identity':
        args['ayanamsha_id'] = 'raman'
    else:
        monkeypatch.setattr(candidate, 'FORMULA_VERSION', 'ka_vedha_candidate/test-revision')
    changed = bundle(**args)
    for family in FAMILIES:
        assert digests(baseline)[family] != digests(changed)[family], dependency


def test_fingerprint_ignores_source_row_order_and_mapping_insertion_order():
    """XXVI.3-8 / PG338-339: ledger identity follows evidence content, not load order."""
    moon = {**SUN_RULE, 'graha': 'Moon', 'count_from_graha': 22, 'direction': 'backward'}
    args = dict(latta_rules=[SUN_RULE, moon],
                nakshatra_residence={'Sun': [(12, A, D)], 'Moon': [(17, A, D)]},
                enrichment=ENRICHMENT)
    one = bundle(**args)
    two = bundle(**{**args, 'pairs_rows': list(reversed(ROWS)),
        'latta_rules': [dict(reversed(list(moon.items()))), SUN_RULE],
        'nakshatra_residence': dict(reversed(list(args['nakshatra_residence'].items())))})
    assert digests(one) == digests(two)


@pytest.mark.parametrize('longitude', [-1.0, 360.0, float('nan'), float('inf'), -float('inf')])
def test_invalid_natal_longitude_is_refused_even_without_transit_residences(longitude):
    """XXVI.3-8 / PG338-339 consume a valid janma reference; B.10 forbids guessing it."""
    with pytest.raises(ValueError, match='natal Moon longitude'):
        bundle(residence={}, nakshatra_residence={},
               janma_fact={'fact_id': 'moon-ref', 'fact_value_num': longitude})


@pytest.mark.parametrize('column,data_type', [('method_qualification', 'text'),
    ('coverage', 'jsonb'), ('upstream_fingerprint', 'jsonb')])
def test_legacy_nullable_columns_exist_without_backfilling_judgments(conn, column, data_type):
    """XXVI.3-8 / PG338-339: legacy rows gain no unearned qualification (packet §4)."""
    info = conn.execute('SELECT data_type,is_nullable,column_default FROM information_schema.columns '
                        'WHERE table_schema=current_schema() AND table_name=%s AND column_name=%s',
                        ('kala_vedha_gochara', column)).fetchone()
    assert info == (data_type, 'YES', None)
    assert conn.execute(f'SELECT {column} FROM kala_vedha_gochara').fetchall() == [(None,)]
    # Exercise typed values, then restore absence; existing IDs/date keys/payload survive.
    prior = conn.execute('SELECT id,chart_id,detail,window_start FROM kala_vedha_gochara').fetchall()
    value = 'qualified' if column == 'method_qualification' else Jsonb({'fixture': 'typed'})
    conn.execute(f'UPDATE kala_vedha_gochara SET {column}=%s', (value,))
    conn.execute(f'UPDATE kala_vedha_gochara SET {column}=NULL')
    assert conn.execute('SELECT id,chart_id,detail,window_start FROM kala_vedha_gochara').fetchall() == prior


@pytest.mark.parametrize('chapter,start,end', [(25, 47, 48), (26, 48, 48), (26, 47, 47)])
def test_enrichment_storage_refuses_wrong_chapter_or_incomplete_verse_span(conn, chapter, start, end):
    """XXVI.47-48 / B.3: matching text and locator cannot substitute for verse identity."""
    conn.execute("INSERT INTO classical_text_chunks VALUES (%s,'phaladeepika',%s,%s,%s,%s)",
                 (ENRICHMENT['locator'], chapter, start, end, ENRICHMENT['passage']))
    before = stored(conn)
    with pytest.raises(ValueError, match='verbatim cited source'):
        store(conn, bundle(enrichment=ENRICHMENT))
    assert stored(conn) == before


def test_enrichment_storage_accepts_verbatim_passage_at_required_chapter_and_verses(conn):
    """XXVI.47-48: positive control for the source-admission refusal oracle."""
    # This isolated fixture stages the exported passage with the API's chapter/
    # verse metadata; it makes no claim about any remote corpus row's metadata.
    conn.execute("INSERT INTO classical_text_chunks VALUES (%s,'phaladeepika',26,47,48,%s)",
                 (ENRICHMENT['locator'], ENRICHMENT['passage']))
    assert store(conn, bundle(enrichment=ENRICHMENT)) == 0
    assert conn.execute("SELECT payload->'enrichment' FROM kala_vedha_gochara_candidate WHERE vedha_kind='latta'").fetchone()[0] == {
        **ENRICHMENT, 'applied_to_computation': False}


@pytest.mark.parametrize('family', FAMILIES)
def test_storage_refuses_outside_horizon_claimed_as_searched_before_replacement(conn, family):
    """XXVI.3-8 / PG338-339, N.7.6: typed payloads cannot attest to an unsearched sky."""
    value = bundle(coverage=covered(requested=(2460000.5, 2460006.5)))
    store(conn, value)
    before = stored(conn)
    dishonest = replace(value, headers=tuple(
        {**h, 'coverage': {**h['coverage'], 'search_state': 'searched'}}
        if h['vedha_kind'] == family else h for h in value.headers))
    with pytest.raises(ValueError, match='coverage.*unsearched'):
        store(conn, dishonest)
    assert stored(conn) == before


@pytest.mark.parametrize('missing', ['rules', 'source_citation', 'verse_ref'])
def test_storage_refuses_latta_qualification_without_cited_rules_before_replacement(conn, missing):
    """PG338-339 slokas 42-44 / B.3: qualified latta requires an actual cited counting rule."""
    value = bundle()
    store(conn, value)
    before = stored(conn)
    rules = [] if missing == 'rules' else [{**SUN_RULE, missing: ''}]
    if rules:
        # Even agreement with an uncited L0 row cannot earn source qualification.
        rule = rules[0]
        conn.execute('INSERT INTO bg_phaladeepika_latta VALUES (%s,%s,%s,%s,%s)',
                     tuple(rule[k] for k in ('graha', 'count_from_graha', 'direction', 'source_citation', 'verse_ref')))
    dishonest = replace(value, sources={**value.sources, 'latta_rules': rules}, headers=tuple(
        {**h, 'method_qualification': 'qualified', 'null_reason': None}
        if h['vedha_kind'] == 'latta' else h for h in value.headers))
    with pytest.raises(ValueError, match='latta.*cited.*rules'):
        store(conn, dishonest)
    assert stored(conn) == before
