---
artifact: SUVARNA_DOCUMENT_MAP
canonical_id: SUVARNA_DOCUMENT_MAP
version: "1.2.1"
status: DRAFT — living; updated whenever a campaign document is added, versioned or retired
produced_on: 2026-09-28
produced_in: session "Strategic Suvarṇa"
changelog:
  - "1.2.1 (2026-09-30, review pass 3 folded in place): plan v1.4.1, charter v1.4.1, architecture v1.4.1, runbook v1.2.1, track briefs v1.1.1, interim runtime v1.1.1, start prompts v1.2.1, role files v1.2 (analyst, builder, build operator, common, monitor v1.2.1), family prompts v1.3, correction notice v1.2; review pass 3 and its disposition added."
  - "1.2 (2026-09-29, plan set v1.4, review pass 2): plan v1.4 added, v1.3 superseded; charter v1.4, architecture v1.4, families v1.3, runbook v1.2, roles and prompts v1.2, correction notice v1.1, track briefs v1.1 (rows added), D6 runbook v1.3 (applied); tracker at 260 tests after L.13, run from the hq worktree; review package marked stale (L.12r); pass-2 reviews and disposition added; §8 rebuilt (L.11–L.13 done)."
  - "1.1 (2026-09-29, plan set v1.3): plan v1.3 added and v1.2 marked superseded; charter v1.3 (v1.2 approved: N-19 + A–C); architecture v1.3; focus families v1.2; D6 runbook, the D6 bootstrap script, the review reports and the pass-1 disposition added; decisions log now authoritative outside git ($SUVARNA_HOME/run/DECISIONS.jsonl), committed copy a mirror; register v2.8 with repaired tallies; tracker 198 tests; PR #2751 merged (branch G replaced by M); §8 rewritten from the launch items L.11–L.15 (charter, roles and runbook removed as written; Track F briefs now written by the family sessions). Map 1.0 changed on 2026-09-29 without a bump; recorded here (REVIEW_PASS1_CONSISTENCY #9)."
  - "1.0 (2026-09-28): first map. Every document that composes the Suvarṇa campaign and the Nikaṣa engine, where it lives, its status, and what is still to be written."
---

# Suvarṇa — document map

Every document that composes the campaign, grouped by the part it serves.

**Where things live.** Most engine documents exist **only on branch `campaign/nikasha-test`**
(worktree `/Users/Dev/madhav-nikasha`). They are **not on `main`** yet. Landing them is Track E, item E4.1 (decision N-3).
Until then, the review package (`SUVARNA_REVIEW_PACKAGE_v1_0.md`) bundles them in one folder.

Branches: **S** = `strategy/suvarna-plan` · **N** = `campaign/nikasha-test` · **M** = `main` · **R** = outside git, in `$SUVARNA_HOME/run/`.

## 1 · The campaign's governing documents (new)

