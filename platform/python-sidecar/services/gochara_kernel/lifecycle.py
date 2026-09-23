"""Arc lifecycle: arcs are built ONCE per (body × substrate_version × knot
window), globally — pure geometry with no chart dependence (plan §4.2:
"arcs are global, contacts are per chart"). Contact solving is per chart and
never rebuilds the index.

The registry is the explicit cache/lifecycle API the plan asks for: a
process-wide singleton keyed by (body, substrate_version, start, end), with
build counts exposed so tests can assert the build-once property.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable

from .arcs import ArcIndex, build_arc_index
from .knots import KnotSeries, sample_knots


@dataclass(frozen=True)
class ArcKey:
    body: str
    substrate_version: str
    start: date
    end: date


class ArcIndexRegistry:
    """Build-once cache of arc indices over pure geometry.

    `knot_sampler` is injectable (tests substitute synthetic series); the
    default samples Swiss sidereal noon-UT knots (F-15, D-1, N-4a(b″)).
    """

    def __init__(
        self,
        knot_sampler: Callable[..., KnotSeries] = sample_knots,
        ephe_path: str | None = None,
    ):
        self._knot_sampler = knot_sampler
        self._ephe_path = ephe_path
        self._cache: dict[ArcKey, ArcIndex] = {}
        self.build_count = 0

    def get(
        self,
        body: str,
        substrate_version: str,
        start: date,
        end: date,
        ephe_path: str | None = None,
    ) -> ArcIndex:
        key = ArcKey(body, substrate_version, start, end)
        if key not in self._cache:
            series = self._knot_sampler(
                body, start, end, ephe_path if ephe_path is not None else self._ephe_path
            )
            self._cache[key] = build_arc_index(
                body, series.knot_jds, series.longitudes_deg
            )
            self.build_count += 1
        return self._cache[key]

    def get_from_series(
        self,
        body: str,
        substrate_version: str,
        start: date,
        end: date,
        series: KnotSeries,
    ) -> ArcIndex:
        """Register a pre-sampled (e.g. synthetic or fixture) knot series
        under the same build-once key."""
        key = ArcKey(body, substrate_version, start, end)
        if key not in self._cache:
            self._cache[key] = build_arc_index(
                body, series.knot_jds, series.longitudes_deg
            )
            self.build_count += 1
        return self._cache[key]

    def invalidate(self, body: str | None = None) -> None:
        if body is None:
            self._cache.clear()
        else:
            self._cache = {k: v for k, v in self._cache.items() if k.body != body}

    def __len__(self) -> int:
        return len(self._cache)


__all__ = ["ArcIndexRegistry", "ArcKey"]
