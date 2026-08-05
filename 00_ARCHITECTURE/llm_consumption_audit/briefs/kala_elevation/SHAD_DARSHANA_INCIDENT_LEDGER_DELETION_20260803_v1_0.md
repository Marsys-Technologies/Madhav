---
artifact: SHAD_DARSHANA_INCIDENT_LEDGER_DELETION_20260803
canonical_id: SHAD_DARSHANA_INCIDENT_LEDGER_DELETION_20260803
version: 1.0
status: CLOSED — incident record; preserved 2026-08-06 during ledger-divergence cleanup
created: 2026-08-06
incident_date: 2026-08-03 ~22:08 UTC
governing: ONGOING_HYGIENE_POLICIES_v1_0.md (incident-record discipline; precedent
  SAMAPTI_SECURITY_INCIDENT_DB_CREDENTIAL_v1_0.md)
---

# INCIDENT — SHAD_DARSHANA_STATE.md deleted out from under a live session (2026-08-03)

## §1 What happened

At ~22:08 UTC on 2026-08-03, the campaign ledger `SHAD_DARSHANA_STATE.md` was found
**deleted** from the main-checkout working directory (`/Users/Dev/Vibe-Coding/Apps/Madhav`,
branch `int-929-final`) while the int-929 session was actively using it — not truncated,
not moved, gone. The session reconstructed the file from its own conversation record and
prepended the RESTORATION NOTICE preserved verbatim in §2 below. That reconstruction lived
only as an untracked local file — on no branch — until this record was created.

**Named probable cause (by the affected session):** multiple concurrent, fully-autonomous
(`--permission-mode bypassPermissions`) Claude Code processes on the same machine, each
independently narrating the same task from the same pasted native-directive prompt, with a
parallel worktree session (`.worktrees/shad-darshana-conductor`) holding its own
actively-modified 2445-line copy of the same file. The affected session assessed that the
other session's tooling most likely performed the deletion, and explicitly declined to
adjudicate between the two sessions' contradictory narrations.

## §2 The RESTORATION NOTICE — verbatim

> ## ⚠ RESTORATION NOTICE (2026-08-03 ~22:15 UTC, int-929 session, main checkout)
>
> **This file was found DELETED from this working directory (main checkout, branch
> `int-929-final`) at ~22:08 UTC — not truncated, not moved, gone — while this session was
> actively using it.** What follows below (down to the "END OF RESTORED CONTENT" marker) is
> this session's own best-effort reconstruction from its own conversation record (everything
> this session itself wrote and read back), covering the file's live NEXT-ACTION history from
> this session's ~10:24 UTC entry onward, plus everything this session had separately read of
> the pre-existing GATE W1 / GATE W0 / MERGE-TRAIN / audit history beneath it. **Content this
> session never read into its own context (this file was 1110+ lines before tonight and had
> grown further since) is NOT recovered here and may be permanently lost from this specific
> copy.**
>
> **Why this almost certainly happened:** this machine has multiple concurrent, fully-autonomous
> (`--permission-mode bypassPermissions`) Claude Code processes running right now, including a
> separate, actively-updated (2445 lines, modified this same minute) copy of this same file at
> `.worktrees/shad-darshana-conductor/00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
> SHAD_DARSHANA_STATE.md`, whose own NEXT-ACTION describes an "INT-929 SESSION" with the same
> chart IDs, same 10:24–21:14 UTC window, and a claim that the native "explicitly LIFTED tonight's"
> descope — a claim this session's own live conversation with the native never made or confirmed,
> and which this session independently found contradicted by git (`origin/shad-darshana/
> integration` HEAD unchanged since 2026-08-02 21:03 IST — no rebase, no force-push occurred,
> despite that other copy's claim that one did). **Read as: the real native likely pasted the
> same governing native-directive prompt into more than one Claude Code window tonight; this
> session and the `shad-darshana-conductor` worktree session are each independently narrating
> the same task, unaware of each other, and something (most likely the other session's own
> tooling) deleted this copy.** The native should reconcile the two sessions directly — this
> session is not attempting to adjudicate between them.

## §3 Disposition (2026-08-06)

1. **Branch ledgers reconciled without loss.** The two-way divergence between
   `origin/main` and `origin/shad-darshana/integration` copies of the ledger was resolved
   by content-preserving merge (`4079a50d` on `shad-darshana/integration`); a line-level
   `comm` audit confirmed zero unique-to-main lines lost.
2. **Full stale local copy archived verbatim** (559 lines, including the notice and the
   session's reconstruction with its SESSION-A-SWEEP close-out detail) at
   `99_ARCHIVE/BRIEFS_RETIRED/SHAD_DARSHANA_STATE_STALE_LOCAL_COPY_20260806.md` — committed
   alongside this record. No line-by-line adjudication of which reconstruction content is
   duplicated on the branch ledgers was attempted; the archive keeps everything.
3. **Untracked local file deleted** from the main checkout after (1) and (2) landed, ending
   the shadow-copy hazard the incident created.

## §4 Lesson (durable)

Concurrent autonomous sessions sharing one checkout can destroy each other's uncommitted
state. The standing mitigations already in force: worktree isolation per lane
(WORKTREE_ISOLATION_PROTOCOL_v1_0.md), single-writer rule for the campaign ledger with
attributed entries, and commit-early discipline for anything a session cannot afford to
lose. An uncommitted file in a shared checkout has no owner and no protection.
