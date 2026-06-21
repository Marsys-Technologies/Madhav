---
artifact: L4_PHALA_SUPREME_EXPANSION_v1_0.md
canonical_id: L4_PHALA_SUPREME_EXPANSION
version: 1.1
status: PROPOSAL (v1.1 correction) — two flagship items re-graded from "net-new" to "activate existing"; M9 multi-school engine added; pending prod-truth reconciliation before plan finalization
authored_by: Cowork 2026-06-21
changelog:
  - v1.1 (2026-06-21): CORRECTION after code-verifying ga_dashas_writer.py + the M9 macro-phase.
    The traversal inventory was WRONG that "only Vimśottarī is computed / 17 systems are
    definitions-only." Re-graded §2.1 (multi-dāśā) from net-new build to ACTIVATE/COMPLETE
    existing capability. Added §2.9 — the M9 multi-school triangulation engine (built-but-dormant,
    partly hardcoded). Native ruled: prod-truth reconciliation FIRST; make M9 chart-general + wire
    into L4. See §0 correction block. Original §1–§7 analysis retained below (still valid on the
    latent-substrate findings).
  - v1.0 (2026-06-21): initial proposal, 8 value-adds + 2 upstream enablers.
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
parent_plan: 00_ARCHITECTURE/L4_PHALA_CAMPAIGN_PLAN_v1_0.md
grounded_in: code-verified traversal of L0 Brahmagyan, L1 Ganita, L2 Bodha, L3 Kala (2026-06-21)
role: >
  Answers the native's question: what is MISSING from the L4 plan that would make it a SUPREME
  prediction layer — beyond the depth of relationship, correlation, and chain-tracing a human
  acharya can hold? Reasons from the REAL capability inventory of L0–L3 (not the handoff). Each
  proposal names the latent substrate it exploits, the prediction value it unlocks, the tech/infra
  required, and where it slots into the DAG. For native ratification.
---

# L4 Phala — Supreme Expansion Proposal v1.1

## §0 — CORRECTION (v1.1): two flagship items are ALREADY BUILT, not net-new

> **The recurring failure, caught again.** Code-verifying before authoring revealed the traversal
> inventory was wrong in the SAME way L3's handoff was wrong — this time it UNDER-counted what exists.
> This project's docs misstate build state in both directions; trust code + prod, never the doc.

**CORRECTION A — Multi-dāśā (§2.1) is largely BUILT, not a net-new L1 reopen.**
`platform/python-sidecar/ga_writers/ga_dashas_writer.py` has `SYSTEMS = [vimshottari, yogini,
ashtottari, chara_karaka, naisargika, mudda, kalachakra]` (7 systems) with real `compute_*_system`
functions for each, and the orchestrator writer (`pipeline/orchestrator/writers/ga_dashas.py`) plans
35 substeps across all 7 × 5 ayanāṃśas. `ka_dasha_kala` already queries all 7. **BUT** evidence
conflicts on prod-population: the L1 seal attributes 536,471 rows to Vimśottarī, and a sibling file
(`l1_dashas.py`) comments "MD ONLY" for non-Vimśottarī systems. **So multi-dāśā is either fully built
+ prod-populated, or built-but-only-Vimśottarī-was-run, or non-Vim systems compute MD-level only.
This is UNVERIFIABLE from code alone (data-plane).** U1 is therefore NOT a heavy L1 reopen — it is a
**verify-then-complete** effort (confirm prod by system_id × level; fill only the genuine gap).

**CORRECTION B — a whole MULTI-SCHOOL TRIANGULATION ENGINE exists (M9 macro-phase), under-counted.**
See §2.9 (new). Built, tested (78 green), CLOSED — but DORMANT (not wired/persisted) and its signal
scores are partly HARDCODED to this native rather than chart-general.

**Native rulings (2026-06-21):** (1) **prod-truth reconciliation FIRST** — verify actual prod state
before authoring U1/U2/the L4 revision; (2) **make M9 chart-general + wire it into L4** as a
first-class consensus confidence axis. The verification brief is `L4_PHALA_PROD_RECONCILIATION_*`.

