---
canonical_id: RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN
version: 1.6
status: FINALIZED-FOR-IMPLEMENTATION (pending native ratification; execution slot R5, after the native rebuild)
created: 2026-07-07
changelog:
  - v1.6 (2026-07-08): ADVERSARIAL REVIEW + EXTERNAL CURRENCY (native-directed step-back critique).
    Added Part VII: §31 substance gaps found by the critique (tool-list context tax, tool-selection
    ergonomics, session-pin collision, BIRTH-TIME SENSITIVITY honesty — the major astrological
    addition, build_id provenance, retrieval telemetry loop), §32 MCP-spec currency (2026-07-28 RC:
    Tasks extension, elicitation, stateless core; 2025-06 output schemas — adoption plan per item),
    §33 convergence check vs Anthropic tool-design guidance. Run-mechanics critiques applied to
    CLAUDECODE_BRIEF_R5_RETRIEVAL_3_0_AUTONOMOUS_RUN (v1.1) — W0 split, strangler codegen, format
    negotiation, frozen pre-authored battery, authority dossier, conformance attestations, rollback
    rehearsal, burn budget.
  - v1.5 (2026-07-07): THE ASTROLOGY PILLAR (native-directed, the governing one) — full review of the
    design against how Jyotish itself reasons. Added Part VI: §26 the acharya-protocol review (where
    the design was database-shaped), §27 the astrological address system (universal `about` facet +
    address resolver + reference frames + paradigm facet), §28 shastra-shaped navigation (bhava-judgment
    recipe, graha portrait, the PACT chain as the predictive investigation protocol, astrologically
    typed drill_pointers, the shastra map on the capabilities card), §29 the re-architecture verdict
    (entity-regroup considered and rejected with reasons; the overlay adopted), §30 wave absorption +
    astrological acceptance criteria. The instrument now navigates in the shastra's own coordinates.
  - v1.4 (2026-07-07): PERFORMANCE PILLAR (native-directed) — end-to-end latency investigated with a
    full code-path trace (hop counts per tool class, measured p50 baselines, 8 ranked latency sinks
    with file:line + fix class). Added Part V: §22 the latency equation (call count × LLM turn is the
    dominant term), §23 ranked sinks + fix program in three tiers, §24 E-8 timing telemetry + SLOs,
    §25 wave absorption + one security flag surfaced by the trace. Perf targets are now acceptance
    gates alongside token targets.
  - v1.3 (2026-07-07): PRE-IMPLEMENTATION CODE AUDIT (native-directed) — two exhaustive repo sweeps
    verified every §1–§16 premise against implementation reality. Added Part IV: §18 premise-verdict
    table (what's confirmed / different / missing, with file:line), §19 the structural finding
    (two-process contract seam → single-source generation mandate), §20 punch-list root causes (every
    audit failure now has an exact file+line fix), §21 finalization deltas to the wave plan. Brief is
    now implementation-grade: no wave brief may contradict §18.
  - v1.2 (2026-07-07): LIVE EMPIRICAL AUDIT (native-directed) — Cowork ran the §9 battery as the actual
    endpoint LLM against the live MCP (8 probes, native chart). Added Part III: §14 probe-by-probe
    findings (6 of 8 failed or degraded), §15 findings triage (R4-heals / serving-bug punch-list /
    3.0-design), §16 the new design elevations the audit forced (serving-health canary, provenance
    freshness contract, served-aggregate consistency invariants, absence framing, temporal facet
    mandate). The design's premises are no longer hypothetical — every Part II clause now has a live
    failure as its evidence.
  - v1.1 (2026-07-07): WORKED-BACKWARDS PASS from the endpoint synthesis LLM (native-directed). Added
    §9 answer taxonomy (the 9 response types the user actually receives), §10 the endpoint-LLM
    requirements ("bill of needs" — frame safety, epistemic vocabulary, negative knowledge, now-context,
    coverage receipts, session stability, inline citations, response-ready values), §11 answer surfaces
    (first-call scaffolds per response type), §12 data-plane additions, §13 eval reorientation (score
    ANSWERS, not retrievals). §§0–8 unchanged. Grounded in a live endpoint failure (the D1-chart
    misread) — §10.1 exists because of it.
author: Cowork (Beyond-Acharya program) — native-directed elevation, sitting 2026-07-07
program: successor to RETRIEVAL_MODERNIZATION_MASTER_PLAN_v1_0.md (P0–P2 waves absorbed as-built);
  execution slot = R5 of BA_PHASE4_RUNWAY_PLAN (after the native rebuild closes)
supersedes-in-thought: the rejected three-plane Composer architecture AND the rejected semantic-view
  plane. NO new layers, NO new planes: the four stations stay exactly as they are —
  data plane → retrieval tools → MCP → agentic LLM. All intelligence upgrades land INSIDE the tools'
  request contracts and response shapes.
native_rulings_encoded: composer redundant with agentic loop (2026-07-06) · no semantic-view plane
  (2026-07-06) · tools must be flexible targeted↔broad, LLM declares question type (2026-07-06) ·
  effort proportional to question; recursive relevant-data pulls for broad questions; token-efficiency
  first-class (2026-07-07)
---

# RETRIEVAL 3.0 — FACETED INSTRUMENTS
## One contract, three idioms, three regimes: proportionate, recursive, token-priced

---

## §0 — The governing doctrine: PROPORTIONALITY

**The cost of a retrieval — tokens, calls, latency — must be proportionate to the question.**

A definitive fact question ("what is the lagna?") is answered by ONE surgical pull of exactly the
fields asked, from the SQL store, in ≤2 KB. A broad interpretive question ("strengths and weaknesses
per the rashi chart?") legitimately mobilizes a large volume — but through a DISCIPLINED RECURSIVE
process (orient → fan-out → drill → tail-check → synthesize), never through a dump. The agentic LLM
reasons between pulls and decides each next pull from what the last one showed. The tools' job is to
make every pull exactly as small as the step needs and to hand the LLM the *map* to the next step
(drill_pointers), not the territory.

Anti-doctrine (what 3.0 kills): dump-with-filters projections · 63 KB answers to 40-byte questions ·
EAV serialization inflation (~60×) · 5-ayanamsha multiplication by default · payloads instead of
pointers · one-size responses regardless of question type.

---

## §1 — THE DATA REALITY (what the tools sit on — the design is derived from this, not imposed on it)

| Store shape | Assets (examples) | Scale reality | Native access idiom |
|---|---|---|---|
| **EAV relational** | chart_facts (L1) | ~27.5k rows/chart × 5 ayanamshas; one astrological "row" (a graha's position) = ~15 EAV rows | Pivot INSIDE the tool (SQL crosstab), project fields, default ONE ayanamsha |
| **Wide relational** | chart_divisionals, ga_strength, ga_condition, kala_* windows, phala_anchors, mimamsa_* | 10²–10⁴ rows/chart | select + where predicate pushdown; time-window predicates MANDATORY on temporal tables |
| **Massive temporal** | chart_dashas | ~536k rows/chart (multi-system, 5 levels) | NEVER unwindowed: (system, level-cap, date-range) required; defaults = vimshottari, 3 levels, ±5y |
| **Ranked signal store** | bodha_msr signals | ~13k/chart/ayanamsha (~65k total) | rank_by + top_k + domain/class facets; salience a column never a filter; tail reachable by explicit facet |
| **Graph** | CGM nodes/edges/paths (bodha_cgm_*) | 10³ nodes, 10⁴ typed edges/chart | TRAVERSAL grammar (seeds, edge types, direction, depth, valence, path patterns) — not row grammar |
| **Registers** | bodha_pratijna (promise), contradictions, triangulation, discoveries | 10²/chart | small; pivoted whole-register pulls are fine |
| **Global corpus** | L0: classical_text_chunks, brahma_yoga_catalog, bg_rules, ontologies, priors, constants | global, no chart_id | semantic/hybrid SEARCH idiom (vector + keyword + citation-id lookup) |
| **User-authored** | life_events (post-BA-LEL: per-chart) | 0–10²/chart | chart-scoped rows; availability-honest (empty-with-reason) |
| **Multi-chart** | charts (native + Abhinandan + Arunima + Kiran + growing) | every per-chart pull entitlement-gated; session chart anchor resolves "my" | chart_id from session nav; cross-chart NEVER implicit |

Three consequences fall straight out of this table:
1. **One grammar cannot have one implementation.** Relational, graph, and corpus stores each get the
   grammar in their own idiom (§3).
2. **The defaults do the token work.** Default ayanamsha (not 5), default pivot (not EAV), default
   window (not 536k rows), default top-K (not 13k signals). Explicit facets unlock everything.
3. **Availability-honesty is part of the contract.** Empty ≠ error ≠ ungranted; every empty result
   says WHY (no rows / out of window / structural-mode / not entitled) — an agent that can't
   distinguish these makes wrong fallbacks.

## §2 — THE UNIFORM REQUEST CONTRACT (every instrument implements it; no new plane anywhere)

```
{
  chart:    <id | session-default>,          // entitlement-gated
  intent:   fact | interpretation | prophecy | intervention,   // LLM declares question type
  regime:   surgical | composed | investigation,               // LLM declares effort class (§4)
  select:   [fields...],                     // projection — the 63KB killer
  where:    {typed predicates},              // pushdown: entity, varga, dignity, domain, class,
                                             //   date-window, magnitude, salience-band, ...
  shape:    pivoted | rows | summary | count | distribution,
  rank_by:  <ranking spec> + top_k,          // where ranking applies (signals, remedies, anchors)
  expand:   [bounded within-domain joins],   // e.g. positions+dignity+strength in ONE call
  depth:    <graph traversal / drill depth>,
  budget:   {max_tokens: n},                 // the tool TRIMS to budget and says what it trimmed
  ayanamsha: lahiri (default) | [...]        // multiplicity only on request
}
```

**Intent sets the defaults; facets override them.** `fact` → pivoted, glance-budget, no ranking.
`interpretation` → ranked + citations + dissent/contradictions included. `prophecy` → activation state
+ windows + posteriors joined. `intervention` → resonance-ranked remedies + cost tiers + mitigation
map. Targeted-vs-broad is therefore the SAME tool with different declared intent — the intelligence
stays in the loop, the flexibility lives in the contract.

**Response contract (every instrument):** the served envelope (grounding, ranking_basis,
judgment_flags — unchanged) PLUS: `drill_pointers` = typed, ready-to-fire next requests ("847 more in
tail → this exact call"; "contradiction C-12 both sides → this call"; "graph hub Saturn 7 edges →
this traversal") · `trim_report` when budget clipped · availability-honest empties. **Token-efficient
wire format:** columnar arrays with a single header row (never key-repeated JSON objects), enums not
strings, degrees to 2dp — this alone reverses most of the 60× EAV inflation.

## §3 — THREE IDIOMS OF THE ONE GRAMMAR

**SQL idiom (L1/L3/L4/L5 relational + registers):** facets compile to parameterized SQL inside the
existing handlers — projection, WHERE pushdown, GROUP BY for shape=summary/count/distribution, crosstab
for shape=pivoted. Postgres does the work it was built for. (The P2 injection rule stands: facet→SQL
compilation is whitelisted-field mapping, never string interpolation.)

**Graph idiom (CGM):** traversal facets — `seeds` (entities/nodes), `edge_types`
(dispositor|aspect|argala|parivartana|yoga-membership|karaka-role|nakshatra-lord), `direction`, `depth`,
`valence`, `min_strength`, and `path_pattern` ("all paths 10th-lord → Moon ≤3 hops via
dispositor|aspect"). Responses are edge-lists/paths with strengths — the astrologically potent
questions ("how does the wealth axis feed the career axis?") become one traversal call instead of
twenty row pulls.

**Corpus idiom (L0 + embeddings):** `query_text` + `k` + filters (text, tradition, yoga-id, rule-class)
+ hybrid keyword/vector + rerank. ref_vector_search graduates from near-unused to the standard way
interpretation-intent calls attach classical attestation.

## §4 — THE THREE REGIMES (proportionality made mechanical)

| Regime | Question class | Protocol | Budget envelope |
|---|---|---|---|
| **SURGICAL** | definitive fact (Q1): "lagna?", "current dasha?", "Jupiter varga positions?" | ONE call: select+where+pivot on the owning SQL surface | ≤2 KB, 1 call |
| **COMPOSED** | bounded interpretation (Q2 narrow): "how is my Saturn?", "10th house assessment" | 2–5 calls, mostly parallel: ranked signals(entity) + strength + graph ego-net(1-hop) + citations | ≤15 KB total, ≤5 calls |
| **INVESTIGATION** | broad/open (Q2 wide, Q5–Q9): "strengths & weaknesses per rashi?", "life themes?", Mahā-Brief precursors | recursive protocol below | declared up-front, e.g. 100–300 KB, 10–30 calls |

**The INVESTIGATION protocol (the recursive loop the native described, made a first-class pattern):**
1. **ORIENT** — one digest call (`bodha_chart_digest` / domain map): pre-computed top-band summary
   across all families + contradiction register + graph hubs. Small (~5 KB). This is the MAP.
2. **FAN-OUT** — PARALLEL targeted pulls on the top-K threads the map surfaced (strength profile,
   yoga composites, dignity extremes, promise register, activation state). Parallel because the
   agentic loop pays latency, not tokens, for breadth.
3. **DRILL** — recursively follow drill_pointers where evidence is strong, contradictory, or
   surprising. Each response's pointers ARE the next questions; the LLM's reasoning chooses among
   them. Depth is budget-bounded, not hardcoded.
4. **TAIL-CHECK** — one complement pass (synth_tail_divergence / explicit tail facet): the Ranking
   Doctrine's "hunt the tail" as a mandatory step, so broad answers never become top-band echo chambers.
5. **SYNTHESIZE** — grounding ledger assembled from the envelopes already in hand.

Where the protocol LIVES (critical — no new plane): in **tool descriptions + one capabilities-card MCP
resource** that teaches regime selection and the per-intent recipes, and in the **drill_pointers** that
make each next step concrete. It is guidance the agentic LLM follows and can deviate from with reason —
never server-side orchestration. (This is also the industry-converged pattern for agentic tool loops:
fewer, schema-rich tools; progressive disclosure via pointers; parallel fan-out; budget hints —
in preference to both 70 thin projections and one generic query tool.)

## §5 — THE INSTRUMENT ESTATE (~70 → 15; every current handler becomes an internal of one instrument)

| # | Instrument | Absorbs (examples) | Idiom |
|---|---|---|---|
| 1 | `chart_query` | ganita_chart_facts/positions/condition/nakshatra/special_lagnas/sade_sati/tajaka | SQL |
| 2 | `dasha_query` | ganita_dashas/dasha_periods, windowed multi-system | SQL (window-mandatory) |
| 3 | `strength_query` | ganita_strength + per-varga extensions | SQL |
| 4 | `structural_query` | ganita_structural/yogas (+ yoga composites) | SQL |
| 5 | `signals_query` | bodha_signals + domain_reading + quality | SQL ranked |
| 6 | `graph_query` | graph_subgraph/traverse + paths | GRAPH |
| 7 | `synthesis_query` | chart_digest, discoveries, tail_divergence, contradictions, promise register, triangulation | SQL registers |
| 8 | `remedy_query` | bodha_remedies + ref remedy family + mitigation_map | SQL ranked |
| 9 | `kala_query` | windows/projections/life_arc/yoga_activation/temporal_bundle | SQL (window-mandatory) |
| 10 | `muhurta_query` | kala_muhurta/muhurta_finder + prashna_undertaking | SQL + compute |
| 11 | `phala_query` | anchors/outlook/mitigation/rectification | SQL ranked |
| 12 | `mimamsa_query` | calibration/insight/lel_query (chart-scoped per BA-LEL) + outcome_record (write) | SQL |
| 13 | `ref_search` | vector_search, classical_citation, rules_search, all ref_* lookups | CORPUS |
| 14 | `ephemeris_query` | ref_planet_transit/aspects_at_time/retrograde/ephemeris_year + natal compute | SQL/compute |
| 15 | `nav` | list_my_charts/select_chart/sessions/orientation + the capabilities card | session |
| — | `apex_*` (4) + Mahā-Brief | KEPT AS-IS: the deliberate bulk products | composed |

Consolidation rules: every absorbed tool name survives as an ALIAS to its instrument (zero breakage,
the P1 alias discipline); one handler per instrument; per-instrument intent-default table is part of
its schema; instrument descriptions carry when/when-not/cost + one worked example per intent.

## §6 — TOKEN-EFFICIENCY ENGINEERING (the measurable half of proportionality)

E1 field projection (select) · E2 columnar wire format, single header, enums · E3 pivot-at-tool
(EAV never crosses the wire) · E4 single-ayanamsha default · E5 mandatory windows on temporal
monsters · E6 top-K + counts + pointers (never full lists) · E7 budget facet with trim_report ·
E8 drill_pointers replace speculative payload ("here's how to get it" ≈ 50 tokens vs "here it is"
≈ 5,000) · E9 dedupe repeated metadata into the envelope header (chart, ayanamsha, versions said ONCE).

**Targets (acceptance-gated):** lagna question ≤2 KB (today: 63 KB — ~30×) · Saturn assessment ≤15 KB ·
full strengths/weaknesses investigation ≤300 KB with ≥90% of retrieved tokens actually consumed in the
final synthesis's grounding ledger (the utilization metric — the true measure of "no hundred
irrelevant things").

## §7 — EVAL: THE NATURAL-QUESTION BATTERY (how "smart" is measured, not felt)

~40 questions across Q1–Q9 × the three regimes × both charts, run over live MCP by an agentic client:
score = answer quality (G10-QT rubric /15) × token cost × call count × wall time, with per-question
regime-conformance checks (a fact question that triggered >1 call = failure; an investigation that
skipped the tail-check = failure). Baseline before wave 1; re-run per wave; regression-gated.
This battery is also R5's standing punch-list vehicle (the D1-chart failure class — lagna-vs-houses
cross-check — becomes battery item #1).

## §8 — MIGRATION PATH (execution slot: R5, after the native rebuild; briefs authored on ratification)

- **W0 — Contract + card:** request/response contract types, capabilities card, columnar wire format,
  budget/trim machinery, eval battery baseline.
- **W1 — SQL idiom on the big four:** chart_query, dasha_query, signals_query, synthesis_query (kills
  the 63 KB class and the windowless-dasha class; battery re-run).
- **W2 — Graph + corpus idioms:** graph_query traversal grammar; ref_search hybrid; interpretation
  intent auto-attaches citations.
- **W3 — Estate consolidation:** remaining instruments, aliases, intent-default tables, description
  engineering; ~70 names → 15 instruments + aliases.
- **W4 — Investigation hardening:** drill_pointer coverage audit (every surface a broad question
  touches emits pointers), tail-check surfaces, utilization metric live, full battery + seal.

Anti-goals for all waves: NO new plane/layer/composer · NO envelope-shape breakage (extensions only) ·
NO generic SQL tool exposed to the LLM · NO removal of any capability (aliases keep everything alive) ·
scoring paths stay LLM-free.

---

# PART II — WORKED BACKWARDS FROM THE ANSWER (v1.1)

*Part I designed the tools from the data upward. Part II designs them from the user's received answer
downward. Where the two meet is the contract. Method: sit in the endpoint LLM's chair — the model that
must synthesize the final response in Claude — and ask what it NEEDS, question by question, to answer
efficiently, accurately, and completely. One of its failure modes is not hypothetical: the 2026-07-06
D1-chart misread happened because nothing in the payload forced a frame check. §10.1 is its fix.*

## §9 — THE ANSWER TAXONOMY (what actually leaves the system)

Nine response types cover the product. Each row: what the user's question looks like → what the
response must contain → what retrieval must therefore supply.

| # | Response type | Question looks like | The response MUST contain | Retrieval must supply |
|---|---|---|---|---|
| A1 | **Fact card** | "What's my lagna?" "Current dasha?" | exact values, zero hedging, correct frame | surgical pull + chart_header (§10.1); formatted canonical values (§10.8) |
| A2 | **Chart reading** | "Strengths & weaknesses per rashi?" "Read my chart" | gestalt headline → ranked themes → strengths w/ evidence → weaknesses w/ evidence → contradictions acknowledged → citations | investigation regime + coverage receipt (§10.5) + tail-check + dissent rows |
| A3 | **Domain assessment** | "How's career?" "Marriage prospects?" | verdict + graded basis + timing hooks + honest caveats | apex/composed + promise register (incl. DENIED) + activation state |
| A4 | **Prediction** | "Job change this year?" | probability + window + falsifier + what-would-change-it + calibration honesty | phala anchors (full range incl. unlikely) + lift_vector + calibration_state |
| A5 | **Timing/election** | "When should I start X?" | ranked windows + why + avoid-windows | kala windows + muhurta + activity ontology |
| A6 | **Intervention** | "What remedy?" | ranked remedies + chart-specific resonance + tiers + what each addresses | remedy resonance + mitigation map + the afflictions they answer |
| A7 | **Verification** | "My astrologer said X — true?" | confirm/deny/partial + THIS system's evidence + tradition triangulation + honest disagreement | NEGATIVE KNOWLEDGE (§10.3) + triangulation register + absence proofs |
| A8 | **Drill/follow-up** | "Tell me more about that Saturn issue" | continuity with the earlier answer — same basis, deeper | session stability (§10.6): pinned ranking, drill_pointers from prior envelopes |
| A9 | **Derivation** | "Why do you say that?" | the visible chain: fact → signal → verdict, with verses | grounding ledger walk + inline citations (§10.7) |

Design rule: **every Q-class × intent lands in exactly one row of this table**, and every instrument's
intent-defaults are tuned so its first response serves that row's needs.

## §10 — WHAT THE ENDPOINT LLM NEEDS (the bill of needs — each item is a contract clause)

**10.1 FRAME SAFETY (the D1-failure killer).** Every per-chart envelope carries a mandatory ~40-token
`chart_header`: `{chart_id_short, name, lagna_sign, lagna_deg, moon_sign, sun_sign, ayanamsha,
current_maha_antar}`. The synthesis LLM cross-checks any positional claim against this header before
asserting it; a payload whose body contradicts its own header is a served-data bug, halt-worthy. Cost:
~40 tokens. Value: the entire class of frame-inversion misreads becomes structurally impossible.

**10.2 UNIFIED EPISTEMIC VOCABULARY.** Hedging language must be machine-fed, not vibes. One `epistemic`
grade per claim-bearing row, from a CLOSED vocabulary:
`ganita_fact | verified_signal | single_pass_signal | classical_contested | calibrated_posterior |
structural_prior | floored_null`. The endpoint maps grade→phrasing ("is" / "strongly indicated" /
"suggested" / "traditions differ" / "estimated at X% (uncalibrated)" / "cannot be computed, because…").
Today this signal is scattered across judgment_flags, verification fields, and calibration notes —
consolidation into ONE field is what makes hedging CONSISTENT across a 20-message conversation.

**10.3 NEGATIVE KNOWLEDGE (A7's prerequisite).** A tool that only returns what exists cannot support
"is it true that…?" The estate must serve absence: promise register `denied` rows ARE first-class
retrievable; yoga-queries support `assert_absent` (returns the checked-and-not-formed proof with the
conditions that failed); "notable non-firings" (famous yogas whose preconditions were near-missed) are
a queryable band. Verification answers then rest on evidence of absence, never on absence of evidence.

**10.4 NOW-CONTEXT.** A4/A5/A8 answers are meaningless without "as of when." One cheap block —
`{today, current dasha stack (3 levels), sade_sati_state, major transits summary}` — available as a
~200-token expand on any temporal instrument (and inside chart_header's current_maha_antar in
miniature). Never recomputed by the LLM, never stale beyond its TTL (dasha-boundary keyed, the P2
cache discipline).

**10.5 COVERAGE RECEIPTS (completeness made verifiable).** A broad answer's most dangerous failure is
silent incompleteness — the LLM cannot know what it never saw. The investigation protocol therefore
ENDS with a receipt the orient-surface can grade: `{grahas_covered: 9/9, bhavas: 12/12, top_band_seen:
k/k, tail_checked: true, contradictions_surfaced: n/n}` — assembled from the envelopes' own coverage
stamps. An A2 response without a full receipt says so ("X not examined"). This turns "completely" from
an aspiration into a checkable property.

**10.6 SESSION STABILITY.** A conversation must not contradict itself because a cache expired or a
prior version bumped mid-session. Retrieval pins `{priors_version, formula_versions, ranking_config,
now_context timestamp}` at session open (the pin rides the session the nav tool already anchors);
every response reports the pin; drill calls inherit it. Version bumps take effect at the NEXT session.
(Two-key snapshot discipline, applied to serving.)

**10.7 INLINE CITATIONS AT INTERPRETATION INTENT.** For acharya-grade prose the endpoint needs the
verse WITH the claim — `{source, verse_ref, 15-30 word quote/translation}` inline for the top-k claims
(k≈5), pointers for the rest. A citation the LLM must chase mid-synthesis is a citation that gets
paraphrased from priors instead — the exact failure the classical bridge exists to prevent.

**10.8 RESPONSE-READY VALUES.** The LLM must never do arithmetic the data plane already did (native's
own precomputation philosophy, applied to the last mile). Alongside numerics, canonical display
strings: `23°32′ Aries, Bharani-4`, `Śukla Tṛtīyā`, `Ketu MD / Venus AD (2027-03 → 2028-01, age 43)`.
Ages accompany dates everywhere (the user thinks in ages; date→age arithmetic is an LLM error class).

## §11 — ANSWER SURFACES (the first call returns scaffolding, not raw material)

Generalizing what digest/apex already prove: for each §9 row, ONE instrument+intent default whose
response is already SHAPED like the answer — a verdict/evidence TREE (claim → supporting rows →
epistemic grade → citation), not a flat rowset the LLM must reorganize. A1←chart_query(fact);
A2←synthesis_query(orient) opening the investigation; A3←apex_*; A4←phala_query(prophecy);
A5←kala/muhurta_query; A6←remedy_query(intervention); A7←synthesis_query(verify: triangulation +
assert_absent); A8←any drill_pointer; A9←grounding-ledger walk. The regime machinery (§4) is unchanged —
answer surfaces are what its FIRST call returns, so composed/surgical answers are often one call deep
and even investigations start already-oriented.

## §12 — DATA-PLANE ADDITIONS (what §9–§11 require that storage doesn't yet hold)

D1 **chart_header materialization** — trivial view over chart_facts; served by every instrument.
D2 **epistemic grade** — derivable now from existing columns (verification, calibration_state, floors);
   ONE mapping function in the serving layer, spec'd in the capabilities card. No new writer.
D3 **absence proofs** — `assert_absent` computes from existing rule preconditions at query time
   (bg_rules + yoga catalog); "notable non-firings" needs a small stored near-miss band from bo_laksana
   (flag at L2 regen, cheap column, no new asset).
D4 **now_context service** — thin compute over chart_dashas + transit service, dasha-boundary TTL.
D5 **coverage stamps** — each envelope self-describes what fraction of its family it served
   (`{family, served, total}`) so receipts are assembled client-side from stamps, not guessed.
D6 **session pin** — serving-layer session row `{pins…}`; no schema change to data assets.
D7 **display strings** — generated at serve time from one canonical formatter (the dd-MMM-yyyy
   discipline, extended to degrees/tithis/dasha-spans/ages); never stored, never duplicated.
Everything lands in the serving layer or as L2-regen flags — NO new layer, NO new asset class,
consistent with the no-new-planes ruling.

## §13 — EVAL REORIENTATION: SCORE THE ANSWER, NOT THE RETRIEVAL

The §7 battery gains a second stage: for each battery question, the full loop runs — retrieval +
endpoint synthesis (product-policy LLM) — and the SYNTHESIZED ANSWER is judged against a per-response-
type rubric (§9's "must contain" column, itemized): A1 exact-match; A2 receipt-complete + both-sides;
A4 falsifier-present + range-honest; A7 absence-evidence-cited; A8 consistency-with-prior-turn; A9
chain-walkable. Plus the frame-safety canary: a battery item that deliberately serves a chart whose
header the question tries to contradict (the D1 regression test). Wave acceptance = answer-rubric
scores, with token/call metrics demoted to efficiency diagnostics. The instrument exists to produce
answers; the eval now measures what it exists for.

---

*One-line summary (v1.1): the four stations stay; the tools stop being taps and become instruments;
and every instrument's first duty is the ANSWER — frame-safe, epistemic-graded, absence-capable,
now-anchored, coverage-receipted, session-stable, verse-in-hand, arithmetic-free.*

---

# PART III — THE LIVE AUDIT (v1.2): the battery run for real, by the endpoint LLM itself

*2026-07-07, native chart 482012f1, live MCP, Cowork as the endpoint. Eight probes spanning §9's
answer types. Verbatim evidence retained in the session transcript. Verdict: 6 of 8 failed or
materially degraded — and the failure MODES are more instructive than the failures.*

## §14 — PROBE FINDINGS

**P1 · A1 fact — "what dasha am I running today?" (`ganita_dashas_get`, as_of_date=2026-07-07): FAIL.**
Returned 15 rows from **1950** — thirty-four years before birth — from the **ashtottari** system at
mixed levels 1–4. `as_of_date` was silently ignored; there is no `system` or `level` facet at all; rows
are ~1,300 tokens each (40+ fields, most null); `applies_to_this_chart_flag=true` on pre-birth rows.
The single most common question in astrology is unanswerable in one call. [→ E-1, E-5]

**P2 · A2 orient — chart digest (`bodha_chart_digest_get`, summary): FAIL as a map.** The top-20
"signals" are twenty near-identical Saturn ashtakavarga atomic tallies, all at the degenerate stored
salience 2.326672 (the stored path — query-time ranking does NOT protect the digest). Header says
`contradiction_count: 1034`; the per-domain rows all say `contradiction_count: 0` — the surface
contradicts itself. Convergence = raw volume counts (career 11,970, the known artifact). An
investigation seeded from this map starts lost. [→ E-2, E-6; partially heals at R4]

**P3 · A7 substrate — yogas (`ganita_yogas_get`, limit=100): OVERFLOW + EMPTY ENVELOPE.** 64KB (blew
the consumer ceiling); and the envelope fields exist but are HOLLOW — `verdict: null`,
`ranking_basis: null`, `drill_pointers: []`, `judgment_flags: []`. Envelope conformance by schema,
not by substance: "schema theater." [→ E-3]

**P4 · A3 substrate — ranked signals (`bodha_signals_get`, career, top_k=5): PARTIAL — the one organ
that mostly works.** ranking_basis present and arithmetically verifiable; provenance honest in FORM.
But: the #1 career signal is "Kala Sarpa: NOT detected (fires=False)" served with no absence framing
and `intrinsic_strength=0.5` (the silent-default constant, live in the ranking); `percentile_within_class=1`
on every row (degenerate); two yoga rows carry `fire_reason=requires_pass` — epistemically ambiguous
(fired? labeled? pending verification?) with benefic valence attached anyway; and the provenance notes
are STALE in both directions ("DEFECT-001 OPEN 91.5% orphan" vs the program's resolved-at-0% gate;
"signature_tier 100% background" while the same response's rows show `major` and `supporting`).
Honest-looking notes that are wrong are worse than no notes. [→ E-2, E-4, §10.2, §10.3]

**P5 · A4 prediction — 12-month outlook (`phala_outlook_get`): FAIL, loudly.** `anchors: []`,
`summary_confidence: 0`, and the provenance block leaks raw SQL errors — `column "id" does not exist`
(PH-4-1), `column "anchor_id" does not exist` (PH-4-2): the serving SQL disagrees with the live schema
(the mig-365 fix never reached the serving path). `panchanga_daily` returned **0 rows for the entire
next year** — election/timing has no forward data. Meanwhile the rectification block leaks train/test
internals into a user-facing answer. A4 is unservable today. [→ E-1, E-7, D-8]

**P6 · dissent organ (`synth_tail_divergence_get`): DOWN.** Hard 404. The MANDATORY step 4 of the
investigation protocol does not exist in prod. Same failure class as the known
`ganita_chart_facts_get` category-filter 404. [→ E-1]

**P7 · corpus semantic search (`ref_vector_search`): DOWN.** 401 — the known callPlatformPrimitive
auth defect, still live. The entire corpus idiom (§3) currently has no working entry point. [→ E-1]

**P8 · citation lookup (`ref_classical_citation_get`, keyword="neecha bhanga"): SILENT EMPTY.**
0 rows, no reason, no alternate-spelling suggestion, no "corpus does not index this term" honesty.
Indistinguishable from "the corpus has nothing on neecha bhanga," which is false. [→ §10.3, E-4]

**What works and must be preserved:** the alias discipline (every renamed tool answered), ranking_basis
transparency (I could re-derive the composite by hand), two-pass verification surfacing, and the
HABIT of provenance honesty — the form is right; the freshness and substance are what fail.

## §15 — TRIAGE (three buckets; do not conflate them)

| Bucket | Findings | Owner |
|---|---|---|
| **R4-heals** (data regenerates at the native rebuild) | P2 degenerate stored top-band + P4 stale-data aspects (orphan rate, signature_tier distribution, percentile degeneracy) — IF the P3B stored path is what R4 rebuilds serve | The runway (verify at R4 gates: re-run P2/P4 post-rebuild) |
| **SERVING-BUG PUNCH-LIST** (code defects, independent of 3.0; several are P0) | P5 SQL column mismatches · P6 404 · P7 401 · P8 silent empty · P1 as_of_date ignored · ganita_chart_facts 404 · P4 stale provenance notes · P5 forward-panchanga emptiness (data job) | Immediate fix brief — do NOT wait for R5 |
| **3.0-DESIGN** (what Retrieval 3.0 must structurally prevent) | Everything in §16 | R5 waves |

## §16 — DESIGN ELEVATIONS FORCED BY THE AUDIT (new contract clauses)

**E-1 · SERVING-HEALTH IS PART OF THE PRODUCT.** Three organs were down/broken and NOTHING announced
it — the endpoint discovers outages by burning a call and parsing an error. The capabilities card
(§4) gains a live `system_health` block (per-instrument: up/degraded/down + reason + since), fed by a
scheduled mini-battery (5 canary calls). Errors NEVER leak transport codes (404/401) or raw SQL — every
failure returns the standard envelope with `judgment_flags.serving_fault={reason, since, workaround}`.
An instrument that can say "my phala backend is schema-broken since 2026-06-30, use kala_windows for
timing" turns an outage into a detour.

**E-2 · PROVENANCE FRESHNESS CONTRACT.** Every provenance/judgment note carries `{as_of, expires_on
(gate-linked)}`; notes tied to a defect gate (DEFECT-001, signature_tier recut) are AUTO-RETIRED when
the gate closes — a stale note is a served bug, equal in severity to stale data. Contract test: no
note may contradict the same response's own rows (P4's self-contradiction becomes a CI failure).

**E-3 · NO SCHEMA THEATER.** Envelope conformance is measured on SUBSTANCE: for each instrument ×
intent, the contract declares which envelope fields MUST be populated (yogas at interpretation intent
MUST have drill_pointers and judgment_flags; verdict-bearing tools MUST have verdict). `null`/`[]` in
a must-populate field fails the battery. Empty-with-reason is the only legal empty (P8's silent zero
becomes: "0 rows — term not indexed; nearest indexed terms: [neechabhanga_rules, dignity_cancellation]").

**E-4 · SERVED-AGGREGATE CONSISTENCY INVARIANTS.** The degenerate-distribution guard (build-side)
extends to serve-side: cross-field invariants checked in the handler before the response ships —
header counts must reconcile with body rows (P2's 1034-vs-0), percentile columns must be
non-degenerate across a served page, no ranking factor may sit at its documented silent-default for
>80% of served rows without a judgment_flag admitting it (P4's intrinsic_strength=0.5).

**E-5 · TEMPORAL FACETS ARE LOAD-BEARING, NOT DECORATIVE.** A declared-but-ignored parameter
(P1's as_of_date) is the worst contract violation in the estate — worse than absence, because the
endpoint TRUSTS it. Every facet in every instrument schema gets a conformance test (send it, verify it
altered the result). dasha_query's mandatory facets per §1: system (default vimshottari), level-cap
(default 3), window (default now±5y) — "current stack today" must cost ≤1 KB, and pre-birth rows never
ship without an explicit historical window asking for them.

**E-6 · THE ORIENT SURFACE IS RANKING-GOVERNED, ALWAYS.** P2 proved the digest reads the STORED band
while signals read the QUERY-TIME ranking — the map and the territory use different rankings. Contract:
every summary/orient surface consumes the same ranking pipeline as its drill surface, with hierarchical
aggregation applied (one composite Saturn-AV profile row, never twenty atoms). No stored-band shortcut
survives 3.0.

**E-7 · USER-FACING vs INSTRUMENT-FACING RESPONSE SPLIT.** P5 leaked train/test splits, leakage
firewalls, and SQL internals into an answer surface. The envelope gains an `audience` seam: synthesis
content (what the answer is built from) vs instrument diagnostics (provenance chains, splits, engine
versions) — the endpoint needs both, but must be able to WITHHOLD the second by default and retrieve
it on demand (A9 derivation pulls it explicitly). Diagnostics-by-default is how internals end up
paraphrased at users.

**D-8 (data-plane, joins §12) · FORWARD TEMPORAL POPULATION.** panchanga_daily (and any
election-serving table) must be populated N months FORWARD on a scheduled job, gate-checked by the
canary battery (P5 found a year of emptiness only because a user-question walked into it).

## §17 — WHAT THIS CHANGES IN THE MIGRATION PATH

W0 absorbs the serving-bug punch-list as its FIRST deliverable (the 3.0 contract cannot be built on
handlers that ignore parameters and leak SQL) and stands up the canary battery + system_health.
W1–W4 unchanged in scope, but every wave's acceptance now includes: facet-conformance tests (E-5),
substance-conformance (E-3), consistency invariants (E-4), freshness contract (E-2). The §13
answer-rubric battery gains the 8 probes of §14 as PERMANENT regression items — this audit is the
eval's seed corpus.

---

*One-line summary (v1.2): v1.1 said what the endpoint needs; the live audit proved the system doesn't
provide it — and that the gap is one-third data (R4 heals it), one-third serving bugs (fix now), and
one-third contract (3.0 exists precisely to make these failure modes structurally impossible).*

---

# PART IV — PRE-IMPLEMENTATION CODE AUDIT (v1.3): every premise verified against the repo

*Two exhaustive sweeps (serving architecture + data plane), 2026-07-07. Full evidence in the audit
transcripts; the verdicts and their design consequences are binding on the wave briefs.*

## §18 — PREMISE VERDICT TABLE

| Premise (§) | Verdict | Reality (key evidence) |
|---|---|---|
| One registry to extend with facets (§2) | **DIFFERENT — the central risk** | ONE canonical registry (`platform/src/lib/retrieval/registry/index.ts`) holds the real handlers; but tools are RE-DECLARED as Zod shims in a separate process (`platform-mcp/src/tools/*`), joined by hand-edited string maps. See §19. |
| 70→15 consolidation cost (§5) | **CONFIRMED-CHEAP, one nuance** | Aliases already delegate many names to one handler (`register_p1_aliases.ts:110,135`); consolidation = deleting alias registrations. Nuance: aliases carry DIVERGING param names (`min_weight` vs `min_salience`, `top_k` vs `limit`) — reconcile, don't just delete. |
| Envelope exists, needs population (§2) | **DIFFERENT — worse** | TWO incompatible envelope shapes: platform-mcp local helper with every field hardcoded null/[] (`register_p1_synthesis.ts:45`, used by ~6 tools; ~60 tools have NO envelope) vs platform `epistemics.ts:129` buildEnvelope (different fields entirely). Unified populated envelope = net-new build, W0. |
| Facet-style SQL precedent (§3 SQL idiom) | **CONFIRMED** | `query_signals.ts:158–181` already does whitelisted filter/params compilation + composite ranking + ranking_basis. This is the facet engine's seed. |
| Graph traversal grammar (§3 graph idiom) | **CONFIRMED — mostly built** | `traverse_chart_graph.ts` already supports seeds/depth(≤3)/edge_types/valence/modes(neighbors·paths·convergence·contradictions)/semantic_query via recursive CTE on `bodha_cgm_edges` (well-indexed, mig 325). W2 is extension, not construction. **CAVEAT: valence vocabulary drift** — mig 325 says benefic/malefic/mixed/neutral; mig 394 re-adds CHECK harmonious/antagonistic/neutral. A valence filter can silently match zero rows. Reconcile in W0. |
| Corpus idiom infra (§3) | **CONFIRMED** | pgvector everywhere needed; signal embeddings 66,738 rows/100%; model PINNED (`text-multilingual-embedding-002`, 768d, `embedText.ts:5-8`). Only the 401 stands between design and function. |
| EAV pivot at tool (§1, E-tools) | **FEASIBLE, MISSING** | chart_facts indexes support the crosstab (`204:36-40, 206:22-23`); NO existing pivoted view — W1 builds it. |
| Dasha window queries (§1, E-5) | **CONFIRMED** | Covering index `cd_temporal_lookup_idx(chart_id, ayanamsha_id, system_id, level_n, start_date, end_date)` (mig 206:63). The facets are a WHERE clause away. |
| Session pin (§10.6) | **CONFIRMED — easiest premise** | DB-backed McpSession with free-form `state_json` (`session.ts:37`, mig 382). Pin drops in with zero schema change. Caveat: default session key is per-user `"default"` — pin semantics are per (user, session-key). |
| Dasha-boundary cache TTL (§10.4) | **DIFFERENT** | Cache is a flat 60s in-process Map (`retrieval/cache.ts`); dasha-boundary TTL is new logic; in-process scope won't span the two processes. |
| Budget/trim machinery (§2, E-7) | **DIFFERENT** | The 25000 "limit" is a cosmetic row ceiling; a real clipper EXISTS (`adapters/shared/result_clipper.ts`) but is unwired from MCP. Budget facet = wire the clipper + per-shape trim rules. |
| Capabilities card (§4) | **PARTIAL — extend, don't build** | `marsys://capabilities` resource already serves from live tool_health + data_coverage (`resources/capabilities.ts`). system_health (E-1) extends it. |
| Digest reads stored band (P2 diagnosis) | **REFINED** | Digest = `query_ucd.ts` reading `vw_chart_digest` + live `ORDER BY computed_salience` — so it's live-but-COARSE ranking, not a stored-band table. `salience_pctl_in_class` EXISTS as a stored column (mig 393) but is unpopulated until rebuild AND unread by serving. E-6 = point digest at the composite ranking pipeline + consume 393 post-R4. |
| panchanga_daily just needs a job (D-8) | **DIFFERENT — bigger** | It's a `WHERE FALSE` stub VIEW (mig `365_w4_l4_schema_drift_fix.sql:176-203`); real table archived. D-8 = re-provision table + writer + forward-population job, not "run a job." |
| Display formatter (§10.8) | **CONFIRMED** | `utils/date.ts` formatDate/formatDateTime (dd-MMM-yyyy). Degrees/tithi/dasha-span/age formatters get added beside it. |

## §19 — THE STRUCTURAL FINDING: THE TWO-PROCESS CONTRACT SEAM

The platform (registry + handlers + DB) and the MCP server (Zod param shims proxying over HTTP) are
**separate processes whose tool contracts are maintained by hand in two languages**, joined by string
maps. This seam is not hypothetical debt — it is the ROOT CAUSE of audit failure P1: the alias declares
`as_of_date`, the handler reads `date_contains`/`date_from`, and the parameter silently dies at the
boundary. A "uniform faceted contract" maintained by hand across this seam would drift the same way
within a quarter.

**Design mandate (binding on W0): SINGLE-SOURCE CONTRACT GENERATION.** The facet schema for each
instrument is declared ONCE, in the registry's CapabilityDescriptor. The MCP-side Zod shims and the
name maps are GENERATED from the registry at build time (codegen step in CI), never hand-edited. A CI
contract test round-trips every declared facet through the seam and asserts it altered the result
(E-5's conformance test, applied at the boundary where drift is born). This replaces the §8 W0 line
"request/response contract types" with something stronger: the contract has one home and the seam
becomes mechanical.

## §20 — PUNCH-LIST ROOT CAUSES (every §14 failure now has an exact fix site)

| Failure | Root cause (file:line) | Fix class |
|---|---|---|
| P6 tail_divergence 404 (+ discoveries, chart_brief, prashna_undertaking) | Tools call `POST /api/mcp/db/query` — **the route does not exist** (`register_p1_synthesis.ts:34-41`; no route file in repo) | Create the route (auth-gated, whitelisted) OR repoint the 4 tools through the capability bridge |
| P7 vector_search 401 | `callPlatformPrimitive` sends only `x-mcp-internal-token`; primitives route requires `X-MCP-User`+`X-MCP-Key-Id` (`registry_bridge.ts:77` vs `primitives/[tool]/route.ts:98-106`). Correct 3-header pattern already exists in `resources/capabilities.ts:26-30` | Copy the working header pattern into both proxy helpers |
| P1 as_of_date ignored | Param dies at the seam: declared in alias (`register_p1_aliases.ts:199-202`), absent from handler (`get_dashas.ts:73-83` reads date_contains/date_from only) | Map as_of_date → containment filter in the handler; then §19 kills the class |
| P5 phala SQL errors | Serving code assumes the LEGACY phala_anchors schema (`anchors.py:161` selects `id`; `mitigation.py:390-396` selects `theme`) vs deployed mig-330 schema (PK `anchor_id UUID`, no `id`, no `theme`). Mig 365's §1 claims to fix it but only adds `domain` (`365:27-28`). Plus anchor_id TEXT-vs-UUID conflict; plus TWO live migration roots with COLLIDING numbers (365 exists twice) | Rewrite serving SQL against mig-330 schema; resolve the type conflict with a real migration; wave briefs must cite migrations by FULL PATH, never number alone |
| P2 degenerate digest map | `query_ucd.ts:117-127` live-ranks by raw computed_salience (coarse), never the composite pipeline; stored pctl column (mig 393) unpopulated + unread | E-6: digest consumes composite ranking + hierarchical aggregation; post-R4 also reads 393 |
| P5 panchanga year-empty | Stub `WHERE FALSE` view (see §18) | D-8 re-provision (table + writer + forward job) |
| P8 silent citation empty | Handler returns bare zero rows, no reason path | E-3 empty-with-reason in the unified envelope |
| P3 64KB yogas + hollow envelope | No envelope on registry_bridge tools; no shape/summary facet; row ceiling cosmetic | W1 facets + unified envelope + wired clipper |
| P4 stale provenance notes | Notes are string literals in handler code (`query_signals.ts` provenance block) | E-2 freshness contract: notes become data with as_of/expires_on |

## §21 — FINALIZATION DELTAS TO THE WAVE PLAN (§8/§17 adjusted; this is the implementation order)

- **W0 (expanded, now the keystone wave):** serving-bug punch-list (§20, all nine) + single-source
  contract generation (§19) + unified populated envelope (one shape, both processes) + valence-vocab
  reconciliation + capabilities-card extension w/ system_health + canary battery + eval baseline.
- **W1:** the big-four SQL instruments on the generated contract — incl. the chart_query crosstab
  (net-new pivot), dasha facets (index already covers), signals/synthesis on the query_signals
  precedent. Budget facet via the wired result_clipper.
- **W2:** graph idiom = EXTEND traverse_chart_graph (path patterns, direction facet, strength floors);
  corpus idiom = vector_search post-401-fix + hybrid + inline-citation attachment at interpretation
  intent.
- **W3:** estate consolidation (delete alias registrations w/ param reconciliation per §18), intent
  defaults, description engineering.
- **W4:** investigation hardening (drill_pointers coverage, receipts from coverage stamps,
  session-pin serving, tail surfaces), full answer-rubric battery + seal.
- **Dependency notes:** D-8 (panchanga) and the 393-column population ride the DATA plane (R4/cascade
  rebuild), not these waves — W-briefs treat them as external gates with empty-with-reason honesty
  until they land. All §18 caveats (session-key semantics, cache process-locality, migration
  dual-root citation rule) are binding constraints on every wave brief.

---

*Finalization statement: with Part IV, every §1–§16 claim is either code-verified or explicitly
corrected, every audit failure has a named fix site, and the one structural risk (the contract seam)
has a binding mitigation. The design is implementation-grade. Remaining before W0 briefs are authored:
native ratification of §5 instrument grouping, §6 budget seeds, and this finalized shape.*

---

# PART V — THE PERFORMANCE PILLAR (v1.4): where the time goes, and how it comes back

*Full code-path trace 2026-07-07 (hop counts per tool class, deploy configs, measured prod baselines).
The endpoint-LLM observation that motivated it: every live-audit probe carried multi-second lag, and
the native's D1-question complaint was about time as much as size.*

## §22 — THE LATENCY EQUATION (what the user actually waits for)

`T_answer ≈ Σ_serial_calls (T_llm_turn + T_server + T_stream(payload))`

The term nobody optimizes is the first one: **every serial tool call costs a full LLM reasoning turn
(seconds) on top of its server time.** A 5-call serial answer with a fast backend is still slower than
a 2-call answer with a mediocre one. Consequences, in priority order:
1. **Call count is the #1 latency lever** — answer surfaces (§11: first call returns scaffolding),
   the `expand` facet (one call instead of three), and precise drill_pointers (no exploratory misses)
   are LATENCY features as much as quality features.
2. **Parallel fan-out is free wall-time** — investigation step 2 (§4) issues its pulls concurrently;
   k parallel calls cost one turn, not k. The instruments must be safe and fast under parallel load.
3. **Payload size is a latency tax twice** — serialization server-side and streaming into context.
   The 63KB→2KB facet cut is also a time cut.
Only after these does per-call server time (§23) dominate.

## §23 — MEASURED REALITY + RANKED SINKS (all asia-south1; full evidence in trace transcript)

Prod p50 baselines (CURRENT_STATE:285-288): list_my_charts 400ms · digest 458ms · signals(50) 672ms ·
domain_reading 1,356ms · assess_career 4,414ms (pre-cap, 17.2MB). No p95 table exists yet (P0 asked;
only p50 landed) — the canary battery (E-1) closes this.

| # | Sink | Evidence | Fix class |
|---|---|---|---|
| S1 | **B.11 double-hop:** ~13 domain tools serially pre-fetch the full UCD orientation before their own query (`registry_bridge.ts:213-238`) — ~458ms added to EVERY domain call (domain_reading 1,356 ≈ UCD 458 + work 900). The 60s cache that should absorb it is per-instance and defeated by min-instances=0 | measured + code | CODE — parallelize (`Promise.all`) or session-share the orientation; biggest MEDIAN win |
| S2 | **Cold-start cascade:** all three services (`amjis-mcp`/`amjis-web`/`amjis-sidecar`) at `--min-instances=0` (deploy.yml:273,385,448); sidecar tools cross TWO cold-eligible services serially; Next.js re-bootstraps the whole registry per cold start (`capability/route.ts:66-90`) | config | CONFIG — min-instances=1 on web+mcp (NATIVE SPEND DECISION, ~$: flagged); warm bootstrap; biggest TAIL win |
| S3 | **Serialization tax ×3-4:** stringify-to-measure (`query_signals.ts:284`), route stringify, then dualOutput RE-parses and PRETTY-PRINTS (indent=2, +20-30% bytes) AND duplicates the payload as text alongside structuredContent (`registry_bridge.ts:137`) | code | CODE — Buffer.byteLength for measurement; drop pretty-print; structuredContent-only above a size threshold |
| S4 | **Primitives gate stack:** up to 4 serial DB queries before real work (rate-limit, tool_registry, role, entitlement — `primitives/[tool]/route.ts:110-205`), uncached | code | CODE — cache tool_registry+role (short TTL) or fold gates into one query |
| S5 | **Sidecar authz hop:** phala/kala/holistic tools call web `/api/mcp/authz` (HTTP+DB) THEN the sidecar, serially (`bo_2-8.ts:169→178`) | code/arch | Short-lived signed entitlement claim minted at Bearer validation (already 60s-cached) replaces the hop |
| S6 | **Salience ORDER BY scan:** dual-pool domain queries sort 66,738-row bodha_msr_signals by computed_salience with no covering index found (`query_signals.ts:216-239`) | code/db | EXPLAIN + add `(chart_id, ayanamsha_id, computed_salience DESC)` index if absent |
| S7 | **Pool sizing:** pg pool max=10 vs Cloud Run concurrency=80 (`db/client.ts:50`); burst → queue → 5s connect timeout; 15s idle eviction re-pays connects after quiet | config | Right-size pool; revisit with the gate-collapse of S4 |
| S8 | **Alias 25k row ceiling:** `limit.max(25000)` default lets one call request the world (`register_p1_aliases.ts:87-126`) | code | Dies with the facet defaults (regime budgets replace cosmetic ceilings) |

**Good news the trace confirmed:** no cross-region hops; session fetch is NOT per-call; Bearer
validation cached 60s; fetch keep-alive works implicitly; query_ucd's three aggregates already run in
Promise.all; identity-token minting cached.

**Security flag (out of scope here, MUST route to the MCP-elevation workstream):** the capability
route checks only the internal token — registry_bridge tools perform NO per-call chart entitlement
(`capability/route.ts:97`), unlike the primitives route. A latency trace found an authz gap.

## §24 — E-8: TIMING TELEMETRY + SLOs (performance becomes observable and gated)

Every envelope gains a `timing` block: `{server_ms_total, gate_ms, db_ms, upstream_ms, serialize_ms,
cold_start: bool, instance_warm_s}` — assembled from cheap hrtime marks in the handler + route. The
canary battery records p50/p95 per instrument per day into the capabilities card's system_health.
**SLOs (warm-path, server-side, acceptance-gated per wave):** surgical ≤600ms p50 / ≤1.5s p95 ·
composed ≤1.5s p50 / ≤3s p95 · sidecar compute ≤4s p95 · investigation total wall-time ≤ its declared
budget. End-to-end (LLM-inclusive) targets live in the §13 answer battery: fact card ≤1 turn,
composed ≤2 turns, investigation ≤declared call budget — turn count IS the end-to-end latency proxy
the eval can enforce.

## §25 — WAVE ABSORPTION

W0 absorbs, alongside §21's punch-list: S2 config wins (min-instances = native spend sign-off), S3
serialization fixes, S1 UCD parallelization, S6 index verification, E-8 telemetry + the p95 baseline
the P0 brief never got. S4/S5 land in W1 with the contract generation (the gate stack is re-plumbed
once, not twice). S8 dies in W1 facet defaults by construction. Every wave's acceptance re-runs the
canary p50/p95 against the SLOs — a wave that improves tokens but regresses latency does not pass.

---

*One-line summary (v1.4): the user's wait = calls × turns + server time + bytes; 3.0 attacks all three
— fewer calls by design (answer surfaces, expand, parallel fan-out), a measured and de-bottlenecked
per-call path (8 named sinks, 5 cheap), and payloads that finally match the question. Performance is
now a gated property of every wave, not a hope.*

---

# PART VI — THE ASTROLOGY PILLAR (v1.5): the design reviewed against the shastra itself

*The governing pillar. Everything below answers one question: does the instrument navigate in the
coordinates of Jyotish, or does it force the LLM to translate Jyotish into database-speak at every
step? Parts I–V built a fast, honest, flexible retrieval system; Part VI makes it an ASTROLOGICAL one.*

## §26 — THE REVIEW: HOW AN ACHARYA REASONS vs HOW THE DESIGN NAVIGATED

The classical judgment protocol for any bhava-question (BPHS/Phaladeepika discipline): examine the
BHAVA, its LORD, and the KARAKA — from the LAGNA and again from the MOON (Sudarshana discipline) —
each graded for strength and affliction; CONFIRM in the operative varga (D9 marriage, D10 career,
D7 progeny…); weigh the YOGAS bearing on the matter; then TIME it: which dasha carries the promise,
does gochara concur (double-transit). The tradition also fixes the predictive grammar: **promise in
the rashi → confirmation in the varga → activation in the dasha → trigger in the transit** (the same
PACT chain the L4 redesign already encodes at the data layer).

Verdict on the v1.4 design, element by element:

| Element | Verdict | Gap |
|---|---|---|
| 15 instruments by data family (§5) | **SOUND as substrate, WRONG as the navigation surface** | The LLM translates "marriage" → domains/tables at every call; astrological meaning leaks at each translation |
| Facet grammar (§2) | **SOUND but astrologically mute** | `where` speaks in columns (entity, varga, dignity) — no bhava-lord indirection, no reference frames, no karaka addressing |
| Investigation protocol (§4) | **SOUND for open readings, GENERIC for predictions** | orient→fan-out→drill→tail is research methodology; the tradition's own protocol (PACT) is stronger for event/timing questions because each stage is classically falsifiable |
| Answer surfaces (§11) | **RIGHT IDEA, data-shaped recipes** | A3's scaffold aggregates signals-by-domain; the acharya's checklist (bhava/lord/karaka × frames × varga) is the classically COMPLETE scaffold |
| Coverage receipts (§10.5) | **RIGHT MECHANISM, wrong units** | "9/9 grahas, 12/12 bhavas" is inventory coverage; classical completeness = "judged from lagna AND Moon, karaka examined, varga confirmed" |
| Response values (§10.8) | **PARTIAL** | Degrees/dates covered; strengths, aspects, avasthas still serve as bare floats where the shastra has named grades |
| drill_pointers | **GENERIC** | "847 more rows" — the astrologically meaningful next steps are "confirm in D9", "check neecha-bhanga", "is the promising dasha still to come?" |

## §27 — THE ASTROLOGICAL ADDRESS SYSTEM (the core of the pillar)

**27.1 The universal `about` facet.** Every instrument accepts the SAME astrological address
vocabulary, and the tools translate to storage — never the LLM:
`about: {graha | bhava | rashi | nakshatra | varga | yoga | karaka | dasha_period | domain | special_point}`
— e.g. `about:{graha:'Saturn'}` on signals_query, strength_query, graph_query, kala_query alike.
One vocabulary, sixteen instruments, zero translation burden on the endpoint.

**27.2 The ADDRESS RESOLVER (shared serving component; the one genuinely new architectural piece).**
Astrological indirection resolved server-side: `lord_of(bhava 7)` · `dispositor_of(Venus)` ·
`bhava_from(Moon, 10)` · `karaka('AK')` · `occupants_of(bhava 4, D9)` · chains like
`dispositor_of(lord_of(10))`. Input: an address expression; output: the resolved concrete entities +
the resolution chain (served, so the synthesis can SHOW its reasoning: "the 7th lord is Venus, placed
in the 9th…"). Backed by chart_facts + the CGM's dispositor edges — the data exists; the resolver is
a thin, cacheable, per-chart pure function. This single component is what lets the LLM ask questions
the way the shastra phrases them.

**27.3 REFERENCE FRAMES.** A `frame` facet on positional/strength/signal/judgment queries:
`frame: lagna (default) | chandra | surya | arudha | karakamsha | varnada`. Sudarshana practice
(judge from lagna AND Moon) becomes `frame:['lagna','chandra']` in ONE call, returning the comparison.
Today every surface is silently from-lagna — a whole classical discipline is unaddressable.

**27.4 The PARADIGM facet.** `paradigm: parashari (default) | jaimini | kp | tajika` — switches the
COHERENT interpretive frame: jaimini activates chara-karaka/arudha/rashi-drishti addressing; kp
activates sub-lord/cusp addressing; tajika activates varshaphala/saham. Prevents the subtle sin of
mixing paradigms mid-answer, and gives the triangulation register (A7) its clean per-paradigm inputs.
The signal store already carries signal_tradition; this facet makes it a navigation dimension.

**27.5 ASTROLOGICAL RESPONSE UNITS (completes §10.8).** Strengths serve as classical grade + number
(`shadbala: 5.2 rupas (strong, 78th pctl of exalted-Saturn class)`); aspects as drishti statements
("Saturn's full 3rd drishti on the 9th"); avasthas by name (Sanskrit + gloss); dignity as the
classical term. The closed epistemic vocabulary (§10.2) and the shastra vocabulary TOGETHER are the
response language.

## §28 — SHASTRA-SHAPED NAVIGATION

**28.1 `judgment_query` — the bhava-adhyaya recipe as one instrument** (generalizes the 4 apex tools
into the classical form). `judgment_query(about:{bhava:7} | {domain:'marriage'})` returns the COMPLETE
classical checklist pre-assembled: bhava condition · bhavesha condition + placement · karaka condition ·
occupants + aspecting grahas · from-lagna AND from-chandra · operative-varga confirmation status ·
bearing yogas (formed AND notably-absent, per §10.3) · promise-register verdict · timing hooks — each
element GRADED (epistemic + strength) with its resolution chain. One call = the acharya's first
working-through of the matter. The apex_* tools become intent-tuned entries into this recipe.

**28.2 `graha_portrait`** — the mirror recipe for graha-questions ("how is my Saturn?"): dignity chain
across operative vargas · shadbala decomposition · avasthas · yogas it participates in · its dasha
periods (past/next) · its CGM neighborhood · functional nature for this lagna. One call.

**28.3 THE PACT PROTOCOL — the predictive investigation grammar.** For A4/A5 (event, timing)
questions the capabilities card teaches the classical chain, not generic research:
`PROMISE (judgment_query on the matter) → CONFIRMATION (varga check via frame/varga facets) →
ACTIVATION (kala_query: which promise-carrier dashas, when) → TRIGGER (transit gates in-window) →
posterior (phala_query anchors)`. Each stage can HALT the chain classically ("the rashi does not
promise it — no dasha can deliver it") — which is both correct Jyotish and a token/latency win: a
denied promise ends the investigation in two calls, honestly. The generic orient→fan-out protocol
remains for open readings (A2); the card routes by answer type.

**28.4 ASTROLOGICALLY TYPED drill_pointers.** The closed pointer vocabulary becomes shastra moves:
`confirm_in_varga · check_from_moon · check_bhanga/cancellation · opposing_yoga · karaka_condition ·
dasha_of_promise · transit_gate · dispositor_chain · tail_dissent`. Every pointer is a classical next
step with its ready-to-fire request; the LLM's investigation reads like an acharya's worksheet.

**28.5 THE SHASTRA MAP (capabilities card).** The domain→bhava/karaka/varga/dasha-rule correspondence
table (marriage→7th/Venus/D9; career→10th/Sun-Mercury-Saturn/D10; …) served as the card's navigation
legend — sourced from the L0 ontologies that already store it. This makes the instrument
endpoint-agnostic: ANY product-policy LLM (Gemini/DeepSeek, weaker Jyotish priors than Claude)
navigates correctly because the map is in the contract, not in the model's memory.

**28.6 COVERAGE RECEIPTS IN CLASSICAL UNITS (upgrades §10.5).** A judgment answer's receipt reads:
`{bhava:✓, bhavesha:✓, karaka:✓, from_moon:✓, varga_confirmed:D9✓, yogas_checked:n, bhanga_checked:✓,
timing_anchored:✓}` — completeness AS THE TRADITION DEFINES IT. An A3 answer missing `from_moon` says
so. This receipt is also the §13 battery's grading rubric for judgment questions.

## §29 — THE RE-ARCHITECTURE VERDICT (considered honestly, as directed)

**Considered: full entity re-architecture** — regroup all instruments by astrological entity
(graha-instrument, bhava-instrument, …). **Rejected**, three reasons: (1) every entity-instrument
must internally fan across all six layers per call — heavier handlers, the §23 latency equation
worsens; (2) Part IV proved the data-family substrate maps cleanly onto real storage and mostly-built
handlers — discarding that is cost without capability; (3) the translation burden the entity-regroup
would remove is ALREADY removed one level up by §27's address system — same value, an overlay instead
of a rebuild.

**Adopted: the shastra speaks through the contract, not the table layout.** Estate = the 15 substrate
instruments + `judgment_query` + `graha_portrait` (17 total; apex_* fold INTO judgment_query as
aliases). The `about`/`frame`/`paradigm` facets + the address resolver + PACT protocol + typed
pointers + shastra map deliver the astrology-native navigation the native asked for — on the substrate
the audit validated. This is the significantly-increased-value path; a wholesale rebuild is not.

## §30 — WAVE ABSORPTION + ASTROLOGICAL ACCEPTANCE

W1 adds the ADDRESS RESOLVER (it's load-bearing for everything after) + `about` facet on the big four.
W2 adds frames + paradigm facets (graph + corpus waves need them anyway for jaimini/kp edges and
per-tradition citations). W3 builds `judgment_query` + `graha_portrait` + apex fold-in + the shastra
map + typed pointers. W4's battery gains the ASTROLOGICAL ACCEPTANCE CLASS: judgment questions graded
on classical-completeness receipts (§28.6); PACT questions graded on chain honesty (a denied promise
must halt, a delivered prediction must cite all four stages); frame questions verified from-Moon;
paradigm questions verified unmixed. An answer that is fast, cheap, and classically incomplete FAILS.

---

*One-line summary (v1.5, the whole design): a data plane the rebuild completes, instruments that
listen (facets), answers designed backwards from the user (Part II), premises verified in code
(Part IV), speed as a gated property (Part V) — and, governing all of it, navigation that thinks in
grahas, bhavas, karakas, vargas, and dashas, so that nothing is lost in translation between the
shastra and the person asking.*

---

# PART VII — ADVERSARIAL REVIEW + EXTERNAL CURRENCY (v1.6)

*The step-back critique, native-directed 2026-07-08. Three lenses: what the design itself missed,
what the moving MCP specification changes, and what industry guidance confirms or contradicts.
Run-mechanics findings are applied directly to the R5 run brief (v1.1); substance findings below.*

## §31 — SUBSTANCE GAPS THE CRITIQUE FOUND

**31.1 THE TOOL-LIST CONTEXT TAX (unmeasured until now).** Seventeen instruments with rich facet
schemas means a large tool-definition block injected into EVERY endpoint-LLM session — a per-session
token tax nobody was measuring, and rich schemas make it worse, not better. Contract: instrument
schemas stay LEAN (facet enums + one-line descriptions); all TEACHING (recipes, protocols, shastra
map, examples) lives on the capabilities card, fetched on demand. New gated metric in the battery:
**tool-definition footprint** (KB of the tools/list response) with a budget, tracked per wave like
latency. The consolidation 70→17 is itself the biggest win here — quantify it in the seal.

**31.2 TOOL-SELECTION ERGONOMICS EVAL.** The estate's navigability was asserted, never measured.
W3 gains a selection eval: a blind product-policy LLM given battery questions + only the tool list;
metric = correct-first-instrument rate (target ≥90%) and facet-well-formedness on first call.
Description engineering gets tuned against THIS metric, not taste.

**31.3 SESSION-PIN COLLISION.** The pin keys on (user, session-key) with session-key defaulting to
`"default"` — two concurrent conversations by the same user share one pin AND one active_chart:
a chart-context collision waiting to happen. Mitigations: chart_id stays explicit in every call
(never rely on active_chart for correctness, only convenience); the pin re-keys to (user,
session-key, chart_id); the capabilities card documents client session-key hygiene. Full fix rides
the MCP-elevation workstream (per-conversation keys are a client concern).

**31.4 BIRTH-TIME SENSITIVITY — the major astrological addition.** The native chart's own
rectification state is `unresolved` (train score 0.21) — and NOTHING in the serving contract
propagates birth-time uncertainty into answers. Astrologically this is a first-order honesty gap:
lagna-dependent claims degrade with time uncertainty, and varga fineness multiplies it (±4 minutes
moves the D60 lagna a full sign; D1 yoga claims survive what D60 claims cannot). Contract addition:
- every chart carries `time_confidence` (from ph_rectification state);
- every claim carries a `time_sensitivity` grade derived from what it depends on (lagna-degree <
  bhava-cusp < varga-lagna, scaled by varga fineness);
- judgment_flags surface the product: a D60-based claim on an unresolved-rectification chart serves
  as `time_sensitive_low_confidence` — or floors honestly.
This joins the §10.2 epistemic vocabulary as its temporal axis. It is also the serving-side twin of
the LEL work: as LEL events accrue and rectification confidence rises, the SAME claims upgrade
automatically. (Pratinidhi-R implements the sensitivity ladder with classical citation per varga.)

**31.5 BUILD PROVENANCE AT SERVE TIME.** Post-R4 there will be rebuilds; sessions must never blend
data across them silently. Envelope gains `build_id` (chart-level); the consistency invariant (E-4)
extends: one response = one build_id; a mid-session build change surfaces as a judgment_flag
("chart rebuilt mid-session; pin refreshed").

**31.6 THE RETRIEVAL TELEMETRY LOOP (L5's spirit applied to retrieval itself).** Investigation
protocols are advisory — nothing measures whether live sessions actually follow them (tail-checks
skipped? judgment receipts incomplete? drill_pointers ignored?). Addition: call-sequence telemetry
per session (tool, facets-shape, timing — no payload retention), analyzed OFFLINE against protocol
conformance; findings tune descriptions, card recipes, and pointer design. The instrument learns
how it is actually played — the same prediction→outcome discipline the L5 layer applies to
astrology, applied to retrieval.

## §32 — MCP-SPEC CURRENCY (the protocol moved; adopt deliberately, not reflexively)

| Spec feature (status) | Relevance | Adoption ruling |
|---|---|---|
| **Tool output schemas** (stable, 2025-06) | Declares what each instrument RETURNS — protocol-level kill of schema-theater (E-3); clients validate structured content | ADOPT in W1 with the generated contract: codegen emits outputSchema alongside input schema — one source, both directions |
| **Tasks extension** (2026-07-28 RC) | Long-running work: the Mahā-Brief and deep investigations are exactly this shape (initiate now, retrieve later) | ADOPT-WHEN-STABLE: design the Mahā-Brief endpoint Task-compatible in W4; flip to protocol Tasks when the RC lands in clients. Punch-list, not gate |
| **Elicitation** (stable) | Server-initiated structured questions to the USER — astrologically potent: PRASHNA needs the question-moment captured cleanly; clarifications (which marriage? whose chart?) become protocol, not prose | ADOPT in W3 for prashna question-capture + judgment_query disambiguation (form mode only; never credentials) |
| **Stateless core** (2026-07-28 RC) | Our session store is already DB-backed (mig 382) — ALIGNED by accident of good design; validates the §10.6 pin approach | No action; note in card |
| **OAuth/OIDC alignment** (RC) | Auth modernization | Routes to the MCP-elevation workstream (M0–M8), not R5 |

## §33 — CONVERGENCE CHECK vs INDUSTRY GUIDANCE (Anthropic tool-design lessons)

Independent convergence, which raises confidence: their `response_format`/verbosity parameter ≈ our
`shape`+`budget` facets; their pagination/filtering/truncation-with-steering ≈ our facet grammar +
trim_report; their namespacing ≈ our layer prefixes; their "evaluate with real agents, iterate" ≈
our battery-first waves; their "steer agents toward many small targeted searches" ≈ our card
protocols. One place we go FURTHER than the guidance: domain-semantic navigation (the shastra map,
astrological addresses) — justified because our domain has a real classical protocol most tool
estates lack. One place the guidance pushed us: keep schemas lean, teach in retrievable context
(→ §31.1). Sources: Anthropic engineering — writing tools for agents; MCP 2026-07-28 RC notes.

---

*One-line summary (v1.6): the design critiqued itself before the swarm builds it — the answer-side
gains time-honesty (birth-time sensitivity), the estate gains measured ergonomics (tool-list tax,
selection eval), the sessions gain collision-safety and build provenance, the instrument gains a
learning loop about its own use, and the whole thing tracks a moving protocol deliberately instead
of discovering it later.*
