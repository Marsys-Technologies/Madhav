---
artifact: PHASE_ALPHA_RECOVERY_v1_0
canonical_id: PHASE_ALPHA_RECOVERY
version: 1.0
status: COMPLETE
authored: 2026-06-08
session: fix/l0-phase-alpha-recovery
---

# Phase α Recovery — Lost-Merge Fix (2026-06-08)

## Discovery

PR #221 was reported merged + Phase α SEALED, but verification showed `c4557828` was never an ancestor of `origin/main`:

```
$ git merge-base --is-ancestor c4557828 origin/main && echo ANCESTOR || echo NOT_ANCESTOR
NOT_ANCESTOR
```

None of Phase α's migrations (176/177/178/179) were in `git ls-tree -r origin/main`.

## Prod state at recovery open

| Item | State |
|---|---|
| 4 brahma_* content tables | EXIST (176 + 179 applied directly via psql) |
| topic_tag column on classical_text_chunks | EXISTS (177 applied) |
| brahma_remedy_corpus.scaffold_status column | EXISTS (177 applied) |
| classical_attributions reshape | EXISTS (177 applied) |
| 10 reference_* tables | **EXIST** (178 was applied — contrary to brief's assumption; all 0 rows) |
| asset_registry 12 L0 rows | EXIST (179 applied) |
| bg_reference count_sql (15-table sum) | EXECUTES CLEANLY, returns 61 |

**Key correction vs brief:** Migration 178 WAS applied to prod before recovery (the 10 reference_* tables existed). The brief stated they were missing based on a snapshot taken before the tables were applied. Recovery §6 became a no-op verification.

## Recovery actions

1. Created worktree `fix/l0-phase-alpha-recovery` off current main (HEAD `3e47eea3`)
2. Cherry-picked `c4557828` — **clean apply, zero conflicts** with PR #222 + PR #223 intervening commits
3. Confirmed 4 migration files now on branch: 176/177/178/179
4. Ran `vitest run asset_names.test.ts` — 28/28 PASS
5. Verified tsc errors in `parity_check.ts` are pre-existing (present on main before cherry-pick)
6. Confirmed all 10 reference_* tables exist in prod (migration 178 already applied)
7. Confirmed bg_reference count_sql returns 61 — no errors

## What this PR brings to main

| File | Purpose |
|---|---|
| `migrations/176_l0_phase_alpha_new_content_tables.sql` | 4 brahma_* content tables (idempotent; already in prod) |
| `migrations/177_l0_phase_alpha_existing_table_schema.sql` | topic_tag + classical_attributions + remedy + ontology + rules columns (idempotent) |
| `migrations/178_l0_phase_alpha_reference_tables.sql` | 10 reference_* tables (idempotent; already in prod) |
| `migrations/179_l0_phase_alpha_asset_registry.sql` | 12 L0 asset_registry rows + count_sql updates (idempotent) |
| `src/lib/jyotish/asset_names.ts` | 12 L0 asset key constants |
| `scripts/seed/asset_registry_seed.ts` | Idempotent upsert with 12 brahmagyan entries |
| `src/lib/retrieval/registry/parity_check.ts` | L0_BRAHMAGYAN_ASSETS const (12 keys) |
| `vitest.config.ts` | Group O re-enabled |

All migrations use `IF NOT EXISTS` / `ON CONFLICT DO NOTHING` — safe to apply on fresh environments.

## Architectural lesson

> **"Phase X SEALED" ≠ commit on main.**

Future seal claims MUST include:
```bash
git merge-base --is-ancestor <implementing_commit> origin/main && echo SEALED || echo NOT_ON_MAIN
git ls-tree -r origin/main --name-only | grep <expected_migration_filename>
```

Do NOT rely on:
- `git log --all` — masks branch isolation; `--all` includes feature branches
- `git show <commit>` — shows what's IN the commit, not where the commit IS
- Prod schema alone — prod state can diverge from main via direct psql applies

## Open follow-up

Phase β can now correctly populate the 10 new reference tables via its seed scripts.
