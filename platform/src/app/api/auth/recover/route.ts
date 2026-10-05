import { createHash } from "node:crypto";
import { query } from "@/lib/db/client";
import { checkRpm } from "@/lib/mcp/rate_limiter_core";

// Resolve on the server: recovery never returns an account's email or existence.
// Firebase's sendOobCode delivers the email; generatePasswordResetLink alone does not.
export async function POST(request: Request) {
  const origin = request.headers.get("origin");
  if (origin && origin !== new URL(request.url).origin)
    return Response.json({ error: "forbidden" }, { status: 403 });
  const ip =
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ??
    "anonymous";
  const rate = checkRpm(
    `account-recovery:${createHash("sha256").update(ip).digest("hex")}`,
    10,
  );
  if (!rate.allowed)
    return Response.json(
      { error: "rate_limited" },
      {
        status: 429,
        headers: { "Retry-After": String(rate.retry_after_seconds ?? 60) },
      },
    );
  let identifier: unknown;
  try {
    identifier = (await request.json()).identifier;
  } catch {
    return Response.json({ error: "invalid_request" }, { status: 400 });
  }
  if (
    typeof identifier !== "string" ||
    !identifier.trim() ||
    identifier.length > 254
  )
    return Response.json({ error: "invalid_identifier" }, { status: 400 });
  const key =
    process.env.FIREBASE_WEB_API_KEY ??
    process.env.NEXT_PUBLIC_FIREBASE_API_KEY;
  if (!key)
    return Response.json({ error: "temporarily_unavailable" }, { status: 503 });
  try {
    const { rows } = await query<{ email: string | null }>(
      "SELECT email FROM profiles WHERE status='active' AND (lower(username)=lower($1) OR lower(email)=lower($1)) ORDER BY id LIMIT 1",
      [identifier.trim()],
    );
    // Submit even on a non-match, keeping the provider/error path identical.
    // No message can be delivered to the reserved .invalid domain.
    const email =
      rows[0]?.email ?? "account-recovery-unmatched@example.invalid";
    const response = await fetch(
      `https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key=${encodeURIComponent(key)}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ requestType: "PASSWORD_RESET", email }),
        signal: AbortSignal.timeout(10000),
      },
    );
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      if (!["EMAIL_NOT_FOUND", "INVALID_EMAIL"].includes(body.error?.message))
        return Response.json(
          { error: "temporarily_unavailable" },
          { status: 503 },
        );
    }
    return Response.json(
      { ok: true },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch {
    return Response.json({ error: "temporarily_unavailable" }, { status: 503 });
  }
}
