---
lane: F-45 (standalone — Flavor B of the CL-06 family: narrative count computed before generic
  trim, never re-derived after)
stream: filed under S2; build mostly routes to S5 (5 of 6 touched files are S5's lease); ONE
  optional S2-owned contribution possible (see §2b)
stage: S — SPEC
author: MATRA-LEAD (S2)
status: DRAFT — awaiting VERIFIER review
---

# SPEC — resync narrative `*_count` fields after generic budget trim

## 0. Board correction

Same BRANCH-EXISTS→OPEN correction as F-12/F-36/F-37 (DIAGNOSIS.md §5). One nuance unique to
F-45: the root cause partly lives inside S2's own `response_budget.ts` (its trim mechanism has no
concept of a scalar count field describing a trimmed array) — see §2b for the optional S2-owned
piece, separate from the five call-site fixes.

## 1. Root-cause statement

Five tools (`bodha_signals_get`, `synth_chart_brief_get`, `kala_priority_ranking_get`,
`kala_windows_get`, `bodha_remedies_get`) each compute a narrative summary field
(`served_count`/`coverage_receipt`/`signal_count`/`activation_count`+`predicate_count`/
`prescription_count`) from an array's `.length` BEFORE that array is trimmed by the generic
budget mechanism (`finalizeMcpBudget` or `applyAutoBudgetToEnvelope`), and the scalar is never
re-derived or flagged stale afterward — `response_budget.ts`'s trimmers only ever touch declared/
auto-detected ARRAY sections, with no concept of a paired scalar.

## 2a. Files to change — five call-site fixes (S5's lease, per conductor routing)

| Tool | File:line (count computed) | Fix |
|---|---|---|
| `bodha_signals_get` | `register_p1_aliases.ts:589` | Move `served_count: rows.length` computation to AFTER `finalizeMcpBudget` (`:599`) runs, reading the post-trim array length, OR set `served_count` from the post-trim `inner['signals'].length` |
| `synth_chart_brief_get` | `register_p1_synthesis.ts:836-843` (`coverage_receipt` prose) | The count is baked into a STRING before `dualOutput`'s `applyAutoBudgetToEnvelope` trims `verdict_summary` at return time (`:871`) — restructure so `coverage_receipt`'s `verdictCount` is read from the trimmed array's length, or move receipt construction to after the trim (requires the trim to run before `dualOutput`'s return, i.e. call `applyAutoBudgetToEnvelope` explicitly earlier in the function rather than only at the `dualOutput` call site) |
| `kala_priority_ranking_get` | `register_p1_aliases.ts` `dualOutput` wraps `signal_count` (primitive itself, `call_service_wrappers.ts:626`, is honest — staleness introduced one layer up by the wrapping `dualOutput`'s trim) | Same shape: re-derive `signal_count` from `content.ranked_signals.length` after `finalizeMcpBudget` trims it |
| `kala_windows_get` | `register_p1_aliases.ts:928` wraps `query_temporal_activation.ts:365,371,375,377` (4 count fields, only `activation_count`/`predicate_count` confirmed live-stale; `window_family_count`/`forward_window_count` same structural risk) | Re-derive ALL FOUR count fields (`activation_count`, `window_family_count`, `forward_window_count`, `predicate_count`) from their respective post-trim array lengths |
| `bodha_remedies_get` | `register_p1_aliases.ts:1015-1025` wraps `query_remedies.ts:590,592` (`resonance_count`, `prescription_count`) | Re-derive both from post-trim array lengths |

**BUILD-STAGE INSTRUCTION:** each file's exact restructuring (move the trim call earlier vs.
re-read the array length after trim) depends on that file's own control flow — DIAGNOSIS.md §3
traces each site's exact call order; build must re-verify against current code before choosing
the specific mechanical fix (move-count-computation vs. re-derive-after), since either achieves
the same observable correctness.

## 2b. OPTIONAL, S2-owned contribution (this stream's own hot file) — a shared mechanism to
prevent recurrence, NOT required to close F-45 itself

`response_budget.ts` (S2 HOT): teach `TrimmableSection` an optional `companionCountField: string`
that names a sibling scalar field the trimmer should update to the post-trim `kept_count` after
trimming. This would let all five (and future) call sites opt into automatic resync instead of
hand-rolling it. **This is new capability, not required by F-45's own exit test** — flagged as a
possible follow-up S2 contribution; VERIFIER should treat §2a (the five call-site fixes) as the
spec's actual required scope, and §2b as an optional enhancement noted for the conductor's
consideration, not gating F-45's closure.

## 3. Exit test

```ts
test('narrative counts stay in sync with their sibling array after trim', async () => {
  const signals = await callTool('bodha_signals_get', { chart_id: CANONICAL_CHART_ID, top_k: 200 })
  expect(signals.content.verdict_summary.served_count).toBe(signals.content.signals.length)  // fails today: 200 !== 20

  const brief = await callTool('synth_chart_brief_get', { chart_id: CANONICAL_CHART_ID, depth: 'complete' })
  expect(brief.content.coverage_receipt).toContain(`${brief.content.verdict_summary.length} domain verdicts`)  // fails today

  const ranking = await callTool('kala_priority_ranking_get', { chart_id: CANONICAL_CHART_ID, top_k: 100 })
  expect(ranking.content.signal_count).toBe(ranking.content.ranked_signals.length)  // fails today: 100 !== 50

  const windows = await callTool('kala_windows_get', { chart_id: CANONICAL_CHART_ID, limit: 500 })
  expect(windows.content.activation_count).toBe(windows.content.activations.length)  // fails today: 500 !== 5
  expect(windows.content.predicate_count).toBe(windows.content.predicates.length)     // fails today: 500 !== 10

  const remedies = await callTool('bodha_remedies_get', { chart_id: CANONICAL_CHART_ID, fields: 'all' })
  expect(remedies.content.prescription_count).toBe(remedies.content.prescriptions.length)  // fails today: 27 !== 13
})
```
All six assertions fail today per DIAGNOSIS.md §1's live table; all pass once §2a's five fixes
land.

## 4. Sibling sites covered

`window_family_count`/`forward_window_count` (DIAGNOSIS.md §4, not confirmed live-stale this pass
but same structural risk) — included in §2a's `kala_windows_get` fix scope (all four count fields
fixed together, not just the two confirmed-live ones).

## 5. Recurrence guard

§2b (optional) is the real recurrence guard if built. Without it, no automated guard — a future
sixth tool with the same pattern would need its own finding. Flagged honestly, not treated as
closed by this spec alone.

## 6. Dependencies and rollback

No DB migration. 5 of 6 files are S5's lease (build routes there per conductor); `response_budget.ts`
(§2b, optional) is S2's own, built separately/later if the conductor wants it. Rollback: each of
the five call-site fixes is independent, no shared new helper in the required §2a scope (§2b, if
built, would be a shared helper — rollback note for that piece specifically: revert
`response_budget.ts` hunk, all five call sites keep working via their own local resync, no hard
dependency created).

## 7. Coverage table

| Sub-claim | Spec element |
|---|---|
| F-45a (bodha_signals_get) | §2a row 1 |
| F-45b (synth_chart_brief_get) | §2a row 2 |
| F-45c (kala_priority_ranking_get) | §2a row 3 |
| F-45d (kala_windows_get) | §2a row 4 (all 4 count fields, not just the named one) |
| F-45e (bodha_remedies_get) | §2a row 5 |
| F-45f (no trim_report cross-reference) | not directly closed by §2a — resyncing the count makes the cross-reference moot rather than adding a pointer; VERIFIER to confirm this is sufficient or whether an explicit pointer is also wanted |
