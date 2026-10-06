"""STRETCH_SINK/1: the structured, per-stretch record of a measuring build (MEASURING_BUILD_CONTRACT v1.0 MB-2.2 to MB-2.4).

Under a validated test slice the certification of the contact geometry reconstructs EVERY in-band stretch of every obligation from the ephemeris. This module turns
those per-stretch results (`contact_certify` hands them over, one dict per stretch, in `t_in` order with a 1-based `stretch_ordinal`) into ONE JSON record per
noteworthy fact, each with a stable `record_id`, and one per-class summary with a digest. The job log is the carrier (`STRETCH_SINK/1 <json>` lines, then
`STRETCH_SINK_SUMMARY/1 <json>`); nothing is stored in a table.

THE RECORD (MB-2.2; the schema is the contract's, field for field, nothing added and nothing missing):
  {schema, record_id, kind, reason, detail, event_class, body, relation, canonical_target, level_deg, orb_deg, horizon_interval, full_interval, clipped_by_horizon,
   closest_approach_deg, closest_approach_at, peak_activity, episode_count, station_at, stretch_ordinal}

THE RECORD_ID RECIPE (MB-2.2, implemented from the contract's text, never from this repository's other code): the canonical string is
  "stretch_sink/1|<kind>|<body>|<relation>|<canonical_target>|<orb>|<lo>|<hi>|<ordinal>"
with `orb` = the point orb formatted `%.3f` (`1.000`), `0.000` for a residence obligation (no point orb); `lo`, `hi` = the inventory horizon bounds as
`YYYY-MM-DDTHH:MM:SS+00:00`; `ordinal` = the decimal `stretch_ordinal`. digest = sha256(bytes)[:16]; byte 6 <- (b6 & 0x0F) | 0x80; byte 8 <- (b8 & 0x3F) | 0x80;
record_id = uuid.UUID(bytes=digest). `stretch_ordinal` is 1 + the number of the obligation's in-band intervals over the horizon starting strictly earlier than the
stretch's `horizon_interval`; an INVENTED ledger contact has no reconstructed stretch, so its rank is computed against the reconstructed ones the same way, and the
obligation-level pairing anomaly has ordinal 1.

CLOSED (kind, reason) TABLE (MB-2.3):

  near_miss              certified_positive_clearance
  unresolved             clearance_below_min_approach | no_crossing_unproved | extension_unsettled   (detail of the last: ambiguous_extension | exceeds_1500_days)
  omission               crossing_detected | unsupported_target
  invented               ledger_contact_not_reconstructed
  anomaly                no_relevant_level | boundary_pairing_mismatch      (detail of the last: the two counts)
  station_seam           arc_index_station_inside      REQUIRES at least one overlapping ledger contact; carries `station_at` and `full_interval`
  multi_episode_stretch  multiple_ledger_episodes      `episode_count` >= 2
  wrap                   ray_band_contains_wrap_cut    detail body_wrapped_inside (bool)
  horizon_clipped        clipped_at_start | clipped_at_end | clipped_both

A stretch may yield several records; each has its own `record_id`. Plain `contact` stretches are COUNTED in the summary, never listed. A word outside the table is
refused `unknown_kind_or_reason`. Pure: no database, no ephemeris, no clock."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Callable

SCHEMA = "stretch_sink/1"
SUMMARY_SCHEMA = "stretch_sink_summary/1"
LOG_PREFIX = "STRETCH_SINK/1 "
SUMMARY_PREFIX = "STRETCH_SINK_SUMMARY/1 "

KIND_REASONS = {
    "near_miss": ("certified_positive_clearance",),
    "unresolved": ("clearance_below_min_approach", "no_crossing_unproved", "extension_unsettled"),
    "omission": ("crossing_detected", "unsupported_target"),
    "invented": ("ledger_contact_not_reconstructed",),
    "anomaly": ("no_relevant_level", "boundary_pairing_mismatch"),
    "station_seam": ("arc_index_station_inside",),
    "multi_episode_stretch": ("multiple_ledger_episodes",),
    "wrap": ("ray_band_contains_wrap_cut",),
    "horizon_clipped": ("clipped_at_start", "clipped_at_end", "clipped_both"),
}
#: the closed value set of `detail` where the table closes it
EXTENSION_DETAILS = ("ambiguous_extension", "exceeds_1500_days")
#: kinds logged at WARNING (a certification finding); the rest are INFO (MB-2.4)
WARNING_KINDS = ("near_miss", "unresolved", "omission", "invented", "anomaly")
CAUSE_KINDS = ("near_miss", "unresolved", "omission", "invented", "anomaly")        # the kinds the certifier assigns to a stretch (or a ledger contact) itself
RECORD_FIELDS = ("schema", "record_id", "kind", "reason", "detail", "event_class", "body", "relation", "canonical_target", "level_deg", "orb_deg", "horizon_interval",
                 "full_interval", "clipped_by_horizon", "closest_approach_deg", "closest_approach_at", "peak_activity", "episode_count", "station_at", "stretch_ordinal")


class StretchSinkUnparseable(ValueError):
    """`stretch_sink_unparseable`: a line that is not a record or a summary of this schema."""


class UnknownKindOrReason(StretchSinkUnparseable):
    """`unknown_kind_or_reason`: a (kind, reason) pair outside the closed table."""


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


def _instant(t: datetime) -> str:
    """`YYYY-MM-DDTHH:MM:SS+00:00`, the contract's format for the horizon bounds in the id."""
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def record_id(kind: str, body: str, relation: str, canonical_target: str, orb_deg, horizon: tuple, stretch_ordinal: int) -> str:
    """The contract's recipe (see the module docstring), written out here from its text. `orb_deg` None = a residence obligation, `0.000`."""
    orb = "0.000" if orb_deg is None else "%.3f" % float(orb_deg)
    canonical = "|".join(("stretch_sink/1", kind, body, relation, canonical_target, orb, _instant(horizon[0]), _instant(horizon[1]), str(int(stretch_ordinal))))
    digest = bytearray(hashlib.sha256(canonical.encode("utf-8")).digest()[:16])
    digest[6] = (digest[6] & 0x0F) | 0x80
    digest[8] = (digest[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(digest)))


