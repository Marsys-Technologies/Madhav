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
                       run_id: int, run_attempt: int = 1, approval_note: str, sealing_commit: str,
                       brief_id: int, producer_execution_id: str) -> dict[str, Any]:
    """The sealing step inside the caller's transaction, under the PINNED text-rendering session settings (F-R12-6): the publication
    digest `ledger.publish` stores is computed by the sealer's session and must be rendered exactly as the briefed one was."""
    with seal_brief.pinned_session(conn):
        return _seal_with_approval(conn, chart_id=chart_id, generation=generation, approved_digest=approved_digest,
                                   approver_login=approver_login, run_id=run_id, run_attempt=run_attempt,
                                   approval_note=approval_note, sealing_commit=sealing_commit, brief_id=brief_id,
                                   producer_execution_id=producer_execution_id)


def _seal_with_approval(conn, *, chart_id: str, generation: str, approved_digest: str, approver_login: str,
                        run_id: int, run_attempt: int = 1, approval_note: str, sealing_commit: str,
                        brief_id: int, producer_execution_id: str) -> dict[str, Any]:
    """`sealing_commit` is the sealing workflow's DEPLOY_SHA (it is inside the approved payload AND in the receipt);
    `approval_note` states on whose authority the approval was given."""
    if not approver_login.strip() or not str(sealing_commit).strip() or not approval_note.strip():
        raise ValueError("an approval receipt names the approver login, the approval note and the sealing workflow commit")
    run_id, run_attempt = int(run_id), int(run_attempt)
    # (1) locks → recompute → compare: refuse BEFORE anything is published
    payload = seal_brief.recompute_under_locks(conn, chart_id, generation, approved_digest, sealing_commit=sealing_commit)
    # (1b) F-R12-4: the approved digest must be the CURRENT brief the VERIFIER persisted for this candidate (the receipt's commit-time
    # trigger enforces the same; refusing here costs nothing and says why before anything is published)
    why = seal_brief.persisted_brief_problem(conn, chart_id, generation, payload["manifest"]["manifest_id"], approved_digest,
                                             brief_id=int(brief_id), sealing_commit=sealing_commit, execution_id=producer_execution_id)
    if why:
        raise seal_brief.ApprovalMismatch(f"{why}: the approval does not name the current brief the verifier persisted for this candidate "
                                          "(this brief id, produced by the sealing commit in this execution) — re-run the verifier's "
                                          "--brief and approve that one")
    # (2) publish, then the authoritative SQL seal (its triggers run the combined gate on the published row)
    gk_ledger.publish(conn, chart_id, generation)
    # (2b) re-check the candidate boundary AFTER publication, still under the seal locks: nothing may have changed between the
    # recompute and the publish (an unguarded write path would show here), and the digest publication stored must be the one the
    # approved payload carried. Any difference refuses the transaction — nothing stays published.
    after = seal_brief.payload_digest(seal_brief.build_payload(conn, chart_id, generation, sealing_commit=sealing_commit,
                                                                as_candidate=True))
    stored = conn.execute("SELECT content_digest FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s",
                          (chart_id, generation)).fetchone()
    stored = next(iter(stored.values())) if isinstance(stored, dict) else stored[0]
    if after != approved_digest or stored != payload["publication_content_digest"]:
        raise seal_brief.ApprovalMismatch(
            "the candidate changed between the approval recompute and publication (or the publication digest is not the approved "
            f"one): payload {after} vs approved {approved_digest}; stored content_digest {stored} vs approved "
            f"{payload['publication_content_digest']} — the transaction is refused, nothing stays published")
    manifest_id = conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (chart_id, generation)).fetchone()
    manifest_id = next(iter(manifest_id.values())) if isinstance(manifest_id, dict) else manifest_id[0]
    # (3) the approval receipt, linked to the seal row by its primary key
    conn.execute(
        "INSERT INTO public.ka_gochara_seal_approval (chart_id, generation, manifest_id, brief_digest, brief_id, producer_execution_id,"
        " approver_login, approved_by_note, run_id, run_attempt, workflow_commit)"
        " VALUES (%s::uuid, %s, %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s)",
        (chart_id, generation, manifest_id, approved_digest, int(brief_id), producer_execution_id, approver_login, approval_note,
         run_id, run_attempt, sealing_commit))
    # (4) a seal with no receipt is refused before COMMIT (the FK is deferred so either order works inside one transaction)
    if conn.execute("SELECT public.ka_gochara_seal_receipt_missing(%s::uuid, %s)", (chart_id, generation)).fetchone()[0]:
        raise RuntimeError("the generation is sealed but no approval receipt exists — the sealing transaction is refused")
    return {"manifest_id": str(manifest_id), "brief_digest": approved_digest, "payload": payload}


