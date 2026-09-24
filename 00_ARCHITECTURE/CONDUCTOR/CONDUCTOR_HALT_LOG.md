# CONDUCTOR Halt Log

Append-only record of every halt the orchestrator emitted. Read top-down for
the full halt history; most recent halt is at the bottom.

**Do NOT edit existing entries.** Update `resolution_status` in a `## RESOLUTION`
sub-entry appended immediately below the entry being resolved.

## Schema

Each entry contains:

| Field | Description |
|---|---|
| `session_id` | Queue entry session_id that triggered the halt |
| `failure_class` | `gate_failed`, `sub_agent_halt`, `human_approval_required`, or `requires_brief_authoring` |
| `timestamp` | ISO 8601 timestamp of the halt |
| `last_passed` | session_id of the last entry that reached `status: passed`, or `"none"` |
| `queue_position` | Position of the halted entry in the queue (e.g. `3 of 11`) |
| `resolution_status` | `open`, `resumed`, `skipped`, or `abandoned` |
| `failure_context` | Gate stderr (≤1000 chars) or sub-agent `human_decision_needed` text |
| `gate_output` | Gate stdout (≤500 chars), or `"(gate not run)"` |
| `resolution_paths` | RESUME / SKIP / ABANDON options |

---

<!-- Conductor appends entries below this line. Do not edit above. -->

## 4C-1-S2 — HALT — 2026-05-19T18:46:00+05:30

| Field | Value |
|---|---|
| Session | 4C-1-S2 |
| Failure class | requires_brief_authoring |
| Timestamp | 2026-05-19T18:46:00+05:30 |
| Last passed | 4C-1-S1 |
| Queue position | 2 of 11 |
| Resolution status | open |

### Failure context

4C-1-S1 has closed. Cowork session needed to author CLAUDECODE_BRIEF_PHASE_4C_1_S2_v1_0.md covering: special_yogas.py implementation, Drik fixture extension to 30 days (10 days in S1), muhurat scoring scaffold, and shastra_tables.py lookup tables. Scope: platform/sidecar/panchang_engine/ only.

### Gate output

(gate not run — entry blocked on requires_brief_authoring)

### Suggested resolution paths

- [Author the brief in Cowork, commit it, update queue entry requires_brief_authoring to false, then re-paste kickoff]
- SKIP 4C-1-S2 — orchestrator marks skipped + advances (not recommended)
- ABANDON — orchestrator stops permanently

---

## 4C-1-S1 — HALT — 2026-05-19T18:38:00+05:30

| Field | Value |
|---|---|
| Session | 4C-1-S1 |
| Failure class | sub_agent_halt |
| Timestamp | 2026-05-19T18:38:00+05:30 |
| Last passed | SMOKE-S0 |
| Queue position | 1 of 11 |
| Resolution status | open |

### Failure context

Sub-agent did not emit a parseable FINAL_SUMMARY block. API stream idle timeout after ~36 minutes of work (30 tool uses). Sub-agent completed Items 1–3 (3 commits: fa3bf1d, 21cd781, 4eb39ab) and wrote angas.py (Item 4) but timed out before committing it. Items 5–12 not attempted.

### Gate output

(gate not run — sub-agent timed out before completing implementation)

### Suggested resolution paths

- RESUME 4C-1-S1 — orchestrator retries with a recovery sub-agent briefed on partial state
- SKIP 4C-1-S1 — orchestrator marks skipped + advances (not recommended — gate not satisfied)
- ABANDON — orchestrator stops permanently

---

## 4C-1-S1 — HALT — RESOLUTION — 2026-05-19T18:38:30+05:30

Conductor issued RESUME 4C-1-S1. Recovery sub-agent spawned with full context of partial
state: Items 1–3 committed, angas.py written (uncommitted), Items 5–12 pending.
Recovery sub-agent instructed to commit angas.py, create all remaining modules, and
complete the Drik parity gate.

---

## 4C-2 — HALT — 2026-05-19T22:46:00+05:30

| Field | Value |
|---|---|
| Session | 4C-2 |
| Failure class | requires_brief_authoring |
| Timestamp | 2026-05-19T22:46:00+05:30 |
| Last passed | 4C-1-S2 |
| Queue position | 4 of 11 |
| Resolution status | open |

