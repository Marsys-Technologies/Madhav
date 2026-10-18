"""Read-only, independent measurements for the unsealed all_classes_full build.

Specification: MEASURING_BUILD_CONTRACT_v1_0.md, amendment v1.0.1 and
MB-1/MB-5/MB-6. This module imports no builder rules. Its horizon is checked
against ruled scope and independent chart/run inputs, or re-derived from legacy
captured life-event rows; it never recomputes L1 chart facts.

Build shares use UTC half-open days; scored shares use IST inclusive dates
(1998-01-01 through 2026-04-17). P4 intersects the agents' instant unions
before either calendar is applied. Near-miss counts are only a tally of
supplied observations, never an independent recount or input to shares.
Seam, wrap, graze, stretch and golden-capture verification belong to their
separate measuring components. Full MB-6 acceptance is measuring_acceptance;
read_measuring_acceptance is its read-only caller (J-3b / verifier B). Marker digest integrity is unknown:
only its syntax is checked here, not the steward's stamp proof.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
import json
import math
import re
from statistics import median

SUBSTRATE_DOMAIN_START = date(1998, 1, 1)
SUBSTRATE_DOMAIN_END = date(2085, 1, 1)
# MB-3.3 enumerates the 18 H classes and MB-6 the other eight. This census is
# deliberately independent of the writer's inventory/registry implementation.
EXCLUDED_EIGHT = frozenset({
    "achievement_recognition", "business_launch", "financial_deception",
    "foreign_settlement", "parental_event", "property_acquisition",
    "psychological_arc", "spiritual_turn",
})
SCORED_CLASSES = EXCLUDED_EIGHT | frozenset({
    "bereavement", "career_advancement", "career_change", "career_entry",
    "career_setback", "childbirth", "chronic_onset", "education_milestone",
    "exam_outcome", "illness_acute", "major_gain", "major_loss", "marriage",
    "relocation", "romantic_start", "separation", "surgery", "travel_event",
})
ALLOWED_RULE_VERSIONS = frozenset({"1.0.0"})
FAST_AGENTS = frozenset({"sun", "moon", "mars", "mercury", "venus"})
SLOW_AGENTS = frozenset({"jupiter", "saturn", "rahu", "ketu"})
ALL_AGENTS = FAST_AGENTS | SLOW_AGENTS
P4_AGENTS = frozenset({"jupiter", "saturn"})
PATHS = ("P1", "P2", "P3", "P4")
VIA_PATHS = {"base": PATHS, "karakatva": ("P1",), "dvi": ("P4",), "kb": ("P3", "P4")}
MEASURING_SCOPE = "test_slice"
MEASURING_RUN = "all_classes_full"
RULED_MEASURING_HORIZON = (date(1998, 1, 1), date(2084, 2, 5))
MARKER_SCHEMA = "gochara_v5_test_slice/1"
MARKER_DIGEST_NOT_CHECKED = "not_checked_by_verifier_steward_stamp_proof"
IST = timezone(timedelta(hours=5, minutes=30))
_SCORER_H0, _SCORER_H1 = date(1998, 1, 1), date(2026, 4, 17)
SCORED_DAYS = 10334


class MeasuringReportError(ValueError):
    """Named refusal of a measurement's inputs."""


def _utc(value):
    if not isinstance(value, datetime):
        raise MeasuringReportError(f"instant_unreadable: {value!r}")
    if value.utcoffset() is None:
        raise MeasuringReportError("naive_datetime")
    return value.astimezone(timezone.utc)


def as_utc_date(value, *, what="bound"):
    if isinstance(value, str):
        try:
            value = date.fromisoformat(value) if len(value) == 10 else datetime.fromisoformat(value)
        except ValueError:
            raise MeasuringReportError(f"horizon_bound_unreadable: {what}") from None
    if isinstance(value, datetime):
        value = _utc(value)
        if value.time() != time():
            raise MeasuringReportError(f"horizon_bound_not_midnight: {what}")
        return value.date()
    if isinstance(value, date):
        return value
    raise MeasuringReportError(f"horizon_bound_unreadable: {what}")


def birth_date_of(value):
    if isinstance(value, dict):
        try:
            # Birth is a civil date in its own offset, not its UTC date.
            return datetime.fromisoformat(value["datetime_iso"]).date()
        except (KeyError, TypeError, ValueError):
            raise MeasuringReportError("birth_params_unreadable") from None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise MeasuringReportError("birth_params_unreadable")


def is_birth_row(row):
    return row.get("domain") == "other/birth"


def _event_date(value):
    if value is None:
        raise MeasuringReportError("lel_date_missing")
    return as_utc_date(value, what="event_date")


