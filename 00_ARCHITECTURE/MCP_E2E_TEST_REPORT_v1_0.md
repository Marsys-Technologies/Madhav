---
artifact: MCP_E2E_TEST_REPORT
canonical_id: MCP_E2E_TEST_REPORT
version: 1.0
status: CURRENT — end-to-end LLM-as-client test of the live MCP (completeness + retrievability + synthesis)
created: 2026-07-02
author: Cowork (acting AS the external LLM client, live over the MCP connector) — for native Abhisek Mohanty
parent: MCP_SYSTEM_AUDIT_FINDINGS_v1_0 (this extends it with post-fix live E2E state)
instrument: live prod amjis-mcp (revision 7d1c2135 era), this Cowork connector session
scope: test the WHOLE reachable system for full coverage / accessibility / no hindrance to deep synthesis;
  list gaps to remediate.
---

# MCP END-TO-END TEST — LLM-AS-CLIENT (completeness · retrievability · synthesis)

> I connected as the external LLM and exercised the live system after the W1→W3R fix campaign. Verdict:
> **the DATA-RETRIEVAL stack is now largely reachable and correct end-to-end (a big improvement) — but two
> things block "synthesis beyond human cognition": (1) the APEX reasoning-unit tools are not reachable from
> this connector session, and (2) even where data serves richly, the SALIENCE + SYNTHESIS judgment layer is
> unbuilt (Wave 5). So the pipes now carry the water; the water is not yet turned into acharya-grade wine.**

## §1 — What is NOW reachable + working (post-fix; confirmed live this session)
| Tool | Result | Note |
|---|---|---|
| list_my_charts | ✅ | 4 charts by name |
| select_chart / list_my_sessions / recall_session | ✅ | M2/M3 session layer works |
| get_chart_orientation | ✅ | under lahiri_chitrapaksha: 12,954 signals, 90 yogas, 1,034 contradictions, convergence per domain |
| get_signals | ✅ | rich, cited, two-pass-verified |
| get_chart_quality | ✅ | scorecard: 64,765 signals, 140 CGM nodes, 365 edges, 94.9% verified |
| get_domain_reading | ✅ (bounded) | 17MB→19.8KB after F-021R-b; lenses+refs capped; drill URI provided |
| get_dashas | ✅ | multi-system (ashtottari/yogini/kalachakra/vimshottari/chara), cited, lord-condition embedded |
| query_planet_position / transit / retrograde | ✅ | L0 ephemeris, real Swiss-Ephemeris data |
| compute_natal_positions | ✅✅ | CORRECT vs FORENSIC (Sun Cap, Moon Purva Bhadrapada, Lagna Aries) |
| resolve_entity | ✅ | Shani→saturn, cited BPHS (post GET→POST + register fix) |
| list_assets | ✅ | full 85-asset catalog |
| lel_query | ✅ | clean-empty + no-leakage discipline |
| get_remedies (chart-scoped) | ✅ (data) | rich prescriptions — BUT degenerate scores (F-007) |
**Net: the L0/L1/L2 + session/entitlement/ephemeris/dasha/remedy-corpus surfaces are reachable and returning
real, cited, mostly-correct data.** This is a major step up from the pre-campaign state where ~half was dark.

## §2 — THE COVERAGE GAPS (what still blocks full E2E synthesis) — the remediation list

### G-A [CRIT — connector] APEX reasoning-unit tools NOT reachable from this session
`assess_marriage/career/health/wealth`, `yoga_activation_by_dasha`, `query_chart_facts`, `vector_search`,
`get_cgm_subgraph` are registered SERVER-SIDE (W2.5) but do NOT appear in this Cowork connector's tool list even
after a refresh. A tool-list refresh did not propagate; the Cowork MCP connector appears to cache its toolset at
connection. **Remediate:** fully REMOVE + RE-ADD the MCP connector in Cowork (not just refresh), OR confirm the
server advertises the new tools in tools/list (MCP spec: server should emit a tools/list_changed notification on
registration). Until then the G10 "superlative insight" apex cannot be witnessed from an LLM client — this is
the single biggest blocker to the stated goal. **This is a serving/connector issue, not a data issue.**

### G-B [CRIT — astrological model, Wave 5] SALIENCE is degenerate + not acharya-relevant
Confirmed again live: for career, the top signals are all Saturn ashtakavarga bindu-counts (identical salience
2.326672), 0 yogas / 0 tenth-lord / 0 raja-yoga. Even with data flowing, the RANKING surfaces trivia over
chart-defining factors. `signature_tier` is 100% background (unused). **This is THE gap between "retrieves data"
and "synthesis beyond human cognition" — a mechanical top-N of varga tallies is not acharya-grade.** Remediate
in the beyond-acharya strategic track (salience re-model + activate signature_tier; native-judgment weighting).

