// FAIL fixture — check_wave2_module_scope_hazards.py — MUST be reported as crash_throw=1.
//
// A bare `throw` statement at module scope, NOT inside any try/catch and NOT inside any
// function/class/arrow body. Importing this file crashes the importer unconditionally.

const CONFIG = process.env.SOME_CONFIG

if (!CONFIG) {
  throw new Error('SOME_CONFIG not set')
}

export function unrelated(): void {
  // nothing
}
