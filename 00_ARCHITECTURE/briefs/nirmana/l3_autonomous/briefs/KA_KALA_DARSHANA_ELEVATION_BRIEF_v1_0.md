---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_KALA_DARSHANA_ELEVATION_BRIEF
version: "1.0"
status: DRAFT_FOR_INDEPENDENT_REVIEW
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md
synergy_binding_version: "2.2"  # §B1 ruled name is precision_regime (not claim_grain, which was v1.0); values {instant_grain, date_grain}; day_grade aliases date_grain until Sangam D-7 successor condition, NOT for a count of generations
asset_or_interface_ids: ["ka_kala_darshana", "SC-5 (the LIMIT 750 intake cap → coverage)", "B4 (the max-over-obstructions suppression depends on Vighnakara's independence marking — a DEMAND)", "SC-6 (this asset IS the layer's verdict producer; B6 says one producer per verdict)"]
goal_objective: "Make the display layer's verdict auditable: it multiplies a producer's convergence score by one minus the LARGEST obstruction override and labels the result, but it takes the max over rows whose independence is unmarked (so one mechanism seen three ways suppresses as hard as three independent ones), it reads only the top 750 convergence windows with no record of the rest, and its labels are threshold restatements whose thresholds live nowhere but the code."
source_revision: "9feac52d7 (l3/kala-layer-briefs); cited code identical at fb46b258f (2026-09-24)"
accepted_upstream_contract: "ka_sangam's kala_convergence (top-750 by convergence_score; mode ∈ {A,B,C,D}); ka_vighnakara's kala_obstruction (severity, override_score, grouped by convergence_id) — whose independence_group this asset DEMANDS"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_KALA_DARSHANA_v1_0.md"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/pipeline/orchestrator/writers/ka_kala_darshana.py", "platform/python-sidecar/tests/l3/test_ka_kala_darshana*.py", "one additive migration on kala_darshana (coverage/qualification columns and the date CHECK conjunct (f) currently has to stand in for)"]
interface_packet_targets_not_may_touch: ["platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_view.ts and register_d5_fanout.ts — Pūrṇa-owned", "platform-mcp/src/tools/kala_views/now.ts, tools/retrieval/kala_temporal.ts — Pūrṇa-owned; L3 owns only the sentinel test"]
must_not_touch: ["kala_convergence / ka_sangam and kala_obstruction / ka_vighnakara (producers; their briefs)", "pipeline/orchestrator/writers/ka_bhavishya_lekha.py, ka_jivana_parva.py (readers; their briefs)", "services/ka_tulana/** (reads kala_darshana; its brief)", "platform-mcp/src/tools/kala_views/**", "applied migrations — incl. 670 and 1033–1070", ".github/workflows/deploy.yml", "kala_gochara_windows WHERE generation='v1'", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY"
target_state_campaign: "ANALYZED → ENRICHED at stage 3"
wave: "W4"
shape: single asset, one row per consumed convergence window (artifact; catalog_status DRAFT)
evidence_base: >
  Source read directly on 9feac52d7 [V]; migration 670's ka_kala_darshana contract (a)–(f),
  blueprint v5.0, Lane D/E [A]; no database query. Claims marked [R] elsewhere in this programme are
  a reviewer's verification and are re-checkable — this brief marks its own reads [V].
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.0 (2026-09-24): first issue; awaiting independent review."
---

# `ka_kala_darshana` elevation brief — a verdict that can be audited

## §0 — The recommendation, in one paragraph

`ka_kala_darshana` is the layer's **verdict producer**: for each of the top 750 convergence windows
it computes `effective_score = convergence_score × (1 − max(override_score))` over that window's
obstructions, assigns a `net_label` from a threshold ladder, and builds a display narrative. Two of
its known defects have already been fixed with unusual care, and both fixes are worth preserving as
written: the **M9 fix** replaced `conv_score or 0.5` — a falsy-coalesce that silently rewrote a
**computed zero** into a middling favourable value — with an explicit `is None` check that **logs a
warning** and states in the code that the path *"had never fired as of L3-W3 (793 zeros, 0 NULLs
measured)"*; and the **F-DARSH-2 fix** replaced a two-way `'daśā-aligned' if mode == 'A' else
'independent sweep'` branch over Saṅgam's real four-value enum with honest per-mode naming, after
measuring that the top-750 intake is *100 % Mode C* — so every served row had carried the wrong mode
description. What remains is the verdict's own auditability. (1) The suppression takes **`max`
over obstructions** (`_compute_effective_score`, *"Multiple obstructions: use max override (not
additive) to avoid collapse"*) — a defensible rule, but it is applied to rows whose
**independence is unmarked**: Vighnakara emits five detectors flat, three of which share one
ephemeris read, so "the largest of three" may be the largest of one mechanism seen three ways, and
nothing in either table says which. (2) The intake is `ORDER BY convergence_score DESC NULLS LAST
LIMIT 750` with **no record of what was not consumed** — and because the ordering is by score, the
windows dropped are the low-scoring ones, which is exactly where an obstruction would matter most
relative to its base. (3) The label thresholds (`0.70 / 0.45 / 0.20`, plus severity overrides) exist
only in `_compute_net_label`; migration 670's conjunct (d) pins the label as a restatement of them,
which is right, but no served row carries the ladder it was graded against. Recommendation:
**`QUALIFY_LIMIT` + `ENRICH_CORRECT`** — the cap becomes coverage; the suppression **DEMANDS**
Vighnakara's `independence_group` and takes its max **per group**; the threshold ladder is stamped
on the row as `label_basis`; and the verdict declares itself the single producer B6 requires.
Decisions: §10.

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 | display-ready temporal view | — |
| Strategy §3 *Comparison/election* (`:97`) | *"no universal ranking or hidden hard cap"* | the 750 cap is hidden |
| **Migration 670 (`:682-795`)** [V] | (a) accretion detector — `kala_darshana` has **only a surrogate id PK**; (b) §N.5 L3-internal authority: *"the display row NEVER restates an upstream computed value"* — peak/window/score are copied, not recomputed; (c) §N.7 item 6 — **the direct F-DARSH-1 detector**: `effective_score` must equal its definition (the M9 defect's machine form); (d) §N.7 item 1 — `net_label` is a restatement of `(effective_score, obstruction severities)`; (e) §N.6 item 1 + §N.7 item 1 — the served `obstruction_summary` must mirror the actual obstruction rows; (f) **range guard**: *"kala_darshana carries no CHECK on its dates at all, so nothing but this …"* | a strong contract that already pins the arithmetic and the label; what it cannot see is what was never consumed |
| Seed (`asset_registry_seed.ts:2373-2388`) | `target_table: 'kala_darshana'`, chart-scoped `count_sql`, `depends_on: ['ka_sangam', 'ka_vighnakara', 'ka_kalasutra']`, **`asset_kind: 'artifact'`, `catalog_status: 'DRAFT'`** | `ka_kalasutra` is declared — whether it is read is §11.2 |
| Blueprint SC-5 (`:284`) | names `ka_kala_darshana.py:31` `LIMIT 750` in the caps list | this brief's §4.2 |
| `writer.py` comments (M9, F-DARSH-2) | *"793 rows with convergence_score = 0 and zero NULLs"*; *"ka_sangam's top-750 intake is 100% Mode C, so every served row carried the wrong mode description"* | both fixes preserved verbatim (§5) |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V]
`storage_type: 'postgres_table'`, `target_table: 'kala_darshana'`, `scope: 'per_chart'`,
`asset_kind: 'artifact'`, `catalog_status: 'DRAFT'`.

### 2.2 The code [V]
- **Idempotency**: `SET LOCAL statement_timeout = 0`; `DELETE FROM kala_darshana WHERE chart_id`
  (`:19`) **before** the candidate is built.
- **Intake** (`:22-34`): `SELECT convergence_id, signal_id, mode, peak_date, window_start,
  window_end, convergence_score, confidence_label, orb_strength, rarity_years FROM kala_convergence
  WHERE chart_id = %s ORDER BY convergence_score DESC NULLS LAST **LIMIT 750**`. Empty →
  *"No convergence windows — run ka_sangam first"* (`:36`).
- **Obstructions**: grouped by `convergence_id` into `obs_by_conv`.
- **Effective score** (`_compute_effective_score` `:146-157`): no obstructions → the clamped
  convergence score; else `convergence_score × (1 − max(override_score))`, clamped `[0,1]`, with the
  rule stated: *"Multiple obstructions: use max override (not additive) to avoid collapse"*.
- **The M9 guard** (`:84-97`): `if conv_score is None:` → a `logger.warning` naming the
  convergence id and the measurement (*"793 zeros, 0 NULLs"*), then the 0.5 substitution —
  **loud, not silent**, and explicitly *"still an invention"*.
- **Label** (`_compute_net_label` `:159-179`): `obstructed_severe` if any severity is `severe`;
  `obstructed` if any `moderate` and `effective < 0.4`; else `auspicious_strong ≥ 0.70`,
  `auspicious_moderate ≥ 0.45`, `auspicious_speculative ≥ 0.20`; else `obstructed` if any
  obstruction; else `neutral`.
- **Narrative** (`_build_narrative` `:181+`): the F-DARSH-2 per-mode naming with an unrecognised
  mode *"naming itself honestly rather than falling into whichever label the old binary happened to
  assign"*; `conf_str = conf_label or 'speculative'` — a fallback worth checking (§4.6).
- **Write** (`:133-141`): `executemany` INSERT of
  `(chart_id, convergence_id, signal_id, effective_score, net_label, peak_date, window_start,
  window_end, obstruction_summary, narrative, source_citation)`;
  `source_citation = f"ka_kala_darshana:v1.0:conv={conv_id}"`.

### 2.3 Consumers [V]
| consumer | reads | role |
|---|---|---|
| `writers/ka_bhavishya_lekha.py` | `kala_darshana` JOIN `kala_convergence`, future 5 years, `net_label NOT IN ('obstructed_severe')`, `ORDER BY effective_score DESC, peak_date, convergence_id LIMIT 100` | the projection layer — **this verdict decides what is projected** |
| `writers/ka_jivana_parva.py` | `COALESCE(kd.effective_score, kc.convergence_score)` per window | the life-arc layer |
| `services/ka_tulana/{__init__,ranker}.py` | named in the comparison kernel's surface | comparison |
| `query_temporal_view.ts`; `register_d5_fanout.ts`; `now.ts`; `kala_temporal.ts` | served | served |
| `kala_derivation_completeness_guard.py` | the table | guard |

**Live-path statement.** This verdict is the gate on the projection layer (`obstructed_severe`
excludes a window from `kala_bhavishya` entirely) and an input to the life arc. The cap, the
unmarked-independence max and the unstamped ladder are live on all of it.

### 2.4 Epistemic class
| field | class | authority | note |
|---|---|---|---|
| `peak_date`, `window_start/end`, `signal_id` | inherited, **copied verbatim** | `kala_convergence` | 670(b) enforces; correct |
| `effective_score` | `INTERPRETIVE_INFERENCE` — a suppression of an engineered score by an engineered override | this writer | 670(c) pins the arithmetic; the **inputs' independence** is unmarked |
| `net_label` | restatement of `(effective_score, severities)` | this writer | 670(d) pins it; the ladder is not served |
| `obstruction_summary` | mirror of the obstruction rows | 670(e) | correct |
| `narrative` | deterministic template over the above | this writer | the F-DARSH-2 fix made the mode naming honest |
| the 0.5 substitution | an **invention**, logged | this writer | never fired as of L3-W3; kept loud |

### 2.5 Ladders
`PLAN_REVIEWED`; `catalog_status: DRAFT`. t3: no event.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | A window drawing three obstructions from Vighnakara — a malefic transit, a gaṇḍānta and a combustion, **all three computed from one ephemeris read at one instant** — is suppressed by `1 − max(override)`, the same as a window drawing one. That is the intended rule, and it is defensible *if* the three are independent; nothing in either table says whether they are, so the verdict cannot distinguish "the strongest of three independent oppositions" from "one mechanism, three views". Meanwhile the windows the verdict never sees are the **751st and beyond by score** — precisely the low-base windows where a given override changes the label most — and no row or coverage object records that they exist |
| Evidence | `ka_kala_darshana.py:22-34` (`LIMIT 750`), `:146-157` (`max(override_score)`), `:159-179` (the ladder); `ka_vighnakara.py` emits five detectors flat with no independence field [V] |
| Expected contract | B4 (`independence_group` on anything a verdict aggregates); SC-5/B5 (every cap disclosed); B6 (one producer per verdict — and the producer states its basis); §N.7 item 1 (a label restates a stated ladder); Strategy §3 (*no hidden hard cap*) |
| Defect class | **uncountable inputs** (a max over unmarked-independence rows) + **undisclosed cap** + **unstamped grading ladder** |
| Impact | the projection layer's gate (`obstructed_severe`) and the life arc both inherit a suppression whose basis cannot be audited; a reader cannot tell why a window is `auspicious_moderate` rather than `_strong` without reading the writer |
| Non-claim | no claim that `max` is the wrong rule — it is a reasonable one and this brief does not propose changing it, only making its inputs countable; no claim that any chart exceeds 750 windows (unmeasured); the 793-zeros and 100 %-Mode-C figures are the writer's own recorded measurements [A] |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q04 (activity coexisting with strain) at the verdict layer; Q02's "which window"
   half via its consumers. Not Q01/Q03.
2. **The cap → coverage (SC-5/B5).** `coverage = {requested_horizon: the chart's convergence span,
   completed_horizon, resolution: 'convergence_window', partitions_searched: ['top_750_by_score'],
   exclusions: [{reason: 'below_intake_cap', dropped: n, min_score_consumed: x}],
   unsearched_regions: [], completion_detector: 'all_convergence_windows_consumed_or_capped'}` —
   `min_score_consumed` matters because the cap is score-ordered, so a reader can see exactly what
   band was cut.
3. **The suppression takes its max per independence group (B4 DEMAND).** `effective_score =
   convergence_score × (1 − max over GROUPS of (max override within the group))` — which is
   identical to today's number whenever the obstructions are independent, and strictly less
   suppressive when they are not. This **requires** `ka_vighnakara` to emit `independence_group`
   (that brief's §4.3 offer); until it does, the row carries
   `suppression_basis='ungrouped_max'` and `completeness_state='unqualified'` on the suppression —
   honest, and unchanged in value.
4. **The ladder stamped.** `label_basis = {thresholds: [0.70, 0.45, 0.20], severity_overrides:
   ['severe→obstructed_severe', 'moderate∧<0.4→obstructed'], formula_version}` on every row, so
   670(d)'s restatement is auditable from the row rather than from the source.
5. **B6: one producer, declared.** This asset **is** the layer's verdict producer for a convergence
   window; the row says so (`verdict_producer='ka_kala_darshana'`, `verdict_version`), so a second
   surface computing a net label is detectable as a rival rather than discovered later.
6. **The `confidence_label` fallback.** `conf_str = conf_label or 'speculative'` (`:186`) is the same
   falsy-coalesce shape the M9 fix removed from the score — on a text field it is less dangerous, but
   an **absent** label and a label that *is* `'speculative'` read identically in the narrative. Make
   it `None`-checked and render *"confidence not stated"* vs *"speculative"*. (Saṅgam is retiring
   `confidence_label` altogether — amendment 9 — so this is a one-generation fix, coordinated.)
7. **Qualification (B2).** `epistemic_class` per §2.4; `operator_role='interpretation'` on the label
   and `'computation'` on the score (F12's vocabulary — not "verdict", which is not a role);
   `tier_basis='relative_uncalibrated'`; `comparable_with='self'` within a chart,
   `different_convention` across `mode` (Saṅgam's modes are not one scale);
   `completeness_state='applied'`, `'unqualified'` on the suppression until §4.3's DEMAND lands.
8. **Old vs new.** Positive: a window with two independent obstructions → the same number, now with
   `suppression_basis='grouped_max'` and coverage. Negative: no convergence windows → the existing
   refusal. Boundary: a chart with 751 windows → 750 consumed, `dropped: 1`, `min_score_consumed`
   stated. Missing: `convergence_score IS NULL` → the existing **loud** 0.5 substitution, preserved
   exactly. Duplicated: three transit-derived obstructions on one window → **one** group, a strictly
   higher `effective_score` than today's, and the change is visible in `suppression_basis`.
9. **Simpler baseline.** Today's rows.
10. **Ablation.** Recompute the canonical chart's verdicts with grouped vs ungrouped max: the set of
    windows whose `net_label` changes is the measured cost of the unmarked independence. If it is
    empty, the grouping is decorative *for this chart* and the brief says so — but the projection
    gate makes even a single label change material.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`, and this is the heart of it: **the M9 guard exactly as written** — the `is None` check,
  the warning, and the comment recording that the path has never fired; and **the F-DARSH-2 per-mode
  naming** including its honest handling of an unrecognised mode. Both are §N.7-item-6 exemplars and
  neither may be "simplified". Also: 670(b)'s verbatim copying; the `max`-not-additive rule; the
  honest empty on no convergence windows.
