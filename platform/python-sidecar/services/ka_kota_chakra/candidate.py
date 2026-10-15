"""Uncited ring occupancy testimony. No attack/defence reading or motion claim."""
from services.gochara_rules.nature import NATURAL_MALEFICS, agent_nature
from services.kala_core.overlays.contested import AdapterContext, envelope, index_ledger
from services.kala_core.sky import boundary_events, coverage_of, ephemeris_at
from services.kala_core.vocab import NullReason
from .logic import ALL_RING_NAMES, count_from_janma, ring_for_count


def build_candidate(*, ctx: AdapterContext, indexes, horizon, ring_rows, ephe_path=None):
    ring_rows = list(ring_rows)
    ring_sets = {name: frozenset(int(r['ring_position']) for r in ring_rows if r['ring_name'] == name) for name in ALL_RING_NAMES}
    positions = [int(r['ring_position']) for r in ring_rows]
    valid = len(positions) == 27 and set(positions) == set(range(1,28)) and all(r['ring_name'] in ALL_RING_NAMES for r in ring_rows)
    results = {g: boundary_events(index,g,['nakshatra_ingress'],horizon,ctx.convention.convention_id,ephe_path=ephe_path)
               for g,index in sorted(indexes.items())}
    bounds = [r.coverage.covered for r in results.values()]
    source = (max(b[0] for b in bounds),min(b[1] for b in bounds)) if bounds and all(bounds) else None
    if source and source[0] >= source[1]: source = None
    coverage = coverage_of(horizon,source,backend='swieph',convention_id=ctx.convention.convention_id)
    fact = ctx.fact('MOON','longitude_sidereal')
    entries = []
    gap = not valid
    if valid and fact and coverage.covered:
        lo,hi = coverage.covered
        janma = int(float(fact['fact_value_num'])/(360/27))
        for graha,result in results.items():
            events = [e for e in result.values if lo <= e.jd < hi]
            edges = sorted({lo,hi,*(e.jd for e in events)})
            for a,b in zip(edges,edges[1:]):
                sky = ephemeris_at(a,ctx.convention,bodies=tuple(sorted(indexes)),ephe_path=ephe_path)
                if not sky.available:
                    gap = True
                    continue
                sky = sky.values[0]
                known = {p.body:p.longitude_deg for p in sky.positions}
                sun,moon = known.get('Sun'),known.get('Moon')
                joined = None
                if 'Mercury' in known:
                    cell = int(known['Mercury']//30)
                    malefics = [g for g in NATURAL_MALEFICS if g in known]
                    if sun is not None and moon is not None and agent_nature('Moon',sun_lon=sun,moon_lon=moon)=='malefic':
                        malefics.append('Moon')
                    if any(int(known[g]//30)==cell for g in malefics): joined = True
                    elif NATURAL_MALEFICS <= known.keys() and sun is not None and moon is not None: joined = False
                nak = next((e.cell_after for e in events if e.jd==a), int(known[graha]/(360/27)))
                count = count_from_janma(nak,janma)
                entries.append({'graha':graha,'t_in':a,'t_out':b,'nakshatra_idx':nak,'count_from_janma':count,
                    'ring':ring_for_count(count,ring_sets),'janma_fact_id':fact['fact_id'],
                    'nature':agent_nature(graha,sun_lon=sun,moon_lon=moon,joined_to_malefic=joined),
                    'nature_evaluated_jd':a,'nature_scope':'entry_instant_only',
                    'direction_of_motion':None,'source_status':'uncited_extension'})
    return envelope('kota_chakra',ctx,coverage,entries,
                    sources={'ring_rows':sorted(ring_rows,key=lambda r:(r['ring_position'],r['ring_name'])), 'sky_indexes':index_ledger(indexes)},
                    null_reason=NullReason.INFORMATION_UNAVAILABLE if gap else None)
