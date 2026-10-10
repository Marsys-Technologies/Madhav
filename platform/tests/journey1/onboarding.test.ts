import { beforeEach, describe, expect, it, vi } from "vitest";
import { NextResponse } from "next/server";

const mocks = vi.hoisted(() => ({
  query: vi.fn(),
  requireAdmin: vi.fn(),
  createUser: vi.fn(),
  getUserByEmail: vi.fn(),
  deleteUser: vi.fn(),
  resetLink: vi.fn(),
  verifyToken: vi.fn(),
  cookie: vi.fn(),
}));
vi.mock("server-only", () => ({}));
vi.mock("@/lib/db/client", () => ({ query: mocks.query }));
vi.mock("@/lib/auth/access-control", () => ({
  requireSuperAdmin: mocks.requireAdmin,
}));
vi.mock("@/lib/firebase/server", () => ({
  createSessionCookie: mocks.cookie,
  getServerUser: vi.fn(),
  adminAuth: {
    createUser: mocks.createUser,
    getUserByEmail: mocks.getUserByEmail,
    deleteUser: mocks.deleteUser,
    generatePasswordResetLink: mocks.resetLink,
    verifyIdToken: mocks.verifyToken,
  },
}));
import { POST as approve } from "@/app/api/admin/access-requests/[id]/approve/route";
import { POST as session } from "@/app/api/auth/session/route";

const jsonRequest = (path: string, body: unknown) =>
  new Request(`https://portal.example.invalid${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
beforeEach(() => {
  vi.resetAllMocks();
  mocks.requireAdmin.mockResolvedValue({ user: { uid: "admin-test" } });
  mocks.createUser.mockResolvedValue({ uid: "approved-test" });
  // A brand-new address: no Firebase account exists yet (today's create path).
  mocks.getUserByEmail.mockRejectedValue(
    Object.assign(new Error("no user"), { code: "auth/user-not-found" }),
  );
  mocks.resetLink.mockResolvedValue(
    "https://portal.example.invalid/reset-password?oobCode=fictional",
  );
  mocks.verifyToken.mockResolvedValue({ uid: "approved-test" });
  mocks.cookie.mockResolvedValue("fictional-test-cookie");
});

describe("approval followed by username choice", () => {
  it("keeps approval restricted to administrators", async () => {
    mocks.requireAdmin.mockResolvedValue(
      NextResponse.json({ error: "forbidden" }, { status: 403 }),
    );
    const response = await approve(
      jsonRequest("/api/admin/access-requests/r1/approve", {}),
      { params: Promise.resolve({ id: "r1" }) },
    );
    expect(response.status).toBe(403);
    expect(mocks.query).not.toHaveBeenCalled();
    expect(mocks.createUser).not.toHaveBeenCalled();
  });
  it("approves without assigning a username and supplies the account-setup continuation", async () => {
    mocks.query.mockImplementation(async (sql: string) => ({
      rows: sql.includes("FROM access_requests")
        ? [
            {
              id: "r1",
              full_name: "Fictional Native",
              email: "native@example.invalid",
              status: "pending",
            },
          ]
        : [],
    }));
    const response = await approve(
      jsonRequest("/api/admin/access-requests/r1/approve", { role: "guest" }),
      { params: Promise.resolve({ id: "r1" }) },
    );
    expect(response.status).toBe(200);
    expect(mocks.createUser).toHaveBeenCalledWith({
      email: "native@example.invalid",
      emailVerified: false,
      displayName: "Fictional Native",
    });
    const insert = mocks.query.mock.calls.find(([sql]) =>
      sql.startsWith("INSERT INTO profiles"),
    )!;
    expect(insert[1]).toEqual([
      "approved-test",
      "Fictional Native",
      null,
      "native@example.invalid",
      "admin-test",
    ]);
    expect(mocks.resetLink).toHaveBeenCalledWith("native@example.invalid", {
      url: "https://portal.example.invalid/setup-account",
    });
    expect((await response.json()).reset_link).toContain("/reset-password");
  });
  it("does not provision an already-reviewed request", async () => {
    mocks.query.mockResolvedValue({ rows: [{ id: "r1", status: "approved" }] });
    const response = await approve(
      jsonRequest("/api/admin/access-requests/r1/approve", {}),
      { params: Promise.resolve({ id: "r1" }) },
    );
    expect(response.status).toBe(409);
    expect(mocks.createUser).not.toHaveBeenCalled();
  });
});

describe("session directs approved users to their own setup", () => {
  it.each([
    [null, true],
    ["native_test", false],
  ])("username %s gives setup flag %s", async (username, expected) => {
    mocks.query.mockResolvedValue({
      rows: [
        { id: "approved-test", role: "guest", status: "active", username },
      ],
    });
    const response = await session(
      jsonRequest("/api/auth/session", { idToken: "fictional-token" }),
    );
    expect(await response.json()).toEqual({
      ok: true,
      username_setup_required: expected,
    });
    expect(mocks.verifyToken).toHaveBeenCalledWith("fictional-token", true);
    const cookie = response.cookies.get("__session")!;
    expect(cookie.value).toBe("fictional-test-cookie");
    expect(cookie.httpOnly).toBe(true);
    expect(cookie.sameSite).toBe("lax");
  });
  it.each(["pending", "disabled"])(
    "refuses %s profiles before creating a cookie",
    async (status) => {
      mocks.query.mockResolvedValue({
        rows: [{ id: "approved-test", role: "guest", status }],
      });
      expect(
        (
          await session(
            jsonRequest("/api/auth/session", { idToken: "fictional-token" }),
          )
        ).status,
      ).toBe(403);
      expect(mocks.cookie).not.toHaveBeenCalled();
    },
  );
  it("refuses an invalid Firebase identity", async () => {
    mocks.verifyToken.mockRejectedValue(new Error("invalid token"));
    expect(
      (
        await session(
          jsonRequest("/api/auth/session", { idToken: "fictional-token" }),
        )
      ).status,
    ).toBe(401);
    expect(mocks.query).not.toHaveBeenCalled();
    expect(mocks.cookie).not.toHaveBeenCalled();
  });
});
