---
artifact: NIKASHA_WAVE1_STATE
version: "0.1"
status: LIVE — rewritten at every lane/gate event
campaign_id: nikasha-wave1
authority: 00_ARCHITECTURE/briefs/nirmana/NIKASHA_WAVE1_EXECUTION_PROMPT_v1_0.md
launched: 2026-09-27
---

# Nikaṣa wave 1 — STATE

| lane | scope | status | gate |
|---|---|---|---|
| A | R216 → P3 closure loop → P4 precursors (R41, R40, R220, D6) | LAUNCHED | — |
| B | R85 catalog provenance derivation → closure → R219 reader scan → `--check` | LAUNCHED | — |

Baselines (2026-09-27, read-only prod): active assets 127; SCUs 182, with producer claims 12 (15 assets),
with `source_query` 137 (135 resolve); necessity closure 63/127; `build_runs.last_error` empty 288/419;
`asset_throughput.rows_per_second` NULL 268/268; `duration_seconds` column ABSENT (migration 1094 not deployed).

## Events
- 2026-09-27 · wave launched; prompt v1.0 committed; both lanes dispatched (builders Sonnet, gate Opus).
