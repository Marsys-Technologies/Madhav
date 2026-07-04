---
artifact: BA_REBUILD_SNAPSHOT_v1_0.md
version: 1.0
status: LIVE
chart_id: 1c826d5a-41cb-4450-b4dc-59d440e5f75a
chart_name: Abhinandan Mohanty
snapshot_timestamp: 2026-07-04T05:50Z
branch: fix/ba-rebuild-live-abhinandan
---

# BA Rebuild Snapshot — Abhinandan Mohanty (1c826d5a)

Rollback anchor recorded before optimized rebuild. Read-only snapshot via PostgreSQL MCP.

## §1 Identity Confirmation (CLEAN — NO CONTAMINATION)
- chart_id: `1c826d5a-41cb-4450-b4dc-59d440e5f75a` ✓ (starts with 1c826d5a)
- SUN = Aquarius (Shatabhisha, Rahu lord) ✓
- MOON = Gemini (Ardra, Rahu lord) ✓
- Native (482012f1): SUN=Capricorn/MOON=Aquarius — DISTINCT ✓

## §2 Pre-Rebuild Row Counts (Rollback Anchor)
| Table | Row Count |
|---|---|
| chart_facts | 137,332 |
| chart_dashas | 538,337 |
| chart_divisionals | 20,877 |
| bodha_msr_signals | 64,726 |
| bodha_contradictions | 5,500 |
| bodha_cgm_nodes | 140 |
| bodha_chart_gestalt | 5 |
| bodha_pratijna | 0 (unbuilt — new asset) |
| kala_activation | 64,726 |
| kala_avadhi | 0 (unbuilt — new asset) |
| kala_taranga | 0 (unbuilt — new asset) |
| kala_bhavishya | 100 |
| kala_jivana_parva | 240 |
| phala_anchors | 400 |
| phala_pramana | 400 |
| phala_phaladesa | 7 |
| mimamsa_calibration | 0 (unscored — expected) |
| mimamsa_predictions | 400 |
| mimamsa_qa_eval | 5 |

## §3 Pre-Flight Audit Result: PASS (with WATCH item)

### Registry Counts: PASS
- Total assets: 91 (25 bg + 16 ga + 15 bo + 14 ka + 9 ph + 12 mi) ✓

### New Assets Wiring: PASS
| Asset | layer | scope | catalog_status | is_active | has_count_sql | depends_on |
|---|---|---|---|---|---|---|
| bo_pratijna | bodha | per_chart | CURRENT | true | YES | [bo_laksana, bo_sangati] |
| ka_avadhi | kala | per_chart | CURRENT | true | YES | [ka_yojaka, bo_pratijna] |
| ka_taranga | kala | per_chart | CURRENT | true | YES | [ka_avadhi, bo_pratijna] |

All new assets: 0 rows (unbuilt, expected) ✓

### WATCH: ga_structural 6cddc910 fix status
- bhava_arudha: 0 rows (MISSING — expected from 6cddc910 fix)
- karaka_web_per_varga: 0 rows (MISSING — expected from 6cddc910 fix)
- arudha_pada: 285 rows (present)
- swamsa_position: 120 rows (present)
- ga_structural last_built_at: 2026-06-30 (BEFORE 6cddc910 commit on 2026-07-04)
- JOB image status: uncertain — will verify during §4B ga_structural rebuild
- If bhava_arudha remains 0 after rebuild → JOB image stale → must rebuild JOB image (§6 path)

### Observation: ka_taranga→ka_avadhi chain
Brief says "both L3 new assets are leaves" but ka_taranga depends on ka_avadhi,
making ka_avadhi a mid-chain node (not a true leaf). ka_taranga IS the leaf.
Functional impact: none — DAG edges are correct; layer-scope rebuild handles ordering.
