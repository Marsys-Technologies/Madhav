---
artifact: L0_L1_SENSEMAKING_AUDIT_v1_0.md
canonical_id: L0_L1_SENSEMAKING_AUDIT
version: 1.1
status: CURRENT — for native discussion (audit + understand; plan comes after, together)
authored_by: Cowork (4 parallel forensic sub-agents + direct read) 2026-06-12
changelog:
  - v1.1 (2026-06-12): added §8 — the native's redundancy question (does MSR reading L1 directly
    make ga_structural redundant?). Verdict: the redundancy is real but the fix is "compute once in
    ga_structural, MSR projects" — NOT "delete ga_structural + MSR re-fires." See §8.
  - v1.0 (2026-06-12): initial L0+L1 per-asset dossier + thematic synthesis.
authored_for: the native — make sense of L0 + L1 (every asset), against completeness + redundancy
framing: >
  We are building a NEW deterministic system. The legacy QUERY/retrieval layer is being REBUILT —
  this audit does NOT judge against old query tools. It judges how L0/L1 ORGANIZE, STRUCTURE, and
  CREATE data so completeness propagates, redundancy is avoided unless value-adding, and legacy
  contamination is purged. Two pillars: (1) data completeness/exhaustiveness, (2) retrievability
  (designed-in at the data-structure level, since the query layer is being rebuilt fresh).
verdict_headline: >
  L0 is a SOLID, deterministic, well-structured classical foundation (no silent drops, redundancy
  is intentional/value-adding). L1's raw writers (positions/strength/vargas/dashas/sensitive/
  panchanga/sade-sati/tajaka) are largely complete + atomic, with a few real silent drops. The
  CRITICAL problem is ga_structural: it computes relationships from only ~5% of L1's dimensionality
  (D1 positions only), ignoring the 30 vargas, 7 dasha systems, and all sensitive points it depends
  on — so the richest relational completeness never gets created, and that gap propagates to L2+.
supersedes_corrections:
  - "Earlier audit said Rahu/Ketu etc. broadly — refined here: the BIG leak is ga_structural's D1-only leverage, not the raw writers."
  - "Earlier 'ga_structural drops uncatalogued yogas' is REAL but is the SMALLER half; the BIGGER half is it never looks at vargas/dashas/sensitive at all."
companion: MARSYS_DATA_INTEGRITY_DEEP_AUDIT_v1_0.md (pillars overview), GA_STRUCTURAL_COMPLETENESS_FINDING_v1_0.md
---

# L0 + L1 Sense-Making Audit v1.0

## §0 — The one thing to take away

**`ga_structural` leverages only ~5% of the L1 data it sits on top of.** It reads D1 graha
positions + the ascendant, and **checks-but-never-reads** `chart_divisionals` (30 vargas),
`chart_dashas` (7 systems), and the sensitive points (Gulika, Mandi, Arudha, sahams). Every
relationship it computes — aspects, yogas, doshas, dispositor chains, argala, avasthas — is
**D1-only and natal-static.** So the deep relational completeness that the rich L1 base *makes
possible* is never created. This is the architectural root of "completeness not propagating to the
upper layers," and it is independent of (and bigger than) the hardcoded-yoga-catalog issue. The
raw L1 writers are mostly doing their job; the synthesis writer is the bottleneck.

---

## §1 — L0 (Brahmagyan) — per-asset dossier (condensed) + verdict

L0 is the global classical-knowledge layer; goal = every chart configuration has a definitional
"coverage home," structured for clean retrieval. **Verdict: structurally sound, deterministic,
no silent drops, redundancy is intentional. The gaps are honest scope-curation, not defects.**

