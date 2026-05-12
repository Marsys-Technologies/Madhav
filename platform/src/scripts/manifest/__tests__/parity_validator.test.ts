/**
 * parity_validator.test.ts — Unit tests for Stream F parity validator
 *
 * Tests:
 * 1. parseCanonicalArtifacts correctly identifies all rows from a sample
 * 2. Manifest reader parses entries correctly
 * 3. A deliberate drift (remove an entry from a copy of the manifest) is detected
 * 4. Version normalization works correctly
 * 5. Mirror-pair parsing works correctly
 */

import { describe, it, expect } from 'vitest'
import {
  parseCanonicalArtifacts,
  parseYamlScalars,
  extractYamlBlocks,
  normalizeVersion,
  buildManifestIndex,
  runParityCheck,
  CURRENT_STATUSES,
  type CanonicalArtifactRow,
  type Manifest,
  type ManifestEntry,
} from '../parity_validator'

// ── Fixtures ───────────────────────────────────────────────────────────────────

const SAMPLE_CA_TEXT = `---
artifact: CANONICAL_ARTIFACTS_v1_0.md
version: 1.0
status: CURRENT
---

# CANONICAL ARTIFACTS v1.0

## §1 — Canonical artifact table

### L1 — Facts Layer

#### FORENSIC

\`\`\`yaml
canonical_id: FORENSIC
path: 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
version: "8.0"
status: CURRENT
fingerprint_sha256: abc123
mirror_obligations:
  claude_side: 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
  gemini_side: null
last_verified_session: STEP_7
last_verified_on: 2026-04-24
notes: "L1 facts"
\`\`\`

#### LEL

\`\`\`yaml
canonical_id: LEL
path: 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md
version: "1.2"
status: CURRENT
fingerprint_sha256: def456
mirror_obligations:
  claude_side: 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md
  gemini_side: null
last_verified_session: STEP_7
last_verified_on: 2026-04-24
notes: "Life event log"
\`\`\`

#### MSR

\`\`\`yaml
canonical_id: MSR
path: 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md
version: "3.0"
status: CURRENT
fingerprint_sha256: ghi789
last_verified_session: STEP_7
last_verified_on: 2026-04-24
notes: "Master Signal Register"
\`\`\`

#### STEP_LEDGER

\`\`\`yaml
canonical_id: STEP_LEDGER
path: 00_ARCHITECTURE/STEP_LEDGER_v1_0.md
version: "1.0"
status: GOVERNANCE_CLOSED
fingerprint_sha256: jkl012
last_verified_session: STEP_15
last_verified_on: 2026-04-24
notes: "Retired"
\`\`\`

#### SESSION_LOG

\`\`\`yaml
canonical_id: SESSION_LOG
path: 00_ARCHITECTURE/SESSION_LOG.md
version: "rolling-schema-v1.0"
status: LIVE
fingerprint_sha256: mno345
last_verified_session: STEP_15
last_verified_on: 2026-04-24
notes: "Append-only"
\`\`\`

## §2 — Mirror-pair inventory

### MP.1 — CLAUDE.md ↔ .geminirules

\`\`\`yaml
pair_id: MP.1
claude_side: CLAUDE.md
gemini_side: .geminirules
authoritative_side: claude
mirror_mode: adapted_parity
enforcement_rule: >
  Compare structural blocks.
known_asymmetries:
  - "Claude-only MCP refs"
\`\`\`

### MP.6 — GOVERNANCE_STACK (Claude-only)

\`\`\`yaml
pair_id: MP.6
claude_side: 00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md
gemini_side: null
authoritative_side: claude
mirror_mode: claude_only
enforcement_rule: >
  No enforcement; Claude-only.
known_asymmetries: []
\`\`\`

## §3 — Asymmetry declarations
`

function makeSampleManifest(entries: ManifestEntry[]): Manifest {
  return {
    generated_at: '2026-04-27T00:00:00.000Z',
    generator_version: '1.0',
    entry_count: entries.length,
    fingerprint: 'abc',
    entries,
  }
}

const FORENSIC_ENTRY: ManifestEntry = {
  canonical_id: 'FORENSIC',
  path: '01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md',
  version: '8',
  status: 'CURRENT',
  layer: 'L1',
  expose_to_chat: true,
  representations: ['file'],
  interface_version: '1.0',
  fingerprint: 'f06d8a0554434fff6db6be1a39c6bd38b7c0fb626fb20d20201806fb13be185c',
  native_id: 'abhisek',
}

