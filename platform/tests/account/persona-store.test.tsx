import {
  act,
  render,
  screen,
  waitFor,
  cleanup,
  fireEvent,
} from "@testing-library/react";
import { it, expect, vi, afterEach } from "vitest";
import { usePersonas } from "@/hooks/usePersonas";
function Store() {
  const p = usePersonas();
  return (
    <>
      <output>
        {p.error ?? (p.loading ? "Loading" : `${p.personas.length} personas`)}
      </output>
      <button onClick={p.reload}>Reload</button>
    </>
  );
}
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
it("a failed persona fetch is shown as an error rather than an empty account", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(Response.json({}, { status: 503 }))),
  );
  render(<Store />);
  await waitFor(() =>
    expect(screen.getByText("Personas could not be loaded.")).toBeTruthy(),
  );
});
it("a response to an older reload cannot overwrite the current persona list", async () => {
  let resolve!: (v: Response) => void;
  const first = new Promise<Response>((r) => (resolve = r));
  const f = vi
    .fn()
    .mockReturnValueOnce(first)
    .mockResolvedValue(Response.json({ personas: [{ id: "one" }] }));
  vi.stubGlobal("fetch", f);
  render(<Store />);
  await waitFor(() => expect(f).toHaveBeenCalledTimes(1));
  fireEvent.click(screen.getByText("Reload"));
  await waitFor(() => expect(screen.getByText("1 personas")).toBeTruthy());
  await act(async () => {
    resolve(Response.json({ personas: [] }));
    await first;
  });
  expect(screen.getByText("1 personas")).toBeTruthy();
});
