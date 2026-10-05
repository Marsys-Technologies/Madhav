import { getServerUserWithProfile } from "@/lib/auth/access-control";
import { validateUsername } from "@/lib/auth/username";
import { query } from "@/lib/db/client";
import { writeAuditLog } from "@/lib/admin/audit";

export async function GET(request: Request) {
  const ctx = await getServerUserWithProfile();
  if (!ctx || ctx.profile.status !== "active")
    return Response.json({ error: "unauthorized" }, { status: 401 });
  const username =
    new URL(request.url).searchParams.get("username")?.trim().toLowerCase() ??
    "";
  const error = validateUsername(username);
  if (error) return Response.json({ available: false, error }, { status: 400 });
  try {
    const { rows } = await query<{ id: string }>(
      "SELECT id FROM profiles WHERE lower(username)=lower($1) AND id<>$2 LIMIT 1",
      [username, ctx.user.uid],
    );
    return Response.json(
      { available: rows.length === 0 },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch {
    return Response.json({ error: "temporarily_unavailable" }, { status: 503 });
  }
}
export async function PATCH(request: Request) {
  const origin = request.headers.get("origin");
  if (origin && origin !== new URL(request.url).origin)
    return Response.json({ error: "forbidden" }, { status: 403 });
  const ctx = await getServerUserWithProfile();
  if (!ctx || ctx.profile.status !== "active")
    return Response.json({ error: "unauthorized" }, { status: 401 });
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Invalid request." }, { status: 400 });
  }
  const submittedUsername =
    body && typeof body === "object" && !Array.isArray(body)
      ? (body as { username?: unknown }).username
      : undefined;
  if (typeof submittedUsername !== "string")
    return Response.json({ error: "Username is required." }, { status: 400 });
  const username = submittedUsername.trim().toLowerCase();
  const error = validateUsername(username);
  if (error) return Response.json({ error }, { status: 400 });
  try {
    const { rows } = await query<{ id: string }>(
      "UPDATE profiles SET username=$1,updated_at=now() WHERE id=$2 AND status='active' RETURNING id",
      [username, ctx.user.uid],
    );
    if (!rows.length)
      return Response.json(
        { error: "Account is unavailable." },
        { status: 403 },
      );
  } catch (err) {
    if ((err as { code?: string }).code === "23505")
      return Response.json(
        { error: "Username is already taken. Please choose another." },
        { status: 409 },
      );
    return Response.json(
      { error: "Could not save username. Please try again." },
      { status: 503 },
    );
  }
  await writeAuditLog(ctx.user.uid, "edit_username", ctx.user.uid, {
    new_username: username,
    self_service: true,
  });
  return Response.json({ ok: true });
}
