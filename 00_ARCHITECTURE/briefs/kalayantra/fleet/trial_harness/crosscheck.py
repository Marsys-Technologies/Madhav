"""G-6 cross-check: re-solve a random sample of the numbered windows (+ every window with a mixed piece among the top-N per path) and compare with the stored
value.  Job-local; not repository code.

WHAT IT CHECKS.  The stored `objective_value` of a numbered window is the solver's claimed GLOBAL maximum of the window's frozen objective F(t) (P4: the
max-min of the two agents' activity; every other path: the evidence-for sum over roots of the per-root max).  This module re-evaluates F from the stored
members through the checkout's own sweep primitives (`window_sweep._pieces`, `_objective_fn`, `maximise_earliest`, `RecordProgram`) — it tests the
MAXIMISATION (the factor VALUES are the independent verifier's claim, G-4) — and compares:

  * DENSE (windows ≤ `dense_max_days`): a 1-second grid over every piece whose live members are not all constant (a constant piece is exact: one evaluation),
    each grid local maximum within `refine_margin` of the best refined by golden section inside its bracket.  Brute force is a LOWER bound of the true maximum
    up to the refinement, so: stored ≥ dense − tol  (the solver found it)  and  stored ≤ dense + tol  (the solver claims nothing higher than exists).
  * SAMPLER (every sampled window): the legacy `maximise_earliest` per piece — it can only under-estimate, so the solver must satisfy stored ≥ sampler − tol.
  * SLIVERS (SR-P1-SLIVER-D2): a piece shorter than one JD-double ulp at its start is one sky event read on two paths, not a sky configuration; the builder leaves it
    out of the window maximum.  Both re-solves above run over the SAME admissible pieces: `is_sliver` is the builder's own predicate (`window_sweep.sliver_resolution_s`,
    the function `window_sweep` applies to the same `_pieces`; imported through the checkout's module, never restated here).  A weak lower bound that counts a sample
    taken inside a sliver would fail a solver for correctly not serving a value that is no sky configuration.  The number left out rides in the record.
  * PEAK CONSISTENCY: F evaluated at the stored peak instant must equal the stored value (a peak that does not produce its value is a defect of either side).

`tol` = the verifier's REAL (float4) storage round-trip (1e-6): the stored column is REAL.  A window the module cannot rebuild is reported under
`recompute_inconsistent` with the reason — never skipped, never counted as agreeing.  Output: window ids (opaque uuids), class/path ids, values, seconds.
"""
from __future__ import annotations

import math
import random
import time
from datetime import datetime, timedelta, timezone

SWEEP_NEEDS = ("sliver_resolution_s", "_pieces", "_objective_fn", "maximise_earliest", "RecordProgram", "SweepRecord", "build_program", "_contains", "_overlaps")
TOL = 1e-6                    # window_verifier._TOL: the REAL (float4) storage round-trip
REFINE_MARGIN = 1e-3          # grid local maxima within this of the best are refined (F changes < 1e-4 per second for any graha / 1.0° orb)
GOLDEN = (math.sqrt(5) - 1) / 2


class AdapterMismatch(RuntimeError):
    """The checkout's window_sweep no longer offers a primitive this cross-check calls (the solver rewrite renamed it): reported, never guessed around."""


def check_adapter(ws) -> None:
    missing = [n for n in SWEEP_NEEDS if not hasattr(ws, n)]
    if missing:
        raise AdapterMismatch(f"window_sweep lacks {missing}")


def _secs(a: datetime, b: datetime) -> float:
    return (b - a).total_seconds()


# ── the window's objective as pieces ────────────────────────────────────────────────────────────────────────────

def is_sliver(ws, a: datetime, b: datetime) -> bool:
    """SR-P1-SLIVER-D2, the builder's predicate: the piece [a, b) is shorter than the stored-edge resolution at its start (`window_sweep.sliver_resolution_s(a)`).
    The same comparison `window_sweep` makes on its `_pieces`; the resolution itself is the builder's function, called, not copied."""
    return (b - a).total_seconds() < ws.sliver_resolution_s(a)


