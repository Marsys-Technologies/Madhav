// @vitest-environment node
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { Pool, type PoolClient } from 'pg'

const databaseUrl = process.env.NIRMANA_CONDUCTOR_TEST_DATABASE_URL
const run = databaseUrl ? describe : describe.skip
const migrationSql = readFileSync(resolve(process.cwd(), 'supabase/migrations/639_nirmana_nonbrowser_conductor.sql'), 'utf8')
const sha = 'a'.repeat(64)
const revision = 'ntap-20260830-test'
const observation = '11111111-1111-4111-8111-111111111111'

run('migration 639 non-browser conductor contract', () => {
  let pool: Pool
  let client: PoolClient
  let leaseId: string

  beforeAll(async () => {
    const parsed = new URL(databaseUrl!)
    if (!['localhost', '127.0.0.1'].includes(parsed.hostname) || parsed.pathname !== '/nirmana_conductor_test') {
      throw new Error('NIRMANA_CONDUCTOR_TEST_DATABASE_URL must target local database nirmana_conductor_test')
    }
    pool = new Pool({ connectionString: databaseUrl })
    client = await pool.connect()
    await client.query(`
      CREATE EXTENSION IF NOT EXISTS pgcrypto;
      CREATE SCHEMA IF NOT EXISTS nirmana_evidence;
      DO $$ BEGIN
        CREATE ROLE nirmana_evidence_owner NOLOGIN;
        CREATE ROLE nirmana_campaign_control_writer LOGIN NOINHERIT;
        CREATE ROLE nirmana_evidence_ingress_writer LOGIN NOINHERIT;
        CREATE ROLE amjis_app LOGIN NOINHERIT;
      EXCEPTION WHEN duplicate_object THEN NULL; END $$;
      ALTER SCHEMA nirmana_evidence OWNER TO nirmana_evidence_owner;
      CREATE TABLE nirmana_evidence.nirmana_elevation_campaign_definitions (
        campaign_id text, definition_revision text, definition_status text, manifest_sha256 text, superseded_at timestamptz
      );
      CREATE TABLE public.nirmana_elevation_monitor_observations (id uuid PRIMARY KEY);
      CREATE TABLE public._migrations_applied (filename text, sha256 text);
    `)
    await client.query(migrationSql)
    await client.query('SET ROLE nirmana_evidence_owner')
    const leased = await client.query(
      `INSERT INTO nirmana_evidence.nirmana_elevation_conductor_leases
         (campaign_id, principal_email, fence, scope, expires_at)
       VALUES ('nirmana-elevation', 'amjis-nirmana-conductor@madhav-astrology.iam.gserviceaccount.com', 1, 'T0,F0,L0', clock_timestamp() + interval '15 minutes')
       RETURNING lease_id::text`,
    )
    leaseId = leased.rows[0].lease_id
    await client.query('RESET ROLE')
  })

  afterAll(async () => {
    if (!pool) return
    client?.release()
    await pool.end()
  })

  it('enforces the receipt lease/fence pair and append-only audit trail', async () => {
    await client.query('SET ROLE nirmana_evidence_owner')
    await expect(client.query(
      `INSERT INTO nirmana_evidence.nirmana_elevation_conductor_receipts
       (campaign_id, idempotency_key, action, lease_id, fence, request_digest_sha256, outcome)
       VALUES ('nirmana-elevation', 'mismatch', 'supersede_definition', $1::uuid, 2, $2, 'blocked')`, [leaseId, sha],
    )).rejects.toThrow(/foreign key/i)

    const inserted = await client.query<{ receipt_id: string }>(
      `INSERT INTO nirmana_evidence.nirmana_elevation_conductor_receipts
       (campaign_id, idempotency_key, action, lease_id, fence, request_digest_sha256, outcome)
       VALUES ('nirmana-elevation', 'exact', 'supersede_definition', $1::uuid, 1, $2, 'blocked') RETURNING receipt_id::text`, [leaseId, sha],
    )
    await expect(client.query(`UPDATE nirmana_evidence.nirmana_elevation_conductor_receipts SET outcome = 'created' WHERE receipt_id = $1::uuid`, [inserted.rows[0].receipt_id]))
      .rejects.toThrow(/append-only/i)
    await client.query('RESET ROLE')
  })

  it('gives the distinct verifier only readiness insertion, narrow receipt reads, and no lease mutation', async () => {
    await client.query('SET ROLE nirmana_evidence_verifier_writer')
    const permittedReceiptFields = await client.query(`SELECT action, outcome FROM nirmana_evidence.nirmana_elevation_conductor_receipts`)
    expect(permittedReceiptFields.rowCount).toBeGreaterThanOrEqual(0)
    await expect(client.query(`SELECT receipt_id FROM nirmana_evidence.nirmana_elevation_conductor_receipts`))
      .rejects.toThrow(/permission denied/i)
    await expect(client.query(`UPDATE nirmana_evidence.nirmana_elevation_conductor_leases SET expires_at = clock_timestamp() WHERE lease_id = $1::uuid`, [leaseId]))
      .rejects.toThrow(/permission denied/i)
    await client.query('RESET ROLE')
  })

  it('records readiness only with policy, definition, release, observation, and fence provenance', async () => {
    await client.query(`INSERT INTO nirmana_evidence.nirmana_elevation_campaign_definitions VALUES ('nirmana-elevation', $1, 'frozen', $2, NULL)`, [revision, sha])
    await client.query(`INSERT INTO public.nirmana_elevation_monitor_observations VALUES ($1::uuid)`, [observation])
    await client.query('SET ROLE nirmana_evidence_verifier_writer')
    await expect(client.query(
      `INSERT INTO nirmana_evidence.nirmana_elevation_conductor_readiness_receipts
       (campaign_id, verifier_principal_email, policy_revision, definition_revision, definition_manifest_sha256,
        main_sha, deployed_sha, cloud_run_revision, migration_set_sha256, source_observation_id, lease_id, fence, verdict, checks, expires_at)
       VALUES ('nirmana-elevation', 'amjis-nirmana-verifier@madhav-astrology.iam.gserviceaccount.com',
         'nirmana-l0-autonomy/v1', $1, $2, $3, $3, 'amjis-web-01808-wvx', $2, $4::uuid, $5::uuid, 1, 'fail', '[]'::jsonb, clock_timestamp() + interval '30 minutes')`,
      [revision, sha, 'b'.repeat(40), observation, leaseId],
    )).resolves.toMatchObject({ rowCount: 1 })
    await client.query('RESET ROLE')
  })
})
