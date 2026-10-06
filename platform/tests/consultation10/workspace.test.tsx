import { beforeEach, afterEach, describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import {
  DockControllerProvider,
  useDockController,
} from "@/components/pariprashna/dock/DockController";
import { RightDock } from "@/components/pariprashna/dock/RightDock";
import { WorkspacePanel } from "@/components/pariprashna/dock/WorkspacePanel";
import { ConsultationHistory } from "@/components/pariprashna/history/ConsultationHistory";
import { Composer } from "@/components/pariprashna/composer/Composer";
function Controls() {
  const c = useDockController();
  return (
    <>
      <output data-testid="state">{`${c.open}/${c.leftOpen}/${c.pinned}/${c.placement}`}</output>
      <button onClick={() => c.setOpen(true)}>Expand</button>
      <button onClick={() => c.setPinned(!c.pinned)}>Pin</button>
    </>
  );
}
beforeEach(() => {
  localStorage.clear();
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  );
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
describe("Consultation review 10 workspace", () => {
  it("opens only pinned panels on return, isolates preferences by user, and does not save transient expansion", () => {
    const view = render(
      <DockControllerProvider userId="a">
        <Controls />
      </DockControllerProvider>,
    );
    expect(screen.getByTestId("state")).toHaveTextContent(
      "false/false/false/pane",
    );
    fireEvent.click(screen.getByText("Expand"));
    expect(localStorage.getItem("madhav.pref.consultation.a")).toBeNull();
    fireEvent.click(screen.getByText("Pin"));
    view.unmount();
    const returning = render(
      <DockControllerProvider userId="a">
        <Controls />
      </DockControllerProvider>,
    );
    expect(screen.getByTestId("state")).toHaveTextContent(
      "true/false/true/pane",
    );
    returning.unmount();
    render(
      <DockControllerProvider userId="b">
        <Controls />
      </DockControllerProvider>,
    );
    expect(screen.getByTestId("state")).toHaveTextContent(
      "false/false/false/pane",
    );
  });
  it("has exactly three evidence tabs and keyboard navigation", () => {
    render(
      <DockControllerProvider defaultOpen>
        <RightDock turns={[]} />
      </DockControllerProvider>,
    );
    expect(screen.getAllByRole("tab").map((t) => t.textContent)).toEqual([
      "Grounding",
      "Windows",
      "History",
    ]);
    fireEvent.keyDown(screen.getByRole("tab", { name: "Grounding" }), {
      key: "ArrowRight",
    });
    expect(screen.getByRole("tab", { name: "Windows" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByText(/Computed activation windows/)).toBeVisible();
  });
  it("changes grounding placement below the composer and persists it without altering AI controls", () => {
    render(
      <DockControllerProvider userId="a">
        <Controls />
        <Composer streaming={false} onSubmit={vi.fn()} onStop={vi.fn()} />
      </DockControllerProvider>,
    );
    fireEvent.change(screen.getByLabelText("Grounding placement"), {
      target: { value: "inline" },
    });
    expect(screen.getByTestId("state")).toHaveTextContent("/inline");
    expect(
      JSON.parse(localStorage.getItem("madhav.pref.consultation.a")!),
    ).toMatchObject({ placement: "inline" });
    expect(screen.getByRole("button", { name: "Ask" })).toBeDisabled();
  });
  it("filters tagged answers and opens the exact answer, while correction history stays a link", () => {
    const select = vi.fn();
    render(
      <ConsultationHistory
        threads={[
          {
            id: "one",
            chartId: "chart",
            chartName: "Native",
            title: "Career",
            updatedAtMs: 1,
            active: false,
            streaming: false,
            tagged: true,
            taggedAnswers: [],
          },
          {
            id: "two",
            chartId: "chart",
            chartName: "Native",
            title: "Travel",
            updatedAtMs: 2,
            active: false,
            streaming: false,
            taggedAnswers: [{ id: "answer", text: "A real saved answer" }],
          },
          {
            id: "old",
            chartId: "chart",
            chartName: "Native",
            title: "Historical",
            updatedAtMs: 0,
            active: false,
            streaming: false,
            href: "/read-only",
          },
        ]}
        onSelect={select}
        onNew={vi.fn()}
        disabled={false}
        loading={false}
        error={null}
        onRetry={vi.fn()}
      />,
    );
    expect(screen.getByRole("link", { name: /Historical/ })).toHaveAttribute(
      "href",
      "/read-only",
    );
    fireEvent.change(screen.getByLabelText("Filter history"), {
      target: { value: "answers" },
    });
    expect(screen.queryByText("Career")).toBeNull();
    fireEvent.click(
      screen.getByRole("button", { name: /A real saved answer/ }),
    );
    expect(select).toHaveBeenCalledWith("two", "answer");
  });
  it("keeps mobile panels closed even when pinned, and exposes a dismissible dialog on demand", () => {
    vi.stubGlobal(
      "matchMedia",
      vi.fn(() => ({
        matches: true,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })),
    );
    localStorage.setItem(
      "madhav.pref.consultation.a",
      JSON.stringify({ rightPinned: true }),
    );
    render(
      <DockControllerProvider userId="a">
        <WorkspacePanel side="right" title="Evidence">
          <button>Inside</button>
        </WorkspacePanel>
      </DockControllerProvider>,
    );
    expect(screen.queryByRole("dialog")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Open evidence" }));
    expect(screen.getByRole("dialog", { name: "Evidence" })).toHaveAttribute(
      "aria-modal",
      "true",
    );
    fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
