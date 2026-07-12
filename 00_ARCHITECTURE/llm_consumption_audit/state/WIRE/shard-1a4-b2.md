# WIRE shard-1a4-b2 — FUSED Lane 1a (synthesizability-as-received) + Lane 4 (receipt honesty)

Charter: LLM_CONSUMPTION_AUDIT_CHARTER v1.1 §7.2 (Lane 1a), §7.5 (attribution).
Probe method: surgical wire POST http://localhost:3000/api/mcp/primitives/<tool>, chart 482012f1-…
Cross-refs cited (not re-derived): LCA-1 (DEAD-19), LCA-2 (consult broken → served-only-by-down-pipeline), LCA-3 (query_chart_facts defects), LCA-7 (msr_sql dishonest).

## Census — 11/11 probed, 0 skipped (rider 1)

Every one of the 11 assigned tool names is REJECTED by the surgical wire with an identical
`{"ok":false,...,"class":"validation","message":"Tool not in surgical whitelist: <tool>"}`
envelope. None of the 11 names appears anywhere in the whitelist the error enumerates, and
none is in the DEAD-19 list (LCA-1). They are therefore full-pipeline-only aliases: the only
consumption path is `ask_madhav` (the down pipeline), whose consult is broken per LCA-2.

Consequence for grading: synthesizability-as-received (§7.2) is a FIRST-CONTACT-of-a-PAYLOAD
grade; no data payload can be obtained surgically for any of these 11, so synthesizability =
**not-probed** and receipt_honesty = **n/a** for all 11 (no counters/flags/counts ever
returned to grade). Channel = **served-only-by-down-pipeline** for all 11.

| tool | channel | synth | receipt | verbatim probe result |
|---|---|---|---|---|
| chart_snapshot | served-only-by-down-pipeline | not-probed | n/a | `"Tool not in surgical whitelist: chart_snapshot"` |
| compute_natal_positions | served-only-by-down-pipeline | not-probed | n/a | `"Tool not in surgical whitelist: compute_natal_positions"` |
| ephemeris_cache_year | served-only-by-down-pipeline | not-probed | n/a | `"Tool not in surgical whitelist: ephemeris_cache_year"` |
| find_verses_about | served-only-by-down-pipeline | not-probed | n/a | `"Tool not in surgical whitelist: find_verses_about"` |
| ganita_chart_facts_get | served-only-by-down-pipeline | not-probed | n/a | `"Tool not in surgical whitelist: ganita_chart_facts_get"` |
| ganita_condition_get | served-only-by-down-pipeline | not-probed | n/a | `"Tool not in surgical whitelist: ganita_condition_get"` |
| ganita_dasha_periods_get | served-only-by-down-pipeline | not-probed | n/a | `"Tool not in surgical whitelist: ganita_dasha_periods_get"` |
| ganita_dashas_get | served-only-by-down-pipeline | not-probed | n/a | `"Tool not in surgical whitelist: ganita_dashas_get"` |
| ganita_nakshatra_get | served-only-by-down-pipeline | not-probed | n/a | `"Tool not in surgical whitelist: ganita_nakshatra_get"` |
| ganita_natal_positions_compute | served-only-by-down-pipeline | not-probed | n/a | `"Tool not in surgical whitelist: ganita_natal_positions_compute"` |
| ganita_positions_get | served-only-by-down-pipeline | not-probed | n/a | `"Tool not in surgical whitelist: ganita_positions_get"` |

## Findings

### F-1a-b2-01 (lane 1a) — 11 assigned MCP tool names are un-probeable surgically; first-contact synthesizability cannot be graded because the only path is the broken down-pipeline
- class: 8 (UN-SYNTHESIZABLE AT SCALE) primary; overlaps 1 (UNREACHABLE via surgical plane)
- severity: HIGH
- suspected layer: MCP contract / serving-query
- Evidence: all 11 return `class:"validation" / "Tool not in surgical whitelist: <tool>"`.
  Remediation string self-directs to `ask_madhav` (full pipeline). Per LCA-2 the full-pipeline
  consult is broken, so these 11 surfaces have NO working first-contact path an LLM can grade or
  synthesize from. Whitelist enumerated 60 surgical primitives; NONE of the 11 ganita_*/chart/
  ephemeris/verse aliases is among them.

### F-1a-b2-02 (lane 4) — remediation self-description is HONEST but points at a non-functional path
- class: (receipt honesty pass) — the error envelope's own claim ("not in surgical whitelist",
  "use ask_madhav") is factually accurate: these tools genuinely are not surgical. No dishonest
  counter/flag on the ERROR envelope itself. receipt_honesty = HONEST for the envelope.
- BUT: the honest pointer targets the LCA-2-broken down pipeline. Honest self-description of a
  dead onward path is a coverage-honesty note, not a class-5 defect. Logged for §8 criterion-4
  coverage honesty. severity: LOW (informational).
- Evidence: `"remediation":"Use ask_madhav for full-pipeline queries."`

## RESUME
Shard COMPLETE. 11/11 probed. 2 findings. No partial rows.
