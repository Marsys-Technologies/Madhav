---
artifact: CLAUDECODE_BRIEF_PHASE_ALPHA_RECOVERY_v1_0
canonical_id: PHASE_ALPHA_RECOVERY_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Phase α recovery — lost-merge fix + missing 10 reference tables
branch: fix/l0-phase-alpha-recovery
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavPhaseARecover (pre-create with `git worktree add`)
estimated_sessions: 1
estimated_time: 60-90 min total
llm_cost: $0
---

# L0 Phase α Recovery — Lost-Merge Fix + Missing 10 Reference Tables

## §0 — The bug being fixed (read first)

**Discovery 2026-06-08 evening:** PR #221 was reported merged + Phase α SEALED. In reality, commit `c4557828` (which contains all the right Phase α work) **was never landed on main.** Verifications:

```
$ git merge-base --is-ancestor c4557828 origin/main
$ echo $?
1   # NOT an ancestor → never merged
```

```
$ git ls-tree -r origin/main --name-only | grep -E "platform/supabase/migrations/17[6-9]"
(empty — no Phase α migrations on main)
```

**Prod state is partial:**
- 4 new content tables exist (brahma_yoga_catalog / brahma_dasha_systems / brahma_dosha_catalog / brahma_compendium_index) → migration 176 was applied directly via psql
- asset_registry has 12 L0 rows → migration 179 was applied directly via psql
- topic_tag column + classical_attributions reshape → probably applied (verify)
- **10 NEW reference_* tables do NOT exist in prod** → migration 178 was never applied
- bg_reference count_sql (15-table sum) is in asset_registry but always fails because 10 of its 15 tables don't exist → returns wrong total

**Codebase state:**
- main has NONE of the Phase α work (no migrations, no asset_names.ts updates, no parity_check.ts updates)
- The work lives only on `origin/feature/l0-phase-alpha` at commit `c4557828`

**Net architectural risk:** if a fresh deploy or schema-reset triggers, prod cannot be recreated from main's migrations alone. Phase α is in a divergent state that this brief fully resolves.

## §1 — Recovery plan

