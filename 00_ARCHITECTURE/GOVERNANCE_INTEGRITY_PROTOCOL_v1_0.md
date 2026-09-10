---
artifact: GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md
version: 1.0
status: CURRENT  # flipped DRAFT_PENDING_REDTEAM → CURRENT 2026-04-24 at Step 8 close (verdict PASS_WITH_FIXES per GOVERNANCE_INTEGRITY_REDTEAM_v1_0.md §1); F.1/F.2/F.3 findings are substantive coverage extensions booked to Step 12 per brief §4
produced_during: STEP_6_GOVERNANCE_INTEGRITY_DESIGN (Step 0 → Step 15 governance rebuild)
produced_on: 2026-04-24
supersedes: (none — first version of this artifact)
consumed_by:
  - Step 7 (Governance Integrity implementation) — primary; Step 7 implements this spec verbatim via §M
  - Step 8 (red-team of the Step 7 implementation) — read as the oracle against which the implementation is judged
  - Step 12 (ongoing hygiene policies) — extensions of the §H drift-detector and §I schema-validator cadence-binding
  - Step 13 (drift-detection baseline run) — first production-mode invocation of the §H drift detector
  - Step 14 (schema-validation baseline run) — first production-mode invocation of the §I schema validator
  - Step 15 (Governance Baseline close) — the entry point into the steady-state governance regime this protocol operates under
role: >
  Specification-only design document for the full drift-prevention, integrity-enforcement, and
  multi-agent-sync system the MARSYS-JIS project will implement. Written in Step 6 of the Step 0 →
  Step 15 governance rebuild. Carries no code and writes no configuration. Becomes the
  requirements spec Step 7 implements. Favors mechanical enforcement over procedural
  exhortation: "session MUST update X" is weaker than "script fails loudly if X is not
  updated." Every control traces to at least one GROUNDING_AUDIT_v1_0 GA.N finding or to
  native directive ND.1 (Mirror Discipline).
authoritative_side: Claude (Claude-only governance-surface; no Gemini-side counterpart required — the protocol governs mirror discipline but is not itself a mirror pair; the principle is stated verbatim in MP v2.0 §IS.2 and v2.2 §D.11, both of which do have Gemini-side mirrors)
mirror_obligations: >
  None for this file itself. The subordinate artifacts Step 7 implements (CANONICAL_ARTIFACTS_v1_0.md,
  SESSION_OPEN_TEMPLATE, SESSION_CLOSE_TEMPLATE, DISAGREEMENT_REGISTER) carry their own
  mirror_obligations declarations per §E and §J below.
related_artifacts:
  - MACRO_PLAN_v2_0.md §System Integrity Substrate (§IS.1–§IS.9) — the substrate declaration this protocol implements at design level
  - PROJECT_ARCHITECTURE_v2_2.md §D.9 (Governance Stack live scope), §D.11 (Multi-Agent Collaboration + MP.1–MP.8 mirror-pair inventory), §L (Governance Rebuild Reference) — the architecture surfaces that forward-point to this protocol
  - GROUNDING_AUDIT_v1_0.md — GA.1–GA.32 findings every control below traces
  - NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md ND.1 — Mirror Discipline directive enacted at §J and §K
  - PHASE_B_PLAN_v1_0.md §H — P1–P9 validator specifications informing §C Axis 1 controls
  - GOVERNANCE_STACK_v1_0.md — existing governance registry the §D redesign extends
  - FILE_REGISTRY_v1_2.md — existing artifact inventory the §D redesign extends
  - LIVING_PROJECT_MAINTENANCE_GUIDE_v1_0.md, MAINTENANCE_SCHEDULE_v1_0.md — long-term hygiene cadences §C Axis 5 co-operates with
changelog:
  - v1.0 (2026-04-24, Step 6 of the Step 0 → Step 15 governance rebuild):
    Initial specification. Produced per STEP_BRIEFS/STEP_06_GOVERNANCE_INTEGRITY_DESIGN_v1_0.md.
    Status DRAFT_PENDING_REDTEAM until Step 8 red-team closes. Flips to CURRENT at Step 8 close
    if verdict is PASS or PASS_WITH_FIXES. Six axes, fourteen sections (§A–§N), 32 GA.N +
    ND.1 covered in §N, thirteen Step 7 implementation artifacts in §M.
---

# GOVERNANCE & INTEGRITY PROTOCOL v1.0
## MARSYS-JIS Project — Design Specification

*Produced in Step 6 of the Step 0 → Step 15 governance rebuild.*
*Specification only — no code, no configuration. Step 7 implements.*
*DRAFT_PENDING_REDTEAM until Step 8 closes.*

---

## §A — AXIOMS

The protocol guarantees six non-negotiable properties. These are not themselves controls; they are the load-bearing claims every control below must uphold. If a design choice elsewhere in this document violates one of them, that choice is wrong — not the axiom.

### A.1 — Single source of truth per canonical artifact

For every canonical artifact (MSR, UCN, CDLM, RM, CGM, FORENSIC, LEL, MACRO_PLAN, PHASE_B_PLAN, PROJECT_ARCHITECTURE, FILE_REGISTRY, GOVERNANCE_STACK, STEP_LEDGER, and every other entry registered under §E), exactly one file is CURRENT at any moment. Every cross-surface reference to that artifact resolves to the same path and the same version. Duplication of canonical paths across surfaces is itself a drift vector — per MP v2.0 §IS.1 — and is replaced here by a single authoritative source (CANONICAL_ARTIFACTS_v1_0.md, §E) that every other surface imports or cites rather than duplicates.

### A.2 — Every cross-surface reference is resolvable and current

No governance surface (CLAUDE.md, `.geminirules`, `.gemini/project_state.md`, SESSION_LOG, STEP_LEDGER, FILE_REGISTRY, GOVERNANCE_STACK, MACRO_PLAN, PHASE_B_PLAN, PROJECT_ARCHITECTURE, this protocol, or any future governance-layer artifact) contains a live pointer to a file that does not exist, a version that is SUPERSEDED without a supersedure banner, or a canonical path that contradicts the CANONICAL_ARTIFACTS declaration. Closed or archival artifacts may reference superseded versions as historical lineage; live pointers in live surfaces always resolve to CURRENT.

### A.3 — No drift goes undetected for more than one session

The drift detector (§H) runs at every session close. A divergence between any two surfaces that should agree is caught within one session of appearing. Sessions that skip the drift detector fail their session-close checklist (§G) and do not close. The principle replaces the procedural-honor-system regime GA.13 documented, in which "a procedural rule that has been broken once will be broken again."

### A.4 — Every session produces an auditable trace

Every session emits a session-open handshake (§F) and a session-close checklist (§G). Both are machine-readable. Both are appended to SESSION_LOG as part of the session's closure. A session without a handshake or without a close checklist is not a well-formed session and cannot claim close. The trace documents what the session read, what it touched, what registry updates it made, and whether the drift detector and schema validator exited clean.

### A.5 — Mirror discipline is mechanically enforced, not procedurally asserted

Per ND.1 (Mirror Discipline as a First-Class Governance Principle), every Claude-side governance file with a Gemini-side counterpart is kept in continuous semantic parity with its counterpart, via adapted parity not byte-identity. Enforcement is the `mirror_enforcer.py` script (Step 7 deliverable) operating over the mirror-pair inventory declared in CANONICAL_ARTIFACTS — not the honor system that GA.13 documented breaking within days of being written. The inventory is the architecture-layer MP.1–MP.8 list in PROJECT_ARCHITECTURE_v2_2 §D.11.2, re-declared machine-readably in CANONICAL_ARTIFACTS (§E).

### A.6 — The protocol itself is a living artifact under its own discipline

This file is a governance-layer artifact. It is registered in FILE_REGISTRY. It is subject to the schema validator (§I). Revisions to it follow §L. Its own red-team cadence is declared in §L. The protocol does not exempt itself from the rules it imposes on the rest of the project.

---

## §B — SCOPE AND NON-SCOPE

### B.1 — What this protocol governs

- **Governance surfaces.** CLAUDE.md, `.geminirules`, `.gemini/project_state.md`, SESSION_LOG, STEP_LEDGER, FILE_REGISTRY, GOVERNANCE_STACK, MACRO_PLAN, PHASE_B_PLAN, PROJECT_ARCHITECTURE, this protocol, CANONICAL_ARTIFACTS (§E), DISAGREEMENT_REGISTER (§K), SESSION_OPEN_TEMPLATE (§F), SESSION_CLOSE_TEMPLATE (§G), CURRENT_STATE (Step 10 deliverable).
- **Registries.** FILE_REGISTRY_v1_2.md (and successors), GOVERNANCE_STACK_v1_0.md (and successors), CANONICAL_ARTIFACTS_v1_0.md (new, Step 7 deliverable), LIVING_PROJECT_MAINTENANCE_GUIDE, MAINTENANCE_SCHEDULE, FALSIFIER_REGISTRY, CONTRADICTION_REGISTRY.
- **Scripts.** `drift_detector.py` (§H), `schema_validator.py` (§I), `mirror_enforcer.py` (§J), and any future governance-integrity script.
- **Session protocol.** Session-open handshake (§F), session-close checklist (§G), STEP_LEDGER transitions (during rebuild era), CURRENT_STATE transitions (post-Step 10).
- **Cross-agent collaboration.** Mirror discipline (per ND.1), two-pass execution boundaries, disagreement-register mechanics.

### B.2 — What this protocol does NOT govern

- **Corpus content.** The interpretation-quality standards for MSR, UCN, CDLM, RM, CGM, and the nine L3 domain reports are governed by PROJECT_ARCHITECTURE §H (quality standards), MP v2.0 §3.5 (Ethical Framework), and the P1–P9 validators in PHASE_B_PLAN §H. This protocol does not re-derive them; it inherits them.
- **Phase-specific execution plans.** PHASE_B_PLAN governs M2. Future phase plans (M3+) govern their own phases. The protocol binds the governance surfaces around them (STEP_LEDGER during rebuild; CURRENT_STATE + per-phase plans post-rebuild) but does not substitute for them.
- **The Learning Layer.** Learning Layer mechanisms (LL.1–LL.10) are the subject of MP v2.0 §Learning Layer and the Step 11 scaffold-or-non-scaffold decision. This protocol locks the project's claims about its own state; the Learning Layer modulates classical priors with empirical evidence. The two substrates are parallel per MP §System Integrity Substrate preamble and are crisply distinct — per Step 6 brief §8 red-team prompt 3, a fresh session should not confuse them.
- **L4 Discovery Layer execution.** Two-pass protocol boundaries are *bounded* by this protocol's mirror and disagreement controls, but the two-pass protocol itself is governed by MP v2.0 §Multi-Agent Collaboration §3.4.B and PHASE_B_PLAN §E.5.
- **Red-team content.** Red-team cadences are declared here (§L) and at MP §IS.8; the actual red-team prompts and verdicts for specific artifacts live in their own red-team files (e.g., MACRO_PLAN_REDTEAM_v1_0.md, the forthcoming GOVERNANCE_INTEGRITY_REDTEAM_v1_0.md at Step 8).
- **Native ethical decisions.** MP v2.0 §3.5 (Ethical Framework) is the authority. This protocol refers to it; it does not re-state it.

### B.3 — Out-of-scope for this step

Per Step 6 brief §4 constraints, this file writes **no code** (no `.py`, no `.sh`, no configs), performs **no edits** to CLAUDE.md / `.geminirules` / `project_state.md` / any registry (those are Step 7 actions), introduces **no new canonical artifact paths** (CANONICAL_ARTIFACTS documents the existing ones), and does **not pre-specify the Learning Layer**. Any future content that would violate one of these is rejected at Step 8 red-team.

---

## §C — THE SIX AXES

This section specifies one subsection per axis listed in the Step 6 brief §1. Each subsection carries: axis definition; threats this axis guards against (cited by GA.N); controls (preventive, detective, corrective); enforcement mechanism (script, template, gate, handshake).

### C.1 — Axis 1: Data Integrity (facts, derivations, interpretations, cross-file citations)

**Definition.** The corpus's claims about the chart and the native's life are layer-separated, citation-tracked, and non-fabricated. L1 facts are distinguishable from L2+ interpretations in every artifact. Every L2+ claim cites specific L1 IDs via a derivation ledger (PROJECT_ARCHITECTURE §H.4 Whole-Chart-Read Protocol; PHASE_B_PLAN §H P1/P2).

**Threats**:
- Layer mixing: a claim in a single sentence mixes L1 fact + L2 interpretation without a layer tag or bridge marker (P1 fires).
- Citation gap: an L2+ claim with no `v6_ids_consumed` field (P2 fires) or citing a fact_id that does not resolve against FORENSIC_v8.0 (P2 fires).
- Fabricated computation: a claim containing a position, degree, or date not in FORENSIC_v8.0 (P4 fires).
- Fabricated signal: a claim citing a signal ID not in MSR_v3.0 (P5 fires).
- Missing whole-chart-read: a narrow-domain interpretive bundle containing no L2.5 (UCN/CDLM) chunk (P3 fires).

