"""KA-3a acceptance detectors for the independent review's surviving reversions.

Classical expectations are re-derived from the cited rules, not JH parity or
another implementation. Sky cases are planted exact boundary inputs, not claimed
observations of Mercury on these dates. Fingerprints test input sensitivity.
"""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from services.kala_core.overlays import sky_residences
from services.kala_core.sky import SkyResult
from services.kala_core.sky.coverage import coverage_of
from services.kala_core.sky.ephemeris import BodyPosition, EphemerisAnswer
from tests.l3.ka_vedha_gochara.test_overlays import A, B, C, D, ROWS, bundle, residence


def sky_inputs(relation, longitude, cells_after):
    coverage = coverage_of((2460676.5, 2460682.5), (2460676.5, 2460682.5),
                           backend='swieph', convention_id='planted-sidereal')
    initial = SkyResult((EphemerisAnswer(
        2460676.5, 'UT', 'swiss_instant', 'swieph', 0, 'flags', 'mean',
        'lahiri_chitrapaksha', 24, 'planted-sidereal',
        (BodyPosition('Mercury', longitude, -1),)),), coverage)
    events = SkyResult(tuple(SimpleNamespace(body='Mercury', relation=relation,
        jd=jd, cell_after=cell) for jd, cell in zip((2460678.5, 2460680.5), cells_after)), coverage)
    return events, initial


@pytest.mark.parametrize('relation,longitude,cells_after,expected', [
    ('sign_ingress', 1, (11, 0), (1, 12, 1)),
    ('sign_ingress', 31, (0, 11), (2, 1, 12)),
    ('nakshatra_ingress', 1, (26, 0), (1, 27, 1)),
    ('nakshatra_ingress', 14, (0, 26), (2, 1, 27)),
])
def test_sky_ingress_destination_handles_retrograde_seam_and_reentry(
        relation, longitude, cells_after, expected):
    # SkyEvent.cell_after is the zero-based cell occupied after the crossing:
    # services/kala_core/sky/events.py:59-65,99. Backward crossings decrement,
    # including 1 -> 12/27; the following direct crossing returns to cell 1.
    events, initial = sky_inputs(relation, longitude, cells_after)
    assert sky_residences(events, initial, 'Mercury', relation) == tuple(
        (cell, lo, hi) for cell, lo, hi in zip(expected, (A, B, C), (B, C, D)))


@pytest.mark.parametrize('initial_convention', ['tropical', 'other-ayanamsha'])
def test_sky_conventions_must_match_before_combining_positions_and_events(initial_convention):
    events, initial = sky_inputs('sign_ingress', 1, (11, 0))
    initial = replace(initial, coverage=replace(initial.coverage, convention_id=initial_convention))
    with pytest.raises(ValueError, match='convention mismatch'):
        sky_residences(events, initial, 'Mercury')


# Literal transcription of Phaladipika XXVI.42-44, Sastri 1950 PG338-339:
# Sun 12, Mars 3, Jupiter 6, Saturn 8 forward; Venus 5, Mercury 7, Rahu 9,
# Moon 22 rearward. Inclusive counting starts at the occupied star (count 1).
# Source text is preserved in brahmagyan/l0_phaladeepika_vedha.py:22-33;
# do not import its computed rows as the oracle's expected values.
LATTA_RULES = (
    ('Sun', 12, 'forward'), ('Mars', 3, 'forward'),
    ('Jupiter', 6, 'forward'), ('Saturn', 8, 'forward'),
    ('Venus', 5, 'backward'), ('Mercury', 7, 'backward'),
    ('Rahu', 9, 'backward'), ('Moon', 22, 'backward'),
)
LATTA_CITATION = ('[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 '
    '(archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG339')
LATTA_VERSE = 'Adh.XXVI PG338-339 Sloka 42-44'


def latta_rule(graha, count, direction):
    return dict(graha=graha, count_from_graha=count, direction=direction,
                source_citation=LATTA_CITATION, verse_ref=LATTA_VERSE)