1. **Cherry-pick `c4557828`** onto a fresh branch off current main
2. **Resolve any conflicts** with intervening main commits (PR #222 cockpit clear-fix, PR #224 cockpit polish round); the changes overlap on `asset_registry_seed.ts` + cockpit API routes
3. **Apply migration 178 directly to prod** (creates the 10 reference tables; idempotent via `CREATE TABLE IF NOT EXISTS`)
4. **Verify** all 14 Phase α tables exist in prod
5. **Verify** bg_reference 15-table count_sql now returns correct sum (currently 88 from existing 5 tables; will be 88 after recovery since new tables exist but are empty)
6. **Open PR** with clear "Phase α recovery — lost-merge fix" framing; merge after CI green
7. **Deploy** + post-deploy smoke

## §2 — Setup

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch --all --prune

# Confirm where we are
git log --oneline origin/main -3
# Top should be 3e47eea3 (force-dynamic routing) per current state

# Pre-create the worktree
git worktree add -b fix/l0-phase-alpha-recovery /Users/Dev/Vibe-Coding/Apps/MadhavPhaseARecover main

cd /Users/Dev/Vibe-Coding/Apps/MadhavPhaseARecover
git log --oneline -3   # confirm on main HEAD

# DB proxy
bash platform/scripts/start_db_proxy.sh > /tmp/proxy_recover.log 2>&1 &
sleep 4
export PROD_DB_URL="postgresql://amjis_app@127.0.0.1:5433/amjis"
psql_prod() { psql "$PROD_DB_URL" -v ON_ERROR_STOP=1 "$@"; }
```

**CHECKPOINT setup:** worktree on `fix/l0-phase-alpha-recovery`; DB proxy live.

## §3 — Pre-flight prod schema audit

Before any change, document what prod has:

```bash
# Are the 14 Phase α tables present?
for t in brahma_yoga_catalog brahma_dasha_systems brahma_dosha_catalog brahma_compendium_index \
         reference_houses reference_strength_systems reference_karakas reference_upagrahas reference_constants \
         reference_topic_tags reference_glossary reference_yogas reference_doshas reference_dasha_systems; do
  exists=$(psql_prod -At -c "SELECT to_regclass('$t')")
  echo "  $t: $exists"
done

# Check the schema additions:
psql_prod -c "SELECT column_name FROM information_schema.columns WHERE table_name='classical_text_chunks' AND column_name='topic_tag'"
psql_prod -c "\d classical_attributions" 2>&1 | head -20
psql_prod -c "SELECT column_name FROM information_schema.columns WHERE table_name='brahma_remedy_corpus' AND column_name='scaffold_status'"
```

**CHECKPOINT 3:** expect output to confirm:
- 4 brahma_* tables (yoga/dasha_systems/dosha/compendium) EXIST
- 10 reference_* tables MISSING (return NULL or 'NULL')
- topic_tag column on classical_text_chunks EXISTS (set by migration 177)
- classical_attributions has the new chunk-pointer-index columns (source_chunk_ids[], topic_canonical_name, etc.)
- brahma_remedy_corpus.scaffold_status EXISTS

Capture this output to `/tmp/prod_schema_before.txt` for the audit trail.

If anything is unexpected (e.g. a brahma_* table missing, or one of the 10 reference tables EXISTS when expected not to), STOP and report. The recovery plan assumes a specific gap profile.

## §4 — Cherry-pick c4557828 onto fix/l0-phase-alpha-recovery

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavPhaseARecover
git cherry-pick c4557828
```

**Likely conflicts** (intervening commits PR #222 + PR #224 touched these files):
- `platform/scripts/seed/asset_registry_seed.ts` — c4557828 added 4 brahmagyan rows + count_sql updates; PR #224 may have edited the same area
- `platform/src/lib/jyotish/asset_names.ts` — c4557828 added 4 new L0 entries
- `platform/src/lib/retrieval/registry/parity_check.ts` — c4557828 added L0_BRAHMAGYAN_ASSETS const
- `platform/vitest.config.ts` — c4557828 re-enabled Group O

**Conflict resolution strategy:** for each conflict, take **BOTH sides**:
- Keep main's existing changes (PR #222 + #224 work)
- ADD c4557828's additions (the 12 L0 asset definitions, the L0_BRAHMAGYAN_ASSETS const, the Group O re-enable)

For `asset_registry_seed.ts` specifically: the 8 existing brahmagyan entries are likely identical on both sides; c4557828 ADDS 4 new entries (bg_yogas, bg_dasha_systems, bg_doshas, bg_compendium_index) and UPDATES count_sql for bg_text_index + bg_reference. Take both: keep main's structure, add c4557828's new entries + updates.

```bash
# After resolving conflicts in each file:
git add <file>
# When all conflicts resolved:
git cherry-pick --continue

# Or if you want to be cautious about the conflicts:
git status   # see remaining conflict markers
# resolve manually, git add, then continue

# If the cherry-pick goes sideways:
git cherry-pick --abort
# halt; report for re-strategy
```

**CHECKPOINT 4:** cherry-pick completes. `git log --oneline -3` shows your new commit on top.

```bash
# Verify the 4 migrations exist now on the branch
ls platform/supabase/migrations/17[6-9]* 2>&1 | head -10
# Expect 4 files: 176, 177, 178, 179
```

## §5 — Code verification (tsc + tests)

```bash
cd platform
npx tsc --noEmit src/lib/jyotish/asset_names.ts src/lib/jyotish/__tests__/asset_names.test.ts \
                 src/lib/retrieval/registry/parity_check.ts 2>&1 | tail -20

npx vitest run src/lib/jyotish/__tests__/asset_names.test.ts 2>&1 | tail -10
# Should pass (12 L0 keys per c4557828)
cd ..
```

**CHECKPOINT 5:** tsc clean; tests pass. If tsc fails because PR #222 or #224 touched a shared type, fix the integration (extend, don't revert).

## §6 — Apply migration 178 to prod

Migration 178 creates the 10 reference tables with `IF NOT EXISTS` — idempotent.

```bash
# Inspect what 178 will do
head -30 platform/supabase/migrations/178_l0_phase_alpha_reference_tables.sql

# Apply
psql_prod -f platform/supabase/migrations/178_l0_phase_alpha_reference_tables.sql
```

**CHECKPOINT 6:** apply succeeds; all 10 tables created.

```bash
# Verify
for t in reference_houses reference_strength_systems reference_karakas reference_upagrahas reference_constants \
         reference_topic_tags reference_glossary reference_yogas reference_doshas reference_dasha_systems; do
  exists=$(psql_prod -At -c "SELECT to_regclass('$t')")
  count=$(psql_prod -At -c "SELECT count(*) FROM $t" 2>/dev/null || echo "ERROR")
  echo "  $t: $exists, count=$count"
done
```

Expected: all 10 tables exist, all return count=0 (no data yet; phase β populates).

## §7 — Apply migrations 176, 177, 179 to prod (idempotency check)

Migrations 176, 177, 179 already ran in prod (the 4 brahma_* tables + topic_tag column + classical_attributions reshape + asset_registry rows all exist). Re-applying them should be safe because:
- 176 uses `CREATE TABLE IF NOT EXISTS`
- 177 uses `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` and `DROP TABLE IF EXISTS` (the classical_attributions stub was empty anyway) — review the file before applying
- 179 uses `UPDATE asset_registry SET ... WHERE asset_id IN (...)` for existing + `INSERT INTO asset_registry` for new rows; the INSERT will fail if rows already exist (which they do)

**Safer approach:** dry-run each by checking what they would do:

```bash
# 176 — inspect for non-idempotent statements
grep -E "CREATE TABLE|INSERT|DELETE|DROP" platform/supabase/migrations/176_l0_phase_alpha_new_content_tables.sql

# 177 — same
grep -E "CREATE TABLE|INSERT|DELETE|DROP|ALTER" platform/supabase/migrations/177_l0_phase_alpha_existing_table_schema.sql

# 179 — same; likely will fail re-inserting existing rows
grep -E "INSERT|UPDATE" platform/supabase/migrations/179_l0_phase_alpha_asset_registry.sql | head -10
```

**Decision:** for the migrations that may fail on re-apply (179 INSERT), the cleanest approach is to leave prod's data alone (it's already correct) and just ensure the MIGRATION FILES are on main so a future fresh-environment deploy works. The migration files become installable historical record. Do NOT re-apply 176/177/179 to prod if their content is already there.

For 178 (the missing one), apply per §6.

**Skip §7 re-apply of 176/177/179 if §3 confirmed their content is in prod already.**

## §8 — Verify bg_reference count_sql now returns sum of 15

```bash
# bg_reference count_sql against prod
psql_prod -c "$(psql_prod -At -c "SELECT count_sql FROM asset_registry WHERE asset_id='bg_reference'")"

# Should return ONE row with the sum (currently 88: 11 planets + 27 nakshatras + 12 signs + ~30 aspects + 16 vargas = 96 ish; or whatever the actual seed counts are)
```

**CHECKPOINT 8:** the 15-table SUM executes successfully (no Postgres error). Result is the sum of rows across all 15 tables (most are 0; first 5 have content from migration 081 + reference seed).

Then verify via the cockpit API:

```bash
# Get a session cookie (you have an active one if Chrome is logged in)
NATIVE_SESSION=$(npx tsx platform/scripts/mint_session_cookie.ts 2>/dev/null || echo "DUMMY")

curl -s -X POST https://madhav.marsys.in/api/cockpit/clear \
  -b "__session=$NATIVE_SESSION" \
  -H "Content-Type: application/json" \
  -d '{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa","scope":"asset","scope_target":"bg_reference"}' \
  | jq '.preview | {tables, total_rows}'
```

**Hard AC:** the response is HTTP 200 with `total_rows` matching the SUM of all 15 tables (NOT 61 — that was the buggy fallback to `reference_nakshatras` alone).

## §9 — Commit + push + PR

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavPhaseARecover
git status
git log --oneline -3  # should show cherry-picked Phase α commit on top

# Add the audit trail markdown
cat > 00_ARCHITECTURE/PHASE_ALPHA_RECOVERY_v1_0.md <<'EOF'
# Phase α Recovery — Lost-Merge Fix + Missing Reference Tables (2026-06-08)

## Discovery
PR #221 was reported merged + Phase α SEALED, but `git merge-base --is-ancestor c4557828 origin/main`
returned NOT ANCESTOR. None of Phase α's migrations (176/177/178/179) were on main.

## Prod state at recovery
- 4 brahma_* content tables: EXIST (migrations 176/179 applied via direct psql)
- topic_tag + classical_attributions reshape: EXIST (migration 177 applied via direct psql)
- 10 reference_* tables: MISSING (migration 178 NEVER applied)
- asset_registry has 12 L0 rows (migration 179 applied)
- bg_reference count_sql is 15-table sum but 10 tables don't exist → previews silently returned wrong totals

## Recovery actions
1. Cherry-picked c4557828 onto fix/l0-phase-alpha-recovery
2. Resolved conflicts with intervening PR #222 + #224 commits
3. Applied migration 178 to prod (created the 10 reference tables, all 0 rows)
4. Did NOT re-apply 176/177/179 (their content already in prod; files on main for future fresh deploys)
5. Verified bg_reference count_sql now returns correct sum across all 15 tables

## Architectural lesson
Future "Phase X SEALED" claims MUST include:
- `git merge-base --is-ancestor <commit> origin/main` check
- Direct prod schema audit against migration manifest
- Cross-check that migration files in commit match files on main

## Open follow-up
Phase β can now correctly populate the 10 new reference tables.
EOF

git add -A
git status   # confirm the cherry-pick contents + the recovery doc are staged

git commit -m "fix(l0/phase-alpha): recovery — cherry-pick c4557828 to main, apply missing migration 178

PR #221 was reported merged + Phase α SEALED on 2026-06-08, but c4557828 never
landed on main. This recovers it.

Cherry-picks c4557828 (Phase α implementation) onto current main with conflicts
resolved against intervening PR #222 (cockpit clear-fix) and PR #224 (cockpit
polish round).

