---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_BHAVISHYA_LEKHA_ELEVATION_BRIEF
version: "1.0"
status: DRAFT_FOR_INDEPENDENT_REVIEW
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md
synergy_binding_version: "2.2"  # §B1 ruled name is precision_regime (not claim_grain, which was v1.0); values {instant_grain, date_grain}; day_grade aliases date_grain until Sangam D-7 successor condition, NOT for a count of generations
asset_or_interface_ids: ["ka_bhavishya_lekha", "SC-1 (the date.today() five-year horizon anchor)", "SC-5 (the LIMIT 100 intake cap → coverage)", "the LEARNING LOOP: this is the ONE Kāla asset that issues a claim, so it is the only one whose proof matrix has a real Evaluation row — MACRO_PLAN P7 is PARKED and its outcome-preservation design must not make the later loop harder", "670(g): the live degeneracy detector — all 100 projections share one peak_date"]
goal_objective: "Make the layer's only prediction artifact predict distinguishably: its intake is ordered by an effective_score that ties at 0.700 for all 100 rows on the canonical chart, so the projection set is decided almost entirely by the tiebreak and every row shares one peak_date — a degeneracy migration 670's conjunct (g) already detects and reports RED. Give the ranking a basis that can separate windows, declare the horizon and the cap, and preserve the outcome-reattachment design exactly, because it is the hinge the calibration loop will hang on."
source_revision: "9feac52d7 (l3/kala-layer-briefs); cited code identical at fb46b258f (2026-09-24)"
accepted_upstream_contract: "ka_kala_darshana's kala_darshana JOIN ka_sangam's kala_convergence (effective_score, net_label, mode, tier_basis, confidence_label, rarity_years, and kc.domain behind a pre-flight schema probe); phala_anchors.bhavishya_id is an ON DELETE SET NULL FK, which is why rows are UPDATEd in place rather than deleted and re-inserted"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_BHAVISHYA_LEKHA_v1_0.md"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/pipeline/orchestrator/writers/ka_bhavishya_lekha.py", "platform/python-sidecar/tests/l3/test_ka_bhavishya_lekha*.py", "one additive migration on kala_bhavishya (coverage/qualification columns; NO change to outcome_recorded/outcome_notes semantics)"]
interface_packet_targets_not_may_touch: ["platform/src/lib/retrieval/registry/layers/L3_kala/query_projections.ts, query_temporal_activation.ts, knowledge/editorial.ts — Pūrṇa-owned", "platform-mcp/src/tools/kala_views/{now,promise_gate,ahead}.ts, lib/ahead_autofile.ts, register_p1_aliases.ts — Pūrṇa-owned; L3 owns only the sentinel test"]
must_not_touch: ["kala_darshana / ka_kala_darshana and kala_convergence / ka_sangam (producers; their briefs)", "phala_anchors and pipeline/orchestrator/writers/ph_nimitta.py, services/ph_nimitta/engine.py (L4 readers, sealed)", "the outcome-reattachment contract: outcome_recorded / outcome_notes semantics, the (signal_id, peak_date) identity, the FOR UPDATE read and the advisory partition lock — P7 depends on them", "platform-mcp/src/tools/kala_views/**", "applied migrations — incl. 670 and 1033–1070", ".github/workflows/deploy.yml", "kala_gochara_windows WHERE generation='v1'", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY"
target_state_campaign: "ANALYZED → ENRICHED at stage 3; the registry check is RED today by design (670 header)"
wave: "W4"
shape: single asset, up to 100 projection rows per chart, ranked 1..n, forward-only over five years
evidence_base: >
  Source read directly on 9feac52d7 [V]; migration 670's ka_bhavishya_lekha contract (a)–(g) and its
  header, blueprint v5.0 [A]; no database query. Figures quoted from code comments are the writer's
  own recorded measurements and are marked [A].
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.0 (2026-09-24): first issue; awaiting independent review."
---

# `ka_bhavishya_lekha` elevation brief — the one asset that predicts

## §0 — The recommendation, in one paragraph

`ka_bhavishya_lekha` is the layer's **only claim-issuing asset**: it turns the top forward-looking
verdicts into ranked probabilistic projections with a falsifiability hook and a source chain. Its
outcome handling is the most carefully built thing in the layer and must not be touched. Rows are
**UPDATEd in place, never delete-and-reinsert**, because `phala_anchors.bhavishya_id` is an
`ON DELETE SET NULL` FK and *"delete/reinsert would sever accepted downstream provenance even inside
a successful transaction"*; recorded outcomes are re-attached by `(signal_id, peak_date)` — *"a
prediction about THIS signal peaking on THIS date"* — **not** by `projection_rank`, because
re-ranking moves it; an unmatched projection defaults to `(False, None)` because *"an unmatched
projection is a NEW prediction, and giving it someone else's outcome would be worse than losing
one"*; the whole partition is taken under a `pg_advisory_xact_lock` and read `FOR UPDATE`; a
duplicate `(signal_id, peak_date)` in existing history **raises** rather than guessing; and anything
left un-re-attached after the rebuild is checked for. The comment says why: *"the writer used to
hardcode `False, None` into every row after a full per-chart DELETE, so the first outcome anyone ever
recorded would be destroyed by the next ordinary rebuild, silently"*, and MACRO_PLAN's P7 is PARKED
with the instruction that *"nothing in this programme may make the later loop harder"*. The defect
is upstream of all that: the intake is `ORDER BY kd.effective_score DESC NULLS LAST, kd.peak_date,
kd.convergence_id LIMIT 100`, and on the canonical chart **100 of 100 rows tie at 0.700** [A] — the
F-BHAV-3 fix gave that tie a *total* order (it previously varied build-to-build), but a total order
over a constant is still arbitrary, and migration 670's conjunct (g) — the F-BHAV-1 degeneracy
detector — reports **all 100 projections sharing one `peak_date`**, RED today. So the artifact ranks
1..100 on a quantity that does not vary, and presents a single date as a hundred predictions.
Recommendation: **`ENRICH_CORRECT` + `QUALIFY_LIMIT`** — give the ranking a basis that can separate
(the tie is upstream, so this is largely a DEMAND on Darshana/Saṅgam), declare the horizon anchor and
the cap as coverage, stamp what the rank was ordered by, and leave every outcome mechanism exactly as
it is. Decisions: §10.

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 | probabilistic forward projection | — |
| Product §5.2 / §7.1 | a probability is not an unexplained scalar; no scalar substitutes | binds `probability_tier` |
| **Migration 670 (`:125-229`) + header (`:31`)** [V] | header: *"ka_bhavishya_lekha — all 100 projections share one peak_date — a degeneracy detector firing"*; (a) accretion on **two** natural keys — `(chart, projection_rank)` and `(chart, convergence_id)` — because the table has only a surrogate id PK; (b) `projection_rank` must be **dense 1..n per chart** (*"its only addressable key"*); (c) §N.5 upstream authority — *"a projection never restates a window value as its own truth"*: peak/window/score/signal are copied verbatim off the source `kala_darshana` row, pinned on `(convergence_id, chart_id)` because *"the FK nulls the reference on cascade and enforces neither chart agreement nor survival"*; (d) §N.7 items 1 and 5 — `probability_tier` is a restatement of `(effective_score, …)`; (e) §N.7 item 1 — the falsifiability hook and the source chain are **narration over this row**, not new claims; (f) forward-only horizon (today .. today+5y); (g) **the degeneracy detector**, the direct F-BHAV-1 invariant (§N.6 item 3, B.10) | the contract is strong and (g) is **already reporting the defect this brief addresses** |
| Seed (`asset_registry_seed.ts:2409-2424`) | `target_table: 'kala_bhavishya'`, chart-scoped `count_sql`, `depends_on: ['ka_kala_darshana', 'ka_vighnakara', 'ka_sangam', 'bo_laksana']`, `asset_kind: 'artifact'`, `catalog_status: 'DRAFT'` | `ka_vighnakara` and `bo_laksana` are declared; the writer reads Darshana and Saṅgam directly — §11.2 |
| **MACRO_PLAN P7 (quoted in the writer, `:104-107`)** | PARKED, with *"nothing in this programme may make the later loop harder"* | the reason the outcome design is `must_not_touch` |
| `writer.py` comments (F-BHAV-3) | *"the old ORDER BY had no tiebreak, so which 100 of the eligible windows survived LIMIT 100 varied build-to-build whenever effective_score ties (measured: 100/100 rows tied at 0.700 on the canonical chart)"* [A] | the fix is real and preserved; the **tie itself** is this brief's subject |
| `writer.py` comments (outcome preservation) | *"Measured at the time of this fix: 200/200 rows `outcome_recorded = false`, 0 notes — so nothing is lost today and this is purely protective"* [A] | the design is protective, not yet load-bearing — and must stay that way until P7 unparks |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V]
`storage_type: 'postgres_table'`, `target_table: 'kala_bhavishya'`, `scope: 'per_chart'`,
`asset_kind: 'artifact'`, `catalog_status: 'DRAFT'`.

