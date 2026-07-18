#!/usr/bin/env python3
"""
Gate-runner scoring script for D-3 §G, cycle-2 (post TRIGGER/CR-102 rebuild).
Faithfully re-implements the DR-11-ratified T-0 algorithm (curve.ts/checks.ts
from PR #602, merge commit 11377530) but swaps the curve SOURCE from the
cycle-1 dasha_lord_confluence_v1 proxy to the SERVED kala_activation surface
(get_temporal_windows / kala_windows_get), per the gate-runner brief's
explicit instruction that the proxy is now obsolete.

Curve construction (documented judgment call, per brief instruction to be
transparent about this):
  - Pooled 77 distinct served activation rows for chart 482012f1, gathered
    from 5 live get_temporal_windows calls covering 1990-1998 (EMPTY),
    1998-2010 (EMPTY), 2008-2013, 2013-2020, 2016-2023, 2022-2027 (dedup by
    signal_id). Confirmed empty_reason on both pre-2010 calls: "8079 dated
    activation rows exist for this chart/ayanamsha outside that filter
    (these are historical)" -- i.e. the served activation-WINDOW surface's
    earliest coverage is ~2010-08-18 (Mercury MD onset). This is reported
    as a substrate-coverage finding, not assumed away.
  - Each pooled activation carries a dated point-ladder
    (activation_predicted_dates_jsonb): {date, strength in [0,1]} triangles
    (period_start=0.6, period_peak=1.0, period_end=0.4) for dasha_timeline-
    sourced rows, or tighter {date,strength} ramps for convergence-sourced
    (TRIGGER-refined) rows.
  - For a given target domain D (wealth for checks a/b; the LEL category's
    mapped domain for check c), the curve is built from every pooled
    activation whose domains_affected_array contains D (or, for the
    "general" fallback domain, every pooled activation regardless of
    domain -- there is no dedicated general domain on this surface).
  - intensity(t) = sum over matching activations of:
        piecewise-linear interpolation of that activation's OWN point
        ladder (sorted by date) at t, using the ladder's own values at
        the two nearest bracketing points (0 outside the ladder's span)
      times (activation.convergence_score if not null else 1.0)
    The convergence_score multiplier is where TRIGGER's genuine refinement
    would show up as amplification/damping over the raw dasha_timeline
    ladder, exactly mirroring how the served surface itself represents it.
  - LIMITATION, disclosed: the pooled extraction captured {date, strength,
    source} per point but NOT per-point graha, so checks (a)/(b) cannot be
    filtered to Mars-only / Venus+Jupiter-only at the point level; they use
    the domain-level "wealth" tag instead (looser than the named
    mechanism, but the only mechanism-adjacent filter actually servable at
    this scale within response-budget trims -- documented per instruction,
    not hidden).
  - Same math primitives as curve.ts: percentileThreshold (nearest-rank),
    localMax (max intensity within +-windowDays of center), variance,
    fractionAtOrAbove. Same thresholds as DR-11: top-decile (p=0.9) for
    checks (a)/(b), top-tercile (p=2/3) for check (c), +-45 days proximity,
    >=50% hit-rate for check (c), anti-gaming variance>0 + top-decile
    day-fraction <15%.
  - Shuffled-birth negative control: circular-shift every pooled
    activation's point ladder by a fixed day offset (wrap within
    [1984-02-05, 2034-12-31)), 7 evenly-spaced shifts, same construction
    as curve.ts's circularShiftPeriods.
"""
import json, datetime, statistics, sys

SCR = "/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/d6aa9c91-2f4f-4044-8214-8432b8934686/scratchpad"

BOUNDS_START = datetime.date(1984, 2, 5)
BOUNDS_END = datetime.date(2034, 12, 31)
PROXIMITY_DAYS = 45
WINDOW_YEARS = 5
STEP_DAYS = 5
SHUFFLE_COUNT = 7

LOSS_EVENT_ID = "d81fae4e-edf4-58d9-b201-cced7eae19d7"
WINDFALL_EVENT_ID = "bd7f5711-8668-5315-8e25-94dc94f2a101"

VAGUENESS_PATTERNS = [
    ("phase_marker", r"\bphase\s*\d"),
    ("arc_marker", r"\barc\b"),
    ("multi_year_marker", r"\bmulti-?year\b"),
    ("ongoing_marker", r"\bongoing\b"),
    ("resurfaced_marker", r"\bresurfaced\b"),
    ("persisted_n_years", r"\bpersist(ed)?\s+~?\d+\s*years?\b"),
    ("tilde_year", r"~\s*\d{4}"),
    ("circa", r"\bcirca\b"),
    ("approximately", r"\bapproximately\b"),
    ("bare_around_year", r"\baround\s+\d{4}\b"),
    ("month_or_month", r"\b[A-Z][a-z]+\s+or\s+[A-Z][a-z]+\s+\d{4}\b"),
    ("year_span_years", r"\b\d+-\d+\s*years?\b"),
    ("paren_year_range", r"\(~?\d{4}-\d{4}\)"),
]
import re
VAGUENESS_RE = [(l, re.compile(p, re.I)) for l, p in VAGUENESS_PATTERNS]

