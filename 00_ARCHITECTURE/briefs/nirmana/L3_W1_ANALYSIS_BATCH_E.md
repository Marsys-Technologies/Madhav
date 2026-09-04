---
artifact: L3_W1_ANALYSIS_BATCH_E
canonical_id: L3_W1_ANALYSIS_BATCH_E
version: "1.0"
status: DRAFT-FOR-W2
produced_on: 2026-09-05
campaign_id: nirmana-elevation
layer: L3
batch: E
theme: "The synthesis / artifact spine — convergence, obstruction, activation, display, life-arc, projection"
assets:
  - ka_sangam
  - ka_vighnakara
  - ka_kalasutra
  - ka_kala_darshana
  - ka_jivana_parva
  - ka_bhavishya_lekha
measurement_chart: 482012f1-710e-4a25-994a-93821f5871aa
corroborating_charts:
  - 1c826d5a-41cb-4450-b4dc-59d440e5f75a
  - cb73cd3d-9eba-4220-9902-0de91566e980
---

# L3 W1 ANALYSIS — BATCH E: the synthesis/artifact spine

All numbers below come from `q.sh` SELECTs run 2026-09-05 against production, or from reading
the writer/serving source at `/Users/Dev/nirmana-s/l3`. Anything I could not measure is written
"unmeasured". VERIFIED vs INFERRED is marked where it matters.

---

## Batch summary

1. **The batch's root defect is a score-commensurability failure, not a data gap.**
   `kala_convergence.convergence_score` is produced by four different modes on four
   incompatible scales. Mode C (`mode_c_subsystem_period`, engine.py:1284) computes
   `score = dignity_score × severity` — a product of **two catalog constants**, no temporal
   engine consulted, `orb_strength` hardcoded `1.0`, `independent_current_count = 1`. Mode A
   (the daśā-prior funnel that actually consults 12 currents) tops out at **0.3086** on the
   native chart; Mode C tops out at **1.0000** and averages **0.7913**. Every downstream
   consumer ranks `ORDER BY convergence_score DESC`, so **the mode carrying the least
   agreement evidence monopolises every served surface.** Measured: the top 200 rows by score
   for chart `482012f1` are **200/200 Mode C**; `kala_darshana`'s 750 rows are **750/750 Mode
   C**; `kala_bhavishya`'s 100 projections descend from those. Mode A/B windows — the only
   rows that carry per-engine testimony at all — are structurally unreachable through the
   ranked surface.

2. **The Temporal Concordance arbiter is ~60% pre-built, in three places that do not know
   about each other.** `ka_sangam` already computes multi-engine agreement (12 weighted
   currents + `independent_current_count` I-22 coupling discount + `cross_dasha_agreement`
   over daśā systems); `kala_explain_get` already emits a `school_voices[]` array with a
   `{school, state, empty_reason, agreement, claim}` testimony shape (`kp_school_voice.ts`,
   `agnivasa_convention_b_voice.ts`) plus a flag-guarded `a5_gochara_agreement`; `kala_now_get`
   already fans out to ~15 temporal engines with a per-engine `*_reachable` honesty flag. What
   is missing is (a) one shared testimony type — three different stance vocabularies exist
   today (`concurs|dissents|not_comparable`, `agrees|diverges|not_comparable`,
   `concurs|dissents|insufficient_data`), (b) a top-level `concordance` verdict, and (c) the
   silent-vs-dissenting distinction inside `ka_sangam` (see item 3). **This is an extension,
   not a new build.**

3. **`ka_sangam`'s agreement machinery cannot express disagreement, and 38% of its weight
   budget is dead.** Every current is a supporting term in `[0,1]`; a current that is
   unavailable and a current that says "no" both contribute `0.0`. Measured over all 1,994
   Mode A/B rows on the native chart: `c_panchanga_quality` **100.0% zero**,
   `c13_school_consensus` **100.0% zero**, `c7_ashtakavarga_potency` **100.0% zero**,
   `c12_tajika_reinforcement` **100.0% zero**, `c8_eclipse_proximity` **100.0% zero**,
   `c_cross_dasha_agreement` **54.1% zero**; `c11_vedha_factor < 1` on **0.0%** of rows
   (the necessary-side veto never fires); `trigger_suppressive_applied > 0` on **0.0%** of
   rows (the D-3 T-6 TRIGGER never fires). Five of those are traced to concrete, fixable code
   defects (F-SANGAM-3 … F-SANGAM-7). Sum of permanently-zero supporting weights = **0.380 of
   1.000**. This is why absolute `confidence_label` degenerated and JL-014 had to bolt on a
   within-chart percentile tier.

4. **All six assets are `catalog_status='DRAFT'`, and the label is stale for all six.**
   Every target table has real, registered serving-plane consumers (§ per-asset item 6). Two
   of them feed headline product surfaces: `register_d9_judgment.ts` (`judgment_query`) and
   `register_d8_assess_domain.ts` (`assess_career`/`assess_wealth`/…) both read
   `kala_activation`. `L3_kala/index.ts`'s own header still describes
   `query_obstruction_periods` and `query_temporal_view` as "STUBBED-PENDING-DATA, 0 rows" —
   they serve 1,283 and 1,500 live rows. D-SERVICE finding, six instances.

5. **The highest-value NULL in the batch:** `kala_activation.orb_strength` and
   `kala_activation.convergence_score` are **99.6% NULL** (measured, n=335,403). They are
   populated only where a predicate's `signal_id` happens to have a `kala_convergence` row —
   and `ka_sangam` only ever selects ≤200 near + ≤60 lifetime predicates out of 50,104. Four
   designed consumers read exactly those columns: `query_temporal_activation.ts` **orders by
   `orb_strength DESC NULLS LAST`** and buckets families by `max_orb_strength`;
   `register_d9_judgment.ts` picks its best activation row by `convergence_score`;
   `register_d8_assess_domain.ts` serves both; `ahead.ts` collapses to the highest-orb row per
   signal. All four are ranking on a column that is NULL 99.6% of the time. The honest
   alternative already exists on the same rows: `dasha_activation_proximity_score` is **0.0%
   NULL**.

6. **`ka_kalasutra`'s 671K rows are honest, not accretion — but the 33s estimate is a
   14.8× under-estimate.** Verified: the writer does `DELETE FROM kala_activation WHERE
   chart_id = %s` before insert (§N.3 compliant); a `UNIQUE (chart_id, signal_id,
   ayanamsha_id, source_citation)` index exists; three independently-built charts land at
   335,403 / 336,093 / 335,447 rows — a stable per-chart figure, which accretion could not
   produce. Measured build p50 since 2026-08-01: **486.9 s** (min 416.6, max 620.4) against
   `estimated_seconds = 33`. Storage: ~1,644 bytes/row of jsonb, of which ~85% is the SAME
   `active_dasha_periods_jsonb` + `activation_predicted_dates_jsonb` payload repeated across
   the ~6.7 period rows CR-109 fans out per predicate.

