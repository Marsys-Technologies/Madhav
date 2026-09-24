---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_YOJAKA_ELEVATION_BRIEF
version: "1.0"
status: DRAFT_FOR_INDEPENDENT_REVIEW      # → PROPOSED_FOR_NATIVE_RULING after the Fable 5.1 review
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / blob 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md   # adopted by reference; B-rows in §7
asset_or_interface_ids: ["ka_yojaka", "L3-U01 (L2→Yojaka binding)", "L3-U07 interface to ph_nimitta (per-domain map)", "SC-9 (generation binding; orphan detector)"]
goal_objective: "Make ka_yojaka's predicates bind to an identified L2 generation rather than a bare signal_id, detect and declare orphaned references instead of carrying them silently, type each predicate's datability honestly, and deliver the per-domain structure it already persists to the consumer that today reads one scalar of it."
source_revision: "9feac52d7 (l3/kala-layer-briefs; = origin/l3/kala-elevation-readiness tip 2026-09-24)"
accepted_upstream_contract: "L2_STRUCTURAL_PROPOSITION_AND_RELATION_CONTRACT/1.0/blob-0cc75ffcf1e3a018265a3efde6cd8b666388f586; L2_PRODUCER_READY_ACCEPTANCE (e5307fadef); bodha_signal_identity (migrations 660/661: deterministic signal_id over (chart, ayanamsha, signal_type, varga, configuration)); L1 ga_yoga_firings.constituent_planets; the accepted Yojaka repair 7697c43b3 (per-domain map restored)"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_YOJAKA_v1_0.md"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/pipeline/orchestrator/writers/ka_yojaka.py", "platform/python-sidecar/services/ka_yojaka/{binder,classifier}.py", "platform/python-sidecar/tests/l3/test_ka_yojaka*.py", "one additive migration on kala_activation_predicates (generation/reference columns; no FK)", "interface packet only: platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts, platform-mcp/src/tools/kala_views/{ahead,now}.ts; L4 packet for ph_nimitta.py:478-486"]
must_not_touch: ["bodha_msr_signals / bodha_writers/_idempotency.py (L2-owned; the diff-based upsert is an L2 proposal, Lane F §3.4)", "ga_yoga_firings (L1)", "pipeline/orchestrator/writers/ph_nimitta.py (L4, sealed — interface packet only)", "ka_sangam.py, ka_kalasutra.py, ka_vighnakara.py, ka_jivana_parva.py (readers; their briefs)", "migration 403's CASCADE set — this brief adds NO foreign key", "applied migrations", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY (stage 3); DATA_ACCEPTED only on an accepted L2 generation (W1/W2); CONSUMER_INTEGRATED when Kalasutra/Saṅgam read the generation-bound reference and L4's packet reads the map"
target_state_campaign: "ANALYZED → ENRICHED at stage 3; a superseded t2 freeze exists and is inadmissible under t3"
wave: "W2 (first row frontier)"
shape: single asset, rows (chart × ayanāṃśa × signal × predicate signature)
evidence_base: >
  Source read directly on 9feac52d7 [V]; Lane D §16, T1 Spine item 2, Lane F §1c/§2c/§3.1/§3.4,
  KALA_DATA_CENSUS §4a (79/50,678 anti-join, 2026-09-22) [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.0 (2026-09-24): first issue; awaiting independent review."
---

# `ka_yojaka` elevation brief — the bridge from structure to time, bound to a generation

## §0 — The recommendation, in one paragraph

`ka_yojaka` is the layer's compiler: every L2 MSR signal becomes a typed activation predicate,
its real firing lords are resolved from **L1** (`ga_yoga_firings.constituent_planets`, dosha
facts) rather than re-derived, and a signal that cannot honestly be dated stays `UNDATED` with an
inspectable `always_on_reason` — the anti-fabrication design is genuinely careful
(`ka_yojaka.py:15-26, 938-995` [V]). Its accepted repair (`7697c43b3`) restored the per-domain
confirmation/strength/promise map that consumers had flattened. What it does **not** do is bind
its input: it reads every `bodha_msr_signals` row for the chart with no generation and no
ayanāṃśa filter (`:80-87` [V]), stores `signal_id` as a bare value with **no foreign key** (Lane F
§3.1, live-confirmed), and so **79 of 50,678 rows point at signals that no longer exist** (0.156%,
census §4a) — orphaned silently when L2 regenerated, invisible to every consumer. Meanwhile the
one L4 reader consumes only `multi_system_confirmation_count`, the primary-domain scalar, and
drops the map (`ph_nimitta.py:478-486` [A: Lane F §1c]; `primary_domain = domains[0]` at `:886`
[V]). Recommendation: **`ENRICH_CORRECT` + `INTEGRATE`** — a generation-bound reference
(`signal_ref = {producer, generation, signal_id}` under binding B3; **no CASCADE FK**, which would
turn the table into a destruction surface), an orphan detector at build and at serve
(`completeness_state='unavailable'`, reason `signal_orphaned`), the two `always_on_reason`s mapped
to two distinct F06 states (`inapplicable` for a distribution yoga, `unavailable` for no
resolvable lord), a `coverage` payload (compiled / undated-by-reason / orphaned), `primary_domain`
labelled the compatibility scalar it is, and an L4 interface packet so the map reaches
`ph_nimitta`. One additive migration. Decision for the native: the orphan policy (§10).

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 (REGISTER:147) | *"Typed activation predicates and fired-yoga participant lookup. P/E/I/Q/C: full mechanism compiler; preserve paired CDLM signals/roles and method key, not net domain average. DP05/06/08."* | unchanged |
| Strategy §6.1 **L3-A11** | *"Compile complete accepted L2 mechanisms, participants, signed multidomain relations, cancellation and all linked roots. Remove one-domain/five-link flattening with explicit migration; preserve distinct convention and mode context."* W2 | the map is persisted (repair); the scalar path and L4's read still flatten (§3) |
| Strategy **L3-U01** | *bind real producer fields, generations, signed routes, complete domains/roots… hydration must use exact accepted snapshots*; test: *changing retention opposition affects that route; unrelated configurations stay stable* | binds §4 and §7 |
| Strategy §3 (connected-DB check) | *"79 predicate signal IDs do not join to current same-chart MSR"* | census re-confirmed 79/50,678 [A] |
| Strategy §6.3 | Yojaka + Vedha + services + raw L0–L2 → Saṅgam; Yojaka → Kalasutra / Vighnakara / Jivana | consumers confirmed [V] (§2.3) |
| CURRENT_STATE §4.1 | *"first frontier; non-FK signal refs guarded"* | the guard does **not** exist on this base — the SELECT filters nothing, the INSERT adds nothing (§2.2); this is the delta |
| W0 register #22 | `kala_activation_predicates`; JSONB payloads (Q2/Q4/QX shapes closed gates) | the map lives inside `dasha_eligibility_rule_jsonb` — a JSON shape, so its consumer contract is exactly the open-shape gate the register names |
| Lane D §16 / T1 Spine 2 | `stale`, 50,678 rows matching `rows_written`; not wiped by the cascade (its `bound_at` post-dates the rerank); consumer binding low-medium; the "flattening at :479-510" citation could not be relocated | consumer binding confirmed here [V]; the flattening is at `:886` and at L4's read, not at `:479` (§2.2) |
| Lane F §1c, §2c | `ka_yojaka.py:845-917` persists `cdlm_domain_strength_by_domain`, `multi_system_confirmation_by_domain`, `pratijna_ids_by_domain`; `ph_nimitta:479` reads only the scalar; `primary_domain = domains[0]` is now a documented compatibility scalar | confirmed [V] (`:332-344, :886`) |
| Lane F §3.1, §3.4 | no FK from `kala_activation_predicates` to `bodha_msr_signals`; orphans are silent; the stable identity is `bodha_signal_identity(chart, ayanamsha, signal_type, varga, configuration)` (migrations 660/661) — "a genuinely survivable binding" would store the tuple/hash as a plain value, not a CASCADE FK | adopted (§4 item 1) |
| Synergy binding B3 | L2 identity = Yojaka's natural key, never a reassigned bigserial; `window_ref` as the cross-asset handle | Yojaka is the *source* of the L2 identity for the layer — this brief defines `signal_ref` |
| Blueprint v5.0 §3.5 row 5, §16.2 | orphan detector; `domain_map_basis`; L4 interface packet; `primary_domain` compatibility-only | binds §4 |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V seed]
`asset_registry_seed.ts:2360-2369`: `storage_type: 'postgres_table'`, `target_table:
'kala_activation_predicates'`, chart-scoped `count_sql`, `depends_on: ['bo_laksana',
'bg_transit_rules', 'ga_dashas', 'bo_bimba', 'bo_sangati', 'bo_pratijna', 'bg_ghatana']` (seven
edges, the widest in the layer), `scope: 'per_chart'`, `estimated_seconds: null`.

### 2.2 The code [V]
- `@register('ka_yojaka')` (`:61`); `dry_run` returns without a cursor (`:69-70`).
- **Input read** (`:78-89`): `SELECT signal_id, chart_id, ayanamsha_id, signal_type_class,
  signal_type_id, configuration_jsonb, constituent_facts_array, valence, dignity_score,
  shadbala_norm, domains_affected_array, domain_salience_jsonb, contradicts_signals_array FROM
  bodha_msr_signals WHERE chart_id = %s` — **no `build_id`, no generation, no `ayanamsha_id`
  filter**; every current MSR row for the chart, whichever of the seven L2 producers and whichever
  build wrote it. Empty → `"no bodha_msr_signals; prior predicate partition preserved"` (`:92-96`)
  — good (empty candidate preserves capital).
- **Firing lords** (`:268-277`, `_resolve_firing_lords` `:938-995`): YOGA → `ga_yoga_firings.
  constituent_planets` keyed by `yoga_canonical_id` (`:608-619`); a distribution (Nābhasa) yoga →
  `[]`, `'distribution_yoga_all_grahas'`, source `ka_yojaka:ga_yoga_firings` (`:988`); DOSHA →
  the fired dosha's graha facts; catalog-only doshas stay `UNDATED`.
- **Generalised honesty** (`:390-407`): every predicate still empty after all fallbacks gets
  `constituent_lords=[]`, `always_on_reason='no_resolvable_dasha_lord'`,
  `constituent_lords_source='ka_yojaka:no_resolvable_lord'` — added after #2456 found *9,347 of
  9,367 undatable rows* carried no reason. Two reasons now exist and are deliberately distinct.
- **Structural enrichment** (`:316`, `:332-348`, `_build…` `:845-903`): `cgm_centrality_weight`
  from `bodha_cgm_nodes` pagerank (`:538`), CDLM strength from `bodha_cdlm_cells` (`:573`);
  `domain_salience_by_domain`, `cdlm_domain_strength_by_domain`, `pratijna_ids_by_domain`,
  `multi_system_confirmation_by_domain`, `multi_system_confirmation_count`,
  `primary_domain = domains[0] if domains else None` (`:886`),
  `multi_system_confirmation_aggregate_rule='primary_domain_v1'` (`:344`); `contrary_signal_ids`
  into the strength hook (`:348, :926`).
- **Write** (`:426-448`): rows `(chart_id, ayanamsha_id, signal_id, signature_class, four JSONB
  payloads)`; `DELETE … WHERE chart_id` **after** the full candidate exists (`:440-445`, replace
  never accretes, §N.3); `INSERT … ON CONFLICT DO NOTHING` (`:431`); batches of 1000.
- **No orphan detection in the writer** [V: no anti-join, no `EXISTS`, no resolver against
  `bodha_signal_identity`]. **A detector does exist at integrity-check time**: migration
  `670_nirmana_l3_w3_integrity_contracts.sql:1738-1819` installs `ka_yojaka`'s
  `integrity_check_sql` with conjunct (a) — every predicate's `signal_id` must still exist for the
  same chart and ayanāṃśa (`:1747-1759`, *"the table carries no foreign key, so a bo_laksana rebuild
  that re-issues signal_ids leaves the whole predicate set pointing at dead rows and nothing
  notices"*), (b) the reverse coverage, (c) `UNDATED` must carry `always_on_reason` (`:1772-1783`;
  the 27,681-row finding this writer's `:390-407` generalisation closed), (d) lord provenance,
  (e) ledger resolution, (f) no hollow payloads [V]. So the orphan is detected **only when the
  integrity check runs**, never at build or at serve — the check is chart-partitioned and reads
  false today on a cascade-damaged chart by design (670 header, `:22-35`).

### 2.3 Consumers (grep on this base, tests excluded) [V]
| consumer | reads | role |
|---|---|---|
| `writers/ka_sangam.py` (+ `services/ka_sangam/engine.py`) | predicates: `transit_trigger_jsonb`, `dasha_eligibility_rule` (Saṅgam R-1 stamps target provenance onto `transit_trigger_jsonb` — writer-side) | `computation` |
| `writers/ka_kalasutra.py` | `dasha_eligibility_rule.constituent_lords`, `always_on_reason` (emits `kind:'always_on'`) | `computation` |
| `writers/ka_vighnakara.py` | predicates for daśā-anchored obstruction rows | `applicability` |
| `writers/ka_jivana_parva.py` | LATERAL `LIMIT 1` predicate per window (`:113-124`) | `interpretation` |
| `writers/ph_nimitta.py:478-486` (L4, sealed) | `signal_id` + `(dasha_eligibility_rule_jsonb->>'multi_system_confirmation_count')::int` **only** | `computation` (L4) |
| served | `query_temporal_activation.ts`, `kala_views/ahead.ts`, `kala_views/now.ts` | `relevance_navigation` |

**Live-path statement.** All six reads are live. The 79 orphans are live rows on every one of
them; nothing on any path distinguishes an orphaned `signal_id` from a valid one.

### 2.4 Epistemic class of the important fields
| field | class | authority | note |
|---|---|---|---|
| `signal_id` | identity reference | L2 (`bodha_signal_identity`, deterministic since 660/661) | stored bare; no generation; no detector |
| `constituent_lords` | `COMPUTED_FACT_CONFIGURATION` (references) | L1 `ga_yoga_firings` / facts | correct authority (§N.5) |
| `always_on_reason` | honest state | this writer | two reasons = two F06 states (§4 item 3) |
| `cgm_centrality_weight`, CDLM strengths | navigation scores | L2 | *navigation aids, not proof* (VA §6.3) — must never gate |
| per-domain map | structural (signed multidomain preserved) | L2 via this writer | persisted; **consumed by nobody in full** |
| `primary_domain` | compatibility scalar | this writer (`:886`) | documented; still the value L4 uses |
| `dasha_activation_proximity_score` | engineered | this writer (CR-5/12/48 wall fix) | `tier_basis='relative_uncalibrated'` owed |

### 2.5 Ladders and cost
`PLAN_REVIEWED`; repair accepted; W2 frontier. t3: t2 freeze inadmissible. Cost: 50,678-signal
fan-out, single-instant batch write (`bound_at` 2026-09-10 17:17:03, census) — the build completes;
duration **unmeasured**.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | Regenerate any of the six MSR producers for the chart (`bo_laksana` did, 2026-09-08/11): `bodha_msr_signals` rows are deleted and re-inserted with deterministic ids; signals whose configuration changed get **new** ids; `kala_activation_predicates` keeps the old ones. Result on the canonical chart: 79 rows whose `signal_id` resolves to nothing (`census §4a` anti-join), served through `query_temporal_activation.ts` and consumed by Saṅgam/Kalasutra/L4 as ordinary predicates. A rebuild of Yojaka would replace them — but nothing *triggers* one, and nothing *detects* that one is needed |
| Evidence | `ka_yojaka.py:80-87` (unfiltered read), `:426-431` (bare `signal_id` INSERT), no anti-join in the writer or on any consumer path [V]; the only detector is the registry `integrity_check_sql` (migration 670 `:1752-1759`), which runs at integrity-check time, not at build or serve [V]; `pg_constraint`: no FK from this table to `bodha_msr_signals` (Lane F §3.1 live) [A]; 79/50,678 [A: census 2026-09-22] |
| Expected contract | L3-U01 (*hydration must use exact accepted snapshots*); Strategy §4 step 3 (*bind one compatible transitive dependency vector… no implicit fall-through to mutable public rows*); F09 (compatible dependency sets, never `latest`); F22 (freshness detector); DP06 (ancestry) |
| Defect class | **stale/mixed generation** (no producer generation on the row) + **detector mismatch** (an orphan reads as a predicate) + **wrong authority at the consumer** (L4 reads the scalar of a map that exists) |
| Impact | Q03's *complete activation route* can be computed for a mechanism that no longer exists; Kalasutra dates it, Saṅgam converges on it, L4 anchors on it — a chain of L3/L4 rows with no living L2 root; conversely a *changed* mechanism keeps its old predicate until someone remembers to rebuild |
| Non-claim | No claim that any of the 79 reached a served reading or an L4 anchor — unmeasured; no claim about L2's rebuild policy (the diff-based upsert is L2's proposal); the 79 count is a 2026-09-22 snapshot and may already differ |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q03 (the complete route — this asset compiles it), Q01 (which exact structure
   is engaged), Q-K02 (activated vs dormant over the *whole* mechanism set). Cannot serve any
   timing question by itself (no instants).
2. **Generation-bound reference (B3, SC-9).** Each row gains `signal_ref = {producer_asset_id,
   l2_generation, signal_id, signal_identity_tuple_hash}` where the hash is
   `bodha_signal_identity(...)` recomputed from the *consumed* signal's own fields at bind time —
   so the reference survives an L2 rebuild that keeps the identity, and **detects** one that
   changes it. **No CASCADE FK** (Lane F §3.4; a FK would make this table the sixth cascade
   surface). Until L2 publishes generations (W1), `l2_generation` carries the consumed
   `bodha_msr_signals.build_id`s as a receipt (`consumed_msr_build_ids[]`), declared as such.
3. **Orphan detector at build and at serve** (the 670 contract's conjunct (a) moved to where it
   can act). Build: after the candidate is compiled, an anti-join against the current MSR; any
   dangling reference is written with
   `completeness_state='unavailable'`, `reason='signal_orphaned'`, never silently as a predicate.
   Serve/consume: a shared `resolve_signal_ref()` (in `services/ka_qualification/identity.py`,
   SC-3) that Kalasutra, Saṅgam, Vighnakara and the served surfaces call; unresolved →
   `unavailable`. A freshness detector (F22): `stale_against_msr: bool` computed from the consumed
   build ids vs the current ones.
4. **Two honest states, not one label (B2).** `always_on_reason='distribution_yoga_all_grahas'`
   → `completeness_state='inapplicable'` (no single activating lord exists *by doctrine*);
   `'no_resolvable_dasha_lord'` → `completeness_state='unavailable'` (L1 could not supply one —
   a gap, not a doctrine). Both keep `always_on_reason` verbatim. `epistemic_class=
   'COMPUTED_FACT_CONFIGURATION'` on lords (references), `'INTERPRETIVE_INFERENCE'` on the proximity
   score and the CGM/CDLM weights; `operator_role='applicability'` on the eligibility rule,
   `'relevance_navigation'` on the weights (they must never gate — VA §6.3);
   `tier_basis='relative_uncalibrated'` on every score; `comparable_with` n/a (predicates are not
   scores) — stated.
5. **The map reaches L4 (U01/U07 interface packet).** `ph_nimitta` reads
   `multi_system_confirmation_by_domain`, `cdlm_domain_strength_by_domain`, `pratijna_ids_by_domain`
   (already persisted) with `domain_map_basis='primary_domain_v1'` beside; `primary_domain` and
   `multi_system_confirmation_count` stay as the labelled compatibility scalar for one generation
   (L4 is sealed — additive only, its packet decides adoption).
6. **Ayanāṃśa context (SC-10, B1).** The input read pins the accepted ayanāṃśa vector (today:
   canonical `lahiri_chitrapaksha`, or all five explicitly as separate partitions) instead of
   reading every ayanāṃśa's signals into one candidate; `ayanamsha_id` is already on the row.
7. **Coverage (B5).** `WriterResult.notes` and a `coverage` column on the partition summary:
   `{signals_read, predicates_compiled, undated_inapplicable, undated_unavailable, orphaned,
   consumed_msr_build_ids}`; an empty candidate remains "prior partition preserved" **with** that
   coverage.
8. **Old vs new.** Positive: a yoga with resolvable lords → `applied`, `signal_ref` complete.
   Negative: a catalog-only dosha → `inapplicable`, undated, as today. Boundary: an L2 rebuild that
   keeps a signal's identity → `signal_ref` resolves, `stale_against_msr=false`. Missing: an L2
   rebuild that drops a signal → the predicate `unavailable/signal_orphaned`, visible on every
   consumer. Duplicated: the same signal under two ayanāṃśas → two partitions, never merged.
9. **Simpler baseline.** Today's bare `signal_id` rows.
10. **Ablation (U01's own test).** Change one signal's `contrary_signal_ids` (retention opposition)
    in a fixture MSR: exactly that predicate's `strength_affliction_hook` changes; geometry and
    unrelated predicates are byte-identical. Seed one orphan: it is reported, and Kalasutra's
    consumer test refuses to date it.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: the L1-sourced firing-lord resolution (`:938-995`); the two `always_on_reason`s; the
  empty-candidate-preserves-capital rule; delete-after-candidate (§N.3); the per-domain map.
- `ENRICH_CORRECT`: `signal_ref`, the orphan/freshness detectors, the F06 mapping, coverage.
- `INTEGRATE`: `resolve_signal_ref()` shared resolver; the L4 packet.
- `QUALIFY_LIMIT`: CGM/CDLM weights labelled navigation; `primary_domain` labelled compat.
- **Migration**: one additive migration (columns `signal_ref jsonb`, `completeness_state`,
  `consumed_msr_build_ids text[]`, `stale_against_msr bool`; CHECK on the six F06 values); numbered
  ≥ 1082 (1080–1081 claimed by Gochara WP0-7); never a FK.
- **Fences**: `bodha_msr_signals` and `_idempotency.py` are L2's — the diff-based upsert stays a
  proposal to the L2 owner; `ph_nimitta.py` sealed — additive fields, its packet adopts; readers
  (Saṅgam/Kalasutra/Vighnakara/Jivana) unchanged until they adopt the resolver in their own
  packets; `cascade_check.sql` before any `rebuild_only` (the table is *not* in the cascade set,
  but its consumers are).
- **Cascade**: none owned; this table is deliberately outside migration 403's set — keep it so.
- **Rollback**: the new columns are nullable/defaulted; readers ignore them until adopted; the
  writer's old path is one flag away.

---

## §6 — Lenses A–J

| lens | answer |
|---|---|
| A | `ka_yojaka`, L3 rows; epistemic: compilation of L2 structure with L1-referenced lords; placement correct (Structural binding object); `ENRICH_CORRECT + INTEGRATE + QUALIFY_LIMIT` |
| B | seven declared edges all read [V: `bodha_msr_signals`, `bodha_cgm_nodes`, `bodha_cdlm_cells`, `ga_yoga_firings`, pratijñā, transit rules, ghaṭanā]; **no generation on any edge** — the defect; fan-out 4 + L4 + served |
| C | invariants: every `signal_ref` resolves at bind; identity hash reproducible from the consumed row; `inapplicable` ⇔ distribution reason; delete-then-insert byte-stable under an unchanged MSR (determinism gate G-3) |
| D | 79 orphans (stale); coverage counts owed; no new rows sought |
| E | six consumers; one reads a scalar of a map (L4); Jivana's `LIMIT 1` is Jivana's defect |
| F | `completeness_state` and `signal_ref` machine-readable; an orphan visible on every surface; navigation weights labelled |
| G | unmeasured; batch insert already; **justified no-change** until profiled |
| H | idempotent (§N.3); no resume needed (single-run); freshness detector added; `count_sql` chart-scoped |
| I | files in `may_touch`; one additive migration ≥ 1082; W2 |
| J | this brief; §7 results; review; the orphan fixture's output |

---

## §7 — Proof matrix

| proof | fixture | expected | invariant | detector fails when… |
|---|---|---|---|---|
| Positive | fixture MSR with one fired yoga + one distribution yoga + one catalog dosha | `applied` / `inapplicable` / `inapplicable`; `signal_ref` complete on all | lords reference L1 rows | any lord not in `ga_yoga_firings` |
| Negative | empty MSR | prior partition preserved **with** coverage | no delete | delete fires |
| Relevant influence (U01) | change `contrary_signal_ids` on one signal | only that predicate's hook changes | others byte-identical | a second row changes |
| Irrelevant control | reorder `domains_affected_array` | map keys identical; `primary_domain` **changes** (it is `domains[0]`) → this is the labelled compat scalar's known limit, asserted as such | map order-invariant | map differs |
| Duplication | same signal under two ayanāṃśas | two rows, two partitions | never merged | one row |
| Context/missingness | seed an orphan (delete one MSR row after bind) | `unavailable/signal_orphaned`; `stale_against_msr=true` | visible | silent bare id |
| Boundary | an L2 rebuild that preserves identity | `signal_ref` resolves; `stale=false` | stable | flagged stale |
| Delivery | sentinel `completeness_state='unavailable'` on one predicate | reaches `query_temporal_activation.ts` and Kalasutra's consumer test | survives | absent / dated anyway |
| Revision | L2 generation advances | `consumed_msr_build_ids` differs; rebuild replaces | no accretion | accretion |
| Value | frozen Q03 question | the route's structure identity is generation-bound; the baseline cannot say which L2 build it came from | — | no distinction |

Binding: **OFFERS** B2 (`completeness_state`, `epistemic_class`, `operator_role`, `tier_basis`),
B3 (the L2 identity for the layer — `signal_ref`), B5 (`coverage`). **DEMANDS** L2 generations
(W1) and `bodha_signal_identity` (present).

---

## §8 — Prioritization

(1) orphan detector + `signal_ref` (correctness/safety; SC-9) → (2) F06 mapping + coverage → (3)
ayanāṃśa-pinned read → (4) L4 packet (unlock: the map's value) → (5) labels. T0, W2; fan-out 4
(Saṅgam is the chokepoint — additive only); no P-candidate. Hold: `DATA_ACCEPTED` waits on an
accepted L2 generation (W1).

---

## §9 — Disposition and target state

`ENRICH_CORRECT` + `INTEGRATE` + `QUALIFY_LIMIT`. Data-plane: `PRODUCER_READY` after §7;
`DATA_ACCEPTED` on an accepted L2 vector; `CONSUMER_INTEGRATED` when Kalasutra/Saṅgam call the
resolver and L4's packet reads the map (records per D-H). Campaign: `ANALYZED` → `ENRICHED`.
Non-claims: `VALUE_EVALUATED` N; no claim that the map improves an L4 anchor (L4's packet tests
that); the 79 figure is a dated snapshot.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Orphan policy: fail-closed at build (refuse to publish a partition with any orphan), or flagged-not-dropped with a serve-time detector?** | **Flagged-not-dropped** — orphans arise *after* a correct build (L2 regenerates later), so fail-closed at build cannot catch them; the detector at consume time is the real guard, with the build-order rule (L2→L3) and `cascade_check.sql` as the process guard |
| 2 | No FK to `bodha_msr_signals` (a value reference + detector instead)? | **Yes, no FK** — a CASCADE FK makes this table a destruction surface (Lane F §3.4); a NO ACTION FK would block L2's own rebuilds |
| 3 | Pin the input read to the canonical ayanāṃśa or partition all five? | partition all five explicitly (the row already carries `ayanamsha_id`); never read all into one candidate |
| 4 | L4 packet: `ph_nimitta` adopts the per-domain map (U07)? | raise it; L4 is sealed — its packet decides; `primary_domain` stays as compat for one generation either way |

---

## §11 — Not verified here

1. The 79-row figure and the FK census — Lane F/census 2026-09-22 [A]; not re-queried.
2. `ph_nimitta.py:478-486` — Lane F's read [A]; L4 is `must_not_touch` and was not opened.
3. Whether any of the 79 orphans reached an L4 anchor or a served reading — unmeasured.
4. Build duration — unmeasured.
5. `services/ka_yojaka/{binder,classifier}.py` were not read line-by-line; the writer was.
