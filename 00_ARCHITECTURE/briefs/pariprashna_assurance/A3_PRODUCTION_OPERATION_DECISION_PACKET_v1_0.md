---
artifact: PARIPRASHNA_ASSURANCE_TRACKER_A3_PRODUCTION_OPERATION_DECISION_PACKET
version: 1.0
status: PENDING_NATIVE_A3
date: 2026-08-24
scope: PARIPRASHNA-ASSURANCE-P0-TRACKER
decision_owner: NATIVE A3 REQUIRED
---

# A3 decision packet — production operation of the assurance tracker

## Decision requested

The CG-0 tracker is locally proven and independently verified. Select a production operating
model before it receives campaign evidence or becomes visible beyond its host. This decision
does not accept CG-0, approve a release, or authorize any campaign progress.

## Current verified boundary

- The tracker is an append-only SQLite/WAL ledger plus deterministic projector and loopback
  JSON/SSE dashboard service.
- It is deliberately bound to loopback and rejects non-local peers. Dashboard reads are only
  unauthenticated because the CG-0 proof is host-local.
- Per-runtime local tokens exist only for proof. They are not a production issuer, identity
  model, or rotation mechanism.
- The proof has 30 automated unit/integration/adversarial checks, a rendered desktop/mobile
  smoke check, replay/hash reconciliation, and an independent verifier PASS.

## Operating-model options

| Option | What it authorizes | Consequence |
| --- | --- | --- |
| A — approved single trusted host | A service identity, approved non-repository runtime directory, host-local backup/restore policy, and an existing approved access boundary | Retains SQLite as one durable host-local control plane; production auth/ingress configuration must be reviewed before any non-loopback exposure |
| B — remain host-local for P1 | An approved local runtime and named operators only; no network exposure | Enables controlled P1 evidence ingestion on one host while deferring shared dashboard access and all network credentials |
| C — shared/high-availability service | A new deployment architecture, persistence/HA design, network auth, monitoring, and cost envelope | Requires a follow-on architecture decision and implementation; it is not covered by the local CG-0 proof |

## Exact native approvals required

1. Choose A, B, or C and name the accountable service owner.
2. Approve the runtime directory, service account/manager, filesystem permissions, and at-rest
   encryption expectation. The runtime must remain outside Git.
3. Decide reader and writer authentication, including the approved identity source, least-
   privilege role mapping, issuance/revocation, rotation owner, and emergency access process.
4. Decide the host exposure boundary: loopback only, existing authenticated private ingress, or
   a separately governed shared-service design. Public exposure is not proposed.
5. Approve backup frequency, retention, encryption, restore owner, and restore-test cadence for
   the immutable event ledger and snapshots.
6. Approve monitoring/incident ownership, including replay-integrity alerts, stale-presence
   alerts, rejected-event review, and service availability escalation.
7. Authorize the governed deployment, production verification, and the later native decision on
   CG-0. A deployment alone is not a gate closure.

## Explicitly not authorized by this packet

- Creating cloud resources, databases, service accounts, credentials, or secrets.
- Changing the current loopback-only guard or exposing the local service.
- Importing historical heartbeat data, manually entering progress, or seeding demonstration
  events into a campaign runtime.
- Marking CG-0, P1, or any later campaign phase complete.

## Safe execution immediately after A3

1. Produce a deployment change scoped to the selected option only.
2. Provision identities through the approved issuer; do not copy local-proof tokens.
3. Start with an empty approved runtime, run replay/integrity verification, and capture the
   backup/restore evidence required by the selected model.
4. Independently verify the deployed access boundary, event authorization, replay recovery,
   dashboard freshness, and failure presentation before accepting production CG-0.
5. Use `P1_ONBOARDING.md` only after those deployment facts are independently evidenced.

## Recommendation

**SURROGATE DECISION — not native acceptance:** Option B is the smallest continuation if the
immediate need is governed P1 takeover on a single trusted host. Option A is appropriate only
when an existing approved authenticated access boundary and an accountable backup/incident
owner are named. Option C should be selected only when shared availability is actually needed;
it is a material architecture expansion.
