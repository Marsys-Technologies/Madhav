---
artifact: IMPLEMENTATION_PLAN_A3_A4_A5_v1_0.md
document: MARSYS-JIS — A3 + A4 + A5 Autonomous Conductor Implementation Plan
status: READY_FOR_EXECUTION
version: 1.0
date: 2026-05-29
authored_by: Cowork (with learnings from prior workstream — JIT brief authoring, daemon-driven tracker sync)
intended_for: Claude Code in Antigravity IDE, running as Conductor with --dangerously-skip-permissions
scope: A3 (chart_facts schema substrate) + A4 (Panchanga per-chart writer) + A5 (Sensitive Points per-chart writer)
execution_mode: fully_autonomous
human_gates: zero
tracker: daemon-driven (auto-syncs session_queue.yaml → state.json → GCS, no Conductor cooperation needed)
estimated_sessions: ~30
estimated_wall_clock: 3–5 days
---

# A3 + A4 + A5 — Implementation Plan

## §0 — Mission

Implement the locked specs A3 (`chart_facts` schema substrate), A4 (Panchanga writer), and A5 (Sensitive Points writer) end-to-end. Single Conductor session in main repo. Sub-agent-driven via parallel worktrees. JIT brief authoring (per-session, one turn each) to stay within output-token budget. Tracker sync handled autonomously by the running `tracker_sync_daemon.py` — Conductor only needs to update `session_queue.yaml`. Definition of Done: A3 schema applied + A4 and A5 writers shipping rows for native chart across all 5 ayanamshas + smoke passes.

## §1 — Learnings from prior workstream (applied)

1. **JIT brief authoring** — Conductor authors each session's brief immediately before spawning sub-agent (one brief per turn, ~80-200 lines), not all upfront. Avoids the 32K/200K output-token wall.
2. **Daemon-driven tracker** — `tracker_sync_daemon.py` is already running. It polls `session_queue.yaml` every 5s, reconciles `state.json`, pushes to GCS. The Conductor does NOT need to call `update_tracker.py` or `deploy_to_gcs.sh`. It only updates `session_queue.yaml` per session close. Sync is automatic.
3. **CLAUDE_CODE_MAX_OUTPUT_TOKENS** — restore to default (already unset by operator). Default cap is sufficient given JIT discipline.
4. **Strict worktree partitioning** — file-overlap discipline prevents merge conflicts.
5. **One cherry-pick at a time touches main** via `lock_main.sh` mutex.

## §2 — Scope

Three specs (each on disk):
- `00_ARCHITECTURE/A3_CHART_FACTS_SPEC_v1_0.md` — 147 fact_category enum (was 131 + 16 new from A5), 4 channel adapters, MV registry, chart_dashas separate to Prana depth, audit tables
- `00_ARCHITECTURE/A4_PANCHANGA_SPEC_v1_0.md` — 32 panchanga categories with full classical scope
- `00_ARCHITECTURE/A5_SENSITIVE_POINTS_SPEC_v1_0.md` — 30 sensitive-point categories with 6 universal enrichment fields + per-category two-pass methodology

## §3 — Operating model

**One Conductor session in the main repo.** Reads this plan + walks the session_queue. Per session:
1. Author session's CLAUDECODE_BRIEF.md inline (JIT, one turn)
2. Pick the right worktree (pre-created)
3. Copy brief into worktree's project root
4. Spawn Claude Code sub-agent with `--dangerously-skip-permissions`
5. Wait for sub-agent exit
6. Gate-check via `scripts/gate_check.sh`
7. On pass: auto-commit + lock_main + cherry-pick to main + push + (deploy if applicable)
8. **Update session_queue.yaml status=complete** — daemon picks it up within 5s and pushes tracker state
9. Advance to next session

Up to 4 concurrent worktrees (configurable; A3 substrate is sequential, A4 + A5 + Acc parallel-eligible).

## §4 — Pre-flight

