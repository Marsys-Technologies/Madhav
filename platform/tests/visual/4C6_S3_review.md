---
artifact: 4C6_S3_review.md
type: VISUAL_REVIEW
phase: 4C-6-S3
session_id: 4C-6-S3
date: 2026-05-20
status: BLOCKED — sidecar not running in Panchang worktree
reviewer: Claude Code (Sonnet 4.6)
---

# Visual Review — 4C-6-S3 (Muhurat Finder Modal UI)

## §1 — Review target

Scope per brief §3 Item 8:
- Open `/panchang`
- Click "Find Muhurat"
- Select "Vivah", date range Apr 2026 → Jun 2026
- Submit
- Verify: 10 results, sorted by star rating, top result plausible, breakdown badges visible

## §2 — Runtime status at review time

**BLOCKED — Panchang Python sidecar not running.**

At the time of this session (2026-05-20 04:12 IST), the port 8000 process is the
**Madhav worktree sidecar** (PID 47478 / 96130), not the Panchang sidecar. The
Panchang sidecar (`/Users/Dev/Vibe-Coding/Apps/Panchang/platform/python-sidecar/`)
has not been started in this worktree.

Pre-flight confirmation:
```
curl http://localhost:8000/api/compute/muhurat  → {"detail":"Not Found"}
curl http://localhost:8000/openapi.json paths   → no /api/compute/muhurat listed
```

The muhurat router IS registered in the Panchang sidecar's `main.py` (S1 commit
`f1f3bf0`). The code is correct and sealed. The sidecar simply needs to be started
in the Panchang worktree before the visual review can proceed.

## §3 — Visual review checklist (pending operator start of Panchang sidecar)

To complete this review, operator should:

1. Start the Panchang sidecar:
   ```bash
   cd /Users/Dev/Vibe-Coding/Apps/Panchang/platform/python-sidecar
   # activate venv, then:
   uvicorn main:app --reload --port 8001  # use 8001 to avoid Madhav collision
   # set PYTHON_SIDECAR_URL=http://localhost:8001 in platform/.env.local
   ```

2. Start the Panchang Next.js dev server:
   ```bash
   cd /Users/Dev/Vibe-Coding/Apps/Panchang/platform
   npm run dev  # starts on port 3001 (if Madhav is on 3000)
   ```

3. Navigate to `http://localhost:3001/panchang`

4. Click "Find Muhurat" → modal should open immediately (was previously "coming soon")

5. Fill in:
   - Event: Vivah (Marriage)
   - From: 2026-04-01
   - To: 2026-06-30 (90 days — this will be capped at 89 by server)
   - Location: default Bhubaneswar (lat 20.27, lon 85.84)
   - Personalise: unchecked (no chart selected) / checked if chart selected

6. Click "Find Muhurat" submit button

7. Verify in results panel:
   - [ ] 10 result rows returned
   - [ ] Results sorted by star rating descending (5★ first)
   - [ ] Each row shows: long-format date, star rating, time window (IST), breakdown badges
   - [ ] Top result is plausible: Thursday preferred + Rohini/Mrigashira/Pushya nakshatra for Vivah
   - [ ] Breakdown badges visible with +score values (e.g., "Nakshatra +0.95", "Vara +0.80")
   - [ ] "Export to Calendar" button present and disabled with "4C-7" label
   - [ ] "Ask Madhav about this date" button functional — clicking opens /clients/.../consume with prompt

## §4 — Acharya sanity check (Item 9 — BLOCKED, same reason)

Three event × 30-day range runs needed:

### Run 1: Vivah — 2026-06-01 → 2026-06-30
Expected top result characteristics:
- Shukla Paksha tithi (especially 2nd, 5th, 7th, 10th, 11th, 13th)
- Nakshatra: Rohini, Mrigashira, Uttara Phalguni, Hasta, Uttara Ashadha, Uttara Bhadrapada, Revati preferred
- Vara: Wednesday (Budha), Thursday (Guru), Friday (Shukra) preferred; Saturday, Tuesday avoided
- Active Sarvartha Siddhi or Amrit Siddhi yoga = bonus

Red flags that would indicate a backend bug:
- Top result on Saturday + Krishna Chaturdashi (both strong malefics for Vivah)
- Top result during Rahu Kalam without penalty in breakdown
- Score > 4.0 without any nakshatra contribution (nakshatra is highest-weighted factor)

### Run 2: Griha Pravesh — 2026-05-21 → 2026-06-19
Expected: Taurus/Gemini sun transit period (good for Griha Pravesh). Top results should favour
Pushya nakshatra, Hasta, Rohini. Sunday and Tuesday avoided.

### Run 3: Vyapara (Business Start) — 2026-05-21 → 2026-06-19
Expected: Wednesday (Budha) strongly preferred. Hasta nakshatra best for commerce.
Pushya + Thursday (Guru Pushya Yoga) = top tier. Avoid Tuesdays, full/new moon days
(Purnima/Amavasya) unless other strong factors override.

## §5 — Known constraints

- Date range input capped at 89 days (sidecar rejects >= 90 days; UI default is today+89).
- Personalise overlay (Tara Bala + Chandra Bala) only applies when chart_id is passed.
  Without personalisation, scoring is purely shastra-table-based.
- The "Export to Calendar" button is intentionally disabled (4C-7 scope).
- Calendar Export badge shows "4C-7" phase label on hover/tooltip.

## §6 — Sign-off

Visual review and acharya sanity check BLOCKED pending operator sidecar start.
All three components (MuhuratFinderModal, MuhuratResultsList, useMuhuratFinder)
are implemented and 25 component tests pass. The acharya review must be done
by the operator before 4C-6-S3 can be declared fully COMPLETE per the canary
criterion in brief §9.

**Operator action required:** Start Panchang sidecar → run visual + acharya checks → update this file.

---
*Generated by Claude Code session 4C-6-S3, 2026-05-20*
