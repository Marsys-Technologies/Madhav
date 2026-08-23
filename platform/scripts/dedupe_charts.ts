/**
 * Deduplicate charts rows by natural key.
 *
 * Natural key: (owner_id, lower(trim(name)), birth_date, birth_time,
 *               ROUND(birth_lat::numeric,4), ROUND(birth_lng::numeric,4))
 *
 * Canonical selection rule:
 *   - Default: oldest created_at in the group.
 *   - Override: if any row has chart_id = NATIVE_CANONICAL_ID, that row is canonical
 *     regardless of age (preserves the native chart UUID used across all asset writers).
 *
 * Dry-run by default — prints planned actions, makes zero writes.
 * Pass --apply to commit mutations.
 *
 * Usage:
 *   cd platform
 *   npx tsx scripts/dedupe_charts.ts            # dry-run
 *   npx tsx scripts/dedupe_charts.ts --apply    # commits
 *
 * Requires:
 *   DATABASE_URL in environment (Cloud SQL Auth Proxy on :5433 or direct).
 *   dotenv loads from .env.local if present.
 *
 * Brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_CHART_DEDUPE_v1_0.md
 */

import * as path from 'node:path'
import * as dotenv from 'dotenv'
import { Pool, PoolClient } from 'pg'
import { isDirectEntrypoint } from './lib/entrypoint'

dotenv.config({ path: path.join(process.cwd(), '.env.local') })

const NATIVE_CANONICAL_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const APPLY = process.argv.includes('--apply')

// ── DB ────────────────────────────────────────────────────────────────────────

const pool = new Pool({ connectionString: process.env.DATABASE_URL! })

async function db<T extends Record<string, unknown> = Record<string, unknown>>(
  sql: string,
  params?: unknown[],
  client?: PoolClient,
): Promise<T[]> {
  const conn = client ?? pool
  const { rows } = await conn.query(sql, params)
  return rows as T[]
}

// ── FK discovery ──────────────────────────────────────────────────────────────

interface FkRef {
  fk_table: string
  fk_column: string
  constraint_name: string
}

async function discoverFkRefs(): Promise<FkRef[]> {
  return db<FkRef>(`
    SELECT
      kcu.table_name   AS fk_table,
      kcu.column_name  AS fk_column,
      tc.constraint_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
     AND tc.table_schema     = kcu.table_schema
    JOIN information_schema.referential_constraints rc
      ON tc.constraint_name = rc.constraint_name
     AND tc.table_schema     = rc.constraint_schema
    JOIN information_schema.key_column_usage ccu
      ON rc.unique_constraint_name = ccu.constraint_name
     AND rc.unique_constraint_schema = ccu.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND ccu.table_name   = 'charts'
      AND ccu.column_name  = 'chart_id'
      AND kcu.table_schema = 'public'
    ORDER BY kcu.table_name, kcu.column_name
  `)
}

// ── Duplicate groups ──────────────────────────────────────────────────────────

interface DupeGroup {
  owner_id: string
  natural_name: string
  birth_date: string
  birth_time: string
  lat_r: string
  lng_r: string
  row_count: string
}

async function findDupeGroups(): Promise<DupeGroup[]> {
  return db<DupeGroup>(`
    SELECT
      owner_id,
      lower(trim(name))              AS natural_name,
      birth_date,
      birth_time,
      ROUND(birth_lat::numeric, 4)   AS lat_r,
      ROUND(birth_lng::numeric, 4)   AS lng_r,
      COUNT(*)                       AS row_count
    FROM charts
    GROUP BY
      owner_id,
      lower(trim(name)),
      birth_date,
      birth_time,
      ROUND(birth_lat::numeric, 4),
      ROUND(birth_lng::numeric, 4)
    HAVING COUNT(*) > 1
    ORDER BY COUNT(*) DESC, natural_name
  `)
}

interface ChartRow {
  chart_id: string
  created_at: string
}

