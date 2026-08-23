# M0-T75 Report — Asset-ID Lineage Manifest (D-103)

**Agent:** KARAKA-M0-T75
**Authority:** D-103 (ADHIKĀRIN), closing PARIKSAKA V-67 / F-V67-1
**Branch:** campaign/nirmana-autonomous
**Status:** COMPLETE — not self-certified (I16/H7); PARIKSAKA verifies.

## What this closes

PARIKSAKA's V-67 found `build_run_assets` carries 4 asset_ids absent from `asset_registry`,
which risked the D-94/x06() unearned-lit ratchet either (a) never seeing evidence recorded
under a pre-rename id, or (b) treating stray non-asset ids as if they were real. D-103 required
a committed, queryable, DERIVED (not hand-guessed) lineage manifest resolving all 4 to a
determined disposition, plus an explicit anchor declaration on x06() itself.

## Files touched

- **`platform/scripts/governance/asset_id_lineage_manifest.json`** (new) — the manifest.
  Not a schema change (D-103 part 5); follows the existing pattern of
  `unearned_lit_floor.json` / `entrypoint_guard_floor.json` /
  `asset_catalogue_disclosed_residuals.json` in the same directory.
- **`platform/scripts/governance/check_asset_catalogue_contract.py`** — x06()'s doc-comment
  only. Added an explicit "ANCHOR DECLARATION" paragraph per D-103 part 6, plus the four
  known-affected ids as named, itemised exceptions. No behavior change (verified: `--live
  --json` still reports `growth: []`, 32/32, identical to before the edit).

## Dispositions established (full evidence trail is in the manifest; summarized here)

| asset_id | disposition | evidence basis |
|---|---|---|
| `ga_pyjhora_engine` | **DELETED** by migration 342 | migration text (`342_retire_ga_pyjhora_engine.sql`); confirmed absent from live `asset_registry` |
| `ka_gochara_v2_materialize` | **RENAMED** to `ka_gochara` by migration 563 | migration text (`563_utkarsha_w64_asset_rename.sql`); confirmed `ka_gochara` exists live, old id does not |
| `chart_dashas` | **legacy_never_registered** | no migration ever inserted this as an asset_id (full grep, zero hits); it is the *target_table* of the real id `ga_dashas` (migration 217); live `build_runs` rows show all 3 `build_run_assets` entries came from one operator's 2026-06-26 E2E test session on chart `1c826d5a` (same principal, same day, `chart_dashas` sitting in the run's own `plan` array) |
| `ga_chart_service` | **legacy_never_registered** (genuinely live service, by design never carried in `asset_registry`) | no migration ever registered it; live query of all 8 `asset_kind='service'` rows today contains no match under any name; `L1_GANITA_CLOSURE_v1_0.md` (SUPERSEDED) listed it in a 10-row table, but `_v2_0.md` (CURRENT)'s 15-asset picture drops it; `RETRIEVAL_STRATEGY_v1_0.md §5.3` (native ruling, 2026-07-19) names it explicitly as a "service asset" — real-time computation that "cannot carry a build_id," a category doctrine deliberately keeps outside `asset_registry`; its one `build_run_assets` row traces to the same 2026-06-26 operator session as `chart_dashas` |

**None marked UNRESOLVED.** Both `chart_dashas` and `ga_chart_service` — the two ADHIKĀRIN
flagged as having no determined disposition — now have one, each backed by a migration grep
(negative result, itself evidence), a live read-only DB query, and (for `ga_chart_service`
specifically, per ADHIKĀRIN's explicit instruction to verify it isn't running under another
registry identity) a check of every current `asset_kind='service'` row plus the doctrine
artifact that names it by name as a deliberately-unregistered live service.

One finding worth flagging explicitly: the 4 `build_run_assets` rows behind `chart_dashas` and
the 1 behind `ga_chart_service` are not independent incidents. Reading the parent `build_runs`
rows (read-only) showed all 4 came from **one operator's single E2E test session** on
2026-06-26 against chart `1c826d5a` (Abhinandan Mohanty, the Phase-E operator-E2E chart),
same triggered_by principal, within a few hours of each other — consistent with someone
following `L1_GANITA_CLOSURE_v1_0.md`'s asset table (which listed `ga_chart_service` and used
`chart_dashas` as a highly visible table name) and submitting builds by a name that was never
actually a registered `asset_registry.asset_id`.

## x06() anchor declaration (D-103 part 6)

Added to the function's doc-comment, verbatim in spirit with D-103: x06() anchors on
`asset_registry` (via `s.assets`) and never on `build_run_assets` directly; `build_run_assets`
is consulted only to test membership for ids ALREADY in `asset_registry`. The four
known-affected ids are named inline (not silently absorbed into any count), with a pointer to
the manifest for full evidence.

## Rename-resolution (D-103 part 5) — considered, not implemented

D-103 part 5 asks whether x06() (or another rule) should READ the manifest to resolve renamed
ids (crediting `ka_gochara_v2_materialize`'s completed builds to `ka_gochara`). I considered
this and did **not** implement it. Reasoning (also recorded in the manifest's
`not_yet_wired_for_resolution` field):

- x06()'s `ran` set is built as `{r["asset_id"] for r in build_run_assets if state=='complete'}`
  and tested by literal string membership against the CURRENT registry id. Making it
  rename-aware means loading the manifest, unioning old-id evidence into the new id's
  membership test, and reasoning about whether the old id could ever coexist with the new one
  in a snapshot — more than a one-line change to a function whose doc-comment already carries
  five ADHIKĀRIN rulings' worth of accumulated invariants (D-42, D-87, D-94, D-95, D-84).
- Given the explicit instruction to stop and report rather than restructure x06()'s core logic
  if the fix isn't small and clearly-scoped, I filed it as a **follow-up recommendation**
  instead: a scoped task that (1) loads the manifest, (2) for each `renamed` entry adds the old
  id into the `ran`-membership lookup for the new id specifically, and (3) adds a fixture
  proving `ka_gochara`'s completed `ka_gochara_v2_materialize` builds now clear it. This is a
  live (not silent) gap — the doc-comment and the manifest both say so — but `ka_gochara` is
  not currently flagged unearned-lit by the live guard run either way (confirmed: `growth: []`
  today), so nothing is silently wrong in the current snapshot.

## Constraints honored

- I13/I14: read-only SELECTs against the live DB throughout (`build_run_assets`, `build_runs`,
  `asset_registry`, `information_schema.columns`); zero writes to any asset-data table; no
  migration authored or applied.
- Not a schema change: the manifest is a committed JSON file, same directory/pattern as the
  existing floor/residual files. No DB table or column added.
- Did not touch Wave 2, the entrypoint guard, or M0-T73/T74's files.
- Every disposition traces to a cited migration file, a live read-only query result, or a
  named doctrine/closure artifact — none hand-guessed.

## What I did NOT do

- Did not certify this work (I16/H7) — PARIKSAKA verifies.
- Did not wire rename-resolution into x06() (see above — recommended as follow-up, not built).
- Did not touch `unearned_lit_floor.json`, `entrypoint_guard_floor.json`, or
  `asset_catalogue_disclosed_residuals.json`.
