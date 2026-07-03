---
artifact: RETRIEVAL_GROUNDTRUTH_TRAVERSAL_MODEL
canonical_id: RETRIEVAL_GROUNDTRUTH_TRAVERSAL_MODEL
version: 1.0
status: DRAFT — research-grounded, pending domain-expert validation
created: 2026-06-27
author: Cowork (classical-corpus research + corpus doctrine synthesis) — for native Abhisek Mohanty
classification: D-GROUNDTRUTH deliverable (3 of 4) — the Vedic-astrology face
parent: RETRIEVAL_SYSTEM_DESIGN_APPROACH (§B.2.2, §B.3)
sourcing: classical Jyotish methodology (BPHS, Phaladeepika, Jataka Parijata as described in primary + secondary sources) + the project's own encoded doctrine (B.11 Whole-Chart-Read, L2_BODHA_RETRIEVAL_STRATEGY query_ucd-first, MSR/CDLM/CGM structure)
validation_status: The native is not an acharya; this model is built from the classical corpus and the project's doctrine, NOT from native acharya judgment. It is explicitly a research-grounded v1 to be validated by a senior Jyotish acharya before being treated as canonical. Never frozen as final.
changelog:
  - v1.0 (2026-06-27): Initial traversal model — the classical reading sequence as a hierarchy of inquiry, mapped onto the project's assets + the UCD-first doctrine, expressed as the input to tool topology. Research-grounded; expert validation pending.
---

# RETRIEVAL GROUND-TRUTH — VEDIC-ASTROLOGY TRAVERSAL MODEL (v1.0)

> **What this is.** A model of **how an acharya-grade Jyotish reading actually traverses a chart** — the
> hierarchy of inquiry, what is consulted first, what clusters, what drills into what — so that the tool
> topology (deliverable 4) mirrors how a reading is actually performed rather than imposing a generic data
> shape. Deliverable 3 of 4 of D-GROUNDTRUTH (see `RETRIEVAL_SYSTEM_DESIGN_APPROACH §B.2.2`).
>
> **Provenance and honesty (important).** The native has stated he is not an astrologer and cannot supply
> acharya judgment. This model is therefore built from two legitimate sources — the **classical Jyotish
> corpus** (the documented BPHS/Phaladeepika/Jataka-Parijata reading methodology) and the **project's own
> encoded doctrine** (B.11 Whole-Chart-Read; the `query_ucd`-first → drill pattern in
> `L2_BODHA_RETRIEVAL_STRATEGY`; the MSR/CDLM/CGM structure). It is a **research-grounded v1**, to be
> validated by a senior Jyotish acharya before it is treated as canonical. It must never be frozen as final
> acharya truth. This is consistent with the project's anti-"generic astrology" stance: the model is
> *citable*, not invented.

---

## §1 — The classical reading sequence (the documented method)

Across the classical texts and standard teaching, a chart is read in a consistent **order of inquiry**. This
is the backbone of the traversal model:

1. **Foundation / orientation.** Establish the chart's frame: Lagna (ascendant) sign, Lagna lord, and the
   overall "promise" of the chart from the main placements. *"Start with the Lagna… it frames the entire
   chart."* The D1 (Rāśi) chart is the prime factor; all else refines it.
2. **The Moon (parallel foundation).** The Moon is read as co-equal with the Lagna — mind, perception, lived
   experience — and the Moon's nakshatra sets the Vimśottarī daśā sequence. Classical predictions prioritize
   the Moon chart equally to the Lagna chart.
3. **Planetary strength & dignity.** Assess each graha's strength: own/exaltation/Moolatrikona/friend/
   neutral/enemy/debilitation (BPHS, Phaladeepika ranking), plus shadbala/avasthā/combustion/motion. Strength
   gates how strongly any promise manifests.
4. **Bhāva (house) analysis.** Examine each house *from the Lagna AND from its kāraka*. "Bhava placement is
   most important, then rulership, then general kārakas, then degrees of closeness" — placement → lordship →
   kāraka → proximity/aspect intensity.
5. **Kāraka (significator) analysis.** Read each life-matter through its natural significator (and Jaimini
   chara-kārakas), cross-checked against the house that governs the same matter.
6. **Yoga / dosha (combinations).** Identify the formed yogas (Rāja, Dhana, etc.) and doshas, which amplify
   or afflict the baseline promise. Hundreds exist across the texts; only *formed* ones matter.
