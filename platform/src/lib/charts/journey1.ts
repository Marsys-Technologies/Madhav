import "server-only";
import { query } from "@/lib/db/client";
import type { ForensicChart } from "@/lib/forensic/snapshot";
import { DEFAULT_AYANAMSHA } from "@/lib/retrieval/registry/constants";
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
// Chart forms store short keys; the computed L1 data uses these released keys.
// Preserve the selected computation frame rather than querying a short-key alias.
export function journey1Frame(stored: string | null) {
  const aliases: Record<string, string> = {
    lahiri: DEFAULT_AYANAMSHA,
    kp: "krishnamurti",
    surya_siddhanta: "surya_siddhanta_classical",
  };
  const selected = (stored ?? "")
    .split(",")
    .map((v) => v.trim())
    .filter(Boolean)
    .map((v) => aliases[v] ?? v);
  return selected.includes(DEFAULT_AYANAMSHA) || !selected.length
    ? DEFAULT_AYANAMSHA
    : selected[0];
}
export function journey1FrameLabel(frame: string) {
  return (
    (
      {
        lahiri_chitrapaksha: "Lahiri · Chitrapaksha",
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
