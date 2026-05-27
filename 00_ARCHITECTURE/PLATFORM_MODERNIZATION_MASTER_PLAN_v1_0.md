---
artifact: PLATFORM_MODERNIZATION_MASTER_PLAN_v1_0.md
document: MARSYS-JIS Platform Modernization & Refactoring — Unified Master Plan
status: DRAFT (umbrella plan — pending native approval; modifies nothing canonical)
version: 1.0
date: 2026-05-27
authored_by: Claude (Cowork session) — reconciliation of the 2026-05-27 plan family + this session's design thread
purpose: >
  Bring nine separately-authored plans into one coherent modernization program: the deterministic
  data rebuild, the JH-equivalent fact engine, the layer-model simplification, multi-tenancy, the
  coefficient model, the tooling refactor, and the autonomous build pipeline — with a single
  sequencing spine, a per-aspect view, a cutover/rollback strategy, a risk register, and a
  consolidated open-decisions list. This is an INDEX + RECONCILIATION; it cites the constituent
  plans by reference and does not duplicate their bodies.
constituent_plans:
  data_engine:
    - 00_ARCHITECTURE/DATA_LAYER_REBUILD_TARGET_SPEC_v1_0.md        # authoritative data-rebuild spec
    - 00_ARCHITECTURE/BRIEFS/FACT_ENGINE_PYJHORA_BRIEF_v1_0.md      # engine layer
    - 00_ARCHITECTURE/STRUCTURAL_FACT_LAYER_SPEC_v1_0.md            # T1 structural facts
  tooling:
    - 00_ARCHITECTURE/TOOL_PORTFOLIO_PLAN_v1_4.md                   # tool refactor plan
    - 00_ARCHITECTURE/INVESTIGATION/TOOL_PORTFOLIO_REALITY_REPORT.md# verified tool facts
    - 00_ARCHITECTURE/PANEL_MODE_TOOL_SPEC_v1_0.md                  # serve-time tool surface
  platform_portal:
    - 00_ARCHITECTURE/PLATFORM_REBUILD_ARCHITECTURE_v1_0.md         # multi-chart + autonomous build
    - 00_ARCHITECTURE/PORTAL_NORTH_STAR_ARCHITECTURE_v1_0.md        # multi-guest + cockpit + pipelines
  governing_findings:
    - 00_ARCHITECTURE/MSR_UCN_CONTAMINATION_AUDIT_v1_0.md           # why the rebuild
    - 00_ARCHITECTURE/PROVENANCE_TIERING_DECISION_v1_0.md           # provenance discipline (partly superseded)
supersessions_honored:
  - "DATA_LAYER §1: salience = COMPUTED column (formula authored once, value computed), NOT serve-time panel vote. Narrows PANEL_MODE_TOOL_SPEC + MSR_UCN_CONTAMINATION_AUDIT §5.2.3 — the LLM panel does meaning/valence only, not the salience number."
  - "DATA_LAYER §3: old corpus = ARCHIVE (freeze as model_attributed) + REPLACE live canonical after JH gate. Upgrades PROVENANCE_TIERING 'reposition T2'."
approval_gate: native sign-off required; this is a multi-canonical-artifact program → treat as a new macro-phase with version bumps + mirror discipline + red-team at close (CLAUDE.md §L, §M).
---

# Platform Modernization & Refactoring — Unified Master Plan

## §0 — Thesis (one paragraph)

One autonomous pipeline takes a single input — birth datetime (IST), lat, lon, location — and
deterministically builds the entire per-chart corpus, narrative-free, on a JH-equivalent Python
engine; every datum is retained with one or more **computed** coefficients (nothing dropped);
interpretation, narrative, and the pick move to **serve time**, where a model panel reasons over
the deterministic substrate and a judge reconciles. The same program completes **multi-tenancy**
(chart_id as the one tenant key, owner/subject split, one authorization brain), **refactors the
tooling** (unify the duplicated dual channel behind one contract, strip the query-time judgment
out of the retrieval logic), and **modernizes the portal** (Consult rename, Command Center gate
control plane, two isolated query pipelines). The existing store schema is *extended additively*,
not torn down, so the refactored tools keep their contracts. This is the largest change in the
project's history and must be run as a governed macro-phase, not a big-bang.

---

## §1 — The reconciliation map (who owns what; what supersedes what)

Nine plans, five tracks. The relationships that matter:

