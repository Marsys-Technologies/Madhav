---
artifact: IMPLEMENTATION_PLAN_v1_0.md
document: MARSYS-JIS Multi-Ayanamsha Build — Autonomous Conductor Implementation Plan
status: READY_FOR_EXECUTION
version: 1.0
date: 2026-05-29
authored_by: Cowork (single-author; no human review gates per native directive)
intended_for: Claude Code in Antigravity IDE, running as Conductor with --dangerously-skip-permissions
scope: A0 global asset substrate (47 items) + A1–A14 per-chart deterministic build + A15-A20 supplementary + INF1–INF12 infrastructure + ACC1–ACC10 acceptance + close. ~95 sessions across 13 parallel worktrees.
execution_mode: fully_autonomous
human_gates: zero (per native directive — all auto-merge, auto-deploy, auto-rollback rails)
tracker: localhost:8765 (state.json + activity feed updated on every session close)
estimated_wall_clock: 8–12 days continuous operation
---

# MARSYS-JIS Multi-Ayanamsha Build — Implementation Plan

> **Read order for the executing Conductor:** §0 → §1 → §2 → §3 → §4 → §5 → §6 → §7 → §8 → §9 → §10 → §11 → §12.
> §0–§2 = mission + scope + decisions. §3–§4 = pre-flight + topology. §5 = wave plan. §6 = session lifecycle. §7–§9 = safety rails + tracker + halt/resume. §10 = ops commands. §11 = DoD. §12 = references.

---

## §0 — Mission

Build the complete MARSYS-JIS Multi-Ayanamsha Deterministic Build workstream end-to-end, autonomously, in 8-12 wall-clock days, via a single Conductor process spawning parallel Claude Code sub-agents across 13 worktrees. Zero human approval gates inside the loop. Per-session commit + auto cherry-pick to main + auto-deploy with canary + auto-rollback rails. Tracker (`localhost:8765`) updated on every state change. Definition of done = all 95+ sessions closed, all 8 hard gates GREEN, answer:eval b11 ≥ 60%, sealing artifact committed.

---

## §1 — Operating model

### §1.1 — One Conductor, many sub-agents

A single Claude Code instance launched in the main repo with `--dangerously-skip-permissions` reads this plan + `session_queue.yaml` and walks the queue. For each ready session it:

1. Picks the worktree the session belongs to (pre-created in §3).
2. Writes the session's `CLAUDECODE_BRIEF.md` into that worktree's project root.
3. Spawns a sub-agent — a Claude Code child process — in that worktree, also with `--dangerously-skip-permissions`.
4. Sub-agent reads CLAUDECODE_BRIEF.md, executes scope, writes tests, runs tests, commits with the conventional message, exits.
5. Conductor gates on the brief's `check_commands` (tests pass; lint pass; schema_validator pass).
6. On pass: auto-commit + auto cherry-pick to main + auto push + auto-deploy if applicable + tracker update + activity row + next session.
7. On fail: retry up to 3× with refined diagnostic; on exhaustion, halt the affected stream only (other streams continue) + tracker → blocked + halt log entry.

Up to **6 sub-agent worktrees run concurrently** (configurable via `MAX_PARALLEL=6`). Within a stream, sessions are sequential. Streams run parallel where dependency graph permits.

### §1.2 — No human gates anywhere in the loop

Hard rule: the Conductor MUST NOT pause, ask, or wait for human input. All decisions made via prescribed rules in this plan. Native intervention only when (a) Conductor itself crashes, or (b) halt log fills with cascading blockers needing scope re-decision.

### §1.3 — Bypass-permissions enforcement

Every Claude Code invocation — Conductor + every sub-agent — runs with `--dangerously-skip-permissions`. No file-write prompts. No git push prompts. No gcloud confirm prompts. All scripted, all silent, all logged.

### §1.4 — Sequential commits within a session

Within ONE session, the sub-agent may make multiple commits if the work is multi-file. Each commit follows convention: `<type>(<scope>): <subject> [BUILD-ORCH-<stream>-<num>]`. Cherry-pick to main picks the ENTIRE session's commits (squash optional per session metadata).

---

## §2 — Scope (what gets built)

### §2.1 — Asset coverage (verbatim from tracker)

