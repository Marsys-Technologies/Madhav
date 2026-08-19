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
    "n": 0,
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
      "role_stage": "queued",
      "name": "environment (worktree farm, cloud-sql-proxy, template test-DB, migration allocator, flag registry)",
      "worktree": null,
      "branch": null,
      "last_event_ts": null,
      "verifier_verdict": null,
      "refuter_votes": []
    },
    "P0-C": {
      "role_stage": "queued",
      "name": "PORTS REFACTOR of route.ts (RF-1, gating lane -- verifier + 3 adversaries required before other lanes open)",
      "worktree": null,
      "branch": null,
      "last_event_ts": null,
      "verifier_verdict": null,
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
      "role_stage": "queued",
      "name": "design-plan grounding pass (docs)",
      "worktree": null,
      "branch": null,
      "last_event_ts": null,
      "verifier_verdict": null,
      "refuter_votes": []
    },
    "P0-F": {
      "role_stage": "queued",
      "name": "DD-2 anthropic delist + DD-3 infra automation probes",
      "worktree": null,
      "branch": null,
      "last_event_ts": null,
      "verifier_verdict": null,
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
  }
};
