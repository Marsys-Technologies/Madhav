"""The interim sink of a validated test slice, in a structured form (steward MB-ADDITIONS 4; GRAZE-INTERIM).

In a test slice the certification of the contact geometry REPORTS instead of raising for the stretches the builder cannot yet represent as contacts. Until now
that report was one prose sentence in a substep's notes (which the orchestrator never stores). This module turns the certifier's per-stretch records into ONE
machine-readable record per class, the schema `gochara_interim_sink/1`, which the writer logs as a single `GOCHARA_INTERIM_SINK <json>` line (the job log is
where a substep's output survives) and returns in the notes:

  counts       every reconstructed in-band stretch by class: contact (a ledger contact touches it), graze, unresolved, omission; and, ORTHOGONALLY, how many
               are horizon-clipped, SEAMS (an arc-index station lies inside the stretch) and WRAPS (a ray level of the stretch lies within the orb of the 0/360
               cut, so the band straddles the cut)
  grazes       every graze (the certifier's own record: level, closest approach, instant, peak activity)
  unresolved   every stretch `classify_graze` could not classify, WITH THE REASON (approach_below_minimum, extension_not_settled, crossing_not_proved,
               no_level_in_band): one unresolved stretch blocks the final seal and nobody has counted them over the whole horizon; the measuring build counts them
  omissions    every stretch with an exact crossing and no contact (a proven omission: raised by the certifier whatever the policy)
  seams        every stretch with an arc-index station inside it, with the station instants
  wraps        every stretch whose band straddles the 0/360 cut

Plain `contact` stretches are COUNTED, never listed (thousands per class). Pure functions: no database, no ephemeris, no clock.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Callable, Iterable

SINK_SCHEMA = "gochara_interim_sink/1"
LOG_PREFIX = "GOCHARA_INTERIM_SINK "
CLASSES = ("contact", "graze", "unresolved", "omission", "unclassified")


def band_straddles_the_cut(level_deg: float, orb_deg: float) -> bool:
    """True when the ray level lies within `orb_deg` of the 0/360 cut, i.e. the in-band stretch around it wraps across the cut."""
    lv = float(level_deg) % 360.0
    return min(lv, 360.0 - lv) <= orb_deg + 1e-9


def levels_of(relation: str, target: str, aspect_angles: Iterable[float]) -> list[float]:
    """The ray levels of a point target for a relation (a conjunction has one; an aspect has the body's aspect angles), exactly as `classify_graze` forms them."""
    kind, _, arg = target.partition(":")
    if kind != "point":
        return []
    lam = float(arg) % 360.0
    angles = (0.0,) if relation == "conjunction" else tuple(aspect_angles)
    return [(lam - ang) % 360.0 for ang in angles]


def build_record(*, event_class: str, generation: str, horizon: tuple[datetime, datetime], stretches: list[dict], grazes: list[dict],
                 stations_in: Callable[[str, datetime, datetime], list[str]], levels_for: Callable[[str, str, str], list[float]],
                 orb_for: Callable[[str], float]) -> dict:
    """One class's structured record from the certifier's per-stretch records.

    `stations_in(body, t0, t1)` -> the arc-index station instants (ISO) of `body` inside [t0, t1); `levels_for(body, relation, target)` -> the ray levels;
    `orb_for(relation)` -> the point orb in degrees. Deterministic: lists are sorted by (body, relation, target, interval start)."""
    counts = {c: 0 for c in CLASSES}
    out = {"unresolved": [], "omissions": [], "seams": [], "wraps": []}
    clipped = seam_n = wrap_n = 0
    for rec in sorted(stretches, key=lambda r: (r["body"], r["relation"], r["target"], r["interval"][0])):
        cls = rec["class"] if rec["class"] in CLASSES else "unclassified"
        counts[cls] += 1
        t0, t1 = (datetime.fromisoformat(x) for x in rec["interval"])
        if rec.get("clipped_at_horizon"):
            clipped += 1
        stations = stations_in(rec["body"], t0, t1)
        if stations:
            seam_n += 1
            out["seams"].append({**{k: rec[k] for k in ("body", "relation", "target", "interval", "class")}, "stations": stations})
        orb = orb_for(rec["relation"])
        if any(band_straddles_the_cut(lv, orb) for lv in levels_for(rec["body"], rec["relation"], rec["target"])):
            wrap_n += 1
            out["wraps"].append({k: rec[k] for k in ("body", "relation", "target", "interval", "class")})
        if cls == "unresolved":
            out["unresolved"].append({k: rec[k] for k in ("body", "relation", "target", "interval", "reason", "clipped_at_horizon")})
        elif cls == "omission":
            out["omissions"].append({k: rec[k] for k in ("body", "relation", "target", "interval", "reason", "clipped_at_horizon")})
    return {"schema": SINK_SCHEMA, "event_class": event_class, "generation": generation,
            "horizon": [horizon[0].isoformat(), horizon[1].isoformat()],
            "counts": {"stretches": len(stretches), **counts, "horizon_clipped": clipped, "seam": seam_n, "wrap": wrap_n},
            "grazes": sorted(grazes, key=lambda g: (g["body"], g["relation"], g["target"], g["interval"][0])), **out}


def canonical_json(record: dict) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def log_line(record: dict) -> str:
    """The single log line a reader greps for: the prefix, then the canonical JSON of the record."""
    return LOG_PREFIX + canonical_json(record)


def parse_log_line(line: str) -> dict:
    """The record back from a log line (the reader's side); refuses a line that is not a sink line of this schema."""
    i = line.find(LOG_PREFIX)
    if i < 0:
        raise ValueError("not an interim-sink log line")
    record = json.loads(line[i + len(LOG_PREFIX):])
    if record.get("schema") != SINK_SCHEMA:
        raise ValueError(f"interim-sink schema {record.get('schema')!r} is not {SINK_SCHEMA!r}")
    return record


__all__ = ["CLASSES", "LOG_PREFIX", "SINK_SCHEMA", "band_straddles_the_cut", "build_record", "canonical_json", "levels_of", "log_line", "parse_log_line"]
