"""Two-stage freeze verification (SI addendum v1.3/v1.4 §5).

Stage 1 — configuration freeze, committed BEFORE any extract is generated: `FREEZE_STAGE1_<run_id>.json`.
Stage 2 — extract seal, committed BEFORE any extract is opened for inspection: `FREEZE_STAGE2_<run_id>.json`.

A Stage-1 file is a freeze only if it is SUBSTANTIVE: a typed schema with every mandatory field present, non-empty and of the
right type; mandatory input identities (a path and a sha256 for each pre-extract input, all verified on disk); no placeholder; the
running-code hashes; the canonical extract command built from typed arguments; and a real manifest ephemeris component that
covers the bodies the run consumes. An empty-but-well-keyed document is refused (Codex R9-8).

The freeze is then BOUND to the run: `bind_scoring_run` compares what `candidate_score` is actually run with (registry, controls,
extract, generation, budget) to the frozen entries; `bind_dump_run` compares what `dump_extract` is actually run with (generation,
Stage-1 path, pinned date, output path) to the frozen command arguments. Any mismatch refuses.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path

from .registry import TIE_TOL

PLACEHOLDER = re.compile(r"<<[^<>]*>>")
SIDECAR_ROOT = Path(__file__).resolve().parents[2]
FROZEN_CODE_FILES = (            # the adapter, scorer and everything they import for the measurement
    "services/gochara_eval/candidate.py", "services/gochara_eval/unknowns.py", "services/gochara_eval/extract.py",
    "services/gochara_eval/metrics.py", "services/gochara_eval/registry.py", "services/gochara_eval/controls.py",
    "services/gochara_eval/freeze.py", "services/gochara_eval/dump_extract.py", "services/gochara_eval/candidate_score.py",
)
CANDIDATE_GENERATIONS = ("4.1",)
#: the pre-extract inputs whose identity (path + sha256) every freeze MUST carry — fixed identifiers, not free text
REQUIRED_INPUTS = (
    "event_registry", "random_controls", "baseline_3_0_extract", "scorer_3_0", "recorded_result_3_0", "recorded_per_event_3_0",
    "evaluation_protocol", "si_addendum", "bounds_model", "design_specs", "test_oracles", "amendments_draft",
)
#: bodies whose Swiss ephemeris files the '4.1' run consumes: the eight persisted bodies AND the Moon (the windows projection
#: and class context read it; it is on-demand, never persisted, but it is still consumed)
REQUIRED_CONSUMED_BODIES = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu")
THRESHOLD_KEYS = ("t_cover", "t_time", "t_rank", "t_fp_adverse", "t_fp_gain", "t_honesty", "random_controls")
CONVENTION_KEYS = ("si_mapping", "utc_to_ist", "merge_implementation", "stored_value_precision", "tie_grouping", "candidate_set")
COHORT_INT_KEYS = ("held_out", "timing_usable", "year_grain", "exact_cohort", "interval_grain")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
DEFAULT_ENUMERATION_BUDGET = 400_000


class FreezeRefused(RuntimeError):
    """The freeze is absent, incomplete, stale, inconsistent or does not match the run; carries every problem found."""

    def __init__(self, problems: list[str]):
        super().__init__("FREEZE REFUSED: " + "; ".join(problems))
        self.problems = problems


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _placeholders(node, where: str = "$") -> list[str]:
    if isinstance(node, str):
        return [f"{where}: {m}" for m in PLACEHOLDER.findall(node)]
    if isinstance(node, dict):
        return [p for k, v in node.items() for p in _placeholders(v, f"{where}.{k}")]
    if isinstance(node, list):
        return [p for i, v in enumerate(node) for p in _placeholders(v, f"{where}[{i}]")]
    return []


def code_hashes(sidecar_root: Path = SIDECAR_ROOT) -> dict[str, str]:
    return {f: sha256_file(sidecar_root / f) for f in FROZEN_CODE_FILES if (sidecar_root / f).exists()}


# ---- the AM-16 ephemeris component (the ONE definition shared with '5.0') -----------------------------------------------------
EPHEMERIS_KEYS = ("backend", "swe_version", "library_sha256", "platform", "files", "probe_digest")
_SE1 = re.compile(r"^se([a-z]+)_([0-9]{2})\.se1$")


def ephemeris_component_problems(c) -> list[str]:
    """Why this manifest ephemeris component does NOT identify the ephemeris that was used ([] = it does)."""
    if not isinstance(c, dict):
        return ["no `ephemeris` component in the manifest input vector (the vector predates AM-16)"]
    probs = [f"ephemeris component lacks key {k!r}" for k in EPHEMERIS_KEYS if k not in c]
    extra = sorted(set(c) - set(EPHEMERIS_KEYS))
    if extra:
        probs.append(f"ephemeris component has keys outside the AM-16 definition: {extra}")
    if c.get("backend") != "swieph":
        probs.append(f"backend is {c.get('backend')!r}, not 'swieph' (a Moshier/analytic fallback is not an identified ephemeris)")
    if not c.get("swe_version"):
        probs.append("swe_version is empty")
    for k in ("library_sha256", "probe_digest"):
        if k in c and not SHA64.match(str(c[k])):
            probs.append(f"{k} is not a sha256")
    if "platform" in c and not c["platform"]:
        probs.append("platform is empty")
    files = c.get("files")
    if "files" in c:
        if not isinstance(files, dict) or not files:
            probs.append("files is empty — no opened .se1 file is recorded (a Moshier-served build opens none)")
        else:
            for name, sha in files.items():
                if not _SE1.match(str(name)):
                    probs.append(f"files: {name!r} is not a Swiss ephemeris .se1 file name")
                if not SHA64.match(str(sha)):
                    probs.append(f"files: {name!r} has no sha256")
    return probs


def required_ephemeris_files(bodies: list[str], first_year: int, last_year: int) -> set[str]:
    """The Swiss ephemeris files a run over [first_year, last_year] consumes: planetary `sepl_NN` for every body but the Moon and
    lunar `semo_NN` for the Moon, one per 600-year block (NN = block start / 100: 1800-2399 -> 18)."""
    names = set()
    for y_block in range(first_year // 600, last_year // 600 + 1):
        nn = f"{y_block * 6:02d}"
        if any(b != "Moon" for b in bodies):
            names.add(f"sepl_{nn}.se1")
        if "Moon" in bodies:
            names.add(f"semo_{nn}.se1")
    return names


def ephemeris_coverage_problems(component: dict, consumed_bodies, horizon) -> list[str]:
    """Does the component's opened-file census cover every body the run consumes over the horizon? (incl. the Moon)"""
    probs: list[str] = []
    if not isinstance(consumed_bodies, list) or not all(isinstance(b, str) for b in consumed_bodies):
        return ["consumed_bodies is not a list of body names"]
    missing_bodies = [b for b in REQUIRED_CONSUMED_BODIES if b not in consumed_bodies]
    if missing_bodies:
        probs.append(f"consumed_bodies omits {missing_bodies} (the run consumes the eight persisted bodies and the Moon)")
    try:
        y0 = dt.date.fromisoformat(horizon["start"]).year
        y1 = dt.date.fromisoformat(horizon["end"]).year
    except Exception:  # noqa: BLE001
        return probs + ["ephemeris horizon {start,end} is missing or not ISO dates"]
    files = component.get("files") if isinstance(component, dict) else None
    if isinstance(files, dict):
        need = required_ephemeris_files(list(consumed_bodies), y0, y1)
        lacking = sorted(need - set(files))
        if lacking:
            probs.append(f"the opened-file census lacks {lacking} (consumed bodies {sorted(consumed_bodies)}, years {y0}-{y1})")
    return probs


