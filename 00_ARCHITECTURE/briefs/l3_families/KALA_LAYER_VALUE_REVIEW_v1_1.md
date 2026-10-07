---
artifact: KALA_LAYER_VALUE_REVIEW
canonical_id: KALA_LAYER_VALUE_REVIEW
version: "1.1"
status: DRAFT — reconciled against Astra's review (PROCEED_WITH_AMENDMENTS → this revision); for the native's rulings (§9 and reviews/KALA_LAYER_PLAN_RECONCILIATION_v1_0.md §7). Research and strategy only. Nothing here authorises a build, a migration, a data clear, a registry edit, a deploy, or a change to any campaign's state or holds.
produced_on: 2026-10-06
produced_in: 'Claude Code (Fable 5.1) session, working tree on campaign/nirmana-autonomous @ badc3f9bc (569 behind origin/main); evidence read from origin/main @ 09fd39b4d, branch l3/sangam-final @ fbbbb9414, branch suvarna/hq @ 79ab6b509, the worktree .kilo/worktrees/cooperative-racer @ c751f3bd8, commit d1560e321 (the September L3 studies), and the production database read-only at 2026-10-06T07:05Z'
method: 'layer-value-elevation skill (consumer-first whole-layer review) — the same method the Gochara-family, Kṣetra and Saṅgam exercises used per asset, applied once to the whole layer. Three bounded read-only research digests (prior exercises; the September studies; the code producer→consumer trace) were produced by sub-agents and are cited as digests where the author did not re-read the source.'
chart_scope: "482012f1-710e-4a25-994a-93821f5871aa only (Pravāha D-SCOPE; Suvarṇa single-chart ruling)"
evidence_labels: "[L] production read-only, verified by the author this session · [S] source read at the named ref · [D] doctrine, document named · [A] taken from a sub-agent digest, not re-read by the author · [I] inference · [U] unverified"
relationship_to_prior_work: >
  Decision delta, not a restart (§1). Supersedes nothing. Builds on: the September L3 studies (stocktake · value architecture · consumer-first
  master plan · cross-layer leverage; commit d1560e321), the approved L3 strategy (MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0, DP-SD-017), the
  three ratified or pending family plans (GOCHARA_FAMILY_ELEVATION_PLAN v2.2 · KSHETRA_ECOSYSTEM_ELEVATION_PLAN v1.17 · SANGAM_ELEVATION_FINAL
  v1.0), the Suvarṇa focus-families note (SUVARNA_L3_FOCUS_FAMILIES v1.4) and this morning's KALA_PIPELINE_CONCEPT_NOTE v1.1 (F-2 option 2).
companion: "KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md (same folder) — code architecture and build plan; KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md (same folder) — per-asset domain-logic elevations; reviews/ASTRA_REVIEW_KALA_LAYER_PLAN_v1_0.md and reviews/KALA_LAYER_PLAN_RECONCILIATION_v1_0.md — the review and its reconciliation"
supersedes: 'KALA_LAYER_VALUE_REVIEW_v1_0.md — retained byte-identical as the reviewed artifact (sha256 ff74f7bb2638aaaaa9bb2662b332ec9025cae9f8d148a6115857244b57b5eec0)'
does_not_decide: "Anything owned by Pravāha (Gochara D-*/ADK-*), Strategic Suvarṇa (N-*), or the native's sealed rulings. Where this review recommends a change to one of those, it says so and routes it (§9)."
changelog:
  - "1.1 (2026-10-06): reconciliation with Astra's review (verdict PROCEED_WITH_AMENDMENTS; its one finding against this document, KL25, amended). Reach is now stated in three layers (registry / MCP facade / web floor) in §0, §3 row 26, §4 and F-L19; F-L21 scoped (a registered capability does read `kala_taranga`; the gap is facade and Vidhi routing); F-L22's \"one-line correction\" withdrawn for `ka_bhavishya_lekha`, whose L4 read protects outcome-referenced rows. No disposition or ruling changed. Companion pointers moved to v1.1."
  - "1.0 (2026-10-06): first whole-layer review. Temporal-plane coverage map (§3), served-reality probe (§4), 25-row asset disposition register (§5), the layer as one system (§6), question→capability readiness (§7), new findings F-L1…F-L22 (§8), eleven rulings for the native (§9), dependency-ordered first slice (§10)."
---

# Kāla — whole-layer value review

**Written for:** the native as decision owner; the Pravāha steward and Strategic Suvarṇa as the two campaign authorities whose scope this touches; and whichever session next writes a Kāla stage brief.

## §0 · One page

**The question asked.** Does the Kāla layer, as a layer, cover the temporal plane, and do its assets deliver the highest value individually and together? The three per-asset exercises (Gochara family, Kṣetra, Saṅgam) answered this for three of twenty-three assets. This review answers it for all of them, and for the seams between them.

**The answer in one paragraph.** The layer *owns* the temporal plane on paper: every classical clock and transit instrument the product definition names has an asset, a table or a service, and the serving tools disclose honestly what they cannot say. But today the native's chart gets almost nothing time-specific from it. The structure→time chain (bridge → convergence → activation → obstruction → view → projection) is dead on the canonical chart: five of its six tables are empty and the sixth, the activation bridge, has 50,678 rows of which 531 still point at a structural signal that exists (the L2 signal layer was rebuilt yesterday) [L]. The served transit layer is a decade-era context layer with no timing windows and, measured under the frozen protocol, does not separate from random [D]. The field (Kṣetra) has never completed a build and is served by nothing [L]. What *does* reach the native today is the calendar and overlay substrate: daśā chapters and boundary bands, daily pañcāṅga primitives, the five classical transit overlays over a rolling fifteen months, the annual Tājaka context, election candidates and ritual opportunities. Those are real and honest, but they are the surround, not the centre.

**Two channel facts change what "served" means — stated by reach layer.** *Registry reach:* several L3 capabilities are registered and read their tables (`kala_windows_get` resolves; `query_activation_waveform.ts` reads `kala_taranga`). *MCP-facade reach:* the eight Kāla views exist in the MCP package and answer a direct MCP client. *Web-floor and portal reach:* the portal renders no Kāla table (the timeline page draws the life-event log; the arrival line is an explicit placeholder) [S]; the conversational channel's web engine resolves only three of the Kāla tools the Vidhi floors name (windows, muhūrta, yoga activation), and the generated bridge counts 29 unmapped live-tool entries, including the NOW/AHEAD/PRIORITY hard floor [S]. So today the layer's main views reach a direct MCP client and not the product's two main doors (§8 F-L19). The "eleven intents" figure is the author's count from the floor contracts, not independently certified.

**Why the layer looks whole and is not.** Three independent engines (Gochara, Saṅgam, Kṣetra) were each built to answer "when does this happen in this life?", each recomputing the sky, the promises and the clocks, each storing a different shape, with the seven downstream "reader" assets wired to whichever engine was alive when they were written. The declared dependency graph disagrees with the real one in at least six places [S][L]. The two pieces of value no single asset owns, cross-clock agreement and the independence of witnesses, were never built (the September studies and the Gochara plan both parked them as "layer-level").

**What has already been decided that this review does not reopen.** F-2 (option 2, 2026-10-06): Saṅgam and Kṣetra become the concordance and odds stages of one pipeline whose spine is Gochara 5.0. N-32: the L2→L3 cascade keys are dropped and downstream rebuilds in wave order. D-SCOPE: one chart. The enrichment order (repair semantics → period relationships and Sudarśana → Tājaka and KP → relatives). Those rulings settle the three families. They do not say what happens to the other twenty assets, who owns them, or what the native is served in the meantime. That is the gap this review fills.

**Recommendation.** Extend the pipeline concept from three families to the whole layer: three shared foundations (promise graph, clock service, outcome record), three evaluated stages (judge, jury, forecaster), one typed negative-space producer, one atomic publication manifest, and the eight views as projections over those. Eleven of the remaining twenty assets become projections or adapters of that pipeline rather than independent writers; three stay as services; two overlays need method adjudication before any consumer is allowed to read them; the century materializer is formally superseded (data retained); nothing is deleted (§5, §6). Fix two serving defects now, with no data change (§8 F-L2, F-L3). Then ten rulings (§9) and a dependency-ordered first slice (§10).

**What this review did not do.** It did not rebuild, re-measure other charts, run any writer, or verify the Suvarṇa or Pravāha launch states beyond their committed records. It makes no claim about predictive validity. Every served figure is as of 2026-10-06 07:05 UTC.

---

## §1 · Where this sits — decision delta

The method is the one the skill distilled from the September Kāla work and the three family exercises reused. The question is new only in scope. The table records what each predecessor established and what this review adds or changes.

