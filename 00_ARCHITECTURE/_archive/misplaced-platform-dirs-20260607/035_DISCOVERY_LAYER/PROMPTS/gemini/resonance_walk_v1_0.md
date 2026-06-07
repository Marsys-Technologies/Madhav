---
prompt_id: gemini.resonance_walk
version: "1.0"
status: CURRENT
phase: B.5
pass_type: GEMINI_PROPOSER_PASS_1
pass_2_authored_by: claude_via_resonance_walk_reconciler.py
produced_by: Madhav_M2A_Exec_10
produced_on: 2026-04-27
gemini_response_target: "035_DISCOVERY_LAYER/PROMPTS/gemini/responses/YYYY-MM-DD_B5_resonance_walk_batch<N>_raw.md"
registered_in: "06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json"
reconciler: "platform/python-sidecar/rag/reconcilers/resonance_walk_reconciler.py"
supersedes: null
changelog:
  - v1.0 (2026-04-27, Madhav_M2A_Exec_10): Initial version. B.5 resonance-walk Gemini Pass-1.
      Resonance Proposer role: Gemini proposes cross-domain resonances BEYOND CDLM explicit cells.
      Each resonance bridges exactly 2 domains via a shared signal mechanism. Claude Pass-2
      validates against P1/P2/P5/P7/P8 + resonance-specific gates (cdlm_cells_referenced resolution,
      domains_bridged exactly 2 elements from canonical domain enum).
---

<!-- =====================================================================
RESONANCE WALK PROMPT — gemini.resonance_walk v1.0
B.5 Discovery Engine — Session 2 of 3 (Exec_10)
======================================================================
HOW TO RUN EACH BATCH:

1. Read "SECTION A — ROLE" through "SECTION C — OUTPUT SCHEMA" below carefully.
2. In "SECTION D — PER-BATCH SEED SET", paste 3–5 curated cross-domain candidate
   triplets for this batch. Each triplet specifies: (domain_pair, signal_cluster, cdlm_anchor).
3. Copy the full prompt body into Gemini 2.5 Pro.
4. Gemini outputs STRICT YAML in the resonance_proposals block.
5. Save Gemini's YAML response as:
     035_DISCOVERY_LAYER/PROMPTS/gemini/responses/YYYY-MM-DD_B5_resonance_walk_batch<N>_raw.md
   (replace YYYY-MM-DD with the run date and <N> with the batch label, e.g. resonance_batch1)
6. Commit the raw file and run:
     python -m rag.reconcilers.run_resonance_pipeline --batches B5_resonance_walk_batch<N>
   from platform/python-sidecar/.
====================================================================== -->

---

## SECTION A — ROLE AND CONTEXT

You are acting as the **Resonance Proposer** for the MARSYS-JIS Jyotish Intelligence System — a
research-grade astrology instrument built for the native Abhisek Mohanty (born 1984-02-05,
10:43 IST, Bhubaneswar, Odisha, India; Aries Lagna, D1 chart).

Your task is to **propose cross-domain resonances** — emergent structural bridges between exactly
two distinct life domains that arise because the same astrological signal mechanism operates
simultaneously in both. A resonance is NOT a CDLM explicit cross-link (those are already mapped);
it is a *deeper or emergent synchrony* that the CDLM matrix flags as relevant but does not fully
articulate. The resonance must articulate *why* the two domains move together structurally — not
merely that they co-occur.

**Critical constraints:**
- Each resonance bridges **exactly two domains** (`domains_bridged` is a 2-element array).
- The shared mechanism is the link — not circumstantial correlation but a shared planetary
  architecture (planet as AK/AmK/PK etc., nakshatra lord, divisional chart pattern, dasha engine)
  that produces outputs in both domains simultaneously.
- `cdlm_cells_referenced` must name the CDLM cells this resonance **extends or complements**.
  Use the format `CDLM.<domain1>.<domain2>` (e.g., `CDLM.career.spiritual`). If the CDLM cell
  is blank (null in CDLM_v1_1), the resonance is extending into new territory — mark it.
- `signals_referenced` must be MSR IDs from the corpus context or batch seed set. Do NOT invent.
- You are a proposer, not a validator. Propose with intellectual honesty and full alternatives.
- This chart's subject (Abhisek Mohanty) has consented to this analysis. All outputs are for
  calibrated, auditable probabilistic research — not deterministic prediction.

---

## SECTION B — INPUT: CORPUS CONTEXT (FIXED ACROSS ALL BATCHES)

### B.1 — D1 Core Positions

- **Lagna:** Aries (Mars-ruled), 12°23′55″ Ashwini nakshatra
- **Sun:** Capricorn 10H, 21°57′35″ Shravana nakshatra (near 11H in Chalit)
- **Moon:** Aquarius 11H, 27°02′48″ Purva Bhadrapada nakshatra
- **Mars:** Libra 7H, 18°31′38″ Swati nakshatra (also in 7H Chalit) — **Putrakaraka (PK)**
- **Mercury:** Capricorn 10H, 00°50′11″ Uttara Ashadha nakshatra (Vargottama in D9)
- **Jupiter:** Sagittarius 9H, 09°48′28″ Moola nakshatra
- **Venus:** Sagittarius 9H, 19°10′12″ Purva Ashadha nakshatra
- **Saturn:** Libra 7H, 22°27′04″ Vishakha nakshatra (Exalted) — **Atmakaraka (AK) + Amatyakaraka (AmK)**
- **Rahu:** Taurus 2H; **Ketu:** Scorpio 8H

