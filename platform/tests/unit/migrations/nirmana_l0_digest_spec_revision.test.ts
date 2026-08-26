import fs from 'node:fs'
import path from 'node:path'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/609_nirmana_l0_digest_spec_revision.sql',
)
const migration = fs.existsSync(migrationPath) ? fs.readFileSync(migrationPath, 'utf8') : ''

const OLD_REFERENCE = '7f29bb1a2a6082096fd365bde66b817ca82c7cf2e56d40ee16e30ebdd4466fb3'
const NEW_REFERENCE = '89e71583339838a72bde5ead48dd0a901b144ff1493d8c825b60ecbf4f39524f'
const OLD_TEXTS = 'c29c5ed004e16cf59f051882c805e458d0070619181829d4e989d6b213c80931'
const NEW_TEXTS = '10416cda800b6bd6d606f8daee76b06928071d66b09ff733a3b48ebc734c02f6'
const migration600 = fs.readFileSync(
  path.resolve(process.cwd(), 'supabase/migrations/600_nirmana_l0_wave0_output_digest_specs.sql'),
  'utf8',
)

function specFromMigration600(assetId: string): Record<string, unknown> {
  const match = migration600.match(new RegExp(
    `\\('${assetId}','[a-f0-9]{64}','({.+?})'::jsonb\\)`,
  ))
  if (!match) throw new Error(`migration 600 spec missing for ${assetId}`)
  return JSON.parse(match[1])
}

const OLD_REFERENCE_SPEC = specFromMigration600('bg_reference')
const OLD_TEXTS_SPEC = specFromMigration600('bg_texts')

describe('migration 609 — append-only L0 digest revisions', () => {
  it('does not rewrite committed migration 600 and carries exact reviewed replacements', () => {
    expect(migration600).toContain(OLD_REFERENCE)
    expect(migration600).toContain(OLD_TEXTS)
    expect(migration600).not.toContain(NEW_REFERENCE)
    expect(migration600).not.toContain(NEW_TEXTS)
    expect(migration).toContain(NEW_REFERENCE)
    expect(migration).toContain(NEW_TEXTS)
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)
  })
})

const TEST_DATABASE_URL = process.env.NIRMANA_L0_DIGEST_REVISION_TEST_DATABASE_URL

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_l0_digest_revision_test') {
    throw new Error(
      'NIRMANA_L0_DIGEST_REVISION_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_l0_digest_revision_test database',
    )
  }
}

