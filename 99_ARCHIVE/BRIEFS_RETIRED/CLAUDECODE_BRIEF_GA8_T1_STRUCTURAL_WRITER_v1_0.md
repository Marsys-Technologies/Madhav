---
artifact: CLAUDECODE_BRIEF_GA8_T1_STRUCTURAL_WRITER_v1_0.md
canonical_id: GA8_T1_STRUCTURAL_WRITER_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10
authored_for: Claude Code in Antigravity IDE (autonomous conductor sub-agent)
campaign: L1_GANITA_BUILD_CAMPAIGN_v1_0 (Wave 4, asset ga_strength/structural — the synthesis feeder)
delivery_model: 1 branch, plan-then-execute, no human gate (agent gate-validators per campaign §E)
governing_principle: deterministic accuracy over volume; floors are aspirational targets, not gates
design_source: 00_ARCHITECTURE/A8_T1_STRUCTURAL_SPEC_v1_0.md (LOCKED — category authority)
depends_on: GA3 (schema), GA4 (panchanga baselines), GA5 (sensitive points), GA6 (varga contributions), GA7 (dasha timeline), G12 yoga library, G13 dosha library, G17 aspect rules, G18 friendship, G19 karaka
---

# GA8 — T1 Structural Facts Writer — Antigravity Execution Brief v1.0

## §0 — Read first (authoritative design sources)

- `00_ARCHITECTURE/A8_T1_STRUCTURAL_SPEC_v1_0.md` — **the category authority.** ~35 categories (§2, groups A–O), per-category two-pass (§3), row-count ~11,000/chart (§4), citations (§5), 6 MVs (§6), tool contract (§7), **data-flow boundaries (§8 — what GA8 consumes from GA3–GA7 and produces for L2)**.
- `00_ARCHITECTURE/GA3_CHART_FACTS_WRITER_v1_0.md` — schema, atomic grain, prime directive, FORENSIC gate.
- `00_ARCHITECTURE/L1_GANITA_BUILD_CAMPAIGN_v1_0.md` — §B DAG (GA8 runs AFTER GA3–GA7; it joins their rows), §E gate-validators.

## §1 — Reality reconciliation (apply over the older spec)

A8 LOCKED 2026-05-29. **Translate:**