async function getGroupRows(g: DupeGroup): Promise<ChartRow[]> {
  return db<ChartRow>(`
    SELECT chart_id, created_at
    FROM charts
    WHERE owner_id = $1
      AND lower(trim(name)) = $2
      AND birth_date = $3
      AND birth_time = $4
      AND ROUND(birth_lat::numeric, 4) = $5
      AND ROUND(birth_lng::numeric, 4) = $6
    ORDER BY created_at ASC
  `, [g.owner_id, g.natural_name, g.birth_date, g.birth_time, g.lat_r, g.lng_r])
}

// ── Counters ──────────────────────────────────────────────────────────────────

const summary = {
  groupsInspected: 0,
  groupsWithDupes: 0,
  rowsRepointed: {} as Record<string, number>,
  rowsDeleted: 0,
  errors: 0,
}

// ── Per-group processing ──────────────────────────────────────────────────────

async function processGroup(
  g: DupeGroup,
  rows: ChartRow[],
  fkRefs: FkRef[],
): Promise<void> {
  const nativeRow = rows.find((r) => r.chart_id === NATIVE_CANONICAL_ID)
  const canonical = nativeRow ?? rows[0]
  const duplicates = rows.filter((r) => r.chart_id !== canonical.chart_id)

  console.log(`\nGroup: "${g.natural_name}" | ${g.birth_date} ${g.birth_time} | owner ${g.owner_id}`)
  console.log(`  Canonical: ${canonical.chart_id}${nativeRow ? ' [NATIVE OVERRIDE]' : ' [oldest]'}`)
  console.log(`  Duplicates (${duplicates.length}): ${duplicates.map((d) => d.chart_id).join(', ')}`)

  if (fkRefs.length > 0) {
    console.log('  FK re-points planned:')
    for (const fk of fkRefs) {
      console.log(`    ${fk.fk_table}.${fk.fk_column} → ${canonical.chart_id}`)
    }
  }

  if (!APPLY) return

  const client = await pool.connect()
  try {
    await client.query('BEGIN')

    for (const dup of duplicates) {
      for (const fk of fkRefs) {
        const result = await client.query(
          `UPDATE ${fk.fk_table}
             SET ${fk.fk_column} = $1
           WHERE ${fk.fk_column} = $2`,
          [canonical.chart_id, dup.chart_id],
        )
        const count = result.rowCount ?? 0
        if (count > 0) {
          summary.rowsRepointed[fk.fk_table] =
            (summary.rowsRepointed[fk.fk_table] ?? 0) + count
          console.log(
            `    [apply] Re-pointed ${count} row(s) in ${fk.fk_table} from ${dup.chart_id} → ${canonical.chart_id}`,
          )
        }
      }

      await client.query('DELETE FROM charts WHERE chart_id = $1', [dup.chart_id])
      summary.rowsDeleted++
      console.log(`    [apply] Deleted duplicate chart ${dup.chart_id}`)
    }

    await client.query('COMMIT')
  } catch (err) {
    await client.query('ROLLBACK').catch(() => {})
    summary.errors++
    console.error(`  [ERROR] Group rolled back: ${err instanceof Error ? err.message : String(err)}`)
  } finally {
    client.release()
  }
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log('='.repeat(70))
  console.log(`MARSYS dedupe_charts — mode: ${APPLY ? 'APPLY (writes committed)' : 'DRY-RUN (no writes)'}`)
  console.log(`Canonical native override UUID: ${NATIVE_CANONICAL_ID}`)
  console.log('='.repeat(70))

  // Discover FK refs from information_schema
  const fkRefs = await discoverFkRefs()
  console.log(`\nFK references to charts.chart_id (${fkRefs.length} found):`)
  if (fkRefs.length === 0) {
    console.log('  (none)')
  } else {
    for (const fk of fkRefs) {
      console.log(`  ${fk.fk_table}.${fk.fk_column} (constraint: ${fk.constraint_name})`)
    }
  }

  // Find duplicate groups
  const groups = await findDupeGroups()
  summary.groupsInspected = groups.length

  if (groups.length === 0) {
    console.log('\nNo duplicate natural-key groups found. Nothing to do.')
  } else {
    summary.groupsWithDupes = groups.length
    console.log(`\nFound ${groups.length} group(s) with duplicates:`)

    for (const g of groups) {
      const rows = await getGroupRows(g)
      await processGroup(g, rows, fkRefs)
    }
  }

  // Summary
  console.log('\n' + '='.repeat(70))
  console.log('SUMMARY')
  console.log(`  Mode:              ${APPLY ? 'APPLY' : 'DRY-RUN'}`)
  console.log(`  Groups inspected:  ${summary.groupsInspected}`)
  console.log(`  Groups with dupes: ${summary.groupsWithDupes}`)
  if (Object.keys(summary.rowsRepointed).length > 0) {
    console.log('  Rows re-pointed:')
    for (const [table, count] of Object.entries(summary.rowsRepointed)) {
      console.log(`    ${table}: ${count}`)
    }
  } else {
    console.log('  Rows re-pointed:   0')
  }
  console.log(`  Rows deleted:      ${summary.rowsDeleted}`)
  console.log(`  Errors:            ${summary.errors}`)
  console.log('='.repeat(70))

  if (!APPLY) {
    console.log('\nDRY-RUN complete. Re-run with --apply to commit changes.')
  }

  await pool.end()
}

