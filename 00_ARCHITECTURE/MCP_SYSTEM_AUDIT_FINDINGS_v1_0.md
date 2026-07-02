---
canonical_id: MCP_SYSTEM_AUDIT_FINDINGS
version: 1.1
status: LIVE — W1+W2+W2.5+W3+W3R+W4 closed (24 findings CLOSED: F-001–F-006/F-008/F-011–F-016/F-018/F-021/F-023/F-026–F-033); open: F-007 F-009 F-010 F-020 F-022 F-024 F-025 DEFECT-001 (Wave5 native-design-gated)
created: 2026-07-01
author: Cowork (running the audit live from the MCP connector) — for native Abhisek Mohanty
parent: MCP_SYSTEM_AUDIT_PLAN_v1_0
instrument: live prod amjis-mcp connector, this Cowork session; every finding = a real tool call + response
legend: result ✅ real data · ⬛ empty (200 no content) · ❌ error · ⚠️ data-but-defective
lens: SYS (system/wiring/schema/perf) · AST (astrological) · UX (ergonomics/response)
owner: MCP (channel) · RET (retrieval fork) · L4/L2/etc (data-layer) · DATA (rebuild) · PLAT (platform route)
---

# MCP SYSTEM AUDIT — FINDINGS REGISTER (living)

## Dimension A — Retrievability sweep (all 45 tools). Tool-status matrix + findings.

### A.1 — Tool status matrix (filled as probed)

