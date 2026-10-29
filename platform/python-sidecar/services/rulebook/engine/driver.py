"""Rule Book engine (E4) — date-range driver: chart + range -> per-day member states.

Output is for the later scorer. It is data only: per evaluable member rule, a
run-length list of states over the civil dates of the range (state of date D = the
configuration at the sunrise that starts D; ``DAY_CONVENTION_ID``). Natal-promise
members are chart-level (one constant run). Nothing here scores, ranks, weights or
tests; the saturation block is a report (CR-ENG-001), not a gate.

Refusals (fail closed): a zone other than IST; a bundle or manifest whose hashes do
not match; a node-excluded or unsupported rule (never present in the bundle).
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import Any, Dict, List, Mapping

from ..ast import NOT_ASSESSED, Tri, k_or
from . import constants as K
from .birthcheck import require_consistent, utc_consistency_problems
from .birthrecord import ChartRefused
from .chart import NatalChart, readiness
from .dayatom import SunriseProvider, build_grid, birth_utc, require_ist, tzdb_version
from .evaluator import combine_member_cards, evaluate_plan
from .plan import TRANSIT_HOUSE, plan_card
from .resolve import EvalContext
from .series import Series
from .sky import SkyTable
from .units import EVALUABLE


class ScanRefused(RuntimeError):
    pass


def prepare_chart(chart: NatalChart, first: date, last: date) -> NatalChart:
    """Fix the birth instant, failing closed.

    Explicit-offset path (``birth.utc_offset_minutes`` set, from the source record): the instant must
    already be local time minus that offset; no zone is consulted. Otherwise the IST path: the zone
    must be an IST zone for the whole run (DF-04), anything else raises.
    """
    b = chart.birth
    if b.utc_offset_minutes is not None:
        from datetime import datetime, time as dtime, timedelta, timezone

        parts = [int(x) for x in b.birth_time_local.split(":")]
        while len(parts) < 3:
            parts.append(0)
        want = (datetime.combine(b.birth_date, dtime(*parts)) - timedelta(minutes=b.utc_offset_minutes)).replace(tzinfo=timezone.utc)
        if b.birth_utc is None or b.birth_utc != want:
            raise ChartRefused("OFFSET_BIRTH_INSTANT_INCONSISTENT", "birth_utc is not local time minus the stated offset")
        return chart
    require_ist(b.zone, min(first, b.birth_date), last)
    from dataclasses import replace

    chart.birth = replace(b, birth_utc=birth_utc(b))
    return chart


def _runs(series: Series) -> List[List[Any]]:
    return [[s, K.STATE_CODE[v.value]] for s, _e, v in series.runs()]


def _duty(series: Series) -> Dict[str, Any]:
    n_true = series.count(Tri.TRUE)
    n_false = series.count(Tri.FALSE)
    n_na = series.count(Tri.NOT_ASSESSED)
    assessed = n_true + n_false
    return {
        "days": series.n,
        "true": n_true,
        "false": n_false,
        "not_assessed": n_na,
        "duty": (n_true / assessed) if assessed else None,
    }


def scan(
    chart: NatalChart,
    sky: SkyTable,
    provider: SunriseProvider,
    first: date,
    last: date,
    bundle: Mapping[str, Any],
    manifest: Mapping[str, Any],
    *,
    manifest_sha256: str,
    bundle_sha256: str,
    include_sunrise: bool = False,
) -> Dict[str, Any]:
    """Evaluate every evaluable unit member over [first, last]; returns the states document."""
    if manifest.get("manifest_schema") != K.MANIFEST_SCHEMA or bundle.get("bundle_schema") != K.BUNDLE_SCHEMA:
        raise ScanRefused("manifest/bundle schema mismatch")
    if manifest.get("bundle_sha256") != bundle_sha256:
        raise ScanRefused("the manifest does not name this bundle (bundle_sha256 differs)")
    chart = prepare_chart(chart, first, last)
    if chart.birth.utc_offset_minutes is not None:
        require_consistent(chart, sky)  # the L1 facts must belong to the stated UT (raises ChartExcluded)
    grid = build_grid(first, last, provider)
    ctx = EvalContext(chart, sky, grid)

    members: Dict[str, Dict[str, Any]] = {}
    sat_cards: Dict[str, Any] = {}
    series_by_member: Dict[str, Series] = {}
    meta_by_member: Dict[str, Mapping[str, Any]] = {}
    for unit in manifest["units"]:
        if unit["status"] != EVALUABLE:
            continue
        for m in unit["members"]:
            if m["status"] != EVALUABLE:
                continue
            rid = m["rulebook_id"]
            brule = bundle["rules"].get(rid)
            if brule is None or brule["rule_sha256"] != m["rule_sha256"]:
                raise ScanRefused(f"{rid}: bundle entry missing or not the manifest's rule (rule_sha256)")
            plans = []
            for c in brule["cards"]:
                plans.append(plan_card(c["ir"], c["operands"]))
            per_card = [evaluate_plan(p, ctx) for p in plans]
            state = combine_member_cards(per_card)
            series_by_member[rid] = state
            meta_by_member[rid] = {"unit": unit["unit_id"], "plane": m["plane"], "polarity": m["polarity"], "transit_bodies": m["transit_bodies"]}
            entry: Dict[str, Any] = {
                "unit": unit["unit_id"],
                "plane": m["plane"],
                "polarity": m["polarity"],
                "chart_level": m["plane"] == "natal_promise",
                "runs": _runs(state),
            }
            members[rid] = entry
            # per-card saturation: the card's duty against its transiting graha's own occupancy of the same houses
            occ = {}
            for p in plans:
                for pp in p.preds.values():
                    if pp.kind == TRANSIT_HOUSE and pp.p("graha"):
                        occ[f"{pp.p('graha')}@{','.join(str(x) for x in pp.p('targets'))}"] = _duty(ctx.pred(pp, p.frame))["duty"]
            d = _duty(state)
            sat_cards[rid] = {
                **d,
                "graha_occupancy": occ,
                "duty_minus_max_occupancy": (d["duty"] - max(v for v in occ.values() if v is not None))
                if d["duty"] is not None and any(v is not None for v in occ.values())
                else None,
            }
    saturation = _saturation(series_by_member, meta_by_member, sat_cards, grid.n)

    sun_bytes = ",".join("NA" if u is None else f"{u.timestamp():.0f}" for u in grid.sunrise_utc).encode("ascii")
    doc: Dict[str, Any] = {
        "states_schema": K.STATES_SCHEMA,
        "engine_version": K.ENGINE_VERSION,
        "manifest_sha256": manifest_sha256,
        "bundle_sha256": bundle_sha256,
        "day_convention": K.DAY_CONVENTION_ID,
        "node_policy": K.NODE_POLICY_ID,
        "chart": {
            "chart_key": chart.chart_key,
            "zone": chart.birth.zone,
            "tzdb": tzdb_version(),
            "birth_utc": chart.birth.birth_utc.isoformat() if chart.birth.birth_utc else None,
            "birth_instant_source": "explicit_utc_offset_from_source_record" if chart.birth.utc_offset_minutes is not None else "ist_zone",
            "utc_offset_minutes": chart.birth.utc_offset_minutes,
        },
        "range": {"first": first.isoformat(), "last": last.isoformat(), "days": grid.n},
        "sunrise": {
            "provider": grid.provider,
            "utc_epoch_seconds_sha256": hashlib.sha256(sun_bytes).hexdigest(),
            "no_sunrise_days": grid.no_sunrise_days,
        },
        "coverage": {
            "sky_coverage_end_jd": sky.coverage_end_jd,
            "sky_fingerprint_sha256": sky.fingerprint(),
            "sky_chain_defects": dict(sorted(sky.chain_defects.items())),
            "md_first_jd": chart.md.first_jd,
            "md_last_jd": chart.md.last_jd,
            "ad_first_jd": chart.ad.first_jd,
            "ad_last_jd": chart.ad.last_jd,
        },
        "ledger": {k: sorted(set(v)) for k, v in chart.ledger.items()},
        "diagnostics": dict(sorted(chart.diagnostics.items())),
        "readiness_problems": readiness(chart),
        "birth_consistency_problems": utc_consistency_problems(chart, sky),
        "members": members,
        "saturation": saturation,
    }
    if include_sunrise:
        doc["sunrise"]["utc_epoch_seconds"] = [None if u is None else int(u.timestamp()) for u in grid.sunrise_utc]
    return doc


def _saturation(
    series_by_member: Mapping[str, Series],
    meta: Mapping[str, Mapping[str, Any]],
    cards: Mapping[str, Any],
    n: int,
) -> Dict[str, Any]:
    """CR-ENG-001 report: per card (above) and per graha (union of its transit members), by polarity.

    Report only. No tolerance is declared in v1 (declared at the pre-run, before E7), no member is
    dropped and nothing is gated. Duty = share of ASSESSED days on which the state is TRUE.
    """
    groups: Dict[str, List[Series]] = {}
    for rid, s in series_by_member.items():
        mm = meta[rid]
        if mm["plane"] != "transit":
            continue
        for b in mm["transit_bodies"]:
            groups.setdefault(f"{b}/{mm['polarity']}", []).append(s)
    per_graha = {}
    for key, ss in sorted(groups.items()):
        union = Series.zip(k_or, *ss) if len(ss) > 1 else ss[0]
        per_graha[key] = {"members": len(ss), **_duty(union)}
    return {
        "status": "report_only",
        "gate": None,
        "per_card": dict(sorted(cards.items())),
        "per_graha_polarity_union": per_graha,
    }


def compact_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def write_states(doc: Mapping[str, Any], path: str) -> str:
    data = compact_bytes(doc)
    with open(path, "wb") as fh:
        fh.write(data)
    return hashlib.sha256(data).hexdigest()
