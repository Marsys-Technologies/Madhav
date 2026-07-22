---
artifact: VERIFY_RC-09.md
canonical_id: RETRIEVAL_RESIDUAL_VERIFY_RC09
version: 1.0
status: VERDICT — ACCEPT
residual: RC-09 (R-8) — Resolve all 51 W1 dark tables
branch_verified: res/rc09-dark-tables @ 83f881f7 (worktree wf_3e85c10c-202-2)
base: main @ 2df42b61
governed_by: 00_ARCHITECTURE/briefs/RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md §E RC-09
verifier_role: INDEPENDENT (did NOT implement; brief §D.4)
verified_by: opus-4.8 verifier agent
verified_at: 2026-07-22
---

# RC-09 Independent Verification — Verdict: **ACCEPT**

## Summary

RC-09 (R-8) delivered a docs-only closure: `DARK_TABLE_DISPOSITIONS_v3_0.md` (211 lines)
+ `RESOLVER_RULINGS.md` (128 lines), zero code changes. I independently re-verified the
count, the dispositions against live code, the DONE bar verbatim, and the scope boundary.
**All checks pass. The residual's DONE bar is met. ACCEPT.**

The implementer's claim ("no code changes needed; the W1-addendum + W2/W2b wiring already
landed on main; RC-09 is a documentation/verification residual") is **substantiated**.

---

## (a) Tests — rerun independently: PASS

The worktree had no `node_modules` (implementer's `npx vitest` claim ran elsewhere).
I symlinked the main checkout's `node_modules` (package.json byte-identical between the
two, `diff` exit 0) and ran the suite against the branch source, then removed the symlink:

```
./node_modules/.bin/vitest run src/lib/retrieval/registry
 Test Files  97 passed | 17 skipped (114)
      Tests  987 passed | 125 skipped (1112)   0 failed
```

**Exactly matches the implementer's reported 97/17, 987/125, 0 failed.** (Trivially expected,
since the branch is docs-only over a real merged main commit — but confirmed, not trusted.)

## (b) DONE bar (brief §E RC-09, verbatim) — MET on all three clauses

> **DONE:** zero tables in NEEDS-OWNER; `DARK_TABLE_DISPOSITIONS_v3_0.md` shows all 51
> terminal; the two mimamsa ledgers recorded GATED with the calibration-maturity revisit
> condition.

1. **Zero tables in NEEDS-OWNER** — CONFIRMED by independent recount (see (d)).
2. **`DARK_TABLE_DISPOSITIONS_v3_0.md` shows all 51 terminal** — CONFIRMED: file exists,
   51 table rows, every row carries one of the five terminal states.
3. **Two mimamsa ledgers GATED w/ calibration-maturity revisit** — CONFIRMED:
   `mimamsa_fact_adjustment` + `mimamsa_signal_adjustment` = GATED, revisit condition
   "calibration-loop maturity or a Samīkṣā drill requirement", matching `RULINGS_ADOPTED.md`
   §F item 3 **verbatim** (I read the source: lines 55–57 carry that exact text).

## (c) RC-06 (golden set) — NOT APPLICABLE to this branch

The verifier checklist item (c) targets RC-06. This branch (`res/rc09-dark-tables`) contains
**no golden-set changes** — its entire diff is two markdown files under
`briefs/retrieval_residual/`. RC-06 is a separate residual on `res/rc06-golden-set`
(a distinct locked worktree). Nothing to spot-check here; out of scope for RC-09.

## (d) RC-09 count 51/51 — recounted from source: CONFIRMED

**Independent recount from the W1 census** (`TABLE_CONCEPT_DISPOSITIONS_v1_0.md`, the
generator-produced source, generated_at 2026-07-19):
- Extracted every `NEEDS-OWNER` table → 52 unique names, but one is `chart_panchanga`,
  which v1.0 **itself corrected to SERVED** in its "own corrections" section
  (`NEEDS-OWNER (DARK) | **SERVED**`). True dark set = **51**.
- Extracted the 51 table rows from the delivered `DARK_TABLE_DISPOSITIONS_v3_0.md`.
- `diff census51 vs delivered51` → **empty (exit 0). Exact set match.** No table dropped,
  none invented.

