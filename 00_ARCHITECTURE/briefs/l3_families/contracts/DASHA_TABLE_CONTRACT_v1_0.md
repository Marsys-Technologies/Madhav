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
- Current table definition: `platform/migrations/_archive/135_chart_dashas.sql`; current row producer: `platform/python-sidecar/ga_writers/ga_dashas_writer.py` (`_jd_to_iso_utc`, row construction, KP subdivision); current pinned Gochara reader: `platform/python-sidecar/services/gochara_kernel/dasha_read.py` and `services/gochara_grammar/dasha_data.py`. They establish the present behavior, not Suvarṇa's future commitment.
- The available coordination log's 2026-10-07 Exec Suvarṇa notice says the forthcoming L1 pass rebuilds `ga_dashas`, changes `build_id`, and requires a deliberate `DASHA_READ_CONTRACT` re-pin. No K0-SV contract acknowledgement was found in the locally available `origin/campaign-coordination` copy. Recheck that branch when local-only mode ends.

## Proposed read surface

All rows are selected from `public.chart_dashas` for one chart, one `ayanamsha_id`, one `system_id`, one `build_id`, and an explicitly accepted `verification_pass_status`. Every field below is an existing column. “Required” means the F2 reader refuses a row missing it; it is not a claim that today's whole table satisfies the rule.

| column | proposed meaning for Kāla | read use |
|---|---|---|
| `chart_id`, `ayanamsha_id`, `system_id`, `build_id` | Exact chart, sidereal convention, named daśā construction, and one L1 build; `chara` and `chara_karaka` are not aliases. | Required selection and lineage. A mixed or null build is a conflict, not a row-order choice. |
| `dasha_row_id`, `parent_row_id`, `level_n` | Period identity, direct parent identity, and hierarchy depth. Levels 1–4 are MD, AD, PD, sūkṣma; level 5 is not persisted. | Required identity and ancestry; a non-root parent must resolve within the same pinned read. |
| `lord_graha` | The L1-computed period lord, without a Kāla recomputation. | Required period context and attachment key. |
| `start_iso`, `end_iso` | Full-precision UTC instants bounding a period. | Required F2 active-at-time and boundary calculation; use half-open `[start_iso, end_iso)`. At an exact end, the old period is inactive. |
| `start_date`, `end_date` | Date projections of the period bounds; precision is lower than the ISO instants. | Display or coarse date filters only; never replace the ISO fields for an instant-level clock. |
| `verification_pass_status` | The row's actual L1 verification tier. | Required tier predicate and disclosed provenance. No blank, null or divergent row is silently promoted. |
| `applies_to_this_chart_flag` | Producer's applicability assessment, where populated. | Input to system applicability; null stays unknown, not true. |
| `sandhi_flag`, `next_dasha_start_iso` | Producer's junction annotation and next boundary, where populated. | Optional annotations; F2's own band and uncertainty calculation must state its rule and cannot infer a filled value from null. |
| `is_truncated_at_window_start`, `is_truncated_at_window_end` | Producer's indication that a period is clipped by the calculation window. | Coverage and boundary precision; a clipped edge must not be presented as the natural period edge. |
| `kp_sublevel`, `kp_sub_lord`, `kp_sub_sub_lord` | KP subdivisions of Vimśottarī, not a separate independent clock. | Keep the KP dimension explicit; do not count it as a second independent system. |

F2's minimal clock projection is the identity and pin fields, `lord_graha`, the ISO bounds, tier, and applicability/coverage state. Other `chart_dashas` fields, including natal-lord condition, `duration_days`, citation and concurrent-system annotations, are outside this proposed F2 read surface. An item that needs another column must amend this contract and record the reason; it must not silently read it. `ka_avadhi` may require a separate attachment contract for natal condition.

## Proposed period and build rules for Suvarṇa to confirm

1. L1 owns calculation and period identity. Its stored hierarchy has levels 1–4; `parent_row_id` links each child to its actual parent. A child interval must lie within that parent's interval. Periods at one system/level/parent do not overlap, and an active-at-time lookup uses the half-open ISO interval. Kāla does not reconstruct the daśā calculation or turn a date-only bound into a timestamp.
2. L1's 1950-01-01 through 2100-12-31 calculation window may clip a natural period. The truncation flags must distinguish that case. Empty coverage, an inapplicable system, an unverified tier, and a broken hierarchy are separate outcomes; none becomes a fabricated period.
3. L1 publishes a coherent build identity after its rebuild. Kāla pins the `build_id` from the settled L1 receipt for the chart and checks it across every row in the chosen system and ayanāṃśa, including tiers it will not consume. A mixed build is refused. The existing Gochara 5.0 frozen pin (`75524b3e-102a-43ec-8cee-3f57fee752c3` for canonical Vimśottarī) remains in force until the governed re-pin after the L1 rebuild; this draft does not override it.
4. The baseline read tier is `two_pass_verified` for the frozen Gochara §4.0 Vimśottarī read. Other system/level tiers require an explicit, source-backed acceptance policy; an honest lower tier remains labelled as such and never masquerades as two-pass. Suvarṇa should state which tiers and system/level combinations its settled build guarantees. Kāla's F2 must expose a typed unavailable/unknown result where the accepted tier has no row.
5. Row IDs may be deterministic across a rebuild, but Kāla pins the build as well as the row ID. The coordination notice says IDs are already UUID5 and `build_id` changes on the upcoming rebuild; stable IDs alone do not prove that old and new rows have equal boundaries or tiers.

## Acknowledgement gate

Suvarṇa must confirm or correct the read-set, each field's meaning and nullability, half-open period cutting, hierarchy/coverage rules, accepted tiers by system and level, and the settled-build identity/re-pin procedure. Record the exact acknowledgement line and coordination commit here only after it exists. Until then, this file remains `LOCAL_DRAFT`; K0-SV is not done, and no Suvarṇa agreement is asserted.
