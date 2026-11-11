---
name: create-migration
description: Create a new numbered SQL migration file for the Madhav platform following the project's naming and idempotency conventions.
---

## How to use

User invokes: `/create-migration <description>`

## Steps

1. Refresh `origin/main`. Run the repository guard from a checkout matching that
   source because it reads the local files. It checks both migration directories
   and reserved owner paths. Reconcile active claims with the integration lead,
   and recheck the number under the merge lock.
   ```bash
   cd platform
   npm run migration:next
   ```

2. Create `platform/supabase/migrations/NNN_<description>.sql`. Keep the number
   in the filename and header in sync, per
   `00_ARCHITECTURE/MIGRATION_AND_MERGE_PROTOCOL_v1_0.md` §§2–3.
   ```sql
   -- Migration NNN: <description>
   -- Created: <date>

   BEGIN;

   -- Your SQL here

   COMMIT;
   ```

3. If adding a new asset, include the asset_registry insert:
   ```sql
   INSERT INTO asset_registry (asset_id, display_name, layer, count_sql, target_floor)
   VALUES (
     '<asset_id>',
     '<display name>',
     '<L0|L1|L2>',
     'SELECT COUNT(*) FROM <table> WHERE chart_id = $1',
     0
   ) ON CONFLICT (asset_id) DO NOTHING;
   ```

4. Run `npm run guard:migration-numbers` from `platform`, then dispatch the
   `migration-guard` subagent to review the exact file.
