---
artifact: CROSS_CAMPAIGN_COLLISION_FORENSICS_AND_REPAIR_v1_0
canonical_id: PARIPRASHNA_PARISESA_COLLISION_INCIDENT
version: 1.0
status: INCIDENT REPORT + REPAIR RUNBOOK — read-only forensics complete 2026-08-19 08:52 UTC;
  repair requires a NATIVE-SIDE session (the Cowork bridge cannot delete files and cannot
  reach /private/tmp worktrees)
date: 2026-08-19
authoritative_side: claude
role: >
  Forensic diagnosis of the PARIPRAŚNA ↔ PARIŚEṢA-RĀTRI-V4 collision, the repair runbook,
  and the binding protocol amendment that prevents recurrence. Amends
  PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md §DD-10 (which was WRONG).
---

# Cross-Campaign Collision — Forensics, Repair, Prevention

## §1 — Verdict in one paragraph

**Paripraśna merged to `main` without holding a cross-campaign lease, and the
merge rewrote five shared governance registries that all ~21 open Pariśeṣa lanes
must also write.** The repo already has a native-directed protocol for exactly
this (`CAMPAIGN_COORDINATION.md`, created 2026-08-10, binding on all concurrent
autonomous campaigns) which names "main merges/deploys" as the first of five
surfaces worktrees cannot isolate. Paripraśna never took the lease — **because
the brief I wrote told it to look in the wrong place and to defer if the file
looked dirty.** Worktree isolation worked correctly; the collision was never
about files-in-a-directory. It was about the four surfaces that are global by
nature: `main`, the shared governance registries, the shared `.git`, and the
root instruction slot. No code was corrupted in either direction.

## §2 — Evidence (all read-only, 2026-08-19 08:51–08:53 UTC)

