/**
 * backfill_manifest.ts — populate CAPABILITY_MANIFEST.json `query_schema`
 * fields from the unified Tool Contract registry.
 *
 * Run manually: `npx tsx src/lib/contract/scripts/backfill_manifest.ts`
 * Idempotent — only writes when a contract-known tool entry has an empty
 * or missing query_schema. Re-running is a no-op once green.
 */

import path from 'path'
import fs from 'fs'
import { TOOL_CONTRACTS } from '../registry'
import { zodToJsonSchema } from '../json_schema'

// Resolve from cwd up to the worktree root. Run from platform/ (the workspace
// vitest+tsx are run from); cwd will be .../platform; manifest is at
// ../00_ARCHITECTURE/CAPABILITY_MANIFEST.json.
const MANIFEST_PATH = path.resolve(process.cwd(), '..', '00_ARCHITECTURE', 'CAPABILITY_MANIFEST.json')

function main(): void {
  if (!fs.existsSync(MANIFEST_PATH)) {
    throw new Error(`manifest not found: ${MANIFEST_PATH}`)
  }

  const manifestRaw = fs.readFileSync(MANIFEST_PATH, 'utf8')
  const manifest = JSON.parse(manifestRaw) as { entries: Array<Record<string, unknown>> }

  // Build {canonical_name → JSON-Schema} from the contract registry.
  const schemasByName: Record<string, ReturnType<typeof zodToJsonSchema>> = {}
  for (const c of TOOL_CONTRACTS) {
    schemasByName[c.canonical_name] = zodToJsonSchema(c.input_schema)
  }

  let touched = 0
  for (const entry of manifest.entries) {
    const name = (entry['tool_name'] ?? entry['retrieval_tool']) as string | undefined
    if (!name || !(name in schemasByName)) continue

    const existing = entry['query_schema'] as
      | { properties?: Record<string, unknown> }
      | undefined
    const isEmpty =
      existing === undefined ||
      existing === null ||
      typeof existing !== 'object' ||
      !existing.properties ||
      Object.keys(existing.properties).length === 0

    if (isEmpty) {
      entry['query_schema'] = schemasByName[name] as unknown as Record<string, unknown>
      touched++
    }
  }

  fs.writeFileSync(MANIFEST_PATH, JSON.stringify(manifest, null, 2) + '\n', 'utf8')
  // eslint-disable-next-line no-console
  console.log(`backfill_manifest: touched ${touched} entries across ${TOOL_CONTRACTS.length} contracts.`)
}

main()
