---
artifact: DASHA_TABLE_CONTRACT
version: "1.0"
status: LOCAL_DRAFT — proposed K0-SV read contract; Suvarṇa acknowledgement pending
item: K0-SV
produced_on: 2026-10-07
---

# Proposed `chart_dashas` read contract for Kāla F2

This is a local proposal for the interface between Suvarṇa's L1 `ga_dashas` producer and Kāla's F2 clocks. It does not record an agreement, a settled L1 build, or a change to Gochara 5.0's frozen §4.0 pin. K0-SV's `suvarna_acknowledged` step remains open until Suvarṇa acknowledges this text (or a reconciled revision) in the campaign-coordination log. No coordination-branch write is made by this draft.

## Evidence and boundary

- Kāla architecture plan v1.1 §3.1 daśā read inventory, §3.2 `clocks/` row, and §4.1 F2 rows: one pinned read supplies period context, boundaries, applicability, hierarchy, sandhi bands and uncertainty scenarios. The plan is at `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md` in the campaign checkout.
- Suvarṇa's `00_ARCHITECTURE/briefs/suvarna/layers/L1/L1_LAYER_INSTANCE_v1_0.md` §2.3 identifies `chart_dashas` as L1's clock output, at `(chart_id, ayanamsha_id, system_id, level_n, start_iso)` grain; §3.10 records 42 columns, with partial population. These are observed inventory facts, not a promise that every optional cell is filled.
- Current table definition: `platform/migrations/_archive/135_chart_dashas.sql`; current row producer: `platform/python-sidecar/ga_writers/ga_dashas_writer.py` (`_jd_to_iso_utc`, row construction, `KP_SYSTEM_ID` and `compute_kp_subperiods`); current pinned Gochara reader: `platform/python-sidecar/services/gochara_kernel/dasha_read.py` and `services/gochara_grammar/dasha_data.py`. They establish the present behavior, not Suvarṇa's future commitment. The producer's V-12 correction gives KP rows `system_id = 'vimshottari_kp'`; a past producer put them under `vimshottari` and caused a real level-2/3 collision.
- The producer also writes a `system_id = 'scope_cap'`, `ayanamsha_id = 'INVARIANT'` marker for the excluded KP depth. Its start and end instants are equal, so it is a capability sentinel, not a period. The fifth Prāṇa level is recorded as a `chart_facts` capability fact, not a `chart_dashas` interval (`ga_dashas_writer.py`, `write_dasha_scope_cap_sentinels`).
- The writer's `stabilize_hierarchical_uuids` post-pass replaces the temporary UUID4 period ids with semantic UUID5 ids and rewires parent links before persistence (`ga_dashas_writer.py`, after verification and before DB write). Its identity includes `start_iso` and `end_iso`: a changed boundary can change `dasha_row_id` even for the same chart and named system. The available coordination log's 2026-10-07 Exec Suvarṇa notice says the forthcoming L1 pass rebuilds `ga_dashas`, changes `build_id`, and requires a deliberate `DASHA_READ_CONTRACT` re-pin. No K0-SV contract acknowledgement was found in the locally available `origin/campaign-coordination` copy. Recheck that branch when local-only mode ends.

## Proposed read surface

All rows are selected from `public.chart_dashas` for one chart, one `ayanamsha_id`, one `system_id`, one `build_id`, and an explicitly accepted `verification_pass_status`. Every field below is an existing column. “Required” means the F2 reader refuses a row missing it; it is not a claim that today's whole table satisfies the rule.

