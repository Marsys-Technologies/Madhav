// PASS fixture — check_wave2_module_scope_hazards.py — MUST produce ZERO findings.
//
// A `throw` at module scope, but inside a `try { }` whose `catch` handles it locally —
// importing this file does not crash the importer. This is the module-scope-crash
// detector's one documented exclusion (see the docstring's "WHAT THIS DOES NOT COVER"):
// it does not verify the catch body never re-throws or calls process.exit — a re-throwing
// catch would itself be caught by this same detector if it calls process.exit, and is
// otherwise out of scope for a source-text scanner.

try {
  if (!process.env.SOME_CONFIG) {
    throw new Error('SOME_CONFIG not set')
  }
} catch (err) {
  console.error('non-fatal, continuing with defaults:', err)
}
