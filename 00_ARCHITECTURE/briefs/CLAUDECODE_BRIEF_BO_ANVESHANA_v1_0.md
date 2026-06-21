---
artifact: CLAUDECODE_BRIEF_BO_ANVESHANA_v1_0.md
canonical_id: BO_ANVESHANA_BRIEF
version: 1.2
status: FOR_NATIVE_REVIEW (the 9th asset — the DISCOVERY ENGINE; the asset that fulfills the absolute goal)
v1_2_changes: >
  SUBSYSTEM-AXIS discovery (native 2026-06-19 — closes a real gap: v1.1 was biased toward the STRUCTURAL
  subsystem because it mined chart-wide graph + embeddings). Discovery must be SUBSYSTEM-COMPLETE on TWO axes
  (§SUBSYSTEM): (1) INTRA-subsystem — run the discovery primitives WITHIN each subsystem against its OWN baseline
  (a nakshatra anomaly is anomalous vs the nakshatra distribution, not washed out by the whole chart); (2)
  CROSS-subsystem — the CROWN JEWEL: the root factor / convergence / contradiction that SPANS subsystems
  (nakshatra + medical + career-structural all tracing to one factor) — the insight NO specialist human can
  produce, because no human holds all subsystems in working memory at once. Cross-subsystem = the sibling of the
  CDLM pivot (root across DOMAINS); this is root across DISCIPLINES — distinct axes, both first-class, linked.
