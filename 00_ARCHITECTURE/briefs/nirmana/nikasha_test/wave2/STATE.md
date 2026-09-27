---
artifact: NIKASHA_WAVE2_STATE
version: "0.2"
status: LIVE — W2-1 accepted and folded; W2-2 next
campaign_id: nikasha-wave2
authority: 00_ARCHITECTURE/briefs/nirmana/NIKASHA_WAVE2_EXECUTION_PROMPT_v1_0.md
---

# Nikaṣa wave 2 — STATE

| packet | rows | gate | state |
|---|---|---|---|
| W2-1 | R224 R231 R223 R222 R225 R42 R52 R56 R48 | W2-1_REVIEW + W2-1_C1_REVIEW: ACCEPT_WITH_CORRECTIONS; **R222 precondition MET** | FOLDED (register v2.3) |
| W2-2 | R44 R49 R45 D6-item-2 R43 R46 R50 R51 R53 R54 R232 R233 | — | NEXT |
| W2-3 | R20 R21 R23 | — | queued |

## Events
- 2026-09-27 · W2-1 built (9 rows, one commit each); gate 1 accepted with corrections but found queued rows counted as runs (C1) → precondition NOT_MET; C1 fixed via started_at; re-gate: precondition MET — all 262 live ledger rows read NO_DETECTOR/PARTIAL/FAIL, simulated first emit 596 OPEN / 0 CLOSED; C4 pinning tests exposed R233 (fail-safe).
- The first production `--emit-gaps` is cleared but NOT run — awaiting the native's choice.
