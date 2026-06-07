---
prompt_id: claude.contradiction_scan
version: "1.0"
status: CURRENT
phase: B.5
pass_type: CLAUDE_PROPOSER_PASS_1
pass_2_adjudicator: gemini
produced_by: Madhav_M2A_Exec_11
produced_on: 2026-04-27
gemini_response_target: "035_DISCOVERY_LAYER/PROMPTS/gemini/responses/YYYY-MM-DD_B5_contradiction_scan_gemini_pass2_batch<N>_raw.md"
registered_in: "06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json"
reconciler: "platform/python-sidecar/rag/reconcilers/contradiction_reconciler.py"
supersedes: null
changelog:
  - v1.0 (2026-04-27, Madhav_M2A_Exec_11): Initial version. B.5 contradiction scan Claude Pass-1.
      FLOW: CONTRADICTS (inverted two-pass). Claude Pass-1 hypothesizes internal corpus
      contradictions (signal polarity conflicts, karaka ambiguities, timing conflicts, p1_layer_bleed,
      p6_uvc_conflicts). Gemini Pass-2 adjudicates each hypothesis as CONFIRMED or REJECTED.
      ≥5 confirmed contradictions required for B.5 close.
---

<!-- =====================================================================
CONTRADICTION SCAN PROMPT — claude.contradiction_scan v1.0
B.5 Discovery Engine — Session 3 of 3 (Exec_11)
======================================================================
FLOW: CONTRADICTS — Inverted two-pass ordering.
  Claude Pass-1: Hypothesize contradictions from corpus analysis.
  Gemini Pass-2: Adjudicate each hypothesis CONFIRMED or REJECTED.

This prompt is Claude's own internal scan — Claude both writes the prompt
AND executes the scan in a single session, producing structured hypotheses
that are then passed to Gemini for adjudication in the next step.
====================================================================== -->

---

## SECTION A — PURPOSE AND SCOPE

You are executing Claude Pass-1 of the B.5 Contradiction Scan for the MARSYS-JIS Jyotish Intelligence System. Your task is to scan the corpus of MSR signals, patterns, resonances, and clusters for **internal contradictions** — cases where two or more signals, patterns, or registered entries make claims that structurally oppose each other given the native's chart.

This is NOT a red-team review. It is a systematic hunt for genuine internal conflicts — places where the corpus speaks with two voices on the same topic. The goal is surfacing conflicts the native and future sessions need to adjudicate, NOT resolving them here.

**Native:** Abhisek Mohanty, born 1984-02-05, 10:43 IST, Bhubaneswar, Odisha, India (Aries Lagna, D1).

---

## SECTION B — CHART CONTEXT (FIXED)

### B.1 — D1 Core Positions

- **Lagna:** Aries 12°23′55″ Ashwini (Mars-ruled)
- **Sun:** Capricorn 10H, 21°57′35″ Shravana
- **Moon:** Aquarius 11H, 27°02′48″ Purva Bhadrapada (Yogi planet)
- **Mars:** Libra 7H, 18°31′38″ Swati — **Putrakaraka (PK) + Avayogi + Lagna Lord**
- **Mercury:** Capricorn 10H, 00°50′11″ Uttara Ashadha (Vargottama in D9)
- **Jupiter:** Sagittarius 9H, 09°48′28″ Moola
- **Venus:** Sagittarius 9H, 19°10′12″ Purva Ashadha
- **Saturn:** Libra 7H, 22°27′04″ Vishakha (Exalted) — **AK + AmK (dual-karaka)**
- **Rahu:** Taurus 2H; **Ketu:** Scorpio 8H

### B.2 — Karaka Assignments

| Karaka | Planet | Notes |
|---|---|---|
| AK (Atmakaraka) | Saturn | Highest degree — 22°27′ |
| AmK (Amatyakaraka) | Saturn | Rare dual-karaka (also 22°27′; no separate AmK planet) |
| PK (Putrakaraka) | Mars | Also Avayogi and Lagna lord |
| Yogi | Moon | Fortune-amplifier planet |

### B.3 — Key L2.5 Register References

- **MSR:** 499 signals (SIG.MSR.001–SIG.MSR.496), canonical at `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md`
- **CDLM:** Cross-Domain Linkage Matrix v1.2, `025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md`
- **CGM:** Causal Graph Model v2.0, `025_HOLISTIC_SYNTHESIS/CGM_v2_0.md`
- **PATTERN_REGISTER:** 22 patterns (PAT.001–PAT.022), `035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_v1_0.json`
- **CLUSTER_ATLAS:** 12 clusters (CLUS.001–CLUS.012), `035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_0.json`

---

## SECTION C — CONTRADICTION CLASSES TO SCAN

Hunt for contradictions in the following classes. Each class has characteristic failure modes:

### C.1 — p1_layer_bleed
An L2 interpretation is stated as if it were an L1 fact, OR an L1 fact is incorrectly cited to support an L2 claim it does not make. Look for signals that cite chart positions imprecisely or assert interpretive claims without derivation ledger.

### C.2 — p6_uvc_conflict
A signal or pattern claims a relationship that directly contradicts a CDLM or CGM cell. Look for signals whose mechanism is opposite to what the CDLM records for that planetary combination.

### C.3 — karaka_ambiguity
The dual-karaka status of Saturn (AK + AmK) creates structural ambiguity: is Saturn signifying soul-dharma (AK function) or vocational function (AmK function) in a given signal? Look for signals that assign incompatible functions to Saturn without acknowledging the ambiguity.

### C.4 — domain_cross_claim
Two signals make incompatible predictions about the same life domain. Example: one signal says "Mars PK indicates progeny difficulty"; another says "Mars Lagna lord indicates strong first-child timing" — these may contradict without explicit reconciliation.

### C.5 — timing_conflict
Two time-indexed signals or patterns claim incompatible outcomes for the same dasha/antardasha window. Look for signals where dasha-period predictions cross.

### C.6 — signal_polarity_conflict
One signal's mechanism directly negates another's. Example: Signal A says "Saturn's 7H exaltation delays marriage"; Signal B says "Saturn's 7H placement accelerates commitment through discipline" — structural opposition requiring reconciliation.

---

## SECTION D — OUTPUT SCHEMA (STRICT YAML — NO DEVIATION)

Your output for each contradiction hypothesis must be structured YAML only. No prose before or after. Do not include markdown code fences. Output raw YAML only.

```
contradiction_hypotheses:
  - hypothesis_id: "CH.NNN"
    contradiction_class: "p1_layer_bleed|p6_uvc_conflict|karaka_ambiguity|domain_cross_claim|timing_conflict|classical_basis_conflict|signal_polarity_conflict"
    hypothesis_text: "<plain-English statement of the contradiction, ≤400 chars>"
    mechanism: "<how the two conflicting claims structurally oppose each other — ≥1 sentence>"
    domains_implicated:
      - "domain_name"
    signals_in_conflict:
      - "SIG.MSR.NNN"
      - "SIG.MSR.NNN"
    l1_references:
      - "<FORENSIC_v8_0 §-citation or CDLM/CGM cell reference>"
    claude_severity_prior: "LOW|MED|HIGH"
    resolution_options:
      - "<resolution path 1>"
      - "<resolution path 2>"
```

**Output constraints:**
1. `hypothesis_id` must be "CH.NNN" (temporary; replaced by CON.NNN on acceptance).
2. `contradiction_class` must be from the canonical enum in Section C.
3. `hypothesis_text` must be ≤400 characters, must not reference signals not in the corpus.
4. `signals_in_conflict` must contain ≥2 valid SIG.MSR.NNN IDs that are in the 499-signal corpus.
5. `l1_references` must cite specific FORENSIC_v8_0 sections, CDLM cells, or pattern IDs — no generic citations.
6. `claude_severity_prior` must be LOW, MED, or HIGH.
7. `resolution_options` must contain ≥1 actionable resolution path.
8. Output raw YAML only — no prose, no markdown fences.

---

## SECTION E — QUALITY DISCIPLINE

**Minimum bar:** ≥8 contradiction hypotheses proposed. Gemini Pass-2 must confirm ≥5 for B.5 close.

**Rejection criteria for self-audit (reject before including):**
- (a) The "contradiction" is resolvable by reading both signals together — a genuine ambiguity but not a conflict.
- (b) The conflict only exists because of imprecise paraphrase — in the original chart data, both claims can be true simultaneously.
- (c) The signals are in different time periods and do not claim the same window.
- (d) One signal is already marked `[EXTERNAL_COMPUTATION_REQUIRED]` — unresolved computation is not a contradiction.

**Severity calibration:**
- HIGH: The two signals make incompatible predictions that will produce opposite guidance to the native in a real consultation.
- MED: The conflict affects corpus reliability but can be resolved by additional data or clarification without removing either signal.
- LOW: The conflict is a genuine interpretive ambiguity but does not change any prediction materially.

---

## SECTION F — PROMPT REGISTRATION

- **Prompt registered at:** `06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json`
  entry: `prompt_id: claude.contradiction_scan`, `version: 1.0`
- **Supersedes:** null (first version)
- **Reconciler:** `platform/python-sidecar/rag/reconcilers/contradiction_reconciler.py`
- **Two-pass ordering:** Claude Pass-1 (this prompt → internal scan) → Gemini Pass-2 (adjudication prompt)

---

*End of contradiction_scan_v1_0.md — claude.contradiction_scan v1.0 — Produced at Madhav_M2A_Exec_11 (2026-04-27)*
