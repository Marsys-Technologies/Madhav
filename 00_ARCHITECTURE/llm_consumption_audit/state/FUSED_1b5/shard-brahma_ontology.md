# FUSED 1b+5 shard — brahma_ontology (1 family)

DB truth: `SELECT count(*) FROM brahma_ontology` = 652 rows across 15 entity_classes
(yoga 175, concept 136, dosha 79, karaka 77, domain 45, nakshatra 27, dasha_system 19,
text 15, aspect_type 13, remedy_type 12, house 12, sign 12, planet 11, upagraha 11, school 8).

Serving tool (ALIVE, whitelisted): `list_entities` (also `resolve_entity`). CONFIRMED reachable-surgical.
Wire call: POST /api/mcp/primitives/list_entities body {"params":{}} (header X-MCP-Chart-Id=482012f1) → ok:true.

WIRE probe: 19,605 bytes, returns only 100 rows (default limit 100; code hard-cap `Math.min(limit ?? 100, 500)`),
ORDER BY entity_class, canonical_name_en. First-100 = aspect_type(13) + concept(87) ONLY.
Entire entity_classes silently dropped from default response: dosha, domain, dasha_system, house,
karaka, nakshatra, planet, remedy_type, school, sign, text, upagraha, yoga (552 rows). No
"more_available" flag / total-count disclosure in the payload.

FIDELITY (Lane 5): returned rows match DB exactly (canonical_id, entity_class, canonical_name_en/sa,
synonyms) — no value corruption. Fidelity = PASS on the 100 delivered.
RETRIEVABILITY (Lane 1b): DEGRADED. Default unfiltered call drops 552/652 with no disclosure; hard
cap 500 < 652 so full catalog is NOT enumerable in a single unfiltered call. Full enumeration is
possible only via 15 entity_class-filtered calls (undocumented requirement). failure_mode=
budget_ceiling_silently_discards_row. Class 7 (DROWNED) / 6 (undisclosed budget cap).

| family_key | channel | retrievability | fidelity | derivation |
|---|---|---|---|---|
| __table_row_count__=652 | reachable-surgical | DEGRADED (budget-ceiling: 100 of 652 default, 500 hard-cap, whole entity_classes silently dropped, no disclosure) | PASS (delivered rows == DB) | path-grade(exemplar=__table_row_count__=652) sole family; full-depth fused probe |
