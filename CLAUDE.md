---
artifact: CLAUDE.md
version: "2.0"
status: CURRENT
role: >
  Root governance surface. Master orientation document for every Claude session on the MARSYS-JIS
  project. Every Claude session opens by reading this file first. Cites the machine-readable
  canonical-artifact registry rather than duplicating it.
produced_during: STEP_9_CLAUDE_MD_REBUILD (Step 0 → Step 15 governance rebuild)
produced_on: 2026-04-24
authoritative_side: claude
mirror_obligations:
  claude_side: CLAUDE.md
  gemini_side: .geminirules
  mirror_mode: adapted_parity
  authoritative_side: claude
  mirror_pair_id: MP.1
  asymmetries: "See CANONICAL_ARTIFACTS_v1_0.md §2 MP.1 known_asymmetries + .geminirules Asymmetries section."
supersedes:
  - "CLAUDE.md rebuild-era-minimal-marker (pre-rebuild; fingerprint fd19b4b7d8adba5d344b78d50d3ed3631d5185f6cfbe742122fae8752e19b4c6). Prior content was a minimal in-place marker maintained in-band during Steps 0–8; §A–§M structure in this v2.0 replaces it wholesale."
consumers:
  - Every Claude session at session-open (mandatory-reading item #1 of its own list)
  - "platform/scripts/governance/mirror_enforcer.py rule_mp1 (MP.1 structural-parity enforcement)"
  - ".geminirules (adapted-parity mirror per ND.1 / MP.1)"
  - "Step 10 (SESSION_LOG schema + CURRENT_STATE) — the §F currently-executing marker is the state-surface Step 10 upgrades to CURRENT_STATE_v1_0.md"
changelog:
  - v2.0 (2026-04-24, Step 9 of the Step 0→15 governance rebuild):
      Full rebuild against the Step 9 brief. Section schema §A–§M installed per brief §3. Resolves
      GA.9 (LIFE_EVENT_LOG surfaced as concurrent workstream), GA.10 (GOVERNANCE_STACK surfaced
      via CANONICAL_ARTIFACTS import), GA.11 (supporting registries surfaced via import),
      GA.19 (§F currently-executing marker installed), GA.1/GA.2 (canonical paths imported
      from CANONICAL_ARTIFACTS_v1_0.md rather than duplicated inline). .geminirules mirror
      propagated in the same session per MP.1. BOOTSTRAP_HANDOFF reference retained as legacy
      orientation (its own pointer to v2.1 is known-deferred drift WARN.4 / WARN.6).
  - v2.0 (amended in-place, 2026-04-24, Step 15 — GOVERNANCE_BASELINE_CLOSE):
      Rebuild-era banner removed from §F. §C item #8 rebuild-era qualifier replaced with
      steady-state CURRENT_STATE pointer. §D snapshot STEP_LEDGER row status updated to
      GOVERNANCE_CLOSED. §L rebuild-step-improvisation bullet removed (rebuild closed).
      PHASE_B_PLAN §C item #5 paused-note removed. §F narrative replaced with steady-state
      position. Footer updated. .geminirules MP.1 mirror propagated in the same session.
---

# MARSYS-JIS — Master Instructions for Claude

## §A — Project mission

Build an LLM-operated Jyotish instrument that, for the native (Abhisek Mohanty), (1) reads the chart with acharya-grade depth; (2) surfaces patterns and contradictions across layers and systems that no individual astrologer could hold in working memory; (3) makes time-indexed, probabilistic, calibrated predictions testable against lived reality and correctable from outcomes. Then extend the method beyond this native so the instrument becomes a research tool for astrology as a discipline. This goal is bounded by the Ethical Framework in `MACRO_PLAN_v2_0.md §Ethical Framework`: the instrument produces probabilistic, calibrated, auditable outputs for consenting audiences under stated disclosure tiers; it is not a fortune-telling product.

## §B — Subject

Abhisek Mohanty, born 1984-02-05, 10:43 IST, Bhubaneswar, Odisha, India.

Canonical L1 chart data: `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` (authoritative; `canonical_id: FORENSIC` in CANONICAL_ARTIFACTS §1). No session re-derives the foundational chart; the v6.0 file is retained as archival only.

## §C — Mandatory reading (per session)

Every Claude session, at open, reads the following in order before any substantive work. Items are named by canonical_id; versioned paths live in CANONICAL_ARTIFACTS §1 and resolve from there — this list does not duplicate version strings.

0. `CLAUDECODE_BRIEF.md` (project root) — **Claude Code sessions only; check first.** If this file exists at the project root and its `status` field is not `COMPLETE`, read it before items 1–11 below. It is the Cowork-authored governing scope for this specific execution session: active phase, file scope, acceptance criteria, and hard constraints. Its `may_touch` / `must_not_touch` declarations override all other scope guidance for the duration of the session. When the session closes and all acceptance criteria are met, set `status: COMPLETE` in this file's frontmatter. If `status` is already `COMPLETE`, or the file does not exist, skip this item and proceed with item 1 normally.

1. `CLAUDE.md` (this file — self-reference; the session's own orientation surface).
2. `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — **new single source of truth** for the canonical-path + artifact catalog (Phase 1B cutover 2026-04-27). Replaces the dual `FILE_REGISTRY` + `CANONICAL_ARTIFACTS` registries. Mirror pairs declared in `00_ARCHITECTURE/manifest_overrides.yaml` `mirror_pairs:` section. `CANONICAL_ARTIFACTS_v1_0.md` retained in place as SUPERSEDED historical record — read it for audit trail only; governance tooling now reads from the manifest. `drift_detector.py`, `schema_validator.py`, `mirror_enforcer.py` default to manifest mode (`*_USE_MANIFEST=true`).
3. `00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md` (canonical_id `PROJECT_ARCHITECTURE`) — governing blueprint. Re-read relevant sections as needed.
4. `00_ARCHITECTURE/MACRO_PLAN_v2_0.md` (canonical_id `MACRO_PLAN`) — ten-macro-phase strategic arc M1–M10, Learning Layer substrate, System Integrity Substrate per ND.1, Ethical Framework, External Dependency Graph, per-phase schema, Meta-Governance, Multi-Agent Collaboration, Post-M10 Framing. Orientation only — do not pre-build for phases later than the current one.
5. **Active phase plan** — `PHASE_M5_PLAN_v1_0.md` (TBD; to be authored at M5-S1 open). Prior plans all SUPERSEDED-AS-COMPLETE: `PHASE_B_PLAN_v1_0.md` (M2, closed 2026-05-01), `PHASE_M3_PLAN_v1_0.md` (M3, closed 2026-05-01), `PHASE_M4_PLAN_v1_0.md` (M4, closed 2026-05-02). Consult `CURRENT_STATE_v1_0.md §2` for the active sub-phase at session open.
6. `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` (canonical_id `GOVERNANCE_INTEGRITY_PROTOCOL`, status CURRENT since Step 8 close) — governs session-open/close, drift/schema/mirror enforcement, disagreement protocol, meta-rules. Re-read axes §C.1–§C.6 + §K disagreement protocol at session open.
7. `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md` + `00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md` — the handshake + close-checklist schemas the session emits. See §G + §H below.
8. `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` (canonical_id `CURRENT_STATE`, LIVE) — the authoritative "you are here" state pointer. Answers in one read: which macro-phase is active, which phase-plan sub-phase is in flight, which session last closed, and what the next session is committed to. Updated at every session close. Authoritative since Step 15 close (2026-04-24); STEP_LEDGER retired per §F. `STEP_LEDGER_v1_0.md` is retained as a historical record (status `GOVERNANCE_CLOSED`) — read it only for audit trail, not for current state.
9. `00_ARCHITECTURE/GROUNDING_AUDIT_v1_0.md` — baseline facts as of 2026-04-23, the CLOSED audit that seeded the Step 0→15 rebuild. Read once per fresh-context session; findings `GA.N` are cited throughout downstream artifacts.
10. `00_ARCHITECTURE/NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` — open directives (ND.N) that bind to the session's step. At v2.0 publication, ND.1 (Mirror Discipline) is `addressed` — no open directive.
11. `00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md` — governance-layer hygiene rule set (CURRENT since Step 12 close, 2026-04-24). §A–§N: archival retain-in-place, predecessor cleanup, scope-boundary enforcement, SESSION_LOG completeness, staleness register, CI cadence + exit-code-3 known_residuals whitelist, red-team cadence + learning_layer_stub validator class, quarterly governance pass, Macro Plan review triggers, implementation-actions index, residual-disposition record, finding-coverage audit. Governs every session-close checklist from Step 12 forward.
12. `00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md` (canonical_id `PORTAL_REDESIGN_TRACKER`, LIVING) + `00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md` (canonical_id `PORTAL_REDESIGN_VISION`, CURRENT) — **Portal Redesign workstream only.** Read when any redesign session (R0–R7) opens. TRACKER §2 canonical state block answers: which R-phase is in flight, which phases are parallel-safe, what the trace-fix status is. Skip this item if the session is not a portal redesign session.

*Item 11 previously named `MARSYS_JIS_BOOTSTRAP_HANDOFF.md` — retired at Step 12 close 2026-04-24 per native decision (WARN.4 / WARN.6 resolution). Every load-bearing claim it carried is now in items 1–10 above + this item 11. Audit trail retained at root-level path.*

## §D — Canonical artifacts (import)

Canonical artifact versions and paths are defined in `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md`. Do not duplicate declarations here. Any disagreement between this file and CANONICAL_ARTIFACTS resolves in favor of CANONICAL_ARTIFACTS.

**Cached snapshot — informational only; authoritative is CANONICAL_ARTIFACTS §1.**

- Snapshot timestamp: 2026-04-24 (Step 9 close moment).
- CANONICAL_ARTIFACTS fingerprint at snapshot: `be76cc7aa84f3c1e16d7745bd2e3ecc809fe10d55a079780fde12dc5d954dc88` (sha256 at read time during Step 9 session-open; rotates on every touch).

| canonical_id | path | version | status |
|---|---|---|---|
| FORENSIC | `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` | 8.0 | CURRENT |
| LEL | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` | 1.2 | CURRENT |
| MSR | `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` | 3.0 (499 signals) | CURRENT |
| UCN | `025_HOLISTIC_SYNTHESIS/UCN_v4_0.md` | 4.1 (internal) | CURRENT |
| CDLM | `025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md` | 1.2 (internal) | CURRENT |
| RM | `025_HOLISTIC_SYNTHESIS/RM_v2_0.md` | 2.1 (internal) | CURRENT |
| CGM | `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` | 9.0 | CURRENT |
| PROJECT_ARCHITECTURE | `00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md` | 2.2 | CURRENT |
| MACRO_PLAN | `00_ARCHITECTURE/MACRO_PLAN_v2_0.md` | 2.0 | CURRENT |
| PHASE_B_PLAN | `00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md` | 1.0.2 | CURRENT |
| FILE_REGISTRY | `00_ARCHITECTURE/FILE_REGISTRY_v1_14.md` | 1.14 | SUPERSEDED (2026-04-27 — see CAPABILITY_MANIFEST.json) |
| GOVERNANCE_STACK | `00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md` | 1.0 (amended in-place) | CURRENT |
| STEP_LEDGER | `00_ARCHITECTURE/STEP_LEDGER_v1_0.md` | 1.0 | GOVERNANCE_CLOSED (2026-04-24) |
| SESSION_LOG | `00_ARCHITECTURE/SESSION_LOG.md` | rolling | LIVE |
| NATIVE_DIRECTIVES | `00_ARCHITECTURE/NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` | 1.0 | LIVING |
| CONVERSATION_NAMING_CONVENTION | `00_ARCHITECTURE/CONVERSATION_NAMING_CONVENTION_v1_0.md` | 1.4 | LIVING |
| GOVERNANCE_INTEGRITY_PROTOCOL | `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` | 1.0 | CURRENT |
| CANONICAL_ARTIFACTS | `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md` | 1.0 | CURRENT |
| SESSION_OPEN_TEMPLATE | `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md` | 1.0 | CURRENT |
| SESSION_CLOSE_TEMPLATE | `00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md` | 1.0 | CURRENT |
| DISAGREEMENT_REGISTER | `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md` | 1.0 | LIVING |
| CLAUDE | `CLAUDE.md` | 2.0 | CURRENT |
| GEMINIRULES | `.geminirules` | re-authored-STEP_7 (fingerprint rotates at Step 9 close for MP.1 mirror) | LIVE |
| PROJECT_STATE | `.gemini/project_state.md` | re-authored-STEP_7 (fingerprint rotates at Step 9 close for MP.2 mirror) | LIVE |

Any path in this snapshot that conflicts with `CANONICAL_ARTIFACTS_v1_0.md §1` is wrong here, not there. `drift_detector.py` enforces this via the canonical-path cross-check (protocol §H.3).

## §E — Concurrent workstreams

Three workstreams run concurrently with (not inside) the currently-active macro-phase and must not be forgotten when the rebuild banner is lifted:

- **Life Event Log (LEL) v1.2** — canonical_id `LEL`, path `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`, 36 events + 5 period summaries + 6 chronic patterns, Swiss-Ephemeris-populated `chart_states`, confidence 0.89. MACRO_PLAN_v2_0 names LEL as an M4 prerequisite with cadence **"Start immediately; do not defer."** Surfacing this workstream in §E closes GA.9 (previously unreferenced in CLAUDE.md). Ongoing maintenance: add new events as they happen; re-close via a minor version bump with Swiss-Ephemeris regeneration when events are added.
- **Prospective Prediction Logging** — per `MACRO_PLAN_v2_0.md §Cross-cutting workstreams` + Learning Layer discipline rule #4 "held-out prospective data is sacrosanct; the model never sees outcome before prediction." Every time-indexed prediction a session emits is logged with its confidence, horizon, and falsifier before the outcome is observed. Scaffold/home lands at Step 11 (LEARNING_LAYER scaffold decision). Sessions that emit time-indexed predictions before Step 11 closes must still log them; the interim logging surface is `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` prediction subsection, flagged for migration when `06_LEARNING_LAYER/` is scaffolded.
- **Phase O — LLM Cost & Usage Observatory** — canonical_id `OBSERVATORY_PLAN_v1_0`, path `00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md`, mirror pair MP.9. **STATUS: COMPLETE (2026-05-04).** All 30 sessions (O.0–O.4) closed. OBSERVATORY_PLAN sealed at v2.0.0. Branch `feature/phase-o-observatory` merged to main and deleted; worktree `/Users/Dev/Vibe-Coding/Apps/Ustad/` retired. Observatory live in production at revision `amjis-web-00044-sn5` behind `MARSYS_FLAG_OBSERVATORY_ENABLED=true`. Remaining items: AC.3 (live telemetry verification), AC.4 (7 nightly reconciliation runs — 7-day clock from 2026-05-04), AC.6 (budget alert end-to-end test). Phase-O+1 tracked items in `OBSERVATORY_PLAN_v1_0.md §14`. **Isolation rule retired** — no active Ustad worktree; Madhav sessions may touch observatory files on main normally.

## §F — Current execution position (You are here)

**Authoritative source of truth: `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` (LIVE; authoritative since Step 15 close 2026-04-24).** Read §2 of that file for the canonical state block. The governance rebuild (Step 0 → Step 15) is **closed** — `GOVERNANCE_BASELINE_v1_0.md` is the sealing artifact. `STEP_LEDGER_v1_0.md` is retired (status `GOVERNANCE_CLOSED`); consult it only for historical audit trail.

At the close of M4-D-S1 (2026-05-02) — M4 MACRO-PHASE CLOSED; M4→M5 TRANSITION:

- **Active macro-phase:** M5 — INCOMING. M2 (Corpus Activation), M3 (Temporal Animation / Discovery Layer), and M4 (Calibration + LEL Ground-Truth Spine) are all CLOSED. Sealing artifacts: `00_ARCHITECTURE/M2_CLOSE_v1_0.md`, `00_ARCHITECTURE/M3_CLOSE_v1_0.md`, `06_LEARNING_LAYER/M4_CLOSE_v1_0.md`.
- **Active phase-plan:** `PHASE_M5_PLAN_v1_0.md` — TBD (to be authored at M5-S1 open). Prior plans SUPERSEDED-AS-COMPLETE: `PHASE_B_PLAN_v1_0.md` (M2), `PHASE_M3_PLAN_v1_0.md` (M3), `PHASE_M4_PLAN_v1_0.md` (M4).
- **Last session:** M4-D-S1 (2026-05-02) — M4 macro-phase close. IS.8(b) red-team PASS 5/5. NAP.M4.7 APPROVED.
- **Next session:** M5-S1 — open M5 macro-phase; read `MACRO_PLAN_v2_0.md §M5` scope; draft `PHASE_M5_PLAN_v1_0.md`.
- **Governance step:** Step 0 → Step 15 rebuild `GOVERNANCE_CLOSED`. Steady-state: quarterly governance pass per `ONGOING_HYGIENE_POLICIES §H`; next due 2026-07-24.
- **ND status:** ND.1 (Mirror Discipline) `addressed` 2026-04-24 at Step 7 close. No open directive.
- **red_team_counter:** 0 (reset at M4 macro-phase-close IS.8(b) discharge).
- **Concurrent workstreams:** Phase O Observatory COMPLETE (2026-05-03; branch merged to main; live at amjis-web-00044-sn5 behind `MARSYS_FLAG_OBSERVATORY_ENABLED=true`). BHISMA Wave 2 Lever 2 CLOSED (2026-05-04; `LLM_FIRST_PLANNER_ENABLED=true` commit fa75e1a; AC.W2.3 DEFERRED pending Lever 3 NAP). **Phase 11B Pipeline Cutover Stage 2 COMPLETE (2026-05-11)** — legacy code path deleted from route.ts, `consume-tools.ts` deleted, `pipelineEnabled` prop chain removed from ConsumeChat + consume page wrappers, `NEW_QUERY_PIPELINE_ENABLED` flag retired from `feature_flags.ts`. New pipeline is the only pipeline. Rollback path is `git revert`, not flag flip.
- **Active feature flags:** `AUDIT_ENABLED=true`, `LLM_FIRST_PLANNER_ENABLED=true`, `MARSYS_FLAG_OBSERVATORY_ENABLED=true`, all `DISCOVERY_*_ENABLED=true`. (`NEW_QUERY_PIPELINE_ENABLED` removed Phase 11B 2026-05-11.)

## §G — Session-open handshake (reference)

Every session begins by emitting the SESSION_OPEN artifact per `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md`. The handshake is validated by `platform/scripts/governance/schema_validator.py` (or equivalent in-session check) before any substantive tool call. A session whose handshake fails validation halts and reports to the native; it does not proceed.

Per `CONVERSATION_NAMING_CONVENTION_v1_0.md §4`, the session proposes its Cowork thread name at the top of the first substantive response; that proposal must match the handshake's `cowork_thread_name` field.

## §H — Session-close checklist (reference)

Every session ends by emitting the SESSION_CLOSE artifact per `00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md`. The checklist is validated by `schema_validator.py` as its last action; only after validation passes does the `SESSION_LOG.md` append happen atomically (session_open block + body + session_close block → one entry). A session whose close-checklist fails validation does not claim close.

## §I — Operating principles (summarized)

**File placement rule (enforced since 2026-05-04).** Before creating or saving any file, consult `00_ARCHITECTURE/ROOT_FILE_POLICY.md`. Nothing lands at the project root unless it is in ROOT_FILE_POLICY §2's exhaustive list. Every other file type has a designated folder. Use the §4 decision tree when in doubt.


The full principle list is `PROJECT_ARCHITECTURE_v2_2.md §B — Architectural Principles (Non-Negotiable)` (B.1–B.12, preserved verbatim from v2.1). Cross-cutting substrates are in `MACRO_PLAN_v2_0.md §Learning Layer` and `§System Integrity Substrate`. The five most-violated principles, surfaced here as inline reminders (seeded from GROUNDING_AUDIT_v1_0.md finding patterns):

- **B.1 — Facts/Interpretation separation.** Facts live at L1; derivations at the L1/L2.5 boundary with explicit ledger; interpretations at L2.5+ only. Mixing layers destroys auditability. *(L2 Analytical Layer archived Phase 14F 2026-04-28; L2.5 is the first active synthesis layer.)*
- **B.3 — Derivation-ledger mandate.** Every L2.5+ claim carries a `DERIVATION_LEDGER` entry listing the specific L1 fact IDs it consumes. No claim rests on "as is known classically" or "per tradition" without a source.
- **B.8 — Versioning discipline.** Every canonical artifact carries frontmatter `version`, `status`, and a changelog. Registries must not disagree (GA.1 failure mode). Silent file mutation fails `drift_detector.py` and `schema_validator.py`.
- **B.10 — No fabricated computation.** If a computation requires a specialist tool (Jagannatha Hora, Parashara's Light, Shri Jyoti Star, Swiss Ephemeris) and the value is not already in L1, the session marks it `[EXTERNAL_COMPUTATION_REQUIRED]` with exact specification of what to compute. Claude never invents numerical chart values.
- **B.11 — Whole-Chart-Read discipline.** Every query routes through L2.5 Holistic Synthesis first (MSR + UCN + CDLM + CGM + RM), surfaces cross-domain signals via the Cross-Domain Linkage Matrix, then produces its domain-specific answer. A query-answer that skips L2.5 consultation is a procedural violation equivalent to a red-team finding.

Beyond the architectural principles, two substrate-layer rules apply at every session:

- **Mirror Discipline (MP.1 + ND.1).** Any change on the Claude-side of a mirror pair triggers a same-session adapted-parity update on the Gemini-side, and symmetrically. `mirror_enforcer.py` exits non-zero on desync; silent overwriting is forbidden per `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §K.3 step 3`.
- **Scope declaration (protocol §F; GA.20 closure).** Every session declares `may_touch` and `must_not_touch` globs at session open. An empty `must_not_touch` fails the handshake.

## §J — Quality standard

Acharya-grade. An independent senior Jyotish acharya reviewing this corpus should reach one of: "this is my own level", "this is above my own level", or "this reveals things I wouldn't have seen on first pass". Nothing less.

## §K — Collaboration with Gemini

Claude works alongside Gemini on this project (Gemini's primary role is the L4 Discovery Layer per `PROJECT_ARCHITECTURE_v2_2.md §D.11`). Governance of the collaboration is specified in:

- `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §K` — multi-agent disagreement protocol (five classes including `DIS.class.mirror_desync`; arbitration protocol §K.3 with forbidden-silent-overwrite rule).
- `CANONICAL_ARTIFACTS_v1_0.md §2` — machine-readable mirror-pair inventory (MP.1–MP.8) with per-pair `enforcement_rule` + `known_asymmetries`.
- `PROJECT_ARCHITECTURE_v2_2.md §D.11` — architecture-layer Multi-Agent Collaboration workstream.
- `NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md §1 ND.1` — Mirror Discipline directive (status: addressed 2026-04-24).

**Operational rule.** Any Claude-side governance change that has a Gemini-side counterpart (MP.1–MP.5, MP.8) is mirrored in the same session on the Gemini side to adapted parity. Same in reverse. The mirror is semantic, not byte-identical; asymmetries are preserved and declared per pair, not synthesized away. `.geminirules` and `.gemini/project_state.md` carry the Gemini-side surfaces; cross-propagation is recorded in the session's close-checklist `mirror_updates_propagated` block. Declared-Claude-only pairs (MP.6 GOVERNANCE_STACK, MP.7 SESSION_LOG) require no Gemini-side update.

## §L — Do not

- Produce generic astrology.
- Collapse layer separation (facts into interpretations or vice versa).
- Skip the Whole-Chart-Read Protocol (B.11 / PROJECT_ARCHITECTURE §H.4).
- Abandon versioning discipline (every artifact carries version metadata + changelog; registries must not disagree).
- Change architecture without native's explicit approval + version bump.
- Duplicate canonical-artifact paths or versions outside `CANONICAL_ARTIFACTS_v1_0.md`. Every other governance surface cites by reference.
- Silently overwrite a mirror-pair counterpart. Desync opens a `DIS.class.mirror_desync` entry in `DISAGREEMENT_REGISTER_v1_0.md` per protocol §K.3 step 3.
- Pre-build infrastructure for macro-phases later than the currently-active one (MACRO_PLAN §Scope Boundary).
- Claim a session is closed without emitting and validating the `session_close` checklist. Close without checklist = not a well-formed session.

## §M — Cadence

Daily sessions. Closed-artifact-per-session discipline — one phase or one step at a time, each producing a discrete, versioned, frontmatter-bearing artifact. Red-team passes at three cadences per MACRO_PLAN v2.0 §IS.8: (a) every third session by default; (b) every macro-phase close before the SESSION_LOG seal; (c) every 12 months for MP itself regardless of phase state. A macro-phase does not close without its red-team. Session-open handshake (§G) validates the cadence obligation via the `red_team_due` field; session-close checklist (§H) validates the obligation was discharged if due.

---

*End of CLAUDE.md v2.1 (amended 2026-05-11 — Phase 11B Pipeline Cutover Stage 2 close: §F updated to remove NEW_QUERY_PIPELINE_ENABLED flag and record legacy-path deletion; new pipeline is the only pipeline). Prior: v2.0 (2026-05-04). Governance rebuild closed; M4 CLOSED 2026-05-02; M5 active.*
