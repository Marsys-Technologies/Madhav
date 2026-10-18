"""Reviewer B3 populations through the real MD reader and permission path."""
import pytest
import swisseph as swe
from services.gochara_grammar import dasha_data as DD
from services.gochara_intensity import permission as perm
from services.gochara_kernel import dasha_read as DR

CHART = '482012f1-710e-4a25-994a-93821f5871aa'
BUILD = '7377833e-5d3b-4e70-8bef-1318904f470e'
UNKNOWN = '33333333-3333-4333-8333-333333333333'


class Population:
    """Emulate SQL predicates, retain provenance exactly as the query projects it."""
    def __init__(self, builds, tier='two_pass_verified'):
        self.builds, self.tier, self.calls = builds, tier, []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        if 'SELECT DISTINCT coalesce' in sql:
            self.rows = [(b or 'NULL',) for b in self.builds]
        elif 'chart_dashas' in sql:
            self.rows = [dict(dasha_row_id=str(i), system_id='vimshottari', level_n=1,
                              parent_row_id=None, lord_graha='Saturn',
                              start_iso='2026-01-01T00:00:00+00:00', end_iso='2026-02-01T00:00:00+00:00',
                              build_id=b, verification_pass_status=self.tier)
                         for i, b in enumerate(self.builds)
                         if 'verification_pass_status =' not in sql or self.tier == 'two_pass_verified']
        else:
            self.rows = []
        return self

    def fetchall(self):
        return self.rows


@pytest.mark.parametrize('builds,code', [
    ([UNKNOWN], 'settled_build_absent'), ([None], 'dasha_build_null'),
    ([BUILD, UNKNOWN], 'settled_build_ambiguous'),
    ([BUILD, None], 'settled_build_ambiguous'), ([], 'settled_build_absent'),
])
def test_legacy_permission_refuses_ungoverned_population(builds, code):
    with pytest.raises(DR.DashaBuildRefused, match=code):
        perm.compute_permission(swe, Population(builds), CHART, 'marriage', [], swe.julday(2026, 1, 9, 0))


@pytest.mark.parametrize('tier', [None, 'unknown', 'single', 'pending_w3_verification'])
def test_legacy_permission_refuses_no_eligible_vimshottari(tier):
    with pytest.raises(DR.DashaBuildRefused, match='settled_build_absent'):
        perm.compute_permission(swe, Population([BUILD], tier), CHART, 'marriage', [], swe.julday(2026, 1, 9, 0))


def test_legacy_md_reader_retains_governed_provenance():
    rows = DD.fetch_dasha_periods(Population([BUILD]), CHART, systems=['vimshottari'])
    assert rows[0]['build_id'] == BUILD
    assert rows[0]['verification_pass_status'] == 'two_pass_verified'
    assert rows[0]['merged_row_ids'] == ['0']


@pytest.mark.parametrize('build', [None, UNKNOWN])
def test_live_supplied_periods_cannot_bypass_receipt(build):
    row = dict(dasha_row_id='supplied', system_id='vimshottari', level_n=1,
               lord_graha='Saturn', start_iso='2026-01-01T00:00:00+00:00',
               end_iso='2026-02-01T00:00:00+00:00', build_id=build,
               verification_pass_status='two_pass_verified')
    with pytest.raises(DR.DashaBuildRefused):
        perm.compute_permission(swe, Population([BUILD]), CHART, 'marriage', [],
                                swe.julday(2026, 1, 9, 0), dasha_periods=[row])


def test_other_ayanamsha_refuses_without_querying():
    conn = Population([BUILD])
    with pytest.raises(DR.DashaBuildRefused, match='ayanamsha_not_settled'):
        DD.fetch_dasha_periods(conn, CHART, ayanamsha_id='raman')
    assert not conn.calls


@pytest.mark.parametrize('builds', [[UNKNOWN], [None], [BUILD, UNKNOWN]])
def test_series_md_prefetch_refuses_review_populations(builds):
    from services.gochara_intensity.engine import compute_lambda_e_series
    with pytest.raises(DR.DashaBuildRefused):
        compute_lambda_e_series(swe, Population(builds), CHART, 'marriage',
                                swe.julday(2026, 1, 9, 0), swe.julday(2026, 1, 10, 0),
                                1, targets=[])


