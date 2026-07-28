// Paripraśna acceptance harness — test-only DOM renderer.
//
// This is NOT the product. It exists so the C-2 Playwright gate battery has
// something concrete to measure (real layout, real scroll, real DOM) before
// C-1's real renderer lands. Every rendering decision here is the *minimum*
// needed to make the gates meaningful, not a preview of the final UI.
//
// Query params:
//   ?fixture=<name>   required. Which fixture to replay (see /fixtures).
//   ?violate=<key>    optional. Seeds ONE deliberate violation so a gate can
//                     be proven non-decorative (must go red). Recognized
//                     keys: cls, caret, transmute, raf, viewport, pill, axe,
//                     mobile-tap. Anything else (including absent) = clean
//                     run.
//
// window.__harness exposes counters/state for Playwright to assert on
// (see each gate spec under tests/pariprashna/gates/ for exact usage).
import { applyEvent, createInitialState, snapshot } from '/reducer.mjs'

const params = new URLSearchParams(location.search)
const fixtureName = params.get('fixture')
const violate = params.get('violate') || null

const $ = (sel) => document.querySelector(sel)
const settled = $('#settled')
const tail = $('#tail')
const viewport = $('#thread-viewport')
const activitiesEl = $('#activities')
const flagsEl = $('#flags')
const phaseLabel = $('#phase-label')
const followPill = $('#follow-pill')
const body = document.body

// ─── window.__harness instrumentation ───────────────────────────────────────

const harness = {
  fixture: fixtureName,
  violate,
  ready: false,
  done: false,
  renderCount: 0,
  framesElapsed: 0,
  settledShiftCount: 0,
  settledShiftDetails: [],
  caretViolations: [],
  caretChecks: 0,
  viewportShiftCount: 0,
  viewportShiftDetails: [],
  pillShown: false,
  pillReSquelched: false,
  eventsReceived: 0,
  eventsExpectedTotal: null,
  malformedSkipped: 0,
}
window.__harness = harness

function setProgress() {
  const total = harness.eventsExpectedTotal
  const pct = total ? Math.min(100, Math.round((harness.eventsReceived / total) * 100)) : 0
  body.dataset.progress = String(pct)
}

function setDone(v) {
  harness.done = v
  body.dataset.done = String(v)
}

// ─── reducer state ───────────────────────────────────────────────────────────

let state = createInitialState()
const citationDefs = new Map() // citation_id -> {label, verification, source_ref}
const openBlockEls = new Map() // block_id -> element (while un-committed)
const seamEls = new Map() // seam_id -> element
const blockRectSnapshots = new Map() // block_id -> {top,left,width,height}

// ─── coalesced render scheduling (G-RAF) ────────────────────────────────────

let pendingRenders = []
let rafScheduled = false

function scheduleRender(fn) {
  if (violate === 'raf') {
    // Deliberate violation: apply immediately, one DOM commit per call,
    // bypassing coalescing entirely.
    fn()
    harness.renderCount += 1
    return
  }
  pendingRenders.push(fn)
  if (!rafScheduled) {
    rafScheduled = true
    requestAnimationFrame(() => {
      const batch = pendingRenders
      pendingRenders = []
      rafScheduled = false
      for (const f of batch) f()
      harness.renderCount += 1
    })
  }
}

// ─── continuous per-frame measurement loop (CLS / caret / viewport / RAF) ───

let measuring = false
function startMeasuringLoop() {
  if (measuring) return
  measuring = true
  const tick = () => {
    harness.framesElapsed += 1
    measureSettledShift()
    measureCaret()
    measureViewport()
    if (!harness.done) requestAnimationFrame(tick)
    else measuring = false
  }
  requestAnimationFrame(tick)
}

function measureSettledShift() {
  for (const [blockId, prevRect] of blockRectSnapshots.entries()) {
    const el = settled.querySelector(`[data-block-id="${cssEscape(blockId)}"]`)
    if (!el) continue
    const r = el.getBoundingClientRect()
    const drift = Math.abs(r.top - prevRect.top) + Math.abs(r.left - prevRect.left)
    if (drift > 0.5) {
      harness.settledShiftCount += 1
      harness.settledShiftDetails.push({ blockId, drift, at: harness.framesElapsed })
    }
  }
}

