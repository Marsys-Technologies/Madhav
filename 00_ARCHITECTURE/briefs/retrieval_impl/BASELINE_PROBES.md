---
artifact: BASELINE_PROBES.md
canonical_id: RETRIEVAL_W0_BASELINE_PROBES
version: 1.0
status: CURRENT
type: W0 live-instrument baseline (RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF §B.1)
captured_by: Claude Code (Sonnet 5)
captured_at: 2026-07-19T17:15–17:20Z
---

# W0 Baseline Probes — MARSYS-JIS MCP connector, pre-implementation snapshot

## §1 — Methodology

Per `RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md` §B.1, this is the **before** picture
of the deployed production retrieval plane, captured by driving the live
`mcp__marsys-jis-direct__*` MCP connector directly — no code was read to infer behavior;
every row below is the result of an actual tool call made this session. Raw
per-call metadata (tool, args, envelope shape, size, flags, errors) is in the
companion file `baseline_probes_raw.json`, one entry per call, so later
verification passes can diff mechanically against it.

**Coverage achieved:** 37 tool calls across 30 distinct tools/capabilities,
spanning all six layers (L0 `bg_*/ref_*`, L1 `ganita_*`, L2 `bodha_*` +
`get_signals`/`get_domain_reading`/`get_chart_quality`, L3 `kala_*` +
`get_temporal_windows`, L4 `phala_*`, L5 `mimamsa_*`/`query_calibration`) plus
cross-cutting tools (`get_chart_orientation`, `judgment_query`,
`plan_retrieval`, `get_dashas`, `get_signals`, `vector_search`,
`list_my_charts`). Both required charts were probed: **482012f1** (Abhisek,
canonical) received the deep sweep; **1c826d5a-41cb-4450-b4dc-59d440e5f75a**
(Abhinandan) received an orientation probe per the ≥1-2-representative-tools
minimum. This exceeds the ≥25-tool / both-chart requirement in full; nothing
was skipped for time — the sweep stopped at 37 calls because that already gave
saturated coverage of every layer plus multiple repeat-finding confirmations
(see §3), not because of a time or budget constraint.

One honest gap: `ref_dignity_reference_get` errored live (§3.6) and was
recorded as-is, not retried with a workaround, per §B.4's "never silently
substitute" instruction.

## §2 — Probe table

