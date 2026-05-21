---
artifact: CLAUDECODE_BRIEF_M2A_Exec_10_SEEDS_APPENDIX.md
version: 1.0
status: AUTHORED
status_set_authored_on: 2026-04-27
parent_brief: CLAUDECODE_BRIEF.md (Madhav_M2A_Exec_10, status: AUTHORED 2026-04-27)
authored_by: Cowork (Claude Opus 4.7) on 2026-04-27
authored_during: Cowork conversation "Madhav M2A-Exec-10 — B.5 Session 2 (Pattern Expansion + Resonance Mapping)" — post-close addendum
governing_clause: This appendix supplies the seed sets that brief AC.6 (pattern batches 4–6) + AC.11 (resonance batches 1–3) require the executor to curate. Native curated them up-front; seeds are now ready for Gemini 2.5 Pro Pass-1 runs.
target_executor: Same as parent brief — Claude Code Extension (Google Anti-Gravity IDE), Sonnet 4.6
expected_session_class: Read-only input to M2 corpus execution session Madhav_M2A_Exec_10
pass_1_actor_lock: gemini  # PER Q1 — these seeds go to Gemini 2.5 Pro web UI for Pass-1 proposal generation; NEVER to a Claude session for Pass-1 self-validation
relationship_to_parent_brief: >
  Brief AC.6 says "the executor curates seeds for batches 4-6 from under-covered domains" and AC.11 says "the executor curates 4 candidate triplets per resonance batch." Native curated all 6 seed sets up-front during the Cowork brief-authoring conversation (2026-04-27, post brief-close). This appendix is the curated output. Exec_10 reads this file at AC.6 + AC.11 instead of curating from scratch — saves the executor seed-authoring effort and locks the seed semantics in writing for audit.
how_to_use: >
  Pattern batches: paste each seed set into Section D of `035_DISCOVERY_LAYER/PROMPTS/gemini/pattern_mining_v1_0.md` (one batch at a time), copy the full prompt body into Gemini 2.5 Pro web UI, save Gemini's YAML response to `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/2026-04-27_B5_pattern_mining_batch<N>_raw.md`, then run `python -m rag.reconcilers.run_pattern_pipeline --batches B5_pattern_mining_batch<N>` from `platform/python-sidecar/`. Resonance batches: same pattern with `resonance_walk_v1_0.md` + `2026-04-27_B5_resonance_walk_batch<N>_raw.md` + `run_resonance_pipeline`.
hard_halt_reminder: >
  Per Q2: first `[ACCEPTANCE_RATE_ANOMALY]` (rate <0.15 or >0.80) opens DIS.class.acceptance_rate_anomaly + halts the pipeline. Do NOT run subsequent batches until native restart logged in close-YAML halts_encountered[]. Run batches one at a time + verify acceptance_rate row before proceeding to the next.
---

# CLAUDECODE_BRIEF_M2A_Exec_10 — SEEDS APPENDIX

## §1 — Purpose

Native-curated seed sets for the 6 batches Exec_10 must run per parent brief AC.6 (pattern top-off batches 4–6) + AC.11 (resonance walk batches 1–3). Each seed is a triplet: `(domain | domain_pair, signal_cluster, cdlm_anchor)` with rationale.

This appendix exists because native completed seed curation up-front during the Cowork brief-authoring conversation (after the brief itself was authored + the Cowork session closed). It saves the Exec_10 executor the AC.6 + AC.11 seed-authoring step. The semantic content of the seeds is locked in writing here for audit; Exec_10 reads this file instead of synthesizing fresh seeds.

**Relationship to brief AC.6 + AC.11:** these seeds satisfy the AC requirements for "≥4 candidates per batch from a target domain" and the under-covered-domain coverage spec. AC.6 + AC.11 acceptance criteria still apply unchanged; only the seed-curation sub-step is pre-completed.

**Pass-1 actor lock (Q1) HOLDS for these batches.** These seeds go to Gemini 2.5 Pro web UI for Pass-1 proposal generation. Claude Pass-2 reconciler runs against Gemini's raw response. Per-batch `pass_1_actor: "gemini"` in PATTERN_REGISTER + RESONANCE_REGISTER metadata at AC.20 close-checklist verification.

