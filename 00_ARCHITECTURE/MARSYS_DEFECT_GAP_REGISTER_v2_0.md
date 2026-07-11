---
canonical_id: MARSYS_DEFECT_GAP_REGISTER
version: 3.0
status: LIVING — the authoritative, exhaustive register of every known defect + coverage gap in the
  MARSYS-JIS instrument as of 2026-07-10. Add rows, never silently drop them. Each row closes only with
  a fix PR + [verify-against] evidence recorded in the Status/Evidence column.
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
| S-4 | **Graduated sputa drishti not computed** | DATA | MED | **APPEARS-FIXED — RECLASSIFY** [concept]. `_build_virupa_drishti_rows` exists (ga_structural:5326), unit `virupa_strength`, per-varga. Verify served, then close. | PARTIAL (verify+close) |
| S-5 | **Gandanta computed, unserved** | SURF | MED | **APPEARS-FIXED** [concept]. `graha_gandanta` per graha + lagna confirmed live via MCP (all false for 482012f1 — legitimately). Verify category is in a tool enum permanently, then close. | PARTIAL (verify+close) |
| S-6 | **Pushkara flags in no tool enum** | SURF | LOW-MED | **VERIFIED-STILL-OPEN** [concept]. PUSHKARA tables coded (ga_vargas_writer.py:162-169), stored in chart_divisionals; keyword+category MCP probes → 0 rows. Subsumed by S-12 (divisional serving hole). | OPEN |
| S-7 | **Per-varga siblings unserved** | SURF | MED | **STILL-OPEN** (partially subsumed by S-12). `aspect_jaimini_per_varga` verified live-served; the avastha/yuddha/ashtakavarga per-varga siblings remain outside tool enums. | OPEN |
| S-8 | **Effective dignity claim ≠ computation** | LOGIC+DOC | MED | **CONFIRMED, WORSE** [code]. Computation (ga_structural:2699-2719) is a 15°-longitude-proximity ±0.25 tweak — not drishti at all (no 7th-house, no special aspects, no rashi drishti, no bhanga) vs get_dignity.ts:25 claim. Adjacent bug: `dignity_scores` map (:2717) lacks `own`/`moolatrikona`/`friend`/`enemy` keys → those states silently score neutral 0.5 (split as D-8). | OPEN |
| S-9 | **Mrityu bhaga not computed** | DATA | MED | **CONFIRMED** [concept]. L1 computes mrityu *sphuta* (`esoteric_point_mrityu`) — a different concept; no per-sign fatal-degree proximity flag found. | OPEN |
| S-10 | **Indu/Sree/Varnada lagnas prototype-only** | DATA | LOW-MED | **PARTIALLY FIXED** [concept]. ga_sensitive now computes Indu, Hora Lagna, Pranapada + ghati/varnada family; `ganita_special_lagnas_get` computes the full PyJHora set on demand. Residual = S-2 serving gaps. | PARTIAL |
| S-11 | **Tool descriptions over-claim** | DOC | MED | **CONFIRMED** [code]. register_p1_ganita.ts:244-248 (condition: "neecha-bhanga/vargottama" — neither in served categories); :346-357 (yogas: "Viparita, Neecha Bhanga, Parivartana" — none can fire per Y-1/3/4); get_dignity.ts:25. | OPEN |

### New rows (v2)

| ID | Title | Gap | Sev | Evidence | Fix approach | Status |
|----|-------|-----|-----|----------|--------------|--------|
| S-12 | **Divisional-chart serving hole — 21,635 chart_divisionals rows MCP-invisible** — vargottama variants, pushkara, per-varga dignity, D108/D150/D2700 all computed; `divisional_query` registered in tool_name_bridge.ts:62 + get_divisionals.ts exists, but the tool is not on the live MCP surface; `query_chart_facts(divisional_chart=D9, category=varga_position)` → 0 rows. Any LLM reading raw D9/D10 placements over MCP must recompute | SURF | HIGH | [concept] live probes + code | Wire divisional_query/`ganita_vargas_get` into the MCP channel (the sealed≠served keystone, again) | OPEN |
| S-13 | **Coverage-matrix CI gate enumerates a stale hardcoded category snapshot** — the "every fact_category maps to ≥1 tool" R3 gate checks a list authored 2026-06-16; `special_lagna`, `bhava_arudha`, `sun_derived_upagraha` are absent from the list itself, so the S-2/S-3 class can never fail CI | SURF+DOC | HIGH | [code] platform/src/lib/retrieval/registry/layers/L1_ganita/coverage_matrix.ts:14+ | Derive the gate list from live `SELECT DISTINCT fact_category FROM chart_facts` (or writer manifests) at gate time — this one fix converts the whole S-family into CI failures | OPEN |
| S-14 | **ga_medical / ga_vastu have no direct MCP read tool** — computed (floors 45/40), reachable only via assess_health/apex_health (which are themselves broken per R-8) | SURF | LOW-MED | [concept] | Thin `ganita_medical_get` / `ganita_vastu_get` reads | OPEN |
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
| R-11 | **traverse_graph string-address DSL sliced to first character** — `about="lord_of(bhava 10)"` → `Could not parse address expression: "l"`; the R5 W2 documented gate example fails; object form works | LOGIC | HIGH | [probe-B] | Fix string-vs-array handling at the about/about_from/about_to normalization step | OPEN |
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
| KP-4 | **KP signals carry wrong domain tags** — bo_laksana `_DOMAIN_MAP` maps only `kp_cuspal_significators`→wealth; `graha_kp_lords` + `cusp_kp_lords` fall to the nakshatra default ["character","relationship"] — so Mars-in-Rahu's-star can NEVER surface in a wealth query; 81 kp signals exist as atomic restatements ranked 4,584-14,199 with cusp-longitude noise rows in the top | LOGIC | HIGH | [kp-trace] bo_laksana.py:313-381 | Add both categories to _DOMAIN_MAP with house-aware domain tags; suppress raw cusp-longitude rows from signal ranking | OPEN |
| KP-5 | **No serving instrument performs KP analysis** — judgment_query/apex_wealth are Parashari-only (0 kp references in register_d9_judgment.ts or the shastra map); the KP paradigm exists in signals only as one-row restatements. The legacy portal's headline capability (cuspal sub-lord verdict + significator table + dasha-lord convergence, cf. DEEP_ANALYSIS line 1866: "KP promise of 10H matters is DUE" under Mer MD/Sat AD) has no current equivalent | SURF | HIGH | [kp-trace] grep evidence | KP lens in judgment_query once KP-1..3 land: cusp sub-lord verdict + significator table + dasha convergence, composed from cited fact_ids | OPEN |
| KP-6 | **Pivoted chart_facts silently merges CUSP_10/11/12 across the two KP categories** — subject-padding inconsistency (`CUSP_01` padded, `CUSP_10+` not; category C unpadded) makes the pivot mask the authoritative star_lord (showed Rahu from the fake category over Mars from cusp_kp_lords). Sibling of the R-23/R-24 serving-shape family | SURF+DATA | MED | [kp-trace] observed pivot collision | Normalize subject naming across categories; pivot must never merge rows from different fact_categories under one subject | OPEN |

