import { Page, Route, Request } from '@playwright/test';

/**
 * Registers a page.route handler that intercepts POST /api/chat/consume
 * and returns a canned SSE stream representing a complete V2 response.
 * The stream includes:
 *   - Five stage events (planning → tool_fetch → synthesis, each with running + done)
 *   - Two data-citation parts with non-empty snippets
 *   - An answer body with two [^N] footnote markers
 *   - A footnote definition block at end-of-answer
 *   - A final data-stage synthesis done event
 *   - A proper SSE stream termination
 *
 * Call this BEFORE page.goto() so the route is registered before the request fires.
 */
export async function applyRound6MockRoute(page: Page): Promise<void> {
  await page.route('**/api/chat/consume', handleConsumeRoute);
}

async function handleConsumeRoute(route: Route, request: Request): Promise<void> {
  if (request.method() !== 'POST') {
    await route.continue();
    return;
  }

  const encoder = new TextEncoder();

  // Build the canned SSE stream as a ReadableStream body.
  const stream = new ReadableStream({
    async start(controller) {
      const emit = (line: string) => {
        controller.enqueue(encoder.encode(`${line}\n`));
      };

      // ── Stage: planning running ──────────────────────────────────────
      emit('data: {"type":"data","name":"stage","data":{"stage":"planning","state":"running","elapsed_ms":0}}');
      emit('');
      await delay(50);

      emit('data: {"type":"data","name":"stage","data":{"stage":"planning","state":"done","elapsed_ms":52}}');
      emit('');
      await delay(50);

      // ── Stage: tool_fetch running ────────────────────────────────────
      emit('data: {"type":"data","name":"stage","data":{"stage":"tool_fetch","state":"running","elapsed_ms":52}}');
      emit('');
      await delay(50);

      emit('data: {"type":"data","name":"stage","data":{"stage":"tool_fetch","state":"done","elapsed_ms":105}}');
      emit('');
      await delay(50);

      // ── Stage: synthesis running ─────────────────────────────────────
      emit('data: {"type":"data","name":"stage","data":{"stage":"synthesis","state":"running","elapsed_ms":105}}');
      emit('');
      await delay(50);

      // ── Citation parts with non-empty snippets ───────────────────────
      // signal SIG.MSR.001 — Sun in Capricorn (L1 fact)
      emit('data: {"type":"data","name":"citation","data":{"index":1,"signal_id":"SIG.MSR.001","layer":"L1","snippet":"Sun in Capricorn (10° 24′) — tenth lord in own sign, exalted in the angular tenth house. Core strength signal for career and public standing."}}');
      emit('');

      // signal SIG.MSR.057 — Saturn ruling the Tenth (L2.5 derivation)
      emit('data: {"type":"data","name":"citation","data":{"index":2,"signal_id":"SIG.MSR.057","layer":"L2.5","snippet":"Saturn rules the tenth house (Capricorn Ascendant). Its dasha periods activate career themes with the weight of its planetary period."}}');
      emit('');
      await delay(50);

      // ── Answer body — streamed in three chunks ───────────────────────
      emit('data: {"type":"text-delta","textDelta":"The native\'s chart reveals remarkable career potential through a combination of stellar placements.[^1] "}');
      emit('');
      await delay(30);

      emit('data: {"type":"text-delta","textDelta":"The tenth house receives Saturn\'s dasha energy in the coming period, activating ambition structures with unusual intensity.[^2]\\n\\n"}');
      emit('');
      await delay(30);

      // Footnote definition block (GFM footnotes, rendered by MarkdownContent after R6.2)
      emit('data: {"type":"text-delta","textDelta":"[^1]: SIG.MSR.001\\n[^2]: SIG.MSR.057\\n"}');
      emit('');
      await delay(30);

      // ── Stage: synthesis done ────────────────────────────────────────
      emit('data: {"type":"data","name":"stage","data":{"stage":"synthesis","state":"done","elapsed_ms":315}}');
      emit('');
      await delay(20);

      // ── Stream termination ───────────────────────────────────────────
      emit('data: [DONE]');
      emit('');

      controller.close();
    },
  });

  await route.fulfill({
    status: 200,
    headers: {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no',
    },
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    body: stream as any,
  });
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
