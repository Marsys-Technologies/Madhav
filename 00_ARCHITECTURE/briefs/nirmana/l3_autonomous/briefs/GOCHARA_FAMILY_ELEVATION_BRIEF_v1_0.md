---
artifact: GOCHARA_FAMILY_ELEVATION_BRIEF
canonical_id: GOCHARA_FAMILY_ELEVATION_BRIEF
version: "1.0"
status: SUPERSEDED
superseded_by: GOCHARA_FAMILY_ELEVATION_BRIEF_v1_1.md  # re-shaped to the asset/interface contract §1–§8 and reconciled to W0_DELTA_GOCHARA_FAMILY; identity dispute withdrawn (census #4/#6)
date: 2026-09-22
brief_for: "ka_gochara · ka_gochara_resonance · ka_gochara_v3_century_materialize · ka_gochara_sweep (retired)"
shape: Strategy §6.4 asset packet + VA §13.3 + Strategy §3 field dossier
supersedes:
  - GOCHARA_FAMILY_ELEVATION_PLAN_v1_0.md — its D-2 SEQUENCE only (§1.3 below); all else carried forward
  - GOCHARA_FAMILY_ELEVATION_PLAN_v0_3.md — SUPERSEDED on 2026-09-22 before this brief; see §1.1
reconciles:
  - 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_L3_KA_GOCHARA_v1_0.md (June 2026, superseded campaign plan — kernel retained, §6)
governed_by:
  - 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_v3_0.md
  - briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md (rows L3-A05, A13, A14, H01; §5 P3)
  - briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md
  - briefs/nirmana/MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md (F01/F04/F06/F08/F09/F12/F13/F14/F17/F19)
  - briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_v2_0.md (§10.2, §13.3)
  - l3_autonomous/KALA_ASSET_BRIEF_CONTEXT_v1_0.md
  - l3_autonomous/KALA_PRE_ELEVATION_CRITICAL_REVIEW_v1_0.md (C4, §7)
depends_on_phase_1:
  - "1.1 Close B1 — registry target_table truth, is_active on Clear, real guard on generation='v1'"
  - "1.2 Grants — incl. SELECT on kala_gochara_windows_archive_20260805 for the restore-drill identity"
consumes_phase_0_1_deliverables: [KALA_BASELINE_v1_0, KALA_COST_PROFILE_v1_0, KALA_IO_USE_MATRIX_v1_0, KALA_PHASE2_DECISIONS_v1_0]
independent_reviewer: "required, not yet assigned — see §15"
does_not_authorize: >
  No code, data, migration, registry, campaign or lifecycle change. No asset retirement. No guard
  weakening. No orchestrator-contract change (§N.2). No release of the century hold. The 2026-08-21
  standing order (no gochara re-materialization without fresh explicit authorization) stands.
evidence_basis: >
  Source read at worktree /Users/Dev/madhav-l3/integration @ 5d8252dbe. Executed evidence in
  briefs/evidence_gochara/ (E1–E8). Live aggregates are inherited from ASTRA_REVIEW_GOCHARA_PLAN_v0_2
  §B (2026-09-20 16:02–16:14 UTC) and from the readiness exercise as reported in the input context —
  the database was NOT reachable from this session (127.0.0.1:5433 refused), so no live value here is
  freshly re-measured. Every such value is tagged.
---

# Gochara family — elevation brief

Evidence tags: `[X]` executed here · `[S]` source at the pinned revision, read this session ·
`[L]` live measurement inherited from the review or readiness exercise, **not** re-measured here ·
`[R]` repository record · `[I]` inference · `[U]` unmeasured.

---

## 1. Status correction and what this brief supersedes

### 1.1 The pointer in the task brief is stale
The task names `GOCHARA_FAMILY_ELEVATION_PLAN_v0_3.md` as `PROPOSAL_FOR_NATIVE_RULING`. On disk it
is `SUPERSEDED` `[S]`. The live artifact is **`GOCHARA_FAMILY_ELEVATION_PLAN_v1_0.md`, status
`NATIVE_RATIFIED_PLAN`, ratified 2026-09-22**, which already closed three decisions (D-1 sidereal
convention, D-2 guard policy, D-3 scoring split) and carried R1–R10. This matters: superseding a
ratified decision needs the native to re-rule, which §1.3 asks for. Everything else in v1.0 stands.

### 1.2 What survives contact with the new evidence
D-1 (Swiss sidereal mode, Lahiri) · D-3 (six pre-approved honesty fixes; four method calls deferred)
· R1, R2, R3, R4, R5, R7, R8, R9, R10 — all survive unchanged in substance. R10 (registry
reconciliation) is **promoted from "early" to Phase-1 blocking**, because the instrument it corrects
is wired to a destructive path. R3's `precision_class` is re-expressed in §5 to bind to F04/F06 and
a comparability flag, so it cannot be mistaken for the forbidden confidence scalar.

### 1.3 What this brief supersedes — one item, and it needs a fresh ruling
**v1.0 D-2's sequence is superseded.** D-2 ruled: *restore drill first, then a generation-keyed
guard.* Two facts make that order wrong:

