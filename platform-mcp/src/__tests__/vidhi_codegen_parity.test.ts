/**
 * vidhi_codegen_parity.test.ts — W2 R-1 item 5 CI drift gate (vidhi registry codegen, GT-56)
 * ================================================================================================
 * Design §19 (single-source contract generation) + the r5_codegen_parity.test.ts precedent
 * (GT-9, wired into the `density-census` CI job). That test asserts BEHAVIORAL parity between
 * a generated module and its canonical source (both imported, function outputs compared) — a
 * real and valuable check, but one that would NOT have caught GT-56: the canonical
 * `platform/src/lib/vidhi/registry_data.ts` and its hand-synced `platform-mcp/src/resources/
 * vidhi/registry_data.ts` mirror had identical DATA (so a behavioral/deep-equal comparison of
 * the exported constants passes clean — see `vidhi_registry_parity.test.ts`, D-2 Lane V-2's
 * own drift guard, which is exactly that kind of test and does NOT catch this drift) but had
 * diverged on the raw SOURCE TEXT of one import line (`'./types'` vs `'./types.js'`), with no
 * gate checking the source text itself.
 *
 * THIS test closes that specific gap: it imports the generator's `generate()` function
 * directly (platform/scripts/generate_vidhi_registry_mirror.ts, exported for exactly this
 * purpose — importing it does NOT trigger a file write or `process.exit()`; see that module's
 * entrypoint guard) and asserts the byte-for-byte string it would produce RIGHT NOW is
 * identical to the currently-committed `platform-mcp/src/resources/vidhi/registry_data.ts`.
 * A future edit to the canonical source that isn't followed by `npm run codegen:vidhi` (in
 * platform/) fails this test loudly, in CI, before merge — the exact class of drift GT-56
 * found happening silently.
 *
 * Cross-package import in a TEST is the established pattern here (see r5_codegen_parity.test.ts
 * importing platform/src/... directly, and vidhi_registry_parity.test.ts importing
 * platform/src/lib/vidhi/* directly) — it runs only in the test process (vitest, via tsx/esbuild
 * transform), never in the shipped MCP build (which cannot cross the package's rootDir).
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { generate, OUTPUT_PATH } from '../../../platform/scripts/generate_vidhi_registry_mirror.ts'

describe('vidhi registry codegen parity — regenerating now matches the committed mirror (GT-56)', () => {
  it('generate() output is byte-identical to the committed platform-mcp/src/resources/vidhi/registry_data.ts', () => {
    const { generated } = generate()
    const committed = readFileSync(OUTPUT_PATH, 'utf8')
    expect(generated).toBe(committed)
  })

  it('the generated file carries the NodeNext .js extension the canonical source lacks (the exact GT-56 drift line)', () => {
    const { generated } = generate()
    expect(generated).toContain("from './types.js'")
    expect(generated).not.toMatch(/from '\.\/types';/)
  })

  it('generate() is deterministic (two consecutive calls produce identical output)', () => {
    const first = generate()
    const second = generate()
    expect(first.generated).toBe(second.generated)
    expect(first.sourceHash).toBe(second.sourceHash)
  })
})
