---
artifact: PARIPRASHNA_ARCHITECTURE_v1_0
canonical_id: PARIPRASHNA_ARCHITECTURE
version: 1.0-RC
status: DRAFT_PENDING_REDTEAM
status_note: >
  Substance red-teamed 2026-08-18 (four-lens panel, RED_TEAM_G0_v1_0.md, PASS-WITH-FIXES,
  all fixes applied to the source package) and confirmatory-verified as an assembled
  artifact the same day. Flips to CURRENT at G0 close: native ratification +
  CAPABILITY_MANIFEST/registry rows + SESSION_LOG close (see the G0-close brief).
produced_during: PARIPRASHNA-V012-PHASE1 (Cowork, Fable 5, 2026-08-18; NCD-1..8 native-ruled same day)
date: 2026-08-18
authoritative_side: claude
subordinate_to: >
  CLAUDE.md · PROJECT_ARCHITECTURE_v2_2 · MACRO_PLAN_v2_0 ·
  GOVERNANCE_INTEGRITY_PROTOCOL_v1_0 · CAPABILITY_MANIFEST.json.
  A conflict with any of these is a defect in THIS document.
supersedes: >
  PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md (v0.11) §4–§14A as the live control path,
  upon this artifact reaching CURRENT. That file is then the frozen forensic/history
  record; its §16/§18/§20 remain the corpus of record for how this design was learned.
companion_artifacts:
  - PARIPRASHNA_ASBUILT_BASELINE_v1_0.md (what exists, dated, evidence-classed — LIVING)
  - PARIPRASHNA_DECISION_REGISTER_v1_0.md (every ruling; append-only — LIVING)
  - PARIPRASHNA_VERIFICATION_MATRIX_v1_0.md (PPR → test → rung → gate — LIVING)
  - briefs/pariprashna_v012/ (the Phase-1 review package: contracts, safety, calibration, NFR annexes + red-team record)
changelog:
  - "1.0-RC (2026-08-18): first assembly, from the ruled v0.12 package + TA v0.11 normative content."
---

# Paripraśna — Normative Architecture

*The conversation layer of MARSYS-JIS: the surface through which a person asks
the instrument a question and receives a reading. This document is NORMATIVE
ONLY — what MUST, SHOULD, and MAY be true. What IS true today lives in the
As-Built Baseline. Why things were decided lives in the Decision Register.
How each requirement is proven lives in the Verification Matrix. History
lives in the frozen target-architecture file. Read this in one sitting; it is
designed for that.*

**Keywords.** MUST/MUST NOT = binding; violation is a defect. SHOULD = binding
unless a recorded decision waives it. MAY = permitted discretion.

## §1 — Mission binding and vocabulary

The instrument (CLAUDE.md §A): acharya-grade chart reading · beyond-working-
memory pattern surfacing · time-indexed, probabilistic, calibrated,
correctable prediction · extension beyond the native under the Ethical
Framework · never a fortune-telling product (§L). Paripraśna is that
instrument's conversational face; every requirement below traces to this
mission via the PPR register (§4) and the Verification Matrix.

**Vocabulary (defined here, used everywhere):**
**Reading** — an assistant turn's prose answer. **Receipt** — the
`AcharyaReadingReceipt`, the machine-checkable record a reading MUST earn
(§5.1). **Register** — the single prose voice (D-15): acharya-grade AND
reader-legible, for everyone; never plural. **Disclosure class** — the
consent/access axis (MP §3.5.B): native_self · cohort_subject ·
acharya_reviewer · public; never a quality tier. **Door** — a transport into
the engine (§2). **Hard stop (HS-n)** — a safety rule that blocks output
regardless of who asks (§5.2). **PPR-nn** — a stable requirement ID.
**Gate (G0–G9)** — a release checkpoint (§7). **Evidence class** — how a
current-state claim is known: STATIC_VERIFIED / LIVE_VERIFIED /
DOCUMENT_ASSERTED / UNVERIFIED / SUPERSEDED (NFR annex §1).

## §2 — Doors and their guarantees

Three paths, one core. Transport, authentication, persistence, and
presentation MAY differ per door. **Epistemic reasoning, validation, safety,
and receipt substance MUST NOT differ** (the parity invariant, PPR-30).

