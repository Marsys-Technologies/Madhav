---
title: PARIŚEṢA-V4 GA-3 Execution Packet — canonical-chart rebuild for F-104 / F-116 / F-63 / F-71 / F-35
version: 1.0
status: CURRENT
date: 2026-08-21
authority: GA-3 protected-data execution, v1.1 §19.2 packet discipline
chart_id: 482012f1-710e-4a25-994a-93821f5871aa (native's canonical chart)
---

## §0 — Scope determination: THREE packets, not one

The five findings do **not** share one rebuild. Verified against `asset_registry.depends_on`
(the DB `text[]` column that is the actual DAG definition — not a Python dict, not YAML) and the
downstream-stale-cascade code at `platform/python-sidecar/pipeline/orchestrator/asset_runner.py:713-722`.

| Finding | Asset needing re-run | Layer | Downstream closure (assets flipped `lit`→`stale`) |
|---|---|---|---|
| F-35 | `mi_sambandha` → then `mi_darshana` | L5 | 1 (`mi_darshana`, which this packet rebuilds anyway) |
| F-104 | `mi_darshana` | L5 | 0 (leaf) |
| F-71 | `mi_bhara` | L5 | 0 (leaf) |
| F-116 | `bo_upaya` | **L2** | **17** |
| F-63 | `ga_panchanga` | **L1** | **53** |

Three distinct blast radii ⇒ three packets.

- **Packet A — L5 trio** (F-35 chart-scoped, F-104, F-71): **EXECUTE**
- **Packet B — L2 `bo_upaya`** (F-116): **EXECUTE**, cascade disclosed + reversible
- **Packet C — L1 `ga_panchanga`** (F-63): **PARKED** — see §5

### §0.1 — Ordering constraint discovered mid-execution (must precede A)

`bo_upaya`'s recursive downstream closure **contains all three Packet A assets**
(`mi_sambandha`, `mi_darshana`, `mi_bhara` — verified by recursive query on `depends_on`).
Running B after A would flip A's freshly-earned `lit` back to `stale`. Correct order is
**B before A**, or A re-run after B. Execution log in §8 records the actual sequence taken.

### §0.2 — `action` semantics (defect found in the first dispatch)

`action='build'` builds only `dormant | error | incomplete` assets — an already-`lit` asset is
**silently skipped**, both in the TS planner (`plan.ts` `resolveBuildPlan`) and in the Python
scheduler (`runner.py:487-493`, `skip <asset> (already lit)`). Re-running a `lit` asset to pick up
a code fix therefore requires **`action='rebuild'`**. The first Packet A dispatch used
`action='build'` and correctly ran only `mi_bhara` (state `error`); `mi_sambandha`/`mi_darshana`
were skipped. This is recorded rather than hidden — it is exactly the "the mechanism reported
success while doing nothing" defect class (§N.8) and would have produced a false "rebuild done"
claim had the job logs not been read.

## §1 — Quiescence proof (§19.2 clause 1)

Measured 2026-08-21 ~02:10Z against production `amjis` via cloud-sql-proxy :5433.

- `pg_stat_activity` (datname=amjis, excluding self): **1 row**, `amjis_app`, state `idle`,
  last query `SELECT filename, sha256, sql_identity FROM _migrations_applied` — a deploy-time
  migration reader, no open transaction (`xact_start` NULL).
- `pg_locks` excluding `AccessShareLock`, excluding self: **0 rows**.
- `asset_throughput WHERE state IN ('building','running','pending','queued')`: **0 rows** (all charts).
- `build_runs WHERE state IN ('planned','running','paused')`: **0 rows**.

⇒ Zero concurrent writers. Additionally, the orchestrator itself takes
`pg_try_advisory_lock(hashtext(chart_id))` (`runner.py:764`) and exits 3 if the chart is locked,
so a race arriving after this measurement is refused rather than interleaved.

## §2 — Code-provenance gate (precondition, not a §19.2 clause — but the packet is worthless without it)

A rebuild only helps if the *executing image* carries the fixes. Verified as an earned signal
(§N.8), by grepping the exact deployed tree — not by inferring from a deploy timestamp:

- Cloud Run job `brahma-build-pipeline-job` image tag:
  `asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:bb5c5278b5adeb1e3e9761bc1655986a0a04e177`
- `git show bb5c5278b:<path>` confirms, in the deployed commit's tree:
  - `writers/mi_darshana.py` — 6× `not_assessed` present (F-104)
  - `writers/mi_sambandha.py` — `scored_count` tracking + `"empirical" if scored >= 5` (F-35)
  - `writers/bo_upaya.py:987` — `_strip_conditional_preamble`, `:1375` `"preamble_stripped"` (F-116)
  - `ga_writers/ga_panchanga_writer.py:1060` — `yoga_dict.get("yoga")` (F-63)
  - `services/mi_bhara/db.py:181` — `AND NOT isempty(observation_window)` (F-71)
- `git merge-base --is-ancestor` confirms `44d5ff5a7` and `f003bf3af` are ancestors of `bb5c5278b`.
  (`355be01df` is the *pre-squash* F-35 commit; it reaches production via the squashed `f003bf3af`.)
- Migration 573 (`scored_count` column on `mimamsa_manifestation_grammar`) verified **applied** in
  production via `information_schema.columns`. F-35's write path will not fail on a missing column.

## §3 — Before-images (§19.2 clause 2)

Full-fidelity `SELECT *` CSV snapshots (every column, every row), captured 2026-08-21 02:10Z into
`verification_artifacts/PARISESA_V4_GA3_REBUILD_20260821/`:

| File | Rows | Covers |
|---|---|---|
| `BEFORE_mimamsa_insight_units.csv` | 115 | F-104 / F-35 (`mi_darshana` output) |
| `BEFORE_mimamsa_manifestation_grammar.csv` | 24 | F-35 (`mi_sambandha` output) |
| `BEFORE_bodha_rm_remedy_prescriptions.csv` | 135 | F-116 (`bo_upaya` output) |
| `BEFORE_chart_facts_panchanga.csv` | 221 | F-63 (`ga_panchanga` output) |
| `BEFORE_mimamsa_predictions.csv` | 139 | F-71 read-side |
| `BEFORE_asset_throughput.csv` | 104 | all cascade state, all assets on this chart |

`asset_throughput` is snapshotted in full precisely so any `lit`→`stale` cascade is reversible.

## §4 — Tested rollback (§19.2 clause 3) — REHEARSED, not described

Rehearsed on a genuinely isolated scratch cluster (PostgreSQL 17.10, `initdb` at
`/tmp/parisesa_rollback_rehearsal`, port 5599) — **not** on production, and not on paper.

1. Replicated the four target tables' DDL from production (`pg_dump --schema-only`).
2. Loaded the before-image CSVs → simulated pre-rebuild state. Dumped + `sha256` = pristine baseline.
3. **Simulated a destructive bad rebuild**: `DELETE` all four scopes → verified 0/0/0/0 rows.
4. **Executed the rollback procedure verbatim** as it would run on production
   (`\copy <table> FROM '<BEFORE_*.csv>' CSV HEADER`).
5. **Detector** (a real one, per §N.8): re-dumped each table with a total `ORDER BY` and compared
   `sha256` against the pristine baseline.

```
iu: BYTE-IDENTICAL  ce08d8d6f5f0c47981b32fe274f592f0a65169836cf10a6d73c92dd7674d3200
mg: BYTE-IDENTICAL  f4d43811e0d257ee6c43b3f38b0e9f4f386995e44c5ab7d1737e2870d59b696e
rx: BYTE-IDENTICAL  f65dcc01ae9324172528e8c380457832e9716819059d0d5c5be17ba75a35a244
cf: BYTE-IDENTICAL  3d111677000b4f51d18dac5dd9b683ebfcdbf18308011d0d15aa7c87080a7869
ROLLBACK_REHEARSAL_RESULT: PASS
```

## §5 — Packet C (`ga_panchanga`, F-63): PARKED — named missing clause

**Missing clause: §19.2 clause 4, bounded scope.** The rollback itself is fine — the byte-level
restore of `chart_facts` passed the §4 rehearsal.

`ga_panchanga` is an L1 root (`depends_on = {ga_positions}`). Rebuilding it flips **53 downstream
assets, spanning all five layers** of the native's canonical chart, from `lit` to `stale`. Neither
possible outcome fits inside a bounded packet:

- **Leave them stale** — the native's cockpit reads "out of date" across the entire derived stack,
  and the packet has silently committed him to a full five-layer chart rebuild it never scoped.
- **Restore `lit` from the before-image** — `chart_facts` really did change, so re-stamping `lit`
  asserts a freshness no detector would now compute (§N.8).

A 5-row `combination_name` correction is not worth either. The right unit of action is a
**deliberate full-chart rebuild, decided by the native**, with F-63 folded into it — not a
5-row-scoped packet whose side effect is 53 assets wide. Parked, explicitly, rather than forced.

F-63's defect is separately confirmed live and unchanged: 5 rows in `chart_facts`
(`fact_category='panchanga_special_yoga_combinations'`, `fact_key='combination_name'`) still read
`'unknown'` on the canonical chart.

## §5.1 — F-35's system-wide scope: measured, then split

The claim "the writers have not re-run for ANY chart since the fix landed" is **confirmed**, and its
true size is now measured rather than assumed:

| Table | Charts affected | Rows |
|---|---|---|
| `mimamsa_manifestation_grammar` (F-35) | **2** — `482012f1…` (canonical), `1c826d5a…` (Abhinandan) | 24 + 23 |
| `mimamsa_insight_units` (F-104) | **2** — same two | 115 + 35 |
| `bodha_rm_remedy_prescriptions` (F-116) | **3** — the two above + `cb73cd3d…` | 135 each |

System-wide before-state, all charts: `evidence_grade='empirical'` on **10 rows with
`scored_count = 0`**; `leakage_status='clean'` on **150/150 rows**; `preamble_stripped` present on
**0/405 rows**. Every one is the pre-fix state.

**Decision: split, not widen.** This packet covers `482012f1…` only. GA-3 authority here is scoped
to *the native's own canonical chart*; `1c826d5a…` and `cb73cd3d…` are different charts and a
different consent surface, so folding them in silently would be authority drift. They are flagged
as a **separate follow-up of identical shape** (same assets, same rebuild, same rollback recipe) —
smaller than this one, and blocked only on scope authorization, not on any technical unknown.

## §5.2 — F-143 is NOT fixed by this rebuild (disclosed, not folded in)

The suggested branch `parisesa/repair-F143-mi-darshana-grading` **does not exist** — verified
against all 23 `refs/heads/parisesa/*` remote branches and a repo-wide PR search. Nothing to fold in.

More importantly, the defect is live and this rebuild will **re-write it**.
`writers/mi_darshana.py:226`, in the emergent-law/discoveries path:

```python
n = r.get("n_support") or 0          # line 214 — an assignment/support count
...
"empirical" if n >= 5 else "prior_only",   # line 226 — no scored-outcome gate
```

This is the *identical* unearned-`empirical` defect F-35 fixed one path over, still standing in the
discoveries path: `n_support` counts assignments, not confirmed/partial/denied outcomes. On the
canonical chart **20 of 71 `mimamsa_discoveries` rows have `n_support >= 5`**, so the rebuild will
emit 20 insight rows graded `empirical` on an unearned basis.

Stated plainly: this rebuild makes `leakage_status` and the manifestation-grammar grade honest; it
does **not** make `evidence_grade` honest chart-wide. Claiming "F-35 resolved ⇒ grades are now
earned" after this execution would be false.

## §5.3 — F-71: crash resolved, asset still cannot complete — PARKED on a NEW blocker

Run `257eb0c2…` (2026-08-21 02:18:20Z) dispatched `mi_bhara`. Outcome, from the job logs:

```
[execute_dag] TIMEOUT: asset_id=mi_bhara exceeded writer_timeout_seconds=600 — marking error
BLOCKED mi_bhara — upstream not complete: ['timeout:600s']
```

**What this proves and does not prove.** The original F-71 defect is genuinely gone: the writer ran
for a full 600 s of real work, streaming `kala_field` (8,599,775 rows for this chart) and fitting
weights across 64 LEL events. It never reached `fetch_open_predictions`'s old `float(None)`
TypeError, and the crash precondition is independently 0 (`mimamsa_predictions` has no open row with
an empty `observation_window`). **But `mi_bhara` still cannot reach `lit`.** It now fails on a
different, previously-hidden blocker that the old crash was masking — the crash used to abort the
asset in seconds, so its watchdog budget was never tested.

**Root cause:** `asset_registry.writer_timeout_seconds` for `mi_bhara` is **600**, against **10800**
for every sibling (`mi_darshana`, `mi_sambandha`, `bo_upaya`). `runner.py:317` prefers the per-asset
budget over the job's `WRITER_TIMEOUT_SECONDS=7200` env, so the env value never applied.

**Why parked, not fixed: §19.2 clause 4, bounded scope.** The remedy is
`UPDATE asset_registry SET writer_timeout_seconds = … WHERE asset_id = 'mi_bhara'` — a row in a
**global, chart-independent registry**. It changes the build contract for `mi_bhara` on *every*
chart, present and future. This packet's declared scope is one chart's data; silently widening it
to a global registry row would be authority drift of exactly the kind §19.2 exists to prevent.
It is also a plausible-looking one-liner that deserves its own review: 600 may be a deliberate
guard rather than an oversight, and nothing in this packet's evidence distinguishes the two.

`mi_bhara`'s `asset_throughput` state is `error` both before and after — unchanged in kind. Only
the `last_error` text changed, from the stale TypeError traceback to the honest current reason.
That is strictly more truthful than what was there before.

## §5.4 — SCOPE AMENDMENT (execution-discovered): Packet A is 7 assets, not 3

**This is a correction to my own §0 analysis, recorded because the packet is worthless if it hides
the fact that its author's first scope model was wrong.**

§0 treated `bo_upaya` (F-116) and the L5 trio (F-35/F-104) as two independently-executable packets
whose only interaction was ordering. That was incomplete. What execution revealed:

1. `bo_upaya`'s rebuild fired its stale cascade over **15 assets**, as predicted and disclosed.
2. But the scheduler seeds only **`lit`** out-of-plan dependencies as satisfied. A `stale`
   dependency **blocks**. So the cascade did not merely re-label the L5 assets — it made the
   2-asset follow-up plan *unrunnable*:
   ```
   mi_sambandha :: BLOCKED: upstream dependency(ies) mi_bhavisya, mi_pariksha, mi_pramana …
   mi_darshana  :: BLOCKED: upstream dependency(ies) mi_adhilepa, mi_gunanaka, mi_pariksha,
                            mi_pramana, mi_sambandha …
   ```
3. The minimal set that unblocks F-35/F-104 is therefore **7 assets**:
   `mi_pramana, mi_pariksha, mi_bhavisya, mi_gunanaka, mi_adhilepa, mi_sambandha, mi_darshana`.

**The honest generalisation:** fixing `bo_upaya` inherently requires rebuilding its downstream
subtree. There is no ordering that avoids this — running the L5 assets first would have left them
stale the moment `bo_upaya` ran. By the same standard I applied to Packet C in §5, F-116 was **not**
a bounded single-asset packet, and I should have said so before executing it rather than after.
I did not, and §0's "Packet B: EXECUTE" call was made on an incomplete model of the cascade.

**No data was harmed by the blocked run.** Verified, not assumed: `mimamsa_insight_units` and
`mimamsa_manifestation_grammar` were re-dumped and compared against their before-images —
**byte-identical**. The BLOCKED path writes nothing; it only set `asset_throughput.state`.

**Scope expanded under full discipline, not waived.** Before executing the 7-asset run:
- Before-images captured for **all 24 chart-scoped `mimamsa_*` tables** (113,491 rows) in
  `BEFORE_expanded/` — a deliberate superset of what the 7 writers touch, so no table they write
  lacks a snapshot.
- Quiescence re-proved at execution time (0 active runs, 0 write locks, 0 building assets). The
  §1 proof was taken at 02:10Z and had expired; a quiescence proof is only valid at its instant.
- Rollback mechanism unchanged and already rehearsed byte-identical in §4 (`\copy … FROM` per table).
- Still one chart, still zero credential/permission/schema changes.

`ka_kshetra` (11,069,325 rows) is **not** in `mi_darshana`'s upstream closure and is not rebuilt.

## §6 — Bounded scope (§19.2 clause 4)

- **Chart:** exactly one — `482012f1-710e-4a25-994a-93821f5871aa`. No other `chart_id` written.
- **Packet A assets:** `mi_sambandha`, `mi_darshana`, `mi_bhara` — nothing else.
- **Packet B asset:** `bo_upaya` — nothing else.
- **Mechanism:** `build_runs` + `build_run_assets` INSERT, then
  `gcloud run jobs execute brahma-build-pipeline-job --args=^:^--run-id:<run_id>`. The plan array
  is the explicit asset list; `_schedule_parallel` seeds already-`lit` out-of-plan deps as satisfied
  (`runner.py:475-484`), so no dependency is silently pulled into the run.

## §7 — Zero credential / permission / schema-destructive changes (§19.2 clause 5)

- **Credentials:** none created, rotated, or written. `amjis-db-password` and `amjis-pipeline-db-url`
  were *read* only. The scratch cluster uses `--auth=trust` on a local socket and holds no production
  secret.
- **Permissions:** no `GRANT`/`REVOKE`/`ALTER ROLE`/IAM change.
- **Schema:** no `CREATE`/`ALTER`/`DROP` against production. Migration 573 was verified
  already-applied, not applied by this packet. All DDL executed in this session ran on the
  throwaway scratch cluster only.
- **Namespaces:** PARIPRAŚNA / EKAVĀKYATĀ untouched.
- Writers use the L1+ idempotency standard (§N.3) — per-chart delete-then-insert scoped to
  `(chart_id × natural key)`. A rebuild REPLACES; it does not accrete.
