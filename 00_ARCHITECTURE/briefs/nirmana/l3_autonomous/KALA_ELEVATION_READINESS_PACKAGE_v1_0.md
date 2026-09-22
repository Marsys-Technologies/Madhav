---
artifact: KALA_ELEVATION_READINESS_PACKAGE
canonical_id: KALA_ELEVATION_READINESS_PACKAGE
version: "1.0"
status: AWAITING_NATIVE_RULING
date: 2026-09-22
supersedes_recommendations_in: KALA_NATIVE_RULING_SHEET_v1_0.md (R1-R6 carried forward, amended)
builds_on: audit/KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md v1.1 (environment + architecture)
sources:
  - readiness/_work/LANE_A_PATHFINDER_BUILD.md          # first real Kala build (this session)
  - readiness/_work/LANE_A2_KSHETRA_CRASH_DIAGNOSIS.md
  - readiness/_work/LANE_B_SECOND_READER.md             # adversarial re-read of the audit
  - readiness/_work/LANE_C_HARD_ASSETS.md               # Gochara / kshetra / sangam, 1106 lines
  - readiness/_work/LANE_D_ASSET_REGISTER.md            # the other 16 assets, 987 lines
  - readiness/_work/LANE_E_LAYER_VALUE_MODEL.md         # consumer questions -> capability -> asset
  - readiness/_work/LANE_F_DEMAND_LEDGER.md             # cross-layer demand, cascade, coordination
  - readiness/_work/LANE_G_ENVIRONMENT_SPEC.md          # operational environment + supervisor fix
  - readiness/_work/INTEGRATOR_VERIFICATION_LOG.md      # the integrator's own re-measurements
does_not_authorize: >
  any build, migration, grant, registry edit, evidence event, deployment or code change.
  Each item below becomes authority only when the native rules on it.
---

# Kāla elevation readiness — the consolidated package

The environment-and-architecture audit asked *can this campaign run here*. This package asks the
question the native actually needs answered: **is the Kāla layer ready to be elevated — as a
layer, as 22 individual assets, and as assets working together — and if not, what exactly must be
done first.**

Seven parallel lanes ran; every claim that would change a decision was re-measured by the
integrating session at its own authority, not by re-running the lane's query. That discipline
changed four conclusions and confirmed one that matters more than all of them.

---

## §1 — The verdict

**Read-only elevation work: GO.** Analysis, contract design, brief reconciliation, route
verdicts, and disposable-database proofs are unblocked today.

**Production-mutating elevation: NO-GO, on five blockers.** Four were known; one is new and is the
most serious thing this exercise found.

**Elevation of the three hard assets specifically: NO-GO on all three**, for three different
reasons — Gochara because its capital is not actually protected, `ka_kshetra` because it cannot
build at all, `ka_sangam` because two of its downstream consumers are being fed the wrong rows and
fixing that changes its contract.

**The layer's own value model is the real prize and is not blocked by any of this.** Kāla's
outer boundary discipline is genuinely good — its probability tiers are honestly stamped
`relative_uncalibrated` in the data. Its losses are internal: the layer discards its best material
between its own assets, before serving is ever reached (§5).

---

## §2 — The five blockers, ranked by whether a live path reaches them today

The ranking criterion is deliberate. Three separate lanes this session reported a hazard as live
when no caller could reach it. Every entry below states its live-path status explicitly.

### B1. A live Clear deletes 40,117 Gochara rows, including the capital v0.3 treats as protected
**LIVE PATH: CONFIRMED, all eight links re-measured.** Severity: blocks Gochara work; standing
hazard regardless of campaign.

The cockpit Clear route loads `asset_registry` with no `is_active` filter
(`clear/route.ts:114-117`); the scope filter ignores `is_active` entirely
(`clearScopeFilter.ts`); `build_protected_assets` — the *only* protection lookup, at
`route.ts:122` — holds **zero rows for every chart**; there is **not one non-internal trigger on
any `kala_*` table** (positive control); and the route falls back to
`DELETE FROM <target_table> WHERE chart_id=$1` (`route.ts:186-187`, stated verbatim in the route's
own authz test at `:14`, whose fixture is literally `target_table: 'kala_gochara_windows'`).

