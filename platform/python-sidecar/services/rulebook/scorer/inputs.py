"""Rule Book scorer - readers for the step-5 and count_blind artefacts, hash-verified before anything is scored.

Formats (conductor, 2026-10-30; count_blind's hash is logged and will not change):

* ``admission-v1_1/timelines/<chart_id>.json``, schema ``admission-v1_1-timeline-1``: run-length member states,
  index 0 = ``range.first``; C2 already applied to daśā members. Family horizons come from
  ``out/s5_horizons.json`` (``charts.<id>.families.<family>.{start,end}``). Every file read is checked against
  ``out/TIMELINES_MANIFEST.json`` (``files``: relative path -> sha256).
* ``COUNT_BLIND_AGGREGATES.csv``, ``COUNT_BLIND_DONORS.csv``, ``COUNT_BLIND_UNITS.csv`` and (count_blind v2)
  ``COUNT_BLIND_DONOR_ELIGIBILITY.csv``, ``COUNT_BLIND_DONOR_DIAGNOSTIC.csv``: UTF-8, header row, decimal integers,
  empty = not applicable. Checked against ``COUNT_BLIND_RUN.json`` (``outputs_sha256``: name -> sha256).

Nothing here reads an occurrence row: only counts, horizons and timelines.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from . import config as C
from .model import ChartTimeline, ScorerError

TIMELINE_SCHEMA = "admission-v1_1-timeline-1"
STATE_CODE = {"T": 1, "F": 0, "N": -1}
SET_PRIMARY = "primary_nonschedulable"
SET_ALL = "all"
GRADE_OF_COUNT = {"day": C.G1, "month": C.G2}

AGG_TEXT = ("chart_id", "family", "set", "area", "direction", "grade")
AGG_INTS = (
    "episodes",
    "scored_applicable",
    "scored_with_opposite_applicable",
    "dropped_horizon",
    "dropped_merge",
    "dropped_mixed",
    "dropped_no_applicable_unit",
    "dropped_under_half_assessed",
    "dropped_g3_or_range",
    "collector_horizon_flag_disagrees",
)
DONOR_COLUMNS = ("threshold", "family", "set", "chart_id", "in_pool", "donors_b", "donors_c")
UNIT_COLUMNS = ("threshold", "family", "set", "unit_id", "scored_applicable_episodes")
# count_blind v2 (COUNT-BLIND-V2-HASHES; SUR-RB-41): the v1.4 M3 / v1.5 P1-P2 donor outputs, masks only
DONOR_ELIG_COLUMNS = ("threshold", "family", "set", "chart_id", "own_cells", "donors_b_m3", "donors_c_m3", "donors_b_p2", "donors_c_p2", "imputed_cells_b_p2", "imputed_cells_c_p2")
DONOR_DIAG_COLUMNS = ("threshold", "family", "set", "check", "pool_charts", "charts_ge5_donors_m3", "k11_floor_met_m3", "charts_ge5_donors_p2", "k11_floor_met_p2", "imputed_cell_share_p2")


class InputError(ScorerError):
    """An input file is missing, malformed, or does not match its logged hash. Nothing is scored."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _verify(path: Path, expected: Optional[str], label: str) -> None:
    if expected is None:
        raise InputError(f"{label}: not listed in its hash index; refusing to read an unlogged file")
    got = sha256_file(path)
    if got != expected:
        raise InputError(f"{label}: sha256 {got[:12]}... does not match the logged {expected[:12]}...")


# ── step-5 timelines ─────────────────────────────────────────────────────────────────────────────────
def runs_to_states(runs: Sequence[Sequence[Any]], n: int) -> np.ndarray:
    out = np.full(n, -2, dtype=np.int8)
    prev = -1
    for k, (s, v) in enumerate(runs):
        s = int(s)
        if s <= prev or s >= n:
            raise InputError("run starts must increase and lie inside the range")
        if v not in STATE_CODE:
            raise InputError(f"unknown state code {v!r}")
        e = int(runs[k + 1][0]) if k + 1 < len(runs) else n
        out[s:e] = STATE_CODE[v]
        prev = s
    if not runs or int(runs[0][0]) != 0 or (out == -2).any():
        raise InputError("runs must start at index 0 and cover the range")
    return out


