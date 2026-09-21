# KĀLA PRIVILEGE MATRIX — F4 `data_plane_builder` grant coverage vs. L3 writer needs

**Status:** v1.0. **Produced by:** KĀLA READINESS AUDIT, cycle 1 (2026-09-22). **Source subagent
work:** `_work/F4.md` (full SQL command log). Conductor independently re-ran the two
highest-stakes privilege checks (§3 below) before promotion.

## 1. Re-measured coverage by table-name prefix

Connected as `data_plane_builder` itself (`source dbenv_builder.sh`); every figure below is
`has_table_privilege('data_plane_builder', ...)`, tested as the role, not inferred as a superuser
would see it.

| prefix | total | SELECT | INSERT | UPDATE | DELETE |
|---|---|---|---|---|---|
| bodha_ | 36 | 28 | 28 | 28 | 28 |
| chart_ | 15 | 4 | 4 | 4 | 4 |
| ganita_ | 2 | 0 | 0 | 0 | 0 |
| kala_ | 41 | 39 | 39 | 39 | 39 |
| mimamsa_ | 37 | 0 | 0 | 0 | 0 |
| phala_ | 20 | 0 | 0 | 0 | 0 |
| other | 280 | 107 | 69 | 69 | 68 |
| **TOTAL** | **431** | **178** | — | — | — |

**Charter-cited numbers re-verified exactly:** `kala_* 39/41`, `bodha_* 28/36`, `chart_* 4/15`,
`mimamsa_* 0/37`, `phala_* 0/20`. **One number corrected:** the cited headline "258/431
inaccessible" is now **253/431** — 5 relations improved since whatever snapshot produced 258.
Direction unchanged (still PARTIAL, still a large uncovered majority); restate as 253/431 going
forward. All 32 `kala_*` sequences have `USAGE` — no sequence-level gap.

The 2 inaccessible `kala_*` tables (`kala_gochara_windows__ssv_20260728c`,
`kala_gochara_windows_archive_20260805`) and 11 inaccessible `chart_*` tables (consent/deletion/
audit + panchanga-cache tables) are confirmed **not touched by any active L3 writer or its import
closure** — not a build risk.

## 2. L3 writer import closure (methodology)

22 active `@register('ka_*')` writers (`ka_gochara_sweep.py` present on disk but its `@register`
import is deliberately removed — retired, confirmed by direct file read). Closure traced one hop
at a time from every writer's `from services.*`/`from pipeline.*`/`from brahmagyan.*`/`from
panchang_engine.*` imports. A first broad-grep pass produced ~110 false positives (tables actually
belonging to `mi_*`/`ph_*`/`ga_*`/`bo_*` writers sharing the same directories) — rescoping to the
precise closure cut the candidate table list from 180 to **68 genuine references**.

## 3. Confirmed build-blocking gaps (would fail an L3 build TODAY)

| Asset | Missing table | Guarded? | Verdict |
|---|---|---|---|
| **`ka_moorti_nirnaya`** | `bg_transit_moorti` (`_fetch_moorti_table`, unconditional, no try/except) | **No** | **CONFIRMED HARD FAIL** — unhandled `psycopg.errors.InsufficientPrivilege` on first substantive DB call; LIGHT writer, no substep isolation. |
| **`ka_kshetra`** | `phala_rectification` (`fetch_sigma_t_days`, mandatory stage3 substep, no try/except) | **No** | **CONFIRMED HARD FAIL** — stage3 is on the mandatory substep path; this HEAVY writer cannot complete it. |
| `ka_kshetra` (secondary) | `bg_synthetic_cohort`/`bg_synthetic_cohort_md` (`cohort_client.py`, stage6) | **Looks handled, isn't** — `try/except` present but no `SAVEPOINT`; the Postgres transaction poisons on the privilege error and the *next* statement in the same substep fails too, less legibly. The codebase knows the correct fix (named per-query `SAVEPOINT`, used correctly for `bg_transit_av_gates`) and just didn't apply it here. | Same net effect as a hard fail, one step removed. |
| `ka_bhavishya_lekha` | `phala_anchors` | **Partially** — guarded by `to_regclass(...) IS NOT NULL`, which checks catalog *existence* only, not privilege | Safe on a chart's **first** build (guard branch skipped, `existing_ids` empty); **fails on any rebuild** of a chart with existing rows — the normal iterative-development mode for the canonical chart. |

**Conductor independent re-verification (this cycle):**
```sql
SELECT has_table_privilege('data_plane_builder','public.bg_transit_moorti','SELECT'),
       has_table_privilege('data_plane_builder','public.phala_rectification','SELECT');
-- f|f
```
Both confirmed inaccessible, matching the subagent's core claim exactly.

## 4. Correctly-guarded gaps (confirmed NOT a build risk)

- `bg_combustion_orbs` (`ka_vighnakara`) — named `SAVEPOINT`, classical-value fallback.
- `bg_transit_av_gates` (`gochara_v3`/`gochara_grammar`) — named per-query `SAVEPOINT`, explicitly documented fix for this exact trap.
- `convergence_scores` (`ka_sangam`) — not queried by any live code path yet (pre-U4 stub; `ka_sangam.py:989` confirms `school_consensus_by_domain` stays empty pre-U4).

## 5. Non-L3 privilege gaps (reported for visibility only — not owned by this audit)

- `mimamsa_* 0/37` — affects every L5 `mi_*` writer, not L3.
- `phala_* 0/20`, except `phala_anchors`/`phala_rectification` which **are** L3's problem (§3); the other 18 are L4 `ph_*` territory.
- `chart_* 4/15` — the 11 inaccessible tables are consent/deletion/audit and panchanga-cache, confirmed outside the L3 closure; a data-governance/L1-serving concern.
- `bodha_* 28/36` — the 8 inaccessible tables do not appear in the L3 closure grep (L3 only touches 5 `bodha_*` tables, all 5 accessible).

## Summary

**Yes — there is a privilege gap that blocks an L3 asset build today, and it is not a single
isolated case.** `ka_moorti_nirnaya` and `ka_kshetra` both have confirmed, completely unguarded
reads against tables `data_plane_builder` cannot SELECT; both hard-fail on the very next build
attempt. `ka_bhavishya_lekha` is safe on first build but fails on rebuild. Migration 1070
restored core orchestrator privileges but did **not** extend to `bg_transit_moorti`,
`phala_rectification`, `bg_synthetic_cohort`, or `bg_synthetic_cohort_md` — these four need
`SELECT` granted to `data_plane_builder` before these three assets are build-safe. Independent of
the grant itself, `ka_kshetra`'s cohort-path `try/except`-without-`SAVEPOINT` pattern (§3) is worth
fixing on its own merits, since the same "looks handled, isn't" shape could recur against any
future privilege gap.

**Native decision implication:** this is a repair candidate (grant `SELECT` on 4 named tables to
`data_plane_builder`) — small, targeted, outside the F1/egate.sql repair lane, and should be
queued as its own low-risk migration once the native authorizes it (this audit does not self-
authorize new migrations beyond the F1 repair per charter scope).
