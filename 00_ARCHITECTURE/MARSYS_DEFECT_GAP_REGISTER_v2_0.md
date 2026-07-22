---
canonical_id: MARSYS_DEFECT_GAP_REGISTER
version: 3.13
status: LIVING — the authoritative, exhaustive register of every known defect + coverage gap in the
  MARSYS-JIS instrument as of 2026-07-10, resynced 2026-07-16 (D-1.6 Lane S-8, Section 13). Add
  rows, never silently drop them. Each row closes only with a fix PR + [verify-against] evidence
  recorded in the Status/Evidence column. CR-90..107 (POST_REMEDIATION_CONSUMPTION_REGISTER §J/K/L
  range) are NOT rows in this file — system-of-record for that range is
  DOCTRINE_CAMPAIGN_EXECUTION_PLAN_v1_0.md §8 + the doctrine-wave briefs, per Section 13 below.
created: 2026-07-10
supersedes: MARSYS_DEFECT_GAP_REGISTER_v1_0.md (2026-07-09) — all v1 rows carried forward with
  re-verified statuses; v1 retained in place per hygiene §A (archival retain-in-place).
author: Cowork (Fable-5) — full-estate end-to-end audit 2026-07-10, five parallel lanes —
  (1) live MCP probe of the Gaṇita + reference estate, (2) live probe of Bodha + flagship instruments,
  (3) live probe of Kāla/Phala/Mīmāṃsā/remedies/catalog, (4) read-only code audit verifying every v1
  root-cause citation + adjacent sweep, (5) astrological concept-completeness audit of the classical
  canon vs L0 Brahmagyan + chart 482012f1. Charts: 482012f1 (Abhisek) · 1c826d5a (Abhinandan).
scope: the whole instrument — L0–L5 build assets, retrieval/serving, MCP, prediction infra, concept coverage.
purpose: feed the R6 "Yoga & Cancellation Integrity + Coverage" campaign and successors. This register
  IS the backlog; campaign briefs draw their scope from it.
audit_verdict_summary: >
  Gaṇita substrate confirmed deep and largely correct (all 7 FORENSIC anchors reproduced live across
  ayanamshas; Mercury sole-vargottama rollup correct; no cross-chart contamination; ~90% classical-canon
  concept coverage at L0/L1, exceeding the canon on several axes). The defects cluster in four bands:
  (1) the yoga/cancellation integrity crisis (v1 Section 1, now root-cause-pinned to the line);
  (2) a serving layer that is the true weakest link — dead tools, silent parameter no-ops, unbounded
  payloads up to 1.04MB, facet mis-routing, and receipts that claim ✓ with zero evidence;
  (3) data-correctness defects invisible to per-row checks (pre-birth anchors, duplicate cycles,
  degenerate distributions, wrong denormalized columns);
  (4) an empty Kāla activation layer + dark ephemeris sidecar that together open-circuit the entire
  dated-prediction promise, plus an empty LEL that open-circuits calibration.
---

# MARSYS DEFECT & GAP REGISTER v2.0

## Legend
**Gap type:** `DATA` never computed · `PERSIST` computed but not stored · `SURF` stored but not served
(or served unlabeled) · `LOGIC` computed/served but WRONG · `INFRA` service/deploy · `UX` tool-contract
ergonomics · `DOC` description over-claims coverage.
**Severity:** `CRITICAL` serves fabricated/wrong astrology on the most common questions · `HIGH` material
astrological miss or blocks a core capability · `MED` real gap, moderate reach · `LOW` edge/polish.
**Status:** `OPEN` · `IN-PROGRESS` · `FIXED` (with evidence) · `PARTIAL`.
**Source tags:** `[probe-G]` live Gaṇita/ref probe · `[probe-B]` live Bodha/flagship probe ·
`[probe-K]` live Kāla/Phala/Mīmāṃsā probe · `[code]` code audit · `[concept]` concept-completeness audit.
All live probes 2026-07-09/10 against prod MCP, read-only.

---

## SECTION 1 — YOGA & CANCELLATION INTEGRITY (the crisis — now root-cause-pinned)

### v1 rows re-verified

| ID | Title | Gap | Sev | v2 verification (2026-07-10) | Status |
|----|-------|-----|-----|------------------------------|--------|
| Y-1 | **Vacuous-pass fabricated yoga surface** | LOGIC+SURF | CRITICAL | **VERIFIED-STILL-OPEN, both charts** [probe-G]. `ganita_yogas_get` serves the whole OCR catalog as `requires_pass`: garbage subjects `cnja_kesari`, `dariclra`, `datidra`, `kemidruma`, `kimadruma`, non-yogas `each`/`another`; contradictory Kemadruma+Gaja-Kesari; total=107, identical on 1c826d5a. **Root cause pinned** [code]: `_evaluate_catalog_rule` at `ga_writers/ga_structural_writer.py:4471-4534` — corpus-extracted rules carry `{"requires":[{"raw_verse_clause":…}]}` (`l0_yogas.py:1960-1963`); the loop matches only `relation`/`planet` req shapes, skips `raw_verse_clause` silently, falls through to `return True,"requires_pass"` (:4534). Unknown relations correctly return False; unknown req *shapes* vacuously pass. `"requires":[]` would also pass. L0 aggravator: dual curated+OCR entries (`gajakesari` AND `gaja_kesari`) in bg catalog. | FIXED [verify-against: prod, R6 2026-07-10] |
| Y-2 | **Honest yoga engine (`ga_yoga_firings`) unwired** | SURF | CRITICAL | **VERIFIED-STILL-OPEN** [code]. Re-ran grep: 0 hits in `platform/src/lib/retrieval/` and `platform-mcp/src/`. Table exists (mig 240, enriched 411), written by `ga_yoga_writer.py:1194-1211`, registry-counted — zero serving readers. `ganita_yogas_get` (register_p1_ganita.ts:378) serves the Y-1 label pass instead. | OPEN |
| Y-3 | **NBRY effectively absent** | DATA+LOGIC | CRITICAL | **VERIFIED-STILL-OPEN** [probe-G][code]. Live: keyword `neecha` → 0 facts (482012f1); L0 `ref_rules_search("neecha bhanga")` → 0 rows too — the vocabulary gap spans L0+L1. Code: catalog rule `debilitated_planet_with_cancelled_debility` (l0_yogas.py:731-744 incl. `bhanga_any` ×4 rules) is in ga_yoga's skip tuple (ga_yoga_writer.py:956); ga_structural returns `relation_unimplemented`; the only real evaluator (simplified) is dead legacy behind the catalog-load fallback (:1727-1737). NBRY fires nowhere, on any chart, by any live path. NOTE: L1 *does* compute `graha_composite_state_classification="debilitation_cancelled"` (dispositor-in-kendra, ga_structural:2586-2591) — the verdict exists under another name and nothing consumes it (see Y-6, D-3). | OPEN |
| Y-4 | **House-lord yoga family undetected** | DATA+LOGIC | HIGH | **CONFIRMED with a split** [code]. Viparita/Dhana/Daridra/Shakata: skip-listed (ga_yoga_writer.py:936-964). **Correction:** Dharma-Karmadhipati + Kendra-Trikona-Raja are NOT skip-listed — they have live branches (:918-934) calling `_check_house_lord_association`/`_check_kendra_trikona_raja` which are hardcoded `return False` stubs (:1049-1066, "Return False to avoid fabrication"). Same outcome, different fix (implement helpers vs de-skip-list) — split as Y-8. Legacy real logic: Viparita defs at ga_structural:253-261; house-lord evaluators :1740-1774 — all dead. | OPEN |
| Y-5 | **Cancellation as a class unimplemented** | DATA | HIGH | **CONFIRMED** [code]. ga_yoga_writer.py:1179-1191: `bhanga_active=NULL` + na_reason for everything except Kemadruma. Dead catalog columns confirmed at l0_yogas.py:715,727,899,909 + NBRY's own `bhanga_any` (:734-738). Nothing reads `cancellation_conditions` except the na_reason string builder. (ga_yoga at least floors honestly; the ga_structural label pass doesn't.) | OPEN |
| Y-6 | **D9 cross-check + salience blind to cancellation** | LOGIC | HIGH | **CONFIRMED, mechanism sharper** [code]. bo_laksana.py:1417-1418 hardcodes `neechabhanga_modifier=1.0, cancellation_modifier=1.0`; main path :933-934 reads `tags.get("neechabhanga", 1.0)` — and NO L1 writer ever emits those tags, so the default applies chart-wide. formulas.py:110-111 documents the 1.3/0.1 modifiers; :154-155 multiplies an always-1.0 value. The computed `debilitation_cancelled` classification (Y-3 note) is never consumed. | OPEN |

### New rows (v2)

