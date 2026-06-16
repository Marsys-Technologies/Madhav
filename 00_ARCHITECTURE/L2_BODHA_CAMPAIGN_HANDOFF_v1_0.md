---
artifact: L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md
canonical_id: L2_BODHA_CAMPAIGN_HANDOFF
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10
authored_for: the L2 Bodha campaign (Cowork plans → Claude Code in Antigravity executes)
purpose: >
  The single authoritative starting context for L2 Bodha. Carries forward everything L0+L1
  established — nomenclature, standards, the FROZEN orchestrator contract, the L1→L2 data
  interface, the 8-asset Bodha DAG, the per-asset specs, and the hard-won traps — so Bodha
  begins fully aligned instead of rediscovering the rules. Read this FIRST when L2 opens.
supersedes: none (new)
read_in_combination_with:
  - 00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md (the FROZEN contract + §5 conformance checklist)
  - 00_ARCHITECTURE/L1_GANITA_CLOSURE_v1_0.md (L1 sealed state + L2 onboarding contract)
  - 00_ARCHITECTURE/A10_MSR_SPEC_v1_0.md … A13_RM_SPEC + A14_UCN_RETIRED_TO_UCD (the L2 asset specs)
  - 00_ARCHITECTURE/MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md (THE trap — read it)
  - 00_ARCHITECTURE/MSR_UCN_CONTAMINATION_AUDIT_v1_0.md (the contamination trap)
  - L1 per-asset briefs CLAUDECODE_BRIEF_GA{3..9}_* + GA_TAJAKA (the pattern Bodha mirrors)
---

# L2 Bodha — Campaign Handoff v1.0

## §0 — What Bodha is, in one paragraph

L2 Bodha (Bodha = "understanding/cognition") is the **synthesis layer**. Where L1 Gaṇita computed
the deterministic chart facts, Bodha computes the **structural relationships and signals** over those
facts: which classical yogas/doshas/patterns FIRE, how they LINK across domains, the GRAPH of grahas/
houses/configs, the strongest signals for REMEDY candidacy, and the chart's overall SIGNATURE. It is
still **deterministic fact** — predicate firings, graph edges, computed salience — **NOT interpretation/
narrative**. Interpretation happens at serve-time, never in the asset. This is the single most important
inherited rule (see §6 traps).

## §1 — Nomenclature + naming standards (LOCKED — match these exactly)

- **External lexicon (LOCKED):** Brahmagyan · Gaṇita · **Bodha** · Kāla · Phala · Mīmāṃsā = internal
  L0 · L1 · **L2** · L3 · L4 · L5. Never show "L0–L5" externally. L2.5 is an internal synonym for the
  Bodha synthesis layer (the `l25_*` table prefix = "Layer 2.5, the synthesis layer above L1.5 chart_facts").
- **Asset-id convention: underscore prefix.** `bg_*` (L0) · `ga_*` (L1) · **`bo_*`** (L2) · `ka_*` (L3) ·
  `ph_*` (L4) · `mi_*` (L5). The dot-notation placeholders were renamed to underscore in migration 224
  (L1 closure Phase B). NEVER create a `bodha.*` id — the orchestrator's `@register('bo_*')` pattern keys
  on underscore.
- **Sanskrit + English names** per asset, roman IAST (like L0/L1 — Graha-sphuṭa, not पञ्चाङ्ग). The 8 bo_
  rows already carry these (Lakṣaṇa / Kāraṇajāla / Bimba / Saṃskāra / Saṅgati / Upāya / Saṃvāda / Pramāṇa-māpā).
- **Canonical chart:** native = `482012f1-710e-4a25-994a-93821f5871aa`. `362f9f17-…` is a DEAD phantom —
  it litters the A10–A14 spec citation examples as `chart=362f9f17`; those are PLACEHOLDERS, never write it.
- **Table prefix:** L2 tables are `bodha_*` (bodha_signals, bodha_graph, bodha_graph_edges,
  bodha_domain_links, bodha_remediation, bodha_resonance, bodha_signal_embeddings) + the global
  `synthesis_quality_scorecard`. (The A10–A14 specs say `l25_msr_signals` etc. — reconcile: the seed
  placeholders use `bodha_*`; confirm the canonical table names at campaign open and make spec + seed +
  writer agree. This is a known spec-vs-seed naming reconciliation, like ganita_dashas vs chart_dashas was.)

