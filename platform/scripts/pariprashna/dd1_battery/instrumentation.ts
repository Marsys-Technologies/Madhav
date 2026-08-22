/**
 * dd1_battery/instrumentation.ts — the in-page recorder for the browser lane.
 *
 * Injected with `page.addInitScript` BEFORE any app code runs, so it is
 * observing from the first frame. It records exactly the quantities M1, M2,
 * M3 and M6's DOM half are defined over — nothing is computed here; the
 * detectors in `browser_lane.ts` read these counters and decide.
 *
 * SELECTORS ARE THE PRODUCTION ONES, harvested from the shipped components,
 * not from the test harness page:
 *   [data-committed="true"]        FrozenBlock.tsx  (settled block)
 *   [data-testid="pp-tail"]        VolatileTail.tsx (volatile tail)
 *   [data-pp-caret]                Caret.tsx
 *   .pp-band                       WorkingBand.tsx  (the working region)
 *   [data-testid="pp-citation-chip"] CitationChip.tsx
 *   [data-testid="pp-composer-send"] / [data-testid="pp-composer-textarea"]
 *
 * `selectorsSeen` exists for the §N.8 question "what would have to fail for
 * this to read false": if the live DOM never yields these nodes, the counters
 * would all be trivially zero and the metrics would read a VACUOUS green. The
 * browser lane refuses to report PASS for a metric whose selector was never
 * observed at all — see `browser_lane.ts`'s selector-presence gate.
 */

export const SELECTORS = {
  settled: '[data-committed="true"]',
  tail: '[data-testid="pp-tail"]',
  caret: '[data-pp-caret]',
  band: '.pp-band',
  chip: '[data-testid="pp-citation-chip"]',
  composer: '[data-testid="pp-composer-textarea"]',
  send: '[data-testid="pp-composer-send"]',
  stop: '[data-testid="pp-composer-stop"]',
  turn: '[data-testid="pp-turn"]',
} as const

/** Drift tolerance in px — the same 0.5px the repo's own G-CLS harness uses. */
export const SETTLED_DRIFT_TOLERANCE_PX = 0.5

export interface Dd1Recording {
  submitAt: number | null
  bandFirstSeenAt: number | null
  frames: number
  settledShiftCount: number
  settledShiftDetails: Array<{ id: string; drift: number; at: number }>
  domMutationCount: number
  domMutationDetails: Array<{ id: string; at: number; before: string; after: string }>
  caretChecks: number
  caretViolations: Array<{ at: number; reason: string }>
  chipGeometryChanges: Array<{ id: string; at: number; before: string; after: string }>
  selectorsSeen: Record<string, number>
}

/**
 * The recorder, as a source string (it runs in the page, not in node). Kept as
 * a template so `SETTLED_DRIFT_TOLERANCE_PX` and `SELECTORS` have exactly one
 * definition shared by both sides.
 */