### 2.2 The code [V]
- **Partition lock** (`_PARTITION_LOCK_SQL`): `pg_advisory_xact_lock(hashtext('madhav:
  ka_bhavishya_lekha:partition:v1'), hashtext(chart_id))` — a transaction-scoped lock, so two
  concurrent builds of one chart cannot interleave their outcome re-attachment.
- **Horizon** (`:83`): `today = date.today()`; the intake window is `[today, date(today.year+5,
  today.month, today.day)]` — a **build-clock** anchor, undeclared on the row.
- **Existing history** (`:115-140`): `SELECT id, projection_rank, probability_tier, domain,
  peak_date, window_start, window_end, convergence_id, signal_id, effective_score, falsifiability,
  source_chain, narrative, outcome_recorded, outcome_notes, source_citation FROM kala_bhavishya
  WHERE chart_id = %s ORDER BY id **FOR UPDATE**`; each row keyed by
  `_outcome_identity(signal_id, peak_date)`; a duplicate key **raises `RuntimeError`**
  (*"rebuilding would make outcome …"*).
- **Re-attachment** (`_reattach_outcome` `:16-27`): `preserved.pop(key, (False, None))` — it
  **consumes** the entry, *"so anything left in `preserved` after the rebuild is an outcome that
  could not be re-attached"*, which `run()` checks at the end.
