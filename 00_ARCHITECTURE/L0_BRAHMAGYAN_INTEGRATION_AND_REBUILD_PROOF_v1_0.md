---
artifact: L0_BRAHMAGYAN_INTEGRATION_AND_REBUILD_PROOF
canonical_id: L0_INTEGRATION_REBUILD_PROOF
version: 1.0
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
amended_by: Racayitā (Build-Guarantor gap-author) 2026-06-08 — FLOORS dict confirmed HELD (no floor changed); migration-band 181-191 note added to §4
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Brahmagyan unified build — integration, Vimarśaka-Ω, delete-and-rebuild proof
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1)
parent_plan: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md
target_floor: N/A (the final gate — gates the whole campaign)
dependencies: [ALL 12 writers + orchestrator fixes]
llm_cost: $0
document_number: 15 of 15
---

# L0 Brahmagyan — Integration, Vimarśaka-Ω, and Delete-and-Rebuild Proof

> **The final gate.** After all 12 writers + the orchestrator fixes execute, this brief verifies the ONE outcome: *native presses "Build" at the Brahmagyan layer → all 12 tiles light at floor, deterministically, with full citation and FK integrity — and the whole layer can be deleted and rebuilt bit-for-bit.* If Vimarśaka-Ω fails any check, the campaign is NOT sealed and does NOT merge.

## §0 — Where this runs in the campaign

This is the last step the executor performs on `feature/l0-unified-build`, after Documents 2-14 are implemented and each asset's per-asset Vimarśaka has passed. It produces `platform/scripts/vimarsaka/vimarsaka_omega.py` (the aggregate gate) and the rebuild-proof runbook. Only after Vimarśaka-Ω PASSES does the executor commit + open the single campaign PR.

## §1 — Pre-conditions (all must hold before running Ω)