7. **The layer's headline predictive artifact is degenerate.** All 100 rows of
   `kala_bhavishya` for the native chart share **one peak_date (2027-10-20)** and **one
   effective_score (0.700)**; 94/100 are `domain='character'`; `projection_rank` 1–100 is an
   arbitrary tie order. Each row ships its own falsifiability hook ("Observable within ±21
   days of 2027-10-20") — 100 separately-falsifiable claims that are one claim repeated. And
   the narrative asserts "High probability (>=70% convergence)" and "This projection is
   probabilistic and calibrated" over a substrate that stamps itself
   `tier_basis = 'relative_uncalibrated'` on **100%** of rows.

---

## PART 1 — THE TEMPORAL CONCORDANCE CONTRACT: EVIDENCE BASE (D-TIME, plan §2 / §5 L3(a))

### 1.1 Temporal engine inventory

Every engine in the system that answers a time-indexed question. "Question" is the
one-sentence form the arbiter would key on. Row counts are `pg_class.reltuples` estimates or
exact counts where noted; ranges are measured where stated, otherwise from the writer/asset
description (INFERRED).

| # | Engine | Asset / module | Table (or none) | The question it answers | Granularity | Range |
|---|---|---|---|---|---|---|
| E1 | Vimśottarī + 8 sibling daśā systems | `ga_dashas` (L1) | `chart_dashas` (1,327,176 rows; 9 `system_id`s measured: chara_karaka, mudda, yogini, vimshottari, kalachakra, ashtottari, naisargika, vimshottari_kp, narayana) | "Which lord's period is running on date D, at MD/AD/PD/SD level, in system S?" | period boundaries (days) | ~1949–2100 |
| E2 | Daśā eligibility + cross-system agreement | `ka_dasha_kala` (service, DRAFT) | none (reads `chart_dashas`) | "Do the running periods across the daśā systems agree that lord L is empowered on D?" | period | life |
| E3 | Gochara v1 (retired corpus) | `ka_gochara_sweep` (RETIRED, `data_disposition=RETAINED_AS_CAPITAL`) | `kala_gochara_windows` (40,171) + `kala_gochara_windows_archive_20260805` (35,620) | "When did transiting graha G cross target T?" (v1 generation) | day | century |
| E4 | Gochara v2/v3 | `ka_gochara`, `ka_gochara_v3_century_materialize` | `kala_gochara_windows_v2` (1,934) | same question, v2/v3 generation | day | 1984–2084 |
| E5 | Gochara authority arbiter | (no writer) | `kala_gochara_authority` (2 rows) | "Which gochara generation is authoritative for THIS chart?" | per-chart | — |
| E6 | Gochara resonance targets | `ka_gochara_resonance` | `gochara_resonance_map` (1,589) | "Which bhāvas/lords/karakas/degrees does event-class E resonate with?" | static targets | — |
| E7 | Muhūrta / pañcāṅga scoring | `ka_muhurta_seva` (service) | none | "How auspicious is day D at location L for event E?" (E ∈ 8 `EVENTS_MVP` keys) | day | any |
| E8 | Ephemeris at T | `ka_graha_sancara` (service) | `bg_ephemeris` / live swisseph | "Where is graha G at instant T?" | instant | 1900–2150 |
| E9 | Tājika Vārṣaphala | `ga_tajaka` (L1) | `l1_tajik_varsha_year_lords` (680; 240 for native) | "Who is the year-lord / where is the Muntha for solar-return year Y?" | year | life |
| E10 | Tithi-praveśa (lunar return) | `ka_tithi_pravesha` | `kala_tithi_pravesha` (240) | "What does the annual chart cast at the Moon's return say about year Y?" | year | life |
| E11 | Sudarśana varṣa | `ka_sudarshana_varsha` | `kala_sudarshana_varsha` (120) | "Which house-per-year is running in the tri-lagna progression at age A?" | year | 120y |
| E12 | Sade-Sati / Dhaiya | `ga_sade_sati` (L1, service) | (derived; `derive_sade_sati_signs`/`_severity` also duplicated inside `ka_sangam`'s engine) | "Is Saturn in the sade-sati/dhaiya window over the natal Moon on D?" | month | life |
| E13 | Kota Cakra | `ka_kota_chakra` | `kala_kota_chakra` (976) | "Which kota ring is transiting graha G in relative to janma nakṣatra, and when does it enter/exit?" | ingress/egress | life |
| E14 | Mūrti Nirṇaya | `ka_moorti_nirnaya` | `kala_moorti_nirnaya` (144) | "Is graha G's stay in this sign gold/silver/copper/iron?" | sign-stay | life |
| E15 | Vedha gochara | `ka_vedha_gochara` | `kala_vedha_gochara` (354) | "Is this transit's effect cancelled by a vedha graha?" | transit | life |
| E16 | Activation predicates | `ka_yojaka` | `kala_activation_predicates` (150,150 total; **50,104** for native) | "Under which daśā/transit conditions does MSR signal S fire?" | predicate | — |
| E17 | Activation windows (**this batch**) | `ka_kalasutra` | `kala_activation` (**335,403** native) | "In which daśā period(s) is signal S active, and when?" | period | birth→life |
| E18 | Convergence (**this batch**) | `ka_sangam` | `kala_convergence` (**14,868** native) | "Which date windows have multiple currents co-activating for signal S?" | window (days) | near 5y + lifetime 100y |
| E19 | Obstruction (**this batch**) | `ka_vighnakara` | `kala_obstruction` (**536** native) | "What suppresses window W on its peak date?" | peak-date | as E18 |
| E20 | Display view (**this batch**) | `ka_kala_darshana` | `kala_darshana` (**750** native) | "Net of obstruction, how strong is window W and what do we call it?" | window | 1961–2049 measured |
| E21 | Life arc (**this batch**) | `ka_jivana_parva` | `kala_jivana_parva` (**100** native) | "What is the biographical quality of daśā chapter P?" | MD/AD/current-PD | birth→life |
| E22 | Forward projection (**this batch**) | `ka_bhavishya_lekha` | `kala_bhavishya` (**100** native) | "What are the ranked, falsifiable forward events in the next 5 years?" | window | today+5y |
| E23 | Monthly waveform | `ka_taranga` | `kala_taranga` (194,543) | "What is the activation amplitude for domain D in month M?" | month | 1950–2100 |
| E24 | Per-period dossier | `ka_avadhi` | `kala_avadhi` (3,344) | "What is the full condition of the lord + activated promises for period P?" | period | life |
| E25 | Point-process field | `ka_kshetra` | `kala_field` (10,669,603), `kala_field_windows` (36,492), `kala_field_salience` (39,000) | "What is the hazard rate λ_e(t) for event class e on day t?" | day | century |
| E26 | Serve-time ranking | `ka_tulana` (service) | none | "Which windows rank highest across patterns/domains by I-11 composite?" | serve-time | — |
| E27 | Yoga activation | `kala_yoga_activation_get` (MCP) | reads `kala_activation` + firings | "Is yoga Y firing now / when will it fire?" | window | life |
| E28 | Paddhati convention profile | (migration-seeded, no writer) | `kala_paddhati_profile` (6 rows) | "Which convention governs factor-family F for THIS chart, and which is a declared dissent slot?" | per-chart | — |
| E29 | KP school voice | `platform-mcp/src/lib/kp_school_voice.ts` | reads `kp_house_significators` + `vimshottari_kp` | "Does the running daśā lord signify this house by the KP ladder?" | period | life |
| E30 | Agnivāsa Convention B | `platform-mcp/src/lib/agnivasa_convention_b_voice.ts` | reads `bg_muhurta_lattice` + `kala_paddhati_profile` | "Does MC 1.36's Agni-vāsa arithmetic agree with the corpus-default convention on this atom?" | day | any |
| E31 | PACT chain | `pact_query` / `kala_explain_get` | multi | "Is the promise→confirmation→activation→trigger chain live on D?" | as-of date | any |
| E32 | L4 predictive anchors | `ph_nimitta` | `phala_anchors` (FK to `kala_convergence` + `kala_bhavishya`) | "Which anchored prediction attaches to window W?" | window | forward |
| E33 | L4 personal muhūrta | `ph_muhurta` | `phala_muhurta` | "Which forward windows are personally auspicious and danger-avoiding?" | day | forward |
| E34 | L4 cross-domain lag | `ph_sankrama` | `phala_sankrama` | "What is the A→B→C cascade lag from real activation windows?" | months | forward |

### 1.2 Overlap matrix — which engine pairs can answer the SAME (domain, range) question

This is the input to "one arbiter surface per (domain, range)". Only pairs that can genuinely
**disagree** are listed — pairs where one is strictly an input to the other are excluded.

| # | (Domain, range) question | Engines that can both answer | How they can disagree | Arbiter today |
|---|---|---|---|---|
| O-1 | "Is lord L empowered on D?" — life range | E1 vimshottari · E1 ashtottari/yogini/kalachakra/… (8 siblings) · E29 KP ladder | different period boundaries + KP's significator-ladder judgment has no Parāśarī analogue | **partial**: `ka_dasha_kala`'s `cross_dasha_agreement.count` (a COUNT, not a verdict); E29's `agreement` field only inside `kala_explain_get` |
| O-2 | "Where is graha G / did it cross T on day D?" — century | E3 gochara v1 · E4 gochara v2/v3 · E8 raw ephemeris | different generations produce different window sets | **YES — `kala_gochara_authority`**, single-winner per chart. The only true arbiter that exists. |
| O-3 | "Is transit X cancelled?" — transit range | E15 `ka_vedha_gochara` (354 rows, CURRENT) · `ka_sangam`'s own C11 `_c11_vedha_factor` (reads `bg_transit_rules WHERE rule_type='vedha'`) | **measured: 0 rows match that filter** — `bg_transit_rules.rule_type` ∈ {unfavourable, favourable, double_transit}; `vedha_house` is populated on 41 `favourable` rows. So the two vedha engines cannot even be compared: one is authoritative and populated, the other is permanently inert | **none** |
| O-4 | "How auspicious is day D?" — day | E7 `ka_muhurta_seva` · E30 Agnivāsa Convention B · E33 `ph_muhurta` · `ka_vighnakara`'s `panchanga_obstruction` detector | different pañcāṅga conventions; MC 1.36 vs corpus-default explicitly disagree by design | **partial**: `kala_paddhati_profile` declares the convention per factor-family, but its arbitration rule lives in a `provenance` TEXT string (see §1.3) |
| O-5 | "Is window W favourable?" — near/lifetime | E18 `ka_sangam` (4 modes on 4 scales) · E19 `ka_vighnakara` · E20 `ka_kala_darshana` · E25 `ka_kshetra` λ_e(t) · E23 `ka_taranga` monthly amplitude | mode-incommensurability (§summary 1) + λ and amplitude are independent measurements of the same thing on different scales | **none.** `kala_darshana.effective_score` composes E18×E19 but never consults E25 or E23 |
| O-6 | "What happens in year Y?" — year | E9 Tājika varṣa-lord · E10 tithi-praveśa lunar return · E11 sudarśana varṣa · E1 daśā at Y | four independent annual clocks; all four can nominate different themes for the same year | **none** |
| O-7 | "Is this a hard period?" — month/year | E12 sade-sati · E19 obstruction · E13 kota cakra ring · E14 mūrti (iron) | four independent "difficulty" signals with no shared scale | **none** |
| O-8 | "When will event class e occur?" — forward | E22 `kala_bhavishya` · E25 `kala_field_windows` · E32 `phala_anchors` · E34 `ph_sankrama` | three forward engines + one lag model, all forward-dated, no reconciliation | **none** (`phala_anchors` FKs to both `kala_convergence` and `kala_bhavishya`, so it inherits rather than arbitrates) |
| O-9 | "Which ayanāṃśa's answer?" — all | 5 ayanāṃśas on `kala_activation`/`kala_activation_predicates`; **`kala_convergence` has NO ayanamsha_id column** | E18/E19/E20/E21/E22 collapse 5 ayanāṃśas to one silently | **none**; and the collapse is undeclared |
| O-10 | "Does the causal chain hold?" — as-of | E31 PACT · E29 KP · `a5_gochara_agreement` (E4) | already served side by side in `kala_explain_get` | **partial** — three stances served, no verdict over them |

**Design consequence.** The overlap matrix has 10 live cells and exactly **one** real arbiter
(O-2). Cells O-5, O-6, O-7, O-8 are the four that a "(domain, range) arbiter surface" would
need first; O-9 is a precondition (an arbiter cannot adjudicate across ayanāṃśas on a table
that has no ayanāṃśa column).

### 1.3 The two seed authority tables, in full

#### `kala_gochara_authority` — 2 rows (exact, `SELECT *`)

Schema: `chart_id uuid PK · authoritative_generation text NOT NULL DEFAULT 'v1' · flipped_at
timestamptz · flipped_by text · evidence_ref text`.

| chart_id | authoritative_generation | flipped_at | flipped_by | evidence_ref |
|---|---|---|---|---|
| `1c826d5a-41cb-4450-b4dc-59d440e5f75a` | `3.0` | 2026-08-11 09:10:42.635488+00 | `parishkara-mr24-battery` | `PARISHKARA_LEDGER.md MR-24 rollback+re-flip exercise, 2026-08-11` |
| `482012f1-710e-4a25-994a-93821f5871aa` | `3.0` | 2026-08-11 09:44:07.812646+00 | `parishkara-mr08-operator` | `MR-24 final battery re-run 2026-08-11: rollback+re-flip exercise on native chart, post THE-ONE-rebuild + MR-40 cockpit fix` |

**What the rows encode:** a per-chart *single-winner* pointer over one engine family
(gochara), plus a complete adjudication audit trail — *when* the flip happened, *who* flipped
it, and *the evidence document* that justified it. The absence of a row is itself meaningful:
migration 527's own test (`test_migration_527_generation_catalog_only.py:95`) asserts the
migration seeds **nothing**, so "no row" means "default generation, never adjudicated". The
consumption pattern is a correlated sub-select that makes the predicate flip automatically:
`COALESCE((SELECT authoritative_generation FROM kala_gochara_authority WHERE chart_id = …),
'v1')` — used in `services/ka_kshetra/stage4_field.py:1388` and
`services/ka_kshetra/writer.py:2171`. **No TypeScript serving-plane code reads it** (grep
across `platform/src` + `platform-mcp/src`: zero non-test hits).

*Weakness to carry into the design:* `authoritative_generation` is free text with a DEFAULT of
`'v1'` and no CHECK constraint, and the stored values are `'3.0'` — a value the default's own
vocabulary ("v1") does not anticipate. Any generalization must pin the vocabulary.

#### `kala_paddhati_profile` — 6 rows (exact, `SELECT *`)

Schema: `id · chart_id · factor_family · convention_id · school_tag · constraint_role
(hard|soft|informational) · convention_status (computed|declared_not_computed) · provenance ·
corpus_gap_ref · native_confirmed bool · awaiting_native_confirmation bool · version ·
created_at · confirmation_provenance`. Natural key `UNIQUE (chart_id, factor_family,
convention_id, version)`.

| id | chart | factor_family | convention_id | school_tag | constraint_role | convention_status | native_confirmed | awaiting | version |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 482012f1 | `agnivasa` | `agnivasa_tithi_element_prithvi` | `corpus_default` | `hard` | `computed` | **t** | f | `paddhati_v01` |
| 2 | 482012f1 | `agnivasa` | `agnivasa_muhurta_chintamani_arithmetic` | `muhurta_chintamani` | `hard` | **`declared_not_computed`** | f | t | `paddhati_v01` |
| 3 | 1c826d5a | `agnivasa` | `agnivasa_tithi_element_prithvi` | `corpus_default` | `hard` | `computed` | **t** | f | `paddhati_v01` |
| 4 | 1c826d5a | `agnivasa` | `agnivasa_muhurta_chintamani_arithmetic` | `muhurta_chintamani` | `hard` | `declared_not_computed` | f | t | `paddhati_v01` |
| 7 | 482012f1 | `agnivasa` | `agnivasa_muhurta_chintamani_arithmetic` | `muhurta_chintamani` | `hard` | **`computed`** | f | t | `paddhati_v02` |
| 8 | 1c826d5a | `agnivasa` | `agnivasa_muhurta_chintamani_arithmetic` | `muhurta_chintamani` | `hard` | `computed` | f | t | `paddhati_v02` |

Load-bearing column values, quoted verbatim:

- Row 2 `provenance` — *"DECLARED SLOT ONLY — no convention content is pinned here. The Muhurta
  Chintamani arithmetic for Agni-vasa is not held in this codebase at verse grain:
  classical_text_chunks(text_id='muhurta_chintamani') is untranslated Devanagari OCR
  (content_en byte-identical to content_sa on all 274 rows; cleaned_translation_text NULL
  throughout). This row exists so the divergence surface is real rather than decorative, and
  is NEVER computed (ADJUDICATION-8 rail 2)."*
- Row 7 `provenance` — *"MC 1.36 (chunk_id=muhurta_chintamani_pg0048_c01), translated
  2026-08-03 …; Arithmetic: remainder = (tithi_id + 1 + vara_id) mod 4; {0,3}=Prthvi(fav),
  1=Akasha, 2=Patala. **Served as a second, informational concurrence/dissent voice ONLY
  (ADJUDICATION-17) -- NEVER enters the residence hard-gate Convention A alone governs.**"*
- Row 1 `confirmation_provenance` — *"native statement 2026-08-02 (correcting the 2026-07-28
  elevation-session misstatement); recorded in SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md
  §NATIVE CONFIRMATIONS"*.

**What the rows encode.** This is already a per-(chart, factor_family) authority profile with
six of the seven fields an arbiter needs:
`factor_family` = the arbitrable question; `convention_id` = the engine; `school_tag` = the
tradition/authority; `constraint_role` = how much weight the verdict may carry;
`convention_status` = **the silent-vs-dissenting distinction** (`declared_not_computed` is
literally "this engine has a seat but casts no vote", the exact thing `ka_sangam`'s `0.0`
currents cannot express); `native_confirmed`/`awaiting_native_confirmation` = *who
adjudicates* — the native, with a cited provenance string; `version` = the profile generation.

**The one field that is missing is the arbitration rule itself.** Row 7 carries
`constraint_role = 'hard'` while its own `provenance` prose says *"informational concurrence/
dissent voice ONLY … NEVER enters the residence hard-gate"*. The machine-readable field and
the prose **contradict each other**, and only the prose is correct — `agnivasa_convention_b_
voice.ts` implements the prose (it reports a voice; `kala_sky_pattern.ts`'s Convention A
branch holds the gate). That is a §N.7-item-4 / §N.8 defect on the seed table itself: a field
that reads "hard gate" with nothing behind it enforcing a hard gate. **F-CONC-2 below.**

**Generalization to a per-engine authority profile.** The minimum viable table is
`kala_paddhati_profile` with `factor_family` widened from convention-families to the
`(domain, range)` cells of §1.2, `convention_id` widened to engine ids (`ka_gochara@3.0`,
`ga_dashas@vimshottari`, `ka_muhurta_seva`, `kp_ladder`, …), plus **two new columns**:
`arbitration_role` ∈ `{gate, primary, corroborating, informational, declared_silent}` — the
prose in row 7's `provenance` promoted to data — and `precedence smallint` (a total order
within a `factor_family`, so `disputed(adjudicated_by=…)` has a deterministic winner rather
than a tie). `kala_gochara_authority` then becomes the special case `factor_family='gochara',
arbitration_role='gate'` with its `flipped_at/flipped_by/evidence_ref` audit triple promoted
onto the general table (it is the better audit design of the two).

### 1.4 Does `ka_sangam` already compute something arbiter-like?

**Yes — substantially. VERIFIED by reading `pipeline/orchestrator/writers/ka_sangam.py` (1,126
lines) and `services/ka_sangam/engine.py` (1,526 lines) and by measuring the stored output.**

**What EXISTS today:**

1. **A 12-current weighted agreement model.** `SUPPORTING_WEIGHTS` (engine.py:39–52, asserted
   to sum to 1.0 at import) over: `constituent_lord_transit` 0.180, `ashtakavarga_transit_
   potency` 0.120, `cross_dasha_agreement` 0.120, `benefic_dristi` 0.100, `school_consensus`
   0.100, `transit_to_transit` 0.080, `panchanga_quality` 0.070, `tara_bala` 0.060,
   `eclipse_proximity` 0.060, `nakshatra_subsystem` 0.050, `station_retrograde` 0.030,
   `tajika_annual_reinforcement` 0.030. Each current is a *different temporal engine's* answer
   about the same window — i.e. the testimony gather already exists.
