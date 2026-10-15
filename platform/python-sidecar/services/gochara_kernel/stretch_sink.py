"""Structured measuring-build evidence (MEASURING_BUILD_CONTRACT MB-2).

This is a pure log codec: it reports certifier findings and never writes rows or
confers verification. Station instants and geometry come from supplied sources.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

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
EXTENSION_DETAILS = ("ambiguous_extension", "exceeds_1500_days")
SEAM_FULL_INTERVAL_DETAILS = EXTENSION_DETAILS + ("not_applicable",)
WARNING_KINDS = ("near_miss", "unresolved", "omission", "invented", "anomaly")
CAUSE_KINDS = WARNING_KINDS
RECORD_FIELDS = ("schema", "record_id", "kind", "reason", "detail", "event_class", "body", "relation", "canonical_target", "level_deg", "orb_deg",
                 "horizon_interval", "full_interval", "clipped_by_horizon", "closest_approach_deg", "closest_approach_at", "peak_activity", "episode_count",
                 "station_at", "stretch_ordinal")


class StretchSinkUnparseable(ValueError):
    """The log cannot be read as measuring evidence."""


class UnknownKindOrReason(StretchSinkUnparseable):
    """A finding is outside the contract's closed vocabulary."""


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _instant(value):
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def record_id(kind, body, relation, canonical_target, orb_deg, horizon, stretch_ordinal):
    orb = "0.000" if orb_deg is None else "%.3f" % float(orb_deg)
    identity = "|".join((SCHEMA, kind, body, relation, canonical_target, orb, _instant(horizon[0]), _instant(horizon[1]), str(int(stretch_ordinal))))
    digest = bytearray(hashlib.sha256(identity.encode("utf-8")).digest()[:16])
    digest[6] = (digest[6] & 0x0F) | 0x80
    digest[8] = (digest[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(digest)))


def band_straddles_the_cut(level_deg, orb_deg):
    lv = float(level_deg) % 360.0
    return min(lv, 360.0 - lv) <= orb_deg + 1e-9


def levels_of(relation, target, aspect_angles):
    kind, _, value = target.partition(":")
    if kind != "point":
        return []
    angles = (0.0,) if relation == "conjunction" else aspect_angles
    return [(float(value) - angle) % 360.0 for angle in angles]


def _record(kind, reason, event_class, st, orb, horizon, **extra):
    rec = dict.fromkeys(RECORD_FIELDS)
    rec.update(schema=SCHEMA, record_id=record_id(kind, st["body"], st["relation"], st["target"], orb, horizon, st["stretch_ordinal"]),
               kind=kind, reason=reason, event_class=event_class, body=st["body"], relation=st["relation"], canonical_target=st["target"], orb_deg=orb,
               horizon_interval=list(st["interval"]), clipped_by_horizon=list(st.get("clipped_at_horizon") or []),
               episode_count=st.get("episode_count"), stretch_ordinal=st["stretch_ordinal"])
    rec.update(extra)
    _check_record(rec)
    return rec


def build_records(*, event_class, horizon, stretches, stations_in, levels_for, orb_for, body_wrapped_inside):
    records = []
    for st in stretches:
        t0, t1 = (datetime.fromisoformat(value) for value in st["interval"])
        raw_orb = orb_for(st["relation"])
        orb = None if raw_orb is None else float(raw_orb)
        if st["kind"] in CAUSE_KINDS:
            details = {key: st[key] for key in ("detail", "full_interval", "level_deg", "closest_approach_deg", "closest_approach_at", "peak_activity")
                       if st.get(key) is not None}
            records.append(_record(st["kind"], st["reason"], event_class, st, orb, horizon, **details))
        if not st.get("derive", True):
            continue
        episodes = st.get("episode_count") or 0
        stations = stations_in(st["body"], t0, t1) if episodes >= 1 else []
        if stations:
            # `full_interval` is the stretch's extent, never a clipped horizon substitute.
            records.append(_record("station_seam", "arc_index_station_inside", event_class, st, orb, horizon,
                                   station_at=sorted(stations)[0], full_interval=st.get("stretch_full"), detail=st.get("stretch_full_detail")))
        if episodes >= 2:
            records.append(_record("multi_episode_stretch", "multiple_ledger_episodes", event_class, st, orb, horizon))
        wraps = [] if orb is None else [level for level in levels_for(st["body"], st["relation"], st["target"]) if band_straddles_the_cut(level, orb)]
        if wraps:
            records.append(_record("wrap", "ray_band_contains_wrap_cut", event_class, st, orb, horizon, level_deg=round(wraps[0], 4),
                                   detail={"body_wrapped_inside": bool(body_wrapped_inside(st["body"], t0, t1))}))
        clipped = st.get("clipped_at_horizon") or []
        if clipped:
            reason = "clipped_both" if len(clipped) == 2 else f"clipped_at_{clipped[0]}"
            records.append(_record("horizon_clipped", reason, event_class, st, orb, horizon))
    return sorted(records, key=lambda rec: (rec["body"], rec["relation"], rec["canonical_target"], rec["horizon_interval"][0], rec["kind"], rec["reason"]))


def _record_totals(records):
    counts = {}
    for rec in records:
        key = f"{rec['kind']}/{rec['reason']}"
        counts[key] = counts.get(key, 0) + 1
    ids = sorted(rec["record_id"] for rec in records)
    return dict(sorted(counts.items())), hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()


def summary(event_class, generation, horizon, records, stretches):
    counts, digest = _record_totals(records)
    return {"schema": SUMMARY_SCHEMA, "event_class": event_class, "generation": generation, "horizon": [value.isoformat() for value in horizon],
            "stretches": len(stretches), "contact_stretches": sum(st["kind"] == "contact" for st in stretches), "records": len(records),
            "counts_by_kind_reason": counts, "record_ids_digest": digest}


def log_line(record):
    return LOG_PREFIX + canonical_json(record)


def summary_line(record):
    return SUMMARY_PREFIX + canonical_json(record)


def _check_record(rec):
    missing, extra = sorted(set(RECORD_FIELDS) - set(rec)), sorted(set(rec) - set(RECORD_FIELDS))
    if missing or extra:
        raise StretchSinkUnparseable(f"stretch_sink_unparseable: record fields missing {missing}, unexpected {extra}")
    if rec["reason"] not in KIND_REASONS.get(rec["kind"], ()):
        raise UnknownKindOrReason(f"unknown_kind_or_reason: {rec['kind']!r}/{rec['reason']!r}")


def parse_line(line):
    for prefix, schema in ((SUMMARY_PREFIX, SUMMARY_SCHEMA), (LOG_PREFIX, SCHEMA)):
        position = line.find(prefix)
        if position < 0:
            continue
        try:
            record = json.loads(line[position + len(prefix):])
        except ValueError as exc:
            raise StretchSinkUnparseable(f"stretch_sink_unparseable: {exc}") from exc
        if not isinstance(record, dict) or record.get("schema") != schema:
            raise StretchSinkUnparseable(f"stretch_sink_unparseable: expected {schema}")
        if schema == SCHEMA:
            _check_record(record)
        return record
    raise StretchSinkUnparseable("stretch_sink_unparseable: no measuring evidence prefix")


def check_summary(summary_record, records):
    counts, digest = _record_totals(records)
    if (counts != summary_record["counts_by_kind_reason"] or digest != summary_record["record_ids_digest"] or len(records) != summary_record["records"]):
        raise StretchSinkUnparseable("stretch_sink_summary_digest_mismatch: records do not reproduce summary")
