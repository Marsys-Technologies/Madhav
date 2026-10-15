#!/usr/bin/env python3
"""Reproduce/check declaration hashes; never certifies G1, readiness or a result.

Default: read-only check. --write is for preparing a NEW version before its
execution freeze, never for silently amending an already bound experiment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = ROOT / "00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KSHETRA_ABLATION_PREREGISTRATION_v1_0.md"
FILES = ("KSHETRA_ABLATION_PREREGISTRATION_v1_1.md", "preregistration.json")


def seal_bytes() -> bytes:
    payload = {
        "schema": "ky.vc1_declaration_seal/1",
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "files": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in FILES},
    }
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="prepare a new, not yet execution-frozen version")
    mode.add_argument("--check", action="store_true", help="read-only hash check (default)")
    args = parser.parse_args()
    try:
        expected = seal_bytes()
        target = HERE / "DECLARATION_SEAL.json"
        if args.write:
            target.write_bytes(expected)
            print("Declaration hashes written; G1 and execution freeze remain unverified.")
        elif target.read_bytes() != expected:
            print("declaration seal mismatch; do not silently amend a frozen experiment", file=sys.stderr)
            return 1
        else:
            print("Declaration bytes match seal; no baseline/readiness/result claim.")
    except (OSError, ValueError) as exc:
        print(f"declaration seal unavailable: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
