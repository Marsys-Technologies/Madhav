import { beforeEach, describe, expect, it, vi } from "vitest";
const h = vi.hoisted(() => ({
  ctx: vi.fn(),
  query: vi.fn(),
  verify: vi.fn(),
  revoke: vi.fn(),
}));
vi.mock("@/lib/auth/access-control", () => ({
  getServerUserWithProfile: h.ctx,
}));
vi.mock("@/lib/db/client", () => ({ query: h.query }));
vi.mock("@/lib/firebase/server", () => ({
  adminAuth: { verifyIdToken: h.verify, revokeRefreshTokens: h.revoke },
}));
import {
  GET as profile,
  PATCH as saveProfile,
} from "@/app/api/account/profile/route";
import {
  GET as preferences,
  PATCH as savePreferences,
} from "@/app/api/account/preferences/route";
import { POST as security } from "@/app/api/account/security/route";
const request = (
  path: string,
  body: unknown,
  origin = "https://example.test",
) =>
  new Request(`https://example.test/api/account/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", origin },
    body: JSON.stringify(body),
  });
beforeEach(() => {
  vi.resetAllMocks();
  h.ctx.mockResolvedValue({
    user: { uid: "alice" },
    profile: { status: "active", role: "guest" },
  });
  h.query.mockResolvedValue({
    rows: [
      {
        name: "Alice",
        email: "alice@example.test",
        username: "alice",
        account_preferences: { titles: "en", navPinned: false },
      },
    ],
  });
  h.verify.mockResolvedValue({
    uid: "alice",
    auth_time: Math.floor(Date.now() / 1000),
  });
  h.revoke.mockResolvedValue(undefined);
});
describe("personal account routes", () => {
  it("denies an unauthenticated profile", async () => {
    h.ctx.mockResolvedValue(null);
    expect((await profile()).status).toBe(401);
  });
  it("denies inactive preferences", async () => {
    h.ctx.mockResolvedValue({
      user: { uid: "alice" },
      profile: { status: "disabled" },
    });
    expect((await preferences()).status).toBe(403);
  });
  it("returns only identity fields from profile", async () => {
    const r = await profile();
    expect(await r.json()).toEqual({
      profile: {
        name: "Alice",
        email: "alice@example.test",
        username: "alice",
      },
    });
  });
  it("rejects an email/owner modification", async () => {
    expect(
      (
        await saveProfile(
          request("profile", {
            name: "A",
            email: "other@example.test",
            userId: "bob",
          }),
        )
      ).status,
    ).toBe(400);
  });
  it("rejects blank display name", async () => {
    expect((await saveProfile(request("profile", { name: "  " }))).status).toBe(
      400,
    );
  });
  it("reads saved false and supplies missing defaults", async () => {
    const p = await (await preferences()).json();
    expect(p.preferences).toMatchObject({
      titles: "en",
      navPinned: false,
      readingDepth: "deep",
      grounding: "right",
      textScale: 1,
    });
  });
  it.each([
    { navPinned: "false" },
    { readingDepth: "invalid" },
    { textScale: 0 },
    { userId: "bob" },
    { password: "secret" },
  ])("rejects invalid preference fields %j", async (body) => {
    expect((await savePreferences(request("preferences", body))).status).toBe(
      400,
    );
  });
  it("rejects a cross-origin write", async () => {
    expect(
      (
        await savePreferences(
          request("preferences", { navPinned: true }, "https://evil.test"),
        )
      ).status,
    ).toBe(403);
  });
  it("rejects another users recent security token", async () => {
    h.verify.mockResolvedValue({
      uid: "bob",
      auth_time: Math.floor(Date.now() / 1000),
    });
    expect(
      (await security(request("security", { idToken: "fictional" }))).status,
    ).toBe(403);
  });
  it("requires recent security authentication", async () => {
    h.verify.mockResolvedValue({
      uid: "alice",
      auth_time: Math.floor(Date.now() / 1000) - 301,
    });
    expect(
      (await security(request("security", { idToken: "fictional" }))).status,
    ).toBe(403);
  });
  it("fails closed without an authentication timestamp", async () => {
    h.verify.mockResolvedValue({ uid: "alice" });
    expect(
      (await security(request("security", { idToken: "fictional" }))).status,
    ).toBe(403);
    expect(h.revoke).not.toHaveBeenCalled();
  });
  it("allows a fresh own token after password change invalidates the cookie", async () => {
    h.ctx.mockResolvedValue(null);
    h.query.mockResolvedValue({ rows: [{ status: "active" }] });
    expect(
      (await security(request("security", { idToken: "fictional" }))).status,
    ).toBe(200);
    expect(h.query).toHaveBeenCalledWith(
      "SELECT status FROM profiles WHERE id=$1",
      ["alice"],
    );
  });
  it("rejects a fresh token from a disabled profile even without a cookie", async () => {
    h.ctx.mockResolvedValue(null);
    h.query.mockResolvedValue({ rows: [{ status: "disabled" }] });
    expect(
      (await security(request("security", { idToken: "fictional" }))).status,
    ).toBe(403);
    expect(h.revoke).not.toHaveBeenCalled();
  });
  it("does not claim sign-out when revocation fails", async () => {
    h.revoke.mockRejectedValue(new Error("offline"));
    expect(
      (await security(request("security", { idToken: "fictional" }))).status,
    ).toBe(503);
  });
  it("clears the browser session after verified revocation", async () => {
    const r = await security(request("security", { idToken: "fictional" }));
    expect(r.status).toBe(200);
    expect(r.headers.get("set-cookie")).toContain("__session=");
    expect(r.headers.get("set-cookie")).toContain("Max-Age=0");
  });
});