**The deeper fault, and why excluding retired assets would not fix it:** the *active* `ka_gochara`
row also carries `target_table = kala_gochara_windows`, while its `count_sql` reads
`kala_gochara_windows_v2 … generation='2.0'` and its writer only ever writes `_v2`
(`ka_gochara.py:120,336,362`). The registry's `target_table` for the live asset points at a table
its writer never touches — and that table holds the 40,117 rows.

*Fix, before any Gochara work:* correct `ka_gochara.target_table`; add `is_active` to the clear
route's query; populate `build_protected_assets` or restore a database-level guard so protection
is enforced rather than asserted in a comment.

### B2. The L2→L3 cascade has already fired once, and the coordination mechanism already exists
**LIVE PATH: CONFIRMED — it already destroyed 335,403 + 14,868 rows on the canonical chart.**

Five `kala_*` tables carry `signal_id REFERENCES bodha_msr_signals ON DELETE CASCADE`
(migration 403, deliberate). L2 rebuilds are delete-then-insert, so an L2 signal rebuild silently
deletes dependent Kāla rows. Proven on a three-chart natural experiment: where L2 was rebuilt
after Kāla, the rows are gone; where Kāla was built last, they are intact to the row.

**What is new since the ruling sheet:** this was already discovered, measured and adjudicated by
the separate live Nirmāṇa campaign (rulings D-CND-15/16), which **already built the checking tool**
(`cascade_check.sql`). A deterministic `bodha_signal_identity` is already deployed and mitigates
*re-attachment*, but not the destructive event itself. So this is a coordination obligation with an
existing process, not a design problem to solve from scratch. *Verify that campaign's state before
designing anything.*

### B3. `ka_kshetra` cannot build, and separately crashed
**LIVE PATH: CONFIRMED (unguarded read); crash diagnosis is a strong hypothesis, not reproduced.**

`stage3_clocks.py:1012` reads `phala_rectification` unguarded, and `data_plane_builder` has no
SELECT on it — the build hard-fails. Measured cost ~7.5 h against a registry
`estimated_seconds = 237`, a 100× estimate error that alone invalidates any schedule built on the
registry's numbers.

Its last run (2026-09-11) died `worker_crash: OperationalError: the connection is lost`, a week
*before* the identity cutover — so it ran as `amjis_app`, which carries
`idle_in_transaction_session_timeout=600s`. It is a substep writer doing long CPU stretches with no
DB traffic: exactly what that killer terminates, and `db.py:46-70` documents the hazard in its own
comments. **`data_plane_builder` now has no timeout at all** — which removes that failure and
introduces the opposite one: an unattended hung build with no server-side bound.

### B4. The rebuild dispatcher records receipts for code that never ran
**LIVE PATH: CONFIRMED.** Fixed and merged this session as PR #2709 — `dispatch_frozen_rebuild.py`
now resolves writer digests from its own repository instead of a stale developer worktree, with a
regression test that fails 2/3 on the old path and now runs in CI. **This blocker is cleared.**

### B5. The century materialiser sits behind a working BUILD-PROTECTED guard
**LIVE PATH: CONFIRMED, and the guard is correct.** It needs a native override to rebuild. Do not
weaken it — B1 is what happens when a protection is assumed rather than enforced.

---

## §3 — What the audit got wrong, and what that changes

| The audit said | Measured | What it changes |
|---|---|---|
| Kshetra and Sangam briefs "CONFIRMED ABSENT — no file, no draft, no placeholder" | **17 L3 briefs exist, 12 per-asset**, incl. a 170-line `KA_SANGAM` brief tagged `[ELEVATE]` that already names the independence discount and the ephemeris-last efficiency spine | **Reconcile, do not re-author.** They are dated 2026-06-21 against a superseded campaign plan — substantively rich, governance-stale. `ka_kshetra`'s absence is real. |
| The missing acceptance receipts need a schema change | The gate is a closed `z.enum` in `evidence-command.ts:50-63`; `source_kind` is open `z.string()`; **no CHECK constraint** on either column | **No migration needed.** One enum member plus a payload contract plus the real detector-design decision. Much cheaper than implied. |
| The inheritance decision concerns 12 Kāla assets | It concerns **48 upstream ancestors** — 22 `bg_*`, 13 `ga_*`, 13 `bo_*`; 7 frozen under t3, 41 superseded-only, 0 never frozen | The decision is about 41 upstream re-freezes nobody is currently doing. Ledger silent since 2026-09-11. |
| `server_reconstructed` evidence is weak, so inheritance needs re-runs | It is the source kind **reserved for the verifier** (`README.md` identity split; migration 632 trigger) — the certified path | Removes the main argument against inheritance. The staleness argument survives; the provenance one does not. |

