import { it, expect, vi, beforeEach } from "vitest";
const h = vi.hoisted(() => ({
  reauth: vi.fn(),
  update: vi.fn(),
  signOut: vi.fn(),
  credential: vi.fn(),
  token: vi.fn(),
}));
vi.mock("firebase/auth", () => ({
  EmailAuthProvider: { credential: h.credential },
  reauthenticateWithCredential: h.reauth,
  updatePassword: h.update,
  signOut: h.signOut,
}));
vi.mock("@/lib/firebase/client", () => ({
  auth: {
    currentUser: {
      uid: "alice",
      email: "alice@example.test",
      getIdToken: h.token,
    },
  },
}));
import { changeAccountPassword } from "@/lib/account/password-flow";
beforeEach(() => {
  vi.resetAllMocks();
  h.reauth.mockResolvedValue({});
  h.update.mockResolvedValue(undefined);
  h.token.mockResolvedValue("fictional-token");
  h.signOut.mockResolvedValue(undefined);
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(Response.json({ ok: true }))),
  );
});
it("never changes the password if current-password authentication fails", async () => {
  h.reauth.mockRejectedValue(Error("bad password"));
  expect(
    await changeAccountPassword("old-fictional", "new-fictional"),
  ).toMatchObject({ changed: false, complete: false });
  expect(h.update).not.toHaveBeenCalled();
  expect(fetch).not.toHaveBeenCalled();
});
it("changes only the authenticated user then revokes sessions without sending passwords to our server", async () => {
  expect(await changeAccountPassword("old-fictional", "new-fictional")).toEqual(
    { changed: true, complete: true },
  );
  expect(fetch).toHaveBeenCalledWith(
    "/api/account/security",
    expect.objectContaining({ body: '{"idToken":"fictional-token"}' }),
  );
  expect(h.signOut).toHaveBeenCalledTimes(1);
});
it("discloses a changed password and incomplete session revocation separately", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(Response.json({}, { status: 503 }))),
  );
  expect(
    await changeAccountPassword("old-fictional", "new-fictional"),
  ).toMatchObject({ changed: true, complete: false });
  expect(h.signOut).not.toHaveBeenCalled();
});