def fully_dated_events(lel_rows, *, birth_date):
    """Conjunction of exact confidence, dated provenance.lel_id and equal date.

    Missing IDs are reported before filtering confidence. The domain birth
    row is set aside; event_id is never substituted for a provenance ID.
    All exclusions are counted once and complete reporting is order-stable.
    """
    rows = list(lel_rows)
    birth_date = birth_date_of(birth_date)
    births = [r for r in rows if is_birth_row(r)]
    if rows and (len(births) != 1 or _event_date(births[0].get("event_date")) != birth_date):
        raise MeasuringReportError("lel_birth_row_unidentifiable")
    result = {"dates": [], "excluded": 0, "birth_row": births[0] if births else None,
              "rows_without_lel_id": [], "flag_exact_but_id_undated": [], "chosen": None}
    admitted = []
    ordered = sorted(rows, key=lambda r: (str(r.get("event_date") or ""), str(r.get("event_id") or "")))
    for row in ordered:
        if is_birth_row(row):
            continue
        confidence, shape = row.get("date_confidence"), row.get("shape")
        if confidence not in {"exact", "month_known", "year_only"}:
            raise MeasuringReportError("lel_date_confidence_unknown")
        if shape not in {"point", "interval", "chain"}:
            raise MeasuringReportError("lel_shape_unknown")
        raw_date = row.get("event_date")
        when = _event_date(raw_date) if raw_date is not None else None
        provenance = row.get("provenance")
        lel_id = provenance.get("lel_id") if isinstance(provenance, dict) else None
        report = {"event_id": row.get("event_id"), "event_date": when.isoformat() if when else None}
        if not lel_id:
            result["rows_without_lel_id"].append(report)
        if confidence != "exact":
            result["excluded"] += 1
            continue
        if not isinstance(when, date):
            raise MeasuringReportError("lel_date_missing")
        match = re.fullmatch(r"EVT\.(\d{4})\.(\d{2})\.(\d{2})\.\d{2}", lel_id) if isinstance(lel_id, str) else None
        try:
            id_date = date(*map(int, match.groups())) if match else None
        except ValueError:
            id_date = None
        if id_date != when:
            result["excluded"] += 1
            if lel_id:
                result["flag_exact_but_id_undated"].append({**report, "lel_id": lel_id})
            continue
        admitted.append(row)
    admitted.sort(key=lambda r: (_event_date(r["event_date"]), str(r.get("event_id") or "")))
    result["dates"] = [_event_date(r["event_date"]) for r in admitted]
    result["chosen"] = admitted[0] if admitted else None

    def jan_first(values):
        return date(min(values).year, 1, 1) if values else None

    by_id = {r.get("event_id"): r for r in rows}
    interval_dates, chain_dates = [], []
    for row in admitted:
        when = _event_date(row["event_date"])
        interval_dates.append(_event_date(row["interval_start"]) if row["shape"] == "interval" and row.get("interval_start") else when)
        root, seen = row, set()
        while root.get("shape") == "chain":
            parent = root.get("chain_parent_event_id")
            if parent in seen or parent not in by_id:
                raise MeasuringReportError("lel_chain_unresolvable")
            seen.add(parent)
            root = by_id[parent]
        chain_dates.append(_event_date(root["event_date"]))
    readings = {"event_date": jan_first(result["dates"]), "interval_start": jan_first(interval_dates), "chain_root": jan_first(chain_dates)}
    if len(set(readings.values())) > 1:
        raise MeasuringReportError("lel_shape_reading_sensitive")
    result["readings"] = readings
    return result


def horizon_problem(horizon, *, birth_date=None):
    start, end = horizon
    if start >= end:
        return "horizon_empty"
    if birth_date is not None and start < birth_date:
        return "horizon_start_before_birth"
    if start < SUBSTRATE_DOMAIN_START:
        return "horizon_start_before_substrate_domain"
    if end > SUBSTRATE_DOMAIN_END:
        return "horizon_outside_substrate_domain"
    return None


def derive_chart_horizon_detail(birth_date, lel_rows, build_date):
    birth = birth_date_of(birth_date)
    if not isinstance(build_date, date):
        raise MeasuringReportError("build_date_unreadable")
    today = _utc(build_date).date() if isinstance(build_date, datetime) else build_date
    try:
        end = birth.replace(year=birth.year + 100)
    except ValueError:
        raise MeasuringReportError("horizon_birth_anniversary_undefined") from None
    rows = list(lel_rows)
    info = fully_dated_events(rows, birth_date=birth)
    if rows and not info["dates"]:
        raise MeasuringReportError("horizon_underivable_log_has_no_dated_event")
    start = date(min(info["dates"]).year, 1, 1) if rows else today
    problem = horizon_problem((start, end), birth_date=birth)
    if problem:
        raise MeasuringReportError(problem)
    if start > today:
        raise MeasuringReportError("horizon_start_in_future")
    return {"start": start, "end": end, "basis": "first_dated_event" if rows else "build_date",
            "excluded_undated": info["excluded"], "readings": info["readings"],
            "rows_without_lel_id": info["rows_without_lel_id"],
            "flag_exact_but_id_undated": info["flag_exact_but_id_undated"],
            "chosen": info["chosen"].get("event_id") if info["chosen"] else None}


