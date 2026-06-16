---
artifact: CLAUDECODE_BRIEF_WS1_AUTONOMOUS_ACTIVATION_v1_0.md
canonical_id: CLAUDECODE_BRIEF_WS1_AUTONOMOUS_ACTIVATION
version: 1.0
status: READY_FOR_EXECUTION
project_codename: Brahma — WS-1 Autonomous Activation (S2 + S3 + Step 0.5)
authored_by: Claude (Cowork) 2026-06-04
authored_for: Claude Code extension in Google Antigravity IDE — Conductor mode
governs_under: BUILD_GUARANTOR_SWARM_CHARTER + BUILD_GUARANTOR_AUTONOMOUS_MODE + RUNTIME_GUARDIAN_MODE
predecessor: WS-1 S1 commit `afe5f971` on `feature/ws1-drivable-portal`
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavWS1 (create via `git worktree add`)
branch: feature/ws1-drivable-portal (continues from S1)
no_backup: true
human_gates: NONE (per AUTONOMOUS_MODE §F amendment, Brahma autonomy 2026-06-04)
---

# WS-1 Autonomous Activation — S2 + S3 + Step 0.5

The remainder of WS-1 (S2 cockpit/SSE/Inspector, S3 consult+admin, plus the deferred Step 0.5 Turbopack blocker) runs as one Conductor session under full AUTONOMOUS_MODE. The Conductor walks the queue; the 12-role swarm handles authoring → code → deploy → runtime; merge-to-main is automatic on green ACs. No paste prompts per sub-step — the queue IS the prompt.

## §1 Setup (CC executes once)

```bash
# Worktree
cd /Users/Dev/Vibe-Coding/Apps
git -C Madhav worktree add ../MadhavWS1 feature/ws1-drivable-portal
cd MadhavWS1
git pull origin feature/ws1-drivable-portal

# Bot identity (per AUTONOMOUS_MODE §E — least privilege, project-scoped)
# Confirm the bot account `brahma-swarm-bot@madhav-astrology.iam.gserviceaccount.com` exists with:
#   - Cloud Run admin (deploy only; not delete/replace existing services)
#   - Cloud SQL Client + writer
#   - Secret Manager accessor
#   - Repo: merge-to-main allowed via branch protection rule "bot OR human"
gcloud iam service-accounts describe brahma-swarm-bot@madhav-astrology.iam.gserviceaccount.com \
  || echo "BOT IDENTITY MISSING — provision before queue start"

# Conductor queue setup
mkdir -p 00_ARCHITECTURE/CONDUCTOR/ws1
cat > 00_ARCHITECTURE/CONDUCTOR/ws1/session_queue.yaml <<'EOF'
wave: ws1
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavWS1
branch: feature/ws1-drivable-portal
mode: AUTONOMOUS_MODE
max_run_budget_usd: 5000
max_spend_per_asset_usd: 300
sessions:
  - id: step-0.5-turbopack
    role: Śilpī (lead) + Nirīkṣaka (diagnose) + Pramāṇa (verify)
    scope: |
      Diagnose the Turbopack/python-sidecar venv symlink that blocks `npm run build` (web).
      Hypothesis: python-sidecar/.venv symlinks confuse Turbopack file tracing.
      Fix: smallest patch that unblocks — likely a next.config.ts experimental.outputFileTracingExcludes
      entry, or a .next-ignore pattern, or moving the venv outside the trace root.
    acceptance:
      - `cd platform && npm run build` exits 0 with "Compiled successfully"
      - No new TS errors vs baseline
    parallel_safe: false  # blocks S2 deploy verification

  - id: s2-cockpit-sse-inspector
    role: full swarm (Racayitā / Śilpī / Review×5 / Pratiṣṭhā / Drashta / Pramāṇa / Darpaṇa)
    scope: |
      Per BRAHMA_BUILD_UX_SPEC §5 (Layer Tower), §6 (push/SSE), §7 (Asset Inspector).
      Components: LayerTower (bottom-up, Brahmagyan bedrock, Mīmāṃsā always-active band),
      OverallProgress rebased to L0–L5, useChartBuildState (server-side via SSE not polling),
      AssetInspector right-panel (data sample + provenance + gate verdict + live tool state).
      Endpoints: GET /api/build/events/[buildId] (SSE), GET /api/build/pyramid-layers
      (S1 deferred this), per-asset GET /api/assets/[chart_id]/[asset_key] for Inspector.
      Also: chart_created toast component (S1 deferred); DCB-001 kala_timeline psycopg fix;
      DCB-004 life_events NOT NULL fix.
    acceptance:
      - BRAHMA_BUILD_UX_SPEC §14.3 (live updates), §14.4 (amber shortfall), §14.5 (Inspector)
      - Drashta drives a real build via the portal; tower fills live; no manual refresh needed
      - Per-asset Inspector returns row counts, provenance, gate verdict, tool live state
    parallel_safe: false  # depends on step-0.5 for deploy verification

  - id: s3-consult-admin
    role: full swarm
    scope: |
      Per BRAHMA_BUILD_UX_SPEC §9 (Progressive Consult) + §10 (admin Brahmagyan view).
      ConsumeChatV2 capability gate (only offer prompts groundable by the verified layer's tools).
      "Consult now (Gaṇita)" affordance on band verify.
      New /admin/foundation route for the one-time Brahmagyan view (per spec §10 — single-band
      tower + Infrastructure checklist).
    acceptance:
      - BRAHMA_BUILD_UX_SPEC §14.7 (Consult progressively capable; no ungroundable suggestions)
      - §14.8 (Brahmagyan as global bedrock for clients; only builds on admin screen)
    parallel_safe: true  # can run alongside Step 0.5 if S2 holds it up

  - id: wave-close
    role: Sūtradhāra + Pramāṇa + Pratiṣṭhā
    scope: |
      Final WS-1 AC sweep across AC-1 through AC-12 (brief §1 + §5).
      Open PR; CI green; swarm merges per AUTONOMOUS_MODE §B (no human gate).
      Tag `ws1-drivable-portal-complete`.
    acceptance:
      - All 12 ACs green in the PR scorecard
      - Six CI gates pass (typecheck, unit-tests, secret-scan, naming-lint, governance-gates, planner-regression)
      - PR auto-merged; tag pushed
EOF
```

