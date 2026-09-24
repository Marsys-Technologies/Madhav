---
artifact: KALA_BRIEF_INDEPENDENT_REVIEW
canonical_id: REVIEW_KA_YOJAKA
version: "1.0"
status: REVIEW_ISSUED
date: 2026-09-24
brief_under_review: 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KA_YOJAKA_ELEVATION_BRIEF_v1_0.md
reviewer: "Fable 5.1 review agent, fresh context, read-only"
worktree: "/Users/Dev/madhav-l3/layer-briefs @ 27b0146f3 (branch l3/kala-layer-briefs)"
source_revision_check: "brief cites 9feac52d7; `git diff 9feac52d7 HEAD` on ka_yojaka.py, services/ka_yojaka/, ph_nimitta.py, migration 670 is empty — the code the brief read is the code reviewed"
method: "every file:line re-read with sed/grep on this worktree; no DB, no network, no git write"
---

# Independent review — `KA_YOJAKA_ELEVATION_BRIEF_v1_0`

## 1. Verdict

**`REWORK`.** The brief's primary deliverable — the orphan detector — is specified in a form the
writer's own delete-then-insert makes vacuous at build and unreachable as a persisted state; its
serve-time half lives in a file that does not exist and is not in `may_touch`; the F06 mapping
misses a third `always_on_reason` that is in the code; the integrity contract it cites (670) was
superseded twice (1019, 1022) and is no longer what is installed; and the live-path/impact
statement is wrong in direction (every downstream INSERT target carries an FK that would refuse an
orphan, so the hazard is a build failure, not silent propagation to L4 or serving). The diagnosis
(no generation, no FK, 79 dangling) and the preservation list are sound; the mechanism and the proof
matrix need to be re-specified before the native rules.

## 2. Findings

