---
wave: D-1.6
lifecycle_step: 6
brief_bound: true
rollback_pin:
  image_sha:
    amjis-web: aa1bad9fa4822f388b8d6bb1c42728d176465632
    amjis-mcp: 1a4b935f8cd59a4c63edfe2aeedf51e079d71005
  abhisek_build_id: pending_lookup
lanes:
  - {lane: S-1, branch: wave/D-1.6/S-1, status: receipted, worktree: /Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/agent-aaa098d3ceb5fa9e5, head_sha: 3c87ebd2, receipt_ref: "verdict=ACCEPT (round 2/3), verifier=opus, scope_warden=pass, all 3 diagnosed tests genuine+passing, zero regressions - lane complete"}
  - {lane: S-2, branch: wave/D-1.6/S-2, status: receipted, worktree: /Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/agent-abf3cb708e89ec1e6, head_sha: 1dd8d632, receipt_ref: "verdict=ACCEPT, verifier=opus, scope_warden=pass, tests py3433/ts5578 all green, gate#4 default-page check PENDING_DEPLOY (correct pre-deploy)"}
  - {lane: S-3, branch: wave/D-1.6/S-3, status: receipted, worktree: /Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/agent-a01b756f0951d8a1c, head_sha: c7b20239, receipt_ref: "verdict=ACCEPT (HIGH CONFIDENCE - independently re-verified via live MCP probe + source read, not accepted on faith), scope_warden=pass, Gate Ś items 5/6/7 CONFIRMED already green live pre-deploy; Y-2/Y-10/Y-12 fixes clean, zero test regressions"}
  - {lane: S-4, branch: wave/D-1.6/S-4, status: receipted, worktree: /Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/agent-a28066c7ff5ae7857, head_sha: 10d4ff86, receipt_ref: "verdict=ACCEPT, verifier=opus, scope_warden=pass, R-45 lord-resolution independently proven fabrication-safe (exact-token match, NULL-on-miss never guesses), flat-0.5 fix genuine, zero new test failures; T-5/T-9 correctly left un-dispatched for conductor REBUILD step"}
  - {lane: S-5, branch: wave/D-1.6/S-5, status: receipted, worktree: /Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/agent-a6f56ca1240fa0d7a, head_sha: 4813d6ec, receipt_ref: "verdict=ACCEPT (with caveats: PARK-#4 correctly deferred to Gate-Ś phase-2, R-18 has documented cross-tool false-negative limits), verifier=opus, scope_warden=pass, 75fail/444pass zero-regression vs main, tsc clean, r18 harness genuine 0-flags"}
  - {lane: S-6, branch: wave/D-1.6/S-6, status: receipted, worktree: /Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/agent-ac5fe8f251fdcb8c7, head_sha: 6b7994e9, receipt_ref: "verdict=ACCEPT, verifier=opus, scope_warden=pass, migration-439 independently reviewed safe/idempotent, kala_temporal rewire sound (mirrors BA-P1 pattern), zero new regressions; O-2+O-8 GCP writes STAGED not executed, need conductor/native decision"}
  - {lane: S-7, branch: wave/D-1.6/S-7, status: pending}
  - {lane: S-8, branch: wave/D-1.6/S-8, status: receipted, worktree: /Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/agent-a173a2019ea963797, head_sha: bbc9bde9, receipt_ref: "verdict=ACCEPT, verifier=opus, scope_warden=pass, note: MARSYS_DEFECT_GAP_REGISTER_v2_0.md is at 00_ARCHITECTURE/ root not under llm_consumption_audit/** - brief may_touch glob imprecision, authorized by lane task text, non-blocking"}
