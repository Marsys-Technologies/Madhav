import { render, screen, waitFor, cleanup } from "@testing-library/react";
import { it, expect, vi, afterEach } from "vitest";
const mocks = vi.hoisted(() => ({
  replace: vi.fn(),
  query:
    "from=2026-10-01T00:00:00Z&to=2026-10-02T00:00:00Z&channel=mcp&provider=openrouter&model=anthropic%2Fclaude&connectionId=11111111-1111-4111-8111-111111111111",
}));
vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(mocks.query),
  usePathname: () => "/account/ai-cockpit/observatory",
  useRouter: () => ({ replace: mocks.replace }),
}));
vi.mock("@/components/observatory/ObservatoryScope", () => ({
  useObservatoryScope: () => ({
    userId: "alice",
    users: [],
    admin: true,
    endpoint: "/api/admin/observatory/metering",
  }),
}));
vi.mock("@/components/account/useAiAccountState", () => ({
  useAiAccountState: () => ({
    state: undefined,
    clis: [],
    loading: false,
    error: false,
  }),
}));
import { PersonalActivity } from "@/components/account/PersonalActivity";
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
it("uses identical personal filters for summary, daily graph and connection hierarchy even for a system administrator", async () => {
  const urls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn((u: string) => {
      urls.push(u);
      return Promise.resolve(
        Response.json(
          u.includes("view=summary")
            ? {
                transport_attempts: 2,
                transport_success: 1,
                cli_executions: 3,
                transport_pending: 0,
                p50_success_ms: null,
                provider_transport_cost_usd: null,
                known_transport_cost_usd: "0.02",
                transport_unpriced: 1,
                legacy_records: 0,
              }
            : { groups: [] },
        ),
      );
    }),
  );
  render(<PersonalActivity view="observatory" />);
  await screen.findByText("Successful API calls");
  await waitFor(() => expect(urls).toHaveLength(3));
  for (const url of urls) {
    const q = new URL(url, "http://localhost");
    expect(q.pathname).toBe("/api/usage");
    expect(q.searchParams.get("channel")).toBe("mcp");
    expect(q.searchParams.get("connectionId")).toBe(
      "11111111-1111-4111-8111-111111111111",
    );
    expect(q.searchParams.get("model")).toBe("anthropic/claude");
    expect(q.searchParams.has("userId")).toBe(false);
  }
  expect(screen.getByText("API calls")).toBeTruthy();
  expect(screen.getByText("CLI executions")).toBeTruthy();
  expect(screen.getByText("Provider-reported cost")).toBeTruthy();
  expect(screen.getAllByText("Not reported").length).toBeGreaterThan(0);
});
it("does not issue a request for an invalid saved period", async () => {
  const saved = mocks.query;
  mocks.query = "from=2026-10-02T00:00:00Z&to=2026-10-01T00:00:00Z";
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  render(<PersonalActivity view="consumption" />);
  expect(screen.getByRole("alert").textContent).toContain("period");
  expect(fetch).not.toHaveBeenCalled();
  mocks.query = saved;
});