```bash
# 0. Verify env
cd /Users/Dev/Vibe-Coding/Apps/Madhav
echo "${CLAUDE_CODE_MAX_OUTPUT_TOKENS:-default}"     # should be 'default'
git checkout main && git pull
git status                                            # clean

# 1. Daemon health (should be running from prior workstream)
ps aux | grep tracker_sync_daemon | grep -v grep      # must show daemon PID
# If missing, restart:
# nohup python3 /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/tracker_sync_daemon.py > /tmp/tracker_sync.log 2>&1 &

# 2. Create 4 worktrees
git worktree add -b feature/a3a4a5/a3-schema      ../MadhavA3       main
git worktree add -b feature/a3a4a5/a4-panchanga   ../MadhavA4Panch  main
git worktree add -b feature/a3a4a5/a5-sensitive   ../MadhavA5SP     main
git worktree add -b feature/a3a4a5/acceptance     ../MadhavA345Acc  main

# 3. DB proxy + infra
bash platform/scripts/start_db_proxy.sh &
gcloud auth list
pnpm install
pip install -r platform/python-sidecar/pipeline/requirements.txt
```

## §5 — Worktree topology

| Stream | Worktree | Scope | Sessions | Parallel-after |
|---|---|---|---|---|
| **A3** | MadhavA3 | Schema migrations + audit tables + CHART_FACTS_SCHEMA.json + MV registry + drift detector + wipe-rebuild | 8 | Day 1 start (sequential) |
| **A4** | MadhavA4Panch | Per-chart panchanga writer covering 32 categories | 10 | After A3-S1 to A3-S5 close |
| **A5** | MadhavA5SP | Per-chart sensitive points writer covering 30 categories | 12 | After A3-S1 to A3-S5 close, after G14 extension (run in A5 stream) |
| **ACC** | MadhavA345Acc | Smoke + acceptance + sealing + production deploy | 7 | After A4 + A5 close |

## §6 — Wave-by-wave session plan (~30 sessions)

### Wave 1 — A3 Schema Substrate (sequential, ~8 sessions)

| ID | Title | Files |
|---|---|---|
| A3-S1 | Migration: chart_facts extension (citation_ref + citation_human + verification_pass_status + audit columns) | `platform/migrations/<next>_chart_facts_extend.sql` |
| A3-S2 | Migration: chart_dashas table (separate, Prana depth, two-pass mandatory CHECK) | `platform/migrations/<next>_chart_dashas.sql` |
| A3-S3 | Migration: chart_facts_history + chart_facts_supersedence audit tables | `platform/migrations/<next>_chart_facts_audit.sql` |
| A3-S4 | Migration: 5 l25_* tables (l25_msr_signals, l25_cdlm_cells, l25_cgm_nodes, l25_cgm_edges, l25_rm_resonances, l25_ucn_digests) | `platform/migrations/<next>_l25_tables.sql` |
| A3-S5 | CHART_FACTS_SCHEMA.json full authoring (147 fact_categories + 4 channel adapters + per-key spec) | `00_ARCHITECTURE/CHART_FACTS_SCHEMA.json` |
| A3-S6 | MV registry (10 MVs from A3 §10) + creation scripts + sync-refresh in build pipeline | `platform/migrations/<next>_mvs.sql` |
| A3-S7 | drift_detector + schema_validator update to read new schema, enforce per-key value_type validation | `platform/scripts/governance/*.py` |
| A3-S8 | Wipe existing chart_facts; smoke schema apply via staging then production | (DB ops + smoke test) |

### Wave 2 — A4 Panchanga Writer (parallel after A3-S5 closes, ~10 sessions)