| ID | Title | Gap | Sev | Evidence | Fix approach | Status |
|----|-------|-----|-----|----------|--------------|--------|
| Y-7 | **Vacuous fires stamped `two_pass_verified`** — every yoga/dosha label row (incl. Y-1 garbage) written with top verification status; bo_laksana `verification_rescale` maps it to 1.00 (strongest epistemic weight) | LOGIC+DATA | HIGH | [code] ga_structural_writer.py:1827-1845 | Unevaluable rule shapes → `(False,"rule_shape_unimplemented:<keys>")` mirroring the `relation_unimplemented` branch; label rows carry a verification status distinct from computed facts | FIXED [verify-against: prod, R6 2026-07-10] |
| Y-8 | **Dharma-Karmadhipati + Kendra-Trikona-Raja helpers are silent `return False` stubs** — appear implemented, can never fire, no marker distinguishing "evaluated false" from "stub" | LOGIC | HIGH | [code] ga_yoga_writer.py:918-934 branches → :1049-1066 stubs | Implement using existing chart_facts house-lord categories (ga_structural computes `_get_house_lord`), or move to skip-list so non-evaluation is explicit | OPEN |
| Y-9 | **Exclusion clauses in formation rules never enforced** — no handler for `exclude` req shape (e.g. Shakata's `jupiter_in_kendra_from_lagna`); today masked by Y-1, but any Y-1 fix MUST handle this class or rules will fire despite violated exclusions | LOGIC | MED | [code] l0_yogas.py:894-895 vs ga_structural_writer.py:4472-4534 (no `exclude` handler) | Implement exclude handling or hard-fail unknown req keys — bundle with the Y-1 fix | FIXED [verify-against: prod, R6 2026-07-10] |
| Y-10 | **Skip-list comment launders the gap** — "The ga_structural writer (GA8) does yoga_fires rows that handle these" is FALSE (relation_unimplemented; capable legacy path dead). Also duplicate skip entry `lagna_lord_and_9th_lord_associate` (:939, :959) | DOC | MED | [code] ga_yoga_writer.py:965-970 | Correct comment to "unimplemented anywhere"; dedupe | OPEN |
| Y-11 | **Degenerate constituent grounding across the whole yoga/dosha family** — all 107 label rows per chart cite ONE identical constituent fact_id (chart A `e2b47b2c6d457725`, chart B `2ddd8464544d8c35`); B.3 derivation-ledger intent defeated | DATA | HIGH | [probe-G] both charts | Writer emits actual constituent graha/house fact_ids per yoga; build gate fails when a grounding column collapses to a single value (degenerate-distribution guard) | OPEN |
| Y-12 | **`ganita_yogas_get` v3 verdict fabricates chart-level negatives from a truncated page** — with limit=3 it asserted "No Pancha Mahapurusha yoga is formed" while `yoga_label.sasa` (Sasa Yoga, BPHS Ch.75/Saravali Ch.27) exists for 482012f1; envelope also reports `yogas_fired:0`, `coverage.served:0`, `category_counts:{}` while serving 60 rows | SURF+LOGIC | HIGH | [concept][probe-G] live calls | Verdict from a dedicated full-count query, or suppress verdict when `pagination.total > served`; populate envelope counts before v3 default flip | OPEN |
| Y-13 | **R6A.3's redemption-map consult excludes pure-D9-context NBRY firings — `broken_promise` is structurally unredeemable** — `bo_laksana.py`'s `_build_nbry_redemption_map` only flips a `broken_promise` classification when the matching `ga_yoga_firings.bhanga_rule_fired` entry is tagged `D1` or `D1->D9`; it never consults a bare `D9`-tagged firing. But `broken_promise` is *by definition* the D1-strong/D9-weak case — the D9 weakness IS what's being judged, so its redemption is exactly a `D9`-context firing, which the filter throws away. Caught live on the native chart `482012f1`'s real Saturn (exalted Libra D1, debilitated Aries D9, redeemed via NBRY rule 2 — `bhanga_rule_fired='saturn@D9:nbry_rule_2_exaltation_lord_kendra'`): `neecha_bhanga_raja_yoga` fired correctly with `bhanga_active=true`, but the D9 cross-check for Saturn still read `broken_promise` in 4/5 ayanamshas post-rebuild (R6A.6 guarded rebuild, halted, chart restored from snapshot per native's no-iteration-on-native-chart instruction). Not caught by R6A.1/R6A.2/R6A.3's own tests or two Ring-2 reviews because no prior real data (synthetic fixtures or Abhinandan's real Jupiter case) happened to exercise a pure-D9-context `broken_promise` redemption path — same "cross-chart-data-path exposure" class as M-23 (ph_nimitta). | LOGIC | CRITICAL | [R6A.6, live guarded native-chart rebuild, 2026-07-11] `bodha_msr_signals` `signal_type_id='navamsha_d9_cross_check:saturn'` chart `482012f1`, `ga_yoga_firings.bhanga_rule_fired` for `neecha_bhanga_raja_yoga` | Widen the redemption consult to the varga-of-weakness principle: for `broken_promise` specifically, also consult pure-`D9`-context firings (not just `D1`/`D1->D9`), behavior-gated to that one classification path so no other classification's output changes; regression-tested against double-application (a D1-context redemption must not also re-apply via the widened D9 consult) and against unredeemed negative controls | OPEN — fix-iteration approved by native 2026-07-11, in progress |

## SECTION 2 — ASTROLOGICAL SURFACING & COVERAGE

### v1 rows re-verified

| ID | Title | Gap | Sev | v2 verification | Status |
|----|-------|-----|-----|-----------------|--------|
| S-1 | **Vargottama/special-states not joined into judgment surfaces** | SURF | HIGH | **VERIFIED-STILL-OPEN** [probe-B][code]. Live: graha_portrait(Mercury@482) — dignity D1/D9 "neutral Capricorn", no vargottama flag anywhere; narration "consistent read across D1/D9"; digest brands Mercury `weakest_graha`. Code: gradeGraha (register_d9_judgment.ts:129-171) queries exactly two categories (dignity_per_varga D1 + shadbala_total); graha_portrait.ts:158 enum has no special_states. Rollup exists and is CORRECT (live: MER is_vargottama=true, 8 others false). | OPEN |
| S-2 | **Special lagnas mis-aliased** | SURF+LOGIC | MED | **PARTIALLY FIXED** [probe-G][code]. `ganita_special_lagnas_get` (compute path) now returns bhava_lagna + kaala/mrityu/yama/gulika/maandi — but HORA/GHATI/VIGHATI still absent from its payload. The stored-facts path still broken: get_sensitive_points.ts:11-19 `SP_CATEGORIES` omits `special_lagna` (also `sun_derived_upagraha`, `bhava_arudha`, `arudha_pada`) while ga_sensitive emits them (writer:2055,2077,2085,2094). | PARTIAL |
| S-3 | **Bhava arudha computed, unserved** | SURF | MED | **CONFIRMED, wording tightened** [code]. Full 2-exception A1–A12 + AL/UPA at ga_sensitive_writer.py:1324-1418; no serving tool reads `bhava_arudha` (get_karakas.ts:13 serves only `arudha_pada`). Nuance: address_resolver.ts:417 consumes it internally for arudha reference-frame re-basing — so not "zero refs", but zero serving. | OPEN |
| S-4 | **Graduated sputa drishti not computed** | DATA | MED | **APPEARS-FIXED — RECLASSIFY** [concept]. `_build_virupa_drishti_rows` exists (ga_structural:5326), unit `virupa_strength`, per-varga. Verify served, then close. | **ROUTE_TO_LANE S-5** [D-1.6 S-7/S-8, 2026-07-16: `ganita_structural_get(facet=aspects)` declares `aspect_parashari_given/_received` in its categories but the default page leads with `aspect_jaimini` rasi-drishti boilerplate; `virupa_strength` rows not observed on the served page — this IS the standing A7 PARK (writer verified correct in D-1.5a; 19 real rows exist in DB; serving-layer facet routing never landed). Data computed; serving incomplete. Merged into Lane S-5's PARK-A7 + R-17 facet-routing item (already first bullet of that lane)] |
| S-5 | **Gandanta computed, unserved** | SURF | MED | **APPEARS-FIXED** [concept]. `graha_gandanta` per graha + lagna confirmed live via MCP (all false for 482012f1 — legitimately). Verify category is in a tool enum permanently, then close. | CLOSED_WITH_EVIDENCE [D-1.6 S-7, 2026-07-16: ganita_sensitive_degrees_get serves per-graha gandanta rows with degree evidence (e.g. JUP not_gandanta, arc 3.3333°, deg_in_sign 9.7875 — honest negative), inside the 55-row sensitive_degree_check category; check_type filter exposed; permanently in a tool enum] |
| S-6 | **Pushkara flags in no tool enum** | SURF | LOW-MED | **VERIFIED-STILL-OPEN** [concept]. PUSHKARA tables coded (ga_vargas_writer.py:162-169), stored in chart_divisionals; keyword+category MCP probes → 0 rows. Subsumed by S-12 (divisional serving hole). | OPEN |
| S-7 | **Per-varga siblings unserved** | SURF | MED | **STILL-OPEN** (partially subsumed by S-12). `aspect_jaimini_per_varga` verified live-served; the avastha/yuddha/ashtakavarga per-varga siblings remain outside tool enums. | OPEN |
| S-8 | **Effective dignity claim ≠ computation** | LOGIC+DOC | MED | **CONFIRMED, WORSE** [code]. Computation (ga_structural:2699-2719) is a 15°-longitude-proximity ±0.25 tweak — not drishti at all (no 7th-house, no special aspects, no rashi drishti, no bhanga) vs get_dignity.ts:25 claim. Adjacent bug: `dignity_scores` map (:2717) lacks `own`/`moolatrikona`/`friend`/`enemy` keys → those states silently score neutral 0.5 (split as D-8). | OPEN |
| S-9 | **Mrityu bhaga not computed** | DATA | MED | **CONFIRMED** [concept]. L1 computes mrityu *sphuta* (`esoteric_point_mrityu`) — a different concept; no per-sign fatal-degree proximity flag found. | OPEN |
| S-10 | **Indu/Sree/Varnada lagnas prototype-only** | DATA | LOW-MED | **PARTIALLY FIXED** [concept]. ga_sensitive now computes Indu, Hora Lagna, Pranapada + ghati/varnada family; `ganita_special_lagnas_get` computes the full PyJHora set on demand. Residual = S-2 serving gaps. | PARTIAL |
| S-11 | **Tool descriptions over-claim** | DOC | MED | **CONFIRMED** [code]. register_p1_ganita.ts:244-248 (condition: "neecha-bhanga/vargottama" — neither in served categories); :346-357 (yogas: "Viparita, Neecha Bhanga, Parivartana" — none can fire per Y-1/3/4); get_dignity.ts:25. | OPEN |

### New rows (v2)

| ID | Title | Gap | Sev | Evidence | Fix approach | Status |
|----|-------|-----|-----|----------|--------------|--------|
| S-12 | **Divisional-chart serving hole — 21,635 chart_divisionals rows MCP-invisible** — vargottama variants, pushkara, per-varga dignity, D108/D150/D2700 all computed; `divisional_query` registered in tool_name_bridge.ts:62 + get_divisionals.ts exists, but the tool is not on the live MCP surface; `query_chart_facts(divisional_chart=D9, category=varga_position)` → 0 rows. Any LLM reading raw D9/D10 placements over MCP must recompute | SURF | HIGH | [concept] live probes + code | Wire divisional_query/`ganita_vargas_get` into the MCP channel (the sealed≠served keystone, again) | CLOSED_WITH_EVIDENCE [D-1.6 S-7, 2026-07-16: ganita_chart_facts_get(divisional_chart=D2|D9) serves a chart_divisionals-native divisional_facts section (D2: 200 rows; D9: 178 rows — per-varga dignity, vargottama, pushkara bhaga/navamsha, house lords/occupants, deities, rollups), budget-capped and source-tagged (D-1.5b PR #575). The EAV layer is MCP-visible] |
| S-13 | **Coverage-matrix CI gate enumerates a stale hardcoded category snapshot** — the "every fact_category maps to ≥1 tool" R3 gate checks a list authored 2026-06-16; `special_lagna`, `bhava_arudha`, `sun_derived_upagraha` are absent from the list itself, so the S-2/S-3 class can never fail CI | SURF+DOC | HIGH | [code] platform/src/lib/retrieval/registry/layers/L1_ganita/coverage_matrix.ts:14+ | Derive the gate list from live `SELECT DISTINCT fact_category FROM chart_facts` (or writer manifests) at gate time — this one fix converts the whole S-family into CI failures | OPEN |
| S-14 | **ga_medical / ga_vastu have no direct MCP read tool** — computed (floors 45/40), reachable only via assess_health/apex_health (which are themselves broken per R-8) | SURF | LOW-MED | [concept] | Thin `ganita_medical_get` / `ganita_vastu_get` reads | CLOSED_WITH_EVIDENCE [D-1.6 S-7, 2026-07-16: both tools live and chart-scoped: ganita_medical_get → 9 rows (per-graha dosha/organ watch, indication tiers, BPHS citations, not_diagnosis flag); ganita_vastu_get → 8 rows (graha→direction, condition_score, Mayamata citations). Matches CR-31 "shipped" note] |
| S-15 | **`percentile_within_class` — the CORRECT stored percentile has zero readers** — mig-393 `salience_pctl_in_class` computed with proper PERCENT_RANK (bo_laksana.py:1576-1613), written, never read; served value recomputed at query time in composite_ranker.ts:242-263 over composite_score with first-occurrence `indexOf` tie-ranking + singleton→1.0 hardcode; coarse categorical sub-scores (incl. Y-6's dead modifiers) make whole classes tie → flat 1.0 (subsumes v1 R-3 root cause) | SURF+LOGIC | MED | [code] both paths pinned | Serve the stored `salience_pctl_in_class` (one join); fix or delete the query-time recompute | OPEN |

## SECTION 3 — PREDICTION / TIMING INFRASTRUCTURE

### v1 rows re-verified

| ID | Title | Gap | Sev | v2 verification | Status |
|----|-------|-----|-----|-----------------|--------|
| T-1 | **Ephemeris/transit sidecar dark → TRIGGER never completes** | INFRA+DATA | HIGH | **VERIFIED-STILL-OPEN** [probe-B][probe-K]. pact_query TRIGGER: exact text "Ephemeris sidecar unreachable or returned no rows … (honest gap, not fabricated)", status `unreachable`. kala_temporal_bundle: `sidecar_available:false`, mode `fallback_empty`, all four assets empty. Phala anchors show `av_transit_potency:0` — transit contribution absent everywhere. The phala_outlook half of v1 T-1 APPEARS-FIXED (PH-4-1/PH-4-2 SQL errors gone, anchors populate). | OPEN |
| T-2 | **Forward panchanga** | INFRA+DATA | HIGH | **PARTIALLY FIXED** [probe-K]. `kala_muhurta_get` returns 15 real, varied, ranked windows (Aug 2026) with genuine panchanga citing mig-427 rolling table; beyond +12mo honest empty-with-reason. BUT flagship-name `muhurta_finder` is completely dead (T-7) and marriage windows include Ekadashi/Vaidhriti/Chaturdashi (quality issue, see C-4). | PARTIAL |
| T-3 | **Activation-window boundary imprecision** | LOGIC | MED→HIGH | **SPLIT VERDICT — root cause pinned, WORSE than registered** [probe-G][probe-B][code]. Tool level: `ganita_dashas_get(as_of=2027-09-01)` now correctly returns Ketu MD — FIXED there. Pact path: STILL-OPEN and worse — ACTIVATION for as_of 2027-09-01 cites Mercury MD + two Saturn ADs ALL ending before the as_of date, never mentions Ketu, and `pact_status:"chain_complete"`/`stages_completed:4` counts the unreachable TRIGGER as complete. Root cause [code]: (1) `as_of_date` never forwarded — register_d10_pact.ts:200-201 calls judgment without it; register_d9_judgment.ts:431-433 hardcodes `new Date()` (server clock, UTC — also wrong for IST between 00:00-05:30); (2) get_dashas.ts:240 inclusive-both-ends containment matches both periods on changeover dates; judgment's limit:5 + all_levels makes the served level set arbitrary. | OPEN (upgraded) |

### New rows (v2)

| ID | Title | Gap | Sev | Evidence | Fix approach | Status |
|----|-------|-----|-----|----------|--------------|--------|
| T-4 | **L3 kala_activation EMPTY for the native chart — the entire Kāla timing surface returns zero** — kala_windows_get, get_temporal_windows, kala_yoga_activation_get, yoga_activation_by_dasha: 0 rows for ANY window 2026–2029; temporal_bundle timeline/convergence/obstruction all 0 | DATA/PERSIST | HIGH | [probe-K] all four tools, chart 482012f1 | Run/verify ka_yojaka→ka_kalasutra build for 482012f1; add count_sql floor alert so an empty activation table can't pass silently | OPEN |
| T-5 | **Phala anchors predate the native's birth** — career_entry anchors with windows 1964–1998 (incl. 1964/1966, 20 years pre-birth) tagged `horizon_tier:"near"`; mitigations with window_start 1966/1995; source `mode_c/SUBSYSTEM/Saturn@Aquarius` cycles projected unclipped over the whole lifetime | LOGIC | HIGH | [probe-K] phala_predictive_anchors_get domain=career; phala_outlook mitigations | Clip mode_c cycle enumeration to [birth_date, horizon_end] at ph_nimitta build; seal gate rejecting anchors with window_end < birth or < today for "near" tier | OPEN — R6 2026-07-10: code fix (ph_nimitta clip) merged & live in prod, but downstream rebuild did NOT complete for 482012f1 before this probe — phala_anchors(482012f1) still 58/400 pre-birth rows, min(window_start)=1964-01-26. phala_anchors(1c826d5a) IS clean (0/104). Needs rebuild re-run for 482012f1. **FINAL STATUS (2026-07-10, after extensive dedicated effort): STILL OPEN, NOT FIXED.** Code fix confirmed live in prod; downstream rebuild remains incomplete after 7+ retry attempts. Root causes pinned, not resolved: (1) a real, previously-undocumented orchestrator bug — `run_asset()`'s initial `state=building` transition never refreshes `asset_throughput.last_built_at`, so the Cloud-Scheduler watchdog's 15-min staleness reaper can fire almost immediately for long single-substep (non-heartbeating) writers like `ga_strength` (~11min) rather than after 15 real minutes; this is FROZEN-orchestrator-adjacent and needs native review per CLAUDE.md §N.2, not a unilateral patch; (2) repeated forced DB-connection kills during this session (at least one traced to another lane's unauthorized backend-kill incident, others unexplained) interrupted otherwise-clean progress multiple times. Two small, unrelated, already-merged fixes came out of this effort (ga_dashas dict_row bug, ga_structural dosha-catalog crash, statement_timeout guards) but the T-5 rebuild itself did not complete. Deferred to a dedicated follow-up session with either the watchdog issue resolved/raised first, or the watchdog paused for one clean uninterrupted closure run. |
| T-6 | **Duplicate-anchor spam, no serve-time cap on drill-down aliases** — phala_anchors_get 421KB, EVERY row identical window 2026-07-08→2026-10-06 + confidence 0.322; phala_mitigation_get 528KB (largest payload of the audit); phala_outlook has trim_report but the drill-downs it points to don't | DATA+SURF | HIGH | [probe-K] | Dedup on (domain,event_type,window,signal) at ph_nimitta; apply R5.3 budget envelope to alias handlers | OPEN |
| T-7 | **`muhurta_finder` returns nothing at all** — no windows, no empty_reason, no error object; twice, valid ranges; it is the documented `recover_via` target in phala_outlook's trim_report. Sibling `kala_muhurta_get` works | INFRA | MED-HIGH | [probe-K] business Aug–Sep 2026 + marriage Aug 2026 | Trace the non-alias route; likely unreturned promise / empty response-stream write | FIXED [verify-against: prod, R6 2026-07-10] |
| T-8 | **Stale hardcoded dasha citation "Mercury MD (2026-2043)"** — every kala_muhurta window cites FORENSIC DSH.V.023 with a WRONG MD span (truth: Mercury MD ends 2027-08-18 → Ketu); `ad_lord:"unknown"` on all windows so dasha_quality is MD-only mislabeled | LOGIC | MED | [probe-K] kala_muhurta_get provenance | Read MD/AD live from chart_dashas; drop hardcoded span | OPEN |
| T-9 | **Life-arc parvas begin 1950 — 34 years pre-birth** — kala_life_arc_get serves chapters starting 1950 for a 1984 native; also 171KB with limit ignored | LOGIC+SURF | MED | [probe-K] | Clip parva enumeration to birth; honor limit | OPEN — R6 2026-07-10: code fix (ka_jivana_parva clip) merged & live in prod, but downstream rebuild did NOT complete for either chart — kala_jivana_parva(482012f1) 67/260 pre-birth (min start_year=1950); kala_jivana_parva(1c826d5a) 84/280 pre-birth. Needs rebuild re-run both charts. **FINAL STATUS (2026-07-10): STILL OPEN, NOT FIXED** — same root causes and disposition as T-5 above (shared rebuild attempt, shared blockers). Deferred to a dedicated follow-up session. |
| T-10 | **kala_projections degenerate clustering** — 123KB, dozens of rows share window_start 2027-10-20; get_projections (Bodha surface): max_projections=3 ignored (20 returned), ALL 20 identical (same peak/window/score 0.7/narrative), top-level `projections_total:0` contradicts content count 20 | DATA+LOGIC | HIGH | [probe-K][probe-B] | Dedup by (domain,window,tier) into one anchor with n_support; honor max_projections; remove dead top-level fields; distribution-collapse gate on projection writer | OPEN |
| T-11 | **LEL corpus EMPTY in prod for the canonical native chart → calibration open-circuited** — lel_query(482012f1) unfiltered → 0 events (provenance cites LIFE_EVENT_LOG v1.7); yet every event_anchors falsifier requires `attestation_required:"lel_entry"` — no anchor can ever be confirmed/refuted. mimamsa STRUCTURAL mode is by design, but an empty LEL is not | DATA/PERSIST | HIGH | [probe-B] | Run LEL intake for 482012f1 (57-event corpus exists as markdown) or serve "corpus not built for this chart" explicitly | OPEN |
| T-12 | **Anchor generator tracks ONE transit cycle only — 2000-01→2022-04 has ZERO dated anchors at any confidence** — every retrodictive anchor in the estate derives from the single `mode_c/SUBSYSTEM/Saturn@Aquarius` cycle (~29.5y period); no dasha-conditioned variety, no other graha cycles, no birth-date gating. 22 years of the native's life carry no claim; recall on major events ≈4-6/15, all inside one window. The multi-signal convergence design premise is absent from what's served | DATA+LOGIC | CRITICAL | [accuracy-test 2026-07-10] blind extraction §5; DISCOVERY_ENGINE_ACCURACY_TEST_v1_0.md | Anchor generation must consume the full convergence substrate (dasha×transit×yoga-activation) once T-1/T-4 land; seal gate: dated-anchor coverage of the natal lifespan must exceed a floor (e.g. ≥60% of adult years carry ≥1 claim) and anchor `cited basis` must show >1 distinct source cycle | OPEN |
| T-13 | **"Near" anchor windows are a build-date artifact** — the standing near-term window (2026-07-08→2026-10-06, 31-69 duplicate rows) is exactly build-date + 90 days, not an astrologically derived window; generic "career/transition discovery event" claims attach to it from σ-anomaly discoveries with no independent timing basis | LOGIC | MED-HIGH | [accuracy-test] blind extraction F1/F2 | Near-tier windows must cite a timing basis (dasha boundary, transit ingress, activation row) or be labeled "monitoring window (no timing signal)" — never presented as a prediction | OPEN |
| T-14 | **Cross-surface score contradiction for the same claim** — the 2027-10-20→2030-04-03 window is served at 0.70/"tier_1_high" by kala_projections/get_projections and 0.3725 by event_anchors, same basis (kala_bhavishya/1423); a consumer gets a 2x confidence swing depending on which tool it calls | LOGIC | MED | [accuracy-test] blind extraction F3 vs F4 | Single scored source of truth per claim; serving surfaces read the same posterior; add cross-surface consistency probe to the canary battery | OPEN |
| T-15 | **`muhurta_finder` hard-rejects a literal "next 3 months" query — 92-day range 422s against an undisclosed 90-day cap** — distinct from T-7 (T-7 = tool returns nothing with valid ranges; this = tool explicitly errors `"date_range spans 92 days; maximum is 90 days"` on the R5.3 B4 battery item's own literal args, reproduced twice, live). `next 3 months` is plain-English and genuinely spans 90-92 days depending on start date; either the cap should accommodate the phrase's natural intent or the tool should clamp+serve rather than hard-fail | LOGIC/UX | MED | [R5.3 B4, verify-against: prod 2026-07-10] `results_90a14176.json` Q6-N-1: `error.class=orchestrator_error`, sidecar 422 | Either raise the cap to ~92-95 days or auto-clamp the requested range to the cap and serve a partial result with an honest note, rather than a hard error | OPEN |

## SECTION 4 — RETRIEVAL / SERVING QUALITY

### v1 rows re-verified

| ID | Title | Gap | Sev | v2 verification | Status |
|----|-------|-----|-----|-----------------|--------|
| R-1 | **Budget/trim not universal** | SURF | HIGH | **VERIFIED-STILL-OPEN, WORSE** [all probes]. Measured un-budgeted payloads: assess_career **1.04MB**; ephemeris_cache_year 815KB; phala_mitigation_get 528KB; phala_anchors_get 421KB; ganita_condition_get default 304KB (no narrowing filters exist); apex_wealth_assess w/ min limits 194KB; kala_life_arc_get 171KB; ganita_chart_facts_get D9-pivot 149KB (worse than the 116KB registered); kala_projections_get 123KB; get_cgm_subgraph 75KB; bodha_graph_traverse_get 71.5KB (limit=5, max_depth=1 ignored); event_anchors 620KB (no pagination params at all); mimamsa_lel_query 61KB (limit ignored); ganita_positions_get default 67KB. C1 budgets hold on judgment (~10.5KB≤12) + portrait (~10KB≤12); pact ~9.5KB vs 8KB budget (~20% over). query_remedies size PARTIAL-FIXED [R5.3 B2/B3, PR #510, verify-against: prod 2026-07-10] — re-measured live post-deploy at 12,941 bytes (was 105,935; 8.2x reduction), compact envelope confirmed; but the underlying filter defects remain OPEN, see R-19 (not R-10 — corrected mis-citation), so the SIZE fix does not mean the tool returns correct/filtered results yet. | OPEN |
| R-2 | **Epistemic grade not derived** | LOGIC+SURF | MED | **VERIFIED-STILL-OPEN** [probe-B]. All v3 envelopes both charts: `grade:"structural_prior", verified_fraction:null, "No epistemic signal computed"`. | OPEN |
| R-3 | **percentile_within_class flat 1** | LOGIC | MED | **VERIFIED-STILL-OPEN**; root cause + fix now pinned at S-15 (stored correct value unread; query-time recompute degenerate). | OPEN → see S-15 |
| R-4 | **Stale provenance-note literals** | LOGIC | MED | **FIXED** [probe-B][code]. Live probes show freshness-derived notes with expiry (DEFECT-001 "RESOLVED 0/2 (0%)" per page / "MOSTLY_RESOLVED 1.1%" chart-wide; signature_tier real distribution). Code: freshness_notes.ts re-derives live (E-2 contract); canary_probes.ts:195 exists to catch regressions. Close. | FIXED (R5.x, verified live 2026-07-10) |
| R-5 | **Denial ≠ empty** | LOGIC | MED | **STILL-OPEN, sharpened** [probe-B]. Empty results (lel_query 0 rows `ok:true`) carry no built-vs-denied disambiguation; errors leak raw SQL (`column "salience_score" does not exist`) instead of a typed envelope. | OPEN |
| R-6 | **graha_portrait include-enum ergonomics** | UX | LOW | **VERIFIED-STILL-OPEN** [probe-B]. `include:["special_states"]` → invalid-option error; `functional_nature` is served but absent from the enum (cannot be requested or excluded). | OPEN |
| R-7 | **Digest family-aggregation** | LOGIC | LOW-MED | **PARTIALLY FIXED** [probe-B]. Family collapse live (300 atomic → 76/102 family rows), no literal duplicates in digest top band. Residuals: top band is a uniform-score wall (fifteen 0.7875 nakshatra-trivia rows ranked "major"); synth_chart_brief top_discoveries still emits literal duplicates ("…sade_sati signals" ×4 at salience 1.2). | PARTIAL |

### New rows (v2) — dead tools

| ID | Title | Gap | Sev | Evidence | Fix approach | Status |
|----|-------|-----|-----|----------|--------------|--------|
| R-8 | **assess/apex family unbounded — assess_career 1.04MB** — catastrophic; no bounding at all on the legacy 8-tool family; apex_wealth with minimum limits still 194KB | SURF | HIGH | [probe-B] | Apply R5 trim/budget envelope + pagination to the legacy assess estate (or retire in favor of judgment_query) | OPEN |
| R-9 | **bodha_discoveries_get DEAD — schema drift** — 500: `column "salience_score" does not exist`; the Bimba discovery layer is MCP-unreachable while synth_chart_brief reads discoveries via a different path | LOGIC+INFRA | HIGH | [probe-B] limit=3, 482012f1 | Align serving SQL to current bodha_discoveries columns; add per-tool smoke test per release | FIXED [verify-against: prod, R6 2026-07-10] |
| R-10 | **synth_tail_divergence_get DEAD — schema drift** — 500: `column "tier" does not exist`; this is the mandatory BA-P4 dissent instrument that judgment_query's drill_pointers direct callers to — the 10% dissent channel is unfulfillable | LOGIC+INFRA | HIGH | [probe-B] domain=career | Same fix class as R-9 | FIXED [verify-against: prod, R6 2026-07-10] |
| R-11 | **traverse_graph string-address DSL sliced to first character** — `about="lord_of(bhava 10)"` → `Could not parse address expression: "l"`; the R5 W2 documented gate example fails; object form works | LOGIC | HIGH | [probe-B] | Fix string-vs-array handling at the about/about_from/about_to normalization step | CLOSED_WITH_EVIDENCE [D-1.6 S-7, 2026-07-16: traverse_graph(about="lord_of(bhava 10)", depth=1) parses+resolves correctly (H10 from Aries lagna = Capricorn → Saturn → placed 7th Libra); 15 nodes/148 edges, is_error=false. Did-not-reproduce, matching CR-53's retest note. SIZE NOTE routed to Lane S-5: depth-1 response is 99KB (>64KB Gate Ś ceiling) — budget work, not a parse defect] |
| R-12 | **prashna_undertaking_get DEAD** — 500: `column gj.verdict does not exist` | LOGIC+INFRA | MED | [probe-K] | Align p1_synthesis query with current ga_prashna_judgment columns | FIXED [verify-against: prod, R6 2026-07-10] |
| R-13 | **holistic_bundle_chart_facts 5/8 sub-tools error** — MSR, CGM, LEL, PANCHANG, DASHA all fail; only UCN/RM/CDLM fire; no usable content | LOGIC+INFRA | MED | [probe-B] | Repair or retire the bundle; per-sub-tool smoke tests | OPEN |
| R-14 | **query_calibration masks broken SQL under "structural mode" empty** — ok:true/0 rows "expected in STRUCTURAL mode" while provenance leaks `db_note: column "id" does not exist LINE 3…`; sibling alias mimamsa_calibration_get 400s outright | LOGIC | MED | [probe-K] | Fix column list; make db errors fail loudly, never annotate-and-swallow | FIXED [verify-against: prod, R6 2026-07-10] |
| R-15 | **Remedy primitive family DOWN: `DATABASE_URL not set`** — query_mantras, query_tantric_remedies, query_remedies_by_planet, query_remedies_for_chart, list_remedies_by_category, read_remedy all dead with the same env error; their 6 ref_* aliases 500/400 in turn | INFRA | HIGH (trivial fix) | [probe-K] all six + aliases | Set DATABASE_URL in that tool bundle's runtime (separate service from remedial_codex_query, which runs) | OPEN |
| R-16 | **`ref_transit_rules_get` + `asset_registry_all/_l0` hard-fail 401** — `platform DB query failed: 401` / `GET /api/cockpit/registry → 401`; the known callPlatformPrimitive auth-header P0, still live in prod | INFRA | CRITICAL (known 1-line fix) | [probe-G][probe-K] | Ship the registered callPlatformPrimitive auth fix (MCP-elevation P0) | PARTIAL — R6 2026-07-10 prod probe: auth-header fix landed & the 401 IS gone for ref_transit_rules_get, but it now 400s "Rejected by whitelist: bg_transit_rules not in read-only whitelist" (ALLOWED_TABLES gap in platform/src/app/api/mcp/db/query/route.ts, never updated). asset_registry_all/_l0 STILL hard 401 — root cause is NOT the header fix at all: platform/src/proxy.ts middleware requires a Firebase session cookie for any /api/* path not in its isPublic allowlist, and /api/cockpit/registry is not on that list — the route itself has no auth check, so headers can never help. Two distinct new fixes needed. |

### New rows (v2) — parameter no-ops & mis-routing

| ID | Title | Gap | Sev | Evidence | Fix approach | Status |
|----|-------|-----|-----|----------|--------------|--------|
| R-17 | **ganita_structural_get facet routing broken** — facet=graha_yuddha and facet=parivartana both return the yoga/dosha category set (total=107); facet=aspects routes correctly — facet→category map has wrong entries | LOGIC | HIGH | [probe-G] chart A | Audit the facet→fact_category map for all 10 advertised facets; serve-time assertion returned-categories ⊆ facet's declared set | OPEN |
| R-18 | **Estate-wide silent parameter no-ops** — kala_windows_get + kala_yoga_activation_get ignore start/end/domain/limit (echo defaults); kala_projections/life_arc/mimamsa_lel_query ignore limit; list_assets + catalog_assets_list ignore layer+limit (92 assets always); catalog_assets_l0 ignores limit; bodha_remedies_get ignores limit+domain; bodha_remedies_search ignores keyword+limit (byte-identical to _get); get_projections ignores max_projections; bodha_graph_traverse ignores limit+max_depth | LOGIC/UX | HIGH | [probe-K][probe-B] | Single alias→primitive arg-mapping conformance sweep (snake_case start_date vs date_from mismatch suspected); reject-or-honor, never silently drop; add param-echo contract test per tool | OPEN |
| R-19 | **remedial_codex_query filters are no-ops → WRONG remedies** — planet=Saturn returns 20 JUPITER rows; keyword="sade sati" returns identical result_hash; top_k ignored; category="mantras" → 0 (vocab lives in remedy_type, category column null); OCR-garbage row served as a "mantra" (`sweep_jupiter_mantra_2ab17171`: "ttl \":(J~6q«g6Q(…") | LOGIC | HIGH | [probe-K] | Wire planet/keyword/category/top_k into SQL WHERE; map category→remedy_type; quarantine corpus_sweep garbage rows | OPEN |
| R-20 | **Three ref_* "catalog" tools are mislabeled vector-search stubs** — ref_dasha_systems_get, ref_dignity_reference_get, ref_nakshatra_get ignore ALL filters, substitute one generic query word, return OCR book-index pages (Brihat Samhita ELEPHANT index for a Saturn-dignity ask). ref_doshas_get/ref_yogas_get prove the intended structured shape exists | SURF+DOC | HIGH | [probe-G] | Back the three with their bg_* catalog tables (as doshas/yogas are), or honestly re-describe as corpus search | OPEN |
| R-21 | **Receipt integrity: ✓ with zero evidence** — judgment_query `varga_confirmed:"D10✓"` with `varga_confirmation.rows:[]`; `timing_anchored:true` with all timing_hooks empty; graha_portrait completeness "✓" for a section trimmed to rows:[] (count 59) | SURF+LOGIC | MED | [probe-B] both charts | A ✓ requires surviving evidence rows, else `checked_no_rows` / trim pointer | OPEN |
| R-22 | **pact_status "chain_complete" with a failed TRIGGER** — stages [promised,confirmed,active_now,unreachable] counted as stages_completed:4; combined with T-3 an expired-dasha, untested-transit chain presents as fully passed; envelope timing.as_of_date echoes today not the requested as_of | LOGIC | MED | [probe-B] | unreachable ≠ completed; pact_status vocabulary gains `chain_incomplete_infra`; echo the requested as_of | OPEN |
| R-23 | **EAV serve order buries canonical content** — positions serves aprakasha before grahas; strength serves composite classifications before shadbala; sade_sati serves 8 duration fragments first; karakas facet serves arudhas before Chara karakas — under limits (the only safe way to call) the head content is unreachable | UX | MED | [probe-G] | Deterministic serve order (grahas/core first) or a category param on every ganita_*_get | OPEN |
| R-24 | **grounding block ignores limit** — chart_facts(keyword=vargottama, limit=20) returned 20 facts + ~250 fact_ids/citations in grounding (~26KB of 30KB) | SURF | MED | [probe-G] | Compute grounding from served rows only (yogas v3 envelope already states this rule) | OPEN |
| R-25 | **Tajaka pagination incoherent — current varsha unreachable** — total flips 16→6 across offsets; offset applies to EAV hadda rows while varsha list restarts at year 1; only years 1–8 reachable for a 42-year-old native | SURF | MED | [probe-G] | Unify pagination across merged sources; add varsha_year filter | OPEN |
| R-26 | **ref_classical_citation_get leaks 768-dim embedding vectors** (~8KB/row) | SURF | LOW | [probe-G] | Strip embedding column from serve | OPEN |
| R-27 | **list_entities class-vocabulary mismatch** — entity_class=graha → 0 silently; store uses "planet" | UX | LOW | [probe-G] | Accept synonyms or return empty_reason listing valid classes | OPEN |
| R-28 | **ganita_positions_get `frame` promises `house_from_frame`, never delivers** — frame=chandra accepted, frame_note claims the field is added, no served row contains it (advertised R5 W2 feature) | SURF+DOC | MED | [probe-G] chart B | Deliver the field or correct the note | OPEN |
| R-29 | **vector_search payload double-encoded JSON-in-string** (+5-6s latency); content relevant | UX | LOW | [probe-B] | Return structured JSON | OPEN |

### New rows (R5.3 B4, 2026-07-10) — failures-to-register mapping, per CLAUDECODE_BRIEF_R5_3_CONTENT_DEPTH_v1_0.md §B4 deliverable. Failures NOT explained by an existing row.

| R-30 | **`judgment_query` v3 envelope carries no narration — same C1 root-cause class the R5.3 B2 entity lane fixed for `graha_portrait` (PR #511), never remediated here** — B4 live Gemini grade: `Q3-N-1` (career, native) 6/11, rationale "raw, truncated JSON tool output rather than a synthesized astrological communication." Regressed from a B1 MET (14/11) — see R5_3_RUN_LEDGER_v1_0.md's zero-regression note; most likely explanation is this item was always marginal/narration-less and B1's grading ran lenient, not a code regression (judgment_query was untouched by any R5.3 PR) | SURF | HIGH | [R5.3 B4, verify-against: prod 2026-07-10] `results_90a14176.json` Q3-N-1 | Apply the same narration-assembly pattern as PR #511 (registry_bridge.ts's `buildGrahaPortraitNarration`) to `judgment_query`'s v3 envelope | OPEN |
| R-31 | **`bodha_signals_get` Jaimini-paradigm response never surfaces the Amatyakaraka (AmK)** — B4 live Gemini grade: `Q3-A-2` (career/Jaimini, Abhinandan) 5/11, rationale "fails to identify the Amatyakaraka, completely missing." Regressed from a B1 MET (13/11), tool untouched by any R5.3 PR — likely a pre-existing marginal gap the B1 grader missed, not a new break | DATA+SURF | MED | [R5.3 B4, verify-against: prod 2026-07-10] `results_90a14176.json` Q3-A-2 | Wire chara-karaka (AmK etc.) computation/surfacing into the Jaimini-paradigm signal response | OPEN |
| R-32 | **`graha_portrait` narration (R5.3 B2 PR #511) gets cut off mid-sentence by the response-budget trimmer before completing** — live: `Q2-N-1`/`Q2-A-1` payloads carry the literal string "…[truncated for budget]" partway through `verdict.narration`, before shadbala/avasthas/yoga/dasha sections render. Root cause: PR #511 added narration + stripped `citation_ref` for headroom, but didn't trim enough of `content.*.rows` to also fit the FULL narration under the existing 12KB `graha_portrait` ceiling for grahas with dense per-varga data (Saturn/Jupiter). B2's own verifier confirmed this same-session (`R5_3_RUN_LEDGER_v1_0.md` B2 residuals) | SURF | HIGH | [R5.3 B2/B4, verify-against: prod 2026-07-10] `results_90a14176.json` Q2-N-1 (3/11), Q2-A-1 (8/11) | A second, tighter trim pass on `content.*.rows` (more boilerplate to cut) to buy back room for the narration to finish — not a narration rewrite | OPEN |
| R-33 | **`ganita_structural_get`'s PR #512 dosha_fires v3 fix is gated behind opt-in `response_format='v3'`, never triggers on the battery's own default-format args** — B4 live: `Q9-N-1` (Kala Sarpa verify, native) called with `facet=dosha_fires`, NO `response_format` param (matching the item's own spec), returns the legacy envelope (`verdict:null`, no Rahu/Ketu axis language) — the real fix from PR #512 exists but is dead code for this call shape. Related to R-17 (facet routing) but distinct — this is a default/opt-in wiring gap, not a routing bug | SURF | MED | [R5.3 B2/B4, verify-against: prod 2026-07-10] `results_90a14176.json` Q9-N-1 (2/12) | Either make `v3` the default response_format for `ganita_structural_get`, or have the item's expected call shape pass it explicitly — Pratinidhi-R / native call on which side should change | OPEN |
| R-34 | **`query_chart_facts` degree/house_12 fields missing on specific Abhinandan-chart facet queries — not yet root-caused, needs R6 triage** — B4 deterministic assertion failures: `Q1-A-1` (`about:"lagna"`, chart_id=1c826d5a) missing an explicit degree marker (`degree_23_32_present`); `Q1-A-2` (`about:{graha:"Venus"}`, same chart) missing an explicit `house_12` marker even though the position data is present per Q1-A-2's other passing assertions. Both are pre-existing (not touched by any R5.3 PR); no root cause diagnosed in this session | SURF | LOW-MED | [R5.3 B4, verify-against: prod 2026-07-10] `results_90a14176.json` Q1-A-1, Q1-A-2 | R6 triage: confirm whether the degree/house_12 values exist in `chart_facts` for 1c826d5a and are simply not surfaced, or genuinely absent | OPEN |
| R-35 | **`query_chart_facts(keyword='vargottama')` doesn't return an honest list-or-empty-reason shape** — B4: `Q1-N-5` fails `honest_result_or_list` (`has_list=false; empty_reason_markers=false`) despite Mercury's `is_vargottama=true` rollup existing per S-1's own note. Not touched by any R5.3 PR; not yet root-caused | SURF | LOW | [R5.3 B4, verify-against: prod 2026-07-10] `results_90a14176.json` Q1-N-5 | R6 triage: likely the same class as S-1 (vargottama rollup computed but not joined into this serving path) — confirm and fix together | OPEN |
| R-36 | **`bodha_signals_get` still carries a stale-marker-vs-rows contradiction post-R-4's fix** — R-4 (stale provenance-note literals) is marked FIXED against `chart_facts` freshness notes, but `X-8`'s live probe of `bodha_signals_get(domain=career)` still shows `known_stale_marker_present=true` alongside notes claiming freshness — R-4's fix did not cover this specific surface | SURF | LOW-MED | [R5.3 B4, verify-against: prod 2026-07-10] `results_90a14176.json` X-8 | Extend R-4's freshness-note re-derivation to `bodha_signals_get`'s note-building path specifically | OPEN |
| M-23 | **`ph_nimitta` writer + all 3 `engine.py` anchor-derivation paths crash on a `timestamptz`-sourced date** — `_enrich_discovery_row` (writer) and `derive_anchor_from_{convergence,bhavishya,discovery}` (engine) only coerced a raw `str` date to `date`, silently passing a raw `datetime.datetime` through untouched whenever the source column is `timestamptz` (e.g. `bodha_discoveries.detected_at`). `window_end` then stayed a `datetime`; the writer's own T-5 pre-birth gate (`window_end < birth_date`, a plain `date`) crashed with `TypeError: can't compare datetime.datetime to datetime.date` — cascading to fail all 18 downstream L4 Phala + L5 Mīmāṃsā assets in a single run. **Surfaced only on Abhinandan's (1c826d5a) live data path** — this exact writer had never previously run end-to-end against fully-fresh L1→L3 real production data in one pass (prior verification was pytest/offline-only, per this session's concurrent-write-race ban); the specific row shape that triggers the bug (a `timestamptz` `detected_at` reaching this code path) apparently never occurred in any prior partial rebuild or test fixture. Twin lesson to R4's native-path (482012f1) HALTs: a fix can look clean on one chart's data path and still hide a live crash on another's — cross-chart data-path exposure is its own verification axis, not covered by same-chart re-testing alone | LOGIC | CRITICAL | [R6, live guardian-monitored Abhinandan canary rebuild, 2026-07-11] Cloud Run job logs, `build_runs` run `774532f3`, `TypeError: can't compare datetime.datetime to datetime.date` | Route through the writer's own already-correct `_parse_iso_date` helper (datetime/date/str uniform handling); added an equivalent `_coerce_date` helper in `engine.py` and replaced all 3 duplicated, identically-broken inline blocks — closes the whole bug class, not just the one path that crashed first | FIXED [verify-against: prod, R6 2026-07-11, PR #540 `3e265785`] |

### New rows (v2.2) — CGM chain-detection integrity (from the Mars+Rahu+Mercury→11H forensic trace, 2026-07-10)

Context: native flagged a known-true deep chain — Mercury(10H) —dispositor→ Saturn(11L, exalted 7H)
←conjunct— Mars(in Rahu's nakshatra Swati) —8th-aspect→ Rahu(2H dhana, exalted) — the chart's
financial-fluidity circuit. L1 grounds every atom of it; the portal never surfaces it. Forensic
trace pinpointed where it dies.

| ID | Title | Gap | Sev | Evidence | Fix approach | Status |
|----|-------|-----|-----|----------|--------------|--------|
| G-1 | **CGM has NO graha→bhava edge classes — bhava nodes are edge-orphans** — edge-type census: {aspect 72, argala 24, dispositor 8, yoga_domain 5, dosha_domain 3}; no `lordship`, no `occupancy`. Saturn (11L) cannot reach his own bhava-11 node (`path_found:false`, any direction, any depth); bhava-11 node `91bd12b4` has 0 edges. EVERY "graha X feeds house Y" chain fails chart-wide — this defeats the CGM's core promise (multi-hop chain detection across house semantics). Graha↔graha edges ARE present and correct (Mercury→Saturn dispositor, Mars→Saturn + Mars→Rahu aspects verified live) | DATA/PERSIST | CRITICAL | [chain-trace 2026-07-10] paths Saturn→bhava11 false while dispositor edge 24ddbd8d exists | Extend the CGM edge writer to project graha→bhava `lordship` + `occupancy` (and optionally graha→bhava-aspect) edges from existing L1 facts — the data is all there, only the projection is missing | OPEN |
| G-2 | **Degenerate edge annotations kill domain routing** — 72/72 aspect edges carry identical strength 0.575 AND identical `affected_domains:["character","career"]`; all 8 dispositor edges 0.6 with domains []; "wealth" appears on exactly 1 of 112 edges in the hub subgraph. Even the intact graha-level chain can never be routed to a wealth query. (Same failure class as D-18 flat pagerank — flat weights in, flat rank out) | DATA+LOGIC | HIGH | [chain-trace] edge census across 75KB subgraph pull | Real per-edge strengths (drik/orb-based, from L1 virupa rows — they exist per S-4); derive affected_domains from target-node bhava/karaka domain map, never constants; degenerate-distribution gate on edge columns | OPEN |
| G-3 | **Graph address resolver rejects its own documented `bhava` key** — `{type:"bhava",bhava:11}` → "House number must be an integer 1..12, got undefined"; only undocumented `house` key works; `{graha:"Mars"}` without `type` → "Unknown address expression type". Sibling of R-11 (string DSL sliced to first char) | UX/LOGIC | MED | [chain-trace] traversal attempts table | Accept both keys; error messages name the expected schema | OPEN |
| G-4 | **neighbors-mode with `about` silently falls back to convergence mode** — seeded-BFS request discarded; returns the flat top-10 pagerank payload (75,100 bytes, byte-identical with/without min_strength); depth/min_strength ignored, no about_resolution echoed. An investigator cannot probe a specific node without insider workarounds | LOGIC | HIGH | [chain-trace] neighbors probe | Honor about/depth/min_strength or fail loudly; never silent mode-switch | OPEN |
| G-5 | **judgment_query is laterally blind on bhava queries** — bhava=11 wealth ask assembles the vertical view correctly (11L Saturn exalted 7H, verdict convergent_strong, dasha timing) but `aspecting_grahas:[]`, `karaka_condition:[]`, `yogas_checked:0`, `bhanga_checked:false`; the wealth shastra map keys karakas to bhava 2/Jupiter only, so an 11H-gains chain has no domain route. Mars/Rahu/Mercury appear nowhere in its evidence | SURF+LOGIC | HIGH | [chain-trace] judgment_query(bhava=11) | Extend shastra domain map (wealth ⊇ bhavas 2+11, karakas Jupiter+Mercury+Rahu-for-unconventional); once G-1 lands, join the CGM chain walk into the judgment evidence block | OPEN |
| G-6 | **MSR has no composite multi-graha chain signal class** — 2,077 wealth signals but the top-10 is a flat wall of generic yoga_label rows (identical salience 0.575, identical composite 1.0465, 8/10 citing the single fact e2b47b2c6d457725 = Y-11's degenerate grounding); no signal type expresses "graha-web → bhava outcome" | DATA | MED-HIGH | [chain-trace] bodha_signals_get(domain=wealth) | New MSR signal class emitted from CGM multi-hop paths (chain signals with constituent edge list) once G-1/G-2 make chains traversable + rankable | OPEN |
| G-7 | **chart_dashas `lord_natal_house_d1` contradicts chart_facts** — Saturn dasha row asserts natal house 11; chart_facts says house_d1=7 (L1-authority violation, §N.5; sibling of D-1's wrong lord_natal_nakshatra — the dasha writer's denormalized lord-columns are systematically unreliable) | DATA | HIGH | [chain-trace] judgment_query dasha row vs fact 74f1a7b3477f5e05 | Same fix as D-1: re-derive ALL denormalized lord_* columns from chart_facts at build + verifier cross-check | FIXED [verify-against: prod, R6 2026-07-10] |
| G-8 | **L1 karaka_web/lord_aspects omit node aspects in D1** — no D1 Mars→Rahu 8th-aspect fact row (category excludes nodes by design in D1 while D9 rows exist for Saturn/Sun/Jupiter→Rahu); the L2 graph derived the edge independently — an L1/L2 derivation asymmetry that violates the cite-don't-recompute discipline | DATA | MED | [chain-trace] fact-base inventory | Emit graha→node aspect rows in D1 karaka_web consistently with per-varga siblings; L2 edge cites the L1 fact_id | OPEN |

### New rows (v2.3) — KP subsystem integrity (from the KP 11th-cusp cash-flow forensic trace, 2026-07-10)

Context: native recalled the legacy portal's STRONGEST wealth signal — KP: Mars+Mercury+Rahu on the
11th cusp = cash-flow channel, Saturn (dual 10/11 lord) = earning channel. Verified in the archive:
FORENSIC v6.0 §4 has it verbatim (KP.CUSP.11 = Star Mars / Sub Mercury / Sub-Sub Rahu; KP.SIG.11 =
Sun, Rahu, Moon, Saturn; DEEP_ANALYSIS v1 line 1866/1907 tied it to the running Mercury MD/Saturn AD).
The current estate contains every atom (cusp_kp_lords CUSP_11 star=Mars sub=Mercury f88bc72a/3a4a7aa9;
Mars in Rahu's star 8e25001f; Mercury↔Rahu mutual sub-lordship 3f74a0d9/f0a8e88f; Rahu significator
of 11 from 2H; Saturn dual 10/11 lord + 10th sub-sub) — but no code composes it, the composed
category that exists is a self-admitted fake, and no wealth instrument reads KP at all.

| ID | Title | Gap | Sev | Evidence | Fix approach | Status |
|----|-------|-----|-----|----------|--------------|--------|
| KP-1 | **KP cusps computed on whole-sign boundaries, not Placidus** — `cusp_kp_lords` derives H2–H12 from `((asc_sign0+h)%12)*30.0` (comment admits it); KP mandates Placidus; legacy v6.0 WAS Placidus (11th cusp 301.13° vs current 300.0° — Mars/Mercury survived by luck, sub-sub flipped Rahu→Mercury). No Placidus computation exists anywhere in the current sidecar for KP | LOGIC | HIGH | [kp-trace 2026-07-10] ga_nakshatra_emitters.py:151-155 vs FORENSIC v6.0 §4.1 | Compute Placidus cusps (pyswisseph, already a dependency) and feed the existing `compute_kp_lords` (verified correct at all 4 levels) | OPEN |
| KP-2 | **`kp_cuspal_significators` is a self-admitted fabricated simplification** — `sub_lord := star_lord` ("Approximation", ga_sensitive_writer.py:1573) + significators = [star_lord, sign_lord] only, on equal-house cusps. It CONTRADICTS the authoritative cusp_kp_lords on the same subjects (C11 sub-lord "Rahu" 4307d55f vs true "Mercury" 3a4a7aa9). Two disagreeing "KP sub_lord" ledgers = authority split (§N.5 spirit); B.10-adjacent | LOGIC+DATA | CRITICAL | [kp-trace] ga_sensitive_writer.py:1553-1577 + both fact rows quoted | Retire the category or rebuild it from the true ladder; never two sources for the same KP quantity | OPEN |
| KP-3 | **The 4-level KP house-significator ladder is never computed** — occupant-star planets > occupants > lord-star planets > lord, + node agency (Rahu/Ketu delivering for star-lord/dispositor/conjunctions). Legacy KP.SIG.* had it; it is FULLY derivable from stored graha_kp_lords + graha_position facts (the trace derived 11H = Sun, Rahu, Moon, Saturn matching legacy exactly) — no writer stores it | DATA | CRITICAL | [kp-trace] §2 derivation + FORENSIC v6.0 §4.3 | New category `kp_house_significators` (L1 or L2) implementing the ladder + node agency, each row citing constituent graha_kp_lords/graha_position fact_ids | OPEN |
| KP-4 | **KP signals carry wrong domain tags** — bo_laksana `_DOMAIN_MAP` maps only `kp_cuspal_significators`→wealth; `graha_kp_lords` + `cusp_kp_lords` fall to the nakshatra default ["character","relationship"] — so Mars-in-Rahu's-star can NEVER surface in a wealth query; 81 kp signals exist as atomic restatements ranked 4,584-14,199 with cusp-longitude noise rows in the top | LOGIC | HIGH | [kp-trace] bo_laksana.py:313-381 | Add both categories to _DOMAIN_MAP with house-aware domain tags; suppress raw cusp-longitude rows from signal ranking | REMEDIATED-PENDING-W4 [WP-1.2 / W1; KP cuspal significators inherit house domain (2nd/11th→wealth) + serving salience demotion of cusp-longitude noise; deployed amjis-web 2385fb62 + amjis-mcp fc84cd0d (== main HEAD), blind-verified + 7/7 prod-verified on deployed channel 2026-07-13] **CLOSED_WITH_EVIDENCE (domain-tag core)** + **RESIDUAL ROUTE_TO_LANE S-5** [D-1.6 S-7, 2026-07-16: bodha_signals_get(paradigm=kp, domain=wealth) → 19 kp rows reachable in the wealth slice (the original "Mars-in-Rahu's-star can NEVER surface in wealth" defect is dead); composite ranking tops with CUSP_11 sub_lord=Mercury (correct). RESIDUAL: raw cusp_longitude_sidereal noise rows still served at ranks 2-4 of the wealth slice — the WP-1.2 "cusp-longitude noise demotion" is not effective on the live composite path; also all 19 rows carry valence_source=keyword_heuristic_v1 (evidence input for Lane S-5's PARK-#4 scoping — the residual population is larger than the 5 "non-node" rows assertion #4 counts)] |
| KP-5 | **No serving instrument performs KP analysis** — judgment_query/apex_wealth are Parashari-only (0 kp references in register_d9_judgment.ts or the shastra map); the KP paradigm exists in signals only as one-row restatements. The legacy portal's headline capability (cuspal sub-lord verdict + significator table + dasha-lord convergence, cf. DEEP_ANALYSIS line 1866: "KP promise of 10H matters is DUE" under Mer MD/Sat AD) has no current equivalent | SURF | HIGH | [kp-trace] grep evidence | KP lens in judgment_query once KP-1..3 land: cusp sub-lord verdict + significator table + dasha convergence, composed from cited fact_ids | OPEN |
| KP-6 | **Pivoted chart_facts silently merges CUSP_10/11/12 across the two KP categories** — subject-padding inconsistency (`CUSP_01` padded, `CUSP_10+` not; category C unpadded) makes the pivot mask the authoritative star_lord (showed Rahu from the fake category over Mars from cusp_kp_lords). Sibling of the R-23/R-24 serving-shape family | SURF+DATA | MED | [kp-trace] observed pivot collision | Normalize subject naming across categories; pivot must never merge rows from different fact_categories under one subject | OPEN |

### New rows (v2.4) — live-consumption findings from Cowork discussion session (Abhinandan 1c826d5a, 2026-07-11; pre-rebuild elevation audit input)

Context: native-driven discussion session (business nature, personality, wealth magnitude) consuming the public MCP channel end-to-end, plus a first-ever live test of the `bo_anveshana` discovery asset (bodha_discoveries). Discovery asset RUNS (1,138 rows served) but output quality fails §J; several receipt/payload and cross-table contradictions surfaced.

| ID | Title | Gap | Sev | Evidence | Fix approach | Status |
|----|-------|-----|-----|----------|--------------|--------|
| R-37 | **`bodha_discoveries_get` top-of-ranking is degenerate** — 12 of top 15 rows are the SAME single 5.1σ ga_sensitive anomaly re-emitted once per descriptive fact_key (yoni_sex, symbol, varna, guna, presiding_deity, nakshatra_lord, nakshatra_id_ref, akshara, pada_lord, star_lord, sub_sub_lord, lord_chain…) with no family collapsing; descriptive nakshatra metadata treated as predictive "patterns"; composite_discovery_rank uniform 1.2; non_obviousness=consequence=confidence saturated at 1.0 everywhere; negative σ outliers (−5.9σ = unusually LOW-salience sade-sati rows) surfaced as the chart's TOP discoveries; hypothesis_text is template boilerplate. Asset is mechanically live but epistemically not a discovery surface | DATA+LOGIC | HIGH | [cowork 2026-07-11] bodha_discoveries_get(1c826d5a, limit=30) live | Family-collapse duplicates (same E-6 pattern as get_chart_orientation); exclude descriptive-metadata fact_keys from anomaly candidacy; sign-aware σ handling; de-saturate scores; require corroboration_count>1 or cross_subsystem_root for top ranks | OPEN |
| R-38 | **`judgment_query` receipt claims varga confirmed while serving zero varga rows** — receipt says `varga_confirmed:"D10✓"` (career) and `"D2✓"` (wealth) but `checklist.varga_confirmation.rows=[]` in both calls — the completeness receipt asserts a check the payload shows was not performed | SURF | MED-HIGH | [cowork 2026-07-11] judgment_query career+wealth, 1c826d5a | Receipt value must derive from rows actually fetched (✓ only when rows>0; else "attempted-empty") | REMEDIATED-PENDING-W4 [WP-1.5 / W1; program-wide honest envelope contract — receipts derive from rows actually fetched (trim-lies structurally impossible); deployed 2385fb62/fc84cd0d, 7/7 prod-verified 2026-07-13] |
| R-39 | **`judgment_query` timing_hooks entirely empty despite populated chart_dashas** — `timing_hooks.current=[]`, `lord_mahadasha_windows=[]`, `karaka_mahadasha_windows=[]` on both career and wealth calls while get_dashas serves the full verified Vimshottari chain for the same chart; receipt still asserts `timing_anchored:true` | SURF | HIGH | [cowork 2026-07-11] judgment_query vs get_dashas, same session | Wire timing_hooks to chart_dashas (current + lord/karaka MD windows); receipt honesty same fix as R-38 | OPEN |
| R-40 | **`assess_wealth` un-budgeted 181KB response + empty analysis stages** — response blows any client budget (same class C1/A2 fixed for judgment_query/graha_portrait/phala_outlook, never applied to the apex assess_* family); within it: `activating_dasha.activations=0` over a 2026–2029 window that contains the Saturn→Jupiter AD transition; `varga_analysis` is a stub note; `verdict_skeleton.by_stage` karaka/lord/strength/varga/temporal all `[]` — the reconciliation stages advertised by the tool are empty shells; top-10 composite is a flat wall of nabhasa yoga_labels (Y-11/G-6 class) | SURF+DATA | HIGH | [cowork 2026-07-11] assess_wealth(1c826d5a), 181,062 chars saved to session file | Apply budget/trim + narration pattern to assess_* family; root-cause empty temporal/karaka/lord stages (likely same wiring gap as R-39) | OPEN |
| R-41 | **`ganita_yogas_get` v3 envelope contradicts its own content** — verdict says `yogas_fired:0, doshas_fired:0` + judgment_flag `zero_rows_returned` while `content.rows` in the SAME response serves 32 rows (8 yoga_label + 22 dosha_label + 2 flags); pancha_mahapurusha narrative admits "position was not available in this response" — envelope counters read a different source than the served page | SURF | MED-HIGH | [cowork 2026-07-11] ganita_yogas_get(1c826d5a, v3) | v3 verdict counters must count the served rows; PM narrative should join graha positions it already has access to | REMEDIATED-PENDING-W4 [WP-1.5 / W1; envelope counters count the served rows (canonical envelope.ts); deployed 2385fb62/fc84cd0d, 7/7 prod-verified 2026-07-13] |
| R-42 | **Yoga/dosha constituent grounding degenerate on chart 1c826d5a** — ALL 22 dosha_label rows cite the identical single constituent fact `2ddd8464544d8c35` and ALL 8 yoga_label rows cite `65cba769ae730e49` (sibling of Y-11's e2b47b2c on chart A — confirms the defect is systemic, not chart-specific); additionally the mutually-exclusive nabhasa sankhya family (Gola=1 sign, Yuga=2, Shoola=3, Kedara=4, Pasha=5) ALL fired simultaneously with identical fire_reason `5_distinct_signs` — only Pasha can be true for a 5-sign distribution; classifier emits the whole family instead of the one applicable member | DATA+LOGIC | HIGH | [cowork 2026-07-11] ganita_yogas_get rows, 1c826d5a | Fix constituent_facts wiring to cite the actual participating graha/bhava facts; sankhya classifier must select the single member matching the sign count | OPEN |
| R-43 | **chart_dashas dignity column wrong again (D-1/G-7 family, third instance)** — every Saturn row carries `lord_natal_dignity_d1:"own"` for Saturn in SCORPIO (Mars-ruled; judgment_query says "neutral" for the same graha) — the denormalized lord_* columns remain unreliable post-D-1/G-7 fixes; also `lord_natal_shadbala_total:null` on every row (field never populated) | DATA | HIGH | [cowork 2026-07-11] get_dashas(1c826d5a) vs judgment_query bhavesha_condition | Extend the D-1/G-7 re-derivation fix to dignity + shadbala columns; add verifier cross-check dignity==chart_facts dignity | REMEDIATED-PENDING-W4 [WP-1.8 / W1; serving-side D1 dignity+shadbala re-derivation grounded to chart_facts (Saturn-Scorpio "own"→neutral corrected, shadbala keyed to display-name); deployed 2385fb62/fc84cd0d, 7/7 prod-verified 2026-07-13] |
| R-45 | **L3 Kāla temporal-activation engine serves ZERO rows — the temporal×structural convergence asset (the native's "activation points" instrument) is inert on chart 1c826d5a** — `get_temporal_windows(2026-07-01→2027-12-31, include_convergence=true)` returns `activations:[], activation_count:0, predicates:[], predicate_count:0` over an 18-month window containing the Saturn–Rahu→Saturn–Jupiter AD transition; tables `kala_activation`/`kala_activation_predicates` appear empty or unqueried for this chart. This is the likely SINGLE ROOT CAUSE behind R-39 (judgment_query timing_hooks empty) and R-40's activating_dasha=0 — three independent consumers starving on the same upstream. **FORK RESOLVED (Brief Foundry observation, 2026-07-12): `kala_activation` is NOT empty — 66,836 rows (482012f1) / 66,747 rows (1c826d5a), matching MSR signal counts — so the ka_* writer ran; suspicion moves to the SERVING-PATH QUERY in `get_temporal_windows` (and its consumers). Item-0 re-test confirms + root-causes the query.** | DATA→SURF | CRITICAL | [cowork 2026-07-11] get_temporal_windows live, 1c826d5a; [foundry 2026-07-12] DB row counts both charts | **ITEM-0 RESOLVED (2026-07-12, DATA_PLANE_WRITER_DEFECT — re-attributed from SURF/serving-path to L3 writer; see `00_ARCHITECTURE/llm_consumption_audit/state/LANE0.md`):** serving query is CORRECT (`normalizeAyanamsha(undefined)→'lahiri_chitrapaksha'` matches stored keys; date filter valid; ayanamsha- and window-mismatch hypotheses falsified). Root cause = the L3 Kāla activation writer emits ~99% of `kala_activation` rows with **NULL `activation_start`/`activation_end`** (and no fallback dates in `activation_predicted_dates_jsonb`), so the correct date-window filter (correctly) excludes them. Native chart 482012f1 on default `lahiri_chitrapaksha`: **0 / 13,364 dated → served 0** (R-45 reproduces here); Abhinandan 1c826d5a lahiri: 84 dated → served 64 (does NOT reproduce on R-45's original chart today). **Defect SURVIVES rebuild** (the 66,747/66,836-row rebuild left ~99% NULL). R-39/R-40 shared-root-cause CONFIRMED (undated activations ⇒ empty timing_hooks / activating_dasha windows). Fix locus = writer date-population logic (not the serving query); a naive re-run will NOT fix it. Primary class 4 EMPTY SHELL (data plane) / secondary class 1 UNREACHABLE. | OPEN (re-attributed DATA→writer) |
| R-46 | **Varga evidence never actually enters verdicts — D9/D10/other vargas structurally subordinate to D1** — judgment_query's deterministic composite weights ONLY D1 dignity/occupants/aspects/from-Moon; the sole varga contribution is `varga_confirmation`, which serves zero rows (R-38); no serving instrument re-weights a verdict on D9 vargottama/D10 dasamsa-lord condition; native observation confirmed: readings over-index D1 while D9/D10/D2/D6 carry decisive classical weight (Parashara: D9 = fruit of the promise) | LOGIC+SURF | HIGH | [cowork 2026-07-11] judgment_query career+wealth composite formula + empty varga rows | Add varga terms to the deterministic verdict formula (operative-varga dignity of bhāveśa/kāraka at minimum); fix R-38 first so rows exist to weigh | REMEDIATED-PENDING-W4 [WP-1.8 / W1; varga terms added to the deterministic verdict formula, BPHS-grounded (native marriage mixed→contested; Venus 7th-lord/kāraka debilitated D9), R-38 varga rows now exist post-WP-1.5; deployed 2385fb62/fc84cd0d, 7/7 prod-verified 2026-07-13] |
| R-47 | **Mrityu-bhaga and sensitive-degree concepts labeled but never computed per graha** — chart_facts for 1c826d5a contains ONLY a catalog `dosha_label` row (citing the degenerate constituent fact, R-42) and a panchanga panchaka classification; no per-graha mrityu-bhaga degree check exists (which grahas sit on MB degrees for their signs), and no serving instrument can therefore ever surface it; same class likely applies to pushkara-bhaga/pushkara-navamsha and per-graha gandanta proximity | DATA | MED-HIGH | [cowork 2026-07-11] ganita_chart_facts_get(keyword=mrityu): 2 rows, neither per-graha | New L1 category `sensitive_degree_check` (graha × {mrityu_bhaga, pushkara_bhaga, gandanta_proximity} with degree evidence); wire into dosha firing + judgment aspecting-graha condition | CLOSED_WITH_EVIDENCE [D-1.6 S-7, 2026-07-16: ganita_sensitive_degrees_get → total_matching=55 rows for 482012f1: per-graha mrityu-bhaga/gandanta/pushkara/kartari/22nd-drekkana class with degree+orb evidence (JUP papa_kartari fired with flanking grahas listed). "Labeled but never computed per graha" defect is dead; CR-31's shipment confirmed live] |
| R-48 | **No large-N synthesis capability — the product cannot reason over high-volume multi-factor evidence** (native observation, 2026-07-11; C-6 is the measured 2-call instance of the same ceiling) — questions whose answer depends on synthesizing hundreds of interacting signals (e.g. "magnitude of wealth", whole-chart contradictions, multi-varga convergence) are served either as budget-trimmed flat top-K lists (rank walls of identical scores) or as un-budgeted dumps (R-40); no instrument performs staged/incremental retrieval-with-aggregation, no map-reduce over signal families, no synthesis narrative built from >~20 signals; the L2 pre-computation (convergence tables, CDLM, CGM) exists precisely to answer this but no serving path composes it into a deep-reasoning answer | ARCH | HIGH | [cowork 2026-07-11] session-wide; assess_wealth verdict_skeleton flat wall; C-6 | R6 architecture item: a synthesis instrument that (a) consumes pre-aggregated L2 surfaces (convergence, CDLM, CGM paths, family composites) instead of atomic signals, (b) supports staged drill with running-state, (c) emits a narrative with a derivation ledger — native to rule on whether this is an in-product orchestrating-LLM step or a client-side (Claude) protocol | **RE-DISPOSITIONED [D-1.6 Lane S-8, 2026-07-16 — was falsely REMEDIATED-PENDING-W4].** S-7 Binder probe (`BIND_D-1.6.md`) found the deployed connector's live `tools/list` (165KB, grepped) contains NO `synthesis`/`compose_large_n` tool face (only `synth_chart_brief_get`/`synth_tail_divergence_get`, a different capability) — the register's "deployed + 7/7 prod-verified" claim does not hold on the connector's actual served surface. **Root cause confirmed by read-only code audit this session:** `platform/src/lib/retrieval/synthesis/{capability.ts,index.ts}` DOES implement + register a `CapabilityDescriptor` (`uri: marsys://tool/synthesis/compose_large_n`, name `compose_large_n`) into the internal unified retrieval catalog (`registry/catalog.ts:79` imports `../synthesis/index`) — the instrument code (`instrument.ts`, `intent.ts`, `surface_gateway.ts`) exists and is unit/integration-tested (`instrument.integration.test.ts`). But **MCP tool exposure in this codebase is hand-wired per file** (`platform-mcp/src/tools/register_p1_*.ts`, e.g. `register_p1_synthesis.ts` for the synth_* tools) — NOT a dynamic iteration over the unified catalog — and no `register_p1_*.ts` file calls into `synthesis/capability.ts` or references `compose_large_n`. **Verdict: STILL PENDING, not closable.** The capability is real, tested, internal-only code; it was never wired into an MCP tool-registration file, so it cannot be the "prod-verified 2026-07-13" deployed capability the prior status claimed. Concrete remaining gap: author `platform-mcp/src/tools/register_p1_synthesis.ts` (or a new register file) exposing `synthComposeLargeNCapability` as a live MCP tool. Per DR-5 (C-6 product-boundary ruling, `BIND_D-1.6.md`): building an in-product orchestrating-LLM step is REJECTED as a campaign deliverable (PARK-class, product-architecture change) — this specific wiring gap (exposing an ALREADY-BUILT capability) is narrower than DR-5's rejected scope and is NOT excluded by it, but is explicitly OUT OF SCOPE for D-1.6 Lane S-8 (docs/data only, no code). **EXCLUDED-to-D-2 with this pointer** (D-2 is the next code-touching wave in the campaign sequence per CONDUCTOR_PROTOCOL.md; the Binder for that wave should re-probe before assuming this is D-2 scope-native — flag for D-2's Binder pass, not silently absorbed) |
| R-44 | **Orientation/domain-reading surfacing gaps** — (a) get_chart_orientation entity attribution degenerate: 298 of 300 top candidates aggregate under `UNATTRIBUTED` (Venus/Jupiter get 1 signal each); (b) nakshatra descriptive trivia (akshara="Cha", symbol="Fish/drum", yoni_sex) occupy the top-signals slots at signature_tier "major"; (c) get_domain_reading returns ranked signal IDs + salience with NO headline text — narrative construction requires N drill calls; (d) domain=character returns education/siblings lenses (DOMAIN_TO_QUESTION_TYPES over-broad); (e) contradiction_count=0 across all 13,369 signals and bodha_contradictions has 0 rows — contradiction engine likely inert on this chart | SURF+DATA | MED-HIGH | [cowork 2026-07-11] get_chart_orientation + get_domain_reading(character), 1c826d5a | Fix entity attribution in the aggregation pipeline; demote descriptive fact_keys from top-signal candidacy (same root as R-37); include headline_text in domain-reading refs; tighten lens map; verify bo_samvada (contradiction writer) actually ran | REMEDIATED-PENDING-W4 (serving-half) [WP-1.2(α+β) / W1; attribution ledger (0% UNATTRIBUTED served, §N.5 fact_ids resolve), descriptive-trivia salience demotion, domain discrimination (wealth∩relationship top-20 ≤25%), domain-reading headline text hydrated; deployed 2385fb62/fc84cd0d, 7/7 prod-verified 2026-07-13. Residual (e) contradiction-engine inert = bo_samvada writer defect → W2] |

## SECTION 5 — DATA CORRECTNESS (new in v2 — defects invisible to per-row checks)

| ID | Title | Gap | Sev | Evidence | Fix approach | Status |
|----|-------|-----|-----|----------|--------------|--------|
| D-1 | **chart_dashas denormalized `lord_natal_nakshatra` WRONG** — Mercury MD row says "Shravana"; Mercury at 270.84° = Uttara Ashadha pada 2 (PyJHora + chart_facts agree); Shravana is the Sun's nakshatra — join/copy slip in the dasha writer's denormalization | DATA | HIGH | [probe-G] ganita_dashas_get, chart A | Re-derive denormalized lord columns from chart_facts at build; verifier cross-check `lord_natal_nakshatra == graha_position.nakshatra(lord)` | FIXED [verify-against: prod, R6 2026-07-10] |
| D-2 | **Sade Sati table: duplicate + pre-birth cycles** — CYCLE_1 & CYCLE_2 share end 1968-06-17 (16y before the 1984 birth); CYCLE_3/4 and 6/7 pairwise identical | DATA | MED | [probe-G] | Audit ga_sade_sati cycle enumeration; uniqueness constraint (chart, cycle_no, period_type); clip to lifetime | FIXED [verify-against: prod, R6 2026-07-10] |
| D-3 | **`graha_composite_state_classification` astrologically suspect** — Jupiter "debilitation_cancelled" while in OWN-SIGN Sagittarius D1 (9°47' Mula); Saturn at 22° Libra (deep exaltation) "neutral"; 8 of 9 grahas "neutral" (near-degenerate). This is the same column Y-3/Y-6 should consume — it must be fixed BEFORE being wired in | DATA+LOGIC | HIGH | [probe-G] chart A | Re-derive classification vs dignity facts; distribution check; then wire into Y-6 | OPEN |
| D-4 | **Tithi-shunya / nakshatra-shunya (dagdha rashis): coded, ZERO rows live** — `_emit_tithi_shoonya` (ga_panchanga_writer.py:636-666) silently skips when `pi.shoonya is None`; live chart has 0 rows in both categories despite Shukla Tritiya having defined shunya rashis — classic silent-skip | DATA | MED-HIGH | [concept] code+live | Populate `shoonya` in panchang_engine or halt-warn on None; backfill on regen | OPEN |
| D-5 | **Digest entity attribution collapse — 299/300 signals "UNATTRIBUTED"** — both charts; per-graha entity profiles effectively empty though graha exists in configuration_jsonb of many rows (e.g. MOON on yoga labels) | DATA | MED | [probe-B] | Fix the attribution extractor to read configuration_jsonb.graha | CLOSED_WITH_EVIDENCE [D-1.6 S-7, 2026-07-16: bodha_chart_digest_get(summary) attribution block: served_unattributed_entities=0, served_unattributed_share=0, candidate_pool 300 with 0 unattributed (WP-1.2β). BONUS pre-evidence for Lane S-1 (not a D-5 finding): digest weakest_graha="Venus" with source "shadbala_total_min (BPHS Ch.27; CR-55 fix)" — CR-55 appears already fixed live; Lane S-1 to verify-then-close rather than re-implement, keeping the regression assertion] |
| D-6 | **bo_upaya remedy ranking degenerate** — all 9 grahas labeled "weakness"; resonance spread only 0.448–0.479; contradiction/domain/motif burden = 0 for every graha — no chart-specific discrimination | DATA+LOGIC | MED-HIGH | [probe-B][probe-K] | Investigate near-constant weakness_score; distribution-collapse gate on bo_upaya | OPEN |
| D-7 | **mimamsa_insight verdicts degenerate** — all career verdict_objects identical (grade 7.168, same 5 fact_ids, same contradiction); classical_sources arrays all empty | DATA | MED | [probe-K] | Event-class differentiation in mi_darshana; populate classical_sources | OPEN |
| D-8 | **Effective-dignity score map lossy + two inconsistent benefic sets in one writer** — dignity_scores lacks own/moolatrikona/friend/enemy keys → silent 0.5; benefics set at ga_structural:2701 excludes Moon while BENEFICS at :4459 includes it | LOGIC | MED | [code] | Single module-level classification constants; complete the score map on the `dignity_of()` vocabulary | OPEN |
| D-9 | **MC approximated as Lagna+270°** — ga_sensitive_writer.py:1431; true MC diverges by degrees at Bhubaneswar latitude; 9 MC-graha midpoints inherit the error. Non-canonical computable substitute (violates canonical-or-floor) | DATA | LOW | [code] | Real MC from ephemeris output, or floor | OPEN |
| D-10 | **bhava_arudha longitudes are sign-start fakes** — `longitude_sidereal = arudha_idx*30.0`; near_sign_boundary computed on it | DATA | LOW | [code] ga_sensitive_writer.py:1380 | Store sign-only or document sign-cusp convention | OPEN |
| D-11 | **PyJHora sidecar emits speed_dps=0 + non-retrograde nodes** — all graha_sthana rows; Rahu/Ketu is_retrograde:false | DATA | LOW | [probe-G] | Populate speed from engine or null the fields | OPEN |
| D-12 | **synth_chart_brief internal contradictions** — "Outcome: denied (grade 5.0/10). Conditional" (denied≠conditional, 5.0 mid-scale) with n_support=0; "signal is redundant … removing would materially alter"; five career lenses all exactly 7.2 with identical n_support=5 | LOGIC | MED | [probe-B] | Verdict-vocabulary mapping + template pass before native-facing | OPEN |
| D-13 | **judgment_query serves requires_pass rows as "bearing_yogas" with dirty labels** — `value_text="Kemidruma\nyoga"` (OCR typo + embedded newline) presented benefic without the JL-004 caveat graha_portrait carries | DATA+SURF | MED | [probe-B] | Clean OCR labels; carry requires_pass caveat at point of use (interim until Y-1/Y-2 land) | FIXED [verify-against: prod, R6 2026-07-10] |
| D-14 | **grounding_score=0 on chart B with full citations present** (=1 on chart A for identical query shape) | DATA | LOW | [probe-G] | Trace grounding_score derivation per chart | OPEN |
| D-15 | **Judgment "denied" block contradicted by lived ground truth** — synth_chart_brief marks childbirth DENIED (5.0/10) for a native whose twins were born 2022-01-03; same block denies foreign_settlement (native lived in the US 2019-23) and relocation. The denied-verdict computation is factually wrong on ≥3 of 8 event classes | LOGIC | HIGH | [accuracy-test 2026-07-10] DISCOVERY_ENGINE_ACCURACY_TEST_v1_0.md §2 | Root-cause the denied-block formula; once T-11 (LEL intake) lands, add an L5 gate that flags any "denied" class with a contradicting LEL event | OPEN |
| D-16 | **Discovery/anchor estate emits ZERO adverse-valence dated claims** — every anchor 1964–2030 is "elevated"/positive; 0/5 recall on the native's major negative events (father's death, scam, panic, employer crash, headache onset). ~~Structural consequence of Y-2/Y-5 (dosha/bhanga signals never reach anchor generation)~~ **ROOT-CAUSED 2026-07-16 (D-2 G0-4 Step-1): the deeper root is VAL-ROOT below — valence COMPUTATION itself structurally never emits adverse (four broken sites all default benefic). Y-2/Y-5 are contributory, not the root; retest after VAL-ROOT lands.** | DATA+LOGIC | HIGH | [accuracy-test 2026-07-10] §3 | Wire dosha/affliction signals into ph_nimitta event-type taxonomy; valence-distribution gate at seal (all-positive = collapse); **superseded-by-root: VAL-ROOT** | OPEN (root = VAL-ROOT) |
| VAL-ROOT | **CRITICAL, estate-wide, all charts — the D-16/CR-54/CR-83 valence-lineage root.** Valence computation is broken at ≥4 independent sites, all defaulting adverse configurations to favorable: (1) `bo_karanajala._EDGE_TYPE_VALENCE` keys edge valence on edge TYPE ("aspect"/"conjunction"/"dispositor"→"harmonious") ignoring the grahas' natures → **121/121 mechanisms on 482012f1 = valence "benefic"**, incl. Mars↔Saturn (two malefics); (2) `ga_vichara.compute_valence` — (actor_lordship_class × target_house) matrix; trikoṇa-membership rule pre-empts the dusthāna-affliction rule for dual-lord Mars (Aries 1L+8L), NO contact-type dimension, skips Rahu/Ketu → Mars-8th-aspect-on-H2 reads "benefic" despite `valence_source="ga_vichara_v1"`; (3) V-5 `vargottama_dhana_emitter` hardcodes `valence="benefic"` (occupancy-alone); (4) V-5 tenancy classes default benefic-on-occupancy. Plus a structural ranking gap: V-5's four separate writers insert `top_k_salience_rank=NULL` and never run bo_laksana's in-memory `_set_top_k_ranks`, so V-5 signals are invisible to top-k salience regardless of valence. Retroactively explains D-16/D-19/D-20 (all-positive valence family). | LOGIC (DATA+SURF contributory) | **CRITICAL** | [D-2 G0-4 Step-1 diagnosis 2026-07-16; live probe chart 482012f1] REPORT/STATE_D-2 | Single shared valence-doctrine module (natural × functional × dignity × contact-type → signed 4-way {benefic/malefic/mixed/neutral}) consumed by ALL emitters per **DR-9/DIS.022**; graha-nature-aware edge valence; V-5 ranking-pass fix; new graha-to-house tenancy Mechanism class; anti-overcorrection specimen gate BOTH directions; 121-mechanism valence-distribution gate. | **CLOSED (D-2 GATE GREEN 2026-07-17)** — DR-9/DIS.022 Parts A (data: shared `valence_doctrine` module, ga_vichara valence_pass) + B (partitioned adverse/supportive serve) live-verified. G0-4 amended assertion PASS (Rahu-tenancy served signed −0.50 in the THREAT layer, grounded); 3 anti-overcorrection specimens PASS (Rahu-H2 mixed not strong_malefic; Ven/Jup-H9 strong_benefic; valence_pass distribution 580/551/406/58, no single-value collapse — was 121/121 benefic). See REPORT_D-2.md §3 gate table + §7 DR-9. |
| D-17 | **Identical causal chain stamped on EVERY anchor** — every anchor's derivation ledger carries the verbatim string "Moon → Saturn → Venus → Jupiter (final dispositor)" with the same 10 cgm_path_ids; the causal-chain field is a constant, not a derivation | DATA | MED-HIGH | [accuracy-test] blind extraction §3.12 | Derive per-anchor chains from the anchor's actual constituent signals; degenerate-distribution gate on the causal-chain column | OPEN |
| D-18 | **CGM convergence-hub scores near-flat** — the 9 grahas' pagerank spans only 0.0919–0.0982 (Moon highest); "convergence hubs" carry no discrimination, so nothing downstream can rank by hub importance | DATA | MED | [accuracy-test] blind extraction §3.13 | Investigate CGM edge-weighting (flat weights → flat pagerank; likely inherits Y-6's dead modifiers); distribution check at seal | OPEN |
| D-19 | **Life-arc degeneracies** — every parva carries the constant `dominant_signal_class=DISPOSITOR_RELATIONAL`; all rows duplicated ~2x; every parva/sub-parva flagged "peak" is positive-valence only (the 2024-27 "peak" contains the May-2025 scam). Sibling of T-9 (pre-birth parvas) | DATA+LOGIC | MED | [accuracy-test] blind extraction §4; scoring §2 | Fix dominant-class derivation; dedup rows; parva quality must integrate affliction signals, not only benefic scores | OPEN |
| D-20 | **1993–98 claims: right window, wrong content** — three overlapping "transition, elevated" windows bracket the native's 1995 chronic-illness onset (negative) and end 25 days before the life-altering 1998-02-16 relationship start; the engine's only pre-2000 claims mislabel the era's actual events in both theme and valence | LOGIC | MED | [accuracy-test] scoring §2 | Symptom of T-12+D-16; retest after those land — this row is the regression witness | OPEN |

## SECTION 6 — CONCEPT COMPLETENESS (new in v2 — classical-canon audit vs L0/L1/MCP)

Verdict: ~90% of the classical canon covered at L0→L1, with genuine over-coverage (per-varga rashi-drishti +
kala-sarpa, esoteric sphuta family, KP subsystem, D108/D150/D2700, Tajaka depth, 13-category remedy corpus,
two-pass citations). The misses:

| ID | Title | Gap | Sev | Evidence | Fix approach | Status |
|----|-------|-----|-----|----------|--------------|--------|
| K-1 | **Conditional nakshatra dashas + Jaimini sthira/shoola/Narayana not computed** — L1 computes Vimshottari(4-level)/Yogini/Ashtottari/Kalachakra/Chara only; Shodashottari/Dwadashottari/Panchottari/Shatabdika/Chaturashiti/Dwisaptati/Shashtihayani exist only as OCR text; Narayana L0-catalog-only | DATA | MED | [concept] | PyJHora exposes most; add as ga_dashas substeps gated by applicability predicates (store applicability verdicts even when not applicable) | OPEN |
| K-2 | **Kuta/ashtakoota matching has no compute path** — all kootas modeled as L0 doshas with bhanga + remedies (l0_doshas.py:540-711) but no two-chart engine or tool; apex_marriage runs single-chart only | DATA | MED | [concept] | `ga_kuta` service tool (chart_a × chart_b, deterministic) — L0 substrate already rich | OPEN |
| K-3 | **Sarvatobhadra / Kota / Sudarshan chakras retired to archive, never rebuilt** — migrations 140/141/144 live only in `platform/migrations/_archive/`; SBC vedha tracking is mainstream transit practice | DATA | MED | [concept] | Rebuild as ka_gochara-adjacent SERVICE (deterministic grid + vedha lines from bg tables), not storage — per transit=service-not-storage ruling | PARTIAL — Sudarshan half CLOSED_WITH_EVIDENCE, Sarvatobhadra/Kota half stays OPEN [D-1.6 S-7, 2026-07-16: bodha_signals_get(signal_type_class=sudarshana_agreement) → 9 tri-frame signals live (per-graha house/class from Lagna/Moon/Sun, agreement verdicts incl. contradicted/partial_2frame), constituent facts resolve 0-orphan; D-1.5b B-3 receipt confirmed live — Sudarshana Chakra is REBUILT and served. NOTE: the Sarvatobhadra remainder has nakshatra-occupancy recorded (sarvatobhadra_vedha row in sensitive_degree_check) but no vedha-line service; Kota not built — this row stays open for those halves only (PARTIAL-with-pointer, not this wave's S-7 item scope)] |
| K-4 | **Sannyasa/pravrajya yoga class not detected** — L0 catalogs it (l0_yogas.py:39); no detector | DATA | LOW-MED | [concept] | Add to ga_yoga catalog-driven firings (trivially deterministic) | OPEN |
| K-5 | **Mrityu-bhaga degrees + bhava madhya/sandhi occupancy flags absent** — (S-9 sibling) KP cusps exist but no sandhi placement flags; sandhi materially alters bhava-phala strength | DATA | LOW-MED | [concept] | Cheap degree-table checks in ga_sensitive/ga_positions | OPEN |
| K-6 | **Rectification engine has no tattva/D60 method** — event-anchor scoring only; also `calibration_state:"calibrated"` label with 0/36 training matches is misleading | DATA+DOC | LOW-MED | [probe-K][concept] | Add tattva ladder per §31.4; relabel calibration_state honestly | OPEN |
| K-7 | **Saturn/Jupiter/Rahu return events not first-class** — derivable from transit anchors but no explicit return event type | DATA | LOW | [concept] | Event type in ka_gochara once T-1 sidecar restored | OPEN |
| K-8 | **Prana (level-5) dasha excluded BY DESIGN** — documented override, sentinel row emitted. Recorded so nobody re-reports it as a bug | — | — | [concept] ga_dashas_writer.py:11 | None (design decision) | N/A |

## SECTION 7 — SECURITY / OPS / INFRA

| ID | Title | Gap | Sev | v2 status | Status |
|----|-------|-----|-----|-----------|--------|
| O-1 | Rate limiting absent on MCP surface | INFRA | MED | Unchanged | OPEN |
| O-2 | `amjis-pending-stream-reaper` silent 401 (Cloud Scheduler auth header) | INFRA | MED | Unchanged; fix pattern proven by the 2 new schedulers | OPEN — R6 2026-07-10 prod probe: code fix landed (x-marsys-cron-secret header pattern) but the LIVE Cloud Scheduler job amjis-pending-stream-reaper still targets the OLD wrong URI /api/cron/reap_pending_streams (userUpdateTime 2026-05-28, unchanged) — infra/terraform-apply gap, the fix was never wired to the actual Scheduler resource. Direct POST to the live configured URI confirmed still 401. |
| O-3 | Capability-route entitlement | INFRA | — | FIXED (R5.2 A1, PR #498) | FIXED |
| O-4 | Grader model-name fragility | INFRA | — | FIXED (R5.3 §B) | FIXED |
| O-5 | **callPlatformPrimitive 401 still LIVE in prod** — evidence-pinned this audit: ref_transit_rules_get + asset_registry_all/_l0 all 401 (= R-16). The "1-line P0" from the MCP-elevation audit remains unshipped | INFRA | CRITICAL | [probe-G][probe-K] | PARTIAL — R6 2026-07-10: see R-16 (same finding, duplicate row) — ALLOWED_TABLES whitelist gap + proxy.ts isPublic allowlist gap, both newly pinned, neither is the original callPlatformPrimitive header issue (that part IS fixed). |
| O-6 | **Remedy tool bundle missing DATABASE_URL in runtime** (= R-15) — 6 primitives + 6 aliases down | INFRA | HIGH | [probe-K] | OPEN |
| O-7 | **Alias→primitive layer inconsistently healthy** — kala_muhurta_get works / muhurta_finder dead; ref_remedies_get works / 6 sibling aliases 500; catalog_* works / asset_registry_* 401 — no conformance contract between a tool and its alias | INFRA | MED | [probe-K] cross-cutting | Single alias→primitive conformance sweep + per-tool smoke battery in CI (subsumes the per-tool fixes' verification) | OPEN |
| O-8 | **DB connection through the Cloud SQL Auth Proxy is terminated on a ~20-25-min cycle mid-transaction, independent of client keepalives** — surfaced during the Doctrine-Campaign Night-1 guarded rebuild (2026-07-14). `ka_sangam` (1 near + up to 60 lifetime substeps, each a ~100-yr convergence scan) died repeatedly with `psycopg.OperationalError: server closed the connection unexpectedly` raised from `runner.py`'s scheduler-connection `should_stop()→rollback()`. TWO distinct killers were isolated: (1) a **role-level `idle_in_transaction_session_timeout=600s`** on `amjis_app` that the orchestrator's libpq `options="-c ...=0"` startup param did NOT reliably disable through the proxy (killed at ~10-11 min) — **FIXED** (commit 011253fc: issue `SET idle_in_transaction_session_timeout=0` + `SET statement_timeout=0` as explicit executed statements post-connect, which no proxy can strip); (2) a **second, longer ~20-25-min connection-lifetime killer** (proxy- or server-side; `cloud-sql-proxy` exposes no lifetime/keepalive flag) that the SET-fix does NOT address — a full `ka_sangam` run exceeds it. Client keepalives (30s idle / 10s interval / 5 count) are already set and do not prevent it. This is the same connection-instability that tanked T-5's rebuild ("repeated forced DB-connection kills … interrupted otherwise-clean progress"). | INFRA | HIGH | Night-1 guarded rebuild 2026-07-14: `build_runs` shows 8+ consecutive `ka_sangam` failures; verified-timeline isolated run healthy 11:38:29→12:01:44 (23 min) then died at row 6854; `pg_roles.rolconfig` confirms the 600s role default; `cloud-sql-proxy --help` confirms no lifetime flag | **ROUTED-AROUND, root cause OPEN.** Killer (1) fixed (011253fc). Killer (2) is routed around by substep-level RESUMPTION (migration 436 `build_substep_progress` + `ka_sangam.plan_substeps` resume/replan; commit TBD) — a build now RESUMES across a dropped connection instead of restarting from substep 1, so it completes over a bounded number of auto-resuming attempts regardless of any single connection's lifetime. The **underlying connection instability remains a latent defect** that will bite any other long-running writer (or a long serving query) and deserves its own investigation: determine whether it is a Cloud SQL server `tcp_keepalives`/max-lifetime setting, a proxy version issue, or local-network NAT idle-eviction; consider running heavy builds via the deployed Cloud Run Job (`brahma-build-pipeline-job`) inside GCP rather than through a local proxy. Cross-ref T-5, and the watchdog-reaper heartbeat bug noted in T-5's status. |

## SECTION 8 — CONTENT-DEPTH / ACCEPTANCE (R5.3 in flight — carried)

| ID | Title | Gap | Sev | v2 note | Status |
|----|-------|-----|-----|---------|--------|
| C-1 | 16 below-floor rubric battery items | LOGIC/depth | HIGH | Carried; this register's Sections 4–5 explain much of the floor misses (dead tools, degenerate content) | IN-PROGRESS (R5.3) |
| C-2 | D60 rectification-confidence / time-sensitivity not served | SURF | MED | Carried; see also K-6 | FIXED [PR #514, verify-against: prod 2026-07-10] — `query_chart_facts(divisional_chart='D60')` now attaches `judgment_flags:['time_sensitive_low_confidence']` + a narrated `time_sensitivity_note` citing the chart's actual `phala_rectification_best` state (native chart `482012f1`: confidence_label='unresolved', win_margin=0, 0/36 LEL matched — genuinely below the §31.4 sensitive_extreme bar) when rectification confidence is below threshold. Facts still served in full, framing-only change. Live-verified post-deploy. |
| C-3 | Acceptance gate un-met (≥90% target; R5.2 actual 31.6%) | process | HIGH | Carried | IN-PROGRESS (R5.3) |
| C-4 | **Muhurta quality: inauspicious panchanga offered for marriage** — Ekadashi/Vaidhriti/Chaturdashi windows ranked for marriage election | LOGIC | MED | [probe-K] new | OPEN |
| C-5 | **L5's own calibration strata confirm the scores are meaningless** — predictions binned [0.5,0.6) → 0% observed (n=55); [0.6,0.7) → 3.6% (n=28); [0.8,0.9) → 100% but n=2 prior_only. The engine already possesses the evidence that its confidence vocabulary is uncalibrated, and nothing consumes it | LOGIC/process | HIGH | [accuracy-test] blind extraction §3.14 | Once T-11 (LEL) + T-12 (real anchors) land, wire the calibration strata into serve-time epistemic grades (fixes R-2 with real data) and into an L5 alert when a stratum's observed rate diverges from its bin | OPEN |
| C-6 | **Composed rubric items requiring 2+ independent raw-data tool calls structurally cannot pass an LLM-synthesis rubric floor** — `Q8-A-1` ("does his debilitated Jupiter need fixing") calls `graha_portrait` + `bodha_remedies_get` independently; both individually correct, well-formed, non-error (B2-verified: R5_3_RUN_LEDGER_v1_0.md); joined and graded together, Gemini scores 3/11 because the item needs a genuinely synthesized answer to an ordering question ("is it broken, THEN what's the remedy") that two raw structured payloads concatenated cannot express by construction. Product-boundary / gate-calibration question, not a simple defect — flagged per the R5.3 brief's own embedded caveat on this exact item, for native/R6 to rule on whether such items need an orchestrating-LLM synthesis step the current architecture doesn't have (see also Q7-N-2's identical structural INCONCLUSIVE) | process | MED | [R5.3 B2/B4, verify-against: prod 2026-07-10] `results_90a14176.json` Q8-A-1 (3/11) | Native/R6 call: either (a) redesign such battery items to grade each tool call independently, or (b) build the orchestrating-LLM synthesis layer these items actually require | OPEN |

## SECTION 9 — RESOLVED (audit trail; do not reopen without cause)

Carried from v1: 17MB/63KB flagship payloads → C1 budgets (verified live: judgment/portrait ≤12KB);
as_of_date on get_dashas → fixed (re-verified live 2026-07-10: Ketu MD for 2027-09-01); phala serving SQL
vs mig-330 → addressed; chart-header frame safety → structurally fixed (every v3 response verified);
muhurta_finder fabrication → replaced by real-or-empty (but see T-7: the tool now returns NOTHING);
native Bodha staleness → healed by R4.

New in v2: **R-4 stale provenance literals → FIXED** (live freshness derivation verified both charts);
**S-4 virupa drishti → computed** (verify served, then close); **S-5 gandanta → served** (verified live);
**T-2 forward panchanga → PARTIAL** (kala_muhurta_get real windows; muhurta_finder still dead);
**T-3 tool-level → ganita_dashas_get boundary correct** (pact path remains, see T-3);
**query_remedies 106KB blob → compact envelope** (but filters broken, R-19);
**R5.1/R5.2 positive controls verified live:** chart_snapshot correct both charts; get_chart_quality live
scorecard honest; get_domain_reading bounded with honest model_mismatch_note; pact "pending NOT denied"
honest-halt on Abhinandan; no cross-chart positions contamination (chart B Sun Aquarius ≠ chart A Sun
Capricorn); all 7 FORENSIC anchors reproduced across lahiri + raman ayanamshas; Mercury sole-vargottama
rollup correct.

---

## SECTION 10 — ACCURACY BASELINE (2026-07-10; the measuring stick for the whole campaign)

Full method + evidence: `00_ARCHITECTURE/DISCOVERY_ENGINE_ACCURACY_TEST_v1_0.md` (blinded
retrodiction, chart 482012f1 vs LEL v1.7). These numbers are the BEFORE; the campaign's success
is measured by re-running the identical blinded protocol after each wave.

| Metric | Baseline 2026-07-10 | Campaign target |
|---|---|---|
| Temporal coverage of 2000–2026 by dated claims | ~12% (one window union) | ≥60% of adult years carry ≥1 claim (T-12 gate) |
| Recall on 15 major LEL events | ~4–6/15 (27-40%), all in one window | ≥60%, distributed across ≥4 distinct windows |
| Recall on major NEGATIVE events | 0/5 (0%) | >0 — any dated adverse claim at all is progress (D-16) |
| Distinct anchor-basis cycles cited | 1 (Saturn@Aquarius) | >3 (T-12) |
| Confidence discrimination | uniform 0.322 floor (one 0.4629) | non-degenerate distribution (S-15/D-3 class gates) |
| Absurdity check (pre-birth / duplicate claims) | FAIL | zero pre-birth, dedup'd (T-5/T-6/T-9) |
| Calibration strata vs observed | [0.5,0.6)→0% (n=55) | strata consumed at serve time (C-5) |
| Recorded genuine hit (preserve, don't regress) | 2022-25 Sade Sati career window, correctly typed | must still fire after all fixes |

## SECTION 11 — TAP FULL-PROTOCOL FINDINGS (v3.0, 2026-07-10 — TAP-4/5/6/7/8 executed)

### §11.1 — METHOD INTEGRITY (TAP-6) — the gravest class: non-canonical methods wearing canonical labels

All rows: writer estate, file:line verified, quoted in the TAP-6 report. Common aggravator: rows
stamped `two_pass_verified` as a STRING LITERAL at emit sites and/or `pyjhora_adapter.*` source
strings on hand-rolled code — the verification vocabulary itself is compromised (M-22).

| ID | Title | Sev | Evidence | Fix | Status |
|----|-------|-----|----------|-----|--------|
| M-1 | **Shadbala never calls PyJHora — a 0-1 toy heuristic stamped two_pass_verified** — sthana=6-bucket lookup (no saptavargaja/ojayugma/kendradi/drekkana), dig=linear house distance, kala=day/night membership only, cheshta=retro-flag→1.0/0.5; "verification" = sub-balas-sum-to-total (self-referential, always passes) | CRITICAL | ga_strength_writer.py:1590, :209-361, docstring :13-29 claims PyJHora | Delegate to PyJHora strength module (exists); invariants become sanity checks not verification claims | OPEN |
| M-2 | **Vimshopaka bala is not vimshopaka** — `min(total/6*20,20)` × cosmetic 0.85/0.90/0.95 per scheme; consumes ZERO varga dignities | CRITICAL | ga_strength_writer.py:388-405 | Compute from ga_vargas per-varga dignity rows with BPHS weight tables | OPEN |
| M-3 | **Ashtakavarga "sodhita" pinda has no shodhana** — trikona skipped (`sodhita ≡ raw`, comment admits), ekadhipatya faked as bindus−1, no gunakara multiplication | CRITICAL | ga_strength_writer.py:931-932 | Implement BPHS shodhana + gunakara or delegate to PyJHora | OPEN |
| M-4 | **ga_vargas per-varga BAV loop bug: all 8 BAVs identical** — inner loop credits every contributor to ALL grids; SAV = 8× one array; correct 8×8 matrix exists unused in ga_strength_writer:441+ | CRITICAL | ga_vargas_writer.py:590-599 | Reuse the full matrix per varga or PyJHora | OPEN |
| M-5 | **Mudda dasha year-lord = rotating Vimshottari index** — not the janma-nakshatra-anchored classical derivation; stamped two_pass_verified | CRITICAL | ga_dashas_writer.py:1797-1809 | Classical Mudda start-lord; unstamp | OPEN |
| M-6 | **Kalachakra dasha ignores the Kalachakra tables** — contiguous signs from Moon-navamsha index; no savya/apasavya, no deha/jeeva, no gati jumps, flat 100y paramayush | CRITICAL | ga_dashas_writer.py:1940-1977 | PyJHora ships Kalachakra; delegate | OPEN |
| M-7 | **Chara dasha falls back to the NATIVE's hardcoded params for ANY chart** — on conn=None/exception: AK=Sun/Capricorn + native CHARA_YEARS ("falling back to FORENSIC hardcoded"); also `years=7 # safe fallback` fabricates period lengths | CRITICAL | ga_dashas_writer.py:1440-1464, :1404 | Hard-fail, never fallback (B1-elimination pattern) | FIXED [verify-against: prod, R6 2026-07-10] |
| M-8 | **Sidecar Jaimini router serves native-fallback longitudes that are WRONG even for the native** — NATIVE_FALLBACK_LONGITUDES: Sun 322.61 Aquarius (truth: Capricorn), Lagna 51.28 Taurus (truth: Aries); plus a non-classical chara-years formula (30−deg capped) on a live HTTP endpoint | CRITICAL | panchang_engine/jaimini_chara.py:65-82; routers/jaimini.py:108-129 | Kill the fallback table; require longitudes; use the correct KN-Rao count already in ga_dashas | FIXED [verify-against: prod, R6 2026-07-10] |
| M-9 | **Fabricated formulas with fabricated classical citations** — Pranapada = Moon+(Lagna−Sun)×4 cited "BPHS" (real BPHS: time-from-sunrise palas/15 on Sun with sign offsets); "Trikona Dasha Sphuta" cited "Jaimini Sutram" (no such sphuta); "Sri Yantra position" = longitude×0.9 (invented) | CRITICAL (B.10 violation) | ga_sensitive_writer.py:826-831, 843-848, 866-869 | Delete or floor `[EXTERNAL_COMPUTATION_REQUIRED]`; compute real Pranapada | OPEN |
| M-10 | **Special lagnas use Sun's within-sign offset as a time proxy** — HL=lagna+(sun%30)×2, GL=+(sun%30)×12, BL=2Sun−lagna+180; classical HL/GL/BL advance by time-since-sunrise. Values essentially arbitrary yet served | CRITICAL | ga_sensitive_writer.py:2068-2091 | Delegate to PyJHora (computes natively) | OPEN |
| M-11 | **Upagraha Kala = Saturn+30°; Gulika-Hindu = Gulika+30°** — invented constants vs time-division rules; live recompute divergence proven (V-7) | MATERIAL | ga_sensitive_writer.py:549, 620-621 | Prefer PyJHora upagraha values | OPEN |
| M-12 | **Tajika aspects: no geometry, no applying/separating, no deeptamsa** — <1°=yamaya, <5°=ithasala, <30°=manaau; eesarpha/nakta unreachable; source stamped pyjhora_adapter + two_pass_verified (both false) | CRITICAL | ga_structural_writer.py:1141-1176 | Real Tajika rules (per-planet deeptamsa, motion) or PyJHora tajaka | OPEN |
| M-13 | **ga_tajaka yogas: flat 7° orb, no Tajika-aspect precondition** — Ithasala fires on any applying pair; Kambula without Moon conditions | MATERIAL | ga_tajaka_writer.py:293-335 | Per-planet deeptamsa + mutual-aspect gate | OPEN |
| M-14 | **"BPHS weighted" composite strength = invented proxy with false PyJHora provenance** — kendra constants + `shadbala_proxy = sthana*5+1 # rough rupa estimate`, emitted ×12 hypothetical houses as graha_in_house_composite_strength | CRITICAL | ga_structural_writer.py:2240-2289 | Derive from real shadbala+bhava bala post-M-1; fix source strings | OPEN |
| M-15 | **Graha yuddha winner by higher longitude** — comment admits latitude needed; classical = latitude/brightness | MATERIAL | ga_condition_writer.py:910-948 | Fetch ecliptic latitude (Swiss Ephemeris has it) | OPEN |
| M-16 | **Arudha 2nd exception missing** — only own-sign→10th handled; 7th-from→4th absent → wrong arudha whenever lord is 4 signs away (A1-A12 + graha arudhas) | MATERIAL | ga_sensitive_writer.py:1231-1242 | Add the branch | OPEN |
| M-17 | **D60 deities = repeating [Malefic,Neutral,Benefic]×20** — canonical 60-deity list is irregular; ~half mislabeled while D60 carries the HIGHEST vimshopaka weight in serving (priors_config D60=0.95) | MATERIAL | ga_vargas_writer.py:192 | Embed canonical table (bg reference data) | OPEN |
| M-18 | **Saptavargaja bala: wrong category ladder, ignores compound friendship** | MATERIAL | ga_vargas_writer.py:1292-1298 | Compound (naisargika+tatkalika) relation per varga, classical virupa ladder | OPEN |
| M-19 | **Combustion: node-combustion invented in fallback (Rahu/Ketu orb 9°); retrograde orbs absent entirely** (Mercury 12°R, Venus 8°R) | MATERIAL | ga_condition_writer.py:642-652 | Drop node rows; add orb_retro branch | OPEN |
| M-20 | **Sade-sati vargottama intensity by "own-sign territory" approximation** while the correct D9 computation exists in the same repo | MATERIAL | ga_sade_sati_writer.py:608 | Use the real D9 sign | OPEN |
| M-21 | **Varsha-pravesha = birth JD + N×365.25** — not the Sun's sidereal return (drift ≈14h by age 42, shifts boundary-adjacent periods) | MATERIAL | ga_dashas_writer.py:1777, 1992-1996 | swe solar-return search (adapter has it) | OPEN |
| M-22 | **`two_pass_verified` is a string literal at emit sites** — wherever M-5/6/12/14 apply, the verification column lies. Class rule: verification status must be computed by a verifier, never passed as a literal | CRITICAL (epistemic) | grep evidence across ga_dashas/ga_structural | CI grep bans the literal at emit sites; verifier owns the column | OPEN |

### §11.2 — VALUE/DISTRIBUTION DEFECTS (TAP-7 + TAP-3b recompute)

Recompute control: **all 9 graha positions + lagna + panchanga anchors match live PyJHora exactly
(10/10)** — the positional core is sound. The rot is in derived quantities:

| ID | Title | Sev | Evidence | Fix | Status |
|----|-------|-----|----------|-----|--------|
| V-1 | **chart_dashas lord_natal_* SYSTEMATICALLY contaminated — 6/9 MD lords wrong** (Mars: Cap/exalted/h10 vs truth Libra/neutral/h7; Rahu: Leo/h5 vs Taurus/h2; Ketu carries Moon-like values; Sun dignity "exalted_friend" in Capricorn; subsumes D-1 + G-7). Any Kāla/Phala consumer of these columns inherits wrong astrology | CRITICAL | [TAP-7] rows b488f391/5fc5a603/63bfd0e5/cf3720cd/ffe60700/ccb632f0/b8cc36f5 | JOIN to chart_facts at write; CI equality gate | FIXED [verify-against: prod, R6 2026-07-10] |
| V-2 | **Cheshta bala = 0.5 rupa constant, ALL planets, BOTH charts** (chart-invariant ⇒ engine-level; consistent with M-1) | HIGH | facts edde4c95/e6f692f6 | Falls out of M-1 delegation; distinctness gate | OPEN |
| V-3 | **Sthana bala quantized {0, 0.375, 0.75}; own-sign Jupiter = 0; exalted Saturn = 0.375** | HIGH | facts f54a408f/c25fa399 | M-1 delegation | OPEN |
| V-4 | **Ishta/kashta collapse: 5/7 planets identical (25.98/33.54)** — arithmetic consequence of V-2/V-3 | MED | fact 7be09369 | Auto-fixes with M-1; add gate | OPEN |
| V-5 | **Saturn's special 3rd/10th drishti not full-strength** (0.25/0.75 vs classical 1.0; Jupiter/Mars specials correct); propagates into L2 aspect signals | MED-HIGH | facts 488b4b59/499680cc | Fix special-aspect table for Saturn | OPEN |
| V-6 | **Upaketu == Indrachapa** (missing final step; identity Upaketu+30°=Sun fails: 275.30 vs 291.96) | MED | fact 76027992 | Fix formula; identity gate | OPEN |
| V-7 | **Stored KALA upagraha = Saturn+30° exactly; live kaala = 304.14° (71.7° off)** — data-side proof of M-11 | MED | fact 9ef35219 | M-11 | OPEN |
| V-8 | **query_chart_facts ignores `offset` (shape=rows)** — page 2 = page 1; silently breaks all sampling beyond page 1 (this bug also blinded parts of this very audit) | MED-HIGH | offset=48 identical page | Fix pagination; disjointness gate | FIXED [verify-against: prod, R6 2026-07-10] |
| V-9 | **All stored MD boundaries ~1 day early with time-of-day dropped** (stored 2027-08-18 00:00 vs live 2027-08-19T11:55) — as-of queries near boundaries misclassify for ~30h windows | MED | live diff table | Store full timestamps from engine; boundary recompute gate ±6h | FIXED [verify-against: prod, R6 2026-07-10] |
| V-10 | **MSR composite saturates at 0.8999… for 7/10 top rows** — rank inside the wall decided by 1e-10 float noise; "chart_defining" ordering effectively arbitrary | MED | [TAP-7] career top-10 | Rescale/tiebreak; spread gate >1e-3 | OPEN |
| V-11 | **chart_dashas dead enrichment columns** — sandhi_flag always true; lord_natal_shadbala_total always null; triggered_yogas always []; lord_transit_at_start always null | LOW | 10-row sample | Populate or drop | FIXED [verify-against: prod, R6 2026-07-10] |
| V-12 | **KP sub-lord chains stored at level_n=2 in the SAME table/system as Vimshottari antardashas** — get_dashas returns two Mercury-Saturn L2 rows with divergent dates (kp_sub 2024-12-04→2027-08-14 vs L2 2024-12-08→2027-08-18); any level≤3 consumer double-counts periods | HIGH | [TAP-5 Law-7] citations ...kp_sub vs ...L2 | Separate dasha_system key + filter defaults; explains TAP-8's "future AD as active" confusion | FIXED [verify-against: prod, R6 2026-07-10] |
| V-13 | Sade-sati cycle rows pairwise duplicated to the second (C3/C4 end 1998-04-17T07:34:13 identical) — hard evidence for D-2 | (D-2) | facts cdd25c6d/0702a424 | D-2 fix + uniqueness gate | FIXED [verify-against: prod, R6 2026-07-10] |

### §11.3 — SEAM CONSERVATION VIOLATIONS (TAP-5) — every seam is a hand-maintained registry that drifted

| ID | Title | Sev | Evidence | Status |
|----|-------|-----|----------|--------|
| SC-1 | `graha_nakshatra_join` (gana/guna/shakti/deity/yoni/nadi per graha — the nakshatra-personality substrate) built, ZERO serving references, absent from coverage matrix | HIGH | live rows + 0 grep hits | OPEN |
| SC-2 | `graha_speed_state`/`graha_retrogression_state`/`graha_combustion_state` unserved — combustion is a first-order judgment input | HIGH | ga_structural:3020, ga_positions:300; no tool | OPEN |
| SC-3 | D1 `parivartana_pairs` orphaned by category-name split (serving knows only parivartana_per_varga; get_yoga_dosha.ts:16 admits the mismatch) | MED | ga_structural:2557 vs get_dispositors.ts:12 | OPEN |
| SC-4 | Ashtakavarga refinement set unserved: trikona/ekadhipathya shodhana, kakshya, per-varga bindu/pinda — exactly what transit-ashtakavarga judgment needs | MED | get_ashtakavarga.ts:11-12 | OPEN |
| SC-5 | `karaka_per_varga` + `nakshatra_cross_ayanamsha` unserved; 39 total emitted categories absent from the coverage matrix (S-13 confirmed: matrix stuck at "158 categories" vs 187 emitted) | MED | TAP-5 Law-1 diff | OPEN |
| SC-6 | CGM `sade_sati` edge type declared in valence/basis maps, never emitted — zero temporal-affliction edges | MED | bo_karanajala.py:99-118 | OPEN |
| SC-7 | **Parivartana never becomes a CGM edge** — the quintessential exchange relation absent from the causal graph (grep=0 in bo_karanajala) | HIGH | bo_karanajala.py | OPEN |
| SC-8 | Karaka web, KP significators, Jaimini/Tajik aspects: no edge types — non-Parashari relational estates never enter the graph | MED-HIGH | bo_karanajala edge census | OPEN |
| SC-9 | Virodha-argala only a valence flip on argala; unmatched class → obstruction recorded as harmonious | LOW-MED | bo_karanajala.py:128 | OPEN |
| SC-10 | **155/187 signal categories fall through `_DOMAIN_MAP`** — whole sensitive-points estate (incl. sahams with individually-defined domains: Punya/Vivaha/Roga!) on hard default ["career","character"]; aspect_parashari_received unmapped while _given is; virodha_argala unmapped while argala is; all bhava_bala_* unmapped (house-specific by nature); kantaka_shani (career-obstruction) generic | HIGH (aggregate; expands KP-4) | bo_laksana.py:313-366 diff | OPEN |
| SC-11 | **bodha_msr_signals epistemic annotation set write-only** — epistemic_tier, domain_salience_jsonb, salience_confidence_interval, conditioned_by, pada_precision_flag, strength_normalized_to_chart_max: ZERO readers (25 TS files read the table, none touch these) | HIGH | TAP-5 Law-4 | OPEN |
| SC-12 | CDLM diagnostics dark: cross_domain_contradiction_flag, asymmetric_linkage_flag, stability/gradient scores, house/karaka_to_domain_strength_jsonb — the B.11 contradiction machinery exists and is unread | MED-HIGH | Law-4 | OPEN |
| SC-13 | **Whole tables with ZERO readers: bodha_cgm_motifs, bodha_cgm_paths, bodha_cdlm_evolution_gradients, bodha_triangulation** — registered, built, counted, never served | HIGH | Law-4 | OPEN |
| SC-14 | **bo_pratijna (Promise Register), ka_avadhi, ka_taranga: built-but-unservable** — zero TS readers; even pact_query recomputes the promise chain live instead of reading bodha_pratijna. These are the Beyond-Acharya PROMISE→ACTIVATION spine | HIGH | Law-5 | OPEN |
| SC-15 | `kala_timeline` served but owned by NO registered asset (inverse conservation failure — untracked by any count_sql) | MED | Law-5 | OPEN |
| SC-16 | 20+ per-chart ka_*/ph_* assets carry target_floor NULL with no documented reason (floor-hygiene drift) | LOW | Law-5 | OPEN |
| SC-17 | `bodha_bundle_get` recover-pointer targets a tool that was never registered (rename never shipped; live tool = holistic_bundle_chart_facts) | MED | holistic_bundle.ts:73 | OPEN |
| SC-18 | **Budget-trim recover pointers name INTERNAL capability names, not MCP tools** (get_dignity/get_avasthas/get_divisionals/query_signals…) — the recovery path fires exactly when data was withheld and points at tool-not-found | HIGH | registry_bridge.ts:2098-2493 | OPEN |
| SC-19 | `instrument:'bo_upaya'` puts an asset id in a tool-pointer field | LOW | query_remedies.ts:272 | OPEN |
| SC-20 | `ganita_positions_get` ≠ `get_positions` — alias returns flat EAV incl. aprakasha-first, no planet param; primitive returns pivoted rows; primitive's planet filter ineffective (67KB) | HIGH | Law-7 live diff | OPEN |
| SC-21 | `bodha_graph_subgraph_get` is a capability-degraded alias of get_cgm_subgraph (no mode/seed/about/min_strength; "same as" claim false; limit ignored) | MED-HIGH | Law-7 | OPEN |
| SC-22 | Mimamsa calibration outputs unreadable: score_manifestation/score_falsifier, hit_rate_by_tier, negative-control scores, phala rectification_confidence — the calibration loop's own outputs have no serving path (compounds C-5) | HIGH | Law-4 | OPEN |

### §11.4 — INSTRUMENT/LATERAL DEFECTS (TAP-8 + TAP-4 battery)

| ID | Title | Sev | Evidence | Status |
|----|-------|-----|----------|--------|
| P-1 | **pact ACTIVATION searches only the bhavesha/karaka's MDs — the actually-running MD lord is not an input** — karmic-debt timing answered "2070-08-18" (native age 86) while Ketu MD opens 2027-08; Ketu-MD business question → "nothing until Venus 2034"; progeny at twins' birth date → "no promise-carrying dasha running" (AD-blind); career as_of 2023-04 cites a FUTURE Saturn AD (2024-12→2027-08) as "running" (V-12's kp_sub row confusion implicated). Any question about an upcoming/running dasha is structurally unanswerable | CRITICAL | [TAP-8 Q1/Q3; TAP-4 GS-17/18] verbatim snippets in reports | OPEN |
| P-2 | **Career domain tag covers 92.5% of ALL signals (12,419/13,426)** — the domain dimension has collapsed; progeny lens leaks into career reading; get_domain_reading emits attribution-free signal-ID arrays | HIGH | [TAP-8 Q7] | OPEN |
| P-3 | **No D1↔D9 promise-vs-delivery synthesizer** — chart_snapshot serves the atoms raw (Saturn D1 exalted Libra → D9 ARIES DEBILITATED — the richest promise/delivery fact in the chart, never named by any instrument; Mercury vargottama likewise) | HIGH | [TAP-8 Q11] | OPEN |
| P-4 | **Relational significations missing from shastra map** — father (9H+Sun pitru-karaka), mother, siblings absent; 9H routed to "Spirituality" only; zero dated backward (retrodiction) entry point in any instrument | HIGH (extends G-5) | [TAP-8 Q4] | OPEN |
| P-5 | **Top "chart_defining" signal is a null flag** — `is_yoga_karaka=false` scored valence=benefic, salience 2.3, ranked #1; false-valued flags compete in ranking | MED-HIGH | [TAP-8 Q12] | OPEN |
| P-6 | **query_chart_facts sign filter dead for divisionals** — divisional_chart=D9 + sign=Gemini → 0 rows while D9_JUP=Gemini demonstrably exists (binds to D1 sign column) | MED | [TAP-4 GS-10] | FIXED [verify-against: prod, R6 2026-07-10] |
| P-7 | **Digest/narration strength semantics inverted** — weakest_graha="Mercury" contradicts served shadbala (Venus 2.36 < Mercury 2.50) AND the archive (Venus=SIG.12); portrait "required rupas" grading calls exalted Saturn "weak (deficit)" with no intra-chart rank | HIGH | [TAP-4 GS-14; TAP-8 Q2] | OPEN |
| P-8 | **Degenerate parivartana narration: "Saturn_in_Capricorn_Saturn_in_Capricorn" self-exchange** minted for a planet in Libra — own-sign rows become fake exchange edges in portraits | MED | [TAP-4 GS-08] | OPEN |
| P-9 | **Sade Sati unanswerable as a life question** — rich 15-category data pages out as EAV shrapnel; cycle numbering starts pre-birth and differs across period families ("cycle 2 of my life" unresolvable); NO flagship instrument mentions Sade Sati at all | MED-HIGH | [TAP-4 GS-04] | OPEN |
| P-10 | **judgment_query never consults bhava_bala** — the 7H max-dignity-occupant/min-house-strength paradox (the chart's declared inflection point) cannot surface through any instrument | MED-HIGH | [TAP-4 GS-16] | OPEN |
| P-11 | **Mahapurusha false negative manufactured from absence-of-rows** — "Sasa is not formed" asserted against an exalted-kendra Saturn because the label rows weren't served (extends Y-12: absence-of-row ≠ verified negative, now proven on the most famous yoga class) | HIGH | [TAP-8 Q9] verbatim | OPEN |

### §11.5 — TAP-4 GOLDEN BATTERY RESULT (the new standing regression baseline)

Corpus: `00_ARCHITECTURE/GOLDEN_SIGNALS_482012f1_v1_0.yaml` (22 golds mined from FORENSIC v6.0,
DEEP_ANALYSIS SIG/CVG/CTR, LEL retrodictive blocks + this session's earned golds).
**Baseline 2026-07-10: PASS 3 · PARTIAL 13 · FAIL 6.** Campaign target: PASS ≥ 18/22, zero FAILs.
12/19 non-PASS grades trace to registered rows (Y-1, KP-1..6, S-1); 7 to Section-11 rows.
TAP-8 adversarial battery baseline: **A:0 B:3 C:3 D:6** — target ≥ 6 A, zero D.
Archive erratum (not an engine defect): LEL "Ketu in 5H Leo" contradicts FORENSIC KP §4.2
(Scorpio/Jyeshtha) — correct the LEL at next intake.

### §11.6 — TAP-9 COVERAGE SELF-DECLARATION (this audit)

| Oracle battery | Status 2026-07-10 |
|---|---|
| TAP-1 Form sweep | APPLIED (v2.0 five-lane probe) |
| TAP-2 Canon conformance | APPLIED (concept lane) |
| TAP-3 Truth battery | APPLIED (anchors ✓ · recompute sampling ✓ 10/10 positions, derived values ✗ see §11.2 · LEL retrodiction ✓ · absurdity gates ✓) |
| TAP-4 Golden-signal regression | APPLIED — 22 golds, baseline 3/13/6 |
| TAP-5 Seam conservation | APPLIED — 7 laws, 22 new violations + CI spec per law |
| TAP-6 Method audit | APPLIED — 21 MATERIAL/CRITICAL + stamp-literal class; ~145 benign |
| TAP-7 Distribution sweep | APPLIED — 12 column families, 2 charts (SAV values + per-varga drishti beyond D1 blocked by V-8 pagination bug — re-run after fix) |
| TAP-8 Adversarial battery | APPLIED — 12 lateral questions, graded |
| TAP-9 This declaration | APPLIED |

Known residual blind spots: SAV numeric values + per-varga drishti values (V-8 blocks paging);
portal UI layer (Cowork audits MCP/data planes only); Abhinandan chart sampled on 2 families only.

## PHASED IMPLEMENTATION PLAN (v3.0 — supersedes the v2 wave plan below; designed for sub-agent
## parallel execution, sequential only where dependencies force it)

**Dependency spine:** Phase 1 (computation truth) must precede anything that ranks/judges on
strength values; Phase 2A/2B/2C are mutually parallel after Phase 1; Phase 3 runs parallel to
Phase 2 (different files); Phase 4 depends on 1+2; Phase 5 gates everything. Phase 0 is
dependency-free — start immediately, fully parallel.

**PHASE 0 — HOTFIX BAND (parallel, dependency-free, days).**
Lane 0a: env/auth — R-15/O-6 DATABASE_URL; R-16/O-5 callPlatformPrimitive 401 (1-line).
Lane 0b: schema-drift dead tools — R-9, R-10, R-12, R-14, T-7; V-8 offset pagination; P-6 D9 sign filter.
Lane 0c: Y-1 kill vacuous pass (+Y-7 stamp, +Y-9 exclusions) — stop serving fabricated yogas.
Lane 0d: lifetime clips — T-5, T-9 pre-birth anchors/parvas.
Lane 0e: V-1 chart_dashas lord_natal_* rebuild from chart_facts (+G-7, D-1, V-11) + CI equality gate.
Lane 0f: M-7/M-8 kill native-fallback contamination (hard-fail pattern) — SAFETY-critical, tiny diff.

**PHASE 1 — COMPUTATION TRUTH (the M/V estate; parallel by writer; sequential prerequisite for
Phases 2/4).** Doctrine: PyJHora-is-the-engine — delegation over reimplementation.
Lane 1a ga_strength: M-1 shadbala→PyJHora, M-2 vimshopaka, M-3 shodhana/pinda (fixes V-2/V-3/V-4).
Lane 1b ga_vargas: M-4 BAV loop, M-17 D60 deities, M-18 saptavargaja.
Lane 1c ga_dashas: M-5 mudda, M-6 kalachakra, M-21 solar return, V-9 boundary timestamps, V-12
  dasha_system separation (kp_sub vs vimshottari).
Lane 1d ga_sensitive: M-9 fabricated sphutas (delete/floor), M-10 special lagnas, M-11/V-6/V-7
  upagrahas, M-16 arudha exception (+D-9 MC, D-10 arudha longitudes).
Lane 1e ga_structural/condition: M-12 tajika aspects, M-14 composite strength, M-15 yuddha
  latitude, M-19 combustion orbs, M-20 sade-sati D9, V-5 Saturn drishti; M-13 ga_tajaka orbs.
Lane 1f cross-cutting: M-22 verification-stamp reform (verifier owns the column; CI literal ban);
  D-3 composite classification (needed by Phase 2A).
EXIT GATE: TAP-3b recompute battery green on derived values; distinctness gates pass; rebuild L1
for both charts.

**PHASE 2 — COMPOSITION (three parallel streams after Phase 1).**
2A Yoga & cancellation: Y-2 wire ga_yoga_firings, Y-3 NBRY per-varga, Y-4+Y-8 house-lord family,
  Y-5 cancellation class, Y-6 feed bhanga (consumes D-3 fixed), Y-11 real constituents, Y-12+P-11
  verdict-from-full-count (absence-of-row ≠ negative), K-4 sannyasa.
2B KP: KP-2 retire fake category → KP-1 Placidus → KP-3 significator ladder → KP-4 domain tags →
  KP-5 KP lens in judgment. Witness: legacy parity (FORENSIC v6.0 §4).
2C CGM graph: G-1 lordship/occupancy edges → G-2 real strengths+domains (uses Phase-1 virupa),
  SC-6 sade_sati edges, SC-7 parivartana edges, SC-8 karaka/KP/Jaimini edges, G-3/G-4 traversal,
  G-6 chain signals, D-17/D-18 (derived fixes). Witness: Mars+Rahu+Mercury→11H chain surfaces.

**PHASE 3 — SERVING INTEGRITY (parallel to Phase 2; TS estate).**
3a Parameter/routing conformance: R-18 sweep + R-17 facets + SC-20/SC-21 alias parity + R-6.
3b Budgets estate-wide: R-1/R-8 + T-6 dedup + R-24 grounding + R-25/R-26/KP-6 shapes.
3c Serve the computed-but-hidden: S-1 special-states join, S-2/S-3, S-12 divisionals, SC-1..SC-5,
  SC-11..SC-13 (epistemic cols → fixes R-2 with real data), SC-22 calibration outputs, S-14, S-15.
3d Domain/attribution truth: SC-10 _DOMAIN_MAP full pass + P-2 career-tag collapse + D-5
  attribution + P-5 flag-signal ranking + P-7 strength semantics + P-8 parivartana narration.
3e Honesty pass: S-8/S-11/R-28 descriptions; R-21 receipts; R-22 pact_status; R-5 denial envelope;
  SC-17/SC-18/SC-19 pointer validity (boot-time check).
3f Lateral judgment: G-5+P-4 shastra map (bhavas 2+11 wealth, 9H+Sun father, relational karakas),
  P-10 bhava-bala join, P-3 D1↔D9 synthesizer, P-9 Sade Sati serving, C-4 muhurta panchanga rules.

**PHASE 4 — PREDICTION INFRA (after Phases 1-2; the Beyond-Acharya spine).**
T-1 sidecar revival → T-4 kala_activation build → T-12 multi-cycle anchors + D-16 adverse valence
(consumes 2A dosha/bhanga) → P-1 pact ACTIVATION rebuild (running-MD input; consumes V-12) → T-3
as_of plumbing → T-13/T-14 timing-basis + single-score → T-8 live citations → T-11 LEL intake
(+LEL Ketu erratum) → C-5 calibration wiring → SC-14 read the Promise Register (bo_pratijna/
ka_avadhi/ka_taranga become the serving substrate) → K-1..K-3/K-5..K-7 concept tail.

**PHASE 5 — VERIFICATION HARNESS (gates the campaign; build alongside, enforce at exits).**
TAP CI suite: the 7 seam-conservation checks (TAP-5 spec), TAP-6 grep set, TAP-7 8 gates, S-13
live coverage matrix. Golden battery (§11.5): 22 golds → PASS ≥18, 0 FAIL. Adversarial battery:
≥6 A, 0 D. Blinded retrodiction re-run (Section 10): all 8 metrics move, genuine hit preserved.
Register rows close ONLY with [verify-against: prod] evidence.

---

## PRIORITIZATION FOR R6 (v2 wave plan — SUPERSEDED by the phased plan above; retained as record)

**HOTFIX BAND (days — stop serving wrong astrology + revive dead infra):**
1. Y-1 kill the vacuous pass (with Y-9 exclusion handling; Y-7 verification stamp fix rides along).
2. O-5/R-16 callPlatformPrimitive 401 (1-line, unblocks 3 tools) + R-15/O-6 DATABASE_URL (env var, unblocks 12).
3. R-9/R-10/R-12/R-14 schema-drift dead tools (column renames; hours each) + T-7 muhurta_finder.
4. T-5 pre-birth anchors + T-9 pre-birth parvas (clip to lifetime — actively absurd output).

**R6 WAVE A — Yoga & Cancellation core (the heart):**
Y-2 wire ga_yoga_firings → retire the label surface; Y-3 NBRY all 5 rules per-varga; Y-4+Y-8 house-lord
family (implement stubs OR de-skip-list); Y-5 generic cancellation evaluator; Y-6 feed bhanga into
salience + D9 cross-check — but ONLY after D-3 (composite classification correctness) is fixed, else
Y-6 wires in wrong data; Y-11 real constituent grounding; Y-12 verdict-from-full-count.

**R6 WAVE A′ — CGM chain integrity (new v2.2; runs beside Wave A, same substrate):**
G-1 graha→bhava lordship/occupancy edges (unblocks ALL house chains — the single highest-leverage
graph fix); G-2 real edge strengths + domain routing; G-4 traversal honesty; G-3 resolver keys;
then G-5 judgment lateral join + G-6 chain-signal class; G-7 rides with D-1 (dasha denorm rebuild);
G-8 rides with the L1 karaka_web touch. **Acceptance witness: the Mercury→Saturn(11L)→11H +
Mars→Rahu(2H) financial-fluidity chain must surface in a wealth/bhava-11 judgment query with
constituent fact_ids — L1 already grounds every atom of it.**

**R6 WAVE A″ — KP integrity (new v2.3; the legacy portal's headline capability, currently absent):**
KP-2 retire/rebuild the fabricated significator category (authority split — do first); KP-1 Placidus
cusps into the existing correct compute_kp_lords; KP-3 the 4-level significator ladder + node agency;
KP-4 domain tags; KP-5 KP lens in judgment; KP-6 pivot subject-collision (rides with R-23/R-24 in
Wave B). **Acceptance witness: a wealth query on 482012f1 must surface KP.CUSP.11 = Mars(star)/
Mercury(sub) with Rahu agency from 2H as the cash-flow channel and Saturn (10L+11L, exalted) as the
earning channel, matching FORENSIC v6.0 §4 — the legacy baseline the native remembers.**

**R6 WAVE B — Serving integrity (the estate-wide sweep, not per-tool patches):**
R-18 alias→primitive parameter conformance sweep + O-7 smoke battery in CI; R-1/R-8 budget everywhere;
R-17 facet map; R-19/R-20 remedies + ref stubs; S-1 special-states join (one helper, highest value/effort);
S-2/S-3/S-12 serve the computed-but-hidden (divisionals foremost); S-13 coverage-matrix gate becomes live-derived
(converts the whole S-family into CI failures); S-11/R-28 honesty pass on descriptions; R-21/R-22 receipt
integrity; S-15 serve the stored percentile.

**R6 WAVE C — Prediction infra (what separates reading from predicting):**
T-1 ephemeris/transit sidecar (unlocks TRIGGER + K-7); T-4 build the empty kala_activation layer;
T-12 multi-cycle anchor generation over the restored substrate (+D-16 adverse-valence claims,
T-13 timing-basis rule, T-14 single scored source); T-3 as_of plumbing (pact→judgment→get_dashas,
timezone + boundary semantics); T-11 LEL intake (open-circuits calibration + C-5 until done);
T-6/T-10 anchor dedup + distribution gates; T-8 live MD/AD citations. **Wave-C exit gate: re-run
the Section-10 blinded accuracy test; all eight baseline metrics must move, and the recorded
genuine hit must not regress.**

**R6 WAVE D — Data correctness + concept tail:**
D-1 dasha lord nakshatra; D-2 sade-sati cycles; D-3 composite classification (pulled earlier if Wave A
needs it); D-4 shunya rashis; D-5 entity attribution; D-6/D-7 degenerate distributions; K-1..K-6 concept
misses in significance order (conditional dashas, kuta service, SBC service, sannyasa, sandhi flags, tattva).

**Fold-in:** R5.3 continues C-1/C-2/C-3; C-4 batches with muhurta work in Wave C.

**Bottom line (v2):** v1's diagnosis holds and deepens. The substrate is genuinely acharya-grade in
concept coverage (~90% of canon, over-coverage in several axes) and the FORENSIC ground truth reproduces
perfectly — but the instrument a user actually touches is gated by: a yoga surface that fabricates, a
serving layer where ~⅓ of tools are dead, mis-routed, unbounded, or ignore their parameters, an empty
activation/LEL layer that open-circuits both dated prediction and calibration, and a set of degenerate
distributions that per-row checks can't see. Fix the hotfix band + Wave A + S-1 + T-1/T-4 and the
instrument crosses from "reads facts, fabricates yogas, stops before the trigger" to "reads facts,
detects yogas honestly with cancellations, and predicts to the transit."

## SECTION 12 — LLM CONSUMPTION AUDIT findings (wave 1, 2026-07-12)

Findings filed during the LLM Consumption Audit execution (plan `LLM_CONSUMPTION_AUDIT_PLAN_v1_0`,
charter `LLM_CONSUMPTION_AUDIT_CHARTER`). Deduped against R-37..R-48 + all prior rows. Per finding
discipline (charter §3 / plan §6), discoveries are filed as found, not held for their lane.

| ID | Description | Gap type | Severity | Evidence/Source | Fix | Status |
|---|---|---|---|---|---|---|
| LCA-1 | **45% of the surgical MCP retrieval surface is DEAD — 19 of 42 whitelisted tools 500 on every call (advertised but unresolvable at the registry seam)** — `MCP_TO_RETRIEVAL_TOOL` (tool_name_bridge.ts) whitelists these on `/api/mcp/primitives/[tool]`, but their retrieval-tool targets are absent from `TOOL_NAME_TO_URI`, so `getToolByName` returns undefined and every call yields `{ok:false, error.class:'internal', message:"Retrieval tool not found in registry: <tool>"}`. Dead set (verified live for temporal/cgm_graph_walk/kp_query/query_ucn_walk; static-derived for the rest, method validated at 100% on the live sample): **cgm_graph_walk, cluster_atlas, contradiction_register, jaimini_chara_dasha, jaimini_chara_dasha_full, kp_query, multi_school_signal_lookup, pattern_register, query_cdlm_lookup, query_chandra_balam, query_jaimini_drishti, query_kp_ruling_planets, query_rm_walk, query_signal_state, query_tara_balam, query_ucn_walk, resonance_register, temporal, timeline_query.** This is the plan's predicted "fails on first contact" base-rate, quantified at the whitelist/registry seam. Consumer impact spans KP (kp_query, query_kp_ruling_planets), Jaimini (chara_dasha, drishti), graph (cgm_graph_walk → **directly disables Lane 9a's graph-consumption path**), CDLM/RM/UCN walks, cross-school, cluster/pattern/resonance/contradiction registers, tara/chandra balam, and temporal. Alive tools confirmed working: chart_facts_query, query_dasha_periods (+21 others resolve). | SURF | **CRITICAL** | [audit 2026-07-12] live POST `/api/mcp/primitives/{temporal,cgm_graph_walk,kp_query,query_ucn_walk}` → `Retrieval tool not found in registry: <tool>` (4/4 dead as predicted); `query_dasha_periods`/`query_chart_facts` → ok:true (alive control); static diff `MCP_TO_RETRIEVAL_TOOL` values ∖ `TOOL_NAME_TO_URI` keys = 19 | Add a build/startup invariant that every `MCP_TO_RETRIEVAL_TOOL` value resolves via `getToolByName`/`TOOL_NAME_TO_URI` (fail CI otherwise); register the 19 missing URIs or remove the dead whitelist entries; until fixed, the MCP surgical surface advertises ~45% more capability than it can serve | REMEDIATED-PENDING-W4 [WP-1.7 / W1; 19 dead whitelist entries resolved (5 registered + 14 removed) + permanent CI whitelist-resolution invariant (fails CI on any unresolvable entry); deployed 2385fb62/fc84cd0d, 7/7 prod-verified 2026-07-13] |
| LCA-2 | **Consume consult pipeline (the product's flagship serving surface) hard-fails for EVERY chart on a nonexistent relation, mislabeled as a transient DB outage — confirmed against the DEPLOYED database.** `platform/src/app/api/chat/consult/route.ts` **line 300** unconditionally runs `SELECT domain, title, version FROM reports WHERE chart_id=$1` inside a `Promise.all` (lines 290–303); relation `public.reports` does not exist in the **deployed** Cloud SQL (`madhav-astrology:asia-south1:amjis-postgres`, reached via the cloud-sql-proxy on 127.0.0.1:5433 that the app itself uses) — DDL survives ONLY in retired `platform/migrations/_archive/001_initial_schema.sql`; NO `CREATE TABLE reports` in canonical `platform/supabase/migrations/`. The query throws, the `catch` (L304-305) maps it to `res.dbError()` → `SYSTEM_DB_UNAVAILABLE {retry:true}`. The failure is **chart-independent** (missing relation, not a per-chart filter), so it reproduces identically for **both audit charts** — native `482012f1` (reproduced live via consult, 3×) and Abhinandan `1c826d5a` (same code path, same missing relation). Two defects: (a) the full-pipeline consult surface **cannot serve ANY chart** — the product's own primary consumption path is dead against the real deployed schema; (b) a permanent missing-relation error is dishonestly reported to the consumer as "Database temporarily unavailable / retry:true" (class 5 DISHONEST SELF-DESCRIPTION). | LOGIC+SURF | **CRITICAL** | [audit 2026-07-12] live `POST /api/chat/consult` (valid Firebase super_admin session), chart 482012f1 → `{"error":{"code":"SYSTEM_DB_UNAVAILABLE","retry":true}}` (3 attempts); `mcp__postgres__query` `SELECT domain,title,version FROM reports WHERE chart_id='…'` → verbatim `relation "reports" does not exist` (both chart_ids; error is chart-independent); deployed-DB confirmed via cloud-sql-proxy target; schema-parity pass (no canonical CREATE). E-7c(i). | Decide canonical intent for `reports` (retired vs. restore); if retired, make the consult lookup optional/null-safe so a missing optional table cannot dead-end the pipeline; separately, stop mapping permanent missing-relation/syntax errors to the transient `SYSTEM_DB_UNAVAILABLE/retry` class. **NOTE:** not fixed this audit (findings-only; E-7c re-routes the pipeline lanes to the MCP wire rather than patching the audited path). | REMEDIATED-PENDING-W4 [WP-1.1 / W1; consult re-pointed off retired `reports` table → live retrieval surfaces + honest permanent-vs-transient error mapping (42*/3F*→500 non-retry, 57/40/08→503 retry); deployed amjis-web 2385fb62 + amjis-mcp fc84cd0d; blind-verified (0 live `FROM reports`, chart-distinct content) + 7/7 prod-verified 2026-07-13] |

### Lane 9b — L1→MSR ingestion matrix (204 fact_categories, both charts; 2026-07-12)

Swarm audit (204/204 categories) + verifier swarm (29.4% coverage, blind re-execution) + conductor
E-5 live retest of headline findings. 283 total findings; full substrate in
`00_ARCHITECTURE/llm_consumption_audit/state/LANE9.md` + `state/LANE9/shard-9b-*.md`. Verdict spread:
42 SOUND / 149 WEAK / 5 BROKEN / 8 NOT_CONSUMED. Confirmed CRITICAL/HIGH + blind anchor rediscoveries:

| ID | Description | Gap type | Severity | Evidence/Source | Fix | Status |
|---|---|---|---|---|---|---|
| LCA-9b-1 | **`aspect_jaimini_per_varga` floods MSR with 15,660 signals/chart, all identical in salience/type/domain — a 15.6k-row indistinguishable wall that makes any genuine signal un-findable** — 1:1 fact→signal ingestion with zero salience differentiation; the funnel floods instead of narrowing | SURF (DROWNED) | **CRITICAL** | [audit+E-5 retest 2026-07-12] cell1=15660 both charts (conductor-confirmed); cell2 supporting=15660; cell5 composite_state=15660; cell4 single value all rows | bo_laksana must not 1:1-emit per-varga aspect facts as flat signals; aggregate/rank or tier them; cap divisional-aspect signal emission | OPEN |
| LCA-9b-2 | **Per-varga / granular salience inflation across a family of categories — divisional and low-decision-weight data promoted to `major`/`chart_defining`, burying genuine chart-defining findings (R-44b anchor RE-DERIVED blind)** — `aspect_parashari_per_varga` (chart_defining=229, major=1317, Abhisek), `ashtakavarga_bindu_per_varga` (major=281/207), `ashtakavarga_pinda_sarva_per_varga` (major=219/165), `bhava_significance_link` (5220 co-tied supporting), `contradiction_pair` (1740 co-tied supporting) | SURF (DROWNED) | HIGH | [audit 2026-07-12] cell2 tier counts per category (verbatim in shard traces); CHARTER §7.4 rationale (an acharya weights a handful of divisional aspects as chart-defining, not thousands) | Re-tier salience so divisional/granular facts cannot occupy `major`/`chart_defining`; demote per-varga aspect + ashtakavarga bindu from top salience candidacy | OPEN |
| LCA-9b-3 | **KP cusp-lord signals uniformly domain-mapped to `character\|relationship` (never wealth) — KP wealth significators (2nd/11th cusps) can never surface under a wealth-domain query (KP-4 anchor RE-DERIVED blind)** — only ~37% of 240 cusp_kp_lords facts consumed | LOGIC (WRONG domain map) | HIGH | [audit 2026-07-12] cell4=`character\|relationship` on all 87–89 consumed signals both charts; cell1 87–89 of 240 chart_facts | Fix domain mapping so KP cuspal significators inherit the house's domain (2nd/11th→wealth); ingest the un-consumed 63% | OPEN |
| LCA-9b-4 | **8 fact_categories entirely un-ingested by bo_laksana — chart_facts rows exist but 0 MSR signals resolve to them (funnel-narrowing / class-1 omission), including the two MOST chart-defining structures in Jyotish** — `dosha_label` (220 facts, 0 signals — E-5 confirmed), `yoga_label` (75 facts, 0 — E-5 confirmed), `vimsopaka_bala_per_graha` (0 — E-5 confirmed), `tara_bala`, `nakshatra_dispositor_chain`, `nakshatra_lord_relationship`, `nakshatra_co_tenancy`, `graha_saptavargaja_bala_component` | DATA→SURF (omission) | HIGH | [audit+E-5 retest 2026-07-12] 5-cell recipe returned [] for each; chart_facts denominators non-zero (dosha_label=220, yoga_label=75) | bo_laksana ingestion-selection must include yoga/dosha LABEL categories + nakshatra dispositor/relationship chains; confirm yoga/dosha names reach consumers (may partially route via yoga/dosha-typed signals — cross-check) | OPEN |
| LCA-9b-5 | **All 220 `signal_type_class=dosha` signals cite only 10 distinct constituent fact_ids (22× reuse), and those fact_ids do not resolve to any `chart_facts.fact_id` — R-42 anchor RE-DERIVED blind + a referential-integrity break violating CLAUDE.md §N.5** | LOGIC (attribution collapse) | HIGH | [audit+E-5 retest 2026-07-12] distinct constituent fids=10, dosha signals total=220 (conductor-confirmed); 0/10 resolve to chart_facts.fact_id | Fix dosha signal attribution to cite the real per-dosha constituent facts; add a referential-integrity verifier (constituent_facts_array entries MUST resolve to chart_facts.fact_id per §N.5) | OPEN |

| LCA-3 | **`query_chart_facts` (the primary chart-facts retrieval tool) silently ignores its `fact_category` filter and returns the entire ~119KB pivoted dump on every call — silent parameter no-op + un-budgeted payload (R-44c class)** — a consuming LLM that scopes its query to one category to stay in budget receives the full 119KB fact dump with no signal the filter was dropped; even an invalid category returns 119KB instead of an error/empty | SURF (silent no-op + un-budgeted dump) | HIGH | [audit 2026-07-12] live POST `/api/mcp/primitives/query_chart_facts` fact_category ∈ {lagna, bhava_bala_lord, dosha_label, nonexistent_category_xyz} → response_bytes = 119492 / 119502 / 119498 / 119511 (all ≈ identical; identical `abhukta_mula_dosha`-first payload head across distinct filters) | Make `fact_category` actually filter server-side (or drop it from the schema if unsupported); validate unknown categories → empty/error not full dump; bound/paginate the payload with a disclosed cap + `more_available` flag (R-44c remediation) | REMEDIATED-PENDING-W4 [WP-1.3(f) / W1; fact_category/fact_subject filters genuinely filter (proven by byte-size deltas) + disclosed pagination with real totals; deployed 2385fb62/fc84cd0d, 7/7 prod-verified 2026-07-13] |

| LCA-9a-1 | **The CGM graph is graha-to-graha only — all 60 bhava nodes are fully ORPHANED (0 edges), no yoga is a first-class node, and no edge carries a temporal hook; the "one of the strongest assets" reaches none of the context a synthesis needs** — 42/42 sampled nodes (both charts): 0 COMPLETE, 18 THIN (grahas, reach only other grahas), 24 ISOLATED (all bhavas). No node reaches bhava-lordship (0/42), yoga membership (0/42 — `bodha_cgm_nodes` has no `node_type='yoga'`), or temporal hook (0/42 — `active_dasha_periods_jsonb` never populated on edges, same failure class as R-45). Directly fails the plan's own Mercury probe (reaches dispositor YES, bhava-lords NO, yogas NO, temporal NO). Combined with consumption (dead `cgm_graph_walk`, LCA-1) and leverage (dead consult, LCA-2): the graph is a **parked, partial database** — structurally crippled, unconsumable, unleveraged. | DATA (graph wiring) | **CRITICAL** | [audit+verify 2026-07-12, 21.4% verifier cov] recipe: bhava nodes edge_count=0 (60/60); graha nodes reach `neighbor_types='graha'` only (Jupiter 26 edges, Mercury 23, all graha-only); temporal populated 0/26 on all sampled; census bhava 60/0-edged vs graha 45/45=1031 edges. Deliverable: state/LANE9.md 9a section + shard-9a-*.md | Wire graha↔bhava (lordship/occupancy/aspect) edges; make yogas first-class graph nodes (or edges); populate edge temporal windows (shares the R-45 activation-date fix); then re-enable a graph-consumption tool (fix LCA-1 cgm_graph_walk) | OPEN |

*(R-44a — 298/300 UNATTRIBUTED — partially surfaced here via the LCA-9b-5 referential break; full ratio
re-derivation belongs to the orientation/domain-reading ranked surface, Lane 6. 149 WEAK categories +
the remaining 278 findings are itemized in the shard-trace substrate, feeding the machine-readable
findings JSON at consolidation.)*

### Fused Lane 1b + Lane 5 — Concept×Retrievability + wire-fidelity matrix (3,058 families / 134 paths; 2026-07-12)

Path-sampled per-channel audit (E-8 schema). 3,058/3,058 per-family rows; channels: **1,384 reachable-surgical · 1,402 served-only-by-down-pipeline (remediation quick-win) · 157 truly-UNREACHABLE · 115 mixed.** 152 findings (133 Lane 1b + 19 Lane 5), verifier 17.2%. Full matrix in `state/LANE1b.md` + `state/LANE5.md` + `state/FUSED_1b5/shard-*.md`. Distinct classes:

| ID | Description | Gap type | Severity | Evidence/Source | Fix | Status |
|---|---|---|---|---|---|---|
| LCA-3-EXT | **`query_chart_facts` is worse than LCA-3 first showed — a hard cap of 1000 pivoted subjects of 5,566 (~82% silently discarded, no `total`/`more_available` disclosure, alpha-sort drop) AND only 1 of 6 ayanamshas (`lahiri_chitrapaksha`) served** — on top of the confirmed `fact_category`/`fact_subject` param no-op | SURF (budget-ceiling + no-op) | HIGH | [audit 2026-07-12] limit=3000→returned 1000 (hard cap); DB=5566 distinct subjects lahiri; default limit=100; no total in payload | Disclosed pagination + `more_available`; serve all ayanamshas; honor filter params (see LCA-3) | REMEDIATED-PENDING-W4 [WP-1.3(f) / W1; all 6 ayanamshas served + disclosed pagination over the 5,566 subjects (real total + more_available, no silent 82% drop); deployed 2385fb62/fc84cd0d, 7/7 prod-verified 2026-07-13] |
| LCA-4 | **The entire dated-prediction + calibration + remedy + graph substrate is UNREACHABLE over the only working wire channel — ~1,402 families "served-only-by-down-pipeline" (data + serving code exist; only the dead surgical tools + broken consult block them)** — includes ALL `kala_*` (activation, taranga ~80k rows/chart, convergence, bhavishya, avadhi, darshana, obstruction, jivana_parva), ALL `mimamsa_*` (predictions, multipliers, manifestation_grammar/sets, signal_adjustment ~66.8k rows/chart), `phala_*` (anchors, mitigation, phaladesa), and populated `bodha_*` (cgm_edges 1057, cgm_paths 45, anomalies 3978/2350, discoveries 2392/1150, pratijna 110, question_lenses, rm_resonances 45, triangulation 95) — the direct, quantified realization of the native's "data exists but is not retrieved" concern | SURF (retrieval) | **CRITICAL** | [audit 2026-07-12] per-table DB counts + dead-tool curl confirmations across 1,402 families (state/FUSED_1b5 shards) | Revive the DEAD-19 surgical tools (LCA-1) and/or repair consult (LCA-2) — this is the single highest-leverage retrieval fix; post-remediation re-audit re-grades exactly this class | REMEDIATED-PENDING-W4 (serving/reachability half) [WP-1.3(a,j) + WP-1.6 / W1; computed-but-unserved kala_*/mimamsa_*/phala_*/bodha_* assets now served + reachability +316 (2,024→2,289); deployed 2385fb62/fc84cd0d, 7/7 prod-verified 2026-07-13. Residual data-plane (empty shells LCA-5, cgm_motifs LCA-6, R-45 NULL dates) → W2] |
| LCA-5 | **Empty-shell analysis stages — computed-nothing across ALL charts (data plane never populated)** — `bodha_cdlm_domain_rollups` (0), `bodha_cdlm_evolution_gradients` (0), `bodha_cdlm_pattern_clusters` (0), `bodha_cgm_chart_topology_summary` (0), `bodha_cgm_sub_graphs` (0), `bodha_contradictions` (0), `bodha_rm_chart_summary`/`bodha_rm_dasha_windowed_prescriptions`/`bodha_rm_dosha_remedy_bundles`/`bodha_rm_pattern_remedies` (0), `phala_phaladesa.narration_jsonb` (NULL, status=pending, all rows) | DATA (never computed) | **CRITICAL** | [audit 2026-07-12] `SELECT count(*)`=0 both charts per table (verbatim in shards); contradiction engine + CDLM rollup/gradient/cluster + CGM topology/subgraph + RM summary/bundle writers emitted nothing | Root-cause each writer (did it run? did it no-op?); these open-circuit contradiction detection, CDLM evolution, CGM clustering, and remedy bundling | OPEN |
| LCA-6 | **The canonical native chart `482012f1` has 0 `bodha_cgm_motifs` — WRITER DEFECT, not a build-order artifact; SURVIVES REBUILD** — only Abhinandan `1c826d5a` populated (6 motifs). Build-order check (rider 2): the native's CGM build `13d205ff` (2026-07-11 16:47) ran ~1h AFTER Abhinandan's `e0c34a9f` (15:45), same pipeline; the native build produced cgm_nodes (140) + cgm_edges (534) but the motif stage emitted 0 rows, while Abhinandan's same-pipeline build produced all three incl. 6 motifs. So the writer existed and ran for the native — it silently produced zero motifs. The native's chart is documented to hold chain configurations (register CGM/G-2 Mars+Rahu+Mercury→11H), so 0 motifs is near-certainly a defect, not a true absence. | DATA (writer defect, chart-specific) | HIGH | [audit 2026-07-12] motif `count(*)`=6 (Abhisek 0/Abhinandan 6); build_ids: native cgm_nodes/edges build 13d205ff@16:47 present but 0 motifs; Abhinandan e0c34a9f@15:45 has nodes+edges+motifs | Fix the motif writer (a rebuild alone won't help — the 16:47 rebuild already produced 0); debug why the native chart's parivartana/stellium detection emits nothing despite known chains | OPEN |
| LCA-7 | **`msr_sql` silently ignores its `sql` param (fixed 17-field projection drops ~83 of 115 columns) and returns top-50 of 13,364 matching signals while reporting `truncated=False`** — silent parameter no-op + dishonest truncation flag on the primary MSR retrieval tool | SURF (no-op + dishonest) | HIGH | [audit 2026-07-12] msr_sql call: fixed 17 fields returned regardless of `sql`; returned_count 50 of 13,364 (66,836 DB rows), `truncated:False` | Honor the `sql`/projection param; report true `truncated`/`total` | REMEDIATED-PENDING-W4 [WP-1.3(g) / W1; msr_sql projection param honored (omit=17 / `*`=82 real cols / explicit list, static-whitelist injection-safe) + honest truncated/total; deployed 2385fb62/fc84cd0d, 7/7 prod-verified 2026-07-13] |
| LCA-8 | **`list_entities` silently drops 552 of 652 `brahma_ontology` rows — whole entity_classes (dosha, yoga, karaka, planet, sign, house) never surface** | SURF (budget-ceiling) | HIGH | [audit 2026-07-12] list_entities returned 100 of 652; missing entity_classes enumerated | Paginate/disclose; ensure entity_class coverage | REMEDIATED-PENDING-W4 [WP-1.5 / W1; list_entities serves real 652 total + cursor (was masking 552); deployed 2385fb62/fc84cd0d, 7/7 prod-verified 2026-07-13. Follow-up: next_cursor disclosure-honest but not yet round-trip-consumable (no cursor input param)] |

*(All 152 fused findings itemized in the shard substrate; the per-family Concept×Retrievability matrix (3,058 rows, per-channel) is the machine-readable deliverable for consolidation. `bodha_msr_signals` path was heterogeneity-escalated to full per-family audit per green-light condition 2.)*

### Lane 8 — Entity-dossier depth audit (the Mercury standard; 20 dossiers = 10 entities × 2 charts, 150 facets; 2026-07-12)

Facet-in-context, consuming the Concept×Retrievability matrix (shaper #3). **1 SYNTHESIZABLE (Jupiter/Abhinandan) · 19 PARTIAL · 0 UNCOMPOSABLE**, avg composability **73.5%**, **114 held-but-not-received facets**, 140 findings (36 HIGH/CRIT), verifier 20% (0 disagreements). Full matrices in `state/LANE8.md` + `state/LANE8/shard-*.md`. Cost 2.36M.

| ID | Description | Gap type | Severity | Evidence/Source | Fix | Status |
|---|---|---|---|---|---|---|
| LCA-9 | **The depth axis confirms the width axis — NOT ONE of the 20 entity dossiers is fully synthesizable over the surgical wire (19/20 PARTIAL, avg 73.5%); the system HOLDS the deep data but cannot deliver it** — the held-but-not-received facets cluster on exactly the acharya-decisive groups: structural×temporal convergence (R-45 asset — held-but-not-received in **ALL 20** dossiers), yoga participation (facet 41, `bodha_msr_signals` 83/115 families down-pipeline), dosha participation (facet 42), remedial mapping (facet 56) — all `served-only-by-down-pipeline`. Even Mercury (the doctrine's own exemplar) composes to only ~63% on Abhinandan. | SURF (retrieval, depth) | **CRITICAL** | [audit 2026-07-12, verifier 20%/0-disagree] 20 dossiers, 114 held-but-not-received facets; kala_convergence (6,484 rows/chart) + bodha_msr yoga/dosha families all served-only-by-down-pipeline per matrix | Same fix as LCA-4 (revive dead tools / repair consult) is what raises dossier depth from PARTIAL→SYNTHESIZABLE; this is the depth-axis quantification of that quick-win | OPEN |
| LCA-10 | **Sensitive-degree concepts NEVER computed (data-plane nonexistence) — R-47 anchor RE-DERIVED blind and extended** — for Venus (spot-checked entity): mrityu-bhaga (R-47), neecha-bhanga, kartari, Sarvatobhadra vedha, 22nd-drekkana/64th-navamsa (khareshwara), pushkara-bhaga/navamsa, declination/kranti/shara — 7 canonical facets with 0 rows in `chart_facts`; not a retrieval gap but a compute gap (the classical canon calls for them; the system never computed them — plan §2.1 UNREACHABLE-by-nonexistence) | DATA (never computed) | HIGH | [audit 2026-07-12] chart_facts `%mrityu_bhaga%`=0, neecha=0, kartari=0, vedha/sarvatobhadra=0, drekkana/khareshwara/64navamsa=0, pushkara=0, kranti/declination=0 | New L1 categories per R-47 fix (sensitive_degree_check per graha × sign); this is the data-plane half that no serving fix can reach | OPEN |

*(R-45 was independently re-confirmed by all 20 Lane-8 dossiers — deduped against the existing re-attributed R-45 row, not new rows. The 104 remaining Lane-8 findings (per-facet held-but-not-received instances) live in the shard substrate for the consolidation findings JSON.)*

### Wire lanes — 1a tool census + 4 receipt honesty (fused) + 1c services + 3 cross-path (2026-07-12)

Surgical + :8000 harness. 1a+4: 127 tools probed. 1c: 30 services. Lane 3: 6 distinct quantities (from 234 rows). Deliverables: `state/LANE1a.md`, `LANE4.md`, `LANE1c.md`, `LANE3.md`. Blind rediscovery: **R-43** (dignity/shadbala). Cost ~1.6M (vs ~4M proj).

| ID | Description | Gap type | Severity | Evidence/Source | Fix | Status |
|---|---|---|---|---|---|---|
| LCA-11 | **Only 17 of 127 MCP tools are reachable over the surgical wire (109 full-pipeline-only behind broken consult + 1 dead); of the 17 reachable, only 7 PASS first-contact synthesizability (5 PARTIAL, 6 FAIL)** — and the highest-value domain-verdict surfaces (`apex_{career,health,marriage,wealth}_assess` + their duplicate `assess_*` twins — a class-3 dedup smell, two tool families for the same 4 domains) are ALL full-pipeline-only, as are the B.11 whole-chart entry (`bodha_chart_digest_get`), the graph tools, and the system's own asset-inventory surfaces (`catalog_assets_*`, `asset_registry_*`) | SURF (retrieval) | HIGH | [audit+verify 2026-07-12, 1a4-verify 19/0] tools.jsonl 127 probed; channel {17 surgical, 109 down-pipeline, 1 dead}; synth {7 PASS, 5 PARTIAL, 6 FAIL, 109 not-probed} | Expand the surgical whitelist to the high-value read tools, or repair consult (LCA-2); dedupe apex_*/assess_* | REMEDIATED-PENDING-W4 [WP-1.3(i) + WP-1.1 / W1; apex_*/assess_* deduped (params restored, lord-bucket parivartana 0→42, starvation fixed) + consult repaired (LCA-2); deployed 2385fb62/fc84cd0d, 7/7 prod-verified 2026-07-13] |
| LCA-12 | **The system's own tool-help text advertises 17 of the 19 DEAD-19 tools as live "Surgical primitives"** — every rejection remediation string enumerates dead tools (`query_tara_balam, jaimini_chara_dasha, temporal, kp_query, pattern_register, resonance_register, cluster_atlas, contradiction_register, query_ucn_walk, query_cdlm_lookup, query_rm_walk, …`); a consumer following the help gets "Retrieval tool not found in registry" | DOC (dishonest self-description) | MED | [audit 2026-07-12] verbatim remediation string lists 17 LCA-1 dead tools as surgical primitives | Regenerate the help text from the live registry (only resolvable tools); same root as LCA-1 (whitelist/registry drift) | REMEDIATED-PENDING-W4 [WP-1.3(h) / W1; help/capabilities no longer advertise dead tools (cross_school/multi_school → PARKED/Degraded), phantom decls (kp_query/query_kp_ruling_planets/timeline_query) dropped; deployed 2385fb62/fc84cd0d, 7/7 prod-verified 2026-07-13] |
| LCA-13 | **The :8000 compute-on-demand layer is partially broken — 17 of 30 services unreachable, and several "reachable" ones are DEGRADED or dishonest** — `query_transit_event` MCP returns ok:true but the sidecar 401s (`Invalid API key`) → 0 data; `query_ephemeris` reports `ok:true / confidence_band:high / no warnings` while returning nothing (dishonest); `/api/pyhora/compute` → `PyJHora not available: No module named jhora`; `/brahmagyan/ephemeris/planet_position` → `DATABASE_URL not set`; arbitrary-date planetary longitude unreachable | INFRA + SURF | HIGH | [audit+verify 2026-07-12, 1c-verify: 3 genuinely alive (varshaphal, ashtottari/kalachakra dasha), 1 degraded, 2 DEAD-19, 1 stub] service payloads quoted | Fix sidecar API key, install `jhora`, set DATABASE_URL for the ephemeris service; make ephemeris report honest confidence when empty | REMEDIATED-PENDING-W4 [WP-1.7 / W1; jhora venv-provisioned + api-key wired + ephemeris honesty (empty→ok:false/confidence:none) + port 8001→8000; deployed 2385fb62/fc84cd0d, 7/7 prod-verified 2026-07-13. Residual: DATABASE_URL local-Postgres bench documented follow-up] |
> **⚠ CHANNEL SCOPE (E-8b, 2026-07-12 — read before acting on LCA-1/-4/-11/-13):** these four findings were measured on the LOCAL surgical-primitives route (`/api/mcp/primitives`) + the `:8000` sidecar. The **deployed MCP connector** (`amjis-mcp-...run.app`, the public channel real consumers use) was subsequently confirmed live with **130 retrieval tools** serving real payloads (get_domain_reading → 23.6KB digest; all cited tools present). So the "unreachability" in LCA-4/-11 is largely a LOCAL-surface artifact, NOT a defect of the deployed system — to be re-tagged at consolidation (served-only-by-down-pipeline → reachable-deployed-mcp for families a deployed tool serves). LCA-1/-13 (dead surgical whitelist entries, broken sidecar) remain real for those local surfaces. The DATA-PLANE defects (R-45, LCA-5, R-42/R-44b/KP-4/R-43, LCA-6/9a-1/9b) are REAL on ALL channels — confirmed via the deployed connector (get_temporal_windows(native)=activation_count:0).

| R-43 (re-confirmed) | **Blind rediscovery of R-43 by Lane 3 cross-path diff** — `chart_dashas.lord_natal_dignity_d1` serves NULL for Sun and Saturn (default lahiri) and `lord_natal_shadbala_total` is advertised in schema but serialized NULL — the denormalized lord_* columns remain unreliable (the two INCONSISTENT quantities of 6). Also latent: `AVAYOGI_POINT` has two `sign` rows (different formula_id → Virgo vs Libra) and the surgical pivot silently returns only one (multi-formula collapse). Deduped against the existing R-43 row (not a new row). | — | — | [Lane 3 2026-07-12] dignity/shadbala NULL both charts; sign fidelity DB↔wire 100% match (37 subjects) otherwise | (see existing R-43 row) | REMEDIATED-PENDING-W4 [see R-43 — WP-1.8 / W1] |

### Lanes 2 / 6 / 7 — DEPLOYED-channel consumption (2026-07-12; Lane 2 partial 80/328 — session-limit interrupt, resumes)

Run against the deployed MCP connector (`amjis-mcp-...run.app`, 130 tools). Deliverables: `state/L267/shard-{2,6,7}-*.md`. Blind rediscoveries: **R-44a, R-48**.

| ID | Description | Gap type | Severity | Evidence/Source | Fix | Status |
|---|---|---|---|---|---|---|
| LCA-14 | **Every live ranked surface on the real channel is DROWNED and 100% UNATTRIBUTED, and the domain readings are domain-INVARIANT** — all 14 orientation/domain surfaces (both charts) fail §7.4: UNATTRIBUTED_share = **100%** (0 rows carry `grounding.fact_ids`/derivation ledger — only opaque signal_id handles; `get_chart_orientation` top entity = `UNATTRIBUTED` at 84.8 salience vs Venus 1.05 — **R-44a re-derived, worse than the 298/300 anchor**); and `get_domain_reading` **wealth top-K is 95% identical to relationship**, career/health/wealth overlap 19/20 — the surface does not discriminate between orthogonal life domains; chart-defining signals buried under identical-scored almanac-trivia walls (+ a wrong-chart substitution instance) | SURF (DROWNED + WRONG domain map) | **CRITICAL** | [Lane 6, 2026-07-12, 16 surfaces] raw §7.4 metrics per surface in shards; UNATTRIBUTED 20/20 & 60/60; wealth∩relationship 95%; get_chart_orientation grounding.fact_ids=[] | Add resolvable derivation-ledger to every ranked row; make domain readings domain-specific (fix the salience/domain mapping — same root as KP-4); demote trivia from top-K | REMEDIATED-PENDING-W4 [WP-1.2(α+β) / W1; resolvable attribution ledger (0% UNATTRIBUTED served, §N.5 fact_ids resolve to chart_facts), domain discrimination (wealth∩relationship top-20 ≤25% — 5%/10% both charts), trivia salience-demoted; deployed 2385fb62/fc84cd0d, 7/7 prod-verified 2026-07-13] |
| LCA-15 | **No large-N synthesis capability — all 7 heavy questions hit the ceiling (R-48 RE-DERIVED)** — magnitude-of-wealth, whole-chart contradictions, career/marriage/health/moksha/cross-domain-life-arc: none has a serving path that composes the N-hundred interacting factors; `get_domain_reading` returns 7,290 signal-ID refs capped at 200 with **no narrative text** (IDs without text), no map-reduce over signal families, no staged retrieval-with-aggregation | ARCH (un-synthesizable at scale) | **CRITICAL** | [Lane 7, 2026-07-12, 7/7 ceiling_hit] character domain convergence_count=7294, refs capped 200, no composing tool; synth_chart_brief_get covers 38 topics but not intelligence/buddhi | R-48 architecture item — a synthesis instrument consuming pre-aggregated L2 surfaces with staged drill + narrative-with-ledger | REMEDIATED-PENDING-W4 [WP-1.4 / W1; synthesis/compose_large_n composes N-hundred interacting factors via pre-aggregated L2 map-reduce (marriage universe 30,754→50 bounded exemplars/5 families, no ceiling), signal_ids resolve; deployed 2385fb62/fc84cd0d, 7/7 prod-verified 2026-07-13] |
| LCA-16 | **[FINAL 328/328] Only 4 of 328 questions (1.2%) are fully SUFFICIENT on the real channel — 170 SUFFICIENT-WITH-GAPS (52%), 154 INSUFFICIENT (47%), and ALL 328 forced class-9 ungoverned improvisation** (505 findings; verifier 37/3, the 3 being honest L5 structural-mode calibration gaps, no fabrication found)** — the consuming LLM had to improvise method/adjudication on every single question. Data-plane gaps surfaced: **no ayurdaya/longevity computation** (Pindayu/Nisargayu/Amsayu, maraka-dasha, alpa/madhya/purna-ayu — only generic 8th-house dignity); **no organ/body-system disease taxonomy** (no graha/sign→body-part map); **`judgment_query` has no character/buddhi domain** and its bhava→domain map collapses (bhava 5 = "progeny" only); `assess_health` top-10 are combustion-negations that **bury** Balarishta doshas + sade-sati (which `get_signals` surfaces → cross-surface INCONSISTENT); `get_temporal_windows`/`kala_windows_get` return `activation_count:0` for ALL domains over a 24-yr horizon (EMPTY SHELL, ~R-45 on the real channel) | SURF+DATA + class 9 | **CRITICAL** | [Lane 2 partial 80/328, 2026-07-12] sufficiency {0 SUFFICIENT, 40 GAPS, 40 INSUFF}; class9=80/80; 129 findings in shards | Governance/method layer (class-9 spec) + the data-plane gaps (ayus, organ-taxonomy, character domain) + fix R-45 empty windows | OPEN (Lane 2 resumes 248 remaining Q) |

| LCA-17 | **`get_chart_orientation` intermittently returns the WRONG chart's data — nondeterministic cross-chart substitution; a CORRECTNESS *and* ENTITLEMENT-class defect (cross-chart data leakage)** — a native-chart (482012f1) orientation call returned Abhinandan's (1c826d5a) digest (13369/13/22 = Abhinandan's, vs the native's true 13364/15/22). **Precise reproduction condition (captured 2026-07-12): NON-deterministic and load-correlated — it manifested during the Lane-6 SWARM (multiple workers hitting `get_chart_orientation` for DIFFERENT chart_ids concurrently) but did NOT reproduce in the verifier's isolated re-run NOR in 5/5 consecutive isolated native calls (all returned correct 13364).** Signature = a shared cache/session keyed on something other than chart_id, bleeding across concurrent different-chart requests (cf. auth.ts 60s validation cache + any orientation/digest cache). This is not merely a wrong-value bug: **a consumer entitled to chart A can receive chart B's data** — an entitlement/isolation breach (M0-gate class), the more severe reading. The register's Gaṇita "no cross-chart contamination" holds at L1; the SERVING layer leaks under concurrent multi-chart load. | LOGIC (data isolation + entitlement) | **CRITICAL** | [Lane 6 audit+verify 2026-07-12] shard-6-b0 captured f75a digest 13369/13/22 for a 71aa request during the concurrent swarm; verifier isolated re-run + 5/5 isolated probes returned correct 71aa 13364 → intermittent/load-correlated | Reproduce under controlled concurrency (N workers, alternating chart_ids); audit every cache in the orientation path for a chart_id-inclusive key; add a mandatory chart_id echo-back assertion server-side (reject/refetch on mismatch); treat as an entitlement bug, not just a correctness bug | **REMEDIATED-PENDING-W4** (WP-0.1 / W0; root cause = weak 32-bit hash in `platform/src/lib/retrieval/cache.ts` collapsing distinct chart_ids to one cache key under concurrent load; fix = SHA-256 key-sorted cache key + chart_id echo-back guard in `query_ucd.ts`; PR #553 merged `6ec244c0`, deployed `amjis-web-00955-qt5`; blind security/entitlement verifier CONFIRMED-FIXED — 0 substitutions / 2M iterations, echo-guard fails-closed vs 8 adversarial payloads, no entitlement regression; findings F-0893/F-0902/F-0905/F-0908; 2026-07-12) |
| LCA-18 | **Receipt-honesty is BETTER on the deployed channel than the local surgical route — refines LCA-7 scope** — the deployed connector honestly declares trims (`assess_*` → `truncated:true` + `total_count`; `get_signals` → `returned_count:50 / total_matching_filters:13364 / truncated:false`; `phala_outlook` → `trim_report`) and carries strong grounding (`fact_id`+`citation_ref` two_pass_verified on positions/dashas). BUT residual honesty defects remain on the deployed channel: `get_chart_orientation` shows 10 of ~13.3k signals with `pagination.total=null / trim_report=null` (**non-disclosed trim**), non-monotonic `top_k_salience_rank` vs presentation order (internal ranking inconsistency), digest counts served as strings while salience floats (type inconsistency), and domain readings are IDs-without-text (class 6). | DOC/SURF (mixed) | MED | [Lane 6 verify 2026-07-12] per-tool receipt evidence quoted in shards | Disclose the orientation trim (pagination.total + more_available); fix salience-rank monotonicity; hydrate domain-reading rows with headline text | REMEDIATED-PENDING-W4 [WP-1.5 + WP-1.2α / W1; orientation trim disclosed (real total + more_available), salience-rank monotonicity + type hygiene, domain-reading rows carry headline+summary; deployed 2385fb62/fc84cd0d, 7/7 prod-verified 2026-07-13] |

*(Lane 2/6/7 COMPLETE 2026-07-12 (resumed after the 06:10 IST usage-limit reset): Lane 2 328/328, Lane 6 16 surfaces, Lane 7 7/7. The 505 Lane-2 + 50 Lane-6 + 39 Lane-7 findings live in `state/L267/shard-*.md` + `state/LANE{2,6,7}.md` for the consolidation findings JSON.)*

### Lane 10 — Promise-vs-delivery grading (67 assets, deployed channel primary; 2026-07-12)

7.5 attribution rules, facet-grained. **DELIVERS 28 (42%) · SHORTFALL 25 · PARTIAL 14.** Shortfall layers: retrieval-plane 23 (dominant), compound 9, data-plane 6, ranking-form 2. Zero "promise undeclared" (all 27 ledger-NOT-FOUND re-sourced via the 4-source search). `state/LANE10.md` + `state/LANE10/shard-*.md`.

| ID | Description | Gap type | Severity | Evidence/Source | Fix | Status |
|---|---|---|---|---|---|---|
| LCA-19 | **Promise-vs-delivery: only 42% of built assets (28/67) deliver their promise; the dominant shortfall is RETRIEVAL-PLANE — 23 assets are computed and stored but have NO serving tool even on the deployed channel** — `ga_medical` (45 rows/chart, no medical tool), `ga_vastu_planet_direction_map` (40), `ga_yoga_firings` (Nabhasa firings w/ bhanga+activation — only the thin chart_facts `ganita_yogas_get` is served), `bodha_cdlm_chart_summary`, `bodha_cgm_motifs`/`paths` (45), `bo_chart_gestalt`, `kala_avadhi` (1,571), **`kala_taranga` (79,728 rows!)**, `kala_sangam` convergence rigor-stratum (6,484), `ka_gochara` transit-event search, `ka_tulana` compare-verdict. Plus data-plane (6): `bo_sangati` per-domain evidence-ledger never computed. Plus `kala_windows_get` = EMPTY SHELL (0 activations, ignores date params — R-45 at the promise level on the deployed channel). | SURF (retrieval) + DATA | **CRITICAL** | [Lane 10, 2026-07-12, verifier-checked] per-asset DB counts + deployed tools/list gaps quoted in shards; 61 findings | Add serving tools for the 23 computed-but-unserved assets (esp. kala_taranga/avadhi/sangam, ga_medical/vastu/yoga_firings, cgm_motifs/paths); this is the promise-level view of LCA-4 — the deployed channel serves the *popular* surfaces but leaves whole computed assets dark | REMEDIATED-PENDING-W4 (serving-half) [WP-1.3(a,j) / W1; 18 of 23 computed-but-unserved assets now served (ga_medical/vastu/yoga_firings, cgm_motifs/paths, kala_taranga aggregate-budgeted/drill-refuses, avadhi/sangam, bodha_discoveries/pratijna/question_lenses/rm_prescriptions/resonances, ph_pratikara/ph_rectification serving-bugs fixed); deployed 2385fb62/fc84cd0d, 7/7 prod-verified 2026-07-13. Residual data-plane (bo_sangati never computed, kala_windows R-45 NULL dates) → W2] |

## SECTION 13 — D-1.6 Śuddhi Lane S-8 governance sync (2026-07-16)

Per `BRIEF_D1_6.md` §F1 Lane S-8: sync every row this wave's S-7 verify-then-close pass closed or
parked, using `BIND_D-1.6.md`'s Binder probe results (13 CLOSED_WITH_EVIDENCE, 2 ROUTE_TO_LANE, 2
closed-core-with-residual). Rows updated in place above (Status column): **S-5** (gandanta) →
CLOSED_WITH_EVIDENCE; **S-4** (sputa/virupa drishti) → ROUTE_TO_LANE S-5 (data computed, serving
incomplete — merges with the standing PARK-A7); **S-12** (divisional-chart serving hole) →
CLOSED_WITH_EVIDENCE; **S-14** (ga_medical/ga_vastu tools) → CLOSED_WITH_EVIDENCE; **R-11**
(traverse_graph DSL) → CLOSED_WITH_EVIDENCE (did-not-reproduce; size residual → S-5); **R-47**
(sensitive-degree concepts) → CLOSED_WITH_EVIDENCE; **R-48** (large-N synthesis capability) →
**RE-DISPOSITIONED, still PENDING** — see the row itself for the full root-cause finding (code
exists + is registered in the internal retrieval catalog, never wired into an MCP
`register_p1_*.ts` tool file; the prior "deployed + 7/7 prod-verified" claim did not hold on the
live connector's `tools/list`); **D-5** (digest attribution) → CLOSED_WITH_EVIDENCE; **K-3**
(Sarvatobhadra/Kota/Sudarshan) → PARTIAL (Sudarshana half closed, Sarvatobhadra vedha-lines + Kota
stay open); **KP-4** (KP domain tags) → CLOSED_WITH_EVIDENCE (domain-tag core) + residual routed to
S-5 (cusp-longitude noise demotion, PARK-#4 scoping evidence). Companion POST_REMEDIATION-side rows
CR-7, CR-18, CR-46, CR-49, CR-50, CR-57, CR-58, CR-60 synced to CLOSED_WITH_EVIDENCE in
`POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md` (same probe evidence, same session).

**§E CR-33..38 permanent-ID assignment** (per the POST_REMEDIATION register's own merge-protocol
note, "assigns permanent IDs" — discharged here for this named sub-range): **CR-33 = Y-12** (same
finding: v3 verdict-builder fabricates "not formed" from a truncated page, Sasa-Yoga specimen —
intake/permanent-ID pair, no new row). **CR-34/CR-35 confirm Y-3 / Y-4** (D1-scoped NBRY blindness;
house-lord yoga family) — already-permanent rows, no new ID. **CR-36** or has no standalone
permanent ID — fully covered by S-1 (vargottama not joined) + CR-55/D-5 (weakest_graha, now
verify-then-close per this section) + G-6 (chain signal class, D-2) + CR-69/leverage_index (D-2);
cross-referenced, not duplicated. **CR-37 confirms T-4** (kala_activation empty; R-45 writer
date-population, D-1.6 Lane S-4) — no new ID. **CR-38** is READING-NOTES (chart knowledge, not a
defect) — no defect ID assigned. Full detail + rationale table in
`POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md` §N.

**CR-90..107 merge debt (Gate Ś item 14):** resolved in `POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md`
§N — this file (`MARSYS_DEFECT_GAP_REGISTER_v2_0.md`) does not carry the raw CR-90..107 finding text
(it never did — those rows were authored directly into the Doctrine-Waves brief corpus in the
2026-07-14/15 Cowork sessions, absorbed at authoring time, and never committed to the
POST_REMEDIATION register's git history either); system-of-record for that range is
`DOCTRINE_CAMPAIGN_EXECUTION_PLAN_v1_0.md §8` + the live doctrine-wave briefs, per the pointer table
in POST_REMEDIATION §N. No dangling row range remains across either register.

**CR-108 [CLOSED 2026-07-18, FIX-PSEL lane, PR #605, verified ACCEPT twice (predicate-selection
diagnosis confirmed genuine ceiling-by-construction not a bug; quota+content-hash tiebreak
fix independently traced correct), deployed, falsifier-confirmed live (16,767 real Mode A/B
kala_convergence rows bear trigger_weights_used post-rebuild — TRIGGER genuinely exercises real
data for the first time in the campaign's history)] (2026-07-18, D-3 cycle-2b, conductor-discovered,
native-ratified — pre-existing class, same system-of-record convention as CR-90..107):**
predicate-selection dignity_score saturation +
insertion-order tiebreak. `ka_sangam.py::plan_substeps()` selects the top-200 (near tier) / top-60
(lifetime tier) `kala_activation_predicates` via `ORDER BY dignity_score DESC NULLS LAST, id ASC
LIMIT N`. On 482012f1, **4,441 predicates across ALL 6 signature classes sit at the exact ceiling
`dignity_score = 1.0`** (SUBSYSTEM 3,827 / DISPOSITOR_RELATIONAL 552 / DIGNITY 60 / YOGA 2) — a score
field saturated at its ceiling for 4,441 rows has zero discriminating power at the top, which is
either a clamp/normalization bug or a degenerate scoring formula (root cause not yet diagnosed).
Compounded by an insertion-order tiebreak (`id ASC`) that always resolves the tie in favor of
SUBSYSTEM (systematically lowest ids), so predicate selection is 100% SUBSYSTEM for this chart,
every rebuild — starving the Mode A/B convergence-scoring path (and everything downstream that
depends on it, including D-3's TRIGGER suppression and CR-102 vedha fix) of any real-data exercise.
Native disposition: fix at source if a clamp/default-fill bug (§1 of the fix lane), else document as
a genuine ceiling-by-construction finding; harden selection with a per-signature-class quota + a
content-hash tiebreak (not insertion-order — flagged as a reproducibility-trap pattern to grep for
estate-wide); STOP-and-report if the saturation traces into `ga_vichara` or the core scoring writer
(would expand this from a selection fix into a scoring rework, out of one lane's scope). System-of-
record: `00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/MEMO_D-3_1.md` (full finding +
native disposition) + `STATE_D-3.md` (`cycle2b_critical_finding_predicate_selection_bug`) — this row
is a pointer only, per the CR-90..107 convention above.

**CR-109 [CLOSED — FIXED 2026-07-19, D-4a Lane A-0, migrations 454/455, independently
Opus-verified live at D-4a close, re-spot-checked live 2026-07-19 pre-D-5 readiness pass
(50 real rows served for 2080-2085, previously-empty range)]:** served activation-window coverage
gap. `resolve_activation_windows()` (`platform/python-sidecar/services/ka_temporal/date_resolver.py`
~L392-551) computes ALL matched dasha periods for a predicate but collapses to a single
`primary_selected` window (current-straddling > soonest-future > most-recent-past, anchored to
build-time "today"), so served coverage effectively brackets ~2010-2032 and drops everything
outside that band — confirmed as the majority driver of D-3's §G RED (A1's coverage-matched
control-gap re-analysis: -16.1pp raw -> -15.8pp coverage-matched, i.e. the gap is real kernel
signal, not a coverage artifact, but the coverage gap itself is a separate genuine defect
independent of that finding). FIX-COV (A2) diagnosed this root cause correctly and STOPPED per
its own guard: a real fix requires a schema/cardinality change (serving multiple windows per
predicate, full-span birth->2054) exceeding FIX-COV's narrow infra-only remit — correct STOP
behavior per protocol, not a failure. The standing one-re-run allowance lapsed with the wave
closing; §G does not re-run on this fix. Disposition: transfers to D-4 as Lane C-0(a),
surgical migration + writer-cardinality change per CLAUDE.md §N.4, zero kernel/weight changes.
System-of-record: `00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/STATE_D-3.md`
(`cycle2_wrapup_pass_A1_A2`), `PRE_D4_WRAPUP_REPORT.md` (§A2), `REPORT_D-3.md` §11.

**CR-110 [CLOSED — REPRODUCED then FIXED 2026-07-19, D-4a Lane A-0 (root cause: `ka_avadhi.py`'s
`_FETCH_MD_SQL`/`_FETCH_AD_SQL` missing an `ayanamsha_id` filter, pooling across 5 ayanamshas),
independently Opus-verified live at D-4a close, re-spot-checked live 2026-07-19 pre-D-5
readiness pass (Mercury MD under vimshottari/lahiri_chitrapaksha: exactly 1 row)]:** double
dasha-spine bug in `kala_temporal_bundle`. Native's
2026-07-18 temporal test on the deployed connector observed two ayanamsha dasha-period variants
interleaved undisclosed in a single served bundle: Mercury MD reported as ending BOTH
2027-08-12 and 2027-08-18 (two different values for the same period boundary in the same
response), plus phantom Ketu-MD-2025 rows carrying Venus/Sun antardashas that do not belong to
that mahadasha lineage. Suspected root cause (unverified): the bundle join pulls dasha rows
across more than one ayanamsha computation without a discriminating filter, silently merging
variant timelines into one served structure. Disposition: intake only — no diagnosis, no fix
attempted this session. Transfers to D-4 as Lane C-0(b); D-4's binder must independently verify
before scoping a fix. System-of-record: native's 2026-07-18 temporal test (conductor-relayed,
not independently reproduced); `D4_BRIEF_REVISION_INPUTS.md` §C-0.

**CR-111 [CLOSED — REPRODUCED then FIXED 2026-07-19, D-4a Lane A-0 (root cause:
`kala_temporal.ts`'s `fetchCapabilityRows` always reading a `.rows` field when
`query_convergence_windows`/`query_obstruction_periods` name their arrays
`convergence_windows`/`obstructions`), independently Opus-verified live at D-4a close,
re-spot-checked live 2026-07-19 pre-D-5 readiness pass (`convergence_count=50` for 2026-2027,
matches `kala_convergence` table)]:** convergence-windows build-vs-serve gap. Native's
2026-07-18 temporal test observed `kala_temporal_bundle` returning 0 convergence windows for
the 2026-2027 range on the deployed connector, while the underlying `kala_convergence` table
holds 16,767 TRIGGER-refined rows (the same FIX-PSEL/PERF-TRIGGER-CACHE-fixed real data
verified live earlier this wave) peaking 2027-10-20 through 2027-11-01 — i.e. the build side
has real, dated, high-density data for exactly the window the serve side reports empty.
Suspected root cause (unverified): a join predicate or date-window filter on the serving path
excludes rows the build path already produced; distinct from CR-109 (which is about window
*selection/collapse*, not a build-vs-serve join mismatch). Disposition: intake only — no
diagnosis, no fix attempted this session. Transfers to D-4 as Lane C-0(c); D-4's binder must
independently verify (direct DB query against the deployed connector, CR-96 discipline: verify
the consuming surface) before scoping a fix. System-of-record: native's 2026-07-18 temporal
test (conductor-relayed, not independently reproduced); `D4_BRIEF_REVISION_INPUTS.md` §C-0.

**CR-112 [CLOSED — FIXED 2026-07-19, pre-D-5 readiness pass, conductor-discovered own briefing
error]:** item #3 (father's spiritual dialogues, 1997→2001 correction) of
`NATIVE_DATE_TIGHTENING_RESPONSES_v1_0.md` was never ingested during D-4a's Lane A-1 — the
conductor mis-briefed the implementer to skip it as "quarantined pending native confirmation,"
when `BRIEF_D4A.md`'s own frontmatter already stated `item-#3-quarantine RESOLVED` and the
responses doc itself showed the item `RESOLVED (native, 2026-07-19)`. Fixed via
`platform/scripts/d4a/fix_item3_spiritual_arc_correction.mts` (committed `3a53acdb`): append-only
correction row inserted (chart 482012f1 `life_events` 62→63), chain-linked to 4 existing
milestone rows (items #6/#10/#14/#15). Independently Opus-verified live (ACCEPT-WITH-FINDINGS,
2 cosmetic-only findings: a 1-day-off provenance date field, no explicit event_class FK column
on `life_events` — neither blocks acceptance).

**CR-113 [CLOSED, verified 2026-07-20 D-5 open + independently re-verified 2026-07-21 pre-D-4b
readiness pass]:** orphaned `build_runs` row `372b5cfa-9aa6-45b7-b72f-dcb813e57f7b`
(`state='running'`, `ended_at=NULL`, `action='rebuild'`, chart 482012f1) — reaped via
`/api/cockpit/watchdog` at D-5 open (BIND_D-5.md `first_actions.cr_113: closed`). Independently
re-confirmed this session via direct query (`SELECT ... FROM build_runs WHERE state NOT IN
('completed','failed','stopped')` returns zero rows) — no new orphaned rows exist as of this
pass.

**CR-114 [CLOSED — dispositioned non-blocking at D-5 open, verified still holding]:**
`amjis-mcp`/`amjis-sidecar` image staleness relative to `origin/main` — resolved by D-5's own
deploys (multiple PRs landed + redeployed through the wave). Re-verified this session (pre-D-4b
readiness pass, 2026-07-21): all three deployed services (`amjis-mcp`, `amjis-web`,
`amjis-sidecar`) are code-current with `origin/main` HEAD — the only commits `origin/main` carries
ahead of the deployed SHAs are pure docs/governance/session-log/ops-script commits (confirmed via
`git diff --stat` against `platform/src`, `platform-mcp`, `platform/python-sidecar` — empty diff).

**CR-116 [CLOSED, this session — pre-D-4b readiness pass, 2026-07-21]:** `ka_gochara_sweep`'s
per-substep throughput defect (native-flagged: ~10min/substep vs the orchestrator's 1800s
`writer_timeout_seconds` budget, blocking full materialization). Root-caused: two DB reads inside
the per-day PERMISSION computation (`gochara_grammar/primitives.py`'s `_fetch_av_gate_rows` — a
global L0 reference-table read — and `_fetch_sade_sati_rows` — a chart-scoped but
build-lifetime-static `chart_facts` read) are re-issued on every one of ~365 grid-day calls per
year-substep, despite both tables being unchanged for a build's entire lifetime. Fixed via
correctness-preserving memoization (module-level cache, keyed by the same arguments that already
determine the query; a read FAILURE is never cached, only success, so a transient error stays
retryable). Measured ~600x speedup on the affected calls (chart 482012f1, career_advancement
targets). Verified: adversarial cache-poisoning probe (a sentinel value planted in the cache is
returned verbatim instead of hitting the DB — proves the cache path is genuinely consulted, not
bypassed); determinism proof (two independent in-process re-derivations of the same 30-day window,
cache cleared between runs, produce byte-identical output); full non-integration test suite
189/189 green. PR #670. **Residual, NOT closed by this fix:** the underlying real ephemeris-search
cost per grid day is untouched by this cache (it only removed the two redundant static reads) —
full 300-substep materialization of `ka_gochara_sweep` for chart 482012f1 remains a
multi-dispatch-cycle operation; see this pass's own report for the live re-materialization
evidence and remaining substep count.

**CR-117 [CLOSED, this session — pre-D-4b readiness pass, 2026-07-21]:** cockpit badge-honesty
defect (native-flagged): the asset badge reported the same `error` state for a genuinely broken
writer and a heavy (`has_substeps`) writer that had merely hit its own `writer_timeout_seconds`
mid-materialization — a safely resumable situation, indistinguishable from a real defect at a
glance. Fixed: `deriveState` (`platform/src/app/api/cockpit/stats/route.ts`) now checks
`build_substep_progress` for `has_substeps` assets in the `error` state — a committed-substep
count > 0 downgrades the badge to a new, distinct `partial` state carrying honest progress
(committed count; `total` left null unless a future asset populates a computable expected-volume
formula — never fabricated per B.10). Wired through both cockpit UI surfaces. Verified: 6/6 new
`deriveState` unit tests; full project `tsc --noEmit` clean. PR #671.

**NEW ASSERTION CLASS registered (this session, not a numbered CR — a standing gate-discipline
rule):** materialization-completeness precedes gate/scoring. D-5's own marriage-specimen verdict
(gate_run_3) was rendered against a `ka_gochara_sweep` that had committed roughly 1% of its
planned substep coverage (3 of ~300, all specimen-priority substeps dispatched first) — defensible
for a targeted specimen spot-check, but this pattern generalizes badly: any future wave whose gate
scores against a HEAVY (`has_substeps`) writer's output must first assert that writer's
materialization is complete (100% of planned substeps committed) before treating a scoring verdict
as meaning what it claims to mean. Encoded as a binding, hard-prerequisite gate criterion in
`BRIEF_D4B.md §0`, ahead of every other D-4b gate criterion — not merely a recommendation.

**CR-115 [OPEN, discovered PG-2 Lane X-5 (2026-07-19), carried to PF-1 §F1 Lane F-2, live
schema-diffed]:** `platform/python-sidecar/brahmagyan/mimamsa/outcome.py` references
`phala_anchors` columns absent from the live schema — it uses `id`, `confidence`,
`prediction_state`, `outcome_note`, `outcome_recorded_at`, `updated_at`; the live table has
`anchor_id`, `confidence_low`/`confidence_high`, `posterior`, `computed_at`. Consequence: the MCP
`record_outcome` tool — the mechanism that closes the calibration loop and lets L5 leave
STRUCTURAL mode — **would fail at runtime and has never been called.** A live hole in the L5
calibration loop, not a cosmetic drift; recorded here rather than left silent inside a FROZEN
brief. Two distinct sub-cases suspected (per PF-1 §F1 Lane F-2): `id`→`anchor_id` and
`confidence`→`confidence_low/high` look like renames (fix the code); the three outcome-capture
fields (`prediction_state`, `outcome_note`, `outcome_recorded_at`) look genuinely absent from the
table (a real migration, not a code fix — do not migrate speculatively). Fix owned by PF-1's
remaining scope (`CLAUDECODE_BRIEF_PF1_ENGINE_RESURRECTION_v1_0.md`, Lane F-2), kickoff after
retrieval-campaign W4 closes, per the native's 2026-07-20 re-scope ruling. Full detail:
`REPORT_PG-2.md`.

**CR-118 [RESOLVED 2026-07-23, RC-11 (R-10/CR-118) root-cause + fix session, branch
`res/rc11-cr118-fastfails` — originally OPEN, discovered W4 precondition-verification live probe
(2026-07-21), chart 482012f1, via the deployed `/api/chat/consult` route post-
`bundle_hydrator.ts` fix]:** the `msr_sql` tool
call errors mid-stream during live synthesis — SSE event
`{"type":"tool","name":"msr_sql","status":"error","ms":4,"ok_count":0,"err_count":1}`, a ~4ms
failure suggesting an immediate validation/dispatch error rather than a slow query or timeout.
Did not block the overall response (synthesis completed successfully around it, HTTP 200,
grounded CGM/UCN-cited answer delivered) — a graceful-degradation case, not a user-facing outage.
`gcloud logging` swept for `msr_sql` in the surrounding 20-minute window on `amjis-web` returned
no matching structured log entries — root cause undiagnosed beyond the SSE evidence above; a
proper diagnosis needs either richer server-side error logging on this tool's dispatch path or a
repro with verbose tracing enabled. Native ruling (2026-07-20): **out of W4 scope** — recorded
here with evidence, to be picked up by whichever of W5 (adaptive-serving/budget work) or PF-1
(teardown-orphan sweep) reaches it first.

**CR-119 [OPEN — DRIFT FINDING, discovered this session, 2026-07-21, formal-D-4b-open recording
pass on `wave/D-4b/open`]:** commit `ae9457d2` ("docs(current-state): cross-campaign note for D-4b
conductor") asserted, inside `CURRENT_STATE_v1_0.md`'s §2 cross-campaign note, that "D-4b was
confirmed actively executing (live gochara-perf branches, concurrent `worktree-agent-*` sessions,
checked via `git branch -a`/`gh pr list`, not a stale ledger read)" as the justification for
withholding the `impl/w5-breaking` rename cutover. This session independently re-ran both cited
commands (`git branch -a`, `gh pr list`) and found **zero** `wave/D-4b/*` branches or open PRs at
the time — directly contradicting the commit's claim. Consequence: the claim that motivated
withholding `impl/w5-breaking` was unsubstantiated at the moment it was written; the underlying
withholding decision may still be correct for other reasons (D-4b was genuinely FROZEN, not open,
per `BRIEF_D4B.md`'s own status at that time — so "no D-4b agent swarm was live" was in fact the
truer state), but the note's own stated evidence for it does not hold up. **Annotated, not
reverted** — commit `ae9457d2` stands in git history; this row is the correction record.
Disposition: informational drift finding for whichever session next reconciles
`RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md §I.6`'s D-4b-quiet re-check gate — the re-check
should not treat the original commit's live-branch claim as verified evidence of anything.

**UPDATE (2026-07-21, post-W4-deploy live-probe, chart 1c826d5a via the deployed connector,
merge commit `a1ed172b`):** the same fast-fail pattern reproduced on **three** tools in one
request, not just `msr_sql` — `{"name":"msr_sql","status":"error","ms":6}`,
`{"name":"get_yoga_firings","status":"error","ms":5}`,
`{"name":"cgm_graph_walk","status":"error","ms":4}` — all erroring in single-digit milliseconds
in the same tool_fetch stage, while a fourth tool in the same request (`vector_search`) ran
normally and returned real data (`ok_count:1`, `ms:6065`). Widens this defect: it is not
`msr_sql`-specific, and notably `get_yoga_firings`/`cgm_graph_walk` are two of the four
web-executable MCP↔retrieval bridge mappings W4's floor-adoption work depends on
(`LIVE_TOOL_TO_RETRIEVAL` in `compiled_floor_adapter.ts`) — so this defect directly reduces how
much of the newly-compiled floor can actually serve data today, on top of the already-documented
namespace-gap limitation. Still did not block the overall response (graceful degradation held).
Still out of W4 scope per the same native ruling; recorded here rather than silently left as a
narrower finding than the evidence now supports.

**RESOLUTION (2026-07-23, RC-11 / R-10 session, branch `res/rc11-cr118-fastfails`):** root-caused
and fixed. The `ToolEvent` shape both live probes cite
(`name`/`status`/`ms`/`ok_count`/`err_count`) exists nowhere else in the codebase but
`platform/src/app/api/chat/consult/route.ts` (its own `ToolEvent` interface + `toolEventLog`
push sites) — confirming both probes ran against `/api/chat/consult`, the web-chat synthesis
route, not the `prashna_ask` MCP tool (which uses an unrelated `tool_name`/`result_count`/
`latency_ms` shape and was independently confirmed healthy live this session — see below).

**Root cause:** `consult/route.ts` builds a `LegacyQueryPlanShape` object ("Adapter: PipelinePlan
→ legacy-shaped object for retrieval tools" comment, ~line 624) that is handed to
`executeWithCache(tool, queryPlan, ...)` → `tool.retrieve(plan, params)`
(`tool_name_bridge.ts`'s `getToolByName().retrieve()`). That wrapper reads `plan['chart_id']`
to populate `args.chart_id` for every `scope: 'per_chart'` capability
(`if (cap.scope === 'per_chart' && chartId) { args['chart_id'] = chartId }`). The
`LegacyQueryPlanShape` **interface never declared a `chart_id` field, and the object literal
never set one** — so `plan['chart_id']` was always `undefined` for this route's dispatch, for
every tool, regardless of which chart the request was actually scoped to. `msr_sql`
(`query_signals.ts`), `get_yoga_firings`, and `cgm_graph_walk` (`traverse_chart_graph`) are all
`scope: 'per_chart'` with `required_inputs: ['chart_id']`; their handlers open with a synchronous
guard — e.g. `query_signals.ts`: `const chart_id = args['chart_id'] as string; if (!chart_id)
return { content: { error: 'chart_id is required' }, is_error: true }` — that returns **before
any DB round-trip**, exactly matching the observed single-digit-ms error/empty pattern.
`vector_search` (chart-agnostic, `scope` ≠ `per_chart`) never reads `chart_id` at all, which is
why it alone succeeded in the same request (`ms:6065`, real data) while the other three fast-failed.

**Fix:** added `chart_id: string` to `LegacyQueryPlanShape` and the object literal in
`consult/route.ts` (`chart_id: chartId`, the same `chartId` the route already validates as a
required UUID at request-body parsing). Mirrored the same `chart_id?: string` field onto the
shared `QueryPlan` type (`platform/src/lib/retrieval/shared_types.ts`) so every future
`QueryPlan`-literal builder is reminded to carry it. Code audit for the same bug class
(`grep -rn '.retrieve('`) additionally found `platform/src/app/api/mcp/primitives/[tool]/route.ts`
— the actual HTTP surface the MCP sidecar's surgical primitive calls hit
(`platform-mcp/src/tools/registry_bridge.ts`'s `callPlatformPrimitive`, `register_p1_aliases.ts`'s
`callPlatformPrim`) — with the identical defect: it resolved `chartId` (from `toolParams` or the
`X-MCP-Chart-Id` header) for the `authorizeChartAccess` entitlement gate only, then built its own
`queryPlan` with no `chart_id` field. Every MCP tool definition observed in this codebase happens
to pass `chart_id` explicitly inside `params` (confirmed both by code reading and by live probes
below), so this second site was not the one CR-118's SSE evidence reproduces — but it is the same
bug class and was fixed alongside it as defense-in-depth (chart_id now threaded from the already-
resolved `chartId` onto `queryPlan.chart_id`; also added `chart_id?: string` to
`platform/src/lib/router/types.ts`'s `QueryPlan`, the type this route imports).

**Live verification:** deployed main (`651c6478`) does not yet carry this fix (fix is local to
this branch, unmerged/undeployed), so a live re-probe of `/api/chat/consult` itself was not
reachable from this MCP-only session (no browser/HTTP-with-session-cookie tool available; only
`mcp__marsys-jis-direct__*` tools). What WAS verified live, against the deployed connector, chart
`482012f1-710e-4a25-994a-93821f5871aa`:
  - `prashna_ask` (job `d008ca3b-da98-4320-9d2c-73ea636cf669`, deep cross-domain query hitting
    yogas/MSR/CGM) → `completeness.tools_dispatched` shows `msr_sql` (`status:"done"`,
    `latency_ms:64`) and `cgm_graph_walk` (`status:"done"`, `latency_ms:22`) both succeeding —
    `empty_result_tools: []`, `unresolved_tools: []`. Confirms `prashna_ask` (which already built
    its `queryPlanLike` with `chart_id: chartId` before this session — not itself affected by
    CR-118) is healthy on the live deployment, consistent with the SSE-shape analysis above.
  - Direct MCP primitive calls `get_signals` (msr_sql-equivalent), `ganita_yoga_firings_get`
    (get_yoga_firings-equivalent), `get_cgm_subgraph` (cgm_graph_walk-equivalent) all returned
    full structured data with no error/empty pattern — consistent with these MCP tool
    definitions always supplying `chart_id` explicitly in `params`.
  - `/api/chat/consult` itself (the actual CR-118 SSE-trace source) could not be re-probed live
    from this session for the reason above. Confidence in the fix rests on: (a) exact root-cause
    match between the code defect and the documented ~4-6ms error/empty symptom; (b) the
    regression tests below, which fail (reproducing CR-118's exact symptom —
    `plan['chart_id'] === undefined` for msr_sql/get_yoga_firings/cgm_graph_walk) against the
    pre-fix code and pass against the fix; (c) `npx tsc --noEmit` clean, full relevant vitest
    sweep green (1103 passed, 0 failed, 125 pre-existing skips unrelated to this change).

**Regression tests added:**
  - `platform/src/app/api/chat/__tests__/cr118_chart_id_plan_regression.test.ts` (new) — drives
    `/api/chat/consult`'s real `POST` handler through a planner mock authorizing exactly
    `msr_sql`/`get_yoga_firings`/`cgm_graph_walk`, captures every `plan` argument
    `executeWithCache` is invoked with, and asserts `plan.chart_id` equals the request's
    `chartId` for all three. Fails pre-fix (`expected undefined to be '482012f1-…'`), passes
    post-fix.
  - `platform/src/lib/__tests__/mcp/primitives.test.ts` (extended, 3 new cases) — CR-118 chart_id
    reaches `queryPlan.chart_id` when supplied via `params`; CR-118 chart_id reaches
    `queryPlan.chart_id` when supplied ONLY via the `X-MCP-Chart-Id` header (the specific gap the
    primitives-route fix closes); chart-agnostic tool (`vector_search`) never has `chart_id`
    fabricated onto its plan. All three fail pre-fix, pass post-fix.
  - Verified regression-test validity directly: reverted the two production fixes via
    `git stash`, re-ran the new/extended tests — all 3 target assertions failed with
    `expected undefined to be '482012f1-710e-4a25-994a-93821f5871aa'`, i.e. they reproduce
    CR-118's exact defect signature; restored the fixes, all tests green again.

**Files touched:** `platform/src/app/api/chat/consult/route.ts`,
`platform/src/lib/retrieval/shared_types.ts`, `platform/src/app/api/mcp/primitives/[tool]/route.ts`,
`platform/src/lib/router/types.ts`, `platform/src/lib/__tests__/mcp/primitives.test.ts`,
`platform/src/app/api/chat/__tests__/cr118_chart_id_plan_regression.test.ts`.

**Residual:** the DONE bar's "resolves cleanly on a live trace" is fully satisfied for the
`prashna_ask`/direct-primitive live paths (verified above) but NOT independently re-verified live
for `/api/chat/consult` itself post-fix (requires a deployed build + authenticated web session,
neither available to this MCP-tool-only session) — flagged honestly rather than claimed. Next
session with web/browser access to the deployed app (post-merge) should re-run the same
yoga/MSR/CGM-triggering chat query against `/api/chat/consult` and confirm the SSE trace shows
`status:"done"` (not `error`) with realistic (non-single-digit-ms) latency for all three tools.

**CR-120 [NOT-EVALUABLE — coverage gap, not a retirement, recorded D-4b permission-bridge lane
(`wave/D-4b/permission-bridge`), 2026-07-22]:** B-1's Grand Bakeoff (`BRIEF_D4B.md §1 B-1`) names
`midpoint-triangle` (the deprecated arithmetic-midpoint incumbent, 0.6/1.0/0.4 envelope) as a
contender every other model must beat. Its `TemporalCurveModel` adapter
(`model_interface.ts`'s `midpointTriangleModel()`) remains an explicit
`NotImplementedModelError` stub — no midpoint-triangle substrate has ever been wired into the
a3_scoring_harness (confirmed live by `B1_BAKEOFF_STATUS_v1_0.md §3`, re-confirmed this lane via
the new `roster_bind.ts` bind-time assertion, which throws loudly and by name if
`midpoint_triangle` is ever included in the ACTIVE roster). **NOT-EVALUABLE, not retired, not
deprecated by this row** — the model is not deleted from doctrine and no code representing it is
removed; `midpointTriangleModel()` stays in `model_interface.ts` exactly as-is, throwing its own
named error rather than being silently dropped. **Disposition (native ruling, this session):**
midpoint-triangle's role as the bakeoff's mandatory baseline-every-model-must-beat passes to the
mirrored shuffled-birth negative controls already built and gated in the harness
(`curve_controls.ts`'s `shuffledBirthControlCurve`, DR-15(b)/(c), exercised identically for every
real contender via `harness.ts`'s `runMirroredScoringHarness`) — "losing a deprecated incumbent
costs little" since the shuffled-birth control already supplies a real, non-fabricated,
doctrine-ratified baseline every contender is scored against. Re-evaluation path (should a real
midpoint-triangle substrate ever be wired in): write the adapter against the FROZEN
`TemporalCurveModel` contract (`model_interface.ts`), pass this lane's `roster_bind.ts` bind-time
assertion, and B-1's Binder decides whether to re-admit it as a scored contender alongside (not
instead of) the shuffled-birth control baseline. No target wave assigned — this is a standing
open item, not a scheduled candidate (unlike CR-121 below).

**CR-121 [NOT-EVALUABLE — coverage gap, not a retirement, recorded D-4b permission-bridge lane
(`wave/D-4b/permission-bridge`), 2026-07-22]:** `transit-kernel` (D-3's kernel, BRIEF_D4B.md §1
B-1: "run on the C-0-repaired serving surface — its D-3 RED per-event table is its standing
baseline entry, not a fresh cold-start") also remains an explicit `NotImplementedModelError` stub
in `model_interface.ts` (`transitKernelModel()`) — confirmed live by `B1_BAKEOFF_STATUS_v1_0.md
§3` and re-confirmed this lane via `roster_bind.ts`. **transit-kernel's D-3 RED gate result
(`REPORT_D-3.md`: both named-mechanism checks miss top-decile 81%/67% of threshold; blind battery
17.5% vs 50% floor; scores worse than shuffled-birth control by -16.1pp, coverage-matched -15.8pp)
REMAINS its last recorded result — labeled explicitly
NOT-RE-EVALUATED-ON-REPAIRED-SUBSTRATE.** The D-3 RED run predates every C-0/RED-C/RED-D repair
this campaign has since made to the serving surface it depends on (per-substep throughput
memoization, AV-gate/sade-sati caching, the RED-C max_days-cap fix, the RED-D marriage-mechanism
activation fix) — its RED verdict was never re-run against the repaired substrate, so it is
neither reconfirmed nor overturned by anything in D-4a/D-5/D-4b to date; treating the old RED as
still-currently-true or as silently stale would both be dishonest, hence this row states plainly
which it is: a stale-but-not-superseded prior result. **Registered as a named D-6-era candidate
item** — per this session's native ruling, a "2.0 sweep engine" planned for the D-6 era is
understood to subsume transit-kernel's underlying physics (no committed design artifact for it
exists yet on this branch as of this row's writing — the next session scoping D-6 should confirm
whether a `GOCHARA_SWEEP_2_0_DESIGN` artifact has since landed and cite it here), so
transit-kernel's real re-evaluation is deferred to whenever that engine lands rather than re-run
piecemeal against the current interim substrate.
**NOT-EVALUABLE, not retired, not deprecated by this row** — no transit-kernel code or doctrine
reference is removed; `transitKernelModel()` stays exactly as-is in `model_interface.ts`.

**CR-122 [OPEN, discovered RC-04 live probe re-run (2026-07-22/23), `PROBE_DIFF_v2_0.md` §3.1,
independently reproduced live by the RC-04 verifier 2026-07-23]:** `phala_anchors_get(chart_id=
482012f1)` — the identical call that succeeded at W0 (2026-07-19, ~4.8KB response, "falsifier +
causal_chain on every anchor") — now 422s: `sidecar /api/compute/phala/event_anchors failed (422):
{"detail":[{"type":"missing","loc":["body","date_range"],"msg":"Field required",...}]}`. **Root
cause: a schema/implementation contract drift, not a caller error** — the live MCP tool's own
JSON schema still lists `date_range` as optional (only `chart_id` is in `required`), but the
underlying Python sidecar (`/api/compute/phala/event_anchors`) now hard-requires it and 422s
without it, sometime between W0 (2026-07-19) and this RC-04 re-run (2026-07-22) — not cited in any
W2-W6 close record `CENSUS_v2_0.md` reviewed, i.e. undocumented/unintended. Every caller relying on
the published tool schema (which says the field is optional) will 422 on this call today. **Not
fixed this session** — per this fix-cycle's own bounded scope (RC-04 is measurement, not
remediation; a real fix requires deciding whether the sidecar's new hard-require is the intended
behavior, in which case the MCP tool schema should be corrected to mark `date_range` required, or
whether the sidecar regressed and should accept the omitted field as it used to — that
determination needs the phala/mimamsa engine owner, not a unilateral one-line guess). Owned by
whichever future residual next touches `phala_anchors_get`'s sidecar contract (candidate: PF-1's
engine-resurrection lane, same family as CR-115's `outcome.py`/`phala_anchors` schema drift, though
a distinct symptom — CR-115 is `record_outcome`'s write-path column drift; this is
`phala_anchors_get`'s read-path required-field drift; both point at the same underlying
phala/mimamsa sidecar contract needing a schema reconciliation pass). Evidence: `PROBE_DIFF_v2_0.md`
§3.1, `VERIFY_RC-04.md` §"Independent re-verification" item 3 (verifier's own live reproduction).

**CR-123 [OPEN, discovered RC-04 live probe re-run (2026-07-22/23), `PROBE_DIFF_v2_0.md` §4]:**
`ref_yogas_get()` and `ref_doshas_get()`, called unfiltered exactly as W0 called them, now return
**86,972 chars** and **61,095 chars** respectively (W0, 2026-07-19: ~2.5KB and ~2.4KB) — both now
hit the MCP client's own max-token cap (saved to disk by the harness's truncation-disclosure
mechanism, not silently truncated). **Root cause confirmed via direct SQL, not a bug in the row
shape:** `brahma_yoga_catalog` has grown to 179 rows and `brahma_dosha_catalog` to 79 rows (real
classical-corpus growth, consistent with `bg_yogas`'s `target_floor: 250`), each a content-rich
structured object; default page size is 100 rows on both tools. **The actual defect:** unlike
`get_domain_reading` / `asset_registry_all` / `mitigation_map` — which this same RC-04 re-run
confirmed are now budget-bounded via `response_budget.ts`'s trimmer (§N.6) — `ref_yogas_get` and
`ref_doshas_get` carry **no `trim_report` / budget-bounding mechanism** and hit the raw transport
limit instead of degrading gracefully as their underlying corpus crosses the threshold. Same defect
class as the still-open R-1 row above (budget/trim not universal) and R-20 (mislabeled `ref_*`
catalog tools), newly manifesting on these two specific tools as their row counts grew past the
old response-size class. **Not fixed this session** — applying `response_budget.ts`'s trimmer to
two more tools is a genuine, scoped code change (find every call site, wire `dualOutput`/trim
config, verify no truncation-disclosure regression) that exceeds this fix-cycle's "one-line
schema/trim-config fix" ceiling; recorded here per §G rather than attempted speculatively.
**Recommendation for the future residual that picks this up:** apply the identical trimmer
mechanism already proven on the three siblings above to `ref_yogas_get`/`ref_doshas_get`. Evidence:
`PROBE_DIFF_v2_0.md` §4.

**CR-124 [OPEN, discovered RC-04 drill-crawl fix-cycle (2026-07-23), `RESOLVER_RULINGS.md`
Ruling RC-04-002]:** `register_p1_aliases.ts` has **22 other `dualOutput(data)` call sites**
(no explicit `toolName` argument) beyond the one this fix-cycle live-reproduced-broken and fixed
(`phala_outlook_get`, line 1434 → now `dualOutput(data, 'phala_outlook_get')`). Every one of
these 22 will default `autoDetectTrimmableSections`'s `recover_via.instrument` to the literal
placeholder `"unknown_tool"` (`register_p1_aliases.ts:181`) the moment its response is large
enough to trigger auto-trim — the same honest-but-unhelpful-navigability defect class as the
fixed instance, not a fabrication (B.10-compliant: it says "unknown," it does not invent a
plausible-but-wrong tool name). **Lines (grep-confirmed, 2026-07-23):** 440, 491, 700, 842, 894,
936, 1007, 1138, 1161, 1197, 1209, 1221, 1233, 1245, 1257, 1269, 1309, 1416, 1479, 1495, 1509,
1583. **Not fixed this session** — none of the 22 was live-reproduced as actually broken (their
auto-trim path may not have fired on the calls made this session), and bulk-auditing/fixing all
22 exceeds this fix-cycle's "one-line schema/trim-config fix" ceiling. **Recommendation:** a
future pass should either (a) live-probe each of the 22 to confirm which actually trigger
auto-trim and pass `toolName` at those sites, or (b) more robustly, change
`autoDetectTrimmableSections`'s call sites in bulk to always pass the tool name, closing the
whole class at once rather than one call site at a time. Evidence: `RESOLVER_RULINGS.md` Ruling
RC-04-002 §"Scope note."

---

**CR-125 [RESOLVED 2026-07-23, RC-17 (web-door dasha-anchoring hallucination) fix session, branch
`res/rc02-rc17-web-door-parity-and-dasha-fix` — discovered by RC-02's live two-door parity
investigation (2026-07-22), independently live-reproduced this session, chart 1c826d5a, via the
deployed `/api/chat/consult` route]:** the web-door synthesis text stated the native was running
"Mercury MD / Saturn AD" while the SAME response's own `data-orientation.chart_header.
current_maha_antar` (and the MCP `prashna_ask` door, for the same chart/question) both correctly
said "Saturn MD / Rahu AD" — a fabricated Mahadasha lord asserted directly to the caller about
their own timing. Root cause: `run_adapter_dispatch.ts`'s `systemContent` assembly never included
the resolved `current_maha_antar` or today's date at all, so the synthesis model had no way to
know which of the many raw dasha periods returned by the B.11 dasha-context floor tool is CURRENT
and reasoned from training-data recency/pattern-bleed instead — the identical defect class fixed
for the MCP `prashna_ask` synthesis path in commit `2df42b61` (W6.3 fix-cycle,
`prashna_ask_synthesis.ts`'s `formatTemporalAnchor`), independently surviving on the web door
because that fix only touched the MCP file. Fixed with the equivalent pattern
(`formatConsultTemporalAnchor` + `buildConsultSystemContent`, wired into `systemContent` ahead of
the B.11 floor bundle, sourced from the orientation block already resolved earlier in the request —
no new fetch needed; degrades honestly, never fabricating a period, when `current_maha_antar` is
unresolved); regression test `rc17_temporal_anchor.test.ts` (8 cases, all passing) proves the
anchor is built correctly and is actually wired into the text the synthesis model receives,
including an explicit regression guard against the exact live symptom (a different dasha lord
silently substituted). Live-reproduced pre-fix twice: the original RC-02 investigation (query_id
`05baeb74-6c7f-4d6b-ab57-9578e57ab083`, 2026-07-22) and an independent re-reproduction this session
(query_id `86d2f98e-1f8c-4f73-90b2-6fc1fd1e9d41`, 2026-07-22 22:43 UTC, deployed revision
`amjis-web-01103-nq7`) — both show the identical orientation-vs-synthesis contradiction. Post-fix
live re-probe of the deployed (fixed) web door is deploy-gated — same carry-condition class as
CR-118/RC-11 (`VERIFY_RC-11.md` §5) — recommended for Wave R-C after batched deploy. Full detail:
`RC-17_WEB_DASHA_HALLUCINATION_v1_0.md`. (Numbered CR-125, not CR-122 as this fix-cycle's own
branch history initially had it — CR-122 collided with RC-04's unrelated `phala_anchors_get`
finding, which merged to `main` first; renumbered during integration, no content change.)

---

*End of MARSYS_DEFECT_GAP_REGISTER. Changelog: v3.13 (2026-07-23, RC-02/RC-17 web-door-parity-and-
dasha-fix session, branch `res/rc02-rc17-web-door-parity-and-dasha-fix`) — CR-125 added and
RESOLVED same-session: web-door (`/api/chat/consult`) synthesis dasha-anchoring hallucination,
discovered by RC-02's live two-door parity investigation, live-reproduced twice, fixed with the
`prashna_ask_synthesis.ts`/`2df42b61` temporal-anchor pattern ported to `run_adapter_dispatch.ts`;
regression test added. Full detail: `RC-17_WEB_DASHA_HALLUCINATION_v1_0.md`. RC-02 CLOSED via
Native-Proxy Resolver Ruling RC-02-001 (`RESOLVER_RULINGS.md`) — DONE bar narrowed to
shared-condition gate-flag parity (fixed, `judgment_flags` aggregation wired into
`/api/chat/consult`) + measured floor-coverage improvement (2/16→8/16, RC-11 consequence); full
receipt-schema/item-set equality WONTFIX'd as a genuine architectural difference between the two
doors, not a defect.
v3.12 (2026-07-23, RC-04 fix-cycle closing
`VERIFY_RC-04.md` clauses 2-3) — CR-122 added OPEN (`phala_anchors_get` date_range 422 regression:
MCP schema says optional, live sidecar now hard-requires it, contract drift since W0, not caller
error); CR-123 added OPEN (`ref_yogas_get`/`ref_doshas_get` now uncapped at 87KB/61KB as their
underlying catalogs grew past 100 rows, no `response_budget.ts` trim coverage unlike their three
sibling tools). Both discovered by `PROBE_DIFF_v2_0.md`'s live RC-04 re-run and independently
reproduced by the RC-04 verifier (`VERIFY_RC-04.md`); neither fixed in this fix-cycle per its own
bounded measurement-not-remediation scope — recorded per §G so they are not silently dropped.
CR-124 added OPEN (22 unaudited `dualOutput(data)` sibling call sites in `register_p1_aliases.ts`
sharing the `phala_outlook_get`/`unknown_tool` defect class this fix-cycle's drill-crawl found and
fixed at its one live-confirmed site — named residual, not silently absorbed into a false
"drill-crawl clean" claim; see Ruling RC-04-002).
v3.11 (2026-07-23, RC-11 / R-10 root-cause-closure
session, branch `res/rc11-cr118-fastfails`) — CR-118 RESOLVED: root cause found (consult/route.ts's
`LegacyQueryPlanShape` never carried `chart_id`, so every per_chart tool it dispatched — msr_sql,
get_yoga_firings, cgm_graph_walk — hit its own `chart_id is required` fast-fail guard before any DB
round-trip, matching the documented single-digit-ms error/empty SSE pattern exactly); fixed
(chart_id threaded onto the queryPlan literal + shared QueryPlan type); same bug class
independently found and fixed as defense-in-depth in `/api/mcp/primitives/[tool]/route.ts` (the
MCP sidecar's surgical-primitive HTTP surface, not itself confirmed as CR-118's origin but
carrying the identical defect); 2 regression test files (1 new, 1 extended, 4 total new cases)
added and confirmed to fail pre-fix / pass post-fix; live-verified healthy on the deployed
`prashna_ask` MCP path and direct MCP primitive calls (chart 482012f1); `/api/chat/consult` itself
not independently re-probed live post-fix (no browser/session-cookie tool available this
session) — flagged as an honest residual, not claimed as verified. v3.10 (2026-07-22, D-4b permission-bridge lane,
`wave/D-4b/permission-bridge`) — CR-120 and CR-121 added NOT-EVALUABLE (coverage gap, not a
retirement): midpoint-triangle's mandatory-baseline role in B-1's bakeoff passes to the mirrored
shuffled-birth controls (native ruling, this session); transit-kernel's D-3 RED result stands as
NOT-RE-EVALUATED-ON-REPAIRED-SUBSTRATE, its re-evaluation registered as a named D-6-era candidate
item once the 2.0 sweep engine subsumes its physics. Neither model's code/doctrine is removed. v3.9 (2026-07-21, D-4b formal-open recording
session, `wave/D-4b/open`) — CR-119 added OPEN (drift finding: commit `ae9457d2`'s
"D-4b confirmed actively executing" claim independently disproven via `git branch -a`/`gh pr list`
showing zero `wave/D-4b/*` branches or PRs at the time; annotated, not reverted). v3.8 (2026-07-21, W4 post-deploy live-probe) —
CR-118 updated: the fast-fail tool-error pattern reproduces on 3 tools (msr_sql,
get_yoga_firings, cgm_graph_walk), not just msr_sql, and 2 of the 3 are floor-adoption's own
web-bridge tools — widens the defect's scope, still out of W4, still deferred to W5/PF-1. v3.7 (2026-07-21, W4 conductor session) — CR-118
added OPEN (msr_sql mid-stream tool error, live-probed during the bundle_hydrator fix
verification; out-of-scope for W4 per native ruling, deferred to W5/PF-1). v3.6 (2026-07-21, pre-D-4b readiness pass v3,
conductor session) — CR-113 CLOSED (re-verified no orphaned build_runs rows exist); CR-114 CLOSED
(re-verified all three deployed services code-current with origin/main); CR-116 added and CLOSED
(ka_gochara_sweep throughput defect, root-caused + fixed via correctness-preserving memoization,
PR #670 — residual noted: full materialization still pending, multi-dispatch-cycle); CR-117 added
and CLOSED (cockpit badge-honesty defect, new `partial` state, PR #671); NEW assertion class
registered (materialization-completeness precedes gate/scoring, encoded in BRIEF_D4B.md §0).
CR-116/117 numbered above CR-115 to avoid collision with v3.5's CR-115 (this changelog entry was
authored concurrently with, and merged after, the v3.5 stash-triage entry below, which had already
claimed CR-115 for an unrelated defect).
v3.5 (2026-07-20, stash-triage close-out session)
— CR-115 added OPEN (record_outcome/phala_anchors schema drift, PG-2 Lane X-5; owned by PF-1's
remaining scope per the native's PF-1/W4 re-scope ruling). Frontmatter `version` corrected 3.2 →
3.5 (had drifted out of sync with this changelog's own tail, which already read v3.4 — a
pre-existing B.8 desync, fixed in place, not introduced by this entry). v3.4 (2026-07-19, pre-D-5 readiness pass,
conductor session) — CR-109/110/111 CLOSED (all three fixed + independently verified in D-4a
Lane A-0, re-spot-checked live this session); CR-112 added and CLOSED (item #3 native
correction, mis-quarantined in D-4a, fixed this session); CR-113/CR-114 added OPEN, carried to
D-5 with named Binder disposition points in BRIEF_D5.md §B.5 (orphaned build_runs row; stale
mcp/sidecar image SHAs ahead of upcoming D-5 sidecar-code lanes). v3.3 (2026-07-18, D-3 closeout directive,
conductor session) — CR-109 pointer added (served activation-window coverage gap,
`resolve_activation_windows()` primary_selected collapse, A2/FIX-COV correct-STOP transferring
to D-4 Lane C-0(a); native-ratified disposition recorded on this row per closeout directive item
2). CR-110 (double dasha-spine bug in kala_temporal_bundle, native-reported, unverified intake)
and CR-111 (convergence-windows build-vs-serve gap, native-reported, unverified intake) added as
Lane C-0(b)/(c) — both explicitly flagged NOT YET INDEPENDENTLY VERIFIED, per closeout
directive item 3's single consolidated C-0 candidate-scope entry. v3.2 (2026-07-18, D-3
cycle-2b, conductor session) —
CR-108 pointer added (predicate-selection dignity_score saturation + insertion-order tiebreak
starving Mode A/B on 482012f1; halt-and-report MEMO_D-3_1.md, native-dispositioned Option-C-amended
fix lane, raw finding text kept in the doctrine-wave artifacts per the CR-90..107 convention). v3.1
(2026-07-16, D-1.6 Lane S-8) — Section 13 added:
governance/register reconciliation sync. 10 rows closed/routed/re-dispositioned with S-7 Binder
probe evidence (S-4, S-5, S-12, S-14, R-11, R-47, R-48, D-5, K-3, KP-4); R-48 specifically
RE-DISPOSITIONED from a false REMEDIATED-PENDING-W4 to honestly PENDING with a code-verified root
cause (capability registered in the internal catalog, never wired into an MCP tool file) —
EXCLUDED-to-D-2 with pointer, not silently carried as closed. §E CR-33..38 permanent-ID assignment
table (CR-33=Y-12, CR-34/35 confirm Y-3/Y-4, CR-36 cross-ref only, CR-37 confirms T-4, CR-38
READING-NOTES/no-ID). CR-90..107 range confirmed resolved (system-of-record = EXECUTION_PLAN §8 +
doctrine-wave briefs, per POST_REMEDIATION §N pointer table) — no dangling row range. v3.0 (2026-07-10, same session) — FULL Total Audit
Protocol executed (TAP-4..9 all APPLIED; TAP-9 declaration §11.6): Section 11 added with 68 new rows
(M-1..22 method integrity, V-1..13 value/distribution, SC-1..22 seam conservation, P-1..11
instrument/lateral) + golden battery baseline (3/13/6) + adversarial baseline (0A/6D); prioritization
rebuilt as the 6-phase implementation plan (Phase 0 hotfix → 1 computation truth → 2 composition →
3 serving → 4 prediction → 5 verification harness) designed for sub-agent parallel execution; v2
wave plan retained as superseded record. Evidence artifacts: GOLDEN_SIGNALS_482012f1_v1_0.yaml,
TOTAL_AUDIT_PROTOCOL_v1_0.md, DISCOVERY_ENGINE_ACCURACY_TEST_v1_0.md. v2.3 (2026-07-10, same session) —
KP forensic trace folded in: rows KP-1..KP-6 + Wave A″ with legacy-parity acceptance witness
(FORENSIC v6.0 §4 KP.CUSP.11 / KP.SIG.11). v2.2 (2026-07-10, same session) —
CGM chain-detection forensic trace (native's Mars+Rahu+Mercury→11H financial-fluidity chain) folded
in: rows G-1..G-8 + Wave A′ with chain-surfacing acceptance witness. v2.1 (2026-07-10, same session) —
discovery-engine blinded accuracy test folded in: rows T-12..14, D-15..20, C-5 added; Section 10
accuracy baseline + Wave-C exit gate added; evidence artifact DISCOVERY_ENGINE_ACCURACY_TEST_v1_0.md.
v2.0 — full-estate five-lane audit (Fable-5): all v1 rows re-verified (2 FIXED, 4 PARTIAL, rest
confirmed with root causes pinned to file:line), 45 new rows added (Y-7..12, S-12..15, T-4..11,
R-8..29, D-1..14, K-1..8, O-5..7, C-4), prioritization rebuilt into hotfix band + 4 waves.
v1.0 (2026-07-09) superseded, retained in place.*
