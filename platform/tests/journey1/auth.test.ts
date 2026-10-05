import { beforeEach, describe, it, expect, vi } from "vitest";
const { q, ctx, audit } = vi.hoisted(() => ({
  q: vi.fn(),
  ctx: vi.fn(),
  audit: vi.fn(),
}));
vi.mock("server-only", () => ({}));
vi.mock("@/lib/db/client", () => ({ query: q }));
vi.mock("@/lib/auth/access-control", () => ({ getServerUserWithProfile: ctx }));
vi.mock("@/lib/admin/audit", () => ({ writeAuditLog: audit }));
import { POST as recover } from "@/app/api/auth/recover/route";
import { GET, PATCH } from "@/app/api/account/username/route";
import { __resetRpmCountersForTest } from "@/lib/mcp/rate_limiter_core";
const request = (
  body: unknown,
  path = "/api/auth/recover",
  origin = "http://localhost",
) =>
  new Request("http://localhost" + path, {
    method: "POST",
    headers: { "Content-Type": "application/json", origin },
    body: JSON.stringify(body),
  });
beforeEach(() => {
  vi.clearAllMocks();
  __resetRpmCountersForTest();
  vi.stubEnv("NEXT_PUBLIC_FIREBASE_API_KEY", "test-public-key");
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}")));
  q.mockResolvedValue({ rows: [] });
  ctx.mockResolvedValue({
    user: { uid: "approved-user" },
    profile: { status: "active" },
  });
});
describe("username/email recovery", () => {
  it.each(["native_name", "fictional@example.invalid"])(
    "uses one generic response for match and non-match: %s",
    async (identifier) => {
      q.mockResolvedValueOnce({
        rows: [{ email: "fictional@example.invalid" }],
      }).mockResolvedValueOnce({ rows: [] });
      const known = await recover(request({ identifier }));
      const unknown = await recover(request({ identifier }));
      expect(known.status).toBe(200);
      expect(await known.json()).toEqual(await unknown.json());
      expect(q.mock.calls[0][1]).toEqual([identifier]);
      expect(q.mock.calls[0][0]).toContain("status='active'");
      const sent = JSON.parse(
        vi.mocked(fetch).mock.calls[0][1]!.body as string,
      );
      expect(sent.requestType).toBe("PASSWORD_RESET");
      expect(sent.email).toBe("fictional@example.invalid");
    },
  );
  it("does not turn account-not-found into an existence oracle", async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify({ error: { message: "EMAIL_NOT_FOUND" } }), {
        status: 400,
      }),
    );
    expect((await recover(request({ identifier: "missing" }))).status).toBe(
      200,
    );
  });
  it("rejects malformed/empty identifiers without a provider call", async () => {
    for (const identifier of ["", {}, "a".repeat(255)])
      expect((await recover(request({ identifier }))).status).toBe(400);
    expect(fetch).not.toHaveBeenCalled();
  });
  it("reports provider outage without claiming delivery", async () => {
    vi.mocked(fetch).mockRejectedValue(new Error("offline"));
    expect((await recover(request({ identifier: "test" }))).status).toBe(503);
  });
  it("blocks cross-origin recovery and limits repeated attempts", async () => {
    expect(
      (
        await recover(
          request({ identifier: "test" }, undefined, "https://foreign.test"),
        )
      ).status,
    ).toBe(403);
    for (let i = 0; i < 10; i++) await recover(request({ identifier: "test" }));
    expect((await recover(request({ identifier: "test" }))).status).toBe(429);
  });
});
describe("approved self-service username", () => {
  it.each([null, [], 1, "text", { username: null }])(
    "rejects malformed JSON values without an account write: %s",
    async (body) => {
      expect((await PATCH(request(body, "/api/account/username"))).status).toBe(
        400,
      );
      expect(q).not.toHaveBeenCalled();
    },
  );
  it("requires an active verified session", async () => {
    ctx.mockResolvedValue(null);
    expect(
      (await PATCH(request({ username: "my-name" }, "/api/account/username")))
        .status,
    ).toBe(401);
    expect(q).not.toHaveBeenCalled();
  });
  it("checks availability excluding only the authenticated principal", async () => {
    q.mockResolvedValue({ rows: [{ id: "other-user" }] });
    const r = await GET(
      new Request("http://localhost/api/account/username?username=Taken"),
    );
    expect(await r.json()).toEqual({ available: false });
    expect(q.mock.calls[0][1]).toEqual(["taken", "approved-user"]);
  });
  it("binds the normalized name to the caller, ignoring a supplied user ID", async () => {
    q.mockResolvedValue({ rows: [{ id: "approved-user" }] });
    const r = await PATCH(
      request(
        { username: "My_Name", user_id: "victim" },
        "/api/account/username",
      ),
    );
    expect(r.status).toBe(200);
    expect(q.mock.calls[0][1]).toEqual(["my_name", "approved-user"]);
    expect(audit).toHaveBeenCalledWith(
      "approved-user",
      "edit_username",
      "approved-user",
      expect.anything(),
    );
  });
  it("handles the unique-index race without overwriting another account", async () => {
    q.mockRejectedValue({ code: "23505" });
    expect(
      (
        await PATCH(
          request({ username: "raced-name" }, "/api/account/username"),
        )
      ).status,
    ).toBe(409);
    expect(audit).not.toHaveBeenCalled();
  });
  it("rejects cross-origin and invalid usernames", async () => {
    expect(
      (
        await PATCH(
          request(
            { username: "test" },
            "/api/account/username",
            "https://foreign.test",
          ),
        )
      ).status,
    ).toBe(403);
    expect(
      (
        await PATCH(
          request({ username: "not a name" }, "/api/account/username"),
        )
      ).status,
    ).toBe(400);
    expect(q).not.toHaveBeenCalled();
  });
});
