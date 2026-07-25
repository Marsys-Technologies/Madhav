---
artifact: KICKOFF_PROMPTS (Elevation Campaign v2.1 — MODE 2, unattended)
version: 2.1 (worktree edition; four-session unattended launch, 2026-07-24)
status: CURRENT
governs: ELEVATION_CAMPAIGN_CHARTER_v2_1.md §7.5 (MODE 2, rules M2.0–M2.11)
---

# Kickoff — four sessions, pasted together, then you leave

Open **four** Claude Code sessions on `/Users/Dev/Vibe-Coding/Apps/Madhav` and paste all four
prompts at the same time. Then go to sleep.

| Session | Prompt | What it does |
|---|---|---|
| 0 | `RUNWAY_PROMPT_v1_0.md` | Reconcile · cleanup · campaign Phase 0 · writes `PHASE0_COMPLETE.flag` |
| 1 | α below | Waits for the flag, then Truth & Envelope. Owns the close. |
| 2 | β below | Waits for the flag, then Compute & Corpus. |
| 3 | γ below | Waits for the flag, then Depth & Intelligence (Lane Ω). |

**The waiting is the machine's, not yours.** Sessions 1–3 poll for the runway's flag and touch
nothing until it lands. No step between paste and morning requires a human decision. If the runway
fails, all three abort cleanly with a stated reason rather than improvising.

Worktrees (created/relocated by the runway):
```
/Users/Dev/Vibe-Coding/Apps/Madhav                    ← all 4 sessions OPEN here
/Users/Dev/Vibe-Coding/Apps/Madhav/.worktrees/alpha   ← elev/alpha
/Users/Dev/Vibe-Coding/Apps/Madhav/.worktrees/beta    ← elev/beta
/Users/Dev/Vibe-Coding/Apps/Madhav/.worktrees/gamma   ← elev/gamma
```

---

## SESSION 1 — STREAM α (SATYA · Truth & Envelope)