**Karaka designations:**
- AK (Atmakaraka): Saturn (soul-dharma governor)
- AmK (Amatyakaraka): Saturn (career-dharma governor) — rare dual-karaka confluence
- PK (Putrakaraka): Mars (children significator — also Avayogi: fortune-reducer)
- Yogi: Moon

### B.2 — Key Validated Signals (from MSR_v3_0)

| Signal ID | Description |
|---|---|
| SIG.MSR.015 | Hidden Raja Yoga: Mars+Saturn exalted conjunction 7H Libra (strength 0.80, mixed valence) |
| SIG.MSR.040 | Saturn-Pisces Triple-Activation 2025–2028: transit + Kakshya + Sade Sati descending |
| SIG.MSR.041 | D27 Lagna Pisces = D1 12H Pisces: strength-chart Lagna is natal Moksha house |
| SIG.MSR.042 | D60 Saturn at Lagna: past-karma primary thread is Saturn-discipline |
| SIG.MSR.228 | Gulika in Gemini 3H: calamity-significator in house of courage and communication |
| SIG.MSR.396 | Sade Sati paradox: peak achievement during Saturn adversity window |
| SIG.MSR.397 | Wealth as dharmic output: AL=10H Capricorn, Saturn AmK |
| SIG.MSR.413 | Mercury Eight-System Convergence: primary operational planet (highest confidence signal) |

**Active dasha windows:**
- Mercury MD: 2010–2027 (peak professional window per SIG.MSR.413)
- Saturn MD begins: ~2027 (after Mercury MD ends)
- Sade Sati (Saturn transit Aquarius-Pisces-Aries): 2023–2032 (peak: Saturn in Pisces 2025–2028)

### B.3 — CDLM Cross-Domain Grid Summary (9×9)

The Cross-Domain Linkage Matrix (CDLM_v1_1) maps 9 domains × 9 domains. The cells below are
**POPULATED** (non-null) in the current CDLM — resonances may extend these:

| Cell | Domain Pair | Status |
|---|---|---|
| CDLM.career.children | Career ↔ Children | POPULATED |
| CDLM.career.spiritual | Career ↔ Spiritual | POPULATED |
| CDLM.career.parents | Career ↔ Parents | POPULATED |
| CDLM.career.wealth | Career ↔ Wealth | POPULATED |
| CDLM.career.health | Career ↔ Health | POPULATED |
| CDLM.career.relationships | Career ↔ Relationships | POPULATED |
| CDLM.career.mind | Career ↔ Mind | POPULATED |
| CDLM.spiritual.children | Spiritual ↔ Children | POPULATED |
| CDLM.spiritual.relationships | Spiritual ↔ Relationships | POPULATED |
| CDLM.wealth.health | Wealth ↔ Health | POPULATED |
| CDLM.relationships.children | Relationships ↔ Children | POPULATED |
| CDLM.relationships.parents | Relationships ↔ Parents | POPULATED |
| CDLM.parents.children | Parents ↔ Children | POPULATED |

**Cells that are BLANK (null) or only briefly touched in CDLM_v1_1 — strong resonance candidates:**
- CDLM.spiritual.wealth, CDLM.spiritual.health, CDLM.spiritual.parents, CDLM.spiritual.mind
- CDLM.wealth.relationships, CDLM.wealth.parents, CDLM.wealth.children, CDLM.wealth.mind
- CDLM.health.relationships, CDLM.health.children, CDLM.health.parents, CDLM.health.mind
- CDLM.children.mind, CDLM.parents.mind, CDLM.travel.* (all travel cells)

Your resonances should preferentially target **blank or thin CDLM cells** where the cross-domain
bridge is not yet explicitly articulated.

---

## SECTION C — OUTPUT SCHEMA (STRICT YAML — NO DEVIATION)

Your entire response must be the YAML block below. No prose before or after the YAML.
Do not include markdown code fences. Output raw YAML only.

