---
artifact: LAYER_2_CHART_INTELLIGENCE_DESIGN_v1_0.md
canonical_id: LAYER_2_CHART_INTELLIGENCE_DESIGN
version: 1.1
status: CLOSED 2026-06-02 (design baseline — sealed in M5_REARCHITECTURE_DESIGN_CLOSE_v1_0; supersedes LAYER_2_SYNTHESIS_DESIGN_v1_0; build phase next)
authored_by: Claude (Cowork) 2026-06-02
changelog:
  - v1.1 (2026-06-02): Deep expansion — §D the Signal (every field, signal-type taxonomy, confidence
    + salience models), §E each component (context, full schema, build algorithm, worked example, LLM
    consumption), and expanded representations/pipeline/tools/storage/provenance.
  - v1.0 (2026-06-02): Initial reimagining (Chart Intelligence Layer).
supersedes: 00_ARCHITECTURE/LAYER_2_SYNTHESIS_DESIGN_v1_0.md
read_with:
  - 00_ARCHITECTURE/LAYER_1_STORAGE_STRATEGY_v1_0.md (the facts L2 consumes)
  - 00_ARCHITECTURE/LAYER_0_FOUNDATION_DESIGN_v1_0.md (rule base, concordance, ontology)
purpose: >
  The complete, field-level design of Layer 2 — the Chart Intelligence Layer. L2 is engineered to hand
  an LLM the maximally enriched, pre-digested intelligence about a chart: grounded, weighted, cited,
  contradiction-aware claims, available tabular + graph + vector — so the LLM's only job is synthesis
  and judgment, never data-wrangling or re-derivation.
---

# Layer 2 — Chart Intelligence Layer · Detailed Design (v1.1)

> **Project Brahma · external name: Bodha / Chart Intelligence.** Per BUILD_WORKFLOW_AND_TOOLING_DESIGN_v2_0 +
> BRAHMA_BUILD_UX_SPEC_v1_0: user-facing surfaces show "Bodha / Chart Intelligence" — never "L2", "MSR", "CGM",
> "CDLM", "RM" (internal docs keep these for precision). Bodha's heterogeneous assets each get their **own
> source-close retrieval tool** — `query_signals` (MSR, with domain/valence/confidence/salience filters),
> `cgm_subgraph` (graph traversal), `cdlm_lookup`, `rm_walk`, `query_remediation` — plus a composite
> `holistic_bundle` for whole-chart-read (B.11). Each tool is built, deployed to web + MCP, and tested against
> fresh data in the same swarm arc as its asset; the layer verifies only when assets **and** tools pass, with a
> volume-floor amber gate. (This is the worked example of why one-tool-per-layer is wrong — see v2.0 §L.)

## §A — What L2 is, and why it is shaped this way

L2 sits between the **facts** (L1 — precise, deterministic, exact-query) and the **answer** (the
query-time LLM). Its job is to convert facts into **intelligence**: not prose, not interpretation
frozen in a document, but a structured, queryable body of *grounded claims and their relationships*
that an LLM can stand on.

The design intent is a single sentence: **do every mechanical derivation here, so the LLM does none
of it.** When a user asks "what about this person's career?", we do not want the LLM to (a) recall
which houses/karakas govern career, (b) look up the facts, (c) apply classical rules, (d) check whether
schools agree, (e) work out timing, (f) decide what matters most. That is mechanical work, and any of
it the LLM does is work it does *imperfectly and unrepeatably*. L2 does all of it in advance and hands
the LLM the result: *the relevant grounded claims, how they connect, where they concentrate, where
they conflict, what's absent, when they activate, and how much each matters.* The LLM then does the one
thing only it can do well — **weigh, reconcile, and articulate**.

Four properties follow directly from that intent, and every design choice serves them:

- **Signal-centric.** The atomic unit is the *signal*: one grounded, falsifiable claim. Everything
  else — graph, lenses, indexes — is structure *over* signals. (Old L2.5 also centered on signals;
  we keep that and enrich it.)
- **Three representations of the same intelligence.** *Tabular* (Postgres — exact filter/lookup, and
  the substrate the rule engine writes), *graph* (valenced edges between signals — relational
  reasoning), *vector* (embeddings over signal claims — semantic search over meaning). The same signal
  is reachable by exact predicate, by traversal, and by similarity.