CATEGORY_TO_DOMAIN = {
    "finance": "wealth", "loss": "wealth", "career": "career", "health": "health",
    "psychological": "health", "relationship": "marriage", "family": "marriage",
    "education": "general", "creative": "general", "spiritual": "general",
    "travel": "general", "other": "general", "residential+travel": "general",
}
# Map our DOMAIN_LORDS-style category-domain to the SERVED surface's domain vocabulary
# (served: career, character, relationship, wealth, health, spirituality)
CATDOM_TO_SERVED = {"wealth": "wealth", "career": "career", "health": "health", "marriage": "relationship", "general": None}

def classify_scorability(ev):
    if ev["domain"] == "other/birth":
        return False, ["birth_anchor_not_an_outcome"]
    reasons = [l for l, r in VAGUENESS_RE if r.search(ev["description"])]
    return (len(reasons) == 0), reasons

def parse(d):
    y, m, dd = [int(x) for x in d.split("-")]
    return datetime.date(y, m, dd)

def days_between(a, b):
    return (b - a).days

def window_for(event_date):
    half = datetime.timedelta(days=int((WINDOW_YEARS / 2) * 365))
    s = max(event_date - half, BOUNDS_START)
    e = min(event_date + half, BOUNDS_END)
    return s, e

def interp_activation_at(points, t):
    # points: sorted list of (date, strength) for ONE activation's own ladder.
    if not points:
        return 0.0
    if t < points[0][0] or t > points[-1][0]:
        return 0.0
    for i in range(len(points) - 1):
        d0, s0 = points[i]
        d1, s1 = points[i + 1]
        if d0 <= t <= d1:
            if d1 == d0:
                return s1
            frac = (t - d0).days / (d1 - d0).days
            return s0 + frac * (s1 - s0)
    return 0.0

def build_curve(activations, target_domain, range_start, range_end, step_days=STEP_DAYS):
    # Pre-sort each activation's own point ladder once.
    prepped = []
    for a in activations:
        if target_domain is not None and target_domain not in a["domains"]:
            continue
        pts = sorted([(parse(p["date"]), p["strength"]) for p in a["points"] if p.get("strength") is not None])
        if not pts:
            continue
        mult = a["conv"] if a["conv"] is not None else 1.0
        prepped.append((pts, mult))
    curve = []
    t = range_start
    while t <= range_end:
        total = 0.0
        for pts, mult in prepped:
            total += interp_activation_at(pts, t) * mult
        curve.append((t, total))
        t = t + datetime.timedelta(days=step_days)
    return curve

def percentile_threshold(curve, p):
    if not curve:
        return 0.0
    vals = sorted(v for _, v in curve)
    idx = min(len(vals) - 1, max(0, int((p * len(vals)) - 1e-9) if p * len(vals) == int(p * len(vals)) else int(p * len(vals))))
    # nearest-rank, mirror curve.ts: idx = ceil(p*n)-1
    import math
    idx = min(len(vals) - 1, max(0, math.ceil(p * len(vals)) - 1))
    return vals[idx]

def local_max(curve, center, window_days):
    lo = center - datetime.timedelta(days=window_days)
    hi = center + datetime.timedelta(days=window_days)
    best = None
    for d, v in curve:
        if d < lo or d > hi:
            continue
        if best is None or v > best[1]:
            best = (d, v)
    return best

def fraction_at_or_above(curve, threshold):
    if not curve:
        return 0.0
    n = sum(1 for _, v in curve if v >= threshold)
    return n / len(curve)

def variance(curve):
    if not curve:
        return 0.0
    vals = [v for _, v in curve]
    mean = sum(vals) / len(vals)
    return sum((v - mean) ** 2 for v in vals) / len(vals)

def score_event(activations, target_domain, event_id, event_date, percentile, proximity_days=PROXIMITY_DAYS):
    s, e = window_for(event_date)
    curve = build_curve(activations, target_domain, s, e)
    threshold = percentile_threshold(curve, percentile)
    peak = local_max(curve, event_date, proximity_days)
    within_proximity = peak is not None
    at_or_above = peak is not None and peak[1] > 0 and peak[1] >= threshold
    return {
        "event_id": event_id, "event_date": str(event_date),
        "window_start": str(s), "window_end": str(e),
        "target_domain": target_domain,
        "threshold_percentile": percentile, "threshold_value": threshold,
        "peak_date": str(peak[0]) if peak else None,
        "peak_intensity": peak[1] if peak else None,
        "peak_lag_days": days_between(event_date, peak[0]) if peak else None,
        "within_proximity": within_proximity,
        "at_or_above_threshold": at_or_above,
        "pass": within_proximity and at_or_above,
    }, curve

def check_curve_not_degenerate(curve):
    v = variance(curve)
    top_decile = percentile_threshold(curve, 0.9)
    frac = fraction_at_or_above(curve, top_decile)
    variance_ok = v > 0
    frac_ok = frac < 0.15
    return {"variance": v, "variance_ok": variance_ok, "top_decile_fraction": frac,
            "top_decile_fraction_ok": frac_ok, "pass": variance_ok and frac_ok}

