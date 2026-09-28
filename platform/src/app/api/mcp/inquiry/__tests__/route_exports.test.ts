import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'

// Next.js rejects any route.ts export outside its permitted set at `next build` time; `tsc` and
// vitest do not. Helpers such as the bounded body reader live in ./bounded_body for this reason.
const PERMITTED = new Set([
  'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS',
  'maxDuration', 'dynamic', 'runtime', 'revalidate', 'fetchCache', 'dynamicParams', 'preferredRegion',
])

export function nonPermittedRouteExports(source: string): string[] {
  const exported = [...source.matchAll(/^export\s+(?:async\s+)?(?:function|const|let|var|class|type|interface)\s+([A-Za-z0-9_]+)/gm)]
    .map((match) => match[1]!)
  return exported.filter((name) => !PERMITTED.has(name))
}

describe('inquiry route.ts exports only what Next.js permits', () => {
  it('exports no helper or type alongside the HTTP handlers', () => {
    const source = readFileSync(new URL('../route.ts', import.meta.url), 'utf8')
    expect(source).toMatch(/^export\s+async\s+function\s+POST\b/m)
    expect(nonPermittedRouteExports(source)).toEqual([])
    expect(source).not.toMatch(/^export\s*\{/m)
  })

  it('detects the exact regression that failed the Next.js build (negative control)', () => {
    const regressed = 'export const maxDuration = 60\nexport async function readBoundedRequestBody() {}\nexport type BoundedBodyResult = never\nexport async function POST() {}\n'
    expect(nonPermittedRouteExports(regressed)).toEqual(['readBoundedRequestBody', 'BoundedBodyResult'])
  })
})