2. **A necessary/supporting split with a real veto.** `convergence_score(necessary, supporting)
   = Π(necessary) × (1 − Π(1 − wᵢ·sᵢ))`. `c11_vedha_factor` enters the *necessary* side —
   architecturally this is `gate` vs `corroborating`, the same distinction §1.3 wants as
   `arbitration_role`.
3. **Explicit independence accounting.** `independent_current_count()` (I-22, engine.py:664)
   discounts *correlated* evidence — daśā+nakṣatra-overlay counted as ~1, pañcāṅga+transit at
   ~0.5, eclipse/school/station/tājika independent. Stored on the row
   (`independent_current_count smallint`). This is precisely the "how many genuinely
   independent voices agree" quantity an `aligned | partially_aligned | disputed` verdict
   needs.
4. **Two cross-system agreement counters.** `_c_cross_dasha_agreement` = `max(count of daśā
   systems agreeing at peak) / 7.0`, sourced from `KaDashaKalaService`'s `EligibleWindow.
   cross_dasha_agreement.count`. `_c13_school_consensus_score` = `schools_agreeing / 7.0`.
5. **Per-window testimony, persisted.** `constituent_factors jsonb` on Mode A rows carries the
   full per-current score set. Verified sample (top-scoring Mode A row, chart 482012f1):
   `{"c_tara_bala":0.9,"dasha_score":0.5,"c11_vedha_factor":1.0,"c_benefic_dristi":1.0,
   "c_panchanga_quality":0.0,"c13_school_consensus":0.0,"c8_eclipse_proximity":0.0,
   "c9_transit_to_transit":1.0,"c10_station_retrograde":1.0,"c7_ashtakavarga_potency":0.0,
   "c_cross_dasha_agreement":0.0,"c12_tajika_reinforcement":0.0,
   "trigger_suppressive_applied":0.0,"convergence_score_pre_trigger":0.3086, …}`.
6. **A confidence tier + an honest admission that it is uncalibrated.** `confidence_label`
   (I-21 absolute) and `confidence_label_relative` (JL-014 within-chart percentile), with
   `tier_basis = 'relative_uncalibrated'` on **100%** of rows.

**What is MISSING for the arbiter:**

| Missing piece | Evidence |
|---|---|
| **A stance vocabulary.** Every current is `[0,1]` supporting. There is no way to say "this engine actively contradicts". A dissent and an absent engine are the same number. | `convergence_score()` sums `wᵢ·sᵢ`; nothing subtracts. |
| **Silent vs dissenting.** `_c_panchanga_quality` returns `0.0` on exception; `_c13_school_consensus_score` returns `0.0` when `ctx.school_consensus_by_domain` is empty; `_c11_vedha_factor` returns `1.0` "no data → no vedha → neutral". All indistinguishable from real answers. `kala_paddhati_profile.convention_status` and `kala_now_get`'s `*_reachable` flags both already model this correctly, one layer away. | engine.py:474, 486, 242 |
| **Per-engine testimony on 86% of rows.** Mode C `constituent_factors` = `{"mode","sign","planet","subsystem","dignity_score","severity_score","signature_class"}` — no currents at all. Mode D = `{"mode","sign","planet","sign_num","sav_score","sav_bindhu","dignity_score","sav_threshold"}`. Measured: 12,755/14,868 rows (**85.8%**) are Mode C or D. | `SELECT mode, count(*) …` |
| **Commensurable scores.** Modes A/B ≤0.31; Mode C avg 0.79 max 1.00; Mode D avg 0.44. No `score_scale` / `score_basis` column. | measured |
| **An adjudicated verdict + `adjudicated_by`.** No column, no computation, no serving field. | schema |
| **Any consultation of the authority profile.** `ka_sangam` never reads `kala_paddhati_profile` or `kala_gochara_authority`. Its vedha input is `bg_transit_rules WHERE rule_type='vedha'` (**0 rows**) rather than `kala_vedha_gochara` (354 rows, `catalog_status=CURRENT`). | grep + measured |
| **Ayanāṃśa dimension.** `kala_convergence` has no `ayanamsha_id`; five ayanāṃśas of predicates collapse into one undeclared answer. | `\d kala_convergence` |

**Route consequence for W2:** the arbiter is an **extension of `ka_sangam` + the existing
`kala_explain_get` envelope**, not a new asset. The expensive part (gathering 12 engines' answers
per window) is built and measured at p50 1,729 s. The additions are: a `stance` enum beside each
current, a `score_basis`/`score_scale` column on `kala_convergence`, an
`arbitration_role`/`precedence` pair on a generalized `kala_paddhati_profile`, and a verdict
composer. **Materially cheaper than a new build.**

### 1.5 The serving side — where the verdict and testimony attach

#### `kala_explain_get` — `platform-mcp/src/tools/kala_views/explain.ts` (764 lines)

- Registration: `registerKalaExplainTool(server, principal)` (line 571). Capability wrapped:
  `marsys://tool/L-PACT/pact_query` via `callKalaRegistryCap`.
- **Emits today** (the `baseContent` object, lines ~739–754): `ok, tool, chart_id,
  ...envelope` (i.e. `reading`, `question_frame`, `field_snapshot_id`,
  `field_snapshot_state`, `field_snapshot_reason`, `tri_plane`, `coverage`, `freshness`,
  `calibration_maturity`), `composed`, **`density_contract`**, `about`, `pact_status`,
  **`weakest_link`**, **`school_voices: kpVoice ? [kpVoice] : []`**, `chain`, `fact_id_refs`,
  `pact_drill_pointers`; plus flag-guarded **`a5_gochara_agreement`** when
  `SM_GAMMA_C4_ENABLED`.
- **Where the arbiter attaches — precisely:**
  - `school_voices: KpSchoolVoice[]` (already an array, already one element) **becomes
    `engine_testimony: EngineTestimony[]`.** `KpSchoolVoice` (`lib/kp_school_voice.ts:103`)
    already has the exact field set: `{school, school_label, state: 'computed'|'honest_empty',
    empty_reason: string|null, agreement: 'concurs'|'dissents'|'not_comparable', …, claim}`.
    `AgnivasaConventionBVoice` (`lib/agnivasa_convention_b_voice.ts:42`) is field-for-field the
    same shape with `agreement: 'agrees'|'diverges'|'not_comparable'`. `A5GocharaAgreement`
    (`explain.ts:424`) is the same idea with `agreement: 'concurs'|'dissents'|
    'insufficient_data'`. **Three implementations, one shape, three vocabularies — unify.**
  - The `aligned | partially_aligned | disputed(adjudicated_by)` verdict attaches as a **new
    top-level key beside `weakest_link`** — the same altitude, and the natural sibling
    (`weakest_link` already names the chain's least-attested edge; `concordance` names the
    cross-engine state).
  - `reading.dissent: ArgumentDissent[]` (`kala_envelope.ts:51`,
    `{claim, fact_ids, source}` — `source` is documented with *'KP sub-lord clock'* and
    *'vimshottari daśā'* as its worked examples) is the **prose** face of the same verdict.
    `applyKpVoiceToReading()` already writes into it. A `disputed` verdict must populate it.
  - Honesty is already handled: `coverage: KalaCoverageEntry[]` with
    `computedCoverage/honestEmptyCoverage/notInCorpusCoverage` (3-state, `reason` required on
    the non-computed states) is where `not_comparable` engines get declared, and
    `kpCoverageEntry(kpVoice)` is the existing worked example.
- **§N.6 pattern to extend:** `explain.ts:707` declares
  `const densityContract: KalaDensityContract = { paginated: false, facets: ['domain','bhava'],
  empty_reason: true }`. `KalaDensityContract` is defined at `kala_envelope.ts:668` as a
  field-for-field mirror of `CapabilityDescriptor.density_contract` in
  `platform/src/lib/retrieval/registry/types.ts`. The trim protection helper is
  `kalaEvidenceTrimmableSection()` (`kala_envelope.ts:643`) which returns a
  `TrimmableSection` with `path:'reading.evidence', minKeep:1, hardFloor:true`. **An
  `engine_testimony` array carrying a `disputed` verdict is exactly the "densest,
  most-actionable layer" §N.6 item 2 says must declare `hardFloor: true`** — otherwise the
  budget trimmer will zero the dissent before it zeroes the catalog-shaped `chain` array.
  `facets` should gain `'engine'`.

#### `kala_now_get` — `platform-mcp/src/tools/kala_views/now.ts` (2,248 lines)

- **Emits today** (`baseResult`, lines 2060–2117): `tool, chart_id, as_of_date, ...envelope,
  reading_prose, windows, darshana, disha_shula, gulika_kalam_now, chandrashtama, hora_now,
  janma_resonance, gochara_dual_reference, dasha_lord_transit_condition,
  sukshma_boundary_uncertainty, dasha_sandhi, kota_chakra, sudarshana_varsha, moorti_nirnaya,
  vedha_gochara, tithi_pravesha, drill_pointers, provenance_envelope`; plus flag-guarded
  `gochara_narrative` under `SM_GAMMA_C4_ENABLED`.
- **This is already the multi-engine gather** — ~15 temporal engines, each as its own
  top-level key, each with a matching `*_reachable` boolean inside `provenance_envelope`
  (`windows_reachable`, `darshana_reachable`, `gochara_dual_reference_reachable`,
  `dasha_lord_transit_condition_reachable`, `dasha_sandhi_reachable`, `kota_chakra_reachable`,
  `sudarshana_varsha_reachable`, `moorti_nirnaya_reachable`, `vedha_gochara_reachable`,
  `tithi_pravesha_reachable`, `sukshma_boundary_uncertainty_reachable`,
  `panchanga_reachable`, `natal_panchanga_reachable`). Two of those were already hardened to
  §N.8 (`… && rowsWithTransitData > 0`, with the count served alongside).
- **The `*_reachable` flags are already the `state: computed | honest_empty` half of the
  testimony shape.** What each block lacks is a **stance** (does this engine's answer support
  or contradict the composed `reading.verdict`?). The arbiter therefore attaches as a
  `concordance` block that maps each existing engine key → `{engine, state (from the existing
  *_reachable flag), stance, claim}` and a verdict over them.
- **Gap vs `explain.ts`:** `now.ts` does **not** declare a `density_contract` (grep: zero
  hits) and does not use `kalaEvidenceTrimmableSection`. With ~20 top-level arrays it is the
  file most exposed to a budget trim zeroing a dissent. **F-CONC-5.**
- No L3_kala capability in `platform/src/lib/retrieval/registry/layers/L3_kala/` declares
  `density_contract` at all (grep across all 20 files: zero hits). The pattern exists only on
  the MCP side.

---

## PART 2 — PER-ASSET ANALYSIS

---

## ka_sangam

**One-line identity:** the convergence engine — turns ≤260 selected activation predicates into
scored date windows by asking 12 temporal currents about each candidate peak.
**Temporal question (D-TIME):** *"Across which date windows do multiple independent temporal
currents co-activate for this signal, and how strongly?"*

