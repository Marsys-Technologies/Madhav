---
artifact: PG1_LANE_R-2
lane: R-2
wave: PG-1 (Paripraśna Grounding Audit)
status: CLOSED
authored_by: Claude Code (Sonnet 5), Lane R-2 agent, 2026-07-19
audit_target: live mcp__marsys-jis-direct__* tool surface, chart_id 482012f1-710e-4a25-994a-93821f5871aa (Abhisek)
---

# PG1 Lane R-2 — Observed Live Retrieval Behaviour

## Scope

Read-only observational audit: executed 35 live tool calls against the
`marsys-jis-direct` connector (the deployed Cloud Run api_key seat) covering
ganita_*, bodha_*, kala_*, phala_*, mimamsa_*, ref_*, query_*, get_* and
judgment_query, plus 3 dedicated A2 (chart_agnostic_gate) probes. Wrote only
to `00_ARCHITECTURE/pg1_audit/deliverables/pg1_findings_R-2.jsonl` and this
state file. No writes to `platform/src/**`, `platform-mcp/src/**`,
migrations, infra, workflows, or governance-manifest files.

## Behavioural table (35 tools exercised)

| tool | rows/empty/error | judgment_flags seen | coverage/total non-null? |
|---|---|---|---|
| ganita_chart_facts_get | 1 row (LAGNA) | none (legacy) | yes (total:1) |
| ganita_dashas_get | 89 rows, trimmed to 44 | none (legacy) | no (pagination.total absent; total=89 only in `total` sibling field) |
| ganita_yogas_get (v3) | 10 rows | catalog_only_rows_present | yes (coverage.total=10) |
| ganita_yoga_firings_get | 12 fired rows | none (legacy) | n/a (no envelope wrapper) |
| ganita_positions_get | 86 rows | none (legacy) | no |
| ganita_strength_get | 520→65 trimmed | none (verdict:null) | no (pagination.total:null; content.total:520) |
| ganita_structural_get facet=dosha_fires (v3) | 0 rows | zero_rows_returned | yes (coverage.served=0,total=0) |
| ganita_nakshatra_get | 39 rows | none | no |
| bodha_chart_digest_get | digest + 20 signals | none | n/a |
| bodha_domain_reading_get (career) | 5 ranked_signals (capped from 20), 2 lenses | none | partial (lens_pagination.total=2; ranked_signals_total per-lens present) |
| bodha_discoveries_get | 30→15 trimmed (of 1275 total) | none | yes (total:1275) |
| bodha_signals_get | 10 rows (of 9946 matching) | none | yes (total_matching_filters:9946) |
| bodha_quality_get | scorecard, 49705 msr signals | none | n/a (scorecard fields) |
| bodha_remedies_get | 9 resonances, 27 prescriptions | none | n/a |
| kala_life_arc_get | 50 parvas | none | n/a |
| kala_windows_get | 50 activations, floored to 5 | none | n/a; drill_pointers broken (see PG1-R2-0001) |
| phala_outlook_get | 3 anchors, 100→10 mitigations, 30→15 windows | none | n/a; drill_pointers broken |
| phala_anchors_get | **ERROR 422** | n/a | n/a |
| phala_mitigation_get | ok, double-encoded content string | none | n/a |
| mimamsa_insight_get | 30 insight units (STRUCTURAL mode) | none | n/a |
| mimamsa_calibration_get | ok, 141 QA checks, double-encoded content string | none | n/a |
| ref_yogas_get | 9 rows | none | yes (total:9) |
| ref_dignity_reference_get | **ERROR 400 internal_error** | n/a | n/a |
| judgment_query domain=marriage (v3) | verdict:contested, composite_score:-3.5 | 4 distinct flags (see below) | coverage:null even in v3 (this tool) |
| query_chart_facts (chart_id=00000000...) | 0 rows (A2 probe) | none | yes (total:0) |
| get_signals (chart_id=00000000...) | 0 rows (A2 probe) | none | n/a |
| ganita_positions_get (chart_id=ffffffff...) | 0 rows (A2 probe) | none | n/a |
| ganita_medical_get | 9 rows | none | yes (total_matching:9) |
| ganita_sade_sati_get | 1259→78 trimmed | none | no |
| ganita_condition_get facet=karakas | 340→85 trimmed | none | no |
| ganita_special_lagnas_get | 49 rows | none | yes (total:49) |
| kala_muhurta_get | 15 windows | none | n/a |
| kala_priority_ranking_get | 20 ranked signals | none | n/a |
| ref_entities_list | 11 planets | none | yes (total:11) |
| get_remedies | same shape as bodha_remedies_get | none | n/a |