| # | Fact | Evidence |
|---|---|---|
| E1 | Worktree isolation was OBEYED by both campaigns | `git worktree list`: `pariprashna/g0-close` → `/private/tmp/pariprashna-g0-close`; `pariprashna/p0-ignition` → `/private/tmp/pariprashna-p0-ignition`; Pariśeṣa in `/Users/Dev/par-night/**` and `.claude/worktrees/par-*` |
| E2 | **`origin/main` = `3fd40b61b`** — the Paripraśna G0 squash (PR #1341) | `git rev-parse`; `merge-base --is-ancestor` = YES |
| E3 | That commit rewrote **5 shared governance registries**: `CURRENT_STATE_v1_0.md` (+20/−), `SESSION_LOG.md` (+107), `CAPABILITY_MANIFEST.json` (62), `FILE_REGISTRY_v1_14.md` (+9), `NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` (+45) | `git show --stat 3fd40b61b` (18 files, 2,648 insertions) |
| E4 | **Local `main` = `7459f8837`** — behind origin/main | refs read |
| E5 | **21 Pariśeṣa lane worktrees are pinned at exactly `7459f8837`** (par-s1-f17/f38/f67/f73, par-s2-f14, par-s3-f34/f35/f47-f48/f68/f69/f134, par-s4-f135, par-s5-f03/f10/f12/f33/f36/f37/f45/f117, par-s6-f78) | worktree list |
| E6 | Every Pariśeṣa lane must append to `SESSION_LOG` + bump `CURRENT_STATE` at close — the same files E3 rewrote | campaign close protocol (GIP §G) |
| E7 | `CAMPAIGN_COORDINATION.md` is Pariśeṣa's **live lease kernel** — its entire recent history is `coord(parisesa): generic lease renewal` / `takeover pending` | `git log -- CAMPAIGN_COORDINATION.md` |
| E8 | **The protocol says the live lease lives on branch `campaign-coordination`, NOT main** ("main carries a mirror that is SLOW BY CONSTRUCTION… useless for a real-time lease"), and says operate it from "**your own worktree — never the main checkout**" | the file's own §0, verbatim |
| E9 | The shared main checkout has that file in `MM` state: **996 lines staged, then reverted in the worktree** — the main checkout was used as a lease scratchpad, which §0 forbids | `git diff --cached --stat` vs `git diff --stat` |
| E10 | **No code contamination either way.** Paripraśna commits are docs-only; no Paripraśna doc appears in any `par/*` or `ekv/*` commit | `git show --stat` on all G0 commits; `git log --all -- <pariprashna paths>` |
| E11 | Shared-checkout pollution, uncommitted: `CLAUDECODE_BRIEF.md` (M), `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` (M), untracked `briefs/pariprashna_swarm/` (4 files) and `briefs/pariprashna_v012/` | file listing + diff |
| E12 | A **0-byte `.git/index.lock`** exists (created 08:51:16) and cannot be removed via the bridge; index-writing git ops in the main checkout now fail (my own follow-up query died with exit 128) | `ls .git/index.lock`; `warning: unable to unlink … Operation not permitted` |
| E13 | Cross-worktree **stash theft has already happened once** in this repo (documented in the stash itself) | `stash@{1}`: "RESTORED: unrelated G14b AHEAD auto-file changes accidentally popped by another worktree's shared stash list … do not drop" |
| E14 | `AGENTS.md` (Codex instruction surface) is dirty with `## Imported Claude Cowork project instructions` — **pre-existing, from the Codex onboarding (CCD-001), not Paripraśna** | `git diff AGENTS.md` (2 lines) |

## §3 — The five collision mechanisms, ranked

**M1 — Governance-registry contention on `main` (PRIMARY, confirmed).** E2+E3+E5+E6.
Paripraśna's squash rewrote CURRENT_STATE, SESSION_LOG, CAPABILITY_MANIFEST,
FILE_REGISTRY and NATIVE_DIRECTIVES. Twenty-one Pariśeṣa lanes branched from the
older main must each touch SESSION_LOG/CURRENT_STATE at close. Consequences,
all of which match "it started impacting us": every open Pariśeṣa PR becomes
out-of-date-with-base → forced rebases → CI re-runs → merge-queue stall;
CURRENT_STATE **version-number collision** (Pariśeṣa writing v6.60→v6.61 while
v6.62 already exists); FILE_REGISTRY / CAPABILITY_MANIFEST are single-source
registries where concurrent registration conflicts by construction.

**M2 — Lease never acquired (ROOT CAUSE, confirmed).** E7+E8+E9. The protocol
requires re-reading the lease from `origin/campaign-coordination` immediately
before any gate merge or deploy. My G0 brief instead said: *register in
CAMPAIGN_COORDINATION.md only if its dirty state has been resolved — otherwise
log the deferral.* Two errors in one sentence: it pointed at the slow `main`
mirror / dirty working copy instead of the `campaign-coordination` branch, and
it made a **blocking precondition optional**. G0 dutifully deferred, then
merged — the exact sequence the protocol exists to prevent.

**M3 — Root instruction-slot contamination (confirmed, high blast radius).** E11.
`CLAUDECODE_BRIEF.md` at the repo root is a **single-slot dispatcher**, and per
CLAUDE.md §C item 0 every Claude session reads it first and its
`may_touch`/`must_not_touch` **override all other scope guidance**. I overwrote
it in the shared checkout with "you are the G0 close session, docs only". Any
Claude Code session or subagent opening in that checkout — including one working
for Pariśeṣa — is silently re-scoped into the wrong campaign. It does not error;
it redirects. (Codex reads `AGENTS.md`, so Codex itself was insulated — but
Claude-side helpers of the Pariśeṣa work were not.) The file's own
`stale_pointer_incident` field documents this exact failure mode happening
three times before.

**M4 — Shared `.git` contention (confirmed, currently blocking).** E12+E13. One
object store, one refs namespace, one stash list, one main-checkout index across
~200 worktrees and two campaigns. Right now a stale `index.lock` blocks
index-writing git operations in the main checkout. Stash theft is a proven
prior occurrence in this very repo.

**M5 — Shared deploy / DB / migration numbering (not yet fired; next in line).**
The protocol's other four surfaces. P0-IGNITION has not committed yet (its
branch sits exactly at `3fd40b61b`), so no Paripraśna deploy has raced a
Pariśeṣa deploy. It would have, within hours, under my v1.1 plan.

