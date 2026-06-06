# Cockpit Consolidated Phase Log

Branch: `feature/cockpit-v2-three-views`
Brief: `ANTIGRAVITY_PASTE_COCKPIT_CONSOLIDATED_PHASES.md`

| Phase | Status | Commit SHA | Notes |
|-------|--------|------------|-------|
| Phase 1: render-layer | COMPLETE | — | Dev server ready at 220ms. Native confirmed Incognito render: hero shows, layer panels populated. |
| Phase 2: date format + top bar | COMPLETE | abdc562e | formatDate() utility; birthDate → dd-MMM-yyyy in CockpitHeader; breadcrumb + ChartSwitcher hidden on /build via usePathname(). |
| Phase 3: asset-state correctness | COMPLETE | 70325af7 | Root cause: Cause 1+3 — 5 assets have is_active=false; UI mapped to "INACTIVE". Fixed to "NOT MIGRATED" neutral label. |
| Phase 4: schema migration 171 | COMPLETE | 2bc93126 | build_runs + build_run_assets + asset_throughput (chart_id, state, built_against_*, last_built_at, last_error) applied to prod. |
| Phase 5: plan resolver + staleness | COMPLETE | 357d7f75 | plan.ts + staleness.ts; 24 vitest tests pass. |
| Phase 6: API endpoints | COMPLETE | ed2ae9f9 | POST plan, POST runs, POST pause/resume/stop, GET active — all super_admin gated. |
| Phase 7: build UI components | COMPLETE | d0128385 | BuildActionButton (auto-label: Build/Update/Rebuild) + PlanModal + CascadeBanner + PauseStopGroup wired at global/layer/asset scopes. useActiveRun polls every 5s. | POST /api/cockpit/plan, POST /runs, POST /runs/[id]/{pause,resume,stop}, GET /runs/active — all super_admin gated. | plan.ts + staleness.ts pure functions; 24 vitest tests pass (empty DAG, linear chain, branching DAG, cycle detection, all 4 actions, scopes, null estimates). | Root cause: Cause 1+3 — 5 assets (panchanga_almanac, balatva, suksmabindu, sade_sati, tajaka) have is_active=false; UI mapped that to "INACTIVE" chip. Fixed to "NOT MIGRATED" neutral label. asset_throughput has no chart_id/state yet (Phase 4 adds those). |
| Phase 8: orchestrator wiring | DEFERRED | — | Orchestrator source outside this repo. Cloud Run Job: `brahma-build-pipeline-job` (asia-south1), image: `asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:latest`. No Dockerfile or pipeline source found in platform/. Cowork to scope a separate brief for the orchestrator repo covering: (1) accept --run-id arg, (2) poll pause/stop signals, (3) mark downstream stale post-write. Watchdog also missing (separate brief). |
| Phase 9: E2E verification | COMPLETE (partial) | — | AC1 PASS — build_run INSERT succeeds in prod (chart_id/scope/action/state correct; build_run_assets 3 rows queued). AC2 PASS at schema level — pause_requested_at sets, cleared on resume, state transitions correct; full orchestrator-driven round-trip blocked by Phase 8 DEFERRED. AC3 PASS — stop_requested_at sets, state→stopped confirmed in prod. AC4 BLOCKED — no stale assets (orchestrator not yet wired to mark downstream stale; Phase 8 DEFERRED). AC5 BLOCKED — CascadeBanner component present; no stale assets to trigger it (blocked by AC4). Test run cleaned up: state=stopped, ended_at set. |
