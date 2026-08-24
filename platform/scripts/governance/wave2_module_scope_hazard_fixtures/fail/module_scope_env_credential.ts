// FAIL fixture — check_wave2_module_scope_hazards.py — MUST be reported as env_credential=1.
//
// A module-scope call that loads a file named `.env.local` / `.env.rag` into
// process.env. Per D-125, such a file is PRESUMED to carry credentials — the presumption
// is the ruling, this detector never opens the file to check.

function loadEnv(file: string): void {
  // (body irrelevant to the detector — it only looks at the call site)
}

loadEnv('.env.local')