| column | proposed meaning for Kāla | read use |
|---|---|---|
| `chart_id`, `ayanamsha_id`, `system_id`, `build_id` | Exact chart, sidereal convention, named daśā construction, and one L1 build; `chara` and `chara_karaka` are not aliases. Classical `vimshottari` and its KP subdivision namespace `vimshottari_kp` are distinct stored systems. | Required selection and lineage. A mixed or null build is a conflict, not a row-order choice. A classical read selects `vimshottari`; a KP read, if supported, explicitly selects `vimshottari_kp`. |
| `dasha_row_id`, `parent_row_id`, `level_n` | Period identity, direct parent identity, and hierarchy depth. Levels 1–4 are MD, AD, PD, sūkṣma; level 5 is not persisted. | Required identity and ancestry. A classical non-root parent resolves in the same system and pinned build. A KP `sub` row currently points to a classical Vimśottarī MD; a KP `sub_sub` row points to its KP `sub` parent. Both must resolve under the same chart, ayanāṃśa and build, even across those two system namespaces. |
| `lord_graha` | The L1-computed period lord, without a Kāla recomputation. | Required period context and attachment key. |
| `start_iso`, `end_iso` | Full-precision UTC instants bounding a period. | Required F2 active-at-time and boundary calculation; use half-open `[start_iso, end_iso)`. At an exact end, the old period is inactive. |
| `start_date`, `end_date` | Date projections of the period bounds; precision is lower than the ISO instants. | Display or coarse date filters only; never replace the ISO fields for an instant-level clock. |
| `verification_pass_status` | The row's actual L1 verification tier. | Required tier predicate and disclosed provenance. No blank, null or divergent row is silently promoted. |
| `applies_to_this_chart_flag` | Producer's applicability assessment, where populated. | Input to system applicability; null stays unknown, not true. |
| `sandhi_flag`, `next_dasha_start_iso` | Producer's junction annotation and next boundary, where populated. | Optional annotations; F2's own band and uncertainty calculation must state its rule and cannot infer a filled value from null. |
| `is_truncated_at_window_start`, `is_truncated_at_window_end` | Producer's indication that a period is clipped by the calculation window. | Coverage and boundary precision; a clipped edge must not be presented as the natural period edge. |
| `kp_sublevel`, `kp_sub_lord`, `kp_sub_sub_lord` | KP subdivisions of Vimśottarī, stored under `vimshottari_kp` with `kp_sublevel = 'sub'` or `'sub_sub'`; they are not a second independent clock. | A classical `vimshottari` hierarchy does not absorb KP rows. An explicit KP read retains the sublevel and its own applicability and tier; it cannot supply an extra independent-system vote. |

F2's minimal clock projection is the identity and pin fields, `lord_graha`, the ISO bounds, tier, and applicability/coverage state. Other `chart_dashas` fields, including natal-lord condition, `duration_days`, citation and concurrent-system annotations, are outside this proposed F2 read surface. An item that needs another column must amend this contract and record the reason; it must not silently read it. `ka_avadhi` may require a separate attachment contract for natal condition.

## Verification tiers at the current producer boundary

These are observations from `ga_dashas_writer.py`'s `_apply_vimshottari_independent_verification` and `build_system` verification loop, and `brahmagyan/verification_vocab.py`'s `UNVERIFIED_DEFAULT = 'single'`. They describe the code in this checkout, not a Suvarṇa guarantee for a later build.

| stored row group | current verification behavior | proposed F2 consequence until Suvarṇa confirms a policy |
|---|---|---|
| Classical `vimshottari`, levels 1–4, without a KP sublevel | An independent period tree is compared row by row; each row keeps its own `two_pass_verified` or `divergent_flagged` result. A chart-wide verdict is not broadcast over the tree. | Accept only a row whose own tier satisfies the explicit read policy. A divergent child cannot inherit a verified parent's tier. |
| `vimshottari_kp` sub and sub-sub rows | The classical independent verifier does not examine this different decomposition; the fallback stamps `single`. | Do not count a classical MD's two-pass tier as verification of its KP child. A KP clock requires a separately accepted tier and parent policy. |
| Other stored systems | Their existing verification functions examine level 1 rows; unexamined deeper rows receive `single`. The level 1 result depends on the system and chart. | Do not infer that level 2–4 rows share the level 1 tier. Suvarṇa must name the accepted system-and-level tier matrix before F2 serves them. |

For an F2 lookup, the tier predicate applies to the **selected row and every required ancestor** under the policy for each row's own system and level. A missing accepted ancestor, a `divergent_flagged` row, or a KP child whose tier policy is still undecided yields a typed unavailable result; none is replaced by a nearby or lower-tier interval. The current Gochara 5.0 reader's frozen `two_pass_verified` Vimśottarī policy is separate and remains unchanged. Suvarṇa must confirm whether this proposed ancestor rule and each non-classical tier policy are compatible with its settled output.

## Proposed period and build rules for Suvarṇa to confirm

