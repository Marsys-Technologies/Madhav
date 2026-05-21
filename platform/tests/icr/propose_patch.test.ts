/**
 * propose_patch.test.ts — ICR-S4 unit tests for the propose-patch builder
 *
 * Gates:
 *   - buildProposePatchArtifact() returns a ProposePatchArtifact with all required fields
 *   - propagation_chain.tier 1 includes MSR.377
 *   - munta_propose_patch_emitted: PROPOSED/DIS.013_MSR.377_proposed.yaml exists on disk
 */

import { describe, it, expect } from 'vitest';
import { existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildProposePatchArtifact } from '@/lib/icr/propose_patch';
import type { ConflictRecord } from '@/lib/icr/types';

// ─────────────────────────────────────────────────────────────────────────────
// Fixture: the DIS.013 ConflictRecord as emitted by ICR-S3
// ─────────────────────────────────────────────────────────────────────────────

const DIS_013: ConflictRecord = {
  conflict_id: 'DIS.013',
  conflict_class: 'A',
  signal_ids_affected: ['MSR.377'],
  description:
    'Signal MSR.377 name asserts "Muntha in Gemini" but FORENSIC VRS.MUNTHA.SIGN = "Libra (7th House)". ' +
    'The signal name is inconsistent with the L1 canonical Varshaphal record.',
  detected_at: '2026-05-21T02:43:09.734Z',
  evidence:
    'signal_name: "Tajika — Muntha Position at Age 42 (2026): Muntha in Gemini 3H = UL/Spouse-Domain Annual Activation" ' +
    '→ asserted_sign: "Gemini" | ' +
    'FORENSIC VRS.MUNTHA.SIGN: "Libra (7th House)" → forensic_sign: "Libra" | ' +
    'MISMATCH: Gemini ≠ Libra',
};

// ─────────────────────────────────────────────────────────────────────────────
// Tests
// ─────────────────────────────────────────────────────────────────────────────

describe('buildProposePatchArtifact (ICR-S4)', () => {
  it('returns a ProposePatchArtifact with all required top-level fields', () => {
    const artifact = buildProposePatchArtifact(DIS_013, {
      authored_on: '2026-05-21',
    });

    expect(artifact.conflict_id).toBe('DIS.013');
    expect(artifact.conflict_class).toBe('A');
    expect(artifact.signal_ids_affected).toEqual(['MSR.377']);
    expect(typeof artifact.proposed_change).toBe('string');
    expect(artifact.proposed_change.length).toBeGreaterThan(0);
    expect(Array.isArray(artifact.propagation_chain)).toBe(true);
    expect(typeof artifact.confidence).toBe('number');
    expect(artifact.confidence).toBeGreaterThan(0);
    expect(artifact.confidence).toBeLessThanOrEqual(1);
    expect(artifact.authored_by).toBe('ICR-S4');
    expect(artifact.authored_on).toBe('2026-05-21');
    expect(artifact.status).toBe('pending');
  });

  it('propagation_chain has exactly 5 tiers (1–5)', () => {
    const artifact = buildProposePatchArtifact(DIS_013, {
      authored_on: '2026-05-21',
    });

    expect(artifact.propagation_chain).toHaveLength(5);
    const tierNumbers = artifact.propagation_chain.map((t) => t.tier);
    expect(tierNumbers).toEqual([1, 2, 3, 4, 5]);
  });

  it('propagation_chain tier 1 (signal) includes MSR.377', () => {
    const artifact = buildProposePatchArtifact(DIS_013, {
      authored_on: '2026-05-21',
    });

    const tier1 = artifact.propagation_chain.find((t) => t.tier === 1);
    expect(tier1).toBeDefined();
    expect(tier1!.tier_name).toBe('signal');
    expect(tier1!.mandatory).toBe(true);
    expect(tier1!.affected_ids).toContain('MSR.377');
  });

  it('propagation_chain tier 2 is mandatory with tier_name ucn_edges', () => {
    const artifact = buildProposePatchArtifact(DIS_013, {
      authored_on: '2026-05-21',
    });

    const tier2 = artifact.propagation_chain.find((t) => t.tier === 2);
    expect(tier2).toBeDefined();
    expect(tier2!.tier_name).toBe('ucn_edges');
    expect(tier2!.mandatory).toBe(true);
    // affected_ids may be empty (no structured UCN edges reference MSR.377)
    expect(Array.isArray(tier2!.affected_ids)).toBe(true);
  });

  it('propagation_chain tiers 3–5 are advisory (mandatory: false) with empty ids', () => {
    const artifact = buildProposePatchArtifact(DIS_013, {
      authored_on: '2026-05-21',
    });

    const advisoryTiers = artifact.propagation_chain.filter((t) => t.tier >= 3);
    expect(advisoryTiers).toHaveLength(3);
    for (const tier of advisoryTiers) {
      expect(tier.mandatory).toBe(false);
      expect(tier.affected_ids).toEqual([]);
    }
  });

  it('proposed_change is a diff-format string containing the before and after signal_name', () => {
    const artifact = buildProposePatchArtifact(DIS_013, {
      authored_on: '2026-05-21',
    });

    // Must contain a minus line (before) and plus line (after)
    expect(artifact.proposed_change).toMatch(/^-\s+signal_name:/m);
    expect(artifact.proposed_change).toMatch(/^\+\s+signal_name:/m);
    // Before: Gemini
    expect(artifact.proposed_change).toMatch(/Gemini/);
    // After: Libra
    expect(artifact.proposed_change).toMatch(/Libra/);
  });

  it('confidence is 0.95 for Class A conflicts', () => {
    const artifact = buildProposePatchArtifact(DIS_013, {
      authored_on: '2026-05-21',
    });
    expect(artifact.confidence).toBe(0.95);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Gate: munta_propose_patch_emitted
// Verifies the patch YAML file was written to PROPOSED/ by ICR-S4
// ─────────────────────────────────────────────────────────────────────────────

describe('munta_propose_patch_emitted gate (ICR-S4)', () => {
  it('DIS.013_MSR.377_proposed.yaml exists in PROPOSED/', () => {
    // Resolve relative to repo root (this test file lives at platform/tests/icr/)
    const thisFile = fileURLToPath(import.meta.url);
    const repoRoot = resolve(dirname(thisFile), '..', '..', '..');
    const proposedFile = resolve(
      repoRoot,
      '00_ARCHITECTURE',
      'CONFLICT_PATCHES',
      'PROPOSED',
      'DIS.013_MSR.377_proposed.yaml',
    );

    expect(
      existsSync(proposedFile),
      `Expected patch file to exist at: ${proposedFile}`,
    ).toBe(true);
  });

  it('DIS.013_MSR.377_proposed.yaml contains a non-empty tier_1 propagation', () => {
    const thisFile = fileURLToPath(import.meta.url);
    const repoRoot = resolve(dirname(thisFile), '..', '..', '..');
    const proposedFile = resolve(
      repoRoot,
      '00_ARCHITECTURE',
      'CONFLICT_PATCHES',
      'PROPOSED',
      'DIS.013_MSR.377_proposed.yaml',
    );

    if (!existsSync(proposedFile)) {
      // Skip body of this test if file doesn't exist (previous test will already fail)
      return;
    }

    const { readFileSync } = require('node:fs');
    const content = readFileSync(proposedFile, 'utf-8') as string;

    // tier_1 must list MSR.377
    expect(content).toMatch(/tier_1:/);
    expect(content).toMatch(/MSR\.377/);
  });
});
