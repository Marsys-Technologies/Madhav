---
artifact: MARSYS_JIS_TOOLING_REMEDIATION_PLAN_v1_0.md
session: TOOLING-REMEDIATION-PLAN-V1
workstream: MARSYS-JIS Tooling Audit Remediation (post-Sankalpa, v4.1)
status: PROPOSED
author: Claude Opus 4.7 (Cowork planning)
created: 2026-05-24
source_audit: MARSYS_JIS_Tooling_Audit_Report.pdf (20pp; Claude, 24 May 2026; post-Sankalpa work session)
verification_method: code+DB-read via parallel exploration agents (no live MCP calls)
verification_date: 2026-05-24
target_revision: amjis-mcp-00011-9zv (MCPT v3.2 prod, post-merge)
estimated_total_duration: 6–10 work-weeks across 12 phases (parallelizable)
---

# MARSYS-JIS Tooling Remediation Plan v1.0

Source: post-Sankalpa tooling audit (24 May 2026, 20 pp, Part I–VI). This plan
verifies every audit finding against the actual repo, then groups all findings
into 12 implementation phases ordered by dependency + impact. The audit ranked
findings by predictive-quality impact; this plan re-ranks by `impact × (1 / cost)`
because the verification pass surfaced six "missing tools" that are actually
built engines waiting for an MCP wrapper — those collapse from multi-day builds
to ~1-hour tasks and should run before the long-tail engine builds.

The audit is acharya-grade: it correctly names every weakness in the v3.2
surface. Verification narrows several remediation targets — the bug for several
"broken" tools sits in the platform primitive or the production environment, not
in the MCP wrapper code — but no audit finding is rejected outright.

---

## §1 Verification result: what the audit got right, where it pointed slightly off

The audit makes 24 falsifiable claims (11 about tool behaviour, 7 about data-layer
state, 6 about missing-tool inventory). Three parallel exploration agents
verified each one against `platform-mcp/src/tools/`, `platform/src/lib/retrieve/`,
`platform/python-sidecar/`, the chart_facts loader, and the canonical-asset
filesystem. Results:

### §1.1 Tool-behaviour claims (Part I of audit)

