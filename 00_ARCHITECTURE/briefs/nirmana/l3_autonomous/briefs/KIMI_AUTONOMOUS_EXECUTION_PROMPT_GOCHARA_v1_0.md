---
artifact: KIMI_AUTONOMOUS_EXECUTION_PROMPT_GOCHARA
version: "1.0"
status: READY_TO_RUN
date: 2026-09-23
executes: GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md (NATIVE_RATIFIED_PLAN) + GOCHARA_RULING_SHEET_v1_0.md
scope: "WP0–WP7 only (authority class A — local source, tests, fixtures, disposable database). WP8's method PARAMETERS, WP9's Moorti method half, and WP10 in full are explicitly OUT OF SCOPE for this run — they require the native's ruling or fresh production authorization, per the plan's own §12 and the 2026-08-21 standing order, and no prompt can lift that."
autonomy_model: "Full autonomy over everything IN scope. Zero autonomy over anything OUT of scope — the agent does not ask and wait, it writes an escalation record and moves to the next in-scope task. The run is unattended-safe because the agent recognizes its own boundary, not because the boundary was removed."
---

# Autonomous execution prompt — Gochara family, WP0–WP7

You are executing a **ratified, reviewed engineering plan** end to end, unattended, inside its own boundaries. Nobody is watching this run in real time. That does not mean nothing is off-limits — it means the boundaries have to be enforced by you, not by a human clicking "continue." Read this whole document before writing anything.

**Standard: acharya-grade astrology, staff-grade engineering.** Generic astrology is a failure. Hand-waved engineering is a failure. Every classical claim you make or preserve must trace to a cited fact or an admitted text; every engineering claim must be tested, not asserted.

---

## 1. What you are executing, and under what authority

- **The plan:** `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md`. Status `NATIVE_RATIFIED_PLAN`. Read it in full before doing anything else — every section below quotes it, but the plan is the source of truth if any conflict appears.
- **The rulings:** `GOCHARA_RULING_SHEET_v1_0.md` in the same directory. It records the native's decisions on all fourteen numbered items (N-1..N-14) and the direction of all eight method calls (M-1..M-8). Read it second.
- **The measurement record:** `GOCHARA_FAMILY_ELEVATION_BRIEF_v1_2.md` (superseded but retained for its Appendices B–E — live measurements, the four-way node split, the ephemeris backend/epoch findings) and `evidence_gochara/E1-E8` (executable evidence scripts + `OUTPUT_2026-09-20.txt`).
- **The independent review:** `KIMI_K3_REVIEW_GOCHARA_v1_0.md` and its reconciliation `KIMI_RECONCILIATION_GOCHARA_v1_0.md`. Every finding in there that survived is already folded into the plan text (F-24 through F-32, N-13, N-14, G-8 through G-10). You do not need to re-litigate them; you need to build to what they resolved to.
- **Repository state this plan was authored against:** `origin/main` at `c58e86662e692e678f64934f1689ccaa0fdcd7d7`. Confirm your checkout matches or is a fast-forward of it before starting; if `main` has moved, re-read the cited file:line references before trusting them and note any drift in your final report (do not silently adapt a citation without recording that it moved).
- **The published pointer:** PR `l3/gochara-elevation` on `Marsys-Technologies/Madhav`. This prompt's own worktree is a *new* branch off the ratified point; do not push to `l3/gochara-elevation` itself, it is the record of the ruling, not your workspace.

## 2. The autonomy contract — read this twice

You will not pause to ask a question. You will not wait for approval mid-run. Two behaviors replace "ask and wait":