**Disposition tally recount** (from the delivered doc's table rows):
SERVED-DIRECT 40 · SERVED-VIA 1 · OPERATIONAL 4 · GATED 4 · RETIRED 2 = **51**. Sums correctly.
(A raw grep shows 5 `**GATED**` hits — one is the prose quote in §3, not a table row; the
table itself has exactly 4 GATED rows.)

**Spot-check of dispositions against actual code (≥10 tables, all five states):**
- SERVED-DIRECT files exist on disk AND registered in layer `index.ts`:
  `query_prashna_lagna_methods.ts`, `get_condition_composite.ts`, `get_prashna_lagna.ts`,
  `query_cdlm_summary.ts`, `query_triangulation.ts`, `query_insight_embeddings.ts`,
  `query_class_priors.ts`, `query_load_bearing.ts` — all present + imported.
- SERVED-DIRECT "already-served" line-anchored claims verified live:
  `bodha_anomalies` → real `FROM bodha_anomalies` in `query_contradictions.ts`;
  `brahma_activity_ontology` + `ga_prashna_judgment` → real `FROM` SQL in
  `register_p1_synthesis.ts` (prashna_undertaking_get, lines 798/841).
- GATED (4): grepped the full `registry`/`tools`/`resources` surface — **zero serving
  queries**. All references are file-header comments in `query_load_bearing.ts` / `index.ts`
  plus a test asserting the SQL does NOT contain them. Correctly withheld.
- RETIRED (2): `ganita_graha_sthana` / `ganita_dashas` → **zero live `FROM` queries** in
  serving code; consistent with the RETIRED reachability rationale.

Every non-SERVE disposition traces to a concrete per-row reason (access-control table,
QA-harness table, dead writer path, or the pre-ruled L5 seal) — not "avoid the work."

## (e) RC-10 (namespace coverage) — NOT APPLICABLE to this branch

Checklist item (e) targets RC-10. This branch contains **no namespace/bridge work** — it is
RC-09, docs-only. RC-10 is a separate residual. Nothing to recompute here; out of scope.

## (f) must_not_touch — CLEAN

Full diff vs main is exactly two files:
```
00_ARCHITECTURE/briefs/retrieval_residual/DARK_TABLE_DISPOSITIONS_v3_0.md
00_ARCHITECTURE/briefs/retrieval_residual/RESOLVER_RULINGS.md
```
Grep of the diff for `writer|orchestrat|migration|kala_|gochara|chart_facts|*.ts|*.py|*.sql`
→ **NONE**. No FROZEN orchestrator / WriterBase, no `ga_*/bo_*/ka_*/ph_*/mi_*` writer logic,
no chart_facts semantics, no D-4b `kala_*`/gochara serving semantics, no migrations. The two
`kala_*` dark tables were confirmed READ-ONLY (dispositioned as already-served, serving
semantics untouched — brief §J respected).

---

## Adversarial notes (honest caveats, none blocking)

1. **Depth of disposition judgment.** The 51-table *set* is exactly right and my
   ~12-table code spot-check across all five states found zero discrepancies. The deeper
   SERVED-DIRECT-vs-OPERATIONAL-vs-GATED *judgments* for tables I did not individually open
   rest on `TABLE_CONCEPT_DISPOSITIONS_v2_0.md`'s hand-verification (which the delivered doc
   confirms rather than re-derives). Given this is a zero-code documentation residual and
   every sampled row held up, residual risk is low.
2. **FINAL_REPORT §H.6 R-8 row not updated.** Deliberate, and correct per the brief's wave
   model: RC-16 (the seal) owns the consolidated §H.6 table so parallel lanes don't collide.
   Consistent with sibling lanes (RC-05/07/08/12/13). Not a defect.
3. **Environmental:** a pre-existing untracked `node_modules` symlink sits at the worktree
   root (timestamp predates this verification); it is not in the commit and does not affect
   the branch. Left as-is.

## Verdict

**ACCEPT.** All six checklist axes pass (with (c)/(e) N/A to an RC-09 branch by construction).
The §E RC-09 DONE bar is met on every clause; the count is genuinely 51/51 terminal, recounted
from source; sampled dispositions match live code; the two mimamsa ledgers carry the exact
recorded GATED revisit condition; the test suite passes 987/0; and the diff touches zero
must_not_touch paths. RC-09 is closable.
