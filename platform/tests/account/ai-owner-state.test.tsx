import { render, screen, waitFor, cleanup, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { it, expect, vi, afterEach } from "vitest";
import { AccountPreferencesProvider } from "@/components/account/AccountPreferencesProvider";
import { useAiAccountState } from "@/components/account/useAiAccountState";
function Snapshot() {
  const s = useAiAccountState();
  return <output>{s.state?.connections[0]?.name ?? "Loading"}</output>;
}
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
it("never shows a previous owner’s cached AI connection while a new owner loads", async () => {
  const cache = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  let bob = false,
    resolve!: (v: Response) => void;
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      if (url.includes("preferences"))
        return Promise.resolve(Response.json({ preferences: {} }));
      if (url.includes("clis"))
        return Promise.resolve(Response.json({ clis: [] }));
      if (bob) return new Promise<Response>((r) => (resolve = r));
      return Promise.resolve(
        Response.json({
          connections: [{ name: "Alice private connection" }],
          configurations: [],
          defaultChoice: null,
        }),
      );
    }),
  );
  const tree = (owner: string) => (
    <QueryClientProvider client={cache}>
      <AccountPreferencesProvider userId={owner}>
        <Snapshot />
      </AccountPreferencesProvider>
    </QueryClientProvider>
  );
  const view = render(tree("alice"));
  await waitFor(() =>
    expect(screen.getByText("Alice private connection")).toBeTruthy(),
  );
  bob = true;
  view.rerender(tree("bob"));
  expect(screen.queryByText("Alice private connection")).toBeNull();
  await act(async () => {
    resolve(
      Response.json({
        connections: [{ name: "Bob connection" }],
        configurations: [],
        defaultChoice: null,
      }),
    );
  });
  await waitFor(() => expect(screen.getByText("Bob connection")).toBeTruthy());
});
