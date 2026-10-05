import type { ActivationWindow } from "@/lib/charts/journey1";
import { formatDate } from "@/lib/utils/date";
export function ActivationTimeline({
  windows,
}: {
  windows: ActivationWindow[];
}) {
  const dates = windows
    .flatMap((w) => [Date.parse(w.window_start), Date.parse(w.window_end)])
    .filter(Number.isFinite);
  const start = Math.min(...dates),
    end = Math.max(...dates),
    span = Math.max(end - start, 86400000);
  return (
    <ol className="j1-windows" aria-label="Recorded activation windows">
      {windows.map((w, i) => {
        const left = Math.max(
            0,
            ((Date.parse(w.window_start) - start) / span) * 100,
          ),
          width = Math.max(
            1,
            ((Date.parse(w.window_end) - Date.parse(w.window_start)) / span) *
              100,
          );
        return (
          <li className="j1-window" key={`${w.event_class}-${i}`}>
            <span>{w.event_class.replaceAll("_", " ")}</span>
            <small>
              {formatDate(w.window_start)} — {formatDate(w.window_end)}
              {w.peak_date ? ` · peak ${formatDate(w.peak_date)}` : ""}
            </small>
            <div
              aria-hidden="true"
              style={{
                height: 6,
                position: "relative",
                marginTop: 8,
                borderRadius: 3,
                background: "#231e14",
              }}
            >
              <i
                style={{
                  position: "absolute",
                  left: `${Math.min(left, 99)}%`,
                  width: `${Math.min(width, 100 - left)}%`,
                  height: 6,
                  borderRadius: 3,
                  background: "#a87c2a",
                }}
              />
            </div>
          </li>
        );
      })}
    </ol>
  );
}
