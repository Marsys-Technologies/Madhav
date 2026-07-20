---
artifact: STRUCTURAL_CLOSES_W2.md
canonical_id: STRUCTURAL_CLOSES_W2
version: 1.0
status: LANE-COMPLETE
type: investigation + serving-side fix record (Retrieval Plane Elevation, W2 structural-close lane)
governing_brief: RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md; RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md §8.5 R-1.5.3
scope_source: RETRIEVAL_STRATEGY_v1_0.md §5.2 open structural register rows: G-1, S-3, SC-2, SC-3, SC-4, SC-5
date: 2026-07-20
---

# Structural Closes W2 — G-1 / S-3 / SC-2 / SC-3 / SC-4 / SC-5

## Lane scope and honest headline result

The master brief scoped this lane serving-side only: no writer changes, no orchestrator
changes; anything that turns out to need writer work gets specced here instead of built. All
five items were investigated by reading the writer source that computes each concept, checking
live `chart_facts`/`bodha_cgm_*` rows against the canonical chart (`482012f1-…`) via the
`retrieval_census_ro` read-only DB role, and reading the current serving-side TS registry code
that either does or doesn't reach that data.

**Result: all five items closed via genuine serving-side fixes. Zero items required writer
work.** This was not a foregone conclusion — the brief explicitly anticipated "it's entirely
plausible ALL FIVE of these turn out to be writer-side." They didn't: in every case the L1
writer had already computed and stored the concept in `chart_facts` (or, for G-1, the writer
fix had already landed in an earlier wave, pre-dating this campaign); what was actually missing
was a serving route, a discoverable default-page inclusion, or — in G-1's case — nothing at
all (the register row was simply stale).

One genuine writer-only residual surfaced during SC-2's investigation (numeric natal `speed_dps`
never persisted to `chart_facts`) and is specced below, not built.

## G-1 — CGM bhava edge-orphans (breaks graph chains through houses)

**Disposition: ALREADY RESOLVED, no code change needed. Register row is stale.**

The register (`MARSYS_DEFECT_GAP_REGISTER_v2_0.md` G-1, `RETRIEVAL_STRATEGY_v1_0.md` §5.2)
describes an edge-type census with no `lordship`/`occupancy` classes and the specific failure
"Saturn (11L) cannot reach his own bhava-11 node (`path_found:false`)."

Investigation:
- `platform/python-sidecar/pipeline/orchestrator/writers/bo_karanajala.py` already contains
  `_build_bhava_edges`, `_fetch_bhava_lordship_facts`, `_fetch_occupancy_facts`, and a
  `_BHAVA_EDGE_META` table for `lordship`/`occupancy` edge types (git blame: commit `912fdb5a`
  "feat(wp-2.3): CGM graph-structure completion — graha↔bhava edges + yoga nodes [LCA-9a-1]",
  landed well before this campaign opened).
- Live DB check (`bodha_cgm_edges`, chart `482012f1-…`, ayanamsha `lahiri_chitrapaksha`):
  `edge_type` distribution includes `lordship` (60 rows), `occupancy` (45 rows) alongside
  `aspect`/`argala`/`bhava_aspect`/`dispositor`/`arudha_house`/`special_lagna_house`/
  `dosha_domain`/`yoga_member` — the full set the register said was missing two of.
- The exact scenario the register cited: a live query for the edge between the Saturn `graha`
  node and the bhava-11 node returns one `lordship` edge, `direction: directed`,
  `computed_strength: 0.579241125` — Saturn (11L) DOES reach his own bhava-11 node today.
- Serving side: `platform/src/lib/retrieval/registry/layers/L2_bodha/traverse_chart_graph.ts`
  (the current CGM traversal capability, superseding the retired `get_cgm_subgraph.ts`) already
  handles `edge_types` as a fully generic, unfiltered pass-through (`e.edge_type IN (...)`) —
  there is no bhava-node exclusion or edge-type allowlist in the BFS/paths SQL. `lordship`/
  `occupancy` edges are traversed exactly like every other edge type, with no code change
  required.

