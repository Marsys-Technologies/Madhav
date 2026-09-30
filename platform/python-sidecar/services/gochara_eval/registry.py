"""Event-registry loader and validation (protocol v2.3 §1, §2, §3, §9.2).

The registry is the ONLY event source. Loads the machine-readable registry
JSON, validates the 27-class universe and the header-count reconciliation
(protocol §9.2: scorer-derived counts vs registry header counts), and exposes
held-out / dev / excluded / annotation partitions plus per-event span helpers.

All event dates are IST calendar dates (protocol §3). Interval endpoints are
calendar-date inclusive on both ends; spans are counted in days inclusive.
"""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path

# Protocol v2.3 §1 / §3 constants.
H0 = dt.date(1998, 1, 1)          # scored horizon start
H1 = dt.date(2026, 4, 17)         # observation mask end
H_DAYS = (H1 - H0).days + 1       # 10,334
CAP_DAYS = 182                    # capped miss value (protocol §5)
TIE_TOL = 1e-9                    # ONE tie tolerance (protocol §4.3, §8.3)

# Protocol v2.3 §2 — the full 27-class table (fixed universe).
CLASSES_27 = [
    "achievement_recognition", "bereavement", "birth_anchor", "business_launch",
    "career_advancement", "career_change", "career_entry", "career_setback",
    "childbirth", "chronic_onset", "education_milestone", "exam_outcome",
    "financial_deception", "foreign_settlement", "illness_acute", "major_gain",
    "major_loss", "marriage", "parental_event", "property_acquisition",
    "psychological_arc", "relocation", "romantic_start", "separation",
    "spiritual_turn", "surgery", "travel_event",
]

# Protocol v2.3 §2 — the frozen adverse set (T-FP).
ADVERSE_CLASSES = [
    "bereavement", "career_setback", "chronic_onset", "financial_deception",
    "illness_acute", "parental_event", "separation", "surgery", "major_loss",
]

HELD_TIERS = ("held_out_timing", "held_out_year")
TIMING_GRAINS = ("exact", "month", "interval")

# The three §11.3 worked events are development cases: tier 'dev', calibration
# only, NEVER scored as held-out (oracle harness_contract.worked_events).
WORKED_EVENT_DATES = ("2013-12-11", "2018-11-28", "2022-01-03")


class RegistryError(ValueError):
    """Registry failed validation (counts, class universe, or structure)."""


@dataclass(frozen=True)
class HeldEvent:
    """One scored registry row (held-out tiers only)."""

    eid: str
    cls: str
    grain: str                     # exact | month | interval | year
    date_or_span: object           # str date for exact/month/year; (lo, hi) for interval
    tier: str                      # held_out_timing | held_out_year

    def span(self) -> tuple[dt.date, dt.date]:
        """Event's scored span as inclusive IST calendar dates (protocol §1, §3)."""
        if self.grain == "exact":
            d = dt.date.fromisoformat(self.date_or_span)
            return d, d
        if self.grain == "month":
            y, m = map(int, self.date_or_span.split("-"))
            lo = dt.date(y, m, 1)
            hi = dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)
            return lo, hi
        if self.grain == "interval":
            return (dt.date.fromisoformat(self.date_or_span[0]),
                    dt.date.fromisoformat(self.date_or_span[1]))
        y = int(self.date_or_span)
        return dt.date(y, 1, 1), dt.date(y, 12, 31)

    def proxy_date(self) -> dt.date:
        """Error-proxy date (protocol §5): 15th of the month; interval midpoint."""
        if self.grain == "exact":
            return dt.date.fromisoformat(self.date_or_span)
        if self.grain == "month":
            y, m = map(int, self.date_or_span.split("-"))
            return dt.date(y, m, 15)
        if self.grain == "interval":
            lo = dt.date.fromisoformat(self.date_or_span[0])
            hi = dt.date.fromisoformat(self.date_or_span[1])
            return lo + (hi - lo) // 2
        return dt.date(int(self.date_or_span), 7, 1)

    def event_year(self) -> int:
        if self.grain == "year":
            return int(self.date_or_span)
        return self.span()[0].year


