---
artifact: CLAUDE.md
version: "6.6"
status: CURRENT
role: >
  Root governance surface. Master orientation document for every Claude session on the MARSYS-JIS
  project. Every Claude session opens by reading this file first. Holds DURABLE orientation only —
  live state lives in CURRENT_STATE_v1_0.md, never in this file.
produced_during: STEP_9_CLAUDE_MD_REBUILD (Step 0 → Step 15 governance rebuild)
produced_on: 2026-04-24
authoritative_side: claude
mirror_obligations_retired: "2026-05-27 — Gemini mirror discipline retired per native directive. See §K close-out."
supersedes:
  - "CLAUDE.md v5.1 (2026-06-09 — realigned to L1-done/L2-next reality at v6.0)"
changelog:
  - v6.4 (2026-07-19, COWORK-RETRIEVAL-STRATEGY):
      §I B.11 amended with the RS-4 proportionality carve-out (native-authorized 2026-07-19):
      B.11 scoped to interpretive queries; pinpointed factual lookups (depth: retrieval) satisfy
      it via frame check (chart_header + session pin) + escalation valve (one-line flag + drill
      pointer when the fact touches an active contradiction, firing yoga, or open prediction
      window). Mirrors in-place amendments to PROJECT_ARCHITECTURE_v2_2.md §B.11/§H.4. Doctrine
      source: RETRIEVAL_STRATEGY_v1_0.md §3.6. §D snapshot CLAUDE row corrected 6.2 → 6.4.
  - v6.3 (2026-07-15, DOCTRINE-WAVES-D1.5B-B7):
      New §N.6 Serving Density Principle — codifies the density/confidence-layering discipline
      the `density_contract` field (registry/types.ts) and the response-budget `hardFloor`
      mechanism (platform-mcp/src/lib/response_budget.ts) already embody in production
      (judgment_query, ganita_yogas_get catalog-vs-confirmed handling). Frontmatter/footer
      version drift corrected (frontmatter had stayed "6.0" since the v6.0 unification while
      the footer advanced through v6.1/v6.2 — both now read 6.3). Full text: §N.6 body + footer.
  - v6.0 (2026-06-12, CLAUDE-MD-REALIGNMENT):
      Structural realignment to L1-done/L2-next reality. §F collapsed to CURRENT_STATE pointer
      (M5/M4 you-are-here specifics deleted). §E replaced: 15 completed arcs → layer-reality
      block (L0✓/L1✓/L2-next/L3–L5 pending) + frozen orchestrator note + open items only. §D
      trimmed to currently-canonical artifacts (retired STEP_LEDGER, old phase plans, FILE_REGISTRY
      superseded rows dropped). Changelog moved to 00_ARCHITECTURE/CLAUDE_MD_CHANGELOG.md (full
      history preserved verbatim). §B fixed: chart_facts is the canonical L1 source; FORENSIC v8.0
      markdown archived; forensic_render.ts RETIRED; 7 FORENSIC birth anchors named. Asset-id
      underscore convention + layer-name lexicon added. §C updated: item 5 → active campaign =
      L2 Bodha per CURRENT_STATE + L2_BODHA_CAMPAIGN_HANDOFF; item 13 → frozen orchestrator
      (ORCHESTRATOR_CONVERGENCE_CLOSE) with correct chart-build note; new §C items 14–16 add L1
      closure, L2 handoff, and orchestrator-close docs. New §N standards block: orchestrator
      contract, idempotency-per-layer, floors/tier/determinism/JH, L1-authority-over-L2.5.
      Frontmatter version corrected (was "4.8" in frontmatter vs "5.1" in body footer — unified to 6.0).
  - v5.1 (2026-06-09, GANITA-NAMING-RECONCILIATION):
      Gaṇita naming reconciliation COMPLETE: migration 195 relabels 8 ganita.* asset_registry ids → ga_*;
      GANITA_NAMING_RECONCILIATION added to §D snapshot.
  - v5.0 (2026-06-02, BUILD-GUARANTOR-SWARM-CHARTER):
      Build-Workflow Guarantor Swarm Charter authored and added to §C + §D.
  - "Prior history: 00_ARCHITECTURE/CLAUDE_MD_CHANGELOG.md (full verbatim record from v2.0)."
---

# MARSYS-JIS — Master Instructions for Claude

## §A — Project mission

Build an LLM-operated Jyotish instrument that, for the native (Abhisek Mohanty), (1) reads the chart with acharya-grade depth; (2) surfaces patterns and contradictions across layers and systems that no individual astrologer could hold in working memory; (3) makes time-indexed, probabilistic, calibrated predictions testable against lived reality and correctable from outcomes. Then extend the method beyond this native so the instrument becomes a research tool for astrology as a discipline. This goal is bounded by the Ethical Framework in `MACRO_PLAN_v2_0.md §Ethical Framework`: the instrument produces probabilistic, calibrated, auditable outputs for consenting audiences under stated disclosure tiers; it is not a fortune-telling product.