# ── the EXECUTABLE caller (R12-2): everything the sealing workflow's job does, as functions of an open connection ──────────────────

import json
import re

REQUIRED_POLICY = "all_null_candidate/1"
APPROVAL_SCHEMA = "seal_approval/2"
#: process exit codes of `pipeline/orchestrator/seal_job.py`
EXIT_SEALED, EXIT_REFUSED, EXIT_MISMATCH, EXIT_IDENTITY, EXIT_ERROR = 0, 2, 3, 4, 5
_HEX64 = re.compile(r"^[0-9a-f]{64}\Z")
#: the MECHANICAL approval note the workflow writes: the owner ruling id and the run's `github.triggering_actor` — never free text. A blank, a
#: sentence, or a note naming someone other than the running workflow's own triggering actor is refused.
NOTE_FORMAT = re.compile(r"^ruling:(?P<ruling>[A-Za-z0-9][A-Za-z0-9._#/-]{0,63}); actor:(?P<actor>[A-Za-z0-9][A-Za-z0-9-]{0,38}(?:\[bot\])?)\Z")
_COMMIT = re.compile(r"^[0-9a-f]{7,64}\Z")
#: the ONLY write privileges the sealer principal may hold (the seal, the publication flip, the receipt)
SEALER_WRITE_ALLOWED = frozenset({
    "INSERT on ka_gochara_generation_seal", "INSERT on ka_gochara_seal_approval",
    "UPDATE(status) on kala_gochara_publication", "UPDATE(published_at) on kala_gochara_publication",
    "UPDATE(content_digest) on kala_gochara_publication", "UPDATE(row_counts) on kala_gochara_publication"})


class SealRefused(RuntimeError):
    """Nothing was written: an input, the approval, the policy or the connection is not what the sealing job requires."""

    def __init__(self, code: str, detail: str, *, exit_code: int = EXIT_REFUSED):
        super().__init__(f"refused:{code} — {detail}")
        self.code, self.detail, self.exit_code = code, detail, exit_code


def parse_approval(text: str | None) -> dict:
    """The approval record the workflow writes from the GitHub approval of THIS run (schema `seal_approval/1`):
    {schema, brief_digest, brief_id, producer_execution_id, run_id, run_attempt, approver_login, approved_by_note}. `brief_id` and
    `producer_execution_id` are the SPECIFIC persisted brief and the verifier execution the approval is for (R13-3: taken from the compact
    line of THIS workflow run's brief job — or, for an explicit reuse, from the earlier run's still-current brief). Absent / malformed ⇒ refused."""
    if not text or not text.strip():
        raise SealRefused("approval_absent", "no approval record was supplied")
    try:
        a = json.loads(text)
    except ValueError as exc:
        raise SealRefused("approval_malformed", f"the approval record is not JSON: {exc}") from exc
    if not isinstance(a, dict) or a.get("schema") != APPROVAL_SCHEMA:
        raise SealRefused("approval_malformed", f"the approval record is not {APPROVAL_SCHEMA}")
    digest, login, note = a.get("brief_digest"), a.get("approver_login"), a.get("approved_by_note")
    if not isinstance(digest, str) or not _HEX64.match(digest):
        raise SealRefused("approval_malformed", "brief_digest is not a lowercase sha256")
    for k in ("run_id", "run_attempt", "brief_id"):
        if not isinstance(a.get(k), int) or isinstance(a.get(k), bool) or a[k] < 1:
            raise SealRefused("approval_malformed", f"{k} is not a positive integer")
    if not isinstance(a.get("producer_execution_id"), str) or not a["producer_execution_id"].strip():
        raise SealRefused("approval_malformed", "producer_execution_id is blank")
    for k, v in (("approver_login", login), ("approved_by_note", note)):
        if not isinstance(v, str) or not v.strip():
            raise SealRefused("approval_malformed", f"{k} is blank")
    if not NOTE_FORMAT.match(note):
        raise SealRefused("approval_note_not_mechanical", "approved_by_note must be exactly 'ruling:<ruling id>; actor:<github "
                          "triggering actor>' as the workflow writes it — a free-typed note is refused")
    return a


