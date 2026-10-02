#!/usr/bin/env python3
"""RECONCILE the generation's seal state after the sealing step — success OR ambiguous failure (R13-4).

A failed workflow status does not prove the sealing transaction rolled back: a lost connection or a cancelled runner around COMMIT can leave it committed (or not) with no acknowledgement. This
read-only step, run in the gated job with the same sealer credential, reads the publication row, the seal row(s) and the approval receipt of the generation and REPORTS what is actually true:

  SEALED         (exit 0)   publication `published`, exactly one seal row, exactly one receipt naming the approved digest, this run and this attempt
  NOT_SEALED     (exit 10)  publication `candidate`, no seal row, no receipt — nothing was published; the candidate is untouched and a FRESH run may be started
  INCONSISTENT   (exit 11)  anything else (e.g. sealed with a receipt of another run/digest, or a seal without a receipt): STOP and report; do not retry
  UNREADABLE     (exit 12)  the database could not be read (the outcome is UNKNOWN): reconcile by hand before any retry

It prints one JSON line (no secret). It never writes. The workflow reports the state in the run summary instead of inferring it from the seal step's status."""
from __future__ import annotations

import argparse
import json
import os
import sys

EXIT = {"SEALED": 0, "NOT_SEALED": 10, "INCONSISTENT": 11, "UNREADABLE": 12}


def classify(pub_status, seals: int, receipts: list, *, digest: str, run_id: int, attempt: int) -> tuple[str, str]:
    if pub_status == "candidate" and seals == 0 and not receipts:
        return "NOT_SEALED", "the candidate was not published and not sealed; no receipt exists"
    if pub_status == "published" and seals == 1 and len(receipts) == 1:
        r = receipts[0]
        if (r["brief_digest"], r["run_id"], r["run_attempt"]) == (digest, run_id, attempt):
            return "SEALED", "published, sealed, and the receipt names this run's approved digest"
        return "INCONSISTENT", "the generation is sealed but its receipt names another digest, run or attempt"
    return "INCONSISTENT", f"publication {pub_status!r}, {seals} seal row(s), {len(receipts)} receipt(s): not a state this workflow can produce"


def read_state(conn, chart_id: str, generation: str):
    pub = conn.execute("SELECT status FROM public.kala_gochara_publication WHERE chart_id = %s::uuid AND generation = %s", (chart_id, generation)).fetchall()
    seals = conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal WHERE chart_id = %s::uuid AND generation = %s", (chart_id, generation)).fetchone()
    recs = conn.execute("SELECT brief_digest, run_id, run_attempt FROM public.ka_gochara_seal_approval WHERE chart_id = %s::uuid AND generation = %s", (chart_id, generation)).fetchall()
    first = lambda r: tuple(r.values()) if isinstance(r, dict) else tuple(r)                   # noqa: E731
    statuses = [first(r)[0] for r in pub]
    if len(statuses) != 1:
        return None, int(first(seals)[0]), [dict(zip(("brief_digest", "run_id", "run_attempt"), first(r))) for r in recs]
    return statuses[0], int(first(seals)[0]), [dict(zip(("brief_digest", "run_id", "run_attempt"), first(r))) for r in recs]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chart-id", required=True)
    ap.add_argument("--generation", required=True)
    ap.add_argument("--brief-digest", required=True)
    ap.add_argument("--run-id", required=True, type=int)
    ap.add_argument("--attempt", required=True, type=int)
    a = ap.parse_args(argv)
    url = os.environ.get("GOCHARA_SEALER_DB_URL")
    try:
        if not url:
            raise RuntimeError("GOCHARA_SEALER_DB_URL is not set")
        import psycopg
        conn = psycopg.connect(url, autocommit=True, connect_timeout=20)
        try:
            pub, seals, recs = read_state(conn, a.chart_id, a.generation)
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001 — whatever went wrong, the outcome is UNKNOWN, never "not sealed"
        print(json.dumps({"state": "UNREADABLE", "detail": f"{type(exc).__name__}: {str(exc)[:200]}"}, sort_keys=True))
        return EXIT["UNREADABLE"]
    state, why = classify(pub, seals, recs, digest=a.brief_digest, run_id=a.run_id, attempt=a.attempt)
    print(json.dumps({"state": state, "why": why, "publication": pub, "seal_rows": seals, "receipts": len(recs)}, sort_keys=True))
    return EXIT[state]


if __name__ == "__main__":
    sys.exit(main())
