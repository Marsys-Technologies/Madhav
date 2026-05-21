/**
 * coverage_gate.test.ts — COV-S7
 *
 * Vitest unit tests for platform/scripts/governance/coverage_gate.py.
 * Uses synthetic fixture directories to verify:
 *   - A PR that wires a new retrieval tool without a manifest entry fails (exit non-zero)
 *   - A PR that wires a tool WITH a manifest entry passes (exit 0)
 *   - --dry-run always exits 0 regardless of gaps
 *
 * Named gate: synthetic_pr_coverage_gate_fails
 */

import { describe, it, expect } from 'vitest'
import { execSync } from 'node:child_process'
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { resolve } from 'node:path'

const GATE_SCRIPT = resolve(__dirname, '../../scripts/governance/coverage_gate.py')

/**
 * Creates a minimal synthetic repo tree that the coverage_gate.py can read.
 *
 * Structure:
 *   <tmpdir>/
 *     platform/src/lib/retrieve/
 *       index.ts                  — imports synthetic_tool
 *       synthetic_tool.ts         — defines TOOL_NAME = 'synthetic_tool'
 *     00_ARCHITECTURE/
 *       manifest_overrides.yaml   — controlled by caller
 *       CAPABILITY_MANIFEST.json  — empty entries (caller controls overrides)
 */
function createSyntheticRepo(opts: {
  manifestHasTool: boolean
  toolName?: string
}): string {
  const toolName = opts.toolName ?? 'synthetic_tool'
  const tmpDir = mkdtempSync(join(tmpdir(), 'coverage_gate_test_'))

  // platform/src/lib/retrieve/
  const retrieveDir = join(tmpDir, 'platform', 'src', 'lib', 'retrieve')
  mkdirSync(retrieveDir, { recursive: true })

  // index.ts — imports and re-exports the synthetic tool
  writeFileSync(
    join(retrieveDir, 'index.ts'),
    [
      `import * as syntheticTool from './${toolName}'`,
      ``,
      `export const RETRIEVAL_TOOLS = [`,
      `  syntheticTool.tool,`,
      `]`,
    ].join('\n'),
  )

  // synthetic_tool.ts — defines TOOL_NAME
  writeFileSync(
    join(retrieveDir, `${toolName}.ts`),
    [
      `const TOOL_NAME = '${toolName}'`,
      ``,
      `export const tool = {`,
      `  name: TOOL_NAME,`,
      `  version: '1.0.0',`,
      `  description: 'Synthetic test tool for coverage gate tests',`,
      `  retrieve: async () => ({ items: [] }),`,
      `}`,
    ].join('\n'),
  )

  // 00_ARCHITECTURE/
  const archDir = join(tmpDir, '00_ARCHITECTURE')
  mkdirSync(archDir, { recursive: true })

  // CAPABILITY_MANIFEST.json — always empty entries
  writeFileSync(
    join(archDir, 'CAPABILITY_MANIFEST.json'),
    JSON.stringify({ entries: [] }, null, 2),
  )

  // manifest_overrides.yaml — controlled by opts.manifestHasTool
  const additionalEntries = opts.manifestHasTool
    ? [
        `  - canonical_id: "RETRIEVAL_TOOL_${toolName}"`,
        `    tool_name: "${toolName}"`,
        `    tool_description: "Synthetic tool for testing"`,
        `    expose_to_planner: true`,
        `    layer: "L1"`,
        `    expose_to_chat: true`,
        `    native_id: "test"`,
      ].join('\n')
    : `  []`

  writeFileSync(
    join(archDir, 'manifest_overrides.yaml'),
    [
      `# synthetic fixture`,
      `overrides: {}`,
      `mirror_pairs: {}`,
      `additional_entries:`,
      additionalEntries,
      ``,
    ].join('\n'),
  )

  return tmpDir
}

function runGate(repoRoot: string, extraArgs = ''): { exitCode: number; output: string } {
  try {
    const output = execSync(
      `python3 "${GATE_SCRIPT}" --repo-root "${repoRoot}" ${extraArgs}`,
      { encoding: 'utf-8', stdio: 'pipe' },
    )
    return { exitCode: 0, output }
  } catch (err: unknown) {
    const e = err as { status?: number; stdout?: string; stderr?: string }
    return {
      exitCode: e.status ?? 1,
      output: (e.stdout ?? '') + (e.stderr ?? ''),
    }
  }
}

describe('coverage_gate.py — COV-S7', () => {
  it('synthetic_pr_coverage_gate_fails — missing tool → exit non-zero', () => {
    // This is the named gate: a synthetic PR that wires a tool without
    // a manifest entry must cause the coverage gate to fail.
    const tmpDir = createSyntheticRepo({ manifestHasTool: false })
    try {
      const { exitCode, output } = runGate(tmpDir)
      expect(
        exitCode,
        `Expected non-zero exit (gate should fail). Output:\n${output}`,
      ).not.toBe(0)
      expect(output).toContain('synthetic_tool')
      expect(output).toContain('ERROR')
    } finally {
      rmSync(tmpDir, { recursive: true, force: true })
    }
  })

  it('passing_case — tool present in manifest → exit 0', () => {
    const tmpDir = createSyntheticRepo({ manifestHasTool: true })
    try {
      const { exitCode, output } = runGate(tmpDir)
      expect(
        exitCode,
        `Expected exit 0 (gate should pass). Output:\n${output}`,
      ).toBe(0)
      // No ERROR lines expected
      expect(output).not.toContain('ERROR tool')
    } finally {
      rmSync(tmpDir, { recursive: true, force: true })
    }
  })

  it('dry_run_always_exits_0 — gap present + --dry-run → exit 0', () => {
    // Even with a coverage gap, --dry-run must exit 0
    const tmpDir = createSyntheticRepo({ manifestHasTool: false })
    try {
      const { exitCode, output } = runGate(tmpDir, '--dry-run')
      expect(
        exitCode,
        `Expected exit 0 in dry-run mode. Output:\n${output}`,
      ).toBe(0)
      // Should still print the ERROR finding (just not exit non-zero)
      expect(output).toContain('synthetic_tool')
    } finally {
      rmSync(tmpDir, { recursive: true, force: true })
    }
  })
})
