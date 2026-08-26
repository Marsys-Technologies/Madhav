# NTAP tracker monitor operator runbook

## Scope and authority

Use this runbook only as an authenticated active `super_admin`. The operational
view is `/admin/nirmana-elevation`; its authenticated API is
`GET /api/admin/nirmana-elevation/snapshot`, and the governed write boundary is
`POST /api/admin/nirmana-elevation/evidence`.

The scheduler monitor is read-only with respect to program identity, acceptance,
and execution. It records observations only. It never freezes a definition,
supersedes a definition, advances a stage, starts a build, or changes progress.

Do not use direct SQL, import historical JSON/JSONL ledgers, or manually edit
progress, stage, denominator, percentage, or monitor records. These are not
alternate acceptance paths.

## Baseline acceptance

1. In the authenticated dashboard Audit Drawer, or from the authenticated snapshot
   API, check `program_sync.status`. Continue only when it is `baseline_missing`
   and the latest observation is fresh (the `program_monitor` source is `fresh`).
   From that same fresh authenticated Audit Drawer observation, record both the
   displayed `candidate_definition_sha256` and
   `candidate_catalogue_sha256`. Do not combine digests from different
   observations, calculate or infer either digest, or retrieve a substitute
   through the scheduler-only internal endpoint.
2. Choose a new, unique definition revision, for example `ntap-v1`. Submit the
   evidence command with the exact two current candidate digests:

   ```json
   {
     "command": "accept_baseline_candidate",
     "definition_revision": "ntap-v1",
     "expected_candidate_sha256": "<exact current candidate_definition_sha256>",
     "expected_candidate_catalogue_sha256": "<exact current candidate_catalogue_sha256>"
   }
   ```

   Send it only to `POST /api/admin/nirmana-elevation/evidence` while authenticated
   as `super_admin`. The server re-reads the live registry serializably; a `409`
   means the candidate changed or another current definition exists. A `429`
   means the per-actor mutation limit was reached; wait for `Retry-After`, then
   re-read one fresh Audit Drawer observation before retrying. Never substitute a
   digest by hand.
3. Confirm the result is `created` (or the exact safe retry is `idempotent`), then
   refresh the snapshot after the next monitor observation. Verify that the
   definition is frozen and synchronization reflects the new observation. Baseline
   acceptance establishes program identity and its label catalogue only: stage,
   layer, wave, asset lifecycle, and progress remain unknown until their separate
   typed acceptance receipts exist. The actor-attributed, append-only
   `asset_label_catalogue_accepted` campaign receipt committed by the acceptance
   transaction is the normative audit provenance. `admin_audit_log` is a
   best-effort operator index only; its absence neither creates nor erases an
   acceptance.

## Plan-adaptation review and adoption

1. When `program_sync.status` is `plan_adaptation_required`, stop treating the
   accepted denominator as current. Capture the observation timestamp, current and
   candidate definition digests, and `affected_asset_ids` from the authenticated
   dashboard/API. This is a proposal signal, not a new plan and not execution
   authority.
2. Review the registry/DAG change and prepare a reviewed, freezable replacement
   manifest outside this monitor. The proposed manifest and its SHA-256 must match
   the live registry; do not rebuild it from historical ledgers or mutate tables to
   force a match. Confirm whether the current frozen definition has campaign events
   or build runs: the governed supersession boundary refuses supersession once it
   does.
3. Only after explicit plan approval, submit one authenticated supersession command:

   ```json
   {
     "command": "supersede_definition",
     "campaign_id": "nirmana-elevation",
     "expected_current_revision": "<current frozen revision>",
     "expected_current_manifest_sha256": "<exact current digest>",
     "new_definition_revision": "<new unique revision>",
     "new_manifest": "<reviewed manifest object>",
     "new_manifest_sha256": "<SHA-256 of that exact manifest>"
   }
   ```

   Send it only to `POST /api/admin/nirmana-elevation/evidence`. A `409` is a
   concurrency or eligibility guard, not permission to retry with altered values.
   Re-read the dashboard/API, resolve the governed conflict, and resubmit only an
   exact approved replacement. Do not use `record_definition`/`freeze_definition`
   as a shortcut around explicit supersession.
4. After a successful `superseded` response, wait for the next scheduler observation
   and confirm `program_sync.status` is no longer `plan_adaptation_required` before
   relying on the new denominator. The monitor still does not create acceptance
   receipts or progress.

## Freshness verification and incident handling

- The scheduler cadence is five minutes. An observation is fresh only while the
  snapshot's `program_monitor` source is `fresh`; the snapshot marks it stale once
  `age_seconds` exceeds 900 seconds (five-minute cadence plus ten-minute grace).
  A quiet runtime can be fresh; lack of active work is not an error.
- For `source_unavailable`, `release_attention`, `evidence_refresh_required`, or
  `label_refresh_required`, preserve the displayed degraded status and investigate
  the authoritative source or governed evidence path. Do not mark progress green,
  edit an observation, or treat the previous observation as current.
- Scheduler deployment verification is a protected-main operator activity. After a
  reviewed protected-main apply, configure the existing `MARSYS_CRON_SECRET` as
  `X-Marsys-Cron-Secret` using the established secret-header procedure, then verify
  authenticated observations arrive on the expected cadence. Never place the secret
  in Terraform, source control, SQL, screenshots, or an `Authorization` header.
