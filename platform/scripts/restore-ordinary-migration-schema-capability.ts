import { Client } from 'pg'

const databaseUrl = process.env.DATABASE_URL

async function main(): Promise<void> {
  if (!databaseUrl) throw new Error('DATABASE_URL is required to restore the ordinary migration schema capability.')
  const client = new Client({ connectionString: databaseUrl })
  await client.connect()
  try {
    await client.query('BEGIN')
    await client.query('SET LOCAL ROLE data_plane_schema_owner')
    await client.query('GRANT USAGE, CREATE ON SCHEMA public TO amjis_app')
    await client.query('COMMIT')
    console.log('Restored ordinary migration public-schema capability.')
  } catch (error) {
    await client.query('ROLLBACK').catch(() => undefined)
    throw error
  } finally {
    await client.end()
  }
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
