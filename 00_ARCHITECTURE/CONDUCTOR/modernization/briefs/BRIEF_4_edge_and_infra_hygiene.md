---
unit: 4.edge_and_infra_hygiene
wave: 4
title: Edge (CDN + Armor) + IAM on MCP + per-service SAs + Scheduler IaC + deploy consolidation + secret/registry hygiene
stream: A
worktree: ../MadhavStreamA
blockedBy: [3.cutover, 4.refactor_pipeline_shim]
on_red: halt_queue   # security + edge changes — surface on failure
---

## Context (self-contained)
Bundles several GCP-native hardening items from master plan §4.2 that share an infra surface:
- **Edge:** external HTTPS LB + Cloud CDN for `_next/static` + chart-document reads + Cloud Armor (WAF/rate-limit).
- **MCP exposure:** `amjis-mcp` is currently `--allow-unauthenticated` (audit §4.1) → put behind IAM (or a
  shared token + LB rule).
- **Least-privilege SAs:** split per-service runtime SAs (web / sidecar / mcp / builder); scoped IAM grants.
- **Scheduler as IaC:** codify MV-refresh + pending-stream-reaper as Cloud Scheduler jobs (today comment-only).
- **Deploy-path consolidation:** GH Actions WIF is the sole authoritative deploy path; delete the parallel
  Cloud Build configs/triggers (audit R11).
- **Secret + registry hygiene:** normalize Secret Manager names; pin/rotate versions (no `:latest`); migrate
  the MCP image off legacy `gcr.io` → Artifact Registry; add image cleanup policies.

## Acceptance criteria (all automated)
1. amjis-mcp is NOT publicly accessible (curl-from-internet returns auth required); IAM-gated.
2. CDN serves `_next/static` from the LB (cache-hit headers visible).
3. Cloud Armor rules active (WAF + a basic rate-limit) — verified via a synthetic policy test.
4. Each Cloud Run service runs under its own least-priv SA (grep current SA != github-actions for runtime).
5. Cloud Scheduler jobs (MV-refresh + reaper) exist as IaC + run on cadence.
6. Cloud Build triggers removed; deploy.yml is the only path that mutates Cloud Run; MCP image at AR.

## must_not_touch
`chart_facts`/`l25_*`, `platform/python-sidecar/**`, `platform/src/lib/synthesis/panel/**`.

## Commit cadence / rollback
Commits: (1) LB + CDN + Armor, (2) IAM on MCP + per-service SAs, (3) Scheduler IaC + deploy consolidation +
secret/registry normalization. Each prod step gets pre-flight + post-deploy smoke + auto-rollback. Rollback =
revert the specific commit; the prior deploy is the safe fallback.