// ─────────────────────────────────────────────────────────────────────────────────────────────
// `isDirectEntrypoint` is THE ONE SHARED IMPLEMENTATION, in `scripts/lib/entrypoint.ts`.
//
// It used to be a private copy of that function in this file. Nirmāṇa finding F-2 (M0-T60,
// re-filed by M0-T65 at EIGHT copies) is that a security-relevant predicate duplicated N times
// with no detector asserting the bodies agree is a defect on its own terms; ruling D-67 part 3
// granted the shared implementation. Task M0-T66.
//
// Imported, not mirrored, and that is safe here for the reason ruling D-9 actually gives:
// `scripts/lib/entrypoint.ts` imports only the three node builtins this file already imported
// for its own copy, and has no module-scope effect at all. This module's graph gains nothing.
//
// Re-exported so this module's public surface is exactly what it was.
export { isDirectEntrypoint }
// ─────────────────────────────────────────────────────────────────────────────────────────────

// Guard: only execute when this module IS the entrypoint — never as an import side effect.
//
// THE HAZARD IS RUNNING. `main()` re-points every foreign key that references `charts` and
// then issues `DELETE FROM charts WHERE chart_id = $1` for every row it judges a duplicate
// (line 196). `--apply` is read from `process.argv` at MODULE SCOPE (line 38), so an importing
// process that happened to carry `--apply` in its own argv would have committed those deletes.
// Dry-run is the default, which limits but does not remove the hazard: even a dry run opened a
// pool on `DATABASE_URL` and ran `information_schema` queries as a side effect of an import,
// and the tail's `process.exit(1)` killed the importer on any failure.
//
// This is the `isDirectEntrypoint` contract (Nirmāṇa M0-T60 / A3.4 operator rule 5), NOT the
// `IMPORT_ONLY !== '1'` contract the two CI gates use (M0-T50 / ruling D-49, documented at
// `scripts/audit/A3_env_matrix.md` Addendum A3.4). A gate's hazard is FAILING to run, so its safe
// default is RUN. This file's hazard is RUNNING, so its safe default is DO NOT RUN.
//
// Nirmāṇa WORK_QUEUE M0-T65, ruling D-74 part 1 (wave 1 of F-4 tier 1: the five scripts that were
// destructive or credential-touching on incidental import). Verified WITHOUT executing this file —
// D-74 parts 2 and 3 forbid running it — by structural assertion over this source plus behavioural
// tests of the identical idiom on a harmless stand-in module. See
// `scripts/__tests__/destructive_entrypoint_guards.test.ts`.
if (isDirectEntrypoint(import.meta.url, process.argv[1])) {
  main().catch((err) => {
    console.error('Fatal:', err)
    process.exit(1)
  })
}
