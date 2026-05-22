---
artifact: CLAUDECODE_BRIEF_MCPT_V34_S1_v1_0.md
status: ACTIVE
version: 1.0
project: MCP Transformation
session_id: v3.4-S1
worktree_path: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-GRD
branch: feature/mcpt-grounding
depends_on: []                                                          # parallel-eligible from Day 1; long-running batch
implementation_surface: Claude Code extension in Google Antigravity IDE
disposition: MSR signal-grounding pass (419/573 ungrounded → grounded) + calibration view (perf brief Phase P6)
---

# v3.4-S1 — MSR Signal-Grounding Pass + Calibration View

You are a Claude Code sub-agent on WT-F (`MadhavMCPT-GRD`). Long-running batch session. Closes the MSR citation-grounding gap (per v1.3 carry-forward queue and `MCP_ARCH §9.2 item 14`): 419 of 573 MSR signals currently lack explicit FORENSIC/LEL citations. This session grounds them via embedding-similarity candidate proposal + operator-reviewed accept.

Also implements perf brief **Phase P6** — the calibration materialized view + dashboard tab.

Read: `MCP_ARCH §9.2 item 14`; `MCP_PERF_SYSTEM_BRIEF §4.2 (mv_calibration_score), §7.4 (Predictions/Calibration tab), §9 (the calibration loop), §11 (P6)`.

## §1 — Scope

Two work tracks running in parallel within this session:

**Track A — MSR signal-grounding pass.** Per ungrounded MSR signal: embed signal content via Vertex 768-dim; cosine-similarity search against FORENSIC + LEL chunks; propose top-3 candidate citations; operator (or LLM-as-suggester running offline) accepts/edits; UPDATE `msr_signals` with grounded citations. Goal: 95%+ grounded by session end.

**Track B — Calibration MV + dashboard tab.** Implement `mv_calibration_score` materialized view (perf brief §4.2 schema verbatim); wire it into the operator dashboard's Predictions/Calibration tab (replacing the placeholder from v3.1.0-S5); implement Wilson-interval helper SQL functions (`wilson_lower_bound`, `wilson_upper_bound`); schedule nightly refresh.

## §2 — Files in scope

```
platform/scripts/grounding/msr_grounding_pipeline.ts                     # Track A: candidate proposal
platform/scripts/grounding/grounding_review_queue.ts                     # Track A: operator review surface (CSV or simple HTML)
platform/scripts/grounding/apply_grounded_citations.ts                   # Track A: writes UPDATEs to msr_signals
platform/test/grounding/**                                               # Track A tests
platform/supabase/migrations/ — (none required; uses existing tables)
platform/src/lib/perf/wilson.sql                                         # Track B: Wilson interval functions
platform/src/lib/perf/mv_refresh.ts                                      # Track B: extend with mv_calibration_score
platform/src/app/admin/mcp/health/tabs/PredictionsCalibration.tsx        # Track B: real implementation (replaces placeholder from S5)
platform/test/perf/calibration_view.test.ts                              # Track B test
```

## §3 — Files NOT in scope

```
025_HOLISTIC_SYNTHESIS/MSR_v5_0.md                                       # canonical source; do not edit (msr_signals DB rows are updated, not the canonical doc)
platform-mcp/**                                                          # no MCP tool changes
01_FACTS_LAYER/**                                                        # untouched
```

## §4 — Track A specification

### Grounding pipeline

1. SELECT signal_id, content FROM msr_signals WHERE source_citation IS NULL OR source_citation = ''.
2. For each ungrounded signal:
   a. Embed signal.content via Vertex 768-dim.
   b. Cosine-similarity search against FORENSIC chunks (`rag_chunks WHERE source_canonical_id = 'FORENSIC_v8_0'`) and LEL chunks (`source_canonical_id = 'LEL_v1_6'`). Top-3 candidates per signal.
   c. Write to review queue: `signal_id, candidate_1_source, candidate_1_section, candidate_1_score, candidate_2_*, candidate_3_*`.