7. **Daśā (timing).** Only after the static promise is judged: apply the daśā system to time when promises
   fructify. "Assess the horoscope before applying any daśā." First the daśā-lord's natal condition (D1),
   then its divisional placements.
8. **Varga (divisional) confirmation.** Refine and confirm each topic in its divisional chart, *always read
   alongside D1, never separately* — D9 for marriage/dharma/maturation, D10 for career, D3 for siblings/
   courage, etc. Vargas confirm or qualify what D1 promised.

The shape is unmistakable: **broad orientation → strength/dignity gate → domain (house/kāraka) → combination
→ timing → divisional confirmation**, always anchored to D1 and the Moon, always reading each matter from
*multiple vantage points* (house + kāraka + varga) and reconciling them.

---

## §2 — The hierarchy of inquiry (traversal levels)

Generalizing the sequence into a reusable hierarchy — the levels a reading moves through for ANY question:

- **L-ORIENT — Whole-chart orientation.** The gestalt: Lagna + Moon + Sun frame, dominant yogas, chart-
  defining signatures, the "promise." *Asked first, always.* (Maps to the project's B.11 Whole-Chart-Read and
  the UCD digest.)
- **L-DOMAIN — Life-domain framing.** Narrow to the matter at hand (career, wealth, marriage, health, etc.)
  via its house(s) + kāraka(s) + governing varga. A reading rarely answers a domain without first seeing the
  whole.
- **L-FACTOR — Factor-level drill.** The specific grahas, houses, aspects, and configurations bearing on the
  domain — with their strength/dignity/condition as the gate on how strongly each acts.
- **L-DERIVATION — Derivation & reconciliation.** *Why* a factor reads as it does: the relational web
  (aspects, lordships, dispositors, argala), the convergences (multiple factors agreeing) and contradictions
  (factors in tension) that an acharya holds in working memory. **This is the layer the instrument can exceed
  a human at** — holding all linkages at once.
- **L-TIMING — Temporal activation.** When the promise fructifies — daśā/antardaśā, transits, varshaphal —
  layered only after the static reading.
- **L-SOURCE — Classical grounding.** The verse/rule/text that authorizes each judgment (the citation spine).

**Two cross-cutting traversal disciplines** the classical method enforces, which the topology must preserve:

- **Multi-vantage reconciliation.** Every matter is read from house AND kāraka AND varga, then reconciled.
  A single-vantage answer is incomplete by classical standard.
- **Anchor-to-D1-and-Moon.** Every divisional/temporal/derivational view is read *alongside* D1 and the Moon,
  never free-floating.

---

## §3 — Mapping the traversal onto the project's assets

The traversal levels map cleanly onto the asset archetypes (from the Asset Matrix, §5) — which is the bridge
to topology:

| Traversal level | What a reading wants | Asset(s) that serve it | Archetype |
|---|---|---|---|
| **L-ORIENT** | the gestalt, first call | **bo_samvada (UCD digest)**; chart-defining signatures from bo_laksana | Orientation/digest (#7) |
| **L-DOMAIN** | a life-domain frame | **bo_drishti (question lenses)**; bo_sangati (CDLM domain cells) | Orientation (#7) + cross-domain (#5) |
| **L-FACTOR** | specific grahas/houses + strength | ga_positions, ga_condition, ga_strength, ga_structural; bo_laksana signals | Flat-fact (#1) + rich-relational (#3) |
| **L-DERIVATION** | the relational web + convergence/contradiction | **bo_bimba/bo_karanajala (CGM graph)**, bodha_contradictions, bo_anveshana | Graph/traversal (#4) + cross-domain (#5) |
| **L-TIMING** | when it fructifies | ga_dashas, ga_tajaka, ga_sade_sati; L3 Kala (ka_*) | Temporal (#6) |
| **L-SOURCE** | the authorizing verse/rule | bg_texts, bg_rules, bg_yogas; `classical_sources_jsonb` on each signal | Prose/citation (#2) |
| **(remedy)** | what to do about it | bo_upaya (RM); bg_remedies | Prose/citation + relational |
| **(quality)** | how trustworthy this read is | bo_pramana_mapa; L5 mi_* calibration | Calibration (#8) |

The critical alignment: **the classical "orient → domain → factor → derive → time → cite" sequence is the
same as the project's already-doctrinal "`query_ucd` first → drill via lens/zoom/domain-evidence" pattern.**
The traversal model and the existing L2 retrieval strategy describe the same motion. Tool topology therefore
*extends a proven, classically-aligned pattern across all layers* rather than inventing one.

---

## §4 — Direct implications for tool topology (the handoff to deliverable 4)

The traversal model yields concrete topology guidance, to be finalized in the Tool-Topology Framework:

1. **Umbrella/"thread" tools at L-ORIENT and L-DOMAIN.** A reading starts broad. There SHOULD be a small set
   of umbrella entry tools — a whole-chart orientation tool (over UCD) and a per-domain framing tool (over
   lenses) — that return the de-duplicated high-level surface and *point* to what can be drilled. This is the
   single most important topology decision and it is classically mandated (you always orient first).
2. **Drill-down leaf tools at L-FACTOR and L-SOURCE.** Finer-grained tools fetch a specific graha's condition,
   a house's occupants/aspects, a verse, a rule — invoked *after* orientation, by reference (signal_id /
   fact_id / chunk_id), so each fact is resolved once (F1 dedup).
3. **A traversal/graph tool at L-DERIVATION.** The CGM graph needs a dedicated traversal tool (neighbors,
   paths, convergence clusters, contradictions) — this is where the instrument's superhuman value lives, and
   it is a distinct topology shape from both flat lookup and prose retrieval.
4. **A temporal tool family at L-TIMING**, time-window/daśā-period keyed, separate from the static tools
   (the classical method explicitly separates static judgment from timing).
5. **Multi-vantage built into the umbrella tools, not pushed onto the LLM.** Because the classical method
   reads every matter from house+kāraka+varga and reconciles, the domain umbrella tool SHOULD return the
   reconciled multi-vantage view (one entry, perspectives attached — exactly F1), not force the LLM to issue
   three separate calls and de-dup itself.
6. **Topology per asset is decided by archetype + traversal level**, not by table row-shape: flat-fact assets
   → leaf lookup tools; rich-relational/orientation assets → umbrella-with-children; graph assets → traversal
   tool; prose → hybrid-retrieval tool; temporal → time-keyed family; calibration → quality/serve tools.

> **The discriminating answer to the native's question** ("one tool per asset, multiple, or umbrella?"):
> it is **driven by the traversal level the asset serves**. Orientation/digest and rich-relational assets
> (bo_samvada, bo_drishti, bo_laksana) become **umbrella tools with drill-down children**; flat-fact assets
> become **single leaf tools**; the CGM graph becomes a **dedicated traversal tool**; prose corpora become
> **hybrid-retrieval tools**; temporal assets become a **time-keyed family**. One-tool-per-asset is the
> exception (flat facts), not the rule.

---

## §5 — Validation obligation (do not skip)

This model is research-grounded, not acharya-authored. Before it hardens into the canonical basis for tool
topology, it MUST be reviewed by a senior Jyotish acharya against the §J quality standard ("my own level / above
my own level / reveals things I wouldn't have seen"). Specifically to validate: the §1 sequence ordering, the
§2 multi-vantage + anchor disciplines, and whether any traversal level or reconciliation step is missing.
Track as an open validation item in the campaign tracker. The model is versioned and revisable; expert
findings bump it.

---

## Sources

Classical methodology (as documented): Brihat Parashara Hora Shastra (vedpuran.net English ed.);
muhuratam.in/vedic-birth-charts; astrosight.ai birth-chart-reading-101; theartofvedicastrology.com (bhāva
aspects); ijirah delineation-through-divisional-charts; thevedichoroscope.com divisional-charts;
prokerala.com divisional-charts; classical strength/dignity ranking per BPHS + Phaladeepika as cited across
sources. Project doctrine: `00_ARCHITECTURE/L2_BODHA_RETRIEVAL_STRATEGY_v1_0.md` (UCD-first → drill, F1/F3);
`PROJECT_ARCHITECTURE_v2_2.md §H.4 / B.11` (Whole-Chart-Read); `RETRIEVAL_GROUNDTRUTH_ASSET_MATRIX_v1_0.md`
(archetypes + spine).

*End of RETRIEVAL_GROUNDTRUTH_TRAVERSAL_MODEL v1.0 — D-GROUNDTRUTH deliverable 3 of 4. Research-grounded;
acharya validation pending.*
