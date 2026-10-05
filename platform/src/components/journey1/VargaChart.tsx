"use client";
import { useState } from "react";
import { NorthIndianChart } from "./NorthIndianChart";
import type { ForensicChart } from "@/lib/forensic/snapshot";
const VARGAS = ["D1 · Rāśi", "D9 · Navāṃśa", "D10 · Daśāṃśa"];
export function VargaChart({
  charts,
  ayanamsha,
}: {
  charts: [ForensicChart, ForensicChart, ForensicChart];
  ayanamsha: string;
}) {
  const [selected, setSelected] = useState(0);
  return (
    <div className="j1-chart-box" data-testid="varga-chart">
      <NorthIndianChart chart={charts[selected]} name={VARGAS[selected]} />
      <div className="j1-chart-slider">
        <label htmlFor="varga-slider" className="j1-note">
          {VARGAS[selected]} <span style={{ float: "right" }}>{ayanamsha}</span>
        </label>
        <input
          id="varga-slider"
          type="range"
          min={0}
          max={2}
          step={1}
          value={selected}
          aria-label="Divisional chart"
          aria-valuetext={VARGAS[selected]}
          onChange={(e) => setSelected(Number(e.target.value))}
        />
        <div className="j1-chart-slider-labels">
          {VARGAS.map((name, i) => (
            <button
              key={name}
              type="button"
              aria-pressed={selected === i}
              onClick={() => setSelected(i)}
            >
              {name}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
