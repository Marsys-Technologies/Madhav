---
artifact: CLAUDECODE_BRIEF_MCPT_V32_S5_v1_0.md
status: ACTIVE
version: 1.0
project: MCP Transformation
session_id: v3.2-S5
worktree_path: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-TAJ
branch: feature/mcpt-tajaka
depends_on: [v3.2-S3, v3.2-S4]                                          # needs Tajaka text + Jaim+KP tables
implementation_surface: Claude Code extension in Google Antigravity IDE
disposition: Tajaka multi-school table backfill (20% → 100%) + school_convergence_index materialized view + merge v3.2 to FINAL
source_data: 00_ARCHITECTURE/SOURCE_DATA/multi_school_seeds/tajaka_seed.csv
migration_number: 079
---

# v3.2-S5 — Tajaka Tables + Convergence Index + v3.2 Merge

You are a Claude Code sub-agent on WT-D. Final v3.2 session. Backfills Tajaka multi-school stance rows (20% → 100%), builds the `school_convergence_index` materialized view, and merges v3.2 work into `feature/mcpt-final`.

Read: `MCP_ARCH §9.2 items 4, 7`; `MCP_PERF_SYSTEM_BRIEF §4.2 (school_convergence_index)`; `MCP_TRANSFORMATION_PLAN §7` (merge protocol).

## §1 — Scope

- Tajaka backfill: muntha + saham + year-lord rows per native chart year + Tajaka-school stances on relevant MSR signals.
- `school_convergence_index` materialized view: precomputed per-claim convergence scores across the 4 schools, refreshed nightly.
- Merge `feature/mcpt-tajaka` + cross-WT pull of v3.2-S1 (WT-B BPHS) and v3.2-S2/S4 (WT-C Jaim+KP) into `feature/mcpt-final`.

## §2 — Source data prerequisite

`00_ARCHITECTURE/SOURCE_DATA/multi_school_seeds/tajaka_seed.csv` with year-lord + muntha + saham mappings. If missing, halt with `MISSING_SOURCE_DATA`.

## §3 — Files in scope

```
platform/supabase/migrations/079_tajaka_and_convergence.sql              # Tajaka columns + school_convergence_index MV definition
platform/scripts/bootstrap/bootstrap_multi_school_tajaka.ts              # new
platform/test/bootstrap/multi_school_tajaka.test.ts
platform/test/perf/school_convergence_index.test.ts                      # MV verification
```

## §4 — Backfill specification

### Tajaka multi-school stance backfill

1. UPDATE multi_school table to set `tajaka_stance` column for MSR signals where a Tajaka reading applies. Cite back into `classical_texts.work='Tajaka Neelakanthi'`.
2. INSERT `tajaka_year_lord_{year}` rows for native chart spans (1984–2070 say) into a separate `tajaka_annual` table (schema in migration 079).

### `school_convergence_index` materialized view

Schema per perf brief §4.2 implications:

```sql
CREATE MATERIALIZED VIEW school_convergence_index AS
SELECT
  signal_id,
  count(*) FILTER (WHERE parashara_stance IS NOT NULL) AS parashara_present,
  count(*) FILTER (WHERE jaimini_stance IS NOT NULL) AS jaimini_present,
  count(*) FILTER (WHERE kp_stance IS NOT NULL) AS kp_present,
  count(*) FILTER (WHERE tajaka_stance IS NOT NULL) AS tajaka_present,
  -- convergence_score: pairwise agreement on stance polarity
  -- 1.0 = all schools agree; 0.0 = all disagree
  compute_convergence_score(parashara_stance, jaimini_stance, kp_stance, tajaka_stance) AS convergence_score,
  array_remove(ARRAY[
    CASE WHEN parashara_stance != consensus_stance THEN 'Parashara' END,
    CASE WHEN jaimini_stance != consensus_stance THEN 'Jaimini' END,
    CASE WHEN kp_stance != consensus_stance THEN 'KP' END,
    CASE WHEN tajaka_stance != consensus_stance THEN 'Tajaka' END
  ], NULL) AS divergent_schools
FROM multi_school_signals
GROUP BY signal_id;

CREATE UNIQUE INDEX ON school_convergence_index (signal_id);
```

Nightly refresh wired into existing scheduler (same cron as other MVs from S4).

### Merge to FINAL

Per `MCP_TRANSFORMATION_PLAN §7`:

```bash
git fetch origin feature/mcpt-bphs feature/mcpt-jaim-kp feature/mcpt-final
git checkout feature/mcpt-final
git merge --no-ff feature/mcpt-bphs -m "MCPT v3.2: BPHS → final"
git merge --no-ff feature/mcpt-jaim-kp -m "MCPT v3.2: Jaim+KP → final"
git merge --no-ff feature/mcpt-tajaka -m "MCPT v3.2: Tajaka → final"
ls platform/supabase/migrations/ | sort -n | uniq -d   # must return empty
git push origin feature/mcpt-final
```

## §5 — Acceptance criteria

- **AC.S5.1** — Tajaka coverage: `SELECT count(*) FROM multi_school_signals WHERE tajaka_stance IS NOT NULL` reaches at least 90% of total signals where a Tajaka reading applies.
- **AC.S5.2** — `school_convergence_index` MV populated, refreshes successfully.
- **AC.S5.3** — `multi_school_bundle({claim:"Mercury is the chart's operational anchor"})` returns ≥4 per-school evidence blocks (Parashara, Jaimini, KP, Tajaka).
- **AC.S5.4** — All three v3.2 branches merged into `feature/mcpt-final` clean.
- **AC.S5.5** — Migration sequence 072–079 unique on `feature/mcpt-final`.

## §6 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-TAJ && \
  test -f platform/supabase/migrations/079_tajaka_and_convergence.sql && \
  test -f platform/scripts/bootstrap/bootstrap_multi_school_tajaka.ts && \
  git log --oneline feature/mcpt-final | grep -q "MCPT v3.2: BPHS" && \
  git log --oneline feature/mcpt-final | grep -q "MCPT v3.2: Jaim+KP" && \
  git log --oneline feature/mcpt-final | grep -q "MCPT v3.2: Tajaka" && \
  test "$(ls platform/supabase/migrations/ | sort -n | uniq -d | wc -l)" = "0"
```

## §7 — Sealing artifact

`00_ARCHITECTURE/MCPT_V32_CLOSE.md` (rolls up S1–S5). Body: classical_texts row counts per work, multi_school coverage matrix per school, school_convergence_index snapshot, merge evidence.

---

*End of CLAUDECODE_BRIEF_MCPT_V32_S5_v1_0.md.*
