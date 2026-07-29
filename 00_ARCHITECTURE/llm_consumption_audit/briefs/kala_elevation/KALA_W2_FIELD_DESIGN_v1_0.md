---
artifact: KALA_W2_FIELD_DESIGN (Wave W2 — The Field as Science: build-precise design for the ten-stage point-process pipeline)
canonical_id: KALA_W2_FIELD_DESIGN
version: 1.0
status: DRAFT
created: 2026-07-29
author: W2 design lane (Opus)
campaign: ṢAḌ-DARŚANA v2 · Wave W2 ("the field as science")
authority_order: >
  KALA_SUPREME_ELEVATION_v1_0.md (v1.2, "the Elevation") > KALA_SIX_VIEWS_DESIGN_v2_0.md >
  KALA_SIX_VIEWS_DESIGN_v1_0.md > SHAD_DARSHANA_BRIEF_v2_0.md (execution contract) > THIS DOCUMENT.
  This document is a BUILD SPECIFICATION, not a design authority: where it appears to conflict
  with the Elevation, the Elevation wins and this document is the thing that gets fixed. Where
  the Elevation says WHAT and this says HOW/WITH-WHICH-FORMULA, this document is binding on the
  five W2 builder lanes.
supersedes: nothing
scope: >
  Wave W2 ONLY (brief §3 W2): pipeline stages 0–6.5, 8, 9 + the Living-LEL calibration plane.
  Registry items 11, 12, 15, 20, 21, 22 (consumer side), 23, 24-full, 25, 27, 39, 44 (populate)
  and E-series E1, E2, E5, E7. NOT in scope here: W2G sub-day precision (item 19), W3K KP
  (item 18), W3 new computations, W4 intervention. No wave designed here REQUIRES sub-day
  precision (brief §4) — every transit-edge constraint this design emits carries
  `precision_regime = 'day_grade'` until W2G upgrades it.
---

# KALA W2 — The Field as Science: build-precise design

## §0 — How to read this document (lane assignment + the anti-collision contract)

W2 is built by **five parallel lanes**. Each lane owns a disjoint set of files and a disjoint
set of tables. Lane boundaries are **table shapes + Python function signatures**, both frozen
by this document. A lane never reads another lane's *code*; it reads another lane's *table* (or
calls its one published function). If a lane believes it needs a boundary changed, it stops and
raises — it does not negotiate bilaterally.

| Lane | Stages / items | Owns (files) | Owns (tables) |
|---|---|---|---|
| **A** | Stage 0 kinematics · Stage 1 symbolization · Stage 2 promise graph | `services/ka_kshetra/stage0_kinematics.py`, `stage1_symbolization.py`, `stage2_promise.py` | `kala_field_kinematics`, `kala_field_primitives`, `kala_field_promise_nodes`, `kala_field_promise_edges`, `kala_field_routes` |
| **B** | Stage 3 clocks + Law-1 applicability (item 12) + uncertainty intervals (item 24-full) | `services/ka_kshetra/stage3_clocks.py`, `uncertainty.py` | `kala_field_clocks`, `kala_field_boundaries` |
| **C** | Stage 4 field assembly + provenance (item 11) · Stage 5 null (item 23) + robustness + Adṛṣṭa | `services/ka_kshetra/stage4_field.py`, `hazard.py`, `integrator.py`, `stage5_null.py` | `kala_field`, `kala_field_windows`, `kala_field_provenance`, `kala_field_null`, `kala_field_snapshots` |
| **D** | Stage 6 salience + submodular (item 25) + rarity (item 15) · Stage 6.5 insight synthesis (E2) | `services/ka_kshetra/stage6_salience.py`, `submodular.py`, `cohort_client.py`, `stage65_insights.py` | `kala_field_salience`, `kala_insights` |
| **E** | Stage 8 timeline spec (item 27) · Stage 9 `mi_bhara` harness (items 21, 39, E1-fit) · Living-LEL plane · item 20 | `services/ka_kshetra/stage8_spec.py`; `services/mi_bhara/*` | `kala_timeline_spec`, `kala_field_weights`, `kala_field_weight_versions`, `kala_field_skill`, `kala_field_gof` |

**Shared, owned by NOBODY (frozen by this document, edited only by a cross-lane PR):**
`services/ka_kshetra/contracts.py` — the dataclasses every lane passes across a boundary; and
`platform/migrations/467…476` — the migration range (see §9).

