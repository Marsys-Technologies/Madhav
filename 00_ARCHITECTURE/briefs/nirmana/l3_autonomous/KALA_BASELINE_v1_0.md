---
artifact: KALA_BASELINE
canonical_id: KALA_BASELINE
version: "1.0"
status: FROZEN_BASELINE
date: 2026-09-22
phase: "Kāla (L3) pre-elevation setup — Phase 0.1: freeze the acceptance baseline"
baseline_authority: >-
  MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md §2 (L3-Q01 … L3-Q13, each with its verbatim
  "Required added distinction" and strategy-named "Primary proof"), plus the three
  MADHAV_PRODUCT_DEFINITION_v3_0.md §14 first-proving-set cases (deep structural question with
  no forced forecast; structure–time question with accountable permitted forward claims;
  historical challenge that actively seeks misfit), plus one constructed ordinary-period case
  required by Product §9 ("The experience must work for ordinary charts and ordinary periods,
  not only dramatic named yogas or the repeatedly studied native chart").
measured_against: >-
  (a) The production PostgreSQL database `amjis` (connected read-only as role `amjis_app`,
  server clock 2026-09-22T11:38:42Z), tables `kala_*`, `chart_dashas`, `life_events`,
  `brahma_prospective_ledger`, `asset_registry`, `asset_throughput`; and
  (b) the deployed MCP tool surface `marsys-jis-direct` (all probes executed live between
  2026-09-22T11:39Z and 2026-09-22T11:44Z).
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
does_not_authorize: "any change; this is a measurement"
read_only_attestation: >-
  No INSERT/UPDATE/DELETE/DDL was issued. No build, migration or writer was run. No credential,
  connection string or DATABASE_URL was printed, logged or written to any file.
vocabulary_note: >-
  F06 states cited here are `applied`, `inapplicable`, `unavailable`, `unqualified`,
  `contradictory_unresolved`, `unexplored` per
  MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md §2 F06 / §3.2. Where this document
  assigns an F06 state it is THIS DOCUMENT'S assignment, made from observed response shape —
  the deployed surfaces do not emit F06 states (see §5 item 2).
changelog:
  - "1.0 (2026-09-22): first freeze. 17 cases measured against live production DB + live deployed MCP surface."
---

# Kāla (L3) — frozen acceptance baseline

## 1. What this freezes, and why

This is the "before" snapshot that makes L3 elevation falsifiable. It records, for seventeen
governing questions, **what the deployed system returns today** — not what an artifact says it
returns, not what a writer was built to produce, and not what `asset_throughput` records as
written.

The unit of record is *structure and shape*: did the surface answer, how many rows, which fields
were populated versus null, which required distinction was present or absent, the verbatim error
text where there was one. No private chart narrative or interpretation is recorded here.

It is frozen because it is unrecoverable if skipped: once elevation work begins, the pre-elevation
answer to "which exact distinctions did the layer already make?" cannot be reconstructed.

**The three facts that dominate every case below, established first so each case need not restate
them:**

**BF-1 — Five L3 assets record large writes in `asset_throughput` while their target tables hold
zero rows for the canonical chart.**

```sql
-- probe (exact)
select asset_id, state, rows_written, last_built_at, left(last_error,60)
  from asset_throughput
 where chart_id='482012f1-710e-4a25-994a-93821f5871aa' and asset_id like 'ka\_%'
 order by asset_id;
select count(*) from kala_activation where chart_id='482012f1-...';   -- etc. per table
```

| asset | `asset_throughput.state` | `rows_written` | `last_built_at` | target table rows for this chart TODAY |
|---|---|---|---|---|
| `ka_kalasutra` | `stale` | 335,403 | 2026-08-13 01:15:50Z | `kala_activation` = **0** (337,148 total, 336,093 of them on `1c826d5a…`) |
| `ka_sangam` | `stale` | 14,868 | 2026-08-13 01:07:13Z | `kala_convergence` = **0** (20,497 total) |
| `ka_kala_darshana` | `stale` | 750 | 2026-08-13 01:15:53Z | `kala_darshana` = **0** (750 total) |
| `ka_bhavishya_lekha` | `stale` | 100 | 2026-08-13 01:15:54Z | `kala_bhavishya` = **0** (100 total) |
| `ka_vighnakara` | `stale` | 536 | 2026-08-13 01:08:12Z | `kala_obstruction` = **0** (747 total) |

Three further rows are errors carrying their own verbatim text:

- `ka_avadhi` — state `error`, `rows_written` 1169, `last_error` = `post-write integrity check failed: integrity_check_sql → False`. **`kala_avadhi` nonetheless holds 1,169 rows for this chart and `kala_bundle_get` serves them as `timeline_excerpt`** — a surface serving rows from an asset whose own post-write integrity check returned False.
- `ka_kshetra` — state `error`, `rows_written` 1,183,134, `last_error` = `worker_crash: OperationalError: the connection is lost`.
- `ka_gochara_v3_century_materialize` — state `error`, `last_error` = `RaiseException: BUILD-PROTECTED: kala_gochara_windows row(s)`.
- `ka_dasha_kala` — state `lit`, `rows_written` **0**, no `target_table` in `asset_registry`.

**BF-2 — `kala_field` holds 8,570,075 rows for this chart, while every serving surface reports the
field build "has not run".**

```sql
select count(*) from kala_field             where chart_id='482012f1-...';  -- 8570075
select count(*) from kala_field_snapshots   where chart_id='482012f1-...';  -- 0
select count(*) from kala_field_salience     where chart_id='482012f1-...';  -- 0
```

Every elevated `kala_*` response carries, verbatim:

> `"field_snapshot_reason":"ka_kshetra has written no kala_field_snapshots row for this chart yet — the first field build has not run. Honest empty marker per B.10/§N.8; the real 'kfs_…' id is served automatically once the field build lands."`

The first field build *did* run — it wrote 8.57M `kala_field` rows and then crashed
(`worker_crash: OperationalError: the connection is lost`) before the snapshot header and the
stage-6 salience rows. The served message asserts a cause the evidence contradicts.

**BF-3 — The canonical chart is not the chart the L3 data lives on.** `kala_activation`,
`kala_convergence` and `kala_bhavishya` rows belong almost entirely to `1c826d5a-41cb-4450-b4dc-59d440e5f75a`
(336,093 / 17,957 / 100 rows respectively). Every "honest empty" recorded in §2 is an honest empty
*for the canonical chart specifically*.

---

## 2. The seventeen cases

Probe transcripts were executed live. Where a response field is quoted, it is quoted verbatim from
the live JSON.

---

### L3-Q01 — "What is active now, and why?" (P09–10/P22)

**Required added distinction (verbatim, Strategy §2):** *"Which exact structure, participants,
condition and qualified clocks are engaged; background versus enabling interval versus contact."*

**Primary proof (verbatim):** *"Perturb the qualifying condition while holding geometry fixed."*

**Probe.**
```
mcp__marsys-jis-direct__kala_now_get(chart_id="482012f1-710e-4a25-994a-93821f5871aa")
mcp__marsys-jis-direct__kala_explain_get(chart_id="482012f1-…", domain="career", max_signals=3)
psql -Atc "select count(*) from kala_activation where chart_id='482012f1-710e-4a25-994a-93821f5871aa';"
psql -Atc "select count(*) from kala_darshana  where chart_id='482012f1-710e-4a25-994a-93821f5871aa';"
```

**Today's actual answer.** `kala_now_get` returned HTTP-level success. `reading.thesis` verbatim:
`"No temporal activation window is active for this chart as of 2026-09-22. No Kāla-Darshana
confluence window is active today."` `windows: []` (0 rows). `darshana: null`.
`reading.evidence: []`, `reading.dissent: []`, `reading.falsifier: null`.
`field_snapshot_id: "field_not_yet_built"`. DB confirms `kala_activation` = 0 and `kala_darshana` = 0
for this chart.

The response is *not* thin elsewhere: 9 `gochara_dual_reference` rows (each with both
`house_from_moon` and `house_from_lagna` — a genuine dual-reference distinction), 2
`dasha_lord_transit_condition` rows with dignity + `dignity_basis`, 8 `dasha_sandhi` bands across
levels 1–4 with an explicit `band_convention` paragraph disclosing its own lite simplification and
its floor behaviour at level 4, 9 `kota_chakra` rows, 8 `moorti_nirnaya` rows (4 with
`moorti_computed: false`), 3 `vedha_gochara` rows, `tithi_pravesha`, `sudarshana_varsha`.

`coverage` carries 18 concepts. Their states come from a **three-value vocabulary**
`{computed, honest_empty, not_in_corpus}` — not F06.

One internal inconsistency inside a single response: `sukshma_boundary_uncertainty: []` with
`reason: "L1 dasha registry (get_dashas) unreachable this call."` and
`sukshma_boundary_uncertainty_reachable: false`, while in the same envelope
`dasha_sandhi_reachable: true` and `provenance_envelope.assets` lists
`"get_dashas (chart_dashas, level_n=4)"` as reached.

The "why" half: `kala_explain_get` returned `pact_status: "unknown"`, `chain: []`,
`weakest_link: null`, `fact_id_refs: []` (full text under case P14-A).

**Verdict on the required distinction: ABSENT.** Nothing in the response types anything as
background vs enabling interval vs contact; there are no engaged structures, participants or
conditions to type. **F06: `unavailable`** — the substrate exists in the schema and for other
charts, but not for this chart (BF-1/BF-3). The response does not itself carry an F06 state.

**Primary proof — not executable today.** "Perturb the qualifying condition while holding geometry
fixed" requires at least one qualifying condition to be engaged. There are none.

**Live-path note.** Registered and reachable live on `marsys-jis-direct` (verified by the call
above); registration at `platform-mcp/src/tools/kala_views/now.ts`,
`platform-mcp/src/tools/kala_views/register_all.ts`. No live in-repo UI caller found within scope:
`grep -rlF "kala_now_get" platform/src/app platform/src/components` returns exactly one file,
`platform/src/components/pariprashna/ArrivalLine.tsx`, and its only hit is line 12 — a code
comment (`a \`kala_now_get\`-shaped capability`), not a call.

---

### L3-Q02 — "When is the closest eligible window, and which later window is better supported?" (P03–04/P09)

**Required added distinction (verbatim):** *"Nearest, strongest under a named criterion, robust
across declared variants and merely present remain distinct."*

**Primary proof (verbatim):** *"Controlled ranking on matched candidates and coverage; preserve
ties/incomparability."*

**Probe.**
```
kala_windows_get(chart_id="482012f1-…", start_date="2026-09-22", end_date="2031-09-22", limit=5)
kala_ahead_get(chart_id="482012f1-…", horizon_years=5, max_items=3)
kala_priority_get(chart_id="482012f1-…", domain="career", top_k=3)
```

**Today's actual answer.** `kala_windows_get`: `activations: []`, `activation_count: 0`,
`total_matching: 0`, `window_families: []`, `forward_windows: []`, `predicates: []`,
`signal_id_refs: []`. `empty_reason` verbatim: *"No activation rows exist for chart
482012f1-710e-4a25-994a-93821f5871aa at ayanamsha 'lahiri_chitrapaksha'. The L3 Kāla activation
asset (ka_kalasutra) may not be built for this chart, or the ayanamsha_id does not match a built
variant."* `forward_window_status.state: "incompatible_filters"` with
`incompatible_filters: ["ayanamsha_id"]` and `source_row_count: null`.

`kala_ahead_get`: `windows: []`, `projections: []`, `recurrence_ladder: []`,
`reading.falsifier: null`; `coverage` nonetheless states
`{"concept":"forward_temporal_windows","state":"computed"}` and
`{"concept":"probabilistic_projections","state":"computed"}` — `computed` on empty arrays, with no
state distinguishing "computed and empty" from "not available".
`period_echo` returned two rows both `status: "insufficient_data"`,
`insufficient_data_reason: "L1 dasha registry (marsys://tool/L1/get_dashas) unreachable this call."`,
`period_echo_reachable: false`.

`kala_priority_get(domain=career)`: `ranked_signals: []`, `signal_count: 0`, thesis *"No
priority-ranked signals activation-overlap 2026-09-22–2026-12-21 (domain: career) for this chart."*

**Named defect (recorded, not fixed).** `kala_windows_get` emits, in the same envelope as that
`empty_reason`, a `temporal_closure` block reading
`"state":"complete_within_stated_window"`, `"exhaustive_within_stated_window": true`,
`"continuation":{"supported":false,"reason":"All rows matching this exact stated window and filters
were returned."}`. A caller reading the closure block alone would read a zero-row result over a
five-year horizon as an exhaustively-searched negative. The `empty_reason` contradicts it. Both
ship together.

**Verdict on the required distinction: ABSENT.** There are no candidates, so nearest / strongest /
robust / merely-present cannot be held apart. The ranking machinery does exist elsewhere in the
layer (see L3-Q10). **F06: `unavailable`.**

**Live-path note.** Live on `marsys-jis-direct` (verified). No live UI caller found within scope
(`platform/src/app`, `platform/src/components`): the only match is the generic MCP passthrough route
`platform/src/app/api/mcp/db/query/route.ts`.

---

### L3-Q03 — "Does a named configuration have a complete activation route?" (P09)

**Required added distinction (verbatim):** *"Formation, cancellation, active participants,
necessary/optional temporal clauses and rival routes."*

**Primary proof (verbatim):** *"Reject a participant contact that does not satisfy the complete
qualified rule."*

**Probe.**
```
kala_yoga_activation_get(chart_id="482012f1-…", limit=3)
kala_explain_get(chart_id="482012f1-…", domain="career", max_signals=3)
```

**Today's actual answer.** `activated_yogas: []`, `total_count: 0`,
`undated_activation_count: 0`, `structurally_always_on_count: 0`,
`undated_pending_window_count: 0`, `signal_id_refs: []`. `empty_reason` verbatim: *"No yoga signals
join to kala_activation for chart 482012f1-710e-4a25-994a-93821f5871aa at ayanamsha
'lahiri_chitrapaksha'."* Join declared as
`signal_id (bodha_msr_signals.signal_id = kala_activation.signal_id)` with
`yoga_filter: "signal_type_class = 'yoga'"`.

**One genuine positive detector fired here.** The response carries a live-derived DEFECT-001 block:
`{"claim_id":"DEFECT-001","status":"RESOLVED","metrics":{"total_refs":73049,"orphan_refs":0,"orphan_pct":0},
"as_of":"2026-09-22T11:40:22.113Z","expires_on":"2026-09-23T11:40:22.113Z"}` — 73,049
`constituent_facts_array` references resolved against `chart_facts` live, 0 orphaned. This is a real
detector with a real denominator and an expiry, computed at call time.

`kala_explain_get` produced `chain: []` and `weakest_link: null` — so no route, complete or
incomplete, is exhibited.

**Verdict on the required distinction: ABSENT.** No formation / cancellation / participant /
temporal-clause / rival-route decomposition is emitted because no yoga signal reaches an activation
row. **F06: `unavailable`.** The primary proof (reject a contact that fails the complete rule)
cannot be run: there is no contact to reject.

**Live-path note.** Live on `marsys-jis-direct` (verified). No live UI caller found within scope
(`platform/src/app`, `platform/src/components`) other than the generic MCP passthrough route.

---

### L3-Q04 — "Why can activity coexist with strain?" (P03–04)

**Required added distinction (verbatim):** *"Receipt/creation versus retention/relief; supporting
and inhibiting paths can overlap."*

**Primary proof (verbatim):** *"A decisive second-domain opposition survives compilation and
projection."*

**Probe.**
```
kala_bundle_get(chart_id="482012f1-…", date_range={start:"2026-01-01", end:"2028-12-31"})
psql -Atc "select count(*) from kala_obstruction where chart_id='482012f1-…';"   -- 0 (747 total)
psql -Atc "select count(*) from kala_convergence where chart_id='482012f1-…';"  -- 0 (20497 total)
```

**Today's actual answer.** `timeline_excerpt`: 5 rows, populated and citation-bearing — each with
`avadhi_id`, `system_id: "vimshottari"`, `level_n`, `lord_graha`, `period_start`/`period_end`,
`dossier.activated_pratijna_ids` (1–8 UUIDs per row), `dossier.sublord_modulation` (populated on
level-2 rows, `null` on level-1), `quality.domains`, `citations`,
`formula_version: "ka_avadhi_v1.0"`. **`dossier.lord_condition_fact_refs` is `[]` on every one of
the 5 rows** — the link from a period to its lord's condition facts is empty.

`convergence_windows: []` (`convergence_count: 0`). `obstructions: []` (`obstruction_count: 0`).
Neither array carries an `empty_reason` — only a count of 0.
`snapshot.kala_readiness.score: null` with `interpretation: "No kala_darshana confluence row active
for today — chart has no computed windows covering the current date."` (an honest null, correctly
not substituted with a number). `snapshot.transit_state.transits: []` with a stated reason and a
cross-pointer. `snapshot.snapshot_date: "2026-09-20"` — two days behind the call date
(2026-09-22); no staleness flag on the field.
`provenance_envelope.obstructions_not_date_filtered: true` is disclosed.

The `ka_avadhi` rows being served are the rows of the asset whose `asset_throughput.state` is
`error` / `post-write integrity check failed: integrity_check_sql → False` (BF-1).

**Verdict on the required distinction: ABSENT.** The inhibiting half of the layer is entirely
empty for this chart, so supporting and inhibiting paths cannot be shown to overlap, and
receipt/creation vs retention/relief is not typed anywhere in the served shape. **F06:
`unavailable`** — and the bundle collapses it to a bare `0`/`[]`, which is precisely the
`no null/zero/empty fallback collapses these states` clause of F06.

**Live-path note.** Live on `marsys-jis-direct` (verified). Registered at
`platform-mcp/src/tools/retrieval/kala_temporal.ts`. No live UI caller found within scope
(`platform/src/app`, `platform/src/components`).

---

### L3-Q05 — "Why do timing methods disagree?" (P15/P19/P21)

**Required added distinction (verbatim):** *"Method-native context, applicability, silent/failed
methods, shared roots and non-comparable scales."*

**Primary proof (verbatim):** *"Remove a method; show actual changed and unchanged evidence without
a forced consensus."*

**Probe.**
```
kala_explain_get(chart_id="482012f1-…", bhava=10,        max_signals=3)
kala_explain_get(chart_id="482012f1-…", domain="career", max_signals=3)
```

**Today's actual answer.** With `bhava=10`, `school_voices` has one entry, populated:

```
{"school":"kp","bhava":10,
 "ladder":{"house":10,"cusp_owner":"Saturn","level_a":["Mercury"],"level_b":["Sun"],
           "level_c":[],"level_d":["Saturn"],"ranked":["Mercury","Sun","Saturn"],
           "fact_ids":["6e1062de9951fcd7","47237d0e33d95027","8844e053ffae8308",
                       "6dbd713f6d93a196","abd6255c867f36b3","3b6eaf1273f5d26e"]},
 "kp_ayanamsha_id":"krishnamurti","chain_ayanamsha_id":"lahiri_chitrapaksha",
 "ayanamsha_divergence":true,
 "state":"honest_empty","kp_stance":"unknown","parasari_stance":"unknown",
 "agreement":"not_comparable","running_lords":[],"matches":[],"strongest_limb":null,
 "empty_reason":"no running `vimshottari_kp` period rows for this chart at the evaluated date —
                 KP judges a RUNNING window, and there is none to judge."}
```

`engine_testimony` returns 2 engines (`kp`, `gochara_v3`), both `state: "honest_empty"`,
`agreement: "not_comparable"`. `concordance: null`. `reading.dissent: []`.

With `domain="career"` instead, only ONE engine appears (`gochara_v3`); the KP voice is dropped with
`"the KP school voice needs a bhava to judge; this call resolved neither `bhava` nor a domain the
shastra map maps to one."` — i.e. the number of consulted methods depends on which parameter the
caller happened to use.

A second observation across the two calls: `a5_gochara_agreement.dominant_valence` reads `"gain"`
with `gochara_windows_active: 3` under `domain=career`, and `"loss"` with
`gochara_windows_active: 10` under `bhava=10` — same chart, same date, different parameter.

**Verdict on the required distinction: ABSENT as a whole; three of its five components are present
as real scaffold.** Present: *method-native context* (`kp_ayanamsha_id` vs `chain_ayanamsha_id` with
an explicit `ayanamsha_divergence: true`), *applicability / silent-failed methods*
(`not_comparable` + a per-engine `empty_reason` naming why, never a forced agreement), *non-comparable
scales* (as the `not_comparable` label). Absent: *shared roots* — nothing anywhere de-correlates two
corroborators by producer provenance; and the disagreement itself is never exhibited, because both
engines are silent. **F06: `unqualified`** for the concordance (the machinery is there but the
comparison is not adjudicated), `unavailable` for the stances.

**Primary proof — not executable today.** "Remove a method; show actual changed and unchanged
evidence" requires at least two methods that both have a verdict. Zero do.

**Live-path note.** Live on `marsys-jis-direct` (verified); registered at
`platform-mcp/src/tools/kala_views/explain.ts`. No live UI caller found within scope
(`platform/src/app`, `platform/src/components`).

---

### L3-Q06 — "How does this chapter differ from the preceding one?" (P10)

**Required added distinction (verbatim):** *"Recurrence with changes in participants, conditions,
clocks, relationships and uncertainty."*

**Primary proof (verbatim):** *"Matched mechanism identities across intervals; no universal
narrative template."*

**Probe.**
```
kala_story_get(chart_id="482012f1-…", budget_kb=14, top_k=40)
psql -Atc "select count(*), sum(high_convergence_count), max(high_convergence_count)
             from kala_jivana_parva where chart_id='482012f1-…';"        -- 100 | 8838 | 1073
psql -Atc "select min(computed_at)::text, max(computed_at)::text
             from kala_jivana_parva where chart_id='482012f1-…';"        -- both 2026-08-13 01:15:53Z
psql -Atc "select count(*) from kala_convergence where chart_id='482012f1-…';"  -- 0
```

**Today's actual answer.** `chapter_count: 2` after budget trim (`trim_report`:
`{"path":"chapters","original_count":40,"kept_count":2,"reason":"life-arc chapters: floored to 2
(hard-cap)"}`, with a `recover_via` pointer). `dedup_report`:
`{"source_row_count":40,"deduped_row_count":40,"collapses":[]}`.