class AdmissionInputs:
    """The step-5 artefacts of one admission directory, every file hash-checked against TIMELINES_MANIFEST.json."""

    def __init__(self, admission_dir: str, verify: bool = True):
        self.dir = Path(admission_dir)
        self.verify = verify
        man_path = self.dir / "out" / "TIMELINES_MANIFEST.json"
        if not man_path.exists():
            raise InputError("out/TIMELINES_MANIFEST.json missing: step 5 is not complete")
        self.manifest_sha256 = sha256_file(man_path)
        self.files: Dict[str, str] = dict(json.loads(man_path.read_text(encoding="utf-8")).get("files") or {})
        self.horizons = self._json("out/s5_horizons.json")
        self.admit = self._json("out/s6_admit.json")

    def _json(self, rel: str) -> Any:
        p = self.dir / rel
        if not p.exists():
            raise InputError(f"{rel} missing")
        if self.verify:
            _verify(p, self.files.get(rel), rel)
        return json.loads(p.read_text(encoding="utf-8"))

    def admitted(self) -> List[str]:
        return sorted(self.admit.get("admitted") or [])

    def dry_run_set(self) -> List[str]:
        return sorted(self.admit.get("dry_run_set") or [])

    def timeline(self, chart_id: str, family: str) -> ChartTimeline:
        """One chart's family timeline: members of that plane, sliced to the s5 family horizon."""
        doc = self._json(f"timelines/{chart_id}.json")
        if doc.get("timeline_schema") != TIMELINE_SCHEMA:
            raise InputError(f"{chart_id}: timeline_schema {doc.get('timeline_schema')!r} is not {TIMELINE_SCHEMA!r}")
        if doc.get("chart_id") != chart_id:
            raise InputError(f"{chart_id}: file names chart {doc.get('chart_id')!r}")
        rng = doc["range"]
        first = date.fromisoformat(rng["first"]).toordinal()
        n = int(rng["days"])
        if date.fromisoformat(rng["last"]).toordinal() != first + n - 1:
            raise InputError(f"{chart_id}: range.days disagrees with range.first/last")
        fam = (((self.horizons.get("charts") or {}).get(chart_id) or {}).get("families") or {}).get(family)
        if not fam:
            raise InputError(f"{chart_id}: no {family} horizon in s5_horizons.json")
        hs, he = date.fromisoformat(fam["start"]).toordinal(), date.fromisoformat(fam["end"]).toordinal()
        if hs < first or he > first + n - 1 or he < hs:
            raise InputError(f"{chart_id}: {family} horizon lies outside the timeline range")
        birth = _birth_from_h12(doc.get("horizon_inputs") or {})
        states = {}
        for rid, m in (doc.get("members") or {}).items():
            if m.get("plane") != family:
                continue
            a = runs_to_states(m["runs"], n)
            states[rid] = a[hs - first : he - first + 1].copy()
        t = ChartTimeline(chart_id, birth, hs, he, states)
        t.validate()
        return t

    def timelines(self, family: str, chart_ids: Optional[Sequence[str]] = None) -> List[ChartTimeline]:
        ids = list(chart_ids) if chart_ids is not None else self.admitted()
        return [self.timeline(c, family) for c in ids]


def _birth_from_h12(hi: Mapping[str, Any]) -> int:
    """Birth date ordinal from the engine's ``horizon_start_12y`` (birth + 12 years). A 29 February birth maps to
    28 February at +12 years (engine rule), so it reads back as 28 February: one day, used only for age matching."""
    s = hi.get("horizon_start_12y")
    if not s:
        raise InputError("timeline has no horizon_inputs.horizon_start_12y")
    d = date.fromisoformat(s)
    return date(d.year - 12, d.month, d.day).toordinal()


# ── count_blind ───────────────────────────────────────────────────────────────────────────────────────
def _int(v: str, name: str) -> Optional[int]:
    v = (v or "").strip()
    if v == "":
        return None
    if not v.lstrip("-").isdigit():
        raise InputError(f"{name}: {v!r} is not a decimal integer")
    return int(v)


def _read_csv(path: Path, columns: Sequence[str]) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        if list(rd.fieldnames or []) != list(columns):
            raise InputError(f"{path.name}: columns {rd.fieldnames} are not {list(columns)}")
        return list(rd)


@dataclass
class CountBlind:
    aggregates: List[Dict[str, Any]]
    donors: List[Dict[str, Any]]
    units: List[Dict[str, Any]]
    run_sha256: str
    outputs_sha256: Dict[str, str] = field(default_factory=dict)
    donor_eligibility: List[Dict[str, Any]] = field(default_factory=list)  # v2
    donor_diagnostic: List[Dict[str, Any]] = field(default_factory=list)  # v2


