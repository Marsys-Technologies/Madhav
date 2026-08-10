---
artifact: GOCHARA_UTKARSHA_CAMPAIGN_PLAN
version: 1.0
status: CURRENT — PLAN OF RECORD (native-ratified for autonomous execution, 2026-08-10)
date: 2026-08-10
campaign_codename: GOCHARA-UTKARṢA (utkarṣa = elevation, excellence)
supersedes: GOCHARA_V2_PARITY_CAMPAIGN_PLAN_v1_0.md (now SUPERSEDED — parity demoted from
  goal to safety-net; its Phase-0 governance/safety tasks are absorbed here as Wave 0)
parent_design: ../doctrine_waves/GOCHARA_SWEEP_2_0_DESIGN_v1_0.md (engineering substrate)
execution_mode: FULLY AUTONOMOUS MULTI-AGENT SWARM — no human gates. All questions and
  rulings are answered by the dedicated ADJUDICATOR agent (Opus). Nothing is DONE until
  the dedicated VERIFIER agent (Opus) issues PASS. Native kicks off the CONDUCTOR
  (Sonnet) via run_conductor.sh and walks away.
native_standing_authorizations: >
  Recorded from the 2026-08-10 ratification session. The native explicitly authorizes,
  in advance, for this campaign: (A1) autonomous commits, branch merges, pushes to
  GitHub, and production deploys via the existing main-branch CI/CD pipeline; (A2) the
  ADJUDICATOR agent as the native's delegate for ALL in-campaign questions and rulings,
  including the W6 cutover mechanism, asset naming, grammar-v3 mechanism admissions,
  divergence dispositions, and authorization of the migration-540 amendment; (A3)
  supersession of the D-4b "no new astrology" freeze by the governed GRAMMAR v3 change
  register defined in this plan; (A4) production builds/rebuilds of gochara-family
  assets for both canonical charts — EXCEPT ka_gochara_sweep itself, which is never
  rebuilt for either protected chart (see I1). NOT delegated (prohibited to every
  agent; enforcement is layered per I6 — restricted builder DB role + recurring
  wave-boundary rail verification + pre-campaign corpus snapshot, NOT merely the 540
  trigger, which this campaign itself amends): writing/deleting protected v1 sweep
  rows, disabling/altering protection triggers outside the one authorized W0.3
  migration, using the app.allow_protected_sweep_rewrite GUC, credential changes,
  deleting any table data outside §N.3 writer idempotency scopes.
changelog:
  - v1.0 (2026-08-10): First full plan. Six waves, ~34 lanes, agent roster
    (CONDUCTOR/ADJUDICATOR/VERIFIER/builders), autonomy rails, conductor prompt +
    re-trigger script as sibling files. Incorporates the critical-pass additions:
    three-legged replacement gate, ablation-driven grammar admission, self-normalizing
    thresholds, negative-control harness, cross-chart pooled fitting, λ decomposition
    facet, LEL mining lane. Same-session autonomous-execution review (10 findings, all
    fixed in place before first presentation): I6 rails made layered and real
    (restricted builder DB role, wave-boundary rail verification, corpus snapshot —
    the "code-enforced" claim was false under --dangerously-skip-permissions); runner
    hang guard (session timeout) + PAUSED end-state so livelocks terminate; global
    termination bounds (FAIL/redesign caps, BLOCKED vs PAUSED); Wave-4 gates corrected
    (W4.1 v3 leg + W4.3 need ALL Wave-2 merges; ablation compute path named; W4.5
    owns the post-fit rebuild W6.1 consumes); new W5.4 lane (writer repoint +
    mutation-guard evolution — W6.1 consumed a repoint no lane produced); W6.3
    rollback assertion made satisfiable (v1 row-set/value identity + additive-null
    envelope, not byte-identity); ka_gochara_sweep never-rebuild rule (I1/W0.2/A4);
    W2.9 citation inventory corrected (4 constants + ~23 inline + rules column);
    ledger pinned to branch utkarsha/campaign with anchored sentinels + worktree
    reattach fallback; W5.1 gains the LEL computeConfigurationSignature regression
    test; §1.2 merge-queue livelock fallback (documented repo history).
---

# GOCHARA-UTKARṢA — Autonomous Elevation Campaign: Implementation Plan of Record

**Goal:** Fully replace `ka_gochara_sweep` with an elevated gochara engine that is more
accurate, more complete, and deeper than the sweep — astrologically first (bounded
calibratable λ, every dormant classical sense wired, 27 event classes, measured against
lived reality), engineering second (arc-substrate exact timing, ≤15–20 min full-century
per chart) — with every current consumer switching seamlessly via the per-chart
`kala_gochara_authority` generation seam.

**Why the current engine must be replaced (verified live, 2026-08-10):** λ_e =
PROMISE × PERMISSION × exp(β·X) − suppression has degenerated into `exp(0.45·X)` alone:
X (designed for 3–6) reaches ~66 in production, raw intensities span 1e0–1.5e21,
PROMISE/PERMISSION (bounded [0,1]) are swamped, suppression has fired ZERO times across
all 35,620 corpus rows, adverse mechanism weights are clamped to zero by two `max(0,·)`
calls, point classes emit a "window" every ~9 days, `major_gain` produced 1 window in a
century, chain shape has produced 0 rows ever. Meanwhile AV gating hardcodes
`bindu_count_resolved: False`, tara bala never receives the natal Moon nakshatra, and
moorti/kota/latta/vedha-scale/annual-stack assets are built, cited, and read by nothing.