- **Schema probe** (`:143-158`): a read-only `information_schema.columns` probe for
  `kala_convergence.domain`, explicitly *"avoids `conn.rollback()` which violates the FROZEN
  orchestrator contract"* — an exemplary way to handle an optional upstream column.
- **Intake** (`:160-180`): `SELECT kd.convergence_id, kd.signal_id, kd.net_label, kd.effective_score,
  kd.peak_date, kd.window_start, kd.window_end, kd.narrative, kd.obstruction_summary,
  kc.confidence_label, kc.rarity_years, kc.mode, kc.tier_basis, {domain} FROM kala_darshana kd JOIN
  kala_convergence kc ON kd.convergence_id = kc.convergence_id WHERE kd.chart_id = %s AND
  kd.peak_date >= today AND kd.peak_date <= today+5y AND kd.net_label NOT IN ('obstructed_severe')
  ORDER BY kd.effective_score DESC NULLS LAST, kd.peak_date, kd.convergence_id **LIMIT 100**` —
  with the F-BHAV-3 comment recording the 100/100-at-0.700 measurement.
- **Candidate identity counts** (`:182+`): duplicate `(signal_id, peak_date)` among **candidates** is
  counted, so the rebuild can refuse rather than produce an ambiguous history.

### 2.3 Consumers [V]
| consumer | reads | role |
|---|---|---|
| `writers/ph_nimitta.py`; `services/ph_nimitta/engine.py` (**L4**) | `kala_bhavishya` | the predictive-anchor layer — **the projections become L4 anchors** |
| `query_projections.ts`; `query_temporal_activation.ts`; `knowledge/editorial.ts` | served | served |
| `kala_views/{now,promise_gate,ahead}.ts`; `lib/ahead_autofile.ts`; `register_p1_aliases.ts` | served | served — `ahead_autofile` writes the reader's *forward* view |
| `brahmagyan/domain_vocabulary.py` | `CANONICAL_DOMAINS` (imported by the writer) | vocabulary |
| `kala_derivation_completeness_guard.py` | the table | guard |

**Live-path statement.** This artifact is the layer's forward-facing output: it reaches L4's
predictive anchors and six served surfaces, including the "what's ahead" view. The degeneracy, the
build-clock horizon and the undisclosed cap are live on all of it.

