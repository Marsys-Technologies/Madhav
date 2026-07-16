---
wave: D-2
lifecycle_step: 5
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
  - {lane: V-1, branch: worktree-agent-a8c6723d1f643e6e8, status: receipted, cycle: 1, worktree_base: d349a9c3, base_stale: true, head_sha: 254200fd, attempt: 2, receipt_ref: "verdict=ACCEPT (attempt 1), verifier=opus, scope_warden=pass, 24/24 tests. INTEGRATE (attempt 2): found missing KNOWN_HAS_WRITER_TRUE entries for bg_vidhi_primitives/bg_vidhi_floors (Step-2 companion edit V-4/V-5 got right, V-1 initially missed); 2-line fix conductor-reviewed directly (trivial, convention-matching, tests confirmed 3 passed/1 skipped) and merged"}
  - {lane: V-4, branch: worktree-agent-a2a7ae8a7815fc407, status: receipted, cycle: 1, worktree_base: d349a9c3, base_stale: true, head_sha: 1be1639e, receipt_ref: "verdict=ACCEPT, verifier=opus, scope_warden=pass, 3521/3521 tests, all 7 judgment calls independently reverified GREEN (DR-7 exact, CR-24 live-confirmed negative, CR-78 PARK genuine, write-scope safe)", risk_flag: "implementer's LOCAL rebuild attempt failed FORENSIC (Sun=Aries/Moon=Ashwini/Lagna=Scorpio, the known trap) - almost certainly a sandbox/env artifact (V-4 touches no position computation) but MUST confirm FORENSIC 7/7 on the real deployed rebuild before closing", followup: "composite_ranker.ts (V-3's file) should consume the now-populated graph_node_strength_contribution_jsonb column - CR-84/25 only closed at data layer by V-4"}
  - {lane: V-5, branch: wave/D-2/V-5, status: receipted, cycle: 1, worktree_base: 47a72b77, base_stale: false, head_sha: 13cc4349, receipt_ref: "verdict=ACCEPT, verifier=opus, scope_warden=pass, 3520/3520 sidecar tests, DR-6 exact match, cross-writer delete-scope proven disjoint, live specimen verified (Mercury sole D9-vargottama). Gate Ś #8 legitimately deferred (fix outside glob)"}
  - {lane: V-6, branch: wave/D-2/V-6, status: receipted, cycle: 1, worktree_base: fdc99de1, base_stale: false, head_sha: 3c0c49ed, attempt: 2, receipt_ref: "verdict=ACCEPT (attempt 2/3), verifier=opus, scope_warden=pass, 3479/3479 canonical §8.6 count reconfirmed exactly, all 4 test-constant fixes verified correct against production source (not tautological), bo_laksana pre-existing failure independently reconfirmed"}
  - {lane: V-2, branch: wave/D-2/V-2, status: pending, cycle: 2}
  - {lane: V-3, branch: wave/D-2/V-3, status: pending, cycle: 2}
integration_branch: wave/D-2/integration
deploy: {done: true, pr: 585, merge_sha: 58e320c40aabaf6fa582c70b9e68b66fd0555ced, ci_note: "one transient Build Check infra flake (no space left on device during docker load), unrelated to D-2 code, cleared on rerun"}
rebuild: {scope: asset_set, full: false, abhisek_build_id: pending}
gate: {run: false, green: [], red: []}
updated_at: 2026-07-16T22:45:00Z
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
  implementer agents per §F1.5 merge order. Each briefed with its may_touch glob, its §F1.7
  ledger rows, and (V-4/V-5) the binding DR-7/DR-6 formula+prior rulings.

  All 5 lanes RECEIPTED (ACCEPT) at Phase-1. V-6 needed one fix-cycle (attempt 2: 4 stale
  test-constant regressions + a false self-reported test count — doctrine substance was sound
  throughout, including the kendradhipati-dosha PROPOSED-marking safety property). Two agents
  (V-6 implementer, integration verifier) hit transient API disconnects mid-task and were
  resumed per protocol §6.4 (does not count against attempt counters).

  INTEGRATE complete: wave/D-2/integration created from main, all 5 lanes merged in declared
  order (V-0->V-1->V-4->V-5->V-6), one expected append-only conflict in
  test_has_writer_completeness.py (V-4+V-5 both appended) resolved keep-both. Full-suite +
  5 mandatory cross-lane checks run: found ONE genuine integration-level regression (V-1 missed
  the KNOWN_HAS_WRITER_TRUE 'Step 2' companion entries for its 2 new writers - a class of edit
  V-4/V-5 got right individually but only surfaces once all lanes combine). Routed back to V-1
  (attempt 2, a 2-line fix), conductor-reviewed directly given its triviality and exact match to
  an already-verified convention, merged. All other 4 cross-lane checks (shared-table
  delete/count scope safety, schema-declaration completeness, migration numbering, FROZEN
  orchestrator conformance) were clean on first pass.

  RISKS CARRIED INTO DEPLOY/REBUILD: (1) G0-4 (CR-54 wealth-loss mechanism) confirmed genuinely
  RED on pre-D-2 live data - expected to flip green only after this cycle's rebuild (V-4 edge-
  strength/CR-84/85 re-rank + V-5 dhana_axis); MUST re-verify post-rebuild, this is the key
  §G.1 6/6 gate risk. (2) V-4's LOCAL rebuild attempt failed FORENSIC in its sandbox
  (Sun=Aries/Moon=Ashwini/Lagna=Scorpio) - almost certainly a sandbox/env artifact since V-4
  touches no position computation, but the REAL deployed rebuild's FORENSIC 7/7 must be
  confirmed, not assumed. (3) Gate Ś #8 stays open/non-blocking (V-5 legitimately deferred it -
  fix requires files outside its glob). (4) composite_ranker.ts (V-3's file, cycle 2) should
  eventually consume the graph_node_strength_contribution_jsonb column V-4 populated - CR-84/25
  only closed at the data layer this cycle.

  NEXT: DEPLOY wave/D-2/integration to main -> CI -> deploy.yml, then REBUILD Abhisek's chart
  (scope computed live from asset_registry.depends_on per §B.10 at rebuild time, expected
  asset_set of similar order to D-1.6's 47), then POST-DEPLOY LIVE verification of cycle-1
  ledger rows before cycle-2 (V-2/V-3) spawns.
