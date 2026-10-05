import type { ForensicChart } from "@/lib/forensic/snapshot";
const signs = [
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
import { grahaIdentityOf } from "@/lib/retrieval/graha_labels";
function shortLabel(planet: string) {
  try {
    return grahaIdentityOf(planet).canonical_label.slice(0, 2);
  } catch {
    return planet;
  }
}
// Fixed HOUSE positions, anti-clockwise from the top diamond. Sign numbers follow Lagna.
const centers = [
  [240, 115],
  [120, 42],
  [42, 120],
  [115, 240],
  [42, 360],
  [120, 438],
  [240, 365],
  [360, 438],
  [438, 360],
  [365, 240],
  [438, 120],
  [360, 42],
];
export function NorthIndianChart({
  chart,
  name = "D1 · Rāśi",
}: {
  chart: ForensicChart;
  name?: string;
}) {
  const placements = chart.houses
    .filter((h) => h.planets.length)
    .map((h) => `${h.planets.join(", ")} in house ${h.house}, ${h.sign}`)
    .join("; ");
  return (
    <svg
      viewBox="0 0 480 480"
      width="469"
      height="469"
      role="img"
      aria-label={
        chart.isEmpty
          ? `${name}: not yet computed`
          : `${name}, North Indian chart. Lagna ${chart.lagnaSign}. ${placements}`
      }
    >
      <rect
        x="1"
        y="1"
        width="478"
        height="478"
        rx="6"
        fill="#080705"
        stroke="#8a5e12"
        strokeWidth="1.5"
      />
      <path
        d="M1 1L479 479M479 1L1 479M240 1L479 240L240 479L1 240Z"
        fill="none"
        stroke="#a87c2a"
        strokeWidth="1.25"
      />
      {!chart.isEmpty &&
        centers.map(([x, y], i) => {
          const h = chart.houses.find((v) => v.house === i + 1);
          const planets = h?.planets ?? [];
          return (
            <g key={i} data-house={i + 1}>
              <text
                x={x}
                y={y - 24}
                textAnchor="middle"
                fontSize="13"
                fill="#a39880"
              >
                {h?.sign ? signs.indexOf(h.sign) + 1 : ""}
              </text>
              {i === 0 && (
                <text
                  x={x}
                  y={y - 42}
                  textAnchor="middle"
                  fontSize="12"
                  fill="#ecc56a"
                >
                  Asc
                </text>
              )}
              {Array.from(
                { length: Math.ceil(planets.length / 3) },
                (_, line) => (
                  <text
                    key={line}
                    x={x}
                    y={y + line * 17}
                    textAnchor="middle"
                    fontFamily="Alegreya,Georgia,serif"
                    fontSize="17"
                    fill="#ecc56a"
                  >
                    {planets
                      .slice(line * 3, line * 3 + 3)
                      .map((p) => shortLabel(p))
                      .join(" · ")}
                  </text>
                ),
              )}
            </g>
          );
        })}
      {chart.isEmpty && (
        <>
          <rect x="103" y="212" width="274" height="56" rx="6" fill="#080705" />
          <text
            x="240"
            y="245"
            textAnchor="middle"
            fontSize="17"
            fill="#c4baa0"
          >
            Not yet computed
          </text>
        </>
      )}
    </svg>
  );
}
