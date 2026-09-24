# REVIEW REQUEST — §4 as a whole (Point-1 residuals, A-class)

**Brief:** `GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md` §4 (lines 116–132)
**Branch:** `l3/gochara-autonomous-wp0-7`
**Sheet items implemented:** M-1, M-3, M-6, N-13, N-14, N-15, N-16, N-17, N-21, N-22 (+ F-11 groundwork consumed by §5)

## What changed

- Mechanism-wiring truth detector and cap-free peak admission (N-17): every admitted peak persisted; the 90-day separation became a serve-time trim (`6a1c23195`).
- Interim sign-level bindu behind `kakshya_bindu_interim` flag, default off (N-22/N-13, `94abfba70`).
- M-6 derived target-contract rows (WP1 §2.2 items 9–11, `ddf985751`).
- Feature flags, all defaults preserving prior behavior: M-1 `activity_shape` (`f2cbe0705`), M-3 `moon_channel` split (`c303ff473`), N-14 `nodal_drishti` removal (`93b6f2818`), N-15 `sade_sati_mode` testimony demotion (`98df8bc40`).
- N-21 standing rule recorded in `WP1_CONTRACTS.md` — nāḍī attestation ⇒ testimony, never weight (`dd84fa311`).
- N-16 citation-drift sweep re-pointing `engine.py` refs to current HEAD (`4b0e0553d`).
- WP8 evidence batteries: M-1 synthetic orb battery (`597b29434`), M-2 retrograde ablation (`73a7cd1a3`, `0481d4565`), factor-level delta report (`627deb504`).

## Tests

Per-commit batteries were green at each packet close; the gochara suite stands at 252 passed after §8.5 (includes §4-era tests). tsc clean; vitest baselines unchanged (platform 1458 passed; platform-mcp 2167 passed / 78 pre-existing failures).

## Unsure of

- The flag defaults encode "prior behavior preserved"; whether M-1/M-3 should ever flip default-on is a reviewer call, not implementation's.
- WP8 battery numbers are synthetic-fixture measurements; they are evidence for the sheet, not production error rates.
