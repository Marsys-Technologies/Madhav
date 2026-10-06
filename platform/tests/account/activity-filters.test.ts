import { it, expect } from "vitest";
import { personalActivityFilters } from "@/lib/account/activity-filters";
it("carries the same applied owner filters to every activity request without an owner override", () => {
  const f = personalActivityFilters(
    new URLSearchParams(
      "from=2026-10-01T00:00:00Z&to=2026-10-02T00:00:00Z&channel=mcp&provider=openrouter&model=anthropic%2Fclaude&purpose=customer&connectionId=11111111-1111-4111-8111-111111111111&userId=bob&view=export",
    ),
    new Date("2026-10-03T12:00:00Z"),
  );
  expect(f.toString()).toBe(
    "from=2026-10-01T00%3A00%3A00Z&to=2026-10-02T00%3A00%3A00Z&channel=mcp&purpose=customer&provider=openrouter&model=anthropic%2Fclaude&connectionId=11111111-1111-4111-8111-111111111111",
  );
  expect(f.has("userId")).toBe(false);
});
it("rejects a reversed or over 90 day window rather than displaying mismatched data", () => {
  expect(() =>
    personalActivityFilters(
      new URLSearchParams("from=2026-10-02T00:00:00Z&to=2026-10-01T00:00:00Z"),
    ),
  ).toThrow();
  expect(() =>
    personalActivityFilters(
      new URLSearchParams("from=2026-01-01T00:00:00Z&to=2026-10-01T00:00:00Z"),
    ),
  ).toThrow();
});
