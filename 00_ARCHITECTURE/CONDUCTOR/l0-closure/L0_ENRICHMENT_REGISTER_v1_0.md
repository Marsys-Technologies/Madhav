---
version: 1.0
status: CURRENT
created: 2026-06-17
branch: fix/l0-closure-integrity
phase: L0 Brahmagyan Closure Pass — Phase 3
---

# L0 Enrichment Register v1.0

## Summary

Phase 3 audited all 22 L0 (bg_*) and supporting brahma_* assets. Gaps identified by reviewing schemas, row counts, and cross-checking against classical classical sources (BPHS, Phaladeepika, Tajika Neelakanthi, Ashtanga Hridayam).

- **Total gaps found**: 6
- **Total built**: 3 (across 3 tables)
- **Total deferred**: 3
- **Rows added**: 47 (33 vedha + 5 tajik yogas + 9 venus transit rules)

---

## Built Gaps

| gap_id | asset | description | rows_added | classical_source | notes |
|--------|-------|-------------|------------|------------------|-------|
| G3-001 | bg_transit_vedha (NEW) | Classical vedha (obstruction) house pairs for all 7 planets' favourable transit results; table did not exist | 33 | BPHS Ch.29; Phaladeepika Ch.26 | vedha_graha=NULL means any transiting planet in the vedha house causes the obstruction; all pairs derived from the explicit vedha_house column already present in bg_transit_rules |
| G3-002 | bg_prashna_tajik_yogas | 5 missing Tajik yogas from the canonical 16: Ikbal (post-station application), Kuttha (severing), Dutthadhuta (malefic trine/square to significator), Tambira (Venus morning star), Durupha (retrograde quesited significator) | 5 | Tajika Neelakanthi Ch.4 | Brought total from 11 to 16 — the complete classical Tajika yoga set |
| G3-003 | bg_transit_rules | Venus gochara phala for houses 4–12 from Moon (only 1,2,3 were present); added 4 favourable + 5 unfavourable | 9 | BPHS Ch.29 | Venus is uniquely favourable in house 8 (unlike other planets); vedha pairs added to bg_transit_vedha correspondingly |

---

## Deferred Gaps

| gap_id | asset | description | reason_deferred | classical_source_if_known |
|--------|-------|-------------|-----------------|---------------------------|
| D3-001 | reference_nakshatra (row 28) | Abhijit nakshatra missing nadi, yoni_en, yoni_sex, body_part, disha | Classical sources (BPHS, Muhurta Chintamani, Jyotish Prabha) do not consistently assign these attributes to Abhijit. It is a supplemental nakshatra covering ~4.27° and its classification in most schemas is incomplete. Fabricating would violate the hard gate. | BPHS mentions Abhijit gana=Deva (already populated); nadi/yoni/body_part not systematically assigned |
| D3-002 | bg_nakshatra_medical | Abhijit (nakshatra 28) absent from body_part medical table | Same as D3-001. No consistent classical assignment in Ashtanga Hridayam or BPHS. | Ashtanga Hridayam covers nakshatras 1-27 systematically |
| D3-003 | bg_transit_rules | Rahu and Ketu transit phala completely absent; only 7 classical planets covered | Node transit phala exists in some appendix traditions of Phaladeepika and in Uttara Kalamrita but is less systematically codified than the 7-planet system. Requires a dedicated sourcing session with high textual fidelity before building. | Phaladeepika appendix chapters; Uttara Kalamrita Ch.5 |
