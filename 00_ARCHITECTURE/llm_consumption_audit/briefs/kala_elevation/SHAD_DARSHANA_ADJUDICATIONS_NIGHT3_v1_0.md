---
artifact: SHAD_DARSHANA_ADJUDICATIONS_NIGHT3 (ANTARYĀMIN ruling block, Night-3 resumed session)
canonical_id: SHAD_DARSHANA_ADJUDICATIONS_NIGHT3
version: 1.0
status: RULED — full text of ADJUDICATION-2 through ADJUDICATION-9, issued by ANTARYĀMIN
  (Opus/max) on 2026-08-01 in the Night-3 resumed session. The ledger
  (SHAD_DARSHANA_STATE.md) carries the one-line summaries and the N-block; THIS file is the
  durable full-text record (the prior convention of "full text in the session transcript" does
  not survive across sessions — this artifact fixes that).
created: 2026-08-01
author: ANTARYĀMIN (adjudicator agent), transcribed verbatim by the Conductor
governing: SHAD_DARSHANA_NIGHT_RUN_v1_0.md (v1.3) + SHAD_DARSHANA_BRIEF_v2_0.md +
  KALA_SUPREME_ELEVATION_v1_0.md (v1.2) + KALA_W2_FIELD_DESIGN_v1_0.md +
  GOCHARA_SWEEP_2_0_DESIGN_v1_0.md
native_review: PENDING — the native reviews rulings each morning and may overrule; reversible
  rulings preferred throughout (every ruling below carries its own reversibility note).
---

# ANTARYĀMIN — ADJUDICATION BLOCK (Night-3 resumed session, 2026-08-01)

These eight rulings supersede the `ADJUDICATION-2 through -5 — NOT ISSUED` placeholders in the
ledger. **N5 is not re-ruled** (native-ruled directly; recorded verbatim in the N-block). No
ruling below alters a FROZEN contract, an untouchable, or a campaign rail.

---

## ADJUDICATION-2: N_e — the lifetime-count priors source (CRITICAL PATH)

**Question.** §5.1 C-1 requires `N_e` = expected lifetime count of event class `e` over a
100-year horizon, read from `brahma_class_priors` at the reserved coordinate
`fact_kind='lifetime_count_per_100y'`. No such row exists anywhere. Where do the values come
from?

**DB findings (read-only, live prod).**
- `brahma_class_priors` = 164 rows, PK `(prior_version, signal_type_class, fact_kind,
  source_subsystem, signal_tradition)`, `CHECK (class_prior > 0)`. All 164 are
  **signal-salience** priors (varga weights, graha×domain affinities, tradition weights) —
  epistemically a different object from `N_e`. Zero rows at
  `fact_kind='lifetime_count_per_100y'`. Confirmed.
- **Both existing consumers are safe from contamination**: `bo_laksana._load_class_priors` and
  `mi_kula._load_registry_priors` both filter `WHERE prior_version='1.0' AND
  signal_tradition='*' AND fact_kind='*'`. New `lifetime_count_per_100y` rows are invisible to
  them. No regression surface.
- `brahma_event_ontology` = **27 event classes** across 12 domains. Its `base_rate_by_age`
  values sum to ≈1.0 per class across the five bands — empirically confirming they are a
  **distribution over age bands**, not a century count. §5.1 C-1's foreclosure is correct on
  the data, not just on doctrine.
- `ka_kshetra`'s `load_class_lifetime_count` / `require_baseline`
  (`services/ka_kshetra/stage4_field.py:614,684`) skip **per class**, raising
  `ClassSkipped(e, 'no_class_prior_row')`. **A partial seed therefore produces a
  partial-but-real field with zero code change.** This is the operative fact behind the ruling.

**Options considered.** (a) classical-text-derived counts; (b) documented demographic base
rates as cited/versioned L0 `structural_prior` rows; (c) cohort-derived; (d) PARK the field
build.

### RULING

**Option (b), with (a) and (c) affirmatively FORECLOSED on doctrinal grounds — not merely
"unavailable".**

**(a) is structurally wrong, not just absent.** Every classical statement about counts (two
marriages from a dual-sign 7th lord; progeny count from Saptāṃśa; number of journeys from
3rd/9th) is **chart-conditional**. Chart-conditional evidence is exactly what `P_e` (Lane A's
noisy-OR promise prior) already carries. Routing it into `λ⁰_e` as well would (i) double-count
the same evidence inside a multiplicative hazard, and (ii) invert B.1 by seating an
interpretation in the base-rate slot. `λ⁰_e` is by construction **chart-independent**. No
śāstra passage states a chart-independent population frequency; the corpus is not silent by
accident, it is silent because this is not a question the śāstra asks. **A builder may not
seed any `N_e` from a classical rule.**

**(c) is foreclosed by the CIRCULARITY GUARD.** `bg_cohort` (10k synthetic charts) carries no
outcome data — it cannot yield event counts. The only real event record is the LEL, and the
guard is absolute: *the field never reads the LEL*. Fitting `λ⁰_e` from LEL events would put
the LEL inside `λ`, break the CI invariance test, and invalidate the skill score. **Note the
model is self-consistent here**: `SS_e` compares model λ against the circular-shifted null,
and a per-class constant cancels exactly in both `Σ ln λ(t_k)` and `Λ(0,T)` (a circular shift
preserves the integral) — so `λ⁰_e` **does not inflate the skill score**. The time-rescaling
GOF, by contrast, *is* scale-sensitive: it is the honest empirical test of whether the seeded
baseline is right. That is the correct division of labour and it is destroyed the moment `λ⁰`
is fitted from the same LEL the GOF scores against.

