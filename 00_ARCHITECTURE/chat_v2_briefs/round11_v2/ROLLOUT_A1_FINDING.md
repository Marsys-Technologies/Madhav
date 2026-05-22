---
artifact: ROLLOUT_A1_FINDING.md
authored: 2026-05-22
phase: A.1
verdict: A.1.a-variant (build-arg present but ineffective)
---

# Phase A.1 — deploy.yml build-arg check

`NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL` IS present in `.github/workflows/deploy.yml` line 80 as a Docker build-arg — technically A.1.a.

However, `platform/Dockerfile` has no corresponding `ARG NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL` / `ENV NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL=...` pair. Without the Dockerfile ARG, the build-arg is silently ignored during `docker build` (Docker discards undeclared build-args). The flag value is therefore always `undefined` in the Next.js build, and `ConsumeChatV2.tsx:110` reads it directly via `process.env.NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL === 'true'`.

Additionally, the value is hardcoded to `false` rather than using a GitHub Actions variable reference, so `gh variable set` alone would have no effect even after fixing the Dockerfile.

**Action taken:** Proceeding with A.2-style fix — add Dockerfile ARG/ENV pair and convert deploy.yml build-arg to use `${{ vars.NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL || 'false' }}`.
