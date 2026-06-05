---
smriti_id: gate-a-pass
session_id: gate-a-acharya
date: 2026-06-05
event: Gate A autonomous AI assessment PASSED
---

# Gate A — PASS

## What happened
Gate A autonomous AI assessment of the bphs-pilot rule extraction completed.
50 rules sampled stratified across 5 batches (10 per batch × confidence tiers).
Three-lens panel assessment: Verse Traceability (A), Classical Accuracy (B), Schema Completeness (C).

## Verdict
PASS

## Key numbers
- Mean composite (all 50 rules incl. stubs): 0.849
- Mean composite (40 non-stub rules): 0.961
- Lens A (verse-trace) direct/inferable: 100%
- Lens B (accuracy) accurate/partial: 95%
- Lens C (schema) complete/minor-gaps: 100%
- Rules above 0.7 composite: 100% (non-stubs), 80% (all incl. stubs)

## Findings summary
- Zero NOT_DERIVABLE or INACCURATE findings in 40 non-stub rules
- STUBs (10 sampled) all correctly encoded per method §5
- 3 optional (non-blocking) improvement recommendations:
  R1: Formalise Rahu/Ketu nakshatra confidence adjustment in method Factor A table
  R2: Canon-extraction should specifically probe contested chapters (Ch. 28, 52, 77)
  R3: Method §3 should add framing guidance for lagna-conditional dasha assertions

## Artifacts
- Sample: 00_ARCHITECTURE/CONDUCTOR/ws3/acharya_eval_gate_A/sample.md
- Verdict: 00_ARCHITECTURE/CONDUCTOR/ws3/acharya_eval_gate_A/verdict.md

## Next session
canon-extraction (depends on this gate PASS)
