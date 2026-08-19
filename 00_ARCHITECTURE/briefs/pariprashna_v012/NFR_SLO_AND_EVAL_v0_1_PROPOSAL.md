---
artifact: NFR_SLO_AND_EVAL_v0_1_PROPOSAL
canonical_id: PARIPRASHNA_NFR_SLO_EVAL
version: 0.1
status: PROPOSAL — Phase-1 output, awaiting native ratification (not canonical; authorizes no code)
produced_during: PARIPRASHNA-V012-PHASE1 (Cowork, Fable 5, 2026-08-18)
date: 2026-08-18
authoritative_side: claude
relates_to:
  - PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md §17 (v0.11) — the replay harness this file keeps and extends
  - CLAUDE.md §J (the quality standard the eval corpus operationalizes)
  - F-25o (dead cost/latency schema — wire it, don't design a new one)
changelog:
  - "0.1 (2026-08-18): initial proposal."
---

# Non-Functional Requirements, SLOs, and the Evaluation System

## §1 — Evidence classes (binding vocabulary for every claim in this package)

| Class | Means | Example |
|---|---|---|
| STATIC_VERIFIED | read from code OR a governing document, at a named revision/date | flag default false at HEAD dfbdfe620; MP §3.5.C read 2026-08-18 |
| LIVE_VERIFIED | observed against the running production system, dated | MCP census 125 tools, 2026-08-18 |
| DOCUMENT_ASSERTED | stated by a governed report, not independently re-observed | C4 criteria (PURNATA_CLOSE §9) |
| UNVERIFIED | no current evidence either way | PITR state TODAY |
| SUPERSEDED | was true, displaced by later evidence | "88 tools /health" |

**Rule:** a current-state claim without a class and date is invalid in any
v0.12+ artifact. Type checks and fixture renders are never LIVE proof
(they are STATIC and REPLAY proof respectively — see §4).

## §2 — SLO table (proposed targets; error budgets set after baseline)

Honesty note: F-25o stands — cost/latency are UNVERIFIED (no measured
baseline; the metrics schema exists with 0 rows). Targets below are
PROVISIONAL-UNTIL-BASELINED; Gate 2's first deliverable is wiring the
existing dead schema and measuring for two weeks before budgets bind.

| NFR | Target (provisional) | Measured by |
|---|---|---|
| Availability (serving routes) | 99.5% monthly | uptime checks + smoke cadence |
| TTFT (POST → first block.delta) | p50 < 4s, p90 < 12s interpretive; p50 < 2s factual | RUM + trace aggregate |
| First signal (POST → turn.open) | < 300ms | already achievable (stream-first); assert in CI + RUM |
| Turn latency by class | factual p95 < 20s · interpretive p95 < 90s · deep_dive p95 < 240s | trace aggregate |
| Tool iterations / timeouts | ≤8 std, ≤16 deep_dive (current); per-tool timeout budgeted by arbitration | existing route config, asserted |
| Reconnect/replay success | ≥99% of drops within buffer TTL recover with zero content loss | transport metrics + replay fixtures |
| Durable persistence success | 100% of settled turns durably persisted OR visibly marked incomplete — no silent divergence | outbox/write-ahead metrics (Gate 2) |
| Cost | per-turn ceiling (native sets, NCD-8); daily ceiling; attribution per (user, channel, model) | wired F-25o schema |
| Concurrency | QoS queue depth + shed behavior stated; interactive class never starved by batch | queue metrics |
| RPO/RTO | ledger + conversations: RPO ≤ 1h (PITR) · RTO ≤ 4h; layer tables: RPO 24h | Cloud SQL config + drill |
| Restore drill | executed once at Gate 1 (a G1 deliverable per the gate plan), then quarterly | drill log |
| Accessibility | axe 0 critical/serious on every state fixture; SR smoke per release | CI + documented smoke |
| Mobile | G-MOBILE battery green at 390×844 incl. keyboard-open streaming | Playwright profiles |
| Audit/evidence retention | receipts + provenance: life of chart + consent terms; traces: 90d (proposal) | retention jobs |
| Deletion completion | verified deletion ≤ 30d from withdrawal (§3.5.D) | deletion workflow log |
| Provider failover | stack fallback stated per class; **no silent epistemic downgrade** — a fallback that changes model tier is disclosed on the turn (flag + provenance) | ModelPlane + turn flags |

## §3 — Model qualification ≠ model health

Health (probe says up) only gates dispatch. **Qualification** gates WORK
CLASSES: a model serves factual / interpretive / predictive / sensitive
classes only after passing that class's eval suite (§4) at a recorded
version. Provider fallback may substitute only an equally-qualified model for
that class; otherwise the turn degrades VISIBLY (disclosed flag, provenance
records the substitution) or queues. This kills the silent-downgrade failure
mode (ED.5/ED.6's "degrades, doesn't block" made explicit and honest).

## §4 — Proof ladder (binding vocabulary)

STATIC PROOF (code/type/lint) → REPLAY PROOF (fixture/harness) →
INTEGRATION PROOF (services together, synthetic traffic) → LIVE PROOF
(deployed production, real data, dated) → NATIVE ACCEPTANCE (AC-15 class).
Every gate in the master review names which rung each criterion requires.
A lower rung never substitutes for a higher one (the PB-2 byte-equality
false-confidence gate is the canonical violation; §N.8 is the doctrine).

## §5 — The Madhav intellectual-quality corpus (the missing eval system)

Keep the renderer replay harness (§17.1) untouched. ADD a reading-quality
corpus — versioned fixtures, run against the DEPLOYED default route
(INTEGRATION/LIVE rungs) and scored against the AcharyaReadingReceipt:

**Query classes (≥5 fixtures each):** factual lookup · interpretive
whole-chart · timing/daśā · cross-domain contradiction · remedial ·
sensitive (health/mortality/mental-health — scored on the SAFETY action,
never on producing the content) · ambiguous→clarification · incomplete/
conflicting evidence (B.12 refusal honesty) · returning conversation +
chart drift · disagreement/correction · prediction capture→outcome ·
portal-vs-prashna_ask parity pairs.

**Scored dimensions → source of truth:** factual correctness (fact_ids vs
chart_facts) · derivation integrity (B.3: every claim's ledger resolves) ·
B.11 coverage (receipt.coverage vs floor) · three-interpretation discipline
(B.4: sets present where triggered; waiver rate) · falsifier quality (native
+ acharya rubric) · contradiction surfacing (planted-contradiction fixtures)
· citation precision/recall (receipt vs prose spans) · calibration-language
honesty (typed confidence never overstated; T-8 scan) · safety compliance
(HS-1..4 fixtures) · reader comprehension (plain-register rubric; layperson
scorer) · register leakage (lint corpus, 100% catch on seeded ids) ·
model/provider consistency (same fixture across qualified models; divergence
report) · **acharya reviewer judgment** (§J: "my level / above my level /
reveals things I'd have missed"). Note: engaging an EXTERNAL human acharya is
M10-gated (MP §3.7 pool policy) — until then this dimension runs as the
native's own §J judgment plus a Jyotish-competent model panel, honestly
labeled as such, and is ASPIRATIONAL for external review.

**AC-15, made a rubric without losing its soul:** the native's week-of-use
verdict remains binary and non-automatable (ruling W-4 stands). The rubric
beneath it: a daily 60-second card — felt friction (y/n + where), trust
moment (y/n + which), register break (y/n), one free line. Seven cards +
the unprompted-symptom-list-empty check = the gate evidence. The verdict
stays the native's; the rubric merely preserves WHY for the record.

## §6 — Parity contract (portal ↔ prashna_ask)

The semantic result of the same question, same chart, same build MUST be
equivalent across doors at the receipt level: same coverage mode, same floor
set, same evidence grades, same safety decision, same confidence types —
prose may differ in rendering, receipts may not differ in substance.
Contract test: fixture questions run through both doors; receipts diffed on
a normalized projection (hash of the semantic fields). This is Gate 4's
instrument, and it is exactly the test that today FAILS by construction
(prashna_ask lacks the gates) — which is why Gate 4 exists.

*End NFR_SLO_AND_EVAL v0.1 PROPOSAL.*
