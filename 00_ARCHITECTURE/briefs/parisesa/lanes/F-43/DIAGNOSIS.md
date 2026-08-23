---
finding: F-43
stream: S1 DVARA
class: CL-11 (dead recover_via pointer — 'unknown_tool' placeholder)
role: CENSUS lane for F-17's exemplar — the ~19 additional sites beyond F-17/F-18
stage: D COMPLETE — spec/build ride on F-17's REVIEW.md once COMPLETE
---

## 1. Live reproduction

```
mcp__marsys-jis-direct__catalog_assets_list({})
```
Not independently re-run this pass; corpus evidence_file already recorded a live PASS-reproduction
on `catalog_assets_list` specifically (the only one of the ~19 the audit live-tested; the other ~16
named tools were source-grep-identified per the finding's own text, PASS verdicts not retroactively
downgraded without live confirmation — same discipline preserved here).

## 2. Claim decomposition

1. "catalog_assets_list live-reproduces the F-17/F-18 defect class" — inherited PASS from corpus,
   not re-run this pass (see §1).
2. "~19 more `register_p1_aliases.ts` sites share the identical bare `dualOutput(data)` call,
   independent of whether each was individually live-retested" — CONFIRMED and made exact by this
   session's own grep (§4 below supersedes the corpus's "~19" with a precise, line-numbered 19).

## 3. Mechanism → file:line

Same helper as F-17: `platform-mcp/src/tools/register_p1_aliases.ts:188`
(`function dualOutput(data, toolName='unknown_tool')`). No new mechanism — this lane's contribution
is exhaustive census, not a new root cause.

## 4. Sibling census (this lane's actual deliverable)

Full grep this session: `grep -n "return dualOutput(data)$" register_p1_aliases.ts` → 21 bare sites.
Removing F-17's own site (1249) and F-18's (657) leaves exactly **19 sites**, matching the corpus's
"~19 more" claim precisely: lines **606, 1155, 1207, 1368, 1499, 1522, 1558, 1570, 1582, 1594, 1606,
1618, 1630, 1670, 1781, 1844, 1860, 1874, 1971**.

Corpus named tools (16 of the 19, by tool name, not independently re-verified line-by-line this
pass): `catalog_assets_all`, `catalog_assets_l0`, `ref_vector_search`, `ref_remedies_get`,
`ref_remedies_chart_get`, `ref_remedies_by_category_list`, `ref_remedy_get`,
`ref_tantric_remedies_get`, `ref_remedies_by_planet_get`, `ref_mantras_get`, `kala_muhurta_get`,
`mimamsa_calibration_get`, `ganita_natal_positions_compute`, `ganita_special_lagnas_get`,
`kala_yoga_activation_get`, plus `bodha_signals_get`'s own outer wrapper — 15 named + 1 wrapper = 16;
this session's line-numbered grep gives 19 total slots, so 3 of the 19 lines are either unnamed in
the corpus text or the corpus's informal count undercounted by ~3 (not investigated further — the
exit test in F-17's SPEC.md §3 checks the file globally by regex, not by named tool list, so this
discrepancy does not block the fix and is noted here only for VERIFIER's awareness).

## 5. Blast radius

Same as F-17/F-18 — no separate build. This lane's DIAGNOSIS.md exists to make F-17's SPEC.md §2
file-list (which already names all 19 of these lines) independently auditable against a second,
finding-specific census. **Disposition: fold into F-17. F-17's REVIEW.md §7 coverage table should
name F-43 explicitly alongside F-18 once amended.**