| Asset | Holds | Structure | Created | Complete? | Redundancy | Legacy flags |
|---|---|---|---|---|---|---|
| bg_ephemeris | 825,084 raw positions 1900–2150 | atomic table | pyswisseph DE441 (pinned) | EXHAUSTIVE | none | none |
| bg_reference | 15 typed vocab tables (planets/nak/signs/houses/karakas/upagrahas/constants…) | normalized, typed, no jsonb | hardcoded + cited | EXHAUSTIVE for closed sets; curated glossary | pointer tables (value-adding) | none |
| bg_texts | 8,193 chunks, 13 classical texts + embeddings | denormalized, atomic at chunk | PDF→chunk→pinned embedding | complete for 13 texts; missing Nadi/Lal-Kitab | none | none (2 alt-source texts, documented) |
| bg_ontology | 384 canonical entities | normalized | hardcoded + cited | EXHAUSTIVE for entities; curated domains/concepts | none | none |
| bg_rules | 1,976 regex-extracted rules | atomic, verse-traceable | python regex (zero LLM) | 8.1% chunk yield — SUBSET | none | none |
| bg_remedies | 260 remedies (matrix+dosha+corpus) | atomic | hardcoded + regex | matrix complete; corpus-sweep partial | dosha→remedy denorm (value-adding) | none |
| bg_concordance | 477 (topic×school) chunk-pointers | array index | deterministic tag match | corpus-bounded (Devanagari/missing texts) | denorm pointers (value-adding) | none |
| bg_yogas | **175 yoga defs** w/ machine-readable `formation_rule_jsonb` | catalog, GIN-indexed | 81 inline + 94 corpus | target was 250 → SUBSET; **chapter-bug FIXED** | none | the bug was remediated |
| bg_doshas | 50 dosha defs | catalog | hardcoded + cited | EXHAUSTIVE for major canon | dosha→remedy FK | none |
| bg_dasha_systems | 18 dasha systems w/ pseudocode | catalog | hardcoded + cited | EXHAUSTIVE classical canon | none | none |
| bg_compendium_index | 7,025 chapter/topic index | materialized index | deterministic (mechanical summaries) | complete for corpus | denorm of chunks (value-adding) | none |
| bg_signal_type_registry (G52) | predicate registry | catalog | seed (69 starter / ~500–700 target) | OPEN/incremental — STARTER ONLY | none | the "500–700 predicates" framing is the LEGACY hangover to re-examine (see §4) |

**L0 synthesis.** Completeness posture: complete for the closed classical canon (planets, signs,
houses, nakshatras, vargas-vocab, dasha systems, doshas, karakas, upagrahas, strength systems);
honestly-curated subsets for the corpus-derived assets (rules 8.1%, yogas 175/250, remedies,
concordance) — all flagged, all resolvable by authoring, none silently fabricated. Redundancy: every
duplication (pointer tables, concordance, compendium, dosha→remedy) is **denormalization for
retrieval, value-adding, FK-clean** — no wasteful/drift redundancy. Legacy: **clean** — no dead
chart_ids, the one real bug (yoga chapter-filter) was fixed. The **`bg_yogas.formation_rule_jsonb`
is the key asset** — it's machine-readable and *designed* to be evaluated, which is exactly what
ga_structural should consume instead of hardcoding (see §3).

---

## §2 — L1 (Gaṇita) raw writers — per-writer dossier (condensed) + verdict

These 8 writers compute chart-specific facts into `chart_facts` (+ `chart_dashas`,
`chart_divisionals`). **Verdict: atomic grammar is gold-standard; per-ayanamsha coverage complete
(all 5); jsonb use is justified everywhere; a handful of real silent drops; native-binding is the
main legacy theme.**

