// PASS fixture — idiom 5 of 5, AND D-71 part 7(d)'s second named case: "a same-line-guarded
// main() must stay green". THREE files in this tree carry exactly this shape
// (audit/tap/sc_pointer_validation.ts:416, ci/migration_number_guard.ts:439,
// generate_signal_glossary_mirror.ts:164). Their `main()` sits at neither column 0 nor line
// start, so they appear in NEITHER the 86 NOR the 76 — no line-anchored pattern can see them.
// A detector that is not aware of them reports three correctly-guarded files as violations.
// EXPECT-GUARD: require.main===module
async function main(): Promise<void> {
  console.log('guarded on one line')
}

if (require.main === module) void main()