- **Cited and scored, end to end.** Every signal carries the L1 facts it rests on, the L0 rule/verse
  it applies, a confidence, and a salience. Nothing is unattributable; nothing is unweighted.
- **Contradiction-aware.** Disagreement — between signals, between schools, between systems — is
  recorded as first-class data, not smoothed away. For a research instrument the disagreements are
  often the most valuable output.

**What changed from the old L2.5 (and why):** the old stack was hand-verified and built for one
native; cross-system convergence was spotted by a human; the unified reading was a stored LLM essay.
The reimagined L2 is **chart-parameterized and rule-driven** (the classical judgment lives once in the
L0 Rule Base + Concordance, applied to any chart), **convergence is detected by the L0 Concordance**
(not a human), **the narrative is query-time** (not stored), and we **add** five enrichments the old
stack lacked: per-chart cross-school concordance, a temporal activation index, a salience ranking,
embeddings over signals, and an explicit derivation ledger on every signal.

## §B — Governing principles (with rationale)

1. **Pre-digest, don't defer.** Rationale: mechanical work the LLM redoes is done imperfectly and
   non-reproducibly. Move it here.
2. **Cite + score everything.** Rationale: grounding lets the LLM cite; confidence/salience let it
   calibrate and prioritize. An unscored claim is a liability.
3. **Surface contradictions.** Rationale: false certainty is the failure mode of astrology tools; honest
   tension is the research value.
4. **One signal corpus, many lenses.** Rationale: CDLM/RM/concordance/contradictions are *views over
   the signal graph*, not separately-authored artifacts — less to build, internally consistent.
5. **Vectorize processed data, never raw facts.** Rationale: facts are precise (exact retrieval wins);
   signals are semantic (similarity retrieval wins). Embeddings live here, not in L1.
6. **PyJHora-boundary.** L2 consumes L1 facts; it never invokes the engine.
7. **Tooling per the L0 standard** — one registry, MCP + internal API, capability-over-primitives,
   typed I/O with a provenance envelope, token-economical on-demand bundles.

## §C — Architecture overview

```
L1 Fact Store  +  L0 (Rule Base · Concordance · Ontology)
        │  L2 build job — per chart × selected ayanamsha (deterministic, content-addressed)
        ▼
2.1 SIGNAL CORPUS ───────── the atomic grounded claims (the spine)
        ▼
2.2 SIGNAL GRAPH ────────── valenced edges between signals (the reasoning substrate)
        ├── 2.3 DOMAIN LENS (CDLM)     — domain-pair aggregation over the graph (view)
        ├── 2.4 RESONANCE LENS (RM)    — focal-hub analysis over the graph (view)
        ├── 2.5 CONCORDANCE LENS       — per-chart cross-school agreement/divergence
        └── 2.8 CONTRADICTION LEDGER   — conflicts harvested from edges + concordance (view)
2.6 TEMPORAL ACTIVATION INDEX ──────── signals × dasha/transit windows
2.7 NEGATIVE-SPACE MAP ─────────────── expected-but-absent patterns
2.9 SALIENCE RANKING ──────────────── importance order over the corpus
2.10 CHART DIGEST (UCD) ────────────── read-time roll-up (not stored)

Representations:  tabular (Postgres) · graph (signal_edges + recursive CTE) · vector (pgvector over signals)
```

Data flow in prose: the build job loads the chart's L1 facts and the L0 knowledge (rules, concordance,
ontology). It **generates signals** by firing rules and detecting convergences; it **connects** them
into a valenced graph; it then computes the **lenses** (domain, resonance, concordance, contradictions)
as derivations over that graph, plus the **indexes** (temporal activation, negative space, salience),
and finally **embeds** the signals. Everything is written to Postgres (+ pgvector), keyed by
`(chart_id, ayanamsha_id, build_id)`, and exposed through typed retrieval tools.

## §D — The atomic unit: the Signal

