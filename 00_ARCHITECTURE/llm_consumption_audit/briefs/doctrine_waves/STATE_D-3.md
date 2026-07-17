---
wave: D-3
lifecycle_step: 5  # DEPLOY complete (native GO 2026-07-18): PR #602 (wave/D-3/integration ->
                   # main) merged squash SHA 11377530892799afd8015d3ee9b6ec68efeb0c0d, full CI
                   # green (incl. the ~8.5min Governance Gates pytest step), Deploy to Cloud Run
                   # workflow completed success. Live SHA confirmed via gcloud describe:
                   # amjis-web AND amjis-mcp both @ 11377530... Rebuild determination: NOT
                   # NEEDED — T-1 diff (get_av_transit_gating.ts/index.ts/register_p1_aliases.ts/
                   # test) contains zero migrations and zero new writers, pure read-serving code
                   # over already-populated chart_facts categories; kala_temporal.ts hotfix is
                   # serving-only. No R-5/§8.2 rebuild trigger applies.
                   #
                   # POST-DEPLOY LIVE READS (both run against the deployed connector):
                   # (1) PRIMARY/hotfix routing — kala_temporal_bundle(482012f1, fwd 1yr):
                   #     timeline_excerpt now 7 rows (was 0), timeline_count:7, active_dasha
                   #     resolved (Mercury MD/Saturn AD), kala_readiness.score=0.7. POPULATES ->
                   #     the double-unwrap WAS the root cause. HOTFIX DISPOSITION = KEEP (critical
                   #     path for T-2/T-5). CR-41 writer-supersession disposition is UNCHANGED/
                   #     SEPARATE (this was a serving bug, not the writer's forward-horizon
                   #     defect) — stood down as a rebuild question per the native's routing.
                   #     Note: convergence_windows/obstructions still 0 in this window — not
                   #     probed further, outside this check's scope.
                   # (2) REGRESSION GUARD — judgment_query(wealth, 482012f1): Dhana Yoga
                   #     (dhana_yoga_2_5_9_11, strength 1.0218) STILL present in bearing_yogas —
                   #     matches. But verdict_grade=convergent_moderate (expected
                   #     convergent_strong) and composite_score=2.38 (expected ~2.78) — BOTH
                   #     MOVED. RED per native's explicit stop-and-report instruction. None of
                   #     the 3 merged lanes (T-0 script, T-1 new capability, kala_temporal.ts
                   #     hotfix) touch wealth-verdict computation (scope-warden confirmed on all
                   #     3) — not an obvious lane regression. Hypotheses NOT investigated further
                   #     (no fix-loop per standing rules): (a) time-dependent drift — kala_
                   #     activations/dasha_activation_proximity_score terms feeding the composite
                   #     are date-relative, "today" has advanced since the D-2 baseline reading;
                   #     (b) the two unrelated PRs (#600 docs, #601 perf-batching) that landed on
                   #     main during this cycle. STOPPED HERE, reported to native, no further
                   #     action taken pending disposition.
                   #
                   # Follow-up-audit finding (3 /api/retrieval/capability callers sharing the
                   # possible double-unwrap bug class) logged in DISAGREEMENT_REGISTER_v1_0.md
                   # as a non-DR FINDING entry (register_p1_synthesis.ts, register_p1_reference.ts,
                   # l0_brahmagyan.ts) — out of D-3 scope, not chased.
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
  - {lane: T-0, branch: wave/D-3/T-0, worktree: /Users/Dev/Vibe-Coding/Apps/Madhav-wave-D3-T0, base: origin/main@b536e13b, head_sha: 9a67f986, status: receipted, model: sonnet, verifier_model: opus, receipt_ref: "verdict=ACCEPT, tests=40/40, scope_warden=pass, live independent reproduction on 482012f1 matched implementer numbers EXACTLY (check-a intensity0/threshold0 FAIL, check-b 2/6 FAIL, check-c 18/40=0.45 vs 0.50 floor FAIL, control_gap=-0.0464 FAIL). DR-10 peak_basis=dasha_lord_confluence_v1 correctly NOT claimed as a named model. DR-11 anti-gaming independent-reproduction requirement satisfied by this verifier pass itself. All-red retrodiction result judged legitimate v1-proxy weakness, not a defect. 2 flag-forward non-blocking items for T-2/T-3 kernel work: (1) top_decile_fraction=1.0 sparse-curve artifact on check-a (does not flip result), (2) verifier-found localMax grid tie-break makes lead/lag distribution (peak_lag_days=-42 on every hit) uninformative, no pass/fail impact."}
  - {lane: T-1, branch: wave/D-3/T-1, worktree: /Users/Dev/Vibe-Coding/Apps/Madhav-wave-D3-T1, base: origin/main@b536e13b, head_sha: 3d888223, status: receipted, model: sonnet, verifier_model: opus, receipt_ref: "verdict=ACCEPT, tests: platform 5687/5687 pass, platform-mcp 515/605 pass (75 pre-existing failures verified byte-identical vs origin/main baseline, none reference AV/kakshya code), new file 25/26 (1 live-integration skipped). scope_warden=pass (exactly 4 files, all in-lane, append-only registrations). CR-87 verified: chart_id required no-default both modes. Live SAV bindus independently re-pulled and re-computed by verifier: 29,29,27,32,30,26,34,32,25,27,23,23 (sum=337 classical total) — exact match; house7=34 amplifying/house10=27 damping confirmed against BRIEF_D3 type specimens. Both v1-tradeoff flags (kakshya duration correction, Lahiri mean-rate sidereal approx) judged RIGHT calls matching the brief's own illustrative framing, not defects. One non-blocking Phase-2 note: kakshya_windows live-serving depends on sidecar transit endpoint, unproven at Phase-1, gate runner should exercise post-deploy."}