Brings to main:
- Migration 176 (4 new content tables: yoga/dasha_systems/dosha/compendium)
- Migration 177 (topic_tag column + classical_attributions reshape + remedy + ontology + rules columns)
- Migration 178 (10 new reference_* tables) — APPLIED to prod by this PR
- Migration 179 (asset_registry: bg_text_index + bg_reference count_sql updates + 4 new L0 rows)
- asset_names.ts (12 L0 entries)
- asset_registry_seed.ts (idempotent upsert with 12 brahmagyan entries)
- parity_check.ts (L0_BRAHMAGYAN_ASSETS const with 12 keys)
- vitest.config.ts (Group O re-enabled)

Prod state after this PR:
- 4 brahma_* content tables: already existed; unchanged
- 10 reference_* tables: NEWLY CREATED by migration 178 (empty; phase β populates)
- asset_registry: unchanged (already correct)
- bg_reference count_sql now returns correct 15-table sum

See 00_ARCHITECTURE/PHASE_ALPHA_RECOVERY_v1_0.md for full audit trail.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

git push -u origin fix/l0-phase-alpha-recovery

gh pr create --title "fix(l0/phase-alpha): recovery — bring c4557828 to main + apply missing migration 178" \
  --body "**Critical recovery PR.** PR #221 was reported merged but the underlying commit (c4557828) never landed on main. This PR recovers it.

