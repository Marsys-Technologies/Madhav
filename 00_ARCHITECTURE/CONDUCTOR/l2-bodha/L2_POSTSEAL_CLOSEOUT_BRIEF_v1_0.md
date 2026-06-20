# L2 Bodha — Post-Seal Closeout (5 items: cockpit + embeddings + merge + re-verify + corpus gaps)

**Paste as the prompt in Claude Code (Antigravity). Closes ALL outstanding L2 post-seal items so the Nirmāṇa
cockpit is fully reflective and the layer is clean before L3. Items are INDEPENDENT — do them in the order below
(C1 cockpit first: highest visibility, smallest fix). Verify against the live repo + prod. Data plane = prod via
Cloud SQL proxy (5433).**

---

## C1 — THE COCKPIT FIX (the root cause is DIAGNOSED — `is_active` was never set)
**ROOT CAUSE (verified in code):** the cockpit stats route (`platform/src/app/api/cockpit/stats/route.ts`) loads
assets `WHERE is_active = true` (line ~244) AND renders `is_active === false` as `not_migrated` (line ~19, the
grey/empty bar). **Migration 326 set `catalog_status='CURRENT'` but NEVER set `is_active`** — so the 9 bo_* assets
(and possibly bo_* rows from mig 325) are excluded or shown as empty bars DESPITE 139,531 real rows. This is the
exact L1 cockpit trap (is_active=false omits assets from the stats route).

**FIX — a tiny surgical migration 327** (`platform/migrations/327_l2_bodha_cockpit_is_active.sql`):
```sql
BEGIN;
UPDATE asset_registry SET is_active = true
WHERE asset_id IN ('bo_laksana','bo_sangati','bo_karanajala','bo_bimba','bo_samskara',
                   'bo_samvada','bo_upaya','bo_drishti','bo_anveshana','bo_pramana_mapa');
COMMIT;
```
Then VERIFY on prod:
1. `SELECT asset_id, is_active, catalog_status, target_floor FROM asset_registry WHERE layer='bodha' ORDER BY sort_order;`
   → all 10 bo_* : is_active=true, catalog_status=CURRENT, target_floor=achieved.
2. Hit `/api/cockpit/stats?chart_id=482012f1-710e-4a25-994a-93821f5871aa` → all 9 bo_ assets present, status `lit`
   (count_sql returns rows > 0), progress bars populated (actualRows vs target_floor).
3. **Cockpit visual check (Chrome MCP on localhost:3000, NOT prod url until post-deploy):** the Nirmāṇa cockpit
   Bodha layer shows all 9 assets lit with full progress bars. (Per memory: trace from page.tsx/registry down —
   the v2 tree is CockpitShell → DataAssetsView → LayerPanel reading /api/cockpit/registry; it does NOT use
   asset_names.ts.) If a count is 0/grey, check that asset's count_sql executes (the $1 binding: stats line ~118
   binds [chartId] only when /\$1/ is in the count_sql — confirm each bo_ count_sql contains $1).
4. **Cross-check the OTHER gaps the native sees:** any L0/L1/ga_ asset showing not_migrated/empty → same is_active
   diagnosis; if its rows>0 on prod but is_active=false, set is_active=true (extend mig 327). Report every asset
   that was inactive-despite-built. Goal: EVERY cockpit cell reflects reality (lit/under-floor-badge/service_ok),
   ZERO false not_migrated.

