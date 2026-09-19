import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

describe('chart_facts build_id schema contract', () => {
  it('declares build_id as UUID in the canonical chart_facts migration', () => {
    const migration = readFileSync(
      join(process.cwd(), 'supabase/migrations/204_chart_facts.sql'),
      'utf8',
    ).replace(/\s+/g, ' ')

    expect(migration).toMatch(/CREATE TABLE IF NOT EXISTS chart_facts \([^;]* build_id UUID NOT NULL,/)
  })

  it('does not compare chart_facts build_id against text in Batch 3 retrieval paths', () => {
    const sourcePaths = [
      'src/lib/retrieval/ranking/l1_context_fetcher.ts',
      'src/lib/retrieval/registry/layers/register_d9_judgment.ts',
      'src/lib/retrieval/registry/layers/reading_checklist.ts',
      'src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts',
      'src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts',
      'src/lib/retrieval/registry/layers/L1_ganita/get_kp_cusps.ts',
    ]

    for (const sourcePath of sourcePaths) {
      const source = readFileSync(join(process.cwd(), sourcePath), 'utf8')
      expect(source, sourcePath).not.toMatch(/build_id\s*=\s*[^\n]*::text/)
    }

    const resolver = readFileSync(
      join(process.cwd(), 'src/lib/retrieval/address_resolver.ts'),
      'utf8',
    )
    expect(resolver).toMatch(/function factBuildFence[\s\S]*?build_id = \$\$\{param\}::uuid[\s\S]*?\n\}/)
    expect(resolver).toMatch(/function divisionalBuildFence[\s\S]*?build_id = \$\$\{param\}::text AND build_id_uuid = \$\$\{param\}::uuid[\s\S]*?\n\}/)
  })
})
