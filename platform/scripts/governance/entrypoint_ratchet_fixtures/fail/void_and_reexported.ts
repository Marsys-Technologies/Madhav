// FAIL fixture — `void main()` / `await main()` spellings. ADHIKĀRIN's own D-67 part 1 pattern
// missed exactly these two forms and undercounted the caller set by two files (ruling D-71
// part 1), so they are pinned here by name.
// EXPECT-VIOLATIONS: 1
export async function main(): Promise<void> {
  console.log('drains an outbox against a live pool')
}

void main()