- `ENRICH_CORRECT`: grouped suppression (value-identical when independent); the `None`-checked
  confidence rendering.
- `QUALIFY_LIMIT`: coverage; `label_basis`; `suppression_basis`; B2 stamps.
- **DEMAND**: `ka_vighnakara.independence_group` — without it §4.3 stays `unqualified`.
- **Migration**: one additive migration on `kala_darshana`; 670(f) notes the table has **no date
  CHECK at all**, so the same migration adds `CHECK (window_end >= window_start)` and a
  `peak_date BETWEEN window_start AND window_end` guard, which moves that conjunct's job into the
  DDL where it belongs.
- Rollback: additive columns; the grouped max reduces to today's number when every row is its own
  group.

---

## §6 — Lenses A–J *(appendix)*

| lens | answer |
|---|---|
| A | L3 artifact rows; a suppression and a labelling over two producers' engineered scores; `QUALIFY_LIMIT + ENRICH_CORRECT` |
| B | three declared edges; `ka_kalasutra` declared — read status §11.2; fan-out: the projection layer, the life arc, four served surfaces |
| C | invariants: 670 (a)–(f); the label restates the **stamped** ladder; the suppression's max is per group; upstream values copied verbatim |
| D | the top-750 cut is the only data limit |
| E | `ka_bhavishya_lekha` is the load-bearing consumer — `obstructed_severe` is a gate |
| F | coverage, `label_basis`, `suppression_basis`, `verdict_producer` machine-readable |
| G | one intake query + one obstruction query; cheap |
| H | idempotent; delete-then-insert (ordering per §11.3) |
| I | files in `may_touch`; one additive migration incl. the missing date CHECKs; W4 |
| J | this brief; §7; the review |

