import {
  render,
  screen,
  fireEvent,
  waitFor,
  cleanup,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  AccountPreferencesProvider,
  useAccountPreferences,
} from "@/components/account/AccountPreferencesProvider";
import { TitleToggle, PageTitle } from "@/components/journey1/Titles";
function Controls() {
  const p = useAccountPreferences();
  return (
    <>
      <button onClick={() => void p!.update({ navPinned: true })}>Pin</button>
      <output>{String(p!.preferences.navPinned)}</output>
      <TitleToggle />
      <PageTitle name="account" />
    </>
  );
}
beforeEach(() => {
  localStorage.clear();
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
it("clears preferences and unsaved changes when the account owner changes", async () => {
  let owner = "alice";
  vi.stubGlobal(
    "fetch",
    vi.fn((_u, init?: RequestInit) =>
      Promise.resolve(
        init?.method === "PATCH"
          ? Response.json({}, { status: 503 })
          : Response.json({
              preferences: { navPinned: owner === "alice", titles: "en" },
            }),
      ),
    ),
  );
  const view = render(
    <AccountPreferencesProvider userId="alice">
      <Controls />
    </AccountPreferencesProvider>,
  );
  await waitFor(() => expect(screen.getByText("true")).toBeTruthy());
  fireEvent.click(screen.getByRole("button", { name: "Pin" }));
  await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
  owner = "bob";
  view.rerender(
    <AccountPreferencesProvider userId="bob">
      <Controls />
    </AccountPreferencesProvider>,
  );
  await waitFor(() => expect(screen.getByText("false")).toBeTruthy());
  expect(screen.queryByRole("alert")).toBeNull();
});
it("a delayed saved preference response cannot overwrite a newer click", async () => {
  let resolve!: (v: Response) => void;
  const get = new Promise<Response>((r) => (resolve = r));
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string, init?: RequestInit) =>
      init?.method === "PATCH"
        ? Promise.resolve(
            Response.json({ preferences: { navPinned: true, titles: "sa" } }),
          )
        : get,
    ),
  );
  render(
    <AccountPreferencesProvider userId="alice">
      <Controls />
    </AccountPreferencesProvider>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Pin" }));
  resolve(Response.json({ preferences: { navPinned: false, titles: "en" } }));
  await waitFor(() => expect(screen.getByText("true")).toBeTruthy());
  await waitFor(() =>
    expect(screen.getByRole("heading").textContent).toContain("My Account"),
  );
});
it("header title choice and account setting use one value", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve(Response.json({ preferences: { titles: "en" } })),
    ),
  );
  render(
    <AccountPreferencesProvider userId="alice">
      <Controls />
    </AccountPreferencesProvider>,
  );
  await waitFor(() =>
    expect(
      screen.getByRole("button", { name: "Show page titles in Sanskrit" }),
    ).toBeTruthy(),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Show page titles in Sanskrit" }),
  );
  expect(
    screen.getByRole("button", { name: "Show page titles in English" }),
  ).toBeTruthy();
});
it("reports a failed save while retaining the user choice", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((_u, init?: RequestInit) =>
      Promise.resolve(
        init?.method === "PATCH"
          ? Response.json({}, { status: 503 })
          : Response.json({ preferences: {} }),
      ),
    ),
  );
  render(
    <AccountPreferencesProvider userId="alice">
      <Controls />
    </AccountPreferencesProvider>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Pin" }));
  await waitFor(() =>
    expect(screen.getByRole("alert").textContent).toContain("not saved"),
  );
  expect(screen.getByText("true")).toBeTruthy();
});
it("retry saves only outstanding changes and clears the failure once they are saved", async () => {
  let fail = true;
  const f = vi.fn((_u, init?: RequestInit) =>
    Promise.resolve(
      init?.method === "PATCH" && fail
        ? Response.json({}, { status: 503 })
        : Response.json({ preferences: { titles: "sa", navPinned: false } }),
    ),
  );
  vi.stubGlobal("fetch", f);
  render(
    <AccountPreferencesProvider userId="alice">
      <Controls />
    </AccountPreferencesProvider>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Pin" }));
  await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
  fail = false;
  fireEvent.click(screen.getByRole("button", { name: "Retry" }));
  await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
  fireEvent.click(
    screen.getByRole("button", { name: "Show page titles in English" }),
  );
  await waitFor(() =>
    expect(f.mock.calls.filter((c) => c[1]?.method === "PATCH")).toHaveLength(
      3,
    ),
  );
  expect(
    f.mock.calls.filter((c) => c[1]?.method === "PATCH").at(-1)?.[1]?.body,
  ).toBe('{"titles":"en"}');
});
it("retrying a failed title change does not resubmit an earlier successfully saved pin", async () => {
  let attempt = 0;
  const f = vi.fn((_u, init?: RequestInit) => {
    if (init?.method !== "PATCH")
      return Promise.resolve(Response.json({ preferences: { titles: "sa" } }));
    attempt++;
    return Promise.resolve(
      attempt === 2
        ? Response.json({}, { status: 503 })
        : Response.json({
            preferences: {
              titles: attempt === 1 ? "sa" : "en",
              navPinned: true,
            },
          }),
    );
  });
  vi.stubGlobal("fetch", f);
  render(
    <AccountPreferencesProvider userId="alice">
      <Controls />
    </AccountPreferencesProvider>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Pin" }));
  await waitFor(() =>
    expect(f.mock.calls.filter((c) => c[1]?.method === "PATCH")).toHaveLength(
      1,
    ),
  );
  await waitFor(() => expect(screen.getByText("true")).toBeTruthy());
  fireEvent.click(
    screen.getByRole("button", { name: "Show page titles in English" }),
  );
  await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
  fireEvent.click(screen.getByRole("button", { name: "Retry" }));
  await waitFor(() =>
    expect(f.mock.calls.filter((c) => c[1]?.method === "PATCH")).toHaveLength(
      3,
    ),
  );
  expect(f.mock.calls.at(-1)?.[1]?.body).toBe('{"titles":"en"}');
});