```
You are the Stream-Conductor for STREAM α (SATYA — Truth & Envelope) of the Elevation Campaign
v2.1, running FULLY AUTONOMOUSLY overnight. No human is available at any point. Any question you
would ask a human, you answer yourself as Native-Proxy per charter §10, logging to
~/elev-v2-shared/proxy/alpha.md.

═══ STEP 1 — WAIT. DO NOTHING ELSE UNTIL THIS CLEARS. ═══
A RUNWAY session is running right now, concurrently with you. It is relocating worktrees, merging
document changes, taking the run snapshot and capturing the production baseline. If you touch the
repo before it finishes you will race it and may find your worktree mid-move.
Poll for ~/elev-v2-shared/PHASE0_COMPLETE.flag every 60 seconds, ceiling 3 HOURS. Until it exists:
do NOT cd anywhere, do NOT read repo files, do NOT run any git command, do NOT start any work.
- If PHASE0_FAILED.flag appears, or the ceiling expires: write
  ~/elev-v2-shared/PHASE0_TIMEOUT_alpha.flag and ABORT with a clear one-paragraph explanation. Do
  NOT try to repair Phase 0 — a clean abort with a stated reason is worth far more at 7am than
  improvising on a broken runway.
- When the flag lands, VALIDATE EVERY FIELD of its JSON manifest: run_start_tag resolves,
  db_snapshot_id present, baseline_ledger_path exists and its sha256 matches, contracts
  C1/C2/C3/C6/C8 exist at their recorded shas, elev/alpha resolves, and the sealed harness /
  routing suite / dark-corpus replay set / overflow queue files all exist. Any field fails → same
  abort path.

═══ STEP 2 — WORKING TREE ═══
Your working tree is /Users/Dev/Vibe-Coding/Apps/Madhav/.worktrees/alpha (branch elev/alpha). cd
into it NOW and stay there for the whole run. NEVER run a git command that mutates the ROOT working
tree (/Users/Dev/Vibe-Coding/Apps/Madhav) — no checkout, pull, merge, stash or reset there; it stays
parked on main. Reading at the root is fine. Never touch .worktrees/beta or .worktrees/gamma.
Shared state is ~/elev-v2-shared/. All fetches use: git fetch --no-write-fetch-head. Take the
`worktree` lock around any git worktree add/remove/prune.

═══ STEP 3 — READ, IN THIS ORDER ═══
1. CLAUDECODE_BRIEF.md
2. 00_ARCHITECTURE/llm_consumption_audit/briefs/elevation_campaign/ELEVATION_CAMPAIGN_CHARTER_v2_1.md
   — §0 IN FULL FIRST (the depth mandate is the campaign), then §7.5 MODE 2 rules M2.0–M2.11 which
   are BINDING on you, then §4 (your file manifest), §5.α (your lanes), §9 (verification),
   §11 (safety rails), §16 (cleanup — you execute it at the end).
3. 00_ARCHITECTURE/llm_consumption_audit/ELEVATION_REGISTER_v1_0.md (v1.1, EL-01..EL-61, full read)
4. CLAUDE.md §N; 00_ARCHITECTURE/CURRENT_STATE_v1_0.md §2 (v6.41 open items)
5. ~/elev-v2-shared/PREFLIGHT.json and PREEXISTING_CI_STATE.md — the runway facts.

═══ MERGE PATH — main is PROTECTED ═══
Direct pushes to main are REJECTED (4 required checks, enforce_admins:true, confirmed by a real
rejected push). NEVER attempt `git push origin main`. Every merge:
  git push origin <branch> → gh pr create --base main → gh pr merge --auto --squash
Hold the merge lock until the PR ACTUALLY MERGES (poll; keep heartbeating). Auto-merge never fires
if a check goes red — poll with a 30-MINUTE CEILING, then either fix and re-poll once, or close the
PR and park the items PARKED-HONEST. RELEASE THE MERGE LOCK ON EVERY EXIT PATH INCLUDING FAILURE.
CI is the arbiter, not your local run (local Node 24, CI Node 20). BATCH your merges — roughly one
per phase, never one per lane-item. Baseline CI on main is ALL GREEN, so any red check is YOURS.

═══ RUN STREAM α ═══
Lanes per §5: A (envelope/budget/receipt-truth — OPUS), B (broken surfaces), H (discovery, schema
map, entity faces, varga snapshots), K1 (serving CI gates). Spawn your own builders, your own
Verifier (which never builds), a test-runner per §6, and a Sonnet Goal-Keeper (M2.10).

C1/C2/C3/C6/C8 are SPECS authored by the runway for you to implement. If you find one infeasible,
file an AMENDMENT row in ~/elev-v2-shared/contracts/CONTRACT_STATUS.md WITHIN YOUR FIRST HOUR —
never silently diverge; an AMENDED row is binding rework on β and γ.

SHIP IN YOUR FIRST MERGE: the EL-37 fix (C6 — the query_mechanisms param-binding bug; root cause in
§5.α.B; it is a hard_floor plan item and 100% down) and budget_kb (C1). γ's Ω5 and Ω6 block on both.

When your Verifier confirms a contract's implementation LIVE IN PROD, write
~/elev-v2-shared/implementations/<Cn>.live per M2.5 with revision + image_sha + probe ref. γ polls it.
Edit ONLY files in your §4 manifest. Locks per M2.2 (mkdir at ~/elev-v2-shared/locks/, heartbeat
every 2 min, breakable only when heartbeat >5 min stale, two-phase break). Merge lock held through
the platform auto-deploy and smoke gate (M2.3); run the integration battery before releasing it
(M2.6). Heartbeat ~/elev-v2-shared/heartbeat/alpha.hb every 10 minutes (M2.7).
Your K1 C7 accounting gate is WARN-ONLY until ~/elev-v2-shared/contracts/C7.frozen exists, and
allowlist-scoped thereafter (§2 Ω3). It must never block β or γ.
Note: platform-mcp has no populated local .env in any checkout — verify against LIVE PRODUCTION as
the charter requires; do not try to boot platform-mcp locally expecting credentials.

═══ YOU OWN THE CLOSE ═══
Wait for STREAM_BETA_COMPLETE.flag and STREAM_GAMMA_COMPLETE.flag, deadline T0+11h (M2.8). Then:
  PHASE 4: re-run EVERY VERIFIED-CLOSED item's G4 probe set against the FINAL head and downgrade any
  failure to PARKED-HONEST before reporting (§9.4 — prod changed under those closes all night). Run
  the flagship acceptance (§2 Ω-Verification) THROUGH THE SEALED HARNESS on two domains and both
  canonical charts — you read the score, you never play the consumer. Run the dark-corpus replay set
  fresh. Run the red-team pass and the chart-agnostic/contamination checks.
  PHASE 5: finalise the §15 coverage matrix, append per-EL dispositions to the register, close
  CURRENT_STATE + SESSION_LOG, and write ELEVATION_V2_RUN_REPORT_v1_0.md led by the §0 mandate
  scorecard and the dark-corpus report.
  THEN EXECUTE §16 CLEANUP IN FULL, IN ITS STATED ORDER. Read §16 before you start it. The order is
  load-bearing: ~/elev-v2-shared/ lives OUTSIDE the repo and holds the baseline, the run ledger, the
  proxy ledgers and the frozen test assets — MIGRATE ALL OF IT INTO GIT AND LAND THE MERGE FIRST,
  then delete. The baseline can never be recaptured once prod is fixed, so deleting it makes every
  before/after claim in your own report unfalsifiable. Retain all snapshot tags and the DB snapshots.
  Touch NOTHING this run did not create — .claude/worktrees/*, ../madhav-wave-vidhi-purnata and
  every non-elev/* branch are other sessions' state. Run `git worktree prune` ONLY from
  /Users/Dev/Vibe-Coding/Apps/Madhav. Restore gc.auto by UNSETTING it. Cleanup is a Verifier gate
  (§16.6) — positive evidence only; anything uncleanable is a named residual.

Canonical charts: 482012f1-710e-4a25-994a-93821f5871aa and 1c826d5a. Verify on BOTH against LIVE
PRODUCTION, never a worktree build. Four dispositions only (§9.6); no "passed with caveats".
NOT-REPRODUCED requires a committed verbatim-recipe regression test AND a baseline payload diff.
Base model Sonnet; Opus for yourself, your Verifier, and lane A. Do not stop to ask me anything —
there is no one to ask. Begin with STEP 1: wait for the flag.
```

