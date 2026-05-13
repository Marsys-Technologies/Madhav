---
artifact: refit_procedure.md
version: "1.0"
status: SCAFFOLD
phase: M5-C
sub_phase: M5-C-S1
authored_at: 2026-05-13
parent_spec: LL8_EMBEDDING_REFIT_SPEC_v1_0.md
---

# LL8 Embedding Refit — 3-Run Stability Test Procedure

This document is the operational companion to `LL8_EMBEDDING_REFIT_SPEC_v1_0.md`. It contains
the step-by-step procedure for executing the 3 refit runs and the implementation stub for the
refit script. Execute this procedure at M5-D open before any Bayesian fitting begins.

---

## Pre-run checklist

Before starting Run 01, verify all of the following:

- [ ] PRIOR_SPEC_v1_0.md has `nap_gate_status: APPROVED` (NAP.M5.2 cleared)
- [ ] `ll1_weights_promoted_v1_0.json` is unchanged from M5-B-S2 commit fingerprint
- [ ] Vertex AI auth: `gcloud auth application-default login` completed
- [ ] GCS access: `gsutil ls gs://amjis-corpus/L1/` returns ≥ 30 objects
- [ ] `natal_to_domain.json` accessible at `06_LEARNING_LAYER/dbn/cpt/natal_to_domain.json`
- [ ] Python env: `google-cloud-aiplatform`, `numpy`, `google-cloud-storage` installed
- [ ] `run_logs/run_01/`, `run_logs/run_02/`, `run_logs/run_03/` directories exist (create if not)

---

## Run execution (repeat 3×, incrementing run number)

### Phase A — Load signal IDs

```python
import json, hashlib, numpy as np
from pathlib import Path

# Load Type A signal IDs from CPT
with open("06_LEARNING_LAYER/dbn/cpt/natal_to_domain.json") as f:
    natal_cpt = json.load(f)

# Extract unique from_node values (Type A signal IDs)
signal_ids = sorted(set(edge["from_node"] for edge in natal_cpt["edges"]))
assert len(signal_ids) == 30, f"Expected 30 Type A signals, got {len(signal_ids)}"
print(f"Signal IDs loaded: {len(signal_ids)}")
```

### Phase B — Retrieve canonical chunks from GCS

```python
from google.cloud import storage

gcs = storage.Client(project="amjis-jyotish")
bucket = gcs.bucket("amjis-corpus")

chunks = {}  # signal_id → chunk_text
for sid in signal_ids:
    # Primary: L1 prefix
    blob_path = f"L1/{sid}.txt"
    blob = bucket.blob(blob_path)
    if blob.exists():
        chunks[sid] = blob.download_as_text()
    else:
        # Fallback: L2_5 prefix
        blob_path = f"L2_5/{sid}.txt"
        blob = bucket.blob(blob_path)
        if blob.exists():
            chunks[sid] = blob.download_as_text()
        else:
            raise RuntimeError(f"No chunk found for signal {sid} in L1 or L2_5")

print(f"Chunks loaded: {len(chunks)}")
```

**Note:** If GCS chunks are not keyed by signal ID but by chunk_id, adapt the lookup to use the
`msr_sql.ts` retrieval logic equivalently. See `LL8.O2` — confirm GCS corpus structure at M5-D.

### Phase C — Generate embeddings (Vertex AI)

```python
from vertexai.language_models import TextEmbeddingModel
import vertexai

vertexai.init(project="amjis-jyotish", location="us-central1")
embed_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")

embedding_manifest = {}
embedding_vectors = {}

for sid in signal_ids:
    text = chunks[sid]
    # RETRIEVAL_DOCUMENT for corpus chunks
    result = embed_model.get_embeddings([text], task_type="RETRIEVAL_DOCUMENT")
    vec = result[0].values  # 768-dimensional float list
    vec_bytes = np.array(vec, dtype=np.float32).tobytes()
    vec_hash = hashlib.sha256(vec_bytes).hexdigest()
    embedding_manifest[sid] = {
        "chunk_length_chars": len(text),
        "embedding_dims": len(vec),
        "embedding_hash": vec_hash,
    }
    embedding_vectors[sid] = np.array(vec, dtype=np.float32)

print(f"Embeddings generated: {len(embedding_manifest)}")
```

### Phase D — Top-1 retrieval audit

```python
# For each signal, embed its "query form" and find top-1 in the signal embedding space
# Query forms: use the signal ID itself as a natural-language query (canonical form)

top1_audit = {}
all_vecs = np.stack([embedding_vectors[sid] for sid in signal_ids])  # (30, 768)
all_vecs_norm = all_vecs / np.linalg.norm(all_vecs, axis=1, keepdims=True)

for sid in signal_ids:
    query_text = sid.replace("_", " ").lower()  # simple query form; refine if needed
    result = embed_model.get_embeddings([query_text], task_type="RETRIEVAL_QUERY")
    q_vec = np.array(result[0].values, dtype=np.float32)
    q_vec_norm = q_vec / np.linalg.norm(q_vec)
    
    scores = all_vecs_norm @ q_vec_norm  # (30,) cosine similarities
    top1_idx = int(np.argmax(scores))
    top1_sid = signal_ids[top1_idx]
    
    top1_audit[sid] = {
        "top1_signal_id": top1_sid,
        "top1_score": float(scores[top1_idx]),
        "pass": top1_sid == sid,
    }

pass_count = sum(1 for v in top1_audit.values() if v["pass"])
print(f"Top-1 audit pass rate: {pass_count}/30 = {pass_count/30:.2%}")
```

