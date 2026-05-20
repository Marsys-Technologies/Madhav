---
artifact_id: CLOSEOUT_COMPLETE
version: 1.0
status: SEALED
created: 2026-05-20
sealed_by: R7-R10 close-out executor session
---

# Chat V2 R7–R10 Arc — Close-Out Complete

All seven phases of the R7-R10 close-out executor plan are complete as of 2026-05-20.

## Phase 0 — Orient + R10 merge

| Item | Result |
|------|--------|
| Phase 4C PR #105 | Merged to main (SHA `3b3405c`) — merge conflict resolved (9 files) |
| R10 PR #106 | Merged to main (SHA `4dae9ed`) |
| Merge blocker artifact | `PHASE_4C_BLOCKS_R10.md` (audit trail; retained at project root) |
| Native option selected | Option A: Land Phase 4C first, then R10 |

## Phase 1 — NEXT_PUBLIC build-arg audit

| Var | Classification | Action |
|-----|---------------|--------|
| `NEXT_PUBLIC_APP_URL` | Infra var (panchang iCal builder) | Added to deploy.yml `=https://amjis-web.run.app` |
| `NEXT_PUBLIC_DATABASE_URL` | Seed-script only (`run_seed.ts`) — never in browser bundle | NOT added (correct) |
| All 17 feature flag NEXT_PUBLIC vars | Feature flags | Verified present in deploy.yml |

## Phase 2 — R9-S2 historical embedding backfill

| Item | Result |
|------|--------|
| Script path | `platform/scripts/backfill_conversation_embeddings.ts` |
| Status | AUTHORED — not yet run against production |
| Prerequisites | Cloud SQL proxy on 5432, ADC auth (`gcloud auth application-default login`), GCP_PROJECT + VERTEX_AI_LOCATION env vars |
| Safety | Idempotent (`ON CONFLICT DO NOTHING`); safe to re-run if interrupted |
| Note | Run instructions in script header. DO NOT run more than once concurrently. |

**Operator action required:** Run the backfill script when Cloud SQL proxy is available.

## Phase 3 — Pre-existing test failure baseline

| Item | Result |
|------|--------|
| Baseline artifact | `KNOWN_PRE_EXISTING_FAILURES.md` v1.1 |
| R10 unit test suite | **566 passed / 0 failed** (55 files in `tests/unit/chat-v2/`) |
| Pre-existing failures | 16 test cases across 9 files (all unrelated to R7-R10) |
| R7-R10 regression count | 0 |

## Phase 4 — NIM_STACK_DEGRADED cleanup (X-S0)

`NEXT_PUBLIC_NIM_STACK_DEGRADED=false` was pre-applied in R10 governance setup PR.
No additional action required. AC verified via `grep`.

## Phase 5 — R10 session queue bookkeeping

Y-S5 (`EDIT_WHILE_STREAMING`) and Y-S9 (`AUTO_RETRY`) marked `completed` in
`session_queue.yaml`. All 21 R10 sessions now show `status: completed`.

## Phase 6 — Governance institutionalization

| Item | Result |
|------|--------|
| `CLAUDE.md` | Bumped to v3.1; R10 marked COMPLETE; Phase 4C PR #105 merged noted |
| `KNOWN_PRE_EXISTING_FAILURES.md` | v1.1 baseline (delta from v1.0 documented) |
| `session_queue.yaml` | All sessions completed |
| Worktree cleanup | MadhavR10 worktree branch (`chat-v2/round10`) deleted by PR #106 merge |

## Phase 7 — Seal

This file seals the R7-R10 arc close-out. The close-out PR (`chat-v2/r7-r10-closeout`)
lands this artifact plus all Phase 1-6 changes.

## Outstanding operator items (not blocking close-out)

1. **Embedding backfill** — run `platform/scripts/backfill_conversation_embeddings.ts`
   via Cloud SQL proxy to populate historical conversation embeddings.
2. **Pre-existing test failures** — 9 stale test files; fix in dedicated follow-up sessions
   (disposition per `KNOWN_PRE_EXISTING_FAILURES.md`).
3. **Phase 4C Wave 2** — `feature/phase-4c-panchang` Wave 2 scope (4B sunrise derivation,
   4D follow-up) pending separate planning session.

---

*Sealed 2026-05-20. R7 (PR #101) · R8 (PR #102) · R9 (PR #100) · Phase 4C (PR #105) · R10 (PR #106) — all merged to main.*
