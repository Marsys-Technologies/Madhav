# FUSED 1b+5 shard — bg_transit_rules

families_total: 1 | channel: truly-UNREACHABLE | members_sampled: 1 | per_family_rows_written: 1

DB-truth: `SELECT count(*) FROM bg_transit_rules` → 57 (matches ledger family_key `__table_row_count__=57`, VF-3019). Columns: id, primary_house, vedha_house, classical_citation, rule_notes, phala, rule_type, graha — classically-cited Gochara phala rules (transit house → phala per graha).
Serving check: ZERO manifest reference as a served table; NOT in ALIVE surgical; NOT in DEAD-19. Consumed only by the `bg_transit_rules` build writer (`writers/bg_transit_rules.py`) and downstream L3 Kala engines (ka_sangam/ka_yojaka) which USE the rules to compute per-chart transit phala. asset_registry_seed registers it as a build asset (count_sql = cockpit stat). No tool emits the 57 rule rows. No wire path → no diff possible.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| __table_row_count__=57 | truly-UNREACHABLE | UNREACHABLE (class 1) — 57-row Gochara phala rule catalog served by no tool | N/A — no wire path, diff impossible | path-grade(exemplar=__table_row_count__=57) + member-confirmation (family_count=1) |

Finding: lane 1b, class 1 UNREACHABLE, severity LOW-MEDIUM. Classically-cited transit phala rules (an acharya-citable body of Gochara doctrine) not retrievable; only derived per-chart transit phala surfaces. Suspected layer: serving-query / MCP contract. Dedupe: new (transit-rules UNREACHABLE).
