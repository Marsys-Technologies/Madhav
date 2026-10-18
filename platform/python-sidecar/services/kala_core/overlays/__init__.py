"""Independent, half-open obstruction sweep over cited pairs and sky residences.

No judge derivation, legacy cancellation, sampled-day interpolation or score is
used here. Empty residence is missing sky information, never established absence.
"""
from datetime import datetime, timezone
from math import isfinite

from services.gochara_rules.vedha_derive import VedhaPairs
from services.kala_core.ayanamsha import sidereal_longitude

STORED = ('Sun', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn')
NODES = ('Rahu', 'Ketu')
MOON_SCOPE = 'excluding_on_demand_moon_obstruction'


def instant(value):
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError('residence timestamps require an explicit UTC offset')
    return dt.astimezone(timezone.utc)


def validated_residence(spans, cells=12):
    out = []
    for cell, lo, hi in spans:
        if type(cell) is not int or not 1 <= cell <= cells or instant(lo) >= instant(hi):
            raise ValueError('invalid residence cell or interval')
        out.append((cell, lo, hi))
    out.sort(key=lambda row: instant(row[1]))
    if any(instant(a[2]) > instant(b[1]) for a,b in zip(out,out[1:])):
        raise ValueError('overlapping residence spans')
    return out


def excepted(a,b):
    return {a,b} in ({'Sun','Saturn'}, {'Moon','Mercury'})


def house_intervals(primary, primary_house, primary_span, *, moon_sign, residence, pairs):
    """Partition a primary span at every relevant occupancy/coverage boundary.

    This endpoint sweep is independent of the verifier's intersection/union/
    subtraction derivation. Both consume the same validated L0 pair authority.
    """
    if not isinstance(pairs,VedhaPairs):
        raise ValueError('pairs must be a validated complete L0 load')
    if type(moon_sign) is not int or not 1 <= moon_sign <= 12:
        raise ValueError('moon_sign must be 1..12')
    lo,hi=map(instant,primary_span)
    if lo >= hi:
        raise ValueError('empty or reversed primary interval')
    key=(primary,primary_house)
    if key not in pairs:
        return []
    necessary=[g for g in STORED if g!=primary and not excepted(primary,g)]
    spans={g:validated_residence(residence.get(g,())) for g in necessary+list(NODES)}
    # Canonicalize equivalent offsets at a cut; preserve the caller's endpoint
    # spelling so exact fixture/oracle comparisons remain possible.
    labels={lo:primary_span[0],hi:primary_span[1]}
    for rows in spans.values():
        for _,a,b in rows:
            for t in (a,b):
                if lo < instant(t) < hi:
                    labels[instant(t)]=t
    cuts=sorted(labels)
    def occupants(g,t):
        return [cell for cell,a,b in spans[g] if instant(a)<=t<instant(b)]
    raw=[]
    previous_signature=None
    for a,b in zip(cuts,cuts[1:]):
        cells={g:occupants(g,a) for g in spans}
        active=sorted(g for g in necessary if cells[g] and (cells[g][0]-moon_sign)%12+1==pairs[key])
        unknown=sorted(g for g in necessary if not cells[g])
        reasons=[]
        if unknown:
            reasons.append('obstructor_residence_unknown')
        if any(cells[g] and (cells[g][0]-moon_sign)%12+1==pairs[key] for g in NODES):
            reasons.append('node_obstruction_undecided')
        if any(not cells[g] for g in NODES):
            reasons.append('node_residence_unknown')
        state='active' if active else 'unqualified' if reasons else 'inactive'
        item={'t_in':labels[a],'t_out':labels[b],'state':state,
              'value':0.0 if active else None if reasons else 1.0,
              'reason':reasons[0] if reasons and not active else None,
              'reasons':reasons if not active else [],
              'scope':MOON_SCOPE if state=='inactive' and primary!='Mercury' else None,
              'obstructors':active,'unknown_obstructors':unknown if not active else []}
        signature=(tuple(active),tuple(unknown),any(not cells[g] for g in NODES),
                   bool(not active and any(cells[g] and (cells[g][0]-moon_sign)%12+1==pairs[key] for g in NODES)))
        # Only semantically relevant boundaries survive: a change between two
        # non-vedha signs is not a new vedha interval (matches the oracle).
        if raw and signature==previous_signature:
            raw[-1]['t_out']=item['t_out']
        else:
            raw.append(item)
        previous_signature=signature
    return raw


def sidereal_samples(samples, ayanamsha_id):
    """Tropical samples converted at their own UT JD; never a fixed offset."""
    return tuple((jd,sidereal_longitude(lon,jd,ayanamsha_id)) for jd,lon in samples)


def sky_residences(events, initial, body, relation='sign_ingress'):
    """Exact residences from sky boundary events and an initial sky position.

    Initial state must be measured at the covered lower bound; no origin or
    missing crossing is guessed. Only the sky's accepted horizon is answered.
    """
    from services.kala_core.sky.identity import kernel_body
    from services.gochara_kernel.substrate import jd_to_utc
    if not events.available or not initial.available or events.coverage.covered is None:
        return ()
    lo,hi=events.coverage.covered
    if events.coverage.convention_id != initial.coverage.convention_id:
        raise ValueError('sky convention mismatch')
    answer,=initial.values
    if answer.jd!=lo:
        raise ValueError('initial sky position must be at coverage start')
    width={'sign_ingress':30.0,'nakshatra_ingress':360/27}[relation]
    body=kernel_body(body)
    cell=int(answer.position(body).longitude_deg//width)+1
    cursor=lo
    out=[]
    for event in sorted(events.values,key=lambda e:e.jd):
        if event.body!=body or event.relation!=relation:
            continue
        if not isfinite(event.jd) or not lo<=event.jd<hi:
            raise ValueError('sky event outside covered interval')
        if event.jd>cursor:
            out.append((cell,jd_to_utc(cursor).isoformat(),jd_to_utc(event.jd).isoformat()))
        cell=event.cell_after+1
        cursor=event.jd
    if cursor<hi:
        out.append((cell,jd_to_utc(cursor).isoformat(),jd_to_utc(hi).isoformat()))
    return tuple(out)
