# FUSED 1b+5 shard — bg_transit_av_gates

families_total: 1 | channel: truly-UNREACHABLE | members_sampled: 1 | per_family_rows_written: 1

DB-truth: `SELECT count(*) FROM bg_transit_av_gates` → 8 (matches ledger family_key `__table_row_count__=8`, VF-3016). Columns: id, house_from_moon, min_av_score, min_sav_score, kakshya_lord, gate_kind, graha, effect, classical_citation, rule_notes — Ashtakavarga transit-gate thresholds (AV/SAV score gates on Gochara), classical doctrine.
Serving check: ZERO manifest reference as a served table; NOT in ALIVE surgical; NOT in DEAD-19. Consumed only by L0/L3 transit compute to gate transit-phala by ashtakavarga strength. No tool emits the 8 gate rows; effect only surfaces in derived transit windows. asset_registry count_sql = cockpit stat. No wire path → no diff possible.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| __table_row_count__=8 | truly-UNREACHABLE | UNREACHABLE (class 1) — ashtakavarga transit-gate config served by no tool | N/A — no wire path, diff impossible | path-grade(exemplar=__table_row_count__=8) + member-confirmation (family_count=1) |

Finding: lane 1b, class 1 UNREACHABLE, severity LOW. Ashtakavarga transit-gate thresholds not retrievable. Suspected layer: serving-query / architecture (config by design). Dedupe: new (av-gate-config UNREACHABLE).
