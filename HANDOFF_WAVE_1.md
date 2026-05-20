# HANDOFF — Wave 1 Close

**Date:** 2026-05-20
**Authored by:** Session 4C-9 (Wave 1 close session)
**Branch:** `feature/phase-4c-panchang`
**Status:** WAVE_1_COMPLETE — awaiting native split-PR action

---

## §1 — Wave 1 Outcome Summary

Phase 4C (Panchang Module) Wave 1 is complete. Nine sessions (4C-0 through 4C-9) ran
concurrently with M5-A and delivered a production-ready Panchang instrument on the
`feature/phase-4c-panchang` branch.

**What shipped (on branch, ready to merge):**

- `panchang_engine` v1.0.0-S3 — Swiss Ephemeris-powered; 5 angas, special yogas,
  planetary positions. 30/30 Drik parity. 230 sidecar tests PASS.
- `query_panchanga` RetrievalTool — engine-direct; registered as tool 29; planner
  R-TC and R-PCI rules; `expose_to_chat_confirmed: true`.
- `/panchang` UI surface — PrimaryStrip (5 angas + timings), PlanetaryGrid, SpecialYogasList,
  Personalise overlay (Tara Bala + Chandra Bala for any chart).
- Muhurat Finder — 6 curated events (Vivah, Griha Pravesh, Property Purchase, Vyapara,
  Yatra, Mantra Initiation); YAML-tunable weights; 90-day date range. Acharya CANARY PASS.
- iCal export — single-day `.ics` download + HMAC-signed 90-day subscribable feed.
- AskMadhavLink — ghost-icon deep links from any panchang row to Madhav chat; 10 KB
  context injection; planner bypass rule when context block present.
- Observatory telemetry — `PanchangLatencyPanel` + `PanchangCachePanel` in Observatory dashboard.
- IS.8(b) red-team PASS 5/5. `PHASE_4C_CLOSE_v1_0.md` sealed.
- Conductor queue: 11 entries, all passed or skipped. Queue closed.

**What is deferred (not blocking merge):**

- 4C-2 SQL cache layer — gated on Phase 4B (MEAN_NODE rebuild + Migration 059).
  `PANCHANG_DAILY_v1_0` status is `CURRENT_ENGINE_DIRECT`; will become `CURRENT` after 4C-2.
- v2 polish items — in `00_ARCHITECTURE/PHASE_4C_FOLLOWUPS_v1_0.md`.
- Real acharya panel review of Muhurat scoring — M10-territory post-merge.

---

## §2 — Split-PR Procedure (run this NOW)

The Conductor was built on `feature/phase-4c-panchang` for convenience. It must
reach `main` BEFORE Wave 2 sessions run. The solution is the **split-PR strategy**:
cherry-pick Conductor commits first (PR 1), then open the Phase 4C application-code
PR (PR 2).

### Step A — Cherry-pick Conductor → PR 1

