---
artifact: L4_PHALA_STAGED_FIX_SPECS_v1_0.md
canonical_id: L4_PHALA_STAGED_FIX_SPECS
version: 1.0
status: BLOCKED_ON_L2
authored_by: Claude Code 2026-06-27
purpose: >
  Exact staged change specs for the 3 L2-dependent L4 fixes from
  L4_PHALA_UPSTREAM_COMPLETENESS_FIX_BRIEF_v1_0.md §B. Do NOT apply these
  until L2 Phase 1–3 (canonical CDLM vocab + sound CGM + sound embeddings) is proven.
  Apply in a single L4 re-fix pass immediately after L2 is confirmed sound.
unblock_condition: L2_BODHA_REMEDIATION_PHASE_PLAN Phases 1–3 merged and production verified.
---

# L4 Phala — Staged Change Specs (BLOCKED ON L2)

These specs are written ready-to-apply. Do NOT commit them live until L2 is sound.
Each spec is self-contained: file path, exact old code, exact new code, verify step.

---

## Spec B.1 — ph_sankrama: vocabulary join after L2 CDLM canonicalization

**File:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_sankrama.py`

**Blocking condition:** `bodha_cdlm_cells.domain_row` shares canonical vocabulary with
`phala_anchors.domain` after L2 CDLM Phase 1 fix lands.

**Confirmed mismatch (2026-06-27 live data):**

| bodha_cdlm_cells.domain_row | phala_anchors.domain | Status |
|---|---|---|
| career | career | ✓ match |
| health | health | ✓ match |
| relationship | relationship | ✓ match |
| spirituality | spiritual | ✗ MISMATCH — causes zero spillovers for spiritual anchors |
| character | (absent) | ✗ NO ANCHOR — character has CDLM cells but no phala_anchors |
| (absent) | transition | ✗ NO CDLM — transition anchors never get spillovers |

**Root cause:** The equality join `c.domain_row == domain` (line 79) is correct code
against correct vocabularies. The mismatch is entirely in L2's CDLM writer emitting
`spirituality` while the L3/L4 pipeline uses `spiritual`. Fix at L2 source; do NOT add
an L4 normalization map (native decision 2026-06-25).

**Post-L2 verification step (DO THIS FIRST before any code change):**

```sql
-- Run after L2 CDLM Phase 1 rebuild. Both sets must be identical for the fix to land clean.
SELECT DISTINCT domain_row FROM bodha_cdlm_cells WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
EXCEPT
SELECT DISTINCT domain FROM phala_anchors WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
-- Expected: 0 rows. If any rows appear, the L2 vocab fix is incomplete — STOP.
```

**If verification passes (0 rows):** No code change to ph_sankrama.py is needed.
The equality join already works; the L2 fix resolves it. Rebuild ph_sankrama and check
spillover-by-domain distribution:

```sql
-- After rebuild, career should NOT dominate at 96.5%.
SELECT source_domain, COUNT(*) as spillovers
FROM phala_sankrama
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
GROUP BY source_domain ORDER BY spillovers DESC;
-- Expected: career ≤ 40% of rows; spiritual + health + relationship all non-zero.
```

**If residual mismatch remains** (e.g. L3-derived suffixes like `career_advancement`
appear in phala_anchors.domain): add a thin normalization only at the JOIN site, reading
the L2 canonical domain list — NOT a separate L4-only map:

```python
# ph_sankrama.py — add near top of run() only if post-L2 mismatch persists:
_CANONICAL_DOMAIN_NORM = {
    # populated from bodha_cdlm_cells.domain_row DISTINCT after L2 rebuild
    # e.g. 'career_advancement': 'career' if L3 suffixes remain
}

# In the matching_cells filter (line 77–79), change to:
matching_cells = [
    c for c in cdlm_cells
    if _CANONICAL_DOMAIN_NORM.get(domain, domain) == c.domain_row
    and c.net_linkage_strength >= _LINKAGE_THRESHOLD
]
```

---

## Spec B.2 — ph_nimitta Axis 3: wire CGM paths loader (remove `return {}`)

**File:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py`

**Blocking condition:** `bodha_cgm_paths` is rebuilt sound after L2 CGM fix
(all nodes have real strength_score and degree_in/degree_out > 0; edges non-degenerate).