### G-C [CRIT — synthesis, Wave 5] NO synthesis/verdict is produced
get_domain_reading (even bounded) returns ranked ingredients + counts, no reconciled reading. There is no tool
that WEIGHS + RECONCILES + delivers a judgment. The apex assess_* tools are meant to — but see G-A (unreachable)
and G-B (they'd inherit the broken salience). **Remediate:** the synthesis contract (Wave 5) + reach the apex tools.

### G-D [HIGH — grounding] machine-grounding 91.5% orphaned (DEFECT-001)
Every served response self-flags: constituent_facts_array → L1 fact_ids resolve at only 8.5%. Human citations
present; machine provenance chain broken (L1 SHA rebuild). **Remediate:** the MSR rebuild against current L1
(request filed: REQUEST_RETRIEVAL_MSR_REBUILD_FOR_MCP_G10). Prerequisite for trustable "prophecy/guidance."

### G-E [HIGH — data model] domain filter is inert
get_domain_reading self-reports `bodha_question_lenses has no domain column; lenses returned chart-wide`. A
career query returns all 12 life areas. **Remediate:** add the domain dimension to the lens schema (Wave 5).

### G-F [MED — contract, NEW this session] query_remedies_for_chart is UNCALLABLE
The entitlement gate returns CHART_REQUIRED, but the tool's schema has NO chart_id param (only affliction+top_k)
— it's a chart-agnostic corpus lookup that got over-gated. Contract contradiction = dead tool. **Remediate:**
either exempt this chart-agnostic tool from the chart_id gate, or add chart_id to its schema. (The M0 gate
over-reached onto a corpus tool.)

### G-G [MED — dasha correctness, NEW this session] get_dashas returns pre-birth rows + wrong default
Requesting 6 dasha rows returned ashtottari periods starting 1950 (native born 1984) — the sort/filter returns
earliest-across-all-systems, not the birth-anchored active sequence; and it defaults to ashtottari, not
vimshottari (the primary system a client expects). Also lord_natal_shadbala_total is null (strength link
unpopulated). **Remediate:** default to vimshottari, birth-anchor + order by date, populate the shadbala link.

### G-H [HIGH — degenerate scoring, standing] remedy + salience scores collapse to constants
get_remedies gives every planet resonance=weakness=0.28; salience collapses to ~3 constants. Prioritization is
meaningless. **Remediate:** real chart-specific scoring (Wave 5 / degenerate-distribution guard).

### G-I [LOW — UX, standing] no working verbosity/discovery polish
response_format digest still returns near-full payloads on some tools; some error envelopes inconsistent.
Mostly addressed by W3R for get_domain_reading; sweep the rest.

## §3 — THE HONEST VERDICT ON THE GOAL
- **Completeness of data:** GOOD — L0–L2 richly built + reachable; 85 assets catalogued; natal facts correct.
- **Retrievability:** MUCH IMPROVED — the previously-dark surfaces serve; the remaining reach-gap is G-A
  (apex tools not in this connector) + G-F (one over-gated tool).
- **Accessibility to current data into all assets:** PARTIAL — most assets reachable; L4 phala + apex synthesis
  tools need the connector re-add (G-A) + confirmation of Wave-4 phala deploy.
- **No hindrance to synthesis beyond human cognition:** NOT YET. Two hard blockers: (G-A) can't reach the apex
  synthesis tools from an LLM client; (G-B/G-C) even reached, the salience+synthesis judgment layer is unbuilt.
  The system today is an excellent, cited, complete DATA-RETRIEVAL instrument — it is not yet a beyond-acharra
  SYNTHESIS instrument. The distance is exactly Wave 5 (astrological model) + G-A (connector reach).

## §4 — REMEDIATION PRIORITY (what to do, in order)
1. **G-A** (connector re-add / tools/list_changed) — unblocks witnessing the apex tools. Fast; do first.
2. **G-F, G-G** (over-gated remedy tool; dasha default/sort/shadbala) — small serving/contract fixes; fold into
   the next Claude Code pass.
3. **G-D** (MSR rebuild) — the machine-grounding prerequisite; retrieval fork.
4. **G-B, G-C, G-E, G-H** (salience re-model + synthesis contract + domain-filter schema + real scoring) —
   the beyond-acharya strategic track (Wave 5). This is the real long pole and needs native astrological input.

*End of MCP_E2E_TEST_REPORT v1.0 — the pipes carry the water; Wave 5 + the connector reach turn it into wine.*
