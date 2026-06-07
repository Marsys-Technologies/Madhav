---
prompt_id: gemini.pattern_mining
version: "1.0"
status: CURRENT
phase: B.5
pass_type: GEMINI_PROPOSER_PASS_1
pass_2_authored_by: claude_via_pattern_mining_reconciler.py
produced_by: Madhav_M2A_Exec_9
produced_on: 2026-04-27
gemini_response_target: "035_DISCOVERY_LAYER/PROMPTS/gemini/responses/YYYY-MM-DD_B5_pattern_mining_batch<N>_raw.md"
registered_in: "06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json"
reconciler: "platform/python-sidecar/rag/reconcilers/pattern_mining_reconciler.py"
supersedes: null
changelog:
  - v1.0 (2026-04-27, Madhav_M2A_Exec_9): Initial version. B.5 pattern-mining Gemini Pass-1.
      Pattern Proposer role: Gemini receives curated cross-domain seed set and proposes
      pattern hypotheses with mechanism, counter-cases, classical basis, and alternatives.
      Claude Pass-2 validates each candidate against P1/P2/P5/P7/P8.
---

<!-- =====================================================================
PATTERN MINING PROMPT — gemini.pattern_mining v1.0
B.5 Discovery Engine — Session 1 of 3 (Exec_9)
======================================================================
HOW TO RUN EACH BATCH:

1. Read "SECTION A — ROLE" through "SECTION C — OUTPUT SCHEMA" below carefully.
2. In "SECTION D — PER-BATCH SEED SET", you (the executor) will paste 3–5 curated seeds
   for this batch. Each seed is a triplet: (signal_cluster, dasha_context, domain_crosslink).
3. Copy the full prompt body into Gemini 2.5 Pro.
4. Gemini outputs STRICT YAML in the pattern_proposals block.
5. Save Gemini's YAML response as:
     035_DISCOVERY_LAYER/PROMPTS/gemini/responses/YYYY-MM-DD_B5_pattern_mining_batch<N>_raw.md
   (replace YYYY-MM-DD with the run date and <N> with the batch number, e.g. batch1)
6. Commit the raw file and run:
     python -m rag.reconcilers.run_pattern_pipeline --batches B5_pattern_mining_batch<N>
   from platform/python-sidecar/.
====================================================================== -->

---

## SECTION A — ROLE AND CONTEXT

You are acting as the **Pattern Proposer** for the MARSYS-JIS Jyotish Intelligence System — a
research-grade astrology instrument built for the native Abhisek Mohanty (born 1984-02-05,
10:43 IST, Bhubaneswar, Odisha, India; Aries Lagna, D1 chart).

Your task is to **propose pattern hypotheses** — emergent structural patterns visible when multiple
astrological signals are viewed together across layer and domain boundaries. These are not
individual signal readings. They are patterns that only become visible when you hold several
signals simultaneously in working memory and ask: *what structural principle do these jointly imply
that no single signal alone could state?*

**Critical constraints:**
- You are a proposer, not a validator. Propose with intellectual honesty.
- Every proposed pattern must carry mechanism, counter-cases, classical basis, and ≥2
  alternatives (if significance ≥ 0.7) — Claude Pass-2 will validate these.
- Signal IDs in `signals_referenced` must come from the provided MSR seed set.
- Do NOT invent signal IDs. If you are unsure of a signal ID, omit it.
- This chart's subject (Abhisek Mohanty) has consented to this analysis. All outputs are
  for calibrated, auditable probabilistic research — not deterministic prediction.

---

## SECTION B — INPUT: CORPUS CONTEXT (FIXED ACROSS ALL BATCHES)

The following is fixed context you should hold throughout your proposal. These are established
facts from FORENSIC_ASTROLOGICAL_DATA_v8_0.md and validated signals from MSR_v3_0.md:

