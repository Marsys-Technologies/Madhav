# Smṛti: Gate B PASS — 2026-06-05

session_id: gate-b-acharya
date: 2026-06-05
status: PASS

## What happened
Gate B autonomous AI acharya assessment completed on 200-rule stratified sample across
BPHS (75), Jaimini (50), KP (40), Tajaka (35). All three verdict thresholds passed with
meaningful margin: mean_composite 0.829 (threshold 0.75), pct_above_0_7 91.5% (threshold
80%), lens_b_pct 93.5% (threshold 85%).

## Key findings retained in smṛti

1. **The corpus is acharya-grade.** Rule extraction correctly distinguishes universally-accepted
   doctrine (high confidence, DIRECT traceability) from contested/commentarial content (low
   confidence, REQUIRES_CONTEXT). No fabricated verse references detected. Schema compliance
   near-universal.

2. **Framework isolation is maintained.** KP rules are KP-native (Placidus, sub-lord hierarchy,
   retrograde correction). Tajaka rules are Tajaka-native (Varshaphal context only, Hayyiz,
   Itthasala moiety orbs). Jaimini rules honour the implicit-sutra form. BPHS rules draw on
   Santhanam translation with cross-text corroboration from Saravali/Brihat Jataka/Phaladeepika.

3. **7 concordance flags (C1–C7) issued for concordance-build session.** These are not quality
   failures; they are principled divergences the concordance must surface and maintain as
   tagged, per-school entries rather than resolving into a single interpretation.
   C1: karaka frameworks (parallel, not competing)
   C2: aspect systems (orthogonal)
   C3: house cusp convention (system-defining)
   C4: strength systems (non-comparable)
   C5: timing systems (non-comparable)
   C6: Rahu/Ketu per-system treatment (explicit per-system entries required)
   C7: retrograde treatment (BPHS vs KP: explicitly contradictory mechanisms)

4. **Jaimini contested-sutra floor applied.** 11 contested Jaimini rules assessed at
   PARTIALLY_ACCURATE(0.7) rather than INACCURATE(0.0) per the floor adjustment. This
   is correct per the gate mechanics for Jaimini sutras where commentarial tradition
   legitimately diverges.

5. **Non-blocking pattern NB-1:** ~8% of BPHS graha-nature rules show assertion-expansion
   beyond verse text (classically correct but INFERABLE). This is within acceptable
   parameters and is compensated by confidence depression (0.80–0.88).

## Next session
concordance-build: build brahmagyan.concordance using C1–C7 flags as the primary
structuring principles. The concordance must NOT flatten divergences into single answers.
It must surface: agree / qualify / conflict / orthogonal per school per topic per rule pair.

## Artifacts written
- 00_ARCHITECTURE/CONDUCTOR/ws3/acharya_eval_gate_B/sample.md (200-rule assessment)
- 00_ARCHITECTURE/CONDUCTOR/ws3/acharya_eval_gate_B/verdict.md (formal verdict)
- 00_ARCHITECTURE/CONDUCTOR/ws3/session_queue.yaml (gate-b-acharya status: passed)
- 00_ARCHITECTURE/CONDUCTOR/ws3/smriti/gate-b-pass.md (this file)
