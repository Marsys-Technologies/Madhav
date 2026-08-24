// PASS fixture — check_wave2_module_scope_hazards.py — MUST produce ZERO findings.
//
// Two negative cases in one file:
//  1. `loadEnv('.env.local')` called INSIDE a function — not module scope.
//  2. `loadEnv('.env.example')` called AT module scope — module scope, but the loaded
//     filename is not `.env.local` / `.env.rag`, so it is outside D-125's presumption
//     (an example/template file is not presumed to carry real credentials).

function loadEnv(file: string): void {
  // body irrelevant
}

export function initLater(): void {
  loadEnv('.env.local')
}

loadEnv('.env.example')
