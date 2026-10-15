"""K12 clock counterexamples, using a query-aware in-memory read surface."""
from datetime import datetime, timedelta, timezone
import pytest
from services.kala_core.clocks import ClockUnavailable, boundaries, period_context

T0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
PIN = dict(build_id='A', ayanamsha_id='lahiri_chitrapaksha', tier='two_pass_verified')


def row(id='md', level=1, parent=None, start=0, end=100, **extra):
    return dict(dasha_row_id=id, level_n=level, parent_row_id=parent, lord_graha='Sun',
                start_iso=T0+timedelta(days=start), end_iso=T0+timedelta(days=end),
                build_id='A', ayanamsha_id=PIN['ayanamsha_id'], system_id='vimshottari',
                verification_pass_status=PIN['tier'], applies_to_this_chart_flag=True, **extra)


class Conn:
    def __init__(self, rows): self.rows = rows
    def execute(self, sql, params):
        self.selected = self.rows
        if 'build_id = %s' in sql: self.selected = [r for r in self.selected if r['build_id'] == params[2]]
        if 'verification_pass_status = %s' in sql: self.selected = [r for r in self.selected if r['verification_pass_status'] == params[-1]]
        return self
    def fetchall(self): return self.selected


def context(rows, day=1, **pin):
    return period_context(Conn(rows), 'chart', T0+timedelta(days=day), 'vimshottari', **(PIN | pin))


def test_mixed_build_hidden_by_filter():
    other = row('other'); other['build_id'] = 'B'; other['verification_pass_status'] = 'single'
    with pytest.raises(ClockUnavailable, match='build_not_pinned'): context([row(), other])


def test_divergent_tier_admitted():
    r = row(); r['verification_pass_status'] = 'divergent_flagged'
    with pytest.raises(ClockUnavailable, match='tier'): context([r], tier='divergent_flagged')


def test_boundaries_requires_as_of():
    with pytest.raises(TypeError): boundaries(Conn([row()]), 'chart', 'vimshottari', **PIN)


def test_terminal_end_preserved():
    result = boundaries(Conn([row(), row('md2', start=100, end=200,
        is_truncated_at_window_end=True)]), 'chart', 'vimshottari', as_of=T0, **PIN)
    terminal = [b for b in result if b.instant == T0+timedelta(days=200)]
    assert len(terminal) == 1 and terminal[0].boundary_truncated


@pytest.mark.parametrize('kind', ['inapplicable', 'orphan', 'wrong_tier_parent'])
def test_ineligible_boundary_refused(kind):
    r = row()
    rows = [r]
    if kind == 'inapplicable': r['applies_to_this_chart_flag'] = False
    else:
        child = row('ad', 2, 'absent' if kind == 'orphan' else 'md', end=50)
        rows.append(child)
        if kind == 'wrong_tier_parent': r['verification_pass_status'] = 'single'
    with pytest.raises(ClockUnavailable):
        boundaries(Conn(rows), 'chart', 'vimshottari', as_of=T0, **PIN)


def test_child_interval_outside_parent():
    with pytest.raises(ClockUnavailable, match='hierarchy_unavailable'):
        context([row(), row('ad', 2, 'md', start=-30, end=130)])


def test_short_child_does_not_erase_parent_sandhi():
    assert context([row(), row('ad', 2, 'md', end=3)]).sandhi


def test_sandhi_window_names_the_period_that_earned_the_band():
    result = context([row(), row('ad', 2, 'md', start=1, end=4)], day=2)
    assert result.sandhi and result.sandhi_window == timedelta(days=3)


def test_half_open_boundary_selects_only_the_successor():
    result=context([row('old',end=1),row('new',start=1,end=100)],day=1)
    assert result.period_ids=={'MD':'new'}


def test_coverage_gap_is_typed():
    with pytest.raises(ClockUnavailable, match='coverage_gap'):
        context([row(end=1),row('new',start=3,end=100)],day=2)


def test_ambiguous_period_is_typed():
    with pytest.raises(ClockUnavailable, match='ambiguous_period'):
        context([row(),row('overlap')])