- **DATA_LAYER_REBUILD_TARGET_SPEC is the authoritative data-rebuild spec.** It supersedes the
  *content* decisions in my earlier PROVENANCE_TIERING (reposition→archive+replace) and narrows
  the salience role in PANEL_MODE / CONTAMINATION_AUDIT (computed column, not panel vote). Where
  this master plan and a constituent disagree, DATA_LAYER wins on data, North-Star wins on
  portal/tenancy, TOOL_PORTFOLIO v1.4 wins on tools, FACT_ENGINE wins on the engine.
- **The five briefs from this session feed the four pre-existing plans**, they don't compete with
  them: FACT_ENGINE + STRUCTURAL_FACT_LAYER are the "how" under DATA_LAYER's "what"; the
  CONTAMINATION_AUDIT is the "why"; PANEL_MODE is the serve-time half of DATA_LAYER §4.
- **No constituent plan owned the tool *de-judgment* finding** (this session): the query-time
  confidence floors / cliques / weights inside the retrieval logic. This master plan injects it
  as an explicit Track-2 phase, because without it the never-drop principle dies at the tool
  boundary even with perfect data.

---

## §2 — The unifying architecture (the single coherent picture)

```
INPUT (datetime IST · lat · lon · location)  →  assigns chart_id
        │
   [Track 3] charts registry (owner≠subject) · chart_grants · authorizeChartAccess
        │
   [Track 1]  PyJHora engine ──adapter──▶ canonical JSONL (source of truth)
        │            │                         │
        │     pyswisseph x-check        FORENSIC v8.0 oracle  ── JH PARITY GATE (Phase 0)
        │                                       │
        │     deterministic loader ─────────────┘
        ▼
   EXISTING STORES (schema extended additively · chart_id-keyed · coefficients child-table)
        │   L1 facts → L1.5 derivations → L2.5 skeleton + COMPUTED coefficients
        │   (MSR complete/never-drop · CDLM shared-factor graph · CGM structural graph ·
        │    UCN computed signature digest · RM deterministic remedy lookup)
        ▼
   [Track 2] unified retrieval contract (one impl, not two) · de-judged · B.11 from T1
        ▼
   [Track 5] SERVE TIME: model panel (meaning/valence only) → judge → answer
        ▲
   [Track 4] Portal/Consult · Command Center gates (source + query availability) · 2 isolated pipelines
```

Determinism seam: **everything through the L2.5 skeleton + computed coefficients is deterministic;
only meaning/valence/narrative/pick at serve time is non-deterministic** (panel + judge). The
coefficient is the boundary object.

---

## §3 — The five tracks

### Track 1 — Engine & Deterministic Data `[owns: DATA_LAYER, FACT_ENGINE, STRUCTURAL_FACT_LAYER]`
PyJHora wrapped+validated → canonical JSONL → loader → extended stores. L1 (engine-direct) folds
with L1.5 (derivations) into one deterministic fact tier (provenance-tagged), per the layer model
we settled. L2 is dropped (Mode-B completeness is inherent in deterministic generation; Mode-A
narrative → serve time). L2.5 assets rebuilt to the same schema as skeleton + **computed**
coefficients. The CGM *is* the deterministic fact-graph (no separate middle layer).
**My view:** this is the spine; everything else is downstream. The single highest-value addition
remains computed shadbala/ashtakavarga feeding the coefficients.

