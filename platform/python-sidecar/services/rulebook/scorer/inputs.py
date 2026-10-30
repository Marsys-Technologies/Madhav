"""Rule Book scorer - readers for the step-5 and count_blind artefacts, hash-verified before anything is scored.

Formats (conductor, 2026-10-30; count_blind's hash is logged and will not change):

* ``admission-v1_1/timelines/<chart_id>.json``, schema ``admission-v1_1-timeline-1``: run-length member states,
  index 0 = ``range.first``; C2 already applied to daśā members. Family horizons come from
  ``out/s5_horizons.json`` (``charts.<id>.families.<family>.{start,end}``). Every file read is checked against
  ``out/TIMELINES_MANIFEST.json`` (``files``: relative path -> sha256).
* ``COUNT_BLIND_AGGREGATES.csv``, ``COUNT_BLIND_DONORS.csv``, ``COUNT_BLIND_UNITS.csv`` and (count_blind v2, with the
  v3 95%-bar columns) ``COUNT_BLIND_DONOR_ELIGIBILITY.csv``, ``COUNT_BLIND_DONOR_DIAGNOSTIC.csv``: UTF-8, header row,
  decimal integers, empty = not applicable; share columns are 6-decimal strings, EMPTY when there are no donor cells
  (kept empty, never read as 0). Checked against ``COUNT_BLIND_RUN.json`` (``outputs_sha256``: name -> sha256), whose
  ``script_sha256`` must be the count_blind hash logged in COUNT-BLIND-V3-HASHES.

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
# count_blind V3 (COUNT-BLIND-V3-HASHES, supersedes V2; SUR-RB-41/45): the v1.4 M3 / v1.5 P1-P2 donor outputs and the
# v1.5 P3 95%-bar columns, masks only. Exact column order as logged by the conductor.
DONOR_ELIG_COLUMNS = ("threshold", "family", "set", "chart_id", "own_cells", "donors_b_m3", "donors_c_m3", "donors_b_p2", "donors_c_p2",
                      "imputed_cells_b_p2", "imputed_cells_c_p2", "donors_b_p95", "donors_c_p95", "imputed_cells_b_p95", "imputed_cells_c_p95")
DONOR_DIAG_COLUMNS = ("threshold", "family", "set", "check", "pool_charts", "charts_ge5_donors_m3", "k11_floor_met_m3", "charts_ge5_donors_p2",
                      "k11_floor_met_p2", "imputed_cell_share_p2", "charts_ge5_donors_p95", "k11_floor_met_p95", "imputed_cell_share_p95")
DONOR_DIAG_INTS = ("pool_charts", "charts_ge5_donors_m3", "k11_floor_met_m3", "charts_ge5_donors_p2", "k11_floor_met_p2", "charts_ge5_donors_p95", "k11_floor_met_p95")
DONOR_DIAG_FLAGS = ("k11_floor_met_m3", "k11_floor_met_p2", "k11_floor_met_p95")
DONOR_DIAG_SHARES = ("imputed_cell_share_p2", "imputed_cell_share_p95")


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

    def offset_normalised_count(self, chart_ids: Iterable[str]) -> int:
        """SUR-RB-48: how many of these admitted charts were built with OFFSET NORMALISATION (verified offset with
        non-zero seconds: offset rounded to the whole minute, local clock time shifted by the residual, UT identical).
        Read from s6_admit.json (``ledger.<chart_id>.offset_normalised``, true/false, recorded by the admission
        helper), never computed here; a chart without a boolean record refuses."""
        led = (self.admit or {}).get("ledger") or {}
        key = C.S6_OFFSET_NORMALISED_FIELD
        ids = sorted(set(chart_ids))
        bad = [c for c in ids if not isinstance((led.get(c) or {}).get(key), bool)]
        if bad:
            raise InputError(f"s6_admit.json does not record {key} (true/false) for {len(bad)} admitted chart(s) (SUR-RB-48)")
        return sum(1 for c in ids if led[c][key])

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


def _share(v: str, name: str) -> str:
    """A share column as logged: a 6-decimal string in [0, 1], or '' when there are no donor cells. The empty value
    stays empty (it is not a zero share)."""
    v = (v or "").strip()
    if v == "":
        return ""
    head, dot, tail = v.partition(".")
    if not (dot and head.isdigit() and tail.isdigit() and len(tail) == 6) or not (0.0 <= float(v) <= 1.0):
        raise InputError(f"{name}: {v!r} is not a 6-decimal share in [0, 1]")
    return v


def share_value(v: str) -> Optional[float]:
    """The numeric share, or None when the column is empty (no donor cells). Never 0 for empty."""
    return None if v == "" else float(v)


def ledger_entries(ledger_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """The append-only decisions ledger: entry id -> every line with that id, in order."""
    p = Path(ledger_path)
    if not p.exists():
        raise InputError(f"the decisions ledger {p.name} is missing")
    out: Dict[str, List[Dict[str, Any]]] = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if isinstance(d, dict) and d.get("id"):
            out.setdefault(d["id"], []).append(d)
    return out


def single_entry(entries: Mapping[str, List[Dict[str, Any]]], entry_id: str) -> Optional[Dict[str, Any]]:
    """The one logged entry with this id (review VERIFY3 G3): None if absent; refused if two lines with the id differ
    (a later line can never silently replace a logged one)."""
    rows = entries.get(entry_id) or []
    if not rows:
        return None
    first = json.dumps(rows[0], sort_keys=True)
    if any(json.dumps(r, sort_keys=True) != first for r in rows[1:]):
        raise InputError(f"the ledger holds {len(rows)} differing lines with id {entry_id}; refused")
    return rows[0]


def logged_count_blind_hashes(ledger_path: Optional[str] = None) -> Dict[str, str]:
    """count_blind's own script (and tests) sha256 as logged in COUNT-BLIND-V3-HASHES."""
    e = single_entry(ledger_entries(ledger_path or C.LOCK_LEDGER_PATH), C.COUNT_BLIND_HASH_ENTRY)
    if not e or not e.get("sha256"):
        raise InputError(f"ledger entry {C.COUNT_BLIND_HASH_ENTRY} (count_blind's own hash) not found")
    return {"script": e["sha256"], "tests": (e.get("tests") or {}).get("sha256", "")}


