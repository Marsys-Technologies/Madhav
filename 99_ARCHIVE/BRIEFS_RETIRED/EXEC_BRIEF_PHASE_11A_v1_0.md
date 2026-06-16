---
brief_id: EXEC_BRIEF_PHASE_11A
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PHASE_11A_v1_0.md and execute it."
phase: 11A
phase_name: Pipeline Cutover — Stage 1 (Flag Flip Only, No Code Deletion)
risk_classification: MEDIUM
parallelizable_with: []
depends_on: [Phases 0-9 + hotfix all COMPLETE]
estimated_streams: 3
---

# EXEC_BRIEF — Phase 11A — Pipeline Cutover Stage 1 (Flag Flip)

## Mission

Make the new pipeline the **default behavior** for the Consume tab without deleting the legacy code path. After this stage, `NEW_QUERY_PIPELINE_ENABLED` and `AUDIT_ENABLED` default `true` instead of `false`. The legacy code path is still in the codebase but is now the explicit-opt-out branch (`NEW_QUERY_PIPELINE_ENABLED=false`), reversing the polarity.

This stage exists to give the native a **revertible cutover** — if the new pipeline misbehaves under real production traffic, flipping the flag back to `false` restores legacy behavior immediately. Once Stage 1 has been live for some observation window and the native is satisfied, Phase 11B deletes the legacy code permanently.

## Scope (`may_touch` / `must_not_touch`)

**`may_touch`:**
- `platform/src/lib/config/feature_flags.ts` — change `NEW_QUERY_PIPELINE_ENABLED` and `AUDIT_ENABLED` defaults
- `.env.example` — update documented defaults so new clones pick up the new behavior
- `platform/src/lib/config/__tests__/feature_flags.test.ts` — update default-value assertions
- `platform/scripts/cutover/stage1_smoke.ts` (new) — single end-to-end smoke script

