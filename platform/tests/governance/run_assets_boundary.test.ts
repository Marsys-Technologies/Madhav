import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { inspectRunAssetsBoundary } from './run_assets_boundary'

const route = readFileSync(resolve(process.cwd(), 'src/app/api/cockpit/runs/[id]/assets/route.ts'), 'utf8')
const owner = readFileSync(resolve(process.cwd(), 'src/lib/build/runAssets.ts'), 'utf8')

describe('exact Portal/Identity/Build run-assets boundary', () => {
  it('connects the current route to the declared read owner', () => {
    expect(inspectRunAssetsBoundary(route, owner)).toEqual([])
  })

  it.each([
    ['missing owner call', route.replace('await readBuildRunAssets(id)', '[]'), owner],
    ['new Portal SQL', route.replace('await readBuildRunAssets(id)', "await query('SELECT * FROM build_runs')"), owner],
    ['swapped private owner', route.replace("'@/lib/build/runAssets'", "'@/lib/unrelated/runAssets'"), owner],
    ['changed Identity namespace', route.replace('FROM profiles', 'FROM asset_registry'), owner],
    ['changed admission role', route.replace("'super_admin'", "'guest'"), owner],
    ['replacement SQL despite equal query count', route, owner.replace('FROM build_run_assets bra', 'FROM chart_facts bra')],
    ['changed chart/global precedence', route, owner.replace('(chart_id IS NOT NULL) DESC', '(chart_id IS NOT NULL) ASC')],
    ['wrong id bind', route, owner.replace('`, [id])', '`, [])')],
    ['mutated run id', route, owner.replace('  const includeBlockedBy', "  id = 'other-run'\n  const includeBlockedBy")],
    ['unsafe optional column', route, owner.replace("'NULL::text AS blocked_by_asset_id'", "'bra.blocked_by_asset_id'")],
    ['discarded probe result', route, owner.replace('await blockedByAssetIdColumnPresent()', 'true')],
    ['raw query escape', route, `${owner}\nconst escaped = query\n`],
    ['new dynamic driver import', route, `${owner}\nvoid import('pg')\n`],
    ['stale missing owner export', route, owner.replace('function readBuildRunAssets(', 'function renamedReadOwner(')],
  ])('rejects %s', (_label, mutatedRoute, mutatedOwner) => {
    expect(inspectRunAssetsBoundary(mutatedRoute, mutatedOwner).length).toBeGreaterThan(0)
  })
})
