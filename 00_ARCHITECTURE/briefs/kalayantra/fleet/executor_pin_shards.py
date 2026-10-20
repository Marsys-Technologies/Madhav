#!/usr/bin/env python3
"""executor_pin_shards.py — append-only pin shards for the executor table (SR-CHURN-CUT 3, extended by SR-CHURN-CUT 5).

test_executor_table.py pins `executor_ops.json` against an independently written expectation. That expectation is an
oracle, so it can never be regenerated from the table it checks (a pin written by the code it pins reads true whatever
the table says: §N.8). What churned was its SHAPE: every PR that changed the table edited the same few lines of one
71 KB test, so every open PR conflicted with every other. SR-CHURN-CUT 5 moves the remaining shared census lines
(kind sets, safety classes, W4 bindings, executor function hashes) into the same shard.

THE RULE: adding or changing one executor kind adds exactly ONE new file, `tests/executor_pin_shards/<ITEM>.json`
(plus the kind's own `executor_ops.json` entry, code and tests). It edits no shared census line in any test.

A shard is one reviewed edit set as a NEW file. Schema /1 (still valid) has only `entries`; /2 is a superset:
  {"schema": "ky.executor_pin_shard/2", "item": "<plan-model item>", "after": "<kind>" | null,
   "entries": {"<kind>": {the exact table entry, key order included}, ...},
   "classes": {"<kind>": ["signed_only" | "cancel_lane" | "mechanical_exempt" | "remote_async" | "teardown" | "no_dryrun"
                          | "dryrun_census" | "marker_client_env" | "marker_in_process" | "marker_no_database", ...]},
   "w4_bindings": {"<kind>": [needs, script, fixed_args, allowed_args, production, timeout_s]},
   "function_hashes": {"W4" | "K9": {"<function or constant of executor.py>": "<sha256 of its source segment>"}},
   "rebase": true}
  · entries: a kind already in the expected table is REPLACED in place (its position is unchanged); a kind not yet in it is
    INSERTED, in `entries` order, directly after `after` (null: appended last).
  · classes: HAND-DECLARED safety classes (the independent oracle for executor.py's own kind sets). The full class set of a
    kind REPLACES its previous one; `[]` removes every class. A kind a shard does not name keeps its earlier classes.
  · w4_bindings: the exact (needs, script, fixed_args, allowed_args, production, timeout_s) of a kind, as test_w4_smalltest_enablement
    states them; a later shard replaces the whole list.
  · function_hashes: sha256 of the source segment of an executor.py function or constant that the boundary test treats as an exact
    reviewed addition; a later shard REPLACES a function's digest.
  · rebase: only the cockpit compacts shards into the BASE literals of the census tests; the CI guard
    (generated_paths.kind_shard_required) refuses an edit to a BASE literal unless the PR also adds a shard with `"rebase": true`.
Shards apply in file-name order, after the BASE literals of each test. Folding is idempotent, so a shard compacted into BASE is harmless.
A merged shard is never edited (generated_paths.shard_violations, enforced by ci_generated.py generate --base): the next edit is a new shard.

The hand-written part is the reviewed content. `scaffold` below drafts `entries` from a base table and a working table so a builder
does not retype 15 keys; the draft is a REVIEW ARTIFACT, never evidence. It NEVER fills `classes` or `function_hashes` — filling them
from executor.py would let the code attest itself (§N.8) — it prints them as "TODO: hand-review" and `load_shards` refuses any shard
that still carries a placeholder.

  executor_pin_shards.py scaffold --item K9-24 --base <executor_ops.json at main> [--ops <working executor_ops.json>]
  executor_pin_shards.py check [--ops <executor_ops.json>]     load every shard, check it against the table, print the folded census
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

SCHEMA_1 = "ky.executor_pin_shard/1"
SCHEMA = "ky.executor_pin_shard/2"
SCHEMAS = (SCHEMA_1, SCHEMA)
PLACEHOLDER = "TODO: hand-review"
CLASS_NAMES = ("signed_only", "cancel_lane", "mechanical_exempt", "remote_async", "teardown", "no_dryrun", "dryrun_census",
               "marker_client_env", "marker_in_process", "marker_no_database")   # (I) the three marker_* classes carry test_executor_mechanical_acceptance.MARKER_ROUTE, the last census a new production kind would otherwise edit
HASH_GROUPS = ("W4", "K9")
V2_KEYS = ("classes", "w4_bindings", "function_hashes", "rebase")
HERE = Path(__file__).resolve().parent
SHARD_DIR = HERE / "tests" / "executor_pin_shards"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _placeholders(value, where: str) -> list[str]:
    if isinstance(value, str):
        return [where] if value.startswith("TODO") else []
    if isinstance(value, dict):
        return [p for k, v in value.items() for p in _placeholders(k, f"{where}.{k}") + _placeholders(v, f"{where}.{k}")]
    if isinstance(value, list):
        return [p for i, v in enumerate(value) for p in _placeholders(v, f"{where}[{i}]")]
    return []


def _check_v2(name: str, doc: dict) -> None:
    classes = doc.get("classes", {})
    if not isinstance(classes, dict):
        raise ValueError(f"{name}: `classes` must be an object {{kind: [class, ...]}}")
    for kind, names in classes.items():
        if not isinstance(names, list) or any(n not in CLASS_NAMES for n in names) or len(set(names)) != len(names):
            raise ValueError(f"{name}: classes[{kind!r}] must be a list of distinct names from {list(CLASS_NAMES)}")
    bindings = doc.get("w4_bindings", {})
    if not isinstance(bindings, dict):
        raise ValueError(f"{name}: `w4_bindings` must be an object {{kind: [needs, script, fixed_args, allowed_args, production, timeout_s]}}")
    for kind, b in bindings.items():
        if not (isinstance(b, list) and len(b) == 6 and isinstance(b[0], str) and isinstance(b[1], str) and isinstance(b[2], list)
                and isinstance(b[3], list) and isinstance(b[4], bool) and (b[5] is None or isinstance(b[5], int))):
            raise ValueError(f"{name}: w4_bindings[{kind!r}] must be [needs, script, fixed_args, allowed_args, production(bool), timeout_s(int|null)]")
        entry = (doc.get("entries") or {}).get(kind)
        if entry is not None:       # two hand declarations of one binding must agree
            for field, value in zip(("needs", "script", "fixed_args", "allowed_args", "production", "timeout_s"), b):
                if field in entry and entry[field] != value:
                    raise ValueError(f"{name}: w4_bindings[{kind!r}] disagrees with entries[{kind!r}].{field}")
    hashes = doc.get("function_hashes", {})
    if not isinstance(hashes, dict) or any(g not in HASH_GROUPS or not isinstance(h, dict) for g, h in hashes.items()):
        raise ValueError(f"{name}: `function_hashes` must be {{\"W4\"|\"K9\": {{function: sha256}}}}")
    for group, table in hashes.items():
        for function, digest in table.items():
            if not (isinstance(function, str) and isinstance(digest, str) and HEX64.fullmatch(digest)):
                raise ValueError(f"{name}: function_hashes[{group!r}][{function!r}] must be a lowercase sha256 (64 hex)")
    if "rebase" in doc and doc["rebase"] is not True:
        raise ValueError(f"{name}: `rebase` is either absent or true")


def load_shards(directory: Path = SHARD_DIR) -> list[dict]:
    shards = []
    for path in sorted(directory.glob("*.json")) if directory.is_dir() else []:
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("schema") not in SCHEMAS:
            raise ValueError(f"{path.name}: schema is not one of {', '.join(SCHEMAS)}")
        if doc.get("item") != path.stem:
            raise ValueError(f"{path.name}: `item` must equal the file stem")
        left = _placeholders(doc, path.name)
        if left:
            raise ValueError(f"{path.name}: hand-review placeholder left in {left[0]}: replace every TODO with a reviewed value or delete the key")
        if doc["schema"] == SCHEMA_1:
            extra = [k for k in V2_KEYS if k in doc]
            if extra:
                raise ValueError(f"{path.name}: {extra[0]!r} needs schema {SCHEMA}")
        else:
            _check_v2(path.name, doc)
        entries = doc.get("entries")
        has_content = bool(entries) or any(doc.get(k) for k in ("classes", "w4_bindings", "function_hashes")) or doc.get("rebase") is True
        if entries is not None and not isinstance(entries, dict):
            raise ValueError(f"{path.name}: `entries` must be an object")
        if doc["schema"] == SCHEMA_1 and not entries:
            raise ValueError(f"{path.name}: no entries")
        if not has_content:
            raise ValueError(f"{path.name}: no entries")
        shards.append(doc)
    return shards


def apply_shards(expected: dict, order: list, shards: list) -> tuple[dict, list]:
    """(expected entries, expected kind order) after every shard; the inputs are not modified."""
    expected, order = json.loads(json.dumps(expected)), list(order)
    for shard in shards:
        entries = shard.get("entries") or {}
        new = [k for k in entries if k not in expected]
        for kind, entry in entries.items():
            expected[kind] = json.loads(json.dumps(entry))
        after = shard.get("after")
        if new and after is None:
            order.extend(new)
        elif new:
            if after not in order:
                raise ValueError(f"{shard['item']}: `after` kind {after!r} is not in the table")
            pos = order.index(after) + 1
            order[pos:pos] = new
    return expected, order


def entries_after(shards: list) -> dict:
    """{kind: the exact table entry} as the shards leave it (a later shard replaces an earlier one); the inputs are not modified."""
    out: dict = {}
    for shard in shards:
        for kind, entry in (shard.get("entries") or {}).items():
            out[kind] = json.loads(json.dumps(entry))
    return out


def enabled_kinds(shards: list) -> set:
    return {k for s in shards for k, e in (s.get("entries") or {}).items() if e.get("enabled") is True}


def kinds_after(base: set, shards: list, predicate) -> set:
    """`base` after the shards: a kind a shard names is in the set iff `predicate(its LAST shard entry)` holds; kinds no shard names keep their BASE membership. Pure."""
    out = set(base)
    for kind, entry in entries_after(shards).items():
        (out.add if predicate(entry) else out.discard)(kind)
    return out


def enabled_after(base: set, shards: list) -> set:
    """`base` (the enabled kinds) after the shards. Pure."""
    return kinds_after(base, shards, lambda e: e.get("enabled") is True)


def production_after(base: set, shards: list) -> set:
    """`base` (the production kinds) after the shards. Pure."""
    return kinds_after(base, shards, lambda e: e.get("production") is True)


def classes_after(base_classes: dict, shards: list) -> dict:
    """{kind: sorted class list} after the shards. A shard's list for a kind REPLACES that kind's classes; `[]` removes them. Pure."""
    out = {k: sorted(v) for k, v in base_classes.items()}
    for shard in shards:
        for kind, names in (shard.get("classes") or {}).items():
            if names:
                out[kind] = sorted(names)
            else:
                out.pop(kind, None)
    return out


def kinds_with(classes: dict, name: str) -> set:
    """The kinds whose class set contains `name`."""
    return {k for k, names in classes.items() if name in names}


def w4_after(base: dict, shards: list) -> dict:
    """{kind: [needs, script, fixed_args, allowed_args, production, timeout_s]} after the shards (a later shard replaces the whole list). Pure."""
    out = json.loads(json.dumps(base))
    for shard in shards:
        for kind, binding in (shard.get("w4_bindings") or {}).items():
            out[kind] = json.loads(json.dumps(binding))
    return out


def hashes_after(base: dict, shards: list) -> dict:
    """{"W4": {function: sha256}, "K9": {...}} after the shards (a later shard replaces a function's digest; new functions are added). Pure."""
    out = json.loads(json.dumps(base))
    for shard in shards:
        for group, table in (shard.get("function_hashes") or {}).items():
            out.setdefault(group, {}).update(table)
    return out


def scaffold(base_ops: dict, now_ops: dict, item: str) -> dict:
    """A draft shard: every kind the working table adds or changes against the base, in table order.

    `classes` and `function_hashes` are placeholders by design: they are hand-declared safety facts, never copied from executor.py."""
    base, now = base_ops["ops"], now_ops["ops"]
    changed = {k: e for k, e in now.items() if k not in base or base[k] != e}
    if not changed:
        raise ValueError("the working table equals the base: nothing to pin")
    keys, after = list(now), None
    added = [k for k in keys if k not in base]
    if added:
        i = keys.index(added[0])
        if keys[i:i + len(added)] != added:
            raise ValueError("added kinds are not contiguous in the table: split them into one shard per run")
        if i == 0:
            raise ValueError("a kind added before every existing kind cannot be pinned (`after` has no anchor)")
        after = None if i + len(added) == len(keys) else keys[i - 1]
    return {"schema": SCHEMA, "item": item, "after": after, "entries": changed,
            "classes": {k: PLACEHOLDER for k in changed},
            "function_hashes": {"W4": {PLACEHOLDER: PLACEHOLDER}}}


def check(shards: list, ops: dict) -> list[str]:
    """Problems between the loaded shards and the working table: every kind a shard names exists and equals its LAST shard entry."""
    table = ops["ops"]
    problems = []
    for kind, entry in entries_after(shards).items():
        if kind not in table:
            problems.append(f"{kind}: named by a shard but absent from the table")
        elif table[kind] != entry:
            problems.append(f"{kind}: the table entry differs from the last shard that names it")
    for shard in shards:
        for kind in (shard.get("classes") or {}):
            if kind not in table:
                problems.append(f"{shard['item']}: classes names {kind!r}, which is not in the table")
    return problems


def census(shards: list) -> str:
    """The folded view of the shards alone (the BASE literals live in the census tests), for a reviewer to read."""
    lines = []
    for s in shards:
        flags = " rebase" if s.get("rebase") else ""
        lines.append(f"shard {s['item']} ({s['schema'].rsplit('/', 1)[1]}{flags}): entries {sorted(s.get('entries') or {})} after {s.get('after')!r}")
    classes = classes_after({}, shards)
    lines.append("classes (shards only): " + (json.dumps(classes, sort_keys=True) if classes else "none"))
    lines.append("enabled by shards: " + json.dumps(sorted(enabled_after(set(), shards))))
    lines.append("w4 bindings: " + json.dumps(w4_after({}, shards), sort_keys=True))
    hashes = hashes_after({}, shards)
    lines.append("function hashes: " + json.dumps({g: {f: d[:12] + "…" for f, d in sorted(t.items())} for g, t in hashes.items()}, sort_keys=True))
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["scaffold", "check"])
    ap.add_argument("--item")
    ap.add_argument("--base", type=Path)
    ap.add_argument("--ops", type=Path, default=HERE / "executor_ops.json")
    ns = ap.parse_args(argv)
    ops = json.loads(ns.ops.read_text(encoding="utf-8"))
    if ns.mode == "scaffold":
        if not ns.item or not ns.base:
            ap.error("scaffold needs --item and --base")
        print(json.dumps(scaffold(json.loads(ns.base.read_text(encoding="utf-8")), ops, ns.item), indent=2, ensure_ascii=False))
        return 0
    shards = load_shards()
    print(census(shards))
    problems = check(shards, ops)
    for p in problems:
        print(f"executor_pin_shards check: {p}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as exc:
        print(f"executor_pin_shards refused: {exc}", file=sys.stderr)
        sys.exit(1)
