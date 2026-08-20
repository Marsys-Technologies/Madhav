---
artifact: PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0
canonical_id: PARIPRASHNA_IMPLEMENTATION_ROADMAP
version: 1.0
status: PROPOSAL — the lane-level execution decomposition of gates G1–G9; authorizes no code
produced_during: PARIPRASHNA-V012-PHASE1 follow-on (Cowork, Fable 5, 2026-08-19)
date: 2026-08-19
authoritative_side: claude
role: >
  The gate plan (PARIPRASHNA_ARCHITECTURE §7 / v0.12 review §11) says what each gate
  PROVES. The Verification Matrix says how each requirement is TESTED. This document
  says what WORK produces them — lanes, dependencies, dispatch order, and per-lane
  acceptance. It is the campaign plan for building the ratified architecture, in the
  PB-campaign idiom (master plan → wave briefs → lane briefs → BIND → gate).
relates_to:
  - 00_ARCHITECTURE/PARIPRASHNA_ARCHITECTURE_v1_0.md (the requirements this builds — PPR IDs)
  - 00_ARCHITECTURE/PARIPRASHNA_ASBUILT_BASELINE_v1_0.md (the GAP rows this closes)
  - 00_ARCHITECTURE/PARIPRASHNA_VERIFICATION_MATRIX_v1_0.md (the tests each lane must pass)
  - 00_ARCHITECTURE/briefs/pariprashna_build/BRIEF_PB-4.md (executes G5 and G7; lanes reused)
changelog:
  - "1.0 (2026-08-19): initial roadmap, authored after G0 close entered execution."
---

# Paripraśna — Implementation Roadmap (G1 → G9)

**Where this starts.** G0 (ratification + decomposition + registration) is in
execution. Every architecture decision is ruled (NCD-1..11). The surface is
built and live behind a flag. What follows is the work that turns the ratified
architecture into the running instrument.

**Sizing convention.** S = one focused lane · M = a lane with real design or
schema work · L = a lane that needs its own brief and probably sub-lanes. No
calendar estimates: this project is phase-indexed, not time-indexed
(MACRO_PLAN §3.8.A).

**Lane count (added 2026-08-20, item 3, PARIPRASHNA-CLOSEOUT session).** This
document and the kickoff prompt both cite the original ~30-lane estimate below.
Lane decomposition expanded to **53 lanes** during P0, as tracked live in
`00_ARCHITECTURE/briefs/pariprashna_swarm/tracker/PLAN.yaml`
(P0(6)+P1(10)+P2(15)+P3(6)+P4(11)+P5(5)) — not a renumbering of this document,
a finer decomposition of the same gates as P0 execution surfaced real sub-lane
boundaries the estimate hadn't. Renumbering nothing here. Division of
authority going forward: **`PLAN.yaml` is normative for lane count, identity,
and dependency edges** (it is what the observatory derives live state
against); **this roadmap is normative for intent and PPR mapping** (what each
gate proves and which requirement each lane closes). Read both; they answer
different questions.

**Reading the dependency column.** "blocks" = do not start the named lane
until this one lands. Lanes with no blocker in the same gate are
parallel-dispatchable.

---

## GATE 1 — WALLS & FLOORS

*Why first: every §14A gap was tolerable while Paripraśna was a flagged
parallel surface with one user. G5 makes it the default and mission item 6
adds subjects — both re-price these risks (T-11). Nothing downstream is safe
to expose until this gate closes.*