**Re-grading:** §2.1 multi-dāśā: *net-new build* → **ACTIVATE/COMPLETE existing**. §2.9 multi-school:
**ACTIVATE + DE-HARDCODE + WIRE existing**. Both move from "build from scratch" to "verify, finish,
surface" — *less* work than v1.0 implied, and higher confidence they're classically sound (they're
already coded). Everything in §2.2–§2.8 (the latent-substrate value-adds) stands unchanged.

---


> **The thesis.** The draft 6-asset plan is a *competent* applied layer: it turns L3 windows into
> anchors, muhūrtas, mitigations, a rectification, and a dossier. But it consumes a fraction of what
> L0–L3 actually built. The traversal found a **massive latent substrate** — a 768-dim semantic
> embedding space over 66,738 signals, a multi-hop causal graph with pre-computed centrality and
> traversable chains, 1,411 non-obvious discoveries, a cross-domain linkage matrix, a contradiction
> store with resolution hints, a remedy map with feasibility economics, and a convergence engine with
> frozen-but-unfilled hooks. **An acharya holds maybe 50–200 active factors in working memory and a
> handful of chains 2–3 hops deep. This instrument holds 333,690 signals, a graph with measured
> betweenness, and 4+-hop chains — and can run them all against time.** That gap is where "supreme"
> lives. This proposal is the set of value-adds that close it.

---

## §1 — What the draft plan LEAVES ON THE TABLE (the latent substrate, code-verified)

The current L4 reads only `bo_laksana` (signals), `bo_upaya` (remedies), `ka_sangam` (windows),
`ka_vighnakara` (obstructions), `ka_muhurta_seva` + `ka_panchanga`. It **does not touch**:

| Latent capability (verified) | Where it lives | What it would unlock for prediction |
|---|---|---|
| **768-dim signal embeddings** (66,738 vectors, HNSW, Vertex AI) | `bodha_signal_embeddings` | Analogical prediction: "this configuration is semantically near these others"; pattern-class matching; precedent retrieval |
| **The causal graph + multi-hop paths** (140 nodes w/ pagerank/betweenness; edges w/ full value-vector; `bodha_cgm_paths.path_length` for 4+-hop chains) | `bodha_cgm_nodes/edges/paths` | Chain-of-influence prediction: trace WHY a window fires through the graph; find the hidden mediator; rank predictions by graph centrality of their root cause |
| **1,411 non-obvious discoveries** (w/ falsifier_jsonb, why_an_acharya_misses_it) | `bodha_discoveries` | Discovery-seeded prediction: the deepest insights become time-anchored predictions; the "acharya misses it" cases are exactly the supreme surface |
| **Cross-domain linkage matrix** (domain-pair linkage, asymmetry, contradiction density) | `bodha_cdlm_cells` | Spillover prediction: "career stress in this window will load onto health" — the cross-domain chains an acharya can't hold |
| **Contradiction store** (yoga-vs-dosha pairs, resolution hints, combined salience) | `bodha_contradictions` | Honest prediction under tension: surfacing where the chart fights itself in a window, not flattening it to one verdict |
| **Resonance/remedy economics** (feasibility, cost, time, incompatibility graph, prereqs) | `bodha_rm_*` | Optimized intervention: not "do this remedy" but "this remedy, this window, this sequence, within your cost/time budget" |
| **Multi-ayanamsha robustness** (`cross_ayanamsha_consistency_score` 0–5 per signal/edge) | `bodha_msr_signals`, `bodha_cgm_edges` | Confidence honesty: weight every prediction by how many of 5 ayanamshas agree — a robustness axis no acharya computes |
| **The convergence engine's unfilled hooks** (`outcome_recorded`, lifetime sweep, Prana level-5, counterfactual) | `ka_sangam`/`kala_bhavishya` | Lifetime + sub-month-grain + self-correcting prediction |
| **17 uncomputed dasha systems** (definitions in `bg_dasha_systems`, only Vimshottari built) | `bg_dasha_systems` / `chart_dashas` | **Multi-dasha consensus** — the single biggest classical lever the instrument doesn't pull (see §2.1) |

