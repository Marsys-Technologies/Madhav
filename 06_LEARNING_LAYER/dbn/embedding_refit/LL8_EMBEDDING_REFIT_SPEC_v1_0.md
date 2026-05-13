---
artifact: LL8_EMBEDDING_REFIT_SPEC_v1_0.md
canonical_id: LL8_EMBEDDING_REFIT_SPEC
version: "1.0"
status: SCAFFOLD
phase: M5-C
sub_phase: M5-C-S1
authored_by: M5-C-S1
authored_at: 2026-05-13
purpose: >
  Scaffold specification for the signal embedding refit infrastructure needed
  in M5-D. Establishes the stability criterion, refit procedure, and directory
  layout before M5-D fitting begins, so no setup delays occur during fitting.
nap_gate: NAP.M5.2
nap_gate_status: PENDING
exit_criterion: >
  MACRO_PLAN §M5 exit state (b): "signal embeddings stable across 3 refit runs."
  Stability is defined in §4 below.
predecessor_artifacts:
  - 06_LEARNING_LAYER/dbn/DBN_TOPOLOGY_v1_0.md (v1.1, NAP.M5.1 APPROVED)
  - 06_LEARNING_LAYER/dbn/PRIOR_SPEC_v1_0.md (M5-C-S1 DRAFT, NAP.M5.2 PENDING)
  - 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/production/ll1_weights_promoted_v1_0.json
changelog:
  - version: "1.0"
    date: 2026-05-13
    author: M5-C-S1 (Claude, surrogate)
    note: Initial scaffold. Status SCAFFOLD — content stubs complete; implementation deferred to M5-D.
---

# LL8 Signal Embedding Refit Specification v1.0

## §1 Purpose and scope

This document specifies the signal embedding refit infrastructure for the MARSYS-JIS DBN. Signal
embeddings are the numerical representations used by the retrieval layer (LL.1 → LL.5) to map
incoming query text to the 30 Type A natal signal nodes and their associated CPT edges. The DBN's
inference quality depends critically on the stability of these embeddings: if a refit run produces
materially different node-to-embedding mappings, the CPT edge weights (natal→domain) must be
re-evaluated before M5-D posterior inference proceeds.

**What this spec governs:**
- The 30 Type A natal signal nodes (signal IDs from `ll1_weights_promoted_v1_0.json`).
- The embedding vectors used by `platform/src/lib/retrieve/msr_sql.ts` for CPT-edge selection.
- The 3-run stability test that gates M5-D commencement.

**What this spec does NOT govern:**
- The LLM inference step (DeepSeek; governed by `DBN_TOPOLOGY_v1_0.md §8`).
- The CPT numerical values themselves (governed by `PRIOR_SPEC_v1_0.md`).
- The Bayesian update step (M5-D scope).

---

## §2 Context: what "signal embeddings" means in this project

In the current architecture the 30 Type A natal nodes are represented as:

1. **Signal IDs** — string keys in `ll1_weights_promoted_v1_0.json` (e.g., `"SUN_IN_CAPRICORN"`,
   `"MOON_GEMINI_NAKSHATRA_ARDRA"`, etc.), each with a production weight `w_i ∈ [0,1]`.

2. **Text chunks** — the corresponding text in the GCS corpus at layer prefix `L1/` and `L2_5/`,
   retrieved via `msr_sql.ts` using semantic vector search.

3. **Embedding vectors** — the 768-dimensional Vertex AI embeddings (`task_type: RETRIEVAL_QUERY`)
   used to rank chunk relevance.

The "refit" operation is: given the current set of 499 MSR signals (LL.1 production), re-run the
embedding generation for all chunks tagged with Type A signal IDs, verify that the top-1 retrieved
chunk for each signal ID is semantically correct, and compare cosine similarity matrices across runs
to establish stability.

**Note on LL.8 label:** LL.8 is the MACRO_PLAN label for the embedding-refit workstream
(referenced in PHASE_M5_PLAN §3 M5-C item 4). LL.9 is the co-labelled DBN fitting scaffold;
both scaffold together in M5-C per the plan.

