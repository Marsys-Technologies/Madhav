---
artifact: CLAUDECODE_BRIEF_BO_DRISHTI_v1_0.md
canonical_id: BO_DRISHTI_BRIEF
version: 1.0
status: FOR_NATIVE_REVIEW (Batch 3 — the QUESTION-LENS asset; NEW, not in migration 226)
authored_by: Cowork (grounded in judgment strategy + CDLM ledgers/pivots) 2026-06-19
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
scope: bo_drishti ONLY — the question-lens asset (Move 5). Pre-computes deterministic classical LENSES (question-type → the chart-specific elements + evidence that bear on it) so retrieval is answer-FOCUSED. Depends on bo_laksana + bo_sangati (ledgers/pivots/central-dynamics) + bo_karanajala (the graph safety-net).
data_plane: ALWAYS prod via Cloud SQL Auth Proxy (127.0.0.1:5433)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
governing:
  - L2_BODHA_JUDGMENT_SUBSTRATE_STRATEGY_v1_0.md (v1.1 FROZEN — Move 5 §5 + the anti-tunnel-vision guard §5.A — THIS asset's spine)
  - L2_BODHA_STORAGE_ARCHITECTURE_v1_0.md (§STORAGE) + L2_BODHA_SCHEMA_REDESIGN_v1_0.md
  - ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 (FROZEN WriterBase)
target_files:
  - platform/python-sidecar/pipeline/orchestrator/writers/bo_drishti.py (NEW writer)
  - new migration: CREATE bodha_question_lenses (+ any lens-element table) + asset_registry seed row for bo_drishti
  - platform/src/lib/retrieval/registry/layers/L2_bodha/ (the lens retrieval tools)
must_not_touch: FROZEN orchestrator contract; ga_* writers; the other bo_* writers.
---

# bo_drishti — the QUESTION-LENS (answer-focused retrieval without pre-answering)

## §0 — What this is + WHY it is L2 data (not a retrieval-layer concern)
A master, asked about career, instantly knows WHICH houses, lords, karakas, yogas, divisional charts, and
evidence bear on it. bo_drishti pre-computes that mapping — **question-type → the chart-specific structural
elements + the evidence ledger that bear on it** — so the LLM retrieves an answer-FOCUSED bundle in one call
instead of scanning everything. It is L2 DATA because "which elements bear on career" is a deterministic CLASSICAL
fact about THIS chart (chart-specific structure) — building it in the retrieval layer would recompute chart
structure outside the data layer, violating "facts live in the data layer."

**THE TWO ABSOLUTE GUARDS (this asset lives or dies by them):**
1. **A lens POINTS, never PRE-ANSWERS.** It assembles "here are the career-relevant elements + the career
   evidence ledger"; it does NOT store "the native will have a good career." Pointing vs concluding. Preserves
   the "ingredients not pre-answered questions" philosophy.
2. **A lens is ADDITIVE, never SUBTRACTIVE (the anti-tunnel-vision guard, strategy §5.A).** It must NEVER lose a
   far-from-template-but-significant signal. See §3 — this is the hardest and most important requirement.

## §1 — Non-negotiables
Deterministic-first (no LLM — the lens is a deterministic assembly); no audience tier; no silent drops; per-chart
isolation; **Trap 1** (the lens REFERENCES element ids / signal ids / ledger ids — never restates values or
conclusions); **Trap 2** (no narrative, no judgment — it points to the ledgers/evidence, the LLM narrates at
serve-time); FROZEN orchestrator contract (`@register('bo_drishti')` WriterBase on ctx.db_conn, never commits, no
asset_throughput); floors aspirational.

## §2 — Preconditions
1. Proxy up; main == prod; max migration verified.
2. **bo_laksana + bo_sangati built** (the lens points at signals, ledgers, pivots, central-dynamics — they must exist).
3. **bo_karanajala/CGM built** (the safety-net graph-sweep, §3, needs the graph + its recursive-traversal tool).
4. Apply the NEW bodha_question_lenses migration + the bo_drishti asset_registry seed row (depends_on
   [bo_laksana, bo_sangati, bo_karanajala]). New asset — author the schema (§4).

## §3 — THE ANTI-TUNNEL-VISION DESIGN (the defining requirement — strategy §5.A)
Every lens returns TWO parts, always:
**(a) THE TEMPLATE SET** — the deterministic classical elements for the question-type. E.g. career-lens template =
{10th house + its lord + D10 + Saturn & Sun karakas + the career-relevant yogas + the CAREER evidence ledger
(bo_sangati §4) + career pivots (CDLM §C3) + career central-dynamics (CDLM §C2)}. Defined per question-type from
classical rules (a `lens_template` config: question_type → element selectors). Fast, organized, the obvious.
**(b) THE MANDATORY WILDCARD SWEEP** — `non_template_significant` elements. Using the CGM graph-sweep
(bo_karanajala §JG.2 / the S1 recursive traversal): find EVERY high-salience / high-impact signal that REACHES
the question's significators (e.g. the 10th-lord node + career karakas) by ANY relationship path — EVEN one the
template never anticipated. A signal high in salience but low in template-fit is INCLUDED and FLAGGED
`non_template_significant = true`, so the LLM LEADS with "the textbook says X, but the unusual thing in YOUR chart
is Y." **The graph is the safety net; the template is the convenience.**
**THREE HARD RULES:**
- The lens **RANKS, never CAPS** — returns EVERYTHING bearing on the question, ranked, template-marked,
  outliers-flagged — never "top N." The weak tail + far-from-mean are ALWAYS reachable (no-drop pillar).
- The wildcard sweep is **NOT optional** — a lens that returns only its template FAILS acceptance.
- An outlier is **highlighted, not buried** — `non_template_significant` is a retrieval facet the LLM can lead with.

## §4 — Schema: bodha_question_lenses (author it)
Per (chart, ayanamsha, question_type):
- `lens_id`, `chart_id`, `ayanamsha_id`, `build_id`, `question_type` (career/wealth/marriage/health/character/
  spirituality/education/progeny/longevity/… the full classical domain set + sub-types).
- `template_element_ids_jsonb` — the template set: {houses[], lords[], vargas[], karakas[], yoga_signal_ids[],
  ledger_id, pivot_ids[], central_dynamic_ids[]} — all as REFERENCES (Trap 1).
- `wildcard_element_ids_jsonb` — the non-template significant signals found by the graph-sweep, each with
  {signal_id, salience, reach_path_id (how it reaches the significators), non_template_significant: true}.
- `all_relevant_ranked_jsonb` — the full ranked union (template ∪ wildcard), the no-cap complete set.
- `lens_template_version` (the versioned selector config) + `lens_formula_version`.
- `points_only_assertion` — a structural guarantee column: the lens stores NO verdict/conclusion (audited by bo_pramana_mapa).
- provenance: verification_pass_status, citation_ref/human, computed_at, engine_version.
**S5 storage:** question_type, lens_id, chart_id = real indexed columns; the element sets are jsonb (variable). chart_id leads indexes (S2).

## §5 — Anti-drift + verification
1. Every element id in template + wildcard resolves to a real signal/ledger/pivot/node (Trap 1; zero unresolved).
2. **Wildcard fired:** for a question where a known significant signal is OUTSIDE the template, confirm it appears
   in `wildcard_element_ids` flagged non_template_significant (the safety net actually works — test with a deliberately off-template high-salience signal).
3. **No pre-answer:** assert the lens row stores NO verdict/conclusion text (points_only).
4. **No cap:** all_relevant_ranked includes the weak tail (a low-salience but career-touching signal is present).
5. Idempotent; no silent drops; FORENSIC unaffected.

## §6 — Retrieval (the payoff)
`query_lens(chart, question_type)` → returns the focused bundle: template set (fast, organized) + wildcard
outliers (flagged) + the full ranked set (complete), each element resolvable to its signal/ledger/pivot with full
provenance + confidence + epistemic state. This is the LLM's ORIENTATION call — it pulls the career lens in one
targeted retrieval instead of scanning everything, AND it cannot miss the significant outlier. Coverage gate:
every question_type has a lens; the wildcard-sweep is exercised in the gate.

## §7 — Acceptance
- [ ] bodha_question_lenses populated for every question_type (full classical domain set + sub-types).
- [ ] **Template set** assembled from classical selectors (houses/lords/vargas/karakas/yogas/ledger/pivots/central-dynamics), all as references.
- [ ] **MANDATORY wildcard sweep** via the CGM graph-sweep — non-template significant signals included + flagged; a lens returning only its template FAILS.
- [ ] **RANKS never CAPS** — full ranked union present; weak tail reachable.
- [ ] **POINTS never PRE-ANSWERS** — points_only guarantee; zero verdict/conclusion stored (audited).
- [ ] Anti-drift: all element refs resolve; wildcard-fired test passes.
- [ ] query_lens tool + coverage gate; storage compliance (S5/S2/S1 reuse); FROZEN contract; migration + seed fresh.

---

# §ELEVATION (toward supreme)
- **D-1 [judgment] Lens carries the question's CENTRAL VERDICT POINTER** — not the verdict (no pre-answer), but a
  pointer to the domain ledger's verdict_class + confidence, so the LLM's first read is "career: strongly-supported
  (0.8 conf), but see these dissents + this outlier." Pointing to the master's weighing, instantly.
- **D-2 [retrievability] Cross-question lenses** — composite question-types ("career + marriage timing-readiness
  structure", "health affecting wealth") that point at MULTIPLE ledgers + the propagation paths (CDLM §C4) between them.
- **D-3 [completeness] Sub-question lenses** — career → {profession, authority, public-image, job-vs-business} so
  the LLM answers at a master's granularity.
- **D-4 [judgment] Lens epistemic surface** — flag where a question's answer is ayanamsha-fragile or classically
  contested (inherits Move 3 from the ledger), so the LLM caveats appropriately.
- **D-5 [retrievability] "What am I missing" lens** — a meta-lens per question that returns ONLY the
  non_template_significant outliers across all domains — the master's "the unusual things in this chart" surface.

---
*End of BO_DRISHTI v1.0. The question-lens: pre-computed deterministic classical lenses (question-type → the
chart-specific elements + evidence that bear on it) so retrieval is answer-FOCUSED. The two absolute guards: a
lens POINTS never PRE-ANSWERS, and is ADDITIVE never SUBTRACTIVE — the mandatory CGM graph-sweep wildcard +
ranks-never-caps + outlier-flagging guarantee the significant far-from-template signal is NEVER lost. The template
is the convenience; the graph is the safety net. The LLM gets the obvious fast AND can never miss the unexpected-
but-significant. ELEVATION adds verdict-pointers, cross/sub-question lenses, epistemic caveats, and a "what am I
missing" surface.*
