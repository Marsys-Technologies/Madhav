import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { join } from 'path';

const SQL = readFileSync(
  join(__dirname, '../../../supabase/migrations/064_query_trace_steps_user_id.sql'),
  'utf-8',
);

describe('migration 064 — query_trace_steps.user_id', () => {
  it('adds user_id column with IF NOT EXISTS guard (idempotent)', () => {
    expect(SQL).toContain('ADD COLUMN IF NOT EXISTS user_id TEXT NULL');
  });

  it('creates sparse index on user_id WHERE NOT NULL', () => {
    expect(SQL).toContain('CREATE INDEX IF NOT EXISTS idx_qts_user_id');
    expect(SQL).toContain('WHERE user_id IS NOT NULL');
  });

  it('targets query_trace_steps table', () => {
    expect(SQL.toLowerCase()).toContain('query_trace_steps');
  });

  it('contains COMMENT documenting the purpose', () => {
    expect(SQL).toContain('PPL ownership check');
  });

  it('contains no destructive statements (no DROP, TRUNCATE, DELETE)', () => {
    const upper = SQL.toUpperCase();
    expect(upper).not.toContain('DROP TABLE');
    expect(upper).not.toContain('TRUNCATE');
    expect(upper).not.toContain('DELETE FROM');
  });
});
