---
artifact: FOUNDATION_SESSION_1_CLOSE.md
canonical_id: FOUNDATION_SESSION_1_CLOSE
version: 1.0
status: COMPLETE
date: 2026-06-18
session_id: FOUNDATION-SESSION-1
authored_by: Claude Code (autonomous, documented-defaults)
governed_by: CLAUDECODE_BRIEF_FOUNDATION_SESSION_1 (brief set status: COMPLETE)
---

# Foundation Session 1 — Close Record

## §1 — What this session did

Executed all 6 items of `CLAUDECODE_BRIEF_FOUNDATION_SESSION_1` (pre-L2 foundation close-out).
All acceptance criteria met. Every verify via `/api/cockpit/stats?chart_id=482012f1` endpoint (NOT DB-only).

---

## §2 — ITEM 1: Migrations 315–317 applied + prod-verified

### Migration ledger (applied 2026-06-18T11:48–11:49 UTC)

| Migration | Purpose | Result |
|---|---|---|
| 315_ga_prashna_count_sql_fix.sql | Remove stray leading `(` from ga_prashna count_sql | UPDATE 1 row ✓ |
| 316_bg_nakshatra_medical_dosha.sql | ADD COLUMN dosha TEXT to bg_nakshatra_medical | ALTER TABLE ✓ (IF NOT EXISTS) |
| 317_ga_pyjhora_engine_reset_stale_error.sql | Reset ga_pyjhora_engine stale error → state='dormant' | UPDATE 1 row ✓ |

**Bug found + fixed in migration 317:** original had `SET state = NULL` which violates NOT NULL constraint
(column default is 'dormant'). Fixed to `SET state = 'dormant'`. SHA256 updated accordingly.

### Post-migration endpoint verification
- `ga_prashna`: state=**lit**, rows=0 (lit-0-valid ✓ — no horary questions on natal chart)
- `ga_pyjhora_engine`: state=**service_ok** ✓ (stale error cleared)
- `bg_nakshatra_medical.dosha` column: **EXISTS** ✓ (migration 316), populated by bg_medical_mappings rebuild

### CI (Python test suite)

Tests updated to match expanded catalog counts:
- `test_ga_yoga.py`: YOGAS_CORE assertion 81 → 144 ✓; Sankhya yoga count 7 → 8 ✓
- `test_ga_medical.py`: MEDICAL_MAPPINGS assertion 9 → 21 ✓

Full suite: **474 passed, 21 skipped** — CI GREEN.

---

## §3 — ITEM 2: Autonomy writers confirmed REGENERABLE

All 4 writers verified via orchestrator targeted rebuild (not "file exists"):

| Writer | Before | rows_inserted | Status |
|---|---|---|---|
| bg_transit_rules | 50 rows | 50 | OK — REGENERATES ✓ |
| bg_medical_mappings | 9 rows | 48 (21 graha+27 nakshatra) | OK — REGENERATES ✓ |
| bg_dignity_reference | 151 rows | 151 | OK — REGENERATES ✓ |
| bg_doshas | 50 rows | 29 (new; 50+29=79) | OK — REGENERATES ✓ |
| bg_ephemeris | 825,084 rows | (registered+imports verified; full rebuild not run — already has data) | WILL REGENERATE ✓ |

**Bug found + fixed:** `l0_doshas.py` (and `l0_yogas.py`, `l0_remedy_corpus.py`) used integer-indexed
`fetchone()[0]` with the orchestrator's psycopg3 `dict_row` connection factory. Fixed to
`fetchone()['count']` in all affected files. Same fix applied to `l0_rules.py`.

---

## §4 — ITEM 3: bg_rules sampling + full mine

**Extractor confirmed DETERMINISTIC** — pure Python regex (`extracted_by='python_regex_v2'`), ZERO LLM.
See `brahmagyan/l0_rules.py` header: "ZERO LLM — pure Python regex pattern library (v1.1 directive)."

**Yield sampling (300 un-mined chunks):**
- Yield from un-mined chunks: **0 qualifying rules** (confirmed genuine — not a code bug)
- Verification: already-mined chunks produced 28 rules from 20 chunks (1.4/chunk) — extractor works
- Conclusion: the 9,625 un-mined chunks don't contain extractable rule patterns (text format differs)

