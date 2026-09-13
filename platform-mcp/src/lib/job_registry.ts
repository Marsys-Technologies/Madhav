export type JobStatus = 'pending' | 'running' | 'complete' | 'failed';

export interface JobProgress {
  message: string;
  pct: number;
}

export interface Job<TResult = unknown> {
  id: string;
  chartId: string;
  /** Authenticated owner. Job ids are correlation handles, never bearer grants. */
  ownerKey?: string;
  status: JobStatus;
  progress?: JobProgress;
  result?: TResult;
  error?: string;
  createdAt: number;
}

/**
 * In-memory, chart-scoped async job store.
 *
 * Gives a caller an immediate job handle back for a long-running operation
 * (e.g. prashna_ask's engine loop) instead of blocking on the full run.
 * Jobs are held in memory only — they do not survive a process restart.
 * Expired jobs are swept opportunistically on every create/get, so a quiet
 * process retains at most its last active set and normal traffic cannot grow
 * the map without bound.
 */
export class JobRegistry<TResult = unknown> {
  private jobs = new Map<string, Job<TResult>>();
  private ttlMs: number;

  constructor(opts: { ttlMs?: number } = {}) {
    this.ttlMs = opts.ttlMs ?? 15 * 60 * 1000;
  }

  create(input: { chartId: string; ownerKey?: string }): Job<TResult> {
    this.sweepExpired();
    const job: Job<TResult> = {
      id: crypto.randomUUID(),
      chartId: input.chartId,
      ownerKey: input.ownerKey,
      status: 'pending',
      createdAt: Date.now(),
    };
    this.jobs.set(job.id, job);
    return job;
  }

  // Raw lookup is intentionally internal. Externally served callers MUST bind
  // the result to ownerKey and re-check chart entitlement.
  get(id: string): Job<TResult> | undefined {
    this.sweepExpired();
    return this.jobs.get(id);
  }

  updateProgress(id: string, progress: JobProgress): void {
    const job = this.jobs.get(id);
    if (!job) return;
    job.status = 'running';
    job.progress = progress;
  }

  complete(id: string, result: TResult): void {
    const job = this.jobs.get(id);
    if (!job) return;
    job.status = 'complete';
    job.result = result;
  }

  fail(id: string, error: string): void {
    const job = this.jobs.get(id);
    if (!job) return;
    job.status = 'failed';
    job.error = error;
  }

  sweepExpired(): void {
    const now = Date.now();
    for (const [id, job] of this.jobs) {
      if (now - job.createdAt > this.ttlMs) this.jobs.delete(id);
    }
  }
}
