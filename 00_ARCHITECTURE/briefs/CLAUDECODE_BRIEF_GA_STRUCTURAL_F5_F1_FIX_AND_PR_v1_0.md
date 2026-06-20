# ga_structural — Fix F5 (aspect off-by-one) + F1 (vargottama ref) + F6 (floor), rebuild, re-verify, PR

**Context:** `GA_STRUCTURAL_REMEDIATION_VERIFY_v1_0.md` = PASS (depth runs on prod, self-parivartana=0, single
path, acharya-correct). BUT two "non-blocking" findings are actually CORRECTNESS issues the native ruled FIX
BEFORE MERGE — because ga_structural is the relational substrate the ENTIRE L2 Bodha layer reads; an aspect
error propagates into every downstream signal. Fix F5 + F1 + F6, rebuild, RE-VERIFY (exercising F5 this time),
then PR with evidence. Standing rails: FROZEN orchestrator contract (HALT if a change is needed); L1-is-authority;
endpoint-verify (`?chart_id=`); FORENSIC 7/7; the three-tier boundary; floors=achieved; deterministic; only
482012f1.

---

## FIX 1 — F5: the aspect off-by-one in `_has_aspect` (the important one)

`_has_aspect` uses offset constants `{5,7,9}` which land on the **6th/8th/10th** positions, NOT the traditional
**5th/7th/9th** Parashari aspects. (House-distance is 1-indexed: the 5th aspect = +4 houses, 7th = +6, 9th = +8.
The current {5,7,9} = +5/+7/+9 = the 6th/8th/10th. Correct offsets = `{4,6,8}` — CONFIRM this against how
`_has_aspect` computes the house-distance before changing, so the fix matches the actual indexing convention.)
- Fix the offsets so 5th/7th/9th special aspects are detected at the correct houses. Also confirm the standard
  7th (opposition) aspect every graha casts is still correct after the change.
- **This is core aspect detection — it feeds `_build_sambandha_rows` (mutual-aspect component), the bhava-web,
  and graph edges. A fraction of ALL aspect-based relationships were mis-detected.** Verify the fix doesn't break
  the cases that were coincidentally right (e.g. same-house / 7th-opposition pairs).
- If correcting the offset reveals the house-distance helper itself is inconsistent → fix at the source, don't
  patch around it.

## FIX 2 — F1: vargottama constituent-ref key mismatch (the L1-authority break)

`_real_fact_id_ref` looks up key `'total_virupas'` but `graha_shadbala_total` stores key `'rupa'` → the
vargottama constituent_facts_array resolves to empty `[]`. The `is_vargottama` flag is correct; only the
provenance back-reference is broken. Fix the key param (`'total_virupas'` → `'rupa'`, or whatever the actual
stored key is — VERIFY against the ga_strength data, don't assume) so the constituent_facts resolve to the real
ga_strength fact_id. (L1-is-authority: every reference must resolve.)

## FIX 3 — F6: stale target_floor (trivial)

Migration 318: `UPDATE asset_registry SET target_floor = <achieved count after rebuild> WHERE
asset_id='ga_structural';` + seed patch (seed already says 77,821 — confirm the post-fix rebuild count and use
THAT, not a stale number). Ledger-reconcile.

---

## REBUILD + RE-VERIFY (exercise F5 this time — the prior pass had a blind spot)

Rebuild ga_structural for 482012f1. Then re-run the verification, BUT specifically:
1. **⭐ F5 must be EXERCISED.** The prior acharya check (MAR_SAT) was a SAME-HOUSE pair → it did NOT test the
   aspect offset. This time, hand-verify a sambandha grade for a pair that is in a **5th, 7th, or 9th special-
   aspect relationship** (e.g. a Jupiter 5th/9th-aspect pair, or a Mars 4th/8th-aspect pair) — confirm the
   mutual-aspect component is now detected at the CORRECT house. Show the pair, the house-distance, and that the
   aspect fires (or correctly doesn't). A same-house pair alone is NOT acceptable re-verification of F5.
2. **F1:** sample a vargottama row → constituent_facts_array now resolves to a real ga_strength fact_id (not []).
3. **Re-confirm the prior PASSes still hold:** single path; 12/14 depth categories non-zero on prod (counts may
   shift slightly with the corrected aspects — that's expected and CORRECT, record the new counts); zero
   self-parivartana; Jupiter final-dispositor; HOUSE_5 net_argala; boundary clean; FORENSIC 7/7; endpoint
   lit/no-error/not-stale; floor=achieved (migration 318).
4. Note: corrected aspects WILL change some sambandha/bhava-web/graph rows — verify the changes are in the RIGHT
   direction (relationships that should fire now fire, spurious ones stop), not just "different."

Output: update `GA_STRUCTURAL_REMEDIATION_VERIFY` to v2 (or a new `GA_STRUCTURAL_F5F1_VERIFY`) with the F5-exercised
acharya check + the F1 resolution + the updated prod counts.

---

## PR (the merge — with evidence in the body)

Open a PR (NOT a local merge — this is the highest-stakes asset). PR body:
- The maximal-depth + remediation summary; the F5/F1/F6 fixes.
- The verification EVIDENCE: depth-category prod counts, self-parivartana=0, the F5-exercised sambandha check, the
  F1 resolution, Jupiter final-dispositor, net_argala, boundary-clean, FORENSIC 7/7. (Paste the actual numbers,
  not "verified".)
- The 28 pre-existing CI failures confirmed zero-diff in touched files.
Merge-verify after; confirm endpoint still green post-merge.

**Then ga_structural is genuinely complete — maximal Tier-2 depth, single-path, aspect-correct, prod-verified,
single-source — and L2 Bodha can open on it.** Report back: the F5-exercised acharya check (the new aspect-pair),
the F1 resolution, the updated depth counts, and the PR/merge SHA.
