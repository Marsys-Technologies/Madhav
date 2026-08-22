# PARIŚEṢA V4 — FULL WRAP Kickoff (paste this into the resumed Claude Code CLI session)

## 0. First, confirm you actually resumed — don't assume it

You were relaunched via `claude --resume <uuid>` after a tmux/CLI restart. Before
doing anything else: confirm you have this campaign's actual prior context (check
your own conversation history, or that you recognize PARIŚEṢA-V4, the Madhav repo,
and `parisesa/campaign-state`). If you do NOT have that context — i.e. this came up
as a fresh session despite `--resume` — STOP and say so explicitly rather than
proceeding as if you remember something you don't. Do not silently restart the
campaign from zero.

If continuity is confirmed: **this is a RESUME, not a restart.** Nothing about the
interruption (CLI update + tmux restart) changes any ruling, authority grant, or
in-flight work below. Re-verify everything in §1 against live sources before
trusting any number in this document — time has passed since it was written.

## 1. Mandatory first actions (in order)

1. Read `00_ARCHITECTURE/briefs/parisesa/state/RESUME.md` and `heartbeat.json` on
   `parisesa/campaign-state`.
2. Pull `state/ledger.json` fresh and recompute terminal vs non-terminal yourself
   from each finding's own `status` (terminal = SERVICE_CLOSED, CONTROL_CLOSED,
   HISTORICAL_STALE_CLOSED, NOT_APPLICABLE_CLOSED). Do not reuse any count from
   this document or any prior report.
3. Run `00_ARCHITECTURE/briefs/parisesa/scripts/check_ledger_pr_sync.py` and
   triage every candidate it returns individually (it's read-only and has known
   false-positive modes — documented in its own docstring).
4. Check `STOP.flag` in the conductor worktree root. If present, halt — that
   overrides everything, always, no exception.
5. Check the live GitHub state of every PR that was mid-review at last known
   contact: **#1439 (F-147)** — was cycling through GA-5 DO-NOT-MERGE →
   addendum → re-review; **#1437 (F-183)** — needed a GA-5 review dispatched,
   may still be waiting; **#1438 (F-182)** — was GA-5 MERGE-WITH-FOLLOWUP and
   enqueued, confirm it actually landed and chase its followup item. Resolve
   each to a real conclusion, not an assumption.

## 2. Standing authority (unchanged — re-confirm the void conditions still hold)

Full v3.0 authority remains in force: unattended merges (GA-5: independent
review + Opus-5 adversarial pre-merge review + fresh coordination-lease read),
unattended deploys (canary → smoke → promote, auto-rollback), GA-3
protected-data execution once a complete R-7-amended packet exists (FK-complete
replica for rollback rehearsal; before-image scope verified against *measured*
rows_written, not assumed), GA-2 architecture decide-and-act (journal rationale
+ rejected alternatives), synthetic/dev live-session access. Sonnet 5 default,
**Opus 5 for every judgment-critical action** — adversarial reviews,
irreversible calls, domain-correctness verification.

This rests on: pre-launch/no real customers, non-durable/non-sensitive data,
and the owner's standing delegation. If any of those has changed, stop and
check with the owner before relying on the rest of this section — do not infer
it silently from context.

Isolation absolutes, never relaxed by any autonomy grant: PARIPRAŚNA (live,
zero shared findings, pure contention hazard — never touch) and all dormant
sibling namespaces (`par/*`, `ekv/*`, `samapti`, `sampurti`, etc. — read-only
prior-work evidence, never write) stay off-limits. Lease discipline via
`origin/campaign-coordination` before any merge/deploy. No stash/gc/prune/
force-push, no credential operations, ever.

Owner rulings R-1 through R-9 (`OWNER_RULINGS_20260821.md`) stand as issued and
apply to every structurally similar item you encounter — use them as precedent,
not just for the specific findings they name. For any **new** classical/
scholarly-judgment question that doesn't fall under an existing ruling's scope
(the F-23 carve-out class), draft a provisional ruling exactly as F-23 did —
investigate fully, state confidence, list open questions — but do **not**
decide it unilaterally. Engineering/operational judgment stays under your own
GA-2 authority; classical-content authority does not, unless the owner
explicitly re-delegates it the way F-23's four questions were.

## 3. The directive — close this out fully, extensively, not on a clock

No deadline gates this. Keep going until every finding in the ledger is either
terminal, or sits at a correctly-scoped, explicitly-justified non-terminal end
state (DATA_PARKED with an authored, ready, or executed packet; EXTERNAL_HOLD
with a genuine external dependency named; PROVISIONAL_RULING awaiting
scholarly confirmation) — never left silently uncategorized. Work roughly in
this order, adjusting for whatever §1's fresh read actually shows:

1. **Finish every in-flight review cycle first** — #1439/F-147, #1437/F-183,
   #1438/F-182 and its followup — before starting new work.
2. **Formally triage every informally-noted new finding** you find in recent
   journal entries (F-190, F-191, and anything newer) — real F-number intake,
   not left as a parenthetical.
3. **Execute the 6 DATA_PARKED GA-3 rebuilds**: F-35 (system-wide, most
   shovel-ready — code fix already independently confirmed correct), F-52,
   F-62, F-63, F-71 (packets already authored for these five), and F-104
   (needs a properly-scoped 10-asset packet authored from scratch). Full
   R-7-amended packet discipline on every one: FK-complete rollback rehearsal,
   before-images verified against measured rows_written, quiescence proof.
4. **F-141's rebuild chain**: R-6's condition 1 (F-149 landed) is only *fully*
   clear once F-185 (pin `KA_KSHETRA_HASH_SPILL_DIR` to real, non-tmpfs disk,
   ≥8GB free) and F-186 (audit sibling loaders for the same unbounded-memory
   pattern) have also landed — confirm both before treating condition 1 as
   satisfied. Then author condition 2 (the GA-3 packet itself) and satisfy
   condition 3 (archive-then-supersede the pre-rebuild `ka_kshetra` snapshot to
   `campaign-state` — never overwrite first). Execute the rebuild only once
   all three conditions are demonstrably met, in that order.
5. **F-23 Lanes 2–3** under R-1..R-4 — confirm F-180/F-178 have actually landed
   first (its own ledger entry gates on this).
6. **Sweep everything else remaining** — every DECISION_PARKED, EXTERNAL_HOLD,
   UNKNOWN, or LANDED-not-terminal row not already covered above. Investigate
   each on its actual merits. Where a genuinely new external or owner-specific
   blocker exists, park it explicitly with the specific reason recorded — don't
   force it, and don't leave it unexamined either.

## 4. Execution discipline (unchanged, restated because it matters)

GA-5 (independent review + Opus-5 adversarial pre-merge review, explicitly
briefed to find a reason NOT to merge) before every merge, no exceptions.
Mutation-test every security or logic fix (revert it, confirm the specific
test goes red, restore, confirm it passes). Fresh coordination-lease read
before every merge/deploy. Journal every decision with its rationale and
rejected alternatives — this is what lets any single ruling be overruled later
without touching anything else. Disclose your own errors the moment you find
them, the same way this campaign has every time so far — that discipline is
not optional and it is the single thing most responsible for this campaign's
credibility so far.

## 5. When the backlog is genuinely exhausted

Write a closure report in the same structure as
`CLOSURE_REPORT_V3_1_20260821.md`: headline numbers (recomputed, not carried
forward), an item-by-item outcome table, every process-integrity disclosure in
full, and a recommendation section for whoever picks this up next. Not before
the backlog is actually dry — this directive has no deadline, so don't write a
premature closure just because a review cycle feels long.