1. L1 owns calculation and period identity. Its stored hierarchy has levels 1–4; `parent_row_id` links each child to its actual parent. A child interval must lie within that parent's interval. Periods at one system/level/parent do not overlap, and an active-at-time lookup uses the half-open ISO interval. Kāla does not reconstruct the daśā calculation or turn a date-only bound into a timestamp. The `system_id` predicate precedes any level-2/3 hierarchy walk: `vimshottari_kp` rows cannot be folded into the classical `vimshottari` MD/AD/PD sequence. An explicit KP ancestry check includes the classical MD parent by ID under the same build, without counting it twice as a KP period. Suvarṇa must confirm the KP parent and tier rules separately before Kāla offers that read.
2. L1's 1950-01-01 through 2100-12-31 calculation window may clip a natural period. The truncation flags must distinguish that case. Empty coverage, an inapplicable system, an unverified tier, and a broken hierarchy are separate outcomes; none becomes a fabricated period.
   The `scope_cap` sentinel must be excluded before any active-period, boundary or overlap calculation. Its zero-length interval does not establish clock coverage or satisfy an absent period. A request for excluded depth returns a typed scope-cap or unavailable result sourced from the relevant capability marker.
3. L1 publishes a coherent build identity after its rebuild. Kāla pins the `build_id` from the settled L1 receipt for the chart and checks it across every row in the chosen system and ayanāṃśa, including tiers it will not consume. A mixed build is refused. The existing Gochara 5.0 frozen pin (`75524b3e-102a-43ec-8cee-3f57fee752c3` for canonical Vimśottarī) remains in force until the governed re-pin after the L1 rebuild; this draft does not override it.
4. The baseline read tier is `two_pass_verified` for the frozen Gochara §4.0 Vimśottarī read. Other system/level tiers require an explicit, source-backed acceptance policy; an honest lower tier remains labelled as such and never masquerades as two-pass. Suvarṇa should state which tiers and system/level combinations its settled build guarantees. Kāla's F2 must expose a typed unavailable/unknown result where the accepted tier has no row.
5. Persisted row IDs are deterministic for the writer's semantic identity, which includes both ISO bounds. Kāla pins the build as well as the row ID: a changed bound can yield a different ID, while an unchanged ID does not establish equal verification tier or a settled new build. The coordination notice says `build_id` changes on the upcoming rebuild, so the read contract needs a deliberate re-pin after that build is accepted.

## Proposed F2 lookup cases for contract review

These cases make the period-cutting and null rules testable after Suvarṇa confirms the contract. They specify reader behavior, not an assertion that the current L1 rows pass every case. `t` is a UTC instant and `A` and `B` are otherwise eligible rows under one pinned chart, ayanāṃśa, system and build.

| source rows and request | proposed F2 result | failure this case must catch |
|---|---|---|
| `A = [t0,t1)`, `B = [t1,t2)`, lookup at `t1` | `B` only | End-inclusive lookup retaining `A` at the shared boundary. |
| `A = [t0,t1)`, `B = [t2,t3)` with `t1 < t < t2` | Typed `coverage_gap`, with no active period | Substituting the nearest interval or a date-only projection. |
| Two eligible rows at the requested level and parent both contain `t` | Typed `ambiguous_period`; reject both | Row order or `LIMIT 1` silently choosing an answer. |
| A selected child has an absent, different-build, or unaccepted-tier required ancestor | Typed `hierarchy_unavailable`; no partial period chain | Borrowing a parent from a prior build or inheriting its tier. |
| The only matching row is `scope_cap`, or the selected row's relevant boundary is window-truncated | Excluded depth gives typed `scope_cap`; a clipped edge carries `boundary_truncated` and cannot be called a natural transition | Treating a sentinel or the calculation-window edge as a witnessed daśā change. |

The failure labels here are proposed F2 outcomes; Suvarṇa's acknowledgement must settle the source guarantees that make each case decidable. Kāla's later implementation may map the labels into its governed closed vocabulary, but it must preserve the distinctions.

## Acknowledgement gate

Suvarṇa must confirm or correct the read-set, each field's meaning and nullability, half-open period cutting, hierarchy/coverage rules, accepted tiers by system and level, and the settled-build identity/re-pin procedure. Record the exact acknowledgement line and coordination commit here only after it exists. Until then, this file remains `LOCAL_DRAFT`; K0-SV is not done, and no Suvarṇa agreement is asserted.
