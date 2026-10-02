"""Two-stage freeze verification (SI addendum v1.3 §5).

Stage 1 — configuration freeze, committed BEFORE any extract is generated: `FREEZE_STAGE1_<run_id>.json`.
Stage 2 — extract seal, committed BEFORE any extract is opened for inspection: `FREEZE_STAGE2_<run_id>.json`.

These functions are the refusal the addendum asks for ("the scorer verifies each extract hash against Stage 2 and refuses a
mismatch or a missing record. No measurement without both stages"). A Stage-1 file that still carries a `<<PLACEHOLDER>>`,
whose pre-extract input hashes do not match the files on disk, whose frozen code hashes do not match the code that is
actually running, or whose declared extract command is not the canonical one, is NOT a freeze and nothing runs.
"""
from __future__ import annotations

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
REQUIRED_STAGE1 = (
    "artifact", "run_id", "generation", "status", "amendments_draft", "addendum", "registries_selected", "orb_state",
    "conventions", "code", "extract_generation_command", "extract_generation_args", "cohort", "controls", "thresholds", "rerun_policy", "inputs",
)
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


class FreezeRefused(RuntimeError):
    """The freeze is absent, incomplete, stale or inconsistent; carries every problem found."""

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


def stage1_problems(doc: dict, inputs_root: Path, canonical_command: str,
                    sidecar_root: Path = SIDECAR_ROOT) -> list[str]:
    probs: list[str] = []
    for k in REQUIRED_STAGE1:
        if k not in doc:
            probs.append(f"missing required field {k!r}")
    probs += [f"unfilled placeholder at {p}" for p in _placeholders(doc)]
    if doc.get("status") != "FROZEN":
        probs.append(f"status is {doc.get('status')!r}, not 'FROZEN'")
    conv = doc.get("conventions", {})
    if conv.get("tie_tolerance") != TIE_TOL:
        probs.append(f"tie_tolerance {conv.get('tie_tolerance')!r} != the protocol's {TIE_TOL!r}")
    code = doc.get("code", {})
    for k in ("adapter_commit", "scorer_commit"):
        if not COMMIT_RE.match(str(code.get(k, ""))):
            probs.append(f"code.{k} is not a 40-hex commit id")
    want = code.get("files", {})
    have = code_hashes(sidecar_root)
    for f in FROZEN_CODE_FILES:
        if f not in want:
            probs.append(f"code.files omits {f}")
        elif want[f] != have.get(f):
            probs.append(f"code hash mismatch for {f}: frozen {want[f]}, running {have.get(f)}")
    args = doc.get("extract_generation_args") or {}
    try:
        want_cmd = canonical_command.format(**args)
    except KeyError as exc:
        want_cmd = f"<missing arg {exc}>"
    if doc.get("extract_generation_command") != want_cmd:
        probs.append("extract_generation_command is not the canonical command built from extract_generation_args")
    if args.get("generation") != doc.get("generation"):
        probs.append("extract_generation_args.generation differs from the freeze's generation")
    for name, ent in (doc.get("inputs") or {}).items():
        p = inputs_root / ent.get("path", "")
        if not p.is_file():
            probs.append(f"input {name}: file {ent.get('path')!r} not found under {inputs_root}")
        elif sha256_file(p) != ent.get("sha256"):
            probs.append(f"input {name}: sha256 mismatch (frozen {ent.get('sha256')}, on disk {sha256_file(p)})")
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


if __name__ == "__main__":      # `python3 -m services.gochara_eval.freeze` prints the `code.files` block for the Stage-1 file
    print(json.dumps({"files": code_hashes()}, indent=1))