| Document | Branch | Status | Role |
|---|---|---|---|
| `briefs/suvarna/SUVARNA_CAMPAIGN_PLAN_v1_4.md` | S | draft v1.4.1 (review pass 3 folded in place), for native review (N-1) | The master plan: end state, standard, tracks, the J1 checklist (§4.2), launch readiness (§5.0b), decisions with status (§8) |
| `briefs/suvarna/SUVARNA_AUTONOMY_CHARTER_v1_0.md` | S | v1.2 approved (N-19; amendments A–C); v1.3–v1.4.1 changes (D1–D5, review folds, G16, §13 isolation proposed pending N-25) confirmed with N-1 | What the swarm decides alone, parks for the native, or refuses |
| `$SUVARNA_HOME/run/DECISIONS.jsonl` | R | living, append-only, **authoritative** | The native's decisions with sources; written only through `python -m suvarna_tracker.decide`, by Strategic Suvarṇa with the native present (charter P14) |
| `control/suvarna/state/DECISIONS.jsonl` | `suvarna/hq` only | mirror | Committed copy of the log, refreshed by Strategic Suvarṇa with `decide --mirror-to`; never changed on S; never read as the authority |
| `control/suvarna/state/QUEUE.jsonl`, `QUEUE_ENGINE.jsonl` | `suvarna/hq` | living, append-only | One work queue per execution session |
| `briefs/suvarna/roles/ROLE_*_v1_0.md` (shared rules + 9 roles) | S | v1.2 (analyst, builder, build operator, common, monitor v1.2.1) | Instructions each swarm agent receives at dispatch |
| `briefs/suvarna/tracks/TRACK_E_BRIEF_v1_0.md`, `TRACK_A_BRIEF_v1_0.md` | S | v1.1.1, for native approval with N-1 | Packets, write sets and boundaries per lane; detector pins and schemas |
| `briefs/suvarna/runtime/INTERIM_RUNTIME_v1_0.md` | S | v1.1.1 (L.15) | The settings generator and template, the hold-guard hook, `conductor_heartbeat`; power settings |
| `briefs/suvarna/SUVARNA_RUNBOOK_v1_0.md` | S | v1.2.1 | Launch checklist (isolation included), daily operation, hold and resume, restart, incidents |
| `briefs/suvarna/prompts/{NIKASHA_ENGINE,EXEC_SUVARNA}_START_PROMPT_v1_0.md` | S | v1.2.1; used after N-1 | Start prompts for the two execution sessions |
| `briefs/suvarna/SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md` | S | draft v1.4.1 | How it runs: isolation (§2.4, proposed pending N-25), swarm, queue, runtime (§5.5), builds (§6), autonomy, cost, the tracker (§11), operating conventions (§12) |
| `control/suvarna/plan_model.json` | S | living | The plan in machine form: tracks, items, dependencies, decisions, done-detectors. Drives the tracker |
| `platform/scripts/governance/suvarna_tracker/` | S (authored) → `suvarna/hq` (runs) | built, 260 tests at L.13 (`4cef1a958`); v1.4 code items in REVIEW_PASS2_DISPOSITION | The real-time tracker (event log, decisions log, detectors, dashboard), the Monitor, the census lock, the decide CLI, the hq commit wrapper |
| `briefs/suvarna/D6_SUVARNA_READER_RUNBOOK_v1_0.md` and `platform/scripts/suvarna-reader-bootstrap.ts` | S | v1.3; **applied 2026-09-29** (plan `31e035f7…`, `21637553c`); kept for re-apply and rollback | The read-only login `suvarna_reader` (D6) |
| `briefs/suvarna/prompts/L3_{GOCHARA,SANGAM,KSHETRA}_FINAL_BRIEF_PROMPT_v1_0.md` | S | v1.3; in use by the family sessions; changes relayed as reports (FI-8) | Start prompts for the three L3 family sessions |
| `briefs/suvarna/prompts/L3_FAMILY_CORRECTION_NOTICE_2026-09-29.md` | S | v1.2; the native pastes it into each family session (FI-8, closed by their acknowledgements) | The relay of prompt corrections |
| `briefs/l3_families/{GOCHARA,SANGAM,KSHETRA}_FINAL_BRIEF_v1_0.md` | family branches | being written by the family sessions | The sealed final briefs; Suvarṇa's L3 analysis evaluates their latest versions |
| `briefs/suvarna/SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` | S | draft v1.3 | Gochara, Saṅgam, Kṣetra: state, target, effort; how Suvarṇa certifies them (§7) |
| `briefs/suvarna/reviews/REVIEW_PASS1_SUBSTANCE_v1_0.md`, `REVIEW_PASS1_CONSISTENCY_v1_0.md` | S | done | Review pass 1 (30 + 44 findings) |
| `briefs/suvarna/reviews/FABLE_REVIEW_D1_D5_v1_0.md` | S | done | The delegated review behind D1–D5 |
| `briefs/suvarna/reviews/REVIEW_PASS1_DISPOSITION_v1_0.md` | S | done | Where each pass-1 finding was fixed, or why not |
| `briefs/suvarna/reviews/REVIEW_PASS2_SUBSTANCE_v1_0.md`, `REVIEW_PASS2_CONSISTENCY_v1_0.md` | S | done | Review pass 2 (30 + 40 findings) |
| `briefs/suvarna/reviews/REVIEW_PASS2_DISPOSITION_v1_0.md` | S | done (pass-3 follow-up section added) | Where each pass-2 finding was fixed, deferred, sent to code or to the native |
| `briefs/suvarna/reviews/REVIEW_PASS3_v1_0.md` | S | done | Review pass 3 (62 pass-2 fixes checked; 10 blockers, near-blockers) |
| `briefs/suvarna/reviews/REVIEW_PASS3_DISPOSITION_v1_0.md` | S | done | Where each pass-3 finding was fixed, sent to code or to the native |
| `briefs/suvarna/SUVARNA_DOCUMENT_MAP_v1_0.md` | S | living v1.2.1 | This map |
| `briefs/suvarna/SUVARNA_REVIEW_PACKAGE_v1_0.md` | S | **STALE** (v1.0, names plan v1.1); rebuilt for the v1.4 set by L.12r before L.9 | The brief for the independent reviewer |
| `briefs/suvarna/SUVARNA_CAMPAIGN_PLAN_v1_3.md` | S | superseded by v1.4 | History |
| `briefs/suvarna/SUVARNA_CAMPAIGN_PLAN_v1_2.md` | S | superseded by v1.3 | History |
| `briefs/suvarna/SUVARNA_CAMPAIGN_PLAN_v1_1.md` | S | superseded by v1.2 | History |
| `briefs/suvarna/SUVARNA_CAMPAIGN_PLAN_v1_0.md` | S | superseded by v1.1 | History |