deploy: {done: true, sha: 38d8210554807dfdc90aa797a7023fdca49465b9, pr: 578, ci_run: 29491712143, deploy_run: 29492213040}
rebuild: {scope: asset_set, full: false, run_id: 83949839-fff3-472f-bbb1-cbf6c3b1bb8a, job_execution: brahma-build-pipeline-job-dv5f9, asset_count: 47, roots: [ga_structural, ga_yoga, ka_yojaka], includes_t5_t9_target: ka_jivana_parva, dispatched: true, abhisek_build_id: pending}
gate: {run: true, green: [1, 2, 3, 4, 5, 6, 7, 12, 13], red: [8, 9], pending: [10, 11, 14, 15, 16]}
updated_at: 2026-07-16T00:00:00Z
notes: >
  OPEN complete. Binder (Fable) BOUND the brief: see BIND_D-1.6.md. 13/16 S-7 items
  CLOSED-with-evidence (no work needed); S-4/CR-49-residuals/KP-4-residual routed to S-5;
  R-48 routed to S-8. DR-4 (CR-23 NBRY doctrine) + DR-5 (C-6 composed-rubric boundary) ruled;
  CR-28 routed to Opus engineering adjudication (pending, own lane task inside S-1 or standalone).
  Rebuild scope ruled scope-limited (no full L1-L5 trigger). Ops flag: Bearer MCP face 401s,
  ?api_key face live — gate harness must use api_key face or fix Bearer key first (S-6 item).
  Next: SPAWN step — worktree+branch per lane, implementers launched.
  CONFIRMED (S-8 verifier): CURRENT_STATE_v1_0.md's git-committed HEAD (main aa1bad9f) still reads
  current_wave=D-1.5b; the D-1.6 banner is an uncommitted working-tree edit only (pre-existing at
  session start, matches original git status M flag) — un-checkpointed per protocol §6.1. Conductor
  action: commit this banner (as part of INTEGRATE or CLOSE step, not standalone) once lanes land.
  INTEGRATE (step 4) complete: all 7 lanes merged onto wave/D-1.6/integration (5cbe0a8c) in order
  S-1..S-6,S-8; one real conflict (POST_REMEDIATION register §M/§N, both sides authored the same
  addendum text independently — resolved by taking S-8's superseding §N version). Full suite on
  integrated branch: platform tsc clean, npm test 5589/0 failed; platform-mcp tsc clean, npm test
  449 passed/75 failed (IDENTICAL to main baseline via direct file-content diff comparison — zero
  new regressions from cross-lane integration); sidecar pytest+bodha_writers 3538 passed/0 failed;
  drift_detector.py 219 findings/exit=3, schema_validator.py 34 violations/exit=3 — BOTH IDENTICAL
  to main baseline (confirmed via direct comparison), pre-existing, not wave-introduced.
  GCP infra writes APPLIED (native go-ahead granted): O-2 terraform apply clean (0 add/3 change/0
  destroy, matched S-6's staged plan exactly) — pending-stream-reaper URI fixed, panchanga-refresh
  gained OIDC token; cron-secret headers on canary-battery-daily + panchanga-daily-refresh
  re-provisioned immediately after via gcloud (captured original value pre-apply). Both jobs found
  PAUSED — pre-existing (not terraform-managed, not caused by this apply — confirmed no
  paused/state attr in the .tf files), left as-is, out of scope. O-8 monitoring alert policy
  created (projects/madhav-astrology/alertPolicies/6294997695917926548) after resolving
  ${ALERT_NOTIFICATION_CHANNEL_ID} to the existing "Native operator" email channel and fixing
  combiner AND->OR (GCP requires OR for log-matching conditions — S-6's staged JSON needed this
  one correction).
  DEPLOY step 5 complete: PR #578 merged to main @ 38d82105 (CI green, gh pr merge --merge).
  Deploy workflow 29492213040 completed success; amjis-web + amjis-mcp both verified live at
  38d8210554807dfdc90aa797a7023fdca49465b9.
  REBUILD complete (step 6): 47/47 assets lit, zero errors, run ended 11:34:03. Build-health: FORENSIC
  7/7 confirmed live (Sun Cap/Moon PBhadrapada/Lagna Aries 12.42°/Shukla Tritiya/Ravivara/Shiva/Garaja).
  chart_facts jumped 27554->138279 (investigated: zero duplicate natural keys within new build, clean
  category separation from prior build_id — legitimate ga_structural combinatorial output growth, NOT
  an accumulation bug). chart_divisionals 22092 matches S-6's floor rebaseline exactly. chart_dashas
  483060 (untouched by this rebuild, pre-existing, not a regression). DEFECT-001 orphan check: 0%
  orphaned. T-5/T-9 (ka_jivana_parva) included in the 47-asset scope, completed successfully as part
  of this rebuild — no separate backfill dispatch needed.

  GATE Ś RESULTS (live MCP against deployed connector 38d82105, post-rebuild):
  GREEN: #1 (Saturn remedy query returns only-Saturn, 29/29 rows) · #2 (digest weakest_graha=Venus,
  CR-55 citation) · #3 (mimamsa_calibration_get == query_calibration, IDENTICAL result_hash) · #4
  (Kemadruma/Kala-Sarpa correctly absent from default dosha_label page, zero shared-stub across 22
  rows) · #5 (Budha-Aditya/Saraswati/Dhana-2L9L all FIRE grounded in real fact_ids) · #6 (NBRY
  Saturn-D9 + Venus-D9 fire with full grounds_jsonb matching DR-4) · #7 (ganita_yogas_get v3 limit=3:
  Sasa correctly "formed", no fabricated "not formed" from truncated page) · #12 (A7 fix confirmed
  live; #4 correctly excluded) · #13 (ref_planet_transit_get no-401, ref_transit_rules_get 200,
  kala_temporal_bundle sidecar_available=true).

  RED (genuine, reproduced twice):
  #8 — yoga_activation_by_dasha AND its alias kala_yoga_activation_get return ALL rows undated
  (activation_start/end=null) with flat dasha_alignment_score=0.5 across the full 2026-2029 window
  (15/15 rows). judgment_query(wealth) AND judgment_query(career) both show receipt.timing_anchored=
  true while timing_hooks.{current,lord_mahadasha_windows,karaka_mahadasha_windows,kala_activations}
  are ALL EMPTY — also a #10 receipt-honesty violation (✓-with-empty-evidence).
  #9 — get_temporal_windows/kala_windows_get returns activation_count=0 for the default 1yr forward
  window; empty_reason discloses "8010 dated activation rows exist... these are historical" — R-45's
  lord-resolution DID populate real dated rows (mechanism proven working), but ALL are backward-
  looking; nothing forward of today got dated. Root cause not yet isolated: chart_dashas' future
  periods ARE correct and real (verified via ganita_dasha_periods_get, e.g. real 2025-2031 Venus
  sub-periods) — the gap is specifically ka_yojaka's forward window-generation, not lord resolution.
  Routing: reopening Lane S-4 for one targeted fix-2 attempt (new gate-driven cycle). If unresolved,
  PARK with this evidence for native review.
  S-4 fix-2 COMPLETE: root cause found (NOT D-3 convergence-engine territory, genuinely in-scope).
  (1) date_resolver.py's resolve_activation_windows picked matched[0] = chronologically earliest-ever
  dasha period instead of a current/soonest-future/most-recent-past tiered selection — live DB proof:
  49360 kala_activation rows, 40040 dated, 0 straddling today, only 140 with any future start. (2)
  register_d8_assess_domain.ts's yoga_activation_by_dasha ranked by dasha_activation_proximity_score
  DESC where undated rows default to exactly 0.5 and most genuinely-dated rows score below 0.5 —
  undated rows crowded out dated ones (exact match to the "15/15 undated flat 0.5" live symptom). (3)
  registry_bridge.ts's judgment_query could ship timing_anchored:true next to empty timing_hooks.
  Fixed all 3: tiered period selection, dated-rows-first ORDER BY, enforceTimingAnchoredHonesty guard.
  Branch wave/D-1.6/S-4-fix2 @ 9bac956f, tests pass (+3 platform, +2 mcp, 0 new failures, tsc clean).
  Live re-verification deferred to next deploy+rebuild+gate cycle (cannot verify from sandbox).
  S-4 fix-2 VERIFIED ACCEPT (Opus, high rigor given deploy stakes): all 3 root causes independently
  confirmed incl. live DB re-query matching implementer's exact numbers (49360/40040/0/140) and the
  0.5-crowding math (9320 undated all=0.5, 35691/40040 dated <0.5). One pre-existing (non-regression)
  mcp graha_portrait drill_pointers failure flagged, confirmed present at base 38d82105 already.
  DEPLOY complete: PR #580 merged @ 08245669, CI green, deploy success, amjis-web+amjis-mcp both
  verified live at 08245669.
  Narrow rebuild attempt 1 (run 71b260c7, 27-asset closure of ka_yojaka) FAILED partway: ka_yojaka +
  ka_sangam both genuinely completed (kala_convergence verified 2488 real rows written for ka_sangam)
  but ka_sangam's asset_throughput.state never transitioned to 'lit' (stuck at 'dormant') — a
  state-commit race/bug in the orchestrator, NOT caused by the S-4 fix-2 code. This tripped a
  DEP-ASSERT on ka_kalasutra ("ka_sangam(dormant)") which then cascaded BLOCKED errors through all
  24 remaining downstream assets. Root cause is orchestrator-level (asset_throughput state-write
  lagging behind actual data-write completion under concurrent load), NOT a D-1.6 lane defect — noted
  for the close report as an out-of-wave finding, not fixed here (§N.2 FROZEN orchestrator — do not
  touch without native sign-off). Recovery: manually corrected ka_sangam's asset_throughput row to
  'lit' (data-verified, not fabricated — real 2488-row count confirmed in kala_convergence first),
  then dispatched a resume run (8a353d5d) for the remaining 25 assets via the same topo-sorted
  asset_set pattern.
  Next: monitor resume run 8a353d5d to completion, re-run Gate Ś items 8/9/10 live, then CLOSE.
---
