#!/usr/bin/env python3
"""Deterministic offline J-0c acceptance; no writes, git, network or subprocesses.

Source citations below are 1-based. M = 00_ARCHITECTURE/control/kalayantra/plan_model.json;
D = /Users/Dev/kalayantra/run/J0_DISPOSITION.json (v1.1);
S = /Users/Dev/kalayantra/run/J0_STATE_INVENTORY.json;
C = 00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md.
A1/A2/A3 are the cockpit rulings in job KV3-B4-ACCEPT-J-0c's second-job prompt.
Acceptance is limited to the checks documented in README.md and ACCEPT_REPORT.md.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

SHA256 = re.compile(r"[0-9a-fA-F]{64}\Z")
COMMIT = re.compile(r"[0-9a-fA-F]{7,40}\Z")
PROPOSALS = {"keep", "merge", "supersede", "salvage", "not-applicable"}

# /Users/Dev/kalayantra/run/J0_DISPOSITION.json:23,77,83,87-88; corroborated by the inherited model:
# /Users/Dev/kalayantra/wt/campaign/00_ARCHITECTURE/control/pravaha/plan_model.json:
# 830-838,1293-1297,1445-1447,1458-1459. Preserve each named edge; additions are allowed.
SOURCE_DEPENDENCIES = {
    "A5.6": {"A5.5", "N-CLOUD", "A5.5i", "A5.5j", "A5.5k", "A5.5l", "N-G9", "A5.5m"},
    "B5.4": {"B5.3", "A5.6", "B4.3", "B4.4"},
    "J2": {"A5.7", "B5.4"}, "J3": {"B6.3"},
}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def integer(value):
    return type(value) is int


class InputUnknown(Exception):
    def __init__(self, code, row, detail):
        self.violation = {"code": code, "row": row, "detail": detail}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON member: {key}")
        result[key] = value
    return result


def read_json(path):
    # 00_ARCHITECTURE/control/kalayantra/plan_model.json:7042-7043,7064,7069; /Users/Dev/kalayantra/run/J0_DISPOSITION.json:8-9. Unknown input never earns §N.8 acceptance.
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise InputUnknown("input_unreadable", str(path), str(exc)) from exc
    try:
        data = json.loads(raw, object_pairs_hook=unique_object,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        if not isinstance(data, dict):
            raise ValueError("expected a JSON object")
    except (ValueError, UnicodeError) as exc:
        raise InputUnknown("input_invalid", str(path), str(exc)) from exc
    return data, raw


def inventory_ids(data, key, field, numeric=False):
    # A1; 00_ARCHITECTURE/control/kalayantra/plan_model.json:6982,7022,7064; actual inventory shapes: /Users/Dev/kalayantra/run/J0_STATE_INVENTORY.json:15-23 and PR inventory prs[].number.
    rows = data.get(key)
    if not isinstance(rows, list):
        raise InputUnknown("input_invalid", key, "inventory class must be a list")
    ids = []
    for row in rows:
        value = row.get(field) if isinstance(row, dict) else None
        if not (integer(value) and value > 0 if numeric else nonempty(value)):
            raise InputUnknown("input_invalid", key, f"invalid inventory {field}")
        ids.append(value)
    if len(set(ids)) != len(ids):
        raise InputUnknown("input_invalid", key, "inventory has duplicate identities")
    return set(ids)


def class_counts(state):
    # A1; /Users/Dev/kalayantra/run/J0_STATE_INVENTORY.json:24-44. (I) INTERPRETATION: every record counts, including inactive/released holds.
    counts = {}
    for key in ("decisions", "sealed_decisions"):
        if not isinstance(state.get(key), list) or not all(isinstance(r, dict) for r in state[key]):
            raise InputUnknown("input_invalid", key, "inventory class must be a list of records")
        counts[key] = len(state[key])
    holds = state.get("holds")
    if (not isinstance(holds, dict) or not isinstance(holds.get("tracker_global"), dict)
            or not isinstance(holds.get("operational"), list)
            or not all(isinstance(r, dict) for r in holds["operational"])):
        raise InputUnknown("input_invalid", "holds", "expected tracker_global record and operational list")
    counts["holds"] = 1 + len(holds["operational"])
    return counts


def reference_checks(text, row, prs, repo, add):
    # A2; 00_ARCHITECTURE/control/kalayantra/plan_model.json:7065; /Users/Dev/kalayantra/run/J0_DISPOSITION.json:26-62 (head/evidence),55,61 (PR references),65-91 (state evidence).
    # (I) INTERPRETATION: explicit PR/#/pull references, labeled commits or bare hex tokens,
    # and slash paths / filename-extension tokens (optionally backticked, with :line anchors).
    # URLs are not filesystem paths; their /pull/N component is still offline-checkable.
    pr_refs = re.findall(r"(?:\bPR\s*#?\s*|(?<!\w)#|/pull/)(\d+)\b", text, re.I)
    for ref in pr_refs:
        if int(ref) not in prs:
            add("pr_unresolved", row, f"PR #{ref} is absent from the inherited PR inventory")
    offline = re.sub(r"\b[a-z][a-z0-9+.-]*://[^\s`<>]+", "", text, flags=re.I)
    for ref in re.findall(r"\b(?:commit(?:\s+id)?|sha(?:-?1)?|head)\s*[:=]?\s*[`\"']?([^\s`\"';,]+)", offline, re.I):
        if not COMMIT.fullmatch(ref.rstrip(".")):
            add("commit_invalid", row, f"commit id {ref!r} must be 7-to-40 hex")
    for ref in re.findall(r"(?<![\w/])[0-9a-fA-F]{7,}(?![\w/])", offline):
        if not COMMIT.fullmatch(ref):
            add("commit_invalid", row, f"commit id {ref!r} must be 7-to-40 hex")
    # A slash token without an extension can be ordinary prose (report/teardown).
    # File paths have a filename extension; backticked paths also support spaces/directories.
    paths = [span for span in re.findall(r"`([^`]+)`", offline)
             if "/" in span or re.search(r"\.[A-Za-z][A-Za-z0-9_-]*(?::\d|$)", span)]
    unquoted = re.sub(r"`[^`]+`", "", offline)
    paths += re.findall(
        r"(?<![\w])(?:[\w./@-]+\.[A-Za-z][A-Za-z0-9_-]*|(?:\./|\.\./|/)[\w./@-]+)"
        r"(?::\d+(?:[,:-]\d+)*)?", unquoted)
    for ref in paths:
        locator = re.sub(r":\d+(?:[,:-]\d+)*$", "", ref).rstrip(".")
        candidate = (repo / locator).resolve()
        if not candidate.is_relative_to(repo) or not candidate.exists():
            add("path_unresolved", row, f"repository path {locator!r} does not exist under --repo")


def check(disposition, raw, inventories, repo):
    violations = []

    def add(code, row, detail):
        violations.append({"code": code, "row": row, "detail": detail})

    prs_data, state = inventories
    prs = inventory_ids(prs_data, "prs", "number", numeric=True)
    items = inventory_ids(state, "non_done_items", "id")
    aggregates = class_counts(state)

    # 00_ARCHITECTURE/control/kalayantra/plan_model.json:7047-7049; /Users/Dev/kalayantra/run/J0_DISPOSITION.json:2,4. The detector's 300-byte floor is necessary, not sufficient.
    if len(raw) < 300:
        add("artifact_size", None, f"{len(raw)} bytes; detector requires at least 300")
    if disposition.get("artifact") != "J0_DISPOSITION" or disposition.get("item") != "J-0c":
        add("artifact_identity", None, "expected artifact J0_DISPOSITION and item J-0c")
    # 00_ARCHITECTURE/control/kalayantra/plan_model.json:7069; /Users/Dev/kalayantra/run/J0_DISPOSITION.json:5,8-9. Presence of recorded observations, not freshness or acceptance.
    for label, data in [("disposition", disposition)] + [
            (key, disposition["sources"][key]) for key in ("pr_inventory", "state_inventory")]:
        if not nonempty(data.get("observed_at")):
            add("observation_missing", label, "observed_at must be recorded and non-empty")
    # 00_ARCHITECTURE/control/kalayantra/plan_model.json:7069; /Users/Dev/kalayantra/run/J0_DISPOSITION.json:8-15. Other declared source hashes are checked for full SHA-256 syntax only.
    for key, data in disposition["sources"].items():
        records = data if isinstance(data, list) else [data]
        for index, record in enumerate(records):
            if isinstance(record, dict) and "path" in record:
                digest = record.get("sha256")
                if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                    add("source_hash", f"sources.{key}[{index}]", "declared source requires a full SHA-256")

    groups = []
    missing = duplicates = 0
    for kind, expected, field in [("pr", prs, "pr"), ("state", items, "id")]:
        rows = disposition.get(kind + "_dispositions")
        # 00_ARCHITECTURE/control/kalayantra/plan_model.json:7064-7065; A1. Invalid row identities cannot be counted as covered.
        if not isinstance(rows, list):
            add("row_contract", kind, "dispositions must be a list")
            rows = []
        actual = Counter()
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                add("row_contract", f"{kind}[{index}]", "row must be an object")
                continue
            value = row.get(field)
            if not (integer(value) and value > 0 if kind == "pr" else nonempty(value)):
                add("row_contract", f"{kind}[{index}]", f"invalid row {field}")
                continue
            label = f"PR #{value}" if kind == "pr" else value
            actual[value] += 1
            groups.append((kind, value, label, row))
        for value in sorted(expected - actual.keys()):
            add("coverage_missing", f"PR #{value}" if kind == "pr" else value, "inventory entry has no disposition")
            missing += 1
        for value, count in sorted(actual.items()):
            label = f"PR #{value}" if kind == "pr" else value
            if value not in expected:
                add("coverage_extra", label, "disposition is absent from the inventory")
            if count > 1:
                add("coverage_duplicate", label, f"inventory entry has {count} dispositions")
                duplicates += count - 1

    # A1; 00_ARCHITECTURE/control/kalayantra/plan_model.json:7064; /Users/Dev/kalayantra/run/J0_DISPOSITION.json:98; /Users/Dev/kalayantra/run/J0_STATE_INVENTORY.json:24-44.
    # (I) INTERPRETATION: add decisions/sealed_decisions/holds counts to existing coverage.
    counts = {"open_prs": len(prs), "state_entries": len(items), "total_entries": len(prs) + len(items),
              "duplicates": duplicates, "missing": missing, **aggregates}
    coverage = disposition.get("coverage", {})
    for key, expected in counts.items():
        actual = coverage.get(key) if isinstance(coverage, dict) else None
        if not integer(actual) or actual != expected:
            add("coverage_count", "coverage." + key, f"expected {expected}, recorded {actual!r}")

    phase_rows = {}
    for kind, value, label, row in groups:
        # 00_ARCHITECTURE/control/kalayantra/plan_model.json:7065; /Users/Dev/kalayantra/run/J0_DISPOSITION.json:26-91. Empty dependency lists are permitted (/Users/Dev/kalayantra/run/J0_DISPOSITION.json:37,74).
        deps = row.get("dependencies")
        phase = row.get("phase")
        if (not nonempty(row.get("proposal")) or row["proposal"] not in PROPOSALS
                or not nonempty(row.get("owner")) or not isinstance(deps, list)
                or not all(nonempty(dep) for dep in deps)
                or not integer(phase) or not 1 <= phase <= 12):
            add("row_contract", label, "requires allowed proposal, owner, dependency list and integer phase 1–12")
        if integer(phase) and 1 <= phase <= 12:
            phase_rows.setdefault((kind, value), []).append((phase, label))
        # A2; 00_ARCHITECTURE/control/kalayantra/plan_model.json:7065; /Users/Dev/kalayantra/run/J0_DISPOSITION.json:26-91. Head is a commit-shaped evidence field on every PR row.
        if not nonempty(row.get("evidence")):
            add("evidence_missing", label, "evidence must be present and non-empty")
        else:
            reference_checks(row["evidence"], label, prs, repo, add)
        if kind == "pr" and (not isinstance(row.get("head"), str) or not COMMIT.fullmatch(row["head"])):
            add("commit_invalid", label, "head must be a 7-to-40-hex commit id")
        if isinstance(deps, list):
            for dep in deps:
                if isinstance(dep, str):
                    reference_checks(dep, label, prs, repo, add)

    for kind, value, label, row in groups:
        deps, phase = row.get("dependencies"), row.get("phase")
        if not isinstance(deps, list) or not integer(phase) or not 1 <= phase <= 12:
            continue
        # A3; /Users/Dev/kalayantra/run/J0_DISPOSITION.json:75-76. Named item IDs and explicit PR references resolve to disposition rows.
        # (I) INTERPRETATION: descriptive prerequisites/done items have no phase in these inputs.
        for dep in deps:
            if not isinstance(dep, str):
                continue
            targets = [("state", item) for item in sorted(items)
                       if re.search(r"(?<![\w.-])" + re.escape(item) + r"(?![\w.-])", dep)]
            targets += [("pr", int(p)) for p in re.findall(r"(?:\bPR\s*#?\s*|(?<!\w)#|/pull/)(\d+)\b", dep, re.I)]
            for target in targets:
                for required_phase, required_label in phase_rows.get(target, []):
                    if phase < required_phase:
                        add("phase_order", label, f"phase {phase} precedes dependency {required_label} in phase {required_phase}")
        # /Users/Dev/kalayantra/run/J0_DISPOSITION.json:23 (named refusal mutations); 00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md:98-107 defines full build as phase 10.
        if (kind == "state" and (phase in {"A5.5h": {5}, "A5.5j": {5}, "A5.5m": {5},
                "A5.5k": {7}, "A5.5l": {5}}.get(value, set())
                or value in {"A5.6", "B5.4", "J2"} and phase < 10)):
            add("phase_constraint", label, f"phase {phase} is prohibited by the named refusal rule")
        # /Users/Dev/kalayantra/run/J0_DISPOSITION.json:22,52; 00_ARCHITECTURE/control/kalayantra/plan_model.json:7066; 00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md:98,105. PR3141 may be considered only in phase 8.
        if kind == "pr" and value == 3141 and phase != 8:
            add("small_test_constraint", label, "PR #3141 must remain unmerged through small tests; proposed phase must be 8")
        if kind == "state" and value in SOURCE_DEPENDENCIES:
            absent = SOURCE_DEPENDENCIES[value] - set(dep for dep in deps if isinstance(dep, str))
            if absent:
                add("source_dependency", label, "listed source dependencies removed/replaced: " + ", ".join(sorted(absent)))

    # 00_ARCHITECTURE/control/kalayantra/plan_model.json:7065,7069; /Users/Dev/kalayantra/run/J0_DISPOSITION.json:21,89-96; /Users/Dev/kalayantra/run/J0_STATE_INVENTORY.json:22,25,34-42; 00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md:120. Reserved proposals route to ADHIKARIN.
    reserved = {r["id"] for r in state["non_done_items"] if str(r.get("source", "")).startswith("decision:")}
    for kind, value, label, row in groups:
        if kind == "state" and value in reserved and row.get("owner") != "ADHIKARIN":
            add("reserved_ruling", label, "reserved decision item must route to ADHIKARIN")
    unresolved = disposition.get("unresolved")
    if not isinstance(unresolved, list):
        add("reserved_ruling", "unresolved", "explicit unresolved records must be a list")
        unresolved = []
    needed = set()
    if any(r.get("status") == "pending" for r in state["decisions"]):
        needed.add("decision")
    if any(r.get("status") in {"historical_unresolved", "reported_active_stale"} for r in state["holds"]["operational"]):
        needed.add("hold")
    for kind in sorted(needed):
        records = [r for r in unresolved if isinstance(r, dict) and r.get("kind") == kind]
        if not records or any(r.get("proposal") != "route_to_ADHIKARIN" for r in records):
            add("reserved_ruling", "unresolved." + kind, "must explicitly route unresolved class to ADHIKARIN")
    for index, record in enumerate(unresolved):
        if not isinstance(record, dict) or not nonempty(record.get("evidence")):
            add("evidence_missing", f"unresolved[{index}]", "unresolved record requires non-empty evidence")
        else:
            reference_checks(record["evidence"], f"unresolved[{index}]", prs, repo, add)
    return violations


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check"])
    parser.add_argument("disposition", type=Path)
    parser.add_argument("--inventory-prs", required=True, type=Path)
    parser.add_argument("--inventory-state", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        data, raw = read_json(args.disposition)
        repo = args.repo.resolve()
        if not repo.is_dir():
            raise InputUnknown("input_unreadable", str(repo), "--repo must be an existing directory")
        inventories = []
        # /Users/Dev/kalayantra/run/J0_DISPOSITION.json:8-9; 00_ARCHITECTURE/control/kalayantra/plan_model.json:7042-7043,7064,7069; A1/A2. Hash actual bytes, not reserialized JSON.
        for key, path in [("pr_inventory", args.inventory_prs), ("state_inventory", args.inventory_state)]:
            inventory, inventory_raw = read_json(path)
            sources = data.get("sources")
            pin = sources.get(key) if isinstance(sources, dict) else None
            digest = pin.get("sha256") if isinstance(pin, dict) else None
            if not isinstance(digest, str) or not SHA256.fullmatch(digest) or hashlib.sha256(inventory_raw).hexdigest() != digest.lower():
                raise InputUnknown("input_digest", key, "inventory bytes do not match the disposition's SHA-256 pin")
            inventories.append(inventory)
        violations = check(data, raw, inventories, repo)
        result, status = ("refused", 1) if violations else ("accepted", 0)
    except InputUnknown as exc:
        violations, result, status = [exc.violation], "unknown", 3
    print(json.dumps({"schema": "ky.accept/1", "item": "J-0c", "result": result,
                      "violations": violations}, ensure_ascii=False, separators=(",", ":")))
    return status


if __name__ == "__main__":
    sys.exit(main())