### D.1 What a signal is
A **signal** is a single, atomic, **grounded, falsifiable claim** about the chart. "Atomic" = one
assertion, not a paragraph. "Grounded" = it names the exact L1 facts it rests on and the exact L0
rule/verse it applies. "Falsifiable" = it can in principle be checked against the chart and against
lived outcome. A signal is *not* an interpretation or a recommendation — it is a verified proposition
("Saturn, exalted in the 7th, forms Sasha Mahapurusha Yoga"), from which interpretation is later built.

### D.2 Schema — table `signals` (keyed by `chart_id, ayanamsha_id, build_id` + `signal_id`)

| Field | Type | Meaning | Example |
|---|---|---|---|
| `signal_id` | text PK | stable id | `SIG.000123` |
| `claim_text` | text | the assertion in natural language — the embeddable surface | "Saturn, exalted in the 7th house, forms Sasha Mahapurusha Yoga, granting disciplined authority expressed through partnership." |
| `claim_subject` | text (ontology id) | the focal entity | `graha.saturn` |
| `claim_predicate` | text (ontology id) | the structured relation | `forms_yoga` |
| `claim_object` | jsonb | the target/value | `{"yoga":"sasha_mahapurusha","house":7}` |
| `domains` | text[] | life domains touched, primary first | `["relationships","career"]` |
| `valence` | enum | benefic · malefic · mixed | `mixed` |
| `confidence` | numeric(4,3) | 0–1, computed (see D.4) | `0.95` |
| `salience` | numeric(4,3) | 0–1, computed (see E.9) | `0.88` |
| `school` | enum | parashari · jaimini · kp · tajaka · nadi | `parashari` |
| `signal_type` | enum | rule_fired · convergence_detected · structural (see D.3) | `rule_fired` |
| `rule_id` | text | the L0 rule applied (null for pure convergence) | `RULE.BPHS.MAHAPURUSHA.SASHA` |
| `source_citations` | text[] | L0 verse refs | `["BPHS.75.3","Phaladeepika.6.1"]` |
| `l1_fact_ids` | text[] | **derivation ledger** — the exact L1 facts consumed | `["positions:saturn","houses:7","strength:saturn.shadbala"]` |
| `focal_entity` | text | the node it centers on (for graph hubs) | `graha.saturn` |
| `activation` | jsonb | conditions that make it "live" | `{"dasha_lords":["saturn"],"transit":null}` |
| `anchors` | text[] | related signal_ids | `["SIG.000201","SIG.000044"]` |
| `provenance` | jsonb | engine/build metadata | `{"build_id":"…","computed_at":"…"}` |

Sibling table `signal_embeddings(signal_id, embedding vector(768), model)` — pgvector, HNSW index,
one row per signal, embedding the `claim_text` (optionally a `claim_text + mechanism` composite for
richer retrieval).

### D.3 The three signal types (and how each is generated)
- **`rule_fired`** — a classical rule from the L0 Rule Base whose **precondition holds** in this chart.
  Example: rule "an exalted graha in a kendra forms its Mahapurusha yoga" + the L1 facts (Saturn in
  Libra = exalted; 7th = a kendra) → signal. `confidence` = the rule's base confidence; `l1_fact_ids`
  = the facts that satisfied the precondition; `rule_id` set; `source_citations` from the rule.
- **`convergence_detected`** — *no single rule produces it*; it emerges because **multiple independent
  schools/systems assert about the same focal entity**. Example: Mercury is flagged vargottama
  (Parashari), Darakaraka (Jaimini), 11th sub-lord (KP), and current MD lord (dasha) — a convergence
  signal "Mercury is the chart's convergence focus." `rule_id` null; `confidence` = a function of the
  *breadth* of convergence (how many independent systems) × their individual strengths; the contributing
  signals become `anchors`.
- **`structural`** — a deterministic structural pattern elevated to a claim where there isn't a single
  one-line classical rule but the pattern is unambiguous (e.g., "a kendra–trikona raja yoga exists
  between the 9th and 10th lords"). Treated like rule_fired but flagged so the source is the structural
  detector rather than a verse.

### D.4 Confidence model (not arbitrary)
`confidence` is **computed**, never guessed:
- rule_fired → the rule's declared base confidence in L0 (some rules are categorical = ~1.0; some are
  indicative = lower), optionally adjusted by strength of the satisfying facts (e.g., how exalted).
