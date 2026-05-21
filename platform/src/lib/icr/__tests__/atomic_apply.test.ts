/**
 * atomic_apply.test.ts — Unit tests for ICR atomic apply infrastructure
 *
 * ICR-S5 (2026-05-21)
 *
 * Tests use os.tmpdir() for all file paths — the real MSR/RESOLVED/ directories
 * are NEVER touched by these tests. Real file writes are used for live-apply tests
 * (no vi.mock on node:fs) to exercise the actual I/O path in a tmp directory.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import {
  mkdtempSync,
  writeFileSync,
  readFileSync,
  existsSync,
  mkdirSync,
  rmSync,
} from 'node:fs'
import * as os from 'node:os'
import * as path from 'node:path'
import { atomicApply, resolveTargetPath } from '../atomic_apply'

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

/** Build a minimal PROPOSED/ YAML string for tests. */
function buildProposedYaml(overrides: {
  signal_id?: string
  current_value?: string
  proposed_value?: string
} = {}): string {
  const {
    signal_id = 'MSR.377',
    current_value = 'Muntha in Gemini 3H = UL/Spouse-Domain Annual Activation',
    proposed_value = 'Muntha in Virgo 6H = Dusthana Annual Activation (6H: Health/Service/Conflict)',
  } = overrides
  return [
    'conflict_id: DIS.013',
    `signal_id: ${signal_id}`,
    'field: signal_name',
    `current_value: "${current_value}"`,
    `proposed_value: "${proposed_value}"`,
    'rationale: "Test rationale"',
    'propagation_chain:',
    '  - "MSR.377 signal_name"',
    'proposed_at: 2026-05-21T09:44:33.370Z',
    'status: proposed',
  ].join('\n') + '\n'
}

/**
 * Set up a minimal tmp repo layout:
 *   <root>/PROPOSED/DIS.013_MSR_377_proposed.yaml
 *   <root>/025_HOLISTIC_SYNTHESIS/MSR_v3_0.md  (contains current_value)
 */
function setupTmpRepo(opts: {
  currentValue?: string
  proposedValue?: string
  targetContent?: string
} = {}): {
  repoRoot: string
  proposedPath: string
  targetPath: string
  currentValue: string
} {
  const currentValue = opts.currentValue ?? 'Muntha in Gemini 3H = UL/Spouse-Domain Annual Activation'
  const proposedValue = opts.proposedValue ?? 'Muntha in Virgo 6H = Dusthana Annual Activation (6H: Health/Service/Conflict)'

  const repoRoot = mkdtempSync(path.join(os.tmpdir(), 'icr-test-'))

  // Create PROPOSED/ dir and artifact
  const proposedDir = path.join(repoRoot, 'PROPOSED')
  mkdirSync(proposedDir, { recursive: true })
  const proposedPath = path.join(proposedDir, 'DIS.013_MSR_377_proposed.yaml')
  writeFileSync(proposedPath, buildProposedYaml({ current_value: currentValue, proposed_value: proposedValue }), 'utf-8')

  // Create synthesis file
  const synthDir = path.join(repoRoot, '025_HOLISTIC_SYNTHESIS')
  mkdirSync(synthDir, { recursive: true })
  const targetPath = path.join(synthDir, 'MSR_v3_0.md')
  const targetContent = opts.targetContent ?? `SIG.MSR.377:\n  signal_name: "${currentValue}"\n  signal_type: tajika-pattern\n`
  writeFileSync(targetPath, targetContent, 'utf-8')

  return { repoRoot, proposedPath, targetPath, currentValue }
}

// ─────────────────────────────────────────────────────────────────────────────
// Cleanup
// ─────────────────────────────────────────────────────────────────────────────

let tmpDirs: string[] = []

afterEach(() => {
  for (const d of tmpDirs) {
    try { rmSync(d, { recursive: true, force: true }) } catch { /* best-effort */ }
  }
  tmpDirs = []
})

function tracked<T extends { repoRoot: string }>(setup: T): T {
  tmpDirs.push(setup.repoRoot)
  return setup
}

// ─────────────────────────────────────────────────────────────────────────────
// resolveTargetPath
// ─────────────────────────────────────────────────────────────────────────────