---

## §2 — Pattern batches 4, 5, 6 (per brief AC.6 + AC.7)

### Batch 4 — Wealth × Health × Relationships (blank/thin CDLM cells)

```yaml
batch_id: B5_pattern_mining_batch4
date_to_run: 2026-04-27
seeds:
  - seed_label: "Seed_1"
    domain: "wealth"
    signal_cluster: ["SIG.MSR.397", "SIG.MSR.040", "SIG.MSR.015"]
    cdlm_anchor: "CDLM.career.wealth"
    seed_rationale: >
      AL=10H Capricorn (SIG.MSR.397) + Saturn AmK = wealth as dharmic output of
      career structure. Saturn-Pisces triple activation (SIG.MSR.040) adds a
      2025-2028 time-indexed pressure window. Hidden Raja Yoga (SIG.MSR.015)
      modulates valence. Patterns: how Saturn's exaltation + AL placement govern
      wealth accumulation mechanics; what the Sade Sati window does to wealth flow.
  - seed_label: "Seed_2"
    domain: "health"
    signal_cluster: ["SIG.MSR.040", "SIG.MSR.228", "SIG.MSR.396"]
    cdlm_anchor: "CDLM.career.health"
    seed_rationale: >
      Gulika in Gemini 3H (SIG.MSR.228) aspects health matters via 3H courage/
      vitality. Saturn-Pisces triple activation (SIG.MSR.040) = 12H Pisces =
      hidden expenditure of vitality. Sade Sati paradox (SIG.MSR.396): peak
      achievement under adversity implies health stress during peak windows.
      Patterns: Gulika's calamity-significator function on vitality; 12H transit
      and recuperation cycles.
  - seed_label: "Seed_3"
    domain: "relationships"
    signal_cluster: ["SIG.MSR.015", "SIG.MSR.042", "SIG.MSR.041"]
    cdlm_anchor: "CDLM.career.relationships"
    seed_rationale: >
      Mars+Saturn 7H conjunction (SIG.MSR.015) = spouse/partnership house with
      AK+PK tension. D60 Saturn at Lagna (SIG.MSR.042) = past-karma weight on
      relationship initiation. D27 Lagna=12H (SIG.MSR.041) = strength-chart
      in moksha house may suppress partnership visibility. Patterns: how karaka
      overload in 7H shapes relationship formation and sustained partnership.
  - seed_label: "Seed_4"
    domain: "wealth"
    signal_cluster: ["SIG.MSR.413", "SIG.MSR.397"]
    cdlm_anchor: "CDLM.career.wealth"
    seed_rationale: >
      Mercury Eight-System Convergence (SIG.MSR.413) = primary operational
      planet driving 2010-2027 MD. Mercury in 10H Capricorn governs commerce,
      accounting, analytical work. AL=10H ties arudha visibility to career output.
      Pattern: Mercury MD as the engine that converts career excellence into
      visible wealth accumulation during 2010-2027.
```

### Batch 5 — Parents × Children × Travel (blank CDLM cells)