@pytest.mark.parametrize('graha,count,direction', LATTA_RULES)
@pytest.mark.parametrize('occupied', range(1, 28))
def test_latta_rederived_by_walking_cited_inclusive_star_count(graha, count, direction, occupied):
    # Walk the named star circle, independently of the production modulo formula.
    stars = list(range(1, 28))
    ordered = stars if direction == 'forward' else list(reversed(stars))
    origin = ordered.index(occupied)
    target = (ordered[origin:] + ordered[:origin])[count - 1]
    rule = latta_rule(graha, count, direction)
    for natal in (target, stars[(stars.index(target) + 1) % 27]):
        fact = {'fact_id': 'moon-ref', 'fact_value_num': (natal - 0.5) * (360 / 27)}
        result = bundle(janma_fact=fact, latta_rules=[rule],
                        nakshatra_residence={graha: [(occupied, A, B), (occupied, C, D)]})
        rows = [r for r in result.intervals if r['vedha_kind'] == 'latta']
        if natal != target:
            assert rows == [], 'adjacent natal star is not the cited latta target'
            continue
        assert [(r['graha'], r['t_in'].isoformat(), r['t_out'].isoformat(), r['state'])
                for r in rows] == [(graha, A, B, 'active'), (graha, C, D, 'active')]
        for row in rows:
            assert row['source_qualification'] == 'verse_cited'
            assert row['classical_citation'] == LATTA_CITATION
            assert row['detail'] == dict(source_nakshatra=occupied, target_nakshatra=target,
                janma_reference_fact_id='moon-ref', verse_ref=LATTA_VERSE,
                count_from_graha=count, direction=direction)


def test_house_interval_carries_exact_l0_rule_citation():
    # Phaladipika XXVI.3 (PG322:C1): Sun in house 3 has vedha at house 9.
    # Aquarius Moon + Sun Aries => house 3; Mars Libra => house 9.
    r = residence()
    r['Sun'] = [(1, A, D)]
    r['Mars'] = [(2, A, B), (7, B, C), (2, C, D)]
    rows = [x for x in bundle(residence=r).intervals if x['graha'] == 'Sun']
    assert [(x['t_in'].isoformat(), x['t_out'].isoformat(), x['state']) for x in rows] == [
        (A, B, 'inactive'), (B, C, 'active'), (C, D, 'inactive')]
    citation, = [row[3] for row in ROWS if row[:3] == ['sun', 3, 9]]
    assert 'Sloka 3' in citation and 'PG322:C1' in citation
    for row in rows:
        assert row['classical_citation'] == citation
        assert row['source_qualification'] == 'verse_cited'
        assert row['detail'] == {'primary_house': 3, 'vedha_house': 9}
    assert rows[1]['obstructors'] == ['Mars']


@pytest.mark.parametrize('field,value', [
    ('count_from_graha', 8), ('direction', 'forward'),
    ('source_citation', 'changed source edition'), ('verse_ref', 'changed locator'),
])
def test_fingerprint_tracks_every_latta_rule_input_even_without_matching_intervals(field, value):
    rule = latta_rule('Mercury', 7, 'backward')
    first = bundle(latta_rules=[rule])
    changed = bundle(latta_rules=[{**rule, field: value}])
    assert first.intervals == changed.intervals == ()
    for before, after in zip(first.headers, changed.headers):
        assert before['upstream_fingerprint'] != after['upstream_fingerprint']


def test_fingerprint_tracks_ayanamsha_when_sky_and_natal_values_are_equal():
    first, changed = bundle(), bundle(ayanamsha_id='raman')
    assert first.intervals == changed.intervals == ()
    for before, after in zip(first.headers, changed.headers):
        assert before['upstream_fingerprint'] != after['upstream_fingerprint']


def test_fingerprint_canonicalizes_latta_rule_order():
    rules = [latta_rule(*row) for row in LATTA_RULES]
    assert bundle(latta_rules=rules).headers[0]['upstream_fingerprint'] == bundle(
        latta_rules=list(reversed(rules))).headers[0]['upstream_fingerprint']
