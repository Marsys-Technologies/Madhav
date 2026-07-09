---
canonical_id: MCP_USAGE_GUIDE
version: 1.0
status: CURRENT
created: 2026-07-09
author: Claude Code (executing CLAUDECODE_BRIEF_R5_1_MCP_CONSUME_v1_0.md C5)
audience: the native (Abhisek), using an MCP-connected chat client directly
---

# MCP USAGE GUIDE — how to actually talk to the instrument

Native-facing, ~1 page. For the technical/governance record, see `R5_1_MCP_CONSUME_ACCEPTANCE_v1_0.md`.

## The two charts
- **Native (you):** `482012f1-710e-4a25-994a-93821f5871aa` — calibrated (57 corroborating life events).
- **Abhinandan:** `1c826d5a-41cb-4450-b4dc-59d440e5f75a` — structural (no LEL corroboration yet).

Every question needs a `chart_id`. Say "for Abhinandan" or give the id directly; otherwise the client should ask which chart, not guess.

## Question patterns that work well
| You want to know... | Ask like this | Tool it reaches |
|---|---|---|
| A single fact ("what's my lagna / Sun sign / current dasha") | Short, direct question | `query_chart_facts` |
| How a life area is going ("how is my career/marriage/health") | Name the domain | `judgment_query` — the full classical bhava-adhyaya recipe in one call |
| A planet's overall condition ("how strong is my Saturn really") | Name the graha | `graha_portrait` |
| Timing of an event ("will I change jobs, when") | Name domain + rough horizon | `pact_query` — chains promise→confirmation→activation→trigger, halts honestly if a stage isn't confirmed |
| A good window to act ("when should I get married / travel / start a business") | Name the action + date range (≤90 days) | `muhurta_finder` — real panchanga-based ranked windows, honest empty-with-reason outside the ~12-month forward window |
| A quick visual of the chart | "show me my chart" | `chart_snapshot` — compact 12-rashi grid, add "and navamsa" for D9 too |
| Whether a classical claim is true | "is it true that..." | pairs with `judgment_query`/`get_classical_citation` for verification |

## Reading responses
- **`chart_header`** — always check this first. If it doesn't say Aries lagna / Capricorn Sun (you) or Aries lagna 23°32′ (Abhinandan), something's wrong upstream — don't trust the rest of the answer.
- **`verdict`/`receipt`** — the actual classical reasoning chain (which bhava/bhavesha/karaka/dashas were consulted).
- **`judgment_flags`** — honesty markers. If you see something like `bhanga_not_checked` or `time_sensitive_low_confidence`, that's the instrument telling you what it couldn't fully verify — not a bug, a feature.
- **`drill_pointers`** — most responses are trimmed for chat (≤8-12KB). Pointers tell you how to get the full underlying detail if you want it — ask a follow-up naming what the pointer references.
- **A `denial` block** vs an **empty result** — a denial means access, not absence. If you get an empty/no-data answer for a chart you should have access to, that's worth flagging (this exact distinction is a known open item — see acceptance report).

## Frames, paradigms, budgets
- **Frame** (which point is "1st house"): default is lagna. Ask "from the Moon" or "from Arudha" to shift.
- **Paradigm**: default is mainstream Parashari. Ask for "Jaimini" or "KP" explicitly to get that system's reading — the instrument keeps paradigms separate, never silently blends them.
- **Budget**: default responses are chat-sized. Ask "give me the full detail" or "don't trim this" to get the un-trimmed version when you want depth over brevity.

## Recording a life event or an outcome
- **A life event** ("I changed jobs last month") → `lel_event_record`. This feeds the calibration loop — more real events, better-calibrated future predictions.
- **An outcome on a specific prediction** ("that career-window prediction from March — it happened") → `mimamsa_outcome_record`. This is what lets the instrument's confidence numbers self-correct over time.
- Recalibration doesn't happen instantly — there's a debounce so a burst of manual corrections doesn't thrash the model; expect it to show up in later prediction confidence, not the very next query.

## Known honest gaps (as of 2026-07-09)
- Some quality punch-items (entitlement-denial clarity, posterior-provenance detail) are fixed correctly but not yet reachable through a public tool name — you won't see them live yet even though the underlying fix shipped.
- The full acceptance battery (40-item frozen eval) does **not yet clear its bar** — see `R5_1_MCP_CONSUME_ACCEPTANCE_v1_0.md` for the honest scorecard. Treat answers with the same critical eye you always would; the instrument is hardened but not yet fully self-certified.
- `/api/retrieval/capability`'s entitlement gate is a real open item — flagged, prioritized, not yet fixed.
