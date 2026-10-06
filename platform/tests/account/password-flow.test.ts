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
import { auth } from "@/lib/firebase/client";
import {
  changeAccountPassword,
  finishAccountSecurity,
  signOutAccountSessions,
} from "@/lib/account/password-flow";
beforeEach(() => {
  vi.resetAllMocks();
  (auth as unknown as { currentUser: typeof auth.currentUser }).currentUser = {
    uid: "alice",
    email: "alice@example.test",
    getIdToken: h.token,
  } as unknown as typeof auth.currentUser;
  h.reauth.mockResolvedValue({});
  h.update.mockResolvedValue(undefined);
  h.token.mockResolvedValue("fictional-token");
  h.signOut.mockImplementation(async () => {
    (auth as unknown as { currentUser: typeof auth.currentUser }).currentUser =
      null;
  });
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

function switchToBob() {
  (auth as unknown as { currentUser: typeof auth.currentUser }).currentUser = {
    uid: "bob",
    email: "bob@example.test",
    getIdToken: vi.fn().mockResolvedValue("bob-token"),
  } as unknown as typeof auth.currentUser;
}
it.each(["reauth", "update", "token", "fetch"])(
  "does not complete or sign out a replacement account after a switch during %s",
  async (stage) => {
    if (stage === "fetch")
      vi.stubGlobal(
        "fetch",
        vi.fn(async () => {
          switchToBob();
          return Response.json({ ok: true });
        }),
      );
    else
      h[stage as "reauth" | "update" | "token"].mockImplementation(async () => {
        switchToBob();
        return stage === "token" ? "alice-token" : undefined;
      });
    const result = await changeAccountPassword(
      "old-fictional",
      "new-fictional",
    );
    expect(result.complete).toBe(false);
    expect(result.changed).toBe(stage !== "reauth");
    expect(h.signOut).not.toHaveBeenCalled();
    if (stage === "reauth") expect(h.update).not.toHaveBeenCalled();
    if (stage !== "fetch") expect(fetch).not.toHaveBeenCalled();
  },
);
it("keeps partial-result retries bound to the original owner", async () => {
  switchToBob();
  expect(await finishAccountSecurity("alice")).toBe(false);
  expect(fetch).not.toHaveBeenCalled();
  expect(h.signOut).not.toHaveBeenCalled();
});
it("does not revoke a replacement user's sessions after reauthentication", async () => {
  h.reauth.mockImplementation(async () => switchToBob());
  expect(await signOutAccountSessions("old-fictional")).toBe(false);
  expect(fetch).not.toHaveBeenCalled();
  expect(h.signOut).not.toHaveBeenCalled();
});

it("reports incomplete completion if another account signs in while local sign-out finishes", async () => {
  h.signOut.mockImplementation(async () => switchToBob());
  expect(
    await changeAccountPassword("old-fictional", "new-fictional"),
  ).toMatchObject({ changed: true, complete: false, ownerId: "alice" });
  expect(auth.currentUser?.uid).toBe("bob");
  expect(h.token).toHaveBeenCalledTimes(1);
});
