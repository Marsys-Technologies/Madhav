---
artifact: NIKASHA_WAVE2_STATE
version: "1.0"
status: CLOSED — all three packets accepted; wave 2 complete
campaign_id: nikasha-wave2
authority: 00_ARCHITECTURE/briefs/nirmana/NIKASHA_WAVE2_EXECUTION_PROMPT_v1_0.md
launched: 2026-09-27
closed: 2026-09-28
---

# Nikaṣa wave 2 — STATE (closed)

| packet | rows | gate passes | outcome |
|---|---|---|---|
| W2-1 | R224 R231 R223 R222 R225 R42 R52 R56 R48 | REVIEW (ACCEPT_WITH_CORRECTIONS, R222 NOT_MET) → C1_REVIEW (ACCEPT, MET) | FOLDED — first production emit cleared and RUN (567 gaps, a72cdf460) |
| W2-2 | R233 R44 R49 R45 D6-item-2 R43 R46 R50 R51 R53 R54 R232 | REVIEW (ACCEPT_WITH_CORRECTIONS — ka_kshetra wrong) → C_KSHETRA_REVIEW (ACCEPT) | FOLDED |
| W2-3 | R20 R21 R23 R240 R241 R242 | REVIEW (ACCEPT_WITH_CORRECTIONS) → C1_REVIEW (ACCEPT_WITH_CORRECTIONS — bo_upaya) | FOLDED |

## What wave 2 delivered

The inspector went from "can close a row" (wave 1) to "closes only rows it has genuinely earned",
across every dimension tested: unmeasured branches, stale rows, misattributed evidence, database-level
holds, and delegated cleanup logic. Two real wrong-verdict defects were found and fixed during the
wave's own corrections passes, not by the original build — ka_kshetra (W2-2) and bo_upaya (W2-3) — each
the same failure class one layer deeper than the last. Six PASSes are chart-conditional by database
design (R243), not a defect. One real defect (bo_upaya) is withheld pending a native ruling (R244).

The first production `--emit-gaps` ran (2026-09-27, commit a72cdf460): 567 gaps opened, 0 closed, ledger
grown from 263 to 830 lines. Every later emit must follow R244's manual withholding procedure until
bo_upaya is fixed or R246's detector lands.

## Events
- 2026-09-27 · W2-1 built and folded; first production emit run and committed.
- 2026-09-27 · W2-2 built; gate found ka_kshetra's Idem.pattern PASS wrong (refused-rebuild counted as replace); fixed, re-gated ACCEPT, folded.
- 2026-09-28 · W2-3 built (delegation-following, blocking radius, field reachability); gate found 6 chart-conditional PASSes (database-enforced, not a defect) and required report corrections; the corrections pass itself then found bo_upaya's PASS is unearned on every chart (a real defect, missed by the original 17-item hand-check); independently re-verified, screened for other landmines (none found), folded with bo_upaya withheld.