| Writer | Emits | Atomic? | Completeness gaps (real drops) | Redundancy | Legacy |
|---|---|---|---|---|---|
| ga_positions | D1 positions, signs, nak, houses (10 bodies × 5 aya) | ✓ atomic | tropical not stored; true-node not stored (mean only) | dual-write to legacy `ganita_positions` | native birth hardcoded; `ganita_positions` = legacy debt |
| ga_strength | shadbala(7), ashtakavarga, bhava-bala, vimsopaka | ✓ atomic | **Rahu/Ketu get NO strength**; **kala-bala hardcoded daytime**; **drik-bala stubbed 0.375**; bhava-drishti simplified | AV recomputed per-varga in GA6 (complementary) | daytime hardcode; stubs |
| ga_panchanga | tithi/vara/yoga/karana/nak + tara baseline | ✓ atomic | hora, ghatikas, Sun-nakshatra, nadi not emitted | Moon-nak also in GA3 (re-read) | native FORENSIC gate |
| ga_sensitive | 30 sensitive-point categories (~13k rows) | ✓ atomic + justified jsonb | Lal-Kitab/Nadi FLOORED-with-flag (acceptable — gated on L0 prereqs) | positions re-derived from GA3 | flooring per-category not centralized |
| ga_vargas | 30 vargas × ~25 categories (~37k rows) | ✓ atomic | D81 skipped (documented); outer planets + per-varga MC floored silently | D1 recomputed (FORENSIC check — intended) | D81/outer-planet floors lack a flag |
| ga_dashas | 7 systems × 4 levels (~140k rows) | mixed (justified jsonb) | **Prana (level-5) not emitted**; KP levels 6/7 collapsed; Mudda/KalachakraNarayana "simplified" | concurrent-lords denormalized to jsonb (drift-risk) | level caps documented but no DB flag |
| ga_sade_sati | cycles/phases/quarters/dhaiya/cancellations | ✓ atomic + 5 justified jsonb | divisional argala not computed; Saturn's other transits out of scope | concurrent-dasha overlay duplicates GA7 | native FORENSIC (Muntha) gate |
| ga_tajaka | varshaphal year-lord, Muntha, Tajik yogas | ✓ atomic + 3 justified jsonb | annual gochara/prana not computed | varsha positions vs chart_divisionals | native-only; Tajik-yoga ruleset under-documented |

**L1 raw synthesis.** The chart_facts grammar (category/subject/key, atomic, dual-citation,
per-ayanamsha) serves completeness *well* — this is the strong part of the system. Real silent
drops to fix: **Rahu/Ketu strength, kala-bala daytime hardcode, drik-bala stub** (these are
correctness/completeness bugs, not scope choices). Documented scope caps (Prana dasha, D81, KP
levels) should at least get an explicit "intentionally-not-emitted" marker so absence is
distinguishable from a bug. Redundancy is mostly acceptable; the two to watch are the legacy
`ganita_positions` dual-write (technical debt) and the denormalized concurrent-dasha-lords jsonb
(rebuild drift-risk). Legacy theme = **native-binding** (birth params + FORENSIC gates hardcoded);
fine for the single-native phase, must be parameterized per chart_id for the real multi-chart goal.

---

## §3 — ga_structural — the core finding (the ~5% leverage problem)

This is the asset the native flagged, and the evidence is unambiguous.

**What it READS:** `chart_output["grahas"]` (D1 positions), `["ascendant"]`, and `["panchanga"]`
(checked, not used).
**What it CHECKS-BUT-NEVER-READS:** `chart_divisionals` (all 30 vargas — line 548 verifies
existence then never queries), `chart_dashas` (7 systems — line 533 same), the 6 sensitive points
(line 513 same). The rich data is *right there in memory and in the DB* and is **ignored.**

**Consequence — every relationship is D1-only and static:**
- Aspects: only D1 Parashari/Tajik — **no D9/D10/D12 aspects** (the divisional dimensions where
  marriage/career/lineage relationships actually read).
- Yogas: 24 hardcoded, checked on D1 only — **no varga-yogas**, and ignores L0's 175-catalog.
- Doshas: 15 hardcoded, D1 only — **Mangal cancellation doesn't check D9 strength** (classical
  rule).
- Dispositor chains: D1 sign-lords only — **no navamsha (D9) dispositor chain** (the karmic/marriage
  layer).
- Argala: D1 sign occupancy only — **no Arudha-based argala** (the manifestation layer).
- **Zero dasha-activated relationships** — yogas are treated as eternally on; nothing fires/cancels
  by dasha period, though the full timeline exists in chart_dashas.
- **Zero sensitive-point participation** — Gulika/Mandi/Arudha/sahams never act as aspect-givers or
  yoga-constituents, though classical Jyotish treats them as maraka/yogakaraka points.

**The high-value relationships MISSING because of partial leverage** (acharya-grade, all
deterministic, all computable from existing L1 data): varga aspects (D9/D10/D12); navamsha
dispositor chains; varga-verified yogas (Jataka Parijata varga-vichara — a yoga "real" only if it
holds in D1 AND D9); strength-modified dosha cancellations (Mangal cancelled only if Mars strong in
D1 *and* D9); dasha-activated/-dormant yogas (BPHS dasha-phala); Arudha-based argala; sensitive
points as aspect/yoga participants; cross-varga composite yogas.

