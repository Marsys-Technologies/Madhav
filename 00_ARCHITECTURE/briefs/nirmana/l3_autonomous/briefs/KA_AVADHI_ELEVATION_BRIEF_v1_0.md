---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_AVADHI_ELEVATION_BRIEF
version: "1.1"
status: DRAFT_FOR_INDEPENDENT_RE_REVIEW      # v1.0 → REWORK (REVIEW_KA_AVADHI_v1_0.md: 1 BLOCKER, 8 MAJOR, 16 minor/note); v1.1 disposes each
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md
asset_or_interface_ids: ["ka_avadhi", "DP01 (one daśā-system vocabulary across L1 / writer / registry)", "SC-9 (L2 generation binding for the pratijñā references)", "SC-5 (the two caps, which cannot bind today)", "registry packet: a successor to migration 1023 re-pinning conjunct (b) + a successor to 859's volume inputs", "ontology DEMAND: _GRAHA_DOMAINS vs brahma_event_ontology.domain's CHECK vocabulary"]
goal_objective: "Make ka_avadhi's dossier say what it is: a per-period bundle of L1 fact references and L2 pratijñā references whose lord-condition refs resolve, whose pratijñā list is labelled the domain match it is AND speaks the ontology's own domain vocabulary (today 21 of its 36 strings cannot match, and Rāhu can never match at all), whose orphan detection lives where it can actually fire, whose seventh daśā system is named the same way by the writer, the registry contract and the volume formula, and whose promised-but-absent field is struck."
source_revision: "9feac52d7 (l3/kala-layer-briefs); cited code identical at 3387c9ac3 (2026-09-24)"
accepted_upstream_contract: "L1_CONDITION_RELATION_CLOCK_CONTRACT (chart_dashas at lahiri_chitrapaksha; system ids as L1 emits them — ga_dashas_writer.py:2026,2055,2084,2112 insert 'chara_karaka' at four levels; DATE bounds start_date/end_date; start_iso/end_iso and sandhi_flag available, 206_ga3_supporting_tables.sql:9,16); L1 chart_facts graha_position vocabulary (subject codes SUN/…/RAH_MEAN); L2 bodha_pratijna (391_bodha_pratijna.sql:5,17: build_id, UNIQUE(chart, ayanamsha, event_class)) + brahma_event_ontology whose domain column is CHECK-constrained to 13 values (388_brahma_ghatana_ontology.sql:14-16); L2 generation substrate data_plane_l2_producer_generations (1036:14-37)"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_AVADHI_v1_0.md (REWORK); re-verification of v1.1 pending"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/pipeline/orchestrator/writers/ka_avadhi.py", "platform/python-sidecar/tests/l3/test_m4_avadhi_lord_condition_refs.py, platform/python-sidecar/tests/test_migration_859_avadhi_expected_volume.py (the live-DB integration assertions; its migration-text assertions do not move)", "one NEW registry migration: successor to 1023 re-pinning conjunct (b) to the writer's system vocabulary and adding the stamp conjuncts (i)/(j) — every other conjunct byte-identical, 1023's own discipline (:36-43); and a successor to 859's expected_volume_inputs. It must not clobber migration 1034's output-digest spec on the same row (:53-55)", "one additive DDL migration on kala_avadhi if §10.3 takes columns over JSONB"]
interface_packet_targets_not_may_touch: ["platform/src/lib/retrieval/registry/layers/L3_kala/query_dasha_dossier.ts (serve coverage + pratijna_refs; and a read-time orphan resolver) — Pūrṇa-owned", "platform-mcp/src/tools/retrieval/kala_temporal.ts:277-321 (disclose the vimshottari-only filter AND the level_n:3 request the writer never satisfies) — Pūrṇa-owned; L3 owns only the sentinel test"]
must_not_touch: ["chart_dashas / ga_writers (L1)", "bodha_pratijna, brahma_event_ontology (L2/L0)", "services/ka_dasha_kala/tree_walk.py (ALL_DASHA_SYSTEMS is the clock authority's; adopted, never forked)", "applied migrations — supabase/migrations/395_kala_avadhi.sql, platform/migrations/670_*, 859_*, 1023_*, 1034_*, and 1033–1070 generally", "platform-mcp/src/tools/kala_views/**", ".github/workflows/deploy.yml", "kala_gochara_windows WHERE generation='v1'", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY (stage 3); DATA_ACCEPTED when a rebuild lands and the re-pinned contract returns TRUE for a reason; CONSUMER_INTEGRATED when query_dasha_dossier serves the coverage fields and kala_temporal discloses its filters"
target_state_campaign: "ANALYZED (this brief) → ENRICHED at stage 3; registry state `error` today"
wave: "W2 (foundation; independent preparation)"
shape: single asset, rows keyed (chart_id, system_id, level_n, period_start) — the DDL natural key (395:22); signature_class is not part of it
evidence_base: >
  Source read directly on 9feac52d7 [V]; reviewer-verified claims adopted are marked [R]; migrations
  395/670/859/1023/1034/1036/388/391, blueprint v5.0, Lane D, T1 [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.1 (2026-09-24): REWORK dispositions (25 findings) — F1 (BLOCKER) the orphan detector is re-specified as READ-time: the writer compiles its pratijñā ids from the live L2 rows in the same transaction, so a build-time anti-join has no path to return a dangling row and delete-then-insert removes orphans rather than marking them; F2 migration 1023 (on this brief's own base) superseded 670 for this asset and rewrote conjunct (d) — under 670's text the brief's own Positive row would fail for 7 of 9 grahas; F3 conjunct (e) is green immediately after a rebuild, red only when L2 regenerates without one; F4 _GRAHA_DOMAINS is not merely uncited — 21 of its 36 strings are outside brahma_event_ontology.domain's CHECK vocabulary and Rāhu matches nothing, so every Rāhu row is structurally empty; F5 bg_ghatana IS brahma_event_ontology (its target_table), so the declared edge is real and read — a native decision was resting on a false premise and is withdrawn; F6 the B3 offer was a per-build uuid4; F7 the Value row credited the M4 rebuild to the elevation; F8 the two caps cannot bind under current vocabularies and Q8 is not ruled; F9 L1 emits same-start chara_karaka rows the non-total ORDER BY + upsert silently collapse; F10–F25 role vocabulary, SC-10 misuse, citations, paths, the dead-domain control, level_n:3, generation substrate."
  - "1.0 (2026-09-24): first issue."
---

# `ka_avadhi` elevation brief — the period dossier, told honestly

## §0 — The recommendation, in one paragraph

`ka_avadhi` writes one dossier row per MD/AD period of seven daśā systems at the canonical ayanāṃśa
(`ka_avadhi.py:71-95,:194-201` [V]) — 1,169 rows live for the canonical chart (migration 859 [A]) —
carrying `lord_condition_fact_refs` (L1 `chart_facts` ids, never values), `activated_pratijna_ids`,
and a `sublord_modulation` note. Its registry state is **`error`**. Five things are wrong, and the
reviewer corrected two of my own premises. (1) **The seventh system has three names**: `chara` in
migration 395's DDL comment (`:27`), in the integrity contract's coverage conjunct (b) and in 859's
six-system volume formula, versus `chara_karaka` in the writer (`ALL_DASHA_SYSTEMS`,
`tree_walk.py:40-43`) and in L1 (`ga_dashas_writer.py:2026,2055,2084,2112` insert it at four levels
[R]) — so (b) is **vacuous** for that system, and a rebuild under today's writer, which refuses
unless all seven of *its* ids are present at MD and AD (`:207-224`), writes seven systems against a
formula expecting six. (2) **The pratijñā list is a domain match wearing an activation's name** —
no time test exists (`:280-290`) — and worse than "uncited": `_GRAHA_DOMAINS` (`:40-50`) uses 36
strings of which **21 are outside `brahma_event_ontology.domain`'s 13-value CHECK**
(`388:14-16`), so `pratijna_by_domain.get(d, [])` returns `[]` for them and **Rāhu (0 of 4 live
domains) can never match a pratijñā at all** [R] — the M4 vocabulary defect in the second
attribution array. (3) `strength_factor` is promised by the docstring (`:15`) and the DDL comment
(`395:37`) and **never emitted** (`:291-294`), with zero readers repo-wide [R]. (4) The two caps of
ten (`:142`, `:290`) **cannot bind** today: the fact query asks for 8 keys, and `bodha_pratijna` is
UNIQUE per `(chart, ayanāṃśa, event_class)` over 26 seeded classes so the largest per-graha union is
8 [R] — they are dead code, and Q8 is **not ruled** (blueprint `:658,:672`). (5) L1 emits
**same-`start_iso` `chara_karaka` MD rows** whose collapse under the writer's non-total `ORDER BY`
plus `ON CONFLICT DO UPDATE` is invisible to the contract [R]. Recommendation: **`ENRICH_CORRECT` +
`QUALIFY_LIMIT`** — rebuild; one vocabulary (adopt `chara_karaka`, re-pin by a successor to
**1023**); the domain map reconciled to the ontology; the pratijñā list renamed, generation-bound and
**orphan-detected at read time**, where a detector can fire; the caps removed as unreachable (Q8's
own text) or kept as a regression guard; `strength_factor` struck. Decisions: §10.

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 (REGISTER:147) | period dossier; refs only; DP05/07 | — |
| Strategy §3 *Clock interval* (`:91`) | *"Dasha/Avadhi/annual/return adapters; overlap and interval joins replace exact date-pair equality"*; applicability/prerequisites, failure reason, exact vs approximated | the dossier carries no applicability, no failure reason, DATE bounds only |
| **Strategy §6.1 L3-A12 (`:282`)** [R] | the asset's own row — it asks this brief to assess the **natural key and ayanāṃśa scope** | binds §4.9 (the same-start collapse) and §2.1 |
| Strategy §6.2 (`:336,:346`) | *"legacy L0–L2 source-table reads → overlays / Avadhi / Yojaka"*; *"registry still declares Avadhi→Taranga"* (Taranga does not consume Avadhi, `:47`) | confirmed: no Kāla writer reads `kala_avadhi` [V] |
| **Migration 1023** (`platform/migrations/1023_nirmana_l3_ka_avadhi_integrity_conjunct_d_graha_code_fix.sql:92-187`) [R] | merged #2556 (2026-09-10), **an ancestor of this brief's base**; `UPDATE asset_registry SET integrity_check_sql` for `ka_avadhi`, **replacing 670's whole text**. Conjunct (d) rewritten (`:153-174`): under 670's `upper('Jupiter')` vs `'JUP'` (`670:101-109`) the check fails for 7 of 9 grahas the moment refs are non-empty (`1023:13-34`); (b) left byte-identical, still `'chara'` (`1023:122-123`) | **this is the live contract**, not 670 (F2). The vacuity claim survives; my v1.0 Positive row silently depended on 1023's fix |
| Migration 670 header (`:25-26`) | ka_avadhi red; 3,087 unresolvable pratijñā ids | historical; the count is the **post-build drift** of an L2 regeneration, not a post-rebuild state (F3) |
| Migration 859 (`:15-24,:60-77`) | expected volume = 6 systems = 1,169; *"chara has zero exact matches; chart_dashas carries chara_karaka … Held item"* | 859 (2026-09-07) predates the writer's vocabulary change (`fa9857f00`, 2026-09-16) [R] — it was not wrong when written |
| Migration 1034 (`:53-55`) | sets `ka_avadhi`'s output-digest spec on the same registry row | the successor migration must not clobber it |
| Migration 1036 (`:14-37`) | `data_plane_l2_producer_generations (chart_id, asset_id, generation_id)` | the SC-9 substrate exists — `pratijna_refs[].generation` binds to it, not to a fall-through build id (F18) |
| Migration 395 (`:9-23,:27,:34-37`) | DDL: natural key `UNIQUE(chart_id, system_id, level_n, period_start)`; DATE bounds; `level_n ∈ {1,2,3}`; comment promises `{graha, strength_factor, modulation_note}` | `strength_factor` never emitted; `modulation_note` emitted as `note`; **level 3 never written** |
| **Migration 388 (`:14-16`)** [R] | `brahma_event_ontology.domain` CHECK: `career, wealth, relationship, progeny, health, education, family, residence, travel, spirituality, character, transition, general` — 13 values, unaltered by any later migration | the basis of F4 |
| **Migration 391 (`:5,:17`)** [R] | `bodha_pratijna.build_id UUID`; `UNIQUE(chart_id, ayanamsha_id, event_class_id)` | with 26 seeded classes, a chart holds ≤ 26 pratijñā at lahiri — the `[:10]` cap cannot bind (F8) |
| Seed (`asset_registry_seed.ts:2334-2352`) [R] | `depends_on: ['ga_dashas', 'bo_pratijna', 'bg_ghatana']`; **`bg_ghatana`'s own seed row has `target_table: 'brahma_event_ontology'`** | the edge the writer joins at `:105` **is** `bg_ghatana` — declared *and* read (F5); my v1.0 "declared-unread" claim was wrong |
| Blueprint §3.5 row 6 (`:322`), §4 (`:394`), §16.2 (`:904`), SC-5 (`:284`), **Q8 (`:658,:672` — still the native's)** | live; registry `error`; caps of 10 | Q8 is **not** a ruling (F8) |
| Lane D / T1 | consumer `query_dasha_dossier.ts` via `kala_temporal.ts` | confirmed; `kala_temporal.ts` fetches **vimshottari only** (`:278,:309,:314`) **and requests `level_n: 3`** (`:319`), which the writer never writes (F16) |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Identity and registration [V]
`storage_type: 'postgres_table'`, `target_table: 'kala_avadhi'`, chart-scoped `count_sql`,
`scope: 'per_chart'`, `sort_order: 4`, `catalog_status: 'CURRENT'`. `FORMULA_VERSION =
"ka_avadhi_v1.0"` (`:33`). Natural key `(chart_id, system_id, level_n, period_start)` (`395:22`) —
whose sufficiency L3-A12 asks this brief to assess (§4.9).

### 2.2 The code [V]/[R]
- **Reads**: `_FETCH_MD_SQL` (`:74-84`) level 1, `_FETCH_AD_SQL` (`:86-96`) level 2 with parent
  join, both `ayanamsha_id = 'lahiri_chitrapaksha'` (`_CANONICAL_AYANAMSHA`, `:72`) and
  `system_id = ANY(_DASHA_SYSTEMS)` where `_DASHA_SYSTEMS` (`:37`) = `tuple(sorted(
  ALL_DASHA_SYSTEMS))` = `{vimshottari, yogini, ashtottari, chara_karaka, naisargika, mudda,
  kalachakra}`; **DATE columns** (`start_date/end_date`), and **`ORDER BY (system_id, start_date)`
  only — not total** (`:81,:94`). `_FETCH_PRATIJNA_SQL` (`:101-109`): every `bodha_pratijna` row for
  the chart at lahiri joined to `brahma_event_ontology` for `domain`, **no generation, no status
  gate**, savepoint-guarded (`:226-247`). `_FETCH_FACT_REFS_SQL` (`:132-143`): `fact_category=
  'graha_position'`, eight real keys, `fact_subject = norm_graha(lord)` (`:259`), total `ORDER BY`,
  **`LIMIT 10` (`:142`)**; savepoint per graha (`:249-276`).
- **Refusal**: any of the seven ids missing at MD or AD → `rows_inserted=0`, *"incomplete
  dasha-system coverage … prior partition preserved"* (`:207-224`) — an honest refusal keyed to the
  writer's vocabulary. Satisfiable in principle: L1 emits `chara_karaka` at four levels with
  sign-name lords, and `chart_dashas.lord_graha` is `NOT NULL` (`206:9`) [R].
- **Build** (`_build_row`, `:280-309`): `domains = _GRAHA_DOMAINS.get(lord, [])` (`:40-50`,
  Title-case keys); `activated_ids` = every pratijñā in any of those domains, **no period-overlap
  test**, capped `[:10]` (`:290`); `sublord_modulation = {graha, note}` (`:291-294`) — **no
  `strength_factor`**; `quality = {domains}`; one literal `citations` entry (`:305-307`).
- **Write**: `DELETE … WHERE chart_id` then `executemany(_INSERT_SQL)` with `ON CONFLICT (chart_id,
  system_id, level_n, period_start) DO UPDATE` (`:324-327`; `:145-163`) — §N.3 conformant; never
  commits. No `date.today()`; whole-lifetime spine.

### 2.3 Consumers (grep `kala_avadhi`, tests/seed/generated excluded) [V]/[R]
| consumer | reads | role |
|---|---|---|
| `query_dasha_dossier.ts:96,:103-110` | rows by system/level/lord/date; `LIMIT 50` with `total_matching` + `more_available` — **disclosed** cap, the good pattern | served `computation` |
| `platform-mcp/src/tools/retrieval/kala_temporal.ts:277-321` | `query_dasha_dossier` with `system_id:'vimshottari'` only (`:278`), `level_n 1/2 active_on today` (`:309,:314`), **and `level_n: 3` for the snapshot `pd` (`:319`) which the writer never writes** | served `relevance_navigation` — six systems and one level silently absent |
| `source_query_availability.ts:3054-3064`; `data-plane-ownership-preflight.ts` | availability / ownership | census |
| Kāla writers, L4, `kala_views/**` | **none**; the dossier is served as opaque jsonb (zero readers of any dossier field by name outside the writer [R]) | — |

**Live-path statement.** Live on two served surfaces. The refs array is `[]` on every live row (M4
unrebuilt); the pratijñā list is live with 3,087 dangling ids and structurally empty for Rāhu; the
vimshottari-only filter and the unsatisfiable `level_n:3` request are live.

### 2.4 Epistemic class
| field | class | authority | note |
|---|---|---|---|
| `period_start/end`, `lord_graha`, `system_id`, `level_n` | `COMPUTED_FACT_CONFIGURATION` (inherited) | L1 `chart_dashas` | referenced, not restated; DATE grain (L1 has `start_iso/end_iso` **and `sandhi_flag`**, `206:9,16`) |
| `lord_condition_fact_refs` | reference bundle to L1 facts | L1 `chart_facts` | `[]` live; ordered by `fact_key, fact_id` |
| `activated_pratijna_ids` | **domain match** (navigation), not activation | L2 × `_GRAHA_DOMAINS` | no time test; no generation; 3,087 orphans; **21/36 map strings dead against the ontology CHECK; Rāhu 0/4** |
| `_GRAHA_DOMAINS` | inference map, **uncited and 58% out-of-vocabulary** | this writer | `source_qualification='unsourced'` **and** a vocabulary defect (F4) |
| `sublord_modulation.note` | narration (template) | this writer | `strength_factor` promised, absent |
| `citations` | literal | this writer | wrong for six of seven systems |

### 2.5 Ladders and cost
`PLAN_REVIEWED`; W2 source accepted. t3: no event (registry `error`). Cost: bounded reads; cheap;
unmeasured.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | Rebuild `ka_avadhi` for the canonical chart: the writer requires `chara_karaka` MD+AD (`:207-224`) and writes **seven** systems, while the registry's expected volume (859) is six = 1,169 and the live integrity contract's coverage conjunct (b) (**migration 1023**, `:122-123`) checks for a system id `'chara'` that L1 never emits — satisfied vacuously either way. Conjuncts (c)–(e) go green on the rebuilt rows; (e) goes red again only when L2 regenerates without a Kāla rebuild. Meanwhile every Rāhu MD/AD row carries `activated_pratijna_ids = []` **structurally** — all four of Rāhu's domain strings (`karma, foreign, technology, unusual`) are outside the ontology's CHECK vocabulary — and (e) passes vacuously for it; and where L1 emits two `chara_karaka` MD rows sharing a `start_date`, the non-total `ORDER BY` plus `ON CONFLICT DO UPDATE` keeps an order-dependent one and neither (a) nor (b) can see the collapse |
| Evidence | `ka_avadhi.py:37,:40-50,:71-95,:81,:94,:207-224,:280-290,:291-294,:305-307,:324-327`; `tree_walk.py:40-43`; `ga_dashas_writer.py:2026-2112`; `1023:122-123,:153-174`; `859:21-22,:60-77`; `388:14-16`; `391:5,17`; `395:22,:27,:37`; `stage3_clocks.py:1071-1076` — [V]/[R] |
| Expected contract | Strategy §3 *Clock interval*; **L3-A12** (key and ayanāṃśa scope assessed); DP01 (no rival definitions); §N.5 (references resolve); §N.7 items 1, 2 (total ORDER BY under a LIMIT), 3, 6; §N.8 (a green check must measure the claim — (b) cannot); SC-5; SC-9 |
| Defect class | **rival vocabulary** (three names, one system) + **vacuous detector** + **out-of-vocabulary inference map** (a second M4-class defect) + **mislabelled** (domain match called activation) + **unbound reference** (no L2 generation) + **silent collapse** (non-total order under an upsert) + **promised field absent** + **unreachable caps** |
| Impact | the registry cannot go green for the right reason; *"how will my Ketu daśā be"* (395 `:3`) is answered with an empty refs array and a partly-dead pratijñā list; a Rāhu period is silently empty; a consumer paging the timeline sees one system and one missing level and does not know it |
| Non-claim | whether the canonical chart's live `chart_dashas` holds `chara_karaka` at both levels, and whether same-start duplicates exist there, is **not measured** (the emitter code and a Kṣetra code comment say yes; no DB); the 3,087 and 1,169 figures are migration headers [A]; whether 1023 is applied in production is [A] on both sides |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q01 (which clocks are engaged), Q06 (what a period carries). Q-K01 is cited as a
   blueprint cross-reference only, not adopted as a question (F20). Not Q02/Q05.
2. **One vocabulary (DP01, not SC-10 — F11).** The writer already adopts the clock authority's
   `ALL_DASHA_SYSTEMS`; the registry follows: a **successor to migration 1023** re-pins conjunct (b)
   to `chara_karaka`, leaving every other conjunct byte-identical (1023's own discipline `:36-43`)
   and preserving migration 1034's digest spec; a companion successor updates 859's
   `expected_volume_inputs` to the seven-system count once measured. 395's DDL comment is corrected
   in the same migration. "One daśā-system vocabulary across L1/L3/registry" is raised as a
   synergy-map amendment, since no existing SC covers it.
3. **Rebuild** — the precondition; conjunct (c) goes green because refs resolve, not because the
   check was loosened.
4. **The domain map reconciled (F4).** `_GRAHA_DOMAINS` is brought into
   `brahma_event_ontology.domain`'s 13-value vocabulary: aliases `children→progeny`,
   `home→residence`, `moksha→spirituality`, `foreign→travel`, `property→residence`; the remaining
   out-of-vocabulary strings (`dharma, authority, mind, disputes, commerce, communication,
   creativity, luxury, karma, longevity, technology, unusual, loss, liberation`) have no ontology
   domain and are either dropped or raised as an **ontology DEMAND** (a graha whose significations
   genuinely have no domain is a gap in the ontology, not in this writer). A lord whose live domain
   set is empty emits `reason='domain_not_in_ontology'` — distinct from `lord_not_a_graha`.
5. **Pratijñā list renamed and labelled.** `pratijna_refs = [{pratijna_id, generation, domain,
   match_basis:'lord_natural_domain'}]` beside the legacy array for one generation;
   `operator_role='relevance_navigation'`, `epistemic_class='INTERPRETIVE_INFERENCE'`,
   `source_qualification='unsourced'`. **No time-overlap test is added** unless §10.2 rules the field
   should become an activation — which needs the pratijñā's own window (L2 offers none) and is a
   DEMAND, not a fabrication.
6. **Generation binding and READ-time orphan detection (F1, F3, F18).** `pratijna_refs[].generation`
   binds to `data_plane_l2_producer_generations` (`1036:14-37`) for `bo_pratijna`. The orphan
   detector is **not** a build-time anti-join — the writer compiles its ids from the live L2 rows in
   the same transaction, so nothing dangling can be found there, and delete-then-insert *removes*
   orphans rather than marking them. Detection lives in two places that can actually fire:
   (i) the registry conjunct (e), which already exists (`1023:177-184`) and reports the drift of an
   L2 regeneration against un-rebuilt rows; (ii) a **serve-time resolver** in `query_dasha_dossier`
   (interface packet, L3-owned sentinel) that compares each ref's `generation` to the L2 head and
   reports `completeness_state='unavailable'`, `reason='pratijna_orphaned'` with the F06 companions
   `owner`, `evidence_ref`, `next_eligible_action` (F21). A *persisted* orphan state would require
   the writer to preserve rows absent from the current L2 — accretion, forbidden by §N.3 — and is
   not proposed.
7. **Coverage (B5).** Per build: `{requested_horizon: null, completed_horizon: null,
   resolution:'period', partitions_searched: the seven systems, exclusions: [{kind, reason, dropped}]
   — including `reason='collapsed_same_start'` (§4.9) and `reason='domain_not_in_ontology'`,
   unsearched_regions: [], completion_detector:'all_candidates_classified'}`. Blueprint §12.1's
   Clock-interval names `clocks_consulted`/`clocks_unavailable` for the served projection (F17) —
   adopted there.
8. **The caps (F8).** Neither can bind under current vocabularies (8 fact keys < 10; ≤ 26 pratijñā
   per chart, largest per-graha union 8). Q8 is **not ruled**, so this brief does not cite it as one:
   it puts the question *to* Q8 and recommends **removing** both caps, since Q8's proposed text is
   "complete coverage where the set is finite" and both sets are finite and small. The Boundary proof
   row is kept only as a regression guard, and no `cap_10.dropped` counter is served (a counter that
   reads 0 forever is a detector with no red path — §N.8).
9. **The same-start collapse (F9, L3-A12).** Both spine fetches gain a **total `ORDER BY`**
   (`system_id, start_date, level_n, lord_graha`) so the surviving row under the upsert is
   deterministic, and the build compares L1 candidate count to rows written per system, reporting any
   difference as `exclusions[reason='collapsed_same_start']`. Whether the natural key should carry
   `start_iso` (or `lord_graha`) instead of `period_start` is put to the native (§10.5) — it is the
   key question L3-A12 asks and it cannot be answered without measuring the duplicates.
10. **`strength_factor`: struck** from docstring and DDL comment (zero readers repo-wide [R]);
    `sublord_modulation = {graha, note}` stays — an honest null beats an invented factor.
11. **Citations per system** from L0's source field (referenced), else `['unsourced']`.
12. **Instants (B1).** `period_start/end` stay DATE (the natural key); the dossier gains
    `t_start/t_end` from L1 `start_iso/end_iso` as `timestamptz`, `inclusivity='closed_open'`,
    `time_basis='event_instant'`, `claim_grain='instant_grain'`, **and carries L1's `sandhi_flag` by
    reference** (blueprint §12.1's qualification set, F17) — additive JSONB or columns (§10.3).
13. **Interface packets.** `query_dasha_dossier.ts`: serve `coverage`, `pratijna_refs` and the
    read-time resolver. `kala_temporal.ts`: disclose `systems_included: ['vimshottari']`,
    `systems_available: 7` **and** that its `level_n: 3` request (`:319`) can never be satisfied.
    Both Pūrṇa-owned; L3 owns the sentinels.
14. **Old vs new.** Positive: rebuild → refs resolve, seven systems, coverage present, contract TRUE
    **under the 1023 successor**. Negative: L1 missing one system at AD → refusal naming it.
    Boundary: regression guard on the (unreachable) caps. Missing: a Yoginī lord → `pratijna_refs=[]`
    with `reason='lord_not_a_graha'`; a Rāhu period **after** item 4 → non-empty, or
    `reason='domain_not_in_ontology'` if the ontology DEMAND is declined. Duplicated: two L1 rows
    sharing a `start_date` → deterministic survivor + a counted exclusion.
15. **Simpler baseline (F7).** The **elevated** rebuild is compared against an **M4-only rebuild**,
    not against today's unrebuilt rows — otherwise the Value row credits the M4 fix (plumbing) to the
    elevation. Under the M4-only baseline refs already resolve; the elevation's measured difference
    is the labelled `pratijna_refs` (incl. Rāhu non-empty), the coverage/exclusions, the seventh
    system present and the disclosed served filters.
16. **Ablation.** Regenerate L2 without rebuilding: today the dossier carries dangling ids silently
    and the served answer cannot tell; after, the serve-time resolver marks them `unavailable` with
    a reason and the count appears in the envelope.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: refs-not-values (B.3); canonical-ayanāṃśa scoping (CR-110); savepoint-guarded soft
  dependencies; the all-systems refusal; delete-then-insert; `norm_graha` normalisation.
- `ENRICH_CORRECT`: vocabulary re-pin; the domain map; `pratijna_refs` + generation + the read-time
  resolver; total `ORDER BY` + collapse accounting; coverage; per-system citations; instants +
  `sandhi_flag`.
- `QUALIFY_LIMIT`: `_GRAHA_DOMAINS` `unsourced`; `note` as narration.
- **Struck**: `strength_factor`; and the two caps (§10.4).
- **Migrations**: a successor to **1023** (conjunct (b) + stamp conjuncts (i)/(j), every other
  conjunct byte-identical, 1034's digest spec preserved) and a successor to 859; optionally one
  additive DDL (§10.3). No FK (the cascade lesson, G20).
- **Registry edges**: all three declared edges are real — `bg_ghatana`'s `target_table` **is**
  `brahma_event_ontology` (F5), so nothing is dropped. The `ka_dasha_kala` import is **not an F12
  input** (`vocabulary` is not one of the eight roles, F10): it is a code-level constant import,
  recorded here, with no `depends_on` edge.
- **Tests that move**: `test_m4_avadhi_lord_condition_refs.py` (key list if the priority order lands);
  `platform/python-sidecar/tests/test_migration_859_avadhi_expected_volume.py` — its **migration-text**
  assertions (`:36,:72-78`) do **not** move (859's file is untouched); only its live-DB integration
  assertions do (F13).
- Rollback: the writer's payload is additive; the registry migration is reversible by a further
  successor.

---

## §6 — Lenses A–J *(appendix; the proof matrix is §7)*

| lens | answer |
|---|---|
| A | `ka_avadhi`, L3 rows; L1/L2 reference bundle + one uncited, partly out-of-vocabulary inference map + template narration; placement correct; `ENRICH_CORRECT + QUALIFY_LIMIT` |
| B | real reads: `chart_dashas`, `chart_facts`, `bodha_pratijna`, `brahma_event_ontology` (= `bg_ghatana`); `ka_dasha_kala` constant import, no edge; fan-out: two served surfaces; T1 |
| C | invariants: spine = L1; every ref resolves and names its lord; every pratijñā id resolves **or is marked at read time**; seven systems under one name; every `_GRAHA_DOMAINS` value ∈ the ontology's 13; deterministic survivor under same-start collapse; `strength_factor` absent everywhere |
| D | the seventh system's L1 rows and their duplicates (unmeasured); pratijñā windows (L2 offers none); the ontology's missing domains |
| E | `query_dasha_dossier` (disclosed cap — good), `kala_temporal` (undisclosed system filter + unsatisfiable level) |
| F | coverage, `pratijna_refs`, `systems_included`, the resolver's `reason` machine-readable |
| G | negligible; justified no-change |
| H | idempotent; savepoints; no credentials |
| I | files in `may_touch`; W2; two registry successors; the ontology DEMAND named |
| J | this brief; §7; the review; the successor contract's TRUE after rebuild |

---

## §7 — Proof matrix

Columns: **verdict tier** is F24's; **scope** `[U]` unit/DB-free, `[I]` DB fixture, `[S]` served.

| proof | verdict tier | scope | fixture / command | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|---|
| Vocabulary | COMPUTATIONAL_CORRECTNESS | U | assert every value of `_GRAHA_DOMAINS` ∈ the 13-value CHECK set (parsed from `388:14-16`) | all pass | one vocabulary | **fails today** (21 strings, Rāhu 0/4) | unit test |
| Positive | COMPUTATIONAL_CORRECTNESS | I | rebuild on a fixture with all seven L1 systems; run the **1023-successor** `integrity_check_sql` | TRUE; refs non-empty on every graha-lord row; Rāhu rows non-empty | (a)–(e) + stamps | any conjunct FALSE; a stamp absent | integrity SQL |
| Negative | COMPUTATIONAL_CORRECTNESS | I | L1 fixture missing `chara_karaka` AD | refusal names `AD=chara_karaka`; 0 rows; prior partition kept | honest refusal | rows written | writer test |
| Relevant influence | COMPUTATIONAL_CORRECTNESS | I+S | regenerate `bodha_pratijna` ids in the fixture **and do not rebuild**; then read through the resolver | refs marked `unavailable`, `reason='pratijna_orphaned'`, count in the envelope | read-time detection | silent dangling ids (today) | route test |
| Irrelevant control | COMPUTATIONAL_CORRECTNESS | U | shuffle `pratijna_by_domain` insertion order | `activated_ids`/`pratijna_refs` set-equal and canonically ordered | order-canonical | order leaks into the payload | unit test |
| Duplication | COMPUTATIONAL_CORRECTNESS | I | two L1 `chara_karaka` MD rows sharing `start_date` | deterministic survivor under the total `ORDER BY`; `exclusions[reason='collapsed_same_start'].dropped = 1` | §N.7 item 2 | order-dependent survivor; collapse invisible | writer test |
| Context | COMPUTATIONAL_CORRECTNESS | U | a Yoginī lord; a Rāhu lord with the ontology DEMAND declined | `reason='lord_not_a_graha'` / `reason='domain_not_in_ontology'` | declared missingness | silent `[]` | unit test |
| Boundary (regression) | COMPUTATIONAL_CORRECTNESS | U | 11 synthetic candidate refs | if the caps are removed: all 11 kept; if retained: 10 + a counted exclusion | the §10.4 ruling | behaviour drifts from the ruling | unit test |
| Delivery | COMPUTATIONAL_CORRECTNESS | S | sentinel `reason='pratijna_orphaned'` on one row | reaches `query_dasha_dossier`'s envelope **as a named jsonb field** (the dossier is served opaquely today) | survives | absent | route test |
| Delivery (timeline) | COMPUTATIONAL_CORRECTNESS | S | `kala_temporal` bundle | `systems_included`, `systems_available`, and the `level_n:3` unsatisfiability disclosed | disclosed | absent | MCP test |
| Revision | COMPUTATIONAL_CORRECTNESS | I | L1 `chart_dashas` regenerated | rows replaced | no accretion | accretion | writer test |
| Value | EXPLANATORY_DISCRIMINATIVE_VALUE | S | frozen Q06 question, **M4-only rebuild vs elevated rebuild** | labelled refs, non-empty Rāhu, coverage/exclusions, seventh system, disclosed filters | the elevation, not the M4 fix | no difference beyond M4's | baseline record |
| Evaluation | — | — | `not_applicable` (a dossier issues no claim) | — | — | — | — |

Binding: **OFFERS** B1 (`t_start/t_end`, `inclusivity`, `time_basis`, `claim_grain`, and L1's
`sandhi_flag` by reference), B2 (`completeness_state` + the F06 companions, `epistemic_class`,
`operator_role`, `source_qualification`), B5 (`coverage`). **B3 — not offered as an id today
(F6):** `avadhi_id` is a `gen_random_uuid()` surrogate regenerated every build, which B3 forbids;
either a content-addressed `sha256(chart_id, system_id, level_n, period_start, FORMULA_VERSION)` is
added (§10.3) or B3 is honestly declined. **DEMANDS** L2 `bodha_pratijna` generation (via 1036) and,
if §10.2 rules activation, the pratijñā's own window; **and an ontology DEMAND** for the domains
item 4 cannot alias. B4: n/a (no testimony aggregation). **Asset-local:** `pratijna_refs`,
`match_basis`, `sublord_modulation`, `quality.domains`, `citations`, `systems_included`.

---

## §8 — Prioritization

(1) the domain-map vocabulary fix (a structurally empty Rāhu is the largest live defect) →
(2) rebuild under M4 → (3) the 1023-successor vocabulary re-pin (the check becomes non-vacuous) →
(4) generation binding + the read-time resolver → (5) the total `ORDER BY` + collapse accounting →
(6) label the pratijñā list; strike `strength_factor`; citations → (7) coverage and the cap ruling →
(8) instants + `sandhi_flag` → (9) the two served disclosures. T1; W2.

---

## §9 — Disposition and target state

`ENRICH_CORRECT` + `QUALIFY_LIMIT`. Data-plane: `PRODUCER_READY` after the `[U]`/`[I]` rows;
`DATA_ACCEPTED` when the rebuilt rows pass the successor contract on production;
`CONSUMER_INTEGRATED` when both served packets carry the sentinels. Campaign: `ANALYZED → ENRICHED`.
Non-claims: no `VALUE_EVALUATED`; the domain map stays uncited until sourced; the seventh system's
live row count and its duplicates are unknown until rebuilt and measured.

**Walkthrough (ordinary period).** "What does my current antardaśā carry?" → one row: Jupiter AD
under Saturn MD, `t_start/t_end` instants with L1's `sandhi_flag` referenced, eight resolved L1 refs,
`pratijna_refs` of the domain-matched pratijñā **in the ontology's own vocabulary** with their
generation, `exclusions=[]`, `sublord_modulation.note`. Nothing invented; nothing structurally empty.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Vocabulary: adopt `chara_karaka` and re-pin conjunct (b) + 859 by successors to 1023/859** | yes — L1 is the authority (§N.5) |
| 2 | **Pratijñā list: labelled domain match (`relevance_navigation`), or a true time-overlap activation (DEMAND on L2 for pratijñā windows)?** | labelled navigation now; raise the DEMAND; do not fabricate overlap |
| 3 | `strength_factor` struck; instants as JSONB or columns; a content-addressed `window_id` added or B3 declined | strike; instants as JSONB; **add the sha256 id** so B3 is offered honestly |
| 4 | **The two caps: remove (both sets are finite and small, per Q8's own proposed text) or retain?** — and note Q8 is still the native's, not a ruling this brief may cite | remove; keep the regression guard |
| 5 | **L3-A12's key question:** should the natural key carry `start_iso`/`lord_graha` rather than `period_start`, given L1's same-start `chara_karaka` rows? | measure the duplicates at stage 3, then decide; until then the total `ORDER BY` + collapse counter makes the loss visible |
| 6 | **Ontology DEMAND:** 14 graha-signification domains have no `brahma_event_ontology` value | raise to the ontology's owner; alias the five that map |

---

## §11 — Not verified here

1. Whether `chart_dashas` holds `chara_karaka` MD **and** AD rows for the canonical chart, and
   whether same-`start_iso` duplicates exist — the emitter (`ga_dashas_writer.py:2026-2112`) and a
   Kṣetra code comment (`stage3_clocks.py:1071-1076`) say yes; no DB.
2. Whether migration 1023 is applied in production (its file is merged on `main`; the ledger is DB).
3. The 3,087 orphan count, the 100.00% empty-refs figure, the 1,169 row count — migration headers [A].
4. Whether `chart_facts` holds more than one build generation per subject (the only way `LIMIT 10`
   could bind).
5. No database query; no test run.

## §12 — Review dispositions (v1.0 → v1.1)

F1 accepted — the orphan detector moved to read time (§4.6, §7 Relevant-influence), with the
accretion alternative named and rejected; F2 accepted (frontmatter, §1 new row, §3, §5, §7 —
migration 1023 is the live contract); F3 accepted (§1, §3 — (e) is green after rebuild, red on
regeneration-without-rebuild); F4 accepted (§0, §2.4, §3, §4.4, §7 Vocabulary row, §10.6 — a defect,
not a citation gap); F5 accepted — the `bg_ghatana`/`brahma_event_ontology` decision **withdrawn**
(§1, §5); F6 accepted (§7 binding, §10.3); F7 accepted (§4.15, §7 Value); F8 accepted (§0, §4.8,
§10.4 — Q8 is not ruled; the caps cannot bind); F9 accepted (§2.2, §3, §4.9, §7 Duplication, §10.5);
F10 accepted (§5 — `vocabulary` is not an F12 role); F11 accepted (DP01, not SC-10); F12 accepted
(line numbers re-pinned); F13 accepted (`may_touch`, §5); F14 accepted (`kala_temporal.ts` moved to
`interface_packet_targets`; boilerplate added to `must_not_touch`); F15 accepted (§7 irrelevant
control); F16 accepted (§2.3, §4.13 — `level_n:3`); F17 accepted (§4.7, §4.12 — §12.1 names +
`sandhi_flag`); F18 accepted (§1, §4.6 — migration 1036); F19 accepted (§2.2, §3 non-claim — upgraded
to [V] with the emitter citation and 859 dated); F20 accepted (§4.1); F21 accepted (§4.6 — F06
companions); F22 accepted (§4.10, §7 Delivery — opaque jsonb passthrough); F23 noted; F24 accepted
(`may_touch` — 1034's digest spec); F25 accepted (lenses moved to an appendix).
