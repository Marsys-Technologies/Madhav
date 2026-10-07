import { z } from "zod";
export const PERSONAL_ACTIVITY_KEYS = [
  "from",
  "to",
  "channel",
  "purpose",
  "provider",
  "model",
  "connectionId",
  "aggregation",
] as const;
const schema = z.object({
  from: z.string().datetime({ offset: true }),
  to: z.string().datetime({ offset: true }),
  channel: z
    .enum(["web", "mcp", "api", "backend", "scheduled", "unknown"])
    .optional(),
  purpose: z
    .enum([
      "customer",
      "admin_test",
      "validation",
      "evaluation",
      "background",
      "legacy",
    ])
    .optional(),
  provider: z.string().max(64).optional(),
  model: z.string().max(256).optional(),
  connectionId: z.string().uuid().optional(),
  aggregation: z
    .enum(["transport", "cli_aggregate", "legacy_aggregate"])
    .optional(),
});
/** Only personal filters survive; the API supplies the authenticated owner. */
export function personalActivityFilters(
  search: Pick<URLSearchParams, "get">,
  now = new Date(),
) {
  const raw: Record<string, string> = {
    from:
      search.get("from") ??
      new Date(now.getTime() - 30 * 86400000).toISOString(),
    to: search.get("to") ?? now.toISOString(),
  };
  for (const key of PERSONAL_ACTIVITY_KEYS.slice(2)) {
    const value = search.get(key)?.trim();
    if (value) raw[key] = value;
  }
  const value = schema.parse(raw),
    duration = Date.parse(value.to) - Date.parse(value.from);
  if (duration <= 0 || duration > 90 * 86400000)
    throw Error("Choose a valid period of up to 90 days.");
  return new URLSearchParams(value as Record<string, string>);
}
