// PASS fixture — idiom 3 of 5. The argv-regex form the three shad_darshana gates use
// (citation_verify_gate.ts:270, completeness_census_seed.ts:687, specificity_gate_v0.ts:564).
// EXPECT-GUARD: argv-regex
async function main(): Promise<void> {
  console.log('a census gate')
}

if (process.argv[1] && /guarded_argv_regex\.(ts|js|mjs)$/.test(process.argv[1])) {
  main().catch(() => process.exit(1))
}