def _record(kind, reason, event_class, st, orb, horizon, **over) -> dict:
    if reason not in KIND_REASONS.get(kind, ()):
        raise UnknownKindOrReason(f"unknown_kind_or_reason: ({kind!r}, {reason!r}) is not in the closed table")
    rec = {"schema": SCHEMA, "record_id": record_id(kind, st["body"], st["relation"], st["target"], orb, horizon, st["stretch_ordinal"]), "kind": kind,
           "reason": reason, "detail": None, "event_class": event_class, "body": st["body"], "relation": st["relation"], "canonical_target": st["target"],
           "level_deg": None, "orb_deg": orb, "horizon_interval": list(st["interval"]), "full_interval": None,
           "clipped_by_horizon": list(st.get("clipped_at_horizon") or []), "closest_approach_deg": None, "closest_approach_at": None, "peak_activity": None,
           "episode_count": st.get("episode_count"), "station_at": None, "stretch_ordinal": st["stretch_ordinal"]}
    rec.update(over)
    return rec


def build_records(*, event_class: str, horizon: tuple[datetime, datetime], stretches: list[dict], stations_in: Callable[[str, datetime, datetime], list[str]],
                  levels_for: Callable[[str, str, str], list[float]], orb_for: Callable[[str], float],
                  body_wrapped_inside: Callable[[str, datetime, datetime], bool]) -> list[dict]:
    """The class's STRETCH_SINK/1 records from the certifier's per-stretch results, sorted by (body, relation, target, t_in, kind, reason).

    `stations_in(body, t0, t1)` -> arc-index station instants (ISO) inside [t0, t1); `levels_for(body, relation, target)` -> the ray levels; `orb_for(relation)` -> the
    point orb (degrees; None for a relation with none); `body_wrapped_inside(body, t0, t1)` -> whether the body's own longitude crossed the 0/360 cut during the
    stretch. A stretch dict with `derive` False (an invented ledger contact, the obligation-level pairing anomaly) yields its own record only: it is not a
    reconstructed stretch, so a station, a wrap or a clip is no statement about it."""
    out = []
    for st in stretches:
        t0, t1 = (datetime.fromisoformat(x) for x in st["interval"])
        raw_orb = orb_for(st["relation"])                       # None for a relation with no point orb (a span stretch): no wrap notion, orb_deg null
        orb = None if raw_orb is None else float(raw_orb)
        if st["kind"] in CAUSE_KINDS:
            extra = {k: st[k] for k in ("level_deg", "closest_approach_deg", "closest_approach_at", "peak_activity", "full_interval", "detail") if st.get(k) is not None}
            out.append(_record(st["kind"], st["reason"], event_class, st, orb, horizon, **extra))
        if not st.get("derive", True):
            continue
        episodes = st.get("episode_count") or 0
        stations = stations_in(st["body"], t0, t1) if episodes >= 1 else []                 # a seam REQUIRES at least one overlapping ledger contact (MB-2.3)
        if stations:
            out.append(_record("station_seam", "arc_index_station_inside", event_class, st, orb, horizon, station_at=sorted(stations)[0],
                               full_interval=list(st.get("full_interval") or st["interval"])))
        if episodes >= 2:
            out.append(_record("multi_episode_stretch", "multiple_ledger_episodes", event_class, st, orb, horizon))
        wraps = [] if orb is None else [lv for lv in levels_for(st["body"], st["relation"], st["target"]) if band_straddles_the_cut(lv, orb)]
        if wraps:
            out.append(_record("wrap", "ray_band_contains_wrap_cut", event_class, st, orb, horizon, level_deg=round(wraps[0], 4),
                               detail={"body_wrapped_inside": bool(body_wrapped_inside(st["body"], t0, t1))}))
        clipped = st.get("clipped_at_horizon") or []
        if clipped:
            reason = "clipped_both" if len(clipped) == 2 else f"clipped_at_{clipped[0]}"
            out.append(_record("horizon_clipped", reason, event_class, st, orb, horizon))
    out.sort(key=lambda r: (r["body"], r["relation"], r["canonical_target"], r["horizon_interval"][0], r["kind"], r["reason"]))
    return out


