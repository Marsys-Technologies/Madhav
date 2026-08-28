---
artifact: S4_LATENCY_WATERFALL
version: "1.0"
status: CURRENT — first-class S4 deliverable, required input to campaign stream S6
  (Performance, Resilience & Observability) per STREAM_CHARTER_S4_v1_0.md and
  test plan v2.1 §4.3 item 4.
date: 2026-08-28
stream_id: S4
produced_by: Paripraśna assurance stream S4 (Pipeline Correctness & Door Parity)
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md §4.2, §4.3.4
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md (E-006 lineage, E-003 lineage)
  - .s4_scratch/S4_synergy_latency_waterfall_report.md (full investigation report, method detail, raw evidence)
changelog:
  - "1.0 (2026-08-28): initial publish. LIVE-rung end-to-end MCP-door turn against
    synthetic chart 1c826d5a, corroborated by direct stage-chain instrumentation
    for S1/S2/S4/S6 and static code-path proof for S3/S7/S9/S10/S11-core.
    Independently reproduces and sharpens EDIR E-006 and E-003."
---

# S4 Latency Waterfall — per-stage accounting for a real Paripraśna turn

**Test subject:** synthetic chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (the native's real
chart `482012f1` was never touched). **Door:** MCP (`prashna_ask`/`prashna_status`).
**Rung:** LIVE (primary — real end-to-end deployed-pipeline turn, not a fixture) +
direct stage-chain instrumentation and static code-path proof (secondary, used only to
decompose the LIVE run's internal buckets).

## 1 — Headline: what production can prove about itself today, unaided

| Stage | Duration (ms) | % of total wall-clock |
|---|---:|---:|
| S6 — ToolBroker dispatch (11 tools, native per-tool timer) | 705 | 0.69% |
| **UNATTRIBUTED** (no native per-stage timer exists for S1–S5, S7–S11) | **101,697** | **99.31%** |
| **TOTAL (wall-clock)** | **102,402** | **100.00%** |

This is read straight from the completed job's own `completeness.tools_dispatched[].latency_ms`
against its own `elapsed_ms` — zero added instrumentation. **This is the number the system can
currently account for about itself, and it is 0.69%.**

This corroborates and sharpens the live seed baseline (EDIR E-006, 2026-08-23: 81.3s turn, ≈4.0s
tool dispatch ≈4.9%, >95% unattributed). This run: 102.4s turn, 0.705s dispatch ≈0.69% —
**same shape, worse ratio**, reproduced on a second, fully independent live turn. The
>95%-unattributed finding is not a one-off; it is this pipeline's structural latency default.

## 2 — Best-effort full 11-stage decomposition

Native telemetry stops at the two rows above. Each remaining stage below was independently
attributed by the strongest evidence class actually available — nothing here is guessed.

| # | Stage | Duration (ms) | % of total | Evidence class |
|---|---|---:|---:|---|
| S1 | NormalizedQuery → intent/scope classify | 0.006 | 0.00% | MEASURED-DIRECT (real function, 20 samples, median) |
| S2 | EntitlementDecision | ~101 | 0.10% | MEASURED-DIRECT (real SQL, 5×, real DB via Cloud SQL proxy; likely upper bound vs. a warm production pool) |
| S3 | SafetyPolicyDecision | 0 | 0.00% | STATIC-PROVEN — `PARIPRASHNA_SAFETY_GATE_ENABLED` defaults OFF; confirmed no safety-decision flag in this job's `judgment_flags` |
| S4 | ScopeTuple / ClarificationRequest | (folded into S1) | 0.00% | MEASURED-DIRECT — same call as S1, no separate invocation |
| S5 | AcharyaPlan (planner) | ~7,920 this run (upper-bound, inferred); **3,925 ms avg independently measured elsewhere in this stream via 14 real `query_trace_steps` rows — treat that as the authoritative typical value** | ~7.7% this run | INFERRED-BOUNDED, corroborated by an independent direct measurement in a sibling S4 investigation |
| S6 | ToolBroker → dispatch (11 tools) | 705 | 0.69% | MEASURED-LIVE (native telemetry) |
| S7 | EvidenceBundle assembly | ~0 | ~0.00% | STATIC-PROVEN near-zero (one `await`, cache-miss-only path; otherwise in-memory transform) |
| S8 | Interpretation & Adjudication (synthesis) | ~93,600 (dominant remainder) | ~91.4% | INFERRED-DOMINANT-REMAINDER — **no native S8 start/end timer exists on either door** to confirm directly; consistent with `judgment_flags.synthesis_evidence_truncated` on this run |
| S9 | Grounding/Safety Validation | ~0 | ~0.00% | STATIC-PROVEN near-zero (zero `await` calls, pure sync checks) |
| S10 | SemanticReadingParts | ~0 (interleaved into S8, not additive) | ~0.00% | STATIC-PROVEN near-zero + structural: block assembly runs incrementally as S8 streams, not as a separate serial pass |
| S11 | TurnProvenance + Receipt | folded into S8 remainder | — | PARTIAL — receipt assembly itself is negligible, but `persistence_stage.ts` makes 7+ sequential real DB writes/reads that were **not independently timed** — the one honest unmeasured gap in this decomposition |
| | **TOTAL** | **102,402** | **100%** | |

## 3 — The core finding: the pipeline cannot currently measure its own dominant cost

**No native per-stage latency telemetry exists between S1 and S11 on either door.** The wire/job
protocol tracks only coarse buckets — the Portal door's `em.phase()` emits 4 named phases (`plan`
covering S1–S5, `retrieve` covering S6–S7, `synthesize` covering S8, `finalize` covering S9–S11),
and even that 4-bucket signal is **Portal-only** — it was not observable through the MCP door used
for this LIVE run at all (`completeness`/`persistence`/`judgment_flags` carry only per-tool
`latency_ms`, no phase timings). **The single largest cost in the turn — S8 synthesis, ~91% of
wall time by this accounting — has zero direct instrumentation on either door.**

