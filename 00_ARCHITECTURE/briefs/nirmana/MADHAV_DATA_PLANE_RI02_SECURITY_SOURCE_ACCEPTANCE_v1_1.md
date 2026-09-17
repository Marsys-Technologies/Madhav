---
artifact: MADHAV_DATA_PLANE_RI02_SECURITY_SOURCE_ACCEPTANCE
version: "1.1"
status: SECURITY_CLEAR_SOURCE_ACCEPTED
recorded_at: 2026-09-17T22:00:00Z
authority: DP-SD-018 and RI02-R-002/RI02-R-003
reviewed_branch_tip: ea9b27bfeba607c5332c51e10b037e100e97b717
integrated_equivalent_tip: ea9b27bfeba607c5332c51e10b037e100e97b717
supersedes: MADHAV_DATA_PLANE_RI02_SECURITY_SOURCE_ACCEPTANCE_v1_0.md
verdict: PASS_SECURITY_CLEAR
recorder_role: evidence_recorder_not_verifier
---

# MADHAV Data Plane RI-02 Security Source Acceptance v1.1

## 1. Recorded independent verdict

This versioned successor records, but does not self-certify, the independent
security and correctness review of protected-main commit
`ea9b27bfeba607c5332c51e10b037e100e97b717`. The independent exact-tip verdict
is:

`APPROVE / SECURITY CLEAR — 0 blocking source findings.`

The review re-checked the direct production ownership and migrator paths. It
confirmed that both are constrained to `127.0.0.1:5432/amjis`, reject query
routing overrides and the wrong role, and carry a sanitized `PoolConfig` into
ownership preflight, migration attestation, and terminal semantic status
verification. It also confirmed targeted security-contract coverage (46/46),
TypeScript `tsc --noEmit`, `git diff --check`, and direct descent from
`7982524fde1b210dea72eb38e1704aa2b0514eb2`.

The recorder is not the verifier. This record exists to preserve the review's
immutable source boundary rather than relying on mutable conversation state.

## 2. Exact integrated surface

The reviewed and integrated tip are the protected-main commit
`ea9b27bfeba607c5332c51e10b037e100e97b717`, directly descending from
`7982524fde1b210dea72eb38e1704aa2b0514eb2`. Its complete reviewed surface is:

- `platform/scripts/data-plane-migration-attestation.ts` —
  `ae225a2d5c3ac1eb03938c8338191e21a8a56fd7`
- `platform/scripts/data-plane-ownership-preflight.ts` —
  `3fc5f7d7f296fd6c79c0e8650154fa51df66b342`
- `platform/scripts/data-plane-protected-cutover.ts` —
  `bad228594eb620d68e6ddbd79267af94499315f0`
- `platform/tests/unit/data_plane_security_contract.test.ts` —
  `f3ea6d49d191dad280390edd6aed76391a37a64f`

The ordered `path + NUL + blob-id + newline` mapping has SHA-256:

`89fdc9c7ef43031faffcf7e9d633114bed4892e7b401703d7d9bb951bcb2dde1`

This acceptance is strictly an exact source-tree claim. It supersedes neither
the original RI-02 acceptance boundary nor any layer generation receipt.

## 3. Accepted source boundary

The reviewed successor accepts only the routing-equivalence repair required
after the original v1.0 record:

- ownership administrator authentication is reconstructed exclusively against
  the authenticated local production proxy;
- protected migration and its semantic terminal read use the same locally
  pinned production route and the `data_plane_migrator` identity;
- hostile host, port, database, query-override, wrong-role, and credential-swap
  paths fail closed before the cutover lease is entered;
- helper support for explicit `PoolConfig` preserves that route through every
  governed privileged consumer.

No writer, asset identity, layer membership, domain computation, receipt
membership, schema migration text, consumer behavior, or historical accepted
record is changed by this source acceptance.

## 4. External live prerequisites remain separate

This record does not provision or validate any secret. A protected live cutover
still requires the correctly provisioned, direct `postgres` ownership
credential; fresh backup/restore and authorization receipts; the exclusive
lease and quiescence proof; and post-cutover deployment, consumer, recovery,
and product-acceptance evidence.

## 5. Non-claims

This record does not claim a deployment, IAM or secret mutation, production
ownership mutation, migration application, build, live traffic verification,
catalogue completion, recovery proof, or product acceptance. It does not alter
the prior v1.0 provenance pin. The successor binding is generated separately
and must reproduce this immutable source surface.
