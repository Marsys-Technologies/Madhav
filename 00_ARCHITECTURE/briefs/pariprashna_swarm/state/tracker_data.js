// tracker_data.js — generated from SWARM_TRACKER.json. Do not hand-edit; the
// conductor regenerates this file whenever SWARM_TRACKER.json changes.
window.TRACKER = {
  "schema_version": "1.1",
  "session_id": "PARIPRASHNA-CONDUCTOR-P0-FRESH-2026-08-19",
  "phase": "P0",
  "phase_status": "STEP_0_COMPLETE_ENTERING_IGNITION",
  "wave": "P0-IGNITION",
  "heartbeat_ts": "2026-08-19T14:19:59Z",
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
      "role_stage": "verifying",
      "name": "PORTS REFACTOR of route.ts (RF-1, gating lane -- verifier + 3 adversaries required before other lanes open)",
      "worktree": "worktree-agent-a6279b3f3d579e906",
      "branch": "pariprashna/p0-c-ports-refactor",
      "last_event_ts": "2026-08-19T15:05:00Z",
      "verifier_verdict": "1 verifier + 3 adversaries (behavioral/security/harness-integrity lenses) dispatched, in progress. Builder's own report: 9 modules, route.ts 1179->237 lines, 37/37 scenarios pass, 700 files/7796 tests 0 failures. Honest limits disclosed: 12-fixture corpus not directly executable (used 37 derived scenarios instead); deployed-stream capture half of RF-1 UNMET; one named ordering blind spot; 3 pre-existing bugs found+reported not fixed; residual 2-way collision on safety_gate.ts for P1.",
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
  ]
};