```bash
# From the Madhav clone (canonical main-branch repository)
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout main
git pull origin main

# Create the migration branch
git checkout -b feature/conductor-to-main

# Identify Conductor-only commits on the panchang branch
git log origin/feature/phase-4c-panchang --oneline \
  -- 00_ARCHITECTURE/CONDUCTOR/ \
     00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_CONDUCTOR_S0_v1_0.md

# NOTE: Verify every commit listed touches ONLY 00_ARCHITECTURE/CONDUCTOR/ paths.
# The list shows newest-first; cherry-pick in REVERSE order (oldest → newest).
# Expected commits (verify against the output above):
#   CONDUCTOR-S0 initial build commits
#   SMOKE-S0 heartbeat commit (ef3d14d or nearest equivalent)
#   Queue APPROVE entries that touch only CONDUCTOR/ paths

# Cherry-pick oldest→newest
git cherry-pick <oldest-sha> ... <newest-sha>

# Verify
python3 00_ARCHITECTURE/CONDUCTOR/validate_queue.py   # must exit 0
ls 00_ARCHITECTURE/CONDUCTOR/smoke/SMOKE_HEARTBEAT.md # must exist

# Push and open PR
git push -u origin feature/conductor-to-main
gh pr create \
  --title "Conductor — autonomous session orchestrator (Wave 1 → main)" \
  --body "$(cat <<'EOF'
## Summary

- Adds the MARSYS-JIS Conductor: autonomous session orchestrator for Wave 1 (Phase 4C)
- Orchestrator walks session_queue.yaml, spawning sub-agents per brief, gated on shell tests
- Smoke test (SMOKE-S0) PASSED during CONDUCTOR-S0 session on 2026-05-19
- All Conductor files live in 00_ARCHITECTURE/CONDUCTOR/ — no application code included

## Contents

- CONDUCTOR_PROMPT_v1_0.md — orchestrator system prompt
- session_queue.yaml — 11-entry Wave 1 queue (all passed or skipped)
- CONDUCTOR_LOG.md — run history (SMOKE-S0 + all Wave 1 sessions recorded)
- CONDUCTOR_HALT_LOG.md — halt log
- schemas/ — JSON schemas for queue entries and halt entries
- validate_queue.py — queue validation script (exits 0 on this branch)
- smoke/ — smoke test brief + queue + SMOKE_HEARTBEAT.md
- README.md — operator documentation
- WAVE_2_MIGRATION_NOTE.md — cherry-pick procedure (this document)
- CLAUDE_MD_AMENDMENT_PROPOSAL.md — deferred CLAUDE.md amendment

## Test plan

- [x] validate_queue.py exits 0
- [x] SMOKE-S0 heartbeat commit exists on feature/phase-4c-panchang
- [x] All cherry-picked commits touch ONLY 00_ARCHITECTURE/CONDUCTOR/ paths
- [ ] Reviewer verifies no application code leaked into cherry-picked commits

🤖 Generated with Claude Code (CONDUCTOR-S0 + 4C-9, 2026-05-19/20)
EOF
)"
```

### Step B — Merge PR 1, then apply CLAUDE.md amendment

After PR 1 merges to main:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout main && git pull

# Verify Conductor on main
ls 00_ARCHITECTURE/CONDUCTOR/
python3 00_ARCHITECTURE/CONDUCTOR/validate_queue.py
ls 00_ARCHITECTURE/CONDUCTOR/smoke/SMOKE_HEARTBEAT.md
```

**Note:** `CLAUDE.md §E` already reflects the Conductor workstream (applied in 4C-9
on the feature branch, v2.7). When the Phase 4C PR merges to main, the amendment
arrives automatically — no separate follow-up session needed. This differs slightly
from the WAVE_2_MIGRATION_NOTE §5 plan (which anticipated a separate amendment session),
but the net result is the same: Conductor is visible in CLAUDE.md §E on main after both
PRs merge.

### Step C — Open Phase 4C close PR (PR 2)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang
git push -u origin feature/phase-4c-panchang   # if not already pushed

# From Madhav or any clone:
gh pr create \
  --title "Phase 4C — Panchang Module (Wave 1 complete)" \
  --head feature/phase-4c-panchang \
  --base main \
  --body "$(cat <<'EOF'
## Summary

Phase 4C delivers the MARSYS-JIS Panchang Module: daily panchang display, Muhurat
Finder, iCal export, personalised overlays (Tara Bala / Chandra Bala), and
Ask-Madhav deep links from any panchang datum to the Madhav chat interface.

## What's in this PR

- **panchang_engine v1.0.0-S3** — Swiss Ephemeris; 30/30 Drik parity; 230 sidecar tests
- **query_panchanga RetrievalTool** — engine-direct; planner R-TC + R-PCI rules
- **/panchang UI** — PrimaryStrip, PlanetaryGrid, SpecialYogasList, Personalise overlay
- **Muhurat Finder** — 6 events, YAML weights, 90-day range; acharya CANARY PASS
- **iCal export** — single-day download + HMAC-signed 90-day subscribable feed
- **AskMadhavLink** — context injection + planner bypass; 10 KB budget guard
- **Observatory panels** — PanchangLatencyPanel + PanchangCachePanel
- **IS.8(b) red-team** — PASS 5/5; finding docs in 00_ARCHITECTURE/RED_TEAM/
- **CLAUDE.md v2.7** — Conductor as sixth workstream; Phase 4C WAVE_1_COMPLETE
- **CAPABILITY_MANIFEST** — PANCHANG_DAILY_v1_0 status CURRENT_ENGINE_DIRECT
- **PHASE_4C_CLOSE_v1_0.md** — Wave 1 close artifact

## Deferred (not blocking)

- 4C-2 SQL cache layer (gated on Phase 4B — MEAN_NODE rebuild)
- v2 polish items (PHASE_4C_FOLLOWUPS_v1_0.md)
- Real acharya panel review (M10-territory)

## Test plan

- [x] panchang_engine: 230/230 pytest PASS
- [x] TypeScript UI: 151/151 jest PASS (panchang suite)
- [x] IS.8(b) red-team: 5/5 PASS
- [x] mirror_enforcer: exit 0
- [x] schema_validator: exit 0
- [x] drift_detector: exit 0
- [x] validate_queue: exit 0

🤖 Generated with Claude Code (Wave 1, sessions 4C-0 through 4C-9, 2026-05-19/20)
EOF
)"
```

