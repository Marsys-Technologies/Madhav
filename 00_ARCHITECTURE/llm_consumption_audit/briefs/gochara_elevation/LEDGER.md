---
artifact: LEDGER.md
campaign: GOCHARA-UTKARSA (gochara v3 elevation)
version: rolling
status: LIVE
single_writer: CONDUCTOR only
branch_model: >
  Integration branch utkarsha/campaign cut from main.
  Lane worktrees on gochara3/w* branches; lane PRs merge to integration;
  integration -> main at wave boundaries after VERIFIER PASS.
---

# GOCHARA-UTKARSA CAMPAIGN LEDGER

Campaign plan: GOCHARA_UTKARSHA_CAMPAIGN_PLAN_v1_0.md (same directory)
Cross-campaign coordination: 00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md

## WAVE POSITION

| Wave | Name | Status | Merged |
|---|---|---|---|
| W0 | Foundations | COMPLETE | main (registry + baseline + migration 556 + grammar-v3 catalog) |
| W1 | lambda-v3 bounded formula | COMPLETE | main (W1.1-W1.5) |
| W2 | Mechanism wiring | COMPLETE | main (W2.1-W2.9) |
| W3 | Infrastructure | COMPLETE | main (W3.1-W3.4) |
| W4 | Calibration | COMPLETE | main (W4.1-W4.6, migration 561) |
| W5 | Serving elevation + docs | IN PROGRESS | W5.2 MERGED (migration 562); W5.1/W5.3/W5.4 in flight |
| W6 | v3 replacement cutover | PENDING | awaiting Wave 5 PASS |

## ADJUDICATOR RULING

UTK-R3 (W4.3 ablation): 10 mechanisms ADMITTED (weight_type=fitted) + 2 STRUCTURAL-ONLY (modifier=1.0).
Mechanism register: platform/python-sidecar/services/gochara_v3/mechanism_register.yaml (W5.3 finalized).

## I-INVARIANTS (restated for every reader)

- I2: NEVER edit services/gochara_grammar/, services/gochara_intensity/, services/ka_gochara_sweep/
- I5: NEVER touch orchestrator code (FROZEN contract per ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md)

## LOG

- 2026-08-10: LEDGER.md created at W5.3 docs-of-record lane. Waves 0-4 COMPLETE. Wave 5 IN PROGRESS.