`coverage` states, verbatim:
- `{"concept":"developmental_thesis","state":"honest_empty","reason":"… the developmental thesis per chapter — what this period asks given what previous chapters built, from lord-relationship + house-progression + LEL verdicts of prior same-lord chapters — is not yet computed at this facade. Requires cross-chapter lord-relationship analysis wired into story composition. … developmental_thesis is the W3 depth remainder, not yet built."`
- `{"concept":"chara_dasha_second_voice","state":"not_in_corpus", …}`
- `{"concept":"punctuation_events","state":"not_in_corpus", …}`

Each chapter carries `retrodiction_fit` with `aligned_ratio: 0`, `method:
"lexical_theme_keyword_match"`, and a note that explicitly disclaims calibration and flags the
sample as `<3` — an honest, correctly-scoped corroboration signal.

Each chapter's `narrative.summary` follows one fixed template:
`"<Lord> daśā (<start>–<end>): <quality> phase marked by <kw1>, <kw2>. N high-convergence windows in
this span."` — a universal narrative template, which is the thing the primary proof names as
disqualifying.

**Named defect (recorded, not fixed).** Chapters serve `high_convergence_count` — 884 for the
Jupiter MD chapter, 178 for Jupiter/Venus, 8,838 summed and 1,073 max across the chart's 100
`kala_jivana_parva` rows — while `kala_convergence` holds **0** rows for this chart. The parva rows
were computed 2026-08-13 01:15:53Z; the convergence rows they count are not in the database today.
A served count whose substrate is not re-derivable.