1. **The drill cannot run.** As `data_plane_builder` the restore identity has no `SELECT` on its own
   recovery source `kala_gochara_windows_archive_20260805` `[L]`. v1.0 R6/WP10 does not name this.
2. **The deletion path is live and ordinary-user-reachable** (§3). Sequencing a weeks-long recovery
   exercise *before* closing a reachable `DELETE` leaves the exposure open for the duration.

**Proposed replacement (native ruling requested):** close the path first — it moves no data and needs
no grant — then run the drill under a grant obtained in Phase 1.2, then add the guard.
Order: **(a) exclusion + registry truth → (b) grant → (c) restore drill → (d) generation-keyed guard.**

---

## 2. Scope and what each asset is

| Asset | Role | Writes `[S]` | Registry `target_table` `[S]` | Strategy row |
|---|---|---|---|---|
| `ka_gochara_resonance` | Per-chart target discovery — which natal points matter for which event class | `gochara_resonance_map` | same | L3-A05, W2 |
| `ka_gochara` | Per-chart windows, progressive ±3 y horizon | **only** `kala_gochara_windows_v2` @ `generation='2.0'` (`ka_gochara.py:120,336,362`) | `kala_gochara_windows` — **wrong** | L3-A13, W3 |
| `ka_gochara_v3_century_materialize` | Century windows, 27 classes, era⊃month⊃day hierarchy | **both** `_v2` @ `g3_utkarsha` **and** `kala_gochara_windows` @ `3.0` | `kala_gochara_windows_v2` — partial | L3-A14, W3 after hold |
| `ka_gochara_sweep` | **Retired.** Historical corpus; `@register` removed, no writer exists | — (unrebuildable) | `kala_gochara_windows` | L3-H01, outside active DAG |

Live population `[L]`: `kala_gochara_windows` 40,117 rows = **38,287 at `v1`** + 1,830 at `3.0`;
`kala_gochara_windows_v2` 1,993. Authority = `'3.0'` for both canonical charts, so **no `2.0` row is
served today**.

---

## 3. The safety findings, with the live-path test applied (context §7)

### B1 — the Clear path reaches the unrebuildable snapshot. CONFIRMED, and the mechanism is not the one the task brief names

**Confirmed in source, this session** `[S]`:
- `clear/route.ts:93` — `allowedScopes = isSuperAdmin ? ['per_chart','global'] : ['per_chart']`. The
  sweep row is `scope='per_chart'`, `layer='kala'`, so an ordinary authenticated chart owner reaches it.
- `clear/route.ts:114-117` and `clear/execute/route.ts:84-88` — both load
  `SELECT … FROM asset_registry ORDER BY layer, sort_order`, with **no `is_active` and no
  `catalog_status` filter**. A RETIRED asset is in scope.
- `clearScopeFilter.ts` layer branch — `registry.filter(r => r.layer === scopeTarget && allowedScopes.includes(r.scope))`. No lifecycle filter either.
- `clear/execute/route.ts:174-182` — `DELETE FROM ${asset.target_table} WHERE chart_id = $1` fallback.
- `build_protected_assets` empty; no non-internal trigger on any `kala_*` table `[L]`.

**Correction to the task brief — the resolution order matters.** `clear/execute/route.ts:160-172`
resolves a clear spec in strict precedence: `EXPLICIT_CLEAR_OPS` → **`deriveDeleteSqlFromCountSql(count_sql)`**
→ `target_table` fallback `[S]`. No gochara asset has an `EXPLICIT_CLEAR_OPS` entry `[S]`.
`deriveDeleteSqlFromCountSql` (`lib/cockpit/assetClearSpec.ts:29-46`) is a prefix swap that
**preserves the whole WHERE clause**, returning null only on a `JOIN` or a non-matching prefix `[S]`.
Therefore:

| Asset | count_sql `[S/L]` | Derived DELETE | Reaches the protected rows? |
|---|---|---|---|
| `ka_gochara_sweep` | `… FROM kala_gochara_windows WHERE chart_id=$1 AND generation='v1'` | `DELETE FROM kala_gochara_windows WHERE chart_id=$1 AND generation='v1'` | **YES — exactly and only them** |
| `ka_gochara` | `… FROM kala_gochara_windows_v2 WHERE chart_id=$1 AND generation='2.0'` (set by migration 670 §4 M6 `[S]`, live-confirmed `[L]`) | `DELETE FROM kala_gochara_windows_v2 WHERE chart_id=$1 AND generation='2.0'` | **No** — and `target_table` is never consulted while `count_sql` is non-null |
| `ka_gochara_v3_century_materialize` | `… FROM kala_gochara_windows_v2 WHERE chart_id=$1 AND generation LIKE 'g3_%'` | DELETE on `_v2` for `g3_%` | No — but it **orphans** its own `3.0` rows in the main table, which its clear spec never names |

**So the task brief's inference — *"excluding retired assets would not save those rows — the active
row points at the same wrong table"* — does not hold.** The active row's *pointer* is wrong, but the
pointer is unreachable: `count_sql` wins, and migration 670 already corrected it. The live hazard runs
through **`ka_gochara_sweep`'s own `count_sql`**, which is not a lie at all — it is an accurate
`count_sql` for a retired asset, mechanically transformed into a precisely-targeted `DELETE`.

