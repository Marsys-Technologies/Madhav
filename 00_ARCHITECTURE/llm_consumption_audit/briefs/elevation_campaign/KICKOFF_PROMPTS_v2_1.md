---
artifact: KICKOFF_PROMPTS (Elevation Campaign v2.1 — MODE 2, three processes)
version: 2.1
status: CURRENT
governs: ELEVATION_CAMPAIGN_CHARTER_v2_1.md §7.5 (MODE 2 binding operating protocol, M2.0–M2.11)
---

# Mode 2 kickoff — three prompts

## Before you launch (5 minutes, once)

```bash
# 1. Three separate clones — NEVER three sessions in one checkout (charter M2.0)
cd ~
git clone /Users/Dev/Vibe-Coding/Apps/Madhav madhav-alpha
git clone /Users/Dev/Vibe-Coding/Apps/Madhav madhav-beta
git clone /Users/Dev/Vibe-Coding/Apps/Madhav madhav-gamma

# 2. Point all three at the real origin so pushes reach GitHub
for d in alpha beta gamma; do
  ( cd ~/madhav-$d && git remote set-url origin "$(cd /Users/Dev/Vibe-Coding/Apps/Madhav && git remote get-url origin)" && git fetch origin && git checkout main && git pull )
done

# 3. Copy the untracked env files each clone needs (adjust if your .env names differ)
for d in alpha beta gamma; do
  cp /Users/Dev/Vibe-Coding/Apps/Madhav/platform/.env.local ~/madhav-$d/platform/.env.local 2>/dev/null
  cp /Users/Dev/Vibe-Coding/Apps/Madhav/.env.rag ~/madhav-$d/.env.rag 2>/dev/null
done

# 4. Shared coordination state, outside every checkout (charter M2.1)
mkdir -p ~/elev-v2-shared/{locks,implementations,heartbeat,proxy,contracts}

# 5. Sanity: prod credentials live
gcloud auth list && ( cd ~/madhav-alpha && git push --dry-run origin main )
```

**Launch order: Terminal 1 (α) FIRST.** Wait until it prints that Phase 0 is complete (it writes
`~/elev-v2-shared/PHASE0_COMPLETE.flag`, typically 45–60 min). **Then launch Terminals 2 and 3
together.** β and γ will poll for that flag anyway and abort safely if it never arrives — but
launching them early just burns their poll window.

Each terminal: `cd` into its own clone, start Claude Code with bypass permissions, paste its prompt.

---

## TERMINAL 1 — STREAM α (SATYA · Truth & Envelope) — LAUNCH FIRST