## §2 — The 8 Bodha assets + the DAG (already in the registry, post-rename)

All `scope: per_chart` except `bo_pramana_mapa` (global). `depends_on` already wired (migration 223/224):

| asset_id | Sanskrit | English | table | depends_on | spec |
|---|---|---|---|---|---|
| `bo_laksana` | Lakṣaṇa | Signal store (MSR) | bodha_signals | `bg_rules` | **A10** — the ROOT; everything fans from it |
| `bo_bimba` | Bimba | Signal graph nodes | bodha_graph | `bo_laksana` | A12 (CGM nodes) |
| `bo_karanajala` | Kāraṇajāla | Signal graph edges (CGM) | bodha_graph_edges | `bo_laksana` | A12 (CGM edges) |
| `bo_sangati` | Saṅgati | Domain links (CDLM) | bodha_domain_links | `bo_laksana` | A11 |
| `bo_samvada` | Saṃvāda | UCN resonance | bodha_resonance | `bo_laksana` | A14 (UCN→UCD) |
| `bo_upaya` | Upāya | Remediation (RM) | bodha_remediation | `bo_laksana`, `bo_sangati` | A13 |
| `bo_samskara` | Saṃskāra | Signal embeddings | bodha_signal_embeddings | `bo_laksana` | (embeddings — deterministic transform) |
| `bo_pramana_mapa` | Pramāṇa-māpā | Synthesis quality | synthesis_quality_scorecard | [] (global) | scorecard |

**Build order:** `bo_laksana` (MSR) FIRST — it is the root the whole layer depends on. Then
`bo_bimba ∥ bo_karanajala ∥ bo_sangati ∥ bo_samvada ∥ bo_samskara` (parallel on MSR), then `bo_upaya`
(needs MSR + CDLM). `bo_pramana_mapa` is a global scorecard. The orchestrator runs this from the
`depends_on` DAG automatically — confirm the edges match this intended order at open (verify against what
each writer actually reads, per the L1 Phase-4 lesson).

## §3 — What Bodha CONSUMES from L1 (the data interface — verified queryable)

Bodha reads L1's `chart_facts` (+ chart_dashas, chart_divisionals) via SQL. Confirmed present for the
native (L1 closure Phase A.2):
- **`ga_structural` (6,075 rows)** — the primary MSR feed: `yoga_fires`, `dosha_fires`, `aspect_*`,
  `graha_dispositor_chain`, `argala_natal_matrix`, avasthas, composite strengths. Every fired structural
  fact → an MSR signal.
- `ga_strength` (shadbala/ashtakavarga) → salience components.
- `ga_sensitive` (karakas, sahams, KP, Tajik, esoteric points) → tradition-specific signals.
- `ga_dashas` → `dasha_activation_proximity_score` (all 7 systems, per A10 Q4).
- `ga_sade_sati`, `ga_panchanga`, `ga_vargas`, `ga_positions` → their respective signal classes.
- **MSR `constituent_facts_array` references fact_ids back to chart_facts** — these MUST resolve. L1
  emitted clean fact_ids precisely so Bodha can back-reference. This is the L1→L2 contract.

## §4 — The standards Bodha INHERITS (non-negotiable — same as L0/L1)

1. **Deterministic-first.** Python over LLM. Embeddings (`bo_samskara`) are a deterministic transform and
   are fine; generative LLM for curation is NOT. ([[feedback-deterministic-first-for-data-build]])
2. **Only facts, no narrative.** No `interpretation`/`meaning`/`narrative` columns. The no-narration
   linter applies. Structured predicate firings + computed salience only. Interpretation = serve-time.
3. **Atomic grain.** One row per signal firing (MSR), one row per edge (CGM), etc. JSONB only for genuinely
   irreducible composites (`configuration_jsonb` is sanctioned — the structured predicate detail). Each
   JSONB use justified.
