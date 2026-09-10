---
artifact: PARIPRASHNA_V012_PHASE1_REVIEW_v0_1
canonical_id: PARIPRASHNA_V012_PHASE1_REVIEW
version: 0.1
status: PROPOSAL — Phase-1 architecture review, now fully discharged as input:
  NCD-1..11 ALL RULED by the native 2026-08-18 (see §13); red-team complete
  (RED_TEAM_G0_v1_0.md, PASS-WITH-FIXES); the v1.0-RC artifact set is authored.
  Remaining G0 mechanics: registration + status flips + SESSION_LOG close, per
  CLAUDECODE_BRIEF_G0_CLOSE_v1_0.md. Authorizes NO code, NO migration, NO
  deployment, NO canonical-file change.
produced_during: PARIPRASHNA-V012-PHASE1 (Cowork, Fable 5, 2026-08-18)
date: 2026-08-18
authoritative_side: claude
role: >
  Reconstitutes the Paripraśna target architecture (v0.11) into a ratifiable
  v0.12/v1.0-RC design package advancing the full Madhav mission. Master
  document of the package; four sibling PROPOSAL annexes carry the Acharya
  Reading Contract, Safety/Privacy/Tenancy, Calibration Method, and NFR/SLO/Eval.
governing_artifacts_read: >
  CLAUDE.md v7.4 (full) · MACRO_PLAN_v2_0 §3.5 Ethical Framework (full) + governance
  sections · PROJECT_ARCHITECTURE_v2_2 (digest, §B/§H.4/§C/§J/§K verified) ·
  CURRENT_STATE_v1_0 §2 (banners through v6.61) · CROSS_CUTTING_DECISION_REGISTER (full)
  · GOVERNANCE_INTEGRITY_PROTOCOL (digest) · ONGOING_HYGIENE_POLICIES (digest) ·
  ROOT_FILE_POLICY (full) · artifact_schemas.yaml (full) · PB close corpus + grounding
  audits (full, from the v0.11 session) · TA v0.11 (full, authored+verified this session-pair).
changelog:
  - "0.1 (2026-08-18): initial Phase-1 package. Same day, in order: NCD-1..8 ruled by
    the native (all recommendations adopted); four-lens red-team panel run
    (PASS-WITH-FIXES, all accepted findings fixed in place — RED_TEAM_G0_v1_0.md);
    NCD-9/10/11 surfaced by the panel and RULED by the native (adopt consent schema
    at G1 · ND directive for the NCD-4 relaxation · amend the Ruling-79 sink at build
    time); v1.0-RC artifact set authored + confirmatory-verified (5 findings fixed).
    §13 and the self-check updated in place at each step."
---

# Paripraśna v0.12 — Phase-1 Architecture Review & Reconstitution Package

## 1 — Executive verdict

**The instrument's conversation layer is built, live behind a flag, and loop-proven —
and it is governed by a document that can no longer govern.** The target
architecture (v0.11, 4,000 lines) is now simultaneously a target-state design,
an as-built census, a forensic archive, and a correction ledger; a fresh agent
cannot extract "what is normative" from it in one sitting, and its own §0
scope rule (current-state facts "only in §16 … and in the 'today' column of
inventory tables, and are marked as such" — quoted in full; the marked-column
allowance covers some but not all of the 42 in-body grounding blocks) is
structurally strained by its own correction protocol. Amend-in-place has
reached its ceiling.

Three deeper verdicts, in mission order:

1. **The epistemic core is under-specified at exactly the serving layer.**
   B.4 (three interpretations + falsifier), B.3 (derivation ledger), B.6/B.7
   (typed, honest confidence) are corpus doctrine with NO serving-layer
   contract. A reading today can be fluent, grounded, register-clean — and
   still un-auditable as a *judgment*. The Acharya Reading Contract (annex,
   §7) closes this: it is doctrine the repo already ratified, extended to the
   turn.
2. **The Ethical Framework is binding governance that is mostly unenforced at
   the serving layer.** Precisely: §3.5.B (disclosure classes), §3.5.C (hard
   stops — no date-of-death, no suicide-adjacent output, double red-team for
   health-crisis/mental-health/mortality), and §3.5.D/F (consent, minors) have
   NO runtime control in the serving path (STATIC_VERIFIED — no safety
   classifier, content gate, or consent check exists in the route or
   `lib/pariprashna/**`). §3.5.E (pre-registration) IS partially enforced
   today — the emission seal, the `trg_bmpl_freeze_confirmed` trigger, and the
   legal-transition matrix are live, as is NO-LEAKAGE arm-2. Tolerable at n=1
   native; disqualifying for mission item 6. The safety annex (§8) translates
   the unenforced clauses into runtime controls, and Gate 1 sequences them
   before exposure grows.
3. **The release order needs one inversion.** v0.11's forward sequence put
   cutover before fidelity; this package inverts it (Gates 2–3 before the
   default flip, §11) because AC-15 — the arc's terminal gate — measured
   against a paragraph-only wire judges the wrong product. Cutover moves
   later; nothing else about BRIEF_PB-4 is disturbed.

The package proposes: a five-artifact decomposition replacing the monolith
(§12), the Acharya Reading Contract (§7), safety/privacy/tenancy architecture
(§8), a calibration method fixed before data accrues (§9), an SLO + eval +
proof-ladder system (§10), a 10-gate release plan (§11), and a decision packet
of eight genuinely-native calls (§13). Nothing was changed anywhere (§15).

