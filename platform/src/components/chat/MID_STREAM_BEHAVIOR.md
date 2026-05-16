# Mid-Stream Interrupt Contract (β3)

## Overview

When a user submits a new message while the assistant is actively streaming, the client
performs a cancel-and-replace: the in-flight generation is aborted, the server records
a `cancelled` trace step, and the new message is sent after a 300 ms delay.

## Client Contract

1. **V2Composer** tracks `isRunning` via `useThreadRuntime().subscribe()` (F.3 idiom).
2. When `isRunning`, the composer exposes two buttons:
   - `v2-abort-btn` — explicit cancel via `ComposerPrimitive.Cancel` (no resend).
   - `v2-interrupt-send-btn` — calls `runtime.cancelRun()`, sets `pendingResubmit`,
     shows the interrupt toast, then waits for `isRunning → false`.
3. When `isRunning` transitions `true → false` with `pendingResubmit` set:
   - A 300 ms `setTimeout` fires.
   - The toast is cleared.
   - `form.requestSubmit()` triggers the normal ComposerPrimitive submit path.
4. **Toast**: `v2-interrupt-toast` (`aria-live="polite"`) displays
   "Cancelled — sending new query" during the 300 ms window.

## Server Contract

1. Route registers an `{ once: true }` `'abort'` listener on `request.signal`
   immediately after `queryId` is resolved.
2. On abort, `traceEmitter.emitStep()` writes a `step_name: 'cancelled'` row to
   `query_trace_steps` with:
   - `status: 'cancelled'` (added to `StepStatus` union in `trace/types.ts`)
   - `completed_at`: ISO timestamp of the cancellation moment
3. The abort propagates naturally through `abortSignal: request.signal` passed to
   the synthesis orchestrator — no additional signal wiring required.

## Data Flow

```
User clicks v2-interrupt-send-btn
  → runtime.cancelRun()           (client aborts SSE fetch)
    → request.signal fires 'abort' (server)
      → traceEmitter writes cancelled step
  → pendingResubmit = true
  → isRunning → false (subscription fires)
    → setTimeout(300ms)
      → toast hidden
      → form.requestSubmit()       (new query sent)
```

## Test IDs

| ID | Element | Condition |
|----|---------|-----------|
| `v2-abort-btn` | Cancel button | `isRunning` |
| `v2-interrupt-send-btn` | Interrupt+send button | `isRunning` |
| `v2-send-btn` | Normal send button | `!isRunning` |
| `v2-interrupt-toast` | Toast overlay | `interruptToast` |