- convergence_detected → `1 − Π(1 − sᵢ)` over the contributing systems' strengths `sᵢ` (breadth raises
  confidence), capped and floored.
- structural → the detector's declared confidence.
This makes confidence comparable across signals and auditable.

### D.5 Why these fields, for the LLM
`claim_text` + `claim_subject/predicate/object` give the LLM both a readable claim and a filterable
structure. `domains/valence/confidence/salience/school` let it select, weight, and attribute.
`l1_fact_ids + source_citations + rule_id` let it cite to fact and to verse. `activation` lets it
reason about timing. `anchors + focal_entity` feed the graph. The embedding lets it find the claim by
meaning when it doesn't know the exact predicate.

## §E — The components, in full detail

### 2.1 · Signal Corpus
- **Purpose / intelligence given:** the body of everything the chart *asserts*, each item grounded and
  weighted — the LLM's evidence base.
- **What it is:** the populated `signals` table (§D). Count is chart-dependent (the single-chart legacy
  corpus held ~573; the rebuilt corpus is generated per chart × ayanamsha).
- **Build algorithm:**
  1. For each rule R in the L0 Rule Base: evaluate R's precondition predicate against the chart's L1
     facts (and the in-memory fact graph). If it holds, instantiate a signal from R's assertion template,
     binding the chart's specifics; record the satisfying `l1_fact_ids`, `rule_id`, `source_citations`,
     `school`, `domains`, `valence`, base `confidence`.
  2. Run **convergence detection** (D.3): group facts/signals by `focal_entity`; where ≥ N independent
     systems assert about the same entity, emit a `convergence_detected` signal linking them as anchors.
  3. Run **structural detectors** for patterns without a single verse (raja-yoga combinations, etc.).
  4. **De-duplicate / merge** near-identical signals (same subject+predicate+object) keeping the richest.
- **Worked example:** Saturn in Libra (exalted) in the 7th (kendra) → rule_fired Sasha Mahapurusha signal
  (conf 0.95); Saturn also AmK (career karaka) and 7th-house occupant → a convergence signal "career and
  partnership share Saturn as backbone" linking the two.
- **LLM consumption:** `query_signals(domain='career', confidence>=0.7, active_on='2027-06-01')` → the
  relevant grounded claims, ready to cite.

### 2.2 · Signal Graph (CGM)
- **Purpose / intelligence given:** *how the claims relate* — what reinforces, what contradicts, what
  co-activates — so the LLM reasons about coherence and tension, not isolated facts.
- **Schema — table `signal_edges`** (keyed by chart): `edge_id, src_signal_id, tgt_signal_id,
  edge_type, valence(+/−), weight(0–1), rationale`.
