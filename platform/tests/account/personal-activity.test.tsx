import {
  render,
  screen,
  waitFor,
  cleanup,
  fireEvent,
} from "@testing-library/react";
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

it.each(["transport", "legacy_aggregate"])(
  "never requests CLI details outside selected %s source",
  async (aggregation) => {
    const saved = mocks.query;
    mocks.query = saved + "&aggregation=" + aggregation;
    const urls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        urls.push(url);
        return Promise.resolve(
          Response.json(
            url.includes("view=summary")
              ? {
                  transport_attempts: 1,
                  transport_success: 1,
                  cli_executions: 0,
                  legacy_records: 1,
                }
              : url.includes("view=conversations")
                ? { conversations: [], nextCursor: "next-page" }
                : { groups: [], events: [], nextCursor: "next-page" },
          ),
        );
      }),
    );
    try {
      render(<PersonalActivity view="consumption" />);
      await screen.findByRole("button", { name: "Show more activity" });
      fireEvent.click(
        screen.getByRole("button", { name: "Show more activity" }),
      );
      await waitFor(() =>
        expect(urls.some((u) => u.includes("cursor="))).toBe(true),
      );
      expect(
        urls.some((u) =>
          new URL(u, "http://local").searchParams
            .getAll("aggregation")
            .includes("cli_aggregate"),
        ),
      ).toBe(false);
      expect(
        screen.queryByRole("button", { name: "Show more CLI executions" }),
      ).toBeNull();
    } finally {
      mocks.query = saved;
    }
  },
);
