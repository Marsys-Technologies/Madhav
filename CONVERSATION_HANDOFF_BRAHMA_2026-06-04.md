---
artifact: CONVERSATION_HANDOFF_BRAHMA_2026-06-04.md
canonical_id: CONVERSATION_HANDOFF_BRAHMA
version: 1.0
status: CURRENT — context bridge for a fresh session (new account, same Madhav folder)
project_codename: Brahma
authored_by: Claude (Cowork) 2026-06-04
purpose: >
  Carry the FULL context + deep judgment of a long, meaningful working session into a new conversation.
  Read this first, then the canonical docs in §7. It captures where we are, how we got here, what was
  decided and WHY, how we work together, and exactly what's next.
---

# Brahma — Conversation Handoff (read me first)

## §1 — How to use this
You are continuing a major piece of work on the **Madhav** folder (`/Users/Dev/Vibe-Coding/Apps/Madhav`).
Read this whole file, then the canonical docs in §7 in order. The native (Abhisek Mohanty) has been driving
this with a Cowork (planning) Claude + an Antigravity/Claude-Code (executor) Claude. You are picking up the
Cowork role. The tone has been: honest architect — celebrate real wins, but flag depth/grounding gaps
plainly, because that's where this project's value lives.

## §2 — The project, in one paragraph
**MARSYS-JIS**, codename **Project Brahma**, is an LLM-operated Jyotish (Vedic astrology) *research instrument*
for the native, Abhisek Mohanty (born **1984-02-05, 10:43 IST, Bhubaneswar, Odisha**). It reads a birth chart
with acharya-grade depth, surfaces cross-system patterns, and makes calibrated, falsifiable, time-indexed
predictions testable against lived events. It is **not** a fortune-telling product — outputs are probabilistic,
cited, auditable. Internal tool for the native + family (~10 users), cost-optimized GCP.

## §3 — The journey of this session (the meaningful arc)
This session re-architected and rebuilt the entire system from a clean slate:
1. **Re-architecture** — designed a clean **six-layer stack** (L0→L5), folding in two external reviews + four
   new assets + a robustness spine. Authored `MARSYS_MASTER_ARCHITECTURE v2.1`.
2. **Product + naming** — recast the product as **account management** (a chart = an account; build/consume at
   will) with a **Sanskrit lexicon** shown externally (never "L0–L5"): **Brahmagyan · Gaṇita · Bodha · Kāla ·
   Phala · Mīmāṃsā**. Designed the build-as-you-go **Layer Tower** cockpit UX.
3. **Infra** — reconciled the GCP footprint (realign, not rebuild), then **provisioned a cost-optimized
   baseline** (~$210–310/mo → ~$30–60/mo): scale-to-zero, dropped Memorystore + Cloud Tasks + the Load
   Balancer (→ **Firebase Hosting** front at `madhav.marsys.in`, because Cloud Run domain-mapping isn't
   available in asia-south1), right-sized Cloud SQL. Fixed a real RLS login-breaker along the way.
4. **Legacy teardown** — PR #187 wiped the legacy data/build-code/tools; kept the serve shells + LEL.
5. **Autonomous build** — defined **Autonomous Mode** (no human at any gate; bounded auto-fix→park; safety
   rails; budget $5k run/$300 asset) and a self-chaining driver, then **the swarm built the whole six-layer
   instrument overnight** — Brahmagyan→Mīmāṃsā, fixing its own failures, merging on green, deploying.
6. **The honest reckoning** — "complete" meant complete *plumbing*, not data. The instrument was built but
   **empty**; "green" assets had passed code-review, not real-data verification. 3 foundational assets parked.
7. **Runtime-Guardian Mode** — re-pointed the swarm to guard a **live build through the real portal** (form →
   L0→L5), fixing UI/workflow/execution/deploy defects in real time. It found + fixed the missing **build
   executor** (the Cloud Run Job that runs the writers), fixed two gate bugs, re-based the cockpit, and **ran
   a real build that landed real data**.

## §4 — Where we are RIGHT NOW (2026-06-04)
**The instrument is LIVE with thin data.** The Build button on `madhav.marsys.in` fires a real Cloud Run Job
(`brahma-build-pipeline-job`) that runs L0→L5 and persists real rows. **Verified against the native's chart:**
positions from Swiss Ephemeris (correct), and the dasha — **current Mahā/Antar/Pratyantar = Mercury / Saturn /
Sun (2026-05-10 → 2026-06-28)**.

