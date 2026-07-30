---
artifact: WORKTREE_ISOLATION_PROTOCOL
canonical_id: WORKTREE_ISOLATION_PROTOCOL
version: 1.0
status: CURRENT
authored_by: SAMĀPTI conductor session (Claude Code, Opus), 2026-07-30/31
implements: INF-1 (worktree isolation) + INF-4/5 (stale-worktree hygiene), part of SAMĀPTI's
  protective set landed per DVA Ruling 83.
purpose: >
  The standing rule for where build/audit/fix work happens in this repository. Written because
  the shared main checkout being used as a build surface by more than one campaign at once is a
  repeatedly-observed risk class this session's own governance ledgers document directly: a prior
  session's shell drifted into the shared checkout mid-campaign (the incident brief §4 of the
  SAMĀPTI implementation cites); this very campaign found its own governance ledgers sitting
  uncommitted in the shared checkout, on the wrong branch, for hours before catching it; and the
  worktree census taken during this campaign's own close found 79 worktrees, most stale, with at
  least one containing dead-end work on no branch that a plain `git worktree prune` would not have
  surfaced.
related: 00_ARCHITECTURE/MIGRATION_AND_MERGE_PROTOCOL_v1_0.md §4 (the merge-lock quiescence check
  already requires enumerating `git worktree list` — this document is the standing policy that
  check exists to enforce, not a replacement for it)
---

# Worktree isolation — the standing rule

## §1 — The rule

**The shared main checkout (`/Users/Dev/Vibe-Coding/Apps/Madhav`, whatever branch it happens to be
on) is never a build surface.** No campaign, lane, or session writes application code, runs a
build, or makes a commit intended to become a PR directly in the shared checkout. Every unit of
work — a builder lane, a verification pass, an integrator's rebase-and-merge, a rebuild dispatch —
happens in its own dedicated `git worktree`, cut fresh from `origin/main` (or from the specific
branch it continues), and is cleaned up when the work concludes.

**Why this is the rule, not merely a preference:** the shared checkout is the one surface every
concurrent campaign and every resumed session can see and touch. A worktree is provably isolated —
its own directory, its own index, its own uncommitted-changes surface — and its lifecycle (create →
work → commit → push → clean up) leaves nothing behind for the next session to trip over. The
alternative already produced two real incidents this campaign documented (governance ledgers
uncommitted in the shared checkout on the wrong branch; a separate prior incident that motivated
the merge-lock's own worktree-enumeration check) — the failure mode is not hypothetical.

## §2 — What this means in practice

- **Starting new work:** `git worktree add -b <branch> <path> origin/main` (or the branch being
  continued), never `git checkout -b <branch>` inside the shared checkout.
- **The shared checkout stays on whatever branch a human or a prior session left it on.** Do not
  switch its branch, do not commit to it, do not run a build against it. Reading files from it
  (for investigation, diffing, orientation) is fine — writing to it is not.
- **Governance/tracking artifacts that must be committed** (campaign ledgers, close reports,
  session logs) are exactly as much at risk sitting uncommitted in the shared checkout as any code
  change — commit them via the same worktree-and-PR path, not as a direct edit to the shared
  checkout's working tree, even when the edit feels "just documentation."
- **Cleanup is part of the work, not an afterthought.** A worktree whose branch has merged (or been
  abandoned/superseded) should be removed (`git worktree remove <path>`) as part of closing that
  unit of work, not left for a later hygiene pass to discover. `git worktree prune` alone is
  insufficient — it only reaps worktrees whose *directory* is already gone; a worktree whose
  directory still exists but whose work is done needs an explicit `remove`.

## §3 — Cross-campaign concurrency

When more than one campaign is active in this repository at once (the normal case, not an edge
case — this campaign ran concurrently with ṢAḌ-DARŚANA for its entire duration), each campaign's
worktrees are its own. Per the ownership rules already established (`SAMAPTI_CONDUCTOR_PROMPT_v1_0.md`
§7), never modify, merge, rebase, or remove a worktree belonging to another active campaign's
lane — even a worktree that looks stale, unless its owning campaign's PR is independently confirmed
merged/closed via `gh pr view`. When genuinely uncertain whether a worktree is safe to touch, leave
it and report it rather than guess (this document's own INF-4/5 audit pass, conducted 2026-07-30/31,
found and correctly left alone several worktrees carrying uncommitted, unattributed changes to
`CONDUCTOR_HALT_LOG.md` files rather than force-removing them).

## §4 — Retirement of the shared checkout as a build surface (this session's own compliance)

This protocol is being landed retroactively, describing a discipline this campaign's own session
already followed for its build/fix/verification work — every builder, VER, and reopen dispatch in
this run worked in its own isolated worktree (`git worktree add`, isolated commit, push, PR), never
committing application code directly to the shared checkout. The one standing exception was this
campaign's own governance ledgers (which, per §2 above, should not have been an exception — they
were found uncommitted in the shared checkout mid-run and had to be recovered via the same
worktree-and-PR path this document now makes the explicit, standing rule for everything, ledgers
included).

## §5 — Stale-worktree hygiene baseline (INF-4/5, as of this protocol's authoring)

A worktree census taken 2026-07-30/31 found **79 worktrees** across this repository. Disposition:
**31 removed** (1 genuinely dangling/prunable; 30 confirmed safe — clean working tree, owning PR
independently verified MERGED via `gh pr view` before removal, never forced against uncommitted
work); **49 left alone** (active work with open PRs, another campaign's active worktrees, or
worktrees carrying uncommitted changes flagged for manual review rather than force-discarded). No
branch was deleted in this pass — only checkout directories; every ref this campaign encountered
survives. `satyadipa/orchestrator-lit-predicate` (a redundant branch this campaign was asked to
confirm/delete) was independently re-verified absent (local and remote) both before and after the
pruning pass — nothing to delete, the branch does not exist.

---

*End of WORKTREE_ISOLATION_PROTOCOL v1.0 (2026-07-31, SAMĀPTI conductor session, landed as part of
the protective set per DVA Ruling 83).*
