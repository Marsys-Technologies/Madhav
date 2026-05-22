---
artifact: CLAUDECODE_BRIEF_MCPT_V33_S3_v1_0.md
status: ACTIVE
version: 1.0
project: MCP Transformation
session_id: v3.3-S3
worktree_path: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-DPT
branch: feature/mcpt-depth
depends_on: [v3.3-S2, v3.2-S3, v3.2-S5]                                 # CROSS-WT: needs Tajaka text (S3) + Tajaka tables (S5)
implementation_surface: Claude Code extension in Google Antigravity IDE
disposition: chart_facts varshphal (Tajaka annual-progressions) ingestion
source_data: 00_ARCHITECTURE/SOURCE_DATA/varshphal_tables/
---

# v3.3-S3 — Varshphal (Tajaka Annual Progressions) Ingestion

You are a Claude Code sub-agent on WT-E. **Cross-worktree dependency**: this session waits for v3.2-S3 (Tajaka text indexed) and v3.2-S5 (Tajaka multi-school tables) to merge into `feature/mcpt-final`. Before starting, the Conductor REBASES `feature/mcpt-depth` against `feature/mcpt-final` to pick up the Tajaka assets.

Read: `MCP_ARCH §9.2 item 13`; `MCP_TRANSFORMATION_PLAN §7 (merge protocol)`; v3.3-S1 brief.

## §1 — Scope

Ingest Tajaka varshphal rows into `chart_facts.category='varshphal'`: per native chart year (1984..2070 baseline) compute and store:
- Muntha (year-progression position)
- Year-lord (Varshpati)
- Sahams (16+ sahams: Punya, Vidya, Yasas, etc.)
- Pancha-vargiya-bala for each year

## §2 — Rebase prerequisite

Before any ingestion work:

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-DPT
git fetch origin feature/mcpt-final
git rebase origin/feature/mcpt-final
# Verify Tajaka text present:
psql "$DATABASE_URL_PROD" -c "SELECT count(*) FROM classical_texts WHERE work='Tajaka Neelakanthi'" | grep -qE "^\s+[4-9][0-9]{2,}" || { echo "Tajaka text not yet present — v3.2-S3 not merged. Halt."; exit 1; }
# Verify Tajaka tables present:
psql "$DATABASE_URL_PROD" -c "SELECT count(*) FROM multi_school_signals WHERE tajaka_stance IS NOT NULL" | tail -1 | awk '{ if ($1 > 100) exit 0; else { print "Tajaka tables not yet present"; exit 1 } }'
```

If either check fails, halt with `CROSS_WT_DEPENDENCY_NOT_MERGED`. Operator merges upstream first; resumes this session.

## §3 — Source data prerequisite

`00_ARCHITECTURE/SOURCE_DATA/varshphal_tables/native_varshphal_1984_2070.csv` (operator-staged OR derivable via Tajaka rules in code). Brief allows compute mode.

## §4 — Files in scope

```
platform/scripts/bootstrap/bootstrap_chart_facts_varshphal.ts            # new
platform/scripts/bootstrap/lib/tajaka_compute.ts                         # NEW Tajaka calculation rules (if compute mode)
platform/test/bootstrap/chart_facts_varshphal.test.ts
```

## §5 — Ingestion specification

Per year (1984..2070):
- 1 row: `subkey='<year>.muntha'`, value_text = sign+degree+house
- 1 row: `subkey='<year>.year_lord'`, value_text = planet name
- ~16 rows: `subkey='<year>.saham.<name>'`, value_text = position
- 1 row: `subkey='<year>.pancha_vargiya_bala'`, value_jsonb = per-planet breakdown

Per year: ~20 rows. Across 86 years: ~1700 rows.

Citations: source_canonical_id='Tajaka Neelakanthi' with chapter reference where applicable.

## §6 — Acceptance criteria

- **AC.S3.1** — `SELECT count(*) FROM chart_facts WHERE category='varshphal'` ≥ 1500.
- **AC.S3.2** — `SELECT count(DISTINCT subkey) FROM chart_facts WHERE category='varshphal' AND subkey LIKE '1984.%'` ≥ 18 (one year fully populated as spot-check).
- **AC.S3.3** — `query_chart_facts({category:"varshphal", year:1984})` returns muntha + year-lord rows.
- **AC.S3.4** — `build_manifests` entry.

## §7 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-DPT && \
  test -f platform/scripts/bootstrap/bootstrap_chart_facts_varshphal.ts && \
  psql "$DATABASE_URL_PROD" -c "SELECT count(*) FROM chart_facts WHERE category='varshphal'" | grep -qE "^\s+1[5-9][0-9]{2}|^\s+[2-9][0-9]{3,}"
```

## §8 — Sealing artifact

`00_ARCHITECTURE/MCPT_V33_S3_CLOSE.md`. Body: per-year row count distribution, spot-check on native's birth year (1984) showing all expected rows.

---

*End of CLAUDECODE_BRIEF_MCPT_V33_S3_v1_0.md.*