| Prior artifact (date) | What it established | What this review keeps | What it adds or changes |
|---|---|---|---|
| L3_STRATEGIC_STOCKTAKE v1.0 (09-11) [S] | 23-asset denominator; 13 frozen / 10 open; five core tables empty; `ka_sangam` has 25 downstream assets; two scoreboards (receipts vs readiness) | The two-scoreboard rule; the empty-table honesty rule | Live re-measurement: the bridge is now 99 % dangling, not 79 rows (§8 F-L1) |
| L3_KALA_VALUE_ARCHITECTURE v1.1 (09-11) [A] | Eight typed quantities never collapsed to one scalar; eight consumer outcomes V1–V8; "no asset is certified safe to delete" | The typed quantities (§2); the no-deletion stance | Its "Kṣetra as common substrate" recommendation was already superseded by the master plan; this review confirms the supersession (§6) |
| L3_KALA_CONSUMER_FIRST_MASTER_PLAN v1.1 (09-12) [A] | Q01–Q18 question portfolio; ten target responsibilities T1–T10; 23 assets mapped to T1–T10; W0–W8 packets | The idea that readers become projections (T10) and Kṣetra donates components (T6) | Replaces T1–T10 with the pipeline's judge/jury/forecaster + F1/F2/F3 (the native's F-2 ruling made that choice); keeps the asset→responsibility mapping as the migration map (§5) |
| L3_KALA_CROSS_LAYER_LEVERAGE v1.0 (09-12) [A] | 36 input-use contracts A01–A12 / B01–B12 / F01–F12; six maturity states | The six maturity states (present → qualified → consumed → effect traceable → served → value evaluated) as the coverage vocabulary (§3) | Applies them to served reality, not to code presence |
| MADHAV_DATA_PLANE_L3_KALA_STRATEGY v1.0 (09-15, approved DP-SD-017) [S] | L3-Q01–Q13 obligations; ten logical objects (§3); 22 active + 1 retired; waves W0–W8; interface packets U01–U11; registry-vs-real edge discrepancies | Q01–Q13 as the acceptance baseline (§7); the ten objects; U01–U11 | Reconciles the strategy's 22-identity map with the pipeline concept (§6.2); records that its wave plan is now gated by F-2 and N-32 |
| GOCHARA_FAMILY_ELEVATION_PLAN v2.2 (09-23, ratified) · Pravāha D-SPECS v1.4 FROZEN (09-30) [A][S] | Judge contract: relationship records, rule paths P1–P9 (P1–P6 implemented in code at the time of this review; P5 held), three-field valence, permission per instant, vedha intervals, sky substrate, publication manifest, 57 oracles; '5.0' candidate; '3.0' served | Everything; cited, never reopened | Names what the judge does *not* own and who should (§6) |
| KSHETRA_ECOSYSTEM_ELEVATION_PLAN v1.17 (09-24, approved for stage 3) [A] | Ten rulings; 6-class product; σ_T from L1; evaluation-only episodes (B8-6); ablation pre-registered | All rulings; B8-6 held | Confirms the forecaster role (F-2) and that nothing serves the field today (§4) |
| SANGAM_ELEVATION_FINAL v1.0 (09-23, pending rulings on main) [A] | Output boundary is the defect; six repairs, six elevations; cascade reaches sealed L4 | Superseded in scope by the concept note (its own §0 says so) | — |
| SUVARNA_L3_FOCUS_FAMILIES v1.4 (09-30) [S] | None of the three families in a good state; links between them; F-1…F-6; N-32; 16 readers frozen in FAMILY_ASSETS.json; Kṣetra on the L5 critical path | The links and the reader list | Extends the family view to the twenty non-family assets, which Suvarṇa's Track F does not cover (§9 D-7) |
| KALA_PIPELINE_CONCEPT_NOTE v1.1 (10-06, reconciled, for seal) [S] | Judge / jury / forecaster over one shared object; F1/F2/F3; evidence algebra; agreement measure; typed negative space; frozen data roles; §11 "the per-asset template does not fit a pipeline; a shared-substrate brief type is missing" | Adopted as the layer's value architecture, as proposed | Answers its §11: maps every remaining asset onto the pipeline (§6.2); adds the readers, services and overlays the note leaves outside its scope |

What is *not* a decision delta: this review does not re-derive the Gochara doctrine, the Kṣetra rulings or the N-32 migration. It cites them.

---

## §2 · What the layer is for — the distinctive contribution, in plain words

From the sealed product definition (v3.0 §3.10) and the approved strategy (§2) [S]:

Kāla answers *which enduring structures of this chart are engaged by which clocks, when, under what conditions, and with which alternatives*. Its unit of value is a **window a forward claim can attach to**: a half-open interval, with the clock and the contact that produced it, the structure it engages, the conditions that enable or inhibit it, and the coverage of the search that found it. A background period, an enabling interval, a specific contact, an inhibiting condition, a recurrence and an inferred manifestation are six different things and are served as six different things. A transit coincidence is not an activation. A precise astronomical instant does not make a forecast precise. "No window found" is bounded by the horizon, the resolution and the methods actually searched.

The eight quantity types that must never be collapsed (VA §4, carried into Product v2.0 E3 and the pipeline concept §2) [A][S]:

1. astronomical instant or interval · 2. rule-based eligibility or activation measure · 3. valence and suppressive contribution · 4. timing shape (onset, peak, decay, recurrence) · 5. model rate with unit and baseline · 6. probability for a defined event over a defined horizon · 7. empirical reliability (n, basis, uncertainty) · 8. salience for *this* question.

Everything below is measured against that contract, not against row counts.

---

## §3 · Coverage of the temporal plane

The user's first question: *does the layer, as a layer, cover the temporal plane?* The table lists every temporal instrument the product definition or the classical corpus in use names, who owns it, and how far it has actually travelled toward the native. Maturity vocabulary is the cross-layer study's: **present** (rows or code exist) → **qualified** (method and source adjudicated; conventions pinned) → **consumed** (a downstream computation reads it) → **served** (a tool returns it to the native) → **value evaluated** (its contribution to a question was tested). A ✗ means the state is not reached; `—` means not applicable.