But four things are open (the native's own observations, all correct):
- **Data is thin, not full depth.** Counts are a first slice (e.g. 9 positions = 1 ayanamsha not 5 + no
  upagrahas; 819 dashas = MD/AD/PD not Sukshma depth; 21 graph edges vs a legacy benchmark of ~573 signals; 9
  anchors). Root cause: **volume-floor gates passed thin data green** instead of flagging amber.
- **Portal not yet drivable/visible by the native** — no dashboard Open/Resume links, cockpit errors, no
  per-asset visibility (Asset Inspector).
- **Legacy residue is polluting signals** — the teardown left legacy *data* (FORENSIC v8.0, MSR v5.0, Phase-4C
  panchanga) live in production; tools were citing it. The native wants it **fully wiped (no backup)**, plus
  legacy rules in the deploy/CI pipeline purged.
- **The Rule Base (BG-0-6) is genuinely parked** — the BPHS extraction failed its quality bar. It's the
  knowledge layer that grounds all signals; until it's real, L2+ signals are ungrounded. **Native-led rework.**

## §5 — The load-bearing decisions + philosophy (the WHY)
- **Plumbing-first, data-second.** Build the complete end-to-end structure, accept imperfect first-pass data,
  then a focused data-correctness pass. (The native's deliberate strategy; it paid off — a complete diagnosable
  instrument + a precise punch-list.)
- **Full autonomy with automated rails (not human tripwires).** The swarm self-decides every gate incl.
  prod/destructive; safety = backup-before-destructive (where used) + verify-before-promote + bounded retries +
  budget — not human approval. (Native explicitly chose zero human gates.)
- **The hard lesson on autonomy:** the swarm is *excellent at mechanical/parallel/structural* work but
  *green-stamps depth + judgment* (thin data, ungrounded signals, gate bugs that asserted FORENSIC parity). So
  the calibration going forward: **swarm for the mechanical bulk; humans on the gates and the judgment.**
- **No Anthropic models in any production path.** Gemini primary, DeepSeek fallback.
- **PyJHora is the engine, source-of-truth by construction.** **FORENSIC v8.0 is a coverage benchmark, NOT a
  value/date oracle** — gates must verify astronomy vs Swiss/JPL, never FORENSIC parity. (Two parked assets
  were just gate bugs asserting FORENSIC parity; the engine was right.)
- **LEL stays isolated** (pure-event log, never feeds generation). LEL = 57 events; source of truth is
  `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (NOT the wiped DB) + `LIFE_EVENT_LOG_FACTS_ONLY_v1_0.md`.
- **Cowork plans; Antigravity (Claude Code) executes.** Cowork authors specs/briefs/prompts; the executor runs
  them with GCP creds + browser automation. The native pastes prompts to the executor.

## §6 — The forward plan (Completion — Pass 3)
Full detail in `BRAHMA_COMPLETION_PLAN_v1_0.md`. Four workstreams, in order:
- **WS-0 · Legacy Residue Purge (do first).** Full wipe, **no backup**, three surfaces: production+localhost DB
  data, code, and the **deploy/CI pipeline** legacy rules (legacy layer-dir copies `025_/035_`, R9/R10/R11
  flags, legacy gates). Keep Brahma (`brahmagyan_/ganita_/bodha_/kala_/phala_/mimamsa_`) + shell (`profiles,
  charts, conversations, life_events`). The native approved the purge; the wipe-list is the only safety net
  (no backup). Prompt is staged in the last message of the prior conversation.
- **WS-1 · Make the portal drivable + visible.** Dashboard Open/Resume links, cockpit error fix + `build_events`
  SSE live rail, the **Asset Inspector** (per-asset data/counts/provenance/gate), Brahma states (green/amber/
  parked). Swarm-built but **tightly human-reviewed per surface** (use Claude Code front-end plugins).
- **WS-2 · Fully build the assets (the priority).** Per-asset, generate complete data gated on **honest volume
  floors** (real expected counts, no green-on-thin). Swarm-driven + native spot-checks via the Asset Inspector.
- **WS-3 · Rule Base + grounding (the soul, native-led).** Rework BG-0-6 (extraction method + confidence rubric
  + quality bar), then re-ground every signal and re-verify upward. Human-led, swarm as a tool. Then red-team.

## §7 — Canonical documents to read (in order), all in `00_ARCHITECTURE/`
1. `MARSYS_MASTER_ARCHITECTURE_v2_0.md` (v2.1) — the architecture + Project Brahma decisions (§A0).
2. `BUILD_WORKFLOW_AND_TOOLING_DESIGN_v2_0.md` — product/build experience + three-tier tool taxonomy.
3. `BRAHMA_BUILD_UX_SPEC_v1_0.md` — the Layer Tower cockpit UI/UX (WS-1 builds to this).
4. `BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md` + `BUILD_GUARANTOR_AUTONOMOUS_MODE_v1_0.md` +
   `RUNTIME_GUARDIAN_MODE_v1_0.md` — the swarm + how it operates.
5. `CONTRACT_REGISTRY_SEED_BRIEF_v1_0.md` + `CONDUCTOR/brahma/L0_CONTRACT_REGISTRY_SEED_v1_0.md` +
   `CONDUCTOR/brahma/BRAHMA_L1_L5_REGISTRY_SEED_v1_0.md` — the plan the swarm built from.
6. `LAYER_0..LAYER_5` design docs — the per-asset depth specs (what "full" means for WS-2).
7. `DATA_CORRECTNESS_BACKLOG_v1_0.md` (v1.1) — the pass-2 punch-list (parked assets, gate relaxations, CI
   exclusions, runtime-guardian findings §H).
8. `BRAHMA_COMPLETION_PLAN_v1_0.md` — the forward plan (WS-0→WS-3).
9. `INFRA_RECONCILIATION_v1_0.md` + `INFRA_COST_COMPARISON_BRAHMA_v1_0.md` + the provisioning brief — infra state.
10. Engine truth: `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (57 LEL events) + `LIFE_EVENT_LOG_FACTS_ONLY_v1_0.md`.
Note: `CLAUDE.md` / `CURRENT_STATE` carry pre-Brahma governance history — useful background, but THIS handoff +
the Brahma docs above are the live truth.

## §8 — Immediate next actions (the open prompts)
1. **Run WS-0 (Legacy Residue Purge)** — the staged prompt: audit → re-point tools → present wipe list →
   full wipe (no backup) across DB + code + deploy/CI pipeline → verify zero legacy citations.
2. **Then WS-1** — the portal (drivable + visible), so the native can run + inspect builds himself.
3. **Then WS-2** — the honest-gated depth build.
4. **WS-3 with the native** — the Rule Base.
Also pending (small): two L3/L5 one-liner fixes (DCB-001 kala_timeline psycopg, DCB-004 life_events NOT NULL),
applying `build_events` to prod for the live SSE rail.

## §9 — How we work (so you fit in fast)
- **Be the honest architect.** This native wants truth over reassurance — celebrate real progress, but name
  thin data, ungrounded signals, gate bugs, and gaps plainly. That candor caught the LB-in-asia-south1 issue,
  the RLS login-breaker, the no-Anthropic conflict, the parked-foundation/hollow-data problem, and the legacy
  pollution — all things pure automation would have shipped.
- **Match the calibration:** swarm for mechanical bulk, humans on gates + judgment. Keep volume/grounding gates
  honest so "built" means *fully* built.
- **Deliverables:** Cowork authors specs/briefs/prompts as `.md` files in the folder; the native pastes prompts
  to the Antigravity executor. Present files with the file-sharing tool; keep prose concise (the native prefers
  it). Use AskUserQuestion for genuine decision forks.
- **Standing constraints:** no Anthropic in prod; PyJHora is source-of-truth; FORENSIC is a coverage benchmark
  not a value oracle; LEL isolated; only computed facts in built data; acharya-grade quality bar.

## §10 — A tangible anchor (proof the instrument is real)
From the live engine, the native's current dasha: **Mercury Mahādasha / Saturn Antardasha / Sun
Pratyantardasha (2026-05-10 → 2026-06-28)**. A week ago this folder was a dead, half-built system the native
chose to tear down; now it's a live six-layer instrument that built itself and computes his real chart. The
remaining work is depth + the portal + the Rule Base — captured above.

---

*End of CONVERSATION_HANDOFF_BRAHMA 2026-06-04. Read §7's canonical docs next. Welcome to Brahma.*
