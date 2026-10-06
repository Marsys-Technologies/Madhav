"use client";

import "../pariprashna/pariprashna.css";
// PB-6 (SAMĀPTI): samiksha.css was never imported anywhere, so the
// spec-conformant KalaRekha/PredictionCard pair's CSS classes (.pp-kala-rekha*,
// .pp-prediction-card*) had no effect wherever they were used — now mounted
// live in the right dock (dock/PredictionCard.tsx).
import "./samiksha/samiksha.css";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ThreadHeader, type ChartPin } from "./ThreadHeader";
import { Transcript } from "./Transcript";
import { EmptyState } from "./EmptyState";
import { ArrivalLine, type ArrivalLineData } from "./ArrivalLine";
import { Composer } from "./composer/Composer";
import { RightDock } from "./dock/RightDock";
import {
  ConsultationHistory,
  type ConsultationThread,
} from "./history/ConsultationHistory";
import {
  restoreConsultation,
  type StoredConsultationMessage,
} from "./history/restore";
import { TagActionsProvider } from "./history/TagActions";
import { WorkspacePanel } from "./dock/WorkspacePanel";
import { ChartNav } from "@/components/journey1/ChartNav";
import { ShareButton } from "@/components/chat/ShareButton";
import { ExportDropdown } from "@/components/chat/ExportDropdown";
import { Bookmark, BookmarkCheck } from "lucide-react";
import { OverlayLayer } from "./overlay/OverlayLayer";
import { DockControllerProvider } from "./dock/DockController";
import { useFixtureStream } from "./state/useFixtureStream";
import { useLiveStream } from "./hooks/useLiveStream";
import { useAiChoices } from "./hooks/useAiChoices";
import { FIXTURE_ARRIVAL_LINE } from "./fixtures/arrival";
import { useVisualViewport } from "./hooks/useVisualViewport";
import type { FixtureMode } from "./fixtures";
import type { SubmitControls, ThreadState, TurnState } from "./state/types";

/**
 * The transport-agnostic stream contract the surface consumes. Both
 * `useFixtureStream` (dev replay) and `useLiveStream` (real SSE) satisfy it:
 * `submit(text, mode, controls?)` — the fixture host plays `mode` as a canned
 * fixture and ignores `controls`; the live host reads `controls` (lane P2-C —
 * `SubmitControls`, sent honestly by the composer's own picker state) to build
 * the real request, no longer re-deriving `reading_depth` from `mode`. Callers
 * with no real picker state (`EmptyState`'s example prompts, the dev fixture
 * picker) omit `controls`; the live host applies the same 'auto'/'standard'
 * defaults the request already had.
 */
export interface PariprashnaStream {
  state: ThreadState;
  submit: (
    text: string,
    mode: FixtureMode,
    controls?: SubmitControls,
  ) => string | void;
  stop: (turnId: string) => void;
  conversationId?: string | null;
  restore?: (id: string | null, turns: TurnState[]) => void;
}

export interface PariprashnaReadiness {
  state: string;
  percent: number;
  label: string;
}

/** Truncates a user question into a sidebar-row-length auto-generated title (§10.1). */
function autoTitle(userText: string): string {
  const trimmed = userText.trim();
  if (trimmed.length <= 46) return trimmed;
  return `${trimmed.slice(0, 45)}…`;
}

const EXAMPLE_PROMPTS = [
  "What does this period ask of my career?",
  "Is a career change on the cards over the next two years?",
  "When should I not initiate anything new?",
];

/** Dev/QA only — exercises fixture modes the Depth control doesn't reach (gap, reconnect, the two lane-C-2-recorded replays). Not part of the mockup's production chrome. */
function DevFixturePicker({
  onPick,
  disabled,
}: {
  onPick: (mode: FixtureMode) => void;
  disabled: boolean;
}) {
  if (process.env.NODE_ENV === "production") return null;
  const modes: { mode: FixtureMode; label: string }[] = [
    { mode: "adaptive", label: "Adaptive · 3 passes" },
    { mode: "single", label: "Single pass" },
    { mode: "gap", label: "Honest gap" },
    { mode: "reconnect", label: "Reconnect mid-pass" },
    { mode: "c2-single", label: "C-2 recorded: single" },
    { mode: "c2-gap", label: "C-2 recorded: gap" },
  ];
  return (
    <div
      className="flex flex-wrap gap-1.5 px-6 py-2"
      style={{ borderTop: "1px solid var(--pp-rule)" }}
    >
      <span
        style={{
          fontSize: 9,
          letterSpacing: "0.2em",
          textTransform: "uppercase",
          color: "var(--pp-gold-tertiary)",
          marginRight: 4,
          alignSelf: "center",
        }}
      >
        Dev · fixture
      </span>
      {modes.map((m) => (
        <button
          key={m.mode}
          type="button"
          disabled={disabled}
          onClick={() => onPick(m.mode)}
          className="rounded"
          style={{
            fontSize: 11,
            color: "var(--pp-ink-dim)",
            border: "1px solid var(--pp-rule)",
            background: "none",
            padding: "4px 9px",
            opacity: disabled ? 0.4 : 1,
          }}
        >
          {m.label}
        </button>
      ))}
    </div>
  );
}

