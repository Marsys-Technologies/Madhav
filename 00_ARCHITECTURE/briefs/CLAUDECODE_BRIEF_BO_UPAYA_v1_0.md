---
artifact: CLAUDECODE_BRIEF_BO_UPAYA_v1_0.md
canonical_id: BO_UPAYA_BRIEF
version: 1.2
status: FOR_NATIVE_REVIEW (Batch 3 — RM remedial measures; the only asset that reads L0 today)
authored_by: Cowork (grounded in live RM schema + current bo_upaya writer) 2026-06-19
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
v1_1_changes: >
  The step-back DRILL (native 2026-06-19). bo_upaya is elevated from a grounded remedy CATALOG to a CAUSAL,
  HONEST, PERSON-FITTED remedial REASONER. Four supreme additions (§SUPREME): R1 causal-root targeting (treat
  the cause via dispositor-chain/pivot, not the symptom); R2 the DO-NOT-REMEDY cases (remediation_advisability —
  the ethical core: the instrument can refuse false hope); R3 remediation evidence ledger + mechanism (weight-of-
  evidence on each remedy, incl. dissents that WARN against it); R4 patient-fit + sequenced PROGRAM + question-
  reachable (adherence-ranked, root-first journey, reachable by life-question via the lens pattern). bo_upaya is
  the highest-stakes asset — the drill matters most here.
v1_2_changes: >
  R5 SUBSYSTEM-COVERAGE (§R5 — closes the F2 gap, native 2026-06-19). VERIFIED: the L0 brahma_remedy_corpus is
  DESIGNED to cover mantras/gemstones/charity/vrata/yantras/puja/tantric/AYURVEDIC/VASTU/behavioral — but the
  consuming path collapses it (the legacy remedy_type CHECK allows only {mantra,charity,gemstone,ritual}, and the
  writer queries the corpus WHERE planet=graha — PLANET-KEYED ONLY). So vastu (direction-keyed), medical
  (body-part-keyed), and nakshatra (nakshatra-keyed) remedials are structurally unreachable even though they're
  in the corpus design. R5 widens the taxonomy + queries by ALL affliction keys + verifies corpus content.
scope: bo_upaya ONLY — RM: owns 6 bodha_rm_* tables (resonances + prescriptions + dasha-windowed + dosha-bundles + pattern-remedies + chart-summary). Remedies grounded to L0 brahma_remedy_corpus. Depends on bo_laksana + bo_sangati.
data_plane: ALWAYS prod via Cloud SQL Auth Proxy (127.0.0.1:5433)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
governing:
  - L2_BODHA_JUDGMENT_SUBSTRATE_STRATEGY_v1_0.md (v1.1 FROZEN — remedies inherit confidence/epistemic + point at the ledgers)
  - L2_BODHA_STORAGE_ARCHITECTURE_v1_0.md (§STORAGE incl. embedding protocol for prescription_embedding_vec) + L2_BODHA_SCHEMA_REDESIGN_v1_0.md + A13_RM_SPEC_v1_0.md
  - GA_STRUCTURAL_REBUILD_VERIFY_v2_1.md (L1 authority) ; brahma_remedy_corpus (L0 G27 — the grounding source)
  - ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 (FROZEN WriterBase)
target_files:
  - platform/python-sidecar/pipeline/orchestrator/writers/bo_upaya.py (the heavy RM writer — already reads brahma_remedy_corpus)
  - migration(s): the 6 bodha_rm_* tables (enriched) + the SEED FIX (bo_upaya owns bodha_rm_resonances + summed count_sql)
  - platform/python-sidecar/bodha_writers/formulas.py (resonance_score_v1 + resonance_match_score_v1 — present)
  - platform/src/lib/retrieval/registry/layers/L2_bodha/ (remedy retrieval tools)
must_not_touch: FROZEN orchestrator contract; ga_* writers; bo_laksana; other bo_* writers.
---

# bo_upaya — RM: remedial measures, grounded to the classical corpus

## §0 — What this is
RM computes (a) the RESONANCE map — the weakest grahas + their remedy candidacy (resonance_score_v1), then
(b) per-tradition × per-category PRESCRIPTIONS grounded to L0 `brahma_remedy_corpus` (every remedy CITED, never
invented), (c) dasha-windowed STRUCTURE, (d) per-dosha bundles, (e) per-pattern/motif remedy themes, (f) chart
remedy priority/sequence. It is the instrument's "what can be DONE" surface — and it must be the most carefully
grounded + caveated of all, because it touches people's lives. DETERMINISTIC: resonance + match are versioned
formulas; remedies are L0-cited; NO invented remedies, NO LLM.

