"""STRETCH_SINK/1: the structured, per-stretch record of a measuring build (MEASURING_BUILD_CONTRACT MB-2; steward MB-CONTRACT-RULINGS).

Under a validated test slice the certification of the contact geometry reconstructs EVERY in-band stretch of every obligation from the ephemeris. This module turns
those per-stretch results (`contact_certify` hands them over, one dict per stretch, in `t_in` order with a 1-based `stretch_ordinal`) into ONE JSON record per
noteworthy fact, each with a stable `record_id`, and one per-class summary with a digest. The job log is the carrier (`STRETCH_SINK/1 <json>` lines, then
`STRETCH_SINK_SUMMARY/1 <json>`); nothing is stored in a table.

CLOSED (kind, reason) list:

  near_miss              certified_positive_clearance                       a graze: in band, never reaches the ray level, certified by proof
  unresolved             clearance_below_min_approach | extension_unsettled | no_crossing_unproved
  omission               crossing_detected | unsupported_target             a stretch with no ledger contact: a real crossing the builder did not mint, or a target the
                                                                            graze notion does not cover
  anomaly                no_relevant_level                                  no ray level within the orb of the sampled stretch
  station_seam           arc_index_station_inside_stretch                   an arc-index station lies inside the stretch (the definition behind the real-chart count)
  multi_episode_stretch  two_or_more_ledger_episodes                        two or more ledger episodes inside one reconstructed stretch (a DIFFERENT fact: the two seams
                                                                            are both recorded and neither replaces the other, steward ruling 4(b))
  wrap                   ray_band_contains_wrap_cut                         a ray level within the orb of the 0/360 cut; detail body_wrapped_inside says whether the body
                                                                            itself crossed the cut during the stretch
  horizon_clipped        clipped_at_start | clipped_at_end | clipped_both

A stretch may yield several records; each has its own `record_id` = uuid8 over `stretch_sink/1|kind|body|relation|canonical_target|orb_deg|horizon_lo|horizon_hi|`
`stretch_ordinal` (the 1-based position among the obligation's in-band stretches over the horizon: stable under input order and sub-second jitter; the horizon is in
the bytes because ordinals are horizon-relative). Plain `contact` stretches are COUNTED in the summary, never listed. Pure: no database, no ephemeris, no clock.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Callable

SCHEMA = "stretch_sink/1"
SUMMARY_SCHEMA = "stretch_sink_summary/1"
LOG_PREFIX = "STRETCH_SINK/1 "
SUMMARY_PREFIX = "STRETCH_SINK_SUMMARY/1 "

KIND_REASONS = {
    "near_miss": ("certified_positive_clearance",),
    "unresolved": ("clearance_below_min_approach", "extension_unsettled", "no_crossing_unproved"),
    "omission": ("crossing_detected", "unsupported_target"),
    "anomaly": ("no_relevant_level",),
    "station_seam": ("arc_index_station_inside_stretch",),
    "multi_episode_stretch": ("two_or_more_ledger_episodes",),
    "wrap": ("ray_band_contains_wrap_cut",),
    "horizon_clipped": ("clipped_at_start", "clipped_at_end", "clipped_both"),
}
#: kinds logged at WARNING (a certification finding); the rest are INFO
WARNING_KINDS = ("near_miss", "unresolved", "omission", "anomaly")
CAUSE_KINDS = ("near_miss", "unresolved", "omission", "anomaly")        # the kinds the certifier assigns to a stretch no ledger contact touches


class StretchSinkUnparseable(ValueError):
    """`stretch_sink_unparseable`: a line that is not a record or a summary of this schema."""


def band_straddles_the_cut(level_deg: float, orb_deg: float) -> bool:
    """True when the ray level lies within `orb_deg` of the 0/360 cut, i.e. the in-band stretch around it wraps across the cut."""
    lv = float(level_deg) % 360.0
    return min(lv, 360.0 - lv) <= orb_deg + 1e-9


def levels_of(relation: str, target: str, aspect_angles) -> list[float]:
    """The ray levels of a point target for a relation (a conjunction has one; an aspect has the body's aspect angles), exactly as `classify_graze` forms them."""
    kind, _, arg = target.partition(":")
    if kind != "point":
        return []
    lam = float(arg) % 360.0
    angles = (0.0,) if relation == "conjunction" else tuple(aspect_angles)
    return [(lam - ang) % 360.0 for ang in angles]


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def record_id(kind: str, body: str, relation: str, canonical_target: str, orb_deg: float, horizon: tuple, stretch_ordinal: int) -> str:
    from .substrate import _uuid8_of
    key = f"{SCHEMA}|{kind}|{body}|{relation}|{canonical_target}|{orb_deg}|{horizon[0].isoformat()}|{horizon[1].isoformat()}|{stretch_ordinal}"
    return str(_uuid8_of(key.encode("utf-8")))


def _record(kind, reason, event_class, st, orb, horizon, **over) -> dict:
    rec = {"schema": SCHEMA, "record_id": record_id(kind, st["body"], st["relation"], st["target"], orb, horizon, st["stretch_ordinal"]), "kind": kind,
           "reason": reason, "event_class": event_class, "body": st["body"], "relation": st["relation"], "canonical_target": st["target"], "level_deg": None,
           "orb_deg": orb, "horizon_interval": list(st["interval"]), "full_interval": None, "clipped_by_horizon": list(st.get("clipped_at_horizon") or []),
           "closest_approach_deg": None, "closest_approach_at": None, "peak_activity": None, "episode_count": None, "detail": None}
    assert reason in KIND_REASONS[kind], (kind, reason)
    rec.update(over)
    return rec


def build_records(*, event_class: str, horizon: tuple[datetime, datetime], stretches: list[dict], stations_in: Callable[[str, datetime, datetime], list[str]],
                  levels_for: Callable[[str, str, str], list[float]], orb_for: Callable[[str], float],
                  body_wrapped_inside: Callable[[str, datetime, datetime], bool]) -> list[dict]:
    """The class's STRETCH_SINK/1 records from the certifier's per-stretch results, sorted by (body, relation, target, ordinal, kind, reason).

    `stations_in(body, t0, t1)` -> arc-index station instants inside [t0, t1); `levels_for(body, relation, target)` -> the ray levels; `orb_for(relation)` -> the
    point orb (degrees); `body_wrapped_inside(body, t0, t1)` -> whether the body's own longitude crossed the 0/360 cut during the stretch."""
    out = []
    for st in stretches:
        t0, t1 = (datetime.fromisoformat(x) for x in st["interval"])
        raw_orb = orb_for(st["relation"])                       # None for a relation with no point orb (a span stretch): no wrap notion, orb_deg null
        orb = None if raw_orb is None else float(raw_orb)
        if st["kind"] in CAUSE_KINDS:
            extra = {k: st[k] for k in ("level_deg", "closest_approach_deg", "closest_approach_at", "peak_activity", "full_interval", "detail") if st.get(k) is not None}
            out.append(_record(st["kind"], st["reason"], event_class, st, orb, horizon, episode_count=st.get("episode_count"), **extra))
        stations = stations_in(st["body"], t0, t1)
        if stations:
            out.append(_record("station_seam", "arc_index_station_inside_stretch", event_class, st, orb, horizon, episode_count=st.get("episode_count"),
                               detail={"stations": stations}))
        if (st.get("episode_count") or 0) >= 2:
            out.append(_record("multi_episode_stretch", "two_or_more_ledger_episodes", event_class, st, orb, horizon, episode_count=st["episode_count"]))
        wraps = [] if orb is None else [lv for lv in levels_for(st["body"], st["relation"], st["target"]) if band_straddles_the_cut(lv, orb)]
        if wraps:
            out.append(_record("wrap", "ray_band_contains_wrap_cut", event_class, st, orb, horizon, level_deg=round(wraps[0], 4),
                               episode_count=st.get("episode_count"), detail={"body_wrapped_inside": bool(body_wrapped_inside(st["body"], t0, t1))}))
        clipped = st.get("clipped_at_horizon") or []
        if clipped:
            reason = "clipped_both" if len(clipped) == 2 else f"clipped_at_{clipped[0]}"
            out.append(_record("horizon_clipped", reason, event_class, st, orb, horizon, episode_count=st.get("episode_count")))
    out.sort(key=lambda r: (r["body"], r["relation"], r["canonical_target"], r["horizon_interval"][0], r["kind"], r["reason"]))
    return out


def summary(event_class: str, generation: str, horizon: tuple, records: list[dict], stretches: list[dict]) -> dict:
    """The per-class line: counts by `kind/reason`, the number of stretches (every in-band stretch, plain contacts included) and the digest of the sorted record ids."""
    counts: dict[str, int] = {}
    for r in records:
        key = f"{r['kind']}/{r['reason']}"
        counts[key] = counts.get(key, 0) + 1
    ids = sorted(r["record_id"] for r in records)
    return {"schema": SUMMARY_SCHEMA, "event_class": event_class, "generation": generation, "horizon": [horizon[0].isoformat(), horizon[1].isoformat()],
            "stretches": len(stretches), "contact_stretches": sum(1 for s in stretches if s["kind"] == "contact"), "records": len(records),
            "counts_by_kind_reason": dict(sorted(counts.items())), "record_ids_digest": hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()}


def log_line(record: dict) -> str:
    return LOG_PREFIX + canonical_json(record)


def summary_line(summary_record: dict) -> str:
    return SUMMARY_PREFIX + canonical_json(summary_record)


def parse_line(line: str) -> dict:
    """The record or summary back from a log line (the reader's side). Refused by name when the line is not this schema (`stretch_sink_unparseable`)."""
    for prefix, schema in ((SUMMARY_PREFIX, SUMMARY_SCHEMA), (LOG_PREFIX, SCHEMA)):
        i = line.find(prefix)
        if i >= 0:
            try:
                rec = json.loads(line[i + len(prefix):])
            except ValueError as exc:
                raise StretchSinkUnparseable(f"stretch_sink_unparseable: {exc}") from exc
            if rec.get("schema") != schema:
                raise StretchSinkUnparseable(f"stretch_sink_unparseable: schema {rec.get('schema')!r} is not {schema!r}")
            return rec
    raise StretchSinkUnparseable("stretch_sink_unparseable: not a STRETCH_SINK/1 line")


def check_summary(summary_record: dict, records: list[dict]) -> None:
    """`stretch_sink_summary_digest_mismatch`: the records of a class must reproduce the summary's counts and digest."""
    ids = sorted(r["record_id"] for r in records)
    if hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest() != summary_record["record_ids_digest"] or len(records) != summary_record["records"]:
        raise StretchSinkUnparseable("stretch_sink_summary_digest_mismatch: the records do not reproduce the summary")


__all__ = ["CAUSE_KINDS", "KIND_REASONS", "LOG_PREFIX", "SCHEMA", "SUMMARY_PREFIX", "SUMMARY_SCHEMA", "StretchSinkUnparseable", "WARNING_KINDS", "band_straddles_the_cut",
           "build_records", "canonical_json", "check_summary", "levels_of", "log_line", "parse_line", "record_id", "summary", "summary_line"]
