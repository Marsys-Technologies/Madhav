# Review packet — Kṣetra (ka_kshetra): the continuous temporal field, its elevation brief and ecosystem plan

You are Kimi K3, asked for a **thorough independent review** of two documents and for
**recommendations** on the elevation of `ka_kshetra`, the L3 (Kāla) continuous-hazard field of this
Jyotiṣa instrument. The native (Abhisek Mohanty, the chart owner and ruling authority) will read
your answer before ruling. You are not the authority — you advise. Standard: **acharya-grade.** A
senior Jyotiṣa ācārya reading your answer should find it at or above their own level, and a senior
engineer should find nothing hand-waved. Generic astrology is a failure; so is generic engineering.

## Ground rules
- Do NOT write any file. Print your answer only.
- Read the two documents under review IN FULL before answering:
  - `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KSHETRA_ELEVATION_BRIEF_v1_0.md` (v4.0 — the
    stage-2 brief, contract §1–§8 shape, packeted by DAG stage)
  - `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KSHETRA_ECOSYSTEM_ELEVATION_PLAN_v1_0.md`
    (the six-stage plan that wraps the brief; §2 is the astrological assessment; §5 the enrichment
    candidates; §6a the cross-stream decisions)
- Read the code for depth — the model is small enough to read whole:
  `platform/python-sidecar/services/ka_kshetra/layer1.py` (the hazard formula, lines 22-30 and 60-165),
  `hazard.py` (baseline, promise, covariates — `COVARIATE_KEYS` at ~line 88), `stage2_promise.py`
  (promise graph and conductance, 317-526), `stage3_clocks.py` (clocks, boundaries, σ_T at ~1012),
  `stage1_symbolization.py` (primitives incl. vedha 241, moorti 222, sandhi 299, coverage gaps 346-362),
  `dhara_null.py` (the null model, header 1-45), `contracts.py` (RobustnessVector 178-227,
  ProvenanceEdge 120-132), `stage4_field.py` (pins 186-212; class-prior selection 1155-1168).
- Governing texts you may consult: `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md`
  (§2 L3-Q01–Q13, §3 data contract, §5 P0–P6, §6.2 Kshetra families); `MADHAV_PRODUCT_DEFINITION_v3_0.md`
  (§1.3, §3.10, §5.2, §9); classical corpus at `00_ARCHITECTURE/SOURCE_DATA/classical_texts/`.
- For every recommendation: the option you recommend · why (classical basis with text/chapter where
  you can; engineering basis where relevant) · what it costs · what would falsify it · what you are
  NOT deciding. Mark each claim **[D]** doctrine (name the text), **[P]** practice, **[J]** your
  judgment, **[U]** you could not verify. Never present a number as fact — thresholds and weights
  are proposals for the native to ratify.
- The native's priority order: (1) quality of what the asset delivers, (2) build efficiency,
  (3) the surrounding ecosystem matters as much as the asset.
- Binding constraints you must respect: no invented computed values (B.10); L1 facts are the
  authority, never restated (§N.5); no scalar "confidence"/"salience" field may be invented; a
  reduced cap, fewer replicates, coarser grid or narrower horizon can never pass as an equivalent
  optimisation (Strategy §5); a signal with no detector behind it is null, not green (§N.8); the
  field may never fit itself to outcomes (Circularity Guard — `mi_bhara` at L5 owns calibration);
  rectification and L5 inputs enter only as separately admitted immutable artifacts, never as live
  L4/L5 table reads (Strategy §6.2); populated-chart replacement is held until W7 and nothing you
  recommend can propose a rebuild on the canonical chart before that.

## What Kṣetra is
A survival / point-process model wearing Jyotiṣa operands. For each life-event class *e* (25 on the
canonical chart, discovered from L2 `bodha_pratijna`; 27 in the ontology) it computes a continuous
hazard rate over a 100-year horizon,

    ln λ_e(t) = ln λ⁰_e + ln P̃_e + Σ_s w_s·A_s·r_{s,e}(t) + Σ_j β_j·x_j(t) + Σ_m ln(1 − ρ_m·u_m(t))

— baseline, promise, clock (daśā), modifiers (12 covariates), suppression (vighna) — and stores it as
~343k contiguous log-linear segments per class **with the four terms retained on every segment**.
Downstream: a circular-shift null, windows (peaks), salience, insights, a timeline spec and a
content-hashed snapshot. Fifteen tables; frozen stage DAG `S0+S2 → S3 → S1 → S4 → S5 → S6 → S6.5 →
S8 → snapshot`. It is the only Kāla producer that emits a **shape over time** (the Strategy §3
"Interval / trajectory segment") rather than a list of windows. Sangam (`ka_sangam`) is the window
producer and is the named simpler baseline.

