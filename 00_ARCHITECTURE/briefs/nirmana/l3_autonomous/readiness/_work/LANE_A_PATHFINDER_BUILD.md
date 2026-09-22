---
artifact: KALA_PATHFINDER_BUILD
version: "1.0"
status: CURRENT
date: 2026-09-22
scope: >
  The measurement no prior audit made: a real L3 Kāla writer run end-to-end against real
  upstream data, on a DISPOSABLE Postgres 15. Domain C proved the orchestrator's MECHANICS
  (advisory lock, manifest verification, writer registration) on a schema-less throwaway
  instance; it never ran a `ka_*` writer or produced a row. This closes that gap.
method: >
  Disposable PG15 (initdb, port 59433, torn down after). Schema for 9 tables dumped
  --schema-only from production (read-only). Three real production rows seeded: the canonical
  chart, its natal Moon `chart_facts` row, and the `asset_registry` row. Writer invoked through
  the real `ContextSpec` the orchestrator constructs (asset_runner.py:983-986) with
  `birth_params` from the real `fetch_birth_params`. NO production mutation of any kind.
produced_by: strategic session (Claude Code), Lane A of the Kāla elevation-readiness completion
---

# Lane A — the first real Kāla build

**Asset chosen:** `ka_tithi_pravesha` (Tithi-Praveśa, the lunar-return annual chart). Selected
because it is the cheapest genuine test in the layer: a LIGHT writer (single `run(ctx)`), one
declared dependency (`ga_positions`), and real astronomy per row (an ephemeris root-find plus a
full annual-chart cast). It is a pathfinder, not a sample — see §5 for what it does NOT establish.

## 1. It builds, and the cost model is now measured rather than estimated

| Measurement | Value |
|---|---|
| Writer discovery (`discover_all`, once per process) | 0.818 s, 123 writers registered |
| Cold build, 120 rows | **0.611 s** |
| Rebuild (idempotency path), 120 rows | **0.577 s** |
| Per row, incl. ephemeris root-find + annual chart | **~5.1 ms** |
| Rows converged (`start_converged` AND `end_converged`) | 120 / 120 |
| Rows carrying their L1 `moon_fact_id` reference | 120 / 120 (§N.5 satisfied) |

The writer's own docstring claims "~3.4 ms/row benchmarked"; measured here at ~5.1 ms/row
wall-clock including INSERT. Same order — the docstring is honest.

**Idempotency (§N.3) holds:** a second run leaves 120 rows, not 240. Delete-then-insert, scoped
to `chart_id`.

## 2. FROZEN orchestrator contract (§N.2) — verified empirically, not assumed

Tested by running the writer and observing a SECOND connection before committing:

| Contract clause | Result |
|---|---|
| Writer must not commit `ctx.db_conn` | PASS — rows invisible to another session pre-commit |
| Orchestrator retains rollback authority | PASS — rollback left 0 rows |
| Writer must not close the connection | PASS — connection open after `run()` |
| Writer must not write `asset_throughput` | PASS — 0 rows written by the writer |

## 3. Its verification flag is EARNED (§N.8) — proven by mutation

