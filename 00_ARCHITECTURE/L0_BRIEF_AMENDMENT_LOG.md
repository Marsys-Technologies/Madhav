---
artifact: L0_BRIEF_AMENDMENT_LOG
canonical_id: L0_BRIEF_AMENDMENT_LOG
version: 1.0
status: CURRENT
authored_by: Racayitā (Build-Guarantor Swarm gap-author) 2026-06-08
remediates: 00_ARCHITECTURE/L0_BRAHMAGYAN_CAMPAIGN_EVALUATION_REPORT_v1_0.md (§2/§4 findings)
branch: plan/l0-brief-amendments
baseline_commit: 035f0e63
scope: briefs-only (00_ARCHITECTURE/BRIEFS/*.md + master plan §-touches); ZERO platform/ changes
---

# L0 Brahmagyan — Brief Amendment Log (Racayitā gap-author pass)

Per-brief record of the gap-author amendments that make each brief deterministically reach its (HELD) floor without fabrication, per the Build-Guarantor Swarm Charter. **Floors were HELD, never lowered.** Where a closed set's honest maximum falls below floor, the structured-extraction bucket carries the remainder with explicit yield arithmetic + a fail-closed REJECT, and the gap is surfaced to native (HARD STOP) — never padded.

## §1 — Per-brief before → after

| Doc | Brief | Floor | inline_before | inline_after | §3a achievement | Status |
|---|---|---|---|---|---|---|
| 11 | bg_yogas | 250 | **25** | **81** (PMP 5, lunar/solar 6, all 32 Nabhasa, named 19, raja 8, dhana 5, sannyasa/aristha 6) | 81 inline + ~20 templated (SARAVALI_YOGA_LOOKUP) + structured-extraction | **HARD STOP to native** — 250 not brief-provable (max ≈101); needs acharya lookup-completion pass; floor HELD, FAIL-CLOSED |
| 13 | bg_doshas | 50 | **18** | **50** (13 core + 12 Kala Sarpa variants + 8 Ashtakoota + 5 arishta + 12 more) | 50 inline + 0 + 0 = 50 | **MET inline.** classical_tradition cite policy flagged (native ratified 2026-06-08) |
| 9 | bg_remedies | 800 | Saturn cell only | full 9-graha `PLANET_REMEDY_DATA` + `gen_planet_matrix()` (~200) | ~200 generated + ~100 dosha-linked + ≥500 auto-live sweep = **≥800 LIVE** | **Accounting DEFECT FIXED** (auto-promote unambiguous sweep → live); REMEDY_TYPE_MAP authored inline |
| 4 | bg_reference | 1,450 / 1,225 own | ~73 | ~588 inline (incl. 77 karakas, ~365 glossary) + ~650 generated (constants w/ bindu tables, topic_tags) | ≥1,238 → ~1,450 | Content embeds authored in a prior pass; **§3a added**; mig 182 |
| 5 | bg_ontology | 380 own / 700 full | ~59 new | 121 inline + 77 karaka-generated-from-Doc4 + ≥190 domain/concept | ≥388 own | **2 arbiter-DESCRIPTION errors fixed** (live writer is composite); §3a; mig 183 |
| 8 | bg_rules | 3,000 | 1,213 existing | pattern library (infra; ~50 templates) | 1,213 + ≥1,800 projected = ≥3,000 | **EMERGENT + HARD STOP** (reject-not-pad if pattern coverage underperforms); mig 188 |
| 12 | bg_dasha_systems | 15 | **18** | 18 | 18 ≥ 15 | **MET inline** (exemplary); arbiter confirmed; §3a; mig 185 |
| 6 | bg_texts | 14,000 | n/a (PDFs) | n/a | ≥14,000 projected | **EMERGENT**; CONDITIONAL on 3 manual-upload PDFs (hard operator prereq) |
| 7 | bg_text_index | 400 | n/a (classifier) | n/a | ≥400 distinct tags projected | **EMERGENT** on corpus; CONDITIONAL; mig 187 |
| 10 | bg_concordance | 800 | n/a (aggregation) | n/a | ≥800 topic×school projected | **EMERGENT** on corpus; CONDITIONAL; mig 190 |
| 14 | bg_compendium_index | 3,000 | n/a (aggregation) | n/a | ≥3,000 projected | **EMERGENT** on corpus/topic_tags; CONDITIONAL; mig 191 |
| 2 | orchestrator-fixes | N/A | — | — | — | (no content amend; mig 181 pre-existing) |
| 3 | bg_ephemeris | 825,084 | n/a (algorithmic) | n/a | already populated | (no amend) |
| 15 | integration/Ω | N/A | — | — | FLOORS dict HELD (matches all above) | migration-band note added |

## §2 — Cross-cutting fixes applied

1. **brahma_ontology ON CONFLICT arbiter** — the live `l0_ontology.py` uses `ON CONFLICT (entity_class, canonical_id) DO NOTHING` (composite). Fixed every ontology insert/contract in **Docs 5, 11, 12, 13** (was wrongly `(canonical_id)`); Doc 5 also had two prose mis-descriptions of the live arbiter — corrected. Catalog/pointer inserts correctly retain their `canonical_id` PK arbiter.
2. **Migration band 181–191 pre-assigned** (eval §4.7): 181=orchestrator (pre-existing), 182=reference, 183=ontology, 184=yogas, 185=dasha_systems, 186=doshas, 187=text_index, 188=rules, 189=remedies, 190=concordance, 191=compendium. ⚠ **Collision flag:** eval §3.2 noted other concurrent workstreams (`CLAUDECODE_BRIEF_BRAHMA_INFRA_PROVISIONING`=187, `CLAUDECODE_BRIEF_BRANCH_SWEEP`=188) claim 187/188. **Native must deconflict** at single-PR time — none are applied yet (live ceiling = 180); renumber sequentially from the true ceiling if the band has shifted.
3. **§3a Floor Achievement Arithmetic** added to all 12 asset briefs with three provable buckets (closed_set_inline / deterministic_generated / structured_extraction) summing ≥ floor, each bucket independently verifiable.
4. **Doc 9 live-vs-review accounting** — the eval §2.11 defect (sweep rows in `review` leaving <800 `live`) fixed: unambiguous sweep matches auto-promote to `live`; only ambiguous → `review` (non-floor-counted).

## §3 — HARD STOPs surfaced to native (require a decision)

1. **Doc 11 (yogas) — lookup completion.** 250 structured yogas is NOT reachable from embedded data alone (brief-provable max ≈ 101: 81 inline + ~20 templated). Authoring 170 accurate Saravali/BPHS formation templates exceeds a gap-author pass without fabrication. **Native: (a)** commission an acharya pass to complete `SARAVALI_YOGA_LOOKUP` to ≥169 verified templates (recommended — names are in the Saravali corpus), or **(b)** accept corpus-verse-defined formation for the residual. Floor HELD; writer FAIL-CLOSED (REJECTs below 250).
2. **Citation policy** — Docs 13/11/9 carry `classical_tradition` on genuinely tradition-rooted rows (Kala Sarpa variants, compatibility kootas, etc.). Doc 4 references a **native-ratified policy (2026-06-08)** accepting this. The other briefs are aligned to that ratification; if it is NOT in force, re-cite the affected rows post-ingest via structured extraction.
3. **3 manual-upload PDFs** (Tajaka Neelakanthi, Yavana Jataka, Bhrigu Samhita) — hard operator prerequisite for the corpus-emergent floors (Docs 6/7/8/10/14). Briefs CONDITIONAL-gate this.

## §4 — Commits on this branch

- `035f0e63` baseline (briefs as authored + eval report)
- `19a2070c` Doc 11 (yogas)
- `1f968f01` Doc 13 (doshas)
- `2fb33164` Doc 9 (remedies)
- `2bb90162` Docs 4/5/6/7/8/10/12/14 (§3a + migrations + arbiter-desc)
- (this log + Doc 15 note: final commit)

## §5 — Resume pass (Task A + Task B, 2026-06-08)

**Task A — Doc 11 yoga residual (v1.2).** Native decided the ~149 residual to floor 250 is closed by **corpus-verse structured extraction** (§3.9b), NOT an acharya pass and NOT fabrication. Each residual row = a verbatim Saravali/BPHS/Phaladeepika verse clause (`formation_rule_jsonb.requires[0].raw_verse_clause`) + `source_chunk_ids` citation — structurally complete, floor-eligible, never a placeholder. §3a now reads 81 inline + ~20 templated + ≥149 corpus_verse = ≥250. Saravali confirmed auto-ingested (`manual_upload:False`). Writer FAIL-CLOSED (REJECT + report if <250 distinct after all yoga chunks). Commit `233f2339`.

**Task B — FULL swarm audit (all 12 asset briefs).** Closed the prior pass's non-uniform-coverage gap: every brief (Docs 3-14) audited by COUNT + CITATION + SCHEMA sub-agents + Sambandha cross-brief. Result + REJECT→fix log in `00_ARCHITECTURE/L0_SWARM_AUDIT_v1_0.md`. 4 REJECTs found and remediated (all re-audited APPROVE): R1 Doc 3 SCHEMA (hardcoded 825,084 → import VOLUME_FLOOR + engine/campaign HARD STOP), R2 Doc 4 COUNT (per-table floor estimates 35/30 → physical 33/19), R3 Doc 9 COUNT (gen yield 72 → real 108), R4 Doc 9 SCHEMA (REMEDY_TYPE_MAP +dietary). Doc 4's glossary 364 / constants 203 / karakas 77 / topic_tags 481 independently counted + PASS (the native's specific concern). Sambandha APPROVE. Commits `637cedac` (remediations) + audit log.

**NEW HARD STOP for native:** Doc 3 ephemeris — live engine `VOLUME_FLOOR=29,200` / 1980-2060 / tropical contradicts campaign `825,084` / 1900-2150 / Lahiri. Surfaced in Doc 3 §0 + L0_SWARM_AUDIT §3.1. Floor held; native must resolve.

*End of L0 Brief Amendment Log v1.0 (resume pass appended 2026-06-08).*
