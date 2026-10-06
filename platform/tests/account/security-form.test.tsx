import {
  render,
  screen,
  fireEvent,
  waitFor,
  cleanup,
} from "@testing-library/react";
import { it, expect, vi, beforeEach, afterEach } from "vitest";
const h = vi.hoisted(() => ({
  change: vi.fn(),
  finish: vi.fn(),
  signOut: vi.fn(),
  replace: vi.fn(),
}));
vi.mock("@/lib/account/password-flow", () => ({
  changeAccountPassword: h.change,
  finishAccountSecurity: h.finish,
  signOutAccountSessions: h.signOut,
}));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: h.replace, refresh: vi.fn() }),
}));
import { SecurityForm } from "@/components/account/SecurityForm";
beforeEach(() => vi.clearAllMocks());
afterEach(cleanup);
function enter(repeat = "new-fictional-password") {
  fireEvent.change(screen.getByLabelText("Current password"), {
    target: { value: "old-fictional-password" },
  });
  fireEvent.change(screen.getByLabelText("New password"), {
    target: { value: "new-fictional-password" },
  });
  fireEvent.change(screen.getByLabelText("Repeat new password"), {
    target: { value: repeat },
  });
}
it("does not submit mismatched passwords", () => {
  render(<SecurityForm />);
  enter("mismatch");
  fireEvent.click(
    screen.getByRole("button", {
      name: "Change password and sign out everywhere",
    }),
  );
  expect(h.change).not.toHaveBeenCalled();
});
it("shows a partial outcome, clears password fields, and retries only session revocation", async () => {
  h.change.mockResolvedValue({
    ownerId: "alice",
    changed: true,
    complete: false,
    error: "Password changed. Sign-out incomplete.",
  });
  h.finish.mockResolvedValue(true);
  render(<SecurityForm />);
  enter();
  fireEvent.click(
    screen.getByRole("button", {
      name: "Change password and sign out everywhere",
    }),
  );
  await waitFor(() =>
    expect(screen.getByRole("alert").textContent).toContain("Password changed"),
  );
  expect(
    (screen.getByLabelText("Current password") as HTMLInputElement).value,
  ).toBe("");
  fireEvent.click(screen.getByRole("button", { name: "Retry sign-out" }));
  await waitFor(() =>
    expect(h.replace).toHaveBeenCalledWith("/login?security=updated"),
  );
  expect(h.change).toHaveBeenCalledTimes(1);
  expect(h.finish).toHaveBeenCalledWith("alice");
});
it("recovery opens the request flow rather than an expired reset-code page", () => {
  render(<SecurityForm />);
  expect(
    screen.getByRole("link", { name: /Account Recovery/ }).getAttribute("href"),
  ).toBe("/login/recovery");
});
