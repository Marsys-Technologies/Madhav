# VC-2 arm generator (value checkpoint)

Generates the three registered arms — A (Saṅgam windows), A′ (+ Taraṅga monthly waveform), B (+ G1 segments, the four
stored term components, weakest link) — for the pre-registered chapter pairs, in one renderer and one table layout,
with blinded P/Q/R judge packets and a sealed order map. It reads one candidate generation from the **lane** database
(`127.0.0.1:55433`, `ky_*`/`kala_ci_*`, read-only transaction), never production. It **never scores or adjudicates**.

- `vc2_core.py` — pure: pins, pair selection, rendering, word budget, blinding, reproducibility digest, readiness gate.
- `vc2_run.py` — lane reader and CLI. `--mode rehearsal` writes anywhere except `value_checkpoint/outputs/`;
  `--mode real` writes only there and only after `check_readiness` returns no reason.
- Tests: `platform/scripts/governance/__tests__/test_vc2_core.py` (pure), `platform/python-sidecar/tests/l3/kala_db/value_checkpoint/` (lane DB).

Inputs the cockpit must supply for a real run (none is invented here): `G1_BASELINE.json` (`ky.g1_baseline/1`),
`VC_BINDING.json` (the seven binding fields of prereg §2), an eligibility declaration (consent reference,
`evaluation_eligible`, LEL coverage reference and span, six calibrated class identities with prior provenance).
