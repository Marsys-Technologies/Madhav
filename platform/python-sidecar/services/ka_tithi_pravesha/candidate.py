"""moon_longitude_return, uncited legacy; phase-return remains uncomputed."""
from datetime import timezone

from services.gochara_kernel.substrate import jd_to_utc
from services.kala_core.overlays.contested import AdapterContext, envelope
from services.kala_core.sky import ephemeris_at
from services.kala_core.vocab import NullReason
from .logic import lunar_return, pravesha_anniversary


def build_candidate(*, ctx: AdapterContext, birth_dt, years, coverage, ephe_path=None):
    if birth_dt.tzinfo is None:
        raise ValueError('birth instant must declare timezone')
    years = tuple(years)
    if not years or any(type(y) is not int or y < 1 for y in years) or len(set(years)) != len(years):
        raise ValueError('distinct positive year numbers required')
    fact = ctx.fact('MOON','longitude_sidereal')
    entries = []
    gap = False
    def longitude(dt):
        jd = dt.timestamp()/86400+2440587.5
        covered = coverage.covered
        if covered is None or not covered[0] <= jd < covered[1]: return None
        answer = ephemeris_at(jd,ctx.convention,bodies=('Moon',),ephe_path=ephe_path)
        return answer.values[0].position('Moon').longitude_deg if answer.available else None
    if fact and coverage.covered:
        for year in sorted(years):
            anniversary = pravesha_anniversary(birth_dt,year)
            instant,audit = lunar_return(anniversary,float(fact['fact_value_num']),longitude)
            if not audit['converged']:
                gap = True
                continue
            jd = instant.timestamp()/86400+2440587.5
            # The return is an instant object; its one-second support is declared,
            # never a claim that this instant's chart holds for a whole year.
            entries.append({'year':year,'return_jd':jd,'return_utc':jd_to_utc(jd).isoformat(),
                't_in':jd,'t_out':min(jd+1/86400,coverage.covered[1]),'janma_fact_id':fact['fact_id'],
                'audit':audit,'method_id':'moon_longitude_return','source_status':'uncited_legacy',
                'phase_return':None,'phase_return_null_reason':'cited_school_definition_missing',
                'annual_object_identity_admitted':False,'year_anchor':'civil_birthday',
                'birth_instant_utc':birth_dt.astimezone(timezone.utc).isoformat()})
    return envelope('tithi_pravesha',ctx,coverage,entries,
                    sources={'birth_datetime':birth_dt.isoformat(),'years':years,
                             'searched_years':tuple(r['year'] for r in entries)},
                    null_reason=NullReason.INFORMATION_UNAVAILABLE if gap else None)
