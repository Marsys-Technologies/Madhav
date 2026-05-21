---
artifact: MACRO_PLAN_v2_0
document: MARSYS-JIS MACRO PLAN — STRATEGIC ARC
project_name: Abhisek Mohanty — Jyotish Intelligence System (MARSYS-JIS)
subject: Abhisek Mohanty (b. 1984-02-05, 10:43 IST, Bhubaneswar)
version: 2.1
status: CURRENT
supersedes: MACRO_PLAN_v1_0.md (SUPERSEDED 2026-04-23 at Step 5 of the Step 0→15 governance rebuild)
closed_on: 2026-04-23 (Step 5 of the Step 0→15 governance rebuild)
author: Abhisek Mohanty (native, project owner)
date: 2026-04-23
produced_during: STEP_3_MACRO_PLAN_REWRITE (Step 0→15 governance rebuild)
id_namespace: M1..M10 (macro-phases); LL.1..LL.10 (Learning Layer mechanisms); IS.1..IS.9 (System Integrity Substrate axes); ED.1..ED.9 (External dependencies); CW.LEL, CW.PPL (Cross-cutting workstreams); MP.1..MP.7 (Mirror pairs, first-pass inventory)
purpose: >
  Strategic orientation layer for the MARSYS-JIS project. Frames the ten macro-phase
  arc (M1–M10) and the two cross-cutting substrates (Learning Layer and System
  Integrity). Read once per session for orientation; execute only the currently-
  scoped phase. This document governs how the project evolves across macro-
  phases and across agents (Claude + Gemini + any admitted future agent). v2.0
  is produced during the governance rebuild workflow (Step 0 → Step 15) that
  closes multi-session drift observed in M2 execution.
audience:
  primary: Any LLM session working on MARSYS-JIS, current and future
  secondary: Abhisek Mohanty (native, project owner)
  tertiary: Independent classical-Jyotish acharyas reviewing the corpus
operational_rule: >
  Read this once per session for orientation. Execute only the currently-scoped
  phase. Do not pre-build infrastructure for later macro-phases. If any
  integrity axis (§System Integrity Substrate) is violated, halt and report.
  For the canonical reading order across all governance surfaces, see
  CLAUDE.md §Mandatory reading before any work.
changelog:
  - v2.1 (2026-05-02, M4-C-S4-CLOSE): Surgical naming propagation per
    DECISION-1 (R.LL5DESIGN.1 native arbitration 2026-05-02 — Option A
    "rename mechanism in governance docs to match brief"). LL.5 mechanism
    name updated from "Retrieval ranking learning" → "Dasha-Transit
    axis-weight modulator" in three places: (a) §LL-Appendix.A activation
    matrix LL.5 row; (b) §LL-Appendix.B per-mechanism heading LL.5;
    (c) §LL-Appendix narrative inline mention. No structural changes; no
    semantic protocol changes; substrate I/O / kill-switch / owner /
    dependency declarations unchanged (mechanism still "ranker weights
    consuming relevance judgements" — name now reflects the Dasha-vs-Transit
    axis-attribution character of the M4-C-S1 first shadow write per
    LL5_DASHA_TRANSIT_DESIGN_v1_0.md design). R.LL5DESIGN.1 CLOSED at this
    propagation. Resolves the M4-C-S1 brief-vs-MACRO_PLAN naming divergence
    flagged in LL5_DASHA_TRANSIT_DESIGN §6.5.
  - v2.0 CLOSED (2026-04-23, Step 5 of the Step 0→15 governance rebuild):
    Status flipped DRAFT_PENDING_REDTEAM → CURRENT. MACRO_PLAN_v1_0.md marked
    SUPERSEDED in the same atomic close. Cross-surface propagation executed
    per MACRO_PLAN_REVISION_SPEC_v1_0.md §5.3 ordering (S.8 → S.5 + S.6 →
    S.1 + S.2 → S.3 → S.7 → S.4 → S.9 → S.10): MP v1.0 banner + frontmatter;
    FILE_REGISTRY bumped to v1.1 with MP v2.0 CURRENT row, MP v1.0 SUPERSEDED
    row, MP Revision Spec CLOSED row, MP Red-team CLOSED row, MSR row
    corrected to MSR_v3_0 (499 signals) per GA.1; GOVERNANCE_STACK amended
    in-place with STEP_5 amendment log; CLAUDE.md mandatory reading item 3
    re-pointed to MP v2.0; .geminirules + .gemini/project_state.md mirrored
    per ND.1 adapted-parity (S.3 resolves GA.7 by dropping the
    twinkly-puzzling-quokka.md reference); STEP_LEDGER Step 5 closed;
    SESSION_LOG appended. Red-team evidence: MACRO_PLAN_REDTEAM_v1_0.md
    (verdict PASS_WITH_FIXES; two surgical FIXes applied inline during Step
    4; post-fix line count 1059). Scope decision recorded in STEP_LEDGER:
    WARN.2 (PHASE_B_PLAN §N.10 stale MP v1.0 pointer) deferred to a tracked
    PHASE_B_PLAN v1.0.3 amendment cycle — not included in this atomic close
    because spec §5.1 S.1–S.10 does not name PHASE_B_PLAN. ND.1 global
    status remains `open` (flips to `addressed` at Step 7 per ND.1 close
    condition). Next step in rebuild: Step 5A (Project Architecture
    refresh v2.1 → v2.2).
  - v2.0 (2026-04-23): Architectural revision per MACRO_PLAN_REVISION_SPEC_v1_0.
    Produced during Step 3 of the Step 0→15 governance rebuild. Addresses 132
    MPC in-schema findings, 4 MPC.OS out-of-schema findings, and the ND.1
    native directive (Mirror Discipline as a First-Class Governance Principle).
    Adds System Integrity Substrate parallel to Learning Layer. Replaces prose
    macro-phase paragraphs with per-row schema (entry / exit / dependencies /
    deliverable paths / risks / quality gate / native-approval points / agent
    roles / time envelope / ethics binding). Introduces five new top-level
    sections (Ethical Framework, External Dependency Graph, Meta-Governance,
    Multi-Agent Collaboration, Post-M10 Framing) plus Acharya Reviewer Pool
    Policy and Time/Effort Stance as separate top-level sections. Adds
    Learning Layer Specification Appendix and Finding-Resolution Appendix.
    Refreshes M1 status (M1 CLOSED 2026-04-19 per GAP_RESOLUTION_SESSION +
    CLOSURE_AUDIT_PASS). Status is DRAFT_PENDING_REDTEAM until Step 4
    red-team passes and Step 5 closure + propagate sets status to CURRENT and
    marks v1.0 SUPERSEDED. Full finding-to-section binding in this document's
    Finding-Resolution Appendix and in MACRO_PLAN_REVISION_SPEC_v1_0.md §7.
  - v1.0 (2026-04-23): Initial macro plan establishing ten macro-phase arc and
    cross-cutting Learning Layer substrate. Introduced to prevent session-level
    scope drift in M2 work. To be marked SUPERSEDED by v2.0 once Step 5 of the
    governance rebuild closes.
---

# MARSYS-JIS Macro Plan — Strategic Arc v2.0

Authoritative strategic arc for the MARSYS-JIS project. See frontmatter for version, status, and audience.

---

## Why this exists

v2.0 of this plan is produced in Step 3 of the Step 0→15 governance rebuild that addressed multi-session drift observed during M2 execution. The rebuild's closed form is the GOVERNANCE_BASELINE artifact produced at Step 15; until then, this plan is governed jointly by the STEP_LEDGER and this frontmatter.

The detailed phase plans in `00_ARCHITECTURE/` describe the current work in depth. They do not describe where the current work sits in the full arc. Without that frame, any session risks over-engineering the present phase or under-engineering it by missing forward dependencies. This document fixes the frame.

## Ultimate goal

Build an LLM-operated Jyotish instrument that, for this native, (1) reads the chart with acharya-grade depth, (2) surfaces patterns and contradictions across layers and systems that no individual astrologer could hold in working memory, (3) makes time-indexed, probabilistic, calibrated predictions testable against lived reality and correctable from outcomes. Then extend the method beyond this native so the instrument becomes a research tool for astrology as a discipline.

This goal is bounded by the Ethical Framework (§Ethical Framework): the instrument produces probabilistic, calibrated, auditable outputs for consenting audiences under stated disclosure tiers; it is not a fortune-telling product.

---

## System Integrity Substrate

The Integrity Substrate is parallel to the Learning Layer. The Learning Layer is how the project gets smarter; the Integrity Substrate is how the project stays coherent across sessions and across agents. Both are cross-cutting (present in M2–M10). Both have kill-switches and governance. Where the Learning Layer modulates classical priors with empirical evidence, the Integrity Substrate locks the project's claims about its own state — canonical artifacts, mirror status across agents, session memory, disagreement handling, automated drift and schema checks — against the forms of drift this project has already observed. Mirror Discipline (per ND.1) is declared here as one of the substrate axes — specifically §IS.2 below.

### §IS.1 — Canonical Artifact Discipline

There is exactly one source of truth per canonical artifact. The authoritative list is `CANONICAL_ARTIFACTS_v1_0.md` (Step 7 deliverable of the governance rebuild). MP v2.0 does not restate the canonical paths inline; duplication is itself a drift vector. A session that needs the current canonical path for MSR, UCN, CDLM, CGM, RM, FORENSIC, or any other registered artifact reads CANONICAL_ARTIFACTS and only CANONICAL_ARTIFACTS. Version-drift between registries (per the grounding audit finding GA.1 where FILE_REGISTRY and GOVERNANCE_STACK claimed MSR_v2_0 while CLAUDE.md and SESSION_LOG claimed MSR_v3_0) is the failure mode this axis closes.

### §IS.2 — Mirror Discipline (ND.1 implementation at MP layer)

Mirror Discipline is a first-class governance axis, promoted from the operational practice named once in CLAUDE.md's Gemini collaboration clause. Three load-bearing claims:

1. **Bidirectional obligation.** Every Claude-side governance file that has a Gemini-side counterpart is kept in continuous semantic parity with its counterpart. Any change on the Claude side triggers a mirror update on the Gemini side in the same session. Symmetrically, any change on the Gemini side triggers a mirror update on the Claude side in the same session.
2. **Adapted parity, not byte-identity.** The mirror is *semantically* equivalent, not *textually* identical. CLAUDE.md speaks in Claude's conventions (`<system-reminder>`-style phrasing, Claude-Code-anchored norms, Claude-tool expectations). `.geminirules` and `.gemini/project_state.md` speak in Gemini's conventions. Each mirror is adapted to its target agent's construct while preserving the meaning. The mirror principle is *semantic parity of governance content, not feature parity of agent capabilities*.
3. **Scope is not limited to CLAUDE.md.** The principle extends to every governance surface that has a Gemini-side reference or counterpart. The authoritative inventory is maintained in `CANONICAL_ARTIFACTS_v1_0.md` (Step 7 deliverable) via a `mirror_obligations` column. The MP-layer first pass of that inventory is carried in the revision spec §5.2 as mirror-pairs MP.1 through MP.7; the Step 5A architecture refresh §D.11 and the Step 7 CANONICAL_ARTIFACTS enforce it.

Enforcement is mechanical, not procedural. Step 7 implements `mirror_enforcer.py` operating over the full inventory; Step 6 designs the enforcement protocol. Mirror-desync is treated as a first-class disagreement class under §Multi-Agent Collaboration §3.4.C.

This subsection implements native directive ND.1 at the MP layer; full inventory is downstream per the Step 5A + Step 7 obligations in ND.1's consumption matrix.

### §IS.3 — SESSION_LOG as drift detector

SESSION_LOG is the cross-session memory anchor. Every macro-phase close binds to a SESSION_LOG seal — an entry that names the macro-phase, the exit-criteria checklist as verified, the deliverable paths, the red-team verdict, and the next macro-phase's opening state. A macro-phase is not closed until its seal exists. The session-open handshake (§IS.7) requires each session to cite the most recent seal and declare which macro-phase is active. GA.19 (no "you are here" marker) is closed at MP layer by this axis; the full CURRENT_STATE artifact is Step 10's deliverable.

### §IS.4 — FILE_REGISTRY and GOVERNANCE_STACK as enforcement registries

`FILE_REGISTRY_v1_0.md` tracks every artifact in the project with CURRENT / SUPERSEDED / ARCHIVAL status. `GOVERNANCE_STACK_v1_0.md` tracks versions, closure events, and amendment history. Both are authoritative by reference (Step 6 governance protocol §D decides whether to merge the two or keep them separate; MP v2.0 does not pre-decide). Every artifact mutation — creation, version bump, supersession, archival — requires a matching row in FILE_REGISTRY and a matching closure entry in GOVERNANCE_STACK. The Step 14 schema validator baseline run (`SCHEMA_VALIDATION_REPORT_STEP_14`) enforces this after Step 12 ongoing hygiene policies land.

### §IS.5 — DISAGREEMENT_REGISTER

Agent-to-agent disagreements (Claude ↔ Gemini today; Claude ↔ Gemini ↔ future agents after §3.4.E admits them) are logged to `DISAGREEMENT_REGISTER` (Step 7 deliverable). Unresolved disagreements escalate to native. Mirror-desync is an implicit disagreement class requiring resolution, not silent overwriting. The protocol steps (isolation re-run, reconciler resolution attempt, native arbitration, mirror-desync handling) are specified in §3.4.C.

