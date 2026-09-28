---
artifact: SUVARNA_DOCUMENT_MAP
canonical_id: SUVARNA_DOCUMENT_MAP
version: "1.0"
status: DRAFT — living; updated whenever a campaign document is added, versioned or retired
produced_on: 2026-09-28
produced_in: session "Strategic Suvarṇa"
changelog:
  - "1.0 (2026-09-28): first map. Every document that composes the Suvarṇa campaign and the Nikaṣa engine, where it lives, its status, and what is still to be written."
---

# Suvarṇa — document map

Every document that composes the campaign, grouped by the part it serves.

**Where things live.** Most engine documents exist **only on branch `campaign/nikasha-test`**
(worktree `/Users/Dev/madhav-nikasha`). They are **not on `main`** yet. Landing them is Track E, item E4 (decision N-3).
Until then, the review package (`SUVARNA_REVIEW_PACKAGE_v1_0.md`) bundles them in one folder.

Branches: **S** = `strategy/suvarna-plan` · **N** = `campaign/nikasha-test` · **M** = `main` · **G** = `governance/nirmana-supersession` (PR #2751).

## 1 · The campaign's governing documents (new)

| Document | Branch | Status | Role |
|---|---|---|---|
| `briefs/suvarna/SUVARNA_CAMPAIGN_PLAN_v1_1.md` | S | draft, review pass 1 | The master plan: end state, standard, tracks, gates, decisions |
| `briefs/suvarna/SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md` | S | draft | How it runs: isolation, swarm, queue, builds, autonomy, cost |
| `briefs/suvarna/SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` | S | draft | Sangam, Kshetra, Gochara: current state, target, effort |
| `briefs/suvarna/SUVARNA_DOCUMENT_MAP_v1_0.md` | S | living | This map |
| `briefs/suvarna/SUVARNA_REVIEW_PACKAGE_v1_0.md` | S | draft | The brief for the independent reviewer |
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
| `briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md` | N | v2.7, living; 252 rows (header tallies need repair, §5.0 of the plan) |
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
| `briefs/nirmana/NIRMANA_SUPERSESSION_RECORD_v1_0.md` | G | RULED; lists the 98 kept assets |
| `briefs/nirmana/NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md` | M | marked SUPERSEDED on G |
| `briefs/nirmana/NIRMANA_AUTONOMOUS_EXECUTION_PROMPT_v1_0.md` | M | marked SUPERSEDED on G |
| `briefs/nirmana/CAMPAIGN_STATE.md` | M | marked SUPERSEDED on G |
| `autonomy/CHARTER.md` (Nirmāṇa's delegated-authority charter) | main checkout | history; its structure is reused for Suvarṇa's charter |

## 6 · Project governance the campaign obeys (inherited)

| Document | Why it matters here |
|---|---|
| `CLAUDE.md` (root) | §N.2 frozen writer contract; §N.3 idempotency; §N.5 L1 authority; §N.7 narration; §N.8 earned signal |
| `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` | the "you are here" pointer; v6.87 records the supersession (on G) |
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

**The review bundle** (not committed; assembled for the independent reviewer): `/Users/Dev/suvarna-review-bundle/` and `/Users/Dev/suvarna-review-bundle.zip` — 40 files, each listed in `MANIFEST.txt` with its origin branch and sha256.

## 8 · Still to be written, in the order needed

| Document | Written in | Needed by |
|---|---|---|
| `SUVARNA_AUTONOMY_CHARTER_v1_0.md` — granted, reserved, prohibited powers | Strategic Suvarṇa | before any execution |
| Role prompts: conductor, steward, architect, analyst, builder, gate reviewer, build operator, scribe | Strategic Suvarṇa | before any execution |
| `SUVARNA_RUNBOOK_v1_0.md` — isolation setup, launch, monitor, hold, restart | Strategic Suvarṇa | before any execution |
| Track E brief (Nikaṣa Engine) | Strategic Suvarṇa | Track E start |
| Track A brief (analysis, all layers) | Strategic Suvarṇa | Track A start |
| Track F briefs, one per family | Strategic Suvarṇa | Track F start |
| Combined reopen agendas: T1, T2, T3 | Strategic Suvarṇa, from Track E and Track A | J1 |
| Tracks I and B brief (implementation, rebuild, certification) | Strategic Suvarṇa | after J1 |
| L1–L5 layer instances; 122 asset briefs | Track A | per layer |
| Layer close reports | Track B | per layer |
| Closure report | Closure | end |
