---
artifact: LANE_E_LAYER_VALUE_MODEL
version: "1.0"
status: DRAFT — Lane E of the L3 KĀLA ELEVATION READINESS campaign
produced_by: L3 Kāla readiness, Lane E (read-only, autonomous)
produced_on: 2026-09-22
canonical_chart: 482012f1-710e-4a25-994a-93821f5871aa
scope: >
  THE LAYER'S VALUE MODEL — what Kāla should contribute as a whole, what it contributes today,
  and where the layer loses information between its own assets. Deliberately NOT a re-run of the
  completed ENVIRONMENT/ARCHITECTURE audit (audit/*.md); that audit is treated as baseline and
  cited, not repeated.
method: >
  Read-only. Every claim carries a file:line or the exact SQL run this session. Baseline facts
  inherited from the completed audit are labelled [BASELINE] and attributed; facts I verified
  myself this session are labelled [VERIFIED-E] with the query or citation. Nothing was written
  to the DB (`default_transaction_read_only` enforced); no narrative/interpretive row content was
  selected — only counts, aggregates, schema and identity/numeric columns.
---

# LANE E — THE LAYER'S VALUE MODEL

## §0. The doctrine under test, and the one sentence this report adds

**L3's stated distinctive contribution** (`00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_STRATEGIC_LEDGER_v1_0.md:110`):

> L3 Kāla | Qualified engagement of those same structures by applicable clocks and contacts |
> Mechanism identity, precise intervals, hierarchy, enablement/inhibition, alternatives,
> recurrence and coverage | **Activity/intensity is not event probability; precise geometry is
> not equally precise life timing.**

Restated as a gate at `MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md:91` (DP08):
"Same structure is temporalized; **activity is not event probability.** Owner L3."

**The sentence this report adds:** Kāla today is not failing at the boundary the doctrine polices
(probability overreach) nearly as badly as it is failing *inside* the boundary the doctrine grants
it. The layer has genuinely earned the right to say "qualified, interval-bounded, recurrent,
contradicted" — and then, at four measured seams, throws away the qualification, the recurrence
and the contradiction before the answer leaves the layer. The doctrine says Kāla must not claim
probability. The evidence says Kāla is *under-claiming* structure: it reduces its own richest
outputs to one undifferentiated scalar and serves that scalar with no way for the reader to ask how
it was formed. **§N.6 (Serving Density) is violated internally, between assets, before serving is
even reached.**

A second doctrinal challenge, raised on evidence in §5.4: the ledger's phrase "applicable clocks"
is doing work the code cannot support, because for the canonical chart **the transit clock is
structurally absent from every composite Kāla output** and nothing in the output says so.

---

## §0.1 Ground state (re-verified this session, not inherited)

[VERIFIED-E] SQL run 2026-09-22 via `source /Users/Dev/madhav-l3/dbenv.sh` then `psql -Atq`:

```sql
SELECT 'kala_activation', count(*) FROM kala_activation WHERE chart_id='482012f1-…'
UNION ALL SELECT 'kala_convergence', …  -- (one UNION per table)
```

| table | rows, canonical chart |
|---|---:|
| `kala_activation` (ka_kalasutra) | **0** |
| `kala_convergence` (ka_sangam) | **0** |
| `kala_darshana` (ka_kala_darshana) | **0** |
| `kala_bhavishya` (ka_bhavishya_lekha) | **0** |
| `kala_obstruction` (ka_vighnakara) | **0** |
| `kala_activation_predicates` (ka_yojaka) | 50,678 |
| `kala_taranga` (ka_taranga) | 92,412 |
| `kala_avadhi` (ka_avadhi) | 1,169 |
| `kala_jivana_parva` (ka_jivana_parva) | 100 |

This corroborates `KALA_PROVING_JOURNEYS_BASELINE_v1_0.md` and `KALA_DATA_CENSUS_v1_0.md` and
establishes the five-table emptiness is **still true today**, not a stale reading.

[VERIFIED-E] Shape of `kala_convergence` globally (all charts), which is the only place the
convergence layer can be inspected at all:

```sql
SELECT mode, tier_basis, count(*), round(avg(independent_current_count)::numeric,2),
       min(convergence_score), max(convergence_score), count(DISTINCT signal_id)
FROM kala_convergence GROUP BY 1,2 ORDER BY 3 DESC;
```

| mode | tier_basis | rows | avg ICC | score min | score max | distinct signals |
|---|---|---:|---:|---:|---:|---:|
| D | relative_uncalibrated | 16,892 | 1.00 | 0.2589 | 0.6071 | **30** |
| A | relative_uncalibrated | 1,545 | 3.33 | 0 | 0.3805 | 41 |
| B | relative_uncalibrated | 1,190 | 3.26 | 0 | 0.2782 | 41 |
| C | relative_uncalibrated | 870 | 1.00 | 0.7000 | 1.0000 | **120** |

Four facts fall out of that one query and they govern most of this report:

1. **`tier_basis` is `relative_uncalibrated` for 100% of rows.** No Kāla score anywhere is a
   probability, and the data says so in its own column. (Corroborated in code at
   `ka_bhavishya_lekha.py:552-553`.)
2. **The modes live on disjoint, incomparable score scales.** Mode A/B top out at 0.3805; Mode C
   *starts* at 0.70. Any `ORDER BY convergence_score DESC` across modes is a mode filter wearing a
   strength filter's clothes — see §3.2.
3. **Modes C and D carry `independent_current_count = 1.00` by construction** (enforced by
   `platform/migrations/670_nirmana_l3_w3_integrity_contracts.sql:1195-1199`: C/D consult no point
   transit and no second current, so `orb_strength` is hard-set 1.0 and ICC floors at 1). 17,762 of
   20,497 rows — 87% of the whole convergence layer — are single-current rows.
4. **Coverage is tiny.** At most 41+41+120+30 = 232 *distinct* signals appear anywhere in
   `kala_convergence`, against 50,678 `kala_activation_predicates` rows. Independently corroborated
   in code by a measured comment at
   `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts:290-291`:
   "`orb_strength` is 99.6% NULL (measured) — ka_sangam only produces windows for <=260 of ~50,104
   activation predicates."

**The convergence layer covers ~0.5% of the predicate population, is 87% single-current, and is
uncalibrated by its own declaration.** Everything downstream that treats `convergence_score` as the
layer's strength axis inherits all three properties without inheriting the disclosure.

---

# §1. CONSUMER QUESTION PORTFOLIO — the acceptance baseline

Sixteen questions. Each is one only a *time* layer can answer: remove L3 and the question has no
addressee. For each: what must be known / computed / compared / challenged; what evidence would
overturn the answer; what an honest partial looks like.

The portfolio is the acceptance baseline in this sense: **a Kāla that can answer Q-K01…Q-K16 with
its contradictions preserved is elevated; a Kāla that answers ten of them and silently flattens the
other six is not**, regardless of row counts.

---

### Q-K01 (ORDINARY) — "What is running right now, on every clock that applies to me?"
- **Know:** every dasha system with in-life coverage at `now`, at every level the system defines;
  which of the seven+ systems the chart actually supports; the current tithi/vara/yoga/karana; the
  current transit positions against natal.
- **Compute:** interval membership at an instant, per system, per level. Which are *applicable* vs
  merely *computable*.
- **Compare:** the systems against each other — do Vimśottarī and (say) Yoginī name the same lord
  class right now?
- **Challenge:** "applicable" must be earned. A system with no adjudicated applicability rule for
  this chart is *computed*, not *running*.
- **Overturned by:** a boundary correction (a period start off by hours flips membership at a
  sandhi); a rectification of birth time.
- **Honest partial:** "Vimśottarī MD/AD/PD named with exact ISO bounds; five other systems computed
  but applicability not adjudicated — listed separately, not merged into one 'what is running'
  list."

### Q-K02 (ORDINARY) — "Which of my chart's mechanisms are currently in an activation window, and which are dormant?"
- **Know:** the set of compiled mechanisms (L2), each one's activation predicate (dasha
  eligibility + transit trigger + strength hook), and the intervals in which the predicate holds.
- **Compute:** predicate ⋈ clock → interval set.
- **Compare:** activated vs dormant is a partition of the *whole* mechanism set, not a top-N.
- **Challenge:** does an activation window mean the mechanism is *engaged*, or only that its
  necessary clock condition is satisfied? These are different claims.
- **Overturned by:** the mechanism's cancellation condition firing (an L2 fact) inside the window.
- **Honest partial:** "N of M mechanisms have a resolvable window; M−N have no constituent lord
  with in-life timeline coverage — enumerated, with the reason per mechanism, not dropped."

### Q-K03 (PRECISE LOOKUP) — "Exactly when does my current antardasha end, to the hour, and what is the sandhi risk?"
- **Know:** L1's `chart_dashas.end_iso` (timestamptz), `sandhi_flag`, `next_dasha_start_iso`.
- **Compute:** nothing — this is a *reference*, not a derivation (§N.5).
- **Compare:** the answer against the ayanamsha actually in force; five ayanamshas give five answers.
- **Challenge:** any L3 restatement that disagrees with L1 to the day is a halt-worthy bug.
- **Overturned by:** an ayanamsha change; nothing else.
- **Honest partial:** "end_date is 2027-03-14; the hour is available in L1 but the L3 surface you
  are reading carries only the date" — which is exactly today's state (§3.1).

### Q-K04 (COMPOUND) — "When do career pressure and health pressure coincide in the next five years, and which dominates?"
- **Know:** per-domain activation over a forward horizon; the domain attribution rule for each
  mechanism; the relative weight of the two.
- **Compute:** interval intersection across two domain streams; a dominance rule that is stated,
  not implied by a score ordering.
- **Compare:** the two streams on a *common* scale — which requires the scales to be commensurable.
- **Challenge:** "dominates" needs a definition. Higher score? Longer overlap? More independent
  currents? Each gives a different winner.
- **Overturned by:** the domain attribution being keyword-derived rather than mechanism-derived
  (see §5.3) — if career/health labels are substring matches, the coincidence is an artefact.
- **Honest partial:** "Both streams are elevated 2028-Q2–Q4; I cannot rank them because the two
  scores are not on a common scale (Mode C vs Mode A/B, §0.1 fact 2). Here are both, unranked, with
  the scale difference stated."

### Q-K05 (COMPARISON) — "Is the window you are pointing at in 2027 stronger than the one I lived through in 2019?"
- **Know:** both windows' full evidence sets, each with its own currents, orb, rarity, obstruction.
- **Compute:** a comparison whose factors are *symmetric in time* — a factor that penalises a
  window for being in the past makes the comparison meaningless.
- **Compare:** head-to-head, with a named decisive factor and a stated margin.
- **Challenge:** if the comparator's composite includes a recency/proximity term, it is a
  *prioritisation* comparator, not a *strength* comparator. The two must not be confused.
- **Overturned by:** the 2019 window's real outcome (L5). Retrodiction is the only empirical check
  the layer has.
- **Honest partial:** "On convergence + rarity + independent-current-count the 2027 window is
  stronger (0.71 vs 0.58, decisive factor = independent currents 4 vs 1). I have deliberately
  excluded the proximity factor, which would have decided this by recency alone."

### Q-K06 (DISAGREEMENT) — "Which clocks disagree about the second half of 2028, and why do they disagree?"
- **Know:** each clock's verdict on the period, each clock's own method and jurisdiction.
- **Compute:** agreement/disagreement as a *first-class output*, not as an accident of which row
  sorted highest.
- **Compare:** Vimśottarī vs Yoginī vs Muddā vs gochara vs Tājika-varsha vs KP — and crucially
  whether any two are independent at all.
- **Challenge:** two clocks that both descend from the same upstream evidence do not corroborate;
  two clocks with the same *root* do not dissent meaningfully either.
- **Overturned by:** discovering the "two clocks" share a producer (this is the live hazard — §3.2).
- **Honest partial:** "Vimśottarī says supported, gochara says obstructed. KP was not consulted
  (no detector ran) — reported as `insufficient_data`, not as agreement."

### Q-K07 (UNCERTAINTY) — "How confident are you about that window, and what specifically would change your mind?"
- **Know:** what the confidence number *is* — its units, denominator, horizon and empirical basis.
- **Compute:** a falsifier that resolves by a date.
- **Compare:** this window's confidence against the layer's own distribution (relative), and
  against outcomes (absolute) — and say which kind is being quoted.
- **Challenge:** `confidence_score` here is **definitionally `independent_current_count / 13`**
  (enforced at `migrations/670_…:1203-1207`, computed at `ka_sangam.py:957`). That is a normalised
  count, not a probability. Quoting it as confidence without that sentence is the §N.7 item 5
  defect.
- **Overturned by:** the outcome at `evaluation_date`; or discovery that the counted currents were
  not independent.
- **Honest partial:** "Confidence label 'moderate' = 4 independent currents out of a 13-slot
  vocabulary, on an explicitly uncalibrated basis (`tier_basis='relative_uncalibrated'`, 100% of
  rows). It is not a probability and no outcome data yet bears on it."

### Q-K08 (CONTINUITY) — "What is the trajectory of my career pressure — rising, cresting, or decaying — not the snapshot?"
- **Know:** a time series, not a set of windows; its sampling grain; what is interpolated.
- **Compute:** first derivative over a grain coarse enough to be meaningful and fine enough to be
  actionable.
- **Compare:** this decade against the last, on the same construction.
- **Challenge:** a trajectory computed from a term that is structurally absent is a trajectory of
  the remaining terms. If the transit term is zero everywhere, the "waveform" is a dasha step
  function, and its "crest" is a lord change.
- **Overturned by:** the transit term becoming available and changing the shape.
- **Honest partial:** "Rising through 2029 — but on 2 of 3 declared components; the transit
  component is 0.0 on every one of the 92,412 rows for this chart because its source table is
  empty. This is a dasha × promise curve, not a dasha × transit × promise curve." **This is exactly
  today's unstated state — see §3.3.**

### Q-K09 (ELECTION) — "I need to sign in the next 90 days. When?"
- **Know:** the undertaking's real constraints; personal suitability (tārā-bala, target graha);
  general calendar quality; the vetoes.
- **Compute:** a search over candidate instants with hard vetoes applied as vetoes, not as penalties.
- **Compare:** best available vs best possible — "the best window in your range" is not "a good
  window".
- **Challenge:** calendar correctness, personal suitability and outcome expectation are three
  different claims (`REGISTER:156` / `ka_muhurta_seva`'s own disposition).
- **Overturned by:** a hard veto found after the fact; a constraint the caller did not state.
- **Honest partial:** "Every candidate in your 90 days carries a personal-star veto — no clean
  election exists in this range" — which `elect.ts:288-290` already emits verbatim. This is the
  portfolio question Kāla answers *best* today.

### Q-K10 (ELECTION, NEGATIVE) — "…and if there is genuinely no good time, say so."
- **Know:** the difference between "searched and found nothing" and "could not search".
- **Compute:** an empty-with-reason, classified.
- **Challenge:** an honest empty must be machine-distinguishable from a broken pipeline.
- **Honest partial:** the *only* acceptable answer is a classified empty. `query_temporal_activation.ts:406-465`
  does this properly (three distinct `empty_reason` branches, one of which names the unbuilt writer
  by asset id); `elect.ts:1078-1106` carries `empty_reason` through to the envelope. **This is the
  layer's strongest existing discipline.**

### Q-K11 (RECURRENCE) — "This pattern fired in 2003 and 2011. When does it fire again, and is that the complete list?"
- **Know:** every in-life interval in which the predicate holds, birth-forward — the *complete* set.
- **Compute:** recurrence enumeration with an explicit coverage statement.
- **Compare:** the returned list against the underlying clock table's own count.
- **Challenge:** any cap on the returned list must be disclosed as a cap. A truncated recurrence
  list presented as complete is the §N.8 defect class applied to coverage.
- **Overturned by:** finding a qualifying period outside the returned set.
- **Honest partial:** "Six occurrences found; the resolver caps at 8, and 6 < 8, so this list is
  complete." Today the cap exists (`date_resolver.py:417,500`) and is **not** disclosed — §3.1.

### Q-K12 (DISAGREEMENT / INDEPENDENCE) — "You said four things point at 2029. Are those four actually four?"
- **Know:** the provenance of each piece of evidence — which asset produced it, and what that asset
  read.
- **Compute:** a de-correlation that is aware of *asset provenance*, not only of factor vocabulary.
- **Challenge:** `ka_sangam`'s `independent_current_count` de-correlates within one row's `currents`
  dict and has no input from which asset produced each current (`services/ka_sangam/engine.py:850-889`
  — verified this session, and independently in `_work/T5.md` Tension 6).
- **Overturned by:** tracing two "independent" corroborators to one producer.
- **Honest partial:** "Four currents, ICC 3.0 after within-row de-correlation. I cannot tell you
  whether the *assets* that supplied them are independent — no detector exists for that."

### Q-K13 (BOUNDARY) — "Am I in a sandhi right now, and how should that change what I do this week?"
- **Know:** exact period boundaries with time-of-day; L1's `sandhi_flag` and
  `sandhi_with_next_dasha_lord`.
- **Compute:** boundary proximity in hours.
- **Challenge:** closed-vs-half-open matters *here specifically*: on a boundary date, a
  closed-closed membership test puts the native in two periods at once.
- **Overturned by:** the timezone convention under which the boundary was computed.
- **Honest partial:** "You are within 3 days of an AD boundary by date; the hour-level answer exists
  in L1 (`end_iso`) but the L3 path you are on reads only `end_date`." — §3.1.

### Q-K14 (COMPARISON, COHORT) — "Is this an unusual period for me, or an ordinary one?"
- **Know:** the within-chart distribution of window strength, and the recurrence interval (rarity).
- **Compute:** a percentile within *this* chart, clearly scoped to this chart and this build.
- **Compare:** against the chart's own history, not against other charts.
- **Challenge:** a "relative" label computed over one build's batch is not comparable across
  builds. `ka_sangam.py:892-894` computes `relative_confidence_labels(batch_scores)` over `deduped`
  — this build's batch.
- **Honest partial:** "Top decile of this chart's own convergence distribution *as of this build*.
  Re-ranked on every rebuild."

### Q-K15 (NEGATIVE / HONEST EMPTY) — "Is there genuinely nothing in Q3 2027, or is something not built?"
- **Know:** row presence, dated-row presence, filter compatibility, and upstream build state — as
  four separable facts.
- **Compute:** a bounded classification query, not a guess.
- **Challenge:** `state='lit'` on `asset_throughput` is not evidence rows exist (§N.8 instance 4);
  the canonical chart is the live proof — `asset_throughput` records `ka_kalasutra` wrote 335,403
  rows on 2026-08-13 and the table holds 0 today [BASELINE: `KALA_PROVING_JOURNEYS_BASELINE_v1_0.md`].
- **Honest partial:** the three-branch classification at `query_temporal_activation.ts:443-465`,
  which distinguishes (a) no rows at all → names `ka_kalasutra` as possibly unbuilt, (b) rows exist
  but undated → names R-45/WP-2.1, (c) rows exist and are dated but outside the filter → says so and
  points at the forward-window fallback.

### Q-K16 (CONTINUITY / RETRODICTION) — "You predicted a promotion in 2019 and it did not happen. Re-derive that window without hindsight and tell me what you now see."
- **Know:** the frozen original claim; the event-free structural/temporal re-analysis; the admitted
  outcome log.
- **Compute:** a re-derivation that does not read the outcome.
- **Compare:** re-derived vs frozen, plus unmatched activations and non-matching events on both sides.
- **Challenge:** the re-derivation must be reproducible. If the resolver's primary-window selection
  depends on `date.today()` (it does — `date_resolver.py:473`), a "re-derivation" run today is not
  the same computation that ran in 2019.
- **Overturned by:** the frozen claim not actually being frozen (a rebuildable projection table that
  rewrites issued history — `REGISTER:156`'s own objection).
- **Honest partial:** "Re-derivation is not currently reproducible: the primary window is selected
  relative to the build date. I can give you the full matched-period listing, which is build-date
  independent, and flag the primary as non-reproducible."

---

# §2. QUESTION → CAPABILITY → ASSET MAP

**Six states, reported independently — deliberately NOT collapsed into a percentage:**

| state | what it asserts | what would have to fail for it to read false |
|---|---|---|
| **PRESENT** | the code/table for the capability exists | file absent / table absent |
| **QUALIFIED** | its method, conventions, approximations and jurisdiction are adjudicated and disclosed | an undisclosed cap, default, or unimplemented declared input |
| **CONSUMED** | some other asset or surface actually reads *this asset's own output* | grep finds no reader of its target table |
| **EFFECT-TRACEABLE** | the consumer's answer observably changes as a function of this asset's rows | the answer is identical with the rows removed |
| **SERVED** | it reaches a consumer-facing tool response | no registered tool returns it |
| **VALUE-EVALUATED** | the delivered answer has been judged against what the native asked | no evaluation record |

Legend: **Y** / **N** / **CNV** (could not verify, with reason). `—` = not applicable.

| # | Capability required | Owning `ka_*` asset(s) | PRES | QUAL | CONS | EFF-TR | SERV | VAL-EV |
|---|---|---|---|---|---|---|---|---|
| Q-K01 | multi-system clock membership at an instant, with applicability | `ka_dasha_kala`, `ka_avadhi` | Y | **N** — `ka_dasha_kala` writes no table; the live path `call_dasha_eligibility` queries raw L1 `chart_dashas` [BASELINE F5] | **N** for `ka_dasha_kala` (own output unconsumed); Y for `ka_avadhi` (`query_dasha_dossier`) | CNV | Y (`kala_now_get`, `query_active_dashas`) | N |
| Q-K02 | mechanism → predicate → interval resolution over the *whole* mechanism set | `ka_yojaka` → `ka_kalasutra` | Y | **N** — 8-window cap undisclosed (§3.1); 79 unresolved MSR refs [BASELINE F7 §4a] | Y (`ka_kalasutra` reads `kala_activation_predicates`) | **N** for canonical chart — `kala_activation`=0 [VERIFIED-E] | Y (surface exists) | N |
| Q-K03 | exact ISO interval bounds + sandhi | L1 `chart_dashas`; L3 `ka_dasha_kala` | Y | **N** — L3 reads the `date` columns, not `start_iso/end_iso` (§3.1) | Y | Y | Y (`kala_dasha_sandhi_get`) | N |
| Q-K04 | cross-domain interval intersection + a stated dominance rule | `ka_taranga` (domain waveform), `ka_sangam` (domain on convergence) | Y | **N** — no dominance rule; scales incommensurable (§0.1 fact 2) | Y (`query_activation_waveform`) | **N** — transit term 0.0 on all rows (§3.3) | Y | N |
| Q-K05 | time-symmetric head-to-head window comparison | `ka_tulana` (`KaTulanaService.compare`) | Y (`services/ka_tulana/ranker.py:307-389`) | **N** — composite includes a proximity term that floors past windows at 0.05 (`ranker.py:204-216`) | **N** — only caller is the self-test probe (`pipeline/orchestrator/service_probes.py:841-845`); grep over `platform/python-sidecar`, `platform-mcp/src`, `platform/src` (`.py`/`.ts`, excluding the service's own dir and tests) found no other caller | N | **N** | N |
| Q-K06 | cross-clock agreement/disagreement as a first-class output | **NO SINGLE OWNING ASSET** — partial, at the serving layer only | partial | — | — | — | partial (`explain.ts:423-447`, `:545-592`; `promise_gate.ts:183`) | N |
| Q-K07 | confidence with units, denominator, horizon, basis | `ka_sangam` | Y | **Y, unusually** — `tier_basis='relative_uncalibrated'` is stored per row and `ka_bhavishya_lekha.py:552-590` refuses probability language unless `tier_basis='calibrated'` | **N inside L3** — `independent_current_count` is read by *no* `ka_*` consumer (§3.2) | N | partial (`query_convergence_windows.ts:122-125` serves it; the composite surfaces do not) | N |
| Q-K08 | trajectory / first derivative over a stated grain | `ka_taranga` | Y | **N** — 3-term formula silently degrades to 2 terms (§3.3) | Y (`query_activation_waveform.ts`) | **N** — the served curve is a function of 2 inputs, one of them binary | Y | N |
| Q-K09 | election search with hard vetoes | `ka_muhurta_seva` | Y | CNV — `score_muhurat()` primitive not independently re-confirmed [BASELINE T1 Frontier] | Y (`muhurta_finder.ts`) | Y | Y (`kala_elect_get`) | N |
| Q-K10 | classified honest-empty on election | `ka_muhurta_seva` + `elect.ts` | Y | Y | Y | Y | Y (`elect.ts:288-290, 1078-1106`) | N |
| Q-K11 | complete recurrence enumeration with coverage statement | `ka_kalasutra` / `services/ka_temporal` | Y | **N** — `max_windows=8` default, undisclosed, and contradicted by the writer's own comment (§3.1) | Y | N (empty for canonical chart) | Y | N |
| Q-K12 | provenance-aware de-correlation | **NO OWNING ASSET.** `ka_sangam`'s detector is vocabulary-scoped, not provenance-scoped | partial | **N** | **N** | **N** | **N** | N |
| Q-K13 | sandhi / boundary proximity with time-of-day | `ka_dasha_kala`, `kala_dasha_sandhi_get` | Y | **N** — date-grain only on the L3 path (§3.1) | Y | Y | Y | N |
| Q-K14 | within-chart rarity/percentile, build-scoped | `ka_sangam` (`confidence_label_relative`) | Y | partial — batch-relative, and the batch scoping is not surfaced | **N** — no `ka_*` consumer reads `confidence_label_relative` | N | partial | N |
| Q-K15 | classified honest-empty on activation | `ka_kalasutra` + `query_temporal_activation.ts` | Y | Y | Y | Y | Y (`:406-465`) | N |
| Q-K16 | reproducible, hindsight-free re-derivation vs a frozen claim | `ka_bhavishya_lekha` (frozen claim), `services/ka_temporal` (re-derivation) | Y | **N** — re-derivation is build-date dependent (`date_resolver.py:473`); frozen claim table is rebuildable (`REGISTER:156`) | Y | **N** — `kala_bhavishya`=0 for canonical chart [VERIFIED-E] | Y | N |

### §2.1 Questions with NO owning asset — the layer's real gaps

Two, and they are the two that matter most for the native's stated goal of "synergistic" elevation:

**GAP-E1 — Cross-clock agreement/disagreement has no owning asset.** Q-K06. Real dissent machinery
exists, but *only at the serving layer and only pairwise*: `explain.ts:433-447` folds a KP voice
into `reading.dissent`; `explain.ts:545-592` grades gochara as `concurs` / `dissents` /
`insufficient_data`; `promise_gate.ts:183` serves both sides of a tier-vs-promise-chain
disagreement rather than reconciling. No `ka_*` asset produces agreement/disagreement as stored,
queryable data. The consequence: disagreement is re-derived per surface, is inconsistent between
surfaces, and cannot be asked about directly ("show me every period where my clocks disagree").
Evidence of the inconsistency: `priority.ts:280` and `priority.ts:316` **hardcode `dissent: []`** —
the exact defect class that was found and fixed in `ahead.ts:1705-1722` (F-110: "`dissent: []` was
hardcoded — an assertion that NO system on this server disagrees, emitted while `pact_query` held a
denial on 63 cited L1 facts"). `story.ts:609` and `explain.ts:302` carry the same literal. Three
surfaces still assert "nothing disagrees" with no detector behind the assertion (§N.8).

**GAP-E2 — Provenance-aware de-correlation has no owning asset.** Q-K12. Detailed in §3.2.

A third, weaker gap: **no asset owns "dominance" for Q-K04.** Two domain streams can be shown to
coincide; nothing states which governs. I mark this a design gap rather than a defect because no
document I read claims the capability.

---

# §3. THE LAYER'S INTERNAL SEAMS — where information dies between Kāla's own assets

Four producer→consumer paths traced inside L3, each with file:line. The seams are ordered by how
much they cost the portfolio above.

---

## §3.1 SEAM 1 — `chart_dashas` (L1) → `services/ka_temporal` → `ka_kalasutra` → `kala_activation`
### Three losses on one path: timezone precision, recurrence completeness, and reproducibility

**(a) Timezone/precision conflation at the layer's front door.**

L1 `chart_dashas` carries *both* grains [VERIFIED-E, `information_schema.columns`]:
`start_date:date, end_date:date, start_iso:timestamp with time zone, end_iso:timestamp with time zone`,
plus `sandhi_flag:boolean`, `next_dasha_start_iso`, `is_truncated_at_window_start/end`.

The L3 loader reads only the coarse pair:

```
services/ka_temporal/date_resolver.py:349
        SELECT lord_graha, level_n, start_date, end_date
```

Everything downstream in L3 is `datetime.date` arithmetic (`date_resolver.py:39`
`from datetime import date, timedelta`), and `kala_activation`'s own columns are
`activation_start:date, activation_end:date, activation_peak_date:date` [VERIFIED-E]. The
timezone-resolved instant, the sandhi flag and the truncation flags are all available at L1 and
none survive into L3. **Q-K03 and Q-K13 are answerable at L1 and unanswerable at L3** — an
inversion of the layer's own purpose ("precise intervals", STRATEGIC_LEDGER:110).

**Closed-vs-half-open:** membership is tested closed-closed —
`date_resolver.py:476` `current_tier = [p for p in matched_all if p.start <= today <= p.end]`, and
again in `ka_taranga.py:157` `if row["ds"] <= m <= row["de"]`. Adjacent dasha periods that share a
boundary date therefore both match on that date. Whether `chart_dashas` emits shared boundary dates
was **COULD NOT VERIFY** — I did not query for adjacent-period boundary equality, to stay inside
budget. The closed-closed test is stated as fact; the double-membership consequence is stated as
conditional on that.

**(b) Recurrence truncated at 8, undisclosed, and contradicted in-file.**

```
services/ka_temporal/date_resolver.py:417      max_windows: int = 8,
services/ka_temporal/date_resolver.py:500      matched = matched[:max_windows]
services/ka_temporal/date_resolver.py:575      for p in matched:          # period_windows built from the TRUNCATED list
```

`ka_kalasutra.py:109-118` calls `resolve_activation_windows(...)` **without passing `max_windows`**,
so every predicate on every chart is capped at 8 emitted periods. A mechanism whose constituent
lord holds 20+ in-life MD/AD periods over an 80-year life returns 8.

The writer's own comment asserts the opposite:

```
pipeline/orchestrator/writers/ka_kalasutra.py:142-144
    # OWN activation_start/end/peak, so a date-range query against
    # kala_activation genuinely finds every period the dasha table holds,
    # not just whichever one was elevated to "primary" at build time.
```

The CR-109 fix this comment describes is real and good — it replaced one collapsed row per
predicate with one row per matched period. But "every period the dasha table holds" is true only up
to 8. **This is §N.8 exactly: a completeness claim with no detector that could report it false.**
`kala_activation` carries no `truncated` flag and no matched-period count, so a consumer cannot
distinguish "6 occurrences, complete" from "8 of 23, capped." **Q-K11 is unanswerable as stated.**

**(c) Reproducibility: the primary window is a function of the build date.**

```
services/ka_temporal/date_resolver.py:473
    today = as_of_date if as_of_date is not None else date.today()
```

`ka_kalasutra.py:109-118` passes no `as_of_date`. The docstring is candid that this drives *which*
matched period is elevated to the single bounded `activation_start/end/peak`
(`date_resolver.py:441-455`). The consequence is not a bug — the WP-S4-fix2 change it documents was
a genuine fix — but it is an unrecorded property: **`kala_activation.activation_start` for a given
`(chart, signal, ayanamsha)` is not a function of the chart alone.** Rebuild in six months and the
primary window moves. Nothing in the row records the `as_of` it was built under (`computed_at`
records *when*, not that the value depends on when). **Q-K16's "re-derive without hindsight" cannot
be honoured**: the re-derivation is anchored to the day it runs.

**(d) What the seam drops on the convergence side.**

`ka_kalasutra` reads `kala_convergence` and keeps almost nothing:

```
pipeline/orchestrator/writers/ka_kalasutra.py:73
        SELECT signal_id, mode, peak_date, orb_strength, convergence_score
```

versus `kala_convergence`'s actual 21 columns [VERIFIED-E], which include
`constituent_factors:jsonb, rarity_years, confidence_score, confidence_label,
independent_current_count, is_off_dasha_discovery, horizon_tier, domain,
confidence_label_relative, tier_basis`.

Then it keeps only the single best-scoring row per signal:

```
ka_kalasutra.py:82-90
    if sig_id not in convergence_map or (row['convergence_score'] or 0) > (…['convergence_score'] or 0):
        convergence_map[sig_id] = {'mode':…, 'peak_date':…, 'orb_strength':…, 'convergence_score':…}
```

— so if `ka_sangam` found the same signal converging in three separate windows (Mode A in 2027,
Mode C in 2031, Mode D in 2033), **two of the three are discarded here, permanently.** The strategy
document's own requirement for this asset is "retain all qualified recurrences / multiple
convergence contributions" (`STRAT:286`); the code retains one.

And then even `mode` — fetched at `:73`, stored in the map at `:84` — is **never written**. The
INSERT at `ka_kalasutra.py:189-199` writes `orb_strength, convergence_score` and nothing else from
convergence. `kala_activation` has no `mode`, no `tier_basis`, no `independent_current_count`, no
`resolution_source` column [VERIFIED-E schema]. The resolution provenance survives only as a
substring inside a free-text field:

```
ka_kalasutra.py:167-170
    f"ka_kalasutra:v1.0:signal={sig_id_str[:8]}:src={pw['resolution_source']}:period={idx}"
```

**A consumer wanting to know whether `activation_peak_date` is a real convergence peak or the
arithmetic midpoint of a 16-year mahadaśā (`date_resolver.py:404-405`, `(end-start).days // 2`)
must parse a citation string.** That is rich structure reduced to one scalar plus prose — §N.6
item 4 inverted ("density signalling is data, not narration").

---

## §3.2 SEAM 2 — `ka_sangam` → (`ka_kala_darshana`, `ka_vighnakara`, `ka_taranga`, `ka_bhavishya_lekha`, `ka_jivana_parva`)
### The de-correlation detector is produced, stored, and read by nothing in L3

**The detector exists and is real.** `services/ka_sangam/engine.py:850-889`,
`independent_current_count(currents)`, docstring at `:852` "RATIFIED I-22: discount correlated
evidence", with hand-written coupling rules (dasha+nakshatra_overlay → 1 not 2; panchanga+transit →
+0.5; ashtakavarga coupled to constituent_lord_transit). It is well tested
(`tests/test_u3_convergence_currents.py:532-584`, `tests/l3/test_ka_sangam.py:212-240`).

**It is stored.** `ka_sangam.py:931` `icc = independent_current_count(currents)`, written to
`kala_convergence.independent_current_count:smallint` (`ka_sangam.py:940`), and `confidence_score`
is *definitionally* derived from it — enforced as a DB-level integrity contract:

```
platform/migrations/670_nirmana_l3_w3_integrity_contracts.sql:1201-1207
  -- (f) §N.7 item 3: confidence_score is not an independent number -- the writer sets it to
  -- round(min(1.0, icc/13), 4) (ka_sangam.py:957). …
  AND NOT EXISTS (SELECT 1 FROM kala_convergence
    WHERE abs(confidence_score - round(least(1.0, independent_current_count / 13.0)::numeric, 4)) > 1e-9)
```

**And within L3 it is read by nothing.** [VERIFIED-E] Repo-wide grep
(`grep -rn independent_current_count platform platform-mcp 00_ARCHITECTURE --include='*.ts' --include='*.py' --include='*.sql'`,
node_modules excluded) returns exactly: the producer (`ka_sangam.py`), its tests, two migrations
(670 = the integrity contract, 980 = the output-digest spec), **one L4 consumer**
(`pipeline/orchestrator/writers/ph_nimitta.py:159,329`), and one serving capability
(`query_convergence_windows.ts:122-125`). **Zero `ka_*` consumers.** The measurement leaps the
entire L3 integrator tier and lands in L4.

Concretely, at the first downstream hop:

```
pipeline/orchestrator/writers/ka_kala_darshana.py:23-32
    SELECT kc.convergence_id, kc.signal_id, kc.mode,
           kc.peak_date, kc.window_start, kc.window_end,
           kc.convergence_score, kc.confidence_label,
           kc.orb_strength, kc.rarity_years
    FROM kala_convergence kc
    WHERE kc.chart_id = %s
    ORDER BY kc.convergence_score DESC NULLS LAST
    LIMIT 750
```

`independent_current_count` and `constituent_factors` are not selected. `confidence_label` *is*
selected — and then used **only inside the narrative string** (`ka_kala_darshana.py:110-118`
`_build_narrative(..., conf_label=conf_label, ...)`); it is not among the INSERT columns
(`:132-141`), and `kala_darshana` has no confidence column [VERIFIED-E]. **The layer's only
independence measurement survives one hop as prose and zero hops as data.**

**Why this is the hazard the prompt named.** Per `_work/T5.md` Tension 6 (which I re-verified
against `F3.md`'s dependency table), `ka_sangam` is the common ancestor of five of the eight L3
integrators: `ka_kala_darshana` reads it directly *and* reads `ka_vighnakara`, which itself reads
`ka_sangam`; `ka_bhavishya_lekha` reads `ka_kala_darshana` + `ka_vighnakara` + `ka_sangam` (three of
four inputs, one producer); `ka_jivana_parva` reads `ka_kala_darshana` + `ka_sangam` + `ka_yojaka`
(and `ka_yojaka` feeds `ka_sangam`). Each of these composes a `ka_sangam` score with something that
is itself a `ka_sangam` score, and none of them can see how many independent currents formed
either leg, **because the column that says so is not in their SELECT and not in their output
schema.** Q-K12 is structurally unanswerable.

**Two further independence defects inside the detector itself, both verified:**

1. `ka_sangam.py:907` `'transit': mode in ('A', 'B')` — the `transit` current is a *structural
   constant of the row's mode*, not a measured observation, yet it contributes a full 1.0 to the
   independence count (`engine.py:891-893`). Every Mode A/B row gets a free independent current.
2. `ka_sangam.py:901-930` builds the entire `currents` dict from `cf = w.get('constituent_factors')`
   — **the same dict from which `convergence_score` was computed upstream.** So `convergence_score`
   (40% weight in `ka_tulana`'s composite) and `confidence_score` (20% weight, = icc/13) are two
   functions of one input dict. They are not independent axes. I did **not** trace the
   `convergence_score` formula itself inside `services/ka_sangam/engine.py` — **COULD NOT VERIFY**
   the exact functional overlap; what is verified is that both derive from the same
   `constituent_factors` payload on the same row.

**And a third, structural:** `migrations/670:1194-1199` records that Modes C and D "consult no point
transit and no second current, so the writer hard-sets `orb_strength = 1.0` … and
`independent_current_count` floors at 1." [VERIFIED-E] those two modes are 17,762 of 20,497 rows
(87%). So for 87% of the convergence layer, `confidence_score` is the constant 1/13 ≈ 0.0769 and
`orb_strength` is the constant 1.0 — **two "strength" signals that are, for most of the data,
constants.** Any downstream ranking that sorts on them is sorting on nothing for those rows.

---

## §3.3 SEAM 3 — `ka_sangam` + `bodha_pratijna` → `ka_taranga` → `kala_taranga` → `query_activation_waveform`
### A three-term formula that silently becomes a two-term formula, with a measured-looking zero standing in for an unevaluated term

This is the seam with the largest live blast radius, because `kala_taranga` is one of only two Spine
tables **actually populated for the canonical chart** (92,412 rows [VERIFIED-E]) — so it is a
surface the native can reach today.

**The declared formula** (`pipeline/orchestrator/writers/ka_taranga.py:13-21`):
> 1. `dasha_contribution` … 2. `transit_contribution` — mean convergence_score of `kala_convergence`
> windows overlapping this month … 3. `promise_contribution` — `bodha_pratijna` grade/10.
> `activation = harmonic_mean(dasha, transit, promise)`.

**The transit source is empty for this chart.** `ka_taranga.py:107-118` selects from
`kala_convergence`, which holds **0 rows for the canonical chart** [VERIFIED-E §0.1]. So
`transit_windows = []`, `transit_by_month_domain = {}`, and:

```
pipeline/orchestrator/writers/ka_taranga.py:197
                t_contrib = sum(t_vals) / len(t_vals) if t_vals else 0.0
```

**The zero is then silently dropped from the mean, not treated as evidence of absence:**

```
platform/python-sidecar/services/taranga_kernel/kernel.py:45-52
def harmonic_mean(values: list[float]) -> float:
    pos = [v for v in values if v > 0]
    if not pos: return 0.0
    if len(pos) == 1: return pos[0]
    return len(pos) / sum(1.0 / v for v in pos)
```

A zero term reduces both the numerator (`len(pos)`) and the denominator. A 3-term harmonic mean
becomes a 2-term harmonic mean with **no record that a term was dropped**.

**Verified live on the canonical chart** [VERIFIED-E]:

```sql
SELECT round(activation,6), components->>'dasha_contribution', components->>'transit_contribution',
       components->>'promise_contribution', count(*)
FROM kala_taranga WHERE chart_id='482012f1-…' GROUP BY 1,2,3,4 ORDER BY 5 DESC LIMIT 15;
```

| activation | dasha | **transit** | promise | rows |
|---:|---:|---:|---:|---:|
| 0.075000 | 0.15 | **0.0** | 0.0 | 16,772 |
| 0.500000 | 1.0 | **0.0** | 0.0 | 3,160 |
| 0.850575 | 1.0 | **0.0** | 0.74 | 1,306 |
| 0.666667 | 1.0 | **0.0** | 0.5 | 1,228 |
| … (every remaining group in the top 15) | 0.15 or 1.0 | **0.0** | various | … |

Aggregate: 92,412 rows, **0 rows with `activation = 0`**, mean 0.4871, max 0.9565.

Three things follow, all verified:

1. **`transit_contribution` is 0.0 on the entire canonical-chart waveform.** The "activation
   waveform" — the layer's trajectory/continuity asset, the answer to Q-K08 — contains no transit
   information whatsoever for this chart.
2. **`dasha_contribution` is a two-valued indicator, not a measure.** `ka_taranga.py:195`
   `d_contrib = 1.0 if domain in lord_domains else 0.15` — a static graha→domain lookup
   (`services.taranga_kernel.kernel.GRAHA_DOMAINS`), 1.0 or 0.15, nothing in between.
3. **Therefore the served `activation` scalar is, for this chart, a function of exactly two inputs,
   one of them binary**: a harmonic mean of {0.15 or 1.0} and the domain's mean pratijñā grade — or,
   where no pratijñā grade exists (20k of the rows above), simply `d_contrib / 2` (the
   `else (d_contrib + t_contrib)/2.0` branch at `:199-200` with `t_contrib = 0`), giving exactly the
   observed 0.075 and 0.500 values. A row reading `activation = 0.85` reads as a strongly-supported
   month; it is `harmonic_mean(1.0, 0.74)` over a lord-domain lookup and a promise grade.

**`components.transit_contribution = 0.0` is the "measured-looking value standing in for an
unevaluated term" defect verbatim** (§N.7 item 6). A consumer cannot distinguish "transit was
evaluated and found nothing" from "the transit source table has no rows for this chart." The
correct emission is `null` with a reason, not `0.0`.

**Additional interval losses on the same path:**

- **No duration weighting.** `ka_taranga.py:168`
  `for m in _month_range(max(ws, _WAVEFORM_START), min(we, _WAVEFORM_END))` — a convergence window
  spanning 2026-01-31→2026-02-01 (two days) contributes its full score to *both* January and
  February, exactly as a window spanning all of January would. `kernel.py:77-87` `month_range`
  yields first-of-month dates inclusive at both ends. Intervals are rounded to month membership
  before any computation.
- **Month-start-only lord attribution.** `ka_taranga.py:155-158`
  `def _lord_for_month(m): for row in vimsh_md: if row["ds"] <= m <= row["de"]: return …` — tests
  the *first of the month* only, and returns the **first matching row**, not the longest-overlapping
  one. A mahādaśā changing on the 20th gives the whole month to the outgoing lord. Combined with
  the closed-closed test, a month-start falling exactly on a boundary resolves by result-set order.
- **Same-signal double counting.** `transit_by_month_domain` appends one sample per
  `kala_convergence` row (`:168-169`), then means them (`:197`). `kala_convergence` holds multiple
  rows per `signal_id` by construction — [VERIFIED-E] Mode D has 16,892 rows over 30 distinct
  signals, ~563 rows per signal. One signal therefore contributes ~563 samples to the mean while a
  single-window signal contributes one. The "mean convergence score for this month" is dominated by
  whichever signals `ka_sangam` happened to emit most rows for. `ka_kalasutra` de-duplicates to one
  row per signal at `:82-90`; `ka_taranga` does not. **The same upstream evidence is counted once in
  one consumer and hundreds of times in the other.**

---

## §3.4 SEAM 4 — `ka_kalasutra` → `call_priority_ranking` → `kala_priority_get`
### The layer's "what matters most" view contributes only a date filter

`kala_priority_get` / `kala_priority_ranking_get` describe themselves as wrapping the `ka_tulana`
service — `priority.ts:330-331`: "Wraps the same **ka_tulana priority-ranking service**
`kala_priority_ranking_get` calls"; the capability description at
`call_service_wrappers.ts:525` says "(ka_tulana service)".

**It does not call `ka_tulana`.** The handler is inline SQL
(`platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts:670-712`):

```sql
(m.computed_salience * COALESCE(a.orb_strength, 1.0) *
  (CASE WHEN m.signal_headline_text ILIKE '%dignity%neutral%' THEN 0.3 ELSE 1.0 END)
) AS priority_score
FROM bodha_msr_signals m
JOIN kala_activation a ON m.signal_id = a.signal_id AND a.chart_id = m.chart_id
  AND a.ayanamsha_id = m.ayanamsha_id
WHERE … AND a.activation_end >= $3::date AND a.activation_start <= $4::date
```

`m.computed_salience` is an **L2 Bodha** value. The code's own measured note at
`call_service_wrappers.ts:688-697` records that `kala_activation.orb_strength` is NULL on
**669,964 of 672,551 rows (99.6%)**, and that the factor is now correctly *dropped* rather than
zero-filled when absent (with an `orb_strength_available` flag — genuinely good §N.6 practice).

**The consequence is the value-model point:** on 99.6% of rows the served `priority_score` reduces
to `computed_salience × {1.0 or 0.3}`. **L3's entire contribution to the "of everything, what
matters most right now" answer is the date-overlap predicate in the WHERE clause.** The ranking
itself is L2's salience ordering, re-served under an L3 tool name. No qualified mechanism, no
interval strength, no recurrence, no obstruction, no independence — none of DP08's obligations
reach this answer.

Meanwhile `ka_tulana`'s actual I-11 composite — 40% convergence + 25% rarity + 20% confidence + 15%
proximity (`services/ka_tulana/ranker.py:38-45`, `:218-237`) — is computed nowhere in production.
Its `compare()` entry point (`ranker.py:307-389`), which produces a `CompareVerdict` with a named
decisive factor and a dissonance-aware recommendation, has **no caller outside the self-test probe**
(`pipeline/orchestrator/service_probes.py:838-846`). [VERIFIED-E, with scope stated: grep over
`platform/python-sidecar`, `platform-mcp/src`, `platform/src` for `KaTulanaService|rank_windows|
attention_map|CompareVerdict`, excluding `services/ka_tulana/` itself and `tests/`/`*.test.*`. A
grep that finds no caller establishes only my search scope; I did not search compiled artefacts,
notebooks, or the `platform/scripts` tree.]

**This is the layer's single largest piece of orphaned value.** Q-K05 (comparison) and Q-K14
(within-chart rarity) have a built, tested, documented implementation that no consumer can reach.

And when it *is* reached, two design properties would still block Q-K05:
- `ranker.py:204-206`: `if days < 0: return 0.05  # past window`. Every historical window is floored
  at the proximity minimum, so a 15%-weighted factor systematically favours the future. **A
  recency-weighted comparator cannot answer "was 2019 stronger".**
- `ranker.py:191-195`: `rarity_years is None → 0.5 neutral`; `ranker.py:222`
  `_CONFIDENCE_NUMERIC.get(w.confidence_label, 0.2)`. Both are invented defaults (§N.7 item 6) — and
  since `kala_activation` (the table the live path actually reads) carries **no** `rarity_years` or
  `confidence_label` column [VERIFIED-E], any future wiring of `rank_windows` over that table would
  give every row `rarity_norm = 0.5` and `confidence = 0.2`, i.e. 45% of the composite weight
  contributed by two constants — while the rationale string at `ranker.py:243-245` would report
  `rarity_norm=0.50 (~unknownyr cycle, weight 25%)` as though it had been measured.

---

## §3.5 SEAM 5 (brief) — `ka_sangam` → `ka_kala_darshana`: the top-750 cut is a mode filter

```
ka_kala_darshana.py:29-31    ORDER BY kc.convergence_score DESC NULLS LAST  LIMIT 750
```

No query, domain, horizon or date parameter — a global score cut taken *before* the obstruction
join (`:38-44`). Combined with [VERIFIED-E §0.1 fact 2] — Mode C scores start at 0.70 while Mode A/B
cap at 0.3805 — **the top-750 is structurally all Mode C.** The writer's own file says so:

```
ka_kala_darshana.py:192-193
    # … Measured live: ka_sangam's top-750 intake is 100% Mode C, so every served row
    # carried the wrong mode description.
```

That comment was written to justify fixing a *label*; the same measurement condemns the *cut*. Two
consequences: (a) every window `ka_kala_darshana` ever presents is a sign-ingress trigger, and
daśā-aligned (Mode A) and anomaly-sweep (Mode B) windows are invisible at this surface by
construction; (b) an obstruction attached to a Mode A window is never evaluated, because the window
never enters the join. **Q-K06's "which clocks disagree" is pre-decided by a LIMIT.** `REGISTER:155`
already names this ("global top-750 … is not complete personalized search"); `_work/T5.md` Tension 5
confirms the NULL→0.5 half was dispositioned in place and this half was not. Lane E adds the
mechanism: it is not merely incomplete, it is **systematically biased toward one mode**, and the
bias is invisible because `kala_darshana` has no `mode` column [VERIFIED-E].

---

# §4. THE SYNERGY CASE — capabilities that exist only between assets

Per-asset review cannot see these. Each is stated as: the emergent capability, the contract that
would have to exist between which assets, and what would prove it works (a *proposed* test — none of
these has been executed).

---

### SYN-1 — Cross-clock agreement/disagreement as stored, queryable data
**Emerges from:** `ka_dasha_kala` (multi-system clocks) × `ka_gochara`/`ka_vedha_gochara` (transit
and obstruction) × `ka_sudarshana_varsha` / `ka_tithi_pravesha` (annual frames) × `ka_kota_chakra`
(ring posture). Invisible per-asset: each asset is individually "correct" and the disagreement
exists only in the relation between them.

**Contract required:** a new stored relation — call it a *concurrence ledger* — keyed
`(chart_id, interval, clock_id, verdict ∈ {supports, opposes, silent, not_applicable}, jurisdiction,
method_version)`. Producers write one row per clock per interval; **`not_applicable` and `silent`
must be distinct values** (a clock with no adjudicated jurisdiction for this chart is not a clock
that stayed quiet). Consumers read agreement as data instead of re-deriving it pairwise per surface.

**What would prove it works (proposed test, not run):** take an interval where
`explain.ts:545-592`'s gochara voice currently returns `dissents` and `promise_gate.ts:183`
currently reports a tier/promise-chain divergence. The ledger must reproduce *both* dissents from
stored rows, with no surface-local recomputation, and `priority.ts` must then be able to populate a
non-empty `dissent` array from the same rows — closing the three hardcoded `dissent: []` sites
(`priority.ts:280,316`, `story.ts:609`, `explain.ts:302`) with a real detector rather than a literal.

---

### SYN-2 — One qualified window that composes daśā + transit + varṣa evidence with contradictions preserved
**Emerges from:** `ka_kalasutra` (interval) × `ka_sangam` (convergence currents) × `ka_vighnakara`
(obstruction) × `ka_sudarshana_varsha` / `ka_tithi_pravesha` (annual frame) × `ka_moorti_nirnaya` /
`ka_vedha_gochara` (modifiers). Invisible per-asset: today each contributes a scalar and the
composition is a product (`_compute_effective_score`, `ka_kala_darshana.py:146-155`:
`convergence_score × (1 − max override)`), which is precisely the operation that destroys the
contradiction — a strong support and a strong obstruction multiply to a middling number
indistinguishable from weak support with no obstruction.

**Contract required:** a window record that carries its *terms*, not their product:
`{interval, terms: [{asset_id, claim ∈ {supports, opposes}, magnitude, basis, provenance_root}],
composite, composite_rule_id, contradiction_present: bool}`. The `provenance_root` field is what
makes SYN-3 possible. `contradiction_present` must be computed (support and opposition both above
threshold), not inferred from the composite.

**What would prove it works (proposed test, not run):** construct a window with
`convergence_score = 0.9` and `max override_score = 0.9`. Today `effective = 0.09` and
`net_label = 'obstructed'` — a reader cannot tell it from `convergence 0.1, no obstruction`
(`effective = 0.1`, `net_label = 'auspicious_speculative'`). The contract passes when the two are
distinguishable in the served payload without parsing prose, and `contradiction_present` is true for
the first and false for the second.

---

### SYN-3 — Provenance-aware independence (closing GAP-E2)
**Emerges from:** `ka_sangam`'s detector × the DAG itself. Invisible per-asset because every
integrator is individually honest — each counts the currents it can see.

**Contract required:** two parts.
(a) **Propagation:** every L3 table whose rows derive from `kala_convergence` gains
`independent_current_count` (or an inherited `provenance_root_set`), so `kala_activation`,
`kala_darshana`, `kala_bhavishya` and `kala_taranga.components` can report it. Today none do
[VERIFIED-E schema]; the measurement reaches L4 `ph_nimitta.py:159` while skipping every L3
consumer.
(b) **Extension:** a second detector, `independent_producer_count(rows)`, that de-duplicates by
`provenance_root` before counting. Given five rows from `ka_kala_darshana`, `ka_vighnakara`,
`ka_bhavishya_lekha`, `ka_jivana_parva` and `ka_sangam`, it must return **1**, not 5.

**What would prove it works (proposed test, not run):** assemble a composed answer from those five
assets for one interval on a chart where `ka_sangam` has data (e.g. `1c826d5a-…`, which holds 17,957
`kala_convergence` rows [BASELINE F7]). The served envelope must report
`independent_producer_count = 1` and name `ka_sangam` as the shared root. A passing test must also
be *mutation-proof*: deleting the `ka_jivana_parva` leg must not change the count.

---

### SYN-4 — Recurrence + comparison: "this is the Nth occurrence, and here is how it ranks among them"
**Emerges from:** `ka_kalasutra` (complete recurrence set) × `ka_tulana` (`attention_map` /
`compare`) × `ka_sangam` (`rarity_years`, `confidence_label_relative`). Invisible per-asset:
`ka_kalasutra` knows *when* it recurs and nothing about relative strength; `ka_tulana` can rank but
has no recurrence input; `ka_sangam` computes rarity that neither reads.

**Contract required:** (i) `ka_kalasutra` must stop truncating at 8 or must emit
`matched_period_count` + `truncated: bool` (§3.1b); (ii) a `WindowInput` adapter that populates
`ka_tulana`'s four factors from *real* columns rather than defaults — which today is impossible
because `kala_activation` carries neither `rarity_years` nor `confidence_label`; (iii) a
**time-symmetric** comparison mode in `ka_tulana` that excludes `proximity_factor`, so past and
future occurrences are comparable (§3.4).

**What would prove it works (proposed test, not run):** ask Q-K05 on a chart with data. The answer
must name the occurrence index ("3rd of 6 in-life occurrences"), rank all six on a
proximity-excluded composite, and state the decisive factor. It fails today at step one: the
recurrence set is capped and the cap is undisclosed.

---

### SYN-5 — Honest-empty as a layer property, not a per-surface property
**Emerges from:** every writer × every serving surface. Invisible per-asset because each surface's
empty handling looks fine in isolation.

**What already works** (and should be the template): `query_temporal_activation.ts:443-465` runs one
bounded classification query and emits three distinct reasons, one of which **names the unbuilt
asset by id**. `elect.ts:1078-1106` carries `empty_reason` onto the envelope.

**Contract required:** a shared classifier — `classifyEmpty(table, chart_id, filters)` → one of
`{no_rows_for_chart(asset_id), rows_undated, filter_excluded, upstream_empty(upstream_asset_id),
incompatible_filters}` — used by every L3 surface, so that the *layer* answers Q-K15 uniformly
rather than one surface answering it well.

**What would prove it works (proposed test, not run):** the canonical chart is a ready-made fixture.
Five tables are empty for it right now [VERIFIED-E]. Every L3 tool called against it must return a
classified empty naming the responsible asset — and specifically, `query_activation_waveform` must
report that `transit_contribution` is unavailable rather than serving 92,412 rows of `0.0` as though
measured (§3.3). Today it does not.

---

# §5. WHAT KĀLA SHOULD STOP DOING

Ordered by how far the claim outruns the computation behind it.

### §5.1 STOP serving a zero that means "not evaluated"
`ka_taranga.py:197` (`t_contrib = … if t_vals else 0.0`) plus `kernel.py:47` (`pos = [v for v in
values if v > 0]`). The result, verified on 92,412 live rows [VERIFIED-E §3.3]: a term that was
never evaluated is stored as a measured-looking `0.0` and then dropped from the mean, producing a
confident-reading `activation = 0.85` from two inputs while the row's own `components` advertises
three. **Emit `null` with a reason and renormalise explicitly** — the codebase's own established
convention, quoted at `call_service_wrappers.ts:694-696`: "DROPPED from the product and the product
renormalised over the factors actually present — never zero-filled."

### §5.2 STOP presenting a global score cut as a personalised search
`ka_kala_darshana.py:29-31` (`ORDER BY convergence_score DESC LIMIT 750`, no query parameter). The
cut is [VERIFIED-E] a **mode filter**, because Mode C's score floor (0.70) exceeds Mode A/B's
ceiling (0.3805). Every served `kala_darshana` row is a sign-ingress trigger; daśā-aligned windows
are structurally excluded; obstructions on excluded windows are never evaluated. Either parameterise
the cut by the question, or disclose it as `mode=C only` — but stop calling the result the chart's
strongest windows.

### §5.3 STOP treating a keyword association as a temporal gate
`ka_bhavishya_lekha.py:471-497` (declaration) / `:499` (first-match loop): `_DOMAIN_KEYWORDS` maps `signal_type_id` → domain by substring
("career" ← any of `raja_yoga`, `amatyakaraka`, `tenth`, `karma`, `arudha`, `dasamsha`, `profession`,
`status`, `power`, `authority`), first match wins, falling through to `'general'`. That domain then
becomes the `domain` column on which a projection is filed, and — via `kala_convergence.domain` —
the axis on which `ka_taranga` buckets its waveform (`ka_taranga.py:113,169`). **A substring match on
an identifier is an association; the code uses it as a gate.** No rule makes a `dasamsha` signal
*necessarily* a career signal for *this* native. Q-K04's "when do career and health coincide" is
answered on this basis. The honest form is a derivation-ledger-backed domain relation (B.3), or an
explicit `domain_basis: 'keyword_match'` field so the reader can discount it.

### §5.4 STOP saying "applicable clocks" when one clock is structurally absent
This is the doctrinal challenge. `STRATEGIC_LEDGER:110` grants L3 "qualified engagement … by
applicable clocks and contacts." For the canonical chart, **the transit clock contributes nothing to
any composite L3 output** — `kala_convergence` is empty [VERIFIED-E], so `ka_taranga`'s transit term
is 0.0 on every row, `ka_kala_darshana` and `ka_bhavishya_lekha` produce no rows at all, and
`ka_kalasutra`'s convergence refinement never fires. The layer is not serving "applicable clocks";
it is serving **one clock (Vimśottarī, via L1) plus a static graha→domain lookup**, under a name that
promises several. The doctrine is not wrong — the code has not earned the plural. Either the
serving surfaces state which clocks were consulted and which were unavailable (a `clocks_consulted`
/ `clocks_unavailable` pair, machine-readable, §N.6 item 4), or the layer stops describing its
outputs as multi-clock.

### §5.5 STOP asserting "no disagreement" with no detector
`priority.ts:280` and `:316`, `story.ts:609`, `explain.ts:302` all emit `dissent: []` as a literal.
`ahead.ts:1705-1707` documents this exact defect being found and fixed there (F-110): "`dissent: []`
was hardcoded — an assertion that NO system on this server disagrees, emitted while `pact_query`
held a denial on 63 cited L1 facts." An empty array asserts a negative. The fix pattern already
exists in-repo at `ahead.ts:1708-1722` (compute `gateContradicts`, populate from it) and at
`explain.ts:429-430` (`honestEmptyCoverage(..., empty_reason)` when the detector could not run).
Three surfaces have not adopted it. §N.8: a signal with no code path that could make it read false
is null, not green.

### §5.6 STOP shipping a schema that says "probability" while the prose says it is not one
`ka_bhavishya_lekha` did the hard half correctly: `_TIER_LABELS` was reworded away from "High
probability (>=70%…)" to "High structural convergence" (`:535-547`), and the caveat is gated on
`tier_basis ∈ {'calibrated'}` — which [VERIFIED-E] never occurs, 100% of rows being
`relative_uncalibrated`. But the **structured** vocabulary a machine consumer reads still says
probability: the column is `kala_bhavishya.probability_tier` [VERIFIED-E schema], the values are
`tier_1_high` / `tier_2_moderate` / `tier_3_speculative` (`:450-458`), and the narrative JSON key is
`'probability_statement'` (`:591`). The prose disclaims what the field names assert; a consumer
reading the column and not the caveat gets the category error the rewording was meant to close.
Rename the field, or carry `tier_basis` beside it on every row.

### §5.7 STOP asserting completeness the code caps
`ka_kalasutra.py:142-144` ("genuinely finds every period the dasha table holds") vs
`date_resolver.py:417,500` (`max_windows=8`, `matched[:8]`). Either raise/remove the cap for the
recurrence listing, or emit `matched_period_count` + `truncated` so the claim becomes falsifiable.
Same class as §5.5, applied to coverage rather than dissent.

### §5.8 Not overreach, but worth naming: two claims that are *correctly* bounded today
Recorded so the elevation campaign does not "fix" them:
- `elect.ts:296-299`'s falsifier — "if X is not undertaken by `top.end`, this specific elected window
  closes" — is a claim about the *window*, not about the outcome. Correct.
- `ka_bhavishya_lekha.py:583-589`'s uncalibrated caveat, and
  `call_service_wrappers.ts:688-697`'s refusal to zero-fill a missing orb term. Both are the right
  pattern; §5.1 asks `ka_taranga` to adopt the same one.

---

# §6. COULD NOT VERIFY — register

Recorded per §N.8 rather than substituted with a plausible default.

1. **Whether `chart_dashas` emits shared boundary dates between adjacent periods.** The closed-closed
   membership tests (`date_resolver.py:476`, `ka_taranga.py:157`) are verified; the double-membership
   consequence depends on boundary-date equality, which I did not query. Stated conditionally in §3.1.
2. **Whether `convergence_score`'s own formula shares terms with the `currents` dict beyond both
   deriving from `constituent_factors`.** I did not trace the scoring function inside
   `services/ka_sangam/engine.py`. What is verified: both are computed from the same
   `constituent_factors` payload on the same row (`ka_sangam.py:901-930`).
3. **Whether `KaTulanaService.compare()` has a caller outside my search scope.** Scope stated in
   §3.4. A grep finding no caller establishes only the search scope.
4. **Whether the L5 side of Q-K16 (frozen-claim adjudication) is independently sound.** Out of L3
   scope, as in the baseline T2 packet.
5. **Why `kala_activation`/`kala_convergence` are empty for the canonical chart despite
   `asset_throughput` recording successful writes on 2026-08-13.** Inherited unresolved from
   [BASELINE `KALA_PROVING_JOURNEYS_BASELINE_v1_0.md`]; Lane E re-confirms the present-tense
   emptiness only, and diagnosed nothing about the cause.
6. **Whether any surface other than `query_convergence_windows` exposes
   `independent_current_count`.** My grep covered `platform`, `platform-mcp`, `00_ARCHITECTURE` for
   `*.ts`/`*.py`/`*.sql` with node_modules excluded. Compiled output and non-matching extensions were
   not searched.
7. **Every "what would prove it works" in §4 is a proposed test, not an executed test.** None was run.

---

## §7. One-paragraph verdict

Kāla's problem is not that it over-claims at its outer boundary — the layer's probability discipline
is genuinely good, stamped in the data (`tier_basis='relative_uncalibrated'` on 100% of rows) and
enforced in code (`ka_bhavishya_lekha.py:552-590`, `call_service_wrappers.ts:688-697`,
`query_temporal_activation.ts:443-465`). Its problem is that **the layer loses its own best material
between its own assets**: the independence measurement it computes reaches L4 but no L3 consumer;
the recurrence set it resolves is capped at 8 while a comment claims completeness; the convergence
richness it stores in 21 columns arrives downstream as two scalars and a citation string; the
comparison kernel it built and tested has no caller; and the one trajectory asset that *is* populated
for the native serves 92,412 rows whose declared transit term is `0.0` everywhere. Elevate the seams
before elevating the assets — five of the six most valuable capabilities in the portfolio (Q-K05,
Q-K06, Q-K08, Q-K11, Q-K12) are blocked not by missing computation but by information discarded at a
hand-off that already exists.
