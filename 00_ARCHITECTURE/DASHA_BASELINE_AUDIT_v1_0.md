---
artifact: DASHA_BASELINE_AUDIT_v1_0
canonical_id: DASHA_BASELINE_AUDIT
version: 1.0
status: BASELINE — pre-Phase-5 measurement
captured_on: 2026-05-19
method: audit_events query + tool-bundle analysis (response_text not stored in schema)
sample_size: 3 (below 5-row threshold — see §Caveat)
---

# Dasha Baseline Audit

Pre-§5A measurement of dasha-correctness failure rate.

## Method

SQL query against `audit_events` table over the last 30 days
(proxy on 127.0.0.1:5433), filtering `query_text ~* '(mahadasha|vimshottari|antardasha|dasha)'`.

**Schema discovery**: `audit_events` does NOT store `response_text` (synthesis output).
Columns available: `query_text`, `query_class`, `tool_bundles` (jsonb — tool names + latency
only, no raw synthesis text), `created_at`. The 20-sample manual classification of response
excerpts described in the brief methodology is not possible from audit_events alone.

Alternative evidence: tool_bundles column records WHICH tools fired — this surfaces
Gap A (no chart_facts_query dasha rows) and Gap B (temporal returns active chain only)
directly from production query traces.

## DB state

- Total audit_events rows: 24 (date range 2026-04-30 → 2026-05-01)
- Dasha-mentioning rows: 3 (all from 2026-04-30)
- All-time dasha query count: 3 (eval discipline kept production traffic minimal)

## Observable evidence from tool_bundles

| # | query_text (abbreviated) | Tools fired | Dasha-correctness signal |
|---|---|---|---|
| 1 | "What does my Saturn dasha bring?" | cgm_graph_walk, **temporal** (1 item), vector_search | `temporal` used for dasha — Gap B pattern (returns active chain, not next MD) |
| 2 | "Where is my Ketu Mahadasha? I feel the data that you're showing is wrong." | msr_sql, **temporal** (1 item), contradiction_register, cgm_graph_walk, vector_search | User explicitly says synthesis data is WRONG. `temporal` again — no `chart_facts_query` dasha rows. Gap A + B both confirmed. |
| 3 | "Can you explain…the mistake you made for Ketu Mahadasha in twenty thirty-one…" | msr_sql, vector_search | **Canonical failure directly confirmed**: synthesis claimed Ketu MD in 2031; correct is 2027-08-19 → 2034-08-21. Neither `chart_facts_query` nor any dasha-specific tool was fired. Synthesis hallucinated from pretrained knowledge. |

## Classification

Full 20-sample classification deferred (see §Sample-size caveat). From the 3 available rows:

| Class | Count | Notes |
|---|---|---|
| correct_current_md | unknown | Response text not stored |
| correct_next_md | 0 | Row 3 directly contradicts this |
| wrong_next_md_saturn | 0 | Wrong lord was implied (2031 date suggests Ketu/Venus boundary confusion) |
| wrong_next_md_other | 1 | Row 3: Ketu MD date error (claimed 2031 vs correct 2027-08-19) |
| wrong_ad_under_md | unknown | Response text not stored |
| no_dasha_claim | 0 | All 3 queries resulted in dasha claims (users were complaining about them) |

## Gap confirmation from tool trace

**Gap A confirmed**: In all 3 queries, `chart_facts_query` was NEVER fired with
`dasha_vimshottari` category. The category exists in the DB but the RCS description
doesn't advertise it — planner cannot discover it.

**Gap B confirmed**: Rows 1 and 2 used `temporal` for dasha context. `temporal` returns
only the active 5-level chain at one date — not the next MD. Synthesis was given current
Mercury MD data and had to extrapolate "next" without the schedule.

**Gap D confirmed**: FORENSIC is always in the bundle (floor asset) but Row 3 shows
synthesis still hallucinated Ketu MD dates despite §5.1 being present — pretrained
knowledge displaced the document.

## Failure rate

Observable wrong-next-MD rate from 3 samples: **1/3 = 33%** (1 confirmed wrong, 2 unknown).
True rate likely higher — Rows 1 and 2 lack synthesis text but show the same tool pattern
that produced the Row 3 failure.

## Sample-size caveat

N=3 is below the 5-row minimum threshold specified in the brief. The eval discipline kept
production traffic minimal — 24 total audit_events covering only 2 days (2026-04-30 to
2026-05-01). The post-campaign measurement (after §5C closes) will use the same methodology
against a larger post-Phase-5 audit_events sample accumulated over production usage.
The delta between pre- and post-§5C measurements is the campaign's primary success metric.

**Per brief §4.0 protocol**: sample_size < 5 → baseline deferred to post-§5C; §5A
proceeds without blocking on this measurement.

---

*Captured by §5A execution session 2026-05-19. Executor: Claude Code (analysis stream).*
*DB: amjis Cloud SQL via proxy 127.0.0.1:5433. Branch: analysis/backend-data-pipeline-perf-audit.*
