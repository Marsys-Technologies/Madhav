---
artifact: MARSYS_DATA_INTEGRITY_DEEP_AUDIT_v1_0.md
canonical_id: MARSYS_DATA_INTEGRITY_DEEP_AUDIT
version: 1.0
status: CURRENT — native review; defines an intervention program
authored_by: Cowork (4 parallel forensic sub-agents + direct code read) 2026-06-12
authored_for: the native — whole-architecture audit against the two pillars + intervention plan
severity: HIGH — multiple confirmed silent-drop + broken-reference + retrievability defects
the_goal: >
  The LLM must have complete, deep, deterministic, data-engineering-derived insight into the
  astrological profile — EVERY configuration, high or low strength, must surface via the
  retrieval tools. Two pillars: (1) DATA COMPLETENESS/EXHAUSTIVENESS (L0 global + L1 chart-specific
  capture everything computable, nothing silently dropped); (2) RETRIEVABILITY (every stored
  relevant fact is reachable by the LLM through tools, including the weak tail).
evidence_base:
  - ga_writers/* (all 9 L1 writers) · brahmagyan/* (L0) · ga_structural_writer.py
  - platform-mcp/src/tools/* + src/lib/retrieval/* (the retrieval layer)
  - migrations 176/204/215 (chart_facts schema + fact_id grammar) · A10–A14 specs
companion: GA_STRUCTURAL_COMPLETENESS_FINDING_v1_0.md (the ga_structural-specific deep-dive)
---

# MARSYS-JIS — Whole-Architecture Data-Integrity Deep Audit v1.0

## §0 — Bottom line in five sentences

The architecture is sound in its skeleton (deterministic engine, layered, fact-grammar with IDs)
and the **raw relational structure of the chart is captured exhaustively**. But against the two
pillars there are **serious, systematic leaks at three levels**: (1) L1 **silently drops** whole
classes of computable facts via hardcoded catalogs/lists and a few thresholds; (2) a **confirmed
broken-reference bug** means the yoga/dosha facts' back-references to L1 do not resolve — the
anti-drift spine is cut; (3) the **retrieval layer exposes only ~30% of stored fact categories** —
shadbala, ashtakavarga, panchanga, sade-sati, alternative dashas, and the entire L0 classical
corpus are stored but **unreachable by the LLM**. Each is individually fixable; together they mean
the system today does NOT meet the stated goal, and Bodha (L2) would inherit every leak. This
report maps all of it and proposes a sequenced intervention program — including completeness gaps
and retrievability gaps you did not name.

---

## §1 — The integrity scorecard (verified)

| Area | Pillar | Status | Headline |
|---|---|---|---|
| L1 raw relational facts (aspects, argala, dispositors, conjunctions, dignities, avasthas) | Completeness | ✅ PASS | Emitted exhaustively for all planets/pairs/houses — NOT dropped |
| L1 named patterns (yoga_fires, dosha_fires) | Completeness | ❌ FAIL | Hardcoded 24 yogas / 15 doshas; ignores L0's 175-yoga catalog; uncatalogued = silent drop |
| L1 strength facts for Rahu/Ketu | Completeness | ❌ FAIL | Shadbala/AV/bhava-bala never computed for the nodes |
| L1 kala-bala | Completeness | ❌ FAIL | Hardcoded `is_daytime=True` → wrong for night births |
| L1 drik-bala | Completeness | ⚠️ WEAK | Stubbed to neutral 0.375, not computed from the aspect matrix |
| L1 dasha depth | Completeness | ⚠️ SCOPED | Prana (5th level) + KP avayogi/pratyayogi not emitted (documented) |
| L1 coverage of varga-yogas, special lagnas, Jaimini, Nadi/Hora dasha, AV-transit, gandanta | Completeness | ❌ GAP | Whole astrological fact-classes not computed anywhere (≈65–70% domain coverage) |
| **fact_id back-references (`_mock_fact_id_ref`)** | Integrity spine | ❌ **CRITICAL** | **CONFIRMED: does NOT match the real `_fact_id` formula — constituent_facts_array will not resolve** |
| Retrieval coverage of stored categories | Retrievability | ❌ FAIL | **Only ~8 of ~27 chart_facts categories have a tool (~30%)** |
| Retrieval of L0 classical corpus (yogas/doshas/remedies/texts) | Retrievability | ❌ FAIL | Stored, but **no tool exposes them** |
| Retrieval weak-tail | Retrievability | ⚠️ DROP | `holistic_bundle` caps graph at `LIMIT 110`; `query_dasha_periods` truncates to 9 |
| Planner/routing | Retrievability | ⚠️ RISK | No planner that guarantees all categories get queried; gaps are invisible to the LLM |
| Phantom chart_id | Hygiene | ⚠️ | A retrieval default still uses `362f9f17` (the DEAD phantom) — must be `482012f1` |

---

## §2 — PILLAR 1: Completeness (L0 + L1) — what silently drops

### §2.1 — The catalog-gating defect (the worst, already deep-dived)
`ga_structural` fires named yogas/doshas only from a **hardcoded 24/15 list in Python**, **never
reads L0's `brahma_yoga_catalog` (175 yogas, with a machine-readable `formation_rule_jsonb` built
for exactly this)**. A real configuration outside the list is never fired, never emitted, never
flagged. Same disease as the old MSR threshold-drop (Contamination C2), one layer lower. Full
analysis + fix in `GA_STRUCTURAL_COMPLETENESS_FINDING_v1_0`.

### §2.2 — Newly-found silent drops in the OTHER L1 writers
- **Rahu/Ketu carry no strength facts** — shadbala, ashtakavarga, bhava-bala, vimsopaka all skip
  the nodes (hardcoded 7-graha list). The LLM can never speak to nodal strength.
- **Kala-bala assumes daytime** (`is_daytime=True` hardcoded) — night-birth charts get a wrong,
  silently-stored value. (A correctness bug, not just a gap.)
- **Drik-bala stubbed** to a constant 0.375 instead of computed from aspects.
- **Sthana-bala dignity map has only 4 states** (missing mooltrikona/friend/enemy nuance).
- **Engine-gated panchanga yogas / sensitive points** — emitted only if the upstream engine
  returns them; if it doesn't compute a rare one, it silently vanishes (no "considered, absent" row).
- **Nakshatra/pada clamped** to valid range silently (invalid → reset to 1, not flagged).

### §2.3 — Whole astrological fact-CLASSES not computed anywhere (≈30–35% domain gap)
These are not bugs but **scope gaps** — a thorough acharya-grade system would compute them, and
right now the LLM can never see them because they don't exist:
varga-specific yogas (D9/D10/D60 yogas — only D1 yogas fire); special lagnas as full charts
(Karakamsha/Hora/Ghatika/Shri Lagna — only points, not lagnas-with-results); most Jaimini
constructs (Chara/Bhava dasha, Karakamsha chakra, rashi-drishti nuance); Nadi dasha + Hora dasha
(not in the 7 systems); Ashtakavarga TRANSIT (only natal AV); gandanta; guna (sattva/rajas/tamas)
classification; retrograde/combustion EFFECTS (state is stored, but its strength-modulation/phala
is not computed); integrated multi-varga strength (each varga independent, no convergence score).

**Verdict on Pillar 1:** raw structure ✅ complete; named/derived/varga/alternative-system layers
❌ materially incomplete, and the incompleteness is invisible (no "absent/uncatalogued" record).

---

## §3 — THE CRITICAL BUG: the fact_id back-reference is broken (cuts the anti-drift spine)

This is the single most important finding and it is **confirmed, not speculative.**

- Real base facts compute their ID as:
  `_fact_id = sha256("{category}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}")[:16]`
- But yoga/dosha (and L2-feeding) `constituent_facts_array` references are built by
  `_mock_fact_id_ref = sha256("{category}|{subject}|rupa|{chart_id_prefix}|{ayanamsha_id}|ga3_build")[:16]`
- **They differ in three fields**: `key` is hardcoded to `"rupa"` (real rows use `longitude`,
  `yoga_strength_score`, …); `chart_id` is truncated to its 8-char prefix; `build_id` is hardcoded
  to `"ga3_build"` (real rows use the actual build UUID).

**Consequence:** every `constituent_facts_array` built this way **points at fact_ids that do not
exist in `chart_facts`.** The whole project rests on "L2 references the L1 fact_id and inherits its
value, never re-derives" — the SIG.MSR.377 anti-drift rule. If the references don't resolve, MSR
*cannot* inherit L1's value, the grounding audit can't verify, and Bodha is built on broken links.
This must be fixed before any bo_ writer runs. (It also means the "mock" naming is honest — it was
never wired to resolve.)

---

## §4 — PILLAR 2: Retrievability — what the LLM cannot reach

Even for facts that ARE stored correctly, the LLM can only see them if a retrieval tool exposes
them. The audit found **~13 tools covering only ~8 of ~27 chart_facts categories (~30%).**

### §4.1 — Stored-but-UNREACHABLE categories (no tool exists)
shadbala / dik-kala-cheshta-etc · ashtakavarga (bindus) · bhava-bala · vimsopaka · **panchanga**
(tithi/vara/nakshatra/yoga/karana) · **sade-sati** · saham · arudha · karaka · **alternative dashas
(Yogini, Jaimini/Chara, Kalachakra, Ashtottari, Mudda, KP)** — only Vimshottari is queryable ·
varshaphal/tajaka · transit. **And the entire L0 corpus:** `brahma_yoga_catalog`,
`brahma_dosha_catalog`, `brahma_remedy_corpus`, `classical_text_chunks`, `sutravali_rules` — all
stored, **none exposed by a tool.** So the LLM cannot cite a classical yoga definition or a remedy
even though they're in the database.

### §4.2 — Weak-tail truncation in the tools that DO exist
- `holistic_bundle` fetchGraphEdges: **`LIMIT 110`** — silently returns ~110 of ~2,000 edges.
  Directly violates "every aspect, high or low confidence, must surface."
- `query_dasha_periods`: returns first **9** mahadashas only — can't reach the full tree.
- (Most other tools return all rows — good — but these two re-drop exactly the weak tail you protect.)

### §4.3 — No planner guarantees coverage
Tools are registered per request; the LLM must know to call each. There is no
planner/dispatcher that ensures, for a "tell me everything" query, that *every* relevant category
is queried. So even reachable facts can go unqueried — a silent gap at answer time.

### §4.4 — Phantom chart_id in a retrieval default
A retrieval default still references `362f9f17` (the DEAD phantom) instead of the canonical
`482012f1`. Per CLAUDE.md this must never appear; it risks querying a non-existent chart.

---

## §5 — Things you may not have named (asked for, unprompted)

1. **Absence must become a first-class fact.** The deepest structural fix for completeness: when a
   configuration is computed-present but has no catalog match / no classical coverage, emit an
   explicit `uncatalogued_configuration` / `no_classical_coverage` row. Then "the LLM can't see it"
   becomes impossible — absence is queryable. This is the architectural realization of "never drop."
2. **A coverage manifest / self-audit asset.** A build-time report per chart: "N configurations
   present, M named, K uncatalogued, P categories with a retrieval tool, Q without." Makes both
   pillars *measurable* and regression-testable, instead of discovered by accident (as here).
3. **Single source of truth for definitions.** Yoga/dosha definitions live in THREE places now
   (L0 catalog 175, L1 hardcode 24, L2 G52 predicates). Collapse to ONE — L0 catalog — read by L1,
   annotated by L2. Eliminates drift by construction (the B.3 mandate).
4. **A retrieval-completeness contract test.** An automated check: every `chart_facts.fact_category`
   MUST have ≥1 retrieval tool, or the build flags it. This turns Pillar 2 into a CI gate.
5. **Fact_id stability policy.** fact_id embeds build_id, so it changes every rebuild — meaning L2
   references break on every L1 rebuild unless references are regenerated in lockstep. Decide:
   stable content-hash IDs (no build_id) vs. regenerate-references-on-rebuild. Today this is
   undefined and is a latent drift source independent of the §3 bug.
6. **Confidence/epistemic tier must travel to the LLM.** The weak-tail isn't just "include it" —
   each fact should carry its strength + verification tier so the LLM can SAY "low-confidence." The
   schema supports it; the tools must return it, not strip it.
7. **Bodha should be a pure projection, not a re-computation.** Resolves the earlier architecture
   question: with §3 fixed and §2.1 catalog-driven, MSR = deterministic transform of ga_structural
   (one fact → one signal, inherit value), and G52 = metadata annotation only (NOT a firing engine).
   This is the only design that doesn't reintroduce drift.

---

## §6 — The intervention program (sequenced; brief in Cowork → execute in Antigravity)

**Wave 0 — Stop the bleeding (correctness, before any Bodha build):**
- W0.1 Fix `_mock_fact_id_ref` → real `_fact_id` (resolvable references). [CRITICAL, §3]
- W0.2 Fix kala-bala day/night; drik-bala from aspects; Rahu/Ketu strength. [§2.2 correctness]
- W0.3 Remove phantom `362f9f17` default → `482012f1`. [§4.4]

**Wave 1 — Completeness, no silent drops (L0+L1):**
- W1.1 ga_structural reads L0 `brahma_yoga_catalog`/`dosha_catalog` (single source). [§2.1, §5.3]
- W1.2 Emit `uncatalogued_configuration` + `no_classical_coverage` facts. [§5.1]
- W1.3 Remove orb-threshold drops → emit with low strength (column, not gate). [§2.2]
- W1.4 Scope decision on the fact-CLASS gaps (§2.3): which to build now vs later (varga-yogas,
  special lagnas, Jaimini, Nadi/Hora dasha, AV-transit, gandanta, guna). Native prioritizes.

**Wave 2 — Retrievability (the second pillar):**
- W2.1 Add the missing retrieval tools: strength, ashtakavarga, panchanga, sade-sati, alternative
  dashas, sensitive points, varshaphal, L0 catalog (yogas/doshas/remedies/texts). [§4.1]
- W2.2 Remove weak-tail caps (`LIMIT 110`, dasha 9-slice) → paginate, don't truncate. [§4.2]
- W2.3 Ensure tools return strength + epistemic tier. [§5.6]
- W2.4 Planner/coverage guarantee + the retrieval-completeness CI gate. [§4.3, §5.4]

**Wave 3 — Make it measurable + Bodha-ready:**
- W3.1 Coverage-manifest self-audit asset. [§5.2]
- W3.2 Fact_id stability policy. [§5.5]
- W3.3 Re-confirm Bodha = projection / G52 = metadata-only; THEN resume bo_laksana. [§5.7]

**Scope note:** Waves 0–1 reopen L1 (a sealed layer) — native approval + version bump required
(CLAUDE.md §L). All writer changes are to writer-internal logic, NOT the FROZEN orchestrator
contract. Bodha work pauses until Wave 0 + the §3 fix land — it cannot be built on broken
references and a dropping L1.

---

## §7 — Decisions for the native
1. Approve this as the governing intervention program (supersedes "proceed to bo_laksana now")?
2. Approve reopening L1 for Waves 0–1?
3. Prioritize the §2.3 fact-class gaps — build-now set vs. deferred set?
4. Confirm the architectural principles in §5 (absence-as-fact, single-source definitions,
   coverage CI gate, Bodha-as-projection) as binding for the rebuild?

---

*End of MARSYS_DATA_INTEGRITY_DEEP_AUDIT_v1_0. Verdict: the goal — complete, deep, retrievable
deterministic insight — is NOT met today. Raw structure is complete; named/derived facts leak via
catalog-gating; the fact_id back-reference is broken; and ~70% of stored categories plus the entire
L0 corpus are unreachable by the LLM. All fixable, sequenced in §6. Both pillars become measurable
via the coverage manifest + CI gate. Bodha must wait for Wave 0.*
