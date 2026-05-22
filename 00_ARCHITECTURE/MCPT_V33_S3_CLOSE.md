---
artifact: MCPT_V33_S3_CLOSE.md
version: 1.0
status: CLOSED
project: MCP Transformation
session_id: v3.3-S3
worktree: E (MadhavMCPT-DPT)
branch: feature/mcpt-depth
closed_at: '2026-05-22'
---

# v3.3-S3 Sealing Artifact — Varshphal Chart Facts Ingestion

## Result: PASS

All acceptance criteria met. 1566 rows inserted into `chart_facts` WHERE `category='varshphal'`.
38 unit tests pass. DB verified. B.10 discipline upheld for all non-deterministic subkeys.

---

## Row Counts

| Subkey pattern | Count | AC | Status |
|---|---|---|---|
| `VPH.*.MUNTHA` | 87 | computed | PASS |
| `VPH.*.MUNTHA_HOUSE` | 87 | computed | PASS |
| `VPH.*.VARSHA_NUMBER` | 87 | computed | PASS |
| `VPH.*.YEAR_LORD` | 87 | B.10 placeholder | PASS |
| `VPH.*.ANNUAL_LAGNA` | 87 | B.10 placeholder | PASS |
| `VPH.*.SAHAM.*` (12 types) | 1044 | B.10 placeholder | PASS |
| `VPH.*.PANCHA_VARGIYA_BALA` | 87 | B.10 placeholder | PASS |
| **TOTAL** | **1566** | **AC.S3.1 ≥ 1500** | **PASS** |

---

## Spot-Check: 1984 (Varsha 1)

All 18 rows verified in DB:

```
VPH.1984.ANNUAL_LAGNA        → [EXTERNAL_COMPUTATION_REQUIRED]
VPH.1984.MUNTHA              → Cancer   ← COMPUTED (natal lagna)
VPH.1984.MUNTHA_HOUSE        → 1        ← COMPUTED (H1 from Cancer lagna)
VPH.1984.PANCHA_VARGIYA_BALA → [EXTERNAL_COMPUTATION_REQUIRED]
VPH.1984.SAHAM.AASHA         → [EXTERNAL_COMPUTATION_REQUIRED]
VPH.1984.SAHAM.BADHAKA       → [EXTERNAL_COMPUTATION_REQUIRED]
VPH.1984.SAHAM.KALI          → [EXTERNAL_COMPUTATION_REQUIRED]
VPH.1984.SAHAM.KAMA          → [EXTERNAL_COMPUTATION_REQUIRED]
VPH.1984.SAHAM.KARMA         → [EXTERNAL_COMPUTATION_REQUIRED]
VPH.1984.SAHAM.MAHATMYA      → [EXTERNAL_COMPUTATION_REQUIRED]
VPH.1984.SAHAM.MITRA         → [EXTERNAL_COMPUTATION_REQUIRED]
VPH.1984.SAHAM.PUNYA         → [EXTERNAL_COMPUTATION_REQUIRED]
VPH.1984.SAHAM.SAMEERA       → [EXTERNAL_COMPUTATION_REQUIRED]
VPH.1984.SAHAM.SHREE         → [EXTERNAL_COMPUTATION_REQUIRED]
VPH.1984.SAHAM.VIDYA         → [EXTERNAL_COMPUTATION_REQUIRED]
VPH.1984.SAHAM.YASAS         → [EXTERNAL_COMPUTATION_REQUIRED]
VPH.1984.VARSHA_NUMBER       → 1        ← COMPUTED
VPH.1984.YEAR_LORD           → [EXTERNAL_COMPUTATION_REQUIRED]
```

---

## 12-Year Cycle Verification (muntha)

```
1984 → Cancer  (Varsha  1) ✓
1985 → Leo     (Varsha  2) ✓
1986 → Virgo   (Varsha  3) ✓
1995 → Gemini  (Varsha 12) ✓
1996 → Cancer  (Varsha 13) ✓  ← 12-year cycle resets
2008 → Cancer  (Varsha 25) ✓
2070 → Virgo   (Varsha 87) ✓  (87 mod 12 = 3 → index 3+2=5=Virgo)
```

