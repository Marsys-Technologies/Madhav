---
canonical_id: MARSYS_DEFECT_GAP_REGISTER
version: 1.0
status: SUPERSEDED by MARSYS_DEFECT_GAP_REGISTER_v2_0.md (2026-07-10 full-estate audit — all rows
  carried forward with re-verified statuses + 45 new rows). Retained in place per hygiene §A.
  Do not add rows here; the living register is v2.0.
created: 2026-07-09
author: Cowork (Opus) — compiled from: Fable-5 yoga-coverage audit (2026-07-09), native hand-analysis of
  chart 482012f1 (vargottama + NBRY, 2026-07-09), Cowork live MCP testing across both native sessions
  (2026-07-07 + 2026-07-09), and the R5/R5.1/R5.2/R5.3 seal + punch-list records.
scope: the whole instrument — L0–L5 build assets, retrieval/serving, MCP, prediction infra. Native's two
  test charts: 482012f1 (Abhisek, calibrated) · 1c826d5a (Abhinandan, structural).
purpose: feed the R6 "Yoga & Cancellation Integrity + Coverage" campaign and its successors. This register
  IS the backlog; the campaign briefs draw their scope from it.
---

# MARSYS DEFECT & GAP REGISTER v1.0

## Legend
**Gap type:** `DATA` never computed · `PERSIST` computed but not stored · `SURF` stored but not served
(or served unlabeled) · `LOGIC` computed/served but WRONG · `INFRA` service/deploy · `UX` tool-contract
ergonomics · `DOC` description over-claims coverage.
**Severity:** `CRITICAL` serves fabricated/wrong astrology on the most common questions · `HIGH` material
astrological miss or blocks a core capability · `MED` real gap, moderate reach · `LOW` edge/polish.
**Status:** `OPEN` · `IN-PROGRESS` · `FIXED` (with evidence) · `PARTIAL`.

---

## SECTION 1 — YOGA & CANCELLATION INTEGRITY (the crisis; Fable-5 audit 2026-07-09)
*The layer users touch first is the weakest. Highest priority block.*

| ID | Title | Gap | Sev | Evidence (file:line / probe) | Fix approach | Status |
|----|-------|-----|-----|------------------------------|--------------|--------|
| Y-1 | **Vacuous-pass fabricated yoga surface** — `ganita_yogas_get`→`yoga_label` fires the ENTIRE OCR-harvested catalog as `requires_pass`, incl. garbage names (`cnja_kesari`,`dariclra`,`kimadruma`) + contradictory pairs (Kemadruma AND Gaja-Kesari together) | LOGIC+SURF | CRITICAL | `ga_structural_writer.py:4535` returns `True,"requires_pass"` for unevaluable rows; live prod probe of native | Kill the vacuous pass: unevaluable rule → NOT fired (or floored explicit). Stop serving fabrication FIRST (hotfix). | OPEN |
| Y-2 | **Honest yoga engine unwired** — `ga_yoga_firings` (real eval + constituent fact_ids + bhanga honesty) is read by ZERO retrieval/MCP tools | SURF | CRITICAL | grep `ga_yoga_firings` in `platform/src/lib/retrieval` + `platform-mcp/src` = 0 hits | Wire `ga_yoga_firings` into retrieval + MCP; retire/replace the `yoga_label` surface | OPEN |
| Y-3 | **Neecha Bhanga Raja Yoga effectively absent** — 5 classical rules, ~1 half-built (D1-only, lagna-only, dispositor branch). Native's Sun-in-D9-kendra case structurally invisible | DATA+LOGIC | CRITICAL | catalog `l0_yogas.py:731-744`; skip-list `ga_yoga_writer.py:936-973`; dead legacy `ga_structural_writer.py:~1726`; native chart: `neecha`/`bhanga` keyword = 0 facts | Build a real bhanga evaluator over catalog `bhanga_any`, all 5 rules, PER-VARGA (D9+). | OPEN |
| Y-4 | **House-lord yoga family undetected** — Viparita (Harsha/Sarala/Vimala), Dhana, Kendra-Trikona Raja, Dharma-Karmadhipati, Daridra, Kala-Sarpa (relation), Shakata: skip-listed in ga_yoga, `relation_unimplemented` in catalog evaluator; "fires" seen are the Y-1 echo | DATA+LOGIC | HIGH | `ga_yoga_writer.py:936-973`; `ga_structural_writer.py:4522`; real logic dead in legacy `YOGA_LIBRARY:254-320` | Real relation-evaluator for the ~30 house-lord relations (or revive+correct legacy) | OPEN |
| Y-5 | **Cancellation as a class is unimplemented** — only Kemadruma has bhanga eval; `cancellation_conditions`/`weakened_if`/`bhanga`/`excluded` catalog columns are dead documentation | DATA | HIGH | `ga_yoga_writer.py:1179-1191` (bhanga_active=NULL all but Kemadruma); `l0_yogas.py:715,727,899,909` | Generic cancellation-evaluator consuming the catalog condition columns for every yoga | OPEN |
| Y-6 | **D9 cross-check blind to cancellation** — classifier is pure `d1_tier×d9_tier`→"broken_promise"; hardcodes `neechabhanga_modifier=1.0`,`cancellation_modifier=1.0`; the 1.3 salience bhanga boost is never fed | LOGIC | HIGH | `bo_laksana.py:1288-1345,1417-1418`; `bodha_writers/formulas.py:110,154` | Cross-check consults Y-3/Y-5 bhanga result before emitting "broken_promise"; feed the boost | OPEN |