Three further lane claims were corrected by the integrator and must not be carried forward as
written: the activation waveform is **not** globally degenerate (its transit term is dead in 91% of
*domain*-scoped rows but live for event-class rows); the `ka_graha_sancara` ayanāṃśa gate is a
**latent** hazard, not a live one (no caller can reach it); and the row-loss signature affects
**five** assets, not two. Full detail in `INTEGRATOR_VERIFICATION_LOG.md`.

---

## §4 — The three hard assets

### Gochara family — blocked by B1, otherwise the best-prepared of the three
The native's v0.3 plan is the model. Its executability gaps are environmental, not conceptual:
the protected capital is not protected (B1); a restore drill run as `data_plane_builder`
**cannot read its own recovery source** (`kala_gochara_windows_archive_20260805`, no SELECT), a
blocker v0.3 does not name; and the Clear route's comment claims a migration-540 trigger guard that
migration 588 dropped — an unearned signal sitting in a destructive path. One correction to the
record: the "retired sweep shares a live table with an active writer" hazard is a **registry**
hazard, not a writer hazard — the writer is correct, the registry row is wrong.

### `ka_kshetra` — the only one of the three with no brief, and the least ready
Beyond B3, the 8.57M rows are **not a completed build**: every row references a
`field_snapshot_id` with zero manifest rows, and the build died mid-`stage5` in alphabetical class
order (25 classes have segments, 15 have null stats, 14 have windows, 0 salience/insights/timeline).
Only 6 classes have a real prior; **85.7% of written windows are `baseline_is_synthetic`**, and
`kala_field` has no such column despite `hazard.py:150-155` claiming the tag rides every downstream
row. The other chart has a *complete, fully-calibrated 6-class* run — so these are **two
configurations, not two runs**, which is the real answer to the PARK-5 question. The load-bearing
gap is that **no retrieval capability exists over any `kala_field*` table**: the layer's largest
investment is unreadable by the product.

### `ka_sangam` — a brief exists; its contract changes once you see what downstream receives
The convergence chokepoint feeds seven assets. Measured: **the top 500 and top 750 rows by score
are 100% Mode C**, so `ka_vighnakara` and `ka_kala_darshana` — which consume exactly those cuts —
**never see a daśā×transit convergence at all**. Their score cut is acting as a mode filter. Mode D
is 70% of the table and ~13× duplicated, and the guard meant to prevent that is vacuous on the
lifetime path (`pred_dicts=[pred]`). `confidence_score` is definitionally `ICC/13` with a
tautological transit term, and `confidence_label` is **anti-correlated with evidence count** —
rows with 2–6 independent corroborations are 100% `speculative` while single-corroboration rows are
the only `high`. The one tier that does discriminate is stored and never served.

---

## §5 — The layer as a layer: where Kāla loses its own material

This is the part no per-asset review can see, and it is where elevation has the most leverage.

1. **Two consumer questions have no owning asset at all** — cross-clock agreement/disagreement
   ("which clocks disagree about this period, and why") and provenance-aware de-correlation. Both
   are squarely within L3's stated charter of "applicable clocks" and "comparison".
2. **Hour-grain and sandhi die at the layer's front door.** `date_resolver.py:349` reads
   `chart_dashas.start_date/end_date` while L1 also holds `start_iso/end_iso` and `sandhi_flag`.
   L3 rounds away precision L1 already computed. `:473` uses `date.today()`, making the primary
   window **build-date dependent** — the same query is not reproducible across days.