**Current bug:** `_load_cgm_meta` (lines 241–283) fetches top-10 paths from
`bodha_cgm_paths` then discards them with `return {}` (line 275). Comment says
"no signal→path mapping available." Result: `causal_chain_jsonb` is NULL on every anchor.

**Schema fact:** `bodha_cgm_paths` has no `signal_id` FK. Mapping is via
`bodha_cgm_nodes.node_subject` (the graha name) → link to signal domain.
The fix uses a two-step join: signal_meta → graha → node → paths.

**Schema note (confirmed 2026-06-27):** `bodha_msr_signals` has no `graha_primary` column.
The cleanest bridge is chart-level: return the top paths for the entire chart, keyed by
`from_graha` (planet name from `bodha_cgm_nodes.node_subject`). In `_build_ctx`, all signals
receive the same chart-level CGM context (the causal graph is chart-wide, not signal-specific).
This is correct: `causal_chain_jsonb` documents the chart's causal structure, not a per-signal path.

**Exact change to `_load_cgm_meta`:**

```python
def _load_cgm_meta(self, conn, signal_ids: list[str]) -> dict[str, dict]:
    """Load top CGM paths for the chart (Axis 3 causal chain).

    bodha_cgm_paths has no signal_id FK; paths are chart-wide (planets as nodes).
    Returns a single '_chart_paths' key with the top paths, shared across all signals.
    After L2 CGM is sound (non-degenerate strength + edges), this populates
    causal_chain_jsonb for every anchor derived from this chart.
    """
    if not signal_ids:
        return {}
    try:
        with conn.cursor() as sp:
            sp.execute("SAVEPOINT sp_nimitta_cgm")
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT chart_id FROM bodha_msr_signals WHERE signal_id = ANY(%s::uuid[]) LIMIT 1",
                (signal_ids,),
            )
            chart_row = cur.fetchone()
            if not chart_row:
                with conn.cursor() as sp2:
                    sp2.execute("RELEASE SAVEPOINT sp_nimitta_cgm")
                return {}
            chart_id = chart_row['chart_id']

            cur.execute(
                """
                SELECT p.path_id, p.path_length, p.path_strength,
                       p.is_final_dispositor, p.path_label_human,
                       n_from.node_subject AS from_graha,
                       n_from.betweenness_centrality AS centrality
                FROM bodha_cgm_paths p
                JOIN bodha_cgm_nodes n_from ON n_from.node_id = p.from_node_id
                                            AND n_from.chart_id = p.chart_id
                WHERE p.chart_id = %s
                ORDER BY p.path_strength DESC, p.path_length ASC
                LIMIT 20
                """,
                (chart_id,),
            )
            path_rows = cur.fetchall()

        with conn.cursor() as sp:
            sp.execute("RELEASE SAVEPOINT sp_nimitta_cgm")

        if not path_rows:
            return {}

        # Chart-level context: distribute to all signals via '_chart_paths' sentinel key.
        top = path_rows[0]
        chart_ctx = {
            'path_ids': [str(r['path_id']) for r in path_rows[:5]],
            'centrality': float(top.get('centrality') or 0),
            'root_graha': top.get('from_graha'),
        }
        # Return the same chart context for every signal in the batch.
        return {sid: chart_ctx for sid in signal_ids}

    except Exception as exc:
        try:
            with conn.cursor() as sp:
                sp.execute("ROLLBACK TO SAVEPOINT sp_nimitta_cgm")
        except Exception:
            pass
        logger.debug("ph_nimitta: cgm_meta load skipped: %s", exc)
        return {}
```

**Post-apply verification (on non-native 1c826d5a after L2 rebuild):**

```sql
SELECT COUNT(*) as total, COUNT(causal_chain_jsonb) as non_null_axis3
FROM phala_anchors WHERE chart_id = '1c826d5a-...';
-- Expected: non_null_axis3 > 0 (was 0 before fix). Aim for > 20% coverage.
```

---

## Spec B.3 — ph_nimitta Axis 5: wire real nearest-neighbor embeddings

