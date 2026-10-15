"""KA-3a typed candidate provider. No serving/publication or live sky binding.

(I) INTERPRETATION: explicit sky-derived residence inputs are the adapter seam;
production binding belongs to the follow-on gate, never a rolling-day fallback.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import re
from math import isfinite

from brahmagyan.verification_tiers import EXTERNAL_COMPUTATION_REQUIRED

from services.gochara_rules.vedha_derive import pairs_from_rows
from services.kala_core.overlays import house_intervals, instant, validated_residence
from services.kala_core.sky.coverage import SkyCoverage

FORMULA_VERSION='ka_vedha_candidate/v1'
KINDS=('house_vedha','sarvatobhadra','latta')


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),default=str,allow_nan=False)


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class VedhaPayload:
    headers: tuple[dict,...]
    intervals: tuple[dict,...]
    janma_fact: dict | None = None
    sources: dict | None = None


def coverage_payload(coverage):
    if not isinstance(coverage,SkyCoverage):
        raise TypeError('typed SkyCoverage is required')
    value=json.loads(canonical(asdict(coverage)))
    value['gaps']=[list(g) for g in coverage.gaps]
    value['search_state']='searched' if coverage.complete else 'unsearched' if coverage.covered is None else 'partial'
    return value


def residence_coverage(coverage, residence, bodies):
    """The sky envelope plus exact per-body holes; empty never means clean."""
    from services.gochara_kernel.substrate import jd_to_utc
    value=coverage_payload(coverage)
    value['sky_complete']=value['complete']
    holes={}
    gaps=list(coverage.gaps)
    if coverage.covered is not None:
        lo,hi=map(jd_to_utc,coverage.covered)
        for body in bodies:
            cursor=lo
            missing=[]
            for _,a,b in residence.get(body,()):
                a=max(instant(a),lo); b=min(instant(b),hi)
                if a>=b:
                    continue
                if cursor<a:
                    missing.append((cursor,a))
                cursor=max(cursor,b)
            if cursor<hi:
                missing.append((cursor,hi))
            holes[body]=[[a.isoformat(),b.isoformat()] for a,b in missing]
            gaps.extend((a.timestamp()/86400+2440587.5,b.timestamp()/86400+2440587.5) for a,b in missing)
    merged=[]
    for a,b in sorted(gaps):
        if merged and a<=merged[-1][1]:
            merged[-1][1]=max(b,merged[-1][1])
        else:
            merged.append([a,b])
    value['residence_gaps']=holes
    value['gaps']=merged
    value['complete']=coverage.complete and not merged
    value['search_state']='unsearched' if coverage.covered is None else 'searched' if value['complete'] else 'partial'
    return value


def build_candidate_payload(*,chart_id,generation,ayanamsha_id,natal_build_id,
                            janma_fact,coverage,residence,pairs_rows,
                            nakshatra_residence,latta_rules,enrichment=None):
    if not re.fullmatch(r'[A-Za-z0-9_.:-]+', generation or '') or generation in ('legacy','current','published','retained'):
        raise ValueError('an explicit new candidate generation is required')
    if not all((chart_id,ayanamsha_id,natal_build_id)):
        raise ValueError('candidate natal pins required')
    cov=coverage_payload(coverage)
    pairs=pairs_from_rows(pairs_rows)
    residence={g:validated_residence(rows) for g,rows in sorted(residence.items())}
    nakshatra_residence={g:validated_residence(rows,27) for g,rows in sorted(nakshatra_residence.items())}
    if enrichment is not None:
        if not all(enrichment.get(k) for k in ('passage','locator','verses')) or enrichment['verses']!='XXVI.47-48':
            raise ValueError('enrichment requires verbatim passage and XXVI.47-48 locator')
        enrichment={**enrichment,'applied_to_computation':False}
    else:
        enrichment={'null_reason':'information_unavailable','applied_to_computation':False}
    lon=None if janma_fact is None else janma_fact.get('fact_value_num')
    if lon is not None and (not isfinite(float(lon)) or not 0<=float(lon)<360):
        raise ValueError('contradictory natal Moon longitude')
    if janma_fact is not None and not janma_fact.get('fact_id'):
        raise ValueError('natal fact reference required')
    sources={'pairs_rows':pairs_rows,'latta_rules':latta_rules,'enrichment':enrichment}
    fp={'schema':'ka_vedha_inputs/1','digest':fingerprint({
        'chart_id':chart_id,'natal_build_id':natal_build_id,'ayanamsha_id':ayanamsha_id,
        'janma_fact':janma_fact,'coverage':cov,'residence':residence,'nakshatra_residence':nakshatra_residence,
        'l0_pairs':sorted(pairs_rows,key=canonical),'latta_rules':sorted(latta_rules,key=canonical),'enrichment':enrichment,'version':FORMULA_VERSION})}
    common={'chart_id':chart_id,'generation':generation,'ayanamsha_id':ayanamsha_id,
            'natal_build_id':natal_build_id,'janma_reference_fact_id':None if janma_fact is None else janma_fact['fact_id'],
            'formula_version':FORMULA_VERSION,'upstream_fingerprint':fp,'coverage':cov}
    # Missing natal reference is typed absence. Its header references the exact
    # external-computation requirement; storage uses an explicit absence token.
    if common['janma_reference_fact_id'] is None:
        common['janma_reference_fact_id']='[EXTERNAL_COMPUTATION_REQUIRED]'
    headers=[]; intervals=[]
    for kind in KINDS:
        family_cov=(residence_coverage(coverage,residence,('Sun','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'))
                    if kind=='house_vedha' else residence_coverage(coverage,nakshatra_residence,[r['graha'] for r in latta_rules])
                    if kind=='latta' else cov)
        null_reason='information_unavailable' if kind=='sarvatobhadra' or lon is None or not family_cov['complete'] else None
        payload={'schema':'ka_vedha_payload/1','viparita':{'applied':False,'reason':'not applied — no served source'}}
        if lon is None:
            payload[EXTERNAL_COMPUTATION_REQUIRED]={'asset':'ga_positions','fact_category':'graha_position','fact_subject':'MOON',
                'fact_key':'longitude_sidereal','chart_id':chart_id,'build_id':natal_build_id,'ayanamsha_id':ayanamsha_id}
        if kind=='sarvatobhadra':
            payload['reason']='grid unpopulated; no algorithmic approximation'
        if kind=='latta':
            payload.update(ketu_gap='information_unavailable',enrichment=enrichment)
            if not latta_rules:
                null_reason='information_unavailable'
        headers.append({**common,'coverage':family_cov,'vedha_kind':kind,'method_qualification':None if null_reason else 'qualified',
                        'null_reason':null_reason,'payload':payload})
    from services.gochara_kernel.substrate import jd_to_utc
    if lon is None or coverage.covered is None:
        return VedhaPayload(tuple(headers),(),janma_fact,sources)
    low,high=map(jd_to_utc,coverage.covered)
    moon_sign=int(float(lon)//30)+1
    moon_nak=int(float(lon)/(360/27))+1
    cites={(str(r[0]).capitalize(),r[1]):r[3] for r in pairs_rows} if pairs_rows and not isinstance(pairs_rows[0],dict) else {
        (r['graha'].capitalize(),r['primary_house']):r['classical_citation'] for r in pairs_rows}
    def interval(kind,graha,a,b,state,cite,detail,reason=None,reasons=(),scope=None,obstructors=(),unknown=()):
        return {'chart_id':chart_id,'generation':generation,'ayanamsha_id':ayanamsha_id,'vedha_kind':kind,
                'graha':graha,'t_in':instant(a),'t_out':instant(b),'state':state,'classical_citation':cite,
                'source_qualification':'verse_cited','detail':detail,'unqualified_reason':reason,'reasons':list(reasons),
                'moon_scope':scope,'obstructors':list(obstructors),'unknown_obstructors':list(unknown)}
    for graha,spans in residence.items():
        if graha=='Moon':  # on-demand testimony, never stored
            continue
        for sign,a,b in spans:
            a=max(instant(a),low); b=min(instant(b),high)
            house=(sign-moon_sign)%12+1
            if a>=b or (graha,house) not in pairs:
                continue
            for seg in house_intervals(graha,house,(a.isoformat(),b.isoformat()),moon_sign=moon_sign,residence=residence,pairs=pairs):
                intervals.append(interval('house_vedha',graha,seg['t_in'],seg['t_out'],seg['state'],cites[(graha,house)],
                    {'primary_house':house,'vedha_house':pairs[(graha,house)]},seg['reason'],seg['reasons'],seg['scope'],
                    seg['obstructors'],seg['unknown_obstructors']))
    seen=set()
    for rule in latta_rules:
        graha=rule['graha']
        if graha not in ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu') or graha in seen:
            raise ValueError('unsupported or duplicate latta source; Ketu has no cited rule')
        seen.add(graha)
        count=rule['count_from_graha']; direction=rule['direction']
        if type(count) is not int or not 1<=count<=27 or direction not in ('forward','backward') or not rule.get('source_citation') or not rule.get('verse_ref'):
            raise ValueError('latta requires a cited source count/direction/verse locator')
        for cell,a,b in nakshatra_residence.get(graha,()):
            target=(cell-1+(count-1)*(1 if direction=='forward' else -1))%27+1
            a=max(instant(a),low); b=min(instant(b),high)
            if target==moon_nak and a<b:
                intervals.append(interval('latta',graha,a,b,'active',rule['source_citation'],
                    {'source_nakshatra':cell,'target_nakshatra':target,'janma_reference_fact_id':janma_fact['fact_id'],
                     'verse_ref':rule['verse_ref'],'count_from_graha':count,'direction':direction}))
    intervals.sort(key=lambda r:(r['vedha_kind'],r['graha'],r['t_in']))
    return VedhaPayload(tuple(headers),tuple(intervals),janma_fact,sources)