---

## §3 Directory layout

```
06_LEARNING_LAYER/dbn/embedding_refit/
├── LL8_EMBEDDING_REFIT_SPEC_v1_0.md       ← this file (scaffold)
├── refit_procedure.md                      ← 3-run stability test procedure (§5 below)
├── run_logs/                               ← populated during M5-D
│   ├── run_01/
│   │   ├── embedding_manifest.json         ← signal_id → embedding_hash
│   │   ├── cosine_similarity_matrix.npy    ← 30×30 cosine sim between signal embeddings
│   │   └── top1_retrieval_audit.json       ← signal_id → {chunk_id, score, pass/fail}
│   ├── run_02/
│   │   └── ... (same structure)
│   └── run_03/
│       └── ... (same structure)
├── stability_report.md                     ← populated after 3 runs (M5-D)
└── REFIT_GATE_v1_0.md                     ← populated at M5-D exit; NAP.M5.3 input
```

**File status at M5-C-S1 close:** `LL8_EMBEDDING_REFIT_SPEC_v1_0.md` and `refit_procedure.md`
are written (SCAFFOLD status). `run_logs/` exists as an empty directory stub. All other files
are populated during M5-D.

---

## §4 Stability criterion (MACRO_PLAN §M5 exit state b)

A set of 3 refit runs is declared **STABLE** if and only if all of the following hold:

### §4.1 Embedding hash stability
For each of the 30 Type A signal IDs `s_i`, the embedding vector hash must be identical across
all 3 runs:

```
∀ i ∈ {1..30}: hash(embed(s_i, run_01)) == hash(embed(s_i, run_02)) == hash(embed(s_i, run_03))
```

This criterion is typically trivially satisfied when the embedding model is deterministic (Vertex AI
`textembedding-gecko@003` with `task_type=RETRIEVAL_DOCUMENT`). If the model is nondeterministic
or has been updated between runs, this criterion fails and the refit is not stable.

### §4.2 Top-1 retrieval consistency
For each signal ID, the top-1 retrieved chunk must be the same across all 3 runs AND must be the
semantically correct chunk (as audited in `top1_retrieval_audit.json`):

```
∀ i: top1_chunk(s_i, run_j) == top1_chunk(s_i, run_k)  for all j ≠ k
pass_rate(top1_retrieval_audit) ≥ 0.90   (i.e., ≥ 27 of 30 signals correct)
```

A signal fails the audit if the top-1 chunk is from a different signal's semantic domain.
Failures below 27/30 require investigation before M5-D can proceed.

### §4.3 Cosine similarity matrix stability
The 30×30 inter-signal cosine similarity matrix `C_j` (computed from the embedding vectors of
all 30 signal IDs) must be stable across runs:

```
max_ij |C_01[i,j] - C_02[i,j]| < 0.01
max_ij |C_01[i,j] - C_03[i,j]| < 0.01
max_ij |C_02[i,j] - C_03[i,j]| < 0.01
```

Threshold 0.01 corresponds to a Frobenius-norm difference of ≤ 0.055 for a 30×30 matrix —
approximately 1% of the dynamic range of cosine similarity.

### §4.4 Stability verdict
If §4.1 + §4.2 + §4.3 all pass → STABLE → M5-D may proceed.
If any criterion fails → UNSTABLE → `REFIT_GATE_v1_0.md` records the failure mode; M5-C-S2 or
a hotfix session investigates before M5-D opens.

---

## §5 Refit procedure (summary — detail in `refit_procedure.md`)

### Step 1 — Environment pre-check
- Confirm Vertex AI auth (Application Default Credentials, project `amjis-jyotish`).
- Confirm GCS corpus at `gs://amjis-corpus/L1/` and `gs://amjis-corpus/L2_5/` is accessible.
- Confirm `ll1_weights_promoted_v1_0.json` is the production file (fingerprint check).
- Confirm embedding model: `textembedding-gecko@003`, `task_type=RETRIEVAL_DOCUMENT`, 768 dims.