**Conclusion:** the underlying writer defect this register row named was fixed in an earlier
wave (`912fdb5a`), and the serving tool that would need updating to surface the fix was already
generic enough to require none. No code touched for G-1. Recommend the native/conductor update
`MARSYS_DEFECT_GAP_REGISTER_v2_0.md` G-1 status from OPEN to CLOSED/STALE and note the same in
`RETRIEVAL_STRATEGY_v1_0.md` §5.2's "(e) still-open register rows" bullet — not done here
(register files are outside this lane's `may_touch`).

## S-3 — bhava_arudha (computed, unserved)

**Disposition: RESOLVED, serving-side fix implemented.**

`bhava_arudha` (A1–A12 + Arudha Lagna + Upapada, full Parashari 2-exception rule) is computed
by `platform/python-sidecar/ga_writers/ga_sensitive_writer.py`
(`_build_bhava_arudha_rows`, category `"bhava_arudha"`) and confirmed live in `chart_facts`
(42 rows per ayanamsha for the canonical chart — `sign`/`longitude_sidereal`/`house_d1` per
subject `BHAVA_ARUDHA_A1..A12`/`BHAVA_ARUDHA_AL`/`BHAVA_ARUDHA_UPA`). No serving tool read this
category — `get_karakas.ts` served only the sibling `arudha_pada` category (confirmed by
reading the file: `KARAKA_CATEGORIES` list had 9 entries, none `bhava_arudha`).

**Fix:** added `bhava_arudha` to `get_karakas.ts`'s default `KARAKA_CATEGORIES` (small row
count, same shape as the sibling `arudha_pada` already on the default page) and updated the
tool description + header comment. Also registered in `coverage_matrix.ts`
(`CHART_FACTS_CATEGORIES` + `CATEGORY_TOOL_COVERAGE`).

File: `platform/src/lib/retrieval/registry/layers/L1_ganita/get_karakas.ts`

## SC-2 — graha speed/retro/combustion refinements

**Disposition: MOSTLY ALREADY SERVED; documented + cross-referenced. One genuine residual is a
writer gap, specced below, not built.**

Investigation split the register's three named categories from the actual concepts:

1. **Retrograde + combustion state — ALREADY SERVED, pre-existing.** The writer
   (`platform/python-sidecar/ga_writers/ga_positions_writer.py`) emits `retrograde_flag` and
   `combustion_state` as keys under the `graha_position` category (not under the three
   register-named categories — see point 3). `get_positions.ts` already serves
   `graha_position` on its default page (CR-50) and its description already states "retrograde
   status, and combust status." No fix needed here; only the register's phrasing was
   misleading. Documented this explicitly in the tool's header comment so a future reader
   doesn't reopen SC-2 against the wrong category names.