```
You are the Stream-Conductor for STREAM α (SATYA — Truth & Envelope) of the Elevation Campaign
v2.1, running FULLY AUTONOMOUSLY overnight. No human is available. Any question you would ask a
human, you answer yourself as Native-Proxy per charter §10, and log it.

Your working tree is ~/madhav-alpha and you must NEVER touch ~/madhav-beta or ~/madhav-gamma.
Shared coordination state is ~/elev-v2-shared/ (outside every checkout).

READ FIRST, IN THIS ORDER:
1. CLAUDECODE_BRIEF.md (repo root)
2. 00_ARCHITECTURE/llm_consumption_audit/briefs/elevation_campaign/ELEVATION_CAMPAIGN_CHARTER_v2_1.md
   — §0 IN FULL FIRST (the depth mandate is the campaign), then §7.5 MODE 2 rules M2.0–M2.11 which
   are BINDING on you, then §4 (your file manifest), §5.α (your lanes), §9 (verification), §11.
3. 00_ARCHITECTURE/llm_consumption_audit/ELEVATION_REGISTER_v1_0.md (v1.1, EL-01..EL-61, full read)
4. CLAUDE.md §N (build standards); 00_ARCHITECTURE/CURRENT_STATE_v1_0.md §2 (v6.41 open items)

═══ PART 1 — YOU OWN CAMPAIGN PHASE 0. Do this before any lane work. ═══
Per charter §7.1 + M2.4, in this order:
  a. mkdir -p ~/elev-v2-shared/{locks,implementations,heartbeat,proxy,contracts}
  b. Snapshot: git tag elev-v2-run-start && push it; take a DB snapshot; record both IDs.
  c. Cut elev/alpha, elev/beta, elev/gamma off main and push all three.
  d. Capture the SHARED Verifier BASELINE against PRODUCTION: every §5 lane recipe plus the §0.2
     depth probes (plan_retrieval + intent_classify on "How is my wealth?", the graha_portrait
     Venus starvation probe, bodha_mechanisms_get, argala, ref_planet_position_get). Raw payloads
     to ledgers/ELEVATION_V2_BASELINE.md. NOTHING MAY MERGE WITHOUT THIS.
  e. Author and FREEZE the α-owned contracts C1 (budget_kb), C2 (category receipt), C3 (schema-map
     output shape), C6 (mechanisms availability), C8 (handler output shape) — commit to main and
     record each in ~/elev-v2-shared/contracts/CONTRACT_STATUS.md. You do NOT author C4/C5 (β) or
     C7 (γ); their rows go in as DRAFT with owner and deadline.
  f. BUILD THE C3 SCHEMA-MAP GENERATOR NOW — it is a Phase-0 deliverable, not Phase-2. Lane Ω's
     TCI is generated from it and may never be stubbed (charter §2 Ω1). γ is blocked on this.
  g. Freeze, read-only, before any Ω builder exists anywhere: the SEALED EVALUATOR HARNESS
     (charter §2 Ω-Verification), the 60-item ROUTING SUITE (≥15 narrow-labelled items, §2 Ω4),
     the DARK-CORPUS REPLAY SET (≥20 questions per flagship domain, §2 Ω7), and OVERFLOW_QUEUE.md.
     These grade γ's work; γ must not author them.
  h. Pre-resolve the two known manifest collisions (M2.9): reassign
     platform-mcp/src/tools/intent_classify*.ts to γ, and scaffold an include point in
     .github/workflows/elev-depth-gates.yml for γ's C7 assertion (you never write the assertion).
  i. LAST, write ~/elev-v2-shared/PHASE0_COMPLETE.flag containing the full JSON manifest specified
     in M2.4. If Phase 0 fails at any step, write PHASE0_FAILED.flag so β and γ fail fast.
  Then print clearly: "PHASE 0 COMPLETE — launch β and γ."

═══ PART 2 — RUN STREAM α ═══
Lanes per §5: A (envelope/budget/receipt-truth — OPUS), B (broken surfaces), H (discovery, schema
map, entity faces, varga snapshots), K1 (serving CI gates). Spawn your own builders, your own
Verifier (which never builds), and a test-runner per §6.

SHIP FIRST, IN YOUR FIRST MERGE: the EL-37 fix (C6 — the query_mechanisms param-binding bug, root
cause is in §5.α.B; it is a hard_floor plan item and 100% down) and budget_kb (C1). γ's Ω5 and Ω6
are blocked on both.

After each merge+deploy, when your Verifier confirms a contract's implementation LIVE IN PROD,
write ~/elev-v2-shared/implementations/<Cn>.live per M2.5 with revision + image_sha + probe ref.
γ is polling that directory.

Edit ONLY files in your §4 manifest. Locks per M2.2 (mkdir at ~/elev-v2-shared/locks/, heartbeat
every 2 min, breakable only when heartbeat >5 min stale, two-phase break). The merge lock is held
through the platform auto-deploy and smoke gate (M2.3). Before releasing any merge lock you run the
integration battery and append to INTEGRATION_LOG.md (M2.6). Touch ~/elev-v2-shared/heartbeat/
alpha.hb every 10 minutes (M2.7).

Your K1 C7 accounting gate is WARN-ONLY until ~/elev-v2-shared/contracts/C7.frozen exists, and
allowlist-scoped thereafter (charter §2 Ω3). Never let it block β or γ.

═══ PART 3 — YOU OWN THE CLOSE ═══
Wait for STREAM_BETA_COMPLETE.flag and STREAM_GAMMA_COMPLETE.flag, deadline T0+11h (M2.8 — not 14h;
Phase 4 and 5 need their budget). Then:
  - PHASE 4: re-run EVERY VERIFIED-CLOSED item's G4 probe set against the FINAL head and downgrade
    any failure to PARKED-HONEST before reporting (§9.4 — prod changed under those closes all
    night). Run the flagship acceptance (charter §2 Ω-Verification) THROUGH THE SEALED HARNESS on
    two domains and both canonical charts — you read the score, you never play the consumer. Run
    the dark-corpus replay set fresh. Run the red-team pass and the chart-agnostic/contamination
    checks.
  - PHASE 5: finalise the §15 coverage matrix, append per-EL dispositions to the register, merge
    the three proxy ledgers and the three stream ledgers, close CURRENT_STATE + SESSION_LOG, remove
    every worktree and delete every elev/* branch, and write
    ELEVATION_V2_RUN_REPORT_v1_0.md led by the §0 mandate scorecard and the dark-corpus report.

Canonical charts: 482012f1-710e-4a25-994a-93821f5871aa and 1c826d5a. Verify on BOTH, against LIVE
PRODUCTION, never a worktree. Four dispositions only (§9.6); there is no "passed with caveats".
NOT-REPRODUCED requires a committed verbatim-recipe regression test AND a baseline payload diff.
Base model Sonnet; Opus for yourself, your Verifier, and lane A. Do not stop to ask me anything.
Begin with Phase 0.
```