---

## §1 — Agent roster and execution mechanics

### Agents

| Agent | Model | Cardinality | Role |
|---|---|---|---|
| **CONDUCTOR** | Sonnet | 1 (the session the native launches) | Reads this plan + LEDGER.md, dispatches lanes respecting the dependency graph, maximizes parallelism, collects results, routes questions to ADJUDICATOR and verdicts to VERIFIER, performs merges/pushes/deploy-sync, updates LEDGER.md and commits it after EVERY state change (this is what makes the campaign resumable). Never writes product code itself. |
| **ADJUDICATOR** | **Opus** | 1 dedicated (persistent across the campaign; re-spawned with LEDGER context on restart) | The native's delegate. Answers every builder/conductor question on platform architecture and Jyotish domain; issues rulings (numbered `UTK-R#`, recorded in LEDGER.md §Rulings) for: W6 cutover mechanism, asset naming, grammar-v3 mechanism admission/rejection (from ablation evidence), divergence dispositions, threshold selections, migration authorizations, redesigns after repeated FAILs. Must ground platform answers in code it reads and domain answers in the classical corpus (`search_classical_texts` / `bg_rules`) — cited, or explicitly flagged as uncited judgment. |
| **VERIFIER** | **Opus** | 1 dedicated (persistent; re-spawned with LEDGER context on restart) | Sole authority for DONE. A lane without `VERIFIER: PASS` in LEDGER.md is not done regardless of what its builder claims. Protocol in §2. Adversarial by charter: its job is to refute the builder's claim, per §N.8 — every asserted signal needs a detector that could have said otherwise. |
| **Builders** | Opus for `[heavy]` lanes, Sonnet for `[mech]` (mechanical) lanes | many, parallel | One lane per builder, one isolated git worktree per builder (`git worktree add ../utk-<lane-id> -b gochara3/<lane-id>` from current main). Builder implements, tests locally, commits to its branch, reports. Builders NEVER merge, never push to main, never deploy. |
| **E2E-PROBE** | Opus | spawned at wave boundaries and in Wave 6 | Drives the deployed product end-to-end (MCP tools against production, Nirmāṇa cockpit via browser tooling, DB spot-checks) and reports evidence to VERIFIER. |

### Mechanics (binding on the CONDUCTOR)

1. **Campaign home** = this directory (`00_ARCHITECTURE/llm_consumption_audit/briefs/gochara_elevation/`).
   State lives in `LEDGER.md` (lane → {status: QUEUED|BUILDING|VERIFYING|PASS|FAIL(n)|
   BLOCKED|MERGED, branch, worktree, builder model, verdict evidence link, rulings}).
   **The ledger lives on the dedicated campaign branch `utkarsha/campaign`** (never on
   main, whose merge queue would gate heartbeats; never on a lane branch). The
   conductor pins to it at session start (`git checkout utkarsha/campaign && git pull`)
   and commits+pushes it after every transition — a restarted conductor reconstructs
   the entire campaign from `origin/utkarsha/campaign` + LEDGER.md alone.
   **Sentinel discipline:** campaign end states are exactly the anchored lines
   `CAMPAIGN-STATUS: COMPLETE` or `CAMPAIGN-STATUS: PAUSED(<reason>)` at the top of
   LEDGER.md; no agent ever writes either string in any other file or context
   (including quotes/examples), so the runner's grep cannot false-positive.
2. **Branch/merge/deploy flow:** builder branch → PR to `main` → CI gates + VERIFIER
   PASS recorded → merge via the repo's merge queue (the queue + CI on main IS the
   deploy path; the pipeline runs `migrate.ts` on deploy). **Merge-path fallback:**
   this repo has a documented history of branch-protection/merge-queue livelock
   (CLAUDE.md v7.0/v7.1 footers) — if a PR sits queued with green CI beyond a bounded
   wait (2 h) or the queue rejects repeatedly, the conductor escalates to ADJUDICATOR
   for a merge-path ruling (rebase-and-requeue, direct merge where permitted, or
   PAUSE) rather than retrying forever. After each wave's merges the CONDUCTOR
   verifies **prod-sync**: deployed revision == origin/main HEAD, migrations applied
   (query `_migrations_applied`), then records `WAVE n: DEPLOYED+SYNCED`, and runs the
   I6(b) rail verification.
3. **Commit cadence:** builders commit small and often in their worktree; the merge to
   main happens only at lane completion (VERIFIER PASS). Worktrees are removed after
   merge. Conflicts: later lane rebases; if semantic conflict → ADJUDICATOR.
4. **Question protocol:** any builder blocked >1 exchange on a decision sends the
   question + minimal context to ADJUDICATOR via the conductor; the ruling lands in
   LEDGER.md §Rulings and is binding campaign-wide. No builder ever waits on a human.
5. **Failure protocol — with a global termination bound (no livelock).** VERIFIER
   FAIL → lane reopens with the findings (same builder, same worktree). 3 FAILs →
   ADJUDICATOR redesign ruling. **Max 2 redesigns per lane**; a lane that fails after
   its second redesign is marked `BLOCKED(reason)` — the campaign CONTINUES without
   it if it is not on the Wave-6 critical path (ADJUDICATOR rules which downstream
   lanes re-scope), else the conductor seals `CAMPAIGN-STATUS: PAUSED(<lane>: <reason>)`
   and exits (the runner recognizes PAUSED and stops relaunching — this is the one
   designed stop that awaits the native). The same PAUSED discipline applies to any
   unresolvable oscillation (e.g. W6.2(c) optimize↔measure loops beyond 3 cycles, a
   wedged merge queue after the §1.2 fallback ruling fails). A crashed/silent builder
   is re-spawned fresh in the same worktree (committed progress survives; uncommitted
   work is expendable by design). Worktree-add fallback: if a crash left branch
   `gochara3/<id>` existing without a worktree, use
   `git worktree add ../utk-<id> gochara3/<id>` (no `-b`) — never loop on the -b error.