integration_branch: {branch: wave/D-3/integration, base: origin/main@b536e13b, merges: ["9a67f986 (T-0, fast-forward)", "3d888223 (T-1, merge commit 9166f5ca)", "04643e3a (hotfix-kala-temporal, merge)"], suite: {platform: {tsc: clean, eslint: clean, vitest: "5727 passed / 317 skipped / 1 todo, 0 failed"}, platform_mcp: {tsc: clean, vitest: "517 passed / 75 failed / 15 skipped — pre-existing baseline (+2 new passing from the hotfix), no new failures across all 3 merges"}}, pushed: false}
hotfix_lanes:
  - {lane: hotfix-kala-temporal, branch: wave/D-3/hotfix-kala-temporal, worktree: /Users/Dev/Vibe-Coding/Apps/Madhav-wave-D3-hotfix-katemporal, base: origin/main, head_sha: 04643e3a, status: receipted+merged, verifier_model: opus, merged_into: wave/D-3/integration, receipt_ref: "verdict=ACCEPT, scope_warden=pass, tests: 75 failed/517 passed/15 skipped (own vitest run) vs origin/main scratch-checkout baseline 75/515/15 — delta=+2 new passing tests only, no regression. Wire shape independently traced from source on BOTH ends (route.ts response wrapping + all 4 L3 handlers' is_error-bearing return shape) — diagnosis confirmed, not taken on faith. CR-93/94 precedent independently confirmed as a faithful transplant of an already-accepted identical fix. Judgment call: code-level evidence (source-traced shape + existing precedent + corrected regression test with a negative don't-mis-unwrap case) sufficient for Phase-1 ACCEPT with live confirmation properly deferred to Phase-2 post-deploy gate, per protocol's own two-phase design — verifier explicitly does not consider this risky enough to require live confirmation before merge. FORWARD-POINTER (not blocking, not this lane's scope): 3 other /api/retrieval/capability callers (register_p1_synthesis.ts, register_p1_reference.ts, l0_brahmagyan.ts) return content raw without the is_error descent — may share the same latent bug class depending on downstream consumption; flagged for a follow-up audit, not traced to a conclusion.", integration_note: "merged into wave/D-3/integration cleanly (2 files, 73 insertions/4 deletions); platform-mcp re-run post-merge: tsc clean, vitest 75 failed/517 passed/15 skipped — matches hotfix lane's own count exactly, full wave integration remains clean."}
deploy: {done: true, pr: 602, merge_sha: "11377530892799afd8015d3ee9b6ec68efeb0c0d", images: {amjis_web: "11377530892799afd8015d3ee9b6ec68efeb0c0d", amjis_mcp: "11377530892799afd8015d3ee9b6ec68efeb0c0d"}, rebuild: {needed: false, reasoning: "T-1 and hotfix are both pure serving-layer changes, zero migrations, zero new writers, no new fact categories — no R-5/§8.2 trigger"}}
gate: {run: false, blocker: null, note: "regression guard RESOLVED BENIGN 2026-07-18 — see carried_item_dispositions / DISAGREEMENT_REGISTER wealth-rebaseline FINDING. ganita_yoga_firings_get confirmed 12/12 yogas fired=true at unchanged strengths (fork check per native directive); the 2.78->2.38 delta is entirely yoga_term, driven by domain-bearing classification 4->3, itself downstream of kala_activations now populating (this wave's own hotfix) + the DR-9 Part B affliction/threat layer going live — not a lost firing. Wealth guard RE-BASELINED to convergent_moderate/~2.38+Dhana Yoga+affliction layer+kala_activations populated; the prior 2.78 pin retired as pre-timing/pre-affliction. Not a D-3 wave-blocker (D-3's gate is the T-0 retrodiction battery). No code changes made."}
updated_at: "2026-07-18T03:05+05:30"
resumed_at: null
