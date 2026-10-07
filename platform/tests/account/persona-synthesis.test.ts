import { it, expect, vi } from "vitest";
vi.mock("@/lib/pariprashna/summaries/splice", () => ({
  getConversationSummaryForSplice: async () => null,
}));
vi.mock("@/lib/config/index", () => ({
  configService: { getFlag: () => false, getValue: () => undefined },
}));
import { assembleSynthesisContext } from "@/lib/pariprashna/pipeline/synthesis_stage";
import { personaReadingGuidance } from "@/lib/account/reading-persona";
import type { PipelinePlan } from "@/lib/pipeline/types";
it("carries each saved presentation style into the actual synthesis prompt with explicit length precedence", async () => {
  for (const [style, term] of [
    ["brief", "concise"],
    ["client", "plain language"],
    ["acharya", "classical terminology"],
  ]) {
    const ctx = await assembleSynthesisContext({
      messages: [
        {
          id: "q",
          role: "user",
          parts: [{ type: "text", text: "Fictional question" }],
        },
      ],
      bundle: { assets: [{ content: "Admitted evidence" }] },
      plan: { synthesis_guidance: null } as unknown as PipelinePlan,
      orientation: null,
      conversationId: "fictional",
      personaGuidance: personaReadingGuidance({
        name: "Fictional",
        system_prompt: "Preserve uncertainty.",
        default_style: style,
      }),
    });
    expect(ctx.systemContentWithSummary).toContain(term);
    expect(ctx.systemContentWithSummary).toContain("explicit response length");
    expect(ctx.systemContentWithSummary).toContain("cannot override");
  }
});