@dataclass
class CountBlind:
    aggregates: List[Dict[str, Any]]
    donors: List[Dict[str, Any]]
    units: List[Dict[str, Any]]
    run_sha256: str
    outputs_sha256: Dict[str, str] = field(default_factory=dict)
    donor_eligibility: List[Dict[str, Any]] = field(default_factory=list)  # v2 / v3 columns
    donor_diagnostic: List[Dict[str, Any]] = field(default_factory=list)  # v2 / v3 columns
    script_sha256: str = ""  # count_blind's own hash as named in COUNT_BLIND_RUN.json


def read_count_blind(cb_dir: str, verify: bool = True, ledger_path: Optional[str] = None) -> CountBlind:
    d = Path(cb_dir)
    run_path = d / "COUNT_BLIND_RUN.json"
    if not run_path.exists():
        raise InputError("COUNT_BLIND_RUN.json missing")
    run = json.loads(run_path.read_text(encoding="utf-8"))
    script = str(run.get("script_sha256") or "")
    if verify:  # SUR-RB-45: only a run of the logged count_blind V3 is read
        logged = logged_count_blind_hashes(ledger_path)
        if script != logged["script"]:
            raise InputError(f"COUNT_BLIND_RUN.json names count_blind sha256 {script[:12] or '(none)'}..., not the {C.COUNT_BLIND_HASH_ENTRY} hash {logged['script'][:12]}...")
        if logged["tests"] and run.get("tests_sha256") and run["tests_sha256"] != logged["tests"]:
            raise InputError(f"COUNT_BLIND_RUN.json names count_blind tests sha256 {run['tests_sha256'][:12]}..., not the logged {logged['tests'][:12]}...")
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
        for k in DONOR_DIAG_INTS:
            row[k] = _int(r[k], k)
            if row[k] is None:
                raise InputError(f"donor diagnostic: {k} is empty")
        if any(row[k] not in (0, 1) for k in DONOR_DIAG_FLAGS):
            raise InputError("donor diagnostic: k11 flags must be 0 or 1")
        for k in DONOR_DIAG_SHARES:
            row[k] = _share(r[k], k)  # 6 decimals as text, or '' (no donor cells; not a zero share)
        ddg.append(row)
    return CountBlind(agg, don, uni, sha256_file(run_path), outs, dele, ddg, script)