3. **Corroboration is counted but never inherited.** `independent_current_count`
   (`engine.py:850-889`) is read by **zero `ka_*` consumers** — only L4's `ph_nimitta` and one
   serving capability. Downstream integrators inherit `ka_sangam`'s score without inheriting the
   detector that qualifies it, so the same evidence arriving by two paths counts twice.
4. **`dissent: []` is hardcoded in seven served tools** — `explain.ts:302`, `now.ts:1312`,
   `priority.ts:280,316`, `story.ts:609`, `ritual.ts:637`, `upaya.ts:265`. `ahead.ts` carries the
   fix and states the defect plainly at `:1705`. An empty array asserts that nothing disagrees.
   This contradicts the product's promise of inspectable disagreement at the point of delivery.
5. **Richness discarded at the L3→L4 seam:** `ka_yojaka` persists a full per-domain confirmation
   map; `ph_nimitta:159` reads only the primary-domain scalar.
6. **VALUE-EVALUATED is N for all 16 consumer questions.** Nothing in the layer has yet been shown
   to improve an answer. That is the honest state, and it is what the elevation must change.

---

## §6 — What must be done, in order

**Phase 0 — make the environment safe (before any mutating work).**
1. Close B1: fix `ka_gochara.target_table`, add `is_active` to the clear route, enforce protection.
2. Coordinate with the Nirmāṇa campaign on B2; use its existing `cascade_check.sql`.
3. Grant SELECT on the three `bg_*` tables; decide `phala_rectification` in the Kshetra brief
   rather than cementing an L3→L4 upward dependency with a grant.
4. Set an explicit `idle_in_transaction_session_timeout` on `data_plane_builder` — deliberate
   value, not inherited silence.
5. Apply Lane G's supervisor fixes (the progress detector counts any file change as progress, so
   its idle-halt cannot fire) and its disposable-PG harness — carrying the seven trigger functions
   my pathfinder ran without.

**Phase 1 — decide (§7). Phase 2 — reconcile the 12 existing briefs; author the Kshetra brief.
Phase 3 — first vertical slice.**

**The first slice should be `ka_tithi_pravesha`,** and it is ready now. It builds in 0.61s, is
idempotent, is frozen-contract compliant under test, and its verification flag is mutation-proven
earned. It also carries one real defect to fix: its window instants are stored **5.5 hours late**
in production, because the writer persists a naive local datetime into a `timestamptz` column and
production's session timezone is UTC. The astronomy is right; the persistence boundary is wrong.
Fixing it, rebuilding, and taking it to a terminal freeze proves the whole chain — build, receipt,
evidence, freeze — on an asset small enough to iterate in seconds. That is worth far more than
starting on the hardest asset.

---

## §7 — Decisions only the native can make

1. **t3 inheritance** — 41 upstream ancestors. Recommend: inherit where the frozen artifact is
   provably unchanged, by re-verification under t3, not rebuild; pilot one L0 asset first.
2. **The headline metric** — report `Delivered N/22` and `Data-accepted N/22` separately, and
   commission the three receipts in parallel (no migration needed).
3. **Brief authority** — ratify Gochara v0.3 once B1 is closed; reconcile the 12 June briefs
   against the current strategy; author the one genuinely missing Kshetra brief.
4. **`ka_kshetra`'s future** — its 8.57M rows are an incomplete generation, 86% synthetic-baseline,
   with no retrieval capability over them. Decide whether to complete, re-scope to the calibrated
   6-class configuration, or park — before spending on a 7.5-hour build.
5. **`ka_sangam`'s contract** — the score cut is a mode filter. Decide whether downstream should
   receive mode-stratified rows, and whether `confidence_label`'s anti-correlation is a bug to fix
   or a definition to replace.
6. **Truncation policy** — one ruling covers six assets.
7. **Independent witness** — what counts as independent, given corroboration is counted but not
   inherited.

## §8 — What this package does not establish

One asset was built end-to-end; 21 were not. Per-asset cost remains unmeasured except for
`ka_tithi_pravesha` (~5.1 ms/row) and `ka_kshetra` (~7.5 h, measured by another lane). The
orchestrator's frozen-manifest path and a real writer run have still not been proven in **one**
run — Domain C proved the first, Lane A the second. No empirical value claim is made for any
asset: VALUE-EVALUATED is N across the board, by measurement, not by omission.
