# PR body: bg_ontology citation pass 2 (OS-2026-10-05-CITATIONS)

**APPLY ORDER (SS 2026-10-05; nothing queues before RELEASE + Pravaha's 90 minutes; rebuilds wait for S-L2):**
1. Rebuild **bg_doshas** first: the `entity_class='dosha'` partition of `brahma_ontology` is written by the bg_doshas writer. **Accept bg_yogas, bg_dasha_systems and bg_ontology showing stale** (shared `grp_brahma_ontology` fingerprint).
2. Rebuild **bg_ontology in the default (unchanged-content) mode**. There is **no expected-change file** for bg_ontology: its rows already moved in step 1, so an expected-change dispatch could never be MET.
3. Rebuild **ga_structural** in the L1 refresh pass **BEFORE the L2 refresh**, so no `dosha_label` fact points at a removed catalog id (`bo_laksana.py:1768` silently drops the link).

**What it does.** Carries the dosha overlay (`citation_pass2_doshas.py`, `l0_doshas.py` hooks and tests, byte-identical to the doshas PR so the two merge cleanly in either order) and adds migration **1325**: bg_ontology's table floor term `COUNT(*) >= 737` becomes `>= 728` (floor 728), the achieved count after the 13 dosha nodes leave: 741 (R4 census total; the live count is not re-read here, the migration is a guarded no-op on a different text) less 13 = 728. Ontology rows are tested by `(entity_class, canonical_id)`: non-dosha classes byte-identical, the 26 undecided dosha rows identical, decided rows carry K1 / K2 / K1_UNVERIFIED text, Punarphoo synonyms, the floor still bites at 727.

**bg_parihara_rules (SS decision 2026-10-05, no reseal).** Shared with the doshas PR (byte-identical): the 14 newly K1-sourced doshas are declared out of the parihara graph (`PARIHARA_K1_SOURCE_CHECK_PENDING`: the K1 source covers the definition, not the cancellation conditions) and K1_ANALOGUE never qualifies, so its row set stays the identical 60 rows (migration 703 untouched). The 27 would-be rows: `ACHARYA/PARIHARA_27_PENDING.tsv`.

**Not in this PR:** the ga_structural change (Exec: `E5.7/KALA_SARPA_VARIANT_REMOVAL_NOTE.md`).
