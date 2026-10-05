import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
const state = vi.hoisted(() => ({ path: "/clients/chart-test" }));
vi.mock("next/navigation", () => ({
  usePathname: () => state.path,
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}));
vi.mock("next/link", () => ({
  default: ({
    children,
    href,
    ...rest
  }: React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));
import { JourneyShell } from "@/components/journey1/JourneyShell";
const props = {
  user: { uid: "fictional" },
  role: "super_admin",
  chartId: "chart-test",
  fallback: <main>Existing consultation shell</main>,
};
beforeEach(() => {
  localStorage.clear();
  state.path = "/clients/chart-test";
});
describe("Journey 1 shared navigation", () => {
  it("starts collapsed, expands on focus, and persists a pin independently of hover", () => {
    const { container } = render(
      <JourneyShell {...props}>Chart overview</JourneyShell>,
    );
    const nav = screen.getByRole("navigation", { name: "Primary navigation" });
    expect(nav).toHaveAttribute("data-open", "false");
    fireEvent.focus(within(nav).getByRole("link", { name: "Birth Charts" }));
    expect(nav).toHaveAttribute("data-open", "true");
    fireEvent.click(
      screen.getByRole("button", { name: "Pin navigation open" }),
    );
    expect(localStorage.getItem("madhav.pref.global-nav-pinned")).toBe("true");
    expect(container.querySelector(".j1-rail-space")).toHaveAttribute(
      "data-pinned",
      "true",
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Release navigation pin" }),
    );
    expect(localStorage.getItem("madhav.pref.global-nav-pinned")).toBe("false");
  });
  it("keeps icon links accessible without the retired global destinations", () => {
    render(<JourneyShell {...props}>Chart overview</JourneyShell>);
    const nav = screen.getByRole("navigation", { name: "Primary navigation" });
    expect(within(nav).getByRole("link", { name: "Atlas" })).toHaveAttribute(
      "href",
      "/information/atlas",
    );
    expect(
      within(nav).queryByRole("link", {
        name: /audit|performance|cockpit|almanac/i,
      }),
    ).toBeNull();
  });
  it("can enter and leave deferred workflows without changing hook order", () => {
    const view = render(<JourneyShell {...props}>Chart overview</JourneyShell>);
    state.path = "/clients/chart-test/pariprashna";
    view.rerender(<JourneyShell {...props}>Chart overview</JourneyShell>);
    expect(screen.getByText("Chart overview")).toBeInTheDocument();
    expect(screen.queryByText("Existing consultation shell")).toBeNull();
    state.path = "/clients/chart-test/samiksha";
    view.rerender(<JourneyShell {...props}>Prediction review</JourneyShell>);
    expect(screen.getByText("Existing consultation shell")).toBeInTheDocument();
    state.path = "/clients/chart-test/edit";
    view.rerender(<JourneyShell {...props}>Chart details</JourneyShell>);
    expect(screen.getByText("Chart details")).toBeInTheDocument();
    expect(screen.queryByText("Existing consultation shell")).toBeNull();
  });
});