# ---- the typed Stage-1 schema -----------------------------------------------------------------------------------------------
def _ne_str(x) -> bool:
    return isinstance(x, str) and bool(x.strip())


def _is_iso_date(x) -> bool:
    try:
        dt.date.fromisoformat(str(x))
        return isinstance(x, str)
    except ValueError:
        return False


def _dict(doc: dict, key: str, probs: list[str], where: str = "") -> dict:
    v = doc.get(key)
    if not isinstance(v, dict) or not v:
        probs.append(f"{where}{key} is missing, not an object, or empty")
        return {}
    return v


def _str_fields(d: dict, keys, probs: list[str], where: str) -> None:
    for k in keys:
        if not _ne_str(d.get(k)):
            probs.append(f"{where}.{k} is missing or empty")


def stage1_problems(doc: dict, inputs_root: Path, canonical_command: str,
                    sidecar_root: Path = SIDECAR_ROOT) -> list[str]:
    probs: list[str] = []
    if not isinstance(doc, dict):
        return ["the freeze is not a JSON object"]
    probs += [f"unfilled placeholder at {p}" for p in _placeholders(doc)]
    if doc.get("artifact") != "FREEZE_STAGE1":
        probs.append("artifact is not 'FREEZE_STAGE1'")
    if not _ne_str(doc.get("run_id")) or not re.fullmatch(r"[A-Za-z0-9_.-]+", str(doc.get("run_id", ""))):
        probs.append("run_id is missing or not a plain identifier")
    if doc.get("generation") not in CANDIDATE_GENERATIONS:
        probs.append(f"generation {doc.get('generation')!r} is not a measurable candidate generation {CANDIDATE_GENERATIONS}")
    if doc.get("status") != "FROZEN":
        probs.append(f"status is {doc.get('status')!r}, not 'FROZEN'")

    ad = _dict(doc, "amendments_draft", probs)
    _str_fields(ad, ("version",), probs, "amendments_draft")
    add = _dict(doc, "addendum", probs)
    _str_fields(add, ("artifact", "version"), probs, "addendum")
    reg_sel = _dict(doc, "registries_selected", probs)
    _str_fields(reg_sel, ("event_registry", "governed_registry_rows"), probs, "registries_selected")

    conv = _dict(doc, "conventions", probs)
    _str_fields(conv, CONVENTION_KEYS, probs, "conventions")
    if conv.get("tie_tolerance") != TIE_TOL:
        probs.append(f"conventions.tie_tolerance {conv.get('tie_tolerance')!r} != the protocol's {TIE_TOL!r}")
    hz = conv.get("horizon")
    if not (isinstance(hz, dict) and _ne_str(hz.get("scored")) and _ne_str(hz.get("extract_assertion"))):
        probs.append("conventions.horizon needs non-empty `scored` and `extract_assertion`")

    cohort = _dict(doc, "cohort", probs)
    for k in COHORT_INT_KEYS:
        if not (isinstance(cohort.get(k), int) and not isinstance(cohort.get(k), bool) and cohort[k] >= 0):
            probs.append(f"cohort.{k} is missing or not a non-negative integer")
    if not UUID_RE.match(str(cohort.get("chart_id", ""))):
        probs.append("cohort.chart_id is not a UUID")
    if isinstance(cohort.get("held_out"), int) and isinstance(cohort.get("timing_usable"), int) \
            and isinstance(cohort.get("year_grain"), int) and cohort["held_out"] != cohort["timing_usable"] + cohort["year_grain"]:
        probs.append("cohort: held_out != timing_usable + year_grain")

    ctl = _dict(doc, "controls", probs)
    _str_fields(ctl, ("file", "experiment", "rule"), probs, "controls")
    if not (isinstance(ctl.get("seed"), int) and not isinstance(ctl.get("seed"), bool)):
        probs.append("controls.seed is missing or not an integer")
    thr = _dict(doc, "thresholds", probs)
    _str_fields(thr, THRESHOLD_KEYS, probs, "thresholds")
    tc = _dict(doc, "tolerances_and_conversions", probs)
    if tc.get("tie_tolerance") != TIE_TOL:
        probs.append("tolerances_and_conversions.tie_tolerance != the protocol's tolerance")
    bud = tc.get("enumeration_budget")
    if not (isinstance(bud, int) and not isinstance(bud, bool) and bud > 0):
        probs.append("tolerances_and_conversions.enumeration_budget is missing or not a positive integer")
    _str_fields(tc, ("percentile", "timezone", "budget_exceeded"), probs, "tolerances_and_conversions")
    if not _ne_str(doc.get("rerun_policy")):
        probs.append("rerun_policy is missing or empty")
    if not _ne_str(doc.get("coverage_manifest")):
        probs.append("coverage_manifest is missing or empty (state UNVERIFIABLE explicitly)")

    # ---- the ephemeris requirement: a REAL component, covering the bodies and years the run consumes ----
    er = _dict(doc, "ephemeris_requirement", probs)
    rb = er.get("manifest_readback")
    if not isinstance(rb, dict) or not rb:
        probs.append("ephemeris_requirement.manifest_readback is missing — the real manifest read-back object is required")
    else:
        comp = rb.get("ephemeris")
        probs += [f"ephemeris_requirement: {p}" for p in ephemeris_component_problems(comp)]          # RE-DERIVED, never trusted
        if rb.get("ephemeris_problems") not in (None, []):
            probs.append("ephemeris_requirement.manifest_readback.ephemeris_problems is not empty")
        if not (isinstance(rb.get("orb_max_deg"), (int, float)) and not isinstance(rb.get("orb_max_deg"), bool)
                and rb["orb_max_deg"] > 0):
            probs.append("ephemeris_requirement.manifest_readback.orb_max_deg is missing or not a positive number")
        _str_fields(rb, ("orb_ruling", "manifest_status"), probs, "ephemeris_requirement.manifest_readback")
        if isinstance(comp, dict):
            probs += [f"ephemeris_requirement: {p}" for p in
                      ephemeris_coverage_problems(comp, er.get("consumed_bodies"), er.get("horizon"))]
    ostate = _dict(doc, "orb_state", probs)
    _str_fields(ostate, ("text", "manifest_location"), probs, "orb_state")

    code = _dict(doc, "code", probs)
    for k in ("adapter_commit", "scorer_commit"):
        if not COMMIT_RE.match(str(code.get(k, ""))):
            probs.append(f"code.{k} is not a 40-hex commit id")
    want = code.get("files") if isinstance(code.get("files"), dict) else {}
    have = code_hashes(sidecar_root)
    for f in FROZEN_CODE_FILES:
        if f not in want:
            probs.append(f"code.files omits {f}")
        elif want[f] != have.get(f):
            probs.append(f"code hash mismatch for {f}: frozen {want[f]}, running {have.get(f)}")

    args = doc.get("extract_generation_args")
    if not (isinstance(args, dict) and all(_ne_str(args.get(k)) for k in ("generation", "stage1", "pinned_at", "out"))):
        probs.append("extract_generation_args needs non-empty generation, stage1, pinned_at, out")
        args = {}
    else:
        if not _is_iso_date(args["pinned_at"]):
            probs.append("extract_generation_args.pinned_at is not an ISO date")
        if args["generation"] != doc.get("generation"):
            probs.append("extract_generation_args.generation differs from the freeze's generation")
        if doc.get("extract_generation_command") != canonical_command.format(**args):
            probs.append("extract_generation_command is not the canonical command built from extract_generation_args")
    if not _ne_str(doc.get("extract_environment")):
        probs.append("extract_environment is missing or empty")

    inputs = doc.get("inputs")
    if not isinstance(inputs, dict):
        probs.append("inputs is missing or not an object")
        inputs = {}
    for name in REQUIRED_INPUTS:
        ent = inputs.get(name)
        if not (isinstance(ent, dict) and _ne_str(ent.get("path")) and SHA64.match(str(ent.get("sha256", "")))):
            probs.append(f"inputs.{name} needs a path and a sha256 (mandatory input identity)")
            continue
        p = inputs_root / ent["path"]
        if not p.is_file():
            probs.append(f"input {name}: file {ent['path']!r} not found under {inputs_root}")
        elif sha256_file(p) != ent["sha256"]:
            probs.append(f"input {name}: sha256 mismatch (frozen {ent['sha256']}, on disk {sha256_file(p)})")
    for name in inputs:
        if name not in REQUIRED_INPUTS:
            probs.append(f"inputs.{name} is not a known input identifier (known: {list(REQUIRED_INPUTS)})")
    return probs


