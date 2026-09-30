"""vedha_interval_relation (GOCHARA_DESIGN_SPECS_v1_4 §5) — obstruction as
intervals, not flags.

Half-open [t_in, t_out) intervals. Attenuation only where state=active at t
(#17); vipareeta CARVES a sub-interval out of the obstruction (it is not a
flag flip); the exception pairs Sun↔Saturn and Moon↔Mercury never obstruct
each other (M-8); absent overlay coverage reads as `unavailable` with a
coverage object, never as factor 1.0 (#25, O-VI-5). Vedha qualifies a
specific primary transit; it never excludes a window (§5.2 inv 1).
"""
from __future__ import annotations

from dataclasses import dataclass, field

STATES = frozenset({"active", "cancelled_vipareeta", "inactive"})

# M-8: these two pairs never obstruct each other.
EXCEPTION_PAIRS = frozenset({
    frozenset({"Sun", "Saturn"}),
    frozenset({"Moon", "Mercury"}),
})


@dataclass
class VedhaInterval:
    vi_id: str
    rule_version: str
    primary_contact_id: str
    obstructor_body: str
    vedha_kind: str
    t_in: str
    t_out: str
    state: str
    exception: str = "none"
    independence_group: str | None = None
    source_ref: str | None = None
    provenance: str = "verse_cited"
    operator_role: str = "scored"
    attenuation: float = 1.0  # the grade→key mapping is data in the rule row
    carved_from: str | None = None

    def __post_init__(self):
        if self.state not in STATES:
            raise ValueError(f"unknown vedha state {self.state!r}")
        if not (0.0 <= self.attenuation <= 1.0):
            raise ValueError("vedha attenuation ≤ 1 (§2.1 codomain)")

    def covers(self, t: str) -> bool:
        """Half-open [t_in, t_out): t = t_out belongs to the next interval."""
        return self.t_in <= t < self.t_out


def exception_for(primary_body: str, obstructor_body: str) -> str:
    pair = frozenset({primary_body, obstructor_body})
    if pair == frozenset({"Sun", "Saturn"}):
        return "sun_saturn"
    if pair == frozenset({"Moon", "Mercury"}):
        return "moon_mercury"
    return "none"


def create_vedha_interval(*, vi_id: str, rule_version: str,
                          primary_contact_id: str, primary_body: str,
                          obstructor_body: str, vedha_kind: str,
                          t_in: str, t_out: str, attenuation: float,
                          source_ref: str | None = None) -> list[VedhaInterval]:
    """Create the obstruction interval for an obstructor occupying a
    primary's vedha house — EXCEPT the two exception pairs, for which NO
    interval is ever created (M-8; O-VI-3)."""
    exc = exception_for(primary_body, obstructor_body)
    if exc != "none":
        return []
    return [VedhaInterval(vi_id=vi_id, rule_version=rule_version,
                          primary_contact_id=primary_contact_id,
                          obstructor_body=obstructor_body,
                          vedha_kind=vedha_kind, t_in=t_in, t_out=t_out,
                          state="active", exception="none",
                          attenuation=attenuation, source_ref=source_ref)]


def carve_vipareeta(interval: VedhaInterval,
                    vipareeta_span: tuple[str, str]) -> list[VedhaInterval]:
    """Vipareeta cancellation CARVES the covered sub-interval out of the
    obstruction — the row is not flag-flipped inactive (O-VI-4). Returns the
    active remainders plus one cancelled_vipareeta row carrying its own
    interval."""
    v_in, v_out = vipareeta_span
    lo, hi = max(interval.t_in, v_in), min(interval.t_out, v_out)
    if lo >= hi:  # no overlap: obstruction stands whole
        return [interval]
    out: list[VedhaInterval] = []
    if interval.t_in < lo:
        out.append(_remnant(interval, interval.t_in, lo, "active"))
    cancelled = _remnant(interval, lo, hi, "cancelled_vipareeta")
    cancelled.attenuation = 1.0  # no attenuation without active obstruction
    out.append(cancelled)
    if hi < interval.t_out:
        out.append(_remnant(interval, hi, interval.t_out, "active"))
    return out


def _remnant(src: VedhaInterval, t_in: str, t_out: str, state: str) -> VedhaInterval:
    return VedhaInterval(vi_id=f"{src.vi_id}@{state}:{t_in}",
                         rule_version=src.rule_version,
                         primary_contact_id=src.primary_contact_id,
                         obstructor_body=src.obstructor_body,
                         vedha_kind=src.vedha_kind, t_in=t_in, t_out=t_out,
                         state=state, exception=src.exception,
                         independence_group=src.independence_group,
                         source_ref=src.source_ref, provenance=src.provenance,
                         operator_role=src.operator_role,
                         attenuation=src.attenuation, carved_from=src.vi_id)


def attenuation_at(t: str, intervals: list[VedhaInterval] | None,
                   overlay_coverage: dict | None = None) -> dict:
    """Vedha qualifier at t. Absent overlay coverage ⇒ `unavailable` with a
    coverage object, NEVER 1.0 (§5.2 inv 4). Inactive/cancelled rows report
    their state and factor exactly 1.0; an active row applies its row's
    attenuation (< 1.0)."""
    if intervals is None:
        return {"state": "unavailable",
                "factor": None,
                "coverage": overlay_coverage
                or {"overlay": "vedha", "computed": False}}
    covering = [iv for iv in intervals if iv.covers(t)]
    active = [iv for iv in covering if iv.state == "active"]
    if not active:
        return {"state": "clean", "factor": 1.0,
                "rows": [{"vi_id": iv.vi_id, "state": iv.state}
                         for iv in covering]}
    # one root attenuates once; duplicates never multiply (independence_group)
    groups = {iv.independence_group or iv.vi_id for iv in active}
    factor = 1.0
    seen = set()
    for iv in active:
        g = iv.independence_group or iv.vi_id
        if g in seen:
            continue
        seen.add(g)
        factor *= iv.attenuation
    assert len(seen) == len(groups)
    return {"state": "attenuated", "factor": factor,
            "rows": [{"vi_id": iv.vi_id, "state": iv.state} for iv in active]}


def attenuation_over(primary_span: tuple[str, str],
                     intervals: list[VedhaInterval]) -> list[tuple[tuple[str, str], float]]:
    """The temporal structure of an obstruction over a primary residence,
    preserved as intervals, not flags (N4, O-VI-2): sorted breakpoints split
    the residence into clean (1.0) and attenuated sub-intervals."""
    p_in, p_out = primary_span
    cuts = sorted({p_in, p_out} |
                  {iv.t_in for iv in intervals if p_in < iv.t_in < p_out} |
                  {iv.t_out for iv in intervals if p_in < iv.t_out < p_out})
    out = []
    for a, b in zip(cuts, cuts[1:]):
        mid = a  # half-open: the segment [a, b) is governed by rows at a
        covering = [iv for iv in intervals if iv.covers(mid)]
        active = [iv for iv in covering if iv.state == "active"]
        factor = 1.0
        for iv in active:
            factor *= iv.attenuation
        out.append(((a, b), factor))
    return out
