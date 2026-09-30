"""Protocol endpoints (v2.3 §5, §6) and degeneracy tests (§8).

Same arithmetic as rerun_3_0_v2_3_scorer.py, factored into clean functions:

  * candidate_set — §4.6 frozen candidate set: merged windows of the event's
    class overlapping the calendar years its scored span touches, clipped to
    the observation mask. One set for N, hit and rank.
  * event_hit — §4.4 / §5: overlap against the scored span; highest-si
    overlapping window is the target; rank percentile 100(r−1)/N with ties at
    the average rank (§4.3); misses stay in the ranking at percentile 100.
  * degeneracy — §8.1 era-boundary fingerprint, §8.2 two-horns, §8.3
    peak-diversity (same 1e-9 grouping predicate as ranking — C5).
  * T-cover (§6.1), T-time (§6.2, uncapped hits disclosed), T-rank (§6.3 with
    machine-readable VOID), T-FP (§6.4 adverse burden + gain 0.5–40 % band),
    T-honesty (§6.5), per-mechanism attribution where the extract labels
    mechanisms (§10 B5.4 disclosure).
"""
from __future__ import annotations

import statistics as st
from collections import defaultdict

from .extract import Extract, MergedWindow
from .registry import (
    ADVERSE_CLASSES,
    CAP_DAYS,
    H_DAYS,
    TIMING_GRAINS,
    TIE_TOL,
    HeldEvent,
    Registry,
)


def candidate_set(event: HeldEvent, merged: dict[str, list[MergedWindow]],
                  registry: Registry) -> list[MergedWindow]:
    """§4.6: merged windows of the event's class overlapping the calendar years
    its scored span touches, clipped to the observation mask [H0, H1]."""
    lo, hi = event.span()
    out: list[MergedWindow] = []
    seen = set()
    for y in range(lo.year, hi.year + 1):
        y_lo = _date(y, 1, 1)
        y_hi = _date(y, 12, 31)
        for w in merged.get(event.cls, []):
            if w.ws <= y_hi and w.we >= y_lo and (w.ws, w.we, w.pk, w.si) not in seen:
                seen.add((w.ws, w.we, w.pk, w.si))
                out.append(w)
    h0, h1 = registry.horizon_start, registry.horizon_end
    return [w for w in out if w.we >= h0 and w.ws <= h1]


def event_hit(event: HeldEvent, merged: dict[str, list[MergedWindow]],
              registry: Registry):
    """Returns (target_window|None, N, rank_percentile|None).

    Rank percentile: candidates of the event's class in the §4.6 set ranked by
    si descending (gain and adverse alike, §4.3); ties take the average rank;
    percentile = 100(r−1)/N. A miss returns (None, N, None); callers enter
    misses into T-rank at the worst-rank convention percentile 100 (§4.4).
    """
    lo, hi = event.span()
    cands = candidate_set(event, merged, registry)
    cont = [w for w in cands if w.overlaps(lo, hi)]
    n = len(cands)
    if not cont:
        return None, n, None
    ranked = sorted(cands, key=lambda w: -w.si)
    tgt = max(cont, key=lambda w: w.si)
    ranks = [i + 1 for i, w in enumerate(ranked) if abs(w.si - tgt.si) < TIE_TOL]
    r = sum(ranks) / len(ranks)
    return tgt, n, 100.0 * (r - 1) / n


def _date(y: int, m: int, d: int):
    import datetime as dt
    return dt.date(y, m, d)


def base_rates(extract: Extract, registry: Registry) -> dict[str, float]:
    """Admitted day-fraction per class (% of H), union of admitted days
    clipped to the horizon. Merged windows are non-overlapping within a class,
    so a sum of clipped window days is the union."""
    return {c: 100 * sum(w.days_in_horizon(registry.horizon_start,
                                           registry.horizon_end)
                         for w in ws) / H_DAYS
            for c, ws in extract.merged.items()}