def pieces_of(ws, in_win: list, path_id: str, event_class: str, lo: datetime, hi: datetime) -> list[dict]:
    """The elementary pieces of the window with their objective function.  A P4 piece outside the joint support (not both agents live) is not a candidate;
    a non-P4 piece with no live member has the identically-zero objective (exactly as `draft_windows`).  Each piece carries `sliver` (see `is_sliver`): a sliver is
    listed, so it is counted, but it is no candidate for the maximum in either re-solve."""
    out = []
    for a, b, live in ws._pieces(lo, hi, in_win):
        if path_id == "P4":
            if {p.rec.agent for p in live} != {"jupiter", "saturn"}:
                continue
        elif not live:
            out.append({"a": a, "b": b, "live": [], "f": (lambda t: 0.0), "constant": True, "sliver": is_sliver(ws, a, b)})
            continue
        f = ws._objective_fn(path_id, live, event_class)
        out.append({"a": a, "b": b, "live": live, "f": f, "constant": all(p.constant is not None for p in live), "sliver": is_sliver(ws, a, b)})
    return out


def _direction(vals: list[float]) -> int:
    """+1 rising, -1 falling, 0 flat, 2 non-monotone (a crest or trough inside)."""
    d = [y - x for x, y in zip(vals, vals[1:])]
    up, down = any(x > 1e-12 for x in d), any(x < -1e-12 for x in d)
    return 2 if up and down else (1 if up else (-1 if down else 0))


def is_mixed(piece: dict, samples: int = 9) -> bool:
    """A piece is MIXED when a rising and a falling active term are concurrent, or a single term is not monotone inside it (the case the endpoint-only
    mistake loses).  Sample-based classification (documented heuristic): terms whose value is 0 at every sample are inactive and ignored."""
    if piece["constant"]:
        return False
    a, b = piece["a"], piece["b"]
    span = _secs(a, b)
    ts = [a + timedelta(seconds=span * k / (samples + 1)) for k in range(0, samples + 2)]
    ts[-1] = b - timedelta(microseconds=1)
    dirs = set()
    for p in piece["live"]:
        if p.constant is not None:
            continue
        vals = [p.value_at(t) for t in ts]
        if any(v is None for v in vals) or not any(v > 0 for v in vals):
            continue
        dirs.add(_direction(vals))
    dirs.discard(0)
    return 2 in dirs or {1, -1} <= dirs


def window_is_mixed(pieces: list[dict]) -> bool:
    return any(is_mixed(p) for p in pieces)


# ── the three re-solves ─────────────────────────────────────────────────────────────────────────────────────────

def _golden_max(f, lo: datetime, hi: datetime, tol_s: float = 1e-4):
    x, y = lo, hi
    c = y - timedelta(seconds=_secs(x, y) * GOLDEN)
    d = x + timedelta(seconds=_secs(x, y) * GOLDEN)
    fc, fd = f(c), f(d)
    if fc is None or fd is None:
        return None
    while _secs(x, y) > tol_s:
        if fc >= fd:
            y, d, fd = d, c, fc
            c = y - timedelta(seconds=_secs(x, y) * GOLDEN)
            fc = f(c)
        else:
            x, c, fc = c, d, fd
            d = x + timedelta(seconds=_secs(x, y) * GOLDEN)
            fd = f(d)
        if fc is None or fd is None:
            return None
    m = x + (y - x) / 2
    fm = f(m)
    return None if fm is None else (max(fm, fc, fd), m)