## SECTION 5 — DATA CORRECTNESS (new in v2 — defects invisible to per-row checks)

| ID | Title | Gap | Sev | Evidence | Fix approach | Status |
|----|-------|-----|-----|----------|--------------|--------|
| D-1 | **chart_dashas denormalized `lord_natal_nakshatra` WRONG** — Mercury MD row says "Shravana"; Mercury at 270.84° = Uttara Ashadha pada 2 (PyJHora + chart_facts agree); Shravana is the Sun's nakshatra — join/copy slip in the dasha writer's denormalization | DATA | HIGH | [probe-G] ganita_dashas_get, chart A | Re-derive denormalized lord columns from chart_facts at build; verifier cross-check `lord_natal_nakshatra == graha_position.nakshatra(lord)` | FIXED [verify-against: prod, R6 2026-07-10] |
| D-2 | **Sade Sati table: duplicate + pre-birth cycles** — CYCLE_1 & CYCLE_2 share end 1968-06-17 (16y before the 1984 birth); CYCLE_3/4 and 6/7 pairwise identical | DATA | MED | [probe-G] | Audit ga_sade_sati cycle enumeration; uniqueness constraint (chart, cycle_no, period_type); clip to lifetime | FIXED [verify-against: prod, R6 2026-07-10] |
| D-3 | **`graha_composite_state_classification` astrologically suspect** — Jupiter "debilitation_cancelled" while in OWN-SIGN Sagittarius D1 (9°47' Mula); Saturn at 22° Libra (deep exaltation) "neutral"; 8 of 9 grahas "neutral" (near-degenerate). This is the same column Y-3/Y-6 should consume — it must be fixed BEFORE being wired in | DATA+LOGIC | HIGH | [probe-G] chart A | Re-derive classification vs dignity facts; distribution check; then wire into Y-6 | OPEN |
| D-4 | **Tithi-shunya / nakshatra-shunya (dagdha rashis): coded, ZERO rows live** — `_emit_tithi_shoonya` (ga_panchanga_writer.py:636-666) silently skips when `pi.shoonya is None`; live chart has 0 rows in both categories despite Shukla Tritiya having defined shunya rashis — classic silent-skip | DATA | MED-HIGH | [concept] code+live | Populate `shoonya` in panchang_engine or halt-warn on None; backfill on regen | OPEN |
| D-5 | **Digest entity attribution collapse — 299/300 signals "UNATTRIBUTED"** — both charts; per-graha entity profiles effectively empty though graha exists in configuration_jsonb of many rows (e.g. MOON on yoga labels) | DATA | MED | [probe-B] | Fix the attribution extractor to read configuration_jsonb.graha | OPEN |
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
| D-16 | **Discovery/anchor estate emits ZERO adverse-valence dated claims** — every anchor 1964–2030 is "elevated"/positive; 0/5 recall on the native's major negative events (father's death, scam, panic, employer crash, headache onset). Structural consequence of Y-2/Y-5 (dosha/bhanga signals never reach anchor generation) | DATA+LOGIC | HIGH | [accuracy-test 2026-07-10] §3 | Wire dosha/affliction signals into ph_nimitta event-type taxonomy; valence-distribution gate at seal (all-positive = collapse) | OPEN |
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
| K-3 | **Sarvatobhadra / Kota / Sudarshan chakras retired to archive, never rebuilt** — migrations 140/141/144 live only in `platform/migrations/_archive/`; SBC vedha tracking is mainstream transit practice | DATA | MED | [concept] | Rebuild as ka_gochara-adjacent SERVICE (deterministic grid + vedha lines from bg tables), not storage — per transit=service-not-storage ruling | OPEN |
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

*End of MARSYS_DEFECT_GAP_REGISTER. Changelog: v3.0 (2026-07-10, same session) — FULL Total Audit
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
