---
artifact: SUVARNA_DOCUMENT_MAP
canonical_id: SUVARNA_DOCUMENT_MAP
version: "1.3"
status: "LIVING v1.3 — plan set v1.5 pre-final (for the parallel independent reviews, N-30)"
produced_on: 2026-09-28
produced_in: session "Strategic Suvarṇa"
changelog:
  - "1.3 (2026-09-30, plan set v1.5): plan v1.5 added, v1.4 SUPERSEDED; charter and architecture v1.5; runbook v1.3; track briefs v1.2; runtime v1.2 (/loop withdrawn, N-34); roles v1.3; start prompts v1.3; Saṅgam/Kṣetra prompts v1.4 (kept; used only if the native opens such a session); Gochara prompt RETIRED (superseded by Pravāha's sealed doctrine); correction notice v1.3 (published on the coordination branch); focus families v1.4; D6 runbook v1.4; review package v2.1 (current; two reviewers, one bundle); new NATIVE_SETUP_v1_0.md and reviews/INDEPENDENT_REVIEW_ASTRA_DISPOSITION_v1_0.md; the Astra review added; decisions log moved to authority/ (N-37); Pravāha documents listed; §8 rebuilt from the v1.5 launch track."
  - "1.2.1 (2026-09-30, review pass 3 folded in place): plan v1.4.1, charter v1.4.1, architecture v1.4.1, runbook v1.2.1, track briefs v1.1.1, interim runtime v1.1.1, start prompts v1.2.1, role files v1.2 (analyst, builder, build operator, common, monitor v1.2.1), family prompts v1.3, correction notice v1.2; review pass 3 and its disposition added."
  - "1.2 (2026-09-29, plan set v1.4, review pass 2): plan v1.4 added, v1.3 superseded; charter v1.4, architecture v1.4, families v1.3, runbook v1.2, roles and prompts v1.2, correction notice v1.1, track briefs v1.1 (rows added), D6 runbook v1.3 (applied); tracker at 260 tests after L.13, run from the hq worktree; review package marked stale (L.12r); pass-2 reviews and disposition added; §8 rebuilt (L.11–L.13 done)."
  - "1.1 (2026-09-29, plan set v1.3): plan v1.3 added and v1.2 marked superseded; charter v1.3 (v1.2 approved: N-19 + A–C); architecture v1.3; focus families v1.2; D6 runbook, the D6 bootstrap script, the review reports and the pass-1 disposition added; decisions log now authoritative outside git ($SUVARNA_HOME/run/DECISIONS.jsonl), committed copy a mirror; register v2.8 with repaired tallies; tracker 198 tests; PR #2751 merged (branch G replaced by M); §8 rewritten from the launch items L.11–L.15 (charter, roles and runbook removed as written; Track F briefs now written by the family sessions). Map 1.0 changed on 2026-09-29 without a bump; recorded here (REVIEW_PASS1_CONSISTENCY #9)."
  - "1.0 (2026-09-28): first map. Every document that composes the Suvarṇa campaign and the Nikaṣa engine, where it lives, its status, and what is still to be written."
---

# Suvarṇa — document map

Every document that composes the campaign, grouped by the part it serves.

