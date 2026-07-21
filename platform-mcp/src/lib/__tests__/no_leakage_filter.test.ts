import { describe, it, expect } from 'vitest';
import { filterLeakedCapabilities } from '../no_leakage_filter';

describe('filterLeakedCapabilities', () => {
  it('drops capabilities flagged calibration_context_only', () => {
    const caps = [
      { id: 'a', calibration_context_only: true },
      { id: 'b', calibration_context_only: false },
      { id: 'c' },
    ];
    const result = filterLeakedCapabilities(caps);
    expect(result.map((c) => c.id)).toEqual(['b', 'c']);
  });

  it('is a pure function — does not mutate input', () => {
    const caps = [{ id: 'a', calibration_context_only: true }];
    const copy = [...caps];
    filterLeakedCapabilities(caps);
    expect(caps).toEqual(copy);
  });

  it('keeps entries where the flag is absent or explicitly false', () => {
    const caps = [{ id: 'x' }, { id: 'y', calibration_context_only: false }];
    const result = filterLeakedCapabilities(caps);
    expect(result).toHaveLength(2);
  });

  it('returns an empty array when all capabilities are flagged', () => {
    const caps = [
      { id: 'a', calibration_context_only: true },
      { id: 'b', calibration_context_only: true },
    ];
    expect(filterLeakedCapabilities(caps)).toEqual([]);
  });

  it('handles an empty input array', () => {
    expect(filterLeakedCapabilities([])).toEqual([]);
  });
});
