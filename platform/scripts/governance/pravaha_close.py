#!/usr/bin/env python3
"""Offline Pravāha close preparation; never completes an item or changes a tracker.

Local row checks and archive byte checks are observations for an independent reviewer.
No subprocess, network, database, credential, Git, or live tracker interface is used.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from string import Template

ROOT = Path(__file__).resolve().parents[3]
REPORT_TEMPLATE = ROOT / "00_ARCHITECTURE/briefs/pravaha/run_records/close/PRAVAHA_CLOSE_REPORT_TEMPLATE_v1_0.md"
ITEMS = ("J-8", "J-8a", "J-8-b63", "J-8-j3")
LINEAGE = {"B6.3": ["A6.2", "A6.3", "B6.1", "B6.2"], "J3": ["B6.3"]}
ARCHIVE_NAMES = ("plan_model.json", "EVENTS.jsonl", "snapshot.json")
FINAL_STATES = {"done", "not_applicable", "superseded"}


class CloseInputError(ValueError):
    """An input cannot support the requested local measurement."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CloseInputError(message)


def nonblank(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def decode(raw: bytes):
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)


def read_object(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    value = decode(raw)
    require(isinstance(value, dict), f"expected JSON object: {path.name}")
    return value, raw


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def indexed(rows, label: str) -> dict:
    require(isinstance(rows, list) and bool(rows), f"{label}: nonempty rows required")
    result = {}
    for row in rows:
        require(isinstance(row, dict) and nonblank(row.get("id")), f"{label}: invalid row id")
        require(row["id"] not in result, f"{label}: duplicate id {row['id']}")
        result[row["id"]] = row
    return result


def disposition_rows(disposition: dict) -> list[dict]:
    require(disposition.get("artifact") == "J0_DISPOSITION" and disposition.get("item") == "J-0c",
            "expected J0_DISPOSITION for J-0c")
    result = []
    for field, identity, prefix in (("pr_dispositions", "pr", "pr"),
                                    ("state_dispositions", "id", "state")):
        rows = disposition.get(field)
        require(isinstance(rows, list) and bool(rows), f"{field}: nonempty rows required")
        for row in rows:
            require(isinstance(row, dict), f"{field}: invalid row")
            value = row.get(identity)
            require((type(value) is int and value > 0) if identity == "pr" else nonblank(value),
                    f"{field}: invalid identity")
            require(row.get("proposal") in {"keep", "merge", "supersede", "salvage", "not-applicable"},
                    f"{field}: invalid proposal")
            result.append({"key": f"{prefix}:{value}", "proposal": row["proposal"],
                           "final_state": None, "evidence": None, "reason": None, "decision": None})
    keys = [row["key"] for row in result]
    require(len(keys) == len(set(keys)), "duplicate J-0 disposition row")
    return result


def source_inputs(args) -> tuple[dict, dict, dict]:
    disposition, disposition_raw = read_object(args.disposition)
    campaign, campaign_raw = read_object(args.campaign_model)
    pravaha, pravaha_raw = read_object(args.pravaha_model)
    originals = indexed(pravaha.get("items"), "Pravāha model")
    for item, deps in LINEAGE.items():
        require(originals.get(item, {}).get("depends_on") == deps, f"inherited lineage changed: {item}")
    current = indexed(campaign.get("items"), "campaign model")
    require(all(item in current for item in ITEMS), "campaign model missing J8 item")
    for item in ITEMS:
        require(isinstance(current[item].get("depends_on"), list) and current[item]["depends_on"],
                f"campaign dependencies missing: {item}")
    sources = {"disposition_sha256": digest(disposition_raw), "campaign_model_sha256": digest(campaign_raw),
               "pravaha_model_sha256": digest(pravaha_raw)}
    return {"schema": "ky.pravaha_close_rows/1", "status": "TEMPLATE_NOT_EVIDENCE",
            "sources": sources, "rows": disposition_rows(disposition)}, current, originals


def load_rows(args) -> tuple[dict, dict, dict]:
    expected, current, originals = source_inputs(args)
    rows, _ = read_object(args.rows)
    require(rows.get("schema") == "ky.pravaha_close_rows/1" and rows.get("status") == "TEMPLATE_NOT_EVIDENCE",
            "expected preparation rows, never an acceptance artifact")
    require(rows.get("sources") == expected["sources"], "source SHA-256 mismatch; regenerate against reviewed inputs")
    supplied = rows.get("rows")
    require(isinstance(supplied, list), "row coverage: rows required")
    keys = [row.get("key") for row in supplied if isinstance(row, dict)]
    require(len(keys) == len(supplied) and all(nonblank(key) for key in keys), "row coverage: invalid key")
    require(len(keys) == len(set(keys)), "duplicate close row")
    require(set(keys) == {row["key"] for row in expected["rows"]}, "J-0 row coverage mismatch")
    proposals = {row["key"]: row["proposal"] for row in expected["rows"]}
    require(all(row.get("proposal") == proposals[row["key"]] for row in supplied), "source proposal changed")
    return rows, current, originals


def check_rows(rows: dict) -> None:
    for row in rows["rows"]:
        state = row.get("final_state")
        require(isinstance(state, str) and state in FINAL_STATES, f"{row['key']}: final state unmeasured or non-terminal")
        require(nonblank(row.get("evidence")), f"{row['key']}: measured evidence required")
        if state != "done":
            require(nonblank(row.get("reason")), f"{row['key']}: explicit disposition reason required")
            require(nonblank(row.get("decision")), f"{row['key']}: disposition decision reference required")


def cell(value) -> str:
    if value is None:
        return "UNMEASURED"
    return str(value).replace("&", "&amp;").replace("|", "&#124;").replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


def render_report(rows: dict, current: dict, originals: dict) -> str:
    table = ["| J-0 key | J-0 proposal (input) | Final state | Measured evidence | Reason | Decision |",
             "|---|---|---|---|---|---|"]
    for row in rows["rows"]:
        table.append("| " + " | ".join(cell(row.get(key)) for key in
                     ("key", "proposal", "final_state", "evidence", "reason", "decision")) + " |")
    lineage = "\n".join(f"- {item} requires: {', '.join(originals[item]['depends_on'])}." for item in LINEAGE)
    gates = "\n".join(f"- {item} requires: {', '.join(current[item]['depends_on'])}." for item in ITEMS)
    pins = "\n".join(f"- {key}: `{value}`" for key, value in rows["sources"].items())
    return Template(REPORT_TEMPLATE.read_text(encoding="utf-8")).substitute(
        source_pins=pins, rows="\n".join(table), lineage=lineage, gates=gates)


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def prepare(args) -> dict:
    rows, current, originals = source_inputs(args)
    report = render_report(rows, current, originals)
    templates = {}
    evidence = {"J-8": ["complete_J0_rows", "J-8a_acceptance", "B6.3_acceptance", "J3_acceptance"],
                "J-8a": ["terminal_pravaha_status", "archive_hashes", "live_write_refusal"],
                "J-8-b63": ["close_report", "CURRENT_STATE", "SESSION_LOG", "validated_SESSION_CLOSE"],
                "J-8-j3": ["B6.3_independent_acceptance"]}
    for item in ITEMS:
        inherited_id = {"J-8-b63": "B6.3", "J-8-j3": "J3"}.get(item)
        templates[item] = {"schema": "ky.pravaha_close_template/1", "status": "TEMPLATE_NOT_EVIDENCE",
                           "item": item, "landing_phase": 12, "depends_on": current[item]["depends_on"],
                           "inherited": ({"item": inherited_id, "depends_on": originals[inherited_id]["depends_on"]}
                                         if inherited_id else None),
                           "sources": rows["sources"], "required_evidence": evidence[item],
                           "prerequisite_evidence": {dep: {"path": None, "sha256": None, "independent_acceptance": None}
                                                     for dep in current[item]["depends_on"]},
                           "artifact_sha256": None, "independent_acceptance": None}
    args.out_dir.mkdir(parents=True, exist_ok=False)
    write_json(args.out_dir / "close_rows.template.json", rows)
    (args.out_dir / "PRAVAHA_CLOSE_REPORT_DRAFT_v1_0.md").write_text(report, encoding="utf-8")
    for item, template in templates.items():
        write_json(args.out_dir / f"{item}.template.json", template)
    return {"status": "TEMPLATE_NOT_EVIDENCE", "rows": len(rows["rows"]), "independent_acceptance": None}


def check_tracker_export(model: dict, snapshot: dict, events_raw: bytes) -> dict:
    items = indexed(model.get("items"), "Pravāha model")
    tracks = snapshot.get("tracks")
    require(isinstance(tracks, list) and tracks, "snapshot coverage: tracks missing")
    rows = []
    for track in tracks:
        require(isinstance(track, dict) and isinstance(track.get("items"), list), "snapshot coverage: invalid track")
        rows.extend(track["items"])
    observed = indexed(rows, "snapshot")
    require(set(observed) == set(items), "snapshot item coverage differs from own tracker model")
    counts = {"done": 0, "not_applicable": 0}
    for item, row in observed.items():
        status = row.get("status")
        require(isinstance(status, str) and status in counts, f"{item}: non-terminal tracker state")
        counts[status] += 1
        require(nonblank(row.get("evidence")) or (status == "done" and items[item].get("done_by") == "join"),
                f"{item}: terminal evidence missing")
        if status == "not_applicable":
            require(nonblank(row.get("detail")), f"{item}: not_applicable reason missing")
        deps = items[item].get("depends_on", [])
        require(isinstance(deps, list) and all(isinstance(dep, str) and dep in items for dep in deps),
                f"{item}: unknown model dependency")
        require(row.get("depends_on") == deps and row.get("deps_open") == [], f"{item}: snapshot dependencies disagree")
        if status == "done":
            allowed = {"done", "not_applicable"} if items[item].get("accepts_not_applicable_dependencies") is True else {"done"}
            require(all(observed[dep].get("status") in allowed for dep in deps), f"{item}: strict dependency remains unmet")
    require(bool(events_raw) and events_raw.endswith(b"\n"), "event log empty or truncated (no final newline)")
    events = []
    for line in events_raw.splitlines():
        try:
            event = decode(line)
            require(isinstance(event, dict) and nonblank(event.get("ts")), "event log timestamp missing")
            datetime.fromisoformat(event["ts"])
        except (ValueError, TypeError, UnicodeError) as exc:
            raise CloseInputError(f"event log malformed: {exc}") from exc
        events.append(event)
    health = snapshot.get("health")
    require(isinstance(health, dict), "snapshot health missing")
    require(health.get("restored_from_disk") is not True, "restored snapshot is not a final capture")
    log = health.get("event_log", {})
    require(isinstance(log, dict) and log.get("exists") is True and type(log.get("malformed")) is int
            and log["malformed"] == 0, "snapshot health: event log missing or malformed")
    require(type(log.get("events")) is int and log["events"] == len(events), "snapshot event count differs from event log")
    require(health.get("last_event_at") == events[-1]["ts"], "snapshot last event differs from event log")
    # tick_errors is retained history (server.py:326), not an unresolved-item
    # predicate. Preserve it in the archive; do not demand history erasure.
    require(not health.get("model_error"), "snapshot health: current model error")
    return counts


def archive_candidate(args) -> dict:
    model, model_raw = read_object(args.pravaha_model)
    snapshot, snapshot_raw = read_object(args.snapshot)
    events_raw = args.events.read_bytes()
    counts = check_tracker_export(model, snapshot, events_raw)
    raw_files = dict(zip(ARCHIVE_NAMES, (model_raw, events_raw, snapshot_raw)))
    for selected in args.material:
        name, separator, source = selected.partition("=")
        require(separator == "=" and safe_material_name(name), "material must be NAME=PATH with a plain filename")
        key = f"material/{name}"
        require(key not in raw_files, f"duplicate material name: {name}")
        raw_files[key] = Path(source).read_bytes()
    manifest = {"schema": "ky.pravaha_archive_candidate/1", "status": "CANDIDATE_NOT_ACCEPTED",
                "files": {name: {"sha256": digest(raw), "bytes": len(raw)} for name, raw in raw_files.items()},
                "observed_terminal_counts": counts, "run_material_inventory_complete": None,
                "live_read_only": None, "independent_acceptance": None}
    args.out_dir.mkdir(parents=True, exist_ok=False)
    if args.material:
        (args.out_dir / "material").mkdir()
    for name, raw in raw_files.items():
        (args.out_dir / name).write_bytes(raw)
    write_json(args.out_dir / "archive.candidate.json", manifest)
    return manifest


def safe_material_name(name: str) -> bool:
    return re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name) is not None


