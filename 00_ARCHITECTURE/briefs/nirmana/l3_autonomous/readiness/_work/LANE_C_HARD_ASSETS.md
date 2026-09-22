---
artifact: LANE_C_HARD_ASSETS
version: "1.0"
status: READINESS_RAW_MATERIAL
date: 2026-09-22
scope: >
  Deep per-asset readiness analysis for the three hardest L3 Kāla assets —
  (A) the Gochara family, (B) ka_kshetra, (C) ka_sangam — as raw material for the native's
  elevation briefs. Read-only. No production mutation, no build dispatch, no campaign evidence
  event, no migration authored or edited, no guard weakened.
worktree: /Users/Dev/madhav-l3/readiness (branch l3/kala-elevation-readiness)
canonical_chart: 482012f1-710e-4a25-994a-93821f5871aa
baseline_inherited_not_redone: >
  00_ARCHITECTURE/briefs/nirmana/l3_autonomous/audit/{KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md,
  KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md, KALA_EXECUTION_DESIGN_v1_0.md,
  KALA_DATA_CENSUS_v1_0.md, KALA_PRIVILEGE_MATRIX_v1_0.md, KALA_DAG_RECONCILIATION_v1_0.md}
evidence_discipline: >
  Every claim carries a file:line or the exact SQL. Claims are graded on the six-state scale the
  charter requires: PRESENT (rows exist) / QUALIFIED (rows carry their own honesty metadata) /
  CONSUMED (a real caller reads it) / EFFECT-TRACEABLE (the decisive field changes a downstream
  value) / SERVED (it reaches a user-facing surface) / VALUE-EVALUATED (someone has shown it
  improves an answer). These are six different claims. A grep that finds no caller establishes
  only my search scope, and I state the scope each time.
---

# LANE C — the three hardest Kāla assets

**How to read this.** §0 is the short list of findings that change a decision. §A is the Gochara
family, scoped as the prompt requires to *environment executability of the native's existing v0.3
plan* — not a re-plan. §B is `ka_kshetra` and §C is `ka_sangam`, each following the eight required
headings, as raw material for briefs that do not yet exist.

Three of my findings **correct** statements in the governing documents. They are flagged
`CORRECTION` and each carries the evidence that overturns the prior claim. Two findings are
**COULD NOT VERIFY** and are named as such rather than resolved by a plausible default.

---

## §0 — The findings that change a decision

| # | Finding | Asset | Evidence |
|---|---|---|---|
| **F1** | **A layer-scoped cockpit Clear would today delete the 16,297 protected sweep-capital rows, with no guard of any kind in place.** `filterScopeAssets` never filters `is_active`, so retired `ka_gochara_sweep` is in scope; its live `count_sql` derives `DELETE FROM kala_gochara_windows WHERE chart_id=$1 AND generation='v1'`; `build_protected_assets` has **0 rows**; and **no trigger exists on any `kala_*` table**. | Gochara | `clearScopeFilter.ts:20-40`; `clear/execute/route.ts:160-183`; live SQL §A.6 |
| **F2** | **CORRECTION — the seed's `target_table` for `ka_gochara` is wrong; the Strategy is right.** `ka_gochara` writes `kala_gochara_windows_v2` at `generation='2.0'` and **never touches `kala_gochara_windows`**. The "retired sweep shares a live table with an active writer" hazard is therefore *not* a writer hazard — it is purely a **registry** hazard (F1). | Gochara | `ka_gochara.py:120,336,362`; live `count_sql` §A.2 |
| **F3** | **The Clear route's own safety comment is false against the live DB.** It states `kala_gochara_windows` "carries a DB-level trigger guard (migration 540) as defense-in-depth". Migrations 540 and 566 both created triggers there; migration **588 dropped all three**; live `pg_trigger` confirms none remain. A stale safety claim inside a destructive code path (§N.8). | Gochara | `clear/execute/route.ts:~94`; `588_remove_asset_build_protection.sql:44-48`; live SQL §A.6 |
| **F4** | **The canonical chart's 8.57M Kshetra rows are an INCOMPLETE, UNPUBLISHED generation — and the incompleteness is invisible from the data.** All 8,570,075 rows reference `field_snapshot_id = kfs_1805…8e5f`, for which `kala_field_snapshots` holds **zero** manifest rows. The build stopped mid-`stage5`, in alphabetical class order: 25 classes have field segments, **15** have null statistics, **14** have windows, **0** have salience / insights / timeline. | Kshetra | live SQL §B.2 |
| **F5** | **19 of the canonical chart's 25 event classes have a fabricated baseline hazard, and `kala_field` has no column that says so.** Only 6 classes have a real `brahma_class_priors` row. The `baseline_is_synthetic` tag exists on `kala_field_windows` but **not on `kala_field`** — so the 8.57M-row table cannot distinguish a calibrated λ from a synthetic one. Of the windows that did get written, **15,024 of 17,528 (85.7%) are `baseline_is_synthetic = true`**. | Kshetra | `hazard.py:139-170`; live SQL §B.2; `information_schema` §B.2 |
| **F6** | **The other chart has a COMPLETE Kshetra run over only the 6 calibrated classes; the canonical chart has an INCOMPLETE run over 25 classes including 19 synthetic.** These are two different configurations, not two runs of one pipeline. This is the real answer to PARK-5. | Kshetra | live SQL §B.2 |
| **F7** | **Mode starvation at the Sangam consumer boundary: the top 500 and top 750 rows by `convergence_score` are 100% Mode C.** `ka_vighnakara` (`LIMIT 500`) and `ka_kala_darshana` (`LIMIT 750`) therefore see **zero** Mode A and zero Mode B windows — they never see a dasha×transit convergence at all. This is the exact class-starvation defect D-3 FIX-PSEL repaired one level *up*, reproduced one level *down* and unrepaired. | Sangam | live SQL §C.4; `ka_vighnakara.py:179-183`; `ka_kala_darshana.py:28-31` |
| **F8** | **Mode D rows are structurally duplicated ~13×.** 14,352 Mode D rows resolve to **1,104 distinct (peak_date, window_start, window_end, score)** tuples across 26 signal_ids. The in-code guard meant to prevent this (`pred_dict is pred_dicts[0]`) is **vacuous on the lifetime path**, because that path passes `pred_dicts=[pred]` — a one-element list, so the guard is always true. Mode D is 70% of the table. | Sangam | `ka_sangam.py:591` vs `:721-726`; live SQL §C.4 |
| **F9** | **CORRECTION — the prompt's cited Sangam caps are partly stale.** The flat `ORDER BY dignity_score DESC, p.id ASC LIMIT 200` at ~`:247` **no longer exists**; it survives only as a comment describing the *prior* query. The live query is a per-`signature_class` window function plus a Python quota selector. The `[:1]` at `engine.py:1102` is **not** on the scoring path — it selects only the C12 tājika `domain_lord`, while the daśā query uses the **full** `constituent_lords` set (`engine.py:1113`). | Sangam | `ka_sangam.py:247-305`, `:166-221`; `engine.py:1099-1124` |
| **F10** | **`confidence_score` is an unearned signal (§N.8).** It is `min(1.0, independent_current_count/13)`, and `independent_current_count` counts hand-weighted booleans, one of which — `'transit'` — is the tautology `mode in ('A','B')`. Nothing measures whether the witnesses are independent. Observed ICC never exceeds 6 of 13, so `confidence_score` is capped at 0.46 by construction. | Sangam | `ka_sangam.py:908,931,965`; `engine.py:850-946`; live SQL §C.4 |
| **F11** | **The only non-degenerate confidence tier is computed, stored, and then not served.** `confidence_label` is degenerate for every Mode A/B row (100% `'speculative'`); the JL-014 within-chart `confidence_label_relative` does discriminate — and the retrieval capability's projection **omits it**, serving the degenerate label instead. | Sangam | `engine.py:789-849`; `query_convergence_windows.ts:118-129`; live SQL §C.4 |
| **F12** | **`ka_kshetra` and `ka_moorti_nirnaya` still cannot build today.** `stage3_clocks.py:1012` calls `fetch_sigma_t_days` → unguarded `SELECT … FROM phala_rectification`, which `data_plane_builder` cannot SELECT. Confirmed the call site independently; the audit's verdict stands. The cohort path *is* `try/except`-guarded (`writer.py:1754-1770`) but with **no SAVEPOINT**, so the caught privilege error still poisons the ambient transaction. | Kshetra | `stage3_clocks.py:1012`; `uncertainty.py:185-206`; `writer.py:1754-1770` |

---

# §A — THE GOCHARA FAMILY

**Scope of this section, per the prompt.** The native has already written
`GOCHARA_FAMILY_ELEVATION_PLAN_v0_3.md` (status `PROPOSAL_FOR_NATIVE_RULING`). I do **not**
re-plan it. My job is: *what must the environment provide for v0.3 to be executable, and what in
v0.3 can the environment not currently support?* I nonetheless resolve family membership myself
from the live registry and the code, because v0.3's WP10 cutover and R6 policy both depend on
that map being right — and it is not right in the seed.

## A.1 — What each member actually computes, and the membership resolved