2. **Numeric speed (degrees/day) for the natal moment — genuinely NOT in `chart_facts`.**
   `ga_positions_writer.py`'s `fact_atoms` list never emits a `speed_dps` value; a dead
   conditional at line ~300 (`if cat in ("graha_retrogression_state", "graha_combustion_state",
   "graha_speed_state") and key in (...)`) references category names `cat` is never actually
   set to in this writer — unreachable code, not a live path. **This is the one genuine
   writer-only gap this lane found.** See "Specced, not built" below.
   - It IS reachable today as a cross-reference, not a gap, per the coverage doctrine
     (`RETRIEVAL_STRATEGY_v1_0.md` §5.2 SERVED-VIA): `ephemeris_daily` (date range
     1899-1899‥2150, tropical, `speed_dps` + `is_retrograde` columns, confirmed live-populated
     for the chart's birth date) is already served by the existing L0 capability
     `query_planet_position(date=...)`. Documented this cross-reference explicitly in
     `get_positions.ts`'s header comment and description.
3. **The three register-named categories (`graha_speed_state`/`graha_retrogression_state`/
   `graha_combustion_state`) are dead/never-emitted category names — confirmed live: zero rows
   for any of the three, for any chart, in the entire DB.** They appear only in a GA3/GA8
   category-overlap guard list (`ga_structural_writer.py:4266-4267`) as reserved names never
   actually assigned to a row's `fact_category`. Requesting them from any tool would honestly
   return zero rows (not an error, not fabricated data) — noted so nobody chases these three
   literal names expecting live data.

File: `platform/src/lib/retrieval/registry/layers/L1_ganita/get_positions.ts`

## SC-3 — D1 parivartana_pairs category-split orphan

**Disposition: RESOLVED — was never actually a data gap, only a discoverability/naming
confusion. Serving-side clarification implemented.**

The register describes a "D1 parivartana_pairs category-split orphan" citing
`ga_structural.py:2557` (where a `parivartana_pairs` category is emitted in code) vs.
`get_dispositors.ts:12` (which serves only `parivartana_per_varga`).

Investigation:
- `parivartana_pairs` (the category the writer code appears to emit at
  `ga_structural_writer.py:3682`) has **zero live rows anywhere in the database, for any
  chart** — confirmed via `SELECT count(*) FROM chart_facts WHERE fact_category=
  'parivartana_pairs'` → 0. This code path is unreachable in the actual build (unlike G-1,
  no prior fix commit was found for this one — it appears to simply never fire; not
  investigated further since fixing writer logic is out of this lane's scope).
- The REAL D1 mutual-exchange data lives under `parivartana_per_varga` with `fact_subject`
  prefix `D1_*` (e.g. `D1_JUP_JUP`, confirmed live with real `mutual_exchange` values and
  citations) — and `parivartana_per_varga` is already served by `get_dispositors.ts` on its
  default page. So D1 parivartana was never actually unreachable; a caller just had no way to
  know it lives inside a per-varga category rather than a dedicated one.

**Fix:** updated `get_dispositors.ts`'s description + header comment to state explicitly that
D1 parivartana is the `D1_` slice of `parivartana_per_varga`, and that `parivartana_pairs` is a
dead category name that will always return zero rows.

**Incidental finding, NOT fixed (out of scope — would require writer-side investigation):**
the one live `D1_JUP_JUP` row reads `"Jupiter_in_Sagittarius_Jupiter_in_Sagittarius"` — a
same-planet self-pairing. Classical parivartana requires two distinct planets mutually
exchanging signs; a self-pair looks like a data-quality artifact in
`ga_structural_writer.py`'s D1 mutual-exchange detector, not a real parivartana. This is a
writer correctness question (not a serving gap), out of this lane's scope
(`ga_structural_writer.py` is `must_not_touch` FROZEN-adjacent L1 writer code) — flagged here
for a future native-sanctioned build session to investigate, not fixed.

File: `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dispositors.ts`

## SC-4 — Ashtakavarga refinement set (trikona/ekadhipathya shodhana, kakshya, per-varga bindu/pinda)

**Disposition: RESOLVED, serving-side fix implemented.**

Live DB check found 11 distinct `ashtakavarga_*` categories with real rows for the canonical
chart; `get_ashtakavarga.ts` served only 5 of them (`ashtakavarga_bindu`,
`ashtakavarga_anubindu` [dead, 0 rows], `ashtakavarga_pinda_bhinna`, `ashtakavarga_pinda_sarva`,
`ashtakavarga_pinda_sodhita`). The six missing, all real and computed:
`ashtakavarga_trikona_shodhana`, `ashtakavarga_ekadhipathya_shodhana`,
`ashtakavarga_kakshya_boundary`, `ashtakavarga_bindu_sign`, `ashtakavarga_pinda_raasi` (all
modest row counts, same order of magnitude as the existing default categories) and
`ashtakavarga_bindu_per_varga` (a large per-divisional-chart row set).

**Fix:** the five modest-size refinement categories were added to the default page; the two
large per-varga categories (`ashtakavarga_bindu_per_varga`,
`ashtakavarga_pinda_sarva_per_varga`) were added as documented opt-in categories reachable via
an explicit `categories` request (not the unconditional default — per the §N.6 density
discipline the CR-50 upagraha-facet pattern in `get_positions.ts` already established, a large
row set should not silently dominate/paginate out a tool's smaller default categories).
`ashtakavarga_anubindu` stays on the default list for back-compat but is documented as a dead
category name (zero live rows, any chart) — requesting it honestly returns nothing.

File: `platform/src/lib/retrieval/registry/layers/L1_ganita/get_ashtakavarga.ts`

## SC-5 — karaka_per_varga + nakshatra_cross_ayanamsha unserved; coverage matrix stuck 158 vs 187

**Disposition: RESOLVED, serving-side fix implemented (the coverage-matrix piece included).**

Live DB check: `karaka_per_varga` as a literal category name does not exist; the real,
computed, previously-unserved karaka categories are `karaka_web_per_varga` (per-varga karaka
relationships) and `karaka_bhava_concordance` (per-house karaka concordance) — both real, both
zero prior serving route (confirmed: zero references anywhere under
`platform/src/lib/retrieval/registry/` or `platform-mcp/src/`).
`nakshatra_cross_ayanamsha` (per-graha 5-ayanamsha nakshatra-stability check) is also real,
computed, and had zero prior serving route.

**Fix:**
- `karaka_web_per_varga` and `karaka_bhava_concordance` added as documented opt-in categories
  on `get_karakas.ts` (not the unconditional default — large row sets, same §N.6 rationale as
  SC-4).
- `nakshatra_cross_ayanamsha` added to `get_positions.ts`'s `categories` enum as a documented
  opt-in category (not the unconditional default — preserves CR-50's deliberate default-page
  discipline).
- The "coverage matrix stuck at 158 vs 187" half of SC-5: `coverage_matrix.ts`'s
  `CHART_FACTS_CATEGORIES` + `CATEGORY_TOOL_COVERAGE` updated to include all eleven categories
  this lane wired (`bhava_arudha`, `karaka_web_per_varga`, `karaka_bhava_concordance`,
  `nakshatra_cross_ayanamsha`, and the six ashtakavarga refinement categories), each mapped to
  its real serving tool URI. This is a narrow, additive fix scoped to exactly the categories
  this lane made servable — **not** a full reconciliation of `coverage_matrix.ts` against the
  live DB's full category set (218 live vs. 158 pre-existing in this array); that full
  reconciliation is separately tracked by W1's own `FACT_CATEGORY_ENUMERATION_
  RECONCILIATION_v1_0.md` / `chart_facts_categories_authoritative_v1.json` deliverables and
  intentionally out of this lane's narrower scope (per those artifacts' own explicit note that
  "no source file was migrated to consume the new authoritative JSON this wave").

Files: `platform/src/lib/retrieval/registry/layers/L1_ganita/get_karakas.ts`,
`get_positions.ts`, `coverage_matrix.ts`

## Specced, not built (the one genuine writer-only residual)

### SC-2 residual — numeric natal graha speed (degrees/day) not persisted to `chart_facts`

**What's missing:** `chart_facts.graha_position` (or a new category) has no `speed_dps`-shaped
numeric value for the natal moment. `ga_positions_writer.py`'s `fact_atoms` list (around line
274) would need a new tuple, e.g. `("graha_position", "speed_dps", <value>, None, "deg/day")`,
sourced from whatever field the underlying `pyjhora_adapter`/swisseph call already returns for
each `g` dict (the sibling `ephemeris_daily` writer path already extracts an equivalent value
via `pyjhora_adapter/transits.py`'s `speed_dps` field — the natal writer would need the
equivalent read from its own chart-computation call, not a copy from `ephemeris_daily`, since
the natal computation is a distinct code path with its own precise sub-day timestamp).

**Why not built here:** `ga_positions_writer.py` is L1 `ga_*` writer code — FROZEN-adjacent,
`must_not_touch` per this lane's scope declaration. Any change to what a writer computes and
persists requires a native-sanctioned build session per the master brief's explicit "no writer
changes" instruction.

**Why it's low-priority despite being unbuilt:** the concept (speed magnitude for the natal
moment, useful mainly for stationary-point proximity judgment) is already reachable today via
`query_planet_position(date=<the chart's own birth date>)` — a SERVED-VIA cross-reference per
the coverage doctrine, not a hard gap. A native-sanctioned build session should treat this as a
nice-to-have convenience (avoids a second tool call to get a value that's already
one call away), not a missing capability.

**Acceptance criteria for a future build session:** `chart_facts` gains a `speed_dps` fact
(unit `deg/day`) for each of the 9 classical grahas under `graha_position` (or a clearly-named
sibling category), correctly signed for retrograde motion, verified against the corresponding
`ephemeris_daily.speed_dps` value for the same instant/body within Swiss Ephemeris precision
tolerance; `get_positions.ts` then serves it with zero additional serving-side work (it's
already a `graha_position` field once the writer emits it).

## Verification run this lane

- `npx tsc --noEmit --skipLibCheck` (platform) — clean, 0 errors.
- `npx tsc --noEmit` (platform-mcp) — clean, 0 errors (confirms the descriptor-consuming mirror
  path is unaffected).
- `npx eslint` on all 5 touched files — clean, 0 errors (4 pre-existing `_ctx`-unused warnings,
  present before this lane's changes, unrelated to the edits).
- `npx vitest run src/lib/retrieval/registry tests/retrieval` (platform) — 672 passed / 125
  skipped, 0 failed, including the live coverage-gate test
  (`tests/retrieval/coverage_gate.test.ts`, which asserts every `CHART_FACTS_CATEGORIES` entry
  resolves to a registered capability — passes with all 11 newly-added categories).
- `npx vitest run` full platform suite — 506 files / 5939 passed / 317 skipped / 1 todo, 0
  failed. No regression anywhere in the estate from these five additive descriptor/query
  changes.
- No live DB write of any kind — all live-DB checks in this lane were `SELECT`-only via the
  `retrieval_census_ro` read-only role (W0.5's provisioned credential) or the equivalent
  read-only MCP Postgres tool. No migration, no writer file, no orchestrator file touched.

## A note on this lane's working conditions

Partway through this lane, a concurrent process/session sharing this exact worktree
(`impl/wave-2b`) advanced the branch HEAD (merge commit `756365a0`, "docs/w2-phase1-deploy-
verified") while this lane's edits were staged uncommitted in the working tree; four of the
five edited files were silently reverted to match the new HEAD (a fifth, `coverage_matrix.ts`,
partially survived). This was caught by an unprompted git-status check, not assumed — all five
files' edits were then reapplied and immediately re-verified via `git diff --stat` before
running the verification suite above, and the branch HEAD was confirmed unchanged
(`756365a0`) for the remainder of the session. Recorded here because a shared, uncommitted
worktree is a real hazard for any future session working the same branch concurrently with
another agent — this lane's final diff is correct and verified, but the collision itself is
worth the conductor's attention for how future waves sequence concurrent lanes against a shared
worktree.

---

*End of STRUCTURAL_CLOSES_W2.md v1.0 (2026-07-20) — G-1/S-3/SC-2/SC-3/SC-4/SC-5 investigated
and closed serving-side; one genuine writer-only residual (SC-2's numeric natal speed) specced
for a future native-sanctioned build session.*