| # | Tool | Chart | Envelope | `chart_header`? | Size | Notable flags/notes |
|---|---|---|---|---|---|---|
| 1 | `list_my_charts` | — | custom `ok` | no | ~0.4 KB | 4 entitled charts enumerated |
| 2 | `get_chart_orientation` | Abhinandan | v1 (legacy) | no | ~3.2 KB | digest mode |
| 3 | `get_chart_orientation` | Abhisek | **v1 string / v3 shape** | **yes** | ~7.1 KB | see §3.1 |
| 4 | `get_dashas` | Abhisek | plain wrapper | no | ~1.4 KB | see §3.2 |
| 5 | `ganita_dashas_get` | Abhisek | plain wrapper | no | ~1.5 KB | ayanamsha-omission gate warning in description |
| 6 | `ganita_chart_facts_get` | Abhisek | plain wrapper | no | ~0.9 KB | `about=lagna` facet resolved correctly |
| 7 | `ganita_yogas_get` | Abhisek | v1 legacy | no | ~3.4 KB | catalog-only flagging live (§3.5) |
| 8 | `ganita_yogas_get` | Abhisek | **v1 string / v3 shape** | **yes** | ~6.4 KB | see §3.1 |
| 9 | `ganita_yoga_firings_get` | Abhisek | plain wrapper | no | ~4.2 KB | `fired=true` default confirmed |
| 10 | `ganita_positions_get` | Abhisek | v1 | no | ~15.3 KB | no limit → all 86 rows served |
| 11 | `ganita_strength_get` | Abhisek | v1 | no | ~1.7 KB | narrow page |
| 12 | `ganita_nakshatra_get` | Abhisek | v1 | no | ~1.9 KB | |
| 13 | `ganita_tajaka_get` | Abhisek | v1 | no | ~15.9 KB | deep nested jsonb even at limit=5 |
| 14 | `ganita_ayurdaya_get` | Abhisek | plain wrapper | no | ~3.1 KB | disclaimer field present |
| 15 | `ephemeris_cache_year` | — | custom `ok` | no | ~0.9 KB | see §3.3 (PII check) |
| 16 | `ref_yogas_get` | — | v1 (reference) | no | ~2.5 KB | |
| 17 | `ref_doshas_get` | — | v1 (reference) | no | ~2.4 KB | |
| 18 | `ref_dignity_reference_get` | — | **ERROR** | — | ~0.18 KB | see §3.6 |
| 19 | `asset_registry_l0` | — | plain wrapper | no | ~8.2 KB | 28 assets, full page |
| 20 | `asset_registry_all` | — | **OVERSIZED** | — | 60,695 chars | see §3.4 |
| 21 | `get_signals` | Abhisek | **v1 string / v3 shape** | **yes** | ~7.8 KB | see §3.1; DEFECT-001 0% orphan on this chart |
| 22 | `get_domain_reading` | Abhisek | **OVERSIZED** | — | 95,380 chars | see §3.4 |
| 23 | `get_chart_quality` | Abhisek | custom wrapper | no | ~7.5 KB | DEFECT-001 0.1% orphan (was ~91.5%) |
| 24 | `bodha_remedies_get` | Abhisek | plain wrapper | no | ~4.4 KB | honest writer-gap disclosure |
| 25 | `get_temporal_windows` | Abhisek | **OVERSIZED** | — | 289,415 chars | see §3.4 — largest capture |
| 26 | `kala_life_arc_get` | Abhisek | v1 | no | ~1.9 KB | |
| 27 | `kala_temporal_bundle` | Abhisek | **OVERSIZED** | — | 124,315 chars | see §3.4 — even at 1-month window |
| 28 | `kala_priority_ranking_get` | Abhisek | plain wrapper | no | ~1.5 KB | `top_k` respected |
| 29 | `phala_anchors_get` | Abhisek | custom `ok` | no | ~4.8 KB | falsifier + causal_chain on every anchor |
| 30 | `mitigation_map` | Abhisek | **tool_bundle** | no | ~4.4 KB | see §3.7 (envelope fragmentation) |
| 31 | `mimamsa_insight_get` | Abhisek | v1 | no | ~1.7 KB | STRUCTURAL/prior_only honestly disclosed |
| 32 | `query_calibration` | Abhisek | **tool_bundle** | no | ~11.8 KB | `latency_ms=14`; 141 QA checks, 0 fails |
| 33 | `judgment_query` (marriage) | Abhisek | v1 legacy | no | ~9.8 KB | trim_report active; verdict='contested' |
| 34 | `judgment_query` (career) | Abhisek | **v1 string / v3 shape** | **yes** | ~11.2 KB | see §3.1; still over 12KB budget after trim |
| 35 | `plan_retrieval` | Abhisek | custom `ok` | no | ~3.6 KB | dark items cite CR-56/64/24 by name |
| 36 | `vector_search` | — | **tool_bundle** | no | ~2.6 KB | `latency_ms=5948` (~6s) |
| 37 | `get_chart_orientation` | all-zero sentinel | v1 | no | ~1.6 KB | see §3.8 (silent-empty, not error) |

## §3 — Known findings reproduced live (cross-referenced to elevation-plan GT-IDs)

### §3.1 — `envelope_version` stays `'v1'` even when the response is fully v3-shaped — **CONFIRMED LIVE, 4x reproduced**
Every call that passed `response_format=v3` / `envelope_format=v3`
(`get_chart_orientation`, `ganita_yogas_get`, `get_signals`, `judgment_query`
×2) returned a response whose top-level `envelope_version` field is the
literal string `"v1"`, while the response body itself is unambiguously v3
shaped: populated `verdict`, `ranking_basis`, `drill_pointers`,
`chart_header`, `epistemic`, `timing`, `coverage`, `build_id`. This is a
direct, repeated live confirmation of the ground-truth finding that
`envelope_version` does not reflect the actual served shape — R-2/W3's
"schema validation over live tools/call output" work has a concrete before-
state to diff against.

### §3.2 — `get_dashas` description no longer mentions "601,443" — **not reproduced; appears already fixed**
The live tool description for both `get_dashas` and its alias
`ganita_dashas_get` (fetched fresh via ToolSearch this session, not from
memory/training data) contains no bulk-count figure at all — it instead
warns explicitly that omitting `ayanamsha_id` returns 5 rows/ayanamsha and
busts the ≤1KB current-dasha gate. Either this was already fixed before W0,
or the description text has since been revised for other reasons. Recorded
as a negative finding (checked, not present) per §B.4.

