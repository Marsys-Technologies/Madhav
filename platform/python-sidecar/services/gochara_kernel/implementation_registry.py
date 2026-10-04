"""The REGISTERED implementation digest of the sealing-side code (ST-WIRE-2 item 3).

`implementation_digest.lock.json`, committed beside this module, records the digest of the implementation modules
(`input_vector.IMPLEMENTATION_MODULES`: geometry, evaluation and the window/verification/sealing stage, `seal_job` included) AT THIS COMMIT. The
sealing job re-computes the digest of the code it is actually running and refuses — before any database contact — unless it equals the
registered one: a dirty or substituted checkout (a module edited after the commit was reviewed) cannot seal. A CI test fails when the lock is stale,
so a commit that changes governed code carries the lock that registers it.

    python -m services.gochara_kernel.implementation_registry           # check (exit 0 current / 2 stale)
    python -m services.gochara_kernel.implementation_registry --write   # regenerate the lock
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCHEMA = "gochara_implementation_registry/1"
LOCK_PATH = Path(__file__).resolve().parent / "implementation_digest.lock.json"


def compute() -> dict:
    from . import input_vector as iv
    from . import input_vector_verifier as ivv
    from . import window_gate as wg
    return {"schema": SCHEMA, "implementation_digest": wg.implementation_digest(),
            "stages": ivv.module_digests(iv.IMPLEMENTATION_MODULES)}


def write(path: Path | None = None) -> dict:
    doc = compute()
    (path or LOCK_PATH).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    return doc


def registered(path: Path | None = None) -> dict | None:
    p = path or LOCK_PATH
    if not p.is_file():
        return None
    try:
        doc = json.loads(p.read_text())
    except ValueError:
        return None
    return doc if isinstance(doc, dict) and doc.get("schema") == SCHEMA and isinstance(doc.get("implementation_digest"), str) else None


def problem(path: Path | None = None) -> str | None:
    """None when the running code is the registered code; else the reason (names the stages that differ)."""
    reg = registered(path)
    if reg is None:
        return "no_registered_digest"
    now = compute()
    if now["implementation_digest"] == reg["implementation_digest"]:
        return None
    stages = sorted(s for s in now["stages"] if now["stages"][s] != (reg.get("stages") or {}).get(s))
    return f"digest_mismatch: running {now['implementation_digest']}, registered {reg['implementation_digest']} (stages {stages})"


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--write" in argv:
        print(write()["implementation_digest"])
        return 0
    why = problem()
    print("current" if why is None else why)
    return 0 if why is None else 2


if __name__ == "__main__":
    sys.exit(main())
