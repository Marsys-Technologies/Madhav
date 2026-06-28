---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_DEEPSEEK_MODEL_MIGRATION
version: 1.0
status: COMPLETE
created: 2026-06-28
author: Cowork (planning) — for execution by Claude Code in Antigravity
classification: CLAUDECODE_BRIEF — DeepSeek model-ID migration (ISSUE-6, time-sensitive)
session_type: implementation — small scoped registry update
deadline: 2026-07-24 15:59 UTC (DeepSeek retires the deepseek-chat/deepseek-reasoner aliases)
parent: RETRIEVAL_AUTONOMOUS_RUN_OUTCOME_v1_0 (ISSUE-6)
hard_constraints:
  - this is a deliberate find-WITH-JUDGMENT, not a naive replace
  - prod-verify after merge (a live DeepSeek call must succeed post-change)
acceptance_criteria: see §3
---

# CLAUDE CODE BRIEF — DEEPSEEK MODEL-ID MIGRATION

> The `deepseek-chat` / `deepseek-reasoner` aliases retire **2026-07-24 15:59 UTC**. After that, calls using
> them break. Migrate to the canonical model ID before then.

## §0 — Verified target (from DeepSeek live docs, 2026-06-28)
Source: https://api-docs.deepseek.com/quick_start/pricing
- **`deepseek-v4-flash` IS the valid current API model ID** (OpenAI-format base `https://api.deepseek.com`).
  It supports BOTH non-thinking and thinking modes (toggle per the Thinking Mode guide), Tool Calls ✓, JSON ✓,
  1M context.
- `deepseek-chat` = deprecating alias → v4-flash **non-thinking** mode.
- `deepseek-reasoner` = deprecating alias → v4-flash **thinking** mode.
- `deepseek-v4-pro` is the higher tier (also valid; already used in routes).

**IMPORTANT — corrects stale code comments:** `registry.ts` currently has comments asserting
"deepseek-v4-flash is not a valid DeepSeek API model ID / API rejects it." Those comments are **WRONG** per
the live docs and must be removed/corrected as part of this change. (Classic code-comment drift — verify, don't
trust the comment.)

## §1 — The migration
In `platform/src/lib/models/registry.ts`:
- Replace `deepseek-chat` usages (the MODEL_INDEX entry, FAMILY_WORKER `deepseek` mapping, and every
  CALL_TYPE_ROUTING primary/fallback that uses it) with **`deepseek-v4-flash`** in **non-thinking** mode.
- Where `deepseek-reasoner` is referenced, map to **`deepseek-v4-flash` thinking mode** (or keep
  `deepseek-v4-pro` if that's the intended thinking tier — preserve the existing thinking-vs-non-thinking intent
  of each route; don't change which routes think).
- Remove/correct the stale "not a valid ID" comments.
- Confirm the thinking-mode toggle mechanism (extra_body / reasoning param per the DeepSeek adapter) is wired
  so v4-flash thinking-mode actually engages where `deepseek-reasoner` used to.

## §2 — Preserve intent, don't change behavior
This is an ID migration, NOT a routing redesign. Each route must keep its current thinking/non-thinking
character and its primary/fallback shape — only the model ID string changes. Don't "improve" the routing here.

## §3 — Acceptance criteria
- Zero `deepseek-chat` / `deepseek-reasoner` references remain in runtime routing (a comment is fine).
- Each migrated route preserves its prior thinking/non-thinking intent + primary/fallback structure.
- Stale "not a valid ID" comments removed/corrected.
- **Prod-verify:** a live DeepSeek call (worker + a thinking route) succeeds against the API post-change.
- Tests green; lands before 2026-07-24.

## §4 — Close
Set `status: COMPLETE` when migrated, prod-verified, and merged. Report back to update the run-outcome record.

*End of CLAUDECODE_BRIEF_RETRIEVAL_DEEPSEEK_MODEL_MIGRATION v1.0.*
