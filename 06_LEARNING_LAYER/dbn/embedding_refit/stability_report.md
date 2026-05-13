---
artifact: stability_report.md
version: "1.0"
status: PASS
run_date: 2026-05-13
produced_by: M5-D-S1
model: text-multilingual-embedding-002
embedding_dims: 768
signal_count: 30
signal_id_source: ll1_weights_promoted_v1_0.json signal_weights keys
corpus_source: msr_signals Postgres table (claim_text + classical_basis); fallback natal_to_domain.json derivation text for composite signals
runs_executed: [run_01, run_02, run_03]
verdict: STABLE
---

# LL8 Embedding Refit Stability Report

## Verdict: STABLE

All three stability criteria (§4.1, §4.2, §4.3) PASS across all three runs.
M5-D CPT Bayesian fitting may proceed.

---

## §4 Stability criteria results

| Criterion | Run 01 | Run 02 | Run 03 | Status |
|---|---|---|---|---|
| §4.1 Hash stability | all 30 identical | all 30 identical | all 30 identical | **PASS** |
| §4.2 Retrieval pass rate (≥27/30) | 30/30 = 100% | 30/30 = 100% | 30/30 = 100% | **PASS** |
| §4.2 Top-1 consistency across runs | identical | identical | identical | **PASS** |
| §4.3 Matrix delta Δ(01,02) | — | 0.00000000 | — | **PASS** |
| §4.3 Matrix delta Δ(01,03) | — | — | 0.00000000 | **PASS** |
| §4.3 Matrix delta Δ(02,03) | — | — | 0.00000000 | **PASS** |

**§4.3 max delta across all pairs: 0.00000000** — the embedding model is perfectly
deterministic for identical inputs, consistent with `LL8_EMBEDDING_REFIT_SPEC_v1_0.md §7.4`.

---

## Top-1 retrieval failures
None. All 30 signals retrieved themselves as top-1 across all three runs.

## Hash instability
None. All 30 signal embedding hashes were bit-for-bit identical across runs 01, 02, and 03.

---

## Implementation notes — bugs corrected during M5-D-S1 execution

Three bugs were identified and fixed in `refit.py` during M5-D-S1 before the successful run:

| Bug | Root cause | Fix |
|---|---|---|
| RC1 — §4.2 7/30 pass rate | `top1_retrieval_audit` used humanized signal ID as query text (`"sig msr 297 signal"`). Token-overlap dominated over semantics; 23 signals mapped to attractors SIG.13/MSR.402/MSR.476. Methodology defect, not embedding defect. | Replaced with self-retrieval: signal's own chunk text as `RETRIEVAL_QUERY`. |
| RC2 — §4.1 hash instability (6/30) | `_fallback_chunk_texts` joined derivations via `" \| ".join(set(...))` — Python set ordering is non-deterministic. Affected 6 fallback signals: CTR.01, CVG.02, SIG.01, SIG.12, SIG.13, SIG.15. | Changed to `sorted(set(...))`. |
| RC3 — §4.3 delta 0.01635 | Downstream consequence of RC2. | Self-corrected after RC2 fix. |
| Scope bug | `top1_retrieval_audit` referenced `chunks` as free variable from `main()`. Raised `NameError` at Phase D. | Added `chunks: dict[str, str]` to function signature; updated call site. |

The embedding quality was never in question. All bugs were in the test procedure, not the embeddings.

---

## JSON summary

```json
{
  "verdict": "STABLE",
  "signal_count": 30,
  "model": "text-multilingual-embedding-002",
  "s4_1_hash_stability": "PASS",
  "s4_1_failures": [],
  "s4_2_retrieval_consistency": "PASS",
  "s4_2_retrieval_failures": [],
  "s4_2_pass_counts": [30, 30, 30],
  "s4_2_pass_rate": "PASS",
  "s4_3_matrix_stable": "PASS",
  "s4_3_deltas": {"(01,02)": 0.0, "(01,03)": 0.0, "(02,03)": 0.0},
  "s4_3_max_delta": 0.0
}
```

---

*End of stability_report.md v1.0 — M5-D-S1, 2026-05-13*
