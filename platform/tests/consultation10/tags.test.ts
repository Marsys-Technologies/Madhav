import { describe, it, expect, vi, beforeEach } from "vitest";
const { query, guard, getConversation, getUser } = vi.hoisted(() => ({
  query: vi.fn(),
  guard: vi.fn(),
  getConversation: vi.fn(),
  getUser: vi.fn(),
}));
vi.mock("server-only", () => ({}));
vi.mock("@/lib/db/client", () => ({
  query,
  withTransaction: async (
    fn: (client: { query: typeof query }) => Promise<unknown>,
  ) => fn({ query }),
}));
vi.mock("@/lib/auth/chart-page-guard", () => ({
  resolveChartPageAccess: guard,
}));
vi.mock("@/lib/conversations", () => ({ getConversation }));
vi.mock("@/lib/firebase/server", () => ({ getServerUser: getUser }));
import {
  ownedConsultation,
  setConsultationTag,
} from "@/lib/conversations/consultation";
import { PATCH, GET } from "@/app/api/conversations/[id]/consultation/route";
const id = "11111111-1111-4111-8111-111111111111",
  chart = "22222222-2222-4222-8222-222222222222",
  message = "33333333-3333-4333-8333-333333333333";
const ctx = { params: Promise.resolve({ id }) };
const request = (body: unknown, origin = "http://localhost") =>
  new Request(`http://localhost/api/conversations/${id}/consultation`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", origin },
    body: JSON.stringify(body),
  });
beforeEach(() => {
  vi.clearAllMocks();
  getUser.mockResolvedValue({ uid: "owner" });
  getConversation.mockResolvedValue({
    id,
    user_id: "owner",
    chart_id: chart,
    module: "consume",
    archive_reason: null,
    archived_at: null,
  });
  guard.mockResolvedValue({ user: { uid: "owner" }, permission: "view" });
  query.mockResolvedValue({ rows: [{ id }] });
});
describe("Owner-scoped Consultation tags", () => {
  it("enforces both current chart access and conversation ownership even for super-admins", async () => {
    await ownedConsultation(id, "owner");
    expect(getConversation).toHaveBeenCalledWith({
      id,
      userId: "owner",
      isSuperAdmin: false,
    });
    guard.mockResolvedValue({ user: { uid: "owner" }, permission: "deny" });
    expect(await ownedConsultation(id, "owner")).toBeNull();
    expect((await PATCH(request({ tagged: true }), ctx)).status).toBe(404);
  });
  it("refuses unauthenticated, cross-origin, malformed and correction-archived writes", async () => {
    getUser.mockResolvedValue(null);
    expect((await PATCH(request({ tagged: true }), ctx)).status).toBe(401);
    getUser.mockResolvedValue({ uid: "owner" });
    expect(
      (await PATCH(request({ tagged: true }, "https://elsewhere.invalid"), ctx))
        .status,
    ).toBe(403);
    expect((await PATCH(request({ tagged: "true" }), ctx)).status).toBe(400);
    expect((await PATCH(request(null), ctx)).status).toBe(400);
    getConversation.mockResolvedValue({
      id,
      chart_id: chart,
      module: "consume",
      archive_reason: "chart_details_changed",
    });
    expect((await PATCH(request({ tagged: true }), ctx)).status).toBe(409);
    expect(query).not.toHaveBeenCalled();
  });
  it("does not acknowledge a tag when a chart correction races the write", async () => {
    query.mockResolvedValue({ rows: [] });
    expect(
      (await PATCH(request({ tagged: true, messageId: message }), ctx)).status,
    ).toBe(409);
    const [sql, params] = query.mock.calls[0];
    expect(sql).toContain(
      "archive_reason IS DISTINCT FROM 'chart_details_changed'",
    );
    expect(sql).toContain("FOR UPDATE");
    expect(params).toEqual([id, "owner"]);
    expect(query).toHaveBeenCalledTimes(1);
  });
  it("updates a tag independently from writer-owned metadata and timestamps", async () => {
    expect(await setConsultationTag(id, "owner", true, message)).toBe(true);
    expect(query.mock.calls[0][0]).toContain("FOR UPDATE");
    const sql = query.mock.calls[1][0];
    expect(sql).toContain("SET consultation_tagged=$3");
    expect(sql).not.toContain("metadata_json=");
    expect(sql).not.toContain("updated_at=");
  });
  it("does not read messages after revoked chart access", async () => {
    guard.mockResolvedValue(null);
    expect((await GET(new Request("http://localhost"), ctx)).status).toBe(404);
    expect(query).not.toHaveBeenCalled();
  });
});
