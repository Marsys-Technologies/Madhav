// FAIL fixture — check_wave2_module_scope_hazards.py — MUST be reported as pool_construction=1.
//
// A module-scope `new Pool(...)` construction — graded TIER-2-EQUIVALENT per D-80 section 5
// (opens no socket by itself), not tier-1, but still a reportable module-scope side effect.

import { Pool } from 'pg'

const pool = new Pool({ connectionString: process.env.DATABASE_URL })

export function unrelated(): void {
  void pool
}