## Real judgment_flags vocabulary discovered (this sample alone)

BIND_PG-1 stated only 3 judgment_flags values are documented anywhere. This
lane's ~35-call sample surfaced **9 distinct values actually served**:

1. `catalog_only_rows_present` (ganita_yogas_get)
2. `zero_rows_returned` (ganita_structural_get, facet=dosha_fires)
3. `bearing_yogas_no_domain_match` (judgment_query)
4. `bearing_yogas_corroboration_caveat` (judgment_query)
5. `notably_absent_not_checked` (judgment_query)
6. `afflictions_present` (judgment_query)
7. `response_still_over_12kb_budget_after_full_trim` (judgment_query)
8. `timing_anchored_forced_false` (judgment_query)

Two more related-but-distinct fields observed adjacent to judgment_flags:
`catalog_only_note` (a sibling string field, not itself in the flags array)
and `dosha_label_gate` (a structured gate-state object, same family).

**Critical caveat**: flags only appeared when `response_format=v3` was
explicitly requested (ganita_yogas_get, ganita_structural_get, judgment_query)
or on tools whose only envelope IS the v3-style unified shape. Every
default-legacy call in this sample returned `judgment_flags:[]` even where
the same underlying condition existed in `content` (e.g. ganita_yoga_firings_get's
bhaṅga ledger, ganita_dashas_get's ayanamsha omission edge case) — so the true
vocabulary is almost certainly larger; recorded as PG1-R2-0007.

## A2 (chart_agnostic_gate) test result

**Confirmed, with a methodology caveat.** Tested 3 tools
(query_chart_facts, get_signals, ganita_positions_get) with the two
RFC-sentinel UUIDs the tools' own schemas explicitly whitelist
(`00000000-0000-0000-0000-000000000000` and
`ffffffff-ffff-ffff-ffff-ffffffffffff`). All three returned clean, honestly
empty results (0 rows/facts/signals) scoped to that literal sentinel
chart_id — **no leak of the real chart (482012f1...) or any default chart
into the response**. The gate holds for this sample (PG1-R2-0004).

However: `chart_id` is a hard `required` JSON-schema field with a strict
UUID-pattern on every one of the ~35 tools this lane exercised. The MCP
client harness itself refuses to build a call omitting a required parameter
— so the literal "omit chart_id entirely" scenario A2 was framed around
could not be exercised from this seat at all. This is recorded as
unverifiable (PG1-R2-0005), handed to a future lane with raw-HTTP or
source-read access.

## Headline finding

Two real server-side defects surfaced from completely ordinary, documented
usage (not edge cases): **phala_anchors_get 422s on its own documented
optional parameter** (date_range is optional in the tool schema but
mandatory one hop downstream at the sidecar; PG1-R2-0002), and
**ref_dignity_reference_get 400s on its flagship documented use** — filtering
by `planet=Saturn`, the exact example the tool's own description gives —
returning `internal_error: platform DB query failed: 400` instead of data
(PG1-R2-0003, severity high). Both are genuinely broken code paths a normal
caller would hit on day one, not adversarial probing.

Runner-up: the `drill_pointers`/`recover_via` self-reference mechanism that
A1's "reference-don't-repeat" premise depends on is itself buggy in ~3 of the
tools sampled — it correctly names the calling tool in some responses
(ganita_dashas_get's own trim_report) but degrades to the literal string
`"unknown_tool"` in others (kala_windows_get, phala_outlook_get) — precisely
the sidecar/alias-backed tools, mirroring R-1's finding that alias/sidecar
tools carry different code paths than registry-backed ones (PG1-R2-0001).
Separately, the pointer mechanism DOES work correctly end-to-end when tested
on a registry-backed pair (ganita_yogas_get → ganita_yoga_firings_get,
PG1-R2-0006, confirmed) — so this is a defect on specific tool classes, not
a wholesale defect in the drill_pointer premise.

A third-tier finding worth flagging for R-1's registration-path work:
mimamsa_calibration_get, mimamsa_insight_get, and phala_mitigation_get wrap
their real payload in a JSON-encoded STRING one level deeper than every
other tool's envelope (PG1-R2-0010) — near-certainly the same "three live
KEYSTONE REQUEST sidecar tools" R-1's server.ts comment-reading flagged as
the concrete A4 pull-in inventory, now independently confirmed from the wire
shape rather than source comments.

## Findings count by class

| class | count |
|---|---|
| new_defect | 5 |
| confirmed | 3 |
| partial | 1 |
| unverifiable | 1 |
| **total** | **10** |