**`must_not_touch`:**
- Any code path implementing the new pipeline (`lib/synthesis/**`, `lib/validators/**`, `lib/audit/**`, etc. — all frozen)
- Any flag-OFF code branch (consume-tools.ts, route.ts legacy branch, etc. — Phase 11B's territory)
- All other feature flags (checkpoint flags + panel flags stay default `false` — operational gradient preserved)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`
- `platform/python-sidecar/**`

## Sub-streams (3 total)

### Stream A — Flip the two master defaults

- In `platform/src/lib/config/feature_flags.ts`:
  - `NEW_QUERY_PIPELINE_ENABLED`: default `false` → `true`
  - `AUDIT_ENABLED`: default `false` → `true`
- All other flags stay at their current defaults (`VALIDATOR_FAILURE_HALT=true`, all checkpoint + panel flags `false`).
- Update `.env.example` to reflect new defaults so a fresh clone gets the new pipeline by default.
- Update the test file to assert new defaults.
- 4+ tests: defaults are correct; explicit env-var override still works (flipping `NEW_QUERY_PIPELINE_ENABLED=false` in env still routes to legacy).

### Stream B — End-to-end smoke script

- New file `platform/scripts/cutover/stage1_smoke.ts`. Usage: `npm run cutover:stage1-smoke`.
- Steps:
  1. Verify environment: `NEW_QUERY_PIPELINE_ENABLED=true`, `AUDIT_ENABLED=true`, ANTHROPIC + OPENAI + GOOGLE keys present, Cloud SQL Auth Proxy running OR running against staging Cloud SQL directly.
  2. Submit one representative query for each of the 8 classes through the live HTTP endpoint `/api/chat/consume`. Use queries from `verification_artifacts/RAG/synthesis_golden_v1_0.json` (the 10 hand-labeled M2/B.5 queries) plus 2 supplementary queries to fill out class coverage.
  3. For each query, assert: HTTP 200, response stream completes, response contains at least one `[signal:...]` or `[asset:...]` or `[chunk:...]` citation marker, response contains a disclosure tier indicator.
  4. After all 8 queries, query `audit_log` directly: `SELECT count(*) FROM audit_log WHERE created_at >= <smoke_start_time>`. Assert count ≥ 8.
  5. For 2 representative rows, fetch via `GET /api/audit/[query_id]` and verify the response payload renders the 8 detail sections (header/bundle/tools/validators/[no checkpoints]/[no panel]/final/raw).
  6. Print a green ✅ summary or red ✗ failure list.
- The script must be idempotent — running it twice should produce 16 rows in audit_log, not corrupt anything.
- Failure mode: if any of the 8 classes returns a 5xx, parse error, or empty response, the script exits with code 1 and prints which class failed. **Native uses this as the gate before triggering Phase 11B.**

### Stream C — Documentation + close

- Append a short note to `00_ARCHITECTURE/SESSION_LOG.md` describing the Stage 1 cutover, with timestamp.
- Update `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` to note that the new pipeline is now default-on, awaiting Stage 2 (Phase 11B) for legacy code deletion.
- Add a CLAUDE.md note (item 12 or appended to §F) reminding future sessions that the new pipeline is now default behavior; legacy is opt-out via env override.
- Verify lint + type-check + full test suite all green (existing tests should still pass since the only change is flag defaults).

## Critical constraints

- **No code deletion.** Phase 11A is purely a default-value flip + a smoke script. The legacy code path stays in the codebase; it just isn't reached by default anymore.
- **Reversibility.** Setting `NEW_QUERY_PIPELINE_ENABLED=false` in env continues to route to legacy. Tests must verify this still works.
- **Stage 1 is a gate for Stage 2.** Phase 11B's brief explicitly gates code deletion on Phase 11A's `cutover:stage1-smoke` passing.
- **Real LLM calls in the smoke script.** This is the first time the new pipeline runs end-to-end with real provider APIs. Budget: ~8 queries × 4 model calls per query (router + synth + maybe checkpoints if any flipped) = ~32 calls. Cost is small; latency may be 30-90s for the full script.
- **Cloud SQL access required.** The smoke script writes audit rows. If the executor doesn't have Cloud SQL Auth Proxy running locally, the script must abort with a clear error message ("start the Auth Proxy and re-run").
- **Other feature flags stay defaulted off.** Checkpoints + panel mode are NOT enabled by Phase 11A. Those are separate operational decisions for the native to make individually after Stage 1 stabilizes.

## Done criteria

1. `feature_flags.ts` defaults updated; tests updated; lint + type-check clean.
2. `cutover:stage1-smoke` script runs and prints green ✅ for all 8 query classes.
3. `audit_log` shows ≥ 8 fresh rows post-smoke.
4. `/audit` route renders the smoke-test rows correctly.
5. Existing flag-OFF code path is reachable via explicit env override (verified by test).
6. SESSION_LOG.md and CURRENT_STATE_v1_0.md updated.
7. Native acceptance — native runs the smoke script themselves, sees the green ✅, and decides whether to trigger Phase 11B.

## Risk classification: MEDIUM

The defaults flip is small, but it is the first time the new pipeline becomes default behavior, and the smoke script is the first end-to-end live exercise. Mitigations:
- Reversible via env-var override (no code path deleted)
- Smoke script gates Stage 2 (no legacy deletion until Stage 1 proves the new path works)
- All other operational flags stay defaulted off (gradient preserved)
- 1,100+ existing unit/integration tests provide a strong floor

## How native triggers

In a Claude Code session in Anti-Gravity (Sonnet 4.6 in VS Code extension):

> Read EXEC_BRIEF_PHASE_11A_v1_0.md and execute it.

After Sonnet completes, native runs `npm run cutover:stage1-smoke` themselves with Cloud SQL Auth Proxy running, observes the output, and either (a) accepts the cutover and triggers Phase 11B for code deletion, or (b) rolls back by setting `NEW_QUERY_PIPELINE_ENABLED=false` in production env and investigates whatever the smoke surfaced.

## Status updates

- AUTHORED 2026-04-28
- IN_PROGRESS_STREAM_X — set when Sonnet picks up the brief
- COMPLETE — set when all 7 done-criteria pass and native accepts