function measureCaret() {
  const caret = $('#caret')
  if (!caret || caret.hidden) return
  harness.caretChecks += 1
  const caretRect = caret.getBoundingClientRect()
  const tailTarget = violate === 'caret' ? (settled.firstElementChild || tail) : tail
  const tailRect = tailTarget.getBoundingClientRect()
  const isSubset =
    caretRect.top >= tailRect.top - 1 &&
    caretRect.left >= tailRect.left - 1 &&
    caretRect.bottom <= tailRect.bottom + 1 &&
    caretRect.right <= tailRect.right + 1
  if (!isSubset) {
    harness.caretViolations.push({
      at: harness.framesElapsed,
      caretRect: rectToPlain(caretRect),
      tailRect: rectToPlain(tailRect),
    })
  }
}

let firstViewportRect = null
function measureViewport() {
  const r = viewport.getBoundingClientRect()
  const pageHeight = document.documentElement.scrollHeight
  if (!firstViewportRect) {
    firstViewportRect = { height: r.height, pageHeight }
    return
  }
  const heightDrift = Math.abs(r.height - firstViewportRect.height)
  const pageDrift = Math.abs(pageHeight - firstViewportRect.pageHeight)
  if (heightDrift > 1 || pageDrift > 1) {
    harness.viewportShiftCount += 1
    harness.viewportShiftDetails.push({ heightDrift, pageDrift, at: harness.framesElapsed })
  }
}

