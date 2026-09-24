---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_JIVANA_PARVA_ELEVATION_BRIEF
version: "1.0"
status: DRAFT_FOR_INDEPENDENT_REVIEW
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md
synergy_binding_version: "2.3"  # binding is UNADOPTED (PROPOSED_FOR_NATIVE_RULING_THEN_ADOPTION) and its §B8 item 9
# still lists the rename direction as open while §B1 asserts it. Authority for the field NAME is therefore the
# underlying rulings, not the binding: Kṣetra ruling 8 + Gochara G-9 + Saṅgam M-3 name `precision_regime`, native
# ruling D-S4 (2026-09-24) confirms it. Alias condition is Saṅgam D-7: `day_grade` reads as `date_grain` until every
# dependent claim has an authorized successor — NOT for a count of generations. Values {instant_grain, date_grain}.
asset_or_interface_ids: ["ka_jivana_parva", "SC-1 (it already reads `ctx.config['as_of_date']` — the ONE writer in the layer that does; that key is the precedent every other as_of proposal should cite)", "SC-9 (the LATERAL LIMIT 1 predicate pick is an unordered choice among per-ayanāṃśa rows)", "registry packet: it DECLARES ka_dasha_kala and reads chart_dashas directly"]
goal_objective: "Make the life-arc chapters say which evidence they rest on: the dominant-signal class and the convergence counts are computed from a window set joined to a predicate chosen by an UNORDERED `LATERAL … LIMIT 1` across per-ayanāṃśa rows, so a chapter's headline class can change between builds from identical data; and the PD level is materialised only for the CURRENT antardaśā against a build-time clock, which the row does not declare."
source_revision: "9feac52d7 (l3/kala-layer-briefs); cited code identical at fb46b258f (2026-09-24)"
accepted_upstream_contract: "L1 chart_dashas — read DIRECTLY and explicitly scoped to `system_id='vimshottari'` AND `ayanamsha_id='lahiri_chitrapaksha'` (the writer's own comment records that the unscoped form returns ~7,800 rows across 7 systems × 5 ayanāṃśas and overflows parva_index); ka_sangam's kala_convergence; ka_kala_darshana's effective_score (COALESCEd); ka_yojaka's predicates via a LATERAL pick; birth_date from birth_params for the T-9 pre-birth clip"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_JIVANA_PARVA_v1_0.md"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/pipeline/orchestrator/writers/ka_jivana_parva.py", "platform/python-sidecar/tests/l3/test_ka_jivana_parva*.py", "one additive migration on kala_jivana_parva (qualification columns; the parva_level column already exists via migration 679)"]
interface_packet_targets_not_may_touch: ["platform/src/lib/retrieval/registry/layers/L3_kala/query_life_arc.ts — Pūrṇa-owned", "platform-mcp/src/tools/kala_views/{story,ahead}.ts, register_p1_synthesis.ts, kala_views/register_all.ts — Pūrṇa-owned; L3 owns only the sentinel test"]
must_not_touch: ["chart_dashas / ga_* (L1)", "kala_convergence / ka_sangam, kala_darshana / ka_kala_darshana, kala_activation_predicates / ka_yojaka (producers; their briefs)", "platform-mcp/src/tools/kala_views/**", "applied migrations — incl. 670, 679 and 1033–1070", ".github/workflows/deploy.yml", "kala_gochara_windows WHERE generation='v1'", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY"
target_state_campaign: "ANALYZED → ENRICHED at stage 3"
wave: "W4"
shape: single asset, rows (chart × parva_level ∈ {1,2,3} × parva_index) — MD + AD for the whole life, PD only for the current AD
evidence_base: >
  Source read directly on 9feac52d7 [V]; migration 670's ka_jivana_parva contract (a)–(h),
  migration 679 (the parva_level column and its CHECK), blueprint v5.0 [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.0 (2026-09-24): first issue; awaiting independent review."
---

# `ka_jivana_parva` elevation brief — chapters whose evidence is named

## §0 — The recommendation, in one paragraph

`ka_jivana_parva` writes the life as chapters: one per vimśottarī mahādaśā and antardaśā across the
whole lifetime, plus pratyantardaśā rows **for the current antardaśā only** (~9 rows, keeping the
total near 247 rather than overflowing `smallint`). Three of its design decisions are exemplary and
must survive any elevation. It is **the only writer in this layer that already reads an `as_of_date`
from `ctx.config`** (`:60`, `ctx.config.get('as_of_date') or date.today()`) — the precedent every
other asset's SC-1 proposal in this programme should cite rather than inventing a new key. It
**scopes its L1 read explicitly** to one system and one ayanāṃśa, with a comment recording exactly
why (*"~7,800 rows … the AD loop then matches ADs across that whole mix, so parva_index overflows
smallint AND the chapters are a meaningless blend of systems"*). And it implements the **T-9
pre-birth clip** in prose and in code: `chart_dashas` legitimately carries a pre-birth start for the
first mahādaśā (the balance-of-daśā convention), and this writer refuses to *serve* a chapter the
native never lived — rows ending before birth are dropped, rows straddling birth have their served
start raised. What is undeclared is the **evidence** behind the chapter's headline. The
`dominant_signal_class` and the convergence counts come from a window set whose `signature_class` is
obtained by `LEFT JOIN LATERAL (SELECT signature_class FROM kala_activation_predicates WHERE
signal_id = … AND chart_id = … **LIMIT 1**)` — the comment says the LIMIT exists *"so the
per-ayanamsha predicate rows don't multiply each convergence window"*, which is true and necessary,
but the pick is **unordered**: the predicate rows differ by ayanāṃśa, and nothing says which one
wins. A chapter's headline class can therefore differ between two builds from identical data. And
the PD level exists only for whichever antardaśā contains the build's `as_of_date`, which the row
does not state. Recommendation: **`ENRICH_CORRECT` + `QUALIFY_LIMIT`** — order the pick (or scope it
to the canonical ayanāṃśa, as the spine read already is), stamp `as_of_used` and the PD level's
scope, and declare the evidence set each chapter's class was counted from. Decisions: §10.

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 | life-arc biographical chapters | — |
| Strategy §3 *Interval / trajectory segment* | a chapter is a segment with its own evidence | binds §4.4 |
| **Migration 670 (`:565-681`)** [V] | (a) §N.3 identity key — *"NOT redundant with the one UNIQUE this table carries"*; (b) §N.7 item 2 — *"the level/lord pin the whole contract rests on must actually hold"*; (c) §N.5 L1 authority — *"a life chapter never invents its own span — every parva must …"*; (d) **the machine test of the T-9 pre-birth clip the writer implements in prose**; (e) per-level tiling — the mahādaśā chapters tile the life without gap; (f) every antardaśā chapter sits inside a served mahādaśā chapter of the parent; (g) §N.7 item 6 — `high_convergence_count` is counted from the same window set; (h) `parva_index` is the table's only UNIQUE key and its serving order, so it must be dense | a strong contract — and (g) is precisely the conjunct the LATERAL pick puts at risk |
| **Migration 679** (cited by the writer, `:31`) | added `parva_level` — *"the real level discriminator this table lacked — before this, MD/AD/PD rows were mixed in one flat table with no served column saying which level each row is, recoverable only by string-parsing `source_citation`"*; CHECK `(1/2/3)` | the column exists; the brief does not re-litigate it |
| Seed (`asset_registry_seed.ts:2391-2406`) | `target_table: 'kala_jivana_parva'`, chart-scoped `count_sql`, `depends_on: ['ka_kala_darshana', 'ka_dasha_kala', 'ka_sangam', 'ka_yojaka', 'ga_dashas']`, `asset_kind: 'artifact'`, `catalog_status: 'DRAFT'` | **`ka_dasha_kala` is declared but the writer reads `chart_dashas` directly** — the same declared-service/read-table pattern the clock-authority brief records from the other side |
| `writer.py:60` | `as_of_date = ctx.config.get('as_of_date') or date.today()` | **the layer's only existing `ctx.config` as_of read** — the SC-1 precedent |
| `writer.py:2-20` (docstring) | D7 MD+AD; O6 PD for the current AD only (~9 rows, *"~247 vs 32767"*); the T-9 clip's full rationale | preserved verbatim (§5) |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V]
`storage_type: 'postgres_table'`, `target_table: 'kala_jivana_parva'`, `scope: 'per_chart'`,
`asset_kind: 'artifact'`, `catalog_status: 'DRAFT'`.

### 2.2 The code [V]
- **`as_of`** (`:60`): `ctx.config.get('as_of_date') or date.today()` — reads the key if present,
  falls back to the build clock. (Note the `or` is a falsy-coalesce; a `date` is never falsy, so it
  is safe here — but see §4.2 on stamping which branch fired.)
- **Birth date** (`:63-70`): resolved from `birth_params`; when absent, a warning states *"pre-birth
  clip DISABLED for this build (upstream bug; parvas may include …)"* — honest, and a red path.
- **Idempotency**: `DELETE FROM kala_jivana_parva WHERE chart_id` (`:75`).
- **Spine** (`:79-92`): `SELECT lord_graha, start_date, end_date, level_n FROM chart_dashas WHERE
  chart_id = %s AND level_n IN (1,2) AND system_id = 'vimshottari' AND ayanamsha_id =
  'lahiri_chitrapaksha' ORDER BY start_date, level_n` — explicitly scoped, with the ~7,800-row
  rationale in the comment. Empty → honest refusals (`:94-108`).
- **Window set** (`:110-129`): `SELECT kc.peak_date, kc.convergence_score, kap.signature_class,
  COALESCE(kd.effective_score, kc.convergence_score) AS effective_score FROM kala_convergence kc
  LEFT JOIN kala_darshana kd ON kc.convergence_id = kd.convergence_id **LEFT JOIN LATERAL (SELECT
  signature_class FROM kala_activation_predicates kap WHERE kap.signal_id = kc.signal_id AND
  kap.chart_id = kc.chart_id LIMIT 1)** kap ON true WHERE kc.chart_id = %s AND kc.peak_date IS NOT
  NULL` — the LATERAL's stated purpose is de-multiplication; **it carries no `ORDER BY`**.
- **Chapters** (`:131+`): `parva_index` incremented across MD then AD then PD; `dominant_signal_class`
  by frequency count of `signature_class` across the windows falling in each MD span (`Counter`);
  the T-9 clip applied per row.
- **PD** (docstring O6): level-3 rows **only** for the antardaśā containing `as_of_date`.

### 2.3 Consumers [V]
| consumer | reads | role |
|---|---|---|
| `query_life_arc.ts` | the chapters | served `interpretation` |
| `kala_views/story.ts`, `ahead.ts`; `register_p1_synthesis.ts`; `kala_views/register_all.ts` | the life arc | served — **`story.ts` is the narrative surface a reader actually meets** |
| `source_query_availability.ts` | catalog | census |

**Live-path statement.** The chapters are the layer's narrative surface. The unordered class pick
and the undeclared PD scope are live on it.

### 2.4 Epistemic class
| field | class | authority | note |
|---|---|---|---|
| `lord_graha`, spans | `COMPUTED_FACT_CONFIGURATION` (inherited, clipped) | L1 `chart_dashas` | 670(c) pins the inheritance; 670(d) pins the clip |
| `parva_level`, `parva_index` | structural | this writer (679) | 670(h) pins density |
| `dominant_signal_class` | `INTERPRETIVE_INFERENCE` — a frequency count over a window set | this writer | the set depends on an **unordered** predicate pick |
| `high_convergence_count` | count over the same set | this writer | 670(g) pins *"counted from the same window set"* — which the pick can vary |
| `effective_score` (COALESCEd) | inherited from Darshana, falling back to Saṅgam | two producers | the fallback is honest but unstamped: a reader cannot tell which produced it |
| the PD rows | a **build-time** slice | this writer + `as_of_date` | the scope is not declared on the row |

### 2.5 Ladders
`PLAN_REVIEWED`; `catalog_status: DRAFT`. t3: no event.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | A convergence window whose signal has predicate rows under five ayanāṃśas contributes **one** `signature_class` to its chapter's frequency count — chosen by a `LATERAL … LIMIT 1` with no `ORDER BY`. Postgres may return any of the five, and the choice can differ between builds (plan, page order, vacuum state), so a chapter's `dominant_signal_class` — the headline the narrative surface renders — can change between two builds from identical data, and `high_convergence_count` with it. Migration 670's conjunct (g) requires the count to come from *"the same window set"*; the set is stable, but the class attached to each window is not. Separately, the PD chapters exist only for the antardaśā containing the build's `as_of_date`, and no row says so: a reader paging `parva_level = 3` sees nine chapters and no statement that the rest of the life has none **by design** rather than by omission |
| Evidence | `ka_jivana_parva.py:110-129` (the unordered LATERAL), `:60` (`as_of_date`), the O6 docstring (PD for the current AD only); `670:565-681` conjuncts (g), (h) [V] |
| Expected contract | §N.7 item 2 (*every selection that reduces a set to one row pins its key and carries a total `ORDER BY`* — the `fact-category-pin-lint` defect class); SC-1 (a build-time clock is declared, not implied); B5 (a scope limit is coverage, not silence); 670(g) |
| Defect class | **unordered single-row selection** (§N.7 item 2, exactly) + **undeclared build-time scope** (the PD slice) + **unstamped provenance** (the COALESCEd score) |
| Impact | the narrative surface's headline class is build-dependent; a `parva_level=3` reader cannot distinguish "by design" from "missing"; a consumer of `effective_score` cannot tell whether a verdict or a raw convergence score produced it |
| Non-claim | no claim that the class *does* vary in practice (unmeasured — it requires two builds and a plan change); no claim that the five ayanāṃśas' `signature_class` values actually differ for a given signal (they may well agree, which would make the defect latent rather than active — that is the ablation, §4.9); the ~247-row and ~9-row figures are the writer's own [A] |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q07 (trajectory segments); Q02's "which chapter" half. Not Q03/Q05.
2. **The pick is pinned (§N.7 item 2).** The LATERAL gains a total order and an explicit scope:
   `WHERE … AND kap.ayanamsha_id = 'lahiri_chitrapaksha' ORDER BY kap.signature_class LIMIT 1` —
   scoping to the canonical ayanāṃśa matches the spine read (`:87-89`) and removes the multiplication
   the LIMIT was added for, while the `ORDER BY` makes the residual choice deterministic. **If the
   five ayanāṃśas disagree**, that disagreement is itself information and should be surfaced rather
   than silently resolved (§10.2): the row can carry `signature_class_agreement ∈ {unanimous,
   split}`.
3. **`as_of` stamped and its branch declared.** `as_of_used` and `as_of_source ∈ {declared,
   build_clock}` on every row — this writer already *reads* the config key, so the only change is to
   record which branch fired. **This key is the SC-1 precedent for the layer**: other briefs in this
   programme propose `ctx.config['as_of']`; this asset shows the pattern already exists as
   `as_of_date`, and the layer should use **one spelling** (§10.3).
4. **The PD slice declared (B5).** `coverage = {requested_horizon: [birth, last MD end],
   completed_horizon, resolution: 'parva', partitions_searched: ['level_1','level_2','level_3'],
   exclusions: [{level: 3, reason: 'current_antardasha_only', scope: <the AD's span>}],
   unsearched_regions: [], completion_detector: 'md_ad_tile_life_pd_current_only'}` — so a
   `parva_level=3` reader is told the level is a deliberate slice and which slice.
5. **Provenance on the score.** `effective_score_source ∈ {kala_darshana, kala_convergence}` beside
   the COALESCEd value, so the fallback is visible (§N.7 item 6's spirit: an inherited value names
   its parent).
6. **The clip stays loud.** The missing-birth-date path (`:63-70`) keeps its warning **and** gains
   `completeness_state='unqualified'` with `reason='pre_birth_clip_disabled'` on the affected rows —
   today the warning is in the log, not on the data, and 670(d) would then be testing rows the writer
   itself knows are unclipped.
7. **Declared edges.** `ka_dasha_kala` is declared while `chart_dashas` is read directly; either the
   edge is re-labelled as the service-vocabulary edge it is, or `ga_dashas` (already declared)
   carries it alone and `ka_dasha_kala` is dropped — a registry packet, and the same question the
   clock-authority brief records from its side (§10.4).
8. **Qualification (B2).** `epistemic_class` per §2.4; `operator_role='interpretation'` on the
   dominant class, `'computation'` on the counts; `tier_basis='relative_uncalibrated'`;
   `comparable_with='self'` within a chart; `completeness_state` per §4.6.
9. **Old vs new.** Positive: a chapter whose windows agree on class → the same headline, now with
   `signature_class_agreement='unanimous'`. Negative: no MD rows → the existing honest refusal.
   Boundary: an MD straddling birth → the T-9 clip (unchanged), 670(d) TRUE. Missing: no birth date →
   the warning **and** `unqualified` rows. Duplicated: one signal with five ayanāṃśa predicates →
   **one** contribution, deterministically chosen, agreement stamped.
10. **Simpler baseline.** Today's chapters.
11. **Ablation.** Recompute `dominant_signal_class` under the pinned pick and under a deliberately
    reversed pick: the chapters whose headline changes are the measured exposure. If none changes,
    the five ayanāṃśas agree for this chart and the defect is latent — worth stating either way,
    because latent-by-data is not the same as fixed-by-code.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`, emphatically: the **T-9 pre-birth clip** and its full prose rationale (a 1984 native
  has no lived chapter that began in 1950); the **explicitly scoped spine read** and the ~7,800-row
  comment that explains it; the **PD-only-for-current-AD** design and its smallint rationale; the
  honest refusals; the missing-birth-date warning; migration 679's `parva_level` discriminator.
- `ENRICH_CORRECT`: the pinned LATERAL; `as_of` stamping; score provenance; the `unqualified` state
  on unclipped rows.
- `QUALIFY_LIMIT`: coverage for the PD slice; B2 stamps.
- **Migration**: one additive migration on `kala_jivana_parva`. No FK.
- Fences: all four producer tables are their own briefs'; the five served surfaces are
  interface-packet targets.
- Rollback: additive columns; the pinned pick changes *which* class is chosen only where the
  ayanāṃśas disagree, and the agreement stamp makes that visible.

---

## §6 — Lenses A–J *(appendix)*

| lens | answer |
|---|---|
| A | L3 artifact rows; a narrative segmentation over L1 clocks with L2/L3 evidence counts; `ENRICH_CORRECT + QUALIFY_LIMIT` |
| B | five declared edges; `ka_dasha_kala` declared / `chart_dashas` read directly; fan-out: five served surfaces |
| C | invariants: 670 (a)–(h); every single-row selection pinned and totally ordered; the PD slice declared; the clip's state on the data, not only the log |
| D | no new rows sought; the evidence set is upstream |
| E | `story.ts` is the surface a reader meets |
| F | `as_of_used`, `signature_class_agreement`, `effective_score_source`, coverage machine-readable |
| G | ~247 rows; one spine query, one window query; cheap |
| H | idempotent; delete-then-insert |
| I | files in `may_touch`; one additive migration; W4 |
| J | this brief; §7; the review |

---

## §7 — Proof matrix

Columns: **verdict tier** F24; **scope** `[U]` unit, `[I]` DB fixture, `[S]` served.

| proof | verdict tier | scope | fixture / command | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|---|
| Positive | COMPUTATIONAL_CORRECTNESS | I | canonical chart | MD+AD chapters tiling the life, PD for the current AD; 670 (a)–(h) TRUE; stamps present | the contract | any conjunct FALSE; a stamp absent | integrity SQL |
| Negative | COMPUTATIONAL_CORRECTNESS | I | no vimśottarī MD rows | the existing honest refusal | no write | rows written | writer test |
| **Pinned pick** | COMPUTATIONAL_CORRECTNESS | I | one signal with five ayanāṃśa predicate rows carrying **different** `signature_class` values | one deterministic contribution; `signature_class_agreement='split'`; the same result across repeated builds | §N.7 item 2 | the class varies between runs (today's exposure) | writer test (run twice) |
| Relevant influence | COMPUTATIONAL_CORRECTNESS | I | add one convergence window inside one MD span | that chapter's counts change; others byte-identical | isolation | a second chapter moves | writer test |
| Irrelevant control | COMPUTATIONAL_CORRECTNESS | I | reorder the convergence rows | identical chapters | order-invariant | differs | writer test |
| **T-9 clip** | COMPUTATIONAL_CORRECTNESS | I | a first MD starting before birth | rows ending before birth dropped; a straddling row's served start raised to the birth year; 670(d) TRUE | the clip | a pre-birth chapter served | integrity SQL |
| **Clip disabled** | COMPUTATIONAL_CORRECTNESS | I | `birth_params` without a birth date | the existing warning **and** `completeness_state='unqualified'`, `reason='pre_birth_clip_disabled'` on the rows | the state is on the data | only a log line (today) | writer test |
| Boundary | COMPUTATIONAL_CORRECTNESS | I | two `as_of_date` values in different antardaśās | **different PD slices**, each declared in `coverage.exclusions`; MD/AD chapters byte-identical | the slice is declared | the PD set changes silently | writer test |
| Context | COMPUTATIONAL_CORRECTNESS | I | a window with no `kala_darshana` row | `effective_score` from `kala_convergence` with `effective_score_source='kala_convergence'` | the fallback named | the source unstated | writer test |
| Delivery | COMPUTATIONAL_CORRECTNESS | S | sentinel `signature_class_agreement='split'` on one chapter | reaches `query_life_arc` and `story.ts` | survives | absent | route test |
| Revision | COMPUTATIONAL_CORRECTNESS | I | Darshana rebuilds | chapters replaced; 670(g) TRUE | no accretion | accretion | integrity SQL |
| Value | EXPLANATORY_DISCRIMINATIVE_VALUE | S | frozen Q07 question | the chapter names its evidence set and whether its class was unanimous; the baseline gives a class | — | no distinction | baseline record |
| Evaluation | — | — | `not_applicable` (a chapter is a segmentation, not an outcome claim) | — | — | — | — |

Binding: **OFFERS** B1 (spans inherited from L1 with their grain declared), B2 (`epistemic_class`,
`completeness_state` incl. `unqualified` with reason, `operator_role`, `tier_basis`,
`comparable_with`), B5 (`coverage`, seven keys, carrying the PD slice). **DEMANDS** nothing new;
the evidence tables are upstream. B3: `window_ref` is inherited per window, not minted per chapter;
the chapter's own identity is `(chart, parva_level, parva_index)` — offered with
`generation = FORMULA_VERSION`. B4: the chapters are not witnesses; n/a, stated.

---

## §8 — Prioritization

(1) the pinned LATERAL (a build-dependent headline on the narrative surface) → (2) the PD slice
declared → (3) `as_of` stamped and the layer's one spelling settled → (4) score provenance →
(5) the clip-disabled state → (6) the declared-edge packet. W4.

---

## §9 — Disposition and target state

`ENRICH_CORRECT` + `QUALIFY_LIMIT`. Data-plane: `PRODUCER_READY`; `CONSUMER_INTEGRATED` when
`query_life_arc` and `story.ts` carry the agreement and coverage stamps. Campaign: `ANALYZED →
ENRICHED`. Non-claims: no `VALUE_EVALUATED`; whether the ayanāṃśas disagree is unmeasured;
`catalog_status` stays `DRAFT` until the native rules.

**Walkthrough (ordinary chapter).** "What was my Jupiter mahādaśā about?" → one chapter: the span
(clipped to the lived portion), `dominant_signal_class` with `signature_class_agreement='unanimous'`,
the convergence counts, `effective_score_source` per window, and `coverage` saying the PD level is
the current antardaśā only. The reader gets the chapter **and** what it was counted from.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Pin the LATERAL predicate pick** (canonical ayanāṃśa + total `ORDER BY`) — §N.7 item 2 | yes |
| 2 | **When the five ayanāṃśas' `signature_class` disagree, surface the split rather than silently resolving it** | yes — stamp `signature_class_agreement`; a split is information |
| 3 | **One spelling for the layer's `as_of` config key.** This writer already reads `ctx.config['as_of_date']`; other briefs in this programme propose `ctx.config['as_of']` | adopt **`as_of_date`** — it exists and is read today; the other briefs cite it rather than inventing a second key |
| 4 | `ka_dasha_kala` declared while `chart_dashas` is read directly: re-label or drop (registry packet) | re-label as the vocabulary edge it is, or drop and keep `ga_dashas` |
| 5 | `catalog_status: DRAFT` → `CURRENT`? | the native's |

---

## §11 — Not verified here

1. Whether the five ayanāṃśas' `signature_class` values actually differ for any signal on this chart
   — unmeasured, and it decides whether the pick defect is active or latent.
2. Whether Postgres in practice returns a stable row for this LATERAL on this data — unmeasured and
   not relied upon: an unordered `LIMIT 1` is a defect regardless of observed stability.
3. The ~247-row and ~9-PD-row figures — the writer's own docstring [A].
4. Whether `ka_kala_darshana`'s rows exist at build time for every window (the COALESCE implies they
   may not) — unmeasured.
5. No database query; no test run.
