"""J5Q offline diagnostics and lossless endpoint presentation.

These functions neither score held-out events nor certify a generation. Gate
predicates added here are (I) INTERPRETATION of the A5.7 title, documented in
J5Q_PREPARATION_v1_0.md. Full solver/serving evidence remains separately owed.
"""
from __future__ import annotations

import datetime as dt
import math
from collections import Counter
from copy import deepcopy

from .candidate import merge_candidates
from .registry import CLASSES_27, H0, H1, TIE_TOL

ENDPOINTS = ("t_cover", "t_time", "t_rank", "t_fp", "t_honesty")
SCORED_CLASSES = tuple(c for c in CLASSES_27 if c != "birth_anchor")
YEARS = tuple(range(H0.year, H1.year + 1))


def record(status: str, measured, predicate: str) -> dict:
    return {"status": status, "measured": deepcopy(measured), "predicate": predicate}


def _endpoint_status(block: dict | None) -> str:
    if not block:
        return "insufficient_evidence"
    if block.get("status") == "VOID":
        return "not_evaluable"
    if block.get("status") in ("UNQUALIFIED", "UNVERIFIABLE", "RANK-UNPROVEN", "PARTIAL"):
        return "insufficient_evidence"
    if block.get("pass") is True:
        return "pass"
    if block.get("pass") is False:
        return "fail"
    return "insufficient_evidence"


def endpoint_records(result: dict | None) -> dict:
    """Present scorer verdicts without recomputation, dropped fields or null→0.

    `measured` retains the original source block including its original status.
    This is a transcription of a pinned scorer artifact, not its verification.
    """
    result = result or {}
    out = {}
    for name in ENDPOINTS:
        source = result.get("t_fp_overall" if name == "t_fp" else name)
        measured = source
        if name == "t_fp" and source is not None:
            measured = {"overall": source, "adverse": result.get("t_fp"), "gain": result.get("t_fp_gain")}
        out[name] = record(_endpoint_status(source), measured,
                           "protocol v2.3 §6; source verdict transcribed; original fields retained")
    return out


def _validated_rows(rows: list[dict]) -> list[dict]:
    for r in rows:
        if r.get("event_class") not in CLASSES_27:
            raise ValueError("unknown event class")
        a, b = dt.date.fromisoformat(r["ws"]), dt.date.fromisoformat(r["we"])
        if a > b:
            raise ValueError("inverted window")
        si = r["si"]
        if si is not None and (isinstance(si, bool) or not isinstance(si, (float, int))
                               or not math.isfinite(si) or si < 0):
            raise ValueError("si must be finite non-negative or explicit null")
        if si is not None and r.get("pk") is None:
            raise ValueError("known si needs peak date")
        if r.get("pk") is not None:
            dt.date.fromisoformat(r["pk"])
        val = r.get("outcome_valence_for_native")
        if val is not None and val not in ("favourable", "adverse", "mixed", "unqualified"):
            raise ValueError("unknown governed outcome valence")
    return [r for r in rows if r["event_class"] != "birth_anchor"
            and dt.date.fromisoformat(r["ws"]) <= H1 and dt.date.fromisoformat(r["we"]) >= H0]


def _coverage(cells: list[dict] | None) -> tuple[dict, dict]:
    by_cell = {}
    for cell in cells or []:
        key = cell["event_class"], cell["year"]
        if (key[0] not in SCORED_CLASSES or type(key[1]) is not int or key[1] not in YEARS
                or type(cell.get("computed")) is not bool or key in by_cell):
            raise ValueError("coverage requires unique scored (class, year) cells and typed computed booleans")
        by_cell[key] = cell["computed"]
    measured = {c: {"computed": sum(by_cell.get((c, y)) is True for y in YEARS), "expected": len(YEARS),
                    "fraction": sum(by_cell.get((c, y)) is True for y in YEARS) / len(YEARS)}
                for c in SCORED_CLASSES}
    complete = len(by_cell) == len(SCORED_CLASSES) * len(YEARS)
    # Missing cells cannot establish a failure of computation or a passing census.
    status = ("insufficient_evidence" if not complete else
              "pass" if all(v["fraction"] >= .5 for v in measured.values()) else "fail")
    coverage = record(status, measured if cells is not None else None,
                      "protocol §6.5: computed (class, year) / horizon cells; ≥50% per scored class; complete census required")
    pre_keys = [(c, y) for c in SCORED_CLASSES for y in YEARS if y < 2020]
    pre = {"computed": sum(by_cell.get(k) is True for k in pre_keys), "expected": len(pre_keys)}
    pre_status = ("insufficient_evidence" if not all(k in by_cell for k in pre_keys) else
                  "pass" if pre["computed"] == pre["expected"] else "fail")
    return coverage, record(pre_status, pre if cells is not None else None,
                            "(I) INTERPRETATION: every scored class/year before 2020 computed, including computed-empty; availability diagnostic only")



def engineering_diagnostics(rows: list[dict], cells: list[dict] | None) -> dict:
    """A5.7 preparation diagnostics over an already pinned, normalized extract.

    `si` is evidence_for for governed 5.x (SI addendum §1). A date-only extract
    cannot prove that no exact instant was fabricated: that gate stays unavailable.
    """
    selected = _validated_rows(rows)
    vals = Counter((r.get("outcome_valence_for_native") or "missing") for r in selected)
    unknown = sum(v for k, v in vals.items() if k in (None, "missing", "unqualified"))
    vs = ("insufficient_evidence" if not selected or unknown else
          "fail" if vals.get("favourable", 0) == len(selected) else "pass")
    valence = record(vs, dict(vals),
                     "(I) INTERPRETATION: known governed outcome-valence census is not all favourable; unqualified/missing never establishes pass")
    peaks = {}
    for cls, windows in merge_candidates(selected).items():
        for year in YEARS:
            ws = [w for w in windows if w.ws <= min(dt.date(year, 12, 31), H1)
                  and w.we >= max(dt.date(year, 1, 1), H0)]
            if not ws:
                continue
            known = sorted(w.si for w in ws if w.si is not None)
            share = None
            if len(known) == len(ws):
                best = cur = 1
                for a, b in zip(known, known[1:]):
                    cur = cur + 1 if b - a < TIE_TOL else 1
                    best = max(best, cur)
                share = best / len(ws)
            peaks[f"{cls}/{year}"] = {"candidates": len(ws), "unknown": len(ws) - len(known),
                                      "largest_tie_share": share}
    ps = ("fail" if any(p["largest_tie_share"] is not None and p["largest_tie_share"] >= .5 for p in peaks.values())
          else "insufficient_evidence" if not peaks or any(p["unknown"] for p in peaks.values()) else "pass")
    coverage, pre = _coverage(cells)
    return {"valence": valence,
            "peaks": record(ps, peaks, "protocol §8.3: adjacent-gap ties <1e-9; ≥50% plateau per populated class/year; unknown representative cannot establish pass"),
            "coverage": coverage, "pre_2020": pre,
            "no_fabricated_instants": record("not_evaluable", None,
                "date-only extracts cannot prove exact-instant provenance; independent solver/record verification required")}
