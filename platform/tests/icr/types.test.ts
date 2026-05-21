// ICR type compilation test — ICR-S1 (2026-05-21)
import type { ConflictRecord, ProposePatchArtifact, PropagationChainTier } from '../../src/lib/icr/types';
import { describe, it, expect } from 'vitest';

describe('ICR types (ICR-S1)', () => {
  it('ConflictRecord shape compiles correctly', () => {
    const r: ConflictRecord = {
      conflict_id: 'DIS.013',
      conflict_class: 'A',
      signal_ids_affected: ['MSR.377'],
      description: 'Muntha claim disagrees with FORENSIC source',
      detected_at: '2026-05-21T00:00:00Z',
      evidence: 'MSR.377 claims Muntha in Virgo; FORENSIC says Aquarius',
    };
    expect(r.conflict_id).toBe('DIS.013');
    expect(r.conflict_class).toBe('A');
    expect(r.signal_ids_affected).toEqual(['MSR.377']);
  });

  it('ProposePathStatus is correctly constrained', () => {
    const s: ProposePatchArtifact['status'] = 'pending';
    expect(['pending', 'confirmed', 'rejected', 'escalated']).toContain(s);
  });

  it('PropagationChainTier tier values are constrained to 1–5', () => {
    const tier: PropagationChainTier = {
      tier: 1,
      tier_name: 'signal',
      mandatory: true,
      affected_ids: ['MSR.377'],
    };
    expect(tier.tier).toBe(1);
    expect(tier.tier_name).toBe('signal');
  });

  it('ProposePatchArtifact shape compiles correctly', () => {
    const patch: ProposePatchArtifact = {
      conflict_id: 'DIS.013',
      conflict_class: 'A',
      signal_ids_affected: ['MSR.377'],
      proposed_change: '-  muntha: Virgo\n+  muntha: Aquarius',
      propagation_chain: [
        { tier: 1, tier_name: 'signal', mandatory: true, affected_ids: ['MSR.377'] },
      ],
      confidence: 0.9,
      authored_by: 'ICR-S1-scaffold',
      authored_on: '2026-05-21',
      status: 'pending',
    };
    expect(patch.conflict_id).toBe('DIS.013');
    expect(patch.confidence).toBe(0.9);
    expect(patch.propagation_chain).toHaveLength(1);
  });
});