---

## §7 — Proof matrix

Columns: **verdict tier** F24; **scope** `[U]` unit, `[I]` DB fixture, `[S]` served.

| proof | verdict tier | scope | fixture / command | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|---|
| Positive | COMPUTATIONAL_CORRECTNESS | I | a window with two independent obstructions | the same `effective_score` as today; `suppression_basis='grouped_max'`; coverage; 670 (a)–(f) TRUE | the contract | any conjunct FALSE | integrity SQL |
| Negative | COMPUTATIONAL_CORRECTNESS | I | no convergence windows | the existing honest refusal | no write | rows written | writer test |
| **M9 regression** | COMPUTATIONAL_CORRECTNESS | I | `convergence_score = 0` (a computed zero) | `effective_score` reflects **zero**, not 0.5; no warning logged | the M9 fix | 0.5 appears (the pre-fix defect) | writer test |
| **M9 guard** | COMPUTATIONAL_CORRECTNESS | I | `convergence_score IS NULL` | 0.5 substituted **and a warning logged naming the convergence id** | the invention stays loud | silent substitution | writer test (assert on the log) |
| Relevant influence | COMPUTATIONAL_CORRECTNESS | I | raise one obstruction's `override_score` | that window's `effective_score` falls; others unchanged | isolation | a second window moves | writer test |
| Irrelevant control | COMPUTATIONAL_CORRECTNESS | I | reorder the obstruction rows for one window | identical `effective_score` and label | `max` is order-free | differs | writer test |
| **Duplication** | COMPUTATIONAL_CORRECTNESS | I | three transit-derived obstructions in **one** `independence_group` | one group's max applied; `effective_score` strictly higher than the ungrouped value; `suppression_basis='grouped_max'` | B4 | the three suppress as three | writer test (needs Vighnakara's DEMAND) |
| Context | COMPUTATIONAL_CORRECTNESS | I | `confidence_label IS NULL` | the narrative says *"confidence not stated"*, distinct from `'speculative'` | absent ≠ speculative | the two read identically (today) | writer test |
| Boundary | COMPUTATIONAL_CORRECTNESS | I | 751 convergence windows | 750 consumed; `dropped: 1`; `min_score_consumed` stated; the label ladder unchanged | the cap disclosed | a silent 750 | writer test |
| Label ladder | COMPUTATIONAL_CORRECTNESS | I | `effective_score` at 0.70, 0.4499, 0.20 exactly | `auspicious_strong` / `auspicious_speculative` / `auspicious_speculative`; `label_basis` stamped and matching | 670(d) | the served label disagrees with the stamped ladder | integrity SQL |
| Delivery | COMPUTATIONAL_CORRECTNESS | S | sentinel `suppression_basis='ungrouped_max'` on one row | reaches `query_temporal_view`'s envelope **and** `kala_bhavishya`'s intake | survives the gate | absent | route + writer test |
| Revision | COMPUTATIONAL_CORRECTNESS | I | Vighnakara rebuilds | rows replaced; 670(e) TRUE | mirror maintained | stale summary | integrity SQL |
| Value | EXPLANATORY_DISCRIMINATIVE_VALUE | S | frozen Q04 question | the verdict states its ladder and whether its suppression was grouped; the baseline gives a label | — | no distinction | baseline record |
| Evaluation | — | — | `not_applicable` — the verdict is a display judgement, not an outcome prediction (the projection layer issues those) | — | — | — | — |

