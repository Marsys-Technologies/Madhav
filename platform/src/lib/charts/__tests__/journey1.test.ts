import { it, expect, vi, beforeEach } from "vitest";
const { q } = vi.hoisted(() => ({ q: vi.fn() }));
vi.mock("server-only", () => ({}));
vi.mock("@/lib/db/client", () => ({ query: q }));
import {
  divisionalChart,
  getJourney1ChartData,
  journey1Frame,
  journey1CrossCheckFrames,
  journey1FrameLabel,
} from "../journey1";
beforeEach(() => {
  q.mockReset();
});
it("reads divisionals in the chart’s own frame and scoped authoritative transit generation", async () => {
  q.mockImplementation(async (sql: string) => ({
    rows: sql.includes("divisionals")
      ? [
          { varga: "D9", graha: "Lagna", sign: "Leo", degree_in_sign: 7 },
          { varga: "D9", graha: "Moon", sign: "Aries", degree_in_sign: 13 },
        ]
      : [],
  }));
  const r = await getJourney1ChartData("chart-a", "raman");
  expect(r.d9.houses[8].planets).toEqual(["Moon"]);
  expect(r.d9.lagnaSign).toBe("Leo");
  expect(r.d10.isEmpty).toBe(true);
  expect(q.mock.calls[0][1]).toEqual(["chart-a", "raman"]);
  expect(q.mock.calls[1][1]).toEqual(["chart-a"]);
  expect(q.mock.calls[1][0]).toContain("authoritative_generation");
});
it("keeps missing lagna and failed source reads honestly empty", async () => {
  expect(
    divisionalChart("chart-b", [
      { varga: "D10", graha: "Sun", sign: "Aries", degree_in_sign: 1 },
    ]).isEmpty,
  ).toBe(true);
  q.mockRejectedValue(new Error("offline"));
  const r = await getJourney1ChartData("chart-b");
  expect(r.d9.isEmpty).toBe(true);
  expect(r.windows).toEqual([]);
  expect(r.flags).toEqual(
    expect.arrayContaining(["divisionals_unavailable", "windows_unavailable"]),
  );
});

it("always serves Lahiri (primary for every chart), even when the stored selection excludes it", () => {
  expect(journey1Frame("lahiri,true_chitra,kp")).toBe("lahiri_chitrapaksha");
  expect(journey1Frame("kp,raman")).toBe("lahiri_chitrapaksha");
  expect(journey1Frame("surya_siddhanta")).toBe("lahiri_chitrapaksha");
  expect(journey1Frame("raman")).toBe("lahiri_chitrapaksha");
  expect(journey1Frame("true_chitra,krishnamurti")).toBe("lahiri_chitrapaksha");
  expect(journey1Frame(null)).toBe("lahiri_chitrapaksha");
  expect(journey1Frame("")).toBe("lahiri_chitrapaksha");
  expect(journey1Frame("not_an_ayanamsha")).toBe("lahiri_chitrapaksha");
});

it("labels the primary frame and keeps the cross-check set as the other selected stored ids", () => {
  expect(journey1FrameLabel(journey1Frame("kp"))).toBe("Lahiri · Chitrapaksha (primary)");
  expect(journey1CrossCheckFrames("lahiri,true_chitra,kp")).toEqual(["true_chitra", "krishnamurti"]);
  expect(journey1CrossCheckFrames("kp,raman")).toEqual(["krishnamurti", "raman"]);
  expect(journey1CrossCheckFrames("surya_siddhanta")).toEqual(["surya_siddhanta_classical"]);
  expect(journey1CrossCheckFrames("lahiri")).toEqual([]);
  expect(journey1CrossCheckFrames(null)).toEqual([]);
  expect(journey1CrossCheckFrames("junk,raman")).toEqual(["raman"]);
});
