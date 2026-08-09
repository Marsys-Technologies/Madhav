---
artifact: SAMPURTI_STATE.md
campaign: SAMPŪRTI — Gap Remediation (G1–G16, PA-0–PA-8, R23–R29)
plan_of_record: 00_ARCHITECTURE/briefs/sampurti/MASTER_PLAN_v1_0.md
version: rolling
status: LIVE
single_writer: CONDUCTOR only (builders/verifiers NEVER touch this file)
branch_model: >
  Integration branch sampurti/integration cut from main @ 1432d7492 (2026-08-10).
  All lane work in worktrees off sampurti/integration; lane PRs -> integration;
  integration -> main only via Gate-Executor packets at wave boundaries.
conductor_session: SAMPURTI-CONDUCTOR-2026-08-10 (first run)
---

# SAMPŪRTI CAMPAIGN LEDGER

CONDUCTOR-HEARTBEAT: 2026-08-10T03:42+05:30 (SAMPURTI-CONDUCTOR-2026-08-10)

## WAVE POSITION

WAVE 0 — IGNITION. Status: ALL 6 LANES DISPATCHED 03:40 IST (background builder
agents, isolated worktrees off sampurti/integration @ 36fa880ae). Conductor is
executing Wave-1 S1 (PA-0 stage I/O map, read-only) while builders run — S1 is
explicitly conductor-permitted and touches no builder files.
Waves 1–4: NOT-STARTED.

## RAILS (immutable, restated for every reader)

R13 no-fitting · R19 L1 sealed · R14 measurement versioning (never overwrite) ·
sweep corpus untouchable (report 606/606 + 16,297/19,323 detector-cited after
each rebuild) · R18 bounded scoring · blind-before-effect (definition committed
before effects computed; CI-checkable by commit order) · R16 every claim
scope-stated + detector-cited · R29 full delegation to NATIVE-PRATINIDHI except
life-event data creation (Abhinandan LEL AWAITING-NATIVE; genuinely ambiguous
LEL resolver rows PARKED-honest, never guessed).

## WAVE 0 LANE TABLE

| Lane | Scope (short) | Branch | Status | Poll deadline (IST) | PARĪKṢAKA | PRATINIDHI |
|---|---|---|---|---|---|---|
| L0a | G16 record repair (CURRENT_STATE:124 + close artifact to main path + 51 census rows + CI citation-resolution upgrade) | sampurti/l0a-record-repair | DISPATCHED 03:35 | 04:35 | — | required |
| L0b | G4a bg_sarvatobhadra_grid root-cause + dispatch | sampurti/l0b-grid | DISPATCHED 03:35 | 04:35 | — | n/a |
| L0c | G12e kala_dasha_sandhi_get prod registration + stale "eight" docstrings | sampurti/l0c-dasha-sandhi | DISPATCHED 03:35 | 04:35 | — | n/a |
| L0d | G13/PA-4 KNOWN_DOMAINS 7→13 migration in bo_sangati/bo_bimba/bo_karanajala (R17 delete local lists) | sampurti/l0d-vocab | DISPATCHED 03:35 | 04:35 | — | required |
| L0e | Pre-rebuild content fixes: G8 KaryatvaMaps ×5 + G10 varga_confirmation + G9 doc-direction reconcile | sampurti/l0e-content | DISPATCHED 03:35 | 05:05 | — | required |
| L0f | G14a L6 LEL→event_class resolver + 64-event backfill classification | sampurti/l0f-resolver | DISPATCHED 03:35 | 05:05 | — | n/a |

Merge order: train on CI-green + PARĪKṢAKA verdict recorded HERE before merge.
ONE gate packet at wave end → main + deploy (content fixes must be deployed
before Wave 1's rebuild).

## G9 DISPUTES QUEUE (for Wave 3 mini-cycles)

(empty — L0e populates)

## L0f PARKED-AMBIGUOUS LEL ROWS (await native's memory — never guessed)

(empty — L0f populates)

## DECISIONS LOG (PRATINIDHI rulings with written rationale)

(none yet)

## GATE LOG (integration → main packets, deploy evidence, production==main)

(none yet)

## DEBTS / PARKS (cause VERIFIED live or it is a defect)

(none yet)

## NEXT-ACTION

Conductor: poll Wave 0 lanes at their deadlines (04:35 / 05:05 IST 2026-08-10);
on each lane completion dispatch PARĪKṢAKA (opus, fresh) and record verdict here
BEFORE merge; L0a/L0d/L0e additionally need NATIVE-PRATINIDHI end-to-end pass.
Then merge train → Wave 0 gate packet → main + deploy → Wave 1 S1 (PA-0 stage
I/O map). If this conductor dies: resume per prompt — adopt live lanes from this
table, salvage (commit+push) any dead builder worktree, never re-dispatch merged
work.