Binding: **OFFERS** B2 (`epistemic_class`, `completeness_state`, `operator_role`, `tier_basis`,
`comparable_with`), B5 (`coverage`), B6 (the declared single verdict producer). **DEMANDS** B4 —
`ka_vighnakara.independence_group`, without which the suppression stays `unqualified`. B1: the row
carries `peak_date` and the window bounds **copied** from the producer; their grain and inclusivity
are the producer's and are declared as inherited. B3: `window_ref` inherited from
`kala_convergence`, not minted here (one window, one identity).

---

## §8 — Prioritization

(1) the grouped suppression + its DEMAND (the verdict gates the projection layer) → (2) the ladder
stamped → (3) the cap → coverage → (4) the confidence-label rendering → (5) the missing date CHECKs.
W4.

---

## §9 — Disposition and target state

`QUALIFY_LIMIT` + `ENRICH_CORRECT`. Data-plane: `PRODUCER_READY`; `CONSUMER_INTEGRATED` when the
served view and the projection intake carry `suppression_basis` and `label_basis`. Campaign:
`ANALYZED → ENRICHED`. Non-claims: no `VALUE_EVALUATED`; the `max` rule is not re-litigated here;
`catalog_status` stays `DRAFT` until the native rules.

**Walkthrough (ordinary window).** "How does this window look?" → `auspicious_moderate`,
`effective_score` 0.52, `label_basis` showing the 0.70/0.45/0.20 ladder, one obstruction group with
its max override, `coverage` showing every window consumed. The reader sees the verdict **and the
rule that produced it**.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Take the suppression max per `independence_group` (value-identical when the obstructions are independent), gated on Vighnakara's offer** | yes — the projection gate depends on it |
| 2 | Stamp `label_basis` and `suppression_basis` on every row | yes |
| 3 | The 750 cap: disclose now; is the number right? (Q8's portfolio question) | disclose; the number is Q8's |
| 4 | Add the missing `window_end >= window_start` and `peak_date` CHECKs to the DDL (670(f) currently stands in for them) | yes |
| 5 | `catalog_status: DRAFT` → `CURRENT` once the stamps land? | the native's; this brief does not claim it |

---

## §11 — Not verified here

1. Whether any chart exceeds 750 convergence windows — unmeasured, and it bounds the cap's
   materiality.
2. Whether `ka_kalasutra` (a declared edge) is actually read by this writer — the intake reads
   `kala_convergence` and `kala_obstruction` only in the ranges read; the full file was not traced
   end to end.
3. Whether the DELETE-before-candidate ordering (`:19`) matters here as it does elsewhere — the
   transaction protects it, but the pattern differs from Avadhi/Kota/Moorti.
4. The 793-zeros / 0-NULLs and 100 %-Mode-C figures — the writer's own recorded measurements [A].
5. No database query; no test run.