### Failure context

Entry has `requires_brief_authoring: true` and `requires_human_approval: true`. Brief `CLAUDECODE_BRIEF_PHASE_4C_2_v1_0.md` does not yet exist.

**External gate note (phase_4b_closed):** The check_command regex `4B.*CLOSED` returned exit 0 via a **false positive** — it matched `M4-B-CLOSED` in Madhav's CURRENT_STATE_v1_0.md (M4 macro sub-phase B), NOT Phase 4B of the Panchang ephemeris accessibility plan. Phase 4B (sunrise derivation + MEAN_NODE rebuild) is a separate pending workstream that has NOT closed. Before authoring the 4C-2 brief, verify Phase 4B status independently. The check_command should be tightened to use a more specific pattern (e.g., `Phase 4B.*CLOSED\|PHASE_4B_CLOSED\|4C.*Phase 4B.*COMPLETE`) to avoid this false match.

### Gate output (truncated to 500 chars)

```
(external gate check_command exited 0 — false positive as described above)
```

### Suggested resolution paths

- **[RECOMMENDED]** Author a more specific phase_4b_closed check_command in session_queue.yaml before proceeding — the current regex is too broad. Then author Phase 4B brief in a Cowork session and wait for Phase 4B to close before authoring the 4C-2 brief.
- SKIP 4C-2 — mark skipped, advance to 4C-3 (query_panchanga RetrievalTool — no SQL dependency; can work directly against the engine); requires Cowork brief authoring for 4C-3.
- ABANDON — stop permanently.

---

## 4C-4 — HALT — 2026-05-19T23:20:00+05:30

| Field | Value |
|---|---|
| Session | 4C-4 |
| Failure class | requires_brief_authoring |
| Timestamp | 2026-05-19T23:20:00+05:30 |
| Last passed | 4C-3 |
| Queue position | 6 of 11 |
| Resolution status | open |

### Failure context

Entry has `requires_brief_authoring: true` and `requires_human_approval: true`. Brief `CLAUDECODE_BRIEF_PHASE_4C_4_v1_0.md` does not yet exist. This is the `/panchang` UI page — the first frontend phase of 4C. It is intentionally gated on human brief authoring because it requires native sign-off on layout (5-anga primary strip, timings panel, planetary grid, date picker, location selector, active special yogas list) with visual review vs Drik Panchang for 5 sample days. Note: Phase 4C.4 is 3–4 sub-sessions; the brief should break scope into 4C-4-S1/S2/S3/S4 with sequential deps.

### Gate output

(gate not run — entry blocked on requires_brief_authoring)

### Suggested resolution paths

- [Author CLAUDECODE_BRIEF_PHASE_4C_4_v1_0.md in Cowork; set requires_brief_authoring: false + requires_human_approval: false in queue entry; then re-paste kickoff]
- SKIP 4C-4 — orchestrator marks skipped + advances (not recommended — skips entire UI layer)
- ABANDON — orchestrator stops permanently

---

## 4C-4-S4 — HALT — 2026-05-20T01:23:00+05:30

| Field | Value |
|---|---|
| Session | 4C-4-S4 |
| Failure class | gate_failed |
| Timestamp | 2026-05-20T01:23:00+05:30 |
| Last passed | 4C-4-S3 |
| Queue position | 9 of 17 |
| Resolution status | open |

### Failure context

Sub-agent returned `status: PASS` and self-updated queue to `passed`, but orchestrator gate command `npm test -- src/app/panchang` exited non-zero (1 test failed).

**Failing test:** `PanchangHeader > Personalise button is present and disabled (4C-5 scope)`
**File:** `platform/src/app/panchang/__tests__/PanchangHeader.test.tsx:97`

Root cause: AC.4C4S4.3 upgraded the Personalise control from a static disabled button to an interactive `<select>` element (with "Generic Panchang" default + disabled 4C-5 hint option). The S1-era test still queries `getByLabelText('Personalise (coming soon)')` which matched the old button's `aria-label`. The new `<select>` element does not carry that exact aria-label.