| Lane | Work | Size | Deps |
|---|---|---|---|
| **G1-A SafetyPolicyGate** | New port between entitlement and planning. Deterministic-first query classifier (keyword/domain/capability-class; LLM assist may only RAISE severity). HS-1 date-of-death block at all three points (plan-time capability exclusion · synthesis-time prompt policy · pre-wire phrasing scan). HS-2 suicide-adjacent: fixed calm response, NO plan built, audit row, cohort-native notification. HS-3 health-crisis/mental-health three-step path (seal-pending → two independent adversarial passes → separate sign-off) with the NCD-4 interstitial for native_self. HS-4 mortality-window aggregate framing + full HS-3 path. HS-5 retraction record. HS-6 predictive-output sampling into the §IS.8 cadence. `safety_decision` written on every turn. Sensitive-class capabilities excluded from the `consult` MCP profile. | **L** | — |
| **G1-B Consent & subjects** (NCD-9) | Migration: `chart_subject_consent` (subject_kind native_self\|cohort\|test · consent_document_ref · granted/withdrawn · anonymization_choice DEFAULT anonymous · redaction_requests · vulnerable_exclusion_flag · verified_deletion_at). Strict `native_self` definition enforced at entitlement resolution. Minor (<18) exclusion computed from the chart's own birth_date. Excluded-subject register. Withdrawal → verified-deletion workflow incl. subject-scoped snapshot deletion with tombstone hashes. Deletion-scope dispute → DISAGREEMENT_REGISTER hook. Subject export as JSON manifest. | **L** | — |
| **G1-C Roles, RLS, arm-1/arm-3** (NCD-5) | The five roles (`role_web_serve` · `role_orchestrator` · `role_ledger_write` · `role_jobs` · `role_sidecar`) with grant walls. Web app migrated off `amjis_app` for read paths; `amjis_app` rotated after cutover (pairs with the CCD-004 rotation already owed). Chart-scoped RLS on C1 + C3 tables keyed to a session-set `app.chart_context`. Out-of-process ledger writer (arm-3) holding the only write role. INSERT-only (or hash-chained) grants for safety/retraction/consent audit rows. | **L** | — |
| **G1-D Limits** (NCD-8) | Create `src/middleware.ts` (does not exist). Per-user rate limits reusing `lib/mcp/rate_limiter.ts`, never a second implementation. **Pre-dispatch** spend ceilings: $2/turn, $40/day, both doors, exceeding = designed failure state not a 500. Cost attribution per (user, channel, model) wired to the existing schema. | **M** | — |
| **G1-E Durability** | Verify Cloud SQL PITR (last known: disabled); enable if off. **Execute one restore drill** against a scratch instance. Write RPO/RTO + DR runbook (ledger+conversations ≤1h/4h; layer tables 24h). Scheduled independent logical export of the two irreplaceable table sets. | **M** | — |
| **G1-F Model-plane hygiene** | Provider posture doc (NCD-6: per-provider retention/training/region, allowlist armed for first cohort subject). `ANTHROPIC_API_KEY` provisioned or the stack delisted from the picker. | **S** | — |
| **G1-G Injection containment** (PPR-13) | Question and retrieved content structurally delimited as data; plan Zod-closed against the injection path; tool-sequence anomaly trace flag; answer-side entitlement scan (chart_ids/facts not belonging to the caller) folded into the existing pre-wire lint pass. | **M** | G1-A (shares the pre-wire scan) |
| **G1-H PB-9-DETECTOR** | The no-auto-promotion CI detector — proves no code path promotes a prediction to `confirmed`/`open` without human action (currently true by inspection only). | **S** | — |

**Gate evidence (all LIVE rung):** psql role/grant matrix + write-denial probe · RLS cross-context denial · every HS fixture observed blocking on the deployed route, demonstrated-can-fail · caps observed blocking · consent-absent chart refusing interpretive serving · executed restore-drill log · arm-4 canary green.
**Rollback:** grants revertible; the safety gate behind its own flag; caps configurable.
**Native point:** approve the HS-3 interstitial UX in the flesh.

---

## GATE 2 — TRUTH OF THE SURFACE

*Why before the flip (NCD-1): AC-15 measured against a paragraph-only wire
with post-hoc citations and cosmetic controls judges a product that won't
exist a month later.*

