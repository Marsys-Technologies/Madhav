---
status: COMPLETE
unit: hygiene.flag_cleanup
wave: 3-hygiene
title: Remove the orphaned LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED flag
stream: B
worktree: ../MadhavStreamB
blockedBy: [3.dejudge]
on_red: rollback
---

## Context (self-contained)
3.dejudge removed the `PANCHA_MP_CLIQUE` query-time consolidation. Its feature flag
`LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED` is now dead (no code reads it) — an orphaned flag (the exact class
the naming-CI + NIM_STACK_DEGRADED orphaned-flag rule targets).

## Scope
- Remove `LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED` from `feature_flags.ts`, `deploy.yml` (and any
  `--build-arg` / Cloud Run env-var reference), and any remaining check site.
- Pair with `gcloud run services update --remove-env-vars` guidance in the operator note (deploy-cloudrun env
  merge lesson) — but the flag flip itself is code-only here.

## Acceptance criteria (all automated)
1. `grep -rn "LL3_PANCHA_MP_CLUSTER_MODIFIER" platform deploy.yml .github` returns none.
2. `naming_lint` + `drift_detector` green; build passes; no behaviour change (the flag was already dead).

## must_not_touch
`platform/src/lib/retrieve/**` (de-judge owns), `chart_facts`/`l25_*`, `platform/python-sidecar/**`.

## Commit cadence / rollback
One commit. Operator follow-up (deferred): `gcloud run services update amjis-web --remove-env-vars MARSYS_FLAG_LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED` if it was set as a Cloud Run env-var. Rollback = revert.