**Fix (trivial):** Update `PanchangHeader.test.tsx:97` to query the Personalise select by its actual rendered aria-label or by role (`getByRole('combobox', { name: /personalise/i })`), then verify it is not disabled (it is now enabled as a select). Then RESUME 4C-4-S4.

### Gate output (truncated to 500 chars)

```
Test Files  1 failed | 4 passed (5)
Tests  1 failed | 56 passed (57)
FAIL  src/app/panchang/__tests__/PanchangHeader.test.tsx >
  PanchangHeader > Personalise button is present and disabled (4C-5 scope)
TestingLibraryElementError: Unable to find a label with the text of: Personalise (coming soon)
```

### Suggested resolution paths

- **RESUME 4C-4-S4** — fix test at `platform/src/app/panchang/__tests__/PanchangHeader.test.tsx:97` to match the select-based Personalise control, then re-kick the conductor
- SKIP 4C-4-S4 — mark skipped + advance to 4C-5 (not recommended — skips ActionBar + phase 4C.4 close artifact)
- ABANDON — orchestrator stops permanently

---

## 4C-9 — HALT — 2026-05-20T05:19:00+05:30

| Field | Value |
|---|---|
| Session | 4C-9 |
| Failure class | human_approval_required |
| Timestamp | 2026-05-20T05:19:00+05:30 |
| Last passed | 4C-8 |
| Queue position | 17 of 17 |
| Resolution status | open |

### Failure context

Entry has `requires_human_approval: true`. 4C-9 is the Wave 1 close session: polish, telemetry, red-team, CLAUDE.md amendment apply, Phase 4C close artifact, HANDOFF_WAVE_1.md. Human approval required before executing.

**Decision prompt (verbatim):**
4C-8 has closed. Phase 4C MVP is feature-complete. Approve to execute 4C-9 (Wave 1 close): polish, telemetry, red-team, CLAUDE.md amendment apply, Phase 4C close artifact, HANDOFF_WAVE_1.md. Reply APPROVE 4C-9, SKIP 4C-9, or ABANDON.

### Gate output

(gate not run — entry blocked on requires_human_approval)

### Suggested resolution paths

- APPROVE 4C-9 — set requires_human_approval: false in queue, then re-paste kickoff
- SKIP 4C-9 — mark skipped + advance (wave would end without close artifacts)
- ABANDON — orchestrator stops permanently

---

## 4C-9 — RESOLVED — 2026-05-20T06:22:00+05:30

### Resolution

4C-9 approved by native (requires_human_approval flipped false via approval script 2026-05-20). Sub-agent executed and completed all 12 ACs. Queue marked COMPLETE. Gate command had 2 pre-existing failures (schema_validator timestamp error + drift_detector directory error) — both confirmed pre-existing via git bisect; scoped-gate PASS applied per 4C-6-S4 precedent.

| Field | Value |
|---|---|
| Prior halt | 4C-9 — HALT — human_approval_required |
| Resolution | PASS (scoped-gate) |
| Resolved at | 2026-05-20T06:22:00+05:30 |

---