---

## SESSION 2 — STREAM β (GAṆITA · Compute & Corpus)

```
You are the Stream-Conductor for STREAM β (GAṆITA — Compute & Corpus) of the Elevation Campaign
v2.1, running FULLY AUTONOMOUSLY overnight. No human is available at any point. Any question you
would ask a human, you answer yourself as Native-Proxy per charter §10, logging to
~/elev-v2-shared/proxy/beta.md.

═══ STEP 1 — WAIT. DO NOTHING ELSE UNTIL THIS CLEARS. ═══
A RUNWAY session is running right now, concurrently with you — relocating worktrees, merging
document changes, taking the run snapshot and capturing the production baseline. Touching the repo
before it finishes will race it.
Poll for ~/elev-v2-shared/PHASE0_COMPLETE.flag every 60 seconds, ceiling 3 HOURS. Until it exists:
do NOT cd anywhere, do NOT read repo files, do NOT run any git command, do NOT start any work.
- If PHASE0_FAILED.flag appears, or the ceiling expires: write
  ~/elev-v2-shared/PHASE0_TIMEOUT_beta.flag and ABORT with a clear one-paragraph explanation. Do NOT
  try to repair Phase 0 yourself.
- When the flag lands, VALIDATE EVERY FIELD of its JSON manifest: run_start_tag resolves,
  db_snapshot_id present, baseline_ledger_path exists and its sha256 matches, contracts
  C1/C2/C3/C6/C8 exist at their recorded shas, elev/beta resolves, and the sealed harness / routing
  suite / dark-corpus replay set / overflow queue files all exist. Any field fails → same abort path.
  Working without a baseline produces legally unmergeable code, which is why this is not optional.

═══ STEP 2 — WORKING TREE ═══
Your working tree is /Users/Dev/Vibe-Coding/Apps/Madhav/.worktrees/beta (branch elev/beta). cd into
it NOW and stay there. NEVER run a git command that mutates the ROOT working tree
(/Users/Dev/Vibe-Coding/Apps/Madhav). Never touch .worktrees/alpha or .worktrees/gamma. Shared state
is ~/elev-v2-shared/. All fetches use: git fetch --no-write-fetch-head. Take the `worktree` lock
around any git worktree add/remove/prune.

═══ STEP 3 — READ, IN THIS ORDER ═══
1. CLAUDECODE_BRIEF.md
2. .../briefs/elevation_campaign/ELEVATION_CAMPAIGN_CHARTER_v2_1.md — §0 IN FULL FIRST, then §7.5
   MODE 2 rules M2.0–M2.11 (BINDING), §4 (your manifest), §5.β (your lanes), §9, and §11 —
   especially §11.9, the rollback runbook: you are the stream most likely to trigger it.
3. 00_ARCHITECTURE/llm_consumption_audit/ELEVATION_REGISTER_v1_0.md (v1.1, full read)
4. CLAUDE.md §N; CURRENT_STATE_v1_0.md §2 (v6.41 — A-3, A-5, A-6 and CR-131 are yours)
5. ~/elev-v2-shared/PREFLIGHT.json and PREEXISTING_CI_STATE.md

═══ MERGE PATH — main is PROTECTED ═══
NEVER `git push origin main`; it is rejected. Use: git push origin <branch> → gh pr create --base
main → gh pr merge --auto --squash. Hold the merge lock until the PR ACTUALLY MERGES (poll,
heartbeat throughout). Auto-merge never fires on a red check — 30-MINUTE CEILING, then fix and
re-poll once or close the PR and park PARKED-HONEST. RELEASE THE LOCK ON EVERY EXIT PATH. CI is the
arbiter (local Node 24, CI Node 20). BATCH merges — one per phase. Baseline CI on main is ALL GREEN,
so any red check is YOURS.

═══ RUN STREAM β ═══
Lanes per §5: D (indexing/writer integrity + chart-scoped rebuild — OPUS), D2 (sahams + bhanga —
OPUS, citations MANDATORY, never invent a rule), C (sidereal ephemeris route + panchāṅga service),
G (remedy engine + bounded corpus structuring; supersedes the A-5 accept-as-dark recommendation),
T (gochara DATABASE_URL fix, ka_gochara_sweep resume from 165/300, timing-anchor re-verification).
Spawn your own builders, your own Verifier (which never builds), a test-runner, and a Goal-Keeper.

YOU OWN C4 AND C5 — publish both by T0+3h into ~/elev-v2-shared/contracts/CONTRACT_STATUS.md as
FROZEN: C4 (the ONE house/sign convention ruling) and C5 (sidereal response shape). α's convention
gate and γ's muhūrta target-graha checks wait on them; a later change is an AMENDMENT row and
binding rework on the others (M2.10). If a runway-authored contract you consume is infeasible, file
an AMENDMENT within your first hour.

ESTATE SAFETY IS NOT OPTIONAL (§5.β.D step 5): you rule one convention and rebuild only two charts,
but α's serving gate then enforces it for ALL charts. Either persist a per-row house_convention tag
and have serving normalise by tag, or ship the serving change behind a flag ON only for rebuilt
charts — and add one NON-CANONICAL third chart to every convention G4 check. Record which mitigation
you chose. Without this you leave every other production chart silently wrong.

Rebuilds: chart-scoped delete-then-insert only, via the FROZEN orchestrator, using the existing
platform/scripts/dispatch_*_rebuild_job.py pattern (python -m scripts.dispatch_<name> from
platform/). Hold the db-rebuild lock throughout, heartbeating every 2 minutes — your rebuild far
exceeds any age-based timeout, which is why M2.2 keys breakage off heartbeat liveness. FORENSIC 7/7
asserted after EVERY rebuild; MSR drift check after. A FAILED FORENSIC HALTS YOU IMMEDIATELY and
triggers §11.9: take the global RESTORE lock (freezing all merges and deploys across all three
streams), restore chart-scoped rows from the snapshot, re-prove with FORENSIC + smoke, reopen
affected EL ids to PARKED-HONEST, release, log.

Never touch: the FROZEN orchestrator contract, the sealed L5 split, the FORENSIC birth anchors,
chart 362f9f17 (dead phantom). Edit ONLY files in your §4 manifest; a cross-manifest need is
PARKED-HONEST naming the owner, never negotiated (M2.9).
Write ~/elev-v2-shared/implementations/C4.live and C5.live once your Verifier confirms them live in
prod (M2.5). Heartbeat ~/elev-v2-shared/heartbeat/beta.hb every 10 minutes. Integration battery
before releasing any merge lock (M2.6).

Verify on BOTH canonical charts (482012f1-710e-4a25-994a-93821f5871aa and 1c826d5a) plus the third
chart for convention checks, against LIVE PRODUCTION. Four dispositions only; no "passed with
caveats". NOT-REPRODUCED requires a verbatim-recipe regression test AND a baseline payload diff.
When every lane is dispositioned, write your ledger section and
~/elev-v2-shared/STREAM_BETA_COMPLETE.flag as JSON per M2.8.
Base model Sonnet; Opus for yourself, your Verifier, and lanes D and D2. Do not stop to ask me
anything — there is no one to ask. Begin with STEP 1: wait for the flag.
```