## C2 — REAL EMBEDDINGS (bo_samskara: placeholder_hash_v1 → real Vertex) — highest-value gap
**THE GAP:** bo_samskara shipped `placeholder_hash_v1` (SHA-256→random 768-dim) — semantically OPAQUE. Semantic
retrieval + the signal↔classical bridge DON'T work (the hash scatters meaning). The input-text plumbing already
exists (`_build_input_summary`); only the hash→model line changes.
**FIX (per CLAUDECODE_BRIEF_BO_SAMSKARA + the storage embedding protocol):**
1. Wire the shared embedding-config constant (EMBEDDING_MODEL=`text-multilingual-embedding-002`, DIM=768) — the
   SAME pinned module bg_texts uses (create it if W0 didn't); bo_samskara imports it (no hardcoded model).
2. Replace `_text_to_deterministic_vec` (the hash) with a real Vertex `embed_content` call over the signal's
   `signal_summary_text` (reuse the bg_texts genai-client path; batch; rate-limit). Stamp embedding_model +
   embedding_model_version per row.
3. Re-run bo_samskara for 482012f1 (delete-then-insert; idempotent) — count stays 66,738 (1:1 with MSR).
4. **Cross-layer consistency CI check:** every populated embedding column across L0 (classical_text_chunks) + L2
   (bodha_signal_embeddings) = same model+version+dim → CI fails on mismatch.
5. **Prove real semantics (the test the hash fails):** two astrologically-related signals (e.g. two career-
   weakness signals) are cosine-NEAR; the signal↔classical bridge (`query_signal_to_classical`) returns the
   relevant classical_text_chunks. `[verify-against: prod]`
6. classical_chunks (stale, empty, no reader) — leave in place (already diagnosed; no action).
**Deterministic-first note:** a pinned Vertex embedding IS a deterministic transform (same text+model→same vector)
— allowed; it is NOT a generative LLM. (Native-ratified.)

## C3 — MERGE PR #302
1. Confirm CI green on `feature/l2-bodha`; the Vimarśaka-RED fix commits (e9b984de + 203597c5) + mig 326 (+327, C1)
   + the C2 embedding fix are all on the branch.
2. Note the branch also carries a post-seal modernization/cleanup arc (47392feb/5464919e/1ef4aafc) — confirm that's
   intended in the merge (it's docs/hygiene).
3. Merge PR #302 to main; push; confirm the Cloud Run deploy picks up the merge SHA (verify the revision per
   [[feedback-verify-cloud-run-revision-before-chrome-probe]] before any prod cockpit probe).

## C4 — §C PROD RE-VERIFY of the Vimarśaka fix (the failure-path proof)
The conn.commit removal must be DATA-NEUTRAL + the savepoint must actually work:
1. Re-run the 6 fixed assets (bo_laksana/sangati/samskara/upaya/drishti/anveshana) for 482012f1 → counts UNCHANGED
   (MSR 66,738, embeddings 66,738 [now real, C2], discoveries 1,411, anomalies 4,359, lenses 60; trap1=0; FORENSIC 7/7).
2. **Failure-path test:** force a bad row in one batch → confirm the per-row SAVEPOINT skips ONLY that row, the
   sub-step otherwise commits via the orchestrator, and the connection transaction survives (no cascading abort).
   This is the guarantee that was broken; prove it fixed.

## C5 — F2 REMEDY-CORPUS GAPS + the chakra gap (L0-expansion; lowest urgency)
The tracked gaps: brahma_remedy_corpus lacks nakshatra-key / vastu-direction (0 rows) / body-part-key remedials;
no chakra table. These are L0-corpus-EXPANSION items, NOT build bugs. Disposition:
1. Confirm bo_upaya §R5 correctly FLAGS them as `remedy_corpus_gap` (honest gap, never invented) — it should already.
2. Record them in a tracked L0 follow-on register (OPEN_ITEMS or a BRAHMA_DEFERRED_FEATURES entry) for a later L0
   corpus-expansion pass. Do NOT block on them; do NOT fabricate remedies. (Decide with the native whether to
   expand the L0 corpus now or defer — default: defer, tracked.)

## SEQUENCE + LANDING
C1 (cockpit migration 327 + verify) → C2 (real embeddings + re-run) → C4 (re-verify, now incl. real embeddings) →
C3 (merge) → C5 (track). Commit each on `feature/l2-bodha`; CI green per step. Update L2_BODHA_CLOSE §10 with the
closeout record (cockpit fixed, real embeddings landed, fix re-verified, gaps tracked). The native reviews the
fully-lit cockpit retrospectively.

## HARD STOPS
- A bo_ count_sql returns 0 on prod despite rows in the table → the count_sql / $1-binding is wrong → fix the
  count_sql, do NOT mask it.
- Real embeddings change the MSR/embedding count → STOP (must stay 66,738 1:1).
- prod ≠ merge SHA when probing the cockpit → wait for the deploy (the phantom-bug trap).

**Begin: C1 — author migration 327, apply, verify the cockpit is fully reflective. Go.**