**Consequence for the fix.** An `is_active`/`catalog_status` exclusion on the two Clear registry
queries is **necessary and, for this hazard, sufficient** — it removes the only asset whose clear spec
resolves onto `generation='v1'`. Correcting `target_table` remains required for separate reasons
(§4), but it is **not** the control that closes B1, and closing B1 must not wait on it.

**Do not, however, "fix" `ka_gochara.target_table` to `_v2` in isolation.** `_v2` is itself shared:
an unscoped `DELETE FROM kala_gochara_windows_v2 WHERE chart_id=$1` would take the century's
`g3_utkarsha` staging corpus with it. Any `target_table` correction must land together with the
guarantee that the fallback path is generation-scoped or unreachable `[I]`.

**Live-path test.** The route is a deployed HTTP endpoint reachable by any authenticated user holding
chart permission; the path is live by construction. Whether it has ever been *invoked* against a
canonical chart is `[U]` — no log or audit evidence was available to this session.

### B2 — an unearned signal sits in the destructive path. CONFIRMED
`clear/execute/route.ts:95-96` states *"kala_gochara_windows additionally carries a DB-level trigger
guard (migration 540) as defense-in-depth"* `[S]`. Migration 588 dropped
`trg_kala_gochara_windows_protect_row`, `…_protect_truncate`, `…_protect_gen3_row`, dropped all three
trigger functions, and emptied `build_protected_assets` `[S]`; applied 2026-08-23 `[L]`. No migration
after 588 recreates a trigger on `kala_gochara_windows` `[S]`. The comment asserts a detector that
does not exist — CLAUDE §N.8, in the one code path where being wrong destroys data.

### B3 — the restore drill cannot restore. CONFIRMED, inherited
`data_plane_builder` has no `SELECT` on `kala_gochara_windows_archive_20260805` `[L]`. Compounding
it: the two retained archives together match only **35,620 of 38,287** current `v1` ids `[L]`, and the
dump named by migration 588 has never been restore-tested — `pg_restore -l` is a listing `[L]`.
Recovery is therefore **unproven at three independent points**: permission, coverage, and execution.

### B4 — correction: the century materialiser's "BUILD-PROTECTED" state is a residue, not a guard

The task brief says *"the century materialiser is in error behind a working BUILD-PROTECTED guard —
do not weaken it"*. That is contradicted by the task brief's own positive control (*"not one
non-internal trigger on any `kala_*` table"*) and by source `[S]`:

- `BUILD-PROTECTED` is the `RAISE EXCEPTION` message text of the migration-540/556/566 triggers `[S]`.
- Migration 588 dropped exactly those triggers and their functions `[S]`.
- Migration 588's own header records the cause: the registry protected `generation='3.0'` under
  `asset_id='ka_gochara'` while the writer producing those rows is
  `ka_gochara_v3_century_materialize`, so *"the trigger could not tell a legitimate write from a
  destructive one, and left that writer in a permanent BUILD-PROTECTED error on the native chart
  (Defect D-02)"* `[S]`.
- No orchestrator-side check on `build_protected_assets` exists in `python-sidecar` `[S]`.

**Therefore the stored error state is a stale string from before 2026-08-23. There is no live guard
to weaken.** This is the *second* unearned signal in this family, and the more dangerous reading:
believing a guard is enforcing the hold when only lane discipline is. The hold in L3-A14 is real as a
*policy*; its enforcement is absent. §11 proposes restoring enforcement as part of Phase 1, keyed on
(table, generation) so it cannot repeat Defect D-02.

*I flag this as a disagreement with my instructions, not a licence: I am not weakening anything. The
instruction "do not weaken it" is preserved in the strongest available form — make the protection
real, then it can be relied on.*

### B5 — new finding: a live non-determinism in this family's own writer
`ka_gochara.py:268` — `now_date = date.fromisoformat(now_date_str) if now_date_str else date.today()`
`[S]`. `services/w2g/materialize.py:140` deliberately makes `today` a parameter *"never `date.today()`
called internally"* `[S]`; the writer defeats that discipline one layer up. Consequences:
- The ±3-year progressive horizon **moves with the wall clock**, so an unchanged chart rebuilt on two
  days produces different rows. Context §4: *"rebuild-freely is only safe if rebuild is deterministic."*
- It defeats migration 1018's `output_digest_spec` for this asset: the digest would report drift where
  nothing changed `[I]`.
This is the context §4 defect class, in my asset. The columns themselves are `DATE`, not
`timestamptz` `[S]`, so the 5.5-hour naive-instant defect does **not** apply here.
**Live path:** reached whenever `ctx.config['now_date']` is absent — orchestrator-supplied, so
reachability depends on the dispatch path; not verified from here `[U]`.

---

## 4. The identity dispute — six instruments, and which is authoritative

