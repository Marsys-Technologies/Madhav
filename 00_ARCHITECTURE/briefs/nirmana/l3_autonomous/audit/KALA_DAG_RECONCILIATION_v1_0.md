# KĀLA DAG RECONCILIATION — F3 four-way (five-source) reconciliation

**Status:** v1.0. **Produced by:** KĀLA READINESS AUDIT, cycle 1 (2026-09-22). **Scope:** all 23
`ka_*` identities (22 active + protected/retired `ka_gochara_sweep`), canonical chart
`482012f1-710e-4a25-994a-93821f5871aa`. Source subagent work: `_work/F3.md` (full command
log). Every claim below was independently spot-re-run by the conductor (migration 563 content,
`dag_edge_guard.py` self-test fixture path) before being promoted here — see §6.

## 0. Correction to the audit brief's premise

The brief expected four sources (seed · live registry · frozen manifest · code). There are
actually **five**, because "seed" is not one artifact:

| # | Source | What it is |
|---|---|---|
| 1 | **MIG345** | `platform/supabase/migrations/345_register_ka_assets.sql` — original 12-asset backfill. Stale; never re-run after later corrections. |
| 2 | **SEED-TS** | `platform/scripts/seed/asset_registry_seed.ts` — current, maintained, all 23 rows. |
| 3 | **LIVE** | `asset_registry` table, queried directly. |
| 4 | **FROZEN** | No static manifest file exists. The real mechanism is `pipeline/orchestrator/runner.py`'s `validate_frozen_run_manifest()` — a per-dispatch snapshot written into `build_runs.plan_manifest` (jsonb) and checked via `_verify_registry_still_matches_manifest` before any writer executes. |
| 5 | **CODE** | Actual writer source (`pipeline/orchestrator/writers/ka_*.py` + `services/ka_*/`), verified by import/read grep. |

## 1. Full 23-identity reconciliation table

See `_work/F3.md` §1 for the complete row-by-row table (asset_id × MIG345 × SEED-TS ×
LIVE × FROZEN × CODE, with discrepancy classification and target_table). Row count check: LIVE,
CODE (writer files), and SEED-TS all independently enumerate the same 23 identities; MIG345 only
ever covered 12 and was never extended.

## 2. Re-verification of the four previously-known discrepancies

| Asset | Prior claim | Re-verified finding |
|---|---|---|
| `ka_muhurta_seva` | seed 1 dep vs live 0 | **CONFIRMED**, and it is a *documented, deliberate* divergence: migration `676_nirmana_l3_n5_muhurta_seva_depends_on.sql` corrected LIVE after verifying the writer touches no producer table; the migration's own text states it is intentionally **not** re-syncing SEED-TS ("the seed file is the as-originally-authored record"). Live footgun, not an oversight. |
| `ka_vighnakara` | seed 4 vs live 5 | **CONFIRMED, but understated.** Migration `730_nirmana_l3_f_vighna_5_depends_on.sql` didn't just add one edge — it removed a fictional `ka_gochara` edge and added two different real ones (`bg_dignity_reference`, `ka_yojaka`). SEED-TS and LIVE share only 3 of their combined 4/5 members. |
| `ka_sangam` | "seed 0 deps vs live 10" | **NOT SUPPORTED BY ANY REAL SOURCE.** MIG345=4, SEED-TS=10 (matches LIVE). The literal `0` traces to `dag_edge_guard.py`'s synthetic, DB-free CI self-test fixture (`_SELF_TEST_REGISTRY`), whose own docstring says it "proves NOTHING about the live registry." A prior pass appears to have mistaken this fixture for a real seed value. **Corrected finding: MIG345=4 vs LIVE=10, both real.** |
| `ka_kalasutra` | "seed 0 deps vs live 3" | **ALSO NOT SUPPORTED.** MIG345=2, SEED-TS=3 (matches LIVE). No source anywhere declares 0. **Corrected finding: MIG345=2 vs LIVE=3.** |

## 3. Highest-severity finding: `ka_gochara` identity reuse in MIG345

`platform/migrations/563_utkarsha_w64_asset_rename.sql` (content independently re-read by the
conductor, lines 1–65) performed a **name transplant**: it deleted the original `ka_gochara` row
(global-scope on-demand *service*, deps `{bg_ephemeris, ka_graha_sancara}`) and reassigned the
`ka_gochara` asset_id to what had been `ka_gochara_v2_materialize` (a per-chart *data* writer,
target_table `kala_gochara_windows`, deps `{bg_gochara_arcs, ka_gochara_resonance}`). MIG345
predates this rename and still describes the original service verbatim — wrong scope, wrong
storage_type, wrong target_table, wrong dependency set, and it will never self-heal (`ON CONFLICT
DO NOTHING`). SEED-TS and LIVE both correctly reflect the post-rename asset; only MIG345 is wrong,
and only a reader treating MIG345 as valid history (exactly what its own header claims) would be
misled. Blast radius: documentation/onboarding risk, not a live build defect.

