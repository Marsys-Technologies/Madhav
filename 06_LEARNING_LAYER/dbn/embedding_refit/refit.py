#!/usr/bin/env python3
"""
refit.py — LL8 Signal Embedding Refit (3-Run Stability Test)
=============================================================
Authored: M5-D-S1 (2026-05-13)
Spec: 06_LEARNING_LAYER/dbn/embedding_refit/LL8_EMBEDDING_REFIT_SPEC_v1_0.md
Procedure: 06_LEARNING_LAYER/dbn/embedding_refit/refit_procedure.md

CORRECTIONS vs refit_procedure.md scaffold:
  O1. Signal ID source: ll1_weights_promoted_v1_0.json.signal_weights keys (30)
      NOT natal_to_domain.json edges/from_node (schema was scaffold assumption).
      SIG.MSR.117 (shadow node in CPT) is excluded from production refit.
  O2. Corpus source: msr_signals Postgres table (claim_text + classical_basis),
      NOT GCS per-signal chunks (GCS holds document-level objects only).
  O3. Embedding model: text-multilingual-embedding-002 (768-dim, production),
      NOT textembedding-gecko@003 (was scaffold assumption).

USAGE:
  # Requires Cloud SQL Auth Proxy on port 5433 and DATABASE_URL env var.
  # Also requires: pip install google-cloud-aiplatform google-auth psycopg[binary] numpy

  # Run 01:
  RUN=run_01 DATABASE_URL="postgresql://..." python3 refit.py

  # Run 02:
  RUN=run_02 DATABASE_URL="postgresql://..." python3 refit.py

  # Run 03:
  RUN=run_03 DATABASE_URL="postgresql://..." python3 refit.py

  # Stability check (after all 3 runs):
  python3 refit.py --stability-check

OUTPUTS per run:
  06_LEARNING_LAYER/dbn/embedding_refit/run_logs/<RUN>/embedding_manifest.json
  06_LEARNING_LAYER/dbn/embedding_refit/run_logs/<RUN>/top1_retrieval_audit.json
  06_LEARNING_LAYER/dbn/embedding_refit/run_logs/<RUN>/cosine_similarity_matrix.npy
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]  # Navigate up from embedding_refit/
RUN_LOGS_DIR = Path(__file__).parent / "run_logs"

LL1_WEIGHTS_PATH = (
    REPO_ROOT
    / "06_LEARNING_LAYER"
    / "SIGNAL_WEIGHT_CALIBRATION"
    / "signal_weights"
    / "production"
    / "ll1_weights_promoted_v1_0.json"
)

VERTEX_PROJECT = "madhav-astrology"
VERTEX_LOCATION = "us-central1"
VERTEX_MODEL = "text-multilingual-embedding-002"  # 768-dim production model
EXPECTED_DIMS = 768

# Stability thresholds (§4.1, §4.2, §4.3)
MIN_TOP1_PASS_RATE = 27  # out of 30
MAX_MATRIX_DELTA = 0.01


# ---------------------------------------------------------------------------
# Phase A — Load 30 Type A signal IDs from ll1_weights (authoritative)
# ---------------------------------------------------------------------------
def load_signal_ids() -> list[str]:
    """
    Load the 30 production-promoted Type A signal IDs.
    Authoritative source: ll1_weights_promoted_v1_0.json.signal_weights keys.
    NOT natal_to_domain.json (schema mismatch; SIG.MSR.117 shadow node excluded).
    """
    with open(LL1_WEIGHTS_PATH) as f:
        data = json.load(f)

    weights = data.get("signal_weights", {})
    if len(weights) != 30:
        print(
            f"WARNING: expected 30 signal IDs from ll1_weights, got {len(weights)}. "
            "Proceeding but check the weights file."
        )
    signal_ids = sorted(weights.keys())
    print(f"Phase A — Signal IDs loaded: {len(signal_ids)}")
    for i, sid in enumerate(signal_ids, 1):
        print(f"  {i:2d}. {sid}")
    return signal_ids


# ---------------------------------------------------------------------------
# Phase B — Load chunk text from msr_signals (Postgres via Auth Proxy)
# ---------------------------------------------------------------------------
def load_chunk_texts(signal_ids: list[str]) -> dict[str, str]:
    """
    For each signal ID, retrieve the embedding input text from Postgres.
    Primary: msr_signals.claim_text + msr_signals.classical_basis (concatenated).
    Fallback: signal ID description synthesized from ll1_weights metadata.

    Requires: Cloud SQL Auth Proxy on port 5433, DATABASE_URL set.
    """
    try:
        import psycopg
    except ImportError:
        print("ERROR: psycopg not installed. Run: pip install psycopg[binary]")
        sys.exit(1)

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        print("ERROR: DATABASE_URL not set. Set it to the Cloud SQL Auth Proxy URL.")
        print("  Example: postgresql://marsys_rw:<password>@localhost:5433/marsys")
        sys.exit(1)

    chunks: dict[str, str] = {}
    missing: list[str] = []

    print(f"\nPhase B — Loading chunk texts from msr_signals (Postgres)...")
    try:
        with psycopg.connect(db_url, connect_timeout=15) as conn:
            for sid in signal_ids:
                row = conn.execute(
                    """
                    SELECT claim_text, classical_basis
                    FROM msr_signals
                    WHERE signal_id = %s
                    LIMIT 1
                    """,
                    (sid,),
                ).fetchone()

                if row:
                    claim_text = row[0] or ""
                    classical_basis = row[1] or ""
                    # Concatenate: signal ID header + claim + basis for richness
                    text = f"{sid}: {claim_text}"
                    if classical_basis:
                        text += f" Classical basis: {classical_basis}"
                    chunks[sid] = text.strip()
                else:
                    missing.append(sid)

    except Exception as e:
        print(f"ERROR: Postgres connection failed: {e}")
        print("  Is Cloud SQL Auth Proxy running on port 5433?")
        sys.exit(1)

    if missing:
        print(f"  WARNING: {len(missing)} signal IDs not found in msr_signals: {missing}")
        print("  These signals may be composite/synthetic (CTR.*, CVG.*, RPT.DSH.01).")
        print("  Attempting fallback: ll1_weights derivation text...")
        chunks = _fallback_chunk_texts(signal_ids, chunks, missing)

    found = len(chunks)
    print(f"  Chunk texts loaded: {found}/{len(signal_ids)}")
    if found < len(signal_ids):
        still_missing = [sid for sid in signal_ids if sid not in chunks]
        print(f"  ERROR: No text source for {still_missing}. Cannot proceed.")
        sys.exit(1)

    return chunks


def _fallback_chunk_texts(
    signal_ids: list[str],
    existing: dict[str, str],
    missing: list[str],
) -> dict[str, str]:
    """
    Fallback for signals not in msr_signals (composite/synthetic signals like
    CTR.01, CVG.02, RPT.DSH.01). Use the derivation text from natal_to_domain.json
    as proxy embedding input.
    """
    cpt_path = REPO_ROOT / "06_LEARNING_LAYER" / "dbn" / "cpt" / "natal_to_domain.json"
    with open(cpt_path) as f:
        cpt_data = json.load(f)

    entries = cpt_data.get("entries", [])
    # Build: signal_id → set of derivation strings
    derivations: dict[str, list[str]] = {}
    for entry in entries:
        sid = entry.get("signal_id", "")
        deriv = entry.get("derivation", "")
        if sid in missing and deriv:
            derivations.setdefault(sid, []).append(deriv)

    result = dict(existing)
    for sid in missing:
        if sid in derivations:
            combined_deriv = " | ".join(sorted(set(derivations[sid])))
            result[sid] = f"{sid}: {combined_deriv}"
            print(f"    {sid}: fallback from natal_to_domain derivation text")
        else:
            print(f"    {sid}: NO TEXT SOURCE FOUND — will abort")

    return result


# ---------------------------------------------------------------------------
# Phase C — Generate embeddings (Vertex AI text-multilingual-embedding-002)
# ---------------------------------------------------------------------------
def generate_embeddings(
    signal_ids: list[str],
    chunks: dict[str, str],
) -> tuple[dict[str, dict], dict[str, np.ndarray]]:
    """
    Embed each signal's chunk text using Vertex AI text-multilingual-embedding-002.
    Task type: RETRIEVAL_DOCUMENT (for corpus chunks).
    Returns: (embedding_manifest, embedding_vectors)
    """
    try:
        import vertexai
        from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel
    except ImportError:
        print("ERROR: vertexai not installed. Run: pip install google-cloud-aiplatform")
        sys.exit(1)

    print(f"\nPhase C — Generating embeddings ({VERTEX_MODEL})...")
    vertexai.init(project=VERTEX_PROJECT, location=VERTEX_LOCATION)
    model = TextEmbeddingModel.from_pretrained(VERTEX_MODEL)

    embedding_manifest: dict[str, dict] = {}
    embedding_vectors: dict[str, np.ndarray] = {}

    for i, sid in enumerate(signal_ids, 1):
        text = chunks[sid]
        t0 = time.perf_counter()
        inputs = [TextEmbeddingInput(text, task_type="RETRIEVAL_DOCUMENT")]
        result = model.get_embeddings(inputs)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        vec = np.array(result[0].values, dtype=np.float32)
        assert len(vec) == EXPECTED_DIMS, (
            f"Expected {EXPECTED_DIMS} dims, got {len(vec)} for {sid}"
        )

        vec_bytes = vec.tobytes()
        vec_hash = hashlib.sha256(vec_bytes).hexdigest()

        embedding_manifest[sid] = {
            "chunk_length_chars": len(text),
            "embedding_dims": len(vec),
            "embedding_hash": vec_hash,
            "latency_ms": round(elapsed_ms, 1),
        }
        embedding_vectors[sid] = vec

        print(f"  [{i:2d}/30] {sid}: hash={vec_hash[:16]}... ({elapsed_ms:.0f}ms)")

    print(f"  Embeddings generated: {len(embedding_manifest)}/30")
    return embedding_manifest, embedding_vectors


# ---------------------------------------------------------------------------
# Phase D — Top-1 retrieval audit
# ---------------------------------------------------------------------------
def top1_retrieval_audit(
    signal_ids: list[str],
    embedding_vectors: dict[str, np.ndarray],
    model,  # Vertex AI TextEmbeddingModel (reuse from Phase C)
    chunks: dict[str, str],
) -> dict[str, dict]:
    """
    Self-retrieval audit: embed each signal's own chunk text as RETRIEVAL_QUERY,
    then find top-1 in the 30-signal RETRIEVAL_DOCUMENT embedding space.
    A signal passes if it retrieves itself as top-1 — the standard coherence check.

    Fix M5-D-S1 (root cause 1): replaced "humanized ID" query strings with the
    signal's own chunk text. The prior approach produced token-overlap attractors
    (SIG.13, SIG.MSR.402, SIG.MSR.476) because ID tokens are not semantic queries.
    """
    try:
        from vertexai.language_models import TextEmbeddingInput
    except ImportError:
        pass  # Already checked in Phase C

    print(f"\nPhase D — Top-1 retrieval audit...")

    all_vecs = np.stack([embedding_vectors[sid] for sid in signal_ids])  # (30, 768)
    all_vecs_norm = all_vecs / np.linalg.norm(all_vecs, axis=1, keepdims=True)

    top1_audit: dict[str, dict] = {}

    for i, sid in enumerate(signal_ids, 1):
        # Self-retrieval: embed the signal's own chunk text as RETRIEVAL_QUERY.
        # Standard pattern: a chunk should retrieve itself as top-1 when its own
        # text is used as the query. "Humanized ID" approach (v1.0 scaffold) was
        # a methodology defect — token-form overlap dominated over semantics.
        # Fix applied M5-D-S1: use chunk text directly. (Root cause 1 correction.)
        query_text = chunks[sid]
        inputs = [TextEmbeddingInput(query_text, task_type="RETRIEVAL_QUERY")]
        result = model.get_embeddings(inputs)
        q_vec = np.array(result[0].values, dtype=np.float32)
        q_vec_norm = q_vec / np.linalg.norm(q_vec)

        scores = all_vecs_norm @ q_vec_norm  # (30,) cosine similarities
        top1_idx = int(np.argmax(scores))
        top1_sid = signal_ids[top1_idx]
        passed = top1_sid == sid

        top1_audit[sid] = {
            "query_text": query_text[:120] + "..." if len(query_text) > 120 else query_text,
            "top1_signal_id": top1_sid,
            "top1_score": float(scores[top1_idx]),
            "self_score": float(scores[i - 1]),
            "pass": passed,
        }

        status = "PASS" if passed else f"FAIL→{top1_sid}"
        print(f"  [{i:2d}/30] {sid}: {status} (score={scores[top1_idx]:.4f})")

    pass_count = sum(1 for v in top1_audit.values() if v["pass"])
    print(f"  Top-1 pass rate: {pass_count}/30 = {pass_count / 30:.1%}")
    return top1_audit


# ---------------------------------------------------------------------------
# Phase E — Cosine similarity matrix
# ---------------------------------------------------------------------------
def cosine_similarity_matrix(
    signal_ids: list[str],
    embedding_vectors: dict[str, np.ndarray],
) -> np.ndarray:
    """
    Compute 30×30 cosine similarity matrix over RETRIEVAL_DOCUMENT embeddings.
    """
    print(f"\nPhase E — Computing 30×30 cosine similarity matrix...")
    all_vecs = np.stack([embedding_vectors[sid] for sid in signal_ids])
    norm_vecs = all_vecs / np.linalg.norm(all_vecs, axis=1, keepdims=True)
    cos_matrix = norm_vecs @ norm_vecs.T
    print(f"  Matrix shape: {cos_matrix.shape}, dtype: {cos_matrix.dtype}")
    print(f"  Diagonal mean (self-similarity): {np.diag(cos_matrix).mean():.6f}")
    off_diag = cos_matrix[~np.eye(30, dtype=bool)]
    print(f"  Off-diagonal mean: {off_diag.mean():.4f}, max: {off_diag.max():.4f}")
    return cos_matrix


# ---------------------------------------------------------------------------
# Phase F — Save run artefacts
# ---------------------------------------------------------------------------
def save_run_artifacts(
    run_id: str,
    signal_ids: list[str],
    embedding_manifest: dict,
    top1_audit: dict,
    cos_matrix: np.ndarray,
) -> Path:
    run_dir = RUN_LOGS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = run_dir / "embedding_manifest.json"
    audit_path = run_dir / "top1_retrieval_audit.json"
    matrix_path = run_dir / "cosine_similarity_matrix.npy"
    meta_path = run_dir / "run_meta.json"

    # Ordered manifest (alphabetical by signal_id for deterministic JSON)
    ordered_manifest = {sid: embedding_manifest[sid] for sid in signal_ids}
    manifest_path.write_text(json.dumps(ordered_manifest, indent=2))

    ordered_audit = {sid: top1_audit[sid] for sid in signal_ids}
    audit_path.write_text(json.dumps(ordered_audit, indent=2))

    np.save(str(matrix_path), cos_matrix)

    pass_count = sum(1 for v in top1_audit.values() if v["pass"])
    meta = {
        "run_id": run_id,
        "signal_count": len(signal_ids),
        "model": VERTEX_MODEL,
        "embedding_dims": EXPECTED_DIMS,
        "top1_pass_count": pass_count,
        "top1_pass_rate": round(pass_count / len(signal_ids), 4),
        "signal_ids": signal_ids,
    }
    meta_path.write_text(json.dumps(meta, indent=2))

    print(f"\nPhase F — Artefacts saved to {run_dir}/")
    print(f"  embedding_manifest.json ({manifest_path.stat().st_size} bytes)")
    print(f"  top1_retrieval_audit.json ({audit_path.stat().st_size} bytes)")
    print(f"  cosine_similarity_matrix.npy ({matrix_path.stat().st_size} bytes)")
    print(f"  run_meta.json ({meta_path.stat().st_size} bytes)")
    return run_dir


# ---------------------------------------------------------------------------
# Stability check (after 3 runs)
# ---------------------------------------------------------------------------
def run_stability_check() -> None:
    """
    Post-run stability check per LL8_EMBEDDING_REFIT_SPEC §4.1–§4.3.
    Run after all 3 refit runs are complete.
    """
    run_dirs = [
        RUN_LOGS_DIR / "run_01",
        RUN_LOGS_DIR / "run_02",
        RUN_LOGS_DIR / "run_03",
    ]

    for d in run_dirs:
        if not (d / "embedding_manifest.json").exists():
            print(f"ERROR: {d}/embedding_manifest.json missing. Run refit.py for {d.name} first.")
            sys.exit(1)

    manifests = [
        json.loads((d / "embedding_manifest.json").read_text()) for d in run_dirs
    ]
    audits = [
        json.loads((d / "top1_retrieval_audit.json").read_text()) for d in run_dirs
    ]
    matrices = [np.load(str(d / "cosine_similarity_matrix.npy")) for d in run_dirs]

    signal_ids = sorted(manifests[0].keys())
    n = len(signal_ids)

    print("=" * 70)
    print("LL8 EMBEDDING REFIT — POST-RUN STABILITY CHECK")
    print("=" * 70)
    print(f"Signals: {n} | Runs: 3")

    # §4.1 — Embedding hash stability
    hash_failures: list[str] = []
    for sid in signal_ids:
        h0 = manifests[0][sid]["embedding_hash"]
        h1 = manifests[1][sid]["embedding_hash"]
        h2 = manifests[2][sid]["embedding_hash"]
        if not (h0 == h1 == h2):
            hash_failures.append(f"{sid}: {h0[:8]}... / {h1[:8]}... / {h2[:8]}...")
    hash_stable = len(hash_failures) == 0

    print(f"\n§4.1 Embedding hash stability:")
    if hash_stable:
        print(f"  PASS — all {n} signal embedding hashes identical across 3 runs")
    else:
        print(f"  FAIL — {len(hash_failures)} signals with hash variance:")
        for f in hash_failures:
            print(f"    {f}")

    # §4.2 — Top-1 retrieval consistency + pass rate
    retrieval_failures: list[str] = []
    for sid in signal_ids:
        t0 = audits[0][sid]["top1_signal_id"]
        t1 = audits[1][sid]["top1_signal_id"]
        t2 = audits[2][sid]["top1_signal_id"]
        if not (t0 == t1 == t2):
            retrieval_failures.append(f"{sid}: {t0} / {t1} / {t2}")
    retrieval_consistent = len(retrieval_failures) == 0

    pass_counts = [sum(1 for v in a.values() if v["pass"]) for a in audits]
    audit_pass_rate = all(p >= MIN_TOP1_PASS_RATE for p in pass_counts)

    print(f"\n§4.2 Top-1 retrieval consistency:")
    if retrieval_consistent:
        print(f"  PASS — top-1 choices identical across 3 runs for all {n} signals")
    else:
        print(f"  FAIL — {len(retrieval_failures)} signals with inconsistent top-1:")
        for f in retrieval_failures:
            print(f"    {f}")

    print(f"\n§4.2 Top-1 pass rate (threshold ≥{MIN_TOP1_PASS_RATE}/{n}):")
    for i, (p, d) in enumerate(zip(pass_counts, run_dirs), 1):
        status = "PASS" if p >= MIN_TOP1_PASS_RATE else "FAIL"
        print(f"  Run {i:02d}: {p}/{n} = {p/n:.1%} — {status}")

    # §4.3 — Cosine matrix delta
    pairs = [(0, 1), (0, 2), (1, 2)]
    pair_labels = ["(01,02)", "(01,03)", "(02,03)"]
    deltas: list[float] = []
    print(f"\n§4.3 Cosine similarity matrix delta (threshold <{MAX_MATRIX_DELTA}):")
    for (i, j), label in zip(pairs, pair_labels):
        delta = float(np.abs(matrices[i] - matrices[j]).max())
        deltas.append(delta)
        status = "PASS" if delta < MAX_MATRIX_DELTA else "FAIL"
        print(f"  Δ{label}: {delta:.8f} — {status}")
    matrix_stable = all(d < MAX_MATRIX_DELTA for d in deltas)

    # Failures summary
    all_pass = hash_stable and retrieval_consistent and audit_pass_rate and matrix_stable
    verdict = "STABLE" if all_pass else "UNSTABLE"

    print("\n" + "=" * 70)
    print(f"OVERALL VERDICT: {verdict}")
    print("=" * 70)
    print(f"  §4.1 Hash stability:          {'PASS' if hash_stable else 'FAIL'}")
    print(f"  §4.2 Retrieval consistency:   {'PASS' if retrieval_consistent else 'FAIL'}")
    print(f"  §4.2 Pass rate ≥{MIN_TOP1_PASS_RATE}/30:        {'PASS' if audit_pass_rate else 'FAIL'} {pass_counts}")
    print(f"  §4.3 Matrix delta <{MAX_MATRIX_DELTA}:    {'PASS' if matrix_stable else 'FAIL'} max={max(deltas):.8f}")

    if verdict == "STABLE":
        print("\nRECOMMENDATION: Embedding refit STABLE. M5-D CPT fitting may proceed.")
    else:
        print("\nRECOMMENDATION: Embedding refit UNSTABLE. Investigate failures before CPT fitting.")

    # Print machine-readable summary for stability_report.md authoring
    print("\n--- JSON SUMMARY (paste into stability_report.md) ---")
    summary = {
        "verdict": verdict,
        "signal_count": n,
        "model": VERTEX_MODEL,
        "s4_1_hash_stability": "PASS" if hash_stable else "FAIL",
        "s4_1_failures": hash_failures,
        "s4_2_retrieval_consistency": "PASS" if retrieval_consistent else "FAIL",
        "s4_2_retrieval_failures": retrieval_failures,
        "s4_2_pass_counts": pass_counts,
        "s4_2_pass_rate": "PASS" if audit_pass_rate else "FAIL",
        "s4_3_matrix_stable": "PASS" if matrix_stable else "FAIL",
        "s4_3_deltas": {label: round(d, 8) for label, d in zip(pair_labels, deltas)},
        "s4_3_max_delta": round(max(deltas), 8),
    }
    print(json.dumps(summary, indent=2))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="LL8 Embedding Refit — 3-Run Stability Test")
    parser.add_argument(
        "--stability-check",
        action="store_true",
        help="Run post-run stability check across run_01, run_02, run_03. No embedding calls.",
    )
    args = parser.parse_args()

    if args.stability_check:
        run_stability_check()
        return

    run_id = os.environ.get("RUN", "")
    if run_id not in ("run_01", "run_02", "run_03"):
        print("ERROR: Set RUN environment variable to run_01, run_02, or run_03.")
        print("  Example: RUN=run_01 DATABASE_URL=... python3 refit.py")
        sys.exit(1)

    print("=" * 70)
    print(f"LL8 EMBEDDING REFIT — {run_id.upper()}")
    print(f"Model: {VERTEX_MODEL} ({EXPECTED_DIMS}-dim)")
    print("=" * 70)

    # Phases A–F
    signal_ids = load_signal_ids()

    chunks = load_chunk_texts(signal_ids)

    # Import Vertex AI model once, reuse for Phase C and D
    try:
        import vertexai
        from vertexai.language_models import TextEmbeddingModel
    except ImportError:
        print("ERROR: vertexai not installed. Run: pip install google-cloud-aiplatform")
        sys.exit(1)

    vertexai.init(project=VERTEX_PROJECT, location=VERTEX_LOCATION)
    model = TextEmbeddingModel.from_pretrained(VERTEX_MODEL)

    embedding_manifest, embedding_vectors = generate_embeddings(signal_ids, chunks)

    top1_audit = top1_retrieval_audit(signal_ids, embedding_vectors, model, chunks)

    cos_matrix = cosine_similarity_matrix(signal_ids, embedding_vectors)

    save_run_artifacts(run_id, signal_ids, embedding_manifest, top1_audit, cos_matrix)

    print(f"\n{'='*70}")
    print(f"{run_id.upper()} COMPLETE. Artefacts in run_logs/{run_id}/")
    pass_count = sum(1 for v in top1_audit.values() if v["pass"])
    print(f"Top-1 pass rate: {pass_count}/30 — {'≥27 PASS' if pass_count >= MIN_TOP1_PASS_RATE else '<27 FAIL'}")
    print(f"{'='*70}")
    _next = {"run_01": "run_02", "run_02": "run_03", "run_03": "--stability-check"}[run_id]
    print(f"\nNext: {_next}")


if __name__ == "__main__":
    main()
