export type JobStatus = 'pending' | 'running' | 'complete' | 'failed';

export interface JobProgress {
  message: string;
  pct: number;
}

export interface Job<TResult = unknown> {
  id: string;
  chartId: string;
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
 * Jobs are held in memory only — they do not survive a process restart —
 * and are swept on a TTL so the registry cannot grow unbounded.
 */
export class JobRegistry<TResult = unknown> {
  private jobs = new Map<string, Job<TResult>>();
  private ttlMs: number;

  constructor(opts: { ttlMs?: number } = {}) {
    this.ttlMs = opts.ttlMs ?? 15 * 60 * 1000;
  }

  create(input: { chartId: string }): Job<TResult> {
    const job: Job<TResult> = {
      id: crypto.randomUUID(),
      chartId: input.chartId,
      status: 'pending',
      createdAt: Date.now(),
    };
    this.jobs.set(job.id, job);
    return job;
  }

  get(id: string): Job<TResult> | undefined {
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
