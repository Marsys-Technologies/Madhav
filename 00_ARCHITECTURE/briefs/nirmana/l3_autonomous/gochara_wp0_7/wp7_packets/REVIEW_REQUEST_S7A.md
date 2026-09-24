# REVIEW REQUEST — §7.A (WP10 cutover runbook as runnable artifacts + rehearsal)

**Brief:** `GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md` §7.A
**Branch:** `l3/gochara-autonomous-wp0-7`
**Sheet items implemented:** WP10 runbook preparation (plan §9 steps 0–10) as runnable scripts + disposable-DB rehearsal

## What changed

- **`platform/python-sidecar/scripts/kala_gochara_cutover/`** — the full runbook: `common.py` (explicit `--dsn`, production refusal per tranche flag, evidence writer), step artifacts 0–10 (`step00_clear_guard.md` cherry-pick instructions referencing `origin/l3/kala-p1-1-b1-clear-guard` head `eb00da67d` — never re-implemented; SQL/Python for steps 1–8 and 10; `step09_soak_checklist.md`), and `evidence/step00…step10_evidence.template.md`, each opening with the standing-order acknowledgment.
- **Production guard:** any DSN on port 5433 (Cloud SQL proxy prod) or a non-loopback host exits 4 `REFUSED` unless `PRODUCTION_TRANCHE_1_AUTHORIZED` (steps 0–5) / `PRODUCTION_TRANCHE_2_AUTHORIZED` (steps 6–10) is exactly `"true"`. Both are `false` in the brief frontmatter; the guard runs before any other failure mode.
- **Step 5 is unnumbered on purpose** (no migration number in the filename); the number is assigned at tranche-1 start after the E-009 re-scan. Step 5 carries the surviving D-C item: the century's `clear_tables` declares `kala_gochara_windows` (F-30).
- **`platform/python-sidecar/tests/l3/gochara/test_wp10_cutover.py`** — 14 tests over a stripped-down synthetic schema on a disposable Postgres (55434): prod refusal, grant, restore-drill NOT_RUN, guard + reversal, idempotent 1080–1086 apply/verify, registry re-pin fields + conjuncts (a)–(k) incl. red-on-injection for (f) and (k), reversal, candidate build + rebuild refusal (exit 6), flip gates incl. gate-4 scratch rollback, flip + reverse, birth-epoch detector, N-11 refusal-then-dispose.
- **`WP10_REHEARSAL_v1_0.md`** — per-step outcome table and the carried NOT_RUN reasons.

## Tests

`test_wp10_cutover.py` 14/14 green on the disposable DB; full `tests/l3/gochara/` battery **266 passed**. Disposable container `gochara-wp10-disposable` torn down after the run; WP6's 55433 container left as found. Note: the rehearsal venv needed PyJHora's pinned transitive deps installed (geocoder et al.) to collect G-10 — environment-only, no repo change.

## Unsure of

- The production-identification heuristic (5433 / non-loopback) is a convention I chose; if the platform's real prod access path differs, tighten `common.py::is_production_dsn` before tranche 1.
- Step 2's digest/gap gates (38,287 rows, 2,667 uncovered ids) are coded but unexercised — no dump exists locally; they prove themselves only at tranche time.
- Conjunct (j)'s `target_table` extraction (`substring(count_sql from 'FROM ([a-z0-9_]+)')`) assumes lowercase relation names in count_sql; verified on the seeded fixture only.