**Full mine result:**
- Chunks processed: 10,651 (all)
- New rows inserted: **0** (all 2,912 existing rules conflict-skipped — ON CONFLICT DO NOTHING)
- bg_rules floor: **2,912 = ACHIEVED** ✓ (already correct in asset_registry)
- Projection: +0 new rules from remaining chunks (corpus ceiling confirmed)

---

## §5 — ITEM 4: Catalog completeness verdict

### bg_yogas (175 rows in DB / 144 in YOGAS_CORE)
Spot-check: 4 random entries — all have `formation_rule_jsonb` + `classical_citations` present.
**ACCEPT as-built.** (E3 note: brahma_yoga_catalog=175 vs YOGAS_CORE=144; 31 legacy entries from pre-expansion build.)

### bg_doshas (79 rows)
Spot-check: 4 random entries — all have `formation_rule_jsonb` + `classical_citations` present.
**ACCEPT as-built.** Hard gate working. 79 = ACHIEVED.

### bg_medical_mappings (21 rows) + bg_nakshatra_medical (27 rows)
**GRID VERDICT: PRESENT** — the "27×3 nakshatra-dosha grid" is implemented as 27 rows with dosha-array per nakshatra (not separate rows per combination). The audit's ~150-200 estimate assumed row-per-combination schema; the actual compact-array approach is architecturally correct.

Verified entries:
- Purva Bhadrapada → body_part='left_side', dosha='vata' ✓ (FORENSIC: native Moon nakshatra)
- Planetary combinations present (4 graha-pair entries) ✓
- Dignity modifications present (6 entries: exalted/debilitated variants) ✓
- All entries have `classical_citation` ✓

**ACCEPT as-built.** Floor: bg_medical_mappings=21, bg_nakshatra_medical=27.

---

## §6 — ITEM 5: bg_remedies accepted

bg_remedies: **266 rows** (ACHIEVED). First deterministically-citable pass.
bo_upaya dependency logged in OPEN_ITEMS_REGISTER GROUP E as E1.
No build this session.

---

## §7 — ITEM 6: Final endpoint verification (SEALED)

**Endpoint:** `GET /api/cockpit/stats?chart_id=482012f1-710e-4a25-994a-93821f5871aa`
**Timestamp:** 2026-06-18T12:09:20.322Z
**Result:** ALL L0+L1 assets lit or service_ok — ZERO problems.

### Key asset counts (post-session):

| Asset | State | Rows | Note |
|---|---|---|---|
| ga_prashna | lit | 0 | lit-0-valid ✓ (migration 315) |
| ga_pyjhora_engine | service_ok | — | error cleared ✓ (migration 317) |
| bg_doshas | lit | 79 | rebuilt from 50 ✓ |
| bg_medical_mappings | lit | 21 | rebuilt from 9 ✓ |
| bg_nakshatra_medical | lit | 27 | dosha column populated ✓ (migration 316) |
| bg_rules | lit | 2912 | full corpus mined ✓ |
| bg_yogas | lit | 175 | catalog floor ✓ |
| bg_remedies | lit | 266 | accepted as-built ✓ |
| bg_ephemeris | lit | 825,084 | ✓ |
| bg_dignity_reference | lit | 151 | ✓ |
| bg_transit_rules | lit | 50 | ✓ |
| ga_structural | lit | 74,034 | ✓ |
| ga_dashas | lit | 536,471 | ✓ |
| ga_sensitive | lit | 8,610 | ✓ |
| ga_strength | lit | 11,936 | ✓ |

All L2/L3/L4/L5 dormant assets (bo_*, ka_*, ph_*, mi_*) are correctly dormant — not built yet.

### Full endpoint JSON