def require_stage1(stage1_path: str | Path, inputs_root: str | Path, canonical_command: str,
                   sidecar_root: Path = SIDECAR_ROOT) -> dict:
    p = Path(stage1_path)
    if not p.is_file():
        raise FreezeRefused([f"Stage-1 freeze file {p} does not exist"])
    doc = json.loads(p.read_text())
    probs = stage1_problems(doc, Path(inputs_root), canonical_command, sidecar_root)
    if probs:
        raise FreezeRefused(probs)
    return doc


def require_stage2(stage2_path: str | Path, stage1_path: str | Path, stage1_doc: dict, extract_path: str | Path) -> dict:
    p = Path(stage2_path)
    if not p.is_file():
        raise FreezeRefused([f"Stage-2 seal file {p} does not exist — no measurement without both stages"])
    doc = json.loads(p.read_text())
    probs = [f"unfilled placeholder at {x}" for x in _placeholders(doc)]
    if doc.get("run_id") != stage1_doc.get("run_id"):
        probs.append("Stage-2 run_id differs from Stage-1")
    if doc.get("stage1_sha256") != sha256_file(stage1_path):
        probs.append("Stage-2 does not seal THIS Stage-1 file (stage1_sha256 differs)")
    ent = (doc.get("extracts") or {}).get(Path(extract_path).name)
    if ent is None:
        probs.append(f"Stage-2 has no record for extract {Path(extract_path).name}")
    elif ent.get("sha256") != sha256_file(extract_path):
        probs.append(f"extract sha256 {sha256_file(extract_path)} differs from the sealed {ent.get('sha256')}")
    if probs:
        raise FreezeRefused(probs)
    return doc


