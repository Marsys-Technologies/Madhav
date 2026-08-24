// FAIL fixture — check_wave2_module_scope_hazards.py — MUST be reported as crash_process_exit=1.
//
// A module-scope `if` block (not inside any function/class/arrow body) that calls
// `process.exit(...)` unconditionally on import — the exact shape D-123 found in
// audit/replay.ts:46-48 and trace/trace_smoke.ts:92-94.

const REQUIRED = process.env.SOME_VAR

if (!REQUIRED) {
  console.error('SOME_VAR not set')
  process.exit(1)
}

export function unrelated(): void {
  // nothing
}
