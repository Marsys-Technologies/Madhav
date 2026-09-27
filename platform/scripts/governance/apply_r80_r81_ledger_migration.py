#!/usr/bin/env python3
"""apply_r80_r81_ledger_migration.py — the ONE authorized real write to
`00_ARCHITECTURE/control/asset_gaps.jsonl` this wave makes (Nikaṣa wave 3, R80 + R81).

Applies, in a single pass:
  R80 — migrates the `_schema` row's own `_doc` text to document `superseded_by`
         (ledger_r81_migration.add_superseded_by_to_schema_doc).
  R81 — appends the 11-pair overlap fold (ledger_r81_migration.fold_overlap_pairs).

Every existing data line (everything after line 1) is preserved BYTE-FOR-BYTE — this script never
re-serialises a line it did not itself compute the new content of, so no line's key order,
escaping or whitespace can silently drift. Only line 1 (`_schema`) is replaced in place (a
one-time documentation update, not a "gap" data row — the ledger's append-only discipline binds
kind=gap/opportunity rows, per the _schema doc's own text); every new gap-fold row is APPENDED,
nothing is ever deleted.

Both migration functions were already proven idempotent on a copy in
platform/scripts/governance/__tests__/test_r80_schema_superseded_by_field.py and
test_r81_ledger_overlap_fold.py before this script exists to run them for real.

Usage:
  python3 apply_r80_r81_ledger_migration.py --dry-run   # default; prints the plan, writes nothing
  python3 apply_r80_r81_ledger_migration.py --apply      # writes the real file, once
  python3 apply_r80_r81_ledger_migration.py --apply      # a second run must be a true no-op —
                                                          # this is the idempotency proof, live
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import ledger_r81_migration as mig  # noqa: E402

ROOT = HERE.parents[2]
LEDGER = ROOT / "00_ARCHITECTURE/control/asset_gaps.jsonl"


def _md5(path: pathlib.Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write the real file (default: dry run)")
    ap.add_argument("--ledger", default=str(LEDGER), help="override for testing against a copy")
    a = ap.parse_args()
    path = pathlib.Path(a.ledger)

    before_lines = path.read_text(encoding="utf-8").split("\n")
    if before_lines and before_lines[-1] == "":
        before_lines = before_lines[:-1]  # trailing newline produces one empty split element
    before_count = len(before_lines)
    before_md5 = _md5(path)

    schema_row = json.loads(before_lines[0])
    if schema_row.get("asset") != "_schema":
        print("REFUSED: line 1 is not the _schema row — aborting without writing", file=sys.stderr)
        return 2
    migrated_schema = mig.migrate_schema_line(schema_row)

    all_rows = [json.loads(ln) for ln in before_lines if ln.strip()]
    ts = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    new_rows = mig.fold_overlap_pairs(all_rows, ts)

    print(f"ledger: {path}")
    print(f"before: {before_count} lines, md5={before_md5}")
    print(f"schema row _doc changes: {'yes' if migrated_schema['_doc'] != schema_row['_doc'] else 'no (already migrated)'}")
    print(f"R81 fold: {len(new_rows)} new row(s) to append "
          f"({len([r for r in new_rows if 'superseded_by' not in r])} content, "
          f"{len([r for r in new_rows if 'superseded_by' in r])} superseding)")

    if not a.apply:
        print("DRY RUN — nothing written. Re-run with --apply to write for real.")
        return 0

    new_lines = [json.dumps(migrated_schema, ensure_ascii=False)] + before_lines[1:] + \
                [json.dumps(r, ensure_ascii=False) for r in new_rows]
    tmp = path.with_suffix(path.suffix + ".r80r81.tmp")
    tmp.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    tmp.replace(path)  # atomic on the same filesystem

    after_count = len(path.read_text(encoding="utf-8").splitlines())
    after_md5 = _md5(path)
    print(f"after:  {after_count} lines, md5={after_md5}")
    print(f"delta:  {after_count - before_count} line(s) added "
          f"(expected {len(new_rows)} net new lines from R81's appends; the schema line is "
          f"replaced in place, not counted as a new line)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
