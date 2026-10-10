// Test-only browser fixture. Imports real UI components; no auth bypass or data writes.
import { createRoot } from "react-dom/client";
import { JourneyShell } from "@/components/journey1/JourneyShell";
import { PageTitle } from "@/components/journey1/Titles";
import { VargaChart } from "@/components/journey1/VargaChart";
import { ChartNav } from "@/components/journey1/ChartNav";
import { NewClientForm } from "@/components/clients/NewClientForm";
import { EditClientForm } from "@/components/clients/EditClientForm";
import type { ForensicChart } from "@/lib/forensic/snapshot";
import "@/app/globals.css";
import "@/app/journey1.css";
import "@/components/profile/jataka-workspace.css";
const screen = new URLSearchParams(location.search).get("screen") ?? "chart";
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
const fixture: ForensicChart = {
  chartId: "fixture-chart",
  lagnaSign: "Aries",
  lagnaDegreeDms: "10°",
  houses: signs.map((sign, i) => ({
    house: i + 1,
    sign,
    planets:
      i === 0
        ? ["Sun", "Moon", "Mars"]
        : i === 2
          ? ["Mercury"]
          : i === 6
            ? ["Jupiter", "Venus", "Saturn"]
            : i === 8
              ? ["Rahu"]
              : i === 11
                ? ["Ketu"]
                : [],
  })),
  topYogas: [],
  currentDasha: null,
  isEmpty: false,
};
const empty = { ...fixture, isEmpty: true };
const chart = {
  id: "fixture-chart",
  name: "Fictional Native",
  preferred_name: null,
  subject_name: null,
  birth_date: "1990-01-01",
  birth_time: "06:00:00",
  birth_place: "Fictional birthplace",
  birth_lat: 20,
  birth_lng: 85,
  timezone_id: "Asia/Kolkata",
  tz_offset_hours: 5.5,
  ayanamshas: ["lahiri", "true_chitra", "kp", "raman", "surya_siddhanta"],
};
createRoot(document.getElementById("root")!).render(
  <JourneyShell
    user={{ uid: "fixture-only", name: "Fictional User" }}
    role="super_admin"
  >
    <div
      style={{
        padding: 8,
        color: "#f3eee2",
        background: "#211909",
        fontSize: 14,
      }}
    >
      Component test · fictional data · submissions disabled{" "}
      <a href="?screen=chart">Chart</a> · <a href="?screen=new">New form</a> ·{" "}
      <a href="?screen=edit">Edit form</a>
    </div>
    {screen === "new" ? (
      <NewClientForm />
    ) : screen === "edit" ? (
      <EditClientForm chart={chart} ayanamshaEditPolicy="block_all" />
    ) : (
      <div className="j1-container">
        <section className="j1-chart-hero">
          <VargaChart
            charts={[
              fixture,
              {
                ...fixture,
                lagnaSign: "Leo",
                houses: fixture.houses.map((house, i) => ({
                  ...house,
                  sign: signs[(i + 4) % 12],
                })),
              },
              empty,
            ]}
            ayanamsha="Lahiri · Chitrapaksha"
          />
          <div className="j1-chart-info">
            <PageTitle name="overview" />
            <h2>Fictional Native</h2>
            <p className="j1-note">Chart rendering fixture</p>
          </div>
        </section>
        <ChartNav chartId="fixture-chart" canBuild />
      </div>
    )}
  </JourneyShell>,
);
