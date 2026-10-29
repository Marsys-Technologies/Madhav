"""Rule Book scorer - the one real run, and the mechanical dry run (v1.1 Part G steps 7-8).

* ``RunLedger.claim`` refuses a second run on the same sample. The claim is made BEFORE anything is
  computed and is never released: a run that crashes after the claim has still "run", and v1.1 Part G says an
  edit after the occurrences are opened makes the result VOID, never a re-run.
* ``mechanical_dry_run`` checks only that the pipeline completes and its invariants hold, and returns no
  statistic.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

import numpy as np

from . import config as C
from .core import FamilyContext, applicable_mask, score_family, scorable_mask
from .footprint import descriptive_hits, family_testable
from .model import ChartTimeline, Episode, ScorerError, UnitSpec
from .outcome import LABEL_CONFLICT_DRIVEN, decide, mde_report


class RunRefused(RuntimeError):
    """A second run on the same sample, or a run that breaks the minimum for a verdict."""


def sample_sha256(timelines: Mapping[str, Sequence[ChartTimeline]], episodes: Mapping[str, Sequence[Episode]]) -> str:
    """Hash of the sample: every chart's family horizon, and every episode (order-independent)."""
    h = hashlib.sha256()
    for fam in sorted(timelines):
        for t in sorted(timelines[fam], key=lambda x: x.code):
            h.update(json.dumps([fam, t.code, t.birth, t.h_start, t.h_end]).encode("utf-8") + b"\n")
    for fam in sorted(episodes):
        rows = sorted((e.chart, e.area, e.direction, e.grade, e.lo, e.hi, e.schedulable) for e in episodes[fam])
        for r in rows:
            h.update(json.dumps([fam] + list(r)).encode("utf-8") + b"\n")
    return h.hexdigest()


class RunLedger:
    """Append-only directory of claims, one file per sample hash, created with O_EXCL."""

    def __init__(self, directory: str):
        self.dir = Path(directory)

    def claim(self, sample_sha: str, scorer_sha: str, note: str = "") -> Path:
        self.dir.mkdir(parents=True, exist_ok=True)
        path = self.dir / (sample_sha + ".run")
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise RunRefused(f"the scorer has already been run on this sample ({sample_sha[:12]}); a second run is refused")
        with os.fdopen(fd, "w") as fh:
            fh.write(json.dumps({"sample_sha256": sample_sha, "scorer_sha256": scorer_sha, "note": note}, sort_keys=True) + "\n")
        return path

    def has(self, sample_sha: str) -> bool:
        return (self.dir / (sample_sha + ".run")).exists()


def _conflict_free(units: Sequence[UnitSpec]) -> List[UnitSpec]:
    return [u for u in units if u.kind == "conflict_free"]