def verify_archive(args) -> dict:
    manifest, _ = read_object(args.archive_dir / "archive.candidate.json")
    require(manifest.get("schema") == "ky.pravaha_archive_candidate/1" and
            manifest.get("status") == "CANDIDATE_NOT_ACCEPTED" and
            manifest.get("run_material_inventory_complete") is None and
            manifest.get("live_read_only") is None and manifest.get("independent_acceptance") is None,
            "expected archive candidate, never an acceptance receipt")
    files = manifest.get("files")
    require(isinstance(files, dict) and set(ARCHIVE_NAMES) <= set(files) and all(
        name in ARCHIVE_NAMES or (name.startswith("material/") and safe_material_name(name[len("material/"):]))
        for name in files), "archive coverage differs or unsafe material path")
    raw_files = {}
    for name in files:
        raw = (args.archive_dir / name).read_bytes()
        require(files[name] == {"sha256": digest(raw), "bytes": len(raw)}, f"archive SHA-256/byte mismatch: {name}")
        raw_files[name] = raw
    model, snapshot = decode(raw_files["plan_model.json"]), decode(raw_files["snapshot.json"])
    require(isinstance(model, dict) and isinstance(snapshot, dict), "archive model/snapshot must be objects")
    counts = check_tracker_export(model, snapshot, raw_files["EVENTS.jsonl"])
    require(manifest.get("observed_terminal_counts") == counts, "archive terminal counts disagree")
    return {"archive_bytes_verified": True, "observed_terminal_counts": counts,
            "live_read_only": None, "independent_acceptance": None}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "render", "check-rows"):
        p = sub.add_parser(command)
        p.add_argument("--disposition", type=Path, required=True)
        p.add_argument("--campaign-model", type=Path, required=True)
        p.add_argument("--pravaha-model", type=Path, required=True)
        p.add_argument("--out-dir" if command == "prepare" else "--rows", type=Path, required=True)
    p = sub.add_parser("archive-candidate")
    for name in ("pravaha-model", "events", "snapshot", "out-dir"):
        p.add_argument(f"--{name}", type=Path, required=True)
    p.add_argument("--material", action="append", default=[], metavar="NAME=PATH",
                   help="explicitly selected runner log/backup/run record; repeatable, no directory traversal")
    p = sub.add_parser("verify-archive")
    p.add_argument("--archive-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare(args)
        elif args.command in ("render", "check-rows"):
            rows, current, originals = load_rows(args)
            if args.command == "render":
                print(render_report(rows, current, originals), end="")
                return 0
            check_rows(rows)
            result = {"local_rows_complete": True, "independent_acceptance": None}
        elif args.command == "archive-candidate":
            result = archive_candidate(args)
        else:
            result = verify_archive(args)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"schema": "ky.pravaha_close_check/1", "error": str(exc), "independent_acceptance": None}))
        return 1
    print(json.dumps({"schema": "ky.pravaha_close_check/1", **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