---

## §2 — THE SUPREME VALUE-ADDS (each: substrate → value → tech → DAG slot)

Eight proposed capabilities, ranked by "supreme uplift × feasibility." Each is classically
defensible in *method* and computationally unprecedented in *execution*. Tagged `[CORE]` (build now,
inside L4) / `[ASSET]` (a new ph_* asset) / `[UPSTREAM]` (needs a lower-layer addition first) /
`[INFRA]` (new technology/infrastructure).

### 2.1 — Multi-Dāśā Consensus Prediction  `[ASSET]` `[UPSTREAM]`  ★ highest uplift
**The gap.** L1 computed ONLY Vimśottarī (536,471 rows). The other 17 systems (Yoginī, Chara,
Kālachakra, Aṣṭottarī, …) have full definitions in `bg_dasha_systems` but **zero computed rows**.
Yet the single most reliable classical timing technique is **dāśā consensus** — web-confirmed:
practitioners "layer multiple dasha systems to triangulate timing." An acharya cross-checks 2–3 by
hand; this instrument could cross-check **all applicable systems at every level, at machine speed.**

**The value.** A prediction window where Vimśottarī AND Yoginī AND Chara all activate the same
domain is *categorically* more reliable than a single-system window. This is the strongest possible
confidence signal — and it is currently impossible because the systems aren't computed.

**Tech/infra.** Needs an **L1 reopening**: a `ga_dashas_multi` writer computing the 6–8 most-used
systems into `chart_dashas` (the schema already has `system_id`). Then `ka_dasha_kala` already
supports "7 systems" in its query API — it's waiting for the data. L4's `ph_nimitta` gains a
`dasha_consensus_count` per anchor.

**DAG slot.** Upstream L1 task → feeds `ka_dasha_kala` → `ka_sangam` cross_dasha_agreement (already a
weighted input, I-7 = 0.18, currently thin) → `ph_nimitta`. **This is the highest-leverage single
change in the entire proposal.**

### 2.2 — Graph-Traced Causal Prediction ("the WHY chain")  `[CORE]`
**The gap.** `bodha_cgm_paths` holds traversable multi-hop chains (`path_node_ids_array`,
`path_length`, `path_strength`, `is_final_dispositor`) with pre-computed graph centrality on every
node. The draft `ph_nimitta` emits "anchor → falsifier" but never says **WHY** through the chart's
own causal structure.

**The value.** A supreme prediction is not "career elevation in 2027" — it is "career elevation in
2027, **because** the convergence root is your 10th-lord, which the graph shows is the highest-
betweenness node bridging your career and wealth clusters, via a 3-hop dispositor chain terminating
in exalted Jupiter." That causal chain is *exactly* what an acharya gestures at but cannot hold
precisely across 140 nodes. The instrument traces it deterministically and ranks predictions by the
graph centrality of their root cause (a high-betweenness root = a structurally load-bearing
prediction).

**Tech/infra.** None new — `bo_karanajala`/`bo_bimba` already computed it with igraph. `ph_nimitta`'s
engine adds a graph-walk: for each convergence window's `signal_id`, fetch the node, its centrality,
and the top causal path to a final dispositor; store as the anchor's `causal_chain_jsonb`.

**DAG slot.** Enriches `ph_nimitta` (reads `bodha_cgm_nodes/edges/paths` in addition to `ka_sangam`).

### 2.3 — Cross-Domain Spillover Prediction  `[ASSET]`
**The gap.** `bodha_cdlm_cells` holds domain-pair linkage with **asymmetry** (`asymmetric_linkage_flag`,
`asymmetry_score`) — e.g. career→health flows but not the reverse. The draft plan predicts per-domain
in isolation.

