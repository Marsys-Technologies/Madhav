---
artifact: CLAUDECODE_BRIEF_L3_KALA_FINAL_CLOSE_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L3_KALA_FINAL_CLOSE
version: 1.0
status: AUTHORED — the final actions to perfectly close L3 Kāla
executor: Claude Code in Antigravity — commands embedded
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
HARD_CONSTRAINT: >
  Code + metadata only. The ONLY data-affecting action is the native clicking Rebuild→Kāla on
  the Nirmāṇa tracker (Step 5), which the native does. No writer is executed by Claude Code; the
  back-fill migration (Step 3) INSERTs asset_registry rows idempotently (registry metadata, NOT
  chart data) and must be safe-by-construction (ON CONFLICT DO NOTHING).
verified_state_2026_06_21:
  - PR #347 (ka_tulana buildable) = OPEN, NOT yet merged; branch fix/l3-ka-tulana-buildable is BEHIND main
  - CI fail-loud = ALREADY on main (deploy.yml has ::error:: + exit 1)
  - migration 343 number used TWICE across roots (platform/migrations/343_retire... AND
    supabase/migrations/343_ka_tulana...) — NOT a collision (migrate.ts dedups by FILENAME,
    applies both) but cosmetically ugly; optional renumber to 344
  - ka_* asset_registry rows + depends_on = in NO migration (governance gap CONFIRMED; zero ka_ INSERTs)
---

# L3 KĀLA — FINAL CLOSE-OUT

Five steps. Steps 1–4 are Claude Code (code + metadata). Step 5 is the native on the tracker.
After all five: L3 Kāla is perfectly, reproducibly closed.

═══════════════════════════════════════════════════════════════════════
STEP 1 — Rebase + merge PR #347 (ka_tulana buildable)
═══════════════════════════════════════════════════════════════════════
PR #347 is open but its branch is BEHIND main (missing L5 manifest, governance, ga_yoga fixes).
Rebase before merge.

```bash
git checkout main && git pull --ff-only origin main
git checkout fix/l3-ka-tulana-buildable
git rebase main          # resolve any conflicts (likely none — disjoint files)
# OPTIONAL TIDY: the migration is supabase/migrations/343_ka_tulana_has_writer.sql, and
# platform/migrations/343_retire_build_dependencies_ts_routes.sql already uses 343.
# They do NOT collide (migrate.ts dedups by filename, applies both), but to avoid two "343"s:
git mv platform/supabase/migrations/343_ka_tulana_has_writer.sql \
       platform/supabase/migrations/344_ka_tulana_has_writer.sql 2>/dev/null || true
# re-verify the migration is metadata-only (asset_registry has_writer/asset_type; NO chart table):
grep -iE "INSERT|UPDATE|TABLE|chart_|kala_" platform/supabase/migrations/344_ka_tulana_has_writer.sql
git add -A && git commit --amend --no-edit 2>/dev/null || git commit -m "chore: renumber ka_tulana migration 343→344 (avoid dup number)"
git push --force-with-lease
```
GATE: CI green on the rebased PR. Then merge PR #347 (squash). Confirm on main:
```bash
git checkout main && git pull --ff-only origin main
git ls-tree -r origin/main --name-only | grep "ka_tulana"   # expect writer + shim + migration
```

