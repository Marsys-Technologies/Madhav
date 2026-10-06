import { z } from "zod";
import { accountOwner, PRIVATE_HEADERS } from "@/lib/account/guard";
import { query } from "@/lib/db/client";
const patch = z.object({ name: z.string().trim().min(1).max(100) }).strict();
export async function GET() {
  const ctx = await accountOwner();
  if (ctx instanceof Response) return ctx;
  try {
    const { rows } = await query(
      "SELECT name,email,username FROM profiles WHERE id=$1 AND status='active'",
      [ctx.user.uid],
    );
    if (!rows[0])
      return Response.json({ error: "account_inactive" }, { status: 403 });
    const { name, email, username } = rows[0];
    return Response.json(
      { profile: { name, email, username } },
      { headers: PRIVATE_HEADERS },
    );
  } catch {
    return Response.json({ error: "account_unavailable" }, { status: 503 });
  }
}
export async function PATCH(request: Request) {
  const ctx = await accountOwner(request);
  if (ctx instanceof Response) return ctx;
  const body = patch.safeParse(await request.json().catch(() => null));
  if (!body.success)
    return Response.json({ error: "invalid_profile" }, { status: 400 });
  try {
    const { rows } = await query(
      "UPDATE profiles SET name=$1,updated_at=now() WHERE id=$2 AND status='active' RETURNING name,email,username",
      [body.data.name, ctx.user.uid],
    );
    if (!rows[0])
      return Response.json({ error: "account_inactive" }, { status: 403 });
    return Response.json({ profile: rows[0] }, { headers: PRIVATE_HEADERS });
  } catch {
    return Response.json({ error: "account_unavailable" }, { status: 503 });
  }
}