### Phase E — Cosine similarity matrix

```python
# 30×30 inter-signal cosine similarity matrix (RETRIEVAL_DOCUMENT embeddings)
norm_vecs = all_vecs / np.linalg.norm(all_vecs, axis=1, keepdims=True)
cos_matrix = norm_vecs @ norm_vecs.T  # (30, 30)
```

### Phase F — Save run artefacts

```python
RUN = "run_01"  # change to run_02, run_03 for subsequent runs
run_dir = Path(f"06_LEARNING_LAYER/dbn/embedding_refit/run_logs/{RUN}")
run_dir.mkdir(parents=True, exist_ok=True)

with open(run_dir / "embedding_manifest.json", "w") as f:
    json.dump(embedding_manifest, f, indent=2)

with open(run_dir / "top1_retrieval_audit.json", "w") as f:
    json.dump(top1_audit, f, indent=2)

np.save(run_dir / "cosine_similarity_matrix.npy", cos_matrix)
print(f"Run {RUN} artefacts saved to {run_dir}")
```

---

## Post-run stability check (after 3 runs)

```python
import json, numpy as np, hashlib
from pathlib import Path

run_dirs = [
    Path("06_LEARNING_LAYER/dbn/embedding_refit/run_logs/run_01"),
    Path("06_LEARNING_LAYER/dbn/embedding_refit/run_logs/run_02"),
    Path("06_LEARNING_LAYER/dbn/embedding_refit/run_logs/run_03"),
]

manifests = [json.loads((d / "embedding_manifest.json").read_text()) for d in run_dirs]
audits    = [json.loads((d / "top1_retrieval_audit.json").read_text()) for d in run_dirs]
matrices  = [np.load(d / "cosine_similarity_matrix.npy") for d in run_dirs]

# §4.1 — Embedding hash stability
signal_ids = sorted(manifests[0].keys())
hash_stable = all(
    manifests[0][sid]["embedding_hash"] == manifests[1][sid]["embedding_hash"] ==
    manifests[2][sid]["embedding_hash"]
    for sid in signal_ids
)

# §4.2 — Top-1 retrieval consistency
retrieval_stable = all(
    audits[0][sid]["top1_signal_id"] == audits[1][sid]["top1_signal_id"] ==
    audits[2][sid]["top1_signal_id"]
    for sid in signal_ids
)
pass_counts = [sum(1 for v in a.values() if v["pass"]) for a in audits]
audit_pass = all(p >= 27 for p in pass_counts)

# §4.3 — Cosine matrix delta
deltas = [
    np.abs(matrices[i] - matrices[j]).max()
    for i in range(3) for j in range(i+1, 3)
]
matrix_stable = all(d < 0.01 for d in deltas)

verdict = "STABLE" if (hash_stable and retrieval_stable and audit_pass and matrix_stable) else "UNSTABLE"

print(f"§4.1 Hash stability:        {'PASS' if hash_stable else 'FAIL'}")
print(f"§4.2 Retrieval consistency: {'PASS' if retrieval_stable else 'FAIL'}")
print(f"§4.2 Audit pass counts:     {pass_counts} ({'PASS' if audit_pass else 'FAIL'})")
print(f"§4.3 Matrix delta max:      {max(deltas):.6f} ({'PASS' if matrix_stable else 'FAIL'})")
print(f"\nOverall: {verdict}")
```

---

## Output: `stability_report.md` (template — populate at M5-D)

```markdown
---
artifact: stability_report.md
version: "1.0"
status: [PASS|FAIL]
run_date: YYYY-MM-DD
---
# Embedding Refit Stability Report

## Verdict: [STABLE | UNSTABLE]

| Criterion | Run 01 | Run 02 | Run 03 | Status |
|-----------|--------|--------|--------|--------|
| §4.1 Hash stability | [hash excerpt] | [hash excerpt] | [hash excerpt] | [PASS/FAIL] |
| §4.2 Retrieval pass rate | N/30 | N/30 | N/30 | [PASS/FAIL] |
| §4.3 Matrix delta max | — | Δ(01,02)=X | Δ(01,03)=X | [PASS/FAIL] |

## Failures (if any)
[List signal IDs that failed top-1 audit; list matrix delta exceedances]

## Recommendation
[STABLE → proceed to M5-D Bayesian fitting | UNSTABLE → describe remediation]
```

---

*End of refit_procedure.md v1.0 (SCAFFOLD — M5-C-S1 2026-05-13)*
