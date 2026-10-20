#!/usr/bin/env python3
"""executor_pin_shards.py — append-only pin shards for the executor table (SR-CHURN-CUT 3).

test_executor_table.py pins `executor_ops.json` against an independently written expectation. That expectation is an
oracle, so it can never be regenerated from the table it checks (a pin written by the code it pins reads true whatever
the table says: §N.8). What churned was its SHAPE: every PR that changed the table edited the same few lines of one
71 KB test, so every open PR conflicted with every other.

A shard is one reviewed edit set as a NEW file, `tests/executor_pin_shards/<ITEM>.json`:
  {"schema": "ky.executor_pin_shard/1", "item": "<plan-model item>", "after": "<kind>" | null,
   "entries": {"<kind>": {the exact table entry, key order included}, ...}}
  · a kind already in the expected table is REPLACED in place (its position is unchanged);
  · a kind not yet in it is INSERTED, in `entries` order, directly after `after` (null: appended last).
Shards apply in file-name order, after the monolith's own enumeration. A merged shard is never edited
(generated_paths.shard_violations, enforced by ci_generated.py generate --base): the next edit is a new shard.

The hand-written part is the reviewed entries. `scaffold` below drafts a shard from a base table and a working table so
a builder does not retype 15 keys; the draft is a REVIEW ARTIFACT, never evidence — the verifier reads each entry
against the item's brief, and the monolith still compares the live table with base + shards.

  executor_pin_shards.py scaffold --item K9-24 --base <executor_ops.json at main> [--ops <working executor_ops.json>]
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

SCHEMA = "ky.executor_pin_shard/1"
HERE = Path(__file__).resolve().parent
SHARD_DIR = HERE / "tests" / "executor_pin_shards"


def load_shards(directory: Path = SHARD_DIR) -> list[dict]:
    shards = []
    for path in sorted(directory.glob("*.json")) if directory.is_dir() else []:
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("schema") != SCHEMA:
            raise ValueError(f"{path.name}: schema is not {SCHEMA}")
        if doc.get("item") != path.stem:
            raise ValueError(f"{path.name}: `item` must equal the file stem")
        if not isinstance(doc.get("entries"), dict) or not doc["entries"]:
            raise ValueError(f"{path.name}: no entries")
        shards.append(doc)
    return shards


def apply_shards(expected: dict, order: list, shards: list) -> tuple[dict, list]:
    """(expected entries, expected kind order) after every shard; the inputs are not modified."""
    expected, order = json.loads(json.dumps(expected)), list(order)
    for shard in shards:
        new = [k for k in shard["entries"] if k not in expected]
        for kind, entry in shard["entries"].items():
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


def enabled_kinds(shards: list) -> set:
    return {k for s in shards for k, e in s["entries"].items() if e.get("enabled") is True}


def scaffold(base_ops: dict, now_ops: dict, item: str) -> dict:
    """A draft shard: every kind the working table adds or changes against the base, in table order."""
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
    return {"schema": SCHEMA, "item": item, "after": after, "entries": changed}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["scaffold"])
    ap.add_argument("--item", required=True)
    ap.add_argument("--base", required=True, type=Path)
    ap.add_argument("--ops", type=Path, default=HERE / "executor_ops.json")
    ns = ap.parse_args(argv)
    doc = scaffold(json.loads(ns.base.read_text(encoding="utf-8")), json.loads(ns.ops.read_text(encoding="utf-8")), ns.item)
    print(json.dumps(doc, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as exc:
        print(f"executor_pin_shards refused: {exc}", file=sys.stderr)
        sys.exit(1)
