// EXPECT-VIOLATIONS: 1
class FrozenSummary {
  private trap2_narration_leak_count = 0;
  /*
  observe(count: number): void {
    this.all += 1
    if (count > 0) {
      this.flagged += 1
      this.trap2_narration_leak_count += count
    }
  }
  */
  value() { return this.trap2_narration_leak_count }
}

export { FrozenSummary }