Branches: **S** = `strategy/suvarna-plan` · **N** = `campaign/nikasha-test` · **M** = `main` · **H** = `suvarna/hq` ·
**A** = outside git, native-owned `$SUVARNA_HOME/authority/` · **R** = outside git, `$SUVARNA_HOME/run/` · **P** =
`/Users/Dev/madhav-l3/pravaha` (the Pravāha campaign's, read only).

Most engine documents still exist only on **N** (not on `main`); landing them is Track E (E4.1).

## 1 · The campaign's governing documents

| Document | Branch | Status | Role |
|---|---|---|---|
| `briefs/suvarna/SUVARNA_CAMPAIGN_PLAN_v1_5.md` | S | **pre-final v1.5** (for the dual review, N-30) | The master plan |
| `briefs/suvarna/SUVARNA_AUTONOMY_CHARTER_v1_0.md` | S | v1.5 pre-final (v1.2 native-approved; v1.3–v1.5 sourced to rulings) | What the swarm decides, parks to SS, refuses |
| `briefs/suvarna/SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md` | S | v1.5 pre-final | How it runs: isolation, runtime, builds, serving guard, Monitor, tracker, conventions |
| `briefs/suvarna/NATIVE_SETUP_v1_0.md` | S | **new** v1.0 | The only things the native physically does (NS.1–NS.10, NP.1), with checks |
| `briefs/suvarna/SUVARNA_RUNBOOK_v1_0.md` | S | v1.3 | Launch, operation, holds, recovery, incidents (for SS and the swarm) |
| `briefs/suvarna/tracks/TRACK_E_BRIEF_v1_0.md`, `TRACK_A_BRIEF_v1_0.md` | S | v1.2 | Packets, write sets, detector pins; the F-3 lane; E5 drills; E7 server enforcement |
| `briefs/suvarna/runtime/INTERIM_RUNTIME_v1_0.md` | S | v1.2 (the `/loop` interim withdrawn by N-34; settings, hook and Monitor parts in force) | Settings generator, hold hook, heartbeat check |
| `briefs/suvarna/roles/ROLE_*_v1_0.md` (shared rules + 9 roles) | S | v1.3 | What each agent is told |
| `briefs/suvarna/prompts/{NIKASHA_ENGINE,EXEC_SUVARNA}_START_PROMPT_v1_0.md` | S | v1.3; used after N-1 | Start prompts of the two execution sessions |
| `briefs/suvarna/prompts/L3_{SANGAM,KSHETRA}_FINAL_BRIEF_PROMPT_v1_0.md` | S | v1.4, kept: used only if the native opens such a session; otherwise the Track F lane brief | Family prompts |
| `briefs/suvarna/prompts/L3_GOCHARA_FINAL_BRIEF_PROMPT_v1_0.md` | S | **RETIRED** v1.4 (superseded by Pravāha's sealed doctrine) | History |
| `briefs/suvarna/prompts/L3_FAMILY_CORRECTION_NOTICE_2026-09-29.md` | S → coordination branch | v1.3; published on `campaign-coordination` (FI-8; ack `ACK FI-8 notice v1.3`) | The relay to Pravāha and any family session |
| `briefs/suvarna/SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` | S | v1.4 | Gochara (Pravāha), Saṅgam, Kṣetra; the '3.0' validity note for the native |
| `briefs/suvarna/D6_SUVARNA_READER_RUNBOOK_v1_0.md`, `platform/scripts/suvarna-reader-bootstrap.ts` | S | v1.4; applied 2026-09-29 | The read-only login |
| `briefs/suvarna/SUVARNA_REVIEW_PACKAGE_v1_0.md` | S | **v2.1, current** (two reviewers, one bundle, 24 questions) | The brief for GPT-6 Astra and Kimi K3 |
| `control/suvarna/plan_model.json` | S | living (v1.5: 211 items; NS.*, LG.*, J1.FO, Pravāha peer items) | The plan in machine form |
| `platform/scripts/governance/suvarna_tracker/` | S (authored) → `control/` (runs, at the pinned control release) | built (685/686 tests pass on the v1.5 model; CODE-36…65 to implement) | Tracker, Monitor, CLIs, hook; broker, merge gate, gate evaluator to come |
| `$SUVARNA_HOME/authority/DECISIONS.jsonl` | A | **authoritative**, append-only (moves from `run/` at NS.4) | Decisions, written only by SS through `decide` |
| `$SUVARNA_HOME/authority/HOLDS.jsonl`, `HOLD_CLEARS.jsonl` | A | new with NS.4 (N-35) | Holds (swarm appends) and clears (SS; native holds by the native) |
| `control/suvarna/state/{DECISIONS,QUEUE,QUEUE_ENGINE}.jsonl`, `DIGEST_<date>.md` | H | mirror · living | Decisions mirror, work queues, digests |
| `briefs/suvarna/reviews/INDEPENDENT_REVIEW_GPT6_ASTRA_v1_0.md` | S | done (DO NOT APPROVE on v1.4.1) | The first independent review |
| `briefs/suvarna/reviews/INDEPENDENT_REVIEW_ASTRA_DISPOSITION_v1_0.md` | S | v1.0 | Where each Astra finding and condition landed; CODE-36…65 |
| `briefs/suvarna/reviews/REVIEW_PASS{1,2,3}_*`, `FABLE_REVIEW_D1_D5_v1_0.md` | S | done | Internal passes 1–3 and their dispositions; the delegated review behind D1–D5 |
| `briefs/suvarna/SUVARNA_CAMPAIGN_PLAN_v1_4.md` | S | **SUPERSEDED** by v1.5 | History |
| `briefs/suvarna/SUVARNA_CAMPAIGN_PLAN_v1_{0,1,2,3}.md` | S | superseded | History |
| `briefs/suvarna/SUVARNA_DOCUMENT_MAP_v1_0.md` | S | living v1.3 | This map |

## 2 · The standard — the four-tier chain (inherited)

| Document | Tier | Branch | Status |
|---|---|---|---|
| `MADHAV_PRODUCT_DEFINITION_FINAL.md` | 1 | N | sealed; reopen agenda ruled |
| `briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md` | 2 | N | sealed; reopen agenda ruled |
| `briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md` | 3 | N | sealed; reopen agenda ruled |
| `briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md` | 4 | N | draft; accepted by SS at J1 (N-7.T4) |
| `briefs/nirmana/ELEVATION_DERIVATION_CHAIN_v1_0.md` | — | N | v1.1 |

Instances: the L0 layer instance v3.0 and five L0 pilot briefs (N, drafts); L1–L5 instances and 122 briefs to be written
(Track A). Reviews of the standard: `briefs/reviews/REVIEW_DATA_PLANE_*`, `REVIEW_L0_STRATEGY_v2_0.md` (N).

## 3 · The engine — Nikaṣa (inherited, live)

Register `briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md` (N, v2.8: 252 rows, 180 open); implementation plan
`NIKASHA_IMPLEMENTATION_PLAN_v1_0.md` (N); the test campaign and its three waves (`nikasha_test/**`, N); rulings
`nikasha_test/DECISIONS_FOR_THE_NATIVE.md`, `DECISIONS_RECOMMENDATIONS_v2_0.md` (N). Machine surfaces on N: the inspector
`asset_census.py`, `asset_elevation_tracker.py`, `catalog_provenance.py`, the ledgers `asset_gaps.jsonl` (857 lines) and
`asset_certs.jsonl` (header only). The build engine: branch `campaign/nirmana-engine` (`briefs/nirmana/engine/**`).

## 4 · Hand-offs

`briefs/nirmana/HANDOFF_TO_L2_BODHA_bo_upaya_2026-09-28.md` (N; fix direction ruled, E4.2) · `engine/HANDOFF_FROM_NIKASHA_2026-09-27.md` (engine; R216, R217).

## 5 · The predecessor — Nirmāṇa (history)

`briefs/nirmana/NIRMANA_SUPERSESSION_RECORD_v1_0.md` (M, ruled; 98 kept assets) and the superseded Nirmāṇa plan, prompt
and state (M).

## 6 · Project governance the campaign obeys

`CLAUDE.md` (§N.2, §N.3, §N.5, §N.7, §N.8) · `CURRENT_STATE_v1_0.md` · `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` ·
`PROJECT_ARCHITECTURE_v2_2.md` · `ROOT_FILE_POLICY.md` · `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md`.

## 7 · The L3 families

| Document | Branch | Role |
|---|---|---|
| `briefs/suvarna/l3_recon/{GOCHARA,SANGAM,KSHETRA}_RECON.md` | S | reconciliations (2026-09-28/29) |
| Pravāha plan model `00_ARCHITECTURE/control/pravaha/plan_model.json`; tracker `127.0.0.1:8766` | P | Gochara's live state, read by `peer_tracker_item` |
| `00_ARCHITECTURE/briefs/pravaha/sealed/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md` | P | the Gochara final brief (sealed; D-BRIEF) |
| `00_ARCHITECTURE/briefs/pravaha/design/L3_FAMILY_COORDINATION_v1_0.md` | P | the consumer contract Saṅgam and Kṣetra designs use |
| `00_ARCHITECTURE/briefs/pravaha/measurement/BASELINE_3_0_v2_1.md` | P | the '3.0' measurement behind the validity note |
| Saṅgam stage 3 (`consolidation/merge-sangam-stage3`), Kṣetra branches (`codex/l3-kshetra-*`) | remote branches | inputs to Track F's design lanes |

**The review bundle** (not committed): built by `python -m suvarna_tracker.review_bundle --out <dir> --zip` for package
v2.1 (CODE-65 points it at plan v1.5 and NATIVE_SETUP), one bundle for both reviewers.

## 8 · Still to be written or done, in the order needed

| What | By | Needed by | Tracker |
|---|---|---|---|
| The v2.1 bundle | SS | the dual review | L.12r |
| Two independent reviews of v1.5 · reconciliation · the final set (with the v1.5 SS decisions recorded) | Astra, K3 · SS | N-1 | L.20a, L.20b, L.21, L.22 |
| CODE-36…65 and the pinned control release | code agent, SS | launch gates | L.13, L.17, LG.7 |
| Native setup | the native (NATIVE_SETUP) | N-1 | NS.1–NS.9 |
| Durable runtime; SS decision runtime | SS + code agent | N-1 | L.14, L.18 |
| Launch-gate drills | the swarm | N-1 | LG.1–LG.10 |
| Saṅgam and Kṣetra final briefs | Track F Architect lanes | SEAL-S, SEAL-K | F1.Sd, F1.Kd |
| Reopen agendas T1–T3; Tracks I and B brief | SS from Tracks E and A | J1 | J1.1a–J1.3a, J1.0d |
| L1–L5 instances; 122 asset briefs | Track A | per layer | A.L1i…A.L5i, A.L1…A.L5 |
| Serving-guard inventory | Track E | the first wave | E5.8 |
| Layer close reports; closure report | Track B; closure | per layer; end | G3.L*, CL.3 |
