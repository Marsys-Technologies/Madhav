"""J5Q report assembly from pinned, independently scored artifacts; offline only.

The manifest and identity declarations are evidence to review, not authenticated
reviewer receipts. This module never scores held-out items, verifies acceptance,
connects to a DB, publishes a generation or computes flip eligibility.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from uuid import UUID

from .n4_reader import DEFER_HEADER
from .qualification import endpoint_records, engineering_diagnostics, record

GENERATIONS = ("3.0", "4.1", "5.0")
PREREQUISITES = ["J-4f", "A5.6", "B5.3", "B4.3", "B4.4", "independent_seal_verification", "independent_acceptance"]


def _identity(value) -> str:
    return value.strip().casefold() if isinstance(value, str) else ""


def _read(entry: dict, root: Path) -> dict:
    path = Path(entry["path"])
    if path.is_absolute() or ".." in path.parts or ":" in str(path):
        raise ValueError("source path must be relative to the input bundle")
    target = (root / path).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError("source path escapes the input bundle")
    raw = target.read_bytes()
    if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
        raise ValueError(f"sha256 mismatch for {path}")
    doc = json.loads(raw)
    if not isinstance(doc, dict):
        raise ValueError(f"{path} is not an object")
    return doc


def _matches_identity(doc: dict, chart: str, generation: str) -> bool:
    if "chart_id" in doc or "generation" in doc:
        return doc.get("chart_id") == chart and doc.get("generation") == generation
    # Historical 3.0/4.1 dump header; exact predicate rather than a substring.
    return bool(re.fullmatch(
        r"(?:public\.)?(?:kala_gochara_windows|ka_gochara_eval_window) where chart_id='"
        + re.escape(chart) + "' and generation='" + re.escape(generation) + "'", str(doc.get("predicate", ""))))


def _disclosure(source: dict, key: str, data=None) -> dict:
    data = source.get(key) if data is None else data
    entry = record("pass" if isinstance(data, dict) and data else "insufficient_evidence", data,
                   "protocol §10 mandatory non-gating disclosure; source content transcribed, not causal verification")
    if key == "path_ablations":
        entry["missing_paths"] = [p for p in ("P1", "P2", "P3", "P4", "P5", "P6")
                                  if not isinstance(data, dict) or not data.get(p)]
        if entry["missing_paths"]:
            entry["status"] = "insufficient_evidence"
    return entry


def _read_ablations(ent: dict, root: Path, chart: str, gen: str) -> tuple[dict, dict]:
    """The pinned `ky.path_ablations/1` output of `path_ablation.py` for this source: its identity must be this chart, this generation and the
    very extract the source scored (a different extract's ablations are not this generation's). Returns (per-path records, run descriptor)."""
    data = _read(ent["path_ablations"], root)
    if data.get("schema") != "ky.path_ablations/1" or data.get("chart_id") != chart or data.get("generation") != gen:
        raise ValueError("path_ablations identity or schema mismatch")
    if data.get("base", {}).get("extract_sha256") != ent["extract"]["sha256"]:
        raise ValueError("path_ablations did not ablate this source's extract")
    if not isinstance(data.get("paths"), dict):
        raise ValueError("path_ablations carries no per-path records")
    return data["paths"], {k: data.get(k) for k in ("mode", "non_gating", "enumeration_budget", "limits")} | {
        "reproduces_recorded_result": data["base"].get("reproduces_recorded_result")}


def assemble(doc: dict, root: Path) -> dict:
    if doc.get("schema") != "ky.qualification_inputs/1":
        raise ValueError("unknown inputs schema")
    chart = doc["chart_id"]
    UUID(chart)
    authors = doc.get("generation_authors")
    if (not isinstance(authors, list) or not authors or any(not _identity(a) for a in authors)):
        raise ValueError("generation_authors must enumerate every generation author")
    sources = doc.get("sources")
    if not isinstance(sources, dict) or set(sources) - set(GENERATIONS):
        raise ValueError("sources must be keyed by 3.0, 4.1, 5.0 only")
    generations = {}
    for gen in GENERATIONS:
        ent = sources.get(gen)
        source = {}
        if ent is not None:
            scorer = _identity(ent.get("scorer_id"))
            if not scorer or scorer in {_identity(a) for a in authors}:
                raise ValueError("independent scorer required; no generation author may score held-out items")
            source = _read(ent, root)
            if source.get("generation", gen) != gen:
                raise ValueError("source generation identity mismatch")
            if source.get("protocol") != "EVALUATION_PROTOCOL_v2_3":
                raise ValueError("source protocol mismatch")
            if source.get("input_adapter", {}).get("status") != "PASS":
                raise ValueError("source input adapter is not PASS")
            if gen != "3.0" and (source.get("mode") != "MEASUREMENT"
                                   or source.get("freeze", {}).get("status") != "VERIFIED"):
                raise ValueError("candidate source requires a frozen MEASUREMENT")
            extract = _read(ent["extract"], root)
            if not _matches_identity(extract, chart, gen):
                raise ValueError("source extract identity mismatch")
            sha = source.get("extract_sha256", {})
            if (sha.get("measured") != ent["extract"]["sha256"] or sha.get("match") is not True
                    or sha.get("declared_pin") != ent["extract"]["sha256"]):
                raise ValueError("source extract digest is not the scorer's measured, declared pin")
        ablations, run = source.get("path_ablations"), None
        if ent is not None and ent.get("path_ablations") is not None:
            ablations, run = _read_ablations(ent, root, chart, gen)
        disclosure = _disclosure(source, "path_ablations", ablations)
        if run is not None:
            disclosure["run"] = run
        generations[gen] = {"endpoints": endpoint_records(source), "source_result": source or None,
                            "mechanism_attribution": _disclosure(source, "mechanism_attribution"),
                            "path_ablations": disclosure}
    rows, cells = [], None
    for key in ("diagnostic_extract", "coverage_cells"):
        if key not in doc:
            continue
        data = _read(doc[key], root)
        if not _matches_identity(data, chart, "5.0"):
            raise ValueError(f"{key} identity mismatch")
        if key == "diagnostic_extract":
            rows = data["rows"]
        else:
            cells = data["cells"]
    return {"schema": "ky.qualification_preparation/1", "header": DEFER_HEADER, "build_state": "built_waiting_on_gate",
            "chart_id": chart, "protocol": "EVALUATION_PROTOCOL_v2_3", "si_addendum": "1.5",
            "generation_authors": authors, "sources": sources,
            "diagnostic_sources": {k: doc[k] for k in ("diagnostic_extract", "coverage_cells") if k in doc},
            "generations": generations, "engineering_diagnostics": engineering_diagnostics(rows, cells),
            "pending_prerequisites": list(PREREQUISITES),
            "limits": "single chart; held-out means not used for calibration, not unseen; authors read the LEL; "
                      "per-mechanism attribution and per-path ablations are non-gating diagnostics; scores are the tuning baseline; "
                      "this report is neither independent acceptance nor authority to flip"}


def render_markdown(result: dict) -> str:
    lines = ["# J5Q qualification preparation", "", f"**{result['header']}**", "", "State: **built, waiting on gate**.", "", result["limits"], "",
             "Missing evidence retains a null measured value. Original scorer statuses and all measured fields are retained below.", ""]
    for gen, data in result["generations"].items():
        lines += [f"## Generation {gen}", "", "| Endpoint | Status |", "|---|---|"]
        lines += [f"| {name} | {entry['status']} |" for name, entry in data["endpoints"].items()]
        lines += ["", "```json", json.dumps(data, indent=2, sort_keys=True, allow_nan=False), "```", ""]
    lines += ["## Engineering diagnostics (independent gates still pending)", "", "```json",
              json.dumps(result["engineering_diagnostics"], indent=2, sort_keys=True, allow_nan=False), "```", "",
              "Pending prerequisites: " + ", ".join(result["pending_prerequisites"]), ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inputs", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--markdown")
    args = ap.parse_args(argv)
    try:
        manifest_path = Path(args.inputs).resolve()
        manifest_raw = manifest_path.read_bytes()
        doc = json.loads(manifest_raw)
        result = assemble(doc, manifest_path.parent)
        result["inputs_manifest_sha256"] = hashlib.sha256(manifest_raw).hexdigest()
        protected = {manifest_path}
        for ent in list(doc["sources"].values()) + [doc[k] for k in ("diagnostic_extract", "coverage_cells") if k in doc]:
            protected.add((manifest_path.parent / ent["path"]).resolve())
            if "extract" in ent:
                protected.add((manifest_path.parent / ent["extract"]["path"]).resolve())
            if ent.get("path_ablations"):
                protected.add((manifest_path.parent / ent["path_ablations"]["path"]).resolve())
        outputs = [Path(p).resolve() for p in (args.output, args.markdown) if p]
        if len(set(outputs)) != len(outputs) or any(p in protected for p in outputs):
            raise ValueError("outputs must differ from each other and every pinned input")
        payload = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
        markdown = render_markdown(result) if args.markdown else None
        Path(args.output).write_text(payload)
        if args.markdown:
            Path(args.markdown).write_text(markdown)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"qualification report refused: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
