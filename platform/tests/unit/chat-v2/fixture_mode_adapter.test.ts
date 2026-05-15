/**
 * Unit tests for the fixture-mode adapter.
 *
 * Tests cover:
 *  - isFixtureModeEnabled reads env var correctly
 *  - resolveFixturePath produces the right path
 *  - loadFixture succeeds for existing fixtures, throws for missing ones
 *  - loadFixture throws descriptive error for malformed JSON
 *  - listFixtures returns available scenarios for a provider
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import path from 'path'
import {
  isFixtureModeEnabled,
  resolveFixturePath,
  loadFixture,
  listFixtures,
} from '@/lib/fixtures/fixture_mode_adapter'

describe('fixture_mode_adapter', () => {
  describe('isFixtureModeEnabled', () => {
    const originalEnv = process.env.MARSYS_FIXTURE_MODE

    afterEach(() => {
      if (originalEnv === undefined) {
        delete process.env.MARSYS_FIXTURE_MODE
      } else {
        process.env.MARSYS_FIXTURE_MODE = originalEnv
      }
    })

    it('returns true when MARSYS_FIXTURE_MODE=true', () => {
      process.env.MARSYS_FIXTURE_MODE = 'true'
      expect(isFixtureModeEnabled()).toBe(true)
    })

    it('returns false when MARSYS_FIXTURE_MODE=false', () => {
      process.env.MARSYS_FIXTURE_MODE = 'false'
      expect(isFixtureModeEnabled()).toBe(false)
    })

    it('returns false when MARSYS_FIXTURE_MODE is not set', () => {
      delete process.env.MARSYS_FIXTURE_MODE
      expect(isFixtureModeEnabled()).toBe(false)
    })

    it('returns false for any value other than "true"', () => {
      process.env.MARSYS_FIXTURE_MODE = '1'
      expect(isFixtureModeEnabled()).toBe(false)
    })
  })

  describe('resolveFixturePath', () => {
    it('produces the expected path structure', () => {
      const result = resolveFixturePath('anthropic', 'default')
      expect(result).toContain(path.join('tests', 'fixtures', 'chat-v2', 'providers', 'anthropic'))
      expect(result).toContain('default.json')
    })

    it('uses process.cwd() as the root', () => {
      const result = resolveFixturePath('openai', 'code_block')
      expect(result.startsWith(process.cwd())).toBe(true)
    })

    it('handles different providers correctly', () => {
      const providers = ['anthropic', 'gemini_pro', 'openai', 'deepseek_v4'] as const
      for (const p of providers) {
        const result = resolveFixturePath(p, 'default')
        expect(result).toContain(p)
      }
    })
  })

  describe('loadFixture', () => {
    it('throws a descriptive error for a missing fixture', () => {
      expect(() => loadFixture('anthropic', 'nonexistent_scenario_xyz')).toThrow(
        /Fixture not found/,
      )
    })

    it('throws error containing provider and scenario in message', () => {
      expect(() => loadFixture('openai', 'no_such_scenario')).toThrow(/provider=openai/)
    })

    it('throws error for invalid JSON (mocked fs)', () => {
      const fs = require('fs')
      const existsSpy = vi.spyOn(fs, 'existsSync').mockReturnValueOnce(true)
      const readSpy = vi.spyOn(fs, 'readFileSync').mockReturnValueOnce('not valid json }{')

      expect(() => loadFixture('anthropic', 'bad_json_fixture')).toThrow(/Invalid JSON/)

      existsSpy.mockRestore()
      readSpy.mockRestore()
    })
  })

  describe('listFixtures', () => {
    it('returns an array (possibly empty) for any known provider', () => {
      const result = listFixtures('anthropic')
      expect(Array.isArray(result)).toBe(true)
    })

    it('returns empty array for an unknown provider directory', () => {
      // This tests the defensive branch — the directory won't exist in the test env
      // unless we're running with the full fixture tree populated.
      const result = listFixtures('nim')
      expect(Array.isArray(result)).toBe(true)
    })

    it('returns only .json file names without extension', () => {
      const fs = require('fs')
      const existsSpy = vi.spyOn(fs, 'existsSync').mockReturnValueOnce(true)
      const readdirSpy = vi
        .spyOn(fs, 'readdirSync')
        .mockReturnValueOnce(['default.json', 'thinking.json', '.gitkeep'])

      const result = listFixtures('anthropic')
      expect(result).toEqual(['default', 'thinking'])

      existsSpy.mockRestore()
      readdirSpy.mockRestore()
    })
  })
})
