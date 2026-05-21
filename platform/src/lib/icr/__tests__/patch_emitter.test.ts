/**
 * patch_emitter.test.ts — Unit tests for ICR propose-patch emitter
 *
 * ICR-S4 (2026-05-21)
 *
 * Tests use a tmp directory as repoRoot to avoid polluting PROPOSED/.
 * Real PROPOSED/ is only written by emit_dis013_patch.ts (the governance script).
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, readFileSync, existsSync, rmSync } from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import {
  emitProposePatch,
  proposedFilename,
  serializeProposePatch,
  type ProposePatch,
} from '../patch_emitter';
import type { ConflictRecord } from '../types';

// ─────────────────────────────────────────────────────────────────────────────
// Fixtures
// ─────────────────────────────────────────────────────────────────────────────

const FAKE_CONFLICT_DIS013: ConflictRecord = {
  conflict_id: 'DIS.013',
  conflict_class: 'A',
  signal_ids_affected: ['MSR.377'],
  description:
    'signal_name asserts sign(s) [Gemini] but falsifier confirms [Virgo] — sign/house mismatch.',
  detected_at: '2026-05-21T08:39:06.325Z',
  evidence:
    'signal_name: "Tajika — Muntha Position at Age 42 (2026): Muntha in Gemini 3H = UL/Spouse-Domain Annual Activation" | falsifier: "Muntha at 42 = Virgo 6H = confirmed."',
};

const FAKE_CONFLICT_GENERIC: ConflictRecord = {
  conflict_id: 'DIS.AUTO.100',
  conflict_class: 'A',
  signal_ids_affected: ['MSR.100'],
  description: 'Test conflict',
  detected_at: '2026-05-21T00:00:00.000Z',
  evidence: 'signal_name: "Sun in Leo 5H" | falsifier: "confirmed"',
};

const BASE_PATCH_DIS013 = {
  conflict_id: 'DIS.013',
  signal_id: 'MSR.377',
  field: 'signal_name',
  current_value:
    'Tajika — Muntha Position at Age 42 (2026): Muntha in Gemini 3H = UL/Spouse-Domain Annual Activation',
  proposed_value:
    'Tajika — Muntha Position at Age 42 (2026): Muntha in Virgo 6H = Dusthana Annual Activation (6H: Health/Service/Conflict)',
  rationale:
    'Muntha year = 1984 + 42 = 2026; 42 mod 12 = 6; 6th sign from Aries = Virgo. signal_name incorrectly states Gemini 3H. Falsifier confirms Virgo 6H.',
  propagation_chain: [
    'MSR.377 signal_name (primary correction target)',
    'any downstream signal that references Muntha sign as Gemini',
  ],
} as const;

// ─────────────────────────────────────────────────────────────────────────────
// Test setup/teardown
// ─────────────────────────────────────────────────────────────────────────────

let tmpRoot: string;

beforeEach(() => {
  tmpRoot = mkdtempSync(path.join(os.tmpdir(), 'icr-patch-test-'));
});

afterEach(() => {
  rmSync(tmpRoot, { recursive: true, force: true });
});

// ─────────────────────────────────────────────────────────────────────────────
// proposedFilename
// ─────────────────────────────────────────────────────────────────────────────

describe('proposedFilename', () => {
  it('converts dots in signal_id to underscores', () => {
    expect(proposedFilename('DIS.013', 'MSR.377')).toBe('DIS.013_MSR_377_proposed.yaml');
  });

  it('preserves dots in conflict_id', () => {
    expect(proposedFilename('DIS.AUTO.214', 'MSR.214')).toBe('DIS.AUTO.214_MSR_214_proposed.yaml');
  });

  it('DIS.013 + MSR.377 produces canonical filename', () => {
    const filename = proposedFilename('DIS.013', 'MSR.377');
    expect(filename).toBe('DIS.013_MSR_377_proposed.yaml');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// serializeProposePatch
// ─────────────────────────────────────────────────────────────────────────────

describe('serializeProposePatch', () => {
  const sample: ProposePatch = {
    conflict_id: 'DIS.013',
    signal_id: 'MSR.377',
    field: 'signal_name',
    current_value: 'Muntha in Gemini 3H',
    proposed_value: 'Muntha in Virgo 6H',
    rationale: 'Mathematical proof: 42 mod 12 = 6 = Virgo',
    propagation_chain: ['MSR.377 signal_name', 'downstream references'],
    proposed_at: '2026-05-21T10:00:00.000Z',
    status: 'proposed',
  };

  it('contains all required top-level fields', () => {
    const yaml = serializeProposePatch(sample);
    expect(yaml).toContain('conflict_id: DIS.013');
    expect(yaml).toContain('signal_id: MSR.377');
    expect(yaml).toContain('field: signal_name');
    expect(yaml).toContain('status: proposed');
    expect(yaml).toContain('proposed_at: 2026-05-21T10:00:00.000Z');
  });

  it('serializes propagation_chain as a YAML list', () => {
    const yaml = serializeProposePatch(sample);
    expect(yaml).toContain('propagation_chain:');
    expect(yaml).toContain('  - "MSR.377 signal_name"');
    expect(yaml).toContain('  - "downstream references"');
  });

  it('wraps current_value in double quotes', () => {
    const yaml = serializeProposePatch(sample);
    expect(yaml).toContain('current_value: "Muntha in Gemini 3H"');
  });

  it('wraps proposed_value in double quotes', () => {
    const yaml = serializeProposePatch(sample);
    expect(yaml).toContain('proposed_value: "Muntha in Virgo 6H"');
  });

  it('escapes double quotes inside string values', () => {
    const withQuotes: ProposePatch = {
      ...sample,
      rationale: 'Result is "Virgo"',
    };
    const yaml = serializeProposePatch(withQuotes);
    expect(yaml).toContain('\\"Virgo\\"');
  });

  it('ends with a newline', () => {
    const yaml = serializeProposePatch(sample);
    expect(yaml.endsWith('\n')).toBe(true);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// emitProposePatch
// ─────────────────────────────────────────────────────────────────────────────

describe('emitProposePatch', () => {
  it('writes a file to PROPOSED/ with the correct filename', () => {
    const writtenPath = emitProposePatch(tmpRoot, FAKE_CONFLICT_DIS013, BASE_PATCH_DIS013);
    const expectedPath = path.join(tmpRoot, 'PROPOSED', 'DIS.013_MSR_377_proposed.yaml');
    expect(writtenPath).toBe(expectedPath);
    expect(existsSync(expectedPath)).toBe(true);
  });

  it('creates PROPOSED/ directory if it does not exist', () => {
    const proposedDir = path.join(tmpRoot, 'PROPOSED');
    expect(existsSync(proposedDir)).toBe(false);
    emitProposePatch(tmpRoot, FAKE_CONFLICT_DIS013, BASE_PATCH_DIS013);
    expect(existsSync(proposedDir)).toBe(true);
  });

  it('written file contains conflict_id', () => {
    const writtenPath = emitProposePatch(tmpRoot, FAKE_CONFLICT_DIS013, BASE_PATCH_DIS013);
    const content = readFileSync(writtenPath, 'utf-8');
    expect(content).toContain('conflict_id: DIS.013');
  });

  it('written file contains signal_id', () => {
    const writtenPath = emitProposePatch(tmpRoot, FAKE_CONFLICT_DIS013, BASE_PATCH_DIS013);
    const content = readFileSync(writtenPath, 'utf-8');
    expect(content).toContain('signal_id: MSR.377');
  });

  it('written file contains field', () => {
    const writtenPath = emitProposePatch(tmpRoot, FAKE_CONFLICT_DIS013, BASE_PATCH_DIS013);
    const content = readFileSync(writtenPath, 'utf-8');
    expect(content).toContain('field: signal_name');
  });

  it('written file has status: proposed', () => {
    const writtenPath = emitProposePatch(tmpRoot, FAKE_CONFLICT_DIS013, BASE_PATCH_DIS013);
    const content = readFileSync(writtenPath, 'utf-8');
    expect(content).toContain('status: proposed');
  });

  it('proposed_at is a valid ISO 8601 date string', () => {
    const writtenPath = emitProposePatch(tmpRoot, FAKE_CONFLICT_DIS013, BASE_PATCH_DIS013);
    const content = readFileSync(writtenPath, 'utf-8');
    const match = content.match(/proposed_at:\s*(\S+)/);
    expect(match).not.toBeNull();
    const dateStr = match![1];
    const parsed = new Date(dateStr);
    expect(Number.isNaN(parsed.getTime())).toBe(false);
    // Must contain T and Z (ISO 8601 with time)
    expect(dateStr).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
  });

  it('propagation_chain appears as a YAML list in the file', () => {
    const writtenPath = emitProposePatch(tmpRoot, FAKE_CONFLICT_DIS013, BASE_PATCH_DIS013);
    const content = readFileSync(writtenPath, 'utf-8');
    expect(content).toContain('propagation_chain:');
    // Each chain item should be indented as a YAML list item
    expect(content).toMatch(/  - "/);
  });

  it('emitting for DIS.013 produces DIS.013_MSR_377_proposed.yaml', () => {
    const writtenPath = emitProposePatch(tmpRoot, FAKE_CONFLICT_DIS013, BASE_PATCH_DIS013);
    expect(path.basename(writtenPath)).toBe('DIS.013_MSR_377_proposed.yaml');
  });

  it('emitting for a generic conflict produces the correct filename', () => {
    const writtenPath = emitProposePatch(tmpRoot, FAKE_CONFLICT_GENERIC, {
      conflict_id: 'DIS.AUTO.100',
      signal_id: 'MSR.100',
      field: 'signal_name',
      current_value: 'Sun in Leo 5H',
      proposed_value: 'Sun in Leo 5H (unchanged — no correction needed)',
      rationale: 'Test only',
      propagation_chain: [],
    });
    expect(path.basename(writtenPath)).toBe('DIS.AUTO.100_MSR_100_proposed.yaml');
  });

  it('proposed_value is written correctly for DIS.013 Virgo correction', () => {
    const writtenPath = emitProposePatch(tmpRoot, FAKE_CONFLICT_DIS013, BASE_PATCH_DIS013);
    const content = readFileSync(writtenPath, 'utf-8');
    expect(content).toContain('Virgo 6H');
    // Must NOT contain the incorrect Gemini 3H in proposed_value line
    const lines = content.split('\n');
    const proposedLine = lines.find(l => l.startsWith('proposed_value:'));
    expect(proposedLine).toBeDefined();
    expect(proposedLine).not.toContain('Gemini 3H');
  });
});
