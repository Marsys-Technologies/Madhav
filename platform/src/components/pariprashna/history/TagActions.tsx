"use client";
import { createContext, useContext, type ReactNode } from "react";
import { ShareButton } from '@/components/chat/ShareButton';
import { ExportDropdown } from '@/components/chat/ExportDropdown';
import { Bookmark, BookmarkCheck } from "lucide-react";
import type { TurnState } from "../state/types";
interface Tags {
  answers: Record<string, boolean>;
  busy: boolean;
  enabled: boolean;
  share?: { conversationId: string; chartId: string };
  setTag: (tagged: boolean, messageId?: string) => void;
}
const Context = createContext<Tags | null>(null);
export function TagActionsProvider({
  children,
  ...value
}: Tags & { children: ReactNode }) {
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function AnswerTag({ turn }: { turn: TurnState }) {
  const tags = useContext(Context);
  if (!tags || turn.status !== "settled") return null;
  const id = turn.persistedMessageId,
    tagged = !!(id && tags.answers[id]);
  return (
    <div className="flex items-center gap-2"><button
      type="button"
      className="pp-tag-answer"
      disabled={
        !tags.enabled || tags.busy || !id || turn.persistence !== "durable"
      }
      aria-pressed={tagged}
      onClick={() => tags.setTag(!tagged, id)}
      title={
        id
          ? "Tag this question and answer"
          : "Tagging becomes available after the answer is saved"
      }
    >
      {tagged ? <BookmarkCheck size={16} /> : <Bookmark size={16} />}{" "}
      {tagged ? "Tagged answer" : "Tag answer"}
    </button>
    {tags.share && id && turn.persistence === "durable" && <><ShareButton conversationId={tags.share.conversationId} messageId={id}/><ExportDropdown conversationId={tags.share.conversationId} chartId={tags.share.chartId} messageId={id}/></>}
    </div>
  );
}