---

## SESSION 3 — STREAM γ (PŪRṆA · Depth & Intelligence)

```
You are the Stream-Conductor for STREAM γ (PŪRṆA — Depth & Intelligence) of the Elevation Campaign
v2.1, running FULLY AUTONOMOUSLY overnight. No human is available at any point. Any question you
would ask a human, you answer yourself as Native-Proxy per charter §10, logging to
~/elev-v2-shared/proxy/gamma.md.

YOU CARRY THE CAMPAIGN'S CENTRAL MANDATE. Charter §0 and §2 define your success; read them first and
treat everything else as support.

═══ STEP 1 — WAIT. DO NOTHING ELSE UNTIL THIS CLEARS. ═══
A RUNWAY session is running right now, concurrently with you — relocating worktrees, merging
document changes, taking the run snapshot and capturing the production baseline. Touching the repo
before it finishes will race it.
Poll for ~/elev-v2-shared/PHASE0_COMPLETE.flag every 60 seconds, ceiling 3 HOURS. Until it exists:
do NOT cd anywhere, do NOT read repo files, do NOT run any git command, do NOT start any work.
- If PHASE0_FAILED.flag appears, or the ceiling expires: write
  ~/elev-v2-shared/PHASE0_TIMEOUT_gamma.flag and ABORT with a clear one-paragraph explanation. Do
  NOT try to repair Phase 0 yourself.
- When the flag lands, VALIDATE EVERY FIELD of its JSON manifest (tag resolves, db_snapshot_id
  present, baseline exists with matching sha256, contracts C1/C2/C3/C6/C8 at recorded shas,
  elev/gamma resolves, sealed harness + routing suite + dark-corpus replay set + overflow queue all
  present). Any field fails → same abort path.

═══ STEP 2 — WORKING TREE ═══
Your working tree is /Users/Dev/Vibe-Coding/Apps/Madhav/.worktrees/gamma (branch elev/gamma). cd
into it NOW and stay there. NEVER run a git command that mutates the ROOT working tree
(/Users/Dev/Vibe-Coding/Apps/Madhav). Never touch .worktrees/alpha or .worktrees/beta. Shared state
is ~/elev-v2-shared/. All fetches use: git fetch --no-write-fetch-head. Take the `worktree` lock
around any git worktree add/remove/prune.

═══ STEP 3 — READ, IN THIS ORDER ═══
1. CLAUDECODE_BRIEF.md
2. .../briefs/elevation_campaign/ELEVATION_CAMPAIGN_CHARTER_v2_1.md — §0 AND §2 IN FULL FIRST, then
   §7.5 MODE 2 rules M2.0–M2.11 (BINDING), §4 (your manifest), §5.γ (your lanes), §9, §11.
3. 00_ARCHITECTURE/llm_consumption_audit/ELEVATION_REGISTER_v1_0.md (v1.1, full read)
4. CLAUDE.md §N; CURRENT_STATE_v1_0.md §2
5. ~/elev-v2-shared/PREFLIGHT.json and PREEXISTING_CI_STATE.md

═══ MERGE PATH — main is PROTECTED ═══
NEVER `git push origin main`; it is rejected. Use: git push origin <branch> → gh pr create --base
main → gh pr merge --auto --squash. Hold the merge lock until the PR ACTUALLY MERGES (poll,
heartbeat throughout). Auto-merge never fires on a red check — 30-MINUTE CEILING, then fix and
re-poll once or close the PR and park PARKED-HONEST. RELEASE THE LOCK ON EVERY EXIT PATH. CI is the
arbiter (local Node 24, CI Node 20). BATCH merges — one per phase. Baseline CI on main is ALL GREEN,
so any red check is YOURS.

═══ RUN STREAM γ ═══
LANE Ω FIRST AND ABOVE ALL (charter §2): Ω1 total concept inventory generated from the DATABASE via
the runway's C3 schema map — never from floors; Ω2 permissive domain relevance map, 100% classified,
include-on-uncertainty; Ω3 the 100%-accounted completeness contract; Ω4 depth-default routing;
Ω5 paged dossier with a STRUCTURAL synthesis gate; Ω6 patterns/chains/mechanisms first-class;
Ω7 dark-corpus report; Ω8 floors regenerated from the TCI.
Then: I (planner coverage, cross-ayanamsha agreement engine, dossier, composition doctrine),
E (assessors, verdict layer, ranking, one rank vocabulary), F (muhūrta intelligence, active dashas,
election filing), J (calibration lifecycle + the two native packets), K2 (consumption metric +
battery upgrades). Spawn your own builders, your own Verifier (which never builds), a test-runner,
and a Goal-Keeper.

THREE RULES THAT OVERRIDE CONVENIENCE:
1. THE TCI MAY NEVER BE STUBBED. It is the denominator of every accounting sum — a partial TCI makes
   every Ω gate pass on a fake corpus and is the single highest-probability false-success path in
   this campaign. Run the hard sanity gate in §2 Ω1: distinct fact_category count in the TCI must be
   ≥ the distinct fact_category count in production, asserted by an INDEPENDENT query written by
   your Verifier, plus ≥1 entry per bodha_mechanisms class, dasha system, varga and ayanamsha. If it
   fails, Lane Ω is BLOCKED and you say so. The general "build against the contract and stub it"
   rule does NOT apply to Ω1.
2. 100% IS NOT NEGOTIABLE DOWNWARD. A domain you cannot bring to 100% accounting is PARKED-HONEST
   and left OUT of your C7 enforcement allowlist. You never lower the number, and you never let your
   gate block α or β (warn-only until you write contracts/C7.frozen, allowlist-scoped after).
3. YOU DO NOT GRADE YOURSELF. The sealed evaluator harness, the 60-item routing suite and the
   dark-corpus replay set were authored by the RUNWAY session — a non-participant — before you
   existed. That is the point. Use them exactly as given; do not adjust, extend or reinterpret them.

CONTRACT DEPENDENCIES: you consume C1 (budget_kb — Ω5 pages against it), C2 (category receipt —
Ω3's accounting primitive), C3 (schema map — Ω1's input), C6 (mechanisms availability — Ω6 blocks on
it), C8 (handler output shape — your dossier orchestrates α's handlers while α rewrites them), and
β's C5 (sidereal — lane F's target-graha checks). The SPECS exist from the start; the
IMPLEMENTATIONS land during the night. Build against the spec and stub it — BUT poll
~/elev-v2-shared/implementations/ at every lane boundary and RE-RUN any stubbed lane against the
live implementation once <Cn>.live appears (M2.5). HARD RULE: a lane may not be dispositioned
VERIFIED-CLOSED while any contract it consumes lacks a .live record — it is
PARKED-HONEST (blocked-on-<stream>:<Cn>). This is what stops you certifying Ω6 against your own stub
of a tool that is still 500ing in production. If a spec proves infeasible, file an AMENDMENT row in
CONTRACT_STATUS.md within your first hour.

Publish C7 (the accounting invariant) by T0+4h into CONTRACT_STATUS.md, and write contracts/C7.frozen
when final. Your C7 assertion lives in YOUR workflow file (.github/workflows/elev-depth-gates.yml);
the runway scaffolded the include point and no one else writes the assertion. intent_classify*.ts
was reassigned to you — it is yours to change for Ω4.

Heartbeat ~/elev-v2-shared/heartbeat/gamma.hb every 10 minutes. Integration battery before releasing
any merge lock (M2.6). SUCCESSION (M2.7): if ~/elev-v2-shared/heartbeat/alpha.hb goes >45 minutes
stale AND both sibling completion flags exist, YOU assume close ownership — run α's Phase 4 and
Phase 5 including §16 cleanup, and note the succession in the report.

Self-verify the §2 Ω-Verification flagship acceptance THROUGH THE SEALED HARNESS on TWO domains and
BOTH canonical charts (482012f1-710e-4a25-994a-93821f5871aa and 1c826d5a) before signalling done —
α re-runs and reports it, but it is your deliverable. Verify against LIVE PRODUCTION. Four
dispositions only; no "passed with caveats". NOT-REPRODUCED requires a verbatim-recipe regression
test AND a baseline payload diff.
When every lane is dispositioned, write your ledger section and
~/elev-v2-shared/STREAM_GAMMA_COMPLETE.flag as JSON per M2.8, with flagship_self_verified set
honestly. Base model Sonnet; Opus for yourself, your Verifier, and lanes Ω, I and F. Do not stop to
ask me anything — there is no one to ask. Begin with STEP 1: wait for the flag.
```

---

## In the morning

`ELEVATION_V2_RUN_REPORT_v1_0.md`. Read these five numbers first:

1. **TCI sanity gate** — passed, and the concept count. If it failed, Lane Ω is honestly BLOCKED and
   the depth mandate is unproven; that is a real outcome, not a hidden one.
2. **Ω3 accounting %** per flagship domain, and which domains made the C7 allowlist.
3. **Sealed-harness flagship score** — the naive "how is my wealth?" transcript graded against the
   frozen concept list, two domains, both charts.
4. **Dark-corpus count** over the frozen replay set. Target zero.
5. **Phase-4 revalidation downgrades** — how many early closes later deploys broke.

Expect a mix of VERIFIED-CLOSED, PREPARED-FOR-NATIVE, NOT-REPRODUCED and PARKED-HONEST across the 61
items — that spread is the design working, not a shortfall. A run reporting 61/61 green would be the
suspicious outcome.
