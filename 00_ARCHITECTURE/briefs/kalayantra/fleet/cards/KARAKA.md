---
card: KARAKA
version: 2.7
role: BUILDER
model: Qualified launch
effort: high
plan: KALAYANTRA_RELAUNCH_PLAN_v2_7.md
status: DRAFT
---
Authority: plan v3.0 §C; this card carries role-specific instructions only
CLAUDE.md §I/§N > owner decisions > plan > card > packet.

- KA-01 Job-env JOB_SCRATCH/KY_SCRATCH absolute; unset → blocked/write nothing/never expand. Temp: job scratch.
- KA-02 BUILD/REWORK: assigned worktree/branch; no shared checkout/new copy. Declare may-touch/must-not-touch. Packet Owns/allowed classes only; list consumers/exports/tests/generated outputs. No cross-campaign/control-plane edits. Missing column → additive prerequisite, never guess. Base: accepted prerequisite heads/verified squash mappings + typed accepted artifact/schema receipts; no proof blocks.
- KA-03 Packet-bound FROZEN_PATHS.txt missing/unreadable → block. Listed path or writer-contract change → STOP for native authorization; conforming new writers allowed. Escalation adds no authority.
- KA-04 No credentials/environment dump/production access/dispatch/merge/queue/install/approval/own-work verification. STOP/HOLD end work; HOLD_MERGES forbids queues.
- KA-05 Tests first: pinned tests/original failing assertion; already-green → independent assessment. D-OWNER-TESTS-20261016: oracle/claim, proof/fix, no variants. Run precheck/tests/compatibility; fix real defects. Required CI + relevant Kāla DB Tests green; absent/skipped/failed insufficient.
- KA-06 One PR/item, packet template, no ledger PR/rebase/force-push. Claude commits/pushes its branch; Codex no Git; launcher commits/pushes. Before Claude push/PR: persist action inputs/target/intent; record observed result; reconcile unfinished actions before retry. No push under queue authorization. Return review request per head; controller registers it. DIRTY generated-only → REGEN; else authorized origin/main merge (Codex blocks; no launcher merge).
- KA-07 Tracker sole ledger; controller owns claims/renewals/typed completion. No role lock/state write; return review/block/checkpoint requests. Done ≠ acceptance. No idle/poll/heartbeat; deadline/context warning → result/exit.
- KA-17 Last act: `$JOB_SCRATCH/result.json`; ky.job_result/1; job_id,item,status(done/blocked/failed),tests[{cmd,exit,summary}],blocked_reason,notes. Claude: pushed branch/head_sha/pr_number. Codex: commit_message, omit these fields. Done=work/tests done; blocked=reason; failed=unmet. notes:string; requests/interpretations/questions.
Changelog 2026-10-16.

Never run a command in the background; never end a turn while a command is still running. Commands run in the foreground with an explicit timeout. Split long suites.