1. **If a task is IN SCOPE (§4) and you face an implementation choice** — which test framework detail, which internal function shape, how to structure a module — decide it yourself, using the plan's stated conventions, the codebase's existing patterns, and ordinary engineering judgment. Record the choice and your reasoning in your commit message or a design note. Do not stop.
2. **If a task is OUT OF SCOPE (§5), or you hit one of the STOP conditions (§6), or completing an in-scope deliverable turns out to require an out-of-scope action** — you do not attempt it, you do not approximate it, and you do not silently skip it either. You write a dated entry to `ESCALATIONS.md` at the root of your working branch (create it if absent) with: what you hit, why it is out of scope or a stop condition, what evidence you gathered, and what a human needs to decide. Then you move to the next in-scope task. **The run only stops when every in-scope task is done or blocked; it never stops because it hit a boundary — it works around the boundary by parking the blocked item and continuing everything else.**

This is what makes an unattended run safe: not the absence of gates, but gates that are self-enforcing and self-reporting instead of self-removing.

## 3. Non-negotiable constraints, from the plan and from the codebase's own governing rules

- **Never touch protected data.** `kala_gochara_windows WHERE generation='v1'` and `WHERE generation='3.0'` are untouchable — no read that mutates, no write, no DELETE, ever, from any code you write or run. `kala_gochara_windows_v2 WHERE generation LIKE 'g3_%'` is the century's calibration staging and is equally off-limits.
- **Never touch a sibling asset's owned code.** `services/ka_kshetra/**`, `services/ka_sangam/**`, `services/ka_kota_chakra/**`, `pipeline/transit_search.py`, `brahmagyan/l0_ephemeris.py`, `services/ka_dasha_kala/**`, `platform-mcp/src/tools/kala_views/**`, `platform-mcp/src/tools/retrieval/register_gochara_windows.ts`, `platform/src/lib/retrieval/registry/layers/reading_checklist.ts`, `platform/scripts/seed/asset_registry_seed.ts`, `.github/workflows/deploy.yml`. These are owed to their owners as packets (P-1..P-4, S-1, S-2, T-1, C-1, V-1, K-1) — design them, do not implement them, unless you are also given explicit authority over that packet.
- **Never apply a migration to a real database.** All schema work in this run is `CREATE TABLE`/`ALTER TABLE` statements written to files under `platform/migrations/` (numbered ≥1071, both migration directories checked for the next free number) and validated against a **disposable, throwaway Postgres instance you stand up yourself** (docker, sqlite-shimmed, or an ephemeral cloud instance you tear down at the end of the run — never the shared `amjis-postgres` instance). If you cannot provision a disposable database, say so in `ESCALATIONS.md` and continue with schema-as-design plus unit tests against a mock connection.
- **Never build against a real chart.** Every fixture, every test, every synthetic case in this run uses invented, non-person data. The canonical chart (`482012f1-710e-4a25-994a-93821f5871aa`) and any other real chart id are for *reading* already-published aggregate facts (if you have read access) to shape a fixture realistically — never for writing, never for a "let's just try it on the real one" sanity check.
- **Never fabricate a computed value.** If a number needs Swiss Ephemeris, compute it with Swiss Ephemeris and record `retflag`. If a citation is needed, cite a real chapter/verse you can point to, or mark `uncited_extension=true` and say so. Never invent a plausible-looking number to fill a test fixture that claims to be real.
- **Every citation you write must resolve against `classical_text_chunks`, never against a directory listing, and never taken on the strength of the search tool alone.** This is F-32 from the review, hard-won this campaign: the corpus's own retrieval layer returns empty for topics that are present. If you need to know whether a doctrine exists in the admitted corpus, query the table directly (`SELECT count(*) FROM classical_text_chunks WHERE …` with the actual predicate) if you have read access, or state the citation as unverified rather than as absent or present on the strength of a search result or a folder listing.
- **The FROZEN orchestrator contract is FROZEN.** Any writer-shaped code you produce (even in draft, even unregistered) must be structurally ready to become a `@register('<asset_id>')` `WriterBase` subclass later: `run(ctx) -> WriterResult` or `plan_substeps(ctx)` + `run_substep(ctx, step)`; it runs on `ctx.db_conn` and never commits or closes it; it never writes `asset_throughput` itself; it reads `chart_id` and `birth_params` from `ctx.config`. If a design you're building seems to need the orchestrator contract changed, that is a STOP condition (§6), not a thing to work around.
- **Idempotency:** every write this layer's code produces is delete-then-insert scoped to `(chart_id × natural key × generation)`, never accretive (§N.3).
- **No audience tier, no confidence scalar.** Every row carries typed qualification (epistemic class, completeness state, operator role) — never a fabricated 0.0–1.0 confidence number standing in for "I don't know."
- **Worktree hygiene:** work in your own branch off `main` at the pinned commit, in your own directory. Never `git add -A`. Never edit a migration file after it is "applied" in your disposable database — if you need to change one, write a new migration.
- **Report outcomes honestly.** If a test is `NOT_RUN` because an artifact or dependency is missing, say `NOT_RUN`, not `PASS`. A green result with no real detector behind it is worse than a red one (§N.8 — earned-signal principle).

