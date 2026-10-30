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
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from . import config as C
from .core import FamilyContext, applicable_mask, score_family, scorable_mask
from .footprint import descriptive_hits, family_testable
from .model import ChartTimeline, Episode, ScorerError, UnitSpec
from .outcome import LABEL_CONFLICT_DRIVEN, decide, mde_report


class RunRefused(RuntimeError):
    """The run is refused: a second run on the same sample, or an input / lock / count mismatch found BEFORE the
    claim (v1.4 conformance B1/M5). Nothing is claimed, nothing is scored."""


# ── pre-claim validation ────────────────────────────────────────────────────────────────────────────
def prepare_episodes(ctx: FamilyContext, episodes: Sequence[Episode]) -> Tuple[List[Episode], Dict[str, int]]:
    """Pure validation pass, before the claim (review B1; v1.2 K2, K15; count_blind's rules). Drops and counts
    mixed-direction rows, grades other than day/month (G3, R), month windows not wholly inside the family horizon
    and day-grade dates outside it; clips a day-grade window (the day +- 1) to the horizon. Never raises on a
    routine row."""
    kept: List[Episode] = []
    drops = {"dropped_mixed": 0, "dropped_g3_or_range": 0, "dropped_horizon": 0, "clipped_day_windows": 0}
    for ep in episodes:
        if ep.grade not in (C.G1, C.G2):
            drops["dropped_g3_or_range"] += 1
            continue
        if ep.direction not in C.POLARITY_OF_DIRECTION:
            drops["dropped_mixed"] += 1
            continue
        if not 0 <= ep.chart < len(ctx.tl):
            raise RunRefused("an episode refers to a chart that is not admitted in this family")
        t = ctx.tl[ep.chart]
        if ep.grade == C.G2:
            if ep.lo < t.h_start or ep.hi > t.h_end:
                drops["dropped_horizon"] += 1
                continue
            kept.append(ep)
            continue
        day = ep.lo + 1 if ep.hi - ep.lo == 2 else None
        if day is None or not t.h_start <= day <= t.h_end:
            drops["dropped_horizon"] += 1
            continue
        lo, hi = max(ep.lo, t.h_start), min(ep.hi, t.h_end)
        if (lo, hi) != (ep.lo, ep.hi):
            drops["clipped_day_windows"] += 1
        kept.append(Episode(ep.chart, ep.area, ep.direction, ep.grade, lo, hi, ep.schedulable))
    for e in kept:
        e.validate()
    return kept, drops


def recount_rows(ctx: FamilyContext, episodes: Sequence[Episode]) -> Dict[Tuple[str, str, str, str], Dict[str, int]]:
    """Per (chart code, area, direction, grade-as-count-blind): episodes, scored_applicable and
    scored_with_opposite_applicable, from horizons and assessed masks only (the count_blind definitions)."""
    from .core import opposite_applicable_mask

    app = applicable_mask(ctx, episodes)
    opp = opposite_applicable_mask(ctx, episodes)
    out: Dict[Tuple[str, str, str, str], Dict[str, int]] = {}
    for e, a, o in zip(episodes, app, opp):
        k = (ctx.tl[e.chart].code, e.area, e.direction, {C.G1: "day", C.G2: "month"}[e.grade])
        row = out.setdefault(k, {"episodes": 0, "scored_applicable": 0, "scored_with_opposite_applicable": 0})
        row["episodes"] += 1
        row["scored_applicable"] += int(a)
        row["scored_with_opposite_applicable"] += int(a and o)
    return out


