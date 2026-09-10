---
finding: F-18
stream: S1 DVARA
class: CL-11 (dead recover_via pointer — 'unknown_tool' placeholder)
role: REPLICATION of F-17's exemplar — same mechanism, same file, sibling call site
stage: D COMPLETE — spec/build ride on F-17's REVIEW.md once COMPLETE
---

## 1. Live reproduction

```
mcp__marsys-jis-direct__bodha_graph_traverse_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa',
  mode:'paths', about_from:'lord_of(bhava 10)', about_to:{type:'graha',graha:'Moon'}, direction:'directed'})
```
Not independently re-run this pass (F-17's identical live call already confirms the mechanism live
in this session); corpus evidence_file already recorded a live PASS-reproduction (97→48 trim,
`recover_via.instrument:'unknown_tool'`). No reason to doubt it — same file, same helper, same
default. STILL REPRODUCES.

## 2. Claim decomposition

Identical single assertion to F-17: `recover_via.instrument` reads `'unknown_tool'` when trimmed.

## 3. Mechanism → file:line

`platform-mcp/src/tools/register_p1_aliases.ts:657` — `return dualOutput(data)` (bare, no toolName),
same `dualOutput(data, toolName='unknown_tool')` default at line 188. Identical root cause to F-17.

## 4. Sibling census

Inherited from F-17's DIAGNOSIS.md §4 (21 bare sites total, this is one of them). Not re-derived.

## 5. Blast radius

Same as F-17 — this lane does not build independently; it is folded into F-17's SPEC.md line-list
(line 657 already included) and closes when F-17's fix lands and the shared exit test asserts zero
bare `dualOutput(data)` sites remain.

**Disposition: fold into F-17. No separate SPEC.md/REVIEW.md — F-17's REVIEW.md covers this finding's
sub-claim per its §7 coverage table once amended to name F-18 explicitly (S1-LEAD action at Stage R).**
