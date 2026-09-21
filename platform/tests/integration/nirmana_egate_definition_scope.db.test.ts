// @vitest-environment node
/**
 * Regression test for F1: egate.sql and capsule_audit.sql must never treat evidence
 * recorded against a SUPERSEDED campaign definition as clearance under the CURRENTLY
 * FROZEN one. Before the fix, `frozen`/`route` in egate.sql and `ev` in capsule_audit.sql
 * §1/§3 (plus the defense-in-depth scoping added to §2) read
 * nirmana_elevation_campaign_events with no definition_revision filter, so an
 * asset_frozen / asset_analysis_accepted / optimization_verdict_accepted / integrity_verified
 * chain logged entirely under a superseded definition was read as current clearance.
 *
 * This suite runs the REAL files (not a re-implementation of their logic) via the psql
 * CLI against a disposable database, because both scripts use psql meta-commands
 * (\echo, \if, \set, :'layer' substitution) a plain SQL client cannot execute.
 *
 *   NIRMANA_ELEVATION_TEST_DATABASE_URL=postgresql://.../nirmana_elevation_test \
 *     npx vitest run tests/integration/nirmana_egate_definition_scope.db.test.ts
 *
 * Reuses the same disposable database as nirmana_elevation_asset_labels.db.test.ts
 * (isolated by a distinct, literal `nirmana_evidence` schema rather than that
 * sibling's randomized schema name — both scripts under test hardcode
 * `nirmana_evidence.<table>` rather than relying on search_path, so the schema
 * must be literally named that). Wired into CI alongside that sibling in the
 * same `unit-tests` job step (ci.yml) since both are cheap, schema-isolated,
 * and share no state.
 */
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { execFileSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { Pool, type PoolClient } from 'pg'

const TEST_DB_URL = process.env.NIRMANA_ELEVATION_TEST_DATABASE_URL
const MIGRATION_592_PATH = resolve(__dirname, '../../migrations/592_nirmana_elevation_campaign_evidence.sql')
const EGATE_SQL_PATH = resolve(__dirname, '../../scripts/nirmana/egate.sql')
const CAPSULE_AUDIT_SQL_PATH = resolve(__dirname, '../../scripts/nirmana/capsule_audit.sql')

function assertDisposableTestDatabaseUrl(databaseUrl: string): void {
  const databaseName = decodeURIComponent(new URL(databaseUrl).pathname).replace(/^\/+/, '')
  if (databaseName !== 'nirmana_elevation_test') {
    throw new Error(
      'F1 egate/capsule_audit regression test must point at the approved disposable database ' +
        '`nirmana_elevation_test`. This suite creates and drops a literal `nirmana_evidence` ' +
        'schema (both scripts hardcode that schema name) and must never run against production.'
    )
  }
}

describe.skipIf(!TEST_DB_URL)('F1 — egate.sql / capsule_audit.sql definition-revision scoping — live DB', () => {
  let pool: Pool
  let client: PoolClient

  const STALE_ASSET = 'ka_test_stale_only'

  beforeAll(async () => {
    assertDisposableTestDatabaseUrl(TEST_DB_URL!)
    pool = new Pool({ connectionString: TEST_DB_URL })
    client = await pool.connect()
    // Both scripts hardcode `nirmana_evidence.<table>` — the schema must be
    // literally named that for the real files to find the fixture data.
    await client.query('DROP SCHEMA IF EXISTS nirmana_evidence CASCADE')
    await client.query('CREATE SCHEMA nirmana_evidence')
    await client.query('SET search_path TO nirmana_evidence, public')
    await client.query(readFileSync(MIGRATION_592_PATH, 'utf8'))

    // Two definitions: one superseded, one frozen. The test asset appears in
    // BOTH manifests with no dependencies (so egate.sql's ancestor check
    // trivially passes and only the route/frozen scoping is under test).
    const manifest = JSON.stringify({
      assets: [{ asset_id: STALE_ASSET, layer: 'L3', asset_kind: 'data', depends_on: [] }],
    })
    await client.query(
      `INSERT INTO nirmana_elevation_campaign_definitions
         (campaign_id, definition_revision, definition_status, manifest, manifest_sha256, created_by, superseded_at)
       VALUES ('nirmana-elevation', 'superseded-rev', 'superseded', $1::jsonb, $2, 'f1-regression-test', now()),
              ('nirmana-elevation', 'frozen-rev',      'frozen',     $1::jsonb, $3, 'f1-regression-test', NULL)`,
      [manifest, 'a'.repeat(64), 'b'.repeat(64)]
    )

    // A COMPLETE evidence chain (asset_frozen + w2 route + integrity_verified),
    // but every event is tagged to the SUPERSEDED definition only. Nothing is
    // recorded under 'frozen-rev'. Correct behavior: this asset must NOT read
    // as cleared/complete under the current frozen definition.
    // migration 592 alone (no writer_identity column / server-writer guard —
    // that arrives in migration 632 and is irrelevant to §1/§3/egate.sql,
    // which this suite exercises; §2's identity-separation scoping is a
    // separate, already-reviewed defense-in-depth change).
    const events: Array<[string, string, string]> = [
      ['stale-analysis', 'asset_analysis_accepted', 'git_commit'],
      ['stale-verdict', 'optimization_verdict_accepted', 'git_commit'],
      ['stale-integrity', 'integrity_verified', 'server_reconstructed'],
      ['stale-frozen', 'asset_frozen', 'server_reconstructed'],
      ['stale-terminal', 'accepted_rebuild_observed', 'build_run'],
    ]
    for (const [key, eventType, sourceKind] of events) {
      await client.query(
        `INSERT INTO nirmana_elevation_campaign_events
           (campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id,
            layer, evidence_payload, source_kind, source_ref, observed_at, recorded_by)
         VALUES ('nirmana-elevation', 'superseded-rev', $1, $2, 'asset', $3,
                 'L3', '{}'::jsonb, $4, 'f1-regression-test', now(), 'f1-regression-test')`,
        [key, eventType, STALE_ASSET, sourceKind]
      )
    }
  })

  afterAll(async () => {
    if (client) {
      await client.query('DROP SCHEMA IF EXISTS nirmana_evidence CASCADE')
      client.release()
    }
    await pool?.end()
  })

  function runPsqlFile(path: string, extraArgs: string[] = []): string {
    // Fixture-only credential on a disposable database created by this suite
    // (not a production secret) — safe to pass on argv here, unlike the
    // charter's prohibition on production credentials.
    return execFileSync('psql', [TEST_DB_URL!, '-Atq', ...extraArgs, '-f', path], {
      encoding: 'utf8',
      timeout: 30_000,
    })
  }

  it('egate.sql: an evidence chain recorded only under a superseded definition is NOT read as OPEN-PENDING-PIN', () => {
    const output = runPsqlFile(EGATE_SQL_PATH, ['-v', 'layer=L3'])
    const row = output.split('\n').find((line) => line.includes(STALE_ASSET))
    expect(row, `expected a row for ${STALE_ASSET} in egate.sql output:\n${output}`).toBeDefined()
    // -Atq is pipe-delimited: layer|asset_id|kind|unfrozen_ancestors|w2_analysis|w2_verdict|gate|waiting_on
    const fields = row!.split('|')
    const gate = fields[6]
    expect(
      gate,
      'BUG REPRODUCED: egate.sql read a superseded-definition-only evidence chain as current clearance'
    ).toBe('BLOCKED-NO-ROUTE')
    expect(gate).not.toBe('OPEN-PENDING-PIN')
  })

  it('capsule_audit.sql §1: the asset is NOT counted as frozen (it has no event under the frozen definition at all)', () => {
    // §1 only reports assets that ARE frozen (bool_or asset_frozen) — this
    // asset's only asset_frozen event is under the superseded definition, so
    // once correctly scoped it must not appear as `frozen` at all, and so
    // cannot appear in §1's "incomplete chain" output either. Assert via §3's
    // per-layer rollup instead, which is unconditional and directly exercises
    // the same scoping bug (a phantom "frozen" count for L3).
    const output = runPsqlFile(CAPSULE_AUDIT_SQL_PATH)
    const l3Line = output.split('\n').find((line) => /^L3\|/.test(line))
    expect(l3Line, `expected an L3 rollup row in capsule_audit.sql §3 output:\n${output}`).toBeDefined()
    // §3 -Atq: layer|assets|frozen|routed_not_frozen|unrouted|pct_frozen
    const fields = l3Line!.split('|')
    expect(fields[0]).toBe('L3')
    expect(fields[1]).toBe('1') // this fixture's one asset
    expect(
      fields[2],
      'BUG REPRODUCED: capsule_audit.sql §3 counted an asset as "frozen" under the current ' +
        'definition using an asset_frozen event recorded only under a superseded one'
    ).toBe('0')
    expect(fields[4]).toBe('1') // unrouted: no event under 'frozen-rev' at all
  })

  it('once the asset also has a real chain under the frozen definition, both scripts correctly clear it', async () => {
    const events: Array<[string, string, string]> = [
      ['fresh-analysis', 'asset_analysis_accepted', 'git_commit'],
      ['fresh-verdict', 'optimization_verdict_accepted', 'git_commit'],
      ['fresh-integrity', 'integrity_verified', 'server_reconstructed'],
      ['fresh-frozen', 'asset_frozen', 'server_reconstructed'],
      ['fresh-terminal', 'accepted_rebuild_observed', 'build_run'],
    ]
    for (const [key, eventType, sourceKind] of events) {
      await client.query(
        `INSERT INTO nirmana_elevation_campaign_events
           (campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id,
            layer, evidence_payload, source_kind, source_ref, observed_at, recorded_by)
         VALUES ('nirmana-elevation', 'frozen-rev', $1, $2, 'asset', $3,
                 'L3', '{}'::jsonb, $4, 'f1-regression-test', now(), 'f1-regression-test')`,
        [key, eventType, STALE_ASSET, sourceKind]
      )
    }
    const egateOutput = runPsqlFile(EGATE_SQL_PATH, ['-v', 'layer=L3'])
    // Now frozen under the current definition -> excluded from egate.sql's
    // "not yet frozen" listing entirely (its `WHERE a.id NOT IN (SELECT id FROM frozen)`).
    expect(egateOutput.includes(STALE_ASSET)).toBe(false)

    const capsuleOutput = runPsqlFile(CAPSULE_AUDIT_SQL_PATH)
    const l3Line = capsuleOutput.split('\n').find((line) => /^L3\|/.test(line))
    const fields = l3Line!.split('|')
    expect(fields[2]).toBe('1') // frozen, correctly, under the real chain
  })
})