1. Orchestrator fixes (Doc 2) merged into the branch; Vimarśaka-FIX 6/6 PASS.
2. All 12 writers registered (`discover_all()` lists all 12).
3. Each asset's per-asset Vimarśaka (Docs 3-14 §7) PASS or CONDITIONAL (manual-PDF gaps only).
4. `depends_on` edges set per the writer briefs (the full DAG, not just migration 179's partial set — §4).

## §2 — Vimarśaka-Ω checks (the 9 acceptance criteria, programmatic)

Author `platform/scripts/vimarsaka/vimarsaka_omega.py`. Each check returns `(ok, message)`; ALL must pass.

### Ω.1 — Every writer registered
`discover_all()` then assert all 12 asset_ids in `list_writers()`.

### Ω.2 — Every asset ≥ floor
```python
FLOORS = {
  'bg_ephemeris':825084, 'bg_reference':1450, 'bg_texts':14000, 'bg_ontology':700,
  'bg_text_index':400, 'bg_rules':3000, 'bg_remedies':800, 'bg_concordance':800,
  'bg_yogas':250, 'bg_dasha_systems':15, 'bg_doshas':50, 'bg_compendium_index':3000,
}
# For each, run the asset_registry.count_sql and assert >= floor.
# CONDITIONAL allowance: bg_texts / bg_text_index / bg_rules / bg_concordance / bg_compendium_index
# may be below floor IFF the shortfall traces to absent MANUAL PDFs (texts 11/12/13) — in that case
# Ω reports CONDITIONAL-PASS with the upload list, NOT a hard fail (operator action).
```

### Ω.3 — Every row source-cited
For each backing table, assert zero rows with NULL citation. Citation column varies: `source_citation` (reference_*, ephemeris, ontology, remedies), `classical_citations`/`source_chunk_ids` (yogas/doshas/dasha_systems), `source_chunk_ids` (concordance, compendium), `classical_citation` (glossary), `verse_ref`+`text_id` (rules). `reference_topic_tags` is EXEMPT (authored vocabulary). Use the per-asset citation rule from each brief's §7.

### Ω.4 — FK integrity (the full set, holistic design §4.1 + master plan §5.4)
```sql
-- Each of these MUST return zero rows:
-- (a) reference planet/sign/karaka/upagraha ids resolve in brahma_ontology
SELECT planet_id FROM reference_planets EXCEPT SELECT canonical_id FROM brahma_ontology;
SELECT upagraha_id FROM reference_upagrahas EXCEPT SELECT canonical_id FROM brahma_ontology;
-- (b) catalog ids resolve in brahma_ontology with correct entity_class
SELECT canonical_id FROM brahma_yoga_catalog EXCEPT SELECT canonical_id FROM brahma_ontology WHERE entity_class='yoga';
SELECT canonical_id FROM brahma_dosha_catalog EXCEPT SELECT canonical_id FROM brahma_ontology WHERE entity_class='dosha';
SELECT canonical_id FROM brahma_dasha_systems EXCEPT SELECT canonical_id FROM brahma_ontology WHERE entity_class='dasha_system';
-- (c) pointer tables resolve in their catalogs
SELECT canonical_id FROM reference_yogas EXCEPT SELECT canonical_id FROM brahma_yoga_catalog;
SELECT canonical_id FROM reference_doshas EXCEPT SELECT canonical_id FROM brahma_dosha_catalog;
SELECT canonical_id FROM reference_dasha_systems EXCEPT SELECT canonical_id FROM brahma_dasha_systems;
-- (d) sutravali_rules.yoga_canonical_id (non-null) resolves in brahma_yoga_catalog
SELECT yoga_canonical_id FROM sutravali_rules WHERE yoga_canonical_id IS NOT NULL
  EXCEPT SELECT canonical_id FROM brahma_yoga_catalog;
-- (e) concordance source_chunk_ids[] resolve in classical_text_chunks (unnest + EXCEPT)
-- (f) compendium text_id resolves; topic_id resolves in reference_topic_tags
```

### Ω.5 — No duplicate (entity_class, canonical_id) in brahma_ontology
`SELECT canonical_id, count(*) FROM brahma_ontology GROUP BY canonical_id HAVING count(*)>1` → empty. (PK on canonical_id should already guarantee this; assert anyway.)

### Ω.6 — Single-source-of-truth (no data in two tables)
Assert the catalogs' doctrinal columns don't appear in ontology (ontology descriptions ≤160 chars, no JSON), and the pointer tables carry ONLY (id, name, category/school) — no doctrine. Spot-check: `brahma_ontology` has no `formation_rule`-like column populated.

### Ω.7 — Layer-level Build triggers all 12 in dependency order
Programmatic: call `resolveBuildPlan({scope:'layer',scope_target:'brahmagyan',action:'build',...})` against the live registry → assert the plan contains all 12, topo-ordered (bg_ontology before yogas/doshas/dashas; bg_texts before text_index/rules/concordance/compendium; bg_reference+bg_ontology before bg_yogas). Reuse the Doc 2 §6 test fixture extended to all 12.

### Ω.8 — Cockpit shows all 12 lit at floor
After a layer Build for the native chart, `SELECT asset_id, state, rows_written FROM asset_throughput WHERE asset_id LIKE 'bg_%'` → all 12 `state='lit'`, `rows_written ≥ floor`.

### Ω.9 — Delete-and-rebuild bit-for-bit proof (§3)
Run the §3 runbook; assert post-rebuild counts match pre-rebuild within ±0.1% and per-asset content hashes match.

## §3 — Delete-and-rebuild proof runbook

> This is the integrity proof the native asked for: the whole layer can be deleted and reconstructed deterministically.

```bash
# 0. Snapshot pre-rebuild state (counts + content hashes per asset)
python platform/scripts/vimarsaka/snapshot_l0.py > /tmp/l0_pre.json
# snapshot_l0.py: for each backing table, record count(*) and md5(string_agg(row::text ORDER BY pk))

# 1. CLEAR the Brahmagyan layer (super_admin, typed-confirmation = native subject name)
#    via the cockpit "Clear instrument" at layer scope='layer', scope_target='brahmagyan'
#    (clear/execute/route.ts: DELETE FROM each global target_table; resets throughput to dormant)
#    EXCEPTION: bg_ephemeris (825K rows) — confirm with native whether to include it in the clear.
#    If included, the rebuild re-derives it via build_ephemeris (multi-minute Swiss-Ephemeris run);
#    if excluded, note it in the proof (the ephemeris wrapper no-ops on the present data).

# 2. Confirm all 12 tables empty (or ephemeris retained per native choice)
psql_prod -c "SELECT 'brahma_ontology', count(*) FROM brahma_ontology UNION ALL SELECT 'brahma_yoga_catalog', count(*) FROM brahma_yoga_catalog ..."  # expect 0s

# 3. BUILD at layer scope — the single click
curl -s -X POST -b "__session=$NATIVE_SESSION" -H "Content-Type: application/json" \
  -d "{\"chart_id\":\"$NATIVE_CHART\",\"scope\":\"layer\",\"scope_target\":\"brahmagyan\",\"action\":\"build\"}" \
  https://madhav.marsys.in/api/cockpit/runs | jq .
#    The orchestrator dispatches the topo-sorted plan; all 12 writers run in dependency order.

# 4. Wait for completion; snapshot post-rebuild
python platform/scripts/vimarsaka/snapshot_l0.py > /tmp/l0_post.json

# 5. Compare
python platform/scripts/vimarsaka/compare_snapshots.py /tmp/l0_pre.json /tmp/l0_post.json
#    PASS iff: per-asset count delta ≤ ±0.1% AND content hash identical for every deterministic asset.
#    (Embedding-bearing chunks: compare chunk COUNT + content_sha256 set, not raw embedding floats —
#     embeddings are deterministic at a pinned model version but float-formatting may vary; hash the
#     content_sha256 set instead.)
```

**Hard AC:** step 5 PASS for all 12 assets. This is criterion 9 of master plan §5 and the native's "delete and rebuild" requirement.

## §4 — DAG completeness check (do this BEFORE Ω.7)

> **Migration band (Racayitā amendment, 2026-06-08):** the campaign's migrations are pre-assigned **181–191** — 181 orchestrator (pre-existing), 182 reference, 183 ontology, 184 yogas, 185 dasha_systems, 186 doshas, 187 text_index, 188 rules, 189 remedies, 190 concordance, 191 compendium-dedup. Re-confirm the live ceiling (`ls platform/supabase/migrations/ | grep -E '^[0-9]' | sort -n | tail -1`) before applying; if other concurrent workstreams have consumed 187/188 (eval §3.2 flag), renumber sequentially from the true ceiling and record the mapping. Ω.2 FLOORS are **HELD** — no floor changed in the amendment pass.

Migration 179 set `depends_on` for only 4 assets. The writer briefs each add their edges. Confirm the FULL DAG is in `asset_registry.depends_on`:

```sql
SELECT asset_id, depends_on FROM asset_registry WHERE layer='brahmagyan' ORDER BY sort_order;
-- Expected edges (assert present):
--   bg_reference        → [bg_ontology]
--   bg_yogas            → [bg_ontology, bg_texts]
--   bg_dasha_systems    → [bg_ontology]
--   bg_doshas           → [bg_ontology]
--   bg_text_index       → [bg_texts, bg_reference]
--   bg_rules            → [bg_texts, bg_ontology, bg_yogas, bg_dasha_systems]
--   bg_remedies         → [bg_ontology, bg_doshas] (+bg_texts if §3.3 sweep used)
--   bg_concordance      → [bg_texts, bg_text_index, bg_reference, bg_rules]
--   bg_compendium_index → [bg_texts, bg_text_index, reference_topic_tags]
--   bg_ephemeris, bg_texts, bg_ontology → [] (Tier 0/2 roots)
```
If any edge is missing, the topo-sort may dispatch a writer before its dependency → that writer's FK validation fails. Fix the `depends_on` before Ω.7.

## §5 — The single campaign PR

After Vimarśaka-Ω PASS:

```bash
git add -A && git commit -m "feat(l0): Brahmagyan unified build — orchestrator fixes + 12 writers + Vimarśaka-Ω

Delivers the outcome: press Build at the Brahmagyan layer → all 12 L0 assets
populate to/beyond floor, deterministically, source-cited, FK-intact; the layer
deletes and rebuilds bit-for-bit.

Orchestrator (Doc 2): discover_all() wired; global_runner reconciled; NULL-safe
  global throughput (migration 181); layer topo-dispatch test.
Writers (Docs 3-14): bg_ephemeris, bg_reference (15 tables), bg_ontology (≥700),
  bg_texts (15 texts/≥14k chunks), bg_text_index, bg_rules (≥3k), bg_remedies (≥800),
  bg_concordance, bg_yogas (≥250), bg_dasha_systems (18), bg_doshas (≥58),
  bg_compendium_index (≥3k). ZERO LLM (embeddings only, bg_texts).
Vimarśaka-Ω: 9/9 PASS. Delete-and-rebuild proof: PASS (±0.1%).

Parent: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md
Design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1)"
git push -u origin feature/l0-unified-build
gh pr create --base main --head feature/l0-unified-build \
  --title "feat(l0): Brahmagyan unified build — 12 writers + orchestrator + Vimarśaka-Ω"
# VERIFY merge per [[pr-quality-gate-is-not-a-merge]]: gh pr view N --json mergeCommit
```

## §6 — Post-merge native verification (the proof the native runs)

1. Confirm fresh Cloud Run revision.
2. Open the cockpit Brahmagyan layer → all 12 tiles `lit` with row counts ≥ floor.
3. Click "Clear instrument" at Brahmagyan layer (super_admin, typed confirmation) → tiles go dormant, tables empty.
4. Click "Build" at Brahmagyan layer → watch all 12 transition dormant → building → lit in dependency order, no manual intervention.
5. Re-run `vimarsaka_omega.py` against prod → 9/9 PASS.

After step 5 PASS, **L0 Brahmagyan is sealed.** Author memory `[[l0-brahmagyan-unified-build-sealed]]` with the PR number, Vimarśaka-Ω results, and the per-asset final counts. Update `CURRENT_STATE`, `SESSION_LOG`, and the master plan §4 status table (all 15 DONE).

## §7 — Hard stops

- Any Ω check hard-fails (not CONDITIONAL on manual PDFs) → do NOT merge; fix the failing asset's writer, re-run Ω.
- Delete-and-rebuild delta > ±0.1% on any asset → a writer is non-deterministic (random ids, unpinned embedding model, LLM leak); find and fix it. This is the integrity guarantee; it cannot be waived.
- Manual-PDF gaps (texts 11/12/13) → CONDITIONAL-PASS allowed for the corpus-dependent assets, with the upload list surfaced to native as an operator action; the campaign may seal with those assets at CONDITIONAL and reach full floor after native uploads + a re-build. Document this clearly in the PR.

---

*End of integration + rebuild proof (Document 15 of 15) — campaign complete.*