**The orchestration shim** `pipeline/orchestrator/writers/ka_kshetra.py` is written ONCE by
Lane C (it owns stage 4, the pipeline's centre of gravity) and consists of nothing but the
`@register('ka_kshetra')` side-effect import, exactly as `ka_gochara_sweep.py` does today.

---

## §1 — Standing rails this design is built to satisfy (read before writing code)

1. **§N.5 / B.10 — L1 and L3 are the authority.** No table in this design ever *restates* a
   computed value owned by L1 (`chart_facts`, `chart_dashas`, `chart_positions`) or by the
   existing L3 writers (`kala_gochara_windows`, `gochara_resonance_map`). Every field row that
   depends on such a value stores a **reference** — `(source_table, source_pk, source_fact_id)`
   — and inherits the value at read time. If a field-derived value disagrees with the L1/L3
   value it cites, that is a **halt-worthy bug**, not a stored divergence.
2. **Legacy is UNTOUCHED (strangler-fig, brief §7 rails).** `kala_gochara_windows` data,
   `build_substep_progress`, and the sealed harness are untouchable. `ka_gochara_sweep`,
   `ka_sangam`, `ka_yojaka`, `ka_kalasutra`, `ka_taranga` keep running and keep serving through
   W2. `ka_kshetra` is built BESIDE them and reads them read-only.
3. **§N.2 FROZEN orchestrator contract.** `ka_kshetra` is a HEAVY writer:
   `@register('ka_kshetra')` → `WriterBase` subclass with `plan_substeps(ctx)` +
   `run_substep(ctx, step)`; runs on `ctx.db_conn` and **never commits, rolls back, or closes
   it**; never writes `asset_throughput`; gets `chart_id` + `birth_params` from `ctx.config`.
   If a lane thinks it needs a contract change → **STOP and raise with the native.**
4. **§N.3 idempotency.** Per-chart **delete-then-insert** scoped to `(chart_id × natural key)`.
   Deletion happens **exactly once, in `plan_substeps`**, before any substep of a fresh/replanned
   build runs — never per-substep (the `ka_gochara_sweep` D-5 RED-C lesson: substep dispatch
   order is arbitrary, and a per-substep delete silently wipes sibling substeps' committed rows).
5. **§N.7 Earned-Signal.** Every PASS/flag this design emits names the detector that computes it
   and the code path that would make it correctly read false. Flags with no such detector are
   `not_computed`, never green. Two checks in this document exist purely to satisfy this rail:
   the provenance reconciliation assertion (§5.4) and the *vacuity* half of the Circularity
   Guard test (§8.6).
6. **CIRCULARITY GUARD (peer of LAW ZERO).** Stages 0–8 NEVER read the LEL. See §8.6 for the
   exact invariant and its detector.
7. **LAW ZERO / honest-empty.** Every honest gap is served with a reason
   (`not_computed` / `honest_empty` / `not_in_corpus`, matching `kala_envelope.ts`'s
   `CoverageState`). Nothing is fabricated to fill a column.
8. **Weights are versioned artifacts.** A field build **pins** its weights version; silent
   weight mutation is a drift failure (§7.3, §9.4).

---

## §2 — The pipeline in one picture

```
  ephemeris_daily (L0) ─┐
  chart_positions (L1)  ├─► STAGE 0 kinematics ──► kala_field_kinematics
  chart_facts (L1)      ┘        (Lane A)
                                     │
  brahma_* reference (L0) ──► STAGE 1 symbolization ──► kala_field_primitives
                                     │                    (Lane A)
  bo_pratijna / bo_sangati /  ──► STAGE 2 promise graph ──► promise_nodes / promise_edges / routes
  bo_upaya / bo_laksana (L2)         (Lane A)
                                     │
  chart_dashas (L1) ──────────► STAGE 3 clocks + Law-1 ──► kala_field_clocks / kala_field_boundaries
  bg_dasha_systems (L0)              (Lane B)
                                     │
  kala_field_weights (pinned v) ► STAGE 4 field assembly ─► kala_field (segments)
  kala_gochara_windows (L3, RO)      (Lane C)              kala_field_windows
  gochara_resonance_map (L3, RO)                           kala_field_provenance
                                     │
                              STAGE 5 circular-shift null ─► kala_field_null
                                     │  (Lane C)             + robustness + adrishta
                                     │
  bg_cohort (L0, global) ────► STAGE 6 salience + submodular ─► kala_field_salience
                                     │  (Lane D)
                              STAGE 6.5 insight synthesis ──► kala_insights
                                     │  (Lane D)
                              STAGE 8 presentation ────────► kala_timeline_spec
                                     │  (Lane E)
  ══ FIELD HASH BOUNDARY ═══════════════════════════════════════════════════════
  LIFE_EVENT_LOG (LEL) ──────► STAGE 9 mi_bhara fit + skill + GOF
                                        (Lane E)  ──► kala_field_weight_versions
                                                      kala_field_skill / kala_field_gof
```

Stages 0–8 are **pure functions of `(chart, corpus_pin, config_pin, weights_version)`**.
Stage 9 is the only state that grows, and it is the only stage that may see the LEL.

---

## §3 — Lane A · Stages 0–2 (kinematics · symbolization · promise graph)

### 3.1 Stage 0 — kinematics

**Input.** `ephemeris_daily(date, body, ayanamsha_id, tropical_longitude NUMERIC(9,6),
latitude NUMERIC(8,6), speed_dps NUMERIC(10,7), is_retrograde)` — daily, tropical, unique on
`(date, body, ayanamsha_id)`. Sidereal longitude is obtained by subtracting the pinned
ayanāṃśa at read time (this is the existing product convention; do not re-derive it).

**Position model (exact).** For each body `b`, build a **cubic Hermite spline** on the daily
knots `(t_i, λ_i, λ̇_i)` where `t_i` = days since J2000 (float64), `λ_i` = sidereal longitude in
degrees **unwrapped** (see below), `λ̇_i = speed_dps` (the Hermite tangent). On each knot
interval `[t_i, t_{i+1}]` with `h = t_{i+1} − t_i` and `u = (t − t_i)/h`:

```
λ_b(t)  = h00(u)·λ_i + h10(u)·h·λ̇_i + h01(u)·λ_{i+1} + h11(u)·h·λ̇_{i+1}
h00 = 2u³−3u²+1   h10 = u³−2u²+u   h01 = −2u³+3u²   h11 = u³−u²
λ̇_b(t) = [h00'(u)·λ_i + h10'(u)·h·λ̇_i + h01'(u)·λ_{i+1} + h11'(u)·h·λ̇_{i+1}] / h
```

**Unwrapping is mandatory and is the #1 source of silent bugs here.** Before splining, walk the
series and add `+360°` to every subsequent knot whenever `λ_{i+1} − λ_i < −180`, and `−360°`
whenever `λ_{i+1} − λ_i > +180`. Retrograde bodies legitimately decrease; the unwrap rule must
use the ±180 test, never `is_retrograde`. All downstream angles are re-wrapped only at the point
of use, with `wrap180(x) = ((x + 180) mod 360) − 180`.

**Velocity rule.** `λ̇_b(t)` is **the spline derivative**, never `speed_dps` read directly and
never mean motion. This is the "true lunar velocity" requirement (Elevation authority: SIX_VIEWS
§A.5). **Validation V0-1 (build-time assert):** `|λ̇_Moon(t)| ∈ [11.60, 15.50] °/day` for every
evaluated `t`; a violation halts the substep with `kinematics_velocity_out_of_range`.

**Root finding.** Every "when exactly" question in stage 0 is a root of a continuous function of
`t` and is solved with **Brent's method** (`scipy.optimize.brentq`) on a bracketing pair of daily
samples, `xtol = 1e-6 days` (≈ 0.09 s), `maxiter = 100`. Bracketing is by sign change on the
daily grid; if no sign change exists in a day-pair there is no root there (day-grade regime — a
double root inside one day is NOT detected at W2 and is exactly what W2G buys).

**Events computed (each a root):**

| Event | Root of | Notes |
|---|---|---|
| `sign_ingress` | `λ_b(t) mod 30 = 0` | 12-fold |
| `nakshatra_ingress` | `λ_b(t) mod (360/27) = 0` | 27-fold |
| `station` | `λ̇_b(t) = 0` | `direction ∈ {retro_onset, direct_onset}` from the sign of `λ̈` |
| `syzygy` | `wrap180(λ_Moon − λ_Sun) = 0` (new) or `= 180` (full) | |
| `contact_in` / `contact_out` | `\|wrap180(λ_b(t) − λ_p)\| = ω` for natal point `p`, orb `ω` | one pair per contact episode |

**Eclipse geometry at W2 (honest limit).** At each `syzygy` root, compute
`beta = latitude(Moon)` at that instant (from the same Hermite spline over
`ephemeris_daily.latitude`). Emit `eclipse_candidate = |beta| ≤ 1.50°` for new-moon syzygies and
`|beta| ≤ 1.00°` for full-moon syzygies, with `gamma_proxy = beta` (degrees). **Eclipse
magnitude and local visibility are `not_computed` at W2** — they require Besselian elements that
`bg_sky_calendar` (W3, item 3) supplies. Emit the coverage entry
`notInCorpusCoverage('eclipse_magnitude', 'requires bg_sky_calendar Besselian elements — W3')`.
Do **not** approximate magnitude. (B.10.)

**Dwell time and the dwell weight (the formula that replaces the "stations act with full
force" special case).** For a contact episode `k` of body `b` on natal point `p` with orb `ω`:

```
D_{b,p,k}   = t_out − t_in                          (days, from the two Brent roots)
D_nom_b     = 2ω / v̄_b                              (days; v̄_b = the body's MEAN sidereal
                                                     daily motion, a constant from bg_reference)
w_dwell     = D / (D + D_nom)   ∈ (0, 1)
```

`w_dwell = 0.5` for a body crossing at its mean speed; `→ 1` as the body stations inside the orb
(`D → ∞`); `< 0.5` for a fast crossing. Bounded, monotone in `D`, no special case for stations.
`ω` comes from `bg_transit_rules` per `(body, target_class)`; if absent, `ω = 3.0°` and the row
carries `orb_source = 'default_3deg'` (never silently).

**Within-episode envelope (needed by stage 4).** The contact's instantaneous strength is a
**trapezoidal kernel** in `t`, piecewise-linear by construction so stage 4's log-linear segment
representation is faithful:

```
x_contact(t) = w_dwell · clamp01( (ω − |wrap180(λ_b(t) − λ_p)|) / (ω − ω_core) )
ω_core = 0.25·ω          (inside ω_core the kernel saturates at w_dwell)
```

The kernel's **knots** (`t_in`, the two `ω_core` crossings, `t_peak` = argmin |Δ|, `t_out`) are
emitted as breakpoints for stage 4.

**Table `kala_field_kinematics`** (Lane A owns):

```sql
kala_field_kinematics (
  id                BIGSERIAL PRIMARY KEY,
  chart_id          UUID        NOT NULL,
  event_kind        TEXT        NOT NULL,   -- sign_ingress|nakshatra_ingress|station|syzygy|
                                            -- contact_in|contact_out|contact_peak|contact_core_in|contact_core_out
  body              TEXT        NOT NULL,
  target_kind       TEXT,                   -- natal_graha|natal_lagna|natal_special_point|NULL
  target_ref        TEXT,                   -- e.g. 'Mo' | 'Lagna' | 'AL'  (NULL for non-contact events)
  t_days            DOUBLE PRECISION NOT NULL,  -- days since J2000, the Brent root
  event_ts          TIMESTAMPTZ NOT NULL,       -- t_days rendered UTC (derived; convenience only)
  longitude_deg     NUMERIC(9,6),
  velocity_dps      NUMERIC(10,7),
  latitude_deg      NUMERIC(8,6),
  episode_id        TEXT,                   -- groups the 5 knots of one contact episode
  dwell_days        DOUBLE PRECISION,       -- episode-level; repeated on each knot of the episode
  dwell_weight      DOUBLE PRECISION,       -- w_dwell
  orb_deg           NUMERIC(6,3),
  orb_source        TEXT,
  eclipse_candidate BOOLEAN     NOT NULL DEFAULT FALSE,
  gamma_proxy       NUMERIC(8,6),
  precision_regime  TEXT        NOT NULL DEFAULT 'day_grade'
                      CHECK (precision_regime IN ('day_grade','sub_day')),
  ayanamsha_id      TEXT        NOT NULL,
  source_table      TEXT        NOT NULL DEFAULT 'ephemeris_daily',
  computed_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX uq_kala_field_kinematics ON kala_field_kinematics
  (chart_id, event_kind, body, COALESCE(target_ref,''), t_days);
CREATE INDEX idx_kfk_chart_t ON kala_field_kinematics (chart_id, t_days);
```

`precision_regime` is `'day_grade'` for every row W2 writes. W2G flips it. Nothing downstream
may branch on `'sub_day'` at W2 other than to pass it through.

### 3.2 Stage 1 — symbolization

Turns kinematics into classical primitives. **Every primitive row is an interval** `[t_start,
t_end]` with a piecewise-linear strength envelope (knots stored as a JSONB array), so stage 4
can consume it uniformly.

Primitive types (`primitive_kind`), each with its one-line rule:

| `primitive_kind` | Rule | Source of the rule |
|---|---|---|
| `contact_moon_ref` | transit contact measured from natal Moon (gochara dual-reference, leg 1) | SIX_VIEWS §E |
| `contact_lagna_ref` | same contact measured from natal Lagna (leg 2) | SIX_VIEWS §E |
| `moorti_at_ingress` | the moorti class (svarṇa/rajata/tāmra/loha) of a `sign_ingress`, per `bg_transit_rules` | v1 §7.4 |
| `vedha` | obstruction of a transit house by an occupied vedha house, per the classical vedha table | v1 §7.5 |
| `latta` | latta kick per the classical table | v1 §7.5 |
| `av_kaksha_gate` | Aṣṭakavarga bindu count + kakṣyā-lord state for the transiting body's position | v1 §7.x |
| `panchanga_limb` | tithi/vara/nakṣatra/yoga/karaṇa state (read from `ga_panchanga`, referenced not recomputed) | §N.5 |
| `sandhi_band` | the ±band around a daśā boundary (from stage 3's boundary + its interval) | Lane B feeds this |
| `station_band` | the ±`w_dwell`-scaled band around a `station` root | stage 0 |
| `syzygy_band` | the ±1.5 day band around a syzygy; `eclipse_candidate` carried through | stage 0 |

**Hard rule (§N.5).** `panchanga_limb` and `av_kaksha_gate` rows do **not** recompute the
pañcāṅga or the Aṣṭakavarga. They reference the L1/L3 row that already holds it
(`source_table`, `source_pk`, `source_fact_id`) and inherit its value. A build-time assertion
compares the inherited value against the referenced row and halts on mismatch
(`l1_authority_divergence`).

```sql
kala_field_primitives (
  id             BIGSERIAL PRIMARY KEY,
  chart_id       UUID NOT NULL,
  primitive_kind TEXT NOT NULL,
  subject        TEXT NOT NULL,          -- transiting body / limb name
  object_ref     TEXT,                   -- natal target / house / NULL
  t_start        DOUBLE PRECISION NOT NULL,
  t_end          DOUBLE PRECISION NOT NULL,
  envelope       JSONB NOT NULL,         -- [{"t": <days>, "v": <0..1>}, ...] ≥2 knots, t ascending,
                                         -- piecewise-LINEAR between knots. v ∈ [0,1].
  polarity       TEXT NOT NULL CHECK (polarity IN ('supportive','obstructive','neutral')),
  class_label    TEXT,                   -- e.g. 'svarna' for moorti
  source_kind    TEXT NOT NULL CHECK (source_kind IN ('l0_reference','l1_fact','l2_signal','l3_row','derived')),
  source_table   TEXT, source_pk TEXT, source_fact_id TEXT,
  kinematics_ids BIGINT[] NOT NULL DEFAULT '{}',   -- the stage-0 rows this primitive stands on
  computed_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX uq_kala_field_primitives ON kala_field_primitives
  (chart_id, primitive_kind, subject, COALESCE(object_ref,''), t_start);
```

**Envelope contract (frozen; stage 4 depends on it).** `envelope` is a JSON array of ≥2 objects
`{"t": float, "v": float}`, `t` strictly ascending, `v ∈ [0,1]`, first and last `v` = 0 unless
the primitive is a step function (in which case emit two coincident knots to make the step
explicit). The value between knots is **linear**. Outside `[t_start, t_end]` the value is 0.

### 3.3 Stage 2 — the promise graph and alternate routings

The promise graph is a **directed weighted graph per chart**, digested from L2 Bodha. Nodes are
chart entities; edges are delivery relations; a *route* is a path from a significator node to an
event-class sink.

**Node kinds:** `graha`, `bhava`, `bhava_lord`, `karaka`, `yoga`, `arudha`, `event_class` (sink).
**Edge kinds:** `dispositor`, `lordship`, `occupation`, `aspect`, `argala`, `yoga_membership`,
`karaka_signification`, `class_signification` (the only edge kind pointing at an `event_class`).

**Edge conductance `c ∈ (0, 1]`** is *inherited*, never invented: it is the stored strength of
the L2 signal that asserts the relation, min-max normalized into `(0,1]` by the L2 signal's own
declared scale, and the row stores the `source_fact_id` it inherited from. An edge whose L2
signal carries no graded strength gets `c = c_default = 0.60` and
`conductance_source = 'ungraded_default'` (served, never hidden).

**Alternate routings — the exact algorithm.** For each `event_class` sink `e`:

1. Build the digraph `G_e` restricted to nodes reachable to `e` within `L_max = 4` hops.
2. Assign edge cost `cost(u,v) = −ln c(u,v) ≥ 0`.
3. Run **Yen's K-shortest-loopless-paths** algorithm with `K = 5`, source = each
   `significator_seed` node (the grahas/bhāvas the L2 class-signification names as primary),
   sink = `e`. Deterministic tie-break: on equal cost, order by the concatenated node-id string
   ascending.
4. Each returned path `r` becomes a **route row** with
   `route_gain p_r = Π_edges c = exp(−cost(r)) ∈ (0,1]`, `route_rank` = its Yen rank,
   `is_primary = (route_rank == 1)`.
5. Routes with `p_r < 0.02` are dropped (`route_floor`), recorded as a count on the sink.

**Promise prior — noisy-OR over routes** (this is what makes an alternate routing genuinely
*add* delivery capacity while saturating rather than exceeding 1):

```
P_e = 1 − Π_{r ∈ routes(e)}  (1 − p_r)        ∈ [0, 1)
```

`P_e = 0` when a class has no route at all — which is precisely the "high natal promise absent"
state that Law 3's graded gate (SIX_VIEWS §C.1) serves rather than suppresses, and that stage 6.5's
`absence_of_expected` insight looks for. **`P_e = 0` never zeroes λ** — see §5.1's `P_floor`.

```sql
kala_field_promise_nodes (
  id BIGSERIAL PRIMARY KEY, chart_id UUID NOT NULL,
  node_id TEXT NOT NULL,              -- stable, e.g. 'graha:Ma' | 'bhava:10' | 'event_class:career_change'
  node_kind TEXT NOT NULL,
  label TEXT NOT NULL,
  source_kind TEXT NOT NULL, source_table TEXT, source_pk TEXT, source_fact_id TEXT,
  UNIQUE (chart_id, node_id)
);
kala_field_promise_edges (
  id BIGSERIAL PRIMARY KEY, chart_id UUID NOT NULL,
  from_node TEXT NOT NULL, to_node TEXT NOT NULL, edge_kind TEXT NOT NULL,
  conductance DOUBLE PRECISION NOT NULL CHECK (conductance > 0 AND conductance <= 1),
  conductance_source TEXT NOT NULL,   -- 'l2_inherited' | 'ungraded_default'
  source_fact_id TEXT,
  UNIQUE (chart_id, from_node, to_node, edge_kind)
);
kala_field_routes (
  id BIGSERIAL PRIMARY KEY, chart_id UUID NOT NULL,
  event_class TEXT NOT NULL,
  route_rank INT NOT NULL,
  path_node_ids TEXT[] NOT NULL,      -- ordered, source → … → 'event_class:<e>'
  path_edge_ids BIGINT[] NOT NULL,    -- FK-shaped refs into kala_field_promise_edges
  route_gain DOUBLE PRECISION NOT NULL,
  is_primary BOOLEAN NOT NULL,
  suppressed_by TEXT[] NOT NULL DEFAULT '{}',   -- vighna keys obstructing this route (stage 1 rows)
  UNIQUE (chart_id, event_class, route_rank)
);
```

**Published function (Lane A → Lanes C/D):**
```python
# services/ka_kshetra/stage2_promise.py
def promise_prior(chart_id: UUID, event_class: str, conn) -> PromisePrior
# PromisePrior = dataclass(p: float, routes: list[Route], n_routes: int,
#                          dropped_below_floor: int, fact_ids: list[str])
```

---

## §4 — Lane B · Stage 3 (clocks, Law-1 applicability, uncertainty intervals)

### 4.1 Law-1 applicability evaluation, per daśā system (item 12)

Applicability is **not** a boolean. It is a `(state, quality)` pair plus a competence class.

**Inputs:** `bg_dasha_systems` (L0 reference: `system_id`, `entry_condition`,
`competence_class`, `seniority_rank`), `chart_dashas` (L1: the computed period ladder per
system), `chart_facts` (L1: Moon longitude, nakṣatra, pada, ayanāṃśa spread).

**Algorithm (run once per chart, per system `s`):**

```
1. jurisdiction:  evaluate bg_dasha_systems.entry_condition against the chart's L1 facts.
                  → state ∈ {applicable, excluded_by_condition}
                  On excluded, store the human-readable reason verbatim. STOP.
2. presence:      does chart_dashas hold ≥1 period row for system s for this chart?
                  → if not: state = 'not_computed', reason = 'no chart_dashas rows for system';
                    quality q_s = NULL. STOP. (Never treat absent as excluded.)
3. competence:    competence_class ∈ {fruition, arena, flavour, health, annual, life_stage}.
                  life_stage is DECLARED NON-PREDICTIVE: its hazard factor is identically 1
                  (see §5.1 rule C-4) — it is served as context, never as a λ term.
4. quality q_s ∈ [0,1]: the system's own determination-robustness, computed per system:
      vimshottari : q = clamp01( d_nak / 0.50° )      d_nak = Moon's angular distance to the
                                                      nearest nakṣatra boundary
      yogini      : q = clamp01( d_nak / 0.50° )      (same Moon-nakṣatra determination)
      kalachakra  : q = clamp01( d_pada / 0.25° )     d_pada = distance to nearest pāda boundary
      chara       : q = clamp01( d_sign / 1.00° )     d_sign = min over the chara-karaka set of
                                                      each graha's distance to a sign boundary
      mudda       : q = 1.0 if the evaluated t lies inside a computed varṣa year, else 0.0
      naisargika  : q = 1.0                            (deterministic, age-based)
      conditional : q = 1.0 if the entry condition holds with margin ≥ its own stated tolerance,
                    else clamp01(margin / tolerance)
   Any system not in this table is `not_computed` with reason 'no quality rule defined' —
   a builder MUST NOT invent one.
5. A_s = q_s. Store. A_s is NOT the fitted weight; the fitted weight w_s (§5.1) multiplies
   in the exponent independently, so calibration can down-weight a system that is
   *determinable but unhelpful*, separately from one that is *undeterminable*.
```

```sql
kala_field_clocks (
  id BIGSERIAL PRIMARY KEY, chart_id UUID NOT NULL,
  system_id TEXT NOT NULL,
  applicability_state TEXT NOT NULL
    CHECK (applicability_state IN ('applicable','excluded_by_condition','not_computed')),
  exclusion_reason TEXT,
  competence_class TEXT NOT NULL,
  seniority_rank INT NOT NULL,
  quality DOUBLE PRECISION,           -- A_s ∈ [0,1]; NULL iff state != 'applicable'
  quality_basis TEXT,                 -- e.g. 'moon_nakshatra_margin=1.83deg'
  is_predictive BOOLEAN NOT NULL,     -- FALSE for competence_class='life_stage'
  source_table TEXT NOT NULL DEFAULT 'chart_dashas',
  UNIQUE (chart_id, system_id)
);
```

### 4.2 The uncertainty budget and interval propagation (item 24-full)

**The two sources.**
- Birth-time uncertainty `σ_T` (days). Read from the rectification posterior if present
  (`phala_rectification`); if absent, `σ_T = 120 s = 1.3889e-3 days` and the row carries
  `sigma_t_source = 'default_120s_assumption'`. Never silently defaulted.
- Ayanāṃśa uncertainty `σ_A` (degrees). Compute the **range** across the five pinned
  ayanāṃśas at the birth epoch, `R_A = max − min`; treat as uniform:
  `σ_A = R_A / sqrt(12)`.

**Propagation into the Vimśottarī ladder (the derivation a builder must implement, not guess).**

Let `L_nak = 360/27 = 13.3333…°`, `v_Moon` = the *true* lunar velocity at birth (°/day, from the
stage-0 spline), `f` = the Moon's fractional traversal of its birth nakṣatra, `T_MD^birth` = the
full Vimśottarī mahādaśā length of the birth-nakṣatra lord (days; e.g. Jupiter 16 y).

```
σ_λ  = sqrt( (v_Moon · σ_T)² + σ_A² )                    (degrees)
σ_f  = σ_λ / L_nak                                        (dimensionless)
```

Every Vimśottarī boundary at every level lies on the **same rigid grid** anchored by the birth
balance: the whole ladder translates by `δt = −T_MD^birth · δf`. Sub-periods are exact rational
fractions of their parent, so they inherit the same translation with no extra term. Adding the
direct birth-instant term (all boundaries are absolute times measured from birth):

```
σ_t = sqrt( (T_MD^birth · σ_f)²  +  σ_T² )                (days) — IDENTICAL AT EVERY LEVEL
```

`dominant_uncertainty_source = 'birth_time'` iff
`(T_MD^birth·(v_Moon·σ_T/L_nak))² + σ_T² > (T_MD^birth·(σ_A/L_nak))²`, else `'ayanamsha'`.

**The precision-support rule (this is the rule that makes Sūkṣma-depth serving defensible).**
For a boundary bounding a period of length `P` days, with `z = 1.96`:

```
interval        = [ t_b − z·σ_t , t_b + z·σ_t ]
width           = 2·z·σ_t
serve_as_instant   iff  width ≤ 0.10 · P
serve_as_interval  iff  0.10·P < width ≤ 1.00 · P
precision_unsupported  iff  width > P
```

A level whose boundaries are `precision_unsupported` **contributes no hazard factor at that
level** (stage 4 rule C-5) and is served with
`honestEmptyCoverage('<system>_<level>', 'boundary uncertainty exceeds period length')`.
This is the operational form of "no claim is ever served at a precision the input uncertainty
cannot support."

Non-Vimśottarī systems: apply the same machinery with `T_MD^birth` replaced by that system's own
birth-balance scale factor; where a system's balance does not depend on a fractional arc
(e.g. naisargika, mudda), `σ_t = σ_T` alone.

```sql
kala_field_boundaries (
  id BIGSERIAL PRIMARY KEY, chart_id UUID NOT NULL,
  system_id TEXT NOT NULL,
  level TEXT NOT NULL,               -- MD|AD|PD|SD|PrD  (the product's existing level vocabulary)
  lord TEXT NOT NULL,                -- the lord of the period STARTING at this boundary
  parent_lords TEXT[] NOT NULL,      -- the enclosing lord stack, outermost first
  t_boundary DOUBLE PRECISION NOT NULL,
  period_days DOUBLE PRECISION NOT NULL,
  sigma_t_days DOUBLE PRECISION NOT NULL,
  interval_lo DOUBLE PRECISION NOT NULL,
  interval_hi DOUBLE PRECISION NOT NULL,
  precision_state TEXT NOT NULL
    CHECK (precision_state IN ('instant','interval','precision_unsupported')),
  dominant_uncertainty_source TEXT NOT NULL CHECK (dominant_uncertainty_source IN ('birth_time','ayanamsha')),
  sigma_t_source TEXT NOT NULL,
  source_table TEXT NOT NULL DEFAULT 'chart_dashas',
  source_pk TEXT NOT NULL,           -- the chart_dashas row this boundary INHERITS (never restates)
  UNIQUE (chart_id, system_id, level, t_boundary)
);
```

**§N.5 assertion (build-time, halting):** `t_boundary` must equal the referenced
`chart_dashas` row's start timestamp to within 1e-6 days. Lane B computes *uncertainty about*
the boundary; it does **not** recompute the boundary.

**Published functions (Lane B → Lane C):**
```python
def applicable_systems(chart_id, conn) -> list[ClockApplicability]
def clock_activation(chart_id, system_id, event_class, t: float, conn) -> float
    # returns a_{s,e}(t) > 0 — see §5.1 rule C-2 for its definition
def boundary_breakpoints(chart_id, conn) -> list[float]
    # every t_boundary whose precision_state != 'precision_unsupported', ascending
```

---

## §5 — Lane C · Stages 4–5 (field assembly, provenance, null calibration)

### 5.1 THE HAZARD FORMULA (E1 · the wave's centre)

`λ_e(t)` is the **hazard rate of event class `e` at time `t` for this chart**, in units of
**events per day**, strictly positive everywhere.

> **λ_e(t)  =  λ⁰_e · P̃_e · C_e(t) · M_e(t) · S_e(t)**

with the five factors defined exactly as follows.

**C-1 — Baseline `λ⁰_e`.** The class's classical lifetime expectation, converted to a rate.
From `bg_class_priors`: `N_e` = expected lifetime count of class `e` over a 100-year horizon.
`λ⁰_e = N_e / 36525` (events/day). A class with no prior row is `not_computed` and is **skipped
entirely** (no field rows written for it) — never given a made-up baseline.

**C-2 — Promise `P̃_e`, and the Law-3 graded gate.**
```
P̃_e = P_floor + (1 − P_floor) · P_e ,      P_floor = 0.05   (structural constant, v0-versioned)
```
`P_e` is Lane A's noisy-OR prior. `P_floor` is the **Adṛṣṭa channel made structural** (SIX_VIEWS
§C.1): a class with zero natal promise still receives 5 % of baseline hazard, so windows over
absent promise are **served, labelled** (`promise_state = 'absent'`), never suppressed — and λ
can never be identically zero, which the hazard interpretation requires.

**C-3 — Clocks `C_e(t)`: the multiplicative concurrence (Law 2 = proportional hazards).**
```
C_e(t)  =  Π_{s ∈ S_pred(e)}  a_{s,e}(t) ^ ( w_s^{(v)} )
```
- `S_pred(e)` = applicable systems with `is_predictive = TRUE` **and** whose deepest
  precision-supported level is what supplies `a`.
- `a_{s,e}(t) = exp( A_s · r_{s,e}(t) )`, where `A_s ∈ [0,1]` is Lane B's applicability quality
  and `r_{s,e}(t) ∈ [−1, +1]` is the **signed relevance of the running lord stack of system `s`
  at time `t` to event class `e`**, computed as the promise-graph reachability of the running
  lords to the `event_class:e` sink:
  ```
  r_{s,e}(t) = tanh( Σ_{ℓ ∈ lord_stack(s,t)}  d_ℓ · sign_ℓ · g_ℓ )
      d_ℓ    = level depth weight: MD 1.0, AD 0.7, PD 0.5, SD 0.3, PrD 0.15   (v0, fitted later)
      g_ℓ    = max over routes r containing node 'graha:<ℓ>' of route_gain(r), else 0
      sign_ℓ = +1 if the lord's role in that route is supportive, −1 if the route row lists it
               in suppressed_by                                       (from kala_field_routes)
  ```
- `w_s^{(v)} ∈ [0,1]` is the **fitted weight for system `s` under weights version `v`**.
  `w_s = 0` collapses the factor to exactly 1 — a calibration run can switch a clock off
  smoothly without changing the model's structure. `a > 0` always, so `C_e > 0` always.
- **Rule C-4:** `competence_class = 'life_stage'` (naisargika) has `w_s ≡ 0` **by construction,
  not by fitting** — it is a context band, never a predictor. The fitter must not be given this
  parameter at all.
- **Rule C-5:** a level whose `precision_state = 'precision_unsupported'` does not appear in
  `lord_stack(s,t)`. Its `d_ℓ` term is simply absent.

**C-5 — Modifiers `M_e(t)`: the log-linear covariate term.**
```
M_e(t) = exp( Σ_{j ∈ J}  β_j^{(v)} · x_{j,e}(t) )
```
The covariate vector `x` is **frozen at W2** as the following twelve entries, each a
piecewise-linear function of `t` built from stage-1 envelopes (so `M` is faithful to the
segment representation), each in `[0,1]` unless noted:

| `j` | covariate `x_j(t)` | built from |
|---|---|---|
| 1 | `contact_moon_ref` — max envelope over active Moon-referenced contacts relevant to `e` | stage 1 |
| 2 | `contact_lagna_ref` — same, Lagna-referenced | stage 1 |
| 3 | `dual_reference_agreement` = `min(x_1, x_2)` | derived |
| 4 | `av_kaksha_gate` — normalized bindu/kakṣyā score of the transiting body's position | stage 1 |
| 5 | `moorti_svarna` (0/1 step) | stage 1 |
| 6 | `moorti_rajata` (0/1 step) | stage 1 |
| 7 | `moorti_tamra` (0/1 step) | stage 1 (`loha` is the reference level — no dummy) |
| 8 | `station_band` | stage 0/1 |
| 9 | `sandhi_band` | stage 1 (from Lane B boundaries) |
| 10 | `syzygy_band` | stage 1 |
| 11 | `eclipse_contact` — `syzygy_band` × `eclipse_candidate` | stage 0/1 |
| 12 | `panchanga_affinity` — the class's pañcāṅga-limb affinity score | stage 1 |

`β_j^{(v)} ∈ [−2, +2]`, fitted, shrunk to the classical prior `β⁰_j` (§7). **Adding a
thirteenth covariate is a weights-version-breaking change** (§7.3) and requires a new `x_schema_version`.

**C-6 — Suppression `S_e(t)`: MULTIPLICATIVE THINNING, never subtraction** (Elevation §3
Stage-4 amendment, binding).
```
S_e(t) = Π_{m ∈ vighna(e)} ( 1 − ρ_m^{(v)} · u_m(t) ) ,   ρ_m ∈ [0, 0.95],  u_m(t) ∈ [0,1]
```
`u_m(t)` is the obstructor's own piecewise-linear envelope (stage-1 rows with
`polarity='obstructive'` that the class's routes list in `suppressed_by`). Because
`ρ_max = 0.95`, `S_e(t) ≥ 0.05^{|vighna(e)|} > 0` — **λ stays strictly positive by
construction**, which is the whole point of the amendment.

The signed negative users see is a **serving-layer rendering**, computed and stored alongside
but never fed back into the math:
```
signed_obstruction(t) = −( 1 − S_e(t) )   ∈ (−1, 0]
```

### 5.2 The segment representation and EXACT analytic integration

**Breakpoint set.** `B_e` = the sorted union, over the chart's horizon `[0, H]`
(`H = 36525` days from birth, matching the existing sweep horizon), of:
every `kala_field_kinematics.t_days`; every envelope knot `t` of every stage-1 primitive
relevant to `e`; every `kala_field_boundaries.t_boundary` with `precision_state != 'precision_unsupported'`;
`0` and `H`.

**On each segment `[t_i, t_{i+1}]` the field is stored log-linearly:**
```
ln λ_e(t) = α_i + γ_i · (t − t_i)
α_i = ln λ_e(t_i⁺)
γ_i = [ ln λ_e(t_{i+1}⁻) − ln λ_e(t_i⁺) ] / (t_{i+1} − t_i)
```
This is a **definition of the stored field**, not an approximation claim: `kala_field` holds
`(α_i, γ_i)` and every downstream consumer — serving, integration, null, fitting — reads *that*.

**Adaptive refinement (bounds the gap between the stored field and the true product form).**
After computing `(α_i, γ_i)` for a segment, evaluate the true `ln λ_e` at the segment midpoint
`t_m`. If
```
| ln λ_e(t_m)  −  (α_i + γ_i·(t_m − t_i)) |  >  τ ,   τ = 0.02 nats
```
split the segment at `t_m` and recurse, to a **maximum depth of 6** (≤ 64 sub-segments per
original segment). A segment that still exceeds `τ` at depth 6 is stored with
`refinement_exhausted = TRUE` and its residual recorded — visible, never silent.

**The integral (exact for the stored representation).** For any `[a, b]`:
```
Λ_e(a,b) = Σ over segments i with [t_i, t_{i+1}] ∩ [a,b] = [u,v] ≠ ∅ of:

      if |γ_i| > ε :   ( exp(α_i + γ_i·(v − t_i))  −  exp(α_i + γ_i·(u − t_i)) ) / γ_i
      else         :   exp(α_i) · (v − u)

   ε = 1e-12  (per day)
```
This is the "analytic integration between events" the brief demands. **Numerical rule
(mandatory):** compute the difference in the log domain when `|γ_i·(v−u)| < 1e-4` using the
stable form `exp(α_i + γ_i(u−t_i)) · (v−u) · expm1(γ_i(v−u)) / (γ_i(v−u))`, i.e. via `expm1`,
to avoid catastrophic cancellation. A unit test asserts agreement with a 10⁴-point Simpson
quadrature to 1e-9 relative on a fixture segment set.

**Windows.** A window for class `e` is a **maximal interval where `λ_e(t) ≥ q_e`**, with the
threshold `q_e` supplied by stage 5 (§5.5) — windows are therefore null-calibrated by
construction. Window endpoints are roots of `α_i + γ_i(t−t_i) = ln q_e`, solved **in closed
form** per segment (log-linear ⇒ linear in the exponent), never numerically.

Because `ln λ` is monotone on each segment, **the peak of a window is always a breakpoint**:
`t_peak = argmax over the window's breakpoints of λ_e`. No interior optimizer is needed, and
this must not be "improved" into one — the closed-form property is what makes the field
hash-replayable.

`expected_count = Λ_e(window_start, window_end)` — this is what makes PRIORITIZE's imminence and
intensity axes dimensionally honest (Elevation §3.1).

**Window id (stable, deterministic):**
```
window_id = 'kfw_' + sha256( f'{chart_id}|{e}|{round(t_start,6)}|{round(t_end,6)}|{weights_version}|{x_schema_version}' )[:24]
```
This id is the **`authority_basis` value** that every temporal claim product-wide cites
(item 44). Any serving path computing its own window is a build error.

### 5.3 Tables `kala_field` and `kala_field_windows`

```sql
kala_field (                                   -- the segment representation (Elevation "stage 4")
  id BIGSERIAL PRIMARY KEY,
  chart_id UUID NOT NULL,
  event_class TEXT NOT NULL,
  segment_index INT NOT NULL,                  -- ascending within (chart, event_class)
  t_start DOUBLE PRECISION NOT NULL,
  t_end   DOUBLE PRECISION NOT NULL,
  alpha   DOUBLE PRECISION NOT NULL,           -- ln λ at t_start⁺
  gamma   DOUBLE PRECISION NOT NULL,           -- d(ln λ)/dt on the segment
  lambda_start DOUBLE PRECISION NOT NULL,      -- exp(alpha)               (denormalized, for cheap reads)
  lambda_end   DOUBLE PRECISION NOT NULL,
  integral_days DOUBLE PRECISION NOT NULL,     -- Λ over this segment       (denormalized, additive)
  promise_term DOUBLE PRECISION NOT NULL,      -- P̃_e (constant in t)
  clock_term_start DOUBLE PRECISION NOT NULL,  -- C_e(t_start)
  modifier_term_start DOUBLE PRECISION NOT NULL,
  suppression_term_start DOUBLE PRECISION NOT NULL,   -- S_e(t_start) ∈ (0,1]
  signed_obstruction_start DOUBLE PRECISION NOT NULL, -- −(1 − S)   SERVING RENDERING ONLY
  refinement_depth SMALLINT NOT NULL DEFAULT 0,
  refinement_exhausted BOOLEAN NOT NULL DEFAULT FALSE,
  weights_version TEXT NOT NULL,
  x_schema_version TEXT NOT NULL,
  field_snapshot_id TEXT NOT NULL,
  UNIQUE (chart_id, event_class, segment_index)
);
CREATE INDEX idx_kala_field_lookup ON kala_field (chart_id, event_class, t_start, t_end);

kala_field_windows (
  id BIGSERIAL PRIMARY KEY,
  chart_id UUID NOT NULL,
  window_id TEXT NOT NULL,                     -- the item-44 authority_basis value
  event_class TEXT NOT NULL,
  t_start DOUBLE PRECISION NOT NULL,
  t_end   DOUBLE PRECISION NOT NULL,
  window_start DATE NOT NULL, window_end DATE NOT NULL, peak_date DATE NOT NULL,  -- rendered
  t_peak DOUBLE PRECISION NOT NULL,
  lambda_peak DOUBLE PRECISION NOT NULL,
  expected_count DOUBLE PRECISION NOT NULL,    -- Λ over the window
  duration_days DOUBLE PRECISION NOT NULL,
  promise_state TEXT NOT NULL CHECK (promise_state IN ('strong','moderate','weak','absent')),
  temporal_shape TEXT NOT NULL CHECK (temporal_shape IN ('point','interval','chain')),
  precision_regime TEXT NOT NULL DEFAULT 'day_grade',
  -- stage 5 columns (written by the same lane, in the stage-5 substep)
  null_p DOUBLE PRECISION, null_R INT, null_resolution DOUBLE PRECISION,
  null_exceeding BOOLEAN,
  robustness JSONB,                            -- see §5.6
  confidence_tier TEXT, weakest_link TEXT,
  adrishta_residual DOUBLE PRECISION,
  weights_version TEXT NOT NULL, x_schema_version TEXT NOT NULL,
  field_snapshot_id TEXT NOT NULL,
  UNIQUE (chart_id, window_id)
);
```

**Relationship to `kala_gochara_windows` (legacy, untouchable).** `ka_kshetra` **reads**
`kala_gochara_windows` read-only as a *cross-check corpus*, and writes **nothing** to it. For
every legacy row it finds, it records the classification of agreement/divergence in
`kala_field_provenance` with `term_role='gate'`, `source_table='kala_gochara_windows'`. It never
copies `signed_intensity` into a field column (§N.5). The equivalence corpus and cutover are
W6 work; W2 only ensures the reference exists so W6 can classify.

### 5.4 Provenance edges (item 11) — schema and the grain

**Grain: one row per (target × term).** A *term* is one multiplicative factor in §5.1 evaluated
at the target's peak. Persisted **at field-write time, inside the same substep transaction** as
the row it explains — never backfilled.

```sql
kala_field_provenance (
  id BIGSERIAL PRIMARY KEY,
  chart_id UUID NOT NULL,
  field_snapshot_id TEXT NOT NULL,
  target_kind TEXT NOT NULL CHECK (target_kind IN ('window','segment','insight')),
  target_id TEXT NOT NULL,                 -- window_id | '<event_class>#<segment_index>' | insight_id
  term_role TEXT NOT NULL
    CHECK (term_role IN ('baseline','promise','route','clock','modifier','suppression','gate')),
  term_key TEXT NOT NULL,                  -- 'baseline' | 'promise' | 'route:rank2'
                                           -- | 'clock:vimshottari:AD:Ke' | 'modifier:x4_av_kaksha_gate'
                                           -- | 'suppression:vedha:Sa->10' | 'gate:legacy_sweep_xref'
  term_value DOUBLE PRECISION NOT NULL,    -- the factor's VALUE at t_peak (e.g. a_s^{w_s}, exp(β_j x_j))
  log_contribution DOUBLE PRECISION NOT NULL,   -- ln(term_value)
  weight_id TEXT,                          -- 'w_s:vimshottari' | 'beta:x4' | 'rho:vedha' | NULL
  weight_value DOUBLE PRECISION,
  weights_version TEXT NOT NULL,
  source_kind TEXT NOT NULL
    CHECK (source_kind IN ('l0_reference','l1_fact','l2_signal','l3_row','derived')),
  source_table TEXT, source_pk TEXT, source_fact_id TEXT,
  authority_basis TEXT NOT NULL,           -- the window_id this edge's target inherits (item 44)
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (chart_id, field_snapshot_id, target_kind, target_id, term_key)
);
CREATE INDEX idx_kfp_target ON kala_field_provenance (chart_id, target_kind, target_id);
CREATE INDEX idx_kfp_fact   ON kala_field_provenance (source_fact_id);
```

**THE RECONCILIATION INVARIANT (the §N.7 detector — this is what makes provenance *earned*
rather than decorative).** For every `window` target:

```
| ln(lambda_peak)  −  Σ over that window's provenance rows of log_contribution |  ≤  1e-9
```

(The `baseline` and `promise` rows carry `ln λ⁰_e` and `ln P̃_e` respectively, so the sum is
complete by construction.) This is asserted **in the writer** (halting the substep on failure,
error `provenance_reconciliation_failed`) **and** in CI over both canonical charts. A provenance
row set that does not reconstruct the value it explains is not weak evidence — it is no
evidence, and the build fails.

**The citation join.** `source_fact_id` resolves back to `chart_facts.fact_id` (or the L2 signal
id). CI asserts **100 % resolution**: a dangling `source_fact_id` fails the build (§N.5).

### 5.5 Stage 5 — the circular-shift null calibration (item 23)

**What is shifted and what is not.** The **transit stream** is shifted; the **natal structure and
the daśā ladder are held fixed**. Shifting the daśā ladder would destroy the chart's identity;
shifting the natal points would destroy the chart. This asymmetry *is* the null hypothesis:
*"the sky's timing carries no information about this chart's events beyond what the clocks
already say."*

**Procedure (fully deterministic — no RNG anywhere; hash-replay must hold).**

```
Horizon H = 36525 days. Replicates R = 256.
Shift grid:  δ_r = r · (H / R),  r = 1 … R      (deterministic, NOT drawn)

For each replicate r:
  1. Re-evaluate every TRANSIT-derived covariate at circular-shifted time:
        x_j^{(r)}(t) = x_j( (t + δ_r) mod H )
     Concretely: rebuild the stage-1 envelope index with every primitive's knots
     translated by −δ_r and wrapped into [0, H). Clock terms C_e, promise P̃_e, baseline λ⁰_e,
     and all weights are UNCHANGED.
  2. Rebuild the segment representation for the replicate (same breakpoint machinery).
  3. For each duration bucket L ∈ {1, 3, 7, 15, 30, 60, 90, 180, 365, 730} days, compute
        M_r(L) = max over t on a 1-day grid of   Λ^{(r)}_e(t, t+L)
     (a sliding-window maximum of the integrated hazard — a matched filter at scale L).
```

**Per-window p-value (permutation p-value with the standard +1 correction):**
```
For observed window W of duration L_W and integrated hazard Λ_obs = Λ_e(W):
   L*      = the smallest bucket L ≥ L_W          (conservative: a longer filter can only
                                                   accumulate more, so p is an upper bound)
   null_p  = ( 1 + #{ r : M_r(L*) ≥ Λ_obs } ) / ( R + 1 )
   null_resolution = 1 / (R + 1)  = 1/257 ≈ 0.00389
   null_exceeding  = ( null_p ≤ 0.05 )
```
`null_p` is served with `null_R` and `null_resolution` so a consumer can never mistake
`p = 0.0039` for `p = 0` (LAW ZERO: we do not report a precision the replicate count cannot
support).

**The window threshold `q_e`** used in §5.2 is the null's 95th percentile *rate*:
```
q_e = quantile_{0.95} over { λ^{(r)}_e(t_g) : r = 1…R, t_g on the 1-day grid }
```
so "a window" means *"a stretch where this chart's own hazard exceeds what its own shifted sky
would produce 95 % of the time"* — a definition, not a tuning knob.

```sql
kala_field_null (
  id BIGSERIAL PRIMARY KEY, chart_id UUID NOT NULL,
  event_class TEXT NOT NULL,
  replicates INT NOT NULL, horizon_days DOUBLE PRECISION NOT NULL,
  q_threshold DOUBLE PRECISION NOT NULL,           -- q_e
  bucket_days INT NOT NULL,
  null_max_stats DOUBLE PRECISION[] NOT NULL,      -- M_r(L) for r = 1..R, this bucket
  weights_version TEXT NOT NULL, x_schema_version TEXT NOT NULL,
  field_snapshot_id TEXT NOT NULL,
  UNIQUE (chart_id, event_class, bucket_days, field_snapshot_id)
);
```

**Cost control (mandatory).** R=256 full rebuilds per class is the dominant cost of W2. The
replicate rebuild reuses the SAME clock/promise terms and only re-indexes stage-1 envelopes, so
it is ~an order of magnitude cheaper than a fresh stage-4 pass. Substep grain is
`(stage5, event_class, replicate_block_of_32)` — 8 substeps per class. If a substep approaches
the writer's `writer_timeout_seconds`, reduce the block to 16; **do not raise the timeout**
(the `ka_gochara_sweep` D-5 lesson, verbatim).

### 5.6 Robustness vector, confidence tier, Adṛṣṭa residual

```json
robustness = {
  "ayanamsha_robust":  true|false,   // window's peak class-assignment survives all 5 pinned ayanāṃśas
  "birth_time_robust": true|false,   // window survives t_peak ± 1.96σ_T without changing null_exceeding
  "system_concurrent": true|false,   // ≥2 applicable, predictive systems have r_{s,e}(t_peak) > 0
  "null_exceeding":    true|false,   // §5.5
  "authority_clean":   true|false    // every provenance source_fact_id resolved (§5.4)
}
```
`confidence_tier` = **the minimum across dimensions** mapped
`{all true → 'concurrent'; any false → 'structural_prior'; overridden to 'calibrated_provisional'
/ 'calibrated' only by stage 9's maturity index}`, and `weakest_link` **names the first false
dimension in the fixed order above** (deterministic).

**Adṛṣṭa residual** — the share of the class's classical expectation that sits outside every
notable window:
```
adrishta_residual_e = clamp01( 1 − ( Σ_{windows w of e} Λ_e(w) ) / ( λ⁰_e · H ) )
```
Served per class; carried onto each window row for convenience.

---

## §6 — Lane D · Stage 6 (salience + submodular selection + rarity) and Stage 6.5 (insights)

### 6.1 The salience vector (item 25)

Five factors, each normalized to `[0,1]`, **served as a vector alongside the ordering scalar**
(the auditability property the native asked for):

| Factor | Formula | Notes |
|---|---|---|
| **Informativeness** `I` | `min(1, −ln(p_cohort) / −ln(1/N_cohort))` | `p_cohort` from §6.3. If `p_cohort` is `None`, `I` is **`null`** and the row carries `not_computed` coverage — never 0. |
| **Consequence** `Q` | `clamp01( 0.5·severity_band/3 + 0.3·min(1, domains_touched/3) + 0.2·significance_class/3 )` | all three from `brahma_event_ontology` |
| **Relevance** `R` | `0.5·domain_match + 0.3·horizon_overlap + 0.2·entity_match`; **`R = 1.0` when no `question_frame` is supplied** | `domain_match ∈ {0,1}`, `horizon_overlap` = Jaccard of the window with the frame's horizon, `entity_match ∈ {0,1}` |
| **Reliability** `B` | `{calibrated:1.0, calibrated_provisional:0.85, concurrent:0.75, structural_prior:0.5}` from `confidence_tier` | §5.6 |
| **Actionability** `A` | `1.0` if an ELECT/UPĀYA lever exists for the class; `0.5` if only a ritual lever; `0.0` if the tri-plane `intervention_ref` is an honest `no_lever` | §11 tri-plane |

**Ordering scalar** (versioned, served with the vector):
```
salience = Σ_f v_f · factor_f ,   v^{(v0)} = [I 0.30, Q 0.25, R 0.20, B 0.15, A 0.10]
```
Missing factors are **renormalized over the present ones**, and the row records
`salience_basis = ['I','Q','R','B','A']` minus the absent ones. Never imputed.

### 6.2 Submodular selection — greedy lazy facility-location, (1 − 1/e)-guaranteed

**The objective.** Let `V` = candidate rows, `S ⊆ V` the selected set, `K` the row budget.
Define the **information-atom universe** `C`: an atom is a triple
`(event_class, window_family_id, driver_term_key)` where `driver_term_key` is a
`kala_field_provenance.term_key` whose `|log_contribution|` is among the top 3 for that window.
`window_family_id` = `sha256(event_class | sorted set of clock lord-stacks active at peak)[:16]`
— the principled generalization of the existing `window_families` dedup.

Atom utility `u_c` = `max` salience among the candidates carrying `c`.
Candidate coverage `cov(i,c) ∈ [0,1]` = candidate `i`'s share of atom `c`'s total log
contribution: `|log_contribution_i(c)| / max_j |log_contribution_j(c)|`.

```
F(S) = Σ_{c ∈ C}  u_c · max_{i ∈ S} cov(i, c)          (monotone submodular: facility location)
Δ(i | S) = Σ_{c ∈ C}  u_c · max( 0 , cov(i,c) − max_{j ∈ S} cov(j,c) )
```

**Algorithm: lazy (accelerated) greedy — Minoux's algorithm.**
```
1. Compute Δ(i | ∅) for all i; push (Δ, i) onto a max-heap.
2. Repeat until |S| = K or the popped Δ < δ_min = 0.01 · F(S):
     pop (Δ_stale, i);  recompute Δ(i | S);
     if Δ(i|S) ≥ the heap's current top Δ_stale  →  S ← S ∪ {i};  else push (Δ(i|S), i) back.
3. Deterministic tie-break at every comparison: lower `window_id` (lexicographic) wins.
```
Because `F` is monotone submodular and the constraint is a cardinality constraint, greedy
achieves `F(S) ≥ (1 − 1/e)·F(OPT)`. Lazy evaluation is an exact optimization of the same
greedy — it changes speed, not the result. This is the mathematical fix for "14 of 15 rows are
the same signal type": the second member of a family has `cov` already covered, so its marginal
gain is near zero and the budget spends itself across 15 *different* things.

**Served with the selection (feeds PRIORITIZE's attention ledger, Elevation §6):**
```
selection_trace = [{window_id, marginal_gain, atoms_newly_covered:[...], rank}]
largest_omission = the highest-Δ unselected candidate, with its Δ and why it lost
coverage_fraction = F(S) / F(V)
```

### 6.3 Rarity from `bg_cohort` (item 15) — the EXACT interface Lane D expects

`bg_cohort` is a **sibling lane building concurrently**. Lane D codes against **this contract
only** and must not read `bg_cohort`'s internals.

**Tables `bg_cohort` provides** (L0, `scope='global'`, built only by explicit super-admin L0
trigger per brief §2.5.2):

```sql
cohort_charts (
  cohort_id TEXT NOT NULL, cohort_version TEXT NOT NULL,
  chart_ref TEXT NOT NULL,                -- synthetic id; NOT a chart_id in `charts`
  birth_jd DOUBLE PRECISION NOT NULL, lat NUMERIC(9,6), lon NUMERIC(9,6),
  tz_offset_minutes INT,
  lagna_sign SMALLINT NOT NULL, moon_nakshatra SMALLINT NOT NULL, md_lord TEXT NOT NULL,
  PRIMARY KEY (cohort_id, cohort_version, chart_ref)
);
cohort_positions (
  cohort_id TEXT, cohort_version TEXT, chart_ref TEXT, body TEXT,
  sidereal_longitude NUMERIC(9,6), sign_number SMALLINT, nakshatra_number SMALLINT,
  pada SMALLINT, house_number SMALLINT, is_retrograde BOOLEAN, dignity TEXT,
  PRIMARY KEY (cohort_id, cohort_version, chart_ref, body)
);
cohort_feature_counts (
  cohort_id TEXT, cohort_version TEXT,
  feature_key TEXT, feature_value TEXT,
  n_charts BIGINT NOT NULL, n_total BIGINT NOT NULL,
  PRIMARY KEY (cohort_id, cohort_version, feature_key, feature_value)
);
```

**The ONE function Lane D calls** (`services/ka_kshetra/cohort_client.py`, written by Lane D
against this signature; `bg_cohort`'s lane guarantees the tables):

```python
@dataclass(frozen=True)
class CohortRate:
    p: float | None          # base rate in [0,1]; None ⇒ not computable, see fallback_reason
    n: int                   # matching charts
    n_total: int             # denominator actually used
    cohort_version: str
    matched: bool            # True ⇒ the matched sub-cohort (E7.3) was used
    fallback_reason: str | None

def cohort_base_rate(
    feature_key: str,
    feature_value: str,
    matched_by: dict[str, str | int] | None = None,   # e.g. {'lagna_sign': 1, 'md_lord': 'Ke'}
    conn=...,
) -> CohortRate: ...
```

**Binding behaviour rules:**
1. `matched_by=None` ⇒ read `cohort_feature_counts` directly (`matched=False`,
   `fallback_reason=None`).
2. `matched_by` given ⇒ compute over `cohort_charts` filtered by those columns. **If the matched
   denominator `n_total < 200`, fall back to the global rate**, return `matched=False` and
   `fallback_reason='matched_subcohort_too_small (n=<n>)'`. Never silently.
3. `feature_key` absent from `cohort_feature_counts` and not derivable from `cohort_positions`
   ⇒ return `p=None`, `fallback_reason='feature_not_in_cohort'`. Lane D then emits
   `notInCorpusCoverage('rarity:<feature_key>', reason)` and leaves informativeness **null**.
4. **Minimum viable cohort: `n_total ≥ 10_000`.** Below it, `cohort_base_rate` returns
   `p=None, fallback_reason='cohort_below_minimum (n=<n>)'` for every call, and the W2 gate's
   "cohort base rates served" criterion is **not met** — a park, not a soft pass.
5. `cohort_version` is **pinned into the field hash** (§7.4). A cohort rebuild changes the hash.

### 6.4 Stage 6.5 — insight synthesis (E2): the 8-type catalog

`kala_insights` rows are **manufactured deterministically**, each carrying `fact_ids`, a cohort
surprise score, a robustness vector, and a drill id.

| # | `insight_type` | One-line definition (the trigger predicate) |
|---|---|---|
| 1 | `concurrence` | ≥3 **independent, applicable, predictive** daśā systems have `r_{s,e}(t_peak) > 0` on the same window (independence = distinct `competence_class`). |
| 2 | `rarity_firing` | The window's active configuration occurs in `< p_rare` of the cohort (`p_rare = 0.05`), from `cohort_base_rate` with the matched sub-cohort where available. |
| 3 | `biographical_echo` | A prior period with the **same lord stack** contains ≥1 LEL event of the same class. **LEL-derived — see the Circularity Guard carve-out below.** |
| 4 | `absence_of_expected` | `P_e ≥ 0.60` (strong natal promise) **and** zero windows for `e` in the queried horizon. |
| 5 | `compression` | ≥`k=3` windows from **distinct** `window_family_id`s overlap a single span of ≤ 45 days. |
| 6 | `scarcity` | The recurrence ladder for `e` shows no further window for ≥ `N=5` years after this one — the honest cost-of-inaction. |
| 7 | `reversal` | `sign(signed_obstruction)` crosses, or `λ_e` crosses `q_e` in the opposite direction, within the horizon — "the weather turns in June". |
| 8 | `contrast` | Field diff vs a baseline (`last_month` / `last_year` / a pinned `field_snapshot_id` / an alternative option) exceeds `Δln λ ≥ 0.5` on any class. |

```
insight_score = cohort_surprise × carrier_salience × reliability
  cohort_surprise = −ln(p_cohort) / −ln(1/N_cohort)   (1.0 when p_cohort is None ⇒ NOT surprise-
                                                       credited: use 0.5 and record basis)
```

**The composer contract (E2, enforced):** every view's `reading.thesis` is composed from the
**highest-scoring insight available for that view's scope**. `argument_composer.ts` gains an
assertion that the thesis's `fact_ids` intersect the leading insight's `fact_ids`; a reading
that leads with anything else fails the specificity battery.

**⚠ CIRCULARITY GUARD CARVE-OUT (subtle; a lane that gets this wrong breaks the wave's
headline invariant).** `biographical_echo` reads the LEL. It therefore **must not be produced by
stages 0–8**. Resolution, binding:

- `kala_insights` carries a column **`lel_derived BOOLEAN NOT NULL`**.
- Stage 6.5 (inside `ka_kshetra`, hash-covered) writes **only the seven non-LEL types**, all with
  `lel_derived = FALSE`.
- `biographical_echo` rows are written by the **biographical-join refresh** (Lane E, stage-9
  adjacent, `mi_bhara`'s sibling path) with `lel_derived = TRUE`.
- **The field hash covers only rows with `lel_derived = FALSE`** (§7.4). This is what lets both
  things be true at once: the insight is served, and the field never moved.

```sql
kala_insights (
  id BIGSERIAL PRIMARY KEY, chart_id UUID NOT NULL,
  insight_id TEXT NOT NULL,                 -- 'kin_' + sha256(...)[:24]; the drill id
  insight_type TEXT NOT NULL CHECK (insight_type IN
    ('concurrence','rarity_firing','biographical_echo','absence_of_expected',
     'compression','scarcity','reversal','contrast')),
  event_class TEXT, window_id TEXT,          -- the carrier window (NULL for absence_of_expected)
  t_start DOUBLE PRECISION, t_end DOUBLE PRECISION,
  statement_key TEXT NOT NULL,               -- the composer template key (NOT prose — B.10)
  statement_params JSONB NOT NULL,           -- the computed values the template fills
  fact_ids TEXT[] NOT NULL,
  cohort_surprise DOUBLE PRECISION, cohort_version TEXT, surprise_basis TEXT NOT NULL,
  robustness JSONB NOT NULL,
  insight_score DOUBLE PRECISION NOT NULL,
  lel_derived BOOLEAN NOT NULL DEFAULT FALSE,
  weights_version TEXT NOT NULL, field_snapshot_id TEXT,   -- NULL allowed iff lel_derived
  UNIQUE (chart_id, insight_id)
);
```

`statement_key` + `statement_params`, **never composed prose in the database** — the argument
composer is template-over-computed-data at serving time (brief §7 B.10 prose rule).

---

## §7 — Lane E · Stage 8 (timeline spec), Stage 9 (`mi_bhara`), Living-LEL

### 7.1 `kala_timeline_spec v1` (item 27)

Renderer-agnostic, opt-in (a flag; MCP token budgets do not pay for it by default). Persisted
for determinism and hash-replay; serialized straight through by the views.

```jsonc
{
  "spec_version": "kala_timeline_spec/1",
  "chart_id": "<uuid>",
  "field_snapshot_id": "<hash>",
  "generated_for": "now|ahead|elect|story|priority|explain",
  "t_zero": "1984-02-05T10:43:00+05:30",     // birth instant; all `t` are ISO dates, never raw days
  "now_marker": "2026-07-29",
  "tracks": [                                 // clocks and domains
    { "track_id": "clock:vimshottari",  "kind": "clock",  "label": "Vimśottarī", "row": 0 },
    { "track_id": "domain:career",      "kind": "domain", "label": "Career",     "row": 1 }
  ],
  "intervals": [{
    "id": "kfw_<hash>",                       // == window_id; 1:1 with EXPLAIN drill ids
    "track_id": "domain:career",
    "start": "2027-03-01", "end": "2027-05-20", "peak": "2027-04-08",
    "start_interval": ["2027-02-24","2027-03-06"],   // null when precision_state='instant'
    "end_interval":   ["2027-05-14","2027-05-26"],
    "valence": "gain|loss|neutral|mixed",
    "tier": "structural_prior|concurrent|calibrated_provisional|calibrated",
    "shape": "point|interval|chain",
    "label": "<short label>",
    "expected_count": 0.83,
    "null_p": 0.0117,
    "precision_regime": "day_grade"
  }],
  "points":  [{ "id":"kfk_<n>", "track_id":"clock:vimshottari", "at":"2027-01-14",
                "kind":"dasha_boundary|station|syzygy|ingress", "label":"…",
                "at_interval":["2027-01-09","2027-01-19"] }],
  "bands":   [{ "id":"kfb_<n>", "track_id":"clock:vimshottari", "start":"…","end":"…",
                "kind":"sandhi|eclipse|sade_sati|naisargika_stage", "label":"…" }],
  "legend":  { "tiers":[...], "valences":[...] },
  "drill":   { "instrument":"kala_explain_get", "id_param":"id" }
}
```

**Golden-render test (rail 5, mandatory):** a fixture covering **every** key above — including
`chain` shape, an interval with `start_interval` present, a `no_lever`-adjacent empty `bands`
array, and both canonical charts — rendered and byte-compared. "Full spec surface" means every
key, not every value.

### 7.2 `mi_bhara` — the weight-fitting harness (items 21, 39; E1 D3)

**Objective — the inhomogeneous Poisson process log-likelihood.** For event class `e` with
training events `t_1 … t_{n_e}` over `[0, T]`:
```
ℓ_e(θ) = Σ_{k=1}^{n_e} ln λ_e(t_k; θ)  −  Λ_e(0, T; θ)
ℓ(θ)   = Σ_e ℓ_e(θ)
```
`Λ` is **exactly the §5.2 integrator** — the same code path serves fitting and serving. This is
load-bearing: if the fitter used a different integral, the published skill score would be
measuring a model the product does not serve.

**Optimizer.** `scipy.optimize.minimize(method='L-BFGS-B')` over
`θ = (w_s for predictive s, β_j for j=1..12, ρ_m for the vighna classes)` with box constraints
`w ∈ [0,1]`, `β ∈ [−2,2]`, `ρ ∈ [0,0.95]`. Analytic gradient optional; finite differences
acceptable at this dimensionality (≤ ~25 parameters). Start at `θ⁰` = the classical priors.
Deterministic: fixed start, fixed tolerances (`ftol=1e-9`, `maxiter=500`), no RNG.

**Train/holdout methodology — blocked forward-chaining (rolling-origin) CV. No random splits,
ever** (a random split leaks the future into the past for a temporal model):

```
1. Sort the chart's LEL events by date.
2. FINAL HOLDOUT: the most recent 20% of events are removed entirely. They are scored ONCE
   per release, never used for fitting or for model selection.
3. On the remaining 80%, run k=5 EXPANDING-ORIGIN folds: with quintile cut-dates c_1..c_5,
   fold j fits on events with date < c_j and evaluates on events in [c_j, c_{j+1}).
   λ's integral term for fold j is taken over [0, c_{j+1}] (the observation window actually
   available at that origin) — not over the full horizon.
4. Report the POOLED out-of-sample log-likelihood as the fit's quality; the shipped parameter
   vector is refit on the full 80% with the shrinkage of §7.2 applied.
5. PROSPECTIVE resolutions (predictions filed BEFORE their outcome, from the item-20 ledger) are
   ALWAYS out-of-sample. They are scored and reported SEPARATELY from retrodiction
   (backfill ≠ prospective — Elevation §7). The skill scoreboard carries both numbers; they are
   never summed.
```

**Shrinkage to classical priors (hierarchical / empirical-Bayes, conservative).** For each
parameter `φ` with classical prior `φ⁰` (weights version `v0_classical`, seeded by migration):
```
φ̂_shrunk = ( n_eff / (n_eff + τ) ) · φ̂_MLE  +  ( τ / (n_eff + τ) ) · φ⁰ ,     τ = 20 events
```
`n_eff` = the number of **out-of-sample** events in the stratum the parameter governs
(per-event-class for `β`/`ρ`; pooled across classes for `w_s`).
- `n_eff = 0` ⇒ `φ̂ = φ⁰` **exactly** — this is the LEL-absent scenario (Elevation §7) falling out
  of the formula rather than being special-cased.
- `n_eff = 20` ⇒ half-way. `n_eff = 57` (the current LEL) ⇒ 74 % data, 26 % prior.
- **Trust region (per release):** `|φ̂_shrunk − φ_prev_release| ≤ 0.5·|φ_prev_release| + 0.25`.
  A single release can never move a weight arbitrarily far; a clipped parameter is recorded with
  `clipped = TRUE` on the version row.

### 7.3 The temporal skill score and the time-rescaling GOF (both real, computable, falsifiable)

**THE SKILL SCORE.** Per chart, per event class — a **log-likelihood-ratio skill score against
the chart's own circular-shifted null**, in **nats per event**:

```
SS_e  =  ( 1 / n_e ) · [  ℓ_e(model)  −  mean_{r=1..R} ℓ_e(null^{(r)})  ]

  ℓ_e(model)     = Σ_k ln λ_e(t_k)          − Λ_e(0,T)            using the FITTED, OUT-OF-SAMPLE λ
  ℓ_e(null^{(r)}) = Σ_k ln λ^{(r)}_e(t_k)   − Λ^{(r)}_e(0,T)       λ^{(r)} = the §5.5 replicate
  n_e            = number of scored LEL events of class e
```

Chart-level: `SS = Σ_e n_e·SS_e / Σ_e n_e` (event-weighted).

**Interpretation:** `SS_e` is the mean log-likelihood advantage, per event, of the real sky's
timing over the same sky shifted. `exp(SS_e)` is the per-event likelihood ratio. **`SS_e = 0` is
exactly the null hypothesis "this field carries no temporal information."**

**Uncertainty:** percentile bootstrap over the `n_e` events, `B = 2000` resamples, seed
`= int(sha256(f'{chart_id}|{weights_version}|{e}').hexdigest()[:8], 16)` — deterministic, so a
rerun reproduces the interval. Report `[SS_lo, SS_hi]` at 95 %.

**Honesty rule (LAW ZERO, and the §N.7 detector for the claim "this instrument has skill"):**
```
skill_state = 'established'      iff  SS_lo > 0  and  n_e ≥ 8
            = 'not_established'  iff  SS_lo ≤ 0  and  n_e ≥ 8
            = 'underpowered'     iff  n_e < 8
```
**We publish the number in all three states.** `not_established` is a legitimate, shippable,
honest result — the instrument is more impressive for reporting it (G4).

**Regression gate (E7.5).** The first published `SS` per chart becomes the CI baseline.
"Regressed" = `SS_new < SS_best_released − 0.05` nats/event, absent a classified reason recorded
in the state ledger. The 0.05 tolerance is stated so ordinary refit churn does not trip the gate;
it is versioned with the harness.

**THE TIME-RESCALING GOODNESS-OF-FIT TEST.** By the time-rescaling theorem, if `t_1 < … < t_n`
are a realization of the point process with intensity `λ_e`, then
```
τ_k = Λ_e(t_{k−1}, t_k)          (with t_0 = 0)   are i.i.d. Exponential(1)
z_k = 1 − exp(−τ_k)                               are i.i.d. Uniform(0,1)
```
Two tests, both required:
1. **Kolmogorov–Smirnov, one-sample, `{z_k}` vs `U(0,1)`.** Statistic
   `D_n = sup_z |F_n(z) − z|`; p-value from the exact KS distribution (`scipy.stats.kstest`).
   Also emit the KS-plot coordinates and the 95 % bands `±1.36/√n` as **data** (the timeline
   spec's sibling artifact — the portal renders it; we never render prose about it).
2. **Ljung–Box on `{z_k}` at lags 1–5** (`statsmodels.stats.diagnostic.acorr_ljungbox`).
   Dependence in the rescaled times means a missing clustering/refractory term, which a KS test
   alone cannot see.

```
gof_state = 'pass'          iff  KS p ≥ 0.05  AND  Ljung-Box p ≥ 0.05  AND  n ≥ 8
          = 'fail'          iff  n ≥ 8  AND  (either p < 0.05)   → failing_statistic named
          = 'underpowered'  iff  n < 8
```
`n < 8` is **never** reported as a pass (§N.7: a PASS needs a detector with the power to fail).

```sql
kala_field_skill (
  id BIGSERIAL PRIMARY KEY, chart_id UUID NOT NULL,
  event_class TEXT,                          -- NULL row = the chart-level aggregate
  weights_version TEXT NOT NULL, field_snapshot_id TEXT NOT NULL,
  n_events INT NOT NULL, n_prospective INT NOT NULL, n_backfill INT NOT NULL,
  skill_score DOUBLE PRECISION NOT NULL,     -- SS_e, nats/event
  skill_lo DOUBLE PRECISION NOT NULL, skill_hi DOUBLE PRECISION NOT NULL,
  skill_state TEXT NOT NULL CHECK (skill_state IN ('established','not_established','underpowered')),
  skill_prospective DOUBLE PRECISION,        -- the SEPARATE prospective-only score
  null_replicates INT NOT NULL,
  released_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (chart_id, COALESCE(event_class,''), weights_version, field_snapshot_id)
);
kala_field_gof (
  id BIGSERIAL PRIMARY KEY, chart_id UUID NOT NULL, event_class TEXT,
  weights_version TEXT NOT NULL, field_snapshot_id TEXT NOT NULL,
  n INT NOT NULL,
  ks_statistic DOUBLE PRECISION, ks_p DOUBLE PRECISION,
  ljung_box_p DOUBLE PRECISION,
  gof_state TEXT NOT NULL CHECK (gof_state IN ('pass','fail','underpowered')),
  failing_statistic TEXT,
  rescaled_z DOUBLE PRECISION[] NOT NULL,    -- the z_k, so the KS plot is reproducible
  UNIQUE (chart_id, COALESCE(event_class,''), weights_version, field_snapshot_id)
);
```

### 7.4 The field hash (E5) — exact definition

```
field_snapshot_id = 'kfs_' + sha256( canonical_json({
    "chart_id":         <uuid>,
    "corpus_pin":       <the pinned corpus/reference build id>,
    "config_pin":       <ephemeris version, ayanamsha id, horizon H, P_floor, τ, ρ_max,
                         x_schema_version, orb table version>,
    "weights_version":  <the PINNED version, §7.5>,
    "cohort_version":   <bg_cohort version used for rarity>,
    "rows":             <canonical serialization of every stage 0–8 row for this chart,
                         EXCLUDING kala_insights rows with lel_derived = TRUE,
                         EXCLUDING the columns id / computed_at / created_at / released_at,
                         sorted by (table_name, natural key)>
}) )[:32]
```
Floating-point columns are serialized with `repr` at 17 significant digits (round-trip exact) so
the hash is stable across platforms. Hash-replay CI: build twice, assert bit-identical.

### 7.5 Weights versioning and the **weights-version acyclicity mechanism** (brief §2.5.4)

This is the subtlest part of the wave. Getting it wrong creates an `L3 ↔ L5` DAG cycle that
`resolveBuildPlan`'s `topoSort` rejects — **breaking every future chart build**, not just this
wave's.

**The rule, stated exactly: `ka_kshetra` NEVER lists `mi_bhara` in `depends_on`.**
That edge, combined with the necessary `mi_bhara.depends_on = ['ka_kshetra']`, would form the
cycle `ka_kshetra → mi_bhara → ka_kshetra`.

**How the calibration loop closes anyway — by version pin, not by DAG edge:**

1. **`weights v0` is seeded by MIGRATION**, not by a writer. Migration `469` inserts
   `kala_field_weight_versions(version_id='v0_classical', status='active', …)` plus its
   `kala_field_weights` parameter rows (the classical structural priors). Therefore **every
   chart's very first build finds an active weights version** — there is no NULL-weights code
   path, and no build order in which `ka_kshetra` needs `mi_bhara` to have run.
2. **`ka_kshetra` READS the newest active version** — a *data* dependency, not a build
   dependency:
   ```sql
   SELECT version_id FROM kala_field_weight_versions
    WHERE status = 'active' ORDER BY activated_at DESC, version_id DESC LIMIT 1;
   ```
3. **`mi_bhara` WRITES a new version row** (INSERT only — never UPDATE an existing version;
   weights are versioned artifacts and silent mutation is a drift failure).
4. **The NEXT `ka_kshetra` rebuild pins the newer version.** The loop closes **ACROSS builds**
   while the DAG stays acyclic **WITHIN every build.**

**Sub-rule 5 (a real correctness trap, easy to miss).** `ka_kshetra` resolves the weights version
**exactly once, in `plan_substeps`**, and stores it in the substep plan payload. Every substep
reads the pinned value **from the plan**, never re-querying the table. Without this, a long build
that straddles an `mi_bhara` release would produce segments under two different weights versions
in one snapshot — a non-deterministic field hash and a silently mixed model. A CI test builds a
chart while inserting a new active version mid-build and asserts a single `weights_version`
across every `kala_field` row of that snapshot.

**Sub-rule 6 (CI guard, §N.7-shaped).** A test asserts (a) `'mi_bhara' NOT IN` the seeded
`depends_on` of `ka_kshetra`, and (b) `resolveBuildPlan` topo-sorts a plan containing
`{ka_kshetra, mi_bhara, mi_sankalpa}` **without error** — a positive assertion, so the guard
would correctly fail if someone added the edge, rather than merely not-noticing.

```sql
kala_field_weight_versions (
  version_id TEXT PRIMARY KEY,               -- 'v0_classical', 'v1_2026-08-14_abhisek', …
  status TEXT NOT NULL CHECK (status IN ('active','superseded','rejected')),
  fitted_from_chart_id UUID,                 -- NULL for v0_classical (global structural prior)
  scope TEXT NOT NULL CHECK (scope IN ('global','per_chart')),
  x_schema_version TEXT NOT NULL,
  n_events_used INT NOT NULL DEFAULT 0, n_prospective_used INT NOT NULL DEFAULT 0,
  tau_shrinkage DOUBLE PRECISION NOT NULL,
  any_clipped BOOLEAN NOT NULL DEFAULT FALSE,
  fit_loglik DOUBLE PRECISION, holdout_loglik DOUBLE PRECISION,
  activated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  notes TEXT
);
kala_field_weights (
  version_id TEXT NOT NULL REFERENCES kala_field_weight_versions(version_id),
  weight_id TEXT NOT NULL,                   -- 'w_s:vimshottari' | 'beta:x4' | 'rho:vedha' | 'd:AD'
  weight_value DOUBLE PRECISION NOT NULL,
  prior_value DOUBLE PRECISION NOT NULL,     -- φ⁰
  n_eff INT NOT NULL, clipped BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (version_id, weight_id)
);
```

**Per-chart vs global scope.** `scope='per_chart'` versions are selected by
`fitted_from_chart_id = <this chart>` first, falling back to the newest `scope='global'` version.
The selection rule is part of the field hash input (it determines `weights_version`).

### 7.6 The Living-LEL plane (item 39) and item 20

**The incremental flow on one LEL append** (LEL entries remain native-only):
1. **Falsifier resolution first** — score the event against every open prospective ledger entry
   (item 20: every AHEAD window and every adopted upāya auto-files one). Prospective hits/misses
   are the gold-standard currency and are tallied separately from backfill.
2. **Weight update** via §7.2 shrinkage → a **new weights version row**.
3. **Skill + GOF recompute**, published to `kala_field_skill` / `kala_field_gof`.
4. **Biographical-join refresh** — `biographical_echo` insights (`lel_derived=TRUE`), STORY
   chapter verdicts, per-chapter retrodiction fits. The only served artifacts consuming LEL
   directly.
5. **Maturity index update** —
   `calibration_maturity = {n_events, prospective_resolutions, event_class_coverage,
   weights_version, skill_score}`, carried in every envelope
   (`kala_envelope.ts::CalibrationMaturity` — the shape already exists; W2 fills it, and
   `noLelCalibrationMaturity()` remains the correct value for the LEL-absent chart).

**Dispatch discipline (brief §2.5.5 — binding).** The LEL-append hook dispatches a **standard,
tracked, scoped build run** (`asset_set = ['mi_bhara', <biographical-join refresh>]`) through the
orchestrator/pipeline. **No side-channel recomputation** — the orchestrator remains the sole
build-state writer. Nirmāṇa must see state, progress, and throughput for a recalibration exactly
as for any other build.

**The portal calibration receipt (a W2 deliverable, not aspiration).** The LEL-intake path
returns, through the existing `mimamsa`/standing-predictions surface:
```jsonc
{ "predictions_scored": [ { "prediction_id": "...", "window_id": "kfw_...",
                            "outcome": "hit|miss|unresolved", "filed_at": "...",
                            "lead_time_days": 243 } ],
  "hits": 2, "misses": 0,
  "maturity_before": { ... }, "maturity_after": { ... },
  "tier_migrations": [ { "scope": "career", "from": "structural_prior",
                         "to": "calibrated_provisional" } ] }
```

**The three LEL scenarios (D6) — all three gated at W2, not merely designed:**

| Scenario | Weights | Views serve |
|---|---|---|
| LEL-rich | fitted with shrinkage | calibrated-track claims where `n_eff` supports; biography-bearing insights |
| **LEL-absent** | `φ = φ⁰` exactly (falls out of `n_eff=0`) | everything `structural_prior`; STORY chapters flagged `no_lived_history_recorded`; `calibration_maturity` an honest **zero**; `skill_state='underpowered'` |
| LEL-growing | matures event by event | tiers migrate visibly, auditable via `tier_migrations` |

The W2 gate requires the **LEL-absent scenario verified on a real chart**, not asserted.

---

## §8 — Cross-cutting: the substep plan, item 44, and the Circularity Guard

### 8.1 `ka_kshetra` substep plan (HEAVY writer)

`plan_substeps(ctx)` returns, in this order (the orchestrator may dispatch in ANY order within a
stage, so **every substep must be correct under arbitrary dispatch order**):

```
stage0:<body>                                  (9 substeps)
stage1:<primitive_kind>                        (~10)
stage2:<event_class>                           (per populated class)
stage3:<system_id>                             (per applicable system)
stage4:<event_class>:<decade>                  (classes × 10)
stage5:<event_class>:<replicate_block 1..8>    (classes × 8)
stage6:<event_class>
stage65:<insight_type>                          (7 — the non-LEL types only)
stage8:<view>                                   (6)
```

**Deletion happens ONCE, in `plan_substeps`**, on the fresh/replanned branch, scoped to
`(chart_id)` across all `kala_*` field tables this writer owns. Never in `run_substep`.
Cross-attempt resumption reuses `build_substep_progress` (migration 436) exactly as
`ka_gochara_sweep` does — that table is untouchable; use it, don't change it.

**Ordering constraint the plan MUST encode:** stages are sequential (`stage4` needs all of
`stage0–3` committed). Because the orchestrator dispatches within a plan freely, the plan is
emitted as **stage-gated batches**: `plan_substeps` returns only the current stage's substeps
plus a sentinel; each stage's completion re-plans the next. If the frozen contract does not
support re-planning mid-run, the fallback (and the default a builder should implement) is a
**single substep per stage-slice that internally checks its upstream stage's row counts and
raises `upstream_stage_incomplete`** rather than silently computing on partial data. **If a lane
concludes the frozen contract genuinely cannot express this, it STOPS and raises with the
native — it does not modify the orchestrator (§N.2).**

### 8.2 Item 44 — authority-basis population at W2

Real field window-ids exist for the first time here. Therefore W2:
- emits `window_id` as the canonical `authority_basis` value (§5.2);
- wires every temporal-claim-bearing serving path to emit `authority_basis`;
- re-points Phala windows to field window-ids wherever they are not already;
- **reports** the census scoreboard in the state ledger (paths enumerated / carrying
  `authority_basis` / computing their own windows — the last must trend to 0).
**W2 reports; W6 gates.** A W2 shortfall is a tracked number, not a wave blocker.

### 8.3 THE CIRCULARITY GUARD — the invariant, stated exactly

> **CG-1.** Let `H(chart, corpus_pin, config_pin, weights_version, cohort_version)` be the field
> hash of §7.4 — the SHA-256 over the canonical serialization of every row written by stages 0–8
> for that chart, **excluding** rows with `lel_derived = TRUE` and excluding the columns
> `id / computed_at / created_at / released_at`.
>
> **For any mutation μ of that chart's LEL — insert, update, or delete of any life-event row —
> that leaves `(corpus_pin, config_pin, weights_version, cohort_version)` unchanged, `H` is
> bit-identical before and after.**

**The detector (CI test `circularity_guard_lel_invariance`), with its vacuity half:**
```
1. Build stages 0–8 for chart C  → record H₀.  Run stage 9 → record digest S₀
   (S = sha256 of the fitted weight vector ‖ skill scores ‖ gof states).
2. BEGIN;  INSERT a synthetic LEL event for C.
3. Rebuild stages 0–8 → H₁.   Run stage 9 → S₁.
4. ASSERT  H₁ == H₀        # the field did not move  ← the Guard
   ASSERT  S₁ != S₀        # stage 9 DID move        ← the §N.7 vacuity half:
                           #   without this, the test passes even if stage 9 is dead code,
                           #   which would make the Guard a signal with no detector.
5. ROLLBACK;
```
**Plus a static half:** an import/SQL scan asserting that no module on the stage 0–8 code path
(`services/ka_kshetra/stage{0,1,2,3,4,5,6,65,8}*.py` and their transitive imports) references the
LEL tables. Whitelist-based; a new LEL reference on that path fails CI.

**Both halves are required.** The dynamic half catches a data path; the static half catches a
path that happens not to fire on the fixture chart.

**The Guard binds from W1** (with item 10's per-chapter LEL pinning); W2 **extends** this test,
it does not introduce it.

---

## §9 — Nirmāṇa build-tracker contract (brief §2.5) — DAG edges, seed rows, migrations

### 9.1 DAG edges (`depends_on`)

```
ka_kshetra.depends_on = [
  'ka_dasha_kala',          # clocks / dasha eligibility (L3)
  'ka_gochara_sweep',       # legacy sweep, read-only cross-check corpus (L3)
  'ka_gochara_resonance',   # gochara_resonance_map targets (L3)
  'ga_panchanga',           # panchanga limbs, referenced not recomputed (L1)
  'bo_pratijna',            # promise (L2)
  'bo_sangati',             # relational structure for the promise graph (L2)
  'bo_upaya',               # intervention/suppression links (L2)
  'bg_cohort'               # L0 global — rarity + specificity cohort
]
mi_bhara.depends_on    = ['ka_kshetra']
mi_sankalpa.depends_on = ['ka_kshetra']

ka_kshetra.depends_on MUST NOT CONTAIN 'mi_bhara'.   ← §7.5; a cycle that breaks every build
```

**⚠ THE EDGE-STAGING RULE (a real trap; get this wrong and every chart build 500s).**
Brief §2.5.3 proposes `bg_sky_calendar` as a `ka_kshetra` dependency — but `bg_sky_calendar` is a
**W3** asset (item 3). §2.5.1 requires every edge to resolve to an **existing** `asset_id`;
`resolveBuildPlan`'s `topoSort` cannot resolve an edge to an id with no seed row.

Therefore: **W2 declares the eight edges above and NOT `bg_sky_calendar`.** W3 **adds**
`'bg_sky_calendar'` to `ka_kshetra.depends_on` **in the same PR that lands `bg_sky_calendar`'s
seed row** — never before. W2's stage 0 accordingly computes syzygy/eclipse *candidates* itself
and marks eclipse magnitude/visibility `not_in_corpus` (§3.1); W3 upgrades them. A W2 lane that
"helpfully" pre-declares the edge breaks production.

**L0 gating consequence (brief §2.5.2).** `bg_cohort` is a `bg_*` global asset built **only via
an explicit super-admin L0 trigger** — never auto-pulled into a user's chart build. A per-chart
build whose `bg_cohort` upstream is dormant shows `ka_kshetra` as **blocked** ("L0 dependency not
built — run the Brahmagyan layer first"). That is correct behaviour, not a defect. **The W2 gate
therefore requires `bg_cohort` built in PRODUCTION before the first per-chart `ka_kshetra`
build**, so no ordinary user build encounters the blocked state.

### 9.2 `asset_registry` seed rows (same PR as the writer — §2.5.1)

| field | `ka_kshetra` | `mi_bhara` |
|---|---|---|
| `asset_id` | `ka_kshetra` | `mi_bhara` |
| `layer` / `layer_name` / `layer_index` | `kala` / `Kāla` / `L3` | `mimamsa` / `Mīmāṃsā` / `L5` |
| `sanskrit_name` | `Kāla Kṣetra` | `Kāla Bhāra` |
| `english_name` | `Temporal Field` | `Field Weight Calibration` |
| `asset_kind` / `storage_type` | data / `postgres_table` | data / `postgres_table` |
| `target_table` | `kala_field` | `kala_field_weight_versions` |
| `count_sql` | `SELECT COUNT(*) FROM kala_field WHERE chart_id=$1` | `SELECT COUNT(*) FROM kala_field_skill WHERE chart_id=$1` |
| `scope` | `per_chart` | `per_chart` |
| `has_writer` / `has_substeps` | true / true | true / false |
| `writer_timeout_seconds` | 1800 | 900 |
| `depends_on` | §9.1 | `['ka_kshetra']` |
| `target_floor` | set to the ACHIEVED count after the first build (§N.4: floors are aspirational, never fabricated) | same |

The catalog-reconciliation CI check (every `@register` id ↔ seed row) must be **green in the same
PR**. A writer without a seed row is invisible to Nirmāṇa ⇒ the wave gate fails.

### 9.3 Migration table list (names + rough columns; the migrations themselves are builder work)

Reserve **467–476** (current max in-tree is 466). One table family per migration; surgical only,
migration-guard reviewed; never `deploy.yml`-auto or bulk `migrate.ts` (§N.4).

| # | Migration | Tables |
|---|---|---|
| 467 | `kala_field_stage0_1` | `kala_field_kinematics`, `kala_field_primitives` |
| 468 | `kala_field_promise` | `kala_field_promise_nodes`, `kala_field_promise_edges`, `kala_field_routes` |
| 469 | `kala_field_weights_seed` | `kala_field_weight_versions`, `kala_field_weights` **+ the `v0_classical` seed rows** (this is the acyclicity keystone — it must land BEFORE `ka_kshetra` ever runs) |
| 470 | `kala_field_clocks` | `kala_field_clocks`, `kala_field_boundaries` |
| 471 | `kala_field_core` | `kala_field`, `kala_field_windows` |
| 472 | `kala_field_provenance` | `kala_field_provenance` |
| 473 | `kala_field_null` | `kala_field_null` |
| 474 | `kala_field_salience_insights` | `kala_field_salience`, `kala_insights` |
| 475 | `kala_timeline_spec` | `kala_timeline_spec`, `kala_field_snapshots` |
| 476 | `kala_field_skill_gof` | `kala_field_skill`, `kala_field_gof` + the `ka_kshetra` / `mi_bhara` / `mi_sankalpa` `asset_registry` rows and `depends_on` arrays |

Every migration is `CREATE TABLE IF NOT EXISTS` + `INSERT … ON CONFLICT DO UPDATE` for registry
rows, with an explicit DOWN block in a trailing comment (the existing house style — see
migration 460).

### 9.4 Rolling-horizon / freshness

`ka_kshetra` writes `field_snapshot_id` and the substrate build ids it consumed into
`kala_field_snapshots`, which is what `kala_envelope.ts::buildKalaFreshness` reads at W2 to fill
`{ephemeris_version, sweep_build_date, field_hash}`. **`buildFieldSnapshotIdStub` is replaced by
a real lookup at W2 — and per its own TODO, that function's body is the ONLY thing that changes;
no caller in the eight facades is touched.**

---

## §10 — Gate W2 acceptance criteria, mapped to the artifact that discharges each

| Gate criterion (brief §3 W2) | Discharged by |
|---|---|
| field deterministic (hash-replay) | §7.4 hash + double-build CI |
| LEL-invariance test green | §8.3 CG-1, both halves |
| skill score + GOF published for both charts, regression-gated | §7.3 + `kala_field_skill` / `kala_field_gof` + the 0.05-nat tolerance |
| **LEL-absent scenario verified** (structural-prior weights, `no_lived_history_recorded`, maturity zero) | §7.6 three-scenario table; `n_eff=0 ⇒ φ=φ⁰` falls out of the shrinkage formula |
| cohort base rates served | §6.3 `cohort_base_rate`, `n_total ≥ 10_000` |
| null exceedance on every window | §5.5 `null_p` on every `kala_field_windows` row |
| salience vector visible in PRIORITIZE | §6.1 vector served with the scalar + §6.2 `selection_trace` |
| insight rows lead readings | §6.4 composer assertion |
| timeline spec renders valid | §7.1 golden-render test, full spec surface |
| specificity gate HARD-green | cohort charts from `bg_cohort`; composer templates must vary |
| legacy writers UNTOUCHED and still serving | §1 rail 2; W2 writes zero rows to any legacy table |
| Nirmāṇa: new data assets appear with DB-true counts on both charts | §9.2 seed rows + `count_sql` |
| item 44 populated (reported, not gated) | §8.2 |

---

## §11 — Open questions this design deliberately does NOT decide

1. **Per-chart vs global weights default.** §7.5 specifies the *selection rule*; whether the
   first fitted version is scoped `per_chart` or `global` is a stage-9 empirical call made at the
   first release, recorded on the version row. Not a build-time ambiguity.
2. **`x` covariate #13 and beyond.** Frozen at twelve for W2 (§5.1 C-5). W3's new computations
   (moorti depth, vedha grid, Kota) will want more; each addition is an `x_schema_version` bump
   and a weights refit, not an in-place edit.
3. **Sub-day precision.** Out of scope by construction (brief §4): every row this design writes
   carries `precision_regime='day_grade'`. W2G upgrades the label and the roots; **nothing here
   may be built to REQUIRE sub-day precision.**
4. **KP as a fourth Law-2 voice.** `S_pred(e)` is open by construction — W3K's KP clock joins by
   adding a `bg_dasha_systems` row and a `q_s` rule (§4.1 step 4), with no change to §5.1.

---

*W2 in one line: λ becomes a strictly-positive, log-linearly-segmented, exactly-integrable
hazard whose every factor is a persisted provenance edge that must reconstruct the value it
explains; its notability is measured against the chart's own circular-shifted sky; its weights
are versioned artifacts that flow across builds rather than around the DAG; and its skill is
published as a number that is allowed to say "not established".*
