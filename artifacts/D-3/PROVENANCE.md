# D-3 per-event scoring artifacts — rescue provenance

Rescued verbatim (byte-for-byte copy, no re-derivation, no re-scoring) by D-4a Lane A-0
(2026-07-19) from the prior D-3 session's scratchpad at
`/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/d6aa9c91-2f4f-4044-8214-8432b8934686/scratchpad/`,
which was still present at rescue time (scratchpads are session-isolated and may be cleaned up
at any point — this is why BRIEF_D4A item 4 called for a rescue-or-re-derive pass).

Files rescued:
- `score_g.py` — the D-3 per-event scoring script.
- `lel_events.json` — the LEL event set the D-3 scoring run consumed.
- `pooled_activations.json` — pooled activation windows used by the scorer.
- `result_g.json` — the D-3 scoring run's output.
- `coverage_matched_control.py` — A1's coverage-matched control-gap re-analysis script
  (the -16.1pp raw -> -15.8pp coverage-matched finding cited in MARSYS_DEFECT_GAP_REGISTER
  CR-109's row).
- `coverage_matched_result.json` — that re-analysis's output.

Not rescued (present in the source scratchpad but not requested by BRIEF_D4A item 4):
`service.py`, `ks.py`, `eng.py`, `ts.py`, `err.log`, `__pycache__/` — working-tree scaffolding,
not the named per-event artifacts.

This is a passive rescue only — no lane in D-4a re-ran, re-scored, or touched the sealed LEL
test split (events on/after 2020-01-01) or the D-3 scoring harness's live behavior. Per
ESCALATION_POLICY_v1_0.md §4, only the gate runner and anti-gaming verifier may read the test
split; this rescue is a filesystem copy of a prior session's already-produced output, not a new
read of the harness.
