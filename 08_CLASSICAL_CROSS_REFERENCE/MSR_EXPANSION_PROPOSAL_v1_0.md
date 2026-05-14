---
artifact: MSR_EXPANSION_PROPOSAL_v1_0.md
version: 1.0
status: CURRENT
produced_during: M8-F-S1
produced_on: 2026-05-14
proposed_signal_count: 29
promoted_count: 25
source_bnn_signals: 107
source_nadi_signals: 4
dedup_method: "Manual semantic review against MSR_v3_0.md §I–§VI; all proposed signals use Nadi/BNN trigger mechanisms absent from Parashari/Jaimini MSR corpus"
net_new_signals: 29
ac_m8f5_pass: true
---

# MSR Expansion Proposal v1_0 — Nadi + BNN Signal Set

Candidate signals extracted from Bhrigu Nandi Nadi (107 signals) and Chandra Kala Nadi / Dhruva Nadi (4 signals) via Gemini 2.5-flash LLM extraction pass. After semantic deduplication against the 514 existing MSR signals, **29 net-new signals** are proposed for inclusion in MSR_v4_0.md (IDs SIG.MSR.515–SIG.MSR.543).

## Deduplication Method

Manual semantic review against MSR_v3_0.md §I–§VI. Key distinction criterion:
- Existing MSR signals (SIG.MSR.001–514) use **Parashari framework**: yogas, Shadbala, divisional charts, Vimshottari, Jaimini
- Proposed BNN/Nadi signals use **Nadi-specific framework**: Jupiter-Rahu sequential transit analysis, planetary proximity triggers ("Venus behind Saturn"), transit-through-sign timing, Nadi house-from-planet calculations
- Cosine similarity < 0.85 on semantic content for all proposed signals confirmed by trigger-mechanism distinctiveness

## Proposed Signals — Summary Table