def derive_chart_horizon(birth_date, lel_rows, build_date):
    detail = derive_chart_horizon_detail(birth_date, lel_rows, build_date)
    return detail["start"], detail["end"], detail["basis"]


@dataclass(frozen=True)
class MeasuringBuildView:
    stored_scope: str | None
    run: str | None
    sealed: bool
    published: bool
    horizon: tuple
    rule_versions: frozenset
    near_miss_rows_stored: int | None
    class_paths_with_rows: frozenset
    marker_classes: frozenset = frozenset()
    marker_schema: str | None = None
    marker_digest: str | None = None
    marker_digest_verified: None = None
    marker_digest_reason: str = MARKER_DIGEST_NOT_CHECKED
    marker_horizon: tuple | None = None
    status: str | None = None
    horizon_basis: dict | None = None
    run_verdict: dict | None = None
    sink_counts: dict | None = None

    @property
    def classes_with_records(self):
        return frozenset(c for c, _ in self.class_paths_with_rows)


def measuring_refusals(view, *, expected_horizon, birth_date=None):
    """Inherited partial checks, NOT MB-6 acceptance; use measuring_acceptance.

    Digest syntax is not integrity. Kept for inherited measurement callers.
    """
    out = []
    checks = [
        (view.stored_scope != MEASURING_SCOPE, "measuring_scope_not_test_slice"),
        (view.run != MEASURING_RUN, "measuring_run_not_all_classes_full"),
        (view.sealed, "measuring_build_sealed"),
        (view.published, "measuring_build_published"),
        (view.status not in (None, "candidate", "published"), "measuring_status_not_candidate"),
        (not view.class_paths_with_rows, "measuring_build_holds_no_rows"),
        (bool(view.rule_versions - ALLOWED_RULE_VERSIONS), "rule_version_not_in_scope"),
        (bool(view.near_miss_rows_stored), "near_miss_rows_stored"),
        (any(c in EXCLUDED_EIGHT and p in ("P1", "P3", "P4") for c, p in view.class_paths_with_rows), "excluded_path_has_rows"),
        (bool(view.classes_with_records - SCORED_CLASSES), "unknown_class_has_rows"),
        (set(view.marker_classes) != SCORED_CLASSES, "class_census_mismatch"),
    ]
    out.extend(code for failed, code in checks if failed)
    try:
        stored = tuple(as_utc_date(v) for v in view.horizon)
        expected = tuple(as_utc_date(v) for v in expected_horizon)
        if stored != expected:
            out.append("horizon_mismatch")
        if problem := horizon_problem(stored, birth_date=birth_date):
            out.append(problem)
        if view.marker_horizon is not None:
            marker = tuple(as_utc_date(v) for v in view.marker_horizon)
            if marker != stored:
                out.append("marker_horizon_mismatch")
    except MeasuringReportError as exc:
        out.append(str(exc))
    if view.marker_horizon is None or view.marker_schema != MARKER_SCHEMA or not view.marker_digest:
        out.append("marker_incomplete")
    elif not isinstance(view.marker_digest, str) or re.fullmatch(r"[0-9a-f]{64}", view.marker_digest) is None:
        out.append("marker_digest_malformed")
    return out


# MB-1.4: these are the captured columns, not a writer's row type.
_BASIS_ROW_FIELDS = frozenset({
    "event_id", "event_date", "category", "event_type", "domain", "provenance_lel_id",
    "provenance_subcategory", "shape", "date_confidence", "interval_start", "interval_end",
    "chain_parent_event_id", "date_tightened_at",
})


def _runtime_refusals(evidence, *, status, stored_scope):
    """MB-4.7 raw R7c states and the log's last index/total, never exit status."""
    if not isinstance(evidence, dict):
        return ["verdict_not_success"]
    out = []
    if evidence.get("run_state") == "failed" and (
            evidence.get("throughput_state") == "lit" or evidence.get("asset_state") == "complete"):
        out.append("asset_lit_under_failed_run")
    index, total = evidence.get("last_substep_index"), evidence.get("planned_substeps")
    if type(index) is not int or type(total) is not int or total <= 0 or index != total:
        out.append("substep_plan_incomplete")
    expected = {"run_state": "completed", "asset_state": "complete", "disposition": "build",
                "throughput_state": "lit", "inventory_classes": 26, "completed_classes": 26}
    states_match = all(type(evidence.get(key)) is type(value) and evidence[key] == value
                       for key, value in expected.items())
    if out or status != "candidate" or stored_scope != MEASURING_SCOPE or not states_match:
        out.insert(0, "verdict_not_success")
    return out


