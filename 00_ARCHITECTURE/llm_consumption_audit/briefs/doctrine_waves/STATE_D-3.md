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
  - {item: "kala_avadhi hollow timeline", verdict: "confirmed live (timeline_count:0, active_dasha:null on 482012f1 across BOTH forward 2026-2027 AND fully-historical 2010-2020 ranges) — CLASSIFIED (a) stale-build/current-population gap, NOT CR-41's forward-horizon shape (CR-41 = rows exist, all historical, zero forward-overlap; here zero rows at ANY date, so CR-41's supersession disposition does not apply and does not block this rebuild)", disposition: "scoped rebuild (asset_set: ka_avadhi + DAG dependents, computed via asset_registry.depends_on) dispatched via documented non-session fallback (Secret Manager pipeline DB URL + gcloud run jobs execute, per REMEDIATION_RUN_LEDGER §8 precedent) — NOT the product session-gated /api/cockpit/runs route", status: "DISPATCHED — agent in flight, result pending"}
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
