import { beforeEach, it, expect, vi } from "vitest";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  cleanup,
} from "@testing-library/react";
import { PageTitle, TitleToggle } from "@/components/journey1/Titles";
import { VargaChart } from "@/components/journey1/VargaChart";
import {
  RecoveryForm,
  RECOVERY_SUCCESS,
} from "@/components/auth/ForgotPasswordModal";
import { RequestAccessForm } from "@/components/auth/RequestAccessModal";
const empty = {
  chartId: "test",
  isEmpty: true,
  lagnaSign: "",
  lagnaDegreeDms: "",
  houses: [],
  topYogas: [],
  currentDasha: null,
};
beforeEach(() => {
  cleanup();
  localStorage.clear();
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(new Response('{"ok":true}')),
  );
});
it("toggles title prominence consistently, preserving body content and the saved preference", () => {
  render(
    <>
      <TitleToggle />
      <PageTitle name="charts" />
      <PageTitle name="overview" />
      <p>Unchanged chart data</p>
    </>,
  );
  expect(
    screen.getByRole("heading", { name: "Jātakas Birth Charts" }),
  ).toBeTruthy();
  fireEvent.click(
    screen.getByRole("button", { name: "Show page titles in English" }),
  );
  expect(
    screen.getByRole("heading", { name: "Birth Charts Jātakas" }),
  ).toBeTruthy();
  expect(
    screen.getByRole("heading", { name: "Chart Overview Jātaka Darśana" }),
  ).toBeTruthy();
  expect(localStorage.getItem("madhav.pref.titles")).toBe("en");
  expect(screen.getByText("Unchanged chart data")).toBeTruthy();
});
it("switches both the slider and labelled controls across all three charts without substituting D1", () => {
  render(<VargaChart charts={[empty, empty, empty]} ayanamsha="raman" />);
  fireEvent.change(screen.getByRole("slider"), { target: { value: "2" } });
  expect(screen.getByRole("img").getAttribute("aria-label")).toContain("D10");
  fireEvent.click(screen.getByRole("button", { name: "D9 · Navāṃśa" }));
  expect(screen.getByRole("img").getAttribute("aria-label")).toContain("D9");
  expect(screen.getByRole("slider").getAttribute("aria-valuetext")).toBe(
    "D9 · Navāṃśa",
  );
});
it("accepts a username in recovery and displays the generic response", async () => {
  render(<RecoveryForm />);
  fireEvent.change(screen.getByLabelText("Username or email"), {
    target: { value: "fictional_native" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Send reset link" }));
  await waitFor(() =>
    expect(screen.getByRole("status").textContent).toBe(RECOVERY_SUCCESS),
  );
  expect(JSON.parse(vi.mocked(fetch).mock.calls[0][1]!.body as string)).toEqual(
    { identifier: "fictional_native" },
  );
});
it("request access does not ask for or reserve a username", () => {
  render(<RequestAccessForm />);
  expect(screen.queryByLabelText(/^Username/)).toBeNull();
  expect(screen.getByLabelText("Full name")).toBeTruthy();
  expect(screen.getByLabelText("Email")).toBeTruthy();
});