```yaml
batch_id: B5_pattern_mining_batch5
date_to_run: 2026-04-27
seeds:
  - seed_label: "Seed_1"
    domain: "parents"
    signal_cluster: ["SIG.MSR.042", "SIG.MSR.015", "SIG.MSR.040"]
    cdlm_anchor: "CDLM.career.parents"
    seed_rationale: >
      D60 Saturn at Lagna (SIG.MSR.042) encodes past-karma weight from parental
      lineage. Saturn as AK governs ancestral soul-debt. Saturn's exaltation in
      7H Libra (SIG.MSR.015) = relationship with authority (father = Sun +
      Saturn overlay via AK). Saturn-Pisces triple activation (SIG.MSR.040)
      falls in 12H = foreign/isolation = possible parental separation/distance.
      Patterns: Saturn AK as parental-lineage karma transmitter; Pisces-12H
      activation and geographical separation from parents.
  - seed_label: "Seed_2"
    domain: "children"
    signal_cluster: ["SIG.MSR.015", "SIG.MSR.042"]
    cdlm_anchor: "CDLM.career.children"
    seed_rationale: >
      Mars as PK (Putrakaraka) + Avayogi = children signifier is simultaneously
      a fortune-reducer (SIG.MSR.015). Mars in 7H Libra (debilitated sign for
      Mars) + exalted Saturn = karaka tension. D60 Saturn at Lagna (SIG.MSR.042)
      = past-karma weight affecting progeny. Patterns: Avayogi PK = structural
      delay or complication in children domain; how Saturn-Mars 7H conjunction
      shapes children timing.
  - seed_label: "Seed_3"
    domain: "travel"
    signal_cluster: ["SIG.MSR.040", "SIG.MSR.041", "SIG.MSR.396"]
    cdlm_anchor: "CDLM.career.health"
    seed_rationale: >
      Saturn-Pisces triple activation (SIG.MSR.040) = 12H Pisces = foreign lands,
      long-distance travel, isolation. D27 Lagna=12H Pisces (SIG.MSR.041) =
      strength-chart anchors in the travel/foreign house. Sade Sati paradox
      (SIG.MSR.396) = peak-achievement during adversity window maps to career
      travel under pressure. Patterns: 12H Pisces as the gateway for foreign/
      travel activation; D27 strength-in-12H as travel excellence potential.
  - seed_label: "Seed_4"
    domain: "mind"
    signal_cluster: ["SIG.MSR.413", "SIG.MSR.228", "SIG.MSR.042"]
    cdlm_anchor: "CDLM.career.mind"
    seed_rationale: >
      Mercury 10H Eight-System Convergence (SIG.MSR.413) = mind is the primary
      operational instrument. Gulika in Gemini 3H (SIG.MSR.228) = calamity-
      significator in the house of intellect/communication courage. D60 Saturn at
      Lagna (SIG.MSR.042) = past-karma discipline structuring mental patterns.
      Patterns: Mercury as mind-ruler in dharma house; Gulika's shadow on
      communication courage; past-karma discipline shaping cognitive style.
```

### Batch 6 — Spiritual × Mind × Meta cross-cuts

```yaml
batch_id: B5_pattern_mining_batch6
date_to_run: 2026-04-27
seeds:
  - seed_label: "Seed_1"
    domain: "spiritual"
    signal_cluster: ["SIG.MSR.042", "SIG.MSR.041", "SIG.MSR.040"]
    cdlm_anchor: "CDLM.career.spiritual"
    seed_rationale: >
      D60 Saturn at Lagna (SIG.MSR.042) = soul's past-karma primary thread is
      Saturn-discipline = Shani as moksha-karaka. D27 Lagna=12H Pisces
      (SIG.MSR.041) = strength-chart in moksha house = spiritual capacity is
      the native's deepest structural strength. Saturn-Pisces triple activation
      (SIG.MSR.040) = Pisces=12H=moksha house under triple pressure 2025-2028.
      Patterns: D60+D27 convergence on moksha/spiritual axis; Pisces activation
      as the catalytic window for spiritual crystallization.
  - seed_label: "Seed_2"
    domain: "mind"
    signal_cluster: ["SIG.MSR.396", "SIG.MSR.413", "SIG.MSR.040"]
    cdlm_anchor: "CDLM.career.mind"
    seed_rationale: >
      Sade Sati paradox (SIG.MSR.396) = peak achievement under Saturn adversity
      implies mind must function under sustained pressure. Mercury Eight-System
      (SIG.MSR.413) = mind's operating system is Mercury-driven precision.
      Saturn-Pisces triple activation (SIG.MSR.040) = 12H Pisces transit =
      mental introspection pressure. Patterns: mental resilience architecture
      under Sade Sati; Mercury precision under Saturn's constraint producing
      paradoxical output quality peaks.
  - seed_label: "Seed_3"
    domain: "spiritual"
    signal_cluster: ["SIG.MSR.015", "SIG.MSR.396", "SIG.MSR.042"]
    cdlm_anchor: "CDLM.career.spiritual"
    seed_rationale: >
      Hidden Raja Yoga Saturn+Mars 7H (SIG.MSR.015) with AK = every public-
      domain act carries soul-weight (AK = Saturn). Sade Sati paradox
      (SIG.MSR.396) = adversity window as the structural context for spiritual
      austerity. D60 Saturn at Lagna (SIG.MSR.042) = entire life framed by
      past-karma debt repayment. Patterns: Raja Yoga as karmic instrument
      rather than material reward; Sade Sati adversity as the initiation window
      for AK Saturn's spiritual mandate.
```

