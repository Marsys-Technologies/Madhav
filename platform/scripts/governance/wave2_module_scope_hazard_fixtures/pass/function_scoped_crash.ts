// PASS fixture — check_wave2_module_scope_hazards.py — MUST produce ZERO findings.
//
// `process.exit(...)` exists in this file, but only inside a function body — it does not
// run on import, only when the function is actually called. Not module-scope.

export function maybeExit(ok: boolean): void {
  if (!ok) {
    process.exit(1)
  }
}
