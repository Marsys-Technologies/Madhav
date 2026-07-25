---
artifact: CONTRACT_STATUS (Elevation Campaign v2.1, Phase 0)
version: 1.0
status: LIVE
authored_by: RUNWAY session (non-participant, charter M2.4 — interface specs authored by the
  non-participant so no stream defines its own grading contract)
---

# Contract status

| id | title | status | owner | path | sha256 | deadline |
|---|---|---|---|---|---|---|
| C1 | budget_kb request param + paging response fields | FROZEN | RUNWAY | contracts/C1_BUDGET_KB_PAGING_v1_0.md | `4f54a8c1b2b76d1216517510c0cf9c694ce8fc4eb347a4d62278cf271dbafebf` | — |
| C2 | per-category receipt shape | FROZEN | RUNWAY | contracts/C2_PER_CATEGORY_RECEIPT_v1_0.md | `8d50fe6a82f916e712e50d0c884ae38df21edf50e39b25cef6c6464e731149f2` | — |
| C3 | schema-map output shape | FROZEN | RUNWAY | contracts/C3_SCHEMA_MAP_OUTPUT_v1_0.md | `3b8a30c73ceb49d42a6643d989c869cb75879619ee75efc47e97a16f7cc07ab2` | — |
| C4 | (β) — investigation required, not pre-authored | DRAFT | β (elev/beta) | — | — | T0+3h |
| C5 | (β) — investigation required, not pre-authored | DRAFT | β (elev/beta) | — | — | T0+3h |
| C6 | mechanisms row shape + returns-200 guarantee | FROZEN | RUNWAY | contracts/C6_MECHANISMS_ROW_SHAPE_v1_0.md | `67816150add4f3d21e4c0b53feb076cfb3a1b1748533e308fa0b7b192b475c32` | — |
| C7 | (γ) — investigation required, not pre-authored | DRAFT | γ (elev/gamma) | — | — | T0+4h |
| C8 | registry handler signature + post-trim envelope shape | FROZEN | RUNWAY | contracts/C8_REGISTRY_HANDLER_ENVELOPE_v1_0.md | `080842ed019b05186d1a5f2be66d4f1754cf48c853f53165fd6c811885358ab1` | — |

## Notes

C4/C5/C7 are deliberately left as DRAFT stubs with owner + deadline only, per charter M2.4: these
are rulings requiring investigation by the participant closest to the affected lane, and the RUNWAY
session (as the eventual grader-author) must not pre-author them to avoid biasing the grading
contract toward one participant's convenience.

C1/C2/C3/C6/C8 are grounded directly in current code (file:line references in each spec's
frontmatter) — none are invented from scratch; each documents what already exists, what is missing,
and freezes the delta as the interface every stream builds against.
