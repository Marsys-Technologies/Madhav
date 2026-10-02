"""Candidate-generation adapter + scorer (SI addendum v1.3; protocol v2.3) — the Stage-1 code of the two-stage freeze.

What it adds over `extract.py` / `metrics.py` (which are unchanged and still score a fully-known generation):

  * an adapter that accepts an UNKNOWN ranking intensity (`si: null`, "unqualified") without dropping, zero-filling or imputing
    it (addendum §3-§4 item 1) — a merged candidate that contains an unknown member has an unqualified representative
    (si = None, peak = None) and still counts in the frozen candidate set and in N;
  * a scorer whose si-dependent endpoints (rank percentile, timing target, §8.3 plateau) are BOUNDS over every attainable
    assignment of the unknown values (`unknowns.py`), qualified only when the verdict is identical for every assignment;
    admission-based endpoints (T-cover, T-FP, §8.1/§8.2 degeneracy, honesty) do not read si at all and are taken from the
    existing, already-qualified `score_generation` run on an admission twin;
  * ranking tie-groups use the addendum's ADJACENT-GAP grouping. `metrics.event_hit` anchors ties on the target value
    (|a - target| < 1e-9). The two agree unless three or more values chain within tolerance; the frozen text governs this
    scorer, and tests/l3/gochara_eval/test_candidate.py pins the divergence rather than hiding it.

For a fully-known extract every range collapses to a point and the figures equal `score_generation`'s — the '3.0'
reproduction (tests + the dry run recorded in the freeze file) is the detector that this adapter measures what the protocol
says.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import statistics as st
from dataclasses import dataclass, field
from pathlib import Path

from .extract import Extract, InputRejected, MergedWindow, measure_sha256
from .metrics import candidate_set, score_generation
from .registry import CAP_DAYS, CLASSES_27, TIE_TOL, TIMING_GRAINS, HeldEvent, Registry
from .unknowns import (DEFAULT_BUDGET, BudgetExceeded, assignments, percentile_of,
                       plateau_fraction)


@dataclass(frozen=True)
class CandWindow:
    """One merged candidate. si/pk are None iff the representative is UNQUALIFIED (an unknown member could change it)."""

    cls: str
    ws: dt.date
    we: dt.date
    pk: dt.date | None
    si: float | None
    unknown_members: int = 0
    members: int = 1

    def overlaps(self, lo: dt.date, hi: dt.date) -> bool:
        return self.ws <= hi and self.we >= lo

    def days_in_horizon(self, h0: dt.date, h1: dt.date) -> int:
        lo, hi = max(self.ws, h0), min(self.we, h1)
        return max(0, (hi - lo).days + 1)


@dataclass
class CandExtract:
    merged: dict[str, list[CandWindow]]
    raw_counts: dict[str, int]
    sha256: dict
    valence_domain: dict
    dedup_table: dict
    row_count: int
    unknown_rows: int
    meta: dict = field(default_factory=dict)


def _finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


def load_candidate_extract(path: str | Path, declared_pin: str | None = None) -> CandExtract:
    """Hash-check (MEASURED, never asserted), class-check, sign-check, then merge with unknown handling.

    INPUT_REJECTED: sha mismatch; class outside the 27; known si < 0 (§4.5) or non-finite (NaN/inf is not a number);
    a missing `si` key (NULL must be explicit `null`, absence is a malformed extract); a window whose we < ws.
    """
    path = Path(path)
    raw = path.read_bytes()
    measured = measure_sha256(raw)
    sha_block = {"declared_pin": declared_pin, "measured": measured,
                 "match": declared_pin is None or measured == declared_pin}
    if declared_pin is not None and measured != declared_pin:
        raise InputRejected("extract sha256 differs from the declared pin "
                            f"(measured {measured}, declared {declared_pin})")
    doc = json.loads(raw)
    rows = doc["rows"]

    unknown_cls = sorted({r["event_class"] for r in rows} - set(CLASSES_27))
    if unknown_cls:
        raise InputRejected(f"extract classes outside the 27-class universe: {unknown_cls}")
    missing = [r for r in rows if "si" not in r]
    if missing:
        raise InputRejected("rows with no `si` key (an unknown intensity must be an explicit null)", missing[:5])
    bad = [r for r in rows if r["si"] is not None and (not _finite(r["si"]) or float(r["si"]) < 0)]
    if bad:
        raise InputRejected("raw rows with si < 0 or non-finite (§4.5 sign-convention adapter)", bad[:5])
    nopk = [r for r in rows if r["si"] is not None and r.get("pk") is None]
    if nopk:
        raise InputRejected("known-si rows with no peak date (pk)", nopk[:5])
    inverted = [r for r in rows if dt.date.fromisoformat(r["we"]) < dt.date.fromisoformat(r["ws"])]
    if inverted:
        raise InputRejected("rows with we < ws", inverted[:5])

    valence_domain: dict = {}
    raw_counts: dict[str, int] = {}
    for r in rows:
        valence_domain[r.get("valence")] = valence_domain.get(r.get("valence"), 0) + 1
        raw_counts[r["event_class"]] = raw_counts.get(r["event_class"], 0) + 1

    merged = merge_candidates(rows)
    dedup = {c: [raw_counts[c], len(merged[c])] for c in sorted(merged)}
    return CandExtract(merged=merged, raw_counts=raw_counts, sha256=sha_block, valence_domain=valence_domain,
                       dedup_table=dedup, row_count=len(rows),
                       unknown_rows=sum(1 for r in rows if r["si"] is None),
                       meta={k: v for k, v in doc.items() if k != "rows"})


def merge_candidates(rows: list[dict]) -> dict[str, list[CandWindow]]:
    """§4.2 dedup. Known groups reproduce `extract.merge_windows` exactly (max si, ties -> earliest peak, ONE tolerance);
    a group with ANY unknown member has an unqualified representative (addendum §4 item 5)."""
    by_cls: dict[str, list[tuple]] = {}
    for r in rows:
        si = None if r["si"] is None else float(r["si"])
        pk = dt.date.fromisoformat(r["pk"]) if r.get("pk") is not None else None
        by_cls.setdefault(r["event_class"], []).append(
            (dt.date.fromisoformat(r["ws"]), dt.date.fromisoformat(r["we"]), pk, si))
    out: dict[str, list[CandWindow]] = {}
    for c, ws in by_cls.items():
        ws.sort(key=lambda w: (w[0], w[1], w[2] or dt.date.min, -1.0 if w[3] is None else w[3]))
        groups: list[list[tuple]] = []
        cur_we = None
        for w in ws:
            if groups and w[0] <= cur_we + dt.timedelta(days=1):
                groups[-1].append(w)
                cur_we = max(cur_we, w[1])
            else:
                groups.append([w])
                cur_we = w[1]
        merged = []
        for g in groups:
            unk = sum(1 for w in g if w[3] is None)
            ws0, we0 = g[0][0], max(w[1] for w in g)
            if unk:
                merged.append(CandWindow(c, ws0, we0, None, None, unk, len(g)))
                continue
            _s, pk, si = g[0][0], g[0][2], g[0][3]
            for w in g[1:]:
                if w[3] > si + TIE_TOL:
                    pk, si = w[2], w[3]
                elif abs(w[3] - si) <= TIE_TOL:
                    pk = min(pk, w[2])
            merged.append(CandWindow(c, ws0, we0, pk, si, 0, len(g)))
        out[c] = merged
    return out


# ---------------------------------------------------------------------------------------------------------------------
# bounds
# ---------------------------------------------------------------------------------------------------------------------
def event_bounds(event: HeldEvent, merged: dict[str, list[CandWindow]], registry: Registry,
                 budget: int = DEFAULT_BUDGET) -> dict:
    """Hit / N / rank-percentile range / timing target for one held-out event over every attainable unknown assignment."""
    lo, hi = event.span()
    cands = candidate_set(event, merged, registry)
    n = len(cands)
    cont_ids = {id(w) for w in cands if w.overlaps(lo, hi)}
    base = {"eid": event.eid, "cls": event.cls, "grain": event.grain, "tier": event.tier, "N": n}
    if not cont_ids:
        return {**base, "hit": False, "pct_lo": None, "pct_hi": None, "pct": None, "unknown_in_set": 0,
                "unknown_in_cont": 0, "target_pk": None, "bounds_status": "EXACT"}

    known = [w for w in cands if w.si is not None]
    a_unk = [w for w in cands if w.si is None and id(w) in cont_ids]
    b_unk = [w for w in cands if w.si is None and id(w) not in cont_ids]
    known_vals = [w.si for w in known]
    known_cont = [i for i, w in enumerate(known) if id(w) in cont_ids]
    k = len(a_unk) + len(b_unk)
    # existing rule: target = first maximal-si overlapping window in candidate order (exact max)
    first_known_target = None
    if known_cont and not a_unk:
        first_known_target = max((known[i] for i in known_cont), key=lambda w: w.si)

    try:
        pcts: dict[float, float] = {}          # rounded key (float-noise dedupe) -> unrounded value
        n_assign = 0
        for combo_a, combo_b in assignments(known_vals, [len(a_unk), len(b_unk)], budget):
            vec = known_vals + list(combo_a) + list(combo_b)
            cont_idx = known_cont + list(range(len(known_vals), len(known_vals) + len(a_unk)))
            tgt = max(cont_idx, key=lambda i: vec[i])
            raw = percentile_of(vec, tgt)
            pcts.setdefault(round(raw, 9), raw)
            n_assign += 1
        pct_lo, pct_hi, status = pcts[min(pcts)], pcts[max(pcts)], ("EXACT" if k == 0 else "BOUNDED")
    except BudgetExceeded:
        pct_lo, pct_hi, status, n_assign = 0.0, 100.0, "BUDGET_EXCEEDED", None
    return {**base, "hit": True, "pct_lo": pct_lo, "pct_hi": pct_hi,
            "pct": pct_lo if pct_lo == pct_hi else None, "unknown_in_set": k, "unknown_in_cont": len(a_unk),
            "target_pk": first_known_target.pk if first_known_target is not None else None,
            "bounds_status": status, "assignments_enumerated": n_assign}


def plateau_verdict(cls: str, year: int, merged: dict[str, list[CandWindow]], budget: int = DEFAULT_BUDGET) -> str:
    """§8.3 verdict over every attainable assignment: 'diverse' | 'plateau' | 'unqualified' (verdict not invariant)."""
    y_lo, y_hi = dt.date(year, 1, 1), dt.date(year, 12, 31)
    ws = [w for w in merged.get(cls, []) if w.ws <= y_hi and w.we >= y_lo]
    if not ws:
        return "diverse"
    known_vals = [w.si for w in ws if w.si is not None]
    k = len(ws) - len(known_vals)
    try:
        verdicts = set()
        for (combo,) in assignments(known_vals, [k], budget):
            verdicts.add(plateau_fraction(known_vals + list(combo)) < 0.5)
    except BudgetExceeded:
        return "unqualified"
    if verdicts == {True}:
        return "diverse"
    if verdicts == {False}:
        return "plateau"
    return "unqualified"


# ---------------------------------------------------------------------------------------------------------------------
# scorer
# ---------------------------------------------------------------------------------------------------------------------
def score_candidate(registry: Registry, cext: CandExtract, coverage_manifest: dict | None = None,
                    budget: int = DEFAULT_BUDGET) -> dict:
    """Same result blocks as `score_generation`; si-dependent endpoints carry ranges and a qualification verdict."""
    merged = cext.merged
    # Admission twin: identical windows, placeholder si. Only the admission-based blocks are taken from it.
    twin_merged = {c: [MergedWindow(cls=c, ws=w.ws, we=w.we, pk=w.pk or w.ws, si=0.0) for w in ws]
                   for c, ws in merged.items()}
    twin = Extract(merged=twin_merged, raw_counts=cext.raw_counts, sha256=cext.sha256, valence_domain=cext.valence_domain,
                   dedup_table=cext.dedup_table, row_count=cext.row_count, meta=cext.meta)
    adm = score_generation(registry, twin, coverage_manifest)
    deg = adm["degeneracy"]
    era = deg["era_indiscriminate"]
    horn = deg["two_horns"]

    held = registry.held
    per_event = [event_bounds(e, merged, registry, budget) for e in held]
    by_eid = {e.eid: e for e in held}

    # ---- T-time: capped median over the exact cohort, as a range ----
    lo_errs, hi_errs, uncapped, unq_time = [], [], [], []
    misses = 0
    for e, p in zip(held, per_event):
        if e.grain != "exact":
            continue
        if not p["hit"]:
            lo_errs.append(CAP_DAYS); hi_errs.append(CAP_DAYS); misses += 1
        elif p["unknown_in_cont"]:
            lo_errs.append(0); hi_errs.append(CAP_DAYS); unq_time.append(e.eid)
        else:
            err = abs((p["target_pk"] - e.proxy_date()).days)
            uncapped.append([e.eid, err])
            lo_errs.append(min(err, CAP_DAYS)); hi_errs.append(min(err, CAP_DAYS))
    if lo_errs:
        m_lo, m_hi = st.median(lo_errs), st.median(hi_errs)
        verdict = True if m_hi <= 45 else (False if m_lo > 45 else None)
    else:
        m_lo = m_hi = None
        verdict = False
    t_time = {"capped_median_days": m_lo if m_lo == m_hi else None, "capped_median_range": [m_lo, m_hi],
              "misses": misses, "uncapped_hits": uncapped, "n_exact": len(lo_errs), "bar_days": 45,
              "pass": verdict, "unqualified_events": unq_time,
              "status": "UNQUALIFIED" if verdict is None else "QUALIFIED"}

    # ---- T-rank ----
    timing = [p for p in per_event if p["grain"] in TIMING_GRAINS]
    plateau_cache: dict[tuple, str] = {}
    eligible, unq_elig = [], []
    for p in timing:
        e = by_eid[p["eid"]]
        if era:
            p["rank_status"] = "void_era"
            continue
        if horn.get(p["cls"]):
            p["rank_status"] = "excluded_two_horns"
            continue
        key = (p["cls"], e.event_year())
        if key not in plateau_cache:
            plateau_cache[key] = plateau_verdict(p["cls"], e.event_year(), merged, budget)
        pv = plateau_cache[key]
        if pv == "plateau":
            p["rank_status"] = "excluded_peak_diversity"
        elif p["N"] < 3:
            p["rank_status"] = "ineligible_N_lt_3"
        elif pv == "unqualified":
            p["rank_status"] = "eligibility_unqualified"
            unq_elig.append(p)
        else:
            p["rank_status"] = "eligible"
            eligible.append(p)
    floor = len(timing) // 2 + 1
    if era:
        same, pairs = deg["identical_pairs"]
        t_rank = {"status": "VOID", "reason": f"era-fingerprint {100 * same / pairs:.1f}% >= 50%",
                  "eligible": 0, "floor": floor, "timing_usable": len(timing)}
    elif len(eligible) + len(unq_elig) < floor:
        t_rank = {"status": "RANK-UNPROVEN", "eligible": len(eligible), "floor": floor, "blocks_flip": True}
    elif unq_elig:
        t_rank = {"status": "UNQUALIFIED", "reason": "§8.3 plateau verdict is not invariant over the unknown intensities "
                  "for these events; unqualified results reduce eligibility, they never relax the floor",
                  "eligible_definite": len(eligible), "eligibility_unqualified": [p["eid"] for p in unq_elig],
                  "floor": floor, "pass": None}
    elif len(eligible) >= floor:
        lows = [p["pct_lo"] if p["pct_lo"] is not None else 100.0 for p in eligible]
        highs = [p["pct_hi"] if p["pct_hi"] is not None else 100.0 for p in eligible]
        m_lo, m_hi = st.median(lows), st.median(highs)
        v = True if m_hi <= 25 else (False if m_lo > 25 else None)
        t_rank = {"status": "VALID" if v is not None else "UNQUALIFIED",
                  "median_percentile": m_lo if m_lo == m_hi else None, "median_range": [m_lo, m_hi],
                  "bar": 25, "pass": v, "eligible": len(eligible), "floor": floor}
    else:
        t_rank = {"status": "RANK-UNPROVEN", "eligible": len(eligible), "floor": floor, "blocks_flip": True}

    for p in per_event:                                   # scorer-internal helper keys stay out of the result
        p.pop("target_pk", None)
    unknown_block = {
        "unknown_rows": cext.unknown_rows,
        "unqualified_merged_candidates": sum(1 for ws in merged.values() for w in ws if w.si is None),
        "events_with_unknown_competitors": [p["eid"] for p in per_event if p["unknown_in_set"]],
        "budget_exceeded_events": [p["eid"] for p in per_event if p["bounds_status"] == "BUDGET_EXCEEDED"],
        "enumeration_budget": budget,
        "rule": "SI addendum v1.3 §4: bounds over all admissible assignments; qualified only if verdict invariant",
    }
    return {"t_cover": adm["t_cover"], "t_time": t_time, "t_rank": t_rank, "t_fp": adm["t_fp"],
            "t_fp_gain": adm["t_fp_gain"], "t_fp_overall": adm["t_fp_overall"], "t_honesty": adm["t_honesty"],
            "degeneracy": deg, "per_event": per_event, "unknown_competitors": unknown_block}
