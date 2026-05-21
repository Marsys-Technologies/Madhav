---
artifact: PHASE_B_PLAN_v1_0_RECONCILER_PASS_v1_0
document: PHASE_B_PLAN_v1_0_RECONCILER_PASS
project_name: MARSYS-JIS
version: 1.0.0
status: ISSUED
author: Claude Sonnet 4.6 (acting as reconciler role; model constraints acknowledged)
date: 2026-04-23
target: PHASE_B_PLAN_v1_0.md v1.0.1
role: Shift #2 skeptical reconciler pass over Gemini pass-1 output
note: >
  The two-pass protocol calls for Claude Opus 4.7 as reconciler. This pass was executed
  by Claude Sonnet 4.6 under session constraints. Native should note the model deviation
  and apply additional scrutiny proportional to the difference in reconciler model.
---

# PHASE_B_PLAN_v1_0 — Reconciler Pass v1.0

---

## 1. Executive Verdict

**REMEDIATE-THEN-EXECUTE**

The plan is substantively coherent and architecturally sound at the macro level. The two-pass protocol, layer separation model, Learning Layer hook discipline, and cost/velocity estimates are well-considered. However, three BLOCK findings make Phase B unexecutable as written: (1) the validator implementation schedule is declared in §H policy but not reflected in any phase task list — validators P1 and P2 are required at chunk-write time (Phase B.2) but are never tasked in B.1 or B.2; (2) the Phase B.0 acceptance criterion for the GAP.13 resolution references `MSR_v2_0.md` while the canonical MSR is now v3.0, making the acceptance test trivially wrong; and (3) Phase B.2's chunker specification is delegated entirely to "v1 plan §5.B.2" — a superseded document not present in the repository and never incorporated into the current plan. Nine ESCALATE findings add meaningful execution risk but do not individually block start. All three BLOCK findings have concrete remediation paths below and can be resolved with targeted plan amendments before B.0 begins.

---

## 2. Findings by Dimension

---

### D1 — Principle-Validator Fidelity

---

**Finding D1.1 — P1 Validator Detection Mechanism Unspecified** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §E.6, P1 row
- Observation: Reject fixtures are "claim mixing L1 fact + L2+ interp in same sentence; L2+ claim with no layer tag." Accept fixtures include "layer-bridged claim with explicit '[L1 fact] → [L2 interp]' marker."
- Issue: The reject case requires detecting "interpretive language" in an L1-tagged chunk. The plan does not specify how `p1_layer_separation.py` identifies interpretive claims. Syntactic marker-based detection (presence/absence of `[L1 fact] →` markers) only works if all cross-layer claims use the marker consistently. Without an LLM call or a curated vocabulary of interpretive language patterns, the validator cannot detect semantic violations — a claim like "Saturn in 7H Libra indicates delayed marriage" in an L1 chunk contains no syntactic marker but is unambiguously interpretive. Risk: the validator ships as a hollow stub that passes any chunk lacking an explicit violation marker, rubber-stamping semantic P1 violations.
- Remediation: Add an explicit subsection to §E.6 P1 specifying the detection strategy. Recommended: maintain a vocabulary of interpretive trigger-words (modal verbs: "indicates," "suggests," "implies," "denotes," "shows"; predictive language: "will," "tends to"; evaluative language: "strong," "weak," "afflicted") that, if present in an L1-tagged chunk without the explicit bridging marker, trigger a reject. This vocabulary becomes a fixture file alongside the accept/reject JSON fixtures. The false-positive rate should be verified against the actual L1 corpus before declaring the validator live.

---

**Finding D1.2 — P2 Field Name Reflects Pre-v8 Convention** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §E.6, P2 row
- Observation: Reject fixture is "L2+ claim with no `v6_ids_consumed`." Accept fixture is "L2+ claim citing resolvable L1 fact_ids." The canonical L1 source is `FORENSIC_ASTROLOGICAL_DATA_v8_0.md`. MSR_v3_0.md confirms the field is literally named `v6_ids_consumed` in the actual corpus.
- Issue: The field name `v6_ids_consumed` refers to the v6 forensic file, which is no longer canonical. IDs that exist in v8.0 but were added after v6.0 (any IDs introduced during v7.0 or v8.0 upgrades) could not have been referenced by `v6_ids_consumed` at signal-authorship time. The P2 validator as designed would pass any claim that cites `v6_ids_consumed` IDs, even if those IDs were superseded in v8.0, and would fail any claim that properly cites v8.0-only IDs under a corrected field name. This is a latent correctness risk as the corpus matures.
- Remediation: In §E.6 P2 row, document explicitly that `v6_ids_consumed` is a historical artifact of the MSR authoring convention and will NOT be renamed in Phase B (to avoid corpus-wide re-authoring cost). Instead, add a note that the P2 validator additionally checks: any L1 ID referenced in `v6_ids_consumed` resolves against `FORENSIC_ASTROLOGICAL_DATA_v8_0.md` (the canonical L1), not v6. Validator implementation must load v8.0 IDs as the resolution target, not v6.0 IDs.

---

**Finding D1.3 — P3 Validator UCN/CDLM Chunk Dependency Must Be Verified Pre-Phase** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §E.6 P3 row; §H
- Observation: P3 rejects "interpretive bundle with no L2.5 (UCN/CDLM) chunks." Confirmed by reconciler verification: UCN_v4_0.md and CDLM_v1_1.md exist in `025_HOLISTIC_SYNTHESIS/`.
- Issue: P3 enforcement requires UCN and CDLM chunks to be present in the `rag_chunks` vector store. The chunker for L2.5 document types must be built and run (Phase B.2) before P3 can meaningfully gate any retrieval bundle (Phase B.6). The plan's B.2 task says "~1,200 layer-tagged, type-tagged, schema-validated chunks" and cites "per-doctype chunkers" — but does not enumerate which doc-types are covered. UCN at 30-50K words requires a bespoke section-chunker; CDLM's 9×9 matrix requires a cell-chunker. These are non-trivial chunker implementations. If they are omitted from B.2, P3 fires vacuously until corrected.
- Remediation: B.2 task list must explicitly name UCN and CDLM as doc-types covered by the 6 chunkers. The chunking_report.json acceptance criterion (currently only "exactly 499 signal chunks; zero cross-layer chunks; no chunk >2000 tokens; stale chunks count matches Staleness Register") must add a line: "≥1 UCN chunk per major section; ≥1 CDLM chunk per cell."