def score_sample(
    contexts: Mapping[str, FamilyContext],
    episodes: Mapping[str, Sequence[Episode]],
    cfg: C.ScoreConfig,
    ledger: RunLedger,
    *,
    power_curve: Optional[Mapping[str, Sequence[float]]] = None,
    note: str = "",
    d7: Optional[Mapping[str, Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    """The real run. Claims the ledger first; refuses below the minimum for a verdict (20 charts and 400
    scored daśā episodes); scores each testable family; reads the outcome by Part E; returns the result."""
    sha = sample_sha256({f: c.tl for f, c in contexts.items()}, episodes)
    ledger.claim(sha, C.source_sha256(), note)
    result: Dict[str, Any] = {
        "scorer_version": C.SCORER_VERSION,
        "scorer_source_sha256": C.source_sha256(),
        "sample_sha256": sha,
        "config": asdict(cfg),
        "yardstick_v10_sha256": C.YARDSTICK_V10_SHA256,
        "yardstick_v11_sha256": C.YARDSTICK_V11_SHA256,
        "cluster_table_sha256": C.CLUSTER_TABLE_SHA256,
    }
    scored_by_family: Dict[str, List[Episode]] = {}
    testab: Dict[str, Dict[str, Any]] = {}
    for fam, ctx in contexts.items():
        ok = applicable_mask(ctx, list(episodes.get(fam, [])))  # K2: scored-applicable, the count D7 and A7 use
        scored_by_family[fam] = [e for e, k in zip(episodes.get(fam, []), ok) if k]
        testab[fam] = family_testable(ctx, scored_by_family[fam])
        if d7 and fam in d7:  # v1.2 D7 / v1.3: the sealed counts decide; the footprint-survival half stays from the timelines
            sealed = d7[fam]
            testab[fam]["sealed_counts"] = {k: sealed.get(k) for k in ("counts_ok", "donor_floor_ok", "dir_testable", "z25_units")}
            testab[fam]["testable"] = bool(sealed.get("counts_ok") and sealed.get("donor_floor_ok") and testab[fam]["units_surviving"] * 2 >= testab[fam]["units"] > 0)
    result["testability"] = testab
    d = scored_by_family.get(C.FAMILY_DASHA, [])
    charts_total = len({e.chart for f in scored_by_family.values() for e in f})
    if charts_total < C.MIN_CHARTS_FOR_VERDICT or len(d) < C.MIN_DASHA_EPISODES_FOR_VERDICT:
        result["outcome"] = "NO_VERDICT"
        result["reason"] = f"minimum not met: {charts_total} charts (need {C.MIN_CHARTS_FOR_VERDICT}), {len(d)} scored daśā episodes (need {C.MIN_DASHA_EPISODES_FOR_VERDICT})"
        return result
    fam_results: Dict[str, Dict[str, Any]] = {}
    for fam, ctx in contexts.items():
        if testab[fam]["testable"]:
            fam_results[fam] = score_family(ctx, episodes.get(fam, []), cfg, d7=(d7 or {}).get(fam))
            fam_results[fam]["descriptive"] = descriptive_hits(ctx, scored_by_family[fam])
    verdict = decide(fam_results, {f: t["testable"] for f, t in testab.items()}, cfg.fallback_primary_set)
    for fam, per in verdict["families"].items():
        if per["strong"]:  # the conflict-free-only sensitivity label (v1.0 section 5, kept by v1.1)
            ctx = contexts[fam]
            cf = FamilyContext(fam, ctx.tl, _conflict_free(ctx.units), ctx.gate_drop)
            sens = score_family(cf, episodes.get(fam, []), cfg)
            fam_results[fam]["conflict_free_only"] = {k: sens.get(k) for k in ("T", "p1", "episodes_scored")}
            if sens.get("T") is not None and sens["T"] <= 0.5:
                verdict["labels"].append(f"{fam}: {LABEL_CONFLICT_DRIVEN}")
    result["families"] = fam_results
    result["verdict"] = verdict
    result["outcome"] = verdict["outcome"]
    if power_curve:
        result["minimum_detectable_effect"] = mde_report(power_curve["q"], power_curve["power"])
    return result


def write_result(result: Mapping[str, Any], path: str) -> str:
    """Write the result file (0600) and return its sha256."""
    data = (json.dumps(result, sort_keys=True, indent=1, default=float) + "\n").encode("utf-8")
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)
    return hashlib.sha256(data).hexdigest()


def mechanical_dry_run(
    contexts: Mapping[str, FamilyContext], episodes: Mapping[str, Sequence[Episode]], seed: int = 1, draws: int = 40
) -> Dict[str, Any]:
    """Part G step 7: the pipeline completes and its invariants hold. NO statistic is returned or kept."""
    cfg = C.ScoreConfig(draws=draws, seed=seed)
    inv: Dict[str, Any] = {}
    for fam, ctx in contexts.items():
        r = score_family(ctx, episodes.get(fam, []), cfg)
        ok = True
        if r.get("status") == "scored":
            for k in ("p1", "p2", "p3", "p_dir"):
                v = r.get(k)
                ok &= v is None or (0.0 < v <= 1.0)
            ok &= all(np.isfinite(x) for x in r["stats"].values())
            ok &= r["episodes_scored"] + r["episodes_unscorable"] == r["episodes_given"]
        inv[fam] = {"completed": True, "invariants_hold": bool(ok), "episodes_scored": r["episodes_scored"], "status": r["status"]}
    return {"dry_run": True, "families": inv, "statistics_kept": False}
