/**
 * icr_gate.test.ts — ICR-S6
 *
 * Vitest unit tests for platform/scripts/governance/icr_gate.ts.
 *
 * Verifies:
 *   (a) parseResolvedId() correctly extracts conflict_id from filenames
 *   (b) loadResolvedIds() reads RESOLVED/ directory correctly
 *   (c) filterUnresolved(): conflict in resolved set → excluded (gate exits 0 path)
 *   (d) filterUnresolved(): conflict NOT in resolved set → included (gate exits 1 path)
 *   (e) filterUnresolved(): empty conflict list → empty result (gate exits 0 path)
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import {
  parseResolvedId,
  loadResolvedIds,
  filterUnresolved,
} from '../../scripts/governance/icr_gate';
import type { ConflictRecord } from '../../src/lib/icr/types';

// ─────────────────────────────────────────────────────────────────────────────
// Fixtures
// ─────────────────────────────────────────────────────────────────────────────

function makeConflict(id: string): ConflictRecord {
  return {
    conflict_id: id,
    conflict_class: 'A',
    signal_ids_affected: ['MSR.001'],
    description: `Test conflict for ${id}`,
    detected_at: new Date().toISOString(),
    evidence: 'test evidence',
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// parseResolvedId
// ─────────────────────────────────────────────────────────────────────────────

describe('parseResolvedId', () => {
  it('parses DIS.013_MSR_377_resolved.yaml → DIS.013', () => {
    expect(parseResolvedId('DIS.013_MSR_377_resolved.yaml')).toBe('DIS.013');
  });

  it('parses DIS.AUTO.42_MSR_42_resolved.yaml → DIS.AUTO.42', () => {
    expect(parseResolvedId('DIS.AUTO.42_MSR_42_resolved.yaml')).toBe('DIS.AUTO.42');
  });

  it('parses DIS.014_UCN_001_resolved.yaml → DIS.014', () => {
    expect(parseResolvedId('DIS.014_UCN_001_resolved.yaml')).toBe('DIS.014');
  });

  it('parses DIS.015_CDLM_005_resolved.yaml → DIS.015', () => {
    expect(parseResolvedId('DIS.015_CDLM_005_resolved.yaml')).toBe('DIS.015');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// loadResolvedIds
// ─────────────────────────────────────────────────────────────────────────────

describe('loadResolvedIds', () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = mkdtempSync(join(tmpdir(), 'icr_gate_test_'));
  });

  afterEach(() => {
    rmSync(tmpDir, { recursive: true, force: true });
  });

  it('returns empty set when RESOLVED/ does not exist', () => {
    const ids = loadResolvedIds(join(tmpDir, 'RESOLVED'));
    expect(ids.size).toBe(0);
  });

  it('loads conflict IDs from existing RESOLVED/ files', () => {
    const resolvedDir = join(tmpDir, 'RESOLVED');
    mkdirSync(resolvedDir);
    writeFileSync(join(resolvedDir, 'DIS.013_MSR_377_resolved.yaml'), 'conflict_id: DIS.013\n');
    writeFileSync(join(resolvedDir, 'DIS.014_UCN_001_resolved.yaml'), 'conflict_id: DIS.014\n');

    const ids = loadResolvedIds(resolvedDir);
    expect(ids.has('DIS.013')).toBe(true);
    expect(ids.has('DIS.014')).toBe(true);
    expect(ids.size).toBe(2);
  });

  it('ignores non-yaml files in RESOLVED/', () => {
    const resolvedDir = join(tmpDir, 'RESOLVED');
    mkdirSync(resolvedDir);
    writeFileSync(join(resolvedDir, 'README.md'), '# readme');
    writeFileSync(join(resolvedDir, 'DIS.013_MSR_377_resolved.yaml'), 'conflict_id: DIS.013\n');

    const ids = loadResolvedIds(resolvedDir);
    expect(ids.size).toBe(1);
    expect(ids.has('DIS.013')).toBe(true);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// filterUnresolved — gate exit-code behavior
// ─────────────────────────────────────────────────────────────────────────────

describe('filterUnresolved', () => {
  it('(AC2a) returns conflict when its id is NOT in resolved set → gate exits 1', () => {
    const conflicts = [makeConflict('DIS.099')];
    const resolved = new Set<string>(['DIS.013']);

    const unresolved = filterUnresolved(conflicts, resolved);
    expect(unresolved).toHaveLength(1);
    expect(unresolved[0].conflict_id).toBe('DIS.099');
  });

  it('(AC2b) returns empty list when all conflicts ARE in resolved set → gate exits 0', () => {
    const conflicts = [makeConflict('DIS.013')];
    const resolved = new Set<string>(['DIS.013']);

    const unresolved = filterUnresolved(conflicts, resolved);
    expect(unresolved).toHaveLength(0);
  });

  it('returns empty list when conflict list is empty → gate exits 0', () => {
    const conflicts: ConflictRecord[] = [];
    const resolved = new Set<string>(['DIS.013']);

    const unresolved = filterUnresolved(conflicts, resolved);
    expect(unresolved).toHaveLength(0);
  });

  it('returns only unresolved conflicts when mix of resolved + unresolved', () => {
    const conflicts = [makeConflict('DIS.013'), makeConflict('DIS.099'), makeConflict('DIS.100')];
    const resolved = new Set<string>(['DIS.013']);

    const unresolved = filterUnresolved(conflicts, resolved);
    expect(unresolved).toHaveLength(2);
    const ids = unresolved.map(c => c.conflict_id);
    expect(ids).toContain('DIS.099');
    expect(ids).toContain('DIS.100');
    expect(ids).not.toContain('DIS.013');
  });

  it('handles DIS.AUTO.* conflict IDs correctly', () => {
    const conflicts = [makeConflict('DIS.AUTO.42'), makeConflict('DIS.013')];
    const resolved = new Set<string>(['DIS.013', 'DIS.AUTO.42']);

    const unresolved = filterUnresolved(conflicts, resolved);
    expect(unresolved).toHaveLength(0);
  });
});
