#!/usr/bin/env python3
"""Compute, check and stamp CAPABILITY_MANIFEST.json's own top-level fingerprint.

Why this exists. The manifest carries `fingerprint` and `generated_at` at its root. Every
per-entry `fingerprint_sha256` is reproducible — it is the sha256 of the file that entry
points at, and `drift_detector.py` recomputes and compares them. The ROOT fingerprint was
not reproducible by anything: no generator existed in the repository, so the field was
stamped by hand, could not be re-derived, and could not fail. Under CLAUDE.md §N.8 that is
not a checksum, it is a number wearing a checksum's clothes.

The definition, fixed here (2026-09-25):

    fingerprint = sha256( canonical_json(entries) )[:16]
    canonical_json = json.dumps(entries, sort_keys=True, separators=(',',':'), ensure_ascii=False)

`entries` is the manifest's own array, as stored, with `entry_count` derived from it. The
root `fingerprint`/`generated_at`/`entry_count` fields are excluded from the input, so
stamping is stable: computing twice in a row gives the same value.

HONEST LIMIT, stated rather than hidden: this algorithm is DEFINED here, not recovered.
Values stamped before 2026-09-25 were produced by an unknown method and this script cannot
reproduce them. The first `--write` therefore changes the value once, legitimately; every
run after that is a real comparison that can fail.

Usage:
  manifest_fingerprint.py --check   exit 0 match · 2 mismatch · 5 error   (read-only)
  manifest_fingerprint.py --write   restamp fingerprint/generated_at/entry_count
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from collections import OrderedDict
from pathlib import Path

MANIFEST = Path(__file__).resolve().parents[3] / "00_ARCHITECTURE" / "CAPABILITY_MANIFEST.json"


def canonical_fingerprint(entries: list) -> str:
    blob = json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--write", action="store_true")
    ap.add_argument("--manifest", default=str(MANIFEST))
    args = ap.parse_args()

    path = Path(args.manifest)
    manifest = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)
    entries = manifest.get("entries", [])
    observed = canonical_fingerprint(entries)
    declared = manifest.get("fingerprint", "")
    count_declared = manifest.get("entry_count")

    if args.check:
        ok = observed == declared and count_declared == len(entries)
        print(f"entries: {len(entries)} (declared {count_declared})")
        print(f"fingerprint declared: {declared or '<none>'}")
        print(f"fingerprint observed: {observed}")
        print("MATCH" if ok else "MISMATCH — run --write in the session that changed the manifest")
        return 0 if ok else 2

    manifest["entry_count"] = len(entries)
    manifest["fingerprint"] = observed
    manifest["generated_at"] = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"stamped: entry_count={len(entries)} fingerprint={observed} (was {declared or '<none>'})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"manifest_fingerprint: script error — {exc}", file=sys.stderr)
        sys.exit(5)