describe.skipIf(!TEST_DATABASE_URL)('migration 609 — real Postgres behavior', () => {
  async function connectPrepared(): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await client.query(`
      DROP TABLE IF EXISTS asset_provenance_receipts, asset_output_digest_specs CASCADE;
      CREATE TABLE asset_output_digest_specs (
        asset_id text NOT NULL,
        spec_sha256 text NOT NULL,
        spec jsonb NOT NULL,
        reviewed_at timestamptz NOT NULL DEFAULT now(),
        retired_at timestamptz,
        PRIMARY KEY (asset_id, spec_sha256)
      );
      CREATE UNIQUE INDEX asset_output_digest_specs_one_current
        ON asset_output_digest_specs (asset_id) WHERE retired_at IS NULL;
      CREATE TABLE asset_provenance_receipts (
        receipt_id bigserial PRIMARY KEY,
        asset_id text NOT NULL,
        output_digest_spec_sha256 text,
        FOREIGN KEY (asset_id, output_digest_spec_sha256)
          REFERENCES asset_output_digest_specs(asset_id, spec_sha256)
      );
    `)
    await client.query(`
      INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec) VALUES
        ('bg_reference', $1, $2::jsonb),
        ('bg_texts', $3, $4::jsonb)
    `, [OLD_REFERENCE, JSON.stringify(OLD_REFERENCE_SPEC), OLD_TEXTS, JSON.stringify(OLD_TEXTS_SPEC)])
    await client.query(`
      INSERT INTO asset_provenance_receipts (asset_id, output_digest_spec_sha256) VALUES
        ('bg_reference', $1), ('bg_texts', $2)
    `, [OLD_REFERENCE, OLD_TEXTS])
    return client
  }

  it('retires but preserves referenced predecessors, installs replacements, and replays', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      await client.query(migration)
      const current = await client.query(`
        SELECT asset_id, spec_sha256 FROM asset_output_digest_specs
        WHERE retired_at IS NULL ORDER BY asset_id
      `)
      expect(current.rows).toEqual([
        { asset_id: 'bg_reference', spec_sha256: NEW_REFERENCE },
        { asset_id: 'bg_texts', spec_sha256: NEW_TEXTS },
      ])
      const predecessors = await client.query(`
        SELECT asset_id, spec_sha256, retired_at IS NOT NULL AS retired
        FROM asset_output_digest_specs
        WHERE spec_sha256 = ANY($1::text[]) ORDER BY asset_id
      `, [[OLD_REFERENCE, OLD_TEXTS]])
      expect(predecessors.rows).toEqual([
        { asset_id: 'bg_reference', spec_sha256: OLD_REFERENCE, retired: true },
        { asset_id: 'bg_texts', spec_sha256: OLD_TEXTS, retired: true },
      ])
      const receipts = await client.query(`
        SELECT count(*)::int AS n FROM asset_provenance_receipts receipt
        JOIN asset_output_digest_specs spec
          ON spec.asset_id = receipt.asset_id
         AND spec.spec_sha256 = receipt.output_digest_spec_sha256
      `)
      expect(receipts.rows).toEqual([{ n: 2 }])
    } finally {
      await client.end()
    }
  })

  it('rejects unknown current drift atomically before retiring either asset', async () => {
    const client = await connectPrepared()
    try {
      await client.query(`
        UPDATE asset_output_digest_specs SET retired_at = now()
        WHERE asset_id = 'bg_texts' AND spec_sha256 = '${OLD_TEXTS}';
        INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
        VALUES ('bg_texts', repeat('a', 64), '{"version":"unknown-drift"}')
      `)
      await expect(client.query(migration)).rejects.toThrow(/unknown current.*bg_texts/i)
      const rows = await client.query(`
        SELECT asset_id, spec_sha256
        FROM asset_output_digest_specs
        WHERE retired_at IS NULL ORDER BY asset_id
      `)
      expect(rows.rows).toEqual([
        { asset_id: 'bg_reference', spec_sha256: OLD_REFERENCE },
        { asset_id: 'bg_texts', spec_sha256: 'a'.repeat(64) },
      ])
      const replacements = await client.query(`
        SELECT count(*)::int AS n FROM asset_output_digest_specs
        WHERE spec_sha256 = ANY($1::text[])
      `, [[NEW_REFERENCE, NEW_TEXTS]])
      expect(replacements.rows).toEqual([{ n: 0 }])
    } finally {
      await client.end()
    }
  })

  it('rejects accepted SHA labels paired with corrupt predecessor or current JSON', async () => {
    const predecessorClient = await connectPrepared()
    try {
      await predecessorClient.query(`
        UPDATE asset_output_digest_specs
        SET spec = jsonb_set(spec, '{version}', '"corrupt"'::jsonb)
        WHERE asset_id='bg_texts' AND spec_sha256=$1
      `, [OLD_TEXTS])
      await expect(predecessorClient.query(migration)).rejects.toThrow(
        /unknown current.*bg_texts/i,
      )
      const replacements = await predecessorClient.query(`
        SELECT count(*)::int AS n FROM asset_output_digest_specs
        WHERE spec_sha256 = ANY($1::text[])
      `, [[NEW_REFERENCE, NEW_TEXTS]])
      expect(replacements.rows).toEqual([{ n: 0 }])
    } finally {
      await predecessorClient.end()
    }

    const currentClient = await connectPrepared()
    try {
      await currentClient.query(migration)
      await currentClient.query(`
        UPDATE asset_output_digest_specs
        SET spec = jsonb_set(spec, '{version}', '"corrupt"'::jsonb)
        WHERE asset_id='bg_texts' AND spec_sha256=$1
      `, [NEW_TEXTS])
      await expect(currentClient.query(migration)).rejects.toThrow(
        /unknown current.*bg_texts/i,
      )
      const current = await currentClient.query(`
        SELECT spec->>'version' AS version
        FROM asset_output_digest_specs
        WHERE asset_id='bg_texts' AND retired_at IS NULL
      `)
      expect(current.rows).toEqual([{ version: 'corrupt' }])
    } finally {
      await currentClient.end()
    }
  })
})
