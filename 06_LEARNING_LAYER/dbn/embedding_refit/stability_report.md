---
artifact: stability_report.md
version: "1.0"
status: FAIL
run_date: 2026-05-13
produced_by: M5-D-S1
model: text-multilingual-embedding-002
signal_count: 30
---

# LL8 Embedding Refit Stability Report

## Verdict: UNSTABLE

| Criterion | Run 01 | Run 02 | Run 03 | Status |
|-----------|--------|--------|--------|--------|
| §4.1 Hash stability | variant | variant | variant | FAIL |
| §4.2 Retrieval pass rate | 7/30 | 7/30 | 7/30 | FAIL |
| §4.3 Matrix delta Δ(01,02) | — | 0.01634651 | — | FAIL |
| §4.3 Matrix delta Δ(01,03) | — | — | 0.01634651 | FAIL |
| §4.3 Matrix delta Δ(02,03) | — | — | 0.00651407 | PASS |

## Top-1 retrieval failures (if any)

All 23 signals failed top-1 across all three runs. The dominant attractor is SIG.13 (capturing most failures) and SIG.MSR.402 / SIG.MSR.476 (capturing the remainder). Only 7 signals self-retrieved correctly in every run: CTR.01, CTR.03, CVG.02, RPT.DSH.01, SIG.13, SIG.MSR.402, SIG.MSR.476.

Signals that failed top-1 in all 3 runs:
SIG.01, SIG.09, SIG.10, SIG.12, SIG.15, SIG.MSR.013, SIG.MSR.118, SIG.MSR.119,
SIG.MSR.143, SIG.MSR.145, SIG.MSR.163, SIG.MSR.170, SIG.MSR.198, SIG.MSR.229,
SIG.MSR.251, SIG.MSR.278, SIG.MSR.291, SIG.MSR.295, SIG.MSR.297, SIG.MSR.300,
SIG.MSR.301, SIG.MSR.391, SIG.MSR.391

SIG.MSR.030 additionally showed inconsistent top-1 across runs (SIG.13 / SIG.MSR.476 / SIG.13).

## Hash instability (if any)

6 signals with hash variance between run_01 and run_02/03 (runs 02 and 03 are mutually
identical for these signals, indicating run_01 was the divergent run):

- CTR.01: 8501b5ad... / 770d11eb... / 770d11eb...
- CVG.02: d497911e... / d594ea33... / d594ea33...
- SIG.01: b4e76404... / 044da4a6... / 044da4a6...
- SIG.12: ca8dcb09... / 10003696... / 10003696...
- SIG.13: a1096a12... / 29da7665... / a1096a12... (run_03 reverted to run_01 hash)
- SIG.15: 872edd75... / 49d9e718... / 49d9e718...

All hash variants are between run_01 and {run_02, run_03}, not between run_02 and run_03
(except SIG.13 which has a three-way split). These are signals sourced via the natal_to_domain
fallback path; the hash instability likely reflects non-deterministic fallback text ordering
(set-to-list conversion in `_fallback_chunk_texts`).

## Recommendation

Embedding refit UNSTABLE. CPT Bayesian fitting (CF.M5C.2) is **blocked** pending remediation.

**Root cause analysis (two distinct failure modes):**

1. **§4.2 Top-1 pass rate failure (7/30 = 23.3%, threshold ≥27/30):** The query-form
   embedding strategy ("sig msr 297 signal" etc.) produces query vectors that are dominated
   by surface-form token overlap with SIG.13 and SIG.MSR.402/476 rather than semantic
   content. The query form used (`sid.replace(".", " ").replace("_", " ").lower() + " signal"`)
   is insufficiently discriminative. Remediation: replace the humanized-ID query form with
   the signal's own chunk text as the query (task_type=RETRIEVAL_QUERY), which is the
   standard self-retrieval test pattern.

2. **§4.1 Hash instability (6/30 signals):** The fallback path `_fallback_chunk_texts`
   uses `set(derivations[sid])` before joining, which produces non-deterministic ordering
   in Python < 3.7 or when there are multiple derivation entries. Run_01 diverged on 5 of
   these 6 signals; runs 02 and 03 agreed. Remediation: replace `set(derivations[sid])`
   with `sorted(set(derivations[sid]))` in `_fallback_chunk_texts` to ensure deterministic
   text construction.

**Next actions before re-running stability test:**
1. Fix `_fallback_chunk_texts`: `sorted(set(derivations[sid]))` instead of `set(...)`.
2. Fix top-1 query form: use chunk text itself as the query (self-retrieval test), not
   humanized signal ID string.
3. Re-run 3-run stability test from scratch (clear run_logs/).
4. Obtain NAP.M5.3 approval on REFIT_GATE_v1_0.md once STABLE verdict is achieved.

*End of stability_report.md v1.0 (M5-D-S1, 2026-05-13)*
