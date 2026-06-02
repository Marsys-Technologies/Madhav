---
artifact: LEL_SCHEMA_AND_INTAKE_v1_0.md
canonical_id: LEL_SCHEMA_AND_INTAKE
version: 1.0
status: CLOSED 2026-06-02 (design baseline — sealed in M5_REARCHITECTURE_DESIGN_CLOSE_v1_0; build phase next)
authored_by: Claude (Cowork) 2026-06-02
read_with:
  - 00_ARCHITECTURE/LAYER_5_LEARNING_DESIGN_v1_0.md (LEL is the L5 isolated Outcome Record)
  - 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md (the existing annotated LEL to migrate; legacy)
purpose: >
  The Life Event Log as a PURE EVENT LOG — what happened, when, in what domain — with NO calculations
  fused in. One canonical store for every client; two intake paths (portal/MCP, and a one-time migration
  of the existing annotated v1.2); and a separate DERIVED "Event Chart-State Index" that does all the
  math. This keeps the ground truth isolated from generation by construction.
---

# LEL — Pure Event Log · Schema, Intake & Migration

## §0 — Required one-time action (TRACKED — do not miss)

**MIGRATE the existing annotated `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (57 events + chronic patterns)
into the pure-event store per §3.2 + §5 — exactly once.** This is a mandatory build step, not optional;
it carries the native's hand-recorded ground truth into the new isolated store. Owner: the L5 build.
Gate: the migrated `life_events` row-count = the v1.2 event-count (57) + chronic patterns; `chart_state`
+ `retrodictive_match` dropped; v1.2 retained as history.

## §1 — Principle

The LEL is the **held-out ground truth**. It must never be fused with anything the engine generates.
Therefore:
- **The LEL stores pure events only** — what happened, when, in what domain. No chart-state, no dashas,
  no transits, no signal matches, no calculations of any kind.
- **All calculations live in a separate, derived asset** — the **Event Chart-State Index** (§4) —
  computed by L5 against any client's events + chart. The events and the math meet *only* at the L5
  scoring join, after predictions are already logged.
- **One canonical store for everyone.** How an event arrived (portal, MCP, or migration) is an intake
  detail; the stored shape is identical for all clients.

## §2 — The pure-event LEL schema

Isolated store (own schema/grants). Table `life_events`:

| Field | Type | Meaning |
|---|---|---|
| `event_id` | uuid PK | stable id |
| `chart_id` | uuid FK | whose event (multi-native) |
| `legacy_id` | text null | original id if migrated (e.g. `EVT.2019.05.XX.01`) |
| `event_date` | date | when it happened |
| `date_precision` | enum | exact · month · year · approximate · range |
| `date_end` | date null | for ranges/periods |
| `event_type` | enum | point_event · chronic_pattern · period |
| `domain` | enum | career · wealth · relationships · health · children · spirit · parents · mind · travel · residence · education · creative · psychological · other |
| `title` | text | short label |
| `description` | text | what happened (factual; no interpretation) |
| `magnitude` | smallint (1–5) | significance |
| `valence` | enum | positive · negative · neutral · mixed |
| `source` | enum | portal · mcp · native_reported · document_extracted · verified |
| `confidence` | numeric(3,2) | the reporter's certainty about event + date |
| `tags` | text[] | optional subcategories |
| `recorded_at` | timestamptz | when logged |
| `recorded_by` | text | who/what logged it |
| `provenance` | jsonb | intake metadata |

**Explicitly NOT in the LEL:** `chart_state`, dasha/transit/sade-sati data, `retrodictive_match`,
signal IDs, predictions — all of that is derived (§4).

## §3 — The two intake paths (one destination)

1. **Clean intake — portal / MCP (default; future clients + the native going forward).**
   - Portal form or an MCP tool (`log_life_event`) writes pure events straight into `life_events`.
   - Validation: required date + `date_precision` + domain enum; free-text title/description; magnitude.
   - No stripping — events arrive clean.
2. **Migration intake — one-time, for the existing annotated v1.2 (§5).**
   - Parse `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`, extract the pure events, drop the fused calculations,
     load into `life_events`. Run once; the v1.2 file is retained as history.

Both write the **identical** stored shape. After migration, the native is indistinguishable from any
other client.

## §4 — The Event Chart-State Index (the separate, derived math)

L5-owned, derived, recomputable — **never stored in the LEL.** Table `event_chart_states`:

| Field | Type | Meaning |
|---|---|---|
| `event_id` | uuid FK → life_events | the event |
| `chart_id, ayanamsha_id, build_id` | — | the chart-build it was computed against |
| `engine_version, weights_version` | text | versioned → recompute as the engine improves |
| `active_dashas` | jsonb | MD/AD/PD/SD per system at `event_date` |
| `transits` | jsonb | relevant transits to natal points at the date |
| `sade_sati_phase` | text | Saturn phase at the date |
| `ashtakavarga_context` | jsonb | bindus/kakshya for the active transits |
| `active_signals` | text[] | L2 signal_ids live on that date |
| `would_have_predicted` | jsonb | what L4 (at `weights_version`) would have called for that window |
| `computed_at` | timestamptz | — |

- **Built by:** the L5 scoring/backtest harness, applying L1/L2/L3/L4 at each event's date.
- **Isolation:** reads `life_events` (read-only) + the chart's generation outputs; **writes only here**;
  **never feeds generation.** Recomputed when the engine/weights change — the LEL stays untouched.

## §5 — Migration mapping (v1.2 → pure events)

| v1.2 element | → pure-event field | Note |
|---|---|---|
| `EVT.*` id | `legacy_id` (+ new `event_id`) | keep the old id for traceability |
| event date (incl. proxy `YYYY.XX.XX`) | `event_date` + `date_precision` | `XX` month/day → `year`/`month` precision |
| category/domain | `domain` | map to the enum (residence/travel dual-tags → primary + `tags`) |
| event description | `title` + `description` | factual only |
| magnitude | `magnitude` | 1–5 |
| valence (if present) | `valence` | else infer neutral/mixed → flag for native confirm |
| `PATTERN.*` (chronic patterns) | rows with `event_type=chronic_pattern` | recurring life facts kept |
| period summaries (§ era) | optional `event_type=period` | descriptive context, not scoring ground truth |
| `source_of_events` | `source` (document_extracted / native_reported) | |
| **`chart_state` block** | **DROP** | re-derived by §4 (multi-ayanamsha, fresh) |
| **`retrodictive_match` (SIG.*)** | **DROP** | derived match, re-derived by L5 scoring |
| `confidence_self_assessment` | per-event `confidence` where available | else default |

**Result:** the 57 events (+ chronic patterns) become pure rows; the calculations come back richer the
first time the new engine runs §4.

## §6 — Isolation guarantees (how it's enforced)

- LEL lives in an **isolated schema**; DB grants give generation paths (L1–L4, synthesis) **no read
  access** — only the L5 scoring service can read it.
- The Event Chart-State Index is the **only** place events and calculations meet, and it is built
  **after** predictions are logged (held-out discipline, L5 §C18).
- The pure-event store is **portable**: it survives any chart rebuild, ayanamsha change, or engine
  version without modification.

---

*End of LEL_SCHEMA_AND_INTAKE v1.0 — DRAFT, 2026-06-02. Pure-event LEL + two intake paths + the derived
Event Chart-State Index; keeps the ground truth isolated by construction.*
