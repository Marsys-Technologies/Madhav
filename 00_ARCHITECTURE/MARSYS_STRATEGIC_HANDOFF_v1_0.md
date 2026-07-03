---
artifact: MARSYS_STRATEGIC_HANDOFF
canonical_id: MARSYS_STRATEGIC_HANDOFF
version: 1.0
status: CURRENT — paste into a fresh Cowork conversation to open the STRATEGIC workstream
created: 2026-07-01
author: Cowork (MCP-elevation + system-audit conversation) — strategic inheritance for native Abhisek Mohanty
classification: strategic conversation handoff / complete-understanding primer (zero-context-loss)
purpose: give a brand-new Cowork conversation the full strategic picture — with DATA (astrological) as the
  spine — needed to drive the project toward its north star: synthesizing acharya-grade-AND-BEYOND astrological
  insight, guidance, prophecy, and interpretation across the data, code, and systems planes.
north_star: >
  An LLM, fronted by this instrument, generates astrological insight of a depth, cross-layer integration, and
  calibrated confidence that exceeds what any individual acharya could hold in working memory or derive by hand
  — not by replacing the tradition, but by holding the WHOLE chart across all systems at once, surfacing the
  convergences and contradictions no human can track, and reconciling them into guidance/prophecy/interpretation
  that is grounded, cited, falsifiable, and calibrated against lived outcomes.
---

# MARSYS-JIS — STRATEGIC HANDOFF (data-first; the path to beyond-acharya insight)

> **How to use this.** Paste this as the first message of a new Cowork conversation dedicated to the STRATEGIC
> aspects of the project. It carries the north star, the honest current reality (a live audit just completed),
> and — most importantly — a deep treatment of the DATA plane from an astrological standpoint: what exists, how
> it is structured, and how it must be ENRICHED so that an LLM can synthesize it into insight, guidance,
> prophecy, and interpretation at a level beyond individual human comprehension. Data is #1. The enabling
> systems (retrieval, MCP channel, synthesis, calibration) are #2 — necessary, but in service of the data.

---

## §0 — THE NORTH STAR (what "beyond-acharya" concretely means)

An acharya reading a chart is limited by working memory: they can hold perhaps a few dozen factors at once —
key yogas, the dasha lord's condition, a handful of transits, one or two divisional charts. This instrument's
reason for existing is to **transcend that bound**: to hold *the entire chart across every system simultaneously*
— all divisionals, all strength models, all dashas, all transits, the full yoga inventory, the nakshatra
substructure, the ashtakavarga lattice — and to surface the **convergences and contradictions across those
layers that no human can track**, then reconcile them into a calibrated, cited, falsifiable reading.

"Beyond acharya" is therefore NOT "more mystical." It is: **(1) completeness** (nothing in the chart is unseen),
**(2) cross-layer integration** (the D10 tenth-lord's dignity read *together with* its ashtakavarga strength
*together with* its dasha activation *together with* the transit trigger — as one judgment), **(3) contradiction-
holding** (surfacing where the chart says opposite things and weighing them, rather than cherry-picking), and
**(4) calibration** (confidence tied to how the same configuration resolved in real lives). The four outcomes
the native wants — **insight, guidance, prophecy, interpretation** — are all downstream of getting those four
things right. And all four are downstream of the DATA being rich enough, and structured enough, to support them.

---

## §1 — PROJECT FRAME (one paragraph)

MARSYS-JIS is an LLM-operated Jyotish (Vedic astrology) instrument for native Abhisek Mohanty (canonical
chart_id `482012f1-710e-4a25-994a-93821f5871aa`; born 1984-02-05, 10:43 IST, Bhubaneswar). It is built in six
layers — **L0 Brahmagyan** (foundation/reference data), **L1 Gaṇita** (deterministic computed chart facts),
**L2 Bodha** (synthesis/relational signal layer), **L3 Kāla** (temporal/timing), **L4 Phala** (prediction),
**L5 Mīmāṃsā** (calibration/learning) — comprising 85 build assets (live count via list_assets) in Postgres, fronted by a retrieval system
that serves two channels (an external MCP server for BYO-LLM clients, and an internal chat engine) across four
LLM families. All six build layers are sealed/closed; the instrument runs per-chart on demand. Governance is
deliberate: facts/interpretation separation (B.1), derivation-ledger mandate (B.3), whole-chart-read discipline
(B.11), reference-don't-restate grounding (§N.5), chart-agnostic zero-native-contamination (#14). Cowork plans
+ briefs; Claude Code in Antigravity implements.