═══════════════════════════════════════════════════════════════════════
STEP 2 — Confirm migration 344 (ka_tulana has_writer) actually lands on PROD
═══════════════════════════════════════════════════════════════════════
The has_writer=true flag is what makes ka_tulana buildable. The CI fail-loud (PR #325) is on main,
so a missing-secret skip now FAILS the build instead of silently passing — but VERIFY the migration
applied to prod (not just that CI was green):

```bash
# via the Cloud SQL Auth Proxy (platform/scripts/start_db_proxy.sh, port 5433):
psql "$PROD_VIA_PROXY" -c \
  "SELECT asset_id, has_writer, asset_type FROM asset_registry \
   WHERE asset_id IN ('ka_tulana','ka_gochara','ka_dasha_kala') ORDER BY asset_id;"
```
GATE: ka_tulana → has_writer=t, asset_type=service. ka_gochara + ka_dasha_kala → asset_type=service.
If has_writer is still false on prod, the migration didn't apply — apply it surgically via psql
(it's idempotent metadata-only) and re-check. This is the gate the whole fix hinges on.

═══════════════════════════════════════════════════════════════════════
STEP 3 — Back-fill the ka_* registry + depends_on migration (the governance reproducibility gap)
═══════════════════════════════════════════════════════════════════════
The 12 ka_* asset_registry rows + their depends_on edges exist ONLY in prod (seeded by the retired
run_ka_*_prod.py path) — they are in NO migration. topoSort/click-Build depends on these prod-
resident edges; a fresh DB cannot reconstruct the L3 DAG from source. Back-fill an idempotent
register migration so L3 is reproducible. This is registry METADATA, not chart data.

```bash
git checkout -b chore/l3-register-ka-assets-migration
# next free number in supabase root after 344:
# create platform/supabase/migrations/345_register_ka_assets.sql
```
The migration must, for each of the 12 ka_* assets, INSERT its asset_registry row (asset_id, layer,
sort_order, sanskrit_name, english_name, storage_type, target_table, count_sql ($1 binding),
asset_kind, has_writer, depends_on, scope, is_active) **idempotently**:
```sql
-- Pattern per asset — ON CONFLICT DO NOTHING makes it safe on prod (rows already exist) AND
-- reproducible on a fresh DB. Source the EXACT values from platform/scripts/seed/asset_registry_seed.ts
-- (the ka_* block) — do NOT invent; copy the registered truth.
INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name,
  storage_type, target_table, count_sql, asset_kind, has_writer, depends_on, scope, is_active)
VALUES
  ('ka_yojaka','kala',5,'Yojaka','Activation bridge','postgres_table','kala_activation_predicates',
   'SELECT count(*) FROM kala_activation_predicates WHERE chart_id = $1','artifact', true,
   ARRAY['bo_laksana','bg_transit_rules','chart_dashas']::text[], 'per_chart', true),
  -- ... repeat for all 12 ka_* (7 artifacts + 5 services; services: storage_type/target_table/
  --     count_sql per their service rows; depends_on per asset_registry_seed.ts) ...
ON CONFLICT (asset_id) DO NOTHING;
```
RULES: (a) copy asset_id/depends_on/count_sql/asset_kind VERBATIM from asset_registry_seed.ts —
the seed is the source of truth. (b) ON CONFLICT DO NOTHING — NEVER overwrite live prod rows.
(c) include the ka_transit_almanac REMOVAL is NOT needed (already deleted; don't re-add it).
(d) this migration must NOT touch any kala_* data table — registry rows only.
GATE: on a scratch/empty DB, applying L0+L1+L2 + this migration makes the 12 ka_* rows present with
correct depends_on (so topoSort would resolve). On prod, it's a no-op (ON CONFLICT). Commit, PR, merge.

```bash
git add -A && git commit -m "chore(l3): back-fill ka_* asset_registry rows + depends_on as idempotent migration (reproducibility; ON CONFLICT DO NOTHING)"
git push -u origin chore/l3-register-ka-assets-migration && gh pr create --fill --base main
```

═══════════════════════════════════════════════════════════════════════
STEP 4 — Update seal docs to v-final + record the close
═══════════════════════════════════════════════════════════════════════
- L3_KALA_CLOSE_v1_0.md → bump to v1.3: note ka_tulana made buildable (PR #347), the ka_* register
  back-fill migration (Step 3), CF.L3.7 + CF.L3.8 fully RESOLVED (orchestrator path proven + all 12
  buildable). Fix any lingering "13 / 8 artifact" frontmatter to "12 / 7 artifact".
- CURRENT_STATE_v1_0.md → bump (v5.91): "L3 Kāla PERFECTLY CLOSED — 12/12 buildable, registry
  reproducible, CI fail-loud, branches swept; NEXT = L4 Phala." Point at the true main HEAD.
- Confirm drift_detector.py + schema_validator.py pass.
```bash
git checkout -b chore/l3-final-seal-docs
# ...edits...
git commit -am "docs(l3): final seal v1.3 — 12/12 buildable, registry back-filled, CF.L3.7/8 resolved; CURRENT_STATE v5.91"
git push -u origin chore/l3-final-seal-docs && gh pr create --fill --base main
```

═══════════════════════════════════════════════════════════════════════
STEP 5 — (NATIVE, on the Nirmāṇa tracker — NOT Claude Code) Rebuild → Kāla
═══════════════════════════════════════════════════════════════════════
After Steps 1–4 merge + deploy, the NATIVE clicks Rebuild → Kāla layer on the tracker. Expected:
plan includes all 12 ka_* (ka_tulana now buildable), builds in DAG order, 7 artifact counts sum to
the layer total, 5 services self-test to 0 rows + healthy, and the cascade-stale badges on
ka_vighnakara + ka_yojaka CLEAR through the orchestrator's own asset_throughput stamp. This is the
true end-to-end proof of the click-Build path (closes CF.L3.8 operationally). Claude Code does NOT
trigger this build.

═══════════════════════════════════════════════════════════════════════
DEFINITION OF DONE (perfectly closed)
═══════════════════════════════════════════════════════════════════════
- [ ] PR #347 rebased + merged; ka_tulana writer/shim/migration on main; migration renumbered to 344.
- [ ] Migration 344 VERIFIED applied on prod (ka_tulana.has_writer=true; 3 services asset_type=service).
- [ ] ka_* register back-fill migration merged (registry reproducible from source; ON CONFLICT DO NOTHING; prod no-op).
- [ ] Seal docs v1.3 + CURRENT_STATE v5.91; drift/schema validators green.
- [ ] (NATIVE) Rebuild→Kāla on tracker: 12/12 built DAG-ordered, counts reconcile, stale flags cleared.
- [ ] (already done earlier this session) CI fail-loud merged (#325); 9 bypass scripts retired (#326);
      closeout docs (#327); L3 branches swept; L4 planning protected on feature/l4-phala-planning-inputs.

NO Claude-Code-initiated data rebuild, writer execution, or build run anywhere. Step 5 is the
native's, on the tracker. Every migration here is idempotent registry/metadata only.
```
*End of brief — the final, precise actions to perfectly close L3 Kāla. After Step 5, the whole arc
L0✓ L1✓ L2✓ L3✓✓ is sealed and reproducible, and L4 Phala opens on clean ground.*
```
