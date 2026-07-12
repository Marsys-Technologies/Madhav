# FUSED 1b+5 shard — bg_transit_moorti

families_total: 1 | channel: truly-UNREACHABLE | members_sampled: 1 | per_family_rows_written: 1

DB-truth: `SELECT count(*) FROM bg_transit_moorti` → 27 (matches ledger family_key `__table_row_count__=27`, VF-3018). Columns: nakshatra_offset, quality_tier, moorti_name, phala_brief, classical_citation, rule_notes — Vedha/Moorti-nirnaya reference (nakshatra-offset → moorti quality/phala), classical Gochara doctrine.
Serving check: ZERO manifest reference as a served table; NOT in ALIVE surgical; NOT in DEAD-19. Consumed only by L0/L3 transit compute (l0_transit.py, ka_sangam/ka_yojaka). No tool emits the 27 moorti rows; effect only surfaces in derived transit windows. asset_registry count_sql = cockpit stat. No wire path → no diff possible.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| __table_row_count__=27 | truly-UNREACHABLE | UNREACHABLE (class 1) — moorti-nirnaya reference served by no tool | N/A — no wire path, diff impossible | path-grade(exemplar=__table_row_count__=27) + member-confirmation (family_count=1) |

Finding: lane 1b, class 1 UNREACHABLE, severity LOW. Moorti-nirnaya reference catalog not retrievable. Suspected layer: serving-query. Dedupe: new (moorti-config UNREACHABLE).