### Step 2 — Signal ID inventory
Load the 30 Type A signal IDs from `ll1_weights_promoted_v1_0.json`. These are the signals
with `domain_node` annotations in `DBN_TOPOLOGY_v1_0.md §4 Type A` and `natal_to_domain.json`.
The 30 IDs are fixed; do not add or remove signals between runs.

### Step 3 — Embedding generation (per run)
For each signal ID `s_i`:
1. Retrieve the canonical chunk from GCS (L1 primary; L2_5 as fallback).
2. Embed the chunk text using Vertex AI (`RETRIEVAL_DOCUMENT`).
3. Store the embedding vector and its SHA-256 hash in `run_0N/embedding_manifest.json`.

### Step 4 — Top-1 retrieval audit (per run)
For each signal ID `s_i`:
1. Embed the signal's "query form" text (the natural-language question that should retrieve it).
2. Run cosine similarity against all 30 signal embeddings.
3. Record whether `s_i` itself is the top-1 result (`pass`) or not (`fail`).
4. Store in `run_0N/top1_retrieval_audit.json`.

### Step 5 — Cosine similarity matrix (per run)
Compute the 30×30 cosine similarity matrix over all signal embeddings. Save as
`run_0N/cosine_similarity_matrix.npy` (NumPy binary format).

### Step 6 — Stability check (after 3 runs)
Apply criteria §4.1, §4.2, §4.3. Record results in `stability_report.md`.

### Step 7 — Gate artifact
Author `REFIT_GATE_v1_0.md` with stability verdict, any failures, and recommendation to native.
This is the NAP.M5.3 input artifact.

---

## §6 Type A signal inventory (30 nodes)

The 30 Type A natal nodes are identified in `DBN_TOPOLOGY_v1_0.md §4` and wired in
`natal_to_domain.json`. The authoritative signal IDs are the keys of
`ll1_weights_promoted_v1_0.json`. The embedding refit operates on these 30 IDs.

**[EXTERNAL_COMPUTATION_REQUIRED: enumerate_type_a_signal_ids]**  
At M5-D refit step, read `natal_to_domain.json` and extract all unique `from_node` values —
these are the 30 Type A signal IDs. Do not hard-code the list here; the CPT JSON is authoritative.

---

## §7 Implementation notes for M5-D

### §7.1 Python environment
Recommended libraries: `google-cloud-aiplatform` (Vertex AI), `google-cloud-storage` (GCS),
`numpy` (cosine similarity matrices), `hashlib` (SHA-256 hashing). All are already in the
project's Python dependency set.

### §7.2 Reference implementation stub
The refit script stub lives at `refit_procedure.md §Implementation`. A complete implementation
is NOT authored at M5-C-S1 (scaffold only). The full script is authored in M5-D or M5-C-S2.

### §7.3 Cost estimate
Vertex AI embedding: ~$0.000025 per 1K characters. 30 signals × ~500 chars/chunk × 3 runs =
45K characters → ~$0.001 per full 3-run refit. Negligible.

### §7.4 Determinism note
Vertex AI `textembedding-gecko@003` is deterministic for identical inputs. Therefore §4.1
(hash stability) should pass trivially assuming no model version change between runs. The
meaningful stability checks are §4.2 (top-1 retrieval pass rate) and §4.3 (cosine matrix delta).

---

## §8 Open items

| ID | Item | Owner | Target |
|----|------|-------|--------|
| LL8.O1 | Enumerate 30 Type A IDs from natal_to_domain.json; confirm count | M5-D-S1 | M5-D open |
| LL8.O2 | Confirm GCS corpus is populated with ≥ 30 L1-tagged chunks | M5-D-S1 | M5-D open |
| LL8.O3 | Author full refit.py script | M5-D-S1 | M5-D open |
| LL8.O4 | Execute 3 refit runs | M5-D-S1 | M5-D in-session |
| LL8.O5 | Author REFIT_GATE_v1_0.md with stability verdict | M5-D-S1 | M5-D close |

---

*End of LL8_EMBEDDING_REFIT_SPEC_v1_0.md v1.0 (SCAFFOLD — M5-C-S1 2026-05-13)*