**(d) is rejected as a whole-field posture** — it is retained only as the per-class default,
which is what the code already does.

#### The seeding design (binding)

**Source hierarchy, mirroring the brief's own W3K §3 citation-tier precedent:**

- **Tier N-i (the only tier that may produce a seeded value).** A published demographic /
  actuarial / epidemiological statistic with **all six** of: publisher · edition or survey
  round · year · indicator/table identifier · geography+cohort · retrievable URL or DOI.
  Transcribed verbatim into a committed seed module, together with the arithmetic converting
  it to a per-100-year count.
- **Tier N-ii (derived identity only).** A value obtained from an already-seeded Tier-N-i
  value by a **stated arithmetic identity**, never by judgement (e.g. `separation ≤ marriage`;
  a completed-fertility mean read directly as `childbirth`). The identity string is stored.
  A "reasonable proportion of" is **not** an identity and is forbidden.
- **Tier N-iii — NOT SEEDED.** `not_computed`; the class is honestly skipped with
  `no_class_prior_row`. This is a shippable outcome and the default.

**Arithmetic convention (binding, so two lanes cannot disagree):**
- `N_e` = expected count of qualifying events over a **100-year modelled timeline from birth,
  assuming survival** — no mortality discount, because `H` is the chart's 100-year horizon and
  `λ⁰` is flat over it.
- Per-person-year incidence `r` → `N_e = 100 · r`. Lifetime prevalence `p` for an
  at-most-once class → `N_e = p` (never > 1). Repeatable class → `N_e = p · E[count | ≥1]`,
  **both figures cited separately**.
- Round to 3 significant figures. Store the raw source figure AND the conversion string.
- **The sourced statistic's inclusion criteria must match the class's `magnitude_floor` and
  `evidence_requirements`.** `illness_acute` has floor `moderate` — a source counting every
  self-reported ailment is off by an order of magnitude and must be restricted or not used.
  Where the published inclusion criteria are broader and cannot be restricted, **do not seed**.
- `CHECK (class_prior > 0)` is respected by *not seeding*, never by flooring to epsilon.
- **Reference population** is a property of the L0 row, not of the chart. Prefer India, birth
  cohorts ~1955–1985. The same row serves every chart, so a future non-Indian chart inherits a
  **labelled** population mismatch that is served, never hidden (Law 4).

**Anti-circularity guard on class selection.** The choice of *which* classes to seed is made
**by source availability alone** and explicitly **not** by which classes the native's LEL
happens to contain. Selecting classes by LEL content would leak the LEL into the field's
structure — a subtler circularity than reading it, and equally forbidden. The seeding lane
must not query the LEL.

**Class dispositions (all 27).**

| Disposition | Classes |
|---|---|
| **EXCLUDED — not a predictable class.** `birth_anchor` is the coordinate origin, not an event. Do not seed; `ka_kshetra` skips it with reason `not_a_predictable_class`. | `birth_anchor` |
| **TRANCHE 1 — MANDATORY seed target** (published figures near-certain to exist; spans 5 domains; sufficient to run stages 4–8 end-to-end). Candidate source families to verify, not to assume: `childbirth` ← completed fertility / TFR (SRS, NFHS-5); `marriage` ← ever-married proportion + remarriage (Census of India marital-status tables, UN World Marriage Data); `separation` ← divorce/separated prevalence (Census of India 2011 C-2/marital status); `relocation` ← lifetime internal migration (Census of India D-series migration tables, NSS); `surgery` ← surgical volume per 100k per year (Lancet Commission on Global Surgery; WHO); `foreign_settlement` ← emigration / migrant-stock share (UN DESA, MEA). | 6 classes |
| **TRANCHE 2 — seed if and only if Tier N-i sourcing succeeds** | `career_entry`, `career_change`, `career_advancement`, `career_setback`, `business_launch`, `property_acquisition`, `chronic_onset`, `illness_acute`, `bereavement`, `education_milestone`, `exam_outcome`, `major_gain`, `major_loss`, `financial_deception`, `travel_event`, `parental_event`, `romantic_start` |
| **DEFER — no defensible population statistic exists at the class's own definition; do not attempt** | `psychological_arc`, `achievement_recognition`, `spiritual_turn` |

**Gate consequence.** Gate W2 does **not** require 27 classes. It requires a non-empty field
with the science published. **Minimum viable unblock = Tranche 1 seeded and verified.**
Unseeded classes are registered in the ledger by explicit name as an open coverage item —
honest-empty *per class*, never honest-empty for the whole field.

**Hard stop.** If the seeding lane cannot obtain and cite **at least the six Tranche-1
classes** at Tier N-i, it seeds **zero rows** and W2 remains `PARKED-HONEST`. It may not seed
placeholders, illustrative values, or "order-of-magnitude" estimates. Honest-empty beats
fabricated-full.

#### What the L0 lane concretely builds

