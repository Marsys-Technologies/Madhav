---
brief_id: M2_B1_CGM_FULL_EDGES
karn_session_name: KARN-W2-R3-CGM-FULL-EDGES
wave: 2
stream: A
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-30 — Wave 1 close
authored_for: Claude Code execution (autonomous, long-running)
session_type: implementation (extractor extension + edge ingest + verify)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: |
    Pre-KARN-2 (RETRIEVAL_11C_a) — landed UCN.SEC.* + KARAKA.DUAL_SYSTEM_DIVERGENCE nodes
    and brought l25_cgm_edges 21 → 126 valid (orphans 105 → 0).
    KARN-W1-R1-PHASE-ALPHA — confirmed current edge count.
  blocks: M2_B4_PATTERN_EXPANSION (W3), M2_C1_CHART_FACTS_QUERY (W4) — both need richer CGM topology.
parallel_stream_note: |
  Two other Wave-2 briefs run concurrently:
  - KARN-W2-R1-MSR-ETL (Stream A, msr_signals 8 columns) — owns migration 028
  - KARN-W2-R2-CHART-FACTS-ETL (Stream A, chart_facts §6–§24) — owns migration 029
  This brief owns:
  - migration 030 (l25_cgm_edges schema unchanged; index additions only)
  - python-sidecar/pipeline/extractors/cgm_extractor.py
  - cgm_graph_walk.ts read-only verify
  Disjoint from sibling briefs.
estimated_time: 1 day single Claude Code session

scope_summary: |
  l25_cgm_edges currently holds 126 valid edges (post-Pre-KARN-2). CGM v9.0 source
  (025_HOLISTIC_SYNTHESIS/CGM_v9_0.md) catalogues 339 edges across 15 edge_types.
  Coverage is 126/339 = 37%.

  This brief expands edge ingest to ~339 across 15 edge_types:
    1. RULES_OVER (lord-of-house relationships)
    2. ASPECTS (Parashari graha drishti)
    3. AFFLICTS (malefic aspect/conjunction)
    4. SUPPORTS (benefic aspect/conjunction)
    5. CONJUNCT (same-sign coincidence)
    6. DISPOSES (sign-lord relationships)
    7. KARAKA_OF (significator relationships)
    8. ARUDHA_OF (image-of relationships)
    9. DASHA_GIVES (dasha lord delivers)
    10. NAKSHATRA_OF (star-lord relationships)
    11. DUAL_SYSTEM_DIVERGENCE (cross-system contradictions; karaka aux node)
    12. SEC_REFERENCES (UCN.SEC.* node back-references)
    13. RESONATES_WITH (RM cross-references)
    14. CONTRADICTS_WITH (contradiction register)
    15. CO_OCCURS (statistical co-occurrence in MSR)

  Net effect: l25_cgm_edges 126 → ~339; cgm_graph_walk gains far richer traversal surface.
  Per-edge_type counts move from "sparse" to "complete" per CGM v9.0 spec.

  Plus rag_chunks doc_type=cgm_node coverage: 234 chunks → 369 chunks (mirror
  l25_cgm_nodes count, per W1-R1 finding §6.5 underchunking).

may_touch:
  - platform/migrations/030_cgm_edges_indexes.sql                      # CREATE — auxiliary indexes only
  - platform/python-sidecar/pipeline/extractors/cgm_extractor.py       # extend to parse all 15 edge types
  - platform/python-sidecar/pipeline/extractors/__tests__/test_cgm_extractor.py  # extend
  - platform/python-sidecar/pipeline/loaders/cgm_loader.py             # accept new edge_types
  - platform/python-sidecar/pipeline/chunkers/cgm_chunker.py           # ensure all 369 nodes chunk
  - platform/python-sidecar/pipeline/chunkers/__tests__/test_cgm_chunker.py
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_B1_CGM_FULL_EDGES.md    # status flip
  - 00_ARCHITECTURE/BRIEFS/M2_B1_VERIFICATION_<DATE>.txt               # CREATE
  - 00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md                         # update §7 + add CGM edge_types subsection