## Verified facts about the current code and data (checked at source; do not re-litigate)
1. **Baseline λ⁰** = `lifetime_count / 36525` from `brahma_class_priors` — an actuarial per-day base
   rate, **not a classical quantity**; constant over life; sourced for **6 of 25** classes. The other
   19 run `shape_only` with a synthetic constant. The `baseline_is_synthetic` tag is computed
   (`hazard.baseline_rate`) and **discarded** at `layer1.py:89` (`_baseline_is_synthetic`); it reaches
   `kala_field_windows` only. 85.7% of the canonical chart's windows are synthetic-baseline.
2. **Promise P̃** = floor + (1−floor)·noisy-OR over the L2 promise graph. **Sign is lost at S2**: a
   denied/opposing L2 relation becomes a *low positive* conductance on a shortest-path graph
   (`stage2_promise.py:351-355,457`, `cost = −log(conductance)`); cancellation becomes "a longer
   path". `kala_field_routes` is QX (reminted surrogate edge ids; migration 1002).
3. **Clock term**: daśā lord stacks MD→AD→PD (PrD never computed by L1 — honest absence), scored by
   `relevance(lord_stack, routes, depth_weights)` — a lord is relevant iff it participates in a stored
   causal route from a promise node to the class; graded and depth-discounted; per-system quality
   `kala_field_clocks.quality`. Lord dignity enters only indirectly via L2 signal strength →
   conductance (unsigned).
4. **Covariates (12)**: `contact_moon_ref`, `contact_lagna_ref`, `dual_reference_agreement`
   (=min of the two), `av_kaksha_gate`, `moorti_svarna/rajata/tamra`, `station_band`, `sandhi_band`,
   `syzygy_band`, `eclipse_contact`, `panchanga_affinity`. Additive in log space; **no
   interactions** (daśā×gochara is not conditional). `av_kaksha_gate` is a declared `not_in_corpus`
   gap; `latta` is `not_in_corpus`. `sandhi_band` is derived from Kṣetra's own S3 boundaries, not
   L1's `sandhi_flag`. Vedha (`build_vedha_primitive`, from L0 `bg_transit_rules`) and moorti
   (`build_moorti_primitive`, from own ingress kinematics) are **re-derived internally**; Kṣetra reads
   **none** of the layer's own `ka_vedha_gochara` (BPHS Ch.29 source-qualified, W0-accepted),
   `ka_moorti_nirnaya`, `ka_kota_chakra`, `ka_sudarshana`, `ka_tithi_pravesha`, `ka_av_transit_gating`.
5. **Suppression**: SM-R-7 Option B — only obstructions a route explicitly names in `suppressed_by`
   can suppress a class; `signed_obstruction_start ∈ [−1,0]` (inhibiting only; no
   protection/cancellation of ariṣṭa). Pūrṇa's G3 found the live evaluator may apply chart-wide
   uniform suppression despite the per-class docstring — an open native ruling.
6. **Null** (`dhara_null.py`): `ln λ_r(t) = C(t) + E((t−δ_r) mod H)`; **circular shift of the transit
   envelope only**, natal structure and daśā ladder held fixed; 1-day grid, H=36,525; no RNG;
   R=1024 = 1 observation + 1023 shifts; `null_p = (1+exceed)/1024`; `coarse_mode` at ~819 MD/AD/PD
   knots. It is a within-chart **phase-alignment** test, not event probability; `null_p` is
   scale-invariant within class (so honest for shape-only classes); absolute `expected_count` is not.
   The stored null layer on the canonical chart is **pre-`87cc8c9baf`** (an accepted HIGH finding:
   the predecessor engine could corrupt maxima/thresholds/p-values).
7. **Robustness**: `confidence_tier` is two-valued by design (`concurrent` iff all five dimensions
   True, else `structural_prior`; calibrated tiers reserved for L5 — Circularity Guard);
   `weakest_link` names the first failed dimension; every detector returns `None` (honest
   not-computed) rather than passing. Provenance reconciles before write
   (`assert_provenance_reconciles`, 1e-9, at window peaks).
