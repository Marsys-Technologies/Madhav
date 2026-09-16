import { describe, it, expect } from "vitest";
import {
  BHAVAT_BHAVAM_MAP,
  BHAVAT_BHAVAM_QUALIFICATION_STATE,
  BHAVAT_BHAVAM_RESTRAINTS,
  BHAVAT_BHAVAM_SEMANTIC_RELEASE_ID,
  BHAVAT_BHAVAM_SLICE_ID,
  ODD_HOUSES,
  EVEN_HOUSES,
  derivedHouses,
  isOddHouse,
} from "../bhavat_bhavam_map";
import {
  AmbiguousAddressResolutionError,
  L0_SEMANTIC_RELEASE_ID,
  grahaCodeOf,
  grahaIdentityOf,
} from "../../retrieval/graha_labels";

describe("bhavat_bhavam_map", () => {
  it("has all 12 houses present as keys", () => {
    expect(
      Object.keys(BHAVAT_BHAVAM_MAP)
        .map(Number)
        .sort((a, b) => a - b),
    ).toEqual(Array.from({ length: 12 }, (_, i) => i + 1));
  });

  it.each([
    [1, [1, 7]],
    [3, [2, 8]],
    [5, [3, 9]],
    [7, [4, 10]],
    [9, [5, 11]],
    [11, [6, 12]],
  ])("odd house %i derives %j (brief verbatim map)", (house, expected) => {
    expect(derivedHouses(house)).toEqual(expected);
  });

  it.each([2, 4, 6, 8, 10, 12])("even house %i receives nothing", (house) => {
    expect(derivedHouses(house)).toEqual([]);
  });

  it("odd/even partition is exhaustive and disjoint", () => {
    const all = new Set([...ODD_HOUSES, ...EVEN_HOUSES]);
    expect(all.size).toBe(12);
    expect(new Set(ODD_HOUSES).size + new Set(EVEN_HOUSES).size).toBe(12);
  });

  it("isOddHouse agrees with the ODD_HOUSES/EVEN_HOUSES partition", () => {
    for (const h of ODD_HOUSES) expect(isOddHouse(h)).toBe(true);
    for (const h of EVEN_HOUSES) expect(isOddHouse(h)).toBe(false);
  });

  it("throws on an invalid house number", () => {
    expect(() => derivedHouses(0)).toThrow();
    expect(() => derivedHouses(13)).toThrow();
  });

  it("preserves the map but exposes its honest L0 qualification and restraints", () => {
    expect(BHAVAT_BHAVAM_SLICE_ID).toBe("L0-SLICE-RESOURCE-CONFIG-01");
    expect(BHAVAT_BHAVAM_QUALIFICATION_STATE).toBe("UNQUALIFIED_SOURCE");
    expect(BHAVAT_BHAVAM_RESTRAINTS).toEqual({
      never_generator: true,
      no_chaining: true,
      never_outranks_primary: true,
    });
    expect(BHAVAT_BHAVAM_SEMANTIC_RELEASE_ID).toBe(L0_SEMANTIC_RELEASE_ID);
  });

  it("uses the same released aliases and preserves explicit node variants", () => {
    expect(grahaCodeOf("Sūrya")).toBe("SUN");
    expect(grahaCodeOf("Ravi")).toBe("SUN");
    expect(grahaCodeOf("RAH_MEAN")).toBe("RAH_MEAN");
    expect(grahaCodeOf("RAH_TRUE")).toBe("RAH_TRUE");
    expect(grahaCodeOf("KET_MEAN")).toBe("KET_MEAN");
    expect(grahaCodeOf("KET_TRUE")).toBe("KET_TRUE");
    expect(grahaIdentityOf("Rahu").legacy_default).toBe(true);
  });

  it("fails closed for ambiguous and unknown identities", () => {
    expect(() => grahaCodeOf("lunar node")).toThrow(
      AmbiguousAddressResolutionError,
    );
    expect(() => grahaCodeOf("Pluto")).toThrow();
  });
});
