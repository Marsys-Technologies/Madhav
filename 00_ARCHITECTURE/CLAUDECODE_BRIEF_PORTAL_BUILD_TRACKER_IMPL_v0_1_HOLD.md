---
artifact: CLAUDECODE_BRIEF_PORTAL_BUILD_TRACKER_IMPL_v0_1_HOLD.md
version: 0.1
status: HELD_PENDING_LATER_ACTIVATION
held_on: 2026-04-26
held_by: Cowork (Claude Opus 4.7) during conversation "Madhav M2A-Exec-7 — B.4 Task 3 (Gemini SUPPORTS two-pass)"
hold_reason: >
  This brief was the active CLAUDECODE_BRIEF.md for Madhav_PORTAL_BUILD_TRACKER_IMPL_v0_1
  (Build Tracker portal Session 1 of 3, governance_aside). Cowork orchestration thread
  Madhav_M2A_Exec_7 was running in parallel for the M2 corpus Exec_7 brief authoring
  (Gemini SUPPORTS two-pass). The native (2026-04-26) directed Cowork to set up Exec_7 as
  the active brief immediately, deferring the Build Tracker 3-session sprint. To preserve
  the Build Tracker brief content for later resumption, it is held here verbatim. The
  decision to defer the portal sprint is the native's; this hold is the safety net.
activation_protocol: >
  When the native decides to resume the Build Tracker portal sprint, a Cowork (or Claude Code
  self-authoring) session re-publishes this content to /Users/Dev/Vibe-Coding/Apps/Madhav/CLAUDECODE_BRIEF.md.
  Apply deltas if Exec_7 (or any intervening session) changed referenced files: most notably,
  if FILE_REGISTRY has bumped beyond v1.6, AC.25 needs the new "from version" updated; if
  CANONICAL_ARTIFACTS has new rows, AC.27's COWORK_LEDGER row insertion location may shift;
  if any §4 must_not_touch entry was modified by the intervening session, scope check at
  re-activation. Otherwise the brief is verbatim.
build_tracker_session_status_at_hold: >
  status was IN_PROGRESS at hold moment (frontmatter line 4). It is unknown whether Claude
  Code in VS Code had begun executing any of the 14 Session 1 ACs at the hold moment. If
  any work was started but not closed, the resuming session must verify on-disk state
  (serializer version, schema files, COWORK_LEDGER existence, FILE_REGISTRY version) before
  continuing — partial work is not necessarily wasted, but partial work + this brief's full
  AC list together can lead to double-execution. Resuming session should diff repo state
  against the §3 AC tests and skip ACs that already pass on disk.
predecessor_session: Madhav_M2A_Exec_6 (CLOSED 2026-04-26)
target_executor: Claude Code (Sonnet 4.6)
expected_session_class: governance_aside
session_count: "Session 1 of 3 per plan §18"
governing_plan: 00_ARCHITECTURE/PORTAL_BUILD_TRACKER_PLAN_v0_1.md (v0.1.1, APPROVED_FOR_IMPLEMENTATION)
---

# CLAUDECODE_BRIEF — Madhav_PORTAL_BUILD_TRACKER_IMPL_v0_1 — Session 1 (HELD)

*Original brief content held verbatim below. The active CLAUDECODE_BRIEF.md slot is now occupied by the Madhav_M2A_Exec_7 brief (B.4 Task 3 SUPPORTS sub-task) per native direction 2026-04-26.*

---

## §1 — Why this session exists

Session 1 of 3 for the Build Tracker portal (`PORTAL_BUILD_TRACKER_PLAN_v0_1.md` v0.1.1,
APPROVED_FOR_IMPLEMENTATION 2026-04-26). Session 1 scope: extend the serializer to v0.2.0,
author three JSON schemas, create the COWORK_LEDGER canonical artifact, and extend four
governance templates/schemas. Sessions 2 + 3 cover the Next.js portal data layer and views.

This session does NOT touch M2 corpus files. It is `governance_aside` and does NOT increment
`red_team_counter`.

---

## §2 — Active context

- **Macro phase:** M2 — Corpus Activation, active.
- **Phase-plan:** PHASE_B_PLAN_v1_0.md v1.0.3. B.4 Session 1 closed (Exec_6). B.4 Task 3
  (SUPPORTS two-pass) is the next M2 corpus objective — Madhav_M2A_Exec_7.
- **Governance:** Steady-state post-Step-15. Quarterly pass due 2026-07-24.
- **Red-team counter:** 1 at Exec_6 close. This governance_aside does NOT increment.

---

## §3 — Acceptance criteria (Session 1 of 3)

Scoped from `PORTAL_BUILD_TRACKER_PLAN_v0_1.md §11` + `§13 Session 1 row`.

