---
artifact: CLAUDECODE_BRIEF_MCPT_V32_S4_v1_0.md
status: ACTIVE
version: 1.0
project: MCP Transformation
session_id: v3.2-S4
worktree_path: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-JK
branch: feature/mcpt-jaim-kp
depends_on: [v3.2-S2]                                                   # same-WT sequential after S2
implementation_surface: Claude Code extension in Google Antigravity IDE
disposition: Multi-school tables backfill — Jaimini karaka mappings + KP cuspal mappings to 100%
source_data: 00_ARCHITECTURE/SOURCE_DATA/multi_school_seeds/
migration_number: 078
---

# v3.2-S4 — Multi-School Tables (Jaim + KP)

You are a Claude Code sub-agent on WT-C. Runs after v3.2-S2 finishes (same WT). Backfills the `multi_school_*` tables for Jaimini (80% → 100%) and KP (60% → 100%) so `cross_school_lookup` returns substantive per-school stances for these two schools.

Read: `MCP_ARCH §9.2 items 5, 6`; `MCP_PERF_SYSTEM_BRIEF §4.2 (multi_school_* mv block)`; `MCP_TRANSFORMATION_PLAN §5` (migration 078 reserved).

## §1 — Scope

Migration 078 adds any missing schema bits (per existing multi_school_* table inspection). Backfill content: Jaimini karaka rows per MSR signal (from 80% to 100%); KP cuspal grid rows + planet sub-lord + significator + ruling-planets (from 60% to 100%).

## §2 — Source data prerequisite

`00_ARCHITECTURE/SOURCE_DATA/multi_school_seeds/jaimini_karaka_mappings_seed.csv` (operator-authored) and `kp_cuspal_grid_seed.csv` (computable from chart). If seeds missing, sub-agent halts with `MISSING_SOURCE_DATA`.

## §3 — Files in scope

```
platform/supabase/migrations/078_multi_school_extensions.sql             # schema bits if any
platform/scripts/bootstrap/bootstrap_multi_school_jaimini.ts             # new
platform/scripts/bootstrap/bootstrap_multi_school_kp.ts                  # new
platform/test/bootstrap/multi_school_jaimini.test.ts
platform/test/bootstrap/multi_school_kp.test.ts
```

## §4 — Files NOT in scope

```
platform/scripts/bootstrap/bootstrap_classical_texts_*.ts                # done in S2
platform-mcp/**                                                          # no tool changes
01_FACTS_LAYER/**, 025_HOLISTIC_SYNTHESIS/**                             # untouched
```

## §5 — Backfill specification

### Jaimini karaka backfill (80% → 100%)

1. SELECT MSR signals where the Jaimini-school stance column is NULL.
2. For each, look up the Jaimini karaka mapping from seed CSV.
3. UPDATE the multi_school table to populate the Jaimini-stance column.
4. Cite back into `classical_texts` where Jaimini Sutram sutra is the source: `source_signal_id = 'JS.{adhyaya}.{pada}.{sutra}'`.

### KP cuspal backfill (60% → 100%)

1. Compute the 12 cuspal sub-lords + significator hierarchy for the native's chart per KP rules. Use `query_ephemeris` + KP cuspal math (Placidus house system + sub-lord lookup via Nakshatra-spans).
2. UPDATE multi_school table with per-cusp stance + ruling planets.
3. Cite back into `classical_texts` (KP Reader vol/chapter references).

## §6 — Acceptance criteria

- **AC.S4.1** — Jaimini coverage: `SELECT count(*) FROM multi_school_signals WHERE jaimini_stance IS NOT NULL` reaches at least 95% of total MSR signals where a Jaimini stance is applicable.
- **AC.S4.2** — KP coverage: KP cusps 1–12 all populated with sub-lord + significator data.
- **AC.S4.3** — `cross_school_lookup({claim:"Saturn in 10th delays career"})` returns substantive Jaimini + KP stances with classical citations.
- **AC.S4.4** — Migration 078 applies cleanly on staging.

## §7 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-JK && \
  test -f platform/supabase/migrations/078_multi_school_extensions.sql && \
  test -f platform/scripts/bootstrap/bootstrap_multi_school_jaimini.ts && \
  test -f platform/scripts/bootstrap/bootstrap_multi_school_kp.ts && \
  psql "$DATABASE_URL_PROD" -c "SELECT count(*) FROM multi_school_signals WHERE jaimini_stance IS NOT NULL" | tail -1 | awk '{ if ($1 > 0) exit 0; else exit 1 }'
```

## §8 — Sealing artifact

`00_ARCHITECTURE/MCPT_V32_S4_CLOSE.md`. Body: per-school coverage delta (before/after percentages), cross_school_lookup sample outputs for representative claims.

---

*End of CLAUDECODE_BRIEF_MCPT_V32_S4_v1_0.md.*
