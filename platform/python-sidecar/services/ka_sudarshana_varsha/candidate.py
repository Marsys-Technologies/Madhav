"""Adapter-side frame geometry only; conclusions and nested periods are judge work."""
from datetime import datetime, timezone

from services.kala_core.overlays.contested import AdapterContext, envelope
from services.kala_core.vocab import NullReason, SignId
from .logic import progressed_sign_index, varsha_window


def build_candidate(*, ctx: AdapterContext, birth_date, years, coverage, year_anchor):
    if year_anchor != 'civil_birthday':
        raise ValueError('only the explicit civil_birthday anchor convention is implemented')
    years = tuple(years)
    if not years or any(type(y) is not int or y < 1 for y in years) or len(set(years)) != len(years):
        raise ValueError('distinct positive year numbers required')
    required = tuple((s,'sign') for s in ('LAGNA','MOON','SUN'))
    facts = {s:ctx.fact(s,k) for s,k in required}
    entries = []
    gap = False
    if all(facts.values()) and coverage.covered:
        signs = [s.value for s in SignId]
        try: natal = {s:signs.index(f['fact_value_text']) for s,f in facts.items()}
        except ValueError as exc: raise ValueError('unknown L1 natal sign') from exc
        for year in sorted(years):
            start,end = varsha_window(birth_date,year)
            a,b = [datetime.combine(d,datetime.min.time(),timezone.utc).timestamp()/86400+2440587.5 for d in (start,end)]
            lo,hi = coverage.covered
            if a < lo or b > hi:
                gap = True
                continue
            entries.append({'year':year,'t_in':a,'t_out':b,
                'frames':{s.lower():progressed_sign_index(idx,year) for s,idx in natal.items()},
                'frame_fact_ids':{s.lower():f['fact_id'] for s,f in facts.items()},
                'judgment':None,'coincident_frame_policy':'birth_chart_only' if len(set(natal.values())) < 3 else 'three_distinct_frames',
                'year_anchor':year_anchor,'anchor_source_status':'declared_convention',
                'calendar_boundary':'civil_date_at_00:00_UT', 'nested_periods':None})
    return envelope('sudarshana_varsha',ctx,coverage,entries,required=required,
                    sources={'birth_date':birth_date.isoformat(),'years':years,'year_anchor':year_anchor,
                             'searched_years':tuple(r['year'] for r in entries)},
                    null_reason=NullReason.INFORMATION_UNAVAILABLE if gap else None)