## HALT: FORENSIC_GATE — 2026-06-12T16:24:35.617185+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-12T16:24:35.617787+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-12T16:24:35.618108+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-15T15:58:16.964807+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-15T15:58:16.965340+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-15T15:58:16.965664+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-16T09:54:43.382229+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-16T09:54:43.382733+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-16T09:54:43.383074+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-16T10:02:55.585328+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-16T10:02:55.588468+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-16T10:02:55.588830+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-16T10:09:14.970426+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-16T10:09:14.970920+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-16T10:09:14.971258+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-16T10:13:36.516085+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-16T10:13:36.516447+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-16T10:13:36.516771+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-17T19:30:58.936543+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-17T19:30:58.937041+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-17T19:30:58.937436+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-17T20:25:22.165746+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-17T20:25:22.166351+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-17T20:25:22.166656+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-18T13:37:52.316125+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-18T13:37:52.316629+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-18T13:37:52.316943+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-18T13:48:10.745929+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-18T13:48:10.746266+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-18T13:48:10.746573+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-18T13:48:38.219649+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-18T13:48:38.219971+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-18T13:48:38.220266+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-20T13:40:30.822464+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-20T13:40:30.823129+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-20T13:40:30.823515+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-20T13:45:55.365723+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-20T13:45:55.366302+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-20T13:45:55.366659+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-20T14:01:14.336072+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-20T14:01:14.336611+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-20T14:01:14.336958+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-20T14:02:52.088757+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-20T14:02:52.089101+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-20T14:02:52.089390+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-25T15:06:43.947867+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-25T15:06:50.853452+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-25T15:06:50.853829+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-25T15:06:50.854157+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-26T00:11:59.306223+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-26T00:11:59.306797+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-26T00:11:59.307129+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-26T00:36:28.996483+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-26T00:36:28.996834+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-26T00:36:28.997162+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-26T00:37:52.289154+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-26T00:37:52.289557+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-26T00:37:52.289913+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-26T16:15:26.450118+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-26T16:15:26.450572+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-26T16:15:26.450910+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-26T16:17:24.731961+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-26T16:17:24.732544+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-26T16:17:24.732885+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-27T08:03:24.337780+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-27T08:03:24.338265+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-27T08:03:24.338568+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-27T08:04:25.477425+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-27T08:04:25.477818+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-27T08:04:25.478129+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-28T21:51:22.848520+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-28T21:51:22.849111+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-28T21:51:22.849505+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-28T22:11:43.730799+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-28T22:11:43.731270+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-28T22:11:43.731693+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-28T22:41:29.367587+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-28T22:41:29.368450+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-28T22:41:29.368857+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-28T22:41:58.730995+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-28T22:41:58.731443+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-28T22:41:58.731795+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-29T02:27:45.901143+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:27:45.901790+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:27:45.902858+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-29T02:43:29.439322+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:43:29.439880+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:43:29.440221+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-29T02:45:00.410661+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:45:00.411104+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:45:00.411437+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-29T02:46:23.633073+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:46:23.633490+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:46:23.633811+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-29T02:53:07.404544+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:53:07.404933+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:53:07.405233+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-29T02:54:55.550290+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:54:55.550665+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:54:55.551001+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-29T02:55:18.380962+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:55:18.381364+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:55:18.381678+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-29T02:55:38.005572+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:55:38.005968+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:55:38.006283+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-29T02:55:57.610108+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:55:57.610511+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:55:57.610829+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-29T02:56:53.967485+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:56:53.967892+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:56:53.968214+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-29T02:59:27.941512+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:59:27.941932+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T02:59:27.942248+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-06-29T15:31:45.862079+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T15:31:45.862739+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-06-29T15:31:45.863102+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-07-05T18:19:44.295239+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-05T18:19:44.295865+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-05T18:19:44.296287+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-07-07T19:26:51.974324+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-07T19:26:51.974738+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-07T19:26:51.975055+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-07-07T20:31:09.747511+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-07T20:31:09.748044+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-07T20:31:09.748389+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-07-16T14:45:24.624724+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-16T14:45:24.625166+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-16T14:45:24.625503+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-07-16T17:08:59.129587+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-16T17:08:59.130046+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-16T17:08:59.130378+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-07-16T19:19:33.613018+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-16T19:19:33.613514+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-16T19:19:33.613841+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-07-16T20:31:48.059417+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-16T20:31:48.059786+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-16T20:31:48.060109+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-07-16T21:44:22.380130+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-16T21:44:22.380684+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-16T21:44:22.381031+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-07-17T00:45:59.746140+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-17T00:45:59.746626+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-17T00:45:59.746946+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-07-17T18:25:15.403927+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-17T18:25:15.404553+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-17T18:25:15.404903+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-07-28T18:40:17.963899+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-28T18:40:17.964487+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-28T18:40:17.964836+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.

## HALT: FORENSIC_GATE — 2026-07-28T18:48:34.254387+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Sun sign expected Capricorn, got 'Aries' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-28T18:48:34.254810+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini' (ayanamsha=lahiri_chitrapaksha)

## HALT: FORENSIC_GATE — 2026-07-28T18:48:34.255139+00:00
FORENSIC GATE FAILED:
  - FORENSIC FAIL: Lagna sign expected 'Aries', got 'Scorpio' (ayanamsha=lahiri_chitrapaksha). Known trap: NOT Scorpio.
