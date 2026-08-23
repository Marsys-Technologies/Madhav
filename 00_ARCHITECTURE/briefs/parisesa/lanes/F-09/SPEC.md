---
finding: F-09
stream: S1 DVARA (spec) → S2 MĀTRĀ (build, per conductor routing 2026-08-16)
class: CL-11-adjacent (generic, schema-unaware recover_via.hint text)
stage: S COMPLETE — awaiting VERIFIER REVIEW, then routes to S2's hot-file builder to apply
build_note: S1 does not touch platform-mcp/src/lib/response_budget.ts directly (S2 HOT,
  single-builder-all-day). This spec was written by reading the file (read-only) to make
  the diff exact and apply-ready for S2's builder, per conductor's routing decision — same
  pattern as F-38's route-middleware handoff, applied to a different stream's lease.
---

## 1. Root cause (one sentence, mechanism-level)

`autoDetectTrimmableSections` (`platform-mcp/src/lib/response_budget.ts:508-530`) is a generic,
tool-schema-unaware fallback trimmer for "thin proxy" tools whose pagination contract this helper
doesn't own (per its own doc-comment at :495-507); at line 527 it builds every trimmed section's
`recover_via.hint` from one hardcoded template — `` `call ${toolName} again with a narrower
filter/date_range, or a smaller top_k/limit, to reach the rest of "${path}"` `` — that names specific
parameter shapes (`date_range`, `top_k`, `limit`) which most callers (e.g. `phala_outlook_get`, whose
only non-`chart_id` parameter is `horizon_months`) do not actually declare.

## 2. Files to change

- `platform-mcp/src/lib/response_budget.ts:527` — replace the hardcoded template with a
  schema-neutral phrasing that does not assert the existence of any specific parameter, e.g.:
  ```ts
  hint: `call ${toolName} again with a narrower scope of its own declared parameters, to reach the rest of "${path}"`,
  ```
  This is the honest fix per CLAUDE.md §N.7 (no fabricated specifics) rather than attempting schema
  introspection: the surrounding comment (:495-507) explicitly documents that this helper handles
  proxy tools whose pagination contract it does NOT know per-call, so claiming specific field names
  (`date_range`/`top_k`/`limit`) is itself the defect — a schema-aware fix would require passing a
  tool-schema registry reference into this function, a larger change this spec does not recommend
  (see §6 — rejected alternative).
- No other files require changes. `instrument` (line 526) is already correct — F-09 is scoped to the
  `hint` text only, not the instrument name (already fixed for `phala_outlook_get` per RC-04,
  confirmed live in DIAGNOSIS.md §1).

## 3. Exit test

New assertion in whatever test file already covers `response_budget.ts` (or a new
`platform-mcp/src/lib/__tests__/response_budget_hint.test.ts` if none exists):
```ts
// FAILS today (hint names date_range/top_k/limit unconditionally); PASSES once hint is schema-neutral.
import { autoDetectTrimmableSections } from '../response_budget'
test('autoDetectTrimmableSections hint does not assert specific parameter names', () => {
  const content = { items: Array.from({ length: 20 }, (_, i) => i) }
  const sections = autoDetectTrimmableSections(content, 'phala_outlook_get')
  expect(sections[0].recover.hint).not.toMatch(/date_range|top_k|limit/)
})
```
Live confirmation (Stage V, post-build): re-run `phala_outlook_get({chart_id:'482012f1-…'})` and
assert `trim_report[].recover_via.hint` no longer contains the literal strings `date_range`, `top_k`,
or `limit`.

## 4. Sibling sites covered

`autoDetectTrimmableSections` is the SOLE call site of this hint template (only one `hint:` literal
at line 527 in the whole function) — every tool that falls through to this generic auto-detect path
(any proxy tool without a hand-declared `TrimmableSection`) is fixed by this one change. No
enumeration of affected tool names is needed since the fix is at the shared-helper level, not
per-caller. `plan_retrieval` (named in the finding alongside `phala_outlook_get`) is covered by the
same mechanism — not independently re-tested live this pass (see DIAGNOSIS.md §2), but structurally
guaranteed to be covered since it goes through the same function.

## 5. Recurrence guard

The exit test in §3 is the permanent recurrence guard — any future hardcoded hint template with a
specific parameter-name claim reintroduced at this call site fails the test immediately. Consider
(not built here, flagged for S2's judgment): a repo-wide lint rejecting hardcoded `date_range|top_k|
limit` literals inside any `hint:` string builder outside a file that actually declares those
parameters — larger scope, S2's call whether to add it now or defer.

## 6. Dependencies and rollback

No dependency on other lanes. Rejected alternative (documented for VERIFIER, not built): schema-aware
hints (looking up each tool's actual Zod schema to name its real parameters) would be more precise
but requires threading a schema registry reference through `autoDetectTrimmableSections`, a larger
API change to a HOT file touched by many other S2 lanes (F-44, F-46, F-13, F-56, F-111, etc. per
LEDGER_S2.md) — rejected in favor of the minimal, honest, zero-API-surface-change fix in §2.
Rollback: revert the single line; behavior returns to today's (misleading but non-crashing) hint
text — zero risk to any currently-working path, since `hint` is documentation-only, never parsed by
callers programmatically (confirmed: `recover_via.hint` is typed `string` throughout, no caller in
this codebase pattern-matches its contents).

## 7. Sub-claim coverage table

| D-2 sub-claim | Spec element that closes it |
|---|---|
| "recover_via.hint on phala_outlook_get names date_range/top_k/limit which the tool doesn't declare" | §2 fix at response_budget.ts:527 |
| "same pattern on plan_retrieval" | §2's fix is at the shared-helper level — covers every caller of autoDetectTrimmableSections structurally, no per-tool patch needed |
