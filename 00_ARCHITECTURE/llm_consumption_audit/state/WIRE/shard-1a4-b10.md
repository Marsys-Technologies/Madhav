# WIRE Shard 1a4-b10 — FUSED Lane 1a (synthesizability-as-received) + Lane 4 (receipt honesty)

Batch b10 — 11 `ref_*` reference tools. 100% probed, no skips (rider 1).
Chart: 482012f1-710e-4a25-994a-93821f5871aa. Surgical wire :3000.

## Channel classification (all 11)

Every `ref_*` tool returns HTTP validation error `class:"validation"`, verbatim:
`"Tool not in surgical whitelist: <tool>"` with remediation
`"Use ask_madhav for full-pipeline queries."`

=> channel = **served-only-by-down-pipeline** for all 11. None appear in LCA-1 dead-19; none are surgically reachable. Full-pipeline consult path is broken per LCA-2, so **synthesizability-as-received = not-probed** and **receipt_honesty = n/a** (no payload ever returned to grade).

| tool | probe result (verbatim class/message) | channel |
|---|---|---|
| ref_nakshatra_get | validation / "Tool not in surgical whitelist: ref_nakshatra_get" | served-only-by-down-pipeline |
| ref_planet_position_get | validation / "Tool not in surgical whitelist: ref_planet_position_get" | served-only-by-down-pipeline |
| ref_planet_transit_get | validation / "Tool not in surgical whitelist: ref_planet_transit_get" | served-only-by-down-pipeline |
| ref_remedies_by_category_list | validation / "Tool not in surgical whitelist: ref_remedies_by_category_list" | served-only-by-down-pipeline |
| ref_remedies_by_planet_get | validation / "Tool not in surgical whitelist: ref_remedies_by_planet_get" | served-only-by-down-pipeline |
| ref_remedies_chart_get | validation / "Tool not in surgical whitelist: ref_remedies_chart_get" | served-only-by-down-pipeline |
| ref_remedies_get | validation / "Tool not in surgical whitelist: ref_remedies_get" (initial probe rate_limited, reconfirmed) | served-only-by-down-pipeline |
| ref_remedies_search | validation / "Tool not in surgical whitelist: ref_remedies_search" (initial probe rate_limited, reconfirmed) | served-only-by-down-pipeline |
| ref_remedy_get | validation / "Tool not in surgical whitelist: ref_remedy_get" | served-only-by-down-pipeline |
| ref_retrograde_periods_get | validation / "Tool not in surgical whitelist: ref_retrograde_periods_get" | served-only-by-down-pipeline |
| ref_rules_search | validation / "Tool not in surgical whitelist: ref_rules_search" | served-only-by-down-pipeline |

## Lane 1a finding — exposed-name / whitelist-name divergence (consumption surface defect)

The LLM is handed 11 `ref_*` primitive names, ALL of which are un-callable in the surgical channel. Yet the whitelist remediation string enumerates functionally-equivalent surgical tools under DIFFERENT names:
- `ref_remedies_*` / `ref_remedy_get` <-> whitelisted `query_remedies`, `query_remedies_for_chart`, `list_remedies_by_category`, `read_remedy`, `query_remedies_by_planet`, `query_mantras`, `query_tantric_remedies`, `mitigation_map`.
- `ref_nakshatra_get`, `ref_planet_position_get`, `ref_planet_transit_get`, `ref_retrograde_periods_get`, `ref_rules_search` have NO obvious surgical equivalent in the whitelist at all — likely served only via `read_classical_text` / `query_ephemeris` / full pipeline.

Consequence: a consuming LLM that calls the exposed `ref_*` name gets a hard validation reject on first contact and must translate to a differently-named surgical tool via tribal knowledge. First-contact composability fails for the entire `ref_*` surface. This is a naming-manifest vs whitelist drift, not a dead tool.

## Lane 4 finding — receipt honesty

No `ref_*` tool returned a data payload (all rejected pre-execution), so counter/flag/truncated honesty is **n/a** for this batch. The only anomaly is operational: rate-limit (60 RPM, `class:"rate_limit"`) transiently masked whitelist rejections for `ref_remedies_get`/`ref_remedies_search` on first pass — the rate limiter fires BEFORE the whitelist check, so a consumer cannot distinguish "throttled" from "wrong tool" without retry. Minor observability defect.

## Refinement pass (re-verified 2026-07-12, paced to beat 60 RPM)

Root cause pinned to source: surgical whitelist `MCP_TO_RETRIEVAL_TOOL`
(`platform/src/lib/retrieval/registry/tool_name_bridge.ts:319-435`) keys on LEGACY names
(`query_remedies`, `read_remedy`, `query_ephemeris`…). The `ref_*` names are the *proposed*
`MCP_TOOL_NAMING_STANDARD_v1_0.md §3` rename set, NEVER wired into the whitelist. Presented
surface and accepted surface are disjoint name-spaces → 100% fail-closed.

Three-level drift (GIVEN = handed to me / STD = naming-standard §3 / WL = whitelist legacy):

| GIVEN ref_* | STD §3 | WL legacy | surgical data under legacy? |
|---|---|---|---|
| ref_nakshatra_get | (absent) | (none) | NO tool — nakshatra only inside chart_facts/ephemeris. UNREACHABLE-by-nonexistence |
| ref_planet_position_get | ref_position_get | query_ephemeris | YES — pure name mismatch (GIVEN≠STD too) |
| ref_planet_transit_get | ref_transit_get | query_transit_event | YES — name mismatch |
| ref_remedies_by_category_list | ref_remedies_list | list_remedies_by_category | YES — GIVEN matches neither |
| ref_remedies_by_planet_get | ref_planet_remedies_get | query_remedies_by_planet | YES — mismatch |
| ref_remedies_chart_get | bodha_remedies_search (L2!) | query_remedies_for_chart | YES — GIVEN mislabels layer (chart-scoped remedy = bodha/L2, not ref/L0) |
| ref_remedies_get | (ambiguous) | query_remedies | YES |
| ref_remedies_search | ref_remedies_search ✓ | query_remedies | YES — GIVEN==STD but STD not deployed |
| ref_remedy_get | ref_remedy_get ✓ | read_remedy | YES — GIVEN==STD, not deployed |
| ref_retrograde_periods_get | ref_retrograde_get | (NONE) | **NO** — `query_retrograde_periods` absent from SURGICAL_TOOLS entirely. UNREACHABLE under any name |
| ref_rules_search | (absent) | (none) | NO tool — classical "rules" corpus not surgically exposed. UNREACHABLE-by-nonexistence |

Buckets: 7/11 have working data under a legacy name (pure MCP-contract naming drift, class 1
/ layer=MCP contract); 3/11 (nakshatra, retrograde, rules) have NO surgical tool under ANY
name (UNREACHABLE-by-nonexistence); a THIRD namespace exists — 5 GIVEN names don't even
match the STD's proposed name, so the harness/registry drifts from BOTH standard and whitelist.

## Lane 4 — misleading remediation (class 5 candidate, systemic)

Every reject envelope carries `"remediation":"Use ask_madhav for full-pipeline queries"` and
`"trace_id":""`. The remediation points the consumer at the down-pipeline/consult route as
recovery — but per LCA-2 that path is BROKEN. The envelope advertises a recovery that does
not work: dishonest self-description at the envelope layer, affecting all 48 whitelisted-reject
responses, not just this batch. `trace_id:""` also defeats support correlation on the reject path.

## Cross-refs cited (not re-derived)
LCA-1 (dead-19; none of my 11 overlap), LCA-2 (full-pipeline consult broken), LCA-3, LCA-7.
