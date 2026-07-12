# FUSED 1b+5 shard — bg_transit_vedha

families_total: 1 | channel: truly-UNREACHABLE | members_sampled: 1 | per_family_rows_written: 1

DB-truth: `SELECT count(*) FROM bg_transit_vedha` → 33 (matches ledger family_key `__table_row_count__=33`, VF-3020). Columns: primary_transit_house, vedha_house, vedha_type, primary_graha, vedha_graha, classical_note, classical_citation, created_at, id — Vedha (transit-obstruction) pair rules, classical Gochara doctrine.
Serving check: ZERO manifest reference as a served table; NOT in ALIVE surgical; NOT in DEAD-19. Consumed only by L0/L3 transit compute (l0_transit.py, ka_sangam/ka_yojaka engines) to apply vedha cancellation in per-chart transit windows. No tool emits the 33 vedha-pair rows. asset_registry count_sql = cockpit stat. No wire path → no diff possible.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| __table_row_count__=33 | truly-UNREACHABLE | UNREACHABLE (class 1) — vedha-pair rule catalog served by no tool | N/A — no wire path, diff impossible | path-grade(exemplar=__table_row_count__=33) + member-confirmation (family_count=1) |

Finding: lane 1b, class 1 UNREACHABLE, severity LOW-MEDIUM. Vedha obstruction-pair rules (acharya-citable Gochara doctrine) not retrievable; only their applied effect surfaces in derived transit windows. Suspected layer: serving-query / MCP contract. Dedupe: new (vedha-config UNREACHABLE).
