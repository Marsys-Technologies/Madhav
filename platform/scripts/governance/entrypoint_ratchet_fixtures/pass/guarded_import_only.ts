// PASS fixture — idiom 2 of 5. The OPPOSITE contract, and it is right for a CI gate: a gate's
// hazard is FAILING to run, so its safe default is RUN and the opt-out is explicit
// (M0-T50 / ruling D-49, scripts/audit/A3_env_matrix.md Addendum A3.4). The ratchet must accept
// both contracts or it would push gates toward the wrong default.
// EXPECT-GUARD: IMPORT_ONLY
async function main(): Promise<void> {
  console.log('a CI gate that must run')
}

if (process.env.IMPORT_ONLY !== '1') {
  main().catch(() => process.exit(1))
}