/**
 * Paripraśna app entry. Chooses the transport HOST at mount:
 *   • live SSE against `/api/pariprashna` when a chartId is present AND the
 *     `NEXT_PUBLIC_PARIPRASHNA_LIVE` flag is on (the deploy-behind-a-flag path);
 *   • otherwise the fixture-replay host (dev / component work / no chartId).
 * The two hosts are distinct components so each calls exactly one transport
 * hook (React hook rules) and both render the same `<PariprashnaSurface>`.
 */
export function PariprashnaApp({
  chartPin,
  chartId,
  readiness,
  userId = "preview",
  canBuild = false,
}: {
  userId?: string;
  canBuild?: boolean;
  chartPin: ChartPin;
  chartId?: string;
  readiness?: PariprashnaReadiness;
}) {
  const liveEnabled =
    process.env.NEXT_PUBLIC_PARIPRASHNA_LIVE === "1" && !!chartId;
  if (liveEnabled && chartId) {
    // Chart identity owns the entire live session. A keyed remount resets the
    // AI-choice acknowledgement alongside transport state before the new
    // chart can submit.
    return (
      <PariprashnaAppLive
        key={chartId}
        chartPin={chartPin}
        chartId={chartId}
        readiness={readiness}
        userId={userId}
        canBuild={canBuild}
      />
    );
  }
  return <PariprashnaAppFixture chartPin={chartPin} readiness={readiness} />;
}

/** Fixture-replay host (default): canned event streams, no backend — no real
 *  chart id, so `chartId` is left undefined (see `AnswerRegion`'s guard). */
function PariprashnaAppFixture({
  chartPin,
  readiness,
}: {
  chartPin: ChartPin;
  readiness?: PariprashnaReadiness;
}) {
  const stream = useFixtureStream();
  return (
    <PariprashnaSurface
      chartPin={chartPin}
      chartId="fixture-chart"
      readiness={readiness}
      stream={stream}
      showDevPicker
      isFixtureHost
    />
  );
}

/**
 * Live host: real SSE via `/api/pariprashna`. Lane P2-C: `reading_depth`,
 * `model_id`, and `length_tier` now come from the composer's OWN picker state
 * (`controls`) rather than being re-derived from the dev-fixture `mode`
 * (which used to force `deep_dive` for every Depth selection except "Quick" —
 * see the P2-C build report for how that mapping was discovered). `mode` is
 * ignored here entirely; it exists only for the fixture host.
 */
function PariprashnaAppLive({
  chartPin,
  chartId,
  readiness,
  userId,
  canBuild,
}: {
  userId: string;
  canBuild: boolean;
  chartPin: ChartPin;
  chartId: string;
  readiness?: PariprashnaReadiness;
}) {
  const live = useLiveStream(chartId);
  const stream = useMemo<PariprashnaStream>(
    () => ({
      state: live.state,
      submit: (text: string, _mode: FixtureMode, controls?: SubmitControls) =>
        live.submit(text, {
          reading_depth: controls?.readingDepth ?? "auto",
          aiMode: controls?.aiMode ?? { kind: "legacy" },
          length_tier: controls?.lengthTier ?? "standard",
        }),
      stop: live.stop,
      conversationId: live.conversationId,
      restore: live.restore,
    }),
    [live],
  );
  return (
    <PariprashnaSurface
      chartPin={chartPin}
      chartId={chartId}
      readiness={readiness}
      stream={stream}
      userId={userId}
      canBuild={canBuild}
      showDevPicker={false}
      isFixtureHost={false}
    />
  );
}

/**
 * The presentational shell — transport-agnostic. Receives a `PariprashnaStream`
 * and renders header / transcript / composer / dock / overlay. Identical markup
 * for both hosts; only the dev fixture picker is fixture-host-only.
 */
