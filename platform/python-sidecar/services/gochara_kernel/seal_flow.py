"""The SEALER's side of the approved seal (Codex round 11, R11-3): ONE transaction that recomputes the approval payload under the
seal locks, refuses on any mismatch BEFORE publishing, publishes the candidate, runs the authoritative SQL seal (whose triggers run
the combined gate on the PUBLISHED row) and writes the approval receipt, durably linked to the seal row. Any failure rolls the
whole transaction back: nothing is half-published, no receipt exists without its seal.

The caller (the approval-gated sealing workflow, running as the sealer principal) owns the connection and the transaction; this
function never commits. The approval record (login, run id, attempt, note) is what GitHub's approval gave the workflow."""
from __future__ import annotations

from typing import Any

from . import ledger as gk_ledger
from . import seal_brief


def seal_with_approval(conn, *, chart_id: str, generation: str, approved_digest: str, approver_login: str,
                       run_id: str, run_attempt: int = 1, approval_note: str = "", sealing_commit: str | None = None) -> dict[str, Any]:
    if not approver_login or not run_id:
        raise ValueError("an approval receipt names the approver login and the run id")
    # (1) locks → recompute → compare: refuse BEFORE anything is published
    payload = seal_brief.recompute_under_locks(conn, chart_id, generation, approved_digest, sealing_commit=sealing_commit)
    # (2) publish, then the authoritative SQL seal (its triggers run the combined gate on the published row)
    gk_ledger.publish(conn, chart_id, generation)
    manifest_id = conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (chart_id, generation)).fetchone()
    manifest_id = next(iter(manifest_id.values())) if isinstance(manifest_id, dict) else manifest_id[0]
    # (3) the approval receipt, linked to the seal row by its primary key
    conn.execute(
        "INSERT INTO public.ka_gochara_seal_approval (chart_id, generation, manifest_id, brief_digest, approver_login,"
        " approval_note, run_id, run_attempt, sealing_commit) VALUES (%s::uuid, %s, %s::uuid, %s, %s, %s, %s, %s, %s)",
        (chart_id, generation, manifest_id, approved_digest, approver_login, approval_note, str(run_id), int(run_attempt),
         sealing_commit))
    return {"manifest_id": str(manifest_id), "brief_digest": approved_digest, "payload": payload}


__all__ = ["seal_with_approval"]
