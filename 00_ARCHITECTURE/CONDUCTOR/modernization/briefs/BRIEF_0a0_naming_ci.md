---
status: COMPLETE
unit: 0a.0
wave: 0a
title: Naming-governance CI gate (establish FIRST — it enforces all later renames)
stream: A
worktree: ../MadhavStreamA
blockedBy: []
sets_gate: naming_ci
on_red: rollback
---

## Context (self-contained)
The platform's naming is fragmented (MASTER_PLAN §3, audit §8). Before any rename lands, build the CI gate
that ENFORCES the canonical taxonomy so drift can't re-accrete. Per the audit, only the *currently-enforceable*
rules go in now; tenant-key + tool-name-in-contract rules are deferred to their waves (contract doesn't exist yet).

## Scope
Create `platform/scripts/governance/naming_lint.py` (and wire it into `.github/workflows/ci.yml`) that FAILS on:
- a Google env prefix outside `GOOGLE_CLOUD_*` (flag `GCP_*` / bare `GOOGLE_*` resource vars);
- a feature flag not matching `MARSYS_FLAG_<DOMAIN>_<FEATURE>` (+ `_ENABLED` for booleans);
- a new route under both `/api/panchang` and `/api/panchanga` (duplicate trees);
- a Cloud Run service/image prefix other than `amjis-` (flags `marsys-pipeline`).
Provide `--self-test` (runs on fixtures, no repo scan) and a normal full-scan mode. Rules are data-driven
(a `naming_rules.yaml`) so later waves can add tenant-key + tool-name rules without code change.

## Acceptance criteria (all automated)
1. `python platform/scripts/governance/naming_lint.py --self-test` exits 0.
2. The gate is wired into `ci.yml` and fails the build on a seeded violation fixture.
3. Running it on the current repo lists today's known violations WITHOUT failing the program (report mode for
   pre-existing; fail mode for NEW). Capture the baseline violation list to `naming_baseline.json`.

## must_not_touch
`platform/src/app/**`, `platform-mcp/src/**` (this unit only adds the gate; it does not perform renames).

## Commit cadence / rollback
One commit: "0a.0 naming-governance CI gate + baseline". Cleanly cherry-pickable (only governance/CI paths).
Rollback = revert the commit; no data/infra effect.
