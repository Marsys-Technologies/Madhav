---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_TARANGA_ELEVATION_BRIEF
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
asset_or_interface_ids: ["ka_taranga", "the W2 §3 SPLIT ruling (the event_class half is degenerate and to be retired; the domain half is kept)", "SC-1 (month boundaries are already tz-pinned — the good pattern)", "registry packet: the declared-but-unread ka_avadhi edge", "Q6 (the semantics of an unevaluated term in a combination rule)"]
goal_objective: "Stop a missing term from reading as a zero term: the waveform's transit contribution is 0.0 on every canonical-chart row because kala_convergence is empty, and 0.0 flows into an arithmetic mean as if it were a measured absence of transit support — so a chart with no convergence data and a chart with genuinely quiet transits produce the same curve. Make an unevaluated term null with a reason, renormalise explicitly, and retire the degenerate half the W2 ruling already condemned."
source_revision: "9feac52d7 (l3/kala-layer-briefs); cited code identical at a99300bb7 (2026-09-24)"
accepted_upstream_contract: "L1 chart_dashas (vimshottari MD) — read WITHOUT an ayanāṃśa filter, which migration 670's conjunct (a) is this asset's CR-110 double-spine detector for; ka_sangam's kala_convergence incl. E5 episode metadata (is_episode, episode_uuid, episode_children); bo_pratijna grades via brahma_event_ontology; the chart's birth timezone for month-boundary pinning"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_TARANGA_v1_0.md"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/pipeline/orchestrator/writers/ka_taranga.py", "platform/python-sidecar/services/taranga_kernel/kernel.py (SHARED — `compute_activation_curve` is the on-demand interface a live caller imports; `harmonic_mean`/`GRAHA_DOMAINS` are byte-identical extractions guarded by tests/l3/test_taranga_kernel_extraction.py, so any change there is a coordinated packet)", "platform/python-sidecar/services/taranga_service.py", "platform/python-sidecar/tests/l3/test_taranga*.py", "one additive migration on kala_taranga (per-term availability/qualification columns)"]
interface_packet_targets_not_may_touch: ["platform/src/lib/retrieval/registry/layers/L3_kala/query_activation_waveform.ts — Pūrṇa-owned; L3 owns only the sentinel test"]
must_not_touch: ["kala_convergence / ka_sangam (producer; its brief)", "bodha_pratijna, brahma_event_ontology (L2/L0)", "chart_dashas / ga_* (L1)", "platform-mcp/src/tools/kala_views/**", "applied migrations — incl. 396, 670 and 1033–1070", ".github/workflows/deploy.yml", "kala_gochara_windows WHERE generation='v1'", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY"
target_state_campaign: "ANALYZED → ENRICHED at stage 3"
wave: "W4"
shape: single asset, rows (chart × month × scope_kind × scope_id) over 1950-01..2100-12 — 1,812 months per scope
evidence_base: >
  Source read directly on 9feac52d7 [V]; migration 670's ka_taranga contract (a)–(e) and its W2 §3
  SPLIT note, blueprint v5.0 §3.5 row 13 / §4 / §16.2 [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.0 (2026-09-24): first issue; awaiting independent review."
---

# `ka_taranga` elevation brief — a waveform that says which terms it measured

## §0 — The recommendation, in one paragraph

`ka_taranga` computes a monthly activation curve from 1950-01 to 2100-12 per scope, combining three
terms: a daśā-lord domain indicator (`1.0` if the month's vimśottarī MD lord's natural significations
include the scope's domain, else `0.15`), a transit term (the mean `convergence_score` of
`kala_convergence` windows overlapping the month for that domain, with E5 episode occupancy and
per-contract dedup), and a promise term (`bodha_pratijna` grade / 10) — combined as
`harmonic_mean([d,t,p])` when `p > 0`, else the **arithmetic mean of `(d, t)`**
(`ka_taranga.py:329-334`; `taranga_kernel/kernel.py:45-52,:56-70` [V]). Several things about it are
done well: month boundaries are pinned to the **chart's birth timezone** (`_resolve_birth_timezone`
`:80-100`, with the offset recorded in `components` when it falls back to UTC) — the SC-1 pattern
other assets in this layer lack; the transit term dedups by a stable `_window_identity` and computes
episode occupancy from the union of child intervals (`:160-170`, `:225-262`); and the kernel is a
**byte-identical extraction** guarded by its own regression test, so the stored output is unchanged
by the refactor. The defect is what happens when a term is not measured. `kala_convergence` is empty
for the canonical chart, so `t_vals` is `[]`, `t_contrib = 0.0` (`:333`), and that zero flows into
the arithmetic mean exactly as a measured zero would: **a chart with no transit data and a chart with
genuinely no transit support produce the same number**, and the blueprint records
`transit_contribution=0.0` on every canonical-chart row. Recommendation: **`ENRICH_CORRECT`** —
an unevaluated term is `null` with a reason, the combination **renormalises over the terms actually
available** and says so, `components` carries `transit_available`; plus the W2 §3 SPLIT is executed
(the `event_class` half is degenerate — its daśā term takes exactly one value across 48,924 rows,
which migration 670's conjunct (e) already asserts as the reason for retirement), the month-lord
selection is made longest-overlap rather than first-match, and the declared-but-unread `ka_avadhi`
edge is dropped. Decisions: Q6's semantics and the SPLIT (§10).

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 | monthly activation waveform | — |
| Strategy §6.1 **L3-A18** (`:288`) | *"Preserve timeline signal; inspect raw Mahadasha context/ayanamsha and class-specific meaning. Class dasha can degenerate to shared domain behavior and class transit to domain maxima. Use actual Pratijna/convergence/clocks/ontology; **no invented Avadhi dependency**."* W4 | the degeneracy it warns about is exactly what 670(e) measures; the Avadhi edge is the "invented dependency" |
| **Migration 670 (`:1322-1420`)** [V] | the header records the **W2 §3 SPLIT ruling**: *"the `scope_kind='domain'` half is the genuine independent witness and is KEPT — the `scope_kind='event_class'` half is degenerate and is to be retired"*. (a) every month's stamped `dasha_lord` must be the lord `chart_dashas` reports at the **canonical ayanāṃśa**, vimshottari MD — *"the writer reads chart_dashas WITHOUT an ayanamsha filter, so this conjunct is also the CR-110 double-spine detector for this asset"*; (b) interior tiling per `(chart, scope_kind, scope_id)` derived from the group's own endpoints (not a count pin); (b2) endpoint tiling — all scopes of a chart share the same first and last month; (c) every month key is a real month start and `activation ∈ [0,1]` (the table carries **no CHECK** on `activation`); (d) the domain half's `dasha_contribution` is uniquely determined by `(dasha_lord, scope_id)`; (e) the domain half is **not degenerate** — it must take at least two distinct `dasha_contribution` values per chart, *"the event_class half's takes exactly one across 48,924 rows — the reason that half is retired"* — and all scopes of one chart-month must agree on the lord | a strong contract, and the SPLIT is already ruled |
| Blueprint §3.5 row 13 (`:329`), §4 (`:401`), §16.2 (`:911`) | rows 92,412; **`transit_contribution=0.0` on every canonical-chart row**; zero-as-unevaluated; month rounding; Avadhi edge false; *"`null` + reason for the unevaluated term, explicit renormalisation; occupancy-weighted overlap; longest-overlap lord; per-signal dedup; drop the false Avadhi edge or read it; `components` carries `transit_available`"* | this brief |
| Seed (`asset_registry_seed.ts:2445-2461`) | `depends_on: ['ka_avadhi', 'bo_pratijna', 'ka_sangam', 'ga_dashas', 'bg_ghatana']`; the comment records migration 406's correction that *"writer reads kala_convergence directly"* | **`ka_avadhi` is declared and not read** (Strategy `:47`: *"Taranga does not consume Avadhi"*) |
| `taranga_kernel/kernel.py:1-25` | `harmonic_mean` and `GRAHA_DOMAINS` are **verbatim, byte-identical** extractions from the writer, guarded by `tests/l3/test_taranga_kernel_extraction.py`; `compute_activation_curve` is the **new shared on-demand interface** a live caller imports; *"NO writer-side I/O anywhere in this module"* | the kernel is shared — changes are a coordinated packet |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V]
`storage_type: 'postgres_table'`, `target_table: 'kala_taranga'`, chart-scoped `count_sql`,
`scope: 'per_chart'`; `volume_explanation` records 1,812 months × scope cardinality. Rows 92,412
live [A]. `FORMULA_VERSION = "ka_taranga_v1.0"` (`:44`); `_WAVEFORM_START = date(1950,1,1)`,
`_WAVEFORM_END = date(2100,12,1)` (`:46-47`).

### 2.2 The code [V]
- **Idempotency**: `SET LOCAL statement_timeout = 0`; `DELETE FROM kala_taranga WHERE chart_id`
  (`:180`); batched upsert `ON CONFLICT (chart_id, month, scope_kind, scope_id) DO UPDATE`
  (`:57-64`).
- **Timezone (the good pattern)**: `_resolve_birth_timezone` (`:80-100`) prefers
  `birth_params.tz_offset_hours`, falls back to `charts.timezone_id`, and **falls back to UTC only
  with the offset recorded in `components`** so the fallback is visible (E5/RRV-05).
- **Daśā** (`:186-200`): `SELECT lord_graha, start_date AS ds, end_date AS de FROM chart_dashas
  WHERE chart_id AND level_n = 1 AND system_id = 'vimshottari'` — **no ayanāṃśa filter** (670(a)'s
  target). Empty → *"no vimshottari MD rows — run ka_dasha_kala first"* (`:202-204`).
  `_lord_for_month` (`:205-210`) returns the **first** MD row containing the month — a first-match,
  not a longest-overlap, selection, so a month straddling two MDs is attributed to whichever appears
  first in `ORDER BY start_date`.
- **Transit** (`:207-262`): `kala_convergence` rows with a domain and both window bounds; occupancy
  computed from episode children where `is_episode`; `_window_identity` (`:160-170`) dedups by
  `('episode', uuid)` or `('contact', signal_id, mode, peak_date, window_start, window_end)`.
- **Promise** (`:225-262`): `bodha_pratijna` grades joined to `brahma_event_ontology`, at
  `lahiri_chitrapaksha`, savepoint-guarded; `grade/10` per event class and the **mean** per domain.
- **Combination** (`:329-334` domain half; `:360-372` event_class half):
  `d_contrib = 1.0 if domain in lord_domains else 0.15`; `t_contrib = mean(t_vals) if t_vals else
  **0.0**`; `p_contrib = pratijna_domain.get(domain) or 0`; `act = harmonic_mean([d,t,p]) if p > 0
  else (d + t) / 2.0`; clamped and rounded (`:341`). The event_class half uses `d_contrib = 1.0/0.1`
  and `t_contrib = max(all domains' values)` — the degenerate half.
- **`components`** carries `dasha_contribution`, `transit_contribution`, `promise_contribution`,
  `dasha_lord`, `formula_note` — **no availability flag**.

### 2.3 Consumers [V]
| consumer | reads | role |
|---|---|---|
| `query_activation_waveform.ts` | `kala_taranga`; `MAX_LIMIT 50` in drill mode; a peaks mode with `MAX_PEAKS`; `total` disclosed | served `relevance_navigation` |
| `services/taranga_service.py` | the table and `kala_activation`; persists into the **existing** `kala_taranga` table (migration 396) | service |
| `services/taranga_kernel/kernel.py` + `__init__.py` | `compute_activation_curve` — the on-demand interface | shared kernel |
| `source_query_availability.ts`, `tool_name_bridge.ts` | catalog | census |

**Live-path statement.** The waveform is served, and every canonical-chart row carries
`transit_contribution = 0.0`.

### 2.4 Epistemic class
| field | class | authority | note |
|---|---|---|---|
| `dasha_contribution` | indicator over a **doctrine map** (`GRAHA_DOMAINS`) | the kernel | 1.0/0.15 is engineered; the map is uncited; note this is a *different* map from `ka_avadhi`'s `_GRAHA_DOMAINS` (nine grahas, fewer domains each) — two graha→domain tables exist in the layer |
| `transit_contribution` | mean of an engineered producer score | `kala_convergence` | **0.0 when unmeasured** — the defect |
| `promise_contribution` | L2 grade / 10 | `bodha_pratijna` | `0` when absent, which then selects the arithmetic branch |
| `activation` | `INTERPRETIVE_INFERENCE` — a combination of three engineered terms | the kernel | no CHECK on the column (670(c) guards it) |
| `dasha_lord` | inherited from L1 | `chart_dashas` | **read without an ayanāṃśa filter** |
| month boundaries | tz-pinned to the chart | this writer | the layer's best SC-1 practice |

### 2.5 Ladders
`PLAN_REVIEWED`; 92,412 rows [A]. t3: no event.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | For the canonical chart `kala_convergence` is empty, so for every month and every domain `t_vals = []` and `t_contrib = 0.0` (`:333`). With no pratijñā grade for that domain the combination is `(d + 0.0) / 2` — the curve is **exactly half the daśā indicator**, and it is indistinguishable from the curve a chart would get if its transits had been measured and found to contribute nothing. Nothing on the row says the term was never evaluated: `components.transit_contribution` reads `0.0` in both cases |
| Evidence | `ka_taranga.py:329-334,:360-372`; `taranga_kernel/kernel.py:45-52,:56-70`; blueprint §3.5 row 13 (`transit_contribution=0.0` on every canonical row) [A] |
| Expected contract | §N.7 item 6 (an honest null beats an invented value — and a zero that means "unmeasured" is an invented measurement); §N.8 (a reported term must have a detector that could report otherwise); F06 (`unavailable` ≠ a measured value); B2 (`completeness_state` per term) |
| Defect class | **unevaluated read as evaluated** (a missing term contributing as a measured zero) + **undeclared degeneracy** (the event_class half, already ruled for retirement) + **first-match lord selection** at month boundaries + **declared-but-unread edge** |
| Impact | a served waveform's shape is set by the daśā indicator alone while presenting as a three-term combination; two epistemically different situations produce identical curves; a month straddling two mahādaśās is attributed to the earlier one with no rule stated |
| Non-claim | no claim that the canonical chart's transits *would* contribute if measured (that is Saṅgam's data gap, not this writer's); no claim about the doctrinal correctness of 1.0/0.15 or of either graha→domain map; the 0.0-everywhere observation is the blueprint's [A], not re-measured |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q07 (trajectory over an interval); Q-K08/K04 as blueprint cross-references.
2. **An unevaluated term is null, and the combination says so (Q6's semantics).** `t_contrib` is
   `None` when `t_vals` is empty, with `transit_available=false` and
   `reason='no_convergence_rows_for_domain'` in `components`; the combination **renormalises over
   the terms actually available** and records which ones they were
   (`terms_used: ['dasha']` / `['dasha','transit']` / all three). The arithmetic-vs-harmonic branch
   becomes explicit: harmonic over the available positive terms, arithmetic only where the rule says
   so, and the branch taken is stamped. **This changes stored values**, so it is a versioned change:
   `FORMULA_VERSION` bumps and the change is declared (§5).
3. **Execute the W2 §3 SPLIT.** The `scope_kind='event_class'` half is retired — 670(e) already
   asserts its degeneracy as the reason (*"takes exactly one value across 48,924 rows"*). Retirement
   is `RETIRE_AFTER_MIGRATION`: one generation emitting it with
   `completeness_state='inapplicable'`, `reason='degenerate_half_retired'`, then removal; the
   registry's `count_sql` and volume note follow.
4. **Longest-overlap lord.** `_lord_for_month` selects the MD with the **greatest overlap** with the
   month rather than the first containing row, and the row records `lord_overlap_days` so a boundary
   month is auditable. 670(a) and (e)'s "all scopes of one chart-month agree on the lord" are
   preserved.
5. **Ayanāṃśa declared.** The daśā read gains the canonical ayanāṃśa filter — which is what 670(a)
   already requires the *result* to satisfy, so this makes the writer state what the contract
   enforces (CR-110's lesson applied here rather than left to the detector).
6. **Drop the unread edge.** `ka_avadhi` is removed from `depends_on` by registry packet
   (Strategy `:47` and the blueprint both record it as false); `ga_dashas`, `ka_sangam`,
   `bo_pratijna`, `bg_ghatana` stay.
7. **Coverage (B5).** Per build: `{requested_horizon: [1950-01, 2100-12], completed_horizon,
   resolution: 'month', partitions_searched: [scope ids], exclusions: [{scope, reason}],
   unsearched_regions: [], completion_detector: 'contiguous_month_run_per_scope'}` — which is
   exactly what 670(b)/(b2) check, now also served.
8. **Qualification (B2, B4).** `epistemic_class='INTERPRETIVE_INFERENCE'` on `activation`;
   `operator_role='computation'`; `tier_basis='relative_uncalibrated'`; `comparable_with='self'`
   within a scope, `different_convention` across `scope_kind`; **`independence_group`**: the daśā
   term and the transit term are **not** independent of the layer's other assets — the daśā term
   shares `chart_dashas` with Avadhi/Kalasutra/Jivana and the transit term is Saṅgam's own score —
   so the row declares the group rather than letting a consumer treat the waveform as a fourth
   witness.
9. **The two graha→domain maps.** `taranga_kernel.GRAHA_DOMAINS` and `ka_avadhi._GRAHA_DOMAINS` are
   different tables for the same concept (DP01). This brief does **not** unify them unilaterally —
   it raises the divergence, notes that Avadhi's is additionally out of the ontology's vocabulary
   (that brief's F4), and asks for one ruling (§10.5).
10. **Old vs new.** Positive: a chart with convergence rows → three terms, `terms_used` all three.
    Negative: no vimśottarī MD → the existing honest refusal. Boundary: a month straddling two MDs →
    the longest-overlap lord with `lord_overlap_days`. Missing: no convergence rows for a domain →
    `transit_contribution=null`, `transit_available=false`, renormalised over two terms — **a
    different number from today's**. Duplicated: one contract appearing as both an episode and its
    children → counted once (`_window_identity`, preserved).
11. **Simpler baseline.** Today's curve.
12. **Ablation.** Compute the canonical chart's curve under today's rule and the renormalised rule:
    the shapes differ wherever the transit term is unmeasured, and the served waveform stops
    asserting a measured zero. If Saṅgam's data later lands, the same fixture shows the third term
    entering — which is the test that the term was genuinely absent, not merely small.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: the tz-pinned month boundaries and the recorded UTC fallback; `_window_identity`
  dedup and episode occupancy; the byte-identical kernel extraction and its regression guard; the
  honest refusal on no MD rows; the upsert key.
- `ENRICH_CORRECT`: null-with-reason terms and explicit renormalisation; longest-overlap lord; the
  ayanāṃśa filter; coverage.
- `RETIRE_AFTER_MIGRATION`: the `event_class` half (one labelled generation).
- **Shared-kernel fence**: `taranga_kernel/kernel.py` is imported by `taranga_service.py` and by the
  on-demand interface; `harmonic_mean`/`GRAHA_DOMAINS` are byte-identical extractions with a
  regression test (`test_taranga_kernel_extraction.py`) — **any change there is a coordinated packet
  and must update that test deliberately, not incidentally**.
- **Versioned change**: §4.2 changes stored values, so `FORMULA_VERSION` bumps; 670(b)/(b2)/(d)/(e)
  must still pass after the rebuild, and (e)'s "at least two distinct `dasha_contribution` values"
  is unaffected (the daśā term is untouched).
- **Migration**: one additive migration (per-term availability/qualification columns). No FK.
- Rollback: the additive columns are nullable; the combination change is behind the version bump.

---

## §6 — Lenses A–J *(appendix)*

| lens | answer |
|---|---|
| A | L3 rows; a three-term engineered combination over L1 clocks, L2 windows and L2 promises; `ENRICH_CORRECT` (+ one retirement) |
| B | five declared edges; **`ka_avadhi` unread**; `kala_convergence` read directly (migration 406 corrected the seed comment); fan-out: one served surface, one service, one shared kernel |
| C | invariants: 670 (a)–(e); an unevaluated term is null and never 0.0; `terms_used` matches the arithmetic actually performed; all scopes of a chart-month agree on the lord; the kernel stays byte-identical unless deliberately versioned |
| D | the transit term's data gap is Saṅgam's |
| E | served ×1; the on-demand kernel is the interesting consumer (it must adopt the same null semantics) |
| F | `transit_available`, `terms_used`, `lord_overlap_days`, coverage machine-readable |
| G | 1,812 months × scopes — the largest row count in the layer; batched; unmeasured |
| H | idempotent; upsert keyed on the natural key |
| I | files in `may_touch`; one additive migration; W4; a coordinated kernel packet |
| J | this brief; §7; the review |

---

## §7 — Proof matrix

Columns: **verdict tier** F24; **scope** `[U]` unit, `[I]` DB fixture, `[S]` served.

| proof | verdict tier | scope | fixture / command | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|---|
| Positive | COMPUTATIONAL_CORRECTNESS | I | a chart with convergence rows and pratijñā grades | three terms present; `terms_used` = all three; 670 (a)–(e) TRUE | the contract | any conjunct FALSE | integrity SQL |
| Negative | COMPUTATIONAL_CORRECTNESS | I | no vimśottarī MD rows | the existing honest refusal | no write | rows written | writer test |
| **Unevaluated term** | COMPUTATIONAL_CORRECTNESS | I | a domain with **no** convergence rows | `transit_contribution = null`, `transit_available = false`, `reason` set; `activation` renormalised over the remaining terms; `terms_used = ['dasha']` | a missing term is never 0.0 | `0.0` appears (today) | writer test |
| Relevant influence | COMPUTATIONAL_CORRECTNESS | I | add one convergence window overlapping one month for one domain | that month/domain's `activation` changes; all others byte-identical | isolation | a second scope moves | writer test |
| Irrelevant control | COMPUTATIONAL_CORRECTNESS | I | reorder the convergence rows | identical output (dedup is identity-based, not order-based) | order-invariant | differs | writer test |
| Duplication | COMPUTATIONAL_CORRECTNESS | I | one contract present as an episode **and** as its children | counted once | `_window_identity` | counted twice | writer test |
| Boundary | COMPUTATIONAL_CORRECTNESS | I | a month straddling two mahādaśās | the **longest-overlap** lord, `lord_overlap_days` recorded; all scopes of that month agree (670(e)) | deterministic boundary rule | first-match (today) | writer test |
| Context | COMPUTATIONAL_CORRECTNESS | I | a chart whose `timezone_id` is missing | the UTC fallback **with the offset recorded in `components`** (preserved behaviour) | the fallback is visible | silent UTC | writer test |
| Degeneracy | COMPUTATIONAL_CORRECTNESS | I | the `event_class` half during its retirement generation | `completeness_state='inapplicable'`, `reason='degenerate_half_retired'`; 670(e)'s domain-half assertion still TRUE | the SPLIT executed | the half is silently dropped or silently kept | integrity SQL |
| Delivery | COMPUTATIONAL_CORRECTNESS | S | sentinel `transit_available=false` on one month | reaches `query_activation_waveform`'s envelope in both drill and peaks modes | survives | absent | route test |
| Revision | COMPUTATIONAL_CORRECTNESS | I | Saṅgam's convergence rows land | the transit term enters; `terms_used` grows; the curve changes | the term was absent, not small | unchanged | writer test |
| Value | EXPLANATORY_DISCRIMINATIVE_VALUE | S | frozen Q07 question | the answer distinguishes "quiet" from "unmeasured"; the baseline cannot | — | no distinction | baseline record |
| Evaluation | — | — | `not_applicable` (a waveform is not an outcome claim) | — | — | — | — |

Binding: **OFFERS** B1 (`precision_regime='date_grain'` at month resolution, `time_basis` per the
tz-pinned boundary), B2 (`completeness_state` **per term**, `epistemic_class`, `operator_role`,
`tier_basis`, `comparable_with`), B4 (`independence_group` — the waveform is not a fourth
independent witness), B5 (`coverage`). **DEMANDS** nothing new; the transit term's data is Saṅgam's.
**Asset-local:** `transit_available`, `terms_used`, `lord_overlap_days`, `formula_note`,
`components`.

---

## §8 — Prioritization

(1) the null-with-reason term and explicit renormalisation (a served curve currently asserts a
measured zero) → (2) the SPLIT retirement → (3) longest-overlap lord → (4) the ayanāṃśa filter →
(5) coverage + B4 → (6) drop the unread edge → (7) the two-map divergence to a ruling. W4.

---

## §9 — Disposition and target state

`ENRICH_CORRECT` (+ `RETIRE_AFTER_MIGRATION` for the degenerate half). Data-plane:
`PRODUCER_READY`; `DATA_ACCEPTED` after the versioned rebuild passes 670 (a)–(e);
`CONSUMER_INTEGRATED` when the served waveform carries `transit_available`. Campaign: `ANALYZED →
ENRICHED`. Non-claims: no `VALUE_EVALUATED`; the transit data gap is upstream; the doctrine maps are
not adjudicated here.

**Walkthrough (ordinary month).** "How active is my career line in March 2027?" → one row:
`activation` computed from the daśā indicator and the promise grade, `transit_contribution=null`
with `transit_available=false` and a reason, `terms_used=['dasha','promise']`, `dasha_lord` with its
overlap days. The reader learns the level **and** that one of the three inputs was never measured —
rather than being told it measured zero.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Q6: an unevaluated term is `null` and the combination renormalises over available terms, with `terms_used` stamped** — this changes stored values and bumps `FORMULA_VERSION` | yes; the alternative (keep 0.0) makes the waveform assert a measurement it never made |
| 2 | **Execute the W2 §3 SPLIT: retire the `event_class` half after one labelled generation** | yes — 670(e) already records the degeneracy |
| 3 | Longest-overlap lord selection with `lord_overlap_days` recorded | yes |
| 4 | Drop the declared-but-unread `ka_avadhi` edge (registry packet) | yes |
| 5 | **Two graha→domain maps exist in the layer** (`taranga_kernel.GRAHA_DOMAINS` and `ka_avadhi._GRAHA_DOMAINS`), and Avadhi's is additionally outside the ontology's vocabulary | one ruling on the doctrine map, not two unilateral fixes |

---

## §11 — Not verified here

1. The 92,412 row count and the `transit_contribution=0.0` observation — blueprint [A], not
   re-measured.
2. Whether `compute_activation_curve`'s live on-demand caller exists and what it would do with a
   null term — it must adopt the same semantics; not traced here.
3. Build duration for 1,812 months × scopes — unmeasured.
4. Whether the `event_class` half has any consumer that would break on retirement.
5. No database query; no test run.