### §IS.6 — Drift-detector and schema-validator automation

Two scripts operate independently of session consent: `drift_detector.py` compares the governance surfaces (CLAUDE.md ↔ .geminirules ↔ .gemini/project_state.md and the mirror-pair inventory) and fails loudly on divergence; `schema_validator.py` enforces schema conformance on SESSION_LOG entries, per-artifact frontmatter, and mirror-pair structural equivalence. Both are produced in Step 7 and run on the cadences established in Step 12 (ongoing hygiene) and at the Step 13 + Step 14 baseline runs. A script cannot be skipped by a session; it either exits 0 or it fails the session's close-criteria. GA.13 ("a procedural rule that has been broken once will be broken again") and GA.14 (no drift-detection script) are closed by this axis.

### §IS.7 — Session-open handshake and session-close checklist

Step 7 produces `SESSION_OPEN_TEMPLATE` and `SESSION_CLOSE_TEMPLATE`. The open handshake requires a session to (a) confirm it has read the mandatory list, (b) cite the current STEP_LEDGER row or the current macro-phase, (c) declare its scope (exactly one step during rebuild; one sub-phase afterwards), (d) confirm the mirror-pair inventory is current, (e) propose its Cowork thread name per `CONVERSATION_NAMING_CONVENTION_v1_0.md`. The close checklist requires a session to (a) confirm SESSION_LOG is appended, (b) confirm every artifact touched has a matching registry row, (c) confirm mirror updates were propagated, (d) run the drift detector, (e) mark the STEP_LEDGER row. A session that does not complete the handshake is not a well-formed session. GA.15, GA.16, GA.20, GA.21 are closed by this axis.

### §IS.8 — Red-team cadence as substrate axis

Red-team passes are mandatory at three cadences: (a) every third session by default (existing CLAUDE.md rule); (b) every macro-phase close before the SESSION_LOG seal (§IS.3); (c) every 12 months for MP itself regardless of phase state, per §3.10.C. A macro-phase does not close without its red-team; an MP revision does not ship without its spec being red-teamed (Step 4 is the paradigm for MP v2.0 itself).

### §IS.9 — Governance rebuild acknowledgment

MP v2.0 is produced in Step 3 of the Step 0→15 governance rebuild, which closes in `GOVERNANCE_BASELINE_v1_0.md` at Step 15. Until Step 15 closes, the STEP_LEDGER governs which step is current and the rebuild banner in CLAUDE.md is the authoritative "you are here" marker. After Step 15 closes, this subsection is revised to point to the governance baseline and to name the rebuild as the predecessor state from which steady-state governance was reached.

---

## The Learning Layer — a cross-cutting substrate

Progressive calibration is woven through M2–M10, not treated as a single phase. It sits in `06_LEARNING_LAYER/` as a sibling to the Discovery Layer. **Directory `06_LEARNING_LAYER/` is scaffold-pending as of v2.0 publication; the LL scaffold decision is Step 11 of the governance rebuild. Sessions reading v2.0 before Step 11 closes must not assume the directory exists.**

Ten mechanisms, roughly in order of feasibility: signal weight calibration (LL.1), graph edge weight learning (LL.2), embedding space adaptation (LL.3), prompt optimization (LL.4), Dasha-Transit axis-weight modulator (LL.5), plan selection learning (LL.6), discovery prior shaping (LL.7), Bayesian model updating (LL.8), counterfactual learning from misses (LL.9), LLM fine-tuning (LL.10). Per-mechanism specifications (input, output, activation phase, kill-switch, owner, inter-mechanism dependency, workstream interaction) are in the Learning Layer Specification Appendix immediately below. The first four become available during M2. The rest activate at M4, M5, M6, M7 respectively per the activation matrix in §LL-Appendix.A.

**Learning discipline — non-negotiable across all macro-phases:**