`verification_pass_status` is not a constant. `writer.py:196-211` recomputes the annual chart's
Moon longitude through a **different code path** (`compute_chart`'s full position pipeline) and
compares it against the root-find target, tolerance `LUNAR_RETURN_TOL_DEG = 0.01`
(`logic.py:73`).

**Mutation test:** forcing the tolerance to `-1.0` (unsatisfiable) flipped **all 120 rows** to
`divergent_flagged`. The detector can genuinely read false. This asset is a positive model of
§N.7 item 5 for the rest of the layer.

## 4. FINDING — `kala_tithi_pravesha`'s window instants are 5.5 hours late in production

**Severity: MATERIAL. Present-tense, reproducible, and invisible to every check that exists.**

The clean-room rebuild reproduces production **exactly** on all ten non-temporal columns —
`pravesha_lagna_sign_idx`, `..._name`, `..._degree`, `natal_moon_longitude_deg`, `moon_fact_id`,
`start_converged`, `end_converged`, `verification_pass_status`, `formula_version`,
`pravesha_year` — 0/120 rows differ. It differs on **exactly** the two `timestamptz` columns, in
**all** 120 rows, by **exactly 19,800 s = 5.5 h = the IST offset**.

Which is correct is decidable from the native's own birth data. Praveśa year 1's `window_start`
IS the birth instant (1984-02-05 10:43 IST, CLAUDE.md §B):

| | stored instant | same instant in IST |
|---|---|---|
| Production | 1984-02-05T10:42:52**+00:00** | 1984-02-05 **16:12:52** IST |
| Clean rebuild | 1984-02-05T05:12:52+00:00 | 1984-02-05 **10:42:52** IST ✓ |

**Root cause —** `services/ka_tithi_pravesha/writer.py:125`:
`return datetime.fromisoformat(raw[:19]), birth_params`. The `[:19]` truncation discards any
timezone suffix, producing a **naive** datetime. The writer then works entirely in local
wall-clock (correctly — `logic.py` receives `tz=float(bp["tz_offset_hours"])` for the astronomy)
but never re-attaches an offset before persisting. psycopg inserts a naive datetime into a
`timestamptz` column, so **Postgres interprets it in the session TimeZone**. Nothing in
`pipeline/orchestrator/` sets a session TimeZone, so the server default applies: production
reports `UTC`. The IST wall clock is therefore stored labelled UTC.

My rebuild is correct only by accident — the disposable instance inherited `Asia/Kolkata` from
the host. **That makes this an environment-dependent correctness bug: the same code writes
different absolute instants depending on where it runs.** A build dispatched from a
differently-configured runner would silently disagree with an existing one.

**Why nothing caught it.** The served path double-cancels the error.
`query_tithi_pravesha.ts:84-85` renders with `to_char(window_start, 'YYYY-MM-DD"T"HH24:MI:SS')`,
and `to_char` on a `timestamptz` renders in the **session** timezone — a UTC serving session
prints `10:42:52`, the original correct wall clock. The displayed text looks right. But
`query_tithi_pravesha.ts:90` computes
`is_current = (window_start <= $4::timestamptz AND window_end > $4::timestamptz)` — a **true
timestamptz comparison**, which is off by 5.5 h. So `kala_now_get` selects the wrong praveśa year
for a 5.5-hour band around every annual boundary, while displaying a correct-looking date.
Two-pass verification did not catch it either: it checks the ASTRONOMY (Moon longitude agreement),
which is correct. The defect is purely at the persistence boundary. This is §N.7 item 5 exactly —
"verified fact ≠ verified prose", here "verified astronomy ≠ verified storage".

**Containment (measured, not assumed).** `kala_tithi_pravesha` is the ONLY `kala_*` table holding
computed astronomical instants in `timestamptz`. Every other `kala_*` `timestamptz` column is
metadata (`bound_at`, `event_ts`, `released_at`, `activated_at`, `flipped_at`). The sibling
annual-chart asset `ka_sudarshana_varsha` stores `window_start`/`window_end` as `date`, so it
cannot carry this defect. The `fromisoformat(raw[:19])` idiom appears in exactly one writer.
**Blast radius: one asset, two columns, 120 rows per chart.**

**Recommended disposition — for the elevation campaign, not for tonight:** make the writer
timezone-explicit (attach the birth offset it already has in `bp["tz_offset_hours"]`, or store
`timestamp` + an explicit offset column), then rebuild. Do NOT "fix" it by setting a session
TimeZone — that hides an environment dependency rather than removing it. A regression test should
assert year 1's `window_start` equals the birth instant, which is a golden value the chart itself
supplies.

## 5. What this does NOT establish

- **One asset is not the layer.** `ka_tithi_pravesha` is the layer's cheapest writer. It says
  nothing about `ka_kshetra` (~14k LOC, millions of rows) or `ka_sangam` (fan-out 7). Per-asset
  cost must still be measured per asset; §1's numbers are an anchor, not a model.
- **Seven trigger-function guards were absent** from the disposable schema (they live in functions
  the table-scoped dump did not carry): `_assert_throughput_global_no_chart_id`,
  `_record_asset_throughput_state_change`, `l1_data_plane_capture_row`,
  `l1_data_plane_guard_active_mutation`, `nirmana_invalidate_chart_receipts`,
  `nirmana_invalidate_registry_receipts`, `reject_build_run_manifest_mutation`. My run therefore
  exercised the writer WITHOUT production's guard layer. A campaign harness must carry the
  functions too — see Lane G's harness spec.
- **This was not `execute_run`.** The full orchestrator entrypoint additionally requires a
  `build_runs` row with a frozen manifest plus `_verify_registry_still_matches_manifest` and
  `_verify_sidecar_code_matches_manifest`. Domain C proved those mechanics separately. The two
  halves have not yet been proven in ONE run — that is the remaining end-to-end gap.
- **`WriterResult.duration_seconds` is reported as 0.0** by this writer (timed externally by the
  orchestrator). Minor, but it means a writer's self-reported duration is not a usable cost signal.

## 6. Reproducing

Disposable instance: PG15 via `initdb`, socket `/tmp/kalapg`, port 59433, DB `kala_pathfinder`;
schema via `pg_dump --schema-only` of 9 tables; 3 rows seeded by `\copy` from production.
Harness scripts written to `/tmp/kalapg/{pathfinder,mutation,contract}.py`. The instance was
stopped and its data directory removed after this report. No production row was read other than
by `SELECT`, and none was written.
