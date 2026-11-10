import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, within, waitFor } from "@testing-library/react";
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
import { AppShellBreadcrumb } from "@/components/shared/AppShellBreadcrumb";
const props = {
  user: { uid: "fictional" },
  role: "super_admin",
  chartId: "chart-test",
  fallback: <main>Existing consultation shell</main>,
};
beforeEach(() => {
  localStorage.clear();
  vi.stubGlobal("fetch",vi.fn((_url,init?:RequestInit)=>Promise.resolve(Response.json({preferences:{...(init?.body?JSON.parse(String(init.body)):{})}}))));
  state.path = "/clients/chart-test";
});
afterEach(()=>vi.unstubAllGlobals());
describe("Journey 1 shared navigation", () => {
  it("starts collapsed, expands on focus, and persists a pin independently of hover", async () => {
    const { container } = render(
      <JourneyShell {...props}>Chart overview</JourneyShell>,
    );
    const nav = screen.getByRole("navigation", { name: "Primary navigation" });
    expect(nav).toHaveAttribute("data-open", "false");
    fireEvent.focus(within(nav).getByRole("link", { name: "Birth Charts" }));
    expect(nav).toHaveAttribute("data-open", "true");
    fireEvent.mouseLeave(nav);
    expect(nav).toHaveAttribute("data-open", "true");
    fireEvent.click(
      screen.getByRole("button", { name: "Pin navigation open" }),
    );
    await waitFor(()=>expect(fetch).toHaveBeenCalledWith("/api/account/preferences",expect.objectContaining({method:"PATCH",body:JSON.stringify({navPinned:true})})));
    expect(container.querySelector(".j1-rail-space")).toHaveAttribute(
      "data-pinned",
      "true",
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Release navigation pin" }),
    );
    await waitFor(()=>expect(fetch).toHaveBeenCalledWith("/api/account/preferences",expect.objectContaining({method:"PATCH",body:JSON.stringify({navPinned:false})})));
  });
  it("keeps icon links accessible without the retired global destinations", () => {
    render(<JourneyShell {...props}>Chart overview</JourneyShell>);
    const nav = screen.getByRole("navigation", { name: "Primary navigation" });
    expect(within(nav).getByRole("link", { name: "Birth Charts" })).toHaveAttribute("aria-current", "location");
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
  it("makes the background inert while mobile navigation is open and restores focus on Escape", async () => {
    await act(async () => render(<JourneyShell {...props}>Chart overview</JourneyShell>));
    const opener = screen.getByRole("button", { name: "Open navigation" });
    opener.focus();
    fireEvent.click(opener);

    const nav = screen.getByRole("navigation", { name: "Primary navigation" });
    expect(opener.closest(".j1-shell-body")).toHaveAttribute("inert");
    expect(within(nav).getByRole("button", { name: "Close navigation" })).toHaveFocus();

    fireEvent.keyDown(nav, { key: "Escape" });
    expect(opener.closest(".j1-shell-body")).not.toHaveAttribute("inert");
    expect(opener).toHaveFocus();
  });
  it("keeps Consultation and Prediction Review in the chart workspace", async () => {
    state.path = "/clients/chart-test/pariprashna";
    const view = await act(async () =>
      render(<JourneyShell {...props}>Consultation</JourneyShell>),
    );
    expect(screen.getByTestId("chart-page-frame")).toHaveAttribute("data-workspace", "consultation");
    expect(screen.getByRole("main")).toHaveTextContent("Consultation");

    state.path = "/clients/chart-test/samiksha";
    view.rerender(<JourneyShell {...props}>Prediction review</JourneyShell>);
    expect(screen.getByTestId("chart-page-frame")).toHaveAttribute("data-chart-id", "chart-test");
    expect(screen.getByTestId("chart-page-frame")).not.toHaveAttribute("data-workspace");
    expect(screen.getByRole("main")).toHaveTextContent("Prediction review");
    expect(screen.getByRole("navigation", { name: "Primary navigation" })).toBeInTheDocument();
  });
  it("can enter and leave a saved legacy consultation without changing hook order", async () => {
    const view = await act(async () =>
      render(<JourneyShell {...props}>Chart overview</JourneyShell>),
    );
    state.path = "/clients/chart-test/consult/saved-reading";
    view.rerender(<JourneyShell {...props}>Saved reading</JourneyShell>);
    expect(screen.getByText("Existing consultation shell")).toBeInTheDocument();
    expect(screen.queryByRole("navigation", { name: "Primary navigation" })).toBeNull();

    state.path = "/clients/chart-test/edit";
    view.rerender(<JourneyShell {...props}>Chart details</JourneyShell>);
    expect(screen.getByRole("main")).toHaveTextContent("Chart details");
    expect(screen.getByRole("navigation", { name: "Primary navigation" })).toBeInTheDocument();
  });
});

describe("AppShell breadcrumbs", () => {
  it("gives the breadcrumb and mobile navigation separate semantics", () => {
    render(<AppShellBreadcrumb
      mobileNav={<button>Open navigation menu</button>}
      segments={[{ label: "Birth Charts", href: "/dashboard" }, { label: "Sample chart", current: true }]}
    />);

    const breadcrumb = screen.getByRole("navigation", { name: "Breadcrumb" });
    expect(within(breadcrumb).getByRole("link", { name: "Birth Charts" })).toHaveAttribute("href", "/dashboard");
    expect(within(breadcrumb).getByText("Sample chart")).toHaveAttribute("aria-current", "page");
    expect(breadcrumb).not.toContainElement(screen.getByRole("button", { name: "Open navigation menu" }));
  });

  it("keeps the mobile menu reachable without a breadcrumb", () => {
    render(<AppShellBreadcrumb mobileNav={<button>Open navigation menu</button>} segments={[]} />);
    expect(screen.getByRole("button", { name: "Open navigation menu" })).toBeInTheDocument();
    expect(screen.queryByRole("navigation", { name: "Breadcrumb" })).not.toBeInTheDocument();
  });
});
