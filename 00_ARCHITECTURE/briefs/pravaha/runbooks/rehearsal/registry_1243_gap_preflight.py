#!/usr/bin/env python3
"""Read-only writer-gap pre-flight for migration 1243 (steward M20261003T020909-6c15).

Runs the orchestrator's REAL `_check_writer_registry_gaps` (pipeline/orchestrator/runner.py, mode ENFORCE by default) over every writer this
checkout registers, against the database named by the libpq environment (source ~/.config/pravaha/pgenv.sh first; never print it). The connection is
READ ONLY (default_transaction_read_only on, one SELECT, rolled back). Exit 0 and `gaps=[]` = the orchestrator's own pre-flight would let a build
run proceed; exit 3 names every gap. Run it as:  python3 registry_1243_gap_preflight.py <checkout-of-the-deployed-commit>/platform/python-sidecar
"""
import json, os, subprocess, sys
from pathlib import Path

SIDECAR = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[5] / "platform" / "python-sidecar"   # argv[1]: the sidecar dir of the deployed commit
SENT = "__GAP_PREFLIGHT_IDS__="
PROBE = f"import json\nfrom pipeline.orchestrator.writers import WRITER_REGISTRY, discover_all\ndiscover_all()\nprint({SENT!r} + json.dumps(sorted(WRITER_REGISTRY)))"


def main() -> int:
    done = subprocess.run([sys.executable, "-c", PROBE], cwd=SIDECAR, capture_output=True, text=True)
    if done.returncode != 0:
        print("STOP — writer discovery failed:\n" + done.stderr, file=sys.stderr); return 3
    ids = json.loads(next(l for l in reversed(done.stdout.splitlines()) if l.startswith(SENT))[len(SENT):])
    sys.path.insert(0, str(SIDECAR))
    import psycopg
    from psycopg.rows import dict_row
    import pipeline.orchestrator.writers as W
    from pipeline.orchestrator import runner
    mode = runner._WRITER_GAP_MODE
    W.WRITER_REGISTRY.clear(); W.WRITER_REGISTRY.update({k: object for k in ids})        # the registered ids the real check will read
    conn = psycopg.connect("", options="-c default_transaction_read_only=on -c application_name=registry_1243_preflight", row_factory=dict_row)
    try:
        with conn.cursor() as cur:
            gaps = runner._check_writer_registry_gaps(cur)
        conn.rollback()
    finally:
        conn.close()
    print(f"writer-gap mode={mode} registered_writers={len(ids)} gaps={gaps}")
    return 0 if not gaps else 3


if __name__ == "__main__":
    sys.exit(main())