| Lane | Work | Size | Deps |
|---|---|---|---|
| **G2-A Semantic blocks** (PPR-07, FD-1) | Server-side commit-time block classification (the server holds the full block text at commit — deterministic, testable; NOT mid-stream segmentation). Carry `kind` + `role` on `block.commit`; version the protocol event. Client: activate the already-built `TableBlock`/`VerseBlock`/`GapRibbonBlock`/heading/prose-role renderers on the LIVE path. **`prediction_card` becomes a first-class wire event carrying the structured candidate + part id** — which also unlocks FD-4 (mount `LogToSamiksha`, the in-stream confirm affordance built and unmounted since PB-3). | **L** | — |
| **G2-B Citations at first paint** (PPR-08, FD-2/FD-6) | Wire the built S-3 rewriter (`lib/pariprashna/citations/rewriter.ts` — hold-back 64B/400ms, tolerant grammar, hallucination counters) into the route so sentinels become `⟦n⟧` + `citation.define` DURING streaming. Server-derive the grounding summary (counts, grade rollup, completeness line from the floor receipt); keep the client rollup only as the disclosed snapshot-degrade path. | **M** | — |
| **G2-C Honest controls** (PPR-09/16, FD-3/FD-12) | Plumb `model_id` and `length_tier` end-to-end (both already exist in the submit options and route contract) and implement length shaping in synthesis — or remove the pills. Derive `reading_depth` from the scope tuple instead of the composer mode; make depth received visible. | **M** | — |
| **G2-D Durable persistence** (PPR-10, FD-9) | Distinguish `settled_visual` from `durably_persisted` in the reducer and the UI. Outbox/write-ahead with idempotent retryable writes; crash recovery replays the outbox; explicit visible incomplete-turn state. Replace the byte-equality invariant with a **normalized semantic-hash comparator**, repurposing the PR-#927 capture as its feed (closes the Ruling-80 posture question). Version event + message schemas with declared compatibility. | **L** | — |
| **G2-E Observability** (PPR-33, GAP-14) | Wire the EXISTING dead cost/latency schema (`llm_usage_events` et al. — do not design a new one). TTFT, per-event latency, delta→commit lag, reconnect/snapshot rates, gate verdict rates, **register-lint firing rate** (the health signal that the primary defenses work), cost per turn/user/channel, prediction capture + resolution coverage. Then a two-week baseline before SLO budgets bind. | **M** | — |
| **G2-F Mobile + a11y** (PPR-19) | PB-4 Lane F-4 as written: `visualViewport` composer, tap-first citations everywhere, sheets for displacing disclosures, aria-live discipline (one polite region; committed blocks leave it), G-MOBILE battery at 390×844 incl. keyboard-open streaming, axe 0 critical/serious on every state fixture, VoiceOver + NVDA smoke. | **M** | — |
| **G2-G Edge-state lexicon** | PB-4 Lane F-3: every §7.8 edge state as a fixture with its exact lexicon copy; fold or delete the second error classifier (FD-11/F-25b). | **S** | — |
| **G2-H History sidebar + empty state + the Seal** | PB-4 Lanes F-1 + F-2: threads by chart, collapse persistence, streaming dot; the empty-state invocation with the ecliptic hairline; the arrival line placeholder; the Seal choreography in strict order; motion constitution audit. | **M** | — |

**Prerequisite worth naming:** the design-engineering plan (v0.3) has never had
its own grounding pass — it still describes the removed reference rail and
predates the dock. G2's design lanes (F-1/F-2/G2-A typography) should run
against a grounded plan. **Recommend a short design-plan grounding pass as
G2's first act** (S, docs-only).
**Gate evidence:** a real reading on the DEPLOYED route renders a daśā table
as a table, a verse as a verse with its gloss, chips at first paint; crash
kill-test surfaces a visible incomplete state; baseline metrics report exists.

---

## GATE 3 — THE CONTRACT (the epistemic core)

*This is where "beyond acharya-grade" stops being an aspiration and becomes a
per-reading, machine-checkable claim.*

| Lane | Work | Size | Deps |
|---|---|---|---|
| **G3-A Receipt emission** (PPR-01) | Assemble `AcharyaReadingReceipt` v1 per turn: coverage (from the live floor + completeness receipt) · facts_consumed by reference · derivation_chains (thread envelope refs through synthesis) · cross_domain · evidence_grades · honest_gaps · safety_decision (from G1-A) · calibration_disclosure · prose_binding · provenance · receipt_hash. Persist it; expose the audit affordance. **Receipt validator: every field earned by a detector or null (§N.8).** | **L** | G1-A, G2-A |
| **G3-B Three interpretations + falsifier** (PPR-02) | Synthesis-stage structured output producing `interpretation_sets` for every SIGNIFICANT judgment (domain verdict · time-indexed · remedial · prediction-detected · rules-in-tension). Selected reading + rationale + falsifier. Waiver path with a monitored rate. Validator rejects a significant claim with no set. | **L** | G3-A |
| **G3-C Typed confidence** (PPR-03) | The five-type enum on every claim; `empirically_calibrated` forbidden below an activation gate; T-8 precision scan (no quantity served beyond what its sample supports); new engine layers (v4.1 promise, v3 gochara, KP) surface at their earned tier with honest language. | **M** | G3-A |
| **G3-D Voice enforcement** (PPR-04, A-43) | Second-person-imperative detector on remedial-class blocks ("you should wear" flags; "the tradition prescribes" passes). Pacing policy for difficult findings (shorter committed blocks, uncertainty before severity, framed probability leading with the number one affordance away). Same defanged verdicts as the register lint. | **M** | G2-A |
| **G3-E Reader affordances** (PPR-05) | "Read it another way" (the non-selected B.4 candidates in plain register) and "What would change my mind" (the falsifier). Affordances, never inline. | **S** | G3-B |
| **G3-F The quality corpus** (the missing eval system) | Versioned fixtures across 12 query classes (factual · interpretive whole-chart · timing · cross-domain contradiction · remedial · sensitive · ambiguous→clarification · incomplete evidence · returning conversation + drift · disagreement · prediction capture→outcome · door parity). 13 scored dimensions incl. derivation integrity, B.11 coverage, falsifier quality, citation precision/recall, calibration-language honesty, safety compliance, reader comprehension, register leakage. Run against the DEPLOYED route. | **L** | G3-A |
| **G3-G Model qualification** (PPR-32) | Per-work-class eval suites (factual/interpretive/predictive/sensitive); a model serves a class only after passing; fallback substitutes only equally-qualified models or degrades VISIBLY with a flag + provenance record. | **M** | G3-F |

