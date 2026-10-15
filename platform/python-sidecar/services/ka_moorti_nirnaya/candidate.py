"""Named moorti_nakshatra_27 legacy method, corrected to sky UT ingress.

The twelve-sign variant is not admitted. No score/suppression is produced.
The legacy writer and its daily epoch remain unchanged.
"""
from services.kala_core.overlays.contested import AdapterContext, envelope, index_ledger
from services.kala_core.sky import boundary_events, coverage_of, ephemeris_at
from services.kala_core.vocab import NullReason
from .logic import MOORTI_GRAHAS, nakshatra_offset_from_janma


def build_candidate(*, ctx: AdapterContext, indexes, horizon, moorti_rows, ephe_path=None):
    rows = list(moorti_rows)
    table = {int(r['nakshatra_offset']): dict(r) for r in rows}
    if len(table) != len(rows) or any(not 1 <= k <= 27 for k in table):
        raise ValueError('duplicate or invalid moorti source offset')
    results = {g: boundary_events(index, g, ['sign_ingress'], horizon, ctx.convention.convention_id, ephe_path=ephe_path)
               for g, index in sorted(indexes.items()) if g in MOORTI_GRAHAS}
    bounds = [r.coverage.covered for r in results.values()]
    source = (max(b[0] for b in bounds), min(b[1] for b in bounds)) if bounds and all(bounds) else None
    if source and source[0] >= source[1]:
        source = None
    coverage = coverage_of(horizon, source, backend='swieph', convention_id=ctx.convention.convention_id)
    fact = ctx.fact('MOON', 'longitude_sidereal')
    entries = []
    missing = not table or fact is None
    if not missing and coverage.covered:
        janma = int(float(fact['fact_value_num']) / (360/27))
        lo, hi = coverage.covered
        for graha, result in results.items():
            events = [e for e in result.values if lo <= e.jd < hi]
            if not events or events[0].jd > lo:
                entries.append({'graha': graha, 't_in': lo, 't_out': events[0].jd if events else hi,
                                'ingress_jd': None, 'moon_evaluated_jd': None, 'moorti_name': None,
                                'null_reason': NullReason.INFORMATION_UNAVAILABLE,
                                'method_id': 'moorti_nakshatra_27', 'source_status': 'uncited_legacy'})
            for i, event in enumerate(events):
                moon = ephemeris_at(event.jd, ctx.convention, bodies=('Moon',), ephe_path=ephe_path)
                if not moon.available:
                    missing = True
                    continue
                nak = int(moon.values[0].position('Moon').longitude_deg / (360/27))
                offset = nakshatra_offset_from_janma(nak, janma)
                source_row = table.get(offset)
                if source_row is None:
                    missing = True
                    continue
                entries.append({'graha': graha, 't_in': event.jd, 't_out': events[i+1].jd if i+1 < len(events) else hi,
                    'ingress_jd': event.jd, 'event_id': str(event.event_id), 'target_sign_idx': event.cell_after,
                    'moon_evaluated_jd': moon.values[0].jd, 'moon_nakshatra_idx': nak,
                    'janma_fact_id': fact['fact_id'], 'nakshatra_offset': offset,
                    'moorti_name': source_row['moorti_name'], 'quality_tier': source_row['quality_tier'],
                    'source_row': source_row, 'method_id': 'moorti_nakshatra_27', 'source_status': 'uncited_legacy',
                    'epoch_correction': 'sky_UT_instant; legacy epoch preserved separately'})
    return envelope('moorti_nirnaya', ctx, coverage, () if not table else entries,
                    sources={'moorti_rows': sorted(rows, key=lambda r:r['nakshatra_offset']), 'sky_indexes': index_ledger(indexes)},
                    null_reason=NullReason.INFORMATION_UNAVAILABLE if missing else None)