**Verdict on the required distinction: ABSENT.** The cross-chapter comparison is explicitly not
built (`developmental_thesis` honest_empty); matched mechanism identities across intervals are not
emitted; the narrative template is universal. **F06: `unexplored`** for the comparison itself;
**`contradictory_unresolved`** for the served convergence counts against the live table.

**Live-path note.** Live on `marsys-jis-direct` (verified); registered at
`platform-mcp/src/tools/kala_views/story.ts` (referenced from `register_all.ts`). No live UI caller
found within scope (`platform/src/app`, `platform/src/components`) other than the generic MCP
passthrough route.

---

### L3-Q07 — "Which domains interact over time?" (P01/P03–10/P17)

**Required added distinction (verbatim):** *"Qualified structural linkage plus coincident/ordered
intervals, enabling or inhibiting roles, ordinary as well as dramatic expressions."*

**Primary proof (verbatim):** *"Destroy the structural bridge while retaining coincident dates; the
cross-domain inference must disappear."*

**Probe.**
```
psql -Atc "select scope_kind, count(*), count(distinct scope_id) from kala_taranga
            where chart_id='482012f1-…' group by 1;"
           -- domain | 43488 | 24      event_class | 48924 | 27
psql -Atc "select month::text, scope_kind, scope_id, activation, components::text
             from kala_taranga where chart_id='482012f1-…'
              and month between '2026-09-01' and '2026-09-30' limit 3;"
psql -Atc "select count(*) total,
                  count(*) filter (where (components->>'transit_contribution')::numeric = 0) zero,
                  round(avg((components->>'transit_contribution')::numeric),4) avg,
                  max((components->>'transit_contribution')::numeric) max
             from kala_taranga where chart_id='482012f1-…';"
gochara_activation_get(chart_id="482012f1-…", as_of_date="2014-10-01", domain="health")
```

**Today's actual answer.** Per-domain time series exist and are populated: 43,488 `domain`-scoped
rows over 24 distinct domains, 48,924 `event_class`-scoped rows over 27 classes. Sample row
(2026-09-01, domain `career`): `activation = 0.293444`, `components =
{"dasha_lord":"Mercury","formula_note":"ka_taranga_v1.0","dasha_contribution":0.15,
"promise_contribution":0.7884,"transit_contribution":0.437}` — all three declared terms non-zero.

Aggregate over all 92,412 canonical-chart `kala_taranga` rows: `transit_contribution` is exactly
`0` on **56,130** rows (60.7%), null on **0**, mean **0.2490**, max **1.0**.

`gochara_activation_get(domain="health")` returned a `coverage` block that is the strongest
coverage accounting observed anywhere in the layer: `event_classes_covered` = 27 named classes,
`event_classes_targeted_not_swept: []`, `domains_not_covered: []`, `coverage_quality.tier: "rich"`
(27 classes / 13 domains), and a `universe_source` paragraph stating the set is
*"Mechanically derived fresh every call from live table state — never hand-maintained."*

**What is absent.** No surface in the layer emits a cross-domain object: no interval intersection
between two domain streams, no enabling/inhibiting role assignment between domains, and no stated
dominance rule. There is no structural bridge to destroy, so the primary proof has no subject.