| Door | What it is | Reading guarantee |
|---|---|---|
| **Portal Paripraśna** (`/clients/[id]/pariprashna`) | browser, Firebase session, streaming SSE, persistent threads | FULL: core pipeline + receipt + all gates |
| **MCP `prashna_ask`/`prashna_status`** | any LLM client, OAuth/key, job handle | FULL (same core, same gates, same receipt) — target state; parity is Gate 4 |
| **Raw MCP tools** | profile-projected tool surface (`full`/`compact`/`consult`) | **NONE — this is the retrieval/research plane.** The self-describing envelope (density contract, judgment flags, reader labels) is the only defense; every projection's documentation MUST say so. Sensitive-class capabilities MUST be excluded from the `consult` profile. |

## §3 — The channel-neutral core (typed ports)

The engine MUST be callable headlessly and MUST NOT branch on which door it
serves (the boundary test). The pipeline, as ports:

```
NormalizedQuery → EntitlementDecision → SafetyPolicyDecision
  → ScopeTuple | ClarificationRequest → AcharyaPlan
  → ToolBroker → EvidenceBundle → Interpretation & Adjudication
  → Grounding/Safety Validation → SemanticReadingParts
  → TurnProvenance + AcharyaReadingReceipt
```

Binding properties: entitlement resolves from the AUTHENTICATED call, never
from question text (PPR-11); safety classification runs BEFORE planning
(PPR-12); B.11 coverage is enforced by floor compilation, not convention
(PPR-15); the question is data, never instruction (PPR-13); every port's
output is schema-validated at the boundary (a malformed object never crosses).

## §4 — The requirements register

Grouped; each row: normative statement · trace · gate. Verification method
per row lives in the Verification Matrix (same IDs). **This register's
numbering (PPR-01..36) is CANONICAL**; the v0.12 master review's
mission-trace table used a provisional PPR-01..10 spine with different
meanings — superseded by this register, mission traceability now carried by
each row's Trace column. External trace codes used below without local
definition (B.n doctrine, §N.n standards, RS-4, T-8, F-nn defects, FD-n
debts, W-n PB-4 rulings, AC-15, LEL = Life Event Log, MP = MACRO_PLAN) are
labeled pointers into CLAUDE.md, PROJECT_ARCHITECTURE, MACRO_PLAN, the TA
history file, and BRIEF_PB-4 respectively.

### §4.1 Identity, entitlement, tenancy

| ID | Requirement | Trace | Gate |
|---|---|---|---|
| PPR-11 | `chart_id` MUST come from the authenticated call and be re-authorized per capability; object-level authz MUST fail closed. | TA §14A.1; PG2-X4-0002 | standing |
| PPR-21 | The five serving DB roles (role_web_serve · role_orchestrator · role_ledger_write · role_jobs · role_sidecar) MUST exist with their grant walls, and the web app MUST NOT serve reads on a credential holding ledger/calibration write. | NO-LEAKAGE arm-1; F-25q | G1 |
| PPR-22 | Chart-scoped RLS MUST protect C1 (sacred-personal) and C3 (predictive) tables beneath application authz. | NCD-5 RULED | G1 |
| PPR-23 | Cache keys MUST be chart-scoped (SHA-256) with server-side chart-id echo-back. | F-20 fix, carried invariant | standing |

### §4.2 Safety, consent, disclosure (annex: SAFETY_PRIVACY_TENANCY)

| ID | Requirement | Trace | Gate |
|---|---|---|---|
| PPR-12 | A SafetyPolicyGate MUST classify every query BEFORE planning and record its decision on the receipt. Hard stops HS-1 (no date-of-death, unqualified), HS-2 (no suicide-adjacent output; no plan built), HS-3 (health-crisis/mental-health: seal → two independent adversarial passes → separate sign-off), HS-4 (mortality windows: aggregate framing + full HS-3 path), HS-5 (reversibility: receipt-linked retraction), HS-6 (predictive outputs sampled into red-team cadence) MUST be enforced at plan-time, synthesis-time, and pre-wire. | MP §3.5.A/C, verbatim carry | G1 |
| PPR-13 | Prompt-injection containment: question and retrieved content MUST be structurally delimited as data; plans MUST be Zod-closed; tool-sequence anomalies MUST be trace-flagged. | TA §14A.1 | G1 |
| PPR-14 | No L2+ output for a chart whose subject lacks a consent row, unless subject_kind = native_self (strictly: the subject IS the native, or the minor-guardian carve-out). Minors (<18) MUST be excluded from any cohort and MUST NOT be servable beyond the guardian context. Exclusions MUST be logged in the excluded-subject register. Withdrawal MUST trigger verified deletion with tombstone-hashed receipt snapshots. | MP §3.5.A.4/D/F; NCD-9 RULED (adopt at G1, 2026-08-18) | G1 |
| PPR-24 | Disclosure classes MUST gate output classes: acharya_reviewer sees identifying data only with native consent + subject's anonymization choice enforced at serve time; public is FAIL-CLOSED until the §3.9.B publication protocol exists. The register (D-15) MUST remain singular for all classes. | MP §3.5.B; two-axis rule | G1 |
| PPR-25 | Rate limits and spend ceilings ($2/turn · $40/day, ruled) MUST block before dispatch on both serving doors; C3 data MUST never enter a synthesis prompt or leave to a provider; the per-provider data posture MUST be documented, with the strict allowlist arming at the first consented cohort subject. | NCD-8, NCD-6 RULED; F-25d | G1 |
| PPR-26 | Safety decisions, retractions, and consent transitions MUST be written append-only (INSERT-only grant or hash chain). Audit rows MUST reference C1 content by id/hash, never duplicate it. | §N.8; safety annex §5 | G1 |
| PPR-27 | A breach-response note (detection, containment incl. same-day dual-door session/key revocation, subject notification duty disclosed in consent documents) MUST exist before a second subject. | ED.9 | G1 |