| Track | Count | Description |
|---|---|---|
| A0 global substrate | 47 items | Classical RAG + ephemeris + Nadi + Lal Kitab + Bhrigu Samhita + lookup tables (nakshatra/sign/graha/yoga/dosha/saham/varga/aspect/friendship/karaka/ayanamsha/sade-sati/tara/chandra/mrityubhaga/muhurta/remedies/worked-examples/era/stars/mantras/gemstones/yantras/compatibility/career/Tantric/Ayurveda/Numerology/mundane). |
| A1–A14 per-chart | 14 items | Engine + FORENSIC render + chart_facts + Panchanga + Sensitive Points + Vargas + Dashas + T1 structural + Sade Sati + MSR + CDLM + CGM + RM + UCN digest. Per-ayanamsha (5× build). |
| A15–A20 supplementary | 6 items | Chakras + Vedha + Argala + Bhrigu Bindu transit + Tajik per-chart + Per-graha next-exact-aspect. Built but native flagged as optional; Conductor runs them as low-priority backlog. |
| INF1–INF12 infrastructure | 12 items | New Client Form, schema migrations, Python pipeline, API surface, Constellation UI, Notifications, Consume Hybrid, no-narration linter, MVs + indexes, RAG + embeddings, MCP Resources, production tracker. |
| ACC1–ACC10 acceptance | 10 items | answer:eval re-baseline + 8 hard gates + red-team + multi-tenant smoke + concurrent-build smoke + version bumps + docs + sealing artifact + prod deploy + native sign-off. |
| MISC decisions | 7 items | Already-recorded off-stream architectural decisions (drop JH-parity, multi-ayanamsha full-build, agentic hybrid, chunking, MCP Pattern 3, similarity signature, 1950 date adjustment). Reference-only; affect specific items per `affects` field. |

**Total: ~96 trackable items × ~95 implementation sessions.**

### §2.2 — Decisions locked (from `state.json` tracks)

All architectural decisions from the planning conversations are LOCKED:
- 5 canonical ayanamshas: Lahiri, True Chitra, KP, Raman, Surya Siddhanta. Default-checked all 5 at new-client time.
- Engine invocation runs 5× per chart in parallel asyncio.
- 23 bodies emitted per ayanamsha (9 grahas + 2 nodes × 2 + 2 Liliths + 10 asteroids/outer).
- G1_internal_invariants replaces G1_jh_parity (algebraic + cross-ayanamsha sanity + classical spot-check + two-pass sensitive points).
- FORENSIC.md chunked + Vertex-embedded with no-narration linter enforcement.
- Per-chart similarity signature: 1 embedding per (chart, ayanamsha).
- MCP sidecar = Resources + Tools (Pattern 3). Internal `/consume` chat uses native SQL retrieval (no MCP roundtrip).
- Consume Hybrid: pre-cached chart bundle (Layer 1) + bounded agentic loop (R11.F substrate) + cross-ayanamsha consensus tool + intent classifier preamble + B.11 inline floor check + stop-confidence + streaming tool-call progress.
- Time-series globals start 1950.
- Whole-system rebuild only; no per-asset surgical rebuild.
- Failure: retry N then halt.
- Cancellation allowed with confirmation.
- Engine pin: chart stays on its build-time engine version until manual rebuild.
- In-app notifications only (no email/push).
- No concurrency limit per guest.

### §2.3 — Out of scope (explicit)

- LEL regeneration (native-disclosed)
- Phase 11B legacy pipeline
- M5-A backlog (concurrent workstream)
- M6 prospective testing (post-this-workstream)
- Monitoring alerts / SLO apply (separate ticket)
- Phase L engine hygiene (D1 dignity + ayanamsha residual tighten — folded if convenient, otherwise separate)

---

## §3 — Pre-flight (one-time, ~10 minutes)

### §3.1 — Repo state

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout main && git pull origin main
git status                                # must be clean
```

### §3.2 — Create all worktrees

```bash
git worktree add -b feature/build-orch/stream-a-globals       ../MadhavBO-A    main
git worktree add -b feature/build-orch/stream-b-form-schema   ../MadhavBO-B    main
git worktree add -b feature/build-orch/stream-c-pipeline      ../MadhavBO-C    main
git worktree add -b feature/build-orch/stream-d-api           ../MadhavBO-D    main
git worktree add -b feature/build-orch/stream-e-engine        ../MadhavBO-E    main
git worktree add -b feature/build-orch/stream-f-render        ../MadhavBO-F    main
git worktree add -b feature/build-orch/stream-g1-l25-base     ../MadhavBO-G1   main
git worktree add -b feature/build-orch/stream-g2-l25-vd       ../MadhavBO-G2   main
git worktree add -b feature/build-orch/stream-g3-l25-structural ../MadhavBO-G3 main
git worktree add -b feature/build-orch/stream-g4-l25-synthesis ../MadhavBO-G4  main
git worktree add -b feature/build-orch/stream-h-constellation ../MadhavBO-H    main
git worktree add -b feature/build-orch/stream-i-notify        ../MadhavBO-I    main
git worktree add -b feature/build-orch/stream-j-consume       ../MadhavBO-J    main
git worktree list
```

### §3.3 — Infra checks

```bash
# DB proxy
bash platform/scripts/start_db_proxy.sh &
sleep 3
psql -h localhost -p 5433 -U postgres -d amjis -c "SELECT version();"

