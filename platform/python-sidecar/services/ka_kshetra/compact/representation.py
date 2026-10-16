"""Lossless, immutable column storage of the existing Segment representation.

Boundary/alpha/gamma doubles are packed without arithmetic. Evaluation is
O(log n); integration retains the existing segment arithmetic and summation
order, including EPS_GAMMA's documented flat branch. No DB or writer hooks.
"""
from __future__ import annotations

import bisect
import math
from dataclasses import dataclass
from typing import Iterable, Literal

from array import array
from services.ka_kshetra.contracts import Segment
from services.ka_kshetra.integrator import segment_integral


def _column(values) -> memoryview:
    return memoryview(array('d', values).tobytes()).cast('d')


@dataclass(frozen=True)
class CompactField:
    _edges: memoryview
    _alpha: memoryview
    _gamma: memoryview
    _metadata: tuple

    @classmethod
    def from_segments(cls, source: Iterable[Segment]) -> 'CompactField':
        rows = tuple(source)
        if not rows:
            raise ValueError('empty field has no numerical contract')
        for i, row in enumerate(rows):
            if (row.index != i or row.t_end <= row.t_start or
                    not all(math.isfinite(v) for v in (row.t_start, row.t_end, row.alpha, row.gamma))):
                raise ValueError('segments require finite coefficients, positive widths and ordered indices')
            if i and rows[i - 1].t_end != row.t_start:
                raise ValueError('segments must be contiguous without overlap')
        return cls(
            _column([r.t_start for r in rows] + [rows[-1].t_end]),
            _column(r.alpha for r in rows), _column(r.gamma for r in rows),
            tuple((r.refinement_depth, r.refinement_exhausted, r.refinement_residual) for r in rows),
        )

    def segment_index(self, t: float, *, side: Literal['left', 'right'] = 'right') -> int:
        if side not in ('left', 'right'):
            raise ValueError('side must be left or right')
        if not math.isfinite(t):
            raise ValueError('time outside finite horizon')
        i = (bisect.bisect_left if side == 'left' else bisect.bisect_right)(self._edges, t) - 1
        if not 0 <= i < len(self._alpha):
            raise ValueError('time outside the requested one-sided horizon')
        return i

    def _row(self, i: int) -> Segment:
        depth, exhausted, residual = self._metadata[i]
        return Segment(i, self._edges[i], self._edges[i + 1], self._alpha[i], self._gamma[i],
                       depth, exhausted, residual)

    def segments(self) -> tuple[Segment, ...]:
        return tuple(self._row(i) for i in range(len(self._alpha)))

    def ln_lambda(self, t: float, *, side: Literal['left', 'right'] = 'right') -> float:
        i = self.segment_index(t, side=side)
        return self._alpha[i] + self._gamma[i] * (t - self._edges[i])

    def integral(self, a: float, b: float) -> float:
        if not all(math.isfinite(t) for t in (a, b)):
            raise ValueError('integral endpoints must be finite')
        if b <= a:
            return 0.0
        total = 0.0
        first = max(0, bisect.bisect_right(self._edges, a) - 1)
        for i in range(first, len(self._alpha)):
            if self._edges[i] >= b:
                break
            u, v = max(a, self._edges[i]), min(b, self._edges[i + 1])
            if v > u:
                total += segment_integral(self._row(i), u, v)
        return total
