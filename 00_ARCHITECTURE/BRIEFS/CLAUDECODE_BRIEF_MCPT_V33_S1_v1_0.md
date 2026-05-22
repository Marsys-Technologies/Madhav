---
artifact: CLAUDECODE_BRIEF_MCPT_V33_S1_v1_0.md
status: ACTIVE
version: 1.0
project: MCP Transformation
session_id: v3.3-S1
worktree_path: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-DPT
branch: feature/mcpt-depth
depends_on: []                                                          # parallel-eligible from Day 1
implementation_surface: Claude Code extension in Google Antigravity IDE
disposition: chart_facts.shadbala + ashtakavarga_* + bhava_bala ingestion
source_data: 00_ARCHITECTURE/SOURCE_DATA/jagannatha_hora_exports/
---

# v3.3-S1 — Shadbala + Ashtakavarga + Bhava Bala Ingestion

You are a Claude Code sub-agent on WT-E (`MadhavMCPT-DPT`). Closes the highest-impact depth gap in `chart_facts`. After v3.3-S1 lands, `query_chart_facts(category:"shadbala")` and `(category:"ashtakavarga_sav")` return populated rows — both were 0/63 and 0/12 at v3.1 start.

Read: `MCP_ARCH §9.2 items 8, 9, 10`; `MCP_DIAGNOSIS §3.1` (the empty-categories list); `MCP_TRANSFORMATION_PLAN §6` (source-data manifest).

## §1 — Scope

Ingest three `chart_facts` category groups for the native's chart:
- **shadbala**: 9 planets × 7 measures (Sthana / Dig / Kala / Cheshta / Naisargika / Drik / Total) = 63 rows.
- **ashtakavarga**: SAV (12 rows, one per house), BAV per planet (12 × 7 = 84 rows), pinda + kakshya zones.
- **bhava_bala**: 12 houses × BVB components.

## §2 — Source data prerequisite

`00_ARCHITECTURE/SOURCE_DATA/jagannatha_hora_exports/native_chart_full_export.csv` (or per-table CSVs) containing the precomputed Shadbala virupas + Ashtakavarga grids + Bhava Bala for the native chart (1984-02-05 10:43 IST Bhubaneswar). Operator stages this in Wave 0. If missing, halt with `MISSING_SOURCE_DATA`.

Fallback: if Jagannatha Hora export is unavailable, the session may COMPUTE these values via Swiss Ephemeris + reference rules (slow but viable). Brief allows operator-chosen mode via `--mode={import|compute}` flag on the bootstrap script.

## §3 — Files in scope

```
platform/scripts/bootstrap/bootstrap_chart_facts_shadbala.ts             # new
platform/scripts/bootstrap/bootstrap_chart_facts_ashtakavarga.ts         # new
platform/scripts/bootstrap/bootstrap_chart_facts_bhava_bala.ts           # new
platform/scripts/bootstrap/lib/chart_facts_ingester.ts                   # shared helper (idempotent INSERT pattern)
platform/test/bootstrap/chart_facts_shadbala.test.ts
platform/test/bootstrap/chart_facts_ashtakavarga.test.ts
platform/test/bootstrap/chart_facts_bhava_bala.test.ts
00_ARCHITECTURE/BRIEFS/SOURCE_INVENTORY_SHADBALA_v1_0.md
```

No new migrations (uses existing `chart_facts` table). UPSERT pattern (ON CONFLICT) so re-runs are idempotent.

## §4 — Files NOT in scope

```
platform/src/lib/retrieve/**                                             # no tool changes
platform-mcp/**                                                          # no MCP-server changes
01_FACTS_LAYER/FORENSIC*                                                 # FORENSIC source unchanged; chart_facts is the DB cache
```

## §5 — Ingestion specification

### Shadbala (63 rows)

Per planet (Sun..Saturn + Rahu + Ketu) × per measure (Sthana, Dig, Kala, Cheshta, Naisargika, Drik, Total):

```sql
INSERT INTO chart_facts (chart_id, category, subkey, value_numeric, value_unit, source_canonical_id, source_section, build_id)
VALUES (
  '<native_chart_id>',
  'shadbala',
  '<planet>.<measure>',                  -- e.g., 'Saturn.Total'
  <virupa_value>,
  'virupa',
  'FORENSIC_v8_0',
  '§3.x.shadbala',
  'mcpt-v33-s1-<timestamp>'
)
ON CONFLICT (chart_id, category, subkey) DO UPDATE SET
  value_numeric = EXCLUDED.value_numeric,
  build_id = EXCLUDED.build_id,
  updated_at = now();
```

### Ashtakavarga (SAV + BAV + pinda + kakshya)

SAV: 12 rows, one per house.
BAV per planet: 9 planets × 12 houses = 108 rows (subkey = `<planet>.house<NN>`).
Pinda + kakshya: per `chart_facts.subkey` convention.

### Bhava Bala

12 rows, one per house. Subkey = `house<NN>.BVB_total`. Plus component decomposition rows.

## §6 — Build manifest

`build_manifests` entry per the v1.3 carry-forward audit item — explicitly INSERT after each of the three ingestions, do not skip.

## §7 — Acceptance criteria

- **AC.S1.1** — `SELECT count(*) FROM chart_facts WHERE category='shadbala'` ≥ 63.
- **AC.S1.2** — `SELECT count(*) FROM chart_facts WHERE category='ashtakavarga_sav'` = 12.
- **AC.S1.3** — `SELECT count(*) FROM chart_facts WHERE category='ashtakavarga_bav'` ≥ 100.
- **AC.S1.4** — `SELECT count(*) FROM chart_facts WHERE category='bhava_bala'` ≥ 12.
- **AC.S1.5** — `build_manifests` entries present for all three ingestions.
- **AC.S1.6** — After v3.1.0-S4 merges into final, `data_coverage({asset_id:"chart_facts", subkey:"shadbala"})` reports `coverage_pct: ≥ 0.95`.

## §8 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-DPT && \
  test -f platform/scripts/bootstrap/bootstrap_chart_facts_shadbala.ts && \
  test -f platform/scripts/bootstrap/bootstrap_chart_facts_ashtakavarga.ts && \
  test -f platform/scripts/bootstrap/bootstrap_chart_facts_bhava_bala.ts && \
  psql "$DATABASE_URL_PROD" -c "SELECT count(*) FROM chart_facts WHERE category='shadbala'" | grep -qE "^\s+[6-9][0-9]+|[1-9][0-9]{2,}" && \
  psql "$DATABASE_URL_PROD" -c "SELECT count(*) FROM chart_facts WHERE category='ashtakavarga_sav'" | grep -qE "^\s+12\s*$" && \
  psql "$DATABASE_URL_PROD" -c "SELECT count(*) FROM build_manifests WHERE asset_id='chart_facts' AND build_id LIKE 'mcpt-v33-s1-%'" | grep -qE "^\s+[3-9]"
```

## §9 — Sealing artifact

`00_ARCHITECTURE/MCPT_V33_S1_CLOSE.md`. Body: pre/post row counts per category, sample row spot-check (Saturn-Uccha-Bala virupa value matches FORENSIC §3.15 / SIG.MSR.053 expectation: 59.18).

---

*End of CLAUDECODE_BRIEF_MCPT_V33_S1_v1_0.md.*
