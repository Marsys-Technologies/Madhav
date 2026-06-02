-- 005_pgvector_rag_schema.sql
-- AM-JIS RAG schema — Madhav 17 B.0 (2026-04-24)
-- Per PHASE_B_PLAN_v1_0.md §G B.0 Task 7

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- RAG chunks: each corpus segment with layer and type metadata
CREATE TABLE IF NOT EXISTS rag_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id TEXT UNIQUE NOT NULL,
    doc_type TEXT NOT NULL,          -- msr_signal|ucn_section|cdlm_cell|l1_fact|domain_report|cgm_node
    layer TEXT NOT NULL,             -- L1|L2|L2.5|L3|L4
    source_file TEXT NOT NULL,
    source_version TEXT NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    is_stale BOOLEAN DEFAULT FALSE,
    stale_reason TEXT,
    stale_since TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RAG embeddings: Vertex AI text-multilingual-embedding-002 embeddings for each chunk
-- NOTE: Original schema used vector(1024) for Voyage-3-large. Migration 010 alters this
-- to vector(768) for Vertex AI text-multilingual-embedding-002. Applied after B.3.
CREATE TABLE IF NOT EXISTS rag_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id TEXT NOT NULL REFERENCES rag_chunks(chunk_id) ON DELETE CASCADE,
    model TEXT NOT NULL,             -- vertex-text-multilingual-embedding-002|openai-fallback
    embedding vector(1024),          -- dimension updated to 768 in migration 010
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RAG graph nodes: chunks + fact_ids + signal_ids + domains
CREATE TABLE IF NOT EXISTS rag_graph_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id TEXT UNIQUE NOT NULL,
    node_type TEXT NOT NULL,         -- chunk|fact|signal|domain
    chunk_id TEXT REFERENCES rag_chunks(chunk_id),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RAG graph edges: typed relationships between nodes
CREATE TABLE IF NOT EXISTS rag_graph_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    edge_id TEXT UNIQUE NOT NULL,
    source_node_id TEXT NOT NULL REFERENCES rag_graph_nodes(node_id),
    target_node_id TEXT NOT NULL REFERENCES rag_graph_nodes(node_id),
    edge_type TEXT NOT NULL,         -- CITES|MENTIONS|AFFECTS_DOMAIN|CROSS_LINKS|SUPPORTS|CONTRADICTS
    weight FLOAT DEFAULT 1.0,
    actor TEXT,                      -- claude|gemini-web-YYYY-MM-DD|deterministic
    ledger_event_id TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RAG queries: logged query-plan executions
CREATE TABLE IF NOT EXISTS rag_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id TEXT UNIQUE NOT NULL,
    query_text TEXT NOT NULL,
    query_plan JSONB,
    significance_score FLOAT,
    actor TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RAG retrievals: bundle of chunks returned per query
CREATE TABLE IF NOT EXISTS rag_retrievals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    retrieval_id TEXT UNIQUE NOT NULL,
    query_id TEXT REFERENCES rag_queries(query_id),
    chunk_ids TEXT[],
    retrieval_method TEXT,           -- vector|bm25|graph|hybrid|rrf
    scores JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RAG feedback: human review flags
CREATE TABLE IF NOT EXISTS rag_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_id TEXT NOT NULL,
    target_type TEXT NOT NULL,       -- chunk|retrieval|discovery_entry
    feedback_type TEXT NOT NULL,     -- flag_for_review|validated|rejected
    note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RAG reproducibility failures: §E.9 tolerance tracking
CREATE TABLE IF NOT EXISTS rag_reproducibility_failures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id TEXT NOT NULL,
    run_1_bundle_hash TEXT NOT NULL,
    run_2_bundle_hash TEXT NOT NULL,
    dimension TEXT NOT NULL,
    tolerance_value FLOAT,
    actual_value FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_rag_embeddings_chunk ON rag_embeddings(chunk_id);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_layer ON rag_chunks(layer);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_doc_type ON rag_chunks(doc_type);
CREATE INDEX IF NOT EXISTS idx_rag_graph_edges_source ON rag_graph_edges(source_node_id);
CREATE INDEX IF NOT EXISTS idx_rag_graph_edges_target ON rag_graph_edges(target_node_id);
CREATE INDEX IF NOT EXISTS idx_rag_graph_edges_type ON rag_graph_edges(edge_type);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_stale ON rag_chunks(is_stale);

-- HNSW index for vector similarity search (see migration 010 — updated to 768 dims for Vertex AI)
CREATE INDEX IF NOT EXISTS idx_rag_embeddings_hnsw
    ON rag_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- GIN index for full-text search on chunk content
CREATE INDEX IF NOT EXISTS idx_rag_chunks_content_gin
    ON rag_chunks
    USING gin(to_tsvector('english', content));
