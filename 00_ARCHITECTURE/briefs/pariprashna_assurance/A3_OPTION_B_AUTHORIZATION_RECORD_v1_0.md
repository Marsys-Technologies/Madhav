---
artifact: PARIPRASHNA_ASSURANCE_A3_OPTION_B_AUTHORIZATION_RECORD
version: 1.0
status: NATIVE_AUTHORIZED_PENDING_DEPLOYED_CG0_EVIDENCE
date: 2026-08-25
scope: PARIPRASHNA-ASSURANCE-P0B-OPTION-B
decision_owner: NATIVE
---

# A3 Option-B authorization record

## Authorized operating boundary

The tracker may operate only on the current trusted Mac host under local account `Dev`, bound
only to `127.0.0.1:8787`. The approved runtime is
`/Users/Dev/.pariprashna-assurance-control`; FileVault must be confirmed on; the runtime is
owned by `Dev` at mode `0700`; and database, credential, snapshot, backup, and sensitive-log
files are mode `0600`. No network exposure, cloud resource, historical-state import, or demo
credential reuse is authorized.

The approved current-user service is `com.marsys.pariprashna-assurance-control`. It must be
installed only from an attested, immutable merged release and must never replace an existing
listener or launchd job.

## Accountable P0B roles

| Authority | Approved identity |
| --- | --- |
| Accountable service owner and launchd manager | local macOS account `Dev` |
| Operational lead | `lead-p0b` |
| Native surrogate | `surrogate-p0b` |
| Independent verifier | `verifier-p0b` |
| Integrator | `integrator-p0b` |

Role tokens are issued separately under the accountable owner. The surrogate owns rotation and
revocation; emergency access requires a native-approved reason, immediate rotation, and
independent review. Token values are never recorded in this artifact.

## Recovery and monitoring

Create encrypted local snapshots before and after each material operational change and daily
while active; retain routine backups for 30 days. `lead-p0b` owns restores, which must use a
separate empty recovery runtime; `verifier-p0b` independently verifies restore tests before
CG-0 and weekly during active operation.

`integrator-p0b` owns replay/hash monitoring, `surrogate-p0b` owns rejected-event review, and
`lead-p0b` owns stale-presence and availability monitoring. Integrity, credential, exposure,
backup, rejected-event, or ownership anomalies are escalated to the native service owner and
block the gate until independently resolved.

## Explicit non-authorizations

This record does not start P1, resume the historical self-paused assurance campaign, create a
network-facing service, import synthetic or historical events, or itself close CG-0. CG-0 needs
independent deployed-runtime verification followed by an evidence-bearing integrator decision.