3. Operator review surface: CSV at `00_ARCHITECTURE/grounding_review/msr_grounding_candidates_<timestamp>.csv` with one row per signal. Operator marks `accepted_candidate: 1|2|3|reject|defer` per row. Defer pattern recommended for ambiguous cases.
4. Apply script: reads operator-edited CSV; UPDATEs msr_signals with accepted citation; tags as `grounded_at: <timestamp>`, `grounded_by: 'mcpt-v34-s1'`.

This is the **only** part of MCP Transformation that may legitimately require operator interaction within a session. Brief allows partial completion: target 95% grounded; if operator backlog prevents reaching 100% within session window, sub-agent reports partial in FINAL_SUMMARY and the residual rolls into v3.5 follow-up.

### LLM-as-suggester variant (optional, recommended)

Instead of (or in addition to) operator manual review, a one-off Cowork session (NOT this Claude Code session — keep the surface separation per PROJECT_MEMORY) can review the candidate CSV with Claude's judgment and produce an accepted-candidate column. Mass-import via the apply script. Brief permits this and notes it explicitly.

## §5 — Track B specification

### `wilson.sql` functions

```sql
CREATE OR REPLACE FUNCTION wilson_lower_bound(successes int, total int, confidence float)
RETURNS float AS $$
DECLARE
  z float;
  p_hat float;
  denom float;
  center float;
  margin float;
BEGIN
  IF total = 0 THEN RETURN NULL; END IF;
  z := CASE confidence
    WHEN 0.95 THEN 1.96
    WHEN 0.99 THEN 2.576
    WHEN 0.90 THEN 1.645
    ELSE 1.96
  END;
  p_hat := successes::float / total;
  denom := 1 + (z * z / total);
  center := (p_hat + (z * z / (2 * total))) / denom;
  margin := (z * sqrt((p_hat * (1 - p_hat) / total) + (z * z / (4 * total * total)))) / denom;
  RETURN greatest(0, center - margin);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- analogous wilson_upper_bound
```

### Calibration MV

Per perf brief §4.2 verbatim. Refreshed nightly at 04:00 UTC (after audit job).

### Dashboard tab implementation

Replaces v3.1.0-S5's placeholder. Renders the calibration grid table per perf brief §7.4: per `(confidence_band, domain, horizon_bucket)` cell, show N, realized rate, Wilson CI, discrepancy flag. Sparklines per cell over time.

## §6 — Acceptance criteria

- **AC.S1.1** (Track A) — `SELECT count(*) FROM msr_signals WHERE source_citation IS NOT NULL` ≥ 0.95 × total signals (≥ 544 of 573).
- **AC.S1.2** (Track A) — Operator review CSV archived to `00_ARCHITECTURE/grounding_review/` for audit trail.
- **AC.S1.3** (Track B) — `mv_calibration_score` materialized view exists, populated.
- **AC.S1.4** (Track B) — Wilson functions return correct values for known test cases (50% of 10: CI ~(0.24, 0.76)).
- **AC.S1.5** (Track B) — Dashboard's Predictions/Calibration tab shows real data (no placeholder).
- **AC.S1.6** — Merge `feature/mcpt-grounding` → `feature/mcpt-final`.

## §7 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-GRD && \
  test -f platform/scripts/grounding/msr_grounding_pipeline.ts && \
  test -f platform/src/lib/perf/wilson.sql && \
  psql "$DATABASE_URL_PROD" -c "SELECT count(*)*100/(SELECT count(*) FROM msr_signals) FROM msr_signals WHERE source_citation IS NOT NULL" | tail -1 | awk '{ if ($1 >= 95) exit 0; else exit 1 }' && \
  git log --oneline feature/mcpt-final | grep -q "MCPT v3.4-S1: grounding"
```

## §8 — Sealing artifact

`00_ARCHITECTURE/MCPT_V34_S1_CLOSE.md`. Body: Track A pre/post grounding stats, sample grounded signals showing the citations applied, Track B calibration grid sample, Wilson function test outputs.

---

*End of CLAUDECODE_BRIEF_MCPT_V34_S1_v1_0.md.*