| id | sev | brief claim (section) | found at source | proposed correction |
|---|---|---|---|---|
| F1 | **BLOCKER** | §4 item 3: *"Build: after the candidate is compiled, an anti-join against the current MSR; any dangling reference is written with `completeness_state='unavailable'`, `reason='signal_orphaned'`"*; §7 Context/missingness row expects that persisted state after *"delete one MSR row after bind"*; §5 migration adds `stale_against_msr bool` as a column. | The candidate is compiled from `SELECT … FROM bodha_msr_signals WHERE chart_id = %s` (`ka_yojaka.py:78-89`) inside the same transaction; every `signal_id` in the candidate exists by construction, so a build-time anti-join has no code path to return a dangling row. The writer then `DELETE … WHERE chart_id` (`:443-447`) and re-inserts only the current signals (`:424-451`): an orphan is *removed* by a rebuild, never written as `signal_orphaned`. A stored `stale_against_msr` is always `false` at write time and no writer runs afterwards to flip it — a status with no detector behind it (CLAUDE.md §N.8). The brief's own §10 D1 concedes *"fail-closed at build cannot catch them"* but §4/§7 still specify the build-time form. | Re-specify: orphan and freshness are **read-time** computations (a resolver + anti-join at consume/serve, and in the registry `integrity_check_sql`), never stored columns. If a persisted orphan state is wanted, the brief must say explicitly that the writer preserves prior rows absent from the current MSR — which is accretion, contradicting §N.3 and the §7 Revision row ("no accretion") — and get that ruled. Rewrite the Context/missingness row so its detector is the resolver, with a fixture that can go red. |
| F2 | **BLOCKER** | §4 item 3: *"a shared `resolve_signal_ref()` (in `services/ka_qualification/identity.py`, SC-3) that Kalasutra, Saṅgam, Vighnakara and the served surfaces call"*. | `platform/python-sidecar/services/` has no `ka_qualification/` directory on this base (listing checked). Blueprint §16.1 (`KALA_ELEVATION_BLUEPRINT_v1_0.md:885`) plans that file as the **SC-3 W1 packet**. It is not in the brief's `may_touch`, and §7 DEMANDS only *"L2 generations (W1) and `bodha_signal_identity`"*. The serve/consume-time half of the detector therefore has no owner, no file and no declared dependency. | Declare a DEMAND on SC-3 (`identity.py`) with a stated fallback (a local resolver under `services/ka_yojaka/`), or add the file to `may_touch` with the SC-3 owner's consent. State which. |
| F3 | MAJOR | §2.2: *"Two reasons now exist and are deliberately distinct"*; §4 item 4 maps exactly two (`distribution_yoga_all_grahas` → `inapplicable`, `no_resolvable_dasha_lord` → `unavailable`); §6 C invariant *"`inapplicable` ⇔ distribution reason"*. | Three exist: `'distribution_yoga_sankhya'` (`ka_yojaka.py:975`, source `ka_yojaka:sankhya_fire_reason`), `'distribution_yoga_all_grahas'` (`:988`), `'no_resolvable_dasha_lord'` (`:407`). The F06 mapping and the invariant omit the saṅkhyā reason. | Map all three (saṅkhyā → `inapplicable`, by doctrine); make the CHECK/test enumerate the three literals so a fourth appearing goes red. |
| F4 | MAJOR | §2.2: *"migration `670_…:1738-1819` installs `ka_yojaka`'s `integrity_check_sql` … the check is chart-partitioned and reads false today on a cascade-damaged chart by design (670 header, `:22-35`)"*; §3 Evidence *"the only detector is the registry `integrity_check_sql` (migration 670 `:1752-1759`)"*. | 670 was superseded by `1019_nirmana_l3_ka_yojaka_integrity_check_scope.sql` (conjunct (c) scoped to canonical, `:83-89`) and then `1022_nirmana_l3_ka_yojaka_integrity_check_scope_ab.sql` (conjuncts (a) and (b) scoped to canonical, `:83-91`, `:96-105`). 1022's header `:17-22` states the red was **canonical's own** rows (pre-determinism v4 ids vs v5, zero overlap), *"NOT cross-chart contamination"* — not cb73cd3d. After the 2026-09-10 rebuild (`1024_…:35-39`) the canonical red is the 79. Consequence for the brief: the live conjunct (a) — the very detector §4 proposes to "move" — is canonical-only and detects nothing on any other chart. | Cite 1022 as the live contract; correct the causal claim; note the canonical-only scope as a limitation the read-time resolver must not inherit. |
| F5 | MAJOR | §2.3 *"All six reads are live. The 79 orphans are live rows on every one of them; nothing on any path distinguishes an orphaned `signal_id` from a valid one"*; §3 Impact *"Kalasutra dates it, Saṅgam converges on it, L4 anchors on it"*. | (i) Serving: `query_temporal_activation.ts:376-394` fetches predicates only for `signal_id`s present in returned `kala_activation` rows; `kala_activation.signal_id` is `ON DELETE CASCADE` to MSR (`403_kala_signal_fk_cascade.sql:10-13`), so an orphaned signal has no activation row and its predicate cannot reach the tool. `ahead.ts`/`now.ts` never read the response's `predicates` field (no `.predicates` reference in either file; they consume `activations`). (ii) L4: `ph_nimitta.py:143-147` keys its lookup on `signal_id`s from `kala_convergence`/`kala_bhavishya`/discoveries — all FK-CASCADE (`403:15-23`) — so an orphan's id is never queried at `:476-482`. (iii) `ka_jivana_parva.py:120-125` LATERALs from `kala_convergence.signal_id` — same. (iv) `ka_kalasutra.py:38-48`, `ka_sangam.py:278-311` (LEFT JOIN keeps orphans), `ka_vighnakara.py:435-436` **do** read orphans — but their INSERT targets `kala_activation`, `kala_convergence`, `kala_obstruction` all carry FKs to `bodha_msr_signals` (`403:10-33`); no filter in either writer (grep `bodha_msr_signals`/`IS NOT NULL` in kalasutra: `:75` only, unrelated). An orphan that gets dated raises an FK violation → build failure. | Restate the live hazard honestly: (a) FK-violation build-failure risk in three writers if any of the 79 is datable; (b) **no live path** from an orphaned predicate to L4 or a served reading today. Drop the *"L4 anchors on it"* chain. Keep "silent" only for the predicate table itself. |
| F6 | MAJOR | §4 item 3 defines freshness as *"`stale_against_msr` … computed from the consumed build ids vs the current ones"*; §7 Boundary row: *"an L2 rebuild that preserves identity → `signal_ref` resolves; `stale=false`"*, detector fails when *"flagged stale"*. | `bodha_msr_signals.build_id` is `UUID NOT NULL` and part of the UNIQUE key (`226_bodha_spec_tables.sql:22, :111`); any L2 rebuild issues a new `build_id`. Under the brief's own definition an identity-preserving rebuild is *always* stale — the Boundary row cannot pass under its own detector. | Define staleness on the identity hash (`bodha_signal_identity`, `661_l2_bodha_signal_identity.sql:53-59`), not on `build_id`; keep `consumed_msr_build_ids` as a receipt only. |
| F7 | MAJOR | Header `may_touch` lists `platform-mcp/src/tools/kala_views/{ahead,now}.ts` and `ph_nimitta.py:478-486` ("interface packet only"); `must_not_touch` also lists `ph_nimitta.py`. | `KALA_ASSET_BRIEF_CONTEXT_v1_0.md` §5: *"Do not design changes to it"* (kala_views); instantiation guide §2 requires `platform-mcp/src/tools/kala_views/**` under `must_not_touch`. A file cannot be in both lists. | Move both to `must_not_touch`; carry the packets as L3-U04/U11 obligations with L3-owned tests only. |
| F8 | MINOR | §0/§1: *"Its accepted repair (`7697c43b3`) restored the per-domain confirmation/strength/promise map"*. | `git show 7697c43b3`: the diff changes `multi_system_confirmation_aggregate_rule` from `'max_supported_domain_v1'` to `'primary_domain_v1'`, adds `primary_domain = domains[0]`, and makes `multi_system_confirmation_count` the *first-domain* value *"exactly matching ph_nimitta's existing `domains_affected_array[1]` selection"*. The map itself (`_build_structural_domain_context`) landed in `fa9857f00` (#2607, 2026-09-16). The repair *narrowed* the compat scalar toward L4's first-domain read. | Attribute correctly; say plainly that the accepted repair institutionalised the first-domain scalar the brief now proposes to label as compat-only. |
| F9 | MINOR | §2.1: *"seven edges, the widest in the layer"*. | `ka_sangam` declares ten (`asset_registry_seed.ts:2312`). | Drop "the widest". |
| F10 | MINOR | §2.2 *"whichever of the seven L2 producers"* vs §3 *"any of the six MSR producers"*. | Six `bo_*` writers call `replace_prior_msr_*` (`bo_arudha`, `bo_laksana`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`); the blueprint says seven. | Pick one figure and cite the grep. |
| F11 | MINOR | Header: *"migrations 660/661: deterministic signal_id over (chart, ayanamsha, signal_type, varga, configuration)"*. | Only `661_l2_bodha_signal_identity.sql:53-59` defines `bodha_signal_identity(p_chart_id, p_ayanamsha_id, p_signal_type_id, p_varga_id, p_configuration)`; `660_nirmana_l2_registry_accuracy.sql` has no identity content. | Cite 661 alone. |
| F12 | MINOR | §4 item 1 / §6 / blueprint row: serves *"Q-K02 (activated vs dormant over the whole mechanism set)"*. | Q-K01–16 are Lane E's portfolio (`LANE_E_LAYER_VALUE_MODEL.md:144`); `KALA_PRE_ELEVATION_CRITICAL_REVIEW_v1_0.md:102-107` (C3) refuses them as baseline; Context §2 forbids a question outside L3-Q01–Q13. | Cite Q-K02 only as a coverage cross-check, or drop. |
| F13 | MINOR | §4 item 4: *"`tier_basis='relative_uncalibrated'` on every score; `comparable_with` n/a (predicates are not scores)"*. | The row carries `dasha_activation_proximity_score`, `cgm_centrality_weight` (`:316`), `cdlm_domain_strength*` (`:332-336`) — scores. Binding B4: *"any projection carrying a score carries `independence_group` + `comparable_with`"*. `independence_group` is absent from the brief. | Either declare the weights scores (then B4 applies in full) or not (then `tier_basis` is n/a). State `independence_group` disposition. |
| F14 | MINOR | §4 item 6 / §10 D3: *"instead of reading every ayanāṃśa's signals into one candidate"*; D3 offers *"partition all five explicitly"* as a change. | Each row already carries the signal's `ayanamsha_id` (`:210`, `:414`), the unique index is `(chart_id, signal_id, ayanamsha_id)` (`243_l3_ka_yojaka.sql:21-22`); the only ayanāṃśa-blind operations are the DELETE by chart (`:445`) and the cross-ayanāṃśa `COUNT(DISTINCT bp.ayanamsha_id)` confirmation count (`:175`), the latter by design. "Partition all five" is current behaviour. | Reframe D3 as DELETE scope and/or `domain_confirmation` semantics, or remove it. |
| F15 | MINOR | §5: migration *"numbered ≥ 1082 (1080–1081 claimed by Gochara WP0-7)"*. | In-tree max is 1072 (`platform/supabase/migrations/1072_…`); blueprint `:440,:585` says 1080+; `KA_TITHI_PRAVESHA_ELEVATION_BRIEF_v1_0.md:240` also claims ≥1082. | Say "next free slot at execution, verified via `git ls-tree origin/main`" (the 1022 header's own practice). |
| F16 | NOTE | §2.1 cites `estimated_seconds: null`. | Guide §3/§11: never cite `asset_registry.estimated_seconds`. Harmless as null, but the field should not appear. | Remove. |
| F17 | NOTE | Header shape *"rows (chart × ayanāṃśa × signal × predicate signature)"* (quoting Strategy `:281`). | DB key is `(chart_id, signal_id, ayanamsha_id)` (`243:21-22`); `signature_class` is not part of the key; 1:1 per signal (`864_…:18-23`). | State the physical key. |
| F18 | NOTE | §4 item 3: `completeness_state='unavailable'`, `reason='signal_orphaned'`. | Foundation §3 (`FOUNDATION_CONTRACT:72`): completeness records `reason`, `owner`, `evidence_ref`, `next_eligible_action`. | Add the other three fields. |
| F19 | NOTE | §3 Evidence: *"`pg_constraint`: no FK … (Lane F §3.1 live) [A]"*; §11 item 1 "not re-queried". | Verifiable at source without a DB: `243_l3_ka_yojaka.sql:4-24` has no `REFERENCES`; grep across both migration trees finds no later FK on this table. | Upgrade to [V] with the DDL citation. |
| F20 | NOTE | §7 Irrelevant control: *"map keys identical; `primary_domain` changes"*. | Reordering `domains_affected_array` also changes `multi_system_confirmation_count` (`:918-922`, keyed off `primary_domain`) and the order of `pratijna_ids` (`:869-879`) — exactly the two values L4 reads. | List all order-dependent outputs in the row. |
| F21 | NOTE | §1 Lane D row: *"the 'flattening at :479-510' citation could not be relocated"*. | Register:147 anchor `W/ka_yojaka.py:479–510` resolves today to `_fetch_house_lord_map` (`:455-490`); the brief's relocation to `:886` and L4's read is correct. | None; recorded as verified. |

## 3. Citations verified

All paths relative to the worktree root. "resolves" = the line(s) say what the brief says.

| citation | result |
|---|---|
| `ka_yojaka.py:15-26` (anti-fabrication docstring) | resolves (`:12-27`) |
| `ka_yojaka.py:61` `@register`; `:69-70` dry_run | resolves |
| `ka_yojaka.py:78-89` / `:80-87` unfiltered SELECT, no build_id/ayanamsha filter | resolves (`:78-89`) |
| `ka_yojaka.py:92-96` empty → "prior predicate partition preserved" | resolves |
| `ka_yojaka.py:268-277` firing-lord override | resolves (`:269-281`) |
| `ka_yojaka.py:316` cgm weight; `:332-348` rule/hook assignments; `:344` `'primary_domain_v1'`; `:348` `contrary_signal_ids` | resolves |
| `ka_yojaka.py:390-407` generalised `no_resolvable_dasha_lord` | resolves (`:390-408`) |
| `ka_yojaka.py:426-448` INSERT/DELETE; `:431` `ON CONFLICT DO NOTHING`; `:440-445` DELETE after candidate | resolves (`:424-451`; DELETE at `:443-447`) |
| `ka_yojaka.py:538` CGM pagerank; `:573` CDLM | resolves (`:535-541`, `:571-577`) |
| `ka_yojaka.py:608-619` `ga_yoga_firings` query | resolves (`:606-613`) |
| `ka_yojaka.py:845-903` `_build_structural_domain_context`; `:886` `primary_domain = domains[0]`; `:926` | resolves (def at `:841`; `:886`; `:926`) |
| `ka_yojaka.py:938-995` `_resolve_firing_lords`; `:988` `distribution_yoga_all_grahas` | resolves — **and `:975` `distribution_yoga_sankhya` is a third reason the brief omits (F3)** |
| "no anti-join / no EXISTS / no `bodha_signal_identity` in the writer" | resolves (grep: none) |
| `670_nirmana_l3_w3_integrity_contracts.sql:1738-1819`, `:1747-1759`, `:1772-1783`, header `:22-35` | lines resolve to the text quoted — **but the contract is superseded by 1019/1022 (F4)** |
| `asset_registry_seed.ts:2360-2369` | resolves (block `:2354-2371`); `depends_on` seven edges confirmed; "widest" false (F9) |
| `ph_nimitta.py:478-486` | resolves (`:476-482`, SELECT of `multi_system_confirmation_count` only); brief marked it [A] — now [V] |
| `ka_jivana_parva.py:113-124` LATERAL `LIMIT 1` | resolves (`:118-125`) |
| `ka_kalasutra.py` reads `constituent_lords`, `always_on_reason`, emits `kind:'always_on'` | resolves (`:45`, `:129-135`, `:235`) |
| `ka_vighnakara.py` reads predicates | resolves (`:435-436`) |
| `ka_sangam.py` reads predicates, `transit_trigger_jsonb` mutation R-1 | resolves (`:278-311`; `:1415-1435` in-memory) |
| `query_temporal_activation.ts`, `kala_views/ahead.ts`, `kala_views/now.ts` "served reads" | `query_temporal_activation.ts:376-394` reads the table; `ahead.ts`/`now.ts` read only via that capability and never touch `predicates` (F5) |
| `243_l3_ka_yojaka.sql` DDL, unique index `(chart_id, signal_id, ayanamsha_id)`, no FK | resolves (`:4-24`) |
| `403_kala_signal_fk_cascade.sql` five CASCADE tables; predicates table absent | resolves (`:10-33`) |
| `661_l2_bodha_signal_identity.sql` tuple `(chart, ayanamsha, signal_type, varga, configuration)` | resolves (`:53-59`); 660 does not (F11) |
| `226_bodha_spec_tables.sql` `bodha_msr_signals.build_id` exists | resolves (`:22`, `:111`) |
| `MADHAV_DATA_PLANE_ASSET_CONTRIBUTION_REGISTER_v2_0.md:147` | resolves verbatim |
| `MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` L3-A11 `:281`, L3-U01 `:441`, L3-U07 `:447`, §3 "79 predicate signal IDs" `:117`, §4 step 3 `:145-147`, §6.3 `:11-13` (rel. to §6.3 block), L3-Q01 `:62`, L3-Q03 `:64` | resolve. Note: U07 (`:447`) is about activity/valence/probability separation — not the per-domain map; the brief's U07 framing is loose |
| `MADHAV_DATA_PLANE_L3_CURRENT_STATE_AND_DISPOSITION_v1_0.md:131` "first frontier; non-FK signal refs guarded" | resolves; brief's "guard does not exist" verified at code |
| `KALA_DATA_CENSUS_v1_0.md` §4a 79/50,678, `bound_at` 2026-09-10 17:17:03 | resolves (`:117-136`, `:32`) — figures are the census's, not re-measured |
| `LANE_F_DEMAND_LEDGER.md` §1c (`:131-135`), §2c (`:252-264`), §3.1 (`:286-313`), §3.4 (`:361-400`) | resolve; §3.4 recommends value column / deferred FK / identity recompute / L2 diff-upsert as the brief says |
| `LANE_D_ASSET_REGISTER.md` §16 (`:792`), `T1_SPINE.md` §2 (`:97-110`) | resolve |
| `KALA_ELEVATION_BLUEPRINT_v1_0.md` §3.3 SC-3 `:282`, SC-9 `:288`, SC-10 `:289`; §3.5 row 5 `:321`; §16.1 `:885,:891`; §16.2 `:903`; §17.2 `:953` | resolve; `:885` places `services/ka_qualification/identity.py` under SC-3/W1 (F2) |
| `KALA_NATIVE_RULING_SHEET_v1_0.md` R4 `:113-130` | resolves: ruled "stable signal key + upstream generation … one migration in the L3 range (1071+), touching only L3-owned foreign keys"; RESTRICT and SET NULL rejected — the brief's D2 (no FK) is consistent with, not a new decision beyond, R4 |
| `KALA_ASSET_BRIEF_CONTEXT_v1_0.md` §2, §5, §11 | resolve (F7, F12) |
| F04 / F06 / F12 vocabularies (`FOUNDATION_CONTRACT:31,33,39,63-68,72`) | `COMPUTED_FACT_CONFIGURATION`, `INTERPRETIVE_INFERENCE`, six F06 values, `applicability`/`relevance_navigation`/`computation`/`interpretation` all valid |
| commit `7697c43b3` "restored the per-domain map" | does **not** resolve as described (F8) |
| commit `9feac52d7` = source revision | exists; writer/service/670/ph_nimitta identical to HEAD `27b0146f3` |
| `platform/scripts/nirmana/cascade_check.sql` | exists |
| `services/ka_qualification/identity.py` | **does not exist** (F2) |
| `tests/l3/test_ka_yojaka*.py` | five files exist; none mentions orphan/dangling |

## 4. What could not be verified, and why

- The **79 / 50,678** orphan count, the 0.156 %, the single `bound_at` instant, and the 0-row
  state of `kala_activation`/`kala_convergence` — no DB access; taken from the census [A]. The
  1022/1024 headers corroborate 50,678 and the 2026-09-10 rebuild but were written 2026-09-10.
- Whether any of the 79 orphaned predicates carries `constituent_lords` (i.e. whether the
  FK-violation build-failure hazard in F5 is live or latent) — requires a DB query.
- Build duration — unmeasured, as the brief says; no `KALA_COST_PROFILE_v1_0.md` exists on this
  base to cite.
- `services/ka_yojaka/{binder,classifier}.py` — not read line-by-line (grep only, matching the
  brief's own declared scope).
- Live `pg_constraint` state — verified at DDL/migration level only (F19).

## 5. Conformance to the binding (B1–B7)

- **B2** — `epistemic_class`, `completeness_state` (six values), `operator_role`, `tier_basis`
  named correctly. `comparable_with` declared n/a while scores are present (F13).
- **B3** — the brief coins `signal_ref = {producer_asset_id, l2_generation, signal_id,
  signal_identity_tuple_hash}`. B3's cross-asset handle is `window_ref = {asset_id, generation,
  id}` (blueprint SC-3 `:282`); the L2-identity row names no field. The keys differ from the
  established pattern for the same concept (asset / generation / id). Non-conformant until it
  aligns to `{asset_id, generation, id, identity_hash}` or declares the mapping.
- **B4** — `independence_group` absent; not disposed (F13).
- **B5** — the brief's `coverage` `{signals_read, predicates_compiled, undated_inapplicable,
  undated_unavailable, orphaned, consumed_msr_build_ids}` reuses the B5 name with a different
  shape; B5 fixes `{requested_horizon, completed_horizon, resolution, partitions_searched[],
  exclusions[], unsearched_regions[], completion_detector}` on every result. Either emit the B5
  shape (partitions = ayanāṃśas searched; exclusions = undated-by-reason; completion_detector =
  the resolver) or name the build receipt something other than `coverage`.
- **Fields outside B1–B7**: `stale_against_msr`, `consumed_msr_build_ids`, `signal_orphaned`,
  `domain_map_basis` (the last is blueprint-sanctioned, `:903`). The first two are also the
  subject of F1/F6.
- **B7** — the Context/missingness and Boundary rows are the binding's tests 6 and 7; as written
  neither can go red for the reason the row claims (F1, F6).

*End of review. Read-only; no repository, database or network write beyond this file.*
