// PASS fixture — check_wave2_module_scope_hazards.py — MUST produce ZERO findings.
//
// `new Pool(...)` exists in this file, but only inside a function body — no Pool is
// constructed merely by importing this module.

import { Pool } from 'pg'

export function getPool(): Pool {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL })
  return pool
}
