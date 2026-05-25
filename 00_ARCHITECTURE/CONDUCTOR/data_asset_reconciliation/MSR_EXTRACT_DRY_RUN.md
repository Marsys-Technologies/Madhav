---
source_file: 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
signals_extracted: 573
gate_check: PASS
notes: All 573 signals extracted clean — SIG.MSR.001 through SIG.MSR.573 sequential with no gaps or None IDs. 74 signals carry category "unknown" (missing signal_type in YAML front-matter); non-blocking. Method used — Python import (Option B): extract_msr_signals(repo_root).
---

# MSR v5.0 Extract Dry-Run Report
Generated: 2026-05-25T01:38:09Z

## Summary

| Field | Value |
|---|---|
| Source | `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` |
| Source version | 5.0 |
| Expected count | 573 |
| Extracted count | 573 |
| Gate check | **PASS** |
| First signal | SIG.MSR.001 |
| Last signal | SIG.MSR.573 |
| Signals with None ID | 0 |

## Extraction Method

Option B — direct Python import:

```python
from pipeline.extractors.msr_extractor import extract_msr_signals
signals = extract_msr_signals('/Users/Dev/Vibe-Coding/Apps/MadhavDataAsset')
# → 573 signal dicts
```

Run from: `platform/python-sidecar/`

## Category Distribution (40 categories)

| Category | Count |
|---|---|
| aspect | 13 |
| conjunction-career | 1 |
| conjunction-environmental | 1 |
| conjunction-pattern | 1 |
| conjunction-placement | 2 |
| conjunction-psychological | 1 |
| contradiction | 10 |
| convergence | 56 |
| dasha-activation | 18 |
| dignity | 52 |
| divisional-pattern | 59 |
| exchange-combination | 1 |
| house-from-planet | 5 |
| house-strength | 2 |
| jaimini-pattern | 39 |
| kp-signature | 6 |
| multi-placement-spiritual | 1 |
| multi-planet-combination | 4 |
| nakshatra-signature | 33 |
| panchang | 18 |
| placement-career | 1 |
| placement-longevity | 1 |
| placement-psychological | 1 |
| placement-spirituality | 1 |
| placement-timing | 1 |
| planetary-aspect | 1 |
| planetary-proximity | 1 |
| sensitive-point | 29 |
| sequential-transit | 2 |
| structural | 1 |
| tajika-foundation | 5 |
| tajika-pattern | 13 |
| tajika-sahama | 4 |
| tajika-yoga | 6 |
| transit-activation | 29 |
| transit-timing | 1 |
| transit-trigger | 1 |
| **unknown** | **74** |
| yoga | 64 |
| yogini-period | 14 |
| **TOTAL** | **573** |

## Anomalies / Warnings

1. **74 signals with `category: unknown`** — these signals have a missing or unrecognised `signal_type` in their YAML front-matter. The extractor falls back to `"unknown"` per `data.get("signal_type", "unknown")`. Non-blocking for the dry-run gate; a separate grounding/repair pass (V1_3_AUDIT_QUEUE item 1) should resolve these.
2. No other anomalies. All signal IDs are sequential SIG.MSR.001–SIG.MSR.573 with no gaps, duplicates, or None values.

## Interface Notes

`msr_extractor.py` does NOT expose a `--dry-run` argparse flag. It exports a single public function:

```python
def extract_msr_signals(repo_root: str) -> list[dict[str, Any]]:
    ...
```

The function raises `ValueError` if the parsed count deviates from 573. The dry-run succeeded without exception, confirming the parser and source file are in sync.