1. **Engine = PyJHora** for any positional recomputation, but **A8 is mostly a JOIN-and-evaluate writer**: it consumes already-written GA3–GA7 atoms from `chart_facts`/`chart_divisionals`/`ganita_dashas` via SQL and evaluates classical predicates (G12/G13/G17/G18/G19) against them. No `natal_engine`. **No JH-parity oracle** — two-pass is predicate-vs-independent-classical-re-derivation + algebraic invariants + classical-worked-example matching (Sage Parashara's chart, BV Raman's 300 Combinations).
2. **Asset id = `ga_strength`** (the campaign's structural/strength asset; A8 "T1 structural" maps here). Target table = **`chart_facts`** (these are derived facts, atomic). All categories ayanamsha-DEPENDENT → 5 rows per key.
3. **Classifications STAY in L1.** Per the campaign decision, A8's structural classifications (functional benefic/malefic, composite-state well-placed/afflicted, dosha/yoga ownership) are **deterministic predicate evaluations = facts**, and live in L1 — NOT pushed to L2. L2 (Bodha) consumes them; it does not own them. Keep them here.
4. **Postgres-direct. No audience tier. Floors aspirational** — ~11,000 is a target. Fire-check all 200+ G12 yogas; emit only those that genuinely fire with real constituents. Never fabricate a firing.

## §2 — Branch + topology

- Branch `feature/ga8-t1-structural-writer` off `main` **after GA3–GA7 land** (GA8 joins their rows — it is the convergence node of the L1 DAG). One PR when green.
- Target chart_id = **`482012f1-710e-4a25-994a-93821f5871aa`** (canonical; keyed). Parameterize. `362f9f17` dead.
- **Dependency-strict:** GA8 must NOT run before GA3–GA7 have written the native's rows. Step 0 of the writer: verify the consumed categories exist for `482012f1` (`graha_position`, `varga_dignity`/`varga_saptavargaja_bala_component`, `karaka_chara_position`, `chart_dashas` rows, panchanga baselines). If any upstream is absent → halt-and-report, do NOT compute against missing atoms.

## §3 — The ~35 categories (A8 §2 — implement every group)

Implement all of A8 §2 groups A–O. Do not drop entries. Highlights:
- **A Aspects (6):** `aspect_parashari_given`/`_received` (quarter-strength 1.0/0.75/0.5/0.25 per Q1), `aspect_jaimini` (rasi-drishti 12×12), `aspect_tajik` (5 types), `conjunction_within_orb` (10° default per Q2 — `single`/geometric), `aspect_matrix_summary`.
- **B Shadbala (8 + V + W):** 6 sub-balas + total (rank/required/surplus) + ishta/kashta + `graha_vargottama_amplification_factor` (W) + `graha_saptavargaja_bala_component` pulled from GA6 (V). *(Note: GA3 §6.2 already ships shadbala. GA8 must reconcile — do NOT double-write. If GA3 wrote `graha_shadbala_*`, GA8 consumes + extends with W/V amplification; if not, GA8 writes them. Confirm ownership at Step 0 to avoid duplicate `fact_id` collisions.)*
- **C Bhava Bala (7 + composites):** 6 sub-balas/house + total + `house_strength_classification_rollup` (kendra/trikona/dushtana composites).
- **D Ashtakavarga (8 incl. Anubindu):** BAV 96 cells, pinda sodhita/bhinna/sarva, kakshya, trikona/ekadhipathya shodhana, `ashtakavarga_anubindu` (Q9). *(Same reconcile-with-GA3 note as shadbala.)*
- **E Vimsopaka (4):** consumed from GA6 per-varga emissions.
- **F Yogas (200+ from G12):** `yoga_fires` per fired yoga — name, `constituent_facts_array` (fact_id refs), classical_citation_id, `yoga_strength_score` (AI), arudha attribution (J), `cancellation_flag` + `cancelled_by_yoga_name` (I), `mahapurusha_strength_bonus` (AE, Mahapurusha only). Two passes: fire-check, THEN cancellation pass.
- **G Doshas:** `dosha_fires` (G13), same shape, cancellation applied.
- **H Avasthas (5 schemes × 9):** baladi/jagrad/deepta/lajjitadi/sayanadi + `graha_avastha_lifetime_exposure_summary` (AB — joins GA7 dasha timeline × avastha state per period over 1950–2100).
- **I Composite graha-in-house strength (Q7):** TWO `formula_id` rows per (graha, house) — `bphs_weighted` + `simple_multiplication`; store `cross_formula_divergence`.
- **J Functional benefic/malefic (Q5):** TWO `formula_id` rows — `bphs_canonical` + `raman_variant` — per graha per Lagna; + `graha_yoga_karaka_flag` (R).
- **K Karakatva (30 significances, G19):** `karakatva_strength_per_significance` + `karaka_house_lord_overlap_flag` (Z).
- **L Structural relationships:** `graha_dispositor_chain` (walk to cycle, `chain_jsonb_atomic` + `cycle_detected_at_step_N` — sanctioned JSONB), `composite_dispositor_strength` (AH), `parivartana_pairs` (Maha/Khala/Dainya per BPHS Ch.27), `graha_composite_state_classification` (X — well-placed/weak/afflicted/debilitation-cancelled).
- **M Special states:** `graha_special_state_rollup` (T), `graha_effective_dignity_modified_by_aspects` (Y).
- **N Argala (P):** `argala_natal_matrix` (12×12) + `virodha_argala_natal_matrix` (12×12) — atomic per cell, NOT one blob.
- **O Esoteric/Jaimini:** `pranic_strength_per_graha` (AJ, two-pass vs G44), `jaimini_tri_deva_role_per_graha` (AK, consumed from GA5 brahma/vishnu/shiva), `graha_tri_deva_role_strength`.

AG (Tajik Hadda) cross-references GA6 — no duplicate emission. AF (Saturn-Jupiter mundane) skipped.

## §4 — Atomic grain (GA3 §5 — binding; A8 has tempting blobs)

The 12×12 argala/virodha matrices = **144 atomic rows each** (subject per house/sign, key per source), NOT a JSONB blob — a reviewer must be able to `WHERE house=7` them. Aspect matrices atomic per (source, target). The ONLY sanctioned JSONB here: `chain_jsonb_atomic` (dispositor chain is an ordered irreducible walk), `constituent_facts_array` (a yoga's fact_id list), `quarter_intensity_rationale_jsonb`-style rule-rollups where the rule SET is the atom. Everything dignity/strength/flag = atomic columns/keys. The atomic-grain gate (campaign §E) audits this writer hardest after GA9.

## §5 — Two-pass verification (A8 §3 — per-category, MANDATORY minimum two_pass_verified)

Implement A8 §3 table verbatim. `single` only for `conjunction_within_orb` (geometric). Everything else two-pass: aspects (geometric vs G17-rule vs matrix-symmetry invariant), shadbala (engine vs BPHS Ch.27–32 vs Parashara example), yoga_fires (G12 predicate vs independent classical re-derivation vs worked-example match), avasthas (vs BPHS Ch.45), composite strengths (both formulas, divergence stored), argala (vs Jaimini Sutram Ch.5 example). `divergent_flagged` → halt + `CONDUCTOR_HALT_LOG.md`.

## §6 — FORENSIC + internal-consistency gate

Built on GA3–GA7 outputs that each passed FORENSIC. GA8's own gate is **internal consistency**: e.g., a yoga that requires "Jupiter in kendra in own/exaltation" must agree with the locked positions (Jupiter's actual house/dignity from GA3); a Mahapurusha firing must be reproducible from the atoms it cites in `constituent_facts_array`. Spot-assert a known structural fact for the native if available (e.g., Lagna=Aries makes Mars the Lagna lord — functional-class and yoga-karaka computations must reflect that). Do NOT copy A8's illustrative examples (e.g., "Saturn shadbala 4.19 rupa", "Hamsa Mahapurusha fires") uncritically — verify against the native's actual atoms.

## §7 — Materialized views (A8 §6)

`mv_chart_yogas_fired_summary`, `mv_chart_aspect_matrix`, `mv_chart_t1_composite_strengths` (new here) + `mv_chart_shadbala_summary`/`_bhava_bala_summary`/`_ashtakavarga_summary` (already declared in GA3 — refresh, don't redeclare). Natal-fixed; refresh synchronous at build close.

## §8 — Downstream contract (A8 §8 — GA8 is the L2 feeder)

GA8 PRODUCES the rows L2 Bodha consumes: yoga firings → MSR signals; composite strengths → salience; aspect matrices + dispositor chains → CGM edges; weakest grahas by shadbala → RM remedy candidates; top yogas → UCN digest. **Emit clean `constituent_facts_array` fact_id references on every yoga/dosha/composite row** — L2's `constituent_facts_array` back-references depend on these being correct and stable. This is GA8's most important downstream obligation.

## §9 — Build-state wiring

On success update `asset_throughput` for `ga_strength` (chart_id `482012f1`): row count + state transition. chart_id targeted = keyed. (If GA3 already lit `ga_strength` with shadbala, GA8 transitions it to its final built state after adding the structural categories — coordinate the state model so the bar reflects true completion.)

## §10 — Acceptance criteria (all `[verify-against: prod]`)

1. Upstream check: GA3–GA7 rows present for `482012f1` before GA8 computes; halt-clean if absent. `[verify: psql existence]`
2. `CHART_FACTS_SCHEMA.json` contains the ~35 A8 categories; drift_detector GREEN. `[verify: drift]`
3. All A8 §2 groups A–O emitted; no shadbala/ashtakavarga duplicate-fact_id collision with GA3. `[verify: psql GROUP BY fact_category + unique fact_id]`
4. 200+ G12 yogas fire-checked; only genuine firings emitted with `constituent_facts_array` fact_id refs; cancellation pass applied. `[verify: psql + constituent ref integrity]`
5. Both-formula categories (composite strength, functional class) emit two `formula_id` rows with divergence stored. `[verify: sample]`
6. Argala/virodha 12×12 = atomic rows (not blobs); only sanctioned JSONB used. `[verify: jsonb audit + row count = 144×2]`
7. Every category at its declared two-pass minimum (zero `divergent_flagged`; `conjunction_within_orb` may be `single`). `[verify: psql GROUP BY verification_pass_status]`
8. Internal-consistency: yoga firings reproducible from cited atoms; functional-class reflects Lagna=Aries. `[verify: assertion]`
9. `constituent_facts_array` refs resolve to real GA3–GA7 fact_ids (L2 contract). `[verify: FK-style join check]`
10. 6 MVs present/refreshed at build close. `[verify: \dm]`
11. `asset_throughput` ga_strength reflects true completion, keyed to `482012f1`; cockpit bar correct. `[verify: cockpit + psql]`
12. CI green; merge-verify before done.

## §11 — Rails

Reversibility, verify-before-promote, merge-verify, no JH-parity, Postgres-only, atomic-grain (sanctioned JSONB only), two-pass minimum, deterministic accuracy over volume, floors aspirational, never fabricate a yoga firing, **dependency-strict (halt if upstream absent)**, classifications stay L1. Halt on upstream-missing, two-pass divergence, duplicate fact_id, constituent-ref break.

---

*End of GA8 brief v1.0. The synthesis feeder: ~35 structural categories joining GA3–GA7, producing the facts L2 Bodha reads. Classifications stay L1.*
