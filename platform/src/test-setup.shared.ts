import { vi } from 'vitest'

// Environment-agnostic setup shared by BOTH vitest projects (see vitest.config.ts).
// Nothing in this file may touch a DOM global — the `node` project loads it too.
//
// Split out of src/test-setup.ts by the CI efficiency audit (2026-07-31). Before
// the split, `environment: 'jsdom'` was global and every one of the ~710 test files
// paid ~0.33s of jsdom construction (measured: 702s cumulative `environment` time
// for a 366s wall). Only ~140 files actually need a DOM. The mocks below, however,
// are needed by node-env tests too — `@/lib/db/monitoring-write` carries
// `import 'server-only'` and is reached transitively by nearly every retrieve tool —
// so they live here rather than in the jsdom-only setup.

// `next/navigation` (useRouter etc.) is not available outside a Next runtime; stub
// globally so panchang components that use AskMadhavLink (which calls useRouter)
// don't throw during unit tests. 4C-8 introduced AskMadhavLink to PrimaryStrip /
// SpecialYogasList / PlanetaryGrid — this mock prevents those tests from breaking.
// Individual test files that need full routing behaviour should override locally.
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn(), forward: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/',
  useParams: () => ({}),
}))

// `@/lib/db/monitoring-write` carries `import 'server-only'`, which refuses to
// load under jsdom. Every retrieve tool now imports `writeToolExecutionLog`
// from this module (MON-7); without a global stub, every transitively-touching
// test file would have to declare its own vi.mock. This stub is opt-out: any
// test that needs the real module can override with a local vi.mock.
vi.mock('@/lib/db/monitoring-write', () => ({
  writeLlmCallLog: vi.fn(),
  writeQueryPlanLog: vi.fn(),
  writeToolExecutionLog: vi.fn(),
  writeContextAssemblyLog: vi.fn(),
  resolveProvider: vi.fn(() => 'mock'),
}))