---

## §2 — HONEST CURRENT REALITY (a live 360° audit just finished — read this before strategizing)

A full system audit was just run FROM a live MCP connector (a real external LLM exercising every tool). The
finding that matters most for THIS conversation:

**The data is rich, correct, and honestly engineered — but the JUDGMENT layer that turns data into insight is
the frontier.** Specifically, per chart the system holds ~**64,765 MSR signals**, **140 CGM causal-graph nodes**,
**365–508 graph edges**, **70 CDLM domain-activation cells**, ~95% two-pass-verified, every signal cited. The
raw material is genuinely there and the natal facts are correct against the 7 FORENSIC birth anchors. BUT:

- **The salience model is astrologically wrong.** For a *career* query, the top-ranked signals are 96% Saturn
  ashtakavarga bindu-counts in exotic sub-vargas (up to D2700), with identical salience scores, and ZERO yogas,
  ZERO tenth-lord, ZERO raja-yogas. The ranking cannot tell a defining yoga from a trivial sub-varga tally. The
  `signature_tier` field meant to elevate chart-defining signals is 100% unused.
- **There is no synthesis step.** The domain-reading tool returns ~90,000 raw relational rows and *zero verdict
  text* — ingredients, never a reconciled reading. (A 17 MB dump for one domain.)
- **Machine-grounding is broken** (DEFECT-001): 91.5% of signals' `constituent_facts_array` no longer resolve to
  L1 fact_ids after an L1 SHA rebuild — human-readable citations are present, but the machine provenance chain is
  orphaned pending an MSR rebuild.

The serving/wiring bugs (an ayanamsha default mismatch that hid the whole insight surface, registration/whitelist
gaps, response-size blowups, L4 schema drift) are being fixed in a deterministic 4-wave campaign now underway.
**Those are not the strategic frontier. THE STRATEGIC FRONTIER — and the reason for this conversation — is the
DATA plane: enriching it, and the salience/synthesis/calibration models that ride on it, so the outcomes
(insight/guidance/prophecy/interpretation) become achievable.** Full audit: `MCP_SYSTEM_AUDIT_FINDINGS_v1_0.md`,
`MCP_SYSTEM_AUDIT_FIX_PLAN_v1_0.md`.

---

## §3 — THE DATA PLANE (THE SPINE — this is #1)

The whole thesis of the instrument is: **if the data captures the chart richly enough and in the right relational
structure, the LLM can synthesize insight beyond what a human could derive.** So the central strategic question
is: *is the data rich enough, and structured for insight — and if not, how do we enrich it?* Here is the data
plane layer by layer, with, for each, (a) what it holds, (b) its astrological role, and (c) the ENRICHMENT
frontier — how it could be deepened to project the target outcomes.

### §3.1 — L1 Gaṇita (the deterministic foundation — every derivation traces here)
- **Holds:** the computed chart facts — 9 grahas + Lagna positions across ALL divisional charts (D1–D60+),
  Vimshottari (and other) dasha chains (536,471 dasha rows), full shadbala/ashtakavarga strength models,
  dignities, avasthas, sensitive points (Sahams, special lagnas, upagrahas), nakshatra substructure, panchanga.
  Canonical counts: chart_facts=27,554; chart_dashas=536,471; chart_divisionals=21,635.
- **Astrological role:** this is the *ground truth* — the raw positional + strength + timing reality of the
  chart. Everything else is interpretation OF this. It is verified 7/7 against FORENSIC birth anchors (Sun
  Capricorn, Moon Purva Bhadrapada, Lagna Aries, etc.) — the natal compute is CORRECT.