def check_approval_note(note: str, triggering_actor: str | None) -> dict:
    """The note's `actor` must be the RUNNING workflow's own `github.triggering_actor` (its environment, like the run id): the note is
    taken from the approval file as the workflow wrote it, and a note naming anyone else — or run where the workflow names no actor — is
    refused. Returns `{ruling, actor}`."""
    m = NOTE_FORMAT.match(note or "")
    if not m:
        raise SealRefused("approval_note_not_mechanical", "approved_by_note is not 'ruling:<ruling id>; actor:<github triggering actor>'")
    if not isinstance(triggering_actor, str) or not triggering_actor.strip():
        raise SealRefused("triggering_actor_absent", "GITHUB_TRIGGERING_ACTOR is not set: the approval note cannot be checked against "
                          "the run that is sealing")
    if m.group("actor").lower() != triggering_actor.strip().lower():
        raise SealRefused("approval_note_actor_mismatch", f"the note names actor {m.group('actor')!r}, this run's triggering actor is "
                          f"{triggering_actor.strip()!r}")
    return {"ruling": m.group("ruling"), "actor": m.group("actor")}


def _one(row):
    return None if row is None else (next(iter(row.values())) if isinstance(row, dict) else row[0])


def check_sealer_identity(conn) -> dict:
    """Refuse unless this session is the SEALER principal: logged in as `gochara_sealer` itself (session_user == current_user — the job
    never uses SET ROLE), not a superuser, not the builder or the verifier or a member of either — NOR A MEMBER OF ANY ROLE THAT OWNS THE
    GOCHARA TABLES, `NOINHERIT` membership included (`pg_has_role(..., 'MEMBER')`, the same test the verifier applies; R13-5) — and holding no
    write privilege, at TABLE or COLUMN level, anywhere on the Gochara tables beyond the seal, the publication flip and the receipt: the
    verification tables and the brief table are inspected like every other (a column-only INSERT/UPDATE grant on them is refused)."""
    from . import verification_job as vj
    who = conn.execute("SELECT current_user, session_user").fetchone()
    user, session = tuple(who.values()) if isinstance(who, dict) else tuple(who)
    if user != "gochara_sealer" or session != "gochara_sealer":
        raise SealRefused("identity_not_sealer", f"session_user {session!r} / current_user {user!r}: the sealing job runs ONLY as the "
                          "gochara_sealer login", exit_code=EXIT_IDENTITY)
    if _one(conn.execute("SELECT rolsuper FROM pg_roles WHERE rolname = current_user").fetchone()):
        raise SealRefused("identity_not_sealer", "the sealer is a superuser", exit_code=EXIT_IDENTITY)
    for other in ("data_plane_builder", "gochara_verifier"):
        if vj._role_exists(conn, other) and _one(conn.execute("SELECT pg_has_role(current_user, %s, 'MEMBER')", (other,)).fetchone()):
            raise SealRefused("identity_not_sealer", f"the sealer is a member of {other}", exit_code=EXIT_IDENTITY)
    for owner in vj._builder_owner_roles(conn):
        if user == owner or _one(conn.execute("SELECT pg_has_role(current_user, %s, 'MEMBER')", (owner,)).fetchone()):
            raise SealRefused("identity_not_sealer", f"the sealer is, or is a member of, {owner}, which OWNS the Gochara tables",
                              exit_code=EXIT_IDENTITY)
    held = [h for h in vj._write_surface(conn, user, exempt=()) if h not in SEALER_WRITE_ALLOWED]
    if held:
        raise SealRefused("identity_not_sealer", f"the sealer holds write privileges beyond the seal set: {held}",
                          exit_code=EXIT_IDENTITY)
    return {"login": user, "session": session}