**Gate evidence:** corpus run on the deployed route with receipts audit-clean;
waiver rate within bounds; a planted-contradiction fixture surfaced, not
smoothed; safety fixtures still blocking with receipts recording it.

---

## GATE 4 — ONE ENGINE IN FACT

| Lane | Work | Size | Deps |
|---|---|---|---|
| **G4-A Unified plan type** | Reconcile web `PipelinePlan` onto the MCP `VidhiPlan` shape (~80% exists there): a total `tool_name ↔ primitive_id` namespace map with its CI proof; promote the free-text `llm_extension_note` band to addressable plan items; wire the web route through the vidhi compiler. | **L** | — |
| **G4-B Headless loop + prashna_ask re-base** | Extract the agentic loop as a channel-agnostic, headless-callable service. Re-base `prashna_ask` onto it so the MCP door gets the SAME gates the web door has (register lint, sentinel rewrite, receipt) — closing the §6.4 stage-9 asymmetry. | **L** | G4-A, G3-A |
| **G4-C Store completion** (FD-8) | History/user turns onto the canonical writer; `tool_call`/`tool_result`/`reasoning` parts written; summaries then build from the full record rather than assistant rows only. | **M** | G2-D |
| **G4-D Parity contract** (PPR-30) | Fixture questions through both doors; receipts diffed on a normalized semantic projection; hash equality asserted in CI. | **M** | G4-B |

---

## GATE 5 — CANARY FLIP

PB-4 **Lane F-6** (post-deploy chat smoke in CI: 200 + persisted
`message_parts` row + zero-internal-id grep on every streamed byte,
**demonstrated-can-fail** against a seeded violation) merges first, then
**F-5 steps 1–2**: `/clients/[id]/pariprashna` becomes the default from every
entry point, flag retained as the rollback lever, then **seven consecutive
green post-deploy smoke runs** (ruling W-1 — counter resets on any red, no
override). SLO budgets bind against the G2 baseline. **Size M; rollback = flag
flip (W-3).**

---

## GATE 6 — AC-15 + HOLD

Your week of daily use on the default surface. The rubric preserves the *why*
without touching the verdict: a 60-second daily card (felt friction y/n +
where · trust moment y/n + which · register break y/n · one free line), seven
cards plus the unprompted-symptom-list-empty check. **The verdict stays binary,
yours, and non-automatable (ruling W-4) — never claimed, simulated, or
proxied.** Size: your time, not a lane.

---

## GATE 7 — RETIREMENT

PB-4 **F-5 steps 3–4**: `consult` + `consume` retired (308 route redirects;
410 + pointer for API callers per the B-4 inbound inventory); dead chat trees
deleted per the **refreshed** PG1-C3 census in leaf-first dependency order;
legacy `parts_json` path removed; `PARIPRASHNA_ENABLED` deleted (grep = 0).
Plus the residue sweep: `audience_tier` type/schema vestiges (GAP-17), the
second error classifier (FD-11). Then **Q-2** (three real readings graded
against §J on the default route) and **F-7** docs seal — design plan to
RATIFIED-AS-BUILT, Baseline regenerated, registers updated. **Size L (F-5 is
the irreversible lane — verifier reviews the deletion diff line-by-line
against the warrant, W-2); rollback after deflag = git revert + rollback pin.**

---

## GATE 8 — THE REMEMBERING