| # | AC | Test |
|---|---|---|
| **AC.1** | `serialize_build_state.py --version` returns `0.2.0` | `python3 platform/scripts/governance/serialize_build_state.py --version` |
| **AC.2** | `--emit-shards --validate-against-schema` writes top-level + per-session + per-phase shards | Inspect output dir; count files |
| **AC.3** | Each emitted JSON validates against its schema | `--validate-against-schema` exits 0 |
| **AC.4** | Top-level JSON contains all keys from plan §3.2.1 with non-null values | jq queries |
| **AC.5** | GCS `build-state.json` updated; HTTP 200 + `"schema_version": "0.2.0"` | curl + jq |
| **AC.6** | ≥1 `gs://marsys-jis-build-state/sessions/{id}.json` exists | curl -sI |
| **AC.7** | ≥1 `gs://marsys-jis-build-state/phases/{id}.json` exists | curl -sI |
| **AC.8** | Default invocation produces v0.2-shape that v0.1 consumers can read | run default; all v0.1 keys present |
| **AC.21** | `COWORK_LEDGER.md` exists with frontmatter + schema + ≥4 bootstrap rows | file presence + grep |
| **AC.22** | `SESSION_CLOSE_TEMPLATE_v1_0.md` carries `native_overrides[]` + `halts_encountered[]` | grep |
| **AC.23** | `SESSION_LOG_SCHEMA_v1_0.md` §1.5 names 8-element `expected_session_class` enum | grep |
| **AC.24** | mirror_enforcer exit 0; drift_detector exit ≤3; schema_validator exit ≤3 | run all three |
| **AC.25** | `FILE_REGISTRY_v1_7.md` exists; v1.6 SUPERSEDED banner added; new rows present | file + grep |
| **AC.26** | `ONGOING_HYGIENE_POLICIES_v1_0.md` §P + §O `shards_emitted` field present | grep |
| **AC.27** | `CANONICAL_ARTIFACTS_v1_0.md` has `COWORK_LEDGER` row; fingerprint matches sha256 | sha256sum |

*Session 2 ACs: AC.9–AC.13, AC.18–AC.20, AC.28. Session 3 ACs: AC.14–AC.17, AC.19 final, AC.24 closing.*

---

## §4 — may_touch / must_not_touch

### may_touch
```
platform/scripts/governance/serialize_build_state.py
platform/scripts/governance/schemas/build_state.schema.json
platform/scripts/governance/schemas/build_state_session_detail.schema.json
platform/scripts/governance/schemas/build_state_phase_detail.schema.json
00_ARCHITECTURE/COWORK_LEDGER.md
00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md
00_ARCHITECTURE/SESSION_LOG_SCHEMA_v1_0.md
00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md
00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
00_ARCHITECTURE/FILE_REGISTRY_v1_6.md          # supersession banner only
00_ARCHITECTURE/FILE_REGISTRY_v1_7.md          # NEW
00_ARCHITECTURE/CURRENT_STATE_v1_0.md          # state-block update at close
00_ARCHITECTURE/SESSION_LOG.md                 # append at close
00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md       # amendment log at close
.gemini/project_state.md                       # MP.2 state-block update at close
CLAUDECODE_BRIEF.md                            # set status COMPLETE at close
00_ARCHITECTURE/PORTAL_BUILD_TRACKER_PLAN_v0_1.md  # §3.4 footnote + §19 append
```

### must_not_touch
```
01_FACTS_LAYER/**, 025_HOLISTIC_SYNTHESIS/**, 03_DOMAIN_REPORTS/**
04_REMEDIAL_CODEX/**, 05_TEMPORAL_ENGINES/**, 06_LEARNING_LAYER/**
035_DISCOVERY_LAYER/**, platform/python-sidecar/**, platform/src/**
00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md, 00_ARCHITECTURE/MACRO_PLAN_v2_0.md
00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md
00_ARCHITECTURE/GOVERNANCE_BASELINE_v1_0.md
00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md
00_ARCHITECTURE/STEP_LEDGER_v1_0.md
00_ARCHITECTURE/NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md
00_ARCHITECTURE/STALENESS_REGISTER.md
00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md
00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md
verification_artifacts/**
```

---

## §5 — Known context (recorded during session-open inspection)

- FILE_REGISTRY observed CURRENT: **v1.6** → bump to v1.7 (per plan §0.2.A.1 amendment).
- Governance report JSON sidecar analysis (plan §0.2.A.2): **branch (a) confirmed** — all
  three report types have JSON sidecars with `exit_code`. Field mapping:
  - Drift: `d['drift_report']['exit_code']`, `len(d['drift_report']['findings'])` for count.
  - Schema: `d['schema_validation_report']['exit_code']`, `d['schema_validation_report']['summary']['total']`.
  - Mirror: top-level `d['exit_code']`, `d.get('pairs_failed', 0)`.
  Full trend reader implemented in serializer v0.2.0. §3.4 footnote appended to plan.
- COWORK_LEDGER bootstrap rows: planning thread + BUILD_TRACKER_INTEGRATION_v0_1 +
  GCS_BOOTSTRAP + GCS_PERMISSIONS_FIX = 4 rows (≥4 required by AC.21).
