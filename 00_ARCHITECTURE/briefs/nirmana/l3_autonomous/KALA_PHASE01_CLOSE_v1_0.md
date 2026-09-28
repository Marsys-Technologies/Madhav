---
artifact: KALA_PHASE01_CLOSE
canonical_id: KALA_PHASE01_CLOSE
version: "1.0"
status: CLOSED_PARTIAL
date: 2026-09-22
phase: "L3 Kāla pre-elevation setup — Phase 0 (freeze and measure) + Phase 1 (make the programme safe)"
authority: >
  KALA_PRE_ELEVATION_CRITICAL_REVIEW_v1_0.md §7 phases 0 and 1 only (PR #2712, not yet on main),
  as amended by KICKOFF_REDIRECT_001.md and KICKOFF_REDIRECT_002.md (PR #2713, not yet on main).
terminal_state: WAITING_FOR_STRATEGIC_BRIEF
does_not_authorize: >
  any Phase 2+ work. No generation substrate, no temporal-contract change, no qualification
  binding, no force-fit removal, no asset elevation. The five decisions are PREPARED, not taken.
production_writes: NONE
---

# Phase 0 / Phase 1 close — what was proved, what changed, what is open

## §1 — Terminal state

**Phase 0: CLOSED-PARTIAL.** Four of five items discharged; 0.3 (cost) is open and says so in its
own frontmatter.
**Phase 1: CLOSED.** All four items landed as separate PRs, each with a test that fails before and
passes after.
**Stop condition reached: `WAITING_FOR_STRATEGIC_BRIEF`** (Foundation Contract §9 item 9). No
Phase 2 work was begun. Activity did not self-authorize the next stage.

**Production was never written to.** No migration was applied, no registry row edited, no build
dispatched, no credential rotated. Every mutation in this campaign happened on disposable
Postgres instances, all five of which are torn down with proof (§7).

## §2 — Deliverables

| Deliverable | State | Where |
|---|---|---|
| `KALA_BASELINE_v1_0.md` + `fixtures/kala_baseline_v1_0.json` | COMPLETE — 17 frozen cases | branch `l3/kala-setup-phase01` |
| `KALA_COST_PROFILE_v1_0.md` | **PARTIAL** — §1/§2/§5 written; §3/§4/§6 absent | same |
| `KALA_IO_USE_MATRIX_v1_0.md` + 2 fixture files | COMPLETE — 178 edges, 32 nodes | same |
| `KALA_PHASE2_DECISIONS_v1_0.md` | COMPLETE — 5 decisions, AWAITING_NATIVE_RULING | same |
| `KALA_PHASE01_CLOSE_v1_0.md` | this document | same |
| Phase 1.1 — B1 closure | MERGED-PENDING — PR **#2715** | `l3/kala-p1-1-b1-clear-guard` |
| Phase 1.2/1.3 — grants + timeout | MERGED-PENDING — PR **#2717** | `l3/kala-p1-2-builder-grants-timeout` |
| Phase 1.4 — supervisor posture | MERGED-PENDING — PR **#2718** | `l3/kala-p1-4-supervisor-posture` |
| Phase 1.5 — cascade coordination | MERGED-PENDING — PR **#2719** | `l3/kala-p1-5-cascade-coordination` |

**Dependency worth stating:** the governing critical review (#2712) and the two redirects (#2713)
are themselves not yet on `main`. Everything here cites documents a reader cannot yet find there.

## §3 — Phase 0, item by item

### 0.1 Baseline — COMPLETE
17 cases frozen: Strategy §2's L3-Q01–Q13, Product §14's three first-proving-set cases, and one
constructed ordinary-period case (Product §9 requires ordinary charts and ordinary periods; every
fixture the campaign held was dramatic). Probed against **both** the production DB read-only and
the live deployed MCP surface — 11 distinct tools answered between 11:39Z and 11:44Z.

**Tally: distinction present 4 · absent 12 · could-not-verify 1.**

The single condition behind 12 of the 12 absences: **`asset_throughput` and the tables disagree.**
Five L3 assets record large writes while their target tables hold **zero** rows for the canonical
chart — `ka_kalasutra` 335,403 → `kala_activation` 0; `ka_sangam` 14,868 → `kala_convergence` 0;
likewise `ka_kala_darshana`, `ka_bhavishya_lekha`, `ka_vighnakara`. The rows live on a different
chart. This is the cascade's footprint (§3.5).

Four findings that change what elevation must fix first:
1. **The EXPLAIN view is broken and says so.** `kala_explain_get` returns, on both routes,
   `pact_status: "unknown (unrecognized status string — served verbatim, not fabricated)"` with
   `chain: []`, `evidence: []`, `fact_id_refs: []`. The layer's whole answer to "why do you say
   that?" is a self-describing failure. It correctly refuses to fabricate — and delivers nothing.
2. **Two served numbers have no live substrate.** `kala_story_get` serves
   `high_convergence_count` (8,838 summed over 100 chapter rows, computed 2026-08-13) while
   `kala_convergence` holds 0 rows for this chart.
3. **A message asserts a cause the evidence contradicts.** Every surface reports *"ka_kshetra has
   written no kala_field_snapshots row for this chart yet — the first field build has not run"*
   while `kala_field` holds **8,570,075** rows for it. The build ran, wrote 8.57M rows, then
   crashed before the snapshot header.
4. **Ayanamsha sensitivity is real on half the layer and structurally impossible on the other
   half.** Switching to `raman` moves the mahādaśā boundary by five years with correct per-variant
   `fact_id`s — but `kala_gochara_windows` has **no `ayanamsha_id` column**, so the transit half
   returned byte-identical output. No surface compares variants.

Also flagged: L3-Q08's `temporal_closure` block declares `exhaustive_within_stated_window: true`
on a zero-row five-year search whose sibling `empty_reason` says the asset may not be built —
read alone, exactly the universal denial that question forbids. And `kala_elect_get` at a 12 KB
budget **trims its own `trim_report`**, so the record of what was dropped is among the dropped.

**COULD NOT VERIFY:** L3-Q13's sentinel proof and L3-Q12's seeded-omission proof both require a
write. Nine of the thirteen strategy proofs are perturbation proofs; for eight of those nine the
proof is additionally moot because the thing to perturb does not exist.

Lane E's sixteen questions are **mapped, not adopted** (review C3/D1). All 16 map; none dropped;
four candidate strategy amendments surfaced, of which **Q-K14 (within-chart rarity) maps to
nothing** and is the strongest argument for a fourteenth Strategy §2 row on ordinariness.

### 0.2 P0 safety — COMPLETE, and framed correctly
**Both hazards REPAIRED-AND-PROVEN by executed tests, not by reading code.**

Per REDIRECT_001 correction 1, the framing matters and the kickoff's was wrong: **receipts already
existed.** FOUNDATION_SAFETY §4.1 (Kshetra `3f109869d`, 27 focused / 133 expanded, independent
ACCEPT) and §4.2 (Bhavishya `a3e518864`, 25 passed plus a disposable lock proof, independent
ACCEPT), with ledger rows 2026-09-15. Those proofs ran against a strict fake. What FOUNDATION_SAFETY
itself lists as not run is the **populated real-database rehearsal**. That is what this campaign
added. **P0 was not unproven before this session**; a real-DB rehearsal was added on top of an
accepted fake-based proof. Per REDIRECT_002 item 1, `main` carries every accepted L3 source commit
by content, so the rehearsal exercised the accepted writers.

- **Kshetra:** real `plan_substeps(ctx)` produced 346 substeps with `txid_current_if_assigned()`
  NULL before and after, an unchanged md5 digest across 17 watched tables, and succeeded inside
  `SET TRANSACTION READ ONLY`. Replacement is an *execution* substep (`writer.py:520` → `:2420`),
  not planning. 7/7 passed.
- **Bhavishya:** an empty candidate plan meeting a retained `outcome_recorded=true` row refuses
  with zero tuple modifications; a matched rebuild preserves both the outcome and the row `id`;
  savepoint crash restores byte-for-byte. 7/7 passed.
- **The detectors are real.** Planting a DELETE into a Kshetra lane planner made **5 of 7** tests
  fail. Monkeypatching Bhavishya back to the legacy ordering made **4 of 7** fail, headline:
  `AssertionError: OUTCOME LOSS: recorded observation(s) destroyed by the rebuild`.
- **The trigger-function trap was reproduced, then solved.** Table-scoped `pg_dump` gave 39 tables,
  14 triggers, **0 functions**; restoring produced 14 `function … does not exist` errors. 11
  functions carried across, loaded functions-first; firing proven four ways, not merely presence.

**One item STILL OPEN → carried forward:** `ka_bhavishya_lekha.run()` has **no `ctx.dry_run`
branch** — a dry-run invocation would write. Asserted by a test so it cannot drift silently. No
live caller passes `dry_run=True` within the scope searched, so it is not a P0 blocker.

### 0.3 Cost — **OPEN, NOT DISCHARGED**
The authoring session was interrupted and the campaign closed without resuming it. **§1
(benchmark contract adopted verbatim + full environment declaration), §2 (method) and §5
(`estimated_seconds`) are complete. §3 (the five profiles), §4 (per-asset table) and §6 were never
written.** The document's own frontmatter and an opening banner now say so; its status was changed
from `MEASURED` to `PARTIAL_INCOMPLETE`, because a document claiming `MEASURED` while its
measurements are absent is precisely the §N.8 defect this campaign exists to catch.

**No cost profile has been measured for any Kāla asset.** Strategy §5's five profiles all remain
unmeasured. The ~7.5 h `ka_kshetra` figure quoted throughout is **carried in from a prior lane**,
not measured here.

What §5 *does* establish, and it is worth more than the F28 claim it was sent to test:
`estimated_seconds` is **not fabricated** — it is a **stale cached snapshot of a live query**,
`ceil(median duration of state='complete' runs in build_run_assets)`. The 24.32-minute figure is
exactly right as arithmetic (22 active `ka_*` rows, 1,459 s) and exactly wrong as a claim.
`ka_kshetra`'s own row disagrees with itself by **365×**: `estimated_seconds` 237 s against
`writer_timeout_seconds` 86,400 s — and only the latter is read by a live detector
(`runner.py:741`). A re-baselining would reproduce the defect: `build_run_assets.disposition` is
**NULL for 676 of 708** `ka_*` complete rows, so no statistic over that table can currently
separate a real build from a no-op.

### 0.4 IO/use matrix — COMPLETE, as an overlay
Per REDIRECT_001 correction 3, this is the **F12 operator-role overlay** on the existing
CURRENT_STATE §4.1 edges, not a rival tracker (DP-SD-019 §6 forbids one). 178 edges, 32 nodes.
By kind: computational_prerequisite 99 · serving_hydration 22 · fk_preservation 20 ·
shared_definition 19 · semantic_use 15 · protected_evaluation 3. By F12 role: computation 91 ·
exclusion 21 · interpretation 16 · relevance_navigation 13 · applicability 12 · counterevidence 11
· evaluation 10 · uncertainty 4.

**The governing finding: there is exactly one real generation selector in all of L3.** 82 edges
select a mutable `public` table on `chart_id` alone — weaker than the `latest` F09 already rejects.
`build_id` appears as a read predicate nowhere else in the layer.

`depends_on`: 62 agreeing / 20 declared-not-observed / 27 observed-not-declared. All three of
Strategy §6.3's named discrepancies adjudicated at the code: Avadhi→Taranga **confirmed absent**
(the only trace is a docstring); Kalasutra→Darshana **confirmed absent**; Gochara→Sangam
**adjudicated differently** — the edge is real but is a **name collision** with a live
Swiss-Ephemeris *service*, so the registry imposes a build-order prerequisite the code does not
need while Sangam's real prerequisite (`ka_vedha_gochara`) stays undeclared.
**Why nothing caught these:** `dag_edge_guard.py:79-83` excludes `services/` from its scan roots
and `:157-159` requires an `@register` decorator — and every Kshetra stage keeps 100% of its SQL
in `services/`.

**The computational DAG is acyclic; no packet is blocked by a cycle.** One cycle exists in the
*preservation* graph only, which constrains nothing.

Seam survival, measured: Sangam→Kalasutra keeps **2 of 21** columns; Sangam→Darshana **5 of 21**
as columns. Recurrence is silently capped at 8. **A prior lane's claim was corrected:**
`ka_taranga`'s transit term is 0.0 on **56,130 of 92,412 rows (60.74%)**, not 100% — and the
correction makes it *worse*, because the 36,282 non-zero rows are **stale**, built 45 s after
`ka_sangam` from 14,868 convergence rows the cascade has since destroyed, with nothing in the row
recording it.

**Four upstream tables L3 reads have no `asset_registry` owner** — `bg_transit_moorti`,
`bg_combustion_orbs`, `bg_transit_av_gates`, `kala_field_weights` — so none can be rebuilt or
version-pinned by the orchestrator. The layer's one real generation selector is itself unowned,
maintained by a one-off script.

### 0.5 Decisions prepared — COMPLETE
`KALA_PHASE2_DECISIONS_v1_0.md`, `AWAITING_NATIVE_RULING`, five ruling blocks. See §4.

## §4 — The five decisions, prepared not taken

| # | Decision | Recommendation | Blocked until ruled | Reversible? |
|---|---|---|---|---|
| D1 | L3 generations | **Authorize physical implementation** per the frozen W0 §6 design | Strategy W1; Phase 2.1/2.3; the cascade fix | schema, costly |
| D2 | Typed confidence vs a scalar | **Confirm F04+F06+F12+Temporal-Testimony; reject the scalar** | Phase 2.4; every §6.4 packet's method-qualification field | typed→scalar cheap; scalar→typed a full rebuild |
| D3 | The protected classes | **Confirm all three** | Phase 1.1 = W0, which gates W1 and therefore everything | **NO — wrong answer is permanent loss** |
| D4 | `ka_tithi_pravesha` qualification | **Commission corpus ingestion; defer the asset** | that asset past `PRODUCER_READY` | yes |
| D5 | Baseline authority | **Adopt L3-Q01–Q13 + §14's three + one ordinary case** | Phase 0.1 | yes |

**Rule D3 first.** It is the only one with campaign-wide transitive block and the only one whose
wrong answer is permanent loss rather than rework.

Per REDIRECT_001 correction 2, **D1 was reframed**: the design is already frozen and independently
accepted at W0 (FOUNDATION_SAFETY §6, eight design points). What is open is *physical
implementation*, held on `L3-W1-UPSTREAM-GENERATIONS-01` pending the RI-01 precursor release. The
ask is to release a hold, not to re-decide a design.

Three pieces of evidence most shaped the sheet:
1. **The L2 guard is already armed, and the review did not know.** `l2_data_plane_mutation_guard`
   is installed and enabled on `bodha_msr_signals`; `assert_l2_msr_delete_safe` (migration
   1036:740-767) discovers every FK from `pg_constraint` and raises, exempting only two in-L2
   tables. Five `kala_*` tables hold CASCADE FKs there and none is exempt. So the real choice is
   not "generations or status quo" — it is **"L3 binds by generation, or the first governed L2
   rebuild hard-fails while Kāla data exists."**
2. **The B1 deletion path is not the one the review named** (see §5).
3. **Zero praveśa citations exist in the corpus.** `classical_text_chunks` (10,651 rows, 15 texts)
   returns **0** hits for `%praves%` in either language field. Tājika Nīlakaṇṭhī *is* ingested (290
   chunks) but `translation_status` is NULL on all of them and sampled content is untranslated
   Devanagari. So the writer's `not_in_corpus` is verified true, and D4's obvious option is
   unavailable — not because the text is absent but because the ingestion is page-scanned and
   untranslated. **This is the weakest recommendation on the sheet and says so.**

## §5 — Phase 1, item by item

### 1.1 — B1 closed (PR #2715)
The hazard is real and **an ordinary authenticated chart owner can reach it** — `allowedScopes =
['per_chart']` is owner-level, not admin. Full chain traced at the code in the PR.

**Two corrections to the governing review, both established at the code:**
- **`target_table` was never the deletion vector.** The route's resolution order makes `count_sql`
  win first; `target_table` is never reached. The review and the kickoff both named it. It is
  corrected anyway, because a *newly seeded* row would take the stale `count_sql` literal verbatim
  and derive a DELETE against the **protected century corpus**.
- **The blast radius is larger than stated.** `generation='v1'` is **38,287 rows across 3 charts**,
  including **2,667 on a chart no prior record listed**.

**The W0 hold was reconciled, not bypassed** (REDIRECT_002 item 2). Why it existed, established
mechanically: the seed's `ON CONFLICT` sets `target_table = EXCLUDED.target_table` while
`count_sql`/`depends_on` are pinned to `asset_registry.<col>` — so a DB-only fix **would** be
reverted by the next seed run. Released by fixing migration 1071 **and** the seed literal in one
commit, with a parity test that reads the writer's own constant rather than copying it.

The guard was scoped with evidence, not by blanket: v1 refused unconditionally for every chart
with no registry lookup (migration 540's old guard was registry-keyed and therefore fail-**open**);
TRUNCATE refused outright; **gen-3.0-pinned DML deliberately allowed**, because the century
materialiser legitimately deletes those rows and blocking it is the defect that caused migration
588 to remove the old guard. Migration 566's guard is untouched. **No guard was weakened.**

Proof: 3→118, 14→52, and a live-DB suite 12/12 where **6/12 fail when the guard is neutered**.
Full suite 12,433 passed / 0 failed.

### 1.2 / 1.3 — grants and timeout (PR #2717)
`data_plane_builder` holds **zero privileges** on all five candidate tables — the full 30-cell
matrix is `f` — because it holds **zero role memberships** and inherits nothing.

Three `bg_*` tables granted SELECT, verb map derived from actual source reads with file:line.
**`phala_rectification` held, and the hold is Strategy-backed** (§6.2: rectification inputs require
separately admitted immutable artifacts; a live read of a mutable L4 table cannot satisfy that).
The hold is **asserted in the migration's verification block**, not merely commented. Its measured
contribution today is **0 of 370 rows** passing the filter.

The undeclared read at `stage3_clocks.py:1012` is filed as a **FIELD_CONTRACT_REGISTER amendment**
(REDIRECT_002 item 3); the W0 register itself was not edited, since it is another campaign's
artifact.

Timeout: `idle_in_transaction_session_timeout = 1800s` (must clear the documented ~20-min pure-CPU
substep, which is an **idle gap, not a statement** — this distinction is the crux, and `amjis_app`'s
600 s does not clear it); `statement_timeout = 86400s` (floor is the largest sanctioned budget, the
`writer_timeout_seconds` a live detector already reads). Both failure modes argued explicitly: a
bound that kills a legitimate build is worse than no bound; a bound that never fires is not a bound.

**⚠️ 1074 will fail at deploy unless a DBA acts — by design.** `amjis_app` has neither SUPERUSER
nor CREATEROLE, so it cannot `ALTER ROLE data_plane_builder`. Rather than land green while doing
nothing, the migration fails with an actionable `E1074_PREFLIGHT_ROLE_ADMIN`. The two commands a
privileged role must run are in the migration header. **1073 is unaffected.**

### 1.4 — supervisor posture (PR #2718)
**The three-strikes idle halt could never fire**, because its progress detector counted any file
change as progress and a stuck session still writes logs and heartbeats. A §N.8 defect in
operational clothing. Fixed, with a stuck-cycle fixture on which the legacy detector scores
`progress=yes` three times and exits 1 while the new one scores `progress=NO`, halts, and still
resets on a genuine commit.

Permission scope and session persistence verified **executably**, with control tests: an in-range
migration path was created successfully while an out-of-range one was denied, proving the globs are
precise rather than a blanket directory deny.

**Finding: four of LANE_G §1.5's proposed rules can never fire** — `Write(...)` forms are not
matched by file permission checks; only `Edit(path)` is. The committed file uses `Edit(...)`.

**Honest gap: `.claude/settings.json` is branch-scoped.** `origin/main` has none, and campaign
worktrees branch from `origin/main` — so **this does not actually close until #2718 lands.**

### 1.5 — cascade coordination (PR #2719) — purely documentary, by design
The brief said coordinate, not design. Both Nirmāṇa rulings verified **CURRENT**; the tool adopted
**unmodified**; CURRENT_STATE §4.2 cited rather than re-derived. One addition §4.2 omits:
`phala_mitigation` and `phala_muhurta` are `ON DELETE SET NULL` children of `phala_anchors` — a
provenance-mutation surface invisible to any CASCADE closure *and* to the automated gate.

**The most important finding is what the cascade missed.** The five emptied tables fail honestly at
0 rows. But `kala_activation_predicates`, `kala_taranga` and `kala_jivana_parva` have **no FK to
MSR**, survived, and are **served live** — carrying **79** dangling references on the canonical
chart and **49,809** across all charts, at 0.16%: small enough never to surface, large enough to be
wrong. Independently re-measured; both figures confirmed exactly.

**The rule's biggest limit, stated plainly:** `dispatch_frozen_rebuild.py` — the L3 lane's own
dispatcher — has **no blast-radius gate at all**. And the rule cannot prevent the failure that
actually occurred: the 79 dangling rows came from a *successful* MSR rebuild, nothing out of order.
Restore has still never been exercised. **Only Phase 2's generation binding closes the class.**

## §6 — What is open, and why

| # | Open item | Why it is open |
|---|---|---|
| O-1 | **Phase 0.3 cost profiles unmeasured** | Authoring session interrupted; not resumed. All five Strategy §5 profiles remain unmeasured. |
| O-2 | Production application of migrations 1071–1074 **unverified** | Session was read-only; application happens at deploy. Post-deploy checks are written out. |
| O-3 | **1074 needs a DBA action** | `amjis_app` lacks CREATEROLE. Two commands documented; fails loudly rather than silently. |
| O-4 | `build_protected_assets.protected_generations` still unread | Asset-level withholding standing in for a generation-level claim (§N.8 shape). Closing it risks the path just secured. |
| O-5 | Re-registering `ka_gochara_sweep` partially reverses migration 588's instruction | Surfaced as a judgment call, **not self-authorised**. Needs native confirmation. |
| O-6 | A chart with gen-3.0 rows but no v1 rows is unprotected from a generation-blind DELETE | Needs a writer-side override; outside B1's scope. |
| O-7 | `ka_bhavishya_lekha.run()` has no `ctx.dry_run` branch | A dry-run would write. Asserted by a test so it cannot drift. No live caller passes it. |
| O-8 | `.claude/settings.json` does not take effect until #2718 lands on `main` | Campaign worktrees branch from `origin/main`. |
| O-9 | Three `kala_*` tables serve 49,809 dangling references | No FK caught them; only Phase 2 closes the class. |
| O-10 | Four upstream tables L3 reads have no `asset_registry` owner | Cannot be rebuilt or version-pinned by the orchestrator. |
| O-11 | `dispatch_frozen_rebuild.py` has no blast-radius gate | PR #2695 modifies that dispatcher — re-check against its merged state. |
| O-12 | #2712 and #2713 are not on `main` | Every citation in this document points at documents a reader cannot yet find there. |

### ⚷ Security observation — reported, not acted on
A production database password is visible in `ps` output on this machine, in the command line of an
unrelated `npx @modelcontextprotocol/server-postgres` process. The value was **not** recorded
anywhere and **nothing was rotated** — credential rotation is the native's decision. Reported here
so the decision is made deliberately rather than by default.

## §7 — Hygiene proof

Five disposable Postgres instances were created across this campaign. **All five are torn down**,
verified at close: ports 59500, 59510, 59520, 59530, 59540 all unbound; data directories
`/tmp/kx`, `/tmp/kp0`, `/tmp/kc0`, `/tmp/kb1`, `/tmp/kg2` all removed; no stray processes.
One (`/tmp/kc0`) **outlived its authoring session's interrupt** and was torn down afterwards by the
orchestrating session — recorded honestly in `KALA_COST_PROFILE_v1_0.md` §7 rather than smoothed
over.

`redact.py --scrub` run before every commit; 0 occurrences across all runs. No credential,
connection string or `DATABASE_URL` was echoed, logged or committed.
Pūrṇa-owned territory (`platform-mcp/src/tools/kala_views/`) was **never edited** — only read, to
trace edges. `.github/workflows/deploy.yml`, applied migrations (≤1070) and
`supabase/migrations/1035|1036` were never touched. `WATCHDOG_SECRET` was never touched.

## §8 — What Phase 2 needs from the native

1. **Rule D3 first** — the protected classes. It is the only decision whose wrong answer is
   permanent loss, and it transitively gates everything.
2. **Rule D1** — authorize physical L3 generation infrastructure per the frozen W0 §6 design, and
   state what releases the `L3-W1-UPSTREAM-GENERATIONS-01` hold. Note the hard dependency: **L3
   cannot bind until L2 publishes a generation, and L2 has never opened one.**
3. **Confirm or correct O-5** — the `ka_gochara_sweep` re-registration judgment call.
4. **Decide on the credential observation** in §6.
5. **Decide whether Phase 0.3 is resumed** before Phase 2, or whether the layer proceeds with cost
   unmeasured. Strategy §5 says runtime budgets "will be set after the first measured profile" —
   which has not happened.

**This session stops here, in `WAITING_FOR_STRATEGIC_BRIEF`. No Phase 2 work was begun.**