@dataclass
class Registry:
    """Validated registry: partitions + reconciliation record."""

    held: list[HeldEvent]          # 47 held-out rows (32 timing + 15 year)
    dev: list[dict]                # calibration only — excluded from every endpoint
    excluded: list[dict]
    annotations: list[dict]        # unscored
    raw_events: list[dict]
    header_counts: dict
    reconciliation: dict           # status MATCH + scorer-derived vs header detail
    horizon_start: dt.date = H0
    horizon_end: dt.date = H1

    @property
    def n_timing_usable(self) -> int:
        return sum(1 for e in self.held if e.tier == "held_out_timing")


def _event_from_row(row: dict) -> HeldEvent:
    cls = row["class"]
    if cls not in CLASSES_27:
        raise RegistryError(
            f"INPUT_REJECTED: registry row {row.get('eid')} carries class {cls!r} "
            "outside the §2 27-class universe")
    grain = row["grain"]
    date_or_span = row.get("date") if row.get("date") is not None else tuple(row["span"])
    return HeldEvent(eid=row["eid"], cls=cls, grain=grain,
                     date_or_span=date_or_span, tier=row["tier"])


def load_registry(path: str | Path) -> Registry:
    """Load and validate the machine-readable event registry.

    Raises RegistryError on: unknown class (INPUT_REJECTED semantics), or a
    source-reconciliation mismatch between scorer-derived counts and the
    registry header counts (protocol §9.2 — neither side presumed correct).
    """
    path = Path(path)
    reg = json.loads(path.read_text())
    events = reg["events"]
    for row in events:
        if "class" not in row:
            if row["tier"] in HELD_TIERS:
                raise RegistryError(
                    f"INPUT_REJECTED: held-out registry row {row.get('eid')} "
                    "carries no class")
            continue
        if row.get("class") not in CLASSES_27:
            raise RegistryError(
                f"INPUT_REJECTED: registry row {row.get('eid')} carries class "
                f"{row.get('class')!r} outside the §2 27-class universe")

    held_rows = [e for e in events if e["tier"] in HELD_TIERS]
    dev = [e for e in events if e["tier"] == "dev"]
    excluded = [e for e in events if e["tier"] == "excluded"]
    annotations = [e for e in events if e["tier"] == "annotation"]
    held = [_event_from_row(e) for e in held_rows]

    hdr = reg["conventions"]["counts"]
    recon_detail = {
        "held_out": (len(held), hdr["held_out"]),
        "timing": (sum(1 for e in held if e.tier == "held_out_timing"),
                   hdr["held_out_timing"]),
        "year": (sum(1 for e in held if e.tier == "held_out_year"),
                 hdr["held_out_year"]),
        "exact": (sum(1 for e in held if e.grain == "exact"), hdr["exact_cohort"]),
        "interval": (sum(1 for e in held if e.grain == "interval"),
                     hdr["interval_grain"]),
        "dev": (len(dev), hdr["dev"]),
        "excluded": (len(excluded), hdr["excluded"]),
        "annotation": (len(annotations), hdr["annotation_rows"]),
    }
    mismatched = {k: v for k, v in recon_detail.items() if v[0] != v[1]}
    if mismatched:
        raise RegistryError(
            "SOURCE-RECONCILIATION HALT: scorer-derived counts differ from the "
            f"registry header — documented diff required (protocol §9.2): {mismatched}")
    reconciliation = {"status": "MATCH", "detail": recon_detail}

    # Worked-event guard: the three §11.3 development events must be dev-tier
    # (calibration only) and must never appear in a held-out partition.
    held_dates = {e.date_or_span for e in held if isinstance(e.date_or_span, str)}
    leaked = sorted(set(WORKED_EVENT_DATES) & held_dates)
    if leaked:
        raise RegistryError(
            f"INPUT_REJECTED: worked/development events in held-out partition: {leaked}")

    horizon = reg.get("horizon", {})
    h0 = dt.date.fromisoformat(horizon.get("start", H0.isoformat()))
    h1 = dt.date.fromisoformat(horizon.get("end", H1.isoformat()))

    return Registry(held=held, dev=dev, excluded=excluded, annotations=annotations,
                    raw_events=events, header_counts=hdr, reconciliation=reconciliation,
                    horizon_start=h0, horizon_end=h1)
