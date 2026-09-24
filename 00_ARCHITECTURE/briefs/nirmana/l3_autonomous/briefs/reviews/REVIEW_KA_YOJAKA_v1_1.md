---
artifact: KALA_BRIEF_INDEPENDENT_REVIEW
canonical_id: REVIEW_KA_YOJAKA
version: "1.1"
status: REVIEW_ISSUED
date: 2026-09-24
brief_under_review: 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KA_YOJAKA_ELEVATION_BRIEF_v1_0.md (frontmatter version "1.1")
prior_review: briefs/reviews/REVIEW_KA_YOJAKA_v1_0.md (REWORK; 2 BLOCKER, 5 MAJOR, 14 MINOR/NOTE)
reviewer: "Fable 5.1 review agent, fresh context, read-only"
worktree: "/Users/Dev/madhav-l3/layer-briefs @ a99300bb7 (branch l3/kala-layer-briefs)"
source_revision_check: "brief cites 9feac52d7; `git diff 9feac52d7 a99300bb7 --stat` on ka_yojaka.py, services/ka_yojaka/, ph_nimitta.py, ka_kalasutra.py, ka_sangam.py, ka_vighnakara.py, query_temporal_activation.ts, kala_views/, both migration trees is EMPTY — the code the brief read is the code reviewed"
method: "every v1.0 finding re-verified at source against v1.1 (§12 not trusted); every new file:line re-read with sed/grep; no DB, no network, no git write; the only write is this file"
---

# Independent re-review — `KA_YOJAKA_ELEVATION_BRIEF` v1.1

## 1. Verdict

**`REWORK`** — narrower than v1.0. Both v1.0 BLOCKERs are genuinely closed (the stored flag is
withdrawn; the resolver is a declared DEMAND with a fallback) and 17 of 21 v1.0 findings are
RESOLVED at source. But the third specification of the mechanism still cannot be executed or
tested inside the brief's own fence: the new `identity_hash` key is byte-identical to `signal_id`
for every v5 row and cannot be "recomputed from the consumed row" because the predicate row stores
none of the five-tuple; the read-time resolver has no caller in `may_touch`, and the one served
route it names can never observe an orphan; the "current L2 head" it compares against has nothing
in it and the brief does not define the interim; the "datable decides build-failure vs inert"
framing is false for Kalasutra (which INSERTs a fallback row for every undated predicate); and the
"chart-partitioned" successor to 1022 is, under the runner that executes it, exactly the
table-wide gate 1022's own header shows is structurally unpassable. Each is a paragraph to fix,
but together they re-specify §4.2, §4.3, §7 (four rows) and §10 D2.

## 2. Findings

