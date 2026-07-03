---
canonical_id: CLAUDECODE_BRIEF_BA_P7A_CLASSICAL_COMPLETIONS
version: 1.0
status: READY-FOR-EXECUTION — gated on BA-P3B COMPLETE (runs ∥ P5/P6); conductor fills ⟦SLOT⟧s
created: 2026-07-03
author: Cowork (Beyond-Acharya unified program; substance frozen — conductor fills slots only)
program: BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN_v1_0.md — phase P7A (classical completions)
slots: ⟦PRATINIDHI_E4_RANKING_LEDGER_REF⟧ ⟦P5_CLOSE_SHAS⟧
common_rules: FROZEN contract · canonical-or-floor (cited values or NULL+reason — NEVER a computable
  substitute) · deterministic extraction (regex/rule-based, no generative LLM for curation) · two-chart rule.
may_touch: ["bg_rules writer EXT (Nadi + muhurta/tajika Phase-2 extraction)", "bg_transit_rules completion", "ga_condition remaining avastha unfloors", "L1/L2 incremental rebuild for new categories"]
must_not_touch: ["orchestrator", "salience formula (v2 frozen)", "priors", "mi_* (P6 owns)", "existing rule content (append-only)"]
---

# BRIEF BA-P7A — CLASSICAL COMPLETIONS

Work items in the order ⟦PRATINIDHI_E4_RANKING_LEDGER_REF⟧ rules (default leverage order below):

1. **Nadi rule extraction:** Bhrigu Nandi Nadi + Nadi Navamsa are IN the text corpus
   (classical_text_chunks) with D108/D150/D2700 positions already computed at L1 but zero interpretive
   consumers. Extract Nadi jataka rules via the deterministic pattern library (l0_rules.py precedent,
   new pattern families for Nadi aphorism structure); quality-gate ≥0.6 LIVE per the standing threshold;
   rules cite chunk_ids.
2. **AV-transit rule completion:** finish bg_transit_rules coverage (per-graha per-house gochara phala +
   vedha pairs + moorti determinations), cited to BPHS Ch.29/Phaladeepika Ch.26/Saravali; the P5A gate
   machinery consumes them.
3. **Remaining avastha unfloors:** any lajjitadi/sayanadi sub-components floored in P3A get computed
   where a cited method exists (else remain floored WITH reason — canonical-or-floor).
4. **Incremental rebuild:** new fact_categories flow L1 → bo_laksana v2 (full-enumeration projects them
   automatically) → ranked by the frozen formula. NO formula change.

## Anti-goals
No generative-LLM curation. No new judgment constants outside the registry. No salience formula edits —
if a new family ranks absurdly, that is a PRIORS issue → log to Judgment Ledger for the Pratinidhi, do
not hack the formula.

## Exit gates
- [ ] new rules cite resolvable chunk_ids; extraction deterministic (re-run = identical) `[verify-against: db]`
- [ ] new fact_categories arrive RANKED sanely: no new family occupies >30% of any domain top-20
      (degeneracy-adjacent gate) `[verify-against: db]`
- [ ] golden-eval non-regression; INTERPRETATION citations now include Nadi sources where relevant
      `[verify-against: prod]`
