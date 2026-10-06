import { describe, it, expect } from "vitest";
import {
  restoreConsultation,
  type StoredConsultationMessage,
} from "@/components/pariprashna/history/restore";
const stored = (
  overrides: Partial<StoredConsultationMessage>,
): StoredConsultationMessage => ({
  id: "saved-answer",
  role: "assistant",
  created_at: "2026-10-05T00:00:00Z",
  schema_version: 1,
  tagged: false,
  metadata_json: null,
  parts_json: [],
  canonical_parts: [],
  ...overrides,
});
describe("Stored Consultation restoration", () => {
  it("restores canonical text and actual citations, without fabricating coverage or promoting candidates", () => {
    const turns = restoreConsultation([
      stored({
        id: "question",
        role: "user",
        canonical_parts: [{ kind: "text", body: { text: "Question" } }],
      }),
      stored({
        canonical_parts: [
          { kind: "text", body: { text: "Actual answer ⟦1⟧" } },
          {
            kind: "citation",
            body: {
              index: 1,
              signal_id: "BPHS",
              layer: "L0",
              snippet: "Actual source",
              grade: "supporting",
            },
          },
          {
            kind: "prediction_candidate",
            body: { claim: "Candidate only", window: "2027" },
          },
        ],
      }),
    ]);
    expect(turns[0]).toMatchObject({
      userText: "Question",
      persistedMessageId: "saved-answer",
      persistence: "durable",
      grounding: null,
      receipt: null,
    });
    expect(turns[0].blocks[0].html).toBe("Actual answer ⟦1⟧");
    expect(turns[0].citations[1]).toMatchObject({
      ref: "BPHS",
      sourceClass: "classical_source",
      grade: "supported",
    });
    expect(turns[0].blocks.some((b) => b.kind === "prediction_card")).toBe(
      false,
    );
  });
  it("fails clearly on unsupported schema and malformed citations", () => {
    expect(() =>
      restoreConsultation([stored({ schema_version: 999 })]),
    ).toThrow(/unsupported/);
    expect(() =>
      restoreConsultation([
        stored({ canonical_parts: [{ kind: "citation", body: { index: 1 } }] }),
      ]),
    ).toThrow();
  });
});