- **ENRICHMENT FRONTIER (data #1 questions):**
  - **Completeness of systems:** are ALL the strength/analysis systems an acharya would use present and per-varga
    — full shadbala AND ashtakavarga in every relevant divisional, not just D1? (A subsystem program exists:
    Nakshatra, Yoga, Dignity, Transit, Medical, Astrovastu, Prashna — waved W0–W4; see `project_subsystem_program`.)
  - **Sensitive/rare factors:** Sahams, Arudha padas, Bhrigu Bindu, Yogi/Avayogi, Pranapada, the full upagraha
    family — are they all computed, or only the common ones? Beyond-acharya means holding the OBSCURE factors too.
  - **Cross-tradition breadth:** Parashari is the base — but Jaimini (chara dasha, arudha, karakas), KP
    (sub-lords, significators), Tajika (annual) — how much is captured as first-class data vs. absent? The audit
    saw `signal_tradition: parashari` dominating; the other traditions are the enrichment horizon.

### §3.2 — L2 Bodha (the RELATIONAL synthesis layer — where insight is born or lost)
- **Holds:** the MSR (Multi-Signal Repository) — ~64,765 per-chart signals, each a classical observation (yoga,
  placement, aspect, nakshatra condition, ashtakavarga strength) with `computed_salience`, `domains_affected`,
  `signal_tradition`, `constituent_facts_array` (→ L1), `citation_human`, verification status. Plus the CGM
  (Causal Graph Model: 140 nodes / 365–508 edges — the relationship graph between grahas/houses/signs/configs),
  the CDLM (Cross-Domain Linkage Matrix: 70 cells — how domains co-activate), the RM (Remedy Model), and the
  contradiction surface (~1,034 contradictions/chart).
- **Astrological role:** THIS is where "beyond-acharya" lives or dies. A human reads a few dozen factors; L2
  holds tens of thousands, graphed and cross-linked. The design philosophy (ratified): "rich pre-computed
  RELATIONAL ingredients, LLM synthesizes at query" — L2 is meant to be the ingredients, the LLM the chef.
- **ENRICHMENT FRONTIER (the most important strategic questions in the whole project):**
  - **SALIENCE — the #1 astrological-model problem.** Today salience is degenerate + varga-count-saturated (an
    acharya would never rank a D2700 bindu above a raja-yoga). **The salience model IS the "what matters" model —
    and it must encode acharya judgment: a Neechabhanga Raja Yoga, a debilitated 10th-lord, a Kemadruma, a
    Vipareeta Raja Yoga must outrank a mechanical sub-varga tally.** This is a native-judgment problem: the
    weighting of signal-classes is an acharya's call, not a code default. Activating `signature_tier` (elevate
    chart-defining signals) is part of it. *This single model, done right, is most of the distance to "insight."*
  - **THE GRAPH is the beyond-acharya organ.** The CGM (causal graph) is the one structure a human genuinely
    cannot hold — it's where cross-layer convergence/contradiction lives. Is it rich enough? Right now 140
    nodes/~400 edges. Enrichment: more edge taxonomies (strength-transfer, aspect-modulation, dispositor chains,
    argala, yoga-activation-by-dasha), edge *valence + directionality*, and query-time traversal that finds
    convergences a human never would. **The graph is where the instrument earns "beyond-acharya."**
  - **CONTRADICTION-HOLDING.** 1,034 contradictions/chart exist — but are they SURFACED and WEIGHED, or just
    counted? Beyond-acharya means: "the chart says X for career via the 10th-lord, but ¬X via the D10 ashtakavarga
    — here is how they reconcile and which dominates and why." That reconciliation is the frontier.
  - **THE OUTCOME VOCABULARY.** insight/guidance/prophecy/interpretation are four DIFFERENT synthesis products.
    Does the data carry what each needs? Prophecy needs time-bound falsifiable anchors (L4); guidance needs
    remedial economics (RM); interpretation needs the classical citation chain (L0); insight needs the graph.
    Strategic: is the data shaped for all four, or only for a generic "reading"?
  - **MACHINE-GROUNDING (DEFECT-001).** The constituent_facts→L1 chain is 91.5% orphaned. For beyond-acharya
    TRUST, every claim must resolve to its computed root. The MSR rebuild against current L1 is a data
    prerequisite for the whole insight thesis (a request is already filed:
    `REQUEST_RETRIEVAL_MSR_REBUILD_FOR_MCP_G10`).

### §3.3 — L3 Kāla (timing — the prophecy substrate)
- **Holds:** dasha×transit alignment, convergence windows (3+ indicators peaking together), obstruction periods
  (Sade Sati, malefic dashas), current-state snapshots. Tables `kala_*`.
- **Astrological role:** insight is atemporal; PROPHECY is timing. L3 is the animation layer — it says WHEN a
  structural potential becomes ripe. A yoga only delivers when its lords run their period AND the transit
  triggers — L3 encodes that gate.
- **ENRICHMENT FRONTIER:** multi-dasha systems (Vimshottari + Yogini + Chara + conditional dashas — cross-
  confirmed timing is more than any acharya juggles); finer convergence detection; the transit layer as a live
  service; tying convergence windows to the L2 graph so "what ripens when" is graph-aware. The audit found L3
  activation empty-served for the test chart — confirm it's populated + serving.

