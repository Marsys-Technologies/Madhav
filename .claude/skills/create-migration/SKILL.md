---
name: create-migration
description: Create a new numbered SQL migration file for the Madhav platform following the project's naming and idempotency conventions.
---

## How to use

User invokes: `/create-migration <description>`

## Steps

1. Run this to find the next migration number:
   ```bash
   ls platform/migrations/*.sql | sed 's/.*\/\([0-9]*\)_.*/\1/' | sort -n | tail -1
   ```
   Add 1 to get `NNN`.

2. Create file at `platform/migrations/NNN_<description>.sql` with this header:
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

4. After creating, dispatch the `migration-guard` subagent to review it.
