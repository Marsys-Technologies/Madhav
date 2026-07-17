---
wave: D-2
lifecycle_step: 8  # cycle-1: through 8 (close+verified) — deployed, rebuilt, live-verified,
                   # G0-4 CLOSED. Wave stays ACTIVE for cycle-2 (V-2/V-3) per the 2-cycle staging.
status: ACTIVE
cycle: 2  # cycle-1 complete; spawning cycle-2 (V-2 MCP delivery + V-3 channel) next.
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
cycle1: complete   # merged (PR #585) + deployed + rebuilt (61/61) + live-verified. 4 rebuild
                   # hotfixes required (PRs #586/#588/#589/#590), see notes.
deploy:
  cycle1: {done: true, pr: 585, merge_sha: 58e320c40aabaf6fa582c70b9e68b66fd0555ced}
  hotfixes:
    - {pr: 586, what: "migration 440 asset_registry column set + layer='L0'->'brahmagyan' (2 defects, migration-guard-caught)"}
    - {pr: 588, what: "Narayana Dasha verification_pass_status enum violation (ad-hoc strings not in CHECK set)"}
    - {pr: 589, what: "bo_laksana_rerank Decimal not JSON-serializable (NUMERIC centrality cols)"}
    - {pr: 590, what: "ga_tajaka solar-return engine-failure resilience (pre-existing, not D-2; env-specific Moshier-range)"}
  g0_4_valence: {parts: {A_data: {pr: 591}, B_serve: {pr: 592}}, both_deployed: true, note: "amjis-web+amjis-mcp live at 4f320a77"}
rebuild:
  cycle1: {scope: asset_set, full: false, closure: 61, build_id: 58747f9b-ddca-4e48-8278-8efc2fb016ec, result: "61/61, 0 errors (4th attempt after the 4 hotfixes)"}
  g0_4_valence: {build_id: b84c3797-b64a-4956-a431-5f4ccdf9ee55, result: "61/61, 0 errors", forensic: "7/7 intact"}
gate:
  cycle1_live: {forensic: "7/7", defect_001_orphan_pct: 0.1, row_counts: sane}
  g0_4: "CLOSED — data plane (DR-9 Part A) + serving plane (DR-9 Part B) both live-verified 2026-07-17; 6/6 specimens green both directions; mechanism valence spreads (was 121/121 benefic -> mixed78/malefic30/neutral8/benefic7); judgment_query(wealth) serves Rahu-occupies-dhana in the affliction_mechanisms threat layer with grounding + afflictions_present flag. See DIS.022/DR-9, VAL-ROOT register row."
updated_at: 2026-07-17T12:25:00+05:30
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

  === CYCLE-1 COMPLETE (deployed + rebuilt + live-verified) ===
  DEPLOY: PR #585 merged to main. deploy.yml's first post-merge run FAILED at the migration
  step (migration 440's asset_registry INSERTs used non-existent columns display_name/
  asset_type/has_substeps + layer='L0'). Clean transaction rollback (no partial apply). Hotfix
  PR #586 (2 defects, the 2nd — layer='L0' invalid vs the brahmagyan/ganita/... CHECK — caught
  by a dedicated migration-guard pass before a repeat incident). Re-deploy succeeded; all 9 D-2
  migrations (440,445-448,450-453) applied.
  REBUILD required FOUR attempts, each surfacing a real defect invisible to every pre-deploy
  altitude (exactly the §F1.7 Definition-of-DONE thesis — code-green != live-correct):
    (1) migration 440 schema (PR #586); (2) Narayana Dasha verification_pass_status enum
    violation, ga_dashas asset (PR #588); (3) bo_laksana_rerank Decimal-not-JSON-serializable,
    60/61 then failed (PR #589); (4) ga_tajaka solar-return swisseph Moshier-range crash —
    PRE-EXISTING legacy code (commit 4d4bda8e), not D-2, pulled into the closure via ga_structural;
    env-specific, unreproducible locally; fixed with graceful engine-failure resilience (PR #590,
    native-approved to fix now). Each fix independently Opus-verified before merge. 4th rebuild
    (build 58747f9b): 61/61, 0 errors. Build-health: FORENSIC 7/7, DEFECT-001 0.1% orphan,
    row counts sane.
  CYCLE-1 LIVE-VERIFY: build-health green; but G0-4 (the §G.1 gate risk) CONFIRMED STILL RED
    post-rebuild — the Rahu/Mars-on-H2 wealth-loss mechanism did NOT surface. Diagnosed, not
    papered over.

  === G0-4 INVESTIGATION -> DR-9 / VAL-ROOT (CRITICAL, estate-wide) — CLOSED ===
  Step-1 (native-directed, diagnosis-only): root-caused to a CRITICAL estate-wide valence-
  computation defect at 4 divergent sites, all defaulting adverse->favorable — the D-16/CR-54/
  CR-83 lineage root (retroactively root-causes D-16 "estate emits ZERO adverse-valence claims").
  Ordering-constraint answer: inversion lived in ga_vichara's own computation (a) — trikoṇa-
  membership pre-empted the dusthāna-affliction cell for dual-lord Mars, no contact-type, nodes
  skipped; plus edge-type-keyed mechanism valence (121/121 benefic) + hardcoded-benefic V-5
  tenancy/vargottama.
  Step-2 (native-directed, both parts ratified): PART A (data) — one shared brahmagyan/
  valence_doctrine.py (natural × functional × dignity incl. classical node exaltation × contact-
  type -> signed 4-way, mixed first-class), consumed by ga_vichara, bo_karanajala edges,
  bo_yantra mechanisms (+ NEW graha_bhava_affliction tenancy Mechanism class), V-5
  tenancy/vargottama emitters (PR #591). PART B (serve, native-ratified at Step-2 close) —
  judgment_query serves a SIGNED PARTITIONED verdict: supporting (bearing_yogas) AND threatening
  (bearing_afflictions + affliction_mechanisms), each with its own §N.6 hardFloor so a trim can
  never zero the adverse layer (PR #592). Both deployed (amjis-web+amjis-mcp @ 4f320a77).
  VERIFIED: 6/6 anti-overcorrection specimens green both directions (unit + live); independent
  adversarial Opus verify SAFE; full sidecar suite 3574/0; mechanism valence spreads; live
  judgment_query(wealth) serves "Rahu occupies dhana (2nd) bhāva (mixed)" in the threat layer
  with grounding. Governance: DR-9/DIS.022 (both parts ratified), VAL-ROOT CRIT row (D-16
  root-caused). FINDING: top_k_salience_rank NULL is NOT the serve gate (serve orders by
  computed_salience DESC NULLS LAST) -> Part B, not a rank fix, surfaces low-salience adverse
  content. Residual follow-up (non-blocking, never mislabels adverse->benefic): arudha AL
  bhava-relation under-call.

  NEXT: SPAWN cycle-2 (V-2 MCP delivery/receipts + capability_version; V-3 channel scan/fetch +
  canonical-face list + CR-9/44/16/15/14/39 + intent_classify per the DR-8 ruling) as parallel
  isolated-worktree implementers per §F1.5 (merge order V-2 -> V-3). V-3 should also pick up the
  composite_ranker.ts follow-up (consume V-4's graph_node_strength_contribution_jsonb, CR-84/25
  serving leg) flagged in the V-4 receipt. No rebuild expected for cycle-2 (serving-only) unless
  a diff touches a writer.