### How to run pattern batches 4, 5, 6

1. Open `035_DISCOVERY_LAYER/PROMPTS/gemini/pattern_mining_v1_0.md`.
2. In Section D, replace the placeholder with the seed set for **one** batch.
3. Copy the full prompt body into Gemini 2.5 Pro (web UI).
4. Save Gemini's YAML response as:
   - `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/2026-04-27_B5_pattern_mining_batch4_raw.md`
   - `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/2026-04-27_B5_pattern_mining_batch5_raw.md`
   - `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/2026-04-27_B5_pattern_mining_batch6_raw.md`
5. Run **one batch at a time** so the Q2 hard-halt can fire correctly between batches:
   ```bash
   cd platform/python-sidecar
   venv/bin/python -m rag.reconcilers.run_pattern_pipeline --batches B5_pattern_mining_batch4
   # verify acceptance_rate row in batch_acceptance_rates.json BEFORE running batch5
   venv/bin/python -m rag.reconcilers.run_pattern_pipeline --batches B5_pattern_mining_batch5
   # verify, then:
   venv/bin/python -m rag.reconcilers.run_pattern_pipeline --batches B5_pattern_mining_batch6
   ```
6. **If `[ACCEPTANCE_RATE_ANOMALY]` fires on any batch** (rate <0.15 or >0.80) → `run_pattern_pipeline.py` opens `DIS.class.acceptance_rate_anomaly` + halts. Subsequent batches do NOT run until native restart logged in close-YAML `halts_encountered[]`. Per brief AC.2.

---

## §3 — Resonance batches 1, 2, 3 (per brief AC.11)

### Batch 1 — Saturn AK/AmK dual-karaka resonances

```yaml
batch_id: B5_resonance_walk_batch1
seeds:
  - seed_label: "Seed_1"
    domain_pair: ["career", "spiritual"]
    signal_cluster: ["SIG.MSR.015", "SIG.MSR.042"]
    cdlm_anchor: "CDLM.career.spiritual"
    seed_rationale: >
      Saturn as AK+AmK creates a single planetary engine governing both career
      dharma and soul dharma simultaneously. Every professional act is a karmic
      act; every spiritual renunciation has career consequence. The D60 Saturn-
      at-Lagna deepens the past-karma weight on both axes.
  - seed_label: "Seed_2"
    domain_pair: ["wealth", "spiritual"]
    signal_cluster: ["SIG.MSR.397", "SIG.MSR.042", "SIG.MSR.041"]
    cdlm_anchor: "CDLM.spiritual.wealth"
    seed_rationale: >
      AL=10H Capricorn (SIG.MSR.397) + Saturn AmK = wealth as dharmic output.
      D27 Lagna=12H Pisces (SIG.MSR.041) = strength in moksha house. The
      resonance: wealth and spiritual capacity share the same Saturn-governed
      engine — accumulation and renunciation are structurally entangled.
  - seed_label: "Seed_3"
    domain_pair: ["career", "relationships"]
    signal_cluster: ["SIG.MSR.015", "SIG.MSR.040"]
    cdlm_anchor: "CDLM.career.relationships"
    seed_rationale: >
      Mars+Saturn conjunction in 7H Libra (SIG.MSR.015) = career karaka (AmK
      Saturn) sits in the spouse/partnership house. Career structure and
      relationship structure share the same house + planetary engine. Saturn-
      Pisces triple activation (SIG.MSR.040) will pressure both simultaneously.
```

### Batch 2 — Mercury MD + blank CDLM cells

