---
artifact: DECLARED_CONTROL_PLANE_EXCEPTION_20261003
version: "1.0"
status: RECORD — owner to confirm or revoke in the morning
date: 2026-10-03
declared_at: "2026-10-03T23:43:23Z"
declared_by: "the steward, under the owner's account, on the authority of Ruling 4 (overnight autonomy; decisions/NATIVE_DIRECT_RULINGS_20261003.md)"
second_eyes: "Stream B (madhav-8b), AGREE with conditions, M20261003T234304-2f7f"
remedy_source: "ROLES_AND_SEAL_PROVISIONING_RUNBOOK_v1_0.md, act-7 row (§ failure table, line 225): the owner's exact triple declared in DATA_PLANE_VERIFIER_CONTROL_EXCEPTIONS and recorded in the act-3 report"
evidence: "/Users/Dev/pravaha/run/sitting-20261003/manual/{act3.txt, act4.txt, act10.txt, act7-preflight-after-act4.txt, act7-exception-test.txt, act3-declared-exception.txt}"
changelog:
  - "1.0 (2026-10-03): recorded by Stream B at the steward's request (ST SIT-EXCEPTION-RECORD)."
---

# Declared control-plane exception — Google-managed Firebase service agent

## What was declared
Repository variable `DATA_PLANE_VERIFIER_CONTROL_EXCEPTIONS` (Marsys-Technologies/Madhav), exactly one triple, nothing else:

```
projects/madhav-astrology|roles/firebase.managementServiceAgent|serviceAccount:service-938361928218@gcp-sa-firebase.iam.gserviceaccount.com
```

## Why it was needed
Sitting acts 3, 10 and 4 completed and read back clean (verifier service account with exactly `roles/cloudsql.client` and no keys; its policy exactly one `roles/iam.serviceAccountUser` binding for the deployment principal; phase variable `deployable`; secret container with exactly one accessor, the verifier account, no version; builder policy unchanged). Act 7's isolation preflight (main `b20bbb520`, strict, `deployable`) then REFUSED:

`Inherited or aggregate capability to create/upload keys for, mint tokens for, impersonate or rewrite the policy of the verifier service account remains outside the declared control-plane exceptions: projects/madhav-astrology:roles/firebase.managementServiceAgent:serviceAccount:service-938361928218@gcp-sa-firebase.iam.gserviceaccount.com`

Once the verifier account exists the same check runs in every routine deploy (`deploy.yml`'s four preflight steps), so the refusal would have failed every deploy closed. The alternative to declaring the exception was rolling acts 4, 10 and 3 back the same night.

## The true trigger (correction recorded)
The steward's first note named `iam.serviceAccounts.create/get/list` as the trigger; that was wrong — those three are not in the preflight's `SA_CONTROL_PERMISSIONS`. Stream B described the role read-only (`gcloud iam roles describe roles/firebase.managementServiceAgent`, 111 permissions) and intersected it with that set: **the only hit is `resourcemanager.projects.setIamPolicy`** (R15-1 clause: a capability to rewrite an ANCESTOR's policy). The role holds no `iam.serviceAccountKeys.*`, no `actAs` / `getAccessToken` / `getOpenIdToken` / `signBlob` / `signJwt` / `implicitDelegation`, no `iam.serviceAccounts.setIamPolicy` and no `secretmanager.*`. "No setIamPolicy" is true only of the service-account policy, not of the project.

## Why it was missing from the allow-list (oversight, not a decision)
`isCanonicalGoogleServiceAgentGrant` (`platform/scripts/data-plane-secret-isolation-preflight.ts`) lists ten Google service-agent roles, built from the services the project visibly uses. Nothing in the preflight or its tests mentions Firebase, and the 2026-10-03 policy read recorded in the runbook enumerated only the named human/admin roles, so this Google-managed agent was never enumerated. It is an omission.

## What the exception allows — and does not
- ALLOWS exactly: that one binding (project `madhav-astrology`, that role, that member, UNCONDITIONAL — `binding.condition === undefined`) to be present when the verifier-control gate runs. The triple is canonicalised by `parseDeclaredExceptions` / `canonicalResource` (a project number resolves to the project id).
- DOES NOT allow: any other agent, role, member, resource or conditional binding; any wildcard. The preflight still refuses everything else, and the other gates are unaffected: a local run with the triple in the process environment exited 0, i.e. it passed ALL isolation gates (secret-accessor and builder-impersonation checks have no exception mechanism and also passed — the runbook's "an exception must satisfy ALL gates" condition).
- The member is a Google-owned service agent: no principal in this project holds its key, can mint its token or impersonate it, so the capability is exercisable only by Google's Firebase management backend through its fixed API behaviour — not by the builder, the application or a human. No new path to the verifier's credential for any principal this project controls.
- The variable reaches the preflight's process environment on all four `deploy.yml` invocations (the `env:` line sits in the same step as each call: lines 538/540, 885/886, 950/951, 1233/1234 on main `b20bbb520`); no other workflow or script invokes the preflight.

## How to revoke
`gh variable delete DATA_PLANE_VERIFIER_CONTROL_EXCEPTIONS --repo Marsys-Technologies/Madhav` — full strictness returns at the next deploy, which would then refuse again at the isolation step until the Firebase agent's project-level binding is removed or the allow-list is corrected (below).

## Owner decision (morning)
The owner CONFIRMS (keep the declaration until the allow-list PR below lands, then the variable can be deleted) or REVOKES (delete the variable; deploys then fail closed until the binding is dealt with). Authority tonight rested on Ruling 4; a security-relevant exception is not on the reserved list, but it is recorded for the owner on purpose.

## Follow-up (after the window, reviewed — never at the sitting)
A reviewed PR adds the exact `roles/firebase.managementServiceAgent` ↔ `serviceAccount:service-<projectNumber>@gcp-sa-firebase.iam.gserviceaccount.com` pair to `isCanonicalGoogleServiceAgentGrant` with a test (positive for that pair, negative for a different member or a conditional binding), after which the declared variable is deleted. Stream B owns that code (#2961's preflight).

## Act-3 report addendum (runbook §3 terms)
- Act: 3 — create the verifier service account and its one project role; ADDENDUM: act-7 isolation refusal, control-plane exception declared.
- Identity used: mail.abhisek.mohanty@gmail.com (the owner's account, driven by the steward).
- UTC timestamp: act 3 ran 2026-10-03T23:29:59Z–23:30:18Z; exception declared 2026-10-03T23:43:23Z.
- Resources created by act 3: service account `gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com` (`roles/cloudsql.client`, no keys). Resource changed by the addendum: repository variable `DATA_PLANE_VERIFIER_CONTROL_EXCEPTIONS` (one triple).
- Read-only verification output: manual/act3.txt, act7-preflight-after-act4.txt (the refusal), act7-exception-test.txt (exit 0 with the triple in the process environment), act3-declared-exception.txt.
- Rollback command: `gh variable delete DATA_PLANE_VERIFIER_CONTROL_EXCEPTIONS --repo Marsys-Technologies/Madhav`.
- Audit-log reference: the GitHub repository-variable audit entry at 2026-10-03T23:43Z and the Cloud Audit Logs for the act-3 calls (steward to attach the entries).
- NEXT ACT WAITS FOR THE STEWARD'S 'continue' (the live proof is the next routine deploy's four isolation steps).