**Divergence from a prior finding, recorded for re-verification at the authority (not adopted).**
`LANE_E_LAYER_VALUE_MODEL.md` §3.3 / Q-K08 states the transit term is *"0.0 on every one of the
92,412 rows for this chart because its source table is empty."* Measured live today it is 0 on
60.7% of rows and non-zero on 39.3%, mean 0.2490. Either the data changed after Lane E measured, or
the Lane E claim was scoped differently. **This baseline records the measurement above; it does not
adjudicate the divergence.**

**Verdict on the required distinction: ABSENT.** Per-domain series and honest domain-coverage
accounting are present; the cross-domain linkage, ordering and role assignment are not. **F06:
`unexplored`.**

**Live-path note.** `gochara_activation_get` live on `marsys-jis-direct` (verified). `kala_taranga`
is served through `query_activation_waveform`; no live UI caller found within scope
(`platform/src/app`, `platform/src/components`) other than the generic MCP passthrough route.

---

### L3-Q08 — "Is *no window found* a real negative?" (P09/P16/P18)

**Required added distinction (verbatim):** *"Searched horizon, resolution, method/target coverage,
unavailable inputs and unknown intervals."*

**Primary proof (verbatim):** *"A window just outside a searched partition must not become a
universal denial."*

**Probe.**
```
kala_windows_get(chart_id="482012f1-…", start_date="2026-09-22", end_date="2031-09-22", limit=5)
kala_priority_get(chart_id="482012f1-…", domain="career", top_k=3)
gochara_activation_get(chart_id="482012f1-…", as_of_date="2014-10-01", domain="health")
```

**Today's actual answer — the strongest discipline in the layer.**

`kala_windows_get` emits `empty_reason` naming the possibly-unbuilt asset by id (`ka_kalasutra`) AND
the alternative cause (ayanamsha variant mismatch); `forward_window_status` classifies its own
separate empty as `"incompatible_filters"` and names the offending filter
(`incompatible_filters: ["ayanamsha_id"]`); `date_filter.honored: true`; two `caveats` disclosing
`single_cycle_per_signal` and `near_tier_build_date_relative`.