export function PariprashnaSurface({
  chartPin,
  chartId,
  readiness,
  stream,
  showDevPicker,
  isFixtureHost,
  userId = "preview",
  canBuild = false,
}: {
  chartPin: ChartPin;
  chartId: string;
  readiness?: PariprashnaReadiness;
  stream: PariprashnaStream;
  showDevPicker: boolean;
  isFixtureHost: boolean;
  userId?: string;
  canBuild?: boolean;
}) {
  const { state, submit, stop } = stream;
  const aiChoices = useAiChoices(
    stream.conversationId ?? null,
    !isFixtureHost &&
      process.env.NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK === "true",
  );
  const activeTurn = state.turns.at(-1);
  const streaming =
    !!activeTurn &&
    !["settled", "interrupted", "errored"].includes(activeTurn.status);
  const [past, setPast] = useState<ConsultationThread[]>([]),
    [historyLoading, setHistoryLoading] = useState(false),
    [historyError, setHistoryError] = useState<string | null>(null);
  const [opening, setOpening] = useState(false),
    [notice, setNotice] = useState<string | null>(null);
  const [readOnly, setReadOnly] = useState(false),
    [selectedTitle, setSelectedTitle] = useState<string | null>(null);
  const [conversationTagged, setConversationTagged] = useState<boolean | null>(
      null,
    ),
    [answers, setAnswers] = useState<Record<string, boolean>>({}),
    [tagBusy, setTagBusy] = useState(false);
  const requestVersion = useRef(0);
  const historyVersion = useRef(0);
  const refresh = useCallback(async () => {
    if (isFixtureHost) return;
    const version = ++historyVersion.current;
    await Promise.resolve();
    if (version !== historyVersion.current) return;
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const response = await fetch(
        `/api/conversations/consultation?chartId=${encodeURIComponent(chartId)}`,
        { cache: "no-store" },
      );
      if (!response.ok)
        throw new Error("History could not be loaded. Please try again.");
      const data = await response.json();
      if (version !== historyVersion.current) return;
      setPast(
        data.conversations.map(
          (c: {
            id: string;
            chart_id: string;
            title: string | null;
            first_message_snippet: string | null;
            created_at: string;
            updated_at: string | null;
            archived_at: string | null;
            archive_reason: string | null;
            tagged: boolean;
            tagged_answers: Array<{ id: string; text: string | null }>;
          }) => ({
            id: c.id,
            chartId: c.chart_id,
            chartName: chartPin.name,
            title:
              c.title ?? c.first_message_snippet ?? "Untitled conversation",
            updatedAtMs: new Date(c.updated_at ?? c.created_at).getTime(),
            active: false,
            streaming: false,
            tagged: c.tagged,
            taggedAnswers: c.tagged_answers,
            archivedAt: c.archived_at,
            archiveReason:
              c.archive_reason === "chart_details_changed"
                ? "chart_details_changed"
                : null,
            ...(c.archive_reason === "chart_details_changed"
              ? {
                  href: `/clients/${encodeURIComponent(c.chart_id)}/consult/${encodeURIComponent(c.id)}`,
                }
              : {}),
          }),
        ),
      );
    } catch (error) {
      if (version !== historyVersion.current) return;
      setHistoryError(
        error instanceof Error ? error.message : "History is unavailable.",
      );
    } finally {
      if (version === historyVersion.current) setHistoryLoading(false);
    }
  }, [chartId, chartPin.name, isFixtureHost]);
  useEffect(() => {
    const task = setTimeout(() => void refresh(), 0);
    return () => clearTimeout(task);
  }, [refresh]);
  useEffect(() => {
    const invalidate = () => {
      requestVersion.current++;
      historyVersion.current++;
    };
    return invalidate;
  }, []);
  // Refresh after durable completion, not every streaming token.
  useEffect(() => {
    if (
      activeTurn?.status !== "settled" ||
      activeTurn.persistence !== "durable"
    )
      return;
    const task = setTimeout(() => void refresh(), 0);
    return () => clearTimeout(task);
  }, [activeTurn?.id, activeTurn?.status, activeTurn?.persistence, refresh]);
  const currentId = stream.conversationId ?? `session-${chartId}`;
  const currentPast = past.find((t) => t.id === currentId);
  const currentTagged = conversationTagged ?? currentPast?.tagged ?? false;
  const threads: ConsultationThread[] = state.turns.length
    ? [
        {
          id: currentId,
          chartId,
          chartName: chartPin.name,
          title:
            selectedTitle ??
            currentPast?.title ??
            autoTitle(state.turns[0].userText),
          updatedAtMs: activeTurn?.openedAtMs ?? 0,
          active: true,
          streaming,
          tagged: currentTagged,
          taggedAnswers: currentPast?.taggedAnswers ?? [],
        },
        ...past.filter((t) => t.id !== currentId),
      ]
    : past;
  const openConversation = useCallback(
    async (id: string, answerId?: string) => {
      if (streaming || opening || !stream.restore) return;
      if (id === currentId) {
        if (answerId)
          document
            .getElementById(`pp-answer-${answerId}`)
            ?.scrollIntoView({ block: "center" });
        return;
      }
      const version = ++requestVersion.current;
      setOpening(true);
      setNotice(null);
      try {
        const response = await fetch(
          `/api/conversations/${encodeURIComponent(id)}/consultation`,
          { cache: "no-store" },
        );
        if (!response.ok)
          throw new Error(
            "This conversation could not be opened. Your current conversation is unchanged.",
          );
        const data = (await response.json()) as {
          conversation: {
            id: string;
            chart_id: string;
            title: string | null;
            tagged: boolean;
          };
          messages: StoredConsultationMessage[];
          readOnly: boolean;
        };
        if (version !== requestVersion.current) return;
        if (
          data.conversation.chart_id !== chartId ||
          data.conversation.id !== id
        )
          throw new Error("The conversation does not belong to this chart.");
        const turns = restoreConsultation(data.messages);
        setReadOnly(data.readOnly);
        setSelectedTitle(data.conversation.title);
        setConversationTagged(data.conversation.tagged);
        setAnswers(
          Object.fromEntries(
            data.messages
              .filter((m) => m.role === "assistant")
              .map((m) => [m.id, m.tagged]),
          ),
        );
        stream.restore(id, turns);
        if (answerId)
          requestAnimationFrame(() =>
            document
              .getElementById(`pp-answer-${answerId}`)
              ?.scrollIntoView({ block: "center" }),
          );
      } catch (error) {
        if (version === requestVersion.current)
          setNotice(
            error instanceof Error
              ? error.message
              : "This conversation could not be opened.",
          );
      } finally {
        if (version === requestVersion.current) setOpening(false);
      }
    },
    [chartId, currentId, opening, stream, streaming],
  );
  const newConversation = () => {
    if (streaming || opening) return;
    requestVersion.current++;
    stream.restore?.(null, []);
    setReadOnly(false);
    setSelectedTitle(null);
    setConversationTagged(false);
    setAnswers({});
    setNotice(null);
  };
  const setTag = async (tagged: boolean, messageId?: string) => {
    if (!stream.conversationId || tagBusy || readOnly) return;
    setTagBusy(true);
    setNotice(null);
    try {
      const response = await fetch(
        `/api/conversations/${encodeURIComponent(stream.conversationId)}/consultation`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tagged, ...(messageId ? { messageId } : {}) }),
        },
      );
      if (!response.ok)
        throw new Error("The tag could not be saved. Please try again.");
      if (messageId)
        setAnswers((previous) => ({ ...previous, [messageId]: tagged }));
      else setConversationTagged(tagged);
      await refresh();
    } catch (error) {
      setNotice(
        error instanceof Error ? error.message : "The tag could not be saved.",
      );
    } finally {
      setTagBusy(false);
    }
  };
  const history = (
    <ConsultationHistory
      threads={threads}
      onSelect={(id, answerId) => void openConversation(id, answerId)}
      onNew={newConversation}
      disabled={streaming || opening || isFixtureHost || tagBusy}
      loading={historyLoading}
      error={historyError}
      onRetry={() => void refresh()}
    />
  );
  const arrival: ArrivalLineData | null =
    isFixtureHost && state.turns.length ? FIXTURE_ARRIVAL_LINE : null;
  const vv = useVisualViewport();
  const handleSubmit = (
    text: string,
    mode: FixtureMode,
    controls?: SubmitControls,
  ) => {
    if (readOnly || opening || tagBusy) return;
    if (!controls && aiChoices.mode.kind === "byok" && !aiChoices.canSubmit)
      return;
    submit(
      text,
      mode,
      controls ?? {
        aiMode: aiChoices.mode,
        readingDepth: "auto",
        lengthTier: "standard",
      },
    );
  };
  const canTag =
    !isFixtureHost &&
    !readOnly &&
    !opening &&
    !!stream.conversationId &&
    state.turns.some((t) => t.receipt && t.persistence === "durable");
  return (
    <DockControllerProvider defaultOpen={false} userId={userId}>
      <TagActionsProvider
        answers={answers}
        busy={tagBusy}
        enabled={canTag}
        setTag={(tagged, messageId) => void setTag(tagged, messageId)}
      >
        <div
          className="pp-root pp-consultation"
          data-vh-source={vv.supported ? "visual-viewport" : "fallback"}
          data-compact-viewport={vv.height != null && vv.height < 550}
          style={{
            height:
              vv.supported && vv.height != null
                ? `${Math.max(160, vv.height - 68)}px`
                : "calc(100dvh - 68px)",
          }}
        >
          {!isFixtureHost && (
            <ChartNav
              chartId={chartId}
              canBuild={canBuild}
              active="consultation"
            />
          )}
          <ThreadHeader
            chartPin={chartPin}
            chartId={isFixtureHost ? undefined : chartId}
          />
          <div className="pp-workspace">
            <WorkspacePanel side="left" title="History">
              <div className="pp-panel-body">{history}</div>
            </WorkspacePanel>
            <div data-testid="pp-main-column" className="pp-main-column">
              <div className="pp-conversation-heading">
                <span>
                  {selectedTitle ?? currentPast?.title ?? "Ask Madhav"}
                </span>
                <div className="pp-conversation-actions">
                  {!isFixtureHost &&
                    stream.conversationId &&
                    !streaming &&
                    state.turns.some((t) => t.persistence === "durable") && (
                      <>
                        <ShareButton
                          key={`share-${currentId}`}
                          conversationId={stream.conversationId}
                        />
                        <ExportDropdown
                          conversationId={stream.conversationId}
                        />
                      </>
                    )}
                  <button
                    type="button"
                    className="pp-tag-answer"
                    disabled={!canTag || tagBusy}
                    aria-pressed={currentTagged}
                    onClick={() => void setTag(!currentTagged)}
                  >
                    {currentTagged ? (
                      <BookmarkCheck size={16} />
                    ) : (
                      <Bookmark size={16} />
                    )}
                    <span>Tag conversation</span>
                  </button>
                </div>
              </div>
              {readiness && readiness.state !== "ready" && (
                <div
                  role="status"
                  data-testid="pp-readiness-notice"
                  className="pp-workspace-notice"
                >
                  Chart readiness · {readiness.percent}% — Responses may be
                  incomplete until the chart is fully built.
                </div>
              )}
              {notice && (
                <div role="status" className="pp-workspace-notice">
                  {notice}
                  <button
                    type="button"
                    aria-label="Dismiss notice"
                    onClick={() => setNotice(null)}
                  >
                    Dismiss
                  </button>
                </div>
              )}
              {opening && (
                <div role="status" className="pp-workspace-notice">
                  Opening conversation…
                </div>
              )}
              {readOnly && (
                <div role="status" className="pp-workspace-notice">
                  Historical conversation · read-only. Start a new conversation
                  to use the current chart.
                </div>
              )}
              <ArrivalLine arrival={arrival} />
              {state.turns.length ? (
                <Transcript
                  key={`transcript-${currentId}`}
                  turns={state.turns}
                  chartId={readOnly ? undefined : chartId}
                />
              ) : (
                <EmptyState
                  examplePrompts={EXAMPLE_PROMPTS}
                  onPick={(text) => handleSubmit(text, "adaptive")}
                />
              )}
              {showDevPicker && (
                <DevFixturePicker
                  disabled={streaming}
                  onPick={(mode) => submit(EXAMPLE_PROMPTS[0], mode)}
                />
              )}
              {!readOnly && (
                <Composer
                  key={`composer-${currentId}`}
                  streaming={streaming}
                  disabled={opening || tagBusy}
                  onSubmit={handleSubmit}
                  onStop={() => {
                    if (activeTurn) stop(activeTurn.id);
                  }}
                  depthReceived={activeTurn?.readingDepthReceived}
                  autoFocus={false}
                  aiChoices={aiChoices}
                />
              )}
            </div>
            <RightDock turns={state.turns} history={history} />
          </div>
          <OverlayLayer turns={state.turns} />
        </div>
      </TagActionsProvider>
    </DockControllerProvider>
  );
}
