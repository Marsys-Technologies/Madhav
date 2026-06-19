---
artifact: L2_BODHA_JUDGMENT_SUBSTRATE_STRATEGY_v1_0.md
canonical_id: L2_BODHA_JUDGMENT_SUBSTRATE_STRATEGY
version: 1.1
status: FROZEN — native-finalized 2026-06-19 (all 5 moves committed; concerns addressed in §1.A, §5.A)
authored_by: Cowork 2026-06-19
purpose: >
  The strategic elevation of L2 Bodha from a DATA substrate to a JUDGMENT substrate. The base approach
  (project all of L1, bridge L0, prove anti-drift) makes Bodha thorough. This makes it SUPREME: it encodes
  the acharya's JUDGMENT — significance, confidence, classical reasoning, and question-focus — not just the
  acharya's data. Everything here is deterministic, classically grounded, and aligned with the two pillars
  + the research-instrument north star (calibrated / testable / correctable; not fortune-telling).
amends: L2_BODHA_OVERALL_APPROACH_v1_0.md
reshapes_briefs: bo_laksana (moves 2,3), bo_sangati + bo_karanajala (move 1), ALL assets (move 4), + a NEW lens asset (move 5)
---

# L2 Bodha — Judgment-Substrate Strategy v1.0

## §0 — The unifying principle (the north star for the whole layer)
> **L2 Bodha encodes not just what is TRUE about the chart, but what is SIGNIFICANT, how STRONGLY it can
> be claimed, WHY the tradition says so, and THROUGH WHICH LENS it answers a question — so the synthesis
> LLM inherits the acharya's JUDGMENT, not just the acharya's DATA.**

The test of "supreme": when a master astrologer and the LLM look at the same chart, the LLM has everything
the master holds in their head — facts, relationships, weight of evidence, contradictions, classical voice,
the judgment of what matters — available to retrieve. The base design gives the LLM the master's DATA. This
strategy gives it the master's JUDGMENT. Five moves.

## §1 — MOVE 1: The WEIGHT-OF-EVIDENCE engine (the centerpiece)
**The strategic reframe:** an amateur reads rules one at a time; a master WEIGHS EVIDENCE. That weighing is
the essence of acharya-grade judgment, and it is a convergence/contradiction operation. So convergence +
contradiction are not side tables — **they are the PRIMARY product of L2; everything else feeds them.**

Per (domain, and per major question-type), pre-compute the full **EVIDENCE LEDGER**:
- **supporting signals** + **opposing signals**, each with its INDEPENDENT weight;
- **independence accounting** — NEVER double-count one underlying fact across two "independent" signals (a
  master doesn't; store WHY each is independent, citing distinct constituent_fact_ids);
- **cross-tradition agreement** (N traditions concurring = weight, not just N signals);
- **net verdict** (where the balance lands) + **CONFIDENCE in that verdict** (strong / leaning / genuinely contested);
- **the dissents** named explicitly (the master says "but these two factors undercut it").

This is what lets the LLM say *"the weight of evidence strongly favours X, with these specific dissents"* —
master's speech, not rule-lookup. Reshapes **bo_sangati** (CDLM = domain evidence ledgers) and
**bo_karanajala** (CGM contradictions + convergence paths). bo_pramana_mapa audits ledger integrity
(no double-counting). DETERMINISTIC: the ledger is computed by versioned formula over MSR signals; no judgment leaks.

### §1.A — HOW it is built (the deterministic mechanism, no hand-waving)
Every MSR signal already carries `domains_affected_array` + a per-domain salience. The ledger per (domain) is:
1. **Gather** every signal whose `domains_affected_array` contains the domain.
2. **Classify** support vs oppose by the signal's `valence` RELATIVE to the domain (benefic yoga on 10th =
   support for career; malefic affliction = oppose). Deterministic from natural + functional nature.
3. **INDEPENDENCE DEDUP (the part masters do, machines botch):** two signals are independent evidence ONLY
   if they rest on DIFFERENT underlying facts. Test deterministically — do signal A and B share
   `constituent_fact_ids`? Shared root fact → counted ONCE, not twice. (This is the payoff of the
   constituent_facts spine.) Store WHY each surviving signal is independent.
4. **Weight** each by its per-domain salience (not chart-global).
5. **Verdict + confidence (versioned `evidence_ledger_formula_v1`):** net = weighted-support − weighted-oppose;
   confidence = f(margin × cross-tradition-agreement × cross-ayanamsha-stability). Reproducible; no judgment injected.
Mechanism in one line: **gather-by-domain → classify by valence → dedup by shared facts → weight by salience →
verdict + confidence.** Pure deterministic data-engineering over existing signals.

