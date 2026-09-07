---
artifact: L1_W6_CLOSE_REPORT_v1_0.md
canonical_id: NIRMANA_L1_W6_CLOSE_REPORT
version: "0.14-DRAFT"
status: DRAFT — sections filled as evidence lands; NOT a close claim
session: L1
layer: L1 — Gaṇita
produced_on: 2026-09-07
charter_ref: C11 (definition of done)
warning: >
  Started early, mirroring L5's own precedent (L5_W6_CLOSE_REPORT_v1_0.md, "your close report
  feeds the Conductor's Phase Z directly — draft it early"), per PROMPT_L1.md's own naming of
  this exact file as the W6 deliverable. It is NOT a claim of closure. No capsule, freeze event,
  or completion is asserted anywhere in this file. Sections marked OPEN are genuinely open.
---

# L1 — Gaṇita — W6 CLOSE REPORT (DRAFT)

## §0 — Status

**NOT CLOSED.** W1 ✅ (19/19 assets analyzed, 5 batch files) · W2 ✅ (139 findings triaged,
routed) · **W3 — finding-list-driven work complete** (NOW tier 18/18 closed cycle 122; MUST tier
was claimed closed for L1's own scope cycle 125, but that claim was **wrong for one id-group**:
F-B32/F-B33 (`coverage_matrix.ts`'s 169-entry hand-maintained list vs. live `chart_facts` category
count, plus `concept_aliases.ts`'s citation of a CI check that does not exist) was independently
re-verified LIVE cycle 146 and is genuinely **still open**. F-B33 (the false CI-check citation)
CLOSED cycle 147 (PR #2191). F-B32 (the stale category list) remains open; quantified precisely
cycle 148: the gap has NOT widened since the original measurement (flat at 169-vs-**219**,
canonical-chart-scoped — cycle 146's own "223" was itself a mis-scoped, corrected claim, see §2)
— 57 categories missing, 6 phantom entries found in the 169-list. Being closed incrementally
cycle 149 onward (31/57 landed across 7 slices, PR #2202; ~25 remaining reframed cycle 156 as
genuinely unreachable by any tool, not a list-staleness gap). See §2 for the corrected
disposition and §5 for the forward item; NEVER-LATER correctly parked by design) but **not yet
formally declared closed** (that ruling belongs to the Conductor/native, not a unilateral session
call — see the W3 STATUS SNAPSHOT in `L1_STATE.md`) · **W4 ⛔ PARTIALLY UNBLOCKED, cycle 155.**
Adjudication #2113 was raised as a campaign-wide `asset_freshness` gate (zero L1 dependency-asset
rows) blocking any L1 rebuild; re-investigated live (cycles 132-133) and found the real picture
was more specific: `ga_positions` (L1's DAG root, zero declared dependencies) is IMMUNE to that
gate by construction, and its true blocker was a now-fixed writer crash (#1856) plus a stale W2
acceptance pin. Pursuing that unblock surfaced a SECOND finding: `ga_positions_writer.py`'s
`fact_id` derivation changed since its last acceptance (PR #1898), and `ga_yoga_firings.
constituent_fact_ids` resolves to exactly `ga_positions`' own categories — a `ga_positions`-only
rebuild would have orphaned those references. Escalated as adjudication #2180; **RULED by the
Conductor 2026-09-07T00:45:28Z** confirming the corrected waves-0-3 coordinated-rebuild scope
(15 assets) as correct, superseding the original 5-asset framing. **Wave 0 (`ga_positions`)
dispatched and completed live, cycle 155**: fresh Cloud SQL backup taken first, `--commit
--acknowledge-destroys` for the WP-6 blast radius (`chart_fact_identity`, in-layer, ~530 rows
scoped to this chart's positions categories — confirmed against this session's own prior
blast-radius statement, not the tool's naive 270,471 whole-table count). `asset_throughput.
state` now `'lit'` (was `'error'`), `chart_facts` repopulated (530 rows). Also found and fixed:
`chart_fact_identity` is repopulated by a SEPARATE standalone script
(`build_fact_identity_index.py`), not the orchestrator writer — re-ran it for the canonical
chart, 125,593 rows restored. **New blocker found, not yet resolved**: `asset_freshness` for
`ga_positions` shows `freshness_state='unknown'`, not `'fresh'` (`asset_registry.
natural_key_partition` empty) — `asset_runner.py`'s DEP-ASSERT gate requires exactly `'fresh'`,
so **wave 1 may still be blocked** by a different gate than #2180's ruling addressed. Posted to
#2180, awaiting a reply. Did not attempt wave 1 this cycle. · **W5 ⛔ BLOCKED** (no completed post-W4
run exists to mechanically check or verify) — one prep artifact exists ahead of need:
`platform/scripts/nirmana/l1_integrity_check_dry_run.sql` (PR #2163), a read-only reporter that
runs all 19 assets' `integrity_check_sql` against LIVE pre-rebuild data (not a substitute for a
real post-rebuild W5 pass, but confirms the mechanical-check half is ready the moment #2113
clears) · W6 ⬜.

No lane-death or stale-worktree incident this campaign (unlike L5's two). One self-inflicted
mid-cycle branch/backup mixup (cycle 123, `fact_category_pin_allowlist.json` stale snapshot) —
fully traced and recovered same-cycle, no data lost, documented in `L1_STATE.md`'s cycle-123
heartbeat.

L1 is second in the C2 freeze ordering (L0→**L1**→L2→L3→L4→L5). Unlike L5 (which closes the
build arc), L1 sits near the *start* of the DAG — its own freeze is a dependency-satisfaction
input other layers' E-gates check, not a terminal event.

## §1 — Asset table (19)

Routes are W2-final. Full per-asset findings/fix history (every F-id, PR, migration) lives in
`L1_STATE.md`'s own per-asset table — this is a condensed pointer, not a duplicate.

| # | asset | live / floor | route | W3 status |
|---|---|---:|---|---|
| 1 | `ga_positions` | 1205 / 50 | `rebuild_only` | layer root/canary; F-A16 fixed (migration 847); wave-0 rebuild dispatched+completed cycle 155 (`state='lit'`), `freshness_state='unknown'` pending #2180 |
| 2 | `ga_vargas` | 23,542 / 22,092 | fixed (PR #1766) | F-A1/F-A3 fixed at writer level; F-A14 contract genuinely RED pending rebuild |
| 3 | `ga_dashas` | 483,859 / 536,471 | `rebuild_only` | floor decomposed to 5 named causes; F-A11 audited |
| 4 | `ga_nakshatra` | 2,847 / 1,802 | `rebuild_only` | F-B18/F-B19 fixed (PR #2118) |
| 5 | `ga_panchanga` | 437 / 437 | fixed (PR #1841) | F-B24 fixed at writer level; F-B26/F-B31 fixed (migration 843) |
| 6 | `ga_sensitive` | 8,565 / 8,610 | `rebuild_only` | deficit = floor-vintage mismatch, not a defect |
| 7 | `ga_sensitive_degree` | 275 / 0 | `rebuild_only` | F-B14 fixed (PR #2133) |
| 8 | `ga_strength` | 13,621 / 11,936 | `rebuild_only` (corrected cycle 23) | F-C1 fixed serving-side (L2's `query_ucd.ts`) |
| 9 | `ga_structural` | 98,542 / 77,821 | `rebuild_only` | F-C9 fixed (migration 842); **7 tracked-red F-A14 conjuncts** (F-A15/A17/157/A18/A24/A25/A26), all fixed at the writer level, awaiting rebuild |
| 10 | `ga_condition` | 2,880 / 2,880 | fixed (PR #1853) | F-C8 fixed at writer level (genuinely red pending rebuild); F-C10 fixed (migration 851, cycle 124) |
| 11 | `ga_yoga` | 63 / 5 | fixed (PR #1865) | F-D1/F-D2 fixed serving-side; F-A16 fixed at writer level (PR #1979, pending rebuild); F-D5 fixed (PR #2140) |
| 12 | `ga_vichara` | 8,249 / 8,249 | `rebuild_only` | `catalog_status` DRAFT→CURRENT fixed; F-D11 fixed (PR #2141) |
| 13 | `ga_sade_sati` | 6,287 / 11,019 | `rebuild_only` | F-A14 contract complete 15/15 categories; F-D18/F-D20 fixed (PR #2142/#2144) |
| 14 | `ga_transit_anchors` | 45 / 45 | fixed (PR #1950) | F-D22 FORENSIC assertion fixed; F-D25 fixed (PR #2145); F-D21/D23 **fixed** — L0's PR #2153 merged, adjudication #2122 closed, verified live cycle 130 |
| 15 | `ga_ayurdaya` | 130 / 130 | `rebuild_only` | F-E4 fixed (migration 845); F-E2/E3 fixed (PR #2146) |
| 16 | `ga_medical` | 45 / 45 | fixed (PR #1871) | F-E5 fixed at writer level; F-E8 fixed (PR #2148) |
| 17 | `ga_vastu` | 40 / 40 | `rebuild_only` | F-E10/E11 fixed; F-E28 fixed (PR #2152) |
| 18 | `ga_tajaka` | 240 / 240 | fixed (PR #1859) | F-E16/E17 fixed at writer level; F-E19 fixed (PR #2151) |
| 19 | `ga_prashna` | 0 / 0 | **dormant disposition** | R-1: facility live-mounted but dormant by design; F-E21/E22 recorded/corrected, ruled out-of-scope (#2123) |

All 19 carry a non-NULL `integrity_check_sql` (closed cross-cutting rollout, confirmed cycle 124).
Live dry-run (2026-09-07, PR #2163): **15/19 PASS**, 4/19 FAIL — all four are the exact
already-tracked, writer-level-fixed residuals named in rows 2/9/10/11 above, none new.

## §1.5 — W3 PR ledger

On the order of **115 merged PRs** authored by this session across cycles 1-129 (live count via
`gh pr list --search "is:pr is:merged head:codex/nirmana-l1-"`, 2026-09-07 — an approximation
bounded by branch-naming convention, not hand-enumerated; a small number of PRs on
differently-prefixed branches, e.g. `fix/nirmana-l1-...`, may not be captured by that search).
Rather than duplicate a PR-by-PR ledger here, the authoritative record is `L1_STATE.md`'s own
per-cycle heartbeat log (one entry per cycle, every entry names its PR number(s)) plus the
per-asset table in §1 above. Structural milestones:
- Cycle 1-99: initial W1/W2 sweep + first-pass fixes across all 19 assets (writer-level +
  migration-level), `integrity_check_sql` rollout began.
- Cycle 100-122: NOW tier (18 findings) closed.
- Cycle 122-125: MUST tier (~24 id-groups) closed for L1's own scope; cross-cutting rollouts
  (F-A14 `integrity_check_sql`, F-C14 scanner tightening) confirmed complete.
- Cycle 124-128: bookkeeping (migration-range tracking, adjudication resolution) + first W5 prep
  artifact.

## §2 — Findings ledger outcome

139 findings total (`L1_W2_DECIDE_v1_0.md` §3). **~24 MUST id-groups · 18 NOW · 11 NEVER-LATER
id-groups.**
- **MUST** — CLOSED for L1's own scope (cycle 125) **with one correction found cycle 146, F-B33
  half closed cycle 147, F-B32 half quantified cycle 148**: F-B32/F-B33 was carried in cycle 125's
  own closure sweep as closed, but was never actually fixed. Re-verified LIVE cycle 146:
  `platform/src/lib/retrieval/registry/layers/L1_ganita/coverage_matrix.ts` still declares
  exactly 169 hand-maintained `fact_category` entries (file header unchanged since 2026-06-16).
  **Correction to cycle 146's own count** (cycle 148): the file's own stated scope is
  "every `chart_facts.fact_category` that exists **for chart_id=native**" (line 13) — the
  correct comparison is therefore the canonical chart's own category count, not an unscoped
  count across all charts in the table. Cycle 146 used an unscoped `SELECT count(DISTINCT
  fact_category) FROM chart_facts` (223, spanning three charts with 217-220 categories each) —
  the right, scope-matched query is `... WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'`,
  which returns **219** — identical to the original W1 measurement. **The gap has not widened;
  it is flat at 169-vs-219**, exactly as first measured. (Cycle 146's "widened to 223" claim is
  itself corrected here — the same discipline applied to catching cycle 125's error applies to
  catching this session's own.) A full `comm`-based diff (cycle 148) found: **57 categories live
  for the canonical chart are absent from the 169-list** (e.g. `ayurdaya`, `bhava_cusps`,
  `graha_nakshatra_join`, `special_lagna`, `upapada_lagna`, `kp_house_significators` — the full
  57 are diverse, spanning nearly every section of the file); **7 entries in the 169-list are NOT
  live for the canonical chart**, of which 6 (`ashtakavarga_anubindu`, `dosha_fires`,
  `esoteric_point_chatushphuta`, `esoteric_point_panchasphuta`, `esoteric_point_trisphuta`,
  `yoga_fires`) do not exist as a `fact_category` value **anywhere in the table, for any chart**
  — genuinely phantom/stale names, not just chart-specific absences (`yoga_label`/`dosha_label`
  are the real live categories the file already separately and correctly lists) — and the 7th
  (`karaka_web_per_varga`) is a real category with 2,945 live rows, just not yet built for the
  canonical chart specifically, so not itself a defect. Separately, `concept_aliases.ts:14` cited
  `platform/scripts/census/schema_map_alias_coverage_check.ts` as an existing CI regression check;
  that file did not exist — **fixed cycle 147, PR #2191** (docstring corrected to state reality
  honestly rather than build the check against a still-unsettled category count). F-B32's own fix
  (updating the 169-list to the true 219, and removing/investigating the 6 phantom entries) is
  handed forward as the next unheld MUST-tier item in §5 — assigning each of the 57 missing
  categories to its correct serving tool requires per-category verification against real serving
  code, which is out of scope for any single bounded cycle; this cycle's contribution is the
  verified, corrected diff itself, not the edit.
  The remaining MUST-tier disposition: the large majority
  fixed at the writer or serving-layer level across cycles 1-124; five id-groups (F-C2/C3/C4/C5/
  C7, the D-SALIENCE feed) correctly routed to L2's `bo_laksana.py` — confirmed not an L1 file;
  three id-groups (F-D21/D22/D23) escalated to L0 via adjudication #2122, **fixed and closed**
  (PR #2153 merged, verified live cycle 130 — root cause was one layer up, L0's own
  `from_moon_view` vidhi primitive); one cross-cutting rollout (F-A14/A15, F-B35, F-C15, F-D28, F-E27 —
  `integrity_check_sql` NULL on all 19) closed via the ongoing per-asset campaign, confirmed
  complete cycle 124; F-C14 (the CI scanner gap) confirmed already closed by an independent
  scanner-tightening commit (issue #1750, Conductor ruling) predating this session's own
  discovery of it, cycle 125.
- **NOW** — CLOSED (cycle 122). All 18 in-layer improvements landed: floor/formula re-baselines,
  `estimated_seconds` re-measurements, `target_table` backfills, `density_contract`/
  `empty_reason` declarations, serving-projection widenings, total-`ORDER BY` fixes,
  `fact_category_ownership` completions, dead materialized-view drops.
- **NEVER-LATER** — correctly remains parked by explicit design: all DAG corrections (immutable
  per #1744), R-1 `ga_prashna` dormancy, native-parked verification items, stale-doc-figure items
  deliberately deferred to opportunistic-only fixes rather than a dedicated pass.

*(Per-finding disposition TABLE — as opposed to this tier-level summary — is OPEN; the source
data for it is complete in `L1_W2_DECIDE_v1_0.md` §3 + `L1_STATE.md`'s per-asset table, but
compiling a single 139-row table is deferred to a later prep cycle or W6 itself, since it does
not change any decision made so far.)*

## §3 — Pillar movement (per the five doctrines)

L1 is the deterministic facts layer — for four of the five doctrines it is a **substrate
provider**, not itself an interpretive claimant, mirroring L5's own framing of D-SALIENCE/
D-SYNTHESIS/D-TIME as "consumer, not producer" roles, inverted: L1 is the producer every later
layer consumes for these.

**D-GROUNDING (P3).** L1's own outputs are computed facts (ephemeris-derived positions, dashas,
divisional charts, strengths), not interpretive claims carrying a `sruti`/`yukti`/`pratyaksa`
citation tier themselves — `grounding_tier` is correctly an L2-Bodha-boundary concept applied to
signal classes/firings (per the L0 W1 batch analyses' own framing, same doctrine). Where L1 DOES
carry classical citation obligations directly — `ga_yoga`'s 233/233 catalog rows (F-D1/F-D2,
fixed) — the citations existed but were unreachable at serve time; now joined and paginated
correctly.

**D-SALIENCE (P5).** L1 is explicitly named upstream feed material (F-C2/C3/C4/C5/C7 — argala,
AV term, vargottama, cancellation modifiers). Confirmed these four findings are genuinely L2's
`bo_laksana.py` to consume/fix, not L1's own writer — L1's job here is producing the raw
computed values correctly (confirmed correct at the writer level; the consumption gap is L2's).

**D-SYNTHESIS (P4) / D-TIME (P6).** L1 supplies the raw substrate (positions, dashas, transit
anchors, panchanga) that L3 Kāla's timing arbitration and L2/L4+ synthesis build on. `ga_transit_
anchors` is the direct D-TIME-adjacent case: F-D21/D22/D23 (a primitive dispatching an argument
no tool reads; a FORENSIC assertion contradicting a correct value; zero data-plane consumers)
turned out to be a serving-layer defect one layer UP (L0's `from_moon_view` primitive), correctly
escalated rather than patched locally — adjudication #2122, PR #2153 (L0's fix) merged and
verified live (cycle 130), closing F-D21/F-D23.

**D-SERVICE (P8).** The Serving Density Principle (CLAUDE.md §N.6) rollout is L1's largest
cross-cutting D-SERVICE contribution this wave: `density_contract`/`empty_reason` declared on
every capability that lacked them (F-C21, F-D18, F-D25, F-E8, F-E28 — 8 files across the NOW/
MUST tiers). Two named built-but-unplugged instances found and fixed: `ga_nakshatra`'s tool
(F-B18/F-B19 — the tool named for the asset served nothing) and `ga_vastu`'s remedy join
(F-E10/E11). `ga_prashna` remains a deliberate dormant D-SERVICE facility by native ruling
(R-1) — live-mounted, real casts exist, but intentionally not a general-purpose query surface.

## §3.5 — Findings that outgrew L1

Two L1 findings became cross-layer adjudications rather than in-layer fixes (both now resolved)
— recording them here in the same spirit as L5's §3.5, since Phase Z's interest in this layer is
partly *not* confined to L1's own assets:

1. **Adjudication #2122 (F-D21/D22/D23, `ga_transit_anchors`) — a serving-layer defect whose
   root cause is L0's, not L1's. CLOSED.** `from_moon_view`'s primitive passed
   `reference_point:"moon"` to `ganita_transit_anchors_get`, which never read it — traced to the
   actual call site (`platform/src/lib/vidhi/registry_data.ts`, L0-owned) rather than patched at
   the L1 asset it appeared to implicate. L0's fix (PR #2153, merged) re-points the primitive at
   the correct tool and dropped the inert argument, fixing both the code AND the already-
   committed live `vidhi_primitives` row (migration 705). Independently re-verified live by this
   session (cycle 130) rather than trusted on the merge alone: confirmed `live_tool=
   'ganita_transit_anchors_get'` / `tool_args={"chart_id":"{chart_id}"}` in both `origin/main`'s
   source and the live database row.
2. **Adjudication #2156 (migration-range encroachment) — L3 mistakenly used 3 of L1's granted
   840-859 migration numbers (848-850) for its own `ka_*` health-probe migrations.** Filed
   decide-and-log (cycle 124) rather than blocking; RULED and CLOSED by the Conductor (cycle
   127): root-caused to L3 having 8 free numbers in its own 730-739 range and using the wrong
   block by mistake (not a legitimate exhaustion case), 848-850 recorded as a permanent
   authorized L3 exception inside L1's block, L3 redirected to 732-739 going forward, no L1
   action required. Worth Phase Z's attention as a general migration-range-hygiene case: the
   collision was caught by L1's own housekeeping (confirming the next free number before use),
   not by any automated guard.
3. **Adjudication #2113/#2180 (chart-rebuild blocker) — re-diagnosed, RULED, wave 0 EXECUTED
   cycle 155; new blocker found and posted, awaiting reply.** Re-investigated live rather than
   re-checking a stale issue comment: `ga_positions` (the DAG root, zero declared dependencies)
   is immune to the originally-reported `asset_freshness` gate by construction, and its
   2026-09-05 failed dispatch was actually a now-fixed writer crash (#1856, PR #1861). Checked
   what changed in `ga_positions_writer.py` since its last acceptance — PR #1898 (issue #1747)
   removed `build_id` from `fact_id`'s derivation, meaning a fresh build produces different
   `fact_id` values than what's currently stored. Found `ga_yoga_firings.constituent_fact_ids`
   stores (rather than re-derives) exactly those values (36/40 refs) — a `ga_positions`-only
   rebuild would have silently orphaned them. Escalated as #2180; **the Conductor RULED
   2026-09-07T00:45:28Z**, confirming the corrected waves-0-3 coordinated-rebuild scope (15
   assets, superseding the original 5-asset framing) and authorizing dispatch.
   **Wave 0 dispatched and completed, same cycle**: fresh Cloud SQL backup, `--commit
   --acknowledge-destroys` for the WP-6 blast radius (`chart_fact_identity`, in-layer, ~530 rows
   scoped — not the tool's naive 270,471 whole-table count, a self-correction of this session's
   own earlier, imprecise "writer reinserts it" claim). `ga_positions` reached `state='lit'`.
   Found and closed a related gap unprompted: `chart_fact_identity` is repopulated by a
   SEPARATE standalone script (`build_fact_identity_index.py`), not the orchestrator writer —
   re-ran it post-dispatch, restored to 125,593 rows for the canonical chart.
   **New blocker surfaced, not yet resolved**: `asset_freshness.freshness_state` for
   `ga_positions` is `'unknown'`, not `'fresh'` (`asset_registry.natural_key_partition` empty) —
   `asset_runner.py`'s DEP-ASSERT gate requires exactly `'fresh'`, so wave 1 may still be blocked
   by a registry-configuration gap distinct from the one #2180's ruling addressed. Posted to
   #2180; did not attempt wave 1. Worth Phase Z's attention as a general pattern beyond this one
   rebuild: a writer's own identity-derivation change (even a deliberately correct one) can
   create a transition hazard for any downstream table that stores rather than re-derives the
   changed value, and a "freshness row exists" check is not the same claim as "freshness row
   reads fresh" — the same §N.8 distinction this campaign has hit before at other layers.

## §4 — Cost actuals vs forecast

**OPEN.** Session token/wall-clock actuals not tracked against a forecast this segment — unlike
L5's report, no per-cycle cost ledger has been reconciled yet (the charter names "reconcile cost
ledger" as a distinct, still-undone priority-5 prep item, separate from this close-report draft).
Registry `estimated_seconds` re-measurement is a related but distinct exercise, and where done
this wave produced real corrections: `ga_positions` (was 5s, measured mean 17s/n=54, migration
847) and `ga_condition` (was 30s, measured mean 71s/n=51, migration 847) — both re-baselined
from live `build_run_assets` data, not estimated. A full session-level cost actuals section
awaits either a dedicated prep cycle or genuine W6 close.

## §5 — Backlog handed forward

**To Phase Z / the Conductor:**
- **Adjudication #2113/#2180** — RULED cycle 155 (waves 0-3, 15 assets, confirmed); wave 0
  (`ga_positions`) dispatched and completed the same cycle (see §3.5 item 3). **Still open**:
  a NEW blocker posted to #2180 cycle 155 — `ga_positions`' `asset_freshness.freshness_state`
  is `'unknown'` not `'fresh'` (`asset_registry.natural_key_partition` empty), and
  `asset_runner.py`'s DEP-ASSERT gate requires exactly `'fresh'` for a dependency to pass. Only
  4 assets campaign-wide show `'unknown'` (vs. 34 showing `'fresh'`, all with a populated
  partition), so this looks like a fixable registry-configuration gap rather than a structural
  wall — but it is genuinely unresolved as of this writing and may block wave 1 for every layer,
  not just L1.
- **Adjudication #2122** (PR #2153, L0's fix for the `from_moon_view` mis-pointing) — CLOSED,
  merged and independently re-verified live (cycle 130). Recorded here so Phase Z sees the
  L1-visible symptom (F-D21/D23) was correctly attributed to L0's root cause, not re-litigated
  as an L1 defect nor silently forgotten once fixed.
- **The `l1_integrity_check_dry_run.sql` script** (PR #2163) is ready for immediate use the
  moment #2113 clears — it needs no changes to serve as the mechanical-check half of L1's real
  W5 pass.

**To L1's own future work (does NOT need #2113 — genuinely unheld, highest-priority open item):**
- **F-B33 — CLOSED cycle 147** (PR #2191, queued): `concept_aliases.ts`'s docstring no longer
  claims `platform/scripts/census/schema_map_alias_coverage_check.ts` is a real, running CI
  check — corrected to state honestly that no such gate exists yet. This closes the
  false-citation half; it does not build the check itself (see F-B32 below, which the check
  would need to share a live-category derivation with anyway).
- **F-B32 — still OPEN, now precisely quantified (cycle 148)**: the correct comparison is the
  canonical chart's own live category count (219, `WHERE chart_id='482012f1-...'` — NOT an
  unscoped cross-chart count; cycle 146's "223" was mis-scoped and is corrected in §2). The gap
  has NOT grown since the original W1 measurement — it is flat at 169-vs-219. Concrete diff
  (`comm` against the live canonical-chart category list, cycle 148): **57 categories present
  live are missing from the 169-list** (full list recorded in this session's cycle-148
  scratchpad; spans nearly every section of the file — ashtakavarga, graha_avastha-per-varga,
  KP, nakshatra-relationship, special-lagna, and more — not concentrated in one area, so no
  single section owner can absorb the whole fix); **6 entries in the 169-list are phantom** —
  `ashtakavarga_anubindu`, `dosha_fires`, `esoteric_point_chatushphuta`,
  `esoteric_point_panchasphuta`, `esoteric_point_trisphuta`, `yoga_fires` do not exist as a
  `fact_category` value for ANY chart in the table (not just the canonical one) — these look like
  stale/renamed names (the real live categories are `yoga_label`/`dosha_label`, already
  separately and correctly listed) and should be investigated (real category that was renamed?
  never-implemented aspiration?) before either removing or re-pointing them; one entry
  (`karaka_web_per_varga`) is real (2,945 live rows) but not yet built for the canonical chart —
  not a list defect. The actual edit (assigning each of the 57 to a verified real serving tool,
  and resolving the 6 phantoms) needs per-category verification against real serving code and is
  still too large for one bounded cycle. **Being closed incrementally instead of in one bulk
  pass, cycle 149 onward, all landing on the same PR #2193**: slice 1
  (`graha_avastha_baladi_per_varga`, `_deeptaadi_per_varga`, `_jagradadi_per_varga`,
  `_lajjitadi_per_varga`, `_sayanadi_per_varga` — 5/57), verified via `get_avasthas.ts`'s own
  data-driven query (opt-in via the `categories` param, same doctrine as the file's existing
  `ashtakavarga_bindu_per_varga` precedent); slice 2 (`graha_cheshta_bala_per_varga`,
  `graha_drik_bala_per_varga`, `graha_kala_bala_per_varga`, `graha_sthana_bala_per_varga` —
  4/57), same doctrine verified against `get_strength.ts`'s equivalent query; slice 3 (the
  `get_nakshatra.ts` cluster — `graha_nakshatra_join`, `graha_pada_join`, `graha_kp_lords`,
  `cusp_kp_lords`, `graha_gandanta`, `nakshatra_dispositor`, `nakshatra_conjunction`,
  `nakshatra_cogravity`, `graha_tara_bala`, `nakshatra_statistics`, `kp_house_significators`,
  `kp_planet_significations` — 12/57), a tool that (per F-B18/F-B19) previously had NO dedicated
  serving tool at all and had ZERO entries anywhere in this file despite its own
  `NAKSHATRA_CATEGORIES` const naming 16 categories — 3 of that const's own categories
  (`nakshatra_lord_placement`, `graha_degree_flags`, `nakshatra_exchange`) were checked and
  found to have ZERO live rows, so deliberately NOT added (a separate tool-docstring-overclaim
  finding, not this one); 3 more from the missing-57 list that look nakshatra-adjacent by name
  (`nakshatra_co_tenancy`, `nakshatra_dispositor_chain`, `nakshatra_lord_relationship`) do not
  appear in `get_nakshatra.ts`'s own list at all and were left for a future slice rather than
  guessed. Slice 4 (5/57): two sub-clusters — `special_lagna`, `upapada_lagna`,
  `sensitive_point_gulika_mandi` (opt-in via `get_sensitive_points.ts`, corroborated by
  `tool_name_bridge.ts:87` mapping the retired `query_special_lagnas` tool name onto the same
  URI); `sensitive_degree_check`, `sensitive_point_yogi` (`get_sensitive_degrees.ts`, served
  UNCONDITIONALLY, no opt-in ambiguity). Slice 5 (1/57): `ayurdaya` — `get_ayurdaya.ts`
  unconditionally serves this via a hardcoded `fact_category = 'ayurdaya'` filter, the simplest
  case yet. Slice 6 (3/57): `bhava_cusps` (`get_kp_cusps.ts`'s dedicated KP-cusp tool, CR-30 —
  spreads its fixed `KP_CATEGORIES` const unconditionally, no caller override; the other three
  categories in that const were already covered via `get_karakas`) + `house_bhava_bala_ratio`,
  `house_chalit` (opt-in via `get_bhava_bala.ts`, same data-driven doctrine as every prior
  opt-in slice). Slice 7 (1/57): `dispositor_tree` — opt-in via `get_dispositors.ts`'s
  data-driven query, 1450 live rows. All seven slices confirmed via live row counts before
  adding. **31/57 closed, ~26/57 remain open**; the 6 phantom entries and the get_nakshatra.ts
  3-category docstring overclaim are both untouched (need their own separate investigation
  before either removing or re-pointing). **New finding, cycle 153**: `graha_yuddha_per_varga`
  (17 live rows) was checked against `get_graha_yuddha.ts` and found genuinely UNREACHABLE by
  any tool — that tool hardcodes `fact_category = 'graha_yuddha'` (a bare, zero-row category for
  this chart) with no `categories`-override mechanism, unlike every other per_varga category
  closed so far. This is a deeper defect class than F-B32 itself (a real computed category with
  no serving path at all, category-granularity version of the original F-B18/F-B19 "asset has no
  tool" finding) and is tracked separately, not folded into the F-B32 tool-mapping work.
  **Reframing finding, cycle 156**: a systematic sweep of every remaining category name against
  every `L1_ganita/*.ts` file found `dispositor_tree` was the ONLY one with a real serving tool
  — the other ~25 (`aspect_received_by_special_point`, `bhava_significance_link`,
  `chart_center_of_gravity`, `chart_cluster`, `conjunction_special_point`, `contradiction_pair`,
  `esoteric_point_sphuta_fertility`, `esoteric_point_yogi_system`, `graha_centrality`,
  `kendradhipati_dosha`, `nakshatra_co_tenancy`, `nakshatra_dispositor_chain`,
  `nakshatra_lord_relationship`, `net_argala_per_varga`, `nway_config_per_varga`,
  `panchadha_maitri`, `sambandha_grade`, `sandhi_flag`, `significator_path`,
  `sun_derived_upagraha`, `tara_bala` bare, `virupa_drishti`, plus `graha_yuddha_per_varga` and
  `karaka_web_per_varga` above) have ZERO hits anywhere — genuinely unreachable by any tool, the
  same defect class as `graha_yuddha_per_varga`. This reframes what remains of F-B32: no longer
  mostly "a stale list needs new entries," mostly "these categories have no serving tool at
  all" — new-endpoint work, out of scope for this hand-maintained list's own repair.

**To L1's own future work (once #2113 clears):**
- W4 dispatch for all 19 assets, `rebuild_only` majority per §1's route column.
- W5: run the dry-run script fresh post-rebuild (the 4 currently-expected FAILs should flip to
  PASS — if any does not, that is new information, not the already-tracked residual).
- A full 139-row per-finding disposition table (§2's own noted OPEN item).
- Session-level cost actuals reconciliation (§4's own noted OPEN item).

## §6 — OPEN

Per-finding disposition table (§2) · cost actuals (§4) · **F-B32 real fix (§5 — F-B33 closed PR
#2191 cycle 147; F-B32 quantified cycle 148 at 57 missing/6 phantom categories; slices 1-7 (31
categories) landed cycles 149-156, PR #2202; ~25 remaining reframed cycle 156 as genuinely
unreachable by any tool — a tool-coverage gap, not a list-staleness gap; plus 6 phantoms and
get_nakshatra.ts's own 3-category docstring overclaim remain, unheld, does not need
#2113)** · **~25 genuinely-unreachable categories, `graha_yuddha_per_varga` included (§5 — new
cycle 153/156, distinct from F-B32's own list-repair scope)**
· W4 partially unblocked (wave 0 dispatched cycle 155; wave 1 blocked on `natural_key_partition`,
posted #2180) · W5
capsules (blocked, same gate) · the Conductor's freeze-ordering ack · closure-safe sync proof ·
this file's own promotion from DRAFT to a real close claim, which requires W4/W5/W6 to actually
run — nothing in this file should be read as asserting that has happened.
