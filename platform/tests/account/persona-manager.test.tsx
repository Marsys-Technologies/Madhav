import {
  render,
  screen,
  fireEvent,
  waitFor,
  cleanup,
} from "@testing-library/react";
import { it, expect, vi, afterEach } from "vitest";
vi.mock("@/components/account/useAiAccountState", () => ({
  useAiAccountState: () => ({
    state: undefined,
    clis: [],
    loading: false,
    error: false,
  }),
}));
import { PersonaManager } from "@/components/account/PersonaManager";
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
it("keeps a failed create form open with its instructions and error", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((_u, init?: RequestInit) =>
      Promise.resolve(
        init?.method === "POST"
          ? Response.json({}, { status: 503 })
          : Response.json({ personas: [] }),
      ),
    ),
  );
  render(<PersonaManager />);
  await screen.findByRole("button", { name: "Save recommended persona" });
  fireEvent.click(screen.getByRole("button", { name: "New Persona" }));
  fireEvent.change(screen.getByTestId("persona-form-name"), {
    target: { value: "Fictional voice" },
  });
  fireEvent.change(screen.getByTestId("persona-form-prompt"), {
    target: { value: "Use plain words." },
  });
  fireEvent.click(screen.getByRole("button", { name: "Create" }));
  await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
  expect(
    (screen.getByTestId("persona-form-prompt") as HTMLTextAreaElement).value,
  ).toBe("Use plain words.");
});