def read_count_blind(cb_dir: str, verify: bool = True) -> CountBlind:
    d = Path(cb_dir)
    run_path = d / "COUNT_BLIND_RUN.json"
    if not run_path.exists():
        raise InputError("COUNT_BLIND_RUN.json missing")
    run = json.loads(run_path.read_text(encoding="utf-8"))
    outs = {Path(k).name: v for k, v in (run.get("outputs_sha256") or {}).items()}
    names = {"agg": "COUNT_BLIND_AGGREGATES.csv", "don": "COUNT_BLIND_DONORS.csv", "uni": "COUNT_BLIND_UNITS.csv",
             "del": "COUNT_BLIND_DONOR_ELIGIBILITY.csv", "ddg": "COUNT_BLIND_DONOR_DIAGNOSTIC.csv"}
    if verify:
        for nm in names.values():
            _verify(d / nm, outs.get(nm), nm)
    agg = []
    for r in _read_csv(d / names["agg"], AGG_TEXT + AGG_INTS):
        row: Dict[str, Any] = {k: r[k] for k in AGG_TEXT}
        for k in AGG_INTS:
            row[k] = _int(r[k], k) or 0
        if row["family"] not in C.FAMILIES or row["set"] not in (SET_PRIMARY, SET_ALL):
            raise InputError(f"aggregates: bad family/set {row['family']!r}/{row['set']!r}")
        agg.append(row)
    don = []
    for r in _read_csv(d / names["don"], DONOR_COLUMNS):
        row = {"threshold": _int(r["threshold"], "threshold"), "family": r["family"], "set": r["set"], "chart_id": r["chart_id"],
               "in_pool": _int(r["in_pool"], "in_pool"), "donors_b": _int(r["donors_b"], "donors_b"), "donors_c": _int(r["donors_c"], "donors_c")}
        if row["in_pool"] not in (0, 1):
            raise InputError("donors: in_pool must be 1 or 0")
        if row["in_pool"] == 1 and (row["donors_b"] is None or row["donors_c"] is None):
            raise InputError("donors: donors_b/donors_c are empty for a chart in the pool")
        don.append(row)
    uni = []
    for r in _read_csv(d / names["uni"], UNIT_COLUMNS):
        uni.append({"threshold": _int(r["threshold"], "threshold"), "family": r["family"], "set": r["set"], "unit_id": r["unit_id"],
                    "n": _int(r["scored_applicable_episodes"], "scored_applicable_episodes") or 0})
    dele = []
    for r in _read_csv(d / names["del"], DONOR_ELIG_COLUMNS):
        row = {"threshold": _int(r["threshold"], "threshold"), "family": r["family"], "set": r["set"], "chart_id": r["chart_id"]}
        for k in DONOR_ELIG_COLUMNS[4:]:
            row[k] = _int(r[k], k)
            if row[k] is None:
                raise InputError(f"donor eligibility: {k} is empty")
        dele.append(row)
    ddg = []
    for r in _read_csv(d / names["ddg"], DONOR_DIAG_COLUMNS):
        if r["check"] not in ("b", "c"):
            raise InputError("donor diagnostic: check must be b or c")
        row = {"threshold": _int(r["threshold"], "threshold"), "family": r["family"], "set": r["set"], "check": r["check"]}
        for k in ("pool_charts", "charts_ge5_donors_m3", "k11_floor_met_m3", "charts_ge5_donors_p2", "k11_floor_met_p2"):
            row[k] = _int(r[k], k)
        if row["k11_floor_met_m3"] not in (0, 1) or row["k11_floor_met_p2"] not in (0, 1):
            raise InputError("donor diagnostic: k11 flags must be 0 or 1")
        row["imputed_cell_share_p2"] = r["imputed_cell_share_p2"].strip()  # 6 decimals as text, or empty
        ddg.append(row)
    return CountBlind(agg, don, uni, sha256_file(run_path), outs, dele, ddg)


