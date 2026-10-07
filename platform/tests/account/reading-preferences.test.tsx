import {
  render,
  screen,
  fireEvent,
  waitFor,
  cleanup,
  act,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { AccountPreferencesProvider } from "@/components/account/AccountPreferencesProvider";
import { Composer } from "@/components/pariprashna/composer/Composer";
import {
  DockControllerProvider,
  useDockController,
} from "@/components/pariprashna/dock/DockController";
function Pins() {
  const d = useDockController();
  return (
    <>
      <output>{JSON.stringify([d.pinned, d.leftPinned, d.placement])}</output>
      <button onClick={() => d.setPinned(false)}>Release evidence</button>
    </>
  );
}
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
});
it("loads separate dock pins and placement from account settings and saves a pin change", async () => {
  const fetcher = vi.fn((_u, init?: RequestInit) =>
    Promise.resolve(
      Response.json({
        preferences:
          init?.method === "PATCH"
            ? {
                evidencePinned: false,
                historyPinned: true,
                grounding: "inline",
              }
            : {
                evidencePinned: true,
                historyPinned: true,
                grounding: "inline",
              },
      }),
    ),
  );
  vi.stubGlobal("fetch", fetcher);
  render(
    <AccountPreferencesProvider userId="alice">
      <DockControllerProvider userId="alice">
        <Pins />
      </DockControllerProvider>
    </AccountPreferencesProvider>,
  );
  await waitFor(() =>
    expect(screen.getByText('[true,true,"inline"]')).toBeTruthy(),
  );
  fireEvent.click(screen.getByText("Release evidence"));
  expect(screen.getByText('[false,true,"inline"]')).toBeTruthy();
  await waitFor(() =>
    expect(fetcher).toHaveBeenCalledWith(
      "/api/account/preferences",
      expect.objectContaining({
        method: "PATCH",
        body: '{"evidencePinned":false}',
      }),
    ),
  );
});
it("starts Deep by default and sends the supported deep_dive wire value", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      Promise.resolve(
        Response.json(
          url === "/api/personas" ? { personas: [] } : { preferences: {} },
        ),
      ),
    ),
  );
  const submit = vi.fn();
  await act(async () => {
    render(
      <AccountPreferencesProvider userId="alice">
        <Composer streaming={false} onSubmit={submit} onStop={() => {}} />
      </AccountPreferencesProvider>,
    );
  });
  expect(screen.getByRole("button", { name: /Depth.*Deep/ })).toBeTruthy();
  fireEvent.change(screen.getByLabelText("Ask the chart"), {
    target: { value: "A fictional question" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Ask" }));
  expect(submit.mock.calls[0][2].readingDepth).toBe("deep_dive");
});
it("a late account depth does not replace the user’s newer depth choice", async () => {
  let resolve!: (v: Response) => void;
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      url === "/api/personas"
        ? Promise.resolve(Response.json({ personas: [] }))
        : new Promise<Response>((r) => (resolve = r)),
    ),
  );
  render(
    <AccountPreferencesProvider userId="alice">
      <Composer streaming={false} onSubmit={() => {}} onStop={() => {}} />
    </AccountPreferencesProvider>,
  );
  fireEvent.click(screen.getByRole("button", { name: /Depth/ }));
  fireEvent.click(screen.getByRole("option", { name: /Quick/ }));
  resolve(Response.json({ preferences: { readingDepth: "deep" } }));
  await waitFor(() =>
    expect(screen.getByRole("button", { name: /Depth.*Quick/ })).toBeTruthy(),
  );
});