# ---- binding the freeze to what is ACTUALLY run -----------------------------------------------------------------------------
def bind_scoring_run(doc: dict, inputs_root: Path, *, registry_path, controls_path, extract_path, extract_header_predicate: str,
                     registry_held_out: int, budget: int | None) -> list[str]:
    """What `candidate_score` is actually run with must be what the freeze names. Returns the problems ([] = bound)."""
    probs: list[str] = []
    inputs = doc.get("inputs", {})

    def same_file(actual, name):
        ent = inputs.get(name, {})
        if actual is None:
            probs.append(f"no {name} supplied (a measurement needs the frozen one)")
        elif not Path(actual).is_file():
            probs.append(f"{name} {actual} does not exist")
        elif sha256_file(actual) != ent.get("sha256"):
            probs.append(f"the actual {name} ({Path(actual).name}, sha256 {sha256_file(actual)}) is not the frozen one "
                         f"({ent.get('path')}, {ent.get('sha256')})")
        elif Path(actual).name != Path(ent.get("path", "")).name:
            probs.append(f"the actual {name} file name {Path(actual).name!r} differs from the frozen {Path(ent.get('path', '')).name!r}")

    same_file(registry_path, "event_registry")
    same_file(controls_path, "random_controls")
    if controls_path and Path(controls_path).name != doc.get("controls", {}).get("file"):
        probs.append("the controls file name differs from controls.file")
    gen = doc.get("generation")
    if f"generation='{gen}'" not in str(extract_header_predicate):
        probs.append(f"the extract's header predicate {extract_header_predicate!r} does not name generation {gen!r}")
    out = doc.get("extract_generation_args", {}).get("out", "")
    if Path(extract_path).name != Path(out).name:
        probs.append(f"the extract file {Path(extract_path).name!r} is not the frozen output {Path(out).name!r}")
    if registry_held_out != doc.get("cohort", {}).get("held_out"):
        probs.append(f"the registry holds {registry_held_out} held-out events, the freeze's cohort says "
                     f"{doc.get('cohort', {}).get('held_out')}")
    frozen_budget = doc.get("tolerances_and_conversions", {}).get("enumeration_budget", DEFAULT_ENUMERATION_BUDGET)
    actual_budget = DEFAULT_ENUMERATION_BUDGET if budget is None else budget
    if actual_budget != frozen_budget:
        probs.append(f"the enumeration budget {actual_budget} is not the frozen {frozen_budget}")
    return probs


def bind_dump_run(doc: dict, *, generation: str, stage1: str, pinned_at: str | None, out: str | None) -> list[str]:
    """What `dump_extract` is actually run with must be the frozen command arguments."""
    frozen = doc.get("extract_generation_args", {})
    probs: list[str] = []
    for k, actual in (("generation", generation), ("pinned_at", pinned_at), ("out", out)):
        if actual != frozen.get(k):
            probs.append(f"--{k.replace('_', '-')} {actual!r} is not the frozen {frozen.get(k)!r}")
    if Path(stage1).name != Path(frozen.get("stage1", "")).name:
        probs.append(f"--stage1 {Path(stage1).name!r} is not the frozen {Path(frozen.get('stage1', '')).name!r}")
    return probs


if __name__ == "__main__":      # `python3 -m services.gochara_eval.freeze` prints the `code.files` block for the Stage-1 file
    print(json.dumps({"files": code_hashes()}, indent=1))
