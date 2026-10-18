"""KA3B-R1: sky availability cannot certify uncomputed annual objects.

Ports the independent review's year-42/year-43 reproduction with real Swiss
positions. Restoring sky-only coverage in either builder or the overlay must
fail these assertions in NOW and AHEAD.
"""
from datetime import date, datetime, timezone

import pytest

from services.kala_core.overlays.contested import testimony as read_testimony
from tests.l3.ka_adapters.test_candidates import api, context, sign_context, cov, LO


def annual(family, years, coverage=None, **changes):
    args = dict(years=years, coverage=coverage or cov(LO, LO+2000, source=(LO, LO+2000)))
    if family == 'sudarshana_varsha':
        args.update(ctx=sign_context(), birth_date=date(1984, 2, 5), year_anchor='civil_birthday')
    else:
        args.update(ctx=context(), birth_dt=datetime(1984, 2, 5, 5, 13, tzinfo=timezone.utc))
    args.update(changes)
    return api(family).build_candidate(**args)


@pytest.mark.parametrize('family', ['sudarshana_varsha', 'tithi_pravesha'])
@pytest.mark.parametrize('years', [(42,), (42, 44)])
@pytest.mark.parametrize('view', ['NOW', 'AHEAD'])
def test_omitted_year_is_unavailable_despite_complete_sky(family, years, view):
    subset = annual(family, years)
    omitted = annual(family, (43,))
    assert subset.entries and omitted.entries
    row = omitted.entries[0]
    at = (row['t_in'] + row['t_out']) / 2
    # Prove the omitted object exists, using an independent normal build.
    assert read_testimony(omitted, at=at, view=view)['entries']
    answer = read_testimony(subset, at=at, view=view)
    assert answer['entries'] == []
    assert answer['coverage']['sky_complete'] is True
    assert answer['coverage']['complete'] is False
    assert answer['coverage']['search_state'] == 'partial'
    assert answer['null_reason'] == 'information_unavailable'
    assert any(lo <= at < hi for lo, hi in answer['coverage']['method_gaps'])


@pytest.mark.parametrize('family', ['sudarshana_varsha', 'tithi_pravesha'])
@pytest.mark.parametrize('view', ['NOW', 'AHEAD'])
def test_computed_support_remains_available_with_other_years_omitted(family, view):
    payload = annual(family, (44, 42))
    assert payload.coverage['searched_years'] == (42, 44)
    for row in payload.entries:
        answer = read_testimony(payload, at=(row['t_in'] + row['t_out']) / 2, view=view)
        assert answer['entries'] == [row]
        assert answer['null_reason'] is None
    assert payload.coverage['complete'] is False
    assert payload.null_reason == 'information_unavailable'


@pytest.mark.parametrize('view', ['NOW', 'AHEAD'])
def test_tithi_coverage_does_not_extend_one_second_return_support(view):
    payload = annual('tithi_pravesha', (42,))
    row = payload.entries[0]
    assert row['t_out'] - row['t_in'] == pytest.approx(1/86400, abs=1e-9)
    assert payload.coverage['method_intervals'] == ((row['t_in'], row['t_out']),)
    for at in (row['t_in'] - 1/86400, row['t_out']):
        answer = read_testimony(payload, at=at, view=view)
        assert answer['entries'] == []
        assert answer['null_reason'] == 'information_unavailable'


@pytest.mark.parametrize('years', [(42,), (42, 43)])
def test_sudarshana_complete_requires_actual_method_interval_coverage(years):
    # Independent civil birthday anchors: 2025-02-05, 2026-02-05, 2027-02-05 UT.
    lo, hi = 2460711.5, (2461076.5 if years == (42,) else 2461441.5)
    payload = annual('sudarshana_varsha', years, cov(lo, hi, source=(lo, hi)))
    assert payload.coverage['complete'] is True
    assert payload.coverage['search_state'] == 'searched'
    assert payload.coverage['method_intervals'] == ((lo, hi),)
    assert payload.coverage['method_gaps'] == []
    assert payload.null_reason is None
    assert read_testimony(payload, at=hi)['null_reason'] == 'information_unavailable'


@pytest.mark.parametrize('family', ['sudarshana_varsha', 'tithi_pravesha'])
@pytest.mark.parametrize('failure', ['missing_fact', 'outside_sky'])
def test_uncomputed_years_have_no_method_coverage(family, failure):
    kwargs = {'ctx': context(facts=())} if failure == 'missing_fact' else {'years': (80,)}
    payload = annual(family, **({'years': (42,)} | kwargs))
    assert not payload.entries
    assert payload.coverage['searched_years'] == ()
    assert payload.coverage['method_intervals'] == ()
    assert payload.coverage['method_gaps'] == [(LO, LO+2000)]
    assert payload.coverage['complete'] is False
    assert payload.coverage['search_state'] == 'unsearched'
    assert read_testimony(payload, at=LO+10)['null_reason'] == 'information_unavailable'