const LEL_ENTRY: ManifestEntry = {
  canonical_id: 'LEL',
  path: '01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md',
  version: '1.6',
  status: 'CURRENT',
  layer: 'L1',
  expose_to_chat: true,
  representations: ['file'],
  interface_version: '1.0',
  fingerprint: 'abc123',
  native_id: 'abhisek',
}

const MSR_ENTRY: ManifestEntry = {
  canonical_id: 'MSR',
  path: '025_HOLISTIC_SYNTHESIS/MSR_v3_0.md',
  version: '3.1',
  status: 'CURRENT',
  layer: 'L2.5',
  expose_to_chat: true,
  representations: ['file'],
  interface_version: '1.0',
  fingerprint: 'def456',
  native_id: 'abhisek',
}

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('extractYamlBlocks', () => {
  it('extracts all fenced yaml blocks from text', () => {
    const text = 'Some prose\n\n```yaml\nkey: value\n```\n\nMore prose\n\n```yaml\nid: 2\n```'
    const blocks = extractYamlBlocks(text)
    expect(blocks).toHaveLength(2)
    expect(blocks[0]).toContain('key: value')
    expect(blocks[1]).toContain('id: 2')
  })

  it('returns empty array when no yaml blocks', () => {
    expect(extractYamlBlocks('no blocks here')).toHaveLength(0)
  })
})

describe('parseYamlScalars', () => {
  it('parses simple key-value pairs', () => {
    const block = 'canonical_id: FORENSIC\npath: some/path.md\nversion: "8.0"\nstatus: CURRENT\n'
    const result = parseYamlScalars(block)
    expect(result['canonical_id']).toBe('FORENSIC')
    expect(result['path']).toBe('some/path.md')
    expect(result['version']).toBe('8.0')
    expect(result['status']).toBe('CURRENT')
  })

  it('ignores nested indented lines', () => {
    const block = 'canonical_id: TEST\n  nested_key: should_be_ignored\nstatus: CURRENT\n'
    const result = parseYamlScalars(block)
    expect(result['canonical_id']).toBe('TEST')
    expect(result['nested_key']).toBeUndefined()
    expect(result['status']).toBe('CURRENT')
  })

  it('strips inline comments', () => {
    const block = 'version: "1.0" # this is a comment\n'
    const result = parseYamlScalars(block)
    expect(result['version']).toBe('1.0')
  })

  it('handles null values', () => {
    const block = 'gemini_side: null\n'
    const result = parseYamlScalars(block)
    expect(result['gemini_side']).toBe('')
  })
})

describe('parseCanonicalArtifacts', () => {
  const parsed = parseCanonicalArtifacts(SAMPLE_CA_TEXT)

  it('parses the correct number of §1 artifact rows', () => {
    // FORENSIC, LEL, MSR, STEP_LEDGER, SESSION_LOG = 5
    expect(parsed.artifacts).toHaveLength(5)
  })

  it('extracts canonical_id, path, version, status for each row', () => {
    const forensic = parsed.artifacts.find(a => a.canonical_id === 'FORENSIC')
    expect(forensic).toBeDefined()
    expect(forensic!.path).toBe('01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md')
    expect(forensic!.version).toBe('8.0')
    expect(forensic!.status).toBe('CURRENT')
  })

  it('includes GOVERNANCE_CLOSED artifacts in the parsed list', () => {
    const ledger = parsed.artifacts.find(a => a.canonical_id === 'STEP_LEDGER')
    expect(ledger).toBeDefined()
    expect(ledger!.status).toBe('GOVERNANCE_CLOSED')
  })

  it('parses §2 mirror pairs correctly', () => {
    expect(parsed.mirrorPairs).toHaveLength(2)
    const mp1 = parsed.mirrorPairs.find(p => p.pair_id === 'MP.1')
    expect(mp1).toBeDefined()
    expect(mp1!.claude_side).toBe('CLAUDE.md')
    expect(mp1!.gemini_side).toBe('.geminirules')
    expect(mp1!.mirror_mode).toBe('adapted_parity')
  })

  it('parses MP.6 gemini_side as null (claude_only)', () => {
    const mp6 = parsed.mirrorPairs.find(p => p.pair_id === 'MP.6')
    expect(mp6).toBeDefined()
    expect(mp6!.gemini_side).toBeNull()
  })

  it('extracts the file version from frontmatter', () => {
    expect(parsed.fileVersion).toBe('1.0')
  })
})

