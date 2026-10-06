import { z } from "zod";
export const preferenceSchema = z
  .object({
    titles: z.enum(["en", "sa"]),
    navPinned: z.boolean(),
    historyPinned: z.boolean(),
    evidencePinned: z.boolean(),
    grounding: z.enum(["right", "inline"]),
    reducedMotion: z.boolean(),
    textScale: z.union([
      z.literal(0.875),
      z.literal(1),
      z.literal(1.125),
      z.literal(1.25),
    ]),
    readingDepth: z.enum(["deep", "auto", "quick", "standard"]),
  })
  .strict();
export type AccountPreferences = z.infer<typeof preferenceSchema>;
export const DEFAULT_PREFERENCES: AccountPreferences = {
  titles: "sa",
  navPinned: false,
  historyPinned: false,
  evidencePinned: false,
  grounding: "right",
  reducedMotion: false,
  textScale: 1,
  readingDepth: "deep",
};
export const preferencePatchSchema = preferenceSchema
  .partial()
  .refine((value) => Object.keys(value).length > 0);
export function readPreferences(value: unknown): AccountPreferences {
  const stored =
    typeof value === "object" && value !== null && !Array.isArray(value)
      ? value
      : {};
  return {
    ...DEFAULT_PREFERENCES,
    ...preferenceSchema.partial().strip().parse(stored),
  };
}