**File:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py`

**Blocking condition:** `bodha_signal_embeddings` is rebuilt sound after L2 embeddings
fix (embeddings in actual msr_signals cluster, not degenerate).

**Current bug:** `_load_precedent_refs` (lines 317–350) queries
`bodha_signal_embeddings` with `WHERE signal_id = ANY(%s::uuid[])` and no ORDER BY
cosine similarity. For each match it returns `{'nearest_signal_ids': [sid]}` — the
signal as its own neighbor. Result: `precedent_refs_jsonb` has only self-reference on
every anchor; ~500–2,000 real neighbors per chart lost.

**Schema facts (confirmed 2026-06-27):**
- `bodha_signal_embeddings.embedding_vec`: `vector(768)`
- HNSW index: `bse_embedding_hnsw` on `(embedding_vec vector_cosine_ops)` — supports `<=>`
- Unique constraint: one embedding per `signal_id`

**Exact change to `_load_precedent_refs`:**

```python
def _load_precedent_refs(self, conn, chart_id: str, signal_ids: list[str]) -> dict[str, dict]:
    """Axis 5: nearest embedding neighbors (top-3 per signal via HNSW cosine search)."""
    if not signal_ids:
        return {}
    try:
        with conn.cursor() as sp:
            sp.execute("SAVEPOINT sp_nimitta_prec")
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            # Lateral join: for each target signal, find 3 nearest neighbors by cosine distance.
            # HNSW index (bse_embedding_hnsw, vector_cosine_ops) accelerates the <=> scan.
            # Exclude self (signal_id != target.signal_id).
            cur.execute(
                """
                SELECT target.signal_id AS target_id,
                       neighbor.signal_id AS neighbor_id,
                       (target.embedding_vec <=> neighbor.embedding_vec) AS cosine_dist
                FROM bodha_signal_embeddings target
                JOIN LATERAL (
                    SELECT e2.signal_id
                    FROM bodha_signal_embeddings e2
                    WHERE e2.chart_id = %s
                      AND e2.signal_id != target.signal_id
                    ORDER BY target.embedding_vec <=> e2.embedding_vec
                    LIMIT 3
                ) neighbor ON true
                WHERE target.chart_id = %s
                  AND target.signal_id = ANY(%s::uuid[])
                ORDER BY target.signal_id, cosine_dist ASC
                """,
                (chart_id, chart_id, signal_ids),
            )
            result: dict[str, dict] = {}
            for r in cur.fetchall():
                tid = str(r['target_id'])
                if tid not in result:
                    result[tid] = {'nearest_signal_ids': [], 'precedent_dates': []}
                result[tid]['nearest_signal_ids'].append(str(r['neighbor_id']))

        with conn.cursor() as sp:
            sp.execute("RELEASE SAVEPOINT sp_nimitta_prec")
        return result
    except Exception as exc:
        try:
            with conn.cursor() as sp:
                sp.execute("ROLLBACK TO SAVEPOINT sp_nimitta_prec")
        except Exception:
            pass
        logger.debug("ph_nimitta: precedent_refs load skipped: %s", exc)
        return {}
```

**Performance note:** The lateral join fires the HNSW index once per target signal.
For a chart with ~200 signals in the batch, this is ~200 HNSW lookups. Each HNSW lookup
is sub-millisecond. Total expected latency: < 200ms for a full chart batch.
If the chart has > 500 signals in one batch, consider chunking (batch in groups of 200).

**Post-apply verification (on non-native 1c826d5a after L2 rebuild):**

```sql
-- Each non-self precedent_refs should have ≥ 1 real neighbor
SELECT COUNT(*) as anchors,
       COUNT(CASE WHEN jsonb_array_length(precedent_refs_jsonb->'nearest_signal_ids') > 0 THEN 1 END) as has_neighbors
FROM phala_anchors WHERE chart_id = '1c826d5a-...';
-- Expected: has_neighbors ≈ anchors (most anchors should have real neighbors now).
-- Before fix: has_neighbors was 0 (all self-reference or empty).
```

---

## Application sequence (when L2 is sound)

1. Confirm L2 Phase 1–3 merged and verified on 1c826d5a.
2. Run Spec B.1 post-L2 vocab verification SQL. If 0 rows — no code change needed.
   If rows remain — apply B.1 normalization patch.
3. Verify `bodha_msr_signals.graha_primary` column exists (B.2 pre-apply gate).
4. Apply B.2 (ph_nimitta Axis 3) and B.3 (ph_nimitta Axis 5) — these are always needed
   regardless of B.1 outcome.
5. Trigger ph_nimitta + ph_sankrama rebuild on 1c826d5a. Run B.1 + B.2 + B.3 verify SQLs.
6. If all pass — commit, then rebuild on native 482012f1 (read-only check only).