1. Classical priors are locked; learning modulates, never overwrites.
2. Bayesian posterior framing with tight priors. Frequentist overfit is rejected.
3. Every parameter update requires ≥N independent observations where N is per-mechanism-defined in the Learning Layer Specification Appendix (N defaults to 3 per mechanism at MP v2.0 publication; per-mechanism overrides land at Step 11 scaffold or at the mechanism's activation phase, whichever comes first, and are logged as an amendment to §LL-Appendix.B); never less than 3. Updates also pass the two-pass Gemini/Claude protocol.
4. Held-out prospective data is sacrosanct; the model never sees outcome before prediction.
5. Every learned parameter is auditable, reversible, versioned, and logged to the ledger.
6. The prior is the classical corpus. Evidence earns the right to modulate the prior; it never automatically does.

**Risk stance.** n=1 phase: risk-averse on calibration, risk-seeking on discovery. Calibration errors compound; discovery misses are recoverable via later re-ranking. Every LL mechanism below is calibrated toward this asymmetry.

**n=1 risk:** with a single native, overfit is the dominant statistical risk, not underfit. Every mechanism above is designed to resist retrofit. New parameters live in shadow mode for N observations before influencing downstream components. The six learning-discipline rules above each attach to one or more n=1 risk classes per §LL-Appendix.C mitigation binding table.

---

## Learning Layer Specification Appendix

### §LL-Appendix.A — Activation-phase matrix

Cell values: `scaffold` = infrastructure built; not active. `active` = mechanism running. `dormant` = paused pending upstream. `n/a` = not applicable at this phase.

| Mechanism | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M8 | M9 | M10 |
|---|---|---|---|---|---|---|---|---|---|---|
| LL.1 Signal weight calibration | n/a | scaffold | scaffold | active | active | active | active | active | active | active |
| LL.2 Graph edge weight learning | n/a | scaffold | scaffold | active | active | active | active | active | active | active |
| LL.3 Embedding space adaptation | n/a | scaffold | scaffold | active | active | active | active | active | active | active |
| LL.4 Prompt optimization | n/a | scaffold | scaffold | active | active | active | active | active | active | active |
| LL.5 Dasha-Transit axis-weight modulator | n/a | scaffold | dormant | active | active | active | active | active | active | active |
| LL.6 Plan selection learning | n/a | scaffold | dormant | active | active | active | active | active | active | active |
| LL.7 Discovery prior shaping | n/a | scaffold | dormant | active | active | active | active | active | active | active |
| LL.8 Bayesian model updating | n/a | n/a | n/a | scaffold | active | active | active | active | active | active |
| LL.9 Counterfactual learning from misses | n/a | n/a | n/a | n/a | scaffold | active | active | active | active | active |
| LL.10 LLM fine-tuning | n/a | n/a | n/a | n/a | n/a | n/a | scaffold | scaffold | scaffold | active |

**Justification for "first four at M2".** LL.1–LL.4 are corpus-internal: they update weights and embeddings over the existing corpus and prompt templates, with no prospective prediction requirement. They can activate as soon as Discovery Engine outputs exist at M2 close. LL.5–LL.7 depend on Discovery Engine output being fed into a retrieval/planning loop, which activates at M4 empirical-calibration kickoff. LL.8 requires probabilistic outputs to update, which is M5. LL.9 requires prediction misses, which is M6. LL.10 requires cohort data (per LL.7/cohort disambiguation in LL-Appendix.B), which is M7 at earliest; fine-tuning activates at M10 post-validation.

### §LL-Appendix.B — Per-mechanism specification

**N for discipline rule #3.** Per Learning Layer discipline rule #3, every parameter update and every rolling-window kill-switch N defaults to 3 per mechanism below. Per-mechanism overrides are set at Step 11 scaffold (or at the mechanism's activation phase, whichever comes first) and logged as an amendment to this appendix.

#### LL.1 — Signal weight calibration

- **Input:** MSR signal rows (499 at current v3.0); per-signal LEL event-match records once M4 produces them; per-signal PPL prediction outcomes once M6 produces them.
- **Output:** Per-signal calibration weights written to a shadow-mode register in `06_LEARNING_LAYER/signal_weights/` (scaffold-pending); promoted to production register after N observations.
- **Activation phase(s):** scaffold at M2; active from M4 per §LL-Appendix.A.
- **Kill-switch:** suspended if per-signal calibration error rate worsens over a rolling window of N updates; suspended globally if any learning-discipline rule (#1 priors-locked in particular) is flagged as violated.
- **Owner:** native introduces weight-update rubric; Claude scaffolds register + update pipeline; Gemini red-teams per cadence.
- **Dependency on other LL.M:** none (foundation mechanism).
- **Interaction with workstreams:** consumes CW.LEL event records; consumes CW.PPL prediction outcomes.

#### LL.2 — Graph edge weight learning

- **Input:** CGM edge rows; signal-to-signal co-activation records from Discovery Engine output; per-edge outcome-correlation data from M4+ onward.
- **Output:** Edge weight modulators written to shadow register in `06_LEARNING_LAYER/edge_weights/` (scaffold-pending); promoted post-N observations.
- **Activation phase(s):** scaffold at M2; active from M4.
- **Kill-switch:** suspended if modulated edge weights produce a worse retrieval-precision score than classical-prior-only edges on held-out probes.
- **Owner:** native approves modulator range; Claude scaffolds; Gemini red-teams.
- **Dependency on other LL.M:** LL.1 (signal weights stabilize before edge weights shift).
- **Interaction with workstreams:** consumes CW.PPL outcomes; emits proposed edge updates to SESSION_LOG for red-team.

#### LL.3 — Embedding space adaptation

- **Input:** current embedding corpus (Voyage-3-large; see ED.3); per-query relevance records; signal-to-signal similarity records.
- **Output:** Adapter weights (LoRA-style or equivalent) layered on the base embedding; emitted to `06_LEARNING_LAYER/embedding_adapters/` (scaffold-pending).
- **Activation phase(s):** scaffold at M2; active from M4.
- **Kill-switch:** suspended if adapted embeddings degrade retrieval MAP/MRR against the classical-only baseline on held-out queries.
- **Owner:** Claude co-owns with native per standard LL ownership (§LL-Appendix.D).
- **Dependency on other LL.M:** none for scaffold; LL.1 stable for active operation.
- **Interaction with workstreams:** indirect (feeds retrieval, which feeds Discovery which feeds PPL).

#### LL.4 — Prompt optimization

- **Input:** per-prompt outcome records (pattern-emission quality, reconciliation correctness); operator feedback on Discovery output.
- **Output:** Updated prompt templates in `06_LEARNING_LAYER/prompts/` (scaffold-pending) with version bumps per template.
- **Activation phase(s):** scaffold at M2; active from M4.
- **Kill-switch:** suspended if updated prompt produces lower acharya-grade score on held-out chart probe.
- **Owner:** Claude co-owns with native.
- **Dependency on other LL.M:** none.
- **Interaction with workstreams:** consumes CW.PPL outcome records tied to specific prompt versions.

#### LL.5 — Dasha-Transit axis-weight modulator

- **Input:** query-result-click (pseudo-click = acharya-grade relevance judgement); ranker features.
- **Output:** Ranker weights in `06_LEARNING_LAYER/retrieval_rankers/` (scaffold-pending).
- **Activation phase(s):** scaffold at M2; dormant at M3; active from M4.
- **Kill-switch:** suspended if learned ranker worsens MAP@k against classical-prior baseline.
- **Owner:** Claude co-owns with native; Gemini red-teams.
- **Dependency on other LL.M:** LL.3 stable.
- **Interaction with workstreams:** consumes relevance judgements (which may arise from native review during LEL curation).

#### LL.6 — Plan selection learning

- **Input:** per-plan outcome records (did the plan produce the expected acharya-grade answer?).
- **Output:** Plan-selector weights in `06_LEARNING_LAYER/plan_selectors/` (scaffold-pending).
- **Activation phase(s):** scaffold at M2; dormant at M3; active from M4.
- **Kill-switch:** suspended if learned selector underperforms the manual-plan-selection baseline on held-out questions.
- **Owner:** Claude co-owns with native.
- **Dependency on other LL.M:** LL.4 stable.
- **Interaction with workstreams:** consumes CW.PPL outcomes tied to specific plan invocations.

#### LL.7 — Discovery prior shaping (multi-chart vs cohort disambiguation)

- **Input:** multi-chart signal co-occurrence records (from M7 cohort); classical-prior specifications.
- **Output:** Updated discovery priors in `06_LEARNING_LAYER/discovery_priors/` (scaffold-pending). Two regimes: (a) *native-only* mode (priors shaped by the native's own outcome record; single chart) — active from M4. (b) *cohort* mode (priors shaped by cohort signal co-occurrence) — active from M7 when cohort ≥ N. This distinction prevents conflating single-subject overfit (n=1) with cohort generalization.
- **Activation phase(s):** scaffold at M2; dormant at M3; native-only mode active from M4; cohort mode active from M7.
- **Kill-switch:** suspended if shaped priors violate learning-discipline rule #1 (classical priors must not be overwritten) or if cohort-mode produces distributions that shift the native-mode distribution more than a declared tolerance.
- **Owner:** native approves prior modifications in both modes; Claude co-owns; Gemini red-teams.
- **Dependency on other LL.M:** LL.1 stable for native-only mode; LL.10 not a hard prerequisite (fine-tune post-validation).
- **Interaction with workstreams:** consumes CW.LEL cross-cohort aggregates; consumes CW.PPL outcome summaries.

#### LL.8 — Bayesian model updating

- **Input:** DBN (M5 deliverable) parameters; observed outcomes from CW.PPL.
- **Output:** Updated posterior parameters; logged to `06_LEARNING_LAYER/bayesian_posteriors/` (scaffold-pending).
- **Activation phase(s):** scaffold at M4; active from M5.
- **Kill-switch:** suspended if posterior update shifts the DBN prior beyond a declared tolerance without warranted evidence; suspended globally if the model identifies on training data but fails held-out.
- **Owner:** native approves updating cadence; Claude co-owns; Gemini red-teams.
- **Dependency on other LL.M:** LL.1 through LL.7 stable (upstream features).
- **Interaction with workstreams:** consumes CW.PPL outcomes at every update.

#### LL.9 — Counterfactual learning from misses

- **Input:** PPL predictions that missed verification; per-miss forensic trace (which signals should have lit, which fired, which didn't).
- **Output:** Per-signal miss-attribution records in `06_LEARNING_LAYER/miss_registry/` (scaffold-pending); feeds LL.1 weight adjustments and LL.8 Bayesian updates.
- **Activation phase(s):** scaffold at M5; active from M6.
- **Kill-switch:** suspended if counterfactual attribution is dominated by a single signal repeatedly (indicating the attribution is spurious).
- **Owner:** Claude co-owns with native; Gemini red-teams.
- **Dependency on other LL.M:** LL.1, LL.8 stable.
- **Interaction with workstreams:** consumes CW.PPL miss records; feeds back into LL.1 and LL.8 updates.

#### LL.10 — LLM fine-tuning (prompt-level vs model-fine-tune disambiguation)

- **Input:** two distinct input regimes: (a) *prompt-level tuning* = systematic prompt-template refinement handled primarily in LL.4; listed under LL.10 only when operator wishes to pin a prompt-level change permanently via an instruction-tuning pass. (b) *model fine-tune* = true weight fine-tuning on a cohort-augmented corpus. (a) is not fine-tuning in the strict sense; it is LL.4 promotion. (b) is the fine-tuning activated at M10.
- **Output:** Fine-tuned model weights or instruction-tuning dataset, in `06_LEARNING_LAYER/finetuned_models/` (scaffold-pending).
- **Activation phase(s):** scaffold at M7; active from M10 (strict fine-tune). LL.4 promotion is always-on from M4.
- **Kill-switch:** suspended if fine-tuned model degrades acharya-grade score relative to prompt+base-model baseline on held-out chart probes; suspended globally if catastrophic forgetting of classical priors is detected.
- **Owner:** native approves fine-tune cadence and dataset composition; Claude co-owns training pipeline; Gemini red-teams.
- **Dependency on other LL.M:** LL.1 through LL.9 stable; cohort corpus (M7) required for meaningful fine-tune.
- **Interaction with workstreams:** consumes PPL+LEL aggregates across cohort subjects.

### §LL-Appendix.C — n=1 risk mitigation binding table

| Learning-discipline rule | Which n=1 risk it mitigates |
|---|---|
| #1 Priors locked; learning modulates, never overwrites | Catastrophic forgetting of classical knowledge under single-subject overfit |
| #2 Bayesian posterior framing, tight priors | Frequentist overfit to single-subject event sequence |
| #3 ≥N independent observations per update | Update-noise inflation (single event drives misleading weight shift) |
| #4 Held-out prospective data sacrosanct | Leakage-driven illusion of calibration |
| #5 Every parameter auditable, reversible, versioned | Stuck-with-bad-update (n=1 cannot self-correct without audit trail) |
| #6 Evidence earns right to modulate prior | Procrustean fitting of classical priors to idiosyncratic single-subject history |

### §LL-Appendix.D — Learning Layer ownership

Native is mechanism-introduction approver for every LL.N: no mechanism activates without explicit native sign-off on its rubric, kill-switch, and dependency map. Claude is mechanism-scaffolder: writes the register, the update pipeline, the shadow-mode gate, and the audit trail. Gemini is mechanism-critic in the red-team cadence (§IS.8): every third session and every macro-phase close, Gemini evaluates LL mechanism operation against learning-discipline rules and escalates any violation to native via the disagreement protocol (§3.4.C).

---

## The ten macro-phases

Every macro-phase below follows a fixed schema. Free-form prose has been replaced with structured rows. M3–M10 exit criteria are coarse-grained in MP; phase-opening sessions refine them into their own phase plans.

### M1 — Corpus Completeness

- **Scope:** Produce an L1 facts corpus at acharya-grade completeness (FORENSIC chart data unified), an L2.5 signals register (MSR), and an L2.5 Holistic Synthesis suite (UCN, CDLM, CGM, RM). No dynamics; no learning; pure reference corpus. *(Note: MSR was always an L2.5 artifact; "L2 signals register" in earlier drafts was a misclassification corrected in Phase 14F.)*
- **Entry state:** n/a — seed phase.
- **Exit state:** (a) CGM rebuilt on FORENSIC v8.0 ✓ (completed 2026-04-19 in GAP_RESOLUTION_SESSION Phase D); (b) all nine L3 Domain Reports at v1.1+ referencing only current L1 / L2.5 artifacts ✓ (completed 2026-04-19 per CLOSURE_AUDIT_PASS); (c) GAP.13 resolved ✓; (d) MSR v3.0 unified at 499 signals ✓ (2026-04-22); (e) UCN v4.0 current ✓; (f) CDLM v1.1 current ✓; (g) RM v2.0 current ✓; (h) FORENSIC v8.0 unified ✓. **Status: CLOSED as of 2026-04-19 per GAP_RESOLUTION_SESSION + CLOSURE_AUDIT_PASS; unification to MSR v3.0 at 499 signals on 2026-04-22 closes the final artifact pointer.**
- **Dependencies:**
  - requires: native's initial chart data; primary classical references.
  - produces: `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md`; `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md`; `025_HOLISTIC_SYNTHESIS/UCN_v4_0.md`; `025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md`; `025_HOLISTIC_SYNTHESIS/CGM_v2_0.md`; `025_HOLISTIC_SYNTHESIS/RM_v2_0.md`; nine L3 Domain Reports at v1.1+.
  - enables: M2, M3.
- **Deliverable paths:** `01_FACTS_LAYER/`; `025_HOLISTIC_SYNTHESIS/`; L3 Domain Reports per FILE_REGISTRY.
- **Risks:** empty — phase closed; residual risk (canonical-artifact drift between registries) migrated to §IS.1 and §IS.4 as substrate enforcement concerns.
- **Quality gate:** all eight exit-state items verified ✓; CLOSURE_AUDIT_PASS sealed on 2026-04-19.
- **Native-approval points:** MSR unification at 499 signals (approved 2026-04-22); L3 Domain Reports at v1.1+ sign-off (approved 2026-04-19).
- **Agent roles:** Claude-only for corpus production; native review gates each version bump; Gemini red-team (retroactive for closed phase).
- **Time/effort stance:** closed; no further envelope applies.
- **Ethics binding:** §3.5.A Principles (probabilistic humility applies to every signal's described manifestation); §3.5.E Pre-registration (LEL entries that precede M1 close are pre-registered as of LEL v1.2 timestamp).

### M2 — Corpus Activation (CURRENT)

- **Scope:** Turn the static M1 corpus into an LLM-navigable graph+vector substrate with Discovery Engine batch operations that surface patterns, resonances, contradictions, and clusters. This is the B.0–B.10 plan governed by `PHASE_B_PLAN_v1_0.md` (currently v1.0.2; see FILE_REGISTRY for CURRENT pointer).
- **Entry state:** M1 exit-state verified; PHASE_B_PLAN v1.0.2 active; Discovery Layer folder scaffolding present.
- **Exit state:** imported by reference from `PHASE_B_PLAN_v1_0.md §N` — the ten-point M2 exit list. MP does not duplicate; a session reads PHASE_B_PLAN §N for the authoritative list.
- **Dependencies:**
  - requires: M1 closed; Voyage-3-large (ED.3); Postgres + pgvector (ED.4); Claude Opus 4.7 (ED.6); Gemini 2.5 Pro (ED.5).
  - produces: graph database; vector index; Discovery Layer outputs; SESSION_LOG updates; FILE_REGISTRY updates.
  - enables: M3, M4.
- **Deliverable paths:** `02_ACTIVATION_LAYER/`; `04_DISCOVERY_LAYER/`; `00_ARCHITECTURE/SESSION_LOG.md` (updates); `00_ARCHITECTURE/FILE_REGISTRY_v1_0.md` (updates).
- **Risks:** imported by reference from `PHASE_B_PLAN §J` (16-risk table). Top three restated here for orientation: (R.1) vector-index drift between build passes → addressed by P1–P9 validator cascade; (R.2) Discovery Engine producing low-precision output at n=1 → addressed by two-pass red-team and shadow-mode Discovery outputs; (R.3) mirror-desync between Claude discovery outputs and Gemini connector outputs → addressed by §3.4.C Disagreement protocol + §IS.5 DISAGREEMENT_REGISTER. Full list in §J.
- **Quality gate:** all P1–P9 validators green + red-team T.1–T.7 pass + native acharya-grade review on 10 representative questions per PHASE_B_PLAN §N.
- **Native-approval points:** pattern-inclusion thresholds; contradiction-resolution class decisions; cluster-naming approvals.
- **Agent roles:** two-pass. Gemini connector (L4 Discovery Layer); Claude reconciler (produces canonical artifacts from Gemini connections). Per §3.4.
- **Time/effort stance:** envelope ≈ 30–60 sessions. Phase-indexed, not time-indexed; native declines hard dates per §3.8.A.
- **Ethics binding:** §3.5.A Principles (probabilistic humility on all surfaced patterns); §3.5.E Pre-registration (Discovery outputs are logged to PPL once they become forward-looking).

### M3 — Temporal Animation

- **Scope:** Add time. Compute Vimshottari + Yogini + Chara + Narayana dashas; cross-check dasha schools; compute transits; produce Varshaphala (Tajika); integrate KP sublord timing; compute shadbala over time. Produce a time-indexed event surface — for any date, which signals are lit, dormant, ripening.
- **Entry state:** M2 closed.
- **Exit state:** (coarse; refined in M3 opening session) — (a) Vimshottari + Yogini + Chara + Narayana dashas computed for native for lifetime horizon; (b) transit engine produces date-indexed signal lit/dormant/ripening states; (c) Varshaphala rectification completed; (d) KP sublord timing integrated with MSR signal system; (e) shadbala computed over full dasha horizon; (f) temporal validator meta-tests pass on held-out date sample.
- **Dependencies:**
  - requires: M2 closed; Swiss Ephemeris (ED.2) available at declared version; Jagannatha Hora exports (ED.1) available for cross-check.
  - produces: `05_TEMPORAL_ENGINES/` outputs (dasha tables, transit engine, shadbala computations, Varshaphala charts).
  - enables: M4, M5, M6.
- **Deliverable paths:** `05_TEMPORAL_ENGINES/`.
- **Risks:** (a) Swiss Ephemeris version-drift changes ayanamsha defaults → mitigation in ED.2 (version-lock + explicit ayanamsha declaration in SESSION_LOG); (b) dasha-lord disagreements across schools (Parashari Vimshottari vs Jaimini Chara) → mitigation: cross-check protocol at M3 open with native-arbitrated disagreement log, and M9 multi-school triangulation as the structural resolution; (c) Jagannatha Hora format incompatibility or deprecation → mitigation in ED.1 (freeze at last compatible export + pyswisseph fallback); (d) temporal validator meta-test false negatives → mitigation: Gemini red-team on validator before opening M3 close.
- **Quality gate:** all six exit-state items verified; temporal validator CI-green on held-out sample; native acharya-grade review on 5 date-specific chart readings.
- **Native-approval points:** ayanamsha selection if deviating from project default; disagreement resolution between Parashari and Jaimini dasha outputs at specific dates.
- **Agent roles:** Claude-only (deterministic computation). Two-pass applies only at validator review.
- **Time/effort stance:** envelope ≈ 10–20 sessions.
- **Ethics binding:** §3.5.A Principles; §3.5.E Pre-registration (temporal predictions logged to PPL at emission).

### M4 — Empirical Calibration

- **Scope:** Turn the Life Event Log (LEL) into the ground-truth spine. Every significant life event maps to which signals should have fired (per M3 temporal engine) and whether they did. Produce per-signal, per-domain calibration tables. First macro-phase where learning algorithms (LL.1–LL.7 active; LL.8 scaffold) fire on real data.
- **Entry state:** M3 closed AND CW.LEL ≥ 40 events spanning ≥ 5 years of native's history (minimum-volume gate per §Cross-cutting workstreams §CW.LEL).
- **Exit state:** (coarse) — (a) per-signal calibration tables produced with bootstrapped confidence intervals; (b) shadow-mode regime documented and enforced for all posterior updates; (c) n=1 validity disclaimer attached to outputs per §3.5.A Principle 1; (d) held-out LEL 20% partition passes calibration validity test; (e) LL.1–LL.7 per-mechanism shadow-to-production promotion criteria met.
- **Dependencies:**
  - requires: M3 closed; CW.LEL at minimum-volume gate; LL.1–LL.7 scaffolds (M2 deliverable) wired.
  - produces: `06_LEARNING_LAYER/` signal-calibration tables (LL.1 activation); edge-weight modulators (LL.2); embedding adapters (LL.3); prompt updates (LL.4); ranker weights (LL.5); plan-selector weights (LL.6); discovery priors in native-only mode (LL.7 mode-a).
  - enables: M5, M6.
- **Deliverable paths:** `06_LEARNING_LAYER/` (scaffolded in Step 11; populated in M4).
- **Risks:** (a) n=1 overfit → mitigation: Learning discipline #3 + shadow mode + §LL-Appendix.C binding table; (b) LEL entry bias (native selectively logs memorable events) → mitigation: §3.5.E Pre-registration + chronological-completeness audit at M4 open; (c) calibration-table staleness as new events arrive → mitigation: re-run at each M4 session close; (d) provisional-validity risk (calibration looks stable on interim LEL but degrades when next 40 events arrive) → mitigation: second-pass calibration at 80-event milestone.
- **Quality gate:** held-out LEL 20% partition passes calibration validity test (per-signal calibration error within declared tolerance on held-out).
- **Native-approval points:** calibration scoring rubric; shadow-mode exit rule (how many observations + what validity margin before a weight promotes out of shadow); LEL entry-bias audit resolution.
- **Agent roles:** two-pass (Gemini connector for LEL↔signal matching; Claude reconciler for calibration table production).
- **Time/effort stance:** envelope ≈ 40–100 sessions (heaviest phase for learning loop stabilization).
- **Ethics binding:** §3.5.A Principles (especially 1 probabilistic humility; 2 truth-in-advertising); §3.5.E Pre-registration (LEL entries are pre-registered at their timestamps); §3.5.G Calibration disclosure.

### M5 — Probabilistic Model

- **Scope:** Dynamic Bayesian Network over (signals × time) → (life-domain outcomes). Signal embeddings become learned vectors. Outputs become probabilities with confidence intervals.
- **Entry state:** M4 closed (calibration tables stable; LL.1–LL.7 active).
- **Exit state:** (coarse) — (a) DBN identifies on held-out data (LEL 20% partition); (b) signal embeddings stable across 3 refit runs; (c) Bayesian posterior framing applied to all outputs; (d) DBN topology approved by native; (e) prior specification documented and approved.
- **Dependencies:**
  - requires: M4 calibration tables; M3 temporal engine; LL.1–LL.8 scaffold (LL.8 activates in M5).
  - produces: DBN spec + parameters file (path TBD in M5 open; likely `06_LEARNING_LAYER/dbn/`).
  - enables: M6, M8, M9.
- **Deliverable paths:** `06_LEARNING_LAYER/dbn/` (tentative; finalized in M5 open).
- **Risks:** (a) prior specification bias → mitigation: Bayesian discipline + two-pass Gemini/Claude prior review; (b) DBN under-identification at n=1 → mitigation: shadow mode + M7 re-fit plan; (c) learned-vs-classical divergence → mitigation: LL discipline #1 (priors locked) + divergence-alert threshold; (d) topology overfit to LEL history → mitigation: held-out M4 partition as topology validation set.
- **Quality gate:** held-out DBN identifies within declared tolerance; signal embeddings refit-stable across 3 runs; native approves topology + prior.
- **Native-approval points:** DBN topology; prior specification; confidence-interval reporting policy.
- **Agent roles:** two-pass. Gemini on topology proposals + prior elicitation; Claude on fit + validation.
- **Time/effort stance:** envelope ≈ 20–40 sessions.
- **Ethics binding:** §3.5.B Disclosure tiers (outputs carry confidence bands); §3.5.G Calibration disclosure.

### M6 — Prospective Testing

- **Scope:** Forward predictions with falsifiable windows. Automated scoring at window close. Counterfactual learning from misses (LL.9 activates). The only real accuracy measurement in the system.
- **Entry state:** M5 closed AND CW.PPL ≥ 50 predictions with ≥ 6-month horizon elapsed (minimum-volume gate per §Cross-cutting workstreams §CW.PPL).
- **Exit state:** (coarse) — (a) ≥ 50 verification windows closed and scored; (b) automated scoring reproducibility verified (re-running produces identical verdicts); (c) counterfactual learning registry populated (LL.9 active); (d) forward prediction validity declared for at least one life-domain; (e) calibration drift monitored and within declared tolerance.
- **Dependencies:**
  - requires: M5 closed; CW.PPL at minimum-volume gate.
  - produces: `07_PROSPECTIVE_TESTING/` scoring dashboards + counterfactual learning registry.
  - enables: M7, M8, M9.
- **Deliverable paths:** `07_PROSPECTIVE_TESTING/`.
- **Risks:** (a) verification-window drift (native retrofits window boundaries) → mitigation: fixed windows set at prediction emission, never modifiable; (b) post-hoc rationalization of near-misses as hits → mitigation: pre-registration from §3.5.E + rubric-bound verdicts; (c) selection bias in which predictions get emitted → mitigation: coverage tracking against MSR signal categories; (d) time-gated phase — cannot be compressed → mitigation: parallelize with M8 once M8 entry state (M5 closed) is met.
- **Quality gate:** ≥ 50 verification windows closed; automated scoring reproducibility verified; calibration drift within tolerance.
- **Native-approval points:** verdict for edge cases (partial-match, delayed-match, ambiguous-domain); inclusion/exclusion of specific predictions from scoring.
- **Agent roles:** two-pass. Claude emits predictions; Gemini scores; native arbitrates edge-case verdicts.
- **Time/effort stance:** **time-gated** (not session-gated; requires elapsed calendar time for verification windows to close). Per §3.8.B and §3.8.C.
- **Ethics binding:** §3.5.A Principle 1 (probabilistic humility); §3.5.B Disclosure tiers; §3.5.E Pre-registration (PPL emission-time timestamp is the pre-registration seal).

### M7 — Population Extension

- **Scope:** Cohort beyond this native — family, public figures with reliable birth data, a research corpus. Desha-kala-patra (place-time-person) modulators learned. Fine-tuning of LLM components becomes feasible for the first time (LL.7 cohort mode activates; LL.10 scaffold).
- **Entry state:** M6 closed AND ethical review complete per §3.5.D (consent protocol operational; per-subject consent obtained for each admitted subject).
- **Exit state:** (coarse) — (a) ≥ N consented subjects added (N ≥ 5 recommended; exact value set in M7 open); (b) per-subject calibration tables match the method-extension validity test; (c) cohort modulators (desha-kala-patra) produced; (d) LL.10 cohort corpus assembled; (e) cohort-mode LL.7 active per §LL-Appendix.A.
- **Dependencies:**
  - requires: M6 closed; IRB-style consent workflow operational per §3.5.D; cohort subject registry scaffold; birth-data rectification pipeline.
  - produces: cohort subject registry (path TBD in M7 open); per-subject L2.5 corpora; desha-kala-patra modulators; cohort-augmented corpus for LL.10.
  - enables: M8 (via expanded classical attribution dataset); M9; M10.
- **Deliverable paths:** cohort subject registry (path TBD); per-subject L2.5 under a cohort subfolder convention.
- **Risks:** (a) birth-time accuracy variance → mitigation: require ≥ A-grade rectification per admitted subject; reject sub-A-grade into an excluded-subject register; (b) consent privacy for public figures → mitigation: explicit consent required; no public figures without consent; (c) anonymization vs attribution trade-off → mitigation: default to anonymization unless subject consents to attribution per §3.5.D; (d) desha-kala-patra modulator overfit on small cohort → mitigation: shadow mode N≥3 observations per modulator; (e) LLM fine-tuning catastrophic forgetting → mitigation: fine-tune only after method-extension validity confirmed AND classical-prior regression test passes.
- **Quality gate:** ≥ N consented subjects (N set at M7 open); method-extension validity test passes; classical-prior regression test passes (fine-tune does not degrade classical baseline).
- **Native-approval points:** cohort inclusion criteria; per-subject consent validation; fine-tune go/no-go decision; fine-tune dataset composition.
- **Agent roles:** two-pass. Gemini proposes cohort admissions; Claude validates consent + rectification grade; native approves each admission.
- **Time/effort stance:** envelope ≈ 30–60 sessions per added subject (front-loaded on corpus build).
- **Ethics binding:** §3.5.D Consent protocol for M7 cohort; §3.5.F Minor/vulnerable-population stance (exclude minors absolutely; exclude active crisis); §3.5.B Disclosure tiers (cohort-subject tier).

### M8 — Classical Text Cross-Reference

- **Scope:** Indexed corpus of BPHS, Phaladeepika, Saravali, Uttara Kalamrita, Jaimini Sutra, Prashna Marga, Hora Sara, KP texts, Brihat Jataka, Brihat Samhita, and selected KP commentaries. Every discovered pattern cross-referenced to classical attribution. Where classical claims systematically hold or fail becomes a finding in itself.
- **Entry state:** M5 closed. **M7 is not a prerequisite** for M8 kickoff; M7 and M8 may overlap per §3.8.C Sequencing stance.
- **Exit state:** (coarse) — (a) all listed corpora indexed and attributed; (b) classical-claim-holds/fails findings produced for each M5 probabilistic output; (c) attribution confidence tags populated for every citation; (d) translation-accuracy cross-check completed for non-English classical sources; (e) MSR signal-set expanded to include Nadi + BNN school signals as a pre-M9 requirement (per MPC.2.6 resolution; enables M9 multi-school triangulation; Nadi/BNN classical basis sourced from the §3.7 acharya pool's tradition-specific consultants where corpora are not procurable under ED.7).
- **Dependencies:**
  - requires: M5 closed (calibrated signal weights needed for attribution); classical corpora procurement (ED.7).
  - produces: classical attribution registry; classical-claim validity table; MSR signal-set expanded for Nadi + BNN schools.
  - enables: M9; M10.
- **Deliverable paths:** `08_CLASSICAL_CROSS_REFERENCE/` (path finalized in M8 open).
- **Risks:** (a) classical corpora procurement (rare texts unavailable) → mitigation: shortlist produced in M8 kickoff with priority tiers (BPHS and Phaladeepika tier 1; others tier 2–3 based on attribution demand); (b) translation accuracy for non-Sanskrit sources → mitigation: multi-source translation cross-check; native's Sanskrit literacy as final arbiter for ambiguous passages; (c) attribution ambiguity in BPHS compilation chapters (multiple attributed authors) → mitigation: explicit attribution confidence flag per citation; (d) classical-claim-failure reputational surface (findings may challenge widely-held claims) → mitigation: explicit disclosure stance per §3.5.B — findings are findings, not attacks on tradition.
- **Quality gate:** native acharya-grade review of attribution accuracy on 20 representative findings; translation cross-check passes for all non-English sources.
- **Native-approval points:** classical corpus shortlist; disclosure policy for classical-claim-failure findings; attribution confidence threshold.
- **Agent roles:** two-pass. Gemini proposes attributions; Claude validates against source text; native arbitrates ambiguity.
- **Time/effort stance:** envelope ≈ 40–80 sessions.
- **Ethics binding:** §3.5.B Disclosure tiers (classical-literature tier — findings published with attribution, translations cited, disagreements logged).

### M9 — Multi-School Triangulation

- **Scope:** Parashari + Jaimini + Tajika + KP + Nadi + BNN + Yogini operating on a shared signal set. Convergence across lenses as a precision signal; divergence as a finding. Humans cannot do this live; the instrument can.
- **Entry state:** M8 closed AND MSR coverage expansion for Nadi + BNN schools completed (per §7 MPC.2.6; MSR expansion owned by M8 as part of its classical-attribution scope so that Nadi and BNN signal sets exist before M9 opens).
- **Exit state:** (coarse) — (a) all seven schools operating on shared signal set; (b) inter-school convergence metrics calibrated; (c) school-disagreement resolution protocol populated with ≥ N worked examples; (d) convergence-as-precision-signal evidence logged.
- **Dependencies:**
  - requires: M8 closed; MSR expansion to Nadi + BNN; M7 closed is not required for M9 kickoff.
  - produces: multi-school convergence scoring artifact; school-disagreement register.
  - enables: M10.
- **Deliverable paths:** `09_MULTI_SCHOOL_TRIANGULATION/` (path finalized in M9 open).
- **Risks:** (a) spurious convergence from shared underlying data (all schools derive from the same chart) → mitigation: cross-school signal-provenance tracking; (b) operator-preference collapse on disagreement (Claude/Gemini "defaults" to Parashari) → mitigation: explicit inter-school weights learned, not assigned; native arbitrates; (c) novel inter-school calibration instability → mitigation: shadow mode for convergence metrics.
- **Quality gate:** convergence metrics stable across refit runs; school-disagreement register entries have native-approved resolutions.
- **Native-approval points:** inter-school weight assignments before they go to learned mode; disagreement-resolution verdicts.
- **Agent roles:** two-pass + acharya consultation on disagreement cases. Gemini proposes cross-school matches; Claude validates; native + acharya arbitrate.
- **Time/effort stance:** envelope ≈ 20–40 sessions.
- **Ethics binding:** §3.5.A Principles 1, 5 (probabilistic humility; red-team oversight); §3.5.B Disclosure tiers (acharya tier).

### M10 — LLM-Acharya Interface and External Validation

- **Scope:** Full wiring. Blind-test against independent acharyas reading the same chart. Publish the methodology. Project-exit phase — project-done = M10 exit state per §3.9.D retirement criteria.
- **Entry state:** M9 closed AND acharya-reviewer panel ≥ 3 acharyas recruited per §Acharya Reviewer Pool Policy.
- **Exit state:** (coarse) — (a) wiring inventory complete (all L4 prompt templates live; UCN at its final version; cohort modulators integrated; LL.10 fine-tune validated); (b) acharya-reviewer panel ≥ 3 active; (c) at least one blind-test report produced and native-published; (d) methodology published — target: arXiv preprint minimum; peer-reviewed journal submission as stretch goal; (e) LL-Appendix activation state shows LL.1–LL.10 all `active`.
- **Dependencies:**
  - requires: M9 closed; acharya panel recruited; publication-venue decision.
  - produces: `99_PUBLICATIONS/`; LLM-acharya interface spec; blind-test reports.
  - enables: Post-M10 Framing transitions (§Post-M10 Framing).
- **Deliverable paths:** `99_PUBLICATIONS/`; `10_LLM_ACHARYA_INTERFACE/` (path finalized in M10 open).
- **Risks:** (a) acharya availability → mitigation: recruitment via native network; honorarium policy per §3.7.B; (b) reviewer disagreement → mitigation: disagreement protocol from §3.4 + §3.7.E (both views logged, not averaged); (c) publication-venue risk (peer-reviewed rejection) → mitigation: fallback to arXiv + native blog; (d) reputational exposure (project produces findings that challenge classical or institutional positions) → mitigation: disclosure-tier stance per §3.5.B; native controls publication scope.
- **Quality gate:** wiring inventory complete; ≥ 1 blind-test report; publication submitted to declared venue; acharya-grade composite score at M10 close meets native-approved threshold.
- **Native-approval points:** acharya shortlist; honorarium budget; publication-venue selection; publication scope (full methodology vs redacted).
- **Agent roles:** two-pass + native + acharya. Native is primary owner at M10.
- **Time/effort stance:** envelope ≈ 20–40 sessions plus acharya coordination time (may extend to 2–4 weeks elapsed per acharya review cycle).
- **Ethics binding:** §3.5.B Disclosure tiers (acharya-reviewer tier; hypothetical-public-consumer tier for post-M10 release); §3.5.A full principles block.

---

## Cross-cutting workstreams

Two workstreams run in parallel with code macro-phases. The schema is extensible; additional workstreams may be added per §Meta-Governance.

### CW.LEL — Life Event Log

- **Scope:** Chronological, structured record of significant events in the native's life, each with date, domain, signal-attribution candidates, and chart-state context at the event date.
- **Cadence:** Session-close checkpoint. Native reviews any new-since-last-session events at close; Claude validates schema at session close. Drift-alert if the last entry is > 14 days old.
- **Owner:** Native authors; Claude validates schema at session close.
- **Schema pointer:** `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (current at v1.2; upgraded at native's cadence).
- **Entry-point:** LEL entry template (path: `01_FACTS_LAYER/LEL_ENTRY_TEMPLATE_v1_0.md`, created on first new entry after v2.0 publication per Step 5 propagation cascade; if not yet present, native creates entries inline in LEL file and Claude retrofits the template).
- **Activation:** Always on from Session 2 onward (current state per CLAUDE.md; LEL v1.2 contains 36 events + 5 period summaries + 6 chronic patterns per GA.9).
- **Duration envelope:** Project lifetime.
- **Feeds into:** [M4 (calibration), M7 (cohort-mode calibration via native-as-subject cross-reference), M9 (multi-school inter-school score tests)].
- **Minimum-volume gate (for feeds_into unlock):** M4 requires ≥ 40 LEL events spanning ≥ 5 years.
- **Failure modes:** Native skips weeks (→ §IS.6 drift-detector flags); Claude forgets to validate at session close (→ §IS.7 session-close checklist); LEL entry bias (→ audit at M4 open per M4 Risks (b)).
- **Freshness / staleness detection:** Drift-alert if last entry > 14 days old.
- **Ethics binding:** §3.5.E Pre-registration (entries timestamped at first entry; post-hoc edits flagged); §3.5.D Consent (native is self-consenting subject).

### CW.PPL — Prospective Prediction Log

- **Scope:** Every falsifiable claim the system surfaces logged at emission with a verification window. The first six months of this data cannot be manufactured later. Pre-registration of predictions so post-hoc rationalization is structurally excluded.
- **Cadence:** Every falsifiable prediction logged at emission — not later. Drift-alert if Discovery Engine produces forward-looking output in a session without a matching PPL entry in the same session.
- **Owner:** Claude authors entries; native approves before commitment; Gemini independently reviews for falsifiability crispness.
- **Schema pointer:** `07_PROSPECTIVE_TESTING/PROSPECTIVE_PREDICTION_LOG_v1_0.md` (path tentative; finalized at scaffold in M2 close).
- **Entry-point:** Prediction-log template (path TBD; created alongside schema pointer at M2 close).
- **Activation:** Scaffolded at M2 close (register exists). Active from first M5 probabilistic output (once predictions carry probabilistic framing).
- **Duration envelope:** Project lifetime.
- **Feeds into:** [M6 (prospective testing), M9 (multi-school inter-school score tests via forward predictions)].
- **Minimum-volume gate (for feeds_into unlock):** M6 requires ≥ 50 predictions with ≥ 6-month horizon elapsed.
- **Failure modes:** Claude forgets to log a prediction (→ §IS.7 session-close checklist — every forward-looking output requires a matching PPL entry in the same session); native bypasses approval (→ audit-trail flags); post-hoc rationalization (→ §3.5.E pre-registration; windows locked at emission).
- **Freshness / staleness detection:** Drift-alert if a session produces Discovery output without matching PPL entry.
- **Ethics binding:** §3.5.A Principle 1 (probabilistic humility); §3.5.E Pre-registration (emission-time timestamp is the pre-registration seal).

---

## Scope Boundary

### Session-scope discipline

A session executes exactly one scoped task. During the Step 0→15 governance rebuild, that is exactly one Step from the STEP_LEDGER. After the rebuild closes, that is exactly one sub-phase of M2 (during M2), or one sub-phase of M_N (during M_N). A session does not pre-build, does not expand scope mid-session, and updates SESSION_LOG at close per §IS.7. It may surface scope-adjacent findings as SESSION_LOG notes, but it does not act on them within the same session.

### Macro-phase scope discipline

A macro-phase M_N executes exactly the scope declared in its row in §The ten macro-phases. It does not expand scope to other macro-phases. Cross-cutting substrates (Learning Layer, System Integrity) may be scaffolded or activated during M_N per their activation matrices (§LL-Appendix.A for Learning Layer; §IS.1–§IS.9 for Integrity Substrate). No M_N-unrelated macro-phase may be started in the middle of M_N. Sequencing stances (e.g., M7/M8 overlap) are per §3.8.C.

### Enforcement

Scope discipline is mechanical, not procedural, per GA.13 ("a procedural rule that has been broken once will be broken again"). The session-open handshake (§IS.7; Step 7 deliverable — `SESSION_OPEN_TEMPLATE`) requires the session to declare its scope before action. The drift detector (§IS.6; Step 7 deliverable — `drift_detector.py`) flags sessions that touch files outside the declared scope. Neither can be skipped by honor-system assertion; both are gate-checked at session close.

---

## Multi-Agent Collaboration

### §3.4.A Current agents

- **Claude Opus 4.7** — reconciler / primary. Produces canonical artifacts; owns versioning discipline; owns the governance-rebuild workflow. Model identifier pinned at session open per §3.4.F.
- **Gemini 2.5 Pro** — connector / critic. Operates the L4 Discovery Layer; proposes connections, patterns, resonances; red-teams Claude's outputs at every third session and at every macro-phase close per §IS.8. Model identifier pinned at session open per §3.4.F.

### §3.4.B Two-pass protocol

The default for multi-output phases is two-pass: Gemini proposes; Claude reconciles and produces canonical artifacts. The default for deterministic computation phases (dasha/transit computation, corpus integrity validators) is single-pass Claude-only. Per-phase mapping lives in each macro-phase row's `Agent roles` field (§The ten macro-phases); MP does not duplicate it here.

### §3.4.C Disagreement protocol

When agents reach conflicting conclusions, the disagreement is logged to `DISAGREEMENT_REGISTER` (Step 7 deliverable; §IS.5 points to it). Arbitration sequence:

1. Re-run each agent in isolation to verify stability of each's output.
2. Claude-reconciler attempts resolution with explicit rationale recorded alongside the disagreement entry.
3. If still unresolved, escalate to native for resolution; native's resolution is logged with its own rationale.
4. **Mirror-desync (per ND.1 / §IS.2) is treated as an implicit disagreement class** — requires resolution via this same protocol, not silent overwriting. When one side of a mirror pair has diverged from its counterpart, the divergence is logged as a disagreement, the authoritative side is identified, and the non-authoritative side is updated via adapted parity.

### §3.4.D Quality gate for agent output per phase

Pass-criterion for agent output at each phase is declared in the macro-phase row's `Quality gate` field (§The ten macro-phases). MP does not restate per-phase criteria in this section; it points to §The ten macro-phases as the single source.

### §3.4.E Future-agent admission policy

Admission of any third agent (future Gemini version; domain-specific model; human-in-the-loop reviewer with tooling privileges) requires: (1) a red-team session dedicated to the admission; (2) a version bump of MP; (3) updates to all mirror-pairs per §IS.2 Mirror Discipline; (4) update to this §3.4.A Current agents list; (5) an entry in STEP_LEDGER tracking the admission workflow.

### §3.4.F Version-pinning discipline

SESSION_LOG records model identifiers at every session open. Model-family migration (e.g., Claude Opus 4.7 → Opus 5.0; Gemini 2.5 Pro → Gemini 3.0) follows the §Meta-Governance protocol with an explicit red-team session dedicated to the migration. Mid-phase migration is disallowed absent native override. Cross-reference in §3.6.D.

---

## Ethical Framework

The instrument will eventually make probabilistic life-domain predictions. Who is allowed to consume them, under what disclosures, and with what guardrails is not an afterthought — it is a structural binding that M4, M6, M7, and M10 each take operational dependency on.

### §3.5.A Principles

1. **Probabilistic humility.** Outputs are probabilities, not certainties; confidence bands are always attached.
2. **Truth-in-advertising.** Calibration figures (accuracy rates, false-positive rates, bounded validity) are disclosed alongside predictions.
3. **No self-harm-adjacent output without guardrail.** Mortality-domain, mental-health domain, and health-crisis domain outputs require double red-team and are subject to §3.5.C.
4. **Consent required for non-native subjects.** Any M7 cohort subject requires explicit informed consent before any L2+ output is produced about them.
5. **Red-team oversight.** Every predictive output is subject to the red-team cadence (§IS.8).
6. **Reversibility.** Every output is rescindable if calibration data reveals it was unfounded.

### §3.5.B Disclosure tiers

Four consumer audiences, each bound to a disclosure protocol:

- **Native self.** Full output; full calibration disclosure; unfiltered.
- **Cohort subject (M7).** Consent-gated; same disclosure tier as native; subject may request redactions; subject retains right to withdrawal + deletion.
- **Acharya reviewer (M10).** Full methodology; subject chart data; native consent required before acharya sees identifying data; anonymization optional and subject's choice.
- **Hypothetical public consumer (post-M10).** Redacted; aggregated; calibration bands mandatory; no individual-fate-adjacent claims; publication follows §3.9.B.

### §3.5.C Self-harm guardrail

- **No date-of-death output** for any subject under any audience tier. Probabilistic mortality-window outputs are subject to double red-team and limited to aggregate statistical framing; individualized mortality windows are disallowed.
- **Health-crisis output requires double red-team** and explicit native sign-off before any output leaves a session.
- **Suicide-adjacent output** (ideation signals, self-harm-adjacent house/lord combinations) is disallowed under all audience tiers.
- **Mental health domain output** is subject to the same double red-team + native sign-off as health crisis.

### §3.5.D Consent protocol for M7 cohort

Each added subject requires:

1. Written informed consent describing the method and the retention policy (data storage location, access controls, retention duration, destruction procedure).
2. Subject's right to withdraw and to request deletion of their L2+ corpus; withdrawal is logged, deletion is verified, disagreement-register entry opened if there is any dispute over scope of deletion.
3. Explicit anonymization-vs-attribution choice — default anonymous; attribution only if subject actively elects.
4. Minor / vulnerable-population exclusion per §3.5.F.

### §3.5.E Pre-registration / blinding

- LEL entries are timestamped at first entry. Post-hoc edits are flagged in the audit trail (who, when, what changed, rationale).
- Prospective predictions are locked at emission. The PPL entry timestamp is the pre-registration seal; the verification window is fixed at emission and never modifiable.
- Native cannot revise a prediction after outcome is known.

### §3.5.F Minor / vulnerable-population stance

The M7 cohort excludes minors (< 18 years of age) absolutely. Subjects with active mental-health crisis or cognitive impairment that would prevent informed consent are excluded from cohort. Exclusions are logged in an excluded-subject register (no corpus produced; no analysis performed).

### §3.5.G Calibration disclosure

All M5/M6 outputs carry calibration band disclosure:

- Point estimate;
- Confidence interval;
- Method pointer (which LL.N produced the estimate);
- Known failure modes (linked to §3.5.A Principle 2).

Outputs without a calibration band attached are not valid outputs; the PPL entry is rejected by schema validator.

### §3.5.H Mode A / Mode B linkage

`PROJECT_ARCHITECTURE` defines Mode A (curated) and Mode B (exhaustive) interaction modes with the instrument. Disclosure tier applies identically across modes; Mode B's volume does not relax any of §3.5.A through §3.5.G. Every Mode B output carries the same calibration and consent discipline as Mode A.

---

## External Dependency Graph

### §3.6.A Dependency table

| ID | Name | Category | Used-by-phase(s) | Failure mode | Contingency | SPOF |
|---|---|---|---|---|---|---|
| ED.1 | Jagannatha Hora | tool | M1, M3 | Format incompatibility or deprecation | Freeze at last compatible export; migrate to pyswisseph for affected fields | partial |
| ED.2 | Swiss Ephemeris | service | M3, M6 | Version bump changes ayanamsha defaults | Version-lock at deployment; explicit ayanamsha declaration in SESSION_LOG | yes |
| ED.3 | Voyage-3-large | model | M2+ | Deprecation; cost | Re-embed corpus on fallback embedding model with documented schema migration | yes |
| ED.4 | Postgres + pgvector | service | M2+ | Version bump; schema drift | Migration scripts versioned alongside schema; rollback plan per migration | yes |
| ED.5 | Gemini 2.5 Pro | model | M2+ | Unavailability; budget cap | Two-pass protocol collapses to one-pass Opus; red-team cadence doubles | no (degrades, doesn't block) |
| ED.6 | Claude Opus 4.7 | model | M2+ | Unavailability; Anthropic deprecation | Sonnet fallback with explicit capability downgrade logged; pause-until-available for high-stakes passes per §3.8.G | partial |
| ED.7 | Classical text corpora (BPHS, Phaladeepika, Saravali, Uttara Kalamrita, Jaimini Sutra, Prashna Marga, Hora Sara, Brihat Jataka, Brihat Samhita, selected KP commentaries) | corpus | M8 | Rare-text procurement; translation accuracy | Shortlist + priority tiers at M8 kickoff; multi-source translation cross-check; native's Sanskrit literacy as final arbiter | corpus-by-corpus (tier-1 yes; tier-2+ partial) |
| ED.8 | Acharya reviewer pool | human-role | M10 | Availability; disagreement | Cross-referenced to §Acharya Reviewer Pool Policy | yes |
| ED.9 | Subject-level data storage | service | all phases | GDPR-style compliance; retention; breach | Data-retention policy per §3.5.D; legal review before M7 cohort open; at-rest encryption baseline | partial |

### §3.6.B SPOF mitigation cadence

Rows flagged `SPOF: yes` (ED.2 Swiss Ephemeris; ED.3 Voyage-3-large; ED.4 Postgres+pgvector; ED.8 Acharya reviewer pool) are reviewed at every macro-phase close plus an annual independent check. The review produces an SPOF-status row in SESSION_LOG for each reviewed dependency, with any contingency-readiness changes surfaced immediately. Rows flagged `SPOF: partial` (ED.1 Jagannatha Hora; ED.6 Claude Opus; ED.9 Subject-data storage) are reviewed at every macro-phase close only. Rows flagged `SPOF: no` (ED.5 Gemini) are reviewed at annual cadence only.

### §3.6.C Licensing and legal status

Classical corpora licensing — public-domain originals (BPHS, Brihat Jataka, Brihat Samhita); copyrighted modern translations handled via citation-only fair use; where a full modern translation is load-bearing, a license is obtained. Cohort data posture follows GDPR-style principles even if not strictly required by native's jurisdiction: data minimization, consent-gated processing, retention limits, subject access rights, right to deletion. Publication licensing at M10 — default CC-BY for methodology; subject data never published without subject's explicit attribution consent.

### §3.6.D Model-family migration policy

Cross-reference to §3.4.F. No duplication here. A model-family migration is a structural event that requires its own red-team + MP version bump.

---

## Acharya Reviewer Pool Policy

### §3.7.A Recruitment channel

Native's own network is the primary channel. Criteria: ≥ 15 years practice; demonstrable classical (non-psychological) Jyotish grounding; willingness to participate in blind-test protocol; no prior commercial or personal relationship with native that would compromise independence. Minimum panel size for M10 opening: **n ≥ 3**.

### §3.7.B Honorarium stance

Default recommendation: **paid per-review** with a bounded hourly rate, native-discretion override (native may elect unpaid peer-review norm if appropriate for a specific reviewer). Honorarium budget is declared at M10 open and logged in GOVERNANCE_STACK as a project-cost event.

### §3.7.C Review protocol pointer

Protocol details live in `ACHARYA_ENGAGEMENT_KIT.md` (existing file per GA.11). MP does not duplicate its contents; M10 kickoff session updates the engagement kit to current MP v2.0 terminology before recruitment.

### §3.7.D Retention plan

Annual review of panel membership; refresh panel if a reviewer withdraws. Maintain at minimum **n = 3** at all times during M10 open state. Falling below n = 3 triggers an M10 blocker per §3.10.A revision-trigger (b) and invokes pause protocol per §3.8.G.

### §3.7.E Disagreement protocol among reviewers

If two acharyas reach opposite conclusions on the same chart, both verdicts are logged to the reviewer-disagreement register (not averaged). The disagreement becomes a finding in its own right — a data point about inter-acharya interpretive variance. Native + at least one additional acharya reviews the disagreement entry and decides whether it warrants further triangulation via M9 multi-school lenses or is left as an open finding.

---

## Time/Effort Stance

### §3.8.A Phase-indexed, not time-indexed

The project is governed by phase progression, not calendar deadlines. The native declines to commit to target dates. MP does not ship Gantt charts. Hard deadlines, where they arise (e.g., Swiss Ephemeris version-lock deadlines tied to upstream releases), are handled at the macro-phase level inside the relevant phase row's `Risks` field and do not create project-wide date commitments.

### §3.8.B Session-volume envelopes

These are rough ranges, not commitments:

- M1 ≈ closed (n/a retrospective envelope).
- M2 ≈ 30–60 sessions.
- M3 ≈ 10–20 sessions.
- M4 ≈ 40–100 sessions (heaviest phase).
- M5 ≈ 20–40 sessions.
- M6 time-gated (requires elapsed calendar time for verification windows, not session count).
- M7 ≈ 30–60 sessions per added subject.
- M8 ≈ 40–80 sessions.
- M9 ≈ 20–40 sessions.
- M10 ≈ 20–40 sessions plus acharya coordination elapsed time.

### §3.8.C Sequencing stance

M1 → M2 → M3 → M4 → M5 → M6 are serial. M7 and M8 may run with partial overlap (M8 can begin once M5 produces calibrated weights; M7 can begin once M6 produces prospective validity; their entry states are independent, not serial). M9 can begin once M8 closes; M9 requires M8. M10 serializes again — M10 requires M9 closed.

### §3.8.D Concurrent workstream duration

CW.LEL spans project lifetime (always on from Session 2). CW.PPL spans from first M5 probabilistic output through project lifetime. Per §Cross-cutting workstreams.

### §3.8.E Budget envelope pointer

MP does not carry cost envelopes inline. A separate budget artifact is created if/when native elects; until then, costs are logged per-session in SESSION_LOG where material. The pointer is declared here; the artifact is out-of-scope for Step 3.

### §3.8.F Native time cadence

Daily sessions (per CLAUDE.md). Pause protocol in §3.8.G.

### §3.8.G Pause protocol

At session close, Claude produces a handoff note sufficient for resumption weeks later — session-close checklist (§IS.7) is the paradigm. If native is unreachable for > 14 days, Claude pauses at the current phase-close boundary and does not begin a new phase. If native is unreachable mid-phase, Claude continues to the nearest natural session-close boundary and then pauses. `SESSION_OPEN_TEMPLATE` (Step 7) enforces pause-resume discipline: a resumed session must cite the last seal and confirm no drift has been introduced by the pause. Unavailable-handoff protocol is the same as pause protocol.

---

## Post-M10 Framing

### §3.9.A Maintenance mode

Post-M10, the corpus is a living artifact. Scheduled drift-detector runs (§IS.6 cadence) continue. Annual red-team continues (§IS.8 cadence + §3.10.C). LEL continues as native's lived record. PPL continues as the forward-prediction registry. Learning Layer mechanisms remain active per the LL-Appendix.A activation matrix (all `active` at M10 close).

### §3.9.B Publication

Methodology is published at M10 close per M10's exit criteria — arXiv preprint minimum; peer-reviewed journal submission as stretch goal. Subject-specific corpus remains private unless native grants permission (§3.5.B public-consumer tier). Classical cross-reference findings (M8) publish independently if warranted; native makes the publication-scope call.

### §3.9.C Ownership and handoff

Default: native retains full ownership of the project, its corpus, and its outputs. If native wishes to share or transfer (e.g., to an institutional steward or a successor owner), a dedicated handoff session is opened with its own red-team, its own MP amendment (version bump required), and its own mirror-pair update cascade.

### §3.9.D Retirement criteria

Project enters review-not-publication mode if any of: (a) acharya panel rejects the corpus at M10 close on substantive grounds; (b) calibration drops below stated floor for ≥ 2 consecutive review cycles; (c) native decides to retire the project. Retirement is **reversible** — a retired project may re-open at a subsequent version bump. M10 exit state = project-done in the closure sense; project-done does not mean project-gone. Retirement is a governance event, not a technical one.

### §3.9.E Versioning policy post-M10

MP v2.0 remains current until a new substrate or a new macro-phase is admitted. Post-M10 events may trigger MP v3.0 (e.g., second-native expansion; cross-cultural extension; commercialization path). Post-M10 events do NOT trigger v2.1-style additive bumps; they either fit within v2.0 (no bump) or they require v3.0. Version-semantics definitions are in §3.10.D.

---

## Meta-Governance

### §3.10.A Revision triggers

MP is revised when any one of the following occurs:

(a) Any macro-phase red-team rejects the phase (the rejection implies an MP claim about that phase is wrong).
(b) Any close-criterion fails across two sessions in a row (systemic failure, not one-off).
(c) Any P1–P9 validator cascade fails after having passed (regression in corpus integrity).
(d) Native issues a new ND.N directive requiring structural change.
(e) A new substrate or macro-phase is admitted.
(f) Annual red-team of MP surfaces structural defects (≥ 1 CRITICAL or ≥ 3 HIGHs).

Any one of these is sufficient. Revision workflow follows §3.10.B.

### §3.10.B Approval protocol

Proposed revision → Revision spec (a Step-2-style artifact, versioned separately as `MACRO_PLAN_REVISION_SPEC_vX_Y.md`) → Red-team on the spec (Step-4-style artifact) → Native approval → Version bump → Mirror update per §IS.2 across all affected surfaces → STEP_LEDGER entry (or the steady-state equivalent after the rebuild) → SESSION_LOG entry. No short-circuiting this chain; revisions that skip a step are rejected.

### §3.10.C Red-team cadence for MP itself

MP is red-teamed at every macro-phase close (the phase's red-team includes an MP-alignment pass — does the phase's closing state still match the MP's claim about this phase?). Additionally every 12 months regardless of phase state. Findings are logged as MPC-style entries (Macro Plan Critique format); if any CRITICAL or ≥ 3 HIGHs surface, a revision spec is opened per §3.10.B.

### §3.10.D Version semantics

- **v1.X additive** — new sections, new bullets, no schema change, no substrate change, no deletions.
- **v2.X architectural** — schema change, substrate change, five or more new top-level sections, or any change that forces downstream artifacts to re-read and re-align.
- **v3.X scope-redefining** — new primary subject; new cross-cultural extension; commercialization; project-purpose change.

Ambiguity resolves upward (if unclear between v1.X and v2.X, treat as v2.X).

### §3.10.E Sunset clause

MP is SUPERSEDED when either of: (a) a successor MP is published (e.g., MP v3.0 admitted at post-M10); OR (b) the project enters steady-state maintenance per §3.9.A AND is audited to require no further MP revisions (the audit itself is a red-team artifact). Superseded MPs are not deleted; they remain in the FILE_REGISTRY under ARCHIVAL status.

### §3.10.F Changelog requirement

Every MP revision ships with a changelog entry in the frontmatter. The entry includes: the spec reference (artifact path); the red-team verdict (artifact path + PASS/FAIL); the approval date; the rebuild-era tag if applicable (`produced_during` field). No revision ships without a changelog entry.

### §3.10.G Status field

MP frontmatter carries `status: CURRENT` or `status: SUPERSEDED` or `status: DRAFT_PENDING_REDTEAM` at all times. `DRAFT_PENDING_REDTEAM` is the interim state between Step 3 production and Step 5 closure (Step 4 red-team must PASS before status flips to CURRENT). Any other status value is ill-formed.

---

## Finding-Resolution Appendix

This appendix binds every Step-1 critique finding (MPC.N.M in-schema and MPC.OS.N out-of-schema) and the native directive ND.1 to the §2.X or §3.X entry in MP v2.0 that resolves it. The table mirrors the revision spec's §7 coverage table, retargeted to MP v2.0 sections. Resolution types: **KEEP** = section retained verbatim; **REVISE** = section content modified; **REPLACE** = section content wholly replaced; **DELETE** = no successor (folded elsewhere); **NEW-SECTION** = resolved by a new top-level section; **INSERT** = new content inserted without new section.

### Dimension 1 — Phase Completeness (8 findings)

| Finding ID | Severity | Resolution type | Resolving section in MP v2.0 |
|---|---|---|---|
| MPC.1.1 | HIGH | REPLACE | §The ten macro-phases — every row gains `Entry state` field |
| **MPC.1.2** | **CRITICAL** | **REPLACE** | §The ten macro-phases — every row gains `Exit state`; M2 imports from PHASE_B_PLAN §N by reference |
| MPC.1.3 | HIGH | REPLACE | §M1 row — rewritten to CLOSED state per 2026-04-19 sealing |
| MPC.1.4 | HIGH | REPLACE | §The ten macro-phases — M3–M10 rows declared coarse-grained; refined in phase-open sessions |
| MPC.1.5 | MEDIUM | INSERT | §Meta-Governance §3.10.A revision triggers + per-row `Quality gate` |
| MPC.1.6 | HIGH | REPLACE | §The ten macro-phases — every row gains `Deliverable paths` field |
| MPC.1.7 | MEDIUM | REPLACE | §M1 row — "mostly done" replaced with "CLOSED 2026-04-19" |
| MPC.1.8 | MEDIUM | REPLACE | §M4 row + §CW.LEL — explicit LEL→M4 feed |

### Dimension 2 — Sequencing and Dependencies (12 findings)

| Finding ID | Severity | Resolution type | Resolving section in MP v2.0 |
|---|---|---|---|
| **MPC.2.1** | **CRITICAL** | **REPLACE** | §The ten macro-phases — every row gains `Dependencies: requires / produces / enables` |
| MPC.2.2 | MEDIUM | REPLACE | §CW.LEL workstream block (cross-cutting declaration + M4 feed with minimum-volume gate) |
| MPC.2.3 | HIGH | REPLACE | §CW.PPL workstream block + §M6 row (minimum-volume gate) |
| MPC.2.4 | HIGH | REPLACE | §M7 row — Entry state "M6 closed AND ethical review complete" |
| MPC.2.5 | MEDIUM | REPLACE | §M8 row — Entry state "M5 closed (earliest legitimate start; M7 not a prerequisite)" |
| MPC.2.6 | HIGH | REPLACE | §M9 row — MSR coverage expansion for Nadi + BNN flagged as M8-owned pre-M9 requirement |
| MPC.2.7 | MEDIUM | NEW-SECTION | §LL-Appendix.B per-mechanism `Dependency on other LL.M` field |
| MPC.2.8 | LOW | NEW-SECTION | §LL-Appendix.A — activation matrix justifies "first four at M2" |
| MPC.2.9 | HIGH | REPLACE | §M10 row — Entry state "M9 closed AND acharya panel ≥ 3"; wiring inventory named |
| MPC.2.10 | MEDIUM | REPLACE | §The ten macro-phases + §System Integrity Substrate + §LL-Appendix (substrate cross-cutting) |
| MPC.2.11 | HIGH | REPLACE | §M2 row — "PHASE_B_PLAN_v1_0.md (currently v1.0.2); see FILE_REGISTRY for CURRENT pointer" |
| MPC.2.12 | MEDIUM | INSERT | Frontmatter `operational_rule` — forward-pointer to CLAUDE.md §Mandatory reading |

### Dimension 3 — Exit Criteria (10 findings)

| Finding ID | Severity | Resolution type | Resolving section in MP v2.0 |
|---|---|---|---|
| **MPC.3.1** | **CRITICAL** | **REPLACE** | §The ten macro-phases — every row gains `Exit state`; M2 imports PHASE_B_PLAN §N; M1 CLOSED; M3–M10 coarse criteria |
| MPC.3.2 | HIGH | REPLACE | §M1 row — CLOSED state per empirical date |
| MPC.3.3 | HIGH | REPLACE | §M3–M10 rows — each gains coarse-grained exit criteria |
| MPC.3.4 | HIGH | REPLACE | §M10 row — wiring inventory + publication target (arXiv minimum; peer-reviewed stretch) |
| MPC.3.5 | LOW | REVISE | §Learning Layer ("no closure; cadence checkpoints") + §LL-Appendix.B `Kill-switch` field |
| MPC.3.6 | MEDIUM | REPLACE | §CW.LEL + §CW.PPL — minimum-volume gates declared |
| MPC.3.7 | MEDIUM | INSERT | §IS.3 SESSION_LOG drift-detector + §IS.7 session-open/close templates |
| MPC.3.8 | MEDIUM | INSERT | §IS.8 red-team cadence as substrate axis (required for macro-phase close) |
| MPC.3.9 | MEDIUM | NEW-SECTION | §Meta-Governance — MP-versioning vs macro-phase-closure disambiguated |
| MPC.3.10 | HIGH | NEW-SECTION | §Post-M10 Framing §3.9.D retirement criteria + §M10 row (project-done = M10 exit state) |

### Dimension 4 — Risk Surface (13 findings)

| Finding ID | Severity | Resolution type | Resolving section in MP v2.0 |
|---|---|---|---|
| **MPC.4.1** | **CRITICAL** | **REPLACE** | §The ten macro-phases — every row gains `Risks` field, 3–6 bullets each |
| MPC.4.2 | LOW | REVISE | §Learning Layer n=1 paragraph (KEPT) + §LL-Appendix.C mitigation binding table |
| MPC.4.3 | MEDIUM | NEW-SECTION | §LL-Appendix.C n=1 mitigation binding table |
| MPC.4.4 | HIGH | REPLACE | §M7 row — consent, accuracy, desha-kala-patra overfit, fine-tuning risks bulleted |
| MPC.4.5 | HIGH | REPLACE | §M8 row — corpus procurement, translation, attribution, reputational risks bulleted |
| MPC.4.6 | HIGH | REPLACE | §M10 row + §Acharya Reviewer Pool Policy — reviewer availability, disagreement, publication-venue, reputational |
| MPC.4.7 | MEDIUM | REPLACE | §M4 row — provisional-validity risk bulleted |
| MPC.4.8 | HIGH | REPLACE | §M5 row — prior specification, DBN under-identification, learned-vs-classical divergence |
| MPC.4.9 | HIGH | REPLACE | §M6 row — verification-window drift, post-hoc rationalization, selection bias |
| MPC.4.10 | MEDIUM | REPLACE | §M9 row — spurious convergence, operator-preference collapse, calibration instability |
| MPC.4.11 | HIGH | NEW-SECTION | §External Dependency Graph — cross-cutting risks as first-class table |
| MPC.4.12 | MEDIUM | NEW-SECTION | §3.6.B SPOF mitigation cadence + §IS.6 drift-detector automation |
| MPC.4.13 | MEDIUM | REVISE | §Learning Layer — risk stance ("risk-averse on calibration, risk-seeking on discovery") |

### Dimension 5 — Learning Layer Specificity (15 findings)

| Finding ID | Severity | Resolution type | Resolving section in MP v2.0 |
|---|---|---|---|
| MPC.5.1 | HIGH | NEW-SECTION | §LL-Appendix.B LL.1 per-mechanism block |
| MPC.5.2 | HIGH | NEW-SECTION | §LL-Appendix.B LL.2 |
| MPC.5.3 | HIGH | NEW-SECTION | §LL-Appendix.B LL.3 |
| MPC.5.4 | HIGH | NEW-SECTION | §LL-Appendix.B LL.4 |
| MPC.5.5 | HIGH | NEW-SECTION | §LL-Appendix.B LL.5 |
| MPC.5.6 | HIGH | NEW-SECTION | §LL-Appendix.B LL.6 |
| MPC.5.7 | HIGH | NEW-SECTION | §LL-Appendix.B LL.7 (multi-chart vs cohort disambiguated) |
| MPC.5.8 | HIGH | NEW-SECTION | §LL-Appendix.B LL.8 |
| MPC.5.9 | HIGH | NEW-SECTION | §LL-Appendix.B LL.9 (prompt-level vs model-fine-tune disambiguated — note: disambiguation lives in LL.10 per spec §3.2 §LL-Appendix.B; MPC.5.9 addressed there) |
| MPC.5.10 | HIGH | NEW-SECTION | §LL-Appendix.B LL.10 |
| **MPC.5.11** | **CRITICAL** | **NEW-SECTION** | §LL-Appendix.A Activation-phase matrix |
| MPC.5.12 | HIGH | NEW-SECTION | §LL-Appendix.B per-mechanism `Kill-switch` field |
| MPC.5.13 | MEDIUM | NEW-SECTION | §LL-Appendix.D Learning Layer ownership |
| MPC.5.14 | MEDIUM | NEW-SECTION | §LL-Appendix.C n=1 mitigation binding table |
| MPC.5.15 | HIGH | NEW-SECTION | §LL-Appendix.B per-mechanism `Interaction with workstreams` |

### Dimension 6 — Concurrency Completeness (12 findings)

| Finding ID | Severity | Resolution type | Resolving section in MP v2.0 |
|---|---|---|---|
| MPC.6.1 | HIGH | REPLACE | §CW.LEL `Cadence` |
| MPC.6.2 | MEDIUM | REPLACE | §CW.LEL `Owner` |
| MPC.6.3 | HIGH | REPLACE | §CW.LEL `Schema pointer` |
| MPC.6.4 | HIGH | REPLACE | §CW.LEL `Entry-point` |
| MPC.6.5 | HIGH | REPLACE | §CW.PPL `Cadence` + `Activation` disambiguation |
| MPC.6.6 | MEDIUM | REPLACE | §CW.PPL `Owner` |
| MPC.6.7 | HIGH | REPLACE | §CW.PPL `Schema pointer` |
| MPC.6.8 | HIGH | REPLACE | §CW.PPL `Entry-point` |
| MPC.6.9 | HIGH | REPLACE | §CW.LEL/PPL `Feeds into` + `Minimum-volume gate` + §M4/§M6 rows importing the gate |
| MPC.6.10 | MEDIUM | REPLACE | §Cross-cutting workstreams `Activation` disambiguates "always on" vs "scaffolded at M_X" |
| MPC.6.11 | MEDIUM | REPLACE | §Cross-cutting workstreams `Failure modes` + `Freshness / staleness detection` |
| MPC.6.12 | HIGH | REPLACE | §Cross-cutting workstreams `Minimum-volume gate` (LEL ≥ 40 events; PPL ≥ 50 predictions) |

### Dimension 7 — External Dependency Graph (12 findings)

| Finding ID | Severity | Resolution type | Resolving section in MP v2.0 |
|---|---|---|---|
| **MPC.7.1** | **CRITICAL** | **NEW-SECTION** | §External Dependency Graph §3.6.A — 9-row dependency table |
| MPC.7.2 | HIGH | NEW-SECTION | §3.6.A ED.1 Jagannatha Hora row |
| MPC.7.3 | HIGH | NEW-SECTION | §3.6.A ED.2 Swiss Ephemeris row with version-lock |
| MPC.7.4 | HIGH | NEW-SECTION | §3.6.A ED.3 Voyage-3-large with re-embed contingency |
| MPC.7.5 | HIGH | NEW-SECTION | §3.6.A ED.4 Postgres+pgvector with migration contingency |
| MPC.7.6 | HIGH | NEW-SECTION | §3.6.A ED.5 Gemini row with two-pass-collapse contingency |
| MPC.7.7 | HIGH | NEW-SECTION | §3.6.A ED.6 Claude Opus row with Sonnet-fallback contingency |
| MPC.7.8 | HIGH | NEW-SECTION | §3.6.A ED.7 Classical corpora + §M8 row (shortlist) |
| **MPC.7.9** | **CRITICAL** | **NEW-SECTION** | §3.6.A ED.8 + §Acharya Reviewer Pool Policy (full section) |
| MPC.7.10 | HIGH | NEW-SECTION | §3.6.B SPOF mitigation cadence |
| MPC.7.11 | MEDIUM | NEW-SECTION | §3.6.C Licensing and legal status |
| MPC.7.12 | MEDIUM | NEW-SECTION | §3.6.D Model-family migration (cross-ref to §3.4.F) |

### Dimension 8 — Role-of-Native Cadence (7 findings)

| Finding ID | Severity | Resolution type | Resolving section in MP v2.0 |
|---|---|---|---|
| MPC.8.1 | HIGH | REPLACE | §The ten macro-phases — every row gains `Native-approval points` |
| MPC.8.2 | MEDIUM | NEW-SECTION | §Meta-Governance §3.10.A — revision triggers (defines "significant" by enumeration) |
| MPC.8.3 | HIGH | REPLACE | §M4/§M7/§M10 rows — native-declaration-moments named |
| MPC.8.4 | MEDIUM | NEW-SECTION | §Time/Effort Stance §3.8.B — session-volume envelopes |
| MPC.8.5 | HIGH | NEW-SECTION | §3.8.G — Pause protocol |
| MPC.8.6 | MEDIUM | NEW-SECTION | §3.8.G — unavailable-handoff folded in |
| MPC.8.7 | MEDIUM | NEW-SECTION | §Multi-Agent Collaboration §3.4.B — Two-pass protocol + per-row `Agent roles` |

### Dimension 9 — Time Horizon vs Phase Indexing (7 findings)

| Finding ID | Severity | Resolution type | Resolving section in MP v2.0 |
|---|---|---|---|
| MPC.9.1 | MEDIUM | NEW-SECTION | §3.8.A Phase-indexed stance + §3.8.B session-volume envelopes |
| MPC.9.2 | MEDIUM | NEW-SECTION | §3.8.A (hard dates declined explicitly) |
| MPC.9.3 | HIGH | NEW-SECTION | §3.8.C Sequencing stance |
| MPC.9.4 | HIGH | NEW-SECTION | §3.8.D Concurrent workstream duration + §Cross-cutting workstreams `Duration envelope` |
| MPC.9.5 | HIGH | NEW-SECTION | §3.8.C Sequencing stance |
| MPC.9.6 | MEDIUM | NEW-SECTION | §3.8.B Session-volume envelopes |
| MPC.9.7 | MEDIUM | NEW-SECTION | §3.8.E Budget envelope pointer |

### Dimension 10 — Post-M10 Framing (6 findings)

| Finding ID | Severity | Resolution type | Resolving section in MP v2.0 |
|---|---|---|---|
| MPC.10.1 | HIGH | NEW-SECTION | §Post-M10 Framing (entire section) |
| MPC.10.2 | MEDIUM | NEW-SECTION | §3.9.A Maintenance mode |
| MPC.10.3 | MEDIUM | NEW-SECTION | §3.9.B Publication |
| MPC.10.4 | MEDIUM | NEW-SECTION | §3.9.C Ownership and handoff |
| MPC.10.5 | MEDIUM | NEW-SECTION | §3.9.D Retirement criteria |
| MPC.10.6 | MEDIUM | NEW-SECTION | §3.9.E Versioning policy post-M10 |

### Dimension 11 — Ethical Framework (9 findings)

| Finding ID | Severity | Resolution type | Resolving section in MP v2.0 |
|---|---|---|---|
| **MPC.11.1** | **CRITICAL** | **NEW-SECTION** | §Ethical Framework (entire section) + §3.5.A Principles |
| MPC.11.2 | HIGH | NEW-SECTION | §3.5.B Disclosure tiers |
| **MPC.11.3** | **CRITICAL** | **NEW-SECTION** | §3.5.C Self-harm guardrail |
| MPC.11.4 | HIGH | NEW-SECTION | §3.5.B Disclosure tiers (four audiences) |
| **MPC.11.5** | **CRITICAL** | **NEW-SECTION** | §3.5.D Consent protocol for M7 cohort |
| MPC.11.6 | HIGH | NEW-SECTION | §3.5.G Calibration disclosure |
| MPC.11.7 | HIGH | NEW-SECTION | §3.5.E Pre-registration / blinding |
| MPC.11.8 | HIGH | NEW-SECTION | §3.5.F Minor / vulnerable-population stance |
| MPC.11.9 | MEDIUM | NEW-SECTION | §3.5.H Mode A / Mode B linkage |

### Dimension 12 — Meta-Governance (7 findings)

| Finding ID | Severity | Resolution type | Resolving section in MP v2.0 |
|---|---|---|---|
| MPC.12.1 | HIGH | NEW-SECTION | §Meta-Governance §3.10.A Revision triggers |
| MPC.12.2 | HIGH | NEW-SECTION | §3.10.B Approval protocol |
| MPC.12.3 | MEDIUM | NEW-SECTION | §3.10.E Sunset clause |
| MPC.12.4 | HIGH | NEW-SECTION | §3.10.C Red-team cadence for MP itself |
| MPC.12.5 | MEDIUM | NEW-SECTION | §3.10.D Version semantics |
| MPC.12.6 | MEDIUM | REVISE | Frontmatter `status: DRAFT_PENDING_REDTEAM` (flips to CURRENT at Step 5 close) + §3.10.G |
| MPC.12.7 | MEDIUM | NEW-SECTION | §3.10.F Changelog requirement + frontmatter changelog block |

### Dimension 13 — Multi-Agent Collaboration (7 findings)

| Finding ID | Severity | Resolution type | Resolving section in MP v2.0 |
|---|---|---|---|
| MPC.13.1 | HIGH | NEW-SECTION | §Multi-Agent Collaboration (entire section) + §3.4.A Current agents |
| MPC.13.2 | HIGH | NEW-SECTION | §3.4.C Disagreement protocol + §IS.5 DISAGREEMENT_REGISTER pointer |
| MPC.13.3 | HIGH | NEW-SECTION | §3.4.B Two-pass protocol + per-row `Agent roles` |
| MPC.13.4 | MEDIUM | NEW-SECTION | §3.4.E Future-agent admission policy |
| MPC.13.5 | MEDIUM | NEW-SECTION | §IS.5 + §3.4.C (DISAGREEMENT_REGISTER pointer) |
| MPC.13.6 | HIGH | REPLACE | Per-row `Quality gate` field + §3.4.D pointer |
| MPC.13.7 | MEDIUM | NEW-SECTION | §3.4.F Version-pinning discipline |

### Dimension 14 — System Integrity and Drift-Prevention (7 findings)

| Finding ID | Severity | Resolution type | Resolving section in MP v2.0 |
|---|---|---|---|
| **MPC.14.1** | **CRITICAL** | **NEW-SECTION** | §System Integrity Substrate (entire section — substrate parallel to Learning Layer) |
| MPC.14.2 | HIGH | NEW-SECTION | §IS.2 Mirror Discipline (three ND.1 load-bearing claims) |
| MPC.14.3 | HIGH | NEW-SECTION | §IS.4 FILE_REGISTRY / GOVERNANCE_STACK as enforcement registries |
| MPC.14.4 | HIGH | NEW-SECTION | §IS.3 SESSION_LOG as drift detector |
| MPC.14.5 | HIGH | NEW-SECTION | §IS.1 Canonical Artifact Discipline (points to CANONICAL_ARTIFACTS_v1_0) |
| **MPC.14.6** | **CRITICAL** | **NEW-SECTION** | §IS.9 Governance rebuild acknowledgment + frontmatter `produced_during` + §Why this exists prepend |
| MPC.14.7 | HIGH | NEW-SECTION | §System Integrity Substrate (elevated to substrate parity with Learning Layer) |

### Out-of-schema findings (4 findings)

| Finding ID | Severity | Resolution type | Resolving section in MP v2.0 |
|---|---|---|---|
| MPC.OS.1 | LOW | REVISE | Frontmatter `produced_during` + §3.10.F changelog requirement |
| MPC.OS.2 | MEDIUM | REPLACE | §Scope Boundary — split into session-scope / macro-phase-scope / enforcement |
| MPC.OS.3 | LOW | REVISE | Title block + header-level normalization across MP v2.0 + §Meta-Governance declaration |
| MPC.OS.4 | LOW | INSERT | Frontmatter `id_namespace: M1..M10; LL.1..LL.10; IS.1..IS.9; ED.1..ED.9; CW.LEL, CW.PPL; MP.1..MP.7` |

### Native directive (ND.1)

| Directive ID | Severity | Resolution type | Resolving section in MP v2.0 |
|---|---|---|---|
| **ND.1 — Mirror Discipline** | **CRITICAL-equivalent** | **NEW-SECTION** | §IS.2 Mirror Discipline (three claims stated) + changelog entry naming ND.1 + frontmatter `id_namespace` including MP.1..MP.7 |

### Coverage audit

**Total findings addressed:** 132 MPC in-schema + 4 MPC.OS out-of-schema + 1 ND.1 = **137**.

- CRITICAL (in-schema MPC): 12 / 12 addressed (100%).
- HIGH (in-schema MPC): 71 / 71 addressed.
- MEDIUM (in-schema MPC): 46 / 46 addressed.
- LOW (in-schema MPC): 3 / 3 addressed.
- Out-of-schema (MPC.OS): 4 / 4 addressed (1 MEDIUM + 3 LOW).
- Native directive: ND.1 addressed (§IS.2 + frontmatter changelog + id_namespace).

Zero `[NATIVE_CONFIRMATION_NEEDED]` flags. Zero `[DEFER_TO_FUTURE_REVISION]` flags. Zero `[SPEC_UNDERSPECIFIED_FOR_SUBSTANCE]` flags. Zero `[SPEC_UNDERSPECIFIED_FOR_DIRECTIVE]` flags.

---

## Spec Traceability Appendix

This appendix is required by the Step 3 brief §5 discipline rules. It maps each new or revised section in MP v2.0 to the entry in `MACRO_PLAN_REVISION_SPEC_v1_0.md` that mandated it. The Finding-Resolution Appendix above maps findings to MP v2.0 sections; this appendix maps MP v2.0 sections to the spec entries that generated them.

| MP v2.0 section / element | Disposition | Spec entry mandating it | ND binding |
|---|---|---|---|
| Frontmatter (version, status, supersedes, produced_during, id_namespace, operational_rule forward-pointer, changelog) | REPLACE | Spec §2.1, §2.10, §4.1, §4.2 | ND.1 changelog entry per §IS.2 obligation |
| Title block ("MARSYS-JIS Macro Plan — Strategic Arc v2.0" + one-line subtitle) | REVISE | Spec §2.2 | — |
| §Why this exists (rebuild-era prepend + original text) | REVISE (KEEP+prepend) | Spec §2.3 | — |
| §Ultimate goal (original two sentences + ethics-scope third sentence) | REVISE | Spec §2.4 | — |
| §System Integrity Substrate (§IS.1–§IS.9) | NEW-SECTION | Spec §3.3 | ND.1 — §IS.2 is the MP-layer implementation; verbatim-or-equivalent three claims; MP changelog names ND.1 |
| §Learning Layer — a cross-cutting substrate (scaffold-pending qualifier, ten-mechanism list, amended discipline rule #3, n=1 paragraph, risk stance) | REVISE | Spec §2.6 (items 1–4) | — |
| §Learning Layer Specification Appendix §LL-Appendix.A Activation-phase matrix | NEW-SECTION | Spec §3.2 §LL-Appendix.A | — |
| §LL-Appendix.B Per-mechanism blocks (LL.1–LL.10) | NEW-SECTION | Spec §3.2 §LL-Appendix.B | — |
| §LL-Appendix.C n=1 risk mitigation binding table | NEW-SECTION | Spec §3.2 §LL-Appendix.C | — |
| §LL-Appendix.D Learning Layer ownership | NEW-SECTION | Spec §3.2 §LL-Appendix.D | — |
| §The ten macro-phases (§M1–§M10 per fixed row schema) | REPLACE | Spec §2.5 (schema + per-phase content direction) | — |
| §Cross-cutting workstreams (§CW.LEL, §CW.PPL) | REPLACE | Spec §2.7 (schema + per-workstream content direction) | — |
| §Scope Boundary (session-scope / macro-phase-scope / enforcement) | REPLACE | Spec §2.8 | — |
| §Multi-Agent Collaboration §3.4.A–F | NEW-SECTION | Spec §3.4 | ND.1 — §3.4.C includes mirror-desync as implicit disagreement class |
| §Ethical Framework §3.5.A–H | NEW-SECTION | Spec §3.5 | ND.1 — ethical framework is a mirror target (Gemini-side counterpart carries same principles) |
| §External Dependency Graph §3.6.A–D | NEW-SECTION | Spec §3.6 | — |
| §Acharya Reviewer Pool Policy §3.7.A–E | NEW-SECTION | Spec §3.7 | — |
| §Time/Effort Stance §3.8.A–G | NEW-SECTION | Spec §3.8 | — |
| §Post-M10 Framing §3.9.A–E | NEW-SECTION | Spec §3.9 | — |
| §Meta-Governance §3.10.A–G | NEW-SECTION | Spec §3.10 (replaces §2.9 Change control stub) | — |
| §Finding-Resolution Appendix (137 rows) | NEW-SECTION | Spec §3.11 + §7 (source of finding-to-spec-entry bindings) | — |
| §Spec Traceability Appendix (this appendix) | NEW-SECTION | Step 3 brief §5 Discipline rules (separate from spec §3.11) | — |

### ND.1 traceability summary

ND.1 (Mirror Discipline as a First-Class Governance Principle) is enacted at three MP v2.0 surfaces:

1. **§IS.2 Mirror Discipline subsection** — the three ND.1 load-bearing claims (bidirectional obligation; adapted parity, not byte-identity — including the verbatim "semantic parity of governance content, not feature parity of agent capabilities"; scope beyond CLAUDE.md) stated explicitly. Maps to spec §3.3 §IS.2 (which maps to ND.1 `NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` §1 ND.1 consumption-matrix Row "3 — Rewrite" obligation).
2. **Changelog entry** — the v2.0 changelog entry names ND.1 explicitly ("the ND.1 native directive (Mirror Discipline as a First-Class Governance Principle)"). Maps to spec §4.2 changelog text.
3. **§3.4.C Disagreement protocol** — mirror-desync declared as an implicit disagreement class; reconciles with §IS.2 per ND.1 consumption-matrix Row 2 verification criterion.

Full Claude-side inventory of mirror pairs is spec §5.2 (MP.1–MP.7), with Step 5A `PROJECT_ARCHITECTURE_v2_2.md` §D.11 producing the authoritative enumeration and Step 7 `CANONICAL_ARTIFACTS_v1_0.md` `mirror_obligations` column providing the machine-readable authoritative list.

ND.1 status remains `open` in `NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` after this rewrite; the flip to `addressed` is Step 7's obligation per ND.1 close condition. This MP v2.0 satisfies the Step-3 row of ND.1's consumption matrix.

---

*End of MACRO_PLAN_v2_0.md — DRAFT_PENDING_REDTEAM. Next: Step 4 (red-team) per STEP_LEDGER.*