**Structure/redundancy:** what it *does* emit is clean — atomic per relationship (288 argala rows,
not blobs), references rather than re-emits GA3 facts. The problem is not how it stores; it's **how
little it computes.**

**Verdict:** ga_structural is the **completeness bottleneck of the entire instrument.** L1 raw
writers create a rich, multi-dimensional base; ga_structural collapses it to a flat D1 snapshot
before the upper layers ever see it. Fixing the hardcoded-yoga-catalog (the earlier finding) is
necessary but *insufficient* — even with all 175 yogas, if they only fire on D1 the instrument is
still blind to the varga/dasha/sensitive dimensions where most real Jyotish lives.

---

## §4 — Legacy contamination to purge (the native's "plaguing" concern, inventoried)

These are the legacy artifacts leaking into the new build — to be purged, not preserved:
1. **Hardcoded native birth params + FORENSIC gates** in every ga_ writer → parameterize per
   `ctx.config['chart_id']`; FORENSIC asserts guarded to fire only for the canonical chart.
2. **The `_mock_fact_id_ref` broken reference** (confirmed: doesn't match real `_fact_id` —
   `key='rupa'`, `chart_prefix`, `build_id='ga3_build'` hardcoded) → cuts the L1-authority spine;
   must use the real fact_id formula.
3. **ga_structural's hardcoded 24-yoga / 15-dosha lists** → replace with a read of L0
   `brahma_yoga_catalog`/`brahma_dosha_catalog` (single source of truth).
4. **The "500–700 predicates" G52 framing** → this is the OLD MSR re-firing model leaking in. If
   ga_structural fires from L0 catalog and MSR/L2 is a pure projection, G52-as-firing-registry is
   redundant; it survives only as optional metadata. (Confirm in the L2 plan.)
5. **`ganita_positions` legacy dual-write** → obsolete once chart_facts is canonical; deprecate.
6. **Phantom `362f9f17`** anywhere it still appears → `482012f1`.
7. **Silent scope caps without markers** (Prana dasha, D81, KP levels, outer planets) → add an
   explicit "intentionally-not-computed" marker so absence ≠ bug.

---

## §5 — Redundancy: avoid unless value-adding (assessment)

Per the native's criterion. **Value-adding (keep):** L0 pointer tables, concordance, compendium,
dosha→remedy FK (all denormalization for retrieval). GA6's D1-recompute-with-FORENSIC-check
(integrity). ga_sensitive's position re-derivation (different geometry). **Wasteful / drift-risk
(fix):** `ganita_positions` dual-write (pure legacy debt); GA7 concurrent-dasha-lords copied into
jsonb (not auto-synced on rebuild → drift). **No other structural redundancy anti-patterns found** —
the system is, encouragingly, *not* bloated; its problem is under-computation (§3), not duplication.

---

## §6 — What this means for the two pillars (pre-plan summary)

- **Pillar 1 (completeness):** L0 ✅ structurally complete (curation gaps are honest + resolvable).
  L1 raw ✅ mostly complete (fix Rahu/Ketu strength, kala/drik, add scope markers). L1 synthesis
  (ga_structural) ❌ the deep leak — D1-only, ~5% leverage. **This is where the rebuild effort must
  concentrate.**