**The value.** The supreme move an acharya can't hold: "this 2027 career-stress window will, with the
chart's measured career→health asymmetry of 0.7, load onto your health domain 3–6 months later." That
is a **second-order, time-lagged, cross-domain prediction** — a chain across the linkage matrix that
requires holding the whole CDLM in memory at once. A new asset `ph_sankrama` ("transmission")
projects spillover predictions from the primary windows along the CDLM edges.

**Tech/infra.** None new — reads `bodha_cdlm_cells` + `ph_nimitta`. The lag model is a documented
deterministic rule (linkage strength × asymmetry → lag window).

**DAG slot.** NEW asset `ph_sankrama` ← `ph_nimitta` + `bodha_cdlm_cells`.

### 2.4 — Discovery-Seeded Prediction  `[CORE]`
**The gap.** `bodha_discoveries` (1,411 rows) holds the chart's deepest non-obvious insights, each
with a `falsifier_jsonb` and a `why_an_acharya_misses_it` field. The draft `ph_nimitta` derives
anchors only from `ka_sangam` convergence windows — it never time-anchors a *discovery*.

**The value.** The discoveries ARE the "beyond an acharya" surface — they were generated precisely
because they're non-obvious (buried in D24, low salience, high consequence). Time-anchoring them
(when does this latent structural insight activate?) produces the instrument's most differentiated
predictions: the ones an acharya would never make because they'd never see the underlying pattern.
`ph_nimitta` should accept discovery roots as a first-class anchor source, tagged `discovery_seeded`.

**Tech/infra.** None new — `ph_nimitta` adds `bodha_discoveries` as a second anchor source; the
discovery's `constituent_refs_jsonb` → its signals → `ka_sangam`/`ka_kalasutra` activation windows.

**DAG slot.** Enriches `ph_nimitta`.

### 2.5 — Analogical / Precedent Prediction via Embeddings  `[CORE]` `[INFRA-light]`
**The gap.** 66,738 signals each have a 768-dim Vertex embedding (HNSW-indexed). The draft plan does
zero semantic retrieval.

**The value.** Two uses an acharya structurally cannot do. (a) **Self-precedent:** when a window
fires on a signal, retrieve the chart's own semantically-nearest past activations (from
`kala_jivana_parva` life-arc) — "this configuration is the same *kind* as your 2010 relocation; that
is the precedent." (b) **Pattern-class matching:** cluster the embedding space to label a prediction
with its archetype (`bodha_discoveries.novelty_class` already gestures at this). This grounds a
prediction in lived precedent, which is the most persuasive and most falsifiable form.

**Tech/infra.** Uses existing embeddings + HNSW; needs a vector-similarity query path in the writer
(pgvector cosine — already indexed). Light infra.

**DAG slot.** Enriches `ph_nimitta` + `ph_phaladesa`.

### 2.6 — Calibration-Ready Falsification Spine (the self-correcting loop)  `[ASSET]` `[INFRA]`  ★ research uplift
**The gap.** Web-confirmed: **systematic Bayesian backtesting/calibration of astrology predictions is
essentially absent from the field.** Yet the substrate is ALL there: `kala_bhavishya` has
`outcome_recorded` + `falsifiability` columns (frozen, unfilled); the LEL holds 57 dated life events;
every L4 anchor carries an explicit falsifier. **Nothing currently scores predictions against
reality.**

**The value.** This is the project's *mission* (calibrated, correctable predictions) and its single
most differentiating capability versus every astrologer alive. A `ph_pramana` ("evidence") asset that
(a) backtests every prediction template against the LEL holdout, (b) computes a per-domain hit-rate
and a calibration curve (are my 0.7s actually 70%?), and (c) emits a per-prediction reliability prior,
turns the instrument from "makes predictions" into "makes predictions *with a measured track record*."
No acharya has ever had this. **Boundary note:** the heavy calibration machinery is L5 Mīmāṃsā — but
L4 should build the *falsification spine* (the scaffolding that makes L5 possible) and a first
backtest, because it's what makes the L4 predictions trustworthy at all.

