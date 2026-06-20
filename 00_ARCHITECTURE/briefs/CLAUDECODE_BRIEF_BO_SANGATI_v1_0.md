---
artifact: CLAUDECODE_BRIEF_BO_SANGATI_v1_0.md
canonical_id: BO_SANGATI_BRIEF
version: 1.1
status: FOR_NATIVE_REVIEW (Batch 2 — CDLM; the FIRST true weight-of-evidence asset)
authored_by: Cowork (grounded in live CDLM schema + judgment strategy) 2026-06-19
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
v1_1_changes: >
  CDLM supreme-elevation (native 2026-06-19). CDLM's purpose is elevated from a domain-pair matrix to a MAP OF
  THE LIFE'S INTERLOCKED DYNAMICS. Five additions (§SUPREME): C1 typed/directional/mechanistic links; C2 central
  tensions+synergies as first-class (cross-domain signature_tier); C3 common-cause/pivot analysis (the one root
  factor explaining multiple domains); C4 domain-network propagation/ripple (consequence chains across life
  areas); C5 FULL judgment parity on links (each link gets its own confidence + weight-of-evidence + wildcard guard).
scope: bo_sangati ONLY — CDLM: cross-domain linkage cells + domain rollups + chart summary + pattern clusters + evolution gradients + bodha_convergence + THE DOMAIN EVIDENCE LEDGERS (Move 1). Depends on bo_laksana.
data_plane: ALWAYS prod via Cloud SQL Auth Proxy (127.0.0.1:5433)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
governing:
  - L2_BODHA_JUDGMENT_SUBSTRATE_STRATEGY_v1_0.md (v1.1 FROZEN — Move 1 weight-of-evidence is THIS asset's core)
  - L2_BODHA_SCHEMA_REDESIGN_v1_0.md + L2_BODHA_STORAGE_ARCHITECTURE_v1_0.md + A11_CDLM_SPEC_v1_0.md
  - formulas.py: linkage_formula_v1 (present) + convergence_formula_v1 (present) + evidence_ledger_formula_v1 (NEW — author)
  - ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 (FROZEN WriterBase)
target_files:
  - platform/python-sidecar/pipeline/orchestrator/writers/bo_sangati.py
  - platform/python-sidecar/bodha_writers/formulas.py (ADD evidence_ledger_formula_v1)
  - migration(s): the 6 CDLM tables + bodha_convergence + the evidence-ledger columns (empty — redefine freely)
  - platform/src/lib/retrieval/registry/layers/L2_bodha/ (CDLM + evidence-ledger retrieval tools)
must_not_touch: FROZEN orchestrator contract; ga_* writers; bo_laksana; CGM/other writers.
---

# bo_sangati — CDLM + the DOMAIN EVIDENCE LEDGERS (the weight-of-evidence core)

## §0 — What this is
CDLM (Cross-Domain Linkage Matrix) computes how the chart's life-domains relate, by aggregating MSR signals.
Under the JUDGMENT strategy, bo_sangati is ALSO the home of **Move 1 — the weight-of-evidence engine**: per
domain, the full EVIDENCE LEDGER (support / oppose / independent-weight / cross-tradition / net-verdict /
confidence / dissents). This is the asset that turns Bodha from a fact store into a judgment substrate. It is
DETERMINISTIC: every value a versioned formula over bo_laksana signals; no narrative, no LLM, no judgment leak.

## §1 — Non-negotiables
Deterministic-first; no audience tier; no silent drops; per-chart isolation; **Trap 1** (cells/ledgers REFERENCE
signal_ids + the constituent fact_ids those signals carry — never restate values); **Trap 2** (linkage_formula_v1
+ convergence_formula_v1 + evidence_ledger_formula_v1 — versioned; no narrative in the asset); FROZEN orchestrator
contract (`@register('bo_sangati')` WriterBase on ctx.db_conn, never commits, no asset_throughput); count_sql
summed across all CDLM tables; floors aspirational.

## §2 — Preconditions
1. Proxy up; main == prod; max migration verified.
2. **bo_laksana built + anti-drift spine PASSED** (CDLM aggregates MSR signals — a broken root poisons it).
3. bo_karanajala/CGM ideally built (CDLM reads bodha_contradictions + convergence paths as ledger inputs — if
   CGM not yet built, compute contradiction-from-MSR as a fallback and flag for a refresh pass once CGM lands).
4. Apply the enriched CDLM-tables migration (incl. the evidence-ledger columns, §4). Empty tables — redefine freely.

## §3 — The CDLM base (linkage matrix — keep + populate fully)
- `bodha_cdlm_cells` — the domain×domain (9×9) + sub-domain (27×27) linkage cells across snapshots (static natal
  + dynamic Maha/Antar across 3 dasha systems + per-tradition views). Populate ALL columns: shared signals,
  positive/negative contribution, net + computed linkage (linkage_formula_v1), contradiction pairs, asymmetry,
  cross-ayanamsha stability, the CGM/RM/UCN enrichment hooks.
  **NOTE (two planes):** the `dynamic_*` / `predicted_activation_dasha_windows_jsonb` columns are dasha-WINDOW
  STRUCTURE (which lord governs the snapshot), NOT the dated timeline — consistent with the L2-timeless rule.
  Do NOT compute dated activation (that's L3). Leave predicted_activation_* hooks NULL for L3.
- `bodha_cdlm_domain_rollups` — per-domain aggregation (the natural home of the evidence ledger, §4).
- `bodha_cdlm_chart_summary`, `bodha_cdlm_pattern_clusters`, `bodha_cdlm_evolution_gradients` — per spec.
- `bodha_convergence` — convergence-density-per-domain (convergence_formula_v1). **SIGNAL-COUNT layer** (see §5).

## §4 — MOVE 1: THE DOMAIN EVIDENCE LEDGER (the centerpiece — build on bodha_cdlm_domain_rollups)
For EACH domain (career, wealth, marriage, health, character, spirituality, education, progeny, … the full
classical domain set), compute a deterministic EVIDENCE LEDGER (the strategy §1.A mechanism):
1. **Gather** every MSR signal whose `domains_affected_array` contains the domain.
2. **Classify** support vs oppose by the signal's `valence` RELATIVE to the domain (benefic yoga on 10th =
   support for career; malefic affliction = oppose). Store both lists with each signal's per-domain salience.
3. **INDEPENDENCE DEDUP (load-bearing — masters don't double-count):** two signals count as INDEPENDENT evidence
   ONLY if they do NOT share constituent_fact_ids. If A and B rest on the same root L1 fact → count ONCE. Use the
   CGM `shared_substructure` (§JG.1 of the graph brief) where available. Store `independent_support_count` +
   `independent_oppose_count` + WHY each surviving signal is independent (the distinct fact_ids).
4. **Weight** by per-domain salience; compute cross-tradition agreement (how many traditions concur).
5. **VERDICT + CONFIDENCE (`evidence_ledger_formula_v1` — author it):** net = weighted-support − weighted-oppose;
   `verdict_class` ∈ {strongly_supported, leaning_supported, balanced/contested, leaning_against, strongly_against};
   `confidence` = f(margin × cross_tradition_agreement × cross_ayanamsha_stability). Store the `dissents_jsonb`
   (the specific opposing signals named) so the LLM can say "strongly favoured, BUT these two undercut it."
**Ledger columns on domain_rollups (or a `bodha_domain_evidence_ledger` table):** supporting_signal_ids[],
opposing_signal_ids[], independent_support_count, independent_oppose_count, weighted_support, weighted_oppose,
net_evidence, verdict_class, confidence, cross_tradition_agreement_count, dissents_jsonb, ledger_formula_version,
+ the epistemic fields (Move 3 — inherited from the constituent signals' epistemic_jsonb, aggregated).

## §5 — NON-REDUNDANCY: the three convergence layers (strategy §1.B — do NOT collapse)
Code-verified — these mean DIFFERENT things; the ledger CONSUMES the lower two, never recomputes:
- `ga_structural.convergence_count` (L1) = graph DEGREE (geometric). | `bodha_convergence` (this asset) =
  SIGNAL-COUNT sharing a domain. | **the evidence ledger (§4) = weighted VERDICT + confidence (judgment).**
- The ledger CITES the bodha_convergence rows + the ga_structural convergence as constituents. Geometry → counting
  → judgment. Zero duplication. **L5 does cross-CHART empirical convergence — NEVER compute that here (within-chart only).**

## §6 — Anti-drift + verification
1. Every cell's `shared_signal_ids_array` + every ledger's supporting/opposing signal_ids resolve to real
   bodha_msr_signals (Trap 1; zero unresolved).
2. **Independence dedup proven:** a ledger where two signals share a root fact_id shows independent_count < raw_count
   (the dedup actually fired) — spot-check a known shared-fact pair.
3. **Acharya check:** the verdict for a domain is astrologically coherent (e.g. a domain with strong yogas + few
   afflictions returns strongly_supported; verify against the native's known life facts where LEL has them).
4. Cross-ayanamsha stability populated; idempotent; no silent drops; FORENSIC unaffected.

## §6B — STORAGE COMPLIANCE (L2_BODHA_STORAGE_ARCHITECTURE — rules that apply to bo_sangati)
- **S5 jsonb-vs-column (CDLM is jsonb-heavy — hold the line):** `domain_row`/`domain_col`, `verdict_class`,
  `confidence`, `net_linkage_strength`, `cross_domain_contradiction_flag`, snapshot_type = real INDEXED columns
  (most already are). The ledger's verdict_class + confidence MUST be columns (the LLM filters "show contested
  domains") — never bury them in jsonb. Only variable per-cell content stays jsonb.
- **S1 recursive-traversal reuse:** the independence-dedup + the ledger's "which signals reach this domain" may
  reuse the CGM recursive-CTE traversal tool (do NOT build a second traversal engine).
- **S2 partitioning readiness:** chart_id leads every index.
- **No embeddings authored here** (bo_sangati has no vector column; embeddings are bo_samskara's job).

## §7 — Retrieval (the retrievability half)
Extend `L2_bodha/`: cell/rollup/cluster fetch tools + **the headline tool `query_domain_evidence(chart, domain)`**
returning the full ledger (verdict + confidence + ranked support + ranked oppose + named dissents + each with
provenance + citation + epistemic state). This is the single most valuable Bodha retrieval surface — it hands the
LLM the master's weighing, ready to narrate. Paginated, no cap; coverage gate extended (every CDLM table + the ledger reachable).

## §8 — Acceptance
- [ ] CDLM cells/rollups/summary/clusters/gradients + bodha_convergence populated (linkage + convergence formulas).
- [ ] **MOVE 1 ledger per domain: support/oppose classified by valence; INDEPENDENCE DEDUP fired (no double-count); verdict_class + confidence + dissents; evidence_ledger_formula_v1 versioned.**
- [ ] **Non-redundancy: ledger CITES ga_structural convergence + bodha_convergence as constituents, recomputes neither; no L5 cross-chart convergence.**
- [ ] Two-planes: dynamic = dasha STRUCTURE only; predicted_activation_* NULL for L3.
- [ ] Anti-drift: all signal refs resolve; independence dedup proven; acharya verdict coherence check.
- [ ] Retrieval: query_domain_evidence + cell/rollup tools; coverage gate green; every return carries provenance + confidence.
- [ ] **§C1:** every cell typed (linkage_type) + directional + mechanism (the causing signal/path).
- [ ] **§C2:** chart's central tensions + synergies derived as named ranked first-class rows.
- [ ] **§C3:** common-cause/pivot analysis — shared roots across domain ledgers ranked (the chart's pivot factor).
- [ ] **§C4:** domain-network propagation paths (ripple/consequence chains) via the S1 traversal; cycle-guarded.
- [ ] **§C5:** full judgment parity on links — per-link weight-of-evidence + epistemic + non_template_linkage wildcard.
- [ ] New retrieval tools: query_central_dynamics, query_chart_pivots, query_domain_propagation.
- [ ] FROZEN contract; migration fresh; summed count_sql; floors = achieved.

---

# §SUPREME — from a domain-pair matrix to a MAP OF THE LIFE'S INTERLOCKED DYNAMICS (native-confirmed 2026-06-19)
*CDLM's supreme purpose: capture how domains REINFORCE, DRAIN, DEPEND ON, and PIVOT AROUND each other — the
integrated story a master sees, not a list of independent life-areas. All deterministic; anti-drift-clean; no
pre-answering. Unifying arc: signal-significance (bo_laksana) → domain-verdict (ledger §4) → INTERLOCKED-STORY (here).*

## §C1 — TYPED, DIRECTIONAL, MECHANISTIC links (not just net_linkage_strength scalar)
Each `bodha_cdlm_cells` row gains: `linkage_type` ∈ {reinforcing, draining, conditional, antagonistic,
common_cause} + `direction` (A→B / B→A / mutual) + `linkage_mechanism_jsonb` (the shared signal_ids / CGM
node-or-path that CAUSES the link). Deterministic: reinforcing = shared benefic support; draining = one domain's
malefic bleeds into another; antagonistic = opposing valence on a shared factor (e.g. spirituality↔wealth
renunciation tension); conditional = a directional dependency via a lord/dispositor; common_cause = shared root
(feeds §C3). Turns "career—wealth: 0.7" into "career FEEDS wealth, via the 10th-lord's strength flowing to the 2nd."

## §C2 — CENTRAL TENSIONS + SYNERGIES as first-class (the cross-domain signature_tier)
Derive the chart's 2–3 DEFINING cross-domain dynamics: the strongest REINFORCING cluster + the strongest
ANTAGONISTIC axis, as named, ranked rows (new `bodha_cdlm_central_dynamics` table or rollup rows). Computed from
the typed links (§C1) ranked by combined linkage strength × salience × cross-ayanamsha stability. So the LLM
LEADS with the life's central dynamic ("fundamentally a chart where public success and private peace are at war").

## §C3 — COMMON-CAUSE / PIVOT analysis (the single highest-value cross-domain insight; nothing computes it today)
Find DETERMINISTICALLY the L1 facts/nodes that are CONSTITUENTS of MULTIPLE domains' evidence ledgers (§4) — the
chart's PIVOT ("the one afflicted Venus explaining career + wealth + marriage"). Mechanism: intersect the
`constituent_fact_ids` / signal_ids across all domain ledgers; rank each shared root by (domains_touched ×
summed per-domain salience). Store `bodha_cdlm_pivots` (or pivot rows): root_fact_id/node, domains_touched_array,
pivot_strength, the ledgers it feeds. This is "the one thing that explains the most about this life." References
the roots (Trap 1) — never restates them.

## §C4 — DOMAIN-NETWORK PROPAGATION / RIPPLE (consequence chains across life areas)
Treat the domain matrix as a GRAPH (domains = nodes, typed links §C1 = edges). Compute PROPAGATION paths — how a
strength/affliction in one domain ripples to others through the shared-factor links (domain-level analog of the
CGM dispositor chains; REUSE the recursive-CTE traversal, storage S1). Store `bodha_cdlm_propagation` (ordered
domain path + the link mechanism per hop + cumulative strength). Lets the LLM narrate "this one weakness cascades
into these three life problems." Cycle-guarded; depth bounded by the domain network.

## §C5 — FULL JUDGMENT PARITY ON LINKS (every link gets the Move 1/3/5 treatment)
A cross-domain LINK is itself a claim that can be supported, contested, confident, or fragile — give links the
same judgment treatment signals + domains get:
- **Move 1 (weight-of-evidence per link):** each link carries its OWN support/oppose — some signals say career
  HELPS wealth, some say it COMPETES; store `link_support_ids` / `link_oppose_ids` + a link verdict + confidence.
- **Move 3 (epistemic honesty per link):** structured `link_epistemic_jsonb` — is "career feeds wealth" robust
  5/5 ayanamshas or fragile 2/5? tradition-agreement on the linkage. (Elevate `cross_ayanamsha_cell_stability_score`.)
- **Move 5 (anti-tunnel-vision):** a far-from-template but REAL domain COUPLING (an unexpected link) must surface,
  flagged `non_template_linkage` — via the CGM graph-sweep, not a template. Never lost.

---

# §ELEVATION (beyond base; toward supreme)
- **S-1 [judgment] Per-(domain × dasha-lord) ledger STRUCTURE** — not the dated timeline (that's L3), but "which
  domains does each dasha-LORD structurally govern" — so L3 can later activate the right ledger. Structure only.
- **S-2 [depth] Sub-domain ledgers** (27×27) — career→{profession, status, authority, public-image} so the LLM
  can answer at the granularity a master would.
- **S-3 [retrievability] Ledger DIFF across ayanamshas** — surface where a verdict is ayanamsha-stable vs fragile
  (feeds Move 3 epistemic honesty at the verdict level).
- **S-4 [judgment] "Evidence tension" surface** — domains where support AND oppose are both strong (genuinely
  contested life areas) flagged distinctly from clearly-resolved ones — the master's "this is complicated."
- **S-5 [completeness] Coverage manifest** — every domain has a ledger; every MSR signal lands in ≥1 domain's
  support/oppose (no signal orphaned from the evidence structure).

---
*End of BO_SANGATI v1.0. CDLM linkage matrix + the DOMAIN EVIDENCE LEDGERS — the weight-of-evidence engine
(Move 1): per domain, support/oppose classified by valence, INDEPENDENCE-DEDUP'd (no double-counting), weighted,
verdict + confidence + named dissents, all deterministic + versioned. Strictly LAYERED over the geometric (L1)
and signal-count (bodha_convergence) convergence — consumes, never duplicates; no L5 cross-chart. The
query_domain_evidence tool hands the LLM the master's weighing. This is where Bodha becomes a judgment substrate.*