**1. Instrument fit.** Serves **D-TIME** (it *is* the layer's agreement engine), **D-SYNTHESIS**
(cross-engine composition), **D-SALIENCE** (`convergence_score` is the intended temporal
multiplier), **D-GROUNDING** partially (`constituent_factors` is a real derivation ledger for
Mode A/B; Mode C/D carry none). **Still the right instrument — but its output scale is not.**
The design intent ("score = agreement") is defeated by Mode C/D writing constants onto the same
column (§summary 1). It is the correct home for the arbiter.

**2. Dependencies (declared vs real).** Declared (`asset_registry.depends_on`, 10):
`{ka_yojaka, ka_dasha_kala, ka_gochara, ka_muhurta_seva, bo_laksana, ga_dashas, ga_strength,
ga_positions, ga_tajaka, bg_transit_rules}`.

| Declared | Actually read? | Evidence |
|---|---|---|
| `ka_yojaka` | ✅ `FROM kala_activation_predicates` (writer:284) | |
| `ka_dasha_kala` | ✅ `KaDashaKalaService(conn)` (writer:315) | |
| `ka_gochara` | ✅ `KaGocharaService(swe)` (writer:319) | |
| `ka_muhurta_seva` | ⚠️ **constructed but its answer is always discarded** — `_c_panchanga_quality` measured 100.0% zero (F-SANGAM-3) | |
| `bo_laksana` | ✅ `FROM bodha_msr_signals` (writer:343) | |
| `ga_dashas` | ✅ `FROM chart_dashas` (writer:870, `_derive_birth_year`) + via `ka_dasha_kala` | |
| `ga_strength` | ❌ **declared-but-unread.** No query in `ka_sangam.py` or `engine.py` touches a strength/ṣaḍbala table. `dignity_score` comes from `bodha_msr_signals`, not `ga_strength`. | grep |
| `ga_positions` | ✅ indirectly via `chart_facts` (writer:760, 995, 1113) | |
| `ga_tajaka` | ⚠️ **read but always scores 0** — `FROM l1_tajik_varsha_year_lords` (writer:1066) returns 240 rows for the native, yet `c12_tajika_reinforcement` is 100.0% zero (F-SANGAM-6) | |
| `bg_transit_rules` | ❌ **effectively unread** — `WHERE rule_type = 'vedha'` matches **0 of 75 rows** (measured; the vocabulary is `{unfavourable, favourable, double_transit}`) | measured |

**Undeclared reads (hidden edges):** `public.charts` (`_resolve_birth_location`, writer:834);
`build_substep_progress` (resumption ledger, writer:491/510 — infrastructure, arguably fine);
`chart_facts` directly for lagna/nakṣatra/Moon-sign/ashtakavarga (writer:760/995/1113) — covered
by `ga_positions` only loosely.

**3. Leverage / NULL check.** `kala_convergence` has essentially **no NULL columns**: measured
on n=14,868 (chart 482012f1) — `signal_id` 0.0%, `mode` 0.0%, `peak_date` 0.0%, `orb_strength`
0.0%, `rarity_years` 0.0%, `confidence_score` 0.0%, `confidence_label` 0.0%,
`independent_current_count` 0.0%, `confidence_label_relative` 0.0%, `tier_basis` 0.0%,
`constituent_factors` empty 0.0%; only `domain` is 3.2% NULL. **The leverage loss here is not
NULLs — it is computed-and-discarded:**

- **`confidence_label_relative` and `tier_basis` are 100% populated and served NOWHERE.**
  `query_convergence_windows.ts`'s SELECT list (lines ~117–127) returns `confidence_label` but
  neither of the other two. Measured: the two labels **disagree on 4,748 of 14,868 rows
  (31.9%)** — including 2,010 rows the absolute label calls `speculative` that the relative
  label calls `high`. The surface serves the label JL-014's own comment says is degenerate, and
  withholds the one built to fix it. **Highest-leverage single-line fix in the batch.**
- **`independent_current_count` is degenerate where it matters.** Measured by mode: A near 3.47,
  A lifetime 3.00, B near 3.45, B lifetime 2.97, **C 1.00, D 1.00**. 85.8% of rows carry the
  value 1.
- **0.380 of 1.000 supporting weight is permanently zero** (§summary 3, five separate root
  causes at F-SANGAM-3…7).
- **The ranked surface is 100% single-mode.** `SELECT … ORDER BY convergence_score DESC LIMIT
  200` → **200/200 Mode C lifetime**, min score = max score = **1.0**. Downstream
  `ka_kala_darshana` (LIMIT 750) and `ka_vighnakara` (LIMIT 500) inherit it.

**4. Grounding tier.** Mode A/B → **`yukti`**: derived by ratified rules (I-16/I-17/I-21/I-22)
from cited L1 facts, with the per-current ledger persisted in `constituent_factors`. Mode C/D →
**`pratyaksa`** and should be *labelled* so: they are catalog-constant products with no classical
derivation and no cited fact. The engine has no tier column; adding one is the honest fix (an
honest `pratyaksa` on Mode C/D is success, not failure — it would immediately stop Mode C from
being read as an evidentially-strong window).

**5. Temporal identity + arbitration.** Question as above. When it disagrees with another
engine, **nothing arbitrates today.** Overlapping engines: `ka_kshetra` (λ_e(t) over the same
days), `ka_taranga` (monthly amplitude over the same months), `ka_avadhi` (period dossiers over
the same periods), `ka_vedha_gochara` (a second, working vedha engine whose answer `ka_sangam`
never reads), `ka_gochara` v2/v3 (the transit substrate, whose authoritative generation
`kala_gochara_authority` already pins for `ka_kshetra` but not for `ka_sangam`). Cells O-3 and
O-5 of §1.2.

**6. Service.** Real consumers: `query_convergence_windows.ts` (L3 registry capability,
registered in `L3_kala/index.ts`), `platform-mcp/src/tools/retrieval/kala_temporal.ts`
(8 refs), and — via FK — `kala_darshana`, `kala_obstruction`, `kala_bhavishya`, `phala_anchors`.
Not shelf inventory. **No `density_contract`** on the capability. **No `empty_reason`
discipline** (it returns `convergence_windows: []` with `window_count: 0` and no reason). Drill
to L1: `signal_id_refs` → `bodha_msr_signals` → `constituent_facts_array` → `chart_facts` = **3
hops**, not ≤2. Serving bug: `input_schema.min_convergence_score` documents *"(0..100, default:
0)"* while the column has `CHECK (convergence_score >= 0.0 AND <= 1.0)` — any caller taking the
doc at its word gets zero rows, silently. The file header also states *"19,482 rows per chart"*;
measured 14,868.

**7. Measured cost.** `estimated_seconds = 463`. **Measured** from `build_run_assets` (state
`complete`, since 2026-08-01, n=5): **min 142.1 s, p50 1,728.9 s, max 3,278.4 s** — p50 is
**3.7×** the estimate; the max is 54.6 minutes. `writer_timeout_seconds = 10800`, so no timeout
risk. `has_substeps = true` (1 `near` + ≤60 `lifetime:N`), with cross-attempt resumption keyed on
a content fingerprint (migration 436) — well engineered. Serve cost: unmeasured.
Rows: 14,868 (native) / 17,957 (1c826d5a) / 2,540 (cb73cd3d). `target_floor` NULL,
`expected_volume_formula` NULL, `expected_volume_inputs` NULL, `integrity_check_sql` NULL.

**8. Findings.**

- **F-SANGAM-1 — `convergence_score` is not commensurable across modes; the least-evidenced mode
  monopolises every ranked surface. `MUST`.** Mode C = `dignity_score × severity` (two catalog
  constants, `orb_strength` hardcoded 1.0, `independent_current_count` 1); Mode A ≤0.3086. Top-200
  by score = 200/200 Mode C. Doctrine: **§N.6 item 1** ("never present catalog matches as confirmed
  findings … counted and flagged SEPARATELY") and **item 2** (the densest layer is protected
  first — here the *least* dense layer wins). Minimum fix: a `score_basis` column
  (`agreement_weighted` | `catalog_constant`) + per-basis ranking, or per-mode normalisation.
- **F-SANGAM-2 — `confidence_label_relative` + `tier_basis` computed on 100% of rows, served on
  0%. `NOW`.** The served `confidence_label` is the one JL-014's own comment documents as
  degenerate; the two disagree on 31.9% of rows. Doctrine: rubric item 3 (leverage);
  **§N.6 item 4** (density signalling is data). One-line SELECT-list fix in
  `query_convergence_windows.ts`.
- **F-SANGAM-3 — `c_panchanga_quality` is 100% zero because the event key is invalid. `MUST`.**
  `engine.py:1028/1201` calls `muhurta_service.score(peak_dt, native_location, event='general')`;
  `'general'` is **not** in `muhurat/finder.py:36`'s `EVENTS_MVP` (8 keys: vivah, griha_pravesh,
  vyapara, yatra, property_purchase, mantra_initiation, upaya_ritual, sadhana_initiation);
  `score_muhurat` raises `ValueError` (finder.py:161–162); `_c_panchanga_quality`'s bare `except`
  swallows it → `0.0`. Weight 0.070 permanently dead; the declared `ka_muhurta_seva` dependency
  contributes nothing. Doctrine: **§N.8** (a signal with no working detector is null, not zero) +
  **§N.7 item 6** (an honest null beats an invented value — `0.0` here reads as "inauspicious",
  a *judgment*, not a gap).
- **F-SANGAM-4 — `c7_ashtakavarga_potency` is 100% zero from a key-format mismatch, on data that
  exists. `MUST`.** `_build_enrichment_context` (writer:1000) parses `chart_facts.fact_subject`
  of the form `JUP-HOUSE_1` into `ashtakavarga_bindu['JUP'][1]`. Measured distinct planet keys:
  `{JUP, MAR, MER, MOON, SARVA, SAT, SUN, VEN}` (96 rows present for the native at
  `lahiri_chitrapaksha`). `_c7_ashtakavarga_potency(planet, …)` (engine.py:98) is called with the
  capitalised full name (`"Mercury"`, `"Saturn"` — visible in stored `constituent_factors`), so
  `.get(planet, {})` always misses. **Second, independent defect in the same function:** the inner
  lookup is `sign_map.get(transit_sign, 0)` but the map was keyed by **house** number. Weight 0.120
  dead. Doctrine: **§N.7 item 1** (a restatement must trace to the fact it reads) + §N.8.
- **F-SANGAM-5 — `c11_vedha_factor` and the whole TRIGGER suppressive term are structurally inert.
  `MUST`.** `_build_enrichment_context` (writer:1036) queries `bg_transit_rules WHERE rule_type =
  'vedha'`; measured **0 of 75 rows** match (`rule_type` ∈ {unfavourable 26, favourable 42,
  double_transit 7}; `vedha_house` is non-null on 41 `favourable` rows). `vedha_rules` is therefore
  always `None` → `_c11_vedha_factor` returns `1.0` on every row (**measured: `c11_vedha_factor < 1`
  on 0.0% of 1,994 rows**) and `apply_trigger_suppression` receives `vedha_rules=None`
  (**measured: `trigger_suppressive_applied > 0` on 0.0%**). The D-3 T-6 admitted weights
  (0.2/0.2) have never applied to a stored row. Meanwhile `ka_vedha_gochara` (`kala_vedha_gochara`,
  354 rows, `catalog_status=CURRENT`) is the layer's *working* vedha engine and is never consulted.
  Doctrine: **§N.8** (the veto's detector cannot fire) + **§N.5** (an L3 derivation must reference
  the authoritative source, not a dead filter). This is also overlap cell **O-3** — two vedha
  engines, no arbiter.
- **F-SANGAM-6 — `c13_school_consensus` is dead twice over. `MUST`.** (a) `_build_enrichment_
  context` never populates `school_consensus_by_domain` — the code comment says so verbatim
  (*"pre-U4 default — not yet built; stays empty"*), so `_c13_school_consensus_score` returns 0.0
  at its first branch. (b) Even with data it would still return 0.0: it maps
  `signature_class` prefixes `{CAREER, HEALTH, RELATIONSHIP, SPIRITUAL, PSYCHOLOGICAL}`, but the
  `kala_activation_predicates.signature_class` CHECK vocabulary is `{YOGA, DOSHA, DIGNITY,
  DISPOSITOR_RELATIONAL, SENSITIVE_POINT, CONJUNCTION_ASPECT, SUBSYSTEM, CLASSIFY_RESIDUAL}` —
  **no overlap whatsoever**. Weight 0.100 dead. Doctrine: **§N.8**.
- **F-SANGAM-7 — `c12_tajika_reinforcement` 100% zero and `c8_eclipse_proximity` 100% zero.
  `NOW`.** C12: `l1_tajik_varsha_year_lords` has 240 rows for the native and is read, but
  `_c12_tajika_score` short-circuits on `domain_lord is None`; `domain_lord` comes from
  `predicate.get('domain_lord')` which `ka_yojaka` does not appear to set (INFERRED — I verified
  the 100% zero, not the writer-side absence). C8: 100% zero across 1,994 rows despite a working
  `KaGocharaService` (Mode C, which needs it, produced 924 rows) — root cause **unmeasured**.
  Combined weight 0.090. Doctrine: §N.8.
- **F-SANGAM-8 — `ga_strength` is a declared-but-unread dependency; `public.charts` and
  `chart_facts` are undeclared reads. `NOW`.** Rubric item 2. `ga_strength` should be dropped from
  `depends_on` or actually consulted (the natural place is `constituent_lord_transit`, the single
  heaviest weight at 0.180).
