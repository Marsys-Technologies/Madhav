---
canonical_id: CLAUDECODE_BRIEF_MAPS_KEY_DOCKERFILE_FIX
version: 1.0
status: ACTIVE
authored: 2026-06-07
author: Cowork (planning)
executor: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: Fix — prod Google Maps key never bakes into the bundle
---

# CLAUDECODE_BRIEF — Maps key not baking into prod build (root cause: missing Dockerfile ARG)

## §1 — Root cause (Cowork-confirmed by reading the files)

The native set the `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` GitHub secret multiple times and it
"never resolves" on prod. The cause is NOT the secret and NOT build caching:

- `.github/workflows/deploy.yml` line 164 (the real `deploy-web` job) correctly passes
  `--build-arg NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=${{ secrets.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY }}`.
  (Line 65 is the throwaway `build-check` CI job, push:false — its empty value is harmless.)
- BUT `platform/Dockerfile` declares an `ARG` + `ENV` pair for EVERY other `NEXT_PUBLIC_*`
  var (Firebase keys, R9/R10/R11 flags, APP_URL, NIM_STACK_DEGRADED) — and has **NO
  `ARG NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` / `ENV` line at all.**
- Docker silently ignores a `--build-arg` with no matching `ARG` declaration. So the key
  value is received by the build step but never enters the build environment → Next.js
  bakes it as undefined/empty → `isGoogleMapsKeyConfigured()` is false on prod → no
  Places autocomplete. This happens on every deploy regardless of the secret. This is the
  whole bug.

## §2 — The fix (Dockerfile, 2 lines)

In `platform/Dockerfile`, in the builder stage where the other `NEXT_PUBLIC_*` ARG/ENV
pairs live (around lines 18–64, alongside e.g. `NEXT_PUBLIC_NIM_STACK_DEGRADED` at 63–64),
add the missing pair:

```dockerfile
ARG NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
ENV NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=$NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
```

Place it in the SAME build stage that runs `next build` (the stage that already has the
other NEXT_PUBLIC ENV lines — confirm it's the builder, not the runtime stage). Match the
exact pattern of the surrounding lines.

## §3 — Optional consistency cleanup (low priority, native's call)

`deploy.yml` line 65 (build-check job) bakes `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=` empty.
That's fine for a push:false CI build, but for consistency you MAY set it to a
`ci-placeholder` like the Firebase keys on lines 57–62. Not required for the fix.

## §4 — Verification (REQUIRED before calling done)

1. `docker build` the platform image locally OR via the deploy job, passing
   `--build-arg NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=test123`, then grep the built bundle for
   the value to prove it bakes in:
   ```
   # after build, in the builder stage / .next output:
   grep -r "test123" platform/.next/ | head    # should find it inlined in client JS
   ```
   (Or build the image and `docker run ... sh -c 'grep -rl test123 /app/.next/static'`.)
   If grep finds the test value inlined, the ARG fix works.
2. Do NOT commit a real key anywhere — use a throwaway test value for the grep proof, then
   rely on the GitHub secret for the real deploy.

## §5 — Ship

```
git checkout -b fix/maps-key-dockerfile-arg
# edit platform/Dockerfile (add the ARG+ENV pair)
git add platform/Dockerfile
git commit -m "fix(docker): declare ARG/ENV NEXT_PUBLIC_GOOGLE_MAPS_API_KEY so the build-arg actually bakes into the bundle (prod Places autocomplete was silently keyless)"
git push origin fix/maps-key-dockerfile-arg
# merge to main (repo bypasses status checks), then the native triggers a fresh deploy-web
```

## §6 — Native actions (after merge)
- Confirm the GitHub secret `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` exists (Secrets tab, exact
  name) — it's referenced by deploy.yml line 164.
- Trigger a fresh `deploy-web` run (workflow_dispatch / Run workflow, or push to main).
- After deploy, Cowork verifies on madhav.marsys.in/clients/new that the Maps SDK loads
  with a real key and Places autocomplete works (window.google present, GetPlace 200).

## §7 — Why this was invisible
Localhost works because `next dev` reads `NEXT_PUBLIC_*` straight from `platform/.env` —
no Docker, no ARG needed. The bug only exists in the Dockerized prod build, which is why
every localhost test passed while prod stayed keyless. Lesson for memory: when a
`NEXT_PUBLIC_*` works on localhost but not prod, check the Dockerfile has the matching
`ARG`+`ENV`, not just the deploy.yml `--build-arg`.