1. **Additive migration** (next free number per `migration_number_guard.ts`, within the
   campaign's reserved block) — no existing row or consumer changes:
   ```sql
   ALTER TABLE brahma_class_priors
     ADD COLUMN IF NOT EXISTS prior_basis TEXT,
     ADD COLUMN IF NOT EXISTS source_ref  TEXT;
   ALTER TABLE brahma_class_priors
     ADD CONSTRAINT brahma_class_priors_lifetime_basis_ck
     CHECK (fact_kind <> 'lifetime_count_per_100y'
            OR (prior_basis IN ('demographic_structural','derived_identity')
                AND source_ref IS NOT NULL));
   ```
   This makes the DATA-HONESTY RAIL **machine-enforced** rather than free-text. Reversible by
   dropping two nullable columns and one constraint.
2. **Seed module** `platform/python-sidecar/brahmagyan/l0_class_lifetime_counts.py` — a
   literal, reviewable table: `(event_class_id, n_e_per_100y, prior_basis,
   reference_population, publisher, edition_year, indicator_id, source_url,
   inclusion_criteria, conversion_arithmetic, ratified_by)`. Append-only convention, same as
   `l0_class_priors.py`.
3. **Writer** `pipeline/orchestrator/writers/bg_class_lifetime_counts.py` —
   `@register('bg_class_lifetime_counts')`, `WriterBase`, `run(ctx)`, L0 idempotency
   `ON CONFLICT DO UPDATE` (§N.3), runs on `ctx.db_conn`, never commits. Writes at the
   reserved coordinate: `fact_kind='lifetime_count_per_100y'`,
   `signal_type_class=<event_class_id>`, `source_subsystem='*'`, `signal_tradition='*'`.
4. **Versioning.** `prior_version` = **`ne_v01`** (zero-padded). `ka_kshetra` selects
   `ORDER BY prior_version DESC LIMIT 1` — a **string** sort, so unpadded `ne_v10` would sort
   below `ne_v2`. Padding is mandatory. A revision is a new `ne_v02` row set, never an
   in-place edit.
5. **Nirmāṇa (§2.5.1), same PR**: `asset_registry_seed.ts` row —
   `asset_id='bg_class_lifetime_counts'`, `layer='brahmagyan'`, `asset_kind='data'`,
   `scope='global'`, `depends_on=[]`,
   `count_sql="SELECT COUNT(*) FROM brahma_class_priors WHERE
   fact_kind='lifetime_count_per_100y'"`. Catalog-reconciliation CI green in the same PR.
6. **DAG edge**: add `bg_class_lifetime_counts` to `ka_kshetra.depends_on` — exactly the
   `bg_cohort` precedent already in the live registry. Acyclic (L0→L3). The §2.5.2 "L0
   dependency not built" blocked state is correct behaviour; the L0 asset must be built in
   production **before** the first per-chart `ka_kshetra` build.
7. **Verifier acceptance (two-pass, mirroring the item-36 round-2 precedent):** a second
   reader independently re-opens each cited source and re-derives each figure and its
   conversion arithmetic. Self-report is not evidence. Any figure that cannot be independently
   re-derived is **deleted, not downgraded**.

**Where the age structure goes.** `base_rate_by_age` may **never** become `N_e`. Its honest
future home is covariate `x_13` — the design's own §"covariate #13 and beyond" (line 1908)
freezes `x` at twelve for W2 and names W3 as the place to extend. Filed as a W3 candidate;
**no W2 lane may touch it.** Until then, the class's age concentration must be carried by the
promise and clock terms — and if it is not, the GOF will say so. That is a legitimate
falsification, and it is the point.

**Rationale summary.** §5.1 C-1 ("never given a made-up baseline") · NIGHT_RUN §D DATA-HONESTY
RAIL ("cited, versioned L0 row labeled structural_prior; a number without a defensible source
is a build error") · CLAUDE.md B.1 (facts/interpretation separation, which is why (a) fails) ·
B.3 · B.10 · §N.3 · §N.5 · brief §7 CIRCULARITY GUARD (which is why (c) fails) · brief §2.5.

**Reversibility: HIGH.** Every artefact is additive and versioned. Retracting a value =
seeding `ne_v02` without it; the class reverts to honest-skip automatically. Retracting the
whole design = drop two nullable columns, one constraint, one asset row, one DAG edge. No
served value in any existing surface changes. No contract touched.

---

## ADJUDICATION-3: N1 — W2G wave naming

**Question.** Does the GOCHARA-2.0 work carry the doctrine-arc label **D-6**, or the
ṢAḌ-DARŚANA arc label **W2G**?

**Options.** (a) D-6; (b) W2G; (c) dual label.

### RULING — **(b). The operative wave identity is `W2G`. "D-6" is RETIRED as a wave label.**

- **Engine name:** `GOCHARA-2.0` (unchanged; this names the *thing built*).
- **Wave id:** `W2G` in every ledger, gate, PR title, worktree name
  (`.worktrees/shad-darshana-w2g-*`), and branch.
- **`D-6`** survives only as a **historical alias** in `GOCHARA_SWEEP_2_0_DESIGN_v1_0.md`'s
  frontmatter (`historical_alias: D-6 (never opened; folded into ṢAḌ-DARŚANA W2G,
  2026-07-29)`). It appears nowhere else.
- **(c) is rejected outright**: two live labels for one wave is precisely the failure mode the
  standing **ONE CANONICAL DOMAIN VOCABULARY** rail exists to prevent.

**Rationale.** The doctrine-waves arc closed at D-5 (`BRIEF_D5.md` is the last brief; no D-6
brief was ever opened, and the design doc is still `RATIFICATION-READY DRAFT`). The fold-in
already happened in fact: brief §3, §4, §5, §6, §7, the N-block, the item-19 registry row and
the NIGHT_RUN kickoff **all already say W2G**. Ratifying the de-facto state costs nothing;
ratifying D-6 would require editing six governance surfaces to reintroduce a label whose
parent arc is closed. Brief §7 rail.

**Reversibility: TOTAL.** Docs-only; no code, no data, no schema.

---

## ADJUDICATION-4: N2 — multi-chart rollout order after cutover

**Question.** In what order do charts move from the v1 sweep to GOCHARA-2.0?

**DB findings.** Six charts exist: Steve Jobs (1955), Elon Musk (1971), Kiran Shenoy (1971),
**Abhisek Mohanty `482012f1` (1984, canonical)**, Arunima Samantray (1984), **Abhinandan
Mohanty `1c826d5a` (1985, canonical)**. `kala_gochara_windows` (the v1 equivalence ground
truth, and an **untouchable**) exists for exactly **three**: `482012f1` (8,345 rows,
1983→2084), `1c826d5a` (5,680 rows, 1984→2084), `cb73cd3d` Kiran Shenoy (2,667 rows,
**1970**→2027).

### RULING — **rollout ordered by descending equivalence-evidence availability, in three
tiers, with a hard tier gate.**

- **Tier 1 — `482012f1` and `1c826d5a`, together, never separately.** The standing *both
  charts identical coverage* rail forbids advancing one without the other. Both carry a
  full-century v1 corpus, so both yield a complete divergence report. This tier IS Gate W2G's
  own §3 equivalence work — it is the gate, not a rollout step after it.
- **Tier 2 — `cb73cd3d` (Kiran Shenoy).** The **only** third chart with a v1 corpus, and the
  only v1 corpus that starts pre-1984 (1970-12-31). It is therefore the first real exercise of
  both the equivalence machinery on a non-canonical chart *and* of ADJUDICATION-5's pre-1984
  calendar. Its v1 corpus ends 2027 (not a full century), so its divergence report is scoped
  to `[1971, 2027]` and that scope is recorded, not silently treated as complete.
- **Tier 3 — `acdf0d66` (Arunima, 1984), `fdee25b5` (Musk, 1971), `e36ba429` (Jobs, 1955).**
  No v1 corpus. These are built **2.0-native**, and **no equivalence check is possible** —
  each chart's rows carry `equivalence_basis='no_v1_baseline'`. They may never be counted
  toward a divergence-report completeness claim. Jobs/Musk additionally carry no verified
  birth time and no LEL; they are substrate-only and must **not** enter any skill-score or
  GOF scoreboard.

**Hard tier gate.** No chart advances to tier *n+1* until tier *n*'s divergence report has
**zero unclassified rows** (design §3.2). Within Tier 3, order is arbitrary (build cost only).

**Rationale.** Design §3.1–3.2 makes v1 the ground truth, so the rollout order that maximises
information per unit of risk is strictly descending equivalence-evidence. Brief §7 both-charts
rail forces the Tier-1 pairing. Elevation Law 4 forces the `no_v1_baseline` label rather than
a silent gap.

**Reversibility: HIGH.** Per-chart and monotone — a tier can be halted after any chart;
nothing later depends on an earlier tier's *authority* flip, only on its divergence report.

---

## ADJUDICATION-5: N3 — pre-1984 backfill of the global event calendar

**Question.** Does the chart-independent global event calendar (lane E-2) backfill deeper than
1984?

**DB finding — decisive.** `ephemeris_daily` **already covers 1899-12-31 → 2150-12-30,
825,084 rows.** The substrate for a pre-1984 backfill is already present and paid for; the
marginal cost is compute over existing data, with **no new ingestion and no new dependency**.
And the need is not hypothetical: three live charts predate 1984 (1955, 1971, 1971), and one
of them (`cb73cd3d`) already has a v1 corpus reaching back to **1970**.

**Options.** (a) 1984 floor; (b) backfill to the ephemeris floor; (c) lazy on-demand per
chart.

### RULING — **(b), bounded: backfill the global event calendar to `1900-01-01`, the
ephemeris coverage floor.**

- Floor = **1900-01-01**, stated as `calendar_epoch_start`, chosen **because it is the
  ephemeris floor** — not a round number. It is derived from live coverage, so it moves only
  if `ephemeris_daily` moves.
- Forward horizon unchanged at **2084** for chart-anchored work; the global calendar itself
  may run to the ephemeris ceiling where it is free to do so, and its own coverage bounds are
  **served as data** on every response (the standing freshness-attestation pattern), never
  assumed.
- Any query that reaches outside `[calendar_epoch_start, calendar_epoch_end]` returns an
  **honest-empty with `reason='outside_calendar_epoch'`** and the epoch bounds — never a
  silently truncated window.
- **(c) is rejected**: lazy per-chart backfill would make a *chart-independent* asset
  chart-dependent, defeating the entire point of the E-2 global calendar and re-introducing
  per-chart compute the 2.0 design exists to eliminate.
- **W2G bind-time validation V2 is amended**: verify `ephemeris_daily` coverage/cadence for
  **1900–2084** × 9 bodies (not 1984–2084). If any body proves to have a later start than
  1900, `calendar_epoch_start` becomes the **max over bodies** of first-covered date, and that
  value is recorded in the ledger. The calendar never claims coverage a body cannot support.

**Rationale.** Design §7 N3 asks the question "for future research charts" — the research
charts already exist in the DB and already fall outside 1984. Design §6 V2. Brief §7
honest-empty rail.

**Reversibility: HIGH.** Backfill is additive; the epoch is a single stated constant.
Narrowing it later costs a delete of rows outside the new epoch and one constant edit; no
consumer contract changes because the epoch is already served as data.

---

## ADJUDICATION-6: N4 — cutover posture

**Question.** Hard cutover after design §3.5, or a dual-serve shadow period with v1
authoritative for N days?

**Options.** (a) hard cutover; (b) dual-serve, v1 authoritative for N calendar days; (c)
dual-serve gated on evidence rather than time.

### RULING — **(c). Dual-serve shadow, authority gated on EVIDENCE, not on elapsed days; then
a bounded observation window with a one-flip revert.**

**The "N days" framing in design §7 is rejected as a category error** and must not be
implemented: `kala_gochara_windows` is a **batch-computed century table**. It does not change
with wall-clock time, so "N days of agreement" measures nothing — day 30's agreement is
byte-identical to day 1's. Time-based soak is a streaming-system idiom misapplied to a batch
artefact.

**The posture, per chart:**

1. **Shadow phase.** 2.0 writes **generation-stamped rows beside v1** — never over them.
   `kala_gochara_windows` **data is an untouchable**: v1 rows are neither updated nor deleted,
   in this phase or ever. (Precedent for provenance-stamped siblings already exists in prod:
   `kala_gochara_windows__ssv_20260728c`.) v1 remains authoritative; every served row carries
   its `generation`.
2. **Authority flip conditions — ALL FOUR required, none time-based:**
   - the equivalence corpus for that chart has **zero unclassified divergences** (design §3.2,
     classes (a)/(b)/(c) all dispositioned);
   - all **§3.3 specimen-continuity** cases reproduce (windfall plateau overlap; both 2013
     marriage peaks including the double-transit at its exact timestamps);
   - **§3.4 determinism** — byte-identical re-derivation on rerun;
   - **§3.5 post-cutover battery** — the D-4b scoring assertions re-run on 2.0 data are within
     tolerance, **or** each drift is explained by a classified divergence. Per design §5,
     drift is a **finding, never a tuning opportunity** — no β/weight may move to make this
     pass.
3. **Observation window — 7 days after each chart's flip.** Both generations stay queryable
   and the divergence report stays served. This window is **not** an approval gate (the gate
   is condition 2); it exists solely so a consumer-visible regression has a defined, cheap
   revert path.
4. **Revert = flipping one per-chart `authoritative_generation` pointer.** No data motion, no
   rebuild, no deploy. Because v1 rows were never touched, revert is total and instant.
5. **Retirement of the v1 writer** happens only per brief §7 strangler discipline — **zero
   consumers, after a duplicate-copy audit, one at a time** — and **legacy data is never
   destroyed**, in any phase.

**(a) is rejected** because it discards the revert path for zero benefit on a batch artefact.
**(b) is rejected** as measuring nothing.

**Rationale.** Design §3.1–3.5, §5, §7 N4 · brief §7 untouchables (`kala_gochara_windows`
data), strangler discipline, "legacy data never destroyed", "merge-state ≠
verification-state".

**Reversibility: MAXIMAL — this ruling is chosen *because* it is the maximally reversible
posture.** One pointer, per chart.

---

## ADJUDICATION-7: W3K — layer seating for the KP sub-lord engine (item 18)

**Question.** Does the KP sub-lord substrate seat as `bg_*` (L0 global reference) or
`ga_*`/`ka_*` (per-chart)?

**DB findings — the brief's premise is partly false and must be corrected before the wave
designs anything.** "KP exists nowhere" is **not** true of the natal layer. Live in
`chart_facts` **right now**, across **5 ayanāṃśas × 3 charts**:

| `fact_category` | rows | emitted by |
|---|---|---|
| `cusp_kp_lords` (star / sub / sub-sub / **prāṇa** per cusp) | 720 | `ga_nakshatra` |
| `kp_cuspal_significators` | 900 | `ga_nakshatra` |
| `graha_kp_lords` | 600 | `ga_nakshatra` |
| `kp_ruling_planets_natal` | 150 | `ga_nakshatra` |
| `bhava_cusps` (**placidus AND sripati**) | 1,080 | `ga_*` |

`get_kp_cusps.ts` already serves these and **already defaults to
`ayanamsha_id='krishnamurti'`**. An archived `_archive/024_kp_sublords.sql` also exists —
legacy, superseded, and **not** to be revived (duplicate-copy rail).

### RULING — **a three-way split, and one explicit non-build.**

**1. `bg_kp_sublord_division` — L0, `scope='global'`, NEW.**
The 249-fold division itself: nakṣatra → pāda → sub → sub-sub boundary **spans in sidereal
longitude**, by Vimśottarī proportional subdivision. This is pure chart-independent reference
geometry — §N.1's exact definition of `bg_*`.
> **Binding sub-ruling:** the table is stored **in sidereal-longitude space and carries NO
> `ayanamsha_key`.** The division of the *sidereal* circle is ayanāṃśa-invariant; the ayanāṃśa
> enters only at the projection of a tropical longitude into it. Stamping an ayanāṃśa on this
> table would fabricate a dependency that does not exist and would multiply the row count 5×
> for no information.

Deterministic Python (§N.4 deterministic-first). Registry row +
`count_sql='SELECT COUNT(*) FROM bg_kp_sublord_division'`, `depends_on=[]`, same PR.

**2. `ga_*` — NO NEW ASSET. `ga_nakshatra` is the standing L1 authority and W3K EXTENDS it.**
The per-chart natal KP projection already exists and is live on all three charts. Creating a
second natal-KP writer is a **duplicate-copy rail violation** and a §N.5 authority inversion
in waiting. Any natal KP fact W3K finds missing is an **amendment to `ga_nakshatra`**, landing
as an additive emitter with `bg_kp_sublord_division` as its boundary authority — never a
restatement of it (§N.5: reference the L1 fact, inherit its value).
> **Consequence for the W3K gate — recorded as already-discharged evidence:** gate clause
> *"ayanāṃśa/house-system divergence from the project default served explicitly"* is
> **largely satisfied today**. All five ayanāṃśas including `krishnamurti` are stored, and
> `bhava_cusps` stores **both** Placidus and Sripati. The divergence is therefore **servable
> as data with no new computation** — Law 4 satisfied by selection, not by reconciliation.
> K.2 must serve it, not recompute it.

**3. `ka_kp_dhara` — L3, `scope='per_chart'`, NEW.** *(name proposed; Conductor confirms
against the live registry at W3K design per brief §2)*
Everything time-indexed: the KP window stream (sub-lord punctuation of the transiting Moon and
the slow bodies over the horizon), sub-lord period boundaries with their uncertainty in the
`kala_field_clocks` shape Lane B already consumes, and ruling-planets-at-time.
`depends_on=['ga_nakshatra','ga_positions','bg_kp_sublord_division','bg_ephemeris']`.

**4. `bg_dasha_systems` gains one row for the KP clock.**
This is the design's own designated extension path (line 1915: *"adding a `bg_dasha_systems`
row and a `q_s` rule, with no change to §5.1"*). It is how KP **earns** concurrence through
Law-1 applicability instead of being privileged — brief §3 W3K's own requirement that
applicability be *evaluated, not assumed*. `w_s` for KP is fitted like every other clock; it
is never hand-set.

**5. DAG ordering — W2 must not become hostage to W3K.**
`ka_kshetra.depends_on` gains `ka_kp_dhara` **only in the W3K close PR**, as a one-line
registry edit. W2 closes without it. The edge is L3→L3 and acyclic (precedent: `ka_kshetra`
already depends on `ka_dasha_kala`).

**Citation tier for verification.** Per brief §3 W3K: the corpus holds **3 chunks** matching
sub-lord/Krishnamurti terms and **all three are false positives** (Saravali on Moola-daśā
sub-periods; Sarvartha Chintāmaṇi on daśā sub-periods) — **there is no ingested KP text.** So
tier (i) is empty, tier (ii) (the CR-75 design doc's worked tables) is the primary, and tier
(iii) (published KP reader examples transcribed into a **committed fixture file**) is the
fallback. The brief already authorises tier (iii) with the corpus gap filed as an ingestion
work item. **File that gap.**

**Rationale.** CLAUDE.md §N.1 (bg_ = global reference · ga_ = L1 per-chart facts · ka_ = L3
time-indexed) · §N.2 · §N.5 · brief §2.5.1/§2.5.3 · brief §3 W3K existing-substrate audit +
duplicate-copy rail · Elevation Law 4 · design line 1915.

**Reversibility: HIGH.** Three new registry rows and one `bg_dasha_systems` row, each
independently retirable. No existing writer's output changes; the `ga_nakshatra` extension is
additive emitters only. `ka_kshetra` gains its edge last, so W3K can be abandoned entirely
without touching W2.

---

## ADJUDICATION-8: Paddhati-profile default for Agnivāsa where the corpus is silent

**Question.** What is the operative Agnivāsa favourable-residence convention for the native's
chart, given the corpus is silent and the native's lineage practice is on record?

**Corpus findings — the gap is precisely located, not merely present.**
- `agniv%` / `agni vas%`: **0 hits across all 10,651 ingested chunks.** The corpus is
  genuinely silent.
- **But the right text IS ingested and is unusable.** `muhurta_chintamani` (Rāma Daivajña,
  **the** classical muhūrta authority, 274 chunks) is present — and `content_en` is
  **byte-identical to `content_sa`**: raw, OCR-noisy, untranslated Devanāgarī/Hindi ṭīkā. It
  is not retrievable, not citable, and not extractable in its current state. The two `कोट`
  hits are false positives (कोठी, नगरकोट).
- **A corpus-default convention is already shipped and live at L1.**
  `panchang_engine/shastra_tables.py:1188` `AGNI_VASA_TABLE`: tithi → pañca-bhūta (**Pṛthvī**
  1–7 · Jala 8–15 · Vāyu 16–22 · Ākāśa 23–30). `ga_panchanga_writer._emit_agni_vasa` emits
  `panchanga_agni_vasa.{residence, computation_formula, auspicious_for_yagna_flag}` with
  **`auspicious ⟺ residence == 'Prithvi'`**.

### RULING

**The critical distinction, and the crux of this ruling: what is on record is the native's
PRACTICE, not his lineage's CONVENTION CONTENT.** "Yajña when Agnivāsa is favourable per his
lineage" states *that* Agnivāsa favourability gates yajña for him. It does **not** state
*which residences his lineage calls favourable*. Pinning invented convention content and
labelling it "the native's lineage" would be a worse fabrication than an invented number — it
would put words in the native's mouth about his own paddhati. **A builder may not do this.**
I will not either.

**Therefore, ruled in three parts:**

**(1) The PRACTICE is pinned now, as a hard constraint.** For chart `482012f1`,
`kala_paddhati_profile` gains `factor_family='agnivasa'` with **`constraint_role='hard'`** for
yajña-class elections. A candidate whose Agnivāsa is unfavourable is **eliminated**, not
merely down-scored, and appears in the gap report with Agnivāsa named as the eliminating
constraint. This is the part that IS on record, and it is ruled without qualification.

**(2) The CONVENTION CONTENT defaults to the corpus, explicitly labelled as unconfirmed.**
The profile row is seeded:
```
chart_id=482012f1 · factor_family='agnivasa'
convention_id  = 'agnivasa_tithi_element_prithvi'
school_tag     = 'corpus_default'
provenance     = 'L1 ga_panchanga / panchang_engine AGNI_VASA_TABLE (shipped)'
native_confirmed            = FALSE
awaiting_native_confirmation = TRUE
version        = 'paddhati_v01'
```
It is served as the operative rule **and simultaneously as an unconfirmed one**. The
response's coverage census states, verbatim: *"agnivāsa convention = corpus default
(tithi-element, pṛthvī-favourable); the native's lineage convention is not on record."* An
unconfirmed default that says so is honest; an unconfirmed default that presents itself as the
lineage's is not.

**(3) The divergence surface ships with a real second slot — declared, not computed.**
Register `convention_id='agnivasa_muhurta_chintamani_arithmetic'` with
**`convention_status='declared_not_computed'`** and `corpus_gap_ref` pointing at the
Muhūrta-Chintāmaṇi translation work item. The muhūrta literature demonstrably carries more
than one Agnivāsa reckoning — which is exactly why the Elevation doc names Agnivāsa as *the*
canonical example of lineage variation — but I will not transcribe a second rule table from
memory when the corpus cannot corroborate it. **A declared-not-computed convention is served
as an honest gap in the census; it is never served as a computed alternative and never enters
a candidate's grading.**

**W4 Mode-2 fixture, discharged exactly.** `agnivasa = favorable` resolves through the profile
→ convention (A) → `auspicious_for_yagna_flag`. PASS condition 3's divergence clause is
satisfied **honestly-empty**:
```json
"paddhati_divergence": { "state": "none_computed",
  "reason": "one convention computable; agnivasa_muhurta_chintamani_arithmetic is
  declared_not_computed pending muhurta_chintamani translation" }
```
That is a genuine divergence block reporting a genuine gap — it is not a substitution, and it
does not require inventing a second table. **The fixture remains satisfiable**: Guru-vāra
(~104 days / 24 months) × Pṛthvī tithi (7 of 30 ≈ 23 %) × non-viṣṭi × tārā-bala (excluding 3
of 9) ≈ **10–16 candidate day-hours in the horizon**, before the Guru-horā and rāhu-kālam
intra-day cuts. Narrow, non-empty, and correctly labelled **intra-day precision** (every
deciding constraint here is pāñcāṅgika).

**Unblock for the real lineage pin: one line from the native** naming his lineage's
favourable-residence set → a `paddhati_v02` version bump. **No code change** — the profile is
versioned data, and every prior election result stays traceable to the convention set that
produced it.

**Corpus work item filed (high leverage, name it in the ledger):** *translate/extract
`muhurta_chintamani` (274 chunks, ingested but untranslated OCR)*. This is the **single
highest-value corpus action available to W3 item 41** — the Agnivāsa, parihāra, and
combination-yoga rule tables item 41 is chartered to extract all come from this text, and it
is already in the database and merely unreadable. Item 41's `not_in_corpus` register should
record `agnivasa` as **"text ingested, translation missing"** — a materially different and far
cheaper gap than "text absent".

**Rationale.** Elevation §"Lineage variation is data" + `kala_paddhati_profile` schema · brief
§3 W4 Mode-2 fixture PASS condition 3 · B.3 · B.10 · Law 4 · brief §7 honest-empty rail.

**Reversibility: TOTAL.** Versioned config data. `paddhati_v02` supersedes `v01` by insert;
no code, no schema, no rebuild.

---

## ADJUDICATION-9: Kota-Chakra ring-table citation tier (blocks W3 gate-close to `main`)

**Question.** Does a cited **secondary** source carrying an explicit `uncited_extension=true`
flag satisfy the DATA-HONESTY RAIL, or does the rail demand primary-corpus ingestion?

**Corpus finding.** `kota chakra` / `kotachakra` / `kota-chakra`: **0 hits across 10,651
chunks.** The two `कोट` hits in `muhurta_chintamani` are false positives (कोठी "firm",
नगरकोट "city-fort"). PR #999's disclosure is **accurate**: there is no ingested primary
source, and the builder checked correctly.

**Options.** (a) accept on the disclosure flags; (b) accept but require the ring table seeded
as a versioned `bg_*` L0 reference table with citation, not inline in writer code; (c) require
corpus ingestion first, parking item 16; (d) serve behind a disclosure tier.

### RULING — **(b), unambiguously. The rail's own text decides this.**

The DATA-HONESTY RAIL (NIGHT_RUN §D) reads: *"every value enters as a **cited, versioned L0
row** labeled `structural_prior`; a number without a **defensible source** is a build error."*
Three conjuncts. Score PR #999 against them:

| conjunct | PR #999 status |
|---|---|
| **cited** | ✅ `ring_table_citation` on every served row |
| **versioned** | ❌ inline Python dict in `services/ka_kota_chakra/logic.py` — no version, no diffable identity |
| **L0 row** | ❌ inline in writer code |

**The rail says "defensible source" — it does not say "primary corpus."** So **(c) is
wrong**, and would additionally contradict the brief's own policy: brief §3 W3K establishes
the three-tier hierarchy explicitly *for exactly this situation*, and explicitly permits tier
(iii) — *"if only (iii) is available, the item is VERIFIED against the fixture and the corpus
gap is filed as an ingestion work item."* A cited secondary transcription is a defensible
source. Parking item 16 would apply a stricter rule than the campaign's own written one.

**(a) is wrong** because it fails two of the three conjuncts. And the failure is not cosmetic
— it is the exact **B.8 silent-mutation defect**: an inline dict can be edited and CI stays
green, so the served fort-chakra could change generation-to-generation with no drift signal
and no version bump. Seating it as a versioned L0 row makes silent mutation **detectable**.
That is the decisive engineering argument, independent of doctrine.

**(d) is not an alternative** — it is orthogonal and already satisfied.
`uncited_extension=true` + `ring_table_citation` **are** the disclosure tier, they are
correct, and **they stay** exactly as shipped. Disclosure is a serving decision; the rail
governs data residence. (b) subsumes (d).

#### Concrete unblock (small; hours, not a wave)

1. **`bg_kota_chakra_rings`** — L0 table, ~28 rows: `ring_position (1..28 counted from
   janma-nakṣatra) · ring_name (stambha | madhya/durgāntara | prakāra | bāhya) · ring_index ·
   dvāra assignment (if the writer uses one) · citation · table_version ·
   corpus_status='not_in_corpus'`.
2. **`bg_kota_chakra_rings`** writer — `@register`, `WriterBase`, L0 `ON CONFLICT DO UPDATE`
   (§N.3), registry row + `count_sql='SELECT COUNT(*) FROM bg_kota_chakra_rings'`,
   `depends_on=[]`, same PR (§2.5.1).
3. **`ka_kota_chakra` reads the L0 table**; the inline dict is deleted (not commented out —
   duplicate-copy rail). `ka_kota_chakra.depends_on` gains `bg_kota_chakra_rings`.
4. **`ring_table_citation` becomes a reference to the L0 row's `table_version`**, not a
   repeated string literal. **`uncited_extension=true` remains on the attack/defence
   posture/severity synthesis** — that flag is about the *interpretive* extension and is
   unaffected by this ruling.
5. **Ingestion work item filed** for the primary source (Kota-Chakra is a
   muhūrta/saṃhitā-tradition technique; the two live candidates are `muhurta_chintamani` —
   already ingested but untranslated, see ADJUDICATION-8 — and a Nārada-Saṃhitā-class text not
   yet held). Filed, not assumed away.
6. **Item 16 disposition: `VERIFIED-FIXED` with disclosure — NOT parked.** The values do not
   change; only where they live changes.
7. **W3 gate-close PR to `main` unblocks** when 1–5 are done. The Conductor's interim
   disposition (land on `shad-darshana/integration`, block the `main` PR) was **correct and
   is affirmed**; this ruling converts the block into a short, bounded task.

**Rationale.** NIGHT_RUN §D DATA-HONESTY RAIL (verbatim, three conjuncts) · brief §3 W3K
three-tier citation hierarchy · CLAUDE.md B.3 (derivation ledger names the source) · B.10
(transcription is not fabrication — the table was *found*, not *invented*) · B.8 (versioning
discipline; silent mutation must fail `drift_detector.py`) · §N.1 (`bg_*` = global reference)
· §N.3 · brief §2.5.1 · brief §7 duplicate-copy rail.

**Reversibility: HIGH.** Pure data-residence move — **no served value changes**, so no
consumer, test, or fixture is affected. If the native later rules for primary-corpus-only, the
L0 row is retired and `ka_kota_chakra` honest-empties through its existing `require_*` skip
path.

---

### Closing notes for the Conductor

- **Nothing above touches a FROZEN contract, an untouchable, or a rail.** Every new writer is
  a `@register` `WriterBase` subclass on `ctx.db_conn`. `kala_gochara_windows` data,
  `build_substep_progress`, the sealed harness and root `CLAUDECODE_BRIEF.md` are untouched.
  N5 was not re-ruled.
- **Critical-path sequencing:** ADJUDICATION-2 unblocks W2 the moment Tranche 1 is seeded and
  independently verified — and **only** then. ADJUDICATION-3/4/5/6 fill N1–N4, which together
  with the native's N5 completes the N-block; **W2G is startable tonight.** ADJUDICATION-7
  lets `w3k-inventory`'s recommendation be ratified immediately (correcting its premise: KP
  natal substrate **exists** at L1). ADJUDICATION-9 converts the W3 `main`-gate blocker into a
  bounded task. ADJUDICATION-8 unblocks the W4 Mode-2 fixture without inventing doctrine.
- **One cross-cutting corpus finding worth its own ledger line:** `muhurta_chintamani` is
  **ingested but untranslated** (274 chunks, `content_en == content_sa`, raw OCR). It is the
  primary source for Agnivāsa, parihāra, combination-yogas — item 41's entire charter — and
  quite possibly for Kota-Chakra. Translating/extracting it is the highest-leverage single
  corpus action available to this campaign, and it costs no acquisition.
