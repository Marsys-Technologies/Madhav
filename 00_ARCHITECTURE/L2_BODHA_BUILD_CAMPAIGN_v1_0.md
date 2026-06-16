---
artifact: L2_BODHA_BUILD_CAMPAIGN_v1_0.md
canonical_id: L2_BODHA_BUILD_CAMPAIGN
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-12
authored_for: the L2 Bodha campaign (Cowork plans → Claude Code in Antigravity IDE executes)
supersedes: none (new — the governing master campaign for L2 Bodha)
implements: L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md (the campaign-open context)
read_in_combination_with:
  - 00_ARCHITECTURE/L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md (the opening context — read first)
  - 00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md (the FROZEN contract + §5 conformance checklist)
  - 00_ARCHITECTURE/L1_GANITA_CLOSURE_v1_0.md (L1 sealed state + §7 L2 onboarding contract)
  - 00_ARCHITECTURE/A10_MSR_SPEC_v1_0.md (LOCKED) … A11_CDLM / A12_CGM / A13_RM (LOCKED) + A14_UCN_RETIRED_TO_UCD (LOCKED)
  - 00_ARCHITECTURE/MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md (Trap 1 — authority inversion)
  - 00_ARCHITECTURE/MSR_UCN_CONTAMINATION_AUDIT_v1_0.md (Trap 2 — interpretation contamination)
native_decisions_locked_2026_06_12:
  - "Table naming = bodha_* (mirrors bg_*/ga_* asset-id-family convention); l25_* placeholders + spec references rename → bodha_*."
  - "LOCKED A10–A14 specs are canonical over the 8-row seed placeholders (native delegated; Claude recommended). Build the rich spec table architecture, renamed l25_→bodha_."
---

# L2 Bodha — Build Campaign v1.0

## §0.0 — Decisions log (NATIVE-RESOLVED 2026-06-12 — read before anything)

The pre-brief readiness audit (`L2_BODHA_PHASE0_GAP_REPORT_v1_1`) surfaced four decisions; all
are now resolved:

1. **Table naming = `bodha_*`** (§3.1) — LOCKED.
2. **LOCKED A10–A14 specs win over the 8-row seed** (§3.2) — LOCKED.
3. **§13.1 philosophy-extension amendments APPROVED** — `bodha_convergence` /
   `bodha_contradictions` / `bodha_cgm_paths` + `convergence_formula_v1` / `centrality_formula_v1`
   are added to the LOCKED A10–A14 specs, authored alongside their writer briefs (version-bump).
4. **`bo_samvada` = Option A (NOT a UCN writer)** (§3.3) — LOCKED.
5. **Phase-0 table reconciliation = REPOINT-NOT-DROP, prod-gated, table-by-table** — the audit
   found `bodha_signals` has a LIVE READER (`consult/route.ts:22`); a blind DROP would break the
   chat consult API. Repoint the reader to the spec table (or compat view) before retiring any
   legacy table. The `l25_*` tables are live (migration 137, 21 defs), not empty stubs. Full
   corrected disposition: `L2_BODHA_PHASE0_GAP_REPORT_v1_1 §2 P0.1`.
6. **Phase-5 E2E = build-time gate** — required before the Bodha build *runs*, not a blocking
   first action; brief-authoring proceeds now in parallel.
7. **`count_sql` basis = SUM-across-all-the-asset's-tables** (native, 2026-06-12). Multi-table
   assets (each writes several spec tables) report a cockpit headline = the chart-scoped row-count
   summed over ALL their tables, not just a primary table. Phase E writes each `count_sql` as a
   summed expression: e.g. `bo_sangati` = `(count cdlm_cells) + (count cdlm_domain_rollups) +
   (count cdlm_chart_summary) + (count cdlm_pattern_clusters) + (count bodha_convergence)`, all
   `WHERE chart_id = $1`. `target_floor` = the achieved SUM after first build (floors aspirational,
   not gates — `[[feedback-floors-are-aspirational-not-gates]]`).

