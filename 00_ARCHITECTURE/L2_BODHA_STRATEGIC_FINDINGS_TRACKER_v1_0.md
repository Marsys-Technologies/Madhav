---
artifact: L2_BODHA_STRATEGIC_FINDINGS_TRACKER_v1_0.md
canonical_id: L2_BODHA_STRATEGIC_FINDINGS_TRACKER
version: 1.0
status: TRACKED_FINDINGS_FOR_NATIVE_REVIEW (not yet folded into the strategy/briefs — deliberately held)
authored_by: Cowork 2026-06-19
purpose: >
  Capture the cross-cutting strategic findings from the native's overall (non-asset-specific) questions, so none
  is lost when the retrieval strategy + remaining briefs are finalized. THREE findings: (F1) the retrieval
  cross-asset DE-DUPLICATION principle — to ADD to the retrieval strategy LATER, not now (native directive);
  (F2) the RM (bo_upaya) SUBSYSTEM-COVERAGE GAP — a real completeness gap to close; (F3) the LAYER-RESOLUTION
  architecture (L0/L1/L2 retrieval reality) — a confirmation to carry as standing reference. Verified against
  live code 2026-06-19.
---

# L2 Bodha — Strategic Findings Tracker v1.0

## F1 — The retrieval cross-asset DE-DUPLICATION principle (HOLD: add to retrieval strategy later)
**Status: NOTED, NOT YET ADDED to the retrieval strategy (native directive — capture, don't fold in yet).**

### The concern (native, validated)
When the LLM answers one question, it may call multiple per-asset query tools (query_msr + query_cdlm + query_ucd
+ query_lens + query_rm). The SAME astrological fact surfaces through ALL of them:
- MSR: "Jupiter–Venus conjunction in D1, salience 0.81" (the signal).
- CDLM: references that signal in the career↔wealth linkage.
- CGM: the same conjunction as a node + edge.
- UCD/digest: points at it as a chart-defining thread.
- Lens: includes it in the career bundle.
- RM: references it as the affliction a remedy targets.
→ The same conjunction lands at the LLM ~5×. This is real token bloat AND — worse — it DISTORTS WEIGHTING: a fact
seen 5× looks 5× as important. We would re-introduce, through the RETRIEVAL door, exactly the double-counting we
banned inside the DATA.

### The crucial nuance (why it's not ALL duplication)
The same FACT appearing in multiple assets is NOT the same as the same INFORMATION repeated. Each asset adds a
DIFFERENT layer of meaning to the shared fact: MSR=what it is; CDLM=what it links; CGM=how it's positioned;
UCD=whether it's chart-defining; RM=what to do about it. These PERSPECTIVES are complementary, not redundant. The
redundancy is in RE-TRANSMITTING the shared identity + base attributes N times — NOT in the N perspectives. The
signal is the SPINE; the assets are ANNOTATIONS on the spine.

### Why the fix is architecturally CHEAP (the spine already exists)
Every asset references the shared fact by `signal_id` / `constituent_fact_ids` — NOT by copying values (the
capture-once-reference-many / anti-drift discipline). So the DATA already knows the conjunction in CDLM, CGM, UCD,
RM is the SAME signal_id. The shared identity is explicit + machine-detectable. What's MISSING is only that the
RETRIEVAL layer doesn't yet EXPLOIT this — each tool re-inflates the shared signal independently.

### The principle to ADD to the retrieval strategy (later)
**"SPINE-ORGANIZED, REFERENCE-DON'T-REPEAT composition."** When an answer touches a signal through multiple
assets, emit the signal ONCE with each asset's perspective ATTACHED — "Jupiter–Venus conjunction [MSR: salience
0.81] [CDLM: links career↔wealth] [CGM: central hub] [UCD: chart-defining] [RM: …]" — not five separate dumps.
Three mechanisms (to detail in the retrieval strategy):
1. **The lens/digest is the natural de-duplicator** — bo_drishti (lens) + bo_samvada (gestalt) return ONE entry
   per signal with all asset-perspectives merged. The LLM should query THESE as the primary surface, not five raw
   asset tools. (This is a reason the lens/digest matter beyond convenience.)
