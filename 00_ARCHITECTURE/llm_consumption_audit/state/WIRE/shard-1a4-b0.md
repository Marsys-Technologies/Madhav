# WIRE shard-1a4-b0 — FUSED Lane 1a (synthesizability-as-received) + Lane 4 (receipt honesty)

Batch b0 tools (11): apex_career_assess, apex_health_assess, apex_marriage_assess,
apex_wealth_assess, assess_career, assess_health, assess_marriage, assess_wealth,
asset_registry_all, asset_registry_l0, bodha_chart_digest_get.

Chart: 482012f1-710e-4a25-994a-93821f5871aa. Surgical wire POST
http://localhost:3000/api/mcp/primitives/<tool>. 100% probed (rider 1), no skips.

## Census result — UNIFORM

**All 11 tools → channel = served-only-by-down-pipeline.** Every one returns HTTP 400,
`ok:false`, `error.class="validation"`:

> `{"ok":false,"trace_id":"","error":{"class":"validation","message":"Tool not in surgical whitelist: <tool>","remediation":"Use ask_madhav for full-pipeline queries. Surgical primitives are: query_chart_facts, query_signals, ...}}`

None of the 11 appear in the surgical whitelist (48 primitives, enumerated in the error
payload). None appear in the LCA-1 DEAD-19 registry-not-found set either — so these are NOT
dead; they are full-pipeline-only tools whose only serving path is `ask_madhav`, the
down/broken consult pipeline (LCA-2). Per rider protocol: synthesizability = **not-probed**
(consult broken), receipt_honesty = **n/a** (no payload emitted on the surgical channel).

### Per-tool channel table
| tool | channel | synthesizability | receipt_honesty |
|---|---|---|---|
| apex_career_assess | served-only-by-down-pipeline | not-probed | n/a |
| apex_health_assess | served-only-by-down-pipeline | not-probed | n/a |
| apex_marriage_assess | served-only-by-down-pipeline | not-probed | n/a |
| apex_wealth_assess | served-only-by-down-pipeline | not-probed | n/a |
| assess_career | served-only-by-down-pipeline | not-probed | n/a |
| assess_health | served-only-by-down-pipeline | not-probed | n/a |
| assess_marriage | served-only-by-down-pipeline | not-probed | n/a |
| assess_wealth | served-only-by-down-pipeline | not-probed | n/a |
| asset_registry_all | served-only-by-down-pipeline | not-probed | n/a |
| asset_registry_l0 | served-only-by-down-pipeline | not-probed | n/a |
| bodha_chart_digest_get | served-only-by-down-pipeline | not-probed | n/a |

## Findings

### F-1a4-b0-1 (lane 1a, class 1 UNREACHABLE, HIGH)
The four highest-value consumer-facing domain-assessment tools `apex_{career,health,
marriage,wealth}_assess` are not reachable on the surgical channel — served only by the
full pipeline (`ask_madhav`), which is the broken consult path per LCA-2. A consuming LLM
asking a domain question (career/health/marriage/wealth — the exact §8 approved-question
themes) has NO working retrieval path to these purpose-built assessors. First-contact
synthesizability is therefore un-obtainable: the assessment never arrives.

### F-1a4-b0-2 (lane 1a, class 1 UNREACHABLE, HIGH)
A second, parallel family `assess_{career,health,marriage,wealth}` covers the identical four
domains and is ALSO full-pipeline-only. Two tool families for the same four life domains
(`apex_*_assess` vs `assess_*`) is a duplication/INCONSISTENT smell (class 3 candidate):
which is authoritative is undiscoverable from the surgical wire, and neither is reachable.
Root-cause + de-dup is a serving-contract finding — surface for Fable 5.

### F-1a4-b0-3 (lane 1a, class 1 UNREACHABLE, MEDIUM)
`asset_registry_all` and `asset_registry_l0` — the self-describing capability/inventory
surfaces a consuming LLM would use to learn what the system holds (Charter §2.1 source (2))
— are full-pipeline-only. The system cannot describe its own asset inventory over the
surgical channel; census-by-tool is impossible without the down pipeline.

### F-1a4-b0-4 (lane 1a, class 1 UNREACHABLE, MEDIUM)
`bodha_chart_digest_get` — the L2 Bodha whole-chart digest, the natural B.11 Whole-Chart-Read
entry surface — is full-pipeline-only. The one tool that would deliver a composed chart
digest to a first-contact consumer is unreachable surgically; consumers must fall back to
raw primitives and self-compose, which is exactly the un-synthesizable-at-scale hazard.

### Lane 4 (receipt honesty)
Per-tool receipt_honesty = n/a for all 11: no tool emitted a data payload with
receipts/counters/flags on the surgical channel (all HTTP 400 validation errors). The
message field correctly names the rejected tool.

### F-4-b0-5 (lane 4, class 5 DISHONEST SELF-DESCRIPTION, MEDIUM) — CORRECTS prior "envelope honest" note
The `remediation` string's advertised "Surgical primitives are: ..." list is DISHONEST: it
enumerates 17 of the 19 DEAD-19 tools (LCA-1) as if they were live surgical primitives —
query_tara_balam, query_chandra_balam, jaimini_chara_dasha, jaimini_chara_dasha_full,
temporal, kp_query, query_kp_ruling_planets, pattern_register, resonance_register,
cluster_atlas, contradiction_register, query_ucn_walk, query_cdlm_lookup, query_rm_walk,
query_jaimini_drishti, timeline_query, query_signal_state. A consuming LLM that follows this
help text to those "primitives" gets "Retrieval tool not found in registry" (DEAD-19). The
self-describing envelope contradicts reality → class 5. (Only cgm_graph_walk +
multi_school_signal_lookup of DEAD-19 are absent from the advertised list.) Cross-ref LCA-1.

## Cross-refs (cited, not re-derived)
- LCA-2: full-pipeline consult path broken → served-only-by-down-pipeline tools cannot be exercised.
- LCA-1: DEAD-19 set — confirmed none of these 11 belong to it (distinct failure mode).
- Rate limit: surgical wire enforces 60 RPM (`error.class=rate_limit`, HTTP 429); pace probes.
