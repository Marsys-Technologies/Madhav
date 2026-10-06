import { accountOwner, PRIVATE_HEADERS } from "@/lib/account/guard";
import {
  preferencePatchSchema,
  readPreferences,
} from "@/lib/account/preference-types";
import { query } from "@/lib/db/client";
export async function GET() {
  const ctx = await accountOwner();
  if (ctx instanceof Response) return ctx;
  try {
    const { rows } = await query(
      "SELECT account_preferences FROM profiles WHERE id=$1 AND status='active'",
      [ctx.user.uid],
    );
    if (!rows[0])
      return Response.json({ error: "account_inactive" }, { status: 403 });
    return Response.json(
      { preferences: readPreferences(rows[0].account_preferences) },
      { headers: PRIVATE_HEADERS },
    );
  } catch {
    return Response.json({ error: "preferences_unavailable" }, { status: 503 });
  }
}
export async function PATCH(request: Request) {
  const ctx = await accountOwner(request);
  if (ctx instanceof Response) return ctx;
  const body = preferencePatchSchema.safeParse(
    await request.json().catch(() => null),
  );
  if (!body.success)
    return Response.json({ error: "invalid_preferences" }, { status: 400 });
  try {
    const { rows } = await query(
      "UPDATE profiles SET account_preferences=account_preferences || $1::jsonb,updated_at=now() WHERE id=$2 AND status='active' RETURNING account_preferences",
      [JSON.stringify(body.data), ctx.user.uid],
    );
    if (!rows[0])
      return Response.json({ error: "account_inactive" }, { status: 403 });
    return Response.json(
      { preferences: readPreferences(rows[0].account_preferences) },
      { headers: PRIVATE_HEADERS },
    );
  } catch {
    return Response.json({ error: "preferences_unavailable" }, { status: 503 });
  }
}
