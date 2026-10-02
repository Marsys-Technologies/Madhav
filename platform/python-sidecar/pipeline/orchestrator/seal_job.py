"""Entry point of the SEALING job (Codex round 12, R12-2) — the executable caller the approval-gated workflow runs.

    python -m pipeline.orchestrator.seal_job --chart <uuid> [--generation 5.0] --approval-file <approval.json>

NOT a registered writer and not in the build DAG. Run only by the `gochara-seal` workflow, in the job that mounts the sealer credential.
It reads exactly ONE database credential, `GOCHARA_SEALER_DB_URL`; its first act is the identity self-check (it refuses to run as anything
but the `gochara_sealer` login) — and BEFORE any database contact it checks that the code it is running is the code registered for the
sealing commit (`implementation_digest.lock.json`; refused, exit 4, otherwise). It owns ONE explicit transaction: seal locks → the policy requirement (`all_null_candidate/1`) → the
approval RECOMPUTE (refused on any mismatch before publishing) → publication → the authoritative seal → the receipt → the
post-publication boundary re-check; a failure anywhere rolls publication back too.

INTERFACE (agreed with Stream B through the steward):
  --approval-file   JSON written by the workflow from the GitHub approval of THIS run (schema `seal_approval/2`, ST-WIRE-2):
                    {"schema": "seal_approval/2", "brief_digest": <sha256>, "brief_id": <int>, "execution_id": <str>, "run_id": <int>,
                     "run_attempt": <int>, "approver_login": <str>, "approved_by_note": "ruling:<owner ruling id>; actor:<github.triggering_actor>"}
                    `brief_id` is the persisted brief the approval is for and `execution_id` the verifier execution that produced it; the job
                    refuses unless that brief is the CURRENT persisted one, with the approved digest, produced by the sealing commit in that execution.
                    The note is MECHANICAL — exactly that format, written by the workflow, never free text; its actor must be this run's
                    GITHUB_TRIGGERING_ACTOR (a blank, a sentence, or another person's name is refused).
  environment       GITHUB_RUN_ID, GITHUB_RUN_ATTEMPT — the approval must have been given for exactly this run and attempt;
                    GITHUB_TRIGGERING_ACTOR — the actor the note must name;
                    GOCHARA_SEALING_COMMIT — the sealing revision (DEPLOY_SHA); it is part of the briefed payload, so a different
                    revision than the one briefed is a different digest and is refused.
Prints one JSON object on stdout. Exit codes: 0 sealed · 2 refused (nothing written) · 3 the approval does not match the candidate
(stale, changed, or wrong revision — nothing written) · 4 identity self-check failed · 5 unexpected error (the transaction rolled back)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from services.gochara_kernel import seal_brief
from services.gochara_kernel import seal_flow as sf

ENV_URL = "GOCHARA_SEALER_DB_URL"


def _int_env(name: str):
    v = os.environ.get(name)
    return int(v) if v is not None and v.isdigit() else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="seal_job", description=__doc__.split("\n\n")[0])
    ap.add_argument("--chart", required=True)
    ap.add_argument("--generation", default="5.0")
    ap.add_argument("--approval-file", default=None)
    args = ap.parse_args(argv)
    try:
        sf.check_own_checkout()                     # ST-WIRE-2: the code this job runs == the registered digest — before ANY database contact
    except sf.SealRefused as exc:
        print(json.dumps({"status": "REFUSED", "code": exc.code, "detail": exc.detail}))
        return exc.exit_code
    url = os.environ.get(ENV_URL)
    if not url:
        print(json.dumps({"status": "REFUSED", "code": "no_sealer_credential", "detail": f"{ENV_URL} is not set"}))
        return sf.EXIT_IDENTITY
    try:
        text = Path(args.approval_file).read_text() if args.approval_file else None
    except OSError as exc:
        text = None
    try:
        approval = sf.parse_approval(text)
        run_id, run_attempt = _int_env("GITHUB_RUN_ID"), _int_env("GITHUB_RUN_ATTEMPT")
        if run_id is None or run_attempt is None:
            raise sf.SealRefused("run_identity_absent", "GITHUB_RUN_ID / GITHUB_RUN_ATTEMPT are not set to integers")
        import psycopg
        conn = psycopg.connect(url, autocommit=True)
    except sf.SealRefused as exc:
        print(json.dumps({"status": "REFUSED", "code": exc.code, "detail": exc.detail}))
        return exc.exit_code
    try:
        out = sf.execute_seal(conn, chart_id=args.chart, generation=args.generation, approval=approval, run_id=run_id,
                              run_attempt=run_attempt, sealing_commit=os.environ.get("GOCHARA_SEALING_COMMIT", ""),
                              triggering_actor=os.environ.get("GITHUB_TRIGGERING_ACTOR"))
        print(json.dumps({"status": "SEALED", "manifest_id": out["manifest_id"], "brief_digest": out["brief_digest"],
                          "run_id": run_id, "run_attempt": run_attempt}, sort_keys=True))
        return sf.EXIT_SEALED
    except sf.SealRefused as exc:
        print(json.dumps({"status": "REFUSED", "code": exc.code, "detail": exc.detail}))
        return exc.exit_code
    except seal_brief.ApprovalMismatch as exc:
        print(json.dumps({"status": "REFUSED", "code": "approval_mismatch", "detail": str(exc)}))
        return sf.EXIT_MISMATCH
    except Exception as exc:  # noqa: BLE001 — the transaction rolled back; say so, exit 5
        print(json.dumps({"status": "ERROR", "detail": f"{type(exc).__name__}: {exc}"}))
        return sf.EXIT_ERROR
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