## 2 — Evidence ledger and review limitations

Vocabulary per the NFR annex §1 (STATIC_VERIFIED / LIVE_VERIFIED /
DOCUMENT_ASSERTED / UNVERIFIED / SUPERSEDED).

| Claim domain | Class | Basis |
|---|---|---|
| MCP surface: 125 tools, catalog-1+t152+r653c2a1a98c8 | LIVE_VERIFIED 2026-08-18 | `mcp_server_info` this session-pair |
| Paripraśna code state (routes, protocol, lint, samiksha, flags, pickers, unwired modules) | STATIC_VERIFIED at HEAD dfbdfe620 | full source read (v0.11 session census) |
| Repo state: branch `ekv/b-01-dignity-oracle-fix`, dirty set incl. TA v0.11 (uncommitted), CAMPAIGN_COORDINATION.md (staged+modified), AGENTS.md; untracked SAMPURTI scripts + briefs/ekavakyata/ | STATIC_VERIFIED 2026-08-18 | `git status` read-only |
| PB waves, C4 loop proof, flag ON in prod, deploy revisions | DOCUMENT_ASSERTED | REPORT_PB-1/2/3, PB_CAMPAIGN_CLOSE, PURNATA_CLOSE §9 — governed reports, not re-observed live |
| Post-08-01 engine content (PRATIJÑĀ v4.1, GOCHARA v3, ṢAḌ-DARŚANA, SAMPŪRTI) | DOCUMENT_ASSERTED | CURRENT_STATE §2 banners |
| Ethical Framework, doctrine B.1–B.12, §N.6–N.8, ROOT_FILE_POLICY, CCD-001..004 | STATIC_VERIFIED (documents read in full) | this session |
| PITR/backup state TODAY; DB roles TODAY; current Cloud Run env (flag value NOW); currently-serving revision | **UNVERIFIED** | last evidence F-25t (2026-07-19) / F-25q / PB-1 (2026-07-28); no live DB/infra probe was run (Phase-1 read-only, no credentials exercised) |
| "88 tools /health", pre-v0.11 registers, PG-1 counts | SUPERSEDED | v0.11 banner + §16.9 |

**Limitations.** (a) No live probe of DB, the deployed WEB app, or Cloud Run
config — every "live in production" statement about those is
DOCUMENT_ASSERTED and dated. (The one live observation made is the MCP
census itself — a live `mcp_server_info` call against the deployed MCP
surface, hence its LIVE_VERIFIED class.)
(b) The review ran against a snapshot of a FEATURE BRANCH working tree
(`ekv/b-01…`), not `origin/main`; divergence from main was not audited beyond
noting the branch's own commits are engine-side (dignity oracle). (c) The
TA v0.11 under review is itself uncommitted work-in-tree authored by this
session-pair — this package reviews it as content, and its self-review bias
is mitigated by adopting the external feedback's findings where they held.
(d) SESSION_LOG / CURRENT_STATE / COWORK_LEDGER close-entries are NOT written
by this session (Phase-1 constraint) — enumerated as ratification-session
actions in §14, with the GIP §I.3.6(c) "no registry update required" rationale
recorded per file in §14.

## 3 — Severity-ranked architecture findings

| # | Sev | Finding | Evidence | Resolution → where |
|---|---|---|---|---|
| V12-F1 | **CRITICAL** | Ethical Framework §3.5.B/C/D/F unenforced at serving: no safety gate, no disclosure-class model, no consent schema, no minor exclusion; longevity tooling live ungated. (§3.5.E is the exception — its seal/freeze/transition enforcement is live, as is arm-2.) | STATIC_VERIFIED route/census; MP §3.5 read | Safety annex; Gate 1; NCD-4/5/6/9 |
| V12-F2 | **CRITICAL** | NO-LEAKAGE arm-1 still 0% (single `amjis_app` credential, full CRUD on ledger+calibration); no RLS; **currently sequenced post-cutover** | F-25q (STATIC_VERIFIED then; UNVERIFIED today, presumed standing) | Gate 1 (moved pre-cutover); safety annex §7 |
| V12-F3 | **HIGH** | No serving-layer epistemic contract: B.4/B.3/B.6 unenforced per turn; receipts scattered; §J unfalsifiable per reading | doctrine read vs code census | Acharya Reading Contract; Gate 3 |
| V12-F4 | **HIGH** | Reproducibility gap: rebuilds destroy evidence; consumed envelopes not snapshotted; a settled reading is unre-derivable | TA §11.4 own admission ("recorded not solved") | TurnProvenance v2 (§7.3); Gate 2 |
| V12-F5 | **HIGH** | Release order judges the wrong product: AC-15 after a cutover that precedes fidelity (paragraph-only wire, post-hoc citations, cosmetic controls) | v0.11 §19.5 vs FD-1..3 | Gate re-order (§11); NCD-1 |
| V12-F6 | **HIGH** | Durable-persistence semantics unstated: "visually settled" vs "durably persisted" not distinguished; no outbox/write-ahead; byte-equality is the wrong invariant (twice-proven false-confidence) | F-33/Ruling 80; store census | §7.4; Gate 2; semantic-hash parity |
| V12-F7 | **HIGH** | Governing document unreadable as authority: normative/as-built/history/corrections interleaved across 4,000 lines; no requirement IDs; no MUST/SHOULD/MAY | the document itself | Decomposition (§12); NCD-2 |
| V12-F8 | MED | D-15 conflated with §3.5.B disclosure classes; TA §13.4's "open check" never closed against source | MP §3.5.B read | Safety annex §1 (two-axis rule); patch plan |
| V12-F9 | MED | prashna_ask lacks the web door's gates (register lint, sentinel, receipt) — "one engine" is aspiration, parity untested | v0.11 grounded note §6.3 | Gate 4 parity contract (NFR annex §6) |
| V12-F10 | MED | Calibration method undefined pre-data: single probability conflates model/operator; flat n=30; no censoring/ESS/temporal-cutoff rules | ledger schema census; v0.11 §14.6 | Calibration annex; Gate 9 |
| V12-F11 | MED | Model qualification ≠ health absent: fallback can silently change epistemic quality | ModelPlane census; ED.5/6 | NFR annex §3 |
| V12-F12 | MED | No reading-quality eval corpus; proof rungs conflated historically (fixture-as-live) | §N.8 instances; harness census | NFR annex §4–5; Gate 3 |
| V12-F13 | LOW | Staleness residue in v0.11: OpenRouter/Tier-C prescribed in §10/§15 though descoped; "session pin" in §6.2/§11.6; missing §20 v0.10 row now disclosed | TA read | patch plan (§14) |
| V12-F14 | LOW | Provider-privacy posture unstated (what C1 data leaves, retention, training) | no artifact exists | Safety annex §6; Gate 1 |

