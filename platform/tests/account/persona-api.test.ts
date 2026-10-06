import { beforeEach, it, expect, vi } from "vitest";
const h = vi.hoisted(() => ({
  ctx: vi.fn(),
  get: vi.fn(),
  list: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  remove: vi.fn(),
}));
vi.mock("@/lib/auth/access-control", () => ({
  getServerUserWithProfile: h.ctx,
}));
vi.mock("@/lib/firebase/server", () => ({
  getServerUser: async () => ({ uid: "alice" }),
}));
vi.mock("@/lib/personas", () => ({
  listPersonas: h.list,
  createPersona: h.create,
  getPersona: h.get,
  updatePersona: h.update,
  deletePersona: h.remove,
}));
import { POST, GET } from "@/app/api/personas/route";
import { PATCH } from "@/app/api/personas/[id]/route";
beforeEach(() => {
  vi.resetAllMocks();
  h.ctx.mockResolvedValue({
    user: { uid: "alice" },
    profile: { status: "active" },
  });
  h.get.mockResolvedValue({ id: "owned", user_id: "alice" });
  h.list.mockResolvedValue([]);
});
const req = (body: unknown, origin = "https://example.test") =>
  new Request("https://example.test/api/personas", {
    method: "POST",
    headers: { origin, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
it("inactive account cannot list personas", async () => {
  h.ctx.mockResolvedValue({
    user: { uid: "alice" },
    profile: { status: "disabled" },
  });
  expect((await GET()).status).toBe(403);
});
it("cross-origin persona mutation is rejected", async () => {
  expect(
    (await POST(req({ name: "N", system_prompt: "P" }, "https://evil.test")))
      .status,
  ).toBe(403);
});
it.each([
  { name: "N", system_prompt: "P", user_id: "bob" },
  { name: "N", system_prompt: "P", is_default: "true" },
  { name: "N", system_prompt: "P", default_style: "invented" },
  { name: "N", system_prompt: "P", default_stack: "invented" },
])("rejects malformed/foreign fields %j", async (body) => {
  expect((await POST(req(body))).status).toBe(400);
});
it("unknown update target is not revealed", async () => {
  h.get.mockResolvedValue(null);
  expect(
    (
      await PATCH(req({ is_default: true }), {
        params: Promise.resolve({ id: "foreign" }),
      })
    ).status,
  ).toBe(404);
});