---

## §3 — Wave 2 Entry Points

After both PRs land on main, choose your next battle:

### Option A — Start Wave 2 Conductor queue (M5-A, Phase 4B, Phase 4D)

Author new briefs + queue entries for:
- M5-A next session (per `PHASE_M5_PLAN_v1_0.md §3 M5-A`)
- Phase 4B (sunrise derivation + MEAN_NODE rebuild + Migration 059) — unblocks 4C-2
- Phase 4D (post-4B ephemeris accessibility expansion)

The Conductor queue (`session_queue.yaml`) has `wave_1_status: COMPLETE`. Append a
`wave_2_sessions:` section or create a new `wave_2_queue.yaml`.

### Option B — Phase 4B immediately (unblocks 4C-2)

Open a fresh Cowork session on the Madhav clone (main branch after PRs merge):
- Read `00_ARCHITECTURE/PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md §4B`
- Author `CLAUDECODE_BRIEF_PHASE_4B_v1_0.md`
- Execute: Migration 059, MEAN_NODE rebuild, sunrise derivation
- After 4B closes: flip `PANCHANG_DAILY_v1_0` to `CURRENT` with `runtime_path: cached`

### Option C — Production user testing of /panchang

Deploy the branch and test /panchang live. The Personalise overlay requires a live
database connection to fetch chart data. Start the sidecar:

```bash
cd platform/python-sidecar/panchang_engine
PYTHONPATH=. python3 ../main.py   # or uvicorn main:app --port 8001
```

Navigate to `/panchang` in the running app. Try:
- Default view (Bhubaneswar, today)
- Personalise → select native chart → verify Tara/Chandra badges
- Muhurat Finder → Vivah → pick a date range → verify scored results
- Export to Calendar → download .ics → import to calendar app
- Subscribe to feed → copy URL → paste in calendar app
- AskMadhavLink → click a row icon → verify context arrives in Madhav chat

---

## §4 — Open Items Inventory

| Item | Owner | Resolution path |
|---|---|---|
| 4C-2 SQL cache + backfill | Engineering | After Phase 4B closes |
| v2 polish items | Engineering | `PHASE_4C_FOLLOWUPS_v1_0.md` |
| Acharya panel real review | Native / M10 | Post-merge, production use data |
| CLAUDE.md amendment on main | Auto (via PR 2 merge) | No separate action needed |
| Wave 2 queue authoring | Conductor / Cowork | Fresh briefs per §3 above |
| Observatory AC.3/AC.4/AC.6 | Engineering | Per `OBSERVATORY_PLAN_v1_0.md §14` |

---

## §5 — Key Files

| File | Purpose |
|---|---|
| `00_ARCHITECTURE/PHASE_4C_CLOSE_v1_0.md` | Wave 1 close artifact (comprehensive) |
| `00_ARCHITECTURE/PHASE_4C_FOLLOWUPS_v1_0.md` | Deferred v2 polish items |
| `00_ARCHITECTURE/CONDUCTOR/WAVE_2_MIGRATION_NOTE.md` | Cherry-pick procedure (expanded) |
| `00_ARCHITECTURE/CONDUCTOR/session_queue.yaml` | Wave 1 queue (all closed) |
| `00_ARCHITECTURE/RED_TEAM/RT_4C_*_FINDING.md` | IS.8(b) red-team finding docs |
| `platform/python-sidecar/panchang_engine/` | Engine source + tests |
| `platform/src/app/panchang/` | UI components |
| `platform/src/app/observatory/` | Observatory panels (including panchang panels) |

---

*End of HANDOFF_WAVE_1.md — authored 2026-05-20, session 4C-9.*
*Conductor banner: QUEUE COMPLETE — Wave 1 closed.*