must_not_touch:
  - CLAUDECODE_BRIEF.md (root)                                         # UI/UX stream
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_A1_MSR_ETL.md           # sibling Wave-2
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_A2_CHART_FACTS_ETL.md   # sibling Wave-2
  - platform/migrations/001-029                                        # historical, do not modify
  - platform/python-sidecar/pipeline/extractors/msr_extractor.py       # W2-R1 territory
  - platform/python-sidecar/pipeline/extractors/chart_facts_extractor.py  # W2-R2 territory
  - platform/src/components/**                                         # UI/UX scope
  - platform/src/app/**                                                # UI/UX scope
  - platform/src/lib/retrieve/cgm_graph_walk.ts                        # read-only this brief; modifications W6
  - platform/src/lib/retrieve/msr_sql.ts                               # W2-R1 territory
  - platform/src/lib/retrieve/vector_search.ts                         # W1-R2 territory
  - platform/src/lib/router/**                                         # not in scope
  - 025_HOLISTIC_SYNTHESIS/CGM_v9_0.md                                 # source-of-truth, read-only
  - 035_DISCOVERY_LAYER/**                                             # off-limits

acceptance_criteria:
  AC.1: |
    Pre-flight gate passes. Baselines:
      l25_cgm_nodes count = 369 (from Pre-KARN-2 11C_a + W1-R1 confirmation)
      l25_cgm_edges count = 126
      rag_chunks doc_type=cgm_node count = 234
    Note: secret name is `amjis-db-password` (NOT `amjis-app-db-password`).
  AC.2: |
    Read CGM v9.0 source carefully (025_HOLISTIC_SYNTHESIS/CGM_v9_0.md).
    Inventory each of the 15 edge_types and count expected edges per type.
    Document expected count per edge_type to verification txt §1.
    Total expected: ~339 (per CGM v9.0 spec).
  AC.3: |
    Migration 030 created at platform/migrations/030_cgm_edges_indexes.sql.
    Adds these auxiliary indexes (no schema changes):
      CREATE INDEX IF NOT EXISTS l25_cgm_edges_edge_type_idx
        ON l25_cgm_edges(edge_type);
      CREATE INDEX IF NOT EXISTS l25_cgm_edges_source_idx
        ON l25_cgm_edges(source_node_id);
      CREATE INDEX IF NOT EXISTS l25_cgm_edges_target_idx
        ON l25_cgm_edges(target_node_id);
      CREATE INDEX IF NOT EXISTS l25_cgm_edges_strength_idx
        ON l25_cgm_edges(strength) WHERE strength IS NOT NULL;
    These accelerate cgm_graph_walk traversal queries.
  AC.4: |
    cgm_extractor.py extended to parse all 15 edge_types from CGM v9.0.
    Each parsed edge has fields:
      edge_id           text         -- stable ID, e.g. "EDG.<source>.<edge_type>.<target>"
      edge_type         text         -- one of 15 enumerated types
      source_node_id    text         -- FK → l25_cgm_nodes.node_id
      target_node_id    text         -- FK → l25_cgm_nodes.node_id
      strength          numeric(4,2) -- per CGM spec, 0.0–1.0
      polarity          text         -- 'positive' | 'negative' | 'mixed'
      classical_basis   text         -- citation
      provenance        jsonb        -- source section reference
    edge_id MUST be unique per-row (existing UNIQUE constraint).
  AC.5: |
    Edge orphan check (FK validity). After ingest:
      SELECT COUNT(*) FROM l25_cgm_edges e
      WHERE NOT EXISTS (SELECT 1 FROM l25_cgm_nodes n WHERE n.node_id = e.source_node_id)
         OR NOT EXISTS (SELECT 1 FROM l25_cgm_nodes n WHERE n.node_id = e.target_node_id);
    MUST return 0. Pre-KARN-2 already brought orphans to 0; this brief MUST preserve that.
    HALT immediately if orphan count > 0 — means new edges reference nodes not in the catalog.
  AC.6: |
    Run cgm ingest pipeline:
      python -m pipeline.ingest_cgm \
        --source ../../025_HOLISTIC_SYNTHESIS/CGM_v9_0.md \
        --upsert
    Post-ingest count check:
      SELECT COUNT(*) FROM l25_cgm_edges;
        ≥ 320 (target ~339; ±5% tolerance)
    HALT if count < 280 (would suggest extractor bug or missing edge_type parsers).
  AC.7: |
    Per-edge_type breakdown:
      SELECT edge_type, COUNT(*) FROM l25_cgm_edges GROUP BY edge_type ORDER BY 2 DESC;
    All 15 edge_types must appear with non-zero counts.
    Counts must be within ±50% of CGM v9.0 spec per type.
    Capture full breakdown to verification txt.
  AC.8: |
    Sample 3 edges per edge_type to verify shape:
      SELECT edge_id, edge_type, source_node_id, target_node_id, strength, polarity,
             classical_basis, provenance::text
      FROM l25_cgm_edges WHERE edge_type=<X> LIMIT 3;
    Each edge MUST have populated source/target node IDs that exist in l25_cgm_nodes.
    Each edge SHOULD have classical_basis populated (≥80% fill rate per type).
  AC.9: |
    Re-chunk all l25_cgm_nodes into rag_chunks doc_type=cgm_node. UPSERT, don't duplicate.
    Post-chunk count:
      SELECT COUNT(*) FROM rag_chunks WHERE doc_type='cgm_node' AND is_stale=false;
        ≥ 365 (was 234; target 369 to mirror l25_cgm_nodes)
    Note: Pre-KARN-2 added 135 nodes but Pre-KARN-4 only chunked 234 (W1-R1 §6.5 finding).
    This brief closes that gap.
  AC.10: |
    cgm_graph_walk.ts read-only verification. Run a probe query that exercises new edge_types:
      SELECT * FROM cgm_graph_walk_test WHERE seed_node='PLN.SATURN' AND depth=2;
    (Or use a representative cgm_graph_walk test in the test suite.)
    Confirm graph walk returns more edges than baseline (was ~126; should now traverse ~339).
    Capture sample walk output to verification txt.
  AC.11: |
    Tests pass at pre-existing baseline (no new failures relative to baseline).
    New extractor unit tests added — at least 1 per edge_type covering parse + edge case.
  AC.12: |
    Cloud Run revision rebuilt and serving 100%.
  AC.13: |
    Live-deploy verification: send 2 fresh queries through Consume tab targeting
    multi-hop graph traversal (e.g. "How does my Saturn affect my Mercury through aspects
    and house lordship?" — should now traverse RULES_OVER + ASPECTS + AFFLICTS edges).
    Capture query_plans + answer + cgm_graph_walk evidence.
  AC.14: |
    M1_M2_ACTIVATION_MATRIX.md updated:
      - §7 Current State Snapshot: l25_cgm_edges row 127 → ~339, mark green ✅.
      - §7: rag_chunks cgm_node row 234 → ~369, mark green ✅.
      - Add new subsection §8 — CGM edge_types breakdown (per-type counts).
  AC.15: |
    git status shows ONLY:
      platform/migrations/030_cgm_edges_indexes.sql (new)
      platform/python-sidecar/pipeline/extractors/cgm_extractor.py (modified)
      platform/python-sidecar/pipeline/extractors/__tests__/test_cgm_extractor.py (modified)
      platform/python-sidecar/pipeline/loaders/cgm_loader.py (modified)
      platform/python-sidecar/pipeline/chunkers/cgm_chunker.py (modified)
      platform/python-sidecar/pipeline/chunkers/__tests__/test_cgm_chunker.py (modified)
      00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_B1_CGM_FULL_EDGES.md (status flip)
      00_ARCHITECTURE/BRIEFS/M2_B1_VERIFICATION_<DATE>.txt (new)
      00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md (modified)
    No other changes.
  AC.16: |
    This brief's frontmatter `status` flipped to COMPLETE. Closing summary appended to
    PROJECT_KARN_SESSION_LOG.md per protocol §3.1.

halt_conditions:
  - Auth Proxy unreachable on 127.0.0.1:5433 after 30s wait
  - gcloud ADC missing OR `amjis-db-password` secret unreadable (note: NOT `amjis-app-db-password`)
  - Branch is not redesign/r0-foundation (DO NOT switch)
  - Pre-existing l25_cgm_nodes count != 369 OR l25_cgm_edges count != 126 (Wave-1 baseline drift)
  - Migration 030 fails to apply
  - Post-ingest edge orphan count > 0 (CRITICAL — means new edges reference missing nodes)
  - Post-ingest edge count < 280 (would suggest extractor bug)
  - Any edge_type has 0 rows after ingest (parser miss)
  - Tests baseline drift > 2 failures
  - Cloud Build failure
  - cgm_graph_walk verification shows fewer edges than baseline (regression)
---

# CLAUDECODE_BRIEF — M2_B1_CGM_FULL_EDGES (Wave 2, Stream A, Run 3)

## §1 — Why this session

Pre-KARN-2 (RETRIEVAL_11C_a) closed the orphan-edge problem (105 → 0) by ingesting UCN.SEC.* + KARAKA.DUAL_SYSTEM_DIVERGENCE nodes. That was a topology fix. The valid edge count rose from 21 → 126.

But CGM v9.0 catalogues **339 edges** across 15 edge_types. We're at 37% coverage. The cgm_graph_walk tool is firing on ~30% of queries (W1-R1 finding §3.3) but each walk traverses a sparse subgraph — relationships that exist in the source aren't reachable in the database.

The big gap categories:
- **ASPECTS** — full Parashari grid: 9 planets × 9 grahas × multiple drishti lookups = ~50 edges expected; we have <10.
- **RULES_OVER** — sign lords + house lords + nakshatra lords = ~50 edges; sparse today.
- **AFFLICTS / SUPPORTS** — malefic/benefic relationships per planet pair = ~80 edges; partial.
- **DISPOSES** — sign-lord relationships per planet's sign = 9 edges; should be complete.
- **KARAKA_OF** — significator catalog = ~30 edges; partial.
- **DUAL_SYSTEM_DIVERGENCE** — cross-system contradictions; the karaka aux node has 4 today.
- **NAKSHATRA_OF** — star-lord relationships per planet = 9 edges; sparse.

After this lands:
- cgm_graph_walk traversal becomes meaningfully expressive — multi-hop queries return real chains.
- W3-R3 pattern_register expansion can mine the new edges for emergent patterns.
- W4-R3 chart_facts_query gets a denser join target via CGM.

**Not in scope:**
- New cgm_graph_walk filter parameters (W6 territory).
- Edge weight/strength tuning (defer to W5 res/con expansion).
- Discovery-layer (L3.5) edges (separate workstream).

## §2 — Pre-flight self-diagnostics (mandatory)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
test "$(git branch --show-current)" = "redesign/r0-foundation" || HALT "wrong branch"

git status --short
# HALT only on uncommitted modifications to files this brief targets.

gcloud auth application-default print-access-token > /dev/null 2>&1 || HALT "ADC missing"

PGPASSWORD=$(gcloud secrets versions access latest --secret="amjis-db-password" --project=madhav-astrology) || HALT "secret unavailable"
# IMPORTANT: secret name is `amjis-db-password` (NOT `amjis-app-db-password`).

nc -z 127.0.0.1 5433 || {
  bash platform/scripts/start_db_proxy.sh &
  for i in {1..30}; do nc -z 127.0.0.1 5433 && break; sleep 1; done
  nc -z 127.0.0.1 5433 || HALT "proxy failed to start"
}

PGPASSWORD="${PGPASSWORD}" psql "postgresql://amjis_app@127.0.0.1:5433/amjis" -t -c "
SELECT 'nodes', COUNT(*) FROM l25_cgm_nodes
UNION ALL
SELECT 'edges', COUNT(*) FROM l25_cgm_edges
UNION ALL
SELECT 'orphans', COUNT(*) FROM l25_cgm_edges e
  WHERE NOT EXISTS (SELECT 1 FROM l25_cgm_nodes n WHERE n.node_id=e.source_node_id)
     OR NOT EXISTS (SELECT 1 FROM l25_cgm_nodes n WHERE n.node_id=e.target_node_id)
UNION ALL
SELECT 'cgm_chunks', COUNT(*) FROM rag_chunks WHERE doc_type='cgm_node' AND is_stale=false;
"
# Expected: nodes=369, edges=126, orphans=0, cgm_chunks=234.
# HALT if any drift.

cd platform && npm test 2>&1 | tail -5
# Expected baseline (account for W2-R1/W2-R2 sibling deltas if landed first).
```

## §3 — Implementation steps

### §3.1 — Read CGM v9.0 + inventory edges (AC.2)

Open `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md`. CGM v9.0 should declare its 15 edge_types and per-type expected counts. Document expected count per edge_type to verification txt §1.

If CGM v9.0 doesn't enumerate exact counts, derive expected counts from the source structure:
- Each chart entity (planet, house, nakshatra, etc.) has well-defined relationship cardinalities.
- E.g., RULES_OVER: each planet rules 1–2 signs, each sign has 1 lord → 12 sign-lord edges + house-lord edges.
- Document the derivation in the verification txt.

### §3.2 — Migration 030

Create `platform/migrations/030_cgm_edges_indexes.sql`:

```sql
-- Migration 030 — KARN-W2-R3 — l25_cgm_edges auxiliary indexes
-- Predecessor: KARN-W1-R1-PHASE-ALPHA + Pre-KARN-2 (orphan resolution)

BEGIN;

CREATE INDEX IF NOT EXISTS l25_cgm_edges_edge_type_idx
  ON l25_cgm_edges(edge_type);

CREATE INDEX IF NOT EXISTS l25_cgm_edges_source_idx
  ON l25_cgm_edges(source_node_id);

CREATE INDEX IF NOT EXISTS l25_cgm_edges_target_idx
  ON l25_cgm_edges(target_node_id);

CREATE INDEX IF NOT EXISTS l25_cgm_edges_strength_idx
  ON l25_cgm_edges(strength) WHERE strength IS NOT NULL;

COMMIT;
```

Apply:
```bash
PGPASSWORD="${PGPASSWORD}" psql "postgresql://amjis_app@127.0.0.1:5433/amjis" \
  -f platform/migrations/030_cgm_edges_indexes.sql
```

### §3.3 — Extend cgm_extractor.py

Locate the edge-extraction code in `platform/python-sidecar/pipeline/extractors/cgm_extractor.py`. The Pre-KARN-2 work added UCN section nodes + KARAKA aux node. This brief expands edge parsing.

Implementation pattern — one parser per edge_type:

```python
def parse_rules_over_edges(cgm_md: str, nodes: dict[str, dict]) -> list[dict]:
    """Parse RULES_OVER (lord-of-X) edges from CGM source.

    Source pattern (illustrative):
      Sun rules Leo (sign lordship)
      Mars rules H1 of D1 (house lordship)
    """
    edges = []
    # ... parse logic ...
    for source, target, basis in extracted:
        edges.append({
            "edge_id": f"EDG.{source}.RULES_OVER.{target}",
            "edge_type": "RULES_OVER",
            "source_node_id": source,
            "target_node_id": target,
            "strength": 1.0,  # categorical, full strength
            "polarity": "positive",
            "classical_basis": basis,
            "provenance": {"source_section": "...", "extracted_at": "..."},
        })
    return edges

# Similar parsers for ASPECTS, AFFLICTS, SUPPORTS, CONJUNCT, DISPOSES,
# KARAKA_OF, ARUDHA_OF, DASHA_GIVES, NAKSHATRA_OF, DUAL_SYSTEM_DIVERGENCE,
# SEC_REFERENCES, RESONATES_WITH, CONTRADICTS_WITH, CO_OCCURS.
```

Critical:
- Every emitted edge MUST have source_node_id and target_node_id that exist in the `nodes` dict.
- Pass the loaded nodes dict in to every parser; if an edge references a missing node, log + skip
  (not silently emit an orphan).

Add unit tests in `__tests__/test_cgm_extractor.py` — at least 1 test per edge_type covering
happy path + 1 edge case (e.g., orphan source node, malformed line).

### §3.4 — Extend cgm_loader.py

Update edge-loader UPSERT to handle all 15 edge_types. Likely already generic on edge_type
(it's just a varchar field), but verify the loader doesn't have a whitelist that needs adding.

ON CONFLICT (edge_id) DO UPDATE SET clause should preserve existing edges if the new ingest
produces the same edge_id with same fields (idempotent re-ingest).

### §3.5 — Run CGM ingest

```bash
cd platform/python-sidecar
python -m pipeline.ingest_cgm \
  --source ../../025_HOLISTIC_SYNTHESIS/CGM_v9_0.md \
  --upsert
```

(Adapt to actual entry-point if named differently.)

### §3.6 — Orphan check (CRITICAL — AC.5)

```sql
SELECT COUNT(*) FROM l25_cgm_edges e
WHERE NOT EXISTS (SELECT 1 FROM l25_cgm_nodes n WHERE n.node_id = e.source_node_id)
   OR NOT EXISTS (SELECT 1 FROM l25_cgm_nodes n WHERE n.node_id = e.target_node_id);
```

MUST be 0. If > 0, HALT and dump all orphan edges to verification txt for triage. Do NOT proceed
to deploy.

### §3.7 — Post-ingest counts (AC.6 + AC.7)

```sql
SELECT COUNT(*) FROM l25_cgm_edges;
-- Expected ≥ 320 (target 339; ±5% tolerance).

SELECT edge_type, COUNT(*) FROM l25_cgm_edges GROUP BY edge_type ORDER BY 2 DESC;
-- All 15 edge_types must appear non-zero.
```

Capture both to verification txt.

### §3.8 — Sample edges per edge_type (AC.8)

```sql
WITH samples AS (
  SELECT DISTINCT ON (edge_type)
    edge_id, edge_type, source_node_id, target_node_id, strength, polarity, classical_basis,
    provenance::text
  FROM l25_cgm_edges
  ORDER BY edge_type, edge_id
)
SELECT * FROM samples;
```

Capture to verification txt. Eyeball: each sample should have populated classical_basis (≥80%
fill rate target).

### §3.9 — Re-chunk CGM nodes (AC.9)

```bash
cd platform/python-sidecar
python -m pipeline.chunk_cgm --upsert
```

Verify:
```sql
SELECT COUNT(*) FROM rag_chunks WHERE doc_type='cgm_node' AND is_stale=false;
-- Expected ≥ 365 (target 369 to mirror l25_cgm_nodes).
```

### §3.10 — cgm_graph_walk verification (AC.10)

Run an existing test that exercises graph walking:
```bash
cd platform
npm test -- cgm_graph_walk
```

Or a probe query in psql:
```sql
-- Find all edges within 2 hops of PLN.SATURN
WITH RECURSIVE walk AS (
  SELECT 'PLN.SATURN' AS node_id, 0 AS depth
  UNION ALL
  SELECT
    CASE WHEN e.source_node_id = w.node_id THEN e.target_node_id ELSE e.source_node_id END,
    w.depth + 1
  FROM walk w JOIN l25_cgm_edges e
    ON (e.source_node_id = w.node_id OR e.target_node_id = w.node_id)
  WHERE w.depth < 2
)
SELECT COUNT(DISTINCT node_id), COUNT(*) FROM walk;
```

Expected: many more nodes reachable than pre-W2-R3 baseline. Capture before/after diff.

### §3.11 — Build, test, deploy

```bash
cd platform
npm test 2>&1 | tail -10
# AC.11 — confirm baseline (account for W2-R1/W2-R2 sibling deltas if landed first)

bash platform/scripts/cloud_build_submit.sh
# AC.12 — capture revision name
```

### §3.12 — Live-deploy verification (AC.13)

Send 2 fresh multi-hop queries through Consume tab. Suggested:
1. "How does my Saturn affect my Mercury through aspects and house lordship?"
2. "Trace the Karaka relationships involving my Atmakaraka."

For each, capture:
- query_plans row showing classifier emitted graph_seed_hints
- cgm_graph_walk evidence in audit_events.tool_bundles
- answer text — should reference multi-step relationship chains, not just direct facts

### §3.13 — Update activation matrix (AC.14)

Edit `00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md`:

§7 — Update l25_cgm_edges count and rag_chunks cgm_node count, mark green.

Add §8 — CGM Edge_Types Breakdown:
```
| edge_type | count | source per CGM v9.0 |
|---|---|---|
| RULES_OVER | N | sign-lord + house-lord catalog |
| ASPECTS | N | Parashari graha drishti grid |
| ... | ... | ... |
```

### §3.14 — Status flip + log entry

- Flip `status: PENDING` → `status: COMPLETE`.
- Append per-brief entry to PROJECT_KARN_SESSION_LOG.md per §3.1.

## §4 — Closing summary template

```
KARN-W2-R3-CGM-FULL-EDGES closed.
- migration 030 applied: 4 indexes on l25_cgm_edges
- l25_cgm_edges: 126 → N edges (+M new across 15 edge_types)
- per-edge_type counts: RULES_OVER=A, ASPECTS=B, AFFLICTS=C, ... (full breakdown in verification txt)
- orphan check: 0 (preserved Pre-KARN-2 invariant)
- rag_chunks cgm_node: 234 → 369 (+135 new chunks for nodes added in Pre-KARN-2)
- cgm_graph_walk traversal: pre {N1 reachable, N2 edges} → post {N1' reachable, N2' edges}
- M1_M2_ACTIVATION_MATRIX.md §7 + new §8 added
- tests: pre N/13 → post N+M/13 (no new failures)
- Cloud Run revision: amjis-web-XXXXX-YYY
- 2 multi-hop live-deploy queries verified
- next pointer: W3-R1 chunker completion (UCN H3 splits) parallel; W3-R3 pattern expansion consumes new edges
```

## §5 — Halt-and-report checklist

- Pre-flight failure
- Migration 030 fails to apply
- Post-ingest orphan count > 0 (CRITICAL — fix extractor before proceeding)
- Post-ingest edge count < 280 (extractor undercount)
- Any edge_type has 0 rows (parser miss)
- classical_basis fill rate < 60% on any edge_type (incomplete extraction)
- Tests baseline drift > 2 failures
- Cloud Build failure
- cgm_graph_walk shows regression (fewer reachable nodes than baseline)

---

*End of CLAUDECODE_BRIEF_M2_B1_CGM_FULL_EDGES. Predecessor: Pre-KARN-2 + KARN-W1-R1. Wave 2.*