| ID | Title |
|---|---|
| A4-S1 | Panchanga writer scaffold + 5 limbs (tithi/vara/nakshatra/yoga/karana) |
| A4-S2 | Hora + choghadiya birth windows |
| A4-S3 | 9 inauspicious time windows (Rahu/Yama/Gulika kalam + Durmuhurta + Varjyam + Visha-ghati + Sashtighati + Yamakantaka + Krakaca) |
| A4-S4 | 9 auspicious time windows (Abhijit + Brahma + 3 sandhya + Amrit kaal + Vijaya + Godhuli + Nishita) |
| A4-S5 | Solar context (Sankranti/Ayana/Ritu) + calendrical (Purnimanta + Amanta + eras + 60-yr cycle) |
| A4-S6 | Astronomical (sunrise/sunset/all 9 graha rise/set + alt/az) |
| A4-S7 | Sun-Moon dynamics (pravesh + arambha timestamps for all limbs) |
| A4-S8 | Agni Vasa + 5-Panchaka classification (Roga/Raja/Agni/Chora/Mrityu) + Disha Shul + Shoonya Rashis |
| A4-S9 | Tara bala natal baseline (27 rows × per ayanamsha) + Chandra bala natal baseline (12 rows × per ayanamsha) |
| A4-S10 | A4 two-pass verification + integration tests + SMOKE: emit all categories for native chart × 5 ayanamshas |

### Wave 3 — A5 Sensitive Points Writer (parallel after A3-S5 closes, ~12 sessions)

| ID | Title |
|---|---|
| A5-S1 | G14 Saham library extension (50 → 70+ classical formulas) — operator step before A5-S4 can complete |
| A5-S2 | Upagrahas (6 classical) + Saturn-derived points (Gulika-Lahiri + Gulika-Hindu + Mandi + Yamaganda + Maandi) |
| A5-S3 | Esoteric bindus: Bhrigu Bindu + Yogi (2 variants) + Avayogi (2 variants) + Mrityu (3 variants) + Trisphuta family + Panchasphuta (2 variants) + Pranapada sphuta + Trikona dasha sphuta |
| A5-S4 | Sahams (70+ extended) — relies on A5-S1 |
| A5-S5 | Karakas (8-system with school variant Rahu in/out) + Karakamsa + Swamsa (12 rows) |
| A5-S6 | Arudha padas (12 ASC + 7 graha = 19 rows with UL/GL/DP aliases) |
| A5-S7 | Midpoints (54: 36 graha-graha + 9 ASC-graha + 9 MC-graha) |
| A5-S8 | KP Ruling Planets (5 entries) + KP Cuspal Significators (12 cusps × significator arrays) |
| A5-S9 | Aprakasha grahas (5 invisible) + Jaimini Brahma/Vishnu/Shiva (3) + Sri Yantra positions (3) |
| A5-S10 | Tajik points (Hadda 60-zone + Triraashipathi + Vargottama-specific) |
| A5-S11 | Lal Kitab special points (Pakka Ghar + arudhas + house anomalies via G41) + Maharsi sphutas (27 Nadi rishi attribution via G44) + Bhrigu Nadi points |
| A5-S12 | A5 two-pass verification + 6 universal enrichment fields (tolerance_arcsec, boundary flags, vargottama-of-point, formula provenance, cross-ayanamsha divergence) + SMOKE |

### Wave 4 — Acceptance + Close (sequential, ~7 sessions, no worktrees needed except ACC)

| ID | Title |
|---|---|
| ACC-S1 | Smoke: build native chart end-to-end, all 5 ayanamshas; verify ~600 A4 rows + ~13K A5 rows per chart |
| ACC-S2 | MV refresh validation: all 10 MVs populate within build_step duration |
| ACC-S3 | verification_pass_status spot-check (sample 100 rows; verify two_pass_verified or classical_match counts match expectations per spec) |
| ACC-S4 | Red-team for divergent_flagged rows: ensure none reach production; halt diagnostics work |
| ACC-S5 | answer:eval delta measurement (expect modest improvement on B.11 holistic-read floor) |
| ACC-S6 | Version bumps (CLAUDE.md, CANONICAL_ARTIFACTS, PROJECT_ARCHITECTURE if affected) + sealing artifact `A3_A4_A5_CLOSE_v1_0.md` |
| ACC-S7 | Final production deploy + 10-min log watch + native sign-off |

## §7 — Session lifecycle

Same as prior plan but with daemon-driven tracker:

1. Conductor authors brief JIT (one Edit/Write per turn)
2. Copies brief to worktree's CLAUDECODE_BRIEF.md
3. Spawns sub-agent via Bash: `claude --dangerously-skip-permissions ... < /dev/null`
4. Waits for sub-agent exit
5. Runs `scripts/gate_check.sh <session_id>`
6. On pass: `auto_commit.sh` → `lock_main.sh` → `auto_cherry_pick.sh` → `unlock_main.sh` → `git push origin main` → (optionally `deploy_and_smoke.sh`)
7. **Updates session_queue.yaml: session_id.status = complete** (one line edit)
8. Daemon picks up within 5s, reconciles state.json, pushes GCS, tracker reflects within ~10s end-to-end
9. Conductor moves to next session

**Conductor does NOT call update_tracker.py or deploy_to_gcs.sh directly.** Daemon handles it. This is the key learning.

## §8 — Safety rails (auto-enforced)

| Rail | Trigger |
|---|---|
| Migration staging-first | Every A3-S* migration; rollback on smoke fail |
| Canary deploy on Cloud Run | ACC-S7 final deploy; 10% → 5-min log watch → auto-promote or auto-rollback |
| CI gates | Every push; halt cherry-pick if CI red |
| Hard gates G1-G6 | Pre-merge check on every cherry-pick |
| Two-pass verification | Mandatory on A4 inauspicious windows / A5 all rows; divergent_flagged halts build |
| answer:eval regression | After Wave 4 ACC-S5; halt seal if b11 drops > 5% |
| One cherry-pick at a time | lock_main.sh mutex |
| Halt-all kill switch | `bash scripts/halt_all.sh` |
| Daemon health monitoring | If daemon dies, Conductor logs but does NOT halt — sync gap closes on next restart |

## §9 — Halt & resume

Same as prior plan. State preserved in `session_queue.yaml` + `state.json`. Resume: re-launch Conductor; reads queue, picks up from last incomplete session.

## §10 — Operational commands

### Launch
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
bash 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/launch_conductor.sh
# OR paste the kickoff prompt into Claude Code chat
```

### Monitor
```bash
# Live tracker (production)
open https://storage.googleapis.com/marsys-tracker-public/index.html

# Daemon log
tail -f /tmp/tracker_sync.log

# Conductor stdout
tail -f 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/CONDUCTOR_RUN.log

# Daemon health
ps aux | grep tracker_sync_daemon | grep -v grep
```

### Halt
```bash
bash 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/halt_all.sh
```

### Resume
```bash
bash 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/resume.sh
```

## §11 — Definition of Done

The A3+A4+A5 workstream is COMPLETE when:

1. All ~30 sessions show `status: complete` in `session_queue.yaml`
2. Tracker reflects A3, A4, A5 brief=locked AND impl=deployed
3. Native chart_id `362f9f17-95a5-490b-a5a7-027d3e0efda0` has:
   - chart_facts rows for all 147 fact_categories with chart_id non-NULL
   - ~600-800 panchanga rows per ayanamsha × 5 = ~3,000-4,000 panchanga rows total
   - ~2,600 sensitive-point rows per ayanamsha × 5 = ~13,000 total
   - chart_dashas populated to Prana depth (subset for SMOKE; full population is A7 territory)
4. All 10 MVs refresh successfully on build close
5. Two-pass verification status counts match spec expectations
6. 8 hard gates GREEN
7. answer:eval baseline run (no regression)
8. Sealing artifact `A3_A4_A5_CLOSE_v1_0.md` committed
9. Final production deploy clean
10. Native sign-off captured in tracker activity

## §12 — References

- `00_ARCHITECTURE/A3_CHART_FACTS_SPEC_v1_0.md`
- `00_ARCHITECTURE/A4_PANCHANGA_SPEC_v1_0.md`
- `00_ARCHITECTURE/A5_SENSITIVE_POINTS_SPEC_v1_0.md`
- `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/IMPLEMENTATION_PLAN_v1_0.md` (prior workstream pattern)
- `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/tracker_sync_daemon.py` (running)
- `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/tracker/state.json` (truth)
- `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/session_queue.yaml` (Conductor's queue — append A3-S* / A4-S* / A5-S* / ACC-S* sessions)

---

*End of IMPLEMENTATION_PLAN_A3_A4_A5_v1_0.md — ready for Conductor execution.*
