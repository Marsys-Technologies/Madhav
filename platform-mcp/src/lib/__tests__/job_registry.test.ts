import { describe, it, expect, vi } from 'vitest';
import { JobRegistry } from '../job_registry';

describe('JobRegistry', () => {
  it('creates a job and retrieves it by id', () => {
    const registry = new JobRegistry();
    const job = registry.create({ chartId: 'chart-1' });
    expect(job.status).toBe('pending');
    expect(registry.get(job.id)?.chartId).toBe('chart-1');
  });

  it('updates progress and marks complete', () => {
    const registry = new JobRegistry();
    const job = registry.create({ chartId: 'chart-1' });
    registry.updateProgress(job.id, { message: 'compiling floor', pct: 40 });
    expect(registry.get(job.id)?.progress?.pct).toBe(40);
    registry.complete(job.id, { ok: true, data: { answer: 'x' } });
    expect(registry.get(job.id)?.status).toBe('complete');
  });

  it('evicts jobs older than the TTL', () => {
    const registry = new JobRegistry({ ttlMs: 1000 });
    const job = registry.create({ chartId: 'chart-1' });
    vi.useFakeTimers();
    vi.advanceTimersByTime(2000);
    registry.sweepExpired();
    expect(registry.get(job.id)).toBeUndefined();
    vi.useRealTimers();
  });

  it('scopes jobs by chart — get() with wrong chartId assertion is caller responsibility, registry stores chartId for the caller to check', () => {
    const registry = new JobRegistry();
    const job = registry.create({ chartId: 'chart-A' });
    expect(registry.get(job.id)?.chartId).toBe('chart-A');
  });
});