**Tech/infra.** Reads LEL + `kala_bhavishya` + all `ph_*`; a deterministic backtest harness (replay
LEL events through the prediction templates, score hit/miss). Possibly a calibration-curve store. The
infra is modest; the discipline is the hard part.

**DAG slot.** NEW asset `ph_pramana` ← all `ph_*` + LEL + `kala_bhavishya`. Hands the calibrated
priors UP to L5. (Coordinate the L4/L5 line carefully — see §4.)

### 2.7 — Multi-Ayanāṃśa Robustness Weighting  `[CORE]`
**The gap.** Every signal and edge carries `cross_ayanamsha_consistency_score` (0–5). The draft plan
ignores it — it reads one ayanamsha's view.

**The value.** A prediction rooted in a signal that holds across all 5 ayanāṃśas is far more robust
than one that appears in only 1 (an artifact of ayanāṃśa choice). Weighting every anchor's confidence
by its cross-ayanāṃśa robustness is a **rigor axis no human computes** (an acharya picks one ayanāṃśa
and never re-derives). It directly hardens the calibration in §2.6.

**Tech/infra.** None new — multiply the confidence transform by the robustness score.

**DAG slot.** Enriches `ph_nimitta`'s confidence ladder (folds into G-LADDER, §6.1 of the plan).

### 2.8 — Lifetime + Sub-Month-Grain Convergence (the temporal extremes)  `[UPSTREAM]` `[INFRA]`
**The gap.** `ka_sangam` runs a **5-year forward horizon** and stops at Sūkṣma (level-4) dāśā. The
engine *structurally* supports a lifetime sweep and `ka_dasha_kala` can compute **Prāṇa (level-5,
~36-day grain)** in-memory but never persists it.

**The value.** Two extremes an acharya can't reach. (a) **Lifetime arc** — run the convergence engine
across the full life (birth→100y) once, so predictions sit in a lifetime context, not a rolling 5-year
window. (b) **Sub-month precision** — Prāṇa-grain convergence narrows a "2027 career window" to a
specific ~5-week peak. Together: the instrument can say "this 80-year-arc-significant event peaks in a
specific fortnight." No human computes a lifetime × Prāṇa grid (that's ~9 levels deep over 100 years).

**Tech/infra.** Needs `ka_sangam` re-parameterization (horizon control) + a persisted Prāṇa option —
this is an L3 reopening, heavier compute (possibly a batch job / more infra). Flag as a larger lift.

**DAG slot.** Upstream L3 enhancement → feeds all `ph_*`.

### 2.9 — Multi-School Consensus Prediction (ACTIVATE the dormant M9 engine)  `[ACTIVATE]` `[CORE]`  ★ added in v1.1
**The gap (under-counted in v1.0).** An entire **multi-school triangulation engine** already exists
from the M9 macro-phase (`platform/src/lib/schools/`): seven school engines — Parāśarī, Jaimini,
Tājika, KP, Nāḍī, BNN, Yoginī — plus a `convergence_calculator` and `school_runner`, 78 passing
tests, CLOSED. Its headline result for the native: *"5/5 domains HIGH convergence (6/6 effective
schools); CAREER 6/6 positive, HEALTH 6/6 neutral, …, 0 divergent domains."* This is **literally the
"consensus prediction beyond an acharya" capability** — and it's built. **BUT it is DORMANT:** not
wired to any route, never persisted to prod (proxy was down at close), migrations 057–060
(school_signal_coverage, school_analysis_runs, convergence_scores, school_disagreements) likely
empty, and critically its per-domain **signal SCORES are partly hardcoded to this native's chart**
(`defaultSignals()` returns fixed arrays) rather than derived live from L1–L3.

**The value.** Multi-school agreement is the single most persuasive confidence axis in the tradition
— when Parāśarī AND Jaimini AND KP AND Yoginī all read a domain the same way, that is a categorical
trust signal an acharya approximates with 2–3 schools by hand. Wired into `ph_nimitta`/`ph_phaladesa`
as a top-tier confidence multiplier, it makes every prediction carry "N-of-7 schools concur."

