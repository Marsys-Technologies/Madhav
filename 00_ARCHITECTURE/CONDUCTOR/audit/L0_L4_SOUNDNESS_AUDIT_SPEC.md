---
artifact: L0_L4_SOUNDNESS_AUDIT_SPEC.md
canonical_id: L0_L4_SOUNDNESS_AUDIT_SPEC
version: 1.0
status: CURRENT — the governing framework for the L0→L4 logic-vs-data soundness audit (pre-L5 confidence gate)
authored_by: Cowork 2026-06-22
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  The reusable audit framework that establishes confidence in the L0–L4 substrate BEFORE investing in L5
  Mīmāṃsā. Hunts the "plausible-but-wrong" bug class (silent-Jupiter, Capricorn ascendant, empty-catch,
  vocabulary-drift) that passes tests + lights the cockpit green while being WRONG. Three lenses:
  data-engineering soundness · astrological soundness · cross-layer faithfulness. Logic-vs-data check on
  a MINIMAL slice (2-3 traced rows/asset), bottom-up L0→L4. ASSESS ONLY — never auto-fix.
---

# L0→L4 Soundness Audit — Framework

## §1 — Why this exists (the bug class we hunt)
Every defect found in the L4 campaign shared ONE signature: **code produced a plausible-looking answer
that passed tests + lit the cockpit green, while being WRONG against reality.** None crashed; none failed
a unit test. They failed only against astrological truth (Lagna=Aries not Capricorn) or internal
consistency (660× Jupiter where diversity was expected). Examples: silent-`'Jupiter'` fallback (ka_sangam);
Capricorn ascendant (JD-convention); ph_pratikara empty-catch (0 rows); CDLM `spirituality`≠`spiritual`
vocabulary drift; ph_phaladesa stub. **A test suite cannot catch these — they are exactly what tests
passed.** This audit looks at ACTUAL VALUES + the CODE LOGIC that produced them, on a slice small enough
to hand-verify. Goal: before building L5 (which calibrates against L4's predictions), CONFIRM the L0–L4
substrate is sound — so the L5 effort rests on confirmed ground, not hope.

## §2 — The core principle (native framing): LOGIC-vs-DATA consistency, not data coverage
If the CODE LOGIC is sound and a TINY slice of its output matches what that logic should produce from its
inputs, the remaining rows follow BY CONSTRUCTION (same code, same input shape). So we do NOT sample for
statistical coverage. We pull **2-3 output rows per asset, trace them back through the writer code, and
independently re-derive what they SHOULD be from the upstream (`depends_on`) inputs.** Match = logic sound.
Mismatch = a silent-wrong bug. The data slice is just the PROBE; the real subject of audit is the LOGIC.

## §3 — The three lenses (every asset, every probed row)
1. **Data-engineering soundness:** row shape/types correct; no unexpected nulls; the upstream IDs the row
   cites actually RESOLVE in the upstream asset; row-count plausible; PK/natural-key unique.
2. **Astrological soundness:** the values are classically coherent — judged by Claude-in-Claude-Code reading
   a plain-language per-asset SUMMARY against classical rules (Lagna correct; dignity matches position;
   dāśā lord in sequence; yoga conditions actually hold; remedy fits the affliction). Deterministic ones are
   re-derived; interpretive ones are judged.
3. **Cross-layer faithfulness:** does the row faithfully INHERIT from its upstream (L-is-authority), or does
   it RESTATE/MUTATE an upstream value (the silent-Jupiter / CDLM-drift class)? The cited upstream value and
   the row's value must agree. **This lens is why the audit is bottom-up + seam-focused.**

## §4 — The detection patterns (probe each asset for these — they are the known tells)
- **Degenerate distribution** (one query, highest signal): a column that should vary collapsed to one value
  (660× Jupiter). `SELECT col, count(*) ... GROUP BY col` — if ~1 distinct where diversity expected → SMELL.
- **Silent-fallback constants** (code grep): `.get(key, <plausible-constant>)` defaults + bare
  `except: return [default]` / `return None`. These are the MECHANISM behind degenerate distributions.
- **Ground-truth anchor violation:** does the data agree with the 7 FORENSIC birth anchors + known LEL
  life events? (Sun=Capricorn, Moon=Purva Bhadrapada, Lagna=Aries ×5 ayanamshas, Tithi=Shukla Tritiya,
  Vara=Ravivara, Yoga=Shiva, Karana=Garaja.)
- **Broken inheritance:** a cited upstream id that doesn't resolve, or resolves to a DIFFERENT value than
  the row restates.
- **Vocabulary/taxonomy drift:** same concept, different label across assets (so joins silently miss) —
  e.g. domain `spiritual` vs `spirituality`, planet casing, sign-name variants.
- **Empty-but-lit:** asset marked built with 0 / suspiciously few rows, or a skewed distribution from a
  too-strict filter.

## §5 — The audit unit (per asset) — STRATIFIED SAMPLE, not 2 cherry-picked rows
**Why not 2 rows:** two hand-picked rows mislead in two ways — they might be the two that happen to WORK
(a bug hitting only SOME rows hides), and 2 rows cannot reveal a DISTRIBUTION problem (the all-Jupiter bug
is invisible in any 2 rows — both are Jupiter, looks fine). The sample must be REPRESENTATIVE (cuts across
the asset) AND REVEALING (surfaces what rows alone can't). So the unit is **distribution census + ~8-12
stratified rows + 2 aggregate checks** — still minimal (the LOGIC is the subject; the sample is the probe),
but it can't be fooled by a lucky pair.

**STEP 1 — DISTRIBUTION CENSUS FIRST (whole column, all rows — not a sample).** Before pulling any rows,
for each meaningful column run `SELECT col, count(*) FROM <table> WHERE chart_id=... GROUP BY col ORDER BY 2 DESC`.
This is the single highest-value check — it catches the degenerate-value class instantly (~1 distinct where
many expected = the silent-Jupiter signature) AND it AUTO-DETECTS THE CATEGORIES (the low-cardinality
categorical columns: signature_class, domain, dāśā lord, varga, etc.) that drive the stratified sample in
Step 2. The census is a census, not sampling; everything else builds on what it reveals.

**STEP 2 — STRATIFIED ROW SAMPLE (~8-12 rows, drawn to cut across the real axes the census exposed):**
- **Random (3-4):** a genuine `ORDER BY random() LIMIT 4` slice — you see rows nobody designed to work.
- **Extremes (2):** the strongest/highest-score row + the weakest/lowest (and the empty/null case if any) —
  bugs live at boundaries (ph_sankrama's skew showed in the TOP rows; empty cases hide silent fallbacks).
- **One per AUTO-DETECTED category (N):** from Step 1's low-cardinality column(s), pull one row of EACH
  distinct value (each signature_class, each domain, each lord). This is what catches a per-category bug
  that a blind random sample misses — the ka_sangam per-signature bug only emerged when DOSHA/DIGNITY/YOGA
  were looked at SEPARATELY. Self-scaling: a 5-category asset gets ≥5 here; a flat asset gets ~0.
- **Anchor (1-2):** rows tied to a known-correct answer (FORENSIC Lagna, a known LEL life event) — check
  vs ground truth, not just internal consistency.
> Sample size auto-scales to the asset's CATEGORY CARDINALITY (one-per-category + random + extremes +
> anchor), not a fixed number. High-category assets get more; flat lists get fewer.

**STEP 3 — Read the writer** (`pipeline/orchestrator/writers/<asset>.py` + `services/<asset>/`) — trace the
logic that produced the sampled rows.

**STEP 4 — Independently re-derive** what the sampled rows SHOULD contain from the `depends_on` upstream —
do NOT trust the asset's own output; compute from inputs.

**STEP 5 — Apply the three lenses** (§3) across the whole stratified sample (so you see per-category, not
just per-row).

**STEP 6 — TWO aggregate checks no row sample replaces** (whole column, all rows):
- **Null-rate per column** — 100% null = silent gap; 0% null where nulls are expected = a fallback filling them.
- **FK/inheritance resolution RATE** — do ALL cited upstream ids resolve (the %), or just the sampled ones?
  Broken inheritance can hit a subset.
- (Plus row-count sanity from the census.)

**STEP 7 — Silent-default code scan** (§4 pattern 2) on the writer.

**STEP 8 — Astrological summary:** emit a plain-language summary of what the asset claims for the native
ACROSS the sampled categories; Claude judges classical coherence.

**VERDICT:** `SOUND` / `SUSPECT` (a tell fired) / `BROKEN` (a lens failed) + the census + the traced
stratified evidence + the re-derivation.

## §6 — Sequence + rules
- **Bottom-up: L0 → L1 → L2 → L3 → L4.** Faithfulness only means something if the foundation is true. A
  layer is not "confirmed sound" until every layer below it is. (L3's ka_sangam is already known-BROKEN +
  in fix — note it, audit its siblings, don't let it block them.)
- **Complete each layer, THEN report all findings** (native ruling) — full SOUND/SUSPECT/BROKEN picture per
  layer at once. A BROKEN asset doesn't block auditing its siblings (may be independent), only blocks
  moving to the NEXT layer up until the native decides fixes.
- **ASSESS ONLY — never auto-fix** (native ruling). Report findings + traced evidence. Any fix is a separate
  native decision (as with ka_sangam). No surprise code changes.
- **Reuse, no speculative infra** — the audit is read-only queries + code reading + the existing test/eval
  harnesses. Build no new tables, no new framework beyond the per-layer report.

## §7 — The dependency graph (re-derive faithfulness along THESE edges)
Bottom-up; each asset's faithfulness is checked against its `depends_on`. (Roots have no upstream → check
against the raw source / classical rule / FORENSIC anchor instead.)
- **L0 Brahmagyan (22):** mostly roots (bg_ephemeris, bg_reference, bg_texts, bg_ontology, bg_rules←texts,
  bg_yogas/dasha_systems/doshas←ontology, bg_transit_rules, bg_nakshatra, bg_dignity_reference, …). Audit
  vs the classical source + internal consistency. THE FOUNDATION — most important to confirm.
- **L1 Gaṇita (16):** ga_positions (root — vs FORENSIC anchors), then ga_vargas/dashas/strength/sensitive/
  panchanga←positions; ga_structural←(positions+strength+panchanga+sensitive+vargas+dashas+nakshatra);
  ga_condition/yoga/vastu/medical/tajaka/sade_sati. The computed-chart layer — re-derive vs chart_facts.
- **L2 Bodha (10):** bo_laksana←(ga_structural+bg_rules) root of L2; bo_bimba/karanajala/samskara/sangati/
  samvada←laksana; bo_upaya←(laksana+sangati); bo_drishti←(laksana+sangati+karanajala); bo_anveshana,
  bo_pramana_mapa. **Audit bo_sangati's CDLM vocabulary specifically (known drift).**
- **L3 Kāla (12):** ka_gochara/graha_sancara←bg_ephemeris; ka_yojaka←(bo_laksana+bg_transit_rules+
  chart_dashas); **ka_sangam←(ka_yojaka+ka_dasha_kala+ka_gochara+ka_muhurta_seva) — KNOWN BROKEN, in fix**;
  ka_vighnakara←sangam; ka_kalasutra/kala_darshana/jivana_parva/bhavishya_lekha/tulana. The temporal layer.
- **L4 Phala (9):** ph_nimitta←(ka_sangam+ka_bhavishya_lekha+bo_*) the spine; ph_muhurta/sodhana/pratikara/
  sankrama←nimitta; ph_suddha_sodhana←sodhana; ph_pramana/phaladesa (composers); ph_rectification←nimitta.
  **ph_pratikara + ph_sankrama known-suspect (downstream of the ka_sangam fix) — re-audit after that lands.**

## §8 — Deliverable per layer
A `L<n>_SOUNDNESS_REPORT.md`: per-asset row (asset · verdict · which lens(es) · traced evidence · the
re-derivation that confirmed/refuted it · degenerate/null/FK rider results · the astrological-coherence
judgment). A layer summary: N SOUND / N SUSPECT / N BROKEN, and the single most important finding. Roll up
to an `L0_L4_AUDIT_SUMMARY.md` once all five layers are done — the pre-L5 confidence statement.

## §8.5 — SEED FINDINGS (from the 2026-06-23 plain-language-map fill — confirm + scope each; find siblings)
The instrument-map fill surfaced 16 anomalies as a free preview. The audit must CONFIRM each with its full
three-lens method (the 2-row glance is not proof), determine "computed-WRONG vs not-yet-COMPUTED" (the
re-derivation step settles this), and find any SIBLINGS the glance missed. Seeded per layer:

**L1 seeds:** chart_divisionals `graha='ALL'` + null sign/degree rows (#2 — summary rows or artifact?);
ga_yoga only 1 yoga fires across all ayanamshas (#5 — strict criteria or build gap?); kala_jivana_parva
is L3 (#11) — see L3.

**L2 seeds (HIGH PRIORITY — L5 calibrates through L2):** bodha_cgm_nodes/edges all grahas strength=0.506
IDENTICAL + all 360 edges valence/affected_domains/relationship_basis NULL + centrality NULL (#3 — the CGM
graph, the "invest hardest" asset; degenerate-uniform OR not-yet-computed — re-derive to settle);
bodha_rm_resonances all grahas identical resonance/weakness=0.28, contradiction=0 (#4 — formula not
differentiating planets?); bo_laksana top signals all sade_sati (#6 — ranking skew or real?); confirm the
bo_sangati CDLM vocabulary fix landed (spiritual/psychological/financial vs the old labels).

**L3 seeds:** kala_jivana_parva start_year=1950 for a 1984-born native (#11 — epoch anchored to dasha-start
not birth → life-chapters mis-dated 34yr; scores null); kala_activation_predicates top all SUBSYSTEM/
sade_sati (#7 — ranking or distribution?); the kala_convergence/activation/darshana/bhavishya pre-fix
states (#8/#9/#10/#16) should be RE-CONFIRMED post the convergence-fix rebuild (they should now be correct).

**L4 seeds:** phala_muhurta every row travel/Mercury/quality=0.3 IDENTICAL (#13 — no differentiation by
undertaking; degenerate); phala_sodhana uniform confidence_inflation (#12 — pre-fix, re-confirm); ph_pratikara
all-Jupiter (#14 — downstream of convergence; MUST re-audit after the ph_pratikara rebuild). #15 rectification
= NOT a bug (confirms Aries lagna — a positive).

**L0 seeds:** bg_texts/bg_compendium_index OCR garble in scanned BPHS sources (#1 — data-quality, scope the
impact: do garbled chunks feed live interpretation, or just sit in the corpus?).

**Pattern note:** #3, #4, #13 are the SAME degenerate-uniform class as the all-Jupiter convergence bug
(a value that should vary collapsed to one constant). The silent-default code scan (§4 pattern 2) + the
distribution census (§5 step 1) are the two checks that catch this class — run them HARD on every asset,
especially the scoring/strength/graph assets where uniformity hides.

## §9 — The payoff
When L0–L4 pass all three lenses at the logic level, the substrate L5 calibrates against is CONFIRMED real
— so the L5 Mīmāṃsā build (currently on hold) rests on verified ground. This audit is the gate between
"L4 looks done" and "L4 is trustworthy enough to build the learning layer on."

---
*End. Logic-vs-data soundness audit, three lenses, minimal traced slice, bottom-up L0→L4, assess-only,
full-layer-then-report. The probe is 2-3 rows; the subject is the LOGIC. Confirms the substrate before L5.*
