---
artifact: L1_W6_CLOSE_REPORT_v1_0.md
canonical_id: NIRMANA_L1_W6_CLOSE_REPORT
version: "0.4-DRAFT"
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
re-verified LIVE cycle 146 and is genuinely **still open** — the drift has in fact worsened (169
vs. 219 at original measurement, 169 vs. **223** live cycle 146). See §2 for the corrected
disposition and §5 for the forward item; NEVER-LATER correctly parked by design) but **not yet
formally declared closed** (that ruling belongs to the Conductor/native, not a unilateral session
call — see the W3 STATUS SNAPSHOT in `L1_STATE.md`) · **W4 ⛔ BLOCKED, but no longer on the
gate this section originally named.** Adjudication #2113 was raised as a campaign-wide
`asset_freshness` gate (zero L1 dependency-asset rows) blocking any L1 rebuild; re-investigated
live (cycles 132-133) and found the real picture is more specific: `ga_positions` (L1's DAG root,
zero declared dependencies) is IMMUNE to that gate by construction, and its true blocker was a
now-fixed writer crash (#1856) plus a stale W2 acceptance pin — both concretely diagnosed. But
pursuing that unblock surfaced a SECOND, more consequential finding before any dispatch was
attempted: `ga_positions_writer.py`'s `fact_id` derivation changed since its last acceptance (PR
#1898 removed `build_id` from the hash — a real, good, already-merged fix), and
`ga_yoga_firings.constituent_fact_ids` (36/40 refs on the canonical chart) resolves to exactly
`ga_positions`' own categories — a `ga_positions`-only rebuild would orphan those references.
**W4 is now blocked on a coordinated-rebuild-sequencing question, not an infrastructure gap** —
posted to #2113, awaiting a reply as of this writing · **W5 ⛔ BLOCKED** (no completed post-W4
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
| 1 | `ga_positions` | 890 / 50 | `rebuild_only` | layer root/canary; F-A16 fixed (migration 847) |
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
- **MUST** — CLOSED for L1's own scope (cycle 125) **with one correction found cycle 146**:
  F-B32/F-B33 was carried in cycle 125's own closure sweep as closed, but was never actually
  fixed — it was, and still is, genuinely OPEN. Re-verified LIVE cycle 146:
  `platform/src/lib/retrieval/registry/layers/L1_ganita/coverage_matrix.ts` still declares
  exactly 169 hand-maintained `fact_category` entries (file header unchanged since 2026-06-16),
  against a live `SELECT count(DISTINCT fact_category) FROM chart_facts` of **223** (the gap has
  widened since the original 169-vs-219 measurement — consistent with the F-A14 `ga_structural`
  campaign's category additions this segment). Separately, `concept_aliases.ts:14` still cites
  `platform/scripts/census/schema_map_alias_coverage_check.ts` as an existing CI regression check
  ("asserts every LIVE fact_category has at least one alias entry"); that file **does not exist**
  anywhere in the repo (confirmed by direct path check and a repo-wide grep for
  `alias_coverage`, cycle 146) — the same false-citation defect the original W1 finding
  described, unchanged. Both halves are un-fixed; cycle 125's "closed" note for this id-group was
  incorrect and is corrected here rather than carried forward silently (§N.8: an unverified "all
  clear" is null, not a fact). Handed forward as the next unheld MUST-tier item in §5 — the fix
  (re-deriving the 169-item list against the live 223 categories, and either implementing the
  cited CI check or correcting the docstring to stop citing a file that doesn't exist) is
  substantial enough that it was not attempted as this cycle's bounded unit.
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
3. **Adjudication #2113 (chart-rebuild blocker) — re-diagnosed from "campaign-wide infra gap" to
   a specific, coordinated-sequencing question. OPEN, awaiting reply.** Re-investigated live
   rather than re-checking a stale issue comment: `ga_positions` (the DAG root, zero declared
   dependencies) is immune to the originally-reported `asset_freshness` gate by construction, and
   its 2026-09-05 failed dispatch was actually a now-fixed writer crash (#1856, PR #1861 merged
   the same night, never retried). Before resubmitting its stale W2 acceptance and dispatching,
   checked what changed in `ga_positions_writer.py` itself since that acceptance — PR #1898
   (issue #1747) removed `build_id` from `fact_id`'s derivation, a real correctness fix, but one
   that means a fresh build produces different `fact_id` values than what's currently stored.
   Checked whether anything stores (rather than re-derives) those specific values and found
   `ga_yoga_firings.constituent_fact_ids` does (36/40 refs on the canonical chart resolve to
   `ga_positions`' own categories) — a `ga_positions`-only rebuild would silently orphan them.
   Did not dispatch; posted the finding and asked whether a coordinated multi-asset rebuild
   (`ga_positions` through `ga_yoga`) or a different sequencing is the right shape. Worth Phase
   Z's attention as a general pattern: a writer's own identity-derivation change (even a
   deliberately correct one) can create a transition hazard for any downstream table that stores
   rather than re-derives the changed value, independent of any campaign-wide gate.

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
- **Adjudication #2113** — no longer a simple campaign-wide `asset_freshness` gap (see §3.5
  item 3 for the full re-diagnosis). The one thing still worth Phase Z's attention from the
  ORIGINAL framing: `asset_freshness` holds rows for `bg_*`/L0 and a few `mi_*`/L5 assets only,
  zero for any L1/L2/L3/L4 asset — this may still matter for OTHER L1 assets whose dependencies
  are themselves L1 (unlike `ga_positions`, which is immune only because it has none). The
  ACTIVE open question is narrower and asset-specific: whether a coordinated `ga_positions`→
  `ga_yoga` rebuild sequencing (or an equivalent ruling) is needed before `ga_positions` can
  safely dispatch alone.
- **Adjudication #2122** (PR #2153, L0's fix for the `from_moon_view` mis-pointing) — CLOSED,
  merged and independently re-verified live (cycle 130). Recorded here so Phase Z sees the
  L1-visible symptom (F-D21/D23) was correctly attributed to L0's root cause, not re-litigated
  as an L1 defect nor silently forgotten once fixed.
- **The `l1_integrity_check_dry_run.sql` script** (PR #2163) is ready for immediate use the
  moment #2113 clears — it needs no changes to serve as the mechanical-check half of L1's real
  W5 pass.

**To L1's own future work (does NOT need #2113 — genuinely unheld, highest-priority open item):**
- **F-B32/F-B33 real fix** (reconfirmed open cycle 146, §2): re-derive
  `coverage_matrix.ts`'s `CHART_FACTS_CATEGORIES` against the live 223-category `chart_facts`
  universe (was 169 at cycle 146; drift is monotonically growing as writers add categories, so
  re-checking the live count at fix-time rather than trusting this report's 223 is required), and
  either implement `platform/scripts/census/schema_map_alias_coverage_check.ts` for real (the
  file `concept_aliases.ts:14` already claims exists) or correct that docstring to stop citing a
  CI check that was never built. Not attempted cycle 146 — scoped as substantial (a real category
  audit + either a new CI gate or a documentation correction with its own review), not a
  single-cycle bounded unit.

**To L1's own future work (once #2113 clears):**
- W4 dispatch for all 19 assets, `rebuild_only` majority per §1's route column.
- W5: run the dry-run script fresh post-rebuild (the 4 currently-expected FAILs should flip to
  PASS — if any does not, that is new information, not the already-tracked residual).
- A full 139-row per-finding disposition table (§2's own noted OPEN item).
- Session-level cost actuals reconciliation (§4's own noted OPEN item).

## §6 — OPEN

Per-finding disposition table (§2) · cost actuals (§4) · **F-B32/F-B33 real fix (§5 — reconfirmed
open cycle 146, unheld, does not need #2113)** · W4 execution (blocked, #2113) · W5
capsules (blocked, same gate) · the Conductor's freeze-ordering ack · closure-safe sync proof ·
this file's own promotion from DRAFT to a real close claim, which requires W4/W5/W6 to actually
run — nothing in this file should be read as asserting that has happened.
