---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_YOJAKA_ELEVATION_BRIEF
version: "1.1"
status: DRAFT_FOR_INDEPENDENT_RE_REVIEW      # v1.0 → REWORK (REVIEW_KA_YOJAKA_v1_0.md: 2 BLOCKER, 5 MAJOR, 14 minor/note); v1.1 disposes each
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md
synergy_binding_version: "2.3"  # binding is UNADOPTED (PROPOSED_FOR_NATIVE_RULING_THEN_ADOPTION) and its §B8 item 9
# still lists the rename direction as open while §B1 asserts it. Authority for the field NAME is therefore the
# underlying rulings, not the binding: Kṣetra ruling 8 + Gochara G-9 + Saṅgam M-3 name `precision_regime`, native
# ruling D-S4 (2026-09-24) confirms it. Alias condition is Saṅgam D-7: `day_grade` reads as `date_grain` until every
# dependent claim has an authorized successor — NOT for a count of generations. Values {instant_grain, date_grain}.
asset_or_interface_ids: ["ka_yojaka", "L3-U01 (L2→Yojaka binding)", "L3-U07 interface to ph_nimitta (per-domain map)", "SC-9 (generation binding)", "SC-3 DEMAND: the shared resolver services/ka_qualification/identity.py — a W1 deliverable that DOES NOT EXIST on this base"]
goal_objective: "Make ka_yojaka's predicates carry an identified L2 generation rather than a bare signal_id, so that a regeneration is DETECTABLE where detection can actually happen — at read/check time, not at build, where the writer compiles its candidate from the live L2 rows in the same transaction and a dangling reference cannot exist; type each predicate's datability across all THREE reasons the writer emits; and deliver the per-domain structure it already persists to the consumer that reads one scalar of it."
source_revision: "9feac52d7 (l3/kala-layer-briefs); `git diff 9feac52d7 e82dd34a3` on ka_yojaka.py, services/ka_yojaka/, ph_nimitta.py and migration 670 is empty"
accepted_upstream_contract: "L2_STRUCTURAL_PROPOSITION_AND_RELATION_CONTRACT/1.0/blob-0cc75ffcf1e3a018265a3efde6cd8b666388f586; L2_PRODUCER_READY_ACCEPTANCE (e5307fadef); bodha_signal_identity — defined by migration 661 ALONE (661:53-59: deterministic over (chart, ayanamsha, signal_type, varga, configuration); 660 carries no identity content); bodha_msr_signals.build_id is UUID NOT NULL and part of the UNIQUE key (226:22,:111), so EVERY L2 rebuild issues a new one; L1 ga_yoga_firings.constituent_planets; the per-domain map landed in fa9857f00 (#2607) and 7697c43b3 NARROWED the compat scalar to first-domain"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_YOJAKA_v1_0.md (REWORK); re-verification of v1.1 pending"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/pipeline/orchestrator/writers/ka_yojaka.py", "platform/python-sidecar/services/ka_yojaka/{binder,classifier}.py", "platform/python-sidecar/tests/l3/test_ka_yojaka*.py", "one additive migration on kala_activation_predicates (signal_ref jsonb, consumed_msr_build_ids text[]; NO FK, NO stored orphan/staleness flag — see §4.3)", "a LOCAL fallback resolver under platform/python-sidecar/services/ka_yojaka/ IF the native declines the SC-3 DEMAND (§10.5)"]
interface_packet_targets_not_may_touch: ["platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts (the read-time resolver) — Pūrṇa-owned", "platform-mcp/src/tools/kala_views/{ahead,now}.ts — Pūrṇa-owned", "pipeline/orchestrator/writers/ph_nimitta.py:476-482 (L4, sealed) — an L4-owned packet; L3 owns only the sentinel tests"]
must_not_touch: ["bodha_msr_signals / bodha_writers/_idempotency.py (L2-owned; the diff-based upsert is an L2 proposal)", "ga_yoga_firings (L1)", "pipeline/orchestrator/writers/ph_nimitta.py (L4, sealed)", "ka_sangam.py, ka_kalasutra.py, ka_vighnakara.py, ka_jivana_parva.py (readers; their briefs)", "migration 403's CASCADE set — this brief adds NO foreign key", "services/ka_qualification/** (SC-3's W1 deliverable; a DEMAND, not this brief's to write)", "platform-mcp/src/tools/kala_views/**", "applied migrations — incl. 670, 1019, 1022, 1024 and 1033–1070", ".github/workflows/deploy.yml", "kala_gochara_windows WHERE generation='v1'", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY"
target_state_campaign: "ANALYZED → ENRICHED at stage 3; a superseded t2 freeze exists and is inadmissible under t3"
wave: "W2 (first row frontier)"
shape: single asset, rows keyed (chart_id, signal_id, ayanamsha_id) — the DB UNIQUE index (243:21-22); signature_class is NOT part of the key
evidence_base: >
  Source read directly on 9feac52d7 [V]; reviewer-verified claims adopted are marked [R]; migrations
  243/403/661/670/1019/1022/1024/226, Lane D §16, T1 Spine 2, Lane F, KALA_DATA_CENSUS §4a
  (79/50,678, 2026-09-22) [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.1 (2026-09-24): REWORK dispositions (21 findings) — F1 (BLOCKER) the build-time orphan detector is VACUOUS: the writer compiles its candidate from `SELECT … FROM bodha_msr_signals WHERE chart_id` inside the same transaction, so every emitted signal_id exists by construction, and delete-then-insert REMOVES orphans rather than marking them; a stored `stale_against_msr` would be false at write time forever (§N.8) — detection moves to read/check time and no stored flag is proposed; F2 (BLOCKER) `services/ka_qualification/identity.py` does not exist — it is SC-3's W1 deliverable, so the shared resolver becomes a DEMAND with a declared local fallback; F3 the writer emits THREE always_on_reasons (`distribution_yoga_sankhya` :975 was missed); F4 migration 670 was superseded for this asset by 1019 and 1022, whose own header says the canonical red was v4→v5 id staleness, NOT cross-chart contamination, and whose conjunct (a) is canonical-only; F5 the live hazard is inverted — every downstream INSERT target is FK-CASCADE-bound to the MSR, so an orphan cannot reach L4 or a served reading; the real risk is an FK-violation BUILD FAILURE in three writers; F6 staleness defined on build_id is always true after any rebuild (build_id is UUID NOT NULL in the UNIQUE key) — it must be defined on the identity hash; F7–F21 the may_touch/must_not_touch conflict, commit attribution, edge count, producer count, migration 661, Q-K02, B4 on scores, D3 being current behaviour, the migration number, estimated_seconds, the physical key, F06 companions, the FK claim upgraded to [V], the irrelevant control, and B3/B5 field shapes."
  - "1.0 (2026-09-24): first issue."
---

# `ka_yojaka` elevation brief — the bridge from structure to time, bound to a generation

## §0 — The recommendation, in one paragraph

`ka_yojaka` is the layer's compiler: every L2 MSR signal becomes a typed activation predicate, its
firing lords are resolved from **L1** rather than re-derived, and a signal that cannot honestly be
dated stays `UNDATED` with an inspectable `always_on_reason` — careful anti-fabrication design
(`ka_yojaka.py:12-27,:938-995`). What it does not do is **identify its input**: it reads every
`bodha_msr_signals` row for the chart with no generation and no ayanāṃśa filter (`:78-89`), stores
`signal_id` bare with **no foreign key** (`243_l3_ka_yojaka.sql:4-24` — verifiable at DDL, [V]), and
**79 of 50,678 rows point at signals that no longer exist** (census §4a [A]). The reviewer corrected
my account of what that costs and where it can be caught, and both corrections matter. **Where:** a
build-time anti-join **cannot fire** — the candidate is compiled from the live L2 rows in the same
transaction, so every emitted id exists by construction, and the writer's delete-then-insert
*removes* orphans rather than marking them; a stored `stale_against_msr` column would read `false`
forever, a status with no detector behind it (§N.8). Detection belongs at **read/check time**.
**What it costs:** every downstream INSERT target — `kala_activation`, `kala_convergence`,
`kala_obstruction` — carries an `ON DELETE CASCADE` FK to `bodha_msr_signals`
(`403_kala_signal_fk_cascade.sql:10-33` [R]), and `ph_nimitta` keys its lookup on ids drawn from
those same cascade-bound tables, so an orphaned predicate **cannot** reach L4 or a served reading;
the real live hazard is an **FK-violation build failure** in Kalasutra/Saṅgam/Vighnakara if any of
the 79 is datable. Also: the writer emits **three** `always_on_reason`s, not two
(`distribution_yoga_sankhya` at `:975` [R]); and migration 670's contract for this asset was
**superseded twice** (1019, 1022), with 1022's own header recording that the canonical red was that
chart's **v4→v5 identity staleness**, not cross-chart contamination, and its conjunct (a) scoped
canonical-only. Recommendation: **`ENRICH_CORRECT` + `INTEGRATE`** — a generation-bound
`signal_ref` carrying the **identity hash** (not the build id, which changes on every rebuild);
read-time resolution through SC-3's shared resolver (a **DEMAND** — the file does not exist) with a
declared local fallback; three F06 states, not two; the per-domain map delivered to L4 by packet.
One additive migration, no FK, **no stored flag**. Decisions: §10.

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 (REGISTER:147) | *"Typed activation predicates and fired-yoga participant lookup. … full mechanism compiler; preserve paired CDLM signals/roles and method key, not net domain average. DP05/06/08."* | unchanged |
| Strategy §6.1 **L3-A11** (`:281`) | *"Compile complete accepted L2 mechanisms, participants, signed multidomain relations, cancellation and all linked roots. Remove one-domain/five-link flattening with explicit migration; preserve distinct convention and mode context."* | the map is persisted; the scalar path and L4's read still flatten |
| Strategy **L3-U01** (`:441`) | *bind real producer fields, generations, signed routes…; hydration must use exact accepted snapshots*; test: *changing retention opposition affects that route; unrelated configurations stay stable* | binds §4, §7 |
| Strategy §3 (`:117`) | *"79 predicate signal IDs do not join to current same-chart MSR"* | census re-confirmed [A] |
| CURRENT_STATE §4.1 (`:131`) | *"first frontier; non-FK signal refs guarded"* | the guard does **not** exist in code — this is the delta |
| **Migration 243 (`:4-24`, index `:21-22`)** [R] | DDL: no `REFERENCES`; UNIQUE `(chart_id, signal_id, ayanamsha_id)` | the FK absence is **verifiable at source** — [V], not [A] (F19); the physical key has three columns, not four (F17) |
| **Migration 403 (`:10-33`)** [R] | five tables carry `ON DELETE CASCADE` to `bodha_msr_signals`; **`kala_activation_predicates` is deliberately NOT among them** | the reason an orphan cannot propagate — and the reason a datable orphan **fails a downstream INSERT** (F5) |
| **Migration 661 (`:53-59`)** [R] | `bodha_signal_identity(p_chart_id, p_ayanamsha_id, p_signal_type_id, p_varga_id, p_configuration)` — **660 carries no identity content** | cite 661 alone (F11) |
| **Migration 226 (`:22,:111`)** [R] | `bodha_msr_signals.build_id UUID NOT NULL`, part of the UNIQUE key | so **every** L2 rebuild issues a new `build_id` — staleness cannot be defined on it (F6) |
| **Migrations 1019 and 1022** [R] | 1019 scoped conjunct (c) to the canonical chart (`:83-89`); **1022** scoped (a) and (b) likewise (`:83-91,:96-105`) and its header (`:17-22`) records that the red was *the canonical chart's own* pre-determinism v4 ids vs v5 — *"NOT cross-chart contamination"*; after the 2026-09-10 rebuild (`1024:35-39`) the canonical red is the 79 | **1022 is the live contract**, and its (a) is **canonical-only**, so it detects nothing on any other chart (F4) |
| **`KALA_NATIVE_RULING_SHEET_v1_0.md` R4 (`:113-130`)** [R] | ruled: *"stable signal key + upstream generation … one migration in the L3 range (1071+), touching only L3-owned foreign keys"*; RESTRICT and SET NULL **rejected** | this brief's no-FK position is **consistent with R4**, not a new decision beyond it |
| Lane F §3.4 (`:361-400`) | value column / deferred FK / identity recompute / an L2 diff-based upsert | adopted as the value-column form |
| Blueprint v5.0 §3.5 row 5, §16.1 (`:885`), §16.2 (`:903`) | orphan detector; `domain_map_basis`; the L4 packet; `primary_domain` compat-only; **and `services/ka_qualification/identity.py` as an SC-3 / W1 deliverable** | that file **does not exist** on this base (F2) |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V]
`asset_registry_seed.ts:2354-2371`: `storage_type: 'postgres_table'`, `target_table:
'kala_activation_predicates'`, chart-scoped `count_sql`, `depends_on: ['bo_laksana',
'bg_transit_rules', 'ga_dashas', 'bo_bimba', 'bo_sangati', 'bo_pratijna', 'bg_ghatana']` — seven
edges (**not the widest; `ka_sangam` declares ten**, `:2312` — F9), `scope: 'per_chart'`.
Physical key: `(chart_id, signal_id, ayanamsha_id)` (`243:21-22`); one predicate row per signal
(`864:18-23`).

### 2.2 The code [V]/[R]
- `@register('ka_yojaka')` (`:61`); `dry_run` returns early (`:69-70`).
- **Input read** (`:78-89`): every current MSR row for the chart — **no `build_id`, no generation,
  no `ayanamsha_id` filter**. Empty → *"no bodha_msr_signals; prior predicate partition preserved"*
  (`:92-96`).
- **Firing lords** (`:269-281`, `_resolve_firing_lords` `:938-995`): YOGA → `ga_yoga_firings.
  constituent_planets` (`:606-613`); DOSHA → the fired dosha's graha facts; catalog-only doshas
  stay `UNDATED`.
- **Three `always_on_reason`s** [R], not two: **`distribution_yoga_sankhya` (`:975`, source
  `ka_yojaka:sankhya_fire_reason`)**, `distribution_yoga_all_grahas` (`:988`), and
  `no_resolvable_dasha_lord` (`:407-408`, the generalisation added after #2456 found 9,347 of 9,367
  undatable rows carrying no reason).
- **Structural enrichment** (`:316`, `:332-348`, `:841-903`): CGM pagerank (`:535-541`), CDLM
  strength (`:571-577`); the per-domain maps; `primary_domain = domains[0]` (`:886`);
  `multi_system_confirmation_aggregate_rule = 'primary_domain_v1'` (`:344`).
- **Write** (`:424-451`): `DELETE … WHERE chart_id` **after** the candidate exists (`:443-447`,
  §N.3); `INSERT … ON CONFLICT DO NOTHING` (`:431`); batches of 1000.
- **No orphan detection anywhere in the writer**, and **none is possible there**: the candidate's
  ids come from the live MSR in the same transaction (F1).

### 2.3 Consumers [V]/[R]
| consumer | reads | can an orphan reach it? |
|---|---|---|
| `writers/ka_sangam.py:278-311` | predicates (LEFT JOIN keeps orphans); `transit_trigger_jsonb` mutated in memory (`:1415-1435`) | **reads them** — and its INSERT target `kala_convergence` is FK-CASCADE-bound (`403:15-23`), so a datable orphan **raises an FK violation** |
| `writers/ka_kalasutra.py:45,:129-135,:235` | `constituent_lords`, `always_on_reason`; emits `kind:'always_on'` | same — `kala_activation` is FK-bound (`403:10-13`) |
| `writers/ka_vighnakara.py:435-436` | predicates for daśā-anchored rows | same — `kala_obstruction` is FK-bound |
| `writers/ka_jivana_parva.py:118-125` | LATERAL `LIMIT 1` per window, from `kala_convergence.signal_id` | **no** — the join key is cascade-bound |
| `writers/ph_nimitta.py:476-482` (L4, sealed) | `signal_id` + `(dasha_eligibility_rule_jsonb->>'multi_system_confirmation_count')::int` only; its lookup is keyed on ids from `kala_convergence`/`kala_bhavishya`/discoveries (`:143-147`) — all cascade-bound | **no** |
| served: `query_temporal_activation.ts:376-394` (fetches predicates only for `signal_id`s present in returned `kala_activation` rows); `kala_views/{ahead,now}.ts` (consume `activations`, never `.predicates`) | — | **no** |

**Live-path statement.** Three L3 writers read orphaned predicates; **no served reading and no L4
row can contain one**, because every path from a predicate to a consumer runs through a
cascade-bound table. The live hazard is therefore a **build failure**, not a silent bad answer.

### 2.4 Epistemic class
| field | class | authority | note |
|---|---|---|---|
| `signal_id` | identity reference | L2 (`bodha_signal_identity`, 661) | stored bare; no generation; no read-time detector |
| `constituent_lords` | `COMPUTED_FACT_CONFIGURATION` (references) | L1 | correct authority (§N.5) |
| `always_on_reason` | honest state | this writer | **three** reasons → three F06 states (§4.4) |
| `cgm_centrality_weight`, CDLM strengths, `dasha_activation_proximity_score` | `INTERPRETIVE_INFERENCE` — navigation, not proof (VA §6.3) | L2 / this writer | scores → **B4 binds** (`independence_group` + `comparable_with`), F13 |
| per-domain map | structural | L2 via this writer | persisted; consumed by nobody in full |
| `primary_domain` | compatibility scalar | this writer (`:886`) | `7697c43b3` **narrowed** the count to this first-domain value to match L4's own `domains_affected_array[1]` selection (F8) |

### 2.5 Ladders and cost
`PLAN_REVIEWED`; W2 frontier. t3: a t2 freeze, inadmissible. Cost: 50,678-signal fan-out, batch
write; **unmeasured** (no `KALA_COST_PROFILE_v1_0.md` on this base).

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | Regenerate any MSR producer (`bo_laksana` did, 2026-09-08/11): signals whose configuration changed get **new** ids; `kala_activation_predicates` keeps the old ones. 79 rows now reference nothing (census §4a). They are read by Saṅgam, Kalasutra and Vighnakara — and if any of them is **datable**, the downstream INSERT into a cascade-bound table raises an FK violation and the build fails; if none is, they sit inert and invisible. Nothing at build can see this (the candidate is compiled from the live MSR), and the only check that can — migration **1022**'s conjunct (a) — is scoped to the canonical chart |
| Evidence | `ka_yojaka.py:78-89` (unfiltered read), `:424-451` (bare `signal_id` INSERT, delete-after-candidate); `243:4-24` (no FK) [V]; `403:10-33` (five cascade tables, this one excluded) [R]; `1022:17-22,:83-105` [R]; 79/50,678 [A] |
| Expected contract | L3-U01 (*exact accepted snapshots*); Strategy §4 step 3 (*no implicit fall-through to mutable public rows*); F09; F22 (a freshness detector); DP06; **ruling R4** (a stable signal key + upstream generation, no FK) |
| Defect class | **unidentified generation** (no producer generation on the row) + **undetectable at the only place that is currently checked for non-canonical charts** + **wrong authority at the consumer** (L4 reads the scalar of a map that exists) |
| Impact | a mechanism that no longer exists can still be compiled, dated and converged on — or can fail a sibling writer's build outright; a *changed* mechanism keeps its old predicate until someone remembers to rebuild |
| Non-claim | **no claim that any of the 79 reached a served reading or an L4 anchor — the cascade makes that impossible**; no claim that any of the 79 is datable (that is what decides build-failure vs inert — unmeasured); the 79 is a 2026-09-22 snapshot |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q03 (the complete route), Q01 (which structure is engaged). Q-K02 is a Lane E
   portfolio question and is cited only as a coverage cross-check, not adopted (F12).
2. **Generation-bound reference (B3, SC-9) keyed on identity, not build id (F6).** Each row gains
   `signal_ref = {asset_id: <producer>, generation: <L2 generation>, id: <signal_id>,
   identity_hash: bodha_signal_identity(...)}` — the binding's `{asset_id, generation, id}` shape
   plus the hash (F-binding). The hash is recomputed from the **consumed** signal's own fields at
   bind time, so a rebuild that preserves identity resolves and one that changes it is detected.
   `consumed_msr_build_ids[]` is carried as a **receipt only** — never as the staleness key, because
   `build_id` is `NOT NULL` and part of the L2 UNIQUE key, so it changes on every rebuild and a
   build-id comparison would report staleness always. **No CASCADE FK** (R4 rejected RESTRICT and
   SET NULL; a FK would make this the sixth cascade surface).
3. **Detection at read/check time — and no stored flag (F1).** A build-time anti-join has no code
   path that can return a dangling row, and delete-then-insert removes orphans rather than marking
   them; a persisted `stale_against_msr`/`signal_orphaned` column would be `false` at write time
   forever — a status with no detector (§N.8). Detection therefore lives in two places that can
   fire:
   - **check time**: the registry `integrity_check_sql` (today migration **1022**'s conjunct (a),
     canonical-only) — this brief asks for a successor that is **chart-partitioned rather than
     canonical-pinned**, so the same drift is detected on every chart (§10.2);
   - **read time**: a resolver on the consume/serve path that compares `signal_ref.identity_hash`
     (and `generation`) against the current L2 head and reports
     `completeness_state='unavailable'`, `reason='signal_orphaned'` with the F06 companions
     `owner`, `evidence_ref`, `next_eligible_action` (F18).
   A *persisted* orphan state would require the writer to preserve rows absent from the current MSR
   — accretion, which §N.3 forbids and which contradicts this brief's own Revision proof — and is
   **not** proposed.
4. **Three honest states, not two (F3).** `distribution_yoga_sankhya` **and**
   `distribution_yoga_all_grahas` → `completeness_state='inapplicable'` (no single activating lord
   exists *by doctrine*); `no_resolvable_dasha_lord` → `'unavailable'` (L1 could not supply one — a
   gap, not a doctrine). All three keep `always_on_reason` verbatim, and the CHECK/test enumerates
   the three literals so a fourth appearing goes red. `operator_role='applicability'` on the
   eligibility rule, `'relevance_navigation'` on the weights (they must never gate — VA §6.3);
   `tier_basis='relative_uncalibrated'`, and — because the row carries scores — **B4 binds**:
   `independence_group` (the CGM/CDLM weights share one L2 root) and `comparable_with` are emitted
   (F13).
5. **The map reaches L4 (U01/U07 packet).** `ph_nimitta` reads `multi_system_confirmation_by_domain`,
   `cdlm_domain_strength_by_domain`, `pratijna_ids_by_domain` with `domain_map_basis=
   'primary_domain_v1'` beside; `primary_domain` and `multi_system_confirmation_count` stay as the
   labelled compatibility scalar for one generation. Note the accepted repair `7697c43b3`
   **institutionalised** that first-domain scalar to match L4's own `domains_affected_array[1]`
   selection (F8) — so the packet's job is to *add* the map, not to reinterpret the scalar.
6. **Ayanāṃśa context (F14).** Each row already carries the signal's `ayanamsha_id` (`:210,:414`)
   and the unique index partitions on it (`243:21-22`); the only ayanāṃśa-blind operations are the
   chart-scoped DELETE (`:445`) and the deliberately cross-ayanāṃśa
   `COUNT(DISTINCT bp.ayanamsha_id)` confirmation count (`:175`). "Partition all five" is therefore
   **current behaviour**, not a change; what is open is whether the DELETE should be
   ayanāṃśa-scoped (§10.4).
7. **Coverage (B5, the binding's shape).** `{requested_horizon: null, completed_horizon: null,
   resolution: 'signal_set', partitions_searched: [ayanāṃśas read], exclusions: [{reason ∈
   {undated_inapplicable, undated_unavailable}, count}], unsearched_regions: [],
   completion_detector: 'all_msr_rows_for_chart_compiled'}`, with `signals_read`,
   `predicates_compiled` and `consumed_msr_build_ids` as **asset-local** counters beside it — the
   v1.0 object reused the B5 name with a different shape (F-binding).
8. **Old vs new.** Positive: a fired yoga → `applied`, `signal_ref` complete. Negative: a
   catalog-only dosha → `inapplicable`, undated. Boundary: an L2 rebuild that **preserves** identity
   → `identity_hash` resolves (the build ids differ, and that is expected, not stale). Missing: an
   L2 rebuild that **drops** a signal → the read-time resolver reports `unavailable/signal_orphaned`;
   the row itself is unchanged until the next Yojaka build removes it. Duplicated: the same signal
   under two ayanāṃśas → two rows, never merged.
9. **Simpler baseline.** Today's bare `signal_id` rows.
10. **Ablation (U01's own test).** Change one signal's `contrary_signal_ids` in a fixture MSR:
    exactly that predicate's `strength_affliction_hook` changes; unrelated predicates are
    byte-identical. Then delete one MSR row **without** rebuilding Yojaka and read: the resolver
    reports the orphan; today nothing does, on any non-canonical chart.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: the L1-sourced firing-lord resolution; all three `always_on_reason`s; the
  empty-candidate-preserves-capital rule; delete-after-candidate (§N.3); the per-domain map.
- `ENRICH_CORRECT`: `signal_ref` with the identity hash; the three-state F06 mapping; coverage in
  the B5 shape; B4 fields on the scores.
- `INTEGRATE`: the read-time resolver (via SC-3, or the local fallback) and the L4 packet.
- `QUALIFY_LIMIT`: CGM/CDLM weights labelled navigation; `primary_domain` labelled compat.
- **DEMAND (F2):** the shared `resolve_signal_ref()` belongs in `services/ka_qualification/
  identity.py` per blueprint §16.1 — **that file does not exist on this base** and is an SC-3 / W1
  deliverable outside this brief's fence. If the native declines to gate on SC-3, the declared
  fallback is a local resolver under `services/ka_yojaka/` that SC-3 later absorbs (§10.5).
- **Migration**: one additive migration — `signal_ref jsonb`, `consumed_msr_build_ids text[]`, and
  a CHECK enumerating the three `always_on_reason` literals. **No FK. No stored orphan/staleness
  column** (F1). Number: the next free slot verified at execution time against `origin/main`
  (ruling R4 says the L3 range is 1071+). Pick the number by scanning **every `origin/*` head** across BOTH `platform/migrations/` and `platform/supabase/migrations/` — NOT `origin/main` alone, which maxes at 1070 while unmerged heads hold 1080–1090 (Gochara 1080–1086, Saṅgam 1088–1090); max across heads = 1090, 1087 is a single free slot. Re-scan at execution; do not trust this figure either — not asserted here (F15).
- **Fences**: `bodha_msr_signals` and `_idempotency.py` are L2's; `ph_nimitta.py` is sealed and
  changes only by its own packet; `kala_views/**` is Pūrṇa's — all three are in `must_not_touch`,
  and the interface targets are listed separately (F7).
- **Cascade**: none owned; this table is deliberately outside migration 403's set — keep it so.
- **Rollback**: the new columns are nullable; readers ignore them until adopted.

---

## §6 — Lenses A–J *(appendix)*

| lens | answer |
|---|---|
| A | `ka_yojaka`, L3 rows; compilation of L2 structure with L1-referenced lords; `ENRICH_CORRECT + INTEGRATE + QUALIFY_LIMIT` |
| B | seven declared edges, all read; **no generation on any** — the defect; fan-out: three L3 writers (which read orphans), one L4 and the served surfaces (which cannot) |
| C | invariants: `identity_hash` reproducible from the consumed row; `inapplicable` ⇔ one of the two distribution reasons; exactly three reason literals; delete-then-insert byte-stable under an unchanged MSR |
| D | 79 orphans [A]; whether any is datable — unmeasured, and it decides build-failure vs inert |
| E | six consumers; one reads a scalar of a map (L4); Jivana's `LIMIT 1` is Jivana's defect |
| F | `completeness_state` + `signal_ref` machine-readable; an orphan visible at read time on every surface |
| G | unmeasured; batch insert already; **justified no-change** |
| H | idempotent (§N.3); the freshness detector is read-time, not a stored flag |
| I | files in `may_touch`; one additive migration (number verified at execution); W2 |
| J | this brief; §7; the review; the orphan fixture's output |

---

## §7 — Proof matrix

Columns: **verdict tier** F24; **scope** `[U]` unit, `[I]` DB fixture, `[S]` served.

| proof | verdict tier | scope | fixture / command | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|---|
| Positive | COMPUTATIONAL_CORRECTNESS | I | fixture MSR: one fired yoga, one Nābhasa (saṅkhyā) yoga, one all-grahas distribution yoga, one catalog dosha | `applied` / `inapplicable` ×2 / `inapplicable`; `signal_ref` complete on all | lords reference L1 rows; **three** reason literals | a lord absent from `ga_yoga_firings`; a fourth reason literal | writer test |
| Negative | COMPUTATIONAL_CORRECTNESS | I | empty MSR | prior partition preserved **with** coverage | no delete | delete fires | writer test |
| Relevant influence (U01) | COMPUTATIONAL_CORRECTNESS | I | change `contrary_signal_ids` on one signal | only that predicate's hook changes | others byte-identical | a second row changes | writer test |
| Irrelevant control | COMPUTATIONAL_CORRECTNESS | I | reorder `domains_affected_array` on one signal | the map's **contents** are set-equal; `primary_domain`, `multi_system_confirmation_count` (`:918-922`) **and** `pratijna_ids` order (`:869-879`) all change — the labelled compat scalar's known limit, asserted as such | every order-dependent output enumerated | an order-dependent output is missed | writer test |
| Duplication | COMPUTATIONAL_CORRECTNESS | I | the same signal under two ayanāṃśas | two rows, two partitions | never merged | one row | writer test |
| Context/missingness | COMPUTATIONAL_CORRECTNESS | I+S | delete one MSR row **and do not rebuild Yojaka**; then read through the resolver | `unavailable/signal_orphaned` with the F06 companions | **read-time** detection | nothing reports it (today, off-canonical); or a stored flag is expected | route test |
| Boundary | COMPUTATIONAL_CORRECTNESS | I | an L2 rebuild that preserves identity (new `build_id`, same hash) | `identity_hash` resolves; **no staleness reported** | staleness keyed on the hash, not the build id | a build-id comparison flags it (the v1.0 defect) | writer test |
| Build-failure hazard | COMPUTATIONAL_CORRECTNESS | I | seed one **datable** orphan; run Kalasutra | today: an FK violation on `kala_activation`; after: the resolver marks it `unavailable` and Kalasutra skips it | orphans never reach a cascade-bound INSERT | the build still fails | writer test |
| Delivery | COMPUTATIONAL_CORRECTNESS | S | sentinel `reason='signal_orphaned'` | reaches `query_temporal_activation`'s envelope | survives | absent | route test |
| Revision | COMPUTATIONAL_CORRECTNESS | I | rebuild Yojaka after an L2 regeneration | orphaned rows **removed**, not marked | §N.3 replace | accretion | writer test |
| Value | EXPLANATORY_DISCRIMINATIVE_VALUE | S | frozen Q03 question with one orphan present | the answer names the unresolvable mechanism; the baseline cannot | — | no distinction | baseline record |
| Evaluation | — | — | `not_applicable` (predicates issue no claim) | — | — | — | — |

Binding: **OFFERS** B2 (`completeness_state` + F06 companions, `epistemic_class`, `operator_role`,
`tier_basis`), B3 (`signal_ref` in the `{asset_id, generation, id}` shape **plus** `identity_hash`),
B4 (`independence_group`, `comparable_with` — the row carries scores), B5 (`coverage` in the
seven-key shape, with the counters asset-local). **DEMANDS** L2 generations (W1),
`bodha_signal_identity` at read time, and **SC-3's `services/ka_qualification/identity.py`**, which
does not exist. **Asset-local:** `consumed_msr_build_ids`, `domain_map_basis`, `primary_domain`,
`signals_read`, `predicates_compiled`.

---

## §8 — Prioritization

(1) `signal_ref` with the identity hash (the binding) → (2) the three-state F06 mapping and the
CHECK → (3) the read-time resolver (SC-3 DEMAND or the local fallback) → (4) a chart-partitioned
successor to 1022's conjunct (a) → (5) coverage + B4 fields → (6) the L4 packet. W2 frontier.

---

## §9 — Disposition and target state

`ENRICH_CORRECT` + `INTEGRATE` + `QUALIFY_LIMIT`. Data-plane: `PRODUCER_READY`; `DATA_ACCEPTED`
only on an accepted L2 generation; `CONSUMER_INTEGRATED` when the readers use the resolver and L4's
packet reads the map. Campaign: `ANALYZED → ENRICHED`. Non-claims: no served reading or L4 row can
today contain an orphan; whether any of the 79 is datable is unmeasured; the resolver's home is a
DEMAND, not a deliverable of this brief.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **`signal_ref` keyed on the identity hash, with `consumed_msr_build_ids` as a receipt only — no FK (consistent with ruling R4)** | yes |
| 2 | **A successor to migration 1022 whose conjunct (a) is chart-partitioned rather than canonical-pinned**, so the drift is detected on every chart | yes — today it detects nothing off-canonical |
| 3 | **No stored orphan/staleness column** (a flag that is false at write time forever) | yes — detection at read and check time only |
| 4 | Should the writer's DELETE be ayanāṃśa-scoped as well as chart-scoped? | assess at stage 3; per-ayanāṃśa partitioning is already the row-level behaviour |
| 5 | **The resolver's home: gate on SC-3's `services/ka_qualification/identity.py` (W1), or write a local fallback this brief owns and SC-3 later absorbs?** | gate on SC-3 if W1 is near; otherwise the local fallback, declared as temporary |

---

## §11 — Not verified here

1. The 79 count, the 0.156 %, and whether any orphan is **datable** (which decides build-failure vs
   inert) — no DB.
2. Whether migrations 1019/1022/1024 are applied in production (files are merged; the ledger is DB).
3. Build duration — unmeasured.
4. `services/ka_yojaka/{binder,classifier}.py` — grep-level only, matching the declared scope.
5. Live `pg_constraint` — the FK absence is verified at DDL (`243:4-24`) and by the absence of any
   later FK migration, which is stronger than the prior [A].
6. No database query; no test run.

## §12 — Review dispositions (v1.0 → v1.1)

F1 accepted — the BLOCKER: detection moved to read/check time, the stored flag withdrawn, and the
accretion alternative named and rejected (§0, §2.2, §4.3, §7 Context/Revision); F2 accepted — the
resolver is a **DEMAND** with a declared fallback (§5, §10.5, `must_not_touch`); F3 accepted (§0,
§2.2, §4.4, §7 Positive — three reasons); F4 accepted (§1 new rows, §3 — 1022 is the live contract,
canonical-only, and its header's causal claim adopted); F5 accepted (§0, §2.3, §3, §7 Build-failure
row — the hazard inverted); F6 accepted (§1, §4.2, §7 Boundary — identity hash, not build id); F7
accepted (frontmatter split); F8 accepted (`accepted_upstream_contract`, §2.4, §4.5); F9 accepted
(§2.1); F10 accepted (the producer count is not restated); F11 accepted (661 alone); F12 accepted
(§4.1); F13 accepted (§2.4, §4.4 — B4 binds); F14 accepted (§4.6, §10.4 — D3 was current behaviour);
F15 accepted (§5 — the number is verified at execution); F16 accepted (`estimated_seconds` removed);
F17 accepted (`shape`, §2.1); F18 accepted (§4.3 — F06 companions); F19 accepted (§1, §11.5 — [V]);
F20 accepted (§7 irrelevant control — all order-dependent outputs); F21 noted; binding B3/B5 shapes
corrected (§4.2, §4.7, §7).
