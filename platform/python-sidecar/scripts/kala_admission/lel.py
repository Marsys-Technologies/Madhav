"""
lel.py -- Life Event Log access for the D-3 ADMIT kernel-admission harness.

*** SEALED TEST-SPLIT CIRCUIT BREAKER (ESCALATION_POLICY_v1_0.md §4) ***

The LEL corpus is split train(36)/test(21) at boundary 2020-01-01: events
dated >= 2020-01-01 are TEST (sealed, never to be read by a build/admission
agent); events dated < 2020-01-01 are TRAIN. This module is the SOLE point
this lane reads LEL data through, and it enforces the boundary twice:

  1. AT FETCH TIME (already done, upstream of this file): the live
     `lel_query` MCP tool call that populated cache/lel_train_events.json
     was made with `date_to=2019-12-31` as a SERVER-SIDE filter argument
     (confirmed in the live response's `filter_applied.end_date` field --
     see that cache file's `fetch_meta` block for the exact receipt). No
     event >= 2020-01-01 ever entered this process's memory or logs -- the
     server excluded it before the response left the connector. This is the
     "constrain the fetch itself" path the brief requires, not a
     client-side post-filter.
  2. AT LOAD TIME (this module, `load_train_events()`): every event loaded
     from the cache is re-asserted < TEST_SPLIT_BOUNDARY. If the cache file
     were ever edited (by hand or by a future re-fetch) to include a
     TEST-split row, this assertion trips immediately and loudly -- the
     harness refuses to run rather than silently scoring a sealed event.
     This is the "belt and suspenders" layer: even though the fetch was
     already constrained server-side, nothing downstream trusts that
     invariant blindly.

No function in this module, or any caller of it, ever accepts a `date_to`
argument >= TEST_SPLIT_BOUNDARY, and no function here performs a live fetch
(this lane's fetch already happened, once, at cache-build time -- see
`cache/lel_train_events.json`'s `fetch_meta` for the exact call and receipt;
CLAUDE.md §I / protocol §F3 throttling discipline is why this harness reads
from the cache on every re-run instead of re-hitting the live connector).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

from .dates import parse_date

TEST_SPLIT_BOUNDARY: date = date(2020, 1, 1)  # events >= this date are TEST (sealed)

CACHE_DIR = Path(__file__).parent / "cache"
TRAIN_EVENTS_CACHE = CACHE_DIR / "lel_train_events.json"


class SealedTestSplitViolation(RuntimeError):
    """Raised if an event dated >= TEST_SPLIT_BOUNDARY is ever loaded by this
    module. This must never fire in normal operation -- if it does, the cache
    file has been contaminated with TEST-split data and the run must stop."""


@dataclass(frozen=True)
class LelEvent:
    event_id: str
    event_date: date
    category: str
    domain: str
    description: str


def load_train_events(cache_path: Optional[Path] = None) -> list[LelEvent]:
    """Loads the TRAIN-only LEL event cache and re-asserts the test-split
    boundary on every row. Raises SealedTestSplitViolation (not a warning,
    not a skip) if any row fails the check -- see module docstring."""
    path = cache_path or TRAIN_EVENTS_CACHE
    with path.open() as f:
        payload = json.load(f)

    events: list[LelEvent] = []
    for raw in payload["events"]:
        d = parse_date(raw["event_date"])
        if d >= TEST_SPLIT_BOUNDARY:
            raise SealedTestSplitViolation(
                f"lel.py refuses to load event_id={raw['event_id']!r} "
                f"event_date={raw['event_date']!r} -- this date is >= "
                f"{TEST_SPLIT_BOUNDARY.isoformat()} (the sealed TEST split "
                "boundary). This should be structurally impossible given "
                "the cache's server-side date_to fetch constraint -- if you "
                "are seeing this, the cache file has been contaminated and "
                "must not be used."
            )
        events.append(
            LelEvent(
                event_id=raw["event_id"],
                event_date=d,
                category=raw["category"],
                domain=raw["domain"],
                description=raw.get("description", ""),
            )
        )
    return events


# ── Scorability heuristic -- ported verbatim from
# platform/scripts/audit/t0_retrodiction/lib/lel.ts's VAGUENESS_PATTERNS /
# classifyScorability / partitionScorable (same regexes, same birth-anchor
# exclusion rule, same "scorable = discrete-onset events with month-or-better
# date precision" definition per BIND_D-3.md §B-3). ─────────────────────────

_VAGUENESS_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("phase_marker", re.compile(r"\bphase\s*\d", re.I)),
    ("arc_marker", re.compile(r"\barc\b", re.I)),
    ("multi_year_marker", re.compile(r"\bmulti-?year\b", re.I)),
    ("ongoing_marker", re.compile(r"\bongoing\b", re.I)),
    ("resurfaced_marker", re.compile(r"\bresurfaced\b", re.I)),
    ("persisted_n_years", re.compile(r"\bpersist(ed)?\s+~?\d+\s*years?\b", re.I)),
    ("tilde_year", re.compile(r"~\s*\d{4}")),
    ("circa", re.compile(r"\bcirca\b", re.I)),
    ("approximately", re.compile(r"\bapproximately\b", re.I)),
    ("bare_around_year", re.compile(r"\baround\s+\d{4}\b", re.I)),
    ("month_or_month", re.compile(r"\b[A-Z][a-z]+\s+or\s+[A-Z][a-z]+\s+\d{4}\b")),
    ("year_span_years", re.compile(r"\b\d+-\d+\s*years?\b", re.I)),
    ("paren_year_range", re.compile(r"\(~?\d{4}-\d{4}\)")),
]


@dataclass(frozen=True)
class ScorabilityVerdict:
    event_id: str
    scorable: bool
    reasons: list[str]


def classify_scorability(event: LelEvent) -> ScorabilityVerdict:
    if event.domain == "other/birth":
        return ScorabilityVerdict(event.event_id, False, ["birth_anchor_not_an_outcome"])
    reasons = [label for label, pat in _VAGUENESS_PATTERNS if pat.search(event.description)]
    return ScorabilityVerdict(event.event_id, len(reasons) == 0, reasons)


def partition_scorable(events: list[LelEvent]) -> tuple[list[LelEvent], list[tuple[LelEvent, list[str]]]]:
    scorable: list[LelEvent] = []
    excluded: list[tuple[LelEvent, list[str]]] = []
    for e in events:
        v = classify_scorability(e)
        if v.scorable:
            scorable.append(e)
        else:
            excluded.append((e, v.reasons))
    return scorable, excluded