def d7_decisions(cb: CountBlind, threshold: int, family: str, set_name: str = SET_PRIMARY) -> Dict[str, Any]:
    """Everything D7 decides from the sealed counts for one candidate threshold and family (v1.2 K4, K5, K8, K11;
    v1.3 L1). The footprint-survival half of D7.2 comes from s7_footprint and is joined by the caller."""
    pool = sorted(r["chart_id"] for r in cb.donors if r["threshold"] == threshold and r["family"] == family and r["set"] == set_name and r["in_pool"] == 1)
    ps = set(pool)
    don = [r for r in cb.donors if r["threshold"] == threshold and r["family"] == family and r["set"] == set_name and r["in_pool"] == 1]
    b_ok = sum(1 for r in don if r["donors_b"] >= C.MIN_ELIGIBLE_DONORS)
    c_ok = sum(1 for r in don if r["donors_c"] >= C.MIN_ELIGIBLE_DONORS)
    scored: Dict[str, int] = {}
    with_opp: Dict[str, int] = {}
    for r in cb.aggregates:
        if r["family"] != family or r["set"] != set_name or r["chart_id"] not in ps or r["direction"] not in C.POLARITY_OF_DIRECTION:
            continue
        scored[r["chart_id"]] = scored.get(r["chart_id"], 0) + r["scored_applicable"]
        with_opp[r["chart_id"]] = with_opp.get(r["chart_id"], 0) + r["scored_with_opposite_applicable"]
    n_scored = sum(scored.values())
    charts_scored = sum(1 for v in scored.values() if v > 0)
    n_dir = sum(with_opp.values())
    charts_dir = sum(1 for v in with_opp.values() if v > 0)
    z25 = sorted(r["unit_id"] for r in cb.units if r["threshold"] == threshold and r["family"] == family and r["set"] == set_name and r["n"] >= C.Z25_MIN_UNIT_EPISODES)
    # v1.5 P1 from count_blind v2's diagnostic, logged before any p-value: P2 for a check if and only if its M3 count
    # misses the K11 floor; the donor counts and floors are then read under the rule that applies
    diag = {r["check"]: r for r in cb.donor_diagnostic if r["threshold"] == threshold and r["family"] == family and r["set"] == set_name}
    rules: Dict[str, str] = {}
    floor_rule: Dict[str, int] = {}
    if set(diag) == {"b", "c"}:
        for k in ("b", "c"):
            rules[k] = "m3" if diag[k]["k11_floor_met_m3"] == 1 else "p2_90"
            floor_rule[k] = diag[k]["charts_ge5_donors_m3"] if rules[k] == "m3" else diag[k]["charts_ge5_donors_p2"]
        b_ok, c_ok = floor_rule["b"], floor_rule["c"]
    return {
        "threshold": threshold,
        "family": family,
        "set": set_name,
        "admitted": pool,
        "episodes_scored_applicable": n_scored,
        "charts_with_scored": charts_scored,
        "counts_ok": bool(n_scored >= C.TESTABLE_MIN_EPISODES and charts_scored >= C.TESTABLE_MIN_CHARTS),
        "donor_charts_b": b_ok,
        "donor_charts_c": c_ok,
        "donor_floor_ok": bool(b_ok >= C.DONOR_FLOOR_CHARTS and c_ok >= C.DONOR_FLOOR_CHARTS),
        "donor_rule_b": rules.get("b", "m3"),
        "donor_rule_c": rules.get("c", "m3"),
        "donor_diagnostic": {k: dict(v) for k, v in diag.items()},
        "dir_episodes": n_dir,
        "dir_charts": charts_dir,
        "dir_testable": bool(n_dir >= C.DIR_MIN_EPISODES and charts_dir >= C.DIR_MIN_CHARTS),
        "z25_units": z25 if len(z25) >= C.Z25_MIN_UNITS else [],
        "a7_ok": bool(len(pool) >= C.MIN_CHARTS_FOR_VERDICT and n_scored >= C.MIN_DASHA_EPISODES_FOR_VERDICT) if family == C.FAMILY_DASHA else None,
    }


def profile_rows(cb: CountBlind, chart_ids: Sequence[str], family: str = C.FAMILY_TRANSIT, set_name: str = SET_PRIMARY) -> List[Tuple[Tuple[str, str, str], ...]]:
    """Per chart, the (area, direction, grade) of its episodes (after trim and merge) for Part F's synthetic placement:
    favourable/unfavourable rows of day or month grade only (mixed episodes are never scored; G3/R are dropped)."""
    per: Dict[str, List[Tuple[str, str, str]]] = {c: [] for c in chart_ids}
    for r in cb.aggregates:
        if r["family"] != family or r["set"] != set_name or r["chart_id"] not in per:
            continue
        g = GRADE_OF_COUNT.get(r["grade"])
        if g is None or r["direction"] not in C.POLARITY_OF_DIRECTION:
            continue
        per[r["chart_id"]].extend([(r["area"], r["direction"], g)] * int(r["episodes"]))
    return [tuple(per[c]) for c in chart_ids]


def donor_rows(cb: CountBlind, threshold: int, family: str, set_name: str = SET_PRIMARY) -> Dict[str, Any]:
    """count_blind v2's donor outputs for one threshold pool, family and set, keyed like ``core.donor_recount``."""
    charts = {r["chart_id"]: {k: r[k] for k in DONOR_ELIG_COLUMNS[4:]} for r in cb.donor_eligibility
              if r["threshold"] == threshold and r["family"] == family and r["set"] == set_name}
    checks = {r["check"]: {k: r[k] for k in DONOR_DIAG_COLUMNS[4:]} for r in cb.donor_diagnostic
              if r["threshold"] == threshold and r["family"] == family and r["set"] == set_name}
    return {"charts": charts, "checks": checks}