---

## TERMINAL 2 — STREAM β (GAṆITA · Compute & Corpus) — launch after α prints Phase 0 complete

```
You are the Stream-Conductor for STREAM β (GAṆITA — Compute & Corpus) of the Elevation Campaign
v2.1, running FULLY AUTONOMOUSLY overnight. No human is available. Any question you would ask a
human, you answer yourself as Native-Proxy per charter §10, logging to
~/elev-v2-shared/proxy/beta.md.

Your working tree is ~/madhav-beta and you must NEVER touch ~/madhav-alpha or ~/madhav-gamma.
Shared coordination state is ~/elev-v2-shared/.

═══ START GATE — do this before anything else (charter M2.4) ═══
Poll for ~/elev-v2-shared/PHASE0_COMPLETE.flag every 60s, ceiling 90 minutes.
VALIDATE EVERY FIELD of its JSON manifest: run_start_tag resolves, db_snapshot_id present,
baseline_ledger_path exists and its sha256 matches, contracts C1/C2/C3/C6/C8 exist at their
recorded shas, branch elev/beta resolves, and the sealed harness / routing suite / replay set /
overflow queue files exist. If PHASE0_FAILED.flag appears, or the timeout expires, or ANY field
fails validation: write ~/elev-v2-shared/PHASE0_TIMEOUT_beta.flag and ABORT. There is no
"looks fine, proceed" path — working without a baseline produces legally unmergeable code.

READ, IN THIS ORDER:
1. CLAUDECODE_BRIEF.md
2. .../briefs/elevation_campaign/ELEVATION_CAMPAIGN_CHARTER_v2_1.md — §0 IN FULL FIRST, then §7.5
   MODE 2 rules M2.0–M2.11 (BINDING), §4 (your manifest), §5.β (your lanes), §9, §11 (especially
   §11.9, the rollback runbook — you are the stream most likely to trigger it).
3. 00_ARCHITECTURE/llm_consumption_audit/ELEVATION_REGISTER_v1_0.md (v1.1, full read)
4. CLAUDE.md §N; CURRENT_STATE_v1_0.md §2 (v6.41 — A-3, A-5, A-6 and CR-131 are yours)

═══ RUN STREAM β ═══
Lanes per §5: D (indexing/writer integrity + chart-scoped rebuild — OPUS), D2 (sahams + bhanga —
OPUS, citations MANDATORY, never invent a rule), C (sidereal ephemeris route + panchāṅga service),
G (remedy engine + bounded corpus structuring; supersedes the A-5 accept-as-dark recommendation),
T (gochara DATABASE_URL fix, ka_gochara_sweep resume from 165/300, timing-anchor re-verification).

PUBLISH YOUR CONTRACTS EARLY — deadline T0+3h: C4 (the ONE house/sign convention ruling) and C5
(sidereal response shape). Record both in ~/elev-v2-shared/contracts/CONTRACT_STATUS.md as FROZEN.
α's convention gate and γ's muhūrta target-graha checks are waiting on them. If you later change
either, file it as an AMENDMENT row — that is binding rework on the other streams (M2.10).

ESTATE SAFETY IS NOT OPTIONAL (charter §5.β.D step 5): you rule one convention and rebuild only two
charts, but α's serving gate then enforces that convention for ALL charts. Either persist a per-row
house_convention tag and have serving normalise by tag, or ship the serving change behind a flag ON
only for rebuilt charts — and add one NON-CANONICAL third chart to every convention G4 check. Record
which mitigation you chose. Without this you leave every other production chart silently wrong.

Rebuilds: chart-scoped delete-then-insert only, via the FROZEN orchestrator, using the existing
platform/scripts/dispatch_*_rebuild_job.py pattern (python -m scripts.dispatch_<name> from
platform/). Hold the db-rebuild lock throughout, heartbeating every 2 minutes — your rebuild is
far longer than any age-based TTL, which is exactly why M2.2 keys breakage off heartbeat liveness.
FORENSIC 7/7 asserted after EVERY rebuild; run the MSR drift check after. A FAILED FORENSIC HALTS
YOU IMMEDIATELY and triggers the §11.9 rollback runbook: take the global RESTORE lock (freezing all
merges and deploys across all three streams), restore chart-scoped rows from the snapshot, re-prove
with FORENSIC + smoke, reopen the affected EL ids to PARKED-HONEST, release, log.

Never touch: the FROZEN orchestrator contract, the sealed L5 split, the FORENSIC birth anchors,
chart 362f9f17 (dead phantom). Edit ONLY files in your §4 manifest; a cross-manifest need is
PARKED-HONEST naming the owner, never negotiated (M2.9).

Locks per M2.2. Merge lock held through auto-deploy + smoke (M2.3); run the integration battery
before releasing it (M2.6). Write ~/elev-v2-shared/implementations/C4.live and C5.live once your
Verifier confirms them live in prod (M2.5). Heartbeat to ~/elev-v2-shared/heartbeat/beta.hb every
10 minutes (M2.7).

Verify on BOTH canonical charts (482012f1-710e-4a25-994a-93821f5871aa and 1c826d5a) plus the third
chart for convention checks, against LIVE PRODUCTION. Four dispositions only; no "passed with
caveats". NOT-REPRODUCED requires a verbatim-recipe regression test AND a baseline payload diff.
When every lane is dispositioned, write your ledger section and
~/elev-v2-shared/STREAM_BETA_COMPLETE.flag as JSON per M2.8.
Base model Sonnet; Opus for yourself, your Verifier, and lanes D and D2. Do not stop to ask me
anything. Begin with the start gate.
```

