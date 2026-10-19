"""J4P-B5: refuse before a projection can erase malformed ISO evidence.

The temporal cases and full F1 storage cases port the independent review probes.
All periods are controlled fixtures, never native astronomical computations.
"""
from datetime import datetime, timezone

import pytest

from services.gochara_kernel import dasha_read as reader
from services.ka_temporal.date_resolver import load_dasha_timeline
from tests.l3.kala_db.test_j4p_malformed_settled_periods import (  # noqa: F401
    db, CHART, BUILD, AYA, START, END, add_period,
)


def temporal(db):
    db.execute("UPDATE chart_dashas SET start_date=start_iso::date, end_date=end_iso::date")
    return load_dasha_timeline(db, CHART, ayanamsha_id=AYA)


@pytest.mark.parametrize('end', [START, datetime(2025, 12, 31, tzinfo=timezone.utc), None])
@pytest.mark.parametrize('system', ['vimshottari', 'yogini'])
def test_temporal_refuses_malformed_iso_before_date_projection(db, end, system):
    add_period(db, end)
    db.execute("UPDATE chart_dashas SET system_id=%s WHERE lord_graha='Mars'", (system,))
    with pytest.raises(reader.DashaBuildRefused, match='dasha_period_malformed'):
        temporal(db)


def test_temporal_valid_control_and_positive_within_day_period(db):
    db.execute("UPDATE chart_dashas SET start_iso='2026-01-01T01:00Z', end_iso='2026-01-01T02:00Z'")
    periods = temporal(db)
    assert [(p.lord, p.start.isoformat(), p.end.isoformat()) for p in periods] == [
        ('Saturn', '2026-01-01', '2026-01-01')]


PROJECTIONS = [
    ('kshetra_row_count', (CHART, 'yogini')),
    ('kshetra_covers_instant', (CHART, 'yogini', 1, START, START)),
    ('resonance_md_lords', (CHART, AYA, ['saturn'])),
    ('tree_children', ('00000000-0000-4000-8000-000000000001', END, START)),
    ('temporal_timeline', (CHART, 'yogini', AYA, 4)),
]


@pytest.mark.parametrize('name,params', PROJECTIONS)
@pytest.mark.parametrize('end', [START, datetime(2025, 12, 31, tzinfo=timezone.utc), None])
def test_non_vim_malformed_period_refuses_before_selection_or_aggregation(db, name, params, end):
    # The valid Vimśottarī anchor must not hide bad operands in another system.
    add_period(db, end)
    # P06: the shared settled-period fixture already declares kp_sublevel.
    db.execute("ALTER TABLE chart_dashas ADD COLUMN kp_sub_lord text")
    with pytest.raises(reader.DashaBuildRefused, match='dasha_period_malformed'):
        reader.execute_governed_dasha_query(db, CHART, reader.dasha_query(name), params)


@pytest.mark.parametrize('canonicalize', [True, False])
def test_multilevel_non_vim_malformed_period_refuses_before_return(db, canonicalize):
    add_period(db, START)
    with pytest.raises(reader.DashaBuildRefused, match='dasha_period_malformed'):
        reader.load_governed_dasha_periods(db, CHART, systems=['yogini'], canonicalize=canonicalize)


@pytest.mark.parametrize('tier', ['unknown', 'single', 'pending_w3_verification'])
def test_unadmitted_malformed_tier_does_not_poison_valid_timeline(db, tier):
    add_period(db, START)
    db.execute("UPDATE chart_dashas SET verification_pass_status=%s WHERE lord_graha='Mars'", (tier,))
    assert [p.lord for p in temporal(db)] == ['Saturn']


def test_admitted_per_level_tier_must_refuse(db):
    # Mudda's honest-computed policy admits a single-pass level 1 operand.
    add_period(db, START)
    db.execute("UPDATE chart_dashas SET system_id='mudda', verification_pass_status='single' WHERE lord_graha='Mars'")
    with pytest.raises(reader.DashaBuildRefused, match='dasha_period_malformed'):
        temporal(db)


def test_explicit_f2_tier_must_refuse_at_reader(db):
    add_period(db, START)
    db.execute("UPDATE chart_dashas SET verification_pass_status='single' WHERE lord_graha='Mars'")
    with pytest.raises(reader.DashaBuildRefused, match='dasha_period_malformed'):
        reader.execute_governed_dasha_query(db, CHART, reader.dasha_query('clock_rows'),
            (CHART, 'yogini', AYA), clock_tier='single')
