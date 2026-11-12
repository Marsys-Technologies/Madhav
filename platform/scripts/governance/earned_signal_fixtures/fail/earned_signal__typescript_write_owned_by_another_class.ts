// EXPECT-VIOLATIONS: 1
class FrozenSummary {
  private lintLeaksTotal = 0
  value() { return this.lintLeaksTotal }
}
class MeasuredSummary {
  private lintLeaksTotal = 0
  private deltaCalls = 0
  private fires = 0
  observe(count: number): void {
    this.deltaCalls += 1
    if (count > 0) {
      this.fires += 1
      this.lintLeaksTotal += count
    }
  }
}

export { FrozenSummary, MeasuredSummary }
