---
lane: F-36
stream: S5 (build routed by conductor; filed under S2)
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-36/SPEC.md, F-36/DIAGNOSIS.md. Confirmed no REVIEW_LEADS.md present (only DIAGNOSIS.md, SPEC.md, NEEDS_LEASE.md in lane dir). Source traced line-by-line against `/Users/Dev/par-night/main-ro/platform/src/lib/retrieval/registry/layers/register_d7_channel.ts`: lines 910-949 (clamp site), 1080-1223 (count query + both echo sites + both content objects).

## Q1-Q5, Q7

**Q1 — Mechanism vs symptom?**
PASS. The spec targets the mechanism directly: a single clamped local `offset` at :924 is echoed in both response branches without any `_requested`/`_clamped` disclosure pair. The fix adds two fields (`offset_requested`, `offset_clamped`) alongside the existing `offset` — no rename, no deletion, purely additive. This resolves the root cause, not a surface symptom.

**Q2 — All sub-claims mapped?**
PASS. All three DIAGNOSIS sub-claims have explicit spec elements:
- F-36a (silent clamp) → §2: clamp logic preserved, `offsetRequested` captures the original value before clamping.
- F-36b (clamped value echoed as caller's own) → §2: `offset_requested` field disambiguates.
- F-36c (no disclosure field) → §2: `offset_clamped` boolean is the exact missing disclosure.
Coverage table §7 makes this mapping explicit. No unmapped sub-claim.

**Q3 — Would the exit test fail on today's code?**
YES — verified by source trace. `res.content.offset_requested` does not exist in either content object (:1134-1145 rows-shape, :1210-1222 pivoted-shape). `res.content.offset_clamped` likewise absent. All three `expect` calls against new fields are genuine red today (value is `undefined` in each case). Second test (unclamped `offset=50`) also fails — `offset_clamped` absent regardless of clamping.

**Q4 — Sibling sites covered or excluded with reason?**
PASS. Both echo sites explicitly covered:
- :1140 (shape='rows' branch): `content = { ..., offset, limit, total, more_available }` — confirmed in source.
- :1216 (shape='pivoted' branch): same structure — confirmed in source.
Broader campaign-wide census of other clamp-with-silent-echo sites in other tools/files is explicitly excluded with a stated reason ('out of Stage-D budget, flagged as follow-up census for conductor, distinct from F-12/F-37 Flavor-A sweep'). Legitimate budget-scoped exclusion, not a silent gap.

**Q5 — Recurrence guard present and adequate?**
ACKNOWLEDGED-ABSENT. Spec states 'None built in this spec (single, isolated fix)' and explains that a broader clamp-census would be needed to determine whether a generic lint is warranted. Absence is named and reasoned, not silent. Defensible for a single narrowly scoped disclosure fix.

**Q7 — Unverified assumptions / file:line citations?**
ALL VERIFIED against main-ro source:
- :924 → `const offset = Math.max(0, Math.min(Number(args['offset'] ?? 0), 100_000))` EXACT MATCH.
- :1140 → `offset,` inside rows-shape content object EXACT MATCH.
- :1216 → `offset,` inside pivoted-shape content object EXACT MATCH.
- :1091-1120 → independent `SELECT COUNT(*)`/`COUNT(DISTINCT fact_subject)` count query confirmed; `total` is correctly independent (DIAGNOSIS §5 assertion verified).
No `offset_requested` or `offset_clamped` field exists anywhere in the current content objects — confirmed absent.

**writer_asset / data_delta / RS-A:**
Not applicable. This is a retrieval-layer TypeScript handler (`platform/src/lib/retrieval/registry/layers/`), not a Python writer-layer lane. Rebuild policy Level 0 shadow run applies to writer-layer lanes only. No RS-A, writer_asset, or data_delta declarations required or expected here.

## Named deficiencies (if INCOMPLETE-RETURN)

None.

## Verdict: COMPLETE
