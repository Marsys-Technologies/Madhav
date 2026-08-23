---
finding: F-123
stream: S1 DVARA (spec) → S4 VĀCA (build, per conductor routing 2026-08-16)
class: CL-11 dead pointer (missing required-args on a tri_plane pointer)
stage: S COMPLETE — awaiting VERIFIER REVIEW, then routes to S4's builder to apply
build_note: S1 does not touch kala_views/now.ts or explain.ts directly (S4's lease per the
  §2.1 kala_views file split). This spec was written by reading both files (read-only) to
  make the diff exact and apply-ready for S4's builder, per conductor's routing decision.
---

## 1. Root cause (one sentence, mechanism-level)

`kala_now_get`'s `tri_plane.interpretation_ref` is built at `now.ts:1760-1763` via
`pointerTo('kala_explain_get', '<hint text>')` — a bare `{instrument, hint}` pair with no argument
payload — while the tool it points to, `kala_explain_get`, hard-validates
`either \`domain\` or \`bhava\` is required` at `explain.ts:587` (`return kalaErrorOutput(TOOL_NAME,
'either \`domain\` or \`bhava\` is required')`); `kala_now_get`'s own NOW-state response has no single
privileged domain to supply (its windows span up to 8-9 domains simultaneously, confirmed live in
DIAGNOSIS.md §1), so a caller following the pointer exactly as advertised has no correct value to
give and dead-ends.

## 2. Files to change

- `platform-mcp/src/tools/kala_views/now.ts:1752-1772` — the `triPlane` object literal. Two
  candidate directions; **recommend (a)**:
  - **(a) Degrade the pointer honestly instead of guessing a domain.** Change
    `interpretation_ref` to a variant `pointerTo` call (or a new helper,
    `pointerToWithCaveat`) that appends the missing-args caveat directly into the hint text, e.g.:
    ```ts
    interpretation_ref: pointerTo(
      'kala_explain_get',
      'Why this NOW state reads as it does — the drivers and classical grounds behind the active ' +
      'windows and confluence. Requires a `domain` or `bhava` argument (this NOW state spans ' +
      'multiple domains; supply the one you care about, e.g. domain="career").',
    ),
    ```
    This is the lower-blast-radius option: it does not change `kala_explain_get`'s contract or
    behavior at all, only makes the pointer honest about what it needs — consistent with
    CLAUDE.md §N.7 item 6 (honest null/honest caveat over a silently-broken promise).
  - **(b) Rejected for this spec, flagged for S4's own judgment:** have `kala_now_get` compute its
    single strongest-signaled domain (e.g. from its own `windows[].domains[]`, ranked by
    `max_orb_strength`) and pass it as a real `domain` arg. This makes the pointer actually
    resolvable in one hop, but requires `now.ts` to make an editorial "which domain matters most"
    judgment that NOW's own multi-domain design (confirmed live: 8-9 domains per window) argues
    against privileging any one domain. S4 may prefer this if UX weighs above architectural purity —
    left as their call, not built here.
- `platform-mcp/src/tools/kala_views/explain.ts` — **no change required** under option (a). Under
  option (b), no change required either (the caller would now supply a valid `domain`). Only relevant
  if S4 chooses a third option not enumerated here.

## 3. Exit test

New test in `platform-mcp/src/tools/kala_views/__tests__/now_tri_plane.test.ts` (or existing
`now.ts` test file):
```ts
// FAILS today (hint gives no indication domain/bhava is required); PASSES once the hint
// (or the pointer's own arg payload) discloses the requirement.
test('kala_now_get tri_plane.interpretation_ref discloses kala_explain_get\'s required args', () => {
  const response = await kalaNowGet({ chart_id: NATIVE_CHART_ID })
  const ref = response.tri_plane.interpretation_ref
  expect(ref.hint).toMatch(/domain|bhava/i)
})
```
Live confirmation (Stage V): call `kala_now_get(chart_id)`, read `.tri_plane.interpretation_ref.hint`,
confirm it now names the requirement; optionally also confirm that blindly following the (now-honest)
pointer with only `chart_id` still 400s as expected (that's correct behavior under option (a) — the
fix is disclosure, not making the bare call succeed) — VERIFIER should confirm which behavior is
intended before running Stage V, since option (a) vs (b) changes what "passing" means.

## 4. Sibling sites covered

Not independently re-verified this pass (flagged in DIAGNOSIS.md §4 as a Stage-S follow-up, now
partially addressed): `now.ts`'s `prediction_ref` (→ `kala_ahead_get`) and `intervention_ref` (→
`kala_elect_get`) at lines 1764-1771 were spot-checked by reading the same `triPlane` block (§2
above) — both target tools take only `chart_id` as their required argument (per this session's own
tool schemas: `kala_ahead_get` and `kala_elect_get` both list only `chart_id` as `required` in their
MCP schema), so neither has this defect. **No other sibling sites in this file need the same fix.**
Other `kala_views/*` files (`ahead.ts:1835`, `elect.ts:740-741`, `priority.ts:383-391`,
`story.ts:564-575,748-749`) also call `pointerTo` with various targets — NOT audited this pass for
the same missing-required-args pattern; flagged as a genuine open census gap for S4 to close before
declaring CL-11's "dead pointer" class fully swept in the `kala_views/*` family.

## 5. Recurrence guard

The exit test in §3 covers this specific pointer. A stronger, generic guard (not built here, flagged
for S4): a lint/contract test that, for every `pointerTo(toolName, hint)` call across `kala_views/*`,
looks up `toolName`'s registered MCP schema and fails if any of that schema's `required` fields
(beyond `chart_id`, which every pointer target trivially inherits) is absent from the calling tool's
own guaranteed-available fields — this would close the sibling-census gap in §4 mechanically rather
than by hand-audit. Recommended but not authored in this spec (out of S1's diagnosis scope; S4 should
decide if it's worth the investment given only one instance is confirmed so far).

## 6. Dependencies and rollback

No dependency on other lanes. Independent of F-73 (also touches `now.ts`, different code region —
`gochara_narrative` vs. `tri_plane` — no line overlap, safe to build in parallel). Rollback: revert
the single hint-string change; behavior reverts to today's (misleading but non-crashing) pointer —
zero risk, since this is a string-content-only change under option (a).

## 7. Sub-claim coverage table

| D-2 sub-claim | Spec element that closes it |
|---|---|
| "kala_explain_get hard-errors on the exact call shape kala_now_get advertises" | §2 option (a): the pointer's hint now discloses the requirement before the caller ever calls kala_explain_get bare |
| "the advertised drill is chart-scoped; the target is domain-scoped" | §2 option (a) makes this scope mismatch explicit in the hint text itself, rather than silently omitted |
| "'Explain my current dasha' is domain-less by nature, no correct value to supply" | Acknowledged directly — option (a) does not force a fabricated domain; option (b) is flagged as S4's call if they want one-hop resolution instead of disclosure |