**The work (native ruling: make it chart-general + wire).** (a) **De-hardcode** the engines to read
real chart data live from L1–L3 (replace `defaultSignals()` presets with derivations from
`bodha_msr_signals` / `chart_facts`); (b) **persist** convergence per domain (the 057–060 tables);
(c) **wire** into L4 prediction as a confidence axis; (d) resolve the two pending flags
([VARSHA_KUNDALI_PENDING] for Tājika, [TRANSIT_DATA_PENDING] for BNN) using L3 services that now exist
(`ka_gochara` gives transits; Tājika varsha via `ga_tajaka`). Scope confirmed by the reconciliation.

**Tech/infra.** Reuses the built engines; the de-hardcoding is the real lift; persistence is the
057–060 tables already migrated. No new infra.

**DAG slot.** Enriches `ph_nimitta` + `ph_phaladesa` (multi-school consensus axis); depends on the
reconciliation's verdict on how hardcoded it really is.

---

## §3 — The revised asset set (draft 6 → supreme 9)

| # | asset | status | what changed |
|---|---|---|---|
| 1 | `ph_nimitta` | ENRICHED | + graph-causal chain (§2.2), + discovery-seeded (§2.4), + embedding precedent (§2.5), + ayanāṃśa robustness (§2.7), + dasha-consensus count (§2.1) |
| 2 | `ph_muhurta` | as drafted | (already strong; unchanged) |
| 3 | `ph_pratikara` | ENRICHED | + remedy feasibility economics (cost/time/incompatibility/sequence from `bodha_rm_*`) |
| 4 | `ph_sodhana` | as drafted | (PyJHora-computed; unchanged) |
| 5 | `ph_suddha_sodhana` | as drafted | unchanged |
| 6 | `ph_phaladesa` | ENRICHED | + contradiction-honest narrative (`bodha_contradictions`), + embedding precedent |
| 7 | **`ph_sankrama`** | **NEW** | cross-domain spillover prediction (§2.3) |
| 8 | **`ph_pramana`** | **NEW** | calibration-ready falsification spine + first backtest (§2.6) |
| 9 | **`ph_anudhyana`** | **NEW (optional)** | discovery-seeded "deep prediction" surface if §2.4 warrants its own asset rather than enriching ph_nimitta |

Plus **two upstream prerequisites** (not L4 assets, but the highest-leverage enablers):
- **U1 — `ga_dashas_multi`** (L1 reopen): compute 6–8 dāśā systems (§2.1). *Highest single uplift.*
- **U2 — `ka_sangam` lifetime + Prāṇa** (L3 reopen): temporal extremes (§2.8). *Larger lift.*

---

## §4 — The L4/L5 boundary under expansion (kept honest)
The expansion pushes on the calibration line, so re-state it precisely:
- **L4 builds the falsification SPINE** (`ph_pramana`): the scaffolding + a first backtest that makes
  predictions trustworthy *now*. It emits per-prediction reliability priors.
- **L5 Mīmāṃsā owns the calibration MACHINERY**: the ongoing scoring loop, the Bayesian refinement,
  the confidence re-calibration over time, the falsification register. `ph_pramana` hands its priors
  UP; it does not own the loop.
- The test: does the asset *make a prediction better right now* (L4) or *score predictions over time*
  (L5)? `ph_pramana`'s first backtest is L4; the standing calibration service is L5.

---

## §5 — Technology & infrastructure implications (the native asked: "whatever tech is required")
- **No new external LLM dependency for computation** — every value-add above is deterministic
  (graph walks, vector cosine, dāśā math, backtest scoring). LLM stays at serve-time synthesis only
  (Gemini/DeepSeek; Anthropic banned). This preserves deterministic-first.