## §4 — Honest attribution

**Paripraśna's G0 session executed correctly.** It used a worktree, stayed
docs-only, and obeyed the (wrong) instruction it was given about the lease.

**The faults are mine, and they are design faults, not execution faults:**

1. **The G0 brief's lease instruction was backwards** (M2) — the single root cause.
2. **I wrote Paripraśna files into the shared main checkout** via the Cowork
   device bridge across several turns, including the root instruction slot (M3),
   violating the protocol's "never the main checkout" rule.
3. **My swarm plan v1.1 carried the same wrong lease model forward** (DD-10:
   "register the lease the moment the file is clean") and would have repeated
   the failure across five phases with far more main merges and live deploys.
4. **My read-only `git status` created the un-removable `index.lock`** (M4/E12) —
   an active breakage introduced by the investigation itself.

## §5 — REPAIR RUNBOOK (native-side; the bridge cannot do these)

Run in a terminal or a Claude Code session **on the Mac**, at the repo root.
Steps 1–3 are safe with campaigns live; step 4 needs the p0 worktree; step 5
is the lease.

```bash
# ── 1. Clear the stale index lock (the bridge cannot delete files)
cd /Users/Dev/Vibe-Coding/Apps/Madhav
ls -la .git/index.lock && rm -f .git/index.lock

# ── 2. Preserve the 4 swarm docs that exist ONLY in the polluted checkout
#      (they are NOT on main; the v012 set already is, via #1341)
mkdir -p ~/pariprashna-swarm-rescue
cp 00_ARCHITECTURE/briefs/pariprashna_swarm/*.md ~/pariprashna-swarm-rescue/
ls -1 ~/pariprashna-swarm-rescue/   # expect 4 files

# ── 3. De-pollute the shared checkout — restore Pariśeṣa's world
#      3a. the root instruction slot (THE important one)
git checkout -- CLAUDECODE_BRIEF.md
#      3b. the TA edit (its content is already on main via #1341)
git checkout -- 00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md
#      3c. the lease scratchpad staged in the shared index — unstage, keep worktree
git restore --staged 00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md
#      3d. remove the untracked Paripraśna trees from the shared checkout
rm -rf 00_ARCHITECTURE/briefs/pariprashna_swarm
#      (leave briefs/pariprashna_v012 — it is tracked on main and will reappear
#       correctly on the next pull; if untracked here, rm -rf it too)
git status --porcelain | head        # expect: only AGENTS.md + CAMPAIGN_COORDINATION (M)

# ── 4. Re-home the swarm docs on the Paripraśna branch, in its own worktree
cd /private/tmp/pariprashna-p0-ignition   # (recreate if pruned:
   # git worktree add /private/tmp/pariprashna-p0-ignition pariprashna/p0-ignition )
mkdir -p 00_ARCHITECTURE/briefs/pariprashna_swarm
cp ~/pariprashna-swarm-rescue/*.md 00_ARCHITECTURE/briefs/pariprashna_swarm/
git add 00_ARCHITECTURE/briefs/pariprashna_swarm
git commit -m "docs(pariprashna/p0): swarm plan set — roadmap, phased plan, v1.1 amendments, kickoff"

# ── 5. ACQUIRE THE LEASE (do this BEFORE any further Paripraśna main merge)
git fetch origin campaign-coordination
git show origin/campaign-coordination:00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md | tail -60
#   → append the §6 row in §6 below, on a checkout of campaign-coordination,
#     then: git push origin campaign-coordination
```

**Also required, native-side: bring local `main` current** (`git fetch origin && git
checkout main && git merge --ff-only origin/main`) so Pariśeṣa's next lanes are
cut from a main that already contains #1341 — one rebase now, instead of 21
surprise conflicts later.

## §6 — The lease row Paripraśna owes (append to `campaign-coordination`)