# GCP
gcloud auth list
gcloud config get-value project   # expect: madhav-astrology

# Node + Python deps
pnpm install
pip install -r platform/python-sidecar/pipeline/requirements.txt

# Tracker server running
curl -s http://localhost:8765 | head -5    # expect HTML
# If not: cd 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/tracker && python3 -m http.server 8765 &
```

### §3.4 — Conductor artifacts

The Conductor itself authors these in its Phase A (first ~30 minutes of run) before kicking off sub-agents:

```
00_ARCHITECTURE/CONDUCTOR/build_orchestrator/
├── IMPLEMENTATION_PLAN_v1_0.md           ← THIS FILE (already exists)
├── CONDUCTOR_BUILD_ORCH_PROMPT.md        ← Conductor's own run loop instructions
├── session_queue.yaml                     ← ~95 sessions, dependency-graphed
├── sessions/                              ← ~95 per-session briefs
│   ├── A-01-G2-ephemeris-1950-extend.md
│   ├── A-02-G6-sankranti-per-ayanamsha.md
│   ├── ...
├── scripts/
│   ├── preflight.sh
│   ├── update_tracker.py
│   ├── auto_commit.sh
│   ├── auto_cherry_pick.sh
│   ├── auto_merge.sh
│   ├── deploy_and_smoke.sh
│   ├── halt_handler.sh
│   ├── halt_all.sh
│   └── resume.sh
├── CONDUCTOR_LOG.md                       ← appended by Conductor
├── CONDUCTOR_HALT_LOG.md                  ← appended on halts
└── CONDUCTOR_RUN.log                      ← raw stdout from Conductor process
```

Phase A duration: ~30-60 minutes. Phase B (execution) begins immediately after.

---

## §4 — Worktree topology + parallelization grid

| Stream | Worktree | Files-owned (must not overlap with other streams) | Sessions | Parallel-after |
|---|---|---|---|---|
| **A** | MadhavBO-A | `marsys_global.*` schema; `platform/python-sidecar/pipeline/global_*`; G* writers; classical corpus ingest | ~30 | Day 1 start |
| **B** | MadhavBO-B | `platform/migrations/124-132`; `platform/src/app/clients/new/`; `platform/src/components/clients/NewClientForm.tsx`; charts table extension | ~12 | Day 1 start |
| **C** | MadhavBO-C | `platform/python-sidecar/pipeline/build_chart.py` + l25_builder extensions; cloudbuild.yaml; Cloud Run Job spec | ~8 | After B closes mig 124-127 |
| **D** | MadhavBO-D | `platform/src/app/api/build/*`, `/api/clients/create`, `/api/engine/current`, `/api/conversations/[id]/active-ayanamshas`, `/api/charts/[id]/ayanamsha-status` | ~9 | After B closes mig 124 |
| **E** | MadhavBO-E | `platform/python-sidecar/natal_engine/*` (positions, vargas, dignities, etc.); `chart_output schema`; G1_internal_invariants tests | ~8 | After A's G20 + B's mig 132 |
| **F** | MadhavBO-F | `platform/python-sidecar/pipeline/render/forensic_*.py`; Jinja2 templates per H2 section; `01_FACTS_LAYER/charts/` writer | ~14 | After E closes |
| **G1** | MadhavBO-G1 | `pipeline/writers/chart_facts_writer.py`; `pipeline/writers/panchanga_writer.py`; `pipeline/writers/sensitive_points_writer.py` | ~8 | After E closes |
| **G2** | MadhavBO-G2 | `pipeline/writers/vargas_writer.py`; `pipeline/writers/dashas_writer.py` | ~7 | After E + A's G15/G16 close |
| **G3** | MadhavBO-G3 | `pipeline/writers/t1_structural_writer.py`; `pipeline/writers/sade_sati_writer.py` | ~6 | After G1 closes |
| **G4** | MadhavBO-G4 | `pipeline/writers/msr_writer.py`; `cdlm_writer.py`; `cgm_writer.py`; `rm_writer.py`; `ucn_digest_writer.py` | ~10 | After G3 closes |
| **H** | MadhavBO-H | `platform/src/components/build_orchestrator/*`; `platform/src/app/clients/[id]/build/page.tsx`; delete BuildChat.tsx | ~13 | After D closes |
| **I** | MadhavBO-I | `platform/src/components/dashboard/BuildsInProgressCard.tsx`; `platform/src/components/toast/*`; notification_views mig | ~5 | After D closes |
| **J** | MadhavBO-J | `platform/src/lib/retrieve/bundle_composer.ts`; `platform/src/lib/retrieve/cross_ayanamsha_consensus.ts`; intent_classifier; prompt_cache adapters; tool description rewrites; consume chat settings | ~15 | After G1 closes |

**File-overlap discipline:** the per-session brief's `may_touch` + `must_not_touch` globs enforce strict partitioning. If two streams need the same file, the brief routes BOTH sessions to one stream serially.

**Concurrency rules:**
- Max 6 active worktrees concurrently (configurable). Tunable via `MAX_PARALLEL` env in Conductor.
- A stream's sessions are sequential (one at a time per worktree).
- Cross-stream merges to main are serialized by `lock_main.sh` — only one cherry-pick at a time touches main.

### §4.1 — Wave schedule

| Wave | Wall-clock | Streams active | Notes |
|---|---|---|---|
| Wave 0 | Day 1 | A + B | A's 30 sessions split into 2 internal sub-streams (A-globals-data, A-globals-rules) running parallel inside the A worktree by partitioning subdirectories. B's 12 sessions sequential. |
| Wave 1 | Days 2-3 | C + D + E | C and D depend on B's early migrations + form. E depends on A's G20 ayanamsha registry. |
| Wave 2 | Days 4-6 | F + G1 + H + I | F and G1 both depend on E. H and I depend on D. |
| Wave 3 | Days 5-7 | G2 + G3 + J | G2 depends on G1's chart_facts schema + A's G15/G16. G3 depends on G1. J depends on G1's chart_facts ready. |
| Wave 4 | Days 7-8 | G4 | G4 depends on G3 + A's G12/G13/G27. |
| Wave 5 | Days 8-9 | ACC + Close | Sequential in main repo (no worktrees). Final deploy + sealing artifact. |

Buffer: 1-2 days for halts/retries. Total ETA: **8-12 days continuous autonomous operation.**

---

## §5 — Wave-by-wave session plan

See `session_queue.yaml` for the complete machine-readable list. High-level structure:

### Wave 0 (parallel: A + B)

**Stream A (30 sessions) — A0 globals:**
A-01 G2 ephemeris 1950 extend · A-02 G6 sankranti per-ayanamsha · A-03 G7 panchanga 5-ayanamsha extend · A-04 G9 nakshatra attribute · A-05 G10 sign attribute · A-06 G11 graha attribute · A-07 G12 yoga definitions (200+) · A-08 G13 dosha definitions · A-09 G14 saham formulas (50+) · A-10 G15 dasha-system rules (32) · A-11 G16 varga formulas (30+) · A-12 G17 aspect rules · A-13 G18 friendship reference · A-14 G19 karaka assignments · A-15 G20 ayanamsha registry (5 canonical + capability-only) · A-16 G21 Saturn ingresses per-ayanamsha · A-17 G22 tara bala matrix · A-18 G23 chandra bala matrix · A-19 G24 Vimshottari starting-lord table · A-20 G25 mrityubhaga/gandanta/pushkara reference · A-21 G26 muhurta auspiciousness · A-22 G27 remedial library · A-23 G28 worked-examples library · A-24 G31 era conversion · A-25 G32 fixed stars · A-26 G33+G34+G35 mantras+gemstones+yantras · A-27 G36+G37+G39 compatibility+muhurta-rules+rituals · A-28 G40+G41+G43 career+Lal Kitab+Bhrigu Samhita · A-29 G44+G45 Nadi+Ayurveda · A-30 G46+G47+G48+G49+G50+G51 Tantric+Numerology+Mundane+Bhrigu Bindu+Tajik+Sankashti.

**Stream B (12 sessions) — INF1 form + INF2 schema:**
B-01 mig 124 builds · B-02 mig 125 build_steps · B-03 mig 126 engine_versions · B-04 mig 127 chart_facts ext · B-05 mig 128 history audit · B-06 mig 129 supersedence · B-07 mig 130 ayanamsha_reports · B-08 mig 131 chart_documents · B-09 mig 132 ayanamsha_registry · B-10 CHART_FACTS_SCHEMA.json extend + drift detector update · B-11 NewClientForm UI + form validation · B-12 /api/clients/create + tests.

### Wave 1 (parallel: C + D + E)

**Stream C (8) — Python pipeline:**
C-01 build_chart.py scaffold + arg parse · C-02 5-ayanamsha parallel runner (asyncio + thread pool) · C-03 build_events emitter · C-04 cancellation polling · C-05 retry-then-halt logic · C-06 Cloud Run Job command repoint (cloudbuild.yaml) · C-07 stub asset writers (no-op emit) · C-08 SMOKE: run native chart 5-ayanamsha empty pipeline.

**Stream D (9) — API surface:**
D-01 extend /api/build/start (builds row + ayanamshas[]) · D-02 /api/build/cancel/[buildId] · D-03 /api/build/active · D-04 /api/build/recent · D-05 hardening /api/clients/create · D-06 /api/engine/current · D-07 /api/conversations/[id]/active-ayanamshas · D-08 /api/charts/[id]/ayanamsha-status · D-09 all routes tests.

**Stream E (8) — Engine expansion:**
E-01 heliocentric coords emission · E-02 declination + RA + altaz for all bodies · E-03 True Node + Mean Node both · E-04 Mean Lilith + True Lilith · E-05 10 asteroids/outer (Ceres/Pallas/Juno/Vesta/Chiron/Uranus/Neptune/Pluto/Sedna/Eris) · E-06 D1+D9+D10 vargas for non-graha bodies · E-07 cross-ayanamsha report generator · E-08 G1_internal_invariants suite (replaces JH-parity gate).

### Wave 2 (parallel: F + G1 + H + I)

**Stream F (14) — FORENSIC render:**
F-01 Jinja2 base + frontmatter + anchor convention · F-02 per-graha sections (17 bodies) · F-03 houses + cusps + house system comparison · F-04 upagrahas + Saturn-derived points · F-05 esoteric + Sahams (50+) · F-06 Karakas/Karakamsa/Arudhas/Special Lagnas · F-07 Yogas + Doshas registers · F-08 Panchanga full birth-day · F-09 Aspects (Parashari + Jaimini + Tajik matrices) · F-10 Ashtakavarga + Shadbala + Bhava Bala · F-11 Vimsopaka + Ishta-Kashta + Avasthas · F-12 Vargas (30+ including Nadi D108/D150/D2700) · F-13 Dashas (32 systems) · F-14 KP cuspal + Tajik + Midpoints + Chakras + Eclipses + Nadi-amsa + Argala + Astronomical + no-narration linter.

**Stream G1 (8) — chart_facts/panchanga/sensitive:**
G1-01 chart_facts writer (per-ayanamsha citation strings + fact_id sha256) · G1-02 chart_facts_history triggers · G1-03 chart_facts_supersedence triggers · G1-04 panchanga writer · G1-05 sensitive points writer · G1-06 materialized views (mv_chart_planet_summary, mv_chart_house_summary) · G1-07 per-(chart_id, ayanamsha_id, category) indexes · G1-08 chart_facts SMOKE.

**Stream H (13) — Constellation UI:**
H-01 delete BuildChat.tsx + BuildActionPanel.tsx + orphan audit · H-02 ConstellationCanvas.tsx (SVG natal wheel) · H-03 AssetNode.tsx (state machine) · H-04 BuildWaveAnimation.tsx (Framer Motion sweep) · H-05 AssetDetailPanel.tsx (slide-in right) · H-06 BuildCommandBar.tsx · H-07 EngineDriftBadge.tsx · H-08 5-ayanamsha multi-pulse · H-09 SSE consumer · H-10 empty-state visual · H-11 cancel-confirmation modal · H-12 mount + parent-context integration tests · H-13 Playwright visual smoke + GIF.

**Stream I (5) — Notifications:**
I-01 BuildsInProgress card · I-02 post-visit toast · I-03 notification_views migration · I-04 cross-chart concurrent UI · I-05 tests.

### Wave 3 (parallel: G2 + G3 + J)

**Stream G2 (7) — Vargas + Dashas writers:**
G2-01 vargas writer (16 Parashari) · G2-02 vargas writer (supplementary D5/D6/D8/D11/D14/D15/D21/D32/D33/D50/D54) · G2-03 vargas writer (Nadi D108/D150/D2700) · G2-04 dashas writer (Vimshottari + Ashtottari + Yogini) · G2-05 dashas writer (Jaimini 12 systems) · G2-06 dashas writer (Tajik 4 systems + Special 4) · G2-07 two-pass verification + storage SMOKE.

**Stream G3 (6) — T1 structural + Sade Sati:**
G3-01 aspect matrix (Parashari + Jaimini + Tajik) · G3-02 dispositors + shadbala (6 sub-balas) · G3-03 ashtakavarga (BAV + SAV + Trikona + Ekadhipathya + Sodhita + Kakshyas) · G3-04 yogas register (200+ from G12) + doshas register (from G13) · G3-05 vimsopaka + bhava bala + ishta-kashta + 5 avastha schemes · G3-06 sade sati cycles writer.

**Stream J (15) — Consume Hybrid:**
J-01 conversations.active_ayanamshas migration · J-02 chart bundle composer (Layer 1) · J-03 bundle MCP Resources (15-25/chart) · J-04 prompt cache Anthropic extension · J-05 prompt cache Gemini cachedContent · J-06 prompt cache DeepSeek telemetry · J-07 cross-ayanamsha consensus retrieval tool · J-08 intent classifier preamble · J-09 stop-confidence wiring · J-10 B.11 inline floor check · J-11 tool description rewrites (top 20) + few-shot inline · J-12 streaming tool-call progress UI · J-13 iteration telemetry dashboard · J-14 R-AYN.1/2/3 planner rules · J-15 consume hybrid tests + answer:eval delta measurement.

### Wave 4 (G4)

**Stream G4 (10) — L2.5 synthesis writers:**
G4-01 salience formula v1 + unit tests · G4-02 MSR writer (every signal, no threshold drop) · G4-03 MSR enrichment (constituent_facts + classical_sources) · G4-04 CDLM writer (9x9 with shared-factor counts) · G4-05 CGM writer (nodes + structural edges) · G4-06 RM writer (weakest → remedy candidates from G27) · G4-07 UCN digest writer (computed signature) · G4-08 RAG chunking + Vertex AI embedding + no-narration linter · G4-09 per-chart similarity signature embedding · G4-10 SMOKE: native chart end-to-end (all 5 ayanamshas, all 14 assets).

### Wave 5 (ACC + Close, sequential)

ACC-01 answer:eval re-baseline · ACC-02 8 hard gates check (G1_internal_invariants replaces G1_jh_parity) · ACC-03 red-team per IS.8(b) · ACC-04 multi-tenant smoke · ACC-05 concurrent-build smoke (3 charts parallel) · ACC-06 version bumps (CLAUDE.md/PROJECT_ARCHITECTURE/CANONICAL_ARTIFACTS/CAPABILITY_MANIFEST) · ACC-07 BUILD_ORCHESTRATOR_README.md · ACC-08 sealing artifact MULTI_AYANAMSHA_BUILD_CLOSE_v1_0.md · ACC-09 final production deploy + 10-min log watch · ACC-10 native sign-off (tracker marks complete).

---

## §6 — Session lifecycle

Each session follows the same lifecycle. Conductor enforces all of it.

### §6.1 — Brief authoring (Conductor Phase A only)

Conductor authors `sessions/<session-id>.md` per session. Each brief carries:

```yaml
---
session_id: A-03-G7-panchanga-5ayanamsha-extend
stream: A
worktree: ../MadhavBO-A
branch: feature/build-orch/stream-a-globals
scope: Extend panchanga_daily table + bootstrap script to populate 5 ayanamshas (Lahiri, True Chitra, KP, Raman, Surya Siddhanta) for 1950-2100.
may_touch:
  - platform/python-sidecar/pipeline/bootstrap_panchanga.py
  - platform/migrations/<next>_panchanga_ayanamsha_ext.sql
  - platform/python-sidecar/pipeline/__tests__/test_panchanga_5ayanamsha.py
must_not_touch:
  - platform/src/**
  - 025_HOLISTIC_SYNTHESIS/**
  - other streams' worktrees
depends_on: [A-15]   # G20 ayanamsha registry
acceptance_criteria:
  - panchanga_daily has ayanamsha_id column added
  - 73,414 × 5 = ~367K rows populated for 1950-2100 across all 5 ayanamshas
  - pytest test_panchanga_5ayanamsha PASS
  - drift_detector PASS
check_commands:
  - pytest platform/python-sidecar/pipeline/__tests__/test_panchanga_5ayanamsha.py
  - python platform/scripts/governance/drift_detector.py
commit_pattern: 'feat(global/G7): panchanga 5-ayanamsha extend 1950-2100'
tracker_update:
  item: G7
  brief: locked  # already locked; impl moves
  impl: merged_main
deploy:
  service: amjis-sidecar
  cloudbuild: platform/python-sidecar/cloudbuild.yaml
  post_deploy_smoke: pytest platform/python-sidecar/pipeline/__tests__/test_g7_prod_smoke.py
---

# Session A-03 — G7 panchanga 5-ayanamsha extend

[full scope spec below]
```

### §6.2 — Sub-agent invocation

```bash
# Conductor pseudo-shell
WORKTREE=../MadhavBO-A
cd $WORKTREE
git checkout feature/build-orch/stream-a-globals

# Copy brief into worktree
cp ../Madhav/00_ARCHITECTURE/CONDUCTOR/build_orchestrator/sessions/A-03-G7-panchanga-5ayanamsha-extend.md ./CLAUDECODE_BRIEF.md

# Spawn sub-agent
claude --dangerously-skip-permissions \
       --append-system-prompt "Read CLAUDECODE_BRIEF.md at project root first. Read CLAUDE.md §C items 1-11. Execute scope. Run check_commands. Commit per commit_pattern. Set CLAUDECODE_BRIEF.md status to COMPLETE. Exit." \
       --print --output-format=stream-json \
       < /dev/null
```

### §6.3 — Gate check

```bash
# After sub-agent exits
bash 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/gate_check.sh A-03
# Runs the brief's check_commands. Exit 0 = pass.
```

### §6.4 — Auto commit + cherry-pick + push

```bash
bash scripts/auto_commit.sh A-03    # idempotent; brief usually self-commits, this re-runs if needed
bash scripts/lock_main.sh           # serializes main mutations
bash scripts/auto_cherry_pick.sh A-03 main
bash scripts/unlock_main.sh
git -C ../Madhav push origin main
```

### §6.5 — Auto deploy (if applicable)

```bash
# Only if brief has `deploy:` field
bash scripts/deploy_and_smoke.sh amjis-sidecar A-03
# Canary 10% → 5min log watch → auto-promote 100% OR auto-rollback
```

### §6.6 — Tracker update

```bash
python scripts/update_tracker.py \
  --item G7 \
  --brief locked \
  --impl deployed \
  --session A-03 \
  --activity "A-03 closed: G7 panchanga 5-ayanamsha deployed to amjis-sidecar rev <X>"
```

This writes `state.json` + the tracker page reflects within 30s.

### §6.7 — On failure (retry then halt)

```bash
# Conductor logic
RETRY=$(get_retry_count A-03)
if [ $RETRY -lt 3 ]; then
  # Re-run with refined diagnostic
  echo "Retry $((RETRY+1))/3 for A-03"
  add_diagnostic_to_brief A-03 "<test output excerpt>"
  spawn_sub_agent A-03
else
  bash scripts/halt_handler.sh A-03
  # Halt stream A only; other streams continue
  python scripts/update_tracker.py --item G7 --impl blocked
fi
```

---

## §7 — Safety rails (within autonomous mode)

| Rail | Mechanism | Triggers on |
|---|---|---|
| Migration safety | Staging-first via `apply_migration_staging.sh` → smoke → auto-promote OR auto-rollback | Every B-XX migration session |
| Canary deploy | Cloud Run 10% → 5min log watch → promote OR rollback | Every deploy step |
| CI gates | Vitest + pytest + drift_detector + schema_validator + naming_lint run on every PR | Every push to feature branch |
| Hard gates G1-G6 | Run as Conductor pre-merge check | Before every cherry-pick to main |
| answer:eval regression | After every L2.5 merge, run answer:eval; if b11 drops > 5% from current baseline, halt | After G1/G2/G3/G4 stream merges |
| Lock-main | Only one cherry-pick at a time touches main | Every cherry-pick |
| Halt-all kill switch | `scripts/halt_all.sh` stops Conductor + all sub-agents | Operator manual run if needed |
| state.json git history | Every tracker update is a commit on main | Continuous |

These run automatically. Honest disclosure: they CANNOT prevent every failure mode (e.g., correct-but-incorrect code that passes tests). They DO prevent (a) syntax/lint errors reaching prod, (b) migrations breaking the DB, (c) deploys taking down /consume, (d) tests silently failing.

---

## §8 — Tracker integration

The Conductor calls `scripts/update_tracker.py` on every state change. State.json fields touched per session:

```
tracks[X].items[Y].brief.status              # 'discussing' → 'locked'
tracks[X].items[Y].impl.status               # 'not_started' → 'in_progress' → 'merged_main' → 'deployed'
tracks[X].items[Y].impl.session_id           # 'A-03'
tracks[X].items[Y].impl.branch               # 'feature/build-orch/stream-a-globals'
tracks[X].items[Y].impl.pr_url               # GitHub PR (if created)
tracks[X].items[Y].impl.merge_sha            # commit SHA
tracks[X].items[Y].impl.started_at           # ISO timestamp
tracks[X].items[Y].impl.completed_at         # ISO timestamp
activity[]                                    # append row
```

`update_tracker.py` is idempotent — safe to retry. Atomic file write via temp file + rename.

**Operator monitoring:** open `http://localhost:8765` anytime. Page polls state.json every 30s. Filter pills + per-track stats update live. Activity feed shows last 50 events.

---

## §9 — Halt & resume protocol

### §9.1 — When the Conductor halts

- Sub-agent retry exhausted (3 attempts × per session)
- Migration smoke failure (staging)
- Canary deploy 5xx-rate exceedance
- Hard gate flips red (G1-G6)
- answer:eval b11 drops > 5%
- Cherry-pick conflict not auto-resolvable

**Behavior on halt:** affected stream halted only. Other streams continue. `CONDUCTOR_HALT_LOG.md` gets an entry. Tracker flips affected item to `blocked`.

### §9.2 — Operator halt-all

```bash
bash 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/halt_all.sh
```

Kills all sub-agents + Conductor process. State preserved. Tracker flips Conductor status to `paused`.

### §9.3 — Resume

```bash
bash 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/resume.sh
```

Re-launches Conductor with previous queue state. Resumes from last incomplete session.

---

## §10 — Operational commands (operator run book)

### Initial kickoff
```bash
# 1. Pre-flight (one-time, ~10 min)
cd /Users/Dev/Vibe-Coding/Apps/Madhav
bash 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/preflight.sh

# 2. Launch Conductor (one command, runs autonomously)
nohup claude --dangerously-skip-permissions \
  --append-system-prompt "$(cat 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/CONDUCTOR_BUILD_ORCH_PROMPT.md)" \
  --print --output-format=stream-json \
  < /dev/null \
  > 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/CONDUCTOR_RUN.log 2>&1 &
echo $! > 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/conductor.pid

echo "Conductor PID: $(cat 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/conductor.pid)"
echo "Tracker:       http://localhost:8765"
echo "Logs:          tail -f 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/CONDUCTOR_RUN.log"
```

### Monitor
```bash
open http://localhost:8765
tail -f 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/CONDUCTOR_RUN.log
cat 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/CONDUCTOR_HALT_LOG.md
git worktree list
```

### Halt all
```bash
bash 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/halt_all.sh
```

### Resume
```bash
bash 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/resume.sh
```

### Clean up after completion
```bash
# Worktrees
for w in MadhavBO-A MadhavBO-B MadhavBO-C MadhavBO-D MadhavBO-E MadhavBO-F MadhavBO-G1 MadhavBO-G2 MadhavBO-G3 MadhavBO-G4 MadhavBO-H MadhavBO-I MadhavBO-J; do
  git worktree remove ../$w --force
done

# Branches (after merge)
git branch -D $(git branch | grep 'feature/build-orch/')
```

---

## §11 — Definition of Done

The workstream is COMPLETE when ALL are true:

1. All ~95 sessions closed (`session_queue.yaml` shows all `status: complete`).
2. All A0 globals deployed; A1-A14 per-chart writers deployed; INF1-INF12 infrastructure deployed; ACC1-ACC10 sequential acceptance closed.
3. answer:eval baseline shows `b11 ≥ 60%` AND `layer_cov ≥ 65%` (material improvement vs v1.1's b11=29%, layer_cov=31%).
4. All 8 hard gates GREEN: naming_ci, jh_oracle_pinned (static ref retained), G1_internal_invariants (replaces G1_jh_parity), G2_authz_live, G3_contract, G4_no_native_lit, G5b_onfinish, G6_tool_coverage.
5. Red-team per IS.8(b) — 0 class-1 findings; class-2/3 documented as residuals.
6. Both tenants queryable end-to-end (legacy + new-architecture).
7. Concurrent-build smoke (3 charts parallel) succeeds.
8. CLAUDE.md + PROJECT_ARCHITECTURE_v2_2.md + CANONICAL_ARTIFACTS_v1_0.md + CAPABILITY_MANIFEST.json version-bumped.
9. Sealing artifact `MULTI_AYANAMSHA_BUILD_CLOSE_v1_0.md` committed.
10. Final production deploy + 10-min log watch clean.
11. Tracker shows 100% Brief track + 100% Impl track.
12. Conductor process exited gracefully (PID file removed).

---

## §12 — References

**Plan + spec:**
- `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/BUILD_ORCHESTRATOR_PLAN_v1_0.md` — parent overall plan
- `00_ARCHITECTURE/DETERMINISTIC_REBUILD_SCOPING_v1_0.md` — scoping doc with all design decisions
- `00_ARCHITECTURE/DATA_LAYER_REBUILD_TARGET_SPEC_v1_0.md`
- `00_ARCHITECTURE/STRUCTURAL_FACT_LAYER_SPEC_v1_0.md`
- `00_ARCHITECTURE/MSR_UCN_CONTAMINATION_AUDIT_v1_0.md`

**Engine:**
- `platform/python-sidecar/natal_engine/__init__.py`
- `platform/python-sidecar/natal_engine/l25_builder/build.py`

**Existing build surface (being replaced):**
- `platform/src/components/build/BuildChat.tsx` (DELETE in H-01)
- `platform/src/app/clients/[id]/build/BuildActionPanel.tsx` (DELETE in H-01)
- `platform/python-sidecar/pipeline/main.py` (REPLACED by build_chart.py in C-01)

**Governance:**
- `CLAUDE.md` v4.8 (current master instructions)
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` v5.64
- `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md`
- `00_ARCHITECTURE/MIGRATION_DIRECTORY_POLICY_v1_0.md` (next migration: 124)

**Tracker:**
- `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/tracker/index.html` (localhost:8765 viewer)
- `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/tracker/state.json` (live truth)

**Conductor pattern precedent:**
- `00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_v1_0.md` (original v1 conductor)
- `00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_MCP_v1_0.md` (MCP arc)
- `00_ARCHITECTURE/CONDUCTOR/modernization/RED_TEAM_PLATFORM_MOD_v1_0.md` (modernization arc seal)

---

*End of IMPLEMENTATION_PLAN_v1_0.md — ready for Conductor execution. No further authoring required before kickoff.*