## §B — Subject

Abhisek Mohanty, born 1984-02-05, 10:43 IST, Bhubaneswar, Odisha, India.

Canonical L1 chart facts: the **`chart_facts` DB table** (built by the L1 `ga_*` writers via the orchestrator). The FORENSIC v8.0 markdown (`01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md`) was deleted in PR #187 Legacy Teardown; a cold archived benchmark copy exists at `99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md` — it is not the live source. `forensic_render.ts` (GA2) was RETIRED (L1 build superseded it; retrieval + panchanga service do its job). No session re-derives the foundational chart.

**7 FORENSIC birth anchors** (hard facts; FORENSIC 7/7 PASS confirmed by L1 production build):
Sun = Capricorn · Moon = Purva Bhadrapada · Lagna = Aries (all 5 ayanamshas) · Tithi = Shukla Tritiya · Vara = Ravivara · Yoga = Shiva · Karana = Garaja.

**Canonical chart_id:** `482012f1-710e-4a25-994a-93821f5871aa`. `362f9f17-…` is a dead phantom — never write it.

## §C — Mandatory reading (per session)

Every Claude session, at open, reads the following in order before any substantive work. Items are named by canonical_id; versioned paths live in CANONICAL_ARTIFACTS §1 and resolve from there.

0. `CLAUDECODE_BRIEF.md` (project root) — **Claude Code sessions only; check first.** If this file exists at the project root and its `status` field is not `COMPLETE`, read it before items 1–16 below. It is the Cowork-authored governing scope for this specific execution session: active phase, file scope, acceptance criteria, and hard constraints. Its `may_touch` / `must_not_touch` declarations override all other scope guidance for the duration of the session. When the session closes and all acceptance criteria are met, set `status: COMPLETE` in this file's frontmatter. If `status` is already `COMPLETE`, or the file does not exist, skip this item and proceed with item 1 normally.

