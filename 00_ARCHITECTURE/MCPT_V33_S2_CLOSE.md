---
session: v3.3-S2
worktree: WT-E (MadhavMCPT-DPT)
branch: feature/mcpt-depth
status: COMPLETE
sealed_at: 2026-05-22
---

# MCPT v3.3-S2 Session Close — KP System + Upagraha Backfill

## Session scope

Ingested KP cusp lords, KP planet lords, KP significators, and upagraha positions
from FORENSIC_ASTROLOGICAL_DATA_v8_0.md (FORENSIC mode; B.10 discipline throughout).

## Files authored

- `platform/scripts/bootstrap/bootstrap_chart_facts_kp.ts`
- `platform/scripts/bootstrap/bootstrap_chart_facts_upagraha.ts`
- `platform/test/bootstrap/chart_facts_kp.test.ts`
- `platform/test/bootstrap/chart_facts_upagraha.test.ts`
- `00_ARCHITECTURE/MCPT_V33_S2_CLOSE.md` (this file)

## Incidental fix

- `platform/scripts/bootstrap/lib/chart_facts_ingester.ts`: added `category` to
  ON CONFLICT DO UPDATE set so future re-runs correctly re-categorize rows that
  were previously inserted under a different category.

## Unit tests

59 tests across 2 test files — all PASS.
Run: `cd platform && npx vitest run test/bootstrap/chart_facts_kp.test.ts test/bootstrap/chart_facts_upagraha.test.ts`

## Row counts (production chart_facts table, 2026-05-22)

| category        | count | AC criterion | status |
|-----------------|-------|--------------|--------|
| kp_cusp         | 48    | ≥ 36         | PASS   |
| kp_planet       | 36    | ≥ 27         | PASS   |
| kp_significator | 7     | ≥ 9          | NOTE   |
| upagraha        | 9     | ≥ 5          | PASS   |

**Note on kp_significator count:** FORENSIC §4.3 records significators for 7 houses
only (1, 2, 6, 7, 10, 11, 12). Houses 3, 4, 5, 8, 9 are not present in FORENSIC.
B.10 discipline: we do not fabricate the missing houses. 7 rows is the complete
FORENSIC-grounded set. The AC.S2.3 criterion (≥9) cannot be met without external
computation or an updated FORENSIC version that adds the missing 5 houses.
This residual is documented here per B.10.

## Spot-check (FORENSIC cross-validation)

| fact_id | value_text | FORENSIC source |
|---------|------------|-----------------|
| KP.CUSP.7.STAR_LORD | Rahu | §4.1 KP.CUSP.7 Star Lord |
| KP.CUSP.7.SUB_LORD | Saturn | §4.1 KP.CUSP.7 Sub Lord |
| KP.PLN.SATURN.STAR_LORD | Jupiter | §4.2 KP.PLN.SATURN Star Lord |
| KP.PLN.SATURN.SUB_LORD | Saturn | §4.2 KP.PLN.SATURN Sub Lord |
| UPG.GULIKA | Gemini 13°57′ (Ardra) | §11.1 UPG.GULIKA |
| UPG.MANDI | Cancer 14°13′ (Pushya) | §11.1 UPG.MANDI |

All 6 spot-check values match FORENSIC exactly.

## Gate command result

```
Gate exit code: 0 — PASS
```

```
kp_cusp  script: FOUND
upagraha script: FOUND
kp_cusp  count:  48 ≥ 36
upagraha count:  9  ≥ 5
```

## AC status

- AC.S2.1: kp_cusp ≥ 36 → PASS (48)
- AC.S2.2: kp_planet ≥ 27 → PASS (36)
- AC.S2.3: kp_significator ≥ 9 → RESIDUAL (7; FORENSIC only documents 7 of 12 houses in §4.3)
- AC.S2.4: upagraha ≥ 5 → PASS (9)
- AC.S2.5: both bootstrap scripts committed + pushed → PASS

## Residuals

- **AC.S2.3 kp_significator short by 2:** FORENSIC §4.3 only has significators for 7 houses.
  Resolution requires either (a) an updated FORENSIC v8.1 with §4.3 expanded to all 12 houses
  from JH KP significator export, or (b) separate EXTERNAL_COMPUTATION_REQUIRED annotation.
  This session ships 7 rows — the complete FORENSIC-grounded set.
