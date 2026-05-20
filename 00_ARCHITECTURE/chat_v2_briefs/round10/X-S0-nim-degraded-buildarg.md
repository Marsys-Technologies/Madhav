---
canonical_id: R10_X_S0
version: 1.0
status: CURRENT
session_id: X-S0
title: NIM_STACK_DEGRADED build-arg cleanup
depends_on: []
blocked_on: []
flag: FLAGLESS
flag_default: ~
client_side: "yes — deploy.yml build-arg only, no source edit"
authored: 2026-05-20
amendment_4_entry: true
---

# X-S0 — NIM_STACK_DEGRADED Build-Arg Cleanup

## Context

`NEXT_PUBLIC_NIM_STACK_DEGRADED` is consumed in `platform/src/components/chat-v2/composer/ModelStylePicker.tsx` (line ~51) to show a "Limited" degradation badge. The flag is present in source but **absent from `.github/workflows/deploy.yml` --build-arg block**, meaning the degradation badge can never appear even when an operator sets the Cloud Run runtime env var (client-side flags are baked at Docker build time, not read at runtime per Amendment 1).

This session adds the flag at `=false` to preserve current behavior while making the control actually flippable by operators. It is a **cleanup**, not a new feature.

**Amendment 4 entry.** This session exists solely because of Amendment 4.

## Files in Scope

- `.github/workflows/deploy.yml` — add one `--build-arg NEXT_PUBLIC_NIM_STACK_DEGRADED=false` line

## Files Must NOT Touch

- Any file under `platform/src/`
- Any file under `platform/tests/`
- Any `package.json` or `package-lock.json`
- Any Phase 4C files (`00_ARCHITECTURE/BRIEFS/`, `00_ARCHITECTURE/CONDUCTOR/`, `feature/phase-4c-panchang` paths)

## Acceptance Criteria

1. `.github/workflows/deploy.yml` contains `--build-arg NEXT_PUBLIC_NIM_STACK_DEGRADED=false` in the Docker build step's `--build-arg` block, adjacent to other `NEXT_PUBLIC_*` flags.
2. No other file is modified.
3. `git diff --stat` shows exactly one file changed: `.github/workflows/deploy.yml`.
4. The flag value is `false` (preserves current behavior — degraded badge is off by default).
5. A comment or inline note clarifies this is an orphaned-flag cleanup (optional but recommended).

## Pre-commit Gates

```bash
# Verify only deploy.yml changed
git diff --stat HEAD | grep -v 'deploy.yml' | grep '|' && echo "FAIL: unexpected files changed" || echo "PASS: only deploy.yml"

# Verify the flag is present
grep "NEXT_PUBLIC_NIM_STACK_DEGRADED" .github/workflows/deploy.yml && echo "PASS: flag found" || echo "FAIL: flag missing"
```

## Commit Template

```
fix(deploy): add NEXT_PUBLIC_NIM_STACK_DEGRADED=false build-arg (Amendment 4 cleanup)

Orphaned client-side flag at ModelStylePicker.tsx:51 was absent from
deploy.yml --build-arg block. Adds it at =false to preserve current
behavior while making the degradation badge actually operator-flippable.
No source edits — deploy.yml only.
```

## Decision Log

*(Executor: record any decisions or deviations here at close.)*
