---
artifact: PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md
canonical_id: PHASE_4C_PANCHANG_MASTER_PLAN
version: 1.0
status: COMPLETE-AS-SHIPPED
authored_by: Claude (Sonnet 4.6, brainstormed under superpowers:brainstorming)
authored_on: 2026-05-19
sealed_on: 2026-05-21
sealed_by: Cowork session — Cowork_PanchangProdClose_2026-05-21
sealing_context: >
  Sealed retrospectively after Phase 4C Wave 1 closed in production 2026-05-21.
  All planned scope shipped: panchang_engine v1.0.0-S3 (Drik parity 30/30; 230
  sidecar tests PASS), query_panchanga RetrievalTool (tool 29), /panchang UI
  surface, Muhurat Finder (6 events, acharya CANARY PASS), iCal export (single-
  day + HMAC-signed 90-day subscribable feed), Ask-Madhav deep links,
  Observatory panels, 5 enrichment field groups (special_yogas, choghadiya,
  hora, inauspicious, auspicious). Shipped via PR #105 (Wave 1 application
  code, merge SHA 3b3405c, 2026-05-20), PR #110 (chat-side enrichment, merge
  SHA 9bdcac24, 2026-05-20), PR #111 (bootstrap-guard fix, merge SHA 74877a21,
  2026-05-20). Live in production at Cloud Run revisions amjis-web-00258-9vq
  + amjis-sidecar-00224-4xs on image SHA 1e5734b7…. FORENSIC-grounded engine
  spot-check at native birth date 1984-02-05 PASS 5/5. Build_id
  phase-4c-enrich-20260521-r2 populates panchanga_daily with 73,414 rows × full
  enrichment, range 1900-01-01 → 2100-12-31. See §0 SEALING NOTE for plan-vs-
  shipped delta.
purpose: >
  Master design plan for Phase 4C (Panchang Module), authored 2026-05-19 as
  a brainstorming output before formal governance adoption and sealed
  retrospectively 2026-05-21 after the planned scope shipped to production.
  This document records what was planned; the brief at
  00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md records what was
  executed; CLAUDE.md §E records the production close-out.
canonical_path: 00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md
brief_path: 00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md
related_artifacts:
  - 00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md (execution brief)
  - 00_ARCHITECTURE/PHASE_4C_FOLLOWUPS_v1_0.md (deferred items)
  - 00_ARCHITECTURE/BOOTSTRAP_PANCHANGA_BUILD_MANIFESTS_AUDIT_v1_0.md (close-out finding)
  - HANDOFF_WAVE_1.md (Wave 1 close handoff, authored by session 4C-9)
deferred_items:
  - 4C.2 SQL cache layer — gated on Phase 4B (sunrise derivation + MEAN_NODE rebuild). Engine-direct in prod.
  - v2 polish items per PHASE_4C_FOLLOWUPS_v1_0.md
  - Real acharya panel review of Muhurat scoring — M10-territory
  - bootstrap_panchanga.py build_manifests auto-registration (see BOOTSTRAP_PANCHANGA_BUILD_MANIFESTS_AUDIT_v1_0.md for the proposed Patch A + B)
---

# Panchang Module — Master Design Plan v1.0

**Project:** MARSYS-JIS Jyotish Instrument
**Workstream:** Phase 4C (Panchang) — concurrent workstream, alongside active M5-A
**Date authored:** 2026-05-19
**Date sealed:** 2026-05-21
**Status:** COMPLETE-AS-SHIPPED — all planned scope live in production. See §0 SEALING NOTE.
**Author:** Claude (Sonnet 4.6, brainstormed under `superpowers:brainstorming`)
**Sealed by:** Cowork session — Cowork_PanchangProdClose_2026-05-21

---

## §0 — SEALING NOTE (added 2026-05-21)

This document was authored 2026-05-19 as a brainstorming output before formal governance adoption of Phase 4C. It was never sealed as the canonical plan in real time — instead, the execution moved straight to the brief at `00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md`, which the 11-session Wave 1 (4C-0 through 4C-9) and the subsequent chat-side enrichment session executed against. The Conductor orchestrator ran the queue; PR #105 (merge SHA `3b3405c`, 2026-05-20) shipped the application code; PR #110 (merge SHA `9bdcac24`, 2026-05-20) shipped chat-side enrichment; PR #111 (merge SHA `74877a21`, 2026-05-20) shipped a bootstrap-guard fix. The production operator steps (migration 069, bootstrap to staging under build_id `phase-4c-enrich-20260521-r2`, atomic staging→live swap) completed 2026-05-21 with FORENSIC-grounded engine verification at 1984-02-05 passing 5/5 (tithi=Shukla Tritiya, vara=Ravivara, moon_nakshatra=Purva Bhadrapada, yoga=Shiva, karana=Garaja; `hora_count=24`; `first_inauspicious_window=rahu_kalam`) and the structural transit check passing (next purnima after 2026-05-19 = 2026-05-31 Shukla Purnima).

This master plan is therefore being sealed **retrospectively** as a historical record of what was planned, rather than as a forward-looking governance artifact. The brief carries the authoritative execution record. Read this document for design intent, product decisions, and the architectural reasoning behind the choices that landed; read the brief for what was actually built; read `CLAUDE.md §E Phase 4C` for the production close-out summary.

### §0.1 — Plan-vs-Shipped Delta

The plan as drafted in §3–§10 maps to what shipped with no scope cuts to Wave 1. Every product decision in §2 (D1 dedicated `/panchang` page, D2 generic-default + per-chart personalisation, D3 priority order: Muhurat Finder → iCal export → Ask-Madhav, D4 Phase 4C insertion, D5 concurrent with M5-A) shipped as designed. The four items deferred at plan time remain deferred and are recorded in `deferred_items` frontmatter:

- `4C.2` SQL cache layer — gated on Phase 4B (sunrise derivation + MEAN_NODE rebuild). The shipped system is engine-direct: `query_panchanga` calls `panchang_engine` via the sidecar on every request, with no SQL cache layer between them. Engine-direct latency baseline measured at 130–380 ms warm, 700–900 ms cold (budgets 800 / 1500 ms — comfortable headroom). The SQL cache layer becomes worth building only once Phase 4B closes; until then the engine path serves all queries.
- v2 polish items per `PHASE_4C_FOLLOWUPS_v1_0.md`.
- Acharya-panel review of Muhurat scoring (M10-territory).
- The Phase 4C enrichment columns (`special_yogas`, `choghadiya`, `hora`, `inauspicious`, `auspicious`) were not in this master plan's original scope — they were added as a follow-on chat-side enrichment workstream after Wave 1 closed. PR #110 + migration 069 carry them.

### §0.2 — One Operational Finding from Close-out

During the production swap on 2026-05-21, the operator discovered that `bootstrap_panchanga.py` does not register a row in `build_manifests` for its build_id. Two builds (`phase-4c-20260519-153426`, rolled back; `phase-4c-enrich-20260521-r2`, live) required manual `build_manifests` registration to maintain the audit trail. Root cause and proposed fix are documented in `BOOTSTRAP_PANCHANGA_BUILD_MANIFESTS_AUDIT_v1_0.md` (Patch A + B). Non-blocking for this seal; must land before the next panchang rebuild.

---

## §1 — Context: Why This Now

The native asked: can the Swiss Ephemeris data we already have (FORENSIC + the ephemeris infrastructure being stood up in Phase 4) be leveraged to give us Drik Panchang–parity functionality, without paid API dependencies, and exposed both as a dashboard surface and as a query-pipeline tool?

Three discoveries from exploration shaped the answer:

1. **Phase 4C `query_panchanga` already exists as a scoped sub-phase** of the Phase 4 Ephemeris Accessibility campaign (per `00_ARCHITECTURE/PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md`). Phase 4A (`query_ephemeris`) closed yesterday (2026-05-19, commit `bd41f13`). Phase 4B (sunrise derivation, `ephemeris_daily` rebuild with MEAN_NODE Rahu fix) is PENDING. Phase 4C is the natural next slot — this is execution unlock, not new strategic ground.

2. **Drik Panchang's content is 100% computable from Swiss Ephemeris + static lookup tables** from classical Muhurta Shastra. No external paid data source is required. The previous research turn (this conversation) established the formulas and gap analysis explicitly.

3. **The query pipeline has a clean `RetrievalTool` interface**, an existing Python sidecar pattern at `/api/compute/[type]`, and a planner that already routes via tool selection. Adding `query_panchanga` is mechanically straightforward — the discipline is in the design, not the wiring.

The native authorised:

- Full GCP infrastructure as needed.
- Best-in-class technology stack (no constraints on libraries / services).
- Both dashboard surface AND query pipeline access.
- Native asked for a master document covering product perspective first, then engineering.

This document is that master.

---

## §2 — Decisions Settled (via brainstorming with native)

Four product decisions were captured before drafting:

| # | Decision | Native's Call |
|---|---|---|
| D1 | Surface scope | Full dedicated `/panchang` page. No dashboard widget. Clean separation as its own first-class section. |
| D2 | Personalisation philosophy | Generic by default + dropdown to apply any client's birth chart. Supports multi-native future from day one. |
| D3 | Actionable MVP features (priority order) | (1) Muhurat Finder → (2) Calendar Export (.ics) → (3) Ask-Madhav prompt suggestions. Daily briefing dropped — native does not want it. |
| D4 | Macro plan placement | Phase 4C insertion, separate-but-layered above ephemeris. No new M-phase. No bundling into FORENSIC. |
| D5 | Sequencing | Concurrent workstream alongside active M5-A. Precedent: Phase O Observatory, Chat V2 Big Bang. Declared in CLAUDE.md §E. |

---

## §3 — Strategic Placement (the two questions the native flagged)

### §3.1 — fMRS (FORENSIC) wrapping decision: KEEP SEPARATE, layered

The native asked: *"should we wrap fMRS into Panchang, since planetary positions are part of Panchang?"* The answer is **no** — keep separate but layer one above the other.

Why:

| Reason | Detail |
|---|---|
| Different temporal cardinality | FORENSIC is a natal snapshot (one moment: Feb 5, 1984, 10:43 IST). Panchang is daily continuous (every day, dawn to dawn, location-anchored). Wrapping a snapshot into a continuous time series collapses two different abstractions. |
| Different access patterns | FORENSIC is read once at session open as a constant. Panchang is queried per-date, per-location. Different cache strategies, different indexes. |
| Different mutation surface | FORENSIC is sealed (B.10 — no fabricated computation, only Swiss Ephemeris regen on bump). Panchang is recomputed daily for new dates. Different change discipline. |
| Layer purity | FORENSIC = L1 facts (natal). Panchang = L1 derivatives (daily, computed). Both L1, but distinct derivation lineages. Conflating them violates B.1 (Facts/Interpretation separation extended to Facts/Derivatives). |
| Phase 4A precedent | The ephemeris query layer (`query_ephemeris`) is already its own retrieval tool, sitting alongside FORENSIC. Panchang follows the same pattern. |

The relationship is **layered, not wrapped**:

```
                    L2.5  ─ MSR / UCN / CDLM / RM / CGM (synthesis)
                            ▲
                            │   (signal generation, e.g.
                            │    "today is Sarvartha Siddhi Yoga for native")
                            │
                    L1.5  ─ PANCHANG_DAILY (this work)
                            ▲                ▲
                            │                │
                    L1 ── EPHEMERIS_DAILY    FORENSIC
                          (Phase 4A,         (natal snapshot,
                           657K rows)         sealed v8.0)
                            ▲                ▲
                            │                │
                            └─── pyswisseph ─┘
                                 (Python sidecar)
```