See 00_ARCHITECTURE/PHASE_ALPHA_RECOVERY_v1_0.md for the full discovery + audit trail.

After this merges + deploys:
- main has all Phase α migrations (176-179) for future fresh-environment deploys
- 10 reference_* tables exist in prod (created by migration 178 application)
- bg_reference clear preview returns correct total (15-table sum, not the misleading 61 fallback)
- Phase α is TRULY sealed" \
  --base main --head fix/l0-phase-alpha-recovery
```

## §10 — Post-merge deploy + verify

```bash
# Watch the deploy after merge
gh run watch

# After deploy:
sleep 60
curl -s -X POST https://madhav.marsys.in/api/cockpit/clear \
  -b "__session=$NATIVE_SESSION" \
  -H "Content-Type: application/json" \
  -d '{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa","scope":"asset","scope_target":"bg_reference"}' \
  | jq '.preview | {tables, total_rows}'
# Expect: total_rows = sum of 15 tables (currently ~88; will grow when phase β fills the 10 new ones)
```

**Hard AC:** preview returns full sum, no error.

## §11 — Hard stops

- §3 audit reveals brahma_yoga_catalog (or any of the 4 content tables) MISSING in prod → migration 176 may also need re-apply; halt + investigate before §4
- §3 audit reveals one of the 10 reference_* tables already EXISTS in prod → unexpected; halt + investigate (may indicate partial migration apply)
- §4 cherry-pick produces unresolvable conflicts → `git cherry-pick --abort` and halt; the lost-merge recovery may need to be done by hand-applying each file
- §6 migration 178 fails to apply → likely a CREATE TABLE depends on something that doesn't exist (e.g. brahma_yoga_catalog for the reference_yogas FK); investigate apply order
- §8 bg_reference count_sql still returns 61 → cache issue OR the count_sql in prod is stale; check `SELECT count_sql FROM asset_registry WHERE asset_id='bg_reference'` post-migration-178 apply
- §10 deploy fails → standard CI investigation; do not roll back unless you know why

## §12 — Out of scope

- Phase β/γ/δ/ε/ζ/η L0 build work
- New tests beyond what cherry-pick brings forward
- Data population in the 10 new reference tables (phase β)
- Repair of the merge-tracking discipline that allowed PR #221 to silently lose its content (governance work; separate)

## §13 — Memory update (post-merge)

After this PR merges, add the architectural lesson to memory:

```markdown
**feedback_phase_sealed_needs_merge_verification.md** — when a phase is reported "SEALED", verify
that the implementing commit is actually an ancestor of origin/main BEFORE updating any
"X is COMPLETE" memory. Commands:
  git merge-base --is-ancestor <commit> origin/main
  git ls-tree -r origin/main --name-only | grep <expected migration filename>
Do NOT rely on:
  git log --all   # masks branch isolation; --all includes feature branches
  git show <commit>  # tells you what's IN the commit, not where the commit IS
```

Begin §2 setup.

---

*End of brief.*
