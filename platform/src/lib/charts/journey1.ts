import "server-only";
import { query } from "@/lib/db/client";
import type { ForensicChart } from "@/lib/forensic/snapshot";
import {
  AYANAMSHA_SERVE_ORDER,
  DEFAULT_AYANAMSHA,
} from "@/lib/retrieval/registry/constants";
import { resolveAyanamshaArg } from "@/lib/retrieval/chart_facts_helpers";
const SIGNS = [
  "Aries",
  "Taurus",
  "Gemini",
  "Cancer",
  "Leo",
  "Virgo",
  "Libra",
  "Scorpio",
  "Sagittarius",
  "Capricorn",
  "Aquarius",
  "Pisces",
];
// Lahiri-primary (SS N-339 / N-342 ruling): `lahiri_chitrapaksha` is the PRIMARY reading for
// EVERY chart. The portal frame is therefore always Lahiri, whatever `charts.ayanamsa` lists:
// a chart whose stored selection omits Lahiri (or lists KP/Raman first) used to be served in
// `selected[0]`, a silent pick of a non-primary frame. `charts.ayanamsa` only selects which of
// the OTHER four are shown as the labelled cross-check set (`journey1CrossCheckFrames`).
// The argument is accepted for call-site compatibility and deliberately ignored.
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function journey1Frame(_stored?: string | null): string {
  return DEFAULT_AYANAMSHA;
}
/**
 * The cross-check set: the chart's selected ayanamshas other than Lahiri, as stored ids in
 * serve order. Unknown entries are skipped (never mapped to Lahiri). Never merged into the
 * primary frame.
 */
export function journey1CrossCheckFrames(stored: string | null): string[] {
  const chosen = new Set<string>();
  for (const part of (stored ?? "").split(",")) {
    const r = resolveAyanamshaArg(part);
    if (r.ok && r.ayanamsha_id && r.ayanamsha_id !== DEFAULT_AYANAMSHA)
      chosen.add(r.ayanamsha_id);
  }
  return AYANAMSHA_SERVE_ORDER.filter((id) => chosen.has(id));
}
export function journey1FrameLabel(frame: string) {
  return (
    (
      {
        lahiri_chitrapaksha: "Lahiri · Chitrapaksha (primary)",
        krishnamurti: "KP · Krishnamurti",
        true_chitra: "True Chitra",
        raman: "B.V. Raman",
        surya_siddhanta_classical: "Surya Siddhanta",
      } as Record<string, string>
    )[frame] ?? frame
  );
}

export type DivisionalRow = {
  varga: string;
  graha: string;
  sign: string;
  degree_in_sign: number | null;
};
export function divisionalChart(
  chartId: string,
  rows: DivisionalRow[],
): ForensicChart {
  const lagna = rows.find((r) => r.graha === "Lagna");
  const index = SIGNS.indexOf(lagna?.sign ?? "");
  const houses = Array.from({ length: 12 }, (_, i) => ({
    house: i + 1,
    sign: index < 0 ? "" : SIGNS[(index + i) % 12],
    planets: [] as string[],
  }));
  if (index >= 0)
    for (const r of rows) {
      const sign = SIGNS.indexOf(r.sign);
      if (r.graha !== "Lagna" && r.graha !== "ALL" && sign >= 0)
        houses[(sign - index + 12) % 12].planets.push(r.graha);
    }
  return {
    chartId,
    lagnaSign: lagna?.sign ?? "",
    lagnaDegreeDms:
      lagna?.degree_in_sign != null
        ? `${Number(lagna.degree_in_sign).toFixed(2)}°`
        : "",
    houses,
    topYogas: [],
    currentDasha: null,
    isEmpty: index < 0,
  };
}
export type ActivationWindow = {
  event_class: string;
  window_start: string;
  window_end: string;
  peak_date: string | null;
  generation: string;
};
export async function getJourney1ChartData(
  chartId: string,
  ayanamsha = DEFAULT_AYANAMSHA,
) {
  const flags: string[] = [];
  const [divisionals, windows] = await Promise.all([
    query<DivisionalRow>(
      `SELECT DISTINCT ON (varga, graha) varga,graha,sign,degree_in_sign FROM chart_divisionals
     WHERE chart_id=$1 AND ayanamsha_id=$2 AND fact_category='varga_position' AND fact_key='sign' AND varga IN ('D9','D10') AND graha<>'ALL'
     ORDER BY varga,graha,created_at DESC,id DESC`,
      [chartId, ayanamsha],
    )
      .then((r) => r.rows)
      .catch(() => {
        flags.push("divisionals_unavailable");
        return [];
      }),
    // Same admission bar as reading_checklist.ts P-2: prior/context rows cannot
    // become a dated activation claim merely because the UI can draw a bar.
    query<ActivationWindow>(
      `SELECT w.event_class,w.window_start::text,w.window_end::text,w.peak_date::text,w.generation
     FROM kala_gochara_windows w WHERE w.chart_id=$1 AND w.window_end>=CURRENT_DATE
       AND w.completeness_state IN ('confirmed','qualified') AND w.peak_basis='gochara_lambda_v3_argmax'
       AND w.generation=COALESCE((SELECT authoritative_generation FROM kala_gochara_authority WHERE chart_id=w.chart_id),'v1')
     ORDER BY w.window_start,w.window_end,w.event_class,w.id LIMIT 4`,
      [chartId],
    )
      .then((r) => r.rows)
      .catch(() => {
        flags.push("windows_unavailable");
        return [];
      }),
  ]);
  return {
    d9: divisionalChart(
      chartId,
      divisionals.filter((r) => r.varga === "D9"),
    ),
    d10: divisionalChart(
      chartId,
      divisionals.filter((r) => r.varga === "D10"),
    ),
    windows,
    flags,
  };
}