## 4 — Contradiction / staleness matrix (the 13 charged items, adjudicated)

| # | Charge | Verdict | Severity | Evidence | Resolution | Native? |
|---|---|---|---|---|---|---|
| 1 | filename v0_1 vs frontmatter 0.11 | **NOT-A-DEFECT** (repo convention: filename anchors generation; same pattern as L1_GANITA_CLOSURE_v2_0 @ 2.1) — but a real fresh-agent confusion | LOW | design plan changelog 0.3 note | decomposition names new artifacts cleanly | no |
| 2 | DRAFT/TARGET doc doubling as as-built census | **CONFIRMED** — §0 scope_note vs §16.9 + 42 GROUNDED markers | HIGH | the doc | decomposition (§12) | ratify |
| 3 | D-11 "architecture precedes execution" vs execution happened | **CONFIRMED-AS-TENSION, not violation**: execution ran under ratified campaign briefs (PB master brief, per §21 rule 6's own mechanism); what broke is the DOC's claim to precede | MED | PB corpus | v1.0-RC ratification re-grounds D-11 going forward | ratify |
| 4 | current-state facts outside §16 | **CONFIRMED** (protocol-caused: D-18 corrections must sit at the claim site) | MED | 42 markers | decomposition separates the surfaces | no |
| 5 | resolved items inside Open Decisions | **STALE CHARGE** — fixed at v0.11 (§1.2 + struck rows) | — | TA §1.2 | none needed | no |
| 6 | OpenRouter/Tier-C descoped yet prescribed | **CONFIRMED** residue in §10.4/§10.5/§15 | LOW-MED | TA read | normative doc: REJECTED-FOR-TARGET, design recorded | no |
| 7 | "session pin" residue post-D-16 | **CONFIRMED** minor (§6.2 "session pin" in shared-list; §11.6) | LOW | TA read | mechanical in normative doc | no |
| 8 | "no audience tier" conflated with Ethical disclosure classes | **CONFIRMED AND NOW RESOLVED against source** — §3.5.B is real, orthogonal; TA §13.4's open check closes | HIGH | MP §3.5.B (read in full this session) | two-axis rule (safety annex §1) | ratify naming |
| 9 | "one engine two doors" vs single-pass prashna_ask | **CONFIRMED** (already grounded at v0.11; unresolved in substance) | MED | v0.11 §6.3 note | Gate 4 + parity contract | no |
| 10 | NO-LEAKAGE roles mandatory yet post-cutover | **CONFIRMED** (v0.11 wave 5) | HIGH | v0.11 §19.5 | moved to Gate 1 | ratify |
| 11 | fidelity/citations/controls/observability after flip | **CONFIRMED** (v0.11 wave 2 follows wave 1) | HIGH | v0.11 §19.5 | Gates 2–3 precede flip (§11) | **NCD-1** |
| 12 | no formal trace model across D/A/OT/F/FD/T/waves | **CONFIRMED** | HIGH | the doc | PPR requirement IDs + traceability (§5) + decomposition | ratify |
| 13 | manifest registration of the canonical artifact | **DETERMINED, not assumed**: briefs/** falls outside every validator glob (schemas read); PROPOSAL artifacts need no CANONICAL_ARTIFACTS row (GIP §E.6 — only CURRENT canonical roles); upon ratification the normative architecture MUST gain CAPABILITY_MANIFEST + registry rows; TA v0_1 today has none and needs none until its status changes | MED | artifact_schemas.yaml; GIP §E.6/§C.5 | §14 patch plan step R-6 | at ratification |

## 5 — Traceability: mission → principle → requirement → verification

Requirement IDs (`PPR-##`) are the stable spine the decomposed normative
document carries. Condensed matrix (full expansion belongs to the normative
doc at Gate 0):

| Mission (§A / prompt) | Principle(s) | Requirement | Verified by |
|---|---|---|---|
| 1 Acharya-grade reading | §J, B.11+RS-4, §N.6/7 | **PPR-01** every interpretive turn emits an AcharyaReadingReceipt with coverage, chains, grades | Gate 3 corpus; receipt validator |
| 2 Beyond-working-memory patterns | B.11 Phase-2, CDLM/CGM | **PPR-02** cross_domain block mandatory on interpretive receipts; contradiction surfacing scored | planted-contradiction fixtures |
| 3 Time-indexed probabilistic auditable predictions | §3.5.E/G, B.6 | **PPR-03** structured emission, immutable model_p, fixed window, calibration band or invalid | calibration annex §1–2; schema triggers |
| 4 Facts→derivations→interpretations preserved | B.1/B.3, §N.5 | **PPR-04** receipts reference fact_ids, never restate; prose_binding maps claims to entries | derivation-integrity eval |
| 5 Testable + leakage-safe learning | NO-LEAKAGE ×4, §3.5.E | **PPR-05** arm-1 roles + RLS pre-cutover; C3 data class never in prompts; temporal cutoff | Gate 1 proofs; arm-4 canary |
| 6 Research beyond native under consent | §3.5.B/D/F | **PPR-06** disclosure-class model, consent schema, minor exclusion, verified deletion — BEFORE second subject | Gate 1; safety fixtures |
| 7 Never generic fortune-telling | §L, §3.5.A, T-8 | **PPR-07** typed confidence; structural priors never wear calibrated language; hard stops | T-8 scan; HS fixtures |
| (product) beyond-acharya experience | D-13/14/15, P1–P9 | **PPR-08** semantic blocks live, first-paint citations, honest controls, receipt affordances | Gate 2/3; AC-15 rubric |
| (system) one engine in fact | §6.5 boundary test | **PPR-09** door-parity at receipt level | Gate 4 parity tests |
| (ops) reproducible + recoverable | D-16, §14A.3 | **PPR-10** TurnProvenance v2 with snapshots; durable-persistence protocol; PITR+drill | Gate 1/2 |

## 6 — Proposed target architecture (diagrams)

### 6.1 Context (unchanged topology, honest labels)

```
 Browser (native/guest) ──Firebase──▶ ┌────────────────────────────┐
                                      │ WEB APP                    │
 MCP client (any LLM) ──OAuth/key──▶  │  Portal UI · API routes    │──▶ LLM providers
   │ profiles: full/compact/consult   │  ┌──────────────────────┐  │    (outbound only,
   │                                  │  │ CHANNEL-NEUTRAL CORE │  │     via ModelPlane)
   └── raw tools = RETRIEVAL/RESEARCH │  │  (§6.2 ports)        │  │
       PLANE (no reading guarantee)   │  └──────────────────────┘  │
                                      └────────────┬───────────────┘
                                     python-sidecar│(residual compute)
                                                   ▼
                                      POSTGRES (+pgvector) — layers · registry ·
                                      conversation store · ledger · consent · health
```

### 6.2 Channel-neutral core (typed ports; container/component view)

```
NormalizedQuery
  → EntitlementDecision            (chart grants; object-level authz; RLS beneath)
  → SafetyPolicyDecision           (annex §3: classes, disclosure class, consent, hard stops)
  → ScopeTuple | ClarificationRequest
  → AcharyaPlan                    (floor compiler; unified plan type = wave-4 debt)
  → ToolBroker → EvidenceBundle    (registry dispatch; v3 envelopes; density contracts)
  → Interpretation & Adjudication  (synthesis; B.4 sets; typed confidence)
  → Grounding/Safety Validation    (citation gate; register lint; HS output scan)
  → SemanticReadingParts           (typed blocks: paragraph|table|verse|gap|prediction_card)
  → TurnProvenance + AcharyaReadingReceipt
────────────────────────────────────────────────────────────────────
 TRANSPORT ADAPTERS over the same semantic result:
   · Portal: SSE events (15-event protocol, live)     · MCP: prashna_ask job + prashna_status poll
 MAY differ per door: transport, auth, persistence, presentation.
 MUST NOT differ: epistemic reasoning, validation, safety, receipt substance. (Gate-4 test)
```

### 6.3 Trust boundaries

```
 TB-1 internet ↔ web app         (Firebase session / OAuth+key; rate+spend caps [Gate 1])
 TB-2 app ↔ LLM providers        (data classes per safety annex §5: C1 sacred-personal
                                  and C2 derived leave; C3 predictive NEVER;
                                  provider allowlist per disclosure class)
 TB-3 serving ↔ learning data    (NO-LEAKAGE, four arms: arm-1 DB roles+RLS ·
                                  arm-2 registry/runtime capability filter ·
                                  arm-3 out-of-process ledger writer ·
                                  arm-4 CI canary)
 TB-4 subject ↔ subject          (chart entitlement + consent + RLS; cache keys chart-scoped)
 TB-5 question text ↔ control    (query is data: delimited prompt, Zod-closed plan, chart_id
                                  from auth only, tool-anomaly logging)
```

### 6.4 Portal sequence (as-built + contract deltas ★)

```
POST /api/pariprashna
 → auth → flag → ★SafetyPolicyGate → stream opens: turn.open, phase{plan}
 → planner (Clarification streams as block) → floor compile (B.11) → NO-LEAKAGE filter
 → tools (activity.upsert, reader labels) → synthesis (agentic loop; ★B.4 structured sets)
 → per-delta lint → ★S-3 sentinel rewrite → block.commit (★kind+role typing) → citation.define
 → citation gate → ★receipt assembly → turn.commit → ★durable-persist protocol → turn.close
```

### 6.5 prashna_ask sequence (target: same core)

```
prashna_ask(chart_id, question) → {job_id}            [profile: full|compact only]
 job: auth → ★SafetyPolicyGate → scope → ★SAME AcharyaPlan → tools → ★SAME synthesis+gates
      → SemanticReadingParts + ★receipt → stored result
prashna_status(job_id) → pending|running(pct)|complete{reading, receipt}|failed
 (today: single-pass, no lint/sentinel/receipt — Gate 4 closes the delta)
```

### 6.6 Raw-MCP sequence (retrieval/research plane — labeled)

```
tools/list (profile-projected; sensitive classes excluded from consult)
 → tool call → entitlement (fail-closed CHART_REQUIRED) → envelope
    (density contract; judgment_flags; reader labels in envelope)
 NO reading guarantee: no B.11 floor, no lint, no receipt — the ENVELOPE is the
 only defense (self-describing, loud flags). Stated in every projection's docs.
```

### 6.7 Turn state machine (client, as-built + durable-persist split ★)

```
submitted → thinking → streaming ⇄ reconnecting → settling → settled_visual
                │            │                        │
                │            └─(drop>buffer)→ snapshot_applied → settling
                ├─(clarification)→ awaiting_user                │
                ├─(stop)→ interrupted(kept)          ★settled_visual → durably_persisted
                └─(error)→ errored(classified)        (outbox ack; divergence = visible
                                                       incomplete state, never silent)
```

### 6.8 Prediction state machine (as-built 9-state + calibration-spec annotations ★)

```
detected ──confirm──▶ confirmed ──▶ open ──window_end──▶ window_closed ──▶ outcome_recorded
   │  ★model_p+window immutable      │                      │                (Brier; ★coverage
   │   from here                     ▼                      ├──▶ unverifiable  stamped)
   ├──▶ dismissed              (★edits: none)               └──▶ lapsed
   └─aged──▶ lapsed_unconfirmed                     ★censored = reporting overlay, not a state
```

## 7 — The Acharya Reading Contract → annex

`ACHARYA_READING_CONTRACT_v0_1_PROPOSAL.md`. Receipt schema, B.4 significance
trigger, typed confidence enum, enforcement points, reader affordances
("Read it another way" / "What would change my mind").

**§7.3 TurnProvenance v2** (supersedes the D-16 stamp's field set, keeps its
semantics): adds to {build_id, priors_version, formula_versions,
ranking_config, now_context_date} — evidence-envelope snapshots (or immutable
refs + hashes) for every envelope the turn consumed; capability catalog
version; planner/prompt/policy/schema versions; model+provider+params; code
revision; locale/timezone; answer-part and receipt hashes.
**Snapshot-on-consume is REQUIRED, not optional** (V12-F4): the TA itself
admits a settled reading is unreproducible; for a research instrument that is
constitutive, and the grounding gate already holds the envelopes at commit
(the TA's own "nearly free" observation — now a MUST). Sealed reading = a
rendering of this immutable package, content-hashed, corrections append-only.

**§7.4 Persistence contract** (V12-F6): distinguish `settled_visual` from
`durably_persisted`; write-ahead/outbox with idempotent, retryable writes;
crash recovery replays the outbox; explicit incomplete-turn states; **parity
invariant = normalized semantic hash** of (event-replay projection) vs
(persisted-parts projection) — byte equality is rejected as the invariant
(twice-proven false-confidence). Event/message schemas carry versions with
declared compatibility. Disposition of the existing byte-equality apparatus
(PR #927 capture + replay-compare, Ruling-80 flag-OFF): **repurposed, not
retired** — the capture becomes the input feed for the semantic-hash
comparator, and FD-9's "standing capture posture" closes against the NEW
invariant; no built work is discarded.

## 8 — Safety / privacy / threat model → annex

`SAFETY_PRIVACY_TENANCY_v0_1_PROPOSAL.md`. Two-axis rule (register vs
disclosure class), HS-1..4 runtime hard stops, SafetyPolicyGate, consent
schema + minors, data classes C1–C5, provider posture, roles+RLS, abuse cases
A1–A8, safe logging.

## 9 — Calibration method → annex

`CALIBRATION_METHOD_SPEC_v0_1_PROPOSAL.md`. Two probabilities; emission seal;
outcome taxonomy incl. censoring; coverage-stamped scores; hierarchical
pooling; ESS/interval activation; temporal cutoffs; blinded path;
independent-reading-before-recall; method versioning.

## 10 — NFR / SLO / eval → annex

`NFR_SLO_AND_EVAL_v0_1_PROPOSAL.md`. Evidence classes; SLO table
(provisional-until-baselined; F-25o wiring first); qualification ≠ health;
proof ladder; the Madhav intellectual-quality corpus; AC-15 rubric; door-parity
contract.

## 11 — Reordered gate plan

Replaces v0.11 §19.5's six waves. Each gate row carries deliverables, the
live evidence that is its test, rollback, native point, and early-proceed
risk; **a gate's preconditions are all prior gates passed plus any item its
row names explicitly** (the sequence IS the precondition graph; G1 is the
only gate with no predecessor beyond G0 ratification). PB-4's brief
(`00_ARCHITECTURE/briefs/pariprashna_build/BRIEF_PB-4.md`) is REUSED, split
across gates: lanes F-1 (sidebar), F-2 (empty state/Seal), F-3 (edge-state
lexicon), F-4 (mobile/a11y) fold into **G2**; F-6 (CI smoke, can-fail-proven)
and F-5 steps 1–2 (default flip + seven-green hold, ruling W-1) execute
**G5**; F-5 steps 3–4 (retirement + flag deletion) and Q-2/F-7 execute
**G7**; ruling W-4 (AC-15 handed to the native, never claimed) governs
**G6**. Nothing in the brief is discarded — only its entry conditions grow.
Vocabulary used below: FD-n = fidelity-debt register rows (TA v0.11 §16.9.3);
NCD = Native-Call Decision (§13); HS-n = hard stops (safety annex §2);
"ANTHROPIC key" = the unprovisioned production `ANTHROPIC_API_KEY`
(PURNATA_CLOSE §5 item 1a — the anthropic stack fails instantly, masked by
the Gemini default).

| Gate | Name | Deliverables (headline) | Live evidence required | Rollback | Native point | Risk if early |
|---|---|---|---|---|---|---|
| **G0** | Ratification | this package ruled; decomposition approved; PPR IDs adopted | — | n/a | **ratifies package** | building on unratified architecture repeats the D-11 tension |
| **G1** | Walls & floors | arm-1 five roles + app off amjis_app + RLS on C1/C3; SafetyPolicyGate + HS-1..4; consent schema + minors; rate/spend caps + middleware; PITR verified + one executed restore drill; provider posture doc; ANTHROPIC key provisioned-or-delisted | psql role/grant proof; HS fixtures blocked LIVE; caps observed to block; drill log | grants revertible; gate OFF flag | approves HS-3 native-chart UX (NCD-4) | a default surface (or second subject) atop a single-credential DB and unenforced §3.5.C |
| **G2** | Truth of the surface | semantic blocks live (kind+role at commit); S-3 wired (first-paint chips, server grounding); honest controls (model/length plumbed or removed); durable-persist protocol + outbox; F-25o metrics wired; critical mobile/a11y (PB-4 F-4 scope) | live reading renders table-as-table + chips at first paint; kill-test: persistence divergence surfaces visibly | per-feature flags | reviews the felt surface | AC-15 later judges a renderer that no longer exists |
| **G3** | The contract | AcharyaReadingReceipt emitted on Door 1; B.4 sets + typed confidence; receipt validator; quality corpus v1 passing floors | corpus run on DEPLOYED route; receipts audit-clean | receipt emission flag | ratifies contract (NCD-3) | readings remain unauditable as judgments |
| **G4** | One engine in fact | prashna_ask re-based on the shared core (lint/sentinel/receipt); unified plan type; door-parity tests green | same question, both doors, receipt-hash parity | MCP profile pin to prior impl | — | MCP door ships a different (worse) instrument under the same name |
| **G5** | Canary flip | PB-4 F-6 smoke (can-fail proven) → default flip, flag retained | 7 consecutive green smokes on default (W-1) | flag flip back (W-3) | approves flip | — |
| **G6** | AC-15 + hold | native week-of-use with rubric cards; hold period | 7 rubric cards; unprompted symptom list empty | flag | **the verdict (W-4)** | — |
| **G7** | Retirement | consult/consume retired per refreshed census; flag deleted (PB-4 F-5 steps 3–4) | redirect assertions; zero orphaned importers; grep=0 | git revert + rollback pin | approves irreversible step | deleting the fallback before AC-15 verdict |
| **G8** | The remembering | recall wired (independent-then-compare); arrival line; window-opening ask; dispute capture + feedback restored; digest real; signal reader text top-50 | returning-thread fixtures live; window-ask observed capturing an outcome | per-feature flags | — | accrual features judged before the base surface is trusted |
| **G9** | Earned calibration | Rulings-55/79 sink built; model_p column; method version stamps; per-cell activation as §6-of-annex gates pass | first activated cell serves interval+n+coverage | collect-only reversion | approves thresholds (NCD-7) | precision theater — the mission's one unforgivable failure |

Cross-cutting: every gate's claims carry evidence classes; every gate
re-verifies its predecessors' [integrity] assertions on the current artifact
(PB-4 §G's own rule, generalized).

## 12 — Document decomposition (proposed; created only after G0)

| # | Artifact (canonical_id) | Purpose / authority | Status & cadence | MUST NEVER contain | Supersedes / indexes |
|---|---|---|---|---|---|
| 1 | `PARIPRASHNA_ARCHITECTURE` (v1.0-RC) | THE normative architecture: MUST/SHOULD/MAY, PPR-IDs, ports (§6.2), contracts by reference. Authority: native ratification; subordinate to the full §21-rule-5 set — CLAUDE.md, PROJECT_ARCHITECTURE, MACRO_PLAN, GOVERNANCE_INTEGRITY_PROTOCOL, CAPABILITY_MANIFEST.json | DRAFT_PENDING_REDTEAM → CURRENT at G0; amended by ADR | struck prose; resolved forks; undated current-state claims; history | supersedes TA §4–§14A as the live control path |
| 2 | `PARIPRASHNA_ASBUILT_BASELINE` | dated census + gap register (FD-table successor), regenerated at every gate; every row evidence-classed | LIVING; per-gate | normative language; aspiration | absorbs TA §16.9 |
| 3 | `PARIPRASHNA_DECISION_REGISTER` | ADR log: D-01.., §1.2 events, OT dispositions, NCD rulings; append-only | LIVING | design elaboration | absorbs TA §1/§1.1/§1.2/§2 |
| 4 | `PARIPRASHNA_VERIFICATION_MATRIX` | PPR → test → proof rung → gate → evidence link | LIVING; per-gate | prose rationale | new |
| 5 | `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` | frozen forensic/history record (the corrections corpus, §16, §18, §20) | flip to `SUPERSEDED` (the enumerated status vocabulary; the by-decomposition mechanism stated in the banner body, not invented as a status string) at G0 close; **no rename until the inbound-reference inventory runs** (≥6 known referrers incl. PB briefs, design plan, CURRENT_STATE banners) | new normative content | — |

The design-engineering plan (v0.3) keeps its own authority for the design
system and is re-pointed, not absorbed. Registration: artifact 1 enters
CAPABILITY_MANIFEST + registry at ratification (finding #13); 2–4 are
governed non-canonical; briefs stay under `briefs/`.

## 13 — Native decision packet — **RULED 2026-08-18**

> **All eight decisions were ruled by the native on 2026-08-18** (Cowork
> conversation, PARIPRASHNA-V012-PHASE1, interactive decision packet). Every
> ruling adopted the package recommendation. Recorded here per §21-rule-1
> discipline; these rulings migrate to the PARIPRASHNA_DECISION_REGISTER
> (artifact 3) when the decomposition executes. Ruling the NCDs discharges
> the DECISION component of Gate 0; the remaining G0 mechanics (red-team
> pass on this package per B.5/GIP §L.7, artifact creation R-3..R-6,
> registration, SESSION_LOG close) are still to run before artifact 1 can
> carry status CURRENT.

| # | Decision | Options | Recommendation | **Native ruling (2026-08-18)** |
|---|---|---|---|---|
| NCD-1 | **Gate order: fidelity before default flip?** (delays cutover; protects AC-15's validity) | (a) G2–G3 before G5 as proposed · (b) keep v0.11 order (flip first) · (c) hybrid: flip after G2 only | (a) | **(a) RULED — fidelity first.** G2–G3 complete before the default flip; v0.11 §19.5's wave order is superseded by the G0–G9 sequence. |
| NCD-2 | **Adopt the five-artifact decomposition?** (retires amend-in-place for this workstream) | (a) yes at G0 · (b) keep the monolith · (c) split normative only | (a) | **(a) RULED — adopt, at Gate 0.** TA v0_1 flips to SUPERSEDED-BY-DECOMPOSITION at G0 close; no rename before the inbound-reference inventory (R-5). |
| NCD-3 | **Ratify the Acharya Reading Contract** (incl. B.4 significance trigger, confidence enum) | ratify / amend / reject | ratify | **RATIFIED** — AcharyaReadingReceipt v1, the §2 significance trigger, the typed-confidence enum, and the earned-calibrated-language rule are adopted; Gate-3 deliverable and AC-15 rubric anchor. |
| NCD-4 | **HS-3 on your own chart:** health-crisis/mental-health readings — self-acknowledged interstitial, or full seal-pending-signoff ceremony? | interstitial / full seal / none (native-only exemption) | interstitial | **INTERSTITIAL RULED** — self-acknowledged pause for the native's own chart; cohort subjects always receive the full seal-pending path. HS-1/HS-2 hard stops remain absolute for everyone. |
| NCD-5 | **RLS adoption** beneath app-level entitlement | (a) yes, C1+C3 tables at G1 · (b) roles only | (a) | **(a) RULED — roles + RLS at Gate 1** on C1 (sacred-personal) and C3 (predictive) tables. |
| NCD-6 | **Provider allowlist for cohort-subject data** (may constrain model choice for non-native charts) | strict allowlist / document-only | strict once a cohort subject exists; document-only until | **RULED — document now, strict later:** the per-provider posture doc is a Gate-1 deliverable; the strict allowlist activates automatically upon the first consented cohort subject. |
| NCD-7 | **Calibration activation thresholds** (annex §6: ±0.15 interval, 60% coverage) + model_p timing (G9 vs G2) | ratify defaults / set your own | ratify; model_p at G9 with the sink | **RATIFIED — defaults pre-registered** (±0.15 Brier-interval half-width on effective n; ≥60% resolution coverage); `model_p` lands at Gate 9 with the Rulings-55/79 sink migration (one schema change). |
| NCD-8 | **Spend ceilings** (per-turn and per-day, both doors) | set numbers | e.g. $2/turn · $40/day as starting caps — yours to set | **RULED — $2/turn · $40/day** as starting caps, enforced before dispatch on both doors (Gate 1); revisited once cost telemetry is live (Gate 2). |

**Post-red-team additions (2026-08-18 panel; ruled by the native the same day):**

| # | Decision | Options | Recommendation | Status |
|---|---|---|---|---|
| NCD-9 | **Adopt the consent schema** (`chart_subject_consent`, safety annex §4) at Gate 1. Scope-Boundary rationale: PPR-06 requires it BEFORE the second subject; a non-native chart already runs L1→L5 today, so this is present-phase protection, not M7 pre-building. | adopt at G1 / defer to first cohort intake | adopt at G1 | **RULED — adopt at G1** · 2026-08-18 |
| NCD-10 | **Formalization route for NCD-4:** the native-self interstitial relaxes §3.5.C's letter for one class; MP meta-governance (§3.10.B) requires deviations from MP to travel spec → red-team → approval → version event. Route NCD-4 through §3.10.B at G0 close, or record it as a native directive (ND-class) binding without an MP bump? | §3.10.B amendment / ND directive | ND directive now, folded into the next natural MP revision (§3.10.A(d)) — proportionate to a native-self-only relaxation | **RULED — ND directive** · 2026-08-18 (logging bound to G0 close) |
| NCD-11 | **`calibration_method_version` on the Ruling-79 sink** — a proposed amendment to a schema DVA Ruling 79 fixed exactly (red-team finding C-F2; calibration annex §8 discloses it). Amend at build time, or build the sink verbatim and migrate later? | amend at build / verbatim + later migration | amend at build (one schema change; rule it at the G9 native point with NCD-7's model_p) | **RULED — amend at build time** · 2026-08-18 |

## 14 — Docs-only patch plan (for a LATER authorized phase; nothing executed now)

Exact steps, each its own commit, may_touch strictly as listed:

- **R-1** `may_touch: 00_ARCHITECTURE/briefs/pariprashna_v012/**` — (this
  package; landed as PROPOSAL by this session-pair; registry disposition per
  GIP §I.3.6(c): "no registry update required — non-canonical PROPOSAL briefs
  under briefs/, outside validator globs; registration occurs at G0 if
  ratified").
- **R-2** `may_touch: 00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md` —
  register the v012 workstream. **BLOCKED until the file's current dirty
  state (MM) is resolved by its owner; never edit a dirty file.**
- **R-3** at G0, create artifact 1 (`00_ARCHITECTURE/PARIPRASHNA_ARCHITECTURE_v1_0.md`)
  populated from this package + TA normative content; MUST/SHOULD/MAY; PPR IDs.
- **R-4** at G0, create artifacts 2–4 under `00_ARCHITECTURE/` (baseline may
  live under briefs/pariprashna_v012/ if the native prefers a lighter root).
- **R-5** TA v0_1: prepend SUPERSEDED-BY-DECOMPOSITION banner + status flip;
  §20 changelog row; **no rename**; run the inbound-reference inventory first
  and re-point: design plan §relates_to, PB briefs' design_authority lines
  (historical — annotate, don't rewrite), CURRENT_STATE banner at next close.
- **R-6** CAPABILITY_MANIFEST + FILE_REGISTRY/GOVERNANCE_STACK rows for
  artifact 1; validator + drift-detector run; SESSION_LOG + COWORK_LEDGER
  close entries (the obligations deferred from this Phase-1 session).
- **R-7** small in-place TA hygiene (only if the native prefers patching the
  frozen doc before G0): §10.4/§10.5/§15 OpenRouter/Tier-C REJECTED-FOR-TARGET
  tags; §6.2/§11.6 "session pin"→"provenance stamp"; §13.4 open-check closure
  note citing MP §3.5.B.

## 15 — Statement of non-change

This session-pair's Phase-1 review changed **no application code, no
migration, no database object or grant, no infrastructure, no deployment, no
feature flag, no credential, no production data, no CURRENT_STATE, no
campaign ledger, and no canonical file.** The only writes are the five
PROPOSAL artifacts under `00_ARCHITECTURE/briefs/pariprashna_v012/` (a new,
additive, non-canonical directory permitted by ROOT_FILE_POLICY §3) and the
session-scratch `_cowork_tmp/` staging archives (user-deletable). The TA
v0.11 amendment was a prior, separately-commissioned deliverable of this
conversation and is inventoried in §2's dirty-file ledger; this review treats
it as content under review, not authority.

---

## Quality-bar self-check (the package fails unless a fresh agent can answer these without inference)

- **What is normative?** → §12 artifact 1 once created (until then, the authority chain TODAY is: CLAUDE.md/PA/MP/GIP/manifest govern; TA v0.11 is the standing Paripraśna design of record; this package is PROPOSAL with its §13 rulings binding as native decisions).
- **What exists today?** → §2 ledger + TA §16.9 (evidence-classed, dated).
- **What is unverified?** → §2's UNVERIFIED rows (PITR, roles, live flag/env, current revision).
- **The reading contract?** → §7 annex (receipt schema, B.4 trigger, confidence types).
- **Hard-stop safety rules?** → HS-1..4 (annex §2), enforced at three points, recorded on every receipt.
- **Guarantees per door?** → §6.2 MAY/MUST-NOT-differ split; §6.6 raw-MCP is the retrieval plane, no reading guarantee.
- **What makes a settled reading reproducible?** → TurnProvenance v2 + envelope snapshots + receipt hash (§7.3).
- **How is outcome leakage prevented?** → TB-3 + C3 data class + arms 1–4 + temporal cutoff (annex §7).
- **What must be true before default cutover?** → Gates 1–4, each with live evidence + rollback (§11).
- **How is each claim tested?** → proof ladder + verification matrix (annex §4; artifact 4).
- **Which decisions still need the native?** → **None — the NCD series is fully ruled (NCD-1..11, 2026-08-18).** What remains is mechanics: the G0-close session (registration, status flips, the NCD-10 directive logging, SESSION_LOG close) and then Gate-1 execution.

*End PARIPRASHNA_V012_PHASE1_REVIEW v0.1 — Phase-1 read-only. Nothing herein
is executable until the native rules.*