def dense_max(pieces: list[dict], *, step_s: float = 1.0, deadline: float | None = None) -> dict:
    """Brute force over the window.  Returns {max, instant, evals, unknown} or {timeout: True}."""
    best_v, best_t, evals, unknown = -1.0, None, 0, 0
    for pc in pieces:
        a, b, f = pc["a"], pc["b"], pc["f"]
        if pc["sliver"]:
            continue                                       # SR-P1-SLIVER-D2: no sky configuration, no candidate for the maximum
        if pc["constant"]:
            v = f(a)
            evals += 1
            if v is None:
                unknown += 1
            elif v > best_v + 1e-12:
                best_v, best_t = v, a
            continue
        n = max(1, int(math.ceil(_secs(a, b) / step_s)))
        grid = [a + timedelta(seconds=k * step_s) for k in range(n)]
        grid.append(b - timedelta(microseconds=1))
        vals = []
        for i, t in enumerate(grid):
            if deadline is not None and (i & 0x3FF) == 0 and time.time() > deadline:
                return {"timeout": True, "evals": evals}
            v = f(t)
            evals += 1
            vals.append(v)
        if any(v is None for v in vals):
            unknown += sum(1 for v in vals if v is None)
            continue
        top = max(vals)
        for i, v in enumerate(vals):                       # earliest grid point of the best value
            if v > best_v + 1e-12 and v >= top - 1e-12:
                best_v, best_t = v, grid[i]
                break
        for i in range(len(vals)):                          # refine every grid local maximum within the margin of the top
            if vals[i] < top - REFINE_MARGIN:
                continue
            if (i > 0 and vals[i] < vals[i - 1]) or (i + 1 < len(vals) and vals[i] < vals[i + 1]):
                continue
            lo_t, hi_t = grid[max(i - 1, 0)], grid[min(i + 1, len(grid) - 1)]
            if hi_t <= lo_t:
                continue
            got = _golden_max(f, lo_t, hi_t)
            evals += 90
            if got is not None and got[0] > best_v + 1e-12:
                best_v, best_t = got[0], got[1]
    return {"max": None if best_t is None else best_v, "instant": best_t, "evals": evals, "unknown": unknown}


def sampler_max(ws, pieces: list[dict]) -> dict:
    """The legacy sampler (`maximise_earliest`) per ADMISSIBLE piece (slivers are skipped, as the builder skips them); constant pieces are exact.  It can only
    under-estimate the true maximum."""
    best_v, best_t, unknown = -1.0, None, 0
    for pc in pieces:
        if pc["sliver"]:
            continue                                       # SR-P1-SLIVER-D2: a sample inside a sub-resolution sliver is not a sky value the solver owes
        if pc["constant"]:
            v = pc["f"](pc["a"])
            got = None if v is None else (v, pc["a"])
        else:
            hints = [h for p in pc["live"] if p.rec.peak_hints is not None for h in p.rec.peak_hints(pc["a"], pc["b"])]
            got = ws.maximise_earliest(pc["f"], pc["a"], pc["b"], hints=hints)
        if got is None:
            unknown += 1
        elif got[0] > best_v + 1e-12:
            best_v, best_t = got
    return {"max": None if best_t is None else best_v, "instant": best_t, "unknown": unknown}


def value_at(pieces: list[dict], t: datetime) -> float | None:
    for pc in pieces:
        if pc["a"] <= t < pc["b"]:
            return pc["f"](t)
    return None


# ── one window ──────────────────────────────────────────────────────────────────────────────────────────────────