def _horizon_basis_refusals(basis, *, chart_id, birth_date, build_date, expected_horizon):
    """Validate the producer's ruled scope or re-derive a legacy captured basis.

    (I) INTERPRETATION: P03's outcome-free field scope takes precedence
    over the historical outcome-selected scope. Both records are checked
    independently here; a ruled-scope label never bypasses evidence checks.
    """
    required = {"schema", "rule", "chart_id", "birth_date", "build_date", "horizon", "basis",
                "chosen", "birth_row", "fully_dated_readings", "shape_readings",
                "excluded_not_fully_dated", "rows_total", "consumed_rows", "consumed_rows_digest"}
    if not isinstance(basis, dict) or not required <= basis.keys():
        return ["horizon_basis_missing"]
    try:
        if basis["schema"] != "horizon_basis/1" or basis["rule"] not in {"ruling7+ruling13", "ruled_scope+birth_centenary"}:
            raise MeasuringReportError("horizon_basis_invalid: schema_or_rule")
        birth = birth_date_of(birth_date)
        if not isinstance(build_date, date):
            raise MeasuringReportError("build_date_unreadable")
        today = _utc(build_date).date() if isinstance(build_date, datetime) else build_date
        if (basis["chart_id"] != str(chart_id) or not chart_id
                or as_utc_date(basis["birth_date"]) != birth
                or as_utc_date(basis["build_date"]) != today):
            raise MeasuringReportError("horizon_basis_invalid: context_mismatch")
        rows = basis["consumed_rows"]
        if not isinstance(rows, list) or any(not isinstance(r, dict) or not _BASIS_ROW_FIELDS <= r.keys() for r in rows):
            raise MeasuringReportError("horizon_basis_missing")
        if type(basis["rows_total"]) is not int or basis["rows_total"] != len(rows):
            raise MeasuringReportError("horizon_basis_invalid: rows_total")
        ids = [r["event_id"] for r in rows]
        if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
            raise MeasuringReportError("horizon_basis_invalid: event_ids")
        if rows != sorted(rows, key=lambda r: (r["event_date"] or "", r["event_id"])):
            raise MeasuringReportError("horizon_basis_invalid: row_order")
        digest = sha256(json.dumps(rows, sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()
        if basis["consumed_rows_digest"] != digest:
            raise MeasuringReportError("horizon_basis_digest_mismatch")
        if basis["rule"] == "ruled_scope+birth_centenary":
            # The field writer consumes no outcome rows. Verify that claim,
            # then derive its bounds from the independent context and ruling.
            if (basis["basis"] != "ruled_horizon" or rows
                    or type(basis["excluded_not_fully_dated"]) is not int
                    or basis["excluded_not_fully_dated"] != 0
                    or basis["chosen"] is not None or basis["birth_row"] is not None
                    or basis["fully_dated_readings"] != {} or basis["shape_readings"] != {}
                    or basis.get("flag_exact_but_id_undated") != []
                    or basis.get("rows_without_lel_id") != []):
                raise MeasuringReportError("horizon_basis_invalid: ruled_scope")
            try:
                centenary = birth.replace(year=birth.year + 100)
            except ValueError:
                raise MeasuringReportError("horizon_birth_anniversary_undefined") from None
            ruled_bounds = (RULED_MEASURING_HORIZON[0], centenary)
            if problem := horizon_problem(ruled_bounds, birth_date=birth):
                raise MeasuringReportError(problem)
            if ruled_bounds[0] > today:
                raise MeasuringReportError("horizon_start_in_future")
            if (ruled_bounds != tuple(as_utc_date(v) for v in expected_horizon)
                    or ruled_bounds != tuple(as_utc_date(v) for v in basis["horizon"])):
                return ["horizon_mismatch"]
            return []
        # Reconstruct the stored reader shape explicitly; no live log or builder helper.
        events = [{**r, "provenance": {"lel_id": r["provenance_lel_id"],
                                      "subcategory": r["provenance_subcategory"]}} for r in rows]
        detail = derive_chart_horizon_detail(birth, events, today)
        derived = (detail["start"], detail["end"])
        if (derived != tuple(as_utc_date(v) for v in expected_horizon)
                or derived != tuple(as_utc_date(v) for v in basis["horizon"])):
            return ["horizon_mismatch"]
        if basis["basis"] != detail["basis"]:
            raise MeasuringReportError("horizon_basis_invalid: basis")
        if (type(basis["excluded_not_fully_dated"]) is not int
                or basis["excluded_not_fully_dated"] != detail["excluded_undated"]):
            raise MeasuringReportError("horizon_basis_invalid: excluded_count")
        info = fully_dated_events(events, birth_date=birth)
        chosen, br = info["chosen"], info["birth_row"]
        expected_chosen = None if chosen is None else {
            "event_id": chosen["event_id"], "lel_id": chosen["provenance_lel_id"],
            "event_date": as_utc_date(chosen["event_date"]).isoformat(),
            "date_confidence": chosen["date_confidence"], "shape": chosen["shape"]}
        expected_birth = None if br is None else {
            "event_id": br["event_id"], "lel_id": br["provenance_lel_id"],
            "event_date": as_utc_date(br["event_date"]).isoformat(), "domain": br["domain"],
            "provenance_subcategory": br["provenance_subcategory"], "column_used": "domain"}
        if basis["chosen"] != expected_chosen or basis["birth_row"] != expected_birth:
            raise MeasuringReportError("horizon_basis_invalid: chosen_or_birth_row")
        shape_readings = {key + "_start": value.isoformat() if value else None
                          for key, value in detail["readings"].items()}
        if basis["shape_readings"] != shape_readings:
            raise MeasuringReportError("horizon_basis_invalid: shape_readings")
        # F/I disagreement is reported, not refused; the conjunction is authoritative.
        others = [r for r in events if not is_birth_row(r)]
        dates_f = [as_utc_date(r["event_date"]) for r in others if r["date_confidence"] == "exact"]
        dates_i = []
        for r in others:
            ident = r["provenance_lel_id"]
            match = re.fullmatch(r"EVT\.(\d{4})\.(\d{2})\.(\d{2})\.\d{2}", ident) if isinstance(ident, str) else None
            try:
                ident_date = date(*map(int, match.groups())) if match else None
            except ValueError:
                ident_date = None
            if ident_date is not None and r["event_date"] is not None and ident_date == as_utc_date(r["event_date"]):
                dates_i.append(ident_date)
        readings = {"rule_F_start": date(min(dates_f).year, 1, 1).isoformat() if dates_f else None,
                    "rule_I_start": date(min(dates_i).year, 1, 1).isoformat() if dates_i else None,
                    "conjunction_start": shape_readings["event_date_start"]}
        if basis["fully_dated_readings"] != readings:
            raise MeasuringReportError("horizon_basis_invalid: fully_dated_readings")
        return []
    except MeasuringReportError as exc:
        return [str(exc)]
    except (KeyError, TypeError, ValueError, OverflowError):
        return ["horizon_basis_invalid: unreadable"]


def _sink_refusals(counts):
    """Aggregate B's independently recounted/consistency-checked sink counts."""
    out = []
    codes = {"omission": "certifier_omissions_present", "invented": "certifier_invented_present",
             "anomaly": "certifier_anomalies_present", "unresolved": None, "near_miss": None}
    for kind, code in codes.items():
        count = counts.get(kind) if isinstance(counts, dict) else None
        if type(count) is not int or count < 0:
            if code:
                out.append(f"sink_counts_missing: {kind}")
        elif code and count:
            out.append(f"{code}: {count}")
    return out


def measuring_acceptance(view, *, expected_horizon, chart_id, birth_date, build_date, reader_refusals=()):
    """Full MB-6 acceptance owned by J-3b / verifier B; partial API is not a PASS.

    run_verdict holds raw MB-4.7 R7c/log evidence, NOT a supplied SUCCESS flag.
    sink_counts holds B's independent MB-2 recount/row-consistency results, NOT
    unverified builder summaries. Missing/invalid counts refuse; positive
    unresolved/near_miss counts are reported, never gates. The caller must bind
    both to this candidate, and supply chart/birth/build context independently.
    This aggregate does not perform the MB-2 geometric recount or stamp proof.
    """
    out = measuring_refusals(view, expected_horizon=expected_horizon, birth_date=birth_date)
    if view.status != "candidate":
        out.append("measuring_status_not_candidate")
    out.extend(reader_refusals)
    if tuple(as_utc_date(v) for v in expected_horizon) != RULED_MEASURING_HORIZON:
        out.append("horizon_mismatch")
    runtime = _runtime_refusals(view.run_verdict, status=view.status, stored_scope=view.stored_scope)
    out.extend(runtime)
    out.extend(_horizon_basis_refusals(view.horizon_basis, chart_id=chart_id, birth_date=birth_date,
                                     build_date=build_date, expected_horizon=expected_horizon))
    out.extend(_sink_refusals(view.sink_counts))
    out = list(dict.fromkeys(out))
    return {"accepted": not out, "refusals": out,
            "run_verdict": "SUCCESS" if not runtime else None,
            "sink_counts": {kind: value if type(value := view.sink_counts.get(kind)) is int and value >= 0 else None
                            for kind in ("omission", "invented", "anomaly", "unresolved", "near_miss")}
                           if isinstance(view.sink_counts, dict) else None,
            "near_miss_rows_stored": view.near_miss_rows_stored, "marker_digest_verified": None,
            "marker_digest_reason": MARKER_DIGEST_NOT_CHECKED}


@dataclass(frozen=True)
class DayGrid:
    label: str
    tz: timezone
    lo: datetime
    hi: datetime
    days: int
    date_inclusive: bool = False


def horizon_days(horizon):
    return (horizon[1] - horizon[0]).days


def build_grid(horizon):
    start, end = (as_utc_date(v) for v in horizon)
    if problem := horizon_problem((start, end)):
        raise MeasuringReportError(problem)
    return DayGrid("utc_half_open", timezone.utc, datetime.combine(start, time(), timezone.utc),
                   datetime.combine(end, time(), timezone.utc), (end - start).days)


def scored_grid():
    return DayGrid("ist_inclusive", IST, datetime.combine(_SCORER_H0, time(), IST),
                   datetime.combine(_SCORER_H1 + timedelta(days=1), time(), IST), SCORED_DAYS, True)


def _merge(intervals):
    ordered = []
    for lo, hi in intervals:
        lo, hi = _utc(lo), _utc(hi)
        if lo > hi:
            raise MeasuringReportError("interval_inverted")
        if lo < hi:
            ordered.append((lo, hi))
    merged = []
    for lo, hi in sorted(ordered):
        if merged and lo <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(hi, merged[-1][1]))
        else:
            merged.append((lo, hi))
    return merged


def _intersection(left, right):
    # Disjoint unions first, then intersect instants, never their day sets.
    a, b = _merge(left), _merge(right)
    i = j = 0
    out = []
    while i < len(a) and j < len(b):
        lo, hi = max(a[i][0], b[j][0]), min(a[i][1], b[j][1])
        if lo < hi:
            out.append((lo, hi))
        if a[i][1] <= b[j][1]:
            i += 1
        else:
            j += 1
    return out


def _days(intervals, grid):
    days = set()
    first_grid = grid.lo.date().toordinal()
    last_grid = grid.hi.date().toordinal()
    for lo, hi in _merge(intervals):
        if not grid.date_inclusive:
            lo, hi = max(lo, grid.lo), min(hi, grid.hi)
            if lo >= hi:
                continue
        local_lo, local_hi = lo.astimezone(grid.tz), hi.astimezone(grid.tz)
        first = local_lo.date().toordinal()
        after = local_hi.date().toordinal() + int(grid.date_inclusive or local_hi.time() != time())
        days.update(range(max(first, first_grid), min(after, last_grid)))
    return days


def admitted_days(intervals, horizon_or_grid):
    grid = horizon_or_grid if isinstance(horizon_or_grid, DayGrid) else build_grid(horizon_or_grid)
    return len(_days(intervals, grid))


def length_distribution(lengths_days):
    lengths = sorted(lengths_days)
    if any(not math.isfinite(x) for x in lengths):
        raise MeasuringReportError("length_not_finite")
    n = len(lengths)
    return {"count": n, "median": median(lengths) if n else None,
            "p90": lengths[math.ceil(n * .9) - 1] if n else None, "max": lengths[-1] if n else None}


@dataclass(frozen=True)
class SupportRecord:
    event_class: str
    path: str
    agent: str
    supports: tuple
    via: str = "base"
    role: str = "scored"


def _supports(records, predicate):
    return _merge(span for r in records if predicate(r) for span in r.supports)


def _p4(records, vias):
    return _intersection(
        _supports(records, lambda r: r.path == "P4" and r.agent == "jupiter" and r.via in vias),
        _supports(records, lambda r: r.path == "P4" and r.agent == "saturn" and r.via in vias))


def _class_supports(records, *, kb=True):
    vias = {"base", "dvi", "karakatva"} | ({"kb"} if kb else set())
    return _merge([*_supports(records, lambda r: r.path != "P4" and r.via in vias), *_p4(records, vias)])


def _report(records, windows, grid):
    records, windows = list(records), list(windows)
    for r in records:
        for bad, code in [
            (r.path not in PATHS, "unknown_path"), (r.agent not in ALL_AGENTS, "unknown_agent"),
            (r.via not in VIA_PATHS, "unknown_via"), (r.role != "scored", "testimony_record_in_scored_share"),
            (r.path == "P4" and r.agent not in P4_AGENTS, "p4_agent_not_jupiter_or_saturn"),
        ]:
            if bad:
                raise MeasuringReportError(code)
        if r.path not in VIA_PATHS[r.via]:
            raise MeasuringReportError("via_not_valid_for_path")
        _merge(r.supports)
    for _, path, lo, hi in windows:
        if path not in PATHS:
            raise MeasuringReportError("unknown_path")
        _merge([(lo, hi)])
    classes = sorted({r.event_class for r in records} | {w[0] for w in windows})
    result = {}
    for cls in classes:
        rs = [r for r in records if r.event_class == cls]
        all_days = _days(_class_supports(rs), grid)
        variants = {
            "P1_base": _supports(rs, lambda r: r.path == "P1" and r.via == "base"),
            "P1_with_karakatva": _supports(rs, lambda r: r.path == "P1"),
            "P2": _supports(rs, lambda r: r.path == "P2"),
            "P3_fast": _supports(rs, lambda r: r.path == "P3" and r.agent in FAST_AGENTS),
            "P3_slow": _supports(rs, lambda r: r.path == "P3" and r.agent in SLOW_AGENTS),
            "P3_union": _supports(rs, lambda r: r.path == "P3"),
            "P4_without_dvi": _p4(rs, {"base", "kb"}),
            "P4_with_dvi": _p4(rs, {"base", "kb", "dvi"}),
        }
        counts = {key: len(_days(spans, grid)) for key, spans in variants.items()}
        counts.update(class_union=len(all_days), kb_only=len(all_days - _days(_class_supports(rs, kb=False), grid)))
        per_agent = {}
        for agent in sorted({r.agent for r in rs}):
            mine = _days(_supports(rs, lambda r: r.agent == agent and r.path != "P4"), grid)
            others = _days(_supports(rs, lambda r: r.agent != agent and r.path != "P4"), grid)
            without = _days(_class_supports([r for r in rs if r.agent != agent]), grid)
            per_agent[agent] = {"days": len(mine), "exclusive_days": len(mine - others),
                                "exclusive_days_vs_class": len(all_days - without)}
        lengths = {p: length_distribution([(_utc(hi) - _utc(lo)).total_seconds() / 86400
                                         for c, path, lo, hi in windows if c == cls and path == p]) for p in PATHS}
        result[cls] = {"admitted_days": counts, "admitted_share": {k: v / grid.days for k, v in counts.items()},
                       "per_agent": per_agent, "window_lengths_days": lengths,
                       "P4_joint": {"without_dvi_days": counts["P4_without_dvi"], "with_dvi_days": counts["P4_with_dvi"]}}
    last = grid.hi.date() - timedelta(days=int(grid.date_inclusive))
    return {"convention": grid.label, "horizon": [grid.lo.date().isoformat(), last.isoformat()], "horizon_days": grid.days, "classes": result}


def class_share_report(records, windows, horizon):
    return _report(records, windows, build_grid(horizon))


def scored_share_report(records, windows):
    return _report(records, windows, scored_grid())


def clip_windows_for_scoring(windows, scored_end):
    end = _utc(scored_end)
    out = []
    for cls, path, lo, hi in windows:
        lo, hi = _utc(lo), _utc(hi)
        if hi < lo:
            raise MeasuringReportError("interval_inverted")
        if lo < end:
            out.append((cls, path, lo, min(hi, end)))
    return out


def near_miss_counts(near_misses):
    counts = Counter("|".join(row) for row in near_misses)
    return {"total": sum(counts.values()), "by_class_relation_body": dict(sorted(counts.items()))}


def _values(row):
    return tuple(row.values()) if isinstance(row, dict) else tuple(row)


def _scalar(row):
    return _values(row)[0]


def read_records(conn, chart_id, generation):
    """Read admitted scored supports; no transaction, connection or state writes."""
    rows = conn.execute(
        "SELECT r.event_class, r.path_id, r.rule_version, r.agent, lower(s.x), upper(s.x), lower_inf(s.x), upper_inf(s.x)"
        " FROM public.ka_gochara_relationship_record r"
        " LEFT JOIN LATERAL unnest(r.temporal_support_intervals) AS s(x) ON true"
        " WHERE r.chart_id = %s AND r.generation = %s AND r.admission_state = 'admitted' AND r.operator_role = 'scored'"
        " ORDER BY r.record_id, lower(s.x)", (chart_id, generation)).fetchall()
    grouped = defaultdict(list)
    for raw in rows:
        cls, path, version, agent, lo, hi, lo_inf, hi_inf = _values(raw)
        if path not in PATHS:
            raise MeasuringReportError("unknown_path_id")
        if version not in ALLOWED_RULE_VERSIONS:
            raise MeasuringReportError("rule_version_not_in_scope")
        if agent not in ALL_AGENTS:
            raise MeasuringReportError("unknown_agent")
        bucket = grouped[(cls, path, agent)]
        if lo is None and hi is None and not (lo_inf or hi_inf):
            continue
        if lo_inf or hi_inf or lo is None or hi is None:
            raise MeasuringReportError("support_interval_unbounded")
        bucket.extend(_merge([(lo, hi)]))
    return [SupportRecord(c, p, a, tuple(spans), "base") for (c, p, a), spans in sorted(grouped.items())]


def read_measuring_view(conn, chart_id, generation, *, run_verdict=None, sink_counts=None):
    """Read the one manifest plus stored seal, versions and class-path census."""
    pair = (chart_id, generation)
    rows = conn.execute(
        "SELECT status, input_generation_vector, lower(horizon), upper(horizon) FROM public.kala_gochara_publication"
        " WHERE chart_id = %s AND generation = %s", pair).fetchall()
    if not rows:
        raise MeasuringReportError("measuring_manifest_missing")
    if len(rows) != 1:
        raise MeasuringReportError("measuring_manifest_ambiguous")
    status, vector, lo, hi = _values(rows[0])
    if isinstance(vector, str):
        vector = json.loads(vector)
    vector = vector or {}
    marker = vector.get("test_slice") or {}
    sealed = _scalar(conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal WHERE chart_id = %s AND generation = %s", pair).fetchone()) > 0
    versions = frozenset(_scalar(r) for r in conn.execute(
        "SELECT rule_version FROM public.ka_gochara_relationship_record WHERE chart_id = %s AND generation = %s"
        " UNION SELECT rule_version FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s", pair * 2).fetchall())
    paths = frozenset(_values(r) for r in conn.execute(
        "SELECT event_class, path_id FROM public.ka_gochara_relationship_record WHERE chart_id = %s AND generation = %s"
        " UNION SELECT event_class, path_id FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s", pair * 2).fetchall())
    near_miss = None
    if _scalar(conn.execute("SELECT to_regclass('public.ka_gochara_near_miss')").fetchone()) is not None:
        near_miss = _scalar(conn.execute("SELECT count(*) FROM public.ka_gochara_near_miss WHERE chart_id = %s AND generation = %s", pair).fetchone())
    return MeasuringBuildView(stored_scope=vector.get("stored_scope"), run=marker.get("run"), sealed=sealed,
                              published=status == "published", horizon=(lo, hi), rule_versions=versions,
                              near_miss_rows_stored=near_miss, class_paths_with_rows=paths, status=status,
                              marker_schema=marker.get("schema"), marker_digest=marker.get("marker_digest"),
                              marker_classes=frozenset(marker.get("classes") or ()),
                              marker_horizon=tuple(marker["horizon"]) if marker.get("horizon") else None,
                              horizon_basis=vector.get("horizon_basis"), run_verdict=run_verdict, sink_counts=sink_counts)


def read_measuring_acceptance(conn, chart_id, generation, *, expected_horizon, birth_date, build_date,
                              run_verdict=None, sink_counts=None):
    """Read-only MB-6 caller for verifier B (J-3b); no evidence defaults to PASS.

    Runtime/log and independently checked sink evidence are explicit inputs;
    the scope basis comes from the captured manifest, never today's LEL.
    Reader refusals join all other findings rather than disappearing.
    """
    try:
        view = read_measuring_view(conn, chart_id, generation, run_verdict=run_verdict, sink_counts=sink_counts)
    except MeasuringReportError as exc:
        return {"accepted": False, "refusals": [str(exc)], "run_verdict": None,
                "sink_counts": None, "near_miss_rows_stored": None, "marker_digest_verified": None,
                "marker_digest_reason": MARKER_DIGEST_NOT_CHECKED}
    reader_refusals = []
    authority = conn.execute("SELECT authoritative_generation FROM public.kala_gochara_authority WHERE chart_id = %s",
                             (chart_id,)).fetchone()
    if authority is not None and str(_scalar(authority)) == str(generation):
        reader_refusals.append("measuring_build_published")
    try:
        read_records(conn, chart_id, generation)
    except MeasuringReportError as exc:
        reader_refusals.append(str(exc))
    return measuring_acceptance(view, expected_horizon=expected_horizon, chart_id=chart_id,
                                birth_date=birth_date, build_date=build_date, reader_refusals=reader_refusals)