def degeneracy(extract: Extract, registry: Registry) -> dict:
    """§8 tests, run BEFORE any endpoint. Exclusions feed T-rank."""
    cls_list = sorted(extract.merged)
    base = base_rates(extract, registry)
    horn = {c: ("high" if base[c] > 95 else "low" if base[c] < 0.5 else None)
            for c in cls_list}

    same = pairs = 0
    for i in range(len(cls_list)):
        for j in range(i + 1, len(cls_list)):
            pairs += 1
            if ([(w.ws, w.we) for w in extract.merged[cls_list[i]]]
                    == [(w.ws, w.we) for w in extract.merged[cls_list[j]]]):
                same += 1
    era_indiscriminate = pairs > 0 and (100 * same / pairs) >= 50
    return {"era_indiscriminate": era_indiscriminate,
            "identical_pairs": [same, pairs],
            "two_horns": {c: v for c, v in horn.items() if v},
            "_base": base, "_horn": horn}


def peak_diverse(cls: str, year: int, merged: dict[str, list[MergedWindow]]) -> bool:
    """§8.3: <50% of in-year windows sharing one si value → diverse. Same 1e-9
    grouping as ranking (C5): sort si, cut groups at gaps >= 1e-9."""
    y_lo, y_hi = _date(year, 1, 1), _date(year, 12, 31)
    ws = [w for w in merged.get(cls, []) if w.ws <= y_hi and w.we >= y_lo]
    if not ws:
        return True
    vals = sorted(w.si for w in ws)
    cur = best = 1
    for a, b in zip(vals, vals[1:]):
        cur = cur + 1 if abs(b - a) < TIE_TOL else 1
        best = max(best, cur)
    return best / len(ws) < 0.5