### §3.4 — L4 Phala (prediction — where prophecy becomes falsifiable)
- **Holds:** calibrated probabilistic event anchors (confidence = dasha_quality × signal_strength ×
  convergence), each with a FALSIFIER clause and source citation; per-anchor mitigations; birth-time
  rectification; auspicious-window (muhurta) finding. Tables `phala_*`.
- **Astrological role:** this is prophecy done HONESTLY — time-bound, probability-weighted, and FALSIFIABLE ("if
  X does not occur by date D, this prediction is false"). That falsifiability is what separates this from
  fortune-telling and is core to the ethical frame.
- **ENRICHMENT FRONTIER:** richer anchor generation from the full signal+graph+timing stack (not a thin subset);
  confidence calibration that actually learns (see L5); the mitigation/remedy economics (what remedy, what
  cost, what expected effect). The audit found L4 schema-drift-broken — being fixed in Wave 4.

### §3.5 — L5 Mīmāṃsā (calibration/learning — the beyond-human feedback loop)
- **Holds:** prediction→outcome calibration (Brier scores per technique × ayanamsha), the Life Event Log (LEL)
  as ground truth, technique-level accuracy tracking. Sealed in STRUCTURAL mode — values fill as outcomes accrue.
- **Astrological role:** THIS is the mechanism by which the instrument becomes beyond-acharya OVER TIME — no
  human astrologer systematically scores their hits/misses per technique and re-weights. L5 does. It's how
  "which technique is reliable for THIS kind of question" becomes empirical rather than dogmatic.
- **ENRICHMENT FRONTIER:** the n=1 problem (one native's LEL is thin) — how to calibrate credibly with limited
  outcome data; extending to multiple charts to build a real calibration corpus (the research-tool horizon);
  feeding calibration BACK into salience (a technique that calibrates poorly should down-weight). **The
  calibration→salience feedback loop is the deepest "beyond-acharya" idea in the system and is barely started.**

### §3.6 — L0 Brahmagyan (the reference substrate — the classical grounding)
- **Holds:** the classical rule base, the text corpus (BPHS, Phaladeepika, etc.), the remedy corpus
  (brahma_remedy_corpus), the entity ontology (grahas/nakshatras/rashis/yogas), ephemeris (1900–2150).
- **Astrological role:** this is what makes interpretation CITED, not invented — every claim can trace to a
  classical source (B.3). It's the difference between "the LLM says" and "Parashara says, per BPHS ch.X."
- **ENRICHMENT FRONTIER:** breadth + depth of the text corpus (how many classical works, how granularly
  verse-linked); the rule base's coverage (are all classical yogas/combinations encoded?); cross-referencing
  rules to signals so every L2 signal retrieves WITH its classical attestation.

---

## §4 — THE ENABLING SYSTEMS (#2 — necessary, in service of the data)

The data cannot produce insight without the systems that compute, store, retrieve, shape, and serve it. In
priority-after-data order:

- **The build/orchestrator (Nirmāṇa):** a FROZEN metadata-driven contract builds any chart's ~81 assets in
  dependency order ("click Build"). New capability = a `@register` writer conforming to the frozen contract.
  This is how data GETS made, per chart, correctly + idempotently. Strategic relevance: enrichment = new writers
  + new assets, onboarded through this contract.
- **The retrieval system (the single query brain):** a sealed registry (`lib/retrieval`) of ~75 capabilities +
  a router + a grounding spine (§N.5) + MARO (model-aware orchestration, 4 LLM-family profiles) +
  bundle-elasticity (response_format). Both channels consume it — ONE source of query logic. This is HOW the
  LLM reaches the data. Strategic relevance: the reasoning-unit tools (`assess_marriage/career/...`,
  `yoga_activation_by_dasha`) live here — they are the apex synthesis surfaces, and their quality = the salience
  + synthesis models of §3.2.
- **The MCP channel (external BYO-LLM access):** production-hardened this cycle — entitlement-gated, multi-chart,
  session-aware, OAuth, per-model surfaces, 45 tools. This is how ANY LLM (Claude/GPT/Gemini/DeepSeek) becomes
  the synthesizing mind on top of the data. Proven live. Strategic relevance: the instrument is not tied to one
  model — the "beyond-acharya" synthesizer can be the best available model at any time.
- **The chat engine (internal):** the same registry, internal-facing. The portal's own reading experience.
- **The governance substrate:** facts/interpretation separation, derivation ledgers, drift/schema validators,
  the honest self-reporting the audit praised. This is what keeps the system TRUSTWORTHY as it grows — essential
  for prophecy/guidance that people would actually rely on.

**The dependency truth:** data is #1, but every gram of insight travels: data (L1→L5) → retrieval registry →
channel (MCP/chat) → the LLM's synthesis. A weak link anywhere caps the output. The audit showed the pipes are
nearly sound; the water (salience/synthesis/calibration models on the data) is the work.

---

## §5 — THE STRATEGIC QUESTIONS THIS CONVERSATION SHOULD DRIVE

Ordered by leverage toward the north star. All are DATA-first or data-adjacent.

1. **The salience/relevance model (highest leverage).** How should signal-classes be weighted so the instrument
   surfaces what an acharya (and beyond) would deem defining? This is a native-judgment encoding: raja-yogas,
   dhana-yogas, arishta, debilitation/exaltation, dispositor strength, dasha-activated factors vs. mechanical
   varga tallies. What is the weighting philosophy? How does `signature_tier` get populated?
2. **The synthesis contract.** Where is the line between "data provides ranked ingredients" and "the tool/LLM
   produces a reconciled verdict"? What does a beyond-acharya READING look like as an output — structure,
   contradiction-handling, confidence, citation? Design the four outcome products (insight/guidance/prophecy/
   interpretation) explicitly.
3. **Data enrichment roadmap.** Which of §3's frontiers move first? (Cross-tradition breadth? Rare sensitive
   factors? Graph edge richness? Text-corpus depth?) What is the enrichment that most increases INSIGHT per unit
   effort? The subsystem program (`project_subsystem_program`) is the existing scaffold.
4. **The graph as the beyond-acharya organ.** How to make the CGM the centerpiece — richer edges, valence,
   traversal that finds non-obvious convergences. This is the one structure genuinely beyond human working memory.
5. **The calibration→salience feedback loop.** How L5 outcomes re-weight L2 salience over time — the mechanism
   that makes the instrument improve beyond any static acharya. And the n=1 → multi-chart research-corpus path.
6. **Machine-grounding integrity.** The MSR rebuild (DEFECT-001) so every claim resolves to its L1 root —
   prerequisite for trustable prophecy.
7. **The ethical/disclosure frame.** Prophecy + guidance for real people demands the falsifiability + calibration
   + disclosure-tier discipline already in the architecture — how does the strategy honor it as capability grows?

---

## §6 — ARTIFACTS THE NEW CONVERSATION SHOULD READ (in order)
1. This handoff (orientation + the data thesis).
2. `CLAUDE.md` (project governance, §A mission, §B subject, §N build standards) + `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` (you-are-here).
3. `MCP_SYSTEM_AUDIT_FINDINGS_v1_0.md` + `MCP_SYSTEM_AUDIT_FIX_PLAN_v1_0.md` — the live audit reality (esp.
   Dimension D/E — the salience/synthesis findings — and Wave 5).
4. `MACRO_PLAN_v2_0.md` (§ the ten-macro-phase arc, Learning Layer, Ethical Framework, Post-M10 research framing).
5. The L2 design philosophy + subsystem program memory (feedback_l2_bodha_design_philosophy, project_subsystem_program,
   feedback_subsystem_embedding_pattern) — the ratified data-enrichment doctrine.
6. The per-layer seal records (L1_GANITA_CLOSURE, L2_BODHA_CAMPAIGN_HANDOFF, L3_KALA_CLOSE, L4_PHALA_CLOSE,
   L5_SEAL_AND_SHIP_REPORT) — canonical counts + what each layer actually contains.
7. Live: connect an LLM to the MCP (45 tools) and READ a real chart — nothing substitutes for exercising the
   instrument on 482012f1 to feel where insight is + isn't.

---

## §7 — THE ONE-LINE CHARGE
**Make the data — and the salience, synthesis, graph, and calibration models that ride on it — rich and
structured enough that an LLM holding the whole chart at once produces insight, guidance, prophecy, and
interpretation beyond what any acharya could derive; and keep every claim grounded, cited, falsifiable, and
calibrated. Data first. Systems in service of the data. The tradition honored, and exceeded.**

*End of MARSYS_STRATEGIC_HANDOFF v1.0 — paste into a fresh Cowork conversation to open the strategic workstream
toward beyond-acharya insight synthesis.*
