import {
  render,
  screen,
  fireEvent,
  waitFor,
  cleanup,
} from "@testing-library/react";
import { afterEach, it, expect, vi } from "vitest";
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh: vi.fn() }) }));
import { ProfileForm } from "@/components/account/ProfileForm";
const initial = {
  name: "Alice",
  email: "alice@example.test",
  username: "alice",
};
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
it("shows immutable email and retains a name when saving fails", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(Response.json({}, { status: 503 }))),
  );
  render(<ProfileForm initial={initial} />);
  expect((screen.getByLabelText("E-mail") as HTMLInputElement).readOnly).toBe(
    true,
  );
  fireEvent.change(screen.getByLabelText("Name"), {
    target: { value: "New Alice" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Save profile" }));
  await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
  expect((screen.getByLabelText("Name") as HTMLInputElement).value).toBe(
    "New Alice",
  );
});
it("reports a partial save honestly if username succeeds but name fails", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      Promise.resolve(
        url.includes("?")
          ? Response.json({ available: true })
          : url.endsWith("/username")
            ? Response.json({ ok: true })
            : Response.json({}, { status: 503 }),
      ),
    ),
  );
  render(<ProfileForm initial={initial} />);
  fireEvent.change(screen.getByLabelText("Username"), {
    target: { value: "alice-new" },
  });
  fireEvent.change(screen.getByLabelText("Name"), {
    target: { value: "New Alice" },
  });
  await waitFor(() => expect(screen.getByText("Available")).toBeTruthy());
  fireEvent.click(screen.getByRole("button", { name: "Save profile" }));
  await waitFor(() =>
    expect(screen.getByRole("alert").textContent).toContain("Username saved"),
  );
  expect((screen.getByLabelText("Name") as HTMLInputElement).value).toBe(
    "New Alice",
  );
});