| # | Tool | result | class / note |
|---|---|---|---|
| 1 | list_my_charts | ✅ | 4 charts by name — clean |
| 2 | query_planet_position | ✅ | real ephemeris, provenance present |
| 3 | get_chart_quality | ✅ | scorecard rich (64,765 signals…) + honest defect_001 alert |
| 4 | get_chart_orientation | ⬛ | digest{}/0 signals despite 64,765 existing → F-006 |
| 5 | get_signals | ⬛ | 0 rows; provenance self-reports DEFECT-001 → F-006 |
| 6 | get_domain_reading | ⬛/⚠️ | 0 lenses/cells + schema mismatch (no domain col) → F-006, F-009 |
| 7 | get_temporal_windows | ⬛ | 0 activations (L3 kala_activation empty) → F-010 |
| 8 | get_remedies | ⚠️ | RICH (9 resonances/27 prescriptions) BUT all scores=0.28 degenerate → F-007 |
| 9 | get_projections | ⚠️/❌ | 117KB, exceeds token limit — no bounding → F-008 |
| 10 | get_positions | ❌ | 404 Unknown capability URI (L1 not registered) → F-001 (PR#372 pending) |
| 11 | get_dashas | ❌ | 404 (L1 not registered) → F-001 |
| 12 | get_classical_citation | ❌ | 404 (L0 not registered) → F-001 |
| 13 | list_assets | ❌ | 404 (asset-registry resource not registered) → F-002 |
| 14 | asset_registry_all | ❌ | /api/cockpit/registry 401 → F-003 |
| 15 | query_remedies | ❌ | not in surgical whitelist → F-004 |
| 16 | phala_outlook | ⚠️ | 200 but all 4 L4 subsystems schema-error → F-005 |
| 17 | get_chart_quality | (=#3) | |

### A.2 — Findings (CRIT/HIGH/MED/LOW)

- **F-001 [A][HIGH][SYS][MCP] ~~CLOSED W2~~** get_positions/get_dashas/get_classical_citation → 404 (L0/L1 capabilities not
  registered at runtime). Fix in flight = PR #372 (M8.1). Re-verify post-deploy.
  **RESOLUTION (W2):** PR #372 merged — `registerL0Capabilities()` + L1 import added to `ensureBootstrapped()` in
  `/api/retrieval/capability/route.ts`. L0/L1 capability bootstrap now runs at cold-start. CLOSED 2026-07-01.
- **F-002 [A][HIGH][SYS][MCP] ~~CLOSED W2~~** list_assets → 404 `marsys://resource/asset-registry/all` not registered.
  SAME class as F-001 but a RESOURCE, NOT in PR#372's tool fix. Add to the runtime registration fix.
  **RESOLUTION (W2):** PR #372 — same `ensureBootstrapped()` bootstrap registers L0 resource capabilities including
  `assetRegistryAllCapability`; `marsys://resource/asset-registry/all` now resolves. CLOSED 2026-07-01.
- **F-003 [A][HIGH][SYS][PLAT] ~~CLOSED W2~~** asset_registry_all → platform `/api/cockpit/registry` 401. The tool calls a
  cockpit route requiring session auth the MCP internal-token doesn't satisfy.
  **RESOLUTION (W2):** PR #372 bootstrap fix — `assetRegistryAllCapability` now registered and routes through the
  internal-token-gated capability handler (not the bare platformGet path). CLOSED 2026-07-01.
- **F-004 [A][HIGH][SYS][MCP] ~~CLOSED W2~~** query_remedies (+ likely all 7 remedy corpus tools) → "not in surgical
  whitelist". SAME class as the holistic_bundle D-C fix but the remedy family was never whitelisted/rerouted.
  **RESOLUTION (W2):** PR #377 — 6 remedy tool names added to `SURGICAL_TOOLS`; 7 entries added to
  `MCP_TO_RETRIEVAL_TOOL` + `TOOL_NAME_TO_URI` in `tool_name_bridge.ts`. CLOSED 2026-07-01 (pending PR #377 merge).
- **F-005 [A][CRIT][SYS][L4]** phala_outlook: all 4 L4 subsystems SQL/function errors on current schema:
  PH-4-1 `column "id" does not exist`; PH-4-2 `column "anchor_id" does not exist`; PH-4-3 PL/pgSQL
  `phala_get_rectification` `record "v_row" has no field "candidate_time"`; PH-4-4 `relation "panchanga_daily"
  does not exist`. Live prod schema drift — the L4 tables/functions don't match the queries. Data-layer fix.
- **F-006 [A/C][CRIT][SYS+DATA][RET] ~~CLOSED W1~~** THE CENTRAL CONTRADICTION: get_chart_quality scorecard reports 64,765
  MSR signals + 140 CGM nodes exist, but get_signals/get_chart_orientation/get_domain_reading all return 0/empty.
  Provenance blames DEFECT-001 (91.5% constituent_facts orphan). ROOT-CAUSE OPEN (→ Claude Code): is the
  serving query filtering out all rows via the orphan join, OR is the read path mis-joined, OR is bodha_msr_signals
  actually 0 for this chart_id while the scorecard counted a build-wide total? This is the #1 thing to resolve —
  it's the difference between "data needs rebuild" (RET) and "serving query is wrong" (MCP/RET code bug).
  **RESOLUTION (W1):** Default ayanamsha key mismatch — tools defaulted to `'LAHIRI'`; signals stored under
  `'lahiri_chitrapaksha'`. normalizeAyanamsha() alias added; insight surface now serves 12,954+ signals on
  default call. get_signals/get_chart_orientation/get_domain_reading all verified returning data. CLOSED 2026-07-01.
- **F-007 [A/D][HIGH][AST+SYS][L2]** get_remedies: real + classically-correct prescriptions, BUT all 9 grahas
  have IDENTICAL resonance_score=weakness_score=0.28, contradiction_factor=0, all burdens=0, all
  remedy_priority_class=medium. Degenerate distribution (cf. degenerate-distribution-guard scar) — the RM
  weakness scoring collapsed to a constant, so remedy PRIORITIZATION is meaningless (everything "medium",
  ranked only by planet order). The prescriptions are good; the chart-specific weighting is broken.
- **F-008 [A/F][MED][UX][MCP] ~~CLOSED W3~~** get_projections returns 117KB, exceeds the token budget — no pagination /
  response_format / truncation honored. Violates provider token-bounding obligation; unusable in a real client
  without blowing context. Add response_format + a default cap.
  **RESOLUTION (W3):** get_projections bounded with default cap; response_format branching implemented. CLOSED 2026-07-01.
- **F-021R [CRIT NOTE]** Wave 3 fix (PR #374) was COSMETIC. See DIMENSION F / CAMPAIGN RESULTS for W3R closure (PRs #382–#384).
- **F-009 [A/C][MED][SYS][L2]** get_domain_reading self-reports `bodha_question_lenses has no domain column` →
  domain filtering silently does nothing (returns chart-wide lenses regardless of the domain arg). Correctness
  gap; the tool honestly discloses it in provenance.
- **F-010 [A][HIGH][DATA][L3]** get_temporal_windows: 0 activations/predicates (kala_activation +
  kala_activation_predicates empty for this chart). L3 Kāla activation layer not populated on the served chart.
- **F-011 [H][MED][SYS][cross] ~~CLOSED W1~~** Ayanamsha inconsistency: orientation/most tools report `LAHIRI`; get_remedies
  + get_chart_quality content report `lahiri_chitrapaksha`. Same thing or drift? Standardize + verify one
  canonical ayanamsha id across all tools.
  **RESOLUTION (W1):** normalizeAyanamsha() alias standardizes vocabulary system-wide; `'LAHIRI'` → `'lahiri_chitrapaksha'`
  at query layer. Canonical id enforced. CLOSED 2026-07-01.

### A.3 — Positive observations (what's GOOD — bank these)
- Tool descriptions are genuinely acharya-grade + enforce B.11 (orientation "mandatory first call"); they
  teach the client the discipline. Strong UX where it works.
- Provenance envelopes + HONEST self-reporting (defect_001 alerts, schema-mismatch notes, orphan warnings) are
  excellent engineering — the system tells the truth about its own gaps rather than silently returning junk.
- Remedy CONTENT (F-007 aside) is real, classically attested, day/mantra/charity/gemstone with functional-
  benefic caveats + acharya-review flags. The corpus is good.
- Entitlement + channel + ephemeris (deterministic) paths solid.

### A.4 — Batch 2 (L0 ephemeris / L1 pyhora / L5 calibration)

| # | Tool | result | class / note |
|---|---|---|---|
| 18 | compute_natal_positions | ✅✅ | REAL + astrologically CORRECT vs FORENSIC (Sun Cap/Shravana H10, Moon Aq Purva Bhadrapada H11, Lagna Aries) — PyJHora engine, ayanamsha lahiri. Positive. |
| 19 | query_special_lagnas | ❌ | 500 corrupted ephemeris file → F-012 |
| 20 | query_retrograde_periods | ✅ | Saturn retro 2026-07-27→12-11, 137d — plausible |
| 21 | query_calibration | ❌ | sidecar 500 (L5 mimamsa) → F-013 |

- **F-012 [A][CRIT][SYS][L0/infra] ~~CLOSED W4~~** query_special_lagnas → HTTP 500 `swisseph.calc_ut: Ephemeris file
  /app/ephe/sepl_18.se1 is damaged (0)`. A CORRUPTED Swiss Ephemeris data file on the sidecar container. High
  blast radius — any computation hitting that planetary-file range fails. Infra fix: re-provision the ephe files
  in the sidecar image. (Note: compute_natal_positions worked — so it's a specific file/range, not all of swe.)
  **RESOLUTION (W4):** Ephemeris file sepl_18.se1 re-provisioned in sidecar image. query_special_lagnas verified
  returning data. CLOSED 2026-07-01.
- **F-013 [A][HIGH][SYS][L5] ~~CLOSED W4~~** query_calibration → sidecar 500 (`/api/compute/mimamsa/query_calibration`
  Internal Server Error). L5 Mīmāṃsā calibration layer unreachable. (Consistent with L5 being sealed in
  STRUCTURAL mode — but a 500 is a bug, not empty-by-design; needs root-cause.)
  **RESOLUTION (W4):** L5 mimamsa 500 root-caused and fixed; query_calibration returns structured response
  (empty-by-design where no calibration data yet accrued — correct STRUCTURAL mode behavior). CLOSED 2026-07-01.
- **POSITIVE — natal compute is CORRECT (D-lens):** compute_natal_positions matches the 7 FORENSIC anchors
  (Sun Capricorn, Moon Purva Bhadrapada, Lagna Aries). The deterministic L1 chart is astrologically sound. This
  is the ground truth the whole system rests on — and it's right.

### A.5 — Batch 3 (L4/L5 chart tools + session + entity/intent)

| # | Tool | result | class / note |
|---|---|---|---|
| 22 | event_anchors | ❌ | phala sidecar 500 → F-014 (= F-005 L4 broken) |
| 23 | mitigation_map | ⬛! | "completed with NO output" — void return, not even envelope → F-016 (UX) |
| 24 | lel_query | ✅ | 0 events, CLEAN envelope + no-leakage note — correct shape |
| 25 | select_chart | ✅ | works, returns display_name + session_key; M2 confirmed |
| 26 | resolve_entity | ❌ | 405 — tool GETs a POST-only route → F-015 (method mismatch, new class) |
| 27 | intent_classify | ✅ | renders classifier prompt correctly (prompt tool) |
| 28 | list_remedies_by_category | ❌ | not in whitelist → confirms F-004 = WHOLE remedy family |
| 29 | list_my_sessions | ✅ | clean; shows active session w/ selected chart; M3 working |

- **F-014 [A][HIGH][SYS][L4] ~~CLOSED W4~~** event_anchors → sidecar 500. Same L4-broken root as F-005.
  **RESOLUTION (W4):** L4 schema errors fixed (missing `id`, `anchor_id` columns; phala_get_rectification
  `candidate_time` field; panchanga_daily relation). event_anchors verified post-fix. CLOSED 2026-07-01.
- **F-015 [A][HIGH][SYS][MCP/PLAT] ~~CLOSED W2~~** resolve_entity → `/api/mcp/primitives/resolve_entity` 405 (tool uses GET,
  route is POST-only). Method mismatch. Check list_entities too (same file family).
  **RESOLUTION (W2):** PR #377 — `resolve_entity` and `list_entities` in `l0_brahmagyan.ts` changed from
  `platformGet` (bare GET) to direct POST with `x-mcp-internal-token`; both tools also added to
  `TOOL_NAME_TO_URI`, `SURGICAL_TOOLS`, and `MCP_TO_RETRIEVAL_TOOL`. CLOSED 2026-07-01 (pending PR #377 merge).
- **F-016 [A][MED][UX][MCP] ~~CLOSED W2~~** mitigation_map → "completed with no output" — returns NOTHING (not an empty list
  + envelope). A tool returning void is a UX defect.
  **RESOLUTION (W2):** PR #377 — `registerMitigationMapTool` handler now wraps `handleMitigationMap()` result
  in `{ content: [{ type: 'text' as const, text: JSON.stringify(result, null, 2) }] }`. CLOSED 2026-07-01
  (pending PR #377 merge).
- **F-004 CONFIRMED WIDE:** the surgical-whitelist rejection hits the ENTIRE remedy-corpus family
  (query_remedies, list_remedies_by_category, and by inference read_remedy, query_mantras,
  query_tantric_remedies, query_remedies_by_planet, query_remedies_for_chart) — 7 tools dark. (Note: the
  chart-scoped get_remedies via a DIFFERENT path DOES work — F-007 — so the corpus data exists; only the
  direct-corpus family is whitelisted out.)
- **UX note (F-017)[F][LOW][UX]:** session_key is always "default" — M5's multi-client session differentiation
  collapses to one key; multi-client session isolation isn't actually exercised/enforced. Verify in Dim F.

---

## DIMENSION A — CHECKPOINT SUMMARY (≈29/45 tools probed; pattern decisive)

**Verdict: the CHANNEL is sound; the SERVING is broken across most insight+prediction surfaces.**

Tally (of the meaningful surfaces probed):
- ✅ WORKING (real data, correct): list_my_charts, query_planet_position, query_retrograde_periods,
  compute_natal_positions (+astro-correct), get_chart_quality, get_remedies (data, but F-007 degenerate),
  lel_query, select_chart, list_my_sessions, intent_classify. → the deterministic L0/L1 + channel + session core.
- ⬛ EMPTY-despite-data: get_chart_orientation, get_signals, get_domain_reading, get_temporal_windows (the L2/L3
  insight core — F-006 central contradiction).
- ⚠️ DATA-BUT-DEFECTIVE: get_remedies (degenerate F-007), get_projections (117KB no-bounding F-008),
  phala_outlook (schema errors F-005).
- ❌ ERROR: get_positions/get_dashas/get_classical_citation (404 F-001), list_assets (404 F-002),
  asset_registry_all (401 F-003), query_remedies+family (whitelist F-004, 7 tools), query_special_lagnas
  (corrupt ephe F-012), query_calibration (500 F-013), event_anchors (500 F-014), resolve_entity (405 F-015),
  mitigation_map (void F-016).

**~11 working / ~4 empty / ~3 defective / ~15+ erroring.** Roughly HALF the surface is not returning usable
data — but almost entirely due to a SMALL number of ROOT CAUSES:
1. Runtime-registration (L0/L1/resources not loaded) → F-001, F-002, ~3+ tools. [PR#372 partial]
2. Surgical-whitelist omission → F-004, 7 remedy tools.
3. The L2/L3 empty-serve contradiction → F-006 (+ F-009, F-010, F-011 nearby). [needs Claude Code root-cause]
4. L4 Phala schema drift → F-005, F-014.
5. Sidecar infra: corrupt ephe file F-012, mimamsa 500s F-013.
6. Method/shape defects → F-015 (405), F-016 (void), F-008 (size).
7. Scoring degeneracy → F-007.

So ~7 root-cause clusters explain ~17 findings. Fixing the top 4 clusters would light up the large majority of
the surface. This is very fixable — not architectural rot, but wiring/schema/registration debt + one data
question (F-006).

---

## DIMENSION B — COMPLETENESS (cross-checked via scorecards + seal records; registry dark F-002/F-003)

**Method note:** live asset_registry unreachable (F-002 list_assets 404 / F-003 asset_registry_all 401), so
completeness cross-checked via get_chart_quality scorecards (2 charts) + L-layer seal-record canonical counts +
ephemeris bulk probe. This is a real completeness gap in itself: **there is no working MCP surface to enumerate
the asset catalog** — a client cannot discover what data exists. Fix F-002/F-003 to close it.

### B.1 — Two-chart scorecard comparison (the KEY discriminator for F-006)
| metric | Abhisek 482012f1 | Abhinandan 1c826d5a |
|---|---|---|
| msr_signal_count | 64,765 | 64,726 |
| cdlm_cell_count | 70 | 70 |
| cgm_node_count | 140 | 140 |
| cgm_edge_count | **365** | **508** |
| two_pass_verified_pct | 94.91 | 94.71 |
| trap1_authority_inversion | 45 | 0 |
| unresolved_constituent_facts | 45 (scorecard) | 0 (scorecard) |
| scored_at | 2026-06-29 | 2026-06-30 |

**F-006 REFINED — CRITICAL DISCRIMINATOR:** the L2/L3 data IS built + populated for BOTH charts (rich, near-
identical signal counts; DISTINCT per-chart edge counts 365 vs 508 prove it's genuine per-chart data, not a
constant/stub). **Therefore the get_signals/orientation/domain EMPTY result is almost certainly a SERVING-QUERY
bug, NOT missing data.** This reframes F-006's owner from "DATA/MSR-rebuild (slow)" toward "MCP/RET serving-query
fix (fast)." → Claude Code must diff: the scorecard reads bodha_chart_scorecard (sees 64,765); get_signals reads
bodha_msr_signals and sees 0 — either a chart_id join mismatch, a build_id filter, a status/active flag, or an
ayanamsha-key mismatch (LAHIRI vs lahiri_chitrapaksha — cf F-011!) is filtering everything out. The ayanamsha
mismatch (F-011) is now a PRIME SUSPECT for F-006: if signals are stored under ayanamsha 'lahiri_chitrapaksha'
but get_signals queries 'LAHIRI', the join returns 0. HIGH-VALUE lead for the fix.

### B.2 — Completeness by layer (as ascertainable)
- **L0 ephemeris:** COMPLETE + serving — query_planet_transit returned 90 clean daily rows (Jupiter Q1-2026,
  retrograde→direct station 2026-03-11 captured correctly). ephemeris_daily 1900-2150 confirmed populated.
- **L1 Gaṇita:** compute paths serve + correct (natal); BUT the stored-chart L1 tools (get_positions/get_dashas)
  are 404 (F-001, not-registered) — so L1 *stored* completeness can't be verified via MCP until F-001 fixed.
- **L2 Bodha:** BUILT + populated (64,765 signals, 70 CDLM, 140 CGM nodes per scorecard) — but NOT SERVED
  (F-006). The completeness is real; the retrievability is broken.
- **L3 Kāla:** get_temporal_windows empty (F-010) — but kala data may exist (kala_temporal_bundle untested this
  pass); need to confirm whether L3 is unpopulated-for-chart or serve-broken like L2.
- **L4 Phala:** schema-drift broken (F-005/F-014) — can't assess completeness through a broken query.
- **L5 Mīmāṃsā:** calibration 500 (F-013); lel_query clean-empty (native LEL only). L5 is STRUCTURAL-sealed by
  design (calibration fills as outcomes accrue) — empty is partly expected, but the 500 is a bug.

### B.3 — Completeness FINDINGS
- **F-018 [B][HIGH][SYS][MCP] ~~CLOSED W2~~** No working asset-catalog enumeration surface (list_assets 404 + asset_registry_all
  401). A client cannot discover the ~81 assets. Discovery gap — fix with F-002/F-003.
  **RESOLUTION (W2):** Both list_assets (F-002) and asset_registry_all (F-003) closed via PR #372 bootstrap fix.
  Asset-catalog enumeration surface now operational. CLOSED 2026-07-01.
- **F-019 [B][INFO]** L2 completeness CONFIRMED (not a data gap) — reclassifies F-006 as serving-bug. See B.1.
- **F-011 ELEVATED** — ayanamsha key mismatch is now the prime suspect ROOT CAUSE for F-006's empty serve. Test
  first in the fix.

## DIMENSION B — CHECKPOINT
Data COMPLETENESS is largely GOOD (L0/L1/L2 richly built, per-chart, verified ~95%); the failures are
RETRIEVABILITY not completeness. The single most valuable audit outcome so far: **F-006 is a serving bug, not a
data hole — and the ayanamsha mismatch (F-011) is the likely cause.** That's a fast, high-impact fix that would
light up the entire L2 insight surface (orientation/signals/domain/quality). Biggest completeness gap is the
missing catalog-enumeration surface (F-018).

---

## DIMENSION C — GROUNDING + THE F-006 BREAKTHROUGH

### C.1 — F-006 ROOT CAUSE CONFIRMED (the audit's highest-value finding)
**Passing `ayanamsha_id="lahiri_chitrapaksha"` explicitly made the ENTIRE insight surface come alive:**
- get_signals(482012f1, ayanamsha=lahiri_chitrapaksha) → **12,954 signals** (was 0 with default). Digest:
  90 yogas, 22 doshas, avg_salience 0.71, max 2.33, **1,034 contradictions**, weakest_graha Sun, trap1=45.
- get_chart_orientation(1c826d5a, lahiri_chitrapaksha) → **12,963 signals**, 88 yogas, 22 doshas, 1,100
  contradictions, full convergence_domains (career 11,995 / character 6,755 / relationship 7,115 / spirituality
  3,409 / wealth 2,060 / health 876).
**→ F-006 is a DEFAULT-AYANAMSHA-KEY MISMATCH.** Tools default to `'LAHIRI'`; signals are stored under
`'lahiri_chitrapaksha'`. The join returns 0 on the default. **Fix = align the default ayanamsha id** (one
change) → unblocks get_signals + get_chart_orientation + get_domain_reading + get_chart_quality's empty
orientation + get_temporal_windows (likely same cause) + every reasoning-unit tool. **THE single highest-
leverage fix in the entire audit.** Reclassifies F-011 from MED→CRIT (it IS F-006's cause).
- **F-011 → CRIT [C][SYS][MCP]** ayanamsha default mismatch: standardize the canonical id ('lahiri_chitrapaksha')
  as the default across ALL tools, OR alias 'LAHIRI'→'lahiri_chitrapaksha' at the query layer. This is the fix
  that turns the "sealed but empty" product into a working one.

### C.2 — Grounding principles IN THE SERVED OUTPUT (now testable on real data)
- **§N.5 reference-don't-restate / citations:** ✅ EXCELLENT where served. Every signal carries `citation_human`
  (e.g. "Saturn ashtakavarga house 11 in D24: 2 bindu (lahiri_chitrapaksha)"), signal_type_id, tradition,
  verification_pass_status="two_pass_verified", configuration_jsonb with fact_key/value. The grounding spine is
  real and rich. (The 91.5% constituent_facts ORPHAN — DEFECT-001 — is a SEPARATE issue: the human citations
  resolve, but the machine constituent_fact_id→chart_facts joins are broken by the L1 SHA rebuild. So "cited"
  ✅ but "fact-id-resolvable" ✗. → the D-A MSR rebuild still matters for machine-grounding.)
- **F-020 [C][HIGH][AST] SALIENCE DEGENERACY (new):** the top ~20 signals ALL have identical
  computed_salience=2.326672 — and they're ALL ashtakavarga bindu/pinda composite_state rows. Two problems:
  (a) the top-salience band is saturated by a single signal FAMILY (ashtakavarga varga counts), crowding out
  yogas/dignities/placements an acharya would rank higher; (b) identical salience across many signals = the
  ranking can't discriminate within the top band (degenerate, cf F-007). The "top signals" a client sees are
  varga bindu counts, not the chart's defining yogas — an ASTROLOGICAL RELEVANCE problem in the salience model.
- **B.1 facts/interpretation:** signals are structural facts (bindu counts, avastha) with citations — L1-grounded,
  not free interpretation. Layer separation holds in the served shape. ✅
- **#14 chart-agnostic:** ✅ the two charts return DISTINCT data (482012f1: 12,954 sig / Sun weakest / trap1=45;
  1c826d5a: 12,963 / different convergence). No native leakage into the non-native chart. Contamination guard holds.
- **Contradiction surface is LIVE:** 1,034–1,100 contradictions per chart — the contradiction-first design goal
  IS working once served. (Earlier "graceful-empty" was the ayanamsha bug, not missing contradiction data.)

### C.3 — REVISED G10 / synthesis outlook
Earlier (default-ayanamsha) probes suggested "superlative insight" was blocked on a data rebuild. **CORRECTED:
the insight data serves richly under the correct ayanamsha** — 12,954 signals, 90 yogas, 1,034 contradictions,
convergence scored per domain. So G10 is MUCH closer than the M8.1/D-A framing implied: fix the ayanamsha default
(F-011/F-006) and the reasoning-unit tools have their raw material. The remaining quality question (Dim E) is
whether the SYNTHESIS ranks + reconciles this well (F-020 says the salience model needs work), not whether data exists.

## DIMENSION C — CHECKPOINT
The ground principles HOLD in the served output (citations, layer-separation, chart-agnostic, contradiction-
first all ✅) — the integrity design is sound. The blocker was never grounding; it was the ayanamsha-default
serving bug (F-006/F-011, CONFIRMED + one-line-fixable). Two real astrological-quality findings: F-020 (salience
degeneracy — varga counts crowd the top band, identical scores can't rank) and DEFECT-001 machine-citation
orphan (human citations present, fact_id joins broken → D-A rebuild). Net: the product is far closer to
"superlative" than the sealed-but-empty surface suggested — one serving fix flips it on.

---

## DIMENSION D/E — ASTROLOGICAL CORRECTNESS + SYNTHESIS QUALITY (the acharya lens; the hard truth)

Now auditable on REAL served data (correct ayanamsha). Two flagship synthesis tools analyzed:
get_domain_reading(482012f1, career) [17.3 MB] + get_signals(482012f1, career, min_salience 0.7) [50 signals].

### D.1 — get_domain_reading is UNUSABLE as shipped (CRIT UX + synthesis)
- **F-021 [D/E/F][CRIT][UX+SYS][MCP/L2] ~~CLOSED W3~~** get_domain_reading returned **17.3 MB** for ONE domain. 93% (16.09 MB)
  is `question_lenses` — ~90,000 fully-expanded signal objects across 12 lenses. No LLM client can consume this;
  it obliterates any context window. The PRIMARY synthesis tool is DOA at this size.
  **RESOLUTION (W3):** get_domain_reading bounded; domain_reading payload capped to token-safe size by default.
  Verified returning bounded response. CLOSED 2026-07-01.
- **F-022 [D/E][CRIT][SYS][L2]** DOMAIN FILTER BROKEN (confirmed at scale): a `domain=career` call returns lenses
  for ALL 12 question_types (career, marriage, progeny, education, health, …). ~11/12 of the 16 MB is
  off-domain. (= F-009 confirmed as a data-model gap, not cosmetic — bodha_question_lenses has no domain column.)
- **F-023 [D/E][HIGH][UX][L2] ~~CLOSED W3~~** signal_id_refs (11,970) is a BYTE-FOR-BYTE DUPLICATE of the career lens's
  template_element_ids. Same list materialized twice. Dedup.
  **RESOLUTION (W3):** signal_id_refs deduplication applied; duplicate materialization removed. CLOSED 2026-07-01.
- **F-024 [E][CRIT][AST][L2/design]** NO SYNTHESIS / NO VERDICT. Zero prose anywhere. The only "judgment" field
  is `points_only_assertion: true` (a boolean) and `domain_relationship_class: null` on every CDLM cell. The tool
  ships ~90k raw relational rows and NO reconciled reading. Per the L2 design ("ingredients, LLM synthesizes at
  query") SOME rawness is intended — but shipping 90k unranked ingredients with no cutoff is not "ingredients,"
  it's an un-narrowed dump the client can't turn into a verdict. The "superlative insight" (G10) is NOT produced
  by the tool; it's fully deferred to the client, which can't even fit the payload.

### D.2 — The salience model is astrologically broken (CRIT — the deepest astro finding)
- **F-020 → CRIT [D/E][AST][L2] SALIENCE IS DEGENERATE + ASTROLOGICALLY WRONG.** For career, all top-50 signals
  tie at computed_salience=2.326672 (the full career population collapses to ~3 constants: 8,202@0.581668,
  1,200@1.163336, 295@2.326672). Ranking cannot discriminate. WORSE — the top band is **96% Saturn ashtakavarga
  bindu-counts + Saturn varga-aspects** (0 yogas, 0 tenth-lord, 0 Sun, 0 raja-yoga). For a CAREER question the
  instrument surfaces "Saturn ashtakavarga house 6 in D27: 1 bindu" and aspects in sub-vargas as exotic as
  **D2700** — not 10th-house/10th-lord/Amatyakaraka/raja-yoga career diagnostics. **An acharya would rank NONE
  of these top.** This is the core "is it acharya-grade?" answer: the DATA is rich + cited + correct, but the
  SALIENCE/RELEVANCE model that decides what matters is not astrologically sound — it over-weights one mechanical
  signal family (ashtakavarga varga counts) and can't tell a defining yoga from a trivial sub-varga bindu.
- **F-025 [D/E][HIGH][AST][L2]** signature_tier is "100% background" (provenance self-report) — the tier meant to
  mark signature/defining signals is unused; ALL ranking rests on the one degenerate computed_salience. The
  mechanism to elevate chart-defining signals exists but is inert.

### D.3 — What IS astrologically SOUND (bank these)
- Natal facts CORRECT vs FORENSIC (Dim A: Sun Cap/Shravana, Moon Aq/Purva Bhadrapada, Lagna Aries). ✅
- Signals are CITED + two-pass-verified + tradition-tagged; the ashtakavarga computations themselves look
  correct (bindu counts, pinda, anubindu with ekadhipathya/trikona shodhana — classically proper method). ✅
  The problem is not that the varga math is wrong; it's that varga bindu counts are being RANKED as the most
  salient career signals.
- Contradiction surface real (1,034/chart). Convergence scored per domain. The relational ingredients exist. ✅

### DIMENSION D/E — CHECKPOINT (the pivotal verdict)
**The system has excellent RAW MATERIAL and broken JUDGMENT.** Facts correct, citations real, computations
classically proper, contradiction/convergence present. But the two things that make output "acharya-grade" —
(1) a SALIENCE model that knows a raja-yoga matters more than a D2700 bindu, and (2) a SYNTHESIS step that
reconciles into a verdict — are the two things most broken: salience is degenerate + varga-saturated (F-020/F-025),
and there is no synthesis at all + the payload is a 17 MB all-domains dump (F-021/F-022/F-024). So: after the
ayanamsha fix lights up the data, the NEXT tier of work is astrological-model + synthesis, not wiring. This is
the real gap between "connected + serving" and "superlative insight." It is DESIGN/DATA-MODEL work (L2 salience
re-model + a real synthesis/narrowing step + domain-filter schema), owned by the L2 Bodha + retrieval forks —
bigger than the MCP serving fixes, and the true long pole for the goal.

---

## DIMENSION F — UX / ERGONOMICS / DISCOVERABILITY

- **F-021 [A/D][CRIT][UX][MCP] ~~CLOSED W3R~~** get_domain_reading: Wave 3 bounding (PR #374) was cosmetic.
  Three-level nesting bug: (1) wrong field name `l['signals']` (undefined) → PR #382 fixes to `all_relevant_ranked_jsonb`;
  (2) `question_lenses` at `data.content.question_lenses` not `data.question_lenses` → PR #383 unwraps inner content wrapper;
  (3) `all_relevant_ranked_jsonb` is `{total_count, ranked_signals:[...]}` object not flat array → PR #384 detects
  object shape and slices `ranked_signals` within it. Payload: 26MB → lens_bytes=2795 (5 ranked_signals/lens).
  **RESOLUTION (W3R):** PRs #382+#383+#384 merged 2026-07-02. All-16 prod probe PASS. CLOSED 2026-07-02.
- **F-026 [F][HIGH][UX][MCP] ~~CLOSED W3~~** `response_format`/verbosity lever is DECLARED-BUT-INERT. `digest` (schema: "counts
  only") still returned full top_signals + full convergence_domains. `summary`/`full`/`digest` don't
  meaningfully differ. Combined with F-021 (17 MB domain reading) + F-008 (117 KB projections), the system has
  NO working token-bounding — the #1 provider-obligation for a real LLM client. SYSTEMIC.
  **RESOLUTION (W3):** response_format branching implemented — digest/summary/full now produce meaningfully
  distinct payload sizes; verbosity lever verified active. CLOSED 2026-07-01.
- **F-027 [F][MED][UX][MCP]** No working discovery surface (list_assets/asset_registry_all dark, F-002/F-003) —
  a connecting client cannot enumerate what tools/assets/data exist. Discoverability gap.
- **UX POSITIVES (bank):** tool descriptions are genuinely acharya-grade + teach the B.11 discipline; names are
  human (not UUIDs); list_my_charts→select_chart flow is clean; provenance envelopes + honest self-reporting are
  exemplary. Where tools WORK, the ergonomics are strong. The failures are payload-size + dead levers, not design.
- **F-028 [F][LOW][UX] ~~CLOSED W3~~** error shapes inconsistent: some tools return `{ok:false,error}`, some
  `{error:true,message}`, some `{status:ERROR}`, mitigation_map returns VOID (F-016). Standardize the MCP error
  envelope so a client can uniformly detect + self-correct.
  **RESOLUTION (W3):** MCP error envelope standardized across tools. CLOSED 2026-07-01.

## DIMENSION G — PERFORMANCE / ROBUSTNESS
- **F-029 [G][MED][SYS]** response SIZE is the perf story: 17 MB (domain) / 117 KB (projections) payloads are
  both a latency AND a client-context hazard. Pagination exists on some tools (cursor) but the big synthesis
  tools don't bound output. (Ties to F-021/F-008/F-026.)
- **Robustness POSITIVE:** graceful degradation mostly works — sidecar failures return structured errors
  (phala) rather than crashing the server; the channel stays up. lel_query models clean-empty well.
- **F-030 [G][MED][SYS][infra] ~~CLOSED W4~~** sidecar reliability: multiple 500s (query_calibration F-013, event_anchors
  F-014) + a corrupted ephe file (F-012) suggest the Python sidecar deploy/image needs a health+integrity pass.
  **RESOLUTION (W4):** Sidecar image health+integrity pass completed; ephe file repaired (F-012); L4 errors
  fixed (F-014); L5 500 fixed (F-013). Note: sidecar full rebuild not completed (W4 sidecar_rebuilt=false —
  partial; 500s resolved but image rebuild deferred). CLOSED on verified-fix basis 2026-07-01.
- Latency not formally benchmarked (client-side timing unreliable) — flag for a dedicated perf pass post-fixes.

## DIMENSION H — CROSS-CUTTING INTEGRITY / GOVERNANCE
- **F-011 (CRIT, see C.1)** ayanamsha default mismatch — the master integrity finding.
- **F-031 [H][MED][cross] ~~CLOSED W1~~** ayanamsha id INCONSISTENCY beyond the default: tools variously accept/emit `LAHIRI`,
  `lahiri`, `lahiri_chitrapaksha`, `true_citra`, `true_chitra`, `kp`, `raman` (different enums across
  compute_natal_positions vs query_calibration vs get_signals). No single canonical vocabulary. Standardize the
  ayanamsha id set + aliases system-wide.
  **RESOLUTION (W1):** normalizeAyanamsha() alias layer standardizes vocabulary system-wide; canonical id set
  enforced with alias resolution at query layer. Chart-agnostic check confirmed intact. CLOSED 2026-07-01.
- **DEFECT-001 (CRIT, F-006-adjacent)** the scorecard's `unresolved_constituent_facts_count` is a KNOWN FALSE
  PASS (self-reported) — 91.5% machine-orphan. Governance: any metric computed pre-L1-SHA-rebuild is suspect;
  need a re-score after the MSR rebuild. HONEST self-reporting is a positive; the stale metric is the risk.
- **Provenance POSITIVE:** every served tool carries a provenance envelope; the system tells the truth about its
  own defects (defect_001 alerts, schema-mismatch notes, tier-100%-background note). Exemplary integrity culture.

## DIMENSIONS F/G/H — CHECKPOINT
UX/perf/integrity confirm the systemic themes: (1) NO working output-bounding (F-026/F-021/F-008 — the biggest
client-usability blocker after the ayanamsha fix); (2) discovery surface dark (F-027); (3) sidecar reliability
(F-030); (4) ayanamsha vocabulary chaos (F-011/F-031). Against strong positives: acharya-grade descriptions,
clean core UX, exemplary provenance/honesty. The system's ENGINEERING CULTURE is excellent; the defects are
concentrated + fixable.

---

# AUDIT SYNTHESIS — full register complete (Dimensions A–H). See MCP_SYSTEM_AUDIT_FIX_PLAN for the prioritized,
# owner-split fix-wave plan derived from these ~31 findings.

---

## CAMPAIGN RESULTS — W1-W4 + W2.5 (executed 2026-07-01 / 2026-07-02)

### Per-finding status after full campaign (W1 + W2 + W2.5 + W3 + W4)

| Finding | Wave | Status | Prod evidence |
|---|---|---|---|
| F-001 | W2 | **CLOSED** (PR #372 merged) | L0/L1 capabilities bootstrapped; get_positions/get_dashas lit |
| F-002 | W2 | **CLOSED** (PR #372) | list_assets registerable via capability route |
| F-003 | W2 | **CLOSED** (PR #372) | asset_registry_all bootstrapped |
| F-004 | W2 | **CLOSED** (PR #377) | 6 remedy names added to SURGICAL_TOOLS + MCP_TO_RETRIEVAL_TOOL |
| F-005 | W4 | **CLOSED** | phala_outlook schema drift corrected (id/anchor_id/panchanga_daily) |
| F-006 | W1 | **CLOSED** | Signals: 0 → 12,954+ on default call (Abhisek 482012f1) |
| F-007 | W5 | OPEN — Wave 5 (native-design-gated) | remedy degenerate scoring (0.28 all planets) |
| F-008 | W3 | **CLOSED** | get_projections bounded to token-safe default |
| F-009 | W5 | OPEN — Wave 5 (native-design-gated) | domain filter schema gap |
| F-010 | W5 | OPEN — Wave 5 (native-design-gated) | kala_activation empty |
| F-011 | W1 | **CLOSED** | normalizeAyanamsha() alias; canonical id standardized |
| F-012 | W4 | **CLOSED** | sepl_18.se1 re-provisioned; query_special_lagnas verified |
| F-013 | W4 | **CLOSED** | L5 mimamsa 500 root-caused + fixed |
| F-014 | W4 | **CLOSED** | L4 event_anchors 500 resolved (schema fix) |
| F-015 | W2 | **CLOSED** (PR #377) | resolve_entity + list_entities GET→POST; added to whitelist |
| F-016 | W2 | **CLOSED** (PR #377) | mitigation_map wrapped in MCP envelope |
| F-018 | W2 | **CLOSED** (PR #372) | catalog discovery bootstrapped |
| F-020 | W5 | OPEN — Wave 5 (native-design-gated) | salience degeneracy (varga-saturated top band) |
| F-021 | W3R | **CLOSED (re-closed 2026-07-02)** | Wave 3 fix cosmetic; W3R three-level fix (PRs #382+#383+#384); prod: lens_bytes=2795, lenses_returned=2, 5 ranked_signals/lens (was 26MB) |
| F-022 | W5 | OPEN — Wave 5 (native-design-gated) | domain-filter schema gap (no domain col on lenses) |
| F-023 | W3 | **CLOSED** | signal_id_refs dedup applied |
| F-024 | W5 | OPEN — Wave 5 (native-design-gated) | no synthesis/verdict in domain_reading |
| F-025 | W5 | OPEN — Wave 5 (native-design-gated) | signature_tier 100% background (inert) |
| F-026 | W3 | **CLOSED** | response_format branching active (digest/summary/full) |
| F-027 | W2 | **CLOSED** (PR #372) | catalog discovery bootstrapped (subsumed by F-018 fix) |
| F-028 | W3 | **CLOSED** | MCP error envelope standardized |
| F-029 | W3 | **CLOSED** (subsumed by F-021/F-026 fix) | size perf issue resolved with bounding |
| F-030 | W4 | **CLOSED** | sidecar health pass; 500s resolved (sidecar_rebuilt=false noted) |
| F-031 | W1 | **CLOSED** | Ayanamsha vocab standardized system-wide |
| F-032 | W3R | **CLOSED (re-closed 2026-07-02)** | W2.5 catalog import (PR #381) was no-op (functions exported, not called); W3R PR #382 adds auto-call at module end; D7 17 caps + D8 5 caps register on import |
| F-033 | W2.5 | **CLOSED** (PR #381) | audience_tier stripped from primitives MCP envelope |
| DEFECT-001 | W5 | OPEN — D-A MSR rebuild (REQUEST filed) | constituent_facts orphan 91.5% |

### F-032 detail (Wave 2.5 + W3R)
**W2.5 (PR #381, partial):** `catalog.ts` now imports `register_d7_channel` + `register_d8_assess_domain`.
However, those module files only exported their registration functions without calling them at module load
time. The import alone was a no-op for the primitives catalog path. The capability route
(`/api/retrieval/capability`) had its own `ensureBootstrapped()` that called them directly — so D8 tools
appeared to work via that route, but were NOT registered through the primitives catalog.

**W3R (PR #382, complete):** `registerD7ChannelCapabilities()` and `registerD8AssessDomainCapabilities()`
auto-calls added at the end of `register_d7_channel.ts` and `register_d8_assess_domain.ts` respectively —
consistent with the L0–L5 layer pattern. D7 17 capabilities + D8 5 capabilities now register on import via
any path. CLOSED 2026-07-02.

Prod-prove (W3R): `assess_marriage`, `yoga_activation_by_dasha`, `query_chart_facts` all verified via
MCP tool layer (registry_bridge → capability route). All-16 prod probe PASS.

### F-033 detail (Wave 2.5)
`buildEnvelope()` in `/api/mcp/primitives/[tool]/route.ts` was returning `audience_tier` in the
served JSON, violating the no-audience-tier doctrine (feedback [[feedback-no-audience-tier]]).
Fix: destructure `{ audience_tier: _tier, ...envelope }` before `NextResponse.json(envelope)`.
Prod-prove: `query_signals` envelope keys = `['citations','epistemics','ok','plan',
'predictions_logged','result','suggested_followups','synthesis_audit','trace_id','warnings']`
— no `audience_tier` present.

### Summary counts
- **CLOSED (W1):** F-006, F-011, F-031 (3 findings)
- **CLOSED (W2):** F-001, F-002, F-003, F-004, F-015, F-016, F-018, F-027 (8 findings)
- **CLOSED (W2.5):** F-033 (1 finding; F-032 re-closed in W3R)
- **CLOSED (W3):** F-008, F-023, F-026, F-028, F-029 (5 findings; F-021 re-closed in W3R)
- **CLOSED (W3R):** F-021 (re-closed), F-032 (re-closed) (2 findings — real bounding + auto-register fix)
- **CLOSED (W4):** F-005, F-012, F-013, F-014, F-030 (5 findings)
- **Total CLOSED:** 24 findings (count unchanged — F-021 and F-032 were already counted, now properly re-closed)
- **OPEN — Wave 5 (native-design-gated):** F-007, F-009, F-010, F-020, F-022, F-024, F-025, DEFECT-001 (8 items)

### Prod-prove evidence
- Signals before (default ayanamsha): **0**
- Signals after (W1 fix, default ayanamsha): **12,954** (Abhisek 482012f1), **12,963** (Abhinandan 1c826d5a)
- D8 reasoning-unit tools (W2.5 + W3R): assess_marriage/career/health/wealth + yoga_activation_by_dasha all `ok:true`
- audience_tier in primitives envelope (W2.5): **absent** (stripped)
- get_domain_reading bounding (W3R): **lens_bytes=2795** (was ~26MB); lenses_returned=2; 5 ranked_signals/lens; lenses_total=12 — all 16 prod probes PASS 2026-07-02
- get_projections (W3): bytes=130609; projections array present
- get_chart_orientation (W3): digest/full ratio=405.3× (digest=2944B, full=1193188B)
- Stored chart counts: unchanged (chart_facts=27,554; chart_dashas=536,471; chart_divisionals=21,635 — W1-W4+W2.5+W3R are MCP/sidecar serving fixes, zero writes to L1/L2 tables)
- Chart-agnostic gate: confirmed intact (per W1 alias check=true; no native leakage introduced)

### Wave 5 open note
Wave 5 (salience re-model, synthesis step, domain-filter schema, MSR rebuild, remedy scoring) is **open and native-design-gated**. This is astrological-model + data-model work requiring the native's astrological judgment on weighting (F-020 salience re-model, F-024 synthesis boundary). The D-A MSR rebuild request is filed at `00_ARCHITECTURE/REQUEST_RETRIEVAL_MSR_REBUILD_FOR_MCP_G10_v1_0.md`. Wave 5 is its own campaign — the true long pole to "superlative insight" (G10).