v1_1_changes: >
  The supreme drill (native 2026-06-19): seven improvements that take bo_anveshana from an ANOMALY DETECTOR to a
  RESEARCH-GRADE, TRUSTWORTHY discovery instrument (§SUPREME). All deterministic + additive + reopen nothing.
  D1 consequence-to-LIVED-IMPACT (not just graph topology); D2 the MEANINGFULNESS GATE (classical-form
  correspondence — promote only astrologically-defensible patterns to discoveries; statistical-only stays in
  bodha_anomalies, NOT dropped — reconciles the gate with no-drop); D3 cross-method CORROBORATION (a pattern found
  by multiple primitives is more trustworthy); D4 surface-vs-depth DELTA (the tension that makes it an insight);
  D5 FALSIFIABLE-HYPOTHESIS framing (each discovery a testable claim vs the LEL — the research loop); D6 NOVELTY
  tagging (chart-unique vs recurring-class; cross-chart correlation stays L5); D7 ruthless RANKING (sharp head,
  deep reachable tail — overcome attention limits, don't replace one overload with another).
authored_by: Cowork (deep-research synthesis over the whole L2 layer) 2026-06-19
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
scope: bo_anveshana ONLY (अन्वेषण = "investigation/discovery") — the NEW asset that MINES the other 7 Bodha assets at BUILD time for consequential NON-OBVIOUS patterns. NOT a producer of facts; a discoverer of insights. Depends on ALL other bo_* (it mines them; runs near-last, before bo_pramana_mapa).
data_plane: ALWAYS prod via Cloud SQL Auth Proxy (127.0.0.1:5433)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
governing:
  - L2_BODHA_DISCOVERY_MISSION_v1_0.md (the strategic rationale — the absolute goal this asset fulfills)
  - L2_BODHA_JUDGMENT_SUBSTRATE_STRATEGY_v1_0.md (v1.1 FROZEN — discovery inherits provenance/epistemic/anti-drift)
  - L2_BODHA_STORAGE_ARCHITECTURE_v1_0.md (§STORAGE — graph + embeddings as DISCOVERY instruments, not just lookup)
  - ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 (FROZEN WriterBase)
target_files:
  - platform/python-sidecar/pipeline/orchestrator/writers/bo_anveshana.py (NEW — the discovery miner; igraph + embeddings + stats)
  - new migration: CREATE bodha_discoveries (+ bodha_anomalies) + bo_anveshana asset_registry seed
  - platform/python-sidecar/bodha_writers/formulas.py (ADD non_obviousness_formula_v1)
  - platform/src/lib/retrieval/registry/layers/L2_bodha/ (the discovery retrieval surface)
must_not_touch: FROZEN orchestrator contract; ga_* writers; the other bo_* writers (it READS + mines them).
---

# bo_anveshana — the DISCOVERY ENGINE (unearthing what no acharya can hold)

## §0 — Why this asset exists (the absolute goal)
An acharya holds ~7±2 chart factors in working memory; a chart has thousands of facts + millions of multi-entity
relationships across 30 vargas × 5 ayanamshas. The acharya, by cognitive necessity, PRUNES — and the consequential
pattern that lives in the interaction of the 40th-salient factor with the 200th, three hops down a chain, in D24,
they NEVER SEE. Not from lack of skill — no human brain can hold it. **The unique value of this instrument is to
surface exactly that: the consequential pattern BELOW THE WATERLINE OF HUMAN ATTENTION.** The other 7 assets built
a substrate from which discovery is POSSIBLE (no-pruning, full graph, deep chains, the pivot). bo_anveshana is the
ENGINE that FULFILLS it — it mines that substrate at build time for the consequential NON-OBVIOUS patterns and
surfaces them as first-class, ranked, retrievable insights. Without it: a magnificent library. With it: a researcher.

**The reframe that makes this asset different from all others:** every other asset is QUERY-DRIVEN (the LLM asks,
it answers). Discovery is the OPPOSITE causality — **the insight must announce itself even when no one asked the
right question, because the whole point is the acharya didn't know to ask.** So discoveries are PRE-COMPUTED at
build time, ranked, and the digest LEADS with them.

## §1 — Non-negotiables
Deterministic-first (graph algorithms + embedding math + statistics are all deterministic; NO LLM, NO generative
judgment); no audience tier; no silent drops; per-chart isolation; **Trap 1** (every discovery REFERENCES the
signal/node/path ids + L1 fact_ids it's built from — never restates values, never INVENTS a pattern not in the
data); **Trap 2** (non_obviousness_formula_v1 + the anomaly thresholds are versioned; no narrative — it points to
the pattern + its chain, the LLM narrates); FROZEN orchestrator contract (`@register('bo_anveshana')` WriterBase
on ctx.db_conn, never commits, no asset_throughput; depends_on all producing bo_* so it runs near-last); floors aspirational.
**A discovery is a found pattern, never a fabricated one — it must trace to real substrate (anti-drift absolute).**

## §2 — Preconditions
1. Proxy up; main == prod; max migration verified.
2. **ALL producing bo_* assets built** (it mines bo_laksana/sangati/karanajala/bimba/samskara/upaya + reads the
   gestalt) — it runs after them, before bo_pramana_mapa (which audits it too).
3. `igraph` available; the embeddings populated (bo_samskara real vectors — the outlier detection needs them).
4. Apply the NEW bodha_discoveries + bodha_anomalies migration + the bo_anveshana asset_registry seed.

## §3 — THE DISCOVERY TOOLKIT (the data-engineering shift: graph + embeddings as DISCOVERY instruments)
Use the substrate we built for LOOKUP as instruments for MINING. Four deterministic discovery primitives:

### §3.1 — NON-OBVIOUSNESS scoring (the core metric — "buried gold")
The acharya finds obvious-and-strong; the machine's unique value is BURIED-and-strong. Compute, per signal/
node/pattern, a `non_obviousness_score` (non_obviousness_formula_v1) = HIGH structural consequence × LOW surface
salience. Structural consequence = (centrality + convergence participation + on-critical-path + pivot-proximity).
Surface salience = the raw computed_salience an acharya would notice. **A factor that is structurally consequential
but low in surface-salience (weak graha / obscure varga / far down a chain) is a LATENT INSIGHT** — flag it. This
is THE discovery surface: high consequence + deeply buried = the thing no acharya would have looked at.

### §3.2 — GRAPH MINING (igraph's discovery algorithms — we currently use ~30%)
Run over bodha_cgm_edges/nodes:
- **STRUCTURAL HOLES / BROKER detection** — the node that BRIDGES two otherwise-disconnected parts of the chart
  (Burt's structural holes / high betweenness + low clustering). "This factor connects two worlds that otherwise
  wouldn't connect" — a non-obvious-broker insight an acharya cannot see by inspection.
- **COMMUNITY detection** (beyond the existing clusters) — natural sub-structures + the factors that BIND them.
- **MOTIF-FREQUENCY anomalies** — a configuration that recurs UNUSUALLY often (or uniquely) in THIS chart.
- **Articulation points / bridges** — the single factor whose removal fragments the chart (a structural keystone).

### §3.3 — EMBEDDING OUTLIER detection (the unused discovery primitive)
Over bodha_signal_embeddings: the signal whose meaning-vector is FAR from every cluster centroid is, by
construction, the chart's UNUSUAL factor. Compute per-signal distance-to-nearest-cluster; flag the top outliers.
(We currently use embeddings only for similarity retrieval — this turns the same vectors into a surprise detector.)

### §3.4 — DISTRIBUTIONAL within-chart anomalies (cheap, deterministic)
Compute the DISTRIBUTION of salience / centrality / convergence / linkage across THIS chart; flag genuine
statistical outliers (e.g. a factor ≥ Nσ above this chart's OWN mean). The thing that stands out from the chart's
own baseline is exactly what pattern-matching humans miss and a statistical engine catches. Store in bodha_anomalies.

## §4 — THE OUTPUT: bodha_discoveries (pre-computed, ranked, the digest leads with these)
Per (chart, ayanamsha), compose the ranked DISCOVERY LIST — "the N most consequential NON-OBVIOUS patterns in this
chart that a thorough acharya would most likely have MISSED." Each `bodha_discoveries` row:
- `discovery_id`, chart/ayanamsha/build, `discovery_class` (latent_insight | structural_hole | community_binder |
  motif_anomaly | embedding_outlier | distributional_anomaly | pivot_consequence),
- `non_obviousness_score` + `consequence_score` + `composite_discovery_rank`,
- `constituent_refs_jsonb` — the signal/node/path/fact ids it's built from (Trap 1 — REFERENCES, never invents),
- `reasoning_chain_jsonb` — the deterministic chain that PROVES it (so the LLM narrates the mechanism, not a claim),
- `why_an_acharya_misses_it` — the deterministic reason (buried in D24 / low surface salience / 3-hops deep / cross-varga only),
- `affected_domains_array` + epistemic_jsonb (confidence + ayanamsha-fragility — inherits Move 3) + provenance.
**This is the asset's reason to exist: a standing, retrievable list of the chart's below-the-waterline insights,
ranked by consequence, each with the chain that proves it — available WITHOUT anyone knowing to ask.**

## §5 — Anti-drift + verification (discovery must be FOUND, never FABRICATED)
1. **Every discovery's `constituent_refs` resolve to real substrate rows** (Trap 1; zero unresolved; a discovery
   that doesn't trace to the data is a HALT-worthy bug — the gravest error here, since a fabricated "insight" is worse than none).
2. **Reasoning chain validity:** each step in reasoning_chain_jsonb is a real edge/path/relationship in the substrate.
3. **Acharya-miss plausibility check:** the top discoveries are genuinely non-obvious (low surface salience) AND
   genuinely consequential (high structural score) — spot-check that the list isn't just re-surfacing the obvious
   chart-defining threads (those belong to the gestalt; discoveries are the COMPLEMENT — the buried ones).
4. **Determinism:** rebuild → identical discovery list + ranks (the discovery is a property of the chart, not of a run).
5. Idempotent; no silent drops; FORENSIC unaffected.

## §6 — Integration: the digest LEADS with discoveries; the scorecard audits them
- **bo_samvada (gestalt):** add a `top_discoveries` pointer block — the digest's "what am I missing" surface is now
  POWERED by bo_anveshana (the §5.A bo_drishti outliers + these build-time discoveries). The LLM's FIRST call now
  surfaces the buried insight, not just the obvious gestalt.
- **bo_pramana_mapa (scorecard):** audits discovery anti-drift (refs resolve) + that discoveries are genuinely
  non-obvious (not duplicating the gestalt) + the determinism check.
- **bo_drishti (lens):** a question-lens can pull the domain-relevant DISCOVERIES (the buried career insight), not just the template + signals.

## §STORAGE COMPLIANCE (storage §4B)
- **Graph + embeddings as DISCOVERY instruments** (S1/S4 extended — run the MINING algorithms igraph offers, not
  just the lookup ones; use the embedding vectors for outlier detection). This is the data-engineering elevation.
- **S5:** discovery_class, scores, ranks = real indexed columns; the refs/reasoning/chain = jsonb. **S2:** chart_id leads.
- No new embedding model (reuses bo_samskara's vectors — the consistency protocol already covers them).

## §7 — Retrieval (discovery, made reachable WITHOUT asking)
Extend `L2_bodha/`: `query_discoveries(chart, top_k|domain?|class?)` → the ranked buried insights WITH their
reasoning chain + why-an-acharya-misses-it + provenance + confidence. `query_anomalies(chart)` → the intra-chart
statistical/structural outliers. These are surfaced PROACTIVELY (the digest leads with them) AND queryable. Coverage gate.

## §8 — Acceptance
- [ ] **Non-obviousness score** (high consequence × low surface salience) computed per signal/node/pattern; latent insights flagged.
- [ ] **Graph mining:** structural holes/brokers + community binders + motif anomalies + articulation points (igraph discovery algorithms, not just lookup).
- [ ] **Embedding outliers:** signals far from every cluster flagged (the unused primitive now used).
- [ ] **Distributional anomalies:** within-chart Nσ outliers in salience/centrality/convergence → bodha_anomalies.
- [ ] **bodha_discoveries:** ranked discovery list; each row references real substrate (Trap 1), carries the reasoning chain + why-an-acharya-misses-it + epistemic.
- [ ] **Anti-drift absolute:** every discovery traces to real data (zero fabricated); reasoning-chain steps are real edges; determinism (rebuild → identical).
- [ ] **Not duplicating the gestalt** — discoveries are the BURIED complement, not the obvious threads.
- [ ] **D1 lived-impact:** consequence scored astrologically (CDLM ledgers / pivot / karaka / domain), not just graph topology.
- [ ] **D2 meaningfulness gate:** only classically-form-corresponding patterns PROMOTED to bodha_discoveries; statistical-only stays in bodha_anomalies (no-drop held); meaningfulness_basis stored.
- [ ] **D3 corroboration:** corroborating_methods_array + count; multi-method convergence multiplies rank (independent methods only).
- [ ] **D4 surface-vs-depth delta:** surface_reading + depth_reading + the delta stored (the delta IS the discovery).
- [ ] **D5 falsifiable hypothesis:** hypothesis_text + falsifier (vs LEL) + calibration_hook on each discovery.
- [ ] **D6 novelty:** novelty_class (chart_unique | instance_of_known_class) + class id; cross-chart correlation NOT computed (L5).
- [ ] **D7 ruthless ranking:** top 5–10 surfaced (digest leads); full set reachable on demand.
- [ ] **S.1 INTRA-subsystem:** primitives run WITHIN each subsystem vs its OWN baseline; discovery_subsystem tag; nakshatra/medical/vastu/etc. each yield buried insights (not washed out by whole-chart baseline).
- [ ] **S.2 CROSS-subsystem (CROWN):** cross_subsystem_root + convergence + contradiction found (factor/theme spanning subsystems); ranked HIGHEST; distinct-but-linked to CDLM pivot (may cite it).
- [ ] **S.3 coverage manifest:** every subsystem mined intra; cross-subsystem count emitted; un-mined subsystem visible (scorecard audits).
- [ ] Integration: digest leads with top_discoveries; lens pulls domain discoveries; scorecard audits.
- [ ] query_discoveries + query_anomalies tools; coverage gate; storage compliance; FROZEN contract; migration + seed fresh.

---

# §SUBSYSTEM — discovery must cut ACROSS ALL subsystems, on TWO axes (native 2026-06-19 — the crown of the engine)
*The gap v1.1 left: mining chart-wide graph + embeddings biases discovery toward the STRUCTURAL subsystem. But
discovery has value WITHIN each subsystem AND — most of all — ACROSS them. This §is the highest-value part of the
whole asset.*

**The subsystems (each maps to source_l1_asset, already tagged by bo_laksana):** structural (ga_structural),
nakshatra (nakshatra writers / ga_sensitive), strength/ashtakavarga (ga_strength), medical (ga_medical), vastu
(ga_vastu), yoga (ga_yoga), tajaka/annual (ga_tajaka), sade-sati (ga_sade_sati), panchanga (ga_panchanga),
divisional/varga (ga_vargas). The `source_l1_asset` tag is the subsystem axis — the substrate already exists.

## §S.1 — INTRA-subsystem discovery (each subsystem's OWN buried insights)
Run the four discovery primitives (non-obviousness / graph-mining / embedding-outlier / distributional-anomaly)
WITHIN each subsystem, judged against THAT SUBSYSTEM'S OWN baseline — a nakshatra anomaly is anomalous vs the
nakshatra distribution; an ashtakavarga-starved house vs the bindu distribution; a medical body-part cluster vs
the medical baseline. (Judging against the whole-chart baseline would WASH OUT subsystem-local insights — a
nakshatra pattern looks unremarkable against thousands of structural facts.) Each subsystem yields its own
below-the-waterline discoveries that even a SPECIALIST in that system might miss. `discovery_subsystem` tag on each.

## §S.2 — CROSS-subsystem discovery (THE CROWN JEWEL — the insight no specialist human can produce)
A human acharya is usually a SPECIALIST — reasons in nakshatras, OR body-parts, OR directions. **Almost no human
holds ALL subsystems simultaneously to spot a pattern that only emerges when you CROSS them.** A computer can. This
is the PUREST expression of the absolute goal. Hunt explicitly for:
- **Cross-subsystem ROOT** — a single factor that surfaces as significant in MULTIPLE subsystems (an afflicted
  Saturn that is a nakshatra vulnerability AND a medical knee-weakness AND a D10 career affliction). **Mechanism:
  MINE the CGM cross-subsystem EDGE family (bo_karanajala §XS) — these relationships are now STORED first-class
  edges (shared-root / classical-cross-discipline / shared-domain), NOT re-derived here.** bo_anveshana reads them +
  ranks; it does not construct them. (Where a cross-subsystem edge is missing, fall back to fact_id intersection +
  FLAG it as an un-stored relationship for the CGM brief — but the primary path is mining the stored edges.)
  `cross_subsystem_root` discoveries — ranked highest.
- **Cross-subsystem CONVERGENCE** — N independent subsystems pointing at the SAME life-theme (weight of evidence
  across DISCIPLINES, not just signals) — the strongest possible corroboration (extends D3 corroboration to the subsystem axis).
- **Cross-subsystem CONTRADICTION** — one subsystem says strength, another says vulnerability for the same entity
  (strength subsystem: strong shadbala; medical subsystem: affliction) — a genuine tension a specialist would never see.
**Relationship to the CDLM pivot (distinct-but-linked, native decision):** CDLM pivot = root across life-DOMAINS
(career+wealth+marriage); cross-subsystem = root across ANALYTICAL DISCIPLINES (nakshatra+medical+structural).
DISTINCT axes (life-area vs discipline), both first-class; a cross-subsystem discovery MAY cite the CDLM pivot as a
constituent where they coincide. Keep them clean; let them reinforce. **Cross-subsystem discoveries are the
highest-value class in the engine — the digest's discovery-lead prioritizes them.**

## §S.3 — Subsystem coverage manifest (completeness on the discovery axis)
Emit a per-subsystem discovery-coverage row: did EVERY subsystem get mined intra (≥ its discovery pass ran), and
how many cross-subsystem patterns were found. So a subsystem silently un-mined is VISIBLE at build time (bo_pramana_mapa audits it).

---

# §SUPREME — from an ANOMALY DETECTOR to a RESEARCH-GRADE, TRUSTWORTHY discovery instrument (drill 2026-06-19)
*A discovery engine has failure modes the other assets don't: it can discover NOISE dressed as insight, the
OBVIOUS called buried, a statistically-real-but-meaningless pattern, or 500 "discoveries" that drown the one that
matters. Supreme = it discovers things that are REAL, CONSEQUENTIAL FOR THE LIFE, astrologically MEANINGFUL,
genuinely NON-OBVIOUS, CORROBORATED, EXPLAINED, FALSIFIABLE, and ranked so the human can act. An engine that
discovers but can't be TRUSTED is worse than none. All seven below are deterministic + additive.*

## §D1 — CONSEQUENCE = LIVED IMPACT, not just graph topology
"Structurally consequential in the graph" ≠ "consequential for the person's LIFE." A factor can be a graph broker
and astrologically minor. So `consequence_score` is scored ASTROLOGICALLY, not just topologically: does the buried
pattern bear on a major life DOMAIN (via the CDLM ledgers), touch a chart-defining thread, connect to the PIVOT,
involve a strong karaka? `non_obviousness_score` stays (× low surface salience); the discovery rank = non-obvious
× LIVED-consequence. Surfaces life-insights, not graph-curiosities.

## §D2 — THE MEANINGFULNESS GATE (classical-form correspondence — noise vs real; reconciled with no-drop)
A chart has millions of relationships; BY CHANCE some are outliers/brokers/embedding-far. NOT every anomaly is an
insight. **A pattern is promoted to a first-class DISCOVERY (bodha_discoveries) ONLY if it corresponds to a
classically-recognizable FORM of significance** — a real relationship type (aspect/dispositor/argala/yoga-form),
a karaka/domain tie, a defined structural pattern — even if UNNAMED. A purely-numerical outlier with NO
astrological form stays in `bodha_anomalies` as a statistical CANDIDATE (NOT dropped — no-drop pillar holds; still
reachable for research) but is NOT promoted to a discovery. **This is the deepest quality lever: it stops the
engine crying wolf so the one real insight doesn't drown.** Gate is deterministic (match against L0 catalog forms
+ the graph's defined edge types). `meaningfulness_basis` stored (the classical form it corresponds to).

## §D3 — CROSS-METHOD CORROBORATION (weight-of-evidence applied to discovery)
The four primitives (non-obviousness, graph-mining, embedding-outlier, distributional-anomaly) run in parallel —
now CROSS-REFERENCE them. A pattern found by MULTIPLE independent methods (e.g. BOTH a graph broker AND an
embedding outlier AND a distributional anomaly) is far more likely REAL than a single-method flag. Store
`corroborating_methods_array` + a `corroboration_count`; corroboration is a confidence MULTIPLIER on the discovery
rank. The methods VOTE; convergence across methods is itself a discovery-strength signal (independence dedup applies
— same as the evidence ledger: methods must be genuinely independent).

## §D4 — SURFACE-vs-DEPTH DELTA (the tension that MAKES it an insight)
A discovery LANDS when it articulates the GAP between the surface reading and the deep reading. Compute + store
`surface_reading` (what the chart's surface salience suggests — "a minor debilitated planet, ignored") vs
`depth_reading` (what the deep structure reveals — "the hidden hinge of three life domains") and the explicit
`surface_depth_delta`. THAT DELTA IS THE DISCOVERY. The LLM narrates "on the surface X, but in depth Y" — the
contrast that turns a fact into an insight.

## §D5 — FALSIFIABLE-HYPOTHESIS framing (the research-instrument loop — the north-star alignment)
A research instrument generates TESTABLE CLAIMS, not oracle pronouncements. Each discovery is framed as a
FALSIFIABLE hypothesis: `hypothesis_text` ("this buried pattern predicts tendency X in domain Y") +
`falsifier_jsonb` (what would CONFIRM or REFUTE it against the native's life events — read the LEL) +
`calibration_hook` (empty, L4/L5 fill with observed outcome). This turns discoveries from clever observations into
testable claims the instrument can VALIDATE against lived reality — the engine of a research DISCIPLINE, not a reading.

## §D6 — NOVELTY tagging (chart-unique vs recurring-class; cross-chart stays L5)
Tag each discovery `novelty_class` ∈ {chart_unique, instance_of_known_class} + the class id. A chart-unique
discovery = a personal insight; an instance of a recurring class = a potential RESEARCH finding. **The class is
tagged HERE (within-chart); whether the class is empirically MEANINGFUL across charts is established by L5
Mīmāṃsā — NEVER computed here** (the within-chart/cross-chart boundary stays clean). This is the L2→L5 bridge.

## §D7 — RUTHLESS RANKING (sharp head, deep reachable tail — overcome attention limits, don't recreate them)
A discovery engine returning 500 "discoveries" has FAILED even if all are real — it replaces one overload with
another, defeating the whole purpose (overcoming human attention limits). So: the digest LEADS with the top 5–10
(by non-obvious × lived-consequence × corroboration × meaningfulness); the full ranked set is reachable ON DEMAND
(no-drop). The CURATION OF THE HEAD matters more here than anywhere else in the layer.

---

# §ELEVATION (toward supreme)
- **A-1 [discovery] Discovery TYPING by acharya-school** — flag whether a discovery would be missed by ALL schools
  or only some (a Jaimini-only insight a Parashari acharya misses) — the cross-tradition blind-spot surface.
- **A-2 [research] Discovery NOVELTY register** — across charts (L5), which discovery-CLASSES recur — feeding the
  research mission (does "structural-hole brokers in D10" correlate with career pivots empirically?). The L2→L5 bridge.
- **A-3 [retrievability] "Tell me something I don't know" tool** — the literal embodiment of the goal: a tool that
  returns the single highest non-obviousness × consequence discovery, with its proof. The instrument's signature capability.
- **A-4 [depth] Counter-intuitive PAIR discovery** — two factors that individually look one way but TOGETHER reverse
  the reading (a strength that becomes a vulnerability in combination) — the deepest below-the-waterline pattern.

---
*End of BO_ANVESHANA v1.0. The DISCOVERY ENGINE — the asset that fulfills the absolute goal: unearthing the
consequential pattern BELOW THE WATERLINE of human attention, the insight no acharya can hold because the
combinatorial depth exceeds working memory. It MINES the substrate the other 7 assets built (no-pruning, full
graph, deep chains, the pivot) using graph-discovery algorithms + embedding outliers + distributional anomalies,
composed into the NON-OBVIOUSNESS score (high consequence × low surface salience = buried gold). Outputs a
pre-computed, ranked, provenance-bearing DISCOVERY LIST the digest LEADS with — discovery that announces itself
WITHOUT anyone knowing to ask. Deterministic, anti-drift-absolute (found never fabricated). This turns the
complete, retrievable library into a RESEARCHER.*
