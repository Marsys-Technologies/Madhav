# FUSED 1b+5 shard — bg_shashtiamsha_deities

families_total: 1 | channel: truly-UNREACHABLE | members_sampled: 1 | per_family_rows_written: 1

DB-truth: `SELECT count(*) FROM bg_shashtiamsha_deities` → 60 (matches ledger family_key `__table_row_count__=60`, VF-3015). Columns: amsa_number, quality, deity_name, classical_citation, rule_notes — a classically-meaningful BPHS Ch.7 D60 reference catalog.
Serving check: ZERO manifest reference as a served table; NOT in ALIVE surgical list; NOT in DEAD-19. Consumed only build-time by `ga_writers/ga_vargas_writer.py` (`SELECT amsa_number, quality, deity_name FROM bg_shashtiamsha_deities`, line 516) to assign the D60 deity/quality of a chart's divisional placement into `chart_divisionals` (that DERIVED per-chart value is reachable via `divisional_query`; the 60-row catalog itself is never emitted). Registered in asset_registry_seed only as a build asset (count_sql = cockpit stat, not a serving path). No wire path → no wire-fidelity diff possible.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| __table_row_count__=60 | truly-UNREACHABLE | UNREACHABLE (class 1) — 60-row D60 deity reference catalog served by no tool | N/A — no wire path, diff impossible | path-grade(exemplar=__table_row_count__=60) + member-confirmation (family_count=1, whole table = the family) |

Finding: lane 1b, class 1 UNREACHABLE, severity LOW-MEDIUM. Reference catalog (classical D60 deity/quality mapping, incl. which amsas are kroora vs soumya) cannot be retrieved or cited by a consuming LLM; only its per-chart derived effect surfaces (via divisional_query). Suspected layer: MCP contract / serving-query (no reference-lookup tool fronts L0 catalogs). Dedupe: distinct from R-37..R-48 (transit/reference-catalog UNREACHABLE, not signal/discovery drowning).
