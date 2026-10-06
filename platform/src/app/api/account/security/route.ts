import { NextResponse } from "next/server";
import { z } from "zod";
import { getServerUserWithProfile } from "@/lib/auth/access-control";
import { adminAuth } from "@/lib/firebase/server";
import { query } from "@/lib/db/client";
const input = z.object({ idToken: z.string().min(1).max(10000) }).strict();
export async function POST(request: Request) {
  const origin = request.headers.get("origin");
  if (origin && origin !== new URL(request.url).origin)
    return NextResponse.json({ error: "forbidden" }, { status: 403 });
  const body = input.safeParse(await request.json().catch(() => null));
  if (!body.success)
    return NextResponse.json({ error: "invalid_request" }, { status: 400 });
  try {
    const token = await adminAuth.verifyIdToken(body.data.idToken, true);
    const age = Math.floor(Date.now() / 1000) - token.auth_time;
    const ctx = await getServerUserWithProfile();
    if (
      !Number.isFinite(age) ||
      age < 0 ||
      age > 300 ||
      (ctx && ctx.user.uid !== token.uid)
    )
      return NextResponse.json(
        { error: "recent_authentication_required" },
        { status: 403 },
      );
    // A password change may already revoke the old session. A fresh own-user token
    // is the identity proof in that case; never accept a uid supplied in the body.
    const active = ctx
      ? ctx.profile.status === "active"
      : (await query("SELECT status FROM profiles WHERE id=$1", [token.uid]))
          .rows[0]?.status === "active";
    if (!active)
      return NextResponse.json({ error: "account_inactive" }, { status: 403 });
    await adminAuth.revokeRefreshTokens(token.uid);
    const r = NextResponse.json(
      { ok: true },
      { headers: { "Cache-Control": "private, no-store" } },
    );
    r.cookies.set("__session", "", {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 0,
      path: "/",
    });
    return r;
  } catch {
    return NextResponse.json(
      { error: "sign_out_unavailable" },
      { status: 503 },
    );
  }
}
