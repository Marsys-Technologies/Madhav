import { it, expect, vi, beforeEach } from "vitest";
const { q } = vi.hoisted(() => ({ q: vi.fn() }));
vi.mock("server-only", () => ({}));
vi.mock("@/lib/db/client", () => ({ query: q }));
import {
  divisionalChart,
  getJourney1ChartData,
  journey1Frame,
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

it("uses the chosen chart form frame's stored L1 key without falling back to a different computation", () => {
  expect(journey1Frame("lahiri,true_chitra,kp")).toBe("lahiri_chitrapaksha");
  expect(journey1Frame("kp,raman")).toBe("krishnamurti");
  expect(journey1Frame("surya_siddhanta")).toBe("surya_siddhanta_classical");
  expect(journey1Frame("raman")).toBe("raman");
});
