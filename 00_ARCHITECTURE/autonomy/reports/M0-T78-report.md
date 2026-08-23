# M0-T78 Report — Lineage-Manifest Completeness Assertion (D-111)

**Agent:** KARAKA-M0-T78
**Authority:** D-111 (ADHIKĀRIN), closing PARIKṢAKA V-70 / F-V70-2
**Branch:** campaign/nirmana-autonomous
**Status:** COMPLETE — not self-certified (I16/H7); PARIKṢAKA verifies.

## What this closes

PARIKṢAKA's F-V70-2 found that `platform/scripts/governance/asset_id_lineage_manifest.json`
(built by M0-T75 under D-103, recording the disposition of the 4 `build_run_assets` asset_ids
absent from `asset_registry`) is read by **nothing**. `x06()` anchors on `asset_registry` by
design and structurally cannot see an orphan id; no other rule compared the two id sets. D-111
ruled the defect was in D-103 itself — "I ordered an artifact and ordered nothing to read it" —
and authorised the fix: a completeness assertion between the live orphan population and the
manifest's enumerated set, naming any mismatch in either direction.

D-111 also corrected the shape before it could be built wrong: every other assertion this
campaign shipped today (entrypoint allowlist, X-06's unearned-lit floor) is **shrink-only**,
because those are allowlists (amnesty for a defect). The manifest is **not** an allowlist — it
is a record, and a record's job is to grow. Building this as a frozen-population/shrink-only
ratchet would have been backwards: it would block the very renames the manifest exists to
document. **The invariant is completeness (an orphan must always have a determined
disposition), not monotonicity (the manifest may have any number of rows).**

## What was built

**`platform/scripts/governance/check_asset_catalogue_contract.py`** — new rule `X-07`
(`EXTENSION_RULES`, BLOCKING severity), following the file's own established X-rule pattern
(`Rule(...)`, `verdict()`, doc-comment carrying the authorising decision, a dedicated
in-process probe called from `self_test()`):

```
{ids in build_run_assets absent from asset_registry} == manifest's enumerated id set
```

Violations are reported by name, in both directions:
- `orphan_missing_from_manifest` — a live orphan the manifest does not record.
- `manifest_entry_not_a_live_orphan` — a manifest entry whose id is no longer (or never
  was) a live orphan.

**Why BLOCKING, and why FAIL rather than NOT_CHECKABLE when the manifest file is entirely
absent:** D-111 part 3 calls the failure mode "UNDETERMINED-AND-FATAL, not forbidden." A
`NOT_CHECKABLE` verdict never gates (confirmed by reading `summarise()`) — it would have made
"no manifest was ever written" behave exactly like today's silent gap, the opposite of the
fix. So `x07()` treats a missing manifest file as an **empty record** (an orphan population
compared against `∅`), not as unmeasurable input, and reports `FAIL` naming every orphan as
undocumented. `NOT_CHECKABLE` is reserved for genuine data absence: no `build_run_assets`
evidence in the snapshot at all, or a manifest file that exists but fails to parse
(corruption, distinguished from omission).

**Why a new snapshot key was needed (`build_run_asset_ids_all`):** X-06's existing
`build_run_assets` snapshot key is deliberately scoped by `read_live()` to
`WHERE state='complete'` — X-06 only needs to know a build *succeeded*. But
`ga_pyjhora_engine` (one of the 4 known orphans) has **10 `build_run_assets` rows, states
`{aborted, error}`, zero `complete`** — it would be invisible to a rule that reused X-06's key.
`read_live()` gained one additional read-only query:

```sql
SELECT DISTINCT asset_id FROM build_run_assets ORDER BY asset_id
```

stored under a new key, `build_run_asset_ids_all`, kept strictly separate from X-06's
`build_run_assets` key so X-06's semantics are untouched. `X-07` reads only the new key.
The module's "ROW SOURCES" doc-comment shape block was updated to document both keys.

Everything else in the file — `x06()`, `m0_exit_scorecard.py`, the entrypoint guard, Wave 2,
and every rule/fixture from M0-T71/T75/T76/T77 — is untouched. `git diff --stat` is pure
addition: **+258/-0**, one file.

## Both directions proven, plus the real historical case (constraint #6)

A dedicated `x07_manifest_completeness_probe()` (mirroring `x06_ratchet_probe`'s discipline,
called from `self_test()`, so it runs — and must pass — on every `--self-test` invocation, not
just as a report claim) proves 7 cases in-process:

1. **The real historical moment, reproduced exactly.** No manifest file at all (the state
   before M0-T75/D-103 ever ran) + the 4 real orphan ids PARIKṢAKA found by hand
   (`ga_pyjhora_engine`, `ka_gochara_v2_materialize`, `chart_dashas`, `ga_chart_service`) →
   **`FAIL`, all 4 named** under `orphan_missing_from_manifest`. This is the constraint-#6
   requirement: the assertion would have caught the gap this task exists to close, at the
   exact moment it existed.
2. Manifest present and complete for those 4 → **clean/`PASS`** (synthetic mirror of today).
3. **Direction 1** — a 5th orphan (`ph_new_undocumented_rename`) appears with no manifest
   entry → **`FAIL`, naming only the new id**.
4. **Direction 2** — the manifest carries an entry (`mi_stale_manifest_only`) for an id that
   is not a live orphan → **`FAIL`, naming only the stale entry**.
5. Manifest restored to correct → clean again (no state bleed).
6. No `build_run_asset_ids_all` key in the snapshot at all → `NOT_CHECKABLE`, never a silent
   pass.
7. Manifest file exists but is not parseable JSON → `NOT_CHECKABLE`, explicitly distinguished
   from case 1's "absent" (which is `FAIL`, not `NOT_CHECKABLE`).

All 7 print `[OK  ]` in the current `--self-test` run (see Verification below).

D-77/PARK-9: every write in the probe lands in an isolated `tempfile.TemporaryDirectory()`;
`LINEAGE_MANIFEST_PATH` is repointed there for the probe's duration and restored in `finally`
(asserted). The real `asset_id_lineage_manifest.json` and its 4 committed entries are never
opened for writing by this task, and no `git checkout` was used anywhere.

## Real, current state confirmed clean (case c) — read-only `--live` run

Requirement (c) — "the real, current state (4 real orphans, 4 manifest entries, matching) →
clean/green" — needs the actual database, which `--self-test` is deliberately DB-free by
design and cannot exercise. Verified instead with a direct, read-only `--live` invocation
(I13/I14: `SELECT` only, no write, no migration):

```
X-07 status: pass
detail: {'live_orphan_ids': ['chart_dashas', 'ga_chart_service', 'ga_pyjhora_engine',
          'ka_gochara_v2_materialize'],
         'manifest_ids': ['chart_dashas', 'ga_chart_service', 'ga_pyjhora_engine',
          'ka_gochara_v2_materialize'],
         'undocumented_orphans': [], 'stale_manifest_entries': []}
X-06 status: pass
summary.blocking_failures: []
```

The live orphan set and the manifest's enumerated set are identical, 4/4, today. No
regression to X-06 or any other rule — full `--live --json` summary shows the same
`blocking_failures: []` and the same set of pre-existing disclosed non-gating failures as
before this change.

## Verification

- `--self-test` **before** the change: exit 0 (baseline, not reproduced verbatim here since
  the change is purely additive and every prior fixture/probe result is unaffected — see
  "Everything else… untouched" above; the after-run below is the operative proof).
- `--self-test` **after** the change: exit 0. New probe section:
  `X-07 lineage-manifest-completeness probe (D-111: set equality, both directions, and the
  real pre-D-103 gap reproduced):` — all 7 cases `[OK  ]`. Contract cross-check still OK (28
  rules parsed, all implemented — `X-07` is correctly excluded from the cross-check as an
  extension rule, same as X-01…X-06). All 4 bundled fixtures still pass their `_expect`
  blocks unchanged (none of them assert on `X-06`/`X-07`, so the new rule reports
  `NOT_CHECKABLE` against them harmlessly — no `build_run_asset_ids_all` key in any bundled
  fixture).
- `--live --json` (read-only): exit 0, `X-07` reports `pass`, `X-06` unchanged `pass`, no new
  blocking failures anywhere.

## Where the rule lives, and why (shape justification)

Added to `EXTENSION_RULES` as `X-07`, not a numbered `C-*` contract rule: like X-01…X-06, this
assertion is a campaign-extension invariant (M0 exit-criteria class), not one of the 28 rules
`ASSET_CATALOGUE_CONTRACT_v1_0.md §6` enumerates, so it is correctly excluded from the
guard-vs-contract cross-check the same way X-01…X-06 already are. It sits immediately after
`x06()` in the file (both reason about `build_run_assets` and orphan/coverage populations),
before the `X-01…X-05` block, and its probe sits immediately after `x06_ratchet_probe()`,
mirroring that function's structure line-for-line (helper `check()` closure, D-77 sandboxed
temp-dir pattern, `finally`-restored module global, final NOT_CHECKABLE/corruption checks
appended in the same style as X-06's structural AST check).

## Disclosed, not fixed (out of scope for this task)

- `m0_exit_scorecard.py` references `X-06` by name in prose/comments; it was explicitly named
  out of scope for this task and was not touched. `X-07` is not wired into it.
- The manifest's own `not_yet_wired_for_resolution` field (rename-credit for `ka_gochara`
  into X-06's "ran" set) remains exactly as M0-T75 left it — unrelated to this task's scope;
  X-07's set-equality check does not depend on that resolution either way, since it compares
  raw id membership, not build-evidence crediting.

Not self-certified (I16/H7) — PARIKṢAKA verifies.