6. **Restartability:** the native runs `run_conductor.sh` (sibling file). If the
   process/API/connection dies, the script relaunches the conductor with the same
   prompt; the conductor resumes from LEDGER.md. Loop exits only on
   `CAMPAIGN: COMPLETE` in LEDGER.md.

### I-invariants (carried + extended; binding on every agent)

- **I1 (two-chart protection).** Charts `482012f1-710e-4a25-994a-93821f5871aa` (native)
  and `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (Abhinandan): their `generation='v1'`
  rows in `kala_gochara_windows` are the frozen benchmark. No agent writes/deletes
  them; the GUC `app.allow_protected_sweep_rewrite` is prohibited campaign-wide (no
  exception — Wave 6 writes `generation='3.0'` rows, which INSERT does not gate and
  the amended guard does not protect). DB triggers remain the hard rail.
  **`ka_gochara_sweep` is never rebuilt for either protected chart, by any agent,
  ever** — after W0.3 Phase A its delete-then-insert is trigger-blocked on those
  charts BY DESIGN; that error is expected, is not a defect, and must not be "fixed"
  or retried. The v1 corpus is frozen history, not a rebuildable asset.
- **I2 (grammar lineage).** v1 scoring modules (`services/gochara_intensity/*`,
  `services/gochara_grammar/*`) are NEVER edited in place — they are the benchmark
  engine. v3 is a parallel implementation (`services/gochara_v3/`) that imports v1
  primitives where unchanged and replaces what it elevates, under
  `GRAMMAR_VERSION = "v3_utkarsha"`. Every v3 mechanism carries `classical_citation`
  or `uncited_extension=true` (B.10); admission to the *weighted* engine requires an
  ADJUDICATOR ruling grounded in ablation evidence (§5, Wave 4).
- **I3 (earned signals, §N.8).** Every PASS, grade, coverage claim, SLO number, and
  calibration state must be produced by a detector that could have said otherwise.
  The VERIFIER's charter is enforcing exactly this.
- **I4 (honest gaps).** Anything not yet computed is a `skipped_reason`/flag/null,
  never a fabricated value or silent omission.
- **I5 (frozen orchestrator).** All writers are `@register` WriterBase subclasses on
  `ctx.db_conn`; no orchestrator changes anywhere in this campaign.
- **I6 (autonomy rails — layered, because a permission-skipping swarm has no CLI
  gate).** (a) **Restricted builder DB role:** the conductor provisions (first
  launch, via ADJUDICATOR-reviewed migration/grant) a `utkarsha_builder` Postgres
  role with NO DDL and NO ability to SET `app.allow_protected_sweep_rewrite`;
  builders and the E2E-PROBE connect ONLY as this role. DDL reaches production
  exclusively through migration files merged to main and applied by the deploy
  pipeline (which runs as the deploy role). (b) **Recurring rail verification:** at
  EVERY wave boundary the conductor re-reads and diff-checks the protection trigger
  function, the guard triggers, the unique index, and `build_protected_assets` rows
  against their expected definitions, and re-runs the protected-corpus
  checksum+rowcount; any drift → `CAMPAIGN-STATUS: PAUSED(rail-drift)` immediately.
  (c) **Pre-campaign snapshot:** first launch records in LEDGER.md a per-chart
  checksum + rowcount of both protected v1 corpora (ORDER BY natural key, md5 of
  canonical serialization) — the last-resort recovery evidence. (d) No agent:
  disables/edits protection triggers except via the one authorized W0.3 migration;
  runs destructive SQL outside §N.3 writer scopes or reviewed migrations (every
  migration lane gets a migration-guard agent review before PR); touches
  credentials; force-pushes; deploys with red CI. Deploys happen only through the
  main-branch pipeline.

---

## §2 — VERIFIER protocol (the definition of DONE)

For each lane the VERIFIER independently (in a clean checkout of the lane branch):

1. Runs the lane's stated test commands and the platform gates (`run-checks`
   equivalents: ESLint/TS/pytest suites relevant to touched dirs) — output quoted.
2. **Detector audit (§N.8):** for every new status/flag/claim, identify the code path
   that would make it read false; if none exists → FAIL.
3. **Fidelity audit (§N.7):** narration/serving reads fact_ids, no re-derivation, no
   wrapper constants shadowing L1 values, honest nulls.
4. **Scope audit:** diff touches only the lane's declared files/dirs; protected-table
   DML absent (grep for `kala_gochara_windows` DML outside the sanctioned writers);
   I2 lineage respected (no in-place v1 edits).
5. **Claim reproduction:** at least one headline claim of the lane (a count, a timing,
   a match rate) re-derived from scratch, not read from the builder's notes.
6. Verdict `PASS` / `FAIL(findings)` recorded in LEDGER.md with evidence. PASS is
   required for merge; the CONDUCTOR never merges on builder assertion.

---

## §3 — Wave plan

Dependency notation: `←` = hard dependency. Lanes within a wave with no `←` on each
other run **in parallel worktrees**. `[heavy]` = Opus builder; `[mech]` = Sonnet builder.

### WAVE 0 — Foundations, hygiene, rulings (all lanes parallel; W0.4 is the long pole)

**W0.1 [mech] Registry & seed hygiene.**
Context: live `asset_registry` = 127 rows, all active, verified complete vs code
(2026-08-10). But `platform/scripts/seed/asset_registry_seed.ts` is 17 rows behind and
running it against prod would blank `ka_kshetra.depends_on` (its own comment,
`asset_registry_seed.ts:2405-2432`). Work: regenerate the seed FROM the live table
(DB is truth); add seed rows for `ka_gochara_sweep`, `ka_gochara_resonance`,
`ka_gochara_v2_materialize`; restore ka_kshetra's 8 edges; extend
`platform/python-sidecar/tests/test_has_writer_completeness.py` into a three-way CI
diff (code `@register` ids ∪ migration INSERTs ∪ seed) that reds on any gap.
Acceptance: CI guard demonstrably fails when a seed row is deleted (VERIFIER performs
that mutation test), passes on real state.

**W0.2 [mech] Baseline builds + error triage.**
**Exclusion (I1):** the baseline set NEVER includes `ka_gochara_sweep` for either
protected chart — its rebuild is trigger-blocked by design after W0.3 Phase A, the
error is expected, and no retry/fix/ADJUDICATOR cycle is to be spent on it.
Context: `ka_gochara_v2_materialize` sits `state='error'` on the native chart
(2026-08-07); likely cause: `bg_gochara_arcs` is `scope='global'` L0 (planner blocks
per-chart builds when the global substrate is absent/stale in the environment —
`platform/src/lib/build/plan.ts:258`). Work: read the actual `asset_throughput.error`,
build `bg_gochara_arcs` if needed, rebuild the v2 asset for BOTH charts, populate the
four empty sibling tables by running their registered writers (`ka_vedha_gochara`,
`ka_moorti_nirnaya`, `ka_kota_chakra`, `ka_tithi_pravesha`) for both charts.
Acceptance: all six assets `lit` for both charts with nonzero (or honestly-zero-with-
reason) rows; error text quoted in LEDGER.

**W0.3 [heavy] The schema migration bundle** (absorbed parity-plan Task 0.2 + era_slice).
Context: `uq_kala_gochara_windows_natural_key` (migration 460) is generation-blind —
generation-3.0 rows with v1-equal natural keys would collide; migration 540's guard is
generation-blind. Work, one migration + one writer PR, two-phase deploy: (Phase A PR)
`services/ka_gochara_sweep/writer.py:691-716` switches its upsert to §N.3
delete-then-insert scoped natural-key + `generation='v1'` (no arbiter inference —
works under either index); (Phase B migration) drop/replace the unique index with the
generation-inclusive form (mirror migration 542's), amend
`build_protected_assets_guard_row()` to protect `protected_generations text[]`
(default `{v1}`), add nullable `era_slice_key TEXT` to both windows tables. Tests in
the existing TS DB-integration harness
(`platform/tests/integration/build_protected_assets_sweep_guard.db.test.ts`):
v1-DELETE raises, 2.0/3.0-DELETE passes, UPDATE raises, TRUNCATE raises, same-natural-
key cross-generation INSERT succeeds. Migration-guard agent review before PR (I6).
Acceptance: all five trigger tests + §N.4 applied-verification (SELECT trigger/index/
column defs quoted).

**W0.4 [heavy] Batched-context scoring engine (THE load-bearing lane).**
Context: scoring cost is ~0.5 s/candidate because `compute_lambda_e` does DB
round-trips per call (922 s for ±3y × 6 classes; naive century × 27 classes ≈ 19 h —
worse than the sweep). The entire ≤15–20 min/chart budget rests on this lane. Work:
new `services/gochara_v3/context.py` — one fetch per (chart × class): resonance
targets (enriched), full dasha timelines for all 12 PERMISSION systems, natal facts,
transit rules, AV bindus, sky-calendar slices → immutable in-memory `ClassContext`;
`services/gochara_v3/engine.py` evaluates λ for a vector of JDs against a
`ClassContext` with ZERO per-candidate DB access (asserted by a query-count test,
pattern: `test_w2g_arc_substrate.py::test_solver_query_count_is_constant_…`).
v1-parity mode: with v1 grammar semantics flagged on, batched engine must reproduce
v1 `compute_lambda_e` outputs bit-comparably on a 200-candidate golden sample from the
protected corpus (read-only) — proving the refactor changed cost, not answers.
Acceptance: query-count test; golden parity test; measured ≥50× per-candidate speedup
on the sample (evidence: timed run).

**W0.5 [mech] Campaign rulings (ADJUDICATOR, not a builder).**
Three rulings requested at campaign start so nothing downstream stalls:
`UTK-R1` W6 cutover mechanism (recommended: generation `'3.0'` rows into
`kala_gochara_windows` + per-chart authority flip; `_v2` table stays a workbench);
`UTK-R2` asset naming (recommended: retire the zero-row draft `ka_gochara` self-test
asset, rename `ka_gochara_v2_materialize` → `ka_gochara` as the production asset at
Wave-6 cutover, keeping id-migration surgical); `UTK-R3` grammar-v3 register format
(mechanism id, citation status, admission state: candidate|admitted|structural-only|
rejected, ablation evidence link).

### WAVE 1 — Engine core (E0) — `← W0.4`

**W1.1 [heavy] Bounded λ_v3 core.** `← W0.4`
Work: in `services/gochara_v3/engine.py`: X(t) becomes saturating noisy-OR over
configuration sentences (same mathematics PROMISE uses, `promise.py:42`); λ_v3 =
PROMISE × PERMISSION × activity × quality-gates ∈ [0,1] × modulators; β priors retire
(the exp() is gone); per-term contributions retained for decomposition (W1.5).
The nine v1 contact primitives (`gochara_grammar/primitives.py`) are imported
unchanged — the *aggregation* is what changes. Orb-strength curves now apply to the
currently-flat primitives (station, eclipse contribute graded, not 1.0).
Acceptance: λ ∈ [0,1] proven by property-based test over random contexts; PROMISE and
PERMISSION demonstrably move the output (sensitivity test: varying each term changes
λ — the exact property the v1 engine fails); no v1 module edited (I2).

**W1.2 [heavy] Direction restored.** `← W1.1`
Context: unfavourable mechanism weights (−1.0 in `gochara_resonance_map` via
`_MECHANISM_WEIGHTS`) are clamped to zero at `promise.py:64` and
`configuration_activity.py:133`. Work: v3 aggregation carries signed support/
affliction channels; a window's valence emerges from the sign of net configuration
evidence, class-level valence retained as prior, disagreement surfaced as a
`valence_tension` flag (honest, not averaged away).
Acceptance: a synthetic afflicted configuration produces an adverse window where v1
produces nothing; golden tests on known corpus configurations.

**W1.3 [heavy] Graded suppression that bites.** `← W1.1`, uses W0.2's populated tables
Work: vedha as multiplicative gate using `bg_vedha_malefic_scale` (5 cited Phaladeepika
grades) + `bg_phaladeepika_latta` (8 rows) + house-vedha rules + populated
`kala_vedha_gochara`; SBC stays `uncited_extension` (algorithmic approximation) until
a school-keyed grid is ingested (bg_sarvatobhadra_grid remains honestly empty).
Acceptance: suppression fires on constructed and real corpus configurations (the v1
count is ZERO across 35,620 rows — any real firing is already an elevation); each
suppression records which malefic set caused it (fact-grounded).

**W1.4 [heavy] Self-normalizing thresholds.** `← W1.1`
Work: activation threshold per (chart × class) = percentile of that chart's own
century λ distribution, reconciled against `brahma_event_ontology.base_rate_by_age`
(exists, currently unread for this purpose): choose the percentile whose implied
window density best matches the ontology's lived base rate; both the percentile and
the achieved density are stored on each window row (provenance, not magic).
Acceptance: implied densities within an ADJUDICATOR-ratified tolerance band of base
rates per class; no class emits the v1 pathology (window every ~9 days) or starves
(0 windows/century for a nonzero-base-rate class) without a flagged reason.

**W1.5 [mech] λ decomposition + uncertainty output model.** `← W1.1`
Work: every v3 window row carries `term_breakdown` JSONB (per-mechanism contribution,
signed) and a credible-interval pair (from prior uncertainty pre-calibration; from
fitted posteriors after Wave 4); serving schema addition is additive (new columns/
JSONB, no repurposing).
Acceptance: breakdown sums reconcile to λ within tolerance (asserted); intervals
present and honest (`structural_prior` labelled until W4.5).

### WAVE 2 — Dormant senses (all parallel, all `← W1.1`; each registers in the grammar-v3 register as `candidate`)

Every lane: implement as a togglable mechanism module in `services/gochara_v3/
mechanisms/<id>.py` with a uniform interface (context → per-JD modifier or sentence),
citation per B.10, unit tests, and registration in the ablation registry (consumed by
W4.3). None is hard-wired into the weighted engine until its `UTK-R` admission ruling.

**W2.1 [heavy] Ashtakavarga gating, real.**
Context: `primitives.py:786` hardcodes `bindu_count_resolved: False`; real bindus live
in `chart_facts` (`ashtakavarga_bindu_sign`), and the damp/neutral/amplify classifier
(vs 337/12 mean) already exists in `get_av_transit_gating.ts`. Work: fetch SAV/BAV
bindus into ClassContext; transit-through-sign modifier (damp/amplify); kakshya-lord
bindu quality on the already-detected kakshya crossings. Cited: Parashara AV chapters
via `bg_transit_av_gates` rules.

**W2.2 [mech] Moorti nirnaya modifier.**
Context: `bg_transit_moorti` (27 rows) + now-populated `kala_moorti_nirnaya` (W0.2);
migration 401 claimed a consumer that never existed. Work: per-ingress
svarṇa/rajata/tāmra/loha quality multiplier on windows overlapping that ingress span.

**W2.3 [mech] Tara bala, alive.**
Context: `nakshatra_ingress_tara` (`primitives.py:558`) is wired-but-dead — the call
site (`configuration_activity.py:67`) never passes `natal_moon_nakshatra_id`, and
nakshatra-level targets rarely resolve. Work: ClassContext carries natal Moon
nakshatra; enrichment resolves `target_nakshatra_id` for nakshatra-typed targets;
9-tara cycle grades nakshatra contacts.

**W2.4 [heavy] Sade Sati, fully.**
Context: only phase-membership boolean consumed; `ga_sade_sati` writes quarter
intensities + 8 cancellation rules to `chart_facts` (11k rows), unread. Work:
phase-quarter intensity as a graded PERMISSION/modifier signal; cancellation rules
evaluated and recorded (a cancelled Sade Sati window says so).

**W2.5 [mech] Kota Chakra overlay.**
Context: rings transcribed (`bg_kota_chakra_rings`, ADJUDICATION-9 tier-(iii));
`kala_kota_chakra` populated in W0.2. Work: malefic entry/exit through
Stambha/…/Bahya as adverse-class windows/modifiers for siege-class events
(illness_acute, chronic_onset + adverse classes lit in W3.1).

**W2.6 [mech] Real eclipses.**
Context: current `eclipse_degree` primitive is a node×luminary proximity proxy
(`uncited_extension=True`); `bg_sky_events` holds real computed solar/lunar eclipses
(31,059-row sky calendar). Work: eclipse sentences sourced from the sky calendar with
natal-point contact via arcs; proxy retired inside v3.

**W2.7 [heavy] Annual context stack.**
Context: `permission.py:60-68` documents Tājaka year-lords as a known gap; Tithi
Praveśa + Sudarśana varsha tables now populated (W0.2); `ga_tajaka` holds
`l1_tajik_varsha_year_lords` (240 rows), Muntha, Vārṣeśa. Work: three annual
PERMISSION generators (year-lord relevance, praveśa-chart tone, sudarśana house), each
a separate mechanism id for independent ablation.

**W2.8 [mech] Bhava targets get degrees.**
Context: `enrich_targets` resolves bhava targets to sign only → stations/eclipses/
returns silently skip every house target. Work: cusp degrees from L1 facts
(referenced by fact_id, §N.5) into enrichment; the three degree-hungry primitives
start seeing house targets.

**W2.9 [mech] Citation resolution table.**
Context: windows carry citation *strings* from three sources — **4 constants** in
`services/gochara_grammar/citations.py` (its full `__all__`), **~23 inline
`classical_citation` strings** in `services/gochara_grammar/primitives.py`, and
`bg_transit_rules.classical_citation` values; nothing resolves any of them to
`classical_text_chunks` verses. Work: resolution table over all three sources
seeded via the migration-528 verified-before-seeded pattern; serving joins it so a
window's sentences resolve to verse_refs through the existing hybrid search.

### WAVE 3 — Coverage, shapes, hierarchy, horizon — `← W1.*` (parallel except as noted)

**W3.1 [heavy] 27-class coverage.**
Context: swept scope = 6 of 27 (`event_class_scope.py:130`); 6 adverse classes named
dark; resonance writer is fully deterministic from `signature_model` + rules. Work:
extend `ka_gochara_resonance` derivation to all 27 classes for both charts,
LEL-represented classes first (they are calibratable); classes with weak
`signature_model` get honest thin maps + a per-class quality note, never invented
targets. Chunked as three parallel sub-lanes (domains split by ADJUDICATOR).

**W3.2 [heavy] Interval + chain shapes.** `← W1.4`
Work: intervals = root-solved λ-threshold crossings (enter/exit instants, peak =
analytic argmax between them — no daily runs, no chunk-continuity machinery, which
died with the grid); chains = milestone_template rows actually produced (marriage:
first-ever chain rows), each milestone scored on its own configuration. Horizon-edge
and slice-edge semantics per the two-level `era_slice_key` scoping (W0.3 column).

**W3.3 [heavy] Multi-resolution hierarchy.** `← W3.2`
Work: era-windows (Saturn/Jupiter/nodes) ⊃ month ⊃ day windows with `parent_window_id`;
muhurta scale stays lazy (Tier-C Moon, computed on demand, cached). Serving exposes
`resolution` facet.

**W3.4 [heavy] Century horizon + slice receipts.** `← W0.3, W3.2`
Work: `plan_substeps` = (class × decade era-slice); slice-scoped delta fingerprints
(class, grammar version, targets, bodies, arc fps, era_slice) so any upstream change
re-runs only affected slices; interval ownership via stored `era_slice_key`.
Acceptance: full-century build both charts into a workbench generation; measured
wall-clock recorded (this is the first end-to-end SLO evidence point); delta re-run
after a synthetic one-class change re-runs only that class's slices (proven).

### WAVE 4 — Calibration & mechanism admission — gates: W4.2/W4.6 `← W3.4`; **W4.1's
λ_v3 leg and W4.3 additionally `← ALL Wave-2 merges`** (ablations are per Wave-2
mechanism — impossible before the mechanisms exist). **Ablation compute path
(binding):** ablation and contender curves are produced by re-evaluating the batched
v3 engine (W0.4 ClassContexts) over the W3.4 candidate corpus's stored candidate JDs
with mechanism toggles — in-memory re-evaluation, NEVER re-materialization per
toggle combination.

**W4.1 [heavy] λ contenders in the bakeoff.**
Context: the CRPS harness exists (`scripts/audit/t0_retrodiction/`,
`lib/a3_scoring_harness/` — proper_scoring, DR-17 grading, sealed-split guard) with 13
contenders, and the composite λ has never been one. Work: `TemporalCurveModel` over
λ_v1 (the sweep corpus, read-only) AND λ_v3 (the W3.4 build), entering the existing
roster; both scoreable against LEL events under the sealed split.

**W4.2 [heavy] Negative-control harness.**
Work: identical scoring against date-shuffled event sets → noise floor with CIs;
any superiority claim in this campaign must clear the floor or say it doesn't (I3).

**W4.3 [heavy] Ablation runner → grammar admissions.**
Work: with-vs-without runs per Wave-2 mechanism (the registry from W0.5/UTK-R3);
results → ADJUDICATOR issues per-mechanism admission rulings: `admitted` (weighted in),
`structural-only` (present in output, flagged, unweighted), or `rejected`. Small-N
honesty: admission requires "does not degrade + classically cited" — NOT statistical
significance; `structural-only` is the default when evidence is flat.

**W4.4 [heavy] Weight fitting, cross-chart pooled.** `← W4.1–W4.3`
Work: SYSTEM_WEIGHTS / suppression / threshold-percentile fitting via the harness with
partial pooling across both charts (hierarchical: shared prior, per-chart offsets);
DR-14's "weights are LEARNED, never assumed" finally discharged. Fitted values land in
a versioned `gochara_v3_calibration` table with fit provenance (dataset hash, split id,
CI) — never hardcoded into modules (§N.7 item 3).

**W4.5 [heavy] `empirically_calibrated`, earnable.** `← W4.4`
Context: today a one-state enum — no code path can set it (unearned-signal case).
Work: the L5-owned path (mīmāṃsā side, respecting the D5 NO-SCORING gate: deterministic
L3 build, calibration state stamped by L5) that marks window rows/classes
`empirically_calibrated` when fitted weights with valid provenance produced them;
bridges the disconnected `lel_calibration.py` vocabulary (`structural|sparse|calibrated`)
to the windows enum. Prospective ledger auto-seeding: top forward windows →
`brahma_prospective_ledger` rows (its schema + DR-16 disclosure machinery already
exist, 7 rows live), closing the predict→outcome loop.
**Also owns the post-fit rebuild:** re-materialize the workbench century corpus for
both charts with ADMITTED mechanisms + FITTED weights (the artifact W6.1 promotes to
production). Without this step, W6.1 would consume a pre-admission candidate corpus
that nothing rebuilt after calibration.

**W4.6 [mech] LEL mining (non-blocking, parallel with all of Wave 4).**
Context: calibration power is data-bound (64 events). Agents cannot invent lived
events, but CAN mine what exists: `LIFE_EVENT_LOG_v1_2.md` + corpus artifacts (MSR,
session logs) for dated-but-unloaded events; stage candidates with source quotes into
a review file `LEL_CANDIDATES_STAGED.md` (native reviews post-campaign — the ONE
deliverable that waits for a human, because only the native can attest lived truth;
it does NOT block any lane). Also date-stamp Abhinandan events if documented.

### WAVE 5 — Serving & integration — `← W3.3, W4.5` (parallel)

**W5.1 [heavy] Serving elevation under the density contract.**
Work: the three gochara MCP tools + `reading_checklist` gain additive facets:
`resolution` (hierarchy level), `term_breakdown`, `calibration_state`,
moorti/suppression detail, verse-resolved citations (W2.9) — layered per §N.6
(calibrated > structural, hard floors on the dense layer, honest empty-reasons).
Generation filter untouched (it's the cutover seam). `SOURCE_CITATION` in
`register_gochara_windows.ts:247` becomes generation-conditional.
Acceptance additionally includes the **LEL signature regression test**: an asserted
test (beside `reading_checklist.fetch_gochara_sweep.test.ts`) that
`computeConfigurationSignature` (`prospective_ledger.ts:164-252`) behaves identically
over generation-'3.0' rows — a probe in W6.3 is not a substitute for this detector (I3).

**W5.2 [mech] Nirmāṇa/DAG integration.**
Work: registry migration — the elevated asset's `depends_on` gains the sibling input
edges (`ka_moorti_nirnaya`, `ka_vedha_gochara`, `ka_kota_chakra`, `ka_tithi_pravesha`,
`bg_sky_calendar`, existing arcs/resonance); `count_sql`/`target_table` point at the
serving table + `generation='3.0'` (§N.4 cockpit truth); sibling assets get correct
`count_sql`. Staleness now true by construction in the DAG.

**W5.3 [mech] Docs-of-record.**
Work: grammar-v3 register finalized (every mechanism: citation, admission state,
evidence link); `CURRENT_STATE_v1_0.md` §2 updated; this plan's LEDGER cross-linked.

**W5.4 [heavy] Writer repoint + mutation-guard evolution** `← UTK-R1, W0.3, W3.4`.
Context: W6.1 says "via the repointed writer" but the repoint is CODE, not
operations — and `writers/tests/test_ka_gochara_v2_mutation_guard.py:38`'s
`PROTECTED_TABLE_RE` currently fails on ANY `kala_gochara_windows` reference in the
writer source, so a naive repoint breaks CI by design. Work: switch the production
writer's target `kala_gochara_windows_v2 → kala_gochara_windows` per UTK-R1;
delete-then-insert at the two-level scope (outer `chart_id × event_class ×
generation='3.0'`, per-slice `era_slice_key`); evolve the mutation-guard test to
assert the NEW invariant — every DML statement carries the `generation='3.0'`
predicate — instead of the blanket table ban; registry `count_sql`/`target_table`
follow in W5.2. Acceptance: guard test fails when the generation predicate is
removed (mutation-tested, as the original guard was); dry-run build on a
non-protected fixture chart writes only '3.0' rows.

### WAVE 6 — Replacement — strictly sequential

**W6.1 Full-century production builds** `← all Wave 3/4/5 merges deployed, W5.4
specifically, and W4.5's post-fit rebuild verified`:
generation `'3.0'` rows into `kala_gochara_windows` per UTK-R1, both charts, via the
W5.4-repointed writer promoting the W4.5 post-fit corpus (v1 rows read-only beside
them; INSERT ungated; amended guard protects `{v1}`). Measured wall-clock per chart recorded (SLO evidence: target
≤15–20 min; if missed, ADJUDICATOR disposes: optimize-vs-accept with the measured
number, never a silent miss).

**W6.2 Three-legged replacement gate (VERIFIER runs it; ADJUDICATOR disposes):**
(a) **No-loss coverage:** equivalence protocol vs v1 corpus, closed classification
vocabulary, zero unclassified — every v1 window matched, superseded-more-precisely, or
classified artifact (`v1_grid_artifact` / `v1_moon_undersampling_miss` / new
ADJUDICATOR-ruled classes); (b) **Mechanism soundness:** §N.8 detector audit over
every admitted mechanism + the W1 property tests green; (c) **Directional empirical:**
λ_v3 ≥ best single-system contender on CRPS with CIs, and above the W4.2 noise floor —
"not worse, honestly measured", not "significant victory".

**W6.3 Authority flip, rehearsed:** flip `kala_gochara_authority` → `'3.0'` for
**Abhinandan**; E2E-PROBE drives all three MCP tools + reading_checklist + LEL ledger
against production, evidence to VERIFIER; **rollback rehearsal** with a precisely
defined assertion — after flipping back to v1, every serving surface returns the
IDENTICAL v1 row set and row values as the pre-campaign corpus (checksum vs the I6(c)
snapshot), with the W5.1 additive envelope fields present-but-null for generation-v1
rows (byte-identity of the full envelope is NOT the assertion — W5.1 changed the
envelope for all generations by design; an unattended VERIFIER must neither fail
forever on the impossible check nor silently weaken the real one); then flip forward;
soak (conductor
schedules a wake-up, re-probes); then flip the native chart with the same probe.

**W6.4 Retirement + rename:** `ka_gochara_sweep` retires in place (docstring +
`catalog_status='RETIRED'`, data kept, protection permanent — now also covering
generation `'3.0'` via `protected_generations` update for both charts); asset rename
per UTK-R2 executed surgically (registry migration + writer registration + cockpit);
post-cutover battery (design §3.5: full serving regression + DR-17 gate assertions)
runs GREEN or every divergence carries an ADJUDICATOR disposition.

**W6.5 Campaign close:** prod-sync verified (deployed == origin/main, migrations
applied); E2E-PROBE full product pass (cockpit shows the new asset lit with true
counts; a fresh judgment/kala query touching gochara serves v3 depth); LEDGER.md
sealed `CAMPAIGN: COMPLETE`; close report written to this directory;
`CURRENT_STATE_v1_0.md` updated. The conductor loop exits.

---

## §4 — Parallelization map (conductor's dispatch order)

```
WAVE 0:  W0.1 ∥ W0.2 ∥ W0.3 ∥ W0.4 ∥ W0.5(rulings)
WAVE 1:  W1.1 → (W1.2 ∥ W1.3 ∥ W1.4 ∥ W1.5)          [gate: W0.4 PASS]
WAVE 2:  W2.1 ∥ W2.2 ∥ … ∥ W2.9                       [gate: W1.1 PASS; 2.x need W0.2 data]
WAVE 3:  W3.1 ∥ W3.2 → W3.3; W3.4 after W3.2          [gate: Wave-1 PASS; W3.4 also W0.3]
WAVE 4:  W4.2 ∥ W4.6 [gate: W3.4] ; W4.1(v3 leg) ∥ W4.3 [gate: W3.4 + ALL Wave-2]
         → W4.4 → W4.5 (incl. post-fit rebuild)
WAVE 5:  W5.1 ∥ W5.2 ∥ W5.3 ∥ W5.4                    [gate: W3.3 + W4.5 PASS; W5.4 also UTK-R1 + W0.3]
WAVE 6:  W6.1 → W6.2 → W6.3 → W6.4 → W6.5             [strictly sequential; W6.1 needs W5.4 + W4.5]
Merges+deploy+prod-sync+I6(b) rail check at each wave boundary (and mid-wave for
independent lanes).
```

Peak concurrency ≈ 9 builder worktrees (Wave 2). Waves 2 and 3 can overlap partially
(W3.1 has no dependency on Wave 2) — conductor may dispatch W3.1 alongside Wave 2.

## §5 — Success criteria (campaign-level, all earned)

1. Both charts served from generation `'3.0'` via the authority seam; all previous
   consumers functioning (E2E-PROBE evidence).
2. λ bounded, decomposed, threshold-normalized; suppression demonstrably firing;
   direction demonstrably flowing; 27 classes; chains exist; hierarchy served.
3. Fitted weights with provenance; `empirically_calibrated` earnable and earned where
   data allows; prospective ledger auto-seeded; noise floor published.
4. Full-century per-chart build wall-clock recorded; ≤15–20 min or an ADJUDICATOR
   disposition of the measured number.
5. v1 corpus intact to the row (verified), protected forever; zero uses of the GUC in
   any transcript/log (VERIFIER greps at close).
6. Prod == main; migrations verified applied; Nirmāṇa cockpit truthful for the new
   asset family (§N.4).

## §6 — Sibling files

- `CONDUCTOR_PROMPT.md` — the prompt the native pastes/launches (used by the script).
- `run_conductor.sh` — the re-trigger loop (crash/API-drop resilient).
- `LEDGER.md` — created by the conductor on first run; the campaign's single state file.

*End GOCHARA_UTKARSHA_CAMPAIGN_PLAN_v1_0.md v1.0*