## §2 Activation (CC kicks the Conductor)

```bash
# Activate the Conductor per 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_v1_0.md
# The Conductor reads session_queue.yaml, spawns one sub-agent per session,
# governs each via AUTONOMOUS_MODE rails.
# Use the self-chaining driver (AUTONOMOUS_MODE §D) so context-budget exhaustion doesn't halt.

# Read the conductor prompt
cat 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_v1_0.md

# Launch
# (CC's mechanism for spawning the Conductor lives in its slash-command + sub-agent toolkit;
# operator runs whatever the local CC + Antigravity stack provides for conductor kickoff.)
```

## §3 Native's role during the run

Watch when convenient via:
- Live cockpit at `madhav.marsys.in/clients/[id]/build` — once S2 lands, observable Layer Tower
- `00_ARCHITECTURE/CONDUCTOR/ws1/CONDUCTOR_LOG.md` — append-only run log
- Smṛti audit trail in `00_ARCHITECTURE/CONDUCTOR/ws1/smriti/` per session

**Hard stops:** none synchronous. The wave runs to completion without native intervention. All exceptional events route through `00_ARCHITECTURE/AUTONOMY_RESILIENCE_PATTERN_v1_0.md`: Tier-1 auto-resolved by the swarm (deep-fix escalation, disposition classifier, auto-budget raise, engine self-repair); Tier-2 decided + Smṛti-logged; Tier-3 (catastrophic-runaway $5k cap only) emits async notification per pattern §E. Vimarśaka post-merge audits run asynchronously after every merge; class-1 findings route through the Tier-1 Severity Remediator.

## §4 Wave-complete signal

Tag `ws1-drivable-portal-complete` on main triggers the WS-1 close handoff. Cowork (me) then writes the WS-1 close artifact summarizing what shipped, what was deferred, and what the next wave inherits.

---

*End of WS-1 Autonomous Activation. Worktree + bot + queue + driver → swarm runs to PR-merged tag.*
