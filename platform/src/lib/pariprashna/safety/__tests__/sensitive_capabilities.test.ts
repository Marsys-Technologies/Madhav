/**
 * Lane G1-A — the sensitive capability class.
 *
 * Two claims, both of which would otherwise rest on "it happens to be true
 * today":
 *   1. the `consult` MCP profile carries no sensitive-class tool — asserted
 *      against the SHIPPED generated artifact, not against the builder;
 *   2. the platform ↔ platform-mcp mirror of the list has not drifted —
 *      asserted by READING the other package's file, so the mirror is a
 *      detector rather than a promise (§N.8).
 */

import { readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, it, expect } from 'vitest'

import {
  applyCapabilityExclusion,
  capabilitiesExcludedFor,
  isSensitiveClassCapability,
  MEDICAL_CLASS_CAPABILITIES,
  MORTALITY_CLASS_CAPABILITIES,
  SENSITIVE_CLASS_CAPABILITIES,
} from '../sensitive_capabilities'

const REPO = path.resolve(__dirname, '../../../../../..')

describe('the consult MCP profile carries no sensitive-class tool', () => {
  it('asserted against the SHIPPED generated profile artifact', () => {
    // Deliberately reads the checked-in generated file rather than re-running
    // the builder: the builder proves what a REGENERATION would produce; this
    // proves what is actually being served today.
    const generated = readFileSync(
      path.join(REPO, 'platform-mcp/src/generated/mcp_surface_profiles.generated.ts'),
      'utf8',
    )
    const consultBlock = generated.slice(generated.indexOf('"consult": {'))
    const namesMatch = consultBlock.match(/"tool_names": \[([\s\S]*?)\]/)
    expect(namesMatch, 'could not locate the consult profile tool_names').not.toBeNull()
    const consultNames = (namesMatch![1].match(/"[a-z0-9_]+"/g) ?? []).map((s) => s.replace(/"/g, ''))
    expect(consultNames.length).toBeGreaterThan(0)
    for (const sensitive of SENSITIVE_CLASS_CAPABILITIES) {
      expect(
        consultNames,
        `${sensitive} is sensitive-class and must not be in the consult profile (architecture §2, abuse case A6)`,
      ).not.toContain(sensitive)
    }
  })
})

describe('the platform-mcp mirror has not drifted', () => {
  it('both packages declare the identical sensitive class', () => {
    const mirror = readFileSync(
      path.join(REPO, 'platform-mcp/src/lib/sensitive_capability_class.ts'),
      'utf8',
    )
    const extract = (constName: string): string[] => {
      const m = mirror.match(new RegExp(`${constName}[^=]*=\\s*\\[([\\s\\S]*?)\\]`))
      expect(m, `${constName} not found in the platform-mcp mirror`).not.toBeNull()
      return (m![1].match(/'[a-z0-9_]+'/g) ?? []).map((s) => s.replace(/'/g, ''))
    }
    expect(extract('MORTALITY_CLASS_CAPABILITIES')).toEqual([...MORTALITY_CLASS_CAPABILITIES])
    expect(extract('MEDICAL_CLASS_CAPABILITIES')).toEqual([...MEDICAL_CLASS_CAPABILITIES])
  })
})

describe('HS-1/HS-4 plan-time capability exclusion', () => {
  it('excludes the mortality capabilities when a mortality class fired', () => {
    expect(capabilitiesExcludedFor(['hs1_date_of_death'])).toEqual([...MORTALITY_CLASS_CAPABILITIES])
    expect(capabilitiesExcludedFor(['hs4_mortality_window'])).toEqual([...MORTALITY_CLASS_CAPABILITIES])
  })

  it('a HEALTH question does NOT lose its health tools — HS-3 is a review path, not a filter', () => {
    // The distinction matters: HS-3 permits the reading and gates its RELEASE.
    // Stripping the health capabilities as well would produce an ungrounded
    // reading and then seal it, which is worse than either control alone.
    expect(capabilitiesExcludedFor(['hs3_health_crisis'])).toEqual([])
    expect(capabilitiesExcludedFor(['hs3_mental_health'])).toEqual([])
  })

  it('a benign turn excludes nothing', () => {
    expect(capabilitiesExcludedFor([])).toEqual([])
  })

  it('applyCapabilityExclusion partitions and reports both halves', () => {
    const { kept, stripped } = applyCapabilityExclusion(
      ['ganita_positions_get', 'get_ayurdaya', 'bodha_signals_get'],
      capabilitiesExcludedFor(['hs1_date_of_death']),
    )
    expect(stripped).toEqual(['get_ayurdaya'])
    expect(kept).toEqual(['ganita_positions_get', 'bodha_signals_get'])
  })
})

describe('what is deliberately NOT in the class', () => {
  it('get_sensitive_degrees is astrologically sensitive, not disclosure-sensitive', () => {
    // Recorded as a test so the reasoning survives: gaṇḍānta / mṛtyu-bhāga
    // degrees are ordinary chart work. Their mortality-adjacent reading is
    // covered by the classifier and the pre-wire scan, not by removing the
    // degree table from every reading that touches it.
    expect(isSensitiveClassCapability('get_sensitive_degrees')).toBe(false)
    expect(isSensitiveClassCapability('get_sensitive_points')).toBe(false)
  })
})
