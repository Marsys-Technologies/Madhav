import { makeInitialTurnState } from "../state/reducer";
import { makeS1LiveAdapter } from "../state/s1LiveAdapter";
import { AcharyaReadingReceiptSchema } from "@/lib/pariprashna/receipt/schema";
import {
  parsePartContent,
  isCanonicalSchemaVersionSupported,
} from "@/lib/pariprashna/store/schema";
import type { TurnState } from "../state/types";

export interface StoredConsultationMessage {
  id: string;
  role: string;
  created_at: string;
  tagged: boolean;
  schema_version: number | null;
  parts_json: Array<{ type: string; text?: string }>;
  metadata_json: Record<string, unknown> | null;
  canonical_parts: Array<{ kind: string; body: unknown }>;
}

/** Restore persisted reader data, not replayed reasoning or invented timing windows. */
export function restoreConsultation(
  messages: StoredConsultationMessage[],
): TurnState[] {
  const turns: TurnState[] = [];
  let question = "";
  for (const message of messages) {
    if (
      message.schema_version != null &&
      !isCanonicalSchemaVersionSupported(message.schema_version)
    ) {
      throw new Error("This conversation uses an unsupported format.");
    }
    const parts = message.canonical_parts.map((p) =>
      parsePartContent(p.kind, p.body),
    );
    const text =
      parts
        .filter((p) => p.kind === "text")
        .map((p) => (p.kind === "text" ? p.body.text : ""))
        .join("\n") ||
      (message.parts_json ?? [])
        .filter((p) => p.type === "text")
        .map((p) => p.text ?? "")
        .join("\n");
    if (message.role === "user") {
      question = text;
      continue;
    }
    if (message.role !== "assistant") continue;
    const turn = makeInitialTurnState(message.id, question);
    turn.persistedMessageId = message.id;
    turn.status = "settled";
    turn.persistence = "durable"; // It was read from the committed message row.
    turn.openedAtMs = new Date(message.created_at).getTime();
    turn.blocks = [{ id: message.id, kind: "paragraph", html: text }];
    const receipt = AcharyaReadingReceiptSchema.safeParse(
      message.metadata_json?.acharya_reading_receipt,
    );
    if (receipt.success) {
      turn.receipt = receipt.data;
      turn.interpretationSets = receipt.data.interpretation_sets ?? null;
    }
    const adapter = makeS1LiveAdapter(message.id, question, turn.openedAtMs);
    for (const part of parts) {
      if (part.kind !== "citation") continue;
      const events = adapter.map({
        type: "citation.define",
        seq: part.body.index,
        t: turn.openedAtMs,
        ...part.body,
      });
      for (const event of events)
        if (event.type === "citation.define")
          turn.citations[event.citation.n] = event.citation;
    }
    // Do not reconstruct server coverage/elapsed time or promote prediction candidates.
    turns.push(turn);
  }
  return turns;
}