`kala_priority_get` reports three concepts independently:
`priority_ranking_legacy_scalar: honest_empty` (reason: no overlap in this window),
`salience_vector_five_axis: honest_empty` (reason: *"no kala_field_salience rows for this chart —
ka_kshetra stage 6 has not yet run"*), `surprise_of_absence: not_in_corpus` (reason: *"absence-as-signal
(item 33, PRIORITIZE deepening) not yet built — lands W3"*). Three genuinely different reasons for
three different kinds of absence, not one flattened empty.

`gochara_activation_get` adds `sweep_completeness`:
`{"substeps_committed":270,"source":"build_substep_progress (asset_id=ka_gochara_v3_century_materialize …)",
"materialized_through":"2084-01-31"}` plus an explicit refusal to fabricate a denominator: *"No
total-planned-substep denominator is reported here: that figure is not independently queryable
post-build without re-deriving the writer's own planning logic, and this field will not fabricate
one."*

**Named defect (recorded, not fixed).** The `temporal_closure` block on the same `kala_windows_get`
response declares `"state":"complete_within_stated_window"` and
`"exhaustive_within_stated_window": true` on a zero-row result whose sibling `empty_reason` says
the asset may not be built. Read alone, the closure block *is* the universal denial the primary
proof forbids.

**Verdict on the required distinction: PRESENT, with one named defect.** Searched horizon,
resolution, method/target coverage and unavailable inputs are all separately reported, by different
surfaces, with reasons. **F06: `unavailable` is correctly held apart from `inapplicable` in the
prose reasons** — but no surface emits an F06 state code, so the distinction lives in free text a
machine cannot key on.

**Live-path note.** All three live on `marsys-jis-direct` (verified). No live UI caller found within
scope (`platform/src/app`, `platform/src/components`) other than the generic MCP passthrough route.

---

### L3-Q09 — "What changes with birth uncertainty or convention?" (P13/P19)

**Required added distinction (verbatim):** *"Input sensitivity differs from method disagreement and
from empirical reliability."*

**Primary proof (verbatim):** *"Recompute declared variants; match the same propositions and
boundary changes."*

**Probe.**
```
kala_now_get(chart_id="482012f1-…")                       # default ayanamsha lahiri_chitrapaksha
kala_now_get(chart_id="482012f1-…", ayanamsha_id="raman")
psql -Atc "select distinct ayanamsha_id from chart_dashas where chart_id='482012f1-…';"
psql -Atc "select column_name from information_schema.columns
             where table_name='kala_gochara_windows' order by ordinal_position;"
```

**Today's actual answer — a genuine, live, reproducible sensitivity demonstration.**

| field | `lahiri_chitrapaksha` (default) | `raman` |
|---|---|---|
| Mahādaśā lord | Mercury | Ketu |
| Antardaśā lord | Saturn | Venus |
| MD span | 2010-08-18 → 2027-08-18 | 2025-11-22 → 2032-11-22 |
| MD band width | 186 days | 77 days |
| level-3 `is_now_within_band` | `false` | **`true`** |
| `natal_moon_sign_fact_id` | `141606653ff3f1ad` | `cac267711001f79b` |
| `janma_resonance.nakshatra.birth_fact_id` | `fe40422d174b38c0` | `3850f63abec1b0bf` |

`chart_dashas` carries six declared variants: `INVARIANT`, `krishnamurti`, `lahiri_chitrapaksha`,
`raman`, `surya_siddhanta_classical`, `true_chitra`.

**What is absent, in three parts.**

1. **No variant-comparison surface.** Each call returns its own answer as if authoritative. Neither
   response mentions the other, flags that a different convention yields a different running lord,
   or matches propositions across variants. The caller must run two calls and diff them by hand —
   which is what this baseline did.
2. **Half the layer cannot vary at all.** `kala_gochara_windows` has **no `ayanamsha_id` column**
   (verified against `information_schema.columns`). Accordingly `gochara_narrative.active_windows`
   was byte-identical across both runs — the same 10 event classes, same 2024-02-05 → 2034-01-30
   spans, same peak dates, same `signed_intensity` values. The daśā half of Kāla is
   convention-sensitive; the transit half is convention-invariant by schema.
3. **Input sensitivity is not typed apart from method disagreement.** The `raman` run's
   `school_voices`/`engine_testimony` machinery (L3-Q05) carries `ayanamsha_divergence` as a flag on
   a *method* voice, which is the one place the two ideas are visibly conflated in the served shape.

**Verdict on the required distinction: ABSENT.** Variant recomputation works and is real; the
distinction the question asks for — input sensitivity held apart from method disagreement and from
empirical reliability — is not made by any surface. **F06: `unqualified`** (the recomputation is
available but its scope is undeclared, and it silently does not apply to the transit half).

**Live-path note.** Live on `marsys-jis-direct` (verified — both variants). No live UI caller found
within scope (`platform/src/app`, `platform/src/components`).

---

### L3-Q10 — "Which feasible initiation intervals meet this undertaking's constraints?" (P11/P21–22)

**Required added distinction (verbatim):** *"General calendar, personal suitability, action
constraints and outcome expectation remain separate."*

**Primary proof (verbatim):** *"Actual interval intersection, location/date fidelity and
binding-constraint explanation."*

**Probe.**
```
kala_elect_get(chart_id="482012f1-…", undertaking="business",
               date_range={start:"2026-09-22", end:"2026-12-20"},
               limit=2, budget_kb=12, native_janma_nakshatra="Purva Bhadrapada")
```

**Today's actual answer — the strongest surface measured.** `candidate_count: 2`. Best candidate
`2026-11-29T00:00:00+00:00 → 2026-12-01T00:00:00+00:00`, `score: 0.662`,
`grading_tier: "silver"`, `grading_tier_label: "Silver — solid but not ideal"`,
`hard_flag: false`, `disqualified: false`.

The four things the distinction requires are kept in four separate fields:
`drivers: ["panchanga_quality=0.63", "dasha_quality=0.60 (Mercury/Saturn)", "transit_quality=0.80",
"signal_activation=0.72", "tara_bala=Sampat (favorable)"]` — general calendar, clock, transit,
chart-signal and personal-star each reported as their own term, never as one composite.

`frontier`: `{"candidate_count":2,"best_tier":"silver","gold_tier_present":false,
"convention_id":"lite_v0_frontier"}` — *best available* is explicitly separated from *best possible*.

`judgment_ledger` per candidate: `dosas_present: []`, `pariharas_applied: []`, `residual_dosas: []`,
`net_standing: "clean"`, plus `convention_only_factor_count` held apart from cited findings.

`lattice_adjudication.pareto`: `axes_used: ["panchangika_quality","residual_dosha_burden",
"cited_auspicious_support"]`, and **three axes explicitly excluded with reasons** —
`personal_field_alignment` (*"requires ka_kshetra field rows, which are not populated at this build
tier"*), `rite_specific_resonance`, `practical_feasibility` (*"no substrate anywhere in this estate
models a querent's practical constraints … "*).

`gap_report.census_disposition_counts: {"computed":39,"not_computed":5,"not_in_corpus":7}` with each
of the 5 and 7 named individually and carrying an `evidence_pointer`.
`parihara_corpus_gap` states `bg_parihara_rules` holds 0 muhūrta-scope rows out of 60 and that
residual doṣas are therefore *"reported UNCANCELLED"* rather than fabricating a cancellation.
`density: {"cited_rows_in_horizon":822,"convention_only_rows_in_horizon":1178,
"parihara_rules_total":60,"parihara_rules_muhurta_scope":0}`.
`reading.falsifier: {"statement":"if business is not undertaken by 2026-12-01T00:00:00+00:00, this
specific elected window closes","resolves_by":"2026-12-01"}`.
`paired_rite: null` with a `paired_rite_reason` naming the searched preparatory horizon.

**Named defect (recorded, not fixed).** At `budget_kb: 12` the `candidates` array was trimmed to 1
entry while `candidate_count` and `frontier.candidate_count` both still read `2`; `trim_report` was
itself trimmed (`original_count: 4, kept_count: 1, reason: "full trim_report omitted to fit
budget"`) with `recover_via.instrument: null`; `judgment_flags: [{"code":"budget_exceeded_after_trim",
"detail":"12kb budget still exceeded after full trim."}]`.

**Verdict on the required distinction: PRESENT.** **F06: `applied`.**

**Live-path note.** Live on `marsys-jis-direct` (verified); registered at
`platform-mcp/src/tools/kala_views/elect.ts`, cross-referenced from `now.ts`, `explain.ts`,
`ritual.ts`. No live UI caller found within scope (`platform/src/app`, `platform/src/components`).

---

### L3-Q11 — "What do actual observations fit or fail to fit?" (P12/P20)

**Required added distinction (verbatim):** *"Independently generated mechanisms, known-time
chronology, unmatched activations and unobserved periods."*

**Primary proof (verbatim):** *"Separate permitted retrospective comparison; no outcomes or derived
selectors in prospective builds."*

**Probe.**
```
mechanism_retrodiction_get(chart_id="482012f1-…", limit=50)
standing_predictions_read(chart_id="482012f1-…", limit=5)
psql -Atc "select lifecycle_status, count(*), min(lower(observation_window))::text,
                  max(lower(observation_window))::text
             from brahma_prospective_ledger where chart_id='482012f1-…' group by 1;"
psql -Atc "select generator_class, model, count(*) from brahma_prospective_ledger
             where chart_id='482012f1-…' group by 1,2 order by 3 desc;"
```

**Today's actual answer.**

*Retrodictive half — populated and honest.* 7 house-mechanisms reported, **8 confirming firings**
total (house 10 ×2, houses 6/4/11/9/12/3 ×1 each), each firing citing `event_id`, `event_date`,
`dasha_level`, `dasha_lord` and `dasha_row_id`. Against that: **25 `not_confirmed_events`**, each
with its `mapped_houses` and a per-event reason of the form *"neither MD nor AD lord matched house
N's lord (X) on this date"*; and **8 `unmapped_events`**, each with reason *"no classical house
mapping for domain prefix '<prefix>'"*. Misfit is reported at roughly 3× the rate of fit and is
individually enumerated, never aggregated away.
`sealed_test_split_note`: events on/after 2020-01-01 excluded unconditionally and *"not a
caller-settable parameter"*. `no_leakage_note` present.
`provenance.grounding` names `lagna_fact_id: "a51211ece89d6a5c"` and the whole-sign walk.

*Prospective half — 18 rows, none ever adjudicated.*

| `lifecycle_status` | count | earliest window start | latest window start |
|---|---|---|---|
| `open` | **18** | 2011-02-15 | 2082-01-01 |

There are **no** `matched`, `confirmed`, `falsified` or `withdrawn` rows. 5 of the 18 open windows
start before 2031; the remaining 13 start 2056–2082. One open row —
`8d85d0c7-dbf0-4636-8f6a-af159aa58770`, window `[2011-02-15,2011-03-11)`, claim prefix
`"G-5 live verification: engine-derived major_gain window 2011-02-15..20"` — has a window that
closed **fifteen years ago** and is still `open`.
`generator_class` distribution: `engine` 14 (`gochara_v3_w45_builder` 12, `gochara_lambda_e` 2),
`reading_synthesis` 3, `native_intuition` 1.
Every gochara-generated row's `falsifier` is the same template sentence with the class substituted:
*"Window end passes without elevated life event in the tracked event class (<class>)"*.

**Verdict on the required distinction: PRESENT for the retrospective half; ABSENT for the rest.**
Independently generated mechanisms and known-time chronology are genuinely present, and the
generation/evaluation firewall is real and enforced in code (hard-coded 2020 split, not a
parameter). *Unmatched activations* cannot be reported because `kala_activation` holds 0 rows for
this chart (BF-1). *Unobserved periods* are not reported at all. **F06: `applied`** for
retrodiction; **`unexplored`** for prospective adjudication.

**Live-path note.** Both live on `marsys-jis-direct` (verified). No live UI caller found within
scope (`platform/src/app`, `platform/src/components`).

---

### L3-Q12 — "What useful question or computation is missing?" (P16–18)

**Required added distinction (verbatim):** *"Omission detection, low-ranked evidence and smallest
admissible discriminating next step."*

**Primary proof (verbatim):** *"Seed an omitted cancellation, method or relationship; expose the
unresolved frontier."*

**Probe.** The `coverage[]` arrays of every elevated surface probed in this baseline, plus
`kala_elect_get`'s `gap_report`:
```
kala_now_get  → coverage[18]   kala_ahead_get → coverage[12]   kala_explain_get → coverage[4]
kala_priority_get → coverage[3]  kala_story_get → coverage[5]
kala_elect_get → coverage[12] + gap_report.factors_not_computed[5] + factors_not_in_corpus[7]
```

**Today's actual answer.** Every elevated surface declares its own un-built concepts by name, with a
reason and usually a brief item number and wave. Observed examples, verbatim concept names and
states: `transit_moorti: not_in_corpus` (item 4, W3), `sky_event_calendar: not_in_corpus` (item 3,
W3), `tithi_pravesa: not_in_corpus` (item 13, W3), `counterfactual_mode: not_in_corpus` (E6, W2/W3),
`classical_citation_join: not_in_corpus` (item 11), `surprise_of_absence: not_in_corpus` (item 33,
W3), `developmental_thesis: honest_empty` (W3 remainder), `chara_dasha_second_voice: not_in_corpus`,
`punctuation_events: not_in_corpus`, `state_delta: honest_empty`,
`muhurta_scope_parihara_rules: not_in_corpus`, `muhurta_lagna_strength: honest_empty`.

`kala_elect_get` goes furthest: `factors_not_computed` names 5 factors
(`janma_tithi_vara_nakshatra_resonance`, `gandanta`, `sandhi_zones`, `nakshatra_tara_bala`,
`nityayoga_vyatipata_vaidhriti_special_status`) and `factors_not_in_corpus` names 7
(`dagdha_yoga`, `hutasana_yoga`, `jvalamukhi_yoga`, `mrityu_yoga`, `mrityu_bhaga`,
`pushkara_navamsha_bhaga`, `shiva_vasa`), each with an `evidence_pointer` (several reading
`"not found (grep-verified)"`).

**What is absent, precisely.**

1. **The gap inventory is authored, not detected.** With one exception these `coverage` entries are
   hand-declared per wave — a writer wrote the concept name, the state and the brief item number.
   There is no code path that would flip `not_in_corpus` to `computed` by measuring; it flips when
   someone edits the facade. Per CLAUDE.md §N.8, a status with no detector behind it is null, not
   green — and these are declared *negative*, which is the safe direction, but they are equally
   undetected. **The one exception is real and worth preserving:** `gochara_activation_get`'s
   `coverage.universe_source` states the covered-class set is *"Mechanically derived fresh every
   call from live table state — never hand-maintained"*, and its `sweep_completeness` reads
   `build_substep_progress` live.
2. **No smallest-admissible-next-step ranking.** No surface ranks its own gaps by information value,
   consequence or burden. The gaps are listed; none is nominated as the next discriminating step.
3. **The omission-detection concept is itself one of the un-built ones.**
   `kala_priority_get` reports `{"concept":"surprise_of_absence","state":"not_in_corpus","reason":
   "absence-as-signal (item 33, PRIORITIZE deepening) not yet built — lands W3"}`.

**Verdict on the required distinction: ABSENT.** A declared-omission inventory is present and is
unusually thorough; omission *detection* and the smallest admissible next step are not. **F06:
`unexplored`.** The primary proof (seed an omitted cancellation and see whether the layer notices)
was **not run** — seeding requires a write, which this session's read-only mandate forbids.

**Live-path note.** Coverage blocks ship on every elevated `kala_*` response served live from
`marsys-jis-direct` (verified on 7 distinct tools this session).

---

### L3-Q13 — "What reaches the person and survives replay?" (Product §§5.3/10)

**Required added distinction (verbatim):** *"Complete material evidence and conjoint interpretation
through managed channels, narrower raw-tool guarantee."*

**Primary proof (verbatim):** *"A sentinel only in a low-ranked, non-default field reaches the
allowed consumer and saved result."*

**Probe.** **The primary proof was NOT executed.** Planting a sentinel requires a write to
production data; this session's mandate is read-only. Observed instead, as the nearest read-only
surrogate, the behaviour of low-ranked non-default fields under the response-budget trimmer:
```
kala_story_get(chart_id="482012f1-…", budget_kb=14, top_k=40)
kala_elect_get(…, budget_kb=12)
gochara_activation_get(…)                       # default budget 20kb
```

**Today's actual answer.**

- `kala_story_get`: `trim_report` = `[{"path":"chapters","original_count":40,"kept_count":2,
  "reason":"life-arc chapters: floored to 2 (hard-cap)","recover_via":{"instrument":"kala_story_get",
  "hint":"call again with a larger budget_kb for the full chapter list"}},
  {"path":"reading.evidence","original_count":3,"kept_count":1,"reason":"argument evidence: trimmed
  to 1","recover_via":{…}}]`. Loss is declared, and a recovery instrument is named. Note that
  `composed_text` still narrates three chapters (Mercury MD, Ketu MD, Ketu AD) while the structured
  `chapters` array carries two — prose and data disagree on what was delivered.
- `kala_elect_get` at 12 KB: **the `trim_report` was itself trimmed** —
  `[{"path":"(trim_report)","original_count":4,"kept_count":1,"reason":"full trim_report omitted to
  fit budget","recover_via":{"instrument":null,"hint":"no smaller recovery instrument available at
  this budget…"}}]`, with `judgment_flags: [{"code":"budget_exceeded_after_trim","detail":"12kb
  budget still exceeded after full trim."}]`. At that point the record of what was dropped is itself
  among the things dropped, and `recover_via.instrument` is `null`.
- `gochara_activation_get` at its default 20 KB emitted the same
  `budget_exceeded_after_trim` flag, and truncated field *values* inline with the marker
  `…[truncated for budget]` inside `suppression_state.note`, `coverage_quality.note`,
  `source_citation` and `context_only_note`.
- The managed-vs-raw guarantee split is visible in tool descriptions
  (`kala_windows_get`: *"This tool remains the raw low-level primitive"*) but no probed response
  carried a machine-readable field declaring which guarantee the caller was receiving.

**Verdict on the required distinction: COULD NOT VERIFY.** The proof as the strategy specifies it
requires planting a sentinel, which requires a write. What *is* established read-only: budget
trimming does drop low-ranked non-default content; the drop is normally declared with a recovery
pointer; and there is a reachable state in which the declaration itself is dropped and no recovery
instrument is named. **F06: `unexplored`** (the proof was never run against this layer).

**Live-path note.** All three tools live on `marsys-jis-direct` (verified). No live UI caller found
within scope (`platform/src/app`, `platform/src/components`).

---

### P14-A — Product §14 first proving set (1 of 3): a deep structural question with no forced forecast

**Question as the governing text states it (verbatim, Product §14):** *"The first proving set should
include a deep structural question without a forced forecast …"*

**Required added distinction.** Not a Strategy §2 row; the governing obligation is Product §14's
*"Interpretive fidelity — material rivals, qualified manifestation bridge, counter-evidence,
dependence accounting and no unsupported prose added after synthesis"*, discharged without
manufacturing a forecast.

**Primary proof.** A structural reading that stands on cited evidence and declines to forecast.

**Probe.**
```
kala_explain_get(chart_id="482012f1-…", domain="career", max_signals=3)
kala_explain_get(chart_id="482012f1-…", bhava=10,        max_signals=3)
```

**Today's actual answer — the most consequential broken surface found.** Both calls returned
`ok: true` and, verbatim:

```
"reading":{"thesis":"Why for this matter as of today: PACT status: unknown (unrecognized status
                     string — served verbatim, not fabricated).",
           "evidence":[],"dissent":[],
           "verdict":{"statement":"PACT status: unknown (unrecognized status string — served
                                   verbatim, not fabricated).","tier":"structural_prior"},
           "falsifier":null},
"pact_status":"unknown",
"weakest_link":null,
"about":null,
"chain":[],
"fact_id_refs":[],
"pact_drill_pointers":[],
"concordance":null,
"composed":{"full_text":"Why for this matter as of today: PACT status: unknown (unrecognized status
                         string — served verbatim, not fabricated). PACT status: unknown
                         (unrecognized status string — served verbatim, not fabricated).
                         [tier: structural prior — pre-calibration]"}
```

The parenthetical is the serving layer stating that it received a status string from the PACT
capability that it does not recognize, and is passing it through rather than mapping it to something
plausible.

**Verdict on the required distinction: ABSENT.** The surface correctly does *not* force a forecast —
`falsifier: null`, no dates, no probability — and correctly does not fabricate around an
unrecognized status. But it delivers no structural reading either: no evidence, no chain, no rivals,
no counter-evidence, no fact ids, no weakest link. The EXPLAIN view, which is the layer's entire
answer to "why do you say that?", returns a self-describing failure on both a domain and a bhava
route. **F06: `contradictory_unresolved`** — a status value the serving layer itself declares
unrecognized, with no resolution path emitted.

**Live-path note.** Live on `marsys-jis-direct` (verified — failed identically on both routes);
registered at `platform-mcp/src/tools/kala_views/explain.ts`. No live UI caller found within scope
(`platform/src/app`, `platform/src/components`).

---

### P14-B — Product §14 first proving set (2 of 3): a structure–time question with accountable permitted forward claims when earned

**Question as the governing text states it (verbatim, Product §14):** *"… a structure–time question
with accountable permitted forward claims when earned …"*

**Governing obligation.** Product §7.2 *"Preserve the forecast actually delivered"* and §14
*"Predictive performance — frozen eligible claims, valid comparison baselines, observation coverage,
discrimination, calibration and uncertainty without leakage or selective denominators."*

**Probe.**
```
kala_ahead_get(chart_id="482012f1-…", horizon_years=5, max_items=3)
standing_predictions_read(chart_id="482012f1-…", limit=5)
psql -Atc "select count(*) from brahma_prospective_ledger
             where chart_id='482012f1-…' and lifecycle_status='open'
               and lower(observation_window) < '2031-01-01';"   -- 5
```

**Today's actual answer.** `kala_ahead_get`: `windows: []`, `projections: []`,
`predictions_logged: {"windows_examined":0,"filed_count":0,"skipped_count":0,"failed_count":0,
"outcomes":[]}`, `reading.falsifier: null`.
`promise_gate: {"state":"not_applicable","gating_scope":"none","contradicts_served_projections":false,
"reason":"No domain to consult … Not a clean bill of health — nothing was checked."}` — an
unusually precise refusal to let a `not_applicable` read as a pass.

`standing_predictions_read` returned 5 open rows; all five carry populated `claim`,
`event_class`, `claim_shape: "interval"`, `window_start`/`window_end`, `confidence`
(0.695–0.701), a mandatory non-null `falsifier`, `generator_class: "engine"`,
`model: "gochara_v3_w45_builder"`, `formula_version`, `as_of`, `filed_by` and `source_citation`.
Their windows: **2056-02, 2056-11, 2058-10, 2068-09, 2081-08**.
`governance` line asserts filing is explicit and *"chat is never mined."*

Ledger-wide (see L3-Q11): 18 open, **0 ever resolved in any status**, one window expired in 2011 and
still `open`.

**Verdict on the required distinction: ABSENT.** Forward claims are *structurally* accountable —
every row has a window, a confidence, a mandatory falsifier, a named generator and a formula
version, and the filing path refuses to mine conversation. They are not accountable *in practice*:
13 of 18 resolve 30–56 years out, the adjudication lifecycle has never once advanced, and the
structure–time surface that is supposed to earn a claim (`kala_ahead_get`) produced nothing to earn.
**F06: `unqualified`** — claims exist and are typed, but no claim has passed through the evaluation
gate that would qualify it.

**Live-path note.** Both live on `marsys-jis-direct` (verified). No live UI caller found within
scope (`platform/src/app`, `platform/src/components`) other than the generic MCP passthrough route.

---

### P14-C — Product §14 first proving set (3 of 3): a historical challenge that actively seeks misfit

**Question as the governing text states it (verbatim, Product §14):** *"… and a historical challenge
that actively seeks misfit."*

**Governing obligation.** Product §8.3 *"A fair reading of history"* and §7.3 *"Evaluate without
hindsight or leakage."*

**Probe.**
```
mechanism_retrodiction_get(chart_id="482012f1-…", limit=50)
kala_story_get(chart_id="482012f1-…", budget_kb=14, top_k=40)     # per-chapter retrodiction_fit
```

**Today's actual answer — the second-strongest surface measured.**

| bucket | count | per-row disclosure |
|---|---|---|
| confirming firings | **8** across 7 houses | `event_id`, `event_date`, `dasha_level`, `dasha_lord`, `dasha_row_id` |
| `not_confirmed_events` | **25** | `mapped_houses` + reason naming the lord that failed to match |
| `unmapped_events` | **8** | reason naming the unmapped domain prefix |

Misfit outnumbers fit roughly 3:1 and every misfit is enumerated individually with its own reason —
none is aggregated into a ratio or dropped.

`kala_story_get`'s per-chapter `retrodiction_fit` reports `aligned_ratio: 0` on the chapters
returned, with `method: "lexical_theme_keyword_match"` and a note stating verbatim that it is
*"A simple lexical corroboration signal, NOT a calibrated probability or model score"* and that the
*"Sample is small (<3 events) — read this ratio as indicative only."*

Leakage controls are real and enforced, not declared: `sealed_test_split_note` excludes events on or
after 2020-01-01 *"unconditionally … not a caller-settable parameter"*, and `no_leakage_note` states
`life_events` is confirmation-only.

**Verdict on the required distinction: PRESENT.** **F06: `applied`.** This is the one case in the
baseline where the surface actively produces the disconfirming evidence rather than the confirming
evidence, and reports a 0.0 fit ratio without softening it.

**Live-path note.** Live on `marsys-jis-direct` (verified). No live UI caller found within scope
(`platform/src/app`, `platform/src/components`).

---

### ORD-1 — the ordinary-period case (Product §9)

**Question as the governing text states it (verbatim, Product §9):** *"The experience must work for
ordinary charts and ordinary periods, not only dramatic named yogas or the repeatedly studied native
chart."*

**The window chosen, and why.** Vimśottarī **level-3 (pratyantardaśā) window
2014-08-23 → 2014-11-17, lord Moon, `ayanamsha_id = lahiri_chitrapaksha`**.

Selection was made by query, not by taste:

```sql
select d.level_n, d.lord_graha, d.start_date, d.end_date,
       (select count(*) from life_events e
         where e.chart_id = d.chart_id
           and e.event_date >= d.start_date and e.event_date < d.end_date) as lel
  from chart_dashas d
 where d.chart_id='482012f1-710e-4a25-994a-93821f5871aa'
   and d.system_id='vimshottari' and d.ayanamsha_id='lahiri_chitrapaksha'
   and d.level_n=3 and d.start_date between '2014-06-01' and '2015-12-01'
 order by d.start_date;
-- 3|Sun    |2014-07-02|2014-08-23|0
-- 3|Moon   |2014-08-23|2014-11-17|0     <-- chosen
-- 3|Mars   |2014-11-17|2015-01-17|0
-- 3|Rahu   |2015-01-17|2015-06-21|0
-- 3|Jupiter|2015-06-21|2015-11-06|1
-- 3|Saturn |2015-11-06|2016-04-18|0
```

Four independent reasons it is ordinary: (a) **zero** logged life events in the span, verified by the
query above; (b) no named yoga can fire in it — `kala_activation` holds 0 rows for this chart at any
date (BF-1), so there is no dramatic firing available to rescue the answer; (c) it is not a
mahādaśā or antardaśā boundary and not inside any sandhi band; (d) it sits mid-way inside the long
Mercury mahādaśā, so no chapter change drives it. A same-grain check at the antardaśā level found
**every** lahiri AD between 1991 and 2010 carries at least one logged event — level 3 is the
finest grain at which a genuinely event-free window of this chart exists.

**Probe.**
```
kala_priority_get(chart_id="482012f1-…", date_from="2014-08-23", date_to="2014-11-17", top_k=3)
gochara_activation_get(chart_id="482012f1-…", as_of_date="2014-10-01", domain="health")
```

**Today's actual answer.**

`kala_priority_get`: `ranked_signals: []`, `signal_count: 0`,
`neutral_dignity_downranked_count: 0`, `excluded_internal_marker_count: 0`,
`catalog_only_rows_in_page: 0`. Thesis verbatim: *"No priority-ranked signals activation-overlap
2014-08-23–2014-11-17 for this chart."* Verdict verbatim: *"Honest empty — nothing to triage in this
window."* Three separately-reasoned coverage states (as in L3-Q08).

`gochara_activation_get`: 3 windows returned — `chronic_onset`, `surgery`, `illness_acute`. **All
three have `window_start: "2014-02-05"` and `window_end: "2024-01-31"` — a ten-year span** — and all
three carry `signed_intensity: 0.28`, `calibration_state: "structural_prior"`,
`era_slice_key: "g3_2014_2024"`. `facets.resolution: {"era":1,"month":0,"day":0,"unavailable":2}`.
`context_only_rows_in_page: 3` of 3, with `context_only_note` stating they are
*"era-scale/unresolved CONTEXT, not timing windows (PK-R-1)"*, and every row's
`resolution_disclosure.is_timing_window: false` with a `timing_window_blocked_reason`
(`era_resolution`, `point_class_context_envelope` ×2).

One further shape observation: each row's `term_breakdown.activity_terms` are the terms that produced
its *peak*, dated **2023-04-04…2023-04-12** and **2017-05-06…2017-05-15** — three to nine years away
from the 2014-10-01 date the call asked about. A row is "active on 2014-10-01" only because a decade
envelope covers that date; the evidence attached to it is not evidence about that date.

**Verdict on the required distinction: ABSENT.** On an ordinary date this layer returns either
nothing at all, or a decade-wide context envelope whose supporting evidence sits years away —
correctly *labelled* as context and not as timing, which is genuinely to its credit, but not an
answer. **F06: `unavailable`** for the activation layer; the gochara response is correctly
`inapplicable` as a timing claim and says so.

**Live-path note.** Both live on `marsys-jis-direct` (verified). No live UI caller found within
scope (`platform/src/app`, `platform/src/components`) other than the generic MCP passthrough route.

---

## 3. Lane E's sixteen mapped onto L3-Q01–Q13

`LANE_E_LAYER_VALUE_MODEL.md` §1 carries a sixteen-question portfolio (Q-K01…Q-K16). It is **not**
baseline authority — Strategy §2's thirteen are. This table is the mapping critical review C3/D1
requires, and it is a mapping, **not an adoption**. No Lane E finding is inherited here; where this
session measured the same thing live, the live measurement is the record (see the Q-K08 note).

| Lane E | Lane E question (short) | Maps to | Mapping note |
|---|---|---|---|
| Q-K01 | What is running right now, on every clock that applies to me? | **L3-Q01** | Direct. Lane E adds the *applicability-vs-computability* adjudication across the 6 declared ayanamsha variants and 7+ daśā systems; Strategy §2's "qualified clocks are engaged" already carries it. |
| Q-K02 | Which mechanisms are in an activation window, which dormant? | **L3-Q01 + L3-Q03** | Splits across two. The "whole mechanism set, not a top-N" partition requirement is an addition Strategy §2 does not state explicitly → **candidate strategy amendment (minor)**. |
| Q-K03 | Exactly when does my antardaśā end, to the hour? | **L3-Q01** (grain sub-case) | A precise-lookup sub-case, not an independent question. Answerable at L1 by reference (§N.5); Lane E's own point is that L3 loses the hour. |
| Q-K04 | When do two domains coincide, and which dominates? | **L3-Q07** | Direct. Lane E's "a *stated* dominance rule, not implied by score ordering" sharpens Strategy §2's "enabling or inhibiting roles". |
| Q-K05 | Is the 2027 window stronger than the 2019 one? | **L3-Q02 + L3-Q06** | Head-to-head strength comparison. Lane E's *time-symmetry* constraint (a proximity term makes the comparison meaningless) is **not** in Strategy §2's L3-Q02 → **candidate strategy amendment**. |
| Q-K06 | Which clocks disagree about H2-2028, and why? | **L3-Q05** | Direct. |
| Q-K07 | How confident are you, and what would change your mind? | **L3-Q05 + L3-Q13** | Confidence *typing* (units/denominator/horizon/basis) sits under L3-Q05's "non-comparable scales"; the falsifier-that-resolves-by-a-date obligation sits under Product §7 via L3-Q13. |
| Q-K08 | Rising, cresting or decaying — trajectory, not snapshot? | **L3-Q06 + L3-Q07** | Trajectory over a chapter. **Live-measurement divergence:** Lane E states the `kala_taranga` transit term is 0.0 on all 92,412 rows; measured live 2026-09-22 it is 0 on 56,130 (60.7%), mean 0.2490, max 1.0. Recorded, not adjudicated (see L3-Q07). |
| Q-K09 | I need to sign in the next 90 days — when? | **L3-Q10** | Direct. |
| Q-K10 | …and if there is genuinely no good time, say so. | **L3-Q08 + L3-Q10** | Negative-election case. Confirmed live: `kala_elect_get` emits a `frontier` with `gold_tier_present: false` and a `gap_report`. |
| Q-K11 | When does this pattern fire again — is that the complete list? | **L3-Q08** | Recurrence completeness = coverage. Lane E's "any cap must be disclosed as a cap" is the same obligation as Strategy §2's "searched horizon, resolution". |
| Q-K12 | You said four things point at 2029 — are those four actually four? | **L3-Q05** | Provenance-aware de-correlation = Strategy §2 L3-Q05's "shared roots". Confirmed absent live (no producer-provenance de-correlation on any surface). |
| Q-K13 | Am I in a sandhi right now? | **L3-Q01** (boundary sub-case) | Sub-case of L3-Q01's "contact". Live: `dasha_sandhi` bands ARE served at levels 1–4 with a self-disclosing `band_convention` — better than Lane E's date-grain-only account describes. |
| Q-K14 | Is this an unusual period for me, or an ordinary one? | **maps to nothing → candidate strategy amendment** | Within-chart rarity / percentile has no L3-Q01–Q13 addressee. It is the closest existing analogue to the **ORD-1** case this baseline had to construct, and is the strongest argument for adding a fourteenth Strategy §2 row on ordinariness/rarity. |
| Q-K15 | Is there genuinely nothing in Q3 2027, or is something not built? | **L3-Q08** | Direct, and the sharpest statement of it. |
| Q-K16 | Re-derive the 2019 window without hindsight. | **L3-Q11** | Direct. Lane E's *reproducibility* constraint (a re-derivation that depends on `date.today()` is not the computation that ran in 2019) is not in Strategy §2's L3-Q11 → **candidate strategy amendment**. |

**Dropped: none.** All sixteen map, except Q-K14 which maps to nothing.

**Four candidate strategy amendments surfaced by the mapping** (recorded, not authorized): a
whole-set partition requirement (Q-K02); time-symmetry of any strength comparator (Q-K05);
re-derivation reproducibility (Q-K16); and an ordinariness/rarity question with no current
addressee (Q-K14).

---

## 4. Summary table

| case_id | distinction present? | F06 state | live caller? | one-line note |
|---|---|---|---|---|
| L3-Q01 | **no** | `unavailable` | MCP live; no UI caller in scope | `windows: []`, `darshana: null`; rich ancillary panchāṅga/gochara detail around an empty core. |
| L3-Q02 | **no** | `unavailable` | MCP live; no UI caller in scope | 0 candidates to rank; `temporal_closure` claims exhaustive completeness on that zero. |
| L3-Q03 | **no** | `unavailable` | MCP live; no UI caller in scope | 0 yoga signals join to `kala_activation`; but a real live detector returned 0/73,049 orphan fact refs. |
| L3-Q04 | **no** | `unavailable` | MCP live; no UI caller in scope | Obstruction + convergence both empty; bundle reports bare `0`, no `empty_reason`. |
| L3-Q05 | **no** (3 of 5 components present) | `unqualified` | MCP live; no UI caller in scope | KP voice with `ayanamsha_divergence: true` is real; both engines `not_comparable`; no provenance de-correlation. |
| L3-Q06 | **no** | `unexplored` / `contradictory_unresolved` | MCP live; no UI caller in scope | `developmental_thesis` not built; chapters serve 8,838 convergence counts against 0 live rows. |
| L3-Q07 | **no** | `unexplored` | MCP live; no UI caller in scope | Per-domain series exist (24 domains); no intersection, no roles, no dominance rule. |
| L3-Q08 | **YES** (one named defect) | `unavailable` held apart from `inapplicable`, in prose only | MCP live; no UI caller in scope | Best negative-reporting discipline in the layer; `temporal_closure` is the one field that undoes it. |
| L3-Q09 | **no** | `unqualified` | MCP live; no UI caller in scope | Variants genuinely recompute (MD flips Mercury→Ketu); no comparison surface; gochara has no ayanamsha column. |
| L3-Q10 | **YES** | `applied` | MCP live; no UI caller in scope | 2 candidates, named criteria kept separate, Pareto with 3 excluded axes, census 39/5/7, uncancelled doṣas declared. |
| L3-Q11 | **YES** (retrodictive half only) | `applied` / `unexplored` | MCP live; no UI caller in scope | 8 fits vs 25 explicit misfits vs 8 unmapped; ledger 18 open, 0 ever adjudicated. |
| L3-Q12 | **no** | `unexplored` | MCP live (7 tools) | Thorough *declared* gap inventory; one mechanically-derived exception; no detection, no next-step ranking. |
| L3-Q13 | **COULD NOT VERIFY** | `unexplored` | MCP live; no UI caller in scope | Sentinel plant requires a write; read-only mandate. Trim declares loss — except when the trim report is itself trimmed. |
| P14-A | **no** | `contradictory_unresolved` | MCP live; no UI caller in scope | `pact_status: "unknown (unrecognized status string…)"`, `chain: []` on both domain and bhava routes. |
| P14-B | **no** | `unqualified` | MCP live; no UI caller in scope | 18 open claims, 0 ever resolved; 13 resolve 2056–2082; one window expired in 2011 still `open`. |
| P14-C | **YES** | `applied` | MCP live; no UI caller in scope | Misfit outnumbers fit ~3:1 and every misfit is individually reasoned; sealed split is code, not a parameter. |
| ORD-1 | **no** | `unavailable` / `inapplicable` | MCP live; no UI caller in scope | Ordinary window → honest empty, or a 10-year envelope whose evidence terms are 3–9 years away. |

**Tally: present 4 · absent 12 · could-not-verify 1.**

---

## 5. What this baseline does NOT establish

1. **It does not establish that the L3 code is wrong.** Twelve of the seventeen absences trace to a
   data condition, not a logic condition: five assets record large writes in `asset_throughput`
   while their target tables hold zero rows for this chart (BF-1). The same code on
   `1c826d5a-41cb-4450-b4dc-59d440e5f75a` may answer several of these questions. This baseline
   measured **one chart**, the canonical one, because that is the chart the campaign's questions are
   asked about. Per F24, computational correctness, explanatory value and empirical performance are
   separate tiers; this document measured mostly the second and only incidentally the first.

2. **It does not establish that the surfaces' own coverage states mean what F06 means.** No probed
   surface emits an F06 state. They emit `{computed, honest_empty, not_in_corpus}` (the `kala_*`
   views), `{applied-ish free text}` (empty_reason prose), `{insufficient_data, not_applicable,
   not_comparable}` (engine testimony), and `{era, month, day, unavailable}` (gochara resolution).
   **Every F06 assignment in §2 is this document's own mapping from observed shape**, not a reading
   of a field. Whether `computed` on an empty array means `applied`, `unavailable` or
   `contradictory_unresolved` is exactly the ambiguity F06 exists to remove, and it is unresolved in
   the served data.

3. **It does not establish the cause of BF-1.** Whether the canonical chart's `kala_activation` /
   `kala_convergence` / `kala_darshana` / `kala_bhavishya` / `kala_obstruction` rows were deleted, a
   rebuild was interrupted, or a chart-scoped purge ran, is **not** determined here. Only the state
   is recorded: `asset_throughput` and the tables disagree, as of 2026-09-22T11:38Z.

4. **It does not establish whether `asset_throughput` is correct for any other chart.** The
   throughput-vs-table divergence was measured for `chart_id = 482012f1…` only.

5. **It does not run the Strategy-named primary proofs.** Nine of the thirteen L3-Q primary proofs
   are *perturbation* proofs — perturb a condition, remove a method, destroy a bridge, seed an
   omission, plant a sentinel. All of them require either a write or a build run, both forbidden to
   this session. For eight of those nine the proof is additionally moot today because the thing to
   be perturbed does not exist (no engaged condition, no second method verdict, no structural
   bridge). **L3-Q13's proof was not run for the mandate reason alone and should be re-attempted the
   moment a write-capable, non-production fixture exists.**

6. **It does not adjudicate the divergence from Lane E on `kala_taranga.transit_contribution`.**
   §3 records both figures and names the disagreement; resolving it requires establishing when the
   rows were written and against what, which is a separate investigation.

7. **It does not establish live-caller *absence*.** Every "no live caller found within scope" in §2
   names its scope exactly: `grep -rlF "<tool_name>" platform/src/app platform/src/components`, with
   the broader `platform/src platform-mcp/src platform/python-sidecar` counts noted separately. A
   caller outside those trees — a scheduled job, an external orchestrator, the deployed portal's own
   server bundle, or a consumer reaching the MCP server directly as this session did — would not
   appear. **The tools are demonstrably reachable and answering: every probe in §2 was a live call
   against the deployed `marsys-jis-direct` server.** "No caller found within scope" is never
   "unused."

8. **It does not measure the `claude.ai Marsys JIS` OAuth-gated MCP server.** That server requires
   an interactive OAuth flow unavailable in this session. All MCP evidence here is from
   `marsys-jis-direct`. Whether the OAuth-gated surface returns the same envelopes is **COULD NOT
   VERIFY: not probed, no interactive authorization available.**

9. **It does not measure latency, cost, concurrency or failure-under-load.** Nor does it measure any
   portal/UI rendering of these responses.

10. **It does not establish that the four PRESENT cases generalize.** L3-Q08, L3-Q10, L3-Q11 and
    P14-C were measured on one chart, on one date, at one budget. Per Product §14, *"Development on
    the familiar native chart is not independent evidence of generalization."*

---

*End of KALA_BASELINE v1.0 — frozen 2026-09-22. This artifact authorizes no change. It is the
measurement against which L3 elevation is to be judged.*
