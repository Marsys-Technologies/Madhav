---
artifact: MADHAV_DATA_PLANE_RI02_SECURITY_SOURCE_ACCEPTANCE
version: "1.0"
status: SECURITY_CLEAR_SOURCE_ACCEPTED
recorded_at: 2026-09-15T16:51:15Z
authority: DP-SD-018 and RI02-R-002/RI02-R-003
reviewed_branch_tip: da498ebd980cac87796eceb889c7f1c42cfb952b
integrated_equivalent_tip: d22533825613c3d428bd844a5dfdc2c0c283b088
verdict: PASS_SECURITY_CLEAR
recorder_role: evidence_recorder_not_verifier
---

# MADHAV Data Plane RI-02 Security Source Acceptance v1.0

## 1. Recorded independent verdict

This artifact records, but does not self-certify, the independent adversarial
security review of the final Lane S source candidate. The reviewed exact branch
tip is `da498ebd980cac87796eceb889c7f1c42cfb952b`. The independent verdict is:

`PASS / SECURITY CLEAR — 0 CRITICAL, 0 HIGH, 0 MED source findings.`

The recorder of this artifact is not the verifier. The verdict came from the
independent security-review lane after its exact-tip re-challenge. This record
exists so the generated provenance successor can bind an immutable artifact and
content digest instead of relying on mutable conversation state.

## 2. Correction and review chain

The accepted tip is the terminal result of the following fail-closed chain:

1. `70417f577bc3d6a02cfc3fb8c6381a9f8fcbcaf9` was rejected after restricted-login
   probes reproduced direct-DML lifecycle bypasses, fabricated/empty generation
   publication, semantic-status false greens, fail-open secret isolation, unsafe
   deployment ordering, and incomplete migration identity attestation.
2. `add01c4edf47100d29f083b1ed802bc08545e74f` was rejected for a non-atomic
   ownership/guard cutover window and residual old-row/shared-table ownership,
   effective IAM, literal-credential, restore-receipt, role-topology, catalog,
   and dispatcher rollback gaps.
3. `26154020cc8002b5f630a8f0b4a51327586d75b1` was rejected for shared MSR/CGM
   producer scoping, contextual literal-secret detection, custom-role parent
   resolution, authenticated validation-instance binding, and authenticated
   GitHub deployment-review binding.
4. The final correction chain through
   `da498ebd980cac87796eceb889c7f1c42cfb952b` closed those source defects. The
   independent exact-tip re-challenge returned the SECURITY CLEAR verdict above.

Prior rejection evidence remains historical and is not rewritten by this
acceptance record.

## 3. Exact integrated equivalence

The Lane S source is integrated at
`d22533825613c3d428bd844a5dfdc2c0c283b088`. All 23 paths changed by Lane S from
the common base `5142109f7f219ea860f859e322646f79d875bee8` have identical Git blob IDs
at the reviewed branch tip and the integrated tip. The canonical ordered
`path + NUL + blob-id + newline` mapping has SHA-256:

`59a1845b74fb0777274f18b876de0ddae3ac873cea95e405f959d1163ad4d876`

This is source-tree equivalence for the reviewed Lane S surface. It is not a
claim that the integrated tip is deployed or that its external cutover
prerequisites exist.

## 4. Accepted source boundary

The review accepts the source design and compatibility implementation for:

- protected L1/L2 generation and history lifecycle enforcement;
- restricted builder, verifier, migrator, owner, and serving-role boundaries;
- exact migration identity, catalog, trigger, function, ACL, membership, and
  semantic-status attestation;
- fail-closed IAM/secret isolation and authenticated GitHub/Cloud SQL cutover
  preflights;
- bounded L1/L2 writer compatibility required to use the protected lifecycle;
- transactionally serialized cutover, restore binding, and rollback controls.

The L1/L2 writer digest movement caused by those reviewed compatibility imports
is therefore an authorized derived/import-closure delta. It is not an
intentional change to the writers' domain behavior, asset identity, layer
membership, or accepted historical receipts.

## 5. External live prerequisites remain separate

SECURITY CLEAR applies to the reviewed source candidate only. Before any live
cutover, the release lane must independently establish all of the following:

- a protected `data-plane-production-cutover` GitHub environment and an
  authenticated independent approval for the exact workflow run;
- the dedicated builder service account and builder-only database secret;
- removal of broad project/folder/organization Secret Manager access and exact
  narrow per-secret/per-runtime bindings;
- the exact build-job identity and secret rebind;
- a fresh backup, isolated restore, authenticated validation-instance receipt,
  exclusive cutover lease, maintenance window, and governed canary;
- exact merged tree, deployed revision, applied migration identities, protected
  production generations, consumer evidence, and acceptance receipts.

These prerequisites were not created or exercised by the source lane and are
not implied by its review verdict.

## 6. Non-claims

This record does not claim a push, pull request, protected merge, deployment,
IAM or secret mutation, role provisioning, migration application, production
build, physical L1/L2/L3 generation, data acceptance, consumer value, or L3
freeze. It does not open L4 or L5. It does not alter any prior provenance pin or
receipt byte; any pin movement must occur only as a separately generated,
versioned successor bound to this immutable record.