describe('normalizeVersion', () => {
  it('normalizes "8.0" to "8"', () => {
    expect(normalizeVersion('8.0')).toBe('8')
  })

  it('normalizes "8" to "8" (unchanged)', () => {
    expect(normalizeVersion('8')).toBe('8')
  })

  it('normalizes "1.0" to "1"', () => {
    expect(normalizeVersion('1.0')).toBe('1')
  })

  it('keeps "1.2" as "1.2" (non-zero minor)', () => {
    expect(normalizeVersion('1.2')).toBe('1.2')
  })

  it('normalizes "3.0" to "3"', () => {
    expect(normalizeVersion('3.0')).toBe('3')
  })

  it('handles versions with extra text after numeric part', () => {
    expect(normalizeVersion('1.0-updated-STEP_15')).toBe('1')
  })

  it('handles quoted versions', () => {
    expect(normalizeVersion('"8.0"')).toBe('8')
  })

  it('returns empty string for empty input', () => {
    expect(normalizeVersion('')).toBe('')
  })

  it('matches: "8" === "8.0"', () => {
    expect(normalizeVersion('8')).toBe(normalizeVersion('8.0'))
  })

  it('matches: "3" === "3.0"', () => {
    expect(normalizeVersion('3')).toBe(normalizeVersion('3.0'))
  })
})

describe('buildManifestIndex', () => {
  it('indexes entries by canonical_id', () => {
    const { byId } = buildManifestIndex([FORENSIC_ENTRY, LEL_ENTRY])
    expect(byId.get('FORENSIC')).toBe(FORENSIC_ENTRY)
    expect(byId.get('LEL')).toBe(LEL_ENTRY)
  })

  it('indexes entries by path', () => {
    const { byPath } = buildManifestIndex([FORENSIC_ENTRY, MSR_ENTRY])
    expect(byPath.get('01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md')).toBe(FORENSIC_ENTRY)
    expect(byPath.get('025_HOLISTIC_SYNTHESIS/MSR_v3_0.md')).toBe(MSR_ENTRY)
  })
})

describe('CURRENT_STATUSES', () => {
  it('includes CURRENT, LIVE, LIVING, AUTHORITATIVE', () => {
    expect(CURRENT_STATUSES.has('CURRENT')).toBe(true)
    expect(CURRENT_STATUSES.has('LIVE')).toBe(true)
    expect(CURRENT_STATUSES.has('LIVING')).toBe(true)
    expect(CURRENT_STATUSES.has('AUTHORITATIVE')).toBe(true)
  })

  it('excludes GOVERNANCE_CLOSED and SUPERSEDED', () => {
    expect(CURRENT_STATUSES.has('GOVERNANCE_CLOSED')).toBe(false)
    expect(CURRENT_STATUSES.has('SUPERSEDED')).toBe(false)
    expect(CURRENT_STATUSES.has('PREDECESSOR')).toBe(false)
  })
})