**D1 Core Positions:**
- Lagna: Aries (Mars-ruled), 12°23′55″ Ashwini nakshatra
- Sun: Capricorn 10H, 21°57′35″ Shravana nakshatra (near 11H in Chalit)
- Moon: Aquarius 11H, 27°02′48″ Purva Bhadrapada nakshatra
- Mars: Libra 7H, 18°31′38″ Swati nakshatra (also in 7H Chalit)
- Mercury: Capricorn 10H, 00°50′11″ Uttara Ashadha nakshatra (Vargottama in D9)
- Jupiter: Sagittarius 9H, 09°48′28″ Moola nakshatra
- Venus: Sagittarius 9H, 19°10′12″ Purva Ashadha nakshatra
- Saturn: Libra 7H, 22°27′04″ Vishakha nakshatra (Exalted)
- Rahu: Taurus 2H; Ketu: Scorpio 8H

**Key validated signals (sample from MSR_v3_0):**
- SIG.MSR.015 — Hidden Raja Yoga: Mars+Saturn exalted conjunction 7H Libra (strength 0.80, mixed valence)
- SIG.MSR.042 — D60 Saturn at Lagna: past-karma primary thread is Saturn-discipline (strength 0.75)
- SIG.MSR.040 — Saturn-Pisces Triple-Activation 2025–2028: transit + Kakshya + Sade Sati descending
- SIG.MSR.041 — D27 Lagna Pisces = D1 12H Pisces: strength-chart Lagna is natal Moksha house
- SIG.MSR.413 — Mercury Eight-System Convergence: primary operational planet (highest confidence signal)
- SIG.MSR.396 — Sade Sati paradox: peak achievement during Saturn adversity window
- SIG.MSR.397 — Wealth as dharmic output: AL=10H Capricorn, Saturn AmK
- SIG.MSR.228 — Gulika in Gemini 3H: calamity-significator in house of courage and communication

**Karaka designations:**
- Atmakaraka (AK): Saturn (highest degree in D1)
- Amatyakaraka (AmK): Saturn (second highest in classical assignment — note: Saturn = AK + AmK in
  this chart per alternate Jaimini counting; verify per your analysis)
- Putrakaraka (PK): Mars (children significator)
- Avayogi: Mars (fortune-reducer)
- Yogi: Moon

**Active dasha windows (key):**
- Mercury MD: 2010–2027 (peak professional window per SIG.MSR.413)
- Venus AD within Mercury MD: current sub-period
- Saturn MD begins: ~2027 (after Mercury MD ends)
- Sade Sati (Saturn transit Aquarius-Pisces-Aries): 2023–2032 (peak: Saturn in Pisces 2025–2028)

**CDLM cross-domain links established:**
- CDLM.D1.D5: Career ↔ Children — constrains (PK Mars in 7H Libra competes with career focus)
- CDLM.D1.D6: Career ↔ Spirit — feeds (AL=10H + Shree Lagna=7H)
- CDLM.D1.D7: Career ↔ Parents — mirrors (Sun as 5L in 10H career house)

**CGM graph edges established (sample):**
- SIG.MSR.413 → UCN.SEC.IV.3 (SUPPORTS): Mercury MD mechanism feeds career peak section
- SIG.MSR.396 → UCN.SEC.VII.4 (SUPPORTS): Sade Sati paradox supports temporal validation section
- SIG.MSR.015 → UCN.SEC.I.1 (SUPPORTS): Hidden Raja Yoga supports five foundation signatures

---

## SECTION C — OUTPUT SCHEMA (STRICT YAML — NO DEVIATION)

Your entire response must be the YAML block below. No prose before or after the YAML.
Do not include markdown code fences. Output raw YAML only.

```
pattern_proposals:
  - proposed_pattern_id: "<placeholder; reconciler assigns PAT.NNN>"
    claim_text: "<plain-English claim, ≤300 chars>"
    mechanism: "<≥1 sentence explaining how the signals causally combine into this pattern>"
    domain: "career|wealth|health|relationships|children|spiritual|parents|mind|travel|meta|cross_domain"
    signals_referenced:
      - "SIG.MSR.NNN"
    counter_cases:
      - "<known counter-example, or omit array entirely if none>"
    classical_basis: "<citation to classical text OR 'derivative — emergent pattern'>"
    alternatives:
      - "<7-karaka reading>"
      - "<8-karaka reading or alternate interpretation>"
    confidence: "LOW|MED|HIGH"
    significance: <0.0 to 1.0>
    is_forward_looking: <true|false>
    time_indexed_falsifier:                        # REQUIRED if is_forward_looking is true; omit if false
      verification_window_start: "YYYY-MM-DD"
      verification_window_end: "YYYY-MM-DD"
      falsifier_conditions:
        - "<condition under which this prediction is falsified>"
    notes: "<optional; use [EXTERNAL_COMPUTATION_REQUIRED] if the claim needs tool verification>"
```

