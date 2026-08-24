---
artifact: ADR_P0_TRACKER_ARCHITECTURE
version: 1.0
status: ACCEPTED_FOR_LOCAL_CG0_PROOF
date: 2026-08-24
decision_owner: SURROGATE DECISION — not native acceptance
scope: PARIPRASHNA-ASSURANCE-P0-TRACKER
---

# ADR — event-sourced Paripraśna assurance control plane

## Decision

CG-0 uses a stdlib Python control-plane service backed by one local SQLite database per
runtime directory. SQLite supplies transactional validation, unique idempotency keys,
optimistic stream sequencing, append-only triggers, durable events, and crash-safe WAL
mode without a new cloud resource, credential, or production database mutation. The
projector is a pure fold of the durable event log. Ephemeral presence lives in a separate
table and is deliberately excluded from the canonical audit hash. A threaded HTTP service
exposes JSON reads, authenticated event writes, and SSE; the responsive dashboard is a
derived client of that API.

This is production-ready for a single trusted deployment host after an approved runtime
directory, service account/token provisioning, and normal deployment review. It is locally
proven for CG-0 only; this ADR does not authorize production deployment.

## Why this architecture

It is the smallest implementation that provides durable append-only history, concurrent
writers, transactionally checked transitions, deterministic rebuild, projector recovery,
and live updates. It directly avoids the prior tracker’s per-writer JSONL race and its
mixed durable-heartbeat history.

## Rejected alternatives

| Alternative | Reason rejected for P0 |
| --- | --- |
| Extend the retired tracker-v2 JSONL daemon | It has no transactional cross-writer validation, no stream authorization, and records liveness in the same audit history. |
| New Cloud SQL/Postgres schema | Technically suitable but requires a production database mutation and deployment authority, both reserved A3 decisions. |
| Git-tracked JSON state | Cannot safely accept concurrent writers or provide a durable low-latency real-time surface. |
| Browser-local state | Not durable, auditable, or shared. |

## Boundaries

Primary evidence remains in GitHub, CI, test artefacts, deployment records, transcripts,
screenshots, and database evidence. Events link to that evidence and never replace it.
The service fails closed: stale, unknown, or integrity-degraded state never renders as
healthy. Production hosting, credentials, and release require native authority.
