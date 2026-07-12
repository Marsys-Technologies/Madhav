# shard-9b-vargottama_per_varga

**shard_id:** 9b-vargottama_per_varga
**lane:** 9b
**charts:** 482012f1, 1c826d5a

## SQL run
5-cell recipe with `f.fact_category = 'vargottama_per_varga'`.

## Verbatim results
- chart_facts rows: 2520 (both charts; ~1260/chart)
- cell1: Abhisek=1232, Abhinandan=1184
- cell2_salience:
  - Abhisek: `background=5, chart_defining=71, major=856, supporting=300`
  - Abhinandan: `background=316, chart_defining=55, major=659, supporting=154`
- cell5_type: both `varga_pattern`
- cell3_attr: 1232/1232 (Abhisek), 1184/1184 (Abhinandan) — 100%
- cell4_domains: both `character|career` (invariant)

## 5-cell verdicts
1. Consumed? YES — near-total ingestion (1232/1184 of ~1260 facts/chart).
2. Salience: **DISTRIBUTED across all four tiers** — unlike every other category in this shard, this one discriminates. But 856 `major` + 71 `chart_defining` signals for one chart is a very large high-tier population: vargottama in minor/subtle vargas (D-45, D-60, etc.) for arbitrary grahas is low-decision-weight yet sits at `major`. Per charter §7.4 metric 3 (descriptive-trivia share at major tier), this is salience inflation — the volume of major-tier vargottama flags would drown genuinely chart-defining findings on any ranked surface. Rationale for exceeding acharya tolerance: an acharya weights vargottama in D-1/D-9 heavily but treats D-45/D-60 graha vargottama as minor; 856 undifferentiated major-tier flags collapse that distinction.
3. Attribution: 100% resolvable — PASS.
4. Domain: **INVARIANT** `character|career` for all ~1200 signals.
5. Emergence: ~1200 `varga_pattern` signals/chart — a single fact_category producing ~1200 signals is itself a DROWNED-risk contributor.

## design_correctness_verdict: WEAK
Fully consumed and attributed, and (uniquely) tier-discriminated; but the sheer volume of major/chart_defining vargottama flags (salience inflation, §7.4 metric 3) plus the invariant `character|career` domain make the genuinely important vargottamas hard to find within the category's own ~1200-signal mass.

## Findings
- **F1 (class 7 DROWNED / salience inflation):** 856 `major` + 71 `chart_defining` vargottama_per_varga signals for Abhisek (659 major + 55 chart_defining for Abhinandan). Minor-varga vargottama (low decision weight) is promoted to the same tier as chart-defining structure. Rationale inline per §7.4 amendment. Suspected layer: ranking (bo_laksana signature_tier assignment). Severity: MED. Evidence: cell2 `major=856, chart_defining=71`. Dedupe: R-44b-class (trivia at major tier).
- **F2 (class 2 / domain mis-map):** ~1200 signals/chart all → invariant `character|career`. Severity: LOW. Evidence: cell4 single value.