describe('resolveTargetPath', () => {
  it('resolves MSR.* to MSR_v3_0.md', () => {
    const result = resolveTargetPath('MSR.377', '/repo')
    expect(result).toBe('/repo/025_HOLISTIC_SYNTHESIS/MSR_v3_0.md')
  })

  it('resolves UCN.* to UCN_v4_0.md', () => {
    const result = resolveTargetPath('UCN.45', '/repo')
    expect(result).toBe('/repo/025_HOLISTIC_SYNTHESIS/UCN_v4_0.md')
  })

  it('returns null for unknown prefix', () => {
    const result = resolveTargetPath('CDLM.5', '/repo')
    expect(result).toBeNull()
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// atomicApply — dry run
// ─────────────────────────────────────────────────────────────────────────────

describe('atomicApply (dry run)', () => {
  it('returns ok:true when current_value is present in target file', () => {
    const { repoRoot, proposedPath } = tracked(setupTmpRepo())

    const result = atomicApply(proposedPath, repoRoot, true)

    expect(result.ok).toBe(true)
    if (result.ok) {
      expect(result.resolved_path).toContain('RESOLVED')
      expect(result.resolved_path).toContain('DIS.013_MSR_377_resolved.yaml')
      expect(result.backup_path).toContain('MSR_v3_0.md.icr_bak')
    }

    // Dry run: no files written
    expect(existsSync(path.join(repoRoot, 'RESOLVED'))).toBe(false)
    expect(existsSync(proposedPath)).toBe(true) // PROPOSED/ artifact untouched
  })

  it('returns ok:false when current_value is not found in target file', () => {
    const { repoRoot, proposedPath } = tracked(setupTmpRepo({
      // target file does NOT contain the current_value string
      targetContent: 'SIG.MSR.377:\n  signal_name: "Already corrected Virgo 6H"\n',
    }))

    const result = atomicApply(proposedPath, repoRoot, true)

    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error).toMatch(/current_value not found/)
    }
  })

  it('returns ok:false for unreadable proposed artifact', () => {
    const result = atomicApply('/nonexistent/path/DIS.013_proposed.yaml', '/any/root', true)

    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error).toMatch(/Failed to read proposed artifact/)
    }
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// atomicApply — live apply
// ─────────────────────────────────────────────────────────────────────────────

describe('atomicApply (live apply)', () => {
  it('replaces current_value with proposed_value and moves artifact to RESOLVED/', () => {
    const currentValue = 'Muntha in Gemini 3H = UL/Spouse-Domain Annual Activation'
    const proposedValue = 'Muntha in Virgo 6H = Dusthana Annual Activation (6H: Health/Service/Conflict)'
    const { repoRoot, proposedPath, targetPath } = tracked(setupTmpRepo({ currentValue, proposedValue }))

    const result = atomicApply(proposedPath, repoRoot, false)

    expect(result.ok).toBe(true)

    // Target file updated
    const updatedContent = readFileSync(targetPath, 'utf-8')
    expect(updatedContent).toContain(proposedValue)
    expect(updatedContent).not.toContain(`"${currentValue}"`)

    // PROPOSED/ artifact is gone
    expect(existsSync(proposedPath)).toBe(false)

    // RESOLVED/ artifact exists
    if (result.ok) {
      expect(existsSync(result.resolved_path)).toBe(true)
      expect(result.resolved_path).toContain('DIS.013_MSR_377_resolved.yaml')
    }

    // Backup removed on success
    const backupPath = targetPath + '.icr_bak'
    expect(existsSync(backupPath)).toBe(false)
  })

  it('returns ok:false without corrupting file when PROPOSED/ artifact is already missing', () => {
    // Simulate a scenario where the proposed file path points to a non-existent file
    const { repoRoot, targetPath } = tracked(setupTmpRepo())
    const missingProposedPath = path.join(repoRoot, 'PROPOSED', 'nonexistent_proposed.yaml')
    const originalContent = readFileSync(targetPath, 'utf-8')

    const result = atomicApply(missingProposedPath, repoRoot, false)

    expect(result.ok).toBe(false)

    // Target file must be untouched
    const contentAfter = readFileSync(targetPath, 'utf-8')
    expect(contentAfter).toBe(originalContent)
  })
})