## SECTION 2 — ASTROLOGICAL SURFACING & COVERAGE GAPS (Fable-5 Track C + native catches)
*Substrate is computed to a high standard; the shopfront doesn't serve it.*

| ID | Title | Gap | Sev | Evidence | Fix approach | Status |
|----|-------|-----|-----|----------|--------------|--------|
| S-1 | **Vargottama / special-states not joined into judgment surfaces** — `graha_special_state_rollup` (is_vargottama/combust/retro/exalted/debil) computed but never joined into `judgment_query` kāraka block or `graha_portrait`. Native's Mercury (only vargottama graha) served as "weak" | SURF | HIGH | `register_d9_judgment.ts:115-168` (only dignity+shadbala); `graha_portrait.ts:158` include-enum has no special_states; rollup built `ga_structural_writer.py:2655-2695` | ONE `getGrahaSpecialStates()` helper joined into (1) gradeGraha, (2) new `special_states` portrait section | OPEN |
| S-2 | **Special lagnas mis-aliased** — `special_lagna` (HORA/GHATI/VIGHATI/BHAVA) computed but `query_special_lagnas`→get_sensitive_points whose `SP_CATEGORIES` OMITS `special_lagna`; the tool named for it cannot return it | SURF+LOGIC | MED | `ga_sensitive_writer.py:2055`; `tool_name_bridge.ts:60`; `get_sensitive_points.ts:13-17` | Add `special_lagna` to the served category set; fix the alias target | OPEN |
| S-3 | **Bhava arudha (full 2-exception Parashari + AL/UPA labels)** computed, unserved — only simplified `arudha_pada` reaches users | SURF | MED | `ga_sensitive_writer.py:1324`; zero refs in layers/*.ts | Serve the full arudha set (AL, UL/Upapada, A2–A12) | OPEN |
| S-4 | **Graduated aspect strength (sputa drishti / drishti pinda, 60-virupa)** not computed — only `drik_bala` approximation | DATA | MED | `ga_strength_writer.py:182` | Compute virupa-graded drishti | OPEN |
| S-5 | **Gandanta** computed, unserved (48′ orb + severity) | SURF | MED | `ga_nakshatra_emitters.py:187`; no tool lists `graha_gandanta` | Add to a served category | OPEN |
| S-6 | **Pushkara navamsha/bhaga flags** computed, in no tool enum | SURF | LOW-MED | `ga_vargas_writer.py:292-293` | Add to served categories | OPEN |
| S-7 | **Per-varga siblings unserved** — `graha_avastha_*_per_varga`, `graha_yuddha_per_varga`, `aspect_parashari_per_varga`, `ashtakavarga_*_per_varga` computed; not in the corresponding tools' category enums (vargottama_per_varga is the lone exception, in get_dignity) | SURF | MED | explorer sweeps; `get_ashtakavarga.ts:10-13` | Add per-varga categories to tool enums / a per-varga facet | OPEN |
| S-8 | **Effective dignity claim ≠ computation** — served desc claims "neechabhanga + rashi-drishti cancellation"; actual is a 15°-orb conjunction ±0.25 tweak | LOGIC+DOC | MED | `ga_structural_writer.py:2700-2731` vs `get_dignity.ts:25` | Either implement the claim or correct the description (canonical-or-floor) | OPEN |
| S-9 | **Mrityu bhaga (fatal-degree doctrine)** not computed (the `esoteric_point_mrityu` upagraha is a different concept) | DATA | MED | explorer sweep; prod `mrityu_bhaga_dosha` label = suspect catalog pass (Y-1) | Compute mrityu-bhaga per graha | OPEN |
| S-10 | **Indu lagna / Sree lagna / Varnada lagna** absent from production (Sree/Varnada only in an L0 prototype) | DATA | LOW-MED | `brahmagyan/ganita/l1_sensitive_points.py:229` (prototype only) | Promote to production writer | OPEN |
| S-11 | **Tool descriptions over-claim coverage** — `register_p1_ganita.ts:245,349` advertise Viparita/Neecha-Bhanga/Parivartana; `get_dignity.ts:25` advertises bhanga | DOC | MED | those lines | Honesty pass on all tool descriptions (only claim what runs) | OPEN |

## SECTION 3 — PREDICTION / TIMING INFRASTRUCTURE (the structural→dated-prediction gap)
*Native-flagged explicitly. This is what separates "reads the chart" from "predicts an event."*

| ID | Title | Gap | Sev | Evidence | Fix approach | Status |
|----|-------|-----|-----|----------|--------------|--------|
| T-1 | **Ephemeris/transit sidecar dark → PACT TRIGGER stage never completes.** `pact_query` stage 4 returns "Ephemeris sidecar unreachable or returned no rows — transit-gate check not completed." So every dated prediction stops one stage short of the transit trigger — the honest-but-incomplete forecast | INFRA+DATA | HIGH | this session's `pact_query(career, as_of 2027-09-01)` TRIGGER stage; conv-1 `phala_outlook` PH-4-1/PH-4-2 SQL errors + empty windows | Restore/repair the transit/ephemeris compute service; wire full sidereal vedha/aspect transit gating into the TRIGGER stage | OPEN |
| T-2 | **Forward panchanga empty → election/muhurta honest-empty.** `panchanga_daily` was a stub view; muhurta/auspicious-windows return empty-with-reason | INFRA+DATA | HIGH | conv-1 `phala_outlook` `auspicious_windows:[]`, `panchanga_daily rows_returned:0`; R5.1 C3 rebuilt the table but forward-population job pending | Verify R5.1 panchanga table live; ensure rolling +12mo forward-population job runs; confirm muhurta consumes it | PARTIAL (R5.1 C3 built table; forward job = R5.1 punch) |
| T-3 | **Activation-window boundary imprecision** — `pact_query` as_of 2027-09-01 cited the just-expired Mercury MD (ended 2027-08-18) as "active_now" instead of Ketu MD | LOGIC | MED | this session's pact_query ACTIVATION stage | Fix dasha-boundary selection to the period actually containing as_of_date | OPEN |

## SECTION 4 — RETRIEVAL / SERVING QUALITY (live-test observations, both sessions)

| ID | Title | Gap | Sev | Evidence | Fix approach | Status |
|----|-------|-----|-----|----------|--------------|--------|
| R-1 | **Budget/trim not universal** — composite tools trimmed (R5.1) but raw `ganita_chart_facts_get` (D9 pivot 116KB), `query_remedies` (106KB single row), and others still blow the ~25KB MCP ceiling | SURF/perf | HIGH | this session D9-pivot 116KB error; R5.3 §B3 query_remedies | Extend budget facet estate-wide (R5.3 B3 covers query_remedies; generalize) | IN-PROGRESS (R5.3) |
| R-2 | **Epistemic grade not derived** — v3 envelope `epistemic` block defaults to "no epistemic signal computed" on judgment/portrait/pact | LOGIC+SURF | MED | this session's 3 flagship calls | Derive epistemic grade (§10.2 vocabulary) per response | OPEN |
| R-3 | **`percentile_within_class` flat = 1** in served ranking rows (degenerate) | LOGIC | MED | this session bodha_signals + digest; R5 punch | Populate/serve real within-class percentile (stored mig-393 col) | OPEN |
| R-4 | **Stale provenance-note literals** — responses still assert "DEFECT-001 OPEN 91.5% orphan" + "signature_tier 100% background" which are FALSE post-R4 | LOGIC | MED | this session bodha_signals provenance block | E-2 freshness contract: notes become data w/ as_of/expires_on, re-derived from live counts | OPEN |
| R-5 | **Denial ≠ empty** — entitlement denial not distinct from empty result (Ring-3 R5.2) | LOGIC | MED | R5.2 Ring-3 | Distinct denial envelope state on every instrument | OPEN |
| R-6 | **graha_portrait include-enum ergonomics** — rejects sensible values (`functional`,`strength` combos), no `special_states` option (see S-1) | UX | LOW | this session's graha_portrait param error | Widen/clarify enum; add special_states | OPEN |
| R-7 | **Digest family-aggregation** — top band still shows near-duplicate family rows (partly E-6) | LOGIC | LOW-MED | this session digest | Complete hierarchical family aggregation | PARTIAL (E-6/R5.1) |

## SECTION 5 — SECURITY / OPS / INFRA

| ID | Title | Gap | Sev | Evidence | Fix approach | Status |
|----|-------|-----|-----|----------|--------------|--------|
| O-1 | **Rate limiting absent on MCP surface** (Ring-3 R5.2) | INFRA | MED | R5.2 Ring-3 | Add rate limiting | OPEN |
| O-2 | **`amjis-pending-stream-reaper` silent 401** — Cloud Scheduler `Authorization` header doesn't survive to `*.run.app`; job silently failing (found R5.2 A4) | INFRA | MED | R5.2 A4 | OIDC-token fix (same pattern as the 2 new schedulers) | OPEN (R5.3 §S) |
| O-3 | **Capability-route entitlement** — closed in R5.2 A1 (per-call chart entitlement on `/api/retrieval/capability`) | INFRA | — | PR #498 | — | FIXED (R5.2 A1) |
| O-4 | **Grader model-name fragility** — pinned `gemini-2.5-flash` 404'd, silently fell back to DeepSeek; fixed to rolling alias | INFRA | — | R5.3 §B, `llm_grader.ts:49` | — | FIXED (R5.3 §B) |

## SECTION 6 — CONTENT-DEPTH / ACCEPTANCE (R5.3 in flight)

| ID | Title | Gap | Sev | Evidence | Fix approach | Status |
|----|-------|-----|-----|----------|--------------|--------|
| C-1 | **16 below-floor rubric battery items** (Q2/Q3 judgment, Q5 prediction, Q7 reading, Q8 remedy, Q9 verification) | LOGIC/depth | HIGH | R5.2 §A5 register; R5.3 B2 | Per-item Pratinidhi-R ruling + serving-synthesis depth | IN-PROGRESS (R5.3) |
| C-2 | **D60 rectification-confidence / time-sensitivity note** (§31.4 ladder) not served | SURF | MED | R5.3 §B3 | Serve time_sensitivity grade per varga fineness × rectification confidence | IN-PROGRESS (R5.3) |
| C-3 | **Acceptance gate un-met** — first true rubric-graded run pending (R5.2 was deterministic-only; grader restored R5.3 §B) | process | HIGH | R5.3 §B1 | Full graded battery ≥90% after fixes | IN-PROGRESS (R5.3) |

## SECTION 7 — RESOLVED (audit trail; do not reopen without cause)
- 17MB/63KB oversized payloads on flagship composites → budget-trimmed (R5.1 C1; v3 ≤12KB verified live this session).
- `as_of_date` ignored by get_dashas → fixed (R5.1/R5.2; verified live this session: current-dasha 1 row).
- Phala serving SQL vs mig-330 (`id`/`theme`/`anchor_id`) → addressed (R5.1/R5.2).
- Chart-header frame safety (D1-misread class) → structurally fixed (every v3 response carries correct header; verified live).
- muhurta_finder fabricating placeholder panchanga on broken column → fixed to real-or-empty (R5.1 C3).
- Native chart Bodha staleness (salience_pctl/typed-edges) → healed by R4 rebuild (digest now 153-distinct salience, trap1=0).

---

## PRIORITIZATION FOR THE R6 CAMPAIGN (recommended sequencing)
1. **HOTFIX (days):** Y-1 (kill fabricated yoga fire) — stop serving wrong astrology immediately. It is actively misleading on the most common question.
2. **R6 Wave A — Yoga & Cancellation core:** Y-2 (wire honest engine), Y-3 (NBRY, all rules, per-varga), Y-4 (house-lord family), Y-5 (cancellation class), Y-6 (D9 cross-check consults bhanga). This is the heart.
3. **R6 Wave B — Surfacing:** S-1 (special-states join — one helper, high value), S-2/S-3/S-5/S-7 (serve computed-but-hidden), S-8/S-11 (honesty on descriptions).
4. **R6 Wave C — Prediction infra:** T-1 (ephemeris/transit — unlocks real dated prediction), T-2 (forward panchanga job), T-3 (activation boundary).
5. **Fold-in (already moving):** R5.3 finishes C-1/C-2/C-3 + R-1; R-2/R-3/R-4/R-5 (serving honesty) batch with Wave B.
6. **Ops tail:** O-1, O-2.

**Bottom line:** the Gaṇita substrate is deep and correct; the defects cluster at the interpretive/serving layer and in one systematic blind spot — cancellations/redemptions. Fixing Section 1 + S-1 + T-1 converts the instrument from "reads facts, fabricates yogas, stops before the trigger" to "reads facts, detects yogas honestly with cancellations, and predicts to the transit." That is the acharya-grade finish line.
