"""KA-3a overlays_module input oracles (review survivors O19–O25, O29).

Classical authority: Phaladipika XXVI.3–8, phaladeepika:PG322:C1 and
PG323:C1 (the existing, read-only L0 fixture). KA-3a packet §4 and algorithm
brief §3.12 require exact half-open residences in one sky convention before
applying those Moon-relative rules. The classical text supplies the vedha
rule; the packet supplies these modern validation/coverage requirements.

B.3/B.10: no captured overlay output or invented chart positions. Sky
positions and ingress roots are computed with the real Swiss corpus. The
only altered numerical inputs are deliberately invalid domain/error probes.
No test claims a natal-chart interpretation or writes L0/L1/L2 data.
"""
from dataclasses import replace
from datetime import date
import json
import os
from pathlib import Path

import pytest

from services.gochara_kernel.arcs import build_arc_index
from services.gochara_kernel.overlays import date_to_jd
from services.gochara_kernel.substrate import jd_to_utc
from services.gochara_rules.vedha_derive import pairs_from_rows
from services.kala_core.overlays import (
    house_intervals, sky_residences, validated_residence,
)
from services.kala_core.sky import (
    SkyConvention, SkyResult, boundary_events, coverage_of, ephemeris_at,
    unavailable,
)


@pytest.fixture(scope='module')
def sky():
    """Real January 2025 roots, independently checked by Swiss positions."""
    start = date_to_jd(date(2025, 1, 1))
    end = date_to_jd(date(2025, 2, 1))
    jds = tuple(start + day for day in range(32))
    convention = SkyConvention()
    ephe_path = os.environ['SE_EPHE_PATH']
    samples = tuple(ephemeris_at(jd, convention, bodies=('Sun', 'Venus', 'Moon'),
                                ephe_path=ephe_path)
                    for jd in jds)
    assert all(sample.available for sample in samples), 'real Swiss corpus required'
    initial = samples[0]
    all_events = []
    for body, relations in (('Sun', ('sign_ingress', 'nakshatra_ingress')),
                            ('Venus', ('sign_ingress',))):
        index = build_arc_index(body, jds, tuple(
            sample.values[0].position(body).longitude_deg for sample in samples))
        result = boundary_events(index, body, relations, (start, end),
                                 convention.convention_id, ephe_path=ephe_path)
        assert result.available
        assert result.values, f'fixture must contain real {body} ingress roots'
        all_events.extend(result.values)
    coverage = coverage_of((start, end), (start, end), backend='swieph',
                           convention_id=convention.convention_id)
    sun = tuple(event for event in all_events
                if event.body == 'Sun' and event.relation == 'sign_ingress')
    assert len(sun) == 1, 'fixture must straddle one actual solar sign ingress'
    crossing = sun[0]
    before = int(initial.values[0].position('Sun').longitude_deg // 30) + 1
    after_position = ephemeris_at(crossing.jd + 1e-4, convention, bodies=('Sun',),
                                  ephe_path=ephe_path)
    assert after_position.available
    after = int(after_position.values[0].position('Sun').longitude_deg // 30) + 1
    assert before != after
    # Expected residence comes from Swiss geometry and the half-open rule,
    # never from sky_residences or validated_residence.
    a, b, c = (jd_to_utc(jd).isoformat() for jd in (start, crossing.jd, end))
    expected = ((before, a, b), (after, b, c))
    return initial, SkyResult(sun, coverage), SkyResult(tuple(all_events), coverage), expected


@pytest.fixture(scope='module')
def pairs():
    path = Path(__file__).parents[1] / 'gochara_rules/fixtures/l0_vedha_rows_2026_10_02.json'
    return pairs_from_rows(json.loads(path.read_text()))


@pytest.mark.parametrize('side', ('events', 'initial'))
def test_o19_refuses_mixed_sky_conventions(sky, side):
    """Phaladipika XXVI.3–8 / PG322–323: compare houses in one frame (KA-3a §4)."""
    initial, events, _, expected = sky
    assert sky_residences(events, initial, 'Sun') == expected
    different = SkyConvention(node_model='true').convention_id
    if side == 'events':
        events = replace(events, coverage=replace(events.coverage, convention_id=different))
    else:
        initial = replace(initial, coverage=replace(initial.coverage, convention_id=different))
    with pytest.raises(ValueError, match='convention mismatch'):
        sky_residences(events, initial, 'Sun')


@pytest.mark.parametrize('bad_time', ('before', 'at_end', 'after', 'nan', 'inf', '-inf'))
def test_o20_refuses_nonfinite_or_uncovered_ingress(sky, bad_time):
    """Phaladipika XXVI.3–8 / PG322–323; KA-3a §4: only accepted sky horizon."""
    initial, events, _, _ = sky
    lo, hi = events.coverage.covered
    invalid = {'before': lo - 1, 'at_end': hi, 'after': hi + 1,
               'nan': float('nan'), 'inf': float('inf'), '-inf': -float('inf')}[bad_time]
    # Corrupt only the timestamp of a real event, preserving its body/relation.
    malformed = replace(events, values=(replace(events.values[0], jd=invalid),))
    with pytest.raises(ValueError, match='outside covered interval'):
        sky_residences(malformed, initial, 'Sun')


@pytest.mark.parametrize('unrelated', ('body', 'relation', 'both'))
def test_o21_other_body_or_relation_cannot_change_solar_sign_residence(sky, unrelated):
    """Phaladipika XXVI.3 / PG322:C1: Sun's sign occupancy uses Sun sign roots."""
    initial, events, mixed, expected = sky
    foreign = tuple(event for event in mixed.values
                    if ((unrelated in ('body', 'both') and event.body != 'Sun')
                        or (unrelated in ('relation', 'both')
                            and event.relation != 'sign_ingress')))
    assert foreign, 'fixture must exercise the requested irrelevant-event branch'
    result = replace(events, values=events.values + foreign)
    assert sky_residences(result, initial, 'Sun') == expected


@pytest.mark.parametrize('missing', ('events', 'initial', 'horizon'))
def test_o22_unavailable_sky_never_establishes_residence(sky, missing):
    """Phaladipika XXVI.3–8 / PG322–323; brief §3.12: unknown occupancy is no proof."""
    initial, events, _, _ = sky
    if missing == 'initial':
        initial = unavailable(initial.coverage)
    elif missing == 'events':
        events = unavailable(events.coverage)
    else:
        events = unavailable(coverage_of(events.coverage.requested, None,
                             backend='swieph', convention_id=events.coverage.convention_id))
    assert sky_residences(events, initial, 'Sun') == ()


def test_available_empty_event_search_establishes_unchanged_residence(sky):
    """Phaladipika XXVI.3 / PG322:C1; KA-3a §4: searched empty differs from unknown."""
    initial, events, _, expected = sky
    lo, _ = events.coverage.covered
    hi = events.values[0].jd
    coverage = coverage_of((lo, hi), (lo, hi), backend='swieph',
                           convention_id=events.coverage.convention_id)
    assert sky_residences(SkyResult((), coverage), initial, 'Sun') == (expected[0],)


@pytest.mark.parametrize('mapping', ('unvalidated_complete', 'partial', 'missing_requested_pair'))
def test_o23_only_validated_complete_cited_authority_is_usable(sky, pairs, mapping):
    """Phaladipika XXVI.3–8 / PG322–323: missing authority cannot mean inapplicable."""
    initial, _, _, spans = sky
    moon_sign = int(initial.values[0].position('Moon').longitude_deg // 30) + 1
    raw = dict(pairs)
    if mapping == 'partial':
        raw = {('Sun', 3): pairs[('Sun', 3)]}
    elif mapping == 'missing_requested_pair':
        del raw[('Sun', 3)]
    with pytest.raises(ValueError, match='validated complete L0 load'):
        house_intervals('Sun', 3, (spans[0][1], spans[-1][2]), moon_sign=moon_sign,
                        residence={}, pairs=raw)


@pytest.mark.parametrize('invalid_sign', (0, 13, -1, True, 11.0))
def test_o24_invalid_janma_rasi_cannot_define_cited_house(sky, pairs, invalid_sign):
    """Phaladipika XXVI.3 / PG322:C1: Moon-relative houses require a 1..12 sign."""
    _, _, _, spans = sky
    with pytest.raises(ValueError, match='moon_sign must be 1..12'):
        house_intervals('Sun', 3, (spans[0][1], spans[-1][2]), moon_sign=invalid_sign,
                        residence={}, pairs=pairs)


@pytest.mark.parametrize('invalid_span', ('empty', 'reversed'))
def test_o25_primary_residence_requires_positive_half_open_extent(sky, pairs, invalid_span):
    """Phaladipika XXVI.3 / PG322:C1; brief §3.12: intersect actual residence spans."""
    initial, _, _, spans = sky
    lo, hi = spans[0][1], spans[-1][2]
    span = (lo, lo) if invalid_span == 'empty' else (hi, lo)
    moon_sign = int(initial.values[0].position('Moon').longitude_deg // 30) + 1
    with pytest.raises(ValueError, match='empty or reversed primary interval'):
        house_intervals('Sun', 3, span, moon_sign=moon_sign, residence={}, pairs=pairs)


def test_o29_disjoint_residence_is_chronological_regardless_of_input_order(sky):
    """Phaladipika XXVI.3 / PG322:C1; KA-3a §4: occupancy follows time, not row order."""
    initial, events, _, expected = sky
    # Reverse real, adjacent Swiss-derived residences; this is not overlap.
    shuffled = tuple(reversed(expected))
    assert validated_residence(shuffled) == list(expected)
    assert sky_residences(events, initial, 'Sun') == tuple(validated_residence(shuffled))
