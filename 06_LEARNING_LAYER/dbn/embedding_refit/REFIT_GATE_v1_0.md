---
artifact: REFIT_GATE_v1_0.md
canonical_id: REFIT_GATE
version: "1.0"
status: FAIL
produced_by: M5-D-S1
produced_on: 2026-05-13
nap_input: NAP.M5.3
gate_verdict: UNSTABLE
m5_d_entry_cleared: false
---

# REFIT_GATE v1.0 — LL8 Embedding Refit Gate

## Gate verdict: UNSTABLE

| Field | Value |
|---|---|
| Model | text-multilingual-embedding-002 (768-dim) |
| Signal count | 30 Type A production signals |
| Runs executed | 3 (run_01, run_02, run_03) |
| Run date | 2026-05-13 |
| §4.1 Hash stability | FAIL |
| §4.2 Top-1 pass rate (≥27/30) | FAIL — counts: run_01=7, run_02=7, run_03=7 |
| §4.3 Matrix delta (<0.01) | FAIL — max delta = 0.01634651 |
| **Overall** | **UNSTABLE** |

## M5-D entry decision

The LL8 embedding refit stability gate is **NOT CLEARED**. Two independent failure modes
were identified:

**Failure 1 — §4.2 Top-1 pass rate: 7/30 across all 3 runs (threshold ≥27/30).**
The top-1 retrieval audit uses a humanized signal ID string as the query
(`"sig msr 297 signal"` etc.), which produces query vectors dominated by surface-form
token overlap with attractor signals SIG.13 and SIG.MSR.402/SIG.MSR.476 rather than
semantic content. 23 of 30 signals fail to self-retrieve against this query form.
This is a methodology defect in the top-1 audit procedure, not an embedding quality failure.

**Failure 2 — §4.1 Hash stability: 6/30 signals show hash variance.**
The `_fallback_chunk_texts` function uses `set(derivations[sid])` before joining, producing
non-deterministic text ordering when multiple derivation entries exist. Run_01 diverged from
runs 02/03 for 5 signals; SIG.13 showed a three-way split. Remediation is a one-line fix:
`sorted(set(derivations[sid]))`.

**Consequent failure — §4.3 Matrix delta: max Δ(01,02) = 0.01634651 (threshold <0.01).**
This is downstream of the §4.1 hash instability; once text construction is deterministic,
this criterion is expected to pass.

CPT Bayesian fitting (CF.M5C.2) is **blocked** until a STABLE gate is achieved.

Next actions:
1. Fix `_fallback_chunk_texts` in refit.py: `sorted(set(...))` for deterministic text.
2. Fix top-1 audit query form: use chunk text itself as RETRIEVAL_QUERY (self-retrieval),
   not humanized signal ID string.
3. Clear run_logs/ and re-run 3-run stability test.
4. Re-submit REFIT_GATE_v1_1.md with STABLE verdict for NAP.M5.3.

## Signal-level audit summary
- Signals with top-1 FAIL (all 3 runs): SIG.01, SIG.09, SIG.10, SIG.12, SIG.15,
  SIG.MSR.013, SIG.MSR.030, SIG.MSR.118, SIG.MSR.119, SIG.MSR.143, SIG.MSR.145,
  SIG.MSR.163, SIG.MSR.170, SIG.MSR.198, SIG.MSR.229, SIG.MSR.251, SIG.MSR.278,
  SIG.MSR.291, SIG.MSR.295, SIG.MSR.297, SIG.MSR.300, SIG.MSR.301, SIG.MSR.391
- Signals with top-1 inconsistency across runs: SIG.MSR.030 (SIG.13 / SIG.MSR.476 / SIG.13)
- Signals with hash variance: CTR.01, CVG.02, SIG.01, SIG.12, SIG.13, SIG.15

## Notes
- Signal ID source: ll1_weights_promoted_v1_0.json signal_weights keys (30 IDs)
- Corpus source: msr_signals Postgres table (claim_text + classical_basis)
- 10 signals not found in msr_signals; sourced via natal_to_domain.json fallback:
  CTR.01, CTR.03, CVG.02, RPT.DSH.01, SIG.01, SIG.09, SIG.10, SIG.12, SIG.13, SIG.15
- Composite signals (CTR.*, CVG.*, RPT.DSH.01): fallback to natal_to_domain.json
  derivation text if not present in msr_signals
- SIG.MSR.117 (shadow node) excluded from refit per LL8.O1
- VERTEX_PROJECT corrected from "amjis-jyotish" to "madhav-astrology" in refit.py
  (was a scaffold error in the initial script; fixed at M5-D-S1 run time)

*End of REFIT_GATE_v1_0.md v1.0 (M5-D-S1, 2026-05-13)*