- **F-SANGAM-9 — `_build_house_lord_map` falls back to `'Aries'`, this native's own lagna.
  `NOW`.** Writer:1108, comment: *"Falls back to Aries (this native's lagna) on any query
  failure."* Directly contradicts the CR-87 fail-loud discipline the same file enforces 250 lines
  earlier in `_resolve_native_chart_context` (*"A loud build failure is the correct outcome —
  proceeding with another chart's constants is exactly the CR-87 failure mode"*). Cross-chart
  contamination hazard.
- **F-SANGAM-10 — `kala_convergence` has no `ayanamsha_id`; 5 ayanāṃśas collapse silently.
  `NOW`.** `kala_activation_predicates` carries 5 ayanāṃśas (10,003–10,040 signals each,
  measured); `kala_convergence` has no such column and `query_convergence_windows.ts` documents
  this as *"kala_convergence has no ayanamsha_id column — filter on chart_id only."* The collapse
  is undeclared to the caller. Overlap cell **O-9**; precondition for any cross-engine arbiter.
- **F-SANGAM-11 — `min_convergence_score` is documented `0..100` against a `0..1` CHECK; the file
  header claims 19,482 rows/chart (measured 14,868). `NOW`.** `query_convergence_windows.ts`
  lines 61 and 4. Doctrine: **§N.7** (narration fidelity — a doc string that cannot be true of
  the fact it describes).
- **F-SANGAM-12 — registry health: `integrity_check_sql`, `expected_volume_formula`,
  `expected_volume_inputs`, `target_floor` all NULL; `size_sql` is not chart-scoped. `NOW` (C12).**
  Proposed real invariants (never a bare `count(*) = N` — C12/D-126): (i) *no orphan* —
  `SELECT count(*) FROM kala_convergence c WHERE c.chart_id=$1 AND c.signal_id IS NOT NULL AND NOT
  EXISTS (SELECT 1 FROM bodha_msr_signals s WHERE s.signal_id=c.signal_id)` must be 0 (§N.5 —
  `signal_id` must resolve); (ii) *range validity beyond the CHECK* —
  `window_start <= peak_date <= window_end` on every row with a peak (the CHECK only asserts
  `window_end >= window_start`); (iii) *lifetime rows lie inside the lifetime horizon* —
  `horizon_tier='lifetime'` rows must have `window_start >= birth_year-01-01`; (iv) *mode/basis
  coherence once F-SANGAM-1 lands* — `mode IN ('C','D')` ⟺ `independent_current_count = 1`.
  Proposed `expected_volume_formula`: `≈ (near_preds × modes_A_B_windows) + (lifetime_preds ×
  lifetime_windows) + mode_D_sign_windows`, inputs `{near_pred_limit: 200, lifetime_pred_limit:
  60, horizon_years: 5, lifetime_horizon_years: 100}`. `target_floor` per §N.4 = achieved count
  after the next clean build (do not fabricate).
- **F-SANGAM-13 — `catalog_status='DRAFT'` is stale. `NOW` (D-SERVICE).** Real registered
  consumer + 4 FK dependants. See §summary 4.

**Route recommendation (W2 input):** `changed` — this asset is the arbiter's home and carries
five `MUST` correctness defects (F-SANGAM-1, 3, 4, 5, 6) that are all small, local code fixes
with large measured effect; a rebuild without them would re-materialise the same dead currents.

---

## ka_vighnakara

**One-line identity:** the obstruction detector — five ephemeris-based detectors run against the
peak date of each of the top 500 convergence windows plus up to `_MAX_DASHA_ANCHORS` daśā-derived
peaks.
**Temporal question (D-TIME):** *"What suppresses this window on its peak date, and by how
much?"*

**1. Instrument fit.** **D-TIME** + **D-SALIENCE** (it is the negative term in the salience
product). Correct instrument, correctly fail-loud: `run()` raises `RuntimeError` if `swisseph`
is unimportable **before** the DELETE, with an explicit comment that stub rows with
`severity_score=0` would be *"indistinguishable from genuine zero-score computations"* — a
textbook §N.8 guard, and the best-disciplined writer in this batch.

**2. Dependencies (declared vs real).** Declared: `{ka_sangam, ka_gochara, ka_muhurta_seva,
ga_positions}`.
- `ka_sangam` ✅ `FROM kala_convergence … LIMIT 500`.
- `ka_muhurta_seva` ✅ `KaMuhurtaSevaService()` (used for real tithi in the pañcāṅga detector).
- `ga_positions` ✅ via `chart_facts` natal lagna longitude (`_fetch_natal_lagna_lon`).
- `ka_gochara` ❌ **declared-but-unread** — the writer imports `swisseph` directly (`import
  swisseph as swe`) and calls `_get_sidereal_lon` itself rather than going through
  `KaGocharaService`. It therefore also bypasses `kala_gochara_authority`'s generation pin.
- **Undeclared reads:** `bg_combustion_orbs` (L0, `_fetch_combustion_orbs`) and
  `kala_activation_predicates` (`ka_yojaka`, `_dasha_anchor_peaks`) — two hidden edges, the
  second a real DAG edge (it can only run after `ka_yojaka`).

**3. Leverage / NULL check.** Measured on the native chart (n=536): `signal_id` 0% NULL;
`convergence_id` NULL on **44 of 536 rows (8.2%)** — the daśā-anchored rows, by design.
The leverage loss is downstream, and it is total:
- **The obstruction pipeline has zero effect on any served label.** `ka_kala_darshana` computes
  `effective = convergence_score × (1 − max_override)` then labels it. Measured override scores:
  `malefic_transit` avg 0.221 (358 rows), `combustion` 0.120 (123), `gandanta` 0.220 (38),
  `panchanga_obstruction` 0.120 (17) — **max 0.221**. The windows it is applied to are 100% Mode C
  with `convergence_score` ∈ {0.70, 1.00}. `1.00 × (1−0.221) = 0.779 ≥ 0.70` → still
  `auspicious_strong`. Measured result: `kala_darshana.net_label` takes exactly **2 of its 6 legal
  values** — `auspicious_strong` 648, `auspicious_moderate` 102. `obstructed`,
  `obstructed_severe`, `neutral`, `auspicious_speculative` are **unreachable**. 336 of 750 rows
  carry a `narrative.caution` string ("Moderate obstruction: …") **while still being labelled
  `auspicious_strong`** — the caution and the label contradict each other on the same row.
- **`severity='severe'` never occurs.** `_SEVERITY_THRESHOLDS = [(0.70,'severe'),(0.40,
  'moderate'),(0.0,'mild')]`; measured max severity = `moderate`. So `idx_kala_obstruction_severe`
  (a partial index `WHERE severity='severe'`) indexes zero rows, and
  `_compute_net_label`'s `has_severe` branch and `ka_bhavishya_lekha`'s `net_label NOT IN
  ('obstructed_severe')` filter are both dead code.
- **3 of 7 `obstruction_type` values never appear:** `dasha_lord_afflicted`,
  `rashi_dristi_conflict`, `papakartari` (the last has a detector — `_check_papakartari` — that
  produced 0 rows on this chart). The first two are documented as *"reserved for future
  detectors"* — honest.

**4. Grounding tier.** **`yukti`** for `gandanta`, `combustion` (orbs from `bg_combustion_orbs`,
an L0 classical table), `papakartari`, `malefic_transit` — all classical-rule re-derivations.
`panchanga_obstruction` is `yukti` via the muhūrta service. The `override_score` *magnitudes*
(0.45 multiplier, 0.12, 0.20, 0.22) are tuning constants with no classical citation → those
specific numbers are **`pratyaksa`** and should be labelled so.

**5. Temporal identity + arbitration.** Question as above. Overlapping engines: `ka_vedha_gochara`
(a different classical obstruction mechanism on the same transits — overlap **O-3**),
`ka_kota_chakra` (ring position is a classical difficulty signal), `ka_moorti_nirnaya` (iron
mūrti = obstruction), `ga_sade_sati`, and `ka_kshetra`'s suppressive field terms — overlap
**O-7**, five independent "this is a hard period" engines with no shared scale and no arbiter.
Nothing arbitrates today.

**6. Service.** Consumers: `query_obstruction_periods.ts` (registered L3 capability),
`kala_temporal.ts` (9 refs), and `ka_kala_darshana` + `ka_bhavishya_lekha` internally.
**`L3_kala/index.ts`'s header still calls it `STUBBED-PENDING-DATA, 0 rows`** — it serves 1,283
rows. No `density_contract`, no `empty_reason`. Drill to L1: `signal_id` → MSR →
`chart_facts` = 3 hops.

**7. Measured cost.** `estimated_seconds = 14`; **measured p50 27.8 s** (min 14.0, max 86.5,
n=5 since 2026-08-01) — the only estimate in this batch that is roughly right (2× at p50).
Rows: 536 (native) / 741 (1c826d5a) / 6 (cb73cd3d — see F-VIGHNA-4).
`integrity_check_sql` / `expected_volume_formula` / `expected_volume_inputs` / `target_floor`
all NULL.

**8. Findings.**

- **F-VIGHNA-1 — obstruction is computed and then structurally discarded. `MUST`.** Measured:
  max `override_score` 0.221 against Mode-C `convergence_score` ≥ 0.70 ⇒ no obstruction can ever
  move a served row out of `auspicious_*`; 336 rows carry a caution string next to an
  `auspicious_strong` label. Doctrine: **§N.6 item 3** (a verdict layer must not present a
  populated-looking envelope that contradicts its own grounding) + **§N.7 item 6**. The root
  cause is F-SANGAM-1 (the denominator), so this is *fixed by* F-SANGAM-1 plus a re-check of the
  `_compute_net_label` thresholds.
- **F-VIGHNA-2 — the 500-window intake is 100% Mode C. `MUST` (inherited).** `ORDER BY
  convergence_score DESC NULLS LAST LIMIT 500` on a table whose top-200 is 200/200 Mode C. The
  detector never sees a daśā-prior (Mode A) window. Mitigated in part by the `_dasha_anchor_peaks`
  path (44 rows), which is the right idea. Doctrine: §N.6 item 2.
- **F-VIGHNA-3 — `_dasha_anchor_peaks` picks its representative signal nondeterministically.
  `NOW`.** The predicate query (`SELECT signal_id, ayanamsha_id, dasha_eligibility_rule_jsonb
  FROM kala_activation_predicates WHERE chart_id = %s`) has **no `ORDER BY`**, and
  `anchors.setdefault(peak, sig_id)` gives the peak to whichever row arrived first; the loop then
  `break`s at `_MAX_DASHA_ANCHORS`. Two builds of identical data can attribute the same
  obstruction to different signals and even select a different anchor set. Doctrine: **§N.7 item
  2** (every selection that reduces a set to one row needs a total `ORDER BY`).
- **F-VIGHNA-4 — FK `ON DELETE CASCADE` from `kala_convergence` silently truncates this table
  while `asset_throughput` still reports success. `MUST` (D-SERVICE / §N.8).** Measured on chart
  `cb73cd3d`: `asset_throughput` says `rows_written = 623, state='stale'` (built 2026-07-27
  14:21, i.e. **after** that chart's `ka_sangam` run at 14:13) but `kala_obstruction` holds
  **6 rows** today; `kala_darshana` says `rows_written = 750` and holds **0 rows**. The 2026-08-07
  `ka_bhavishya_lekha` error message on the same chart records the anomaly detector catching a
  related state/data mismatch verbatim: *"ANOMALY (data present despite state): ka_sangam:
  expected state 'lit', actual 'stale', but 2540 data rows ARE present"*. A `ka_sangam` re-run
  cascade-deletes every downstream row without flipping the downstream asset's state out of
  `lit`/`stale`. Doctrine: **§N.8** (`state` asserts "this asset's data is present"; the detector
  behind it never checks that the rows survived a cascade). Recommend a real
  `integrity_check_sql` as the detector (below) rather than a contract change.
- **F-VIGHNA-5 — `ka_gochara` declared but unread; `bg_combustion_orbs` and
  `kala_activation_predicates` read but undeclared. `NOW`.** Rubric item 2. The `ka_yojaka` edge
  is a real ordering dependency and its absence from `depends_on` is a DAG correctness issue, not
  just bookkeeping.
- **F-VIGHNA-6 — `_SATURN_PROXY_WINDOWS` hardcodes this native's Saturn transits. `NEVER-LATER`
  (log with reason).** Module-level constant, comment: *"known harsh Saturn transits for this
  native (Aries lagna, Aquarius Moon)"*. Currently unreachable in production because `run()`
  hard-raises without `swisseph`, so it is a test-only fallback — but it is exactly the CR-87
  contamination pattern and should be moved into the test module rather than left in the writer.
- **F-VIGHNA-7 — registry health. `NOW` (C12).** Proposed `integrity_check_sql` (this is also the
  F-VIGHNA-4 detector): *"every obstruction row that names a `convergence_id` must still point at
  a live convergence row for the same chart, and the count of obstruction rows must be > 0
  whenever `kala_convergence` for this chart is non-empty"* —
  `SELECT count(*) FROM kala_obstruction o WHERE o.chart_id=$1 AND o.convergence_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM kala_convergence c WHERE c.convergence_id=o.convergence_id AND
  c.chart_id=o.chart_id)` = 0, plus a non-vacuity clause. Proposed
  `expected_volume_formula`: `≈ (min(500, convergence_rows) + dasha_anchors) × avg_detectors_
  firing_per_peak`, inputs `{window_intake_limit: 500, max_dasha_anchors: <const>,
  detector_count: 5}`. `target_floor` = achieved count post-build (§N.4).
- **F-VIGHNA-8 — `catalog_status='DRAFT'` stale + `L3_kala/index.ts` header says
  "STUBBED-PENDING-DATA, 0 rows". `NOW` (D-SERVICE, §N.7).**

**Route recommendation (W2 input):** `changed` — F-VIGHNA-3 (determinism) and F-VIGHNA-7 (the
cascade detector) are in-writer/in-registry fixes; the rest of its value is unlocked by
F-SANGAM-1, so it must be rebuilt after `ka_sangam` regardless.

---

## ka_kalasutra

**One-line identity:** the activation-window materializer — resolves every one of the chart's
~50K activation predicates against its own ayanāṃśa's L1 daśā timeline and emits one row per
matched in-life period.
**Temporal question (D-TIME):** *"In which daśā periods of this native's life is signal S
active, and over what dates?"*

**1. Instrument fit.** **D-TIME** + **D-GROUNDING** (its whole WP-2.1 redesign was to stop
depending on `kala_convergence.peak_date` — which was ~99% NULL for its inputs — and instead
date every activation from a real `chart_dashas` row: *"No fabricated dates (B.10): every date
traces to a chart_dashas row (§N.5)"*). That is exactly the right instrument and the right fix.

**2. Dependencies (declared vs real).** Declared: `{ka_yojaka, ka_sangam, bo_laksana}`.
- `ka_yojaka` ✅ `FROM kala_activation_predicates`.
- `ka_sangam` ✅ `FROM kala_convergence … WHERE signal_id IS NOT NULL` (the *refinement* path).
- `bo_laksana` ❌ **declared-but-unread** — no `bodha_*` query in the writer. The FK
  `kala_activation.signal_id → bodha_msr_signals.signal_id` makes it a real *referential*
  dependency, so this is defensible, but nothing is read.
- **Undeclared reads:** `chart_dashas` (`ga_dashas`, via `services.ka_temporal.
  load_dasha_timeline`) and `public.charts`/birth params (`resolve_birth_date`) — **`ga_dashas`
  is the writer's single largest real input and is not declared.** Hidden edge.

**3. Leverage / NULL check.** Measured, n=335,403 (chart 482012f1):
`activation_start` **2.8% NULL**, `activation_peak_date` 2.8%, `dasha_activation_proximity_score`
**0.0% NULL**, `active_dasha_periods_jsonb='[]'` 2.8%, `activation_predicted_dates_jsonb='[]'`
2.8% — the WP-2.1 fix worked, the ~99%-NULL-date problem is genuinely solved. **But two columns
are 99.6% NULL and four consumers rank on them** (§summary 5):
`orb_strength` **99.6% NULL**, `convergence_score` **99.6% NULL**. Both are copied from
`convergence_map`, which is keyed on `signal_id` equality against `kala_convergence` — and
`ka_sangam` only ever produces windows for ≤260 of the 50,104 predicates.
Consumers reading exactly those columns:
- `query_temporal_activation.ts:191` — `ORDER BY orb_strength DESC NULLS LAST, activation_start,
  id`; `:223/:231/:239/:242/:252` — `max_orb_strength` per family, families sorted by it;
  `:155` — an optional `orb_strength >= $n` filter that silently drops 99.6% of the table.
- `register_d9_judgment.ts:1073–1087` — `judgment_query` picks the best activation row per signal
  by `convergence_score`, with `?? -Infinity`; 99.6% of the time every candidate is `-Infinity`,
  so "best" is arbitrary.
- `register_d8_assess_domain.ts:1949–1950` — `assess_career`/`assess_wealth`/etc. select and
  serve `ka.orb_strength, ka.convergence_score`.
- `platform-mcp/.../kala_views/ahead.ts:1275–1326` — collapses duplicate rows to the
  *"highest-`orb_strength` row per signal"*.
The honest alternative is on the same row and 0.0% NULL: `dasha_activation_proximity_score`.

**4. Grounding tier.** **`pratyaksa`** and correctly so — the dating is a deterministic
resolution of a predicate against an L1 daśā timeline; no classical claim is made or needed.
The `signature_class`-keyed `delta_map` widths in the legacy convergence-path helpers
(`YOGA: 7, DOSHA: 14, DIGNITY: 5, SENSITIVE_POINT: 5` days) are uncited tuning constants —
`pratyaksa`, and those helpers are documented as retained for backward-compat/tests only.

**5. Temporal identity + arbitration.** Question as above. Overlapping engines: `ka_avadhi`
(per-period dossiers over the same `chart_dashas` periods), `ka_taranga` (monthly amplitude for
the same signals), `ka_kshetra` (λ over the same days), `ka_sangam` (windows for the same
signals). Overlap cell **O-5**. Nothing arbitrates. Note this is the *only* asset in the batch
that preserves the **ayanāṃśa dimension** (`ayanamsha_id`, 5 values, 66,957–67,272 rows each) —
so it is the natural place to anchor an ayanāṃśa-aware arbiter, and the natural evidence for
F-SANGAM-10.

**6. Service.** Heavily consumed and genuinely load-bearing: `query_temporal_activation.ts` (12
refs), `register_d8_assess_domain.ts` (15), `register_d9_judgment.ts` (14), `ahead.ts` (9),
`now.ts`, `registry_bridge.ts`, `kala_yoga_activation_get`. **`judgment_query` and the four
`assess_*` tools are headline product surfaces.** No `density_contract`; `query_temporal_
activation.ts` does build families with counts, which is the right shape. Drill to L1: row →
`signal_id` → `bodha_msr_signals.constituent_facts_array` → `chart_facts` = 3 hops; but
`active_dasha_periods_jsonb` names the `chart_dashas` periods directly ⇒ **≤2 hops for the
timing claim specifically.** Good.

**7. Measured cost.** `estimated_seconds = 33`. **Measured p50 486.9 s** (min 416.6, max 620.4,
n=5 since 2026-08-01) — a **14.8×** under-estimate, the worst in the batch.
Rows/chart measured: 335,403 (482012f1) / 336,093 (1c826d5a) / 335,447 (cb73cd3d).
Storage: `pg_total_relation_size('kala_activation')` = **2,274 MB** for 672,551 rows across 3
charts (~3.5 KB/row all-in). Measured average column sizes: `active_dasha_periods_jsonb`
**1,166 B**, `activation_predicted_dates_jsonb` **478 B**, `source_citation` 62 B.

**Volume anomaly — verdict.** **NOT accretion. The estimate is stale.** Evidence, all measured:
(i) the writer opens with `DELETE FROM kala_activation WHERE chart_id = %s` — §N.3-compliant
per-chart delete-then-insert; (ii) `UNIQUE (chart_id, signal_id, ayanamsha_id, source_citation)`
exists; (iii) three independently-built charts land within 0.2% of each other (335,403 /
336,093 / 335,447) — accretion across builds would diverge, and the native chart has been rebuilt
many times (30+ `build_run_assets` rows); (iv) the arithmetic closes:
**50,104 predicates × ~6.7 in-life daśā periods each = 335,403**, with 5 ayanāṃśas ×
~10,020 signals = 50,104 predicates and up to 9 distinct `period=` indices observed
(measured: `count(DISTINCT split_part(source_citation,'period=',2)) = 9`; the largest per-index
groups are 8,176 rows for `krishnamurti period=0..7`). The 33 s figure predates the CR-109
per-period fan-out, which multiplied the row count ~6.7× in one change.

**8. Findings.**

- **F-KALA-1 — `orb_strength` and `convergence_score` are 99.6% NULL and four designed consumers
  rank on them. `MUST`.** Full evidence in item 3. This is the batch's highest-value leverage
  finding: `judgment_query` — the product's headline verdict tool — selects its representative
  activation row by a column that is NULL 99.6% of the time. Doctrine: rubric item 3; **§N.6
  item 3** (a verdict layer must report the honest gap rather than a hollow-but-populated
  envelope); **§N.7 item 2** (a selection reducing a set to one row must have a real total
  order). Two independent fixes are available: (a) rank on
  `dasha_activation_proximity_score` (0% NULL) with `orb_strength` as a tiebreak, and/or (b) join
  `kala_convergence` by *window overlap* rather than `signal_id` equality so far more rows get a
  real orb.
- **F-KALA-2 — `estimated_seconds = 33` vs measured p50 487 s. `NOW`.** 14.8× under-estimate; the
  cockpit's build-time projection for a chart is wrong by ~7.5 minutes on this asset alone.
  Measure-and-set, per §N.4's "achieved, not aspirational" spirit.
- **F-KALA-3 — ~85% of the 2.27 GB is one jsonb payload repeated per period row. `NOW`.** The
  writer's own comment states the redundancy: *"Every row carries the SAME full
  active_dasha_periods_jsonb / predicted_dates listing"*. Measured 1,644 B of jsonb per row ×
  335,403 rows ≈ 550 MB/chart, of which ~6.7−1 / 6.7 ≈ 85% is duplication. Not a correctness bug;
  a real storage/scan cost on the layer's largest table. Options: hoist the shared payload to a
  per-`(chart, signal, ayanamsha)` side table, or store it only on `period=0`.
- **F-KALA-4 — `source_citation` is a per-row unique string, so the UNIQUE index cannot detect
  duplicates. `NOW`.** The key is `(chart_id, signal_id, ayanamsha_id, source_citation)` and the
  citation embeds `:src=<resolution_source>:period=<idx>`; measured, essentially every row has its
  own citation value. The writer's own comment concedes the `ON CONFLICT` is *"a true no-op safety
  net (should never actually fire)"*. The natural key it *means* is `(chart_id, signal_id,
  ayanamsha_id, period_idx)` — `period_idx` should be a real column, not embedded in a text
  citation that also has to carry provenance. As it stands, `natural_key_partition` on
  `asset_registry` is NULL and the effective natural key is undeclared anywhere.
- **F-KALA-5 — `ga_dashas` is the largest real input and is undeclared; `bo_laksana` is declared
  and unread. `NOW`.** Rubric item 2.
- **F-KALA-6 — 83% of rows are `signature_class='SUBSYSTEM'`. `NEVER-LATER` (log).** Measured
  class mix on the native: SUBSYSTEM 278,258 · DISPOSITOR_RELATIONAL 46,763 · DIGNITY 7,560 ·
  CLASSIFY_RESIDUAL 1,639 · DOSHA 976 · YOGA 207. That mix originates in `ka_yojaka`/`bo_laksana`
  (out of this batch's write-set — **hand-off**, not an L3 NOW item), but it is what makes this
  the layer's largest table and it is worth stating that 83% of the volume is the least
  discriminating class.
- **F-KALA-7 — registry health. `NOW` (C12).** Proposed `integrity_check_sql`: (i) *every dated
  row's window must lie inside a real L1 daśā period for the same chart and ayanāṃśa* —
  `SELECT count(*) FROM kala_activation a WHERE a.chart_id=$1 AND a.activation_start IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM chart_dashas d WHERE d.chart_id=a.chart_id AND
  d.ayanamsha_id=a.ayanamsha_id AND d.start_date <= a.activation_start AND d.end_date >=
  a.activation_end)` = 0 (this is the direct machine test of the writer's own B.10/§N.5 claim);
  (ii) *no orphan signal* — every `signal_id` resolves in `bodha_msr_signals`; (iii) *no pre-birth
  activation* — `activation_start >= birth_date`. Proposed `expected_volume_formula`:
  `rows = Σ_predicates |in-life dasha periods matched|`, inputs
  `{predicate_count: <from kala_activation_predicates>, ayanamsha_count: 5,
  avg_periods_per_predicate: ~6.7}` — derived, not pinned. `target_floor` = achieved count (§N.4).
- **F-KALA-8 — `catalog_status='DRAFT'` is stale on the asset that feeds `judgment_query` and
  four `assess_*` tools. `NOW` (D-SERVICE).** The most consequential of the six DRAFT
  mislabels.

**Route recommendation (W2 input):** `rebuild_only` for the data itself (the writer's dating
logic is correct and §N.3-clean; the volume is honest) — **but the four consuming call sites in
F-KALA-1 are `changed`, and they live in the serving plane, not in this writer.** Registry
metadata (F-KALA-2, 7, 8) is a metadata-only `changed`.

---

## ka_kala_darshana

**One-line identity:** the display view — takes the top 750 convergence windows, nets them
against obstruction, and writes a labelled, narrated row per window.
**Temporal question (D-TIME):** *"Net of what obstructs it, how strong is this window and what
should we call it?"*

**1. Instrument fit.** **D-SERVICE** (it is the read-model) + **D-SALIENCE** (`effective_score`
is the salience number) + **D-SYNTHESIS**. Right instrument in principle; in practice it is a
thin projection that inherits every upstream pathology and adds three of its own.

**2. Dependencies (declared vs real).** Declared: `{ka_sangam, ka_vighnakara, ka_kalasutra}`.
- `ka_sangam` ✅ `FROM kala_convergence … LIMIT 750`. `ka_vighnakara` ✅ `FROM kala_obstruction`.
- `ka_kalasutra` ❌ **declared-but-unread** — the writer contains no `kala_activation` query.
  No undeclared reads. So: 2 of 3 declared edges real, 1 spurious.

**3. Leverage / NULL check.** Measured, n=750: `peak_date` **0% NULL**;
`obstruction_summary='[]'` on 403/750 (53.7%); `narrative.caution` non-null on 336/750 (44.8%).
No high-NULL column. The leverage losses are label collapse and mode collapse:
- **`net_label` takes 2 of 6 legal values** (auspicious_strong 648, auspicious_moderate 102);
  four values unreachable (§F-VIGHNA-1).
- **`effective_score` spans 0.495–0.797** — a 0.30-wide band on a `[0,1]` column.
- **100% of rows are Mode C** (measured by joining back: C/lifetime 666, C/near 84). Modes A, B
  and D contribute **zero** display rows.
- The `signal_id` and `convergence_id` are carried, so drill works.

**4. Grounding tier.** The narrative strings are **`pratyaksa`** — template prose over computed
numbers, no classical claim — and the `_compute_net_label` thresholds (0.70/0.45/0.20/0.40) are
uncited tuning constants, also `pratyaksa`. That is honest and fine. What is *not* fine is
narrating a `pratyaksa` composite in language that implies classical grading (below).

**5. Temporal identity + arbitration.** Question as above. It is itself a **two-engine composer**
(`ka_sangam` × `ka_vighnakara`) and is therefore the closest thing in the batch to an arbiter
already — but it composes multiplicatively rather than adjudicating, and it consults neither
`ka_kshetra`'s λ nor `ka_taranga`'s amplitude for the same window (overlap **O-5**).

**6. Service.** Consumers: `query_temporal_view.ts` (registered), `kala_temporal.ts` (11 refs),
`now.ts` (5 refs — the `darshana` block of `kala_now_get`), `ka_jivana_parva` and
`ka_bhavishya_lekha` internally. Real. **`L3_kala/index.ts` header still calls it
`STUBBED-PENDING-DATA, 0 rows`.** No `density_contract`. `now.ts` does carry a
`darshana_reachable` honesty flag and a `computedCoverage('kala_darshana_confluence')` /
`honestEmptyCoverage('kala_darshana_confluence', …)` pair — good §N.6 practice, and the pattern
the other five should copy.

**7. Measured cost.** `estimated_seconds = 1`; **measured p50 3.2 s** (min 1.9, max 3.8, n=5).
Rows: 750 / 750 / **0** (cb73cd3d — cascade-wiped, see F-VIGHNA-4, while `asset_throughput`
still records `rows_written=750`). All four C12 registry fields NULL.

**8. Findings.**

- **F-DARSH-1 — `_compute_effective_score(conv_score or 0.5, …)` turns a genuine computed 0.0
  into a favourable 0.5. `MUST`.** Writer line ~72:
  `effective = _compute_effective_score(conv_score or 0.5, obstructions)`. Python truthiness
  makes `0.0` fall to the literal `0.5`, i.e. mid-scale. This is **verbatim the defect class
  CLAUDE.md §N.7 item 6 names** (*"the `5.0`-on-computed-zero-`grade` defect … a
  favorable/neutral-sounding invention standing in for 'I don't know'"*). It is currently masked
  because Mode C never scores 0.0 — but it will fire the moment F-SANGAM-1 lets Mode A/B rows
  through, and those legitimately score near zero. Fix: `if conv_score is None`.
- **F-DARSH-2 — every served row is narrated `"independent sweep"`, which is Mode B's meaning,
  while 100% of rows are Mode C. `MUST` (§N.7 item 1).**
  `mode_label = 'daśā-aligned' if mode == 'A' else 'independent sweep'` — a two-way branch over a
  four-value enum. Mode C is a sign-ingress trigger and Mode D is an SAV-bindhu window; neither is
  a sweep. Measured: 750/750 rows carry the wrong mode description. A grade/label assignment keyed
  off a proxy instead of the actual fact it reports.
- **F-DARSH-3 — a `caution` and an `auspicious_strong` label ride the same row. `MUST`.**
  Measured: 336/750. See F-VIGHNA-1 for the mechanism. Doctrine: **§N.6 item 3**.
- **F-DARSH-4 — the 750-row intake is 100% Mode C. `MUST` (inherited from F-SANGAM-1).** This is
  the point at which the mode collapse becomes *user-visible*: `kala_now_get`'s `darshana` block
  and `query_temporal_view` are the layer's display surface, and neither can ever show a
  daśā-aligned window.
- **F-DARSH-5 — `ka_kalasutra` declared but unread. `NOW`.** Rubric item 2.
- **F-DARSH-6 — no ayanāṃśa dimension. `NOW`.** Inherited from `kala_convergence` (F-SANGAM-10);
  worth restating because this is the *served* surface, so the undeclared collapse is what a
  reader actually receives.
- **F-DARSH-7 — registry health. `NOW` (C12).** Proposed `integrity_check_sql`: (i) *one display
  row per convergence window, and every display row points at a live window* —
  `SELECT count(*) FROM kala_darshana d WHERE d.chart_id=$1 AND NOT EXISTS (SELECT 1 FROM
  kala_convergence c WHERE c.convergence_id=d.convergence_id AND c.chart_id=d.chart_id)` = 0
  (the partial UNIQUE index already guarantees distinctness, so this closes the other direction);
  (ii) *label/score coherence* — no row may carry `net_label LIKE 'auspicious%'` while
  `obstruction_summary` contains a `severity='severe'` entry (this is exactly the F-DARSH-3
  detector); (iii) *window ordering* — `window_start <= peak_date <= window_end`. Proposed
  `expected_volume_formula`: `min(750, convergence_rows_for_chart)`, inputs
  `{display_limit: 750}` — trivially derivable and currently NULL.
- **F-DARSH-8 — `catalog_status='DRAFT'` stale + stale `index.ts` header. `NOW` (D-SERVICE,
  §N.7).**

**Route recommendation (W2 input):** `changed` — F-DARSH-1 and F-DARSH-2 are two-line writer
fixes with direct §N.7 citations, and the asset must be rebuilt after `ka_sangam` anyway.

---

## ka_jivana_parva

**One-line identity:** the life-arc chapter artifact — one narrated row per Vimśottarī MD, per AD
within it, and per PD of the currently-running AD, clipped to the lived portion of life.
**Temporal question (D-TIME):** *"What is the biographical quality and theme of this daśā chapter
of the native's life?"*

**1. Instrument fit.** **D-SYNTHESIS** + **D-TIME** + **D-SERVICE**. The right instrument, and
the best-reasoned writer in the batch on two counts: the **T-9 pre-birth clip** (an MD whose
theoretical "balance of daśā" start predates birth is served from birth, and one that ends before
birth is dropped — *"a 1984 native has no lived experience of a chapter that began in 1950"*), and
the **system/ayanāṃśa scoping** (`system_id='vimshottari' AND ayanamsha_id='lahiri_chitrapaksha'`,
with an explicit comment that omitting it blends 7 systems × 5 ayanāṃśas into a meaningless
chapter list and overflows `smallint`). Both are exactly the right calls.

**2. Dependencies (declared vs real).** Declared: `{ka_kala_darshana, ka_dasha_kala, ka_sangam,
ka_yojaka, ga_dashas}`.
- `ga_dashas` ✅ `FROM chart_dashas` (levels 1, 2, and current-3). `ka_sangam` ✅
  `FROM kala_convergence`. `ka_kala_darshana` ✅ `LEFT JOIN kala_darshana` for `effective_score`.
  `ka_yojaka` ✅ `LEFT JOIN LATERAL … kala_activation_predicates` for `signature_class`.
- `ka_dasha_kala` ❌ **declared-but-unread** — no service call in the writer.
- No undeclared reads. 4 of 5 declared edges real — the cleanest dependency declaration in the
  batch.

**3. Leverage / NULL check.** Measured, n=100 (chart 482012f1):
`avg_effective_score` NULL on the rows with no windows in span (e.g. parva_index 7);
`high_convergence_count` = 0 on those. The leverage losses:
- **`parva_quality` never takes the value `peak`.** Measured distribution: `building` 74,
  `receding` 15, `consolidating` 8, `transitional` 3, **`peak` 0**. `_assign_quality` requires
  `avg_score >= 0.55` (ongoing) or `>= 0.60` (past); `avg_effective_score` measured range is
  0.000–0.513 across all 100 rows. The strongest label in the vocabulary is unreachable — so a
  reader can never be told which chapter of their life was the peak of it. Root cause is upstream
  (the same score-scale problem), but it lands here as a user-visible gap.
- **74/100 rows are `building` because every ongoing period gets `building` regardless of
  evidence.** `if is_ongoing and avg_score and avg_score >= 0.55: return 'peak'` / `if is_ongoing:
  return 'building'`. Any period ending in or after the current year is `building` by default —
  a label with no detector distinguishing it from "we have no evidence". §N.8.
- **`avg_score` truthiness bug** on the same line: a genuinely computed `0.0` is falsy and
  short-circuits, indistinguishable from "no windows in span".

**4. Grounding tier.** `theme_keywords` (`_PLANET_THEMES`: Sun → authority/identity/recognition,
Jupiter → expansion/wisdom/abundance, …) is a **`sruti`-adjacent but uncited** planetary-
significations table — classical in origin, but with no citation in the writer, so it must be
labelled **`yukti`** at best and honestly **`pratyaksa`** until a `classical_citation` is attached.
`parva_quality` and the narrative are `pratyaksa`.

**5. Temporal identity + arbitration.** Question as above. Overlapping engines: **`ka_avadhi`**
answers a near-identical question over the same `chart_dashas` periods ("what is the lord's
condition and which promises activate in period P") and is `catalog_status=CURRENT` with 3,344
rows — this is the sharpest **direct duplication** in the layer and belongs in overlap cell
**O-1/O-5**. Also `ka_taranga` (monthly amplitude across the same spans) and `ka_kshetra` (λ over
the same days). Nothing arbitrates; `ka_jivana_parva` and `ka_avadhi` can disagree about the same
period with no reconciliation surface.

**6. Service.** Consumers: `query_life_arc.ts` (registered L3 capability), `story.ts` (8 refs —
`kala_story_get`), `register_p1_synthesis.ts` (3 refs). Real. No `density_contract`. Drill to L1:
the row names `dasha_planet` + `start_year/end_year` but carries **no `chart_dashas` row key**, so
a reader cannot drill from a parva to the exact L1 daśā row in one hop — **>2 hops**, and
ambiguous (see F-PARVA-1).

**7. Measured cost.** `estimated_seconds = 1`; **measured p50 2.3 s** (min 1.3, max 2.6, n=5).
Rows: 100 / 100 / 109. All four C12 registry fields NULL.

**8. Findings.**

- **F-PARVA-1 — MD, AD and PD rows are mixed in one flat table with no level discriminator.
  `MUST`.** Measured on the native: `parva_index 8 = Saturn 1991–2010` (a mahādaśā) sits between
  `parva_index 7 = Saturn 1991–1994` and `parva_index 9 = Saturn 1991–1994` (antardaśās) — three
  rows, overlapping year ranges, same planet, and **nothing in the served columns says which level
  each is.** The level is recoverable only by string-parsing `source_citation`
  (`ka_jivana_parva:v2.0:MD=Saturn` vs `…:MD=Saturn:AD=Mercury`). A consumer rendering a life arc
  will double-count or interleave. The only UNIQUE key is `(chart_id, parva_index)` — a loop
  counter, not a natural key. Doctrine: **§N.7 item 2** (a serving surface must be able to pin the
  row it means) + **§N.6 item 1** (never present differently-graded rows as one undifferentiated
  list). Fix: add a `parva_level smallint` (1/2/3) column + a real natural key
  `(chart_id, parva_level, dasha_planet, start_year)`.
- **F-PARVA-2 — `asset_registry.volume_explanation` says "One row per mahadasha (typically 9 for a
  full Vimshottari cycle)"; measured 100. `MUST` (§N.7 narration fidelity).** The registry
  description is 11× wrong and describes a design (MD-only) the writer explicitly superseded at D7
  and O6. The cockpit reads this table's metadata.
- **F-PARVA-3 — `parva_quality='peak'` is unreachable; 74% of rows are the no-evidence default
  `building`. `NOW`.** Measured distributions in item 3. Doctrine: **§N.8** (a label must be
  produced by a detector that measures the claim; "ongoing" is not evidence of "building").
- **F-PARVA-4 — the `avg_score` truthiness short-circuit conflates a computed 0.0 with
  no-data. `NOW` (§N.7 item 6).** `if is_ongoing and avg_score and avg_score >= 0.55`.
- **F-PARVA-5 — `ka_dasha_kala` declared but unread. `NOW`.** Rubric item 2. Notable because
  `ka_dasha_kala` is the cross-system agreement service — consulting it is precisely what would
  turn a parva's quality into a concordance-aware judgment (D-TIME).
- **F-PARVA-6 — direct functional overlap with `ka_avadhi` (CURRENT, 3,344 rows) is undeclared
  and unarbitrated. `NEVER-LATER` (log with reason).** Both narrate the same daśā periods from
  the same L1 rows. Not a correctness bug today; it is the clearest candidate for the "one arbiter
  surface per (domain, range)" rule, and should be logged as such rather than resolved in-layer
  without a design decision.
- **F-PARVA-7 — registry health. `NOW` (C12).** Proposed `integrity_check_sql` (once F-PARVA-1
  lands): (i) *no gaps or overlaps within a level* — for `parva_level=1`, consecutive rows ordered
  by `start_year` must tile without overlap; (ii) *no pre-birth chapter* — `min(start_year) >=
  birth_year` (the machine test of the T-9 clip the writer already implements); (iii) *every
  parva's `(dasha_planet, start_year)` resolves to a real `chart_dashas` row at the matching
  level for `system_id='vimshottari'`. Proposed `expected_volume_formula`:
  `MD_count + AD_count_within_lived_MDs + PD_count_of_current_AD`, inputs
  `{system_id: 'vimshottari', ayanamsha_id: 'lahiri_chitrapaksha', levels: [1,2,3-current]}`.
- **F-PARVA-8 — `catalog_status='DRAFT'` stale. `NOW` (D-SERVICE).**

**Route recommendation (W2 input):** `changed` — F-PARVA-1 requires a migration (new column + key)
plus a writer change, and F-PARVA-2 is a registry text correction; neither can be reached by
`rebuild_only`.

---

## ka_bhavishya_lekha

**One-line identity:** the forward-projection artifact — the top 100 future display windows,
ranked, tiered, domain-labelled, and issued with a falsifiability hook.
**Temporal question (D-TIME):** *"What are the ranked, falsifiable events this chart projects
over the next five years, and how would we know if they did not happen?"*

**1. Instrument fit.** **D-TIME** + **D-GROUNDING** (falsifiability) + **D-SERVICE**, and it is
the asset that most directly carries the MACRO_PLAN Ethical Framework obligation (*"probabilistic,
calibrated, auditable outputs"*). The instrument is right and its `falsifiability` /
`source_chain` / `outcome_recorded` design is genuinely good — it is built for the L5 calibration
loop. **Its current output does not meet that obligation** (F-BHAV-1/2).

**2. Dependencies (declared vs real).** Declared: `{ka_kala_darshana, ka_vighnakara, ka_sangam,
bo_laksana}`.
- `ka_kala_darshana` ✅ `FROM kala_darshana kd`. `ka_sangam` ✅ `JOIN kala_convergence kc`.
  `bo_laksana` ✅ `SELECT signal_id, signal_type_id FROM bodha_msr_signals` (for domain
  inference).
- `ka_vighnakara` ⚠️ **read only through a dead filter** — `AND kd.net_label NOT IN
  ('obstructed_severe')`; measured, `obstructed_severe` occurs on **0 of 750** darshana rows, so
  the obstruction dependency excludes nothing. Effectively unread.
- Undeclared: `information_schema.columns` (a schema probe — benign, and correctly done without a
  `rollback()` so the FROZEN contract is honoured). 3 of 4 declared edges real.

**3. Leverage / NULL check.** Measured, n=100 (chart 482012f1) — and this is where the asset
fails:

| Measurement | Value |
|---|---|
| distinct `peak_date` | **1** (`2027-10-20`) |
| distinct `effective_score` | **1** (`0.700`) |
| distinct `convergence_id` | 100 |
| distinct `signal_id` | 100 |
| `probability_tier` distribution | `tier_1_high` **100/100** |
| `domain` distribution | `character` 94 · `career` 4 · `relationship` 2 |
| `outcome_recorded` | 0 |

Every one of the 100 "ranked projections" points at the **same single day** with the **same
score** in the **same tier**. `projection_rank` 1…100 is an arbitrary tie order over 100 equal
scores (the SQL is `ORDER BY kd.effective_score DESC NULLS LAST LIMIT 100` with no tiebreak).
Each row nevertheless ships its own `falsifiability` hook — *"Observable within ±21 days of
2027-10-20: personal transformation (mindset shift, psychological change)"* for 94 of them —
so the artifact presents **100 independently falsifiable claims that are one claim repeated 100
times**. If the L5 outcome loop scores these, one real-world observation resolves 94 predictions
at once, which would badly corrupt any calibration statistic computed from them.

**4. Grounding tier.** **`pratyaksa`.** The tiers, the ±21-day window, and the domain-confirmation
sentences are instrument-emergent conventions with no classical claim — that is honest and
correct. What is dishonest is dressing a `pratyaksa` composite in calibrated-probability language
(F-BHAV-2).

**5. Temporal identity + arbitration.** Question as above. Overlapping forward engines:
`ka_kshetra`'s `kala_field_windows` (36,492 rows, λ-based forward windows for the same days),
`phala_anchors` (`ph_nimitta`, which FKs to **both** `kala_convergence` and `kala_bhavishya`),
`ph_sankrama` (cascade lag), `ph_muhurta`. Overlap cell **O-8**: four forward engines, no
reconciliation. `phala_anchors`'s dual FK means L4 currently *inherits* both L3 forward answers
rather than adjudicating between them — which makes this the single most important cell for the
arbiter to cover, because it is where L3's disagreement is silently laundered into L4.

**6. Service.** Consumers: `query_projections.ts` (registered), `query_temporal_activation.ts`
(6 refs — the forward-window fallback), `ahead.ts` (6 refs — `kala_ahead_get`), `now.ts` (3),
`promise_gate.ts` (3), `register_p1_aliases.ts` (3); plus `phala_anchors.bhavishya_id` FK. Real,
and reaching a headline surface (`kala_ahead_get`). No `density_contract`. Drill: `source_chain`
carries `convergence_id` + `mode` + `confidence` ⇒ **1 hop to `kala_convergence`, 2 to
`bodha_msr_signals`** — the best drill path in the batch.

**7. Measured cost.** `estimated_seconds = 1`; **measured p50 2.0 s** (min 0.5, max 2.2, n=6).
Rows: 100 / 100 / **0** (cb73cd3d — `state='error'`, `rows_written=0`, honest: *"DEP-ASSERT:
declared dependency(ies) not lit before run: ka_kala_darshana(stale), ka_sangam(stale),
ka_vighnakara(stale) — refused to build on incomplete/missing upstream data"*, which is the
DEP-ASSERT gate working exactly as designed). All four C12 registry fields NULL.

**8. Findings.**

- **F-BHAV-1 — all 100 projections collapse to one date, one score, one tier. `MUST`.** Measured
  in item 3. The layer's headline predictive deliverable currently makes one claim wearing 100
  hats, with 100 separate falsifiability hooks pointing at the same 42-day window. Root cause is
  F-SANGAM-1 (Mode C's constant scores tie in bulk, and Mode C windows cluster on shared sign-
  ingress dates) plus the untiebroken `ORDER BY`. Doctrine: **§N.6 item 3** (never substitute a
  populated-looking but hollow envelope for an honest result) + **B.10**.
- **F-BHAV-2 — the narrative asserts calibrated probability over a substrate that stamps itself
  uncalibrated. `MUST`.** `_TIER_LABELS['tier_1_high'] = 'High probability (>=70% convergence,
  clear activation)'` — `effective_score` is a `[0,1]` product of catalog constants, not a
  probability, and reading `0.70` as "70%" is a category error. `_build_projection_narrative`'s
  `caveat` reads *"This projection is probabilistic and calibrated."* Measured against it:
  `kala_convergence.tier_basis = 'relative_uncalibrated'` on **100% (14,868/14,868)** of rows, and
  `mimamsa` calibration is sealed in STRUCTURAL mode by design. Doctrine: **§N.7 item 5**
  (`two_pass_verified` on a fact says nothing about the sentence that grades it) + **item 6**
  (an honest null beats an invented judgment) + MACRO_PLAN §Ethical Framework. The fix is a
  wording fix, not a modelling fix: say "structural prior, uncalibrated" and let the tier carry
  `tier_basis` through from `kala_convergence`. The vocabulary already exists —
  `kala_envelope.ts:62`'s `ArgumentVerdictTier = 'structural_prior' | 'calibrated_provisional' |
  'calibrated' | 'unresolved'`.
- **F-BHAV-3 — `projection_rank` has no deterministic tiebreak. `MUST`.** `ORDER BY
  kd.effective_score DESC NULLS LAST LIMIT 100` over 100 identical scores: the rank assignment,
  and therefore *which* 100 of the eligible windows are selected at all, varies between builds of
  identical data. Doctrine: **§N.7 item 2** (a selection reducing a set to one row — here to a
  top-100 — needs a total `ORDER BY`).
- **F-BHAV-4 — 94/100 rows are `domain='character'`. `NOW`.** Inherited from
  `kala_convergence.domain` (measured: character 9,221 · career 4,153 · wealth 956 · NULL 478 ·
  spirituality 27 · relationship 25 · health 8), which comes from
  `bodha_msr_signals.domains_affected_array[0]`. A forward-projection surface where 94% of
  predictions are "personal transformation" is not actionable. Root cause is an L2 domain
  distribution — **hand-off to the Bodha layer**, not an L3 NOW item; the L3-side mitigation is
  a per-domain quota in the top-100 selection (the same fix `ka_sangam`'s
  `_select_top_predicates_with_class_quota` already applies one level up, and for exactly this
  reason).
- **F-BHAV-5 — `ka_vighnakara` is a declared dependency whose only use is a filter that excludes
  nothing. `NOW`.** `net_label NOT IN ('obstructed_severe')`; measured 0/750 such rows.
- **F-BHAV-6 — `volume_explanation` says "Up to 50 ranked projections … over a 3-year forward
  horizon"; the writer does `LIMIT 100` over `today + 5 years`. `NOW` (§N.7).** Registry text
  wrong on both the count and the horizon.
- **F-BHAV-7 — registry health. `NOW` (C12).** Proposed `integrity_check_sql`: (i) **the direct
  F-BHAV-1 detector** — *a projection set must not be degenerate*:
  `SELECT count(DISTINCT peak_date) FROM kala_bhavishya WHERE chart_id=$1` must be > 1 whenever
  `count(*) > 1` (an honest, non-count-pinning invariant that would have caught this the day it
  appeared); (ii) *rank distinctness and contiguity* — `projection_rank` values form `1..n` with
  no gaps or duplicates; (iii) *forward-only* — `peak_date >= computed_at::date`;
  (iv) *chain resolves* — every `convergence_id` resolves in `kala_convergence` for the same
  chart. Proposed `expected_volume_formula`:
  `min(100, future_darshana_rows_in_horizon)`, inputs `{projection_limit: 100, horizon_years: 5}`.
- **F-BHAV-8 — `catalog_status='DRAFT'` stale (feeds `kala_ahead_get` + `phala_anchors`). `NOW`
  (D-SERVICE).**

**Route recommendation (W2 input):** `changed` — F-BHAV-2 and F-BHAV-3 are writer-local and must
be fixed before any rebuild, because a rebuild alone would regenerate 100 identical
"calibrated ≥70% probability" claims. F-BHAV-1 additionally requires F-SANGAM-1 upstream.

---

## PART 3 — CROSS-CUTTING FINDINGS (batch-level)

- **F-CONC-1 — Three implementations of one testimony shape, three stance vocabularies. `NOW`
  (D-TIME).** `KpSchoolVoice.agreement: 'concurs'|'dissents'|'not_comparable'`;
  `AgnivasaConventionBVoice.agreement: 'agrees'|'diverges'|'not_comparable'`;
  `A5GocharaAgreement.agreement: 'concurs'|'dissents'|'insufficient_data'`. All three already
  carry `state: 'computed'|'honest_empty'` + `empty_reason` + a template-composed `claim`. Unify
  into one `EngineTestimony` before adding a fourth. Doctrine: **§N.6 item 4** (density signalling
  is data — a machine-readable contract cannot have three vocabularies).
- **F-CONC-2 — `kala_paddhati_profile` row 7 carries `constraint_role='hard'` while its own
  `provenance` prose says "informational … voice ONLY … NEVER enters the residence hard-gate".
  `MUST`.** The prose is correct and the code implements the prose; the machine-readable field
  contradicts both. Doctrine: **§N.7 item 4 / §N.8** — a field that reads "hard gate" with no code
  path enforcing a hard gate. Fix by promoting the prose to an `arbitration_role` column (§1.3).
- **F-CONC-3 — the arbitration rule lives in a free-text `provenance` column. `NOW` (D-TIME).**
  No machine-readable field says "Convention B is informational, Convention A gates". A CI census
  cannot check it; a serving surface cannot route on it. Same doctrine as F-CONC-2.
- **F-CONC-4 — `kala_paddhati_profile`'s `version` selection is client-side string-sort.
  `NEVER-LATER` (log).** Documented honestly in `query_kala_paddhati_profile.ts` (*"`paddhati_v10`
  would sort below `paddhati_v2` without zero-padding"*). Not a defect today (the seeded data is
  zero-padded); it is a latent ordering hazard the arbiter must not inherit.
- **F-CONC-5 — `kala_now_get` emits ~20 top-level engine blocks with no `density_contract` and no
  `hardFloor` trim protection. `NOW` (§N.6 item 2).** `explain.ts` declares both; `now.ts`
  declares neither (grep: zero `density_contract` hits in `now.ts`, zero across all 20
  `L3_kala/*.ts` capability files). The moment a `concordance`/dissent block lands there, the
  generic biggest-section-first trimmer can zero it — the exact regression §N.6 item 2 was written
  about. `kalaEvidenceTrimmableSection()` (`kala_envelope.ts:643`) is the ready-made pattern.
- **F-CONC-6 — `_c_cross_dasha_agreement` normalises by a hardcoded `7.0`; `chart_dashas` holds
  **9** `system_id`s. `NOW` (§N.7 item 3).** Measured systems: chara_karaka, mudda, yogini,
  vimshottari, kalachakra, ashtottari, naisargika, vimshottari_kp, narayana.
  `_c13_school_consensus_score` also divides by a hardcoded `7.0`. A wrapper-local constant
  shadowing a countable quantity.
- **F-CONC-7 — all six assets' `size_sql` is `pg_total_relation_size('<table>')`, not
  chart-scoped, on `scope='per_chart'` assets. `NOW` (C12).** With 3 charts resident the cockpit
  over-reports each chart's footprint ~3×. `count_sql` is correctly chart-scoped on all six
  (`… WHERE chart_id = $1`) — verified.
- **F-CONC-8 — all six have `integrity_check_sql`, `expected_volume_formula`,
  `expected_volume_inputs` and `target_floor` NULL. `NOW` (C12/D-126).** Per-asset proposals at
  F-SANGAM-12, F-VIGHNA-7, F-KALA-7, F-DARSH-7, F-PARVA-7, F-BHAV-7. None is a bare `count(*) = N`
  pin; each is a cross-table or ordering/tiling invariant.
- **F-CONC-9 — `catalog_status='DRAFT'` is stale on all six. `NOW` (D-SERVICE).** Every target
  table has registered serving-plane consumers; `L3_kala/index.ts`'s own header still describes
  two of them as `STUBBED-PENDING-DATA, 0 rows`.
- **F-CONC-10 — hard-floor note.** `kala_gochara_windows_archive_20260805` (35,620 rows),
  `kala_gochara_windows__ssv_20260728c` (1,267) and the five `*__ssv_20260728b` shadow tables
  (`kala_activation__ssv…` 337,270 · `kala_convergence__ssv…` 34,046 · `kala_darshana__ssv…` 750 ·
  `kala_obstruction__ssv…` 723 · `kala_jivana_parva__ssv…` 200 · `kala_bhavishya__ssv…` 100) are
  the v1 gochara corpus and pre-change snapshots named in the brief's hard floor. **No finding in
  this document proposes touching any of them.** Flagged here so W2 can see they exist and are
  adjacent to the tables it will rebuild.

---

## PART 4 — ROUTE RECOMMENDATIONS (summary)

| Asset | Route | One-line justification |
|---|---|---|
| `ka_sangam` | **`changed`** | The arbiter's home; five `MUST` dead-current defects (0.380 of 1.0 weight budget) are small local fixes with large measured effect — a rebuild without them re-materialises the same zeros. |
| `ka_vighnakara` | **`changed`** | Determinism fix (F-VIGHNA-3) + the cascade detector as `integrity_check_sql` (F-VIGHNA-4/7); must rebuild after `ka_sangam` regardless. |
| `ka_kalasutra` | **`rebuild_only`** (data) + `changed` (registry metadata) | Writer logic is correct and §N.3-clean; the 671K rows are honest. The four NULL-ranking consumers (F-KALA-1) are serving-plane changes, not writer changes. |
| `ka_kala_darshana` | **`changed`** | Two two-line §N.7 defects (`or 0.5` on a computed zero; "independent sweep" on 750/750 Mode C rows) must not survive a rebuild. |
| `ka_jivana_parva` | **`changed`** | F-PARVA-1 needs a migration (level column + real natural key); F-PARVA-2 is a registry text correction. Neither is reachable by rebuild. |
| `ka_bhavishya_lekha` | **`changed`** | A rebuild alone would regenerate 100 identical claims labelled "calibrated ≥70% probability"; F-BHAV-2/3 are writer-local prerequisites. |

**Ordering constraint for W2:** `ka_sangam` → `ka_vighnakara` → `ka_kala_darshana` →
{`ka_jivana_parva`, `ka_bhavishya_lekha`}; `ka_kalasutra` depends on `ka_sangam` only for its
(99.6%-NULL) refinement columns and can run in parallel. Budget from measured p50s, single chart:
1,729 + 28 + 487 + 3 + 2 + 2 ≈ **2,251 s (~38 min)**, not the registry's implied 513 s.

---

*End of L3_W1_ANALYSIS_BATCH_E v1.0. Every quantity stated as a measurement was produced by a
`q.sh` SELECT or a source read on 2026-09-05; quantities I could not establish are marked
"unmeasured" (`c8_eclipse_proximity` root cause; all serve-cost figures; `ka_yojaka`'s
`domain_lord` emission). This document recommends triage; the L3 session makes the call.*