### 2.4 Epistemic class
| field | class | authority | note |
|---|---|---|---|
| `peak_date`, `window_*`, `effective_score`, `signal_id`, `convergence_id` | inherited, **copied verbatim** | `kala_darshana` | 670(c) enforces |
| `projection_rank` | ordering | this writer | 670(b) pins density; **the order is over a tied quantity** |
| `probability_tier` | restatement of `(effective_score, …)` | this writer | 670(d) pins it; Product §5.2 forbids it standing alone |
| `falsifiability`, `source_chain` | **narration over this row** | 670(e) | correct — they add no claim |
| `outcome_recorded`, `outcome_notes` | **observed-world facts** | the outside world, recorded by a human | not derived from L1/L2 — the one place in the layer where that is true |
| `domain` | inherited when the column exists, else NULL | `kala_convergence` | the probe makes the absence honest |

### 2.5 Ladders
`PLAN_REVIEWED`; `catalog_status: DRAFT`; the registry check is **RED by design** (670 header, the
(g) degeneracy). t3: no event.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | On the canonical chart every eligible window carries `effective_score = 0.700` [A], so the intake's primary sort key is constant: the hundred projections that survive `LIMIT 100` are chosen by `peak_date, convergence_id` alone, and `projection_rank` 1..100 orders rows that the artifact itself cannot distinguish. Migration 670's conjunct (g) — the F-BHAV-1 degeneracy detector — reports that **all 100 share one `peak_date`**, and it is RED today. A reader of the "what's ahead" view is therefore shown a hundred ranked predictions about one date, ranked by a number that is the same for all of them |
| Evidence | `ka_bhavishya_lekha.py:160-180` (the intake and the F-BHAV-3 comment), `:83` (the build-clock horizon); `670:125-229` conjunct (g) and the header's *"all 100 projections share one peak_date"* [V] |
| Expected contract | §N.6 item 3 (a verdict layer is never silently empty **or** silently uniform); B.10 (no fabricated distinction); Product §5.2 (a tier is not an unexplained scalar); SC-5 (caps disclosed); SC-1 (a horizon is declared, not a clock side-effect); 670(g) |
| Defect class | **degenerate ranking** (a rank over a constant) + **undisclosed cap** + **undeclared build-clock horizon** |
| Impact | the layer's only predictions are undifferentiated; L4's anchors inherit the degeneracy; a reader is given false resolution — a hundred rows implying a hundred distinctions |
| Non-claim | **the cause is upstream**: `effective_score` is Darshana's, and its ties come from Saṅgam's convergence scores — this brief does not claim the writer computes it wrongly, only that it ranks on it without saying it cannot separate; the 100/100-at-0.700 and 200/200-no-outcomes figures are the writer's own recorded measurements [A]; whether the tie persists on other charts is unmeasured |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q07 (what lies ahead) — and this is the layer's only asset whose output is a
   **claim**, so it is the only one whose Evaluation row is real (§7).
2. **The rank declares its basis and its resolution.** Every row carries
   `rank_basis = {primary: 'effective_score', tiebreaks: ['peak_date','convergence_id'],
   distinct_primary_values: n, ties_at_rank_1: m}` — so a reader (and L4) can see that the primary
   key took **one** value across the set. When `distinct_primary_values == 1`, the artifact declares
   `completeness_state='unqualified'` on the ranking with `reason='degenerate_primary_key'`: the rows
   are still served (B.10 — never silently dropped) but the **rank is not offered as a
   distinction**.
3. **The separation is a DEMAND, not a local invention.** A rank can only separate if the upstream
   score does. This brief **DEMANDS** from `ka_kala_darshana` (and through it `ka_sangam`) either a
   score with real variance or an explicit secondary ordering key (rarity, independence count,
   proximity). It does **not** invent a local tiebreak that would manufacture a distinction the
   evidence does not support — that is precisely the §N.7-item-6 defect. Until the DEMAND lands the
   honest artifact is *"n windows, indistinguishable on the available evidence, listed by date"*.
4. **The horizon declared (SC-1).** `as_of` from `ctx.config` — and the layer already has a
   precedent spelling: `ka_jivana_parva` reads `ctx.config['as_of_date']`, so this asset uses the
   **same key** rather than a second one. `as_of_used`, `as_of_source ∈ {declared, build_clock}` and
   `horizon_end` stamped on every row; the five-year span becomes a declared parameter rather than a
   literal.