export function recorderSource(): string {
  return `
(() => {
  const S = ${JSON.stringify(SELECTORS)};
  const TOL = ${SETTLED_DRIFT_TOLERANCE_PX};
  const rec = {
    submitAt: null, bandFirstSeenAt: null, frames: 0,
    settledShiftCount: 0, settledShiftDetails: [],
    domMutationCount: 0, domMutationDetails: [],
    caretChecks: 0, caretViolations: [],
    chipGeometryChanges: [],
    selectorsSeen: { settled: 0, tail: 0, caret: 0, band: 0, chip: 0 },
  };
  window.__dd1 = rec;

  let nextId = 0;
  const known = new Map();   // element -> { id, rect, html }
  const chips = new Map();   // element -> { id, rect }

  const rectStr = (r) => [r.x, r.y, r.width, r.height].map((n) => Math.round(n * 100) / 100).join(',');

  // M3: the click itself stamps submitAt, in the page, at the real event — not
  // an approximation taken from node before/after an await.
  document.addEventListener('click', (e) => {
    const t = e.target;
    if (t && t.closest && t.closest(S.send)) rec.submitAt = performance.now();
  }, true);

  function tick() {
    rec.frames += 1;
    const now = performance.now();

    // Working region (M3).
    const band = document.querySelector(S.band);
    if (band) {
      rec.selectorsSeen.band += 1;
      if (rec.bandFirstSeenAt === null) rec.bandFirstSeenAt = now;
    }

    // Settled blocks (M1 geometry + M6 DOM byte-identity).
    const settled = document.querySelectorAll(S.settled);
    if (settled.length) rec.selectorsSeen.settled += 1;
    settled.forEach((el) => {
      const r = el.getBoundingClientRect();
      const html = el.outerHTML;
      const prev = known.get(el);
      if (!prev) {
        known.set(el, { id: 'b' + nextId++, rect: r, html });
        return;
      }
      const drift = Math.max(Math.abs(r.y - prev.rect.y), Math.abs(r.x - prev.rect.x));
      if (drift > TOL) {
        rec.settledShiftCount += 1;
        if (rec.settledShiftDetails.length < 40) {
          rec.settledShiftDetails.push({ id: prev.id, drift: Math.round(drift * 100) / 100, at: Math.round(now) });
        }
        prev.rect = r; // re-baseline so one shift is not counted every frame forever
      }
      if (html !== prev.html) {
        rec.domMutationCount += 1;
        if (rec.domMutationDetails.length < 20) {
          rec.domMutationDetails.push({
            id: prev.id, at: Math.round(now),
            before: prev.html.slice(0, 300), after: html.slice(0, 300),
          });
        }
        prev.html = html;
      }
    });

    // Citation chips (M6: final geometry on first paint).
    document.querySelectorAll(S.chip).forEach((el) => {
      const r = el.getBoundingClientRect();
      const prev = chips.get(el);
      if (!prev) { chips.set(el, { id: 'c' + nextId++, rect: rectStr(r) }); rec.selectorsSeen.chip += 1; return; }
      const nowStr = rectStr(r);
      // Width/height are the geometry that must not transmute; x/y move
      // legitimately as the block reflows within the tail before it commits.
      const dim = (s) => s.split(',').slice(2).join(',');
      if (dim(nowStr) !== dim(prev.rect)) {
        if (rec.chipGeometryChanges.length < 20) {
          rec.chipGeometryChanges.push({ id: prev.id, at: Math.round(now), before: prev.rect, after: nowStr });
        }
        prev.rect = nowStr;
      }
    });

    // Caret discipline (M2). AC-2's invariant: the caret is the last inline
    // child of the deepest last text-bearing node of the tail block, and
    // caret-absent <=> no volatile block.
    const tail = document.querySelector(S.tail);
    const caret = document.querySelector(S.caret);
    if (tail) rec.selectorsSeen.tail += 1;
    if (caret) rec.selectorsSeen.caret += 1;
    if (tail && caret) {
      rec.caretChecks += 1;
      let reason = null;
      if (!tail.contains(caret)) {
        reason = 'caret is not inside the volatile tail block';
      } else {
        // deepest last text-bearing node of the tail
        let node = tail;
        for (;;) {
          const kids = Array.from(node.childNodes).filter(
            (n) => (n.nodeType === 3 && n.textContent.trim().length > 0) ||
                   (n.nodeType === 1 && n !== caret && n.textContent.trim().length > 0),
          );
          if (kids.length === 0) break;
          const last = kids[kids.length - 1];
          if (last.nodeType === 3) break;
          node = last;
        }
        const rc = caret.getBoundingClientRect();
        // Find the last text rect in \`node\`.
        let lastTextRect = null;
        const range = document.createRange();
        const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
        let tn = null, cur;
        while ((cur = walker.nextNode())) { if (cur.textContent.trim()) tn = cur; }
        if (tn) {
          range.selectNodeContents(tn);
          const rects = range.getClientRects();
          if (rects.length) lastTextRect = rects[rects.length - 1];
        }
        if (lastTextRect && rc.height > 0) {
          const lineH = Math.max(lastTextRect.height, rc.height, 1);
          const sameLine = Math.abs(rc.top - lastTextRect.top) <= lineH;
          const adjacent = rc.left >= lastTextRect.left - 2 && rc.left - lastTextRect.right <= lineH * 2;
          if (!sameLine) reason = 'caret is on its own line, detached from the last text node';
          else if (!adjacent) reason = 'caret is horizontally detached from the last text node';
        }
      }
      if (reason && rec.caretViolations.length < 40) {
        rec.caretViolations.push({ at: Math.round(now), reason });
      }
    }

    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
})();
`
}
