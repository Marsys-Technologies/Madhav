---
wave: D-3
lifecycle_step: 3  # SPAWN dispatched (native GO 2026-07-18): T-0 + T-1 implementers launched
                   # in isolated worktrees, background. ka_avadhi disposition classified live
                   # as (a) stale-build/current-population gap (NOT CR-41's forward-horizon
                   # shape — CR-41 rows exist-but-historical; here zero rows at ANY date range,
                   # even fully historical 2010-2020) and scoped rebuild dispatched via the
                   # documented non-session fallback. IMPLEMENT ∥ VERIFY in flight for T-0/T-1;
                   # verifiers not yet spawned (awaiting implementer claims).
status: ACTIVE
cycle: 1
brief_bound: true
bind_record: 00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/BIND_D-3.md
rollback_pin:
  image_sha:
    amjis-web: e8b1047f56a06591352dbb748373a59b6dea5715
    amjis-mcp: 8c3b21a9afa88934e621a9d525f460a72ed5ca52
    amjis-sidecar: 6487694fe70635e12c84746443ee2359c51b447d
    brahma-build-pipeline-job: 6487694fe70635e12c84746443ee2359c51b447d
  abhisek_build_id: b84c3797-b64a-4956-a431-5f4ccdf9ee55
adjudications:
  - {dr: DR-10, dis: DIS.023, subject: "within-period peak model", ruling: "pratyantar-lord decomposition is classical default; midpoint-triangle DEPRECATED (never bare-served); peak_basis provenance mandatory; transit-kernel supersedes both where computed", recorded: true}
  - {dr: DR-11, dis: DIS.024, subject: "T-0 retrodiction-gate thresholds v1", ruling: "±45d window / top-decile salience / ≥50% blind-battery hit-rate vs shuffled-birth control; DR-revisable only; anti-gaming rule binding (no primary-runner-only green)", recorded: true}
  - {dr: DR-12, dis: DIS.025, subject: "D-4 peak-model adjudication hook", ruling: "D-4 battery MUST score midpoint-triangle vs pratyantar-lord vs transit-kernel against LEL corpus; data retires the loser; forward-binding, inherited by D-4 Binder at its own bind", recorded: true}
carried_item_dispositions:
  - {item: "orchestrator run-rollup race", verdict: "diagnosis confirmed current; §N.2 STOP not triggered (run-machinery-owned, no WriterBase contract change)", disposition: "first-agenda D-3 lane, platform-owned: (A) run-start rollup reconciliation from build_run_assets children, (B) watchdog reconcile-to-truth instead of blind-fail. Both idempotent.", status: "pending spawn as first lane"}
  - {item: "kala_avadhi hollow timeline", verdict: "REVISED — original (a)/(b) classification was itself premature. Rebuild-dispatch agent found via direct DB query (live pipeline DB): kala_avadhi=1571 rows / kala_convergence=1580 / kala_darshana=750 / kala_obstruction=679 for 482012f1, computed_at 2026-07-17T01:47:24Z (build b84c3797, asset_set rebuild, already ran and completed cleanly ~21h before this wave opened). Vimshottari coverage spans 1949-2100. Data was NEVER missing. Underlying capability endpoints (query_dasha_dossier/query_convergence_windows/query_obstruction_periods via /api/retrieval/capability, same principal as the MCP connector) return real rows fine (43/560/679 for 2010-2027).", root_cause: "CODE BUG, not a data gap: platform-mcp/src/tools/retrieval/kala_temporal.ts fetchCapabilityRows() double-content-unwrap defect. /api/retrieval/capability's real response shape is {ok, content:{content:{rows:[...]}, is_error}} (wrapped twice) but fetchCapabilityRows() only unwraps once (reads data.content.rows instead of data.content.content.rows), so rows is always undefined -> silently falls back to [] while still reporting ok:true. Systemic to EVERY chart kala_temporal_bundle is called for, not Abhisek-specific.", disposition: "NO rebuild dispatched (agent correctly aborted once the true cause was found — a rebuild would have been a no-op and risked a false-positive 'fixed' read). One-line fix identified: const rows = (content as {content?:{rows?:unknown}}).content?.rows — applies to all 3 fetchCapabilityRows call sites in computeKalaTemporalBundle plus the snapshot sub-calls sharing the helper. NOT yet applied — new finding, outside the T-0/T-1 spawn scope authorized this cycle; routing to native/conductor for disposition (fold into T-6 now vs. quick standalone hotfix lane) rather than unilaterally spawning new work.", status: "DIAGNOSED, NOT FIXED — awaiting disposition"}
rebuild_scope_ruling:
  scope: pending  # full-wave scope not yet computed; the kala_avadhi scoped rebuild above is a
                  # separate pre-spawn action, not the wave's own T-lane rebuild (lifecycle step 6)
  expected_per_brief: "L3 convergence assets + Taranga service; L2 read-only (no L2 rebuild) — BRIEF_D3 §8.2 per-wave expected scope"
lanes:
  - {lane: T-0, branch: wave/D-3/T-0, worktree: /Users/Dev/Vibe-Coding/Apps/Madhav-wave-D3-T0, base: origin/main@b536e13b, status: implementing, model: sonnet}
  - {lane: T-1, branch: wave/D-3/T-1, worktree: /Users/Dev/Vibe-Coding/Apps/Madhav-wave-D3-T1, base: origin/main@b536e13b, status: implementing, model: sonnet}
integration_branch: null
deploy: {done: false}
gate: {run: false}
updated_at: "2026-07-18T00:05+05:30"
resumed_at: null
