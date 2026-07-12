# WIRE shard-1a4-b9 — FUSED Lane 1a (synthesizability-as-received) + Lane 4 (receipt honesty)

Worker probe of 11 assigned tools. 100% probed, no skips. Surgical wire:
`POST http://localhost:3000/api/mcp/primitives/<tool>` with audit headers, chart_id=482012f1-710e-4a25-994a-93821f5871aa.

## Channel verdict: ALL 11 = served-only-by-down-pipeline

Every one of the 11 assigned tools returned an identical surgical rejection:

```
{"ok":false,"trace_id":"","error":{"class":"validation",
"message":"Tool not in surgical whitelist: <tool>",
"remediation":"Use ask_madhav for full-pipeline queries. Surgical primitives are: ..."}}
```

Per task rider: `"Tool not in surgical whitelist"` => channel=served-only-by-down-pipeline;
the full pipeline (`ask_madhav`) consult path is BROKEN per LCA-2. synthesizability=not-probed
(cannot grade first-contact payload — tool never reachable on the surgical wire). receipt_honesty=n/a
(no payload with counters/flags to audit).

| tool | channel | synth | receipt | note |
|---|---|---|---|---|
| recall_session | served-only-by-down-pipeline | not-probed | n/a | full-pipeline-only |
| record_outcome | served-only-by-down-pipeline | not-probed | n/a | full-pipeline-only |
| ref_aspects_at_time_get | served-only-by-down-pipeline | not-probed | n/a | full-pipeline-only |
| ref_classical_citation_get | served-only-by-down-pipeline | not-probed | n/a | full-pipeline-only; twin of whitelisted `read_classical_text` |
| ref_dasha_systems_get | served-only-by-down-pipeline | not-probed | n/a | full-pipeline-only |
| ref_dignity_reference_get | served-only-by-down-pipeline | not-probed | n/a | full-pipeline-only |
| ref_doshas_get | served-only-by-down-pipeline | not-probed | n/a | full-pipeline-only |
| ref_entities_list | served-only-by-down-pipeline | not-probed | n/a | full-pipeline-only; twin of whitelisted `list_entities` |
| ref_entity_resolve | served-only-by-down-pipeline | not-probed | n/a | full-pipeline-only; twin of whitelisted `resolve_entity` |
| ref_ephemeris_year_get | served-only-by-down-pipeline | not-probed | n/a | full-pipeline-only; twin of whitelisted `query_ephemeris` |
| ref_mantras_get | served-only-by-down-pipeline | not-probed | n/a | full-pipeline-only; twin of whitelisted `query_mantras`/`query_remedial_mantras` |

## Lane 1a finding — NAMESPACE FORK: entire `ref_*`/session tool class is severed from the surgical wire

All 11 tools exposed to the LLM consumer (the `ref_*` reference-lookup family + `recall_session`/`record_outcome`
session tools) are absent from the 48-name surgical whitelist. For at least 5 of them a **functionally equivalent
twin exists in the whitelist under a different name**:
- `ref_entity_resolve` (mine) vs `resolve_entity` (whitelisted)
- `ref_entities_list` (mine) vs `list_entities` (whitelisted)
- `ref_mantras_get` (mine) vs `query_mantras` / `query_remedial_mantras` (whitelisted)
- `ref_ephemeris_year_get` (mine) vs `query_ephemeris` (whitelisted)
- `ref_classical_citation_get` (mine) vs `read_classical_text` (whitelisted)

The consumer is handed `ref_*`-named handles that the surgical layer does not recognize; the equivalent
capability lives behind a differently-named whitelist entry the consumer was NOT handed. A first-contact LLM
following the given tool names hits a hard validation wall on 100% of calls with no hint that a renamed twin exists
on the surgical path. Composability-to-one-cited-sentence on first contact = 0/11. This is a synthesizability-as-received
FAIL for the whole reference/session surface, driven by name drift between the exposed toolset and the surgical whitelist.

## Lane 4 finding — receipt honesty n/a but rate-limiter honesty confirmed

No payloads with counters/flags/truncated fields were obtainable, so receipt honesty cannot be scored for any of the 11
(distinct from LCA-7 msr_sql `truncated=False` dishonesty, which is a different tool). Incidental observation: the surgical
gateway enforces a 60 RPM limit and returns an honest `rate_limit`-class error with accurate remediation when tripped —
the gateway's own error receipts (validation + rate_limit classes) are HONEST and self-describing. The dishonesty in this
system is downstream in payload counters (LCA-7), not in the gateway envelope.
