---
artifact: KALAYANTRA_CAMPAIGN_CHARTER
canonical_id: KALAYANTRA_CAMPAIGN_CHARTER
version: "1.1"
status: ACTIVE — native-directed, fully autonomous execution campaign. This file is authoritative over every prompt in this folder. Where it and a prompt disagree, this file wins. Where it and the plan documents disagree on WHAT to build, the plan documents win and the disagreement is a defect ADHIKĀRIN rules on. (Filename keeps v1_0 by repository convention; the frontmatter version is authoritative.)
campaign_id: kalayantra
campaign_name: "KĀLA-YANTRA (कालयन्त्र) — the time-engine: the Kāla layer built as one engine"
produced_on: 2026-10-06
produced_in: 'Claude Code (Fable 5.1); v1.1 after Astra''s review of v1.0 (REWORK, 11 blocking) — reviews/ASTRA_REVIEW_KALAYANTRA_CHARTER_v1_0.md; reconciliation in reviews/KALAYANTRA_CHARTER_RECONCILIATION_v1_0.md'
native_directive: 'Abhisek Mohanty, 2026-10-06 (verbatim in §1)'
plan_documents:
  - '00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md (sha256 85d999442273caf975d40a950d013e9b8c4efcd64402718ffd833237ff96a9ef) — WHAT and in WHICH ORDER (§9)'
  - '00_ARCHITECTURE/briefs/l3_families/KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md (sha256 ec382daa61eed5fde19bc4d9e8bca45719ab5b82de878c4c1e8893bd52524569) — the astrology inside each asset'
  - '00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_VALUE_REVIEW_v1_1.md (sha256 57d528320b5ee1b514d442a129f699b3fae0a166bb4e4651cbb6325ccde483bc) — evidence base'
  - '00_ARCHITECTURE/briefs/l3_families/decisions/KALA_LAYER_NATIVE_RULINGS_v1_0.md (sha256 dcb854cb796f7b3d736a72e9c77f33639dff586194dac836c6ef6ca23d1eb5be) — NR-KALA-R13 / R12 / R2'
  - '00_ARCHITECTURE/briefs/l3_families/reviews/KALA_LAYER_PLAN_RECONCILIATION_v1_0.md (sha256 f418ef9d9000a4c7e20dce78cefcd9210617f7b1fda91d107515290243ea7b24)'
  - 'all five are committed on branch campaign/kalayantra and land on main with B-1; B-0 verifies these hashes in the checkout before any other bootstrap step'
absorbs: 'the Pravāha campaign (Gochara 5.0) in full — tracker, plan model, open PRs, decisions, holds and the steward role (§2.3), under an explicit ownership transfer (B-5)'
fleet_root: /Users/Dev/kalayantra
campaign_branch: campaign/kalayantra
control_plane: '00_ARCHITECTURE/control/kalayantra/plan_model.json (145 items, generated; every item carries its brief) served by a second instance of the Pravāha tracker on 127.0.0.1:8767, generalised by B-1b (atomic claims, guarded completion, structured decisions, verdict events, audit) — §4'
production_boundary: 'fleet/executor.py — the only process holding a production credential; it runs only operations and code merged to main; agents submit typed requests and read credential-free receipts (§7)'
hold_switch: /Users/Dev/kalayantra/HOLD
changelog:
  - "1.1 (2026-10-06): reconciliation with Astra's review. Control plane: atomic per-worker claims, guarded completion (deps ∧ steps ∧ accepted verdict at exact head ∧ detector), structured decision outcomes, verdict events, audit — all B-1 deliverables with acceptance cases; no K worker runs before B-7. Credentials: agents start under an allow-listed environment; production operations go through a fixed-operation executor with typed requests and receipts; the fleet refuses to start if a secret is in its environment. Review before queue: workers never enable auto-merge; SŪTRADHĀRA queues only verdict-accepted heads. Gochara absorption: J lane re-cut into twelve landing phases; G6 requires every protocol endpoint to pass (no insufficient_evidence for the flip); G7 requires a real teardown; the authority CHECK replacement migration and legacy-reader cutover are explicit items. Close: a mandatory-results join; the finalizer runs outside the agents. Supervisor: process groups, lane locks, atomic cycle reservations for all lanes, per-cycle logs, STOP before HOLD, Codex profile madhav-parity. Deploy compatibility: expand/contract predicate on every item that changes writer or reader semantics. Value checkpoint runs on the full G1 baseline. Residual risks stated (§15)."
  - "1.1 additions found while setting up (2026-10-06): the Pravāha tracker package, its plan model, the measuring-build contract and about 230 review and decision records existed only as untracked files on disk — copied into the bootstrap branch (B-1a) so the absorbed work is in the repository. The tracker, the fleet supervisor and the executor each run from a snapshot, and the executor reads its operations table and scripts from origin/main, so a working-tree edit cannot change a running process. The local secret scan is run as CI runs it. Pool size is a file the conductor writes (no implementation worker before launch acceptance). Items: an adapters-and-services packet (KA), a contract-phase packet (KR), a mandatory flag, and not_applicable as a terminal state so an honest gate failure closes the campaign CLOSED-PARTIAL instead of stalling it."
  - "1.0 (2026-10-06): first version; reviewed by Astra as REWORK."
---

# KĀLA-YANTRA — campaign charter

**Written for:** the agents of the fleet (SŪTRADHĀRA, ADHIKĀRIN, PARĪKṢAKA ×2, the KĀRAKA pool) and the two operator-run processes (fleet supervisor, executor). The native reads §0, §1, §15 and the kickoff.

## §0 · Mission and definition of done

**Mission.** Build the Kāla layer as one temporal engine, exactly as `KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md` §9 sequences it and `KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md` specifies it, absorbing the Gochara 5.0 work (Pravāha) to its '5.0' flip without losing any of it, and leave the layer rebuilt for the canonical chart, served, and carrying its certification mapping — with no human in the loop after kickoff.

**Done means all of the following are TRUE by their detectors and accepted by independent verdict** (plan-model item `JOIN-ALL` joins every mandatory item; `C-4` is the final acceptance after the post-stop receipt):

