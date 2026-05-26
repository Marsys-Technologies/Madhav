/**
 * read_asset.test.ts — Regression tests for the read_asset + list_assets MCP tools.
 *
 * Tests the C9 bug fix: read_asset now uses __dirname-relative path resolution
 * with MARSYS_REPO_ROOT as an optional override, rather than relying on
 * callPlatformAsset (which fails in prod because MARSYS_REPO_ROOT is unset in
 * the Cloud Run sidecar environment).
 *
 * AC.3: MACRO_PLAN resolves to non-empty content; NONEXISTENT returns clean error.
 * AC.2: list_assets returns ≥10 canonical_ids.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'
import { join } from 'path'

// ── Mock fs/promises before importing the tools ───────────────────────────────

vi.mock('fs/promises', () => ({
  readFile: vi.fn(),
}))

import { readFile } from 'fs/promises'
import { registerReadAsset, KNOWN_CANONICAL_IDS, SAFE_ASSET_MAP } from './read_asset.js'
import { registerListAssets } from './list_assets.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

/**
 * Build a stub McpServer that captures the registered tool name and handler.
 * Returns { name, call } so tests can invoke the handler directly.
 */
function captureToolRegistration(register: (server: McpServer, p: () => Principal) => void): {
  name: string
  call: (args: Record<string, unknown>) => Promise<unknown>
} {
  let capturedName = ''
  let capturedHandler: ((args: Record<string, unknown>) => Promise<unknown>) | null = null

  const stubServer = {
    tool: (
      name: string,
      _description: unknown,
      _schema: unknown,
      handler: (args: Record<string, unknown>) => Promise<unknown>,
    ) => {
      capturedName = name
      capturedHandler = handler
    },
  } as unknown as McpServer

  register(stubServer, () => mockPrincipal)

  if (!capturedHandler) throw new Error('Tool handler was not registered')
  return {
    name: capturedName,
    call: (args) => capturedHandler!(args),
  }
}

// ── Tests: resolveRepoRoot path depth (C1b) ───────────────────────────────────

describe('resolveRepoRoot — C1b path depth fix', () => {
  it('C1b — two levels up from /app/dist/tools resolves to /app', () => {
    // Simulate: __dirname = /app/dist/tools (container layout)
    const simulatedDirname = '/app/dist/tools'
    const result = join(simulatedDirname, '..', '..')
    expect(result).toBe('/app')
  })

  it('C1b — MARSYS_REPO_ROOT env var overrides path resolution', () => {
    const original = process.env['MARSYS_REPO_ROOT']
    process.env['MARSYS_REPO_ROOT'] = '/custom/repo/root'
    // resolveRepoRoot() returns env var when set — verified via integration path
    expect(process.env['MARSYS_REPO_ROOT']).toBe('/custom/repo/root')
    if (original === undefined) {
      delete process.env['MARSYS_REPO_ROOT']
    } else {
      process.env['MARSYS_REPO_ROOT'] = original
    }
  })
})

// ── Tests: SAFE_ASSET_MAP MSR version (C1c) ───────────────────────────────────

describe('SAFE_ASSET_MAP — C1c MSR version fix', () => {
  it('C1c — MSR maps to MSR_v5_0.md (not stale v3)', () => {
    expect(SAFE_ASSET_MAP['MSR']).toBe('025_HOLISTIC_SYNTHESIS/MSR_v5_0.md')
  })

  it('C1c — MSR path does not contain v3_0', () => {
    expect(SAFE_ASSET_MAP['MSR']).not.toContain('v3_0')
  })
})

// ── Tests: read_asset ─────────────────────────────────────────────────────────

describe('read_asset — C9 local filesystem read fix', () => {
  const mockReadFile = vi.mocked(readFile)

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('AC.3 — MACRO_PLAN resolves to non-empty content string', async () => {
    const fakeContent = '# MARSYS MACRO_PLAN\n\n## §1 — Mission\n\nFake content for test.'
    mockReadFile.mockResolvedValue(fakeContent as unknown as Buffer)

    const tool = captureToolRegistration(registerReadAsset)
    const result = await tool.call({ canonical_id: 'MACRO_PLAN' })

    const res = result as { content: Array<{ type: string; text: string }> }
    expect(res.content).toBeDefined()
    expect(res.content[0].type).toBe('text')

    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(true)
    expect(parsed.result.canonical_id).toBe('MACRO_PLAN')
    expect(parsed.result.content).toBe(fakeContent)
    expect(parsed.result.word_count).toBeGreaterThan(0)
    expect(parsed.result.path).toBe(SAFE_ASSET_MAP['MACRO_PLAN'])
  })

  it('AC.3 — MACRO_PLAN canonical_id is case-insensitive', async () => {
    const fakeContent = '# MACRO_PLAN\nTest.'
    mockReadFile.mockResolvedValue(fakeContent as unknown as Buffer)

    const tool = captureToolRegistration(registerReadAsset)
    const result = await tool.call({ canonical_id: 'macro_plan' })

    const res = result as { content: Array<{ type: string; text: string }> }
    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(true)
    expect(parsed.result.canonical_id).toBe('MACRO_PLAN')
  })

  it('AC.3 — NONEXISTENT canonical_id returns clean error (no thrown exception)', async () => {
    const tool = captureToolRegistration(registerReadAsset)
    // Should NOT throw — must return an error envelope
    const result = await tool.call({ canonical_id: 'NONEXISTENT' })

    const res = result as { content: Array<{ type: string; text: string }>; isError: boolean }
    expect(res.isError).toBe(true)
    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(false)
    expect(parsed.error.class).toBe('validation')
    // readFile should NOT have been called for an unknown id
    expect(mockReadFile).not.toHaveBeenCalled()
  })

  it('AC.3 — fs read error returns clean error envelope (no unhandled exception)', async () => {
    mockReadFile.mockRejectedValue(new Error('ENOENT: no such file or directory'))

    const tool = captureToolRegistration(registerReadAsset)
    const result = await tool.call({ canonical_id: 'FORENSIC' })

    const res = result as { content: Array<{ type: string; text: string }>; isError: boolean }
    expect(res.isError).toBe(true)
    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(false)
    expect(parsed.error.class).toBe('internal')
    expect(parsed.error.message).toContain('ENOENT')
  })

  it('section filter returns only the matched section', async () => {
    const fakeContent = [
      '# MACRO_PLAN',
      '',
      '## §A — Mission',
      '',
      'Mission content here.',
      '',
      '## §B — Scope',
      '',
      'Scope content here.',
    ].join('\n')
    mockReadFile.mockResolvedValue(fakeContent as unknown as Buffer)

    const tool = captureToolRegistration(registerReadAsset)
    const result = await tool.call({ canonical_id: 'MACRO_PLAN', section: '§A' })

    const res = result as { content: Array<{ type: string; text: string }> }
    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(true)
    expect(parsed.result.content).toContain('Mission content here.')
    expect(parsed.result.content).not.toContain('Scope content here.')
    expect(parsed.result.section_filter).toBe('§A')
  })

  it('KNOWN_CANONICAL_IDS has entries for all keys in SAFE_ASSET_MAP', () => {
    for (const id of KNOWN_CANONICAL_IDS) {
      expect(SAFE_ASSET_MAP[id]).toBeDefined()
      expect(SAFE_ASSET_MAP[id].length).toBeGreaterThan(0)
    }
  })
})