2. **Hydration return shape** — raw asset tools return REFERENCES (signal_ids + that asset's delta); the
   composition resolves each unique signal_id ONCE and merges the per-asset deltas (a join collapsing on the key).
3. **The retrieval contract: "reference, don't repeat"** — a standing rule the B6 eval EXPLICITLY tests ("does
   answering a question return each fact once with its perspectives, or N times?").
**ACTION: DONE — folded into L2_BODHA_RETRIEVAL_STRATEGY_v1_0.md §2 (2026-06-19). F1 now governs the retrieval layer; B6 tests it.**

---

## F2 — The RM (bo_upaya) SUBSYSTEM-COVERAGE GAP (a real completeness gap to close)
**Status: CLOSED IN BRIEF 2026-06-19 — folded into bo_upaya v1.2 §R5. Verification refined the finding: the L0
corpus is DESIGNED for ayurvedic/vastu (asset bg_remedies scope line); the gap is the CONSUMING PATH (4-type CHECK
+ planet-only query), not corpus absence — except where the corpus has the design-slot but no rows (an L0
expansion task, flagged not invented). R5 = widen taxonomy + query by all affliction keys + per-subsystem coverage
audit. Residual: VERIFY corpus CONTENT has medical/vastu/nakshatra rows (possible L0 task).**

### The finding (verified in code 2026-06-19)
We elevated bo_upaya's REASONING (causal-root, do-not-remedy, evidence ledger, patient-fit) — but we did NOT
verify its REMEDY CORPUS covers every subsystem we built. It does not, fully:
- The legacy remediation table constrains `remedy_type` to ONLY FOUR: **mantra, charity, gemstone, ritual**.
- The newer RM schema (mig 226) is broader (gem/mantra/yantra/dana/pilgrimage/chronobiology/substitute-gems) —
  but still does NOT structurally cover the SUBSYSTEM-SPECIFIC remedials.

### What the subsystems DIAGNOSE that has no matching remedial coverage (verified)
- **ga_medical** emits `body_part_watch` + `disease_tendency` + `nakshatra_body_part` → these DEMAND
  **medical / ayurvedic remedials** (dosha-pacifying, body-part-specific, herb/lifestyle) — NOT in RM today.
- **ga_vastu** emits directional/vastu facts → these DEMAND **vastu remedials** (directional corrections) —
  which is the ENTIRE POINT of the vastu subsystem — NOT in RM today.
- **nakshatra subsystem** emits gana / tara / nakshatra-lord facts → these have classical **nakshatra remedials**
  (nakshatra-deity propitiation, nakshatra-lord remedies, tara-based timing) — NOT distinctly in RM today.

### The principle (parallels the L1-completeness catch)
**RM's remediation completeness must SPAN every subsystem that produces an affliction.** If a subsystem can
DIAGNOSE a problem (medical body-part, vastu direction, nakshatra affliction), RM must be able to REMEDY it —
the L0 remedy corpus + the RM categories must COVER what the subsystems DIAGNOSE. Right now there is a coverage
hole for medical, vastu, and nakshatra-specific remedials.

### Options to close it (for native decision when we revisit bo_upaya / the corpus)
1. **Widen the remedy_category taxonomy** in RM to include medical/ayurvedic, vastu, nakshatra-deity categories +
   ensure the L0 brahma_remedy_corpus actually CONTAINS those remedies (grounded, cited — the absolute rule holds).
2. **Per-subsystem remedial coverage check** — a deterministic audit (bo_pramana_mapa could own it): for every
   affliction class a subsystem diagnoses, is there ≥1 grounded remedy? Flag uncovered affliction classes.
3. **Corpus gap may need an L0 build** — if brahma_remedy_corpus lacks medical/vastu/nakshatra remedies, closing
   the gap is partly an L0 (Brahmagyan) corpus-expansion task, not only a bo_upaya task. Verify the corpus content.
**ACTION: track as a bo_upaya / L0-corpus completeness item; decide closure path on revisit. Do NOT silently
assume RM covers all subsystems.**

---

## F3 — The LAYER-RESOLUTION architecture (L0/L1/L2 retrieval) — standing reference (CONFIRMED sound)
**Status: CONFIRMED — the architecture is correct; carry as standing reference.**

### Q: Can L2 Bodha provide ALL information, or do we need L0 + L1 retrieval tools too?
**All three layers are needed, and all three retrieval layers EXIST (verified):**
- **L1 Gaṇita: ~20 grouped tools** — get_positions, get_strength, get_ashtakavarga, get_dashas, get_panchanga,
  get_sensitive_points, get_tajik, get_tara_chandra_bala, get_dignity, get_dispositors, get_divisionals,
  get_karakas, get_aspects, get_argala, get_avasthas, get_bhava_bala, get_sade_sati, get_yoga_dosha, get_eclipse_flags, coverage_matrix.
- **L0 Brahmagyan tools** — query_classical_texts, query_yoga_catalog, query_dosha_catalog, query_remedy_corpus,
  resolve_entity, intent_classify, list_entities.
This is CORRECT architecture, not redundancy. **L2 is NOT a superset of L1/L0 — it is a different LAYER OF
MEANING.** L2 holds significance/relationships/judgment; it deliberately does NOT re-store raw deterministic
values (that would be the Trap-1 violation). Routing: "what does it MEAN / how strong / what does it link to" →
L2; "the EXACT longitude / shadbala NUMBER / dasha DATES" → L1; "what does Phaladeepika SAY / catalog definition"
→ L0.

### Q: Does MSR have ALL deterministic factual info, or only relational? Does L1 still add value?
**MSR does NOT contain all deterministic facts; L1 ABSOLUTELY still adds value — BY DESIGN.** MSR PROJECTS L1 (a
signal per L1 fact) and REFERENCES the L1 fact_id — it does NOT copy the raw value (capture-once-reference-many,
the anti-drift spine). So:
- MSR knows: "a signal here, salience 0.81, fact_kind=magnitude, references fact_id X."
- The ACTUAL value — Jupiter's shadbala = 387.2 virupas, exact longitude, precise bindu count — lives in **L1, not
  MSR.** MSR points at it.
**So MSR is the ENTRY POINT (significance + pointer); L1 is the GROUND TRUTH it resolves to.** L1's value is
irreplaceable: the exact figures, full precision, the raw facts MSR only CHARACTERIZES. The LLM answering "how
strong is Jupiter" gets significance from MSR, then resolves to get_strength (L1) for the precise number.

### The unifying insight across all three
**L2 is a layer of MEANING + REFERENCE sitting OVER L1's FACTS and L0's KNOWLEDGE — it POINTS DOWN, it does not
ABSORB.** Therefore: (1) the LLM needs all three retrieval layers (they exist); (2) MSR gives significance + a
pointer, L1 gives the precise value the pointer resolves to; (3) this reference-architecture only delivers
COMPLETENESS if the layers actually COVER each other — which is exactly why F2 (RM not covering all subsystems) is
a real gap. The retrieval composition (F1) must resolve cleanly DOWN the layers: MSR signal → L1 fact_id → precise
value, with L0 citation attached. F1 (de-dup) and F3 (layer-resolution) are two sides of the same retrieval coin.

---
*End of L2_BODHA_STRATEGIC_FINDINGS_TRACKER v1.0. THREE tracked findings from the native's overall questions:
(F1) the spine-organized reference-don't-repeat retrieval de-dup principle — HELD for the retrieval strategy, not
folded in yet; (F2) the RM subsystem-coverage gap (medical/vastu/nakshatra remedials missing) — a real
completeness gap to close, parallel to the 14-L1-assets catch; (F3) the L0/L1/L2 layer-resolution architecture —
confirmed sound, L2 points down + does not absorb, all three retrieval layers exist + are needed. For native review.*
