---
wave: D-2
lifecycle_step: 2
status: ACTIVE
brief_bound: true
rollback_pin:
  image_sha:
    amjis-web: b623033e1f00e6ace96e4be2722506f30b057031
    amjis-mcp: 0824566951a3189bc750e24d20eab650f5542fb4
    brahma-build-pipeline-job: dfa4e8705aaa2243c3a24ba7eca26f55350cda8c
  abhisek_build_id: 8a353d5d-032f-4c49-b0e1-66e3eed8d381
row_count_baseline:
  chart_facts: 138279
  chart_dashas: 483060
  chart_divisionals: 22092
  bodha_msr_signals: 49360
adjudications:
  - {dr: DR-6, dis: DIS.019, subject: "V-5 signal-class priors", ruling: "nakshatra_semantic=1.00, arudha=1.10, special_lagna=0.90, vargottama_amplification=1.15, dhana_axis=1.05", recorded: true}
  - {dr: DR-7, dis: DIS.020, subject: "V-4 edge-strength formula", ruling: "edge_strength = base_relation_weight × valence_factor × ratification_factor × consistency_weight, clamp[0.1,2.0], formula_version=edge_strength_v1", recorded: true}
  - {dr: DR-8, dis: DIS.021, subject: "CR-28 intent_classify contract", ruling: "REDESIGN to deterministic rule-based scope_tuple + fallback_prompt (Opus engineering)", recorded: true}
rebuild_scope_ruling:
  scope: asset_set
  full: false
  layers: [L0-vidhi-rules, L1-subset, L2, minimal-L3-ingest]
  expected_writers: [bg_vidhi_new, bo_karanajala, bo_cgm_motifs, bo_cgm_paths, bo_cgm_metrics, bo_yantra_new, bo_laksana, bo_anveshana, ka_yojaka, ga_structural, ga_sensitive, bo_signal_class_new_x4]
  exact_closure: computed_post_cycle1_merge_via_asset_registry_depends_on
migration_blocks:
  V-1: [440, 444]
  V-4: [445, 449]
  V-5: [450, 454]
  V-6: [455, 459]
lanes:
  - {lane: V-0, branch: worktree-agent-abd702623395ca54e, status: receipted, cycle: 1, worktree_base: d349a9c3, base_stale: true, head_sha: a3e6ad56, receipt_ref: "verdict=ACCEPT, verifier=opus, scope_warden=pass (incl. necessary workflow_dispatch top-level trigger, judged safe/additive), 33/33 tests, tsc/eslint clean", risk_flag: "G0-4 (CR-54 wealth-loss mechanism, Rahu/Mars-on-H2) CONFIRMED GENUINE RED on live data (true-negative, not harness bug) - expected to flip green only after V-4 (edge-strength/CR-84/85 re-rank) + V-5 (dhana_axis CR-36) deploy+rebuild; MUST re-verify before stamping §G.1 6/6 - tracked as wave-level gate risk"}
  - {lane: V-1, branch: worktree-agent-a8c6723d1f643e6e8, status: receipted, cycle: 1, worktree_base: d349a9c3, base_stale: true, head_sha: c12adcc6, receipt_ref: "verdict=ACCEPT, verifier=opus, scope_warden=pass, 24/24 tests, reconciled against real BIND_D-2.md (CR-status/migration-440/census all consistent); note track3/README overstates migration allocation as 440-441 (only 440 exists, harmless doc inaccuracy)"}
  - {lane: V-4, branch: worktree-agent-a2a7ae8a7815fc407, status: implementing, cycle: 1, worktree_base: d349a9c3, base_stale: true}
  - {lane: V-5, branch: worktree-agent-a2af6d94c873f4ed9, status: verifying, cycle: 1, worktree_base: 47a72b77, base_stale: false, verifier_dispatched: a8c7c61b47b26005c, note: "Gate Ś #8 explicitly DEFERRED (fix requires bo_laksana.py/ka_yojaka.py, both outside glob) - verifier confirming reasoning"}
  - {lane: V-6, branch: worktree-agent-a38731279aa1a82f5, status: implementing, cycle: 1, worktree_base: fdc99de1, base_stale: false}
  - {lane: V-2, branch: wave/D-2/V-2, status: pending, cycle: 2}
  - {lane: V-3, branch: wave/D-2/V-3, status: pending, cycle: 2}
deploy: {done: false}
rebuild: {scope: asset_set, full: false, abhisek_build_id: pending}
gate: {run: false, green: [], red: []}
updated_at: 2026-07-16T15:50:00Z
notes: >
  OPEN complete. Binder (Fable) BOUND the brief: see BIND_D-2.md — 12/12 regression sample PASS,
  0 unexpected reds (both expected residuals confirmed: PARK-#4, Gate Ś #8). §F1.7 promise ledger
  total at 56 rows. Three DR-n rulings recorded (DR-6/7/8, DIS.019/020/021) per §8.8(ii)
  conductor-only register-edit rule. CR-9 anomaly noted: 401 did not reproduce on the
  marsys-jis-direct face — V-3 re-verifies root cause before "fixing". Tool census = 135 (not
  ~126). chart_dashas baseline revised 536,471(superseded) -> 483,060 (stability-checked at
  first rebuild, not assumed a defect). PARK-#4's "5 rows" framing is narrow-assertion-scope only;
  live keyword_heuristic_v1 population = 43,408/49,360 rows chart-wide (V-4 ledger row 39 note).
  SPAWN complete: cycle-1 lanes V-0/V-1/V-4/V-5/V-6 launched as parallel isolated-worktree
  implementer agents (2026-07-16 ~21:35 IST) per §F1.5 merge order (V-0 -> V-1 -> V-4 -> V-5 ->
  V-6). Each briefed with its may_touch glob, its §F1.7 ledger rows, and (V-4/V-5) the binding
  DR-7/DR-6 formula+prior rulings to implement exactly. V-6's kendradhipati-dosha item explicitly
  instructed to BLOCK-and-report rather than self-adjudicate doctrine if no DR-n is available in
  its own turn. Awaiting implementer claims -> Phase-1 Opus verifiers next.