Panchang reads from `EPHEMERIS_DAILY` (planetary positions) and combines with static Muhurta Shastra lookup tables to produce daily Panchang state. It does **NOT** touch FORENSIC except when the user opts in to "Personalise for [client]" — at which point Panchang reads the client's birth Nakshatra, birth Lagna, and current Dasha from FORENSIC to overlay Tara Bala, Chandra Bala, and dasha-aware muhurat scoring.

### §3.2 — M11 vs Phase 4C insertion: PHASE 4C INSERTION

The macro plan closes at M10. `MACRO_PLAN_v2_0.md §3.9` frames post-M10 explicitly as governance state (publication, retirement) — not new strategic phases. Adding M11 would require macro plan amendment and would conflict with the project's stated scope-boundary discipline (B.1 + MACRO_PLAN §Scope Boundary: do not pre-build for phases later than the active one).

Panchang fits Phase 4C exactly as already specified. The ephemeris accessibility campaign (PHASE_4) is the right home: it's the infrastructure spine for everything date-indexed and ephemeris-derived. Phase 4 already enumerates:

| Sub-phase | Status | Scope |
|---|---|---|
| 4A | CLOSED (`bd41f13`, 2026-05-19) | `query_ephemeris` RetrievalTool wrapping `ephemeris_daily` (657K rows, 1900–2100) |
| 4B | PENDING | Sunrise derivation, Migration 059, TRUE_NODE → MEAN_NODE Rahu fix, 657K row rebuild |
| **4C** | **THIS WORK** | `query_panchanga` RetrievalTool + `PANCHANG_DAILY` asset + `/panchang` UI surface |
| 4D | PENDING | `query_transit_event` for ingress/aspect/conjunction/station search |

No macro plan amendment required. Phase 4C is sealed by:

1. Author `00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md` (this document, promoted)
2. Update `PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md §B` state tracker
3. Declare concurrent workstream in `CLAUDE.md §E` (alongside Phase O, Chat V2, etc.)
4. Update `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` with `PANCHANG_DAILY` canonical asset

---

## §4 — Product Specification

### §4.1 — Route & shell

- **Route:** `/panchang` (Next.js App Router, server component layout + client components)
- **Access:** Auth-gated. Pattern from `dashboard/layout.tsx`. All authenticated roles (super_admin, admin, client).
- **Nav entry:** Sidebar rail icon in `AppShell` (`platform/src/components/shared/AppShell.tsx`). Icon: stylised lunar crescent + sun (custom SVG, gold-accented to match brand).
- **Layout root:** `ZoneRoot` + `AppShell` (same wrapper as `/dashboard`). Brand styling: gold accents (`#fce29a`, `#d4af37`) on dark (`#1c1c1a`), brand-card containers, Inter sans + Source Serif 4.

### §4.2 — Page layout (ASCII mockup)

```
┌────────────────────────────────────────────────────────────────────┐
│ AppShell rail │  PANCHANG                                          │
│               │  ┌──────────────────────────────────────────────┐  │
│ [home]        │  │  DATE PICKER ◀ Tue, May 19 2026 ▶            │  │
│ [dashboard]   │  │                                              │  │
│ [build]       │  │  LOCATION ▼ New Delhi, IN     PERSONALISE ▼ │  │
│ [consume]     │  │                                              │  │
│ [▶ panchang]  │  └──────────────────────────────────────────────┘  │
│ [admin]       │                                                    │
│               │  ┌─── PRIMARY STRIP (5 angas + Vara) ───────────┐  │
│               │  │ TITHI       Shukla Dvitiya        ends 17:42 │  │
│               │  │ NAKSHATRA   Bharani               ends 22:15 │  │
│               │  │ YOGA        Shubha                ends 11:03 │  │
│               │  │ KARANA      Bava → Balava                    │  │
│               │  │ VARA        Mangalavara (Tuesday)             │  │
│               │  │ PAKSHA      Shukla   MASA Vaishakha          │  │
│               │  └──────────────────────────────────────────────┘  │
│               │                                                    │
│               │  ┌── TIMINGS ──────────┬── PLANETARY POSITIONS ──┐│
│               │  │ Sunrise   05:42     │ Sun     Mesha 04°23'   ││
│               │  │ Sunset    19:08     │ Moon    Mesha 18°51'   ││
│               │  │ Moonrise  09:14     │ Mars    Mithuna 12°R   ││
│               │  │ Moonset   22:01     │ Mercury Mesha 09°(C)   ││
│               │  ├─────────────────────┤ Jupiter Mithuna 25°    ││
│               │  │ Rahu Kalam 15:24-16:53│ Venus Vrishabha 02°  ││
│               │  │ Yamagandam 09:10-10:38│ Saturn Kumbha 18°R   ││
│               │  │ Gulika Kal 12:25-13:54│ Rahu    Meena 27°    ││
│               │  ├─────────────────────┤ Ketu    Kanya 27°      ││
│               │  │ Abhijit    11:55-12:42│                     ││
│               │  │ Brahma Muh 04:54-05:42│  (legend: R retro,   ││
│               │  │ Amrit Kalam 07:08-08:33│   C combust)        ││
│               │  └─────────────────────┴────────────────────────┘│
│               │                                                    │
│               │  ┌── ACTIVE SPECIAL YOGAS (today) ──────────────┐  │
│               │  │ ✓ Amrit Siddhi Yoga    05:42 → 22:15  ★★★    │  │
│               │  │ ✓ Vidhdhi Yoga         all day        ★★     │  │
│               │  │ ✗ Bhadra (avoid)       16:30 → 22:00  ⚠       │  │
│               │  └──────────────────────────────────────────────┘  │
│               │                                                    │
│               │  ┌── CHOGHADIYA & HORA (collapsed by default) ──┐  │
│               │  │ ▶ Day Choghadiya  (8 segments)               │  │
│               │  │ ▶ Night Choghadiya (8 segments)              │  │
│               │  │ ▶ Hora (24 planetary hours)                  │  │
│               │  └──────────────────────────────────────────────┘  │
│               │                                                    │
│               │  ┌── ACTION BAR (sticky bottom on mobile) ──────┐  │
│               │  │ [🔎 Find Muhurat]  [📅 Export to Calendar]   │  │
│               │  │ [💬 Ask Madhav about this day]                │  │
│               │  └──────────────────────────────────────────────┘  │
└───────────────┴────────────────────────────────────────────────────┘
```