| # | Instrument / clock | Owning asset(s) · table | Present [L] | Qualified | Consumed | Served today [L] | Gap, in one line |
|---|---|---|---|---|---|---|---|
| 1 | Vimśottarī daśā, levels 1–4 | L1 `chart_dashas` · `ka_dasha_kala` (service) · `ka_avadhi` | ✓ (L1; avadhi 1,169 rows, 2026-08-12) | ✓ at L1 (two_pass_verified build pinned in Gochara §4.0) | ✓ (judge permission; sandhi bands; STORY) | ✓ NOW sandhi bands L1–L4; AHEAD lord transit condition; STORY chapters; bundle timeline | Sūkṣma boundary uncertainty is a placeholder (± half own span), not error propagation; the F2 covariance defect is live (§8 F-L14) |
| 2 | Other daśā systems: Yoginī, Chara, Kālacakra, Mudda, Naisargika, KP sub-level; Aṣṭottarī absent | L1 (nine system ids) · `ka_dasha_kala` "cross-system agreement" · `ka_avadhi` dossiers | ✓ | ✗ applicability per system stored but never adjudicated; "agreement scoring" has no independence model | ✓ avadhi/kshetra clocks read them | partial: Mudda chain in AHEAD; others only via bundle timeline | No consumer compares systems within a competence class; the jury's G-J/G-T/G-K/G-A sequential admission is the first design for this |
| 3 | Period relationships: lord condition at commencement (BPHS 47.3–6), MD/AD/PD lord relationships (52.11–14, 61.1), beginning/middle/end fruition | none | ✗ | — | — | ✗ | Enrichment step 2 (native's order); nothing exists |
| 4 | Gochara to natal structure (served) | `ka_gochara_sweep` v1 (retired capital, 16,297 rows) · `'3.0'` (914 rows, authority since 2026-09-28) | ✓ | ✗ `'3.0'` measured: T-cover 32/47 vs random 68.6 %; T-FP fails 8/9 adverse classes [D] | ✓ Kṣetra read it (undeclared) | ✓ `gochara_forecast_get`; NOW `gochara_narrative.active_windows` | Every served row is a decade-era context row (`is_timing_window=false`); none is a timing claim (§8 F-L3, F-L6) |
| 5 | Gochara to natal structure (judge, `'5.0'`) | `ka_gochara_v5` (INERT skeleton) · `ka_gochara_eval_window` 0 rows · `ka_gochara_contact` 0 rows | code ✓, data ✗ | ✓ specs FROZEN v1.4; 57 oracles; protocol v2.1 | — | ✗ | Pravāha owns; small-test staging in progress (migration 1304, 2026-10-06) |
| 6 | Vedha (transit obstruction) | `ka_vedha_gochara` · 171 rows (2026-09-27) | ✓ | ✓ cited Phaladīpikā XXVI; PG353 scale only; exceptions pending G-9 | ✓ Saṅgam (undeclared), century, Kṣetra | ✓ NOW | Horizon is rolling 2026-07-29 → 2027-11-01 only (§8 F-L7) |
| 7 | Moorti-nirṇaya (transit quality) | `ka_moorti_nirnaya` · 74 rows | ✓ | ✗ method contested (27-nakṣatra offset vs 12-house Moon table, VA §5 F5) [A] | ✓ century context | ✓ NOW (4 of 8 grahas computed) | Served while contested (§8 F-L8) |
| 8 | Kota-cakra (transit fortress) | `ka_kota_chakra` · 585 rows | ✓ | ✗ ring table is a tier-(iii) transcription, `uncited_extension=true` on every served row | ✗ century declares, does not read | ✓ NOW | Nothing downstream uses it; citation gap filed (ADJUDICATION-9) |
| 9 | Aṣṭakavarga gating / kakṣyā | L1 bindu (sign-level, single_pass) · judge P5 planned | ✓ at L1 | ✗ single_pass; contributor-level kakṣyā unbuilt (G-10) | Saṅgam C7 "always None" | ✗ | Judge P5 is the only designed consumer |
| 10 | Sade-sati / Moon-reference transits | L1 `ganita_sade_sati` · NOW dual reference | ✓ | ✓ | — | ✓ NOW (house from Moon and from Lagna, side by side) | Fine as a fact; not a window |
| 11 | Tājaka varṣaphala (annual) | L1 `ga_tajaka` · AHEAD `mudda_dasha_varsha` | ✓ | ✓ at L1; judge P9 behind D-T2 | — | ✓ AHEAD (year lord, Muntha, Mudda chain) | Served as context; no annual *window* yet |
| 12 | Tithi-praveśa (lunar return) | `ka_tithi_pravesha` · 120 rows | ✓ | ✗ method contested (Moon-longitude return vs Sun–Moon angle); "not_in_corpus" citation on the served row | ✗ | ✓ NOW; AHEAD says `not_in_corpus` for the same concept | Two tools disagree on whether it exists (§8 F-L8) |
| 13 | Sudarśana year-wheel (three frames) | `ka_sudarshana_varsha` · 120 rows | ✓ | partial: wheel only, not the Sudarśana daśā (BPHS 74) | ✗ | ✓ NOW (`tri_lagna_convergence`) | Enrichment step 2 makes it a judge method |
| 14 | Sky-event calendar (ingress, station, eclipse-to-natal, return) | judge `sky_event_substrate` (spec) · `ka_graha_sancara` | code ✓ | ✓ in spec | — | ✗ (`not_in_corpus` in AHEAD) | Arrives with `'5.0'` |
| 15 | Daily pañcāṅga primitives: horā, gulika, diśā-śūla, candrāṣṭama, janma resonance | `ka_muhurta_seva` / panchang engine | ✓ | ✓ | — | ✓ NOW, AHEAD (31-day gulika) | Facts, honestly ungraded; fine |
| 16 | Election (muhūrta) for an undertaking | `ka_muhurta_seva` · `kala_elect_get` · L4 `ph_muhurta` | ✓ | partial: Factor Census; no doṣa-cancellation corpus | — | ✓ ELECT; ritual opportunities in AHEAD digest | Election over *qualified* methods is a view the concept note defers (§4.4) |
| 17 | Praśna (question chart) | none in Kāla; `prashna_ask` is a channel name | — | — | — | — | Consciously out of scope for natal timing (CL §7); listed so the exclusion is visible |
| 18 | Structure → time bridge (which signal fires under which predicate) | `ka_yojaka` · `kala_activation_predicates` 50,678 | ✓ | ✗ every Mode A/B predicate targets 0° Aries; one domain; no ayanāṃśa identity | ✓ Saṅgam/Kalasutra/Vighnakara/Jivana | ✗ | **531 of 50,678 resolve to a live signal** after the 2026-10-05 L2 rebuild (§8 F-L1); F1 replaces it |
| 19 | Concordance (several clocks agree on one window) | `ka_sangam` · `kala_convergence` | ✗ 0 rows | ✗ | — | ✗ (NOW/AHEAD/PRIORITY honest-empty) | Jury stage; no asset owned independence until the concept note §5.2–5.4 |
| 20 | Activation intervals and recurrence per signal | `ka_kalasutra` · `kala_activation` | ✗ 0 rows | — | — | ✗ | Projection of jury output in the target (§6.2) |
| 21 | Obstruction / counter-indication periods | `ka_vighnakara` · `kala_obstruction` | ✗ 0 rows | — | — | ✗ | Becomes the typed negative-space producer (§6.2) |
| 22 | Display-ready confluence view | `ka_kala_darshana` · `kala_darshana` | ✗ 0 rows | — | — | ✗ | Becomes the publication projection (§6.2) |
| 23 | Forward projections / issued forecasts | `ka_bhavishya_lekha` · `kala_bhavishya` | ✗ 0 rows | ✗ "probability tiers" with no event model | — | ✗ (AHEAD empty; `predictions_logged` 0) | Becomes the `issued_forecast` object (concept §2) |
| 24 | Life chapters | `ka_jivana_parva` · 100 rows (2026-08-13) | ✓ | partial: chapter hierarchy from L1; convergence density from a table now empty | — | ✓ STORY | **Serves 8,838 "high-convergence windows" across 43 chapters from data that no longer exists** (§8 F-L2) |
| 25 | Period dossiers ("how will my Ketu daśā be") | `ka_avadhi` · 1,169 rows (2026-08-12) | ✓ | partial: ten-row limits, fixed domains, no ayanāṃśa in key | ✗ Taranga does not read it (false edge) | ✓ bundle timeline | Two reproducible failed rebuilds, unresolved (#2581/#2582) |
| 26 | Monthly activation waveform 1950–2100 | `ka_taranga` · 92,412 rows (2026-08-13) | ✓ | ✗ W2 decided the event-class half is degenerate; writer still builds both | ✗ | registry capability `query_activation_waveform` reads the table (summary/drill); no MCP facade; the Vidhi `taranga_curve` primitive points at `kala_bundle_get`, which does not read it [S] | Registry-only; not on the intended facade or floor (§8 F-L11, F-L21) |
| 27 | Continuous hazard field λ_e(t) per event class | `ka_kshetra` · `kala_field` 8,570,075 rows (2026-09-10), 15 tables | ✓ rows, ✗ snapshot (0) | ✗ axis offset ≈ 15.9 y; chart-wide suppression; σ_t defect | L5 `mi_bhara` binds to an unpublished snapshot | ✗ nothing serves it; every view says `field_not_yet_built` | Forecaster stage; rebuild refused by design until W7 |
| 28 | Cross-pattern prioritisation / attention | `ka_tulana` (service) · `kala_field_salience` 0 rows | code ✓ | ✗ legacy single scalar ("salience monoculture") | ✗ PRIORITY ranks `bodha_msr_signals ⨝ kala_activation` directly; the `ka_tulana` ranker is called only by the orchestrator's service probe [S] | ✓ PRIORITY (honest-empty) | The service the layer registered as its ranker ranks nothing the native sees (§8 F-L20) |
| 29 | Birth-time / ayanāṃśa sensitivity of windows | Kṣetra clocks σ_t · NOW lite bound | partial | ✗ covariance defect `uncertainty.py:268–276` | — | lite only | F2 fixes once (§8 F-L14) |
| 30 | Outcome record and evaluation | Samīkṣā ledger · EVENT_REGISTRY v2.1 (47 held-out; 30 timing-usable) · `kala_insights` 0 | ✓ | ✓ protocol pre-declared | — | `calibration_maturity`: 7 events, 0 prospective resolutions, skill ≈ 0 | Honest; nothing to score until forecasts are issued |
| 31 | Rectification as an evidence update | L4 `phala_rectification_best` · concept §6.5 | ✓ at L4 | ✗ Kṣetra reads it live (forbidden upward read) | — | — | F2 governs the path |
| 32 | Relatives' charts for shared events | none (D-SCOPE) | — | — | — | — | Deferred by ruling; listed |

**Reading the table.** Coverage of the *plane* is complete at the "present" column: 29 of 32 rows have an asset. Coverage of *value* is thin: eleven rows reach the native, and of those only the daśā chapters, the boundary bands, the pañcāṅga primitives, the annual context and the vedha overlay are both served and qualified. The centre of the plane, rows 18–23 (bridge, concordance, activation, obstruction, view, forecast), is entirely dark on the canonical chart. That is where the mission's third obligation lives (time-indexed, testable claims), and it is the part the three family exercises and F-2 are rebuilding.

---

## §4 · Served reality on 2026-10-06 — what the native actually gets

Six tools were called read-only on the canonical chart at 07:05 UTC [L]. The point of this section is the "served" column above: a populated table is not a served capability.

| Tool | What came back | Honest? | Defect |
|---|---|---|---|
| `kala_now_get` | Thesis "no temporal activation window is active"; `field_not_yet_built`; sandhi bands L1–L4 (Sūkṣma boundary band active today); dual-reference transits; MD/AD lord transit condition; horā, gulika (active now), diśā-śūla, candrāṣṭama, janma resonance; kota (9 grahas), sudarśana year 43, moorti (4 of 8 computed), vedha (3 rows), tithi-praveśa year 43; `gochara_narrative.active_windows`: ten `'3.0'` rows 2024-02-05 → 2034-01-30 with peak dates and signed intensities; `field_gochara_alignment: divergent` | Mostly. Coverage block names 18 concepts with states; staleness reported null with reason | The `active_windows` block presents decade-era rows (every one `is_timing_window=false` in the forecast tool) as "active windows" with peak dates, without the era disclosure the forecast tool carries (§8 F-L3) |
| `kala_ahead_get` (3 y) | No windows, no projections, `promise_gate: not_applicable`, recurrence ladder empty, Mudda/Muntha context, 31-day gulika, 90-day digest with four "charity (mars)" ritual opportunities, period echo (Saturn AD hypothesis from one prior occurrence), `predictions_logged: 0` | Yes | None new; the digest's ritual rows are the only forward-dated items a reader would see as "coming" |
| `kala_priority_get` (90 d) | Honest empty; five-axis salience `honest_empty` (no `kala_field_salience` rows) | Yes | — |
| `kala_story_get` | Mercury MD "building"; 91 chapter rows deduplicated to 91; each chapter carries `high_convergence_count` and `avg_effective_score` (e.g. Jupiter MD 1984–1991: 884 windows, 0.423); LEL pinning per chapter; lexical retrodiction fit | **No** | The convergence figures were computed 2026-08-13 from `kala_convergence`, which has 0 rows for this chart today; the number is served as a current fact with a `structural_prior` tier and no staleness flag (§8 F-L2) |
| `gochara_forecast_get` (2026-10 → 2027-10) | 8 interval rows, generation `'3.0'`, shapes all interval, resolution 5 era / 3 untagged, `is_timing_window=false` on all 8; coverage lists 26 event classes; 246 KB response (term_breakdown ≈ 21 KB per row) | Yes (resolution disclosure present) | Nothing in the next year is a timing claim; the response is 25× the budget other kala tools honour (§8 F-L6) |
| `kala_gochara_authority` [L] | `'3.0'`, flipped 2026-09-28 by the F-0 safety reversal | — | — |
| Portal pages [S] | No page or component under `platform/src/app` or `platform/src/components` reads a `kala_*` table; the client timeline page renders the life-event log; `ArrivalLine.tsx` is a placeholder with no `kala_now_get` call | — | The native's own portal shows no Kāla output (§8 F-L19) |
| Paripraśna web engine [S] | Of the Kāla live tools the Vidhi floors name, only `kala_windows_get`, `kala_muhurta_get` and `kala_yoga_activation_get` resolve to a capability; `now_read`/`ahead_read`/`priority_read` (hard floor in 11 intents), `elect_read`, `story_read`, `ritual_read`, `explain_read` and all `gochara_*` resolve to `None` and are counted as `unmappedPrimitives` | — | The conversational channel cannot reach the layer's main views (§8 F-L19) |

**Who can reach even this.** Only a direct MCP client. The portal shows none of it and the conversational channel resolves three tools of nineteen. Every "served" tick in §3 therefore means "served to a direct tool caller", not "served to the native in the product".

**What the native can and cannot ask today.** "What period am I in, where are its boundaries, what is the sky doing relative to my Moon and Lagna, which daily hours to avoid, what is my annual context, when is a good day for a rite" — answered, honestly. "When does my financial promise activate; is a rough patch coming; which of two windows is better supported; why do the methods disagree; what did you predict and what happened" — not answerable from the layer today, and the tools say so.

---

## §5 · Asset disposition register — all 25 registry rows

Twenty-three frozen-denominator identities (22 active + the retired sweep) plus two Pravāha staging rows in the live registry [L]. Dispositions use the skill's vocabulary: **retain** · **correct** · **enrich** · **integrate** (fold into an owner) · **projection** (keep the output as a view, retire the independent writer after migration) · **adapter** (keep as a qualified method input) · **supersede-after-migration** · **historical** · **park** · **unresolved**. No disposition authorises deletion; every "projection" or "supersede" names its successor and keeps its data until the successor is accepted.

| Asset | Live state (chart 482012f1) [L] | Consumers found (search scope §11) | Unique value worth keeping | Disposition → successor in the pipeline (§6.2) | Owner today |
|---|---|---|---|---|---|
| `ka_graha_sancara` | service; `last_selftest` probe | judge sky substrate; NOW/AHEAD transit joins; Saṅgam scan | ephemeris-at-T with memo cache; two read paths | **retain** as the sky service under the judge's `sky_event_substrate` | Pravāha (Stream A) |
| `ka_dasha_kala` | service | Saṅgam prior (static 0.5 fallback); Kṣetra clocks; NOW/AHEAD | L1-authoritative clock reads across 7 systems | **retain → becomes F2** (`period_context`, `boundaries`), gaining applicability per system and correct σ | unowned (Suvarṇa Track A/I) |
| `ka_muhurta_seva` | service | ELECT; Saṅgam C8; Vighnakara | deterministic pañcāṅga scoring; Tāra-bala overlay | **retain**; election view re-based on qualified methods later (concept §4.4) | unowned |
| `ka_tulana` | service; 0 salience rows | none in serving: `call_priority_ranking` ranks `bodha_msr_signals ⨝ kala_activation` itself; the ranker is invoked only by `service_probes.py` [S] | head-to-head compare with dissonance verdicts (unused) | **retain kernel → re-base** on jury D(W) + forecaster axes and wire PRIORITY to it, or retire the service honestly; today it is a shelf service with a registry row (§8 F-L20) | unowned |
| `ka_gochara_resonance` | 623 rows, 2026-10-01 | `ka_gochara`, century, Kṣetra | per-class target discovery with citations | **correct** (R-1…R-6: 154 targets on negative results, 54 dangling yoga targets) → folds into the judge's relationship record | Pravāha |
| `ka_gochara` | `'2.0'` 87 rows in `_v2`; writer still writes the old table | none (unserved) | the registered per-chart materialiser identity | **supersede-after-migration** by the `'5.0'` registered writer (A5.3); identity kept, table shape strangled | Pravāha |
| `ka_gochara_sweep` (retired) | 16,297 v1 rows; no writer | `'v1'` COALESCE fall-throughs (being removed) | irreplaceable historical corpus (I2) | **historical**; snapshot-protected | Suvarṇa (R8 fence) |
| `ka_gochara_v3_century_materialize` | `is_active=false`; 914 g3 rows; EXTERNAL_HOLD | none current | scoring astrology reused in the judge's kernels | **supersede-after-migration** by the judge's compute-once sky substrate + compact evaluator; data retained; needs the owner's formal disposition (§9 D-4) | native (hold) |
| `ka_gochara_v4_41_candidate` (staged) | 0 rows; `domain`/`rung` null | — | engineering proof only (D-41) | **historical** once `'5.0'` lands; registry row needs domain/rung (§8 F-L5) | Pravāha |
| `ka_gochara_v5` (staged, INERT) | 0 rows; small-test staging | — | the judge | **the judge** | Pravāha |
| `ka_vedha_gochara` | 171 rows, 2026-09-27; horizon to 2027-11-01 | Saṅgam (undeclared), century, Kṣetra, NOW | three cited vedha mechanisms as interval relations | **retain + enrich**: declare the Saṅgam edge; extend or disclose horizon; exceptions per G-9; becomes the judge's `vedha_interval_relation` input | Pravāha (per 09-24 rulings) |
| `ka_moorti_nirnaya` | 74 rows | century context; NOW | transit-quality overlay | **adapter, gated**: method adjudication (27-nakṣatra vs 12-house table) before any consumer reads it; mark served rows `method_contested` (§9 D-5) | Pravāha |
| `ka_kota_chakra` | 585 rows | NOW only | ring testimony | **adapter**: judge soft factor only after a primary citation lands (ADJUDICATION-9); until then served as `uncited_extension` (already true) | unowned |
| `ka_tithi_pravesha` | 120 rows | NOW only | lunar-return annual identity | **adapter, gated**: same as moorti; reconcile NOW (`computed`) vs AHEAD (`not_in_corpus`) | unowned |
| `ka_sudarshana_varsha` | 120 rows | NOW only | three-frame annual wheel | **enrich → judge method** at enrichment step 2 (BPHS 74 nested periods) | unowned |
| `ka_yojaka` | 50,678 predicates; **531 resolve** | Saṅgam, Kalasutra, Vighnakara, Jivana | signature-class templates; the idea of a compiled predicate | **supersede-after-migration by F1** (promise graph from L1 facts + versioned rules); no canonical rebuild (concept §8.4) | Suvarṇa family_sangam |
| `ka_avadhi` | 1,169 rows, 2026-08-12; 2 failed rebuilds | bundle timeline; `query_dasha_dossier` | per-period dossier shape | **projection over F2 + F1** (dossier = period context + attached promises); retire the writer after migration; the failed-build diagnosis becomes moot (§9 D-9) | unowned |
| `ka_sangam` | 0 rows | Darshana, Kalasutra, Vighnakara, Taranga, Tulana, Bhavishya, Jivana | the concordance question | **the jury** (F-2 option 2) | Suvarṇa Track F / the Saṅgam session |
| `ka_kalasutra` | 0 rows | NOW/AHEAD windows; recurrence ladder | per-signal activation intervals + recurrence | **projection of jury assertions** attached to L2 signals (concept §5.5); the recurrence ladder reads judge contacts | unowned |
| `ka_vighnakara` | 0 rows | Darshana, Tulana, Bhavishya | obstruction as a first-class quantity | **integrate → the typed negative-space producer** (concept §6.4): obstruction/cancellation/exception *as the judge records them*, six states; no separate scorer | unowned |
| `ka_kala_darshana` | 0 rows | NOW confluence; STORY density; Jivana; Bhavishya; Tulana | one display row per window | **projection over the publication manifest** (concept §3.4); the 0.5-on-missing default and top-750 cut go | unowned |
| `ka_jivana_parva` | 100 rows, 2026-08-13 | STORY | daśā-anchored chapter hierarchy with LEL pinning | **correct now (serving) + projection later**: chapters = F2 hierarchy; density = aggregated assertions per period; never a count from a dead table (§8 F-L2) | unowned |
| `ka_bhavishya_lekha` | 0 rows | AHEAD projections; L4 `ph_nimitta`; L4 `phala_anchors.bhavishya_id`; **the writer itself reads L4 `phala_anchors`** (an upward read, like Kṣetra's rectification read) [S] | the testable-prediction intent | **supersede-after-migration by `issued_forecast`** (concept §2): canonical identity per event, immutable, Samīkṣā-registered; "probability tiers" retired for typed calibration status | unowned |
| `ka_taranga` | 92,412 rows, 2026-08-13 | registry capability `query_activation_waveform` only; no MCP facade; no Vidhi primitive reaches it [S] | monthly waveform as a shape over time | **projection of the forecaster's compact evaluator** (∫λ per month, domain scope only — the W2 split); event-class half retired | unowned |
| `ka_kshetra` | 8,570,075 rows, 0 snapshots | `mi_bhara` reads `kala_field`, `_null`, `_weight_versions`; `kala_field_snapshots`/`_skill` feed every facade envelope; `_windows` only behind a default-off flag; **nine of fifteen tables have no consumer at all** [S] | the only asset emitting a *shape over time* with components; the chance test; salience axes | **the forecaster** (F-2); S0/S1 knot producer held (B8-6); dense field → compact evaluator after byte-equality | Suvarṇa Track F / Kṣetra lane |

Twenty-five rows, no deletions. Count by disposition: retain 4 · correct/enrich 4 · adapter (gated) 3 · projection 5 · integrate 1 · supersede-after-migration 4 · the three stages 3 · historical 1. Eleven assets stop being independent writers; their outputs survive as views over the pipeline.

---

## §6 · The layer as one system

### 6.1 What the three-engine shape cost

The focus-families note and the concept note both measured it [S]: three recomputations of the sky, three promise graphs, three clock readers, three output shapes, and a reader fan-out wired to whichever was alive. Two consequences the per-asset exercises could not see from inside one asset:

1. **The declared graph is not the real graph.** The live registry still says `ka_taranga` depends on `ka_avadhi`, `ka_kala_darshana` on `ka_kalasutra`, and `ka_sangam` on the materialised `ka_gochara`; the code reads none of those [S][L]. It omits `ka_vedha_gochara → ka_sangam`, Gochara windows → Kṣetra, and Kṣetra's upward read of L4 rectification [S]. Every scheduler decision, blast-radius statement and staleness flip is computed from the wrong map (§8 F-L4).
2. **Cascade coupling turned one L2 rebuild into a layer-wide wipe.** Eight `ON DELETE CASCADE` keys into `bodha_msr_signals` emptied five Kāla tables when `bo_laksana` was rebuilt on 2026-09-08, and the 2026-10-05 MSR rebuild orphaned the bridge [L]. N-32 removes the keys; it does not restore the rows. Until the pipeline rebuilds in wave order, the centre of the layer stays dark by design.

### 6.2 The target: every asset placed

The concept note designed the pipeline for three assets and said (§11) the shared substrate has no brief type and the per-asset template does not fit. This section is the whole-layer placement it asked for.

```
FOUNDATIONS (shared, generation-scoped, no stage owns them)
  F1 promise graph      ← L1 facts + versioned L0 rules; L2 MSR/CGM attach      [replaces ka_yojaka; Kṣetra S2]
  F2 clock service      ← L1 chart_dashas; applicability per system; correct σ  [ka_dasha_kala grows into it; ka_avadhi becomes a view]
  F3 outcome record     ← LEL events + Samīkṣā resolutions; frozen data roles   [L5-owned; Kāla reads only through roles]

STAGES (evaluated, in order; each writes assertions over the shared object)
  JUDGE   Gochara 5.0   sky once · contacts · relationship records · rule paths · valence · permission · vedha intervals · annual objects
                        inputs: ka_graha_sancara (sky), ka_vedha_gochara, ka_gochara_resonance (folded), moorti/kota (gated adapters), sudarśana (step 2)
  JURY    Saṅgam        declared witness groups · evidence algebra · segment agreement D(W) · turning points · contests · claim attachment
                        inputs: judge assertions, F1, F2, admitted schools' assertions
  NEGATIVE SPACE        obstruction / cancellation / exception as the judge records them → six typed states   [ka_vighnakara folds here]
  FORECASTER Kṣetra     compact field + ∫λ · alignment null · sourced priors · odds only under a declared event model · salience axes
                        inputs: judge + jury assertions, F2, base rates, F3 through roles only

PUBLICATION
  atomic manifest per generation (natal facts, conventions, F1, F2, judge, jury, forecaster, rule registry, cutoff) → compare-and-swap
  issued_forecast objects → Samīkṣā (prospective only)                              [replaces ka_bhavishya_lekha]

VIEWS (projections; no independent truth; one query answers "what is served")
  NOW · AHEAD · EXPLAIN · PRIORITY (ka_tulana re-based) · ELECT (ka_muhurta_seva) · STORY (ka_jivana_parva re-based) · RITUAL · UPĀYA
  kala_darshana = the published confluence view · kala_activation = per-signal intervals view · kala_taranga = monthly ∫λ view · kala_avadhi = period dossier view
```

Why this and not the alternatives considered:

| Alternative | Why not |
|---|---|
| Keep twenty independent writers and brief each on the asset template | The value lies at the boundaries (agreement, independence, negative space, one manifest). The September master plan, the Gochara plan (§1.5 G-2/G-3), the blueprint (§3.4) and the concept note (§11) each parked exactly these as "layer-level, no owner". A twenty-first brief would park them again. |
| Make Kṣetra the universal substrate (VA §7, 2026-09-11) | Superseded by the master plan (T6, "not the universal product brain") and by F-2, which makes it the odds/attention stage. Its dense field is 5.36 GB of unserved rows with a known axis defect. |
| Retire Saṅgam into `kala_field` (ŚAḌ-DARŚANA W6) | Rejected by F-2 option 2; the retirement line still needs formal withdrawal (coordination item). |
| Rebuild the existing chain once on `'3.0'` as a stopgap so NOW/AHEAD show something | Would serve convergence over a transit generation that failed its own protocol, re-create 99 % dangling references at the next L2 rebuild, and spend the one build slot the pipeline needs. Offered to the native as a trade-off, not recommended (§9 D-3). |

What the placement preserves: every table's data until its successor is accepted; every asset id (the strangler cutover keeps `ka_gochara`/`ka_sangam`/`ka_kshetra` ids per concept §8.6); the FROZEN writer contract (each stage is a `@register` `WriterBase`); the Gochara frozen spec; all Kṣetra rulings including B8-6.

### 6.3 Synergy obligations, stated as contracts not hopes

Each edge below is the kind of input-use contract the skill requires (consumer question · exact fields · operator · proof). Full field lists belong in the stage briefs; the obligations are fixed here.

| Edge | Operator | Proof that the edge does work |
|---|---|---|
| judge → jury | assertions with `roots`, `role`, `used_for_selection` | reused root yields zero increment (mutation test); P8-selected window never G-J-corroborated |
| F2 → every stage | `period_context` with σ and applicability | boundaries move together under a birth-time perturbation; an inapplicable system is silent, not dissenting |
| F1 → judge/jury/forecaster | signed mechanism graph with `missing_fact` vs `evaluated_empty` | removing an L2 signal attachment changes nothing in the universe of promise; removing an L1 fact does |
| negative space → forecaster/views | six typed states | `evaluated_silent` never becomes "expect quiet"; `obstruction_active` names what, by what, until when |
| forecaster → PRIORITY/ELECT | salience axes, coverage, alignment null | a universally active witness ranks nothing higher; an empty table ranks nothing |
| judge coverage → every "no window" | coverage manifest | a window just outside the searched partition is `unsearched`, not `none` |
| L5 (`mi_bhara`, `mi_sankalpa`, `mi_adhilepa`) ← publication manifest | bind by manifest id, never `LIMIT 1` | changing an unpublished candidate changes no L5 read |
| L4 (`ph_nimitta`, `ph_pratikara`, `ph_muhurta`) ← issued forecasts and jury contests | by canonical forecast id | a rebuilt candidate never resets a delivered forecast (U10) |

---

## §7 · Question → capability → readiness

The approved strategy's L3-Q01–Q13 is the ratified acceptance baseline; this review does not add a new list. For each, the pipeline component that answers it and the earliest point at which the native can be served an answer, in dependency order (not dates). "Served" here means the honest tool answer changes from an empty to a populated, qualified result.

| Q | Question (short) | Answering component | Served… |
|---|---|---|---|
| Q01 | What is active now, and why | judge windows + F2 + negative space | after `'5.0'` flips (judge alone can answer this) |
| Q02 | Nearest eligible window vs better-supported later one | judge ranking by exposure; jury D(W) for "better supported" | nearest: `'5.0'`; better-supported: jury |
| Q03 | Does a named configuration have a complete activation route | F1 + judge rule paths | F1 + `'5.0'` |
| Q04 | Why activity coexists with strain | negative space + signed F1 | F1 + negative space |
| Q05 | Why timing methods disagree | jury contests + declared groups | jury |
| Q06 | How this chapter differs from the last | F2 hierarchy + per-period assertions (STORY re-based) | F2 + judge (chapter view); mechanism composition needs forecaster |
| Q07 | Which domains interact over time | jury turning points | jury |
| Q08 | Is "no window" a real negative | judge coverage manifest | `'5.0'` |
| Q09 | Birth-time / convention sensitivity | F2 scenarios | F2 (after the covariance fix) |
| Q10 | Feasible initiation intervals | ELECT over qualified methods | today (general); personal suitability after judge |
| Q11 | What observations fit or fail | F3 + Samīkṣā | after the first prospective issued forecasts close |
| Q12 | What is missing | forecaster omission detection; jury silence states | forecaster |
| Q13 | Does the decisive field survive to the person | publication manifest + density contracts | with each stage's serving packet |

Today's score against this baseline, honestly: Q10 partially. Everything else is `not_computed`. After the judge flips: Q01, Q02 (nearest), Q03, Q08. After the jury: Q05, Q07, Q02 (better-supported). After the forecaster: Q06 (full), Q12. Q11 depends on prospective data and will read `insufficient_evidence` for a long time regardless of engineering.

---

## §8 · Findings new to this review

Each finding names its evidence and its class. "Class" uses the project's own doctrine: §N.5 (L1 authority), §N.7 (narration fidelity), §N.8 (earned signal), B.10 (no fabricated computation).

| ID | Finding | Evidence | Class | Disposition |
|---|---|---|---|---|
| F-L1 | The activation bridge is 99 % dangling: 50,678 predicates, 531 resolve to a signal that exists for this chart; MSR was rebuilt 2026-10-05 (126,449 signals, 3 builds) | [L] same-chart join, 2026-10-06 | staleness after an upstream regeneration; expected under N-32 until the downstream wave | No rebuild (concept §8.4); record in the Suvarṇa dangling-reference measurement; F1 supersedes |
| F-L2 | STORY serves per-chapter `high_convergence_count` (8,838 across 43 chapters) and `avg_effective_score` computed 2026-08-13 from `kala_convergence`, which has 0 rows for this chart; no staleness flag, tier `structural_prior` | [L] `kala_story_get`; `kala_jivana_parva.computed_at`; `kala_convergence` count | §N.8 (a figure with no live detector behind it) · §N.5 (derived value outliving its source) | **Fix now, serving-only**: null the two fields with reason `source_table_empty_for_chart` or re-derive at serve time; no data change (§9 D-2) |
| F-L3 | NOW's `gochara_narrative.active_windows` lists ten `'3.0'` rows 2024-02-05 → 2034-01-30 with peak dates and signed intensities as "active windows"; the same rows are `is_timing_window=false` in `gochara_forecast_get` and carry no resolution disclosure in NOW | [L] both tools | §N.6 (density flattening) · PK-R-1 (era rows are context, never timing) | **Fix now, serving-only**: carry `resolution_disclosure` into NOW; rename the block or filter to `is_timing_window=true` (which today yields zero) (§9 D-2) |
| F-L4 | Live registry still declares the false edges `ka_avadhi→ka_taranga`, `ka_kalasutra→ka_kala_darshana`, `ka_gochara→ka_sangam` and omits `ka_vedha_gochara→ka_sangam`, Gochara windows→`ka_kshetra`, L4→`ka_kshetra` | [L] `asset_registry.depends_on`; [S] strategy §6.3; focus families §3.3 | registry/real-graph disagreement (GA.1 class) | One surgical registry migration (Suvarṇa Track E range), verified, before any wave touches these assets |
| F-L5 | Two staged Pravāha rows (`ka_gochara_v4_41_candidate`, `ka_gochara_v5`) carry `domain=null`, `rung=null` | [L] registry | catalogue contract gap (NIRMANA I9/§8.3) | Pravāha to stamp at the small-test registry step (1304 is already touching this row) |
| F-L6 | The served transit generation `'3.0'` has no timing windows in the next year (8/8 `is_timing_window=false`) and, under protocol v2.1, no separation from random (T-cover 68.1 % vs 68.6 %; T-FP fails 8/9 adverse classes at 99.87 % admitted-day fraction); the forecast tool returns 246 KB for 8 rows | [L] tool; [D] BASELINE_3_0_v2_1 via focus families §1.5 | served value ≈ context only; response budget | Known to Pravāha (J2 decides); this review adds: every consumer of `'3.0'` must label it `context_only`; trim `term_breakdown` under the response budget |
| F-L7 | Vedha, moorti and kota overlays cover a rolling window only (2026-07-29 → 2027-11-01); no consumer discloses the horizon | [L] min/max window on the three tables | coverage conflated with absence | Declare the horizon in every consumer's coverage block now; century coverage arrives with the judge |
| F-L8 | Two overlays are served while their method identity is contested and uncited: tithi-praveśa (Moon-longitude return vs Sun–Moon angle; `not_in_corpus` citation on the served row) and moorti (27-nakṣatra offset vs 12-house Moon table); NOW says tithi-praveśa is `computed`, AHEAD says `not_in_corpus` | [L] NOW/AHEAD rows; [A] VA §5 F5 | method qualification before consumption (strategy §6.1 A06/A09) | Gate: `method_contested` on served rows until the corpus custodian adjudicates (§9 D-5); reconcile the NOW/AHEAD coverage states |
| F-L9 | Kota ring table is a tier-(iii) transcription; every served row says `uncited_extension=true`; nothing downstream reads it | [L] NOW rows; [S] strategy A07 | honest but idle | Keep served as is; judge soft factor only after a primary citation (ADJUDICATION-9) |
| F-L10 | `ka_avadhi` has two reproducible failed rebuilds with an untested error-mislabel hypothesis (#2581/#2582); its rows are from 2026-08-12 | [S] stocktake §4; [L] `computed_at` | unresolved operational failure | Becomes moot if avadhi is a view over F2 (§9 D-9); otherwise fund the transaction-local diagnosis |
| F-L11 | Taranga's W2 decision (domain waveform legitimate, event-class half degenerate) is not implemented; the writer builds both | [A] stocktake §6.4; [S] strategy A18 | decision-to-code gap | Fold into the forecaster's monthly ∫λ view (domain scope only) |
| F-L12 | No asset owned cross-clock agreement or witness independence; the concept note §5.2–5.4 is the first design | [A] blueprint §3.4; Gochara plan §1.5 G-2 | layer-level capability gap | Confirmed owned by the jury; this review places it (§6.2) |
| F-L13 | Kṣetra: 8,570,075 rows on a time axis offset ≈ 15.9 y; 0 snapshots; chart-wide suppression where route-scoped was documented; rebuild refused by design | [L] counts; [A] focus families §3.2; Kṣetra plan §0 | correctness + unserved capital | Forecaster stage per F-2; W7 storage per F-1 (open) |
| F-L14 | σ_t adds birth-time contributions in quadrature although both derive from one dT (`services/ka_kshetra/uncertainty.py:268–276`); every served uncertainty inherits it | [S] via concept §3.2 (verified there) | numerical defect in production | F2 fixes once; until then NOW's lite bound is the honest placeholder |
| F-L15 | `kala_gochara_contacts` and `ka_gochara_contact` are both 0 rows; the Contact object exists only as schema | [L] | present ≠ populated | Arrives with `'5.0'`; no consumer may assume contacts exist |
| F-L16 | L5 `mi_bhara` binds to an unpublished Kṣetra snapshot with an unordered `LIMIT 1`; `mi_sankalpa`/`mi_adhilepa` also read Kāla | [A] Kṣetra plan §0; [S] consumer grep | downstream binding to unqualified state | U10 packet: bind by manifest; disposition `qualify` pending Kṣetra (N-21) |
| F-L17 | L4 `ph_nimitta`, `ph_pratikara`, `ph_muhurta` read `kala_convergence`/`phala_anchors` chains that are empty for this chart; sealed L4 rows cascade from `kala_convergence` | [S] consumer grep; strategy §4.2 | downstream reads of an empty upstream | Already fenced as family readers (FAMILY_ASSETS.json); confirm `not_computed` propagation in each |
| F-L18 | Nine of twenty-two active identities have no owner under the current campaigns: Pravāha owns the Gochara family; Suvarṇa Track F owns Saṅgam and Kṣetra design; the seven readers, `ka_avadhi`, the three services and `ka_sudarshana_varsha`/`ka_tithi_pravesha`/`ka_kota_chakra` are "family readers" or unassigned | [S] FAMILY_ASSETS.json; focus families §5 | ownership gap | §9 D-7 |
| F-L19 | The layer's main views do not reach the product's two main doors — stated by layer: *portal* — no page reads a `kala_*` table (`ArrivalLine.tsx` is a structural placeholder); *web floor* — the Paripraśna engine resolves `kala_windows_get`, `kala_muhurta_get`, `kala_yoga_activation_get` and counts 29 unmapped live-tool entries in the generated bridge, including `now_read`/`ahead_read`/`priority_read`, `elect_read`, `story_read`, `ritual_read` and the `gochara_*` tools (`compiled_floor_adapter.ts:290–300`; `web_tool_bridge.generated.json`); *registry* — registered L3 capabilities do exist and answer direct callers. "No page reads a table" does not prove no indirect product retrieval; the "11 intents" count is the author's | [S] code trace; bridge `unmapped = 29` re-read 2026-10-06 | served-evidence gap (strategy Q13; U11) | Channel packet before any claim that a Kāla view is "served to the native" through the product doors; the bridge is generated, so this is a mapping fix, not a rebuild |
| F-L20 | `ka_tulana`'s ranker is never called by `call_priority_ranking` (which ranks `bodha_msr_signals ⨝ kala_activation` directly); the only caller is `service_probes.py`; the editorial attribution credits `ka_tulana` for PRIORITY | [S] `call_service_wrappers.ts:708`; `producer_editorial_review.ts:386` | shelf service presented as a consumer's engine (§N.8 class, attribution) | Decide: wire or retire (§5); correct the four wrong editorial attributions (avadhi→life_arc, bhavishya→prospective_ledger, kshetra→predictive_anchors, tulana→priority) |
| F-L21 | `kala_taranga` is **registry-only**: `query_activation_waveform.ts` is a real table reader and registered capability (summary and bounded drill), but there is no MCP facade and the Vidhi `taranga_curve` primitive points at `kala_bundle_get`, which does not read it; `kala_gochara_windows_v2`, `kala_gochara_v2_build_state`, `kala_convergence_staging`, `gochara_v3_calibration`, `kala_field_gof` and the `lel_derived=true` rows of `kala_insights` have no consumer **within the searched code scope** | [S] code trace, bounded to the searched registration paths | present-but-unserved-on-the-intended-floor capital | Fold into §5 dispositions; no deletion |
| F-L22 | Two Gochara v3 annual mechanisms (`w27b`, `w27c`) name `kala_tithi_pravesha` and `kala_sudarshana_varsha` as inputs but the production `ClassContext` never carries them, so both evaluate on an empty list; `ph_muhurta` returns `{}` explicitly and falls back to a documented neutral 0.5 transit score; `ka_bhavishya_lekha` reads L4 `phala_anchors` **to find bhavishya ids referenced by outcomes and preserve them** | [S] `w27_annual_stack.py:332,465`; `ph_muhurta.py:358–376`; `ka_bhavishya_lekha.py:262–276` | declared-but-dead inputs; documented neutral default; an upward read that is a protection, not a defect | The first two are corrections in the owning packets. **The Bhavishya read is not a one-line cleanup**: removing it without a replacement reference-protection contract would weaken outcome preservation (plan R-11) |

---

## §9 · Decisions for the native

Each decision is stated with the options, the recommendation and who executes if adopted. Nothing below executes on this document.

| ID | Decision | Options | Recommendation | Routed to |
|---|---|---|---|---|
| D-1 | **Scope of the pipeline concept.** Does the judge/jury/forecaster + F1/F2/F3 architecture govern the whole layer, or only the three families? | (a) whole layer: the seven readers, avadhi, taranga and the overlays become projections/adapters per §5; (b) three families only, the rest briefed per asset on the asset template | **(a).** The value the layer lacks lives at the seams no single asset owns. (b) re-parks it. Per-stage briefs follow; a "shared substrate" brief type is written once (concept §11). | native seals; Suvarṇa Track F extends scope; Pravāha informed |
| D-2 | **Serving honesty now.** Fix F-L2 (stale convergence counts in STORY) and F-L3 (era rows as "active windows" in NOW) before the pipeline, serving-layer only, no data change? | (a) now, two small PRs with golden tests; (b) wait for the re-based views | **(a).** Both are §N.8-class: a figure or a label with no live detector behind it, served today to the native. Cheap, reversible, no table touched. | whoever owns `platform-mcp/src/tools/kala_views/` (unowned → Suvarṇa Track I) |
| D-3 | **Interim stopgap or honest dark.** Rebuild yojaka → saṅgam → … once on `'3.0'` so NOW/AHEAD show windows until the pipeline lands? | (a) no stopgap; the native sees honest empties until the judge flips; (b) one stopgap rebuild, labelled `context_only`, snapshot first | **(a).** A stopgap would serve convergence over a generation that failed its own protocol, re-orphan at the next L2 rebuild, and take the single build slot. The cost is real: no forward windows for the duration of Pravāha J2. Stated so the native chooses knowingly. | native |
| D-4 | **Century materializer disposition.** | (a) formally supersede by the judge's compute-once sky substrate + compact evaluator, data retained as capital, hold retired for that disposition only; (b) keep the hold indefinitely as "deferred" | **(a).** The strategy says deferral alone cannot elevate an asset; the judge now owns what the century computed. The hold's owner is the native (#2562). | native (hold owner) → Pravāha records |
| D-5 | **Contested overlays.** Tithi-praveśa and moorti are served while their method identity is disputed and uncited. | (a) mark served rows `method_contested` now; corpus custodian adjudicates; (b) stop serving until adjudicated; (c) keep serving as is | **(a).** Honest tier over silence or false confidence. Also reconcile NOW `computed` vs AHEAD `not_in_corpus` for tithi-praveśa. | corpus custodian (counts); serving owner (flag) |
| D-6 | **Overlay horizon.** Vedha/moorti/kota cover ~15 rolling months. | (a) declare the horizon in every consumer's coverage block now; century coverage via the judge; (b) extend the three writers to century now | **(a).** Cheap; the judge's `vedha_interval_relation` and sky substrate make century coverage free later. | serving owner; Pravāha for the judge |
| D-7 | **Ownership of the non-family assets** (nine with no owner, F-L18). | (a) extend Suvarṇa Track F to "the Kāla pipeline" with one Architect lane per stage plus one "views" lane; (b) create a separate Kāla-readers session; (c) leave to Suvarṇa's generic Tracks I/B | **(a).** One owner per stage matches §6.2; the readers are projections of stages, not peers. | Strategic Suvarṇa (N-28) |
| D-8 | **L4/L5 readers.** `ph_nimitta`, `ph_pratikara`, `ph_muhurta`, `mi_bhara`, `mi_sankalpa`, `mi_adhilepa` read empty or unpublished Kāla state. | (a) disposition `qualify` pending their stage (N-21 already offers this for the two L5 readers); (b) accept Kṣetra on the L5 critical path | **(a)** for all six, with the manifest-binding packet (U10) as their re-entry condition. | Strategic Suvarṇa |
| D-9 | **`ka_avadhi`.** | (a) fold into F2 as the period-dossier view, retire the writer after migration, drop the failed-build diagnosis; (b) fund the transaction-local diagnosis and rebuild | **(a).** Its content is F2 + F1 by definition; a second clock reader is the three-engine mistake again. | Track F (F2 lane) |
| D-10 | **`ka_taranga`.** | (a) fold into the forecaster's monthly ∫λ view, domain scope only; (b) implement the W2 split in the existing writer | **(a).** The waveform is an integral of the field; a separate convolution is a second forecaster. | Track F (forecaster lane) |
| D-11 | **Channel reach (F-L19).** The product's two main doors cannot reach the Kāla views. | (a) a channel packet now: regenerate the web tool bridge so the Vidhi floor primitives resolve, and wire one portal surface (the arrival line) to `kala_now_get`; (b) wait until the pipeline has something to show | **(a) for the bridge, (b) for the portal.** The bridge is a generated mapping and its absence falsifies every "served" claim; the portal surface should first show the honest-empty state the tools already produce, which is itself the product promise (graceful incompleteness, Product §10.2). | Paripraśna owner (bridge); portal owner |

---

## §10 · First slice and sequence (dependencies, not dates)

Consistent with the concept note §8.2 and the strategy's wave gates; nothing here is authorised by this document.

0. **Serving honesty and reach (D-2, D-5, D-6, D-11a).** Serving-layer changes with golden tests and a mutation test each, plus the regenerated tool bridge; no table, no migration, no build. Independent of everything else; can land this week if ruled.
1. **Registry truth (F-L4, F-L5).** One surgical, verified migration correcting `depends_on` for the six edges and stamping the two staged rows. Precedes any wave that dispatches these assets.
2. **Judge: `'5.0'` small test → gates → J2 → N-FLIP** (Pravāha; not this review's to sequence). Q01/Q02-nearest/Q03/Q08 become answerable.
3. **Foundations F1/F2/F3 specs** and the N-32 storage addition (atomic manifest), routed to the Pravāha steward (F1 touches the frozen judge) and the Suvarṇa steward (manifest). F2 lands the σ fix once.
4. **Enrichment step 1** (repair existing semantics) as Gochara amendments; the jury's and negative-space doctrine notes; Astra review; reconcile.
5. **Jury + negative-space specs and oracles → freeze**; build candidate-only on a rehearsal DB; retrodict judge-only vs judge+jury (G-J first); four-way verdicts.
6. **Views re-based** (STORY, NOW, AHEAD, PRIORITY) as projections; `kala_avadhi`, `kala_activation`, `kala_darshana` become views; writers retired after migration with data retained.
7. **Forecaster** (Kṣetra) per its ten rulings and F-1 (W7 storage); compact evaluator; byte-equality before any dense-row deletion.
8. **Enrichment steps 2–4** in the native's order, each through the same review loop.

**First vertical slice to prove the whole shape** (one chart, one question): Q01 "what is active now, and why" served from judge `'5.0'` windows + F2 period context + negative-space states, through `kala_now_get`, with the publication manifest id on the response and a sentinel distinction (one obstruction state present only in the negative-space table) demonstrably reaching the served reading. Producer-ready is not value-proven; the slice is proven only when the sentinel is in the tool output.

---

## §11 · Non-claims, limits and search boundaries

- No predictive validity is claimed or implied for any component. The one measured generation (`'3.0'`) did not separate from random under the frozen protocol.
- All row counts and served outputs are for chart `482012f1` at 2026-10-06 07:05 UTC and are re-measurable quantities, not durable facts. No other chart was inspected.
- The working tree is on `campaign/nirmana-autonomous` @ `badc3f9bc`, 569 commits behind `origin/main`; every repository claim above cites the ref it was read from. This file is written into that tree; where it is committed is the native's call.
- Consumer searches (the code-trace digest, at `c751f3bd8`) covered `platform/src/**`, `platform-mcp/src/**` and `platform/python-sidecar/{pipeline,services,brahmagyan,routers}/**`, excluding tests, `generated/`, `migrations/` and `scripts/` except where a script is a table's only writer. "Consumer" means a real SQL read, a DB-proxy read, or a capability call that leads to one; comments, deletes and LIMIT-0 probes do not count. "No consumer found" means none in that scope; dynamic reads were not exhaustively traced.
- Three sub-agent digests were used: the prior exercises (worktree `cooperative-racer`), the September studies (commit `d1560e321`), and the code trace. Claims marked [A] were not re-read by the author.
- Suvarṇa's launch state (N-1) and Pravāha's live tracker were not read; their committed records on `suvarna/hq` and `origin/main` were.
- The MSR rebuild on 2026-10-05 was observed by `computed_at`; which L2 writer ran, and under which campaign, was not determined and is not asserted.
- This review did not re-derive any classical rule, re-adjudicate any method identity, or re-score any held-out event.

## §12 · Sources

Repository (ref in brackets): `MADHAV_PRODUCT_DEFINITION_v3_0.md` §3.10, §9, §12 [origin/main]; `briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` §2–§7 and `…_L3_KALA_EXECUTION_BRIEF_v1_0.md`, `…_L3_CURRENT_STATE_AND_DISPOSITION_v1_0.md` [origin/main]; `briefs/nirmana/L3_STRATEGIC_STOCKTAKE_v1_0.md`, `L3_KALA_VALUE_ARCHITECTURE_AND_RATIONALIZATION_v1_0.md`, `L3_KALA_CONSUMER_FIRST_MASTER_PLAN_v1_0.md`, `L3_KALA_CROSS_LAYER_LEVERAGE_RESEARCH_v1_0.md` [d1560e321]; `briefs/nirmana/l3_autonomous/**` — the Gochara, Kṣetra and Saṅgam plans, ruling sheets, reviews, `KALA_ASSET_ELEVATION_PLAN_TEMPLATE_v2_0.md`, `KALA_IO_USE_MATRIX_v1_0.md`, `audit/KALA_DATA_CENSUS_v1_0.md`, `STATE.md` [cooperative-racer @ c751f3bd8]; `briefs/suvarna/SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` v1.4, `SUVARNA_CAMPAIGN_PLAN_v1_5.md`, `control/suvarna/state/DECISIONS.jsonl` [suvarna/hq @ 79ab6b509]; `control/FAMILY_ASSETS.json` [origin/main]; `briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_4.md`, `L3_FAMILY_COORDINATION_v1_0.md`, `measurement/EVALUATION_PROTOCOL_v2_1.md` [eea2610d0 / 317bc0d7b / 77ff058bc]; `briefs/l3_families/KALA_PIPELINE_CONCEPT_NOTE_v1_1.md` and `reviews/RECONCILIATION_KALA_PIPELINE_CONCEPT_v1_0.md` [l3/sangam-final @ fbbbb9414]; `L3_KALA_CLOSE_v1_0.md`, `L3_KALA_TEMPORAL_ARCHITECTURE_v1_0.md`, `llm_consumption_audit/briefs/kala_elevation/SHAD_DARSHANA_CLOSE_v1_0.md`, `KALA_SIX_VIEWS_DESIGN_v2_0.md` [working tree]; `CLAUDE.md` v7.4 §N.5–§N.8.

Production, read-only, 2026-10-06 07:05Z: `asset_registry` (25 `ka_*` rows); chart-scoped counts on every `kala_*`, `ka_gochara_*`, `gochara_resonance_map` table; `computed_at`/`bound_at` extrema; `kala_gochara_authority`; the predicate→`bodha_msr_signals` same-chart join; `bodha_msr_signals` extrema. MCP tools called: `kala_now_get`, `kala_ahead_get`, `kala_priority_get`, `kala_story_get`, `gochara_forecast_get`.
