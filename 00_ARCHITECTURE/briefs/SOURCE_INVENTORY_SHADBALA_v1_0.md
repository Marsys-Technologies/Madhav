---
artifact: SOURCE_INVENTORY_SHADBALA_v1_0
version: 1.0
status: CURRENT
session_id: v3.3-S1
created: 2026-05-22
---

# Source Inventory — Shadbala + Ashtakavarga (v3.3-S1)

Documents the authoritative L1 sources used to populate `chart_facts` categories `shadbala`, `ashtakavarga_sav`, and `ashtakavarga_bav` in session v3.3-S1.

## Mode

`--mode=compute` — values extracted directly from FORENSIC L1 source (no Jagannatha Hora CSV import). JH export not available in Wave 0.

## Primary source

**`01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md`** (canonical_id: FORENSIC, status: CURRENT)

| Section | Content | Categories populated |
|---------|---------|----------------------|
| §6.1 | Shadbala component totals per planet (Uccha, Sthana, Dig, Kala, Chesta, Naisargika, Drik) | `shadbala` |
| §6.2 | Shadbala totals in virupa and rupa per planet | `shadbala` |
| §6.4 | Bhava Bala totals per house | `bhava_bala` (pre-existing) |
| §7.1 | Ashtakavarga BAV bindu grid — 7 planets × 12 signs | `ashtakavarga_bav` |
| §7.2 | Sarvashtakavarga (SAV) — 12 signs, FORENSIC canonical values | `ashtakavarga_sav` |
| §7.3 | Shuddha Pinda (Rasi Pinda, Graha Pinda, Shuddha Pinda) | `ashtakavarga_bav` |

## Provenance notes

- **SAV discrepancies**: Libra H7 = 33 (FORENSIC) vs 34 (JH export); Scorpio H8 = 33 (FORENSIC) vs 32 (JH); Capricorn H10 = 26 (FORENSIC) vs 27 (JH). FORENSIC canonical values used per B.10 (no fabricated computation; FORENSIC is L1 authority).
- **Shadbala totals**: FORENSIC §6.2 virupa totals used. JH rupas differ slightly (Saturn JH=8.79 vs FORENSIC=7.47 rupa); FORENSIC values stored with `TOTAL_VP` / `TOTAL_RP` suffixes — JH rupas can be added as `TOTAL_RP_JH` rows in a future session if needed.
- **Uccha Bala**: Stored as a standalone row (`SBL.*.UCCHA`) — it is a sub-component of Sthana Bala, not additive on top of it.

## Build identifier

`mcpt-v33-s1-chart-facts-20260522` — shared across all three v3.3-S1 ingestions.