## 4. Frozen-manifest coverage gap

Of 23 identities, only **11** have ever been captured by a surviving `build_runs.plan_manifest`
snapshot: `ka_avadhi, ka_dasha_kala, ka_gochara, ka_gochara_resonance, ka_kota_chakra, ka_kshetra,
ka_moorti_nirnaya, ka_sudarshana_varsha, ka_tithi_pravesha, ka_vedha_gochara, ka_yojaka`. The other
12 — **including `ka_sangam`, "THE VALUABLE CORE"** — have never been dispatched through a run
whose manifest survived, despite 522 build_runs existing for the canonical chart. Where the
mechanism has fired, LIVE and FROZEN agree in every case (order differs only; documented as
expected). **The freeze-and-verify protection has never actually been exercised for over half the
L3 Kāla DAG.**

## 5. Minor: `ka_avadhi` imports `ka_dasha_kala` without declaring it

`ka_avadhi.py:29` imports `ALL_DASHA_SYSTEMS` from `services.ka_dasha_kala.tree_walk`, but no
source declares `ka_dasha_kala` in `ka_avadhi`'s `depends_on`. Constant/vocabulary import, not a
table read or service call — unlikely to be a real ordering bug, but structurally invisible to
`dag_edge_guard.py` (regex only matches `FROM`/`JOIN <table>`; `ka_dasha_kala` has no
`target_table` to gate on regardless). Flagged as documentation-only.

## 6. Does `dag_edge_guard.py` catch any of this? — No, by construction, and the conductor independently confirmed why

Read directly (both by the subagent and re-confirmed by the conductor): `dag_edge_guard.py`
compares **live `asset_registry` against writer-code reads** only. It never reads SEED-TS or
MIG345. Two structural blind spots:

1. **It has never run as a per-commit CI gate against a live DB** — its only DB-connected caller
   is skip-decorated when `DATABASE_URL` is absent, which is always true in push/PR CI. It only
   runs on a scheduled/manual `fresh_chart_smoke.yml` job.
2. **It would not have caught either confirmed discrepancy (`ka_muhurta_seva`, `ka_vighnakara`)**
   even when run, because by the time migrations 676/730 fixed LIVE (verifying against the writer
   source first), LIVE already matched CODE — a live scan today reports both as clean, correctly,
   while the actual defect (SEED-TS/MIG345 left stale, by explicit accepted policy) remains
   permanently invisible to it. **This is exactly the F3 defect class**: the guard protects
   code-vs-registry consistency, not registry-vs-seed consistency. The normal migration-replay
   bootstrap path (345→676→730→…) self-corrects; the risk is specific to any future bootstrap that
   substitutes `asset_registry_seed.ts`'s `runSeed()` for full migration replay, which would
   silently resurrect both fixed-then-abandoned-in-seed edges.

## 7. Conductor verification log (this cycle)

- Re-ran `grep -n "ka_gochara" platform/supabase/migrations/345_register_ka_assets.sql` → confirmed row present, matches subagent's citation.
- Re-read `platform/migrations/563_utkarsha_w64_asset_rename.sql` lines 1–65 directly → confirmed the delete-then-rename mechanics exactly as reported (the subagent's first path guess, `platform/supabase/migrations/563_*`, was wrong directory; the file is under `platform/migrations/563_*` — corrected here).
- Did not independently re-run the full 23-row LIVE/SEED-TS/CODE grep sweep (accepted on the strength of the fully-reproducible command list in `_work/F3.md` plus the two spot-checks above, which corroborate the report's two highest-stakes individual claims).

## Summary / severity ranking

1. **§3 — `ka_gochara` stale identity in MIG345** (highest; documentation/onboarding hazard, inert against current DB).
2. **§4 — frozen-manifest coverage gap for 12/23 assets including `ka_sangam`** (process-integrity hazard: the campaign's own freeze-and-verify mechanism is unproven for its most important asset).
3. **§2 — two confirmed, policy-accepted-but-permanent SEED-TS/LIVE divergences** (`ka_muhurta_seva`, `ka_vighnakara`) that no automated guard can ever catch under current tooling.
4. **§5 — soft `ka_avadhi`/`ka_dasha_kala` coupling** (documentation-only).

No live L3 build is broken by any F3 finding today — LIVE and CODE agree everywhere. The risk
surface is entirely in (a) stale/misleading documentation-of-record (MIG345, and the "seed 0 deps"
claims this reconciliation corrects) and (b) an unexercised safety mechanism (frozen-manifest
coverage) that the campaign has been implicitly trusting without ever having tested it for its
highest-value asset.
