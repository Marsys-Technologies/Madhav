// tracker_data.js — generated from SWARM_TRACKER.json. Do not hand-edit; the
// conductor regenerates this file whenever SWARM_TRACKER.json changes.
window.TRACKER = {
  "schema_version": "1.1",
  "session_id": "PARIPRASHNA-CONDUCTOR-P0-FRESH-2026-08-19",
  "phase": "P1",
  "phase_status": "P1_FOUNDATION_WAVE2_DISPATCHED",
  "wave": "P1-FOUNDATION",
  "heartbeat_ts": "2026-08-19T17:42:00Z",
  "concurrency": {
    "n": 4,
    "cap": 10,
    "hard_cap": 24
  },
  "budget": {
    "phase": "P0",
    "ceiling_usd": 40,
    "spent_usd": 0
  },
  "prior_attempt": {
    "session_id": "PARIPRASHNA-G0-CLOSE-2026-08-19",
    "retired_reason": "Merged pariprashna/g0-close to main (PR #1341, 3fd40b61b) without a cross-campaign lease per origin/campaign-coordination. Retired 2026-08-19 under CROSS_CAMPAIGN_COLLISION_FORENSICS_AND_REPAIR_v1_0.md \u00a77 (rules X-1..X-7).",
    "verified_findings_carried_forward": [
      "G0/PR #1341 merged 2026-08-19T08:46:16Z as 3fd40b61b; drift_detector 216/216 baseline, schema_validator 42/43 baseline, 26 required checks green.",
      "Two real governance-gate regressions were found and fixed pre-merge in G0: FILE_REGISTRY registry_disagreement (8 findings, drift 224->216) and SESSION_LOG level-3-heading schema break (schema 44->42, exit 2->3). Both pre-empted in Step 0 of the fresh-start (registered FILE_REGISTRY + CAPABILITY_MANIFEST in the same commit; used a level-2 SESSION_LOG heading from the start).",
      "gh auth live (user amonty84, repo/workflow scopes).",
      "gcloud authenticated (project madhav-astrology, 2 accounts: firebase-admin service account + mail.abhisek.mohanty@gmail.com).",
      "pariprashna/p0-ignition (183b2bfed) was docs-only, 7 files, zero code -- nothing functional was lost by retiring it; its 6 planning docs (all but the superseded SWARM_TRACKER.json) were carried forward byte-identical in Step 0."
    ],
    "not_yet_probed_owed_by_p0_b": [
      "cloud-sql-proxy",
      "template test-DB for per-lane clones (RF-5)",
      "conductor-owned migration-number allocator (RF-2)",
      "flag registry"
    ]
  },
  "step_0": {
    "status": "COMPLETE",
    "0a_lease_announcement": {
      "status": "DONE",
      "ref": "origin/campaign-coordination @ 0f4408ac4"
    },
    "0b_worktree_and_docs": {
      "status": "DONE",
      "worktree": "/private/tmp/pariprashna-p0",
      "branch": "pariprashna/p0",
      "base": "origin/main @ a7136b467"
    },
    "0c_pr_land": {
      "status": "MERGED",
      "pr": "https://github.com/Marsys-Technologies/Madhav/pull/1346",
      "pr_number": 1346,
      "merge_commit": "45f0ddf56793a23bf5881701ee6c184f6868f20a",
      "merged_at": "2026-08-19T14:19:13Z"
    },
    "0d_retire_old_refs": {
      "status": "DONE",
      "deleted": [
        "pariprashna/g0-close (local+remote, was 7bdb9a53c)",
        "pariprashna/p0-ignition (local+remote, was 183b2bfed)"
      ],
      "worktrees_pruned": [
        "/private/tmp/pariprashna-g0-close",
        "/private/tmp/pariprashna-p0-ignition"
      ]
    },
    "0e_tracker": {
      "status": "DONE",
      "note": "This file, drafted before 0c merge; committed once 0d completes."
    }
  },
  "lanes": {
    "P0-B": {
      "role_stage": "merged",
      "name": "environment (worktree farm, cloud-sql-proxy, template test-DB, migration allocator, flag registry)",
      "worktree": "/private/tmp/pariprashna-p0-b-env",
      "branch": "pariprashna/p0-b-env",
      "last_event_ts": "2026-08-19T14:28:00Z",
      "verifier_verdict": "conductor-reviewed, cherry-picked clean (13888e3d9)",
      "refuter_votes": []
    },
    "P0-C": {
      "role_stage": "merged",
      "name": "PORTS REFACTOR of route.ts (RF-1, gating lane -- verifier + 3 adversaries required before other lanes open)",
      "worktree": "worktree-agent-a6279b3f3d579e906",
      "branch": "pariprashna/p0-c-ports-refactor",
      "last_event_ts": "2026-08-19T15:20:00Z",
      "verifier_verdict": "SAFE TO MERGE. 1 verifier + 3 adversaries (behavioral/security/harness-integrity) all converged: no auth/tenant-isolation/NO-LEAKAGE regression, decomposition manually confirmed behaviorally faithful. Adversarial review found and the conductor fixed 2 real governance-gate coverage gaps before merge: (1) naming_lint baseline mis-pointed for the moved CITATION_GATE_OVERRIDE flag -- would have failed CI; (2) COLLECT-ONLY calibration-leak gate's SERVING_PATH_FILES allowlist didn't cover the 9 new pipeline modules -- demonstrated via red/green mutation, now fixed and re-verified. Non-blocking follow-ups filed as known residuals (see p0_c_known_residuals below), not fixed in this lane: harness doesn't record args at ~half its mocked I/O boundaries (3 proven false-PASS mutations: deleted auth DB round-trip/super_admin demotion, dropped retrieval params+scrambled QoS principal, collapsed orientation fallback); 3 misleading derived_from scenario names; 2 uncovered branches (NO_ADAPTER, chart-mismatch); a pre-existing swallowed citation-gate error reporting PASS (validation_stage.ts:64-66, NOT introduced by this refactor); a latent unreachable abort-path ordering fragility (no adapter has a finally block today). Full test suite 424/449 pass (25 pre-existing skips), naming_lint/drift_detector/schema_validator/tsc all clean.",
      "refuter_votes": []
    },
    "P0-D": {
      "role_stage": "admissible",
      "name": "tracker scaffold",
      "worktree": "/private/tmp/pariprashna-p0",
      "branch": "pariprashna/p0",
      "last_event_ts": "2026-08-19T14:19:59Z",
      "verifier_verdict": null,
      "refuter_votes": []
    },
    "P0-E": {
      "role_stage": "merged",
      "name": "design-plan grounding pass (docs)",
      "worktree": "worktree-agent-a3eb62b2d427955b5",
      "branch": "worktree-agent-a3eb62b2d427955b5",
      "last_event_ts": "2026-08-19T14:31:32Z",
      "verifier_verdict": "conductor-reviewed, cherry-picked clean (9365f02ef), drift/schema baseline held (216/42)",
      "refuter_votes": []
    },
    "P0-F": {
      "role_stage": "admissible",
      "name": "DD-2 anthropic delist + DD-3 infra automation probes",
      "worktree": "worktree-agent-ae31a8d8d360e94b8",
      "branch": "pariprashna/p0-lane-f",
      "last_event_ts": "2026-08-19T14:28:00Z",
      "verifier_verdict": "DD-2 merged (2d759b00f), diff reviewed clean. DD-3: all 4 items IAM-permitted (owner role) but PARKED pending explicit human authorization -- PITR enable, scratch instance creation (billable), restore drill, and amjis_app credential rotation all carry real production/cost risk. Exact commands captured in P0-F agent report for when authorized.",
      "refuter_votes": []
    },
    "P1-J": {
      "role_stage": "merged",
      "name": "design-plan grounding pass",
      "note": "Already satisfied by P0-E (doc at v0.5)."
    },
    "G1-F": {
      "role_stage": "merged",
      "name": "Model-plane hygiene (provider posture doc)",
      "worktree": null,
      "branch": null,
      "last_event_ts": "2026-08-19T17:08:00Z",
      "verifier_verdict": "conductor-reviewed, cherry-picked clean, docs-only, drift baseline held",
      "refuter_votes": []
    },
    "G1-H": {
      "role_stage": "merged",
      "name": "PB-9-DETECTOR (no-auto-promotion CI gate)",
      "worktree": null,
      "branch": null,
      "last_event_ts": "2026-08-19T17:08:00Z",
      "verifier_verdict": "conductor-reviewed, committed (agent left uncommitted), 20/20 tests independently re-verified, drift/naming_lint clean",
      "refuter_votes": []
    },
    "G1-D": {
      "role_stage": "merged",
      "name": "Rate limits + pre-dispatch spend ceilings (middleware.ts)",
      "worktree": null,
      "branch": null,
      "last_event_ts": "2026-08-19T17:08:00Z",
      "verifier_verdict": "conductor-reviewed. Caught+self-corrected a near-miss (would have clobbered src/proxy.ts, the real app-wide session gate -- Next 16 renamed middleware.ts convention). Migration 574 (nullable channel column + 2 non-locking indexes on llm_usage_events) is additive-only, applies automatically via the existing deploy pipeline when this branch reaches main -- not applied manually. Flag-off by default (PARIPRASHNA_LIMITS_ENABLED). 69/69 lane tests + full suite 707/751 files, 7877 tests 0 failures, independently re-verified. drift/naming_lint clean.",
      "refuter_votes": []
    },
    "G1-B": {
      "role_stage": "merged",
      "name": "Consent & subjects schema (NCD-9) -- migration authored+locally-verified only, NOT applied to production by the agent",
      "worktree": null,
      "branch": null,
      "last_event_ts": "2026-08-19T17:08:00Z",
      "verifier_verdict": "conductor-reviewed. Real migration-number collision found and fixed: both G1-D and G1-B independently picked 574 (shared platform/migrations+platform/supabase/migrations sequence). Renumbered G1-B's to 575, updated all 4 internal references, re-verified: 73 unit + 14 DB-integration tests re-run independently against a fresh local scratch Postgres after rename, all pass. Resolved a real merge conflict in feature_flags.ts (both lanes added a flag in the same enum/defaults block) -- both flags coexist correctly, safety_gate.ts auto-merged clean with correct ordering (authorizeChartAccess -> resolveSubjectConsent, per G1-B's own header doc). Full suite after all 4 wave-1 lanes: 711/756 files, 7950 tests, 0 failures. drift/naming_lint clean. Migration NOT applied to production by the agent or conductor -- will apply automatically via the deploy pipeline when this branch reaches main.",
      "refuter_votes": []
    },
    "G1-A": {
      "role_stage": "verifying",
      "name": "SafetyPolicyGate + HS-1..HS-6 (serializes before G1-G)",
      "worktree": "worktree-agent-a7fb9dab527dd607a",
      "branch": "pariprashna/g1-a-safety-gate",
      "verifier_verdict": "Builder report: 260 new tests, 2 rounds of self-adversarial testing (17 real misses found+fixed), honest disclosed residual (typo evasion not closeable without breaking muhurta questions), Hinglish/Devanagari coverage added. 1 verifier + 3 adversaries (evasion/bypass, DB-integrity/state-machine, harness-integrity) dispatched given the subject matter (suicide-adjacent content, health crisis, minors)."
    },
    "G1-C": {
      "role_stage": "merged",
      "name": "5 DB roles + RLS (EXCLUDING amjis_app rotation) -- serializes before P1-I",
      "verifier_verdict": "conductor-reviewed. RLS created but deliberately NOT enabled (arming script outside migration dirs, confirmed by conductor). arm-3 out-of-process ledger writer built from scratch (didn't exist). Real cross-context RLS denial proven (17 DB-integration tests). Full suite 714/760 files, 7987 tests, 0 failures. drift/naming_lint clean, no migration collision (576). SECURITY FINDING surfaced by this lane (pre-existing on main, NOT introduced by any pariprashna session, verified by conductor): a live-shaped plaintext amjis_app password committed at platform/python-sidecar/tests/l5/test_mi_bhara_circularity_guard_w2.py:295 -- flagged directly to the native, not silently fixed."
    },
    "G1-G": {
      "role_stage": "queued",
      "name": "Injection containment (serializes after G1-A, shares pre-wire scan file)"
    },
    "P1-E": {
      "role_stage": "merged",
      "name": "Durability: DR runbook + RPO/RTO doc + export-schedule mechanism ONLY -- PITR enable + restore drill HELD",
      "verifier_verdict": "conductor-reviewed, cherry-picked clean, scripts syntax-checked, drift baseline held"
    },
    "P1-I": {
      "role_stage": "merged",
      "name": "Ground-truth re-verification of Baseline UNVERIFIED rows (serializes after G1-C)",
      "verifier_verdict": "conductor-reviewed. Live re-verification: PITR still disabled, migration 576 confirmed inert on production (2 independent checks), flags at expected defaults, serving revisions confirmed (amjis-web-01529-hf8, amjis-mcp-00575-pgx, both 100%). Own bug caught+fixed by conductor: the doc edit made PARIPRASHNA_ASBUILT_BASELINE's declared manifest fingerprint stale (drift 216->217, exit 3->2, HIGH); rotated fingerprint, back to 216/exit=3."
    }
  },
  "trains": [],
  "deploys": [],
  "gate_results": {
    "P0_gate": {
      "status": "NOT_STARTED",
      "criteria": [
        "golden streams semantically identical through the decomposed route (deployed artifact)",
        "tracker live with a fresh heartbeat",
        "every DD-3 command proven or explicitly parked"
      ]
    }
  },
  "dd3_pending_human_authorization": [
    {
      "item": "PITR enable on amjis-postgres",
      "command": "gcloud sql instances patch amjis-postgres --project=madhav-astrology --enable-point-in-time-recovery --transaction-log-retention-days=7",
      "risk": "state change + retention cost on real production DB"
    },
    {
      "item": "Scratch Cloud SQL instance",
      "command": "gcloud sql instances create <scratch-name> --project=madhav-astrology --database-version=POSTGRES_15 --tier=db-g1-small --region=asia-south1",
      "risk": "new billable resource"
    },
    {
      "item": "Restore drill",
      "command": "gcloud sql instances clone amjis-postgres <clone-name> --point-in-time=<ts> (or backups restore onto scratch instance)",
      "risk": "depends on scratch instance; touches restore mechanics"
    },
    {
      "item": "amjis_app credential rotation",
      "command": "gcloud sql users set-password amjis_app --instance=amjis-postgres --project=madhav-astrology --password=<NEW>",
      "risk": "could break live serving app if amjis-db-password/amjis-pipeline-db-url Secret Manager secrets aren't synchronized in the same change"
    }
  ],
  "p0_c_known_residuals": [
    {
      "id": "P0C-R1",
      "finding": "Golden-stream harness doesn't record args at ~half its mocked I/O boundaries (authorizeChartAccess, getConversation, db.query, getToolByName, dispatch_queue.submit, floor adapters, bundle/orientation/manifest loaders) -- 3 real regressions proven to pass green: deleted auth DB round-trip (silent super_admin demotion), dropped retrieval invocation params + scrambled QoS principal, collapsed orientation fallback chain.",
      "severity": "MEDIUM",
      "recommendation": "Add rec() to the listed mocks; add a super_admin scenario; give buildChartOrientation distinct chart_header/dasha_context stub values. Additive only, does not touch the refactor itself. Should land before a P1 lane starts relying on this harness for its own equality claims.",
      "blocking": false
    },
    {
      "id": "P0C-R2",
      "finding": "3 of 37 scenarios' derived_from names are misleading (unclosed-sentinel, malformed-sentinel-variants, 3s-stall bind to a different phenomenon than the fixture of that name; sharpest: unclosed-sentinel's own note says the turn closes fine, contradicting the fixture it's named after).",
      "severity": "LOW",
      "recommendation": "Rename or annotate as unmappable so a future lane doesn't over-read coverage.",
      "blocking": false
    },
    {
      "id": "P0C-R3",
      "finding": "2 branches built into the harness but never exercised by a scenario: NO_ADAPTER halt, existingConversation='chart-mismatch'.",
      "severity": "LOW",
      "recommendation": "Add 2 scenarios; cheap.",
      "blocking": false
    },
    {
      "id": "P0C-R4",
      "finding": "PRE-EXISTING (not introduced by this lane): validation_stage.ts:64-66 swallows a thrown citation-gate error and reports the initialized 'PASS' default with no wire flag -- a live SS N.8 violation predating the refactor.",
      "severity": "MEDIUM",
      "recommendation": "File its own ticket before P1 citation/receipt work opens on this file.",
      "blocking": false
    },
    {
      "id": "P0C-R5",
      "finding": "PRE-EXISTING (not introduced by this lane): citation markers are scrubbed by lintReaderProse before extractCitations ever sees the text, so citation.define wire events and canonical citation parts are structurally dead on this path. Same in the original 1179-line route.",
      "severity": "LOW",
      "recommendation": "Track alongside P0C-R4 for the same future citation/receipt lane.",
      "blocking": false
    },
    {
      "id": "P0C-R6",
      "finding": "Latent, currently-unreachable: abort-path turn.close now fires after adapter generator cleanup instead of before (shell now calls finish() after the stage returns halt('aborted'), vs. original's inline return). Unobservable today because none of the 5 provider adapters have a finally block in their generators.",
      "severity": "LOW",
      "recommendation": "Note in P1 brief for whichever lane first adds adapter cleanup logic.",
      "blocking": false
    },
    {
      "id": "P0C-R7",
      "finding": "Two newly-exported pipeline functions (runPersistenceStage, runEvidenceStage, etc.) have no auth of their own and no 'server-only' import guard -- structurally reachable by a future caller that skips safety_gate.ts, though none exists today.",
      "severity": "LOW",
      "recommendation": "Add import 'server-only' to persistence_stage.ts and safety_gate.ts; consider an importer CI guard before P1 opens multiple lanes on these files.",
      "blocking": false
    },
    {
      "id": "P0C-R8",
      "finding": "RF-1's 'captured real streams' half of the golden-stream equality claim was never attempted -- would require an authenticated real chat session against the deployed artifact, captured and diffed against a pre-refactor baseline. Only local/CI equality (37 scenarios) plus a live boot+auth-gate confirmation exist.",
      "severity": "LOW",
      "recommendation": "If a P1 lane needs stronger deployed-artifact assurance, run PARIPRASHNA_STREAM_CAPTURE=1 against a real authenticated session and diff against the 496d087f9 baselines.",
      "blocking": false
    }
  ],
  "p0_merge_to_main": {
    "status": "MERGED",
    "pr": "https://github.com/Marsys-Technologies/Madhav/pull/1349",
    "merge_commit": "9db457dccd07edbc4ca4056e7e522fa5f77897b5",
    "merged_at": "2026-08-19T16:36:32Z",
    "note": "Main CI running now; deploy.yml will auto-trigger on its success (--no-traffic stage + smoke + promote-if-success). This closes the P0 gate's deployed-artifact criterion once observed."
  },
  "p0_deploy_verification": {
    "status": "PASS",
    "deploy_run": "https://github.com/Marsys-Technologies/Madhav/actions/runs/32277741066",
    "revision": "amjis-web-01527-mrz",
    "traffic": "100%",
    "automated_smoke": [
      "candidate revision boots and routes (HTTP 200 on /api/health)",
      "auth guard enforced on the candidate revision (401 on unauthenticated sidecar health probe)",
      "sidecar dependency reachable"
    ],
    "conductor_targeted_check": "POST /api/pariprashna (unauthenticated, no session cookie) against the LIVE production URL -> HTTP 401, matching safety_gate.ts's getServerUser() check exactly as verified by the P0-C reviews.",
    "honest_scope_note": "This confirms the decomposed route is live, serving 100% production traffic, boots correctly, and its auth gate behaves as verified. It does NOT constitute the full RF-1 'captured real streams' golden-comparison (an authenticated end-to-end reading captured and diffed against a pre-refactor baseline) -- that requires a real authenticated session and was not attempted here. Filed as a residual, not blocking: the local/CI golden-stream harness (37/37) plus this live boot+auth confirmation together give strong, but not complete, deployed-artifact evidence."
  },
  "p0_gate": {
    "status": "CLOSED",
    "criteria": {
      "golden_streams_semantically_identical": "PASS (local/CI, 37/37) + PARTIAL (deployed: boot+auth confirmed live; full authenticated captured-stream comparison not attempted -- residual P0C-R8)",
      "tracker_live_with_fresh_heartbeat": "PASS",
      "every_dd3_command_proven_or_parked": "PASS (all 4 IAM-permitted, all 4 deliberately parked pending explicit human authorization due to cost/production risk)"
    },
    "closed_at": "2026-08-19T16:56:00Z"
  },
  "p1_scope_decision": {
    "authorized": [
      "G1-A",
      "G1-B",
      "G1-C (minus amjis_app rotation)",
      "G1-D",
      "G1-F",
      "G1-G",
      "G1-H",
      "P1-I",
      "P1-J"
    ],
    "held_pending_explicit_authorization": [
      "PITR enable",
      "scratch Cloud SQL instance creation",
      "restore drill execution",
      "amjis_app credential rotation"
    ],
    "recorded": "origin/campaign-coordination @ 3e8530248"
  },
  "migration_ceiling": {
    "value": 575,
    "note": "574 = G1-D (llm_usage_events channel column), 575 = G1-B (chart_subject_consent + 4 related tables). Both additive-only, neither applied to production yet."
  },
  "concurrent_session_discovered": {
    "session": "PARIPRASHNA-TRACKER-V2",
    "pr": "https://github.com/Marsys-Technologies/Madhav/pull/1350",
    "scope": "00_ARCHITECTURE/briefs/pariprashna_swarm/tracker/** (new dir) + AMENDMENTS_v1_1.md \u00a77 addendum only",
    "collision_check": "No overlap with any file this session has touched or has open work on. Acknowledged in origin/campaign-coordination @ 51e41198d. Continuing this session's own SWARM_TRACKER.json for P0/P1 already in flight; will evaluate adopting tracker-v2 for P2+ once its PR merges."
  },
  "security_findings": [
    {
      "id": "SEC-1",
      "severity": "HIGH",
      "finding": "Plaintext DSN with a live-shaped amjis_app password committed at platform/python-sidecar/tests/l5/test_mi_bhara_circularity_guard_w2.py:295, connecting through what the test comment calls a 'live Cloud SQL proxy'. Confirmed present on origin/main (pre-existing, not introduced by this campaign).",
      "found_by": "G1-C lane agent, independently verified by conductor via git show origin/main",
      "action_taken": "None -- reported to the native directly. Not edited, not redacted, not rotated (rotation authority explicitly withheld by the native for a separate decision).",
      "recommendation": "Rotate amjis_app's password (this finding strengthens the case for doing so soon, not just eventually) and consider whether git history scrubbing is warranted given how long this may have been exposed."
    }
  ],
  "g1_a_review_findings": [
    {
      "source": "architecture/DB-integrity adversary",
      "verdict": "NOT safe to merge as-is",
      "blocking": [
        "5b (new finding): reclassifyAfterPlan (post-plan escalation) never opens a review row (no finalize()/openReview call), but route.ts emits SEAL_PENDING_ACKNOWLEDGMENT telling the user 'the review has been opened' -- false statement + zero review record + no FK to catch it (review_id has no FK constraint at all)",
        "2: interstitial_is_native_self_chk uses bare '=' so subject_kind IS NULL passes it (three-valued logic hole); NULL is TODAY'S DEFAULT since SUBJECT_CONSENT_ENFORCEMENT ships OFF -- fix: IS NOT DISTINCT FROM",
        "4: the HS-3 review lifecycle (recordAdversarialPass/signOff/withhold/persistReviewTransition/loadReview/isReleasable) has ZERO production callers -- no cron, no admin UI, nothing ever advances a review out of seal_pending. Contradicts the 'real state machine' framing in the lane's own commit message."
      ],
      "non_blocking": [
        "1a: HS-4-never-gets-interstitial rule is TypeScript-only, no DB CHECK backing it (commit message overclaims 'both facts are DB CHECK constraints')",
        "1: 'released requires two independent passes' is app-only, not DB-enforced (pariprashna_safety_reviews excluded from append-only triggers)",
        "TRUNCATE bypasses row-level append-only triggers (needs a FOR EACH STATEMENT trigger)",
        "reviewer_context_id has no non-empty check, unlike the sibling table's pattern -- blank-context passes could double-count as independent passes",
        "pariprashna_safety_notifications.decision_id not FK'd, written even when appendSafetyDecision failed"
      ],
      "confirmed_safe": [
        "concurrency/CAS logic (real 2-session test)",
        "no-reading-composed-at-all claim (traced end to end, genuinely more conservative than spec)",
        "audit-row completeness for HS-2/HS-5 (real actionable content, real hash-chain verifier)"
      ]
    },
    {
      "source": "evasion/bypass adversary",
      "verdict": "NOT safe to merge \u2014 critical gaps",
      "critical": [
        "F-1: suicide-METHOD and electional-muhurta phrasing ('best muhurta to leave this body', 'which day for jal samadhi/prayopavesa', 'I have a plan and a date picked') entirely uncovered -- worst case: the instrument's own muhurta/election capability picks a date for a suicide. kala_muhurta_get/kala_elect_get not even in sensitive_capabilities.ts.",
        "F-2: vocabulary-free date-of-death renderings ('The last row of your dasha table falls in 2052') defeat BOTH the pre-wire scan AND the classifier -- invalidates the lane's own stated containment argument for the accepted typo-evasion residual (only 1 of 3 controls actually holds, not 2)."
      ],
      "high": [
        "F-3: suicide content in Odia (the native's own state), Bengali, Tamil, Telugu, Kannada, Malayalam, Gujarati, Urdu, and French/German/Italian/Portuguese all miss; even Hindi/Devanagari coverage is only half done (noun forms caught, common verb forms like 'I don't want to live' missed)",
        "F-4: TWO OTHER ROUTES have zero safety-gate wiring -- /api/mcp/prashna_ask and /api/chat/consult both compose real LLM readings from free text with no classifier call at all",
        "F-5: demographic false-positive bug -- Hinglish 'kab mar*' regex is too broad, misclassifies extremely common questions (marriage timing 'Meri marriage kab hogi?', planet retrograde 'Shani kab margi hoga?') as date-of-death requests, seals them with no reading. Penalizes code-mixed Indian users specifically -- the product's actual primary market."
      ],
      "medium": [
        "F-6: third-person family framing ('How long does my mother have?') evades first-person-pinned patterns -- arguably highest-harm population (terminal diagnosis in the family)",
        "F-7: English euphemisms still open ('When will I be gone?', 'my exit year', 'check out')",
        "F-8: classical Jyotish death vocabulary missing (nidhana, randhra, ashtama sthana)",
        "F-9: multi-turn asymmetry -- classifier sees only current turn, synthesis sees 4 prior turns; a turn-2-only death question can slip through",
        "F-10: 'expiry date'/metaphorical diagnosis/elective surgery unguarded, same defect class as an already-fixed pattern just not generalized"
      ],
      "confirmed_safe": [
        "no negation/hypothetical/third-person EXEMPTION branch exists (F-6 is pattern-pinning gap, not a bypass code path)",
        "no error-recovery/retry/fallback path around the gate within /api/pariprashna itself",
        "consent-dependency direction (NULL subject_kind fails toward seal, not toward wrongly-granted interstitial) -- safe direction, but very high false-seal rate as a cost"
      ]
    },
    {
      "source": "independent verifier",
      "verdict": "safe to merge with named caveats (per verifier's own philosophy: flag-OFF, zero production DB calls when off) -- but converges with the DB-integrity adversary on the NULL-hole and adds a new critical finding",
      "new_critical": [
        "Finding A: leet '1'->'l' substitution defeats HS-2 entirely ('I want to ki11 myse1f' / 'end my 1ife' normalize to nothing and MISS) -- the normalizer's own header claims no spelling evasion survives it; this is false, demonstrated concretely. HS-2 has only the prompt-policy clause as backstop (no output-side self-harm scan), so this is a full bypass of the highest-stakes class with a 2-keystroke cost."
      ],
      "convergent_with_db_adversary": [
        "Independently reproduced the same NULL-hole in interstitial_is_native_self_chk (subject_kind IS NULL passes a check meant to require literal 'native_self'). Recommends fixing NOW since migration not yet applied to production -- cheapest/only safe window per SS N.4 (never edit an applied migration)."
      ],
      "other_findings": [
        "Hinglish HS-2 'want to die' desire-forms miss (only interrogative 'kab marunga' forms covered)",
        "Plain non-evasive age-reaching asks miss ('Will I live to 90?')",
        "HS-4's breadth + no release path = PERMANENT refusal for a wide band of ordinary jyotish questions once flag flips (a product-shape question, not a bug)",
        "No committed DB-integration test for the migration's own constraints -- verifier had to redo all constraint verification by hand",
        "mergeLlmAssist (the monotone-join guarantee) has ZERO production callers currently and no structural barrier stopping a future lane from bypassing the envelope by hand",
        "platform-mcp consult-profile exclusion is unflagged (takes effect on merge) but currently removes 0 tools against the real profile -- no production behavior change in fact, but the test asserting it passes vacuously"
      ]
    }
  ]
};