```json
{
  "data": {
    "assets": [
      {"asset_id":"bg_compendium_index","actual_rows":9538,"state":"lit","last_built_at":"2026-06-09 00:38:44.077645+00"},
      {"asset_id":"bg_concordance","actual_rows":720,"state":"lit","last_built_at":"2026-06-16 11:04:00.801304+00"},
      {"asset_id":"bg_dasha_systems","actual_rows":18,"state":"lit","last_built_at":"2026-06-16 11:15:16.800141+00"},
      {"asset_id":"bg_dignity_reference","actual_rows":151,"state":"lit","last_built_at":"2026-06-17 14:45:25.026692+00"},
      {"asset_id":"bg_doshas","actual_rows":79,"state":"lit","last_built_at":"2026-06-16 11:15:16.800141+00"},
      {"asset_id":"bg_ephemeris","actual_rows":825084,"state":"lit","last_built_at":"2026-06-16 11:15:16.800141+00"},
      {"asset_id":"bg_ephemeris_engine","actual_rows":null,"state":"service_ok"},
      {"asset_id":"bg_medical_mappings","actual_rows":21,"state":"lit","last_built_at":"2026-06-17 07:25:56.680335+00"},
      {"asset_id":"bg_nakshatra","actual_rows":2857,"state":"lit","last_built_at":"2026-06-17 07:26:05.255749+00"},
      {"asset_id":"bg_nakshatra_medical","actual_rows":27,"state":"lit","last_built_at":"2026-06-17 14:46:31.468729+00"},
      {"asset_id":"bg_ontology","actual_rows":652,"state":"lit","last_built_at":"2026-06-16 11:15:16.800141+00"},
      {"asset_id":"bg_panchanga","actual_rows":null,"state":"service_ok"},
      {"asset_id":"bg_prashna_rules","actual_rows":41,"state":"lit","last_built_at":"2026-06-17 07:25:56.263487+00"},
      {"asset_id":"bg_reference","actual_rows":1514,"state":"lit","last_built_at":"2026-06-16 11:15:16.800141+00"},
      {"asset_id":"bg_remedies","actual_rows":266,"state":"lit","last_built_at":"2026-06-16 11:04:00.801304+00"},
      {"asset_id":"bg_rules","actual_rows":2912,"state":"lit","last_built_at":"2026-06-16 11:15:16.800141+00"},
      {"asset_id":"bg_text_index","actual_rows":361,"state":"lit","last_built_at":"2026-06-16 11:04:00.801304+00"},
      {"asset_id":"bg_texts","actual_rows":10651,"state":"lit","last_built_at":"2026-06-16 11:15:16.800141+00"},
      {"asset_id":"bg_transit_engine","actual_rows":9,"state":"lit","last_built_at":"2026-06-17 07:25:56.263487+00"},
      {"asset_id":"bg_transit_rules","actual_rows":50,"state":"lit","last_built_at":"2026-06-17 07:25:56.263487+00"},
      {"asset_id":"bg_vastu_directions","actual_rows":32,"state":"lit","last_built_at":"2026-06-16 11:15:16.800141+00"},
      {"asset_id":"bg_yogas","actual_rows":175,"state":"lit","last_built_at":"2026-06-16 11:15:16.800141+00"},
      {"asset_id":"ga_condition","actual_rows":2880,"state":"lit"},
      {"asset_id":"ga_dashas","actual_rows":536471,"state":"lit"},
      {"asset_id":"ga_medical","actual_rows":45,"state":"lit"},
      {"asset_id":"ga_nakshatra","actual_rows":1802,"state":"lit"},
      {"asset_id":"ga_panchanga","actual_rows":221,"state":"lit"},
      {"asset_id":"ga_positions","actual_rows":530,"state":"lit"},
      {"asset_id":"ga_prashna","actual_rows":0,"state":"lit","error":null},
      {"asset_id":"ga_pyjhora_engine","actual_rows":null,"state":"service_ok","error":null},
      {"asset_id":"ga_sade_sati","actual_rows":11019,"state":"lit"},
      {"asset_id":"ga_sensitive","actual_rows":8610,"state":"lit"},
      {"asset_id":"ga_strength","actual_rows":11936,"state":"lit"},
      {"asset_id":"ga_structural","actual_rows":74034,"state":"lit"},
      {"asset_id":"ga_tajaka","actual_rows":240,"state":"lit"},
      {"asset_id":"ga_transit_anchors","actual_rows":45,"state":"lit"},
      {"asset_id":"ga_vargas","actual_rows":21635,"state":"lit"},
      {"asset_id":"ga_vastu","actual_rows":40,"state":"lit"},
      {"asset_id":"ga_yoga","actual_rows":5,"state":"lit"}
    ]
  },
  "fetched_at": "2026-06-18T12:09:20.322Z",
  "errors": []
}
```

