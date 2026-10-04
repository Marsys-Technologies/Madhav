---
artifact: DECLARED_CONTROL_PLANE_EXCEPTION_20261003
version: "1.3"
status: RECORD — owner to confirm or revoke in the morning
date: 2026-10-03
declared_at: "2026-10-03T23:43:23Z"
declared_by: "the steward, under the owner's account, on the authority of Ruling 4 (overnight autonomy; decisions/NATIVE_DIRECT_RULINGS_20261003.md)"
second_eyes: "Stream B (madhav-8b), AGREE with conditions, M20261003T234304-2f7f"
remedy_source: "ROLES_AND_SEAL_PROVISIONING_RUNBOOK_v1_0.md, act-7 row (§ failure table, line 225): the owner's exact triple declared in DATA_PLANE_VERIFIER_CONTROL_EXCEPTIONS and recorded in the act-3 report"
evidence: "/Users/Dev/pravaha/run/sitting-20261003/manual/{act3.txt, act4.txt, act10.txt, act7-preflight-after-act4.txt, act7-exception-test.txt, act3-declared-exception.txt}"
changelog:
  - "1.0 (2026-10-03): recorded by Stream B at the steward's request (ST SIT-EXCEPTION-RECORD)."
  - "1.1 (2026-10-04): adds Codex's residual-risk statement (reviews/ASTRA_REVIEW_C53_FIREBASE_AGENT_ALLOWLIST_v1_0.md, on PR #3119 head 54b33e11f) near the top for the owner, and updates the follow-up: the allow-list change is confined to the verifier-control gate (PR #3119 head ab96a9fa8). Stream B, at the steward's request (ST C53-CODEX). The 'allows' and 'revoke' sections are unchanged; one sentence under 'What the exception allows' is qualified (see the residual-risk section)."
---

# Declared control-plane exception — Google-managed Firebase service agent

## Residual risk — the owner must read this sentence before confirming or revoking
**The sentence (Codex ASTRA review v1.1, ACCEPT on PR #3119 head ab96a9fa8, verbatim): "the owner accepts that the Firebase agent's project-IAM rewrite authority can be used to grant control over the verifier."**

**Condition (steward, M20261004T062516-0d64):** PR #3119 stays DRAFT and unmerged until (a) the S-L1 hold ends and (b) the OWNER has confirmed the exception with the sentence above in front of him. Merging the allow-list change makes that acceptance permanent in code, so it is the owner's decision, not the steward's or Stream B's. Codex's answer to "may this be merged and the variable then removed" is YES for the Firebase-only declared exception — a technical ACCEPT, not the owner's confirmation. Until then the declared variable stays as it is.

Codex's earlier statement (v1.0 review, on head 54b33e11f; recorded here in substance): **"same class" is fair for Google MANAGEMENT agents, but it is NOT equivalent AUTHORITY.** None of the ten Google service agents already on the allow-list holds `resourcemanager.projects.setIamPolicy`; the Firebase management agent does. Its project-IAM rewrite authority is materially broader — misuse of it could grant secret access or verifier impersonation to itself or to others.

What bounds that risk today (facts, not reassurance): the member is Google-owned (no principal in this project holds its key, can mint its token or impersonate it), so the authority is exercisable only through Google's Firebase management backend; and the allow-list change that PR #3119 proposes is now confined to the VERIFIER-CONTROL gate only — the builder-impersonation gate keeps the original ten entries and would still reject this agent if its role ever gained an impersonation permission (cross-gate regression test). What is NOT bounded: while the declaration (or the PR) is in force, the verifier-control gate does not flag this agent's project-level `setIamPolicy`. That is a standing, owner-visible exception to the verifier-control rule, not a neutral oversight fix.


## Incident — the variable was deleted by a tracker report (2026-10-04, dated note)
- **What happened.** `DATA_PLANE_VERIFIER_CONTROL_EXCEPTIONS` was deleted at **2026-10-04T05:48:58Z** under the owner's `gh` identity. Audit-log line: `repo.remove_actions_variable` (the steward's reading of the repository audit log).
- **Whose action.** Stream B's session (madhav-8b). At 05:48:56Z Stream B sent a tracker report (ref B6.0, the C53 report) whose text was passed to the shell inside a DOUBLE-QUOTED string. The text recommended the deletion step and wrote that command in backticks; in a double-quoted string the shell executes a back-quoted span, so the delete ran. The report exited 0 and the slip was not noticed until the steward asked at 09:07Z. No intent to delete: the report only described the post-merge step (item b of its own list).
- **Effect.** From 05:48:58Z to 09:08Z every routine deploy failed its isolation step on the Firebase agent's project-level binding (the exception no longer masked it) and skipped migrations — Suvarna's migration 1256 was not applied and the protected train could not run (about three hours).
- **Repair.** The steward restored the variable at 09:08Z with the same single triple (`projects/madhav-astrology|roles/firebase.managementServiceAgent|serviceAccount:service-938361928218@gcp-sa-firebase.iam.gserviceaccount.com`). Stream B changed nothing in the interval and did not restore it itself.
- **Audit by Stream B.** Every Bash command of the session was searched: the only other double-quoted report containing back-quoted spans (2026-10-03T00:57:58Z) held three spans that are not commands (they failed as command-not-found and executed nothing). No other `gh variable` / `gh secret` write was run by Stream B.
- **Standing rule (steward, M20261004T090839-be2b).** Report and message text is never passed to the shell inside double quotes: write it to a file with a quoted heredoc (or use single quotes), check the file, pass it with the file's content only; never put backticks or dollar-parenthesis in a command line that is not meant to execute; quote commands in reports as plain words; re-read the exact command line before sending any report that mentions a destructive command (delete, drop, revoke, reset, rm, force).

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
- The member is a Google-owned service agent: no principal in this project holds its key, can mint its token or impersonate it, so the capability is exercisable only by Google's Firebase management backend through its fixed API behaviour — not by the builder, the application or a human. (Qualified in v1.1: this is a statement about WHO can exercise the capability, not about its breadth — see "Residual risk" above: a project-IAM rewrite authority is materially broader than that of the ten listed agents.)
- The variable reaches the preflight's process environment on all four `deploy.yml` invocations (the `env:` line sits in the same step as each call: lines 538/540, 885/886, 950/951, 1233/1234 on main `b20bbb520`); no other workflow or script invokes the preflight.

