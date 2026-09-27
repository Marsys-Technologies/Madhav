---
artifact: NIKASHA_WAVE2_STATE
version: "0.3"
status: LIVE — W2-1 and W2-2 folded; W2-3 next
campaign_id: nikasha-wave2
authority: 00_ARCHITECTURE/briefs/nirmana/NIKASHA_WAVE2_EXECUTION_PROMPT_v1_0.md
---

# Nikaṣa wave 2 — STATE

| packet | rows | gate | state |
|---|---|---|---|
| W2-1 | R224 R231 R223 R222 R225 R42 R52 R56 R48 | ACCEPT_WITH_CORRECTIONS + re-gate: R222 precondition MET | FOLDED (register v2.3) |
| W2-2 | R233 R44 R49 R45 D6-item-2 R43 R46 R50 R51 R53 R54 R232 | ACCEPT_WITH_CORRECTIONS + C-KSHETRA re-gate: ACCEPT | FOLDED (register v2.4) |
| W2-3 | R20 R21 R23 R240 R241 R242 | — | NEXT |

## Events
- 2026-09-27 · W2-2 built (12 rows); gate found ka_kshetra's Idem.pattern PASS was WRONG (not correct-by-accident) — the writer refuses a rebuild when the chart is populated (KshetraReplacementHeld). Fixed via C-KSHETRA: the fix itself then found two more assets whose Idem.pattern PASS didn't hold up — bo_upaya (honest understatement, delegated replacement) and ka_gochara (registry/table name mismatch, R240). Re-gate: ACCEPT. Real CLI --emit-gaps run on ledger copies (not simulated): 577/0 first emit; 33/14/0 second-emit simulation, ka_kshetra correctly absent from the closed set.
- Both W2-1's and W2-2's blockers on a second production emit (dep_liveness scope, Dens.served comment-as-declaration) are now landed. The first production emit is still not run — awaiting the native.
