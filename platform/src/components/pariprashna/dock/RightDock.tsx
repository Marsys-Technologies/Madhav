"use client";
import { useEffect, useRef, type ReactNode } from "react";
import type { TurnState } from "../state/types";
import { GroundingCard } from "./GroundingCard";
import { PredictionCard } from "./PredictionCard";
import { InterpretationSetsSection } from "./InterpretationSetsSection";
import { useDockController } from "./DockController";
import { WorkspacePanel } from "./WorkspacePanel";

export function GroundingContent({ turns }: { turns: TurnState[] }) {
  const { activeCitation } = useDockController();
  const cardRefs = useRef(new Map<string, HTMLDivElement | null>());
  useEffect(() => {
    if (activeCitation)
      cardRefs.current
        .get(`${activeCitation.turnId}:${activeCitation.n}`)
        ?.scrollIntoView?.({ behavior: "smooth", block: "center" });
  }, [activeCitation]);
  const hasGrounding = turns.some(
    (t) => Object.keys(t.citations).length > 0 || t.interpretationSets,
  );
  return (
    <div className="pp-grounding-content">
      {!hasGrounding && (
        <p className="pp-panel-empty">
          Grounding appears here as sources are verified.
        </p>
      )}
      {[...turns].reverse().map((turn) => {
        const citations = Object.values(turn.citations).sort(
          (a, b) => a.n - b.n,
        );
        const classicalCount = citations.filter(
          (c) => c.sourceClass === "classical_source",
        ).length;
        // P2-close Lane K (PPR-03 typed confidence, G3-C). The receipt types
        // EVERY CITATION this turn typed (confidence_typing's own header
        // comment) — keyed by `ref`, the same token as `citation.ref`
        // (TypedConfidenceEntrySchema's own doc comment). Built once per
        // turn render, not per-citation, so a turn with many citations
        // doesn't re-scan `entries` for each row. `undefined` (never a
        // guessed type) when the receipt hasn't arrived, the flag was off,
        // or this ref simply wasn't typed.
        const confidenceTyping = turn.receipt?.confidence_typing;
        const confidenceByRef =
          confidenceTyping?.status === "measured" && confidenceTyping.entries
            ? new Map(
                confidenceTyping.entries.map((e) => [e.ref, e.confidence_type]),
              )
            : null;
        // The Seal (§5.3 step 4): the sealed turn's own ledger fades in once,
        // the instant `turn.commit` moves it to `settling`/`settled` — not on
        // every intermediate citation arriving mid-stream (ruling 8a's
        // "grounding accrues across passes" still holds; only the coordinated
        // fade is a one-time settle event). Keying the inner block on the
        // sealed/live split forces React to remount exactly once at that
        // transition, replaying `.pp-dock-seal-in`'s mount animation once —
        // further re-renders of an already-sealed turn (unrelated field
        // updates) keep the same key and do not replay it.
        const sealed = turn.status === "settling" || turn.status === "settled";
        return (
          <div key={turn.id} className="mb-5">
            <div
              key={sealed ? "sealed" : "live"}
              className={sealed ? "pp-dock-seal-in" : undefined}
            >
              {citations.length > 0 && (
                <>
                  <div
                    style={{
                      fontSize: 9,
                      letterSpacing: "0.22em",
                      textTransform: "uppercase",
                      color: "var(--pp-gold-dim)",
                      margin: "2px 0 10px",
                    }}
                  >
                    <span style={{ color: "var(--pp-ink)" }}>
                      {citations.length}
                    </span>{" "}
                    CHART FACTORS
                    {classicalCount > 0 && (
                      <>
                        {" "}
                        ·{" "}
                        <span style={{ color: "var(--pp-ink)" }}>
                          {classicalCount}
                        </span>{" "}
                        CLASSICS
                      </>
                    )}
                  </div>
                  {citations.map((c) => (
                    <GroundingCard
                      key={c.n}
                      citation={c}
                      highlighted={
                        activeCitation?.turnId === turn.id &&
                        activeCitation?.n === c.n
                      }
                      registerRef={(el) =>
                        cardRefs.current.set(`${turn.id}:${c.n}`, el)
                      }
                      confidenceType={confidenceByRef?.get(c.ref)}
                    />
                  ))}
                </>
              )}
              {turn.interpretationSets && (
                <InterpretationSetsSection
                  interpretationSets={turn.interpretationSets}
                />
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function RightDock({
  turns,
  history,
}: {
  turns: TurnState[];
  history?: ReactNode;
}) {
  const { tab, setTab } = useDockController();
  const windows = turns.flatMap((t) =>
    t.blocks.filter((b) => b.kind === "prediction_card" && b.prediction),
  );
  return (
    <div data-testid="pp-right-dock">
      <WorkspacePanel side="right" title="Evidence">
        <div className="pp-evidence-tabs" role="tablist" aria-label="Evidence">
          {(["Grounding", "Windows", "History"] as const).map((name) => (
            <button
              key={name}
              type="button"
              role="tab"
              id={`pp-tab-${name}`}
              aria-controls="pp-evidence-content"
              aria-selected={tab === name}
              tabIndex={tab === name ? 0 : -1}
              onClick={() => setTab(name)}
              onKeyDown={(e) => {
                const names = ["Grounding", "Windows", "History"] as const;
                const at = names.indexOf(name);
                let next: number | undefined;
                if (e.key === "ArrowRight") next = (at + 1) % 3;
                if (e.key === "ArrowLeft") next = (at + 2) % 3;
                if (e.key === "Home") next = 0;
                if (e.key === "End") next = 2;
                if (next !== undefined) {
                  e.preventDefault();
                  setTab(names[next]);
                  document.getElementById(`pp-tab-${names[next]}`)?.focus();
                }
              }}
            >
              {name}
            </button>
          ))}
        </div>
        <div
          id="pp-evidence-content"
          className="pp-panel-body"
          role="tabpanel"
          aria-labelledby={`pp-tab-${tab}`}
        >
          {tab === "Grounding" && <GroundingContent turns={turns} />}
          {tab === "Windows" &&
            (windows.length ? (
              windows.map((b) => (
                <PredictionCard key={b.id} prediction={b.prediction!} />
              ))
            ) : (
              <p className="pp-panel-empty">
                Computed activation windows will appear when supplied by a
                reading. Open Prediction Review for the chart’s recorded
                predictions.
              </p>
            ))}
          {tab === "History" && history}
        </div>
      </WorkspacePanel>
    </div>
  );
}
