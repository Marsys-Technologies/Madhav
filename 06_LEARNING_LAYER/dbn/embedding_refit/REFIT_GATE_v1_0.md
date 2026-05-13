---
artifact: REFIT_GATE_v1_0.md
canonical_id: REFIT_GATE
version: "1.0"
status: PASS
produced_by: M5-D-S1
produced_on: 2026-05-13
nap_input: NAP.M5.3
gate_verdict: STABLE
m5_d_entry_cleared: true
companion_artifact: 06_LEARNING_LAYER/dbn/embedding_refit/stability_report.md
---

# REFIT_GATE v1.0 — LL8 Embedding Refit Gate

## Gate verdict: STABLE — CLEARED

| Field | Value |
|---|---|
| Model | text-multilingual-embedding-002 (768-dim) |
| Signal count | 30 Type A production signals |
| Signal ID source | ll1_weights_promoted_v1_0.json signal_weights keys |
| Corpus source | msr_signals Postgres table (claim_text + classical_basis) |
| Runs executed | 3 (run_01, run_02, run_03) |
| Run date | 2026-05-13 |
| §4.1 Hash stability | **PASS** — all 30 hashes identical across 3 runs |
| §4.2 Top-1 pass rate (≥27/30) | **PASS** — 30/30 each run [30, 30, 30] |
| §4.2 Top-1 consistency | **PASS** — top-1 choices identical across all 3 runs |
| §4.3 Matrix delta (<0.01) | **PASS** — max delta = 0.00000000 (perfectly deterministic) |
| **Overall** | **STABLE** |

---

## M5-D entry decision

The LL8 embedding refit stability gate is **CLEARED**. CPT Bayesian fitting
(CF.M5C.2) may proceed.

The 30 Type A production signal embeddings under `text-multilingual-embedding-002`
are perfectly deterministic and retrieval-coherent across 3 independent runs.
No remediation required before M5-D CPT fitting begins.

The §4.3 matrix delta of exactly 0.0 across all three run-pairs confirms that
Vertex AI `text-multilingual-embedding-002` is fully deterministic for identical
text inputs — the embedding space is stable and will not introduce noise into
CPT edge weight estimation.

---

## Signal-level audit summary

- Signals with top-1 FAIL (any run): **None**
- Signals with hash variance: **None**
- All 30 signals self-retrieved as top-1 in all 3 runs

---

## Procedure correction log

Three bugs in the refit scaffold were identified and corrected during M5-D-S1
before the gate-qualifying run. The gate result reflects the corrected procedure.
See `stability_report.md §Implementation notes` for full details.

The bugs were in the test procedure (methodology + code), not in the embeddings
or the underlying corpus. The UNSTABLE result from the initial run was not a
signal quality finding.

---

## NAP.M5.3 note

This artifact is the primary input to NAP.M5.3 (confidence-interval reporting
policy for the DBN). The gate being CLEARED with perfect scores indicates the
embedding substrate is sound and CPT posterior distributions can be computed
with confidence that the retrieval layer is stable.

---

*End of REFIT_GATE_v1_0.md v1.0 — M5-D-S1, 2026-05-13*
*Gate status: CLEARED. CF.M5C.1 COMPLETE. M5-D CPT fitting unblocked.*