### §1.B — NON-REDUNDANCY with existing convergence/contradiction (native concern — VERIFIED + resolved)
Convergence/contradiction exists at THREE layers; they mean DIFFERENT things and must LAYER, never duplicate
(code-verified 2026-06-19):
| Where | What it ACTUALLY means | Plane |
|---|---|---|
| `ga_structural.convergence_count` (L1) | graph DEGREE — how many aspect-edges touch a graha per varga | geometric |
| `ga_structural.contradiction_pair` (L1) | structurally opposing geometric configs | geometric |
| `bodha_convergence` (L2 base) | how many SIGNALS share a domain | signal-count |
| **Move 1 evidence ledger (L2 new)** | weighted, dedup'd, confidence-scored VERDICT per domain | **judgment** |
**Rule: geometry → counting → judgment. Move 1 CONSUMES the lower two as inputs (references them as
constituents), never recomputes them.** The ledger cites the ga_structural convergence_count + the
bodha_convergence rows. Strict layering, zero redundancy. (Also check downstream: L4 Phala / L5 Mīmāṃsā will
do EMPIRICAL convergence across charts — that is cross-chart inference, explicitly L5, NEVER computed in L2.
L2's ledger is WITHIN-chart deterministic only. Do not duplicate L5's job either.)

## §2 — MOVE 2: Relational/contextual SALIENCE + chart-defining tiering (bo_laksana)
Salience is currently an absolute formula score. A master thinks relationally: *"this matters BECAUSE that
is also true; this is the DEFINING feature; that is a footnote."* Two additions to bo_laksana:
- **Conditional salience** — store the CONDITIONING relationships ("signal A's significance is amplified/
  damped by signal B"), e.g. a debilitated graha matters more when its dispositor is also weak. The LLM
  inherits the "it depends on" reasoning, deterministically (from the structural relationships, not opinion).
- **signature_tier** — a deterministic classifier separating the 5–10 **chart-DEFINING** structural threads
  (for the native: the Rahu–Moon–Jupiter axis) from the hundreds of merely-true background facts. So the LLM
  LEADS with what defines the chart instead of reciting a flat list. (Computed from centrality + convergence +
  cross-ayanamsha stability — all already in the layer.)

## §3 — MOVE 3: Structured EPISTEMIC HONESTY (mandatory for the north star)
This is not optional elevation — it is FIDELITY to what the instrument IS (calibrated, testable, correctable,
a research tool not a fortune-teller). An instrument that cannot represent its own uncertainty cannot be those
things. Replace the binary `epistemic_tier` with structured, retrievable uncertainty on every signal/ledger:
- **tradition agreement state** — sources AGREE (high confidence) vs sources DISAGREE (genuinely contested);
- **ayanamsha fragility** — holds 5/5 (robust) vs 2/5 (method-dependent — flag it);
- **computation-vs-interpretation split** — the deterministic computation is solid BUT the classical
  interpretation is ambiguous (distinct from "the computation is uncertain");
- **calibration hook** — a field L4/L5 can later populate with observed-accuracy (the correctable loop).
So the LLM natively distinguishes *near-certain* / *contested* / *method-dependent* / *interpretively-ambiguous*.
Reshapes bo_laksana (per-signal) + the evidence ledgers (per-verdict confidence). This is the ethical spine.

## §4 — MOVE 4: The L0 bridge carries REASONING + inter-authority disagreement (committed, scoped honestly)
The base bridge attaches citation ids. The supreme bridge makes retrievable, per signal, **what the sources
SAY and where authorities DIFFER** — so the LLM presents the tradition's DISCOURSE ("Parāśara reads this as X;
Jaimini's method differs; Phaladeepika adds a condition"), not a bare "per BPHS."
- **NOW (deterministic, committed):** store the retrievable LINKAGE — signal → the relevant bg_texts verses +
  the KNOWN cross-school positions (where the catalog/ontology already encodes school attribution). This is a
  deterministic join + linkage, deliverable in the L0-bridge step of every asset.
- **DEPTH (scoped, not over-promised):** extracting "what the verse SAYS + the disagreement structure" from
  embedded text chunks is NLP-adjacent, not a SQL join. Treat deep disagreement-EXTRACTION as a dedicated
  later pass; do NOT claim a deterministic guarantee we can't cleanly keep. The bridge RETRIEVES the verses so
  the LLM can read them — that alone is a large elevation; structured disagreement is the stretch goal.

## §5 — MOVE 5: The QUESTION-LENS asset (new; folded into L2)
Pre-compute the deterministic classical LENSES — question-type → the chart-specific structural elements that
bear on it. Career-lens = {10th house + its lord + D10 + Saturn/Sun karakas + the career-relevant yogas + the
CAREER evidence ledger (Move 1)}. Likewise marriage / health / wealth / spirituality / character / education /
progeny / etc.
- **Why it is L2 DATA (not a retrieval-layer concern):** which elements bear on career is a deterministic
  CLASSICAL fact about THIS chart — chart-specific structure. Keeping it in L2 honors "facts live in the data
  layer." Building it in the retrieval layer would recompute chart structure outside the data layer.
- **THE GUARD — a lens POINTS, never PRE-ANSWERS.** It assembles "here are the relevant elements + the evidence
  ledger for career"; it does NOT store "the native will have a good career." Pointing vs concluding. This
  preserves the design philosophy (ingredients, not pre-answered questions) WHILE making retrieval
  answer-FOCUSED — the LLM pulls the career lens in one targeted call instead of scanning everything.
- **New asset:** `bo_drishti` (Dṛṣṭi = "viewpoint/lens") or fold as a lens-table under bo_samvada (UCD). Owns
  `bodha_question_lenses` (per chart × domain/question-type → element id arrays + ledger ref). Depends on
  bo_laksana + bo_sangati (needs the ledgers). Confirm asset-id at brief time.

### §5.A — THE ANTI-TUNNEL-VISION GUARD (native's deepest concern — the lens must NOT lose the significant outlier)
**The fatal flaw of ANY lens/model: it retrieves only what the model knew to look for.** A signal that is
statistically FAR from the career template but astrologically DEVASTATING for career (a rare affliction, an
unenumerated yoga, an unexpected path to the 10th lord) would be silently dropped. That is exactly how real
astrologers fail — apply a checklist, miss the thing that doesn't fit it. The instrument must NOT inherit this.

**Principle: the lens is ADDITIVE, never SUBTRACTIVE. It points TO the obvious without filtering OUT the
non-obvious.** Three mechanisms, all deterministic:
1. **Template set + MANDATORY WILDCARD SWEEP.** Every lens returns TWO parts: (a) the template-relevant
   elements (10th house, its lord, D10, karakas, standard yogas) AND (b) **a graph-sweep for ANY high-salience /
   high-impact signal that reaches the domain's significators by ANY relationship-graph PATH — even one the
   template never anticipated.** Because every signal has domains_affected + the CGM graph has paths, we ask
   "does any signal reach the 10th-lord / career-karaka through the graph, regardless of the template?" The
   GRAPH catches what the template misses. (This is WHY the deep multi-entity graph matters — it's the
   safety net against tunnel vision.)
2. **FLAG outliers, don't just include them.** A signal that is high-salience + impacts the domain + is
   OUTSIDE the template gets `non_template_significant = true`. The LLM is TOLD "this is an unexpected but
   significant factor for career" — exactly what a master leads with ("the textbook says X, but the unusual
   thing in YOUR chart is Y"). The outlier becomes a FEATURE, not a loss.
3. **The lens RANKS, never CAPS.** It returns EVERYTHING that touches the domain, ranked, template-marked,
   outliers-flagged — never "top N." Retrieval may LEAD with the template set for speed, but the full set
   (weak tail + far-from-mean) is ALWAYS reachable (the no-drop pillar). **A lens is a LENS, not a FILTER —
   it focuses attention without restricting access.**
Result: the obvious arrives fast + organized; the non-obvious-but-significant can NEVER be lost. Surfacing the
significant outlier is itself acharya-grade — the guard makes the lens BETTER than a naive lens, not merely safe.

## §6 — How this reshapes the build (the briefs to amend / add)
| move | reshapes | what changes |
|---|---|---|
| 1 weight-of-evidence | bo_sangati, bo_karanajala, bo_pramana_mapa | CDLM = domain evidence ledgers (support/oppose/independence/verdict/confidence/dissents); CGM contradictions feed it; scorecard audits no-double-count |
| 2 relational salience + tiering | bo_laksana | conditional-salience relationships + signature_tier column |
| 3 epistemic honesty | bo_laksana + the ledgers | structured uncertainty (agreement/fragility/comp-vs-interp/calibration hook) replaces binary tier |
| 4 L0 reasoning bridge | ALL assets' L0-bridge step | linkage to verses + cross-school positions now; deep extraction scoped later |
| 5 question-lens | NEW asset (bo_drishti / under bo_samvada) | bodha_question_lenses; points-not-answers guard |

## §7 — What stays sacred (so elevation doesn't corrupt)
- Deterministic-first — every elevation is a versioned formula / deterministic join, NEVER an LLM judgment baked into data.
- Anti-drift (Trap 1) — ledgers + lenses + salience REFERENCE fact_ids/signal_ids; never restate values.
- No pre-answering (the lens points, never concludes).
- **The lens is additive not subtractive — significant outliers can never be filtered out (§5.A).**
- **Convergence/contradiction LAYERS, never duplicates (geometry→counting→judgment, §1.B); L5 cross-chart convergence stays L5.**
- Two planes stay separate (no temporal/resonance in L2 — deferred to Kāla).
- The two pillars remain the acceptance; the eval harness (B6) gates the seal — now testing JUDGMENT quality
  (does the LLM weigh evidence + state confidence + lead with what matters + SURFACE the significant outlier),
  not just retrieval coverage.

---
*End of L2_BODHA_JUDGMENT_SUBSTRATE_STRATEGY v1.0. Five moves take Bodha from thorough to supreme: (1) the
weight-of-evidence engine as the PRIMARY product; (2) relational/contextual salience + chart-defining tiering;
(3) structured epistemic honesty (the research-instrument spine); (4) the L0 bridge carrying classical reasoning +
inter-authority disagreement (scoped honestly); (5) the question-lens asset (points, never pre-answers). The LLM
inherits the acharya's JUDGMENT, not just the data. All deterministic, classically grounded, anti-drift-clean,
and aligned with the calibrated-research-instrument north star.*
