import { describe, it, expect } from 'vitest';
import {
  buildReadingContract,
  COMPOSITION_SEQUENCE,
  MANDATORY_GESTALT_VOLUNTEER,
  READING_CONTRACT_EXAMPLE,
} from '../resources/vidhi/composition_doctrine.js';

describe('EL-29 composition doctrine + EL-05 volunteering', () => {
  it('the composition sequence is the fixed six-stage doctrine order', () => {
    expect(COMPOSITION_SEQUENCE).toEqual([
      'gestalt',
      'promise',
      'evidence_chains',
      'tensions_adjudication',
      'timing',
      'guidance',
    ]);
  });

  it('STRUCTURAL GATE: a BLOCKED dossier page yields NO composition content (empty stages)', () => {
    const contract = buildReadingContract({ synthesis_gate: 'BLOCKED', coverage_so_far: { pct: 40 } });
    expect(contract.synthesis_gate).toBe('BLOCKED');
    expect(contract.stages).toEqual([]); // withheld by construction, not by prose
    expect(contract.gate_note).toMatch(/BLOCKED/);
  });

  it('an OPEN gate yields the full six-stage sequence, in order', () => {
    const contract = buildReadingContract({ synthesis_gate: 'OPEN', coverage_so_far: { pct: 100 } });
    expect(contract.synthesis_gate).toBe('OPEN');
    expect(contract.stages.map((s) => s.stage)).toEqual([...COMPOSITION_SEQUENCE]);
    expect(contract.stages.map((s) => s.order)).toEqual([1, 2, 3, 4, 5, 6]);
  });

  it('EL-05: stage 1 (gestalt) MANDATES top-N gestalt volunteering; no other stage carries it', () => {
    const contract = buildReadingContract({ synthesis_gate: 'OPEN' });
    const gestalt = contract.stages.find((s) => s.stage === 'gestalt');
    expect(gestalt?.gestalt_volunteer).toBe(MANDATORY_GESTALT_VOLUNTEER);
    expect(MANDATORY_GESTALT_VOLUNTEER.mandatory).toBe(true);
    expect(MANDATORY_GESTALT_VOLUNTEER.served_unprompted).toBe(true);
    expect(MANDATORY_GESTALT_VOLUNTEER.serving_tools.map((t) => t.tool)).toEqual([
      'synth_chart_brief_get',
      'bodha_discoveries_get',
      'bodha_chart_digest_get',
    ]);
    for (const s of contract.stages.filter((s) => s.stage !== 'gestalt')) {
      expect(s.gestalt_volunteer).toBeUndefined();
    }
  });

  it('the exported worked example is the OPEN contract', () => {
    expect(READING_CONTRACT_EXAMPLE.synthesis_gate).toBe('OPEN');
    expect(READING_CONTRACT_EXAMPLE.stages).toHaveLength(6);
  });
});
