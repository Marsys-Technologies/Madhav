"""Admitted-day-share report and the ND-H DVI guard (ND-H-20261005 conditions 2 and 4; FB-41, FB-50).

Outcome-free by construction: the only inputs are a generation's ADMITTED SPANS and the horizon — no life
event, no score. So the density evidence the pending fast-agent decision needs (ND-P2 rule 5) can be read
before any outcome is inspected.

    admitted-day share = days with at least one admitted span ÷ days in the horizon

reported per class and per series:

    P1, P2, P3 (union), P3_fast, P3_slow, P4 (alone, AS BUILT — with its DVI members), P4_no_dvi,
    kb_only (days admitted ONLY through a luminary kāraka target), union (the class, all paths)

The guard (pre-registered in the ruling): a class whose P4-ALONE share exceeds the protocol's 40% gain band
reverts its DVI member to SUPPORT in the NEXT generation. It is COMPUTED here and REPORTED; nothing in this
module edits a registry row or the current generation.

What this module does not do: it does not recompute P4 without DVI. P4 is an AND across agents, so the
no-DVI series is not a subtraction — it must be supplied as its own spans (`series="P4_no_dvi"`, the P4
sweep rerun over the non-DVI members). Absent ⇒ reported `None` with reason `series_not_supplied`, never 0.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

#: protocol §6.4 (C1): the gain band's upper bound, as a share
GAIN_BAND_UPPER = 0.40
GUARD_RULING = "ND-H-20261005"
#: ND-H's own partition: K-B names Jupiter/Saturn and Rāhu/Ketu and says "fast agents never"
SLOW_AGENTS = frozenset({"jupiter", "saturn", "rahu", "ketu"})
FAST_AGENTS = frozenset({"sun", "moon", "mars", "mercury", "venus"})
SERIES = ("P1", "P2", "P3", "P3_fast", "P3_slow", "P4", "P4_no_dvi", "kb_only", "union")
NOT_SUPPLIED = "series_not_supplied"


@dataclass(frozen=True)
class AdmittedSpan:
    """One admitted span of one class on one path: inclusive calendar days [lo, hi].

    `agent` (lowercase graha) is needed only for the P3 fast/slow split; `via_kb` marks a span admitted through
    a luminary kāraka target (`object_role karaka`); `series` overrides the path-derived series for a span of a
    RECOMPUTED series (`P4_no_dvi`)."""

    event_class: str
    path_id: str
    lo: dt.date
    hi: dt.date
    agent: str | None = None
    via_kb: bool = False
    series: str | None = None

    def __post_init__(self) -> None:
        if self.hi < self.lo:
            raise ValueError(f"span {self.event_class}/{self.path_id}: hi {self.hi} < lo {self.lo}")
        if self.series is not None and self.series != "P4_no_dvi":
            raise ValueError(f"span series {self.series!r}: only the recomputed 'P4_no_dvi' may be named")
        if self.agent is not None and self.agent not in SLOW_AGENTS | FAST_AGENTS:
            raise ValueError(f"span agent {self.agent!r} is not a lowercase graha")


def _days(spans, h0: dt.date, h1: dt.date) -> set[int]:
    out: set[int] = set()
    for s in spans:
        lo, hi = max(s.lo, h0), min(s.hi, h1)
        if lo <= hi:
            out.update(range(lo.toordinal(), hi.toordinal() + 1))
    return out


def class_day_sets(spans: list[AdmittedSpan], h0: dt.date, h1: dt.date) -> dict[str, set[int] | None]:
    """{series: the set of admitted days} for ONE class's spans; None where a series was not supplied."""
    built = [s for s in spans if s.series is None]
    by_path = {p: [s for s in built if s.path_id == p] for p in ("P1", "P2", "P3", "P4")}
    p3 = by_path["P3"]
    sets: dict[str, set[int] | None] = {p: _days(by_path[p], h0, h1) for p in by_path}
    if any(s.agent is None for s in p3):
        sets["P3_fast"] = sets["P3_slow"] = None            # the split needs every P3 span's agent
    else:
        sets["P3_fast"] = _days([s for s in p3 if s.agent in FAST_AGENTS], h0, h1)
        sets["P3_slow"] = _days([s for s in p3 if s.agent in SLOW_AGENTS], h0, h1)
    no_dvi = [s for s in spans if s.series == "P4_no_dvi"]
    sets["P4_no_dvi"] = _days(no_dvi, h0, h1) if no_dvi else None
    sets["union"] = _days(built, h0, h1)
    sets["kb_only"] = _days([s for s in built if s.via_kb], h0, h1) - _days(
        [s for s in built if not s.via_kb], h0, h1)
    return sets


