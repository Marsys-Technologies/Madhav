#!/usr/bin/env python3
"""PG-1 Lane A-0: findings-shard validator. Exit 0 = all shards valid, 1 = violation found."""
import json
import sys
from pathlib import Path

DELIV = Path(__file__).resolve().parent.parent / "deliverables"
VALID_CLASS = {"stale", "confirmed", "partial", "unverifiable", "new_defect"}
VALID_SEVERITY = {"critical", "high", "medium", "low", "informational"}
VALID_CONFIDENCE = {"high", "medium", "low"}


def validate_line(obj, shard, lineno):
    errors = []
    for field in ("id", "lane", "assumption", "class", "claim", "reality", "evidence", "severity", "confidence"):
        if field not in obj:
            errors.append(f"{shard}:{lineno} missing field '{field}'")
    if obj.get("class") not in VALID_CLASS:
        errors.append(f"{shard}:{lineno} invalid class '{obj.get('class')}'")
    if obj.get("severity") not in VALID_SEVERITY:
        errors.append(f"{shard}:{lineno} invalid severity '{obj.get('severity')}'")
    if obj.get("confidence") not in VALID_CONFIDENCE:
        errors.append(f"{shard}:{lineno} invalid confidence '{obj.get('confidence')}'")
    if obj.get("class") != "unverifiable":
        ev = obj.get("evidence")
        if not isinstance(ev, list) or len(ev) == 0:
            errors.append(f"{shard}:{lineno} class '{obj.get('class')}' requires non-empty evidence array (G.2)")
        else:
            for e in ev:
                if "file" not in e or "line" not in e:
                    errors.append(f"{shard}:{lineno} evidence entry missing file/line: {e}")
    return errors


def main():
    all_errors = []
    total = 0
    shards = sorted(DELIV.glob("pg1_findings_*.jsonl"))
    for shard in shards:
        for lineno, raw in enumerate(shard.read_text().splitlines(), 1):
            if not raw.strip():
                continue
            total += 1
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError as e:
                all_errors.append(f"{shard.name}:{lineno} invalid JSON: {e}")
                continue
            all_errors.extend(validate_line(obj, shard.name, lineno))
    print(f"Validated {total} findings across {len(shards)} shards.")
    if all_errors:
        print(f"{len(all_errors)} VIOLATIONS:")
        for e in all_errors:
            print(f"  - {e}")
        sys.exit(1)
    print("All shards valid.")
    sys.exit(0)


if __name__ == "__main__":
    main()