1. Every mandatory K-packet item is complete: dependencies done, steps done, its exact reviewed head merged to `main` through the merge queue with CI green, PARĪKṢAKA's verdict ACCEPTED for that head, and its runtime evidence (migration applied, deploy green, local rehearsal) accepted — in the order plan §9 fixes.
2. Gochara 5.0: the two small tests (with real teardowns), the measuring build, the final-rules candidate and the full century build have run; the generation `'5.0'` is sealed by the separately dispatched verification job; the evaluation protocol v2.3 and the A5.7 gates are **run and recorded** (by the native's direction they are the tuning baseline, not a gate; an engineering defect still blocks); the authority CHECK replacement migration is deployed; the serving reader is live; **chart `482012f1-710e-4a25-994a-93821f5871aa` is flipped to `'5.0'`** by ADHIKĀRIN's ruling under G6; soak and legacy retirement are recorded; the Pravāha tracker is closed read-only with its close report.
3. The layer is rebuilt for the canonical chart through the orchestrator (lease held, backup verified, dry run, one slot, executor-dispatched): every K-stage writer's own detector reads built; read models are populated; the seven views resolve through the retrieval registry and the Vidhi bridge; `kala_now_get` serves the negative-space sentinel distinction; the arrival line renders the honest state.
4. Each implemented asset ships its certification mapping (plan §7) with the detector revision named; a rehearsal census records the **expected** verdict per gate, honest `NO_DETECTOR` included.
5. The close report exists; the campaign-level `SESSION_CLOSE` validates; `SESSION_LOG`, `CURRENT_STATE` and the cross-cutting decision register are updated through a merged PR; the finalizer's post-stop receipt shows no fleet process and no lane worktree remaining; PARĪKṢAKA's final verdict (`C-4`) accepts the five lines against their evidence.

Nothing else is in scope. Anything not on the path to these five lines is a digression and is refused (§8).

**This campaign's close is not certification.** The Suvarṇa engine certifies the Kāla assets afterwards, may change them, and rebuilds the data; this campaign delivers code written to Suvarṇa's per-asset elevation template, its data as a measured rehearsal of the rebuild, and Gochara 5.0 switched on.

**What this charter does not promise.** That the evaluation's scores will be good — they are recorded, not gated. It guarantees that a failure is detected, recorded as a failure, never relabelled success — and that the fleet keeps working on everything that does not depend on it. A mandatory item whose gate honestly and finally fails ends `not_applicable`; the close report then reads that line **NOT MET** and the campaign closes `CLOSED-PARTIAL`, never `CLOSED`.

## §1 · The native's directive (verbatim) and what it changes

> "the plan for me is to execute this Kāla strategy plan … I want to do it in a way that it is successfully implemented without fail. … in a different work tree so that it does not impact the other work … high throughput, running in parallel wherever possible and sequentially wherever essential … optimise the entire development and CI/CD deployment. Very importantly, I want to cut the governance and security-related overwork to only the essential and minimal … fully autonomous … a complete agentic swarm … The Gochara 5 has been mostly implemented, if not completely. It should be fully absorbed. We should not lose that work. There should be no human gates, no approval from humans. Have an owner surrogate or a native surrogate to address any requirements so that the execution can happen fully autonomously. … implement this very focussedly, without digressions, without idle time, with high throughput, targeting the completion of all the assets and the campaign. Don't bother with other digressions which exist."
> — Abhisek Mohanty, 2026-10-06

**Recorded as ruling `NR-KALA-AUTONOMY-20261006` (and, for the shared register, as the CCD entry B-4 writes):**

**Native direction of 2026-10-07 (`NR-KALA-DIRECTION-20261007`), verbatim in substance:** "Gochara is the way forward. There is nothing for me to prove. We may need to tweak it, elevate it, change it, modify it — those are future enhancements." "I am not averse to multiple rebuilds; one objective of this exercise is to make the rebuild fully efficient, and wherever I can avoid one I happily do so." "When the Suvarṇa engine runs on Kāla it will test Kāla as the template of elevating each asset, and it may make changes on Kāla." Consequences: (1) the Gochara '5.0' switch-on is gated on **engineering correctness**, not on the evaluation protocol passing — the evaluation is run and recorded as the baseline for future tuning; (2) production rebuilds stay in scope and are measured (their cost is a product of this campaign); (3) this campaign's close is not certification: the Suvarṇa engine certifies the Kāla assets afterwards and may change them, so Kāla code is written to Suvarṇa's per-asset elevation template and to an agreed daśā-table contract, so that the certification run elevates rather than rewrites.

- Every decision the plan documents or Pravāha reserved to the native or its steward — `D-FLIP`, `D-T2`, `D-G9`, `D-CLOUD`, production chart-data writes on the governed path, the steward's holds, and the five held plan decisions R-5 / R-6 / R-8 / R-9 / R-11 — passes to **ADHIKĀRIN** (§9; `KALAYANTRA_OWNER_SURROGATE_CHARTER_v1_0.md` v1.1), **subject to the unchanged evidence gates**. Delegation changes who decides, never what counts as evidence.
- Governance is the §8 minimum. Per-session reading sequences, per-cycle handshakes, decision packets to the native and review ceremonies not named in §10 are not part of this campaign.
- Isolation is physical for files (`/Users/Dev/kalayantra/`) and procedural for everything files cannot isolate (§13, §15).
- The frozen contracts and the doctrine rulings (`NR-KALA-R13/R12/R2`) are not relaxed by autonomy.
- The only things that remain the human's are the three in §9.3 — credentials, the spend ceiling, the HOLD switch — none of which gates work: a missing credential blocks only the production items that need it, honestly, while every local item proceeds.

## §2 · Scope

### 2.1 In scope — the work (plan §9 re-sequenced; plan model §4)

| Phase | Items | What lands |
|---|---|---|
| **B** bootstrap | B-0 … B-8 | specifications hash-verified; tracker package and Pravāha's unsaved material in the repository; control plane generalised with acceptance cases; executor live; lane environments; campaign SESSION_OPEN + CCD entry; Pravāha ownership transfer; bootstrap PR merged; launch acceptance (B-7) releases one worker; first earned progress (B-8) raises the pool |
| **K0a** vertical slice | K0a-0 … K0a-4, V-K0a | the campaign's tests really run by CI (K0a-0: a canary in the required job; one additive job for database-backed tests where a skip is a failure); `kala_core` with real code; G1 clock repair; candidate → verification → publication contract (the verification dispatch is real, not a stub); one assertion end-to-end with mutations that fail |
| **K1 ∥ K2 ∥ K7 ∥ KA** | K1-1a/b, K2-1a/b, K2-2, K7-1a/b, K7-2, K7-3, K7-4, KA-1 … KA-4b | F2 clocks; F1 graph + resolver; serving composites, aliases, bridge, the two serving defects, density contracts, Tulana wiring (on `D-R6`); the shared sky, rules, overlays and calendar modules with the five adapters and three services re-based on them (plan §3.2, §4.1 adapters paragraph, §8) |
| **K1b, K3** | K1-2, K3-1, K3-2 | Avadhi read model; negative space on fixtures, then on the sealed real generation |
| **K4** | K4-1, K4-2a/b, K4-3, V-K4 | shared null preparation + the jury's experiment; `ka_sangam` rewrite with a compatibility shim for live readers until K9-4; claim attachment |
| **K5-G1, VC** | K5-G1a, K5-G1b, VC-1, VC-2, D-VC, V-VC | the **full** G1 baseline lands first (algorithm 3.20 a–g) and is frozen at K5-G1b's merged head; then the frozen ablation on it; the surrogate adjudicates |
| **K5** | K5-2, D-COMPACT, K5-2b, D-G2, K5-3 | compact-evaluator trial under the numerical contract; dense rows retired only on `approved`; G2 only on `approved` with every element specified |
| **K6** | K6-1 … K6-5 (+K6-5a L5 contract), V-K6 | read models; registrar after `D-R11` and the L5 lifecycle contract |
| **K8** | K8-R26, K8-K0a, K8-K12, K8-KA, K8-K3, K8-K4, K8-K5, K8-K6, K8-K7, K8-REG | plan §7's gate table reconciled with the criterion registry revision live on `main` (26; the plan was written against 25) first; then the certification mapping per landed packet (serving and adapters included, L3 entries of the declarations file only); registry-truth migration last, depending on every mapping |
| **L0** | L0-M, L0-K | scoped muhūrta parihāra extraction; KP Reader ingestion — both through the existing ingestion/migration mechanism (surrogate charter H1 exception) |
| **J** judge (absorbed Pravāha) | J-0, J-0m, J-1a … J-8 (twelve landing phases, §2.3) | inventory and disposition, then PR-sized children under each phase join; small tests with teardowns; measuring build; upstream release and protected window; final-rules candidate; full build; qualification; seal; serving + authority migration + rollback rehearsal; flip; soak; retirement; Tier-2; L5 hand-off; Pravāha close |
| **K9, KR** | K9-1 … K9-6, KR-1, KR-2, V-K9 | rehearsal build; benchmarks; drills; production rebuild + publish (executor); census; live acceptance of the views and the arrival line; then the contract phase — code whose replacement is published is deleted, legacy second writers retired (on `D-KR`) |
| **C** close | JOIN-ALL, C-1 … C-4 | mandatory join; close report; SESSION_CLOSE + SESSION_LOG + CURRENT_STATE + CCD; finalizer (external); final acceptance |

### 2.2 Out of scope — refused, not parked

Work on L0–L2 or L4–L5 beyond the two named L0 demands and the L5 issued-forecast lifecycle contract (K6-5a); Nirmāṇa, Suvarṇa, Pūrṇa-Anveṣaṇa and Paripraśna work (branches, worktrees, PRs, trackers, ledgers untouched — §13); a second chart (D-SCOPE); any change to the frozen orchestrator contract or the frozen Gochara spec v1.4 beyond the routed amendments (R-1, R-3, the measuring-build horizon); portal UI beyond wiring the arrival line to `kala_now_get`'s honest output; "while I was here" refactors; new asset ids (`NR-KALA-R2`); merging an inherited PR outside its landing phase.

### 2.3 Absorbed — Pravāha (Gochara 5.0)

Pravāha is **absorbed, not restarted**. Its tracker (`127.0.0.1:8766`) stays running as the earned-signal record for its 102 items; the J lane works them through the Pravāha CLI as streams `A`/`B` so Pravāha's own detectors decide. **B-5 makes the hand-over real:** (a) verify that no Pravāha writer is active (the Kimi runner `C` is retired; `A`/`B` were human-driven Claude sessions — check `pgrep`, the runner logs and `run/` state, and record it); (b) register the KY lane worktrees and the `kalayantra/j-*` + `pravaha/*` branch patterns in the Pravāha plan model's stream definitions (a steward edit of the model, committed with the hand-over PR) so `pravaha preflight` passes from a KY lane; (c) preserve `EVENTS.jsonl`, unacknowledged messages, item owners, quota/hold state, dirty worktrees and running job ids; (d) write `NATIVE_DIRECT_RULINGS_20261006.md` in Pravāha's `decisions/` with the native's verbatim words and the transfer of the steward role to ADHIKĀRIN; (e) `pravaha send --as steward` to A and B; (f) **preserve**: the tracker package, the Pravāha plan model, `MEASURING_BUILD_CONTRACT`, about sixty review records and the decision and owner-instruction records of `/Users/Dev/pravaha/run/` existed only as untracked files — the setup session copied them into the bootstrap branch (`platform/scripts/governance/pravaha_tracker/`, `00_ARCHITECTURE/control/pravaha/`, `00_ARCHITECTURE/briefs/pravaha/**` incl. `run_records/2026-10-06/`), two files flagged by the secret scan excepted and left on disk; the live event log, snapshots, runner logs and backups are archived at close (J-8a). B-5 is ADHIKĀRIN's item (it is the new steward), delivered as branch `kalayantra/n-b5` that SŪTRADHĀRA merges into the bootstrap PR.

**J-0 is triage and ordered disposition, never "land everything"; J-0m then turns the disposition into PR-sized child items under each phase join.** For each open `pravaha/*` PR (37 at review time — the fleet counts them live), each remaining item, decision and hold: `keep / merge / supersede / salvage / not-applicable`, with evidence, owner, dependencies and the **landing phase**. The twelve phases (from the inherited runbooks `SMALL_TEST_SITTING_CHECKLIST`, `MEASURING_BUILD_CONTRACT`, `FINAL_BUILD_SCOPE`, `ROLES_AND_SEAL_PROVISIONING_RUNBOOK`, `PROTECTED_WINDOW_REHEARSAL_PLAN`):

1. small-test prerequisites only (nothing the checklist says must stay unmerged — e.g. G8 PR 3141 — lands here);
2. run 1 → readback → teardown → absence proof;
3. run 2 → readback → teardown → absence proof;
4. measuring builder/verifier prerequisites on the measuring rules;
5. measuring dispatch → readback → golden capture → report → teardown;
6. final-build decisions and upstream release prerequisites (Suvarṇa SETTLED-1 / single Vimśottarī build — an external prerequisite with its own detector);
7. protected-window changes and independent readbacks (grants, principals, 1240/1241 lineage);
8. final-rule builder/verifier changes with their equality / non-interference proofs;
9. final-rules candidate, density/residual decisions, cap qualification;
10. final build → A5.7 engineering gates + evaluation protocol v2.3 → independent verification → seal;
11. serving migration (the authority CHECK replacement — migration 1236 refuses a `5.x` authority by design; its reviewed replacement is item J-6m), end-to-end reader and rollback acceptance, `D-FLIP`;
12. flip, live readback, soak, legacy retirement (A6.2), admitted Tier-2 and L5 hand-off (B6.2), original Pravāha closure.

Nothing of Gochara 5.0 is rewritten by the K lanes; they consume it (plan §2.2 judge row; R-1). **Shared-file ownership:** inherited PRs touch `ka_gochara_v5.py`, kernel manifests, generated writer digests, mūrti/vedha writers and generated inventories; J-0 produces a file-ownership map and K items that touch those files wait for the inherited change to land first (the item brief names them).

## §3 · The swarm

### 3.1 Roles

| Role | Lanes | Model / effort | Owns | Never |
|---|---|---|---|---|
| **SŪTRADHĀRA** (conductor) | `sutradhara` | `gpt-6-sol` / high | bootstrap B-0…B-8 (except B-1c, B-5); fleet health; the only hand that queues a campaign PR (after verdict + CI + compatibility + lease); merge-queue pacing; designated writer of `plan_model.json`; the lease; ledger and digests; SESSION_OPEN/CLOSE; close report | stage code or astrology; a reserved ruling; queueing an unverified head |
| **ADHIKĀRIN** (owner surrogate) | `adhikarin` | `gpt-6-astra` / xhigh | every decision the native reserved (§9); the Pravāha steward role and its hand-over (B-5); production operation **requests** to the executor under G8; inter-lane disputes; precedent; execution-mechanics repair (G12) | touching a credential; weakening a gate; verifying its own operation; dispatching anything itself |
| **PARĪKṢAKA** (verifier) | `v1`, `v2` | `gpt-6-astra` / xhigh | exact-head verdicts for every item in `review`; packet-exit reviews; pre-operation acceptance receipts and post-operation readbacks; B-1c, the launch verdict, the final acceptance C-4 | authoring a fix; a verdict without the measured command; completing an item (the guarded transition does that) |
| **KĀRAKA** (worker pool) | `k1`…`k6` | `gpt-6-sol` / high | atomic claim of one READY item for its `worker_id`; implementation to the item brief; PR + review request | enabling auto-merge; another worker's claim; rebasing a published branch; a credential |
| **executor** (not an agent) | operator-run process | — | the only holder of production credentials; runs typed operation requests from a closed set, at merged commits only; writes credential-free receipts; runs the finalizer | taking instructions from anything but a validated request file |
| **supervisor** (not an agent) | operator-run process | — | lane loops, locks, process groups, reservations, backoff, idle spacing | holding a secret |

### 3.2 Process model — supervised cycles, fresh sessions, isolated environment

`fleet/kalayantra_fleet.sh` ports the Nirmāṇa v2.3 supervised-cycle loop to Codex:

- `up` **snapshots** the fleet folder to `/Users/Dev/kalayantra/fleet_live` and starts one loop per lane from the snapshot, each fully detached into its own session (it survives the shell or the Codex session that started it) and under a **lane lock** (a second `up` cannot duplicate a lane). Role prompts are read from `wt/campaign` at each cycle.
- Each cycle invokes `codex exec -p kalayantra` in the lane's worktree. The profile is **generated** before every cycle by `fleet/make_codex_profile.sh` as an overlay on the operator's Codex configuration: the `madhav-parity` posture (approvals never, full access — GIP §P.4) with **every personal MCP server and plugin switched off** (the operator's configuration carries, among others, a database connector with an embedded connection; a lane must not have it) and the turn-end notifier silenced. `madhav-parity.config.toml` itself does not load against the current base configuration and is not used. The cycle runs with the model and effort of the role, the cycle prompt on stdin and the last message written to a **per-cycle** file; the process runs in its own **process group** under a controller that enforces the 90-minute cap and reaps every descendant.
- The agent's environment is **allow-listed with `env -i`**: `HOME`, an explicit tool `PATH` (node's folder named, since it comes from nvm), locale, `USER`, `TMPDIR`, `KY_*` identifiers, `SE_EPHE_PATH`, `KY_PY`; **no `DATABASE_URL`, no `KY_*_DATABASE_URL`**. The agent's shell does not source the operator's start-up files (`ZDOTDIR` points at a generated, empty start-up — the operator's `~/.zshrc` exports personal keys). The supervisor refuses to start if any secret variable is present in its own environment (secrets belong only to the executor's shell, §7).
- **`kalayantra_fleet.sh smoke` proves all of this with a real start** of the worker and the reviewer model under the exact lane environment: the profile loads, the login works, the models answer, the tools resolve, and no credential-like variable name reaches a command an agent runs. Preflight runs it; the launch does not proceed without `LANE SMOKE PASS` (first passed 2026-10-06 with `gpt-6-sol` and `gpt-6-astra`; `gpt-6.1-sol` is refused for this login and is not used).
- A cycle is a **fresh session**; continuity is the tracker's claim/resume record plus the item brief (§5), not the model's memory.
- Every cycle start is an **atomic reservation** (`run/CYCLE_STARTS.jsonl` under a lock) for every lane; the daily cap applies to the whole fleet (workers stop at 80 %, all lanes at 100 %); a quota or rate-limit marker **in the current cycle's log** backs the whole fleet off `KY_QUOTA_BACKOFF_S`; a lane whose cycle printed `IDLE-OK` waits `KY_IDLE_SLEEP` (10 minutes) before its next cycle — no paid minute-by-minute polling.
- `STOP_<lane>` is tested before `HOLD`; `down` writes STOP files and lets active cycles finish inside their cap (watchdogs preserved); `up` is idempotent. All of this was rehearsed on 2026-10-06 with `KY_DRY_RUN=1` (the supervisor runs every step but calls no model): one loop per lane after two `up` calls, cycles only for the three permitted lanes, HOLD stopping new cycles, `down` leaving no process.

### 3.3 Concurrency and pacing

- **Pool size is a file, not a default.** `run/KY_WORKERS` absent or 0 = no implementation worker (the state from kickoff to B-7); SŪTRADHĀRA writes 1 at launch acceptance, raises it after the first earned progress (B-8) when READY ≥ 4 and the verification backlog is ≤ 2 heads per verifier, up to 6; lowers it after a backoff or when the backlog exceeds that bound (workers then do permitted fixes and evidence completion, not new claims). `run/KY_VERIFIERS` is 1 until atomic claims are installed (B-2), then 2.
- Merge queue: at most 5 entries, one merge at a time, CI 9–13 min on `main` → plan on **3–5 PRs/hour**; the 37 inherited PRs alone are 7–12 hours of landing capacity, spread across phases. SŪTRADHĀRA queues only verdict-accepted, dependency-ready, deploy-compatible heads and reserves capacity for the next J or critical-path dependency.
- One production build or deploy at a time across campaigns (`CAMPAIGN_COORDINATION.md` lease; §13); the executor runs one production operation at a time and read-only readbacks in parallel beside it.

## §4 · Work — the plan model and the control plane

### 4.1 Control plane

A second instance of the Pravāha tracker (same package, different home, model, port and HOLD) serves `00_ARCHITECTURE/control/kalayantra/plan_model.json`:

```
PRAVAHA_HOME=/Users/Dev/kalayantra   PRAVAHA_EVENTS=/Users/Dev/kalayantra/run/EVENTS.jsonl
PRAVAHA_PLAN_MODEL=/Users/Dev/kalayantra/wt/campaign/00_ARCHITECTURE/control/kalayantra/plan_model.json
PRAVAHA_TRACKER_PORT=8767   PRAVAHA_REPO=/Users/Dev/kalayantra/wt/campaign
PRAVAHA_PGENV=/Users/Dev/.config/pravaha/pgenv.sh   PRAVAHA_HOLD=/Users/Dev/kalayantra/HOLD   (B-1b adds the HOLD knob)
```

The tracker and the `ky` CLI run from a **snapshot** of the selected package (`/Users/Dev/kalayantra/tracker_live`, taken by `fleet/install_tracker.sh --gov <dir>`), so B-1b can be developed in the working tree without breaking the running control plane. The package was never in git: B-1a lands the copy (taken from Pravāha's worktree, byte-identical, its 29 tests passing) on the bootstrap branch.

**B-1b is a control-plane work package, not a stream-name patch.** It adds, behind the model's declarations so Pravāha's behaviour is identical:

| Capability | Why | Acceptance case (local fixtures, `pravaha_tracker/tests/test_kalayantra_control_plane.py`) |
|---|---|---|
| message parties and actors from the plan model (`send --to <stream>`, `send --as <stream>`), stream-to-stream policy declared in the model | V must message K; S must message V | `send --as V --to K` accepted; the Pravāha model still rejects stream-to-stream |
| `PRAVAHA_HOLD` path from the environment; preflight accepts a detached lane worktree that holds no claim | the fleet's HOLD is `$KY_ROOT/HOLD`; lanes rest at `origin/main` between items | preflight sees the configured HOLD; a detached lane without a claim passes |
| **`claim <ID> --worker <lane> --lease <s>`**: under an exclusive lock on the event log, recompute status from events; refuse unless READY and no unexpired claim by another worker; issue `claim_id`; `renew`, `release`; expired claims recover with a recorded hand-over preserving branch, head and step; `run/claims/<worker>.json` | two K workers today both succeed on `start` | two simultaneous claims → exactly one winner; a stale snapshot cannot claim; a stopped worker's claim recovers without losing its branch |
| **verdict events** (`verdict <ID> --head <sha> --result ACCEPTED|REJECTED [--phase post_deploy] --detail`) from stream `V`, never from the item's author lane; a later push to the PR head invalidates the verdict | review must bind to the exact head | changed head → verdict stale |
| **guarded completion with typed evidence**: a code item needs an independent ACCEPTED verdict on the exact PR head and the recorded merge result mapping that head to the squash commit (a post-deploy verdict binds the deployed merge commit); an artifact or operational item needs its typed artifact digest or operation/request identity, its declared evidence, completed steps, eligible dependencies and independent acceptance — never a fictional Git head; S invokes the guarded `done` for N- and V-owned items after their independent acceptance; a join completes from its children; a packet item consumes the independent reviewer's verdict and the review's sha256 (parsed fields, not a pattern); detector matches are necessary evidence inputs, never sufficient; a recorded `done` is durable | today a merge detector or a long file completes an item regardless of review | REJECTED + merged → not done; a rejecting review file → packet not unlocked; a flapping detector does not un-do |
| **structured decisions and skip propagation**: `decide --outcome approved|refused|deferred|insufficient_evidence`; `approved` and `refused` are **final**, the other two leave the decision **open** (dependants wait; it is re-decided when evidence or capability changes, and never becomes terminal by time passing); dependants declare `requires_outcome`; a dependant whose required decision is final at another outcome becomes **`not_applicable`**; **an executable consumer of a `not_applicable` dependency also becomes `not_applicable`** (it would be working without its input); only items declaring `accepts_not_applicable_dependencies` — joins, independent reviews, certification and disposition reports, close reports — become READY from skipped dependencies, and their acceptance enumerates the gaps; a mandatory item that ends `not_applicable` is a declared campaign gap | refused ≠ approved; a failed gate must neither stall the close nor let work start without its input | refused D-FLIP skips the live readback and the full rebuild and forces a partial close; refused D-G2 → K5-3 skipped, V-K5 ready; deferred D-TEARDOWN → J-2a keeps waiting |
| per-worker heartbeat; **`audit --since <ts|kickoff>`** (duplicate claims, expired workers, rejected-but-done, unmet dependencies, unbound production operations, zero earned progress in a non-blocked interval; lists mandatory items that ended `not_applicable`) | the next-morning check | the audit fails on each planted defect |
| `reopen` / `unblock` as explicit owner-authorised transitions | a note never changes state | a note does not unblock |

Until B-1 lands and B-7 accepts, **no K worker runs** (`run/KY_WORKERS` is 0) and one verifier runs; S, N and V bootstrap work uses single-actor streams where contention cannot arise.

**Pre-B-2 bootstrap protocol — overrides §5 and the role prompts until B-2 is done.** Only S, N and v1 act. Check `/Users/Dev/kalayantra/HOLD` and `run/STOP_$KY_LANE` directly; look at the tracker's health and your worktree directly. **Do not call** `ky preflight` (it fails in a detached worktree), `claim`, `renew`, `audit`, `verdict`, `unblock`, `decide --outcome`, or `send` between the campaign's streams — the unmodified tracker has none of them. Use only `ky status`, `ky next`, `ky start`, `ky step`, `ky review`, `ky note`, `ky report`, `ky heartbeat` and `kybrief`. No campaign decision is due before B-2.

S is the only writer of the bootstrap branch; N writes only its B-5 branch. **Hand-offs are files, not messages.** An author asks for a review by writing `run/bootstrap/<ID>.request.json` = `{"item", "branch", "head", "checks"}`; v1 looks for these each cycle and answers with `run/bootstrap/<ID>.verdict.json` = `{"item", "branch", "head", "result": "ACCEPTED"|"REJECTED", "commands", "evidence_sha256", "by", "ts"}` (plus a copy named `<ID>.<head>.verdict.json`). A changed head needs a new verdict. A state the old tracker shows as DONE because a detector matched is **advisory** during bootstrap and never authorises a merge. S queues the bootstrap PR only when B-4, B-3b and B-5 are each evidenced and v1 has accepted the final integrated head. B-2 installs the merged package, validates its receipt and audit, and imports the bootstrap receipts through the new guarded completion. Only then do the ordinary commands apply and the second verifier start.

Streams: `S`, `N` (uses `--as steward` for Pravāha decisions and model edits), `V` (lanes `v1`, `v2`), `K` (lanes `k1`…`k6`). Stream K routes; a **worker owns a claim**.

### 4.2 Item ownership, review and completion

```
ky preflight                                        # tracker live, in your worktree, HOLD off
ky next                                             # READY items for your stream; never a WAITING item
kybrief <ID>                                        # the item's whole specification
ky claim <ID> --worker $KY_LANE --lease 5400        # atomic; refused if another worker holds it; renew every ≤ 30 min
ky step <ID> <step> --evidence "<commit|file|test>" # per declared step; a step never completes the parent
ky review <ID> --detail "PR #n @ <sha>"             # the PR exists; auto-merge is NOT enabled by the worker
   → PARĪKṢAKA: ky verdict <ID> --head <sha> --result ACCEPTED|REJECTED --detail "<tests, oracles, mutations, readback>"
   → SŪTRADHĀRA queues an ACCEPTED head whose required CI is green, whose deploy-compatibility predicate holds, and (for production-adjacent deploys) whose lease covers it:  gh pr merge <n> --squash --auto
ky done <ID> --evidence "PR #n merged <sha>; verdict <id>"   # guarded: deps ∧ steps ∧ verdict@head ∧ detector; refused otherwise
ky block <ID> | ky park <ID> --detail "..."         # with the question, evidence and a recommendation; ADHIKĀRIN rules within one cycle
ky report --detail "NEW ITEM: ..."                   # ask the designated model writer for an item; `request` asks for a DECISION, not an item
```

Rules: branch `kalayantra/<item-id-lowercase>` from `origin/main` (one item, one branch, one PR); **never rebase or force-push a published branch** — merge `origin/main` into it, or open a replacement PR with a supersession note and keep the old branch; an item whose brief says "S splits" is split into children **before** claiming (the model already splits the known large ones); a first child's merge never completes the parent (parents are joins); PR ownership is the claim's registered PR number, never "PRs by the shared GitHub author"; a `done` without a verdict, or a verdict without the measured commands, is reverted by S and ruled on by N.

### 4.3 Dependency graph (what runs in parallel, what cannot)

```
B-0 ─┬→ B-4 ──────────────────────────────┐
     ├→ B-1a → B-1b → B-1c (V) ───────────┤
     ├→ B-5 (N, branch n-b5) ─────────────┼→ B-1p (PR open) → B-1v (V: verdict at the exact head) → B-1 (PR merged) ─┬→ B-2 (reinstall; wt/campaign follows main) ─┐
     └→ B-3b (local DBs, precheck) ───────┘                   └→ B-6 (executor answers from main) ──────────┼→ B-3 (launch preflight) → B-7 (launch acceptance) → B-8
B-2 → D-R5, D-R6, D-R8, D-R9, D-R11, D-KR (one batch)
B-7 → K0a-0, K0a-1, K8-R26, L0-M, L0-K, J-0                             — nothing of K, L or J is READY before B-7
K0a-1a ─┬→ K0a-2 ; K0a-1a → K0a-1c ; K0a-1b        (K0a-1 = join of 1a, 1b, 1c)
        └→ K0a-3a (∧ K0a-1b) → K0a-3b, K0a-3c       (K0a-3 = join of 3a, 3b, 3c) → K0a-4
K0a-2 ∧ K0a-4 ∧ K0a-0 → V-K0a ─┬→ K1-1a → K1-1b ─┐
                                         ├→ K2-1a → K2-1b ─┴→ K1-2 ─┐      K2-1b → K2-2 ─┴→ V-K12 → K3-1 → V-K3 → K4-1 → K4-2a → K4-2b → K4-3 → V-K4
                                         ├→ K7-1a → K7-1b → K7-2 → K7-3 → K7-4 (D-R6 approved ∧ K4-2b) → V-K7
                                         └→ KA-1, KA-2 → KA-3a (∧ J-0m) → KA-3b (D-R8 ∧ J-0m) ; KA-4 → KA-4b (∧ L0-M ∧ K7-1b) → V-KA
V-K4 ∧ K0a-2 ∧ KA-3a ∧ KA-3b → K5-G1a → K5-G1b (baseline frozen) → VC-1 → VC-2 → D-VC → V-VC → K5-2 → D-COMPACT → K5-2b (approved)
D-VC (approved) → D-G2 → K5-3 (approved)          every K5 child terminal → V-K5
V-K4 → K6-1, K6-2, K6-3 ; K5-G1b → K6-4 ; D-R11 ∧ V-K4 → K6-5a → K6-5 ; all five → V-K6
each V-<packet> ∧ K8-R26 → K8-<packet> (K8-KA also ∧ K7-4 ∧ J-5s: it carries the judge's own mapping) ; all eight → K8-REG
J-0 → J-0m → J-1a → D-TEARDOWN → J-2a (approved) → J-2b → J-2c → J-2d → J-3a, J-3b → J-3c → J-3d → D-G9
J-3d → J-4a → J-4b → J-4c → J-4d (∧ D-G9) → D-CLOUD → J-4e (approved) → J-4f → J-5q → J-5s
J-5s → K3-2 → V-K3b → K8-K3           J-5s → J-6a → J-6m → J-6r → D-FLIP → J-6 (approved) → J-6l → V-J6 → J-7a
J-6l ∧ L0-K → D-T2 → J-7 (approved, optional) ; J-6l → J-7b ; J-7a ∧ J-7 ∧ J-7b → J-8a → J-8
(V-K6 ∧ V-K5 ∧ V-K7 ∧ V-KA ∧ K8-REG ∧ V-K3b) → K9-1 → K9-2, K9-3 → K9-4a (∧ J-6l, D-FLIP approved) → K9-4b → K9-6 → KR-1, KR-2 (D-KR) → K9-5 (census after the contract phase) → V-K9
JOIN-ALL (every other item terminal) → C-1 → C-2 → C-3 (drain, external) → C-4 (v1's final review, then the physical shutdown receipt)
```

Parallel from the first hour after B-7: K0a ∥ J-0 ∥ L0. After V-K0a: K1 ∥ K2 ∥ K7 ∥ KA ∥ J ∥ L0. The critical path is K0a → K1/K2 → K3 → K4 → K5-G1 → VC → K6 → K9; J runs beside it and joins at K3-2, K9-1 and K9-4a. Optional items (`mandatory: false`): K5-2b, D-G2, K5-3, J-7. K7-4 and KR-2 are mandatory: their decisions may be refused, and that is then a declared gap.

### 4.4 Item schema

The model is **generated** (its generator's self-checks: unique ids, no unknown dependency, no cycle, every non-decision item has a detector, every item pins its specification, every `requires_outcome` decision is also a dependency, nothing of K, L or J can be READY before B-7, the coverage tables name only real items) and then checked by the tracker's own `check_model`. Fields beyond the tracker's own, which it tolerates: `join` (a parent completed by its children, without a detector), `accepts_not_applicable_dependencies` (the 28 joins, reviews and reports), `brief` (`spec` — the pinned sections; `owns`; `shared`; `tests` — oracles and the mutations that must fail; `migration`; `compat` — the deploy-compatibility predicate; `op` and `g8` for production items; `notes`), `requires_outcome` (`{"D-X": "approved"}`), `mandatory` (false for the four optional items: K5-2b, D-G2, K5-3, J-7), and at the top level `control_plane` (the declarations B-1b reads), `documents` (short names → paths) and `coverage` (each of the 21 algorithm cards, each asset and legacy module of plan §8, and each of the five definition-of-done lines → the items that deliver it). Detector types: `pr_merged`, `pr_ready`, `branch_merged`, `branch_file_contains`, `file_exists`, `file_contains`, `db_query` (read-only; the SQL must return **no rows on false**), `http_ok`. Packet exits are detected by a structured verdict file (`run/reviews/<PACKET>.VERDICT.json` with `"result": "ACCEPTED"`), never by a review file's size.

## §5 · The cycle contract (one invocation = one cycle = exit)

You run under a supervisor in print mode. You cannot ask anything and nothing will answer. When you finish this cycle you end your turn; the supervisor reinvokes you in about a minute until `HOLD` exists. Do not sleep, poll in a loop, or wait inside a session. **Long jobs run outside the cycle:** a cycle submits or inspects one operation and exits; the next cycle reads its state.

**Orientation set (read these; read nothing else unless the item brief names it):** this charter · your role prompt · `CLAUDE.md §N.2–§N.8` · `ky status`, `ky next`, your durable claim/resume record (`run/claims/<worker>.json`) · the item's `brief` (`kybrief <ID>`) and the plan-document sections it pins. The 16-item `CLAUDE.md §C` sequence is discharged for the campaign by the campaign-level SESSION_OPEN (B-4) and its CCD entry; the root `CLAUDECODE_BRIEF.md` belongs to another workstream and does not govern this fleet; lanes neither edit nor replace it. **Where the documents are:** always at `/Users/Dev/kalayantra/wt/campaign/` — on branch `campaign/kalayantra` until the bootstrap PR merges, a detached mirror of `origin/main` from B-2 on; lanes read them there by absolute path.

**Steps, in order:**

- **−1 STOP / HOLD.** `run/STOP_<lane>` → print `STOP`, exit. `HOLD` → print `HOLD`, exit.
- **0 Resume or sync.** If your claim record names an item: fetch `origin/main`, check out that branch, continue at the recorded step — do not create a new branch. Otherwise `git fetch origin main`; `ky preflight`.
- **1 PR hygiene — only your registered PRs.** Merge `origin/main` into a DIRTY branch (never rebase); RED → read the failing job, fix at root, push, `ky review` again (the previous verdict is stale by construction). Never start new work while an own PR rots.
- **2 One unit of the highest-priority work (20–45 min; hard cap 90).** `ky next` → `ky claim` → read the brief → do one resumable slice → `fleet/precheck.sh` + the brief's explicit tests and mutations → explicit-path commit → push → `gh pr create` (or update) → `ky review`. No auto-merge.
- **3 Persist and exit.** `ky renew`; `ky heartbeat --detail "CYCLE <n> <lane>: <did> → next: <what>"`; the tracker's claim record carries branch, head, step, next action. Print one summary line. Exit.

**IDLE cycles** (`ky next` empty, PRs clean): print `IDLE-OK (verified: <what>)` as the last line and exit — the supervisor then spaces that lane's next cycle by ten minutes. **Escalation:** decide-and-log if yours; else `ky block`/`ky park` with evidence and recommendation, take the next item. Nothing waits for a human.

## §6 · Worktrees, branches, PRs, CI/CD

**Layout** (`/Users/Dev/kalayantra`; never inside the Madhav main checkout or `madhav-l3/*`):

```
wt/campaign     branch campaign/kalayantra until the bootstrap PR merges, then a detached mirror of origin/main —
                documents, plan model, fleet; the tracker's PRAVAHA_REPO; nobody edits it after B-2
wt/sutradhara  wt/adhikarin  wt/v1  wt/v2  wt/k1 … wt/k6     detached at origin/main; one branch per claimed item
tracker_live/   the tracker package snapshot the tracker and `ky` run from      fleet_live/   the supervisor snapshot
exec/           the executor snapshot and its private per-operation checkouts
run/            EVENTS.jsonl · snapshot.json · claims/ · verdicts/ · reviews/ · tests/ · ops/{requests,inflight,receipts,done,acceptance,sql}
                · KY_WORKERS · KY_VERIFIERS · CYCLE_STARTS.jsonl · *.lock · STOP_<lane> · schema/ (local DB seed)
logs/           <lane>.<cycle>.log · <lane>.<cycle>.last.md · supervisor.log · executor.log
venv/  ephe/  bin/ky  bin/kybrief
```

Lane worktrees are created from the Madhav repository's object store (`git worktree add` reads and writes only the shared `.git/worktrees` metadata and never the main checkout's files or branches); the shared stash is never used (`git stash` is forbidden to lanes).

**Branches and PRs.** `kalayantra/<item-id>` from `origin/main`; PRs target `main` (an integration branch would run **zero** required CI under `ci.yml`'s allowlist and `tap-ci.yml` has a different allowlist; direct-to-main is acceptable only for **independently deploy-compatible slices**, which §8 rule 8 makes every item be). Required checks + merge queue (squash, ALLGREEN) are the automated gate; `required_approving_review_count` is 0; **the campaign's own review gate (verdict before queue) is stricter than the repository's**.

**CI/CD, concretely.** (1) `fleet/precheck.sh` is a **fast local check**, not the six required checks: tsc, vitest, migration-number guard, the secret scan as CI runs it (the project's rule set, without the local-only whole-history gitleaks pass that reports pre-existing findings CI never sees) plus gitleaks on the diff's own files, drift/schema **within CI's accepted baselines** (79 drift findings / 43 schema violations, exit 3 accepted), TAP-6, the governance tool tests only when the diff touches `platform/scripts/governance/` (the whole suite takes over half an hour locally; CI runs it in five shards), the item brief's explicit tests, and — for a migration — the real application to the lane database through `migrate.ts`. Required CI remains the merge gate. (2) One item, one PR; docs ride with the item; S batches ledger changes. (3) S queues (`gh pr merge --squash --auto`) only after verdict + CI + compatibility + lease. (4) Deploy is automatic after CI on `main`; for a migration-carrying PR the **post-deploy acceptance** (verify-migrations-deployed green + an executor `readback_sql` op) is a separate verdict before the item is done. (5) Writer changes regenerate the writer-digest / capability inventories **in the same PR** (CI checks provenance on every writer PR). (6) Protected migrations (the runner refuses them outside the protected window) land only inside J-4b's window. (7) **Tests that CI really runs.** The required Governance Gates job collects `platform/python-sidecar/tests/**` by discovery, so a database-free test under `tests/l3/<area>/` runs on every PR; a database-backed test is skipped there. Item K0a-0 adds one additive job that runs `tests/l3/kala_db/**` against a throwaway Postgres with a skip counted as a failure — one workflow edit, after which no item touches `ci.yml` again and parallel PRs never collide on it. SŪTRADHĀRA requires that job green before queueing.

## §7 · Environment, credentials, the executor, databases, ephemeris

**Two processes, two environments.** Both are started by the kickoff session (owner direction 2026-10-07: the launch is one pasted prompt). The executor is started in a child process that sources `executor.env`, so the connections never enter an agent's environment; after a restart of the computer the kickoff prompt is simply pasted again.

| Process | Shell environment | Holds |
|---|---|---|
| `fleet/kalayantra_fleet.sh up` | `~/.config/kalayantra/fleet.env` — **no secrets**; the script refuses to start if `DATABASE_URL`, `KY_BUILDER_DATABASE_URL`, `KY_OWNER_DATABASE_URL` or `PGPASSWORD` is set | lane loops |
| `fleet/executor.sh up` | `~/.config/kalayantra/executor.env` (chmod 600) — `KY_BUILDER_DATABASE_URL`, optional `KY_OWNER_DATABASE_URL`; `gcloud` auth; the read-only connection file | the production boundary |

**The executor** (`fleet/executor.py`, started by `fleet/executor.sh` from a snapshot of itself, one instance by a lock) watches `run/ops/requests/*.json`. **It trusts only what is merged to `main`:** the operations table (`fleet/executor_ops.json`) and a read-only operation's script are read from `origin/main`; a production operation runs in a private checkout of the request's `reviewed_commit`, which must be an ancestor of `origin/main`. Nothing an agent edits in a working tree can change what it runs. A request is typed JSON (`operation_id`, `kind`, `item_id`, `chart_id`, `generation`, `reviewed_commit`, `image_digest`, `lease_id`, `expires_at`, `idempotency_key`, `acceptance_receipt`, `args`, `requested_by`, `kyd`). The executor **validates**: the kind is listed and `enabled`; the requester is allowed for the kind (production kinds: `adhikarin` only; the read-only readbacks: `adhikarin`, `v1`, `v2`, `sutradhara`; `finalize` and the schema seed: `sutradhara`); the capability is present; argument keys are allowed and values carry no unsafe characters; and for a production kind — the canonical `chart_id`; a lease that is the **single unexpired ACTIVE row** of the shared lease table; the commit merged; and a pre-acceptance receipt under `run/ops/acceptance/` that is ACCEPTED by a verifier lane and **binds the complete request** (the sha256 of the request as sorted compact JSON without the `acceptance_receipt` field), is at most three hours old, precedes a timezone-qualified `expires_at`, attests `backup_taken`, `restore_verified` and — for a mutating run — `dry_run_passed`, and marks true every checklist row the kind's table entry requires. Authorisation is checked when the request is queued **and again immediately before execution**; a HOLD or a changed operation definition refuses it then. It **executes** the mapped command in its own process group (nothing outlives it) with an allow-listed environment plus, at most, the one connection the operation needs — neither privileged connection reaches a read-only child — and writes `run/ops/receipts/<operation_id>.json` (status, exit code, redacted tail) with the complete redacted output beside it (`<operation_id>.output.txt` and its sha256: evidence is the whole output, never the tail). Read-only operations run in parallel. **Production operations take a single slot, held by a fence file `run/ops/PRODUCTION_PENDING.json` that is retained after every production invocation** — success, failure or interruption — because a dispatch can return while its remote job still runs; ADHIKĀRIN removes it only after PARĪKṢAKA's quiescence receipt for that request. An operation in flight when the executor restarts is **never re-run**: its receipt reads `INTERRUPTED`, the fence stays, and the postconditions are read back. Agents read receipts; they never see the credential or an unredacted error.

Kinds: `readback_sql` (one SELECT/WITH statement from a file under `run/ops/sql/`, through a database driver — never the `psql` client, so no client command exists to abuse; the session is read-only and a second statement is refused), `migration_readback`, `local_schema_seed`, `finalize` — enabled from the bootstrap PR; `backup_snapshot`, `backup_restore_verify`, `smalltest_dispatch[_dryrun]`, `smalltest_teardown[_dryrun]`, `measuring_dispatch`, `verification_job`, `century_dispatch`, `publish_head`, `rollback_head` (the Gochara authority surface), `orchestrator_rebuild[_dryrun]`, `layer_verify`, `layer_publish`, `layer_rollback` (the whole-layer surface — a different one; neither substitutes for the other) — **disabled until the plan-model item named in `enabled_by` lands the reviewed script, arguments and required checklist rows** (J-1a, J-3a, J-4b, J-4d, J-6m, J-6r, K9-3). The executor writes `run/ops/CAPABILITIES.json` (presence only, never a value) at start and every 5 minutes; a missing capability refuses the dependent request with `capability_missing`, which makes that item wait — nothing else.

**Local rehearsal databases.** The seed is a read-only `pg_dump --schema-only` of production plus the applied-migrations ledger, taken by the operator or by the executor (`local_schema_seed`) — never by a lane, since it reads the production connection settings. `local_db.sh db <lane>` creates `ky_<lane>` from the seed and runs the project's own `platform/scripts/migrate.ts` for pending migrations, or **re-validates** an existing database; either way it answers READY or FAILED from assertions run in that invocation (≥ 400 tables, ≥ 70 `kala_*`/`ka_gochara*` tables, runner exit 0, ledger ≥ 900 rows, and **no restore error other than the nine expected ones** from the four planner tables the dump cannot include) and writes a receipt `run/local_db/<lane>.json` bound to the seed's hash — never just "exists". All ten lane databases were rebuilt and read READY on 2026-10-06 (436 tables, 73 Kāla tables, ledger 949, zero unexpected restore errors). A fresh database cannot be built from the migrations alone (production predates the squash). The container `ky-pg` is reused only when its image and its `campaign=kalayantra` label match.

**Ephemeris.** `SE_EPHE_PATH=/Users/Dev/kalayantra/ephe`, three `.se1` files from `https://storage.googleapis.com/madhav-ephemeris/se1/` verified against `ephemeris_pins.py` by preflight. **Python**: shared venv `/Users/Dev/kalayantra/venv` (`KY_PY`). **Node**: `platform/`, `platform-mcp/` node_modules per worktree (installed in all eleven worktrees on 2026-10-06; a lane that changes a lockfile runs `npm ci` again).

## §8 · Governance — the minimum, and what is explicitly not done

**The nine rules. Nothing else applies to this campaign's day-to-day.**

1. **Frozen contracts.** `WriterBase`; Gochara spec v1.4 + the delegated rulings of 2026-10-02; the Kṣetra rulings (B8-6 verbatim); N-32; `NR-KALA-R13/R12/R2`. A packet that "needs" a change stops and ADHIKĀRIN rules — almost always "design around it".
2. **Idempotent, additive, verified.** §N.3 replace-then-insert scoped to `(chart × generation × grain)`; migrations additive, numbered by the guard (`npm run migration:next`), applied to the lane database before push, verified applied in production after deploy, never edited once applied (§N.4). Immutable records are never deleted to satisfy a detector.
3. **Earned signals.** `done` is the guarded conjunction (§4.2). A status with no detector and no verdict is `unmeasured`. Nobody verifies their own work.
4. **Production discipline.** Every production operation is an executor request under G8: lease held, backup exists and its restore verified, dry run passed, one build slot, PARĪKṢAKA's pre-acceptance receipt; postconditions read back after completion (never from an exit code). Production SQL writes happen only through the orchestrator, a migration, or the closed executor set.
5. **No credential handling by agents.** Agents never read, source, print, log or commit a credential; `pgenv.sh` is sourced only by the tracker (launchd) and the executor; readbacks are executor `readback_sql` ops.
6. **One campaign-level handshake.** SŪTRADHĀRA writes the SESSION_OPEN as a YAML `session_open:` mapping with every field the validator requires (`tool: Codex`, `tool_profile: madhav-parity` — the posture, applied through the generated `kalayantra` overlay and recorded so in the CCD entry — a live lease id verified on `origin/campaign-coordination`, the cross-cutting register read, fingerprint check rows with no `match: false`, enumerated `may_touch`/`must_not_touch` without brace globs, `red_team_due: false`) and records the campaign-level exception as a CCD entry before any state-changing campaign work; SESSION_CLOSE likewise at C-2.
7. **No history rewrite, no writes to `main` outside the merge queue, no disabling of a check, no fabricated row, floor, measurement, verdict or heartbeat** (Nirmāṇa H1–H8).
8. **Deploy compatibility (expand/contract).** Every merge deploys. An item that changes a writer's or reader's semantics ships with a compatibility predicate in its brief: live readers keep working on the published head until K9-4 publishes the new generation (additive columns/tables, candidate/published separation, a shim for a deleted mode, a versioned reader); PARĪKṢAKA's verdict checks the predicate; a PR that would break the live product before its replacement exists is REJECTED.
9. **Shared-surface coordination** (`CAMPAIGN_COORDINATION.md` on branch `campaign-coordination`). Lease (§1) before a production mutation this campaign performs; migration numbers from the guard and claimed in §2 at PR open, never renumbering another campaign's; the §3a partition with Pūrṇa Anveṣaṇa respected (never `retrieval/registry/knowledge/**`, `purna/**`, `planner_*`/`inquiry_*` tables; generated artifacts only through their generators; requests as `PA-REQ-nn`); only L3 entries of the declarations file and `ka_*` rows of `asset_registry` (L0–L2 are Suvarṇa's); no touching another campaign's branches, worktrees, PRs, trackers or ledgers.

10. **The control plane is finished (owner rule, 2026-10-07).** After B-7 no lane edits, wraps or replaces the fleet scripts, the tracker package, `$KY_ROOT/bin`, `fleet_live` or `tracker_live` in a cycle, and no lane invents a mode, guard or control subsystem. A fleet or tracker defect is filed once as a `NEW ITEM` and fixed by a builder through an ordinary PR. The supervisor refuses to start a cycle while a tool wrapper sits in `$KY_ROOT/bin`. Budgets are counted apart: builders 600 starts a day, control lanes 300, with control lanes paced at five minutes.

**Explicitly not done:** decision packets to the native; DISAGREEMENT_REGISTER entries (ADHIKĀRIN's ledger is the record); per-PR Astra reviews (packet-exit only, §10); red-team cadences; per-lane handshakes; the 16-item reading per cycle; waiting for anyone.

## §9 · The owner surrogate

Full charter: `KALAYANTRA_OWNER_SURROGATE_CHARTER_v1_0.md` (v1.1). In one table:

### 9.1 Decides, records in `run/DECISIONS.jsonl` before acting

R-5 / R-6 / R-8 / R-9 / R-11 (defaults = the recorded recommendations) · `D-VC` from the frozen rubric as judge · `D-G2`, `D-COMPACT` · `D-TEARDOWN` (a real teardown path or a block — never retention) · the absorbed `D-G9`, `D-CLOUD`, `D-T2`, `D-FLIP` and every steward hold, **under the unchanged evidence gates** · production operation requests under G8 · inter-lane disputes · execution-mechanics repairs within the fixed mission, evidence gates, scope and budget (G12).

### 9.2 Decides nothing already decided

The plan documents and `NR-KALA-R13/R12/R2` are not reopened; defects are ruled on evidence with `supersedes` named.

### 9.3 Reserved to the human — three things, none a gate

(a) Credentials and IAM: minting, rotating, exporting, broadening. (b) Raising the spend ceiling or the worker ceiling (6). (c) The `HOLD` switch. Everything else is ADHIKĀRIN's — including amending this charter's **operational** sections by a recorded KYD entry (not the mission, the evidence gates, the scope or the budget).

## §10 · Verification and review gates (PARĪKṢAKA)

- **Item verdicts.** Check out the registered PR's exact head in your worktree; run `precheck.sh` and the brief's tests and mutation oracles (an item without a mutation that fails is a finding); read the diff against the pinned plan sections and `NR-KALA-R13`; check the deploy-compatibility predicate; for a migration, confirm additive + guard-numbered + applied to `ky_<lane>`; then `ky verdict <ID> --head <sha> --result ACCEPTED|REJECTED --detail "<commands and outputs>"` and write `run/verdicts/<ID>.<sha>.md`. A changed head needs a new verdict. Post-deploy acceptance (migration applied in production, deploy green — read through a `migration_readback` request the verifier writes itself) is a **second** verdict on the same item before `done`.
- **Packet-exit reviews** (the `V-*` items: K0A, K12, K7, KA, K3, K3B, K4, VC, K5, K6, J6, K9): write the review packet at an absolute path under `run/reviews/`, run Astra (`codex exec -p kalayantra -s read-only -m gpt-6-astra -c model_reasoning_effort="xhigh"`), read the review, and write the **structured verdict file** `run/reviews/<PACKET>.VERDICT.json` — `ACCEPTED` only when the review's verdict is LAUNCH/ACCEPT and every BLOCKING finding is resolved by a merged item or validly dispositioned by ADHIKĀRIN; file each open BLOCKING finding with `ky report --detail "NEW ITEM: …"`. The verdict file is the detector; a review file's existence or size is not acceptance.
- **Production gates.** Before an operation: the pre-acceptance receipt (the checklist's readback rows TRUE, backup **and restore** evidence present, lease live, the `reviewed_commit` named) written to `run/ops/acceptance/<operation_id>.json`; after: the postcondition readback through an executor `readback_sql` request, read from `build_runs` / `build_run_assets` / `asset_throughput` / the manifest for the recorded run id — never from an exit status.
- **Bootstrap and close.** B-1c (the control plane's acceptance cases, each shown to fail without its guard), the launch verdict for B-7, and C-4 — the final acceptance of the five lines, performed by lane `v1` after the finalizer's receipt, ending with the one message to the native and `v1` stopping itself.

## §11 · Throughput and spend

Cycle cap 90 min; unit 20–45 min; one unit per cycle. **Atomic start reservations** for every lane in `run/CYCLE_STARTS.jsonl`; `KY_MAX_CYCLES_PER_DAY` (default 400) applies to the whole fleet; at 80 % the supervisor stops starting worker cycles and keeps S/N/V. Quota/rate-limit markers in the **current** cycle log set a fleet backoff (`KY_QUOTA_BACKOFF_S`, default 1800); the fleet never switches models or retries in a tight loop. Costs are measured (wall time per cycle; tokens where `--json` reports them) and summarised in S's digest.

## §12 · Stop, hold, recovery, finalisation

`touch /Users/Dev/kalayantra/HOLD` pauses every lane at its next boundary and makes the executor refuse to start an operation; `run/STOP_<lane>` stops one lane; `fleet/kalayantra_fleet.sh down` writes STOP files and lets active cycles finish inside their cap. A killed cycle loses at most one unit; the claim record resumes it. The tracker restarts under launchd; the event log is the truth. After a restart of the computer the operator starts the executor and the fleet again (two commands; nothing is lost).

**Finalisation has two phases** (`fleet/finalize.sh`, run by the executor on SŪTRADHĀRA's `finalize` request after C-2 is done and the close PR merged). **Drain (C-3):** every lane except `v1` is stopped, their locks are proven released, only clean worktrees are removed, and `run/DRAIN_RECEIPT.json` is written; a timeout, a busy lane, a dirty worktree or a failed removal is a **failed** drain, never an accepted receipt, and nothing further is removed. **Final (C-4):** lane `v1` reviews the five lines against the drain and close evidence, writes `run/reviews/FINAL_REVIEW.json` and `run/FINAL_MESSAGE_DRAFT.md`, then stops itself — it does not claim the shutdown line MET while it is still running. The finalizer waits for `v1`'s lock to release, removes its clean worktree, verifies all ten lanes stopped and all ten worktrees gone, and only then writes `run/FINAL_RECEIPT.json` and `run/FINAL_MESSAGE.md` (the reviewed draft plus the measured shutdown facts). Branches, evidence and the campaign checkout remain. Agents never remove a worktree.

## §13 · Coexistence with the other campaigns

`NIRMANA_HOLD` stays; Nirmāṇa, Suvarṇa, Pūrṇa-Anveṣaṇa and Paripraśna branches, worktrees, PRs, trackers and ledgers are not touched. **Agreed with the Suvarṇa campaign on 2026-10-06** (recorded in the plan model's `coordination` block): the judge's final build (J-4a) waits for Suvarṇa's line `L1_SETTLED v1 …` on the coordination branch and pins the build ids it carries (the daśā build must stay 75524b3e; any L1 rebuild of the canonical chart between the final build and the layer publication stales the seal and goes to ADHIKĀRIN); Suvarṇa gives a day's notice before any later L1 rebuild; `bg_parihara_rules` is pinned at 60 rows, so L0-M coordinates one reseal; the KP Reader ingestion has no collision. Further: the lease on `campaign-coordination` is taken for production builds/deploys this campaign needs verified and released after; migration numbers come from the guard; the Docker container `ky-pg` is validated by image and label before reuse; launchd label `com.madhav.kalayantra.tracker`, port 8767.

## §14 · Close

`JOIN-ALL` (every other item terminal — done, or `not_applicable` with its reason; the mandatory items that ended `not_applicable` are the campaign's gaps) → C-1 close report (each of the five lines **MET or NOT MET** with its evidence; status `CLOSED` only when all five are MET, otherwise `CLOSED-PARTIAL`; decisions ledger; gaps; measured costs; lessons) → C-2 SESSION_CLOSE validated, `SESSION_LOG` entry, `CURRENT_STATE §2`, CCD closure row, one merged PR → C-3 the drain receipt → C-4 `v1`'s final review of the five lines against their evidence, then the physical shutdown receipt. The final act is one message to the native (`run/FINAL_MESSAGE.md`): the close report path, the five lines with evidence, the gaps, and the measured shutdown.

## §15 · Residual risks, stated

1. **Same-account access.** Agents run as the operator's Unix user with full disk access (the `madhav-parity` posture). The deterministic leaks are closed and tested by the lane smoke (allow-listed environment; no personal MCP server or plugin; a shell that does not source the operator's start-up files; the executor boundary); prose forbids reading `pgenv.sh` or other campaigns' worktrees, but prose is not a boundary. Hardening the fleet into a separate account or container is available (`fleet/README.md`, `KY_ISOLATED_USER`) and requires the operator to create it; the campaign runs without it and says so.
2. **Deploy on merge.** Any merge that triggers a production deployment is production-adjacent, including an ordinary runtime or migration PR (the shared file's prime rule: one campaign deploys or builds at a time). SŪTRADHĀRA holds an unexpired shared lease from queue admission through deployment and the required readback; it takes one lease per **merge window** (a bounded expiry, the PRs it will queue named in the purpose), not one per PR, and queues nothing runtime while another campaign's lease is live. A documentation-only PR is exempt only when its deployment is demonstrably skipped. Compatibility acceptance and lease ownership are separate requirements. The cost is real: the campaign's merges share one production lane with every other campaign.
3. **Weak scores are recorded, not hidden.** The Gochara evaluation no longer gates the flip (native direction 2026-10-07); its results are published in J-5q as the tuning baseline. `D-VC` can still honestly read `fail` / `insufficient_evidence` for the replacement-model question; the campaign then completes everything else and reports it.
8. **Suvarṇa will revisit Kāla.** The certification run may change Kāla code. K0-SV obtains Suvarṇa's per-asset elevation template and the daśā-table contract first, so that the likely change is elevation, not rewrite.
4. **External prerequisites** (Suvarṇa's SETTLED-1 single-build state for J-4a; a sealer/verifier principal provisioned in production) have detectors and block only their dependants.
5. **Bootstrap comes first.** No implementation worker runs until the control plane is generalised, reviewed, merged and accepted (B-1b … B-7) — several hours in which only the conductor, the surrogate and one verifier work. That is the price of exclusive claims and review-before-merge; it is paid once.
6. **Two processes are the operator's.** The executor (it holds the credentials) and the fleet supervisor are started by the operator and must be started again after a restart of the computer. Without a builder credential the production items wait; without the owner credential the small tests wait; nothing else does.
7. **J-lane detail is discovered, not assumed.** The J phase joins are filled with PR-sized children only after J-0's inventory of the 37 open PRs and the remaining Pravāha items (J-0m); several executor operations are disabled until the items that land their reviewed scripts.
