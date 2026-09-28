---
artifact: JATAKA_PHASE_A3_L0_FROZEN_PINS_DRIFT_FINDING
canonical_id: JATAKA_PHASE_A3_L0_FROZEN_PINS_DRIFT_FINDING
version: 1.0
status: OPEN — reported, not fixed
created: 2026-09-27
lane: JATAKA-PHASE-A3-SOURCE-INTEGRITY (Nirmāṇa L5 re-pin, item 4)
scope: read-only finding; no fix applied; no file this finding concerns was modified
---

# L0_FROZEN_PINS drift — a pre-existing bug in the shared Nirmāṇa pin generator

## Summary

`platform/scripts/generate/nirmana_analysis_layer_pins.py`'s module-level `L0_FROZEN_PINS`
constant is stale by two generations. It still holds L0's **first-ever** pin values
(`convergence_commit: 49bb5c98b864...`, `writer_inventory_sha256: 5125cccb68715e...`), even
though L0 has since been correctly, legitimately re-pinned twice via the script's own
`--admit-successor` path — most recently by the `NATIVE-2026-09-24-L0-REPAIR-REPIN` successor
admission (PR #2727). The **committed `nirmana-analysis-layer-pins.json` is correct** — its live
`layers.L0.pin.writer_inventory_sha256` already reads `64b8859fe6925c178719f6da8b130de73cd29ffe03dcf4bdc19bd0981a0ffff1`
(generation_id `l0:7d40f8c70640:64b8859fe692`), matching current source exactly, with the
`5125cccb...` value correctly preserved as a superseded historical generation in `history.L0[0]`.

Only the separate `L0_FROZEN_PINS` constant — used exclusively by the `build_pins()` code path
(the one invoked by **any** non-`--admit-successor` regeneration, including a single-layer
`--layer <X>` splice for a completely different layer) — was never advanced to match. The result:
`build_pins()` always false-positives an "L0 drift" and hard-stops, refusing to regenerate **any**
layer's pin, not just L0's, until this constant is fixed.

## Evidence

1. `L0_FROZEN_PINS` in the current script (matches `origin/main`, no divergence on this branch):
   ```python
   L0_FROZEN_PINS = {
       "convergence_commit": "49bb5c98b864a2cb2fee037cdb7f14f6892a8263",
       "writer_inventory_sha256": "5125cccb68715ebc6054c3ce47bc4c047684445249503a4c4dabd85e0d036178",
       "receipt_count": 40,
   }
   ```
2. The committed `platform/src/generated/nirmana-analysis-layer-pins.json`'s live `layers.L0.pin`:
   ```json
   {
     "asset_prefix": "bg_",
     "convergence_commit": "7d40f8c706406ee8187eadb5c3930553800a1a4a",
     "generation_id": "l0:7d40f8c70640:64b8859fe692",
     "writer_inventory_sha256": "64b8859fe6925c178719f6da8b130de73cd29ffe03dcf4bdc19bd0981a0ffff1",
     "receipt_count": 40,
     "supersedes_generation_id": "l0:d2369b888e76:3dda261170ee",
     "admission": {
       "authority_decision": "NATIVE-2026-09-24-L0-REPAIR-REPIN",
       "source_commit": "7d40f8c706406ee8187eadb5c3930553800a1a4a"
     }
   }
   ```
   The `5125cccb...` value lives correctly in `history.L0[0]` (`generation_id
   l0:49bb5c98b864:5125cccb6871`), already superseded twice over
   (`l0:d2369b888e76:3dda261170ee` → the current `l0:7d40f8c70640:64b8859fe692`).
3. Independently re-derived `64b8859f...` two ways, confirming the live value is correct and
   self-consistent (not something this session computed differently by accident):
   - `layer_inventory_sha256()` applied to the bg_* slice of `nirmana-writer-digests.json` as
     committed at `b6690928f` (the merged L0-repair commit) → `64b8859f...`.
   - The same computation applied to `7d40f8c706406ee8187eadb5c3930553800a1a4a` (the exact source
     commit `AUTHORIZED_SOURCE_COMMITS["NATIVE-2026-09-24-L0-REPAIR-REPIN"]["L0"]` cites as
     authorized) → `64b8859f...`, identical.
   - Both disagree with `L0_FROZEN_PINS`'s `5125cccb...` in the same way, confirming the constant
     — not the JSON, not this session's source — is the stale element.

## Why this blocked Jātaka Phase-A3 item 4

Phase-A3 needed a narrow Nirmāṇa L5 successor re-pin (source-provenance only, reflecting this
session's `mi_bhara/db.py` context-staleness filter change) via
`nirmana_analysis_layer_pins.py --layer L5 --convergence-commit <reviewed head> --definition-snapshot-commit <existing valid snapshot>`.
That invocation calls `build_pins()` internally (even though only L5's derived record is ultimately
spliced back in), and `build_pins()` unconditionally validates every layer's live-computed hash
against its frozen/pinned expectation before doing anything else — so it stopped on L0 before ever
reaching L5.

## Scope note

This is a pre-existing defect on `origin/main`, dated to on or before PR #2727 (well before this
branch's merge-base with main, `d1bd8916a`). It is unrelated to any Jātaka Phase-A3 (or Phase-A2)
change. No file this finding concerns — `scripts/generate/nirmana_analysis_layer_pins.py` or
`src/generated/nirmana-analysis-layer-pins.json` — was modified while investigating or reporting
this; investigation was read-only (git blob inspection, hash re-derivation) against a
`nirmana_campaign_control_writer` connection opened with `set_session(readonly=True)`.

## Suggested fix (not applied — outside this lease's scope)

Update `L0_FROZEN_PINS` in `nirmana_analysis_layer_pins.py` to the current live values already
recorded in `nirmana-analysis-layer-pins.json`'s `layers.L0.pin`:
```python
L0_FROZEN_PINS = {
    "convergence_commit": "7d40f8c706406ee8187eadb5c3930553800a1a4a",
    "writer_inventory_sha256": "64b8859fe6925c178719f6da8b130de73cd29ffe03dcf4bdc19bd0981a0ffff1",
    "receipt_count": 40,
}
```
This is an L0/shared-generator-tooling change, outside Jātaka Phase-A3's narrow three-surface
authority (`brahma_mimamsa_prediction_ledger`, `brahma_prospective_ledger`,
`mimamsa_calibration_snapshot`) — it belongs to whoever currently owns L0/Nirmāṇa-generator
governance, not to this lease.