## 2 · The standard — the four-tier chain (inherited)

| Document | Tier | Branch | Status |
|---|---|---|---|
| `MADHAV_PRODUCT_DEFINITION_FINAL.md` | 1 — product | N | sealed; reopen agenda ruled (D2) |
| `briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md` | 2 — data plane | N | sealed; reopen agenda ruled |
| `briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md` | 3 — layer template | N | sealed; reopen agenda ruled |
| `briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md` | 4 — asset template | N | draft, pending native acceptance |
| `briefs/nirmana/ELEVATION_DERIVATION_CHAIN_v1_0.md` | how the tiers derive from one another | N | v1.1 |

**Instances of the standard:**

| Document | Branch | Status |
|---|---|---|
| `briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md` (L0 layer instance) | N | draft, pending native acceptance |
| `briefs/nirmana/l0_assets/BG_{ONTOLOGY,RULES,EPHEMERIS,PANCHANGA,SARVATOBHADRA_GRID}_ELEVATION_BRIEF_v1_0.md` (5 pilot asset briefs) | N | pilots; regenerated after tier-4 acceptance |
| L1–L5 layer instances | — | **not yet written** (Track A) |
| 122 further asset briefs | — | **not yet written** (Track A) |

**Reviews of the standard:** `briefs/reviews/REVIEW_DATA_PLANE_v3_0.md`, `REVIEW_DATA_PLANE_FINAL_v1_0.md`, `REVIEW_L0_STRATEGY_v2_0.md` (N).

## 3 · The engine — Nikaṣa (inherited, live)

**Plans and records**

| Document | Branch | Status |
|---|---|---|
| `briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md` | N | v2.8, living; 252 rows, 180 open; tallies computed and detector-checked (FI-3, FI-4) |
| `briefs/nirmana/NIKASHA_IMPLEMENTATION_PLAN_v1_0.md` | N | in progress; packets P1–P10 |
| `briefs/nirmana/NIKASHA_TEST_CAMPAIGN_PROMPT_v1_0.md` | N | executed |
| `briefs/nirmana/nikasha_test/NIKASHA_TEST_CAMPAIGN_REPORT_v1_0.md` | N | the test campaign's findings |
| `briefs/nirmana/nikasha_test/PHASE6_ANALYSIS.md` | N | the freeze-criterion evaluation (§6.5) |
| `briefs/nirmana/nikasha_test/STATE.md` | N | living |
| `briefs/nirmana/NIKASHA_WAVE{1,2,3}_EXECUTION_PROMPT_v1_0.md` | N | executed |
| `briefs/nirmana/nikasha_test/wave1/`, `wave2/`, `wave3/` — reports and gate reviews | N | 21 reports and reviews |

**Rulings**

| Document | Branch | Status |
|---|---|---|
| `briefs/nirmana/nikasha_test/DECISIONS_FOR_THE_NATIVE.md` | N | D1–D6 RULED |
| `briefs/nirmana/nikasha_test/DECISIONS_RECOMMENDATIONS_v2_0.md` | N | v2.1 (D5 revised by the native) |
| `briefs/reviews/REVIEW_NIKASHA_DECISIONS_RECOMMENDATIONS_v1_0.md` | N | the independent review behind them |
| Register rows R227, R244, R246 (native rulings) | N | inside the register |

**Machine surfaces**

| Surface | Branch |
|---|---|
| `platform/scripts/governance/asset_census.py` — the inspector | N |
| `00_ARCHITECTURE/control/asset_elevation_tracker.py` — the tracker | N |
| `platform/scripts/governance/catalog_provenance.py` — catalog provenance | N |
| `00_ARCHITECTURE/control/asset_gaps.jsonl` — the delta ledger (857 lines) | N |
| `00_ARCHITECTURE/control/asset_certs.jsonl` — the certification ledger (header only) | N |
| `briefs/nirmana/nikasha_test/provenance/` — producer provenance and closure reports | N |

**The build engine** (branch `campaign/nirmana-engine`, worktree `/Users/Dev/madhav-engine`): `briefs/nirmana/NIRMANA_ENGINE_ELEVATION_PROMPT_v1_0.md`, `briefs/nirmana/engine/STATE.md`, `engine/DECISIONS_FOR_THE_NATIVE.md`, `engine/reviews/`, `engine/HANDOFF_FROM_NIKASHA_2026-09-27.md`.