**Membership, resolved from live `asset_registry` + code (not from the seed's prose):**

```sql
SELECT asset_id, is_active, storage_type, scope, target_table, superseded_by,
       data_disposition, estimated_seconds, target_floor, array_to_string(depends_on,'+')
FROM asset_registry WHERE asset_id LIKE 'ka_%' ORDER BY asset_id;
```

| asset | active | target_table (registry) | **live `count_sql` target** | est s | floor | depends_on |
|---|---|---|---|---|---|---|
| `ka_gochara` | t | `kala_gochara_windows` | **`kala_gochara_windows_v2` WHERE generation='2.0'** | 1 | 83 | `bg_gochara_arcs`+`ka_gochara_resonance` |
| `ka_gochara_resonance` | t | `gochara_resonance_map` | (same) | 1 | 762 | `bg_transit_rules` |
| `ka_gochara_sweep` | **f** | `kala_gochara_windows` | `kala_gochara_windows` WHERE generation='v1' | 1000 | 16297 | `ka_gochara_resonance` |
| `ka_gochara_v3_century_materialize` | t | `kala_gochara_windows_v2` | `kala_gochara_windows_v2` WHERE generation LIKE 'g3_%' | 614 | 914 | `ka_gochara_resonance`+`ka_vedha_gochara`+`ka_moorti_nirnaya`+`ka_kota_chakra`+`ka_tithi_pravesha`+`bg_sky_calendar` |

`ka_gochara_sweep` carries `superseded_by = 'ka_gochara'`, `data_disposition = 'RETAINED_AS_CAPITAL'`.

### F2 — the seed-vs-strategy contradiction, resolved AGAINST the seed

The discussion prompt frames this as "the seed says X, the Strategy says Y, establish which is
true." **The Strategy is correct and the seed's `target_table` is stale.** Three independent
pieces of evidence, all live:

1. `platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara.py:120` —
   `TABLE = "kala_gochara_windows_v2"`. This module-level constant is the *only* DELETE/INSERT
   target in the file (`:336` DELETE scoped by `(chart_id, event_class, generation)`, `:141`
   INSERT, `:362` `"generation": GENERATION_V2`).
2. `services/ka_gochara/service.py:15-17` states it in the docstring: "`@register('ka_gochara')`
   WriterBase subclass that joins … `generation='2.0'` rows into `kala_gochara_windows_v2`".
3. The live registry's own `count_sql` for `ka_gochara` reads
   `SELECT COUNT(*) FROM kala_gochara_windows_v2 WHERE chart_id=$1 AND generation='2.0'`.

So the writer's own file header (`ka_gochara.py:16-66`) is explicit that `kala_gochara_windows`
is its **frozen read-only cross-check corpus**, never a write target.

**Consequence for v0.3.** v0.3's D9 says "Migration 670 already corrected `count_sql`;
`target_table` and the seed remain stale" — confirmed exactly. But v0.3's §1 and the discussion
prompt both still carry the *stronger* claim that "retired history shares a live table" and that
"any delete-then-insert rebuild of `ka_gochara` is a hazard to protected history." **That
specific hazard is closed at the writer level.** The hazard that remains is entirely in the
registry, and it is worse than the writer one — see A.6/F1.

### What each computes (from code, not docstring)

- **`ka_gochara`** — per event class, resolves a *progressive horizon*
  (`services.w2g.materialize.progressive_horizon`, `ka_gochara.py:110,269-273`), computes a class
  fingerprint, and if changed, deletes and re-inserts that `(chart_id, event_class,
  generation='2.0')` partition. Horizon status is disclosed per class in
  `kala_gochara_v2_build_state.horizon_status` (`ka_gochara.py:80-81,437-458`). Classical
  technique: gochara contacts of transiting bodies to natal/derived targets, arc-based
  (`bg_gochara_arcs` upstream). **Departure from classical:** the unit of record is a *day-level
  window* (the table stores dates, not instants — v0.3 §3.6 already names this), and the search
  is horizon-bounded rather than lifetime-complete.
- **`ka_gochara_v3_century_materialize`** — the century/era/resolution-grid materialiser, 2,480
  LOC, the largest single writer in L3. Writes `kala_gochara_windows_v2` at `generation LIKE
  'g3_%'` (live: `g3_utkarsha`, 914 rows canonical).
- **`ka_gochara_resonance`** — the T0 root; writes `gochara_resonance_map`; feeds the other three.
- **`ka_gochara_sweep`** — retired, `@register` import deliberately removed (confirmed by the
  environment audit's direct file read). Its 16,297 `generation='v1'` rows in
  `kala_gochara_windows` are the protected capital.

## A.2 — Output: what is actually in the tables

```sql
SELECT generation, count(*), count(DISTINCT event_class) FROM kala_gochara_windows
 WHERE chart_id='482012f1-…' GROUP BY 1;   -- v1|16297|6   3.0|914|27
SELECT generation, count(*) FROM kala_gochara_windows_v2
 WHERE chart_id='482012f1-…' GROUP BY 1;   -- 2.0|87   g3_utkarsha|914
```

Two generations coexist in **both** tables. Note the shape: `kala_gochara_windows` `generation='v1'`
covers only **6** event classes but 16,297 rows; `generation='3.0'` covers **27** classes in 914
rows. `kala_gochara_windows_v2` `'2.0'` = 87 rows; `'g3_utkarsha'` = 914 rows. The `914` appearing
in both tables under different generation labels (`3.0` and `g3_utkarsha`) is the
multiple-generation-label artefact the census already flagged; I did not determine whether they are
the same 914 windows written twice. **COULD NOT VERIFY: whether `kala_gochara_windows.generation='3.0'`
and `kala_gochara_windows_v2.generation='g3_utkarsha'` are the same 914 windows** — deciding it needs
a row-level content comparison, which would mean selecting per-row window payloads; I kept to
aggregates per the conduct rules. It is cheap for an authorised operator to settle and it matters
to v0.3 R6's restore drill, so it should be settled there.

## A.3 — Inputs, and the declared-vs-actual read question

The century materialiser's live `depends_on` is
`ka_gochara_resonance + ka_vedha_gochara + ka_moorti_nirnaya + ka_kota_chakra + ka_tithi_pravesha +
bg_sky_calendar`.

**CORRECTION to the discussion prompt's premise:** it lists `ka_sudarshana_varsha` among the
century materialiser's declared-but-unconsumed inputs. **`ka_sudarshana_varsha` is not in the live
`depends_on` at all.** The declared-but-unconsumed set to adjudicate is the *three* named in the
prompt's own first clause — `ka_kota_chakra`, `ka_tithi_pravesha` — plus `ka_moorti_nirnaya` and
`ka_vedha_gochara`, whose consumption I did not trace (see scope note below). `ka_sudarshana_varsha`
is a separate portfolio question: it is declared by nothing and consumed by nothing.

**Scope statement.** I did not re-trace the century materialiser's read closure; the environment
audit already did (`KALA_PRIVILEGE_MATRIX_v1_0.md §2`, 68 genuine references from a precise
import closure). I inherit that and did not duplicate it.

**Does Sangam read the materialised table?** No. `ka_sangam.py:35` imports
`services.ka_gochara.service.KaGocharaService`, and `plan_substeps` constructs it as
`KaGocharaService(swe)` (`ka_sangam.py:317-320`) — a Swiss-ephemeris-injected *on-demand geometry*
service, not a table reader. `ka_sangam.py` appears nowhere in a repo-wide grep for
`kala_gochara_windows` across `platform/python-sidecar/**/*.py`. **So the Strategy is right and the
registry's declared `ka_gochara` edge on `ka_sangam` is a scheduling/ordering edge, not a
computational read.** Search scope: `grep -rl 'kala_gochara_windows' --include='*.py'` over the
whole sidecar, excluding tests.

## A.4 — Consumers

Search scope: `grep -rln` for `kala_gochara_windows` over `platform-mcp/src` and `platform/src`
(TypeScript) and `--include='*.py'` over `platform/python-sidecar`, tests excluded. Non-test
consumers found:

| Consumer | File | What survives the projection |
|---|---|---|
| MCP coverage attestation | `platform-mcp/src/tools/retrieval/register_gochara_windows.ts` | v0.3 §5 already documents: unknown generation falls into the retired-sweep branch (`:963-977`, `:1466-1478`, `:1041`); can answer `not_covered` before reading rows. **I did not re-verify these line numbers** — inherited from v0.3's `[A]`-tagged review evidence. |
| Reading checklist | `platform/src/lib/retrieval/registry/layers/reading_checklist.ts` | v0.3 §5: drops ids/generation/basis, `LIMIT 200` then counts the capped set. Not re-verified here. |
| **Cockpit Clear** | `platform/src/app/api/cockpit/clear/execute/route.ts` | **Re-verified in full — see A.6. This is the live blocker.** |
| Pariprasna engine tier | `platform/src/lib/pariprashna/confidence/engine_tier.ts` | v0.3 §5: not wired. Not re-verified. |
| L5 prospective ledger | `platform/src/lib/lel/prospective_ledger.ts` | v0.3 §5: no field for contact id/generation/convention. Not re-verified. |
| Kshetra cross-check | `services/ka_kshetra/writer.py`, `stage4_field.py`, `hazard.py` | reads `kala_gochara_windows` as a *classification-only* legacy corpus; `writer.py:2253-2262` is explicit that legacy VALUES are never copied (§N.5-compliant). |
| D9 judgment / AV gates | `register_d9_judgment.ts`, `query_transit_av_gates.ts` | not re-verified. |

## A.5 — Known defects

I did not re-audit the Gochara *numerical* defects (F3 wrong-zodiac W2G solve, F13
exception→0.0→"active", F15 uncited kakshya fixture, the W2G station-merge and seam-tangency
losses, the S0 noon/midnight assignment). v0.3 §2 D1–D12 already carries each with `[A][X E8]`
re-run evidence, and the prompt directs me not to re-plan. **They are inherited as stated.**

The defects I did establish myself are environment/registry defects and are in A.6.

## A.6 — Build reality, and THE environment blocker for v0.3

### F1 + F3 — the sweep-capital deletion path, live

This is the single thing that must be fixed before v0.3's WP10 (or any Clear-adjacent work) is
executable. Four facts, each independently verified:

1. **Nothing filters retired assets out of a Clear.**
   `platform/src/lib/cockpit/clearScopeFilter.ts:20-40` — every branch filters on `scope`,
   `layer`, or `asset_id`. `is_active` is never referenced. A `scope='layer',
   scope_target='kala'` Clear therefore includes `ka_gochara_sweep`.
2. **The derived DELETE targets exactly the protected rows.**
   `platform/src/app/api/cockpit/clear/execute/route.ts:160-172` resolves ops from
   `deriveDeleteSqlFromCountSql(asset.count_sql)` **first**, and only falls back to
   `target_table` (`:174-183`) when that yields nothing. `ka_gochara_sweep.count_sql` is live
   `SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='v1'` → a derived
   `DELETE … WHERE chart_id=$1 AND generation='v1'` → the 16,297 capital rows.
   *(Silver lining, and worth recording: because `count_sql` wins over `target_table`,
   `ka_gochara`'s stale `target_table` is never reached — its derived DELETE is correctly scoped
   to `kala_gochara_windows_v2 … generation='2.0'`. The stale field is a documentation hazard,
   not a deletion hazard.)*
3. **The application-layer protection set is empty.**
   ```sql
   SELECT count(*) FROM build_protected_assets;   -- 0
   ```
   `route.ts:95-99` builds `protectedAssetIds` from this table; with zero rows the exclusion at
   `:106` is a no-op.
4. **The claimed DB-level defense-in-depth does not exist.**
   ```sql
   SELECT c.relname, t.tgname FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
   JOIN pg_namespace n ON n.oid=c.relnamespace
   WHERE n.nspname='public' AND NOT t.tgisinternal AND c.relname LIKE 'kala_%';
   -- (0 rows)
   ```
   Positive control (same query without the `kala_%` filter) returns `asset_registry|1`,
   `asset_throughput|2`, and 2 triggers on each of ~25 `bodha_*` tables — the query works.
   Root cause is traced, not inferred: `540_build_protected_assets.sql:180,217` and
   `566_parishkara_mr06_gen3_protection.sql:146` create the three triggers; both are recorded
   applied in `_migrations_applied` (ids 400 and 425, 2026-08-06 and 2026-08-10); and
   `platform/migrations/588_remove_asset_build_protection.sql:44-48` explicitly
   `DROP TRIGGER IF EXISTS` all three. So the live absence is *intended by 588*, and the defect
   is that `clear/execute/route.ts`'s comment (~`:94`) still asserts the guard as present. That
   is a §N.8 earned-signal defect in a destructive path: a safety claim with no code behind it.

**v0.3 already knows part of this** (D8 "cockpit Clear is an unlisted destructive writer with the
protection registry now empty"; D10 "Migration 588 is applied; no guard triggers exist"). What
this lane adds is the *mechanism*: the missing `is_active` filter is what converts "the registry
is empty" into "a routine layer Clear deletes the capital", and the route's own comment is what
would make a reviewer believe otherwise.

### What the environment must provide for v0.3 to be executable

| v0.3 item | Environment requirement | Status today |
|---|---|---|
| **R6** (fresh (table, generation) policy; map the whole mutation surface incl. cockpit Clear; real restore drill on all 38,287 v1 rows; rollback under concurrent reads) | An `is_active` (or explicit disposition) filter in `filterScopeAssets`, **or** seeded `build_protected_assets` rows, **or** restored triggers — at least one. Plus a corrected route comment. | **BLOCKING. None of the three is in place.** |
| **R10** (reconcile seed · live registry · generated contracts · integrity SQL · coverage logic, early) | The reconciliation must include `ka_gochara.target_table` (stale, F2) and must be re-runnable, because `asset_registry_seed.ts`'s `runSeed()` would re-introduce it. `KALA_DAG_RECONCILIATION §6.2` already shows the guard cannot catch registry-vs-seed drift. | **Not blocking, but must land before WP1's D1/D3 contracts, exactly as v0.3 says.** |
| **WP3a/WP4** (kernel + decomposed comparison on synthetic non-person fixtures) | No production data, no real chart. Nothing in the environment blocks this. `transit_search.py` remains untouched per R2. | **Executable today.** |
| **WP9 overlays** (Vedha, Moorti, Kota on the agreed convention) | `ka_moorti_nirnaya` **cannot build**: `_fetch_moorti_table` reads `bg_transit_moorti`, unconditional, no try/except; `data_plane_builder` lacks SELECT (`has_table_privilege(...,'bg_transit_moorti','SELECT') → f`). | **BLOCKING for WP9's Moorti half.** Needs the 4-table grant the privilege matrix proposes. |
| **WP10 benchmark → cutover** | Needs R6 closed (above) + the four functional flip gates on `kala_gochara_authority` (`527:98-102`). `kala_gochara_authority` holds 1 row for the canonical chart. | **Blocked behind R6.** |
| **v0.3 §5 receiving contracts** | The MCP coverage branch, `reading_checklist`, and the L5 ledger fields are all TypeScript edits with no environment dependency. | **Executable today.** |

### What v0.3 asserts that the environment cannot currently support

1. **v0.3 §3.6 "atomic switch only to a *complete* candidate; readers pin one publication per
   request."** There is no publication-identity table for the Gochara family. `kala_gochara_v2_build_state`
   is per-`(chart, event_class, generation)` build bookkeeping (297 rows canonical, two distinct
   `build_id`s), not an immutable publication manifest with a complete-partition guarantee.
   Kshetra's `kala_field_snapshots` is the only such structure in L3 — and §B.2 shows it is
   itself unwritten for the canonical chart. **v0.3's publication model has no substrate yet; it
   has to be built, and it should be built once for both families rather than twice.**
2. **v0.3 §3.7 "Every answer declares which it is: snapshot, interpolated, or direct."** No
   served surface carries such a field today, and the L3 retrieval registry has no capability
   with a `density_contract` (§N.6) — `query_convergence_windows.ts` has zero occurrences. The
   receiving side of the declaration does not exist.
3. **v0.3 R6's "restore drill covering all 38,287 current v1 rows, content-checked."**
   The canonical chart holds 16,297 of them; a second archive table
   (`kala_gochara_windows_archive_20260805`, 16,297 rows canonical) exists but
   `data_plane_builder` has **no SELECT on it** (privilege matrix §1: it is one of the two
   inaccessible `kala_*` tables). **A restore drill executed as the builder role cannot read its
   own recovery source.** This is a concrete, new environment blocker for R6 that v0.3 does not
   name.

## A.7 — The elevation question (environment framing only)

The prompt correctly scopes me out of re-planning. The one thing I will say, because it follows
from the environment evidence rather than from method opinion: **v0.3's own §8.2 priority — kill
the fixture kakshya fallback — is the only item on its list whose value does not depend on any
missing environment capability.** Everything downstream of it (publication identity, coverage
attestation, `snapshot|interpolated|direct` declaration, restore drill) needs substrate that does
not exist yet. If sequencing has to be argued, that asymmetry is the argument.

**Ablation to test whether an elevation helped.** For the kakshya repair specifically: re-run the
served path with the fixture fallback *forced on* vs *replaced by `not_evaluated`*, and measure
the spread of the activity value. v0.3 §1 records all 380 served gen-3.0 activity values sitting
between 0.99964 and 1.0. If the repair is real, that degenerate band must widen or the rows must
become honestly unevaluated. If neither happens, the fixture was not the cause.

## A.8 — Open decisions for the native (Gochara)

| # | Decision | Options and costs |
|---|---|---|
| A-1 | **How is the sweep capital protected?** | (a) add `is_active` filtering to `filterScopeAssets` — smallest change, but silently changes Clear semantics for every retired asset in every layer; (b) seed `build_protected_assets` — explicit, per-chart, but is a data row anyone can delete; (c) restore the 540/566 triggers — strongest, but reverses a deliberate migration-588 decision and needs the native's ruling on why 588 removed them. **v0.3 R6 asks for a fresh ruling here; this is the concrete menu.** |
| A-2 | **Fix `ka_gochara.target_table`, or delete the field's authority?** | Correcting it in the registry is one UPDATE, but `asset_registry_seed.ts` re-introduces it on any reseed. The deeper option is to make `count_sql` the single authority and stop deriving anything from `target_table` — which removes a whole class of staleness but touches the cockpit contract. |
| A-3 | **Does the R6 restore drill run as `data_plane_builder` or as a privileged operator?** | As builder it cannot read `kala_gochara_windows_archive_20260805`. Either grant SELECT (one more table on the privilege-repair migration) or declare the drill an operator-role activity and say so in the gate. |
| A-4 | **Is publication identity built once for L3, or per family?** | Kshetra already has `kala_field_snapshots`' schema (content hash, corpus pin, config pin, substrate build ids, hashed tables, event classes, skipped classes). Gochara needs the same shape. Building it twice guarantees they diverge. |
| A-5 | **The 914-row ambiguity** (A.2) — settle it inside R6's drill, or before? | Cheap to settle; it determines whether `generation='3.0'` in the *legacy* table is capital, duplicate, or orphan. |

---

# §B — ka_kshetra

## B.1 — What it actually computes

**In plain language.** Kshetra models, for each of a fixed set of life-event classes, a
**continuous time-varying hazard rate λ_e(t)** over the native's 100-year horizon, and stores it
as a piecewise segment table. It is a survival/point-process model wearing Jyotiṣa operands — not
a window-finder.

The formula is stated exactly at `services/ka_kshetra/layer1.py:22-30` and implemented at
`layer1.py:60-165`:

```
ln λ_e(t_k) = ln λ⁰_e + ln P̃_e                      baseline + promise (constant in t)
            + Σ_s w_s · A_s · r_{s,e}(t_k)           clock term    (daśā lord stacks)
            + Σ_j β_j · x_j(t_k)                     modifier term (covariates)
            + Σ_m ln(1 − ρ_m · u_m(t_k))             suppression   (SM-R-7 filtered)
```

Term by term, with the classical technique each stands in for:

- **λ⁰_e** — `hazard.baseline_rate()` (`hazard.py:139-170`) = `lifetime_count / 36525`, i.e. the
  class's classical lifetime expectation per 100 years, divided into a per-day rate. **This is
  not a classical quantity.** It is an actuarial base rate that classical Jyotiṣa does not
  supply; the project sources it from `brahma_class_priors` and, where absent, *fabricates* it
  (see F5).
- **P̃_e** — `promise_tilde()` (`hazard.py:175+`): `P_floor + (1−P_floor)·P_e`, where `P_e` is a
  noisy-OR prior over the chart's structural promise (yoga/bhāva/kāraka evidence from L2). This
  is the **Adṛṣṭa floor** — the model's refusal to let a chart's silence on a class mean zero
  probability. Classical analogue: the doctrine that an unpromised event is unlikely, not
  impossible. The noisy-OR combination is the departure — classical texts do not combine
  promise evidence probabilistically.
- **Clock term** — `layer1.py:109-136`: for each predictive daśā system, builds the lord stack at
  knot *k* (MD→AD→PD by `LEVEL_ORDER`), computes `relevance(lord_stack, routes,
  depth_weights)`, and adds `clock_log_factor(clock.quality, r, w_s)`. **This is the actual
  Jyotiṣa.** A period is "relevant" to an event class iff its lord participates in a `Route` —
  a stored causal path from a promise node to the class. Departure: classical daśā judgment is
  categorical (the lord is or is not a kāraka for the matter); this makes it a graded, weighted,
  depth-discounted continuous relevance.
- **Modifier term** — `layer1.py:138-150`: `Σ β_j x_j(t_k)` over `COVARIATE_KEYS`, read straight
  out of a pre-computed Layer 0 matrix. Gochara, transit intensity, and similar. Classical
  analogue: gochara as a modulator of a daśā promise, which is orthodox. Departure: additive in
  log space, with fitted β.
- **Suppression term** — `layer1.py:152-165`: `Σ ln(1 − ρ_m u_m(t_k))`, filtered per class by
  **SM-R-7 Option B** — only obstructions that some `Route` explicitly names in
  `suppressed_by` can suppress that class. A class with no suppressed routes gets `S_e(t)=1.0`.
  Classical analogue: vighna / arishta cancellation. This is the most disciplined term in the
  model — it is *structurally impossible* for an unrelated obstruction to touch a class.

**Purity.** `layer1.py` is documented and written as pure: no DB, no IO, no RNG. The whole
expensive path reads pre-computed Layer 0 arrays rather than re-evaluating `terms_at()` — the
docstring at `:12-14` says this eliminates "60K+ redundant evaluations." That is a real
architectural achievement and it is the reason the 8.57M-row build finished stage 4 in ~1h35m
(§B.6).

**The null programme** (`stage5_null.py`, `dhara_null.py`, `dhara_null_vec.py`) generates
`DEFAULT_REPLICATES = 1024` shifted replicates per class and derives an exceedance statistic. The
prompt's Q4 asks what `null_p`/`null_r` mean. From the schema and the code they are a
**within-chart, shift-invariance exceedance**: "how often does a random temporal shift of this
chart's own clock produce a peak at least this high?" That is a statement about the *structure of
the chart's own clock*, not about event probability in a population. I did not read the estimator
end-to-end (budget), so: **COULD NOT VERIFY the exact null hypothesis the shift grid instantiates**
— `stage5_null.py:584-600` shows a `sigma_t_days`-widened bracket around `t_peak`, and
`kala_field_null` stores `shift_grid_step`, `q_threshold`, `bucket_days=730`, `replicates=1024`,
but I did not confirm whether the shift is circular, reflected, or truncated at the horizon. That
distinction changes the denominator materially and is exactly what the native's Q4 needs settled.

## B.2 — Output: grain, counts, and the state of the rows

**Target table** (registry): `kala_field`. **Grain**: `(chart_id, event_class, segment_index)`,
with `t_start`/`t_end` in days-from-birth. Key columns: `alpha`, `gamma` (segment shape),
`lambda_start`/`lambda_end`, `integral_days`, and the four decomposed terms
(`promise_term`, `clock_term_start`, `modifier_term_start`, `suppression_term_start`) —
**the decomposition survives into storage**, which is unusual and valuable: a consumer can ask
*why* λ is high, not just *that* it is.

Eighteen relations in the family. Live census for the canonical chart:

```sql
SELECT event_class, count(*), round(avg(t_end-t_start)::numeric,4), min(refinement_depth), max(refinement_depth)
FROM kala_field WHERE chart_id='482012f1-…' GROUP BY 1 ORDER BY 2 DESC;
```

| fact | value |
|---|---|
| `kala_field` rows, canonical | **8,570,075** |
| event classes | **25** |
| rows per class | **342,803 — identical for all 25** |
| mean segment length | **0.1065 days (~2.6 h) — identical for all 25** |
| `t` range | 0 … 36,525 (exactly 100 Julian years) |
| `refinement_depth` | **min 0, max 0 — adaptive refinement never deepened, on any row** |
| `refinement_exhausted` | 0 rows true |
| `lambda_start=0 AND lambda_end=0` | 0 rows |
| distinct `field_snapshot_id` | **1** (`kfs_180521585e89394014dcf30015ef8e5f`), 0 NULL |

The identical per-class row count and mean segment length establish something the strategy does
not state: **the breakpoint grid is shared across classes, not class-specific.** All 25 classes
are evaluated on one union knot set. That is a design fact with a direct cost consequence — adding
a 26th class costs a full 342,803 segments regardless of whether that class has any structure.

### F4 — the generation is incomplete and unpublished

```sql
SELECT count(*) FROM kala_field_snapshots
 WHERE field_snapshot_id = 'kfs_180521585e89394014dcf30015ef8e5f';   -- 0
```

8,570,075 rows point at a snapshot manifest that **does not exist**. Four of the eighteen relations
carry `field_snapshot_id` and all four agree on that one dangling id (`kala_field` 8,570,075;
`kala_field_provenance` 959,032; `kala_field_windows` 17,528; `kala_field_null` 150). The other
stage tables (`_kinematics`, `_boundaries`, `_primitives`, `_routes`, `_clocks`, `_promise_*`)
**carry no `field_snapshot_id` column at all** — so the field cannot prove which kinematics
generation produced it. And the timestamps say it could be a problem: `kala_field` was computed
2026-09-10 19:40–21:15, while `kala_field_kinematics`, `_boundaries` and `_primitives` are stamped
2026-09-11 01:49–01:50 — **after** the field that is supposed to depend on them.

The build's stopping point is exact and alphabetical:

| stage table | classes present | rows |
|---|---|---|
| `kala_field` (S4) | 25 — all | 8,570,075 |
| `kala_field_null` (S5 dhara) | **15** — alphabetically through `major_loss` | 150 (10/class) |
| `kala_field_windows` (S5 finalize) | **14** — alphabetically through `major_gain` | 17,528 (1,252/class) |
| `kala_field_salience` (S6) | **0** | 0 |
| `kala_insights` (S6.5) | **0** | 0 |
| `kala_timeline_spec` (S8) | **0** | 0 |
| `kala_field_snapshots` (terminal) | **0** | 0 |

The 11 classes with no windows: `major_loss, marriage, parental_event, property_acquisition,
psychological_arc, relocation, romantic_start, separation, spiritual_turn, surgery, travel_event`
— **exactly the alphabetically-last 11**, and they include **four of the six calibrated classes**
(`marriage`, `relocation`, `separation`, `surgery`). The plan is 25 classes × 10 decades of
stage-4 substeps, then per-class stage-5 substeps, then stage6/stage65/stage8/snapshot
(`writer.py:353-398`), so the run died inside `stage5finalize:major_loss`.

**This is the answer to the prompt's PARK-5 question ("is the served surface wrong, or is the data
unusable?"): neither framing is right.** The data is real, it is a legitimate partial product of a
genuine pipeline, and it is *unfinished and unpublished*. Three of the six calibrated classes never
reached a window. The writer's own contract (prompt §"Internal DAG") already says a partially
completed stage set cannot be selected as a complete snapshot — and the missing manifest row is
that contract working correctly.

### F5 — 19 of 25 classes have a fabricated baseline, untagged in `kala_field`

```sql
SELECT prior_version, count(*), string_agg(signal_type_class,',' ORDER BY signal_type_class)
FROM brahma_class_priors
WHERE fact_kind='lifetime_count_per_100y' AND source_subsystem='*' AND signal_tradition='*'
GROUP BY 1;
-- ne_v01|6|childbirth,foreign_settlement,marriage,relocation,separation,surgery
```

Six classes have a real `λ⁰`. The other 19 can only have been built via
`shape_only=True`, which `hazard.py:162-163` returns as
`SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT / DAYS_PER_CENTURY`.

`hazard.py:150-155` says the `True` tag "is the §N.8 earned-signal fix — a queryable field on every
downstream row." It is not:

```sql
SELECT table_name, column_name FROM information_schema.columns
WHERE table_schema='public' AND column_name IN ('baseline_is_synthetic','shape_only');
-- kala_field_windows | baseline_is_synthetic          (only)
```

**`kala_field` has no `baseline_is_synthetic` column.** A consumer of the 8.57M-row field table
cannot tell a calibrated hazard from a synthetic one. The tag appears only on the *derived*
windows — and there:

```sql
SELECT baseline_is_synthetic, count(*), count(DISTINCT event_class)
FROM kala_field_windows WHERE chart_id='482012f1-…' GROUP BY 1;
-- f | 2504  | 2   (childbirth, foreign_settlement)
-- t | 15024 | 12
```

**85.7% of the canonical chart's field windows rest on a fabricated baseline rate.** The two
honestly-calibrated classes are `childbirth` and `foreign_settlement`.

### F6 — the other chart is the complete run, and it is a different configuration

```sql
SELECT chart_id, count(*), count(DISTINCT event_class) FROM kala_field GROUP BY 1;
-- 1c826d5a-… | 2412882 | 6
-- 482012f1-… | 8570075 | 25
SELECT chart_id, count(*) FROM kala_field_salience GROUP BY 1;   -- 1c826d5a-… | 7650
```

Chart `1c826d5a` has 6 classes — **exactly the 6 calibrated ones** — 2.41M segments, 7,650 salience
rows, 415 insights, 6 timeline specs, and **1 snapshot manifest row**. It is a *complete,
fully-calibrated, published* Kshetra generation. The canonical chart has a *25-class,
19-synthetic, incomplete, unpublished* one. These are two different configurations of the writer,
not two runs of one. Any statement of the form "the field is/isn't useful" that does not say which
of these two it means is ambiguous.

### Qualification of the windows that do exist

```sql
SELECT count(*) FILTER (WHERE null_p IS NULL), count(DISTINCT confidence_tier),
       string_agg(DISTINCT precision_regime,','), string_agg(DISTINCT promise_state,',')
FROM kala_field_windows WHERE chart_id='482012f1-…';
-- 0 | 1 | day_grade | moderate,strong
```

`null_p` is populated on every row (so the null programme did run and land). But `confidence_tier`
has **exactly one distinct value across all 17,528 rows** — a degenerate tier, the same defect
class as Sangam's `confidence_label` (F11). `precision_regime` is uniformly `day_grade`.
`promise_state` does discriminate (`moderate`/`strong`) — but never `weak`, which, given that 19
classes have no real promise evidence, is worth the native's attention.

## B.3 — Inputs

Declared `depends_on` (live): `ka_dasha_kala`, `ka_gochara_resonance`, `ga_panchanga`,
`bo_pratijna`, `bo_sangati`, `bo_upaya`, `bg_cohort`, `bg_class_lifetime_counts` — eight edges,
matching the shim's own header (`pipeline/orchestrator/writers/ka_kshetra.py:38-47`). Note `bg_sky_calendar`
is deliberately **not** an edge (W3 edge-staging rule) and `mi_bhara` is deliberately not an edge
(acyclicity; the calibration loop closes across builds by weights-version pin).

Grain / units / convention checks:

| Input | Read at | Grain | Convention check |
|---|---|---|---|
| `brahma_class_priors` (asset `bg_class_lifetime_counts`) | `stage4_field.py:1155-1168` | one row per `(prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition)` | **Exemplary.** All four coordinates pinned, `ORDER BY` made total, `LIMIT 1`, with a 20-line docstring (`:1146-1156`) explaining that a heap-order-dependent `N_e` would make the whole field non-deterministic. This is §N.7 item 2 done right, and should be the pattern cited to every other L3 writer. |
| `brahma_event_ontology.temporal_shape` | `stage4_field.py:1178-1188` | one row per `event_class_id` | READ, never derived — `:1181-1186` explicitly refuses to infer shape from window duration (§N.7 item 3). |
| `chart_facts` natal Lagna | `writer.py:2277+` (`_natal_lagna_sign`) | fact row | Longitude **referenced**, only the sign bucket derived, using `int(lon/30)+1` — the identical arithmetic `bg_cohort.py` uses, explicitly so the native is compared against an identically-labelled population (`writer.py:2286-2290`). §N.5-compliant. |
| `phala_rectification` | `uncertainty.py:185-206` via `stage3_clocks.py:1012` | one row per rectification candidate | **Unguarded and inaccessible — see F12/B.6.** |
| `bg_synthetic_cohort` / `_md` | `cohort_client.py:171-365` via `writer.py:1754-1762` | synthetic chart + MD-lord interval | try/except present, **no SAVEPOINT** — see B.6. |
| `kala_gochara_windows` (legacy) | `writer.py:2253-2270` | day-level window | Classification only. `writer.py:2255` is explicit: "the legacy row's VALUES are never copied (§N.5)". Comparison is peak-inside-window — deliberately the coarsest honest statement. |
| `kala_field_boundaries.sigma_t_days` | `writer.py:2241-2247` | per boundary | `MIN` over `precision_state <> 'precision_unsupported'`, justified because §4.2 makes σ_t identical at every ladder level. Guarded (`try/except` → `None` → honest not-computed). |

**Upstream richness fetched then discarded — the one I found.** The four decomposed hazard terms
(`promise_term`, `clock_term_start`, `modifier_term_start`, `suppression_term_start`) are stored on
every one of the 8.57M `kala_field` rows. **No consumer reads them** (search scope: `grep -rn` for
each column name over `platform-mcp/src` and `platform/src`, and over `platform/python-sidecar`
excluding `services/ka_kshetra/**` and tests — zero non-owner hits). This is the single richest
discarded signal in the asset: the model already knows *why* λ is elevated at any instant, per
term, and nothing downstream asks.

## B.4 — Consumers

**Search scope, stated explicitly:** `grep -rln 'kala_field'` over `platform-mcp/src` and
`platform/src` (TypeScript, tests excluded); `grep -rl 'kala_field' --include='*.py'` over
`platform/python-sidecar` excluding `services/ka_kshetra/**` and `tests/**`; plus a directory
listing of `platform/src/lib/retrieval/registry/layers/L3_kala/`.

| Consumer | Reads | Does the decisive field survive? |
|---|---|---|
| **`mi_bhara`** (L5) — `pipeline/orchestrator/writers/mi_bhara.py`, `services/mi_bhara/{field,basis,weights,skill,living_lel,db}.py` | `kala_field*` | The **only** substantive machine consumer. Owns `kala_insights.lel_derived = true`; Kshetra owns `false`. The calibration loop. Not traced further (out of lane scope). |
| `kala_priority_get` — `platform-mcp/src/tools/kala_views/priority.ts:78-219` | `kala_field_salience` via the read-only DB proxy | **A real serving path exists.** It reads five salience axes and reports `honest_empty` with a stated reason when absent (`:139,154,197`). For the canonical chart it *always* returns honest_empty, because S6 never ran. Exemplary honesty; zero delivered value today. |
| `kala_explain_get` — `platform-mcp/src/tools/kala_views/explain.ts:40` | a minimal slice of a `kala_field_windows` row | Slice only — I did not enumerate which fields. |
| `kala_ritual_get` — `platform-mcp/src/tools/kala_views/ritual.ts:783-789` | *nothing* | Reports λ as not-in-corpus with an honest reason. See below. |
| `kala_upaya_get` — `upaya.ts:26`, `kala_upaya_diagnosis.ts:896-908` | `kala_field_routes` **optional** | Secondary to `bodha_graph_*`. |
| `kala_ahead_get` — `ahead.ts:740` | *nothing* | See below. |
| **L3 retrieval registry** — `platform/src/lib/retrieval/registry/layers/L3_kala/` | **nothing** | **There is no `kala_field*` capability.** 16 capabilities are registered (11 data + 5 service wrappers, `index.ts:1-30`); none is over any field table. |

### The two stale served claims, one already fixed and one not

- `ritual.ts:783-789` **has been corrected** and is now right about the mechanism: it says the
  earlier claim that Kshetra "has written no rows" was false, that the field *is* populated, and
  that the real blocker is that "no registry capability exists over any `kala_field*` table — so
  λ cannot be reached from the serving plane." I independently confirm the blocker (directory
  listing above). **But its replacement number is also wrong**: it cites "31,350 for the canonical
  chart" in `kala_field_windows`; live is **17,528** for the canonical chart and 7,650 for the
  other (24,178 combined — still not 31,350). A corrected comment that hardcodes a re-measurable
  count re-acquires the same staleness (the DVA-Ruling-16 pattern).
- `ahead.ts:740` **has not been corrected**: "the W2 `kala_field` (still empty in production …
  `ka_kshetra` writes zero field rows)". That is false by 8.57M rows. It is a comment, not a
  served value — the served output of that item is genuinely field-independent — but it is the
  *justification* for a design decision, and the justification is counterfactual.

**So PARK-5's real disposition** is: the served surface is not "hard-coding field empty" in the
sense of returning a false empty; two surfaces carry stale *prose*, one surface reads salience
honestly and finds nothing because S6 never ran, and the load-bearing gap is that **no retrieval
capability exists over the field at all**. Repairing the prose fixes nothing a user sees.

## B.5 — Known defects (file:line)

| # | Defect | Class | Cite |
|---|---|---|---|
| K-1 | `kala_field` carries no `baseline_is_synthetic`, though `hazard.py:150-155` claims the tag is "a queryable field on every downstream row". 6.5M of 8.57M rows rest on a synthetic λ⁰ with no in-table marker. | §N.8 unearned/missing signal | `hazard.py:150-163`; `information_schema` §B.2 |
| K-2 | 8.57M rows reference a `field_snapshot_id` with no manifest row. Nothing in the data says the generation is incomplete. | publication identity | live SQL §B.2 |
| K-3 | The upstream stage tables (`_kinematics`, `_boundaries`, `_primitives`, `_routes`, `_clocks`, `_promise_*`) carry no `field_snapshot_id`; their `computed_at` is **later** than the field they fed. | generation binding | `information_schema`; census §1 timestamps |
| K-4 | `confidence_tier` on `kala_field_windows` has exactly 1 distinct value over 17,528 rows. | degenerate tier | live SQL §B.2 |
| K-5 | `refinement_depth` is 0 on all 8.57M rows and `refinement_exhausted` is never true — the adaptive refinement machinery produced no refinement anywhere. Whether that is correct (no segment needed it) or a disabled path is **COULD NOT VERIFY** without reading the refinement trigger; the two are indistinguishable from the data. | possible dead path | live SQL §B.2 |
| K-6 | `cohort_client.py` is called inside `try/except Exception` (`writer.py:1754-1770`) with **no SAVEPOINT**. On a privilege error the exception is caught and an honest coverage note recorded — but the Postgres transaction is now aborted, so the *next* statement in the same substep fails with a less legible error. The codebase knows the right pattern (`ka_sangam.py:997,1028,1033` uses named SAVEPOINTs correctly; the privilege matrix cites `bg_transit_av_gates` as the documented fix for this exact trap). | "looks handled, isn't" | `writer.py:1754-1770` |
| K-7 | `fetch_sigma_t_days` (`uncertainty.py:185-206`) issues an unguarded `SELECT … FROM phala_rectification`, called from the mandatory `stage3_clocks.py:1012`. | unguarded read on inaccessible table | see F12 |
| K-8 | The four decomposed hazard terms are stored and read by nobody. | discarded richness | search scope §B.3 |

**Defects I looked for and did NOT find.** No NULL→favourable-default substitution in the baseline
path — `baseline_rate` *raises* on a non-positive count rather than flooring it (`hazard.py:164-169`),
and `promise_tilde` raises rather than clamping. No unordered `LIMIT 1` in the class-prior read —
it is the best-pinned selection I saw anywhere in L3 (`stage4_field.py:1155-1168`). No
first-domain-only selection. This asset's *arithmetic honesty* is markedly better than its
*publication and serving* honesty.

## B.6 — Build reality

**Can it build today? No.** `stage3_clocks.py:1012` → `uncertainty.py:185-206` →
`SELECT offset_minutes, lel_fit_score, lagna_stable FROM phala_rectification WHERE chart_id = %s`,
with no `try/except` at the call site and no SAVEPOINT. Independently confirmed:

```sql
SELECT has_table_privilege('data_plane_builder','public.phala_rectification','SELECT');  -- f
```

Stage 3 (clocks/boundaries) is on the mandatory substep path, so the writer hard-fails there.
This confirms the privilege matrix's verdict — and I note one refinement: the writer *also* has a
**guarded** σ_t read (`writer.py:2231-2251`, from `kala_field_boundaries`, `try/except → None`).
The two are different reads for different purposes and only the stage-3 one is fatal.

Secondary: the cohort path (K-6) is `try/except` without SAVEPOINT against `bg_synthetic_cohort`
/`_md`, which `data_plane_builder` also cannot SELECT.

**What it needs that it cannot get:** `SELECT` on `phala_rectification`, `bg_synthetic_cohort`,
`bg_synthetic_cohort_md` (and, for `ka_moorti_nirnaya`, `bg_transit_moorti`) — the four-table grant
the privilege matrix proposes. That migration is not authored here and is not self-authorised.

**Cost, measured rather than estimated.** The registry says `estimated_seconds = 237`. The real
figures from `computed_at` spans on the canonical chart:

| stage | span | wall |
|---|---|---|
| `kala_field` (S4, 8.57M rows, 25 classes × 10 decades) | 2026-09-10 19:40:08 → 21:15:12 | **~1 h 35 m** |
| `kala_field_provenance` + `_windows` + `_null` (S5) | 2026-09-10 21:17:51 → 2026-09-11 03:14:39 / 03:22:11 | **~6 h** |
| `_kinematics`/`_boundaries`/`_primitives`/`_routes`/`_clocks` | 2026-09-11 01:49:07 → 01:50:51 | ~2 m |

**Registry `estimated_seconds` understates the real S4+S5 cost by roughly two orders of magnitude**
(237 s vs ~7.5 h), and the run still did not reach S6. What drives it is P1: the null programme at
`DEFAULT_REPLICATES = 1024` per class (`writer.py:330-333,374-388`), over a knot set of ~342,803
segments per class. S5 is ~4× S4.

**Also note:** `target_floor = 8,599,775` while live is 8,570,075 — the floor sits 29,700 *above*
the achieved count. Per §N.4 floors are aspirational and never gates, so this is not a failure; it
is a sign the floor was set from a different (25-class, complete) run than the one that landed.

**Any BUILD-PROTECTED guard?** Not on Kshetra. But the L2 cross-layer delete guard the prompt
names is real and must not be disabled: Kshetra owns only `kala_insights.lel_derived = false`,
`mi_bhara` owns `true`, and a naive `DELETE FROM kala_insights WHERE chart_id` would cross that
boundary.

## B.7 — The elevation question

**The honest framing first.** More field rows are not value. The canonical chart already has 8.57M
segments and **zero** of them reach a user. The gap is not production; it is *completion,
publication, and a serving path* — in that order.

Four distinguishable elevations, ranked by what each unlocks:

1. **REPAIR A DEFECT — finish the generation and write the manifest.** Run S5→S6→S6.5→S8→snapshot
   to completion so `kala_field_snapshots` has a row. **Consumer capability unlocked:
   `kala_priority_get`'s five-axis salience vector stops returning `honest_empty`** (`priority.ts:139`)
   — the only existing serving path into the field, currently starved. This is the cheapest
   elevation with a real consumer at the end of it, and it requires no new doctrine. Cost: the
   remaining ~11 classes of S5 plus S6/S6.5/S8 — on measured rates, several hours, and it is
   blocked behind the `phala_rectification` grant (B.6).
2. **QUALIFY EXISTING DATA — put `baseline_is_synthetic` on `kala_field`, and fix
   `confidence_tier`'s degeneracy.** Today a consumer of the field cannot tell calibrated from
   fabricated. **Consumer capability unlocked: a served field answer can say "this class has no
   calibrated base rate; the shape is real, the level is synthetic"** — which is the difference
   between usable and misleading for 19 of 25 classes. Cheap, schema-only, and it makes (1)
   safe to serve.
3. **SURFACE DISCARDED RICHNESS — expose the four decomposed hazard terms.** The model already
   stores *why* λ is elevated at every instant. **Consumer capability unlocked: "the elevation in
   2027 is 70% clock-term (Saturn AD on a route to this class) and 30% modifier; suppression is
   inactive" — a mechanism answer, not a magnitude answer.** No other L3 asset can produce this.
   This is the strongest argument I can see for the continuous-field model *as such*: a window
   ladder gives you when; the field gives you when-and-because-of-which-term, continuously.
4. **ADD GENUINELY NEW EVIDENCE — more classes, more replicates, finer knots.** I would argue
   against this until (1)–(3) land. The per-class cost is fixed at 342,803 segments (§B.2), so
   every new class costs the same whether or not it has structure, and none of it reaches a
   consumer today.

**The native's Q1 ("is the continuous-field model the right abstraction to preserve?").** The
evidence that bears on it, neutrally stated: the model's *arithmetic* is the most disciplined in
L3 (B.5's "defects I did not find"); its *decomposition* is a capability nothing else in the
system has (3 above); and its *delivery* is zero — no capability, no manifest, no complete
generation, on the native's own chart. Those three facts are compatible with either answer. What
they rule out is deciding on the basis of "8.6M rows exist."

**Ablations to test whether an elevation actually helps.**

- *For (1) completion:* build the snapshot, then answer one real timing question with
  `kala_priority_get`'s salience vector present vs. absent. If the ranking of the top-5 priorities
  is identical either way, salience is decorative.
- *For (3) decomposition:* take the top-10 field windows by `lambda_peak`, generate a mechanism
  sentence from the four terms, then **zero out the clock term and regenerate**. If the sentence
  does not change, the clock term — the only genuinely classical operand in the formula — is not
  doing the work the model claims.
- *For the null programme:* re-run one class at `replicates=128` instead of 1024. If `null_p`'s
  ranking of windows is unchanged, 87% of the S5 cost is buying precision nobody consumes.
- *For the synthetic baselines:* compare window *rank order* within a class between the 2
  calibrated classes and the 12 synthetic ones. If synthetic-baseline classes rank windows
  identically to calibrated ones (λ⁰ is a constant multiplier, so within-class rank *should* be
  invariant), that is the proof that the synthetic baseline affects only cross-class comparison —
  which would let the native serve within-class rankings honestly today and defer the priors work.
  **I did not run this; it is a single aggregate query and it is the highest-information cheap
  test on this asset.**

## B.8 — Open decisions for the native (Kshetra)

| # | Decision | Options and costs |
|---|---|---|
| B-1 | **25 classes or 6?** The canonical chart's run used 25 (19 synthetic); the completed run on the other chart used 6 (all calibrated). | (a) 6 calibrated only — honest, complete, publishable today, but silent on 19 life domains; (b) 25 with `baseline_is_synthetic` propagated to `kala_field` and enforced at serve time — full coverage, 4× the cost, and every consumer must handle the tag; (c) 25 but serve only within-class rank for synthetic classes (see the B.7 ablation). |
| B-2 | **Does `Accepted N/22` count a partially-elevated Kshetra?** The stage DAG makes staged acceptance natural, but the snapshot manifest is all-or-nothing by design. | (a) one terminal asset — simple, but a 7.5-hour build is an all-or-nothing acceptance; (b) per-stage-family acceptance with the snapshot as a separate terminal gate — matches the code, but needs a definition of what a "stage-accepted, unpublished" field means to a consumer. |
| B-3 | **What does `null_p` mean, and what is the honest denominator?** | Needs the shift-grid semantics settled (my COULD-NOT-VERIFY in B.1). Options for the oracle: an analytic exceedance for a known-λ synthetic process (independent of the implementation), vs. re-running the existing estimator at a different replicate count (**not** an oracle — the old output cannot validate a method that may have a defect). |
| B-4 | **Is the shared knot grid right?** All 25 classes share one breakpoint set at 342,803 segments each. | Per-class grids would cut cost for structureless classes but break the cross-class comparability the shared grid gives for free. |
| B-5 | **Is `refinement_depth` a dead path?** (K-5) | Either confirm no segment met the refinement trigger (then the column is honest and the machinery is dormant), or find the disabled path. Cheap to settle by reading the trigger; I did not. |
| B-6 | **Which of the 699 registered fields are load-bearing?** | The register is the worklist. My one concrete datum: the four decomposed hazard terms are stored, material, and have **no** receiving operator (K-8) — they are either the most valuable unexploited asset in L3 (B.7 item 3) or four columns × 8.57M rows of dead weight. |
| B-7 | **Sequencing: P0/P1/P2/P6.** | The measured cost (B.6) says P1 (the null programme) is ~4× P-everything-else. But P6 (publication) is what turns 8.57M rows into something a consumer can pin. **Publication before optimisation** is the position the evidence supports: optimising an unpublishable artefact cannot pay back. |

---

# §C — ka_sangam

## C.1 — What it actually computes

**In plain language.** Sangam takes each MSR-derived *activation predicate* (a structural claim
about the chart, written by `ka_yojaka`), asks "when could this fire?", and writes ranked date
windows. It does this in **four separate modes** that share a scoring function but not a search
method — and that is the root of most of its problems.

| Mode | Method | Classical technique | Departure |
|---|---|---|---|
| **A** | Daśā-eligibility **soft prior** → transit search *inside* eligible survivors. `dasha_kala_service.query(target_lords=…, max_level=3)` gives windows; `find_aspect_events` from `transit_search.py` finds contacts inside the horizon; each hit is scored. (`engine.py:1048-1200`) | The orthodox core: *daśā gives the period, gochara gives the moment.* | The daśā prior is a **soft** multiplier rather than a gate — a transit hit outside any eligible window still scores via `static_dasha_score` (`engine.py:1109,1134-1141`). |
| **B** | Off-daśā sweep — transit search across the whole horizon, `magnitude_threshold=0.3`, flagged `is_off_dasha_discovery`. (`engine.py:1332+`) | No classical analogue. | This is explicitly a *discovery* mode, and it is honestly flagged as such in the row. |
| **C** | SUBSYSTEM predicates routed to `mode_c_subsystem_period` — **sign-ingress** triggered periods, not aspect-based. (`engine.py:1570-1671`) | Sade-Sati-like / sign-residence judgments (`_AYUR_SIGNS_SATURN`, `_AYUR_SIGNS_MARS`, `_VASTU_SIGNS` at `engine.py:1563-1567`). | Coarse — a sign residence is a multi-year state, scored on the same 0–1 scale as a same-day aspect. |
| **D** | SAV-bindhu activation: for `('Jupiter','Saturn','Mars')`, windows where the transited sign's SAV ≥ 28. (`engine.py:1673-1760`) | Aṣṭakavarga transit gating — orthodox. | Sign-level and **predicate-agnostic** — which is precisely why F8 happens. |

**Scoring** (`engine.py:696-729`, "RATIFIED I-16"):
`score = Π(necessary) × (1 − Π(1 − w_i·s_i))` — a multiplicative veto over necessary conditions
(C11 vedha enters here), times a saturating sum over weighted supporting currents. The supporting
currents are C7 aṣṭakavarga potency, C8 eclipse proximity, C9 transit-to-transit, C10 station,
C11 vedha, C12 tājika annual, C13 school consensus, plus pāñcāṅga quality, benefic dṛṣṭi,
cross-daśā agreement, nakṣatra subsystem. A TRIGGER **suppressive** term is then composed on top
for Modes A/B only, at admitted weights 0.2/0.2 (`ka_sangam.py:41-44,50-136`).

**One genuinely good piece of design worth naming**: the supporting dict distinguishes an *absent
key* from a *present 0.0*, and `_current_stance` (`engine.py:731-760`) surfaces that as
`{'state':'honest_empty','empty_reason':…}`. Its docstring is candid that the vocabulary does not
yet cover "this engine actively dissents" — a dissent and an absent engine are still the same
number. That is the right shape of honesty about an unfinished thing.

## C.2 — Output

**Target table** `kala_convergence`. **Grain**: one row per *(mode, peak_date, signal_id)* after a
per-substep dedup (`ka_sangam.py:879-887`) — **not** a natural key in the DB; `convergence_id` is
a bigint surrogate. Columns and semantics:

| column | semantics | qualification |
|---|---|---|
| `convergence_score` | the I-16 score, 0–1 | **not comparable across modes** — see F7 |
| `confidence_score` | `min(1.0, ICC/13)` | **unearned — F10** |
| `confidence_label` | I-21 absolute thresholds 0.75/0.45 | **degenerate for A/B — F11** |
| `confidence_label_relative` + `tier_basis='relative_uncalibrated'` | JL-014 within-chart percentile | the only discriminating tier; **not served — F11** |
| `independent_current_count` | hand-weighted boolean count | **not independence — F10** |
| `domain` | `domains_affected_array[0]` of the originating MSR signal | **first-domain-only — C.5** |
| `is_off_dasha_discovery` | Mode B flag | honest |
| `horizon_tier` | `'near'` (7y forward) / `'lifetime'` (birth+100y) | honest |
| `constituent_factors` (jsonb) | every current's value, plus `convergence_score_pre_trigger`, `trigger_suppressive_applied`, `trigger_weights_used` | **rich, and it does survive to the retrieval projection** |
| — | **no `ayanamsha_id` column at all** | the identity gap the prompt names, confirmed at schema level |

**Live counts.** Canonical chart: **0 rows.** Globally 20,497 across two other charts.

```sql
SELECT chart_id, count(*), count(*) FILTER (WHERE peak_date IS NULL), count(*) FILTER (WHERE domain IS NULL),
       min(convergence_score), max(convergence_score), avg(convergence_score)
FROM kala_convergence GROUP BY 1;
-- 1c826d5a-… | 17957 | 0 | 1656 | 0.0000 | 1.0000 | 0.4161
-- cb73cd3d-… |  2540 | 0 |    0 | 0.2589 | 0.3393 | 0.2803
```

**Status: ABSENT for the canonical chart.** `ka_sangam` has never produced a row for
482012f1 — which matters doubly because §4 of the DAG reconciliation records that `ka_sangam` is
one of the 12 assets whose `build_runs.plan_manifest` freeze-and-verify has **never fired**,
despite 522 build runs on this chart. The layer's chokepoint has neither data nor a proven
freeze on its most important chart.

## C.3 — Inputs

Declared `depends_on` (live, 10 edges): `ka_yojaka`, `ka_dasha_kala`, `ka_gochara`,
`ka_muhurta_seva`, `bo_laksana`, `ga_dashas`, `ga_strength`, `ga_positions`, `ga_tajaka`,
`bg_transit_rules`.

**Actual reads, traced from the writer:**

| Read | Line | Grain / convention |
|---|---|---|
| `kala_activation_predicates` ⋈ `bodha_msr_signals` | `ka_sangam.py:274-305` | per predicate; `ROW_NUMBER() OVER (PARTITION BY signature_class ORDER BY raw_dignity_score DESC NULLS LAST, content_hash ASC)` capped at 200/class |
| `bodha_msr_signals` (dignity, graha, house, domains) | `:337-352` | per signal |
| `chart_facts` (Moon nakṣatra, Moon sign, Lagna sign) | `:758-762`, `:1150-1156` | per fact |
| `public.charts` (lat/lng/timezone_id) | `:832-838` | per chart |
| `chart_dashas` (`MIN(start_date) WHERE level_n=1`) | `:869-874` | birth year derivation |
| `chart_facts` aṣṭakavarga bindus | `:997-1028` | SAVEPOINT-guarded |
| `kala_vedha_gochara` | `:1055-1073` | SAVEPOINT-guarded |
| `l1_tajik_varsha_year_lords` | `:1098-1120` | SAVEPOINT-guarded |
| `KaDashaKalaService.query(...)` | `engine.py:1113-1126` | service call, `max_level=3` |
| `KaGocharaService(swe)` / `find_aspect_events` | `ka_sangam.py:317-320`; `engine.py:1088` | **on-demand Swiss geometry** |
| `convergence_scores` (C13 school consensus) | — | **not queried by any live path** — `ka_sangam.py:989` keeps `school_consensus_by_domain` empty pre-U4. So C13 is structurally always 0/absent. |

**Declared vs actual — typed discrepancies:**

- `ka_gochara` (declared): **scheduling edge, not a computational read.** Sangam uses on-demand
  geometry (`KaGocharaService(swe)`), never `kala_gochara_windows*`. Confirms the Strategy against
  the registry. Type: *scheduling*.
- `ga_strength`, `ga_positions`, `bg_transit_rules`, `bo_laksana` (declared): reached
  **transitively** — via `bodha_msr_signals`, `chart_facts` and `kala_activation_predicates`
  rather than by direct table read. Type: *computation, indirect*. I did not attempt to falsify
  each; scope stated.
- `ka_muhurta_seva` (declared): reached as a **service** (`KaMuhurtaSevaService()`,
  `ka_sangam.py:322-326`), and it is the asset whose own `depends_on` was deliberately set to
  empty in LIVE by migration 676 while the seed still says 1. Type: *unresolved dynamic* — its
  own edge state disagrees across sources by accepted policy.

**Convention checks:**

- **Ayanāṃśa.** `engine.py:1097` reads `predicate.get('ayanamsha_id') or 'lahiri'` — a
  **default-on-missing** — and the resulting value is used for the daśā query but **never
  stored**: `kala_convergence` has no ayanāṃśa column (schema, C.2). So two rows computed under
  different ayanāṃśas are indistinguishable in the output, and a row computed under a defaulted
  `'lahiri'` is indistinguishable from one computed under an explicit one. *(Note: `chart_facts`
  elsewhere stores `'lahiri_chitrapaksha'`, not bare `'lahiri'` — `ka_sangam.py:993-995` documents
  that exact distinction as a prior bug (B6 fix). The engine's default is the bare string.)*
- **Timezone.** `_resolve_birth_location` (`ka_sangam.py:813-860`) **refuses to default to IST**
  and raises instead (`:858-862`) — CR-87 fail-loud, correct.
- **Sign-vs-house.** `moon_sign` is threaded through explicitly so the C11 vedha filter computes
  `transit_house` in the house-**from-Moon** frame (CR-102 fix, `ka_sangam.py:685,723`); the
  docstring at `engine.py:1060-1066` is candid that omitting it falls back to the old *bugged*
  sign-number behaviour rather than silently producing "a wrong-but-confident house number."
- **Intervals.** `_dasha_score_for_date` uses `ew.start_date <= peak_date <= ew.end_date`
  (`engine.py:1138`) — **closed on both ends**. A daśā boundary date therefore belongs to both
  adjacent periods. Whether that matches `chart_dashas`' own convention is **COULD NOT VERIFY**
  without reading the L1 writer's boundary rule; it is a one-line question with real consequences
  for sandhi windows.

**Upstream richness fetched then discarded — two instances:**

1. `domains_affected_array` is fetched in full (`ka_sangam.py:343`) and then reduced to
   `da[0] if da else None` (`:353`). Every additional domain is dropped at the source. And
   `ka_tulana`'s own input model has `domains: list[str]` (`services/ka_tulana/ranker.py:138`) —
   a downstream consumer that *can* take multiple domains is fed a single one.
2. `dignity_score` NULL → **0.5** (`ka_sangam.py:348`, and again as the `pred_dicts` default at
   `:360`). This is a NULL→mid-value substitution *inside the ranking key* that selects which 200
   predicates get computed at all. A signal with no dignity outranks any signal with a measured
   dignity below 0.5.

## C.4 — Consumers, and the mode-starvation finding

**Search scope:** `grep -rn -B3 -A12 'FROM kala_convergence' --include='*.py'` over
`pipeline/orchestrator/writers/`, `services/ka_tulana/`, `services/ka_temporal/`,
`services/ph_nimitta/`, `services/taranga_kernel/`; plus `grep -rln 'kala_convergence'` over
`platform-mcp/src` and `platform/src` (tests and generated JSON excluded).

| Consumer | Read | Does the decisive field survive? |
|---|---|---|
| **`ka_kala_darshana`** | `:28-31` `ORDER BY convergence_score DESC NULLS LAST LIMIT 750` | **No.** Drops `domain`, `independent_current_count`, `constituent_factors`, both relative-confidence fields. And **F7: 100% of its 750 rows are Mode C.** |
| **`ka_vighnakara`** | `:179-183` `ORDER BY convergence_score DESC NULLS LAST LIMIT 500` | **No.** Same drops. **F7: 100% Mode C.** |
| **`ka_taranga`** | `:111-114` `WHERE domain IS NOT NULL … ORDER BY window_start` | **No.** Silently excludes all NULL-domain rows — **1,656 of 17,957 (9.2%)** on chart 1c826d5a. No LIMIT, so coverage is otherwise complete; but it sees exactly one domain per window. |
| **`ka_jivana_parva`** | `:116-127`, no LIMIT | Mostly yes — but `LEFT JOIN LATERAL (SELECT signature_class … LIMIT 1)` at `:120-125` is an **unordered LIMIT 1** over `kala_activation_predicates` (§N.7 item 2 class). |
| **`ka_kalasutra`** | `:74-76` all rows with `signal_id IS NOT NULL`, then keeps max score per signal in Python (`:80-88`) | Yes for its purpose. Its docstring (`:6-10`) references "the ~99% NULL-date case" — measured live, `peak_date` is NULL on **0 of 20,497 rows**; the claim must refer to signals *without* a convergence row, not to NULL dates. Stale phrasing on a load-bearing docstring. |
| **`ka_tulana`** | in-memory `WindowInput` | `confidence_label: str = 'speculative'` is a **dataclass default** (`ranker.py:135`) — a row arriving without a label is silently the lowest tier rather than unknown. `domains: list[str]` (`:138`) can hold many; the source gives one. |
| **`ph_nimitta`** | `:337-348` `ROW_NUMBER() PARTITION BY domain … rn <= 50`, then `LIMIT 500` | **Best-behaved consumer in the set** — the per-domain quota (`_MAX_CONVERGENCE_PER_DOMAIN = 50`, `:38`) is exactly the structural fix `ka_kala_darshana`/`ka_vighnakara` lack. |
| `ph_nimitta` (second read) | `:710-715` nearest convergence within 90 days, `ORDER BY ABS(peak_date − detected_at) LIMIT 1` | **Unordered on ties.** No score or mode tiebreak; binds an *outcome* to an arbitrary one of several equidistant convergences. |
| **`mi_adhilepa`** (L5) | `:297` `SELECT convergence_id FROM kala_convergence WHERE chart_id = %s **LIMIT 500**` | **Unordered LIMIT 500** — a calibration multiplier is applied to 500 arbitrary convergences, heap order. This is the worst single truncation in the set, because it is silent *and* it feeds calibration. |
| `mi_kula`, `ph_muhurta`, `ph_pratikara`, `ph_sodhana`, `taranga_kernel`, `ka_temporal/date_resolver` | — | not traced; scope stated. |
| **`query_convergence_windows`** (retrieval) | `query_convergence_windows.ts:118-129` `ORDER BY convergence_score DESC NULLS LAST LIMIT $topK`, with a parallel `COUNT(*)` and honest pagination (`:135,147`) | **Mostly yes** — `constituent_factors` **does** survive (`:125`). **Dropped: `confidence_label_relative`, `tier_basis`** (F11). `density_contract` occurrences in the file: **0** (§N.6). |
| `kala_temporal.ts` (MCP) | — | not traced. |

### F7 — the measurement

```sql
WITH t AS (SELECT mode FROM kala_convergence WHERE chart_id='1c826d5a-…'
           ORDER BY convergence_score DESC NULLS LAST LIMIT 500)
SELECT mode, count(*) FROM t GROUP BY 1;   -- C | 500
-- same query at LIMIT 750:                -- C | 750
```

**Mode A and Mode B rows never reach `ka_vighnakara` or `ka_kala_darshana` at all.** The mechanism
is exactly the one D-3 FIX-PSEL diagnosed one level up and documented at length in
`ka_sangam.py:249-266`: a ranking key that is systematically higher for one class, plus a flat
`LIMIT`, equals total starvation of the others. The fix was applied to *predicate selection* and
not to *consumer projection*. The distribution behind it:

```sql
SELECT mode, horizon_tier, count(*), string_agg(DISTINCT confidence_label,','),
       min(independent_current_count), max(independent_current_count), avg(independent_current_count)
FROM kala_convergence GROUP BY 1,2 ORDER BY 1,2;
```

| mode | tier | rows | `confidence_label` | ICC min/max/avg |
|---|---|---|---|---|
| A | lifetime | 1,223 | **speculative only** | 2 / 6 / 3.37 |
| A | near | 322 | **speculative only** | 2 / 5 / 3.16 |
| B | lifetime | 958 | **speculative only** | 2 / 5 / 3.31 |
| B | near | 232 | **speculative only** | 2 / 5 / 3.03 |
| C | lifetime | 510 | high, moderate | 1 / 1 / 1.00 |
| C | near | 360 | high, moderate | **1 / 1 / 1.00** |
| D | lifetime | **16,892** | moderate, speculative | 1 / 1 / 1.00 |

Read that table as an epistemics statement: **the rows with the most witnesses (A/B, ICC 2–6) are
labelled `speculative` without exception, and the rows with exactly one witness (C, ICC 1) are the
only ones ever labelled `high`.** The confidence label is anti-correlated with the evidence count.

### F8 — Mode D duplication

```sql
SELECT mode, count(DISTINCT signal_id), count(DISTINCT peak_date), count(*)
FROM kala_convergence WHERE chart_id='1c826d5a-…' GROUP BY 1;
-- A|41|733|1545   B|41|575|1190   C|120|15|870   D|26|552|14352
SELECT count(*) FROM (SELECT DISTINCT peak_date, window_start, window_end, convergence_score
                      FROM kala_convergence WHERE mode='D' AND chart_id='1c826d5a-…') t;  -- 1104
```

14,352 Mode D rows → **1,104 distinct window tuples**, ~13× duplication. The code comment at
`ka_sangam.py:722-726` states the intent precisely — "running it for every predicate produces N×K
duplicate windows with different signal_ids that bypass the dedup key check (which includes
signal_id)" — and the guard it installs is `if pred_dicts and pred_dict is pred_dicts[0]`
(`:726`). On the lifetime path the writer calls `_generate_windows(pred_dicts=[pred], …)`
(`ka_sangam.py:591`) — a **one-element list**, so `pred_dict is pred_dicts[0]` is unconditionally
true, and Mode D runs once per lifetime substep with a different `signal_id` each time. The guard
prevents the defect it names only on the `near` path. **70% of the table is a known, named,
documented defect that the installed guard does not reach.**

## C.5 — Known defects (file:line)

| # | Defect | Class | Cite |
|---|---|---|---|
| S-1 | Mode D duplicated ~13× on the lifetime path; guard vacuous. | vacuous guard | `ka_sangam.py:591` vs `:721-726` |
| S-2 | Top-N consumer projections are 100% Mode C — total A/B starvation. | truncation cap | `ka_vighnakara.py:179-183`; `ka_kala_darshana.py:28-31`; SQL C.4 |
| S-3 | `mi_adhilepa.py:297` — **unordered `LIMIT 500`** feeding a calibration multiplier. | unordered LIMIT | `mi_adhilepa.py:294-309` |
| S-4 | `ph_nimitta.py:710-715` — `LIMIT 1` ordered only by date distance; ties arbitrary; binds outcome→convergence. | unordered LIMIT 1 | as cited |
| S-5 | `ka_jivana_parva.py:120-125` — `LATERAL … LIMIT 1` with no ORDER BY on `kala_activation_predicates`. | unordered LIMIT 1 (§N.7 item 2) | as cited |
| S-6 | `dignity_score` NULL → **0.5** in the predicate ranking key. | NULL→mid default in a selection key | `ka_sangam.py:348,360` |
| S-7 | `ka_tulana` `WindowInput.confidence_label` defaults to `'speculative'`. | default substitution | `ranker.py:135` |
| S-8 | `ayanamsha_id` defaults to bare `'lahiri'` and is **never stored**. | identity gap + default | `engine.py:1097`; `kala_convergence` schema |
| S-9 | `domain = domains_affected_array[0]`; `ka_taranga` then drops NULL-domain rows entirely. | first-domain-only + silent exclusion | `ka_sangam.py:353`; `ka_taranga.py:112` |
| S-10 | `confidence_score = ICC/13` where `'transit'` is the tautology `mode in ('A','B')`. Nothing measures independence. | **§N.8 unearned signal** | `ka_sangam.py:908,931,965`; `engine.py:850-946` |
| S-11 | `confidence_label` degenerate (100% speculative for A/B) and **anti-correlated with ICC**; the discriminating `confidence_label_relative` is computed, stored, and **not served**. | degenerate tier + projection loss | `engine.py:789-849`; `query_convergence_windows.ts:118-129` |
| S-12 | A mode that raises is logged at `warning` and skipped (`ka_sangam.py:654,690,716,738`); events below `HIGH_CONFIDENCE_ORB_THRESHOLD` (= 0.45, `engine.py:968`) are `continue`d (`engine.py:1171` Mode A, `:1400` Mode B). **A caller cannot distinguish "no window" from "the search failed" from "results were filtered out."** | missing coverage state | as cited |
| S-13 | C13 school consensus is structurally always absent (`ka_sangam.py:989`, pre-U4) yet counts as a potential independent current in the ICC denominator of 13. | denominator includes an unreachable term | as cited |
| S-14 | `ka_sangam.py:1150-1156` — `WHERE … fact_key='sign' LIMIT 1` with no ORDER BY. `fact_key` *is* pinned (so it clears the `fact-category-pin-lint` bar) but the order is not total across build generations. | §N.7 item 2, residual | as cited |
| S-15 | No `ayanamsha_id` and only one `domain` in the natural key — two rows differing only in ayanāṃśa or in secondary domain are indistinguishable. | identity | schema C.2 |

**CORRECTION (F9) — two of the prompt's cited caps are stale or mis-scoped:**

- The flat `ORDER BY dignity_score DESC NULLS LAST, p.id ASC LIMIT 200` at ~`:247` **no longer
  exists as code.** It survives only inside the explanatory comment at `ka_sangam.py:247-250`
  describing the *prior* query. The live query (`:274-305`) is a per-`signature_class`
  `ROW_NUMBER()` capped at 200/class, feeding a Python quota selector
  (`_select_top_predicates_with_class_quota`, `:166-221`) that guarantees every populated class a
  floor. The tiebreak was also changed from insertion-order `p.id` to a content-derived `md5`
  hash — a real reproducibility fix.
- `engine.py:1102`'s `[:1]` is **not on the scoring path.** It resolves `domain_lord` for the C12
  tājika current only, and only when `predicate['domain_lord']` is absent. The daśā query at
  `engine.py:1113` uses `set(dasha_rule.get('constituent_lords', []))` — the **full** set. So the
  answer to the prompt's question 4 ("is Sangam's scoring currently built on a single lord where
  the rule has several?") is **no for the daśā prior, yes for the C12 tājika current only.** That
  is a much smaller defect than the prompt assumes, and the brief should say so rather than
  inherit the larger claim.

**Per-cap disposition, as far as the evidence supports:**

| cap | value | classification on the evidence | what a caller learns today |
|---|---|---|---|
| near predicates | 200/class candidate pool + quota select | **performance**, with an explicit anti-starvation design | nothing — no coverage field |
| lifetime predicates | 60 | **performance** | nothing |
| `_LIFETIME_MAX_ROWS` | 40,000 | **performance** | nothing |
| `max_level=3` | MD/AD/PD only | **semantic or accident — undetermined.** PrD/level-5 is documented elsewhere in the codebase as never computed by L1 (`stage3_clocks.py:1005-1008`), which would make 3 vs 4 the real question. | nothing |
| `[:1]` constituent lords | 1 | **accident, narrow scope** (C12 only) | nothing |
| consumer `LIMIT 500`/`750` | — | **accident with a severe effect** (F7) | nothing |
| `mi_adhilepa LIMIT 500` | unordered | **accident** | nothing |
| `HIGH_CONFIDENCE_ORB_THRESHOLD` filter | — | **semantic** (sub-threshold events are not evidence) | nothing — the count of filtered events is never reported |

## C.6 — Build reality

**Can it build today? Yes, on privileges.** Every unguarded read (`kala_activation_predicates`,
`bodha_msr_signals`, `chart_facts`, `public.charts`, `chart_dashas`, `build_substep_progress`) is
inside `data_plane_builder`'s grant set per the privilege matrix; the three soft dependencies
(`chart_facts` aṣṭakavarga, `kala_vedha_gochara`, `l1_tajik_varsha_year_lords`) are **correctly**
SAVEPOINT-guarded with matching `RELEASE`/`ROLLBACK TO` (`ka_sangam.py:997-1034`, `:1055-1079`,
`:1098-1126`) — **this writer is the codebase's correct example of the pattern Kshetra's cohort
path gets wrong (K-6).** `convergence_scores` is never queried (pre-U4).

**Cost.** Registry `estimated_seconds = 463`; `target_floor = 14,868`. The plan is 1 `near`
substep + 1 substep per lifetime predicate (≤60), each a 100-year convergence scan
(`ka_sangam.py:400-406`). What drives cost is the per-predicate Swiss `find_aspect_events` over a
100-year horizon, multiplied by up to 60 predicates. The writer carries a purpose-built
cross-attempt resume ledger (`:408-446`, `_KA_SANGAM_RESUME_VERSION = 2`) precisely because the
substeps outlast a proxy connection — and each lifetime substep deletes only its own `signal_id`'s
rows (`:576-579`) so a resumed run is byte-identical to an uninterrupted one. That is careful,
correct engineering.

**Unguarded reads that would hard-fail: none found.** **BUILD-PROTECTED guard: none.**

**The real build risk is not privileges — it is the unexercised freeze.** `KALA_DAG_RECONCILIATION
§4`: `ka_sangam` is among the 12 of 23 identities that have **never** been captured by a surviving
`build_runs.plan_manifest`. The campaign's freeze-and-verify protection has never run for the
layer's chokepoint.

## C.7 — The elevation question

**What would NOT be value.** Raising `_MAX_PREDICATES` from 200. Adding a fifth mode. Extending
the lifetime horizon. All three produce more rows into a table whose top-750 projection is already
100% one mode and 70% duplicates.

**Four elevations, distinguished as the prompt requires:**

1. **REPAIR A DEFECT — fix the Mode D guard and the consumer truncation.** These are one problem
   seen twice. **Consumer capability unlocked: `ka_kala_darshana` and `ka_vighnakara` begin to see
   daśā×transit convergences at all** — today they cannot, so *every* downstream obstruction
   judgment and temporal view in L3 is built on sign-ingress windows exclusively. This is not an
   improvement to Sangam; it is the difference between seven downstream assets consuming Sangam's
   actual work and consuming a proxy for it. The fix on the consumer side is the one `ph_nimitta`
   already implements (`ROW_NUMBER() PARTITION BY …`): partition the top-N by **mode** (and by
   domain), so no mode can be starved. **This is the highest-value single change in the lane.**
2. **QUALIFY EXISTING DATA — serve `confidence_label_relative`, retire or re-fit the absolute
   one, and replace `confidence_score` with something a detector produces.** §N.8 is unambiguous:
   a signal whose detector cannot make it read false is null, not green. `confidence_score = ICC/13`
   with a tautological `transit` term qualifies. **Consumer capability unlocked: a caller can
   distinguish a five-witness window from a one-witness window** — which is the entire claim the
   asset's name makes.
3. **SURFACE DISCARDED RICHNESS — carry all domains, and add ayanāṃśa to the identity.**
   `ka_tulana` already models `domains: list[str]` and is fed one. **Consumer capability unlocked:
   cross-domain convergence — "this window is simultaneously a career and a relationship
   window" — which is exactly the Cross-Domain Linkage claim B.11 rests on, and which
   `domains_affected_array[0]` makes structurally unrepresentable today.**
4. **ADD GENUINELY NEW EVIDENCE — a real independence model.** This is the Q3 epistemics question
   and it is the only one that needs the native's doctrine rather than code. The current
   `independent_current_count` is a scoring convention wearing an epistemic name. Until it is
   replaced, **no convergence count in this system means what it says**, and seven assets inherit
   that.

**Ablations.**

- *For (1):* rebuild `ka_kala_darshana` twice — once on the current top-750, once on a
  mode-partitioned top-750 — and compare its output rows. If `kala_darshana` is materially the
  same either way, then Mode C really was carrying the signal and A/B add nothing, which would be
  a finding in its own right. If it changes substantially, the starvation was destroying
  information.
- *For (4):* take any window with ICC = 5 and **delete one current at a time**, recomputing the
  score. If removing a current that the coupling table calls "independent" moves the score by the
  same amount as removing one it calls "coupled," the coupling table is decorative.
- *For (3):* count how many `kala_convergence` rows would change `domain` if the array's *second*
  element were used instead of the first. If that number is large, first-domain-only is not a
  simplification, it is a coin flip. **Cheap, one query, not run here.**
- *For Mode D generally:* since Mode D is predicate-agnostic and 70% duplicated, delete the
  duplicates and re-run any downstream consumer. If nothing downstream changes, Mode D's
  contribution is 1,104 windows, not 16,892 — and every rows-based statement about this asset is
  overstated by an order of magnitude.

## C.8 — Open decisions for the native (Sangam)

| # | Decision | Options and costs |
|---|---|---|
| S-A | **What is an independent witness?** (prompt Q3) | (a) keep the hand-weighted coupling table but rename the field so it stops claiming independence — cheapest, honest, and it stops seven assets inheriting a false claim; (b) define lineage groups and count groups, not currents — bookkeeping, and the strategy's L3-U02 already warns this is not *demonstrated* independence; (c) require empirical decorrelation before a current counts — correct, and needs outcome data that L5 does not yet have. **Doing nothing is choosing (a) without saying so.** |
| S-B | **How does a caller learn a cap bound?** (prompt Q8) | Every cap in C.5's table is currently invisible. Options: a `coverage` object per response (`searched / returned / truncated / failed_modes`), vs. a `judgment_flags`-style entry (§N.6 item 1's pattern, already used by `ganita_yogas_get`). The second has precedent in this codebase and should probably win on consistency. |
| S-C | **Is the top-N partitioned by mode, by domain, by both — or is the score made cross-mode comparable instead?** | Partitioning is a small change in four SQL statements and fixes F7 immediately. Making the score comparable across modes is the deeper fix and requires deciding what a sign-residence window and a same-day aspect mean on one scale — which may not be answerable. **They are not alternatives: partition now, and treat comparability as a separate, possibly-unanswerable question.** |
| S-D | **Does Mode D survive, and in what form?** | It is predicate-agnostic, sign-level, ICC=1, 70% of the table, and 13× duplicated. Options: (a) fix the guard and keep it as a *modifier* rather than a window-producing mode; (b) keep it as a mode but exclude it from any ranked projection; (c) retire it. Each needs its own qualified meaning per the prompt's Q5. |
| S-E | **Ayanāṃśa in the natural key?** | Adding it makes rebuilds under a different ayanāṃśa non-destructive and makes the identity honest — but multiplies row counts per ayanāṃśa and changes every consumer's dedup assumption. Not adding it means the default at `engine.py:1097` is permanently unrecoverable from the data. |
| S-F | **Multi-domain representation.** | (a) `domains text[]` on `kala_convergence` — `ka_taranga`'s `WHERE domain IS NOT NULL` and `ka_tulana`'s `domains` list both already want it; (b) a child table; (c) keep `domain` and add `domains_all`. The strategy forbids one-domain flattening, so (a) or (b); (c) is the migration-free compromise that keeps the flattening alive. |
| S-G | **`max_level=3` — semantic or accident?** | If L1 genuinely never computes PrD, then 3 is forced and should be *documented* as forced rather than left as a literal. If L1 does compute level 4, this is silently discarding a level of daśā precision on every Mode A window. **Settling this is one query against `chart_dashas`.** |
| S-H | **Is the closed-closed daśā interval test right?** (`engine.py:1138`) | Closed-closed double-counts boundary dates. Half-open `[start, end)` would match the usual convention. Needs a check against L1's own boundary rule before changing anything — a mismatch in *either* direction is worse than a consistent choice. |
| S-I | **P4 shared geometry.** | `transit_search.py` is imported by Kshetra, Sangam, the Gochara family, and frozen L0 `bg_sky_calendar`. v0.3 R2 already rules that the new kernel must **not** import it and must not edit it. That ruling should be adopted here verbatim rather than re-litigated, so Sangam's elevation does not become a cross-stream invalidation. |
| S-J | **The unexercised freeze.** | `ka_sangam` has never had a surviving `plan_manifest`. Before any elevation, one dispatch whose manifest is captured and verified — otherwise the campaign's own integrity mechanism remains unproven on its most important asset. |

---

## §D — What is NOT settled, plainly

1. **COULD NOT VERIFY: the null programme's shift-grid semantics** (circular / reflected /
   truncated). It determines `null_p`'s denominator and therefore what the native's Q4 is even
   asking. `stage5_null.py:584-600` and the `kala_field_null` schema constrain it but do not
   settle it.
2. **COULD NOT VERIFY: whether `kala_gochara_windows.generation='3.0'` (914 rows) and
   `kala_gochara_windows_v2.generation='g3_utkarsha'` (914 rows) are the same windows.** Needs a
   row-content comparison I did not run.
3. **COULD NOT VERIFY: whether Kshetra's `refinement_depth = 0` everywhere is correct silence or
   a dormant code path.** Indistinguishable from the data (K-5).
4. **COULD NOT VERIFY: whether `chart_dashas` uses closed or half-open period boundaries**, which
   `engine.py:1138`'s closed-closed test must match (S-H).
5. **COULD NOT VERIFY: whether L1 computes daśā level 4**, which decides whether `max_level=3` is
   forced or lossy (S-G).
6. **Not traced, scope stated:** the century materialiser's read closure (inherited from the
   privilege matrix); `mi_bhara`'s consumption of the field; `mi_kula` / `ph_muhurta` /
   `ph_pratikara` / `ph_sodhana` / `taranga_kernel` / `ka_temporal` reads of `kala_convergence`;
   `kala_temporal.ts`; and the Gochara MCP coverage-branch line numbers, which are inherited from
   v0.3's `[A]` evidence rather than re-verified.
7. **Every method question remains the native's**, at acharya standard: what a convergence is,
   what an independent witness is, whether the continuous field is the right abstraction, and
   whether Mode C's sign-residence and Mode A's exact aspect belong on one scale at all.

---

*Produced read-only. No row was written, no migration authored or edited, no build dispatched, no
campaign evidence event emitted, no guard weakened, no credential echoed. Every DB statement was a
single-statement `SELECT` under `default_transaction_read_only = on` (confirmed at session open),
and every one was an aggregate, a schema lookup, or an identity/timestamp column — no narrative,
interpretive or JSONB payload column was ever selected.*