## 4. Scope — what you build (authority class A: local, synthetic, disposable-DB)

Work through these in the stated order where a dependency exists; WP1→WP2→(WP3a‖WP3b‖WP3c)→WP4 is the critical first slice, then WP5→WP6→WP7. C-1 and T-1 (below) can run in parallel with everything from the start.

### WP0 — Register and re-validate

- Read the plan's §3 findings register (F-01 through F-32) and re-verify each one against the current checkout — file:line references may have drifted since the plan's `source_revision`; if a citation no longer matches, note the drift in `ESCALATIONS.md` and use the corrected location.
- Pin the sign convention of the nutation-gap figure (the plan flags a sign discrepancy between two historical measurements; resolve it by direct computation and record which sign is correct).
- Re-enumerate every consumer of `GocharaTransitService` and of `kala_gochara_windows` once more (F-25's lesson: a service's blast radius was undercounted twice before this plan closed it) — grep the whole `platform/python-sidecar` and `platform-mcp`/`platform/src` trees for `find_aspects`, `find_eclipse_proximity`, `search_long_horizon`, `kala_gochara_windows`, `kala_gochara_windows_v2`, `kala_gochara_authority`, `gochara_resonance_map`. If you find a caller the plan does not name, add it to your findings and to the reader inventory you produce in WP7 — do not silently omit it, and do not silently "fix" it either; a new undeclared consumer is an escalation, not a WP0 fix.

**Exit gate:** every finding re-verified or its drift recorded; no claim made about the historical "≥2-era case" beyond "misattributed diagnosis, unreconstructed."

### WP1 — Contracts (the foundation everything else reads)

Produce, as design documents plus their golden-case fixtures (not yet code):

1. **The convention vector**, exactly as specified in plan §4.1: `zodiac=sidereal`, `ayanamsha=lahiri_chitrapaksha`, `sidereal_method=swe_flg_sidereal` (D-1), `node_model=mean` with `node_source=swiss_mean_node_flg_sidereal` (N-4a(b″)), `epoch_convention=noon_ut_knot_abscissa`, `ephemeris_backend` recorded from `retflag` never from the requested flag, `time_scale=UT→TT via swe.deltat`, `house_system=whole_sign` for sign-level targets. Two rows with different convention ids are never compared. Write the schema for a `convention` reference table or embedded jsonb shape — your choice, documented.
2. **The target-resolution contract**, verbatim per plan §5.3's table (reproduced below) — write it as executable resolution logic with one golden-case fixture per row, including the negative cases:

   | target_type | resolution rule | object kind | unresolvable state |
   |---|---|---|---|
   | `karaka` | `graha_position[subject=graha].longitude_sidereal`; nodes → `RAH_MEAN`/`KET_MEAN` | point | `unavailable` if fact absent |
   | `dasha_lord_portfolio` | same as karaka | point | same |
   | `lord` (`1L`…`12L`) | whole-sign house-N sign from `LAGNA`; sign→lord by the fixed classical rulership table; lord→its `graha_position` row | point | `unqualified` if rulership row missing |
   | `bhava` (`1`…`12`) | whole-sign span from `LAGNA`; **never invent a point from a cusp** | interval (residence) | n/a |
   | `mechanism_node` | graha + rule + house → house sign span | interval | `unqualified` if the rule's operand is unwired |
   | `arudha` | sign span of the stored sign value (the stored `longitude_sidereal` is a cusp placeholder — **never treat it as a real degree**) | interval | n/a |
   | `yoga_constituent` | `ga_yoga_firings[fired=true].constituent_fact_ids` → each constituent's `graha_position` row; one `independence_group` per yoga | point(s) | `unavailable` if the yoga id has no live firing row |
   | `sensitive_degree` | resolve to the subject graha's own degree **only when the check result is positive** (papa/śubha kartari, pushkara); merge into that graha's `independence_group`. **A negative-result row (`not_gandanta`, `not_fired`, `not_pushkara`, `kartari=none`) is never a target** | point (qualifier) | such rows are removed at the resonance layer, not carried as `inapplicable` |