- **Edge types + generation rules:**
  - `reinforces` — same valence AND (shared `focal_entity` OR shared domain OR src's object supports
    tgt's premise). `weight` ∝ degree of overlap.
  - `contradicts` — opposite valence on the same subject/predicate. `weight` ∝ the strength of each side.
  - `co_activates` — overlapping activation windows (same dasha lord/period).
  - `shares_focal` — same `focal_entity` (a structural grouping edge).
  - `derives_from` — src's L1 fact appears in tgt's premise chain (a provenance edge).
- **Build algorithm:** pairwise over signals (bounded — a chart has hundreds, not millions), apply the
  rules above; write edges with `rationale` (the human-readable reason). No graph DB — edges are rows.
- **Traversal:** recursive CTE. Example — everything reinforcing a seed claim within 2 hops:
  ```sql
  WITH RECURSIVE r AS (
    SELECT tgt_signal_id, 1 d FROM signal_edges
      WHERE src_signal_id=$seed AND edge_type='reinforces' AND chart_id=$1 AND ayanamsha_id=$2
    UNION ALL
    SELECT e.tgt_signal_id, r.d+1 FROM signal_edges e JOIN r ON e.src_signal_id=r.tgt_signal_id
      WHERE e.edge_type='reinforces' AND r.d<2)
  SELECT DISTINCT tgt_signal_id FROM r;
  ```
- **LLM consumption:** `query_signal_graph(seed_signal_id, edge_types=['contradicts'], depth=1)` →
  "what undercuts this claim?"

### 2.3 · Domain Lens (CDLM)
- **Purpose / intelligence given:** the chart's **cross-domain wiring** — which life areas move together,
  so the LLM knows what to fold in when answering about one domain.
- **Schema — materialized view `domain_linkages`** (9×9): `row_domain, col_domain, linkage_type
  (feeds/constrains/mirrors/amplifies/compensates/contradicts), mechanism, strength(0–1),
  direction(row→col/col→row/bi), valence, msr_anchors[], key_finding`.
- **Build algorithm (aggregation over the graph):** for each ordered pair (Dx, Dy): take signals tagged
  Dx and signals tagged Dy; collect `signal_edges` between the two sets; group edges by `edge_type`;
  the dominant type → `linkage_type`; Σ weights (directed Dx→Dy) → `strength`; `mechanism` = the
  highest-weight edge's `rationale`; `key_finding` = a templated one-line summary. Asymmetry is natural
  (the Dx→Dy edge mass differs from Dy→Dx).
- **Worked example:** Career (D1) and Relationships (D3): both sets contain Saturn-centered signals;
  the dominant edges are `shares_focal` (Saturn = AmK and 7th occupant) → `linkage_type=mirrors`,
  `strength≈0.9`, `key_finding`="career and partnership share Saturn as their structural backbone."
- **LLM consumption:** `query_domain_lens('career')` → the domains career pulls/pushes, with mechanisms.

### 2.4 · Resonance Lens (RM)
- **Purpose / intelligence given:** *where the chart concentrates*, and whether the concentration is
  harmonious or paradoxical — the chart's headline architecture.
- **Schema — table `resonance_elements`:** `element_id, focal_entity, member_signal_ids[],
  constructive_signal_ids[], destructive_signal_ids[], amplification_score, tension_score,
  net_resonance(STRONGLY_AMPLIFIED/TENSION_BEARING/MIXED), domains_primary[]`.
- **Build algorithm (hub analysis over the graph):**
  1. Compute, per `focal_entity`, its **degree** = number of signals referencing it.
  2. Take focal entities with degree ≥ threshold (the hubs).
  3. For each hub: gather member signals; partition their internal edges — `reinforces` → constructive,
     `contradicts` → destructive.
  4. `amplification_score` = Σ constructive weights; `tension_score` = Σ destructive weights.
  5. Classify: amp ≫ ten → STRONGLY_AMPLIFIED; both high → TENSION_BEARING (a structural paradox); else MIXED.
- **Worked example:** Mercury hub — 8 converging signals (vargottama, Yogi, DK, Karakamsa lord, MD lord,
  11th sub-lord, AL co-location, dispositor) mostly constructive, with destructive edges (rules the 6th;
  susupta avastha). amp ≫ ten with a notable tension → `STRONGLY_AMPLIFIED` element flagged "protect the
  6th-lord boundary."
- **LLM consumption:** `query_resonance(net_resonance='TENSION_BEARING')` → "the chart's central paradoxes."

### 2.5 · Concordance Lens (cross-school)  *[NEW]*
- **Purpose / intelligence given:** for any claim, **where the traditions agree, qualify, or disagree** —
  the research differentiator; lets the LLM speak in a multi-school voice instead of a single flattened one.
- **Schema — table `signal_concordance`:** `topic_id, signal_id, school_stances jsonb
  {parashari:asserts|qualifies|silent|contradicts, jaimini:…, kp:…, tajaka:…, nadi:…},
  agreement_level(0–1), divergence_notes, source_refs jsonb`.
- **Build algorithm:** for each signal, resolve its `topic_id` via the ontology; look up the topic in the
  **L0 Concordance** (which already maps per-school stances + verses); for each school, determine whether
  this chart's per-school facts trigger that school's stance (assert) or qualify/contradict it; record
  `school_stances`; `agreement_level` = (#assert − #contradict)/#schools-with-an-opinion.
- **Worked example:** a wealth signal where Parashari and Tajaka assert, Jaimini qualifies (via a Chara
  Karaka caveat), KP is silent → `agreement_level≈0.5`, `divergence_notes`="Jaimini conditions it on
  the Dhana karaka's dignity."
- **LLM consumption:** `query_concordance(signal_id)` → "Parashari and Tajaka assert; Jaimini qualifies;
  KP is silent."

### 2.6 · Temporal Activation Index  *[NEW]*
- **Purpose / intelligence given:** **when** each claim is live, pre-computed — so "what's happening in
  2027?" is an instant join, not a re-derivation.
- **Schema — table `signal_activation`:** `signal_id, activation_type(dasha/transit), period_ref(→ L1
  dasha period id or transit window), start_date, end_date, strength(0–1)`.
- **Build algorithm:** for each signal with a dasha activation condition, join to the L1 `dashas` table
  on the activating lord at the relevant levels (MD/AD/PD/SD) → emit one activation row per matching
  period with its dates; `strength` reflects the level (MD > AD > …) and the signal's confidence. Transit-
  activated signals define a condition that the on-demand transit engine resolves to windows (precompute
  only the headline ones).
- **LLM consumption:** `query_active_signals(date_range='2027-01-01..2027-12-31')` → the live claims for
  that year, ordered by strength.

### 2.7 · Negative-Space Map  *[pulled up]*
- **Purpose / intelligence given:** **what the chart lacks** — expected-but-absent patterns — closing the
  blind spot that "only what's present" creates.
- **Schema — table `negative_space`:** `absence_id, expected_pattern, why_expected(rule_ref),
  absent_feature, significance(0–1)`.
- **Build algorithm:** the L0 Rule Base includes **expectation rules** (precondition X ⇒ expect feature
  Y). For each, if X holds in the chart but Y is absent → log the absence with `why_expected` and a
  `significance` reflecting how diagnostic the absence is.
- **Worked example:** "9th lord strong (X) ⇒ expect a benefic link to the 5th (Y)"; X holds but Y absent
  → absence "dharma-to-progeny channel unsupported," significance 0.6.
- **LLM consumption:** `query_negative_space(domain?)` → what's structurally missing.

### 2.8 · Contradiction / Divergence Ledger  *[pulled up]*
- **Purpose / intelligence given:** **where things conflict** — between signals, schools, or systems —
  so the LLM gives honest nuance instead of false certainty.
- **Schema — table `contradictions`:** `contradiction_id, kind(signal_signal/cross_school/cross_system),
  a_ref, b_ref, description, severity(0–1), resolution_status(surfaced/qualified/unresolved)`.
- **Build algorithm:** (a) harvest `contradicts` edges from the graph → signal_signal; (b) harvest
  cross-school contradictions from `signal_concordance` → cross_school; (c) detect cross-system divergences
  (e.g., dasha-date deltas across systems) → cross_system. Log with severity + status.
- **LLM consumption:** `query_contradictions(domain?)` → the tensions to disclose.

### 2.9 · Salience Ranking  *[NEW]*
- **Purpose / intelligence given:** the chart's **priority order** — so the LLM leads with what matters
  and doesn't dump everything flat.
- **Where it lives:** `signals.salience` (computed) + a ranked view `signal_salience_rank`.
- **Salience function (deterministic, tunable):**
  `salience = w1·focal_strength_norm + w2·dasha_currency + w3·domain_reach_norm + w4·confidence
            + w5·concordance_breadth + w6·resonance_membership`
  - `focal_strength_norm` — normalized shadbala/strength of the focal entity (from L1).
  - `dasha_currency` — is the signal active now / activating soon (from the activation index).
  - `domain_reach_norm` — number of domains it touches, normalized.
  - `confidence` — the signal's confidence.
  - `concordance_breadth` — fraction of schools that assert it.
  - `resonance_membership` — bonus if it belongs to a STRONGLY_AMPLIFIED or TENSION_BEARING hub.
  Weights `w1..w6` are config, calibrated later against the prediction/outcome loop.
- **LLM consumption:** `query_top_signals(n=15, domain?)` → the headline items.

### 2.10 · Chart Digest (UCD)
- **Purpose / intelligence given:** a **one-shot structured overview** before drilling in.
- **What it is:** a **read-time** assembly (not stored): top-K salient signals + the strongest
  `domain_linkages` + the `resonance_elements` + the top `contradictions` + the most significant
  `negative_space` items → one structured object.
- **LLM consumption:** `query_chart_digest(chart_id, ayanamsha_id)`.

## §F — The three representations (when each is used)

- **Tabular (Postgres):** the default for exact, filterable retrieval (by domain, valence, confidence,
  salience, school, activation) and the write-target of the build job. The rule engine and most tools use it.
- **Graph (`signal_edges` + recursive CTE):** for relational questions — "what reinforces / contradicts
  X," "the cluster around Mercury." CDLM, RM, and the contradiction ledger are *views* over it.
- **Vector (`signal_embeddings`, pgvector HNSW):** for semantic questions where the predicate is unknown —
  "find signals about sudden reversals." `semantic_signal_search` returns candidates that the LLM then
  reasons over. The **only vectorized corpus besides L0 texts; L1 facts are never embedded.**

## §G — The L2 build pipeline (per chart × ayanamsha; deterministic, content-addressed)

1. Load L1 facts (Fact Store/JSONL) + L0 (rule base, concordance, ontology).
2. Generate signals (rule-fired + convergence + structural) → `signals`.
3. Derive edges → `signal_edges`.
4. Compute domain lens + resonance lens (views/derivations over the graph).
5. Compute concordance → `signal_concordance`.
6. Compute temporal activation → `signal_activation`.
7. Compute negative space → `negative_space`.
8. Detect contradictions → `contradictions`.
9. Score salience → `signals.salience` + rank view.
10. Embed signals → `signal_embeddings`.
- Runs as a Cloud Run Job after L1; idempotent; validated (row counts, anchor resolution, embedding
  coverage) before an atomic swap. A failed validation aborts (no partial intelligence layer).

## §H — Tools (the L2 retrieval surface; MCP + internal API, one registry)

Each is typed, provenance-bearing, token-economical, returns on-demand bundles:
`query_signals(filters)` · `query_signal_graph(seed, edge_types, depth)` · `query_domain_lens(dx, dy?)`
· `query_resonance(focal? | net_resonance?)` · `query_concordance(signal_id | topic)` ·
`query_active_signals(date|range)` · `query_negative_space(domain?)` · `query_contradictions(domain?)` ·
`query_top_signals(n, domain?)` · `query_chart_digest(chart_id, ayanamsha_id)` ·
`semantic_signal_search(query, k, filters)`.

## §I — Storage, keying, volume

- All tables keyed by `(chart_id, ayanamsha_id, build_id)`; Cloud SQL Postgres (+ pgvector for embeddings).
- Per chart per ayanamsha: ~hundreds–low-thousands of signals; a few thousand edges; small lens/index/
  ledger tables; one embedding per signal. A few MB — **far smaller than L1** (no dasha-row explosion).
- `build_id` versions every L2 build; the latest per (chart_id, ayanamsha_id) is active; priors retained.

## §J — Provenance & verification

- Every signal carries `l1_fact_ids` + `source_citations` + `rule_id`; every edge carries `rationale`;
  every lens cites its anchors; concordance cites per-school verses.
- Verification = internal consistency only: all `anchors`/`msr_anchors` resolve; all `rule_id`s exist in
  L0; determinism on the rule-fired parts (rebuild → identical signal set); FK integrity to L1;
  embedding coverage = 100% of signals. No JH oracle. Built + audited by the swarm.

## §K — Open decisions

1. **Domain taxonomy** — keep the 9 (Career/Wealth/Relationships/Health/Children/Spirit/Parents/Mind/
   Travel) or revise.
2. **Rule library identity** — confirm `signals.rule_id` resolves to the single L0 Rule Base (no duplicate).
3. **Salience weights** `w1..w6` — initial values + calibration plan against the prediction/outcome loop.
4. **Embedding model** — shared with the L0 decision.
5. **Layer assignment** of negative-space + contradiction ledger — kept at L2 for LLM adjacency; confirm
   vs formally L3.
6. **Edge-generation thresholds** (reinforces/contradicts weights) + the resonance hub-degree threshold —
   tunable; set initial values.

---

*End of LAYER_2_CHART_INTELLIGENCE_DESIGN v1.1 — DRAFT for native review, 2026-06-02. Field-level spec of
the Chart Intelligence Layer; supersedes the five-asset synthesis draft.*
