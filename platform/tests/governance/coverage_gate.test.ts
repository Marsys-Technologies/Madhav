/**
 * coverage_gate.test.ts
 *
 * COV-S7 gate verification: verifies that coverage_gate.py correctly fails on
 * synthetic bad inputs (tool missing from manifest; asset folder unbound) and
 * passes on clean synthetic inputs.
 *
 * Three scenarios tested per §E of COV-S7_BRIEF_v1_0.md:
 *   A — Manifest gap: tool in RETRIEVAL_TOOLS[] absent from manifest → exit 1 or 3
 *   B — Asset gap: asset folder with no tool binding → exit 2 or 3
 *   C — Clean baseline: both pass → exit 0
 *
 * Audit reference: §G.7 of CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT_v1_0.md
 */

import { describe, it, expect, afterEach } from 'vitest'
import { execFileSync, spawnSync } from 'node:child_process'
import { mkdtempSync, writeFileSync, mkdirSync, rmSync, existsSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { resolve, join } from 'node:path'

// Path to coverage_gate.py relative to this test file
// tests/governance/ → scripts/governance/
const COVERAGE_GATE_PY = resolve(
  __dirname,
  '../../scripts/governance/coverage_gate.py',
)

// Repo root (platform/ parent)
const REPO_ROOT = resolve(__dirname, '../../../')

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

interface RunResult {
  exitCode: number
  stdout: string
  stderr: string
}

function runGate(args: string[]): RunResult {
  const result = spawnSync('python3', [COVERAGE_GATE_PY, ...args], {
    encoding: 'utf-8',
    cwd: REPO_ROOT,
  })
  return {
    exitCode: result.status ?? 4,
    stdout: result.stdout ?? '',
    stderr: result.stderr ?? '',
  }
}

/**
 * Create a minimal synthetic retrieve/index.ts with a single RETRIEVAL_TOOLS entry.
 * The tool name is defined via a TOOL_NAME constant in a sibling file.
 */
function createSyntheticRetrieveIndex(dir: string, toolName: string): string {
  // Create the tool module file
  const toolFile = join(dir, 'synthetic_tool.ts')
  writeFileSync(
    toolFile,
    `const TOOL_NAME = '${toolName}'\nexport const tool = { name: TOOL_NAME }\n`,
  )
  // Create the index file that imports it
  const indexFile = join(dir, 'index.ts')
  writeFileSync(
    indexFile,
    `import * as syntheticTool from './synthetic_tool'\nexport const RETRIEVAL_TOOLS = [\n  syntheticTool.tool,\n]\n`,
  )
  return indexFile
}

/**
 * Create a minimal synthetic CAPABILITY_MANIFEST.json.
 * toolNames: list of tool names to declare in the manifest.
 * boundDirs: list of asset directory prefixes to bind a tool to (e.g. '01_FACTS_LAYER').
 */
function createSyntheticManifest(
  manifestPath: string,
  toolNames: string[],
  boundDirs: { dir: string; toolName: string }[],
): void {
  const entries: Record<string, unknown>[] = []

  // Add tool entries (no path prefix — they won't count as asset-bound)
  for (const tn of toolNames) {
    entries.push({
      canonical_id: `RETRIEVAL_TOOL_${tn}`,
      tool_name: tn,
      path: null,
      layer: 'L1',
      status: 'CURRENT',
      version: '1',
      interface_version: '1.0',
    })
  }

  // Add asset-bound entries
  for (const { dir, toolName } of boundDirs) {
    entries.push({
      canonical_id: `ASSET_${dir}`,
      tool_name: toolName,
      path: `${dir}/some_asset.md`,
      layer: 'L1',
      status: 'CURRENT',
      version: '1',
      interface_version: '1.0',
    })
  }

  const manifest = {
    generated_at: new Date().toISOString(),
    generator_version: '1.0',
    entry_count: entries.length,
    fingerprint: 'test-synthetic',
    entries,
  }
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2))
}

/**
 * Create a temporary asset directory (simulates a canonical layer folder).
 */
function createAssetDir(tmpRoot: string, dirName: string): string {
  const fullPath = join(tmpRoot, dirName)
  mkdirSync(fullPath, { recursive: true })
  return fullPath
}

// ---------------------------------------------------------------------------
// Temp dir management
// ---------------------------------------------------------------------------

const tempDirs: string[] = []

function makeTempDir(): string {
  const dir = mkdtempSync(join(tmpdir(), 'cov-s7-'))
  tempDirs.push(dir)
  return dir
}