1. `CLAUDE.md` (this file — self-reference; the session's own orientation surface).
2. `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — **new single source of truth** for the canonical-path + artifact catalog (Phase 1B cutover 2026-04-27). Replaces the dual `FILE_REGISTRY` + `CANONICAL_ARTIFACTS` registries. `CANONICAL_ARTIFACTS_v1_0.md` retained in place as SUPERSEDED historical record — read it for audit trail only; governance tooling now reads from the manifest. `drift_detector.py` and `schema_validator.py` default to manifest mode (`*_USE_MANIFEST=true`).
3. `00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md` (canonical_id `PROJECT_ARCHITECTURE`) — governing blueprint. Re-read relevant sections as needed.
4. `00_ARCHITECTURE/MACRO_PLAN_v2_0.md` (canonical_id `MACRO_PLAN`) — ten-macro-phase strategic arc M1–M10, Learning Layer substrate, System Integrity Substrate per ND.1, Ethical Framework, External Dependency Graph, per-phase schema, Meta-Governance, Multi-Agent Collaboration, Post-M10 Framing. Orientation only — do not pre-build for phases later than the current one.
5. **Active campaign** — consult `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2 for which layer campaign is active. Currently **L2 Bodha** — read `00_ARCHITECTURE/L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md` (canonical_id `L2_BODHA_CAMPAIGN_HANDOFF`) for the full L2 context: nomenclature, standards, FROZEN orchestrator contract, L1→L2 data interface, 8-asset Bodha DAG, per-asset specs, and hard-won traps. Prior phase plans all SUPERSEDED-AS-COMPLETE (`PHASE_B_PLAN_v1_0.md` M2, `PHASE_M3_PLAN_v1_0.md` M3, `PHASE_M4_PLAN_v1_0.md` M4, `PHASE_M5_PLAN_v1_0.md` M5-A).
6. `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` (canonical_id `GOVERNANCE_INTEGRITY_PROTOCOL`, status CURRENT since Step 8 close) — governs session-open/close, drift/schema enforcement, disagreement protocol, meta-rules. Re-read axes §C.1–§C.6 + §K disagreement protocol at session open.
7. `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md` + `00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md` — the handshake + close-checklist schemas the session emits. See §G + §H below.
8. `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` (canonical_id `CURRENT_STATE`, LIVE) — the authoritative "you are here" state pointer. Answers in one read: which layer campaign is active, which sub-phase is in flight, which session last closed, and what the next session is committed to. Updated at every session close. Authoritative since Step 15 close (2026-04-24); STEP_LEDGER retired per §F. `STEP_LEDGER_v1_0.md` is retained as a historical record (status `GOVERNANCE_CLOSED`) — read it only for audit trail, not for current state.
9. `00_ARCHITECTURE/GROUNDING_AUDIT_v1_0.md` — baseline facts as of 2026-04-23, the CLOSED audit that seeded the Step 0→15 rebuild. Read once per fresh-context session; findings `GA.N` are cited throughout downstream artifacts.
10. `00_ARCHITECTURE/NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` — open directives (ND.N) that bind to the session's step. ND.1 (Mirror Discipline) is `RETIRED` (2026-05-27, native decision) — no open directive.
11. `00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md` — governance-layer hygiene rule set (CURRENT since Step 12 close, 2026-04-24). §A–§N: archival retain-in-place, predecessor cleanup, scope-boundary enforcement, SESSION_LOG completeness, staleness register, CI cadence + exit-code-3 known_residuals whitelist, red-team cadence + learning_layer_stub validator class, quarterly governance pass, Macro Plan review triggers, implementation-actions index, residual-disposition record, finding-coverage audit. Governs every session-close checklist from Step 12 forward.
12. `00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md` (canonical_id `PORTAL_REDESIGN_TRACKER`) + `00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md` — **Portal Redesign workstream only (STATUS: COMPLETE).** Read if auditing the redesign history. Skip for all other sessions.
13. `00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` (canonical_id `ORCHESTRATOR_CONVERGENCE_CLOSE`, CURRENT) — **Chart-build workflow sessions + every new-layer session (L2+).** The sealed record of the FROZEN orchestrator contract: `WriterBase` conformance (`@register`, `run(ctx)` / `plan_substeps + run_substep`, `ctx.db_conn` never committed by writer, no `_telemetry`, `WriterResult`); Phase 5 E2E runbook; L2-readiness conformance checklist (§5). Also read `00_ARCHITECTURE/BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md` (canonical_id `BUILD_GUARANTOR_SWARM_CHARTER`) for the 12-role agentic swarm charter. Skip both if the session does not touch the chart-build workflow.
14. `00_ARCHITECTURE/L1_GANITA_CLOSURE_v1_0.md` (canonical_id `L1_GANITA_CLOSURE`, CURRENT) — **L1 layer sessions and any L2 onboarding session.** The definitive L1 sealed record: 9 data assets + ga_chart_service, canonical row counts (chart_facts=27,554; chart_dashas=536,471; chart_divisionals=21,635; total Gaṇita header=585,710), DAG edges, Phase E status (operator E2E gated on Abhinandan Mohanty `1c826d5a`), the L2 onboarding contract. Read at L2 open; skip for unrelated sessions.
15. `00_ARCHITECTURE/L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md` (canonical_id `L2_BODHA_CAMPAIGN_HANDOFF`, CURRENT) — same as item 5 above; listed here for cross-reference completeness.
16. `00_ARCHITECTURE/MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md` + `00_ARCHITECTURE/MSR_UCN_CONTAMINATION_AUDIT_v1_0.md` — **L2 Bodha sessions only.** The two documented traps that Bodha must not repeat (computed-value authority inversion; interpretation contamination of the deterministic base). Read at L2 open.

## §D — Canonical artifacts (import)

Canonical artifact versions and paths are defined in `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md`. Do not duplicate declarations here. Any disagreement between this file and CANONICAL_ARTIFACTS resolves in favor of CANONICAL_ARTIFACTS. Governance tooling reads `CAPABILITY_MANIFEST.json` (authoritative since 2026-04-27).

**Cached snapshot — informational only; authoritative is CAPABILITY_MANIFEST.json / CANONICAL_ARTIFACTS §1.**

| canonical_id | path | version | status |
|---|---|---|---|
| FORENSIC | `99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md` (cold archived benchmark; live canonical source = `chart_facts` table built by L1 `ga_*` writers; `forensic_render.ts` RETIRED) | 8.0 | ARCHIVED |
| LEL | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` | 1.7 | CURRENT |
| MSR | `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` | 5.0 (573 signals) | CURRENT |
| UCN | `025_HOLISTIC_SYNTHESIS/UCN_v4_0.md` | 4.1 | CURRENT (UCN→UCD retirement in L2 Bodha build — see L2 handoff §1) |
| CDLM | `025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md` | 1.3 | CURRENT |
| RM | `025_HOLISTIC_SYNTHESIS/RM_v2_0.md` | 2.2 | CURRENT |
| CGM | `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` | 9.0 | CURRENT |
| PROJECT_ARCHITECTURE | `00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md` | 2.2 | CURRENT |
| MACRO_PLAN | `00_ARCHITECTURE/MACRO_PLAN_v2_0.md` | 2.0 | CURRENT |
| CURRENT_STATE | `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` | rolling | LIVE |
| SESSION_LOG | `00_ARCHITECTURE/SESSION_LOG.md` | rolling | LIVE |
| GOVERNANCE_INTEGRITY_PROTOCOL | `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` | 1.0 | CURRENT |
| CANONICAL_ARTIFACTS | `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md` | 1.0 | CURRENT (SUPERSEDED by CAPABILITY_MANIFEST.json for tooling) |
| SESSION_OPEN_TEMPLATE | `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md` | 1.0 | CURRENT |
| SESSION_CLOSE_TEMPLATE | `00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md` | 1.0 | CURRENT |
| DISAGREEMENT_REGISTER | `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md` | 1.0 | LIVING |
| NATIVE_DIRECTIVES | `00_ARCHITECTURE/NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` | 1.0 | LIVING |
| CONVERSATION_NAMING_CONVENTION | `00_ARCHITECTURE/CONVERSATION_NAMING_CONVENTION_v1_0.md` | 1.4 | LIVING |
| GROUNDING_AUDIT | `00_ARCHITECTURE/GROUNDING_AUDIT_v1_0.md` | 1.0 | CLOSED |
| ONGOING_HYGIENE_POLICIES | `00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md` | 1.0 | CURRENT |
| BUILD_GUARANTOR_SWARM_CHARTER | `00_ARCHITECTURE/BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md` | 1.0 | CURRENT |
| ORCHESTRATOR_CONVERGENCE_CLOSE | `00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` | 1.0 | CURRENT |
| L1_GANITA_CLOSURE | `00_ARCHITECTURE/L1_GANITA_CLOSURE_v1_0.md` | 1.0 | CURRENT |
| L2_BODHA_CAMPAIGN_HANDOFF | `00_ARCHITECTURE/L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md` | 1.0 | CURRENT |
| CLAUDE | `CLAUDE.md` | 6.5 | CURRENT |

Any path in this snapshot that conflicts with `CANONICAL_ARTIFACTS_v1_0.md §1` is wrong here, not there. `drift_detector.py` enforces this via the canonical-path cross-check (protocol §H.3).

## §E — Layer build arc (current reality)

**CLAUDE.md holds DURABLE orientation; live state lives in `CURRENT_STATE_v1_0.md`.** For deep history of completed arcs, see the CURRENT_STATE changelog + the per-arc CLOSE artifacts.

**The layer build is the active arc:**

| Layer | Name | Status | Key facts |
|---|---|---|---|
| L0 | Brahmagyan | ✓ SEALED | Infrastructure provisioned; DB bootstrap complete; ga_chart_service live |
| L1 | Gaṇita | ✓ CLOSED | 9 data assets + service; FORENSIC 7/7; orchestrator-native; id-naming standardized. Seal: `L1_GANITA_CLOSURE_v2_0.md`. |
| L2 | Bodha | ✓ BUILT | 14 `bo_*` assets in DAG (bo_laksana root → bo_bimba / bo_karanajala / bo_sangati / bo_samvada / bo_samskara → bo_upaya → bo_pramana_mapa + 4 gestalt/CGM/CDLM writers); tables `bodha_*`; ran end-to-end (Abhinandan L1→L5, 2026-06-27). Handoff: `L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md` |
| L3 | Kāla | ✓ CLOSED | 12 `ka_*` assets, 12/12 buildable; tables `kala_*`; ran end-to-end (Abhinandan L1→L5). Seal: `L3_KALA_CLOSE_v1_0.md` |
| L4 | Phala | ✓ CLOSED | 9 `ph_*` assets, 9/9; tables `phala_*`; ran end-to-end (Abhinandan L1→L5); deterministic phala, calibration owned by L5 (ph_pramana D5 NO-SCORING gate). Seal: `L4_PHALA_CLOSE_v1_0.md` |
| L5 | Mīmāṃsā | ✓ SEALED | 12 `mi_*` assets (10 data writers + 2 service verifiers); tables `mimamsa_*`; sealed in **STRUCTURAL mode** — empirical calibration values fill in as prediction→outcome data accrues (this is by design, not unfinished work). Seal: `L5_SEAL_AND_SHIP_REPORT_v1_0.md` |

**The orchestrator is FROZEN** (sealed at `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md`). The product "click Build" drives any chart's assets in dependency order via the FROZEN `WriterBase` contract. Future layers onboard by writing a `@register('<asset_id>')` `WriterBase` subclass that conforms to the frozen contract — never by extending the orchestrator. See §N for the one-paragraph contract summary and §C item 13 for the full sealed record.

**Truly open items:** see `CURRENT_STATE_v1_0.md §2` for the authoritative live list (this section previously hardcoded a v5.74 snapshot and is intentionally not maintained here — per §F, live state lives in CURRENT_STATE). Durable note: **all six build layers (L0–L5) are now sealed/closed** — the build arc is complete; remaining work is per-chart builds + the L5 calibration loop maturing as outcome data accrues.

## §F — Current execution position (You are here)

**State is authoritative in `CURRENT_STATE_v1_0.md` — read §2 of that file at session open. Do NOT read "you are here" from this file; §F is intentionally not maintained here** ([[feedback-verify-state-not-claude-md]]).

## §G — Session-open handshake (reference)

Every session begins by emitting the SESSION_OPEN artifact per `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md`. The handshake is validated by `platform/scripts/governance/schema_validator.py` (or equivalent in-session check) before any substantive tool call. A session whose handshake fails validation halts and reports to the native; it does not proceed.

Per `CONVERSATION_NAMING_CONVENTION_v1_0.md §4`, the session proposes its Cowork thread name at the top of the first substantive response; that proposal must match the handshake's `cowork_thread_name` field.

## §H — Session-close checklist (reference)

Every session ends by emitting the SESSION_CLOSE artifact per `00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md`. The checklist is validated by `schema_validator.py` as its last action; only after validation passes does the `SESSION_LOG.md` append happen atomically (session_open block + body + session_close block → one entry). A session whose close-checklist fails validation does not claim close.

## §I — Operating principles (summarized)

**File placement rule (enforced since 2026-05-04).** Before creating or saving any file, consult `00_ARCHITECTURE/ROOT_FILE_POLICY.md`. Nothing lands at the project root unless it is in ROOT_FILE_POLICY §2's exhaustive list. Every other file type has a designated folder. Use the §4 decision tree when in doubt.

The full principle list is `PROJECT_ARCHITECTURE_v2_2.md §B — Architectural Principles (Non-Negotiable)` (B.1–B.12). Cross-cutting substrates are in `MACRO_PLAN_v2_0.md §Learning Layer` and `§System Integrity Substrate`. The five most-violated principles, surfaced here as inline reminders:

- **B.1 — Facts/Interpretation separation.** Facts live at L1; derivations at the L2 (Bodha) boundary with explicit ledger; interpretations at L2+ only. Mixing layers destroys auditability.
- **B.3 — Derivation-ledger mandate.** Every L2+ claim carries a `DERIVATION_LEDGER` entry listing the specific L1 fact IDs it consumes. No claim rests on "as is known classically" or "per tradition" without a source.
- **B.8 — Versioning discipline.** Every canonical artifact carries frontmatter `version`, `status`, and a changelog. Registries must not disagree (GA.1 failure mode). Silent file mutation fails `drift_detector.py` and `schema_validator.py`.
- **B.10 — No fabricated computation.** If a computation requires a specialist tool (Jagannatha Hora, Parashara's Light, Swiss Ephemeris) and the value is not already in L1, the session marks it `[EXTERNAL_COMPUTATION_REQUIRED]` with exact specification of what to compute. Claude never invents numerical chart values.
- **B.11 — Whole-Chart-Read discipline.** Every *interpretive* query routes through L2 Bodha synthesis first (MSR + CDLM + CGM + RM), surfaces cross-domain signals via the Cross-Domain Linkage Matrix, then produces its domain-specific answer. A query-answer that skips L2 consultation is a procedural violation equivalent to a red-team finding. **Proportionality carve-out (RS-4, native-authorized 2026-07-19):** a pinpointed factual lookup (`depth: retrieval`) satisfies B.11 via the frame check its response carries (chart_header + session pin) plus the escalation valve — a one-line flag with drill pointer whenever the fact touches an active contradiction, firing yoga, or open prediction window. Source: `RETRIEVAL_STRATEGY_v1_0.md` §3.6; PROJECT_ARCHITECTURE §B.11/§H.4 amended in place.

**Scope declaration (protocol §F; GA.20 closure).** Every session declares `may_touch` and `must_not_touch` globs at session open. An empty `must_not_touch` fails the handshake.

*Mirror Discipline (MP.1 + ND.1) retired 2026-05-27 per native directive (Gemini collaboration inactive). See `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §K` close-out.*

## §J — Quality standard

Acharya-grade. An independent senior Jyotish acharya reviewing this corpus should reach one of: "this is my own level", "this is above my own level", or "this reveals things I wouldn't have seen on first pass". Nothing less.

## §K — Collaboration with Gemini

Multi-agent mirror discipline retired (2026-05-27) — see `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §K` close-out. Gemini collaboration declared inactive by native directive.

## §L — Do not

- Produce generic astrology.
- Collapse layer separation (facts into interpretations or vice versa).
- Skip the Whole-Chart-Read Protocol (B.11 / PROJECT_ARCHITECTURE §H.4).
- Abandon versioning discipline (every artifact carries version metadata + changelog; registries must not disagree).
- Change architecture without native's explicit approval + version bump.
- Duplicate canonical-artifact paths or versions outside `CANONICAL_ARTIFACTS_v1_0.md`. Every other governance surface cites by reference.
- Pre-build infrastructure for macro-phases later than the currently-active one (MACRO_PLAN §Scope Boundary).
- Claim a session is closed without emitting and validating the `session_close` checklist. Close without checklist = not a well-formed session.

## §M — Cadence

Daily sessions. Closed-artifact-per-session discipline — one phase or one step at a time, each producing a discrete, versioned, frontmatter-bearing artifact. Red-team passes at three cadences per MACRO_PLAN v2.0 §IS.8: (a) every third session by default; (b) every macro-phase close before the SESSION_LOG seal; (c) every 12 months for MP itself regardless of phase state. A macro-phase does not close without its red-team. Session-open handshake (§G) validates the cadence obligation via the `red_team_due` field; session-close checklist (§H) validates the obligation was discharged if due.

## §N — Build standards (durable; inherited by every layer)

These standards were hard-won across L0/L1. Every future layer (L2+) inherits them without exception.

### §N.1 — Layer model + naming (LOCKED)

**External lexicon (LOCKED):** Brahmagyan · Gaṇita · Bodha · Kāla · Phala · Mīmāṃsā = internal L0 · L1 · L2 · L3 · L4 · L5. Never show "L0–L5" externally.

**Asset-id convention — underscore prefix per layer:**
`bg_*` (L0) · `ga_*` (L1) · `bo_*` (L2) · `ka_*` (L3) · `ph_*` (L4) · `mi_*` (L5).
Dot-notation retired (migration 224 — L1 closure Phase B). **Never create a `bodha.*` or `ganita.*` id.**

### §N.2 — FROZEN orchestrator contract

The orchestrator was built once and is FROZEN at `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2`. Every new-layer writer:
- is a `@register('<asset_id>')` `WriterBase` subclass;
- implements `run(ctx) -> WriterResult` (light) OR `plan_substeps(ctx)` + `run_substep(ctx, step)` (heavy);
- runs on **`ctx.db_conn` and NEVER commits or closes it** — orchestrator owns the transaction + savepoint per sub-step;
- does NOT write `asset_throughput` itself — orchestrator is the sole build-state writer;
- gets `chart_id` + `birth_params` from `ctx.config`.

**If a writer seems to need a contract change → STOP and raise with the native.** The freeze is deliberate. See ORCHESTRATOR_CONVERGENCE_CLOSE §2 for the canonical type definitions.

### §N.3 — Idempotency standard per layer ([[feedback-idempotency-pattern-per-layer]])

- **L0 (Brahmagyan):** `ON CONFLICT DO NOTHING` / `ON CONFLICT DO UPDATE` — global reference tables, safe to upsert.
- **L1+ (Gaṇita, Bodha, …):** per-chart **delete-then-insert** scoped to `(chart_id × natural key)`. Rebuild REPLACES, never accretes. Shared helper mirrors `ga_writers/_idempotency.py`.

### §N.4 — Ratified build principles

- **Floors aspirational, not gates** ([[feedback-floors-are-aspirational-not-gates]]): set `target_floor` = achieved count after build; never fabricate rows to hit a number.
- **No audience tier** ([[feedback-no-audience-tier]]): writers emit all rows; serve-time governs access.
- **Deterministic-first** ([[feedback-deterministic-first-for-data-build]]): Python over LLM for computation; embeddings are a deterministic transform and are fine; generative LLM for curation is NOT.
- **No JH-parity oracle** ([[feedback-no-jh-parity-anywhere]]): verification is internal-consistency + classical-rule re-derivation + FORENSIC grounding.
- **Cockpit truth:** each asset needs a correct chart-scoped `count_sql` on `asset_registry` (stats route reads `count_sql`, NOT `asset_throughput` — the L1 trap).
- **Surgical migrations only:** never deploy.yml-auto or bulk `migrate.ts` ([[feedback-deploy-migrations-silent-noop]]).

### §N.5 — L1 is the authority over L2+ derivations ([[the MSR drift handoff]])

An L2+ signal NEVER restates an L1 computed value as its own truth — it REFERENCES the L1 `fact_id` and inherits L1's value. If a signal's derivation disagrees with the L1 fact it cites, that is a halt-worthy bug, not a stored divergence. The `constituent_facts_array` in MSR signals resolves back to `chart_facts.fact_id` — these MUST resolve. See `MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md` for the documented trap.

### §N.6 — Serving Density Principle ([[density_contract]] · Doctrine Campaign D-1 → D-1.5b)

Every served surface layers its rows/signals by verification/confidence density and never flattens them into one undifferentiated list. This principle was implicit in the codebase since the D-1 Night-1 `density_contract` field landed on `CapabilityDescriptor` (`platform/src/lib/retrieval/registry/types.ts`) and the R5.1 C1 response-budget trimmer (`platform-mcp/src/lib/response_budget.ts`); D-1.5b Lane B-7 is the first session to write the principle out in prose, from what the code already does, not from a fresh idea.

**The principle, in the concrete form the code already enforces:**

1. **Never present catalog/label matches as confirmed findings.** A row that is a single-pass catalog match awaiting cross-verification (e.g. `ganita_yogas_get` / `get_yoga_dosha.ts`'s `fire_reason: 'requires_pass'` rows) is still served — B.10 forbids silently dropping data — but is counted and flagged SEPARATELY from confirmed findings (`catalog_only_rows_in_page`, `catalog_only_note`, and the v3-envelope `judgment_flags` entry `catalog_only_rows_present`), with an explicit pointer to the firings-authoritative surface (`ganita_yoga_firings_get`) for the cross-verified layer. A caller must never be able to read the raw row count as "N confirmed yogas."
2. **The densest, most-actionable layer is the one a budget trim protects first.** `response_budget.ts`'s `TrimmableSection.hardFloor` flag exists specifically because the generic biggest-section-first trim logic will, left alone, zero out a section the instant it becomes genuinely populated (the exact regression the D-1.5a wave gate caught in `judgment_query`'s `bearing_yogas`). A section carrying confirmed/high-density findings — a verdict's grounding evidence, a firings-authoritative row set — declares `hardFloor: true` so its declared `minKeep` survives even the hard-cap fallback pass; lower-density sections (label catalogs, secondary MSR corroboration) are trimmed first and are floorable to zero.
3. **Within a layered response (verdict / grounding / drill_pointers / judgment_flags), the verdict layer is never empty when grounding data exists.** `judgment_query` (`register_d9_judgment.ts`) computes its deterministic `verdict` from already-graded dignity/varga/yoga terms and separately reports `bearing_yogas` (confirmed, firings-authoritative) ahead of `bearing_yogas_corroboration` (catalog-label, secondary) — sorted so a domain-matching confirmed row survives any row-count cut ahead of a higher-raw-strength but domain-irrelevant one. An honest empty result is reported via `judgment_flags` (e.g. `bearing_yogas_empty`, `timing_anchored_false`), never silently substituted with a populated-looking but hollow envelope.
4. **Density signaling is data, not narration.** `density_contract` (optional on `CapabilityDescriptor`) declares a capability's `paginated`, `facets`, and `empty_reason` discipline machine-readably, so a CI/census harness can assert byte caps and facet/empty-reason coverage per tool without re-deriving it from source (§N.6 Part 2 below is that harness for two load-bearing surfaces).

**What violates this principle:** flattening confirmed and catalog-only rows into one array with no distinguishing field; a generic budget trim that can zero a response's only confirmed-finding section while a less-dense section survives; a verdict/summary layer that goes silently empty instead of reporting the honest gap via a flags field; a capability that claims `density_contract` but ships no `empty_reason` discipline behind it.

### §N.7 — Narration Fidelity Principle ([[suddha_vaca]] · ŚUDDHA-VĀCA campaign, 2026-07-28)

Drawn from what the code now enforces after the ŚUDDHA-VĀCA narration-purification wave — not a
fresh idea, a codification of the discipline five independent writer fixes and a new CI guard
converged on independently:

1. **Narration is a deterministic restatement of L1-referenced facts.** A sentence that grades,
   labels, or verbalizes a computed value must trace to a cited `fact_id` it *reads*, never one it
   *re-derives*. Re-deriving invites drift between the restatement and the fact it claims to restate.
2. **Every fact selection that reduces a set to one row pins `fact_key` and carries a total
   `ORDER BY` (or `DISTINCT ON` / `LIMIT 1` equivalent).** Category-only selection (`fact_category`
   alone, `.find()`/`.filter()[0]` without a key check) is the D1 defect class — enforced permanently
   by the `fact-category-pin-lint` CI guard (`platform/scripts/governance/
   check_fact_category_pinning.py`). Note the guard's honest scope: it closes fact_key-level
   ambiguity; it does not by itself guarantee single-row-per-key across `build_id` generations —
   that remains a write-path idempotency discipline, not a read-time lint's job.
3. **No wrapper-local constant may shadow an L1-computed value**, even when the constant's current
   value happens to be correct — a constant can drift from its source; a reference cannot.
4. **A verification flag must have a real detector behind it, or be null.** A flag that reads "0
   leaks" or "verified clean" with no code path that could ever produce a different value is not a
   clean result — it is an unimplemented check wearing a clean result's clothes.
5. **Verified fact ≠ verified prose.** `two_pass_verified` on a fact covers the number; it says
   nothing about the sentence that selects among numbers and grades them. Every narration layer that
   assembles a verdict from facts needs its own semantic/golden-value test — a passing fact-level
   verification pass is not evidence the narration built on top of it is correct.
6. **An honest null beats an invented judgment.** Where a sentence cannot be derived from a cited
   fact, remove the claim or emit a null — never substitute a plausible-sounding default (the
   `'elevated'`-on-missing-`direction` and `5.0`-on-computed-zero-`grade` defects were both exactly
   this: a favorable/neutral-sounding invention standing in for "I don't know").

**What violates this principle:** everything §N.6 already lists, plus: a grade/valence assignment
keyed off a proxy signal (corroboration tier) instead of the actual classical fact it's supposed to
report (agreement vs. matching_class); a fallback value chosen for how it *reads* rather than for
being the codebase's own established neutral convention; a model-policy allowlist that contradicts
its own docstring.

### §N.8 — Earned-Signal Principle ([[the SATYA-DIPA no-op-completion defect]] · SATYA-DĪPA campaign, 2026-07-29)

Every status, grade, or PASS must be computed by a detector that measures the specific claim it
asserts; a signal without such a detector is null, not green. §N.7 item 4 said this for narration
verification flags specifically; SATYA-DĪPA found the same defect class one layer down, in the
build system's own success signal, and generalizes it here across all three campaigns it has now
been confirmed in.

**Confirmed instances:**

1. **Ṣaḍbala selector regression (ŚUDDHA-VĀCA)** — a serving-layer selector picked the wrong
   strength column; nothing detected the mismatch because no test compared the served value against
   the source-of-truth computation.
2. **Two `bo_pramana_mapa` flags (ŚUDDHA-VĀCA)** — verification flags that could be set true without
   the check they claimed to represent ever running (the direct precedent for §N.7 item 4).
3. **The PB-2 byte-equality gate** — a "byte-identical" claim with no byte comparison behind it.
4. **The orchestrator no-op-completion promotion predicate (SATYA-DĪPA)** — `asset_throughput.state
   = 'lit'` asserted "this asset's build is complete," but the detector behind it only checked "rows
   present," never "the substep plan finished." A genuinely partial build with some earlier-committed
   data present could satisfy the proxy without satisfying the claim — the same defect class as
   D-1.6 itself, one layer deeper (D-1.6 was "the rescue doesn't exist"; this was "the rescue exists
   but doesn't check the right thing"). Fixed 2026-07-29: the predicate now asks the substep-plan-
   completeness question directly, for writers that have a real plan to be complete or incomplete
   about (`00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` §7.1; `SATYA_DIPA_REPORT_v1_0.md`).

**What to do when auditing a status/grade/PASS surface:** ask "what specifically does this signal
claim, and what code path would have to run — and fail — for the signal to correctly read false?"
If no such code path exists, or it checks a proxy rather than the claim, the signal is null. "It's
usually true" or "nothing has broken yet" is not a substitute for a real detector.

---

*End of CLAUDE.md v6.6 (2026-07-29, SATYA-DĪPA campaign) — new §N.8 Earned-Signal Principle,
generalizing §N.7 item 4's "a flag needs a real detector or it's null" doctrine to the build layer:
the orchestrator's no-op-completion promotion predicate asserted substep-plan completeness while
only ever checking row presence, the same defect class as D-1.6 one layer deeper. Fixed via the one
authorized freeze exception in `asset_runner.py` (see `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` §7.1
and `SATYA_DIPA_REPORT_v1_0.md`). Also corrects a stale carry-forward: §N.7's own footer (v6.5) said
"two P0 lanes remain PARKED on PARISHODHANA PRs #827/#828" — both merged 2026-07-28 and their lanes
(lane:serve-shadbala, lane:ga-tajaka) released the same day, making ŚUDDHA-VĀCA fully CLOSED (7/7),
not PARTIAL; this was independently re-verified live during SATYA-DIPA Phase 0 (serve-shadbala fix
confirmed still correct in production on the canonical chart). Prior: v6.5 (2026-07-28, ŚUDDHA-VĀCA
Phase C/D/E/F session) — new §N.7 Narration Fidelity Principle, codifying the discipline enforced by
the fact-category-pin-lint CI guard and five independently-verified writer fixes (bo_laksana,
sudarshana_emitter, l3_convergence, mi_darshana, ph_nimitta/engine.py) merged this wave. Prior: v6.4
(2026-07-19, Cowork retrieval-strategy session) — §I B.11
amended with the RS-4 proportionality carve-out (native-authorized): B.11 scoped to interpretive
queries; factual lookups satisfy it via frame check + escalation valve. Mirrors the in-place
amendments to `PROJECT_ARCHITECTURE_v2_2.md` §B.11/§H.4; doctrine source `RETRIEVAL_STRATEGY_v1_0.md`
§3.6. Prior: v6.3 (2026-07-15, DOCTRINE-WAVES D-1.5b Lane B-7) — new §N.6 Serving Density Principle:
codifies the density-layering discipline the `density_contract` field (types.ts) and the
response-budget `hardFloor` mechanism (response_budget.ts) already embody, drawn from `judgment_query`
and `ganita_yogas_get`'s catalog-vs-confirmed handling. Frontmatter/footer version drift corrected
(frontmatter had stayed "6.0" since v6.0 while the footer advanced to "6.2" — both now read 6.3).
Prior: v6.2 (2026-06-29 — L4 Phala SEALED: §E L4 BUILT→CLOSED (seal `L4_PHALA_CLOSE_v1_0.md`); §E
"truly open items" note updated — all six layers L0–L5 now sealed/closed, build arc complete). v6.1
(2026-06-29 — §E layer-reality refresh: L2 NEXT→BUILT, L3 draft→CLOSED, L4 draft→BUILT, L5
draft→SEALED). v6.0 (2026-06-12 — structural realignment). Full changelog history at
`00_ARCHITECTURE/CLAUDE_MD_CHANGELOG.md`.)*