---

## Compute Mode Summary

| Subkey | Compute status | Rule / Source |
|---|---|---|
| `muntha` | COMPUTED (deterministic) | Tajaka Neelakanthi ch.2 — muntha advances 1 sign/year from natal lagna |
| `muntha_house` | COMPUTED (deterministic) | Derived from muntha_sign relative to natal lagna (Cancer = H1) |
| `varsha_number` | COMPUTED (trivial) | `year - 1984 + 1` |
| `year_lord` | [EXTERNAL_COMPUTATION_REQUIRED] | Needs weekday of solar return → varshapati per Tajaka ch.3 |
| `annual_lagna` | [EXTERNAL_COMPUTATION_REQUIRED] | Needs exact time of solar return → lagna at that moment |
| `saham.*` (12 types) | [EXTERNAL_COMPUTATION_REQUIRED] | Each saham formula needs full annual chart positions |
| `pancha_vargiya_bala` | [EXTERNAL_COMPUTATION_REQUIRED] | D1/D2/D3/D9/D12 of annual chart needed |

Required software: Jagannatha Hora / Parashara's Light / Shri Jyoti Star — compute solar return for each of 87 years, extract subkeys.

---

## Files Committed

- `platform/scripts/bootstrap/bootstrap_chart_facts_varshphal.ts` — bootstrap script (exports `buildAllRows`, `getMunthaSign`, `getMunthaHouse`, `getVarshaNumber`, constants)
- `platform/test/bootstrap/chart_facts_varshphal.test.ts` — 38 unit tests (all PASS)
- `00_ARCHITECTURE/MCPT_V33_S3_CLOSE.md` — this sealing artifact

---

## Tests

38 tests, 38 PASS, 0 FAIL.

Coverage:
- Row count ≥ 1500 (AC.S3.1) ✓
- 18 distinct subkeys per year ✓
- muntha 1984 = Cancer ✓
- muntha 1985 = Leo ✓
- muntha 1986 = Virgo ✓
- muntha 1996 = Cancer (12-year cycle) ✓
- All years 1984–2070 represented ✓
- muntha_house for lagna-year = 1 ✓
- varsha_number 1984 = 1, 2070 = 87 ✓
- year_lord rows exist for all years ✓
- saham.punya rows exist for all years ✓
- EXTERNAL_COMPUTATION_REQUIRED discipline exact marker ✓
- muntha rows NOT marked as EXTERNAL_COMPUTATION_REQUIRED ✓
- fact_id format `VPH.<year>.<SUBKEY>` ✓
- No duplicate fact_ids ✓
- category = varshphal ✓
- divisional_chart = D1 ✓
- Provenance structure complete ✓
- All 12 saham subkeys present for 1984 ✓
- PANCHA_VARGIYA_BALA rows for all years ✓

---

## DB Verification

```sql
SELECT count(*) FROM chart_facts WHERE category='varshphal';
→ 1566

SELECT count(*) FROM chart_facts WHERE category='varshphal' AND is_stale=false;
→ 1566 (AC.S3.1 PASS)
```

build_manifests row: `mcpt-v33-s3-varshphal-20260522` → status=live ✓

---

## Residuals

- `year_lord`, `annual_lagna`, all 12 `saham.*` types, `pancha_vargiya_bala` for all 87 years:
  total 1305 rows marked [EXTERNAL_COMPUTATION_REQUIRED]. Resolution requires solar return
  calculations in Jagannatha Hora or equivalent for each of years 1984–2070 against the native's
  birth data (1984-02-05, 10:43 IST, Bhubaneswar). This is operator-runnable post-session work;
  the placeholders ensure the row schema is correct and query_chart_facts surfaces the gap explicitly
  rather than silently.

- No code regressions. Pre-existing test failures unchanged (see KNOWN_PRE_EXISTING_FAILURES.md).