def circular_shift(activations, shift_days):
    total_days = (BOUNDS_END - BOUNDS_START).days
    out = []
    for a in activations:
        new_points = []
        for p in a["points"]:
            if p.get("strength") is None:
                continue
            d = parse(p["date"])
            offset = ((d - BOUNDS_START).days + shift_days) % total_days
            nd = BOUNDS_START + datetime.timedelta(days=offset)
            new_points.append({"date": str(nd), "strength": p["strength"]})
        out.append({**a, "points": new_points})
    return out

def run_blind_battery(activations, blind_inputs):
    per_event = []
    for e in blind_inputs:
        s, _ = score_event(activations, e["served_domain"], e["event_id"], e["date"], 2 / 3)
        per_event.append(s)
    hits = [p for p in per_event if p["pass"]]
    return {"scored_count": len(per_event), "hit_count": len(hits),
            "hit_rate": (len(hits) / len(per_event)) if per_event else 0.0,
            "per_event": per_event,
            "lead_lag": [h["peak_lag_days"] for h in hits]}

def main():
    events = json.load(open(f"{SCR}/lel_events.json"))
    activations = json.load(open(f"{SCR}/pooled_activations.json"))

    scorable, excluded = [], []
    for e in events:
        ok, reasons = classify_scorability(e)
        (scorable if ok else excluded).append({**e, "reasons": reasons})

    result = {"lel_total": len(events), "scorable_count": len(scorable), "excluded_count": len(excluded),
               "excluded": [{"event_id": e["event_id"], "event_date": e["event_date"], "reasons": e["reasons"]} for e in excluded]}

    # ---- Check (a) peak-proximity: 8L-Mars->2H wealth-loss vs 2025-05-15 ----
    loss_ev = next(e for e in events if e["event_id"] == LOSS_EVENT_ID)
    check_a, curve_a = score_event(activations, "wealth", LOSS_EVENT_ID, parse(loss_ev["event_date"]), 0.9)
    anti_a = check_curve_not_degenerate(curve_a)

    # ---- Check (b) windfall: Venus+Jupiter dhana-yoga vs 2010-07-01 ----
    wind_ev = next(e for e in events if e["event_id"] == WINDFALL_EVENT_ID)
    check_b, curve_b = score_event(activations, "wealth", WINDFALL_EVENT_ID, parse(wind_ev["event_date"]), 0.9)
    anti_b = check_curve_not_degenerate(curve_b)

    # ---- Check (c) blind battery (strict: served-domain match; general->None=all domains) ----
    blind_inputs = []
    for e in scorable:
        catdom = CATEGORY_TO_DOMAIN.get(e["category"], "general")
        served_domain = CATDOM_TO_SERVED.get(catdom, None)
        blind_inputs.append({"event_id": e["event_id"], "date": parse(e["event_date"]), "served_domain": served_domain, "category": e["category"]})

    blind_real = run_blind_battery(activations, blind_inputs)

    shuffled = []
    total_days = (BOUNDS_END - BOUNDS_START).days
    for i in range(1, SHUFFLE_COUNT + 1):
        shift = round((total_days / (SHUFFLE_COUNT + 1)) * i)
        shifted_acts = circular_shift(activations, shift)
        r = run_blind_battery(shifted_acts, blind_inputs)
        shuffled.append({"shift_days": shift, "hit_rate": r["hit_rate"]})
    shuffled_mean = sum(s["hit_rate"] for s in shuffled) / len(shuffled)
    control_gap = blind_real["hit_rate"] - shuffled_mean

    check_c = {
        "threshold_hit_rate": 0.5,
        "scored_count": blind_real["scored_count"], "hit_count": blind_real["hit_count"],
        "hit_rate": blind_real["hit_rate"], "meets_threshold": blind_real["hit_rate"] >= 0.5,
        "lead_lag_distribution_days": blind_real["lead_lag"],
        "shuffled_birth_control": shuffled, "shuffled_mean_hit_rate": shuffled_mean,
        "control_gap": control_gap, "beats_shuffled_control": control_gap > 0,
        "pass": blind_real["hit_rate"] >= 0.5 and control_gap > 0,
    }

    result["check_a_peak_proximity"] = check_a
    result["check_a_anti_gaming"] = anti_a
    result["check_b_windfall"] = check_b
    result["check_b_anti_gaming"] = anti_b
    result["check_c_blind_battery"] = check_c
    result["check_c_per_event"] = blind_real["per_event"]

    # Substrate coverage note: fraction of scorable events with an event_date before the
    # earliest confirmed served-surface activation coverage (~2010-08-18).
    earliest_served = datetime.date(2010, 8, 18)
    pre_coverage = [e for e in scorable if parse(e["event_date"]) < earliest_served]
    result["substrate_coverage_note"] = {
        "earliest_confirmed_served_activation_date": str(earliest_served),
        "scorable_events_before_earliest_coverage": len(pre_coverage),
        "scorable_events_before_earliest_coverage_ids": [e["event_id"] for e in pre_coverage],
    }

    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