**Standardization clarity (the native's point, preserved):** Phase-0 completes
standardization-sense **(A)** — asset-ids + `WriterBase`/FROZEN-orchestrator contract +
`chart_facts` fact-grammar (`bg_*`/`ga_*`/`bo_*`), which is never touched — and retires only
standardization-sense **(B)**, the legacy `bodha_signals` contaminated column-shape that the A10
spec replaces. (A) ≠ (B); the audit's v1.0 conflated them and is corrected.

---

## §0 — How to use this document

This is the **governing master campaign** for L2 Bodha, the synthesis layer. It mirrors the
proven L1 Gaṇita campaign shape. It does three jobs:

1. **Settles the open reconciliations** (handoff §8 + the two larger ones surfaced at open)
   so no brief rediscovers them mid-build.
2. **Decomposes the work** into Phase-0 prerequisites + per-asset execution briefs, with the
   batching order and the orchestrator §5 conformance checklist to embed verbatim.
3. **Binds every brief to the inherited standards + the two documented traps**, so Bodha is
   built right the first time rather than audited-and-fixed like the old hand-authored MSR.
4. **Carries the native-locked design philosophy (§13)** — what Bodha is *for*, the
   acharya-grade bar, and where the philosophy *extends* the LOCKED A10–A14 specs (§13.1,
   sign-off-gated). Read §13 before writing any per-asset brief; it is the intent every brief
   serves.

**Cowork plans; Antigravity executes.** Per `[[feedback-cowork-vs-antigravity-split]]`, every
deliverable below becomes either a committed `.md` brief or a pasteable Claude-Code prompt —
never chat bullets the native must translate by hand. Implementation goes to Claude Code in
the Google Antigravity IDE on a dedicated branch.

**Verify state from CURRENT_STATE + git, not frozen docs.** `[[feedback-verify-state-not-claude-md]]`.
At open: main HEAD `00000587` (L1 closure + non-native chart build fix #266); CURRENT_STATE v5.74.

---

## §1 — What Bodha is (one paragraph) + the prime directive

L2 Bodha (*bodha* = understanding/cognition) computes the **structural relationships and
signals** over the L1 Gaṇita chart facts: which classical yogas/doshas/patterns FIRE
(MSR), how domains LINK (CDLM), the graph of grahas/houses/configs (CGM), the strongest
signals for REMEDY candidacy (RM), and the chart's overall digest (UCD). It is **still
deterministic fact** — predicate firings, graph edges, computed salience — **NOT
interpretation/narrative.** Interpretation happens at serve-time, never in the asset. This
is the single most important inherited rule. The prime directive (from every A10–A14 spec):
**only computed facts; structural predicate firings; no narrative; two-pass verification
mandatory per row; no threshold drop (strength is a column, not a gate).**

---

## §2 — Native subject (invariant)

Native = Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar. Canonical chart_id =
**`482012f1-710e-4a25-994a-93821f5871aa`**. `362f9f17-…` is a **DEAD phantom** — it litters
the A10–A14 spec citation examples as `chart=362f9f17`; those are PLACEHOLDERS. Never write it.
FORENSIC is the L1 authority surface (e.g. Muntha = Libra / 7H / Venus — Trap 1's proof case).

---

## §3 — Reconciliations SETTLED at campaign open (do not relitigate mid-build)

### §3.1 — Table naming → `bodha_*` (NATIVE-LOCKED 2026-06-12)

The A10–A14 specs and the only existing (empty) DDL (migration 206) use the `l25_*` prefix;
the asset_registry seed rows use `bodha_*`. **Decision: `bodha_*` wins**, mirroring the L0/L1
"asset-id family = table prefix" convention (`bg_*`→bg tables, `ga_*`→ga tables, so `bo_*`→
`bodha_*` tables). Action: the Phase-0 migration **renames the 6 empty `l25_*` placeholders
→ `bodha_*`** and the writer briefs reference `bodha_*` throughout; the A10–A14 spec `l25_`
table names are read as `bodha_` (a spec-amendment note records the rename — the schemas are
otherwise authoritative). This is the ganita_dashas-vs-chart_dashas reconciliation done
*before* writing, as the handoff §8.1 demands.

### §3.2 — LOCKED specs win over the 8-row seed (NATIVE-DELEGATED → Claude-RECOMMENDED 2026-06-12)

The A10–A14 specs (native sign-off 2026-05-29, LOCKED) define a **rich multi-table
architecture**; the asset_registry seed has only 8 coarse `bo_` rows each pointing at one flat
`bodha_*` table. **Decision: the LOCKED specs are canonical.** Rationale: the specs carry the
native's sign-off, the full ~50-column schemas, the versioned deterministic formulas
(`salience_formula_v1`, `resonance_score_v1`), and the two-pass methodology — they *are* the
design. The 8 seed rows are coarse placeholders. Critically, the spec architecture is exactly
what *fixes* both documented traps; collapsing to 8 flat tables would discard locked
granularity (CGM motifs, CDLM pattern_clusters, RM prescription chains, the MVs) and require
amending five LOCKED native-signed specs *downward* — the wrong direction.

**The asset-id grain stays at 8 `bo_` assets** (matching the orchestrator DAG + the cockpit
tiles). Each `bo_` asset's writer populates its **real spec tables** — exactly as L1's one
`ga_dashas` asset writes many rows across 36 sub-steps. Spec → asset → tables map:

| `bo_` asset | spec | bodha_* tables the writer populates (renamed from l25_) |
|---|---|---|
| `bo_laksana` | A10 MSR | `bodha_msr_signals` (~50 cols) + 3 MVs (`mv_msr_top_signals_per_chart`, `mv_msr_recurring_patterns_per_chart`, `mv_msr_domain_summary`) |
| `bo_sangati` | A11 CDLM | `bodha_cdlm_cells`, `bodha_cdlm_domain_rollups`, `bodha_cdlm_chart_summary`, `bodha_cdlm_pattern_clusters` (+1 per A11 §2) + 5 MVs |
| `bo_bimba` | A12 CGM (nodes) | `bodha_cgm_nodes` (graph-index flat cols) |
| `bo_karanajala` | A12 CGM (edges + struct) | `bodha_cgm_edges`, `bodha_cgm_sub_graphs`, `bodha_cgm_motifs`, `bodha_cgm_chart_summary` |
| `bo_upaya` | A13 RM | `bodha_rm_resonances`, `bodha_rm_remedy_prescriptions`, + the remaining A13 §4 tables (6 total) |
| `bo_samskara` | embeddings | `bodha_signal_embeddings` (pgvector, 1:1 with MSR signals) |
| `bo_samvada` | A14 UCD | **OPEN — see §3.3.** Likely NOT a writer. |
| `bo_pramana_mapa` | scorecard | `synthesis_quality_scorecard` (global) |

> Note on the `bo_bimba`/`bo_karanajala` split: the seed names `bo_bimba` = "graph nodes" and
> `bo_karanajala` = "graph edges." A12 is one CGM build (nodes + edges + sub_graphs + motifs
> computed together via igraph). Keep the two asset-ids for cockpit/DAG legibility, but the
> CGM compute is one igraph pass — decide at brief time whether `bo_bimba` (nodes) and
> `bo_karanajala` (edges + derived structures) are two writers sharing a compute, or one
> heavy writer with two registry faces. Recommend: one heavy `bo_karanajala` writer that
> emits nodes + edges + sub_graphs + motifs; `bo_bimba` is a thin nodes-only registry face
> reading the same compute. Confirm against the orchestrator DAG executor at brief time.

### §3.3 — A14/UCN is RETIRED → UCD is a read-side join (the `bo_samvada` open item)

A14 (`A14_UCN_RETIRED_TO_UCD`, LOCKED) **retires UCN as a separate per-chart writer asset.**
UCD (Unified Chart Digest) is a **read-side conceptual surface** — a join of the A8/A11/A12/A13
chart_summary rows, optionally materialized as `vw_chart_digest`, exposed by a single
`query_ucd(...)` tool. The 5 "truly-new" UCD fields fold into existing summary tables (A11
chart_summary, A12 topology_summary, A8 chart_summary) as ~5–6 added columns — **zero new
writer pipeline.**

But the seed carries `bo_samvada` ("UCN resonance" → `bodha_resonance`) as a per-chart writer.
**RESOLVED (native, 2026-06-12) → Option A:** `bo_samvada` is **NOT a UCN writer.** UCD is a
read-side join (`vw_chart_digest` + a `query_ucd` tool), and/or `bo_samvada` becomes the *thin
writer for the 5 folded UCD columns* on the existing summary tables. It is **not** built as the
retired UCN narrative. (Option B — re-scoping UCD to a real per-chart resonance table, requiring
an A14 spec amendment — was declined.) The `bo_samvada` brief is authored to Option A.

### §3.4 — G52 `signal_type_registry` is a NEW GLOBAL prerequisite (handoff §8.3)

A10 §5 + §12 require `signal_type_registry` (~500–700 data-driven predicate definitions across
all 6 traditions + synthetic predicates) **seeded before `bo_laksana` runs** — predicate
evaluation is data-driven, not hardcoded. It does not exist anywhere yet (confirmed at open).
**Phase-0 builds it as an L0/global asset** (`bg_*` or a global registry table per the L0
naming) with its own writer + seed, registered in `asset_registry`, and made a `depends_on`
of `bo_laksana`. This is the largest Phase-0 sub-task and gates the entire layer.

### §3.5 — The `l25_*` placeholder DDL is a STUB, not the spec (handoff §8.4)

Migration 206 created 6 `l25_*` tables "empty — L2 Bodha writes them," but the placeholder DDL
is a coarse stub (`l25_msr_signals` = 12 columns) versus the A10 spec (~50 columns). **The
Phase-0 corrective migration must build the FULL spec schemas** (renamed to `bodha_*`), not
preserve the stubs. The 6 stubs are dropped/replaced; the ~17 real `bodha_*` tables are
created to spec. Per `[[feedback-rebuild-skepticism-of-existing-code]]`, the stub is reference
for intent, not authoritative implementation.

---

## §4 — The 8-asset DAG + build order (already wired, migration 224 — verify, don't re-author)

All `scope: per_chart` except `bo_pramana_mapa` (global). `depends_on` already in the registry:

```
bo_laksana (MSR, A10)            depends_on: [bg_rules]            ← ROOT; everything fans from it
 ├─ bo_bimba (CGM nodes, A12)    depends_on: [bo_laksana]
 ├─ bo_karanajala (CGM edges,A12)depends_on: [bo_laksana]
 ├─ bo_sangati (CDLM, A11)       depends_on: [bo_laksana]
 ├─ bo_samvada (UCD, A14)        depends_on: [bo_laksana]          ← see §3.3 open item
 └─ bo_samskara (embeddings)     depends_on: [bo_laksana]
bo_upaya (RM, A13)               depends_on: [bo_laksana, bo_sangati]
bo_pramana_mapa (scorecard)      depends_on: []  (global)
```

**Build order:** `bo_laksana` FIRST (root). Then the fan-out
`bo_bimba ∥ bo_karanajala ∥ bo_sangati ∥ bo_samvada ∥ bo_samskara` in parallel on MSR. Then
`bo_upaya` (needs MSR + CDLM). `bo_pramana_mapa` global scorecard. The orchestrator DAG
executor runs this automatically from `depends_on`. **Verify the edges match what each writer
actually reads** (the L1 Phase-4 lesson: the declared DAG must match real read dependencies).
One correction to confirm: `bo_laksana.depends_on` should also pull `ga_structural` (its
primary feed) + `signal_type_registry` (G52) — `[bg_rules]` alone is insufficient. The DAG
executor resolves transitively, but `signal_type_registry` is a global that must be an explicit
edge.

---

## §5 — What Bodha CONSUMES from L1 (the verified data interface)

Bodha reads L1's `chart_facts` (+ `chart_dashas`, `chart_divisionals`) via SQL on
`ctx.db_conn`. Confirmed present + FORENSIC-verified for the native (L1 closure):
- **`ga_structural` (6,075 rows)** — the primary MSR feed: `yoga_fires`, `dosha_fires`,
  `aspect_*`, `graha_dispositor_chain`, `argala_natal_matrix`, avasthas, composite strengths.
  Every fired structural fact → an MSR signal. Confirmed populated categories in
  `L1_GANITA_CLOSURE §7.3` (aspects, yoga firings, dispositors, functional class, karakatva,
  argala).
- `ga_strength` (shadbala/ashtakavarga) → salience components (`shadbala_norm`, AV multiplier).
- `ga_sensitive` (karakas, sahams, KP, Tajik, esoteric) → tradition-specific signals.
- `ga_dashas` (7 systems) → `dasha_activation_proximity_score` (A10 Q4 = all 7).
- `ga_sade_sati`, `ga_panchanga`, `ga_vargas`, `ga_positions` → their signal classes.
- **MSR `constituent_facts_array` references fact_ids back to `chart_facts`** — these MUST
  resolve. L1 emitted clean fact_ids precisely so Bodha can back-reference. **This is the
  L1→L2 contract and the spine of Trap-1 avoidance** (§6.1).

---

## §6 — The standards Bodha INHERITS + the two TRAPS it must avoid

### §6.A — Inherited non-negotiables (same as L0/L1)

1. **Deterministic-first.** Python over LLM. Embeddings (`bo_samskara`) are a deterministic
   transform and are fine; generative LLM for curation is NOT. `[[feedback-deterministic-first-for-data-build]]`
2. **Only facts, no narrative.** No `interpretation`/`meaning`/`narrative` columns. The
   no-narration linter applies. Structured predicate firings + computed salience only.
3. **Atomic grain.** One row per signal firing (MSR), per cell (CDLM), per edge (CGM), per
   prescription (RM). JSONB only for genuinely irreducible structured composites
   (`configuration_jsonb` is the sanctioned A10 case — structured predicate detail). Each
   JSONB use justified.
4. **Two-pass verification MANDATORY per row** (A10 §6 prime directive). `divergent_flagged`
   → HALT the build.
5. **Idempotency = the L1 pattern.** Per-chart scoped delete-then-insert on the natural key,
   via a shared helper mirroring `ga_writers/_idempotency.py`. Rebuild REPLACES, never
   accretes. NOT the L0 ON-CONFLICT style. `[[feedback-idempotency-pattern-per-layer]]`
6. **No JH-parity oracle.** Verification = internal-consistency + classical-rule
   re-derivation + FORENSIC grounding. `[[feedback-no-jh-parity-anywhere]]` `[[project-pyjhora-is-the-engine]]`
7. **No audience tier.** No code branches on client/acharya/super_admin. `[[feedback-no-audience-tier]]`
8. **Floors aspirational, not gates.** A10 says ~4,000–6,250 signals/chart — chase genuine
   deterministic firings; set `target_floor = achieved count` AFTER build; never fabricate to
   hit a number; never halt for being under floor. `[[feedback-floors-are-aspirational-not-gates]]`
9. **Cockpit truth.** Each `bo_` asset needs a correct chart-scoped `count_sql` on
   `asset_registry` (the stats route reads `count_sql` from `asset_registry`, NOT
   `asset_throughput` — the L1 trap), pointing at the real `bodha_*` table the writer writes,
   and `target_floor` set = achieved count so the bar fills.
10. **PyJHora engine, Postgres-direct, surgical migrations.** Never deploy.yml-auto migrate
    (silent no-op `[[feedback-deploy-migrations-silent-noop]]`) and never bulk `migrate.ts`
    blind (`[[feedback-migrate-runner-untracked-legacy]]`). Apply one migration at a time via
    the Cloud SQL proxy; verify file-vs-live schema first; record the tracker row.

### §6.B — TRAP 1: Computed-value drift / authority inversion (`MSR_COMPUTED_VALUE_DRIFT_HANDOFF`)

The worst documented failure: an MSR signal carried a stale/wrong computed value that
CONTRADICTED the canonical L1 fact (SIG.MSR.377 asserted Muntha = Gemini/3H and Virgo/6H
across five inconsistent fields; FORENSIC = Libra/7H/Venus). Root cause: **retrievability was
treated as authority** — there was no rule that L1 facts WIN over L2.5 derivations on conflict,
so the most-retrievable corrupt signal out-ranked the truth.

**Bodha rule (bind in every brief):** **L1 is the authority.** A Bodha signal/cell/edge
**NEVER restates an L1 computed value as its own truth — it REFERENCES the `fact_id`
(`constituent_facts_array`) and inherits L1's value.** If a writer's derivation disagrees with
the L1 fact it cites, that is a **halt-worthy bug** (`divergent_flagged` → HALT), **not a
stored divergence.** The GA-Tajaka build already proved this works (Muntha = Libra/7H/Venus
FORENSIC-exact); Bodha preserves it, does not re-derive over it. Two-pass verification's
cross-layer-consistency check (handoff audit §4 check 1) is the enforcing mechanism.

### §6.C — TRAP 2: Interpretation-contamination of the deterministic base (`MSR_UCN_CONTAMINATION_AUDIT`)

The prior hand-authored MSR let authoring JUDGMENT leak into a base that should be purely
computed: hand-assigned `strength_score`/`confidence` (C1 — opinions in a data-shaped wrapper);
a **silent drop** of weak configurations with no candidate-pool trace (C2 — the most
consequential, 87% of signals scored ≥0.70 because weak ones were never written down);
deliberation committed into "fact" fields (C3); interpretive claims in `signal_name`/
`supporting_rules`/`domains_affected` (C4).

**Bodha rules (bind in every brief):**
- **Salience is formula-driven + reproducible** (`salience_formula_v1`, the versioned
  deterministic function in A10 §4; `resonance_score_v1` in A13 §3). **No human/LLM judgment
  in which signals fire or how strong they are.** Same inputs → same salience, unit-tested.
- **No threshold drop (C2).** Emit EVERY firing — wide-orb, single-source, low-strength
  included. **Strength is a COLUMN, not a filter.** Serve-time ranks; the asset never gates.
  This re-exposes the candidate pool the old register erased.
- **Decompose the coefficient** (the audit's §5.2 recommendation, already realized in A10's
  schema): `deterministic_strength` (computed) × `verification_certainty` (rule-checkable) ×
  composed `computed_salience`. Interpretive salience/valence is the ONLY thing a model could
  supply — and Bodha does NOT supply it at write time (serve-time concern).
- **Fresh build — do NOT port the old MSR_v5_0 573 hand-authored signals.** Bodha computes
  signals fresh from `signal_type_registry` predicates × L1 facts. The old corpus is reference
  for *coverage intent* only, never an import source. (This is what makes Bodha clean by
  construction rather than audited-and-fixed.)

### §6.D — Epistemic tiering (inherited from L1 GA-Tajaka; handoff trap 4)

L1 facts come in two tiers: FORENSIC-exact hard facts (positions, Muntha, the 7 anchors) vs
documented-approximations (Tajik-yoga classifier, Pañcavargīya scoring — no JH-parity oracle).
**Carry the tier through into each Bodha row's `verification_pass_status` + `citation_ref`**
per `L1_GANITA_CLOSURE §7.2`:

| Row type | `verification_pass_status` | `citation_ref` form |
|---|---|---|
| Hard-fact (directly read from L1, no judgment) | `two_pass_verified` | `<fact_id>` → L1 `chart_facts` row |
| Synthesized (multi-factor scoring) | `documented_approximation` | `<rule_citation>@constituents=[<fact_id1>,…]` |
| Classical-text application (BPHS/Jaimini/KP) | `documented_approximation` | classical source + activating L1 fact_ids (+ `citation_human`) |

Only rows with `verification_pass_status IN ('two_pass_verified','documented_approximation')`
and non-null `citation_ref` pass the grounding audit. Don't flatten the two tiers.

---

## §7 — Orchestrator conformance (the FROZEN contract — Bodha onboards, does NOT extend)

The orchestrator was built once and FROZEN (`ORCHESTRATOR_CONVERGENCE_CLOSE`). **Every Bodha
writer onboards by conforming — no orchestrator code changes.** **Embed this §5 checklist
VERBATIM in every `bo_` brief:**

> A writer is orchestrator-native iff **all** hold:
> - [ ] **Is a class**, `@register('<asset_id>')`, subclassing `WriterBase`; `asset_id` matches the registry.
> - [ ] **Discoverable** — imported by `_auto_discover()` (lives under `pipeline/orchestrator/writers/` or a thin adapter that does) **and ships in the `brahma-pipeline` job image**.
> - [ ] **`run(ctx)`** (light) **or** `plan_substeps(ctx)` + `run_substep(ctx, step)` (heavy: > ~10 min or > a few hundred k rows).
> - [ ] **Connection:** uses `ctx.db_conn` exclusively; **never** opens its own, **never** `commit()/rollback()/close()`.
> - [ ] **chart_id / birth:** reads `ctx.config['chart_id']` and `ctx.config['birth_params']` (None → its verified default); `ctx.build_id`. **No hard-coded native default in the build path.**
> - [ ] **Idempotency:** its own natural-key-scoped `replace_prior_*` on `ctx.db_conn` immediately before INSERT, scoped to the sub-step key; any sub-step safe to re-run.
> - [ ] **Telemetry:** writes **nothing** to `asset_throughput`; returns counts in `WriterResult`.
> - [ ] **FORENSIC:** any native-anchored assertion is guarded `if chart_id == CANONICAL_CHART_ID`; structural invariants stay unconditional.
> - [ ] **dry_run:** honors `ctx.dry_run`.
> - [ ] **Registry row** with correct `scope`, `asset_type`, `layer`, **populated `depends_on`** (real edges, not `[]`), `count_sql` + `target_floor`, `sort_order`; `has_substeps=true` if heavy; `rebuild_on_probe_fail=true` + a `health_probe`/`integrity_check_sql` if self-healing.
> - [ ] **No orchestrator change required** — if onboarding needs a new `if` in `run_asset`/`runner.py`, the contract was violated; fix the writer, not the orchestrator.

`bo_laksana` (MSR) is almost certainly **heavy** → `plan_substeps` per ayanamsha (×5) and/or
per signal-class. `bo_karanajala` (CGM igraph) and `bo_upaya` (RM, 6 tables) are likely heavy
too. **If any Bodha writer seems to need a contract change → STOP and raise with the native.**
The freeze is deliberate; MSR/CDLM/CGM/RM are per-chart computed writers — exactly what the
contract was generalized for, so it should NOT need one.

Result: when a user clicks Build, the orchestrator runs Bodha in dependency order
automatically — same as L1. Bodha is the first layer built **orchestrator-native from day
one** (no hand-run sidecar script — the whole point of the L1 convergence arc).

---

## §8 — Phase-0 prerequisites (build these BEFORE any `bo_` writer brief)

Phase-0 is the foundation. Each item is a discrete, surgical, verified step:

| # | Phase-0 task | Detail |
|---|---|---|
| P0.1 | **Settle table naming in code** | Author the corrective migration: drop the 6 `l25_*` stub tables (migration 206); create the ~17 full-spec `bodha_*` tables from A10–A14 schemas (renamed `l25_`→`bodha_`). Apply surgically via Cloud SQL proxy, one at a time, file-vs-live verified, tracker row recorded. |
| P0.2 | **Build G52 `signal_type_registry`** | New global asset: ~500–700 data-driven predicate definitions (A10 §5 schema) across all 6 traditions + synthetics. Its own writer + seed, registered in `asset_registry`, made an explicit `depends_on` edge of `bo_laksana`. **Largest Phase-0 task; gates the layer.** |
| P0.3 | **Reconcile the 8 seed rows → real spec tables** | Update each `bo_` row's `target_table`/`count_sql`/`size_sql` to point at its real `bodha_*` spec table(s) per §3.2 map. Confirm `depends_on` matches real reads (add `ga_structural` + `signal_type_registry` to `bo_laksana`). Flip the 8 rows DRAFT→CURRENT only after their tables + writers exist. |
| P0.4 | **Resolve the `bo_samvada`/UCD open item** | Native decision per §3.3 (Option A recommended). Encode the choice before authoring `bo_samvada`'s brief. |
| P0.5 | **Confirm Phase-5 E2E + non-native build proven** | The orchestrator-native build must be proven on a non-native chart before L2 rides the same machinery. #266 fixed non-native builds; confirm the Phase-5 E2E runbook (`ORCHESTRATOR_CONVERGENCE_CLOSE §4`) has been executed green, or schedule it as a Phase-0 gate. `[[project-orchestrator-convergence-complete]]` notes Phase-5 live E2E is operator-only + NOT YET RUN — **run it before L2 builds.** |
| P0.6 | **Author the shared idempotency helper** | `bodha_writers/_idempotency.py` mirroring `ga_writers/_idempotency.py` — per-chart scoped `replace_prior_*(conn, chart_id, natural_key)`. All `bo_` writers import it. |
| P0.7 | **Author `salience_formula_v1` + `resonance_score_v1` as unit-tested pure functions** | A10 §4 + A13 §3. Pure Python, versioned, unit-test fixtures (known inputs → known outputs, reproducibility). These are the deterministic core of Trap-2 avoidance. |

---

## §9 — Per-asset execution briefs (authoring plan + batching)

Each `bo_` asset gets a **fully-detailed, self-contained, Claude-Code-executable brief** (the
L1 `CLAUDECODE_BRIEF_GA{n}_*` pattern Bodha mirrors). Every brief embeds: the §7 conformance
checklist verbatim; the §6.B/§6.C/§6.D trap rules; the exact spec schema (A-N reference); the
exact source `ga_*` facts it reads; the two-pass verification method; the FORENSIC/L1-authority
assertions; atomic grain + idempotency; `count_sql`/`target_floor` cockpit wiring.

**Batch 1 (the root):** `CLAUDECODE_BRIEF_BO_LAKSANA` (A10 MSR). The biggest and the root —
author it alone, get it built + cockpit-verified, before the fan-out. Includes G52 dependency.

**Batch 2 (the fan-out, parallel-safe on MSR):**
`CLAUDECODE_BRIEF_BO_SANGATI` (A11 CDLM), `CLAUDECODE_BRIEF_BO_BIMBA` + `BO_KARANAJALA`
(A12 CGM — see §3.2 split note), `CLAUDECODE_BRIEF_BO_SAMSKARA` (embeddings),
`CLAUDECODE_BRIEF_BO_SAMVADA` (UCD — pending P0.4).

**Batch 3 (the dependents):** `CLAUDECODE_BRIEF_BO_UPAYA` (A13 RM — needs MSR + CDLM),
`CLAUDECODE_BRIEF_BO_PRAMANA_MAPA` (global scorecard).

Each batch closes (built + verified) before the next opens, per the closed-artifact-per-session
discipline.

---

## §10 — Build → verify → seal

1. **Build via the orchestrator** — `POST /api/cockpit/runs { chart_id: 482012f1-…,
   scope: 'layer', scope_target: 'bodha', action: 'build' }`. NOT a hand-run sidecar.
2. **Cockpit-verify** — per-asset `building→lit` via SSE; for heavy writers (`bo_laksana`,
   `bo_karanajala`, `bo_upaya`) ≥N `asset.substep` heartbeats; bars fill; counts true
   (`count_sql` from `asset_registry`); `built_against_writer_hash`/`upstream_hash` non-NULL;
   no `[telemetry]` on the conformed path; `target_floor` = achieved count.
3. **FORENSIC gate** — native-anchored Bodha rows match L1 (Muntha signal = Libra/7H/Venus,
   not re-derived). Cross-layer-consistency check (Trap-1) passes: zero `divergent_flagged`.
4. **Two-pass + grounding audit** — every row `two_pass_verified` or `documented_approximation`
   with non-null `citation_ref`; no narrative columns (no-narration linter green); no
   threshold-drop (weak-tail present in the distribution — the C2 fingerprint absent).
5. **IS.8(b) red-team** — per the macro-phase cadence; zero class-1 findings before seal.
6. **Seal** — `L2_BODHA_CLOSE_v1_0.md` with the validated state + the **L3 Kāla onboarding
   contract** (L3 reads L2 the same way L2 reads L1), mirroring `L1_GANITA_CLOSURE`. Update
   CURRENT_STATE + SESSION_LOG.

---

## §11 — Open questions for the native (raise in the receiving conversation)

1. **`bo_samvada` / UCD (§3.3, P0.4)** — Option A (not a UCN writer; UCD = read-join view +
   `query_ucd` tool, or thin writer for the 5 folded columns) vs Option B (re-scope to a real
   resonance table, requiring an A14 spec amendment)? **Recommend A.**
2. **`bo_bimba`/`bo_karanajala` CGM split (§3.2 note)** — one heavy CGM writer with two
   registry faces, or two writers sharing a compute? **Recommend: one heavy `bo_karanajala`
   writer (nodes+edges+sub_graphs+motifs); `bo_bimba` a thin nodes-face.**
3. **MV scope** — A10 (3 MVs) + A11 (5 MVs) define materialized views "natal-fixed, refresh at
   build close." Build all MVs in Bodha, or defer to a read-optimization pass? **Recommend:
   build with the layer (they're part of the spec) but flag any that depend on multi-chart data.**
4. **Floor reporting** — A10 projects ~4,000–6,250 signals/chart. Confirm `target_floor=null`
   at registry-author time, set = achieved count after first native build (the L1 lesson).

---

## §12 — Verification checklist before declaring L2 Bodha done

- [ ] All ~17 `bodha_*` tables exist to spec; 6 `l25_*` stubs gone; G52 `signal_type_registry` seeded.
- [ ] 8 `bo_` writers `@register`'d, conformant (§7 checklist), shipped in `brahma-pipeline` image, discoverable.
- [ ] Orchestrator builds the whole layer in DAG order from one `scope=layer/bodha` run; heavy writers heartbeat.
- [ ] `bo_laksana` emits genuine MSR signals fresh from G52 × L1 facts (NOT ported from MSR_v5_0); no threshold drop (weak tail present).
- [ ] Salience + resonance are `salience_formula_v1`/`resonance_score_v1` — reproducible, unit-tested; no judgment.
- [ ] Every row references `fact_id`(s) in `constituent_facts_array`; FORENSIC-anchored values inherited from L1, never re-derived; zero `divergent_flagged`.
- [ ] Two-pass verification on every row; epistemic tier carried (`two_pass_verified` vs `documented_approximation`); citation_ref non-null.
- [ ] No-narration linter green; no audience-tier branches; idempotency = per-chart replace (rebuild replaces, not accretes).
- [ ] Cockpit: 8 tiles lit, bars filled, counts true (`count_sql` from `asset_registry`), `target_floor` = achieved.
- [ ] Migrations applied surgically + tracker rows recorded; non-native build proven (Phase-5 E2E green).
- [ ] IS.8(b) red-team: zero class-1. `L2_BODHA_CLOSE` sealed with L3 onboarding contract; CURRENT_STATE + SESSION_LOG updated.

---

## §13 — The L2 Bodha design philosophy (NATIVE-LOCKED — binds every brief)

> This section is the *intent* behind the build. §1–§12 say what to build and how to conform;
> §13 says **what Bodha is FOR** and the bar it must clear. Every per-asset brief is written
> to this philosophy. Recorded fully in memory `feedback-l2-bodha-design-philosophy`.

**The frame.** L1 was *storage completeness* — capture every computable fact. **L2 is
leverage** — turn that corpus into relationships-among-facts, deterministically, stored
optimized for LLM retrievability. L1 answers "what is true about this chart." L2 answers
"**what patterns hold across what's true, and which of them matter.**" That shift — from facts
to relationships-among-facts — is the entire value of Bodha. A human acharya holds ~7±2 factors
in working memory; the instrument's edge is holding *all* of them and computing *every*
meaningful intersection. The acharya-grade bar (§J): Bodha must "reveal things an acharya
wouldn't see on first pass," not merely be complete.

**The five locked principles:**

1. **Within-chart deterministic statistics only; cross-chart → L5.** L2 computes everything
   reproducible from *this chart's own facts*: cross-ayanamsha consistency (a signal firing 5/5
   ayanamshas is deterministically more robust than 2/5 — nuance no human computes), convergence
   density per domain, graph centrality, P10/P50/P90 confidence intervals under input
   perturbation. **None of it touches another person's data or any life outcome.** Cross-chart /
   population / outcome correlation ("this config correlated with career disruption in 62% of
   500 charts") is **L5 Mīmāṃsā** — empirical inference, held-out-gated ("never see the outcome
   before the prediction"), needs the Life Event Log. **The line is the protection:** the moment
   Bodha computes a cross-chart correlation it has left "what the chart structurally says" and
   entered "what we've learned tends to happen" — contaminating the deterministic base the whole
   project rests on. L2 = structural statistics within the chart; L5 = predictive statistics
   across charts.

2. **Convergence + contradiction are FIRST-CLASS artifacts** (the ceiling-raiser).
   - **Convergence-density-per-domain:** not "Saturn is in the 7th" (L1) but "Saturn-in-7th ×
     7th-lord-debilitated × Venus-combust × Sade-Sati-active-this-dasha × Dārākaraka-afflicted"
     — *N independent L1 signals converging on one domain (relationships)*. The convergence
     count is itself a deterministic, computable strength score. **This is the single most
     acharya-like move: weight of evidence, not isolated rules.**
   - **Contradiction-pairs:** where L1 signals *conflict* — a Raja Yoga firing while its
     constituent planets are `divergent_flagged` across ayanamshas; a benefic yoga whose lord
     sits in maraṇa-kāraka-sthāna. Stored as first-class rows carrying the *deterministic basis
     for the tension*. An acharya's skill is partly resolving contradictions; the instrument's
     edge is surfacing *every one* so none is missed. **Contradiction-detection is both the
     deepest insight AND the drift guardrail** — the MSR computed-value-drift trap (§6.B) is
     itself a contradiction-detection problem (signal-vs-L1-fact). Make it a feature, not just
     a guardrail.

3. **Retrieval architecture = "rich pre-computed relational INGREDIENTS, LLM synthesizes at
   query"** (NOT pre-answered questions). This is the deliberate resolution of the
   flexibility-vs-determinism tension, and it interacts directly with the drift trap:
   - Bodha does **NOT pre-answer** ("career → one canned answer row") — that would sacrifice the
     query-time flexibility a *research instrument* needs (it must answer questions you didn't
     pre-anticipate).
   - Bodha **DOES pre-compute the deterministic RELATIONSHIPS** — convergence counts,
     contradiction pairs, graph properties, salience rankings — and stores them as first-class,
     citable, provenance-bearing rows alongside the granular signals.
   - The query-time LLM then **synthesizes the narrative from a pre-structured, pre-related,
     drift-resistant ingredient set** — it does **flexible narration, not flexible
     computation.** The relationships can't drift, because they were computed at build time
     (reproducible, auditable, cited). The LLM composes from pre-computed relationships, not a
     pile of raw atoms — so it has less room to drift and more structure to ground in.
   - **Two retrieval axes, both built:** `bo_samskara` embeddings give *semantic* retrieval;
     `computed_salience` gives *significance* retrieval. "Give me the top 5 things about this
     chart" returns the genuinely strongest 5, deterministically, every time. Salience is the
     universal sort key on every L2 artifact (signals, edges, domain-cells, resonance).

4. **Every judgment is a VERSIONED FORMULA, not a stored opinion** — the unifying principle and
   the architectural fix for the contamination trap (§6.C / audit C1). The prior MSR build let
   authoring judgment leak into *which signals fire* and *how strong they are*. The fix is not
   "be more careful" — it is architectural: **every selection, every weight, every threshold is
   a parameter in a named, versioned formula** (`salience_formula_v1`, `convergence_formula_v1`,
   `centrality_formula_v1`, `resonance_score_v1`). Then "why is this the top signal?" has a
   deterministic, reproducible, auditable answer. Improve the method → bump the formula version
   → rebuild → clean before/after. **This is what makes Bodha a research instrument a senior
   acharya reviews at the METHOD level (the formula), rather than arguing with individual
   outputs** — and not a fancy lookup.

5. **Invest hardest in the GRAPH** (`bo_karanajala` + `bo_bimba` / CGM A12) — **the part not to
   under-build.** A chart *is* a graph: grahas/houses/signs as nodes; aspect / dispositor /
   lordship / conjunction / parivartana / karaka as typed edges. L1 has every edge as an atom;
   L2 computes the graph-theoretic properties **no acharya computes by hand but that are
   deterministic and deeply meaningful** — and here "deterministic" and "deep insight" stop
   being in tension, *because the insight IS the computed graph property*:
   - **Final-dispositor convergence** — trace every `graha_dispositor_chain` (already in L1) to
     its terminus; the planet the most chains converge on is, deterministically, the chart's
     *center of gravity / functional king*. Plus parivartana cycle structure (the loops).
   - **Centrality** — highest weighted degree (aspects given+received + lordships + karaka
     roles) = a deterministic *"most consequential factor" ranking* that a human only
     approximates by intuition.
   - **Path analysis** — shortest-path / does-a-path-exist between domain significators (e.g.
     10th-lord ↔ 5th-lord = career ↔ creativity) traced through the edge graph. **This is
     exactly the reasoning chain an acharya narrates** — made computable.

**One-line for the briefs:** *L2 Bodha pre-computes, with versioned deterministic formulas, the
within-chart relationships-convergences-contradictions-and-graph-structure between L1's atoms,
storing them as rich, salience-ranked, fully-provenanced ingredients that a query-time LLM
synthesizes into insight — deferring all cross-chart predictive statistics to L5, and treating
contradiction-detection as a first-class feature because it is both the deepest insight and the
guardrail against the drift trap.*

### §13.1 — Where this EXTENDS the LOCKED A10–A14 specs (flag for native sign-off at brief time)

The philosophy adds scope beyond what A10–A14 currently LOCK. These extensions must get
explicit native sign-off when the affected brief is authored — **add them deliberately, never
silently** (the LOCKED specs carry the native's 2026-05-29 sign-off; extending them is a
version-bump event per B.8):

| Extension | Beyond the spec because… | Lands in |
|---|---|---|
| **Convergence-density-per-domain as its own salience-ranked artifact** | A11 CDLM scopes pairwise domain *cells*; this is the per-domain *count of independent converging signals* as a first-class row + `convergence_formula_v1` | A11 amendment → `bodha_cdlm_*` (new rollup/cluster rows or a `bodha_convergence` table) |
| **Contradiction-pairs as first-class rows** | A10 has `contradicts_signals_array` (a column); this promotes contradictions to *their own rows* with the deterministic tension basis + salience | A10/A11 amendment → a `bodha_contradictions` table |
| **Graph-depth: final-dispositor convergence, weighted centrality, path-analysis** | A12 specs nodes+edges+motifs; this mandates the *graph-theoretic computations* (chain-terminus convergence, centrality ranking, significator path-existence) as flat columns / derived rows + `centrality_formula_v1` | A12 amendment → flat cols on `bodha_cgm_nodes` + a derived `bodha_cgm_paths`/terminus structure |
| **New versioned formulas** | `convergence_formula_v1`, `centrality_formula_v1` join `salience_formula_v1`/`resonance_score_v1` as named, unit-tested pure functions (P0.7 extends to cover them) | Phase-0 P0.7 |

**Build-priority consequence:** `bo_karanajala`/`bo_bimba` (the graph) become the
**deepest-built assets** in Batch 2, and A11 (`bo_sangati`) gains the convergence/contradiction
first-class scope. The per-asset briefs reflect this; the A10–A14 spec amendments are authored
alongside their briefs and sign-off-gated.

---

## §14 — LOCKED asset → table mapping (the Phase-E transcription reference)

This is the definitive map of each `bo_` asset to its **full spec table set** (names renamed
`l25_`→`bodha_` per §3.1, with §13.1 extensions folded into the owning asset), its **primary
table**, and the **summed `count_sql`** (native decision §0.0 item 7: sum across ALL the asset's
tables). Phase E transcribes this verbatim into `asset_registry_seed.ts`; Phase B's migration
creates exactly these tables. All table names are authoritative against A10–A14 §-schemas as read
2026-06-12. **`count_sql` is chart-scoped (`WHERE chart_id = $1`) summed across the asset's tables;
MVs are NOT counted** (they're derived). `target_floor` = achieved sum after first native build.

| asset | spec | bodha_* tables it writes | primary (headline) | depends_on (corrected) |
|---|---|---|---|---|
| `bo_laksana` | A10 | `bodha_msr_signals` (+ MVs `mv_msr_top_signals_per_chart`/`_recurring_patterns_per_chart`/`_domain_summary`) | `bodha_msr_signals` | `['ga_structural','signal_type_registry']` |
| `bo_sangati` | A11 + §13.1 | `bodha_cdlm_cells`, `bodha_cdlm_domain_rollups`, `bodha_cdlm_chart_summary`, `bodha_cdlm_pattern_clusters`, `bodha_cdlm_evolution_gradients`, **`bodha_convergence`** (+ 5 MVs) | `bodha_cdlm_cells` | `['bo_laksana']` |
| `bo_bimba` | A12 (nodes) | `bodha_cgm_nodes` | `bodha_cgm_nodes` | `['bo_laksana']` |
| `bo_karanajala` | A12 (edges+struct) + §13.1 | `bodha_cgm_edges`, `bodha_cgm_sub_graphs`, `bodha_cgm_motifs`, `bodha_cgm_chart_topology_summary`, **`bodha_cgm_paths`** | `bodha_cgm_edges` | `['bo_laksana']` |
| `bo_upaya` | A13 | `bodha_rm_resonances`, `bodha_rm_remedy_prescriptions`, `bodha_rm_dasha_windowed_prescriptions`, `bodha_rm_dosha_remedy_bundles`, `bodha_rm_pattern_remedies`, `bodha_rm_chart_summary` | `bodha_rm_resonances` | `['bo_laksana','bo_sangati']` |
| `bo_samskara` | embeddings | `bodha_signal_embeddings` (pgvector; 1:1 w/ MSR) | `bodha_signal_embeddings` | `['bo_laksana']` |
| `bo_samvada` | A14 (Option A) | **NONE as a per-chart writer** — UCD = read-side join (`vw_chart_digest` + `query_ucd`), and/or thin writer for the 5 folded UCD columns on existing summary tables. **Contradiction-pairs land in `bodha_contradictions`** (§13.1) — decide at brief time whether `bo_karanajala`, `bo_sangati`, or `bo_samvada` owns that table. | n/a (or `bodha_contradictions` if it owns it) | `['bo_laksana']` |
| `bo_pramana_mapa` | scorecard | `synthesis_quality_scorecard` (global) | `synthesis_quality_scorecard` | `[]` (global) |

**Open sub-decision flagged for brief time (not blocking this mapping):** which asset OWNS
`bodha_contradictions` — contradiction-pairs are computed over the CGM graph (`bo_karanajala`) but
consumed by CDLM convergence (`bo_sangati`). Recommend `bo_karanajala` owns it (it has the edge
graph), `bo_sangati` reads it. Confirm when the A12/A11 amendments are authored (Phase A).

**Summed `count_sql` shape (Phase E writes this per multi-table asset).** Example — `bo_sangati`:

```sql
SELECT
  (SELECT count(*) FROM bodha_cdlm_cells            WHERE chart_id = $1)
+ (SELECT count(*) FROM bodha_cdlm_domain_rollups   WHERE chart_id = $1)
+ (SELECT count(*) FROM bodha_cdlm_chart_summary    WHERE chart_id = $1)
+ (SELECT count(*) FROM bodha_cdlm_pattern_clusters WHERE chart_id = $1)
+ (SELECT count(*) FROM bodha_cdlm_evolution_gradients WHERE chart_id = $1)
+ (SELECT count(*) FROM bodha_convergence           WHERE chart_id = $1)
```

Single-table assets (`bo_bimba`, `bo_samskara`, `bo_pramana_mapa`) keep a plain
`SELECT count(*) FROM <table> WHERE chart_id = $1` (global scorecard drops the WHERE).

---

*End of L2_BODHA_BUILD_CAMPAIGN_v1_0. Bodha is the synthesis layer — deterministic structural
signals over L1 facts, built orchestrator-native, under the standards L0/L1 proved, with the
rich LOCKED A10–A14 architecture (renamed bodha_*) plus the §13 design philosophy (convergence +
contradiction first-class, graph built deepest, every judgment a versioned formula,
within-chart-only stats), avoiding the documented computed-value-drift and contamination traps.
L1 is the authority; Bodha references, never re-derives over it. Next deliverables: Phase-0
prereq briefs (P0.1–P0.7) then the per-asset briefs, Batch 1 (bo_laksana) first — each written
to §13 and carrying its A10–A14 spec amendment where §13.1 applies.*