```markdown
### PARIPRAŚNA — campaign entry (2026-08-19, retroactive + forward)

- **Campaign:** PARIPRAŚNA implementation (chat-engine build, phases P0–P5).
  Branches `pariprashna/*`. Plan `00_ARCHITECTURE/briefs/pariprashna_swarm/`.
- **RETROACTIVE DISCLOSURE:** PR #1341 (`3fd40b61b`, G0 close) merged to main
  2026-08-19 **without a lease**, rewriting CURRENT_STATE (→v6.62), SESSION_LOG,
  CAPABILITY_MANIFEST, FILE_REGISTRY and NATIVE_DIRECTIVES (ND.2). Cause: a
  defective instruction in the G0 brief, not a protocol rejection. Campaigns
  branched from main < `3fd40b61b` must rebase; CURRENT_STATE is at v6.62 — do
  not re-use v6.60/v6.61.
- **Territory claimed:** `platform/src/{app/api/pariprashna,app/clients/[id]/{pariprashna,samiksha},components/pariprashna,lib/pariprashna}/**`,
  `00_ARCHITECTURE/PARIPRASHNA_*`, `00_ARCHITECTURE/briefs/pariprashna_*`.
- **Shared surfaces — Paripraśna's commitments:** (1) no main merge or production
  deploy without re-reading this file from `origin/campaign-coordination`
  immediately prior; (2) governance-registry writes batched to ONE serialized
  step per phase close, under an explicit lease row, never mid-phase;
  (3) migration numbers reserved here before authoring; (4) deploys announced
  here with the Cloud Run revision tag; (5) never the main checkout — worktrees
  only; (6) never `git stash` in a shared-`.git` worktree.
- **Lease requested:** governance-write + main-merge window at each Paripraśna
  phase close, ~30 min, announced ≥1 entry in advance.
```

## §7 — BINDING PROTOCOL AMENDMENT (supersedes v1.1 DD-10)

`PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md` DD-10 is **struck and
replaced**. New binding rules for every phase P0–P5:

| # | Rule |
|---|---|
| **X-1** | **Lease-before-merge is a BLOCKING precondition, never deferrable.** Read `origin/campaign-coordination` (the branch — never main's mirror, never the working copy) at phase open, at every train close, and immediately before every main merge and every deploy. No lease → no merge. Halt and report instead. |
| **X-2** | **Governance registries are close-only, batched, serialized.** CURRENT_STATE, SESSION_LOG, FILE_REGISTRY, CAPABILITY_MANIFEST, NATIVE_DIRECTIVES are never written mid-phase. Each phase accumulates its deltas in `briefs/pariprashna_swarm/state/GOVERNANCE_DELTA_pN.md` and applies them in ONE step at phase close, holding an announced lease window. CURRENT_STATE version numbers are read live at that moment, never predicted. |
| **X-3** | **The root instruction slot is forbidden to Paripraśna while another campaign is live.** `CLAUDECODE_BRIEF.md` is single-slot and override-powered; Paripraśna carries its brief path in the dispatch prompt instead (the kickoff prompt already does). Never write that file. |
| **X-4** | **Never operate in the main checkout** — not for git, not for lease reads, not for file writes. Worktrees only. This binds the Cowork bridge too: **Cowork delivers files via chat for a native session to commit on a branch; it does not `device_commit_files` into the shared checkout.** |
| **X-5** | **`git stash` is banned** in any worktree sharing this `.git` (the stash list is global; theft is a proven prior incident). Use a WIP commit on the lane branch. |
| **X-6** | **Deploy and DB are leased, not assumed.** Announce the Cloud Run revision tag in the coordination file before shifting traffic; DB-integration suites use per-lane template clones; migration numbers reserved in the coordination file before authoring. |
| **X-7** | **Fetch-and-rebase before cutting any lane.** Local main is not a source of truth; `origin/main` is. |

**Recurrence test:** a phase that cannot show a lease row timestamped before its
main merge has failed its gate, regardless of how green its code is.

*End CROSS_CAMPAIGN_COLLISION_FORENSICS_AND_REPAIR v1.0.*