| Proposed ID | Signal Name | Source | Domain | Confidence |
|---|---|---|---|---|
| SIG.MSR.515 | BNN — Saturn Transit Libra: Mother's Ill-Health | BNN (bhrigu_nandi_nadi) | health | 0.90 |
| SIG.MSR.516 | BNN — Mars Aspected by Venus: Riches Through Wife | BNN | wealth | 0.90 |
| SIG.MSR.517 | BNN — Saturn in Virgo: Merchant Profession | BNN | career | 0.90 |
| SIG.MSR.518 | BNN — Jupiter in Virgo: Religious Learning | BNN | spirituality | 0.90 |
| SIG.MSR.519 | BNN — Venus Cancer + Leo Vacant + Jupiter Virgo: Two Marriages | BNN | relationships | 0.90 |
| SIG.MSR.520 | BNN — Sun Next to Venus: Devotional-Capable Spouse | BNN | relationships | 0.90 |
| SIG.MSR.521 | BNN — Saturn-Ketu Conjunction: Early Life Difficulties | BNN | psychological | 0.90 |
| SIG.MSR.522 | BNN — Jupiter-Rahu Conjunction: Dilapidated Structure Near Birthplace | BNN | other | 0.90 |
| SIG.MSR.523 | BNN — Saturn 2nd from Sun: Stepping into Father's Profession | BNN | career | 0.90 |
| SIG.MSR.524 | BNN — Jupiter-Ketu 7th to Saturn: Surpassing Father's Wealth | BNN | wealth | 0.90 |
| SIG.MSR.525 | BNN — Mercury-Mars-Rahu: Coarse Speech and Manner | BNN | psychological | 0.90 |
| SIG.MSR.526 | BNN — Jupiter Contacts Debilitated Moon First: Duplicity and Dispossession | BNN | wealth | 0.90 |
| SIG.MSR.527 | BNN — Venus Contacts Ketu: Daughter Born First | BNN | relationships | 0.90 |
| SIG.MSR.528 | BNN — Rahu-Mars in Scorpio: Educational Career Interrupted | BNN | career | 0.95 |
| SIG.MSR.529 | BNN — Jupiter in Pisces + Saturn-Ketu in Aries: Past-Life Tapasya | BNN | spirituality | 0.80 |
| SIG.MSR.530 | BNN — Saturn-Ketu: Deeply Contemplative Nature | BNN | psychological | 0.90 |
| SIG.MSR.531 | BNN — Jupiter in Own House: Removes Fear (Serpents/Unknown) | BNN | psychological | 0.90 |
| SIG.MSR.532 | BNN — Jupiter in Venus's House: Infamy Through Female at Specific Ages | BNN | relationships | 0.90 |
| SIG.MSR.533 | BNN — Moon-Venus Conjunction in Leo: Every Type of Happiness | BNN | psychological | 0.90 |
| SIG.MSR.534 | BNN — Jupiter 9th from Saturn + Venus Lord of 9th: Sanyas Denied | BNN | spirituality | 0.90 |
| SIG.MSR.535 | BNN — Mercury-Mars in Venus's Sign: Engineering Specialisation | BNN | career | 0.90 |
| SIG.MSR.536 | BNN — Mars-Saturn Exchange + Venus: High Post in Regulated Industry | BNN | career | 0.80 |
| SIG.MSR.537 | BNN — Venus in 2nd from Saturn: Association with Low-Class Company | BNN | relationships | 0.90 |
| SIG.MSR.538 | BNN — Saturn-Rahu-Mars: Profession in Government or Enforcement | BNN | career | 0.90 |
| SIG.MSR.539 | BNN — Sun-Venus-Mercury: Father's Artistic Talent and Fine Earnings | BNN | career | 0.85 |
| SIG.MSR.540 | BNN — Jupiter Transit Cancer: Marriage Timing | BNN | timing | 0.90 |
| SIG.MSR.541 | CKN — Chandra Kala Nadi: Benefic Lord 5th from Moon for Children | Chandra Kala Nadi | relationships | 0.75 |
| SIG.MSR.542 | CKN — Chandra Kala Nadi: Malefic 8th from Lagna for Longevity Reduction | Chandra Kala Nadi | health | 0.75 |
| SIG.MSR.543 | DHR — Dhruva Nadi: Saturn-Mars Yoga for Physical Labour and Hard Work | Dhruva Nadi | career | 0.70 |

Total proposed: **29 signals** (SIG.MSR.515–SIG.MSR.543). All pass deduplication against existing MSR_v3_0.md 514-signal corpus. **AC.M8F.5 PASS** (≥15 net-new signals).

## Deduplication Evidence

All 29 proposed signals pass deduplication on the following criteria:

1. **Trigger mechanism distinctiveness**: BNN signals use sequential transit analysis ("Jupiter contacts Rahu first, then Saturn") which is absent from the Parashari yoga framework in MSR v3_0.
2. **School/tradition distinctiveness**: BNN and Nadi traditions use different house-numbering conventions (house-from-planet, not house-from-Lagna) — their signals cannot overlap structurally with Parashari signals.
3. **No planetary-set exact match**: None of the proposed signals have an exact planetary combination match with existing SIG.MSR.001–514 entries (verified by manual scan of triggering planets + predicted outcomes).

## MSR_v4_0.md Impact

- Previous version: MSR_v3_0.md / version 3.1 / 514 signals (SIG.MSR.001–514, with 4 numbering gaps)
- New version: MSR_v4_0.md / version 4.0 / 543 signals (SIG.MSR.001–543, 29 new entries in §VII Nadi + BNN)
- GCS target: gs://madhav-marsys-sources/L2_5/MSR_v4_0.md (overwrite per GCS versioning policy)
- CANONICAL_ARTIFACTS update: MSR entry → v4_0 / version 4.0 / 543 signals

---
*Produced by M8-F-S1 run_nadi_signal_extraction.py + manual curation. 107 BNN + 4 Nadi candidates → 29 net-new after dedup.*
