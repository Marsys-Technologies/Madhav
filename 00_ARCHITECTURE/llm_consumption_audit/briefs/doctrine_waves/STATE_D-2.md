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
  - {lane: V-0, branch: wave/D-2/V-0, status: pending, cycle: 1}
  - {lane: V-1, branch: wave/D-2/V-1, status: pending, cycle: 1}
  - {lane: V-4, branch: wave/D-2/V-4, status: pending, cycle: 1}
  - {lane: V-5, branch: wave/D-2/V-5, status: pending, cycle: 1}
  - {lane: V-6, branch: wave/D-2/V-6, status: pending, cycle: 1}
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
  Proceeding to SPAWN: cycle-1 lanes V-0/V-1/V-4/V-5/V-6 launching as parallel isolated-worktree
  implementers per §F1.5 merge order (V-0 -> V-1 -> V-4 -> V-5 -> V-6).