def d7_decisions(cb: CountBlind, threshold: int, family: str, set_name: str = SET_PRIMARY, escalated: Sequence[str] = ()) -> Dict[str, Any]:
    """Everything D7 decides from the sealed counts for one candidate threshold and family (v1.2 K4, K5, K8, K11;
    v1.3 L1). The footprint-survival half of D7.2 comes from s7_footprint and is joined by the caller.

    ``escalated`` names the checks ("b", "c") whose P2 bar v1.5 P3 raised to 95%: their rule is ``p2_95`` and their
    K11 floor count, floor flag and imputed share are read from the sealed 95% columns (count_blind V3)."""
    pool = sorted(r["chart_id"] for r in cb.donors if r["threshold"] == threshold and r["family"] == family and r["set"] == set_name and r["in_pool"] == 1)
    ps = set(pool)
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
    shares: Dict[str, Optional[float]] = {}
    if set(escalated) - {"b", "c"}:
        raise InputError(f"escalated checks must be b and/or c, not {sorted(escalated)}")
    if set(diag) == {"b", "c"}:
        for k in ("b", "c"):
            rules[k] = "m3" if diag[k]["k11_floor_met_m3"] == 1 else "p2_90"
            if k in escalated:
                if rules[k] != "p2_90":
                    raise InputError(f"check ({k}) meets the K11 floor under M3: v1.5 P3 has no P2 bar to raise")
                rules[k] = "p2_95"
            suffix = {"m3": "m3", "p2_90": "p2", "p2_95": "p95"}[rules[k]]
            floor_rule[k] = diag[k][f"charts_ge5_donors_{suffix}"]
            if diag[k][f"k11_floor_met_{suffix}"] != int(floor_rule[k] >= C.DONOR_FLOOR_CHARTS):
                raise InputError(f"donor diagnostic: check ({k}) k11_floor_met_{suffix} disagrees with charts_ge5_donors_{suffix}")
            shares[k] = None if suffix == "m3" else share_value(diag[k][f"imputed_cell_share_{suffix}"])
        b_ok, c_ok = floor_rule["b"], floor_rule["c"]
    else:  # review VERIFY3 G5: no fallback to the v1 horizon-only donor counts
        raise InputError(f"the count_blind V3 donor diagnostic has no (b) and (c) rows for threshold {threshold}, {family}, {set_name}; refused")
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
        "imputed_share_b": shares.get("b"),  # under the rule that applies; None = M3 or no donor cells (never 0)
        "imputed_share_c": shares.get("c"),
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
    """count_blind V3's donor outputs (v2 columns plus the 95% bar) for one threshold pool, family and set, keyed like ``core.donor_recount``."""
    charts = {r["chart_id"]: {k: r[k] for k in DONOR_ELIG_COLUMNS[4:]} for r in cb.donor_eligibility
              if r["threshold"] == threshold and r["family"] == family and r["set"] == set_name}
    checks = {r["check"]: {k: r[k] for k in DONOR_DIAG_COLUMNS[4:]} for r in cb.donor_diagnostic
              if r["threshold"] == threshold and r["family"] == family and r["set"] == set_name}
    return {"charts": charts, "checks": checks}
