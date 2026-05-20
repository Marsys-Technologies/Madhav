# Chat V2 Round 10 — Sessions Log

Branch: chat-v2/round10 | Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR10
Stream type: sequential single-stream (21 sessions)
Log started: 2026-05-20

---

## X-S0 — NIM_STACK_DEGRADED Build-Arg Cleanup

**Status:** COMPLETED  
**Commit:** 2efce23  
**Completed:** 2026-05-20T08:00:00Z

Added `NEXT_PUBLIC_NIM_STACK_DEGRADED=false` to the `--build-arg` block in `.github/workflows/deploy.yml`. The client-side flag at `platform/src/components/chat/ModelStylePicker.tsx:51` was absent from deploy.yml, meaning the NIM degradation badge was unreachable by operators (client-side flags are baked at Docker build time). Added at `=false` to preserve current off-by-default behavior while making it operator-flippable. Single file changed: `.github/workflows/deploy.yml`. Acceptance check PASS. Amendment 4 satisfied.

**Amendments:** A3 (FLAGLESS — deploy.yml cleanup only) | A4 (NIM_STACK_DEGRADED entry — this IS the fix)

---