function rectToPlain(r) {
  return { top: r.top, left: r.left, bottom: r.bottom, right: r.right, width: r.width, height: r.height }
}
function cssEscape(s) {
  return String(s).replace(/["\\]/g, '\\$&')
}

if (violate === 'viewport') viewport.classList.add('violate-viewport')

// ─── block content rendering (kind-aware) ───────────────────────────────────

function renderBlockContent(el, block) {
  el.dataset.kind = block.kind
  if (block.kind === 'table') {
    renderTable(el, block.text)
  } else if (block.kind === 'list') {
    const ul = document.createElement('ul')
    for (const line of block.text.split('\n').filter((l) => l.trim())) {
      const li = document.createElement('li')
      li.textContent = line.replace(/^-\s*/, '')
      ul.appendChild(li)
    }
    el.replaceChildren(ul)
  } else {
    const tag = block.kind === 'heading' ? 'h2' : block.kind === 'blockquote' ? 'blockquote' : block.kind === 'code' ? 'pre' : 'p'
    const contentEl = el.__contentEl && el.__contentEl.tagName.toLowerCase() === tag ? el.__contentEl : document.createElement(tag)
    contentEl.textContent = block.text
    if (!el.contains(contentEl)) el.replaceChildren(contentEl)
    el.__contentEl = contentEl
  }
}

function renderTable(el, rawText) {
  const lines = rawText.split('\n').filter((l) => l.trim().startsWith('|'))
  const table = document.createElement('table')
  lines.forEach((line, i) => {
    const cells = line.split('|').map((c) => c.trim()).filter((_, idx, arr) => idx !== 0 && idx !== arr.length - 1)
    if (cells.every((c) => /^-+$/.test(c))) return // separator row
    const tr = document.createElement('tr')
    for (const c of cells) {
      const cell = document.createElement(i === 0 ? 'th' : 'td')
      cell.textContent = c
      tr.appendChild(cell)
    }
    table.appendChild(tr)
  })
  el.replaceChildren(table)
}

// ─── seam / citation rendering ───────────────────────────────────────────────

function renderSeamPending(seamId) {
  const span = document.createElement('span')
  span.className = 'seam seam-pending'
  span.dataset.seamId = seamId
  span.textContent = '\u2022'
  seamEls.set(seamId, span)
  return span
}

function renderSeamResolved(seamId) {
  const span = seamEls.get(seamId)
  if (!span) return
  const seam = state.seams.get(seamId)
  if (!seam) return
  if (seam.citation_id === null) {
    span.className = 'seam honest-gap-marker'
    span.textContent = '[gap]'
    span.setAttribute('title', 'No citation found for this claim')
    return
  }
  const citation = citationDefs.get(seam.citation_id)
  if (!citation) return
  const btn = document.createElement('button')
  btn.type = 'button'
  btn.className = 'citation-chip' + (violate === 'mobile-tap' ? ' violate-mobile-tap' : '')
  btn.dataset.citationId = seam.citation_id
  btn.dataset.verification = citation.verification
  btn.setAttribute('aria-expanded', 'false')
  btn.setAttribute('aria-label', `Citation: ${citation.label}`)
  btn.textContent = citation.label
  const detail = document.createElement('span')
  detail.className = 'citation-detail'
  detail.hidden = true
  detail.textContent = citation.source_ref || ''
  btn.addEventListener('click', () => {
    const open = btn.getAttribute('aria-expanded') === 'true'
    btn.setAttribute('aria-expanded', open ? 'false' : 'true')
    detail.hidden = open
  })
  const wrap = document.createElement('span')
  wrap.className = 'seam'
  wrap.dataset.seamId = seamId
  wrap.appendChild(btn)
  wrap.appendChild(detail)
  span.replaceWith(wrap)
  seamEls.set(seamId, wrap)
}

// ─── activity rendering ──────────────────────────────────────────────────────

function renderActivity(key) {
  const activity = state.activities.get(key)
  if (!activity) return
  let row = activitiesEl.querySelector(`[data-activity-key="${cssEscape(key)}"]`)
  if (!row) {
    row = document.createElement('div')
    row.className = 'activity-row'
    row.dataset.activityKey = key
    activitiesEl.appendChild(row)
  }
  row.dataset.status = activity.status
  row.dataset.passId = activity.pass_id
  row.textContent = `${activity.pass_id}: ${activity.label_key} — ${activity.status}${activity.detail ? ' (' + activity.detail + ')' : ''}`
}

// ─── flag rendering ───────────────────────────────────────────────────────────

function renderFlag(flag) {
  const row = document.createElement('div')
  row.className = 'flag-row'
  row.dataset.severity = flag.severity
  row.dataset.flagKey = flag.flag_key
  row.textContent = `[${flag.severity}] ${flag.flag_key}${flag.detail ? ': ' + flag.detail : ''}`
  flagsEl.appendChild(row)
}

// ─── caret placement ──────────────────────────────────────────────────────────

function placeCaret() {
  let caret = $('#caret')
  if (!caret) {
    caret = document.createElement('span')
    caret.id = 'caret'
    caret.dataset.testid = 'caret'
    caret.setAttribute('aria-hidden', 'true')
    viewport.appendChild(caret)
  }
  const target = violate === 'caret' ? (settled.lastElementChild || tail) : tail
  const rect = target.getBoundingClientRect()
  const viewportRect = viewport.getBoundingClientRect()
  caret.style.top = `${rect.bottom - viewportRect.top + viewport.scrollTop - 16}px`
  caret.style.left = `${rect.left - viewportRect.left + 8}px`
  caret.hidden = false
}

function hideCaret() {
  const caret = $('#caret')
  if (caret) caret.hidden = true
}

// ─── auto-scroll / follow-pill ────────────────────────────────────────────────

let autoFollow = true
let lastProgrammaticScrollTop = null

function scrollToBottom() {
  lastProgrammaticScrollTop = viewport.scrollHeight
  viewport.scrollTop = viewport.scrollHeight
}

function maybeAutoScroll() {
  if (autoFollow) scrollToBottom()
}

if (violate !== 'pill') {
  viewport.addEventListener('scroll', () => {
    // Ignore the scroll event that WE just caused programmatically.
    if (lastProgrammaticScrollTop !== null && Math.abs(viewport.scrollTop - lastProgrammaticScrollTop) < 2) {
      lastProgrammaticScrollTop = null
      return
    }
    const distanceFromBottom = viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight
    if (distanceFromBottom > 40 && !harness.done) {
      autoFollow = false
      followPill.hidden = false
      harness.pillShown = true
    } else if (distanceFromBottom <= 4) {
      autoFollow = true
      followPill.hidden = true
    }
  })
}

followPill.addEventListener('click', () => {
  autoFollow = true
  followPill.hidden = true
  harness.pillReSquelched = true
  scrollToBottom()
})

// ─── event -> DOM ─────────────────────────────────────────────────────────────

function handleTypedEvent(event) {
  const prevState = state
  state = applyEvent(state, event, { strict: false })
  if (state.applied_ids.size === prevState.applied_ids.size) return // was a duplicate, no-op

  switch (event.type) {
    case 'phase': {
      scheduleRender(() => {
        phaseLabel.textContent = event.phase + (event.label ? ` — ${event.label}` : '')
      })
      break
    }
    case 'activity.upsert': {
      scheduleRender(() => renderActivity(event.key))
      break
    }
    case 'block.open': {
      scheduleRender(() => {
        const el = document.createElement('section')
        el.className = 'block'
        el.dataset.blockId = event.block_id
        el.dataset.committed = 'false'
        tail.appendChild(el)
        openBlockEls.set(event.block_id, el)
        renderBlockContent(el, state.blocks.get(event.block_id))
        placeCaret()
        maybeAutoScroll()
      })
      break
    }
    case 'block.delta': {
      scheduleRender(() => {
        const el = openBlockEls.get(event.block_id)
        if (!el) return
        renderBlockContent(el, state.blocks.get(event.block_id))
        placeCaret()
        maybeAutoScroll()
      })
      break
    }
    case 'seam.open': {
      scheduleRender(() => {
        const el = openBlockEls.get(event.block_id)
        if (!el || !el.__contentEl) return
        el.__contentEl.appendChild(renderSeamPending(event.seam_id))
      })
      break
    }
    case 'seam.set': {
      scheduleRender(() => renderSeamResolved(event.seam_id))
      break
    }
    case 'citation.define': {
      citationDefs.set(event.citation_id, {
        label: event.label,
        verification: event.verification,
        source_ref: event.source_ref,
      })
      break
    }
    case 'block.commit': {
      scheduleRender(() => {
        const el = openBlockEls.get(event.block_id)
        if (!el) return
        el.dataset.committed = 'true'
        el.dataset.committedHtml = el.innerHTML
        openBlockEls.delete(event.block_id)

        const shouldExitLiveRegion = violate !== 'axe'
        if (shouldExitLiveRegion) {
          settled.appendChild(el) // reparent OUT of the aria-live #tail region
        }
        // Record post-settle rect for CLS tracking.
        blockRectSnapshots.set(event.block_id, el.getBoundingClientRect())

        if (violate === 'cls') {
          // Deliberate violation: insert a spacer ABOVE all committed
          // content, shifting every previously-recorded block downward.
          const spacer = document.createElement('div')
          spacer.style.height = '14px'
          spacer.className = 'violate-cls-spacer'
          settled.insertBefore(spacer, settled.firstChild)
        }
        hideCaret()
        maybeAutoScroll()
      })
      break
    }
    case 'flag': {
      scheduleRender(() => renderFlag(event))
      break
    }
    case 'turn.close': {
      scheduleRender(() => {
        phaseLabel.textContent = `closed (${event.reason})`
        hideCaret()
      })
      break
    }
    default:
      break
  }
}

// ─── SSE stream consumption ───────────────────────────────────────────────────

async function run() {
  if (!fixtureName) {
    phaseLabel.textContent = 'error: missing ?fixture='
    return
  }
  startMeasuringLoop()
  harness.ready = true

  const res = await fetch(`/stream?fixture=${encodeURIComponent(fixtureName)}`)
  const totalHeader = res.headers.get('x-fixture-event-count')
  harness.eventsExpectedTotal = totalHeader ? Number(totalHeader) : null

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const KNOWN_TYPES = new Set([
    'turn.open', 'phase', 'activity.upsert', 'block.open', 'block.delta',
    'block.commit', 'seam.open', 'seam.set', 'citation.define', 'flag',
    'grade', 'turn.commit', 'turn.close', 'error',
  ])

  function processFrame(frame) {
    const line = frame.split('\n').find((l) => l.startsWith('data: '))
    if (!line) return
    const jsonText = line.slice('data: '.length)
    let parsed
    try {
      parsed = JSON.parse(jsonText)
    } catch {
      harness.malformedSkipped += 1
      return
    }
    const looksValid =
      parsed && typeof parsed.id === 'string' && typeof parsed.seq === 'number' &&
      typeof parsed.type === 'string' && KNOWN_TYPES.has(parsed.type)
    if (!looksValid) {
      harness.malformedSkipped += 1
      return
    }
    harness.eventsReceived += 1
    setProgress()
    handleTypedEvent(parsed)
  }

  try {
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      let idx
      // eslint-disable-next-line no-cond-assign
      while ((idx = buffer.indexOf('\n\n')) !== -1) {
        const frame = buffer.slice(0, idx)
        buffer = buffer.slice(idx + 2)
        if (frame.trim()) processFrame(frame)
      }
    }
  } catch (err) {
    // Disconnect/abrupt-end fixtures land here — this is expected, not a bug.
    harness.streamError = String(err)
  } finally {
    setDone(true)
  }
}

run()
