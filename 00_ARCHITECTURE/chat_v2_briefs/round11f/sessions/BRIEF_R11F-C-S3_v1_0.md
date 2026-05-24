---
artifact: BRIEF_R11F-C-S3_v1_0.md
session_id: R11F-C-S3
version: 1.0
phase: C
parallel_safety: false
depends_on: [R11F-C-S2]
estimated_loc_delta: +15
---

# R11F-C-S3 — deploy.yml Flag Flips (R11E Loop Flags)

## Scope

Add all R11E loop flags to `deploy.yml`. This is a commit-only session — production
flag activation happens after PR merge via the gcloud commands documented in C-S4.

Per §6 of the master plan: NVIDIA flag is only added if B-S5 confirmed model supports
function calling (Case A). If Case B (N/A), NVIDIA is skipped.

## Precondition

IS.8(b) red-team from C-S2 must have returned PASS before this session proceeds.

## Files May Touch

```
platform/deploy.yml
```

## Files Must NOT Touch

Everything else.

## Implementation

Locate the `env_vars` block in `platform/deploy.yml`. Append the following flags (adjust
based on B-S5 NVIDIA outcome):

```yaml
# R11.F — Agentic Loop Activation (added arc R11F-C-S3, 2026-05-23+)
MARSYS_FLAG_R11E_ANTHROPIC_LOOP: "true"
MARSYS_FLAG_R11E_GEMINI_LOOP: "true"
MARSYS_FLAG_R11E_OPENAI_LOOP: "true"
MARSYS_FLAG_R11E_DEEPSEEK_LOOP: "true"
# MARSYS_FLAG_R11E_NVIDIA_LOOP: "true"  # Uncomment if B-S5 Case A; leave commented if N/A
```

Also verify: `MARSYS_FLAG_R11D_GEMINI_CACHE` should already be in deploy.yml from the
precursor arc's S7. If not, add it here:
```yaml
MARSYS_FLAG_R11D_GEMINI_CACHE: "true"
```

## Acceptance Tests

```bash
# AC.f: loop flags in deploy.yml
grep -c "R11E_ANTHROPIC_LOOP\|R11E_GEMINI_LOOP\|R11E_OPENAI_LOOP\|R11E_DEEPSEEK_LOOP" platform/deploy.yml
# expected: 4 (or 5 if NVIDIA Case A)

# Verify no vitest regression from deploy.yml change (no tests depend on it)
cd platform && npx vitest run --no-coverage 2>&1 | tail -5
# expected: no failures
```

## Deliverable Artifacts

- Patched `platform/deploy.yml`
- Commit: `chore(r11f-c-s3): deploy.yml — add R11E loop flags for all providers`

## Rollback Steps

```bash
git revert HEAD  # removes deploy.yml flag lines
# Production flags remain at current state (off) until PR merges
```

## Note on Production Activation

These flags take effect at the NEXT Cloud Run deployment after the PR merges. The operator
will confirm activation via `gcloud run services describe amjis-web --region asia-south1`
and check the `--env-vars` list. No manual `gcloud run services update` is needed
if Cloud Build picks up the deploy.yml changes on merge.