## How to revoke
`gh variable delete DATA_PLANE_VERIFIER_CONTROL_EXCEPTIONS --repo Marsys-Technologies/Madhav` — full strictness returns at the next deploy, which would then refuse again at the isolation step until the Firebase agent's project-level binding is removed or the allow-list is corrected (below).

## Owner decision (morning)
The owner CONFIRMS (keep the declaration until the allow-list PR below lands, then the variable can be deleted) or REVOKES (delete the variable; deploys then fail closed until the binding is dealt with). Authority tonight rested on Ruling 4; a security-relevant exception is not on the reserved list, but it is recorded for the owner on purpose.

## Follow-up (after the window, reviewed — never at the sitting)
A reviewed PR adds the exact `roles/firebase.managementServiceAgent` ↔ `serviceAccount:service-<projectNumber>@gcp-sa-firebase.iam.gserviceaccount.com` pair to `isCanonicalGoogleServiceAgentGrant` with a test (positive for that pair, negative for a different member or a conditional binding), after which the declared variable is deleted. Stream B owns that code (#2961's preflight).

**Status (2026-10-04):** PR #3119 (draft) implements it. Codex ACCEPT_WITH_AMENDMENTS on head 54b33e11f: the matcher is shared with the builder gate (`assertEffectiveIsolation`), so the Firebase exemption was confined to the verifier-control gate only (head ab96a9fa8; the original ten entries byte-identical; cross-gate regression, foreign-project-resource and mixed-member tests added). Codex v1.1 ACCEPTED head ab96a9fa8 (40/40 at that head; 39/40 against 54b33e11f, failing exactly the cross-gate regression). Merge now waits on the owner, not on review: PR #3119 stays DRAFT until the hold ends AND the owner has confirmed the exception with the residual-risk sentence in front of him (steward ruling, 2026-10-04T06:25Z). Only after the merge and the deploy is the variable deleted, then the isolation proof re-run.

## Act-3 report addendum (runbook §3 terms)
- Act: 3 — create the verifier service account and its one project role; ADDENDUM: act-7 isolation refusal, control-plane exception declared.
- Identity used: mail.abhisek.mohanty@gmail.com (the owner's account, driven by the steward).
- UTC timestamp: act 3 ran 2026-10-03T23:29:59Z–23:30:18Z; exception declared 2026-10-03T23:43:23Z.
- Resources created by act 3: service account `gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com` (`roles/cloudsql.client`, no keys). Resource changed by the addendum: repository variable `DATA_PLANE_VERIFIER_CONTROL_EXCEPTIONS` (one triple).
- Read-only verification output: manual/act3.txt, act7-preflight-after-act4.txt (the refusal), act7-exception-test.txt (exit 0 with the triple in the process environment), act3-declared-exception.txt.
- Rollback command: `gh variable delete DATA_PLANE_VERIFIER_CONTROL_EXCEPTIONS --repo Marsys-Technologies/Madhav`.
- Audit-log reference: the GitHub repository-variable audit entry at 2026-10-03T23:43Z and the Cloud Audit Logs for the act-3 calls (steward to attach the entries).
- NEXT ACT WAITS FOR THE STEWARD'S 'continue' (the live proof is the next routine deploy's four isolation steps).