**Output constraints:**
1. `signals_referenced` must contain ≥1 SIG.MSR.NNN ID from the fixed context above or the per-batch seed set.
2. `alternatives` must have ≥2 entries when `significance ≥ 0.7`.
3. `time_indexed_falsifier` is required (not null) when `is_forward_looking` is true.
4. `classical_basis` must be a verbatim citation if classical, else exactly: `derivative — emergent pattern`.
5. The YAML block is your complete response — no prose, no markdown fences, just the raw YAML.
6. Propose between 3 and 8 patterns per batch. Quality over quantity.

---

## SECTION D — PER-BATCH SEED SET

**[EXECUTOR: Replace this section with the curated seed set for this batch before running Gemini.]**

The seed set for each batch is a list of 3–5 signal clusters that span domain or layer boundaries.
Each seed contains:
- A signal cluster (2–5 SIG.MSR.NNN IDs that are already linked via CGM SUPPORTS edges)
- A relevant dasha context (which MD/AD window activates these signals)
- One or more CDLM cross-domain links or RM resonance hints

Curation guidance:
- Seeds drawn from the accepted SUPPORTS edge batches (cgm_supports_edges_manifest_v1_0.json
  and cgm_contradicts_edges_manifest_v1_0.json) are preferred.
- Each seed should span at least one cross-domain boundary (e.g., career + spiritual) OR one
  cross-layer boundary (e.g., L1 D1 fact → MSR signal → UCN synthesis claim) to be productive
  for pattern mining.
- Avoid seeds that are entirely within a single domain with no cross-link.

**Batch [N] — [date run] — Seed Set:**

```
seeds:
  - seed_label: "Seed_1"
    signal_cluster: ["SIG.MSR.NNN", "SIG.MSR.NNN"]
    dasha_context: "<MD/AD window>"
    cdlm_links: ["CDLM.D1.DX"]
    curation_note: "<why this cluster is productive for pattern mining>"
```

---

## SECTION E — EXAMPLES OF GOOD vs BAD PATTERNS

**GOOD pattern (cross-domain, non-obvious, mechanistically grounded):**
```yaml
claim_text: "Saturn AK + AmK dual-karaka confluence in exaltation forces karmic acceleration: professional peak coincides with peak karmic pressure, producing visible paradox."
mechanism: "AK (soul significator) and AmK (career significator) both map to Saturn in this chart. Saturn is exalted (Libra 7H) yet also the Sade Sati planet (crossing Moon-sign Aquarius 2023-2032). When the same planet governs soul purpose AND career dharma AND produces the adversity window, the chart cannot experience career peak without simultaneous karmic intensification — the domains are structurally entangled, not parallel."
signals_referenced: ["SIG.MSR.015", "SIG.MSR.040", "SIG.MSR.396"]
classical_basis: "Jaimini §2.1.12 (AK = primary soul-dharma governor); BPHS Ch.53 (Saturn transit adversity); BPHS Ch.7 Sl.1-3 (exaltation amplifies both benefic and malefic qualities)"
alternatives:
  - "7-karaka reading: Saturn AK makes career peaks inherently austere — the soul refuses easy success; the professional peak is real but comes with renunciation."
  - "8-karaka reading: Saturn AmK designation disputed in 8-karaka system (falls to Venus); if Venus is AmK, the karmic entanglement is partially reduced — the paradox is milder."
significance: 0.88
is_forward_looking: false
```

**BAD pattern (too narrow, single-signal, obvious):**
```yaml
claim_text: "Mercury is exalted in Virgo in the Navamsha."
# — This is a single L1 fact, not a pattern. Rejected.
```

---

*End of pattern_mining_v1_0.md. Reconciler: platform/python-sidecar/rag/reconcilers/pattern_mining_reconciler.py.*
*Supersedes: none. Registered in: 06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json (entry: gemini.pattern_mining v1.0).*
