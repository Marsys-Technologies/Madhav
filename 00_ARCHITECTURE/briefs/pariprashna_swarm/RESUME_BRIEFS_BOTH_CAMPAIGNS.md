---
artifact: RESUME_BRIEFS_BOTH_CAMPAIGNS
version: 1.0
status: READY — paste §A into the Codex/Pariśeṣa session, §B into the Paripraśna session,
  AFTER the native steps in §C are done
date: 2026-08-19
---

# Resume briefs — Pariśeṣa (Codex) and Paripraśna (Claude Code)

## §A — PASTE INTO THE CODEX / PARIŚEṢA-RĀTRI-V4 SESSION

> **Resume notice — cross-campaign incident, resolved. Read before resuming work.**
>
> While you were running, a second autonomous campaign (PARIPRAŚNA, chat-engine
> build, `pariprashna/*` branches) merged **PR #1341 to `main`** without holding a
> cross-campaign lease. That was a defect in Paripraśna's own brief, not a claim
> against your territory, and it has been diagnosed and repaired. Nothing of yours
> was rewritten, deleted, or cleaned up.
>
> **What changed under you — the only thing that matters for your resume:**
> `origin/main` moved from `7459f8837` to **`3fd40b61b`**. That commit is
> **docs-only** (18 files, 2,648 insertions, zero code) but it touched five shared
> governance registries:
> - `CURRENT_STATE_v1_0.md` → **now at v6.62**. Do NOT reuse v6.60 or v6.61; read
>   the live version number at your close, don't predict it.
> - `SESSION_LOG.md` → +107 lines appended (a Paripraśna G0 entry).
> - `CAPABILITY_MANIFEST.json`, `FILE_REGISTRY_v1_14.md` → four new canonical
>   artifacts registered (`PARIPRASHNA_ARCHITECTURE` + 3 companions).
> - `NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` → **ND.2 added** (native-self
>   interstitial for sensitive readings; Paripraśna-scoped, no effect on you).
>
> **Consequence for your lanes:** your ~21 lane worktrees are branched from
> `7459f8837` and your local `main` is at `2e56ba9d1`. Fetch and rebase before
> your next merge, or your PRs will report out-of-date-with-base and your merge
> queue will stall on those five files. The rebases should be trivial — your lanes
> touch code, #1341 touched docs — **except** where your close protocol appends to
> `SESSION_LOG` / bumps `CURRENT_STATE`, which is where the real conflicts live.
> Suggested: rebase, take both sides on SESSION_LOG (append-only file), re-read
> CURRENT_STATE's live version before writing.
>
> **What was NOT touched, explicitly:** no `platform/**` code, no migration, no
> deploy, no DB, no credential, no branch or worktree of yours, and — per
> `CAMPAIGN_COORDINATION.md`'s write_rule — **not your `CAMPAIGN_COORDINATION.md`
> entries.** One anomaly is flagged for you rather than fixed: that file sits in
> `MM` state in the **main checkout** (996 lines staged, then reverted in the
> worktree). It is not Paripraśna's; if it is a Pariśeṣa lease scratchpad, note
> that §0 of that file forbids operating the lease from the main checkout — please
> re-do it from your own worktree and unstage the main checkout's copy.
>
> **Also cleaned up (Paripraśna's own mess, in the shared main checkout only):** a
> Cowork session had written Paripraśna documents into the **shared main checkout**
> while it sat on your `ekv/b-01-dignity-oracle-fix` branch — including the root
> `CLAUDECODE_BRIEF.md`, which per CLAUDE.md §C item 0 every Claude session reads
> first and whose scope declarations override all others. Any Claude-side helper
> that opened in that checkout would have been silently re-scoped into
> Paripraśna's G0 task. **All of it has been reverted byte-exact**;
> `CLAUDECODE_BRIEF.md` is back to `CLAUDECODE_BRIEF_PURNATA` / `status: COMPLETE`
> (i.e. §C item 0 says skip and proceed normally). Paripraśna's footprint in the
> shared checkout is now zero.
>
> **One item you may need to clear:** a stale `.git/index.lock` (0 bytes, created
> 08:51:16 UTC by a read-only Cowork `git status` that could not unlink it) blocks
> index-writing git operations **in the main checkout only** — your worktrees have
> their own indexes and are unaffected. If it is still present:
> `rm -f .git/index.lock`.
>
> **Going forward, Paripraśna has committed to these rules** (binding on its every
> phase, and it now owes you a lease row on `campaign-coordination`): lease-before-
> merge as a non-deferrable blocker read from `origin/campaign-coordination`;
> governance registries written **only at phase close, batched, under an announced
> lease window**; never the main checkout; no `git stash` in a shared-`.git`
> worktree; deploys and migration numbers announced in the coordination file
> before use. If you observe Paripraśna violating any of these, log it in §6 of
> `CAMPAIGN_COORDINATION.md` and it will be treated as a gate failure on their side.
>
> Resume when ready. Your work is intact.

## §B — PASTE INTO THE PARIPRAŚNA (Claude Code) SESSION

> **Resume notice — you are HALTED pending a lease. Do not merge or deploy.**
>
> Your G0 close succeeded and is on `origin/main` (`3fd40b61b`);
> `PARIPRASHNA_ARCHITECTURE_v1_0.md` is `status: CURRENT`. But it merged **without
> a cross-campaign lease**, which broke a concurrent campaign (PARIŚEṢA-RĀTRI-V4,
> ~21 open lanes) by moving five shared governance registries under it. Root cause:
> a defective instruction in your own G0 brief. It is fixed; you must now operate
> under the amended protocol.
>
> **Before you do anything else, read:**
> `00_ARCHITECTURE/briefs/pariprashna_swarm/CROSS_CAMPAIGN_COLLISION_FORENSICS_AND_REPAIR_v1_0.md`
> §7 — the seven binding rules X-1..X-7. They **supersede DD-10** in
> `PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md`.
>
> **Your first three acts, in order:**
> 1. **Acquire the lease.** From your own worktree (never the main checkout):
>    `git fetch origin campaign-coordination`, read
>    `origin/campaign-coordination:00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md`,
>    then append the lease row drafted in §6 of the forensics document — including
>    its **retroactive disclosure** of the un-leased #1341 merge — and push to
>    `campaign-coordination`. No further main merge or deploy until that row is
>    live.
> 2. **Re-home the swarm plan set.** The four swarm documents
>    (roadmap · phased plan · v1.1 amendments · kickoff prompt) plus this forensics
>    document exist only in a quarantine directory
>    (`_cowork_tmp/quarantine/pariprashna_swarm/` in the main checkout — copy, do
>    not git-add from there). Commit them to
>    `00_ARCHITECTURE/briefs/pariprashna_swarm/` **on your own branch, from your
>    own worktree.**
> 3. **Then, and only then, resume P0 IGNITION** — with X-2 in force: no
>    governance-registry write mid-phase; accumulate deltas in
>    `state/GOVERNANCE_DELTA_p0.md` and apply them in one leased step at phase
>    close.
>
> Everything else in the P0 plan stands unchanged: the ports refactor of
> `route.ts` is still the first substantive lane and still gates the rest.

## §C — NATIVE STEPS (a terminal or Claude Code session on the Mac)

Already done by Cowork (verified byte-exact, both campaigns paused): the shared
main checkout has **zero Paripraśna footprint** — `CLAUDECODE_BRIEF.md` and
`PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` restored to their `ekv` blobs
(hash-verified), and every stray Paripraśna file moved to
`_cowork_tmp/quarantine/`. Nothing belonging to another campaign was touched.

Remaining, because the bridge cannot delete files and has no network:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# 1. Clear the stale lock (0 bytes, 08:51:16 UTC, created by a Cowork read)
rm -f .git/index.lock

# 2. Bring local main current so future lanes branch from the right base
git fetch origin
git checkout main && git merge --ff-only origin/main   # 2e56ba9d1 → 3fd40b61b
git checkout ekv/b-01-dignity-oracle-fix               # return the shared checkout

# 3. Recover the quarantined Paripraśna docs (do this from the p0 worktree)
#    They are at _cowork_tmp/quarantine/ :
#      pariprashna_swarm/   (4 files — NOT on main, must be committed)
#      pariprashna_v012/    (identical to main — discardable)
#      arch_v1_0/           (superseded by main's versions — discardable)
#    See §B step 2 for where they belong.

# 4. (Optional, Pariśeṣa's call) the MM lease scratchpad in the main checkout:
#    git restore --staged 00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md
#    Left untouched by Cowork per the file's own write_rule.
```

**Resume order:** native steps → Codex/Pariśeṣa (§A) → Paripraśna (§B) only after
its lease row is live on `campaign-coordination`.

*End RESUME_BRIEFS_BOTH_CAMPAIGNS v1.0.*