def score_generation(registry: Registry, extract: Extract,
                     coverage_manifest: dict | None = None) -> dict:
    """All co-primary endpoints. Returns the result blocks (t_cover, t_time,
    t_rank, t_fp, t_fp_gain, t_fp_overall, t_honesty, degeneracy, per_event,
    mechanism_attribution). Dev-tier events are never touched (§9.4)."""
    merged = extract.merged
    held = registry.held
    deg = degeneracy(extract, registry)
    era_indiscriminate = deg["era_indiscriminate"]
    horn = deg["_horn"]
    base = deg["_base"]

    # ---- per-event records + T-cover (§6.1) ----
    cover_hit, cover_miss, per_event = [], [], []
    mechanism_hits: dict[str, list[str]] = defaultdict(list)
    for e in held:
        w, n, pct = event_hit(e, merged, registry)
        (cover_hit if w else cover_miss).append(e.eid)
        per_event.append({"eid": e.eid, "cls": e.cls, "grain": e.grain,
                          "tier": e.tier, "N": n, "hit": bool(w), "pct": pct})
        if w is not None and w.mechanism is not None:
            mechanism_hits[w.mechanism].append(e.eid)
    t_cover = {"hits": len(cover_hit), "total": len(held), "misses": cover_miss,
               "bar": "32/47", "pass": len(cover_hit) >= 32}

    # ---- T-time (§6.2): capped median over the exact cohort; uncapped disclosed ----
    errs, misses, uncapped = [], 0, []
    for e in held:
        if e.grain != "exact":
            continue
        w, _n, _p = event_hit(e, merged, registry)
        if w is None:
            errs.append(CAP_DAYS)
            misses += 1
        else:
            err = abs((w.pk - e.proxy_date()).days)
            uncapped.append([e.eid, err])
            errs.append(min(err, CAP_DAYS))
    t_time = {"capped_median_days": st.median(errs) if errs else None,
              "misses": misses, "uncapped_hits": uncapped, "n_exact": len(errs),
              "bar_days": 45,
              "pass": bool(errs) and st.median(errs) <= 45}

    # ---- T-rank (§6.3): §8 exclusions first; machine-readable VOID ----
    timing = [p for p in per_event if p["grain"] in TIMING_GRAINS]
    eligible, excluded = [], []
    for p in timing:
        e = next(x for x in held if x.eid == p["eid"])
        if era_indiscriminate:
            excluded.append((p["eid"], p["cls"], "era-fingerprint (generation-wide VOID)"))
            p["rank_status"] = "void_era"
            continue
        if horn.get(p["cls"]):
            excluded.append((p["eid"], p["cls"], f"two-horns {horn[p['cls']]}"))
            p["rank_status"] = "excluded_two_horns"
            continue
        if not peak_diverse(p["cls"], e.event_year(), merged):
            excluded.append((p["eid"], p["cls"], "peak-diversity"))
            p["rank_status"] = "excluded_peak_diversity"
            continue
        if p["N"] >= 3:
            eligible.append(p)
            p["rank_status"] = "eligible"
        else:
            p["rank_status"] = "ineligible_N_lt_3"
    floor = len(timing) // 2 + 1
    if era_indiscriminate:
        same, pairs = deg["identical_pairs"]
        t_rank = {"status": "VOID",
                  "reason": f"era-fingerprint {100 * same / pairs:.1f}% >= 50%",
                  "eligible": len(eligible), "floor": floor,
                  "timing_usable": len(timing)}
    elif len(eligible) >= floor:
        pcts = [p["pct"] if p["pct"] is not None else 100.0 for p in eligible]
        t_rank = {"status": "VALID", "median_percentile": st.median(pcts), "bar": 25,
                  "pass": st.median(pcts) <= 25, "eligible": len(eligible),
                  "floor": floor}
    else:
        t_rank = {"status": "RANK-UNPROVEN", "eligible": len(eligible),
                  "floor": floor, "blocks_flip": True}

    # ---- T-FP (§6.4): adverse burden + enforced gain 0.5–40% band (C1) ----
    t_fp = {}
    for c in ADVERSE_CLASSES:
        adm = sum(w.days_in_horizon(registry.horizon_start, registry.horizon_end)
                  for w in merged.get(c, []))
        burden = 100 * adm / H_DAYS
        n_c = sum(1 for e in held if e.cls == c)
        budget = min(1.0, 3 * max(n_c, 1) * 90 / H_DAYS) * 100
        t_fp[c] = {"burden_pct": round(burden, 4), "budget_pct": round(budget, 4),
                   "pass": burden <= budget}
    t_fp_gain = {}
    high = low = ok = 0
    for c in sorted(merged):
        if c in ADVERSE_CLASSES or c == "birth_anchor":
            continue
        b = base[c]
        if b > 40:
            high += 1
        elif b < 0.5:
            low += 1
        else:
            ok += 1
        t_fp_gain[c] = {"burden_pct": round(b, 4), "band": "0.5-40%",
                        "pass": 0.5 <= b <= 40}
    t_fp_overall = {"pass": all(v["pass"] for v in t_fp.values())
                    and all(v["pass"] for v in t_fp_gain.values()),
                    "rule": "every adverse entry (t_fp) AND every gain entry "
                            "(t_fp_gain) must pass"}
    deg_out = {k: v for k, v in deg.items() if not k.startswith("_")}
    deg_out["gain_tally"] = {"high": high, "low": low, "ok": ok}

    # ---- T-honesty (§6.5): coverage manifest is a build requirement ----
    if coverage_manifest is None:
        t_honesty = {"status": "UNVERIFIABLE", "pass": False,
                     "consequence": "UNVERIFIABLE on a candidate generation means "
                                    "not flip-eligible (protocol v2.3 §6.5b)",
                     "reason": "no computation-coverage manifest supplied "
                               "(manifest is a build requirement)"}
    else:
        unqualified = []
        for c, frac in coverage_manifest.items():
            if frac < 0.5:
                unqualified.append(c)
        t_honesty = {"status": "PASS" if not unqualified else "PARTIAL",
                     "pass": not unqualified,
                     "coverage": coverage_manifest,
                     "unqualified_classes": sorted(unqualified)}

    mechanism_attribution = {m: {"hits": len(eids), "eids": sorted(eids)}
                             for m, eids in sorted(mechanism_hits.items())}

    return {"t_cover": t_cover, "t_time": t_time, "t_rank": t_rank,
            "t_fp": t_fp, "t_fp_gain": t_fp_gain, "t_fp_overall": t_fp_overall,
            "t_honesty": t_honesty, "degeneracy": deg_out,
            "per_event": per_event,
            "mechanism_attribution": mechanism_attribution}