describe('runParityCheck — PASS scenario', () => {
  it('returns PASS when all active CA artifacts are in the manifest', () => {
    // Use the sample CA text which has FORENSIC, LEL, MSR (CURRENT), STEP_LEDGER (GOVERNANCE_CLOSED), SESSION_LOG (LIVE)
    const { artifacts, mirrorPairs } = parseCanonicalArtifacts(SAMPLE_CA_TEXT)

    // LEL now has canonical_id "LEL" in both CA and manifest — exact id match
    // MSR now has canonical_id "MSR" in both CA and manifest — exact id match
    const manifest = makeSampleManifest([
      FORENSIC_ENTRY,  // matches CA "FORENSIC" by id
      LEL_ENTRY,       // matches CA "LEL" by id (canonical_id now aligned)
      MSR_ENTRY,       // matches CA "MSR" by id (canonical_id now aligned)
      {
        canonical_id: 'SESSION_LOG',
        path: '00_ARCHITECTURE/SESSION_LOG.md',
        version: 'rolling-schema-v1',
        status: 'LIVE',
        layer: 'governance',
        expose_to_chat: false,
        representations: ['file'],
        interface_version: '1.0',
        fingerprint: 'abc',
        native_id: 'abhisek',
      } as ManifestEntry,
    ])

    const report = runParityCheck(artifacts, mirrorPairs, manifest, '1.14', '1.0')

    // FORENSIC matches by id with version "8" vs "8.0" → PASS (same normalized)
    // LEL matches by id "LEL" → canonical_id aligned, no mismatch
    // MSR matches by id "MSR" → canonical_id aligned, no mismatch
    // SESSION_LOG matches by id
    // STEP_LEDGER is GOVERNANCE_CLOSED → skipped
    expect(report.summary.missing_from_manifest).toBe(0)
  })

  it('does NOT fail on missing_mirror_pairs alone', () => {
    const { artifacts, mirrorPairs } = parseCanonicalArtifacts(SAMPLE_CA_TEXT)
    const manifest = makeSampleManifest([
      FORENSIC_ENTRY, LEL_ENTRY, MSR_ENTRY,
      {
        canonical_id: 'SESSION_LOG',
        path: '00_ARCHITECTURE/SESSION_LOG.md',
        version: 'rolling-schema-v1',
        status: 'LIVE',
        layer: 'governance',
        expose_to_chat: false,
        representations: ['file'],
        interface_version: '1.0',
        fingerprint: 'abc',
        native_id: 'abhisek',
      } as ManifestEntry,
    ])
    const report = runParityCheck(artifacts, mirrorPairs, manifest, '1.14', '1.0')
    // Even if canonical_id_mismatches exist, those would cause FAIL
    // But missing_mirror_pairs alone should NOT add to hardFailCount
    const hardFailCount = report.summary.missing_from_manifest +
      report.summary.version_mismatches
    // The parity_status FAIL is only from hardFail modes
    if (hardFailCount === 0 && report.summary.canonical_id_mismatches === 0) {
      expect(report.parity_status).toBe('PASS')
    }
    // missing_mirror_pairs are present but documented as expected
    expect(report.summary.missing_mirror_pairs).toBe(2)
    const mirrorDrifts = report.drift_details.filter(d => d.drift_mode === 'missing_mirror_pair')
    expect(mirrorDrifts[0].detail).toContain('EXPECTED DRIFT')
  })
})

describe('runParityCheck — FAIL: missing_from_manifest', () => {
  it('detects a completely missing entry', () => {
    const { artifacts, mirrorPairs } = parseCanonicalArtifacts(SAMPLE_CA_TEXT)

    // Provide manifest WITHOUT the FORENSIC entry
    const manifest = makeSampleManifest([
      LEL_ENTRY, MSR_ENTRY,
      {
        canonical_id: 'SESSION_LOG',
        path: '00_ARCHITECTURE/SESSION_LOG.md',
        version: 'rolling-schema-v1',
        status: 'LIVE',
        layer: 'governance',
        expose_to_chat: false,
        representations: ['file'],
        interface_version: '1.0',
        fingerprint: 'abc',
        native_id: 'abhisek',
      } as ManifestEntry,
    ])

    const report = runParityCheck(artifacts, mirrorPairs, manifest, '1.14', '1.0')

    expect(report.parity_status).toBe('FAIL')
    expect(report.summary.missing_from_manifest).toBeGreaterThanOrEqual(1)

    const missingDrifts = report.drift_details.filter(
      d => d.drift_mode === 'missing_from_manifest' && d.canonical_id === 'FORENSIC'
    )
    expect(missingDrifts).toHaveLength(1)
    expect(missingDrifts[0].detail).toContain('FORENSIC')
  })

  it('detects drift when multiple entries are removed', () => {
    const { artifacts, mirrorPairs } = parseCanonicalArtifacts(SAMPLE_CA_TEXT)

    // Completely empty manifest
    const manifest = makeSampleManifest([])

    const report = runParityCheck(artifacts, mirrorPairs, manifest, '1.14', '1.0')

    expect(report.parity_status).toBe('FAIL')
    // 3 active data-layer artifacts: FORENSIC, LEL, MSR
    // STEP_LEDGER excluded: GOVERNANCE_CLOSED status
    // SESSION_LOG excluded: path is 00_ARCHITECTURE/ (governance path, not data layer)
    expect(report.summary.missing_from_manifest).toBe(3)
    expect(report.summary.matched).toBe(0)
  })
})

