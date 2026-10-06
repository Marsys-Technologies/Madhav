import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook, act, waitFor, cleanup } from "@testing-library/react";
import { useLiveStream } from "@/components/pariprashna/hooks/useLiveStream";
import { makeInitialTurnState } from "@/components/pariprashna/state/reducer";
const conversation = "11111111-1111-4111-8111-111111111111";
function response(id = conversation) {
  return new Response(
    new ReadableStream<Uint8Array>({
      start(c) {
        c.enqueue(
          new TextEncoder().encode(
            `data: ${JSON.stringify({ type: "turn.open", seq: 0, t: 1, turn_id: "server-turn", conversation_id: id, chart_id: "chart", model_id: "model", reading_depth: "auto", length_tier: "standard" })}\n\n`,
          ),
        );
        c.close();
      },
    }),
    { headers: { "Content-Type": "text/event-stream" } },
  );
}
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
describe("Consultation history transport", () => {
  it.each(["legacy", "byok"] as const)(
    "continues a restored %s conversation using its exact server identity",
    async (kind) => {
      const fetch = vi.fn<typeof globalThis.fetch>(async () => response());
      vi.stubGlobal("fetch", fetch);
      const { result } = renderHook(() => useLiveStream("chart"));
      const stored = makeInitialTurnState("stored", "Original question");
      stored.status = "settled";
      act(() => result.current.restore(conversation, [stored]));
      act(() =>
        result.current.submit("Follow-up", {
          aiMode:
            kind === "legacy"
              ? { kind: "legacy", modelId: "model" }
              : { kind: "byok", selection: { kind: "default" } },
        }),
      );
      await waitFor(() => expect(fetch).toHaveBeenCalled());
      expect(JSON.parse(fetch.mock.calls[0][1]!.body as string)).toMatchObject({
        conversationId: conversation,
        chartId: "chart",
      });
      expect(result.current.state.turns[0].id).toBe("stored");
    },
  );
  it("aborts a previous session and ignores a late response instead of restoring its conversation identity", async () => {
    let release: (response: Response) => void = () => {};
    let signal: AbortSignal | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn((_url: unknown, options: RequestInit) => {
        signal = options.signal as AbortSignal;
        return new Promise<Response>((resolve) => {
          release = resolve;
        });
      }),
    );
    const { result } = renderHook(() => useLiveStream("chart"));
    act(() => result.current.submit("Old question"));
    act(() => result.current.restore(null, []));
    expect(signal?.aborted).toBe(true);
    await act(async () => release(response()));
    expect(result.current.conversationId).toBeNull();
    expect(result.current.state.turns).toEqual([]);
  });
});
