# ga_structural Maximal-Depth — VERIFICATION pass (paste into Claude Code / Antigravity)

**This is a READ-ONLY verification of the deepest, highest-stakes code in the instrument. "380 tests pass + 175
smoke rows" proves the code RUNS — it does NOT prove the relationships are CORRECT, that Phase 1 ran first, or
that nothing crossed into L2. Do NOT merge/trust until all 4 parts pass.** Connect to prod (`amjis-db-password/3`),
chart `482012f1`. Make NO changes — report findings; the native decides remediation. Standing rails:
endpoint-verify (`?chart_id=`); FORENSIC; L1-is-authority; the three-tier boundary (fact vs meaning).

---

## PART 1 — DID PHASE 1 RUN FIRST? (the critical dependency — verify before anything else)

The implementation report described PHASE 2 (the 12 depth types) but NOT Phase 1 (Part A reference-not-recompute,
Part 0 yoga-fork, Part C DAG). Phase 2's graph results are only valid if Phase 1's referenced graph exists —
centrality/final-dispositor computed over INLINE-PROXY edge-weights instead of authoritative ga_strength values
= WRONG results. Establish Phase-1 status from the code + prod:

1. **Reference-not-recompute (Part A):** read the edge-weight builders (`_build_shadbala_extension_rows`,
   `_build_vimsopaka_ext_rows`, `_build_anubindu_rows`, the aspect builders). Do they NOW reference ga_strength's
   per-varga Shadbala / ashtakavarga_bindu_per_varga via fact_id, OR still compute an INLINE DIGNITY PROXY? Check
   a sample emitted edge-weight row's `constituent_facts_array` — does it resolve to a real ga_strength fact_id,
   or a recomputed number? **If still proxy → Phase 1 did NOT run; Phase 2's graph-theoretic results are computed
   on the wrong graph and must be recomputed after Phase 1.**
2. **yoga-fork (Part 0):** is yoga_label now single-writer (ga_structural only, ga_yoga repointed/firing-detail),
   or do BOTH still write it? Was `GA_STRUCTURAL_YOGA_FORK_FINDING.md` produced?
3. **DAG (Part C):** does `asset_registry.depends_on` for ga_structural now include all value-assets (ga_strength,
   ga_sensitive, ga_condition, ga_nakshatra, ga_tajaka, …)? Does upstream rebuild cascade ga_structural stale?
4. **enriched ingest (Part B):** does `_load_special_points` now read all 6 enriched ga_sensitive categories, or
   still ONLY `upagraha_position` (line 2847)?

**VERDICT for Part 1:** Phase 1 FULLY RAN / PARTIALLY / NOT-AT-ALL, with evidence per item. If not-fully, the
Phase-2 depth results are provisional and need recompute after Phase 1 lands.

---

## PART 2 — PROD ENDPOINT VERIFICATION (do the new categories actually populate on a real rebuild?)

Rebuild ga_structural for 482012f1 (orchestrator), then hit `/api/cockpit/stats?chart_id=482012f1` + query
chart_facts:
- The 14 new fact_categories actually EXIST with rows on prod (not just in a smoke test): sambandha, nakshatra-
  dispositor-chain, dispositor-tree, bhava-web, karaka-bhava-concordance, net-argala, n-way-config, graph-
  theoretic (final-dispositor/centrality/cycles/components), varga-provenance-meta, convergence-count,
  contradiction-pair. Report the prod row-count per category (vs the smoke-test counts: sambandha 36, nak-chain 9,
  tree 10, bhava-web 36, karaka-concordance 30, net-argala 12, graph-theoretic 20, convergence 21 …).
- ga_structural lit; FORENSIC 7/7 holds; floor recalibrated to achieved; endpoint shows no error/stale.
- ZERO duplicate fact_ids across the full prod build (not just the smoke sample).

---

## PART 3 — ACHARYA CORRECTNESS SPOT-CHECKS (the part tests CANNOT do — is it astrologically RIGHT?)

Hand-verify these against the ACTUAL chart (the deterministic results must be CORRECT, not just present). For
each, show the computed value AND the independent derivation:

1. **Final dispositor = Jupiter (claimed):** trace the rashi-dispositor chains by hand from 482012f1's placements.
   Does every chain actually terminate at Jupiter (or a Jupiter-containing cycle)? If the chains DON'T converge on
   Jupiter, the final-dispositor + the centrality built on it are WRONG. Show the chain traces.
2. **Sambandha grade (pick Sun↔Saturn or any conjunct/aspecting pair):** verify the 4-fold computation —
   conjunction? mutual aspect? exchange (parivartana)? mutual reception? — each component correctly detected, and
   the grade correctly aggregates them. Show the 4 sub-checks.
3. **Net argala on one house (e.g. 7th):** verify argala − virodhargala arithmetic resolves to the right net
   value with the right contributing houses (no off-by-a-house). Show the components.
4. **One parivartana/dispositor CYCLE:** verify a claimed cycle is a REAL closed loop in the chart (A disposits B
   disposits … back to A), not a DFS artifact. Show the loop.
5. **Centrality top graha:** does the most-central graha make astrological sense given the chart (heavily-aspected
   / dispositor-hub)? Sanity-check, not proof.

**VERDICT for Part 3:** each spot-check CORRECT / WRONG with the hand-derivation. Any WRONG = a real bug in the
deepest logic — flag, do not merge.

---

## PART 4 — L1/L2 BOUNDARY AUDIT (did any depth row cross into MEANING?)

The hard rule: ga_structural emits the deterministic FACT, NEVER life-meaning. Audit the 12 new builders + the
new constants for boundary violations:
- **`SIGNIFICANCE_TO_HOUSE` (new constant) — the highest-risk one.** Is it used to compute a STRUCTURAL
  relationship (e.g. which house a karaka relates to — OK, that's structural), or to LABEL A LIFE-DOMAIN /
  outcome (e.g. "house 7 = marriage prospects" — NOT OK, that's L2)? Read every use site.
- **convergence-count rows:** confirm they emit ONLY the COUNT (N edges on house/planet X), NOT a domain-mapping
  ("house7 → marriage"). The count is Tier-2; the meaning is L2.
- **contradiction-pair rows:** confirm they emit the OPPOSED-PAIR (structural), NOT a "which wins for the life-
  area" judgment (L2).
- **karaka-bhava-concordance:** "concordant/friendly/neutral" between karaka and lord is structural (OK); confirm
  it does NOT say what the concordance MEANS for the person's life.
- No row anywhere assigns salience-ranking ("most important"), a life-outcome ("strong career"), or a life-domain
  label. Those are L2.

**VERDICT for Part 4:** CLEAN / VIOLATIONS-FOUND, with the specific row/builder for each violation.

---

## DELIVERABLE

`GA_STRUCTURAL_DEPTH_VERIFICATION_v1_0.md`: the 4 verdicts (Phase-1-status / prod-endpoint / acharya-correctness /
boundary), each evidence-backed. Then a single recommendation: TRUST+MERGE / REMEDIATE-FIRST (with the specific
fixes). Remember: this is the relational substrate the ENTIRE L2 Bodha layer reads — a wrong final-dispositor or
a boundary leak here propagates into every downstream signal. Verify hard. NO changes in this pass — report only.