**GA.N mapped**: GA.1 (MSR version drift affects P5 resolution target if registry is behind CURRENT; protocol closes via Axis 3 too); GA.32 (system integrity as a substrate — this axis is one of the substrate's expressions); GA.23 Step-1-resolved in MP v2.0 §Learning Layer + §LL-Appendix; the axis itself is unaffected.

**Controls**:
- **Preventive**: P1–P9 validators (PHASE_B_PLAN §H) run at every chunk write, retrieval, and artifact write. The five fact-citation validators (P1 Layer separation, P2 Citation discipline, P4 No fabricated computation, P5 Signal ID resolution, P3 Whole-Chart-Read) are Axis 1's primary controls.
- **Detective**: existing `citation_graph_builder.py`, `invariants_l1.py`, and `audit.py` + `verify_corpus.py` (per Step 6 brief §2 MAY-read list). These scripts were pre-existing; Axis 1 reuses them, does not duplicate.
- **Corrective**: on validator fail, the artifact write is rejected; session logs the failure in SESSION_LOG + ledger; native reviews at session close.

**Enforcement mechanism**: the P1–P9 validator cascade implemented per PHASE_B_PLAN §H and run on the cadences declared there (`P1/P2/P5 at every chunk write, retrieval, and artifact write`; P3 at every retrieval bundle assembly; P4 at every synthesis; P6 at synthesis + contradiction-scan; P7 at synthesis for significance ≥ 0.7; P8 at every artifact write; P9 at reproducibility-check cadence). Integration with this protocol is via the schema validator (§I) which verifies that artifact-level frontmatter declares which validators ran with what verdict.

### C.2 — Axis 2: Data Accuracy (numeric invariants, position grammar, version pointers)

**Definition.** Numeric claims in the corpus (signal counts, positions, degrees, dates, line counts, node counts) agree across every surface that states them. Version pointers (MSR_v3.0 not v2.0; CGM_v2.0 not v1.0; FORENSIC_v8.0 not v6.0) are consistent across surfaces. Positional values match FORENSIC_v8.0's canonical set within declared tolerance.

**Threats**:
- Numeric drift: MSR signal count reported as 500 on one surface and 499 on another (GA.2). Line-count claims that do not match `wc -l`. Node-count claims that do not match actual node enumeration.
- Version drift: surfaces that should cite MSR_v3.0 still citing MSR_v2.0 (GA.1 primary). Surfaces claiming "CGM not rebuilt on v8.0" when it was rebuilt 2026-04-19 (GA.4). Surfaces claiming "four L3 reports stale" when all nine are at v1.1+ (GA.5).
- Positional fabrication: an LLM-emitted degree-minute-second token that does not match any FORENSIC_v8.0 position within tolerance (P4).

**GA.N mapped**: GA.1 (CRITICAL — primary numeric/version drift), GA.2 (500 vs 499), GA.4 (CGM-v8.0 staleness; resolved in MP v2.0 but re-checked by this axis at every session), GA.5 (L3 staleness; resolved in MP v2.0 but re-checked).

**Controls**:
- **Preventive**: every numeric or version claim in a governance surface cites CANONICAL_ARTIFACTS as the source of truth and reads it at session open (§F). Surfaces that cannot cite CANONICAL_ARTIFACTS (e.g., human-written narrative paragraphs) declare the value inline and the schema validator (§I) cross-checks.
- **Detective**: drift detector (§H) compares declared numerics across surfaces. Any disagreement between two surfaces that both claim to be authoritative on the same fact emits a drift report entry.
- **Corrective**: on drift, the surface that disagrees with CANONICAL_ARTIFACTS is the one corrected (CANONICAL_ARTIFACTS is the authoritative side for numerics and versions by construction).

**Enforcement mechanism**: `drift_detector.py` (§H) + `schema_validator.py` (§I) + `invariants_l1.py` (existing; reused). The drift detector runs at every session close and fails the close if any numeric or version drift is detected. The schema validator runs at every artifact write and rejects frontmatter with numerics that disagree with CANONICAL_ARTIFACTS (where the artifact type declares a numeric-parity obligation).

### C.3 — Axis 3: Data Consistency (cross-surface version agreement, canonical-path agreement)

**Definition.** Governance surfaces that name the same canonical artifact name the same path and the same version. No surface makes a claim about the CURRENT version of any artifact that disagrees with CANONICAL_ARTIFACTS.

**Threats**:
- Path drift: CLAUDE.md cites `MSR_v3_0.md`, FILE_REGISTRY cites `MSR_v2_0.md`, GOVERNANCE_STACK cites `MSR_v2_0.md`. A fresh session reading all three receives contradictory claims about the CURRENT MSR (GA.1 — the canonical example this protocol is designed to prevent).
- Plan-pointer drift: `.gemini/project_state.md` cites `twinkly-puzzling-quokka.md` as the plan while CLAUDE.md and PHASE_B_PLAN both cite PHASE_B_PLAN_v1_0.md (GA.7 — resolved at Step 5 for this specific case; the protocol prevents recurrence).
- Registry drift: FILE_REGISTRY and GOVERNANCE_STACK disagree about an artifact's status (CURRENT vs SUPERSEDED).
- Missing-pointer drift: an artifact exists, is authoritative, and is not listed in any registry or canonical-path table (GA.9: LEL_v1.2 not in CLAUDE.md; GA.10: GOVERNANCE_STACK not in CLAUDE.md; GA.11: maintenance/falsifier/contradiction/audit files not in CLAUDE.md).

**GA.N mapped**: GA.1 (primary), GA.3, GA.7 (recurrence-prevention), GA.9 (unreferenced LEL), GA.10 (unreferenced GOVERNANCE_STACK), GA.11 (unreferenced supporting artifacts), GA.13 (procedural-to-mechanical conversion is this axis's raison d'être), GA.14 (no drift-detection script — this axis's enforcement is the drift detector).

**Controls**:
- **Preventive**: CANONICAL_ARTIFACTS (§E) is the single authoritative source. Surfaces that cite canonical paths either (a) reference CANONICAL_ARTIFACTS by name rather than duplicating the path, or (b) duplicate the path with a declared `verified_against: CANONICAL_ARTIFACTS_v1_0 @ <sha256>` attestation at the top of the surface.
- **Detective**: drift detector (§H) does explicit pairwise comparisons of: CLAUDE.md path table ↔ `.geminirules` canonical-path block; `.geminirules` block ↔ `.gemini/project_state.md` corpus state block; CANONICAL_ARTIFACTS ↔ each of the above; FILE_REGISTRY ↔ CANONICAL_ARTIFACTS; GOVERNANCE_STACK §1 version registry ↔ CANONICAL_ARTIFACTS.
- **Corrective**: on pairwise disagreement, the drift detector emits a structured report naming (a) which pair disagrees, (b) which side is stale against CANONICAL_ARTIFACTS, (c) which sentence/row differs. The session that observes the drift report halts at close and opens a DISAGREEMENT_REGISTER entry (mirror-desync class per §K) — resolution is not silent overwriting.

**Enforcement mechanism**: `drift_detector.py` (§H). Runs at every session close as part of §G. Exit code 0 is required for close; exit code ≠ 0 fails the close and emits the drift report to the session's close-entry attachment.

### C.4 — Axis 4: Alignment to Goals and Plan (scope-boundary enforcement per Macro Plan and active phase plan)

**Definition.** Every session operates within the currently-active macro-phase's scope and the currently-active phase-plan expansion. During the governance rebuild era, scope is exactly one STEP_LEDGER row. Post-rebuild, scope is the current CURRENT_STATE-declared macro-phase and sub-phase. Sessions do not pre-build infrastructure for later macro-phases; do not modify the prior-macro-phase closed artifacts; do not edit files outside their declared scope.

**Threats**:
- Rebuild-era scope creep: a Step-N session also modifies Step-M artifacts (N ≠ M) without ledger amendment.
- Phase-B scope creep: an M2 Phase B.2 session pre-builds Phase B.5 infrastructure, or scaffolds `06_LEARNING_LAYER/` ahead of the Step 11 decision (WARN.1).
- Cross-phase scope creep: a session in M2 mutates MP v2.0 (an M0-era artifact) without invoking the §L meta-governance revision protocol.

**GA.N mapped**: GA.20 (scope-boundary clause unenforced — primary), GA.21 (no automated SESSION_LOG check for artifact touches), GA.32 (substrate axis).

**Controls**:
- **Preventive**: session-open handshake (§F) requires the session to declare its scope up front in machine-readable form. `declared_scope` is a list of paths the session may touch; paths outside are forbidden at the protocol level.
- **Detective**: session-close checklist (§G) compares `files_touched` against `declared_scope`. Any touch outside scope fails the close. The schema validator (§I) cross-references touched files against the declared scope.
- **Corrective**: an out-of-scope touch requires (a) explicit in-session scope amendment with rationale logged to SESSION_LOG, or (b) the session halts, reverts the out-of-scope edits, and closes with the intended scope.

**Enforcement mechanism**: `SESSION_OPEN_TEMPLATE` (§F; Step 7 deliverable) + `SESSION_CLOSE_TEMPLATE` (§G; Step 7 deliverable) + schema validator (§I) scope-boundary check. Mirror of MP v2.0 §Scope Boundary — per MP's enforcement clause: "Scope discipline is mechanical, not procedural, per GA.13. The session-open handshake requires the session to declare its scope before action. The drift detector flags sessions that touch files outside the declared scope."

### C.5 — Axis 5: Living-Document Hygiene (registry currency, staleness detection)

**Definition.** Every artifact mutation (creation, version bump, supersession, archival, in-place amendment) produces a corresponding entry in FILE_REGISTRY and a closure/amendment entry in GOVERNANCE_STACK within the same session. Session-level discipline ensures SESSION_LOG contains an entry for every session; the entry enumerates files touched; the touched-files list resolves to registry updates on the one side and to an artifact-frontmatter update on the other.

**Threats**:
- Orphan mutations: a file edited in-session without a matching FILE_REGISTRY row update (GA.21).
- Orphan artifacts: a new file created in-session without registry registration (e.g., a `06_LEARNING_LAYER/` scaffolding that does not appear in FILE_REGISTRY until Step 11's scaffold decision closes).
- Orphan supersessions: an old version retained on disk without its SUPERSEDED banner (GA.12 — LEL_v1.1 still in facts folder).
- Phantom references: a live pointer to a file that does not exist (GA.6 06_LEARNING_LAYER/; GA.7 twinkly-puzzling-quokka.md; GA.8 MARSYS_JIS_BOOTSTRAP_HANDOFF.md existence verification — the latter verified 2026-04-24 at this step's production: 32.5 KB, exists, frontmatter consistent).
- Missing scheduled-maintenance records: LIVING_PROJECT_MAINTENANCE_GUIDE cadences not observed (quarterly heatmap; annual Varshphal + LEL bump + MSR review).

**GA.N mapped**: GA.6 (phantom), GA.7 (phantom + staleness; prevention of recurrence), GA.8 (verified at §C.5 production — existence confirmed), GA.11 (unreferenced supporting artifacts — the hygiene cadence re-registers them), GA.12 (LEL_v1.1 hygiene — Step 11 decision), GA.17 (session-naming schema — Step 10), GA.18 (next-objective schema — Step 10), GA.19 (you-are-here marker — Step 10 replaces the minimal marker this rebuild cycle installs), GA.21 (SESSION_LOG entry-per-touched-file discipline — this axis's primary obligation).

**Controls**:
- **Preventive**: artifact creation template requires FILE_REGISTRY row + GOVERNANCE_STACK §1 row at the same session. SESSION_LOG entry is required per session and enumerates `files_touched` as a structured list. Session-open (§F) refuses to start if STEP_LEDGER's latest SESSION_LOG entry is missing or malformed.
- **Detective**: schema validator (§I) cross-checks per-session that every `files_touched` entry has (a) a registry row update or existing-entry acknowledgement and (b) an artifact frontmatter update (`updated_at` or equivalent). Missing cross-reference fails validation.
- **Corrective**: session cannot close without reconciling every `files_touched` entry. Fail-modes trigger a post-close hygiene session whose own scope is solely the reconciliation.

**Enforcement mechanism**: `schema_validator.py` (§I) + the FILE_REGISTRY + GOVERNANCE_STACK + SESSION_LOG triad + ongoing hygiene policies (Step 12 extension; this axis anchors the policies Step 12 will refine). Phantom-reference detection is a dedicated drift-detector check (§H.3.4).

### C.6 — Axis 6: Multi-Agent Collaboration (Claude ↔ Gemini sync, session-open handshake, session-close checklist)

**Definition.** Claude-side and Gemini-side governance surfaces are kept in continuous semantic parity per ND.1 Mirror Discipline. Session-open and session-close templates include cross-agent mirror checks; the disagreement register captures inter-agent conflicts including mirror-desync as a first-class class.

**Threats**:
- Mirror-desync (unchecked): one side of a mirror pair diverges from its counterpart and no session detects it (GA.13: "the policy has already been violated within days of being written"; ND.1: promotes mirror discipline to a first-class axis).
- Silent overwriting: on detecting a mirror-desync, a session overwrites the stale side without logging the divergence as a disagreement (ND.1 §J / §K guard against this).
- Asymmetric updates: Claude-side update without Gemini-side mirror, or vice versa, both against ND.1's bidirectional-obligation claim.
- Two-pass mismatch: Claude-reconciler rejects a Gemini-connector proposal without the rejection being logged to DISAGREEMENT_REGISTER (per MP §3.4.C step 2 + §IS.5).
- Future-agent admission without mirror cascade: adding a third agent without updating all mirror pairs per MP §3.4.E.

**GA.N + directive mapped**: GA.13 (procedural-to-mechanical conversion — this axis is the conversion for mirror discipline specifically), GA.14 (no drift-detection for cross-agent sync — `mirror_enforcer.py` fills this), GA.31 (multi-agent collaboration as protocol — resolved at MP v2.0 §3.4 and §IS.2; this axis operationalizes), ND.1 (primary directive this axis implements).

**Controls**:
- **Preventive**: every change to a Claude-side governance surface triggers a mirror update to its Gemini-side counterpart in the same session (per ND.1 §1 bidirectional obligation). Session-open handshake (§F) carries a `mirror_pair_freshness_check` field citing the last-update timestamps per pair; session-close checklist (§G) carries a `mirror_updates_propagated` list.
- **Detective**: `mirror_enforcer.py` (§J) runs at every session close over the full mirror-pair inventory (CANONICAL_ARTIFACTS mirror_obligations column). Mirror-desync emits a DISAGREEMENT_REGISTER entry of class `mirror_desync` — not a silent correction.
- **Corrective**: mirror-desync is resolved via §K disagreement protocol: (1) identify authoritative side from CANONICAL_ARTIFACTS; (2) update non-authoritative side to adapted parity; (3) log resolution to DISAGREEMENT_REGISTER with rationale and both sides' state-before/state-after hashes.

**Enforcement mechanism**: `mirror_enforcer.py` (§J; Step 7 deliverable) + DISAGREEMENT_REGISTER (§K; Step 7 deliverable) + SESSION_OPEN_TEMPLATE + SESSION_CLOSE_TEMPLATE. Explicit ND.1 citation carried in every artifact this axis produces.

---

## §D — ARTIFACT REGISTRY REDESIGN

### D.1 — The decision: keep FILE_REGISTRY and GOVERNANCE_STACK separate; add CANONICAL_ARTIFACTS as a narrow-purpose third

Three registries govern different slices of the project's state:

| Registry | Purpose | Audience | Primary consumer |
|---|---|---|---|
| `FILE_REGISTRY_v1_2.md` (and successors) | Complete inventory of every artifact on disk with CURRENT / SUPERSEDED / CLOSED / ARCHIVAL status, organized by layer (L0, L1, L2, L2.5, L3, L4/L5, Architecture/Governance) | Humans auditing the corpus; grep-friendly | Session-close hygiene; MP §IS.4 enforcement registry |
| `GOVERNANCE_STACK_v1_0.md` (amended in-place; successor is v2.0 when a major change forces schema break) | Version registry (by layer) + confidence ledger + known-gaps register + change-control protocol + red-team cadence + per-session amendment logs | Humans auditing the project's state evolution; change-control record | MP §IS.4 enforcement registry; MP §3.10 meta-governance approval-protocol log |
| `CANONICAL_ARTIFACTS_v1_0.md` (NEW at Step 7; no prior version) | Minimal machine-readable table: canonical artifact ID → CURRENT path + SHA-256 fingerprint + declared version + mirror_obligations (per ND.1) | Scripts: `drift_detector.py`, `schema_validator.py`, `mirror_enforcer.py`; also humans at a glance | The drift/schema/mirror trio at §H/§I/§J |

**Justification for keeping three separate**:

1. **Different consumers, different formats.** FILE_REGISTRY is organized for human grep over the full project inventory. GOVERNANCE_STACK is organized for change-control log-over-time. CANONICAL_ARTIFACTS is organized for machine consumption — a short, flat table of exactly the canonical fingerprints scripts need. Merging FILE_REGISTRY and GOVERNANCE_STACK would force log-entries and status-rows into a single schema whose two parts are read by different audiences on different cadences.
2. **Different update cadences.** FILE_REGISTRY changes whenever a file's CURRENT/SUPERSEDED status changes (possibly several times per session during a supersession cascade; bump to v1.X per change). GOVERNANCE_STACK is amended in-place per session (with a `§N STEP_X amendment log` block appended each time); schema-breaking changes force v2.0. CANONICAL_ARTIFACTS is amended whenever a canonical fingerprint rotates — low-frequency but high-consequence (every script re-runs after every CA amendment).
3. **Different failure modes.** FILE_REGISTRY errors surface as "a superseded file appears CURRENT" or "a CURRENT file is missing." GOVERNANCE_STACK errors surface as "a closure event is missing its amendment log." CANONICAL_ARTIFACTS errors surface as "a script computed a fingerprint mismatch." Merging them would merge their error classes and weaken the post-hoc diagnosis.
4. **MP §IS.1 + §IS.4 already imply this split.** §IS.1 names canonical-artifact discipline; §IS.4 names FILE_REGISTRY + GOVERNANCE_STACK as "enforcement registries." CANONICAL_ARTIFACTS operationalizes §IS.1's claim that "duplication is itself a drift vector" by giving every other surface the one authoritative place to read canonical paths from.

**Decision recorded**: the three-file arrangement above.

### D.2 — FILE_REGISTRY schema (preserved; minor additions at Step 7)

Current FILE_REGISTRY_v1_2.md frontmatter and body structure is preserved. Step 7 amendments (landing in `FILE_REGISTRY_v1_3.md` as part of the Step 7 bundle):

- **Frontmatter (preserved)**: `artifact`, `version`, `status`, `date`, `scope`, `supersedes`, `changelog`.
- **Body (preserved)**: §1 L0, §2 L1, §3 L2, §4 L2.5, §5 L3, §6 L4/L5, §7 Working/platform, §8 Archival, §9 Architecture & Governance (including §9.1 architecture-and-governance rows + §9.2 governance-rebuild-family rows + §9.3 STEP_BRIEFS rows).
- **New columns Step 7 adds**: per-row `canonical_artifact_id` field pointing at a CANONICAL_ARTIFACTS entry when the row names a canonical artifact; `mirror_obligations` summary column whose authoritative detail lives in CANONICAL_ARTIFACTS.

### D.3 — GOVERNANCE_STACK schema (preserved; Step 7 adds §10 amendment continuation)

Current GOVERNANCE_STACK_v1_0.md structure is preserved. Schema:

- **Frontmatter (preserved)**: `artifact`, `version` (string with `-updated-STEP_X` suffix for in-place amendments), `status`, `session` (multi-session comma list), `date_closed`, `date_updated`, `scope`, `architecture_ref`.
- **Body (preserved)**: §1 Version Registry (by layer); §2 Confidence Ledger; §3 Known Gaps; §4 Change-Control Protocol; §5 Red-Team Cadence; §6 Maintenance Schedule; §7 Closure Events; §8 Amendment Logs §STEP_5 (Macro Plan closure); §9 STEP_5 amendment log; §10 STEP_5A amendment log; (Step 7 adds) §11 STEP_7 amendment log.

Decision: GOVERNANCE_STACK stays amendable in-place; v1.0-updated-STEP_N pattern continues through Step 15. A v2.0 GOVERNANCE_STACK is triggered only when a schema-break (new section class, field removal) is necessary; Step 7 additions do not break schema.

### D.4 — CANONICAL_ARTIFACTS_v1_0.md schema (NEW; Step 7 produces)

The authoritative specification follows in §E. Summary here: one row per canonical artifact with `canonical_id`, `path`, `version`, `status`, `fingerprint_sha256`, `mirror_obligations`, `last_verified_session`, `last_verified_on`.

### D.5 — How the three registries stay synchronized

- Whenever an artifact's CURRENT version bumps (e.g., MSR_v3_0 → MSR_v4_0 at some future date): FILE_REGISTRY bumps its version (to, say, `FILE_REGISTRY_v1_3.md`), GOVERNANCE_STACK amends in-place (`§N STEP_X amendment log`), CANONICAL_ARTIFACTS bumps its fingerprint row for that canonical_id and any surfaces that cite the path directly are mirror-updated per §J.
- The drift detector (§H) cross-checks all three pairwise every session close. Any two-of-three consensus or any lone disagreement is flagged.
- The schema validator (§I) verifies each registry's frontmatter and body schema on every artifact write.

---

## §E — CANONICAL PATH DECLARATION PROTOCOL

### E.1 — The artifact: `CANONICAL_ARTIFACTS_v1_0.md`

File path: `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md`. Produced by Step 7 as the highest-priority artifact in the implementation bundle (§M priority P1). No prior version exists. Successors follow the patch/minor/major-bump rules in §L.

### E.2 — Format decision: YAML frontmatter + markdown table hybrid

**Decision**: YAML frontmatter for machine-readable metadata + one primary markdown table per section, with per-row YAML-style key:value attributes for the machine-parseable fields.

**Justification**:

1. **Machine-parseability**. YAML is trivially parsed by Python (`yaml.safe_load`). The scripts in §H/§I/§J need `canonical_id → path + fingerprint + mirror_obligations` at sub-millisecond cost. Pure-markdown parsing would require regex that is fragile to formatting drift.
2. **Human-readability**. Every other governance-layer artifact is primarily markdown. Adding a YAML section + markdown table preserves convention. The table columns display cleanly in any markdown renderer.
3. **Grep-friendly**. A user can `grep MSR_v3_0 CANONICAL_ARTIFACTS_v1_0.md` and see the row. Pure YAML would require `yq` or a script.
4. **Rejection of pure JSON**: JSON in a `.md` file is a poor citizen — breaks the markdown reader experience and offers no grep benefit over YAML.
5. **Rejection of plain markdown table only**: sub-fields (mirror_obligations, asymmetries) are structured; a plain markdown cell cannot hold a nested list without inline HTML or escaping.

### E.3 — Required fields (per row)

Every row represents one canonical artifact. Fields:

| Field | Type | Description |
|---|---|---|
| `canonical_id` | string | Stable ID for this canonical artifact (e.g., `MSR`, `UCN`, `CDLM`, `CGM`, `RM`, `FORENSIC`, `LEL`, `MACRO_PLAN`, `PHASE_B_PLAN`, `PROJECT_ARCHITECTURE`, `FILE_REGISTRY`, `GOVERNANCE_STACK`, `STEP_LEDGER`, `NATIVE_DIRECTIVES`, `CONVERSATION_NAMING_CONVENTION`, `GOVERNANCE_INTEGRITY_PROTOCOL`, `CANONICAL_ARTIFACTS`). The ID does not carry a version; the version field holds the current version. |
| `path` | string (repo-relative) | Current path (e.g., `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md`). Updated when the canonical version rotates. |
| `version` | string | Current version of the artifact (e.g., `3.0` for MSR_v3_0). Free-form since some artifacts carry `v1.0-updated-STEP_5A` patterns. |
| `status` | enum | `CURRENT` / `DRAFT_PENDING_REDTEAM` / `LIVING` / `LIVE` / `CLOSED`. (No `SUPERSEDED` entries in this file — CANONICAL_ARTIFACTS lists only CURRENT.) |
| `fingerprint_sha256` | string (hex) | SHA-256 of the file content at the moment of last verification. Used by `drift_detector.py` to detect silent file mutation. |
| `mirror_obligations` | structured (nested YAML) | Per-pair obligation: `{claude_side: <path>, gemini_side: <path or null>, mirror_mode: adapted_parity\|claude_only\|gemini_only, authoritative_side: claude\|gemini\|none, asymmetries: <free-form string>}`. `null` on `gemini_side` + `mirror_mode: claude_only` indicates declared Claude-only (e.g., GOVERNANCE_STACK, SESSION_LOG). |
| `last_verified_session` | string | Session ID of the last session that re-computed the fingerprint and confirmed the row. |
| `last_verified_on` | date (ISO 8601) | Date of last verification. |
| `notes` | string (optional) | Short free-form; used for transition-state annotations (e.g., "CGM will become CGM_v9_0 after Phase B.3.5"). |

### E.4 — Body structure

Two sections:

- **§1 Canonical artifact table** — one row per `canonical_id` entry per §E.3 fields. Sorted by layer (L1, L2.5, L3, governance) then by `canonical_id` within layer.
- **§2 Mirror-pair inventory (per ND.1)** — the MP.1 through MP.N inventory (currently MP.1–MP.8 per PROJECT_ARCHITECTURE_v2_2 §D.11.2), cross-referenced to the `canonical_id` on each side. Each row carries: `pair_id` (MP.N), `claude_side` (canonical_id or path), `gemini_side` (canonical_id or path or `none`), `authoritative_side`, `mirror_mode`, `enforcement_rule` (how `mirror_enforcer.py` checks this pair), `known_asymmetries`.

### E.5 — Update rules

- **Version bump on any fingerprint change.** Rotating a fingerprint means the file content changed; the row is re-verified in the session that caused the change; the session ID and date are recorded; CANONICAL_ARTIFACTS itself is patch-bumped (v1.0 → v1.0.1) if the update is additive-only to metadata, minor-bumped (v1.0 → v1.1) if a new row is added, major-bumped (v1.0 → v2.0) if the schema changes.
- **Claude-side vs Gemini-side authoritative declaration.** Per ND.1, MP.1 through MP.8 declare an authoritative side. Changes to an authoritative side trigger a mirror update to its counterpart in the same session. Changes to a non-authoritative side (unusual; typically only happens when Gemini sessions edit `.gemini/project_state.md` directly) trigger a mirror update back to the authoritative side in the same session.
- **Never `SUPERSEDED` rows.** Superseded versions are removed from CANONICAL_ARTIFACTS and retained in FILE_REGISTRY §8 Archival. CANONICAL_ARTIFACTS is the CURRENT-only view.

### E.6 — What CANONICAL_ARTIFACTS does NOT do

- Does not duplicate FILE_REGISTRY's full inventory. Only canonical artifacts live here.
- Does not carry amendment logs. Those live in GOVERNANCE_STACK.
- Does not govern closed artifacts (MACRO_PLAN_CRITIQUE, MACRO_PLAN_REDTEAM, STEP_BRIEFS, SESSION_LOG entries). Closed artifacts are registered in FILE_REGISTRY with status `CLOSED` and do not appear in CANONICAL_ARTIFACTS unless they also carry a CURRENT canonical role (e.g., STEP_LEDGER which is LIVE until Step 15 closure).
- Does not replace CLAUDE.md's canonical path table. That table will be rewritten in Step 9 to refer to CANONICAL_ARTIFACTS (by name) rather than re-stating paths. Post-Step-9, CLAUDE.md is a thin pointer into CANONICAL_ARTIFACTS for canonical paths.

---

## §F — SESSION-OPEN HANDSHAKE

### F.1 — The artifact: `SESSION_OPEN_TEMPLATE.md`

File path: `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE.md`. Produced by Step 7 as template material; each session produces an instantiation (appended to SESSION_LOG as the first block of that session's entry).

### F.2 — Mandatory fields

Every session, before any substantive tool call, emits a session-open handshake. Fields:

```yaml
session_open:
  session_id: string                        # unique; "STEP_6_GOVERNANCE_INTEGRITY_DESIGN" during rebuild era; post-rebuild format TBD at Step 10
  cowork_thread_name: string                # per CONVERSATION_NAMING_CONVENTION_v1_0.md §1 (e.g., "Madhav 06 — Governance Integrity Protocol Design")
  agent_name: string                        # "claude-opus-4-6" / "claude-opus-4-7" / "gemini-2-5-pro" / etc. Pinned per MP §3.4.F.
  agent_version: string                     # model version identifier at session open
  step_number_or_macro_phase: string        # "STEP_6" during rebuild; "M2.B.3" post-rebuild for macro-phase + sub-phase
  predecessor_session: string               # session_id of the previous session that handed off to this one; checked against STEP_LEDGER handoff note
  mandatory_reading_confirmation:
    - file: <path>
      fingerprint_sha256: <hex>
      read_at: <ISO timestamp>
    - ... (one entry per item in the mandatory reading list per current CLAUDE.md / current era)
  canonical_artifact_fingerprint_check:
    # Read CANONICAL_ARTIFACTS; re-compute fingerprints of a sampling (per-session-minimum: the canonical artifacts this session intends to touch); compare to declared.
    - canonical_id: MSR
      declared_fingerprint: <hex from CANONICAL_ARTIFACTS>
      observed_fingerprint: <hex from actual file read>
      match: true|false
    - ... (one entry per canonical artifact the session's declared_scope names, plus MACRO_PLAN + CANONICAL_ARTIFACTS itself unconditionally)
  declared_scope:
    may_touch:
      - <path pattern, e.g., "00_ARCHITECTURE/STEP_LEDGER_v1_0.md">
      - <path pattern>
    must_not_touch:
      - <path pattern, e.g., "025_HOLISTIC_SYNTHESIS/**" during Step 6>
  mirror_pair_freshness_check:
    # For every mirror pair in CANONICAL_ARTIFACTS §2, report last_verified_on + gap-in-days since this session opens.
    - pair_id: MP.1
      last_verified_on: <date>
      days_since_verification: <int>
      stale: false|true  # true if days_since_verification > 1 (threshold per §J.4)
    - ... (one entry per mirror pair)
  native_directive_obligations:
    # For every `open` ND.N whose consumption matrix names the current step, enumerate the obligation.
    - directive_id: ND.1
      obligation_summary: "see §J + §K + §N"
      acknowledged: true
  red_team_due: true|false                  # true if this session is the 3rd-session-cadence cycle or the session closes a macro-phase per MP §IS.8
  notes: string                              # free-form
```

### F.3 — Enforcement

The handshake is validated by `schema_validator.py` (§I) before any other action in the session:

- If `mandatory_reading_confirmation` is missing an item from the current mandatory-reading list, the handshake fails.
- If any `canonical_artifact_fingerprint_check` row has `match: false`, the handshake fails (indicates silent file mutation since last CANONICAL_ARTIFACTS update).
- If any `mirror_pair_freshness_check` row has `stale: true`, the session is obligated to run `mirror_enforcer.py` (§J) as its first substantive action and either (a) confirm parity and update the `last_verified_on` field in CANONICAL_ARTIFACTS, or (b) open a DISAGREEMENT_REGISTER mirror-desync entry (§K).
- If `declared_scope.must_not_touch` is empty, the handshake fails (every session must declare both may-touch and must-not-touch positively).
- Any `open` directive's obligation not acknowledged fails the handshake.

A session whose handshake fails does not proceed. It halts and reports.

### F.4 — Conversation-naming rule integration

Per `CONVERSATION_NAMING_CONVENTION_v1_0.md` §4, the session proposes the Cowork thread name at the top of the first substantive response. `cowork_thread_name` in the handshake is the machine-readable mirror of that proposal. The handshake and the first response agree.

### F.5 — GA.N closure

Closes GA.15 (no session-open handshake — primary), GA.19 (no "you are here" marker — the handshake's `step_number_or_macro_phase` + `predecessor_session` fields form the minimal marker; Step 10 upgrades to a proper CURRENT_STATE artifact), GA.26 (native role/cadence — `red_team_due` + handoff ingest replaces the undeclared native-cadence convention at this layer).

---

## §G — SESSION-CLOSE CHECKLIST

### G.1 — The artifact: `SESSION_CLOSE_TEMPLATE.md`

File path: `00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE.md`. Produced by Step 7 as template material; each session produces an instantiation (appended to SESSION_LOG as the closing block of that session's entry).

### G.2 — Mandatory fields

Every session, before claiming close, emits a session-close checklist. Fields:

```yaml
session_close:
  session_id: string                        # same as session_open.session_id
  closed_at: <ISO timestamp>
  files_touched:
    - path: <repo-relative path>
      mutation_type: created|modified|superseded|archived|deleted
      sha256_before: <hex or null for created>
      sha256_after: <hex or null for deleted>
      justification: string                 # one-line rationale tying to declared_scope
      within_declared_scope: true|false
    - ... (one entry per touched file)
  registry_updates_made:
    file_registry:
      - row_before: <excerpt or "new">
        row_after: <excerpt>
        version_of_registry: <e.g., v1.3>
    governance_stack:
      - section: §11 STEP_7 amendment log
        entry_excerpt: <first 200 chars>
    canonical_artifacts:
      - canonical_id: <id>
        change: fingerprint_rotated|version_bumped|added|status_changed
        details: string
  mirror_updates_propagated:
    # For every mirror pair touched this session, confirm the counterpart was updated in the same session.
    - pair_id: MP.1
      claude_side_touched: true|false
      gemini_side_touched: true|false
      both_updated_same_session: true|false
      rationale: string (required if one side only)
  red_team_pass:
    due: true|false                         # from session_open.red_team_due
    performed: true|false
    verdict: PASS|PASS_WITH_FIXES|FAIL|n/a
    artifact_path: <path or null>
  drift_detector_run:
    script: drift_detector.py
    exit_code: 0|nonzero
    report_path: <path or null>
    divergences_found: <int>
  schema_validator_run:
    script: schema_validator.py
    exit_code: 0|nonzero
    report_path: <path or null>
    violations_found: <int>
  mirror_enforcer_run:
    script: mirror_enforcer.py
    exit_code: 0|nonzero
    report_path: <path or null>
    desync_pairs: []                        # list of pair_ids
  step_ledger_updated: true|false           # rebuild-era only; post-Step-15 becomes CURRENT_STATE update
  current_state_updated: true|false         # post-Step-10 field; n/a pre-Step-10
  session_log_appended: true|false
  disagreement_register_entries_opened: []  # list of DR entry IDs if any
  native_directive_per_step_verification:
    - directive_id: ND.1
      step: STEP_6
      obligation_addressed: true|false
      evidence: string                      # which sections/artifacts satisfy the obligation
  close_criteria_met: true|false            # all checklist boxes green
  unblocks: <next step or next phase pointer>
  handoff_notes: string                     # brief for the next session
```

### G.3 — Enforcement

Every field with a `true|false` value must be `true` for the session to close. Any `exit_code: nonzero` from any script fails the close. Any `within_declared_scope: false` row fails the close. Any mirror pair with `both_updated_same_session: false` fails the close unless the rationale explains a declared Claude-only or Gemini-only pair (e.g., GOVERNANCE_STACK is Claude-only per MP.6).

The schema validator (§I) verifies the checklist itself as its last action. Only after the checklist validates does the SESSION_LOG append happen atomically.

### G.4 — Integration with STEP_LEDGER (rebuild-era) and CURRENT_STATE (post-Step-10)

- **Rebuild era (Steps 0–15)**: `step_ledger_updated: true` is required. The checklist's `unblocks` field corresponds to the ledger's per-row `status` transition (`completed` + next step `ready`).
- **Post-rebuild (after Step 15 closes GOVERNANCE_BASELINE_v1_0)**: `current_state_updated: true` is required. `step_ledger_updated` becomes `n/a` and is dropped (or schema-amended away at Step 10).

### G.5 — GA.N closure

Closes GA.16 (no session-close checklist — primary), GA.21 (no automated SESSION_LOG entry-per-touched-file — `files_touched` + `session_log_appended` enforce this), GA.20 (scope-boundary unenforced — `within_declared_scope` is checked per row), GA.13 (procedural-to-mechanical — exit-code-required fields cannot be honor-skipped).

---

## §H — DRIFT-DETECTION SCRIPT SPEC

### H.1 — The artifact: `drift_detector.py`

File path: `platform/scripts/governance/drift_detector.py`. Produced by Step 7 as part of the implementation bundle. Language: Python 3.10+ (matches existing `platform/scripts/` convention — `citation_graph_builder.py`, `invariants_l1.py`, `corpus_common.py`).

### H.2 — Inputs

- `CANONICAL_ARTIFACTS_v1_0.md` (read: canonical path + fingerprint per canonical_id; authoritative source for cross-surface comparison).
- `/CLAUDE.md` (read: canonical path table — to be mirrored in CANONICAL_ARTIFACTS after Step 9).
- `/.geminirules` (read: canonical path block + Mirror Discipline section).
- `/.gemini/project_state.md` (read: canonical corpus state block).
- `00_ARCHITECTURE/FILE_REGISTRY_v1_2.md` (current version; read: §9 Architecture/Governance + §4 L2.5 rows).
- `00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md` (read: §1 Version Registry).
- `00_ARCHITECTURE/STEP_LEDGER_v1_0.md` (read during rebuild era: the full ledger for one-in-progress-at-a-time invariant and prerequisite satisfaction).
- `00_ARCHITECTURE/MACRO_PLAN_v2_0.md` (read: active-macro-phase pointer per status field + any per-macro-phase claims about PHASE_B_PLAN binding).
- `00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md` (read: active-sub-phase pointer).
- Filesystem: every path cited in the above surfaces; verify existence.

### H.3 — Checks performed

**H.3.1 — Canonical path table parity (CLAUDE.md ↔ `.geminirules` ↔ CANONICAL_ARTIFACTS)**

For each canonical_id in CANONICAL_ARTIFACTS: verify (a) CLAUDE.md names the same path (where CLAUDE.md cites it explicitly — post-Step-9 this becomes an "imports CANONICAL_ARTIFACTS by reference" check); (b) `.geminirules` canonical-path block names the same path (for the subset of canonical_ids Gemini-side surfaces reference — MP.5 defines this subset); (c) version in each surface matches CANONICAL_ARTIFACTS.

**H.3.2 — CANONICAL_ARTIFACTS ↔ filesystem**

For each canonical_id: verify the declared `path` exists on disk; compute sha256 of the file; compare to declared `fingerprint_sha256`. Any mismatch is a drift-detector finding (class: `fingerprint_mismatch`).

**H.3.3 — MACRO_PLAN ↔ PHASE_B_PLAN alignment**

Verify: the active macro-phase declared in MP v2.0 matches the macro-phase governed by the current PHASE_B_PLAN; where PHASE_B_PLAN names an MP macro-phase (currently M2), that name matches MP's §The ten macro-phases §M2 row; any PHASE_B_PLAN live-pointer to a superseded MP version is a finding (picks up WARN.2 recurrence).

**H.3.4 — STEP_LEDGER internal consistency (rebuild era only)**

Verify: exactly one row has `status: in_progress`; every `ready` row's predecessor (per column `blocked_by` or implicit sequence) is `completed`; no `superseded` rows claim `ready` or `in_progress`; the `updated_at` frontmatter field has a timestamp within the last 30 days (stale STEP_LEDGER is itself a finding).

**H.3.5 — FILE_REGISTRY ↔ CANONICAL_ARTIFACTS agreement**

For each canonical_id in CANONICAL_ARTIFACTS: find the corresponding row in FILE_REGISTRY; verify status is `CURRENT` (not `SUPERSEDED`); verify path matches. Finding class: `registry_disagreement`.

**H.3.6 — GOVERNANCE_STACK ↔ CANONICAL_ARTIFACTS agreement**

For each canonical_id: find the corresponding row in GOVERNANCE_STACK §1 Version Registry; verify version and status. Finding class: `governance_stack_disagreement`.

**H.3.7 — Phantom-reference scan**

Grep every governance-layer file (CLAUDE.md, `.geminirules`, `.gemini/project_state.md`, all `00_ARCHITECTURE/*.md` except closed/time-stamped artifacts per §B.2) for live pointers (`backtick-quoted paths`, `markdown links`). For each pointer, verify the referenced path exists on disk. Finding class: `phantom_reference`. Known-deferred classes (WARN.2–WARN.7 per STEP_LEDGER history) are whitelisted with their ticket references until their booking step (Step 9 or PHASE_B_PLAN v1.0.3) resolves them.

**H.3.8 — Unreferenced canonical-artifact scan**

For each canonical_id in CANONICAL_ARTIFACTS: verify at least one governance surface (CLAUDE.md or `.geminirules` or FILE_REGISTRY §9) names it. Finding class: `canonical_unreferenced`. Closes GA.9, GA.10, GA.11 at the detection layer once Step 9 CLAUDE.md rebuild surfaces them.

### H.4 — Output

**Exit code**: 0 if no findings; 1 if CRITICAL findings; 2 if HIGH; 3 if only MEDIUM/LOW; 4 on script-internal error.

**Report**: structured JSON at `00_ARCHITECTURE/drift_reports/DRIFT_REPORT_<session_id>_<ISO-timestamp>.json`, schema:

```yaml
drift_report:
  session_id: string
  run_at: <ISO timestamp>
  findings:
    - class: fingerprint_mismatch|registry_disagreement|governance_stack_disagreement|phantom_reference|canonical_unreferenced|step_ledger_violation|macro_plan_phase_plan_drift|mirror_path_disagreement
      severity: CRITICAL|HIGH|MEDIUM|LOW
      canonical_id: <if applicable>
      surfaces_involved: [<path>, <path>, ...]
      evidence: <quoted sentence or row>
      suggested_remediation: string
      whitelist_ticket: <WARN.N or null>
  summary:
    total: <int>
    by_class: {...}
    by_severity: {...}
  exit_code: <int>
```

### H.5 — Failure modes

- Script-internal error (IO failure, YAML parse error): exit 4; report is partial and tagged `incomplete: true`.
- File missing: each missing file is a finding of class `phantom_reference` (the script does not halt).
- `mirror_enforcer.py` integration: the drift detector does NOT duplicate mirror-enforcer's job. It covers fingerprint + registry + phantom + ledger. Mirror-desync is the mirror enforcer's job (§J). The two scripts are called sequentially at session close.

### H.6 — GA.N closure

Closes GA.1 + GA.2 + GA.4 + GA.5 + GA.7 + GA.13 + GA.14 (primary — this script is the mechanical enforcement that GA.14 explicitly names missing) + GA.19 (via H.3.4) + the recurrence-prevention half of GA.6 + GA.8 + GA.9 + GA.10 + GA.11.

---

## §I — SCHEMA VALIDATOR SPEC

### I.1 — The artifact: `schema_validator.py`

File path: `platform/scripts/governance/schema_validator.py`. Produced by Step 7. Python 3.10+.

### I.2 — Inputs

- All files under `00_ARCHITECTURE/*.md` (except STEP_BRIEFS/ which have their own lightweight schema — optional validation).
- All files under `025_HOLISTIC_SYNTHESIS/*.md`.
- `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` and `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`.
- `03_DOMAIN_REPORTS/*.md` (nine L3 reports).
- Optional: session-open and session-close YAML blocks (validated against the schemas in §F.2 and §G.2 above).

### I.3 — Validations performed

**I.3.1 — Frontmatter per artifact class**

Each artifact has a minimum required frontmatter field set per its class:

- **Architecture/Governance class (00_ARCHITECTURE/*.md)**: `artifact`, `version`, `status`, (optional) `supersedes`, (optional) `produced_during`, `changelog` (when `version` is > 1.0 or amended). The schema validator loads the class-to-fields map from a declared JSON/YAML config in the script (not hard-coded).
- **L1 facts class (01_FACTS_LAYER/*.md)**: `artifact`, `version`, `status`, `subject`, `source_hash`.
- **L2.5 synthesis class (025_HOLISTIC_SYNTHESIS/*.md)**: per-artifact-specific templates (MSR: `signal_count`, `canonical_path`, `supersedes`, `unification_session`; UCN: `parts`, `part_precedence`; CDLM: `grid_dimensions`, `cell_count`; RM: `element_count`, `element_subtypes`; CGM: `node_count`, `edge_count`, `rebuild_base_l1`).
- **L3 domain reports class (03_DOMAIN_REPORTS/*.md)**: `artifact`, `version`, `status`, `domain`, `l1_basis_version`, `l2_5_basis_version`.
- **Session artifact class (SESSION_LOG entries, STEP_LEDGER rows, session-open/close blocks)**: per §F.2 and §G.2.

**I.3.2 — MSR/UCN/CDLM/RM/CGM required fields (per each artifact's declared template)**

Per PROJECT_ARCHITECTURE §G detailed specs. The schema validator loads the per-artifact template from the CANONICAL_ARTIFACTS mirror_obligations column's `schema_template` field (Step 7 populates this column).

**I.3.3 — SESSION_LOG entry schema**

Every SESSION_LOG entry has: `session_open` block (per §F), body (free-form, per session style), `session_close` block (per §G). The validator verifies structural presence, not content quality.

**I.3.4 — STEP_LEDGER row schema (rebuild era)**

Per STEP_LEDGER_v1_0.md's frontmatter declaration of row columns: `step`, `title`, `status`, `deliverable(s)`, `evidence`, `blocking_notes`. History entries have their own free-form-but-dated structure.

**I.3.5 — Mirror-pair structural equivalence**

For each mirror pair per ND.1 MP.1–MP.8: verify the "shape" of the parity-bearing sections on both sides is equivalent (e.g., if Claude-side CLAUDE.md has a "Mandatory reading" block with N items, Gemini-side `.geminirules` has a "Mandatory reading before any work" block with N items — adapted to Gemini's phrasing, not byte-identical). The structural check is: header count, list count, item count per list. Content parity is the mirror-enforcer's job (§J).

**I.3.6 — Registry-row-per-touched-file discipline (per Axis 5)**

For each session's close-checklist `files_touched` list: verify every entry appears either (a) as a new or updated row in FILE_REGISTRY within the same session, or (b) as an amendment-log entry in GOVERNANCE_STACK within the same session, or (c) as an explicitly-declared "no registry update required" entry with rationale.

**I.3.7 — Version-monotonicity**

For each canonical artifact: verify the versions in FILE_REGISTRY, GOVERNANCE_STACK, and CANONICAL_ARTIFACTS are monotonic (not regressing). A rollback (version decrease) requires an explicit `rollback_rationale` field or fails validation.

### I.4 — Output

**Exit code**: 0 if clean; 1 on any CRITICAL violation; 2 on HIGH; 3 on MEDIUM/LOW; 4 on script-internal error.

**Report**: structured JSON at `00_ARCHITECTURE/schema_reports/SCHEMA_REPORT_<session_id>_<ISO-timestamp>.json`.

### I.5 — GA.N closure

Closes GA.21 (primary — orphan-mutation detection; via I.3.6), GA.17 + GA.18 (SESSION_LOG and next-objective schemas — bound to Step 10; schema validator extension lands at Step 10), GA.19 (via I.3.4 STEP_LEDGER internal validation + downstream Step 10 CURRENT_STATE validation).

---

## §J — MIRROR ENFORCER SPEC

### J.1 — The artifact: `mirror_enforcer.py`

File path: `platform/scripts/governance/mirror_enforcer.py`. Produced by Step 7. Implements native directive **ND.1 — Mirror Discipline as a First-Class Governance Principle** verbatim.

### J.2 — Inputs

- `CANONICAL_ARTIFACTS_v1_0.md` §2 Mirror-pair inventory (read: per-pair authoritative side + mirror mode + enforcement rule + known asymmetries).
- Every file named in any pair's `claude_side` or `gemini_side` field.
- Semantic-parity rules — a small, declarative-not-NLP rule set for each mirror mode. The rules are authored in Step 7 as part of CANONICAL_ARTIFACTS §3 (a new subsection); this protocol does not pre-specify them as implementable rules, only the policy they enforce.

### J.3 — Mirror-pair inventory enforcement (per ND.1)

For each mirror pair (currently MP.1 through MP.8 per PROJECT_ARCHITECTURE_v2_2 §D.11.2):

| Pair | Claude-side | Gemini-side | Authoritative | Enforcement rule this script applies |
|---|---|---|---|---|
| **MP.1** | `CLAUDE.md` | `/.geminirules` | Claude-side (master instructions) | Compare structural blocks: mandatory-reading list (same N items, same canonical IDs); canonical-path table (same canonical IDs with Gemini-side a subset per MP.5 scope); governance-rebuild banner (semantic parity); project-overview block (semantic parity). Known asymmetries per §J.5 (Claude Code/MCP/skills references; Gemini-rules idiom). Fail on structural-block mismatch; fail on canonical-ID disagreement; pass with asymmetries-noted on byte-level differences within each paired block. |
| **MP.2** | Composite of `SESSION_LOG.md` + `STEP_LEDGER_v1_0.md` + active phase/macro-plan pointers | `/.gemini/project_state.md` | Claude-side (authoritative state lives in the composite) | Compare: "current executed step" (Gemini side) vs STEP_LEDGER's single `in_progress` or latest `completed` row (Claude side); "next step" (Gemini side) vs STEP_LEDGER's `ready` row; canonical corpus state block (Gemini side) vs CANONICAL_ARTIFACTS's CURRENT rows; pending actions (Gemini side) vs SESSION_LOG's tail handoff note. Fail on state disagreement; pass on adapted-phrasing differences. |
| **MP.3** | `MACRO_PLAN_v2_0.md` | Compact MP summary in `.geminirules` + `.gemini/project_state.md` | Claude-side | Compare: MP version pointer (`.geminirules` item #3 ↔ MP frontmatter); ten-macro-phase arc summary (Gemini-side compact list matches MP §The ten macro-phases by count and by M1..M10 names); Learning Layer + System Integrity Substrate mentions (Gemini side names both, not necessarily with full IS.1–IS.9 detail). Fail on version disagreement; fail on macro-phase-name disagreement; pass on summary-vs-full differences. |
| **MP.4** | `PHASE_B_PLAN_v1_0.md` (v1.0.2) | Phase-B pointer in `.gemini/project_state.md` + `.geminirules` item #4 | Claude-side | Compare: PHASE_B_PLAN version pointer (Gemini side cites v1.0.2 matching PHASE_B_PLAN frontmatter); pause-during-rebuild banner (Gemini side reflects the paused state while STEP_LEDGER is LIVE). Fail on version disagreement. |
| **MP.5** | `FILE_REGISTRY_v1_2.md` (CURRENT) | Canonical-path block in `.geminirules` (L2.5 paths) | Claude-side | Compare: the L2.5 path subset Gemini side carries (MSR_v3_0 / UCN_v4_0 / CDLM_v1_1 / CGM_v2_0 / RM_v2_0) vs FILE_REGISTRY §4. Fail on path disagreement; pass if Gemini side is a proper subset with no contradictions. |
| **MP.6** | `GOVERNANCE_STACK_v1_0.md` | (none — Claude-only) | Claude-only | No enforcement; the pair is declared Claude-only. The script emits a PASS_DECLARED_CLAUDE_ONLY entry in the report. |
| **MP.7** | `SESSION_LOG.md` | (none — Claude-only per Step 5A decision) | Claude-only | Same as MP.6. |
| **MP.8** | `PROJECT_ARCHITECTURE_v2_2.md` | Compact architecture reference in `.geminirules` + `.gemini/project_state.md` | Claude-side | Compare: architecture version pointer (`.geminirules` item #2 and `.gemini/project_state.md` canonical corpus state); five-layer architecture summary (Gemini-side matches PROJECT_ARCHITECTURE §C by layer count and by L0..L4 names); mirror-pair inventory cite (Gemini side references `PROJECT_ARCHITECTURE_v2_2.md §D.11.2` as the architecture-layer first pass). Fail on version disagreement; fail on layer-naming disagreement. |

**Future mirror pairs (MP.9+)**: added to the inventory as new pairs arise (e.g., if a Gemini-side SESSION_LOG-of-convenience is later introduced, MP.7 is re-opened; if a third agent is admitted per MP §3.4.E, new pairs MP.9+ are added with their own enforcement rules). Each new pair is added to CANONICAL_ARTIFACTS + mirror_enforcer.py rule set within the same session that introduces the pair.

### J.4 — Cadence: when the script runs

- **At every session close** as part of the §G checklist — exit code 0 required.
- **On-demand during session** — if the session-open handshake's `mirror_pair_freshness_check` flags any pair as `stale: true` (defined: `days_since_verification > 1`, enforced strictly because this project's cadence is daily).
- **Scheduled** — daily at a consistent time (Step 12 ongoing-hygiene deliverable decides exact time; likely end-of-day native-time).

The reason enforcement is script-based, not git-hook-based: git hooks assume every change passes through `git`, but the Cowork workflow edits files directly and only commits periodically. A git hook would under-fire relative to the daily session cadence. A script called at every session close + scheduled run covers the real pattern.

### J.5 — Asymmetry declaration

Per ND.1 "Asymmetries to preserve (not defects)": Claude-side files may contain Claude-specific constructs (Claude Code / MCP / skills references) with no Gemini equivalent. Gemini-side files may contain Gemini-specific constructs (Gemini-rules idiom) with no Claude equivalent. The mirror enforcer's rule set declares these asymmetries explicitly per pair:

- **MP.1**: Claude-only sections — CLAUDE.md's `##Collaboration with Gemini` is Claude-addressing; `.geminirules` counterpart `##Mirror Discipline (ND.1) — Collaboration with Claude` is Gemini-addressing. Neither side has a mirror for Claude-Code-specific hooks or MCP server references. These are whitelisted.
- **MP.2**: Claude-only sections — SESSION_LOG historical entries (time-stamped; Gemini-side only carries the current state, not the history).
- **MP.3 / MP.4**: Gemini-side carries compact summaries; full content is Claude-side. Not considered a desync; the comparison is between summary and its-source-of-truth, not full-vs-full.
- **MP.5**: Gemini-side carries a proper subset of FILE_REGISTRY (L2.5 only). Subset relationship is the declared asymmetry.
- **MP.6, MP.7**: Declared Claude-only. No enforcement.
- **MP.8**: Gemini-side carries a compact architecture summary; full v2.2 text is Claude-side.

Each asymmetry is declared once in CANONICAL_ARTIFACTS §2 (per-pair `known_asymmetries` field) and once in the script's rule set. Drift between the two declarations is itself a finding (class: `asymmetry_declaration_drift`).

### J.6 — Output

**Exit code**: 0 if all pairs clean; 1 on any mirror-desync; 2 on asymmetry-declaration drift; 3 on declared-Claude-only or declared-Gemini-only mismatches between CANONICAL_ARTIFACTS and the rule set; 4 on script-internal error.

**Report**: structured JSON at `00_ARCHITECTURE/mirror_reports/MIRROR_REPORT_<session_id>_<ISO-timestamp>.json`. Schema:

```yaml
mirror_report:
  session_id: string
  run_at: <ISO timestamp>
  pairs_checked: <int>
  pairs_passed: <int>
  pairs_failed: <int>
  pairs_claude_only: <int>
  pairs_gemini_only: <int>
  findings:
    - pair_id: MP.N
      finding_class: mirror_desync|asymmetry_declaration_drift|subset_relationship_violation
      severity: CRITICAL|HIGH|MEDIUM
      authoritative_side: claude|gemini|none
      which_side_stale: claude|gemini|both
      section_affected: <path#anchor or "whole-file">
      evidence_claude: <excerpt>
      evidence_gemini: <excerpt>
      suggested_remediation: "update <stale_side> to semantic parity with <authoritative_side>; log resolution to DISAGREEMENT_REGISTER as mirror_desync class"
  exit_code: <int>
```

### J.7 — Explicit ND.1 citation

This script implements ND.1 verbatim:
- ND.1 claim 1 (bidirectional obligation) — enforced by the session-close requirement that `mirror_updates_propagated.both_updated_same_session: true` per pair touched.
- ND.1 claim 2 (adapted parity, not byte-identity) — implemented via the per-pair rule set that compares structural blocks and semantic content, not bytes.
- ND.1 claim 3 (scope beyond CLAUDE.md) — implemented via the full MP.1–MP.8 inventory, not just MP.1.

### J.8 — GA.N + ND.1 closure

Closes ND.1 (primary — this is the script-layer implementation that ND.1 demands) + GA.13 (procedural-to-mechanical conversion; the mirror-enforcement half) + GA.14 (no drift-detection for cross-agent sync — the mirror-enforcer is the script).

---

## §K — MULTI-AGENT DISAGREEMENT PROTOCOL

> **Mirror discipline retired 2026-05-27 per native directive ND.1 close-out.** The mirror-desync class (DIS.class.mirror_desync) and §K.3 mirror arbitration sub-protocol below are RETIRED; the remaining four disagreement classes (output_conflict, version_disagreement, scope_disagreement, closure_disagreement) remain in force. References to `mirror_enforcer.py`, `.geminirules`, and Gemini-side surfaces are historical.

### K.1 — The artifact: `DISAGREEMENT_REGISTER.md` (or `DISAGREEMENT_REGISTER_v1_0.md`)

File path: `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md`. Produced by Step 7 as a LIVING artifact (per GA naming convention similar to NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md). Rows are appended; rows are never deleted; resolved rows carry a `resolved_on` + `resolution` field.

### K.2 — Disagreement classes

Four classes, enumerated (mirror-desync RETIRED 2026-05-27):

| Class | Trigger | Example |
|---|---|---|
| **DIS.class.output_conflict** | Two sessions reach conflicting conclusions on the same input (a pattern proposal, a reconciliation, a validation verdict) | Session A proposes pattern P with evidence E; Session B rejects on P1 layer-separation grounds. |
| **DIS.class.version_disagreement** | Two governance surfaces claim different CURRENT versions for the same canonical artifact | FILE_REGISTRY says MSR_v2_0 CURRENT; CLAUDE.md says MSR_v3_0 CURRENT (GA.1 was exactly this). |
| **DIS.class.scope_disagreement** | Two sessions disagree on whether a proposal is in-scope for the current macro-phase | M2 session proposes a pattern that requires M4-era calibration data; another session rejects scope. |
| **DIS.class.closure_disagreement** | Two sessions disagree on whether a close criterion is met | Session N claims Step X closed; Session N+1 re-opens on grounds of an unmet criterion. |

### K.3 — Arbitration protocol (per MP §3.4.C, expanded for this spec)

1. **Isolation re-run.** Each session produces its output in isolation (no sight of the other's output). If isolation re-run reverts the disagreement, the disagreement was an artifact of cross-contamination and is closed with that rationale.
2. **Reconciler resolution attempt.** A reconciling session reviews both isolation-outputs and attempts resolution with explicit rationale. Resolution is logged alongside the DR entry.
3. **Native arbitration.** If the reconciler cannot resolve (or native wishes to arbitrate), escalate. Native arbitration is logged with its own rationale.
4. **Registration in FALSIFIER_REGISTRY / CONTRADICTION_REGISTRY**, when appropriate. An output-conflict disagreement that reveals a testable falsifier (e.g., P6 UCN-authority conflict on a specific signal) is cross-referenced to FALSIFIER_REGISTRY for future verification.

*Mirror-desync special handling RETIRED 2026-05-27 per native directive ND.1 close-out.*

### K.4 — DR entry schema

```yaml
disagreement_register_entry:
  dr_id: DIS.001, DIS.002, ...              # sequential
  class: output_conflict|version_disagreement|scope_disagreement|closure_disagreement
  opened_on: <ISO date>
  opened_by_session: <session_id>
  parties: [<session_id>, <session_id>]
  description: string                        # 2–5 sentences; what the disagreement is
  authoritative_side: none|n/a               # "n/a" for pure output_conflict; "none" for legitimate open conflict
  evidence_side_a: <excerpt + path or session reference>
  evidence_side_b: <excerpt + path or session reference>
  arbitration_steps_taken:
    - step: isolation_re_run|reconciler_resolution|native_arbitration|cross_reg_registration
      result: string
      timestamp: <ISO>
  status: open|resolved|escalated|reopened
  resolution: string (free-form; present if status == resolved)
  resolved_on: <ISO date or null>
  resolved_by_session: <session_id or null>
  linked_artifacts:
    - path: <path>
      linkage: "cause"|"remediation"|"evidence"|"registry_updated"
```

### K.5 — (RETIRED 2026-05-27)

Mirror-desync class and the bidirectional Claude↔Gemini parity discipline that motivated it are retired per native directive ND.1 close-out. Historical entries in `DISAGREEMENT_REGISTER_v1_0.md` carrying class `mirror_desync` remain as audit trail.

### K.6 — Integration with SESSION_LOG and STEP_LEDGER

- Every open DR entry is referenced in the session's close-checklist `disagreement_register_entries_opened` field.
- Every resolved DR entry is referenced in the resolving session's close-checklist.
- STEP_LEDGER (rebuild era) and the forthcoming CURRENT_STATE (post-Step-10) surface a summary count of open DR entries as a governance-health metric.

### K.7 — GA.N + ND.1 closure

Closes ND.1 (secondary — §J is primary; §K implements the disagreement-class half of ND.1's consumption matrix) + GA.31 (multi-agent-collaboration-as-protocol — resolved at MP §3.4 level; operationalized here via DR entry schema and arbitration protocol).

---

## §L — GOVERNANCE META-RULES (how this protocol itself is revised)

### L.1 — Version-bump triggers

The Governance & Integrity Protocol is revised when:

1. A new ND.N directive is issued that requires changes to §J (Mirror enforcer) or §K (Disagreement protocol) or to the axis set §C.
2. Any Step 7 implementation detail reveals a spec gap (e.g., a required field in §F.2 that `SESSION_OPEN_TEMPLATE` cannot populate) — triggers a spec amendment.
3. A new mirror pair is admitted (e.g., MP.9 on future-agent admission); §J and §E both update.
4. A new canonical-artifact class is admitted (e.g., if a new L4 Discovery Layer artifact class becomes canonical at M2 close); §E schema extends.
5. An annual red-team of this protocol surfaces defects (≥ 1 CRITICAL or ≥ 3 HIGH) — bump triggered.
6. A schema-break to CANONICAL_ARTIFACTS itself forces a reference re-alignment in §E, §H, §I, §J.

### L.2 — Version semantics

- **v1.X additive** — new controls in an axis; new enforcement mechanism; new DR class; new mirror pair; new script check. Schema preserved.
- **v2.X architectural** — axis set changes (e.g., a seventh axis is introduced); schema break in CANONICAL_ARTIFACTS; reorganization of §C, §E, or §J that forces all Step 7 scripts to re-align.
- **v3.X scope-redefining** — protocol extends beyond governance surfaces (e.g., to user-facing publication compliance per MP §3.5.B post-M10); or substrate change that mirrors a MP v3.X event.

Ambiguity resolves upward per MP §3.10.D.

### L.3 — Approval protocol

Revision → revision-spec artifact (e.g., `GOVERNANCE_INTEGRITY_PROTOCOL_REVISION_SPEC_vX_Y.md`) → red-team on the spec → native approval → version bump → mirror update per §J across all affected surfaces (primarily CLAUDE.md reference to this protocol + `.geminirules` if cross-agent-facing sections change) → STEP_LEDGER entry (rebuild era) or CURRENT_STATE entry (post-rebuild) → SESSION_LOG entry → updated FILE_REGISTRY + GOVERNANCE_STACK rows.

### L.4 — Red-team cadence

- **Annual.** This protocol is red-teamed every 12 months regardless of phase state, per MP §IS.8 + §3.10.C. Findings tagged per the Step 1 critique convention (MPC-style) re-used as `GIPRT-style` (Governance Integrity Protocol Red-Team).
- **On each new ND.N.** A new native directive triggers a targeted red-team of §J + §K + §N for that directive's consumption obligation.
- **At each macro-phase close.** The phase's red-team includes a governance-integrity-protocol-alignment pass: does the phase's closing state still match this protocol's claims?
- **On script failure at meaningful rate.** If drift detector / schema validator / mirror enforcer emit > 3 CRITICALs per week over two consecutive weeks, the protocol is red-teamed for whether its enforcement rules are correctly calibrated.

### L.5 — Sunset clause

Protocol is SUPERSEDED when either: (a) a successor protocol is published (e.g., GOVERNANCE_INTEGRITY_PROTOCOL_v2_0.md admitted at some future date); OR (b) the project enters a steady-state regime where governance-integrity is fully folded into CURRENT_STATE + CANONICAL_ARTIFACTS + the three scripts, and this markdown specification is no longer the source of truth — at which point the protocol is marked ARCHIVAL-SUPERSEDED-BY-IMPLEMENTATION. Neither condition applies in v1.0 lifecycle.

### L.6 — Changelog requirement

Every revision ships with a frontmatter `changelog` entry naming: the revision spec path, the red-team verdict, the approval date, the `produced_during` tag, and whether this revision triggers a mirror cascade.

### L.7 — Status field

Frontmatter `status:` carries exactly one of: `DRAFT_PENDING_REDTEAM` / `CURRENT` / `SUPERSEDED` / `ARCHIVAL-SUPERSEDED-BY-IMPLEMENTATION` at all times. v1.0 ships as `DRAFT_PENDING_REDTEAM` (this file) and flips to `CURRENT` at Step 8 close if red-team verdict is PASS or PASS_WITH_FIXES.

---

## §M — IMPLEMENTATION HAND-OFF (Step 7 deliverables)

This section is the implementable spec for Step 7. A fresh conversation reading only §M (plus the brief cross-references below) can implement the full bundle without re-reading §A–§L. The brief cross-references required are: §C for threat-to-axis mapping; §E for CANONICAL_ARTIFACTS schema; §F for SESSION_OPEN_TEMPLATE schema; §G for SESSION_CLOSE_TEMPLATE schema; §H–§J for the three scripts; §K for DISAGREEMENT_REGISTER.

### M.1 — Deliverables (priority order)

| Priority | Artifact | Path | Description | Depends on |
|---|---|---|---|---|
| **P1** | `CANONICAL_ARTIFACTS_v1_0.md` | `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md` | Machine-readable canonical-path + mirror-pair inventory. Schema per §E.3 + §E.4. Populated with every CURRENT canonical artifact (MSR, UCN, CDLM, CGM, RM, FORENSIC, LEL, MACRO_PLAN, PHASE_B_PLAN, PROJECT_ARCHITECTURE, FILE_REGISTRY, GOVERNANCE_STACK, STEP_LEDGER, NATIVE_DIRECTIVES, CONVERSATION_NAMING_CONVENTION, GOVERNANCE_INTEGRITY_PROTOCOL, CANONICAL_ARTIFACTS itself). MP.1–MP.8 mirror-pair inventory transcribed from PROJECT_ARCHITECTURE_v2_2 §D.11.2 with machine-parseable fields. | (none — highest priority; everything else reads this) |
| **P1** | `SESSION_OPEN_TEMPLATE.md` | `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE.md` | Template for the session-open handshake. Schema per §F.2. Carries a worked example for a rebuild-era step and a post-rebuild-era session. | CANONICAL_ARTIFACTS |
| **P1** | `SESSION_CLOSE_TEMPLATE.md` | `00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE.md` | Template for the session-close checklist. Schema per §G.2. Carries a worked example. | CANONICAL_ARTIFACTS |
| **P1** | `DISAGREEMENT_REGISTER_v1_0.md` | `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md` | Skeleton with frontmatter + §0 purpose + §1 directive classes (per §K.2) + §2 DR entry template (per §K.4) + §3 arbitration protocol (per §K.3). Zero entries at creation; entries accumulate from Step 7 onward. | CANONICAL_ARTIFACTS |
| **P2** | `drift_detector.py` | `platform/scripts/governance/drift_detector.py` | Full implementation per §H. Unit-tested with at least one fixture per finding class (§H.3.1 through §H.3.8). Exit-code convention per §H.4. | CANONICAL_ARTIFACTS; SESSION_OPEN_TEMPLATE (to read session_id field) |
| **P2** | `schema_validator.py` | `platform/scripts/governance/schema_validator.py` | Full implementation per §I. Schema-config YAML at `platform/scripts/governance/schemas/` (per-artifact-class frontmatter-required-fields map). Unit-tested per §I.3 sub-check. | CANONICAL_ARTIFACTS; SESSION_OPEN_TEMPLATE; SESSION_CLOSE_TEMPLATE |
| **P2** | `mirror_enforcer.py` | `platform/scripts/governance/mirror_enforcer.py` | Full implementation per §J. Per-pair rule set authored in Python; declarative-not-NLP. Unit-tested per MP.1–MP.8 pair. Exit-code convention per §J.6. | CANONICAL_ARTIFACTS |
| **P3** | `.geminirules` (edited) | `/.geminirules` | Re-authored to adapted-parity mirror per ND.1 interpretation. Adds an "Asymmetries" section (Step 7 obligation per ND.1 §J.5). Updates the Mirror Discipline section's scope clause to name `CANONICAL_ARTIFACTS_v1_0.md` as the authoritative inventory (promotes the current PROJECT_ARCHITECTURE §D.11.2 reference to its script-ready successor). | CANONICAL_ARTIFACTS; SESSION_OPEN_TEMPLATE |
| **P3** | `.gemini/project_state.md` (edited) | `/.gemini/project_state.md` | Re-authored to adapted-parity mirror. Adds an "Asymmetries" section. Updates canonical corpus state block to cite CANONICAL_ARTIFACTS by reference. | CANONICAL_ARTIFACTS |
| **P3** | `FILE_REGISTRY_v1_3.md` | `00_ARCHITECTURE/FILE_REGISTRY_v1_3.md` | Additive bump from v1.2. Registers CANONICAL_ARTIFACTS + GOVERNANCE_INTEGRITY_PROTOCOL + DISAGREEMENT_REGISTER + SESSION_OPEN_TEMPLATE + SESSION_CLOSE_TEMPLATE + the three scripts (as working-folder entries). Adds `canonical_artifact_id` and `mirror_obligations` columns per §D.2. | CANONICAL_ARTIFACTS; all Step 7 artifacts |
| **P3** | `GOVERNANCE_STACK_v1_0.md` (amended in-place) | `00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md` | Frontmatter version string → `1.0-updated-STEP_7_GOVERNANCE_INTEGRITY_IMPLEMENTATION`. §1 Architecture/Governance block adds rows for the new artifacts. §11 STEP_7 amendment log appended with full propagation-surfaces list + ND.1 verification. | all Step 7 artifacts |
| **P4** | `DRIFT_REPORT_STEP_7_v1_0.md` | `00_ARCHITECTURE/drift_reports/DRIFT_REPORT_STEP_7_v1_0.md` | First production run of `drift_detector.py` against the full repo. Baseline report. Any findings here flagged for the Step 13 baseline run to reconcile. | drift_detector.py complete |
| **P4** | `SCHEMA_VALIDATION_REPORT_STEP_7_v1_0.md` | `00_ARCHITECTURE/schema_reports/SCHEMA_VALIDATION_REPORT_STEP_7_v1_0.md` | First production run of `schema_validator.py`. Baseline report. Flagged for Step 14. | schema_validator.py complete |
| **P5** | `CLAUDE.md` (edited, minor) | `/CLAUDE.md` | **Deferred to Step 9 per Step 6 brief §4 constraint.** Step 7 does NOT rewrite CLAUDE.md; it leaves the mandatory-reading list untouched except for adding a single line: "Session-open handshake: emit per `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE.md`." — the minimum needed for sessions to start using the template before Step 9 full rebuild. This is a tracked amendment, not a rebuild. | all Step 7 artifacts |

### M.2 — Step 7 close criteria (anticipatory; binding on Step 7)

- [ ] All P1 artifacts exist.
- [ ] All P2 scripts pass their unit tests.
- [ ] `drift_detector.py` exits 0 against the post-Step-7 repo state (baseline clean) OR emits only deferred-WARN-whitelisted findings.
- [ ] `schema_validator.py` exits 0 against the post-Step-7 repo state.
- [ ] `mirror_enforcer.py` exits 0 against the post-Step-7 repo state.
- [ ] `.geminirules` + `.gemini/project_state.md` mirror updated in the same session as this protocol's adoption.
- [ ] FILE_REGISTRY bumped to v1_3; GOVERNANCE_STACK amended.
- [ ] DRIFT_REPORT_STEP_7 + SCHEMA_VALIDATION_REPORT_STEP_7 produced.
- [ ] ND.1 global status flips from `open` to `addressed` per its consumption matrix close condition.
- [ ] STEP_LEDGER Step 7 row → `completed`.
- [ ] SESSION_LOG appended.

### M.3 — Out-of-scope for Step 7 (deferred to later steps)

- **CLAUDE.md wholesale rebuild** → Step 9.
- **SESSION_LOG schema retrofit** (GA.17 naming + GA.18 single-objective) → Step 10.
- **CURRENT_STATE_v1_0.md creation** → Step 10.
- **Learning Layer scaffold decision** → Step 11.
- **Ongoing hygiene policies** (cadence for running the scripts scheduled; LEL/Varshphal/Heatmap quarterly cadences) → Step 12.
- **Baseline drift-detection run** (as a formal step deliverable, not just the P4 report) → Step 13.
- **Baseline schema-validation run** (ditto) → Step 14.
- **Governance baseline close** → Step 15.

---

## §N — FINDING COVERAGE TABLE

This table binds every GROUNDING_AUDIT_v1_0 finding (GA.1–GA.32) and every `open` native directive whose consumption matrix names Step 6 (currently ND.1) to one or more axes of this protocol, declares the control type, and names the implementation artifact.

Legend:
- **Axis**: C.1–C.6 per §C.
- **Control type**: P = preventive; D = detective; Cr = corrective.
- **Impl artifact**: which Step 7 deliverable closes the loop (per §M.1).
- **Status here**: ADDRESSED | DEFERRED-TO-STEP-N | OUT-OF-SCOPE-RATIONALE | ADDRESSED-AT-MP-LEVEL.

### N.1 — GA.N findings

| Finding | Severity | Class | Owning step per GA | Covered by axis | Control type | Impl artifact | Status here |
|---|---|---|---|---|---|---|---|
| GA.1 | CRITICAL | VERSION-DRIFT | Step 7 + Step 6 | C.2 + C.3 | P + D | CANONICAL_ARTIFACTS; drift_detector; schema_validator | ADDRESSED |
| GA.2 | MEDIUM | VERSION-DRIFT | Step 9 | C.2 | D | drift_detector (numeric parity check) | ADDRESSED-AT-DETECTION-LAYER; full resolution at Step 9 CLAUDE.md rebuild |
| GA.3 | LOW | UNREFERENCED-ARTIFACT | Step 7 | C.3 + C.5 | P | CANONICAL_ARTIFACTS (UCN row + MP.2 pair) + Step 7 `.gemini/project_state.md` re-author | ADDRESSED |
| GA.4 | HIGH | STALENESS | Step 1 + Step 3 | C.2 | D (recurrence prevention) | drift_detector (MP ↔ filesystem check) | ADDRESSED-AT-MP-LEVEL (MP v2.0 §The ten macro-phases §M1 row corrected); recurrence prevented by drift_detector |
| GA.5 | HIGH | STALENESS | Step 1 + Step 3 | C.2 | D (recurrence prevention) | drift_detector | ADDRESSED-AT-MP-LEVEL; recurrence prevented |
| GA.6 | MEDIUM | PHANTOM-REFERENCE | Step 3 + Step 11 | C.5 | D | drift_detector (phantom-reference scan §H.3.7) | ADDRESSED-AT-DETECTION-LAYER; full resolution at Step 11 scaffold decision |
| GA.7 | HIGH | STALENESS + PHANTOM-REFERENCE | Step 7 | C.3 + C.5 + C.6 | P + D + Cr | Step 7 `.gemini/project_state.md` re-author + drift_detector + mirror_enforcer | ADDRESSED |
| GA.8 | LOW | VERIFY | Step 6 | C.5 | D | **Verified at Step 6 production**: `MARSYS_JIS_BOOTSTRAP_HANDOFF.md` exists (32.5 KB, 2026-04-23 timestamp, frontmatter consistent). drift_detector's phantom-reference scan will continue to verify. | ADDRESSED |
| GA.9 | CRITICAL | UNREFERENCED-ARTIFACT | Step 9 | C.3 + C.5 | P | CANONICAL_ARTIFACTS (LEL canonical_id registered) + drift_detector + Step 9 CLAUDE.md rebuild | ADDRESSED-AT-REGISTRY-LEVEL; full surfacing at Step 9 |
| GA.10 | HIGH | UNREFERENCED-ARTIFACT | Step 9 | C.3 + C.5 | P | CANONICAL_ARTIFACTS (GOVERNANCE_STACK canonical_id registered) + Step 9 CLAUDE.md rebuild | ADDRESSED-AT-REGISTRY-LEVEL; full surfacing at Step 9 |
| GA.11 | MEDIUM | UNREFERENCED-ARTIFACT | Step 9 | C.3 + C.5 | P | CANONICAL_ARTIFACTS (all supporting artifacts registered) + Step 9 | ADDRESSED-AT-REGISTRY-LEVEL; full surfacing at Step 9 |
| GA.12 | LOW | HYGIENE | Step 11 | C.5 | Cr | Step 11 or Step 12 — LEL_v1.1 hygiene (retain under `01_FACTS_LAYER/archive/` or mark with SUPERSEDED banner; this protocol does not pre-decide) | DEFERRED-TO-STEP-11-OR-STEP-12 per GA.12 owning-step |
| GA.13 | CRITICAL | SYNC-GAP | Step 7 | C.1–C.6 all (procedural-to-mechanical conversion is the protocol's central design claim per Axiom A.3 + A.5) | P + D + Cr | drift_detector + schema_validator + mirror_enforcer + SESSION_OPEN/CLOSE templates | ADDRESSED |
| GA.14 | HIGH | SYNC-GAP | Step 7 | C.3 + C.6 | D | drift_detector + mirror_enforcer | ADDRESSED |
| GA.15 | MEDIUM | SYNC-GAP | Step 6 | C.4 + C.6 | P | SESSION_OPEN_TEMPLATE | ADDRESSED |
| GA.16 | MEDIUM | SYNC-GAP | Step 6 | C.4 + C.5 + C.6 | D + Cr | SESSION_CLOSE_TEMPLATE | ADDRESSED |
| GA.17 | MEDIUM | SCHEMA-GAP | Step 10 | C.5 | P | Step 10 SESSION_LOG_SCHEMA_v1_0.md | DEFERRED-TO-STEP-10 per GA.17 owning-step; this protocol's §I.3.3 + §I.3.4 provide the minimum validation that Step 10 will upgrade |
| GA.18 | LOW | SCHEMA-GAP | Step 10 | C.4 | P | Step 10 schema | DEFERRED-TO-STEP-10 |
| GA.19 | MEDIUM | SCHEMA-GAP | Step 6 (minimal) + Step 10 (full) | C.4 + C.5 | P + D | §F handshake provides minimal "you are here"; Step 10 CURRENT_STATE_v1_0.md provides full | ADDRESSED-MINIMALLY-HERE; full at Step 10 |
| GA.20 | MEDIUM | SCOPE-CREEP | Step 7 + Step 12 | C.4 | P + D | SESSION_OPEN declared_scope + SESSION_CLOSE within_declared_scope check + schema_validator scope enforcement | ADDRESSED |
| GA.21 | LOW | SCOPE-CREEP | Step 12 | C.5 | D | schema_validator §I.3.6 registry-row-per-touched-file; Step 12 extends cadence | ADDRESSED-AT-DETECTION-LAYER; Step 12 extends |
| GA.22 | HIGH | STALENESS | Step 1 | n/a — Step 1 critique surfaced; Step 3 MP v2.0 resolved | n/a | n/a (MP v2.0 §The ten macro-phases §M1 fully enumerates exit criteria) | ADDRESSED-AT-MP-LEVEL |
| GA.23 | HIGH | SPEC-GAP | Step 1 | n/a — Step 3 MP v2.0 resolved | n/a | n/a (MP §LL-Appendix) | ADDRESSED-AT-MP-LEVEL |
| GA.24 | HIGH | SPEC-GAP | Step 1 | n/a — Step 3 MP v2.0 resolved | n/a | n/a (MP §Cross-cutting workstreams CW.LEL + CW.PPL per 13-field schema) | ADDRESSED-AT-MP-LEVEL |
| GA.25 | MEDIUM | SPEC-GAP | Step 1 | n/a — Step 3 MP v2.0 resolved | n/a | n/a (MP §External Dependency Graph ED.1–ED.9) | ADDRESSED-AT-MP-LEVEL |
| GA.26 | MEDIUM | SPEC-GAP | Step 1 | C.4 (minor — native-cadence declared in SESSION_OPEN `red_team_due` field) | P | SESSION_OPEN_TEMPLATE | ADDRESSED-AT-MP-LEVEL for MP-layer; this protocol operationalizes the cadence-declaration |
| GA.27 | MEDIUM | SPEC-GAP | Step 1 | n/a — Step 3 MP v2.0 resolved | n/a | n/a (MP §Time/Effort Stance §3.8.A "phase-indexed, not time-indexed") | ADDRESSED-AT-MP-LEVEL |
| GA.28 | LOW | SPEC-GAP | Step 1 | n/a — Step 3 MP v2.0 resolved | n/a | n/a (MP §Post-M10 Framing §3.9) | ADDRESSED-AT-MP-LEVEL |
| GA.29 | MEDIUM | SPEC-GAP | Step 1 | n/a — Step 3 MP v2.0 resolved | n/a | n/a (MP §Ethical Framework §3.5) | ADDRESSED-AT-MP-LEVEL |
| GA.30 | HIGH | META | Step 1 | C.4 (alignment) | P | n/a (MP §Meta-Governance §3.10) + this §L for the protocol's own meta-governance | ADDRESSED-AT-MP-LEVEL + ADDRESSED-HERE-FOR-PROTOCOL |
| GA.31 | HIGH | SPEC-GAP | Step 1 | C.6 | P + D + Cr | MP §Multi-Agent Collaboration §3.4 + this protocol's §J + §K operationalize | ADDRESSED-AT-MP-LEVEL + OPERATIONALIZED-HERE |
| GA.32 | CRITICAL | META | Step 1 + Step 6 | C.1–C.6 all — this axis set IS the substrate this finding demanded | P + D + Cr | entire protocol | ADDRESSED |

### N.2 — Open native directives (per NATIVE_DIRECTIVES_FOR_REVISION_v1_0 §1 whose consumption matrix names Step 6)

| Directive | Status | Bound step | Covered by axis | Control type | Impl artifact | Status here |
|---|---|---|---|---|---|---|
| **ND.1 — Mirror Discipline as a First-Class Governance Principle** | `open` (global status flips to `addressed` at Step 7 close) | Step 6 (this step's obligation per consumption matrix Row 5) | C.6 (primary) + C.3 (secondary — mirror discipline is a consistency axis too) | P + D + Cr | §J `mirror_enforcer.py` (Step 7 P2 deliverable) + §K DISAGREEMENT_REGISTER (Step 7 P1 deliverable) + §E CANONICAL_ARTIFACTS `mirror_obligations` column (Step 7 P1 deliverable) | **ADDRESSED at design level per Step 6 brief §6 ND.1 close-criterion.** §J enumerates the full MP.1–MP.8 inventory with per-pair enforcement rules and cites ND.1 verbatim (§J.7). §K lists mirror-desync as DIS.class.mirror_desync (§K.2) with full arbitration protocol including the forbidden-silent-overwrite rule (§K.3 step 3). §N carries this ND.1 row explicitly. Global ND.1 flip to `addressed` fires at Step 7 close. |

### N.3 — Coverage audit (aggregate)

- **Total GA.N findings**: 32 (GA.1–GA.32).
- **Total `open` directives bound to Step 6**: 1 (ND.1).
- **CRITICAL findings**: 4 (GA.1, GA.9, GA.13, GA.32). All ADDRESSED.
- **HIGH findings**: 11 (GA.4, GA.5, GA.7, GA.10, GA.14, GA.22, GA.23, GA.24, GA.30, GA.31, + ND.1 which the directive log records as CRITICAL-equivalent). All ADDRESSED or ADDRESSED-AT-MP-LEVEL.
- **MEDIUM findings**: 12. All ADDRESSED or ADDRESSED-AT-DETECTION-LAYER or DEFERRED-WITH-EXPLICIT-DOWNSTREAM-STEP.
- **LOW findings**: 5. All ADDRESSED, DEFERRED, or ADDRESSED-AT-MP-LEVEL.
- **Findings DEFERRED out of Step 6 scope**: GA.12 (Step 11 or Step 12), GA.17 (Step 10), GA.18 (Step 10). Each has an explicit downstream step named in this protocol and in the STEP_BRIEFS.
- **CRITICAL and HIGH coverage**: 100% (Step 6 brief §6 close criterion requires this).

### N.4 — Axis coverage density

- **Axis C.1 (Data Integrity)**: GA.32 (substrate), GA.1 (indirect via registry drift affecting P5 target).
- **Axis C.2 (Data Accuracy)**: GA.1, GA.2, GA.4, GA.5.
- **Axis C.3 (Data Consistency)**: GA.1, GA.3, GA.7, GA.9, GA.10, GA.11, GA.13, GA.14, ND.1.
- **Axis C.4 (Alignment to Goals and Plan)**: GA.15, GA.16, GA.19, GA.20, GA.26, GA.30.
- **Axis C.5 (Living-Document Hygiene)**: GA.6, GA.7, GA.8, GA.11, GA.12, GA.17, GA.18, GA.19, GA.21.
- **Axis C.6 (Multi-Agent Collaboration)**: GA.13, GA.14, GA.31, ND.1 (primary).

Every axis has at least two findings bound. Every finding has at least one axis coverage. No orphans.

---

## §O — APPENDICES

### O.1 — Integration-gate rail (appended 2026-07-27, ŚODHANA-ŚEṢA fast-follow W3.3)

**Origin.** ŚODHANA's P0 production incident (`SHODHANA_REPORT_v1_0.md` §4): a portal-wide
registration-time monkeypatch (`strict_tool_schema_gate.ts`, PR #805) passed unit tests against a
mocked `server.tool()` and crash-looped `amjis-mcp` in production the moment a real MCP SDK call
reached it — the mock could never have caught the SDK-version-specific positional-overload bug
that caused the crash. Ten track PRs had already merged by the time this was caught in live
post-merge verification, not before. This section codifies the two standing rails that close this
gap for every future multi-track campaign, per the ŚODHANA-ŚEṢA brief's explicit instruction to
record "the incident's lesson, codified."

**Rail 1 — merged-main real-verify before any traffic shift.** Any campaign merging more than one
serving-path PR must, before shifting ANY production traffic to a new revision: (a) build the
deploy candidate from `main` at the exact merge commit the campaign intends to ship (never a
revision merely "newest at the time" — ŚODHANA's own P0 response hit this exact trap on its first
cutover attempt, targeting the wrong revision); (b) hit the deployed-but-not-yet-traffic-shifted
candidate with REAL authenticated calls and check logs — not a health-check ping — before any
canary; (c) canary with real traffic at a small percentage, confirm clean logs, THEN cut over
fully. Each step is confirmed clean before proceeding to the next; a step that isn't clean rolls
back immediately rather than proceeding "to see if it clears up."

**Rail 2 — real-SDK integration test for any portal-wide registration-time gate.** Any mechanism
that wraps or monkeypatches every tool's registration call (a "gate" or "profile" applied at
registration time, portal-wide — as of this writing there are three: the profile gate, the
deprecated-tool gate, the strict-schema gate) requires an integration test that drives the REAL
`@modelcontextprotocol/sdk` `McpServer` — not a hand-rolled mock of `server.tool()` — before it
ships. The regression test PR #812 added
(`platform-mcp/src/lib/__tests__/strict_tool_schema_gate.test.ts`'s real-SDK addition, A/B-verified
to fail on the pre-fix code and pass on the fix) is the template: construct a real `McpServer`
instance, register a tool through the gate exactly as production does, and assert the registration
does not throw — for both a flat shape and a nested-optional shape (the exact shape class that
crashed). A mocked `server.tool()` cannot catch an SDK-version-specific registration-parser bug by
construction; only the real SDK can.

**Enforcement.** These are process rails, not (yet) mechanically enforced by `drift_detector.py`/
`schema_validator.py` — a future step may add a static check (e.g. grep for `server.tool(` calls
inside files matching `*_gate.ts`/`*_monkeypatch.ts` and require a co-located `*.integration.test.ts`
importing `@modelcontextprotocol/sdk` directly). Recorded here now, mechanized later, per this
protocol's own A.6 (the protocol is a living artifact).

### O.2 — Verify production traffic state directly; never trust a green deploy workflow alone (appended 2026-07-27, ŚODHANA-ŚEṢA close-out)

**Origin.** During this campaign's own close, `amjis-mcp`'s Cloud Run traffic spec was found
hard-pinned by revision name to a stale revision left over from an earlier session (a `canary2`
tag from a prior incident response). Three consecutive automatic "Deploy to Cloud Run" workflow
runs — each reported `conclusion: success` — built and readied new revisions that never received
any traffic, because a named-revision traffic pin does not get overridden by a plain
`deploy-cloudrun` action invocation the way routing-to-`latest` would. Production silently served
stale code through all three "successful" deploys. This was caught only because the close protocol
requires confirming production state directly, not because any CI signal flagged it.

**Rail.** Before declaring "production == `main` HEAD" at any session or campaign close that
touched `amjis-mcp` (or any other Cloud Run service with tag-based traffic history), run
`gcloud run services describe <service> --format=json` and check `spec.traffic` directly:
confirm either (a) traffic is split via `latestRevision: true` (always routes to newest), or (b) if
traffic is pinned by explicit `revisionName`, that the pinned revision's image actually matches the
commit being verified. A green deploy-workflow badge proves a new revision was BUILT and marked
Ready; it does not prove that revision is receiving traffic. This is the same class of gap §O.1
addresses (a passing check that doesn't test the thing that actually matters) — recorded as its
own rail because the failure mode is different: not a code defect, but a traffic-routing state
that silently persists across unrelated deploys until someone checks it directly.

---

## §P — CROSS-TOOL ORIENTATION, DECISION, AND LEASE CONVENTION

### P.1 — One governed orientation path

Claude Code and Codex are equal consumers of the governed repository, not of one
another's transient conversation. At session open, each tool first reads
`00_ARCHITECTURE/CURRENT_STATE_v1_0.md` and then
`00_ARCHITECTURE/CROSS_CUTTING_DECISION_REGISTER_v1_0.md`, before selecting further
documents from the mandatory-reading sequence. `CURRENT_STATE` is the live
you-are-here pointer; the CCD register is the append-only record of tool-neutral,
cross-cutting decisions. Stale auxiliary state (`.conductor-state.json`,
`.gemini/project_state.md`, and a `CLAUDECODE_BRIEF.md` marked COMPLETE) is not an
orientation authority.

### P.2 — Decision and work-order authority

The native project owner remains the only authority for scope, production actions,
and decisions that change project policy. Each CCD entry records its decision ID,
authority, affected surfaces, evidence, and any supersession. A session records its
selected work order in the session-open handshake and its result in the session-close
record; the work order is a task record, not a second decision register. A tool must
append a CCD entry when it makes or receives a new cross-cutting decision, and must
cite the precise CCD ID when it consumes one.

### P.3 — Leased worktree discipline

Before work begins, a tool verifies a live lease on the campaign-coordination branch
and records the lease ID, remote verification time, and absolute worktree path in its
session-open handshake. The lease limits the holder to its stated scope and does not
grant production, migration, deployment, or unrelated-edit authority. At close, the
holder records the work-order outcome, updates the governed state it changed, and
releases the lease through the established coordination procedure. Separate tools use
separate task worktrees for concurrent work; a sequential acceptance hand-off may use
one leased worktree only while its lease remains live.

### P.4 — Codex local profiles and scope of this convention

Codex uses the checked-in orientation loader plus the local `madhav-safe` and
`madhav-parity` profiles. Both disable automatic project-document fallback so that the
loader can require the full canonical `CLAUDE.md`, rather than inheriting a truncated
32 KiB fallback. Both expose only the project `marsys-jis` MCP, authenticated through
`MARSYS_MCP_KEY`; the safe profile is reviewable and the parity profile is for explicit
owner-authorized work. This session's native authority permits Codex to acquire and
release only its campaign-coordination lease rows, and to commit and push only those
lease-row changes. All other changes stay uncommitted for owner review. This is the
standing convention for both Claude Code and Codex unless a later CCD entry supersedes
it.

The profiles live at `~/.codex/madhav-safe.config.toml` and
`~/.codex/madhav-parity.config.toml` and launch with `codex -p madhav-safe` and
`codex -p madhav-parity`, respectively. Both use the server's live MCP endpoint
`https://amjis-mcp-938361928218.asia-south1.run.app/mcp`: the unchanged repository
`.mcp.json` root URL returns HTTP 404 to a streamable-HTTP `initialize`, while `/mcp`
returns the server's initialization response. This is a Codex transport normalization,
not a second server or credential surface; the repo configuration remains untouched.
**Warning:** keep the `/mcp` endpoint in both Codex profiles; do not change it back to the
repository root endpoint, which returns HTTP 404 to streamable-HTTP initialization.

### P.5 — Mechanical enforcement and evidence

`SESSION_OPEN_TEMPLATE_v1_0.md`, `SESSION_CLOSE_TEMPLATE_v1_0.md`, and
`platform/scripts/governance/schema_validator.py` require tool identity, profile,
worktree, lease verification, CCD consumption, and close synchronization for newly
created session records. The acceptance suite must use fresh tool sessions, check the
effective MCP surface, discover project skills, and prove a full `CLAUDE.md` read by
citing content beyond byte 32,768. A loader that cannot produce that proof fails the
acceptance test.

---

**END OF GOVERNANCE & INTEGRITY PROTOCOL v1.0.**

*This specification is the Step 6 deliverable of the Step 0 → Step 15 governance rebuild. Status DRAFT_PENDING_REDTEAM until Step 8 closes. Step 7 implements per §M. ND.1 Mirror Discipline addressed at design level per §J + §K + §N.2; global ND.1 status flip to `addressed` fires at Step 7 close per the directive's consumption-matrix close condition.*