def admitted_day_share_report(spans: list[AdmittedSpan], horizon: tuple[dt.date, dt.date], *,
                              dvi_members: dict[str, list[int]] | None = None,
                              generation: str | None = None) -> dict:
    """The report (FB-50 items 1 and 4) for every class present in `spans` or `dvi_members`.

    `dvi_members` is {class: [lagna houses]} of the GENERATION'S OWN H table (the caller reads it from the
    registry at the generation's rule_version) — the guard names what would revert; it re-picks nothing."""
    h0, h1 = horizon
    if h1 < h0:
        raise ValueError("horizon must be non-empty")
    total = (h1 - h0).days + 1
    dvi_members = dvi_members or {}
    classes = sorted({s.event_class for s in spans} | set(dvi_members))
    out_classes = {}
    for cls in classes:
        sets = class_day_sets([s for s in spans if s.event_class == cls], h0, h1)
        shares = {name: (None if sets[name] is None else round(len(sets[name]) / total, 6)) for name in SERIES}
        days = {name: (None if sets[name] is None else len(sets[name])) for name in SERIES}
        dvi = sorted(dvi_members.get(cls, ()))
        p4 = shares["P4"]
        exceeds = p4 is not None and p4 > GAIN_BAND_UPPER
        out_classes[cls] = {
            "admitted_days": days, "admitted_day_share": shares,
            "not_supplied": sorted(n for n in SERIES if sets[n] is None),
            "dvi_guard": {
                "ruling_ref": GUARD_RULING, "band_upper": GAIN_BAND_UPPER, "series": "P4",
                "p4_alone_share": p4, "exceeds_band": exceeds, "dvi_members": dvi,
                # the reversion applies to the NEXT generation only; a class with no DVI member has none to revert
                "revert_dvi_to_support_next_generation": dvi if (exceeds and dvi) else [],
                "applies_to": "next_generation",
            },
        }
    return {"artifact": "admitted_day_share", "generation": generation,
            "horizon": [h0.isoformat(), h1.isoformat()], "horizon_days": total,
            "reason_when_null": NOT_SUPPLIED, "classes": out_classes,
            "dvi_reversions_next_generation": {c: v["dvi_guard"]["revert_dvi_to_support_next_generation"]
                                               for c, v in out_classes.items()
                                               if v["dvi_guard"]["revert_dvi_to_support_next_generation"]}}


def load_spans(rows: list[dict]) -> list[AdmittedSpan]:
    """Spans from plain JSON rows: {event_class, path_id, lo, hi, agent?, via_kb?, series?} (ISO dates)."""
    return [AdmittedSpan(event_class=r["event_class"], path_id=r["path_id"],
                         lo=dt.date.fromisoformat(r["lo"]), hi=dt.date.fromisoformat(r["hi"]),
                         agent=r.get("agent"), via_kb=bool(r.get("via_kb", False)), series=r.get("series"))
            for r in rows]


__all__ = ["AdmittedSpan", "GAIN_BAND_UPPER", "FAST_AGENTS", "SLOW_AGENTS", "SERIES", "NOT_SUPPLIED",
           "admitted_day_share_report", "class_day_sets", "load_spans"]