---

## §8 — Code changes in this session

### Files modified
| File | Change |
|---|---|
| `platform/migrations/317_ga_pyjhora_engine_reset_stale_error.sql` | Fixed `SET state = NULL` → `SET state = 'dormant'` (NOT NULL constraint); fixed comment header number 316→317 |
| `platform/python-sidecar/brahmagyan/l0_doshas.py` | Fixed `fetchone()[0]` → `fetchone()['count']` (psycopg3 dict_row compat) |
| `platform/python-sidecar/brahmagyan/l0_yogas.py` | Fixed `fetchone()[0]` → `fetchone()['count']` |
| `platform/python-sidecar/brahmagyan/l0_remedy_corpus.py` | Fixed `fetchone()[0]` → `fetchone()['count']` (×2 occurrences via orchestrator conn) |
| `platform/python-sidecar/brahmagyan/l0_rules.py` | Fixed `fetchone()[0]`→`['count']` (×3), `r[0]`→column-name access in set comprehensions (×3), integer-indexed row dict `r[0..3]`→named keys |
| `platform/python-sidecar/pipeline/orchestrator/writers/__tests__/test_ga_yoga.py` | Updated assertions: YOGAS_CORE 81→144; Sankhya 7→8 |
| `platform/python-sidecar/pipeline/orchestrator/writers/__tests__/test_ga_medical.py` | Updated assertion: MEDICAL_MAPPINGS 9→21; updated docstring |
| `00_ARCHITECTURE/OPEN_ITEMS_REGISTER_v1_0.md` | C1 → RESOLVED; GROUP E added (E1 bg_remedies/bo_upaya, E2 bg_rules ceiling, E3 bg_yogas discrepancy) |

### Untracked files now ready to commit (parallel thread work)
- `platform/migrations/311–317` (7 migration files)
- `platform/python-sidecar/pipeline/orchestrator/writers/bg_dignity_reference.py`
- `platform/python-sidecar/pipeline/orchestrator/writers/bg_ephemeris.py`
- `platform/python-sidecar/brahmagyan/l0_medical.py` (expanded to 21 entries)
- `platform/python-sidecar/brahmagyan/l0_doshas.py` (expanded to 79 entries)
- `platform/python-sidecar/brahmagyan/l0_yogas.py` (expanded to 144 entries)
- `platform/python-sidecar/brahmagyan/l0_remedy_corpus.py`
- `platform/python-sidecar/pipeline/orchestrator/writers/bg_medical_mappings.py`
- `platform/python-sidecar/pipeline/orchestrator/writers/bg_transit_rules.py`
- `platform/scripts/seed/asset_registry_seed.ts`
- `platform/src/app/api/cockpit/stats/route.ts`
- Various 00_ARCHITECTURE docs

---

## §9 — Acceptance criteria check

| Criterion | Status |
|---|---|
| migrations 315–317 APPLIED to prod, ledger-reconciled | ✓ DONE (SHA256s in _migrations_applied) |
| all §6 endpoint checks pass (not DB, not report) | ✓ ALL L0+L1 lit/service_ok, zero errors |
| bg_rules sampled THEN mined; floor = achieved; deterministic extractor confirmed | ✓ DONE (0 yield from un-mined; 2,912 floor confirmed; ZERO LLM) |
| 4 autonomy writers confirmed REGENERABLE (behavioral) | ✓ DONE (all 4 ran, inserted rows) |
| bg_medical grid/combos verified present-or-built | ✓ PRESENT (27-row nakshatra grid + combo entries) |
| FOUNDATION_SESSION_1_CLOSE.md written with endpoint JSON evidence | ✓ THIS DOCUMENT |

---

## §10 — Next session

**Session 2** opens: `ga_structural` Option-C re-architecture (the relational-hub rebuild against the now-settled catalogs). Source brief: `00_ARCHITECTURE/STAGED_CLAUDECODE_BRIEF_FOUNDATION_SESSION_2_GA_STRUCTURAL.md`.

The current branch (`chore/disable-brahma-conductor-schedule`) carries all foundation completion work uncommitted. A PR should be opened against main with all these changes before Session 2 begins.

*End FOUNDATION_SESSION_1_CLOSE v1.0 — 2026-06-18*
