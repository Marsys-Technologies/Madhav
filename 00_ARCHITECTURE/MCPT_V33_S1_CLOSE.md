---
artifact: MCPT_V33_S1_CLOSE
version: 1.0
status: COMPLETE
session_id: v3.3-S1
closed_at: 2026-05-22
worktree: MadhavMCPT-FIN (executing on feature/mcpt-final per cross-worktree merge posture)
---

# v3.3-S1 Close — Shadbala + Ashtakavarga + Bhava Bala Ingestion

## Acceptance criteria

| AC | Check | Result |
|----|-------|--------|
| AC.S1.1 | `chart_facts WHERE category='shadbala'` ≥ 63 | **63** ✓ PASS |
| AC.S1.2 | `chart_facts WHERE category='ashtakavarga_sav'` = 12 | **12** ✓ PASS |
| AC.S1.3 | `chart_facts WHERE category='ashtakavarga_bav'` ≥ 100 | **105** ✓ PASS |
| AC.S1.4 | `chart_facts WHERE category='bhava_bala'` ≥ 12 | **12** ✓ PASS (pre-existing) |
| AC.S1.5 | `build_manifests` entry present | `mcpt-v33-s1-chart-facts-20260522` status=live ✓ PASS |
| Tests | `vitest run test/bootstrap/` | **29/29 PASS** |

## Pre/post row counts

| Category | Pre-v3.3-S1 | Post-v3.3-S1 |
|----------|-------------|--------------|
| shadbala | 0 | 63 |
| ashtakavarga_sav | 0 | 12 |
| ashtakavarga_bav | 0 | 105 |
| bhava_bala | 12 | 12 (unchanged — pre-existing) |

## Spot-check: FORENSIC value fidelity

- **Saturn Uccha Bala** — `SBL.FORENSIC.SATURN.UCCHA` = **59.18 virupa** (FORENSIC §6.1 ✓)
- **Moon Pisces BAV** — `BAV.FORENSIC.MOON.PI` = **6 bindus** (FORENSIC §7.1 ✓)
- **Mars Shuddha Pinda** — `BAV.FORENSIC.MARS.PINDA_SHUDDHA` = **198** (rank 1, FORENSIC §7.3 ✓)
- **SAV total** — sum(SAV_BINDUS) = **337** (FORENSIC §7.2 ✓)

## Scripts delivered

- `platform/scripts/bootstrap/bootstrap_chart_facts_shadbala.ts`
- `platform/scripts/bootstrap/bootstrap_chart_facts_ashtakavarga.ts`
- `platform/scripts/bootstrap/bootstrap_chart_facts_bhava_bala.ts`

## Tests delivered

- `platform/test/bootstrap/chart_facts_shadbala.test.ts` (10 assertions)
- `platform/test/bootstrap/chart_facts_ashtakavarga.test.ts` (12 assertions)
- `platform/test/bootstrap/chart_facts_bhava_bala.test.ts` (7 assertions)

## Source inventory

`00_ARCHITECTURE/BRIEFS/SOURCE_INVENTORY_SHADBALA_v1_0.md` — documents FORENSIC §6.1/§6.2/§7.1/§7.2/§7.3 as L1 authority; notes SAV discrepancies vs JH export.

## Execution mode

`--mode=compute` — values extracted from FORENSIC L1 source (JH export unavailable in Wave 0).

## Build manifest

`mcpt-v33-s1-chart-facts-20260522` — status=live; notes: "MCPT v3.3-S1: Shadbala + Ashtakavarga direct ingest from FORENSIC §6.1/§6.2/§7.1/§7.2/§7.3"

## Residuals / open items

- AC.S1.6 (`data_coverage` ≥0.95 for shadbala) is a downstream check gated on v3.1.0-S4 merge to final — not testable in this session.
- JH rupa totals differ from FORENSIC §6.2 rupas for Saturn (JH=8.79 vs FORENSIC=7.47). JH values can be added as `TOTAL_RP_JH` rows if needed by a downstream query.
- The brief's gate command references `WHERE asset_id='chart_facts'` in build_manifests — this column does not exist in the actual schema. Build manifest entry verified by `build_id` directly.