```yaml
batch_id: B5_resonance_walk_batch2
seeds:
  - seed_label: "Seed_1"
    domain_pair: ["career", "mind"]
    signal_cluster: ["SIG.MSR.413", "SIG.MSR.397"]
    cdlm_anchor: "CDLM.career.mind"
    seed_rationale: >
      Mercury Eight-System Convergence (SIG.MSR.413) = mind IS the career
      instrument — no separation between cognitive style and professional
      output. AL=10H Capricorn under Mercury MD. The resonance: mind and career
      are not two domains but one Saturn-Mercury compound during 2010-2027.
  - seed_label: "Seed_2"
    domain_pair: ["spiritual", "health"]
    signal_cluster: ["SIG.MSR.040", "SIG.MSR.041"]
    cdlm_anchor: "CDLM.spiritual.health"
    seed_rationale: >
      Saturn-Pisces triple activation (SIG.MSR.040) = 12H Pisces = isolation,
      hospitalization, retreat. D27 Lagna=12H (SIG.MSR.041) = strength-chart
      in moksha house. The resonance: spiritual retreat capacity and health
      recuperation capacity share the same 12H Pisces engine — illness windows
      and spiritual retreats are structurally co-activated.
  - seed_label: "Seed_3"
    domain_pair: ["wealth", "health"]
    signal_cluster: ["SIG.MSR.040", "SIG.MSR.396", "SIG.MSR.397"]
    cdlm_anchor: "CDLM.wealth.health"
    seed_rationale: >
      Sade Sati paradox (SIG.MSR.396) = peak career/wealth achievement during
      adversity window, implying health stress coincides with peak wealth.
      AL=10H wealth-dharmic output (SIG.MSR.397) + Saturn-Pisces 12H health-
      expenditure pressure (SIG.MSR.040). Resonance: wealth accumulation and
      health expenditure are inversely co-activated by Saturn's 2025-2028 window.
```

### Batch 3 — Parents × Children × Travel cross-cuts

```yaml
batch_id: B5_resonance_walk_batch3
seeds:
  - seed_label: "Seed_1"
    domain_pair: ["spiritual", "mind"]
    signal_cluster: ["SIG.MSR.042", "SIG.MSR.041", "SIG.MSR.413"]
    cdlm_anchor: "CDLM.spiritual.mind"
    seed_rationale: >
      D60 Saturn at Lagna = past-karma shapes cognitive architecture. D27
      Lagna=12H = strength in moksha = spiritual insight is the mind's deepest
      capacity. Mercury Eight-System Convergence = mind as operational planet.
      Resonance: the mind's analytical precision (Mercury MD) and its spiritual
      depth (D27 moksha) are the same instrument expressed at different frequencies.
  - seed_label: "Seed_2"
    domain_pair: ["relationships", "children"]
    signal_cluster: ["SIG.MSR.015", "SIG.MSR.042"]
    cdlm_anchor: "CDLM.relationships.children"
    seed_rationale: >
      Mars as PK (children) + Saturn as 7H partner-house occupant (SIG.MSR.015)
      = the same planetary conjunction governs both partnership formation and
      progeny. D60 Saturn (SIG.MSR.042) weights both with past-karma. Resonance:
      partnership readiness and parenthood readiness are structurally gated by
      the same 7H Mars-Saturn engine — they move together, not independently.
  - seed_label: "Seed_3"
    domain_pair: ["travel", "spiritual"]
    signal_cluster: ["SIG.MSR.040", "SIG.MSR.041"]
    cdlm_anchor: "CDLM.spiritual.travel"
    seed_rationale: >
      D27 Lagna=12H Pisces = strength in the house of foreign lands + moksha.
      Saturn-Pisces triple activation (SIG.MSR.040) = 12H lit up 2025-2028.
      Resonance: travel (particularly foreign/retreat travel) and spiritual
      activation share the 12H Pisces engine — pilgrimage-like travel is the
      structural form spiritual activation takes in this chart.
```

### How to run resonance batches 1, 2, 3

