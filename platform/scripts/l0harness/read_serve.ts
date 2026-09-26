/**
 * read_serve.ts — W-L0-7 readings-runner serve bridge
 * =====================================================
 * Invokes the REAL deployed serve handlers (no SQL re-derivation):
 *   R2 → get_yoga_firings  (platform/src/lib/retrieval/registry/layers/L1_ganita/get_yoga_firings.ts)
 *   C0 → query_yoga_catalog (platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_yoga_catalog.ts)
 *
 * Usage (cwd = platform/):
 *   DATABASE_URL=postgres://data_plane_builder@127.0.0.1:55433/madhav_l0w7_fixture \
 *     node_modules/.bin/tsx -C react-server scripts/l0harness/read_serve.ts R2 '{"chart_id":"…","yoga_canonical_id":"sunapha","all":true}'
 *
 * `-C react-server` is required: src/lib/db/client.ts:1 imports 'server-only',
 * whose package exports resolve to a throwing module under the default condition
 * and to the empty module under the `react-server` condition.
 *
 * DATABASE_URL selects the database + role (src/lib/db/client.ts:46-52 pools on
 * it). The harness connects as data_plane_builder: the fixture's
 * production-probed grants give amjis_app NO SELECT on ga_yoga_firings
 * (role_table_grants probe 2026-09-26), so the production serving role cannot
 * run R2 against the fixture; data_plane_builder holds SELECT. Disclosed in
 * REHEARSAL_NOTES.md.
 *
 * Output: one JSON line on stdout — the handler's own return value verbatim
 * ({content, is_error}). Exit 2 on transport-level failure.
 */
import { getYogaFiringsCapability } from '@/lib/retrieval/registry/layers/L1_ganita/get_yoga_firings'
import { queryYogaCatalogCapability } from '@/lib/retrieval/registry/layers/L0_brahmagyan/query_yoga_catalog'

const [tool, argsJson] = process.argv.slice(2)

const capabilities = {
  R2: getYogaFiringsCapability,
  C0: queryYogaCatalogCapability,
} as const

async function main(): Promise<void> {
  const cap = capabilities[tool as keyof typeof capabilities]
  if (!cap) {
    console.error(`unknown tool ${JSON.stringify(tool)} — expected R2 or C0`)
    process.exit(2)
  }
  const args = argsJson ? JSON.parse(argsJson) : {}
  const result = await cap.handler(args as Record<string, unknown>, null)
  process.stdout.write(JSON.stringify(result) + '\n')
  process.exit(0)
}

main().catch((err) => {
  console.error(String(err && (err as Error).stack ? (err as Error).stack : err))
  process.exit(2)
})