8. **σ_T (birth-time uncertainty)**: read live from L4 `phala_rectification` at
   `stage3_clocks.py:1012` — inadmissible under Strategy §6.2 (event-derived posterior into an
   event-free prospective asset) and build-blocking (no grant). `compute_sigma_t_days` already has a
   documented default branch (`default_120s_assumption`). σ_A is already derived from L1
   `chart_facts` ayanāṃśa spread. The same S3 chain has an ayanāṃśa-ambiguous `rows[0]` pick
   (live: five ayanāṃśa copies of Vimśottarī's first MD disagree on `lord_graha`).
9. **Data**: 8.57M `kala_field` rows on the canonical chart, 25 classes, all referencing a
   `field_snapshot_id` with **zero manifest rows** — stage 5 died alphabetically (15 null, 14 windows,
   0 salience/insights/timeline). Not resumable (resume ≥9 rejects pre-DHARA-1.2 checkpoints;
   `dhara_sweep_semantic_version` is in `config_pin`). The other chart has a complete, calibrated,
   published **6-class** run. W0 classes the rows "not accepted useful coverage or a rebuild warrant".
10. **Ephemeris frame** (settled 2026-09-23 across three sessions): `ephemeris_daily` stores
    **true-node** Rāhu/Ketu at **noon-UT** knots, Swiss-exact (stored 73.629058 = Swiss TRUE at
    1984-02-05 12:00 UT to 6 dp), while migration 624:30 asserts `node_mode:"mean"` and L1 natal is
    mean-node. Natal Rāhu at the birth instant: MEAN 49.0289 (L1 serves `RAH_MEAN` 49.0330) →
    Rohiṇī pāda 3; TRUE 50.0451 → pāda 4 (margin 163″). L1 serves no `RAH_TRUE`. Hub ruling pending;
    Kṣetra's proposed disposition under a mean ruling is (b): keep true knots, derive mean at read,
    declare the disagreement on the row.
11. **Consumers**: `mi_bhara` (L5, sealed) binds via `SELECT field_snapshot_id FROM kala_field … LIMIT 1`
    with no ORDER BY (`mi_bhara.py:403`) and never reads `baseline_is_synthetic`; four MCP surfaces
    via `resolveFieldSnapshot` return `FIELD_NOT_YET_BUILT`; **no retrieval-registry capability**
    exists over any `kala_field*` table (thirteen sibling assets have one).
12. **Registry edges** are wrong both ways: `bo_sangati`/`bo_upaya` declared and never read; ~10
    tables read and undeclared (incl. `bodha_msr_signals`, `bodha_cgm_*`, `brahma_event_ontology`,
    `ephemeris_daily`, `bg_transit_rules`, `kala_gochara_authority`).

## The value proposition as currently framed (please attack it)
The brief claims the trajectory segment uniquely serves **L3-Q06** ("how does this chapter differ
from the preceding one?" — matched mechanism identity across intervals, via per-term composition),
strongly serves **Q07** (shared knot grid → exact cross-class simultaneity) and **Q08** via the null
("is no window a real negative?"). Baseline: Sangam's windows (interval, score, mode, witnesses —
no shape, no composition, no null, no totality). **Ablation**: two adjacent MD chapters — if Sangam's
windows already say *what mechanism changed* rather than *which witnesses*, the segment earns
nothing and the asset is parked. Disposition: no populated-chart build before W7; re-scope to the
calibrated 6-class configuration and build fresh at W7; P6 → P2 → P1, P1 gated on the ablation.

## The questions

### K-1 — Value proposition and the ablation
Is Q06 the right *unique* home, or is the honest claim weaker (Q07 only? Q08 only? none)? Is the
adjacent-MD-chapter ablation the right falsifier, and is "Sangam's windows" the right competent
simpler baseline, or is there a stronger one (e.g. Sangam + Taranga's monthly waveform)? What
distinction, in an ācārya's words, would a *shape over time with per-term composition* let a reader
make that a good window list cannot? If none, say so.

### K-2 — The model form, term by term, from an ācārya's chair
For each of the five terms: is the mathematical form a defensible formalisation of the classical
operation it stands in for, a tolerable engineering departure, or a distortion? Specifically:
(a) an **actuarial constant** λ⁰ as the base — classically defensible at all? age-varying?;
(b) **noisy-OR** promise with an adṛṣṭa floor vs. classical promise doctrine (bhāva/kāraka/yoga
concordance) — and the loss of **sign** (no bhaṅga/denial representable);
(c) **graded, depth-discounted, continuous** daśā relevance vs. categorical daśā judgment — and
whether lord *dignity/avasthā at the time* and *bhāva placement relative to the kāraka bhāva* should
enter the clock term directly rather than via L2 strength; PrD absence; sandhi as a ±band derived
from own boundaries rather than inherited from L1;
(d) **additive log-linear** covariates with no daśā×gochara interaction — is "transit Saturn over
the MD lord" the same as "transit Saturn elsewhere" in any tradition?;
(e) **multiplicative thinning** suppression, route-scoped, inhibiting-only — where is ariṣṭa-bhaṅga?
Rank the nine gaps the plan's §2 lists (and any it misses) by classical weight, and say which are
seam repairs vs. model changes needing a cited source.

### K-3 — The covariate set and the varṣa layer
Are the twelve the right set? What is missing that an ācārya would insist on (sade-sati, kakṣā gating
live, lattā, tājaka/varṣaphala, muntha, Kota, Sudarśana, transit over natal/daśā-lord specifically)?
Should the layer's own `ka_vedha_gochara` / `ka_moorti_nirnaya` / `ganita_av_transit_gating` feed the
covariates (the plan proposes yes, with per-`vedha_kind` qualification and one verdict per instant)?
Which covariates are genuinely orthogonal and which are the same origin twice (L3-U02)?

### K-4 — The null model: is "surprise vs a re-phased sky" a Jyotiṣa claim?
The null holds natal structure and daśā ladder fixed and rigidly re-phases the transit stream. State
in classical terms what a low `null_p` does and does not license. Is a **two-factor** null (also
shifting the ladder with transit fixed) the right next step, and does it deliver the "daśā AND
gochara concur" claim? Is `q_threshold` (95th pct of pooled replicate λ) a meaningful exceedance
bar? Is the exhaustive 36,525-shift enumeration the right independent oracle? What would an ācārya
want instead of, or in addition to, a permutation-style null?

### K-5 — Baseline honesty and the 6-vs-25 configuration
Given 6 sourced priors, is the plan right to make the calibrated 6-class run the product and hold
the 25-class run as substrate until Pūrṇa P4 sources priors? Or should shape-only classes be served
with within-class rank only (λ⁰ is a constant multiplier so rank is invariant — untested; "A1")?
Is a demographic life-table λ⁰(t) per class a legitimate structural prior for a Jyotiṣa instrument,
or a category error?

### K-6 — The ecosystem: upstream and downstream guarantees
Review §3 of the plan. What is missing from the upstream/downstream guarantee lists? Is
"L1 birth-time precision as the admitted σ_T artifact" the right replacement for the
`phala_rectification` read, and is a rectification posterior *ever* admissible into an event-free
prospective field? Is node disposition (b) right? Should the field's stored per-term decomposition
be exposed downstream (U11 capability), and to which consumers first?

### K-7 — Technical: identity, publication, efficiency order, serving
P6 → P2 → P1 with P1 gated on the ablation; the equivalence contracts (P1 "same finite-value policy,
float64/rank/ties, full shift set, duration buckets and statistical denominator"); pin-hash
identity with `config_pin`; the L3-U11 `query_field_trajectory` capability shape; the L3-U10 fix
for L5's unordered bind. What is wrong, missing, or over-engineered? Is a full-horizon continuous
field the right *physical representation* at all, or should the segment table be a qualified compact
substrate with exact refinement semantics (Strategy §5's alternative)?

### K-8 — Defects in the two documents themselves
Where do the brief or the plan overclaim, cite wrongly, omit a falsifier, invent a scalar, or
violate one of the binding constraints above? Be specific: section, sentence, what is wrong, what
replaces it. Treat this as adversarial review; the author expects to be wrong somewhere.

### K-9 — The offensive question
What single missing entity, relationship, variant, applicability condition, negative case, precision
level or comparison operator would unlock the most valuable new consumer capability from this asset
— with a named consumer, classical basis, cost, and test? (VA §10.3.)

## Deliverable
A markdown answer with one section per question (K-1 … K-9) in that order, each containing:
**Recommendation** · **Classical basis** (cite text/chapter) · **Engineering basis** · **Cost** ·
**Falsifier** · **Not decided here** · **Confidence** (with [D]/[P]/[J]/[U] tags). Then:
**Overall verdict on the value proposition — astrological and technical, separately** (three
paragraphs each at most); a **cross-question coherence check**; **the three things you would ask
the native before ruling**; and a **ranked top-ten list of elevations** (each: what, why, classical
basis, cost, falsifier) that you would put in front of the native if you were the author.
