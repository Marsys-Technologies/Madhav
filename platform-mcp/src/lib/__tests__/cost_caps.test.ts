import { describe, it, expect, vi } from 'vitest';
import { CostCapTracker } from '../cost_caps';

describe('CostCapTracker', () => {
  it('allows calls under both caps', () => {
    const tracker = new CostCapTracker({ maxCalls: 10, maxWallClockMs: 120_000 });
    for (let i = 0; i < 9; i++) {
      expect(tracker.checkAndRecordCall().stopped).toBe(false);
    }
  });

  it('stops on call-count cap and reports which cap tripped', () => {
    const tracker = new CostCapTracker({ maxCalls: 2, maxWallClockMs: 120_000 });
    tracker.checkAndRecordCall();
    tracker.checkAndRecordCall();
    const result = tracker.checkAndRecordCall();
    expect(result.stopped).toBe(true);
    expect(result.reason).toBe('call_count_cap');
  });

  it('stops on wall-clock cap independent of call count', () => {
    vi.useFakeTimers();
    const tracker = new CostCapTracker({ maxCalls: 10, maxWallClockMs: 1000 });
    vi.advanceTimersByTime(1500);
    const result = tracker.checkAndRecordCall();
    expect(result.stopped).toBe(true);
    expect(result.reason).toBe('wall_clock_cap');
    vi.useRealTimers();
  });

  it('never silently truncates — stopped result always carries a judgmentFlag', () => {
    const tracker = new CostCapTracker({ maxCalls: 1, maxWallClockMs: 120_000 });
    tracker.checkAndRecordCall();
    const result = tracker.checkAndRecordCall();
    expect(result.judgmentFlag).toBe('cost_cap_call_count_exceeded');
  });
});
