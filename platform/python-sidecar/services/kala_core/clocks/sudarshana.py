"""Candidate-only BPHS 74.21-23 periods; never an L1 chart_dashas writer.

(I) INTERPRETATION: divide the declared civil-birthday year into twelve equal
parts at each depth. The text's 360-day nominal year, 30-day month, 2.5 days
and 12.5 ghatika retain their ratios; actual elapsed durations scale with the
anchor interval. A solar-return instant is neither calculated nor claimed.
"""
from __future__ import annotations

from hashlib import sha256
import json
from math import isfinite
import re

from .methods import validate_f2_row

FRAMES = ('lagna', 'moon', 'sun')
_NOMINAL_DAYS = (360., 30., 2.5, 5/24)


def period_rows(*, chart_id, generation, natal_build_id, convention_id,
                varsha_year, t_in, t_out, natal_signs, frame_fact_ids, year_anchor):
    """Emit linked half-open F2 rows, with annual applicability and L1 refs.

    Every child starts its own twelve-sign circuit at its parent's sign.
    Identities include the whole pin and ordinal lineage, never rounded dates.
    The coincident-frame rule is applied before any periods or judgments exist.
    """
    if (not all((chart_id, natal_build_id, convention_id))
            or not re.fullmatch(r'[A-Za-z0-9_.:-]+', generation or '')
            or generation in ('legacy', 'published', 'current', 'retained')
            or type(varsha_year) is not int or varsha_year < 1
            or not all(isfinite(v) for v in (t_in, t_out)) or t_in >= t_out
            or year_anchor != 'civil_birthday'):
        raise ValueError('explicit candidate pin, positive year and finite declared anchor required')
    if (set(natal_signs) != set(FRAMES) or set(frame_fact_ids) != set(FRAMES)
            or any(type(v) is not int or v not in range(12) for v in natal_signs.values())
            or not all(frame_fact_ids.values())):
        raise ValueError('three valid natal signs and L1 references required')
    collapsed = len(set(natal_signs.values())) < 3
    frames = (('birth_chart', natal_signs['lagna']),) if collapsed else tuple(natal_signs.items())
    rows = []
    for frame, natal in frames:
        refs = [frame_fact_ids[k] for k in FRAMES] if collapsed else [frame_fact_ids[frame]]

        def emit(lo, hi, sign, lineage, parent=None):
            level = len(lineage) + 1
            key = [chart_id, generation, natal_build_id, convention_id,
                   varsha_year, frame, lineage, t_in, t_out, year_anchor]
            identity = sha256(json.dumps(key, separators=(',', ':')).encode()).hexdigest()
            row = dict(period_id=identity, parent_period_id=parent, child_period_ids=[],
                       chart_id=chart_id, generation=generation, natal_build_id=natal_build_id,
                       convention_id=convention_id, method_id='sudarshana_bphs74_candidate/1',
                       varsha_year=varsha_year, frame=frame, level_n=level,
                       ordinal_path=list(lineage), sign_idx=sign, t_in=lo, t_out=hi,
                       nominal_days=_NOMINAL_DAYS[level-1], applicability_tags=['annual'],
                       source='BPHS 74.21-23', fact_ids=refs,
                       coincident_frame_policy='birth_chart_only' if collapsed else 'three_distinct_frames',
                       year_anchor=year_anchor, anchor_source_status='declared_convention',
                       duration_convention='proportional_360_day_year')
            rows.append(row)
            if level < 4:
                # Shared cut values ensure exact equality at every seam and the
                # parent's last endpoint, including leap-year civil anchors.
                cuts = [lo + (hi-lo)*k/12 for k in range(12)] + [hi]
                for k in range(12):
                    row['child_period_ids'].append(emit(
                        cuts[k], cuts[k+1], (sign+k)%12, (*lineage, k+1), identity))
            return identity

        emit(t_in, t_out, (natal + varsha_year-1)%12, ())
    validate_f2_row(rows)
    return rows
