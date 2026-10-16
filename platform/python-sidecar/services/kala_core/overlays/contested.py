"""Candidate envelopes and sole consumer boundary for KA-3b testimony.

Pre-build under SR-A4-01. Nothing resolves a serving head or installs a judge
operand. Entries use explicit half-open UT JD intervals, never legacy dates.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from math import isfinite
from pathlib import Path
import re

from services.kala_core.sky import SkyConvention, SkyCoverage
from services.kala_core.vocab import MethodQualification, NullReason, OperatorRole

FAMILIES = ('moorti_nirnaya', 'kota_chakra', 'tithi_pravesha', 'sudarshana_varsha')
QUALIFICATIONS = {
    'moorti_nirnaya': MethodQualification.METHOD_CONTESTED,
    'kota_chakra': MethodQualification.UNCITED_EXTENSION,
    'tithi_pravesha': MethodQualification.METHOD_CONTESTED,
    'sudarshana_varsha': MethodQualification.METHOD_CONTESTED,
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), default=str, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class AdapterContext:
    chart_id: str
    generation: str
    natal_build_id: str
    convention: SkyConvention
    facts: tuple[dict, ...]

    def __post_init__(self):
        if not self.chart_id or not self.natal_build_id or not isinstance(self.convention, SkyConvention):
            raise ValueError('candidate chart, natal build and typed convention required')
        if not re.fullmatch(r'[A-Za-z0-9_.:-]+', self.generation or '') or self.generation in ('legacy', 'published', 'current', 'retained'):
            raise ValueError('an explicit new candidate generation is required')
        keys = [(f.get('fact_subject'), f.get('fact_key')) for f in self.facts]
        if len(set(keys)) != len(keys) or any(not f.get('fact_id') for f in self.facts):
            raise ValueError('ambiguous or unreferenced L1 facts')

    def fact(self, subject, key):
        found = next((f for f in self.facts if f.get('fact_subject') == subject and f.get('fact_key') == key), None)
        if found is not None and key == 'longitude_sidereal':
            lon = found.get('fact_value_num')
            if lon is None or not isfinite(float(lon)) or not 0 <= float(lon) < 360:
                raise ValueError('invalid L1 longitude')
        return found


@dataclass(frozen=True)
class AdapterPayload:
    family: str
    context: AdapterContext
    coverage: dict
    entries: tuple[dict, ...]
    sources: dict
    external_computation_required: tuple[dict, ...]
    null_reason: str | None
    method_qualification: MethodQualification
    operator_role: OperatorRole
    upstream_fingerprint: dict
    formula_version: str = 'ka_contested_candidate/1'

    def content(self):
        return {k: v for k, v in asdict(self).items() if k != 'upstream_fingerprint'}

    def validate(self):
        if self.family not in FAMILIES or self.method_qualification != QUALIFICATIONS[self.family] or self.operator_role != OperatorRole.TESTIMONY:
            raise ValueError('candidate qualification/role mismatch')
        if self.upstream_fingerprint != {'schema': 'ka_contested_inputs/1', 'digest': digest(self.content())}:
            raise ValueError('candidate fingerprint integrity failure')
        return self


def envelope(family, ctx, coverage, entries, *, sources=None, required=(('MOON', 'longitude_sidereal'),), null_reason=None):
    if not isinstance(ctx, AdapterContext) or not isinstance(coverage, SkyCoverage):
        raise TypeError('typed candidate context and sky coverage required')
    if coverage.convention_id != ctx.convention.convention_id:
        raise ValueError('sky convention does not match natal convention')
    missing = tuple({'asset': 'ga_positions', 'chart_id': ctx.chart_id, 'build_id': ctx.natal_build_id,
                     'ayanamsha_id': ctx.convention.ayanamsha_id, 'fact_category': 'graha_position',
                     'fact_subject': subject, 'fact_key': key}
                    for subject, key in required if ctx.fact(subject, key) is None)
    cov = asdict(coverage)
    cov['gaps'] = coverage.gaps
    cov['sky_complete'] = coverage.complete
    cov['search_state'] = 'searched' if coverage.complete else 'unsearched' if coverage.covered is None else 'partial'
    if not ctx.convention.computable:
        entries = ()
        null_reason = NullReason.INFORMATION_UNAVAILABLE
    if missing:
        entries = ()
        null_reason = NullReason.INFORMATION_UNAVAILABLE
        cov['complete'] = False
        cov['search_state'] = 'unsearched'
    elif coverage.covered is None:
        entries = ()
        null_reason = NullReason.INFORMATION_UNAVAILABLE
    elif not coverage.complete and null_reason is None:
        null_reason = NullReason.INFORMATION_UNAVAILABLE
    cov['method_gaps'] = [(r['t_in'], r['t_out']) for r in entries if r.get('null_reason')]
    if family in ('sudarshana_varsha', 'tithi_pravesha'):
        # Annual search provenance is earned by successful evaluations, never
        # by the requested years or sky availability. Older envelopes without
        # this provenance cannot certify a searched absence.
        searched = (sources or {}).get('searched_years', ())
        entries = tuple(r for r in entries if r['year'] in searched)
        cov['searched_years'] = tuple(sorted({r['year'] for r in entries}))
        intervals = []
        for lo, hi in sorted((r['t_in'], r['t_out']) for r in entries if not r.get('null_reason')):
            if intervals and lo <= intervals[-1][1]:
                intervals[-1] = (intervals[-1][0], max(hi, intervals[-1][1]))
            else:
                intervals.append((lo, hi))
        cov['method_intervals'] = tuple(intervals)
        # (I) INTERPRETATION: a computed lunar return certifies only its
        # declared one-second support, not the rest of that annual chart.
        # Sudarshana entries already carry their computed annual intervals.
        cursor, end = coverage.requested
        cov['method_gaps'] = []
        for lo, hi in intervals:
            if cursor < lo:
                cov['method_gaps'].append((cursor, lo))
            cursor = max(cursor, hi)
        if cursor < end:
            cov['method_gaps'].append((cursor, end))
        cov['complete'] = coverage.complete and not cov['method_gaps'] and bool(intervals)
        cov['search_state'] = 'searched' if cov['complete'] else 'partial' if intervals else 'unsearched'
    if cov['method_gaps'] and null_reason is None:
        null_reason = NullReason.INFORMATION_UNAVAILABLE
    if null_reason is not None:
        cov['complete'] = False
        cov['search_state'] = 'partial' if entries else 'unsearched'
    from dataclasses import replace
    p = AdapterPayload(family, ctx, cov, tuple(entries), sources or {}, missing, null_reason,
                       QUALIFICATIONS[family], OperatorRole.TESTIMONY, {})
    return replace(p, upstream_fingerprint={'schema': 'ka_contested_inputs/1', 'digest': digest(p.content())})


def testimony(payload, *, at, view='NOW', chart_id=None, generation=None, fingerprint=None):
    """Both NOW and AHEAD consume the same envelope, with no scored operand."""
    if not isinstance(payload, AdapterPayload):
        raise TypeError('typed adapter payload required')
    payload.validate()
    if view not in ('NOW', 'AHEAD') or not isfinite(float(at)):
        raise ValueError('unknown view or nonfinite instant')
    ctx = payload.context
    if ((chart_id is not None and chart_id != ctx.chart_id)
            or (generation is not None and generation != ctx.generation)
            or (fingerprint is not None and fingerprint != payload.upstream_fingerprint['digest'])):
        raise ValueError('adapter identity/fingerprint mismatch')
    covered = payload.coverage['covered']
    inside = covered is not None and covered[0] <= at < covered[1]
    method_intervals = payload.coverage.get('method_intervals')
    if method_intervals is not None:
        inside = inside and any(lo <= at < hi for lo, hi in method_intervals)
    entries = [r for r in payload.entries if inside and r['t_in'] <= at < r['t_out']]
    reason = payload.null_reason if inside else NullReason.INFORMATION_UNAVAILABLE
    if inside and method_intervals is not None:
        # A gap elsewhere in a sparse annual request does not invalidate the
        # successfully computed object at this instant.
        reason = next((r['null_reason'] for r in entries if r.get('null_reason')), None)
    # No numeric factor bridge: contested values are structured testimony only.
    return {'value': None, 'operator_role': OperatorRole.TESTIMONY,
            'method_qualification': payload.method_qualification, 'entries': entries,
            'coverage': payload.coverage, 'upstream_fingerprint': payload.upstream_fingerprint,
            'null_reason': reason,
            'external_computation_required': payload.external_computation_required}


_BYPASS = re.compile(r'\b(?:FROM|JOIN)\s+(?:"?public"?\s*\.\s*)?"?kala_(?:' + '|'.join(FAMILIES) + r')_candidate\b"?|'
                     r'\b(?:from|import)\s+services\.ka_(?:' + '|'.join(FAMILIES) + r')\.candidate\b', re.I)


def lint_consumers(paths):
    offenders = [str(p) for p in paths if _BYPASS.search(Path(p).read_text())]
    if offenders:
        raise ValueError('contested adapter consumer must use kala_core.overlays: ' + ', '.join(offenders))


def index_ledger(indexes):
    """Fingerprint the substrate actually consumed, including its noon UT JDs."""
    return {g: {'jds': list(map(float, index.knot_jds)),
                'longitudes': [float(index.lon_unwrapped(jd)) for jd in index.knot_jds]}
            for g, index in sorted(indexes.items())}