- **pgvector / HNSW** — already provisioned (used by L2). §2.5 reuses it; no new infra.
- **igraph** — already used by L2 for centrality; §2.2 reuses the stored metrics; no new infra.
- **Compute for U1 (multi-dasha)** — moderate batch (6–8 systems × 4 levels); fits the existing
  orchestrator. **Compute for U2 (lifetime × Prāṇa)** — heavier; may warrant a dedicated Cloud Run
  batch job or a bounded-horizon default with on-demand deepening. This is the one place new infra
  (a heavier batch tier) might be justified.
- **A calibration store** (§2.6) — a small new table; trivial infra, high discipline.
- **Embeddings for new prediction text** — if `ph_*` outputs are themselves embedded for precedent
  search, reuse the Vertex pipeline already in `bo_samskara`.

---

## §6 — Recommendation & sequencing
**Tier 1 (build inside L4 now — pure enrichment, zero new infra, huge uplift):**
§2.2 graph-causal, §2.4 discovery-seeded, §2.5 embedding-precedent, §2.7 ayanāṃśa-robustness — all
fold into `ph_nimitta` + `ph_phaladesa`. §2.3 (`ph_sankrama`) + §2.6 (`ph_pramana`) as the two new
assets. Remedy-economics enrichment of `ph_pratikara`.

**Tier 2 (upstream reopen — schedule deliberately):**
U1 `ga_dashas_multi` (§2.1) — **strongly recommend doing this first or in parallel**; it is the
highest-leverage classical lever and `ka_dasha_kala`/`ka_sangam` already have the slots waiting.

**Tier 3 (larger lift — stage after Tier 1 proves out):**
U2 lifetime + Prāṇa (§2.8) — most compute-intensive; do once the prediction spine is validated.

**The honest framing.** Tier 1 alone moves L4 from "competent" to "clearly beyond an acharya's
working memory" — graph-traced causal chains, discovery-seeded predictions, semantic precedent, and
multi-ayanāṃśa robustness are all things no human holds. Tier 2 (multi-dāśā consensus) is what makes
the *timing* itself supreme. Tier 3 is the precision/lifetime frontier. §2.6 (calibration spine) is
what makes the whole thing *honest* — and is the project's mission-defining differentiator.

---

## §7 — Decisions for the native (before the plan is finalized)
1. **Scope of this L4 build:** Tier 1 only? Tier 1 + the `ga_dashas_multi` upstream (U1)? Or the full
   ambition including U2?
2. **`ph_pramana` calibration spine:** build the first backtest in L4 (recommended — it's what makes
   the predictions trustworthy), or defer entirely to L5?
3. **New assets:** approve `ph_sankrama` (spillover) and `ph_pramana` (calibration spine)? And does
   discovery-seeding get its own asset (`ph_anudhyana`) or just enrich `ph_nimitta`?
4. **Upstream reopens:** authorize U1 (`ga_dashas_multi`, L1) and/or U2 (`ka_sangam` lifetime/Prāṇa,
   L3)? These touch sealed layers — they need explicit sign-off + version bumps.

---

## Sources (multi-dāśā consensus + calibration white-space grounding)
- [42 Dasha Systems in Vedic Astrology — AstroNidan](https://astronidan.com/dashas/)
- [Types of Dasha in Astrology — IVA](https://www.ivaindia.com/blog/types-of-dasha-in-astrology)
- [Kalachakra Dasha System Explained — AstroSight](https://astrosight.ai/transits/kalachakra-dasha-system-explained)
- [Predictive Methods — Astrotheme](https://www.astrotheme.com/predictive-methods.php)
- [How Accurate Are AI Astrology Predictions — AllAboutAI](https://www.allaboutai.com/resources/ai-astrology-predictions/)

---
*End of L4_PHALA_SUPREME_EXPANSION v1.0. Eight value-adds + two upstream enablers, grounded in the
code-verified L0–L3 substrate. The gap between competent and supreme is the relationship depth, the
chains, the precedent, and the track record — exactly what a computer + LLM holds and an acharya cannot.*