def execute_seal(conn, *, chart_id: str, generation: str, approval: dict, run_id: int, run_attempt: int, sealing_commit: str,
                 triggering_actor: str | None, required_policy: str = REQUIRED_POLICY, enforce_identity: bool = True) -> dict[str, Any]:
    """The sealing job's whole act, owning ONE explicit transaction on an AUTOCOMMIT connection: inputs and approval validated (nothing
    touched), the connection proven to be the sealer, then — inside the transaction — the seal locks, the policy requirement, the
    approval RECOMPUTE (refused on any mismatch BEFORE publishing), publication, the authoritative seal, the receipt, the post-publication
    boundary re-check. A failure anywhere — the receipt included — rolls publication back too. `run_id` / `run_attempt` /
    `sealing_commit` / `triggering_actor` are what the RUNNING workflow says it is (its environment); the approval must have been given for
    exactly them, and its note must be the mechanical `ruling:<id>; actor:<triggering actor>`."""
    from . import verification_job as vj
    from .result_policy import manifest_policy
    if not isinstance(run_id, int) or run_id < 1 or not isinstance(run_attempt, int) or run_attempt < 1:
        raise SealRefused("run_identity_malformed", "the run id / attempt are not positive integers")
    if not isinstance(sealing_commit, str) or not _COMMIT.match(sealing_commit):
        raise SealRefused("sealing_commit_malformed", "the sealing commit (DEPLOY_SHA) is absent or not a hex commit id")
    if (approval["run_id"], approval["run_attempt"]) != (run_id, run_attempt):
        raise SealRefused("approval_not_for_this_run", f"the approval was given for run {approval['run_id']} attempt "
                          f"{approval['run_attempt']}, this is run {run_id} attempt {run_attempt}")
    check_approval_note(approval["approved_by_note"], triggering_actor)
    if not getattr(conn, "autocommit", False):
        raise SealRefused("connection_not_autocommit", "the sealing job owns its transaction: it needs an autocommit connection")
    if enforce_identity:
        check_sealer_identity(conn)
    import psycopg
    try:
        with conn.transaction():
            # bounded waits (steward ruling): a held lock or a runaway statement ends in a NAMED refusal; the transaction rolls back, so
            # nothing stays published
            seal_brief.set_local_timeouts(conn, statement=seal_brief.SEAL_STATEMENT_TIMEOUT, lock=seal_brief.SEAL_LOCK_TIMEOUT)
            vj.take_locks(conn, chart_id)
            policy = manifest_policy(conn, chart_id, generation)
            if policy != required_policy:
                raise SealRefused("wrong_policy", f"the manifest selects {policy!r}; this milestone's sealing job requires "
                                  f"{required_policy!r}")
            return seal_with_approval(conn, chart_id=chart_id, generation=generation, approved_digest=approval["brief_digest"],
                                      approver_login=approval["approver_login"], run_id=run_id, run_attempt=run_attempt,
                                      approval_note=approval["approved_by_note"], sealing_commit=sealing_commit,
                                      brief_id=approval["brief_id"], producer_execution_id=approval["producer_execution_id"])
    except psycopg.errors.LockNotAvailable as exc:
        raise SealRefused("seal_lock_timeout", f"a seal lock was not available within {seal_brief.SEAL_LOCK_TIMEOUT} — another build, "
                          f"verification or seal holds it; nothing was published ({exc})") from exc
    except psycopg.errors.QueryCanceled as exc:
        raise SealRefused("seal_statement_timeout", f"a statement exceeded {seal_brief.SEAL_STATEMENT_TIMEOUT} (or was cancelled); the "
                          f"sealing transaction was rolled back, nothing was published ({exc})") from exc


__all__ = ["APPROVAL_SCHEMA", "REQUIRED_POLICY", "SEALER_WRITE_ALLOWED", "SealRefused", "check_sealer_identity", "execute_seal",
           "check_approval_note", "parse_approval", "seal_with_approval"]