def _sha_file(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@dataclass
class RunLock:
    """What the lock log fixes before opening, and the run must match exactly (review S2, S5, S8, M6; v1.4)."""

    occurrence_sha256: str
    birth_data_sha256: str
    scorer_sha256: str  # the frozen scorer
    seed: int
    fallback_primary_set: bool  # the A7 choice
    count_set: str  # "primary_nonschedulable" or "all"
    admitted: Mapping[str, Sequence[str]]  # family -> chart codes (after K8 exclusion 5)
    d7: Mapping[str, Mapping[str, Any]]  # family -> sealed D7 record (testable, dir_testable, z25_units, donor_charts_b/c)
    count_rows: Mapping[str, Sequence[Mapping[str, Any]]]  # family -> count_blind aggregate rows of count_set
    files: Mapping[str, str] = field(default_factory=dict)  # role -> path of every input file loaded
    scheme_combination: str = "simes"
    ledger_dir: str = C.LEDGER_DIR


def claim_keys(lock: RunLock, contexts: Mapping[str, FamilyContext]) -> Dict[str, str]:
    """Review S5 / v1.4: the claim is keyed on the logged sha256 of the occurrence file, the birth-data file and the
    frozen scorer; a second key covers the content of the sorted admitted set (chart codes and horizons, by code,
    never by list order)."""
    k1 = hashlib.sha256(f"{lock.occurrence_sha256}|{lock.birth_data_sha256}|{lock.scorer_sha256}".encode()).hexdigest()
    h = hashlib.sha256()
    for fam in sorted(contexts):
        for t in sorted(contexts[fam].tl, key=lambda x: x.code):
            h.update(json.dumps([fam, t.code, t.birth, t.h_start, t.h_end]).encode() + b"\n")
    return {"inputs": k1, "admitted_set": h.hexdigest()}


class RunLedger:
    """Append-only directory of claims, one file per key, created with O_EXCL; one fixed, logged path."""

    def __init__(self, directory: str = C.LEDGER_DIR):
        self.dir = Path(directory)

    def _path(self, key: str) -> Path:
        return self.dir / (key + ".run")

    def has(self, key: str) -> bool:
        return self._path(key).exists()

    def claim(self, keys: Mapping[str, str], scorer_sha: str, note: str = "") -> List[Path]:
        self.dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        for role, key in keys.items():
            if self.has(key):
                raise RunRefused(f"the scorer has already been run on this sample ({role} key {key[:12]}); a second run is refused")
        out = []
        for role, key in keys.items():
            try:
                fd = os.open(str(self._path(key)), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                raise RunRefused(f"the scorer has already been run on this sample ({role} key {key[:12]})")
            with os.fdopen(fd, "w") as fh:
                fh.write(json.dumps({"role": role, "key": key, "scorer_sha256": scorer_sha, "note": note}, sort_keys=True) + "\n")
            out.append(self._path(key))
        return out


def _conflict_free(units: Sequence[UnitSpec]) -> List[UnitSpec]:
    return [u for u in units if u.kind == "conflict_free"]


def validate_before_claim(
    contexts: Mapping[str, FamilyContext], episodes: Mapping[str, Sequence[Episode]], cfg: C.ScoreConfig, lock: RunLock
) -> Dict[str, Any]:
    """Everything that can refuse the run, BEFORE the claim (v1.4 conformance B1/M5, S2, S3, S8, M6). Raises
    RunRefused on any mismatch. Returns the prepared episodes and the counts of the validation."""
    from .core import d7_from_counts, donor_eligibility_counts

    problems: List[str] = []
    if lock.scorer_sha256 != C.source_sha256():
        problems.append("the scorer is not byte-identical to the frozen one (sha256)")
    if cfg.draws != C.DRAWS_PRODUCTION:
        problems.append(f"draws {cfg.draws} != {C.DRAWS_PRODUCTION}")
    if cfg.seed != lock.seed:
        problems.append("seed differs from the logged seed")
    if cfg.fallback_primary_set != lock.fallback_primary_set:
        problems.append("A7 primary-set flag differs from the logged choice")
    if cfg.scheme_combination != lock.scheme_combination:
        problems.append("scheme combination differs from the logged one (v1.4 M1)")
    # files actually loaded (S8)
    hashes: Dict[str, str] = {}
    for role, path in sorted(lock.files.items()):
        if not Path(path).exists():
            problems.append(f"input {role} missing")
            continue
        hashes[role] = _sha_file(path)
        name = Path(path).name
        if name in C.YARDSTICK_SHA256 and hashes[role] != C.YARDSTICK_SHA256[name]:
            problems.append(f"{name} does not match its locked sha256")
        if role == "cluster_table" and hashes[role] != C.CLUSTER_TABLE_SHA256:
            problems.append("cluster table does not match its logged sha256")
    if set(C.YARDSTICK_SHA256) - {Path(p).name for p in lock.files.values()}:
        problems.append("not every yardstick file (v1.0 to v1.4) was supplied for hashing")
    if "cluster_table" not in lock.files or "unit_manifest" not in lock.files:
        problems.append("cluster table and unit manifest must be supplied for hashing")
    prepared: Dict[str, List[Episode]] = {}
    drops: Dict[str, Dict[str, int]] = {}
    recount_ok: Dict[str, bool] = {}
    for fam, ctx in contexts.items():
        codes = sorted(t.code for t in ctx.tl)
        if codes != sorted(lock.admitted.get(fam, [])):
            problems.append(f"{fam}: the family's charts are not the logged admitted set (K8)")
        kept, dr = prepare_episodes(ctx, episodes.get(fam, []))
        prepared[fam], drops[fam] = kept, dr
        mine = recount_rows(ctx, kept)
        sealed: Dict[Tuple[str, str, str, str], Dict[str, int]] = {}
        for row in lock.count_rows.get(fam, []):
            if row["direction"] not in C.POLARITY_OF_DIRECTION or row["grade"] not in ("day", "month"):
                continue
            k = (row["chart_id"], row["area"], row["direction"], row["grade"])
            sealed[k] = {f: int(row[f]) for f in ("episodes", "scored_applicable", "scored_with_opposite_applicable")}
        if {k: v for k, v in mine.items() if v["episodes"]} != {k: v for k, v in sealed.items() if v["episodes"]}:
            problems.append(f"{fam}: episode / scored-applicable counts differ from the logged count_blind aggregates")
        # sealed D7 record against the recount (S2)
        rec = lock.d7.get(fam) or {}
        own = d7_from_counts(ctx, kept)
        don = donor_eligibility_counts(ctx, kept)
        if bool(rec.get("dir_testable")) != own["dir_testable"]:
            problems.append(f"{fam}: p_dir testability differs from the sealed D7 record")
        if sorted(rec.get("z25_units") or []) != (own["z25_units"] if len(own["z25_units"]) >= C.Z25_MIN_UNITS else []):
            problems.append(f"{fam}: the Z25 unit set differs from the sealed D7 record")
        if (rec.get("donor_charts_b"), rec.get("donor_charts_c")) != (don["b"], don["c"]):
            problems.append(f"{fam}: K11 donor counts differ from the sealed D7 record (v1.4 M3)")
        recount_ok[fam] = True
    # A7 on the daśā family only (S3, v1.2 K8)
    d_eps = [e for e, ok in zip(prepared.get(C.FAMILY_DASHA, []), applicable_mask(contexts[C.FAMILY_DASHA], prepared.get(C.FAMILY_DASHA, []))) if ok] if C.FAMILY_DASHA in contexts else []
    a7 = {"dasha_charts": len({contexts[C.FAMILY_DASHA].tl[e.chart].code for e in d_eps}) if d_eps else 0, "dasha_scored_applicable": len(d_eps)}
    a7["ok"] = bool(a7["dasha_charts"] >= C.MIN_CHARTS_FOR_VERDICT and a7["dasha_scored_applicable"] >= C.MIN_DASHA_EPISODES_FOR_VERDICT)
    testable = {fam: bool((lock.d7.get(fam) or {}).get("testable")) for fam in contexts}
    if problems:
        raise RunRefused("refused before the claim: " + "; ".join(problems))
    return {"episodes": prepared, "drops": drops, "a7": a7, "testable": testable, "input_sha256": hashes}


def dry_pass(contexts: Mapping[str, FamilyContext], prepared: Mapping[str, Sequence[Episode]], testable: Mapping[str, bool], lock: RunLock) -> None:
    """A full pass of every testable family with few draws, BEFORE the claim; nothing is kept. Refuses on any
    exception, on a possibly undefined p1, or on a K11 floor the donor check would miss (v1.4 conformance B1/M5)."""
    cfg = C.ScoreConfig(draws=20, seed=lock.seed, fallback_primary_set=lock.fallback_primary_set, scheme_combination=lock.scheme_combination)
    for fam, ok in testable.items():
        if not ok:
            continue
        try:
            r = score_family(contexts[fam], prepared[fam], cfg, d7=lock.d7.get(fam))
        except Exception as exc:  # noqa: BLE001 - every failure must stop the run before the claim
            raise RunRefused(f"refused before the claim: {fam} dry pass raised {type(exc).__name__}: {exc}") from exc
        if r.get("p1") is None:
            raise RunRefused(f"refused before the claim: {fam} is testable but its p1 would be undefined")
        if not r.get("donor_floor_ok"):
            raise RunRefused(f"refused before the claim: {fam} donor floors (K11) not met at scoring")


def score_sample(
    contexts: Mapping[str, FamilyContext],
    episodes: Mapping[str, Sequence[Episode]],
    cfg: C.ScoreConfig,
    lock: RunLock,
    *,
    ledger: Optional[RunLedger] = None,
    power_curve: Optional[Mapping[str, Sequence[float]]] = None,
    note: str = "",
) -> Dict[str, Any]:
    """The real run (v1.1 Part G step 8 with v1.2 K1 and the v1.4 conformance fixes).

    Order: validate everything and run a full dry pass (refuse on any problem) -> no testable family or A7 not met:
    NO_VERDICT, nothing claimed -> claim (never released) -> score each testable family -> read Part E."""
    import platform

    ledger = ledger or RunLedger(lock.ledger_dir)
    v = validate_before_claim(contexts, episodes, cfg, lock)
    result: Dict[str, Any] = {
        "scorer_version": C.SCORER_VERSION,
        "scorer_source_sha256": C.source_sha256(),
        "config": asdict(cfg),
        "input_sha256": v["input_sha256"],
        "occurrence_sha256": lock.occurrence_sha256,
        "birth_data_sha256": lock.birth_data_sha256,
        "yardstick_sha256": dict(C.YARDSTICK_SHA256),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "ledger_dir": str(ledger.dir),
        "canonical_ledger": str(ledger.dir) == C.LEDGER_DIR,
        "validation_drops": v["drops"],
        "a7": v["a7"],
        "testability": v["testable"],
    }
    if not v["a7"]["ok"]:
        result.update(outcome="NO_VERDICT", reason="A7 minimum not met on the daśā family (20 charts, 400 scored-applicable episodes)")
        return result
    if not any(v["testable"].values()):
        result.update(outcome="NO_VERDICT", reason="no family is testable (m = 0)")
        return result
    dry_pass(contexts, v["episodes"], v["testable"], lock)
    keys = claim_keys(lock, contexts)
    ledger.claim(keys, C.source_sha256(), note)
    result["claim_keys"] = keys
    fam_results: Dict[str, Dict[str, Any]] = {}
    for fam, ctx in contexts.items():
        if v["testable"][fam]:
            fam_results[fam] = score_family(ctx, v["episodes"][fam], cfg, d7=lock.d7.get(fam))
            fam_results[fam]["descriptive"] = descriptive_hits(ctx, [e for e, ok in zip(v["episodes"][fam], scorable_mask(ctx, v["episodes"][fam])) if ok])
    verdict = decide(fam_results, v["testable"], cfg.fallback_primary_set)
    for fam, per in verdict["families"].items():
        if per["strong"]:  # the conflict-free-only sensitivity label (v1.0 section 5, kept by v1.1)
            ctx = contexts[fam]
            cf = FamilyContext(fam, ctx.tl, _conflict_free(ctx.units), ctx.gate_drop)
            sens = score_family(cf, v["episodes"][fam], cfg)
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
        kept, _drops = prepare_episodes(ctx, episodes.get(fam, []))
        r = score_family(ctx, kept, cfg)
        ok = True
        if r.get("status") == "scored":
            for k in ("p1", "p2", "p3", "p_dir"):
                v = r.get(k)
                ok &= v is None or (0.0 < v <= 1.0)
            ok &= all(np.isfinite(x) for x in r["stats"].values())
            ok &= r["episodes_scored"] + r["episodes_unscorable"] == r["episodes_given"] == len(kept)
        inv[fam] = {"completed": True, "invariants_hold": bool(ok), "episodes_scored": r["episodes_scored"], "status": r["status"]}
    return {"dry_run": True, "families": inv, "statistics_kept": False}