---

**Finding D1.4 — P4 Validator Implementation Complexity Understated** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §E.6, P4 row
- Observation: Reject: "claim containing a position/date/degree not in L1."
- Issue: Detecting positions/dates/degrees "not in L1" requires exhaustive enumeration of all valid L1 positional values (planetary degrees, house cusps, dates, arc minutes), then checking any numeric value in LLM output against that set. This is harder than it sounds: positions appear in multiple syntactic forms (e.g., "21°57'35"", "21 degrees 57 minutes", "22°" in rounded form). The reject fixture tests one form; the actual LLM output vocabulary is wider. The plan does not allocate any explicit implementation effort for P4 beyond "each validator becomes implemented in the phase where its principle first applies." Phase B.4 (synthesis at B.8) is where P4 first applies — but the implementation complexity is comparable to parsing a small planetary position grammar.
- Remediation: Add to §H or §E.6 P4 row: "P4 implementation loads FORENSIC_v8_0 positions into a canonical_positions set at startup. Position detection in LLM output uses a regex that catches degree-minute-second patterns, rounded-degree patterns, and date patterns. Any detected position not in canonical_positions triggers reject. Tolerance: ±0.5° for rounded references." This bounds the implementation scope and avoids a hollow stub.

---

**Finding D1.5 — P5 Validator** — VERDICT: UPHOLD

- Location: §E.6, P5 row
- Observation: Reject is "claim citing SIG.MSR.888 (not in register)"; accept is "claim citing signals that exist in MSR_v3.0." Implementation: load 499 signal IDs from MSR_v3_0, check all SIG.* references in artifact text against this set.
- This is clear, implementable, and deterministic. No issues.

---

**Finding D1.6 — P6 Validator Requires Semantic Comparison; Not Purely Deterministic** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §E.6, P6 row; §H
- Observation: Reject: "answer favoring L3 domain claim when UCN contradicts without explicit override."
- Issue: Detecting that "UCN contradicts" an L3 claim requires semantic comparison between the answer and UCN content. This is not a deterministic structural check — it requires either (a) an LLM call to detect semantic tension, or (b) a pre-built contradiction index (which is exactly what the CONTRADICTION_REGISTER in B.5 is supposed to produce). But B.5 comes after B.6 and B.8 in the phase sequence, meaning P6 would need to enforce a rule during synthesis (B.8) using a contradiction index that doesn't exist until B.5 output is complete. The phase ordering creates a bootstrapping paradox: P6 needs contradictions identified to enforce authority, but contradictions are identified in B.5, and synthesis is tested in B.8 which comes after B.5.
- Remediation: Add to §H P6 dependency notes: "P6 during B.8 synthesis enforces UCN authority against L3 claims using the CONTRADICTION_REGISTER produced in B.5. Prior to CONTRADICTION_REGISTER existence, P6 degrades to: if the synthesis answer cites only L3 domain content with no UCN citation, flag as [P6_UNCHECKED]. Full P6 enforcement activates at B.8 after B.5 register is available." Document this degraded mode explicitly so implementors know P6 starts partial and completes at B.8.

---

**Finding D1.7 — P7 Significance Scoring Mechanism Undefined** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §E.6, P7 row; §E.9
- Observation: Reject: "significance≥0.7 answer with <3 interpretations." §E.9 mentions P7 active for "significance≥0.7" in tolerance spec.
- Issue: Neither §E.6 nor §H defines how a query or artifact receives a significance score at runtime. Significance is described as a threshold (≥0.7) but the mechanism that assigns this score to an incoming query or synthesis output is not specified. Is it a field in the QueryPlan output from the router? Is it computed from the retrieval bundle's average signal confidence? Without a defined scoring function, P7 cannot fire deterministically — the validator has no input to compare against 0.7.
- Remediation: Add to §H or §E.6 P7 row: "Significance score is a field in the `QueryPlan` object emitted by the router (Phase B.7). Router prompt instructs Opus to score significance on [0.0, 1.0] based on: (a) number of domains affected, (b) presence of timing/prediction in the query, (c) query type classification. Significance field is required in QueryPlan Pydantic model. P7 validator reads significance from the artifact's metadata field `significance_score`." This makes P7 enforceable.

---

**Finding D1.8 — P8 Rationale Quality Not Structurally Enforceable** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §E.6, P8 row
- Observation: Accept fixture: "claim with LOW/MED/HIGH + rationale citing citation breadth + convergence + counter-evidence."
- Issue: The accept fixture tests that rationale text is PRESENT and cites citation breadth/convergence/counter-evidence. But a claim with `confidence: HIGH` and `rationale: "high confidence"` contains the word "confidence" and would pass a keyword check while violating the spirit of P8. The validator cannot distinguish substantive rationale from superficial rationale without an LLM call.
- Remediation: Accept this structural limitation explicitly in §E.6. Document that P8 enforces structural presence (confidence field is LOW/MED/HIGH, rationale field is non-empty, rationale length ≥ 50 characters) but NOT rationale quality. Rationale quality is a human-in-loop concern at phase-gate review. Mark this as a known validator gap in the meta-test fixture header.

---

**Finding D1.9 — P9 Audit Trail Validator** — VERDICT: UPHOLD

- Location: §E.6, P9 row
- Observation: Reject cases are "missing ledger event references" and "input_bundle_hash mismatch." Both are structural, deterministic checks against the ledger.
- Implementation is sound and enforceable without LLM calls.

---

### D2 — Layer-Separation Self-Discipline

---

**Finding D2.1 — B.0 Task 1 Targets MSR_v2_0.md; Canonical MSR Is v3_0** — VERDICT: BLOCK

- Location: `PHASE_B_PLAN_v1_0.md` §G Phase B.0 Task 1; §G Phase B.0 Acceptance Criteria
- Observation: Task 1: "Append the string '7-karaka-alternative' to those specific signals in `MSR_v2_0.md`." Acceptance criterion: "grep of `MSR_v2_0.md` for '7-karaka-alternative' returns exactly the count enumerated in the resolution file."
- Issue: Confirmed by reconciler file inspection: the canonical MSR is `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md`. `MSR_v2_0.md` is also present in the same directory (not archived), creating version confusion. Appending "7-karaka-alternative" to v2_0 while the system uses v3_0 means the GAP.13 resolution has no effect on the operationally active MSR. P5's signal-ID resolution will load v3_0 IDs; the GAP.13 annotations will be invisible to the validator pipeline. The acceptance criterion would pass (grep on v2_0 succeeds) while the actual pipeline ignores the annotations. This is a silent failure mode.
- Remediation: Amend Task 1 to target `MSR_v3_0.md`. Amend the acceptance criterion to `grep of MSR_v3_0.md for '7-karaka-alternative'`. Archive `MSR_v2_0.md` to `99_ARCHIVE/` as part of B.0 cleanup (add as explicit sub-task). Also archive any other superseded MSR versions (v1_0, v2_0) to eliminate version ambiguity.

---

**Finding D2.2 — GAP_13_RESOLUTION Mixes L1 Determination With Interpretive Policy** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §G Phase B.0 Task 1; file placement `00_ARCHITECTURE/`
- Observation: The resolution document "detail[s] the 8-karaka lock, the rule preserving 7-karaka as a formal alternative for Pitrukaraka-dependent claims per P7."
- Issue: The 8-karaka vs. 7-karaka determination is an L1 fact decision (which planets constitute the 8 karakas is a positional calculation). The "rule preserving 7-karaka as formal P7 alternative" is interpretive policy (L2+). Placing both in `00_ARCHITECTURE/` is governance-appropriate but creates a document that straddles L1 and L2+ without a derivation ledger. The resolution document should cite the specific FORENSIC_v8_0 ID(s) that establish the karaka sequence, and the policy rule should be explicitly tagged as "[L2+ policy]" to preserve layer discipline within the governance document itself.
- Remediation: Add to Task 1: "GAP_13_RESOLUTION_v1_0.md must carry explicit layer tags: karaka sequence assertion tagged [L1 source: FORENSIC_v8_0 §<section>]; P7 alternative rule tagged [L2+ policy: interpretive]; signal enumeration references signal IDs from MSR_v3_0."

---

**Finding D2.3 — STALENESS_REGISTER in Architecture Folder Contains Analytical Judgments** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §G Phase B.1 Task 3
- Observation: "00_ARCHITECTURE/STALENESS_REGISTER.md — enumerate each L3 file, record `version_aligned_with`, mark stale where ≠ v8_0."
- Issue: The staleness judgment ("this L3 file is stale relative to v8_0") is an analytical assessment of corpus health, not a governance artifact. Placing it in `00_ARCHITECTURE/` blurs the architecture folder's role. Minor layering concern.
- Remediation: Move STALENESS_REGISTER.md to `035_DISCOVERY_LAYER/STALENESS_REGISTER.md` as it is a corpus analysis artifact, not an architectural governance document. If the project convention requires corpus health documents to live in architecture, document this convention explicitly in `00_ARCHITECTURE/CLAUDE.md`.

---

### D3 — Citation and Derivation Discipline

---

**Finding D3.1 — Cost Model Claims Uncited** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §E.7
- Observation: "Opus Pricing: $15 / 1M input tokens, $75 / 1M output tokens." "Voyage Pricing: $0.12 / 1M tokens." No source citation.
- Issue: API pricing is an externally-determined fact that changes without notice. The $210 budget was derived from these prices. If Opus 4.7 pricing differs from Opus 4.6 (which the cited prices match), the entire cost model is off. Additionally, call-count estimates (500 reconciler calls in B.5, 200 in B.4) lack derivation — there is no enumeration showing how 500 reconciler calls was computed from the planned discovery task volume.
- Remediation: Add to §E.7 a footnote: "Pricing as of 2026-04-23, Anthropic published rates. Verify at phase start. Call-count derivation: B.5 estimate of 500 reconciler calls assumes ~20 validated patterns × 5 reconciler passes/pattern + 10 resonances × 5 + 5 contradictions × 10 (inverted pass = higher iteration) + 10 clusters × 5 = ~250 core calls, doubled for re-runs and schema rejections = 500." Whether this arithmetic is correct is less important than that the derivation is visible and auditable.

---

**Finding D3.2 — "≥1,565 Deterministic Edges" Baseline Source Not Cited** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §G Phase B.4 Acceptance Criteria
- Observation: "Deterministic edges ≥1,565 (matches existing baseline)."
- Issue: The "existing baseline" is presumably the output of `platform/scripts/citation_graph_builder.py` run against the current corpus, but no verification artifact is cited. A fresh executor has no way to verify this number without running the script, and the script's output may differ from 1,565 after v8.0 upgrades.
- Remediation: Add: "Baseline of 1,565 edges was established by running `citation_graph_builder.py` on corpus as of 2026-04-23 and is recorded in `verification_artifacts/RAG/baseline_edge_count.json`. This file must be created in B.0 (pre-migration) to fix the baseline before QUERY_INTERFACE migration alters citation counts."

---

**Finding D3.3 — "Expected ~46" Current Files in FILE_REGISTRY Not Verifiable** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §G Phase B.1 Acceptance Criteria
- Observation: "Manifest count matches FILE_REGISTRY `is_current=true` count (expected ~46)."
- Issue: The tilde (~46) introduces imprecision into an acceptance criterion, and no FILE_REGISTRY version is cited. FILE_REGISTRY is itself an artifact that could change between plan authoring and B.1 execution.
- Remediation: Change to: "Manifest count matches FILE_REGISTRY_v1_0.md `is_current=true` count at phase-start snapshot. Record the actual count from FILE_REGISTRY_v1_0 in the B.0 session log entry and use that count as the B.1 acceptance target." Remove the tilde.

---

### D4 — Cost Model Realism

---

**Finding D4.1 — Reconciler Input Token Estimate Understated; 50% Buffer Insufficient** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §E.7
- Observation: "Reconciler: 4.0K in / 0.5K out = ~$0.0975 / call." B.5 has 500 reconciler calls ($48.75). Total with 50% buffer: ~$210.
- Issue: A 4K input context for a reconciler pass is realistic for simple graph-edge proposals (edge-type + two chunk summaries + principle checklist). It is not realistic for complex cross-domain pattern reconciliation in B.5, where the reconciler must hold: the full pattern hypothesis (mechanism + candidates + counter-cases + falsifier + supporting chunk IDs), the relevant MSR signals (each ~200-400 tokens), applicable principle texts, and prior-ledger context. A realistic B.5 reconciler context is 8K-16K tokens for complex patterns. At 8K average:
  - B.5 reconciler cost: 500 × ($15×0.008 + $75×0.0005) = 500 × ($0.12 + $0.0375) = 500 × $0.1575 = $78.75 (vs $48.75 in plan, +62%)
  - B.4 reconciler cost at 8K: 200 × $0.1575 = $31.50 (vs $19.50 in plan, +62%)
  - New base estimate: $140.09 - $48.75 - $19.50 + $78.75 + $31.50 = $181.09
  - At 50% buffer: ~$271 — still within a generous budget, but the stated $210 budget becomes inadequate.
- Counter-estimate: Recommend base budget of ~$180, buffer 75% (not 50%) → **~$315 budget for v1.0 M2.**
- Remediation: Amend §E.7 buffer statement to: "+75% for B.4/B.5 reconciler context overrun, retries, schema drift reworks → **~$315 budget for v1.0 M2.**" Alternatively, add a reconciler call profile split: "B.3.5/B.4 reconciler (edge proposals, low context): 4K in. B.5 reconciler (pattern/resonance/cluster, high context): 10K in / 1.0K out = $0.225/call."

---

**Finding D4.2 — Human-In-Loop Time Cost Acknowledged But Uncosted** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §E.7, §E.8
- Observation: "Gemini Pricing: $0.00 (Human-in-loop flat-rate)."
- Issue: §E.8 documents ~17h Gemini wall time + ~45h coding = ~62h native time investment. The $140 LLM budget represents only the API cost. This framing is correct for LLM billing purposes but risks creating misaligned expectations. The "budget" for Phase B is actually ~$315 API + ~62h native time. At any reasonable valuation of senior engineering time, the human-in-loop cost dominates.
- Remediation: Add a single line to §E.7: "Note: LLM budget covers API costs only. Human-in-loop estimated at ~62h total (§E.8). This is not in the LLM budget but is the dominant project cost."

---

### D5 — Doctrinal Risk Coverage

---

**Finding D5.1 — Staleness Register** — VERDICT: UPHOLD

Active mitigation in B.1 (STALENESS_REGISTER.md), B.2 (is_stale chunk metadata), §J risk table (stale-L3 contamination), red-team probe 3. Fully mitigated.

---

**Finding D5.2 — Two Vector Spaces: Index-Time OpenAI Fallback Creates Orphaned Chunks** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §G Phase B.3 Tasks
- Observation: "OpenAI only at index time, never at query time. If Voyage down at query time, return [RETRIEVAL_UNAVAILABLE]."
- Issue: If Voyage is unavailable during the B.3 indexing run and the runner falls back to OpenAI for some chunks, those chunks exist in a different embedding space. At query time, Voyage query vectors cannot retrieve OpenAI-indexed chunks (incompatible spaces). The chunks are effectively invisible — silently orphaned. The plan's §J risk table acknowledges this as "L" (low likelihood) but does not prescribe index-time halt behavior. The mitigation says "Index-time Voyage-only" but the fallback policy for Voyage index-time failure is not stated.
- Remediation: Add to §G Phase B.3 Tasks: "Index-time fallback policy: if Voyage API returns error on any batch, the indexing run HALTS with [RETRIEVAL_UNAVAILABLE] and logs the unindexed chunk IDs to `verification_artifacts/RAG/unindexed_chunks.jsonl`. No OpenAI fallback at index time. The run is re-attempted when Voyage is available. Reason: OpenAI-indexed chunks in a Voyage-indexed store create a silently-mixed embedding space that is undetectable at query time."

---

**Finding D5.3 — Opus 4.7 Router Has No Fallback Policy** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §B.5 CQ6; §G Phase B.7
- Observation: "CQ6: Opus 4.7 router — STACK DEVIATION; native override reconfirmed; no downgrade path."
- Issue: "No downgrade path" is stated but no availability fallback is described. If Opus 4.7 is unavailable (model deprecation, API outage), the router cannot classify queries, the discovery engine cannot proceed, and the synthesis path fails. At a ~4-week execution timeline, the risk of a multi-hour API outage is non-trivial.
- Remediation: Add to §G Phase B.7: "Router availability fallback: if Opus 4.7 is unavailable, route all incoming queries to a static fallback QueryPlan: type='exploratory', significance=0.5, domains=['all']. Log the degraded routing event to ledger. Do NOT fall back to a different model — the router is intentionally Opus 4.7 and a different model would produce different plan taxonomies incomparable to logged ones."

---

**Finding D5.4 — Ledger Compaction Roll-Up Never Tasked** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §B.3 (B.2.4 reference), §J risk table
- Observation: §J risk table mentions "rolled-up ledger view; acceptance rate tracked per batch, threshold alerts at <15% or >80%." §E.5 mentions "B.2.4 rolled-up ledger view."
- Issue: No phase task in B.0–B.10 explicitly creates the ledger roll-up view or the acceptance-rate tracking mechanism. The `ledger.py` module is listed in §K but never tasked with implementing the roll-up. Discovery register bloat is rated "H" (high likelihood) in §J — this is the dominant operational risk in B.5 — yet the mitigation artifact is never explicitly built.
- Remediation: Add to §G Phase B.5 Tasks: "Before beginning pattern-mining batches: ensure `ledger.py` exposes `get_acceptance_rate(batch_id)` function. After each Gemini batch, compute acceptance rate and log to `verification_artifacts/RAG/batch_acceptance_rates.json`. If rate < 15% or > 80%, emit stop-marker `[ACCEPTANCE_RATE_ANOMALY]` and surface to native before proceeding."

---

**Finding D5.5 — Pass-Order Inversion** — VERDICT: UPHOLD

§E.5 table is complete, internally consistent, and clearly typed. Contradictions (Claude→Gemini), reconciliations split by type, retrieval bundles excluded. UPHOLD.

**Finding D5.6 — CGM Rebuild** — VERDICT: UPHOLD

Phase B.3.5 explicitly scoped as prerequisite micro-phase. CQ5=b resolved. UPHOLD.

**Finding D5.7 — Structural Reproducibility** — VERDICT: UPHOLD

§E.9 tolerance specification is complete: artifact IDs (hash-derived, 100% identical), confidence (±1 level), citation set (≥85% Jaccard), interpretation similarity (≥0.75 cosine), validator decisions (100% identical). Enforcement via ledger. UPHOLD.

---

### D6 — Learning Layer Integration Test

---

**Finding D6.1 — Hook 1: `06_LEARNING_LAYER/` Scaffold** — VERDICT: UPHOLD

- Phase B task creating the hook: B.0 Task 10 ("Scaffold `06_LEARNING_LAYER/` tree + `prediction_ledger.jsonl` (empty) + schema files v0.1"). Wiring is explicit and specific. UPHOLD.

---

**Finding D6.2 — Hook 2: P8 Validator Extension and `prediction_ledger.py` Not Sequenced Within B.5** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §F.2; §G Phase B.5 Step 17; §H
- Observation: "Any register entry containing a time-indexed falsifiable claim triggers a row in `06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl`. P8 validator extension enforces 'no falsifier → cannot be classified forward-looking'." §H says P8 is implemented "in the phase where its principle first applies (B.5 for P7/P8)."
- Issue: B.5 simultaneously (a) implements the P8 extension, (b) starts discovery mining that produces prediction-ledger rows, and (c) depends on the P8 extension being in place before the first forward-looking artifact is written. If B.5 task sequencing is: start mining → hit first forward-looking claim → write row → P8 extension not yet built, the row is written without P8 enforcement. Additionally, `prediction_ledger.py` (the writer module) is listed in §K's file manifest but never explicitly tasked in any phase. B.0 Task 9 scaffolds "empty modules with docstrings" — this covers `prediction_ledger.py` skeleton, but the actual append-logic implementation must happen before B.5 Step 17.
- Remediation: Add to §G Phase B.5 Tasks, as Task 0 (pre-mining gating task): "Before beginning any discovery mining: (a) implement and test `rag/prediction_ledger.py` with `append_prediction(entry: Prediction)` method and append-only file writes; (b) implement and test P8 validator extension: any artifact marked as forward-looking must have non-null `falsifier_conditions` field; (c) implement and test P7 validator now (needed simultaneously). Run `pytest validators/` before proceeding to mining tasks."

---

**Finding D6.3 — Hook 3: `prompt_registry.py` Implementation Not Tasked** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §F.3; §K file manifest
- Observation: Every prompt file carries frontmatter hash; every ledger event references `prompt_ref`, `prompt_version`, `prompt_hash`; `PROMPT_REGISTRY/INDEX.json` accumulates entries.
- Issue: `platform/python-sidecar/rag/prompt_registry.py` is listed in §K but never tasked in any phase. The mechanism for creating registry entries when prompt files are written — whether via git hook, manual invocation, or a function called at ledger-event write time — is unspecified. If `prompt_hash` is required in every ledger event (it was promoted to a required field in v1.0.1 changelog), but no code exists to compute and insert it, ledger events will be malformed from day one.
- Remediation: Add to §G Phase B.0 Tasks: "Task 12: Implement `rag/prompt_registry.py` with function `register_prompt(path: str, version: str) -> PromptRegistryEntry`. This function: reads the prompt file, computes sha256 of body, writes/updates `PROMPT_REGISTRY/INDEX.json` with the entry, returns the entry for inline use in ledger events. Create a B.0 smoke-test: register the single empty prompt placeholder file and verify INDEX.json is updated." Population deferred to Phase B.4+ when actual prompts are authored.

---

### D7 — Two-Pass Ordering Execution Fidelity

---

**Finding D7.1 — No Runtime Enforcement That Gemini Pass Precedes Claude Pass** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §E.5; §B.5 Tasks
- Observation: §E.5 specifies Gemini→Claude ordering for patterns, resonances, clusters. CQ3 specifies: "human-in-loop Gemini; batched prompts + response files; `actor=gemini-web-<date>`."
- Issue: The Gemini pass is mediated by human copy-paste, not code. The `actor=gemini-web-<date>` field in ledger events is set by the executor (Claude or native), not verified against any cryptographic or structural property of the response. A Claude-authored response mistakenly labeled `actor=gemini-web-<date>` would pass all ledger checks. There is no code path that enforces "this response was produced by a Gemini model." P9's audit trail check verifies that two-pass ledger events exist; it cannot verify the events' actor fields are truthful.
- Issue severity: In practice, native-mediated Gemini copy-paste is a behavioral enforcement. The risk is process drift (a session where Claude drafts pattern hypotheses labeled as Gemini pass, skipping the true promiscuous-connector step).
- Remediation: Cannot be fully code-enforced given human-in-loop architecture. Add a compensating control: "Each Gemini batch produces a raw response file saved at `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/<date>_batch_N_raw.md` before Claude reconciler runs. This file is committed to git. Its existence and timestamp provides non-repudiation that a Gemini pass occurred. P9 validator should verify the corresponding raw response file exists for every Gemini-authored ledger event." This is not cryptographic but is auditable in git history.
- UPHOLD for contradiction pipeline: Claude's invariant scanner (code-enforced) must run before Gemini reconciliation, so the inverted pass order for contradictions IS runtime-enforced.

---

### D8 — Dependency-Ordering Soundness

---

**Finding D8.1 — P1/P2 Validators Required at B.2 Chunk-Write but Not Tasked in B.1 or B.2** — VERDICT: BLOCK

- Location: `PHASE_B_PLAN_v1_0.md` §H; §G Phase B.1 Tasks; §G Phase B.2 Tasks
- Observation: §H states: "P1, P2, P5 run at every chunk write, retrieval, and artifact write." §H also states: "each validator becomes implemented in the phase where its principle first applies (B.1 for P1/P2, B.5 for P7/P8, etc.)."
- Issue: B.1's task list contains 5 tasks: (1) ingest.py, (2) models.py, (3) STALENESS_REGISTER.md, (4) ingestion_manifest.json, (5) first prompt-registry entries. Zero mention of building `p1_layer_separation.py` or `p2_citation.py`. B.2's task list says "Each chunk validated against `Chunk` Pydantic model pre-write" — this is a data-model validation, not principle validation. If P1 and P2 validators are required "at every chunk write" and first apply at B.2, they must be implemented before B.2 chunk writes begin. Neither B.1 nor B.2's task lists include this. This is a BLOCK: the first 1,200 chunk writes in Phase B will occur without the gating validators that the plan declares mandatory.
- Remediation: Add to §G Phase B.1 Tasks as new Task 1.5 (after models.py is built): "Implement and test `rag/validators/p1_layer_separation.py`, `p2_citation.py`, and `p5_signal_id_resolution.py`. These three validators must pass their meta-tests before B.2 begins. P1 meta-tests: 3 reject fixtures (interpretive claim in L1 chunk, no layer tag, mixed claim without marker) + 2 accept fixtures. P2 meta-tests: 2 reject fixtures (no v6_ids_consumed, non-existent ID) + 2 accept fixtures. P5 meta-tests: 2 reject fixtures (non-existent signal ID) + 2 accept fixtures. Run: `pytest platform/python-sidecar/rag/validators/test_p1_p2_p5.py` must pass before B.2 begins."

---

**Finding D8.2 — Gemini Batch Prompt Templates for B.3.5 Not Tasked or Described** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §G Phase B.3.5 Task 4
- Observation: "Two-pass. Gemini proposes any additional edges (e.g., subtle aspect relationships, Chalit shifts) from the L1 base."
- Issue: B.3.5 is the first phase that invokes a Gemini pass. The prompt for this Gemini pass (asking Gemini to propose additional CGM edges given L1 data) is not described, not listed in the file manifest, and not tasked in B.3.5. The §E.4 cluster annotation prompt is described, but no comparable CGM edge-proposal prompt exists anywhere in the plan. An executor reaching B.3.5 Task 4 would need to author a Gemini prompt from first principles.
- Remediation: Add to §G Phase B.3.5 Tasks a new task before Task 4: "Author `035_DISCOVERY_LAYER/PROMPTS/gemini/cgm_edge_proposals_v1_0.md`. Prompt structure: ROLE (promiscuous connector, pass 1), TASK (propose additional CGM edges beyond deterministic set), INPUT (node list, existing edge types, L1 basis for proposed nodes), OUTPUT (strict YAML: proposed_edges: [{source_node, edge_type, target_node, L1_basis, classical_basis_if_applicable, confidence_prior}]), CONSTRAINTS (cite only from L1 v8.0; no invented positions; if uncertain flag [EXTERNAL_COMPUTATION_REQUIRED]). Register prompt in PROMPT_REGISTRY before use." This can be authored by Claude at B.3.5 start — it does not require native action.

---

**Finding D8.3 — Discovery-Eval Harness Tests B.5 Work from B.9; 4-Phase Evaluation Gap** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §G Phase B.9 Tasks; §G Phase B.5 Acceptance Criteria
- Observation: B.5 acceptance criteria: "At least 20 validated patterns, 10 validated resonances, 5 validated contradictions, 10 annotated clusters." The discovery-engine eval harness (seeded known facts, seeded contradictions, seeded false patterns) is built in B.9, which is 4 phases later.
- Issue: Phase B.5 closes with self-assessed acceptance criteria (reconciler declares >20 validated patterns). The formal eval harness that could falsify this count doesn't exist until B.9. If the discovery engine has a systematic flaw — for example, a chunker bug that caused 40% of MSR signals to be mis-chunked, causing spurious pattern proposals — B.5 would declare success while producing low-quality patterns that the B.9 eval harness would later reject. The 4-phase gap means 4-6 sessions of work proceed on potentially flawed foundations.
- Remediation: Add to §G Phase B.5 Tasks a mid-phase gate: "After first 5 patterns are validated: run `rag/eval/run_eval.py --mode=discovery_sanity --seed_set=5` against the 5 seeded known facts (to be created as part of B.5 setup, not B.9). This mini-eval must achieve seed recall ≥ 0.8 on the 5 seeds before proceeding to full discovery mining. This is NOT the full B.9 eval harness, but provides early signal that the chunking and embedding pipeline correctly surfaces known content." Full eval harness with 50 golden queries remains in B.9.

---

**Finding D8.4 — B.2 Chunker Specification References Superseded External Document** — VERDICT: BLOCK

- Location: `PHASE_B_PLAN_v1_0.md` §G Phase B.2 Tasks
- Observation: "Tasks. Per-doctype chunkers as in v1 plan §5.B.2, preserving all invariants there."
- Issue: "v1 plan" refers to the session-scoped draft `twinkly-puzzling-quokka.md`, which the Phase B Plan header states it supersedes: "Supersedes: `twinkly-puzzling-quokka.md` (session-scoped draft)." Confirmed by reconciler inspection of `twinkly-puzzling-quokka.md`: it contains the identical self-referential line at §B.2 Tasks — "Per-doctype chunkers as in v1 plan §5.B.2" — meaning neither document contains the actual chunker specification. The specification was never written. An executor attempting B.2 must author all per-doctype chunker invariants from scratch, introducing non-reproducibility.
- Issue (extended): The chunker specification defines: what constitutes a chunk boundary for each document type (MSR signal boundaries, UCN section boundaries, CDLM cell boundaries, L1 fact boundaries, domain report section boundaries), what metadata fields each chunk carries, what the maximum token limit enforcement mechanism is, and how signal-type chunks are tagged for the cluster annotation step (B.5 Step 13 filters to "L2.5 signal chunks only"). None of this is in the plan.
- Remediation: This is a BLOCK requiring a plan amendment before B.2 begins (not before B.0). Add to §G Phase B.2 a "Chunker Specification" subsection that explicitly defines for each of the 6 doc-types: (a) chunk unit (signal boundary / UCN H2 section / CDLM cell / L1 fact group / domain report Part), (b) chunk metadata required fields, (c) boundary detection method (regex / YAML frontmatter / markdown H-level), (d) maximum token limit enforcement, (e) how stale metadata is propagated. Alternatively: create `035_DISCOVERY_LAYER/SCHEMAS/chunker_spec_v1_0.md` as a Phase B.0 artifact that contains this specification, and amend B.2 to reference it.

---

### D9 — Structural Reproducibility

---

**Finding D9.1 — Chunker Invariants Depend on Unrepresented External Document** — VERDICT: BLOCK

See Finding D8.4 above. This is the primary structural reproducibility failure: the chunker specification is absent from the plan, making Phase B.2 output non-reproducible from the plan alone.

---

**Finding D9.2 — MSR Stale Version Reference Undermines Acceptance Criterion Reproducibility** — VERDICT: BLOCK

See Finding D2.1 above. A fresh executor following the plan literally would append to MSR_v2_0 (which exists on disk) and pass the grep acceptance criterion, without the annotations appearing in the operationally active MSR_v3_0.

---

**Finding D9.3 — Gemini Pass Output Files Not Committed to Plan-Specified Locations** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §B.5 Tasks; §E.5
- Observation: CQ3: "batched prompts + response files; `actor=gemini-web-<date>`."
- Issue: The plan does not specify where Gemini response files are stored. Finding D7.1's remediation proposes `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/<date>_batch_N_raw.md`. Without a specified location in the plan, response files may be stored ad hoc or discarded, making the two-pass trail unauditable from the plan alone.
- Remediation: Add to §G Phase B.3.5 and B.4/B.5 Tasks a standard: "Gemini response files stored at `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/YYYY-MM-DD_B<phase>_batch<N>_raw.md` before Claude reconciler reads them. Path recorded in ledger event `gemini_response_ref` field."

---

**Finding D9.4 — Golden Query Sets Not Specified** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §G Phase B.6 Acceptance Criteria; §G Phase B.7 Acceptance Criteria; §G Phase B.9 Tasks
- Observation: "20 golden router queries correctly classified (manual review)." "50 golden queries" in B.9. These sets are not enumerated in the plan.
- Issue: A fresh executor must generate the golden sets from scratch. If the original golden sets were carefully curated to represent known-hard cases (e.g., query types that would stress-test the Whole-Chart-Read enforcement), a fresh generation may be easier and produce over-optimistic eval metrics.
- Remediation: The golden sets should be authored in Phase B.0 and saved as `verification_artifacts/RAG/golden_router_queries_v1_0.json` (20 queries with expected classifications) and `platform/python-sidecar/rag/eval/golden.jsonl` (50 queries with expected retrievals). Add "Author golden query sets (20 router, 50 eval)" as Task 13 to Phase B.0.

---

### D10 — Scope-Boundary Integrity

---

**Finding D10.1 — CGM Not Confirmed as Chunked Doc-Type; P3 Enforcement in Graph-Walk Bundles May Be Incomplete** — VERDICT: ESCALATE

- Location: `PHASE_B_PLAN_v1_0.md` §G Phase B.2; §K file manifest
- Observation: §K lists `platform/python-sidecar/rag/chunkers/*.py (6 files per doc-type)`. §G Phase B.3.5 rebuilds CGM_v9_0.md as an L2.5 corpus artifact.
- Issue: The 6 doc-types are never enumerated. CGM is an L2.5 artifact with distinct structure (nodes: dicts of properties; edges: typed triples). A graph-walk retrieval bundle that follows CROSS_LINKS or AFFECTS_DOMAIN edges would naturally land on CGM nodes. If CGM is not chunked and embedded, these traversals produce no retrievable chunks. P3 requires "≥1 UCN chunk + ≥1 CDLM chunk" in interpretive bundles — it does not require CGM chunks, so this does not block P3. But holistic synthesis quality degrades if CGM node properties cannot be surface in retrieval.
- Remediation: Explicitly enumerate the 6 chunker doc-types in §G Phase B.2: (1) MSR signals (YAML-boundary chunker), (2) UCN sections (H2-boundary chunker), (3) CDLM cells (grid-cell chunker), (4) L1 fact groups (section-boundary chunker from FORENSIC_v8_0), (5) Domain reports Parts (H2-Part-boundary chunker), (6) CGM nodes (property-dict chunker: one chunk per CGM node, carrying all properties). CGM is the sixth chunker. Add to B.2 acceptance criteria: "CGM node chunks count = CGM_v9_0 node count (verify post-B.3.5 rebuild)." Note: CGM chunker runs after B.3.5 produces CGM_v9_0, so Phase B.3.5 must re-trigger the CGM chunker; add this as an explicit step in B.3.5.

---

**Finding D10.2 — Objective Achievable Given Confirmed L2.5 Corpus** — VERDICT: UPHOLD

- Reconciler verification confirms: UCN_v4_0.md, CDLM_v1_1.md, MSR_v3_0.md, CGM_v2_0.md all exist in `025_HOLISTIC_SYNTHESIS/`. The previously unresolved question of whether UCN exists is answered: UCN v4.0 is present. P3 enforcement is achievable once UCN is chunked and indexed. "L2.5 synthesis query-callable" is achievable within Phase B scope given the L2.5 corpus completeness.

---

**Finding D10.3 — Discovery-Primary Objective Fully In Scope** — VERDICT: UPHOLD

Phase B delivers four discovery registers, two-pass trail, and thin validation UI. M3+ work (temporal animation, signal-weight calibration, Bayesian model) is explicitly excluded. Learning Layer hooks are substrate-only. Scope boundary is clean and enforced.

---

## 3. Aggregate Summary

### BLOCK Findings (must remediate before Phase B.0 begins)

| Finding | Location | Remediation |
|---------|----------|-------------|
| D8.1 — P1/P2 validators not tasked in B.1/B.2 despite being required at chunk-write time | §H; §G B.1/B.2 Tasks | Add Task 1.5 to B.1: implement and meta-test p1, p2, p5 validators before B.2 begins |
| D2.1 — B.0 acceptance criterion targets MSR_v2_0; canonical is MSR_v3_0 | §G B.0 Task 1 + Acceptance Criteria | Amend Task 1 and acceptance criterion to target MSR_v3_0; archive v2_0 and earlier in B.0 |
| D8.4/D9.1 — B.2 chunker specification delegated to superseded, unrepresented document | §G B.2 Tasks | Add explicit chunker specification subsection or create `chunker_spec_v1_0.md` in B.0; enumerate 6 doc-types with boundary rules and metadata requirements |

### ESCALATE Findings (address before Phase B closes; do not block B.0 start)

| Finding | Severity | Dimension |
|---------|----------|-----------|
| D1.1 — P1 hollow stub risk; detection mechanism unspecified | Medium | D1 |
| D1.2 — v6_ids_consumed field vs v8.0 canonical; validator must resolve against v8.0 IDs | Low | D1 |
| D1.3 — UCN/CDLM chunker not confirmed; must be explicit in B.2 | Medium | D1/D10 |
| D1.4 — P4 implementation complexity understated; needs position grammar spec | Medium | D1 |
| D1.6 — P6 requires semantic comparison; degraded-mode enforcement must be documented | Medium | D1 |
| D1.7 — P7 significance scoring mechanism undefined | High | D1 |
| D1.8 — P8 rationale quality unenforceable structurally; document gap explicitly | Low | D1 |
| D2.2 — GAP_13_RESOLUTION mixes L1 and L2+ without layer tags | Low | D2 |
| D2.3 — STALENESS_REGISTER in architecture folder; analytical artifact placement | Low | D2 |
| D3.1 — Cost model call-count derivation uncited; pricing uncited | Medium | D3 |
| D3.2 — "≥1,565 edges" baseline source uncited | Low | D3 |
| D3.3 — "~46 current files" imprecise acceptance criterion | Low | D3 |
| D4.1 — Reconciler input underestimated; 50% buffer likely insufficient; recommend 75% | High | D4 |
| D4.2 — Human-in-loop time cost not acknowledged in budget framing | Low | D4 |
| D5.2 — OpenAI index-time fallback creates orphaned chunks; plan must specify halt-not-fallback | High | D5 |
| D5.3 — Opus 4.7 router has no availability fallback | Medium | D5 |
| D5.4 — Ledger compaction roll-up script never tasked | Medium | D5 |
| D6.2 — Hook 2: prediction_ledger.py and P8 extension unsequenced within B.5 | High | D6 |
| D6.3 — Hook 3: prompt_registry.py never explicitly tasked | Medium | D6 |
| D7.1 — Gemini pass order unenforceable in code; compensating control (raw response files) recommended | Medium | D7 |
| D8.2 — CGM edge-proposal prompt for B.3.5 not authored or tasked | Medium | D8 |
| D8.3 — Discovery eval harness 4-phase gap; mid-phase sanity eval recommended | Medium | D8 |
| D9.3 — Gemini response file storage location unspecified | Low | D9 |
| D9.4 — Golden query sets not authored in plan | Medium | D9 |
| D10.1 — CGM not confirmed as 6th chunker doc-type | Medium | D10 |

### UPHOLD Findings (no action required)

- D1.5 — P5 signal-ID validator: clean, deterministic, implementable
- D1.9 — P9 audit trail validator: structural, implementable
- D5.1 — Staleness register: fully mitigated across B.1, B.2, §J, red-team probe 3
- D5.5 — Pass-order inversion for contradictions: correctly typed and enforced
- D5.6 — CGM rebuild: explicitly scoped as B.3.5
- D5.7 — Structural reproducibility: §E.9 tolerance specification complete
- D6.1 — Hook 1 wiring: B.0 Task 10 is explicit and specific
- D10.2 — L2.5 corpus confirmed complete (UCN v4.0, CDLM v1.1, MSR v3.0 exist)
- D10.3 — Scope boundary to M2 is clean; Learning Layer hooks are substrate-only

---

## 4. Pre-Execution Checklist (BLOCK remediation sequence)

Before Phase B.0 begins, the following amendments to `PHASE_B_PLAN_v1_0.md` must be applied and confirmed by native:

- [ ] **B.0 Task 1**: Change `MSR_v2_0.md` → `MSR_v3_0.md` everywhere in Task 1 and its acceptance criterion. Add sub-task: archive MSR_v1_0.md, MSR_v2_0.md to `99_ARCHIVE/` in B.0.
- [ ] **B.1 Task 1.5**: Add explicit task: implement `p1_layer_separation.py`, `p2_citation.py`, `p5_signal_id_resolution.py` with meta-tests passing before B.2 begins.
- [ ] **B.2 Chunker Spec**: Add `035_DISCOVERY_LAYER/SCHEMAS/chunker_spec_v1_0.md` as a B.0 artifact (authored at B.0 time), enumerating 6 doc-types with boundary rules. Amend B.2 Tasks to reference this spec.

Three amendments. One plan version bump to v1.0.2. Then B.0 can proceed.

---

*Reconciler pass closed: 2026-04-23. All BLOCK findings carry concrete remediation paths. No finding requires architectural rethink. ESCALATE findings should be tracked in the §J risk table updates or as session-log flags at the phase where each becomes actionable.*