afterEach(() => {
  for (const dir of tempDirs.splice(0)) {
    if (existsSync(dir)) {
      rmSync(dir, { recursive: true, force: true })
    }
  }
})

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('COV-S7 — coverage_gate.py', () => {
  /**
   * Scenario A: Tool in RETRIEVAL_TOOLS[] absent from manifest → exit 1 or 3
   */
  describe('synthetic_pr_coverage_gate_fails — Scenario A: manifest gap', () => {
    it('exits non-zero (1 or 3) when a tool has no manifest entry', () => {
      const tmp = makeTempDir()

      // Create retrieve dir with a tool NOT in the manifest
      const retrieveDir = join(tmp, 'retrieve')
      mkdirSync(retrieveDir)
      const indexPath = createSyntheticRetrieveIndex(retrieveDir, 'orphan_tool_not_in_manifest')

      // Create manifest with NO tool_name entries
      const manifestPath = join(tmp, 'manifest.json')
      createSyntheticManifest(manifestPath, [], [])

      // No asset dirs to scan (avoid asset-gate interference for this test)
      const result = runGate([
        '--retrieve-index', indexPath,
        '--manifest-path', manifestPath,
        '--asset-dirs',  // empty list means no asset dirs checked
      ])

      // Exit 1 = manifest only; exit 3 = both
      expect(result.exitCode).toBeGreaterThanOrEqual(1)
      expect([1, 3]).toContain(result.exitCode)

      // JSON output should name the missing tool
      const report = JSON.parse(result.stdout)
      expect(report.categories.COVERAGE_GATE_MANIFEST.status).toBe('FAIL')
      expect(report.categories.COVERAGE_GATE_MANIFEST.missing).toContain(
        'orphan_tool_not_in_manifest',
      )
    })
  })

  /**
   * Scenario B: Asset folder with no tool binding → exit 2 or 3
   */
  describe('synthetic_pr_coverage_gate_fails — Scenario B: asset gap', () => {
    it('exits non-zero (2 or 3) when an asset folder has no manifest binding', () => {
      const tmp = makeTempDir()

      // Create retrieve dir with a tool that IS in the manifest
      const retrieveDir = join(tmp, 'retrieve')
      mkdirSync(retrieveDir)
      const indexPath = createSyntheticRetrieveIndex(retrieveDir, 'bound_tool')

      // Create manifest with the tool present (manifest gate passes)
      const manifestPath = join(tmp, 'manifest.json')
      // No bound dirs — asset gate should fail
      createSyntheticManifest(manifestPath, ['bound_tool'], [])

      // Create a synthetic asset dir
      const assetDirName = 'SYNTH_ASSET_LAYER'
      createAssetDir(tmp, assetDirName)

      const result = runGate([
        '--repo-root', tmp,
        '--retrieve-index', indexPath,
        '--manifest-path', manifestPath,
        '--asset-dirs', assetDirName,
      ])

      // Exit 2 = asset only; exit 3 = both
      expect([2, 3]).toContain(result.exitCode)

      const report = JSON.parse(result.stdout)
      expect(report.categories.COVERAGE_GATE_ASSETS.status).toBe('FAIL')
      expect(report.categories.COVERAGE_GATE_ASSETS.unbound).toContain(assetDirName)
    })
  })

  /**
   * Scenario C: Clean baseline → exit 0
   */
  describe('clean_state_passes — Scenario C: both gates pass', () => {
    it('exits 0 when all tools are in manifest and all asset dirs are bound', () => {
      const tmp = makeTempDir()

      // Create retrieve dir with a tool that IS in the manifest
      const retrieveDir = join(tmp, 'retrieve')
      mkdirSync(retrieveDir)
      const indexPath = createSyntheticRetrieveIndex(retrieveDir, 'well_covered_tool')

      // Create manifest with the tool present AND a binding for the asset dir
      const assetDirName = 'SYNTH_CLEAN_LAYER'
      const manifestPath = join(tmp, 'manifest.json')
      createSyntheticManifest(
        manifestPath,
        ['well_covered_tool'],
        [{ dir: assetDirName, toolName: 'well_covered_tool' }],
      )

      // Create the asset dir
      createAssetDir(tmp, assetDirName)

      const result = runGate([
        '--repo-root', tmp,
        '--retrieve-index', indexPath,
        '--manifest-path', manifestPath,
        '--asset-dirs', assetDirName,
      ])

      expect(result.exitCode).toBe(0)

      const report = JSON.parse(result.stdout)
      expect(report.verdict).toBe('PASS')
      expect(report.categories.COVERAGE_GATE_MANIFEST.status).toBe('PASS')
      expect(report.categories.COVERAGE_GATE_MANIFEST.missing).toHaveLength(0)
      expect(report.categories.COVERAGE_GATE_ASSETS.status).toBe('PASS')
      expect(report.categories.COVERAGE_GATE_ASSETS.unbound).toHaveLength(0)
    })
  })

  /**
   * Structural: JSON report always contains both required categories
   */
  it('JSON report always contains COVERAGE_GATE_MANIFEST and COVERAGE_GATE_ASSETS keys', () => {
    const tmp = makeTempDir()
    const retrieveDir = join(tmp, 'retrieve')
    mkdirSync(retrieveDir)
    const indexPath = createSyntheticRetrieveIndex(retrieveDir, 'any_tool')
    const manifestPath = join(tmp, 'manifest.json')
    createSyntheticManifest(manifestPath, ['any_tool'], [])

    const result = runGate([
      '--retrieve-index', indexPath,
      '--manifest-path', manifestPath,
      '--asset-dirs',
    ])

    const report = JSON.parse(result.stdout)
    expect(report).toHaveProperty('verdict')
    expect(report).toHaveProperty('categories.COVERAGE_GATE_MANIFEST')
    expect(report).toHaveProperty('categories.COVERAGE_GATE_ASSETS')
    expect(report).toHaveProperty('run_at')
    expect(report.categories.COVERAGE_GATE_MANIFEST).toHaveProperty('status')
    expect(report.categories.COVERAGE_GATE_MANIFEST).toHaveProperty('missing')
    expect(report.categories.COVERAGE_GATE_ASSETS).toHaveProperty('status')
    expect(report.categories.COVERAGE_GATE_ASSETS).toHaveProperty('unbound')
  })
})