### §4.3 Planning, coverage, evidence

| ID | Requirement | Trace | Gate |
|---|---|---|---|
| PPR-15 | Every interpretive query MUST route through a compiled acharya floor enforcing B.11 (whole-chart read); pinpointed factual lookups satisfy B.11 via the RS-4 frame check + escalation valve. The floor's completeness receipt (served/empty/dark, honest `total: null`) MUST reach the receipt. | B.11 + RS-4; §N.6 | standing (built — Baseline §2) / G3 (receipt) |
| PPR-16 | `reading_depth` MUST derive from the scope tuple, not a picker default; depth received MUST be visible (grounding counts + completeness line). | v0.11 A-40 | G2 |
| PPR-17 | Evidence MUST be graded (verified / corroborating / catalog_only / prior_reading / unverified); catalog matches MUST never present as confirmed; honest empties go through flags. prior_reading MUST never satisfy a floor item. | §N.6; §11.5 firewall | standing |
| PPR-18 | The engine MUST be able to ask: clarification as a planner outcome (built — Baseline §2); the pre-plan window-check ask ("Before I answer — in March I indicated X…") MUST run when a closed window overlaps the question's domain. | §6.6; v0.11 A-42 | G8 |

### §4.4 The reading itself (annex: ACHARYA_READING_CONTRACT)

| ID | Requirement | Trace | Gate |
|---|---|---|---|
| PPR-01 | Every interpretive reading MUST emit an `AcharyaReadingReceipt` v1: coverage, facts consumed (by reference, never restated — §N.5), derivation chains, cross-domain block, evidence grades, honest gaps, safety decision, calibration disclosure, prose binding, provenance, receipt hash. Every receipt field MUST be earned by a detector or be null (§N.8). | B.1/B.3; contract annex | G3 |
| PPR-02 | Every SIGNIFICANT interpretive judgment (domain verdict, time-indexed, remedial, prediction-detected, or rules-in-tension) MUST carry ≥3 candidate interpretations, a selected reading with rationale, and a falsifier — or an explicit waiver whose rate is monitored. | B.4, extended to serving | G3 |
| PPR-03 | Every confidence MUST be typed: deterministic_fact · structural_prior · classical_prior · empirically_calibrated · unresolved. `empirically_calibrated` language MUST NOT be used below a passing activation gate; a quantity MUST NOT be served with more precision than its sample supports (T-8). New engine layers surface at their earned tier only. | B.6/B.7; MP §3.5.G; T-8 | G3 |
| PPR-04 | Prose MUST be a restatement of receipt-cited facts (never a re-derivation) in one register, zero internal identifiers, Sanskrit glossed inline, remedies attributive ("the tradition prescribes"), never imperative; difficult findings MUST lead with uncertainty and shorter blocks. | §N.7; D-14/D-15; §13.8/§13.9 | G3 (lint extension) |
| PPR-05 | The reader-facing affordances of the receipt — grounding counts, "Read it another way" (non-selected candidates), "What would change my mind" (falsifier) — MUST be affordances, never forced into the prose flow. | D-15 affordance rule; P2 | G3 |

### §4.5 Render and persistence

