"""
dasha_periods.py -- loads the cached Vimsottari dasha-period substrate
(cache/dasha_periods.json) for chart 482012f1, fetched once live via
`ganita_dasha_periods_get` (see that file's fetch_meta for the exact window
and pagination receipt) and cached so repeated tuning runs do not hammer the
live connector (CLAUDE.md §I / protocol §F3 throttling discipline).

Dasha periods are deterministic L1 chart facts (chart_dashas), NOT LEL
outcome events -- the sealed test-split circuit breaker (lel.py) does not
apply to this file. This loader has no train/test boundary logic because
none is needed here.
"""
from __future__ import annotations

import json
from pathlib import Path

from .curve import DashaPeriod
from .dates import parse_date

CACHE_DIR = Path(__file__).parent / "cache"
DASHA_PERIODS_CACHE = CACHE_DIR / "dasha_periods.json"


def load_dasha_periods(cache_path: Path | None = None) -> list[DashaPeriod]:
    path = cache_path or DASHA_PERIODS_CACHE
    with path.open() as f:
        payload = json.load(f)
    out: list[DashaPeriod] = []
    for level, lord, start, end in payload["periods"]:
        out.append(DashaPeriod(level=level, lord=lord, start=parse_date(start), end=parse_date(end)))
    return out


def load_dasha_lord_capability(cache_path: Path | None = None) -> dict:
    path = cache_path or (CACHE_DIR / "dasha_lord_capability.json")
    with path.open() as f:
        return json.load(f)


def running_lord(periods: list[DashaPeriod], level: int, d) -> str | None:
    for p in periods:
        if p.level == level and p.start <= d < p.end:
            return p.lord
    return None