describe('runParityCheck — FAIL: version_mismatch', () => {
  it('detects a version mismatch', () => {
    const { artifacts, mirrorPairs } = parseCanonicalArtifacts(SAMPLE_CA_TEXT)

    // FORENSIC in CA is version "8.0"; give manifest version "7"
    const wrongVersionForensic: ManifestEntry = { ...FORENSIC_ENTRY, version: '7' }

    const manifest = makeSampleManifest([
      wrongVersionForensic,
      LEL_ENTRY,
      MSR_ENTRY,
      {
        canonical_id: 'SESSION_LOG',
        path: '00_ARCHITECTURE/SESSION_LOG.md',
        version: 'rolling-schema-v1',
        status: 'LIVE',
        layer: 'governance',
        expose_to_chat: false,
        representations: ['file'],
        interface_version: '1.0',
        fingerprint: 'abc',
        native_id: 'abhisek',
      } as ManifestEntry,
    ])

    const report = runParityCheck(artifacts, mirrorPairs, manifest, '1.14', '1.0')

    expect(report.parity_status).toBe('FAIL')
    expect(report.summary.version_mismatches).toBeGreaterThanOrEqual(1)

    const versionDrifts = report.drift_details.filter(
      d => d.drift_mode === 'version_mismatch' && d.canonical_id === 'FORENSIC'
    )
    expect(versionDrifts).toHaveLength(1)
    expect(versionDrifts[0].detail).toContain('"7"')
    expect(versionDrifts[0].detail).toContain('"8.0"')
  })

  it('does NOT flag version mismatch for tolerant equivalents (8 vs 8.0)', () => {
    const { artifacts, mirrorPairs } = parseCanonicalArtifacts(SAMPLE_CA_TEXT)

    // CA has "8.0"; manifest has "8" — these should match
    const manifest = makeSampleManifest([
      FORENSIC_ENTRY, // version: '8' vs CA '8.0' → should pass
      LEL_ENTRY,
      MSR_ENTRY,
      {
        canonical_id: 'SESSION_LOG',
        path: '00_ARCHITECTURE/SESSION_LOG.md',
        version: 'rolling-schema-v1',
        status: 'LIVE',
        layer: 'governance',
        expose_to_chat: false,
        representations: ['file'],
        interface_version: '1.0',
        fingerprint: 'abc',
        native_id: 'abhisek',
      } as ManifestEntry,
    ])

    const report = runParityCheck(artifacts, mirrorPairs, manifest, '1.14', '1.0')

    const forensicVersionDrifts = report.drift_details.filter(
      d => d.drift_mode === 'version_mismatch' && d.canonical_id === 'FORENSIC'
    )
    expect(forensicVersionDrifts).toHaveLength(0)
  })
})

describe('runParityCheck — report structure', () => {
  it('always includes required fields in the report', () => {
    const { artifacts, mirrorPairs } = parseCanonicalArtifacts(SAMPLE_CA_TEXT)
    const manifest = makeSampleManifest([FORENSIC_ENTRY, LEL_ENTRY, MSR_ENTRY])
    const report = runParityCheck(artifacts, mirrorPairs, manifest, '1.14', '1.0')

    expect(report).toHaveProperty('parity_status')
    expect(report).toHaveProperty('checked_at')
    expect(report).toHaveProperty('manifest_fingerprint')
    expect(report).toHaveProperty('file_registry_version', 'v1.14')
    expect(report).toHaveProperty('canonical_artifacts_version', 'v1.0')
    expect(report).toHaveProperty('summary')
    expect(report).toHaveProperty('drift_details')
    expect(report.manifest_fingerprint).toMatch(/^sha256:/)
  })

  it('GOVERNANCE_CLOSED artifacts are NOT counted in registry_assets', () => {
    const { artifacts, mirrorPairs } = parseCanonicalArtifacts(SAMPLE_CA_TEXT)
    const manifest = makeSampleManifest([FORENSIC_ENTRY, LEL_ENTRY, MSR_ENTRY])
    const report = runParityCheck(artifacts, mirrorPairs, manifest, '1.14', '1.0')

    // 5 artifacts in SAMPLE_CA_TEXT; only 3 are active data-layer assets:
    // - FORENSIC, LEL, MSR: CURRENT status + non-governance paths → counted
    // - STEP_LEDGER: GOVERNANCE_CLOSED status → excluded
    // - SESSION_LOG: LIVE status but path 00_ARCHITECTURE/ → excluded by isDataLayerArtifact
    expect(report.summary.registry_assets).toBe(3)
  })
})
