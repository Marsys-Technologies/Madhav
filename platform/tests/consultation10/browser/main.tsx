/** Test-only component harness. No application route, credentials or AI-provider calls. */
import { createRoot } from "react-dom/client";
import { useMemo, useState } from "react";
import "@/app/globals.css";
import "@/app/journey1.css";
import { JourneyShell } from "@/components/journey1/JourneyShell";
import {
  PariprashnaSurface,
  type PariprashnaStream,
} from "@/components/pariprashna/PariprashnaApp";
import {
  initialThreadState,
  threadReducer,
} from "@/components/pariprashna/state/reducer";
import { buildFixtureForMode } from "@/components/pariprashna/fixtures";
import type { ThreadState } from "@/components/pariprashna/state/types";
const chart = "22222222-2222-4222-8222-222222222222",
  id = "11111111-1111-4111-8111-111111111111";
function App() {
  const [state, setState] = useState<ThreadState>(initialThreadState),
    [conversation, setConversation] = useState<string | null>(null);
  const stream = useMemo<PariprashnaStream>(
    () => ({
      state,
      conversationId: conversation,
      submit: (question, mode) => {
        setConversation(id);
        setState((previous) => {
          let next = threadReducer(previous, {
            type: "CLIENT_SUBMIT_TURN",
            turnId: "test-turn",
            userText: question,
          });
          for (const { event } of buildFixtureForMode(
            mode,
            "test-turn",
            question,
          ).events)
            next = threadReducer(next, event);
          return next;
        });
      },
      stop: () => {},
      restore: (selected, turns) => {
        setConversation(selected);
        setState({ turns, surfaceStatus: turns.length ? "idle" : "empty" });
      },
    }),
    [state, conversation],
  );
  return (
    <JourneyShell
      chartId={chart}
      user={{ uid: "consultation-test", name: "Fictional test user" }}
      role="guest"
    >
      <PariprashnaSurface
        chartPin={{
          name: "Fictional Test Native",
          bornLine: "05 Feb 1984 · 10:43 · Test location",
        }}
        chartId={chart}
        canBuild
        userId="consultation-test"
        stream={stream}
        showDevPicker={false}
        isFixtureHost={false}
      />
    </JourneyShell>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
