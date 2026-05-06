// One-shot diag — safe to delete.
// Usage: npx tsx --conditions=react-server scripts/diag/check_signal.ts SIG.MSR.150
import 'dotenv/config'
import { query } from '../../src/lib/db/client'

async function main() {
  const signalId = process.argv[2]
  if (!signalId) {
    console.error('Usage: npx tsx scripts/diag/check_signal.ts <signal_id>')
    process.exit(2)
  }
  const res = await query<{
    chunk_id: string
    layer: string
    source_version: string
    is_stale: boolean
    content_len: number | null
    embed_len: number | null
    created_at: string
    embed_created: string | null
  }>(
    `SELECT c.chunk_id,
            c.layer,
            c.source_version,
            c.is_stale,
            LENGTH(c.content) AS content_len,
            LENGTH(e.embedding::text) AS embed_len,
            c.created_at,
            e.created_at AS embed_created
       FROM rag_chunks c
       LEFT JOIN rag_embeddings e ON e.chunk_id = c.chunk_id
      WHERE c.metadata->>'signal_id' = $1
        AND c.doc_type = 'msr_signal'
      LIMIT 1`,
    [signalId]
  )
  if (res.rowCount === 0) {
    console.log(JSON.stringify({ signal_id: signalId, exists: false }, null, 2))
  } else {
    const row = res.rows[0]
    console.log(
      JSON.stringify(
        {
          signal_id: signalId,
          exists: true,
          chunk_id: row.chunk_id,
          layer: row.layer,
          source_version: row.source_version,
          is_stale: row.is_stale,
          content_len: row.content_len,
          embedding_present: (row.embed_len ?? 0) > 0,
          embedding_chars: row.embed_len,
          chunk_created_at: row.created_at,
          embed_created_at: row.embed_created,
        },
        null,
        2
      )
    )
  }
  process.exit(0)
}

main().catch((err) => {
  console.error('check_signal failed:', err)
  process.exit(1)
})