## §1 — Non-negotiables
Deterministic-first; no audience tier; no silent drops; per-chart isolation; **Trap 1** (resonance targets
REFERENCE the L1/MSR weakness signals; prescriptions REFERENCE the L0 remedy corpus id — never restate/invent);
**Trap 2** (resonance_score_v1 + resonance_match_score_v1 versioned; no narrative); FROZEN orchestrator contract
(`@register('bo_upaya')` WriterBase on ctx.db_conn, never commits, no asset_throughput); count_sql summed across
all 6 tables; floors aspirational. **Every remedy carries a classical citation or it is NOT written (grounding is absolute).**

## §2 — Preconditions
1. Proxy up; main == prod; max migration verified.
2. **bo_laksana + bo_sangati built** (resonance reads MSR weakness signals + the CDLM ledgers/pivots — the
   pivot, CDLM §C3, is the highest-value remedy target: fixing the root helps multiple domains).
3. `brahma_remedy_corpus` (L0 G27) present + queryable (the current writer reads it: planet + scaffold_status='live').
4. Apply the enriched 6-table migration + **THE SEED FIX** (§3).

## §3 — THE SEED FIX (pending — apply with this brief)
Per the asset-table map: `bo_upaya` must OWN `bodha_rm_resonances` as its PRIMARY table + summed count_sql across
all 6 RM tables (currently the seed points at bodha_rm_remedy_prescriptions). Fix the asset_registry seed row.
(And confirm bo_samvada is cleared off bodha_rm_resonances — done in the bo_samvada brief.)

## §4 — The build (6 tables)
- **bodha_rm_resonances** — per weakest-graha resonance target (resonance_score_v1); weakness/contradiction/
  domain/motif burden; weakest_rank; associated doshas/motifs/CDLM cells. **Targets reference MSR weakness signals.**
- **bodha_rm_remedy_prescriptions** — per target × tradition × category, grounded to brahma_remedy_corpus
  (`remedy_id_g27` + `classical_source_citation_id` MANDATORY); resonance_match_score (resonance_match_score_v1);
  counter-indications; feasibility/cost/time; cross-tradition corroboration; chronobiology (see §6 two-planes);
  acharya-review flag; prescription_embedding_vec (embedding protocol).
- **bodha_rm_dasha_windowed_prescriptions** — dasha-window STRUCTURE (which dasha-lord period a remedy aligns to)
  — NOT the dated timeline (§6).
- **bodha_rm_dosha_remedy_bundles** — per-dosha remedy bundles.
- **bodha_rm_pattern_remedies** — CDLM-pattern + CGM-motif → remedy themes.
- **bodha_rm_chart_summary** — chart-level remedy priority + phase-sequenced intensity profile.

## §5 — L0 GROUNDING (absolute — the asset's integrity spine)
Every prescription's `remedy_id_g27` + `classical_source_citation_id` resolves to a real `brahma_remedy_corpus`
row. A remedy with no classical citation is NOT written (logged as un-groundable, never invented). Carry
`classical_source_text_jsonb` (the cited remedy text) so retrieval returns the remedy WITH its classical basis.
This is the L0 bridge for this asset — grounded, never invented.

## §6 — TWO-PLANES discipline (RM has a temporal surface — keep it clean)
RM has `dasha_windowed`, `recommended_hora/choghadiya/lunar_phase`, `phase_duration`, `outcome_tracking`. These
touch TIME. Rule (consistent with the L2-timeless boundary):
- **STRUCTURE in L2:** which dasha-lord a remedy aligns to, the chronobiology RULE (e.g. "do on Saturn's hora"),
  the phase-sequence STRUCTURE — these are timeless remedial-rule facts → keep.
- **DATED TIMELINE → L3 Kāla:** the actual calendar windows ("do this on 2026-03-14") are NOT computed here.
  `dasha_windowed` stores the structural alignment (lord), NOT dated rows; `outcome_tracking_placeholder_jsonb`
  stays empty for L4/L5. Do NOT compute dated remedy schedules (that's L3/serve-time).

## §7 — JUDGMENT inheritance (the strategy at the remedy level)
- **Confidence + epistemic on each prescription:** classical_strength_rating + cross_tradition_corroboration_count
  + a structured epistemic (is the remedy classically well-attested or contested? traditions agree or differ?).
  So the LLM presents "strongly-attested remedy" vs "one-tradition suggestion" honestly.
- **The PIVOT as the priority remedy target (Move-1/CDLM tie-in):** the chart's pivot (CDLM §C3 — the root
  factor explaining multiple domains) is the highest-leverage remedy target (fix the root, help many domains).
  Rank pivot-targeting remedies highest in bodha_rm_chart_summary.
