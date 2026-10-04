---
artifact: ENVIRONMENT_BRANCH_POLICY_FINDING_20261004
version: "1.1"
status: RECORD — owner to decide on the data-plane-production-cutover recommendation
date: 2026-10-04
written_by: "Stream B (madhav-8b) at the steward's request (SIT-ROW5-6)"
audience: "the owner, reading in the morning"
evidence: "/Users/Dev/pravaha/run/sitting-20261003/manual/{act5.txt, row6-gate-proof.txt, row6-secret-neutralised.txt}"
sources:
  - "GitHub Docs, Deployments and environments (deployment branches): \"If no branch protection rules are defined for any branch in the repository, then all branches can deploy.\" https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments"
  - "GitHub REST, Create or update an environment: protected_branches = \"Whether only branches with branch protection rules can deploy to this environment.\"; custom_branch_policies = \"Whether only branches that match the specified name patterns can deploy to this environment.\"; they must be opposite. https://docs.github.com/en/rest/deployments/environments"
  - "GitHub REST, Deployment branch policies: name = \"The name pattern that branches or tags must match in order to deploy to the environment.\"; type = branch or tag. https://docs.github.com/en/rest/deployments/branch-policies"
changelog:
  - "1.0 (2026-10-04): recorded."
  - "1.1 (2026-10-04, steward SIT-CUTOVER-ENV-FACTS M20261004T010608-4373): CORRECTION — the automatic deploy does NOT use data-plane-production-cutover (both jobs that declare it are manual-dispatch-only); the earlier advice against a required reviewer was wrong on that point and is replaced by an exact list of what would wait."
---

# A safety lock that was not locking — and what to do about it

## Bottom line
During the proof of the seal-approval gate, a job started from a throw-away work branch was NOT turned away by the environment's "protected branches only" rule; it waited for the approver and ran once approved. The rule does nothing in this repository. Nothing harmful happened (the proof job does nothing and holds no secret), but the same rule is the only branch restriction on the environment that holds the database administrator secrets.

## Why the rule did nothing
"Protected branches only" is judged against classic branch-protection rules. GitHub's own documentation says: "If no branch protection rules are defined for any branch in the repository, then all branches can deploy." This repository has NO classic rules — only a newer-style "ruleset" on `main` — so every branch counts as allowed. (GitHub's branch listing still calls `main` "protected" because of the ruleset, which is why the setting looked right.) That matches what was observed: `main` shows as protected, the work branch does not, yet both were admitted.

## What the steward did at once
The admin-secret refresh made at 01:00Z was overwritten at 01:04Z with a throw-away value of the same shape (the real database password is unchanged). Between the two moments only the steward's own create-roles run (from `main`) used that environment.

## The fix for the seal environment (`gochara-seal`) — proposed, to be checked by Codex before use
1. Replace the policy with a custom one: `PUT /repos/Marsys-Technologies/Madhav/environments/gochara-seal` with the full body (the call replaces settings, so all are repeated): `{"wait_timer":0,"prevent_self_review":false,"can_admins_bypass":false,"reviewers":[{"type":"User","id":<owner user id>}],"deployment_branch_policy":{"protected_branches":false,"custom_branch_policies":true}}`.
2. Add exactly one allowed branch: `POST /repos/Marsys-Technologies/Madhav/environments/gochara-seal/deployment-branch-policies` with `{"name":"main","type":"branch"}`.
3. Read back: the environment shows `protected_branches:false, custom_branch_policies:true`, the one reviewer unchanged, `can_admins_bypass:false`; the policy list is exactly one entry, `main` (branch).
4. Re-prove: a proof run from the work branch must now be REFUSED (never waiting, no pending approval); a proof run from `main` waits, is approved with the ruling comment, and runs.

## The same weakness on `data-plane-production-cutover` (NOT changed — your decision)
- It holds the administrator and owner secrets (names only): DATA_PLANE_ADMIN_DATABASE_URL, DATA_PLANE_MIGRATOR_DATABASE_URL, DATA_PLANE_OWNERSHIP_ADMIN_DATABASE_URL (currently a throw-away value), DATA_PLANE_VERIFIER_DATABASE_URL, DATA_PLANE_RESTORE_VALIDATION_* and DATA_PLANE_BACKUP_RESTORE_ID. It has NO required reviewer, admins may bypass, and the same ineffective branch rule.
- Who declares it (verified against `deploy.yml` on main): exactly two jobs, `privileged-bootstrap` ("One-time Protected DB Bootstrap") and `jataka-protected-migrations` ("Apply Protected Public-Schema Migrations" — the protected window, act 9), and BOTH run only on a manual dispatch (`github.event_name == 'workflow_dispatch'`). Two more workflow files name it: `data-plane-credential-preflight.yml` (manual dispatch only, no branch guard) and `gochara-role-provisioning-oneshot.yml` (manual dispatch; its job has an in-file `github.ref == main` guard, which a work branch that edits the file can remove). The routine jobs ("Inspect DB Migration State", "Apply Routine DB Migrations") declare NO environment (they use a repository secret); automatic deploys never touch this environment.
- Who can exploit it: the repository has a single collaborator with write access (the owner's account), so no outsider is involved. The real exposure is that anything acting with the owner's token (including these automated sessions) could run a modified workflow from any branch and read those secrets. It adds little beyond what that token can already do, but it removes the one server-side brake.
- All recorded uses of this environment in the last days ran from `main` (five of five).
- **Recommendation, in two independent steps:**
  1. **Branch rule (recommended now-ish; no job waits):** apply the same two calls as above (custom policy, one entry `main`). Nothing in normal use changes — every recorded use ran from `main`, routine and automatic deploys do not use the environment, and Suvarṇa confirms it does not disturb their W1. Easy to undo. Best done well before 06:30Z or after SETTLED-1 — not inside Suvarṇa's window.
  2. **Required reviewer (optional; adds a manual approval):** a reviewer only means something if administrators cannot bypass it, so it needs THREE settings: a reviewer, `can_admins_bypass:false`, and (with one account) `prevent_self_review:false`. **Exactly what would start WAITING for an approval:** (a) the manual dispatch of the protected window (act 9, `jataka-protected-migrations`) — one extra approval click at the sitting; (b) the manual one-time bootstrap (`privileged-bootstrap`); (c) the one-shot role workflow `gochara-role-provisioning-oneshot.yml` (create-roles); (d) `data-plane-credential-preflight.yml`. **What would NOT wait:** every automatic deploy and the routine migration job. The approver would be the steward under your account (ruling 2), so it adds a second look and an audit record but not a second person. The sitting checklist would need one extra step at act 9.
  Decision: yours; the steward will not touch the environment without your word.