1. Open `035_DISCOVERY_LAYER/PROMPTS/gemini/resonance_walk_v1_0.md` (verified to exist on disk; `prompt_id: gemini.resonance_walk` v1.0).
2. In Section D, replace the placeholder with the seed set for **one** batch.
3. Copy the full prompt body into Gemini 2.5 Pro (web UI).
4. Save Gemini's YAML response as:
   - `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/2026-04-27_B5_resonance_walk_batch1_raw.md`
   - `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/2026-04-27_B5_resonance_walk_batch2_raw.md`
   - `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/2026-04-27_B5_resonance_walk_batch3_raw.md`
5. Run **one batch at a time** so the Q2 hard-halt can fire correctly between batches:
   ```bash
   cd platform/python-sidecar
   venv/bin/python -m rag.reconcilers.run_resonance_pipeline --batches B5_resonance_walk_batch1
   # verify acceptance_rate row in batch_acceptance_rates.json BEFORE running batch2
   venv/bin/python -m rag.reconcilers.run_resonance_pipeline --batches B5_resonance_walk_batch2
   # verify, then:
   venv/bin/python -m rag.reconcilers.run_resonance_pipeline --batches B5_resonance_walk_batch3
   ```
6. Hard-halt enforcement same as pattern batches per brief AC.2 + AC.10.

---

## §4 — Coverage map (for audit)

**Pattern batches 4–6 — domain coverage:**

| Batch | Seeds | Primary domains targeted |
|---|---|---|
| Batch 4 | 4 seeds | wealth ×2, health ×1, relationships ×1 |
| Batch 5 | 4 seeds | parents ×1, children ×1, travel ×1, mind ×1 |
| Batch 6 | 3 seeds | spiritual ×2, mind ×1 |

Combined Exec_10 pattern coverage **after these batches accept** (assuming reasonable acceptance rate): adds wealth, health, relationships, parents, children, travel, mind+ to the Exec_9 coverage of career×3, cross_domain×3, spiritual×3, children×1, mind×1. Aggregate of 11 (Exec_9) + ~9–11 (Exec_10) = ~20–22 patterns spanning all canonical domains except meta. Meets brief AC.7 target ≥20 + brief §5 priority 3 instruction "Curate seeds for pattern batches 4, 5, 6 from under-covered domains."

**Resonance batches 1–3 — bridge coverage:**

| Batch | Bridges proposed |
|---|---|
| Batch 1 | career×spiritual, wealth×spiritual, career×relationships |
| Batch 2 | career×mind, spiritual×health, wealth×health |
| Batch 3 | spiritual×mind, relationships×children, travel×spiritual |

9 distinct cross-domain bridges proposed. Meets brief AC.11 target ≥10 resonances if Gemini/Claude two-pass yields ≥1 resonance per seed (rough expectation — some may yield 2).

**CDLM cell coverage:** the seeds cite `CDLM.career.{wealth,health,relationships,parents,children,mind,spiritual}` + `CDLM.spiritual.{wealth,health,mind,travel}` + `CDLM.wealth.health` + `CDLM.relationships.children` — most are blank or thin in the explicit CDLM_v1_1 9×9 grid, satisfying the §B.5 line 670 design intent "propose cross-domain resonances beyond CDLM explicit cells."

---

## §5 — Audit trail

This appendix is a sibling artifact to the parent `CLAUDECODE_BRIEF.md` (Madhav_M2A_Exec_10). It does not require its own status flip at Exec_10 close (the parent brief flipping to COMPLETE covers it). FILE_REGISTRY bump at Exec_10 close (per brief AC.23, v1.10 → v1.11) should add a row for this file alongside the other Exec_10 deliverables.

Authored at the Cowork conversation `Madhav M2A-Exec-10 — B.5 Session 2 (Pattern Expansion + Resonance Mapping)` after the Cowork session was officially closed (atomic SESSION_LOG entry `Madhav_COW_M2A_Exec_10_BRIEF_AUTHORING` already appended, 2026-04-27 15:00 UTC). This sibling artifact is a follow-on within the same Cowork conversation; it does not require a second SESSION_LOG entry per the post-close addendum precedent.

---

*End of CLAUDECODE_BRIEF_M2A_Exec_10_SEEDS_APPENDIX.md. Authored by Cowork (Claude Opus 4.7) 2026-04-27.*