| id | sev | brief claim (section) | found at source (exact `file:line` read) | proposed correction |
|---|---|---|---|---|
| N1 | **MAJOR** | §4.2: `signal_ref … identity_hash: bodha_signal_identity(...)` — *"The hash is recomputed from the **consumed** signal's own fields at bind time, so a rebuild that preserves identity resolves"*; §6 C invariant *"`identity_hash` reproducible from the consumed row"*; §7 Boundary: *"new `build_id`, same hash → `identity_hash` resolves"*. | (i) Under migration 661 `signal_id` **is** `bodha_signal_identity(chart, ayanamsha, signal_type_id, varga_id, configuration_jsonb)`: every MSR producer assigns it in its INSERT (`bo_laksana.py:3206`, `bo_sudarshana.py:119`, `bo_nakshatra_semantic.py:86`, `bo_special_lagna.py:81`, `bo_vargottama_dhana.py:91`), and migration 931 (`:82-84`) is the conformance detector. After the 2026-09-10 rebuild (`1022:17-22`) canonical is all-v5, so `identity_hash == signal_id` on every row the writer consumes; the fourth key adds no information. (ii) "Recomputed from the consumed row" is impossible at read time: the predicate row persists only `chart_id, ayanamsha_id, signal_id` (`243:6-8`; `ka_yojaka.py:411-420`) and the ledger's `source_context` carries only `chart_id, ayanamsha_id, signal_id, constituent_fact_ids` (`ka_yojaka.py:921-927`); the writer's own SELECT does not even read `varga_id` (`ka_yojaka.py:80-87` — columns: `signal_id, chart_id, ayanamsha_id, signal_type_class, signal_type_id, configuration_jsonb, …`; `varga_id` exists on the table, `325:73`). (iii) Consequently the Boundary row's detector reduces to "a row with this `signal_id` exists for (chart, ayanamsha)" — which is migration 1022's conjunct (a) verbatim (`1022:83-91`). | State that under 661 `signal_id` is the identity and define staleness as *no MSR row at `(chart_id, ayanamsha_id, signal_id)`*. Either drop `identity_hash`, or persist the five-tuple (`signal_type_id, varga_id, configuration_jsonb`) and say what independent recomputation buys (only the v4→v5 case 1022 already closed). Rewrite the Boundary row so its detector differs from 1022(a) or admit it does not. |
| N2 | **MAJOR** | §4.3 *"read time: a resolver on the consume/serve path … reports `completeness_state='unavailable'`, `reason='signal_orphaned'`"*; §7 Context/missingness scope `I+S`, evidence *"route test"*; §7 Build-failure row *"after: the resolver marks it `unavailable` and Kalasutra skips it"*; §7 Delivery *"reaches `query_temporal_activation`'s envelope"*. | (i) No file in `may_touch` reads predicates at consume time; the three readers (`ka_kalasutra.py:36-49`, `ka_sangam.py:280-311`, `ka_vighnakara.py:433-441`) are all in `must_not_touch`, as are `kala_views/**` and `query_temporal_activation.ts` (Pūrṇa-owned, per the brief's own `interface_packet_targets_not_may_touch`). A local resolver under `services/ka_yojaka/` would have **zero callers** within the fence. "Kalasutra skips it" is a change to `ka_kalasutra.py`. (ii) The served route named cannot observe an orphan: `query_temporal_activation.ts:373-394` builds `predSignalIds` from the returned `kala_activation` rows (`:375-378`) and fetches predicates `WHERE … signal_id IN (…)` (`:391`); `kala_activation.signal_id` is `ON DELETE CASCADE` (`246:6`, `403:10-13`), so an orphaned predicate is never selected there. Deleting an MSR row in the fixture cascades its activation and the route returns nothing about it — the `[S]` half of Context/missingness has no code path to go red *or* green for the stated reason (the F1 defect class, one layer over). (iii) Whether the app's DB role may EXECUTE `bodha_signal_identity` is unverifiable here; migration 936 (`:14-16`) had to grant it to `nirmana_evidence_ingress_writer` explicitly, so PUBLIC EXECUTE is not assured. | Say plainly: within this brief's fence the **only** detector that can fire is check-time (`integrity_check_sql`) plus a unit-tested resolver module with no caller; consume-time detection is an obligation carried by the three readers' briefs and SC-3, and serve-time detection needs a predicate-first capability (an L3-U04/U11 packet) — `query_temporal_activation` is the wrong sentinel target. Re-scope Context/missingness to `[I]` + check-time; move the Build-failure "after" state to Kalasutra's brief; keep Delivery as a fixture-injected sentinel and say it cannot arise from data on that route. Add the EXECUTE grant to the migration or to §11. |
| N3 | **MAJOR** | §4.2 `generation: <L2 generation>`; §4.3 the resolver *"compares `signal_ref.identity_hash` (and `generation`) against the current L2 head"*; §9 *"`DATA_ACCEPTED` only on an accepted L2 generation"*. | The substrate exists — `data_plane_l2_producer_generations` keyed `(chart_id, asset_id, generation_id)` (`1036:14-45`), `l2_data_plane_generation_heads` `(chart_id, asset_id, current_generation_id)` (`1036:232-243`), per-row content in `l2_data_plane_row_snapshots` (`1036:206-226`), and all seven MSR producers are registered outputs (`1036:255-262`) — but Context §3 measured **zero** L2 generations ever opened (2026-09-22 [A]); the head table carries no signal-level content, so "compare against the head" is a join against nothing today. The brief DEMANDS L2 generations (§7) but never says what `signal_ref.generation` holds until one exists, nor what the resolver compares against in the interim — which Context §3 requires (*"state explicitly what changes if the decision goes the other way"*). | Define the interim: `generation = null` (or the `build_id` receipt, labelled as not-a-generation) until a head exists; resolver target = live `bodha_msr_signals` by `(chart_id, ayanamsha_id, signal_id)` now, `l2_data_plane_row_snapshots` by `(chart, asset, generation, row_identity)` once heads are selected. State which `asset_id` the head is looked up under (see N6). |
| N4 | **MAJOR** | §0/§3/§6 D/§11.1: *"if any of the 79 is datable, the downstream INSERT … raises an FK violation … if none is, they sit inert and invisible"*; *"whether any is datable … decides build-failure vs inert"*; §2.3 Saṅgam/Vighnakara *"a datable orphan raises an FK violation"*. | **Kalasutra** inserts at least one `kala_activation` row for **every** predicate it reads: `period_entries = windows.period_windows or [{start: None, …}]` (`ka_kalasutra.py:147-152`) then `rows.append(…)` per entry (`:153-170`) with no `continue` in the loop (`:100-170`); the INSERT (`:189-200`) has `ON CONFLICT (…) DO NOTHING`, which does not absorb an FK violation; the FK is `NOT NULL … ON DELETE CASCADE` (`246:6`, `403:10-13`). So on a Kalasutra-only rebuild **any** orphan — datable or not — fails the `executemany` batch. Datability is irrelevant for Kalasutra. **Saṅgam**: orphans survive the LEFT JOIN with `raw_dignity_score NULL`, rank **last** per class (`ORDER BY raw_dignity_score DESC NULLS LAST`, `:296-299`), are cut at 200/class in SQL (`:305-307`, `_MAX_PREDICATES=200` `:142`), then sort at `-1.0` in `_select_top_predicates_with_class_quota` (`:203-206`); an orphan reaches the INSERT (`:990-1019`) only if its class holds < 200 rows *and* the engine emits a window — possible, not "raises". **Vighnakara**: returns early when `kala_convergence` is empty (`:186-190`; 0 rows on canonical today), and a daśā-anchored orphan reaches the INSERT (`:285-292`) only if datable, first claimant of its peak date (`:463-466`, `ORDER BY signal_id`), under `_MAX_DASHA_ANCHORS=200` (`:40`) and with `_detect_all` non-empty. | Restate: the live hazard is *unconditional* for Kalasutra (any orphan, any rebuild that does not first re-run Yojaka) and *conditional and bounded* for Saṅgam and Vighnakara; drop "datable decides"; §11.1 then asks the right unmeasured question (does a Kalasutra-only rebuild ever run against un-rebuilt predicates?). Note that a full DAG build re-runs Yojaka first and removes the orphans (§N.3), so the hazard is confined to partial/`rebuild_only` runs. |
| N5 | **MAJOR** | §4.3 / §8 / §10 D2: *"a successor [to 1022's conjunct (a)] that is **chart-partitioned rather than canonical-pinned**, so the same drift is detected on every chart"*. | `asset_runner._probe_asset` executes `integrity_check_sql` with **no parameters** and takes the first column of one row as a boolean (`asset_runner.py:816-830`). A chart-partitioned *gate* is therefore a table-wide gate — precisely what 1019 and 1022 removed: 1022's header (`:23-30`) records that cb73cd3d's 49,730/49,875 pre-existing violation "can never be cleared by anything this campaign's dispatch does — the check is structurally unpassable regardless of how correct a canonical rebuild is." D2 re-opens that condition without addressing the reason it was closed. The chart-attributing pattern that *does* exist is a **report function** beside the gate — `bodha_n5_lineage_report()` (`661:87-100`, "chart-partitioned per D-CND-03 … binds no parameter"). | Split D2: (a) keep the pinned boolean gate (or pin it to "every chart Yojaka has built *since* the successor migration"); (b) add a 661-style per-chart report function (`kala_yojaka_orphan_report()` returning `(chart_id, orphan_count)`) that the readiness query surfaces — detection on every chart without an unpassable gate. Cite 1022:23-30 as the constraint. |
| N6 | MINOR | §4.2 `signal_ref = {asset_id: <producer>, …}`; §7 *"B3 (`signal_ref` in the `{asset_id, generation, id}` shape)"*. | `bodha_msr_signals` has no producer-asset column: `source_l1_asset` is the **L1** origin (`325:68`), `signal_tradition`/`signal_type_class` are taxonomies (`226:24-26`), and `engine_version` is a free-text label (only `bo_laksana`'s `"bo_laksana_v2.2"` verified, `bo_laksana.py:74`; the other five producers' values not found by grep). Seven assets share the table (`1036:255-262`). The brief names no derivation for `asset_id`. | State the derivation (`engine_version` prefix with a declared mapping, or `l2_data_plane_row_snapshots.asset_id` once generations exist) or emit `asset_id: null` with `reason` until one exists. Do not invent an attribution (§N.7 item 6). |
| N7 | MINOR | §5: *"in-tree max is 1072; ruling R4 says the L3 range is 1071+"*. | 1071 and 1072 are already taken (`platform/supabase/migrations/1071_kala_convergence_target_provenance.sql`, `1072_kala_convergence_episodes.sql`); `platform/migrations/` tops at 1042. Blueprint §5.1 (`:440`) and §7 (`:585-586`) say L3 lands at **1080+** in `platform/migrations/` (1075–1079 consumed by the L0 repair, 1080–1081 by Gochara WP0-7). "Verified at execution" is right; the cited range is stale. | Cite blueprint 1080+ and the `platform/migrations/` directory; keep "verified at execution against `origin/main`". |
| N8 | NOTE | Header field `interface_packet_targets_not_may_touch`. | Not a contract §1 field (`…EXECUTION_BRIEF_CONTRACT_v1_0.md:19-41` lists `may_touch` / `must_not_touch` only); the guide says "verbatim fields" (§2). Harmless and useful; non-standard. | Keep, but move the list into §5 "Fences" prose or get the field added to the contract; do not let a validator trip on it. |
| N9 | NOTE | §2.3: *"`kala_convergence` is FK-CASCADE-bound (`403:15-23`)"*. | `403:15-18` is `kala_bhavishya`; `kala_convergence` is `:20-23`. | `403:20-23`. |
| N10 | NOTE | §2.3 ph_nimitta: *"its lookup is keyed on ids from `kala_convergence`/`kala_bhavishya`/discoveries (`:143-147`)"*. | Stronger than stated: the predicate lookup at `:476-482` iterates `signal_meta.keys()` (`:473`), and `signal_meta` is built **from `bodha_msr_signals`** (`:413-428`) — an id that no longer resolves in the MSR is never queried, independently of the cascade. Discoveries contribute `NULL::uuid AS signal_id` (`:380`). | Cite `:473` + `:413-428`; drop "discoveries". |
| N11 | NOTE | Header: *"L3-U07 interface to ph_nimitta (per-domain map)"*. | Strategy `:447` U07 is activity/valence/prior/probability separation and duplicate-anchor independence; the per-domain map is closer to U01's "complete domains/roots" (`:441`) — the same looseness v1.0 §3 noted. | Cite U01 for the map; cite U07 only for the confirmation-count-is-not-support point. |
| N12 | NOTE | §2.1 *"seven edges … `ka_sangam` declares ten (`:2312`)"*; §2.1 file cited as `asset_registry_seed.ts`. | Resolves — but the file is `platform/scripts/seed/asset_registry_seed.ts` (`:2312`, `:2354-2371`); the brief gives no directory. | Add the path once. |

## 3. Citations verified

All paths relative to the worktree root. "resolves" = the line(s) say what the brief says.

| citation | result |
|---|---|
| `ka_yojaka.py:12-27` anti-fabrication docstring; `:61` `@register`; `:69-70` dry_run | resolves |
| `ka_yojaka.py:78-89` unfiltered SELECT — no `build_id`, no `ayanamsha_id`, **no `varga_id`** | resolves (`:80-87`); the missing `varga_id` is N1 |
| `ka_yojaka.py:92-96` empty → "prior predicate partition preserved" | resolves |
| `ka_yojaka.py:175` `COUNT(DISTINCT bp.ayanamsha_id)` | resolves |
| `ka_yojaka.py:210`, `:414` `ayanamsha_id` on row | resolves |
| `ka_yojaka.py:269-281` firing-lord override; `:316` cgm weight; `:332-348`; `:344` `'primary_domain_v1'` | resolves |
| `ka_yojaka.py:407-408` `no_resolvable_dasha_lord` | resolves (`:405-408`) |
| `ka_yojaka.py:424-451` INSERT/DELETE; `:431` `ON CONFLICT DO NOTHING`; `:443-447` DELETE after candidate; `:445` | resolves |
| `ka_yojaka.py:535-541` CGM; `:571-577` CDLM; `:606-613` `ga_yoga_firings` | resolves |
| `ka_yojaka.py:841-903` `_build_structural_domain_context`; `:869-879` promise order; `:886` `primary_domain = domains[0]`; `:918-922` count keyed off primary | resolves |
| `ka_yojaka.py:938-995` `_resolve_firing_lords`; `:975` `distribution_yoga_sankhya`; `:988` `distribution_yoga_all_grahas` | resolves; DOSHA branch `:1000-1026` returns `None` reason — **exactly three literals** in non-test code (grep `always_on_reason` over `platform/`: `ka_yojaka.py:277,405,407`; `ka_kalasutra.py:131,135` reads only) |
| "no orphan detection anywhere in the writer" | resolves (grep: no `EXISTS`/anti-join/`bodha_signal_identity` in `ka_yojaka.py`) |
| `243_l3_ka_yojaka.sql:4-24` no `REFERENCES`; `:21-22` UNIQUE `(chart_id, signal_id, ayanamsha_id)` | resolves (`platform/supabase/migrations/`) |
| `403_kala_signal_fk_cascade.sql:10-33` five CASCADE tables; predicates absent | resolves; convergence is `:20-23` (N9). No later migration drops any of the five constraints (grep both trees) |
| `246_l3_ka_kalasutra.sql:6` `kala_activation.signal_id NOT NULL REFERENCES … ON DELETE CASCADE` | resolves (read for N4) |
| `226_bodha_spec_tables.sql:22`, `:111` `build_id UUID NOT NULL`, in UNIQUE | resolves |
| `661_l2_bodha_signal_identity.sql:53-59` five-arg identity; 660 no identity content | resolves (`platform/migrations/`); `:79-84` COMMENT and `:87-100` `bodha_n5_lineage_report` read for N1/N5 |
| `1019:83-89` conjunct (c) canonical-scoped | resolves (`:76-89`) |
| `1022:17-22` header (v4→v5, "NOT cross-chart contamination"); `:83-91` (a); `:96-105` (b) | resolves; `:23-30` (structurally unpassable table-wide) read for N5 |
| `1024:35-39` 2026-09-10 rebuild, 50,678 | resolves |
| `864:18-23` one predicate per signal | resolves |
| `KALA_NATIVE_RULING_SHEET_v1_0.md:113-130` R4 | resolves ("1071+"; N7 on the range) |
| `ka_sangam.py:278-311` LEFT JOIN keeps orphans; `:1415-1435` in-memory mutation | resolves; `:296-299` NULLS LAST, `:142` cap, `:170-226` quota selector, `:335-353` meta fetch (no drop), `:990-1019` INSERT read for N4 |
| `ka_kalasutra.py:45`, `:129-135`, `:235` | resolves; `:147-170`, `:189-200` read for N4 |
| `ka_vighnakara.py:435-436` | resolves (`:433-441`); `:186-190`, `:250-292`, `:40` read for N4 |
| `ka_jivana_parva.py:118-125` LATERAL `LIMIT 1` from `kala_convergence.signal_id` | resolves |
| `ph_nimitta.py:143-147`, `:476-482` | resolves; `:473`, `:413-428`, `:380` read for N10 |
| `query_temporal_activation.ts:376-394` predicates only for returned activation `signal_id`s | resolves (`:373-394`); read for N2 |
| `kala_views/{ahead,now}.ts` consume `activations`, never `.predicates` | resolves (grep: only comments mention predicates) |
| `register_d8_assess_domain.ts:1461` lists `kala_activation_predicates` | reads via `query_temporal_activation` handler (`:1467`); not a direct predicate read |
| `source_query_availability.ts:3146-3150` direct `FROM kala_activation_predicates` | a `LIMIT 0` availability probe; no rows served |
| `platform/scripts/seed/asset_registry_seed.ts:2354-2371` ka_yojaka block; `:2312` ka_sangam ten edges | resolves; `estimated_seconds` no longer cited by the brief (grep) |
| `asset_runner.py:816-830` `integrity_check_sql` executed with no parameters, one boolean | read for N5 |
| `1036:14-45`, `:206-226`, `:232-243`, `:255-262` generation tables | read for N3; openers exist (`bodha_writers/data_plane_contracts.py:505`, imported by all `bo_*` writers) |
| `325_l2_bodha_enriched_schema.sql:68`, `:73` `source_l1_asset`, `varga_id` | read for N1/N6 |
| `bo_laksana.py:3206`, `bo_sudarshana.py:119`, `bo_nakshatra_semantic.py:86`, `bo_special_lagna.py:81`, `bo_vargottama_dhana.py:91` `signal_id = bodha_signal_identity(...)`; `931:82-84` conformance | read for N1 |
| `936:14-16` EXECUTE grant needed for `bodha_signal_identity` | read for N2 |
| `KALA_ELEVATION_BLUEPRINT_v1_0.md` §3.5 row 5 (`:321`); §16.1 `:885` (SC-3 `identity.py`), `:891` (SC-9); §16.2 `:903`; `:440`, `:585-586` (1080+) | resolve |
| Strategy `:62`, `:64` (Q01/Q03); `:117`; `:145-147`; `:281` (A11); `:441` (U01); `:447` (U07) | resolve (N11 on U07) |
| Register `:147`; CURRENT_STATE `:131`; Lane F §3.4 `:361-400`; census §4a `:117-136`, `:32` | resolve (census at `l3_autonomous/audit/KALA_DATA_CENSUS_v1_0.md`) |
| Foundation `:33` F06; `:72` companions `reason/owner/evidence_ref/next_eligible_action` | resolve |
| commits `7697c43b3` (narrowed count to first domain, 20-line writer diff) and `fa9857f00` (#2607, map landed) | resolve as v1.1 now states |
| `services/ka_qualification/identity.py` | does not exist (v1.1 says so) |
| `tests/l3/test_ka_yojaka*.py` — five files | exist; none mentions orphan / `signal_ref` / `identity_hash` |

## 4. What could not be verified, and why

- The **79 / 50,678** count and whether any orphan carries `constituent_lords` — no DB. Note
  that after N4 the datability question matters only for Saṅgam/Vighnakara; for Kalasutra any
  orphan is fatal on a Kalasutra-only rebuild.
- Whether `data_plane_l2_producer_generations` / `l2_data_plane_generation_heads` hold rows
  today — no DB; Context §3's zero-count is 2026-09-22 [A].
- Whether the application DB role may EXECUTE `bodha_signal_identity` — no DB (`936` implies a
  grant is needed per role).
- Whether migrations 1019/1022/1024 and 1035/1036 are applied in production — file-level only.
- Live `pg_constraint` on the five cascade tables — verified at DDL (246/403) and by the absence
  of any later DROP in either migration tree.
- `services/ka_yojaka/{binder,classifier}.py` — grep only (no `always_on_reason`, no orphan
  logic).
- No test run; no build.

## 5. Conformance to the binding (B1–B7)

- **B2** — `epistemic_class`, six-state `completeness_state`, `operator_role`, `tier_basis`,
  `comparable_with` named correctly; F06 companions present (§4.3). Conformant.
- **B3** — `signal_ref = {asset_id, generation, id, identity_hash}`: the first three match the
  binding's `window_ref` shape; `identity_hash` is a declared extension. Conformant in shape;
  see N1 (the extension is redundant with `id`) and N6 (`asset_id` has no source column).
- **B4** — `independence_group` + `comparable_with` now emitted on the scores. Conformant.
- **B5** — `coverage` in the seven-key shape with `exclusions[{reason, count}]` and the build
  counters asset-local. Conformant. `completion_detector: 'all_msr_rows_for_chart_compiled'` is
  a real invariant (864:18-23) but is trivially true by construction; a detector that could go
  red would be `predicates_compiled == signals_read`.
- **Fields outside B1–B7**: `consumed_msr_build_ids`, `domain_map_basis` (blueprint-sanctioned,
  `:903`), `signals_read`, `predicates_compiled`, `identity_hash` — all declared asset-local or
  as an extension. No v1.0 residue (`stale_against_msr`, `signal_orphaned`-as-column) remains.
- **B7** — Context/missingness (test 6) and Boundary (test 7): as written, the `[S]` half of
  test 6 cannot observe the condition on the route named (N2) and test 7's detector is
  indistinguishable from 1022(a) (N1). Test 9 (served sentinel) is a fixture-only sentinel on
  a route that cannot carry the real condition (N2).

## 6. Disposition of the v1.0 findings, verified at source

| v1.0 id | sev | v1.1 status | evidence |
|---|---|---|---|
| F1 | BLOCKER | **PARTIAL** | The stored flag is withdrawn and accretion is named and rejected (§4.3, §7 Revision) — the BLOCKER is closed. But the replacement read-time detector has no caller in the fence and cannot observe an orphan on the served route it names (N2); the check-time successor as specified is table-wide (N5). |
| F2 | BLOCKER | **RESOLVED** | `identity.py` declared a DEMAND with a local fallback under `services/ka_yojaka/` (frontmatter, §5, §10.5); `services/ka_qualification/**` in `must_not_touch`. Whether the fallback has a caller is N2, a new finding. |
| F3 | MAJOR | **RESOLVED** | Three literals mapped (§2.2, §4.4, §7 Positive); verified exactly three in code (`:407`, `:975`, `:988`). |
| F4 | MAJOR | **RESOLVED** | 1022 cited as the live contract with the header's causal claim (§1, §3); canonical-only scope stated. The proposed successor is N5. |
| F5 | MAJOR | **PARTIAL** | Direction corrected (no live path to L4/serving; build-failure hazard) and verified (§2.3 table holds). But "datable decides" is false for Kalasutra and overstated for Saṅgam/Vighnakara (N4). |
| F6 | MAJOR | **PARTIAL** | Staleness moved off `build_id` (§1, §4.2, §7 Boundary) — correct. But the identity hash is `signal_id` itself and cannot be recomputed from the stored row, so the Boundary detector collapses to 1022(a) (N1). |
| F7 | MAJOR | **RESOLVED** | `kala_views/**`, `ph_nimitta.py` in `must_not_touch`; packet targets listed separately (N8 on the field name). |
| F8 | MINOR | **RESOLVED** | `fa9857f00` landed the map; `7697c43b3` narrowed the scalar (`accepted_upstream_contract`, §2.4, §4.5) — matches `git show`. |
| F9 | MINOR | **RESOLVED** | "widest" dropped; ka_sangam's ten cited (`:2312`). |
| F10 | MINOR | **RESOLVED** | Producer count no longer restated (grep). |
| F11 | MINOR | **RESOLVED** | 661 alone cited; "660 carries no identity content" verified (grep). |
| F12 | MINOR | **RESOLVED** | Q-K02 cited as a coverage cross-check only (§4.1). |
| F13 | MINOR | **RESOLVED** | Weights declared scores; `independence_group` + `comparable_with` bound (§2.4, §4.4). |
| F14 | MINOR | **RESOLVED** | D3 reframed as DELETE scope; "partition all five" stated as current behaviour (§4.6, §10.4). |
| F15 | MINOR | **RESOLVED** (with N7) | "Verified at execution" adopted; the cited "1071+" range is stale. |
| F16 | NOTE | **RESOLVED** | `estimated_seconds` absent (grep). |
| F17 | NOTE | **RESOLVED** | Physical key stated in `shape` and §2.1. |
| F18 | NOTE | **RESOLVED** | `owner`, `evidence_ref`, `next_eligible_action` named (§4.3). |
| F19 | NOTE | **RESOLVED** | FK absence marked [V] with the DDL citation (§1, §11.5). |
| F20 | NOTE | **RESOLVED** | Irrelevant-control row enumerates `primary_domain`, `multi_system_confirmation_count`, `pratijna_ids` order. |
| F21 | NOTE | **RESOLVED** | Recorded. |
| B3 shape | — | **RESOLVED** | `{asset_id, generation, id}` + declared `identity_hash`. |
| B5 shape | — | **RESOLVED** | Seven-key shape; counters asset-local. |

*End of review. Read-only; no repository, database or network write beyond this file.*