3. **The Contact ledger schema** (`kala_gochara_contacts`) and **Search-coverage manifest schema** (`kala_gochara_coverage`), field-for-field per plan §4.3–4.4 (reproduced above in this prompt's context — use the plan text verbatim, do not paraphrase the column list). `contact_id` = SHA-256 over `(chart_id, convention_id, body, target_kind, target_fact_id-or-ref, relation, aspect_deg, round(t_exact, 60s), method_version)`. A tolerance or method change always implies a new `convention_id`.
4. **The publication model** (`kala_gochara_publication`) per §4.7: `manifest_id`, `writer_asset_id`, `convention_id`, `input_generation_vector`, `ephemeris_backend`, `horizon`, `row_counts`, `content_digest`, `published_at`, `superseded_at`, `status ∈ {candidate, published, superseded, rolled_back}`. Generation label for this family's product going forward is **`'4.0'`**, never a `g4_*` prefix (it would fall through the serving code's existing branches — see §5 below, this is P-1's problem to fix, not yours to avoid by relabeling).
5. **Input generation vector** (§5.5): resonance build id + row count, `ga_yoga_firings` build id, `chart_facts` build ids for the categories the target contract reads, `ephemeris_daily substrate_version`, overlay build ids, `bg_transit_rules`/`bg_transit_av_gates` **content digests** (not counts — a count misses an in-place edit), convention id. A rebuild whose vector differs from a published one is always a new candidate, never an in-place refill.
6. **`comparable_with` vocabulary** — pin it now as a closed enum or it degenerates into free text later.
7. **The orb table and the kakṣyā lord order** each need a stated source in your design doc — a cited practice table with `uncited_extension=true` is fine; unstated silence is not.

**Exit gate before you move to WP2:** independently review your own WP1 output against the plan (a second pass, not the same pass that wrote it); every target type has a stated resolution or an honest unresolved state; `comparable_with` is pinned; the orb table and kakṣyā lord order each cite something. **Also confirm** `KALA_COST_PROFILE_v1_0.md` and `KALA_BASELINE_v1_0.md` are reachable from your checkout (they exist today only in a separate worktree, not on `main` — if they are not reachable from your branch, write an escalation naming exactly this, and proceed with WP4's cost measurement work using your own freshly-produced numbers instead of assuming those files' prior content).

### WP2 — Synthetic fixture suite (non-person data only)

Build every one of these as an independently-derived expected answer (never derived by running the legacy code and copying its output):

- Close-station cubic (three roots)
- True-node excursion under mean-node convention
- Seam tangency at a partition boundary (≥1 episode expected, not zero)
- Start-inside and end-inside episodes at the horizon edge (truncated, never dropped)
- Noon/midnight epoch conversion (the ~332″ trap this campaign already hit once)
- Per-graha special dṛṣṭi angles (Mars 90/180/210, Jupiter 120/180/240, Saturn 60/180/270, all others 180 only — **no dṛṣṭi from Rāhu/Ketu at all, per N-14**, they remain valid conjunction/ingress targets and agents)
- A negative-result sensitive-degree check (must produce **zero** targets, not a target marked negative)
- A cusp-placeholder arudha (must never produce a point contact)
- A dangling yoga id with no live firing row (must produce `unavailable`, not a silent skip)
- A missing overlay (Vedha/Moorti absent for the interval → `unavailable`, never `quality_gates=1.0` by default)
- A solver exception (must propagate as an explicit failure state, **never** as a `0.0` score that a `>=` threshold then certifies as "active")
- Plateau ties in peak detection
- A hand-specified, independently-computed factorized scorer oracle (this is what WP4's duplication test and WP2's own acceptance both compare against — it must not be derived from the system under test)

**Exit gate:** every case above has a written expected answer with its derivation shown, before any kernel code exists to compare it against.

### WP3a — The kernel (`services/gochara_kernel/`, new module, unimported until WP7 adopts it)

Build exactly per plan §4.2: monotone-arc index over a cubic spline on noon-UT knots, converted to sidereal *before* arc-building (this is the fix for the F-07 tropical/sidereal frame defect — do not build sidereal arcs by adjusting a tropical arc after the fact, build them sidereal from the start); explicit direction/wrap/station structure with **no station coalescing**; for each (body, target, relation) bracket every root from the arc index then refine by direct Swiss bisection at the instant; emit episodes with `t_in/t_exact/t_out`, declared orb, `branch`, dwell, `exact_crossing`, horizon truncation flags; residence spans for sign-level targets; declared `tolerance_arcsec` + `bracket_seconds` per relation class (a dṛṣṭi exact and a conjunction exact do not share one ε); `near_station_unresolved` must propagate `completeness_state='unqualified'` into the row, never stay a silent boolean. Moon: same kernel, on demand, not persisted by default, but its searched interval still produces a coverage record. Arcs are built once per (body × substrate_version), globally; contact solving is per chart.

**Ephemeris backend discipline (F-14):** never trust the requested Swiss flag. After every `swe.calc_ut` call in a test or gate, read the returned `retflag` and assert `retflag & 2` (SWIEPH) before treating a result as gate-grade; if `retflag & 4` (Moshier fallback), the comparison is `NOT_RUN`, never a pass. Record the three `.se1` checksums alongside every gate result that used them.

**Exit gate:** every WP2 fixture passes; the candidate root set is independently enumerated (not just "the kernel found N roots, trust it"); kernel-vs-direct-Swiss agreement within declared ε, gated on `retflag & 2`; the historical spike evidence (this campaign's own kernel feasibility spike, described in the plan's Appendix C) is re-run as a **committed, reproducible test** under the pinned `FLG_SIDEREAL` convention (the original spike used a different convention and is not gate evidence on its own); wrap-tangency, close-station-pair, and start/end-inside cases demonstrated on real arcs, not only synthetic cubics; an independently-enumerated Moon sweep.

### WP3b — Span-aware legacy algebra (runs in parallel with WP3a)

Reproduce the existing `services/gochara_v3` scoring algebra's *legacy event semantics* in a span-aware form — i.e., prove you understand exactly what the current system computes, factor by factor, before changing anything underneath it. This is the equivalence baseline WP4 diffs against.

**Exit gate:** factor-by-factor equivalence against the WP2 matrix; every artifact (deliberate behavior vs. accidental bug) classified as one or the other, with evidence.

### WP3c — Resonance corrections (`services/ka_gochara_resonance/writer.py`)

Implement, as pre-approved honesty fixes (N-12):
- **R-1:** filter `sensitive_degree` targets to positive check results only (drop the four negative predicates: `not_gandanta`, `mrityu_bhaga=not_fired`, `not_pushkara`, `kartari=none`); merge survivors into the subject graha's own `independence_group`.
- **R-2:** type `arudha` targets as sign-level (never a point from the stored cusp placeholder).
- **R-3:** re-validate `yoga_constituent` targets against live `ga_yoga_firings` at build time; pin the result in the input generation vector so a later drift (a yoga id that stops firing) is caught, not silently served stale.
- **R-4:** implement `lord` resolution per the WP1 contract.
- **R-5:** retain the *first* source root when a resonance rule has multiple, and preserve the `afflicted` qualifier instead of stripping it.
- **R-6:** add a `target_resolution_state` column (design the migration; do not apply it to a real database) so the honest null is stored, never inferred.

**Exit gate:** every WP2 negative-case fixture (negative sensitive check, cusp arudha, dangling yoga) now produces the documented honest state through this writer; the resonance layer's existing 27-event-class completeness gate still passes; `target_resolution_state` populated; rows with no citable source stay `unqualified`, not silently dropped and not silently promoted.

### WP4 — Decomposed comparison

Run, on one pre-declared synthetic workload (not a real chart): independent oracle → legacy event semantics (WP3b) → kernel geometry (WP3a) → scoring projection. Classify every delta you find against its source input, not as an unexplained residual. Measure timings with prepare/search/query phases separated, cold and warm. Price explicitly: global arc-build cost, per-chart contact-solve cost, ledger write and index cost at a measured (not assumed) row-count scale, and end-to-end wall time on your synthetic workload compared to this family's own historically-measured best completed run (**58.2 minutes**, not the unverified 20–25 hour anecdote — do not use the larger number as your baseline, the plan explicitly forbids it). **No cap, coarser grid, or narrower horizon may ever be presented as the source of a speedup** — if your numbers look better because you searched less, that is a defect in your measurement, not a result.

**Exit gate:** every delta classified with its input and reference; contact ids stable when you re-partition the horizon differently and re-run; label the whole output *producer prototype evidence*, explicitly not a production-build result and not a `DATA_ACCEPTED` claim.

### WP5 — Honesty fixes

Implement exactly these, each with a golden-value test proving the served-path behavior now matches its own documentation:

- **H-1a** (provenance only): read kakṣyā boundaries from the L1 fact table instead of the in-code equal-eighths fixture. State explicitly in your commit/design note that this does **not** reduce activity saturation — the L1 grid is the same equal-eighths division, just sourced from a fact table instead of a constant. Do not claim this fixes the saturation problem; it only fixes provenance.
- **H-1b is OUT OF SCOPE for this run** — it changes served λ values and is gated on N-13/M-7, which the ruling sheet ties to a further L1 data-model gap (G-10, no per-contributor bindu matrix exists yet). Design it, do not ship it; write the escalation.
- **H-2:** a solver or evaluation exception must never become a `0.0` score.
- **H-3:** no era window may be declared over a range where the underlying score is zero; report requested vs. completed horizon exactly, never silently truncate one into the other.
- **H-4:** replace eclipse-window-edge placeholder timestamps with real eclipse instants from the L0 substrate (timing only — do not change eclipse *weight*, that is a method call, out of scope).
- **H-5:** remove the fixed cap on stored peaks per era per decade; store every admitted peak; trim only at serve time.
- **H-6:** one physical contribution reached through multiple targets or rules counts once (`independence_group`), never multiplied.

**Exit gate:** golden-value tests per fix; served-path behavior matches its own documentation.

### WP6 — Ledger, coverage, publication (implementation, on your disposable database)

Implement the WP1 schemas for real, on a disposable database instance you provision and tear down yourself. Test: crash mid-write and resume cleanly; horizon extension without duplicate contacts; an upstream correction (a resonance target changes) propagating correctly; concurrent read during a write; full rollback of a candidate generation. **The writer must refuse a delete-then-insert against a `published` generation** — write the test that proves the refusal, not just the happy path. Measure storage size and serving-query latency with covering indexes actually in your migration file (design the migration; do not apply it to a shared database). A Clear operation against your disposable database must leave **zero** rows in all three owned relations (contacts, coverage, publication) — write and pass this test explicitly; it is the single blocking finding (F-24) the independent review caught in the prior version of this plan, and it must not regress.

**Exit gate:** all six lifecycle tests pass on your disposable database; storage and latency measured, not assumed; the publish-refusal test passes; the Clear-leaves-zero-rows test passes.

### WP7 — Receiving contracts (design only — these are owed to other owners, per §3 above)

You do not implement code inside `register_gochara_windows.ts`, `reading_checklist.ts`, the L5 ledger, `GocharaTransitService`, `kala_trigger`, Kṣetra, or Saṅgam's engine — those are outside `may_touch`. What you *do* produce here is the **design packet** each owner needs, precise enough that they can implement it without another round of discovery:

- **P-1 (serving provenance/coverage):** the exact branch logic needed so a `'4.0'`-or-later generation resolves provenance and coverage from the `kala_gochara_publication` manifest rather than a hardcoded string — write this as a design note with the exact function signatures and the exact failure mode it fixes (a hardcoded `'4.0'` string would silently break on the first rebuild to `'4.1'`).
- **P-2 (reading checklist):** what fields (`contact_id`, `completeness_state`) must survive the existing page-capping logic, and why dropping them breaks Q01/Q02.
- **P-3 (L5 ledger):** that a `contact_id` field is needed for frozen-claim identity, and where it plugs in.
- **P-4 (new read capability):** the shape of a contact-ledger + coverage read capability, density-layered per the codebase's own §N.6 discipline (confirmed rows never flattened together with catalog-only rows).
- **S-1 / S-2 (`GocharaTransitService`):** the service keeps its existing `find_aspects` return shape for its duck-typed callers (`kala_trigger`, `kala_admission/currents.py`) — do not change that shape — and gains a **new** `find_episodes` method that returns kernel episodes with grain, coverage, and `contact_id`, which Saṅgam and future callers opt into. Write this as an interface design, not an implementation inside a file you don't own.
- **T-1 (`kala_trigger`):** a one-paragraph note to its owner on whether its fan-out cost is reduced by adopting `find_episodes`, with your WP4 numbers as evidence, not a recommendation you implement yourself.
- **C-1 (cockpit Clear):** the exact `EXPLICIT_CLEAR_OPS['ka_gochara']` entry needed — three generation-scoped DELETEs in dependency order (coverage, then contacts, then windows), and the refusal condition when the target generation is the chart's authoritative one. Write the SQL as a design artifact for the cockpit owner to apply; do not touch the shared cockpit codebase yourself since it is outside `may_touch`.
- **V-1 (Saṅgam) / K-1 (Kṣetra):** one paragraph each stating the dependency edge they are missing today (Saṅgam reads `kala_vedha_gochara` undeclared; Kṣetra reads `kala_gochara_windows` undeclared and pins provenance edges by row id) and what declaring it requires of them.

**Exit gate:** a sentinel value placed in a low-ranked row's `independence_group` survives your own WP6 storage, a simulated retrieval/budget/delivery pass, and a simulated replay — proving identity survives the whole chain even though you don't own every link in it; each of the eight design packets above is complete enough that its owner needs no further discovery conversation to implement it.

## 5. Explicitly out of scope for this run — do not implement, only design and escalate

- **WP8 method parameters** (M-1's decay shape and orb values, M-2's dwell weight if any, M-3's channel algebra, M-4's mechanism admission list, M-6's per-class citation ruling, M-7's bindu-weight mapping) — the *direction* of each is already ruled (see the ruling sheet), but the **numeric choice** is evidence-gated to a native ruling by the plan's own D-3 discipline. Produce the comparison evidence (ablations, side-by-side projections) as WP8 asks, but do not pick a final number and ship it as settled. Write each comparison as a self-contained report ready for a ruling, and stop there.
- **WP9's Moorti method half** — the overlay *engineering* (coverage horizon, stamps) is in scope; a change to how Moorti's classical grade is *computed* is not.
- **WP10 in full** — no production build, no migration applied to a shared database, no registry edit on the live `asset_registry`, no lifecycle flip, no deployment, no authority flip, no release of the century hold, no re-materialization of any chart's Gochara data. This is gated on fresh explicit authorization per the plan's own frontmatter and the 2026-08-21 standing order; no instruction in this prompt can lift that, and none should be read as trying to.
- **Anything inside `must_not_touch`** (§3 above, verbatim from the plan's frontmatter).
- **Any new corpus admission decision** — if you need to know whether a text is in the admitted corpus, count it in `classical_text_chunks`; do not decide to add a citation source that isn't already there.

## 6. Absolute stop-and-escalate conditions

Write an `ESCALATIONS.md` entry and move on — never guess past these:

- An astronomical convention is unresolved and no fixture in WP2 covers it.
- An unknown input would otherwise be silently treated as empty.
- A physical topology (a wrap, a station, a horizon edge) is missed with no declared fallback.
- A divergence between two computations is unclassified — you don't know why they differ.
- An identity (`contact_id`, `window_id`) drifts when you re-partition an equivalent horizon.
- A comparison you're about to report as a "pass" is actually vacuous — zero permission, absent operands, or Moshier-compared-against-Moshier.
- A target would be resolved to a degree its cited fact does not actually carry.
- A cleanup path you're building would leave any owned relation orphaned.
- A consumer of a contract you're changing was not re-enumerated in this run (see WP0).
- You find yourself wanting to change the FROZEN orchestrator contract to make something easier.
- You find yourself about to write to, or design a path that could write to, a `must_not_touch` location.

## 7. Final report (produce this even if the run is interrupted partway)

Structure it exactly like the plan's own §12/§13 asks of a completed execution:

1. **State reached** — which work packets fully passed their exit gate, which are partial, which never started.
2. **Unreached states** — explicitly: WP8 parameters, WP9 Moorti method, WP10 in its entirety, and anything from §5.
3. **Residuals** — every `ESCALATIONS.md` entry, summarized, each with what evidence you gathered and what a human decision would need to consider.
4. **Confirmation** — that `v1`, `'3.0'`, `kala_views/`, the seed file, `transit_search.py`, and every sibling asset's code were untouched; that no production database was written to; that every test run against a database ran against a disposable instance you provisioned and can name/tear down.
5. **Artifacts** — every file created or modified, every migration file written (unapplied to any shared database), every design packet produced for another owner, with paths.

Do not claim `DATA_ACCEPTED` or `PRODUCER_READY` — those states require the production steps this run explicitly does not take. The honest ceiling for this run's own output is: contracts, fixtures, kernel, algebra, resonance corrections, honesty fixes, ledger, and design packets, all proven on synthetic data and a disposable database, ready for the native's WP8 rulings and, eventually, WP10's own authorization.

---

## Invocation

```bash
kimi -m kimi-code/k3 --auto -p "$(cat 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KIMI_AUTONOMOUS_EXECUTION_PROMPT_GOCHARA_v1_0.md)"
```

Run it from `/Users/Dev/madhav-l3/integration` (or a fresh worktree off the same `main` commit) so relative paths resolve. `--auto` removes Kimi's own tool-confirmation prompts for routine file writes and commands inside the session — it does not, and must not be read to, remove the boundaries in §5 and §6 above; those are enforced by this prompt's own instructions, not by Kimi's permission mode. If you want a paper trail of the run as it happens rather than only the final report, add `--output-format stream-json > gochara_run.jsonl` and tail that file.

Expect this to be a long run — WP0 through WP7 is the bulk of a serious engineering elevation. Let it run to its own completion or its own exhaustive escalation list; do not stop it partway and expect a coherent partial state beyond what §7 describes.
