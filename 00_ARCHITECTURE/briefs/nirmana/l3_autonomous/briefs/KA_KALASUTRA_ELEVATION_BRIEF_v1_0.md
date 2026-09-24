---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_KALASUTRA_ELEVATION_BRIEF
version: "1.0"
status: DRAFT_FOR_INDEPENDENT_REVIEW
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md
asset_or_interface_ids: ["ka_kalasutra", "SC-1 (the shared date resolver's `date.today()` default and its 8-window cap)", "SC-5 (the cap → coverage)", "SC-9 (the signal reference it inherits from Yojaka)", "registry packet: declare the undeclared L1 read (`chart_dashas` via ka_temporal)"]
goal_objective: "Make the activation table say which periods it searched and which it dropped: the shared resolver caps every predicate at eight matched periods and picks its 'primary' one against the SERVER's today, so a build's own date silently decides which window a consumer sees; and the table's dating authority, upstream agreement and signal identity are already contracted but two of the three read FALSE on a cascade-damaged chart. Declare the cap, declare the horizon anchor, declare the L1 read, and carry the producer's own convergence contributions instead of only the best one."
source_revision: "9feac52d7 (l3/kala-layer-briefs); cited code identical at a99300bb7 (2026-09-24)"
accepted_upstream_contract: "ka_yojaka's kala_activation_predicates (its own brief's signal_ref is DEMANDED here); L1 chart_dashas via services/ka_temporal/date_resolver (vimshottari, level_n ≤ 2, per-predicate ayanāṃśa, birth-forward); ka_sangam's kala_convergence (peak REFINES a window, never creates one)"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_KALASUTRA_v1_0.md"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/pipeline/orchestrator/writers/ka_kalasutra.py", "platform/python-sidecar/services/ka_temporal/date_resolver.py (SHARED — ka_vighnakara also calls resolve_activation_windows; any signature change is a coordinated packet with that writer's owner)", "platform/python-sidecar/tests/l3/test_ka_kalasutra*.py, tests/**/test_date_resolver*.py", "one additive migration on kala_activation (coverage/qualification columns; NO new FK)"]
interface_packet_targets_not_may_touch: ["platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts — Pūrṇa-owned", "platform-mcp/src/tools/kala_views/{ahead,now,promise_gate}.ts — Pūrṇa-owned", "platform/src/lib/retrieval/spine/{compute_spine_bundle,constants,types}.ts and register_d8/d9/spine_bundle — the spine reads this table; L3 owns only the sentinel test"]
must_not_touch: ["kala_activation_predicates / ka_yojaka (producer; its brief)", "kala_convergence / ka_sangam (producer; its brief)", "chart_dashas / ga_* (L1)", "migration 403's CASCADE set and migration 455's uniqueness key (applied)", "platform-mcp/src/tools/kala_views/**", "applied migrations — incl. 246, 403, 455, 670 and 1033–1070", ".github/workflows/deploy.yml", "kala_gochara_windows WHERE generation='v1'", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY"
target_state_campaign: "ANALYZED → ENRICHED at stage 3"
wave: "W4"
shape: single asset, rows keyed (chart_id, signal_id, ayanamsha_id, source_citation) — the DB UNIQUE index, where source_citation embeds the build's own period index
evidence_base: >
  Source read directly on 9feac52d7 [V]; migrations 246/403/455/670, blueprint v5.0 §3.5 row 11 /
  §4 / §16.2, Lane D/E/F [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.0 (2026-09-24): first issue; awaiting independent review."
---

# `ka_kalasutra` elevation brief — the dating step, with its cap and its clock declared

## §0 — The recommendation, in one paragraph

`ka_kalasutra` turns Yojaka's predicates into dated activation windows. Its headline claim is
honest — *"no fabricated dates: every date traces to a chart_dashas row"* (`ka_kalasutra.py:1-10`
[V]) — and the CR-109 fix made it emit **one row per matched in-life period** rather than one
collapsed row per predicate (`:142-170`), keyed by a `source_citation` that embeds
`period={idx}` so the semantic key is unique by construction (`:172-199`). Three things are
undeclared. (1) The shared resolver caps each predicate at **eight** matched periods
(`date_resolver.py:417` `max_windows: int = 8`, cut at `:498-500`) and nothing on the row or in the
result says a cut happened. (2) It selects the "primary" period — the one whose dates become
`activation_start/end/peak` — against **`date.today()`** (`:473`, `as_of_date` defaults to the
server's date; current-tier then future-tier, `:475-500`), so **the build's own calendar day decides
which of a predicate's periods a consumer sees**, and two builds a month apart produce different
primaries from identical data. (3) The L1 read is **undeclared**: `depends_on` names `ka_yojaka`,
`ka_sangam`, `bo_laksana` (seed) while the writer reads `chart_dashas` through `ka_temporal`
(`:54-66`). Meanwhile the live contract (migration 670 `:796-890`) already asserts what matters —
(a) every dated window lies inside a real vimshottari MD/AD of the same chart **and ayanāṃśa**,
(b)/(b2) the semantic key and its parseable period marker, (c) window coherence and no pre-birth
start, (d) two-way agreement with Yojaka, (e) signal identity — and two of those read FALSE today
on a cascade-damaged chart (670 header). Recommendation: **`ENRICH_CORRECT` + `QUALIFY_LIMIT`** —
`as_of` becomes a declared input (chart-zone), the cap becomes B5 coverage with the dropped periods
named, the L1 edge is declared, and the producer's convergence contributions are carried rather
than only the single best one. No new FK. Decisions: §10.

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 | activation windows from predicates × clocks | — |
| Strategy §6.1 (the asset's row) | compile activation over the complete candidate set; no fabricated dates | the no-fabrication rule is met; the *selection* among real dates is not declared |
| **Migration 670 (`:796-890`)** [V] | (a) dating authority — every `activation_start/end` inside a real `chart_dashas` vimshottari row of the same chart and ayanāṃśa, `level_n ≤ 2` (**RED today on 56 rows, all one chart, all `src=dasha_timeline`**); (b) accretion on the **semantic** key (`split_part(source_citation,':period=',2)`), because the DB UNIQUE index `(chart, signal, ayanamsha, source_citation)` cannot see it; (b2) every citation must carry the period marker or (b) degenerates; (c) start/end populated together, not inverted, peak inside, **no activation before `charts.birth_date`**; (d) two-way agreement with `kala_activation_predicates` (**RED: 49,730 predicates with no activation — the cascade**); (e) the signal belongs to this chart and ayanāṃśa | a strong contract; the elevation must not weaken it |
| Migration 246 (`:3-33`) | DDL: FK `chart_id → charts` CASCADE **and `signal_id → bodha_msr_signals` CASCADE**; `signature_class` CHECK; DATE activation columns; scores bounded `[0,1]`; `source_citation NOT NULL DEFAULT 'ka_kalasutra:v1.0'`; unique index `(chart, signal, ayanamsha)` — later widened by 455 to include `source_citation` | the cascade FK is why an orphaned predicate cannot produce a row here (Yojaka's §2.3) |
| Blueprint §3.5 row 11 (`:327`), §4 (`:399`), §16.2 (`:909`) | rows **0** (335,403 recorded — the cascade); cap 8; build-date primary; undeclared L1 read; *"keep all convergence contributions (not best-only); persist `mode`, `tier_basis`, independence; declare `ga_dashas`; adopt SC-1"* | this brief |
| `date_resolver.py` [V] | `resolve_activation_windows(..., max_windows: int = 8, as_of_date: Optional[date] = None)` (`:408-417`); `today = as_of_date if as_of_date is not None else date.today()` (`:473`); current-tier then future-tier primary selection (`:475-500`); the primary is **guaranteed a slot ahead of the cut** (`:496-500`); `load_dasha_timeline` selects `start_date, end_date` (DATE) for `system_id='vimshottari'`, `level_n <= max_level`, birth-forward (`:325-370`) | the cap and the clock are the resolver's, and the resolver is **shared** with `ka_vighnakara` |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V]
`asset_registry_seed.ts:2280-2295`: `storage_type: 'postgres_table'`, `target_table:
'kala_activation'`, chart-scoped `count_sql`, `depends_on: ['ka_yojaka', 'ka_sangam',
'bo_laksana']`, `scope: 'per_chart'`. **`ga_dashas` is read and not declared.**

### 2.2 The code [V]
- **Idempotency**: `SET LOCAL statement_timeout = 0`; `DELETE FROM kala_activation WHERE chart_id`
  (`:33`) **before** the candidate is built — note this is the opposite of the
  prepare-then-delete discipline other writers in the layer adopted (§4.7).
- **Predicates** (`:38-48`): all predicate rows for the chart, ordered by `signature_class`.
  Empty → *"No predicates — run ka_yojaka first"* (`:50-52`).
- **Timelines** (`:54-66`): `resolve_birth_date`, then one `load_dasha_timeline` per
  **predicate's own ayanāṃśa**, lazily cached — correct (each predicate resolves against its own
  ayanāṃśa's periods).
- **Convergence map** (`:68-92`): `SELECT … FROM kala_convergence WHERE chart_id AND signal_id IS
  NOT NULL`, reduced to the **single highest `convergence_score` per signal** — every other
  contribution is discarded before the resolver sees it.
- **Resolution** (`:100-118`): `resolve_activation_windows(dasha_rule, timeline, transit_rule=…,
  strength_hook=…, convergence_peak=peak, signature_class=…, birth_date=…)` — **`as_of_date` is not
  passed**, so the resolver falls back to `date.today()`.
- **Rows** (`:142-199`): one per `period_windows` entry, each carrying the **same** full
  `active_dasha_periods_jsonb` and `predicted_dates` but its own `start/end/peak` and
  `proximity_score`; `source_citation = f"ka_kalasutra:v1.0:signal={sig[:8]}:src={resolution_source}:
  period={idx}"` (+ `:always_on={reason}`); `ON CONFLICT (chart, signal, ayanamsha, source_citation)
  DO NOTHING` (`:189-199`), documented as a true no-op safety net after migration 455.
- **Always-on** (`:135-141`): a predicate with `always_on_reason` emits
  `[{'kind':'always_on','reason':…}]` into the predicted dates.

### 2.3 Consumers [V]
| consumer | reads | role |
|---|---|---|
| `query_temporal_activation.ts:376-394` | activation rows, then the predicates for those signals | served `computation` |
| `kala_views/{ahead,now,promise_gate}.ts`; `ahead_autofile.ts`; `register_p1_aliases.ts` | activations | served |
| `platform/src/lib/retrieval/spine/{compute_spine_bundle,constants,types}.ts`; `register_d8_assess_domain.ts`, `register_d9_judgment.ts`, `register_spine_bundle.ts` | the spine bundle | **the retrieval spine** — the widest fan-out of any Kāla table |
| `services/taranga_service.py` | activation rows | service |
| `knowledge/editorial.ts`, `source_query_availability.ts` | catalog | census |

**Live-path statement.** This is the layer's most-read table. The eight-window cap and the
server-date primary are live on every one of those surfaces.

### 2.4 Epistemic class
| field | class | authority | note |
|---|---|---|---|
| `activation_start/end/peak` | `COMPUTED_FACT_CONFIGURATION` (derived from L1) | L1 `chart_dashas` via the resolver | DATE grain; **which** period they come from is server-date-dependent |
| `active_dasha_periods_jsonb`, `activation_predicted_dates_jsonb` | the full birth-forward listing | the resolver | capped at 8 — undeclared |
| `dasha_activation_proximity_score` | `INTERPRETIVE_INFERENCE` | the resolver | `tier_basis='relative_uncalibrated'` owed |
| `orb_strength`, `convergence_score` | inherited from Saṅgam | `kala_convergence` | **only the best contribution survives** |
| `signature_class` | inherited | Yojaka | CHECK-constrained (246) |
| `source_citation` | provenance **and** the semantic key | this writer | 670(b)/(b2) depend on it |

### 2.5 Ladders
`PLAN_REVIEWED`; rows **0** live for the canonical chart (the cascade), 335,403 recorded [A]. t3: no
event.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | Build the chart today and again in three months from identical L1/L2 data: a predicate whose lord has nine matched in-life periods emits **eight** rows both times, but the period promoted to `activation_start/end/peak` differs, because the resolver's `today` is `date.today()` (`:473`) and the current/future tiering moves with it — and the ninth period is dropped with no record either time. A consumer of `kala_now_get` therefore sees a window chosen by *when the build ran*, and a consumer counting a predicate's activations sees eight without being told there were nine |
| Evidence | `date_resolver.py:417,:473,:475-500`; `ka_kalasutra.py:100-118` (no `as_of_date` passed), `:142-170`; seed `depends_on` vs `:54-66` [V] |
| Expected contract | SC-1 (a horizon/clock is a declared input, never a server-date side effect); SC-5/B5 (every cap disclosed); F09/DP06 (declared dependencies); §N.8 (a selection that cannot be reproduced from the row's own fields is not auditable) |
| Defect class | **wrong context** (build-date selection) + **undisclosed cap** + **undeclared dependency** + **discarded contributions** (best-only convergence) |
| Impact | build-to-build nondeterminism on a table the retrieval spine reads; a predicate's activation count is a floor presented as a total; Saṅgam's other contributions for the same signal never reach the dating step |
| Non-claim | no claim that any specific served answer changed between builds (unmeasured); the 0-row live state is the L2 cascade's, not this writer's; whether nine-period predicates are common is unmeasured |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q02 (which periods a mechanism is engaged in), Q03's dating half. Not Q05.
2. **`as_of` declared (SC-1).** `ka_kalasutra` passes `as_of_date` explicitly from `ctx.config`
   (chart-zone today by default) and stores it on the row (`as_of_used`), so the primary selection is
   reproducible. The resolver keeps its `Optional` default — **it is shared with `ka_vighnakara`
   (`:448-458`), so the signature does not change**; only this caller's argument does.
3. **The cap disclosed (SC-5/B5).** `coverage = {requested_horizon: [birth, last matched period],
   completed_horizon, resolution: 'dasha_period', partitions_searched: [ayanāṃśa], exclusions:
   [{reason: 'above_max_windows', dropped: n}], unsearched_regions: [], completion_detector:
   'all_matched_periods_emitted_or_capped'}` per predicate; `max_windows` itself is carried as
   `window_cap` so a reader can see the bound that produced the number.
4. **All convergence contributions, not the best one.** The convergence map keeps every row per
   signal with its `mode`, `tier_basis` and independence fields; the resolver still **refines** with
   the best peak (unchanged behaviour), but the row carries `convergence_contributions[]` so a
   consumer can see that three windows agreed rather than one.
5. **Declared dependency.** `ga_dashas` is added to `depends_on` by registry packet (the edge is
   real and load-bearing); `ka_sangam` and `ka_yojaka` stay.
6. **Inherited identity (SC-9).** The row carries Yojaka's `signal_ref` (that brief's DEMAND) rather
   than a bare `signal_id`, so an L2 regeneration is visible here too; **no new FK** — the existing
   cascade FK (246) already binds it, and that is the reason an orphan cannot reach this table.
7. **Delete-then-insert ordering.** The DELETE fires before the candidate is assembled (`:33`),
   unlike Avadhi/Kota/Moorti, which assemble first. If the resolver raises mid-build the partition
   is already gone (the transaction rolls back, so nothing is lost on disk — but the pattern differs
   from the layer's). Recommend aligning to assemble-then-delete for uniformity (§10.4).
8. **Qualification (B2).** `tier_basis='relative_uncalibrated'` on the proximity score;
   `epistemic_class` per §2.4; `operator_role='computation'`; `completeness_state='applied'` on a
   dated row, `'unavailable'` with `reason` where nothing resolved (today the fallback is an
   all-NULL row — it must carry the reason).
9. **Old vs new.** Positive: a predicate with three matched periods → three rows, coverage
   `dropped: 0`, `as_of_used` stamped. Negative: no predicates → the existing honest refusal.
   Boundary: a predicate with nine matched periods → eight rows + `dropped: 1`; and the same build
   run with two different `as_of` values produces the **same eight rows** with a different primary,
   which is now visible. Missing: nothing resolves → one row with
   `completeness_state='unavailable'` and a reason, not a silent all-NULL row. Duplicated: the same
   signal under two ayanāṃśas → two partitions.
10. **Simpler baseline.** Today's rows.
11. **Ablation.** Build twice with `as_of` fixed to two different dates: the row set is identical and
    only `as_of_used` + the primary differ — today the row set is identical but the primary changes
    with no field explaining why.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: the no-fabricated-dates rule; per-predicate ayanāṃśa timelines; the CR-109 one-row-per
  period emission and its `period={idx}` citation key (670(b)/(b2) depend on it); the always-on
  passthrough; the `ON CONFLICT` no-op safety net.
- `ENRICH_CORRECT`: `as_of` passed and stored; all convergence contributions; the declared edge.
- `QUALIFY_LIMIT`: the cap as coverage; `tier_basis`; the unresolved-row reason.
- **Shared-code fence**: `date_resolver.py` is called by `ka_vighnakara` too — no signature change,
  only this caller's argument; any resolver change is a coordinated packet.
- **Migration**: one additive migration on `kala_activation` (coverage/qualification columns);
  **no new FK**; number verified at execution.
- Rollback: additive columns; the `as_of` argument defaults to today's behaviour if unset.

---

## §6 — Lenses A–J *(appendix)*

| lens | answer |
|---|---|
| A | L3 rows; derivation of dates from L1 periods under L2 predicates; `ENRICH_CORRECT + QUALIFY_LIMIT` |
| B | three declared edges; **`ga_dashas` read and undeclared**; fan-out: the retrieval spine, four served surfaces, one service |
| C | invariants: 670 (a)–(e); every emitted date inside a real L1 period of the same ayanāṃśa; the citation's period marker parseable; the row set invariant to `as_of` |
| D | the 0-row live state is upstream (the cascade) |
| E | the widest consumer set in the layer |
| F | coverage, `as_of_used`, `convergence_contributions` machine-readable |
| G | unmeasured; one timeline load per ayanāṃśa, cached |
| H | idempotent; delete-then-insert (ordering per §4.7) |
| I | files in `may_touch`; one additive migration; W4; a coordinated resolver fence |
| J | this brief; §7; the review |

---

## §7 — Proof matrix

Columns: **verdict tier** F24; **scope** `[U]` unit, `[I]` DB fixture, `[S]` served.

| proof | verdict tier | scope | fixture / command | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|---|
| Positive | COMPUTATIONAL_CORRECTNESS | I | a predicate with three matched periods | three rows; coverage `dropped: 0`; `as_of_used` stamped; 670 (a)–(e) TRUE | the contract | any conjunct FALSE; a stamp absent | integrity SQL |
| Negative | COMPUTATIONAL_CORRECTNESS | I | no predicates | the existing honest refusal | no write | rows written | writer test |
| Relevant influence | COMPUTATIONAL_CORRECTNESS | I | add one matched L1 period to the fixture timeline | one more row (or `dropped` +1 at the cap) | the row set follows L1 | unchanged | writer test |
| Irrelevant control | COMPUTATIONAL_CORRECTNESS | I | run the same build with two different `as_of` values | **identical row set**; only `as_of_used` and the primary differ, both visible | `as_of` selects, never filters | the row set changes | writer test |
| Duplication | COMPUTATIONAL_CORRECTNESS | I | the same signal under two ayanāṃśas | two partitions; each resolved against its own timeline | never merged | one partition | writer test |
| Context | COMPUTATIONAL_CORRECTNESS | I | a predicate that resolves to nothing | one row with `completeness_state='unavailable'` + reason | honest gap | a silent all-NULL row (today) | writer test |
| Boundary | COMPUTATIONAL_CORRECTNESS | I | a predicate with **nine** matched periods | eight rows + `exclusions[above_max_windows].dropped = 1`; the primary still present | the cap disclosed and the primary never cut | a silent eight | writer test |
| Pre-birth | COMPUTATIONAL_CORRECTNESS | I | a period straddling birth | clipped to birth; 670(c) TRUE | no pre-birth activation | 670(c) FALSE | integrity SQL |
| Delivery | COMPUTATIONAL_CORRECTNESS | S | sentinel `exclusions[above_max_windows].dropped = 1` on one predicate | reaches `query_temporal_activation`'s envelope and the spine bundle | survives | absent | route test |
| Revision | COMPUTATIONAL_CORRECTNESS | I | Yojaka rebuilds | rows replaced; no accretion (670(b)) | §N.3 | accretion | integrity SQL |
| Value | EXPLANATORY_DISCRIMINATIVE_VALUE | S | frozen Q02 question | the answer states how many periods were searched and how many dropped; the baseline gives a count | — | no distinction | baseline record |
| Evaluation | — | — | `not_applicable` (activation windows are not outcome claims) | — | — | — | — |

Binding: **OFFERS** B1 (`t_start/t_end` as declared resolver-derived views over the DATE columns,
`inclusivity`, `claim_grain='date_grain'`), B2 (`completeness_state` + reason, `epistemic_class`,
`operator_role`, `tier_basis`), B5 (`coverage`, seven keys). **DEMANDS** Yojaka's `signal_ref`
(SC-9) and Saṅgam's per-contribution `mode`/`tier_basis`/independence fields. B3: the row's identity
is the semantic key `(chart, signal, ayanamsha, period_idx)` — offered as `window_ref` with
`generation = FORMULA_VERSION`. **Asset-local:** `as_of_used`, `window_cap`,
`convergence_contributions`, `source_citation`.

---

## §8 — Prioritization

(1) `as_of` declared and stored (build-to-build determinism on the spine's own table) → (2) the cap
as coverage → (3) the declared `ga_dashas` edge → (4) all convergence contributions → (5) the
unresolved-row reason → (6) `signal_ref` when Yojaka's lands. W4.

---

## §9 — Disposition and target state

`ENRICH_CORRECT` + `QUALIFY_LIMIT`. Data-plane: `PRODUCER_READY`; `DATA_ACCEPTED` requires the
upstream cascade to be resolved (rows are 0 today for the canonical chart);
`CONSUMER_INTEGRATED` when the spine and the served surfaces carry the coverage sentinel. Campaign:
`ANALYZED → ENRICHED`. Non-claims: the 0-row state is upstream; no `VALUE_EVALUATED`.

**Walkthrough (ordinary period).** "When is this mechanism engaged?" → three dated windows, each
with its own period, the primary marked, `as_of_used` shown, `coverage.dropped = 0`. The reader
learns not just when, but that nothing was hidden by a cap or chosen by the server's clock.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **`as_of` as a declared input stored on the row** (the resolver's signature unchanged, since `ka_vighnakara` shares it) | yes |
| 2 | **The eight-window cap: keep and disclose, or raise/remove?** (Q8's portfolio question) | keep and disclose now; the number is Q8's |
| 3 | Carry all convergence contributions rather than the best-only reduction | yes |
| 4 | Align the DELETE to assemble-then-delete, as Avadhi/Kota/Moorti do | yes, for uniformity |
| 5 | Declare `ga_dashas` on `depends_on` (registry packet) | yes |

---

## §11 — Not verified here

1. The live 0-row state and the 335,403 recorded count [A]; the 56 and 49,730 red-row figures are
   migration 670's own measurements.
2. How often a predicate has more than eight matched periods — unmeasured, and it bounds the cap's
   materiality.
3. Build duration.
4. Whether any served answer changed between two builds — unmeasured.
5. No database query; no test run.
