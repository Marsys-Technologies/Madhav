---
artifact: LEDGER_MAP_PB-3
type: LEDGER AUTHORITY MAP (per MEMO_PB-3_0 item 4)
campaign: PB — Paripraśna Build
wave: PB-3 SAMĪKṢĀ
version: 1.0
status: LIVE — authoritative disambiguation of every prediction/outcome table
date: 2026-07-28
authored_by: Claude Code (autonomous execution session)
---

# LEDGER_MAP_PB-3 — which table, when

Four tables now touch "prediction" or "outcome" in this codebase. This map is
the single place that says, for any given caller, which one is authoritative.
Written because X-5 found the pre-PB-3 landscape had **no** such map, and that
absence is exactly what let two different tools both named `record_outcome`
silently diverge onto two different tables with zero cross-reference.

## The four tables

| Table | Rows (at PB-3 BIND) | Populated by | Authoritative for |
|---|---|---|---|
| **`brahma_mimamsa_prediction_ledger`** (NEW, this wave) | 0 at creation, grows from real confirmed conversational predictions | PB-3 L-2 (candidate confirm) via the L-1 DAL | **The conversational prediction loop, full stop.** Every claim detected in a real `/api/pariprashna` reading, confirmed by a human, tracked through its window, and resolved. This is the ONLY table `mimamsa_calibration` should be written to from PB-3 onward (via L-5's `record_outcome`). If a caller's question is "what did the native predict, in conversation, and did it come true" — this table, always. |
| **`mimamsa_predictions`** | 286 live at BIND (X-5's snapshot said 384; the difference is a normal L5 rebuild's DELETE-then-INSERT, not data loss — hash-pinned at BIND, untouched by this wave) | `mi_bhavisya.py` (L5 build orchestrator, DELETE-then-INSERT) | **Build-time deterministic analytical predictions** — the L5 STRUCTURAL-mode predictions produced by a chart *build*, not by a conversation. Referenced by the pre-existing `mimamsa_calibration` rows that predate PB-3. Read-only historical reference from PB-3's perspective; no PB-3 lane writes here, ever. |
| **`mcp_predictions`** | 12 live at BIND, all content-empty stamp rows (X-5's snapshot said 0 — see MEMO_PB-3_0's BIND-AT-OPEN correction; RETIRED this wave regardless, per that memo) | *(none — table dropped)* | **Nothing.** This table no longer exists as of PB-3's L-1 migration. It was a chat-relay scaffold (migration 071) that predated §14, accumulated only content-empty `calibration_producer.ts` stamp rows, and was never read by anything downstream. A full backup (`mcp_predictions_retired_backup`, capturing all 12 rows as they stood at migration time) exists per the rollback path in MEMO_PB-3_0; do not resurrect the live table name without a fresh Pratinidhi ruling. |
| **`brahma_prospective_ledger`** | 7 live at BIND (X-5's snapshot said 5 — an active, independent write path; untouched by this wave) | `/api/mcp/writes/prospective_ledger_file` (D-4a Lane A-4) | **Explicit-filing prospective claims** — a *different* design (§11), where a claim is filed explicitly (not detected from conversation) and matched against LEL events. Not part of the §14 detection→confirm→resolve loop this wave builds. If a caller's question is "what was explicitly filed as a prospective claim, independent of any chat turn" — this table. |

## `phala_anchors` — not a ledger, but where `record_outcome` used to point

`phala_anchors` (286 rows live at BIND, tracking `mimamsa_predictions`'
rebuild cycle 1:1 — X-5 cited 384 as of its own snapshot; L4 anchor set) is
**not** a prediction ledger — it's
the anchor set the *sidecar's* `record_outcome` tool (`platform-mcp/.../
mimamsa_outcome.ts` → `brahmagyan/mimamsa/outcome.py`) attempts to UPDATE. X-5
found this path is currently broken: `outcome.py` references `phala_anchors`
columns (`id`, `confidence`, `prediction_state`, `outcome_note`,
`outcome_recorded_at`, `updated_at`) that do not exist on the live table
(which has `anchor_id`, `confidence_low`/`confidence_high`, `posterior`,
`computed_at`). This is L-5's charge to diagnose and disposition (fix, retire,
or park-with-costed-spec) — this map records the pre-PB-3 state as background,
not as a resolution.

## `record_outcome` disambiguation — there are (were) two tool surfaces

Before PB-3, calling something named "record outcome" was ambiguous:

1. **MCP tool `record_outcome`** (`platform-mcp/.../mimamsa_outcome.ts`) →
   sidecar `/api/compute/mimamsa/record_outcome` → attempts `UPDATE
   phala_anchors` (currently broken, see above) → `update_calibration()` →
   `mimamsa_calibration`.
2. **P1 alias `mimamsa_outcome_record`** → `callPlatformPrim('record_outcome')`
   → `/api/mcp/writes/record_outcome` → `ppl_writer.recordOutcome()` → UPDATE
   `mcp_predictions` (now retired — this path no longer has a table to write
   to as of PB-3 L-1; L-5 disposition-owns whatever remains of this call
   chain).

**After PB-3 (per L-5's charge):** the conversational outcome-recording path
should resolve a claim against `brahma_mimamsa_prediction_ledger` (the ledger
IS the citation, per §14.5) and write `mimamsa_calibration` from there — a
single, named, unambiguous path. `mimamsa_predictions`' own build-time
lifecycle continues to be transitioned only by `mi_abhilekha.py`, untouched by
any conversational `record_outcome` call, exactly as before this wave.

## Rule for future sessions

If you are about to write a prediction, a confirmation, a window-close, or an
outcome, and you are unsure which table — **check this map before writing
code, not after.** The absence of a map like this one is the specific,
named root cause X-5 traced for why two same-named tools silently diverged.

*End LEDGER_MAP_PB-3 v1.0.*
