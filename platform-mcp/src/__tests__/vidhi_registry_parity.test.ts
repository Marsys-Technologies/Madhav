/**
 * vidhi_registry_parity.test.ts — D-2 Lane V-2 drift guard (BIND_D-2.md §F1.7 ledger row 14).
 *
 * Proves the MCP-served vidhi rows "match V-1's registry" by importing BOTH:
 *   - the vendored mirror this lane serves from (src/resources/vidhi), and
 *   - V-1's canonical module (platform/src/lib/vidhi),
 * and asserting deep-equality of the data + compiler output. Cross-package import in a TEST is
 * the established pattern here (see r5_codegen_parity.test.ts importing platform/src/... directly)
 * — it runs only in the test process, never in the shipped MCP build (which cannot cross the
 * package's rootDir). A drift between mirror and canonical fails THIS test loudly.
 */
import { describe, it, expect } from 'vitest';

// Vendored mirror (what the MCP server actually serves):
import {
  VIDHI_PRIMITIVES as MIRROR_PRIMITIVES,
  VIDHI_INTENT_FLOORS as MIRROR_FLOORS,
  compileContract as mirrorCompile,
  defaultRegistry as mirrorRegistry,
} from '../resources/vidhi/index.js';

// V-1 canonical (source of truth):
import {
  VIDHI_PRIMITIVES as CANON_PRIMITIVES,
  VIDHI_INTENT_FLOORS as CANON_FLOORS,
} from '../../../platform/src/lib/vidhi/registry_data.ts';
import {
  compileContract as canonCompile,
  defaultRegistry as canonRegistry,
} from '../../../platform/src/lib/vidhi/compiler.ts';
import type { ScopeTuple } from '../../../platform/src/lib/vidhi/types.ts';

describe('vidhi registry parity — served mirror equals V-1 canonical', () => {
  it('VIDHI_PRIMITIVES deep-equal (rows match V-1)', () => {
    expect(MIRROR_PRIMITIVES).toEqual(CANON_PRIMITIVES);
    expect(MIRROR_PRIMITIVES.length).toBeGreaterThanOrEqual(30);
  });

  it('VIDHI_INTENT_FLOORS deep-equal (all 11 intents)', () => {
    // VIDHI-PŪRṆATĀ P-2 (F1): 8 → 11 intent floors (added spirituality_deepdive [MANDATORY],
    // education_deepdive, progeny_deepdive [CANDIDATE]). The deep-equal below still enforces
    // mirror↔canonical parity; only the count literal advances with the taxonomy.
    expect(MIRROR_FLOORS).toEqual(CANON_FLOORS);
    expect(MIRROR_FLOORS.length).toBe(11);
  });

  it('compiler produces byte-identical contracts for the same tuple', () => {
    const tuple: ScopeTuple = {
      intent: 'wealth_deepdive',
      domains: ['wealth'],
      width: 'standard',
      depth: 'deepdive',
      horizon: 'current',
      intervention: false,
      entitlement: 'native',
    };
    const chartId = '482012f1-710e-4a25-994a-93821f5871aa';
    const mirror = mirrorCompile(tuple, mirrorRegistry(), chartId);
    const canon = canonCompile(tuple, canonRegistry(), chartId);
    expect(JSON.stringify(mirror)).toBe(JSON.stringify(canon));
  });
});