- **Pillar 2 (retrievability, designed-in):** the chart_facts atomic grammar is genuinely
  retrieval-friendly — the new query layer can sit cleanly on it. The risk isn't structure, it's
  that **facts never created (ga_structural's missing relationships) can't be retrieved by any tool,
  however good.** Retrievability starts with creation. So the order is: fix creation (ga_structural +
  the raw drops) → then build the new query layer over the now-complete base.
- **Legacy purge (§4):** seven concrete items, mostly in L1, to stop the old model from
  contaminating the new one.

---

## §7 — For our discussion (not a plan yet)
1. Does the ga_structural ~5%-leverage finding match your intuition of "only leveraging part of the
   data"? This is the headline; everything else is secondary.
2. Which missing relationship-classes (§3) are highest-value to build first — varga aspects?
   dasha-activation? navamsha dispositors? varga-verified yogas?
3. Confirm the legacy-purge list (§4) as the "stop the plaguing" worklist.
4. Confirm redundancy disposition (§5): deprecate `ganita_positions`, fix concurrent-lord jsonb.
5. Then — together — we turn this into the rebuild plan (ga_structural as catalog-driven +
   full-leverage + dasha-temporal; raw-writer drop fixes; the new query layer over the complete base).

---

## §8 — The redundancy question: does MSR reading L1 directly make ga_structural redundant?

**The native's question:** if MSR (L2) can read L1 raw assets directly and compute relationships
itself, what value does ga_structural add — is it redundant, does keeping both add wasteful
duplication?

**Finding — the redundancy is REAL.** Today ga_structural AND MSR BOTH independently fire yogas,
doshas, parivartana, avasthas. Direct overlap on ~200 yogas, ~15 doshas, parivartana, the 5 avastha
schemes; partial overlap on aspects/dispositors/karaka. And because they use *different* fire-
criteria (ga_structural's hardcoded 24 vs MSR's G52 predicates) and *different* strength formulas
(`yoga_strength_score` vs `computed_salience`), **they can disagree on whether a yoga fires, how
strong it is, and whether it's cancelled** — the SIG.MSR.377 drift class, structurally recreated.
A10 §0 explicitly says MSR "evaluate[s] every classical signal predicate against A1-A9 atoms" — i.e.
MSR is currently specced as a SECOND firing engine. That is the duplication-without-value to remove.

**But the fix is NOT "delete ga_structural and let MSR re-fire" (one sub-agent's recommendation).**
That just moves the single firing engine up a layer, discards the L1 fact-grammar + derivation-
ledger advantage, and still leaves one engine doing the work. It also contradicts the native's own
ratified principle: *MSR is a deterministic TRANSFORM of L1, not a re-computation; record every
signal the deterministic engine produces, no re-judgment.*

**The correct resolution — "compute once, project once":**
- **ga_structural is the SOLE deterministic relationship-firing engine** (fixed per §3: catalog-
  driven from L0 `brahma_yoga_catalog`, full-leverage across vargas/dashas/sensitive points). It
  fires every yoga/dosha/aspect/dispositor/argala exactly once, stores them as ID'd `chart_facts`
  with the two-pass verification + derivation-ledger living HERE (where the computation is).
- **MSR does NOT re-fire. It PROJECTS.** One fired L1 relationship → one MSR signal: reference the
  `fact_id`, inherit L1's value, attach salience decomposition + domains + classical sources. No
  second evaluation ⇒ no drift ⇒ no possible disagreement (there is only one firing engine).
- **What MSR adds (its non-redundant value):** salience ranking, domain tagging, cross-signal
  enrichment, synthetic composites, and the retrieval-optimized signal shape — the things that are
  genuinely L2 work, none of which re-decide what L1 already determined.

**So the verdict flips the question:** ga_structural is **NOT** redundant — it is the single
deterministic engine and the right home for relationship-firing (B.1 puts "yoga detection /
derivations" at the L1↔L2 boundary with a derivation-ledger). **What is redundant is MSR's
*re-firing*** (A10 §0's "evaluate every predicate against A1-A9 atoms"). That re-firing is the
legacy "MSR-as-its-own-engine with 500–700 predicates" model leaking into the new build — the exact
contamination to purge (§4 item 4). Remove the re-firing, keep ga_structural as the engine, make MSR
a pure projection: the redundancy AND the drift risk both disappear, and G52 demotes to optional
metadata (citations/domains), never a firing registry.

**Net:** keep ga_structural (fix its leverage); de-scope MSR from firing to projecting. This is the
non-redundant architecture, and it's the one consistent with both B.1 and the native's deterministic-
transform principle.

---

*End of L0_L1_SENSEMAKING_AUDIT (v1.1). L0 is solid. L1's raw layer is strong with a few real drops.
The instrument's completeness is bottlenecked at ga_structural, which leverages ~5% of L1 — D1-only,
static, hardcoded — discarding the vargas, dashas, and sensitive points that hold most of the
relational truth. Fix creation before retrieval; purge the seven legacy items; concentrate the
rebuild on ga_structural's leverage. Discuss, then plan together.*