def summary(event_class: str, generation: str, horizon: tuple, records: list[dict], stretches: list[dict]) -> dict:
    """The per-class line: counts by `kind/reason`, the number of stretches (every in-band stretch, plain contacts included) and the digest of the sorted record ids
    (the contract's `{event_class, counts_by_kind_reason, record_ids_digest}` plus the class's totals)."""
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


def _check_record(rec: dict) -> None:
    """A record of this schema has exactly the contract's fields and a (kind, reason) inside the closed table."""
    missing = [f for f in RECORD_FIELDS if f not in rec]
    extra = sorted(set(rec) - set(RECORD_FIELDS))
    if missing or extra:
        raise StretchSinkUnparseable(f"stretch_sink_unparseable: record fields missing {missing}, unexpected {extra}")
    if rec["reason"] not in KIND_REASONS.get(rec["kind"], ()):
        raise UnknownKindOrReason(f"unknown_kind_or_reason: ({rec['kind']!r}, {rec['reason']!r}) is not in the closed table")


def parse_line(line: str) -> dict:
    """The record or summary back from a log line (the reader's side). Refused by name when the line is not this schema (`stretch_sink_unparseable`), is a record
    with the wrong fields, or names a (kind, reason) outside the table (`unknown_kind_or_reason`)."""
    for prefix, schema in ((SUMMARY_PREFIX, SUMMARY_SCHEMA), (LOG_PREFIX, SCHEMA)):
        i = line.find(prefix)
        if i >= 0:
            try:
                rec = json.loads(line[i + len(prefix):])
            except ValueError as exc:
                raise StretchSinkUnparseable(f"stretch_sink_unparseable: {exc}") from exc
            if not isinstance(rec, dict) or rec.get("schema") != schema:
                raise StretchSinkUnparseable(f"stretch_sink_unparseable: schema {rec.get('schema') if isinstance(rec, dict) else rec!r} is not {schema!r}")
            if schema == SCHEMA:
                _check_record(rec)
            return rec
    raise StretchSinkUnparseable("stretch_sink_unparseable: not a STRETCH_SINK/1 line")


def check_summary(summary_record: dict, records: list[dict]) -> None:
    """`stretch_sink_summary_digest_mismatch`: the records of a class must reproduce the summary's counts and digest."""
    ids = sorted(r["record_id"] for r in records)
    counts: dict[str, int] = {}
    for r in records:
        counts[f"{r['kind']}/{r['reason']}"] = counts.get(f"{r['kind']}/{r['reason']}", 0) + 1
    if (hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest() != summary_record["record_ids_digest"] or len(records) != summary_record["records"]
            or dict(sorted(counts.items())) != summary_record["counts_by_kind_reason"]):
        raise StretchSinkUnparseable("stretch_sink_summary_digest_mismatch: the records do not reproduce the summary")


__all__ = ["CAUSE_KINDS", "EXTENSION_DETAILS", "KIND_REASONS", "LOG_PREFIX", "RECORD_FIELDS", "SCHEMA", "SUMMARY_PREFIX", "SUMMARY_SCHEMA", "StretchSinkUnparseable",
           "UnknownKindOrReason", "WARNING_KINDS", "band_straddles_the_cut", "build_records", "canonical_json", "check_summary", "levels_of", "log_line", "parse_line",
           "record_id", "summary", "summary_line"]
