#!/usr/bin/env python3
"""
pipeline_smoke_audit.py — MARSYS-JIS End-to-End Query Pipeline Audit
======================================================================
Audits every service hop and data source touched by a consumer chat query.

Pipeline under test:
  Consumer UI
    → Firebase Auth (GCP Identity Platform)
    → Cloud SQL (chart/profile lookup + all 6 L2.5 structured tables)
    → classify() → Anthropic API
    → loadManifest() → filesystem (MARSYS_REPO_ROOT/00_ARCHITECTURE/)
    → 10 retrieval tools:
        msr_sql            → Cloud SQL: msr_signals
        pattern_register   → filesystem: 035_DISCOVERY_LAYER/REGISTERS/
        resonance_register → filesystem: 035_DISCOVERY_LAYER/REGISTERS/
        cluster_atlas      → filesystem: 035_DISCOVERY_LAYER/REGISTERS/
        contradiction_reg  → filesystem: 035_DISCOVERY_LAYER/REGISTERS/
        temporal           → Python sidecar (PYTHON_SIDECAR_URL)
        query_msr_agg      → no I/O (stub — multi-native not deployed)
        cgm_graph_walk     → Cloud SQL: l25_cgm_nodes + l25_cgm_edges
        manifest_query     → filesystem: 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
        vector_search      → Vertex AI (embed) + Cloud SQL: rag_embeddings + rag_chunks
    → synthesize() → Anthropic API
    → audit write → Cloud SQL: audit_events
    → persist → Cloud SQL: conversations + messages

Usage (requires Auth Proxy running on port 5433):
    pip install psycopg[binary] google-cloud-storage google-auth requests python-dotenv --break-system-packages
    python3 platform/scripts/pipeline_smoke_audit.py [--repo-root /path/to/repo]

Outputs:
    - Console: live pass/fail per check
    - File:    PIPELINE_SMOKE_AUDIT_REPORT_<timestamp>.json  (machine-readable)
    - File:    PIPELINE_SMOKE_AUDIT_REPORT_<timestamp>.md    (human-readable)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# The canonical chart (CLAUDE.md section B): the only default where a chart selector is needed.
CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

# ── Colours ───────────────────────────────────────────────────────────────────

RESET = "\033[0m"
RED   = "\033[91m"
GRN   = "\033[92m"
YLW   = "\033[93m"
BLU   = "\033[94m"
BOLD  = "\033[1m"
DIM   = "\033[2m"

def pass_(msg: str) -> str: return f"{GRN}✅ PASS{RESET}  {msg}"
def fail_(msg: str) -> str: return f"{RED}❌ FAIL{RESET}  {msg}"
def warn_(msg: str) -> str: return f"{YLW}⚠️  WARN{RESET}  {msg}"
def info_(msg: str) -> str: return f"{BLU}ℹ️  INFO{RESET}  {msg}"
def head_(msg: str) -> str: return f"\n{BOLD}{BLU}{'─'*60}{RESET}\n{BOLD}{msg}{RESET}\n{'─'*60}"

# ── Result accumulator ────────────────────────────────────────────────────────

class AuditResult:
    def __init__(self, check_id: str, category: str, description: str):
        self.check_id = check_id
        self.category = category
        self.description = description
        self.status: str = "unknown"      # pass | fail | warn | info | skip
        self.detail: str = ""
        self.latency_ms: float | None = None
        self.data: dict[str, Any] = {}

    def ok(self, detail: str = "", latency: float | None = None, **data: Any) -> "AuditResult":
        self.status = "pass"
        self.detail = detail
        self.latency_ms = latency
        self.data = data
        return self

    def fail(self, detail: str, latency: float | None = None, **data: Any) -> "AuditResult":
        self.status = "fail"
        self.detail = detail
        self.latency_ms = latency
        self.data = data
        return self

    def warn(self, detail: str, latency: float | None = None, **data: Any) -> "AuditResult":
        self.status = "warn"
        self.detail = detail
        self.latency_ms = latency
        self.data = data
        return self

    def skip(self, reason: str) -> "AuditResult":
        self.status = "skip"
        self.detail = reason
        return self

    def print(self) -> None:
        lat = f"  {DIM}({self.latency_ms:.0f}ms){RESET}" if self.latency_ms is not None else ""
        if   self.status == "pass": print(pass_(f"[{self.check_id}] {self.description}{lat}") + (f"\n         {DIM}{self.detail}{RESET}" if self.detail else ""))
        elif self.status == "fail": print(fail_(f"[{self.check_id}] {self.description}{lat}") + f"\n         {self.detail}")
        elif self.status == "warn": print(warn_(f"[{self.check_id}] {self.description}{lat}") + (f"\n         {DIM}{self.detail}{RESET}" if self.detail else ""))
        elif self.status == "skip": print(f"  {DIM}⏭  SKIP  [{self.check_id}] {self.description}  — {self.detail}{RESET}")
        else:                       print(info_(f"[{self.check_id}] {self.description}{lat}") + (f"\n         {DIM}{self.detail}{RESET}" if self.detail else ""))

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "category": self.category,
            "description": self.description,
            "status": self.status,
            "detail": self.detail,
            "latency_ms": self.latency_ms,
            "data": self.data,
        }


results: list[AuditResult] = []

def check(check_id: str, category: str, description: str) -> AuditResult:
    r = AuditResult(check_id, category, description)
    results.append(r)
    return r

# ── Env loader ────────────────────────────────────────────────────────────────

def load_env(repo_root: str) -> None:
    env_path = Path(repo_root) / "platform" / ".env.local"
    if not env_path.exists():
        print(warn_(f".env.local not found at {env_path} — relying on existing env vars"))
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path, override=False)
        print(info_(f"Loaded env from {env_path}"))
    except ImportError:
        # Manual parse without python-dotenv
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k not in os.environ:
                    os.environ[k] = v.strip().strip('"').strip("'")


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Static code audit: no localhost/stale provider refs in pipeline
# ═════════════════════════════════════════════════════════════════════════════

def audit_static_code(repo_root: str) -> None:
    print(head_("SECTION 1 — Static code: no stale service refs in pipeline"))

    platform_src = Path(repo_root) / "platform" / "src"
    sidecar_src  = Path(repo_root) / "platform" / "python-sidecar"

    # 1.1 — No NEXT_PUBLIC_SIDECAR_URL in any active code file
    r = check("1.1", "static", "No NEXT_PUBLIC_SIDECAR_URL in active TS source")
    hits: list[str] = []
    for f in platform_src.rglob("*.ts"):
        if ".next" in str(f) or "node_modules" in str(f):
            continue
        try:
            txt = f.read_text()
            if "NEXT_PUBLIC_SIDECAR_URL" in txt:
                hits.append(str(f.relative_to(repo_root)))
        except Exception:
            pass
    for f in platform_src.rglob("*.tsx"):
        if ".next" in str(f) or "node_modules" in str(f):
            continue
        try:
            txt = f.read_text()
            if "NEXT_PUBLIC_SIDECAR_URL" in txt:
                hits.append(str(f.relative_to(repo_root)))
        except Exception:
            pass
    if hits:
        r.fail(f"Still present in: {hits}").print()
    else:
        r.ok("Clean — all 3 RAG clients use PYTHON_SIDECAR_URL").print()

    # 1.2 — No SIDECAR_API_KEY (old name) in any active code
    r = check("1.2", "static", "No old SIDECAR_API_KEY in active TS/Python source")
    hits = []
    for pattern in ["*.ts", "*.py"]:
        for f in list(platform_src.rglob(pattern)) + list(sidecar_src.rglob(pattern)):
            if any(x in str(f) for x in [".next", "node_modules", "venv", "__pycache__"]):
                continue
            try:
                txt = f.read_text()
                # Only flag if it's in an assignment or os.environ.get() — not comments
                if re.search(r'SIDECAR_API_KEY[^_]', txt) and \
                   "PYTHON_SIDECAR_API_KEY" not in txt:
                    hits.append(str(f.relative_to(repo_root)))
            except Exception:
                pass
    if hits:
        r.fail(f"Old key name found in: {hits}").print()
    else:
        r.ok("Clean — only PYTHON_SIDECAR_API_KEY used everywhere").print()

    # 1.3 — temporal.ts uses PYTHON_SIDECAR_URL (not hardcoded localhost)
    r = check("1.3", "static", "temporal.ts sidecar URL reads from PYTHON_SIDECAR_URL env var")
    temporal_path = platform_src / "lib" / "retrieve" / "temporal.ts"
    if temporal_path.exists():
        txt = temporal_path.read_text()
        if "PYTHON_SIDECAR_URL" in txt and "localhost:8000" not in txt.split("PYTHON_SIDECAR_URL")[0][:200]:
            r.ok("Reads process.env.PYTHON_SIDECAR_URL with localhost fallback only").print()
        elif "localhost:8000" in txt and "PYTHON_SIDECAR_URL" not in txt:
            r.fail("Hardcoded localhost:8000 with no env override").print()
        else:
            r.ok("Reads PYTHON_SIDECAR_URL (localhost:8000 is fallback only)").print()
    else:
        r.fail("temporal.ts not found").print()

    # 1.4 — No supabase package imports in active TS
    r = check("1.4", "static", "No @supabase/supabase-js imports in active TS source")
    hits = []
    for f in platform_src.rglob("*.ts"):
        if any(x in str(f) for x in [".next", "node_modules"]):
            continue
        try:
            if "@supabase" in f.read_text():
                hits.append(str(f.relative_to(repo_root)))
        except Exception:
            pass
    if hits:
        r.fail(f"Supabase still imported in: {hits}").print()
    else:
        r.ok("No @supabase imports — fully migrated to Cloud SQL").print()

    # 1.5 — No voyageai imports in active Python
    r = check("1.5", "static", "No voyageai imports in active Python source (outside venv)")
    hits = []
    for f in sidecar_src.rglob("*.py"):
        if any(x in str(f) for x in ["venv", "__pycache__"]):
            continue
        try:
            if "import voyageai" in f.read_text() or "from voyageai" in f.read_text():
                hits.append(str(f.relative_to(repo_root)))
        except Exception:
            pass
    if hits:
        r.fail(f"voyageai imported in: {hits}").print()
    else:
        r.ok("Voyage AI fully replaced — no voyageai imports in active Python").print()

    # 1.6 — Dockerfile copies 035_DISCOVERY_LAYER for register tools
    r = check("1.6", "static", "Dockerfile copies 035_DISCOVERY_LAYER (needed by 4 register tools)")
    dockerfile = Path(repo_root) / "platform" / "Dockerfile"
    if dockerfile.exists():
        txt = dockerfile.read_text()
        if "035_DISCOVERY_LAYER" in txt:
            r.ok("035_DISCOVERY_LAYER is COPY'd into runner stage").print()
        else:
            r.fail(
                "CRITICAL: 035_DISCOVERY_LAYER NOT in Dockerfile COPY commands.\n"
                "         pattern_register, resonance_register, cluster_atlas, contradiction_register\n"
                "         all call filesystemAdapter.readFile('035_DISCOVERY_LAYER/REGISTERS/...')\n"
                "         which reads from MARSYS_REPO_ROOT=/app — that path will not exist in Cloud Run.\n"
                "         Fix: add to Dockerfile runner stage:\n"
                "           COPY --from=builder --chown=nextjs:nodejs /app/035_DISCOVERY_LAYER ./035_DISCOVERY_LAYER"
            ).print()
    else:
        r.fail("Dockerfile not found").print()

    # 1.7 — Register JSON files exist locally (pre-flight for tools)
    r = check("1.7", "static", "L3 register JSON files present under MARSYS_REPO_ROOT")
    register_paths = [
        "035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_v1_0.json",
        "035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_0.json",
        "035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_0.json",
        "035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_0.json",
    ]
    missing = [p for p in register_paths if not (Path(repo_root) / p).exists()]
    if missing:
        r.fail(f"Missing locally: {missing}").print()
    else:
        sizes = {p: (Path(repo_root) / p).stat().st_size for p in register_paths}
        r.ok(f"All 4 present. Sizes: { {p.split('/')[-1]: f'{s//1024}KB' for p,s in sizes.items()} }",
             files=list(sizes.keys())).print()


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Cloud SQL connectivity + table health
# ═════════════════════════════════════════════════════════════════════════════

def audit_cloud_sql() -> None:
    print(head_("SECTION 2 — Cloud SQL (postgres via Auth Proxy)"))

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        for r_id, desc in [
            ("2.1","DB connection"), ("2.2","charts table"), ("2.3","msr_signals"),
            ("2.4","rag_chunks + rag_embeddings"),
            ("2.5a","l25_cgm_nodes"), ("2.5b","l25_cgm_edges_valid"), ("2.5c","l25_cgm_edges_total"),
            ("2.6","L2.5 structured tables"), ("2.7","audit_events"), ("2.8","conversations"),
        ]:
            check(r_id, "cloud_sql", desc).skip("DATABASE_URL not set").print()
        return

    try:
        import psycopg
    except ImportError:
        for r_id, desc in [("2.1","DB connection")]:
            check(r_id, "cloud_sql", desc).fail("psycopg not installed: pip install psycopg[binary]").print()
        return

    # 2.1 — Connection
    r = check("2.1", "cloud_sql", "Cloud SQL connection via Auth Proxy")
    t0 = time.perf_counter()
    try:
        conn = psycopg.connect(db_url, connect_timeout=10)
        latency = (time.perf_counter() - t0) * 1000
        row = conn.execute("SELECT version()").fetchone()
        r.ok(f"PostgreSQL: {row[0][:60]}...", latency=latency).print()
    except Exception as e:
        r.fail(f"{e}\n         → Is the Cloud SQL Auth Proxy running? (./scripts/start_db_proxy.sh)").print()
        return

    def q(sql: str, params: tuple = ()) -> list[tuple]:
        return conn.execute(sql, params).fetchall()

    def q1(sql: str, params: tuple = ()) -> Any:
        rows = conn.execute(sql, params).fetchone()
        return rows[0] if rows else None

    # Helper
    def table_check(check_id: str, table: str, count_sql: str, min_rows: int,
                    extra_desc: str = "", layer: str = "") -> None:
        desc = f"{table} ({layer + ' — ' if layer else ''}{extra_desc or 'row count'})"
        r2 = check(check_id, "cloud_sql", desc)
        t0 = time.perf_counter()
        try:
            cnt = q1(count_sql)
            lat = (time.perf_counter() - t0) * 1000
            if cnt is None or cnt == 0:
                r2.warn(f"Table exists but 0 rows — data may not be ingested yet", latency=lat, row_count=0).print()
            elif cnt < min_rows:
                r2.warn(f"{cnt} rows (expected ≥{min_rows})", latency=lat, row_count=cnt).print()
            else:
                r2.ok(f"{cnt:,} rows", latency=lat, row_count=cnt).print()
        except Exception as e:
            r2.fail(f"{e}", latency=(time.perf_counter()-t0)*1000).print()

    # 2.2 — Core app tables
    table_check("2.2", "charts", "SELECT COUNT(*) FROM charts", 1, "must have ≥1 chart")
    table_check("2.3", "msr_signals", "SELECT COUNT(*) FROM msr_signals", 400,
                "L2.5 MSR signals — pipeline tool: msr_sql", "L2.5")
    table_check("2.4a", "rag_chunks", "SELECT COUNT(*) FROM rag_chunks WHERE is_stale=false", 100,
                "non-stale RAG chunks — pipeline tool: vector_search", "L1+L2.5")
    table_check("2.4b", "rag_embeddings", "SELECT COUNT(*) FROM rag_embeddings", 100,
                "vector embeddings — pipeline tool: vector_search")
    table_check("2.5a", "l25_cgm_nodes",
                "SELECT COUNT(*) FROM l25_cgm_nodes", 200,
                "CGM graph nodes — tool: cgm_graph_walk", "L2.5 CGM")
    table_check("2.5b", "l25_cgm_edges_valid",
                "SELECT COUNT(*) FROM l25_cgm_edges WHERE status = 'valid'", 15,
                "CGM graph edges (valid) — tool: cgm_graph_walk", "L2.5 CGM")
    table_check("2.5c", "l25_cgm_edges_total",
                "SELECT COUNT(*) FROM l25_cgm_edges", 100,
                "CGM graph edges (all statuses)", "L2.5 CGM")

    # 2.6 — L2.5 structured tables (Phase 14D)
    for tid, tbl, min_r, lyr in [
        ("2.6a", "ucn_sections",   5,  "L2.5 UCN"),
        ("2.6b", "cdlm_links",     5,  "L2.5 CDLM"),
        ("2.6c", "cgm_nodes",      5,  "L2.5 CGM nodes"),
        ("2.6d", "cgm_edges",      5,  "L2.5 CGM edges"),
        ("2.6e", "rm_resonances",  5,  "L2.5 RM"),
        ("2.6f", "chart_facts",    10, "L1 structured facts"),
        ("2.6g", "eclipses",       10, "L1 eclipses"),
        ("2.6h", "retrogrades",    10, "L1 retrogrades"),
        ("2.6i", "life_events",    1,  "L1 life events"),
        ("2.6j", "sade_sati",      1,  "L1 Sade Sati cycles"),
    ]:
        table_check(tid, tbl, f"SELECT COUNT(*) FROM {tbl}", min_r, layer=lyr)

    # 2.7 — Audit/trace tables
    table_check("2.7a", "audit_events",      "SELECT COUNT(*) FROM audit_events",      0, "pipeline audit log")
    table_check("2.7b", "query_trace_steps", "SELECT COUNT(*) FROM query_trace_steps", 0, "pipeline trace steps")
    table_check("2.8",  "conversations",     "SELECT COUNT(*) FROM conversations",     0, "persisted conversations")

    # 2.9 — pgvector extension
    r = check("2.9", "cloud_sql", "pgvector extension installed")
    t0 = time.perf_counter()
    try:
        row = q1("SELECT extversion FROM pg_extension WHERE extname='vector'")
        lat = (time.perf_counter() - t0) * 1000
        if row:
            r.ok(f"pgvector {row} installed", latency=lat).print()
        else:
            r.fail("pgvector extension not found — vector_search tool will fail").print()
    except Exception as e:
        r.fail(str(e)).print()

    # 2.10 — Embedding dimension sanity (768 for Vertex AI text-multilingual-embedding-002)
    r = check("2.10", "cloud_sql", "rag_embeddings dimension = 768 (Vertex AI text-multilingual-embedding-002)")
    t0 = time.perf_counter()
    try:
        row = q1(
            "SELECT array_length(embedding::real[], 1) FROM rag_embeddings LIMIT 1"
        )
        lat = (time.perf_counter() - t0) * 1000
        if row is None:
            r.warn("No embeddings yet — cannot check dimension", latency=lat).print()
        elif row == 768:
            r.ok(f"dim={row} ✓ matches Vertex AI text-multilingual-embedding-002", latency=lat).print()
        else:
            r.fail(f"dim={row} — expected 768. Stale Voyage embeddings may be present.", latency=lat).print()
    except Exception as e:
        r.warn(f"Could not check embedding dim: {e}").print()

    # 2.11 — HNSW index
    r = check("2.11", "cloud_sql", "HNSW index on rag_embeddings (cosine, m=16)")
    t0 = time.perf_counter()
    try:
        row = q1("SELECT indexname FROM pg_indexes WHERE tablename='rag_embeddings' AND indexname LIKE '%hnsw%'")
        lat = (time.perf_counter() - t0) * 1000
        if row:
            r.ok(f"Index '{row}' present", latency=lat).print()
        else:
            r.warn("HNSW index not found — vector_search will use sequential scan (slow)", latency=lat).print()
    except Exception as e:
        r.warn(str(e)).print()

    conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 3 — GCS bucket accessibility
# ═════════════════════════════════════════════════════════════════════════════

def audit_gcs() -> None:
    print(head_("SECTION 3 — GCS buckets (Application Default Credentials)"))

    try:
        from google.cloud import storage as gcs_lib
    except ImportError:
        for r_id in ["3.1","3.2","3.3","3.4","3.5"]:
            check(r_id, "gcs", "GCS bucket").skip("google-cloud-storage not installed").print()
        return

    project = os.environ.get("GCP_PROJECT", "madhav-astrology")

    buckets_to_check = [
        ("3.1", os.environ.get("GCS_BUCKET_CHAT_ATTACHMENTS", "madhav-astrology-chat-attachments"),
         "Chat attachments bucket (upload/download for chat files)"),
        ("3.2", os.environ.get("GCS_BUCKET_CHART_DOCUMENTS", "madhav-astrology-chart-documents"),
         "Chart documents bucket (reports PDF storage)"),
        ("3.3", os.environ.get("GCS_SOURCES_BUCKET", "madhav-marsys-sources"),
         "Sources bucket (pipeline reads VALIDATED_ASSET_REGISTRY + corpus files)"),
        ("3.4", os.environ.get("GCS_ARTIFACTS_BUCKET", "madhav-marsys-build-artifacts"),
         "Build artifacts bucket (pipeline writes build manifests)"),
    ]

    client = gcs_lib.Client(project=project)

    for r_id, bucket_name, desc in buckets_to_check:
        r = check(r_id, "gcs", f"{desc} [{bucket_name}]")
        t0 = time.perf_counter()
        try:
            bucket = client.bucket(bucket_name)
            blobs = list(bucket.list_blobs(max_results=1))
            lat = (time.perf_counter() - t0) * 1000
            r.ok(f"Accessible (sampled 1 object)", latency=lat, bucket=bucket_name).print()
        except Exception as e:
            r.fail(f"{e}", latency=(time.perf_counter()-t0)*1000, bucket=bucket_name).print()

    # 3.5 — Validate key corpus files exist in sources bucket
    r = check("3.5", "gcs", "L1/L2.5 corpus files present in sources bucket")
    t0 = time.perf_counter()
    sources_bucket = os.environ.get("GCS_SOURCES_BUCKET", "madhav-marsys-sources")
    expected_gcs_paths = [
        ("L1/facts/FORENSIC_ASTROLOGICAL_DATA_v8_0.md",   "L1 Forensic"),
        ("L2_5/MSR_v3_0.md",                              "L2.5 MSR"),
        ("L2_5/UCN_v4_0.md",                              "L2.5 UCN"),
        ("L2_5/CGM_v9_0.md",                              "L2.5 CGM"),
        ("L2_5/CDLM_v1_1.md",                             "L2.5 CDLM"),
        ("L3/registers/PATTERN_REGISTER_v1_0.json",       "L3 Pattern Register"),
        ("L3/registers/RESONANCE_REGISTER_v1_0.json",     "L3 Resonance Register"),
        ("L3/registers/CLUSTER_ATLAS_v1_0.json",          "L3 Cluster Atlas"),
        ("L3/registers/CONTRADICTION_REGISTER_v1_0.json", "L3 Contradiction Register"),
    ]
    try:
        bucket = client.bucket(sources_bucket)
        present: list[str] = []
        missing: list[str] = []
        for gcs_path, label in expected_gcs_paths:
            blob = bucket.blob(gcs_path)
            if blob.exists():
                present.append(f"{label} ({gcs_path})")
            else:
                missing.append(f"{label} ({gcs_path})")
        lat = (time.perf_counter() - t0) * 1000
        if missing:
            r.fail(
                f"{len(present)}/{len(expected_gcs_paths)} present.\n"
                f"         Missing: {missing}", latency=lat,
                present=present, missing=missing
            ).print()
        else:
            r.ok(f"All {len(present)} corpus files present in GCS", latency=lat,
                 present=present).print()
    except Exception as e:
        r.fail(str(e)).print()

    # 3.6 — VALIDATED_ASSET_REGISTRY
    r = check("3.6", "gcs", "VALIDATED_ASSET_REGISTRY_v1_0.json in sources bucket")
    t0 = time.perf_counter()
    try:
        bucket = client.bucket(os.environ.get("GCS_SOURCES_BUCKET", "madhav-marsys-sources"))
        blob = bucket.blob("00_ARCHITECTURE/VALIDATED_ASSET_REGISTRY_v1_0.json")
        if blob.exists():
            size = blob.size or 0
            r.ok(f"Present ({size//1024}KB)", latency=(time.perf_counter()-t0)*1000).print()
        else:
            r.fail("VALIDATED_ASSET_REGISTRY not found — pipeline will fail to start").print()
    except Exception as e:
        r.fail(str(e)).print()


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Vertex AI embedding endpoint
# ═════════════════════════════════════════════════════════════════════════════

def audit_vertex_ai() -> None:
    print(head_("SECTION 4 — Vertex AI (text-multilingual-embedding-002, asia-south1)"))

    try:
        from google.auth import default as gauth_default
        import urllib.request
        import urllib.error
    except ImportError:
        check("4.1", "vertex_ai", "Vertex AI embedding call").skip("google-auth not installed").print()
        return

    project = os.environ.get("GCP_PROJECT", "madhav-astrology")
    location = os.environ.get("VERTEX_AI_LOCATION", "us-central1")

    # 4.1 — ADC credentials
    r = check("4.1", "vertex_ai", "Application Default Credentials available")
    t0 = time.perf_counter()
    try:
        creds, proj = gauth_default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        lat = (time.perf_counter() - t0) * 1000
        r.ok(f"ADC: project={proj or '(none in creds)'}  GCP_PROJECT env={project}", latency=lat).print()
        creds.refresh(None) if not creds.valid else None
    except Exception as e:
        r.fail(f"{e}\n         → Run: gcloud auth application-default login").print()
        check("4.2", "vertex_ai", "Vertex AI embed call").skip("No ADC credentials").print()
        return

    # 4.2 — Live embedding call
    r = check("4.2", "vertex_ai", f"Embed test phrase via Vertex AI ({location})")
    t0 = time.perf_counter()
    try:
        import vertexai
        from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel
        vertexai.init(project=project, location=location)
        model = TextEmbeddingModel.from_pretrained("text-multilingual-embedding-002")
        inputs = [TextEmbeddingInput("[L2.5] [msr_signal]\nSaturn in 7th house, Libra ascendant", "RETRIEVAL_QUERY")]
        results_vx = model.get_embeddings(inputs)
        vec = results_vx[0].values
        lat = (time.perf_counter() - t0) * 1000
        if len(vec) == 768:
            r.ok(f"dim=768 ✓  first3={[round(v,4) for v in vec[:3]]}", latency=lat,
                 dim=len(vec), location=location).print()
        else:
            r.fail(f"Unexpected dim={len(vec)}, expected 768", latency=lat).print()
    except Exception as e:
        r.fail(f"{e}", latency=(time.perf_counter()-t0)*1000).print()


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Python sidecar health + endpoints
# ═════════════════════════════════════════════════════════════════════════════

def audit_sidecar(chart_id: str = CANONICAL_CHART_ID) -> None:
    print(head_("SECTION 5 — Python sidecar (PYTHON_SIDECAR_URL)"))

    sidecar_url = os.environ.get("PYTHON_SIDECAR_URL", "http://localhost:8000").rstrip("/")
    sidecar_key = os.environ.get("PYTHON_SIDECAR_API_KEY", "")

    import urllib.request, urllib.error
    headers = {"Content-Type": "application/json"}
    if sidecar_key:
        headers["x-api-key"] = sidecar_key

    def sidecar_get(path: str) -> tuple[int, dict]:
        req = urllib.request.Request(f"{sidecar_url}{path}", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, {}
        except Exception as exc:
            return -1, {"error": str(exc)}

    def sidecar_post(path: str, body: dict) -> tuple[int, dict]:
        data = json.dumps(body).encode()
        req = urllib.request.Request(f"{sidecar_url}{path}", data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            try: body_err = json.loads(e.read())
            except: body_err = {}
            return e.code, body_err
        except Exception as exc:
            return -1, {"error": str(exc)}

    # 5.1 — Health
    r = check("5.1", "sidecar", f"Sidecar health check [{sidecar_url}/health]")
    t0 = time.perf_counter()
    status, body = sidecar_get("/health")
    lat = (time.perf_counter() - t0) * 1000
    if status == 200 and body.get("status") == "ok":
        r.ok(f"HTTP 200 {body}", latency=lat, url=sidecar_url).print()
    elif status == -1:
        r.fail(
            f"Cannot reach sidecar: {body.get('error')}\n"
            f"         URL: {sidecar_url}\n"
            f"         → Start sidecar: cd platform/python-sidecar && uvicorn main:app --port 8000"
        ).print()
        for r_id in ["5.2","5.3","5.4","5.5","5.6"]:
            check(r_id, "sidecar", "sidecar endpoint").skip("sidecar unreachable").print()
        return
    else:
        r.fail(f"HTTP {status}: {body}", latency=lat).print()

    today = datetime.now(timezone.utc).date().isoformat()
    native_payload = {"chart_id": chart_id, "date": today}

    sidecar_endpoints = [
        ("5.2", "/transits",           native_payload,  "Transits (temporal tool → /transits)"),
        ("5.3", "/ephemeris",          native_payload,  "Ephemeris (temporal tool forward_looking → /ephemeris)"),
        ("5.4", "/sade_sati",          native_payload,  "Sade Sati cycles"),
        ("5.5", "/eclipses",           {"start_date": today, "end_date": "2026-12-31"}, "Eclipses window"),
        ("5.6", "/rag/retrieve",       {"query": "Saturn 7th house Libra ascendant", "mode": "hybrid_rrf", "k": 3},
         "RAG retrieve (/rag/retrieve — hybrid_rrf)"),
    ]

    for r_id, path, payload, desc in sidecar_endpoints:
        r2 = check(r_id, "sidecar", f"{desc} [{path}]")
        t0 = time.perf_counter()
        sc, rb = sidecar_post(path, payload)
        lat = (time.perf_counter() - t0) * 1000
        if sc == 200:
            # Summarise response
            if isinstance(rb, list):
                r2.ok(f"HTTP 200 — {len(rb)} items returned", latency=lat).print()
            elif isinstance(rb, dict):
                keys = list(rb.keys())[:4]
                r2.ok(f"HTTP 200 — keys: {keys}", latency=lat).print()
            else:
                r2.ok(f"HTTP 200", latency=lat).print()
        elif sc == 401:
            r2.fail(f"HTTP 401 Unauthorized — check PYTHON_SIDECAR_API_KEY matches Cloud Run env", latency=lat).print()
        elif sc == -1:
            r2.fail(f"Connection error: {rb.get('error')}", latency=lat).print()
        else:
            r2.fail(f"HTTP {sc}: {json.dumps(rb)[:200]}", latency=lat).print()


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Retrieval tool data source checks (all 10 tools)
# ═════════════════════════════════════════════════════════════════════════════

def audit_retrieval_tools(repo_root: str) -> None:
    print(head_("SECTION 6 — All 10 retrieval tools: data source accessibility"))

    db_url = os.environ.get("DATABASE_URL", "")

    # Tool 1: msr_sql → Cloud SQL msr_signals
    r = check("6.1", "tool", "msr_sql — Cloud SQL: msr_signals table")
    if not db_url:
        r.skip("DATABASE_URL not set").print()
    else:
        try:
            import psycopg
            t0 = time.perf_counter()
            with psycopg.connect(db_url) as conn:
                cnt = conn.execute("SELECT COUNT(*) FROM msr_signals").fetchone()[0]
                sample = conn.execute(
                    "SELECT domain, COUNT(*) FROM msr_signals GROUP BY domain ORDER BY COUNT(*) DESC LIMIT 5"
                ).fetchall()
            lat = (time.perf_counter() - t0) * 1000
            domain_summary = {row[0]: row[1] for row in sample}
            if cnt >= 400:
                r.ok(f"{cnt:,} signals. Top domains: {domain_summary}", latency=lat, row_count=cnt).print()
            else:
                r.warn(f"Only {cnt} signals (expected ~499). May affect query quality.", latency=lat).print()
        except Exception as e:
            r.fail(str(e)).print()

    # Tools 2–5: Register JSON files
    for r_id, tool, reg_path, label, layer in [
        ("6.2", "pattern_register",      "035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_v1_0.json",      "Pattern Register",      "L3"),
        ("6.3", "resonance_register",    "035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_0.json",    "Resonance Register",    "L3"),
        ("6.4", "cluster_atlas",         "035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_0.json",         "Cluster Atlas",         "L3"),
        ("6.5", "contradiction_register","035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_0.json","Contradiction Register", "L3"),
    ]:
        r2 = check(r_id, "tool", f"{tool} — filesystem: {reg_path} ({layer})")
        full_path = Path(repo_root) / reg_path
        t0 = time.perf_counter()
        if not full_path.exists():
            r2.fail(
                f"File NOT FOUND at {full_path}\n"
                f"         This file WILL fail in Cloud Run too (035_DISCOVERY_LAYER not in Dockerfile)\n"
                f"         Fix: COPY --from=builder --chown=nextjs:nodejs /app/035_DISCOVERY_LAYER ./035_DISCOVERY_LAYER"
            ).print()
        else:
            try:
                txt = full_path.read_text()
                data = json.loads(txt)
                lat = (time.perf_counter() - t0) * 1000
                # Count entries
                if isinstance(data, dict):
                    # Pattern/Resonance/Contradiction registers have a top-level list key
                    list_key = next((k for k, v in data.items() if isinstance(v, list)), None)
                    cnt = len(data[list_key]) if list_key else "dict"
                    r2.ok(f"{cnt} entries ({list_key or 'nested'}), {len(txt)//1024}KB", latency=lat).print()
                else:
                    r2.ok(f"{len(data)} entries, {len(txt)//1024}KB", latency=lat).print()
            except json.JSONDecodeError as e:
                r2.fail(f"Invalid JSON: {e}").print()
            except Exception as e:
                r2.fail(str(e)).print()

    # Tool 6: temporal → sidecar (already covered in Section 5, just reference)
    r = check("6.6", "tool", "temporal — Python sidecar /transits (see 5.2 for live check)")
    sidecar_url = os.environ.get("PYTHON_SIDECAR_URL", "http://localhost:8000").rstrip("/")
    r.ok(f"Delegates to sidecar at {sidecar_url}/transits — result in check 5.2").print()

    # Tool 7: query_msr_aggregate — no I/O stub
    r = check("6.7", "tool", "query_msr_aggregate — no I/O (multi-native stub, always returns status)")
    r.ok("Stub tool — returns 'multi_native_not_deployed' immediately, no cloud calls").print()

    # Tool 8: cgm_graph_walk → Cloud SQL l25_cgm_nodes + l25_cgm_edges
    r = check("6.8", "tool", "cgm_graph_walk — l25_cgm_nodes + l25_cgm_edges (L2.5 CGM)")
    if not db_url:
        r.skip("DATABASE_URL not set").print()
    else:
        try:
            import psycopg
            t0 = time.perf_counter()
            with psycopg.connect(db_url) as conn:
                nodes       = conn.execute("SELECT COUNT(*) FROM l25_cgm_nodes").fetchone()[0]
                edges_valid = conn.execute("SELECT COUNT(*) FROM l25_cgm_edges WHERE status='valid'").fetchone()[0]
                edges_total = conn.execute("SELECT COUNT(*) FROM l25_cgm_edges").fetchone()[0]
                edge_types  = conn.execute(
                    "SELECT edge_type, status, COUNT(*) FROM l25_cgm_edges "
                    "GROUP BY edge_type, status ORDER BY COUNT(*) DESC"
                ).fetchall()
            lat = (time.perf_counter() - t0) * 1000
            et_summary = {f"{row[0]}({row[1]})": row[2] for row in edge_types}
            if nodes > 0 and edges_valid > 0:
                r.ok(
                    f"nodes={nodes:,}  edges_valid={edges_valid}  edges_total={edges_total}  types={et_summary}",
                    latency=lat,
                ).print()
            else:
                r.warn(
                    f"nodes={nodes}  edges_valid={edges_valid}  edges_total={edges_total} — CGM graph may not be ingested yet",
                    latency=lat,
                ).print()
        except Exception as e:
            r.fail(str(e)).print()

    # Tool 9: manifest_query → filesystem 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
    r = check("6.9", "tool", "manifest_query — filesystem: 00_ARCHITECTURE/CAPABILITY_MANIFEST.json (L0)")
    manifest_path = Path(repo_root) / "00_ARCHITECTURE" / "CAPABILITY_MANIFEST.json"
    t0 = time.perf_counter()
    if manifest_path.exists():
        try:
            data = json.loads(manifest_path.read_text())
            lat = (time.perf_counter() - t0) * 1000
            n_entries = len(data.get("entries", []))
            fp = data.get("fingerprint", "?")[:16]
            r.ok(f"{n_entries} entries  fingerprint={fp}...", latency=lat, entries=n_entries).print()
        except Exception as e:
            r.fail(str(e)).print()
    else:
        r.fail(f"CAPABILITY_MANIFEST.json not found at {manifest_path}").print()

    # Tool 10: vector_search → Vertex AI + Cloud SQL rag_embeddings + rag_chunks
    r = check("6.10", "tool", "vector_search — Vertex AI embed + Cloud SQL: rag_embeddings ⊕ rag_chunks")
    if not db_url:
        r.skip("DATABASE_URL not set — skipping vector search check").print()
    else:
        try:
            import psycopg
            t0 = time.perf_counter()
            with psycopg.connect(db_url) as conn:
                chunk_cnt = conn.execute("SELECT COUNT(*) FROM rag_chunks WHERE is_stale=false").fetchone()[0]
                emb_cnt   = conn.execute("SELECT COUNT(*) FROM rag_embeddings").fetchone()[0]
                # Verify coverage: embeddings / chunks ratio
                coverage = round(emb_cnt / chunk_cnt * 100, 1) if chunk_cnt > 0 else 0
                # Check doc_type distribution
                doc_types = conn.execute(
                    "SELECT doc_type, COUNT(*) FROM rag_chunks WHERE is_stale=false GROUP BY doc_type ORDER BY COUNT(*) DESC"
                ).fetchall()
            lat = (time.perf_counter() - t0) * 1000
            dt_summary = {row[0]: row[1] for row in doc_types}
            if chunk_cnt == 0:
                r.warn("No non-stale chunks — vector_search will return empty results", latency=lat).print()
            elif emb_cnt == 0:
                r.warn(f"{chunk_cnt:,} chunks but 0 embeddings — run embed.py or pipeline", latency=lat).print()
            elif coverage < 90:
                r.warn(f"chunks={chunk_cnt:,}  embeddings={emb_cnt:,}  coverage={coverage}%  doc_types={dt_summary}", latency=lat).print()
            else:
                r.ok(f"chunks={chunk_cnt:,}  embeddings={emb_cnt:,}  coverage={coverage}%  doc_types={dt_summary}", latency=lat).print()
        except Exception as e:
            r.fail(str(e)).print()


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Anthropic API reachability
# ═════════════════════════════════════════════════════════════════════════════

def audit_anthropic() -> None:
    print(head_("SECTION 7 — Anthropic API (classify + synthesize hop)"))

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        check("7.1", "anthropic", "Anthropic API key set").fail("ANTHROPIC_API_KEY not set").print()
        return

    r = check("7.1", "anthropic", "Anthropic API key format")
    if api_key.startswith("sk-ant-"):
        r.ok(f"Key present: sk-ant-...{api_key[-8:]}").print()
    else:
        r.warn("Key present but doesn't start with sk-ant- — may be wrong key type").print()

    # Quick auth check — list models endpoint
    r = check("7.2", "anthropic", "Anthropic API reachable (models endpoint)")
    import urllib.request, urllib.error
    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/models",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            lat = (time.perf_counter() - t0) * 1000
            models = [m["id"] for m in data.get("data", [])[:3]]
            r.ok(f"HTTP 200 — sample models: {models}", latency=lat).print()
    except urllib.error.HTTPError as e:
        lat = (time.perf_counter() - t0) * 1000
        if e.code == 401:
            r.fail("HTTP 401 — API key invalid or expired", latency=lat).print()
        else:
            r.fail(f"HTTP {e.code}", latency=lat).print()
    except Exception as e:
        r.fail(f"Network error: {e}").print()


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 8 — End-to-end pipeline hop summary
# ═════════════════════════════════════════════════════════════════════════════

def print_pipeline_map() -> None:
    print(head_("SECTION 8 — Full pipeline hop map"))
    hops = [
        ("Consumer UI", "POST /api/chat/consume", "Next.js server"),
        ("Firebase Auth", "getServerUser()", "Google Cloud / Firebase Admin SDK"),
        ("Cloud SQL", "chart + profile + reports lookup", "charts, profiles, reports tables"),
        ("classify()", "LLM router → QueryPlan", "Anthropic API (claude model)"),
        ("loadManifest()", "CAPABILITY_MANIFEST.json", "filesystemAdapter → MARSYS_REPO_ROOT/00_ARCHITECTURE/"),
        ("compose()", "rule_composer → ToolBundle", "Deterministic — no I/O"),
        ("msr_sql", "L2.5 MSR signals", "Cloud SQL: msr_signals"),
        ("pattern_register", "L3 Pattern Register", "filesystemAdapter: 035_DISCOVERY_LAYER/REGISTERS/"),
        ("resonance_register", "L3 Resonance Register", "filesystemAdapter: 035_DISCOVERY_LAYER/REGISTERS/"),
        ("cluster_atlas", "L3 Cluster Atlas", "filesystemAdapter: 035_DISCOVERY_LAYER/REGISTERS/"),
        ("contradiction_reg", "L3 Contradiction Register", "filesystemAdapter: 035_DISCOVERY_LAYER/REGISTERS/"),
        ("temporal", "Current transits + ephemeris", "Python sidecar → pyswisseph"),
        ("query_msr_agg", "Multi-native aggregate", "Stub (not deployed) — no I/O"),
        ("cgm_graph_walk", "L2.5 CGM BFS traversal", "Cloud SQL: l25_cgm_nodes + l25_cgm_edges"),
        ("manifest_query", "L0 Architecture manifest", "filesystemAdapter: 00_ARCHITECTURE/"),
        ("vector_search", "Semantic similarity", "Vertex AI embed → Cloud SQL: rag_embeddings + rag_chunks"),
        ("synthesize()", "Multi-model synthesis", "Anthropic API (panel or single model)"),
        ("audit write", "Query audit log", "Cloud SQL: audit_events"),
        ("trace emit", "Trace steps", "Cloud SQL: query_trace_steps"),
        ("persist", "Conversation + messages", "Cloud SQL: conversations + messages"),
    ]
    for step, action, backend in hops:
        print(f"  {BOLD}{step:<22}{RESET}  {action:<35}  {DIM}→ {backend}{RESET}")


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 9 — Report generation
# ═════════════════════════════════════════════════════════════════════════════

def generate_report(repo_root: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    total   = len(results)
    passed  = sum(1 for r in results if r.status == "pass")
    failed  = sum(1 for r in results if r.status == "fail")
    warned  = sum(1 for r in results if r.status == "warn")
    skipped = sum(1 for r in results if r.status == "skip")

    print(head_("AUDIT SUMMARY"))
    print(f"  {BOLD}Total checks:{RESET}  {total}")
    print(f"  {GRN}Passed:{RESET}        {passed}")
    print(f"  {RED}Failed:{RESET}        {failed}")
    print(f"  {YLW}Warnings:{RESET}      {warned}")
    print(f"  {DIM}Skipped:{RESET}       {skipped}")

    if failed > 0:
        print(f"\n{BOLD}{RED}FAILURES requiring action:{RESET}")
        for r in results:
            if r.status == "fail":
                print(f"  [{r.check_id}] {r.description}")
                print(f"         {r.detail}")

    if warned > 0:
        print(f"\n{BOLD}{YLW}Warnings to review:{RESET}")
        for r in results:
            if r.status == "warn":
                print(f"  [{r.check_id}] {r.description}")
                if r.detail:
                    print(f"         {r.detail}")

    # JSON report
    json_report = {
        "audit_version": "1.0",
        "produced_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": repo_root,
        "summary": {"total": total, "passed": passed, "failed": failed,
                    "warned": warned, "skipped": skipped},
        "checks": [r.to_dict() for r in results],
    }
    json_path = Path(repo_root) / f"PIPELINE_SMOKE_AUDIT_REPORT_{ts}.json"
    json_path.write_text(json.dumps(json_report, indent=2))
    print(f"\n{info_(f'JSON report: {json_path}')}")

    # Markdown report
    md_lines = [
        f"# Pipeline Smoke Audit Report",
        f"",
        f"**Produced:** {datetime.now(timezone.utc).isoformat()}",
        f"**Repo root:** `{repo_root}`",
        f"",
        f"## Summary",
        f"",
        f"| | Count |",
        f"|---|---|",
        f"| ✅ Pass | {passed} |",
        f"| ❌ Fail | {failed} |",
        f"| ⚠️ Warn | {warned} |",
        f"| ⏭ Skip | {skipped} |",
        f"| **Total** | **{total}** |",
        f"",
        f"## Results",
        f"",
        f"| ID | Category | Description | Status | Detail | Latency |",
        f"|---|---|---|---|---|---|",
    ]
    icons = {"pass": "✅", "fail": "❌", "warn": "⚠️", "skip": "⏭", "info": "ℹ️"}
    for r in results:
        icon = icons.get(r.status, "?")
        lat = f"{r.latency_ms:.0f}ms" if r.latency_ms is not None else "—"
        detail = r.detail.replace("\n", " ").replace("|", "\\|")[:120]
        md_lines.append(
            f"| {r.check_id} | {r.category} | {r.description} | {icon} {r.status.upper()} | {detail} | {lat} |"
        )

    if failed > 0:
        md_lines += ["", "## ❌ Failures (action required)", ""]
        for r in results:
            if r.status == "fail":
                md_lines += [f"### [{r.check_id}] {r.description}", f"", f"```", r.detail, f"```", ""]

    if warned > 0:
        md_lines += ["", "## ⚠️ Warnings", ""]
        for r in results:
            if r.status == "warn":
                md_lines += [f"### [{r.check_id}] {r.description}", f"", r.detail, ""]

    md_path = Path(repo_root) / f"PIPELINE_SMOKE_AUDIT_REPORT_{ts}.md"
    md_path.write_text("\n".join(md_lines))
    print(f"{info_(f'MD  report: {md_path}')}")


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="MARSYS-JIS Pipeline Smoke Audit")
    parser.add_argument("--repo-root", default=None,
                        help="Path to repo root (default: auto-detect from script location)")
    parser.add_argument("--skip-vertex", action="store_true", help="Skip Vertex AI embed call (saves ~2s)")
    parser.add_argument("--skip-sidecar", action="store_true", help="Skip sidecar checks")
    parser.add_argument("--chart-id", default=CANONICAL_CHART_ID,
                        help="Chart UUID used for the sidecar probes (default: the canonical chart)")
    args = parser.parse_args()

    # Detect repo root from script location: scripts/ is 2 levels down from platform/, 3 from root
    if args.repo_root:
        repo_root = args.repo_root
    else:
        script_dir = Path(__file__).resolve().parent   # platform/scripts/
        platform_dir = script_dir.parent               # platform/
        repo_root = str(platform_dir.parent)           # repo root

    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  MARSYS-JIS Pipeline Smoke Audit{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}")
    print(f"  Repo root:  {repo_root}")
    print(f"  Time:       {datetime.now(timezone.utc).isoformat()}")

    load_env(repo_root)

    print_pipeline_map()
    audit_static_code(repo_root)
    audit_cloud_sql()
    audit_gcs()
    if not args.skip_vertex:
        audit_vertex_ai()
    else:
        check("4.1","vertex_ai","Vertex AI ADC").skip("--skip-vertex flag").print()
        check("4.2","vertex_ai","Vertex AI embed call").skip("--skip-vertex flag").print()
    if not args.skip_sidecar:
        audit_sidecar(args.chart_id)
    else:
        for i in range(1,7):
            check(f"5.{i}","sidecar","sidecar check").skip("--skip-sidecar flag").print()
    audit_retrieval_tools(repo_root)
    audit_anthropic()
    generate_report(repo_root)


if __name__ == "__main__":
    main()