- **Acharya-review gate (the ethical spine):** `requires_acharya_review_flag` set for any remedy that is
  high-impact / contested / has counter-indications — the instrument FLAGS where a human acharya must vet. This
  is fidelity to the research-instrument-not-fortune-teller north star (remedies are the highest-stakes output).
- **Counter-indication + compatibility graph:** incompatible_with / prerequisite prescription arrays populated —
  so the LLM never recommends a contradictory or out-of-sequence remedy set.

## §STORAGE COMPLIANCE (storage §4B)
- **Embedding protocol** for `prescription_embedding_vec` — SAME shared model constant (text-multilingual-embedding-002,
  768-dim, HNSW) as bo_samskara/L0; stamped; the cross-layer CI check covers it. (Coordinate with bo_samskara's shared module.)
- **S5** target_graha, tradition, remedy_category, requires_acharya_review_flag, resonance_match_score = real
  indexed columns (already are); the prescription detail stays jsonb.
- **S2** chart_id leads indexes.

## §8 — Anti-drift + verification
1. **Grounding:** EVERY prescription resolves to a real brahma_remedy_corpus row (zero invented; zero un-cited written).
2. **Resonance targets** reference real MSR weakness signals (Trap 1).
3. **Acharya check:** the top resonance target = the chart's genuinely weakest/most-afflicted graha (verify
   against ga_strength + the ledgers; e.g. coherent with the native's known weak points).
4. **Two-planes:** no dated remedy schedules computed; dasha_windowed = structural alignment only.
5. Embedding consistency (same model as L0/bo_samskara). Idempotent; no silent drops; FORENSIC unaffected.

## §9 — Retrieval
Extend `L2_bodha/`: `query_remedies(chart, graha|domain|dosha)` → prescriptions WITH classical citation +
strength + counter-indications + acharya-review flag + confidence; `query_resonance_targets(chart)` → the ranked
weakest grahas (pivot-first); semantic remedy search (HNSW on prescription_embedding_vec). Every return carries
the classical citation (grounded) + the acharya-review flag (honest). Coverage gate: all 6 RM tables reachable.

## §10 — Acceptance
- [ ] 6 RM tables populated; **SEED FIX applied** (bo_upaya owns resonances + summed count_sql).
- [ ] **L0 grounding absolute:** every prescription cites a real brahma_remedy_corpus row; zero invented; un-groundable logged not written.
- [ ] Resonance targets reference MSR weakness signals; pivot ranked as top remedy target.
- [ ] **Two-planes:** structure + chronobiology RULES kept; NO dated schedules (L3); outcome_tracking empty (L4/L5).
- [ ] **Judgment:** per-remedy confidence/epistemic; acharya-review flag set for high-impact/contested; counter-indication + compatibility graph.
- [ ] Embedding protocol on prescription_embedding_vec (shared model; CI check). Storage compliance.
- [ ] **R1 causal-root:** affliction_cause_class + causal_root_ref; root-targeting remedies ranked highest.
- [ ] **R2 do-not-remedy (ethical core):** remediation_advisability {indicated/not_indicated/caution_acharya_only} + reason; false-weakness (neechabhanga) / backfiring / karmically-load-bearing cases return "no remedy indicated — here's why".
- [ ] **R3 evidence ledger:** remedy_support_strength + stated_mechanism + dissents (texts warning against); weight-of-evidence per remedy.
- [ ] **R4 fit/program/question:** adherence ranking; dependency-ordered sequenced program with reasoning; remedies reachable by domain/life-question with anti-tunnel-vision guard.
- [ ] **R5 subsystem-coverage:** remedy_category widened (graha/medical-ayurvedic/vastu/nakshatra/behavioral — drop the 4-type legacy CHECK); corpus queried by ALL affliction keys (planet ∪ nakshatra ∪ direction ∪ body_part ∪ dosha), NOT planet-only; per-subsystem remedial-coverage audit — every diagnosed affliction class has ≥1 grounded remedy OR is flagged remedy_corpus_gap (L0-expansion task, never invented).
- [ ] New retrieval: query_remedy_program, query_remedies_for_problem; advisability + mechanism + dissents in every return.
- [ ] query_remedies + query_resonance_targets + semantic tools; coverage gate; FROZEN contract; migration + seed fresh.

---

# §SUPREME — from a grounded remedy CATALOG to a CAUSAL, HONEST, PERSON-FITTED remedial REASONER (drill 2026-06-19)
*bo_upaya is the ONLY asset whose output a human might ACT on (spend money, perform a ritual). So supreme means
two things at once: maximize genuine remedial completeness AND be ruthlessly honest about efficacy + limits. The
leap: from "here are cited remedies for your weak planets" to "here is what is actually wrong at the ROOT, what
genuinely helps + how strongly the tradition backs it, what you can realistically DO, in what ORDER — and where
the honest answer is to do NOTHING." All deterministic; all L0-grounded; never invented.*

## §R1 — CAUSAL-ROOT TARGETING (treat the cause, not the symptom)
A master doesn't strengthen weak planets blindly — they reason about the CAUSAL CHAIN of the affliction: weak
INTRINSICALLY (debilitation → strengthen directly), weak BECAUSE its dispositor is afflicted (treat the
dispositor FIRST), or weak BY ASSOCIATION (it's fine; the malefic co-tenant is the issue). The remedy differs
completely by cause. Add to bodha_rm_resonances: `affliction_cause_class` ∈ {intrinsic, dispositor_derived,
associational, functional} + `causal_root_ref` (the CGM dispositor-chain node / the CDLM pivot §C3 that is the
ROOT). Rank ROOT-targeting remedies highest — "treating the root, which helps 3 downstream domains" beats
"treating a symptom." This is the remedial analog of the pivot insight.

## §R2 — THE DO-NOT-REMEDY CASES (the ethical core — the one place the instrument refuses false hope)
A genuine master often says "don't remedy this." A fortune-telling product ALWAYS sells a remedy. The instrument
must be able to say NO. Add a first-class `remediation_advisability` ∈ {indicated, not_indicated,
caution_acharya_only} + `advisability_reason_jsonb` (the classical basis), for the cases:
- **karmically load-bearing** — the difficulty is the lesson (classically, some afflictions are not to be remedied).
- **backfiring** — strengthening a functional MALEFIC for the lagna would HARM (the remedy is worse than the condition).
- **FALSE weakness** — a debilitated graha with NEECHABHANGA / cancellation is NOT actually weak → no remedy needed.
- **cure-worse-than-condition** — high counter-indication burden.
When not_indicated, the asset stores the REASON, and retrieval returns "no remedy indicated — here's why." This
is the deepest expression of the research-instrument-not-fortune-teller north star, on the asset where it matters most.

## §R3 — REMEDIATION EVIDENCE LEDGER + MECHANISM (weight-of-evidence on remediation)
Beyond a single citation: each remedy carries HOW STRONGLY the tradition supports it for THIS affliction. Add:
`remedy_support_strength` + `cross_tradition_corroboration` (already partly present) + `stated_mechanism_jsonb`
(WHY it works — "the gem channels the planet's ray" vs "tradition says so") + `dissents_jsonb` (texts that WARN
AGAINST this remedy — the opposing evidence). So the LLM says "strongly-attested across BPHS + Phaladeepika +
Lal Kitab, works by X" vs "single-tradition, uncertain mechanism — caution." The weight-of-evidence engine (Move 1)
applied to remediation.

## §R4 — PATIENT-FIT + SEQUENCED PROGRAM + QUESTION-REACHABLE
- **Patient-fit (adherence ranking):** the most powerful remedy nobody performs helps no one. Rank remedies by
  REALISTIC ADHERENCE (the schema's feasibility/cost/time/complexity columns become a MATCHING dimension, not
  just attributes) alongside classical strength — a usable simple mantra can outrank an unusable tantric ritual.
- **Sequenced PROGRAM (a journey, not a menu):** compose the dependency-ordered remedial program in
  bodha_rm_chart_summary — root-first (R1), prerequisite chains (the schema's prerequisite/incompatible arrays),
  WITH the reasoning for the order ("stabilize the dispositor 3 months, THEN strengthen the karaka"). Hand a path.
- **Question-reachable (the lens pattern):** remedies reachable by life-DOMAIN + life-PROBLEM ("how do I improve
  my career", "why this recurring obstacle") via the resonance target's domain burden + the CDLM ledger — with
  the bo_drishti ANTI-TUNNEL-VISION guard (don't lose an unexpected-but-relevant remedy). People don't ask "how
  do I strengthen Saturn"; they ask about their life.

## §R5 — SUBSYSTEM-COVERAGE (the F2 gap closure — RM must remedy EVERY subsystem that diagnoses)
**The gap (verified 2026-06-19):** we elevated bo_upaya's REASONING but its REMEDY REACH was planet-only. The L0
`brahma_remedy_corpus` (asset bg_remedies / "Upāya-kośa") is DESIGNED to hold mantras / gemstones / charity /
vrata / yantras / puja / tantric / **AYURVEDIC / VASTU** / behavioral — but two things collapse it:
1. the legacy `remedy_type` CHECK allows only `{mantra, charity, gemstone, ritual}` (too narrow);
2. the writer queries `brahma_remedy_corpus WHERE planet = graha` — **PLANET-KEYED ONLY.**
So vastu (DIRECTION-keyed), medical (BODY-PART-keyed), and nakshatra (NAKSHATRA-keyed) remedials are structurally
UNREACHABLE — even though they exist in the corpus design. **Principle: RM completeness must SPAN every subsystem
that DIAGNOSES an affliction.** If a subsystem can diagnose it, RM must be able to remedy it.

**The closure (three parts):**
1. **Widen the remedy taxonomy.** RM `remedy_category` must include: graha (mantra/gem/charity/ritual/yantra),
   **medical/ayurvedic** (dosha-pacifying, body-part-specific, herb/lifestyle), **vastu** (directional
   corrections), **nakshatra** (nakshatra-deity propitiation, nakshatra-lord, tara-timing), behavioral. Drop the
   4-type legacy CHECK; use the full corpus taxonomy.
2. **Query the corpus by ALL affliction KEYS, not just planet.** The resonance/affliction targets come from MANY
   subsystems — so query brahma_remedy_corpus keyed by: planet ∪ **nakshatra** (from ga_sensitive/nakshatra) ∪
   **direction** (from ga_vastu) ∪ **body_part** (from ga_medical body_part_watch/disease_tendency) ∪ **dosha**.
   A vastu affliction (weak SW corner) → its directional remedy; a medical affliction (Saturn afflicts knees) →
   its body-part/ayurvedic remedy; a nakshatra affliction → its nakshatra remedy.
3. **VERIFY corpus CONTENT (the one place an L0 task may remain).** The corpus is DESIGNED for these types —
   confirm it actually CONTAINS rows for medical/vastu/nakshatra keys. Where the corpus has the DESIGN slot but
   NO rows, that is an **L0 (Brahmagyan) corpus-expansion task** — flag it (do NOT invent remedies to fill it;
   grounding is absolute). bo_pramana_mapa's per-subsystem remedial-coverage audit (below) makes any hole visible.
**Coverage audit:** for every affliction class each subsystem diagnoses (graha/nakshatra/vastu/medical/dosha),
assert ≥1 grounded remedy exists OR flag the class as `remedy_corpus_gap` (an honest known-gap, not a silent miss).

---

# §ELEVATION (toward supreme)
- **U-1 [judgment] Remedy "evidence ledger" parity** — like CDLM domains, each remedy TARGET carries why it's a
  target (the converging afflictions) + the confidence the remedy addresses them — the weight-of-evidence applied to remediation.
- **U-2 [completeness] Remedy for the central TENSION, not just weak grahas** — the chart's central antagonistic
  axis (CDLM §C2) may need a balancing remedy, not a graha-strengthening one. Add tension-targeting remedies.
- **U-3 [retrievability] Remedy → domain impact map** — which domains a remedy is expected to help (via the
  resonance target's domain burden), so the LLM answers "what helps my career" not just "what strengthens Saturn."
- **U-4 [depth] Substitute + escalation chains** — gem→substitute-gem→mantra escalation (the schema has
  substitute_options); store the full fallback chain so the LLM can offer feasible alternatives.
- **U-5 [ethics] The acharya-review surface as a first-class retrieval facet** — the LLM can always say "this
  remedy needs a qualified acharya's vetting" where flagged — the highest-stakes honesty.

---
*End of BO_UPAYA v1.0. RM: resonance map (weakest grahas, pivot-first) → prescriptions GROUNDED to L0
brahma_remedy_corpus (every remedy cited, none invented — grounding is absolute) across 6 tables, with the SEED
FIX (owns resonances + summed count_sql). Two-planes kept clean (chronobiology RULES + dasha STRUCTURE in L2;
dated schedules → L3). Judgment inheritance: per-remedy confidence/epistemic, the pivot as top target, and the
acharya-review gate as the ethical spine (research-instrument, not fortune-teller). Embedding protocol on the
prescription vector. ELEVATION: remedy evidence-ledger parity, tension-targeting remedies, domain-impact map,
substitute/escalation chains, acharya-review as a first-class honesty surface.*
