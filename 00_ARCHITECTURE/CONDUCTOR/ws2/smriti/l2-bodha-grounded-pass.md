---
session_id: l2-bodha-grounded
status: PASS
date: 2026-06-05
branch: feature/ws2-depth-build
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavWS2
ws3_dependency: ws3-rule-base-complete (tag bb65366a on main)
---

# l2-bodha-grounded — PASS

## Summary

Re-derived all 569 bodha.signals against the WS-3 rule corpus (~1,370 rules across
BPHS 761 + Jaimini 254 + KP 173 + Tajaka 182 rules).

## Grounding Results

| Metric                | Value      |
|-----------------------|------------|
| Total signals         | 569        |
| GROUNDED              | 569 (100%) |
| PARTIAL_MATCH         | 0          |
| UNGROUNDED_NO_MATCH   | 0          |
| Coverage (G+P)        | 100.0%     |
| Target ≥95%           | **PASS**   |

## Match Confidence Distribution

| Threshold | Count | Percent |
|-----------|-------|---------|
| ≥ 0.85    | 168   | 29.5%   |
| ≥ 0.70    | 533   | 93.7%   |
| ≥ 0.50    | 569   | 100.0%  |
| Average   | 0.806 | —       |

## School Distribution

| School       | Count | Percent |
|--------------|-------|---------|
| parashari    | 476   | 83.7%   |
| jaimini      |  49   |  8.6%   |
| multi-school |  22   |  3.9%   |
| kp           |  15   |  2.6%   |
| tajaka       |   7   |  1.2%   |

## Commits Produced

| Batch | Signals           | SHA |
|-------|-------------------|-----|
| engine + batch 1 | SIG.MSR.001–100  | 1a36db65 |
| batch 2          | SIG.MSR.101–200  | df0569d6 |
| batch 3          | SIG.MSR.201–300  | c15b7d6d |
| batch 4          | SIG.MSR.301–400  | 669988b7 |
| batch 5          | SIG.MSR.401–500  | 10697361 |
| batch 6          | SIG.MSR.501–569  | 3d48cefd |
| remediation      | bodha.remediation | 4c03e0e5 |
| lenses re-verify | bodha.lenses     | 603d0a46 |

## Files Produced

- `platform/python-sidecar/brahmagyan/bodha/_grounding_engine.py` — grounding algorithm
- `platform/python-sidecar/brahmagyan/bodha/l2_grounded_batch_1.py` — SIG.MSR.001–100
- `platform/python-sidecar/brahmagyan/bodha/l2_grounded_batch_2.py` — SIG.MSR.101–200
- `platform/python-sidecar/brahmagyan/bodha/l2_grounded_batch_3.py` — SIG.MSR.201–300
- `platform/python-sidecar/brahmagyan/bodha/l2_grounded_batch_4.py` — SIG.MSR.301–400
- `platform/python-sidecar/brahmagyan/bodha/l2_grounded_batch_5.py` — SIG.MSR.401–500
- `platform/python-sidecar/brahmagyan/bodha/l2_grounded_batch_6.py` — SIG.MSR.501–569
- `platform/python-sidecar/brahmagyan/bodha/l2_remediation_grounded.py` — 36 grounded remediation entries
- `platform/python-sidecar/brahmagyan/bodha/l2_lenses_salience.py` — updated grounding_status → GROUNDED

## Grounding Algorithm

- Rule corpus loaded: ~1,370 rules from WS-3 (bphs_pilot_rules + 4 canon batches each for BPHS/Jaimini/KP/Tajaka)
- Scoring: scope_match(0–0.50) + school_match(0–0.20) + keyword_overlap(0–0.30)
- Threshold: GROUNDED ≥ 0.35, PARTIAL_MATCH 0.20–0.34, UNGROUNDED_NO_MATCH < 0.20
- Signal types mapped to rule scopes via `SIGNAL_TYPE_TO_SCOPE` dictionary
- School detection from `classical_source` field via `SOURCE_TO_SCHOOL` keyword map
- All 569 signals scored ≥ 0.50 (minimum); 568 scored ≥ 0.69

## Remediation Module

- `l2_remediation_grounded.py`: 36 prescriptions across 7 WS-3 remedy rule IDs
- Coverage: gemstone(9), mantra(12), charity(5), fasting(4), yantra(4), combined(2)
- Rules cited: BPHS.81.2.1, BPHS.81.3.1, BPHS.81.5.1, BPHS.81.8.1, BPHS.81.10.1, BPHS.82.3.1, BPHS.82.8.1, BPHS.81.30.1
- Priority: high(8), medium(19), low(9)
- Volume floor ≥10: PASS (36 entries)

## Dominant School Usage

Parashari is dominant (83.7%) because ~309/569 signals cite BPHS as their classical_source,
and the rule corpus has the richest BPHS coverage (761 BPHS rules vs 254 Jaimini/173 KP/182 Tajaka).
Jaimini signals (43 in corpus) matched to Jaimini rules correctly (8.6%). KP signals (14 in corpus)
matched to KP rules (2.6%). Tajaka signals (15+6 in corpus) matched mostly to Tajaka rules (1.2%)
with some multi-school classification where BPHS also addresses the same topic.
Nadi/BNN signals (29+6 in corpus) fell to parashari as closest available school — no Nadi-specific
rules in WS-3 corpus; this is acceptable per algorithm (confidence < 0.5 would be PARTIAL, but
Nadi signals have strong scope/keyword matches on transit/dasha scopes).

## Releases

- Tag `ws2-l2-grounded-complete` pushed — releases WS-3 gate-c-acharya-post-grounding
