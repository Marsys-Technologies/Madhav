import { getServerUser } from "@/lib/firebase/server";
import { query } from "@/lib/db/client";
import {
  ownedConsultation,
  consultationMessages,
  setConsultationTag,
  uuidLike,
} from "@/lib/conversations/consultation";
import {
  isCorrectionArchived,
  archivedReadOnlyResponse,
} from "@/lib/conversations/readOnly";
import { res } from "@/lib/errors";

export async function GET(
  _request: Request,
  ctx: { params: Promise<{ id: string }> },
) {
  const user = await getServerUser();
  if (!user) return res.unauthenticated();
  const { id } = await ctx.params;
  if (!uuidLike.test(id)) return res.badRequest("Valid conversation required");
  try {
    const conversation = await ownedConsultation(id, user.uid);
    if (!conversation) return res.notFound("conversation");
    const messages = await consultationMessages(id);
    // Receipt validation controls optional modern metadata, not the availability
    // of a durable answer written before receipts were introduced.
    if (!messages.some((m) => m.role === "assistant"))
      return res.notFound("consultation");
    const { rows } = await query(
      "SELECT consultation_tagged AS tagged FROM conversations WHERE id=$1",
      [id],
    );
    return Response.json(
      {
        conversation: { ...conversation, tagged: rows[0]?.tagged === true },
        messages,
        readOnly:
          isCorrectionArchived(conversation) || !!conversation.archived_at,
      },
      { headers: { "Cache-Control": "private, no-store" } },
    );
  } catch {
    return res.dbError();
  }
}

export async function PATCH(
  request: Request,
  ctx: { params: Promise<{ id: string }> },
) {
  const user = await getServerUser();
  if (!user) return res.unauthenticated();
  const origin = request.headers.get("origin");
  if (origin && origin !== new URL(request.url).origin) return res.forbidden();
  const { id } = await ctx.params;
  if (!uuidLike.test(id)) return res.badRequest("Valid conversation required");
  let body: { tagged?: unknown; messageId?: unknown };
  try {
    body = await request.json();
  } catch {
    return res.badRequest("Invalid body");
  }
  if (
    !body ||
    typeof body !== "object" ||
    Array.isArray(body) ||
    typeof body.tagged !== "boolean" ||
    (body.messageId !== undefined &&
      (typeof body.messageId !== "string" || !uuidLike.test(body.messageId)))
  )
    return res.badRequest("Invalid tag");
  try {
    const conversation = await ownedConsultation(id, user.uid);
    if (!conversation) return res.notFound("conversation");
    if (isCorrectionArchived(conversation) || conversation.archived_at)
      return archivedReadOnlyResponse();
    const updated = await setConsultationTag(
      id,
      user.uid,
      body.tagged,
      body.messageId as string | undefined,
    );
    if (!updated)
      return Response.json(
        { error: "This conversation or answer is unavailable for tagging." },
        { status: 409 },
      );
    return Response.json({ ok: true, tagged: body.tagged });
  } catch {
    return res.dbError();
  }
}
