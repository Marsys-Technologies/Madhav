#!/usr/bin/env python3
"""kyclosure.py — reproducible acceptance closure of the KĀLA-YANTRA plan model.

Relaunch plan v2.2 §0, closure procedure step 2. Pure and deterministic: the output depends only on the
content of the plan model and of the acceptance-root file (no clock, no tracker, no live state), so two runs
give one hash, and re-indenting either input changes nothing.

Edge semantics (the tracker's own, state.py build_state):
  depends_on        item → item edges
  requires_outcome  item → decision-item edges, explicit even where depends_on omits the decision
  steps             intra-item obligations, never item ids
  join              `join: true` coincides with `done_by: join`
Skips:
  an item is skip-capable when it is optional, needs a decision outcome, or — not accepting skipped inputs —
  consumes a skip-capable item. A consumer with accepts_not_applicable_dependencies absorbs a skipped input as a
  GAP; the gap is reported on every acceptance above it and never counts as satisfied.

Usage:
  kyclosure.py --model plan_model.json --roots ACCEPTANCE_ROOTS.json --out CLOSURE.json
  kyclosure.py --model plan_model.json --roots ACCEPTANCE_ROOTS.json --check CLOSURE.json
Exit: 0 ok · 1 --check differs · 2 the model or the roots are refused (findings on stderr)
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

SCHEMA = "kalayantra.closure/1"


def canonical(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(obj) -> str:
    return hashlib.sha256(canonical(obj)).hexdigest()


def render(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode("utf-8")


def item_edges(item: dict) -> dict:
    """prerequisite id → sorted edge kinds ('item' from depends_on, 'decision' from requires_outcome)"""
    out: dict = {}
    for dep in item.get("depends_on", []):
        out.setdefault(dep, set()).add("item")
    for decision in item.get("requires_outcome") or {}:
        out.setdefault(decision, set()).add("decision")
    return {k: sorted(v) for k, v in out.items()}


def model_findings(model: dict) -> list:
    out = []
    ids = [i.get("id") for i in model.get("items", [])]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        out.append(f"duplicate item id: {dup}")
    items = {i["id"]: i for i in model.get("items", [])}
    for iid, it in items.items():
        for dep in it.get("depends_on", []):
            if dep not in items:
                out.append(f"{iid}: depends_on names no item: {dep}")
        for decision in it.get("requires_outcome") or {}:
            if items.get(decision, {}).get("done_by") != "decision":
                out.append(f"{iid}: requires_outcome names no decision item: {decision}")
        if (it.get("join") is True) != (it.get("done_by") == "join"):
            out.append(f"{iid}: join={it.get('join')!r} disagrees with done_by={it.get('done_by')!r}")
        for step in it.get("steps") or []:
            if step in items:
                out.append(f"{iid}: step '{step}' is an item id; steps are intra-item obligations")
    return out


def roots_findings(model: dict, roots: dict) -> list:
    out = []
    items = {i["id"]: i for i in model.get("items", [])}
    seen = set()
    for acc in roots.get("acceptances", []):
        if acc.get("id") in seen:
            out.append(f"duplicate acceptance id: {acc.get('id')}")
        seen.add(acc.get("id"))
        if not acc.get("roots"):
            out.append(f"acceptance {acc.get('id')}: no root item")
        for root in acc.get("roots", []):
            it = items.get(root.get("item"))
            where = f"acceptance {acc.get('id')} root {root.get('item')}"
            if it is None:
                out.append(f"{where}: no such item")
                continue
            if root.get("brief_spec") != it.get("brief", {}).get("spec"):
                out.append(f"{where}: brief citation differs from the model's brief.spec")
            if root.get("detector") != it.get("detector"):
                out.append(f"{where}: detector citation differs from the model's detector")
            if root.get("step") is not None and root["step"] not in (it.get("steps") or []):
                out.append(f"{where}: step '{root['step']}' is not one of the item's steps")
    for iid in roots.get("mechanical_close_chain", {}).get("items", []):
        if iid not in items:
            out.append(f"mechanical_close_chain names no item: {iid}")
    return out


def skip_capable(items: dict) -> dict:
    """item id → sorted reasons it can end not_applicable"""
    cap: dict = {}
    for iid, it in items.items():
        reasons = set()
        if it.get("mandatory") is False:
            reasons.add("optional")
        for decision, needed in (it.get("requires_outcome") or {}).items():
            reasons.add(f"decision:{decision}={needed}")
        if reasons:
            cap[iid] = reasons
    changed = True
    while changed:
        changed = False
        for iid, it in items.items():
            if it.get("accepts_not_applicable_dependencies") is True:
                continue
            for dep in it.get("depends_on", []):
                if dep in cap and f"input:{dep}" not in cap.setdefault(iid, set()):
                    cap[iid].add(f"input:{dep}")
                    changed = True
    return {k: sorted(v) for k, v in cap.items()}


def reach(items: dict, start: list) -> set:
    seen, stack = set(), list(start)
    while stack:
        iid = stack.pop()
        if iid in seen:
            continue
        seen.add(iid)
        stack.extend(item_edges(items[iid]))
    return seen


def compute(model: dict, roots: dict) -> dict:
    found = model_findings(model) + roots_findings(model, roots)
    if found:
        raise ValueError("\n".join(found))
    items = {i["id"]: i for i in model["items"]}
    cap = skip_capable(items)
    excluded = sorted(roots.get("mechanical_close_chain", {}).get("items", []))
    acceptances, membership = {}, {}
    for acc in roots["acceptances"]:
        root_ids = sorted({r["item"] for r in acc["roots"]})
        members = reach(items, root_ids)
        for iid in members:
            membership.setdefault(iid, set()).add(acc["id"])
        gaps = sorted(
            ({"absorbed_by": iid, "input": dep, "reasons": cap[dep]}
             for iid in members if items[iid].get("accepts_not_applicable_dependencies") is True
             for dep in items[iid].get("depends_on", []) if dep in cap),
            key=lambda g: (g["absorbed_by"], g["input"]))
        acceptances[acc["id"]] = {
            "roots": root_ids,
            "closure": sorted(members),
            "closure_count": len(members),
            "skip_capable_roots": {r: cap[r] for r in root_ids if r in cap},
            "gap_candidates": gaps,
        }
    closure = sorted(membership)
    out = {
        "schema": SCHEMA,
        "plan_version": roots.get("plan_version"),
        "inputs": {
            "model_canonical_sha256": digest(model),
            "model_version": model.get("model_version"),
            "model_items": len(items),
            "roots_canonical_sha256": digest(roots),
        },
        "acceptances": acceptances,
        "closure": closure,
        "closure_count": len(closure),
        "outside": sorted(set(items) - set(closure)),
        "outside_count": len(items) - len(closure),
        "mechanical_close_chain_excluded_as_roots": excluded,
        "members": {
            iid: {
                "acceptances": sorted(membership[iid]),
                "prerequisites": item_edges(items[iid]),
                "required_by": sorted(c for c in closure if iid in item_edges(items[c])),
                "skip_capable": cap.get(iid, []),
            } for iid in closure
        },
    }
    out["closure_sha256"] = digest(out)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--model", required=True)
    ap.add_argument("--roots", required=True)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--out")
    group.add_argument("--check")
    args = ap.parse_args(argv)
    model = json.loads(Path(args.model).read_text(encoding="utf-8"))
    roots = json.loads(Path(args.roots).read_text(encoding="utf-8"))
    try:
        result = render(compute(model, roots))
    except ValueError as refused:
        print(f"REFUSED\n{refused}", file=sys.stderr)
        return 2
    if args.check:
        if Path(args.check).read_bytes() != result:
            print(f"DIFFERS: {args.check} is not the closure of these inputs", file=sys.stderr)
            return 1
        print(f"OK {args.check} sha256={hashlib.sha256(result).hexdigest()}")
        return 0
    Path(args.out).write_bytes(result)
    print(f"wrote {args.out} sha256={hashlib.sha256(result).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