def test_governed_md_can_still_emit_an_active_vote():
    value, detail = perm.compute_permission(
        swe, Population([BUILD]), CHART, 'marriage', [], swe.julday(2026, 1, 9, 0))
    assert value > 0
    assert 'vimshottari' in detail['systems_active']


@pytest.mark.parametrize('builds,code', [
    ([UNKNOWN], 'settled_build_absent'), ([None], 'dasha_build_null'),
    ([BUILD, UNKNOWN], 'settled_build_ambiguous'),
])
def test_permission_http_surface_returns_typed_unavailable(monkeypatch, builds, code):
    from datetime import datetime, timezone
    from fastapi import HTTPException
    from routers import permission_curve as router
    conn = Population(builds)
    conn.close = lambda: None
    monkeypatch.setattr(router, '_get_conn', lambda: conn)
    request = router.PermissionCurveRequest(
        chart_id=CHART, event_class='marriage',
        t_start=datetime(2026, 1, 9, tzinfo=timezone.utc),
        t_end=datetime(2026, 1, 10, tzinfo=timezone.utc))
    with pytest.raises(HTTPException) as refusal:
        router.post_permission_curve(request)
    assert refusal.value.status_code == 503
    assert refusal.value.detail['code'] == code


def test_database_failure_is_typed_unavailable():
    class Broken:
        def execute(self, *args):
            raise RuntimeError('fixture SQL read unavailable')
    with pytest.raises(DR.DashaBuildRefused, match='dasha_read_unavailable'):
        DD.fetch_dasha_periods(Broken(), CHART)


class ScopedPopulation(Population):
    """SQL-boundary emulator with independent system/tier/level predicates."""
    def __init__(self, rows):
        self.source, self.calls = rows, []

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        if 'SELECT DISTINCT coalesce' in sql:
            systems = [params[1]] if 'system_id = %s' in sql else params[2]
            selected = [r for r in self.source if r['system_id'] in systems]
            self.rows = [(b,) for b in sorted({r['build_id'] or 'NULL' for r in selected})]
        elif 'chart_dashas' in sql:
            self.rows = [r for r in self.source
                         if r['system_id'] in params[2] and r['level_n'] in params[3]
                         and r['verification_pass_status'] in (params[4] if isinstance(params[4], list) else [params[4]])
                         and (len(params) < 6 or r['build_id'] == params[5])]
        else:
            self.rows = []
        return self


def population_row(system, build, level=1, tier='two_pass_verified'):
    return dict(dasha_row_id=system + str(level), system_id=system, level_n=level,
                parent_row_id=None, lord_graha='Saturn',
                start_iso='2026-01-01T00:00:00+00:00', end_iso='2026-02-01T00:00:00+00:00',
                build_id=build, verification_pass_status=tier)


@pytest.mark.parametrize('reader', ['public_md', 'public_multilevel', 'projection'])
@pytest.mark.parametrize('foreign,code', [
    ([population_row('yogini', UNKNOWN)], 'settled_build_absent'),
    ([population_row('yogini', None)], 'dasha_build_null'),
    ([population_row('yogini', BUILD), population_row('yogini', UNKNOWN, 4, 'unknown')],
     'settled_build_ambiguous'),
])
def test_non_vim_population_checked_before_filtering(reader, foreign, code):
    conn = ScopedPopulation([population_row('vimshottari', BUILD)] + foreign)
    expected = 'settled_build_ambiguous' if reader == 'projection' else code
    with pytest.raises(DR.DashaBuildRefused, match=expected):
        if reader == 'projection':
            DR.execute_governed_dasha_query(conn, CHART, DR.dasha_query('tree_level1'),
                                           (CHART, 'lahiri_chitrapaksha', 'yogini', '2026-02-01', '2026-01-01'))
        elif reader == 'public_multilevel':
            DD.fetch_dasha_periods_multilevel(conn, CHART, systems=['yogini'])
        else:
            DD.fetch_dasha_periods(conn, CHART, systems=['yogini'])