```
resonance_proposals:
  - proposed_resonance_id: "<placeholder; reconciler assigns RES.NNN>"
    claim_text: "<plain-English statement of the cross-domain resonance, ≤300 chars>"
    mechanism: "<≥1 sentence: how the shared signal mechanism produces outputs in BOTH bridged domains simultaneously>"
    domains_bridged:
      - "career|wealth|health|relationships|children|spiritual|parents|mind|travel|meta"
      - "career|wealth|health|relationships|children|spiritual|parents|mind|travel|meta"
    signals_referenced:
      - "SIG.MSR.NNN"
    cdlm_cells_referenced:
      - "CDLM.<domain1>.<domain2>"
    counter_cases:
      - "<condition under which the resonance breaks — domains become independent>"
    classical_basis: "<citation to classical text OR 'derivative — emergent resonance'>"
    alternatives:
      - "<alternate framing that reduces or eliminates the cross-domain bridge>"
      - "<second alternative interpretation>"
    confidence: "LOW|MED|HIGH"
    significance: <0.0 to 1.0>
    is_forward_looking: <true|false>
    time_indexed_falsifier:                         # REQUIRED if is_forward_looking is true; omit if false
      verification_window_start: "YYYY-MM-DD"
      verification_window_end: "YYYY-MM-DD"
      falsifier_conditions:
        - "<condition under which this prediction is falsified>"
    notes: "<optional; use [EXTERNAL_COMPUTATION_REQUIRED] if tool verification needed>"
```

**Output constraints:**
1. `domains_bridged` must be exactly 2 elements from the canonical domain enum.
2. `signals_referenced` must contain ≥1 SIG.MSR.NNN ID from the corpus context or batch seed set.
3. `cdlm_cells_referenced` must contain ≥1 cell ID in CDLM.<d1>.<d2> format.
4. `alternatives` must have ≥2 entries when `significance ≥ 0.7`.
5. `time_indexed_falsifier` is required (not null) when `is_forward_looking` is true.
6. `classical_basis` must be a verbatim citation if classical, else exactly: `derivative — emergent resonance`.
7. The YAML block is your complete response — no prose, no markdown fences, just the raw YAML.
8. Propose between 3 and 6 resonances per batch. Quality over quantity.

---

## SECTION D — PER-BATCH SEED SET

**[EXECUTOR: Replace this section with the curated seed set for this batch before running Gemini.]**

Each batch seed set is a list of 3–5 cross-domain candidate triplets. Each triplet specifies:
- `domain_pair`: the two domains to bridge (from the blank/thin CDLM cells above)
- `signal_cluster`: 2–4 SIG.MSR.NNN IDs that jointly activate in both domains
- `cdlm_anchor`: the CDLM cell this resonance extends or complements
- `seed_rationale`: why the shared mechanism is architecturally compelling for this domain pair

**Batch [N] — [date run] — Seed Set:**

```
seeds:
  - seed_label: "Seed_1"
    domain_pair: ["career", "spiritual"]
    signal_cluster: ["SIG.MSR.NNN", "SIG.MSR.NNN"]
    cdlm_anchor: "CDLM.career.spiritual"
    seed_rationale: "<why Saturn AK/AmK or other karaka creates a structural bridge here>"
  - seed_label: "Seed_2"
    domain_pair: ["wealth", "health"]
    signal_cluster: ["SIG.MSR.NNN", "SIG.MSR.NNN"]
    cdlm_anchor: "CDLM.wealth.health"
    seed_rationale: "<Mars Avayogi + 8H Ketu mechanism>"
```

---

## SECTION E — EXAMPLES OF GOOD vs BAD RESONANCES

**GOOD resonance (shared mechanism, two domains genuinely entangled, non-obvious):**
```yaml
claim_text: "Saturn as AK (soul purpose) + AmK (career) creates a structural entanglement: no career move is purely professional — every career act carries soul-debt weight, and every spiritual renunciation has career consequence."
mechanism: "When a single planet governs both AK and AmK functions, the soul-dharma and career-dharma are not two parallel rivers but one channel. Saturn's exaltation in 7H Libra means career acts register simultaneously in the soul's karmic ledger — the two domains cannot operate independently even when the native attempts to separate them."
domains_bridged: ["career", "spiritual"]
cdlm_cells_referenced: ["CDLM.career.spiritual"]
signals_referenced: ["SIG.MSR.015", "SIG.MSR.042"]
alternatives:
  - "AK governs soul-level themes only; AmK is purely external career. The dual-karaka assignment does not entangle the domains — it just means the same planet rules both independently."
  - "The entanglement is timing-specific (only during Saturn MD, 2027+) — not a lifetime structural resonance."
significance: 0.87
```

**BAD resonance (correlation, not mechanism — no shared signal driver):**
```yaml
claim_text: "Career success leads to better health because successful people can afford healthcare."
mechanism: "Financial resources from career success fund health maintenance."
```
*Why bad: this is a generic correlation, not a chart-specific signal mechanism. It does not cite an MSR signal, does not reference a CDLM cell, and could be true for anyone regardless of chart structure.*

---

## SECTION F — PROMPT REGISTRATION

- **Prompt registered at:** `06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json`
  entry: `prompt_id: gemini.resonance_walk`, `version: 1.0`
- **Supersedes:** null (first version)
- **Reconciler:** `platform/python-sidecar/rag/reconcilers/resonance_walk_reconciler.py`
- **Two-pass ordering:** Gemini Pass-1 (this prompt) → Claude Pass-2 (reconciler)

---

*End of resonance_walk_v1_0.md — gemini.resonance_walk v1.0 — Produced at Madhav_M2A_Exec_10 (2026-04-27)*
