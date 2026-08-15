---
artifact: PARIPURNA_2_AUDIT_REPORT
version: 1.0
status: CURRENT (P5 complete; §6.3 awaits P6)
date: 2026-08-15
branch: audit/paripurna2-evidence
plan_of_record: /Users/Dev/shad_overnight/PARIPURNA_2_AUDIT_PLAN_v2_0.md
evidence_base: pp2-audit/manifest.json (141 findings, 125-tool census), pp2-audit/evidence/ (495 files)
---

# PARIPŪRṆA-2 — THE COMPREHENSIVE AUDIT REPORT

**Subject:** the elevated MARSYS-JIS instrument — code + data + the live MCP server —
audited end-to-end against the two ground-truth charts (`482012f1-710e-4a25-994a-93821f5871aa`,
the native, 64 LEL events; `1c826d5a-41cb-4450-b4dc-59d440e5f75a`, the zero-history comparison chart).

**What this document is.** The P5 deliverable of the six-phase PARIPŪRṆA-2 audit
(`PARIPURNA_2_AUDIT_PLAN_v2_0.md` §4). P0–P4 produced the evidence; this report consolidates it.
P6 (PARĪKṢAKA self-verification) runs after this document is written and appends its results to §6.3.

**Sourcing rule observed throughout.** Every claim below traces to a finding id (`F-nn`) in
`pp2-audit/manifest.json`, a defect class (`CL-nn`) in `pp2-audit/p4_defect_classes.json`, a
re-verification record in `pp2-audit/p4_prior8_reverification.json`, a residual row in
`pp2-audit/p4_residual_register.json`, or a named evidence file under `pp2-audit/evidence/`.
Where the audit did **not** measure something, this report says so in the same sentence rather
than inferring. Sections that report on the audit's own conduct (§5, §6) hold the audit to the
same standard it applies to the instrument.

**Headline, stated once, up front.** The instrument is **not flawless**. 114 of the audit's 141
findings assert a real defect; 25 of those are TIER1-CORRECTNESS. The single most consequential is
**F-110 (confidence laundering)**: for the identical chart, domain and date, one serving path
narrates a `tier_1_high` "≥70% convergence" marriage projection while another returns
`pact_status='denied_at_promise'` graded strong on 63 fact_ids — the two verdicts share five
fact_ids, and nothing reconciles them. Which answer a real person receives is decided by which
tool the consuming LLM happens to pick. Against that: the honesty machinery this project has built
is real and was repeatedly caught working (§4). It is unevenly installed, and that unevenness —
not an absence of discipline — is this audit's central structural result.

---

## §1 — LINEAGE SCOREBOARD

Every gap card (G1–G16) and every ruling (R17–R28) named in
`/Users/Dev/shad_overnight/GAP_REMEDIATION_MASTER_PLAN.md` and
`/Users/Dev/shad_overnight/MASTER_PLAN_IDENTITY_AND_PROMISE.md`, with a verdict and the specific
evidence that substantiates it.

**Verdict vocabulary.**
- **RESOLVED** — the card's own PROOF condition is met, evidenced.
- **PARTIALLY-RESOLVED** — some of the card's proof rungs are green, others are measurably not.
- **STILL-OPEN** — this audit measured the card's subject matter and found the condition unmet.
- **NOT-APPLICABLE-TO-THIS-AUDIT** — **no finding among the 141 addresses this card at all.**
  This verdict is a statement about the audit's coverage, not a pass for the card.

### §1.1 — Gap cards G1–G16

| Card | Verdict | Substantiating evidence |
|---|---|---|
| **G1 · CLOCKLESS FIELD** (keystone: wire stages 0–3; clocks>0; windows track the daśā ladder) | **PARTIALLY-RESOLVED** | The field is built and structurally sound on both charts: 25 event classes × full `[0, 36525]`-day horizon with zero segment-to-segment gaps at every decade seam (**F-75**), the 25×10 null grid exact (**F-76**), full-horizon coverage on both charts (**F-87**), and `field_content_hash` **independently recomputed and matched** over all 10,502,780 rows / 7 tables (**F-77**). `kala_field_windows` holds 31,350 rows and `kala_field_provenance` 1,839,618 rows for the native (`p4_prior8_reverification` #5). **But:** no finding measures `kala_field_clocks` / `kala_field_boundaries` row counts, and none tests PA-1's blind acceptance criteria (>1 window per clocked class; windowed fraction of horizon ≲20%; ≤45-day overlap and ≥5-year gap features computable). The build's completion signal is additionally **not earned** — `ka_kshetra` reads `state='lit'` alongside a non-empty `last_error` that explicitly denies promotion, set by manual repair after an OOM (**F-141**). MEASUREMENT #4 is not on record. |
| **G2 · 21/27 CLASSES FIELDLESS** (Tranche-3 sourcing; R23 T2/T3 tiers) | **PARTIALLY-RESOLVED** | Class coverage on the native chart is now **25 of 27** (**F-76**), a large advance on the 6 the card was written against; the comparison chart still builds only **6 of 27 declared**, with the other 21 honestly recorded in `skipped_classes` with reason `no_class_prior_row` (**F-78**). `kala_field_skill` carries six per-class rows plus a rollup (**F-140**). **But** R23's serving discipline is not built: the P3-b suppression the ruling depends on is implemented **in `ka_kshetra` only**, and four parallel surfaces invented their own permanent non-calibrated tags and then serve 4-decimal posteriors, confidence bands and 0–10 grades straight through with no suppression gate (**CL-08**: F-68, F-69, F-117, F-119, F-126). The T3 qualitative labelled response form does not exist as a first-class serving shape anywhere in the 125-tool census. No served-coverage dashboard was found or measured. |
| **G3 · CROSS-GENERATION INCOHERENCE** (full-DAG rebuild both charts; zero stale/error) | **STILL-OPEN** | Falsified directly. `mi_bhara` is in `state='error'`, `rows_written=0`, for the native chart (**F-71**, re-confirmed live `p4_prior8_reverification` #7, `last_built_at` 2026-08-13); for the comparison chart it is BLOCKED on `ka_kshetra`. Cross-generation incoherence is independently visible in served data: the built gochara windows' `term_breakdown.formula` is an **older formula string** carrying no `tara_modifier`/`w30_modifier`, i.e. these charts have not been rebuilt since those engine mechanisms landed (**F-21**). `ka_kshetra`'s own throughput row disagrees with reality by 566,545 rows (**F-141**). |
| **G4 · FOUR EMPTY W3 PLANES** (dispatch `bg_sarvatobhadra_grid`; moorti/tithi/kota/vedha populated *and consumed*) | **PARTIALLY-RESOLVED** | Two of the four planes are demonstrably populated **and consumed at the serving layer**: `kala_now_get`'s `kota_chakra`/`moorti_nirnaya` joins supplied "all the genuinely current-dated texture" in a whole-chart timing read (**F-136**). **But** no finding tests the four dedicated L3 query tools, the `bg_sarvatobhadra_grid` dispatch, or the tithi/vedha planes; and `transit_moorti` (per-ingress moorti-nirṇaya) remains `not_in_corpus`, recorded as BY-DESIGN-OPEN in the residual register. The card's before/after ELECT/AHEAD enrichment diff was not performed. |
| **G5 · DIGNITY-NOT-STRENGTH** (band = dignity × ṣaḍbala-ratio + combustion reducer) | **STILL-OPEN** | No evidence of the amendment being adopted, and the audit found the *input* vocabulary is itself defective one layer below it: the dignity classifier **never emits `moolatrikona` anywhere, chart-wide** — natal Jupiter at 9.79° Sagittarius (squarely inside its classical MT range) is served as `'own'` — systematically under-scoring Sthana Bala (MT=45 vs Own=30 ṣaṣṭyāṁśa) for any graha in its own MT range (**F-62**). Ṣaḍbala itself is reachable only by offset trial-and-error (**F-60**), and the one place a strength-modified band *is* computed — `bo_upaya`'s resonance — is plain inverse-ṣaḍbala with three constant terms (**F-117**). `assess_marriage` never surfaces the chart's exalted 7th-house Saturn at all (**F-113**). |
| **G6 · DEAD YOGA SLOT** (auxiliary-evidence band: firings / Jaimini incl. upapada+darakaraka / doṣa labels) | **NOT-APPLICABLE-TO-THIS-AUDIT** | No finding measures a per-class auxiliary-evidence slot being non-zero, and none names upapada or darakaraka. The slot's host is `bo_pratijna`, which **has 135 rows across 27 classes for the native chart and zero live MCP serving path** (**F-67**) — so the card cannot be verified from the served surface at all until that registration lands. Adjacent evidence that domain-bearing yoga evidence is unevenly wired: `assess_career` returns 2 CONFIRMED domain-bearing firings while `assess_marriage`/`assess_health` receive the "none name only this domain's bhāveśa/kāraka(s)" flag from the same 13 chart-wide firings (**F-124**). |
| **G7 · CONDITION COARSENESS + the R24 PORTAL AUDIT LANE** | **STILL-OPEN — and this audit executed the card's census** | The R24 portal census the card mandates was performed and **failed 3 of 4 surfaces**: `SPECIAL_DRISHTI_DEG` (primitives.py, feeds all three `gochara_*` tools) (**F-20**), `NB_GRAHA_DRISHTI` (ga_yoga_writer.py, Vipareeta dilution loop) (**F-19**/**F-64**), and the dead-but-latent `special` dict in ga_vargas_writer.py (**F-65**) all truncate Rahu/Ketu to the universal 7th, against this codebase's own correct `NODE_PARASHARI_ASPECTS={5,7,9}` in ga_structural_writer.py. **F-52** is the live, present-day instance: today Ketu's 5th aspect onto natal Venus (7th-lord + kāraka) and Rahu's 9th onto the natal 7th are both suppressed from this chart's own marriage windows. No doctrine-census CI gate exists. PA-3's corrected premise also holds: remedy intensity still does not consume condition magnitude — `kala_upaya_get`'s slate is 50% one duplicated non-remedy with `efficacy_tier` constant across all 100 rows (**F-118**). |
| **G8 · FIVE PROVISIONAL CLASSES** (author their KaryatvaMaps; `confidence_tier='karyatva'` ×5) | **NOT-APPLICABLE-TO-THIS-AUDIT** | No finding among the 141 addresses `confidence_tier='karyatva'`, the condition_malefic sets, or the 27-class uniqueness property test. As with G6, **F-67** means the promise layer that would carry the proof has no live serving path, so this card is currently unauditable from the user seat. |
| **G9 · REGISTRY↔ONTOLOGY DIVERGENCE** (reconcile; CI parity check) | **STILL-OPEN** | Measured and falsified. At least **four independent domain/enum vocabularies coexist unreconciled** — `CANONICAL_DOMAINS` (13), `SHASTRA_MAP` (10 concept-groups), `brahma_event_ontology.domain`, and the gochara window domain enum (**CL-04**) — and the divergence is bidirectional: `judgment_query` cannot serve 4 of the 13 canonical domains (family, general, transition, travel) even while `family` shows as the 2nd-highest-salience convergence domain in that same call's own payload (**F-55**), and `moksha` is a fully working domain absent from the canonical 13 (**F-58**). No handler validates its input against its own vocabulary, so an out-of-vocabulary value is byte-indistinguishable from a genuine negative (**F-40**, **F-41**, **F-42**, **F-53**, **F-57**). No CI parity check exists. |
| **G10 · `varga_confirmation` NULL → cross-ayanamsha consensus** | **STILL-OPEN** | Still empty, live. `judgment_query`'s `receipt.varga_confirmed` reads `D9✗ (no divisional row found)` with an accompanying `varga_confirmed_forced_false` judgment flag and an empty `varga_confirmation.rows` array (**F-101** — which grades the *flag* COMPLIANT precisely because it honestly reports the absence). The consensus computation the card specifies does not exist in any served response the audit captured. |
| **G11 · TWO TEMPORAL AUTHORITIES (the real W6)** | **STILL-OPEN (indirect evidence only)** | **No finding tests the card's own acceptance criteria** — `authority_basis` population, the armed-to-fail census, or the staged retirement of the 14 legacy temporal surfaces. What the audit *does* show is the condition the cutover exists to end: multiple temporal surfaces answering the same question differently and none consuming the other — `judgment_query` serves all-empty marriage `timing_hooks` while `assess_marriage` on the identical chart+domain serves a real dated `activating_dasha` (**F-51**); `kala_now_get` reports "not in a dasha junction" on four explicit `false` bands while `ganita_dasha_periods_get` shows the level-4 period running that day with `sandhi_flag=true` (**F-120**, **F-121**); and the forecaster does not consume the promise verdict at all (**F-110**). |
| **G12 · FACADE ENRICHMENTS (R26: all five)** | **PARTIALLY-RESOLVED** | The E6 per-view elevation machinery is live and inspectable — `kala_now_get`/`kala_explain_get` carry the E6 `coverage[]` block citing `KALA_SUPREME_ELEVATION_v1_0.md §6` by name (**F-139** evidence). **But** the card's own named sub-item "`kala_dasha_sandhi_get` production registration verified/fixed" is **falsified**: the tool is non-functional for all charts because the real `Principal` is dropped at registration, and the resulting auth failure is swallowed into a generic honest-empty that reads as a data gap (**F-25**). ELECT's actionable layer is additionally being trimmed away — `candidate_count=4` with one candidate surviving, beside ~60 full hora bookkeeping rows (**F-122**). `state_delta` is unbuilt (BY-DESIGN-OPEN, residual register), and its stated blocker is now factually false (**F-139**). No evidence bearing on the timeline widget contract, the robustness vector on claims, or the E8 register. |
| **G13 · ASSESS SUITE** (`assess_domain(domain)` over the canonical 13) | **STILL-OPEN** | The live 125-tool catalog contains **no `assess_domain` tool** — the suite is still the four legacy tools (`assess_career`/`health`/`marriage`/`wealth`). The audit's own "13 domains" journey had to be run **through `judgment_query`** because no assess-side surface accepts a domain argument (`journey_reports[assess_suite_13_domains_latency]`, which also records the vocabulary split behind G9). The four legacy tools are additionally unequal by tiers of depth (**F-124**, **F-14**, **F-15**). PA-4's substrate half was not measured: no finding reports `bodha_cdlm_cells`' domain count. |
| **G14 · THE LOOP (R28: Abhishek-centred)** | **STILL-OPEN** | Every leg measured, every leg blocked. **(a)** `brahma_prospective_ledger` holds 22 `open` + 1 `matched` for the native and **35 open + 1 matched across all charts, with zero `confirmed`/`falsified`/`withdrawn` — not one prediction anywhere in the system has ever been resolved**; `mcp_prediction_outcomes` holds 0 rows (`p4_prior8_reverification` #7). **(b)** The only MCP tool that discloses the open ledger returns `is_error:true` on every call (**F-01**; PR #1287 exists, correctly titled, and is **OPEN/unmerged**). **(c)** The resolver writer is down (**F-71**). **(d)** The L6 resolver's reach is measurable and small: `kala_field_skill` records `n_events=7` against the chart's 64 logged life events (**F-140**). |
| **G15 · QUALITY UNMEASURED** (21-question dark-corpus re-run; bright% on record) | **PARTIALLY-RESOLVED — discharged in part *by this audit*** | The wealth 21-question set was re-run in full: **19/21 = 90.48% BRIGHT**, with both DARK items (DC-W-16, DC-W-21) arising from well-cited answers silently evading the specific expert technique the question named rather than from hollow content (**F-109**, **F-107**, **F-108**). Two honesty caveats stated by the measurement itself: this qualitative per-answer rubric is **not comparable** to the 2026-07-25 baseline's 5.58% wealth bright% (a structurally different concept-coverage metric, not re-run), and **the career 21-question set was not re-run**. Calendar known-anchor spot-checks are partly covered by the leap-day/ephemeris boundary battery (`dimension_reports[J-boundary]`, all PASS). The §J acharya review (R27) is not commissioned. |
| **G16 · THE RECORD** | **STILL-OPEN** | The governance record still fails its own validators on a clean tree: `drift_detector.py` exits 3 with 216 findings, of which 164 are non-whitelisted MEDIUM/LOW (**F-94**), and `schema_validator.py` exits 3 with 43 violations (**F-95**). Critically, that accepted baseline **contains at least one unambiguously fresh GA.1-class defect**: `CURRENT_STATE.last_session_id = F1-AMENDMENT-CONDUCTOR-2026-08-09` against a `SESSION_LOG` tail of `F1-ADOPTION-CONDUCTOR-2026-08-09` (**F-95**) — genuine drift is currently indistinguishable from the accepted residual. Two further record defects: `CAPABILITY_MANIFEST.json`'s 115 entries are **all** governance-doc canonical_ids with zero data-asset ids, so CLAUDE.md §C-2's single-source-of-truth claim cannot cover the >120-row `asset_registry` and no reconciliation mechanism exists (**F-81**); and migration `456_lel_schema_v2_event_shapes.sql` is recorded as applied but its SQL is **deleted outright** — the one unexplained exception in 430 applied rows (**F-79**, isolated by the otherwise-clean **F-82**). |

### §1.2 — Rulings R17–R28

| Ruling | Verdict | Substantiating evidence |
|---|---|---|
| **R17 · Adoption over addition** (acceptance by REMOVAL counts / adoption censuses) | **PARTIALLY-RESOLVED** | On the chart-identity axis the ruling **holds, verified**: no `legacy_id`/`old_chart_id`/`identity_map`/`id_crosswalk` column or table exists anywhere in the live schema across 115 scanned tables/columns, no source file references such a construct, and the dead phantom chart_id `362f9f17-…` is confirmed absent (0 rows) from `charts`, `chart_facts`, `asset_throughput` and `kala_field` (**F-80**). As a *general* discipline it fails, and P4's cross-class meta-pattern is exactly R17's failure mode restated: **in at least seven independent cases the correct fix already exists in the same repo — often the same file — and was applied to one sibling site out of many** (RC-04's `toolName` fix at 1 of ~22 sites, **F-43**; `resolveChartFactsAyanamsha` at 1 of 11, **F-59**; `hardFloor:true` on `bearing_yogas` but not `timing_hooks`, **F-51**; `NODE_PARASHARI_ASPECTS` correct in one writer and absent from three other drishti tables, **CL-07**; `mi_adhilepa`'s honest tier not adopted by `mi_darshana`, **F-104**; the already-fixed regex not wired to the output, **F-24**; `finalizeMcpBudget`'s honesty-echo unused by the sibling path, **F-46**). |
| **R18 · Bounded rubric scoring** (weights sum to 1, factors in [0,1], cited bands) | **PARTIALLY-RESOLVED** | The rubric exists and conforms structurally where it can be read: `BASE_WEIGHTS` (bhava_lord 0.35 / dusthana 0.30 / kāraka 0.20 / divisional 0.10 / yoga 0.05), **per-class renormalised to sum to exactly `Fraction(1)`**, with a factor ledger, denial checks and fact-id-backed provenance, and 135 rows across 27 event classes stored for the native chart (**F-67**). **But** it has **zero live MCP serving path**, so the declared invariant set the audit was asked to census is verifiable only by reading source and DB directly and can never be confirmed or consumed by any live caller — including the `assess_*` tools that would need it. |
| **R19 · L1 stays sealed** (chart_facts never rewritten for identity reasons; Index rebuildable) | **PARTIALLY-RESOLVED** | Sealedness holds on every axis the audit tested: FK/orphan integrity clean across five tables spanning L1–L5 (**F-83**), no duplicate `(chart_id, fact_id, build_id)` rows (**F-84**), all 10 live `verification_pass_status` values inside the declared vocabulary with no prohibited `'pass'`/`'PASS'` literal in production data (**F-85**), and R17's identity check clean (**F-80**). **But** the Fact Identity Index (`chart_fact_identity`) itself — the keystone deliverable of Lane A5 — is **named by no finding at all**; its >99% parse-coverage acceptance was not measured. Separately, a serving-layer violation of L1's authority *was* found: `ganita_positions_get` and 10 sibling call sites silently rewrite `ayanamsha_id='true_chitra'` to `lahiri_chitrapaksha` and then falsely echo the substituted value, making L1's genuinely-computed true_chitra dataset unreachable (**F-59**). |
| **R20 · Blind amendments** | **NOT-APPLICABLE-TO-THIS-AUDIT** | R20 is cited as *standing* in `GAP_REMEDIATION_MASTER_PLAN.md` and its cycles are named in G5/G6/G7 (F-STRENGTH, F3, F-CONDITION), but **its text is defined in neither of the two master-plan files**, and no finding tests blind-before-effect procedure. Recorded here rather than omitted. |
| **R21 · (the "R21 pattern", extended in G8)** | **NOT-APPLICABLE-TO-THIS-AUDIT** | Referenced only by name in G8 ("the R21 pattern extended"); **not defined in either file**, and addressed by no finding. |
| **R22 · F1 adopted** | **NOT-APPLICABLE-TO-THIS-AUDIT** | Listed in the standing-rulings line; **not defined in either file**, and addressed by no finding. |
| **R23 · NO CLASS IS SILENT** (T1 measured / T2 anchored / T3 qualitative — always speak, never invent a number) | **STILL-OPEN** | The ruling's *second* clause ("never pretends a number it doesn't have") is violated on four independent surfaces that invented their own permanent non-calibrated tags and then serve full numeric precision through them with no suppression gate keyed on the tag: `confidence_basis:'structural_not_yet_empirical'` with 4-decimal posteriors and confidence bounds (**F-68**), `evidence_grade:'structural'/'prior_only'` with 0–10 provenance grades and confidence bands (**F-69**), an inverse-ṣaḍbala resonance labelled `CRITICAL` at 0.173 on a 0–1 scale (**F-117**), and — the highest-harm shape — **five single-day acute-illness dates two-to-three years out with no probability, no confidence interval and none of the `resolution_disclosure` envelope the sibling tool attaches for exactly this purpose** (**F-119**). The ruling's *first* clause is met in places (**F-136**'s `context_only_note` is textbook-correct under PK-R-1), but the T3 qualitative tier does not exist as a first-class labelled serving form. |
| **R24 · NODAL 5/7/9 FULL-STRENGTH + portal-wide census + CI doctrine-census** | **STILL-OPEN — the census ran and the doctrine failed it** | Four independent aspect tables exist; **one is correct and three truncate the nodes to the universal 7th** (**CL-07**: F-19, F-20, F-21, F-52, F-64, F-65 — see G7 above for the per-table breakdown). The distortion is not hypothetical: as of the audit date it is actively suppressing Ketu's 5th aspect onto natal Venus and Rahu's 9th onto the natal 7th from this chart's own marriage-timing windows (**F-52**). The compensator that would partially offset it (`w30_nodal_drishti`) exists in `engine.py` and leaves **no trace in the served window data** (**F-21**). No CI doctrine-census gate exists in any form. One correction of record from the plan itself is upheld: Sarvatobhadra vedha is grid-vedha, not graha-dṛṣṭi, and was correctly left out of scope. |
| **R25 · AMENDMENT ADOPTION, HYBRID** (+ fact of record: outcome data exists for ONE chart only) | **STILL-OPEN** | The ruling's stated fact of record is **confirmed and materially worsened**. Outcome data does exist for one chart only (64 `life_events` for the native, **F-70**; `1c826d5a` remains the zero-history chart across every journey), but the held-out-outcome-validation path the ruling reserves for judgment-call changes is **unavailable system-wide**: across all charts the ledger holds 35 `open` + 1 `matched` and **zero terminal verdicts of any kind**, and `mcp_prediction_outcomes` is empty (`p4_prior8_reverification` #7). No judgment-call amendment can currently be validated by the mechanism R25 names. |
| **R26 · E6 ALL FIVE per-view elevations built in full + E8 register created** | **PARTIALLY-RESOLVED** | The E6 elevation blocks are live and self-describing in at least NOW and EXPLAIN, citing their own spec section and carrying honest coverage states (**F-139** evidence). "In full" is not met: `state_delta` is genuinely unbuilt (residual register, BY-DESIGN-OPEN — the W3 depth remainder), and its attached blocker reason has drifted into being **factually false**, pointing a reader at a field build that has already completed (**F-139**). **No evidence bearing on the E8 register** appears anywhere in the 141 findings. |
| **R27 · ACHARYA REVIEW after all waves (§J closing gate)** | **NOT-APPLICABLE-TO-THIS-AUDIT** | Not commissioned; no finding addresses it. It is the arc's closing ceremony and is downstream of this report. |
| **R28 · LOOP FUEL** (Abhinandan LEL awaiting-native; near-term work on 482012f1: L6 resolver + AHEAD auto-filing) | **PARTIALLY-RESOLVED** | Both halves measured. **Abhinandan LEL: unchanged** — `1c826d5a` behaved as a genuine zero-history chart through every journey and boundary test (`dimension_reports[J-boundary]`, **F-88**), consistent with AWAITING-NATIVE. **Prospective filing exists**: 22 open ledger rows for the native, 35 across all charts — so something *is* turning served windows into dated claims. **The other two legs are broken**: the L6 resolver has reached 7 of the 64 events (**F-140**), the read surface crashes (**F-01**), and the resolver writer is in `error` (**F-71**). The loop's dashed edges are not the two native-owned ones. |

### §1.3 — Master-plan §7 success dashboard (rows this audit can speak to)

| Metric | Gate | This audit's measurement |
|---|---|---|
| `ref_entity_resolve('MAR')` resolves | resolves | **Not measured** — no finding addresses `ref_entity_resolve`; the tool is PASS in the 125-tool census with no entity-round-trip probe recorded. |
| Identity-bearing facts parsed into Index | >99%, gaps explained | **Not measured** — `chart_fact_identity` appears in no finding (see R19). |
| `condition_grade` nonzero | live distribution | **Not measured directly**; the condition axis is only reachable through `bo_pratijna`, which has no serving path (**F-67**). |
| Grade distribution — no monoculture | rubric spread | **Not measured** for `bo_pratijna`. A monoculture *was* found in an adjacent grading field: `efficacy_tier='classically_attested'` on 100/100 rows with `feasibility` null on 50 (**F-118**), and `evidence_grade` hardcoded per row type (**F-69**). |
| Promise scoreboard published | v0, all charts | **Does not exist in the live tool catalog** (125-tool census). |
| Temporal measurement #3 / #4 | published | **Not on record.** The audit's own measurements are the retrodiction baseline (8/41 mapped-and-fired = 19.5%, 25 mapped-not-fired, 8 unmapped, honestly disclosed — **F-72**) and the wealth dark-corpus bright% (**F-109**). |
| Independent graha maps (Py/TS) 13/6 → 1/1 | 1 / 1 | **Not measured as a census.** The audit's structurally analogous census — nodal-aspect tables — found **4 independent maps where 1 is required** (**CL-07**). |

---

## §2 — TEN-DIMENSION FINDINGS

The ten dimensions are A–J as defined in `PARIPURNA_2_AUDIT_PLAN_v2_0.md` §3. **Every one of the
ten has real coverage in the evidence base** — including C, F, I and J, which were discharged by
the P0/P1 base pass and P4 rather than by this session's F-59+ waves, and whose evidence lives in
`manifest.json`'s `tools` census (125 entries), `journey_reports` (4), `dimension_reports`
(`J-boundary`, `J-edge`, `I`), and the two P4 consolidation files. Sub-axis gaps within a covered
dimension are named explicitly below; none is silently omitted.

**One honest bookkeeping defect, stated before the substance:** `manifest.json`'s
`dimension_signoff` object records `null` for all ten letters. The dimensions were *worked* — the
evidence proves it — but **not one was formally signed off in the manifest**, which is a hard
blocker in the audit's own gate (§5.3). The coverage below is reconstructed from the evidence, not
read off a sign-off.

### A — ASTROLOGICAL CORRECTNESS · **covered**

The strongest classical result and the strongest classical failure both live here. Ten fired yogas
were independently re-derived from L1 positions and chart facts: **eight confirmed correct**
(sasa, budha_aditya, vasi, anapha, sarasvati, dhana 2/5/9/11, raja kendra-trikona, kedara), and
**two are misfires** — Chatra and Ardhachandra fire on a chart whose seven classical planets occupy
only four distinct houses, because the detector tests containment rather than exact
seven-distinct-consecutive-house coverage, and the engine's own served `constituent_houses` are
synthetic window ranges (**F-66**). The R24 nodal census found three of four aspect tables
truncating Rahu/Ketu to the universal 7th, with a live present-day distortion of this chart's
marriage timing (**CL-07**; F-19, F-20, F-21, F-52, F-64, F-65). The dignity vocabulary never
emits `moolatrikona` chart-wide, under-scoring Sthana Bala by construction (**F-62**); ṣaḍbala
totals are correct once reached but reachable only by offset trial-and-error (**F-60**); the
saptavargaja score named `…score` is served null with only unresolvable row-id pointers (**F-61**);
and a panchanga detector fires `true` while serving `combination_name='unknown'` (**F-63**).
Tier-honesty (a stated A sub-axis) failed on two surfaces (**F-68**, **F-69**). The open
marriage-zero-gochara-windows question was answered with a mechanism, not a restatement:
`marsys://tool/L4/gochara_forecast_get` is registered nowhere in the retrieval registry, so
`kala_now_get`/`kala_explain_get`'s internal call 404s and is silently converted to
`field_gochara_alignment:'insufficient_data'` (**F-73**). Retrodiction ran under R13 with no
fitting and is reported as-is (**F-72**). **Sub-axis gaps:** no finding records an explicit
FORENSIC 7/7 re-verification on both charts, and the "25-fact classical battery" is not evidenced
as a 25-item battery — the classical re-derivation that *is* evidenced is the 10-yoga set plus the
per-finding cross-checks.

### B — DATA COMPLETENESS · **covered (the audit's strongest dimension)**

Nine VERIFIED-PASS results, several of them expensive and genuinely independent. The headline:
`kala_field_snapshots.field_content_hash` was **recomputed from scratch for both charts** — the
algorithm re-implemented verbatim from `stage4_field.py`, rows streamed from live production via a
fresh connection rather than the writer's object graph — and matched exactly, over 10,502,780 rows
for the native (≈1204s wall clock) and 2,818,813 for the comparison chart (**F-77**). Alongside:
zero decade-seam gaps across all 25 classes and the full horizon (**F-75**), the 25×10 null grid
exact (**F-76**), `[0, 36525]` coverage on both charts with no truncation (**F-87**), FK/orphan
integrity clean across L1–L5 (**F-83**), no duplicate natural keys (**F-84**), the verification
vocabulary conformant with no prohibited literal in production (**F-85**), migration timestamps
monotonic across all 430 rows (**F-86**), and R17 identity adoption clean (**F-80**). Two defects:
`event_classes` conflates attempted-with-built (27 declared / 6 built on the comparison chart, the
21 honestly recorded in `skipped_classes` — currently dormant, no consumer reads the column)
(**F-78**), and migration 456's SQL is unrecoverable (**F-79**, isolated by **F-82**'s otherwise-
clean 430-vs-423 reconciliation). **Sub-axis gap:** the G4/G9/G10 data proofs named in the
dimension spec were not separately produced.

### C — SERVING / MCP (all 125 tools) · **covered**

**125 of 125 live tools carry a verdict**: 82 PASS, 40 GAP, 1 PARTIAL, 2 NOT-APPLICABLE (both
write-path tools — `mimamsa_outcome_record` and `prashna_ask` — excluded with written
justification under the read-only directive). Four tools are **100% unreachable for any argument**
— `read_chapter`, `list_classical_texts`, `find_verses_about`, `search_classical_texts` — all four
rejected before reaching any executor because their MCP-facing names were never added to
`MCP_TO_RETRIEVAL_TOOL` (**F-02**, **F-07**), a class confirmed exhaustively rather than
anecdotally via a whitelist sweep. Four journey tests ran: `when_will_i_marry`
(**PARTIALLY_COHERENT**, with `r24_distortion_check: CONFIRMED_DISTORTION`), `health_rough_patch`
(**COHERENT** — and its F-14 impact assessment is a model of proportionate grading, measuring the
gap's real cost rather than asserting a black hole), `election_muhurta_remedies_prashna_session`
(election **PARTIAL_DEFECT**, remedies **DISAGREE**, prashna/session **COHERENT**), and the
13-domain assess-suite latency sweep (**p50 9,903 ms / p95 18,588 ms, hard_error_count 0** — no
5xx). That last journey also records the finding that the assess suite has no domain-parameterised
surface at all, so the 13-domain sweep had to be run through `judgment_query` (see G13). The
gravest serving result is that **all four `assess_*` tools ship 3.5×–17.4× over their own declared
and echoed budget and are undeliverable to a normal MCP client** (**F-56**, **F-111**) — the audit
could only read them because it had shell and `jq`.

### D — ARCHITECTURE & GOVERNANCE · **covered**

Guards were **mutation-tested**, not asserted. `fact-category-pin-lint` was broken, proven to fail
CI at the exact injected file:line, and reverted to green — and it correctly distinguished the
injected violation from the 29 pre-existing allowlisted ones and kept its hermetic self-test
separate from the live-tree scan (**F-96**). FM-23, FM-25 and FM-26 were each mutation-tested with
RED/GREEN artifacts committed to `pp2-audit/evidence/` (`FM2{3,5,6}_mutation_{RED,GREEN}.txt`);
FM-23 produced no finding, i.e. it passed. The §N.7/§N.8 honesty sweep took ten flags and found a
real detector behind nine of them — including the SATYA-DĪPA orchestrator promotion predicate,
confirmed **still fixed and not reverted** (**F-102**), a live SQL re-derivation on every call
rather than a cached status (**F-106**), and content-checked rather than call-succeeded-checked
receipts (**F-100**, **F-101**) — and **one violation**: `leakage_status` is a bare `'clean'`
literal at all six `mi_darshana` INSERT sites, on blind-retrodiction rows, while the sibling writer
one file over already established `'not_assessed'` as this codebase's honest tier for the identical
concept (**F-104**, contrasted by **F-105**). Both validators fail on a clean tree (**F-94**,
**F-95**) — as designed against an accepted baseline, except that the baseline contains a fresh
GA.1-class defect. G14 loop cycling: measured and blocked (see G14 above).

### E — EXPERIENCE & DEPTH · **covered**

The dark-corpus wealth set was re-run in full with the bright% on record (**F-109**, 19/21 =
90.48%, with both caveats stated by the measurement itself). A fresh agent answered five natural
questions using only MCP tools, producing the audit's most consequential findings: **F-110**
(confidence laundering — the same evidence, opposite verdicts, no reconciliation), **F-111**
(assess_* undeliverable), **F-113** (the domain-specialised tool misses the exalted 7th-house
Saturn that a generic dasha tool surfaced incidentally in ~6KB), **F-114** (the marriage lens's top
ten signals are ten `ga_sensitive` Saturn rows at byte-identical salience 2.16108, none naming the
7th lord, Venus or a marriage yoga), **F-115** (two tools name different #1 remedy targets from the
same asset), **F-116** (catalog affliction preambles contradicting a FORENSIC birth anchor), and
**F-119**. Three whole-chart depth reads on served output produced the jargon-leakage class across
six surfaces (**F-128**–**F-132**) plus its decisive positive contrast: `graha_portrait` and
`judgment_query`'s v3 envelope already self-gloss every internal token via a `register`/
`reading_contract` pair (**F-137**), which makes the leakage an inconsistency across code paths,
not a platform limitation. The reads also produced the audit's one clear "beyond a competent human"
demonstration: `kala_ahead_get`'s `period_echo` cross-references the currently-active Saturn
Antardasha against its own prior occurrence in the native's lifetime using LEL-corroborated events
from that period, correctly labelled `hypothesis_served` (**F-138**). **Sub-axis gaps:** the career
21-question set was not re-run, and **no PRATINIDHI (opus-max) grading record for tool selection /
synthesis / citation fidelity / depth / honest-uncertainty appears in the manifest** — the
consumability *run* happened; the *grades* the plan specifies are not on record.

### F — RESIDUAL CONSOLIDATION · **covered (complete)**

`p4_residual_register.json` consolidates **42 named residuals** across the manifest, the 23 defect
classes, `ONGOING_HYGIENE_POLICIES §F/§K` and the Phase-14G whitelist, `CURRENT_STATE v6.60`'s
RES-R42-1/2/3, and the ~293-row `MARSYS_DEFECT_GAP_REGISTER_v2_0.md`, each graded **GAP (35)** or
**BY-DESIGN-OPEN (7)** with an owner lane — including two deliberate SPLIT grades where the waiting
is by design but the blockers preventing the wait from ever ending are not. All eight prior-audit
findings were re-verified from scratch against the live server and live Postgres (§6.1). This is
the one dimension with no sub-axis gap.

### G — SECURITY & ISOLATION · **covered**

The cross-chart leakage question was tested directly and the system **failed closed correctly**:
no tool was found that silently substitutes the session's implicit `active_chart_id` for a
caller-omitted `chart_id` — the tools error instead (**F-88**), which materially de-risks the one
real observation there (the session's implicit active chart is the *comparison* chart, not the
native, so a caller reading `session_recall`'s usage hint could be misled into passing it
manually). Profile scoping is UX curation rather than an access boundary: a `compact`-profile
caller who cannot see `ganita_sensitive_degrees_get` can retrieve byte-identical rows through
`ganita_chart_facts_get`, which *is* in that profile — for charts they are already entitled to
(**F-91**). Two real error-hygiene leaks: a raw Postgres encoding literal reaching
`content.content` (**F-89**) and a shared alias helper leaking **internal microservice routes**
(`/api/pyhora/compute`, `/api/compute/phala/muhurta_finder`) plus verbatim CPython exception text
across ~7 tools / 10 call sites (**F-90**). The entitlement boundary is crossed unevenly: five of
eight `bodha_bundle_get` subsystems fail the per-chart gate on **every** call (**F-30**, **F-74**,
**F-127**) while `kala_now_get` performs no existence check at all and returns a full
successful-looking envelope for a fabricated UUID (**F-38**). **Sub-axis gap:** no finding records
an explicit secrets/credential sweep of responses and error paths; the axis is covered only
indirectly by F-89/F-90.

### H — DETERMINISM & CONCURRENCY · **covered, but thinnest of the ten**

Two findings, one of which falsifies the dimension's primary claim. `judgment_query(domain=career)`
returned **4 then 6 distinct deduped activation windows on two byte-identical calls ~2.3s apart**,
with the disclosure flag text changing to match; the headline verdict and composite score were
stable, but the served supporting-evidence array underneath them was not (**F-92**). `prashna_ask`
narrated Mahādaśā/Antardaśā boundary dates **~6 weeks off** the `two_pass_verified` `chart_dashas`
row it should be restating (**F-93**). Pagination stability under repeat is covered from dimension
A rather than here: `ganita_strength_get`'s declared `total` and `counterfactual_rows_dropped`
**changed on every retry at a different offset for the identical chart** (**F-60**). **Sub-axis
gaps:** concurrent-call session-memory corruption and `as_of` backdating reproducibility have **no
evidence at all** — these are genuine holes in H's coverage, not merely unreported passes.

### I — CONTRACT CONFORMANCE · **covered**

Sixteen tools were exercised against the budget/trim/`density_contract` axis, of which **seven are
GAP** (`dimension_reports[I]`): stale pre-trim counts on five independent tools (`bodha_signals_get`
200 vs 20, `synth_chart_brief_get` 27 vs 13, `kala_priority_ranking_get` 100 vs 50,
`kala_windows_get` 500 vs 5, `bodha_remedies_get` 27 vs 13 — with the untouched `resonance_count`
correctly matching its own array, proving the mismatch tracks the trimmer) (**F-45**); the honest
budget-echo contract present in one helper and absent in the sibling path (**F-46**); a
`trim_report` that self-collapses under extreme pressure, hiding that `chapters` went 91→0 while
`chapter_count` still read 91, and naming a non-existent `response_format:legacy` recovery
instrument (**F-44**); and the live `unknown_tool` placeholder reproduction (**F-43**). The PASS
side is real and worth preserving as regression anchors — `dossier` at `budget_kb=1` returns an
honest BLOCKED gate rather than fabricated coverage, `scan_fetch_signals` carries a true total with
a working recovery path, and `plan_retrieval`'s completeness receipt is self-consistent. **Sub-axis
gap:** "every response validated against the tool's DECLARED schema" was **not performed
mechanically** — I's evidence is budget/trim/density-focused, not a schema-conformance sweep.

### J — REGRESSION & EDGE · **covered**

Roughly 29 scenarios across two reports. **J-boundary:** birth-instant PASS on two tools (the L3
Pratyantardaśā active at birth resolves correctly, no off-by-one); pre-birth **GAP** on
`ganita_dasha_periods_get` (served as `two_pass_verified` rows whose only tell is a free-text
`age ~-4`) (**F-33**) against a clean honest degrade on `kala_now_get`; the 2084 horizon straddle
**GAP** (22 silently-capped windows with `empty_reason:null`, where a fully-beyond-horizon query
*does* disclose) (**F-34**); leap day 2024-02-29/2028-02-29 PASS across four tools with a dasha
boundary landing exactly on the leap day and gap-free monotonic ephemeris; `varsha_year=200` honest
empty. **J-edge:** nonexistent UUID cleanly rejected by five tools and **not** by `kala_now_get`
(**F-38**), with a narration-fidelity defect in the shared denial template that asserts "this chart
exists" for a fabricated UUID (**F-39**); malformed args cleanly rejected on six tools; unknown
domain **GAP** on `judgment_query` (**F-41**) and `gochara_forecast_get` (**F-40**) against clean
honest empties on `kala_priority_get` and `bodha_signals_get`; unvalidated `ayanamsha_id` returning
an indistinguishable empty page (**F-42**). The zero-history chart went through the full journey
set and behaved correctly throughout. **Sub-axis gap:** golden-fixture comparison against the Δ2
fixture estate was not run.

---

## §3 — THE GAP LEDGER


**Scope.** All **114** of the audit's 141 findings that assert a real defect. The remaining **27**
are verified-PASSes, positive controls and informational baselines isolated by P4 as bucket
`CL-00`; they assert no defect and are listed separately in **Appendix A**, where they should be
preserved as regression anchors rather than remediated.

**Ordering.** TIER 1 → TIER 4, and within each tier grouped by the 23 root-mechanism defect classes
from `pp2-audit/p4_defect_classes.json`. Severity labels in the manifest are heterogeneous (the
waves used three different vocabularies — see §5.3); they are normalised here as
`TIER1-CORRECTNESS`/`critical` → TIER 1, `TIER2*`/`high`/`major` → TIER 2,
`TIER3*`/`medium` → TIER 3, `TIER4`/`low`/`informational` → TIER 4, and each finding's original
label is printed verbatim beside its id so the normalisation is auditable.

**Per finding:** the `reproduce_cmd` a third party can paste and run, the diagnosed mechanism (or
an explicit `DIAGNOSIS-INCOMPLETE` where the audit could not trace it — **28 of the 138 clustered
findings carry that marker on their exact file:line, mechanism, or both**, and it is preserved
rather than smoothed over), and a proposed remediation lane.

**The single most important cross-class observation**, from P4's own meta-pattern note and repeated
here because it should shape how the remediation campaign is *organised* rather than merely what it
contains:

> In at least **seven independent cases the correct fix already exists somewhere in the same repo —
> often the same file — and was simply not propagated to sibling call sites**: RC-04's `toolName`
> fix applied to 1 of ~22 `dualOutput` sites (F-43); `resolveChartFactsAyanamsha` applied to 1 of
> 11 alias sites (F-59); `hardFloor:true` applied to `bearing_yogas` but not `timing_hooks` (F-51);
> `NODE_PARASHARI_ASPECTS={5,7,9}` correct in `ga_structural_writer` but absent from three other
> drishti tables (CL-07); `mi_adhilepa`'s honest `'not_assessed'` tier not adopted by `mi_darshana`
> (F-104); the already-fixed `DEEP_DOMAIN_WORD` regex not wired to the output (F-24);
> `finalizeMcpBudget`'s honesty-echo not used by `applyAutoBudgetToEnvelope` (F-46).
> **A remediation campaign should treat "apply the known fix at every sibling site, enforced by a
> lint" as a first-class lane in its own right.**

### §3.0 — Ledger at a glance

| Tier | Findings | Classes represented |
|---|---|---|
| **TIER 1** | 25 | CL-01, CL-03, CL-05, CL-06, CL-07, CL-08, CL-14, CL-15, CL-17, CL-19, CL-20, CL-21 |
| **TIER 2** | 53 | CL-01, CL-02, CL-03, CL-04, CL-05, CL-06, CL-07, CL-08, CL-09, CL-10, CL-11, CL-12, CL-13, CL-16, CL-17, CL-18, CL-19, CL-20, CL-21, CL-22 |
| **TIER 3** | 27 | CL-02, CL-03, CL-04, CL-07, CL-08, CL-10, CL-11, CL-12, CL-13, CL-14, CL-22, CL-23 |
| **TIER 4** | 9 | CL-01, CL-04, CL-07, CL-08, CL-11, CL-12, CL-13, CL-23 |
| **Total** | **114** | 23 defect classes (CL-01…CL-23) |

---

### §3.1 — TIER 1 — CORRECTNESS  (25 findings)

*The served answer is wrong, unreachable, or contradicted by the same server. A caller acting on these is acting on a false premise.*

#### CL-01 Registered-but-unreachable capability (dispatch/registration wiring gap)

> **Root mechanism (class-level).** A capability is fully implemented — often with its own contract, schema and even a whitelist entry in ONE map — but the map the live dispatcher actually consults never receives the key: MCP_TO_RETRIEVAL_TOOL (F-02/F-07/F-11), the retrieval-registry URI table (F-73's marsys://tool/L4/gochara_forecast_get, zero registered gochara URIs anywhere in platform/src/lib/retrieval/registry — re-verified live this pass), server.tool() registration (F-67 bo_pratijna), or the Principal argument at registration time (F-25). server.ts's own docstring names this class: 'registered != deployed != callable'.

> **Class remediation lane.** LANE-WIRING: one sweep that asserts, in CI, that every CapabilityDescriptor/contract with annotations.surgical is present as a key in MCP_TO_RETRIEVAL_TOOL AND reachable end-to-end, and that every callRegistryCapability URI literal resolves to a registered capability.


##### F-02  ·  `TIER1-CORRECTNESS`

**Claim.** Four live, read-only MCP tools -- read_chapter, list_classical_texts, find_verses_about, and search_classical_texts (F-07) -- are 100% unreachable for any argument. All four are registered in platform-mcp/src/tools/read_classical_text.ts and share the identical root cause: their MCP-facing name was never added as a key to MCP_TO_RETRIEVAL_TOOL (tool_name_bridge.ts:508+), so isAllowedSurgicalTool() always rejects them regardless of arguments. Confirmed live for all four (read_chapter, list_classical_texts, find_verses_about, search_classical_texts). A systematic sweep (evidence/whitelist_sweep_report.json) diffed every primitive name invoked via callPlatformPrimitive/callPlatformPrim against the whitelist and found no further live-tool instances of this class.

**Reproduce.**

```
mcp__marsys-jis-direct__read_chapter({text_id:'bphs', chapter:1}) | mcp__marsys-jis-direct__list_classical_texts({}) | mcp__marsys-jis-direct__find_verses_about({topic:'exalted Mars in tenth house'}) | mcp__marsys-jis-direct__search_classical_texts({query:'Saturn in the seventh house effects on marriage'}) -- all four return {error:true, message:'Tool not in surgical whitelist: <name>'}
```

**Evidence.** `evidence/whitelist_sweep_report.json`

**Mechanism.** platform/src/app/api/mcp/primitives/[tool]/route.ts:113-124 (whitelist check calls isAllowedSurgicalTool(mcpToolName), 400s on false) + platform/src/lib/retrieval/registry/tool_name_bridge.ts:602-606 (isAllowedSurgicalTool: `return Object.hasOwn(MCP_TO_RETRIEVAL_TOOL, mcpToolName)`) + tool_name_bridge.ts:505-608 (MCP_TO_RETRIEVAL_TOOL object literal -- 'read_chapter' is never a key). The only place 'read_chapter' appears wired is TOOL_NAME_TO_URI at tool_name_bridge.ts:110, an unrelated map keyed differently, so it does not satisfy the whitelist check. MCP server (platform-mcp/src/tools/read_classical_text.ts:90-106) faithfully proxies and surfaces the platform's 400 verbatim as isError:true. Confirmed as a 4-tool class via systematic sweep, not just the original 2: list_classical_texts (read_classical_text.ts:126) and find_verses_about (read_classical_text.ts:154) fail identically (evidence/list_classical_texts__whitelist_reject.json, evidence/find_verses_about__whitelist_reject.json).

**Proposed remediation.** LANE-WIRING — add all four MCP-facing names as keys in `MCP_TO_RETRIEVAL_TOOL`, and add a CI assertion that every contract declaring `annotations.surgical` is present as a whitelist key and is reachable end-to-end.

##### F-07  ·  `TIER1-CORRECTNESS`

**Claim.** The MCP tool search_classical_texts -- fully registered with its own contract (annotations.surgical:true) and JSONSchema -- is unconditionally rejected by the actual MCP dispatch whitelist for every call, valid or not, making the tool 100% non-functional. Same defect class and root cause as F-02 (read_chapter).

**Reproduce.**

```
mcp__marsys-jis-direct__search_classical_texts({query: 'Saturn in the seventh house effects on marriage', top_k: 5})
```

**Evidence.** `evidence/search_classical_texts__saturn_seventh.json`

**Mechanism.** platform/src/app/api/mcp/primitives/[tool]/route.ts:115-119 calls isAllowedSurgicalTool(mcpToolName) (tool_name_bridge.ts:602-605, Object.hasOwn(MCP_TO_RETRIEVAL_TOOL, mcpToolName)). MCP_TO_RETRIEVAL_TOOL (tool_name_bridge.ts:508+) only keys 'read_classical_text' -> 'classical_text_search' (line 525); no key 'search_classical_texts'. TOOL_NAME_TO_URI (line 107, a separate map) does map 'search_classical_texts' -> 'marsys://tool/L0/query_classical_texts', and the tool's own contract (registry.ts:172-209) declares surgical:true with a full schema -- but that contract/URI mapping is never consulted by the actual dispatcher. Every call 400s before reaching any executor.

**Addendum.** Confirmed part of the F-02 4-tool whitelist class (see F-02, extended); see evidence/whitelist_sweep_report.json for the full systematic sweep.

**Proposed remediation.** Fold into the same four-key patch as F-02, and retire the parallel `TOOL_NAME_TO_URI` path so one map — the one the dispatcher actually consults — governs reachability.

##### F-25  ·  `TIER1-CORRECTNESS`

**Claim.** kala_dasha_sandhi_get is non-functional for all charts due to a dropped Principal at tool registration, causing every dispatch to the L1 dasha registry to fail authorization and get silently reported as an honest-empty result -- proven by sibling tool kala_now_get successfully serving the identical chart_dashas data via its own dasha_sandhi sub-field in the same session.

**Reproduce.**

```
MCP kala_dasha_sandhi_get {chart_id:'482012f1-710e-4a25-994a-93821f5871aa'} vs MCP kala_now_get {chart_id:'482012f1-710e-4a25-994a-93821f5871aa'} (compare dasha_sandhi field)
```

**Evidence.** `evidence/kala_dasha_sandhi_get__revalid.json`

**Mechanism.** platform-mcp/src/tools/kala_views/register_all.ts:64 omits the real Principal when calling registerDashaSandhiCalendar (unlike all sibling kala_* registrations); dasha_sandhi.ts:358-362 falls back to a hardcoded fake 'system' principal that fails the /api/retrieval/capability entitlement gate; dasha_sandhi.ts:173,187-189 swallows the resulting error into a generic honest-empty message that reads as a data gap, not an auth failure.

**Proposed remediation.** Pass the real `Principal` into `registerDashaSandhiCalendar`, and make the hardcoded `'system'` fallback a hard registration-time error rather than a runtime honest-empty that reads as a data gap.

##### F-67  ·  `TIER1-CORRECTNESS`

**Claim.** The bo_pratijna v4 'promise rubric' (R18's actual target: BASE_WEIGHTS bhava_lord=0.35/dusthana=0.30/karaka=0.20/divisional=0.10/yoga=0.05, per-class renormalized to sum to exactly Fraction(1) by compute_class_weights, with a factor_ledger, denial checks, and fact-id-backed provenance) is fully computed and stored -- 135 rows exist in bodha_pratijna for the native chart 482012f1, spanning 27 event classes -- but has ZERO live MCP serving path. The capability is fully implemented as a CapabilityDescriptor (query_pratijna.ts) and is whitelisted in the primitives bridge under the alias bodha_pratijna_get (tool_name_bridge.ts:584), yet no file under platform-mcp/src/tools/*.ts (or server.ts) ever calls server.tool() to register 'bodha_pratijna_get' or 'query_pratijna' as an invokable MCP tool -- confirmed by an exhaustive case-insensitive grep for 'pratijna' across platform-mcp/src, which returns only a single unrelated comment (register_p1_synthesis.ts:257) and nothing in server.ts. A live ToolSearch against the marsys-jis-direct MCP surface for 'pratijna promise denial ledger' returned no matching tool. This means the entire declared invariant set the task asked to census (weights sum to 1.0, factor bounds, citation resolution) is verifiable only by reading source/DB directly -- it can never be confirmed, audited, or consumed by any live MCP caller, including the assess_* tools and judgment_query, none of which surface this rubric's weights/factor_ledger. server.ts's own docstring (lines 103-111) names this exact defect class ('a genuine registered capability, never wired to MCP ... registered != deployed != callable') as something the codebase has fixed once before (for read_classical_text and siblings); bo_pratijna is an unfixed second instance.

**Reproduce.**

```
psql: SELECT count(*) FROM bodha_pratijna WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'; (returns 135) -- then grep -rli "pratijna" platform-mcp/src --include="*.ts" | grep -v generated (returns only register_p1_synthesis.ts's comment, no registration); grep -n "pratijna" platform-mcp/src/server.ts (no output). ToolSearch({query:'pratijna promise denial ledger'}) against marsys-jis-direct returns no bodha_pratijna_get/query_pratijna tool.
```

**Evidence.** `evidence/sql__bo_pratijna_unreachable.txt`

**Mechanism.** platform/src/lib/retrieval/registry/layers/L2_bodha/query_pratijna.ts (capability fully defined, never consumed by MCP) + platform/src/lib/retrieval/registry/tool_name_bridge.ts:203,584 (alias registered in the primitives whitelist only) + platform-mcp/src/server.ts (no `import`/`registerXxx()` call for any Pratijna tool anywhere in the file, confirmed by exhaustive grep across platform-mcp/src).

**Proposed remediation.** Register `query_pratijna` / `bodha_pratijna_get` as an invokable MCP tool so the R18 rubric invariants (weight sum, factor bounds, citation resolution) become auditable and consumable from the serving surface at all.

#### CL-03 Parameter accepted but never applied (no-op filter / silent value substitution)

> **Root mechanism (class-level).** The MCP schema declares a parameter and the alias layer forwards it, but it is dropped before it reaches a SQL predicate — either because the primitive's input_schema does not declare it (F-08 domain), the SQL simply has no clause (F-03 limit/offset, F-06 chart_id, F-10 action_class, F-133 horizon_months on the mitigations family), the call site never passes it (F-49 mitigation_map), or a file-local alias map rewrites the value before the query (F-59 true_chitra -> lahiri_chitrapaksha at 10 of 11 unfixed call sites). Callers get false confidence that scoping occurred. Several of these carry an inline comment claiming the filter IS applied (F-10).

> **Class remediation lane.** LANE-PARAMPARITY: contract test per tool asserting that changing each declared parameter changes the result_hash, or that the tool documents the parameter as advisory.


##### F-10  ·  `TIER1-CORRECTNESS`

**Claim.** prashna_undertaking_get's election_windows sub-query applies no domain/action_class filter whatsoever, despite an inline code comment claiming a domain->action-class mapping is applied there. For domain='health', top-ranked 'best election windows' were action_class='marriage' (ranked above the actually health-relevant 'medical' window); for domain='career', all returned windows were action_class='new_venture' rather than the domain-mapped 'business_start'. A caller trusting the top election window for an undertaking is handed a wrong-domain recommendation with no mismatch disclosure.

**Reproduce.**

```
mcp__marsys-jis-direct__prashna_undertaking_get({chart_id: '1c826d5a-41cb-4450-b4dc-59d440e5f75a', domain: 'health'}) -- inspect content.election_windows[].action_class vs content.action_class
```

**Evidence.** `evidence/prashna_undertaking_get__zero_health.json`

**Mechanism.** platform-mcp/src/tools/register_p1_synthesis.ts:902-913 -- muhurtaResult SQL (`SELECT ... FROM phala_muhurta pm WHERE pm.chart_id = $1 AND pm.composite_quality IS NOT NULL ORDER BY pm.composite_quality DESC NULLS LAST LIMIT $2`) has no action_class predicate, even though the comment directly above it (line 902) claims domain->action-class mapping is applied. actionClass IS correctly computed via _DOMAIN_TO_ACTION (934-946) and correctly used to filter the separate ontologyResult query (947-951) -- the domain filter was simply never wired into the muhurtaResult query.

**Proposed remediation.** Wire the already-correct `actionClass` (`_DOMAIN_TO_ACTION`) into the `muhurtaResult` SQL predicate and delete the inline comment that claims it already is applied.

##### F-59  ·  `TIER1-CORRECTNESS`

**Claim.** ganita_positions_get (and 10 sibling MCP tool call-sites in the same file) silently rewrite ayanamsha_id='true_chitra' to 'lahiri_chitrapaksha' before querying, so a caller who explicitly requests the true_chitra ayanamsha is served lahiri_chitrapaksha's rows instead -- byte-identical fact_id values, and the response's own ayanamsha_id field falsely reads 'lahiri_chitrapaksha'. The chart's true_chitra dataset is genuinely computed and stored in chart_facts (confirmed live via direct SQL) but is unreachable through this tool. This is the SAME defect class as an already-diagnosed bug (registry_bridge.ts AYANAMSHA_ALIAS / LCA-3), duplicated into a second, unfixed alias map (register_p1_aliases.ts) and never patched at 10 of its 11 call sites -- only the ganita_chart_facts_get alias site was fixed.

**Reproduce.**

```
mcp__marsys-jis-direct__ganita_positions_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa', planet:'LAGNA', ayanamsha_id:'true_chitra'}) -- compare returned rows' ayanamsha_id field and fact_id values against the default/lahiri_chitrapaksha call; also compare against mcp__postgres__query("SELECT * FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='graha_position' AND fact_subject='LAGNA' AND ayanamsha_id='true_chitra'") which returns genuinely distinct, correctly-computed rows (longitude 12.4467deg vs lahiri's 12.4311deg). Control: ayanamsha_id='bogus_nonexistent_ayanamsha_xyz' correctly returns an empty row set, proving the filter mechanism itself works and true_chitra is specifically mishandled, not generically ignored.
```

**Evidence.** `evidence/ganita_positions_get__native_true_chitra_bug.json`

**Mechanism.** platform-mcp/src/tools/register_p1_aliases.ts:39-43 defines a file-local AYANAMSHA_ALIAS map (Record<string,string>) including 'true_chitra: lahiri_chitrapaksha', consumed by a local na() normalizer (same file) that is called at 11 tool sites (lines 382, 494, 572, 650, 702, 920, 970, 1199, 1244, 1290, plus the ganita_positions_get site at line 702: `ayanamsha_id: na(ayanamsha_id as string | undefined)`). This is a duplicate of the already-known, already-partially-fixed defect in platform-mcp/src/tools/registry_bridge.ts:98-124 (its own AYANAMSHA_ALIAS/normalizeAyanamsha, whose WP-1.3(f)/LCA-3 code comment explicitly documents this exact symptom: 'COLLAPSES true_chitra/true_citra -> lahiri_chitrapaksha, which made true_chitra's own 27,112-row dataset UNREACHABLE'). The correct fix -- resolveChartFactsAyanamsha()/CHART_FACTS_AYANAMSHA_ALIAS at registry_bridge.ts:125-142, which passes true_chitra through unchanged -- is imported into register_p1_aliases.ts (line 26) but wired to only ONE of its 11 alias call sites (line 1347, ganita_chart_facts_get); the other 10, including ganita_positions_get, still call the broken local na(). The underlying registry capability (get_positions.ts:150,77-79) itself has no bug -- it queries ayanamsha_id verbatim; the corruption happens entirely in the MCP alias layer before the query ever runs. True_chitra is confirmed genuinely implemented and populated at the writer level (ga_ayurdaya.py:16, ga_sensitive_degree.py:16, ga_medical.py:18, ga_yoga.py:25, ga_vichara.py:27, ga_transit_anchors.py:42, ga_nakshatra.py:39 all iterate it as one of 5 computed sidereal ayanamshas).

**Proposed remediation.** Replace the file-local ayanamsha alias map with `registry_bridge`'s `resolveChartFactsAyanamsha` at all 11 call sites, plus a lint forbidding any file-local ayanamsha rewrite.

#### CL-05 Response-budget / trim defects (unenforced ceiling, inverted density priority, unreachable data)

> **Root mechanism (class-level).** A generic post-hoc byte trimmer runs outside the handlers' knowledge. It has no notion of which section carries the answer — hardFloor:true is declared on only some sections, so timing_hooks (F-51) and the kala_elect candidate slate (F-122) are floored to zero while hora bookkeeping and catalog rows survive intact; sections attached AFTER the trimmer (F-112's domain_completeness) escape it entirely, so verbosity:'concise' makes the response BIGGER; some tools have no budget control at all (F-13, 1.30MB); and the budget is echoed as budget_kb_applied but not enforced (F-56/F-111: 3.5x-17.4x overshoot with a self-reported budget_exceeded_after_trim flag). Re-verified live this pass: assess_marriage = 158,200 bytes against budget_kb_applied 40; mimamsa_calibration_get still truncates mid-JSON at ~120 chars. Direct violation of CLAUDE.md §N.6 items 2-3.

> **Class remediation lane.** LANE-BUDGET: make budget_kb a hard contract — declare hardFloor+minKeep on every answer-bearing section, move post-trim attachments inside the trim path, and fail loudly (typed error + drill pointer) rather than shipping an over-budget payload.


##### F-51  ·  `TIER1-CORRECTNESS`

**Claim.** judgment_query's marriage-domain timing_hooks are ALL empty for both charts, and the tool honestly downgrades receipt.timing_anchored=false via judgment_flag -- but this reads as 'no timing evidence exists' when the lord/karaka's Mahadasha IS on file (native: Venus MD 2034-2054, two_pass_verified) and sibling tool assess_marriage, called on the identical chart_id+domain, DOES surface a real dated activating_dasha (Mercury MD 2010-2027). Direct cross-tool contradiction inside one 'when will I marry' journey.

**Reproduce.**

```
judgment_query(chart_id='482012f1-710e-4a25-994a-93821f5871aa', domain='marriage', response_format='v3') -> checklist.timing_hooks all-empty + timing_anchored_forced_false; contrast assess_marriage(chart_id=..., reading_depth='deep_dive') -> activating_dasha.activations[0] has real Mercury MD dates
```

**Evidence.** `evidence/judgment_query__native_marriage.json`

**Mechanism.** CONFIRMED, not a date-window bug: register_d9_judgment.ts:708-738 fetches Venus's real 2034-2054 mahadasha correctly with an explicit 1900-2100 window. Root cause is POST-SERVE BUDGET TRIMMING: judgment_query defaults to a 12KB ceiling (registry_bridge.ts:323). The timing_hooks.current (minKeep:3, :3505-3524) and mahadasha_windows_by_graha (minKeep:4, :3526-3555) trim sections are declared WITHOUT hardFloor:true -- unlike >10 other sections in the same file including bearing_yogas (:3437,3457,3475). Per response_budget.ts:118-131's PASS-2 hard-cap fallback, sections without hardFloor:true get floored to 0 first -- the exact failure mode the code's own comment (response_budget.ts:122-127) says hardFloor exists to prevent, citing bearing_yogas as the worked fix example. timing_hooks was never given the same protection. Direct violation of CLAUDE.md SS N.6 Serving Density Principle point 2.

**Proposed remediation.** Declare `hardFloor:true` + `minKeep` on `timing_hooks` exactly as `bearing_yogas` already does, and add a §N.6 test asserting no answer-bearing section can be floored to zero while bookkeeping sections survive.

##### F-56  ·  `TIER1-CORRECTNESS`

**Claim.** All 4 assess_* tools (career, health, marriage, wealth) shipped responses 3.5x-4.2x over their own declared 40KB budget ceiling on this exact native-chart call (168,575 / 142,742 / 147,023 / 157,566 bytes). Each response's own judgment_flags includes 'budget_exceeded_after_trim' -- the server KNOWS it exceeded budget and ships the oversized payload anyway. In this audit's MCP client, all 4 calls triggered a hard tool-output token-limit failure requiring a file-based fallback to read; a client without that fallback gets an unrecoverable failure on every assess_* call against this chart, including the two domains (career, marriage) previously verdicted PASS.

**Reproduce.**

```
assess_career(chart_id='482012f1-710e-4a25-994a-93821f5871aa')  # and assess_health / assess_marriage / assess_wealth, all reproduce identically, 100% rate
```

**Evidence.** `evidence/assess_career__native.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE -- root cause not traced to source in this pass (trim logic lives in platform-mcp/src/lib/response_budget.ts per CLAUDE.md SS N.6, not opened to confirm why the trim pass fails to converge for this tool family specifically). Confirmed and reproducible: 4/4 assess_* calls exceed budget by 3.5x-4.2x; judgment_query calls in the same session (12KB budget) never did.

**Proposed remediation.** LANE-BUDGET — make `budget_kb` a hard contract: fail with a typed over-budget error plus a drill pointer rather than shipping a payload the declared ceiling says will not fit.

##### F-111  ·  `critical`

**Claim.** All three assess_* tools are undeliverable to a normal MCP client. assess_marriage=147,294 bytes (budget_kb_applied 40), assess_career=163,241 bytes (applied 20), assess_health=139,678 bytes (budget_kb_requested 8, applied 8). Every one exceeded the client token ceiling and had to be spilled to disk; every one self-reported judgment_flags:[{code:'budget_exceeded_after_trim'}]. The overshoot is 3.7x, 8.1x and 17.4x the declared budget respectively. I could only read them because I had shell and jq - a capability the actual end user of this server (an LLM in an MCP client) does not have. In a plain client all three domain-assessment tools return nothing usable.

**Reproduce.**

```
Q1/Q2/Q3. Call assess_marriage(chart_id=482012f1-710e-4a25-994a-93821f5871aa); assess_career(chart_id=same, verbosity='concise', max_signals_per_lens=3); assess_health(chart_id=same, max_signals_per_lens=1, budget_kb=8). Each returns a token-limit error. Check jq '.object.judgment_flags' on the spill files.
```

**Evidence.** `pp2-audit/evidence/E2_q1_raw_assess_marriage.json | pp2-audit/evidence/E2_q2_raw_assess_career.json | pp2-audit/evidence/E2_q3_raw_assess_health.json`

**Mechanism.** response_budget.ts trims only the sections it is given; the dominant payload sections escape it. In assess_marriage/assess_health the bulk is activating_dasha (62KB) + verdict_skeleton (43KB) = 105KB of 147KB - two sections the trimmer evidently cannot floor to zero. The budget_kb parameter is accepted, echoed as budget_kb_applied, and then not enforced; 'budget_exceeded_after_trim' is emitted as an informational flag rather than triggering a harder fallback (e.g. dropping activating_dasha to a summary). A declared-and-echoed budget that cannot be honoured is a contract the caller cannot plan against.

**Proposed remediation.** Same lane as F-56, plus a client-realistic delivery test asserting every `assess_*` response on the canonical chart is under its declared ceiling without shell/`jq` assistance.

#### CL-06 False or stale aggregate / pagination fields

> **Root mechanism (class-level).** An aggregate is derived from the wrong set: from the post-LIMIT page instead of a COUNT(*) (F-12 dignity/avasthas/karakas, F-37 ref_yogas_get), from the PRE-trim array the trimmer later cut and never re-derived (F-45, five independent tools: bodha_signals_get 200 vs 20, synth_chart_brief_get 27 vs 13, kala_priority_ranking_get 100 vs 50, kala_windows_get 500 vs 5, bodha_remedies_get 27 vs 13), from a clamped input echoed back as the caller's own (F-36 offset silently clamped to 100,000), or from a case-mismatched SQL FILTER that matches zero rows (F-29, served 0/0/0 against a real 2 CONFIRMED / 23 PARTIAL / 7 REFUTED distribution). A caller cannot page or size any of these surfaces correctly.

> **Class remediation lane.** LANE-COUNTS: every total/…_count field either issues its own COUNT(*) or is re-derived after the trimmer, and any clamped/substituted input is echoed alongside the caller's original value.


##### F-29  ·  `TIER1-CORRECTNESS`

**Claim.** mimamsa_insight_get's calibration_summary always reports 0 confirmed / 0 partial / 0 denied regardless of the chart's real calibration state, due to a case-sensitivity SQL FILTER mismatch -- verified against live DB data showing a real, non-trivial distribution (2 CONFIRMED / 23 PARTIAL / 7 REFUTED) that the served summary should reflect but never does.

**Reproduce.**

```
mcp__marsys-jis-direct__mimamsa_insight_get({chart_id: '482012f1-710e-4a25-994a-93821f5871aa'}) -- inspect content.calibration_summary (always {confirmed:0, partial:0, denied:0}); cross-check against a direct read-only SQL count of the same chart's calibration verdict rows (2/23/7)
```

**Evidence.** `evidence/mimamsa_insight_get__valid_native.json`

**Mechanism.** query_insights.ts:118-120 -- a lowercase-vs-UPPERCASE SQL FILTER predicate mismatch against the verdict enum values (the stored verdict strings are uppercase (CONFIRMED/PARTIAL/REFUTED) but the FILTER clause compares against lowercase literals, so every FILTER(WHERE verdict = '...') aggregate matches zero rows). File:line preserved from the original agent's report (not lost in the concurrent-write race, unlike F-27/F-28).

**Proposed remediation.** Fix the case-mismatched SQL FILTER predicates in `query_insights.ts` and pin the real 2 CONFIRMED / 23 PARTIAL / 7 REFUTED distribution in a golden test.

#### CL-07 Nodal (Rahu/Ketu) special-aspect truncation to the universal 7th

> **Root mechanism (class-level).** FOUR independent hardcoded Mars/Jupiter/Saturn-only special-aspect tables, each with a silent universal-7th fallback for every other body: SPECIAL_DRISHTI_DEG (primitives.py, feeds all three gochara_* tools), NB_GRAHA_DRISHTI (ga_yoga_writer.py, feeds the Vipareeta Raja Yoga dilution loop), the local `special` dict in ga_vargas_writer.py::_compute_aspect_matrix (dead code today, latent landmine), against this same codebase's own CORRECT NODE_PARASHARI_ASPECTS={5,7,9} in ga_structural_writer.py. F-52 is the live present-day instance: Ketu's 5th aspect onto natal Venus and Rahu's 9th onto the natal 7th are both suppressed from this chart's own marriage-timing windows today. F-21 is the corollary: the w30_nodal_drishti compensator exists in engine.py but the built windows show no trace of it.

> **Class remediation lane.** LANE-NODAL: one shared nodal-aspect constant (5/7/9) imported by every drishti site, a lint forbidding a locally-defined graha->aspect dict, and a chart rebuild so the built gochara windows pick up the corrected engine.


##### F-20  ·  `TIER1-CORRECTNESS`

**Claim.** The core drishti_contact primitive shared by gochara_activation_get, gochara_forecast_get, and gochara_election_avoidance_get treats transiting Rahu and Ketu as casting ONLY the universal 7th-house aspect, never their classical 5th/9th special aspects -- the exact 'aspect-less/truncated shadow point' pattern R24 warns against. Confirmed both in code and empirically in live served data.

**Reproduce.**

```
Code read: platform/python-sidecar/services/gochara_grammar/primitives.py:187-194 (SPECIAL_DRISHTI_DEG={Mars:[90,180,210], Jupiter:[120,180,240], Saturn:[60,180,270]}; _DEFAULT_DRISHTI_DEG=[180.0] applies to every graha not in that dict, including Rahu/Ketu). Empirically confirmed live: evidence/gochara_election_avoidance_get__native_valid_daterange.json shows Rahu drishti_contact activity_terms only ever at the 7th-equivalent contact, never 5th/9th.
```

**Evidence.** `evidence/gochara_activation_get__native_valid_asof.json`

**Mechanism.** SPECIAL_DRISHTI_DEG (primitives.py:187-194) has no Rahu/Ketu entries; the comment above it does not even acknowledge nodes as a special case, unlike w30_nodal_drishti.py which explicitly documents the later-tradition classical basis for full nodal 5/7/9 aspects. Systemic: affects every transiting Rahu/Ketu contact computed across all three gochara_* tools, which all read the same primitive/table. Affects three live MCP tools: gochara_activation_get, gochara_forecast_get, gochara_election_avoidance_get.

**Proposed remediation.** LANE-NODAL — import one shared nodal 5/7/9 constant into `SPECIAL_DRISHTI_DEG` and add a lint forbidding a locally-defined graha→aspect dict anywhere in the tree.

##### F-52  ·  `TIER1-CORRECTNESS`

**Claim.** Live confirmation of F-20 (Rahu/Ketu 5th/9th aspect truncation) as a currently-active, concrete distortion in this exact chart's marriage journey: as of 2026-08-15, Ketu transiting Leo casts a real classical 5th aspect onto natal Venus (7th-lord + marriage karaka) and Rahu transiting Aquarius casts a real 9th aspect onto the natal 7th house -- both textbook nodal marriage-timing triggers -- yet gochara_activation_get's one active marriage window shows zero Rahu/Ketu contribution. Not hypothetical: this is F-20 actively suppressing a real, present-day nodal contribution to this chart's own marriage timing.

**Reproduce.**

```
gochara_activation_get(chart_id='482012f1-710e-4a25-994a-93821f5871aa', event_class='marriage', as_of_date='2026-08-15') -> windows[0].term_breakdown.activity_terms lists only Mars/Sun/Jupiter/Venus/Moon, no Rahu/Ketu; cross-check kala_now_get gochara_dual_reference for Rahu=Aquarius/Ketu=Leo positions
```

**Evidence.** `evidence/gochara_activation_get__native_marriage_today.json`

**Mechanism.** Same root cause as F-19/F-20: primitives.py:184-194,208,340 -- SPECIAL_DRISHTI_DEG omits Rahu/Ketu, both call sites fall through to 7th-only _DEFAULT_DRISHTI_DEG. This finding's contribution is the live-chart, present-day concrete confirmation of real impact, not a new mechanism.

**Proposed remediation.** Rebuild both charts' gochara windows after the F-20 fix and assert, in the build test, that nodal contributions appear in the marriage activation terms for this chart.

#### CL-08 Tier-honesty leaks (non-calibrated data served at full numeric precision / inflated labels)

> **Root mechanism (class-level).** The project's own P3-b suppression discipline ('shape_only classes must NEVER show absolute/numeric probability values end-to-end') is implemented in ka_kshetra only. Parallel surfaces invented their own permanent non-calibrated tags — confidence_basis:'structural_not_yet_empirical' (F-68, AnchorRecord's only-ever-set value), evidence_grade:'structural'/'prior_only' (F-69, hardcoded per row type), calibration_status:'prior_only' + mode:'STRUCTURAL' — and then serve 4-decimal posteriors, confidence bands, 0-10 provenance grades and 'CRITICAL' priority labels through with NO suppression gate keyed on the tag. F-119 is the highest-harm shape: five single-day acute-illness dates 2-3 years out, no probability, no confidence interval, and none of the resolution_disclosure/{resolution,is_timing_window} envelope that gochara_forecast_get attaches precisely so a caller can tell a decade-era context row from an actionable date. F-126 is the same confusion in the confidence field itself: confidence_band='high' describes retrieval determinism, not evidential weight, on a zero-result query.

> **Class remediation lane.** LANE-TIERSUPPRESS: one shared serving-layer gate that reads the epistemic tag and suppresses/rounds numerics + attaches resolution_disclosure, applied to L4 anchors, L5 insights, bo_upaya resonance and the assess_* gochara projection.


##### F-68  ·  `TIER1-CORRECTNESS`

**Claim.** phala_predictive_anchors_get serves precise numeric probability point-estimates (`posterior`, 4-decimal precision, e.g. 0.95, 0.02, 0.2475, 0.5367 across both canonical charts) and numeric confidence bounds (`confidence_low`/`confidence_high`) and multiple numeric lift-decomposition factors (`base_rate_value`, `promise_lift_value`, `activation_lift`, `trigger_lift`, `ayanamsha_robustness_modifier`) end-to-end, for anchors that are UNCONDITIONALLY and PERMANENTLY tagged `confidence_basis: 'structural_not_yet_empirical'` -- the tool's own posterior_provenance.cardinality_note states in-band 'this posterior has no underlying N of observed outcomes to report ... the empirically-calibrated analog ... is L5 query_calibration'. Every anchor sampled across BOTH canonical charts (482012f1 and 1c826d5a) carries this same non-calibrated tag with no exceptions -- confirming the tag is not conditional on any calibration state ever being reached (AnchorRecord's own dataclass default, never overridden by any code path). This is the exact defect class the project's own documented P3-b tier-suppression principle (ka_kshetra's shape_only/calibrated split: 'shape_only classes must NEVER show absolute/numeric probability values end-to-end') exists to prevent, applied one layer over in the L4 Phala predictive-anchor surface, which uses its own parallel terminology ('structural_not_yet_empirical' vs. 'calibrated') for the identical epistemic distinction but implements none of P3-b's serving-layer suppression discipline.

**Reproduce.**

```
mcp__marsys-jis-direct__phala_predictive_anchors_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa', limit:10}) and mcp__marsys-jis-direct__phala_predictive_anchors_get({chart_id:'1c826d5a-41cb-4450-b4dc-59d440e5f75a', limit:3}) -- inspect any anchor's confidence_basis + posterior + confidence_low/high fields.
```

**Evidence.** `evidence/phala_predictive_anchors_get__native_leak.json, evidence/phala_predictive_anchors_get__second_chart_leak.json`

**Mechanism.** platform/python-sidecar/services/ph_nimitta/engine.py:418 (`confidence_basis: str = 'structural_not_yet_empirical'` -- the AnchorRecord dataclass's only-ever-set value; module docstring lines 7-12 explicitly states 'Do NOT treat computed posteriors as calibrated until JL-009 is closed') combined with lines 289-357 (`compute_posterior`/`_posterior_confidence_band`, which unconditionally compute and attach the numeric `posterior`/`confidence_low`/`confidence_high`/`lift_vector` fields regardless of confidence_basis) and the serving path platform/src/lib/retrieval/registry/layers/L4_phala/query_predictive_anchors.ts, which passes these numeric fields straight through with no suppression gate keyed on confidence_basis.

**Proposed remediation.** LANE-TIERSUPPRESS — gate numeric posteriors and confidence bounds on `confidence_basis` through one shared serving-layer helper that suppresses or rounds when the tag is non-calibrated.

##### F-119  ·  `critical`

**Claim.** assess_health serves five single-day acute-illness dates two-to-three years out, with no probability, no confidence interval, and no resolution/is_timing_window disclosure. gochara_sweep(domain='health') returns 17 forward windows - 11 loss, 6 neutral, 0 favourable - whose top five are ALL event_class='illness_acute', temporal_shape='point', is_adverse=true, on the single days 2027-08-21, 2028-11-21, 2028-12-13, 2029-04-13 and 2029-07-18. gochara_forecast_get's schema documents a resolution_disclosure/{resolution, is_timing_window} contract precisely so a caller can tell a decade-era context row from an actionable date (PK-R-1: 'a decade-era row is CONTEXT, never a genuine timing claim'); the assess_health gochara_sweep surface carries NO such field on any row. A consuming LLM has no machine-readable way to know these are not actionable dates, and the response's shape actively invites relaying them.

**Reproduce.**

```
Q3. Call assess_health(chart_id=482012f1-710e-4a25-994a-93821f5871aa) and inspect .object.content.gochara_sweep.top_windows - note temporal_shape='point' with a single date and the absence of resolution_disclosure, probability, or confidence on every row.
```

**Evidence.** `pp2-audit/evidence/E2_q3_raw_assess_health.json | pp2-audit/evidence/E2_q3_health_outlook_trace.json`

**Mechanism.** The kala_gochara_windows signed-intensity field is projected into assess_* without carrying the MR-11(b) resolution_disclosure envelope that gochara_forecast_get attaches. A local intensity maximum becomes a 'point'-shaped row indistinguishable from a genuine day-resolution claim. Combined with calibration_maturity n_events=0 / skill_score=null (nothing has ever been validated), the surface presents uncalibrated field maxima in the visual grammar of dated medical predictions. This is the highest-harm shape in the system: an LLM relaying it verbatim tells a real person they will fall acutely ill on a named day three years hence.

**Proposed remediation.** Attach `gochara_forecast_get`'s `resolution_disclosure`/`is_timing_window` contract to `assess_*`'s `gochara_sweep` rows and suppress single-day point dates that carry no probability or interval.

#### CL-14 Uneven wiring of cross-cutting capabilities across a tool family

> **Root mechanism (class-level).** Capabilities that should be cross-cutting gates were implemented per-handler, so sibling tools presenting identical envelopes differ sharply in depth and contract. DOMAIN_READING_FAMILIES has no 'health' or 'relationship' key, so assess_health and assess_marriage can never return the documented reading/domain_completeness/completeness_directive layer on any chart or budget setting while assess_career does (F-14/F-15/F-124 — re-verified live this pass: assess_marriage still ships no `reading` field). The mandatory B.11 orientation pre-fetch is on assess_* only, so kala_upaya_get can serve a PACT promise-DENIAL — the most interpretively loaded output in the estate — with no orientation_ok field at all (F-125). The honest budget-echo contract (budget_kb_applied/requested + merged drill pointers) exists in finalizeMcpBudget but not in the applyAutoBudgetToEnvelope path used by ganita_planet_get and siblings (F-46).

> **Class remediation lane.** LANE-PARITY: promote reading-layer attachment, B.11 orientation and budget-echo to shared middleware over the tool registry rather than per-handler code, and add a family-parity test.


##### F-14  ·  `TIER1-CORRECTNESS`

**Claim.** assess_health never returns the documented W7 substance-inline reading digest / domain_completeness / completeness_directive fields, on any chart or budget setting, because DOMAIN_READING_FAMILIES has no 'health' entry.

**Reproduce.**

```
mcp__marsys-jis-direct__assess_health({chart_id: '482012f1-710e-4a25-994a-93821f5871aa', reading_depth: 'deep_dive'}) -- inspect top-level keys, 'reading' and 'domain_completeness' are absent
```

**Evidence.** `evidence/assess_health__native_deep_dive.json`

**Mechanism.** platform-mcp/src/tools/registry_bridge.ts:1034 (DOMAIN_READING_FAMILIES missing 'health' key) + :1568-1574 (attachDomainReading early-returns on families_total===0)

**Proposed remediation.** Add a `'health'` key to `DOMAIN_READING_FAMILIES` — or better, promote reading-layer attachment to registry middleware — so the documented layer exists for every `assess_*` sibling.

##### F-15  ·  `TIER1-CORRECTNESS`

**Claim.** assess_marriage never returns the documented W7 substance-inline reading digest / domain_completeness / completeness_directive fields, on any chart or budget setting, because DOMAIN_READING_FAMILIES has no 'relationship' entry (assess_marriage's internal domain key).

**Reproduce.**

```
mcp__marsys-jis-direct__assess_marriage({chart_id: '482012f1-710e-4a25-994a-93821f5871aa', reading_depth: 'deep_dive'}) -- inspect top-level keys, 'reading' and 'domain_completeness' are absent
```

**Evidence.** `evidence/assess_marriage__native_deep_dive.json`

**Mechanism.** platform-mcp/src/tools/registry_bridge.ts:1034 (DOMAIN_READING_FAMILIES missing 'relationship' key) + :1568-1574 (attachDomainReading early-returns on families_total===0). Same root cause and same file as F-14 -- one fix (adding health/relationship keys to DOMAIN_READING_FAMILIES) likely closes both.

**Proposed remediation.** Add the `'relationship'` key in the same patch, and add a family-parity test asserting all four `assess_*` siblings expose `reading` / `domain_completeness` / `completeness_directive`.

#### CL-15 Cross-tool incoherence — unreconciled contradictory verdicts on the same question

> **Root mechanism (class-level).** Two surfaces compute the same question over the same substrate and neither consumes nor flags the other's verdict. F-110 (the single most consequential finding in the corpus): for the identical chart, domain and date the marriage-timing path returns a tier_1_high relationship projection for 2027-10-20..2030-04-03 narrated as 'High probability (>=70% convergence, clear activation)', while kala_upaya_get(domain=relationship) returns pact_status='denied_at_promise' graded strong on 63 fact_ids — the two verdicts SHARE 5 fact_ids including Venus debilitated in D9, and assess_marriage additionally certifies contradictions.status='no_contradictions_in_domain'. kala_ahead_get names the cause in its own coverage block ('promise_gated_forecasting: not_in_corpus — Law-3 PACT gating is not yet applied to these raw windows') but still narrates the unqualified probability. Which answer a real person receives is decided by which tool the consuming LLM picks, and the natural tool for 'when will I marry' is the one that omits the denial. F-49 is the same shape on remedies: three surfaces disagree on which graha needs remediation.

> **Class remediation lane.** LANE-PROMISEGATE: join the PACT promise verdict into every forward-projection surface and suppress/downgrade projections the promise chain denies; where two surfaces can disagree, require an explicit reconciliation field rather than silence.


##### F-49  ·  `TIER1-CORRECTNESS`  ·  *also manifests as CL-03*

**Claim.** The three remedy surfaces for the native chart DISAGREE on which planet needs remediation. bodha_remedies_get (unfiltered) independently ranks Venus #1/critical priority. kala_upaya_get for domain='marriage' AND domain='health' both return interventions dominated by 50 identical Saturn-targeted rows and never surface Venus at all, because pact_query's diagnosis failed to name a specific targeted graha for marriage, which silently disabled the one filter that could have scoped remedies correctly.

**Reproduce.**

```
bodha_remedies_get(chart_id='482012f1-710e-4a25-994a-93821f5871aa') -> resonance_ranked[0].graha='Venus', priority='critical'. Then kala_upaya_get(chart_id=..., domain='marriage') and domain='health' -> both include 50 identical Saturn-targeted rows, no Venus row in either.
```

**Evidence.** `evidence/bodha_remedies_get__unfiltered.json`

**Mechanism.** platform-mcp/src/lib/kala_upaya_diagnosis.ts:507 -- callPlatformPrimitive('mitigation_map', {chart_id, limit:50}, principal) passes neither domain nor targetedGraha, so this intervention source is structurally domain/graha-blind. Contrast with kala_upaya_diagnosis.ts:508-511 (bodha_rm_prescriptions_get / query_remedies_for_chart), which DO receive targetedGraha -- but that filter silently no-ops to 'return everything' whenever pact_query's diagnosis fails to name a specific graha, exactly what happened for domain='marriage'.

**Proposed remediation.** Pass the PACT-diagnosed target graha through to `kala_upaya_get`'s filter, and where the diagnosis names none, fall back to the Bodha resonance rank-1 rather than silently disabling the only scoping filter.

##### F-110  ·  `critical`

**Claim.** CONFIDENCE LAUNDERING (top-severity). For the identical chart, domain and date, the marriage-timing path (assess_marriage + kala_ahead_get domain=relationship) returns a tier_1_high relationship projection for 2027-10-20..2030-04-03 narrated as 'High probability (>=70% convergence, clear activation)', while kala_upaya_get(domain=relationship) returns pact_status='denied_at_promise' - 'The rasi checklist does not promise this matter... no later stage can deliver what the rashi itself does not promise' - graded strong on 63 fact_ids. The two verdicts share 5 fact_ids (incl. d332fe1dbda74ea0, Venus debilitated in D9): SAME evidence, OPPOSITE conclusions, no reconciliation anywhere. assess_marriage additionally asserts contradictions.status='no_contradictions_in_domain', actively certifying an absence of tension in the exact domain the promise-chain denies. kala_ahead_get names the cause in its own coverage block: 'promise_gated_forecasting: not_in_corpus - Law-3 PACT gating ("pressure without delivery") is not yet applied to these raw windows.' The system HOLDS the promise verdict and the forecaster does not consume it. Which answer a real person receives is determined entirely by which tool the consuming LLM happens to pick - and the natural tool for 'when will I marry' is the one that omits the denial. This is the exact failure mode a predictive astrology system must not have: a confidently-stated, precisely-dated marriage prediction over a chart the same server judges does not promise marriage.

**Reproduce.**

```
Q1 'When will I marry?' + Q4 'What remedy helps me now?'. Call kala_ahead_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, domain='relationship', horizon_years=10) then kala_upaya_get(chart_id=same, domain='relationship', as_of_date='2026-08-15'). Compare .projections[0].probability_tier ('tier_1_high') against .diagnosis.pact_status ('denied_at_promise'). Inspect E2_q1_marriage_timing_trace.json and E2_q4_remedy_now_trace.json.
```

**Evidence.** `pp2-audit/evidence/E2_q1_marriage_timing_trace.json | pp2-audit/evidence/E2_q4_remedy_now_trace.json | pp2-audit/evidence/E2_q4_raw_kala_upaya.json | pp2-audit/evidence/E2_q1_raw_assess_marriage.json`

**Mechanism.** kala_bhavishya/kala_activation forward windows are emitted without joining the PACT promise verdict that pact_query/kala_upaya_get already computes. The gap is disclosed inside kala_ahead_get's coverage array as 'not_in_corpus' prose, but the projection is still narrated with an unqualified '>=70%' probability statement rather than being suppressed, downgraded, or flagged in the reading/verdict. A consumer reading the reading/verdict/falsifier - the fields designed to be read - never sees the caveat.

**Proposed remediation.** LANE-PROMISEGATE (highest-priority lane in this report) — join the PACT promise verdict into every forward-projection surface, suppressing or explicitly reconciling any projection the promise chain denies, and forbid a `no_contradictions_in_domain` certification in a domain the promise chain has denied.

#### CL-17 Malformed source data crashing or leaking through unguarded parsers

> **Root mechanism (class-level).** FOUR rows in brahma_prospective_ledger carry a PostgreSQL EMPTY daterange literal in observation_window (re-confirmed live this pass: 4 rows, chart 482012f1). Neither reader guards for it, and the SQL-level `observation_window IS NOT NULL` filter does not catch it because an empty range is itself non-NULL — only its bounds are. The TypeScript path throws out of parseDaterange and serves String(err) verbatim, so standing_predictions_read has been 100% unusable for this chart (still is: PR #1287 is OPEN, never merged, and the live call still returns 'parseDaterange: could not parse daterange literal empty'). The Python path does float(None) in mi_bhara's falsifier-resolution phase and takes the ENTIRE calibration-plane build down with an uncaught TypeError (asset_throughput.state='error' confirmed live, last_built_at 2026-08-13). One data repair plus two guards closes both.

> **Class remediation lane.** LANE-EMPTYRANGE: repair or nullify the 4 rows, add isempty() guards on both read paths, and add a NOT isempty(observation_window) CHECK constraint so it cannot recur.


##### F-01  ·  `TIER1-CORRECTNESS`

**Claim.** standing_predictions_read returns is_error:true for a valid native chart relationship query.

**Reproduce.**

```
MCP standing_predictions_read {chart_id:'482012f1-710e-4a25-994a-93821f5871aa'}
```

**Evidence.** `evidence/standing_predictions_read__native_default_repro.json`

**Mechanism.** Live open ledger rows include four interval rows whose observation_window renders as PostgreSQL literal 'empty' (evidence/sql__f01_empty_ledger_windows.txt). The L4 handler maps every open row through toServed (platform/src/lib/retrieval/registry/layers/L4_phala/query_prospective_ledger.ts:191), which calls deriveWindowFields (lines 66-68); deriveWindowFields passes a truthy 'empty' string to parseDaterange (platform/src/lib/lel/prospective_ledger.ts:591-594), whose regex fails and throws (lines 758-760). The handler catches it and serves String(err) in content.error (query_prospective_ledger.ts:230-234), leaking the parser literal. Fix commit 525188467 exists locally but is not an ancestor of HEAD, and the live MCP still reproduces the failure.

**Proposed remediation.** LANE-EMPTYRANGE — repair or nullify the four empty-daterange rows, add `isempty()` guards on both read paths, add a `NOT isempty(observation_window)` CHECK constraint, and merge PR #1287.

#### CL-19 Chart-scope entitlement boundary crossed inconsistently

> **Root mechanism (class-level).** Chart-scope authorization is enforced at exactly one route boundary (isPerChartPrimitive -> authorizeChartAccess in /api/mcp/primitives/[tool]), and paths cross it unevenly. bodha_bundle_get — the tool whose entire purpose is the B.11 whole-chart-read floor — fans out over an internal HTTP loopback whose principal fails that gate for every scope:'per_chart' sub-capability, so 5 of 8 subsystems (MSR, CGM, LEL, PANCHANG, DASHA) error on every call for both ground-truth charts while the 3 backed by scope:'global' capabilities always succeed (F-30/F-74/F-127). The mirror-image failure: kala_now_get performs no entitlement/existence check at all before doing substantial work, returning a full successful-looking envelope for a nonexistent chart UUID (F-38). The bundle degrades honestly (b11_floor_passed:false), but the B.11 floor tool is nonetheless majority-failed on every call.

> **Class remediation lane.** LANE-ENTITLEMENT: give the internal bundle caller a real principal (or resolve sub-capabilities in-process), and apply one uniform chart-existence + entitlement precondition to every chart-scoped handler.


##### F-30  ·  `TIER1-CORRECTNESS`

**Claim.** bodha_bundle_get (the B.11 whole-chart-read floor's own bundle tool) reports status='degraded' with 5 of its 7 constituent subsystems (MSR, CGM, LEL, PANCHANG, DASHA) erroring on every call, reproducibly, on both the native and zero-history ground-truth charts -- only UCN/RM/CDLM ever fire successfully. The tool discloses this honestly (b11_floor_passed:false, explicit sub_errors_note) rather than laundering it into a false-complete envelope, but the aggregate capability is nonetheless broken: a caller relying on this tool for a genuine whole-chart read gets a majority-failed bundle every time.

**Reproduce.**

```
mcp__marsys-jis-direct__bodha_bundle_get({chart_id: '482012f1-710e-4a25-994a-93821f5871aa'}) and mcp__marsys-jis-direct__bodha_bundle_get({chart_id: '1c826d5a-41cb-4450-b4dc-59d440e5f75a'}) -- both return status:'degraded' with identical sub_errors:['MSR','CGM','LEL','PANCHANG','DASHA']
```

**Evidence.** `evidence/bodha_bundle_get__native_primary.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE -- five independent sub-tool failures (MSR, CGM, LEL, PANCHANG, DASHA) inside the bundle dispatcher have not been individually traced to file:line in this pass; each would need its own root-cause investigation (this bundle tool's holistic_bundle route is bundle_adapters-based, distinct from the callPlatformPrimitive whitelist class in F-02/F-07/F-11). Flagged as a priority item for the next investigative pass given its centrality to B.11 whole-chart-read discipline.

**Proposed remediation.** LANE-ENTITLEMENT — give `bundle_adapters`' internal loopback caller a real principal (or resolve the sub-capabilities in-process) so `scope:'per_chart'` sub-tools clear `authorizeChartAccess`.

##### F-74  ·  `TIER1-CORRECTNESS`

**Claim.** F-30 deep dive, root cause confirmed for all 5 subsystems as ONE shared mechanism (not 5 separate causes): bodha_bundle_get's MSR/CGM/LEL/PANCHANG/DASHA sub-tool calls all resolve, via bundle_adapters.ts's internal HTTP loopback to /api/mcp/primitives/[tool], to registry capabilities with scope:'per_chart' (msr_sql, cgm_graph_walk, lel_query/query_life_events, get_panchanga, get_dashas -- confirmed by reading each capability's own `scope:` declaration in source) -- which triggers an authorizeChartAccess entitlement gate inside the primitives route that the 3 surviving sub-tools (UCN/RM/CDLM, all backed by the single scope:'global' query_classical_texts/vector_search capability) skip entirely via the identical isPerChartPrimitive() guard. This split is deterministic (100% reproducible, both charts, repeated calls) and exactly matches the observed 5-fail/3-succeed pattern -- confirming the failure is architectural (a per-chart-scope gate boundary), not 5 independent bugs. I independently verified the underlying capabilities themselves are healthy: calling bodha_signals_get and bodha_graph_subgraph_get directly (bypassing the bundle's internal loopback) with equivalent params returned full, correct, real data for the native chart. Separately (a genuinely distinct, compounding defect, not a 6th sub-tool cause): bundle_adapters.ts's callPrimitive() discards the real upstream HTTP status code behind a generic `throw new Error('HTTP ${response.status}')`, so the exact reason the per-chart gate rejects the internal bundle-calling principal (400 CHART_REQUIRED? 401 entitlement denial? 500 uncaught exception in the unguarded resolveMcpPrincipalRole/authorizeChartAccess block at route.ts:207-208?) is unrecoverable from the served response and was NOT pinned in this pass (server-log access would be required) -- marked DIAGNOSIS-INCOMPLETE for that last-mile step only. DISCLOSURE VERDICT: honestly disclosed, not silently masked -- b11_floor_passed:false and the explicit sub_errors_note both correctly tell a caller not to treat the bundle as a complete whole-chart read.

**Reproduce.**

```
mcp__marsys-jis-direct__bodha_bundle_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa'}) and ({chart_id:'1c826d5a-41cb-4450-b4dc-59d440e5f75a'}) -- both degraded, sub_tools_errored:['MSR','CGM','LEL','PANCHANG','DASHA'], sub_tools_fired:['UCN','RM','CDLM']; contrast mcp__marsys-jis-direct__bodha_signals_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa'}) and bodha_graph_subgraph_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa'}), both of which succeed fully when called outside the bundle
```

**Evidence.** `evidence/bodha_bundle_get__F30_rootcause_trace.json`

**Mechanism.** platform/src/lib/mcp/bundle_adapters.ts:274-303 (buildHolisticParams, resolves each sub-tool to its primitive toolName) + :373-376 (executeHolisticBundle fan-out) + :131-151 (callPrimitive, the shared HTTP-loopback caller for all 8 sub-tools) => platform/src/app/api/mcp/primitives/[tool]/route.ts:200-218 (per_chart entitlement gate: `if (isPerChartPrimitive(mcpToolName)) { ...authorizeChartAccess...if (perm==='deny') return 401 }`) => platform/src/lib/retrieval/registry/tool_name_bridge.ts:613-620 (isPerChartPrimitive, the classifier). Capability scope declarations confirmed individually: query_signals.ts:230 scope='per_chart' (MSR), traverse_chart_graph.ts:140 scope='per_chart' (CGM), query_life_events.ts:99 scope='per_chart' (LEL), get_panchanga.ts:52 scope='per_chart' (PANCHANG), get_dashas.ts:188 scope='per_chart' (DASHA), query_classical_texts.ts:124 scope='global' (UCN/RM/CDLM, all three route through this one capability with different source_filter values). Error-swallowing confirmed at bundle_adapters.ts:149.

**Proposed remediation.** Same fix as F-30, plus stop discarding the real upstream HTTP status in `callPrimitive()` so an authorization failure is never reported to the caller as a generic `tool_error`.

#### CL-20 Classical-derivation defects (wrong predicate, or technique with no computed representation)

> **Root mechanism (class-level).** The classical rule is either evaluated with the wrong predicate or has no representation at all, while the reading_checklist still certifies the unit as covered. F-66: Chatra and Ardhachandra Yoga fire on a chart whose 7 planets occupy only 4 distinct houses, because the detector's test is containment (`all(p in ps_in_houses for p in placed)`) rather than exact 7-house coverage with one planet per house. F-62: the dignity classifier never emits 'moolatrikona' anywhere, chart-wide — natal Jupiter at 9.79° Sagittarius is served as 'own' — which systematically under-scores Sthana Bala (MT=45 vs Own=30 shashtiamsha) for any graha in its own MT range. F-113: natal D1 dignity-in-bhava for the 7th house is in NO leg of assess_marriage's pipeline; Saturn EXALTED in Libra in the 7th (2nd-strongest graha in the chart) never appears — 'exalted' occurs zero times in the whole 158KB response, re-verified live this pass — while the generic ganita_dasha_lord_capability_get surfaced it in ~6KB. F-107/F-108: cross-varga (D2/D11/Indu Lagna) convergence and bhavat-bhavam have no fact_category, signal or checklist unit anywhere.

> **Class remediation lane.** LANE-CLASSICAL: re-derive each Nabhasa/dignity detector against its cited BPHS rule with a golden-chart test; add a direct 7th-house/7th-lord/karaka fact join to assess_marriage; register bhavat-bhavam and cross-varga convergence as first-class checklist units (even if initially not_built) so their absence is disclosed.


##### F-62  ·  `TIER1-CORRECTNESS`

**Claim.** The graha_dignity_per_varga.dignity_state vocabulary never emits 'moolatrikona' anywhere in the native chart's data (confirmed chart-wide across every varga and every graha via direct SQL ILIKE search, zero rows), collapsing this classically-distinct dignity tier into plain 'own'. Concrete instance: natal Jupiter sits at 9.79deg Sagittarius (D1), squarely inside Jupiter's classical Moolatrikona range (Sagittarius 0-10deg per BPHS Ch.4's moolatrikona table; Own-only applies 10-30deg) -- yet D1_JUP.dignity_state is served as 'own', not 'moolatrikona'. This is not a cosmetic labeling gap: Moolatrikona and Own carry different point values in classical Sthana Bala (positional strength, one of the six Shadbala components) -- MT=45 shashtiamsa vs Own=30 -- so any Sthana Bala / overall Shadbala score computed from this dignity_state systematically under-scores every graha whose natal degree happens to fall in its own Moolatrikona range, native chart or otherwise.

**Reproduce.**

```
mcp__marsys-jis-direct__ganita_chart_facts_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa', fact_subject:'D1_JUP', category:'graha_dignity_per_varga'}) returns dignity_state:'own'; cross-check JUP longitude_sidereal=249.787497023181deg from ganita_positions_get (Sagittarius 9.7875deg, sign starts 240deg) against classical Moolatrikona table (Jupiter MT = Sagittarius 0-10deg). Confirm vocabulary gap via mcp__postgres__query("SELECT DISTINCT fact_value_text FROM chart_facts WHERE fact_category='graha_dignity_per_varga' AND fact_value_text ILIKE '%moola%'") which returns zero rows chart-wide, and mcp__marsys-jis-direct__ganita_chart_facts_get({chart_id:..., keyword:'moolatrikona'}) which also returns zero facts.
```

**Evidence.** `evidence/dignity_and_dasha_spotchecks.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE -- confirmed as a real, reproducible, chart-wide vocabulary gap at the data layer (the dignity classifier that writes graha_dignity_per_varga never emits the 'moolatrikona' token, only 'own'/'exalted'/'debilitated'/'friend'/'neutral'/'enemy'), but the specific ga_writers/* source file implementing sign-dignity classification was not located/read in this pass -- no code-level file:line citation is asserted for the root cause, only for the absence of the value in served/stored data.

**Proposed remediation.** LANE-CLASSICAL — emit `moolatrikona` from the dignity classifier against the BPHS MT degree ranges, and re-derive Sthana Bala with the 45-vs-30 ṣaṣṭyāṁśa split, with a golden-chart test on natal Jupiter at 9.79° Sagittarius.

##### F-66  ·  `TIER1-CORRECTNESS`

**Claim.** Chatra Yoga and Ardhachandra Yoga (Nabhasa Akriti class) fire on the native chart (482012f1) via ganita_yoga_firings_get even though the native chart's 7 classical planets occupy only 4 distinct houses (Sun/Mercury=10, Moon=11, Mars/Saturn=7, Jupiter/Venus=9) -- categorically failing both yogas' own classical formation rule (each requires the 7 planets to occupy 7 DISTINCT consecutive houses, one planet per house -- confirmed via ref_yogas_get's own formation_text: 'The seven planets in seven consecutive houses from the 7th (7-1)' for Chatra, 'seven consecutive houses beginning from a non-kendra' for Ardhachandra, both BPHS Ch.35). The engine's own served constituent_houses ([7,8,9,10,11,12,1] for Chatra, [5,6,7,8,9,10,11] for Ardhachandra) are synthetic 7-house window ranges that do not reflect the planets' actual houses and do not have one planet per house. By contrast Kedara Yoga (a DIFFERENT Nabhasa sub-class requiring only 'seven planets occupy four signs') correctly fires on this same chart, confirming the 4-distinct-houses reading is right and Chatra/Ardhachandra are the misfires, not a chart-data problem. Independent re-derivation of the other 8 sampled fired yogas (sasa, budha_aditya, vasi, anapha, sarasvati_yoga, dhana_yoga_2_5_9_11, raja_yoga_kendra_trikona, kedara) against classical rules and raw ganita_positions_get/ganita_chart_facts_get data confirmed all 8 as correct matches to their classical stated rule -- this is an isolated defect in the two 7-consecutive-house Nabhasa detectors, not a general yoga-engine failure.

**Reproduce.**

```
mcp__marsys-jis-direct__ganita_yoga_firings_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa'}) [chatra id=2680, ardhachandra id=2678, kedara id=2682 fired=true] cross-checked against mcp__marsys-jis-direct__ganita_positions_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa'}) for house_d1 of all 7 grahas, and mcp__marsys-jis-direct__ref_yogas_get({yoga_name:'chatra'|'ardhachandra'|'kedara'}) for the classical formation_rule_jsonb/formation_text.
```

**Evidence.** `evidence/ganita_yoga_firings_get__native_fired.json, evidence/ref_yogas_get__chatra_ardhachandra_kedara.json`

**Mechanism.** platform/python-sidecar/ga_writers/ga_yoga_writer.py:627-649 (the 'all_seven_planets_in_seven_consecutive_from' evaluation branch). Line 644: `if len(placed) >= 5 and all(p in ps_in_houses for p in placed):` only checks that every PLACED planet falls somewhere WITHIN a candidate 7-house window (containment/subset test) -- it never checks that all 7 houses in that window are actually occupied (coverage), nor that no house holds more than one of the 7 planets. Because the native chart's planets (all 7) happen to be clustered into houses {7,9,10,11}, that entire cluster is trivially a subset of the window [7,8,9,10,11,12,1] (start=7, Chatra's fixed single start) and of [5,6,7,8,9,10,11] (one of Ardhachandra's tried starts for a_panaphara_or_apoklima), so both fire despite houses 8/12/1 (Chatra) and 5/6 (Ardhachandra) holding zero planets and houses 7/9/10 holding 2 planets each -- the opposite of the classical 'one planet per house, all 7 houses filled' pattern both yogas require. The Sankhya-count sibling branch (lines 547-555, `distinct_signs_occupied`) is correctly implemented (exact count match) and is why Kedara fires correctly on the same data.

**Proposed remediation.** Replace Chatra/Ardhachandra's containment test with exact seven-distinct-consecutive-house coverage (one planet per house), and add a golden-chart regression pinning this native's four-distinct-house configuration as a non-firing case.

##### F-113  ·  `critical`

**Claim.** assess_marriage omits the chart's single most consequential 7th-house fact. The string 'exalted' appears ZERO times in the entire 147,294-byte assess_marriage response. Saturn is EXALTED in Libra in the 7TH HOUSE (Vishakha, shadbala 7.83 - the 2nd-strongest graha in the chart), and Venus - the 7th lord and stored karaka for domain 'marriage' - sits in the bottom strength quartile (shadbala_percentile 0.25, warning_tier 'watch'). Neither fact appears anywhere in the marriage assessment. Both were surfaced incidentally, in ~6KB, by ganita_dasha_lord_capability_get - a generic dasha tool called for an unrelated question. The domain-specialised tool missed what the generic tool found.

**Reproduce.**

```
Q1 vs Q5. Run: grep -c 'exalted' on the assess_marriage spill file (returns 0). Then call ganita_dasha_lord_capability_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa) and ganita_dasha_periods_get(chart_id=same, ayanamsha_id='lahiri_chitrapaksha', as_of_date='2026-08-15', all_levels=true) and read the Saturn rows (lord_natal_house_d1=7, lord_natal_dignity_d1='exalted').
```

**Evidence.** `pp2-audit/evidence/E2_q1_raw_assess_marriage.json | pp2-audit/evidence/E2_q5_current_dasha_trace.json`

**Mechanism.** assess_marriage's house_analysis leg is driven by bodha_question_lenses ranked signals rather than by a direct 7th-house/7th-lord/karaka fact join. Its varga_analysis leg reads D9 only. So natal D1 dignity-in-bhava for the 7th - the first thing any acharya looks at - is in no leg of the pipeline. The reading_checklist reports 'bhava_bhavesha: served' on the strength of the CDLM/lens path, which makes the omission invisible: the checklist certifies the unit as covered while the actual placement never surfaces.

**Proposed remediation.** Add a direct natal D1 7th-house / 7th-lord / kāraka dignity join to `assess_marriage`'s pipeline, with a test asserting the chart's exalted 7th-house Saturn appears in the response.

#### CL-21 Response-envelope shape mismatch (double-enveloping) — top level contradicts nested payload

> **Root mechanism (class-level).** The registry capability wraps its own response in {content:{...}} and the MCP handler then reads content['rows'] one nesting level too shallow, so the primary field is always empty while the real rows sit at content['content']['rows']. bodha_discoveries_get's discoveries/total/returned are permanently empty/zero for this reason (F-16), and the SAME response simultaneously carries judgment_flags:[{code:'hollow_envelope_no_data_rows'}] at the top level and 15 fully-populated discovery objects at content.content.rows (F-128) — the envelope actively contradicts its own payload.

> **Class remediation lane.** LANE-ENVELOPE: one typed unwrap helper for callRegistryCapability results plus a test asserting top-level counts equal nested row counts.


##### F-16  ·  `TIER1-CORRECTNESS`

**Claim.** bodha_discoveries_get's primary discoveries field (and total/returned/min_salience_filter_applied) is always empty/zero because the handler reads content['rows'] one nesting level too shallow -- the registry capability response is double-enveloped and the real data lives at content['content']['rows'].

**Reproduce.**

```
mcp__marsys-jis-direct__bodha_discoveries_get({chart_id: '482012f1-710e-4a25-994a-93821f5871aa', domain: 'wealth', min_salience: 0.5, limit: 5}) -- compare top-level discoveries:[]/total:0 against content.content.rows (5 real rows) and content.content.total_matching (29)
```

**Evidence.** `evidence/bodha_discoveries_get__native_wealth_minsalience.json`

**Mechanism.** platform-mcp/src/tools/register_p1_synthesis.ts:611-618 -- callRegistryCapability('marsys://tool/L2/query_discoveries', ...) returns an object already shaped {content: {rows, total_matching, ...}, is_error} (query_discoveries.ts:196-199 wraps its own response in {content: {...}}), but line 617-618 reads content['rows'] without unwrapping the extra content.content level, so allRows is always [].

**Proposed remediation.** LANE-ENVELOPE — add one typed unwrap helper for `callRegistryCapability` results plus a test asserting top-level counts equal nested row counts.

---

### §3.2 — TIER 2 — HONESTY & INTEGRITY  (53 findings)

*The answer may be right but the envelope around it misreports scope, size, calibration, provenance or determinism.*

#### CL-01 Registered-but-unreachable capability (dispatch/registration wiring gap)

> *Class root mechanism and remediation lane stated in full at §3.1; CL-01 spans multiple tiers.*


##### F-73  ·  `TIER2`

**Claim.** kala_now_get's (and identically kala_explain_get's) gochara_narrative.field_gochara_alignment is 'insufficient_data' UNCONDITIONALLY for every chart and every domain -- not a marriage-specific or even a low-signed-intensity-specific symptom. Root cause: the narrative composer calls a registry-capability URI, marsys://tool/L4/gochara_forecast_get, that has NO matching registration anywhere in platform's retrieval registry (grep -rn "uri: '[^']*gochara[^']*'" across every layers/*/index.ts in platform/src returns zero hits; grep -rn 'marsys://tool/L4/gochara' likewise zero hits). Every call 404s against /api/retrieval/capability, which fetchGocharaForecastWindows() silently converts to an empty active_windows array, which in turn forces field_gochara_alignment to 'insufficient_data'. This reproduces prior finding #4 with a concrete mechanism and confirms the prior diagnosis 'blamed the wrong subsystem': the underlying kala_gochara_windows substrate is fully healthy (22+ event classes, 4627 marriage rows alone, real active windows spanning today confirmed via direct DB query and via the standalone gochara_activation_get/gochara_forecast_get MCP tools) -- the defect is entirely inside kala_now_get/kala_explain_get's own internal narrative-assembly code reaching for a capability that was never wired into the registry, one layer above the substrate a naive diagnosis would blame. This is a DIFFERENT root cause from F-53 (the domain='marriage' vs domain='relationship' naming trap in gochara_activation_get/gochara_forecast_get themselves) -- F-53 affects direct callers of those two tools with a bad domain value; this finding affects kala_now_get/kala_explain_get's own internal call, for every chart/domain, regardless of what value (if any) a caller ever passes.

**Reproduce.**

```
mcp__marsys-jis-direct__kala_now_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa'}) -> gochara_narrative:{active_windows:[], field_gochara_alignment:'insufficient_data', narrative_tier:'thin'}; grep -rn "uri: '[^']*gochara[^']*'" platform/src (zero matches) confirms no registered capability behind the URI the narrative composer calls
```

**Evidence.** `evidence/gochara_marriage_diagnosis__native.json`

**Mechanism.** platform-mcp/src/tools/kala_views/now.ts:1359-1394 (fetchGocharaForecastWindows) calling callRegistryCapability('marsys://tool/L4/gochara_forecast_get', ...) at line 1373 -- a URI absent from the entire platform/src/lib/retrieval/registry (confirmed via exhaustive grep, zero hits for any 'gochara'-containing registered capability URI); the 404 response makes callRegistryCapability (now.ts:120-153) return {content:null, ok:false}; fetchGocharaForecastWindows (now.ts:1381) then returns [] unconditionally on !resp.ok; buildGocharaNarrativeBlock (now.ts:1426-1428) sets field_gochara_alignment='insufficient_data' whenever activeWindows.length===0. Identical dead-URI reference at platform-mcp/src/tools/kala_views/explain.ts:476. Reads as a legitimate epistemic judgment ('insufficient_data') rather than disclosing that an internal call failed -- this is a masked failure, not an honestly-disclosed one (contrast with F-30/A4-F-63 below, which DOES disclose its failure explicitly).

**Proposed remediation.** Register the `gochara_forecast_get` capability URI in the retrieval registry (or call the tool directly), and make `fetchGocharaForecastWindows` surface a 404 as an explicit unreachable-capability disclosure instead of collapsing it into `'insufficient_data'`.

#### CL-02 Implemented backend with no serving consumer (dead data path + false 'no such data' assertion)

> **Root mechanism (class-level).** Real, correct, populated data or computation exists (reference_nakshatra 28 rows; brahma_dasha_systems 20 rows + a complete tested query_dasha_systems capability; tantric.yaml + l0_remedy_loader; the 6 per-varga saptavargaja components; mi_bhara's calibration plane) but no serving-layer code reads it. The surface silently falls back to a weaker path and, in F-04/F-22, emits a fallback_reason that positively asserts the structured table does not exist. Re-verified this pass: kala_field_skill holds 7 real rows for the native chart (n_events=7, weights_version v0_classical) while all 8 kala_* facades still hardcode calibration_maturity n_events=0 (see P4-F-140).

> **Class remediation lane.** LANE-DEADPATH: audit every fallback_reason/'no such table' literal against information_schema, and wire the existing capabilities (query_dasha_systems, reference_nakshatra, mi_bhara skill rows) into their declared consumers.


##### F-04  ·  `TIER2`

**Claim.** ref_nakshatra_get's description promises a structured nakshatra catalog (lord, devata, gender, gana, varna, nadi, pada lords, body part, symbol) but the tool always routes through unstructured classical-text hybrid search (structured_filter_applied:false), even though a live, fully-populated (28 rows) structured catalog table with exactly these fields (reference_nakshatra, managed by the bg_nakshatra writer, canonical per migration 302) exists in the database and is never queried by any serving-layer code.

**Reproduce.**

```
mcp__marsys-jis-direct__ref_nakshatra_get({nakshatra: 'purva_bhadrapada', limit: 5})
```

**Evidence.** `evidence/ref_nakshatra_get__F04_resolution.json`

**Mechanism.** RESOLVED (was DIAGNOSIS-INCOMPLETE): genuine wiring gap, not a total absence. Handler platform-mcp/src/tools/register_p1_reference.ts:410-447 unconditionally calls marsys://tool/L0/query_classical_texts and its fallback_reason string (line 440) / inline comment (line 428) both falsely assert 'No structured bg_nakshatra catalog table exists'. DB verification: `SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%nakshatra%'` returns reference_nakshatra (28 rows, canonical per migration 302_deprecate_reference_nakshatras.sql) with columns vimshottari_lord/presiding_deity/nakshatra_gender/gana/varna/nadi/body_part/symbol -- verified populated and correct for Purva Bhadrapada (jupiter/Aja Ekapada/Male/Manushya/Brahmin/Adi/left side/Front of a funeral cot). No file in platform/src or platform-mcp/src references reference_nakshatra or reference_nakshatras (grep-empty outside generated census artifacts). Root cause: the naming-convention search likely looked only for a 'bg_*'-prefixed table and missed the 'reference_*'-prefixed canonical one. See evidence/ref_nakshatra_get__F04_resolution.json.

**Proposed remediation.** LANE-DEADPATH — point `ref_nakshatra_get` at the live `reference_nakshatra` table and delete the `fallback_reason` literal that positively asserts the table does not exist.

##### F-22  ·  `TIER2`

**Claim.** ref_dasha_systems_get's description promises structured dasha-system fields (total years, planet sequence with period lengths, activation criteria, source authority) but always routes through unstructured classical-text hybrid search (structured_filter_applied:false), returning topically-irrelevant Muhurta Chintamani wedding-timing verses for a query_used:'dasha system' search -- even though a live, fully-populated (20 rows) structured table (brahma_dasha_systems) with exactly these fields exists AND a complete, correct, already-registered-and-tested capability (query_dasha_systems) that queries it already exists in the codebase, unused.

**Reproduce.**

```
mcp__marsys-jis-direct__ref_dasha_systems_get({system:'vimshottari', limit:10}) -- observe structured_filter_applied:false, query_used:'dasha system', and irrelevant marriage-muhurta citations returned instead of the Vimshottari 120-year 9-planet sequence
```

**Evidence.** `evidence/ref_dasha_systems_get__wiring_gap.json`

**Mechanism.** Handler platform-mcp/src/tools/register_p1_reference.ts:369-408 calls marsys://tool/L0/query_classical_texts; its inline comment (line 385-386) and emitted fallback_reason both falsely assert 'no structured bg_dasha_systems catalog table exists (confirmed absent from the migration set)'. DB verification: brahma_dasha_systems (20 rows) exists with columns canonical_id/name_en/total_cycle_years/base_unit/sequence_jsonb/computation_method/computation_pseudocode/conditions_for_use/school/classical_citations -- verified correct for Vimshottari (Ketu 7 + Venus 20 + Sun 6 + Moon 10 + Mars 7 + Rahu 18 + Jupiter 16 + Saturn 19 + Mercury 17 = 120 years, matching classical values exactly). A complete, correct, tested capability already querying this exact table exists at platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_dasha_systems.ts (uri marsys://tool/L0/query_dasha_systems, registered in index.ts:44, own test file present) but is never called by ref_dasha_systems_get and is not exposed as any MCP tool -- the fix is a one-URI-string change from query_classical_texts to query_dasha_systems, not new development.

**Proposed remediation.** Change `ref_dasha_systems_get`'s URI from `query_classical_texts` to the already-registered-and-tested `query_dasha_systems`, and delete the comment claiming the structured table was 'confirmed absent'.

##### F-61  ·  `TIER2`

**Claim.** graha_saptavargaja_bala_component.<graha>.saptavargaja_score is served with fact_value_num=null and fact_value_text=null for every graha on every call, chart-wide -- despite the fact_key being literally named '...score'. Only a jsonb pointer to 6 chart_divisionals.id UUIDs (not chart_facts.fact_id citation values) is served instead. Direct SQL resolution of the 6 pointers for SUN shows the real per-varga components DO exist and are individually correct (D1=7.5 Sama, D2=30 Own, D3=3.75 Shatru, D9=22.5 Adhi_Mitra, D12=7.5 Sama, D60=22.5 Adhi_Mitra, summing to a legitimate classical value of 93.75) -- the data is never aggregated into the score the fact_key promises, and a normal MCP-only caller has no queryable path to those chart_divisionals.id pointers (chart_divisionals is reachable per-varga via ganita_chart_facts_get's divisional_chart parameter, but only by fact_id, not by the raw table-row id used here, and only one varga at a time -- not as a resolvable citation from this pointer).

**Reproduce.**

```
mcp__marsys-jis-direct__ganita_strength_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa', offset:0}) -- observe every graha_saptavargaja_bala_component row has fact_value_num:null; cross-reference constituent_fact_ids against mcp__postgres__query("SELECT id,varga,sign,fact_value_num,fact_value_text FROM chart_divisionals WHERE id::text IN (<uuid list>)") which resolves to real, non-null, classically-sensible per-varga strength values.
```

**Evidence.** `evidence/ganita_strength_get__native_saptavargaja_null_score.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE -- confirmed at the data/serving level (the aggregation step that would sum the 6-7 per-varga components into a single saptavargaja_score is never executed or never written to chart_facts; the underlying per-varga inputs are proven present and correct via direct SQL), but the specific writer or serving-layer file/line responsible for emitting the null-with-pointer row instead of a summed value was not located/read in this pass.

**Proposed remediation.** Aggregate the six per-varga saptavargaja components into the score the fact_key names (or null it honestly), and cite resolvable `chart_facts.fact_id` values rather than raw `chart_divisionals` row ids.

##### F-70  ·  `TIER2`

**Claim.** calibration_maturity is hardcoded to noLelCalibrationMaturity() -- {n_events:0, prospective_resolutions:0, event_class_coverage:0, weights_version:null, skill_score:null} -- unconditionally, in ALL EIGHT kala_* view facades (kala_now_get, kala_priority_get, kala_ahead_get, kala_upaya_get, kala_ritual_get, kala_explain_get, kala_story_get, kala_elect_get), regardless of the target chart's actual LEL richness. Reproduced live: kala_now_get and kala_priority_get on the native chart (64 LEL events, 40 pre-2020) both serve calibration_maturity.n_events=0. This is a live reproduction of prior finding #3's discrepancy. It is NOT internally consistent with the rest of the system: mimamsa_calibration_get / mimamsa_insight_get (a separate, working L5 surface) report REAL non-zero calibration data for the identical chart_id -- calibration_summary.total_matches=57, mean_composite_score=0.495, with 6 calibrated_outlook insight_units whose n_support values (7+12+18+3+13+4=57) sum exactly to total_matches. A caller reading kala_now_get's calibration_maturity and mimamsa_insight_get's calibration_summary for the same chart gets two contradictory claims about whether calibration exists at all.

**Reproduce.**

```
mcp__marsys-jis-direct__kala_now_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa'}) and mcp__marsys-jis-direct__kala_priority_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa'}) -- both show calibration_maturity:{n_events:0,...}; contrast mcp__marsys-jis-direct__mimamsa_insight_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa', insight_type:'calibrated_outlook'}) -> calibration_summary.total_matches=57
```

**Evidence.** `evidence/kala_now_get__native_calibration_maturity_check.json`

**Mechanism.** platform-mcp/src/tools/kala_views/now.ts:1970, priority.ts:434, ahead.ts:1984, upaya.ts:427, ritual.ts:572, explain.ts:699, story.ts:756, elect.ts:761 -- each unconditionally passes `calibrationMaturity: noLelCalibrationMaturity()` into makeKalaEnvelope(), never reading any chart-specific value. The one real computation path that COULD populate this honestly -- platform/python-sidecar/pipeline/orchestrator/writers/mi_bhara.py's compute_calibration_maturity(), which writes to kala_field_weight_versions/kala_field_skill/kala_field_gof -- is never read by any file in platform-mcp/src or platform/src (grep for those three table names outside test files returns zero hits). This is a genuine wiring gap between a real backend computation and its own documented consumer field, not merely an aspirational placeholder: the tool descriptions themselves call it 'the honest zero stub at W0 -- no calibration plane exists yet', but the plane DOES exist and does compute real numbers (see A4-F-60 for why it currently can't reach the native chart specifically).

**Proposed remediation.** Point `makeKalaEnvelope`'s `calibrationMaturity` at `kala_field_skill` / `kala_field_weight_versions` instead of `noLelCalibrationMaturity()` — one read, eight facades.

##### F-140  ·  `TIER2`

**Claim.** ESCALATION of F-70, materially changing its severity: all eight kala_* view facades now serve calibration_maturity {n_events:0, prospective_resolutions:0, event_class_coverage:0, weights_version:null, skill_score:null} OVER real, present, non-null rows in the exact tables that field is supposed to read. kala_field_skill holds 7 rows for chart 482012f1 (released_at 2026-08-09T09:25:34Z) — a chart-wide rollup row with n_events=7, n_backfill=7, weights_version='v0_classical', skill_state='underpowered', plus six per-class rows (childbirth, foreign_settlement, marriage, relocation, separation, surgery, each n_events>=1) — and kala_field_weight_versions holds 1 row. When F-70 was filed the served zero could still be read charitably as 'the backend never computed anything anyway'; that reading is no longer available. The facades are not serving an aspirational stub over an empty backend, they are serving a hardcoded FALSE ZERO and a FALSE NULL weights_version over live data, on a field whose entire purpose is to tell a caller how much calibration this chart's timing claims rest on. This is the §N.8 earned-signal inversion: a signal reading 'no calibration exists' when calibration data demonstrably does exist and could be read in one SELECT.

**Reproduce.**

```
MCP kala_now_get {chart_id:'482012f1-710e-4a25-994a-93821f5871aa'} -> .calibration_maturity  ;  SQL: SELECT event_class,n_events,n_prospective,n_backfill,skill_score,skill_state,weights_version,released_at FROM kala_field_skill WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' ORDER BY event_class;  SELECT count(*) FROM kala_field_weight_versions
```

**Evidence.** `pp2-audit/p4_prior8_reverification.json (reverifications[2])`

**Mechanism.** Unchanged from F-70's diagnosis — platform-mcp/src/tools/kala_views/{now.ts:1970, priority.ts:434, ahead.ts:1984, upaya.ts:427, ritual.ts:572, explain.ts:699, story.ts:756, elect.ts:761} each unconditionally pass `calibrationMaturity: noLelCalibrationMaturity()` into makeKalaEnvelope() and never read a chart-specific value; no file in platform-mcp/src or platform/src references kala_field_weight_versions / kala_field_skill / kala_field_gof outside tests. What is NEW here is the other side of the gap: mi_bhara's compute_calibration_maturity() has SUCCESSFULLY WRITTEN those rows for this chart (2026-08-09), so the wiring gap is now demonstrably suppressing real data rather than papering over an empty table. Note this coexists with mi_bhara's CURRENT state='error' (F-71, re-confirmed live, last_built_at 2026-08-13) — the 2026-08-09 rows are from an earlier successful run and are stale-but-real. The fix is a read, not a computation. Defect class CL-02.

**Proposed remediation.** Same one-line read as F-70, now escalated: the hardcoded zero is actively suppressing live rows, so ship this ahead of F-70's queue position and add a test that the served `n_events` equals the stored rollup.

#### CL-03 Parameter accepted but never applied (no-op filter / silent value substitution)

> *Class root mechanism and remediation lane stated in full at §3.1; CL-03 spans multiple tiers.*


##### F-03  ·  `TIER2`

**Claim.** ref_remedies_by_category_list's limit/offset schema parameters are complete no-ops -- the underlying SQL never applies them -- so a populous category always fetches every row, gets serialized into one JSON string, and the generic response-budget trimmer hard-truncates that string mid-JSON when it exceeds 40KB, producing an unparseable payload with no recovery path.

**Reproduce.**

```
mcp__marsys-jis-direct__ref_remedies_by_category_list({category: 'mantra'}) vs mcp__marsys-jis-direct__ref_remedies_by_category_list({category: 'mantra', limit: 5}) -- both return result_hash sha256:ad8a27bbdc37a7b8f37586af5bfcaee7463895dd36599891073203a45008006c, proving limit is ignored
```

**Evidence.** `evidence/ref_remedies_by_category_list__mantra.json`

**Mechanism.** platform/src/lib/retrieve/remedy_tools.ts:171-188 (listRemediesByCategory.retrieve() reads only params?.category; SQL has no LIMIT clause, never reads params?.limit/offset) reached via platform-mcp/src/tools/register_p1_aliases.ts:1576-1583 (alias forwards {category, limit, offset} believing they're honored) -> oversized result hits platform-mcp/src/lib/response_budget.ts:462-488 (truncateLongStringsInPlace), hard-truncating mid-character with '...[truncated for budget]', producing invalid embedded JSON.

**Proposed remediation.** LANE-PARAMPARITY — apply `limit`/`offset` in `listRemediesByCategory`'s SQL and add a contract test asserting a changed `limit` changes the `result_hash`.

##### F-06  ·  `TIER2`

**Claim.** ref_remedies_chart_get's tool description promises 'chart-specific remedy suggestions,' but neither the MCP-facing parameter schema nor the server-side query implementation actually scope by chart -- chart_id cannot even be passed by a caller, and where the underlying capability does accept an optional chart_id it is used only for provenance/logging, never in the SQL WHERE clause.

**Reproduce.**

```
mcp__marsys-jis-direct__ref_remedies_chart_get({affliction:'Saturn', top_k:5}) -- schema accepts only {affliction, top_k}, no chart_id field exists
```

**Evidence.** `evidence/ref_remedies_chart_get__saturn_career_mars.json`

**Mechanism.** MCP alias: platform-mcp/src/tools/register_p1_aliases.ts:1563-1573 exposes only {affliction, top_k}, forwarding to primitive query_remedies_for_chart. Live server handler: platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:1437-1526 -- input_schema (1453-1468) declares chart_id optional with the code's own comment 'optional -- provenance only'; SQL at 1495-1504 has no chart_id predicate anywhere, and chart_id is not even reachable through the public alias tool's schema.

**Proposed remediation.** Either expose `chart_id` on the alias schema and put it in the SQL predicate, or rename the tool and correct its description to what it is — a global affliction-keyed remedy lookup.

##### F-08  ·  `TIER2`

**Claim.** phala_mitigation_get's domain parameter is silently ignored end-to-end -- passing domain='career' vs. omitting it entirely produces byte-identical results for the native chart, giving callers false confidence that domain-scoping occurred.

**Reproduce.**

```
mcp__marsys-jis-direct__phala_mitigation_get({chart_id: '482012f1-710e-4a25-994a-93821f5871aa'}) vs mcp__marsys-jis-direct__phala_mitigation_get({chart_id: '482012f1-710e-4a25-994a-93821f5871aa', domain: 'career'}) -- compare result.result_hash in both responses (both sha256:abbd452f...50a4d02)
```

**Evidence.** `evidence/phala_mitigation_get__native_domain_career.json`

**Mechanism.** platform-mcp/src/tools/register_p1_aliases.ts:1739-1747 (alias forwards {chart_id, domain} to callPlatformPrim('mitigation_map', ...)), routed via tool_name_bridge.ts:565 (mitigation_map -> query_remedy_program) to platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts:334-421 (queryRemedyProgramCapability). input_schema (357-364) only declares chart_id/intensity_tier/limit/offset; handler (367-421) never reads args['domain'] in the SQL WHERE clause -- dropped at the primitive boundary.

**Proposed remediation.** Declare and apply `domain` in `query_remedy_program`'s `input_schema` and WHERE clause, or document the parameter as advisory in the tool description.

##### F-26  ·  `TIER2-QUALITY`  ·  *also manifests as CL-02*

**Claim.** kala_life_arc_get advertises LEL life-event cross-linking (include_lel_events param, default true) that is entirely unwired: the parameter is accepted but never read, and the underlying SQL never joins to any LEL table -- confirmed absent even for the native chart's 64-event history.

**Reproduce.**

```
MCP kala_life_arc_get {chart_id:'482012f1-710e-4a25-994a-93821f5871aa', include_lel_events:true} -- inspect parvas[] for lel_events (absent)
```

**Evidence.** `evidence/kala_life_arc_get__lel_gap.json`

**Mechanism.** platform/src/lib/retrieval/registry/layers/L3_kala/query_life_arc.ts never reads include_lel_events and its SQL (lines 147-177) only selects kala_jivana_parva; the capability descriptor itself declares lel_capable:false (line 39).

**Proposed remediation.** Implement the LEL join in `query_life_arc` — or remove `include_lel_events` and align the descriptor's `lel_capable:false` with the advertised behaviour rather than with the code.

##### F-27  ·  `TIER2`

**Claim.** mimamsa_calibration_get's domain parameter is a complete no-op -- identical result_hash returned with and without it -- despite real, distinct 57-row calibration data (across 4 verdict classes) existing in the DB that a real domain filter should be able to narrow.

**Reproduce.**

```
mcp__marsys-jis-direct__mimamsa_calibration_get({chart_id: '482012f1-710e-4a25-994a-93821f5871aa'}) vs mcp__marsys-jis-direct__mimamsa_calibration_get({chart_id: '482012f1-710e-4a25-994a-93821f5871aa', domain: 'career'}) -- compare result_hash
```

**Evidence.** `evidence/mimamsa_calibration_get__valid_domain_native.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE on exact file:line -- recovered from a compressed agent summary after a concurrent-write race deleted the original finding's full detail (see audit-integrity note on this recovery in the P1 status report); the underlying observation (domain is DB-verified real but not honored) was independently reproduced and is not in question, only the precise source line was lost.

**Proposed remediation.** Apply `domain` in `mimamsa_calibration_get`'s query, add the parameter-parity contract test, and re-diagnose the file:line lost in the write race so the fix lands at the right site.

#### CL-04 Unreconciled domain/enum vocabularies + unvalidated input (false honest-zero)

> **Root mechanism (class-level).** At least four independent domain/enum vocabularies coexist (CANONICAL_DOMAINS 13 entries, register_d9_judgment SHASTRA_MAP 10 concepts, brahma_event_ontology.domain, the gochara window domain enum, six stored ayanamsha ids) and were never reconciled 1:1; no handler validates its input against its own vocabulary. An out-of-vocabulary value therefore falls through to an empty/neutral path that is byte-indistinguishable from a genuine negative result — and in F-40/F-53 it defeats the very not_covered refusal the tool's description says was added to prevent exactly this. F-24 is the same shape one file down: two DOMAIN regex lists in intent_scope_classifier.ts, only one of them fixed and it is not the one wired to the output.

> **Class remediation lane.** LANE-VOCAB: publish one canonical domain vocabulary, make every handler validate against it and return a typed UNKNOWN_DOMAIN error, and delete the duplicate regex/alias maps.


##### F-24  ·  `TIER2-QUALITY`

**Claim.** intent_classify collapses realistic questions to domains:['general'] and near-zero confidence despite a corrected regex list existing elsewhere in the same file that would recognize them.

**Reproduce.**

```
MCP intent_classify {query:'When will I get married?'} and {query:'Is this a good time to change jobs?'}
```

**Evidence.** `evidence/intent_classify__revalid.json`

**Mechanism.** platform-mcp/src/tools/intent_scope_classifier.ts:178-189 (DOMAIN_RULES, stale non-plural-safe regex, misses 'married'/'jobs') vs lines 232-233 (DEEP_DOMAIN_WORD, already-fixed regex, not wired to scope_tuple.domains output).

**Proposed remediation.** LANE-VOCAB — wire the already-corrected `DEEP_DOMAIN_WORD` regex to `scope_tuple.domains` and delete the stale duplicate `DOMAIN_RULES` list.

##### F-40  ·  `TIER2`

**Claim.** gochara_forecast_get's tool description explicitly documents a guarantee (the 'S4-05 fix'): passing `domain` gets 'an explicit not_covered refusal with a cross_pointer to the capable instrument (kala_windows_get) instead of relying on silence' whenever the sweep does not cover that domain — specifically to prevent a caller from misreading silence on a domain as an all-clear. Passing an unrecognized/garbage domain value ('nonexistent_domain_xyz', which cannot match any real domain) does NOT trigger this documented refusal path: `coverage.domains_not_covered` stays empty (it is computed independently of the requested filter, from the chart's own global sweep coverage) and the response instead silently returns `windows:[]` with a generic, unrelated empty_reason ('no kala_gochara_windows rows overlap this date_range/filter combination'). This is exactly the failure mode the tool's own documentation says it was fixed to prevent, just triggered by a misspelled/unknown domain string rather than a genuinely-uncovered real domain.

**Reproduce.**

```
mcp__marsys-jis-direct__gochara_forecast_get(chart_id='482012f1-710e-4a25-994a-93821f5871aa', date_range={start:'2026-08-15',end:'2026-11-15'}, domain='nonexistent_domain_xyz')
```

**Evidence.** `evidence/gochara_forecast_get__unknown_domain.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE — behavior confirmed live (domains_not_covered empty regardless of an unrecognized domain filter, no not_covered refusal fires); did not trace the gochara_forecast_get handler source in platform/src to pin the exact file:line where the domain filter is applied without vocabulary validation.

**Proposed remediation.** Compute `domains_not_covered` from the caller's requested filter rather than from the chart's global sweep, so the documented `not_covered` refusal fires for an unknown domain value as its own docstring promises.

##### F-41  ·  `TIER2`

**Claim.** judgment_query, when passed an unrecognized `domain` value ('nonexistent_domain_xyz', not one of the seven documented domain names), does not reject the call. Instead it silently treats the domain as if it were absent/undefined, computes and returns a large chart-wide 'orientation_context' payload (full entity_profiles across every graha/bhava, convergence_domains, thousands of resolved fact_ids), and only then reports the actual validation failure — 'judgment_query requires either domain (...) or bhava (1-12)' — nested three levels deep at `content.error`, inside an otherwise fully-populated v3 envelope (top-level `verdict`, `chart_header`, `epistemic`, `register`, `reading_contract` all present, no top-level `ok:false` or `is_error:true`). A caller checking only top-level envelope shape would reasonably conclude the call succeeded.

**Reproduce.**

```
mcp__marsys-jis-direct__judgment_query(chart_id='482012f1-710e-4a25-994a-93821f5871aa', domain='nonexistent_domain_xyz')
```

**Evidence.** `evidence/judgment_query__unknown_domain.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE — confirmed live via response shape only; did not trace the judgment_query handler source (likely platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts per the tool description) to pin the exact file:line where an unrecognized domain string falls through to the missing-domain branch instead of being validated against the enum up front.

**Proposed remediation.** Validate `domain` against the handler's own vocabulary and return a typed top-level `UNKNOWN_DOMAIN` error *before* computing and shipping the orientation payload.

##### F-42  ·  `TIER2`

**Claim.** ganita_dashas_get's `ayanamsha_id` parameter accepts any free-form string with no validation against the six known stored ayanamshas (lahiri_chitrapaksha, krishnamurti, raman, surya_siddhanta_classical, true_chitra, INVARIANT). Passing an unrecognized value ('not_a_real_ayanamsha') silently returns `rows:[], total:0` with no error or empty_reason disclosing that the ayanamsha itself is not recognized. Verified against a control call with identical chart_id and default window but `ayanamsha_id='lahiri_chitrapaksha'`, which returns 90 real dasha-period rows — proving the empty result for the bad ayanamsha value is a silently-swallowed invalid input, not an honest 'no data in this window' result. A caller who mistypes an ayanamsha name gets an indistinguishable-from-legitimate empty page.

**Reproduce.**

```
mcp__marsys-jis-direct__ganita_dashas_get(chart_id='482012f1-710e-4a25-994a-93821f5871aa', ayanamsha_id='not_a_real_ayanamsha')  -- compare to the same call with ayanamsha_id='lahiri_chitrapaksha'
```

**Evidence.** `evidence/ganita_dashas_get__unknown_ayanamsha_silent_empty.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE — confirmed live via the control-vs-test comparison; did not trace the get_dashas handler source (platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts per earlier grep) to pin the exact file:line where ayanamsha_id is used unvalidated in the underlying query.

**Proposed remediation.** Validate `ayanamsha_id` against the six stored ids and return a typed error instead of an empty page indistinguishable from a legitimate one.

##### F-55  ·  `TIER2`

**Claim.** judgment_query's domain resolver does not support 4 of the 13 domain values in the system's own CANONICAL_DOMAINS vocabulary (family, general, transition, travel) -- each call returns is_error:false but with an empty verdict and an embedded content.error, even though 'family' and 'transition' appear as live, high-salience entries in that SAME call's own orientation_context.convergence_domains digest (family convergence_count=5684, 2nd highest of all domains present). The tool's own error message is additionally stale: it lists only 7 domain names, omitting 3 more (moksha, character, residence) the SHASTRA_MAP source actually supports.

**Reproduce.**

```
judgment_query(chart_id='482012f1-710e-4a25-994a-93821f5871aa', domain='family')  # or domain='general'/'transition'/'travel'
```

**Evidence.** `evidence/judgment_query__family.json`

**Mechanism.** platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts SHASTRA_MAP (~lines 103-139) has no bhava mapping for family/general/transition/travel; BHAVA_TO_DOMAIN reverse-lookup (~162-175) also has no fallback for them. Error message string at ~345-397 is stale relative to the map's actual 10-concept coverage.

**Proposed remediation.** Reconcile `CANONICAL_DOMAINS` with `SHASTRA_MAP` 1:1, add resolvers for family/general/transition/travel, and generate the error message's domain list from the live map so it cannot go stale.

#### CL-05 Response-budget / trim defects (unenforced ceiling, inverted density priority, unreachable data)

> *Class root mechanism and remediation lane stated in full at §3.1; CL-05 spans multiple tiers.*


##### F-13  ·  `TIER2`

**Claim.** kala_ritual_get has no response-size control on either mode (Mode 1 opportunity scan or Mode 2 sky_pattern_spec search). A Mode-2 call produced a 1.30MB/15,420-line response and a Mode-1 call (limit=10) produced 570KB/8,899 lines -- both exceeded a normal MCP client's tool-output token ceiling. The driver is an exhaustive per-candidate census (gap_report.factors_not_computed/factors_not_in_corpus) with multi-paragraph prose per candidate window, multiplied across every candidate. Unlike sibling kala_story_get (has budget_kb, default 40, demonstrably trims with a trim_report), kala_ritual_get's schema exposes no budget_kb/max_kb -- 'limit' only bounds candidate count, not per-candidate payload size.

**Reproduce.**

```
mcp__marsys-jis-direct__kala_ritual_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa', sky_pattern_spec:{all:[{factor_type:'vara',factor_id:6}], horizon:{months:3}}}) -- observe response byte size vs. schema (no budget_kb) vs. kala_story_get's schema (has budget_kb)
```

**Evidence.** `evidence/kala_ritual_get__native_mode2_sky_pattern_spec.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE on exact file/line for the census-generation code (likely Mode-2 gap_report/census builder inside kala_sky_pattern.ts or kala_lattice_query.ts's adjudication path). Confirmed at the contract level: kala_ritual_get's MCP schema has no budget_kb/max_kb property, unlike kala_story_get's schema which does and visibly exercises it. Violates CLAUDE.md SS N.6 Serving Density Principle's requirement that every served surface bound its own payload.

**Proposed remediation.** Add `budget_kb` to `kala_ritual_get`'s schema and bound the per-candidate census the way `kala_story_get` already bounds its chapters.

##### F-28  ·  `TIER2`

**Claim.** mimamsa_calibration_get's response content is unconditionally hard-truncated to roughly 120 characters with no override parameter, making the real underlying 57-row/4-verdict-class calibration data practically unrecoverable through this tool even though it demonstrably exists in the DB.

**Reproduce.**

```
mcp__marsys-jis-direct__mimamsa_calibration_get({chart_id: '482012f1-710e-4a25-994a-93821f5871aa'}) -- observe response content length vs. DB row count for the same chart
```

**Evidence.** `evidence/mimamsa_calibration_get__valid_domain_native.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE on exact file:line -- same recovery caveat as F-27 (concurrent-write race deleted the original finding's full detail). The truncation-to-~120-chars observation with no recovery path was independently reproduced and DB-cross-checked; only the precise source line was lost in the race.

**Proposed remediation.** Give `mimamsa_calibration_get` a real budget/pagination path so the 57 calibration rows are retrievable, rather than a ~120-character truncation with no override.

##### F-112  ·  `high`

**Claim.** verbosity:'concise' makes the response BIGGER. assess_career called with verbosity='concise' AND max_signals_per_lens=3 returned 163,241 bytes - 11% LARGER than assess_marriage's 147,294 at full default verbosity and default caps. The declared budget did halve (40 -> 20) exactly as documented, yet the delivered payload grew, because the unbudgeted domain_completeness block (13,825-concept coverage map across 26 serving tools) is appended outside the trim path. The knob's documented behaviour ('tightens this call's response-budget ceiling to roughly half its normal size') is true of the ceiling and false of the response.

**Reproduce.**

```
Q2. Call assess_career(chart_id=482012f1-710e-4a25-994a-93821f5871aa, verbosity='concise', max_signals_per_lens=3) and assess_marriage(chart_id=same) with no knobs. Compare byte counts of the two spill files: wc -c on E2_q2_raw_assess_career.json vs E2_q1_raw_assess_marriage.json.
```

**Evidence.** `pp2-audit/evidence/E2_q2_raw_assess_career.json | pp2-audit/evidence/E2_q1_raw_assess_marriage.json`

**Mechanism.** The Omega5 domain_completeness/dossier coverage-walk is attached to the envelope after response_budget.ts runs, so it is invisible to the trimmer and unaffected by verbosity/budget_kb. Because it is roughly constant in size, lowering the budget lowers only the trimmable remainder while the fixed block dominates - producing the inversion. Callers steering for size will make the problem worse, not better.

**Proposed remediation.** Move the `domain_completeness` attachment inside the trim path so `verbosity:'concise'` shrinks the payload it advertises rather than only the ceiling.

##### F-122  ·  `high`

**Claim.** kala_elect_get's budget trim deletes the actionable layer and keeps the bookkeeping. The call returned candidate_count=4 and frontier data for 4 candidates, but only ONE candidate object survived into .candidates - while the same response emitted ~60 full hora_* neutral_annotation rows (each with a multi-line source_citation), 15 hora_ladder entries, a 12-row dosha list, a 10-row residual_dosa list and 114 convention_only_keys, all in full. The response also reported judgment_flags 'budget_exceeded_after_trim: 20kb budget still exceeded after full trim'. The user-facing question ('which windows can I act in?') is answerable only from the candidate array that was trimmed to 25%; the surviving bulk is per-hour planetary-hour bookkeeping.

**Reproduce.**

```
Q2. Call kala_elect_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, undertaking='business', date_range={start:'2026-08-15',end:'2026-11-12'}, limit=4, native_janma_nakshatra='Purva Bhadrapada', budget_kb=20). Compare .candidate_count (4) with (.candidates|length) (1), then count .lattice_adjudication.ledgers[].neutral_annotations rows surviving.
```

**Evidence.** `pp2-audit/evidence/E2_q2_job_change_trace.json`

**Mechanism.** Inverted density priority relative to CLAUDE.md N.6 item 2: the candidate slate is the confirmed, highest-density, most-actionable section and should declare hardFloor with a minKeep, while hora/neutral_annotation/convention_only sections are the floorable-to-zero catalog layer. The trimmer's generic biggest-section-first heuristic appears not to be applied to lattice_adjudication at all, so the section that should be trimmed first is the one that survives intact.

**Proposed remediation.** Declare `hardFloor:true` + `minKeep` on `kala_elect_get`'s candidate slate and make the hora/convention bookkeeping the first thing trimmed, not the last.

#### CL-06 False or stale aggregate / pagination fields

> *Class root mechanism and remediation lane stated in full at §3.1; CL-06 spans multiple tiers.*


##### F-12  ·  `TIER2`

**Claim.** ganita_condition_get's content.total field (dignity/avasthas/karakas facets) is computed as the returned row count post-LIMIT, not a real COUNT(*) -- so any call with a limit smaller than the true matching-row count silently reports a false, truncated total with no more_available signal to compensate.

**Reproduce.**

```
mcp__marsys-jis-direct__ganita_condition_get({chart_id: '482012f1-710e-4a25-994a-93821f5871aa', facet: 'dignity', limit: 3}) -> content.total=3; then limit=25000 -> content.total=563 (true value)
```

**Evidence.** `evidence/ganita_condition_get__native_dignity_limit3_total_bug.json`

**Mechanism.** platform/src/lib/retrieval/registry/layers/L1_ganita/get_dignity.ts:85 (`total: result.rows?.length ?? 0`), identically in get_avasthas.ts:72 and get_karakas.ts:118 -- all three condition-facet handlers set total to the post-LIMIT SQL result length instead of a separate SELECT COUNT(*) (contrast with get_condition_composite.ts:90-92 in the same directory, which does this correctly). avasthas/karakas happened to report correctly only because their default limits (300/500) exceed true row counts (54/382), masking the same defect.

**Proposed remediation.** LANE-COUNTS — replace `total: rows.length` with a real `COUNT(*)` in `get_dignity.ts`, `get_avasthas.ts` and `get_karakas.ts`, following the correct pattern already in `get_condition_composite.ts` in the same directory.

##### F-36  ·  `TIER2`

**Claim.** ganita_chart_facts_get (marsys://tool/L1/chart_facts_query, backing register_d7_channel.ts) silently clamps any requested `offset` above 100,000 down to exactly 100,000, and echoes the CLAMPED value back in the response's `offset` field as though it were the caller's own input — with no disclosure field (no `offset_clamped`, `requested_offset`, or similar) anywhere in the schema or response. A caller paging deep into a large fact set (e.g. the 5,750-fact chart_facts catalog) using their own offset arithmetic will silently get page 100000 forever past a certain point, with no way to detect the substitution from the response alone.

**Reproduce.**

```
mcp__marsys-jis-direct__ganita_chart_facts_get(chart_id='482012f1-710e-4a25-994a-93821f5871aa', offset=999999)  -- and again with offset=500000, both return offset:100000 in the payload
```

**Evidence.** `evidence/ganita_chart_facts_get__pagination_past_end_offset999999.json`

**Mechanism.** platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:924 — `const offset = Math.max(0, Math.min(Number(args['offset'] ?? 0), 100_000))`; response fields built at lines 1130-1223 echo this post-clamp local variable, not the original request value.

**Proposed remediation.** Echo `requested_offset` alongside the clamped value and add an explicit `offset_clamped` disclosure field so a deep-paging caller can detect the substitution from the response alone.

##### F-37  ·  `TIER2`

**Claim.** ref_yogas_get (query_yoga_catalog capability) reports `total` as the number of rows returned on the CURRENT page (`rows.length`), not the true count of matching rows in the brahma_yoga_catalog table. Verified three ways: offset=0/default limit=100 → total:100 (=page size); offset=50/limit=10 → total:10 (=page size, and the 10 rows are genuinely DIFFERENT yogas than page 1, proving the real catalog exceeds 60 rows); offset=999999 → total:0 (should still report the true catalog/filtered size, per the tool's own description promising 'discloses pagination (total + more_available)'-style honesty seen correctly implemented elsewhere, e.g. ganita_chart_facts_get keeps total=5750 constant across offsets). A caller cannot determine the true catalog size from any single call to this tool.

**Reproduce.**

```
mcp__marsys-jis-direct__ref_yogas_get() then mcp__marsys-jis-direct__ref_yogas_get(offset=50, limit=10) then mcp__marsys-jis-direct__ref_yogas_get(offset=999999) — compare the three `total` values
```

**Evidence.** `evidence/ref_yogas_get__pagination_control_offset50_limit10.json`

**Mechanism.** platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_yoga_catalog.ts:61 — `total: rows.length` inside the handler's returned content object; no separate COUNT(*) query is issued.

**Proposed remediation.** Derive `ref_yogas_get`'s `total` from a `COUNT(*)` over the filtered catalog rather than the current page, matching the correct behaviour `ganita_chart_facts_get` already exhibits.

##### F-45  ·  `TIER2`

**Claim.** A systemic, repeatedly-live-reproduced defect: several tools compute a narrative/summary count field (verdict_summary.served_count, coverage_receipt text, content.signal_count, content.activation_count, content.prescription_count) BEFORE the generic post-hoc budget trimmer cuts the sibling array those fields describe, and never re-derive or flag the field as stale afterward. Confirmed live on FIVE independent tools: bodha_signals_get (served_count:200 vs signals.length:20), synth_chart_brief_get (coverage_receipt '27 domain verdicts' vs verdict_summary.length:13), kala_priority_ranking_get (signal_count:100 vs ranked_signals.length:50), kala_windows_get (activation_count:500 vs activations.length:5), and bodha_remedies_get (prescription_count:27 vs prescriptions.length:13, while the untouched resonance_count:9 correctly matches its own array -- confirming the mismatch tracks specifically with which array the generic trimmer cut).

**Reproduce.**

```
mcp__marsys-jis-direct__bodha_signals_get({chart_id: '482012f1-710e-4a25-994a-93821f5871aa', top_k: 200}) -> compare content.verdict_summary.served_count to content.signals.length; or mcp__marsys-jis-direct__bodha_remedies_get({chart_id: '482012f1-710e-4a25-994a-93821f5871aa', limit: 25000, fields: 'all'}) -> compare content.prescription_count to content.prescriptions.length
```

**Evidence.** `evidence/stale_pretrim_counts__three_tools.json`

**Mechanism.** platform-mcp/src/tools/register_p1_aliases.ts:579-604 for bodha_signals_get specifically (comment at line 582: 'Built BEFORE the trimmer runs so the verdict reflects the untrimmed served set' -- an acknowledged design choice, undisclosed to the API consumer). Root cause for the other four instances is the same shared pattern but their exact handler file:line was not individually traced -- DIAGNOSIS-INCOMPLETE on the precise source line for synth_chart_brief_get, kala_priority_ranking_get, and kala_windows_get specifically, though live behavioral evidence for all five is confirmed.

**Proposed remediation.** Re-derive every `*_count` / `served_count` after the trimmer runs, or emit pre-trim and served counts as two distinct fields with an explicit staleness marker.

#### CL-07 Nodal (Rahu/Ketu) special-aspect truncation to the universal 7th

> *Class root mechanism and remediation lane stated in full at §3.1; CL-07 spans multiple tiers.*


##### F-19  ·  `TIER2`

**Claim.** Rahu/Ketu's classical 5th/7th/9th special aspects are silently truncated to 7th-only in the Vipareeta Raja Yoga dilution/cancellation check (ganita_yoga_firings_get), contradicting both R24 and this same codebase's own correct nodal-aspect table used elsewhere (ga_structural_writer.py's NODE_PARASHARI_ASPECTS={5,7,9}, confirmed empirically live via ganita_structural_get facet=aspects on the same chart).

**Reproduce.**

```
Code read: platform/python-sidecar/ga_writers/ga_yoga_writer.py:1499-1504 (NB_GRAHA_DRISHTI table omits rahu/ketu, falls to NB_DEFAULT_DRISHTI={7}) consulted by _cancel_vipareeta_raja_yoga (2302-2340, specifically 2325). Cross-check: evidence/CROSSCHECK_ganita_structural_get__native_aspects_nodal.json shows RAH_MEAN/KET_MEAN casting correct 5/7/9 aspects elsewhere in the same codebase.
```

**Evidence.** `evidence/ganita_yoga_firings_get__native_all_true.json`

**Mechanism.** NB_GRAHA_DRISHTI dict (ga_yoga_writer.py:1499-1504) omits rahu/ketu keys; _nb_aspects_house (1588-1592) falls back to NB_DEFAULT_DRISHTI={7} for nodes. Latent for both ground-truth charts (vipareeta_raja_yoga did not fire in either chart's current firing set, so it hasn't manifested in served output yet), but a real, reproducible code defect that would silently suppress a legitimate VRY dilution finding whenever a node's only aspect onto the relevant dusthana-lord's house is via the 5th or 9th (not conjunction or the universal 7th). nbry_rule_3_lord_aspect is NOT affected -- its candidate aspectors are drawn only from NB_SIGN_LORDS, which never resolves to rahu/ketu.

**Proposed remediation.** Import the shared nodal 5/7/9 constant into `NB_GRAHA_DRISHTI` so the Vipareeta dilution loop can see a node's 5th/9th aspect; the rule-3 path is compliant by construction and needs no change.

#### CL-08 Tier-honesty leaks (non-calibrated data served at full numeric precision / inflated labels)

> *Class root mechanism and remediation lane stated in full at §3.1; CL-08 spans multiple tiers.*


##### F-69  ·  `TIER2`

**Claim.** mimamsa_insight_get exhibits the same tier-suppression violation as A3-F-61 in a second, independent surface: the tool's top-level envelope declares `calibration_status: 'prior_only'` and `mode: 'STRUCTURAL'` for the entire L5 layer ('L5 Mimamsa is SEALED in STRUCTURAL mode. Empirical calibration accrues as outcome data is recorded'), and every served insight_type='verdict_object' row (the bo_pratijna-derived per-domain verdicts) carries a HARDCODED `evidence_grade: 'structural'` literal (never 'empirical' for this row type, by construction -- confirmed in source, not merely observed live), and every insight_type='retrodiction' row carries `evidence_grade: 'prior_only'` (mi_darshana.py's own honest non-calibrated marker: 'empirical' only when n_support>=5, which the sampled rows do not reach). Despite this permanent non-calibrated tagging, both row types are served with full numeric `rank_consequence` scores (e.g. 0.95, 0.88, 0.786, 0.774), numeric `confidence_band` intervals (e.g. '[0.68,0.98)'), and numeric `provenance_chain.grade` values on a 0-10 scale (8.8, 7.86, 7.74) -- no suppression applied anywhere in the served payload.

**Reproduce.**

```
mcp__marsys-jis-direct__mimamsa_insight_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa', top_k:10}) -- inspect top-level calibration_status/mode plus any insight_unit's evidence_grade + rank_consequence + confidence_band + provenance_chain.grade.
```

**Evidence.** `evidence/mimamsa_insight_get__native_leak.json`

**Mechanism.** platform/python-sidecar/pipeline/orchestrator/writers/mi_darshana.py:215 (`'empirical' if n >= 5 else 'prior_only'` for retrodiction rows) and lines 247, 366, 509 (evidence_grade hardcoded to the literal `'structural'` for every verdict_object row, never conditional) -- both row-writer paths populate `rank_consequence`/`confidence_band`/`provenance_chain.grade` unconditionally regardless of the assigned evidence_grade, and the serving path (mimamsa_insight_get, backed by L5_mimamsa/query_insights.ts) forwards them with no suppression gate.

**Proposed remediation.** Apply the shared tier-suppression gate to L5 insight rows so `evidence_grade:'structural'/'prior_only'` cannot ship 0–10 provenance grades and confidence bands unqualified.

#### CL-09 Earned-signal violations (flag/grade with no detector, or a detector on a proxy)

> **Root mechanism (class-level).** CLAUDE.md §N.8's own class, found in four more places. leakage_status is a bare Python string literal 'clean' at all 6 mi_darshana INSERT sites — on BLIND RETRODICTION rows, the exact row type where an unearned cleanliness claim does most damage — while the sibling writer mi_adhilepa already established 'not_assessed' as this codebase's honest tier for the identical concept (F-104). transit_quality, 20% of the muhurta composite, contains no transit computation at all — a lunar-phase approximation plus a static day-of-week table, by the code's own docstring (F-48). 50% of that same composite (dasha_quality + transit_quality) takes no action_type parameter, so the 'domain-specific' election score is half domain-blind (F-47). efficacy_tier is assigned by source_surface, restating provenance rather than assessing anything, and reads 'classically_attested' on 100/100 rows (F-118).

> **Class remediation lane.** LANE-EARNEDSIGNAL: for each status/grade/PASS field, require a named detector and a test that makes it read false; where none exists, emit the honest null/not_assessed tier.


##### F-47  ·  `TIER2`

**Claim.** kala_elect_get and kala_muhurta_get share one underlying scoring engine (PH-4-4/muhurta.py) in which 50% of the composite auspiciousness score (dasha_quality 30% + transit_quality 20%) is computed with NO action_type/undertaking parameter at all, making it domain-blind -- only panchanga_quality (40%) and signal_activation (10%) are genuinely domain-sensitive. Not F-10's total domain-blindness, but a real partial one: the same top-ranked window came out #1 for business, marriage, AND medical in this test, differing only in numeric score.

**Reproduce.**

```
kala_muhurta_get(chart_id='482012f1-710e-4a25-994a-93821f5871aa', activity_type='business'|'marriage'|'medical', start_date='2026-08-15', end_date='2026-09-14') -- compare factors.dasha_quality and factors.transit_quality per matching window; dasha_quality=0.72 in every window of every domain
```

**Evidence.** `evidence/kala_muhurta_get__business.json`

**Mechanism.** platform/python-sidecar/brahmagyan/phala/muhurta.py:372 (_dasha_quality_for_chart -- no action_type param) and :420 (_transit_quality_for_window -- no action_type param), confirmed called at muhurta.py:814-815/858 without action_type. Contrast with :231 _panchanga_quality_for_action and :468 _signal_activation_for_action, which DO take action_type and produce domain-differentiated scores.

**Proposed remediation.** LANE-EARNEDSIGNAL — pass `action_type` into `_dasha_quality_for_chart` and `_transit_quality_for_window`, or reweight the composite so only genuinely domain-sensitive components carry the 'domain-specific' election score.

##### F-48  ·  `TIER2`

**Claim.** The transit_quality field served by kala_elect_get/kala_muhurta_get (20% of composite score) contains no actual planetary transit computation -- it is a lunar-phase approximation plus a static day-of-week lookup table. A SS N.8 earned-signal violation: a signal named 'transit quality' with no transit detector behind it, by the code's own docstring admission.

**Reproduce.**

```
Read platform/python-sidecar/brahmagyan/phala/muhurta.py:420-465 (_transit_quality_for_window); docstring admits 'Full transit computation requires Swiss Ephemeris... simplified seasonal approximation... All values are approximations only'
```

**Evidence.** `evidence/kala_muhurta_get__business.json`

**Mechanism.** platform/python-sidecar/brahmagyan/phala/muhurta.py:420-465

**Proposed remediation.** Rename `transit_quality` to what it actually computes (a lunar-phase and weekday heuristic) or implement a real transit detector — a signal named for a detector it does not have must be renamed or nulled.

##### F-104  ·  `high`

**Claim.** VIOLATION — mimamsa_insight_get's leakage_status is a hardcoded literal 'clean' with zero detector behind it (flag `leakage_status` served by `mimamsa_insight_get`, subsystem: L5 Mimamsa (mi_darshana insight-unit writer)) Verdict: VIOLATION. grep of mi_darshana.py confirms the bare Python string literal "clean" is written at every one of 6 INSERT call sites for the leakage_status column — no variable, no conditional, no detector of any kind computes this value; it cannot ever read anything else. Live-confirmed: every one of 15 inspected insight_unit rows served for chart 482012f1 (spanning insight_type=retrodiction, verdict_object, and load_bearing) reads leakage_status='clean' identically. This is the same defect class as the four confirmed §N.8 instances (a flag with no code path that could ever produce a different value). It is materially more serious than a routine finding because leakage_status specifically claims train/test-leakage cleanliness on BLIND RETRODICTION rows (T-90d cutoff insight_units) — the entire epistemic value of a retrodiction test rests on the cutoff genuinely excluding future information, and this is precisely the row type where an unearned 'clean' claim does the most damage to the calibration story. The correct pattern already exists in the codebase one file over: mi_adhilepa.py:156-163 uses the honest 'not_assessed' tier for the identical leakage_status concept, with a code comment stating in so many words that 'clean' is reserved for when a real detector exists and passes (migration 549_adhilepa_leakage_not_assessed.sql codifies the same honest-tier convention). mi_darshana.py does not follow its sibling writer's own documented convention.

**Reproduce.**

```
Call mcp__marsys-jis-direct__mimamsa_insight_get on chart_id=482012f1-710e-4a25-994a-93821f5871aa and inspect field `leakage_status`
```

**Evidence.** `pp2-audit/evidence/n7n8_honesty_sweep_10flags.json (flag #8)`

**Mechanism.** platform/python-sidecar/pipeline/orchestrator/writers/mi_darshana.py:136,183,214,246,365,508; platform/python-sidecar/pipeline/orchestrator/writers/mi_adhilepa.py:156-163 (contrast — correct pattern); platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insights.ts:105 (serves the field verbatim) | recommendation: Either (a) implement a real leakage detector for mi_darshana insight units analogous to mi_adhilepa's gated design, or (b) until one exists, emit the honest 'not_assessed' tier mi_adhilepa already established as this codebase's convention for exactly this situation — never a bare 'clean' literal with no check behind it.

**Proposed remediation.** Adopt `mi_adhilepa`'s honest `'not_assessed'` tier at all six `mi_darshana` `leakage_status` INSERT sites until a real leakage detector exists, with a test that makes the field read something other than `'clean'`.

##### F-118  ·  `high`

**Claim.** kala_upaya_get's intervention slate is 50% one duplicated non-remedy, and its efficacy grading carries zero information. intervention_count=100, but only 14 distinct labels; 50 of the 100 rows are the byte-identical string 'light - for saturn - severity=medium x anchor_magnitude=minor -> light', each under a different phala_mitigation UUID. The entire 'remedy' content of half the slate is the word 'light' - a severity classification leaked into the label field, containing no action a native could take. Additionally, all 100 rows carry efficacy_tier='classically_attested' and targets_link='promise', and feasibility is null on 50 - so within this response no row could ever have graded differently on any of the three discriminating fields. Every intervention targets 'promise', the very link the same response's diagnosis just declared denied.

**Reproduce.**

```
Q4. Call kala_upaya_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, domain='relationship', as_of_date='2026-08-15'); count distinct .interventions[].label (14 of 100) and Counter over .interventions[].efficacy_tier (all classically_attested) and .targets_link (all 'promise').
```

**Evidence.** `pp2-audit/evidence/E2_q4_raw_kala_upaya.json | pp2-audit/evidence/E2_q4_remedy_now_trace.json`

**Mechanism.** The phala_mitigation join emits one intervention row per source mitigation row without deduplicating on label, so a mitigation severity-bucket repeated 50 times across anchors produces 50 identical 'remedies'. The label is built from severity x anchor_magnitude -> tier rather than from any remedy text. efficacy_tier appears to be assigned by source_surface (everything from phala_mitigation/bodha_rm is 'classically_attested'), so the tier is a restatement of provenance, not an assessment - a flag with no detector behind it (CLAUDE.md N.7 item 4 / N.8).

**Proposed remediation.** Deduplicate the intervention slate, move the severity token out of the label field, and null `efficacy_tier` / `feasibility` until a detector can grade them — a field constant across 100/100 rows carries no information.

#### CL-10 Jargon / raw-internal leakage into user-facing prose

> **Root mechanism (class-level).** The v3 register/reading_contract self-glossing mechanism exists and demonstrably works (graha_portrait, judgment_query — F-137 is the positive contrast), but was never applied to the primary narrative slot of the other serving code paths. Those interpolate raw internals directly into sentence templates: signal_type_id colon-namespaces ('Signal tajik_hadda_lord:sign appears unremarkable', F-128/F-129), enum concatenations ('strongest: CLASSIFY_RESIDUAL/DIGNITY/YOGA/SUBSYSTEM', F-132), raw truncated JSON mid-sentence (F-130, 2/2 tools, 2 families each), MSR-style templates ('SAT: graha nakshatra join: nakshatra id ref = 16 [ga_sensitive]', F-114/F-131), and in F-131 an internal computation-ABSTENTION marker ('floored: no_canonical_per_varga_method') salience-scored and served as the #3 priority signal deserving the native's attention. Re-verified live this pass on assess_marriage: 10/10 top-ranked marriage-lens signals are that exact ga_sensitive template string, all at identical salience 2.16108, and the marriage and progeny lenses share 6 of their 10 top signal_ids — the ranker does not discriminate at the top of the distribution or between domains.

> **Class remediation lane.** LANE-REGISTER: make the v3 register/reading_contract glossing pass mandatory for any string that reaches a narrative field, plus a CI lint forbidding raw signal_type_id/enum/JSON interpolation into *_text/*_thesis/*_statement slots.


##### F-114  ·  `high`

**Claim.** Domain-lens signal ranking is degenerate and non-domain-discriminating. assess_marriage's 'marriage' lens reports signal_count 3698 and returns as its top 10 ranked signals ten ga_sensitive SATURN rows with IDENTICAL salience 2.16108: 'SAT: graha nakshatra join: nakshatra id ref = 16', 'SAT: bhrigu nadi point: sign = Capricorn', 'SAT: esoteric point shiva: sign = Aquarius', 'SAT: upagraha position', 'SAT: midpoint', 'SAT: graha pada join', 'SAT: saham position', 'SAT: aprakasha position'. Not one names the 7th lord, Venus, or a marriage yoga. assess_health's health lens returns the same class of row as its #1 of 767 ('SAT: sun derived upagraha: sign = Capricorn'). The tie at 2.16108 across ten rows means the composite ranker is not discriminating at all at the top of the distribution, and the surfaced rows are unusable for the question asked.

**Reproduce.**

```
Q1/Q3. jq '.object.content.house_analysis.question_lenses[0].all_relevant_ranked_jsonb.ranked_signals[]|{salience,headline}' on E2_q1_raw_assess_marriage.json; same path on E2_q3_raw_assess_health.json.
```

**Evidence.** `pp2-audit/evidence/E2_q1_raw_assess_marriage.json | pp2-audit/evidence/E2_q3_raw_assess_health.json | pp2-audit/evidence/E2_q1_marriage_timing_trace.json`

**Mechanism.** The composite_4d score is class_prior x topic_relevance x intrinsic_strength x structural_role x temporal_activation x percentile. ga_sensitive rows carry signature_tier 'chart_defining' and topic_relevance 1, so the whole ga_sensitive block scores identically and saturates the top of every lens regardless of domain. The lens itself is chart-wide (its own note: 'bodha_question_lenses returned chart-wide (no domain column); reconcile via cdlm_cells'), so domain filtering never happens at ranking time. verification_pass_status on the lens is 'documented_approximation'.

**Proposed remediation.** LANE-REGISTER — run lens headlines through the v3 register/reading_contract glossing pass, and give the composite ranker a domain filter plus a real tiebreaker so the top-10 is not a single-salience plateau shared across domains.

##### F-129  ·  `high`

**Claim.** synth_chart_brief_get (the Maha-Brief, the flagship whole-chart-synthesis tool) at depth=complete serves its top_discoveries array — the cross-domain-discoveries section of a whole-chart brief — as raw signal descriptors rather than narrative: 'Signal combustion_per_varga:is_combust with low visibility (salience 0.215)', 'Signal dispositor_chain_per_varga:chain with low visibility (salience 0.227)', and 'Appears as one of many composite_state signals' (verbatim, repeated across multiple rows with different discovery_ids and no chart-specific content differentiating them beyond the salience number).

**Reproduce.**

```
Call mcp__marsys-jis-direct__synth_chart_brief_get with chart_id=482012f1-710e-4a25-994a-93821f5871aa, depth=complete; inspect content.top_discoveries[].statement
```

**Evidence.** `pp2-audit/evidence/E3_read1_general_trace.json (step 2)`

**Mechanism.** synth_chart_brief_get content.top_discoveries[].statement field — the user-facing narrative slot for the maha-brief's discovery section — renders raw signal_type_id / signal_type_class tokens instead of a synthesized claim.

**Proposed remediation.** Render `top_discoveries` through the register glossing pass instead of interpolating `signal_type_id` strings into the Mahā-Brief's discovery slot.

##### F-130  ·  `high`

**Claim.** assess_career and assess_wealth's 'reading' array — explicitly billed by completeness_directive as 'SUBSTANCE-INLINE: this response's reading field carries N/12 concept families as grounded sentences (fact_id-cited) — read it directly, it IS the opening reading, not a pointer to one' — contains, in the 'timing_windows' family of BOTH tools, a raw truncated JSON blob mid-sentence instead of rendered prose. Verbatim (assess_career): "10 activation window(s) in range; nearest: {\"id\":\"8106742\",\"signal_id\":\"1846a106-4424-41bf-8fe9-3e7a2c7df8c0\",\"ayanamsha_id\":\"lahiri_chitrapaksha\",\"signature_class\":\"SUBSYSTEM\",\"activation_start\":\"2027-08-18\",\"activation_end\":\"2028-01-15\",\"activation_peak_date\":\"." — the sentence is cut off mid-JSON-key with a dangling period. The identical defect class recurs in assess_wealth's timing_windows AND in both tools' 'contradictions_with_adjudication' family (assess_career: '...signal_b_id\":\"36a6e81b-9e8c-478b-a24e-3535f7ee0'). This is not a one-off truncation artifact — it is the same code path serving raw JSON into a sentence template across two different tools and two different families within each tool.

**Reproduce.**

```
Call mcp__marsys-jis-direct__assess_career and mcp__marsys-jis-direct__assess_wealth with chart_id=482012f1-710e-4a25-994a-93821f5871aa; inspect object.reading[] entries with family='timing_windows' and family='contradictions_with_adjudication'
```

**Evidence.** `pp2-audit/evidence/E3_read2_career_wealth_trace.json (steps 1-2)`

**Mechanism.** assess_career / assess_wealth reading[].sentences template for the timing_windows and contradictions_with_adjudication families interpolates a raw (and truncated) JSON object into the sentence string instead of rendering its fields into prose. Reproduced identically in 2/2 tools tested.

**Proposed remediation.** Fix the `reading[]` sentence builder to render structured window/contradiction objects as prose; no raw JSON may reach a `*_text`/`*_statement` slot, enforced by lint.

##### F-131  ·  `high`

**Claim.** kala_priority_ranking_get — described as ranking 'which signals deserve attention in a time window' — returns, for the current 6-month window (2026-08-15 to 2027-02-15), 15 top-ranked 'priority' signals that are 100% raw signal_type_id template strings with zero interpretive content, e.g. 'SAT: arudha pada: sign = Aquarius [ga_sensitive]', 'SAT: graha nakshatra join: yoni en = Tiger [ga_sensitive]'. Worse, the #3-ranked signal by priority_score is 'graha cheshta bala per varga: D14 = floored: no_canonical_per_varga_method [ga_structural]' — this is not an astrological finding at all but an internal computation-abstention marker (the writer had no verifiable classical per-varga formula for D14 cheshta bala and floored the value per B.10 rather than fabricate one). That floor-reason string has been salience-scored and served as if it were a priority signal deserving the native's attention right now.

**Reproduce.**

```
Call mcp__marsys-jis-direct__kala_priority_ranking_get with chart_id=482012f1-710e-4a25-994a-93821f5871aa, date_from=2026-08-15, date_to=2027-02-15, top_k=15; inspect ranked_signals[].signal_headline_text, particularly ranked_signals[2]
```

**Evidence.** `pp2-audit/evidence/E3_read3_timing_trace.json (step 3)`

**Mechanism.** kala_priority_ranking_get's ranked_signals[].signal_headline_text is a raw MSR-style template ('GRAHA: category: key = value [subsystem]') applied uniformly to every signal regardless of whether its value is a genuine astrological fact or an internal floor/abstention marker; no filtering excludes non-astrological internal-state strings from the priority ranking.

**Proposed remediation.** Gloss ranked headlines and exclude computation-abstention markers (`floored: no_canonical_per_varga_method`) from salience ranking entirely — an abstention is not a finding.

#### CL-11 Non-actionable or dead recovery pointers (recover_via / drill_pointers / tri_plane)

> **Root mechanism (class-level).** Recovery and navigation pointers are emitted by shared helpers that know nothing about the target: dualOutput's default toolName='unknown_tool' fires on ~22 registrations in one file (F-17/F-18/F-43), the budget helper emits a boilerplate hint naming date_range/top_k/limit params the target tool does not have (F-09), the 1-entry-still-too-big fallback names a non-existent 'response_format:legacy' instrument (F-44), and tri_plane pointers carry an instrument name with none of the arguments the target actually requires, so following the server's own navigation graph dead-ends (F-123: kala_now_get points at kala_explain_get, which then demands a domain a NOW question has no value for). A sibling fix (RC-04) exists and was applied to exactly one call site.

> **Class remediation lane.** LANE-POINTERS: make toolName a required argument of dualOutput, derive recover_via hints from the target's real JSONSchema, and emit required-args alongside every drill/tri_plane pointer.


##### F-43  ·  `TIER2`

**Claim.** The 'unknown_tool' placeholder recover_via defect (already confirmed on bodha_graph_subgraph_get/bodha_graph_traverse_get, F-17/F-18) is not isolated -- live-reproduced on catalog_assets_list, and source inspection finds ~19 more register_p1_aliases.ts tool registrations sharing the identical bare dualOutput(data) call site (no toolName argument), so the same defect fires on ANY of them the moment auto-detected trimming triggers: catalog_assets_all, catalog_assets_l0, ref_vector_search, ref_remedies_get, ref_remedies_chart_get, ref_remedies_by_category_list, ref_remedy_get, ref_tantric_remedies_get, ref_remedies_by_planet_get, ref_mantras_get, kala_muhurta_get, mimamsa_calibration_get, ganita_natal_positions_compute, ganita_special_lagnas_get, kala_yoga_activation_get, plus bodha_signals_get's own outer wrapper. One sibling (phala_outlook_get) was already patched (RC-04, 2026-07-23) by passing the real tool name explicitly, proving the fix pattern is known but was not applied file-wide. NOTE: only catalog_assets_list (plus the original 2) were live-reproduced this pass; the other ~16 names are source-grep-identified, not independently re-tested -- their existing PASS verdicts from earlier waves are NOT retroactively downgraded without live confirmation.

**Reproduce.**

```
mcp__marsys-jis-direct__catalog_assets_list({limit: 500}) -- observe trim_report[0].recover_via.instrument === 'unknown_tool' and drill_pointers[0].instrument === 'unknown_tool'
```

**Evidence.** `evidence/catalog_assets_list__unknown_tool_live.json`

**Mechanism.** platform-mcp/src/tools/register_p1_aliases.ts:188 (function dualOutput(data, toolName='unknown_tool')) combined with the bare dualOutput(data) call for catalog_assets_list at line 1155; ~19 additional bare-call line numbers found via grep at lines 606, 657, 1207, 1249, 1368, 1499, 1522, 1558, 1570, 1582, 1594, 1606, 1618, 1630, 1670, 1781(fixed/RC-04), 1844, 1860, 1874, 1971 in the same file.

**Proposed remediation.** LANE-POINTERS — make `toolName` a required argument of `dualOutput` and patch all ~22 call sites in one sweep, with a lint forbidding the bare form.

##### F-44  ·  `TIER2`  ·  *also manifests as CL-05*

**Claim.** kala_story_get's honesty mechanism (trim_report) can itself be trimmed away under extreme budget pressure (budget_kb=2), replacing the real per-section trim entries with a generic collapsed summary that (a) does not disclose WHICH section was cut to zero -- chapters silently drops from 91 real chapter objects to an empty array while chapter_count still reads 91 -- and (b) names a non-real, non-actionable recover_via instrument, 'response_format:legacy', which does not correspond to any parameter on kala_story_get's schema. Same defect class as F-17/F-18/F-43 (unknown_tool) -- a recover_via pointer naming nothing a caller can actually call -- reached via a different code path (the trim_report degrades itself). At budget_kb=8 and the 40KB default, trim_report stays intact and fully honest.

**Reproduce.**

```
mcp__marsys-jis-direct__kala_story_get({chart_id: '482012f1-710e-4a25-994a-93821f5871aa', budget_kb: 2}) vs budget_kb: 8 vs omitted -- compare chapters.length, chapter_count, and trim_report[0].recover_via.instrument across the three calls
```

**Evidence.** `evidence/kala_story_get__trim_report_self_collapse.json`

**Mechanism.** platform-mcp/src/lib/response_budget.ts:402-410 (finalizeMcpBudget's 1-entry-still-too-big fallback, recover_via:{instrument:'response_format:legacy'}) and an identical fallback at :292 inside applyResponseBudget's own '(whole response)' branch.

**Proposed remediation.** Keep `trim_report`'s per-section entries above the self-collapse threshold, disclose which section was zeroed, and remove the non-existent `response_format:legacy` recovery pointer.

#### CL-12 Narration-fidelity defects (prose diverges from the rows it sits on)

> **Root mechanism (class-level).** CLAUDE.md §N.7's class. The sentence is not a faithful restatement of the cited rows: fabricated dasha boundary dates ~6 weeks off the two_pass_verified chart_dashas row (F-93); catalog trigger-condition preambles presented as chart-matched diagnoses of afflictions this native does not have — 'debilitated Jupiter in Capricorn' for a chart whose Jupiter is in its OWN sign, 'debilitated Sun in Libra' against a FORENSIC birth anchor of Sun in Capricorn (F-116); a narration hard-coded to three dasha levels that labels the level-3 period 'current' and never mentions the level-4 period running today with sandhi_flag=TRUE (F-120); four explicit per-band false booleans rendering absence-of-coverage in the same grammar as absence-of-condition (F-121); '#1 remedy-priority target' asserted for the chart's second-strongest graha (F-50); an ENTITLEMENT_DENIED template asserting 'this chart exists' for a fabricated UUID (F-39); an empty weaknesses bucket beside five conditional sub-5/10 grades (F-135); and a detector that fires true but serves combination_name='unknown' (F-63).

> **Class remediation lane.** LANE-NARRATION: every narration layer gets its own golden-value test asserting the sentence's numbers/labels equal the cited fact row (§N.7 item 5); remove conditional catalog preambles unless a predicate confirms the condition on this chart.


##### F-93  ·  `TIER2-QUALITY`

**Claim.** prashna_ask's synthesized narrative answer for a direct, unambiguous factual question ('What is the current Vimshottari mahadasha lord for this chart?', chart_id=482012f1) states incorrect Mahadasha/Antardasha boundary dates. The narrative reads: 'This 17-year Mercury Mahadasha is active from July 7, 2010, to July 7, 2027. Within this major period, the current Antardasha (sub-period) of Saturn is running from October 27, 2024, to July 7, 2027.' The correct MD lord (Mercury) is right, but the actual boundary dates on record in the authoritative chart_dashas table (surfaced this same session via ganita_dashas_get, verification_pass_status=two_pass_verified) are start_date 2010-08-18 / end_date 2027-08-18 -- roughly 6 weeks off from what the narrative states on both ends. kala_now_get's dasha_sandhi block (also this session) independently confirms the 2010-08-18/2027-08-18 boundary. The AD end-date the narrative gives ('July 7, 2027') also does not match any AD boundary served elsewhere. This is a narration-fidelity defect (§N.7): the prashna_ask synthesis layer appears to be generating/paraphrasing a plausible-sounding date rather than restating the cited L1 dasha row's own start_date/end_date verbatim.

**Reproduce.**

```
mcp__marsys-jis-direct__prashna_ask({chart_id:'482012f1-710e-4a25-994a-93821f5871aa', question:'What is the current Vimshottari mahadasha lord for this chart?', response_format:'concise'}) -> poll mcp__marsys-jis-direct__prashna_status({job_id}) to completion; compare result.reading's stated MD/AD boundary dates against mcp__marsys-jis-direct__ganita_dashas_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa', level:1, ayanamsha_id:'lahiri_chitrapaksha'}) for the same chart.
```

**Evidence.** `evidence/prashna_ask__career_MD_lord_job_result.json (pointer to full saved job result + the ganita_dashas_get cross-check excerpt)`

**Mechanism.** DIAGNOSIS-INCOMPLETE -- confirmed live exactly once this session via direct cross-check against the authoritative chart_dashas-backed ganita_dashas_get response captured in the same session. Did not trace prashna_ask's synthesis/narration code path (likely an LLM-composed answer over retrieved tool results in platform-mcp or platform/src) to pin the exact file:line where the cited dasha row's start_date/end_date is paraphrased rather than restated verbatim. Filed as a secondary/tertiary observation discovered incidentally while executing Task 2 (session/concurrency) rather than a primary determinism finding -- it was not re-tested for repeat-call stability of the WRONG date (i.e. whether the narrative is at least internally deterministic in its own wrongness), so it is reported strictly as a one-time-observed narration-accuracy defect, not a non-determinism instance.

**Proposed remediation.** LANE-NARRATION — make `prashna_ask` restate the cited `chart_dashas` `start_date`/`end_date` verbatim rather than paraphrasing, with a golden-value test on the MD/AD boundary sentence.

##### F-116  ·  `high`

**Claim.** Remedy prescriptions carry conditional preambles that are FALSE for this chart, presented as chart-matched. (a) Jupiter japa: 'For afflicted Jupiter (debilitated in Capricorn, Guru Chandal dosha, retrograde in dasha)' - this chart's Jupiter is in SAGITTARIUS, its OWN sign (ganita_medical_get natal_sign='Sagittarius'; assess_career D10 reports Jupiter 'own'). (b) Sun japa: 'For afflicted Sun (combust, debilitated in Libra, or in 6/8/12)' - this chart's Sun is in CAPRICORN, which is one of the seven FORENSIC birth anchors. (c) Venus Shri Sukta: 'For Venus-related wealth affliction (Venus in 6H/12H, debilitated in Virgo, or Shukra dasha poverty)' - this chart's D1 Venus is in Sagittarius. Generic catalog blurbs are served in remedy_label_human as though the stated affliction had been detected on this chart.

**Reproduce.**

```
Q4. Call bodha_remedies_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, limit=8, fields='compact'), read .content.prescriptions[].remedy_label_human, and cross-check each stated condition against ganita_medical_get(chart_id=same).content.rows[].natal_sign.
```

**Evidence.** `pp2-audit/evidence/E2_q4_remedy_now_trace.json | pp2-audit/evidence/E2_q3_health_outlook_trace.json`

**Mechanism.** brahma_remedy_corpus rows are keyed to target_graha only; the human label embeds the catalog's generic trigger-condition list verbatim. The join to the resonance is by graha, and no predicate ever tests whether the named condition holds on this chart. Nothing in the response distinguishes 'this remedy is for your Jupiter because your Jupiter is weak' from 'this remedy's catalog entry describes a Jupiter unlike yours' - so the prose reads as a chart-specific diagnosis of an affliction the native does not have.

**Proposed remediation.** Gate every conditional catalog preamble on a predicate that confirms the affliction on *this* chart, or strip the preamble from `remedy_label_human` — a template contradicting a FORENSIC birth anchor must never reach a served sentence.

#### CL-13 Missing disclosure of a known partial or mixed result

> **Root mechanism (class-level).** The surface knows (or can cheaply know) that it clipped, skipped or mixed scopes, but the disclosure branch is gated on the wrong condition — usually total emptiness. gochara_forecast_get emits an empty_reason only when rows.length===0, so a range half beyond the swept horizon returns 22 silently-capped windows with empty_reason:null (F-34). assess_health omits the entire documented reading layer without a judgment_flag, in a response whose judgment_flags mechanism is live and used for a lesser gap in the same payload (F-31). A pre-birth as_of_date is served as two_pass_verified dasha rows whose only tell is a free-text 'age ~-4' (F-33). Cross-chart population-mined insights carry evidence_grade='empirical' with no population-level marker beside this chart's own structural rows (F-35). event_classes conflates attempted-with-built (F-78). An already-peaked 2025 window sits inside an 'upcoming' forward sweep unflagged (F-134).

> **Class remediation lane.** LANE-DISCLOSE: move every empty_reason/coverage guard from an 'is empty' predicate to a 'did we serve less/other than asked' predicate.


##### F-34  ·  `TIER2`

**Claim.** gochara_forecast_get silently truncates results at the chart's build horizon (birth+100y) when a query's date_range partially overlaps the horizon, without any field disclosing that part of the requested range is unswept -- even though the same tool DOES supply an explicit empty_reason/coverage caveat when the ENTIRE query falls beyond the horizon. Disclosure only fires on total emptiness, not partial truncation.

**Reproduce.**

```
MCP gochara_forecast_get {chart_id:'482012f1-710e-4a25-994a-93821f5871aa', date_range:{start:'2083-06-01', end:'2085-06-01'}} -- empty_reason is null despite ~16 months of the query being past the swept horizon; compare against a fully-beyond-horizon query which DOES disclose
```

**Evidence.** `evidence/gochara_forecast_get__horizon_2084_partial_overlap.json`

**Mechanism.** platform-mcp/src/tools/retrieval/register_gochara_windows.ts:1429 -- empty_reason is gated purely on rows.length===0; no branch checks whether the requested date_range extends past the chart's actually-swept horizon when rows.length>0. Confirmed live: 2083-06-01..2085-06-01 query returns 22 windows all capped at window_end<=2084-01-31 (era_slice_key g3_2074_2084) with empty_reason=null.

**Proposed remediation.** LANE-DISCLOSE — change the `empty_reason` guard from `rows.length===0` to a 'did we serve less than asked' predicate and disclose the horizon cap on partial overlap.

#### CL-16 Unstable row selection — no total ORDER BY / non-deterministic serving

> **Root mechanism (class-level).** Identical inputs do not produce identical served evidence. judgment_query returned 4 then 6 distinct kala_activation windows on two byte-identical calls ~2.3s apart, with the flag text changing to match (F-92) — the dedup step has no total tiebreaker. ganita_strength_get's offset is not a stable pointer: declared total and counterfactual_rows_dropped changed on every retry at a different offset for the identical chart, and it took 5 escalating attempts to reach the graha_shadbala_total rows the ŚUDDHA-VĀCA campaign exists to protect (F-60). assess_career and bodha_remedies_get name different #1 remedy targets from the same bodha_rm_resonances asset because neither pins the rank-1 ordering key (F-115). Exactly the defect class §N.7 item 2 names for fact selection, one layer up at the row-set level.

> **Class remediation lane.** LANE-DETERMINISM: total ORDER BY (with a UUID/pk tiebreaker) on every reducing/paginating query, plus a repeat-call result_hash equality test in CI for the top ~20 tools.


##### F-60  ·  `TIER2`  ·  *also manifests as CL-05*

**Claim.** ganita_strength_get's default response (offset=0, or any offset up to 250 tried) never surfaces the graha_shadbala_total category -- the exact HIGH-PRIORITY data this audit was asked to verify following the ŚUDDHA-VĀCA wrong-column-selector campaign -- despite that category being listed in the response's own top-level 'categories' array on every single call. The 'limit' parameter (tested at 25000, the tool's documented maximum) has no effect on how many rows are actually served; every call is silently capped at 48-60 rows by an internal byte-budget trim. Offset does not behave as a stable pointer into a fixed row ordering: the declared 'total' and 'counterfactual_rows_dropped' counts both changed on every retry at a different offset for the identical chart/ayanamsha (223/297 at offset=0, 208/232 at offset=80, 205/190 at offset=125, 193/77 at offset=250, 120/0 at offset=400), and it took 5 escalating trial-and-error attempts (0, 80, 125, 250, 400) to finally reach graha_shadbala_total rows. NOTE: once reached, the shadbala_total VALUES themselves are verified CORRECT (see A1-F-60 evidence / prose summary) -- this finding is about reachability/discoverability, not value correctness.

**Reproduce.**

```
mcp__marsys-jis-direct__ganita_strength_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa', limit:25000}) then retry with offset:80, offset:125, offset:250, offset:400 -- observe categories array always lists graha_shadbala_total but rows never contain it until offset=400; observe total/counterfactual_rows_dropped changing across retries.
```

**Evidence.** `evidence/ganita_strength_get__native_shadbala_total_verification.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE -- the response-budget trim and offset/counterfactual-filter interaction were characterized behaviorally (see offset_escalation_log in the evidence file) but the specific serving-layer source file/line responsible (likely a response_budget.ts-style byte-cap trimmer per CLAUDE.md §N.6, combined with an offset applied pre-filter against a raw counterfactual-inclusive row set rather than the final served ordering) was not located/read in this pass -- no code-level citation is asserted.

**Proposed remediation.** LANE-DETERMINISM — give `ganita_strength_get` a total `ORDER BY` with a pk tiebreaker, make `limit` real, and expose `graha_shadbala_total` by category rather than by offset luck.

##### F-92  ·  `TIER2`

**Claim.** judgment_query(chart_id=482012f1-710e-4a25-994a-93821f5871aa, domain='career') is non-deterministic on IMMEDIATE repeat calls with byte-identical parameters: the served content.checklist.timing_hooks.kala_activations array — a computed evidence set backing the response's timing narrative — differs between two back-to-back calls fired in the same batch (~2.3s apart). Call 1 returned 4 distinct deduped activation windows (ids 8095951, 7858084, 8177250, 7859260) and judgment_flags[].kala_activations_trimmed read '...deduped by window to 4 distinct window(s)'. Call 2, same params, returned 6 distinct windows -- the same 4 PLUS two additional entries never present in call 1 (id 7845521, signature_class=DIGNITY; id 8115481, signature_class=SUBSYSTEM) -- and the flag text changed to '...deduped by window to 6 distinct window(s)'. Both calls agreed on verdict_grade ('convergent_strong') and composite_score (4.58), so the headline verdict number is stable, but the served supporting-evidence array underneath it is not -- a caller drilling into 'why does this verdict hold' would see a different evidentiary picture depending purely on which of two identical calls they happened to read. This is exactly the class of defect CLAUDE.md's deterministic-first / no-fabricated-computation doctrine (§N.4, B.10) is meant to prevent: the same chart_id + domain + ayanamsha should always yield the same activation-window dedup result.

**Reproduce.**

```
mcp__marsys-jis-direct__judgment_query({chart_id:'482012f1-710e-4a25-994a-93821f5871aa', domain:'career'}) called twice in immediate succession (same batch) -- diff content.checklist.timing_hooks.kala_activations and judgment_flags[] where code='kala_activations_trimmed' between the two responses.
```

**Evidence.** `evidence/judgment_query__career_call1.json, evidence/judgment_query__career_call2.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE -- behavior confirmed live exactly once this session (two calls, unambiguous divergence in a computed array: 4 vs 6 rows, 2 rows in call 2 entirely absent from call 1). Did not trace the judgment_query handler's kala_activations dedup-by-window query in platform/src to pin the exact file:line, but the shape of the defect (a 'raw N rows deduped by window to M distinct windows' step where M itself varies call-to-call on identical inputs) is consistent with a classic missing-deterministic-tiebreaker bug: a GROUP BY / DISTINCT-style window-dedup query with no total ORDER BY (or a LIMIT applied before a stable sort), so which rows survive the dedup pass is not guaranteed stable across repeated executions -- the same defect class §N.7 item 2 already names for fact-selection queries ('every fact selection that reduces a set to one row pins fact_key and carries a total ORDER BY'), here occurring one level up in an array-reducing (not single-row) selection.

**Proposed remediation.** Add a total tiebreaker to `judgment_query`'s activation-window dedup and add a repeat-call `result_hash` equality test in CI for the top ~20 tools.

##### F-115  ·  `high`

**Claim.** Two tools on the same server name different #1 remedy targets for the same chart from the same underlying asset. bodha_remedies_get: 'Your Bodha remedy layer flags VENUS as your #1 remedy-priority target - resonance_score 0.173195, priority class CRITICAL - followed by Ketu, Rahu, Moon.' assess_career's remedies reading family: 'Your Bodha remedy layer flags KETU as your #1 remedy-priority target - resonance_score 0.139, priority class HIGH - followed by Rahu, Moon, Jupiter.' Ketu is rank 2 in the authoritative listing. assess_career silently drops the rank-1 critical row and promotes rank 2 to '#1', with a lower score and a lower priority class, using the identical sentence template. A consumer asking about remedies in a career context is told to prioritise the wrong graha and is given a milder severity than the data carries.

**Reproduce.**

```
Q2 vs Q4. Call bodha_remedies_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, limit=8, fields='compact') and read .content.narration.lead. Then jq -r '.object.reading[]|select(.family=="remedies")|.sentences[0]' on E2_q2_raw_assess_career.json.
```

**Evidence.** `pp2-audit/evidence/E2_q4_remedy_now_trace.json | pp2-audit/evidence/E2_q2_raw_assess_career.json`

**Mechanism.** assess_career's remedies family selects its 'top' resonance row without pinning the rank-1 ordering key - a fact-selection-without-total-ORDER-BY defect of exactly the class CLAUDE.md N.7 item 2 describes. The two surfaces rank over bodha_rm_resonances with different (or non-total) orderings, so 'the #1 target' is whichever row the query happened to return first. Neither surface flags the disagreement.

**Proposed remediation.** Pin the rank-1 ordering key on `bodha_rm_resonances` so two tools reading the same asset cannot name different #1 remedy targets with different priority classes.

#### CL-17 Malformed source data crashing or leaking through unguarded parsers

> *Class root mechanism and remediation lane stated in full at §3.1; CL-17 spans multiple tiers.*


##### F-71  ·  `TIER2`

**Claim.** The mi_bhara asset (the actual Living-LEL calibration-plane writer that would populate calibration_maturity, if A4-F-59's wiring gap were closed) is itself broken for the native chart: asset_throughput.state='error', crashing inside its own falsifier-resolution phase before it can compute anything, due to a NULL value from a malformed row in brahma_prospective_ledger. Root data condition (4 rows with observation_window = the PostgreSQL 'empty' daterange literal) is the SAME underlying data defect already documented in manifest finding F-01, but here it produces a DIFFERENT, distinct failure: a build-fatal Python TypeError inside the mi_bhara writer, not F-01's leaked-parser-string in query_prospective_ledger.ts. For the second (zero-history) chart, mi_bhara fails for an unrelated reason: BLOCKED on an incomplete upstream dependency (ka_kshetra).

**Reproduce.**

```
SQL: SELECT * FROM asset_throughput WHERE asset_id='mi_bhara' AND chart_id='482012f1-710e-4a25-994a-93821f5871aa' -> state='error', last_error contains 'TypeError: float() argument must be a string or a real number, not NoneType' at services/mi_bhara/db.py:189; SELECT observation_window::text, lower(observation_window), upper(observation_window) FROM brahma_prospective_ledger WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND lifecycle_status='open' -- 4 of 20 sampled rows show observation_window='empty' with lower()/upper() both NULL
```

**Evidence.** `evidence/db__mi_bhara_asset_throughput_and_prospective_ledger.json`

**Mechanism.** platform/python-sidecar/services/mi_bhara/db.py:189 -- fetch_open_predictions()'s list comprehension does `window_start=float(r['w_start'])` where w_start is computed in SQL as `(lower(observation_window) - %s::date)::double precision`. For a PostgreSQL EMPTY range literal, lower()/upper() both evaluate to NULL (not an error, not caught by the query's own `observation_window IS NOT NULL` filter, since an empty range is itself non-NULL -- only its bounds are). float(None) raises TypeError, which propagates uncaught up through mi_bhara.py:141 (run()) and asset_runner.py:440/562, halting the ENTIRE mi_bhara build for this chart with zero rows written. Same 4 malformed rows F-01 already identified (prediction_ids 59c9f870-2200-47be-9d62-534a5812ce81, 94d6679c-96d2-4b7b-81b3-b4192705dcd1, 8ef06a85-7192-47c8-aa3f-de3f724d9f7f, b7cd449b-9927-4954-920d-6b54abbe11b5).

**Proposed remediation.** Guard `mi_bhara`'s `float()` against NULL and repair the four source rows (shared root cause with F-01) so the calibration-plane build can complete at all.

#### CL-18 Error-hygiene leaks (raw driver/upstream text and internal routes to the caller)

> **Root mechanism (class-level).** Shared helpers embed an upstream response body or driver exception verbatim into a thrown Error with no sanitization boundary between the internal service mesh and the MCP caller. callSidecarPath/callSidecarGet in register_p1_aliases.ts do `throw new Error(\`[alias] sidecar ${path} failed (${res.status}): ${txt.slice(0,200)}\`)` at 10 call sites across ~7 tools, leaking both the internal microservice route ('/api/pyhora/compute', '/api/compute/phala/muhurta_finder') and the raw CPython exception ('Invalid isoformat string: ...') (F-90). ref_rules_search served a raw Postgres 'invalid byte sequence for encoding UTF8: 0x00' literal into content.content (F-89). Same class as CL-17's symptom.

> **Class remediation lane.** LANE-ERRSANITIZE: one sanitizing error boundary at the MCP dispatch edge that maps upstream failures to typed, path-free, driver-text-free MCP errors, with the raw text logged server-side only.


##### F-89  ·  `TIER2`

**Claim.** ref_rules_search leaked a raw, unsanitized Postgres error literal ('error: invalid byte sequence for encoding "UTF8": 0x00') directly into the response's content.content field with is_error:true, when the `keyword` free-text parameter reached the database query in a state that triggered a Postgres encoding exception. Same defect CLASS as F-01 (leaked Postgres 'empty' daterange literal) and the raw-upstream-error-leak class this audit's task brief names: an internal driver/DB exception string reaches the MCP caller verbatim instead of being caught and re-served as a clean structured error.

**Reproduce.**

```
mcp__marsys-jis-direct__ref_rules_search({keyword:'Saturn null byte test'}) -- captured live once during this audit session (first call in a two-tool-call batch). NOTE: two immediate retries of the byte-identical keyword string (standalone, and re-paired with the same adjacent unicode/RTL-override query) both returned the tool's normal clean honest-empty shape instead of the error -- the trigger condition was not reliably reproduced on demand, but the captured response itself is an unedited, genuine server response, not a fabrication.
```

**Evidence.** `evidence/ref_rules_search__G_raw_postgres_error_leak.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE -- behavior confirmed live exactly once this session (raw Postgres UTF8 encoding-violation error text served verbatim in content.content, is_error:true, no MCP-level sanitization wrapper). Did not trace the ref_rules_search handler's keyword-matching SQL (likely an ILIKE/tsquery WHERE clause) in platform/src to pin the exact file:line where a Postgres exception is caught and re-thrown/served without message sanitization; reproduction was intermittent across 3 attempts with the identical parameter value, suggesting the trigger depends on transient byte-level content in the parameter as it crossed some encoding boundary rather than the literal ASCII text alone. Flagged as a real instance of the class regardless, since the one captured response is unambiguous raw internal-driver text reaching the caller.

**Proposed remediation.** LANE-ERRSANITIZE — catch driver exceptions at the query boundary and re-serve a typed error; no Postgres text may reach `content.content`.

##### F-90  ·  `TIER2`

**Claim.** A shared, unguarded error-handling helper in the MCP-facing alias layer leaks raw upstream Python-sidecar error text AND internal API routing paths to the MCP caller whenever the sidecar call fails, across at least 7 distinct MCP tools / 10 call sites. Confirmed LIVE on two tools this session: (1) ganita_natal_positions_compute with a malformed datetime_iso returned {"error":"Error: [alias] sidecar /api/pyhora/compute failed (500): {\"detail\":\"Computation error: Invalid isoformat string: 'not-a-real-date'\"}"}; (2) kala_muhurta_get with malformed start_date/end_date returned {"error":"Error: [alias] sidecar /api/compute/phala/muhurta_finder failed (422): {\"detail\":\"date_range must have 'start' and 'end' ISO date strings: Invalid isoformat string: 'not-a-date'\"}"}. Both leak: (a) the internal sidecar's relative API path structure ('/api/pyhora/compute', '/api/compute/phala/muhurta_finder' -- internal microservice routing, not part of the MCP tool's documented surface), and (b) the raw Python exception message verbatim ('Invalid isoformat string: ...', a CPython datetime.fromisoformat() error string), with zero sanitization into a clean structured MCP error.

**Reproduce.**

```
mcp__marsys-jis-direct__ganita_natal_positions_compute({datetime_iso:'not-a-real-date', latitude_deg:999, longitude_deg:999}) | mcp__marsys-jis-direct__kala_muhurta_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa', start_date:'not-a-date', end_date:'also-not-a-date'})
```

**Evidence.** `evidence/register_p1_aliases__G_sidecar_error_leak.json`

**Mechanism.** platform-mcp/src/tools/register_p1_aliases.ts:127-139 (callSidecarPath) and :150-161 (callSidecarGet) are the two shared helpers every '[Phase-1 alias]' MCP tool in this file routes its Python-sidecar calls through. On a non-2xx sidecar response, both do the identical unsafe thing: `throw new Error(\`[alias] sidecar ${path} failed (${res.status}): ${txt.slice(0, 200)}\`)` (line 136) / `... sidecar GET ${path} failed ...` (line 158) -- txt is the sidecar's raw HTTP response body (up to 200 chars), embedded verbatim into the thrown Error's message with no attempt to parse out just a safe summary, and `path` is the internal relative sidecar route. This single unguarded pattern is the shared root cause behind at least 10 call sites in this one file: callSidecarGet at lines 1391, 1410, 1429, 1446, 1459 (the ref_planet_position_get / ref_planet_transit_get / ref_aspects_at_time_get / ref_retrograde_periods_get / one more ephemeris alias family) and callSidecarPath at lines 1730, 1776, 1796, 1873, 1970 (phala_predictive_anchors_get/event_anchors, kala_muhurta_get, phala_outlook_get, and ganita_natal_positions_compute x2). Only 2 of these 7+ tools were live-reproduced this session (budget-limited sampling); the shared-helper root cause means the remaining call sites are very likely to exhibit the identical leak on their own malformed-input paths, not independently verified live here.

**Proposed remediation.** Add one sanitizing error boundary at the alias/sidecar dispatch edge that strips internal routes and CPython exception text, logging the raw text server-side only.

#### CL-19 Chart-scope entitlement boundary crossed inconsistently

> *Class root mechanism and remediation lane stated in full at §3.1; CL-19 spans multiple tiers.*


##### F-38  ·  `TIER2`

**Claim.** kala_now_get performs no entitlement/existence check on chart_id before doing substantial work, unlike every other chart-scoped tool tested in this audit (ganita_chart_facts_get, assess_career, judgment_query, dossier, catalog_chart_select all cleanly reject a nonexistent chart_id with ENTITLEMENT_DENIED/AUTHZ_DENIED before any computation). Given a syntactically-valid but nonexistent chart UUID, kala_now_get instead returns a full, structurally successful-looking envelope: real (but chart-UNRELATED) live planetary transit data in gochara_dual_reference, a populated reading/verdict/tri_plane/coverage structure, and — inside provenance_envelope.panchanga_native_context_error — the raw upstream microservice error string `"HTTP 404: Chart 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee' not found"` leaking through verbatim. The caller receives no clean signal anywhere in the envelope that the chart_id does not exist; they would have to notice that most `coverage[].state` entries read 'honest_empty'/'unreachable' and infer it themselves.

**Reproduce.**

```
mcp__marsys-jis-direct__kala_now_get(chart_id='aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee')
```

**Evidence.** `evidence/kala_now_get__nonexistent_uuid.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE — behavior pinned by live response only; did not trace the kala_now_get handler source in platform/src to confirm exactly where the entitlement check is skipped or where panchanga_native_context_error is populated verbatim from the upstream HTTP client. Response shape strongly suggests kala_now_get's substrate calls (panchanga service, L3 registries) are invoked directly without a preceding chart-entitlement gate that the other tested tools share.

**Proposed remediation.** Apply the same chart-existence and entitlement precondition every sibling chart-scoped tool already uses, before `kala_now_get` performs any computation.

##### F-127  ·  `high`

**Claim.** bodha_bundle_get — the tool designed to serve the B.11 whole-chart-synthesis bundle in one call — returns DEGRADED status on a plain, unparameterized call for the native's canonical chart: 5 of 8 subsystems (MSR, CGM, LEL, PANCHANG, DASHA) error with error_class=tool_error, leaving only UCN/RM/CDLM served. The tool's own sub_errors_note states this explicitly: 'This is NOT a complete whole-chart read (B.11) — the failing subsystems are named in sub_errors; do not treat the served sections as exhaustive.' A caller following the documented B.11 whole-chart-read path through this tool would either compose an incomplete reading or need out-of-band knowledge to fall back to individual subsystem tools.

**Reproduce.**

```
Call mcp__marsys-jis-direct__bodha_bundle_get with chart_id=482012f1-710e-4a25-994a-93821f5871aa (no other params)
```

**Evidence.** `pp2-audit/evidence/E3_read1_general_trace.json (step 3)`

**Mechanism.** bodha_bundle_get response envelope: status=degraded, ok=false, b11_floor_passed=false, sub_tools_errored=[MSR,CGM,LEL,PANCHANG,DASHA]. Recommendation: fix or fail loudly at the orchestration layer rather than silently degrading a tool whose entire purpose is completeness assurance for the B.11 discipline.

**Proposed remediation.** Closed by the F-30/F-74 principal fix; keep the honest `sub_errors_note` and `b11_floor_passed:false` degrade as the regression anchor rather than removing it.

#### CL-20 Classical-derivation defects (wrong predicate, or technique with no computed representation)

> *Class root mechanism and remediation lane stated in full at §3.1; CL-20 spans multiple tiers.*


##### F-107  ·  `TIER2-QUALITY`

**Claim.** judgment_query(domain='wealth') and bodha_mechanisms_get, when asked to answer DC-W-16 ('What convergent mechanisms across my D1, D2, D11 and Indu Lagna support or contradict wealth accumulation?'), silently substitute a D1-natal-graph-only mechanism list for the specific cross-varga (D2/D11/Indu Lagna) convergence the question named — no field, filter, or row anywhere in the response references D2, D11, or Indu Lagna.

**Reproduce.**

```
MCP bodha_mechanisms_get {chart_id:'482012f1-710e-4a25-994a-93821f5871aa'} — inspect response: mechanism rows (convergent_dispositor_chain onto Jupiter, mutual_aspect_triangle x84, mutual_aspect x36) are all snapshot_type='static_natal' (D1 only); no D2/D11/Indu-Lagna-scoped mechanism facet exists on this tool.
```

**Evidence.** `evidence/E1_dark_corpus_21q_results.json (item DC-W-16)`

**Mechanism.** bodha_mechanisms_get (bo_yantra_mechanism writer / CGM subgraph) is architecturally scoped to the D1 chart-facts graph only; it has no varga/divisional-chart parameter and no notion of cross-varga mechanism convergence (D1 promise vs D2/D11 confirmation vs Indu Lagna). A user asking the acharya-grade question 'do my D1, D2, D11, and Indu Lagna agree on wealth' gets a real, well-cited, but entirely off-topic D1-only mechanism dump instead — the specific convergence-across-vargas technique the question named is never computed anywhere in the served surface, and nothing in the response discloses that the D2/D11/Indu-Lagna legs were skipped.

**Proposed remediation.** Register cross-varga (D2/D11/Indu Lagna) convergence as a first-class checklist unit — even if initially `not_built` — so its absence is disclosed rather than silently answered with a D1-only substitute.

##### F-108  ·  `TIER2-QUALITY`

**Claim.** The bhavat-bhavam (house-from-house amplification) technique named in DC-W-21 ('Given all bhavat-bhavam amplifiers on my wealth houses, what is the net structural verdict?') is entirely absent from the live served concept model — judgment_query(domain='wealth') never names or computes it, and a direct keyword search confirms zero matching fact_category/alias entries exist.

**Reproduce.**

```
MCP judgment_query {chart_id:'482012f1-710e-4a25-994a-93821f5871aa', domain:'wealth'} — response has no field, checklist unit, or judgment_flag mentioning 'bhavat-bhavam' or house-from-house amplification anywhere. Confirming lookup: MCP ganita_chart_facts_get {chart_id:'482012f1-710e-4a25-994a-93821f5871aa', keyword:'bhavat'} returns 0 rows, empty_reason states 'No concept alias or live fact_category matched bhavat — checked 29 seed alias entries and 219 live fact_category values'.
```

**Evidence.** `evidence/E1_dark_corpus_21q_results.json (item DC-W-21)`

**Mechanism.** judgment_query's classical checklist (bhava/bhavesha/karaka/varga/yogas/timing) has no bhavat-bhavam unit — the technique of judging a house's promise through the house-counted-from-that-house lens (e.g. the 2nd-from-2nd as amplifier of wealth) is a documented classical Jyotish method with no corresponding fact_category, computed signal, or checklist unit anywhere in the served surface. A user asking this specific expert question receives a real, well-cited, but generic wealth verdict (dhana/raja yoga firings, afflictions) that never engages the named technique, and no judgment_flag discloses the omission the way other coverage gaps on this same tool are disclosed (e.g. 'ashtakavarga: not_joined', 'special_lagnas: not_joined' are honestly flagged in reading_checklist.units, but bhavat-bhavam is not even listed as a known-absent unit — it is unrepresented in the checklist's own vocabulary, not just unserved).

**Proposed remediation.** Register bhavat-bhavam as a named checklist unit (initially `not_built`) so a question naming the technique gets a disclosed gap instead of a silent substitution.

#### CL-21 Response-envelope shape mismatch (double-enveloping) — top level contradicts nested payload

> *Class root mechanism and remediation lane stated in full at §3.1; CL-21 spans multiple tiers.*


##### F-128  ·  `high`  ·  *also manifests as CL-10*

**Claim.** bodha_discoveries_get — described as serving 'the system's highest-signal cross-domain observations... acharya-grade discoveries' — at min_salience=0.5 returns 15 rows whose 'discovery' content is entirely raw internal signal_type_id strings in template sentences (e.g. surface_reading='Signal tajik_hadda_lord:sign appears unremarkable to pattern inspection', hypothesis_text='Pattern kp_cuspal_significators:sign_lord represents a chart-unusual semantic configuration whose practical significance may be underweighted') with zero actual Jyotish interpretive content — none of the 15 rows states what the signal MEANS for the native, only that it is a statistical embedding outlier. Additionally, the SAME response is internally contradictory: the outer envelope carries judgment_flags=[{code:'hollow_envelope_no_data_rows', detail:"the served 'discoveries' field is empty for this call"}] and separately reports discoveries:[], total:0, returned:0 at the top level, while content.content.rows simultaneously carries the 15 fully-populated discovery objects described above.

**Reproduce.**

```
Call mcp__marsys-jis-direct__bodha_discoveries_get with chart_id=482012f1-710e-4a25-994a-93821f5871aa, limit=15, min_salience=0.5
```

**Evidence.** `pp2-audit/evidence/E3_read1_general_trace.json (step 6)`

**Mechanism.** bodha_discoveries_get response: judgment_flags[0].code=hollow_envelope_no_data_rows contradicts content.content.rows (15 populated objects) and discovery_families (15 grouped motifs). surface_reading/hypothesis_text templates render raw signal_type_id colon-namespace strings verbatim (e.g. 'aspect_tajik:eesarpha', 'aspect_tajik:ithasala', 'dispositor_chain_per_varga:chain') instead of a rendered classical-Jyotish interpretation.

**Proposed remediation.** Apply the F-16 unwrap fix and derive the `hollow_envelope_no_data_rows` flag from the same unwrapped rows it describes, so an envelope can never contradict its own payload.

#### CL-22 Governance / registry drift and auditability

> **Root mechanism (class-level).** Multiple governance registries have no enforced 1:1 reconciliation, so genuine new drift is indistinguishable from the accepted residual. drift_detector.py exits 3 with 216 findings and schema_validator.py exits 3 with 43 violations on the clean tree (F-94/F-95) — both functioning as designed against a knowingly-accepted nonzero baseline, but that baseline includes at least one unambiguously fresh GA.1-class defect (CURRENT_STATE.last_session_id F1-AMENDMENT-… vs SESSION_LOG tail F1-ADOPTION-…). CAPABILITY_MANIFEST.json's 115 entries are ALL governance-doc canonical_ids with zero ga_*/bo_*/ka_*/ph_*/mi_*/bg_* ids, so the CLAUDE.md §C-2 claim that it is the single source of truth cannot cover the >120-row asset_registry, and no reconciliation mechanism between the two exists (F-81). Migration 456_lel_schema_v2_event_shapes.sql is recorded as applied but its SQL is deleted outright rather than archived — the one exception in 430 applied rows (F-79).

> **Class remediation lane.** LANE-GOVDRIFT: drive the known_residuals whitelist to an explicit enumerated list so any un-whitelisted finding fails close, reconcile CURRENT_STATE/SESSION_LOG, restore migration 456 to _archive/, and either extend the manifest to asset_registry or amend §C-2's scope claim.


##### F-79  ·  `TIER2-AUDITABILITY`

**Claim.** Migration 456_lel_schema_v2_event_shapes.sql is recorded as applied in _migrations_applied (applied_at 2026-07-18T23:30:11.222Z, sha256 a6d30ee4...) but its SQL source file does not exist anywhere in the repository -- not in platform/migrations, not in platform/supabase/migrations, and not in platform/migrations/_archive/ (unlike 6 sibling filename/no-file mismatches -- 118/124/125/126/127_build_notifications/133_notification_views -- which are all legitimately archived under platform/migrations/_archive/). A different migration, 457_lel_schema_v2_event_shapes.sql, exists on disk and is separately recorded as applied one second later with a DIFFERENT sha256 (fdc1edb0...), so this is not a simple filename rename of identical content -- 456's actual SQL, once run against production, is now unrecoverable from the repository for audit or rollback-safety review.

**Reproduce.**

```
SELECT filename, applied_at, sha256, sql_identity FROM _migrations_applied WHERE filename IN ('456_lel_schema_v2_event_shapes.sql','457_lel_schema_v2_event_shapes.sql'); -- then: find /Users/Dev/Vibe-Coding/Apps/Madhav -name '456_lel_schema_v2_event_shapes.sql' (not -path '*/node_modules/*' etc) -> no results anywhere in the repo, including archive dirs
```

**Evidence.** `evidence/migrations_applied_vs_disk_diff.json`

**Mechanism.** CLAUDE.md SS N.4 'Surgical migrations, verified' requires migrations be authored surgically and never edited after application; it does not explicitly require permanent retention of applied migration source, but the project's own practice for every OTHER superseded/renumbered migration in this window is retain-in-place under _archive/ (ONGOING_HYGIENE_POLICIES SS archival retain-in-place). 456_lel_schema_v2_event_shapes.sql is the one exception in the entire 430-row _migrations_applied set where an applied migration's source was deleted outright rather than archived, breaking the 'every applied migration's SQL is inspectable' invariant the archive convention otherwise upholds project-wide.

**Proposed remediation.** LANE-GOVDRIFT — restore migration 456's SQL to `platform/migrations/_archive/`, or record it as permanently unrecoverable in the residual register with a named owner and a rollback-risk note.

##### F-94  ·  `major`

**Claim.** drift_detector.py exits non-zero (exit=3, 216 findings) on the current repo state Ran `python3 platform/scripts/governance/drift_detector.py --repo-root . --session-id PARIPURNA2-W3-2-FM25-audit` against the unmutated, post-revert repo state (agent worktree audit/paripurna2-evidence). Result: 216 findings, exit_code=3 (per the script's own compute_exit_code: 0=clean, 1=critical, 2=high, 3=medium/low-only, 4=script error). Breakdown by class: registry_disagreement=84, canonical_unreferenced=77, phantom_reference=52 (all 52 carry whitelist_ticket and are excluded from the exit-code computation), governance_stack_disagreement=1, schema_file_empty=1, a3_schema_db_unreachable=1 (LOW; this last one is an environment artifact — no local Postgres reachable in this worktree at 127.0.0.1:5433 — not a documentation-registry drift). That leaves 164 non-whitelisted MEDIUM/LOW findings driving the exit=3, e.g.: evidence="FILE_REGISTRY does not name 'CGP_AUDIT_v1_0.md'" (registry_disagreement), evidence="GOVERNANCE_STACK does not name 'MSR_v5_0.md'" (governance_stack_disagreement), evidence="Canonical CGP_AUDIT_v1_0 (CGP_AUDIT_v1_0.md) not referenced in any surface" (canonical_unreferenced), evidence="CHART_FACTS_SCHEMA.json has no columns declared" (schema_file_empty). Per the audit brief's framing this canonical-path/registry-disagreement check is meant to be always-green, and the observed result is not green. Calibration note: IMPORTANT CONTEXT before treating this as newly-discovered drift: ONGOING_HYGIENE_POLICIES_v1_0.md §F explicitly documents exit code 3 (MEDIUM/LOW findings only, no HIGH/CRITICAL) as 'the normal baseline when drift_detector.py reports pre-existing whitelisted MEDIUM/LOW drift', gated on each session's close checklist carrying a `known_residuals` block. SESSION_LOG.md's most recent matching entry (line ~31778) records `drift_detector_run: {exit_code: 3, divergences_found: 219, disposition: "pre-existing baseline (ONGOING_HYGIENE §F exit-3 whitelist); 0 findings reference this session's files"}` — i.e. 219 findings at that prior close vs 216 measured here, a small delta consistent with normal accrual/whitelist churn rather than a fresh regression. So this finding is best read as: the guard is functioning as designed (it detects and reports the drift correctly) and the project's own governance process has knowingly accepted a nonzero (exit=3) baseline rather than driving it to exit=0 — this is a documented, accepted policy exception, not evidence drift_detector.py is broken or miswired. Recorded as 'major' per this audit wave's literal finding taxonomy ('drift_detector.py reported real drift = major'), but the disposition is 'known accepted baseline', not 'undiscovered defect'.

**Reproduce.**

```
Run drift_detector.py (platform/scripts/governance/drift_detector.py) against current repo state
```

**Evidence.** `pp2-audit/evidence/ (drift_detector run captured inline in this finding; raw JSON/MD written to scratchpad, not committed, per task scope — repo-root run: exit=3, 216 findings, 164 non-whitelisted, matches SESSION_LOG's most recent exit-3/known-baseline precedent)`

**Mechanism.** DIAGNOSIS-INCOMPLETE

**Proposed remediation.** Drive `drift_detector.py`'s known_residuals whitelist to an explicit enumerated list so any un-whitelisted finding fails closed, and commit the run artifact as evidence rather than leaving it in a scratchpad.

##### F-95  ·  `major`

**Claim.** schema_validator.py does not exit clean on the current repo state platform/scripts/governance/schema_validator.py (run with no args, its default manifest-mode invocation) reports 43 violations and exits with code 3 (per its own exit-code legend printed in the report: '0 clean; 1 critical; 2 high; 3 medium/low; 4 script error'). This is not a clean pass. Breakdown: 31x 'frontmatter_field_missing[architecture_governance/artifact]' (LOW/MEDIUM) across 00_ARCHITECTURE/*.md artifacts missing a required `artifact:` frontmatter key; 11x 'session_log_entry_missing_next_objective_heading' (LOW) on historical SESSION_LOG.md entries dated 2026-07-14 through 2026-07-22 missing a '### Next session objective' heading; and 1x 'current_state_last_session_id_disagreement' (MEDIUM), a genuine registry cross-reference mismatch: CURRENT_STATE.last_session_id=`F1-AMENDMENT-CONDUCTOR-2026-08-09` but the SESSION_LOG.md tail entry is `F1-ADOPTION-CONDUCTOR-2026-08-09` -- exactly the GA.1-class 'registries must not disagree' failure mode CLAUDE.md B.8 warns against. No CRITICAL or HIGH severity violations were found. Run performed AFTER the FM-26 mutation was reverted (git diff --quiet confirmed clean on the mutated file first), so this is unrelated to and uncontaminated by the FM-26 mutation test. Calibration note: This finding is scoped to the secondary Step 6 task (schema_validator.py green check), not to FM-26 itself. Whether the 31 frontmatter/11 session-log LOW items are an accepted, previously-whitelisted baseline (per ONGOING_HYGIENE_POLICIES_v1_0.md's exit-code-3 known_residuals concept) was not independently confirmed against a whitelist artifact in this session's scope; flagged here per the mission's explicit instruction to capture any reported violation. The current_state_last_session_id_disagreement item is the one item of this set that is unambiguously a fresh, concrete registry-drift defect rather than a plausibly-whitelisted historical residual.

**Reproduce.**

```
python3 platform/scripts/governance/schema_validator.py --json-path /tmp/schema_validator.json --report-path /tmp/schema_validator_report.txt
```

**Evidence.** `— none recorded (see §5.3)`

**Mechanism.** 00_ARCHITECTURE/CURRENT_STATE_v1_0.md: CURRENT_STATE.last_session_id=`F1-AMENDMENT-CONDUCTOR-2026-08-09` but SESSION_LOG tail entry is `F1-ADOPTION-CONDUCTOR-2026-08-09`

**Proposed remediation.** Reconcile `CURRENT_STATE.last_session_id` with the `SESSION_LOG` tail (the one genuine GA.1-class defect in the baseline) and backfill the 31 missing `artifact:` frontmatter keys.

---

### §3.3 — TIER 3 — EXPERIENCE & DISCLOSURE  (27 findings)

*A real defect a careful reader can work around, or a disclosure that fires on the wrong condition.*

#### CL-02 Implemented backend with no serving consumer (dead data path + false 'no such data' assertion)

> *Class root mechanism and remediation lane stated in full at §3.2; CL-02 spans multiple tiers.*


##### F-05  ·  `TIER3`

**Claim.** ref_tantric_remedies_get can never return a non-empty result in production for any argument combination, because the only content-ingestion path for tantric remedies (tantric.yaml) is dead code never wired into the actual production seeding pipeline.

**Reproduce.**

```
mcp__marsys-jis-direct__ref_tantric_remedies_get({}) or with any planet/deity filter -> always {remedies:[], returned_count:0}; cross-check: SELECT remedy_type, count(*) FROM brahma_remedy_corpus GROUP BY remedy_type -- 'tantric' never appears
```

**Evidence.** `evidence/ref_tantric_remedies_get__saturn_rahu_and_unfiltered.json`

**Mechanism.** platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:1720 (query logic itself correct). Root cause upstream: platform/python-sidecar/brahmagyan/remedy_corpus/tantric.yaml is only loaded by l0_remedy_loader.py::load_remedies() (sets remedy_type/category='tantric'), which has zero callers anywhere in the repo. The actually-registered production writer (bg_remedies.py -> l0_remedy_corpus.py::build_all_remedies()/seed_remedy_corpus()) never emits 'tantric' despite declaring it in VALID_REMEDY_TYPES.

**Proposed remediation.** Wire `l0_remedy_loader`'s `tantric.yaml` into the production seeding path, or mark `ref_tantric_remedies_get` NOT-IMPLEMENTED in its own description rather than shipping a permanently-empty tool.

#### CL-03 Parameter accepted but never applied (no-op filter / silent value substitution)

> *Class root mechanism and remediation lane stated in full at §3.1; CL-03 spans multiple tiers.*


##### F-133  ·  `medium`

**Claim.** phala_outlook_get called with horizon_months=18 (query_window 2026-08-15 to 2028-02-06) correctly scopes its 'anchors' section to the requested horizon, but its 'mitigations' section is NOT scoped the same way: of the 10 mitigation rows served (trimmed from 100), several carry window_start dates as old as 1966-04-08 and 1993-10-15 — the 1966 window predates the native's own birth (1984-02-05) by 18 years. A remedy/mitigation program keyed to a pre-natal obstruction window is served inside an '18-month forward outlook' response with no flag explaining its relevance or why it was selected ahead of the mitigation rows that actually fall inside the requested horizon.

**Reproduce.**

```
Call mcp__marsys-jis-direct__phala_outlook_get with chart_id=482012f1-710e-4a25-994a-93821f5871aa, horizon_months=18; inspect mitigations[].window_start (native birth date is 1984-02-05)
```

**Evidence.** `pp2-audit/evidence/E3_read2_career_wealth_trace.json (step 5)`

**Mechanism.** phala_outlook_get's mitigations family (ph_pratikara / PH-4-2 layer) is trimmed by row-count (top 10 of 100) without a horizon_months date filter, unlike the anchors family (PH-4-1 layer) which is correctly windowed; the trim ordering surfaces several mitigation rows with obstruction windows decades outside — in one case predating — the native's lifetime.

**Proposed remediation.** Apply `horizon_months` to the mitigations query so a pre-natal (1966) obstruction window cannot appear inside an 18-month forward outlook.

#### CL-04 Unreconciled domain/enum vocabularies + unvalidated input (false honest-zero)

> *Class root mechanism and remediation lane stated in full at §3.2; CL-04 spans multiple tiers.*


##### F-53  ·  `TIER3`

**Claim.** gochara_forecast_get/gochara_activation_get's domain parameter silently returns a false 'honest zero' when passed domain='marriage' -- a natural value since 'marriage' IS the event_class name -- because 'marriage' is not itself a valid domain (the real domain is 'relationship'), and the not-covered refusal guard only fires for domains that are real-but-uncovered, not for domain values that aren't real domains at all.

**Reproduce.**

```
gochara_forecast_get(chart_id='482012f1-710e-4a25-994a-93821f5871aa', date_range={start:'2026-08-15',end:'2036-08-15'}, domain='marriage') -> window_count=0 with a completed-scan-worded empty_reason; contrast domain='relationship' -> window_count=8, or event_class='marriage' -> window_count=3
```

**Evidence.** `evidence/gochara_forecast_get__native_domain_marriage_empty.json`

**Mechanism.** register_gochara_windows.ts:1090-1117 notCoveredFor(domain, coverage): domains_not_covered is populated only from real brahma_event_ontology.domain values, so an invalid string like 'marriage' never appears in that list and the refusal guard silently returns null, letting the downstream SQL filter produce a misleading zero-row result.

**Proposed remediation.** Validate `domain` against the real domain vocabulary and return the documented `not_covered` refusal — with the `event_class` cross-pointer — for the natural-but-wrong value `'marriage'`.

##### F-57  ·  `TIER3`

**Claim.** For domains education, progeny, and residence, judgment_query's internal gochara_sweep and bodha_signals_get drill_pointer silently resolve to a generic domain='other' bucket instead of the actually-requested domain -- a cross-subsystem domain-vocabulary mismatch between the classical-checklist layer (correctly resolves these to bhava 4/5/4) and the transit-forecast layer underneath. Honestly disclosed via a 'gochara_domain_not_covered' judgment_flag each time -- lesser severity than F-55/F-56.

**Reproduce.**

```
judgment_query(chart_id='482012f1-710e-4a25-994a-93821f5871aa', domain='education')  # check content.gochara_sweep.domain
```

**Evidence.** `evidence/judgment_query__education.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE -- likely the gochara_windows/bodha_signals domain enum does not include education/progeny/residence as first-class values and falls back to 'other'; not traced to exact source line.

**Proposed remediation.** Reconcile the classical-checklist and transit-forecast domain vocabularies for education/progeny/residence rather than silently bucketing them to `'other'`; the existing `gochara_domain_not_covered` flag is the right disclosure and should stay.

#### CL-07 Nodal (Rahu/Ketu) special-aspect truncation to the universal 7th

> *Class root mechanism and remediation lane stated in full at §3.1; CL-07 spans multiple tiers.*


##### F-21  ·  `TIER3`

**Claim.** A separate, newer w30_nodal_drishti mechanism exists in engine.py (later-tradition Rahu/Ketu 5/7/9 special-aspect compensator, enabled by default) that would partially offset F-20, but the currently-served native/zero-chart gochara window data shows no trace of it -- the served term_breakdown.formula string is an older formula predating the w30/tara-bala additions, suggesting these charts' gochara windows have not been rebuilt since those mechanisms were added to the codebase.

**Reproduce.**

```
Code read: platform/python-sidecar/services/gochara_v3/engine.py:594-639 (w30_modifier/tara_modifier computed and merged into formula 'lambda_v3 = PROMISE * PERMISSION * activity * tara_modifier * w30_modifier * quality_gates'). Contrast served data: evidence/gochara_activation_get__native_valid_asof.json and evidence/gochara_forecast_get__native_valid_daterange.json -- every window's term_breakdown carries only {formula, promise, activity, lambda_v3, permission, quality_gates, activity_terms} with the OLDER formula string and zero occurrences of tara_modifier/w30_modifier.
```

**Evidence.** `evidence/gochara_forecast_get__native_valid_daterange.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE -- read-only audit cannot distinguish 'charts genuinely need a rebuild to pick up the newer engine' from 'a serving-layer regression drops these fields'. The observable fact (served data does not reflect the codebase's own nodal-aspect compensation mechanism) is confirmed and reproducible, but the root cause is not.

**Proposed remediation.** Rebuild both charts' gochara windows so `w30_modifier`/`tara_modifier` appear in `term_breakdown`, and assert the current formula string in a build test so a stale generation is detectable.

##### F-64  ·  `medium`

**Claim.** A SECOND, independent hardcoded Mars/Jupiter/Saturn-only special-aspect table (NB_GRAHA_DRISHTI, with NB_DEFAULT_DRISHTI={7} as the silent fallback for every other graha) lives in ga_writers/ga_yoga_writer.py, separate from the already-known primitives.py SPECIAL_DRISHTI_DEG (F-20/F-52). It backs the shared helper _nb_aspects_house(), which is called from two places: (a) nbry_rule_3_lord_aspect (Neecha Bhanga Raja Yoga rule 3) -- NOT reachable by the node gap, because rule 3's candidate aspectors are drawn only from NB_SIGN_LORDS (classical sign rulers), and Rahu/Ketu never own a sign lordship in this codebase's model, so a node can never appear as a rule-3 candidate (compliant by construction, verified live: chart 482012f1's neecha_bhanga_raja_yoga firing shows rule_3 'checked':true/'fired':false for both venus@D9 and saturn@D9, consistent with classical sign lords only); and (b) _cancel_vipareeta_raja_yoga's dilution loop, which IS reachable by the gap -- it iterates `for other, oh in state.planet_house.items()` (ALL grahas, including Rahu/Ketu) and calls _nb_aspects_house(other, oh, lord_house) to decide whether `other` dilutes a firing Vipareeta Raja Yoga. Because NB_GRAHA_DRISHTI has no 'rahu'/'ketu' keys, a node sitting at a 5th- or 9th-house offset (not 7th) from the dusthana lord's house is silently treated as non-aspecting, so its classical dilution influence on VRY is missed -- the yoga can be reported as bhanga_active=False ("stands undiluted") or with an incomplete bhanga_rule_fired ground-list when a node's real 5/9 special aspect should have contributed. Live-reachability of the exact code path is confirmed: chart 1c826d5a's vipareeta_raja_yoga firing shows bhanga_active=true via bhanga_rule_fired='conjunct_or_aspected_by_non_dusthana_lord:venus' -- proving _cancel_vipareeta_raja_yoga's dilution loop executes and populates diluted_by from arbitrary planets in state.planet_house (the Venus example demonstrates the mechanism; no chart in the two audited was found with a node at exactly a 5th/9th non-7th offset from a dusthana lord to show the miss directly, so the defect claim rests on the static code plus the confirmed-live mechanism, not a live false-negative instance).

**Reproduce.**

```
grep -n 'NB_GRAHA_DRISHTI\|NB_DEFAULT_DRISHTI\|_nb_aspects_house\|_cancel_vipareeta_raja_yoga' platform/python-sidecar/ga_writers/ga_yoga_writer.py
```

**Evidence.** `pp2-audit/evidence/ganita_yoga_firings_get__vipareeta_raja_yoga__1c826d5a.json; pp2-audit/evidence/ganita_yoga_firings_get__neecha_bhanga__482012f1.json`

**Mechanism.** platform/python-sidecar/ga_writers/ga_yoga_writer.py:1499-1504 (NB_GRAHA_DRISHTI dict keys only mars/jupiter/saturn; NB_DEFAULT_DRISHTI=frozenset({7})) feeding :1588-1592 (_nb_aspects_house) consumed at :2322-2326 (_cancel_vipareeta_raja_yoga's unrestricted dilution loop over state.planet_house, which includes Rahu/Ketu)

**Proposed remediation.** Delete the local `NB_GRAHA_DRISHTI` table in favour of the shared nodal constant (same patch as F-19); the rule-3 path needs no change and its compliance-by-construction should be recorded in the test.

#### CL-08 Tier-honesty leaks (non-calibrated data served at full numeric precision / inflated labels)

> *Class root mechanism and remediation lane stated in full at §3.1; CL-08 spans multiple tiers.*


##### F-117  ·  `medium`

**Claim.** bo_upaya 'resonance' ranking is inverse-shadbala with three constant terms, and its priority labels are inflated. Across all 8 resonance rows: contradiction_factor=0 for every graha, domain_burden=0 for every graha, motif_burden=0.4 for every graha. The only varying input is weakness_score, and the resulting rank order is exactly the inverse shadbala order (Venus sha 0.84 < Moon 0.94 < Ketu 1.00 = Rahu 1.00 < Mars 1.11 < Jupiter 1.20 < Saturn 1.57 < Sun 1.69). Separately, Rahu and Ketu both carry sha=1.00 EXACTLY - shadbala is not classically computed for the nodes, so this is a placeholder - yet they are ranked #2 and #3 'high' priority on it. Finally, a resonance_score of 0.173 on a 0-1 scale is labelled remedy_priority_class 'critical'.

**Reproduce.**

```
Q4. Call bodha_remedies_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, limit=8, fields='compact') and inspect .content.resonances[] for contradiction_factor / domain_burden / motif_burden (all constant) and .content.narration.resonance_ranked[].citation for the sha= values.
```

**Evidence.** `pp2-audit/evidence/E2_q4_remedy_now_trace.json`

**Mechanism.** Three of the four composite inputs are unpopulated or constant chart-wide, collapsing a nominally 4-factor 'resonance' to a monotone function of one factor. The presentation ('resonance_score', 'priority class critical', 'named_affliction_mapping') implies a richer synthesis than the arithmetic supports, and the node placeholder value means two of the top four priorities rest on a number that was never computed. Compare CLAUDE.md N.8: a grade whose discriminating inputs cannot vary is not an earned signal.

**Proposed remediation.** Give `bo_upaya`'s resonance real contradiction/domain/motif inputs or drop the constant terms and rename the field, and stop ranking Rahu/Ketu 'high' on a placeholder ṣaḍbala of exactly 1.00.

#### CL-10 Jargon / raw-internal leakage into user-facing prose

> *Class root mechanism and remediation lane stated in full at §3.2; CL-10 spans multiple tiers.*


##### F-132  ·  `medium`

**Claim.** kala_now_get's reading.thesis — the single sentence that answers the tool's own stated question 'What is my temporal state right now?' — names its strongest active window using raw internal enum concatenation with no plain-language rendering: 'strongest: CLASSIFY_RESIDUAL/DIGNITY/YOGA/SUBSYSTEM (orb strength 1.00, 10 contributing signal(s)).' The response DOES carry a register/glossary elsewhere in the payload that maps some tokens to plain language, but it is not applied to the thesis sentence itself, which is the part of the response most likely to be surfaced to an end user verbatim.

**Reproduce.**

```
Call mcp__marsys-jis-direct__kala_now_get with chart_id=482012f1-710e-4a25-994a-93821f5871aa; inspect object.reading.thesis
```

**Evidence.** `pp2-audit/evidence/E3_read3_timing_trace.json (step 1)`

**Mechanism.** kala_now_get reading.thesis string interpolates window.signature_classes.join('/') directly (raw enum values CLASSIFY_RESIDUAL/DIGNITY/YOGA/SUBSYSTEM) rather than a glossed label.

**Proposed remediation.** Apply the register glossing to `reading.thesis` specifically — the one sentence most likely to be surfaced to an end user verbatim.

#### CL-11 Non-actionable or dead recovery pointers (recover_via / drill_pointers / tri_plane)

> *Class root mechanism and remediation lane stated in full at §3.2; CL-11 spans multiple tiers.*


##### F-17  ·  `TIER3`

**Claim.** bodha_graph_subgraph_get's trim_report/drill_pointers.recover_via.instrument is the literal placeholder 'unknown_tool' instead of the real tool name whenever a response is budget-trimmed.

**Reproduce.**

```
mcp__marsys-jis-direct__bodha_graph_subgraph_get({chart_id: '482012f1-710e-4a25-994a-93821f5871aa', mode: 'neighbors', start_node: '478359a4-0637-46b6-8a78-300ead95787f', depth: 2}) -- content.edges gets trimmed (166->41), recover_via.instrument reads 'unknown_tool'
```

**Evidence.** `evidence/bodha_graph_subgraph_get__native_neighbors_depth2.json`

**Mechanism.** platform-mcp/src/tools/register_p1_aliases.ts:1249 `return dualOutput(data)` omits the toolName argument, so dualOutput's default (register_p1_aliases.ts:188, toolName='unknown_tool') is what applyAutoBudgetToEnvelope uses when constructing recover_via. A sibling fix pattern for this exact defect class already exists in the same file (comments at lines 1800-1803) but was not applied here.

**Proposed remediation.** One-line fix at `register_p1_aliases.ts:1249` — pass the real tool name to `dualOutput`; subsumed by the F-43 file-wide patch.

##### F-18  ·  `TIER3`

**Claim.** bodha_graph_traverse_get's trim_report/drill_pointers.recover_via.instrument is the literal placeholder 'unknown_tool' instead of the real tool name whenever a response is budget-trimmed. Same root cause as F-17.

**Reproduce.**

```
mcp__marsys-jis-direct__bodha_graph_traverse_get({chart_id: '482012f1-710e-4a25-994a-93821f5871aa', mode: 'paths', about_from: 'lord_of(bhava 10)', about_to: {type:'graha',graha:'Moon'}, direction: 'directed'}) -- content.edges gets trimmed (97->48), recover_via.instrument reads 'unknown_tool'
```

**Evidence.** `evidence/bodha_graph_traverse_get__native_paths_10thlord_moon.json`

**Mechanism.** platform-mcp/src/tools/register_p1_aliases.ts:657 `return dualOutput(data)` omits the toolName argument, same defect class/root cause as F-17.

**Proposed remediation.** One-line fix at `register_p1_aliases.ts:657`; subsumed by the F-43 file-wide patch.

##### F-123  ·  `medium`

**Claim.** kala_explain_get hard-errors on the exact call shape kala_now_get advertises. kala_now_get's response contains tri_plane.interpretation_ref = {instrument:'kala_explain_get', hint:'Why this NOW state reads as it does - the drivers and classical grounds behind the active windows and confluence'} and repeats it in drill_pointers, with no indication that any further argument is required. Following that pointer with only chart_id returns {ok:false, error:'either `domain` or `bhava` is required'}. The advertised drill is chart-scoped ('this NOW state'); the target is domain-scoped. 'Explain my current dasha' is domain-less by nature and has no correct value to supply.

**Reproduce.**

```
Q5. Call kala_now_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa), read .tri_plane.interpretation_ref and .drill_pointers[0], then call kala_explain_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa) exactly as pointed and observe the error.
```

**Evidence.** `pp2-audit/evidence/E2_q5_current_dasha_trace.json | pp2-audit/evidence/E2_q1_marriage_timing_trace.json`

**Mechanism.** tri_plane pointers are emitted as static instrument names without the required-argument set, and the pointer is generated at the chart scope while the target validates at the domain scope. Nothing in the pointer payload carries the args the drill needs, so an autonomous consumer following the server's own navigation graph dead-ends.

**Proposed remediation.** Emit required-args alongside every `tri_plane`/drill pointer, or give `kala_explain_get` a chart-scoped mode so a domain-less NOW question has a followable drill.

#### CL-12 Narration-fidelity defects (prose diverges from the rows it sits on)

> *Class root mechanism and remediation lane stated in full at §3.2; CL-12 spans multiple tiers.*


##### F-39  ·  `TIER3`

**Claim.** The shared ENTITLEMENT_DENIED error message template used by ganita_chart_facts_get / assess_career / judgment_query (and similar registry_bridge-backed tools) unconditionally states '(distinct from an empty result — this chart exists but you are not granted)' even when the chart_id supplied is a syntactically-valid but entirely fabricated/nonexistent UUID. The message asserts a specific fact ('this chart exists') that is false in the nonexistent-UUID case, conflating two genuinely different situations (real chart the caller lacks access to, vs. no such chart at all) into one message that actively misstates the nonexistent case. This is a narration-fidelity issue, not a security leak — the denial itself is appropriately generic/safe — but the message text should not assert existence it cannot verify.

**Reproduce.**

```
mcp__marsys-jis-direct__ganita_chart_facts_get(chart_id='aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee')
```

**Evidence.** `evidence/ganita_chart_facts_get__nonexistent_uuid.json`

**Mechanism.** platform-mcp/src/tools/registry_bridge.ts (message template containing the literal string 'this chart exists but you are not granted') — exact line not pinned; DIAGNOSIS-INCOMPLETE on line number, but the message string was directly observed verbatim across three independent tool calls (ganita_chart_facts_get, assess_career, judgment_query) so the shared template's existence is confirmed, only the precise source line is not.

**Proposed remediation.** Split the shared denial template into 'no such chart' and 'exists but not granted' variants, or simply drop the existence assertion the message cannot verify.

##### F-50  ·  `TIER3`

**Claim.** bodha_remedies_get's graha-filtered call reports the requested planet as the user's '#1 remedy-priority target' even when that planet is actually one of the chart's STRONGER planets. graha='Saturn' produces narration '#1 remedy-priority target' but the unfiltered call shows Saturn is rank 8-of-9 (nearly the strongest), consistent with D1 Saturn exalted in Libra house 7. Underlying numeric fields are honestly reported alongside, so a careful reader isn't misled, but the narration sentence in isolation overstates priority.

**Reproduce.**

```
bodha_remedies_get(chart_id='482012f1-710e-4a25-994a-93821f5871aa', graha='Saturn') -> narration says '#1 remedy-priority target'; compare ganita_condition_get(facet='dignity') D1_SAT=exalted and bodha_remedies_get unfiltered -> Saturn rank 8 of 9
```

**Evidence.** `evidence/bodha_remedies_get__saturn.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE -- narration-wording observation ('#1 of 1' phrasing under single-graha filter), not traced to a specific file:line.

**Proposed remediation.** Derive the '#1 remedy-priority target' sentence from the unfiltered ranking rather than from the caller's own filter argument.

##### F-63  ·  `TIER3`

**Claim.** panchanga_special_yoga_combinations fires with active_at_birth_flag='true' but combination_name='unknown' for the native chart (a detector recognizes that SOME named vara+tithi+nakshatra special combination pattern is active at birth, but cannot or does not resolve which one, and serves the literal string 'unknown' instead of either the real classical name or an honest null/inactive state). The equivalent row is simply absent (not present at all, active or otherwise) in the second/comparison chart's panchanga response, so this is not a universal always-on placeholder -- it is conditionally firing 'true' with an unresolved label specifically for the native chart, which is the pattern of a partially-implemented classical-combination lookup table (some combinations recognized and named, this one detected-but-unmapped) rather than a static broadcast default.

**Reproduce.**

```
mcp__marsys-jis-direct__ganita_chart_facts_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa', category:'panchanga'}) -- locate the YOGA_UNKNOWN / panchanga_special_yoga_combinations row (active_at_birth_flag:'true', combination_name:'unknown'). Compare against the equivalent call for chart_id='1c826d5a-41cb-4450-b4dc-59d440e5f75a', which returns 37 panchanga rows with no such YOGA_UNKNOWN entry at all.
```

**Evidence.** `evidence/ganita_chart_facts_get__native_panchanga.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE -- observed only at the served-data level; the classical-combination lookup/matching logic responsible was not located or read in this pass, so whether this is a genuinely-unnamed rare combination (arguably an honest gap) versus a lookup-table bug that fails to match a combination it should recognize could not be determined without reading the source.

**Proposed remediation.** Resolve `combination_name` against the classical combination table or null the row — a detector that fires `true` must name what it detected, never `'unknown'`.

##### F-120  ·  `medium`

**Claim.** ganita_dasha_periods_get's narration drops the finest currently-running period and its sandhi flag. The payload correctly returns four rows including level_n=4 (Sukshma, Mercury, 2026-08-13..2026-08-25) with sandhi_flag=TRUE - i.e. the as_of_date 2026-08-15 falls inside a flagged junction period. The narration string reads: 'You are in Mercury Mahadasha (ends 2027-08-18, age ~43) -> Saturn Antardasha (ends 2027-08-18, age ~43) -> Moon Pratyantardasha (current, ends 2026-09-17, age ~42).' It labels the LEVEL-3 period 'current', stops there, and never mentions the level-4 period or its sandhi_flag. A caller who reads the prose - which is what prose is for - is told they are not in a junction when the data says they are.

**Reproduce.**

```
Q5. Call ganita_dasha_periods_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, ayanamsha_id='lahiri_chitrapaksha', as_of_date='2026-08-15', all_levels=true, fields='compact'). Compare .content.narration against .content.rows[3] (level_n=4, sandhi_flag=true).
```

**Evidence.** `pp2-audit/evidence/E2_q5_current_dasha_trace.json`

**Mechanism.** The narration template is hard-coded to three levels (MD -> AD -> PD) and applies the word 'current' to whichever is last in that fixed chain, regardless of levels_available (which the same response reports as 4). sandhi_flag is not consulted by the narrator at any level. This is a narration-fidelity defect of the CLAUDE.md N.7 class: the prose is not a faithful restatement of the rows it sits on, and it omits precisely the field that would change a reader's behaviour.

**Proposed remediation.** Extend the dasha narration to the finest currently-running level and surface `sandhi_flag` in the sentence, with a golden test against the level-4 row.

##### F-121  ·  `medium`

**Claim.** kala_now_get reports 'not in a dasha junction' while a junction is active. Its dasha_sandhi block computes exactly 4 bands - MD start/end and AD start/end - and reports is_now_within_band=false on all four, with no statement that finer levels were not examined. Meanwhile ganita_dasha_periods_get shows the level-4 Sukshma period running on the same date carries sandhi_flag=true. The band_convention prose does disclose that this is a 'LITE' convention, but discloses only the two-period-vs-one-period simplification, not the level restriction. A caller asking 'am I in a sandhi right now' gets four explicit false values, which reads as an all-clear rather than as a scope limit.

**Reproduce.**

```
Q1/Q5. Call kala_now_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa) and read .dasha_sandhi.bands[].is_now_within_band (all false, levels 1-2 only). Then call ganita_dasha_periods_get(chart_id=same, ayanamsha_id='lahiri_chitrapaksha', as_of_date='2026-08-15', all_levels=true) and read rows[3].sandhi_flag (true).
```

**Evidence.** `pp2-audit/evidence/E2_q1_marriage_timing_trace.json | pp2-audit/evidence/E2_q5_current_dasha_trace.json`

**Mechanism.** The item-1-lite sandhi calendar is built only over currently-active level 1 and 2 periods. Because the response emits an explicit per-band boolean rather than a coverage statement, absence-of-coverage is rendered in the same grammar as absence-of-condition. The honest form would be a coverage entry ('dasha_sandhi levels 3-4: not_computed') alongside the bands; the coverage array instead lists dasha_sandhi as flatly 'computed'.

**Proposed remediation.** Compute `dasha_sandhi` bands at all four levels, or state the level restriction in the same block that emits four explicit `false` values (the LITE convention note currently discloses only the two-period simplification).

##### F-139  ·  `TIER3`

**Claim.** kala_now_get's (and kala_explain_get's) coverage entry for `state_delta` is an honest_empty whose stated BLOCKER is factually false as of today: the reason string asserts 'Requires ka_kshetra field provenance rows (kala_field_windows / kala_field_provenance) for this chart — P-G1 field-build must complete first', but those rows exist in production in quantity (kala_field_provenance = 1,839,618 rows, kala_field_windows = 31,350 rows for chart 482012f1) and ka_kshetra's asset_throughput row reads state='lit', last_built_at 2026-08-15T06:28:11Z. The honest-null itself is correct and by-design (the W3 state_delta computation genuinely is not built); the defect is the attached reason, which sends a reader — human or LLM — to rebuild an asset that is already built instead of to the real remaining work. Under CLAUDE.md §N.7 an honest null's REASON is itself a narration claim and is subject to the same fidelity standard as any other served sentence; this one has drifted behind the data it names.

**Reproduce.**

```
MCP kala_now_get {chart_id:'482012f1-710e-4a25-994a-93821f5871aa'} -> .coverage[] | select(.concept=="state_delta") .reason  ;  SQL: SELECT count(*) FROM kala_field_provenance WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';  SELECT count(*) FROM kala_field_windows WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';  SELECT asset_id,state,last_built_at FROM asset_throughput WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND asset_id='ka_kshetra'
```

**Evidence.** `pp2-audit/p4_prior8_reverification.json (reverifications[4])`

**Mechanism.** The coverage reason for state_delta is a static string literal in platform-mcp/src/tools/kala_views/now.ts (~line 1939-1945, the E6 per-view-elevation coverage block; identical construction in explain.ts). It was written when the field build was genuinely the blocker and encodes that precondition as prose rather than deriving it from a live check. Nothing re-evaluates it against kala_field_windows/kala_field_provenance row presence, so it cannot self-correct once the named precondition is met. Contrast the correct pattern already in this codebase: bodha_quality_get's deriveDefect001Note() (freshness_notes.ts:73-146) re-derives its own status via live SQL on every call specifically so the served note cannot go stale (F-106, graded COMPLIANT). Applies to both kala_now_get and kala_explain_get; defect class CL-12 (narration fidelity).

**Proposed remediation.** Derive the `state_delta` blocker reason from a live row-presence check — the `deriveDefect001Note()` pattern already in this codebase (F-106) — instead of a static string that cannot self-correct.

#### CL-13 Missing disclosure of a known partial or mixed result

> *Class root mechanism and remediation lane stated in full at §3.2; CL-13 spans multiple tiers.*


##### F-31  ·  `TIER3`

**Claim.** assess_health omits the documented reading/domain_completeness/completeness_directive fields for the health domain (F-14) WITHOUT emitting any judgment_flag disclosing the omission, even though the response's own judgment_flags mechanism is live and used for a different, lower-stakes gap in the same payload (budget_exceeded_after_trim). This breaks the self-disclosure pattern the rest of the health-journey chain follows (judgment_query flags 'varga_confirmed_forced_false'/'notably_absent_not_checked' for its own analogous gaps).

**Reproduce.**

```
assess_health(chart_id='482012f1-710e-4a25-994a-93821f5871aa', reading_depth='deep_dive') and assess_health(chart_id='1c826d5a-41cb-4450-b4dc-59d440e5f75a', reading_depth='deep_dive') -- inspect content (no reading/domain_completeness/completeness_directive key) vs judgment_flags (no corresponding disclosure entry)
```

**Evidence.** `evidence/assess_health__native_deep_dive.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE -- DOMAIN_READING_FAMILIES lookup table and handler location already established by F-14; this finding's contribution is the measured downstream consequence (no judgment_flag self-disclosure), not a new code-location claim.

**Proposed remediation.** Emit a `judgment_flag` disclosing the missing reading layer until F-14/F-15 land — the mechanism is already live in the same payload for a lesser gap.

##### F-33  ·  `TIER3`

**Claim.** ganita_dasha_periods_get accepts an as_of_date that precedes the chart's own birth date and silently serves computed, two_pass_verified-tier dasha rows with no structured pre-birth flag or guard -- the only signal the query is nonsensical is a free-text narration side-effect ('age ~-4'), not a machine-checkable field.

**Reproduce.**

```
MCP ganita_dasha_periods_get {chart_id:'482012f1-710e-4a25-994a-93821f5871aa', as_of_date:'1980-01-01', ayanamsha_id:'lahiri_chitrapaksha'} -- native chart born 1984-02-05
```

**Evidence.** `evidence/ganita_dasha_periods_get__pre_birth.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE -- behavior confirmed live but the exact serving-handler file/line was not pinned. Arguably by-design (Vimshottari balance-of-dasha math is well-defined before birth), so the finding is about missing DISCLOSURE, not incorrect math.

**Proposed remediation.** Add a structured pre-birth guard/flag to `ganita_dasha_periods_get` rather than leaving a free-text `age ~-4` as the only machine-detectable tell.

##### F-78  ·  `TIER3-CLARITY`

**Claim.** kala_field_snapshots.event_classes for the second chart (1c826d5a) declares 27 event classes, but only 6 (childbirth, foreign_settlement, marriage, relocation, separation, surgery) actually have rows in kala_field / kala_field_null. The remaining 21 are all present in the same row's skipped_classes array with reason 'no_class_prior_row' (honest-skip per require_baseline()/ClassSkipped in stage4_field.py) -- so this is NOT a silent data-loss bug, but event_classes conflates 'classes the writer attempted to build' with 'classes actually built', with no field-level comment distinguishing the two and no documented caller obligation to subtract skipped_classes before treating event_classes as the built set. No serving-layer TypeScript code currently reads kala_field_snapshots.event_classes (grep across platform/src and platform-mcp/src found zero consumers), so this is presently dormant rather than user-facing, but any future reader of this column risks misreporting build coverage.

**Reproduce.**

```
SELECT unnest(event_classes) FROM kala_field_snapshots WHERE chart_id='1c826d5a-41cb-4450-b4dc-59d440e5f75a' EXCEPT SELECT DISTINCT event_class FROM kala_field WHERE chart_id='1c826d5a-41cb-4450-b4dc-59d440e5f75a';  -- returns 21 rows, all of which appear in the same snapshot row's skipped_classes JSON
```

**Evidence.** `evidence/kala_field_null_25x10_grid.json`

**Mechanism.** writer.py's self._event_classes is populated by _discover_event_classes() (all candidate classes for the chart) and written unconditionally to kala_field_snapshots.event_classes at line ~1760; self._skipped (populated by ClassSkipped exceptions caught during the build) is written separately to skipped_classes. Both are legitimate per-design honest-skip bookkeeping, but nothing enforces event_classes minus skipped_classes' event_class values == the classes with real kala_field rows for any caller that doesn't independently know to compute that set difference.

**Proposed remediation.** Split `event_classes` into attempted-vs-built columns (or document the `skipped_classes` subtraction obligation on the column) before any consumer reads it; currently dormant, so fix it cheaply now.

#### CL-14 Uneven wiring of cross-cutting capabilities across a tool family

> *Class root mechanism and remediation lane stated in full at §3.1; CL-14 spans multiple tiers.*


##### F-46  ·  `TIER3`

**Claim.** ganita_planet_get (and, per response_budget.ts's own doc-comment, likely ganita_condition_get, kala_life_arc_get, kala_projections_get, mimamsa_lel_query, and other tools sharing the same wiring) genuinely trims multiple response sections but never echoes budget_kb_applied/budget_kb_requested and never merges the trim's recover_via pointers into the top-level drill_pointers array -- both of which the stronger finalizeMcpBudget mechanism used elsewhere DOES provide. Inconsistent honest-budget-echo contract across the tool estate. ganita_database_schema_get was also observed missing budget_kb_applied despite trimming, corroborating this gap is not isolated to one tool.

**Reproduce.**

```
mcp__marsys-jis-direct__ganita_planet_get({chart_id: '482012f1-710e-4a25-994a-93821f5871aa', planet: 'Saturn'}) -- observe 6 trim_report entries each floored to 10, yet no budget_kb_applied field anywhere and top-level drill_pointers remains []
```

**Evidence.** `evidence/ganita_planet_get__missing_budget_echo.json`

**Mechanism.** platform-mcp/src/tools/register_p1_ganita.ts:155-168 (dualOutput calling applyAutoBudgetToEnvelope) vs. the stronger finalizeMcpBudget (platform-mcp/src/lib/response_budget.ts:361-441, sets budget_kb_applied/budget_kb_requested at lines 380-381 and merges recover_via into drill_pointers at line 384). applyAutoBudgetToEnvelope (response_budget.ts:584-598) only appends trim_report -- never attaches the honesty-echo fields the sibling function does.

**Proposed remediation.** LANE-PARITY — route `ganita_planet_get` and its siblings through `finalizeMcpBudget` so the budget echo and merged drill pointers are uniform across the estate.

##### F-124  ·  `medium`

**Claim.** The three assess_* siblings are advertised as equivalent domain assessments but differ sharply in depth. assess_career returns a substance-inline `reading` array carrying 11 of 12 career concept families as grounded, fact_id-cited sentences (per-varga AV, D10, karakamsha, argala, dispositor closure, mechanisms, special lagnas, cross-ayanamsha agreement, timing, remedies, contradictions) plus a completeness_directive and a 13,825-concept domain_completeness accounting. assess_marriage and assess_health return NO `reading` field, NO completeness_directive and NO domain_completeness at all. assess_career also returned 2 CONFIRMED domain-bearing yoga firings (Sasa, Budha Aditya) from the same 13 chart-wide firings for which marriage and health both got the flag 'none name only this domain's bhavesa/karaka(s)'. A consumer cannot know from the tool descriptions - which are near-identical in structure - that a marriage or health question will be answered several tiers more thinly than a career one.

**Reproduce.**

```
Q1/Q2/Q3. Compare jq '.object|has("reading"),has("completeness_directive"),has("domain_completeness")' across E2_q2_raw_assess_career.json (all true) vs E2_q1_raw_assess_marriage.json and E2_q3_raw_assess_health.json (all false).
```

**Evidence.** `pp2-audit/evidence/E2_q2_raw_assess_career.json | pp2-audit/evidence/E2_q1_raw_assess_marriage.json | pp2-audit/evidence/E2_q3_raw_assess_health.json`

**Mechanism.** The Omega5 gather-then-compose reading/completeness layer has been wired to assess_career only; the sibling handlers still return the older bundle shape. Because the depth difference is invisible in the tool schema and in the envelope (all three report orientation_ok:true and a populated reading_checklist claiming 10/13 units served), the thinner responses present as complete.

**Proposed remediation.** Promote reading-layer attachment to shared middleware over the tool registry so sibling `assess_*` tools cannot differ by tiers of depth behind near-identical descriptions.

##### F-125  ·  `medium`

**Claim.** B.11 orientation is enforced on assess_* but absent from the intervention and remedy path, and I completed a full interpretive remedy answer without ever routing through Bodha synthesis. assess_marriage/assess_career/assess_health all carry orientation_ok:true (the mandatory B.11 orientation pre-fetch). kala_upaya_get - which served a PACT promise-denial verdict, the single most interpretively-loaded output of the entire session - carries NO orientation_context and NO orientation_ok field at all. bodha_remedies_get likewise returns none. Q4 ('What remedy helps me now?') is squarely interpretive and not a depth:'retrieval' lookup exempt under the RS-4 carve-out, yet nothing in either tool's envelope required, performed, or flagged the missing Whole-Chart-Read routing, and I was never prompted to call bodha_bundle_get. Self-charged: my own Q4 tool selection omitted it.

**Reproduce.**

```
Q4. Call kala_upaya_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, domain='relationship', as_of_date='2026-08-15') and bodha_remedies_get(chart_id=same, limit=8); check for orientation_ok / orientation_context on either envelope (absent on both) and compare with assess_* where it is present and true.
```

**Evidence.** `pp2-audit/evidence/E2_q4_raw_kala_upaya.json | pp2-audit/evidence/E2_q4_remedy_now_trace.json`

**Mechanism.** The B.11 orientation pre-fetch is implemented per-handler on the assess_* family rather than as a cross-cutting gate on interpretive capabilities. Tools that emit verdicts of equal or greater interpretive weight (a promise-chain denial; a prioritised remedy prescription) bypass it silently. Because the obligation is invisible in the envelope of the tools that skip it, a consuming LLM has no signal that the Whole-Chart-Read step was never performed.

**Proposed remediation.** Apply the B.11 orientation pre-fetch to `kala_upaya_get` and `bodha_remedies_get` — the PACT promise-denial is the most interpretively loaded output in the estate and currently carries no `orientation_ok` field at all.

#### CL-22 Governance / registry drift and auditability

> *Class root mechanism and remediation lane stated in full at §3.2; CL-22 spans multiple tiers.*


##### F-81  ·  `TIER3-DOCUMENTATION`

**Claim.** Registry<->manifest reconciliation is structurally vacuous as literally specified: 00_ARCHITECTURE/CAPABILITY_MANIFEST.json's 115 catalog entries are ALL governance/documentation-artifact canonical_ids (e.g. LEL, MSR_v5_0, PROJECT_ARCHITECTURE, CGP_AUDIT_v1_0) -- a grep for any ga_*/bo_*/ka_*/ph_*/mi_*/bg_* id inside the manifest file returns zero matches. The live asset_registry DB table (data-layer writer catalog, >120 rows: ka_kshetra, bo_laksana, mi_pramana, ph_pramana, etc.) has no representation in CAPABILITY_MANIFEST.json at all, so a naive orphan comparison would flag 100% of asset_registry as 'orphaned' and vice versa. This is a namespace/scope mismatch, not evidence of registry drift within either catalog's own domain -- but it means CLAUDE.md SS C item 2's description of CAPABILITY_MANIFEST.json as 'the new single source of truth for the canonical-path + artifact catalog' cannot be read as covering the data-asset catalog, and no reconciliation mechanism between the two actually exists in the codebase today.

**Reproduce.**

```
python3 -c "import json; m=json.load(open('00_ARCHITECTURE/CAPABILITY_MANIFEST.json')); print(m['entry_count'])"  -- 115.  grep -o '"ga_[a-z_]*"\|"bo_[a-z_]*"\|"ka_[a-z_]*"\|"ph_[a-z_]*"\|"mi_[a-z_]*"\|"bg_[a-z_]*"' 00_ARCHITECTURE/CAPABILITY_MANIFEST.json | sort -u | wc -l  -- 0.  SELECT asset_id FROM asset_registry ORDER BY asset_id; -- returns the full data-layer catalog, disjoint from the manifest's canonical_ids.
```

**Evidence.** `evidence/capability_manifest_vs_asset_registry.json`

**Mechanism.** CAPABILITY_MANIFEST.json's generator (referenced in CLAUDE.md SS C item 2 as the Phase 1B cutover replacing FILE_REGISTRY + CANONICAL_ARTIFACTS) only enumerates markdown/doc artifacts under 00_ARCHITECTURE and sibling folders; it was never wired to enumerate asset_registry rows, so 'registry<->ontology reconciliation' as a literal cross-check has no implementation to audit against -- there is nothing currently drifting because the two catalogs were never unified in the first place.

**Proposed remediation.** Either extend `CAPABILITY_MANIFEST.json` to cover the `asset_registry` data-asset catalog, or amend CLAUDE.md §C-2's scope claim to what the manifest actually covers; a reconciliation mechanism must exist either way.

##### F-141  ·  `TIER3`

**Claim.** ka_kshetra's asset_throughput row for chart 482012f1 is internally self-contradictory and carries a hand-set completion signal: state='lit' while last_error is NON-EMPTY and reads 'orphan-watchdog: heartbeat went stale while a substep plan was in flight. 301 substep(s) committed and 8599775 data row(s) are present, but this route cannot prove the plan finished, so the asset was NOT promoted to lit. Re-run the build...'. Every other successfully-built asset for this chart carries last_error='' (verified across all 12 mi_* rows), so a non-empty last_error alongside state='lit' is anomalous, and the error text directly denies the state it sits next to. CURRENT_STATE_v1_0.md v6.60 (dated today, 2026-08-15) independently corroborates the reading: the R42 snapshot substep OOM'd on 1,839,618 provenance rows and 'asset_throughput.state=lit' was set as part of a manual local repair via cloud-sql-proxy, not earned through the orchestrator's own promotion predicate. Additionally the row's rows_written=11,069,325 disagrees with the 10,502,780 rows actually present across the 7 field tables for this chart (kala_field 8,599,775 + provenance 1,839,618 + windows 31,350 + salience 31,350 + null 250 + insights 431 + timeline_spec 6). This is the §N.8 defect class one level up from instance #4: the SATYA-DĪPA fix hardened the orchestrator's promotion predicate (F-102 re-verified it as still COMPLIANT), but an out-of-band manual UPDATE bypasses that predicate entirely and leaves no field distinguishing an earned 'lit' from a hand-set one.

**Reproduce.**

```
SQL: SELECT asset_id,state,rows_written,last_built_at,left(coalesce(last_error,''),240) FROM asset_throughput WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND asset_id='ka_kshetra';  compare against the same SELECT for asset_id LIKE 'mi_%' (all last_error='');  SQL row-count sum: kala_field + kala_field_provenance + kala_field_windows + kala_field_salience + kala_field_null + kala_insights + kala_timeline_spec WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'  => 10,502,780
```

**Evidence.** `pp2-audit/p4_prior8_reverification.json (reverifications[4] evidence (b)); 00_ARCHITECTURE/CURRENT_STATE_v1_0.md v6.60 changelog entry (RES-R42-1/2/3)`

**Mechanism.** DIAGNOSIS-INCOMPLETE on the exact write path. Confirmed at the data level: (i) state='lit' coexists with a last_error asserting non-promotion; (ii) no other asset for this chart carries a non-empty last_error while lit, so last_error is normally cleared on success and was not cleared here; (iii) CURRENT_STATE v6.60 records the promotion as a manual local repair after an OOM, and names RES-R42-2 ('build_run.state=failed despite data fully integrated') as a known residual of the same event; (iv) rows_written overstates the actual present rows by 566,545. Not traced: whether the manual UPDATE simply omitted `last_error=''`, or whether the orphan-watchdog path writes last_error after a separate promotion writes state. IMPORTANT NON-CLAIM: the underlying field DATA is intact — the 7-table row-set is exactly the 10,502,780 rows F-77 independently recomputed field_content_hash over, and the stored hash kfh_3a8d00db6577713f58206afc329c613a is unchanged and is the value kala_now_get.freshness.field_hash currently serves. This finding is about the truthfulness of the build-state signal, not about data corruption. Defect class CL-22 / §N.8.

**Proposed remediation.** Clear `last_error` on promotion, add an explicit earned-vs-hand-set provenance field on `asset_throughput` so an out-of-band UPDATE cannot masquerade as an earned `lit`, and reconcile `rows_written` with the actual row count.

#### CL-23 Corpus / data-coverage gaps (honestly served, genuinely thin)

> **Root mechanism (class-level).** Not serving-layer defects — the tools query the right table and honestly null or disclose what is missing. The gap is in the corpus: only 16/67 (24%) mantra rows carry mantra_text and 9/67 (13%) carry mantra_sanskrit (F-23); and kala_gochara_windows currently holds NO rows at month/day resolution for the native chart in the tested ranges, so both tools purpose-built for near-term transit triggers return era-scale context only, correctly flagged via context_only_note per the PK-R-1 ruling (F-136).

> **Class remediation lane.** LANE-CORPUS: content/backfill work, tracked as data debt rather than code defects; keep the honest-disclosure behaviour unchanged.


##### F-23  ·  `TIER3`

**Claim.** ref_mantras_get correctly queries brahma_remedy_corpus and honestly returns null (not fabricated text) for missing fields, but the underlying corpus is sparse: only 16/67 (24%) of all remedy_type='mantra' rows have mantra_text populated, and only 9/67 (13%) have mantra_sanskrit populated -- most rows carry only prescription_text (contextual remedy guidance) with the actual mantra itself absent.

**Reproduce.**

```
mcp__marsys-jis-direct__ref_mantras_get({planet:'Saturn', limit:10}) then `SELECT count(*), count(mantra_text), count(mantra_sanskrit) FROM brahma_remedy_corpus WHERE remedy_type='mantra'`
```

**Evidence.** `evidence/ref_mantras_get__coverage_check.json`

**Mechanism.** Not a wiring bug -- the tool correctly queries brahma_remedy_corpus per platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:1825ff and honestly nulls missing fields (consistent with CLAUDE.md N.7 item 6). This is a genuine, quantified data-completeness gap in the underlying corpus, not a serving-layer defect.

**Proposed remediation.** LANE-CORPUS — backfill `mantra_text`/`mantra_sanskrit` in `brahma_remedy_corpus`; data debt, not a code defect, and the honest-null behaviour should be left exactly as it is.

##### F-54  ·  `TIER3`

**Claim.** kala_muhurta_get cannot serve muhurta candidates for the one genuine gochara marriage window this same journey surfaces (2027-11-11), due to a hard 90-day max query span plus panchanga_daily's rolling ~12-month population horizon. A user told 'your marriage window is around 2027-11-11' cannot get a same-journey muhurta recommendation for it today.

**Reproduce.**

```
kala_muhurta_get(chart_id='482012f1-710e-4a25-994a-93821f5871aa', activity_type='marriage', start_date='2027-10-01', end_date='2027-12-15') -> window_count=0, empty_reason cites panchanga_daily populated window 2026-07-09..2027-07-09; wider span -> 422 'maximum is 90 days'
```

**Evidence.** `evidence/kala_muhurta_get__native_marriage.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE on exact source file:line for the 90-day cap / rolling horizon; confirmed live via verbatim error/empty_reason text.

**Proposed remediation.** Raise or window `kala_muhurta_get`'s 90-day cap and extend `panchanga_daily`'s horizon so a gochara window this same journey surfaces can receive a same-journey muhurta recommendation.

---

### §3.4 — TIER 4 — POLISH & LATENT  (9 findings)

*Low blast radius today: cosmetic, dormant, or a landmine that has not been wired in yet.*

#### CL-01 Registered-but-unreachable capability (dispatch/registration wiring gap)

> *Class root mechanism and remediation lane stated in full at §3.1; CL-01 spans multiple tiers.*


##### F-11  ·  `TIER4`

**Claim.** CONFIRMED (was UNCONFIRMED LEAD): query_kala_paddhati_profile is unreachable from kala_ritual_get's Mode-2 sky_pattern_spec path -- live call returns 'query_kala_paddhati_profile returned status 400' (same whitelist-wiring defect class as F-02: absent from MCP_TO_RETRIEVAL_TOOL). However, the surface degrades HONESTLY, not silently: coverage[] carries {concept:'paddhati_profile', state:'honest_empty', reason:'query_kala_paddhati_profile returned status 400'} and the nested paddhati block carries {available:false, unavailable_reason:'...', census_statement: '...an unreachable profile is reported as unreachable, never restated as not on record.'}. Net: the underlying primitive is broken, but the caller-facing contract correctly reports the gap per CLAUDE.md SS N.7 item 6 (honest null over fabricated value) -- not a correctness/honesty defect, just an unfixed wiring gap feeding an honest degrade path.

**Reproduce.**

```
mcp__marsys-jis-direct__kala_ritual_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa', sky_pattern_spec:{all:[{factor_type:'vara',factor_id:6}], horizon:{months:3}}}) -- inspect response.opportunities.paddhati.available / unavailable_reason and coverage[] entry for concept='paddhati_profile'
```

**Evidence.** `evidence/kala_ritual_get__native_mode2_sky_pattern_spec.json`

**Mechanism.** Live-confirmed: query_kala_paddhati_profile returns HTTP 400 (absent from MCP_TO_RETRIEVAL_TOOL, tool_name_bridge.ts:508+ -- same class as F-02). The remaining actionable work is fixing the primitive's routing, not the serving-layer honesty around it, which is already correct.

**Proposed remediation.** Fix `query_kala_paddhati_profile`'s routing (same whitelist class as F-02); the surrounding honest-degrade path is already correct per §N.7 item 6 and must be preserved unchanged.

#### CL-04 Unreconciled domain/enum vocabularies + unvalidated input (false honest-zero)

> *Class root mechanism and remediation lane stated in full at §3.2; CL-04 spans multiple tiers.*


##### F-58  ·  `TIER4`

**Claim.** 'moksha' is a fully functional judgment_query domain (bhava 12, D20, verdict_grade=convergent_strong) but does not appear anywhere in the CANONICAL_DOMAINS 13-domain vocabulary that is the actual basis for the system's '13 life domains' claim -- the inverse gap to F-55 (there, canonical domains judgment_query can't serve; here, a working domain absent from the canonical list).

**Reproduce.**

```
judgment_query(chart_id='482012f1-710e-4a25-994a-93821f5871aa', domain='moksha')
```

**Evidence.** `evidence/judgment_query__moksha.json`

**Mechanism.** platform/src/lib/domain_vocabulary.ts CANONICAL_DOMAINS array (13 entries) vs. register_d9_judgment.ts SHASTRA_MAP (10 concepts) -- the two domain vocabularies were never reconciled 1:1. Not a functional bug, a documentation/consistency gap.

**Proposed remediation.** Add `'moksha'` to `CANONICAL_DOMAINS`, or state explicitly why the system's '13 domains' claim excludes a domain that demonstrably works.

#### CL-07 Nodal (Rahu/Ketu) special-aspect truncation to the universal 7th

> *Class root mechanism and remediation lane stated in full at §3.1; CL-07 spans multiple tiers.*


##### F-65  ·  `low`

**Claim.** A THIRD independent hardcoded Mars/Jupiter/Saturn-only special-aspect computation exists in ga_writers/ga_vargas_writer.py's _compute_aspect_matrix() (feeds the declared 'varga_aspect_matrix' fact_category), with the same silent-7th-only-fallback pattern for every graha not in its local `special` dict -- i.e. it would truncate Rahu/Ketu to 7th-only exactly like primitives.py's SPECIAL_DRISHTI_DEG, if it ever ran. It does not currently run: grep across the whole repository finds no caller of _compute_aspect_matrix() anywhere (only its own def), and an empirical DB query confirms chart_facts has ZERO rows for fact_category='varga_aspect_matrix' on the native chart -- 'varga_aspect_matrix' is declared in TWO_PASS_CATEGORIES (line 299) but the function that would populate it is dead code. This is not a live defect (no served tool output is affected today), but it is a real latent landmine: if this function is ever wired into the writer's dispatch table (e.g. to actually populate the declared-but-empty category), it will silently reproduce the F-20/F-52 defect class for the per-varga aspect matrix.

**Reproduce.**

```
grep -rn '_compute_aspect_matrix\b' --include='*.py' platform/python-sidecar/ && echo '--- confirms only the def, no caller ---'
```

**Evidence.** `pp2-audit/evidence/postgres_query__varga_aspect_matrix_deadcode__482012f1.json`

**Mechanism.** platform/python-sidecar/ga_writers/ga_vargas_writer.py:573-595 (_compute_aspect_matrix, local `special` dict keys only Mars/Jupiter/Saturn, silent fallback to universal 7th-only for every other body via `special.get(body, [])`) -- DEAD CODE, unreachable: no caller found repo-wide, and chart_facts has 0 rows for fact_category='varga_aspect_matrix' (target category declared at line 299, never populated)

**Proposed remediation.** Delete the dead `special` dict in `_compute_aspect_matrix()` (or import the shared nodal constant) now, before anything wires it in and reproduces the F-20 class for the per-varga aspect matrix.

#### CL-08 Tier-honesty leaks (non-calibrated data served at full numeric precision / inflated labels)

> *Class root mechanism and remediation lane stated in full at §3.1; CL-08 spans multiple tiers.*


##### F-126  ·  `low`

**Claim.** mimamsa_lel_query returns epistemics.confidence_band='high' on a zero-result query. Querying the life-event log for 'marriage relationship spouse partner wedding' returned events:[], count:0, total_matching:0 - while the envelope reported epistemics:{surgical:true, confidence_band:'high', falsifier:null}. The LEL is demonstrably populated for this chart (kala_ahead_get's period_echo surfaced two logged rows, a 1993 painting award and a congenital speech-pattern correction), so the empty result is a genuine absence rather than an empty corpus - but a 'high confidence' stamp on a null retrieval invites a consumer to read the absence as an established negative fact ('he is not married') rather than as unrecorded. In a marriage-timing question that distinction changes the entire answer.

**Reproduce.**

```
Q1. Call mimamsa_lel_query(chart_id=482012f1-710e-4a25-994a-93821f5871aa, query='marriage relationship spouse partner wedding', limit=15) and read .object.epistemics.confidence_band alongside .result.results[0].content count=0.
```

**Evidence.** `pp2-audit/evidence/E2_q1_marriage_timing_trace.json`

**Mechanism.** confidence_band appears to describe the retrieval mechanism's determinism (surgical:true - the query ran cleanly) rather than the evidential weight of its result. Two different meanings of 'confidence' share one field, and the response carries no empty_reason distinguishing 'no such event is recorded' from 'no such event occurred' - the empty_reason discipline that CLAUDE.md N.6 item 4 requires of a density_contract surface.

**Proposed remediation.** Derive `confidence_band` from evidential weight rather than retrieval determinism, and never stamp `'high'` on a zero-result retrieval where the absence could be read as an established negative.

#### CL-11 Non-actionable or dead recovery pointers (recover_via / drill_pointers / tri_plane)

> *Class root mechanism and remediation lane stated in full at §3.2; CL-11 spans multiple tiers.*


##### F-09  ·  `TIER4`

**Claim.** The shared response-budget trim helper emits a generic recover_via.hint ('call <tool> again with a narrower filter/date_range, or a smaller top_k/limit') on phala_outlook_get and plan_retrieval even though neither tool's actual parameter schema has a date_range/top_k/limit field -- the recovery advice is not actionable via the named instrument.

**Reproduce.**

```
mcp__marsys-jis-direct__phala_outlook_get({chart_id: '482012f1-710e-4a25-994a-93821f5871aa'}) -- inspect trim_report[].recover_via.hint; same pattern in mcp__marsys-jis-direct__plan_retrieval({chart_id: '482012f1-710e-4a25-994a-93821f5871aa', question: 'What does my career look like over the next year?'})
```

**Evidence.** `evidence/phala_outlook_get__native_default.json`

**Mechanism.** platform/src/lib/response_budget.ts:527 -- a generic, tool-schema-unaware boilerplate hint string emitted by the shared trim/budget helper regardless of what parameters the target tool actually declares.

**Proposed remediation.** Derive `recover_via` hints from the target tool's real JSONSchema instead of a boilerplate string naming parameters the target does not declare.

#### CL-12 Narration-fidelity defects (prose diverges from the rows it sits on)

> *Class root mechanism and remediation lane stated in full at §3.2; CL-12 spans multiple tiers.*


##### F-135  ·  `low`

**Claim.** synth_chart_brief_get's ranked_themes.weaknesses array is empty at depth=complete, even though the same response's open_questions list several genuinely low-grade domains that read as natural 'weaknesses' content for a whole-chart read: Marriage (conditional, 4.5/10), Romantic Relationship Start (conditional, 3.9/10), Property Acquisition (conditional, 3.8/10), Acute Illness (conditional, 4.7/10), Surgery (conditional, 4.7/10). None of these are promoted into the weaknesses bucket, so a caller reading only ranked_themes (the structured summary slot) sees a strengths list and an open_questions list but no distinctly-labeled weaknesses, even though the underlying grades clearly support one.

**Reproduce.**

```
Call mcp__marsys-jis-direct__synth_chart_brief_get with chart_id=482012f1-710e-4a25-994a-93821f5871aa, depth=complete; inspect content.ranked_themes.weaknesses vs content.ranked_themes.open_questions
```

**Evidence.** `pp2-audit/evidence/E3_read1_general_trace.json (step 2)`

**Mechanism.** ranked_themes.weaknesses population logic in the mi_darshana maha-brief writer does not promote any conditional/low-grade verdict into the weaknesses bucket for this chart; only open_questions (grade-agnostic 'conditional' activation_state) captures them, diluting the strengths/weaknesses contrast an acharya-grade summary should foreground.

**Proposed remediation.** Promote the sub-5/10 conditional grades into `ranked_themes.weaknesses`, or state in-band why the bucket is empty beside five qualifying domains.

#### CL-13 Missing disclosure of a known partial or mixed result

> *Class root mechanism and remediation lane stated in full at §3.2; CL-13 spans multiple tiers.*


##### F-35  ·  `TIER4`

**Claim.** mimamsa_insight_get, on a zero-history chart, mixes chart-specific structural-tier insights (evidence_grade='structural') with at least one cross-chart manifestation_grammar insight carrying evidence_grade='empirical' and a real last_calibrated_at timestamp, without an inline marker disambiguating that the 'empirical' grade reflects population-level cross-chart mining rather than this chart's own outcome history.

**Reproduce.**

```
MCP mimamsa_insight_get {chart_id:'1c826d5a-41cb-4450-b4dc-59d440e5f75a', domain:'career'} -- inspect insight_units[] for insight_id='gram_career_ch_career_verbal_2' (evidence_grade='empirical') alongside sibling verdict_object units (evidence_grade='structural')
```

**Evidence.** `evidence/journey_mimamsa_insight_get__zero_career.json`

**Mechanism.** DIAGNOSIS-INCOMPLETE -- plausible correct-by-design (documented cross-chart insight_type), but per-unit JSON lacks an explicit population-level marker, so a caller filtering on evidence_grade alone could momentarily conflate it with the chart's own calibration. Exact source file for insight-unit assembly not located in this pass.

**Proposed remediation.** Mark population-mined rows with an explicit cross-chart provenance marker beside this chart's own structural rows, so `evidence_grade='empirical'` cannot be read as this native's outcome history.

##### F-134  ·  `low`

**Claim.** judgment_query(domain=wealth)'s gochara_sweep reports upcoming_window_count=3 with window_range starting 2026-08-15 ('now'), but its top-ranked window (event_class=major_gain, valence=gain) has peak_date=2025-04-27 — more than a year in the PAST relative to the call's own now_context_date. This already-peaked window is presented inside the 'upcoming' forward-sweep set alongside two genuinely future loss windows (peak 2030-08-14) with no flag distinguishing past-peaked activity from forward activity.

**Reproduce.**

```
Call mcp__marsys-jis-direct__judgment_query with chart_id=482012f1-710e-4a25-994a-93821f5871aa, domain=wealth, response_format=v3; inspect content.gochara_sweep.top_windows[0]
```

**Evidence.** `pp2-audit/evidence/E3_read2_career_wealth_trace.json (step 4)`

**Mechanism.** gochara_sweep.top_windows selection (kala_gochara_windows overlap query) includes any window overlapping the sweep's window_range even when peak_date falls before 'now'; no is_past_peak / already_occurred flag distinguishes it from a genuinely upcoming peak.

**Proposed remediation.** Flag already-peaked windows inside an 'upcoming' forward sweep, or exclude them from the forward set entirely.

#### CL-23 Corpus / data-coverage gaps (honestly served, genuinely thin)

> *Class root mechanism and remediation lane stated in full at §3.3; CL-23 spans multiple tiers.*


##### F-136  ·  `informational`

**Claim.** For chart 482012f1, both gochara_activation_get (as-of today, 2026-08-15) and gochara_forecast_get (career domain, next 12 months) return rows that are ALL era-scale context (resolution_disclosure.is_timing_window=false for every row in both calls) — meaning the two tools purpose-built for 'is this configuration active right now' and 'what career transit windows are coming' currently have ZERO genuine day/month-resolution rows to serve for this chart. This is honestly disclosed each time via context_only_note (compliant with the PK-R-1 native ruling — not a fabrication defect), but it means a timing-focused whole-chart read gets no actionable near-term transit-trigger content from either dedicated gochara tool; all genuinely current-dated texture in this read came from kala_now_get's kota_chakra/moorti_nirnaya joins instead.

**Reproduce.**

```
Call mcp__marsys-jis-direct__gochara_activation_get and mcp__marsys-jis-direct__gochara_forecast_get (date_range 2026-08-15..2027-08-15, domain=career) with chart_id=482012f1-710e-4a25-994a-93821f5871aa; inspect windows[].resolution_disclosure.is_timing_window across both
```

**Evidence.** `pp2-audit/evidence/E3_read3_timing_trace.json (step 2); pp2-audit/evidence/E3_read2_career_wealth_trace.json (step 6)`

**Mechanism.** kala_gochara_windows for this chart currently has no rows stamped resolution in {'month','day'} within the tested ranges — a data-coverage gap in the D-5 gochara sweep, not a serving-layer honesty defect (both tools disclose the gap correctly per PK-R-1).

**Proposed remediation.** LANE-CORPUS — populate month/day-resolution gochara rows for this chart; the `context_only_note` disclosure is correct under PK-R-1 and must be left unchanged.

---

## APPENDIX A — CONFIRMED CLEAN (bucket `CL-00`, 27 entries)

These 27 findings assert **no defect**. They are the audit's positive controls and verified
passes, recorded for completeness and — per P4's own disposition — **to be preserved as regression
anchors, not remediated**. Their existence is what makes the 114 defect findings legible: an audit
that reports only failures cannot distinguish "this was checked and is correct" from "this was
never checked."

> **Class note.** Findings recorded for audit completeness that assert no defect: eight data-integrity PASSes (kala_field decade-seam contiguity, the 25x10 null grid, the independently recomputed 10,502,780-row field_content_hash for both charts — re-confirmed by row count this pass, R17 identity adoption, FK/orphan integrity, natural-key uniqueness, verification_pass_status vocabulary, migration-order monotonicity, full-horizon coverage), nine §N.8 earned-signal COMPLIANT verdicts including the mutation-tested fact-category-pin-lint guard, two positive-contrast records (mi_adhilepa's honest 'not_assessed'; the v3 register mechanism), the retrodiction and dark-corpus baseline measurements, one genuine depth demonstration (kala_ahead_get's period_echo), and two informational observations (session active_chart_id labelling; sensitive-degree profile scoping being UX curation, not an access boundary). F-137 is dual-listed with CL-10 as its positive contrast; F-82's one exception is F-79 in CL-22.

| Finding | Label | What it establishes |
|---|---|---|
| **F-32** | `TIER4` | POSITIVE/NON-DEFECT finding, logged for audit completeness: judgment_query(domain='health') and assess_health(reading_depth='deep_dive') independently compute matching gochara_sweep figures for the same chart (native: upcoming_window_count=17, matching peak dates; zero: upcoming_window_count=8, m… |
| **F-72** | `TIER4` | Baseline retrodiction measurement (informational, per R13 -- reported as-is, not tuned): mechanism_retrodiction_get on the native chart's LEL (sealed pre-2020 split) confirms 8 dasha-lord/house-activation firings across 7 houses/domains (career x2, health, education/family, wealth/finance, spirit… |
| **F-75** | `VERIFIED-PASS` | Kala field decade-seam contiguity, native chart: RE-VERIFIED PASS. Zero segment-to-segment gaps exist anywhere in kala_field for the native chart (482012f1-710e-4a25-994a-93821f5871aa, field_snapshot_id kfs_e23ba1abdf1c6fd3a1cc5c08c7538aeb) across all 25 event classes over the full [0, 36525]-day… |
| **F-76** | `VERIFIED-PASS` | kala_field_null 25x10 grid invariant: EXACT MATCH for the native chart. 250 rows = 25 event classes x 10 duration buckets (1,3,7,15,30,60,90,180,365,730 days), with no missing or extra cells. The native chart's kala_field_snapshots.event_classes array (25 entries) matches the 25 classes actually… |
| **F-77** | `VERIFIED-PASS` | kala_field_snapshots.field_content_hash independently recomputed and CONFIRMED MATCHING for BOTH charts. Native chart (482012f1-710e-4a25-994a-93821f5871aa, field_snapshot_id kfs_e23ba1abdf1c6fd3a1cc5c08c7538aeb): recomputed kfh_3a8d00db6577713f58206afc329c613a == stored kfh_3a8d00db6577713f58206… |
| **F-80** | `VERIFIED-PASS` | Identity adoption (R17) check: PASS. No legacy_id / old_chart_id / identity_map / id_crosswalk column or table exists anywhere in the live schema (115 tables/columns scanned via information_schema), and no source file under platform/src, platform-mcp/src, or platform/python-sidecar references suc… |
| **F-82** | `VERIFIED-PASS-WITH-ONE-EXCEPTION` | _migrations_applied (430 rows) vs on-disk migration files under platform/migrations + platform/supabase/migrations (423 files): 7 filenames present in the DB with no matching file in those two directories; 0 files on disk with no matching applied row. Of the 7, 6 are explained by legitimate retai… |
| **F-83** | `VERIFIED-PASS` | FK/orphan referential integrity: PASS across 5 sampled tables spanning L1 (chart_facts), L3 (kala_field), L2 (bodha_msr_signals), L4 (phala_anchors), L5 (mimamsa_calibration) -- zero distinct chart_id values in any of these tables lack a matching row in charts. |
| **F-84** | `VERIFIED-PASS` | No duplicate natural-key rows found in kala_field (event_class, segment_index) for the native chart, and no duplicate (chart_id, fact_id, build_id) rows in chart_facts for the native chart. |
| **F-85** | `VERIFIED-PASS` | chart_facts.verification_pass_status enum/vocabulary check: PASS. All 10 distinct live values (classical_match, computed_extension, divergent_flagged, documented_approximation, floored, not_defined_for_nodes, pending_w3_verification, single, single_pass, two_pass_verified) are declared members of… |
| **F-86** | `VERIFIED-PASS` | _migrations_applied.applied_at is monotonically non-decreasing when the table is ordered by its own id column (0 out-of-order rows across all 430 applied migrations) -- migration application timestamps are internally consistent with application order. |
| **F-87** | `VERIFIED-PASS` | Coverage range [0, 36525] for day-offset-indexed kala_field, BOTH charts, no truncation: native chart's 25 event classes and second chart's 6 built event classes each independently span min(t_start)=0 to max(t_end)=36525 exactly. |
| **F-88** | `TIER4` | The MCP session's implicit `active_chart_id` (as reported by session_recall and used only as a human-facing convenience pointer) defaults to the second/zero-history chart (1c826d5a-41cb-4450-b4dc-59d440e5f75a, 'Abhinandan Mohanty'), not the native chart (482012f1-...). This is a real, live, repro… |
| **F-91** | `TIER4` | MCP tool-catalog profile scoping (full/compact/consult, per platform/src/generated/projections/mcp_surface_profiles.generated.json) excludes get_sensitive_degrees from the 'compact' (20-tool) and 'consult' (8-tool) profiles, but 'compact' still includes chart_facts_query, which serves byte-identi… |
| **F-96** | `informational` | fact-category-pin-lint CI guard mutation-tested: catches the exact D1 defect class it claims to enforce Verdict: COMPLIANT — the guard is a real, working detector, not a null check. It genuinely distinguishes the injected violation from the 29 pre-existing allowlisted violations (correctly does n… |
| **F-97** | `informational` | ga_yoga_firings.bhanga_active has a real per-rule detector (neecha-bhanga grounds_jsonb ledger) (flag `bhanga_active / bhanga_rule_fired / grounds_jsonb` served by `ganita_yoga_firings_get`, subsystem: L1 Ganita) Verdict: COMPLIANT. grounds_jsonb carries a per-rule, per-planet ledger (checked/fir… |
| **F-98** | `informational` | bo_pramana_mapa trap1/trap2 counters — confirmed §N.8 instance #2 already fixed with real detectors (flag `trap1_authority_inversion_count / trap2_narration_leak_count` served by `bodha_quality_get`, subsystem: L2 Bodha) Verdict: COMPLIANT. Code at bo_pramana_mapa.py:682-688 documents the fix exp… |
| **F-99** | `informational` | kala_sarpa_reconciliation.agrees is a genuine cross-source equality check, not a hardcoded true (flag `kala_sarpa_reconciliation.agrees` served by `ganita_structural_get (facet=dosha_fires, v3)`, subsystem: L1 Ganita) Verdict: COMPLIANT. Computed as a real equality check (perVargaFires === effect… |
| **F-100** | `informational` | judgment_query receipt.timing_anchored is content-checked, not call-succeeded-checked (flag `receipt.timing_anchored` served by `judgment_query (v3)`, subsystem: Synthesis/judgment layer (built on L1 dasha + L3 kala facts)) Verdict: COMPLIANT. timingAnchored = currentRows.length > 0 \|\| hasWindowR… |
| **F-101** | `informational` | judgment_query receipt.varga_confirmed genuinely gates on divisional-row presence (flag `receipt.varga_confirmed` served by `judgment_query (v3)`, subsystem: Synthesis/judgment layer) Verdict: COMPLIANT. vargaConfirmed defaults false and is set true only when a real divisional-chart query returns… |
| **F-102** | `informational` | Orchestrator asset_throughput.state='lit' no-op-completion guard (confirmed §N.8 instance #4) verified still fixed (flag `asset_throughput.state = 'lit'` served by `orchestrator build-completion promotion`, subsystem: Orchestrator (build system)) Verdict: COMPLIANT. For writers with has_substeps=… |
| **F-103** | `informational` | phala_predictive_anchors_get posterior_provenance.base_rate_matches_uniform_fallback_value is a real (if simple) equality check (flag `posterior_provenance.base_rate_matches_uniform_fallback_value` served by `phala_predictive_anchors_get`, subsystem: L4 Phala) Verdict: COMPLIANT. Computed as lift… |
| **F-105** | `informational` | Contrast case — mi_adhilepa's leakage tier correctly uses the honest 'not_assessed' null value (flag `leakage (calibration-overlay leakage_status)` served by `mimamsa_calibration_get / mi_adhilepa overlay tables`, subsystem: L5 Mimamsa (mi_adhilepa calibration-overlay writer)) Verdict: COMPLIANT.… |
| **F-106** | `informational` | bodha_quality_get defect_001 status is re-derived live via real SQL on every call, not a stored/stale value (flag `defect_001.status / defect_001_alert` served by `bodha_quality_get`, subsystem: L2 Bodha (quality scorecard freshness contract)) Verdict: COMPLIANT. deriveDefect001Note() runs a live… |
| **F-109** | `informational` | SUMMARY — 21-question wealth-domain dark-corpus re-run (G15 gate): 19/21 questions (90.48%) graded qualitatively BRIGHT under this run's rubric; 2/21 (DC-W-16, DC-W-21) graded DARK, both from well-cited answers silently evading the specific expert technique named in the question rather than from… |
| **F-137** | `informational` | Contrast (informational) — graha_portrait and judgment_query's v3 response_format demonstrate the system CAN avoid raw jargon leaking to the end user when the serving code path is built for it: both self-gloss internal tokens via a 'register' array (e.g. token='parivartana' -> label='Parivartana… |
| **F-138** | `informational` | Non-generic depth (informational, positive) — kala_ahead_get's period_echo mechanism cross-references the CURRENTLY ACTIVE Saturn Antardasha (2024-12-08 to 2027-08-18) against its own prior occurrence in the native's lifetime (Saturn AD 1991-08-18 to 1994-08-21) using genuine Life-Event-Log-corro… |

---

## §4 — "IS IT FLAWLESS?"

**The three verdicts.**
- **flawless** — no defect found, and the coverage is sufficient to mean it.
- **graded-and-disclosed** — real gaps exist, and the system *surfaces them itself*: honest nulls,
  coverage blocks, `empty_reason`s, degrade flags. Not perfect; honest.
- **needs-next-wave** — the dimension cannot yet be called either of the above, **either** because
  the evidence is insufficient **or** because the defects found are *silent* — wrong or missing
  answers that the system does not disclose, which is the failure mode this project's own doctrine
  (§N.6/§N.7/§N.8) exists to prevent. This extended reading of the label is stated explicitly here
  rather than smuggled in: a silent defect and an unmeasured axis both mean the same thing
  operationally — another wave is required before a verdict can be earned.

| Dim | Verdict | Justification |
|---|---|---|
| **A** Astrological correctness | **needs-next-wave** | The defects found are silent, not disclosed: the R24 nodal truncation is actively suppressing Ketu's 5th onto natal Venus and Rahu's 9th onto the natal 7th from *this chart's own marriage windows today* with no flag anywhere (**F-52**, **F-20**); `moolatrikona` is never emitted chart-wide, under-scoring Sthana Bala by construction (**F-62**); and two Nabhasa yogas fire on a chart that categorically cannot form them (**F-66**). Eight of ten re-derived yogas were correct — the dimension is not broken, it is **unevenly** correct, which is exactly the state a next wave must resolve. |
| **B** Data completeness | **graded-and-disclosed** | Nine verified passes including an independently recomputed 10,502,780-row content hash on both charts (**F-77**), zero seam gaps (**F-75**), exact null grid (**F-76**), clean FK/natural-key/vocabulary/migration-order integrity (**F-83**–**F-86**). The two defects are auditability, not correctness, and one of them (**F-78**) is *already honestly recorded* in `skipped_classes` — the disclosure is present, only the column naming is ambiguous. **F-79** (unrecoverable migration SQL) is the one genuine unremediated gap. |
| **C** Serving / MCP | **needs-next-wave** | 40 of 125 tools are GAP; four are 100% unreachable for any argument (**F-02**, **F-07**); and all four `assess_*` tools — the flagship domain surfaces — are **undeliverable to a normal MCP client at 3.5×–17.4× their own echoed budget** (**F-56**, **F-111**). Some of this is honestly flagged (`budget_exceeded_after_trim` fires), but a response that self-reports over-budget *and ships anyway* is a disclosure without an action, and the four unreachable tools disclose nothing to a caller reading the tool list. |
| **D** Architecture & governance | **graded-and-disclosed** | The guards are real and were proven so by mutation, not assertion: `fact-category-pin-lint` broke, failed CI at the exact injected line, and reverted green (**F-96**); FM-23/25/26 carry RED/GREEN artifacts; the SATYA-DĪPA orchestrator predicate is confirmed still fixed (**F-102**); nine of ten honesty flags have a genuine detector behind them, with an honest-null contrast case already shipping (**F-105**, **F-106**). The two validators fail on a clean tree **by design against a known baseline** (**F-94**, **F-95**) — the disclosure exists; what is missing is enumeration, so one fresh GA.1-class defect currently hides inside an accepted 216-finding residual. One real §N.8 violation (**F-104**). |
| **E** Experience & depth | **needs-next-wave** | **F-110** alone forces this: the same server, same chart, same domain, same shared fact_ids, opposite verdicts, and *no reconciliation field anywhere* — the denial is not disclosed to the surface that omits it. Add **F-113** (the domain-specialised tool misses the chart's exalted 7th-house Saturn that a generic tool surfaced in ~6KB), **F-114** (a ten-row salience plateau sharing 6 of 10 signals across two different domains), and **F-116** (a remedy preamble contradicting a FORENSIC birth anchor). The bright% is on record (**F-109**) but establishes a *new* baseline rather than a comparison, and the PRATINIDHI grades the plan specifies are not on record. |
| **F** Residual consolidation | **graded-and-disclosed** | Complete and unusually honest: 42 residuals graded GAP/BY-DESIGN-OPEN with owner lanes, **including two deliberate SPLIT grades where the waiting is by design but the blockers preventing the wait from ever ending are not** — precisely the distinction a less careful register would collapse. All eight prior findings re-verified from scratch (§6.1). |
| **G** Security & isolation | **graded-and-disclosed** | The highest-stakes question — can chart A's data reach a caller holding chart B's id — was tested and the system **failed closed**, correctly, every time (**F-88**). The bundle's majority-failure degrades honestly (`b11_floor_passed:false`, named `sub_errors`) rather than laundering into a false-complete envelope (**F-30**). Two real leaks are error-hygiene, not credential: internal microservice routes and raw driver text (**F-89**, **F-90**). The caveats are honest ones: **F-38** is a genuinely silent boundary crossing, and no explicit secrets sweep is on record. |
| **H** Determinism & concurrency | **needs-next-wave** | Two findings total, and one of them falsifies the dimension's core claim: byte-identical repeat calls returned different evidence sets ~2.3s apart, with the disclosure text *changing to match* (**F-92**) — the response is self-consistent about a fact that is not stable. Pagination is not a stable pointer either (**F-60**). And two named sub-axes — concurrent-call session-memory integrity, `as_of` backdating reproducibility — have **no evidence at all**. This is the thinnest dimension in the audit. |
| **I** Contract conformance | **needs-next-wave** | Seven of sixteen tools GAP, and the defect shape is specifically the one §N.6 names: counts computed before the trimmer and never re-derived (**F-45**, five independent tools), a `trim_report` that can *trim away its own honesty* and then point at a non-existent recovery instrument (**F-44**), and an inconsistent budget-echo contract (**F-46**). Separately, the dimension's own headline axis — "every response validated against the tool's DECLARED schema" — **was not performed mechanically**, so conformance is graded on the budget/density axis only. |
| **J** Regression & edge | **graded-and-disclosed** | ~29 scenarios; the large majority PASS *with honest degrades* rather than by luck — pre-birth on `kala_now_get`, fully-beyond-horizon gochara, `varsha_year=200`, six malformed-arg rejections, two clean unknown-domain honest-empties, and a leap-day battery across four tools with a dasha boundary landing exactly on 2024-02-29. The four GAPs are each a **missing disclosure on a correct-enough computation** (**F-33**, **F-34**, **F-38**, **F-42**), which is the graded-and-disclosed failure mode rather than the silent one. Golden-fixture comparison was not run. |

### §4.1 — The system as a whole

**Verdict: NOT FLAWLESS — and the honesty discipline itself is intact.**

Both halves of that sentence are load-bearing, and neither is a hedge.

**Not flawless, concretely.** 114 real defects; 25 at TIER 1. Four tools cannot be called at all.
All four flagship `assess_*` tools cannot be delivered to a normal client. The system's own
promise-denial verdict and its own marriage-timing projection contradict each other on shared
evidence with no reconciliation, and the tool a consuming LLM will naturally reach for is the one
that omits the denial (**F-110**). A classical doctrine the native has personally ratified (R24) is
violated in three of four aspect tables and is measurably distorting this chart's own marriage
timing today (**F-52**). No prediction anywhere in the system has ever been resolved to a terminal
verdict, and the read tool that would let anyone review the open ones has been crashing for the
entire period (**F-01**, prior-8 #7). This instrument should not currently be described as
acharya-grade end-to-end; it is acharya-grade in parts, with silent failures in others.

**The honesty discipline is intact, concretely — and this is not a consolation prize.** The
machinery this project built to keep itself honest was tested adversarially and it *worked*:
- A guard was **broken on purpose** and it failed CI at the exact injected line, then went green on
  revert, and it correctly distinguished the injection from 29 pre-existing allowlisted violations
  (**F-96**).
- Nine of ten status flags surveyed under §N.8 have a **real detector** behind them, including one
  that re-derives itself with live SQL on every single call specifically so it cannot go stale
  (**F-106**), and two that check *content* rather than *call-succeeded* (**F-100**, **F-101**).
- The codebase already contains, and ships, the correct pattern for nearly every defect class the
  audit found: the honest `'not_assessed'` tier (**F-105**), the self-glossing `register` /
  `reading_contract` envelope (**F-137**), the `hardFloor` mechanism, the `resolution_disclosure`
  contract, `context_only_note` under PK-R-1 (**F-136**). **Almost nothing here needs to be
  invented. It needs to be propagated** — which is why P4's meta-pattern (the right fix applied to
  one sibling site out of many) is the most actionable single result in this report.
- The B.11 floor tool, when majority-failed, says so — `b11_floor_passed:false` with the failing
  subsystems named, rather than a complete-looking envelope (**F-30**).
- And this audit's **own gate refused to pass** (§5.3), the prior audit's fabricated finding was
  caught by fresh measurement rather than inherited (§6.1), and the desk corrected its own misread
  in public (§6.4).

The honest synthesis is therefore not "it's broken" and not "it's fine". It is: **the discipline is
real and unevenly installed.** Where a layer was built to carry the honesty contract, it carries it
— often beautifully. Where a sibling surface was built beside it, the contract was not propagated,
and the resulting silence is indistinguishable, to a caller, from a considered answer. That is a
tractable problem with a known shape and a known fix, and it is the right problem for the next wave.

---

## §5 — COVERAGE ATTESTATION

### §5.1 — Tools

| Measure | Value | Source |
|---|---|---|
| Tools declared in the live catalog | **125** | `manifest.json.tool_count_declared`; catalog snapshot `catalog-1+t152+r653c2a1a98c8`, evidence `evidence/live_tools_list__p0_catalog.json` + `evidence/mcp_server_info__p0_catalog.json` |
| Tools carrying a verdict | **125 / 125 (100%)** | `manifest.json.tools` (125 entries) |
| — PASS | 82 | |
| — GAP | 40 | |
| — PARTIAL | 1 (`ref_mantras_get`) | |
| — NOT-APPLICABLE | 2 (`mimamsa_outcome_record`, `prashna_ask`) | Both are write/job-creating paths, excluded **with written justification** under the campaign's read-only-on-production directive; neither was invoked. |
| Raw evidence files captured | **495** | `pp2-audit/evidence/` |
| Findings recorded | **141** (114 defects + 27 CL-00 controls) | `manifest.json.findings` |

**The 125 figure is real, not assumed.** The inventory was built from a live `tools/list`
snapshot; the plan explicitly bans source-grep inventories (which return 29 names including a test
fixture), and the gate refuses an inventory under 100 tools.

### §5.2 — Phase completion

| Phase | Scope | Status |
|---|---|---|
| **P0 INVENTORY** | live catalog snapshot → `audit_gate.py init` | **COMPLETE** — snapshot committed at `9730d2890`. |
| **P1 SWEEP** | dimensions C + I + J across all 125 tools | **COMPLETE** — 125/125 verdicted; `dimension_reports[I]`, `[J-boundary]`, `[J-edge]`; 4 `journey_reports`; F-01…F-58. |
| **P2 DEPTH** | dimensions A + B + G + H | **COMPLETE** — Wave 1 (six parallel agents, F-59…F-91, commit `c0eee770c`) + Wave 2 (H, F-92–F-93, `3e601cf06`). |
| **P3 ADVERSARIAL** | D (guard mutation-testing) + E (dark corpus, consumability, depth reads) | **COMPLETE-WITH-ONE-GAP** — Wave 3 (`5298a6548`, F-94…F-106) and Wave 4 (`d7435b97d`, F-107…F-138) both ran in full. **Gap: no PRATINIDHI (opus-max) grading record** for tool selection / synthesis / citation fidelity / depth / honest-uncertainty exists in the evidence base; the consumability *run* happened, the specified *grades* did not land. **Second gap: the career 21-question dark-corpus set was not re-run** (wealth only, 21/21). |
| **P4 CONSOLIDATE** | dimension F + re-verification of all 8 prior findings | **COMPLETE** — Wave 5 (`6adc84e43`): 42-item residual register, 23 defect classes, 8/8 prior findings re-verified from scratch, F-139…F-141. |
| **P5 REPORT + GATE** | this document + `audit_gate.py verify` | **REPORT COMPLETE; GATE FAILS — see §5.3.** |
| **P6 PARĪKṢAKA** | independent re-run, 15% `reproduce_cmd` sample, refutation attempt on the top-3 findings | **PENDING — runs after this document.** |

### §5.3 — The gate: **FAILING**, and exactly why

The plan's binding rule (§1 of `PARIPURNA_2_AUDIT_PLAN_v2_0.md`) is that no terminal marker may be
posted until `audit_gate.py verify` exits 0 and its signed `AUDIT-COVERAGE-VERIFIED:` line is
pasted verbatim. **It does not exit 0.** Run at P5 against the committed manifest:

```
AUDIT-GATE: FAILED
187 blocking problem(s). The terminal marker MUST NOT be posted.
```

**There is therefore no signed coverage line to paste into this report, and this section does not
pretend otherwise.** The 187 decompose as follows, with an honest assessment of which are real
coverage defects and which are gate-parser artifacts:

| Count | Class | Assessment |
|---|---|---|
| **120** | Severity label outside the gate's closed vocabulary | **Real bookkeeping defect, low substance.** The gate accepts only `TIER1-CORRECTNESS`/`TIER2-HONESTY`/`TIER3-EXPERIENCE`/`TIER4-POLISH`; the waves used **fifteen** different labels (`TIER2`, `TIER2-QUALITY`, `TIER2-AUDITABILITY`, `TIER3`, `TIER3-CLARITY`, `TIER3-DOCUMENTATION`, `TIER4`, `critical`, `high`, `major`, `medium`, `low`, `informational`, `VERIFIED-PASS`, `VERIFIED-PASS-WITH-ONE-EXCEPTION`). Every finding *is* severity-graded; three vocabularies were used to do it. §3 normalises them explicitly and prints the original label beside each id. |
| **53** | "evidence file missing" | **51 are gate-parser artifacts, 2 are real.** The gate treats `evidence_file` as one literal path; 51 of these entries are multi-file strings (`a.json \| b.json`) or carry a locator annotation (`… (step 3)`, `… (reverifications[4])`). Re-checked by splitting and stripping annotations, **every referenced artifact exists on disk except two**: **F-94** (drift_detector run captured inline, raw output written to a scratchpad and never committed) and **F-141**'s second pointer (a governance-doc reference with a version suffix, `CURRENT_STATE_v1_0.md v6.60`, which exists as a file). |
| **10** | Dimension sign-off not recorded | **Real.** `dimension_signoff` is `null` for all ten letters. The dimensions were worked and are evidenced (§2), but **not one is formally signed off**. |
| **2** | Evidence "not valid JSON" | **Gate-parser artifacts.** `sql__bo_pratijna_unreachable.txt` is a SQL capture (`.txt`, correctly so), and `gochara_forecast_get__native_domain_marriage_empty.json` is a multi-document capture the gate's single-`json.load` cannot parse. Both files exist and are non-empty. |
| **2** | **F-95** has no `evidence_file` field at all | **Real, and the one genuine E-2/E-3 protocol violation in the corpus.** The `schema_validator.py` finding is fully reproducible from its `reproduce_cmd` and its numbers are quoted inline, but it ships no saved artifact. |

**Two further coverage facts, disclosed rather than omitted:**

1. **226 of the 495 evidence files are not referenced anywhere in `manifest.json`.** This is the
   *opposite* of the v1 fabrication signature (a claim pointing at evidence that does not exist):
   it is surplus capture — scenarios recorded under the E-1 "save every MCP call" rule that no
   finding or tool verdict ended up citing. It is not a defect, but it does mean the evidence base
   is larger than the manifest's own index of it, and a future pass should index them.
2. **28 of the 138 clustered findings (20%) carry `DIAGNOSIS-INCOMPLETE`** on their exact
   file:line, mechanism, or both (residual register). Under protocol E-6 this is the correct
   disposition — a stated symptom with an honest "cause not traced" beats v1's wrong-cause
   diagnoses — but it means one finding in five hands the next wave a symptom rather than a fix
   site.

### §5.4 — Dimension coverage: honest bottom line

**All ten dimension letters (A–J) have real coverage** — none is a blank. **None is formally signed
off.** The genuinely uncovered *sub-axes*, restated here so they cannot be lost in §2's prose:

- **A** — no recorded FORENSIC 7/7 re-verification on both charts; the "25-fact classical battery"
  is not evidenced as a 25-item battery (a 10-yoga re-derivation is).
- **B** — the G4/G9/G10 data proofs were not separately produced.
- **E** — no PRATINIDHI grading record; career dark-corpus set not re-run.
- **G** — no explicit secrets/credential sweep of responses and error paths.
- **H** — concurrent-call session-memory integrity and `as_of` backdating reproducibility have **no
  evidence at all** (the two largest true holes in the audit).
- **I** — schema-conformance validation was not performed mechanically.
- **J** — golden-fixture comparison against the Δ2 fixture estate was not run.

---

## §6 — AUDIT INTEGRITY

*This section holds the audit to the standard it demands of the instrument. It records what the
audit got wrong, what it nearly lost, and what it corrected in public.*

### §6.1 — The eight prior findings, re-adjudicated

All eight findings of the prior (v1, non-PARIPŪRṆA-2) audit were **reproduced from scratch**
against the live production MCP server and live production Postgres. No prior verdict was
inherited; prior text was consulted only *after* an independent measurement. No write tool was
invoked. Source: `pp2-audit/p4_prior8_reverification.json`.

**Tally: 7 CONFIRMED-STILL-BROKEN · 1 FABRICATED-BY-PRIOR-AUDIT · 0 fixed · 0 partially-addressed.**

| # | Prior claim | Fresh verdict | What the fresh measurement found |
|---|---|---|---|
| 1 | `assess_marriage` returns an empty `seventh_lord_placement` field | **FABRICATED-BY-PRIOR-AUDIT** | The identifier **does not exist anywhere**: zero matches repo-wide (excluding `.git`/`node_modules`, *including* all 495 evidence captures), and zero hits at any nesting depth in a fresh 158,200-byte live `assess_marriage` response whose `content` object has exactly 21 keys. A field that has never existed cannot be "empty". |
| 2 | `standing_predictions_read` crashes; PR #1287 shipped a fix | **CONFIRMED-STILL-BROKEN** | Byte-for-byte reproduction of the crash today. `gh pr view 1287` → `state: OPEN, mergedAt: null`; `git merge-base --is-ancestor 525188467 HEAD` → not an ancestor; the four `isempty(observation_window)` rows are untouched. |
| 3 | `calibration_maturity.n_events = 0` despite 64 LEL events | **CONFIRMED-STILL-BROKEN (worse)** | Still zero — and `kala_field_skill` now holds 7 real rows for this chart with `weights_version='v0_classical'`, so the facades serve a hardcoded false zero **over live data**. Escalated as **F-140**. |
| 4 | `field_gochara_alignment='insufficient_data'` though 22 windows cover today | **CONFIRMED-STILL-BROKEN** | Both halves reproduce. Mechanism independently re-derived (not restated): the internal capability URI is registered nowhere; every call 404s and is silently converted to an epistemic-sounding verdict. Corroborates **F-73**. |
| 5 | `state_delta` carries a stale reason | **CONFIRMED-STILL-BROKEN** | The concept is still unbuilt (by design) but its stated blocker is now **factually false** — the named precondition holds in production (1,839,618 + 31,350 rows). Filed as **F-139**. |
| 6 | `freshness.ephemeris_version` / `sweep_build_date` are null | **CONFIRMED-STILL-BROKEN** | Both still null, while the same block asserts `stale:false` with `stale_reason:null` — a positive freshness claim beside the two fields that would let a caller judge freshness independently. Graded a GAP in the residual register rather than duplicated as a finding. |
| 7 | Prediction lifecycle is stalled | **CONFIRMED-STILL-BROKEN** | Stalled at the first hop, system-wide: 35 open + 1 matched across **all** charts, **zero** terminal verdicts ever, `mcp_prediction_outcomes` empty, the read tool crashing, and the resolver writer in `error`. Deliberately MIXED-graded in the register: the waiting is by design (L5 STRUCTURAL seal), the blockers that make the wait un-endable are not. |
| 8 | Jargon headline + salience defect | **CONFIRMED-STILL-BROKEN** | Reproduced live in one call: ten `ga_sensitive` Saturn template strings at byte-identical salience 2.16108, none naming the 7th lord, Venus or a marriage yoga — plus a new corroborating measurement (the progeny lens shares 6 of its 10 signal_ids with marriage). Covered by **F-114** and **F-128**–**F-132**/**F-137**. |

**Why item 1 matters beyond itself.** The prior audit's *top-ranked* finding named a response field,
with a stated value-state, for a field the codebase has never defined. That is a **fabricated
observation, not a mis-graded one** — the claim is not wrong about severity or root cause, it names
a non-existent artifact. The correct inference is the one P4 drew: **no unre-verified prior-audit
finding may be inherited into a manifest on its own authority.** PARIPŪRṆA-2 acted on that rule
prospectively — none of the eight entered this manifest without independent live reproduction.

**And the counterweight, which is equally part of integrity.** The *defect class* the fabricated
claim gestured at is **real, and was independently found and measured by this audit** as **F-113**:
natal D1 dignity-in-bhava for the 7th house is in no leg of `assess_marriage`'s pipeline, Saturn is
exalted in Libra in the 7th (2nd-strongest graha in the chart), and the string `exalted` appears
zero times in the entire 158,200-byte response. A fabricated claim being fabricated does not make
the underlying concern false, and this report does not use one to dismiss the other.

**One further negative control, recorded because it is generalisable.** Item 2 is a clean natural
experiment on the phrase *"reportedly shipped a fix"*: PR #1287 exists, is correctly scoped and
correctly titled, and produced **zero change in live behaviour because it was never merged**. Any
remediation tracking that counts authored PRs as closed findings will systematically overstate
completion. The remediation campaign that follows this report should count **merged-and-live-
verified**, nothing less.

### §6.2 — The manifest write race, and the fix that held

**The incident.** Before the per-file-per-agent write discipline was adopted — during the P0/P1
base pass — a concurrent-write race on the shared manifest **silently deleted six findings**. Two survivors carry the scar in their own text: **F-27** and **F-28** are
recorded with an explicit caveat that "a concurrent-write race deleted the original finding's full
detail" — their underlying observations were independently re-reproduced and are not in question,
but their precise source lines were lost and both now carry `DIAGNOSIS-INCOMPLETE` on file:line
alone. **F-29**'s text notes, by contrast, that its file:line *was* preserved. That contrast is the
race's fingerprint, left in place rather than tidied away.

**The structural fix.** The discipline adopted in response is **one evidence file per agent, merged
serially by the desk** — never concurrent writes to the shared manifest. Waves 1–5 of this session
ran entirely under it.

**It held: zero races across five waves.** The evidence is the file layout itself — `wave1_A1`,
`wave1_A2`, `wave1_A3`, `wave1_A4`, `wave1_B`, `wave1_G`, `wave2_H`, `wave3_FM23`, `wave3_FM25`,
`wave3_FM26`, `wave3_FactPin`, `wave4_E1`, `wave4_E2`, `wave4_E3`, `wave5_P4_findings` — fifteen
per-agent files, one per agent, merged into `manifest.json` in five sequential commits
(`c0eee770c` → `3e601cf06` → `5298a6548` → `d7435b97d` → `6adc84e43`). Findings F-59 through F-141
— **83 findings, 59% of the corpus** — were produced under this discipline with no loss.
**This is recorded as the successful application of a known fix, not as a new incident.**

**One residual risk, disclosed.** Until commit `9730d2890`, the entire P0/P1 evidence base — 125
tool verdicts, 58 findings, 414 evidence files — existed **only as untracked working-tree files**,
i.e. one `git clean` from oblivion. It is committed now, and every wave since has committed at its
own close. The lesson generalises past this audit: an evidence base that is not committed is not an
evidence base.

### §6.3 — This audit's own findings that failed verification

*(P6 self-verification runs next; this subsection will be completed with P6's results — see
`pp2-audit/p6_selfverification.json` once available.)*

### §6.4 — Desk self-correction: the F-51 misread

Held to the same standard this report demands of the instrument, the desk records an error of its
own, made and corrected during this session.

**What happened.** The desk flagged **F-51** as carrying a bad citation — specifically, that its
anaphoric reference to the `hardFloor` mechanism pointed at a line that did not support the claim.
**That flag was wrong.** On re-check the citation was correct: the reference resolves to
`registry_bridge.ts`, and `timing_hooks.current` with `minKeep: 3` sits at
`registry_bridge.ts:3512` **exactly**. F-51's citation was accurate as written; the desk's reading
of it was not.

**How it was closed out.** Rather than correct the single instance and move on, the desk ran a
**mechanical sweep of all 73 citations** in the affected set, which found **zero EOF-violations** —
i.e. no citation in the corpus points past the end of the file it names. The suspicion that
generated the flag was therefore not merely wrong about F-51; it was wrong about the population.

**Why it is recorded here.** Three reasons, in ascending order of importance. (a) A false-positive
in an audit desk is the same defect class as a false-negative in the instrument: a status asserted
without a detector that could have made it read the other way (§N.8). (b) An unrecorded correction
leaves the corpus looking like it survived a challenge it never actually faced, which inflates
confidence in exactly the way this audit was commissioned to prevent. (c) This report grades the
instrument on whether it surfaces its own gaps rather than masking them; a desk that does not do
the same has no standing to grade it. **F-51 stands as filed, its citation is correct, and the
misread was the desk's.**

### §6.5 — Other honesty items in this audit's own conduct

Recorded so a reader can weight the findings correctly rather than uniformly:

- **Scope discipline held.** No write tool was invoked at any point; the two write-path tools were
  verdicted `NOT-APPLICABLE` by schema inspection rather than invocation, and the prediction-
  lifecycle measurement (prior-8 #7) was taken read-only with `mimamsa_outcome_record` deliberately
  not called even though calling it would have produced a cleaner measurement.
- **Non-retroactive downgrading, explicitly.** **F-43** identified ~16 further tools sharing the
  `unknown_tool` defect **by source grep, not by live retest**, and states in its own text that
  those tools' existing PASS verdicts are **not** retroactively downgraded without live
  confirmation. The audit chose a narrower true claim over a broader plausible one.
- **One finding is non-reproducible on retry.** **F-89** (raw Postgres encoding literal leaked into
  `content.content`) was captured live once; two immediate retries of the byte-identical input did
  not reproduce it. It is filed with that caveat visible rather than dropped or generalised.
- **A dark-corpus number that could have been flattering was refused.** **F-109** reports
  19/21 = 90.48% BRIGHT and immediately states that this is **not comparable** to the 2026-07-25
  baseline's 5.58% (a structurally different metric that was not re-run), and that the career set
  was not re-run at all. The comparison that would have looked like a 16× improvement is explicitly
  disclaimed by the measurement itself.
- **The audit's own gate is reported as failing** (§5.3) rather than waived, and the signed
  coverage line the plan requires is **absent from this report because it cannot honestly be
  produced yet**.

---

*End of PARIPŪRṆA-2 audit report v1.0 (P5). §6.3 awaits P6. Nothing in this document may be read as
a terminal completion marker: per `PARIPURNA_2_AUDIT_PLAN_v2_0.md` §7, done means the gate exits 0,
its signed line is in the ledger, and PARĪKṢAKA's independent re-run and 15% reproduction sample
pass. As of this writing the gate reports 187 blocking problems and P6 has not run.*