| # | Instrument | Says | Detector behind it? |
|---|---|---|---|
| 1 | **The writer's own DML** (`ka_gochara.py:120,336,362`) `[S]` | `_v2` @ `'2.0'` | it *is* the fact |
| 2 | `asset_registry.count_sql` (migration 670 §4 M6) `[S][L]` | `_v2` @ `'2.0'` | yes — executed by the cockpit stats route; and by the Clear derivation |
| 3 | `asset_registry.integrity_check_sql` (migration 670) `[S]` | `_v2` @ `'2.0'`, explicitly *"written for the asset AS THE WRITER BEHAVES"* | yes — executed |
| 4 | `asset_output_digest_specs` (migration 1018) `[S]` | relation `kala_gochara_windows_v2`, `where_equals generation='2.0'` | yes — executed |
| 5 | `asset_registry.target_table` `[S]` | `kala_gochara_windows` — **wrong** | **no** — a bare pointer nothing validates |
| 6 | `asset_registry_seed.ts:2117-2125` `[S]` | `kala_gochara_windows` — **wrong**; would restore #5 on a reseed | no |

**Proposed resolution — this is not a two-way authority contest.** Instruments 1–4 agree. The
question *"cockpit `count_sql` or the migration-1018 digest"* has no conflict to resolve: they agree
with each other and with the writer, and they answer **different** questions — `count_sql` is the
*serving/quantity* instrument (CLAUDE §N.4 cockpit-truth), the digest spec is the *content/determinism*
instrument. Both are authoritative in their own dimension.

The outliers are #5 and #6, and they are not rival authorities — they are **an unqualified
declaration with no detector**, which is why it drifted and why nothing caught it. Proposal:
- **Ground truth** = the writer's DML.
- **Declared authority** = the instrument that is executed and compared. A declaration with no
  detector may not outrank one that has one (§N.8 generalised).
- **`target_table` should stop being a second, contradicting declaration of the same fact.** Preferred
  end state: it is either derived from, or validated against, `count_sql`/the digest spec — not
  independently hand-maintained. Minimum acceptable: corrected *and* covered by an integrity conjunct
  that fails when it disagrees with `count_sql`'s relation.
- Migration 670 deliberately left `target_table` uncorrected and recorded the mismatch in
  `ka_gochara.volume.md` rather than encoding it as true `[S]`. That was the right call for an
  integrity contract; it is not a resting place, because #5 is wired to a `DELETE`.

**Sixth-way note.** `asset_registry.target_floor = 83` (migration 670) `[S]` is a quantity claim over
an unnamed relation; it is only meaningful against #2. It should be stated as a floor *on the
count_sql relation*, or it becomes a seventh drifting declaration.

---

## 5. Binding to the ratified vocabulary (context §1) — no new scalar

**This family will not emit a confidence, salience or reliability number.** Product §5.2 forbids the
collapse; context §1 makes it explicit. `ka_taranga`'s `tier_basis='relative_uncalibrated'` is the
discipline extended here.

Every served row and every temporal testimony this family emits carries:

| Contract | Field | Values for this family |
|---|---|---|
| **F04** epistemic class | `epistemic_class` | `computed_fact` for contacts and geometry; `qualified_rule` for a cited classical gate (vedha, moorti, AV); `interpretive_inference` for any projection that grades; never `external_claim` |
| **F06** completeness | `completeness_state` | `applied` · `inapplicable` (class/shape does not admit this method) · `unavailable` (overlay not built for this span — the F5/§7 case) · `unqualified` (source qualification missing — the five provisional ontology classes) · `contradictory_unresolved` · `unexplored` (outside searched horizon). **No null/zero/empty fallback may stand for any of these** |
| **F12** operator | `operator_role` | `computation` (contact geometry) · `applicability` (daśā permission, AV gate) · `counterevidence` (vedha, obstruction) · `uncertainty` (bracket/tolerance) · `exclusion` (protected/held) · `relevance_navigation` (class targeting) |
| **Strategy §3 Temporal testimony** | full object | target structure · exact evidence roots · method/family · units/polarity · applicability · support/opposition/**silence** · **independence group** · material uncertainty |
| **Comparability** (L3-Q05, F08) | `comparable_with` | a method/scale key. A v3 λ is **not** comparable with a v1 λ_e, nor with Sangam's ICC. Declared, never left for the reconciling LLM to assume |

**`independence group` is load-bearing here.** One physical contact reached through several resonance
targets is **one witness**. Honesty fix H-6 (§9) implements this; the field is what lets the
reconciling LLM see it.

**R3 restated to avoid the forbidden pattern.** v1.0's `precision_class` is **not** a confidence. It
is a three-field qualification: `time_basis` (`direct_swiss` | `interpolated` | `day_snapshot`),
`bracket_days` + `tolerance_arcsec`, and `claim_grain` (the forecast grain the product permits, which
never inherits the astronomical grain — Product §3.10).

---

## 6. Reconciling the June brief (`CLAUDECODE_BRIEF_L3_KA_GOCHARA_v1_0.md`)

That brief targeted a superseded campaign plan and described `pipeline/transit_search.py` as missing.
It now exists `[S]`. Its **kernel is retained**, not re-authored:

| June kernel | Status now | Where it lives in this brief |
|---|---|---|
| §3.3 event vocabulary as **generators with a uniform interface** (ingress, return, station, eclipse, confluence, transit-to-transit) | **Adopted.** This is the kernel's shape | §8 kernel; the episode types |
| §3.4 **continuous orb-strength I-17** — orb at exact + speed + applying/separating, *"the curve FORM + weights are native-ratified judgments — propose, do not silently pick"* | **Adopted, and identified as the same question as v1.0's M-1.** June already ruled it native-judgment | §9.2 M-1 (now explicitly = I-17) |
| §3.4 node convention — PHASE_4D `MEAN_NODE` vs `ka_graha_sancara` `TRUE_NODE`, *"pick ONE, document it, apply everywhere"* | **Open and unresolved.** L0 stores `TRUE_NODE` (`l0_ephemeris.py`, swe id 11) `[S]`; `bg_sky_calendar` excludes node stations by classical convention `[S]` | §5 convention vector; **raised as decision N-4** |
| §3.2 efficiency law — route through the ephemeris service/cache, ephemeris-last | **Adopted in spirit, amended in fact.** `ka_graha_sancara` PATH-A returns the *day's noon* position for any instant `[S]`, so it is not a valid oracle for sub-day work until repaired | §8; `ka_graha_sancara` repair is its own packet |
| §3.5 coarse-to-fine, not a hard ±10 y wall | **Adopted.** The episode ledger is horizon-parametric | §8 |
| §0 "the single most valuable build in the layer" | **Retained as the claim to test**, not as an assertion. Context §9: VALUE-EVALUATED is N for all sixteen questions examined | §13 |

Two June positions are **not** carried: `ka_transit_almanac` subsumption (that asset is outside this
family's scope now), and the ±10 y router cap as a design constraint (it is a router latency guard).

---

## 7. Force-fitting instances in this family (VA §10.2 checklist, context §6)

| VA §10.2 category | Instance in this family | Evidence | Replacement |
|---|---|---|---|
| Forced favourable default for missing data | `quality_gates` falls back to **1.0** when no vedha row overlaps; the overlay covers only −60/+400 d, so ~98 % of a century scores as *unobstructed* | `engine.py` step 4d; `ka_vedha_gochara/writer.py:86-87` `[S]` | F06 `unavailable`, never a neutral multiplier |
| Misleading "applied/complete" detector | `lambda_thresh=0.0` with `>=` makes every sample "active"; a λ≡0 range still yields one era window | writer `:1940`; `threshold.py:393`; `E5` `[X]` | H-3 (§9.1) |
| Misleading detector (2) | `_eval_single` converts **any exception** to `0.0`, which the `>= 0.0` threshold then certifies as active | `interval_solver.py:116-136` `[S]` | H-2 |
| Unqualified input sold as evidence | `kakshya_cell_crossing` runs an **uncited `equal_eighths_fixture_approximation`** on the served path — the engine passes `conn=None` unconditionally, contradicting its own docstring. 147/202 sentences, ~59 % of evaluation cost | `engine.py:1063-1112`; `primitives.py:664-719`; `E3`,`E4` `[X]` | H-1 — cited L1 BPHS Ch.66 boundaries, else F06 `unqualified` |
| Duplicate-evidence counting | one physical contact reached via several targets counts several times into the noisy-OR | `_compute_activity_v3` `[S]` | H-6 + `independence group` |
| Silent truncation | `MAX_PEAKS_PER_ERA_WINDOW = 3` — at most three timing claims per class per decade, undisclosed | `resolution_hierarchy.py:105` `[S]` | H-5 — store all, trim at serve with a disclosed count |
| Aggregation erasing material distinction | activity saturates: all **380** served rows carrying an activity value sit in **[0.99964844, 1.0]** `[L]`; fixture range 0.9940–1.000 `[X]` | `E2`,`E3` `[X]`, live `[L]` | M-1/M-3 (deferred, §9.2) |
| Timestamp that is an artefact of the caller | `eclipse_degree` stamps events at the search-window edge | `E7` `[X]` | H-4 — real L0 eclipse instants; **timing only** |

Not a VA §10.2 category but the same family of harm: **B5's `date.today()`** (§3) and **F3's
wrong-zodiac contacts** (§8).

---

## 8. Disposition per asset — preserve / change / reuse

### `ka_gochara_sweep` — PRESERVE, unchanged
Retired, unrebuildable, outside the active DAG (L3-H01). **No retirement decision is proposed** —
it is already retired; this brief proposes only that its *data* stop being reachable by a Clear
(§3 B1) and that its recovery be made real (§3 B3). The non-rebuild detector — absence of
`@register` — is preserved `[S]`. F19 preserves it as historical capital.

### `ka_gochara_resonance` — PRESERVE the kernel, CHANGE two defects
Preserve: eight target types, citation discipline, the honest `uncited_extension` flagging, the
coverage-quality notes. Change: (a) `setdefault` retains only the **first** source root when a target
resolves more than once `[L]`; (b) target parsing strips a lord qualifier such as `afflicted` `[L]`.
Both destroy evidence roots that §5's Temporal testimony requires, and neither is recoverable
downstream by a stable contact id. Reserve L2 binding columns (R8). 508 of 765 live rows are flagged
uncited `[L]` — that is a qualification fact to carry (F06 `unqualified`), not a defect to hide.

### `ka_gochara` — RETAIN the id and the horizon semantics, REPLACE the geometry
Preserve, per L3-A13: the v2 computation and the **progressive ±3-year search as bounded coverage**
— the Strategy asks for it to be *disclosed*, not extended. Preserve the arc-substrate idea, delta
fingerprinting, horizon attestation.
Change: the frame defect (F3 — sidereal targets solved against tropical arcs; Saturn 763 d, Jupiter
349 d, Mars 33 d from the true contact `[X]`); `date.today()` (B5); and the geometry defects the
independent review established `[X E8]` — station coalescing below 0.25 d (1 of 3 real roots found),
a dropped 0°/360° seam tangency, and a solver exception swallowed as `[]`.
**Live-path test for F3:** authority is `'3.0'` on both canonical charts, so gen-`2.0` rows are not
served — *no live serving caller found within scope: the three `gochara_*` MCP tools,
`reading_checklist.ts`, D8/D9 adapters, `engine_tier.ts`, `ka_kshetra` stage-4 cross-check (which
resolves through `kala_gochara_authority`)* `[S]`. The asset remains buildable, so the defect is
latent, not inert.

### `ka_gochara_v3_century_materialize` — see §11

### The kernel (new, shared) — REUSE, one-way dependency
A pure numerical module: sidereal-frame arcs under the D-1 convention, episode solving (in/peak/out,
core crossings, branch, dwell, truncation), generators per event type (June §3.3). It **imports
nothing from `ka_kshetra`** (that inverts into a cycle when S0 later adopts it) and **edits neither
`transit_search.py` nor `ka_dasha_kala`** — both sit inside frozen digest closures (campaign plan §4).
It may lift individually proven functions under an explicit inventory with a duplicate-copy audit
entry. Kshetra S0's own defects are **not** imported: it emits nothing for a body already inside orb
at horizon start, and assigns noon data to a midnight origin (7.5° for the Moon) `[X E8]`.

---

## 9. Method qualification — what is settled and what is not

### 9.1 Pre-approved honesty fixes (D-3, ratified) — no doctrine changes
H-1 cited kakshya boundaries or `unqualified` · H-2 an exception is never a score · H-3 no era window
over a zero-λ range, and requested-vs-completed horizon stated exactly · H-4 real L0 eclipse instants,
**timing only** · H-5 no hidden peak cap; disclosed trim at serve · H-6 one physical contribution
counted once, with its `independence group`.
Each is "make the code do what it already claims". Each needs a golden value and an F06 state.

### 9.2 Deferred to native ruling with evidence (D-3) — these change what the astrology asserts
**M-1 = the June brief's I-17.** Should a transit contribute *while within orb*, scaled by actual
separation and applying/separating, replacing "an exact crossing fell within ±5 days"? The curve form
and weights are native judgments — June said so, and that ruling is inherited, not re-opened.
**M-2** dwell weighting (slow/stationary passages weigh more).
**M-3** the Moon's participation in *this score*. It stays in the evidence under every option;
ADJUDICATION-14 rejects cost-led amputation of bodies `[R]`.
**M-4** which of the unwired mechanisms enter scoring, and in what order — each preceded by an
operand audit. `w21_av_gating` is **not** first: it substitutes a rule threshold (`min_sav_score`)
for the chart's actual bindu count `[S]`. Its annual-stack item is gated on the cross-asset
independent-witness ruling.

---

## 10. The packet body (Strategy §6.4)

**Input generations.** No L1 or L2 generation head has ever been opened `[L]`; adopting the
1035/1036 pattern for L3 is native decision 1, still open. This family is written to bind a
**compatible transitive dependency vector** — L1 natal facts, `chart_dashas`, AV, Sade-Sati, kakshya
boundaries; L0 `ephemeris_daily`, `bg_sky_calendar`, transit rules, moorti and vedha corpora; L2 via
the reserved binding columns. **If generations are adopted:** reads pin a published generation, and
the publication manifest (below) names it. **If they are not:** the same fields are pinned as a
content digest over the consumed relations, and the manifest records that it is a content pin rather
than a generation pin. No implicit fall-through to mutable `public` rows in either case.

**Field-level transformations and the §3 dossier.** For each material field:
`contact_id` (text, deterministic; natural key = normalized target + relation + convention +
branch/occurrence; never renamed by horizon clipping; operator `computation`) ·
`t_in`/`t_peak`/`t_out` (instant + `bracket_days` + `tolerance_arcsec`; unit days/arcsec; null means
`unexplored`, never 0) · `exact_crossing` (bool; false for a tangency or closest approach — the
distinction F12 `computation` must preserve) · `orb_deg` + `orb_source` (a cited rule or
`default_3deg`, which is F06 `unqualified`, not a fact) · `dwell_days` · `epistemic_class`,
`completeness_state`, `operator_role`, `comparable_with`, `independence_group` (§5) ·
`evidence_roots` (array of canonical L1 `fact_id`s; §N.5 — referenced, never restated).
Each gap is classified *missing · computed-but-discarded · persisted-but-unused · flattened ·
unqualified · stale · unserved* — they need different fixes. The known
**computed-but-discarded** instances in this family are the resonance first-root loss and the lord
qualifier (§8); the known **unserved** instance is every field below the serving trim (§12).

**Preserve / change / reuse.** §8.

**Output keys and partitions.** Contacts: `(chart_id, contact_id)`, partitioned by body and horizon
slice. Windows projection: the existing natural key
`(chart_id, event_class, window_start, peak_date, coalesce(milestone_id,''), coalesce(resolution,''), generation)`
(migration 568) `[S]` — **preserved unchanged**, so the projection remains a drop-in for every current
reader. Exact instants live in the contact ledger, **not** in the windows table, whose
`window_start`/`window_end`/`peak_date` are `DATE` `[S]` and therefore structurally unable to carry
them.

**Source and data checks.** Geometry against Swiss under the *same* convention vector (D-1) — the two
sidereal methods in this repository disagree by up to 16.5″ for the Moon, so an unpinned "Swiss
agrees" is meaningless `[X]`. Scoring against a hand-specified factorised reference, **not** against
old output: Strategy §5 — *"where the current method has a defect, the old output is not the
unquestioned parity oracle"*, and §7 establishes several. Determinism: same input vector → byte-equal
output, which B5 must be fixed to permit.

**Consumer effects — as interface packets, not L3 code (context §5).** Serving belongs to Pūrṇa.
This family raises, in L3-U04/U11 form:
- **P-1** the coverage attestation routes an unknown generation into the retired-sweep branch and can
  answer `not_covered` before reading windows `[S]`; it also intersects *current mutable* resonance
  targets. Obligation: coverage resolves against the publication manifest, including complete-empty
  partitions. Test: a chart with a complete but empty class returns `applied`+empty, not `unavailable`.
- **P-2** `reading_checklist.ts:1063-1092` drops ids, generation, resolution, parents and
  `peak_basis`, limits to 200 and returns 5 while counting the capped set `[S]`. Obligation: honest
  returned/available/truncated counts; evidence identity survives.
- **P-3** the L5 prospective ledger has no field for `contact_id`, generation or convention `[S]`.
  Obligation stated; **no claim issuance is touched under an L3 packet**.
**I own the sentinel test** (Execution Brief §7): a sentinel placed only in a low-ranked, non-default
field must reach the allowed consumer and the saved result. Known failure shape to avoid: a field
computed, stored, then trimmed before synthesis — `ka_sangam`'s discriminating tier is exactly that.

**Benchmark target.** Deliberately **not stated as a number here.** Strategy §5's contract applies
(cold, warm, resume, horizon extension, upstream correction, no-window, dense-window, rare boundary;
wall, CPU, RSS, Swiss-lock time, SQL count, rows/bytes/WAL, recovery, time to first *qualified
consumer result*; repeated matched runs with spread). The baseline is
**`KALA_COST_PROFILE_v1_0.md`** (context §10) — **not** `asset_registry.estimated_seconds`. Measured
unit costs available today: 64 ms per evaluation at 2 targets, ~92 % of it repeated event search
`[X]`; 0.013 ms per instant for closed-form evaluation once events are known `[X]`; ~111 µs per
arc-solved contact `[R]`. The recorded century executions are 240 s, 613 s and 3,492 s with 270
substeps spanning ~5 h `[L]` — **none proven to be one cold uninterrupted build**, so no total is
claimed. The ~25–36 h figure in circulation belongs to the **retired sweep** (35.6 h `[R]`).

**History and rollback contract.** `v1` rows are preserved in place and made unreachable by Clear
(§1.3 (a)); recovery is made real (§1.3 (b)–(c)); then a **(table, generation)** guard protecting
`'v1'` only (§1.3 (d)) — keyed so it cannot repeat migration 588's Defect D-02. New output is written
**beside** existing generations under an immutable publication identity distinct from the algorithm
label, with a complete partition manifest including valid-empty partitions. Go-live and rollback are
per chart via `kala_gochara_authority` and its four functional flip gates (migration 527 — none of
them time-based `[L]`); a soak period is observation, never a gate substitute. Rollback is proven by
flipping back *through the real serving adapters*.

**Independent reviewer.** §15.

---

## 11. The century materialiser — answering Strategy §5 without deferral

Strategy §5 requires a choice: *"an elevated complete materialization or a qualified compact substrate
with explicit refinement semantics"*, and *"deferral alone cannot earn full asset elevation."*

**Proposed answer: the qualified compact substrate — and it is complete over the century, so the
question's apparent trade-off dissolves.** The substrate is the contact-episode ledger: complete for
the declared body set and horizon, with a declared angular resolution ε and an explicit
`near_station_unresolved` state above which completeness is not claimed. Windows are a deterministic
**refinement projection** of it, at era/month/day grain, preserving the existing natural key and parent
ids. This satisfies both halves of L3-A14: *"ensure complete overlay coverage, content-bound resume
and coherent publication"* and Strategy §5 P3's *"unique target-specification events over absolute
intervals plus boundary halos; chart/common and class-specific context; time-indexed clocks; batched
hierarchy writes."*

**What is preserved from the century writer:** the λ_v3 engine, signed channels, the era⊃month⊃day
hierarchy, chain milestones, the `peak_basis` and `shape_conformance` vocabularies, the scoring
signature, the mechanism corpus, and **both existing table roles** (P3's explicit requirement).

**What is proposed about its lifecycle:** nothing yet. Consolidation into one accountable windows
asset (v1.0 R1) is a *destination*, gated on the full R1 gate set and on a Strategy amendment for the
denominator. **No retirement is proposed in this brief** — context §11 reserves that. The hold stays.

**And the hold must be enforced, not assumed.** §3 B4 establishes that its DB enforcement was dropped
on 2026-08-23 and never replaced. Phase 1.1's *"real guard on `generation='v1'`"* should be extended
to cover `'3.0'` under the writer that actually produces it — keyed on (table, generation), never on
`asset_id`, which is the exact shape of Defect D-02.

---

## 12. Which questions this family serves (context §2 — L3-Q01–Q13, not a local portfolio)

| Question | This family's role | State today |
|---|---|---|
| **L3-Q01** what is active now, and why | Primary — the specific-contact layer | partial: contacts exist but saturate (§7) |
| **L3-Q02** nearest vs better-supported later window | Primary | capped at 3/class/decade (H-5) |
| **L3-Q03** complete activation route for a named configuration | **Contributing only** — needs the L2 structural binding this family does not yet have (R8) | not served |
| **L3-Q05** why timing methods disagree | Contributing — via `comparable_with` and `independence_group` | absent today |
| **L3-Q08** is "no window" a real negative | **Primary, and currently failing** — searched horizon, resolution and method coverage are not expressible; F06 states are absent | the strongest single gap |
| **L3-Q09** what changes with convention | Contributing — D-1's convention vector makes it answerable | not served |
| **L3-Q10** feasible initiation intervals | Contributing — Moon-scale drill-down from the same kernel | separate election path today |
| **L3-Q04, Q06, Q07, Q11, Q12, Q13** | Not this family's to answer alone | — |

No question portfolio is invented here. Nothing in this family serves a need that L3-Q01–Q13 fails to
cover, so no strategy amendment is raised on that axis.

---

## 13. Acceptance state I am designing for (context §9)

**`PRODUCER_READY`, honestly.** Not `DATA_ACCEPTED`, and explicitly not `VALUE_EVALUATED` —
which is `N` for all sixteen consumer questions examined `[L]`, this family included.

The distinction this family would earn, and the ablation that tests it: *given a chart and a domain,
can a reader distinguish "no qualified window in the searched horizon" from "outside the searched
horizon" from "the method never ran"?* Today all three render identically. The ablation is the
three-way negative on matched questions against today's frozen baseline
(`KALA_BASELINE_v1_0.md`). A second, weaker claim — that contact evidence discriminates at all — is
testable only after M-1, because the current term is saturated (§7).

Two structural blockers are outside my control and are named, not worked around:
`CONSUMER_INTEGRATED` and `VALUE_EVALUATED` have **no admissible event type** today — a closed
`z.enum` at `evidence-command.ts:50-63`, native decision 2 `[L]`.

---

## 14. Decisions for the native

**Requested now (this brief's own):**
- **N-1 — re-rule D-2's sequence.** Close the deletion path first, then grant, then drill, then
  guard (§1.3). Supersedes the ratified order.
- **N-2 — accept §4's resolution of the identity dispute:** ground truth = writer DML; declared
  authority = the instrument with a detector; `target_table` derived-or-validated rather than
  independently maintained; `target_floor` restated against the `count_sql` relation.
- **N-3 — accept §11's answer to Strategy §5** (qualified compact substrate, complete over the
  century, windows as refinement) **as the century's method disposition**, with its lifecycle
  disposition still held.
- **N-4 — node convention: `TRUE_NODE` or `MEAN_NODE`,** one, applied everywhere (June §3.4, still
  open; L0 stores `TRUE_NODE` `[S]`).

**Already ruled, carried forward:** D-1 (Swiss sidereal mode, Lahiri) · D-3 (§9) · R1–R10 as amended.

**Deferred to evidence:** M-1 (= I-17) · M-2 · M-3 · M-4 (§9.2).

**I must not decide, and do not (context §11):** L3 generations · typed-confidence binding · the
protected classes · `ka_tithi_pravesha` source qualification · baseline authority · any asset
retirement · any guard weakening · `convergence_commit` · the orchestrator contract.

---

## 15. Independent reviewer, and what this brief does not establish

**Reviewer required, not yet assigned.** Scope for them: §3's two corrections to the input brief
(B1's mechanism and B4's stale guard) — both were derived from source with the database unreachable,
and both change what Phase 1 must build. Then §4's authority proposal, §11's disposition, and whether
the §10 packet would survive its own gates.

**Not established here.** The database was unreachable from this session `[U]`, so every `[L]` value
is inherited and none re-measured — including the `count_sql` live values on which §3's correction
turns, the archive grant, and the trigger absence. No cold full-workload build time exists `[U]`. The
full-century activity distribution is unknown — the 380 rows are selected peaks, not a time series
`[L]`. The Moorti misclassification rate, ledger storage size and a complete reader/writer inventory
are `[U]`. Whether the Clear path has ever been invoked against a canonical chart is `[U]`. Executed
evidence used a two-target fixture with no database, so production target composition and weights are
`[U]` — live classes carry 14–40 targets `[L]`. I did not read the ten mechanism bodies, Sangam's
scoring, or Kshetra stages 1–8 in full.