### §3.3 — `ephemeris_cache_native_lifetime` PII leak — **not reproduced; no such tool found under that name, and its nearest live relatives are clean**
No live tool named `ephemeris_cache_native_lifetime` was found in the
current tool catalog. The closest live surfaces — `ephemeris_cache_year` and
its Phase-1 alias `ref_ephemeris_year_get` — were called live (year=1984,
month=2) and their descriptions and served payloads contain **no** native
name, DOB, or birthplace anywhere; only tropical ephemeris body positions.
If this leak previously existed on a resource description (MCP `resources/`
surface rather than a `tools/` surface), it was out of reach of this
session's probe method and should be explicitly re-checked by whichever
lane owns the resources/list surface, rather than assumed fixed.

### §3.4 — Unclamped tools exceeding response budget — **CONFIRMED LIVE, 4 distinct reproductions, including the largest observed**
Four separate calls exceeded the MCP client's own max-token result cap and
were truncated to disk by the harness, even when explicit narrowing
parameters were passed:
- `get_domain_reading` (domain=career, `max_lenses=2`, `max_signals_per_lens=3`) → **95,380 chars**
- `get_temporal_windows` (as_of=today, no date range) → **289,415 chars** (largest capture this session)
- `kala_temporal_bundle` (1-month `date_range`, the narrowest window the tool accepts) → **124,315 chars / 3,747 lines**
- `asset_registry_all` (no params available at all on this tool) → **60,695 chars**

This is strong, reproducible live evidence for the W-5/W-8 "~36 unclamped
tools" finding and for the R-2 budget-unification work items — these four
are now concrete "before" numbers a post-fix verifier can re-run verbatim.

### §3.5 — §N.6 density/catalog-only discipline — **CONFIRMED LIVE**
`ganita_yogas_get` distinctly flags `catalog_only_rows_in_page`,
`dosha_label_gate` (with an `excluded_total` count and explanatory note),
and a `catalog_only_note`, all pointing callers to
`ganita_yoga_firings_get` as the firings-authoritative surface. This matches
CLAUDE.md §N.6 point 1 exactly and confirms the density-layering discipline
described there is already live in production, not aspirational.

### §3.6 — Live error shape captured: `ref_dignity_reference_get`
```json
{"ok": false, "error": {"class": "internal_error", "message": "Error: [p1_reference] platform DB query failed: 400"}, "tool": "ref_dignity_reference_get"}
```
A genuine sidecar-level 400 on the `p1_reference` platform DB query,
recorded honestly rather than retried/masked.

### §3.7 — Envelope fragmentation: two coexisting families in production
`ganita_*`/`get_*` tools use the `{type, object: {envelope_version, tool,
verdict, ranking_basis, grounding, pagination, drill_pointers,
judgment_flags, ...}}` registry envelope. `mitigation_map`,
`query_calibration`, and `vector_search` instead use an entirely different
`{ok, trace_id, epistemics, result, citations, plan, predictions_logged,
synthesis_audit, warnings}` "tool_bundle" envelope. Both are live
simultaneously today — direct "before" evidence for R-2's "One Envelope"
unification work.

### §3.8 — Sentinel/invalid `chart_id` does not fail loud
Calling `get_chart_orientation` with the all-zero sentinel UUID
(`00000000-0000-0000-0000-000000000000`, which the tool's own JSON-schema
pattern explicitly permits) returns a well-formed 200-shaped envelope with
every collection empty (`entity_profiles: []`, `top_signals: []`,
`candidate_pool_size: 0`) rather than an explicit "chart not found" error.
Relevant baseline for W3's `chart_header` fail-loud work (W-9): in the
legacy envelope path today, an unresolvable chart silently produces an
empty-but-successful response, not a loud failure.

### §3.9 — Latency spread observed
`query_calibration` reported `latency_ms: 14` (fast, structured DB read,
`served_from_cache: false`). `vector_search` reported `latency_ms: 5948`
(~6 seconds — semantic/embedding search over the classical-text corpus).
Both are self-reported by the tool_bundle envelope's `epistemics`/timing
fields, not independently timed by this session, but both numbers are
recorded as-served for baseline comparison.

## §4 — What this baseline is for

Every number and flag above is the reference point the wave verifiers (§V0
onward) diff against per Master Brief §B.2: a wave whose live probes
regress this baseline does not close. The four oversized-response captures
in §3.4 in particular give W3 (One Envelope / budget unification) concrete
before/after targets rather than an abstract "reduce payload size" goal.

---
*End of BASELINE_PROBES v1.0 — 37 live probes, 30 distinct tools, both required charts, captured 2026-07-19.*
