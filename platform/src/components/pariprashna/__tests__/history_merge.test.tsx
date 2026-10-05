/** Review 10 closes the previously visible-but-not-openable history gap. */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  render,
  screen,
  cleanup,
  fireEvent,
  waitFor,
} from "@testing-library/react";
import type { ThreadState } from "../state/types";
import { makeInitialTurnState } from "../state/reducer";
vi.mock("../Transcript", () => ({ Transcript: () => null }));
vi.mock("../composer/Composer", () => ({
  Composer: ({ disabled }: { disabled: boolean }) => (
    <button disabled={disabled}>Composer</button>
  ),
}));
vi.mock("../overlay/OverlayLayer", () => ({ OverlayLayer: () => null }));
vi.mock("../hooks/useVisualViewport", () => ({
  useVisualViewport: () => ({ supported: false, height: null }),
}));
const { live, restore } = vi.hoisted(() => ({
  restore: vi.fn(),
  live: vi.fn(),
}));
vi.mock("../hooks/useLiveStream", () => ({ useLiveStream: live }));
import { PariprashnaApp } from "../PariprashnaApp";
const PIN = { name: "Native", bornLine: "Birth data" },
  chart = "chart-1";
const row = (id: string, title: string, extra = {}) => ({
  id,
  title,
  chart_id: chart,
  created_at: "2026-10-01T00:00:00Z",
  updated_at: null,
  archived_at: null,
  archive_reason: null,
  tagged: false,
  tagged_answers: [],
  ...extra,
});
beforeEach(() => {
  vi.stubEnv("NEXT_PUBLIC_PARIPRASHNA_LIVE", "1");
  localStorage.clear();
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  );
  live.mockReturnValue({
    state: { turns: [], surfaceStatus: "empty" } as ThreadState,
    submit: vi.fn(),
    stop: vi.fn(),
    conversationId: null,
    restore,
  });
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  restore.mockReset();
});
const mount = () => {
  render(<PariprashnaApp chartId={chart} chartPin={PIN} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Open conversation history" }),
  );
};
describe("Consultation persisted history", () => {
  it("loads real history and restores messages with the actual server conversation identity", async () => {
    vi.spyOn(global, "fetch").mockImplementation(async (url) =>
      String(url).includes("?chartId=")
        ? Response.json({ conversations: [row("past", "Past consultation")] })
        : Response.json({
            conversation: {
              id: "past",
              chart_id: chart,
              title: "Past consultation",
              tagged: false,
            },
            readOnly: false,
            messages: [
              {
                id: "answer",
                role: "assistant",
                created_at: "2026-10-01T00:00:00Z",
                schema_version: null,
                parts_json: [{ type: "text", text: "Stored answer" }],
                canonical_parts: [],
                metadata_json: {},
                tagged: false,
              },
            ],
          }),
    );
    mount();
    fireEvent.click(
      await screen.findByRole("button", { name: /Past consultation/ }),
    );
    await waitFor(() =>
      expect(restore).toHaveBeenCalledWith(
        "past",
        expect.arrayContaining([
          expect.objectContaining({
            persistedMessageId: "answer",
            blocks: expect.arrayContaining([
              expect.objectContaining({ html: "Stored answer" }),
            ]),
          }),
        ]),
      ),
    );
  });
  it("keeps history disabled while streaming and merges the current id only once", async () => {
    const turn = makeInitialTurnState("turn", "Current question");
    turn.status = "streaming";
    live.mockReturnValue({
      state: { turns: [turn], surfaceStatus: "idle" },
      submit: vi.fn(),
      stop: vi.fn(),
      conversationId: "current",
      restore,
    });
    vi.spyOn(global, "fetch").mockResolvedValue(
      Response.json({
        conversations: [
          row("current", "Current conversation"),
          row("past", "Past consultation"),
        ],
      }),
    );
    mount();
    expect(
      await screen.findByRole("button", { name: /Past consultation/ }),
    ).toBeDisabled();
    expect(
      screen.getAllByRole("button", { name: /Current conversation/ }),
    ).toHaveLength(1);
  });
  it("does not restore data from another chart or silently replace the current thread after a failed read", async () => {
    vi.spyOn(global, "fetch").mockImplementation(async (url) =>
      String(url).includes("?chartId=")
        ? Response.json({ conversations: [row("past", "Past consultation")] })
        : Response.json({
            conversation: { id: "past", chart_id: "other" },
            messages: [],
            readOnly: false,
          }),
    );
    mount();
    fireEvent.click(
      await screen.findByRole("button", { name: /Past consultation/ }),
    );
    expect(
      await screen.findByText(/does not belong to this chart/),
    ).toBeVisible();
    expect(restore).not.toHaveBeenCalled();
  });
  it("links correction archives to their existing read-only reader", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      Response.json({
        conversations: [
          row("old", "Before correction", {
            archive_reason: "chart_details_changed",
            archived_at: "2026-10-02T00:00:00Z",
          }),
        ],
      }),
    );
    mount();
    expect(
      await screen.findByRole("link", { name: /Before correction/ }),
    ).toHaveAttribute("href", "/clients/chart-1/consult/old");
  });
  it("shows partial readiness without fabricating engine completeness", () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      Response.json({ conversations: [] }),
    );
    render(
      <PariprashnaApp
        chartId={chart}
        chartPin={PIN}
        readiness={{ state: "partial", percent: 33, label: "Partial" }}
      />,
    );
    expect(screen.getByTestId("pp-readiness-notice")).toHaveTextContent("33%");
    expect(screen.getByTestId("pp-readiness-notice")).toHaveTextContent(
      "may be incomplete",
    );
  });
});