### §4.3 — Personalisation dropdown (D2)

A **Personalise ▼** dropdown sits in the page header alongside the location selector.

- **Default state:** "Generic Panchang" (no overlay).
- **Options:** A list of clients pulled from the `Chart` table (filtered by current user's access). Selecting one applies that chart's birth Nakshatra + Lagna + active Dasha as a context overlay.

**Overlay effects when personalised:**

- Nakshatra row gets a **Tara Bala** badge (Janma / Sampat / Vipat / Kshema / Pratyari / Sadhaka / Vadha / Mitra / Ati Mitra).
- Moon row gets a **Chandra Bala** badge (favourable/unfavourable rashis relative to native's Moon).
- Special yogas list gets a "for [client]" annotation when the yoga is dasha-amplified.
- Muhurat Finder (§4.4.1) becomes native-aware — windows scored against the selected chart.

- **Persistence:** Last-used personalisation persists per-user in localStorage; no cross-session pollution.
- **Resetting:** "Clear personalisation" option at top of dropdown returns to Generic.

### §4.4 — Action layer (the "actionable" requirement)

Three actions ship in MVP, in priority order.

#### §4.4.1 — Muhurat Finder (priority 1)

- **Pattern:** Modal or full-page form that takes an event type + date range and returns ranked auspicious windows.
- **Event types (MVP set, drawn from classical Muhurta Shastra):**

| Category | Events |
|---|---|
| Life-cycle | Vivah (marriage), Namakarana (naming), Mundan (tonsure), Upanayana (sacred thread), Annaprasana (first solids) |
| Property | Griha Pravesh (housewarming), Bhumi Puja (groundbreaking), Property Purchase, Vehicle Purchase |
| Commerce | Vyapara (business start), Contract Signing, Investment, Loan |
| Travel & social | Yatra (travel), Important Meeting, Public Speaking |
| Spiritual | Mantra Initiation, Puja, Vrata Beginning |

**Scoring rubric (transparent, not magic):**

For each candidate date+window in the range, compute a score:

```
muhurat_score =
    W_tithi    * tithi_quality_for_event(tithi, event)
  + W_nakshatra* nakshatra_quality_for_event(nakshatra, event)
  + W_vara    * vara_quality_for_event(vara, event)
  + W_yoga    * (1 if active_special_yoga(SARVARTHA_SIDDHI|AMRIT_SIDDHI|...) else 0)
  + W_planet  * (1 - combust_penalty(Guru, Shukra) - leap_lunar_month_penalty)
  + W_native  * (chandra_bala + tara_bala) [only if personalised]
  - W_avoid   * (1 if in_rahu_kalam | in_yamagandam | in_dur_muhurta else 0)
```

Weights `W_*` are event-specific and read from a YAML config so the rubric is auditable, tunable, and not buried in code. The shastra tables for `tithi_quality_for_event` etc. live in the `panchang_engine` Python module.

**Output:** Top 10 windows in the requested range, each showing:

- Date, time window, duration
- Star rating (1–5 ★)
- Breakdown of why it scored well (e.g., "Pushya Nakshatra on Thursday → Guru Pushya Yoga; Jupiter not combust; Shukla Paksha 5th Tithi favourable for Griha Pravesh")
- "Export this window to my calendar" inline action
- "Ask Madhav about this date" deep link

#### §4.4.2 — Calendar Export (.ics) (priority 2)

**Pattern:** "Export to Calendar" button on three surfaces:

1. **The Panchang page itself:** export the current day's significant windows (Rahu/Yama/Gulika to avoid, Abhijit/Brahma to use, active special yogas).
2. **The Muhurat Finder results:** export selected windows as time-blocked events.
3. **A "Subscribe to Panchang feed" option:** outputs a hosted iCal URL (`/api/panchang/feed.ics?location=...&personalise=...`) that user can subscribe to in Google Calendar / Apple Calendar / Outlook — auto-updates daily.

**Event format:**

- Title: `Sarvartha Siddhi Yoga` / `Rahu Kalam (avoid)` / `Muhurat: Griha Pravesh ★★★★★`
- Description: full breakdown of why this window is auspicious or inauspicious, with link back to the `/panchang?d=YYYY-MM-DD` page
- Location: human-readable location name (e.g., "Bhubaneswar, IN")
- Category: `MARSYS-Panchang/auspicious` or `MARSYS-Panchang/avoid` (allows users to colour-code)

**Implementation:** `ical` npm package, server-side route at `/api/panchang/ics`.

#### §4.4.3 — Ask-Madhav Prompt Suggestions (priority 3)

**Pattern:** A discreet "💬 Ask Madhav" affordance attached to every Panchang element. Clicking opens the chat (`/clients/[id]/consume`) with the question pre-loaded and the day's Panchang state attached as context.

**Suggested prompts surface automatically based on what's visible:**

- On the Tithi row: *"What does Shukla Dvitiya mean for me today?"*
- On an active special yoga: *"Explain why today's Amrit Siddhi Yoga matters for [event]"*
- On a planetary retrograde indicator: *"What's Mars retrograde doing in my chart right now?"*
- On Tara Bala badge (when personalised): *"Is today a Mitra Tara for me? What does that mean for planning?"*
- On a Muhurat Finder result: *"Walk me through why this date is ranked highest for our wedding"*

**Context injection:**

- Prompt arrives in chat with hidden context block containing the day's full Panchang JSON.
- Pipeline planner sees Panchang context → can call `query_panchanga` for richer detail or skip if context suffices.

This is how Panchang flows into the query pipeline organically — through user-initiated questions that carry Panchang state as context.

---

## §5 — Engineering Architecture

### §5.1 — High-level data flow

```
┌──────────────────────────────────────────────────────────────┐
│  USER  ────────► /panchang (Next.js page, server+client)     │
│                       │                                       │
│                       ▼                                       │
│              Server Component: load today's Panchang          │
│                       │                                       │
│                       ▼                                       │
│  GET /api/panchang/day?date=...&lat=...&lon=...               │
│                       │                                       │
│                       ▼                                       │
│  Next.js API route ── check Cloud SQL cache (panchang_daily)  │
│                       │                                       │
│             ┌─── HIT ─┴─ MISS ───┐                            │
│             ▼                    ▼                            │
│       return cached     POST /api/compute/panchanga           │
│                                  │                            │
│                                  ▼                            │
│                      Python sidecar (pyswisseph)              │
│                      reads ephemeris_daily,                   │
│                      computes 5 angas + timings + yogas       │
│                      writes panchang_daily row,               │
│                      returns full payload                     │
└──────────────────────────────────────────────────────────────┘

For LLM planner:
    planner → tool_calls: [{ tool_name: "query_panchanga", params: {...} }]
        → query_panchanga.retrieve() reads panchang_daily, same cache
        → returns ToolBundle with structured Panchang state
        → synthesis prompt receives it, generates answer with [^N] citations
```

### §5.2 — New canonical asset: PANCHANG_DAILY

Added to `CAPABILITY_MANIFEST.json` as a new entry.

| Field | Value |
|---|---|
| `canonical_id` | `PANCHANG_DAILY_v1_0` |
| `path` | `03_DERIVATIONS/PANCHANG_DAILY_v1_0.md` (schema doc) + Cloud SQL `panchang_daily` table |
| `layer` | L1.5 (derived from L1 ephemeris) |
| `version` | 1.0.0 |
| `status` | PLANNED → IN_DEVELOPMENT → CURRENT |
| `expose_to_chat` | true |
| `floor_asset` | false (computed per query) |

**Schema (`panchang_daily` Cloud SQL table):**

```sql
CREATE TABLE panchang_daily (
  -- composite primary key
  date              DATE        NOT NULL,
  lat               NUMERIC(8,4) NOT NULL,
  lon               NUMERIC(8,4) NOT NULL,
  tz_offset_minutes INTEGER     NOT NULL,
  -- derived from sunrise at (lat, lon, date)
  sunrise_utc       TIMESTAMPTZ NOT NULL,
  sunset_utc        TIMESTAMPTZ NOT NULL,
  moonrise_utc      TIMESTAMPTZ,
  moonset_utc       TIMESTAMPTZ,
  -- 5 angas (sunrise-anchored)
  tithi_id          SMALLINT NOT NULL,  -- 1..30
  tithi_end_utc     TIMESTAMPTZ NOT NULL,
  nakshatra_id      SMALLINT NOT NULL,  -- 1..27
  nakshatra_end_utc TIMESTAMPTZ NOT NULL,
  yoga_id           SMALLINT NOT NULL,  -- 1..27
  yoga_end_utc      TIMESTAMPTZ NOT NULL,
  karana_first_id   SMALLINT NOT NULL,  -- 1..11
  karana_second_id  SMALLINT NOT NULL,
  karana_end_utc    TIMESTAMPTZ NOT NULL,
  vara_id           SMALLINT NOT NULL,  -- 1..7
  paksha            VARCHAR(8) NOT NULL,  -- 'shukla'|'krishna'
  -- timings (computed JSON for flexibility)
  inauspicious      JSONB NOT NULL,  -- {rahu_kalam, yamagandam, gulika_kalam, dur_muhurta[]}
  auspicious        JSONB NOT NULL,  -- {abhijit, brahma_muhurta, amrit_kalam, varjyam}
  choghadiya        JSONB NOT NULL,  -- {day: [...], night: [...]}
  hora              JSONB NOT NULL,  -- 24 planetary hours
  -- special yogas (active periods)
  special_yogas     JSONB NOT NULL,  -- [{yoga: "sarvartha_siddhi", start, end, strength}]
  -- planetary positions at sunrise
  planets           JSONB NOT NULL,  -- {sun: {lon, sign, nakshatra, pada, retrograde, combust}, ...}
  -- audit
  computed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  computation_version VARCHAR(16) NOT NULL,  -- panchang_engine.__version__
  ephemeris_version VARCHAR(16) NOT NULL,    -- swisseph version + .se1 hash
  PRIMARY KEY (date, lat, lon)
);
CREATE INDEX idx_panchang_date ON panchang_daily(date);
CREATE INDEX idx_panchang_special_yogas ON panchang_daily USING GIN(special_yogas);
```

**Cache strategy:**

- Bhubaneswar (native's birth city) and Delhi (likely default) precomputed for 1900–2100 (~146,000 rows × 2 = ~292K rows).
- Other coordinates computed on demand, cached on write.
- TTL: never (rows are mathematically deterministic; only recompute if `computation_version` or `ephemeris_version` changes — handled by migration).

### §5.3 — Computation engine: `panchang_engine` Python module

**Location:** `platform/sidecar/panchang_engine/` (new module in the existing Python sidecar service).

**Files:**

```
panchang_engine/
  __init__.py          # version, public API
  angas.py             # tithi, nakshatra, yoga, karana, vara — pure math
  timings.py           # sunrise/sunset, rahu/yama/gulika, abhijit, choghadiya, hora
  special_yogas.py     # sarvartha_siddhi, amrit_siddhi, ravi/guru_pushya, etc.
  planets.py           # planetary positions, retrograde, combustion
  muhurat.py           # event-specific muhurat scoring
  shastra_tables.py    # static lookup tables from Muhurta Chintamani, Brihat Samhita
  ayanamsha.py         # Lahiri default, configurable
  tests/
    test_angas.py
    test_special_yogas.py
    test_muhurat.py
    fixtures/drik_panchang_30_days.json  # validation set
```

**Public API:**

```python
def compute_panchang(date: date, lat: float, lon: float, tz_offset: int) -> Panchang:
    """Full Panchang for a single day."""

def find_muhurat(event: str, date_from: date, date_to: date, lat: float, lon: float,
                 native_chart: Optional[NatalChart] = None) -> list[MuhuratWindow]:
    """Top auspicious windows for an event in a date range."""

def panchang_range(date_from: date, date_to: date, lat: float, lon: float, tz_offset: int) -> list[Panchang]:
    """Batch compute (for calendar feed)."""
```

**Validation gate:** Cross-check 30 random days against drikpanchang.com. Required precision:

- Tithi/Nakshatra/Yoga IDs: exact match.
- Transition times: within 2 minutes.
- Sunrise/Sunset: within 30 seconds (swisseph is more precise than Drik's display).
- Special yogas presence/absence: exact match.

### §5.4 — RetrievalTool: `query_panchanga`

**Location:** `platform/src/lib/retrieve/query_panchanga.ts`

Conforms to `RetrievalTool` interface (`platform/src/lib/retrieve/types.ts:101`).

```typescript
export const queryPanchanga: RetrievalTool = {
  name: 'query_panchanga',
  version: '1.0.0',
  description: 'Returns daily Panchang state (5 angas, timings, special yogas, planetary positions) for a given date and location. Supports native overlay via chart_id.',
  async retrieve(plan, params) {
    const { date, lat, lon, chart_id, range, fields } = params ?? {};
    // 1. Check panchang_daily cache
    // 2. On miss, POST /api/compute/panchanga
    // 3. If chart_id present, hydrate Tara Bala / Chandra Bala from FORENSIC
    // 4. Apply `fields` projection to control token budget
    // 5. Return ToolBundle
  },
};
```

**Registered in:** `platform/src/lib/retrieve/index.ts:66+` (added to `RETRIEVAL_TOOLS` array).

**Planner integration:** Add to `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md §4` with a few-shot example: *"If the query asks about today's Panchang, an auspicious window, or 'good day for X', call `query_panchanga` with appropriate params."*

**R-TC (transit-context) rule extension:** Panchang is a special case of transit context — the planner's existing R-TC rule (added in Phase 4A) should reference `query_panchanga` when the query is Panchang-specific vs `query_ephemeris` when it's about planetary positions.

### §5.5 — Frontend module

**Location:** `platform/src/app/panchang/`

```
panchang/
  layout.tsx              # AppShell + auth gate
  page.tsx                # Server component, loads today's Panchang
  loading.tsx             # skeleton
  error.tsx               # error boundary
  components/
    PanchangHeader.tsx    # date picker + location + personalise dropdown
    PrimaryStrip.tsx      # 5 angas + Vara
    TimingsPanel.tsx      # sunrise/sunset/inauspicious/auspicious
    PlanetaryGrid.tsx     # 9 grahas + status
    SpecialYogasList.tsx  # active yogas with star ratings
    ChoghadiyaPanel.tsx   # collapsible Choghadiya + Hora
    ActionBar.tsx         # Muhurat Finder / Calendar / Ask Madhav
    MuhuratFinderModal.tsx
    NativeOverlayBadge.tsx
  hooks/
    usePanchangDay.ts     # SWR fetcher for /api/panchang/day
    useChartList.ts       # for personalise dropdown
```

**Component library:** Existing shadcn/ui primitives + brand-card styles. No new design system. New iconography: lunar/solar SVGs added to `platform/src/components/ui/icons/`.

### §5.6 — API routes

| Route | Purpose |
|---|---|
| `GET /api/panchang/day?date=&lat=&lon=&tz=&chart_id=` | Single day Panchang, with optional native overlay |
| `GET /api/panchang/range?from=&to=&lat=&lon=` | Range (for calendar feed, week view) |
| `POST /api/panchang/muhurat` | Muhurat Finder backend (event, range, optional chart_id) |
| `GET /api/panchang/feed.ics?location=&personalise=` | Subscribable iCal feed |
| `POST /api/compute/panchanga` | Sidecar passthrough (internal) — extends existing `[type]` route |

### §5.7 — Observability & tracing

`query_panchanga` calls emit standard pipeline trace steps via the existing emitter pattern (`platform/src/lib/trace/emitter.ts`). Step type: `sql` for cache hits, `external_computation` for sidecar calls. Latency, token budget, and cache hit/miss surfaced in the trace.

Observatory dashboard (existing) gets two new metric panels:

- Panchang sidecar latency (p50/p95/p99)
- Cache hit ratio

---

## §6 — Implementation Phases (the build sequence)

Workstream declared as concurrent alongside M5-A. Phased delivery so each phase is independently shippable and verifiable.

### Phase 4C.0 — Brief & governance (1 session)

- Promote this document to `00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md`
- Update `PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md §B` state tracker
- Declare in `CLAUDE.md §E` concurrent workstreams (Four → Five)
- Add `PANCHANG_DAILY_v1_0` to `CAPABILITY_MANIFEST.json`
- Create `03_DERIVATIONS/PANCHANG_DAILY_v1_0.md` schema document

### Phase 4C.1 — `panchang_engine` Python library (3–4 sessions)

- Build pure-Python module with all 5 angas, timings, special yogas, planetary status
- Encode classical shastra lookup tables (cite source per table)
- Test suite: 30-day validation fixture against Drik Panchang
- **Gate:** All 30 days match Drik to within tolerance (§5.3 validation gate)
- No infra needed yet — runs on dev machine, validates feasibility

### Phase 4C.2 — Schema + cache + sidecar wiring (2 sessions)

- Migration: create `panchang_daily` table
- Extend `/api/compute/[type]` route to accept `panchanga` type
- Wire `panchang_engine` into existing Python sidecar service
- Backfill: Bhubaneswar + Delhi for 1900–2100 (~292K rows, batch job ~6 hrs)
- **Gate:** Sample 100 cached rows match fresh re-computation byte-for-byte

### Phase 4C.3 — `query_panchanga` RetrievalTool (1 session)

- Build the tool, register in `RETRIEVAL_TOOLS`
- Update `PLANNER_PROMPT_v2_0.md` with few-shot example
- Extend R-TC rule to differentiate from `query_ephemeris`
- E2E test: planner picks `query_panchanga` for Panchang queries, synthesis cites correctly
- **Gate:** 10/10 planner picks correct tool on a curated probe set

### Phase 4C.4 — `/panchang` page MVP (3–4 sessions)

- Page shell, header, primary strip, timings panel, planetary grid
- Date picker, location selector
- Active special yogas list
- **Gate:** Visual review against Drik Panchang screenshot for 5 sample days; native sign-off on layout

### Phase 4C.5 — Personalise dropdown + native overlay (1–2 sessions)

- Chart list dropdown
- Tara Bala / Chandra Bala badges
- Native-aware special yoga annotations
- localStorage persistence
- **Gate:** Switching personalisation correctly hydrates from FORENSIC for the selected chart

### Phase 4C.6 — Action 1: Muhurat Finder (3–4 sessions)

- Backend: `find_muhurat` in `panchang_engine` with shastra scoring rubric
- YAML config for event weights
- Frontend: modal form, results list with star ratings + breakdown
- "Export this window to calendar" + "Ask Madhav about this date" inline actions
- **Gate:** 5 manual test events × 30-day range each, results sensible to acharya-grade review

### Phase 4C.7 — Action 2: Calendar Export (.ics) (1–2 sessions)

- Server-side `ical` generation
- `/api/panchang/ics` route (one-off export)
- `/api/panchang/feed.ics` subscribable feed
- Per-event categorisation (auspicious/avoid)
- **Gate:** Round-trip test: export → import to Google Calendar → events render correctly

### Phase 4C.8 — Action 3: Ask-Madhav prompt suggestions (1 session)

- Inline "💬" affordances on every relevant element
- Pre-loaded prompt with hidden Panchang context block
- Deep link into `/clients/[id]/consume` with prompt + context
- **Gate:** Chat receives Panchang context; planner can reference it without extra tool call

### Phase 4C.9 — Polish, telemetry, close (1 session)

- Observatory panels for Panchang sidecar latency + cache hit ratio
- Red-team pass (IS.8(b) — Phase 4 close requires this)
- Update `PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN.md §B` state tracker to CLOSED
- Append M-4C close to `SESSION_LOG.md`
- Update `CLAUDE.md §E` workstream entry to COMPLETE

**Total estimate:** ~16–22 sessions. Concurrent with M5-A.

**Dependency:** Phase 4B must close before Phase 4C.2 can run (the Migration 059 sunrise derivation + MEAN_NODE rebuild). Phase 4C.0 and 4C.1 are 4B-independent and can start immediately.

---

## §7 — Critical Files Map

### Files to create

| Path | Purpose |
|---|---|
| `00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md` | Promoted form of this plan |
| `03_DERIVATIONS/PANCHANG_DAILY_v1_0.md` | Canonical schema document for `PANCHANG_DAILY` asset |
| `platform/sidecar/panchang_engine/__init__.py` | Module entry |
| `platform/sidecar/panchang_engine/angas.py` | 5 angas computation |
| `platform/sidecar/panchang_engine/timings.py` | Sunrise/sunset, Rahu/Yama/Gulika, Abhijit, Choghadiya, Hora |
| `platform/sidecar/panchang_engine/special_yogas.py` | Sarvartha Siddhi, Amrit Siddhi, Ravi/Guru Pushya, etc. |
| `platform/sidecar/panchang_engine/muhurat.py` | Muhurat Finder scoring |
| `platform/sidecar/panchang_engine/shastra_tables.py` | Static classical lookup tables |
| `platform/sidecar/panchang_engine/config/muhurat_weights.yaml` | Auditable scoring weights per event |
| `platform/sidecar/panchang_engine/tests/test_*.py` | Validation suite |
| `platform/migrations/060_create_panchang_daily.sql` | Schema migration |
| `platform/src/lib/retrieve/query_panchanga.ts` | RetrievalTool |
| `platform/src/app/api/panchang/day/route.ts` | Day endpoint |
| `platform/src/app/api/panchang/range/route.ts` | Range endpoint |
| `platform/src/app/api/panchang/muhurat/route.ts` | Muhurat Finder endpoint |
| `platform/src/app/api/panchang/feed.ics/route.ts` | iCal feed |
| `platform/src/app/panchang/layout.tsx` | Auth + AppShell |
| `platform/src/app/panchang/page.tsx` | Page entry |
| `platform/src/app/panchang/components/*.tsx` | UI components (per §5.5) |
| `platform/src/app/panchang/hooks/usePanchangDay.ts` | SWR hook |

### Files to modify

| Path | Modification |
|---|---|
| `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` | Add `PANCHANG_DAILY_v1_0` entry |
| `00_ARCHITECTURE/PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md` | §B state tracker → 4C ACTIVE |
| `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` | §4 add Panchang few-shot; R-TC rule extension |
| `CLAUDE.md` | §E: Four → Five workstreams; add Phase 4C entry |
| `platform/src/lib/retrieve/index.ts` | Register `queryPanchanga` in `RETRIEVAL_TOOLS` |
| `platform/src/app/api/compute/[type]/route.ts` | Add `panchanga` to ALLOWED types |
| `platform/src/components/shared/AppShell.tsx` | Add `/panchang` rail icon + nav entry |

### Files to reuse (no modification, just leverage)

| Path | Why |
|---|---|
| `platform/src/lib/db/client.ts` | Cloud SQL connection — same pattern as `msr_sql.ts` |
| `platform/src/lib/trace/emitter.ts` | Pipeline tracing |
| `platform/src/lib/streams/data_parts.ts` | If we want Panchang to stream as data parts in chat |
| `platform/src/lib/auth/access-control.ts` | `getServerUserWithProfile()` pattern |
| `platform/src/components/ui/*` | shadcn primitives |
| Existing Python sidecar | Already supports ephemeris compute type — just extend |

---

## §8 — Verification & Acceptance

### Per-phase gates (see §6 above)

Each phase has a named gate. No phase claims close without its gate passing.

### Whole-workstream acceptance criteria

| AC | Criterion | Evidence |
|---|---|---|
| AC.4C.1 | `panchang_engine` validates to within tolerance against Drik Panchang for 30 random days | `tests/fixtures/drik_panchang_30_days.json` validation passes |
| AC.4C.2 | `panchang_daily` cache covers Bhubaneswar + Delhi for 1900–2100 | `SELECT COUNT(*) FROM panchang_daily` ≥ 292,000 |
| AC.4C.3 | `query_panchanga` callable from planner with correct tool selection | 10/10 probe set |
| AC.4C.4 | `/panchang` page renders correct data, matches Drik visually for 5 sample days | Manual review with screenshots |
| AC.4C.5 | Personalise dropdown applies overlay correctly | Switch native, verify Tara Bala badges update |
| AC.4C.6 | Muhurat Finder returns acharya-grade rankings for 5 event types | Native + senior acharya review |
| AC.4C.7 | Calendar export round-trips through Google Calendar | Manual test |
| AC.4C.8 | Ask-Madhav prompts launch chat with Panchang context loaded | Manual test |
| AC.4C.9 | Red-team pass per IS.8(b) for Phase 4 close | Red-team report attached to close artifact |

### End-to-end verification (the close moment)

A senior Jyotish acharya should be able to use the `/panchang` page in place of Drik Panchang for daily reference, including running Muhurat Finder for a real event in their life, exporting to their calendar, and asking follow-up questions of the LLM — all without ever leaving the MARSYS app, and with every claim auditable back to Swiss Ephemeris + a classical shastra reference. That's the §J acharya-grade bar.

---

## §9 — Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Drik Panchang's transition times drift slightly from ours (display rounding) | 2-minute tolerance window; if drift exceeds, investigate ayanamsha or sunrise definition |
| Muhurat Finder rankings disputed by native or acharya | Open the `muhurat_weights.yaml` config in-app for transparent tuning; never claim oracle status |
| Sidecar latency under load (Cloud Run cold start) | Aggressive Cloud SQL caching; sidecar only on miss; min instances = 1 in production |
| Phase 4B blocks Phase 4C.2 | Phase 4C.0 + 4C.1 are 4B-independent — start there. 4B can be pursued in parallel by a separate session. |
| Layer-purity violation if Panchang accidentally synthesises | Hard discipline: `panchang_engine` returns computed facts only; any interpretation goes through the LLM synthesis layer, not the engine |
| Calendar feed leaks user identity / location | Signed, time-boxed feed URLs; per-user tokens; never expose `chart_id` in URL |

---

## §10 — Open Decisions for Native (before Phase 4C.0)

Three minor calls remain before promoting this document to the canonical brief:

1. **Default location on the `/panchang` page for first-time visitors** — Bhubaneswar (native's birthplace, project-canonical), or user's geo-IP detected location, or no default (force selection)?

2. **Muhurat Finder event list scope for MVP** — full set per §4.4.1 (15+ events), or a smaller curated set (5–6) for v1 with extension in v2?

3. **Calendar feed authentication** — anonymous time-boxed signed URLs (easier), or full user-token auth (more secure but adds friction)?

These can be settled in the Phase 4C.0 governance session, not now.

---

## Appendix A — Why the macro plan stays untouched

This is a defensive cite for future sessions that may re-question Phase 4C placement.

| Question | Answer |
|---|---|
| Why not M11? | `MACRO_PLAN_v2_0.md §3.9` closes macro phases at M10. Post-M10 is governance state (publication, retirement), not new strategic phases. Adding M11 violates the closed-scope discipline. |
| Why not insert into M2–M5 active work? | M2–M5 are L2.5 synthesis layer phases. Panchang is L1.5 (derived facts). Different layer, different lineage. |
| Why a sub-phase of Phase 4 specifically? | Phase 4 is the ephemeris infrastructure spine (`query_ephemeris`, sunrise derivation, transit search). Panchang is the next logical layer on top of that infrastructure. Phase 4C is already named in `PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md §B`. |
| Why concurrent workstream and not M5-pause? | Precedent: Phase O Observatory and Chat V2 Big Bang both ran as concurrent workstreams alongside active macro-phases. `CLAUDE.md §E` codifies this pattern. M5-A focus discipline is preserved. |

---

## Appendix B — Why FORENSIC stays separate

| Question | Answer |
|---|---|
| Planetary positions are in both — why duplicate? | FORENSIC stores positions at ONE moment (natal). PANCHANG_DAILY stores positions at sunrise of every day. Same kind of data, different temporal cardinality. |
| Could PANCHANG_DAILY have replaced FORENSIC for the native? | No — FORENSIC carries 27 sections beyond planet longitudes (divisional charts, dasha systems, sahams, special lagnas, yogas register). PANCHANG_DAILY is a strict subset of date-indexed daily state. |
| When does Panchang touch FORENSIC? | Only via the personalise overlay: read native's birth Nakshatra + Lagna + active Dasha from FORENSIC to overlay Tara Bala / Chandra Bala / dasha-aware muhurat scoring. Read-only access. |

---

*End of Master Design Plan v1.0. Sealed 2026-05-21 as `00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md` (COMPLETE-AS-SHIPPED). Companion brief at `00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md` carries the execution record; `CLAUDE.md §E Phase 4C` carries the production close-out summary; `BOOTSTRAP_PANCHANGA_BUILD_MANIFESTS_AUDIT_v1_0.md` carries the one operational finding from close-out (non-blocking; must land before next panchang rebuild).*
