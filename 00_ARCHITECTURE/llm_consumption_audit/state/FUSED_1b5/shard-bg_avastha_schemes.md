# FUSED Lane 1b+5 shard — bg_avastha_schemes

- table: `bg_avastha_schemes`  families: 1  DB row counts: GLOBAL=35
- channel: **truly-UNREACHABLE**
- serving tool: `(none)`
- wire probe: `(none)` — NO tool (surgical or full-pipeline) references `bg_avastha_schemes` in the retrieval registry (grep of platform/src/lib/retrieval/ for avastha_schemes → 0 hits). L0 global reference substrate consumed internally by avastha writers; its COMPUTED products (per-graha baladi/jagradadi avastha) surface via chart_facts_query, but the scheme-definition table itself has no query surface.
- retrievability (1b): UNREACHABLE (direct) — reference substrate, not a per-chart consumption surface; likely by-design (low severity).
- fidelity (5): not-assessable — no wire value.

## Per-family rows

- {"row_id": "VF-3002", "family_key": "__table_row_count__=35", "channel": "truly-UNREACHABLE", "retrievability_verdict": "UNREACHABLE-reference-substrate (derived products reachable via chart_facts)", "fidelity_verdict": "not-assessable-no-wire-value", "derivation": "full per-family (single sentinel family VF-3002 __table_row_count__; grep-confirmed no serving tool)"}