A live DB read during this investigation found the scaffolding for exactly this timer already
half-built and abandoned: the Portal/WEB door's `query_trace_steps` table inserts a
`step_name='synthesis'` row with a real `started_at` the instant tool-dispatch completes, but
`completed_at`/`latency_ms` are **never populated** — every one of 16 observed rows for this step
name is permanently stuck `status='running'`. This was independently reproduced by two separate
S4 investigation lanes (the S8-stage agent and this waterfall agent) working different evidence
paths. Separately, the **MCP door writes zero rows to `query_trace_steps` at all** — confirmed for
this report's exact live time window — consistent with the job's own `persistence.status:"none"`
field and the already-tracked P2-B-004/E-119 finding (MCP has no durable turn-persistence path).

**Proposed fix class** (filed to EDIR_V3, not executed by this report): add stage-boundary spans
at each of the 11 architectural seams (today's `plan`/`finalize` buckets each silently collapse
4/3 stages into one); complete the already-half-built `query_trace_steps` synthesis-completion
write on the Portal door; surface the same span data through the MCP door's job-result envelope so
`prashna_status` final results carry a real waterfall, not only per-tool dispatch numbers.

## 4 — Bonus corroboration surfaced by the same live run

The `prashna_status` progress message froze byte-identical for 43 of the run's 102 seconds
(elapsed_ms 8,726 → 51,613) while the job's `elapsed_ms` field itself kept advancing correctly —
independently reproducing EDIR E-003's shape on a fresh live turn, worse than the original seed
(this stream's dedicated progress-truthfulness synergy test reproduced this defect directly and in
more depth; see that report and its EDIR_V3 filing for the primary finding).

## 5 — Rung honesty statement

- The **§1 headline table is 100% LIVE**, zero inference.
- In §2: S1/S2/S4/S6 are directly measured (LIVE or DIRECT); S3/S7/S9/S10/S11-core are proven
  negligible by exhaustive static read of every `await`/I/O call site, not timed (timing a
  proven-zero-I/O pure function adds no information); **S5 and S8 are the two figures this
  investigation could not independently measure on this specific run** — they are
  bounded/remainder inferences and are exactly what §3's finding explains: no instrumentation
  exists to measure them directly on either door today.
- Persistence writes inside S11 are a known, real, unmeasured gap folded into the S8 estimate,
  called out rather than silently absorbed.

## 6 — For S6 (Performance, Resilience & Observability)

This artifact is your NFR-baseline input per test plan §4.3.4 / §9. Headline numbers to carry
forward: **102.4s wall-clock, 0.69% natively accounted for, >99% unattributed** (second
independent live corroboration of the E-006 shape: >95% unattributed is the structural default,
not an anomaly). The S5 typical-value figure to use for planning-cost baselining is the
directly-measured **3,925 ms avg** (14 real trace rows), not this run's 7,920ms upper-bound
inference. Full raw evidence, polling logs, and measurement scripts:
`.s4_scratch/S4_synergy_latency_waterfall_report.md` (this worktree, not yet committed — ask S4's
stream lead for the branch/PR pointer if this file has since been committed and this note is
stale).

*End S4_LATENCY_WATERFALL v1.0.*