4. **Two-pass verification MANDATORY** per row (A10 prime directive). `divergent_flagged` → halt.
5. **Idempotency = the L1 pattern.** Per-chart delete-then-insert scoped to (chart_id × the natural key),
   via a shared helper mirroring `ga_writers/_idempotency.py`. Rebuild REPLACES, never accretes.
   ([[feedback-idempotency-pattern-per-layer]]) NOT the L0 ON-CONFLICT style.
6. **No JH-parity oracle.** Verification is internal-consistency + classical-rule re-derivation +
   FORENSIC grounding. ([[feedback-no-jh-parity-anywhere]])
7. **No audience tier.** ([[feedback-no-audience-tier]])
8. **Floors aspirational, not gates.** A10 says ~4,000–6,250 signals/chart — chase genuine deterministic
   firings; set target_floor = achieved count after build (the L1 lesson); never fabricate to hit a number.
   ([[feedback-floors-are-aspirational-not-gates]])
9. **Cockpit truth.** Each bo_ asset needs a correct chart-scoped `count_sql` on `asset_registry` (the
   stats route reads count_sql from asset_registry, NOT asset_throughput — the L1 trap), and target_floor
   set = achieved count so the bar fills. (The 8 placeholders already have count_sql — verify they match
   the real tables the writers write.)
10. **PyJHora engine, Postgres-direct, surgical migrations** (never deploy.yml-auto / bulk migrate.ts —
    both are silent-failure traps [[feedback-deploy-migrations-silent-noop]] [[feedback-migrate-runner-untracked-legacy]]).

## §5 — Orchestrator conformance (the FROZEN contract — Bodha onboards, does NOT extend)

The orchestrator was built once and FROZEN (ORCHESTRATOR_CONVERGENCE_CLOSE). **Every Bodha writer onboards
by conforming — no orchestrator code changes.** Each bo_ writer:
- is a `@register('bo_<id>')` `WriterBase` subclass in the orchestrator's writer package;
- implements `run(ctx) -> WriterResult` (light) OR `plan_substeps(ctx)` + `run_substep(ctx, step)` (heavy —
  e.g. `bo_laksana` MSR may be heavy: per-ayanamsha or per-signal-class sub-steps);
- runs on **`ctx.db_conn` and NEVER commits/closes** (orchestrator owns the txn + savepoint per sub-step);
- does NOT write `asset_throughput` itself (orchestrator is the sole build-state writer — no `_telemetry`);
- owns its idempotency on `ctx.db_conn` scoped per sub-step key;
- gets `chart_id` + `birth_params` from `ctx.config`.
- **If a Bodha writer seems to need a contract change → STOP and raise with the native.** The freeze is
  deliberate. (It should NOT need one — MSR/CDLM/CGM are per-chart computed writers, exactly what the
  contract was generalized for.)
The conformance checklist is ORCHESTRATOR_CONVERGENCE_CLOSE §5 — **embed it verbatim in every bo_ brief.**
Result: when a user clicks Build, the orchestrator runs Bodha in dependency order automatically — same as L1.

## §6 — The TRAPS Bodha MUST avoid (hard-won; read the audits)

These are real failures already documented — do not repeat them:

1. **Computed-value drift / authority inversion (MSR_COMPUTED_VALUE_DRIFT_HANDOFF).** The worst one: an
   MSR signal can carry a stale or wrong computed value that CONTRADICTS the canonical L1 fact (the audit
   found a Muntha signal asserting the wrong sign vs FORENSIC's Libra-7H-Venus). Root cause: *retrievability
   was treated as authority*; there was no rule that L1 facts WIN over L2.5 derivations on conflict. **Rule
   for Bodha: L1 is the authority. An MSR signal NEVER restates an L1 computed value as its own truth — it
   REFERENCES the fact_id and inherits L1's value. If a signal's derivation disagrees with the L1 fact it
   cites, that's a halt-worthy bug, not a stored divergence.** The GA-Tajaka build already proved this works
   (Muntha = Libra/7H/Venus FORENSIC-exact) — Bodha must preserve it, not re-derive over it.
2. **Interpretation-contamination of the deterministic base (MSR_UCN_CONTAMINATION_AUDIT).** A prior MSR/UCN
   build let authoring JUDGMENT leak into what should be a purely computed base (signal selection, strength
   shading). **Rule: signal firing + salience are formula-driven and reproducible (salience_formula_v1, a
   versioned deterministic formula). No human/LLM judgment in which signals fire or how strong they are.**
3. **Strength-as-gate (Contamination C2).** Do NOT drop weak signals — `no threshold drop`. Strength is a
   COLUMN, not a filter. Emit every firing; let serve-time rank. (A10 prime directive.)
4. **Epistemic tiering (inherited from L1 GA-Tajaka).** L1 facts come in two tiers: FORENSIC-exact hard
   facts (positions, Muntha, the 7 anchors) vs documented-approximations (Tajik-yoga classifier,
   Pañcavargīya scoring — no JH-parity oracle exists). **Bodha must carry this tier through into MSR's
   `verification_certainty`** — a signal built on a hard fact is higher-certainty than one built on a
   documented approximation. Don't flatten the two.
5. **Citation/grounding (MSR_CITATION_SCAFFOLDS, V1_3 CF.V13.1).** Every signal carries `classical_sources`
   + `constituent_facts_array` — grounded, not "as is known classically." 50 citation scaffolds already exist;
   build on them.

## §7 — How Bodha gets built (same campaign shape as L1 — proven)

1. **Master campaign** (like L1_GANITA_BUILD_CAMPAIGN): governing principles, the 8-asset DAG, Phase-0
   prereqs (create the `bodha_*` tables + the `l25_*`/table-name reconciliation + flip the 8 bo_ rows
   DRAFT→CURRENT + confirm count_sql/target_floor scaffolding), agent gate-validators.
2. **Per-asset execution briefs** — one per bo_ asset, fully detailed (every signal class/predicate, exact
   source facts, two-pass method, FORENSIC/L1-authority assertions, atomic grain, idempotency, the §5
   conformance checklist embedded). Author in batches (bo_laksana first — it's the root and the biggest;
   then the fan-out; then bo_upaya + bo_pramana_mapa).
3. **Build via the orchestrator** — NOT a hand-run sidecar script. Bodha is the first layer built
   orchestrator-native from day one: `POST /api/cockpit/runs scope=layer/bodha` for the chart. The whole
   point of the L1 convergence arc was so L2 never hand-builds.
4. **Cockpit-verify** — bars fill, tiles lit, counts true, all via the orchestrator path.
5. **Seal** — L2_BODHA_CLOSE with the validated state + the L3 Kāla onboarding contract (L3 reads L2 the
   same way L2 reads L1).

## §8 — Open reconciliations to resolve at L2 open (don't let these surprise mid-build)

1. **Table naming:** A10–A14 specs say `l25_msr_signals` / `l25_cdlm_cells` / `l25_cgm_*` / `l25_rm_*` /
   `l25_ucn_*`; the seed placeholders say `bodha_signals` / `bodha_graph` / etc. Pick the canonical names,
   make spec + seed + writer + count_sql agree, BEFORE writing. (The L1 ganita_dashas-vs-chart_dashas
   ambiguity cost a halt — settle this first.)
2. **UCN → UCD:** A14 is "UCN RETIRED → UCD" — confirm what `bo_samvada` (UCN resonance) actually builds
   (the resonance/UCD digest), not the retired UCN.
3. **G52 signal_type_registry** — ELIMINATED 2026-06-16 (native directive). No build task, no seed, no dependency. `bo_laksana` uses projection model; `signal_type_id` derived from class/tradition. See A10 v1.3 §5.
4. **The l25_* tables** were created-but-empty by the L1 GA3 migration (A3 §7) — confirm their DDL matches
   the A10–A14 schemas, or author corrective migrations.
5. **Phase 5 E2E + Abhinandan** — confirm L1's orchestrator-native build is proven on a non-native chart
   before L2 rides the same machinery (the E2E in flight at this handoff's authoring).

---

*End of L2 Bodha handoff v1.0. Bodha is the synthesis layer — deterministic structural signals over L1
facts, built orchestrator-native, under the same standards L0/L1 proved, avoiding the documented
computed-value-drift and contamination traps. L1 is the authority; Bodha references, never re-derives over it.*
