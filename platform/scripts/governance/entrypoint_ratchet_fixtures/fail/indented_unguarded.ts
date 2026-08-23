// FAIL fixture — D-71 part 7(d), NAMED IN THE RULING: "an INDENTED unguarded main() must go
// red". Indentation is not a guard, and a column-0 grep — the pattern that produced the 76 —
// cannot see this at all. A ratchet that stays green here admits exactly what it was built to
// catch, silently and permanently.
// EXPECT-VIOLATIONS: 2
async function main(): Promise<void> {
  console.log('runs on import, twice over')
}

if (process.env.FORCE) {
  main()
}

try {
  await main()
} catch {
  process.exit(1)
}
