---
unit: 4.observability
wave: 4
title: Cloud Trace + Monitoring + SLOs + alerts + batch Vertex embeddings + budget guard
stream: B
worktree: ../MadhavStreamB
blockedBy: [3.cutover]
on_red: rollback
---

## Context (self-contained)
Today only the Observatory cost-reconciliation surface exists; no end-to-end tracing, SLOs, or alerting. With
zero-touch prod, observability IS the safety net (master plan §4.2-9). Also: Vertex embeddings are per-text
REST today — batch them.

## Scope
- **Cloud Trace** across web → sidecar → mcp (instrument the request boundaries; propagate trace headers).
- **Cloud Monitoring** dashboards (latency p50/p95/p99 per route + per pipeline, error rates, cache hit/miss
  from 4.memorystore_caching).
- **SLOs** (request latency, error rate, build success rate) + **alert policies** to a configured channel.
- **Batch Vertex embeddings** — switch `lib/embeddings/embedText.ts` from per-text REST to `instances[]`
  batched calls; confirm `VERTEX_AI_LOCATION` set in `deploy.yml` env_vars (audit §4.1 marked unverified).
- **Budget guard** — Cloud Billing alert tied to the program kill-switch threshold; codify the cost ceiling
  per the §11 native call.

## Acceptance criteria (all automated)
1. A representative request produces a Trace spanning web → sidecar → mcp (visible in Cloud Trace).
2. Dashboards exist (codified as JSON); SLOs configured; one synthetic alert fires end-to-end.
3. Embedding batching: a 50-text call uses 1 Vertex request (not 50); latency + cost reduced (measured).
4. Budget alert fires on a test threshold and writes to gate_status (kill-switch wiring).

## must_not_touch
`chart_facts`/`l25_*`, `platform/src/lib/synthesis/panel/**`, `platform/python-sidecar/natal_engine/**`.

## Commit cadence / rollback
Commits: (1) Trace instrumentation, (2) Monitoring/SLOs/alerts IaC, (3) batch embeddings + Vertex region pin,
(4) budget alert + kill-switch hook. Rollback = revert; observability is additive (no behaviour change in app).
