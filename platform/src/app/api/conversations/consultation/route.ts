import { getServerUser } from "@/lib/firebase/server";
import {
  consultationAccess,
  consultationHistory,
  uuidLike,
} from "@/lib/conversations/consultation";
import { res } from "@/lib/errors";

export async function GET(request: Request) {
  const user = await getServerUser();
  if (!user) return res.unauthenticated();
  const chartId = new URL(request.url).searchParams.get("chartId") ?? "";
  if (!uuidLike.test(chartId)) return res.badRequest("Valid chartId required");
  try {
    const access = await consultationAccess(chartId);
    if (!access || access.user.uid !== user.uid) return res.forbidden();
    return Response.json(
      { conversations: await consultationHistory(chartId, user.uid) },
      { headers: { "Cache-Control": "private, no-store" } },
    );
  } catch {
    return res.dbError();
  }
}