def test_public_non_vim_rows_keep_the_named_build_and_tier():
    conn = ScopedPopulation([population_row('vimshottari', BUILD), population_row('yogini', BUILD)])
    rows = DD.fetch_dasha_periods(conn, CHART, systems=['yogini'])
    assert [r['system_id'] for r in rows] == ['yogini']
    assert rows[0]['build_id'] == BUILD
    assert rows[0]['verification_pass_status'] == 'two_pass_verified'


def test_empty_system_filter_uses_the_guarded_default_population():
    """The legacy [] means all systems; it must not skip their population guard."""
    conn = ScopedPopulation([
        population_row('vimshottari', BUILD), population_row('yogini', BUILD),
        population_row('yogini', UNKNOWN, 4, 'unknown'),
    ])
    with pytest.raises(DR.DashaBuildRefused, match='settled_build_ambiguous'):
        DD.fetch_dasha_periods(conn, CHART, systems=[])


def test_f2_declared_honest_tier_is_preserved_without_promotion():
    """F2's explicit single tier remains readable within the governed build."""
    from datetime import datetime, timezone
    from services.kala_core import clocks

    class ClockPopulation(ScopedPopulation):
        def execute(self, sql, params=()):
            if sql.lstrip().startswith('WITH governed_chart_dashas'):
                self.calls.append((sql, params))
                self.rows = [r for r in self.source if r['system_id'] == params[-2]
                             and r['build_id'] == params[2]
                             and r['verification_pass_status'] == params[4]]
                return self
            return super().execute(sql, params)

    row = population_row('yogini', BUILD, tier='single')
    row['applies_to_this_chart_flag'] = True
    conn = ClockPopulation([population_row('vimshottari', BUILD), row])
    context = clocks.period_context(conn, CHART, datetime(2026, 1, 9, tzinfo=timezone.utc),
                                    'yogini', build_id=BUILD,
                                    ayanamsha_id='lahiri_chitrapaksha', tier='single')
    assert context.lords == {'MD': 'Saturn'}
    assert context.tier == 'single'
    assert context.build_id == BUILD


@pytest.mark.parametrize('tier', ['unknown', 'divergent_flagged'])
def test_f2_unknown_or_divergent_tier_refuses_before_read(tier):
    conn = ScopedPopulation([population_row('vimshottari', BUILD)])
    with pytest.raises(DR.DashaBuildRefused, match='dasha_tier_refused'):
        DR.execute_governed_dasha_query(conn, CHART, DR.dasha_query('clock_rows'),
                                       (CHART, 'yogini', 'lahiri_chitrapaksha'), clock_tier=tier)
    assert not conn.calls


def test_legacy_projection_cannot_widen_the_vote_tier():
    conn = ScopedPopulation([population_row('vimshottari', BUILD)])
    with pytest.raises(DR.DashaBuildRefused, match='read_contract_mismatch'):
        DR.execute_governed_dasha_query(conn, CHART, DR.dasha_query('permission_spine'),
                                       (), clock_tier='single')
    assert not conn.calls


@pytest.mark.parametrize('start,end', [
    ('2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'),
    ('2026-02-01T00:00:00Z', '2026-01-01T00:00:00Z'),
    (None, '2026-02-01T00:00:00Z'),
    ('2026-01-01T00:00:00Z', None),
    ('malformed', '2026-02-01T00:00:00Z'),
    ('2026-01-01', '2026-02-01'),
])
@pytest.mark.parametrize('path', ['preloaded', 'multilevel', 'period_rows_for'])
def test_every_live_operand_entrypoint_refuses_malformed_bounds(start, end, path):
    row = population_row('vimshottari', BUILD)
    row.update(start_iso=start, end_iso=end)
    conn = ScopedPopulation([row])
    with pytest.raises(DR.DashaBuildRefused, match='dasha_period_malformed'):
        if path == 'preloaded':
            perm.compute_permission(swe, conn, CHART, 'marriage', [],
                swe.julday(2026, 1, 9, 0), dasha_periods=[row])
        elif path == 'multilevel':
            DD.fetch_dasha_periods_multilevel(conn, CHART)
        else:
            rows_for, _ = DR.make_period_rows_for(conn, CHART)
            rows_for('Saturn')