| Code | Audit claim | Verification | Remediation target |
|---|---|---|---|
| C1 | `chart_summary` returns 0 rows on every invocation | **DISPUTED at MCP layer.** Wrapper at `platform-mcp/src/tools/chart_summary.ts:127–176` passes `category[]` and optional `chart_id` correctly to `query_chart_facts` primitive. If 0 rows, the bug is in the platform primitive's chart_id default resolution OR in the categories the wrapper picks by default. | Reproduce against prod; trace whether the primitive returns rows for the same params. Fix at the platform layer, not the MCP wrapper. |
| C2 | `holistic_bundle` UCN/RM/CDLM sub-tools always error | **PARTIAL.** `holistic_bundle.ts:184–196` routes UCN/RM/CDLM to `vector_search` with different `source_filter` values (lines 215–219). If they error, the issue is the `source_filter` values themselves (likely `source_filter` strings don't match any chunks tagged as UCN/RM/CDLM in `rag_chunks`). | Audit the rag_chunks `source` column for what UCN/RM/CDLM chunks are actually tagged as; fix the source_filter strings to match. |
| C3 | `cross_school_lookup` returns `coverage_type: "silent"` for every claim | **UNVERIFIED BY CODE — likely DATA-EMPTY.** Schema (migration 057) defines 7 schools × 3 coverage types. Loader for `school_convergence_index` not located in the repo. Tool code is correct. | Count rows in prod `school_convergence_index` per school; build/run the missing loader. |
| C4 | `query_signals` filters silently ignored (`forward_looking`, `min_confidence`) | **DISPUTED at MCP layer.** `query_signals.ts:76–89` threads all filters through to the platform primitive. If filters don't fire, bug is in the primitive's SQL WHERE clause. | Trace to platform primitive; add filter-honour SQL + tests. |
| C5 | `query_ephemeris` returns only one date even when `date_range` passed | **DISPUTED at MCP layer.** `query_ephemeris.ts:49–77` declares and forwards `date_range`. Bug is downstream in the primitive's LIMIT or in how it interprets the range. | Fix at platform primitive; honour the range; add sampling cap. |
| C6 | `query_transit_event` required `event_type` not in schema; errors with `"Unknown event_type 'undefined'"` | **CONFIRMED.** `query_transit_event.ts:48–60` declares only `planet`, `target`, `date_range`. `event_type` is undocumented and required. | Add `event_type` to schema as enum; mark required; improve error message. |
| C7 | `query_dasha_periods` returns only MD/AD; no PD/SD | **CONFIRMED at schema layer.** No `level` enum exposed in `query_dasha_periods.ts:46–57`. Description mentions Pratyantar but schema doesn't surface it. | Add `level: enum(maha\|antar\|pratyantar\|sookshma)` param; thread through to engine. |
| C8 | `query_panchanga` missing `hora`, `choghadiya`, inauspicious windows in response | **DISPUTED at MCP layer.** Tool description and schema response shape claim these fields. PR #110 added 5 JSONB columns to `panchanga_daily` for `special_yogas`, `choghadiya`, `hora`, `inauspicious`, `auspicious`. If response is missing these, the primitive isn't surfacing the enrichment columns. | Trace to primitive `query_panchanga` handler; surface enrichment JSONB columns into response. |
| C9 | `read_asset` returns `ENOENT` for `MACRO_PLAN` and `LEL` (path leading slash) | **DISPUTED at code layer.** Both files exist on disk; `route.ts:49–62` builds relative paths correctly. Likely a **Cloud Run sidecar `process.cwd()` mismatch**: in prod the container's working dir may not be where the repo root sits. The leading slash in the audit's error message (`'/00_ARCHITECTURE/…'`) suggests an absolute-path concat went wrong somewhere. | Reproduce against the prod sidecar with the same `canonical_id` values; inspect the container working-dir; fix the path resolution OR bake the docs into the container image. |
| C10 | `read_classical_text` is OCR-noisy; no chapter:verse lookup; only 4 texts | **CONFIRMED.** `read_classical_text.ts:28–40` hardcodes 4 texts (BPHS, KP Reader, Jaimini Sutram, Tajaka Neelakanthi). Schema (lines 54–89) has only `query` + `text_id` + `limit`. No chapter:verse parameter. | Add `chapter`/`verse`/`citation` exact-lookup endpoint. OCR-cleaning the existing corpus is a separate workstream. Expanding to Saravali, Brihat Jataka, Phaladeepika, Jataka Parijata, Uttara Kalamrita is the long tail. |
| C11 | `query_chart_facts` returns empty silently for `deity_assignment`, `ishta_kashta`, `chandra_placement` | **DISPUTED at code layer.** Categories are listed in `CHART_FACTS_CATEGORIES` (`query_chart_facts.ts:47–57`). Extractor code populates them (see D1 below). If empty, the prod DB just doesn't have the rows — extraction never ran, or ran and matched zero. | Run extractor against the MSR signals; add `populated_count` to the response shape so empty-but-known is distinguishable from no-matches. |

### §1.2 Data-layer claims (Part II/V references)

| Code | Audit claim | Verification | Remediation target |
|---|---|---|---|
| D1 | `chart_facts` categories empty: `deity_assignment`, `ishta_kashta`, `chandra_placement`, `avastha` | **CODE-FALSE / DATA-UNKNOWN.** Extractor (`extractor.py:346–375, 562–596, 863–902, 904–980`) parses all 4 categories. Loader accepts all 4 in `VALID_CATEGORIES`. SIG.MSR.397 and SIG.MSR.438 exist in `MSR_v5_0.md`. So the extractor *could* populate these; if the table is empty in prod, the extraction either never ran for these sections or ran and matched zero. | Run extractor against current MSR; diff against prod table; backfill the rows. |
| D2 | shadbala returns partial (no 6-component roll-up) | **CONFIRMED.** Extractor parses 19 sub-component rows under `category="shadbala"` (`_SBL_COMPONENT_MAP` lines 168–189) but no roll-up to the 6 canonical components (Sthana, Dig, Kala, Cheshta, Naisargika, Drig). MCP `query_chart_facts` returns raw component rows. | Add roll-up either at extractor time (write 6 aggregate rows per planet) or at tool time (new `get_shadbala_full` synthesizes from components). |
| D3 | `read_asset` ENOENT in prod | **DISPUTED on disk.** Files exist at expected paths; resolution code is correct. Issue is prod runtime, not the dev tree. | (Same as C9.) Investigate Cloud Run sidecar `cwd`. |
| D4 | Every school in `school_convergence_index` returns `silent` | **UNABLE TO VERIFY without DB access.** Migration 057 + MV from migration 079 confirm 7-school × 3-coverage-type schema. No loader script found in repo. Expected capacity 543 signals × 7 schools = 3,801 rows max. | First action: count rows in prod by school. Then build/run the loader. |
| D5 | 2,717 chart_facts rows across 27 categories | **PARTIAL.** Verification artifact `E_chart_facts.json` (2026-04-29) shows 589 rows × 18 categories. Extractor adds 19 new categories; loader estimate ~200–215 new rows → ~800 total. The 2,717 number is aspirational, not measured. | Re-run extractor; capture actual count; publish to closing artifact. |
| D6 | 4,589 RAG chunks | **UNABLE TO VERIFY.** Chunking code exists (`classical_text_chunker.ts`); no closing artifact found with the count. | Count `rag_chunks` rows in prod; publish. |
| D7 | Only 4 classical texts indexed; Saravali, Brihat Jataka, Phaladeepika, Jataka Parijata, Uttara Kalamrita absent | **CONFIRMED.** `chunker.ts` hardcodes WORK ∈ {BPHS, Jaimini, KP, Tajaka}. No files for the 5 other texts in repo. | Long-tail corpus expansion. Source acquisition (OCR / digitized editions) is the cost driver, not the indexing. |

### §1.3 Missing-tool inventory (Part II of audit, 24 items)

The audit names 18 missing tools but actually lists 24. Verification triages them
into 4 cost classes:

**Class A — Engine already exists, MCP wrapper missing (≈1-hour task each):**
- `query_varshphal` → `platform/src/lib/retrieve/query_varshaphala.ts` (full Tajaka engine; reads `varshaphala` table)
- `query_divisional_chart` → `platform/src/lib/retrieve/divisional_query.ts` (D1–D60 from chart_facts)
- `query_remedial_mantras` → `platform/src/lib/retrieve/remedial_codex_query.ts` (RAG-chunk filter on `doc_type='l4_remedial'`)
- `muhurta_finder` → `platform/python-sidecar/panchang_engine/muhurat.py` (Phase 4C-shipped, prod-ready)
- `tara_balam_for_native` → `platform/python-sidecar/panchang_engine/tara_bala.py` (integrated into muhurat scoring)
- `chandra_balam_for_native` → same file as above

**Class B — Data ready, engine needs to be written:**
- `query_transits_over_natal` (ephemeris + orb computation)
- `query_yogas_active_now` (cross-reference natal `yoga` rows × current dasha + transits)
- `get_planet_avastha` (compute live state from current ephemeris × natal positions; data category exists)
- `get_shadbala_full` (component roll-up; D2 above)
- `query_planetary_period_predictions` (curator over BPHS/Jaimini classical-text chunks)
- `query_dasamsha_career` (D10 chart_facts + interpretation rules)
- `query_shashtiamsha` (D60 chart_facts + analysis)
- `query_drekkana_drishti` (D3 chart_facts + Jaimini aspects)
- `query_remedies_prescribed` (codex × chart-condition index)

**Class C — Sidecar stub exists, needs implementation:**
- `query_jaimini_chara_dasha` (stub at `python-sidecar/routers/jaimini.py`, framework deferred to M6)
- `query_eclipse_transits` (stub at `python-sidecar/routers/eclipses.py` + writer pipeline present)

**Class D — Greenfield (out-of-scope for v3.x; needs new substrate):**
- `compute_synastry` (two-chart compatibility; needs spouse/partner data per §11)
- `compute_business_chart` (entity chart; needs MARSYS founding data per §11)
- `query_kp_horary` (KP method horary; new engine)
- `query_planet_war` (graha_yuddha computation; could be a thin engine over ephemeris)
- `compute_progressions` (western secondary OR Tajaka progression)
- `vastu_audit` (structural/spatial analysis; new domain)
- `numerology_sync` (name + number resonance; new domain)

### §1.4 Headline reframe

The audit's "single most valuable next step" priority list reads "fix chart_summary; fix cross_school_lookup; add query_varshphal; fix query_ephemeris; gather spouse/partner data." After verification, three of those five reorder usefully:

| Audit rank | Audit framing | After verification | Cost |
|---|---|---|---|
| 1 | Fix `chart_summary` (FIRST CALL tool returns 0) | **Diagnose where the 0-rows happens** — wrapper is correct; bug is in platform primitive or default chart_id resolution | M (couple days of trace + fix) |
| 2 | Fix `cross_school_lookup` (silent for all schools) | **Count rows in `school_convergence_index` per school in prod; build the loader if 0** | L (loader work, possibly 1–2 weeks) |
| 3 | Add `query_varshphal` | **Wrap the existing engine in an MCP tool** | S (1 hour) |
| 4 | Fix `query_ephemeris` date_range | **Fix at platform primitive** (MCP wrapper is correct) | S (half-day) |
| 5 | Provide spouse + business co-founder data | **No code change — elicitation from native** | (out-of-scope for engineering) |

Item #3 (varshphal) drops from "build new engine" to "wrap existing engine"
— a single-session task. This rebases the entire plan: instead of an 8-week
engine-build campaign followed by data fixes, the right order is
**bug-fixes-and-wrappers-first (1 week to capability parity), engine-builds-after**.

---

## §2 Phased implementation plan

Twelve phases. Phases marked **[parallel]** can run concurrently with the
previous phase. Each phase produces one CLAUDECODE brief at the time it kicks
off (not upfront — same convention as MCPT v3.2).

### Phase 0 — Pre-flight diagnostic (1 day; gates everything)

Before changing anything, capture the **exact** ground truth of what's broken
and what's empty in prod. The audit was Claude's hands-on observation; this
phase is the structured baseline.

Tasks:
1. Run `data_coverage` against prod with `super_admin` tier; save the response.
2. Run `tool_health` over the last 30 days; save.
3. For each of the 11 tools the audit flags broken/partial (C1–C11), run a
   minimal invocation and capture: schema-valid? row count? error shape?
4. Query prod DB (or via `data_coverage`):
   - chart_facts row count per category (target table for D1, D5)
   - school_convergence_index row count per school × coverage_type (target for D4)
   - rag_chunks row count grouped by `source` / `doc_type` (target for D6, D7)
5. Capture baseline: `eval-results/tooling_audit_baseline_TS.json`
6. Open a tracking issue (or `Plans/MARSYS_JIS_TOOLING_AUDIT_TRACKER_v1_0.md`)
   that lists each finding, its baseline state, and the phase that will fix it.

Acceptance: baseline file + tracker exist; every audit finding has a row.

### Phase 1 — Critical broken-tool fixes (1 week; parallel internal tasks)

Six fixes. All are high-impact, low-cost. Most are platform-primitive bugs not
MCP-wrapper bugs, so the work happens in `platform/src/lib/retrieve/` and
`platform/src/lib/mcp/primitives_registry.ts` (and the platform tests), not
`platform-mcp/src/tools/`.

| Sub | Target | Audit ref | Effort |
|---|---|---|---|
| 1.1 | `chart_summary` 0-rows root cause + fix | C1, audit P-VI #1 | M (1–2 days) |
| 1.2 | `query_transit_event` — add `event_type` to schema, mark required, improve error message | C6, audit Cat-3 | S (½ day) |
| 1.3 | `query_signals` — honor `forward_looking`, `min_confidence`, add `valence` + `temporal_activation` + `domains[]` filters | C4, audit Cat-2 | M (1 day) |
| 1.4 | `query_ephemeris` — honor `date_range`; add `sample_step` (1/7/30 days); add `return_changes_only` flag | C5, audit P-VI #4 | M (1–2 days) |
| 1.5 | `read_asset` — diagnose prod cwd / path resolution; surface a `list_assets` endpoint while we're there | C9, D3, audit Cat-4 + P-V | M (1 day) |
| 1.6 | `query_panchanga` — surface the 5 enrichment JSONB columns (`hora`, `choghadiya`, `inauspicious`, `auspicious`, `special_yogas`) added by PR #110 | C8, audit Cat-3 | S (½ day) |

Acceptance: each tool has a regression test that fails today and passes after
the fix; routing eval still ≥80%; no new tools broken.

### Phase 2 — Cross-school convergence + classical-text scope (2 weeks)

The audit's #2 priority. Verification couldn't measure prod-DB state, so this
phase starts with a count and bifurcates.

2.1 — Count `school_convergence_index` rows per school. Two branches:
- **If meaningfully populated** (≥1,000 rows): the bug is in `cross_school_lookup`'s matching join. Fix in `platform-mcp/src/tools/cross_school_lookup.ts` or its primitive.
- **If sparse** (<500 rows): build the loader. Source: MSR signals tagged by school; classical-text excerpts attributed to BPHS/Jaimini/KP/Tajaka. Target: 543 signals × at-minimum-2-schools-each = ~1,100 rows minimum.

2.2 — Run the loader to populate; verify `cross_school_lookup` returns
non-silent coverage for a representative spread of claims.

2.3 — Add **6 schools that are silent today** (audit names 7: Parashari,
Jaimini, KP, Tajaka, Nadi, BNN, Yogini). For Nadi/BNN/Yogini, decide explicitly:
populate stub `silent` rows (acknowledging the school isn't represented), or
defer to a future phase. Recommendation: stub silent for v1.0 honesty.

2.4 — Classical-text corpus expansion. The audit names 5 missing texts
(Saravali, Brihat Jataka, Phaladeepika, Jataka Parijata, Uttara Kalamrita). For
each: identify a digitized source, OCR, chunk, embed, ingest. **Source
acquisition is the cost driver, not the ingestion pipeline.** Recommendation:
do Phaladeepika and Brihat Jataka first (highest standalone reference value);
defer the other 3 to v1.1.

2.5 — Add chapter:verse exact-lookup to `read_classical_text` (audit C10).

Acceptance: `cross_school_lookup` returns at least one `primary` coverage_type
across the 30 routing-eval prompts. `read_classical_text` supports
`citation: "BPHS.33.12"` exact lookup. Two new texts in the rag_chunks corpus.

### Phase 3 — Empty-category backfill (1 week; **[parallel with Phase 2]**)

D1 + audit P-I Cat-2. The extractor code populates the 4 empty categories; if
prod has 0 rows, the extractor either never ran or matched 0. Diagnose, then
fix.

3.1 — Re-run the chart_facts extractor against current MSR_v5_0 (or v5.1 if
that's the current version per CANONICAL_ARTIFACTS). Count rows extracted per
category. Compare against the prod table.

3.2 — For each of `deity_assignment`, `ishta_kashta`, `chandra_placement`,
`avastha`: if extraction produces 0, the MSR section the extractor parses is
either differently-shaped now or the extractor needs to widen its regex. SIG.MSR.397
(deity) and SIG.MSR.438 (ishta_phala) exist; verify they sit in the section the
extractor reads from.

3.3 — Backfill the missing rows in prod via the standard chart_facts loader.

3.4 — Reconcile the v3.2 closing artifact's "2,717 rows / 27 categories" claim
with reality. Publish a corrected count.

3.5 — Add `populated_count` field to every `query_chart_facts` response so an
empty-and-documented category is distinguishable from a no-match.

3.6 — Add `include_empty_counts: bool` flag so caller can request a tally even
when only some categories matched.

Acceptance: all 27 (or actual-count) categories report `populated_count > 0`
where data exists, with `populated_count = 0` explicit for known-empty ones.

### Phase 4 — Quick-win MCP wrappers (3 days; **[parallel with Phase 1+2+3]**)

Class A from §1.3. Six tools where the engine exists; only the wrapper needs to
be added under `platform-mcp/src/tools/`. Each wrapper follows the existing
pattern in `query_chart_facts.ts` (`description_builder` + `_envelope` + Zod
schema + tier-aware dispatch).

| Sub | Tool | Source engine | Effort |
|---|---|---|---|
| 4.1 | `query_varshphal` | `platform/src/lib/retrieve/query_varshaphala.ts` | 1 hr |
| 4.2 | `query_divisional_chart` | `platform/src/lib/retrieve/divisional_query.ts` | 1 hr |
| 4.3 | `query_remedial_mantras` | `platform/src/lib/retrieve/remedial_codex_query.ts` | 1 hr |
| 4.4 | `muhurta_finder` | `platform/python-sidecar/panchang_engine/muhurat.py` (via existing sidecar HTTP route) | 2 hrs |
| 4.5 | `tara_balam_for_native` | `platform/python-sidecar/panchang_engine/tara_bala.py` | 2 hrs |
| 4.6 | `chandra_balam_for_native` | same file | 1 hr |

Each wrapper gets: schema description that matches existing patterns,
tier-aware visibility (default super_admin + acharya), at least one happy-path
test, routing-eval addition (one prompt per new tool).

Acceptance: 6 new tools exposed; routing eval re-run shows the new tools route
correctly when invoked by name and by intent.

### Phase 5 — `holistic_bundle` remediation + streaming (1 week)

5.1 — Diagnose UCN/RM/CDLM `source_filter` mismatch (C2). Audit the
`rag_chunks` table: what `source` values exist? Pick the right strings.
Alternative: change UCN/RM/CDLM routing to use `read_asset` (once Phase 1.5
fixes that) instead of `vector_search`.

5.2 — Add `subset_size` to the schema (default 100 signals; caller can request
30 or 200). Audit P-I Cat-1.

5.3 — Add `return_format: "verbose" | "compressed"` flag (compressed strips
descriptions, returns IDs + scores only). Audit P-I Cat-1.

5.4 — Implement response streaming or pagination for any tool whose response
can exceed 50KB. `holistic_bundle` (72KB observed) and `cross_school_lookup`
with full evidence are the targets. Audit P-V item 2. Use MCP's
`Content-Type: text/event-stream` chunked emission.

Acceptance: `holistic_bundle` with default params returns ≤50KB and surfaces
non-error UCN/RM/CDLM payloads. `subset_size: 30` returns proportionally less
data. Any response that would exceed 64KB streams instead.

### Phase 6 — Tier-1 engine builds (3 weeks)

Class B from §1.3. The audit's Tier-1 missing tools that still need engine
work (varshphal/muhurta/tara/chandra are in Phase 4 because engines exist).

| Sub | Tool | Engine scope | Effort |
|---|---|---|---|
| 6.1 | `query_transits_over_natal` | Given `[date_from, date_to]`, `target_natal_point`, `orb_degrees`, scan ephemeris and return every transit event where any transit planet enters orb of the target. Audit calls this "the single most-used query in real predictive work." | M (1 week) |
| 6.2 | `query_yogas_active_now` | Given a date, cross-reference natal `yoga` category rows × current dasha state × current transits; return active/dormant yogas with activation reason. | M (1 week) |
| 6.3 | `get_planet_avastha` | Compute live avastha state (Lajjita/Garvita/Kshudita/Trushita/Mudita/Kshobhita) from current ephemeris × natal positions. Distinct from dignity. | S–M (3 days) |
| 6.4 | `get_shadbala_full` | Roll-up 19 component rows into 6 canonical Shadbala components (Sthana, Dig, Kala, Cheshta, Naisargika, Drig) + total. Either at extractor time or as a synthesis tool. | M (3–5 days) |

Acceptance: each tool has happy-path + edge-case tests; routing eval includes a
prompt for each; bench harness shows acceptable latency (<3s p95 for each).

### Phase 7 — Tier-2 engine builds (3 weeks)

The audit's Tier-2 list, minus tools that are now covered:

| Sub | Tool | Effort |
|---|---|---|
| 7.1 | `query_dasha_periods` — extend to Pratyantar + Sookshma | S (½ day) |
| 7.2 | `query_jaimini_chara_dasha` — implement the sidecar stub | M (1 week) |
| 7.3 | `query_planetary_period_predictions` — curator over BPHS/Jaimini classical-text chunks (relies on Phase 2.4 if expanding beyond BPHS) | M (1 week) |
| 7.4 | `query_dasamsha_career` — D10 chart_facts + classical interpretation rules | M (1 week) |
| 7.5 | `query_shashtiamsha` — D60 chart_facts + analysis rules | M (1 week) |
| 7.6 | `query_drekkana_drishti` — D3 + Jaimini aspect computation | S–M (3 days) |

Note: `compute_synastry`, `compute_business_chart`, `query_kp_horary` are
**deferred to Phase 12** because they depend on context that doesn't exist
today (spouse data, MARSYS founding data, KP cusp specialization).

Acceptance: each tool tested + routing-eval-prompted; data-coverage updated.

### Phase 8 — Tier-3 + sidecar-stub engines (2 weeks; defer per priority)

| Sub | Tool | Effort | Defer? |
|---|---|---|---|
| 8.1 | `query_eclipse_transits` — implement sidecar stub (writer pipeline exists) | M (3–5 days) | No |
| 8.2 | `query_planet_war` (graha_yuddha) — thin engine over ephemeris | S (1–2 days) | No |
| 8.3 | `query_remedies_prescribed` — chart-condition-indexed prescriber over remedial codex | M (3–5 days) | No |
| 8.4 | `vastu_audit` | L | **Defer to v1.1.** Different domain expertise; not blocking. |
| 8.5 | `numerology_sync` | L | **Defer to v1.1.** Same. |
| 8.6 | `compute_progressions` | M | **Defer to v1.1.** Annual-chart progression is partially covered by `query_varshphal`. |

Acceptance: 3 of 6 shipped in v1.0; 3 deferred with explicit rationale.

### Phase 9 — Server-level cross-cutting improvements (2 weeks; **[parallel with Phase 6+7]**)

Part V of the audit. Each item is independent of the tool inventory.

| Sub | Improvement | Audit ref | Effort |
|---|---|---|---|
| 9.1 | Schema parameter honour-check — every tool warns if an ignored param is supplied | P-V item 1 | M |
| 9.2 | Streaming / pagination for large responses (also Phase 5.4) | P-V item 2 | covered above |
| 9.3 | Better error messages — every error tells caller what valid values look like | P-V item 3 | S |
| 9.4 | `list_available_assets` endpoint — returns which canonical_ids resolve vs. schema-only (also Phase 1.5) | P-V item 4 | S |
| 9.5 | Coverage indicator on every category (`populated_count`, also Phase 3.5/3.6) | P-V item 5 | covered above |
| 9.6 | Tool composition recipes — pre-built workflows like `interpret_current_dasha`, `career_timing_audit` | P-V item 6 | M (2–3 days each, 3 recipes for v1.0) |
| 9.7 | Versioned corpus snapshots endpoint — `list_canonical_artifact_versions` | P-V item 7 | S |
| 9.8 | Tier surfacing in tool descriptions — every tool description names the tier(s) that can call it | P-V item 9 | S (½ day) |
| 9.9 | Multi-language Sanskrit output — Devanagari + IAST + Harvard-Kyoto encodings | P-V item 10 | M (1 week) |

Real-time ephemeris computation (P-V item 8) is **deferred** — the
pre-computed `ephemeris_daily` table covers everything until 2100; real-time
is only needed for >2100 dates or sub-day precision, neither of which is on
the v1.0 roadmap. Note in deferred items.

Acceptance: each item shipped with test; tool descriptions audited and updated;
recipes added to the catalog.

### Phase 10 — Methodology / Claude-side rules (1 week)

Part IV of the audit. These are **planner-prompt amendments and session-open
discipline rules**, not server-side code. They land in:
- `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` (R-rule additions)
- `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md` (handshake additions)
- `CLAUDE.md` (operating principles)
- `.geminirules` (MP.1 mirror)

| Sub | Rule | Audit ref |
|---|---|---|
| 10.1 | Session-start diagnostic — every session MUST call `data_coverage` + `tool_health` before substantive work | P-IV ¶1 |
| 10.2 | No date estimation — every future-dated claim MUST be sourced from `query_ephemeris` or `query_transit_event`, never extrapolated from mean motion | P-IV ¶2 (audit's own Rāhu-date error) |
| 10.3 | `log_prediction` mandatory — every substantive predictive claim gets logged with confidence + falsifier | P-IV ¶3 + audit P-I Cat-5 |
| 10.4 | `flag_disagreement` on broken tools — log formally instead of silent workaround | P-IV ¶4 + P-I Cat-5 |
| 10.5 | Cross-school convergence required before high-confidence claims (once Phase 2 ships) | P-IV ¶5 |
| 10.6 | Pre-compute and cache chart summary at session start | P-IV ¶6 |
| 10.7 | `vector_search` + `get_cgm_subgraph` proactive use (2-hop CGM walk on every key signal) | P-IV ¶7 + P-I Cat-1 |
| 10.8 | Triangulate before asserting — MSR → chart_facts → ephemeris chain | P-IV ¶8 |
| 10.9 | Mark every clause: permanent / dasha-tied / transit-tied | P-IV ¶9 |
| 10.10 | Re-read every tool's full schema before first use in session | P-IV ¶10 |

Acceptance: planner prompt v2.1+ ships with these rules; MP.1 mirror to
`.geminirules` lands same session; new session-open handshake fields validate
that 10.1 and 10.2 were honored.

### Phase 11 — Context-gap solicitation (no implementation — elicit from native)

Part III of the audit. These are **inputs we need from the native**, not code.
This phase is a structured request artifact, not a build task.

Sub-items:

11.1 — Spouse / partner birth data (date, time, place). Unlocks
`compute_synastry` (Phase 12).
11.2 — Business co-founders / key partners birth data. Same.
11.3 — Children birth data (if any). Activates 5H interpretation; enables
generational synastry.
11.4 — MARSYS founding date + time + place. Unlocks `compute_business_chart`
(Phase 12).
11.5 — Past major events with dates (10–15 minimum). Goes into LEL.
**Highest leverage of this phase.**
11.6 — Past financial milestones in detail.
11.7 — Health history dated.
11.8 — Spiritual sadhana history.
11.9 — Yantra consecration details.
11.10 — Pendant consecration details.
11.11 — Current goals beyond wealth.
11.12 — Constraints / lines not to cross.

Recommended format: a structured intake form (Cowork-rendered or Excel/Word
template); native fills it; data flows into LEL + a new `native_context.yaml`
that retrieval tools can read.

Acceptance: intake template authored; native has filled the high-leverage items
(11.5 minimum). LEL has at least 10 new dated events. `native_context.yaml`
exists in `01_FACTS_LAYER/`.

### Phase 12 — Greenfield + deferred (long tail, post-v1.0)

Class D from §1.3 + audit Tier-3 deferrals.

| Sub | Tool | Dependency | Recommendation |
|---|---|---|---|
| 12.1 | `compute_synastry` | Phase 11.1, 11.2, 11.3 | Build once spouse data is in |
| 12.2 | `compute_business_chart` | Phase 11.4 | Build once founding data is in |
| 12.3 | `query_kp_horary` | none — pure greenfield | v1.1 |
| 12.4 | `vastu_audit` | new domain context (altar placement, house layout) | v1.1 |
| 12.5 | `numerology_sync` | name analysis substrate | v1.1 |
| 12.6 | `compute_progressions` (full secondary) | classical progression engine | v1.1 |

Acceptance: each marked DEFERRED with explicit reason in the closing artifact.

---

## §3 Sequencing & dependencies

Recommended wave structure:

```
Wave 0 (½ day):  Phase 0 (diagnostic — gates everything)
                    │
Wave 1 (1 week, parallel):
  ├── Phase 1 (broken-tool fixes — independent)
  ├── Phase 4 (quick-win wrappers — independent)
  └── Phase 10 (methodology — independent)
                    │
Wave 2 (2 weeks, parallel):
  ├── Phase 2 (cross-school + classical-text scope)
  ├── Phase 3 (empty-category backfill)
  ├── Phase 5 (holistic_bundle + streaming — depends on Phase 1.5 for read_asset)
  └── Phase 11 (context elicitation — async, runs alongside)
                    │
Wave 3 (3 weeks, parallel):
  ├── Phase 6 (Tier-1 engine builds)
  └── Phase 9 (server-level cross-cutting)
                    │
Wave 4 (3 weeks):    Phase 7 (Tier-2 engine builds)
                    │
Wave 5 (2 weeks):    Phase 8 (Tier-3 + sidecar stubs)
                    │
Wave 6 (post-v1.0):  Phase 12 (greenfield + deferred)
```

Critical path: Phase 0 → Phase 2 (cross-school is the highest-rated audit
finding, and it's likely a 2-week loader build) → ship v1.0.

Each phase produces a single `CLAUDECODE_BRIEF_TOOLING_REMEDIATION_PHASE_<N>.md`
at the time it kicks off, following the MCPT v3.2 cadence convention. Briefs
are NOT authored upfront because earlier phases will inform later ones (e.g.,
Phase 0 diagnostic will change Phase 2 scope materially).

---

## §4 Coverage matrix — every audit point ↔ phase assignment

Every finding from the audit is enumerated below with its phase home. Where a
finding is deferred or out-of-scope, that's stated explicitly.

### Part I — Tool-by-tool audit (21 tools)

| Audit tool | Audit status | Phase | Notes |
|---|---|---|---|
| `chart_summary` | BROKEN | 1.1 | Highest-impact bug fix |
| `holistic_bundle` | PARTIAL | 5.1, 5.2, 5.3 | UCN/RM/CDLM fix + subset_size + return_format |
| `multi_school_bundle` / `cross_school_lookup` | BROKEN | 2.1, 2.2, 2.3 | Population + matching |
| `get_cgm_subgraph` | NOT USED | 10.7 | Methodology only — make Claude use it |
| `vector_search` | NOT USED | 10.7 | Same |
| `query_chart_facts` | WORKS (empty categories) | 3.1–3.6 | Backfill + populated_count |
| `query_signals` | PARTIAL | 1.3 | Filter enforcement |
| `query_dasha_periods` | WORKS (no PD/SD) | 7.1 | Level extension |
| `query_panchanga` | WORKS (missing fields) | 1.6 | Surface enrichment columns |
| `query_ephemeris` | PARTIAL | 1.4 | date_range + sample_step + return_changes_only |
| `query_transit_event` | BROKEN | 1.2 | event_type schema fix |
| `read_classical_text` | PARTIAL | 2.5, 2.4 | citation lookup + corpus expansion |
| `read_asset` | BROKEN | 1.5 | Prod cwd diagnosis |
| `data_coverage` | NOT TESTED | 0, 10.1 | Use in baseline + methodology |
| `tool_health` | NOT TESTED | 0, 10.1 | Same |
| `list_recent_queries` | NOT TESTED | 0 | Used in baseline |
| `get_trace` | NOT TESTED | 0 | Used in diagnosis |
| `log_prediction` | NOT USED | 10.3 | Methodology only |
| `record_outcome` | NOT USED | 10.3 | Methodology only |
| `flag_disagreement` | NOT USED | 10.4 | Methodology only |

### Part II — Missing tools (24 items across 3 tiers)

| Audit tool | Tier | Class | Phase |
|---|---|---|---|
| `query_varshphal` | T1 | A (wrap) | 4.1 |
| `query_transits_over_natal` | T1 | B (build) | 6.1 |
| `muhurta_finder` | T1 | A (wrap) | 4.4 |
| `query_yogas_active_now` | T1 | B (build) | 6.2 |
| `get_planet_avastha` | T1 | B (build) | 6.3 |
| `get_shadbala_full` | T1 | B (build) | 6.4 |
| `query_divisional_chart` | T2 | A (wrap) | 4.2 |
| `compute_synastry` | T2 | D (greenfield) | 12.1 (after 11.1) |
| `compute_business_chart` | T2 | D | 12.2 (after 11.4) |
| `query_remedial_mantras` | T2 | A (wrap) | 4.3 |
| `query_jaimini_chara_dasha` | T2 | C (stub) | 7.2 |
| `query_planetary_period_predictions` | T2 | B (build) | 7.3 |
| `query_kp_horary` | T2 | D | 12.3 |
| `tara_balam_for_native` | T2 | A (wrap) | 4.5 |
| `chandra_balam_for_native` | T2 | A (wrap) | 4.6 |
| `query_eclipse_transits` | T3 | C (stub) | 8.1 |
| `query_planet_war` | T3 | B (thin) | 8.2 |
| `compute_progressions` | T3 | D | 12.6 |
| `query_drekkana_drishti` | T3 | B (build) | 7.6 |
| `query_dasamsha_career` | T3 | B (build) | 7.4 |
| `query_shashtiamsha` | T3 | B (build) | 7.5 |
| `vastu_audit` | T3 | D | 12.4 |
| `numerology_sync` | T3 | D | 12.5 |
| `query_remedies_prescribed` | T3 | B (build) | 8.3 |

### Part III — Context gaps (12 items)

All in Phase 11 (elicitation):
11.1 spouse; 11.2 partners; 11.3 children; 11.4 MARSYS founding; 11.5 past
events; 11.6 financial milestones; 11.7 health history; 11.8 sadhana;
11.9 yantra; 11.10 pendant; 11.11 goals; 11.12 constraints.

### Part IV — Methodology (10 rules)

All in Phase 10:
10.1 session-start diagnostic; 10.2 no date estimation; 10.3 log_prediction;
10.4 flag_disagreement; 10.5 cross-school; 10.6 cache chart summary;
10.7 vector_search + cgm subgraph; 10.8 triangulate; 10.9 permanent vs
transit-tied; 10.10 read schemas.

### Part V — Server-level (10 items)

All in Phase 9:
9.1 schema honour-check; 9.2 streaming/pagination; 9.3 better errors;
9.4 list_assets; 9.5 coverage indicator; 9.6 composition recipes; 9.7 versioned
snapshots; **DEFERRED** real-time ephemeris (P-V item 8); 9.8 tier surfacing;
9.9 multi-language Sanskrit.

### Part VI — Priority list

| Audit rank | Audit item | Phase |
|---|---|---|
| 1 | Fix `chart_summary` | 1.1 |
| 2 | Fix `cross_school_lookup` | 2.1 + 2.2 |
| 3 | Add `query_varshphal` | 4.1 |
| 4 | Fix `query_ephemeris` | 1.4 |
| 5 | Provide spouse + business co-founder data | 11.1 + 11.2 + 11.4 |
| 6 | Add `query_transits_over_natal` | 6.1 |
| 7 | Populate empty chart-fact categories | 3.1–3.4 |
| 8 | Add `muhurta_finder` | 4.4 |
| 9 | Provide past major events with dates | 11.5 |
| 10 | Add MARSYS founding chart data | 11.4 |

**All 10 priority items are covered. Half are in early phases (Wave 1–2), half
need either context elicitation (Phase 11) or engine builds (Phase 6).**

---

## §5 Out-of-scope (explicit, with reasoning)

- **Real-time Swiss Ephemeris computation** — pre-computed `ephemeris_daily`
  covers all dates to 2100. Not needed for v1.0. (Audit P-V item 8.)
- **Vastu, numerology, KP horary, full progressions** — different domain
  substrates; not blocking. v1.1+. (Audit Tier 3.)
- **OCR cleaning of the existing classical-text corpus** — long, low-priority
  per-text task; not blocking on Phase 2.5 (chapter:verse lookup works even
  with noisy text). Track separately.
- **Saravali, Jataka Parijata, Uttara Kalamrita** — included in Phase 2.4 only
  if source acquisition is straightforward; otherwise v1.1. (Audit C10.)

---

## §6 What I'll do at kickoff

When this plan is approved:

1. Confirm phase ordering (especially: should Phase 11 elicitation start in
   parallel with Phase 0 so context is in by Wave 3?).
2. Author `CLAUDECODE_BRIEF_TOOLING_REMEDIATION_PHASE_0.md` for the diagnostic
   pass.
3. Open the tracker (`Plans/MARSYS_JIS_TOOLING_AUDIT_TRACKER_v1_0.md`).
4. The audit's Sankalpa session output itself — high-quality despite the broken
   tooling — gets retained as the **calibration baseline**: when chart_summary,
   cross_school_lookup, and varshphal all work, re-run a Sankalpa-equivalent
   query and diff against this audit's analysis to verify the new tools
   actually improve the output.

---

*End of MARSYS_JIS_TOOLING_REMEDIATION_PLAN_v1_0.md. 12 phases, 6 waves,
every audit finding covered (Part I 21 tools + Part II 24 missing + Part III
12 context gaps + Part IV 10 methodology + Part V 10 server-level + Part VI
top-10 priority = 87 distinct findings, all mapped). Estimated 6–10 weeks for
v1.0 (Phases 0–10 + Phase 11 elicitation); Phase 12 is post-v1.0.*
