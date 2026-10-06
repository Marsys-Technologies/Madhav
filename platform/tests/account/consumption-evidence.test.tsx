import {
  render,
  screen,
  fireEvent,
  waitFor,
  cleanup,
} from "@testing-library/react";
import { it, expect, vi, afterEach } from "vitest";
vi.mock("@/components/observatory/ObservatoryScope", () => ({
  useObservatoryScope: () => ({ users: [] }),
}));
import {
  Consumption,
  type Totals,
  type Conversation,
} from "@/components/observatory/ObservatoryDashboard";
const summary: Totals = {
  transport_attempts: 1,
  transport_success: 1,
  transport_failed: 0,
  transport_pending: 0,
  customer_attempts: 1,
  validation_attempts: 0,
  complete_usage: 1,
  transport_unpriced: 0,
  input_tokens: "10",
  output_tokens: "5",
  known_transport_cost_usd: "0.2",
  legacy_records: 0,
  legacy_estimate_usd: null,
  p50_success_ms: 1,
};
const row: Conversation = {
  key: "record",
  conversation_id: null,
  user_id: "alice",
  channel: "web",
  purpose: "customer",
  model: "fictional",
  first_at: "2026-10-01T00:00:00Z",
  last_at: "2026-10-01T00:00:01Z",
  turns: 1,
  attempts: 1,
  success: 1,
  incomplete_usage: 0,
  unpriced: 0,
  input_tokens: "10",
  output_tokens: "5",
  known_cost_usd: "0.2",
  snippet: "Fictional question",
};
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
it("keeps provider-reported receipt and calculated estimate separate in call details", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve(
        Response.json({
          events: [
            {
              id: "record",
              turn_id: "turn",
              operation_id: "operation",
              channel: "web",
              purpose: "customer",
              provider: "fixture",
              model: "fictional",
              role: "synthesizer",
              status: "success",
              aggregation: "transport",
              evidence: "metered",
              started_at: row.first_at,
              usage: { input: 10, output: 5, source: "provider" },
              computed_cost_usd: "0.2",
              provider_cost_usd: "0.1",
            },
          ],
        }),
      ),
    ),
  );
  render(
    <Consumption
      summary={summary}
      initial={{ conversations: [row], nextCursor: null }}
      baseUrl="/api/usage?from=2026-10-01T00%3A00%3A00Z&to=2026-10-02T00%3A00%3A00Z"
      portal={false}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: /Fictional question/ }));
  expect(
    await screen.findByText(
      "Provider-reported $0.1000 · calculated estimate $0.2000",
    ),
  ).toBeTruthy();
});
it("retains the pagination cursor and current records after a failed next page", async () => {
  const fetcher = vi.fn((_url: string) =>
    Promise.resolve(Response.json({}, { status: 503 })),
  );
  vi.stubGlobal("fetch", fetcher);
  render(
    <Consumption
      summary={summary}
      initial={{ conversations: [row], nextCursor: "fixture-cursor" }}
      baseUrl="/api/usage?channel=web"
      portal={false}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: "Show more activity" }));
  await screen.findByRole("alert");
  expect(screen.getByText("Fictional question")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Show more activity" }));
  await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2));
  expect(
    fetcher.mock.calls.every((c) =>
      String(c[0]).includes("cursor=fixture-cursor"),
    ),
  ).toBe(true);
});