## 4 · Hand-offs and findings for owners

| Document | Branch | Status |
|---|---|---|
| `briefs/nirmana/HANDOFF_TO_L2_BODHA_bo_upaya_2026-09-28.md` | N | open; fix direction ruled |
| `engine/HANDOFF_FROM_NIKASHA_2026-09-27.md` (R216, R217) | engine | open |

## 5 · The predecessor — Nirmāṇa (history)

| Document | Branch | Status |
|---|---|---|
| `briefs/nirmana/NIRMANA_SUPERSESSION_RECORD_v1_0.md` | M | RULED; lists the 98 kept assets (PR #2751, merged 2026-09-29) |
| `briefs/nirmana/NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md` | M | marked SUPERSEDED |
| `briefs/nirmana/NIRMANA_AUTONOMOUS_EXECUTION_PROMPT_v1_0.md` | M | marked SUPERSEDED |
| `briefs/nirmana/CAMPAIGN_STATE.md` | M | marked SUPERSEDED |
| `autonomy/CHARTER.md` (Nirmāṇa's delegated-authority charter) | main checkout | history; its structure is reused for Suvarṇa's charter |

## 6 · Project governance the campaign obeys (inherited)

| Document | Why it matters here |
|---|---|
| `CLAUDE.md` (root) | §N.2 frozen writer contract; §N.3 idempotency; §N.5 L1 authority; §N.7 narration; §N.8 earned signal |
| `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` | the "you are here" pointer; records the supersession and Suvarṇa on `main` (FI-5) |
| `00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` | the frozen orchestrator contract every writer conforms to |
| `00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md` | architectural principles B.1–B.12 |
| `00_ARCHITECTURE/ROOT_FILE_POLICY.md` | where files may land |
| `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` | session open and close, drift and schema checks |

## 7 · The L3 focus families (existing documents)

| Document | Branch | Role |
|---|---|---|
| `briefs/suvarna/l3_recon/GOCHARA_RECON.md` | S | reconciliation; §2 lists every Gochara workstream, branch, brief and decision log |
| `briefs/suvarna/l3_recon/SANGAM_RECON.md` | S | reconciliation; §2 lists the stage-3/stage-4 work, PR #2735 and the D-K review |
| `briefs/suvarna/l3_recon/KSHETRA_RECON.md` | S | reconciliation; §2 lists every Kṣetra branch, the W7 dependency and the unstarted stage 3 |
| Live Gochara workstream: `CLAUDECODE_BRIEF*.md`, ADK decision log, WP0–WP7 plan | `l3/gochara-autonomous-wp0-7` (PR #2731) | live; not Suvarṇa's to edit |
| Saṅgam stage 3 | `sangam/stage3` (PR #2735, draft) | unmerged |
| Kṣetra briefs and stage plans | merged to `main` as documents | stage 3 authorized 2026-09-24, not started |

**The review bundle** (not committed; assembled for the independent reviewer): `/Users/Dev/suvarna-review-bundle/` and `/Users/Dev/suvarna-review-bundle.zip` — stale (the v1.1 set); rebuilt with the package by L.12r, each file listed in `MANIFEST.txt` with its origin branch and sha256.

## 8 · Still to be written, in the order needed

| Document | Written in | Needed by | Tracker |
|---|---|---|---|
| Review package and bundle for the v1.4 set | Strategic Suvarṇa | L.9, N-1 | L.12r |
| Runtime: settings file, lane launcher and watchdog (interim), headless runner (durable) | Strategic Suvarṇa | N-1 (interim); B.W1 (durable) | L.15, L.14 |
| Isolation set-up record (user, GitHub identity, branch protection) | native, verified by Strategic Suvarṇa | N-1 | L.16a, L.16g, L.16b |
| Final briefs, one per family | L3 Gochara, L3 Saṅgam, L3 Kṣetra (N-17) | their own implementation | F1.G, F1.S, F1.K |
| Combined reopen agendas: T1, T2, T3 | Strategic Suvarṇa, from Track E and Track A | J1 | J1.1a, J1.2a, J1.3a |
| Tracks I and B brief (implementation, rebuild, certification) | Strategic Suvarṇa, after A.L0 | N-24 (Track I starts there) | J1.0d, J1.0 |
| L1–L5 layer instances; 122 asset briefs | Track A | per layer | A.L1i … A.L5i, A.L1 … A.L5 |
| Layer close reports | Track B | per layer | G3.L0 … G3.L5 |
| Closure report | Closure | end | CL.3 |