5. **The cap → coverage (SC-5/B5).** `coverage = {requested_horizon: [as_of, as_of+5y],
   completed_horizon, resolution: 'convergence_window', partitions_searched: ['forward_eligible'],
   exclusions: [{reason: 'net_label_obstructed_severe', dropped: n}, {reason: 'below_intake_cap',
   dropped: m, min_score_consumed: x}], unsearched_regions: [], completion_detector:
   'all_forward_eligible_windows_ranked_or_capped'}` — the `obstructed_severe` exclusion matters
   especially: a window suppressed by the verdict layer is **not** projected, and that is a judgement
   the reader should see, not an absence.
6. **`probability_tier` keeps its restatement discipline (670(d)) and gains its ladder**, as the
   verdict layer's `label_basis` does: `tier_basis_ladder` on the row, so Product §5.2's "not an
   unexplained scalar" is satisfied from the row rather than from the source.
7. **Everything about outcomes is preserved, byte for byte** — see §5. The only addition permitted
   near them is **read-only**: `outcome_reattached ∈ {true, false, n/a}` derived from whether
   `_reattach_outcome` found an entry, so the loop's own health is observable without changing its
   mechanics.
8. **Qualification (B2).** `epistemic_class` per §2.4 — including the honest statement that
   `outcome_recorded` is an **observed-world** fact, not a derivation; `operator_role='evaluation'`
   on the outcome fields (the one place in this layer where F12's `evaluation` role applies) and
   `'interpretation'` on the tier; `tier_basis='relative_uncalibrated'` **until P7 unparks** — this
   asset is exactly where a `calibrated:<gate_id>` value will eventually belong, and saying so now
   marks the seam.
9. **Old vs new.** Positive: a chart with varied scores → ranks that separate, `rank_basis` showing
   n distinct values. Negative: no forward windows → an honest empty **with coverage** (today: no
   rows and no statement). Boundary: `effective_score` all equal → rows served, rank `unqualified`,
   `reason='degenerate_primary_key'`, 670(g) still red and now **explained on the data**. Missing: a
   recorded outcome whose `(signal_id, peak_date)` no longer appears → the existing
   un-re-attached check fires (preserved). Duplicated: two candidates sharing
   `(signal_id, peak_date)` → the existing refusal (preserved).
10. **Simpler baseline.** Today's projections.
11. **Ablation.** Serve the same forward question with and without `rank_basis`: today the reader
    receives a hundred ranked rows and cannot tell that the ranking is over a constant; after, the
    same hundred rows arrive with the rank explicitly not offered as a distinction. The measured
    difference is whether false resolution reaches the reader.

---

## §5 — Preservation, fences, migration, rollback

- **`PRESERVE` — the outcome contract, in full and unaltered.** The advisory partition lock; the
  `FOR UPDATE` read of existing history; re-attachment by `(signal_id, peak_date)` and **not** by
  `projection_rank`; the consuming `pop` and the end-of-run check for un-re-attachable outcomes; the
  `RuntimeError` on duplicate history identity; the `(False, None)` default for an unmatched
  projection and the reason given for it; **UPDATE in place rather than delete-and-reinsert**,
  because `phala_anchors.bhavishya_id` is `ON DELETE SET NULL`. These are in `must_not_touch` and
  the reason is MACRO_PLAN P7: *"nothing in this programme may make the later loop harder"*.
- Also `PRESERVE`: the read-only schema probe (it avoids a `conn.rollback()` that would violate the
  FROZEN contract — the right pattern for an optional upstream column); the F-BHAV-3 total
  `ORDER BY`; the forward-only horizon; 670(c)'s verbatim copying.
- `ENRICH_CORRECT`: `rank_basis` and the `unqualified` ranking state; `as_of` declared.
- `QUALIFY_LIMIT`: coverage; `tier_basis_ladder`; the B2 stamps.
- **DEMAND**: a separating quantity from `ka_kala_darshana`/`ka_sangam` (§4.3).
- **Migration**: one additive migration on `kala_bhavishya`. It must not touch `outcome_recorded`,
  `outcome_notes` or the row `id` (the L4 FK's target).
- Rollback: additive columns; the ranking's *order* is unchanged — only its declared status moves.

---

## §6 — Lenses A–J *(appendix)*

| lens | answer |
|---|---|
| A | L3 artifact rows; the layer's only claim-issuing asset; `ENRICH_CORRECT + QUALIFY_LIMIT` |
| B | four declared edges; Darshana and Saṅgam read directly; `ka_vighnakara`/`bo_laksana` declared — §11.2; fan-out: L4 anchors + six served surfaces |
| C | invariants: 670 (a)–(g); rank density; verbatim upstream copying; **every outcome mechanism unchanged**; the rank's basis declared |
| D | the tie is upstream — the DEMAND, not a local fix |
| E | L4's predictive anchors are the consequential consumer |
| F | `rank_basis`, coverage, `tier_basis_ladder`, `outcome_reattached` machine-readable |
| G | one history read under a lock + one intake query; cheap |
| H | idempotent by UPDATE-in-place under an advisory lock; the un-re-attached check is the reliability detector |
| I | files in `may_touch`; one additive migration; W4 |
| J | this brief; §7; the review |

---

## §7 — Proof matrix

Columns: **verdict tier** F24; **scope** `[U]` unit, `[I]` DB fixture, `[S]` served.
**This is the one asset in the layer with a real Evaluation row.**

| proof | verdict tier | scope | fixture / command | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|---|
| Positive | COMPUTATIONAL_CORRECTNESS | I | a chart with **varied** `effective_score` | ranks separate; `rank_basis.distinct_primary_values > 1`; 670 (a)–(g) TRUE | the contract | any conjunct FALSE | integrity SQL |
| **Degeneracy** | COMPUTATIONAL_CORRECTNESS | I | the canonical shape — all scores equal | rows served; `completeness_state='unqualified'` on the ranking with `reason='degenerate_primary_key'`; `distinct_primary_values = 1`; 670(g) still red **and explained on the row** | B.10 + §N.6 item 3 | the rank is offered as a distinction (today) | integrity SQL + writer test |
| Negative | COMPUTATIONAL_CORRECTNESS | I | no forward-eligible windows | an honest empty **with coverage**, not silence | B5 | no rows and no statement | writer test |
| **Outcome preservation** | COMPUTATIONAL_CORRECTNESS | I | a row with `outcome_recorded=true` and notes; rebuild with the same `(signal_id, peak_date)` present | the outcome survives on the rebuilt row; `outcome_reattached=true`; the row `id` is unchanged (the L4 FK's target) | P7's hinge | the outcome is lost, or the id changes | writer test |
| **Outcome orphan** | COMPUTATIONAL_CORRECTNESS | I | a recorded outcome whose `(signal_id, peak_date)` is absent from the new candidate set | the end-of-run un-re-attached check fires; nothing is silently dropped | the consuming `pop` | it passes silently | writer test |
| **Outcome ambiguity** | COMPUTATIONAL_CORRECTNESS | I | two existing rows sharing `(signal_id, peak_date)` | `RuntimeError`, no write | never guess an outcome's owner | a guess is made | writer test |
| Relevant influence | COMPUTATIONAL_CORRECTNESS | I | raise one window's `effective_score` above the tie | it takes rank 1; the rest shift by one; no other field moves | isolation | a second row's content changes | writer test |
| Irrelevant control | COMPUTATIONAL_CORRECTNESS | I | reorder the intake rows | identical projections (the total `ORDER BY` guarantees it) | F-BHAV-3 | differs | writer test |
| Context | COMPUTATIONAL_CORRECTNESS | I | `kala_convergence.domain` absent | the probe returns false; `domain` NULL; **no rollback** | the FROZEN contract | a `conn.rollback()` path | writer test |
| Boundary | COMPUTATIONAL_CORRECTNESS | I | 101 forward-eligible windows; and a window at exactly `as_of + 5y` | 100 ranked, `dropped: 1`, `min_score_consumed`; the boundary window **included** | the cap disclosed; the horizon's inclusivity declared | a silent 100; the edge window's treatment unstated | writer test |
| Excluded-by-verdict | COMPUTATIONAL_CORRECTNESS | I | a window with `net_label='obstructed_severe'` | excluded **and named** in `coverage.exclusions` | a judgement, not an absence | silently missing | writer test |
| Delivery | COMPUTATIONAL_CORRECTNESS | S | sentinel `rank_basis.distinct_primary_values = 1` | reaches `query_projections`, the "ahead" view and L4's anchor intake | survives | absent | route test |
| Revision | COMPUTATIONAL_CORRECTNESS | I | Darshana rebuilds | projections re-derived; outcomes preserved; ranks dense (670(b)) | no accretion, no outcome loss | either fails | integrity SQL |
| Value | EXPLANATORY_DISCRIMINATIVE_VALUE | S | frozen Q07 question | the reader is told the ranking cannot separate; the baseline implies a hundred distinctions | — | no distinction | baseline record |
| **Evaluation** | EMPIRICAL_OUTCOME_PERFORMANCE | — | **governed, and PARKED**: MACRO_PLAN P7 owns the calibration loop; this asset's `outcome_recorded`/`outcome_notes` are its substrate. No evaluation claim is made or permitted here; `tier_basis` stays `relative_uncalibrated` until P7 supplies a gate id | the seam is marked, not crossed | a calibration claim appears before P7 | P7 |

Binding: **OFFERS** B2 (`epistemic_class` incl. the observed-world class on outcomes,
`completeness_state`, `operator_role` — `evaluation` on the outcome fields, `interpretation` on the
tier, `tier_basis` with its `calibrated:<gate_id>` seam marked), B5 (`coverage`, seven keys).
**DEMANDS** a separating quantity from `ka_kala_darshana`/`ka_sangam` (§4.3). B1: `peak_date` and the
window bounds are copied from the producer with the producer's grain declared as inherited. B3:
`window_ref` inherited from `kala_convergence`; the projection's own identity is
`(signal_id, peak_date)` — **the outcome key**, and it is not to be changed. B4: n/a — a projection
is not a witness; stated.

---

## §8 — Prioritization

(1) `rank_basis` + the `unqualified` ranking state (the reader is currently shown false resolution)
→ (2) the DEMAND on Darshana/Saṅgam for a separating quantity → (3) coverage incl. the
`obstructed_severe` exclusion → (4) `as_of` declared under the layer's one spelling →
(5) `tier_basis_ladder` → (6) the read-only `outcome_reattached` observability field. W4.

---

## §9 — Disposition and target state

`ENRICH_CORRECT` + `QUALIFY_LIMIT`. Data-plane: `PRODUCER_READY`; `CONSUMER_INTEGRATED` when the
served projections and L4's anchor intake carry `rank_basis`. Campaign: `ANALYZED → ENRICHED`.
Non-claims: **no calibration claim of any kind** — P7 is PARKED and `tier_basis` stays
`relative_uncalibrated`; no `VALUE_EVALUATED`; the degeneracy's cause is upstream and this brief does
not fix it locally; `catalog_status` stays `DRAFT` until the native rules.

**Walkthrough (ordinary forward view).** "What's ahead for me?" → the forward-eligible windows,
ranked where the evidence separates and **explicitly not ranked** where it does not, each with its
tier and the ladder that produced it, the `obstructed_severe` windows named as excluded rather than
missing, and the horizon stated. The reader gets what the evidence supports and no more resolution
than it has.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **When the primary ranking key takes one value, declare the ranking `unqualified` and serve the rows unranked-in-substance** rather than inventing a local tiebreak | yes — a manufactured distinction is the §N.7-item-6 defect, and the rows must still be served (B.10) |
| 2 | **DEMAND a separating quantity from `ka_kala_darshana` / `ka_sangam`** (score variance, or a declared secondary key) | yes — the fix belongs upstream |
| 3 | Declare `as_of` under the layer's existing spelling (`ctx.config['as_of_date']`, which `ka_jivana_parva` already reads) and make the five-year span a parameter | yes |
| 4 | The 100 cap: disclose now; is the number right? (Q8's portfolio question) | disclose; the number is Q8's |
| 5 | **Confirm that the outcome-reattachment contract stays untouched** (lock, `FOR UPDATE`, `(signal_id, peak_date)` identity, UPDATE-in-place, the refusals) while P7 is PARKED | yes — this brief adds only a read-only observability field near it |

---

## §11 — Not verified here

1. Whether the 0.700 tie persists on charts other than the canonical one — unmeasured, and it
   decides whether the degeneracy is chart-specific or structural.
2. Whether `ka_vighnakara` and `bo_laksana` (declared edges) are read by this writer — the ranges
   read cover the lock, history, probe and intake; the full file was not traced end to end.
3. Whether any `outcome_recorded=true` row exists today — the writer's comment records 200/200 false
   at the time of its fix [A]; P7 is PARKED, so probably still none.
4. The live registry state (RED by design per the 670 header) and the live row count.
5. Whether the horizon's upper bound is inclusive in practice for a window at exactly `as_of + 5y` —
   the SQL uses `<=`, but the `date(today.year+5, …)` construction can raise on 29 February.
6. No database query; no test run.