| Lane | Work | Size | Deps |
|---|---|---|---|
| **G8-A Recall wired** (PPR-18, A-41, FD-5) | Give the built pgvector recall its caller: per-chart cross-thread recall surfacing prior conclusions as `prior_reading`-graded citations (already structurally barred from satisfying floors). **Independent-then-compare** — the current reading composes BEFORE prior conclusions are retrieved (anti-anchoring, anti-sycophancy). Contradiction surfacing made adjudicable by the D-16 stamps both readings carry. Dedup + decay ranking. | **L** | G3-A |
| **G8-B The arrival line** | One quiet chrome line on thread open: current daśā year + open prediction windows, derived from L1/Kāla truth, **never model-composed** (wire-tap proves retrieved values). | **S** | — |
| **G8-C The window-opening ask** (A-42) | Pre-plan ledger check for `window_closed` rows whose domain overlaps the question → one sentence ("Before I answer: in March I indicated X for April–June. What happened?") with the one-tap outcome affordance attached, then the answer in the same turn regardless of reply. **The single highest-leverage unbuilt feature — it converts outcome-recording decay into the loop's most natural moment.** | **M** | G2-A (wire event), G1-B |
| **G8-D Dispute capture** (PPR-31, A-48) | The affordance on any turn; first-class rows keyed to `(message_part, claim_span)` carrying the D-16 stamp; reviewed in Samīkṣā. **Re-retrieve, never re-word; never fold when the data supports the claim.** Restore or replace the feedback endpoint that still discards every rating. | **M** | — |
| **G8-E Digest + journal** (FD-10) | Real transport for the window-close digest (currently log-only stub); the digest journal off the filesystem into the DB; the −14d `closing_soon` notice live. | **S** | — |
| **G8-F Signal reader text** (A-44) | `signal_reader_text` as a NEW column (never overwrite the deterministic embedding columns). Generate-review-**freeze** (never at serve time). Prioritized by observed citation frequency — now a SQL query against real persisted citations, not a guess. Top ~50 first; fallback stays classical source + grade, never the internal text. **Parallelizable editorial work — can start any time after G3-A gives real citation data.** | **L** | G3-A (for prioritization data) |
| **G8-G Narration audit** (GAP-18) | The post-six-views narration audit against the now-settled Kāla layer, by the arc's proven method (defect-class census + adversarial refuter panel + live-proof acceptance). The #2 PŪRṆATĀ handoff item. | **L** | — |

---

## GATE 9 — EARNED CALIBRATION

| Lane | Work | Size | Deps |
|---|---|---|---|
| **G9-A The sink** | Build `mimamsa_conversational_calibration` EXACTLY per DVA Rulings 55/79, **plus `calibration_method_version`** (NCD-11, native-approved amendment). Collect-only; leak-guarded. | **M** | — |
| **G9-B `model_p`** (NCD-7) | Immutable model-stated probability captured at detection, never conflated with the operator band; immutability triggers proven by rejected-UPDATE tests. | **S** | G9-A |
| **G9-C Scoring** | Full outcome taxonomy incl. censoring; proper scoring by type; coverage-stamped scores (interval + n + coverage on every figure); hierarchical partial pooling; reliability diagrams; temporal knowledge cutoffs; held-out/prospective partitions kept separate. | **L** | G9-A |
| **G9-D Per-cell activation** | The ruled gate (±0.15 interval half-width on effective n; ≥60% coverage) computed per cell; below gate serves the honest flag; above gate serves the interval — **and the first activated cell is the moment L5 leaves STRUCTURAL mode for that cell only.** | **M** | G9-C |

---

## Dispatch shape

**Serial spine:** G1 → G2 → G3 → G5 → G6 → G7. These gate each other for real
reasons (exposure, then fidelity, then the contract AC-15 judges, then the
flip, then the verdict, then the irreversible retirement).

**Parallel-capable:** G4 alongside G2/G3 where lanes don't collide (G4-A and
G4-C touch different files than the render lanes). G8-F (editorial reader
text) and G8-G (narration audit) are ideal idle-capacity work and can start
as soon as G3-A produces real citation data. G1's eight lanes are largely
mutually independent — that gate parallelizes best.

**Hard orderings not to break:** arm-1 roles before any second subject gets an
entitlement (D-09's moment) · G1 before G5 (T-11) · G2-A before G3-A's
prose_binding and before G8-C's wire event · the receipt (G3-A) before parity
(G4-D) can mean anything · seven green smokes before the retirement commit
(W-1) · AC-15 verdict before deleting the fallback (G6 before G7).

## Immediate next actions

1. **Finish G0** (in execution): registration, status flips, the NCD-10
   directive, SESSION_LOG close, PR.
2. **Author the Gate-1 campaign brief** — master brief + eight lane briefs +
   BIND, in the PB idiom. This is the biggest single authoring task left and
   the one that unblocks all execution.
3. **Ground the design plan** (short docs pass) before G2's design lanes.
4. **Regenerate the As-Built Baseline** at each gate close; the UNVERIFIED
   rows (PITR, roles, live flag env, serving revision) are G1's first probes.

*End PARIPRASHNA_IMPLEMENTATION_ROADMAP v1.0.*
