---
artifact: ENVIRONMENT_BRANCH_POLICY_FINDING_20261004
version: "1.0"
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
- Five workflow files use it: `deploy.yml` (two jobs), `data-plane-credential-preflight.yml`, `gochara-role-provisioning-oneshot.yml`. Only the one-shot has a `github.ref == main` guard, and that guard lives inside the file, so a work branch that edits the file can remove it; only the environment's own rule is enforced by GitHub itself.
- Who can exploit it: the repository has a single collaborator with write access (the owner's account), so no outsider is involved. The real exposure is that anything acting with the owner's token (including these automated sessions) could run a modified workflow from any branch and read those secrets. It adds little beyond what that token can already do, but it removes the one server-side brake.
- All recorded uses of this environment in the last days ran from `main` (five of five).
- **Recommendation:** apply the same two-call fix to `data-plane-production-cutover` (custom policy, one entry `main`). It is the smallest change, cannot break the existing flows (they all run from `main`), and is easy to undo (set the policy back). Do NOT add a required reviewer there: the automatic deploy uses the environment and would stop waiting for a person. Optionally add the same `main` guard line to the other jobs that use it. Decision: yours; the steward will not touch it without your word.