| ID | Requirement | Trace | Gate |
|---|---|---|---|
| PPR-06 | Settled content MUST never move (append-only frozen blocks, one volatile tail, stable-geometry chrome, owned scrolling, caret inside the tail). | P1; design plan | standing (built — Baseline §2) |
| PPR-07 | Semantic blocks MUST originate from structured reading intent or deterministic data (kind + role at commit: paragraph, heading, table, verse, gap_ribbon, prediction_card) with paragraph fallback — never solely from heuristic reparse. Tables/verses commit whole. | v0.11 A-37 | G2 |
| PPR-08 | Citations MUST render at final geometry from first paint (server-side sentinel rewrite mid-stream, hold-back bounded, tolerant grammar, per-model hallucination counters); the grounding summary MUST be server-derived, with the client rollup only as the disclosed snapshot-degrade path. | §12.9; v0.11 A-38 | G2 |
| PPR-09 | Every UI control MUST be functional or absent. | v0.11 A-39 | G2 |
| PPR-10 | `settled_visual` and `durably_persisted` MUST be distinct states; persistence MUST use an idempotent outbox/write-ahead with crash recovery and explicit, visible incomplete-turn states. The replay↔persistence parity invariant MUST be a normalized semantic hash (byte equality is rejected; the PR-#927 capture apparatus is repurposed as the comparator's feed). Event and message schemas MUST carry versions with declared compatibility. | v0.12 §7.4 | G2 |
| PPR-19 | Transport resilience MUST hold: seq-replay reconnect over a bounded buffer, disclosed snapshot fallback, visibility-stall reconnect, interrupted turns keep everything received, incomplete turns excluded from prediction detection. Mobile and accessibility MUST meet the design-plan §9 bar (tap-first citations, one polite live region, axe 0 critical/serious). | §12.9.2/§12.11/§12.12 | standing (built — Baseline §2) / G2 (mobile-a11y completion) |

### §4.6 Provenance and reproducibility

| ID | Requirement | Trace | Gate |
|---|---|---|---|
| PPR-20 | Every turn MUST carry TurnProvenance v2: build/priors/formula/ranking versions + now_context_date (the built D-16 core — Baseline §2) PLUS evidence-envelope snapshots or immutable hashed refs, capability-catalog version, planner/prompt/policy/schema versions, model+provider+params, code revision, locale/timezone, answer+receipt hashes. **Snapshot-on-consume is REQUIRED**: a settled reading MUST remain reproducible after its chart rebuilds. The stamp MUST be copied — never referenced — into ledger rows (built: freeze trigger, Baseline §2). The sealed reading is a rendering of this immutable package, content-hashed, corrected append-only. | D-16, extended; v0.12 §7.3 | G2 |

### §4.7 Prediction and calibration (annex: CALIBRATION_METHOD_SPEC)

| ID | Requirement | Trace | Gate |
|---|---|---|---|
| PPR-28 | Predictions MUST be structured at emission; `model_p` (if stated) MUST be immutable from detection; the operator band MUST be immutable from confirm; the two MUST never be conflated. The window MUST be fixed at emission — a mis-parsed window is dismissed and re-registered, never edited. | MP §3.5.E verbatim | G9 (model_p) / standing (seal) |
| PPR-29 | Outcomes MUST use the full taxonomy (binary, partial, censored, lapsed, unverifiable); every served score MUST carry interval + n + resolution coverage; activation MUST be per-cell on effective-sample interval width (±0.15) and coverage floor (60%), ruled; pooling MUST be hierarchical where cells justify it; temporal knowledge cutoffs MUST bound retrospective judgment; recall MUST be independent-then-compare (reading composed before prior conclusions retrieved). Scoring-method changes MUST be versioned; the `calibration_method_version` addition to the Ruling-79 sink is a native-approved amendment (NCD-11 RULED 2026-08-18: amend at build time). | annex §3–§8; NCD-7 RULED | G9 |
| PPR-31 | Life events and outcomes MUST never feed prospective generation (NO-LEAKAGE, four arms: 1 roles+RLS · 2 capability filter · 3 out-of-process writer · 4 CI canary). LEL-drafted outcome suggestions MUST remain post-hoc and human-confirmed. Disagreement MUST be captured as first-class rows; the engine re-retrieves, never re-words, and never folds when data supports the claim. | §14.10/§14.8 | G1 (arms 1,3) / G8 (disputes) |

### §4.8 Model plane and operations (annex: NFR_SLO_AND_EVAL)

| ID | Requirement | Trace | Gate |
|---|---|---|---|
| PPR-32 | Model HEALTH gates dispatch only; model QUALIFICATION (per work class: factual/interpretive/predictive/sensitive, via the eval suite) gates work. Fallback MUST substitute only an equally-qualified model or degrade VISIBLY (flag + provenance). No silent epistemic downgrade, ever. | NFR §3 | G3+ |
| PPR-33 | The SLO table (provisional until baselined) MUST bind after two weeks of measurement on the wired metrics schema (F-25o: wire the existing dead schema, never design a new one). RPO/RTO MUST be stated and drilled (ledger+conversations ≤1h/4h; **one restore drill executed at G1** per the gate plan, then quarterly). | NFR §2 | G1 (drill) / G2 (wire) / G5 (bind) |
| PPR-34 | Proof rungs (STATIC → REPLAY → INTEGRATION → LIVE → NATIVE ACCEPTANCE) MUST be named per verification; a lower rung MUST never substitute for a higher one; current-state claims MUST carry an evidence class and date. | §N.8; NFR §1/§4 | standing |

### §4.9 Doors, parity, release

| ID | Requirement | Trace | Gate |
|---|---|---|---|
| PPR-30 | Portal and `prashna_ask` MUST produce receipt-level-equivalent results for the same question/chart/build (normalized semantic-hash parity test). Until parity passes, prashna_ask's documentation MUST state which gates it lacks. | §6.5 boundary test | G4 |
| PPR-35 | Release MUST follow the gate sequence G0–G9 with each gate's live evidence, rollback, and native point; fidelity (G2–G3) MUST precede the default flip (G5) — RULED; hardening (G1) MUST precede any exposure growth; PB-4's brief executes G5/G7 under its own rulings W-1..W-4 unmodified. | NCD-1 RULED; T-11 | G0–G9 |
| PPR-36 | This document set MUST stay decomposed: normative here; as-built in the Baseline (regenerated per gate); decisions appended to the Register; verification in the Matrix; history frozen. Amendments to THIS file ride ADR entries; no struck prose, no resolved forks, no undated current-state claims may enter it. | NCD-2 RULED; T-10 | standing |

## §5 — Contracts incorporated by reference (binding)

**§5.1 The Acharya Reading Contract** — `briefs/pariprashna_v012/ACHARYA_READING_CONTRACT_v0_1_PROPOSAL.md`
(RATIFIED via NCD-3): receipt schema v1, the significance trigger, the
confidence-type enum, enforcement points. **§5.2 Safety architecture** —
`…/SAFETY_PRIVACY_TENANCY_v0_1_PROPOSAL.md`: HS-1..6, SafetyPolicyGate,
consent schema (NCD-9 RULED: adopt at G1), data classes C1–C5, abuse cases A1–A9,
provider posture. **§5.3 Calibration method** —
`…/CALIBRATION_METHOD_SPEC_v0_1_PROPOSAL.md` (thresholds RULED via NCD-7).
**§5.4 NFR/SLO/eval** — `…/NFR_SLO_AND_EVAL_v0_1_PROPOSAL.md`: evidence
classes, proof ladder, SLO table, quality corpus, AC-15 rubric. At G0 close
these annexes SHOULD be re-issued as versioned canonical artifacts or folded
into this file's later minor versions — decision for the G0 session.

## §6 — Data plane bindings

The conversation store (canonical `message_parts` + summaries), the
prediction ledger (`brahma_mimamsa_prediction_ledger`, 9-state), the ruled
calibration sink (Rulings 55/79), the consent schema (NCD-9), and the
role/RLS walls (PPR-21/22) — current state per the Baseline; the FROZEN
orchestrator and the L0–L5 build DAG are out of scope and sacrosanct (§N.2).
Store completion (history/user turns canonical; tool_call/tool_result/
reasoning parts) is Gate-4 work.

## §7 — Release gates (binding summary)

G0 ratification+decomposition → G1 walls & floors (safety, roles+RLS, caps,
consent, PITR+drill, key) → G2 truth of the surface (semantic blocks,
first-paint citations, honest controls, durable persistence, metrics,
mobile/a11y) → G3 the contract (receipt live + quality corpus) → G4 one
engine in fact (parity) → G5 canary flip (PB-4 F-6 smoke + W-1 hold) → G6
AC-15 + hold (W-4: the native's verdict, never claimed) → G7 retirement
(PB-4 F-5 steps 3–4) → G8 the remembering (recall, arrival line, window-ask,
disputes) → G9 earned calibration. Full per-gate table: v0.12 master review
§11. A gate that promotes a surface MUST re-price every risk priced under
the old exposure (T-11).

## §8 — How this document evolves

Amendments enter via the Decision Register (ADR row first, edit second, same
session). Version semantics per B.8. The three tests every amendment passes:
no current-state claim without evidence class + date; no resolved item left
looking open; still readable in one sitting. When this file and the Baseline
disagree about what exists, the Baseline wins; when it and a governing
artifact disagree about what MUST be, the governing artifact wins and the
conflict is raised as a defect (§21-rule-5 discipline, inherited).

*End PARIPRASHNA_ARCHITECTURE v1.0-RC.*