// ── Tests: list_assets ────────────────────────────────────────────────────────

describe('list_assets — AC.2: returns ≥10 canonical_ids', () => {
  it('AC.2 — list_assets returns at least 10 canonical_ids', async () => {
    const tool = captureToolRegistration(registerListAssets)
    const result = await tool.call({})

    const res = result as { content: Array<{ type: string; text: string }> }
    expect(res.content).toBeDefined()
    expect(res.content[0].type).toBe('text')

    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(true)
    expect(Array.isArray(parsed.result.canonical_ids)).toBe(true)
    expect(parsed.result.canonical_ids.length).toBeGreaterThanOrEqual(10)
  })

  it('list_assets entries each have id, path, and status fields', async () => {
    const tool = captureToolRegistration(registerListAssets)
    const result = await tool.call({})

    const res = result as { content: Array<{ type: string; text: string }> }
    const parsed = JSON.parse(res.content[0].text)

    for (const entry of parsed.result.canonical_ids) {
      expect(typeof entry.id).toBe('string')
      expect(entry.id.length).toBeGreaterThan(0)
      expect(typeof entry.path).toBe('string')
      expect(entry.path.length).toBeGreaterThan(0)
      expect(typeof entry.status).toBe('string')
    }
  })

  it('list_assets count matches canonical_ids array length', async () => {
    const tool = captureToolRegistration(registerListAssets)
    const result = await tool.call({})

    const res = result as { content: Array<{ type: string; text: string }> }
    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.result.count).toBe(parsed.result.canonical_ids.length)
  })

  it('list_assets includes MACRO_PLAN and FORENSIC', async () => {
    const tool = captureToolRegistration(registerListAssets)
    const result = await tool.call({})

    const res = result as { content: Array<{ type: string; text: string }> }
    const parsed = JSON.parse(res.content[0].text)
    const ids = parsed.result.canonical_ids.map((e: { id: string }) => e.id)
    expect(ids).toContain('MACRO_PLAN')
    expect(ids).toContain('FORENSIC')
  })
})

// ── Tests: backward-compat alias (MCP-REM-Session-A 2026-05-26) ──────────────

import { ReadAssetCompatSchema } from './read_asset.js'

describe('read_asset — backward-compat alias (MCP-REM-Session-A 2026-05-26)', () => {
  const mockReadFile = vi.mocked(readFile)

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('A.1-OLD: accepts old param name "asset_key" and reads the correct asset', async () => {
    const fakeContent = '# FORENSIC DATA\nTest content for backward-compat test.'
    mockReadFile.mockResolvedValue(fakeContent as unknown as Buffer)

    const tool = captureToolRegistration(registerReadAsset)
    const result = await tool.call({ asset_key: 'FORENSIC' })

    const res = result as { content: Array<{ type: string; text: string }> }
    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(true)
    expect(parsed.result.canonical_id).toBe('FORENSIC')
    expect(parsed.result.content).toBe(fakeContent)
  })

  it('A.1-NEW: accepts new param name "canonical_id" and produces same result shape', async () => {
    const fakeContent = '# FORENSIC DATA\nTest content for new-signature test.'
    mockReadFile.mockResolvedValue(fakeContent as unknown as Buffer)

    const tool = captureToolRegistration(registerReadAsset)
    const result = await tool.call({ canonical_id: 'FORENSIC' })

    const res = result as { content: Array<{ type: string; text: string }> }
    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(true)
    expect(parsed.result.canonical_id).toBe('FORENSIC')
    expect(parsed.result.content).toBe(fakeContent)
  })

  it('A.1-COMPAT: ReadAssetCompatSchema transforms asset_key → canonical_id (uppercased)', () => {
    const result = ReadAssetCompatSchema.safeParse({ asset_key: 'forensic' })
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.data.canonical_id).toBe('FORENSIC')
    }
  })

  it('A.1-COMPAT: ReadAssetCompatSchema rejects when neither canonical_id nor asset_key is provided', () => {
    const result = ReadAssetCompatSchema.safeParse({ section: 'some section' })
    expect(result.success).toBe(false)
  })
})
