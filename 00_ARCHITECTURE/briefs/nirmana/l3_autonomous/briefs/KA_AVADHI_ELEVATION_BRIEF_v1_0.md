---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_AVADHI_ELEVATION_BRIEF
version: "1.0"
status: DRAFT_FOR_INDEPENDENT_REVIEW      # → PROPOSED_FOR_NATIVE_RULING after the Fable 5.1 review
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md   # adopted by reference; B-rows + asset-local fields in §7
asset_or_interface_ids: ["ka_avadhi", "SC-10 (one daśā-system vocabulary: chara vs chara_karaka)", "SC-5 (caps of 10 → coverage)", "registry packet: migration 670 conjunct (b) + migration 859 volume formula re-pinned to the writer's vocabulary", "L2 dependency: bo_pratijna generation (SC-9 class)"]
goal_objective: "Make ka_avadhi's dossier say what it is: a per-period bundle of L1 fact references and L2 pratijñā references whose lord-condition refs actually resolve (the M4 fix rebuilt), whose pratijñā list is labelled the domain match it is (not a time-overlap activation), whose two caps of ten are disclosed as coverage, whose seventh daśā system is named the same way by the writer, the registry contract and the volume formula, and whose promised-but-absent fields (strength_factor) are either produced or removed from the DDL comment and docstring — so the registry integrity check can go green for a reason and the served timeline can stop being vimshottari-only in silence."
source_revision: "9feac52d7 (l3/kala-layer-briefs)"
accepted_upstream_contract: "L1_CONDITION_RELATION_CLOCK_CONTRACT/1.0 (chart_dashas at lahiri_chitrapaksha: system ids as L1 emits them — chara_karaka, naisargika, mudda, …; DATE bounds start_date/end_date; start_iso/end_iso instants available); L1 chart_facts graha_position vocabulary (subject codes SUN/…/RAH_MEAN; keys {sign, nakshatra, nakshatra_lord, sign_lord, house_d1, pada, longitude_sidereal, combustion_state, retrograde_flag}); L2 bodha_pratijna + brahma_event_ontology (no generation column read today)"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_AVADHI_v1_0.md"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/pipeline/orchestrator/writers/ka_avadhi.py", "platform/python-sidecar/tests/l3/test_m4_avadhi_lord_condition_refs.py, tests/l3/test_migration_859_avadhi_expected_volume.py (assertions that move)", "one NEW registry migration: re-pin asset_registry.integrity_check_sql conjunct (b) and expected_volume_inputs for ka_avadhi to the writer's system vocabulary (successor to 670/859 — never an edit of either)", "one additive DDL migration on kala_avadhi if the native takes §10.3 (coverage/generation columns; no FK)", "interface packet only: platform/src/lib/retrieval/registry/layers/L3_kala/query_dasha_dossier.ts, platform-mcp/src/tools/retrieval/kala_temporal.ts:277-314 (vimshottari-only timeline disclosed)"]
must_not_touch: ["chart_dashas / ga_writers (L1)", "bodha_pratijna, brahma_event_ontology (L2/L0)", "services/ka_dasha_kala/tree_walk.py (the ALL_DASHA_SYSTEMS constant is the clock authority's; this brief adopts it, never forks it)", "supabase/migrations/395_kala_avadhi.sql, platform/migrations/670_*, 859_* (applied; superseded by a new migration, never edited)", "platform-mcp/src/tools/kala_views/** (no reader of kala_avadhi there today)", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY (stage 3); DATA_ACCEPTED when a rebuild lands under the M4 fix and the re-pinned integrity contract returns TRUE for a reason (conjunct (c) green because refs resolve, conjunct (b) non-vacuous for the seventh system); CONSUMER_INTEGRATED when query_dasha_dossier serves the coverage fields and kala_temporal discloses its system filter"
target_state_campaign: "ANALYZED (this brief) → ENRICHED at stage 3; registry state `error` today (integrity check red by design, 670 header)"
wave: "W2 (foundation; independent preparation)"
shape: single asset, rows (chart × system × level × period_start)
evidence_base: >
  Source read directly on 9feac52d7 [V]; migration 670 header + ka_avadhi contract, migration 859,
  migration 395 [V]; blueprint v5.0 §3.5 row 6 / §4 / §16.2, Lane D, T1 [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.0 (2026-09-24): first issue; awaiting independent review."
---

# `ka_avadhi` elevation brief — the period dossier, told honestly

## §0 — The recommendation, in one paragraph

`ka_avadhi` writes one dossier row per MD/AD period of seven daśā systems at the canonical
ayanāṃśa (`ka_avadhi.py:72-96,195-199` [V]) — 1,169 rows live for the canonical chart
(migration 859 [A]) — carrying three things: `lord_condition_fact_refs` (L1 `chart_facts` ids,
never values — the B.3 discipline done right), `activated_pratijna_ids`, and a `sublord_modulation`
note. Its registry state is **`error`** because the migration-670 integrity contract is red by
design until a rebuild lands the W3 M4 fix (`fact_subject='Sun'` vs L1 `'SUN'` — refs `[]` on
100.00% of rows; the fix is on this base via `norm_graha`, `:257` [V]; 670 header `:25-26`,
conjunct (c) `:86-97` [V]). Four further things are wrong and none is in the 670 contract:
(1) the **seventh system has three names** — `chara` in migration 395's DDL comment (`:27`), in
670's conjunct (b) (`:75-76`) and in 859's six-system volume formula (`:21-22,:60-65`), versus
`chara_karaka` in the writer (`ALL_DASHA_SYSTEMS`, `tree_walk.py:40-43` [V]) and in L1 — so
conjunct (b) is **vacuous** for that system (no `'chara'` row can ever exist to be missing), 859
records the gap as *Held*, and a rebuild under today's writer — which **refuses** unless all seven
of *its* ids are present at MD and AD (`:200-215` [V]) — would write seven systems against a
formula that expects six; (2) the docstring says pratijñā ids are activated when *"the period
overlaps within the dossier window"* (`:13-14`) but the code activates every pratijñā whose
ontology domain matches the lord's hardcoded natural domains, no time test at all (`:280-290`
[V]) — a **domain match wearing an activation's name**, and 3,087 of those ids do not resolve
(670 `:26`, conjunct (e)); (3) `strength_factor` is promised by the docstring (`:15`) and the DDL
comment (395 `:37`) and **never emitted** (`:291-294` [V]); (4) two silent caps of ten (`LIMIT 10`
refs `:143`; `[:10]` pratijñā `:290`) and a generic literal citation on every row including
Yoginī/Kālacakra periods (`:306-308`). Recommendation: **`ENRICH_CORRECT` + `QUALIFY_LIMIT`** —
rebuild under M4; one vocabulary (adopt the writer's/L1's `chara_karaka`; re-pin 670(b) and 859 by
a successor migration); rename-and-label the pratijñā list (`operator_role='relevance_navigation'`,
domain match, with an honest orphan count); caps → B5 coverage; `strength_factor` produced or
struck; citations per system or `unsourced`; the L2 generation referenced (SC-9). No new table.
Decisions: the vocabulary, the pratijñā semantics, the DDL (§10).

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 (REGISTER row for ka_avadhi) | period dossier; refs only; DP05/07 | — |
| Strategy §3 *Clock interval* (`:91`) | *"Dasha/Avadhi/annual/return adapters; overlap and interval joins replace exact date-pair equality"*; applicability/prerequisites, failure/absence reason, exact vs approximated | the dossier carries no applicability, no failure reason, and DATE bounds only |
| Strategy §6.2 (`:336,:346`) | *"legacy L0–L2 source-table reads → overlays / Avadhi / Yojaka"*; *"registry still declares Avadhi→Taranga"* (Taranga does not consume Avadhi, `:47`) | confirmed: no Kāla writer reads `kala_avadhi` [V grep]; Taranga's declared edge is documentation-only |
| Strategy §6.4 W2 (`:374`) | Avadhi in W2 — *"per-asset semantic/data/service acceptance; purpose/method/convention scope explicit"* | this brief |
| Migration 670 header (`:25-26`) + contract (`:44-122`) | (a) spine = `chart_dashas` at canonical ayanāṃśa exactly; (b) coverage of `{vimshottari, yogini, ashtottari, chara, naisargika, mudda, kalachakra}` MD/AD; (c) every graha-lord period carries ≥1 ref — **RED today by design**; (d) refs resolve and name their own lord; (e) pratijñā ids resolve — **3,087 unresolvable** | (c) will go green on rebuild; (b) is vacuous for `chara`; (e) is a real L2-generation defect (§3) |
| Migration 859 (`:15-24,:60-77`) | expected volume = 6 systems = 1,169 (`vimshottari 117, yogini 308, ashtottari 104, naisargika 70, mudda 480, kalachakra 90`); *"chara has zero exact matches; chart_dashas carries chara_karaka … Held item"* | the writer's own list is `chara_karaka`, so a rebuild writes 7 systems — the Held item is on this asset's critical path |
| Migration 395 (`:9-23,:27,:34-37`) | DDL: natural key `UNIQUE(chart_id, system_id, level_n, period_start)`; `period_start/end DATE`; `level_n ∈ {1,2,3}`; comment promises `sublord_modulation: {graha, strength_factor, modulation_note}` | `strength_factor` never emitted; `modulation_note` is emitted as `note`; level 3 never written |
| Seed (`asset_registry_seed.ts:2335-2353`) | `depends_on: ['ga_dashas', 'bo_pratijna', 'bg_ghatana']` (migration 406 dropped the phantom `ka_yojaka` edge); `count_sql` chart-scoped; `target_floor: 0` (859 → 1169 live) | `bg_ghatana` is **declared and not read** (grep `ghatana` → docstring only); `brahma_event_ontology` is **read and not declared** (`:105`); `ka_dasha_kala` constant imported, undeclared (`:29`) |
| Blueprint v5.0 §3.5 row 6 (`:322`), §4 (`:394`), §16.2 (`:904`), SC-5 (`:284`) | live; registry `error`; caps of 10; "diagnose the failing check; declare the `ka_dasha_kala` edge or drop the import" | diagnosed here (§3); the import is a vocabulary adoption — keep and declare as `vocabulary` (F12 role), not a data edge |
| Lane D / T1 | consumer `query_dasha_dossier.ts` via `kala_temporal.ts` | confirmed [V]; and `kala_temporal.ts` fetches **vimshottari only** (`:278,:309,:314`) |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Identity and registration [V]
`storage_type: 'postgres_table'`, `target_table: 'kala_avadhi'`, `count_sql` chart-scoped,
`scope: 'per_chart'`, `sort_order: 4`, `catalog_status: 'CURRENT'`. Live registry state `error`
(blueprint §4 [A]). `FORMULA_VERSION = "ka_avadhi_v1.0"` (`:36`).

### 2.2 The code [V]
- **Reads**: `_FETCH_MD_SQL` (`:74-84`) level 1, `_FETCH_AD_SQL` (`:86-96`) level 2 with parent
  join, both `ayanamsha_id = 'lahiri_chitrapaksha'` (`_CANONICAL_AYANAMSHA`, `:72`) and `system_id
  = ANY(_DASHA_SYSTEMS)` where `_DASHA_SYSTEMS = tuple(sorted(ALL_DASHA_SYSTEMS))` (`:34`) =
  `{vimshottari, yogini, ashtottari, chara_karaka, naisargika, mudda, kalachakra}`; **DATE
  columns** `start_date/end_date` (not `start_iso/end_iso`). `_FETCH_PRATIJNA_SQL` (`:101-108`):
  every `bodha_pratijna` row for the chart at lahiri joined to `brahma_event_ontology` for
  `domain`, **no generation, no status gate** (SHABDA-SHUDDHI R6, `:97-100`), savepoint-guarded
  soft dependency (`:226-247`). `_FETCH_FACT_REFS_SQL` (`:133-143`): `fact_category=
  'graha_position'`, eight real keys, `fact_subject = norm_graha(lord)` (`:257`), total `ORDER BY`,
  **`LIMIT 10`**; savepoint per graha (`:250-273`).
- **Refusal**: if any of the seven ids is missing at MD or AD → `rows_inserted=0`, *"incomplete
  dasha-system coverage … prior partition preserved"* (`:200-215`) — an honest refusal, keyed to
  the writer's vocabulary.
- **Build** (`_build_row`, `:276-309`): `domains = _GRAHA_DOMAINS.get(lord, [])` (`:40-50`,
  Title-case keys — so a Yoginī or Kālacakra lord that is not one of nine grahas gets `[]`);
  `activated_ids` = every pratijñā in any of those domains, **no period-overlap test**, capped
  `[:10]` (`:280-290`); `sublord_modulation = {graha, note}` (`:291-294`) — no `strength_factor`;
  `quality = {domains}`; `citations = ["BPHS ch. Vimshottari-Dasha / Classical dasha lord
  tables"]` on every row (`:306-308`).
- **Write**: `DELETE … WHERE chart_id` then `executemany(_INSERT_SQL)` with `ON CONFLICT DO
  UPDATE` (`:325-327`; `:145-166`) — §N.3 delete-then-insert, conformant; never commits.
- No `date.today()`; whole-lifetime spine (no horizon anchor) — correct for a dossier.

### 2.3 Consumers (grep `kala_avadhi`, tests/seed/generated excluded) [V]
| consumer | reads | role |
|---|---|---|
| `platform/src/lib/retrieval/registry/layers/L3_kala/query_dasha_dossier.ts` | rows by system/level/lord/date; `LIMIT 50` with `total_matching` + `more_available` (`:93-113`) — **disclosed** cap, good pattern | served `computation` |
| `platform-mcp/src/tools/retrieval/kala_temporal.ts:277-314` | `query_dasha_dossier` with `system_id: 'vimshottari'` only (`:278`), `level_n 1/2 active_on today` (`:309,:314`) | served `relevance_navigation` — **six systems silently absent from the "timeline"** |
| `source_query_availability.ts:3054-3064` | availability count | census |
| Kāla writers, L4, `kala_views/**` | **none** | — |
| Taranga (declared edge, Strategy `:47`) | does not read | documentation-only |

**Live-path statement.** The dossier is live on two served surfaces. The refs array is `[]` on
every live row (M4 unrebuilt); the pratijñā list is live with 3,087 dangling ids; the sublord
note is live; the vimshottari-only filter is live.

### 2.4 Epistemic class
| field | class | authority | note |
|---|---|---|---|
| `period_start/end`, `lord_graha`, `system_id`, `level_n` | `COMPUTED_FACT_CONFIGURATION` (inherited) | L1 `chart_dashas` | referenced, not restated — 670(a) enforces; DATE grain (L1 has instants) |
| `lord_condition_fact_refs` | reference bundle to L1 facts | L1 `chart_facts` | `[]` live; ≤ 10 by `ORDER BY fact_key, fact_id` — the cap can drop `sign` for `combustion_state` alphabetically |
| `activated_pratijna_ids` | **domain match** (navigation), not activation | L2 `bodha_pratijna` × hardcoded `_GRAHA_DOMAINS` | no time test; no generation; 3,087 orphans; ≤ 10 |
| `_GRAHA_DOMAINS` | classical natural-signification map, **unsourced** | this writer | `source_qualification='unsourced'` until cited |
| `sublord_modulation.note` | narration (deterministic template) | this writer | `strength_factor` promised, absent — an honest null is better than a promise |
| `quality.domains` | the same map echoed | this writer | not a quality |
| `citations` | literal | this writer | wrong for six of seven systems |

### 2.5 Ladders and cost
`PLAN_REVIEWED`; W2 source accepted. t3: no event (registry `error`). Cost: bounded reads;
1,169 rows; cheap; unmeasured.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | Rebuild `ka_avadhi` for the canonical chart on this base: the writer requires `chara_karaka` MD+AD rows (`:200-215`) and, if L1 has them (859 `:22` says it does), writes **seven** systems — while the registry's expected volume (859) is six systems = 1,169 and its integrity contract's coverage conjunct (670(b)) checks for a system id `'chara'` that L1 never emits, so (b) is satisfied vacuously whether or not `chara_karaka` is covered. Conjunct (c) turns green (refs resolve under M4) but (e) stays red: 3,087 `activated_pratijna_ids` point at no `bodha_pratijna` row, because the list is compiled from the current L2 rows by domain with no generation and no FK, and L2 regenerated. And every one of those ids is labelled *activated* while nothing tested whether the pratijñā's window overlaps the period |
| Evidence | `ka_avadhi.py:34,72-96,200-215,257,280-294,306-308`; `tree_walk.py:40-43`; migration 670 `:25-26,:71-85,:86-97,:110-119`; migration 859 `:21-22,:60-77`; migration 395 `:27,:37` — all [V] |
| Expected contract | Strategy §3 *Clock interval* (applicability, failure reason, exact vs approximated); DP01 (no rival definitions — one system vocabulary); §N.5 (references resolve); §N.7 items 1, 3, 6 (narration restates cited facts; no wrapper-local constant shadows an L1 value; honest null beats a promise); §N.8 (a green check must measure the claim — (b) cannot); SC-5 (caps disclosed); SC-9/SC-10 |
| Defect class | **rival vocabulary** (three names, one system) + **vacuous detector** (670(b)) + **mislabelled** (domain match called activation) + **unbound reference** (no L2 generation; 3,087 orphans) + **promised field absent** (`strength_factor`) + **undisclosed caps** + **unsourced literal citation** |
| Impact | The registry cannot go green for the right reason; Q01/Q06's *"how will my Ketu daśā be"* (395 `:3`) is answered with an empty refs array and a list of pratijñā ids a tenth of which are dead; a consumer paging the timeline sees one system and does not know it |
| Non-claim | Whether L1 has `chara_karaka` MD+AD rows for the canonical chart is inferred from 859's text, not queried; the 3,087 figure is 670's measurement (2026-09-2x) [A]; no claim that the domain map is classically wrong — only that it is uncited |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q01 (which clocks are engaged — the dossier's spine), Q06 (what a period
   carries); Q-K01. Not Q02/Q05 (no comparison, no agreement — those are the clock service's).
2. **One vocabulary (SC-10).** The writer already adopts the clock authority's
   `ALL_DASHA_SYSTEMS`; the registry follows it: a **successor migration** re-pins 670's conjunct
   (b) array and 859's `expected_volume_inputs` to `chara_karaka` (and records the seventh
   system's count once measured). 395's DDL comment is corrected in the same migration
   (`COMMENT ON` is not data). The `ka_dasha_kala` import is declared as a `vocabulary` edge
   (F12), not a data dependency.
3. **Rebuild under M4** — the precondition for everything else; conjunct (c) goes green because
   refs resolve, not because the check was loosened.
4. **Pratijñā list renamed and labelled.** `activated_pratijna_ids` → carried one generation as
   is, plus `pratijna_refs = [{pratijna_id, generation, domain, match_basis:'lord_natural_domain'}]`
   with `operator_role='relevance_navigation'`, `epistemic_class='INTERPRETIVE_INFERENCE'` (the
   domain map is an inference), `source_qualification='unsourced'` until `_GRAHA_DOMAINS` cites.
   **No time-overlap test is added** unless the native rules the field should become an
   activation (§10.2) — then it needs the pratijñā's own window (L2 offers none today) and is a
   DEMAND, not a fabrication.
5. **Generation-bound references (SC-9).** `pratijna_refs[].generation` from `bodha_pratijna`'s
   generation column **if one exists** (not read today; §11) — else the L2 build id; the orphan
   detector: build-time anti-join, dangling ids written under `completeness_state='unavailable'`
   with `reason='pratijna_orphaned'`, counted in coverage — never silently dropped, never carried
   as live.
6. **Coverage (B5) per row and per build.** Row: `coverage = {requested_horizon: null,
   completed_horizon: null, resolution: 'period', partitions_searched: ['graha_position',
   'bodha_pratijna'], exclusions: [{kind:'fact_ref', reason:'cap_10', dropped: n}, {kind:
   'pratijna', reason:'cap_10'|'orphaned', dropped: n}], unsearched_regions: [], completion_
   detector: 'all_candidates_classified'}`. The caps stay (Q8 ruling) but are **disclosed**; the
   fact-ref cap's `ORDER BY fact_key` is replaced by a declared priority (`sign, house_d1,
   nakshatra, sign_lord, nakshatra_lord, combustion_state, retrograde_flag, longitude_sidereal`)
   so a cap never drops `sign` for an alphabetically earlier key.
7. **`strength_factor`: produce or strike (§10.3).** Recommended: **strike** from docstring and
   DDL comment; `sublord_modulation = {graha, note}` stays — an honest null beats an invented
   factor (§N.7 item 6).
8. **Citations per system.** `citations` becomes a per-`system_id` map from L0
   `l0_dasha_systems.py`'s source field (referenced, not restated) or `['unsourced']`.
9. **Instants (B1).** `period_start/end` stay DATE (the natural key); the dossier gains
   `t_start/t_end` from L1 `start_iso/end_iso` as `timestamptz`, `inclusivity='closed_open'`,
   `time_basis='event_instant'`, `claim_grain='instant_grain'` — additive JSONB or columns (§10.3).
10. **Interface packets.** `query_dasha_dossier.ts`: serve `coverage` and `pratijna_refs` (additive).
    `kala_temporal.ts`: the timeline's `system_id: 'vimshottari'` filter is **disclosed** in the
    envelope (`systems_included: ['vimshottari']`, `systems_available: 7`) — Pūrṇa-owned TS,
    L3-owned sentinel.
11. **Old vs new.** Positive: rebuild → refs resolve (670(c) green), seven systems, coverage
    present. Negative: L1 missing one system at AD → refusal unchanged, and now the note names
    which. Boundary: a lord whose refs exceed 10 → `exclusions.cap_10.dropped > 0`. Missing: a
    Yoginī lord (not a graha) → `pratijna_refs=[]` with `reason='lord_not_a_graha'` (today: silent
    `[]`). Duplicated: n/a (natural key unique).
12. **Simpler baseline.** The current writer after a rebuild (M4 only).
13. **Ablation.** Regenerate L2 (`bodha_pratijna`) with different ids: today the dossier carries
    dangling ids silently; after, the orphan count appears in coverage and the ids are marked
    `unavailable` — the added distinction is that count.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: refs-not-values (B.3); the canonical-ayanāṃśa scoping (CR-110); the savepoint-guarded
  soft dependencies; the all-systems refusal; delete-then-insert; the `norm_graha` normalisation.
- `ENRICH_CORRECT`: vocabulary re-pin; `pratijna_refs` + generation + orphan detector; coverage;
  ref-cap priority; per-system citations; instants.
- `QUALIFY_LIMIT`: `_GRAHA_DOMAINS` `unsourced`; `note` as narration; caps disclosed.
- **Struck**: `strength_factor` (docstring + DDL comment).
- **Migrations**: one registry successor migration (670(b)/859 re-pin + 395 comment); optionally
  one additive DDL (§10.3). No FK (the cascade lesson, G20).
- **Registry edges**: `bg_ghatana` declared-unread → drop by registry packet (own owner);
  `brahma_event_ontology` read-undeclared → declare; `ka_dasha_kala` → `vocabulary`.
- **Tests that move**: `test_migration_859_avadhi_expected_volume.py` (six-system formula);
  `test_m4_avadhi_lord_condition_refs.py` (key list if the priority order lands).
- Rollback: the writer's payload is additive; the registry migration is reversible by a further
  successor.

---

## §6 — Lenses A–J

| lens | answer |
|---|---|
| A | `ka_avadhi`, L3 rows; epistemic: L1/L2 reference bundle + one uncited inference map + template narration; placement correct (Clock-interval dossier); `ENRICH_CORRECT + QUALIFY_LIMIT` |
| B | real reads: `chart_dashas`, `chart_facts`, `bodha_pratijna`, `brahma_event_ontology`; declared `bg_ghatana` unread; `ka_dasha_kala` vocabulary; fan-out: two served surfaces; T1 |
| C | invariants: spine = L1 (670(a)); every ref resolves and names its lord (670(d)); every pratijñā id resolves or is marked orphaned; seven systems under one name; `strength_factor` absent everywhere. Golden: 670 contract green after rebuild; boundary: >10 refs |
| D | the seventh system's L1 rows (inferred present); pratijñā windows (L2 offers none) |
| E | `query_dasha_dossier` (disclosed cap — good), `kala_temporal` (undisclosed system filter) |
| F | coverage + `pratijna_refs` + `systems_included` machine-readable |
| G | negligible; justified no-change |
| H | idempotent; savepoints; no credentials |
| I | files in `may_touch`; W2; one registry migration; registry-edge packet separate |
| J | this brief; §7; review; the 670 contract's TRUE after rebuild |

---

## §7 — Proof matrix (tier `[U]` unit/DB-free, `[I]` integration/DB fixture, `[S]` served)

| proof | tier | fixture / command | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|
| Positive | I | rebuild on a DB fixture with all seven L1 systems; `SELECT integrity_check_sql` | 670 (re-pinned) returns TRUE; refs non-empty on every graha-lord row | (a)–(e) | any conjunct FALSE | integrity SQL output |
| Negative | I | L1 fixture missing `chara_karaka` AD | refusal note names `AD=chara_karaka`; 0 rows; prior partition kept | honest refusal | rows written | writer test |
| Relevant influence | I | regenerate `bodha_pratijna` ids in the fixture | `exclusions.orphaned.dropped` = the count; ids marked `unavailable` | detected | silent dangling ids (today) | writer test |
| Irrelevant control | U | reorder `_GRAHA_DOMAINS` dict | identical rows | order-invariant | differs | unit test |
| Duplication | I | two L1 rows for one period at two ayanāṃśas | one dossier row (canonical only) | CR-110 | two rows | writer test |
| Context | U | a Yoginī lord (`'Sankata'`) | `pratijna_refs=[]`, `reason='lord_not_a_graha'`; refs `[]` with reason | declared missingness | silent `[]` | unit test |
| Boundary | U | 11 candidate refs for one lord | 10 kept by declared priority incl. `sign`; `cap_10.dropped=1` | priority + disclosure | `sign` dropped / no count | unit test |
| Delivery | S | sentinel `exclusions.orphaned.dropped=3` on one row | reaches `query_dasha_dossier` envelope | survives | absent | route test |
| Delivery (timeline) | S | `kala_temporal` bundle | `systems_included: ['vimshottari']` present | disclosed | absent | MCP test |
| Revision | I | L1 `chart_dashas` regenerated | rows replaced (delete-then-insert) | fresh | accretion | writer test |
| Value | S | frozen Q06 question ("how will my Ketu daśā be") | refs resolve to sign/house/nakṣatra facts; the baseline returns `[]` | — | no refs | baseline |
| Evaluation | — | `not_applicable` (a dossier issues no claim) | — | — | — | — |

Binding: **OFFERS** B1 (`t_start/t_end`, `inclusivity`, `time_basis`, `claim_grain`), B2
(`completeness_state`, `epistemic_class`, `operator_role`, `source_qualification`), B5 (`coverage`).
**DEMANDS** L2 `bodha_pratijna` generation identity (SC-9) and, if §10.2 rules activation, the
pratijñā's own window. B3: `window_ref = {asset_id:'ka_avadhi', generation: FORMULA_VERSION +
build, id: avadhi_id}` offered. B4: n/a (no testimony). **Asset-local:** `pratijna_refs`,
`match_basis`, `sublord_modulation`, `quality.domains`, `citations`, `systems_included`.

---

## §8 — Prioritization

(1) rebuild under M4 (the registry goes from `error` toward green for a reason) → (2) vocabulary
re-pin (the check becomes non-vacuous; 859 stops disagreeing with the writer) → (3) orphan
detector + generation (3,087 dead ids stop masquerading) → (4) label the pratijñā list → (5) caps
→ coverage; strike `strength_factor`; citations → (6) instants → (7) the timeline disclosure.
T1; W2; no P-candidate.

---

## §9 — Disposition and target state

`ENRICH_CORRECT` + `QUALIFY_LIMIT`. Data-plane: `PRODUCER_READY` after §7 `[U]`/`[I]`;
`DATA_ACCEPTED` when the rebuilt rows pass the re-pinned 670 contract on production;
`CONSUMER_INTEGRATED` when both served packets carry the sentinels. Campaign: `ANALYZED →
ENRICHED`. Non-claims: no `VALUE_EVALUATED`; the domain map remains uncited until sourced; the
seventh system's live row count is unknown until rebuilt.

**Walkthrough (ordinary period).** "What does my current antardaśā carry?" → one row: Jupiter AD
under Saturn MD, `t_start/t_end` instants, seven resolved refs (sign, house, nakṣatra, lords,
combustion, retrograde, longitude — all L1 ids), `pratijna_refs` of four domain-matched pratijñā
with generation, `exclusions=[]`, `sublord_modulation.note`. Nothing invented; the caps unhit.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Vocabulary: adopt `chara_karaka` (writer + L1) and re-pin 670(b)/859/395-comment by successor migration; or rename in L1?** | adopt `chara_karaka` — L1 is the authority (§N.5); one migration |
| 2 | **Pratijñā list: keep as a labelled domain match (`relevance_navigation`), or make it a true time-overlap activation (DEMAND on L2 for pratijñā windows)?** | keep as labelled navigation now; raise the DEMAND; do not fabricate overlap |
| 3 | `strength_factor`: strike (docstring + DDL comment) or specify and produce? Instants as JSONB fields or new columns? | strike; instants as JSONB in `dossier` (no DDL) |
| 4 | Registry edges: drop `bg_ghatana`, declare `brahma_event_ontology`, `ka_dasha_kala` as `vocabulary` | yes, by registry packet |

---

## §11 — Not verified here

1. Whether `chart_dashas` holds `chara_karaka` MD **and** AD rows for the canonical chart (859's
   text says the id exists; the writer's refusal depends on both levels) — no DB.
2. Whether `bodha_pratijna` carries a generation column — not read; if absent, the L2 build id.
3. The 3,087 orphan count and the 100.00% empty-refs figure — 670's measurements [A].
4. Live registry state `error` — blueprint [A].
5. Whether `l0_dasha_systems.py` carries a citation field usable for per-system `citations`.
6. No database query; no test run.
