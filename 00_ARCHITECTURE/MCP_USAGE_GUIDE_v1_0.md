---
canonical_id: MCP_USAGE_GUIDE
version: 1.1
status: CURRENT
created: 2026-07-09
author: Claude Code (executing CLAUDECODE_BRIEF_R5_1_MCP_CONSUME_v1_0.md C5; updated for R5.2 A6 close)
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

## What changed in R5.2 (2026-07-09)
- **Entitlement gate closed.** `/api/retrieval/capability` (the path every flagship instrument routes through) now checks per-chart access on every call. A chart you don't have a grant for returns a distinct denial, not an empty result — the "denial vs. empty" caveat below no longer applies.
- **`query_chart_facts`/`ganita_chart_facts_get` now serves a `dignity` field on planet-position rows** (exalted/own/friend/neutral/enemy/debilitated) — you no longer need a separate `get_dignity` call just to know if a planet is exalted.
- **New tool: `phala_predictive_anchors_get`** — the posterior-provenance fix from R5.1 (honest base-rate sourcing, no fabricated sample sizes) is now reachable; it wasn't wired to any public tool name before.
- **Budget discipline extended** to `phala_outlook`, `holistic_bundle_chart_facts`, and `bodha_signals_get` — these used to serve 100KB-500KB+ responses by default; now trimmed to a sane ceiling with a `recover_via` pointer to get the full detail if you ask for it.

## Known honest gaps (as of 2026-07-09, post-R5.2)
- The full acceptance battery (38-item frozen eval, real Gemini/DeepSeek rubric grading) improved from 23.7% to 31.6% overall but **does not clear the ≥90% bar** — see `R5_2_RUN_LEDGER_v1_0.md` §A5 for the honest scorecard and root-cause register. Treat answers with the same critical eye you always would; the instrument is hardened in specific, verified spots, not broadly self-certified.
- Content-depth/synthesis quality (remedies, timing windows, verification-style questions) is the largest remaining gap — 16 rubric-graded battery items still score below their floor even under real grading. The underlying tool data is often substantively rich (verified via direct spot-checks); the gap is in how thoroughly a client's answer draws on it.
- `query_remedies` still serves an oversized single result (~106KB) — not yet fixed, needs its own investigation (not a simple array-trim case).
- D60 (and other fine divisional-chart) queries via `query_chart_facts` don't yet carry a birth-time-sensitivity/rectification-confidence caveat, even though D60 readings are classically far more sensitive to precise birth time than D1.