### Track 2 — Tooling Refactor `[owns: TOOL_PORTFOLIO v1.4, REALITY_REPORT, PANEL_MODE]`
Three layers, three treatments (this session's core finding):
1. **Schema** — extend additively (chart_id everywhere, a coefficients child-table keyed by
   `(fact_id, chart_id, source)`, narrative columns emptied). No teardown.
2. **Contracts** — keep; but **unify the duplicated dual channel** (`platform/src/lib/retrieve/`
   *and* `platform-mcp/src/tools/`) behind one contract + shared Zod schema. This is the biggest
   mess-multiplier: every change today is made twice.
3. **Logic — DE-JUDGMENT (the phase the v1.4 plan underweights):** strip the query-time
   `CONFIDENCE_FLOOR=0.6`, the `FINANCE_WEALTH_FLOOR=0.35`, the hardcoded `PANCHA_MP_CLIQUE`, and
   the inlined `LL1_PRODUCTION_WEIGHTS` out of `msr_sql.ts` (and peers). Return all signals with
   coefficients; move the pick to the serve-time model. Also: fix 17 ghost tools, SURGICAL_TOOLS
   duplicates, null `query_schema`, stale tests (REALITY_REPORT).
**My view:** do contract-unification *before* de-judgment so the logic change is done once.

### Track 3 — Multi-tenancy & Autonomous Build `[owns: PLATFORM_REBUILD, North-Star §3]`
chart_id as the one tenant key (already half-threaded — `signal_states` has it, tools default to
`NATIVE_CHART_ID`); charts registry splitting **owner ≠ subject**; `chart_grants` view-only ACL;
**one `authorizeChartAccess` brain for web + MCP.** The autonomous build = the deterministic,
content-addressed ~25-node DAG fired from a dashboard Build/Rebuild button, with two-level progress
UX and live per-asset verification.
**My view:** the build DAG is *not* the Conductor — Conductor orchestrates LLM sessions, this
orchestrates pure computation with no LLM in the path. Keep them distinct. Complete chart_id before
flipping the `NATIVE_CHART_ID` fallback off (hard gate).

### Track 4 — Portal & Experience `[owns: North-Star]`
Consume→Consult rename; role client→guest; shared-chart view-only; **Command Center** runtime gate
control plane (five gate classes incl. data-source + query-level availability); two **isolated**
query pipelines (Classic single-pass vs Claude-style agentic) in `lib/pipelines/shared/`; remove
the depth selector.
**My view:** the Command Center is exactly the home for the "source-level + query-level
availability" control you described — your control over what's built and what's exposed becomes a
runtime gate registry, not code edits.

### Track 5 — Serve-time Query & Learning `[owns: DATA_LAYER §4, PANEL_MODE, learning layer]`
Interpretation lives here now: the model panel reasons over the deterministic substrate and does
**meaning/valence only** (salience is already a computed column upstream); the judge reconciles;
the query-level gate decides what's exposed per model/tier. Prospective predictions are logged
before outcomes (sacrosanct held-out), feeding the learning layer, which calibrates the **computed
salience formula** over time.
**My view:** this closes the loop — the learning layer is what makes the computed coefficient
*improve* rather than being a one-time authored formula. It only becomes statistically meaningful
at multi-native scale, so build it instrumented-but-uncalibrated now (per our n=1 discussion).

---

## §4 — Sequencing spine & hard gates

**Hard gates (non-negotiable orderings):**
1. **JH parity gate** (engine reproduces FORENSIC v8.0 for the native; ayanamsha pinned) — *nothing
   above L1 is buildable until this passes.* (DATA_LAYER §5, FACT_ENGINE Phase 0.)
2. **Multi-tenant authz live before tier-excision** — else an access-control gap opens (v1.4 §5).
3. **Contract unification before de-judgment** — so the logic change is made once, not twice.
4. **Data plane chart_id-keyed before the `NATIVE_CHART_ID` fallback is removed** (v1.4 Phase 3).

**Wave model (parallel-safe unless a gate intervenes):**
- **Wave 0 — immediate, parallel-safe:** tooling hygiene (ghosts, dups, stale tests, null
  query_schema) + B.11 hotfix. No dependency on anything. *(TOOL Phase 0/1.)*
- **Wave 1 — the gate:** engine + adapter + JH parity gate (Track 1). Blocks all of L2.5.
- **Wave 2 — parallel:** (a) L1→L1.5→L2.5 deterministic build into the extended schema (Track 1);
  (b) contract unification + chart_id landing (Track 2); (c) charts registry + authz brain
  (Track 3). These share only the schema, coordinate via it.
- **Wave 3 — sequenced:** de-judgment (after contract unification); per-chart cutover (after build
  validates); portal rename + Command Center + pipeline isolation (co-arc with authz); tier-excision
  (after authz live).
- **Wave 4 — close:** eval re-baseline (multi-chart aware, after data+contract cutover); learning
  loop wiring; red-team + macro-phase seal.

---

## §5 — My view on each aspect (discussed and not)

- **Engine-first is correct and non-negotiable.** The JH parity gate is the cheapest insurance in
  the program; skipping or deferring it risks building the entire corpus on a mis-pinned ayanamsha.
- **Salience-as-computed-column (DATA_LAYER's upgrade) is the right call** and stronger than my
  panel-vote idea — *with one caveat:* keep the computed coefficient and any serve-time LLM
  meaning/valence in clearly separate fields, so the panel retains a defined narrow job and never
  silently re-introduces a "score." Store multiple coefficients in the child table, not one column.
- **Archive + replace: endorse the destination, reject the big-bang.** Replacing live canonical
  files is the single riskiest act in the program. Do it as a **strangler / parallel-run**: build
  the new chart_id-keyed corpus alongside the old, validate each asset vs the JH oracle *and* diff
  vs the old corpus, cut over **per-chart behind a Command Center gate**, and keep the frozen old
  corpus as the rollback. Never a single global swap.
- **Tool de-judgment is the missing phase** and I'd rank it as important as the data rebuild
  itself — clean data through a tool that still applies a 0.6 floor is still dropped data.
- **Dual-channel unification is the highest-leverage cleanup.** Two implementations of every tool
  is the reason the portfolio is "a mess"; unifying behind one contract makes every future change
  (including de-judgment) single-site.
- **Multi-tenancy is foundational, not a feature.** chart_id + owner/subject split + one authz
  brain should land early because tier-excision, sharing, and the cockpit all gate on it.
- **Command Center is the right home for your source/query control** — it operationalizes the
  provenance-tiering decision as runtime gates rather than fixed code.
- **Two-pipeline isolation is sound;** put the gateway + B.11-from-T1 + authz in the shared seam so
  both pipelines inherit them.
- **Not discussed but relevant — geocoding/historical timezone:** for the native (IST) it's trivial,
  but multi-tenancy means arbitrary birth places/eras → historical DST/timezone resolution becomes a
  determinism risk at intake. Pin a geocode+tz resolution source and record it in provenance.
- **Not discussed — the learning loop is where the coefficient stops being a one-time opinion.**
  Without it, "computed salience" is just a frozen formula someone authored. Wire prediction-logging
  now (instrumented, uncalibrated) so the loop exists before scale makes it meaningful.
- **Not discussed — governance load.** This program touches almost every canonical artifact. It must
  run as a declared macro-phase with version bumps, mirror discipline, and a red-team at close — not
  as scattered edits. That overhead is real and should be in the schedule.

---

## §6 — Cutover & rollback (the riskiest part, called out separately)

1. Build the new corpus into **new chart_id-keyed rows/tables alongside** the live ones (no
   in-place mutation).
2. **Validate** each asset: vs JH oracle (correctness) + diff vs old corpus (regression awareness —
   divergences are expected where the old corpus was contaminated; they are reviewed, not feared).
3. **Cut over per-chart behind a Command Center gate** — the native chart first, validated live,
   before any other.
4. **Freeze the old corpus** as `model_attributed` archive (rollback target), do not delete.
5. **Re-baseline eval** only after cutover, multi-chart aware, once per consolidated batch (not
   per-PR — project discipline).

---

## §7 — Risk register

| # | Risk | Mitigation |
|---|---|---|
| R1 | Big-bang archive+replace destroys the live system / no rollback | Strangler parallel-run; per-chart gated cutover; freeze old (§6) |
| R2 | PyJHora ayanamsha mismatch invalidates the whole corpus | JH parity gate before any L2.5 build (Gate 1) |
| R3 | De-judgment surfaces weak signals → eval looks "broken" | Re-baseline; the change is intended, not a regression |
| R4 | Data + tooling + portal entangled into one mega-effort | Five isolated tracks + contract seam + per-track worktrees |
| R5 | Silent canonical changes break mirror/drift governance | Run as a macro-phase; native approval; version bumps; red-team |
| R6 | Tier removed before authz live → access-control gap | Hard gate 2 |
| R7 | "Computed salience" is itself an encoded judgment | Author formula transparently; version it; calibrate via learning loop; keep auditable |
| R8 | Multi-tenant intake non-determinism (historical tz/geocode) | Pin geocode+tz source; record in provenance |

---

## §8 — Consolidated open decisions (from all plans + this session)

1. **Ayanamsha parity** — settled (PyJHora reproduces FORENSIC), or is Phase 0 the first build step?
2. **Coefficient storage** — confirm the `(fact_id, chart_id, source)` child-table shape.
3. **Hybrid tools** — `vector_search` / `domain_report_query` chart_id-optional rule (v1.4 Q5).
4. **Write/ops authz** — who calls log_prediction/record_outcome/flag_disagreement/tool_health/
   data_coverage post-tier (v1.4 Q4).
5. **Pipeline isolation timing** — A0 precondition vs co-arc for the gateway (v1.4 Q7; recommend co-arc).
6. **Per-asset additional deterministic data** — confirm the accuracy add-ons per asset (PLATFORM §6).
7. **Cutover granularity** — per-chart gated (my recommendation) vs per-asset vs global.
8. **Macro-phase declaration** — what M-number / governance wrapper this program runs under.

---

## §9 — Provenance
Model-authored (Claude, Cowork), DRAFT, reconciling the 2026-05-27 plan family. Modifies nothing.
Per CLAUDE.md §L, no implementation begins until the native approves and the affected canonical
artifacts are version-bumped. Recommended next step: declare the macro-phase, then dispatch
per-track CLAUDECODE_BRIEF units (each track above is already plan-backed by its constituent docs).