---

## TERMINAL 3 — STREAM γ (PŪRṆA · Depth & Intelligence) — launch after α prints Phase 0 complete

```
You are the Stream-Conductor for STREAM γ (PŪRṆA — Depth & Intelligence) of the Elevation Campaign
v2.1, running FULLY AUTONOMOUSLY overnight. No human is available. Any question you would ask a
human, you answer yourself as Native-Proxy per charter §10, logging to
~/elev-v2-shared/proxy/gamma.md.

YOU CARRY THE CAMPAIGN'S CENTRAL MANDATE. Charter §0 and §2 define your success; read them first
and treat everything else as support.

Your working tree is ~/madhav-gamma and you must NEVER touch ~/madhav-alpha or ~/madhav-beta.
Shared coordination state is ~/elev-v2-shared/.

═══ START GATE — do this before anything else (charter M2.4) ═══
Poll for ~/elev-v2-shared/PHASE0_COMPLETE.flag every 60s, ceiling 90 minutes. VALIDATE EVERY FIELD
of its JSON manifest (tag resolves, db_snapshot_id present, baseline exists with matching sha256,
contracts C1/C2/C3/C6/C8 at recorded shas, elev/gamma resolves, sealed harness + routing suite +
dark-corpus replay set + overflow queue all present). If PHASE0_FAILED.flag appears, or the timeout
expires, or any field fails: write ~/elev-v2-shared/PHASE0_TIMEOUT_gamma.flag and ABORT.

READ, IN THIS ORDER:
1. CLAUDECODE_BRIEF.md
2. .../briefs/elevation_campaign/ELEVATION_CAMPAIGN_CHARTER_v2_1.md — §0 AND §2 IN FULL FIRST, then
   §7.5 MODE 2 rules M2.0–M2.11 (BINDING), §4 (your manifest), §5.γ (your lanes), §9, §11.
3. 00_ARCHITECTURE/llm_consumption_audit/ELEVATION_REGISTER_v1_0.md (v1.1, full read)
4. CLAUDE.md §N; CURRENT_STATE_v1_0.md §2

═══ RUN STREAM γ ═══
LANE Ω FIRST AND ABOVE ALL (charter §2): Ω1 total concept inventory generated from the DATABASE via
α's C3 schema map — never from floors; Ω2 permissive domain relevance map, 100% classified,
include-on-uncertainty; Ω3 the 100%-accounted completeness contract; Ω4 depth-default routing;
Ω5 paged dossier with a STRUCTURAL synthesis gate; Ω6 patterns/chains/mechanisms first-class;
Ω7 dark-corpus report; Ω8 floors regenerated from the TCI.
Then: I (planner coverage, cross-ayanamsha agreement engine, dossier, composition doctrine),
E (assessors, verdict layer, ranking, one rank vocabulary), F (muhūrta intelligence, active dashas,
election filing), J (calibration lifecycle + the two native packets), K2 (consumption metric +
battery upgrades).

THREE RULES THAT OVERRIDE CONVENIENCE:
1. THE TCI MAY NEVER BE STUBBED. It is the denominator of every accounting sum — a partial TCI makes
   every Ω gate pass on a fake corpus and is the single highest-probability false-success path in
   this campaign. Run the hard sanity gate in §2 Ω1: distinct fact_category count in the TCI must be
   ≥ the distinct fact_category count in production, asserted by an INDEPENDENT query written by
   your Verifier, plus ≥1 entry per bodha_mechanisms class, dasha system, varga and ayanamsha. If it
   fails, Lane Ω is BLOCKED and you say so — you do not proceed on a stub. The general
   "build against the contract and stub it" rule does NOT apply to Ω1.
2. 100% IS NOT NEGOTIABLE DOWNWARD. A domain you cannot bring to 100% accounting is PARKED-HONEST
   and left OUT of your C7 enforcement allowlist. You never lower the number, and you never let your
   gate block α or β (it is warn-only until you write contracts/C7.frozen, allowlist-scoped after).
3. YOU DO NOT GRADE YOURSELF. The sealed evaluator harness, the 60-item routing suite and the
   dark-corpus replay set were frozen by α in Phase 0 before you existed. Use them as given. Your
   Verifier reads scores; it never plays the consumer, and it never authors the test set.

CONTRACT DEPENDENCIES: you consume α's C1 (budget_kb — Ω5 pages against it), C2 (category receipt —
Ω3's accounting primitive), C3 (schema map — Ω1's input), C6 (mechanisms availability — Ω6 blocks on
it), C8 (handler output shape — your dossier orchestrates α's handlers while α rewrites them), and
β's C5 (sidereal — lane F's target-graha checks). If an implementation is not live yet, build
against the contract and stub it — BUT poll ~/elev-v2-shared/implementations/ at every lane boundary
and RE-RUN any stubbed lane against the live implementation once <Cn>.live appears (M2.5). HARD
RULE: a lane may not be dispositioned VERIFIED-CLOSED while any contract it consumes lacks a .live
record — it is PARKED-HONEST (blocked-on-<stream>:<Cn>). This is what stops you certifying Ω6
against your own stub of a tool that is still 500ing in production.

Publish C7 (the accounting invariant) by T0+4h into CONTRACT_STATUS.md, and write contracts/C7.frozen
when it is final. Your C7 assertion lives in YOUR workflow file (.github/workflows/elev-depth-gates.yml);
α scaffolded the include point and never writes the assertion. intent_classify*.ts was reassigned to
you in Phase 0 — it is yours to change for Ω4.

Locks per M2.2; merge lock held through auto-deploy + smoke (M2.3); integration battery before
releasing it (M2.6). Heartbeat to ~/elev-v2-shared/heartbeat/gamma.hb every 10 minutes.
SUCCESSION (M2.7): if ~/elev-v2-shared/heartbeat/alpha.hb goes >45 minutes stale AND both sibling
completion flags exist, YOU assume close ownership — run Phase 4 and Phase 5 per α's Part 3 and note
the succession in the report.

Self-verify the §2 Ω-Verification flagship acceptance THROUGH THE SEALED HARNESS on TWO domains and
BOTH canonical charts (482012f1-710e-4a25-994a-93821f5871aa and 1c826d5a) before signalling done —
α re-runs and reports it, but it is your deliverable. Verify against LIVE PRODUCTION, never a
worktree. Four dispositions only; no "passed with caveats". NOT-REPRODUCED requires a verbatim-recipe
regression test AND a baseline payload diff.

When every lane is dispositioned, write your ledger section and
~/elev-v2-shared/STREAM_GAMMA_COMPLETE.flag as JSON per M2.8, with flagship_self_verified set
honestly. Base model Sonnet; Opus for yourself, your Verifier, and lanes Ω, I and F. Do not stop to
ask me anything. Begin with the start gate.
```

---

## What to check in the morning

`ELEVATION_V2_RUN_REPORT_v1_0.md` — but read these five numbers first:

1. **TCI sanity gate result.** If it failed and Lane Ω is BLOCKED, that is the honest outcome and
   everything else in the depth mandate is unproven. If it passed, note the concept count.
2. **Ω3 accounting %** per flagship domain, and which domains are in the C7 allowlist.
3. **Sealed-harness flagship score** — the naive "how is my wealth?" transcript, graded against the
   frozen concept list, on two domains and both charts.
4. **Dark-corpus count** — computed over the frozen replay set. Target zero.
5. **Phase-4 revalidation downgrades** — how many items closed early were broken by later deploys.

Then the ratification packet and the LEL intake packet, which are the only two things that need you.