def check_window(ws, pieces: list[dict], stored_value: float, stored_peak: datetime, lo: datetime, hi: datetime, *, dense_max_days: float = 3.0,
                 step_s: float = 1.0, tol: float = TOL, deadline: float | None = None) -> dict:
    """Compare one stored (value, peak) with the three re-solves.  Returns the per-window record (violations are named, not just counted)."""
    days = _secs(lo, hi) / 86400.0
    t0 = time.time()
    rec = {"days": round(days, 3), "stored_value": stored_value, "mixed": window_is_mixed(pieces), "sliver_pieces_skipped": sum(1 for pc in pieces if pc["sliver"]),
           "violations": []}
    fp = value_at(pieces, stored_peak)
    rec["value_at_stored_peak"] = fp
    if fp is None:
        rec["violations"].append({"kind": "recompute_inconsistent", "detail": "the objective is undeterminable at the stored peak instant"})
    elif abs(fp - stored_value) > tol:
        rec["violations"].append({"kind": "recompute_inconsistent", "detail": f"F(stored peak)={fp:.9f} != stored {stored_value:.9f}"})
    sm = sampler_max(ws, pieces)
    rec["sampler_max"] = sm["max"]
    if sm["max"] is None:
        why = "every piece of the window is a sub-resolution sliver, yet the window is numbered" if pieces and all(pc["sliver"] for pc in pieces) else "the legacy sampler found the objective unknown"
        rec["violations"].append({"kind": "recompute_inconsistent", "detail": why})
    elif stored_value < sm["max"] - tol:
        rec["violations"].append({"kind": "sampler", "detail": f"stored {stored_value:.9f} < sampler {sm['max']:.9f}"})
    if days <= dense_max_days:
        dm = dense_max(pieces, step_s=step_s, deadline=deadline)
        if dm.get("timeout"):
            rec["dense"] = {"timeout": True}
            rec["violations"].append({"kind": "timeout", "detail": "dense scan hit the deadline"})
        else:
            rec["dense"] = {"max": dm["max"], "evals": dm["evals"], "unknown": dm["unknown"]}
            if dm["max"] is None or dm["unknown"]:
                rec["violations"].append({"kind": "recompute_inconsistent", "detail": f"the dense scan found the objective unknown at {dm['unknown']} point(s)"})
            else:
                if stored_value < dm["max"] - tol:
                    rec["violations"].append({"kind": "dense", "detail": f"stored {stored_value:.9f} < brute force {dm['max']:.9f} (a higher value exists)"})
                if stored_value > dm["max"] + tol:
                    rec["violations"].append({"kind": "dense", "detail": f"stored {stored_value:.9f} > brute force {dm['max']:.9f} (a value that does not exist)"})
    rec["seconds"] = round(time.time() - t0, 2)
    return rec


# ── sample selection ────────────────────────────────────────────────────────────────────────────────────────────

def sample_size(rate: float, n: int) -> int:
    return min(n, math.ceil(rate * n)) if n else 0


def random_sample(window_ids: list[str], rate: float, seed: int) -> list[str]:
    ids = sorted(window_ids)
    return sorted(random.Random(seed).sample(ids, sample_size(rate, len(ids))))


def aggregate(selection: dict, results: dict, numbered_windows: int, rate: float, status: str = "COMPLETE", detail: str | None = None) -> dict:
    """The `crosscheck` section the gate evaluator reads.  `results` = {window_id: per-window record}."""
    sampler_v, dense_v, incon = [], [], []
    dense_windows = 0
    for wid, r in sorted(results.items()):
        for v in r.get("violations", []):
            item = {"window_id": wid, "event_class": r.get("event_class"), "path_id": r.get("path_id"), "detail": v["detail"]}
            (sampler_v if v["kind"] == "sampler" else dense_v if v["kind"] in ("dense", "timeout") else incon).append(item)
        if "dense" in r and not r["dense"].get("timeout"):
            dense_windows += 1
    checked_top = [w for w in selection["top_mixed"] if w in results]
    return {"schema": "ky.trial_crosscheck/1", "status": status, "detail": detail, "seed": selection["seed"], "sample_rate": rate, "numbered_windows": numbered_windows,
            "sampled": len([w for w in selection["random"] if w in results]), "sample_required": sample_size(rate, numbered_windows),
            "top_mixed_requested": len(selection["top_mixed"]), "top_mixed_checked": len(checked_top),
            "dense": {"windows": dense_windows}, "sampler_violations": sampler_v, "dense_violations": dense_v, "recompute_inconsistent": incon,
            "windows_checked": len(results), "sliver_pieces_skipped": sum(r.get("sliver_pieces_skipped", 0) for r in results.values()), "mixed_windows_checked": sum(1 for r in results.values() if r.get("mixed"))}
