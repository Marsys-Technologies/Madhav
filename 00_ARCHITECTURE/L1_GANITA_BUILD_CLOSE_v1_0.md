---
artifact: L1_GANITA_BUILD_CLOSE
version: 1.0
status: COMPLETE
date_closed: 2026-06-10
seal_commit: d228aa0f1cb3d4640b12ce6f124627c27b5e8147
git_tag: l1-ganita-build-complete
---

# L1 Gaṇita Build — Wave Close

## §1 — Summary

The L1 Gaṇita layer (GA3–GA9) is **COMPLETE** and merged to `main` as of 2026-06-10.

All 7 writer sub-agents executed, all CI gates cleared, IS.8(b) red-team PASSED (0 class-1 findings), and all 7 PRs merged in sequence into `feature/ga3-chart-facts-writer` then to `main`.

- **Main HEAD**: `d228aa0f1cb3d4640b12ce6f124627c27b5e8147`
- **Git tag**: `l1-ganita-build-complete`
- **PRs merged**: #237 (GA3 integration→main), #238 (GA4), #239 (GA6), #240 (GA7), #241 (GA5), #242 (GA8), #243 (GA9)

## §2 — Deliverables

### Writers Shipped

| Writer | PR | Categories | Target Table | Migration |
|--------|-----|------------|--------------|-----------|
| GA3 ga_positions + ga_strength | #237 | 27 | `chart_facts`, `ganita_positions` | 206, 207 |
| GA4 ga_panchanga | #238 | 26 | `chart_facts` (INVARIANT + DEPENDENT) | 208 |
| GA5 ga_sensitive | #241 | 32 | `chart_facts` (5 ayanamshas) | 209 |
| GA6 ga_vargas | #239 | 26 | `chart_divisionals` | 210 |
| GA7 ga_dashas | #240 | — | `chart_dashas` (7 systems × Sukshma L4 × 5 ayanamshas) | 211 |
| GA8 ga_structural (T1) | #242 | 43 | `chart_facts` | 212 |
| GA9 ga_sade_sati | #243 | 15 | `chart_facts` | 213 |

**Total CHART_FACTS_SCHEMA.json categories**: 169 (GA3:27 + GA4:26 + GA5:32 + GA6:26 + GA8:43 + GA9:15; GA7 writes to `chart_dashas` not chart_facts)

### Migrations

| # | File | Purpose |
|---|------|---------|
| 206 | `206_ga3_supporting_tables.sql` | GA3 supporting tables (ganita_positions, chart_divisionals, chart_dashas) |
| 207 | `207_ga3_materialized_views.sql` | GA3 materialized views |
| 208 | `208_ga4_panchanga_mv.sql` | GA4 panchanga MV |
| 209 | `209_ga5_sensitive_points_mv.sql` | GA5 sensitive points MV |
| 210 | `210_ga6_chart_divisionals_extension.sql` | GA6 divisionals extension |
| 211 | `211_ga7_dashas_kp_sublevel.sql` | GA7 chart_dashas + KP sublevel column |
| 212 | `212_ga8_t1_structural.sql` | GA8 structural MVs |
| 213 | `213_ga9_sade_sati.sql` | GA9 sade sati MVs |

### Test Suites

All passing (pre-merge CI green on every PR):

| Test file | Coverage |
|-----------|---------|
| `test_ga3_writers.py` | GA3 schema + position + strength + FORENSIC anchors |
| `test_ga4_writer.py` | GA4 panchanga tithi/vara/nakshatra/yoga/karana |
| `test_ga5_writer.py` | GA5 sensitive points — 30 categories, Section-B enrichment |
| `test_ga6_writer.py` | GA6 vargas — 30 divisional charts |
| `test_ga7_writer.py` | GA7 dashas — 7 systems, Sukshma L4, KP sublevel |
| `test_ga8_writer.py` | GA8 T1 structural — argala/virodha/badhaka/yogas |
| `test_ga9_writer.py` | GA9 sade sati — 15 categories, 8 cancellation rules |

## §3 — IS.8(b) Red-Team Result

**CLEARED** — 0 class-1 findings. All 8 adversarial dimensions verified:

1. Migration sequence coherence (206→207→208→209→210→211→212→213): PASS
2. chart_dashas table consistency (GA7 writes only to chart_dashas): PASS
3. GA3/GA8 fact_id pattern disjointness: PASS
4. GA9 concurrent dasha atomic grain (7 lords as separate rows): PASS
5. FORENSIC anchor coverage (Sun=Capricorn, Moon=PurvaBhadra, Lagna=Aries, etc.): PASS
6. Phantom chart_id guard (`362f9f17` never written): PASS
7. GA7 level_n ≤ 4 (ZERO level_n=5 Prana rows): PASS
8. constituent_facts_array format (GA9 references GA3 positions correctly): PASS

Remediation commits (pre-merge): `c5516232` (GA5 migration 208→209), `8604d364` (GA6 migration 209→210 + CHECK constraint), `546490df` (GA7 migration 208→211 + AYANAMSHAS + DO block).

## §4 — Build Runner

`platform/python-sidecar/ga_writers/build_runner.py` — GA3+GA4+GA5+GA6+GA7+GA8+GA9 orchestrator.

Steps in order:
1. ga_positions → `ganita_positions` + `chart_facts`
2. ga_strength → `chart_facts` (shadbala + ashtakavarga + bhava_bala)
2b. ga_vargas → `chart_divisionals`
3. ga_structural (GA8) → `chart_facts` (argala/virodha/badhaka/yogas)
3. ga_sensitive (GA5) → `chart_facts` (30 A5 categories)
3b. ga_panchanga (GA4) → `chart_facts` (INVARIANT + DEPENDENT)
4. Refresh all materialized views
5. ga_dashas (GA7) → `chart_dashas` (7 systems)
5. ga_sade_sati (GA9) → `chart_facts` (Sade Sati cycles)
6. Gate validation (FORENSIC + two-pass)

## §5 — Operator Actions Required

The following must be completed before the build can run against production:

- [ ] Apply migrations 206–213 in order to production DB
- [ ] Verify `chart_facts`, `chart_divisionals`, `chart_dashas` tables exist
- [ ] Run `build_runner.py` for canonical chart_id `482012f1-710e-4a25-994a-93821f5871aa`
- [ ] Verify FORENSIC anchor gate (PASS = build accepted; any divergence = halt + investigate)
- [ ] Verify row floors per writer:
  - GA3: ≥200 ganita_positions rows; ≥1,000 chart_facts strength rows
  - GA4: ≥39 panchanga rows (31 INVARIANT + 8 DEPENDENT)
  - GA5: ≥13,000 chart_facts sensitive-points rows
  - GA6: ≥78,000 chart_divisionals rows
  - GA7: ≥50,000 chart_dashas rows (7 systems × 4 levels × 5 ayanamshas)
  - GA8: ≥5,000 chart_facts structural rows
  - GA9: ≥875 chart_facts sade sati rows (15 categories × 5 ayanamshas)

## §6 — Concurrent Workstream Registry Entry

This wave closes the **L1 Gaṇita Build** workstream declared in the L1 Gaṇita campaign.
Conductor queue: `00_ARCHITECTURE/CONDUCTOR/l1-ganita-build/session_queue.yaml` — all 9 entries `status: passed`.
Campaign doc: `00_ARCHITECTURE/L1_GANITA_BUILD_CAMPAIGN_v1_0.md`.

CURRENT_STATE must be updated to reflect this workstream as COMPLETE.

---
*Sealed 2026-06-10. All acceptance criteria met. Signed: Claude Sonnet 4.6.*
