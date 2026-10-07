import "server-only";
import { getServerUserWithProfile } from "@/lib/auth/access-control";
export async function accountOwner(request?: Request) {
  if (request) {
    const origin = request.headers.get("origin");
    if (origin && origin !== new URL(request.url).origin)
      return Response.json({ error: "forbidden" }, { status: 403 });
  }
  const ctx = await getServerUserWithProfile();
  if (!ctx) return Response.json({ error: "unauthorized" }, { status: 401 });
  if (ctx.profile.status !== "active")
    return Response.json({ error: "account_inactive" }, { status: 403 });
  return ctx;
}
export const PRIVATE_HEADERS = { "Cache-Control": "private, no-store" };
