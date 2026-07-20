---
artifact: BIND_PG-1
type: BINDER (opens PG-1 under BRIEF_PG-1.md §B)
version: 1.0
status: OPEN
authored_by: Claude Code (Sonnet 5), conductor session, 2026-07-19
governs: CLAUDECODE_BRIEF_PARIPRASHNA_GROUNDING_AUDIT_v1_0.md (BRIEF_PG-1 v2.0)
---

# BIND_PG-1 — Wave Open

## B-1 — Base pin
`origin/main` @ `8f3ace3756c219a65fe8d3baee96606092a38913`. Working tree at open carries
uncommitted changes from concurrent D-4a/D-3 closeout work (native's own session) — PG-1 does not
touch those paths (§F2 must_not_touch) and does not stage/commit them. `pg1/wave` branch cut from
this HEAD.

**CORRECTION (recorded post-SPAWN, integration step):** local `main` had already diverged from
`origin/main` by commit `9c358819` ("docs(retrieval): strategy+plan+consult v1 set..."), an
already-committed-but-unpushed commit from a concurrent session that itself touches `CLAUDE.md`
(§F2 must_not_touch) — `pg1/wave` was cut from local `main` HEAD, which includes this commit, not
from `origin/main` directly. This is NOT a PG-1 scope violation (PG-1 authored none of that
commit's content) but it means a naive `git diff origin/main...HEAD` scope-warden check would
falsely attribute `9c358819`'s `CLAUDE.md` touch to PG-1. Corrected: scope-warden and gate G.9 are
scoped to PG-1's own commit range (`9c358819..HEAD`, i.e. from PG-1's first commit `e58e19ce`'s
parent forward). Verified clean: `git diff --stat 9c358819...HEAD` touches 31 files, all under
`00_ARCHITECTURE/pg1_audit/**` or the wave's own brief file, zero forbidden paths.

## B-2 — Concurrency status
`CLAUDECODE_BRIEF.md:current_wave = D-4a` (INCOMING). A `BIND_D-4A.md` exists (status: OPEN) and a
`wave/D-4a/A-0` branch exists — D-4a is mid-flight (a concurrent native/Claude-Code session per the
recent-context log: "Resume D-4a Lane A-0"). Per §0.3: **PG-1 does not halt** — read-only posture is
safe. Coexistence recorded; PG-1 does not advance `current_wave` and does not touch
`CLAUDECODE_BRIEF.md`.

## B-3 — Live capability count
**Bearer-face probe FAILED** (`POST /mcp` with `Authorization: Bearer $MARSYS_MCP_KEY` sourced from
`scripts/setup_mcp_env.sh` → `401 {"error":"Unauthorized","message":"Invalid or missing Bearer API
key"}`). The `marsys-jis-direct` (`?api_key=`) seat IS live and answering (confirmed via
`list_my_charts`), satisfying protocol §8.1's "either face is the deployed connector" ruling — B-3's
denominator is derived from that seat's registered tool surface instead. **The Bearer-key failure
itself is recorded as a candidate finding for Lane R-2/O-1** (stale/rotated prod key, or an auth
regression — cannot tell without further investigation; `unverifiable` root cause, `confirmed`
symptom). Recorded per PC-1.

Declared tool surface derived from the connected `marsys-jis-direct` session: ~200 flattened MCP
tool bindings observed in this session's tool listing (`mcp__marsys-jis-direct__*` prefix). Lane R-1
re-derives the exact live count mechanically (never hand-counted, per its lane charge) and reconciles
against `CAPABILITY_MANIFEST.json` (`entry_count: 113`, `entries: 113` — i.e. manifest is internally
consistent at 113, but likely undercounts the served surface, which appears larger). **This
discrepancy (113 manifest vs ~200 observed live) is itself R-1's first assumption check.**

## B-4 — DB access confirmation
**CONFIRMED.** `mcp__postgres__query` (read-only) answers live against the production Cloud SQL
instance. Lanes D-1/D-2/D-3/S-1/Q-1 proceed with DB access; no PARK required.

## B-5 — Canonical chart build state
Chart `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek) is present and queryable. **Row counts
diverge materially from `L1_GANITA_CLOSURE_v1_0.md`'s canonical figures** (probed live, this session):

| Table | L1_GANITA_CLOSURE canonical | Live count (this probe) | Delta |
|---|---|---|---|
| `chart_facts` | 27,554 | **138,519** | +402.7% |
| `chart_dashas` | 536,471 | 484,387 | −9.7% |
| `chart_divisionals` | 21,635 | 22,092 | +2.1% |

None of these are within the §8.7 ±1% health-check tolerance. `chart_facts` in particular is
5× the closure figure — this is either (a) a legitimate post-closure enrichment (D-1.5b "full
L1→L5" wave, or Doctrine-Waves L1 structural-enrichment briefs seen in the repo, landing new fact
rows since L1_GANITA_CLOSURE was sealed) or (b) a duplication/idempotency defect. **PG-1 does not
diagnose this** (read-only, §F2) — it is recorded here as a BIND-time observation and handed to
Lane R-2/D-1 as a named investigation target (assumption-check candidate, not in the A1–A32 list —
recorded as a new defect candidate for Z-1's F- sequence). `build_id` not separately probed (no
direct `chart_header`-returning tool call made at BIND time to avoid scope creep beyond the §B
slot's literal ask); R-2 pulls it as part of its full-surface sweep.

## B-6 — Architecture doc fingerprint
`PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` (v0.5) sha256:
`cf347c85cf13c88a6db6467fe2d11c38fde36a8047e7834541a6e7221cddc284`

Z-1's corrections (→ v0.6) apply against this exact fingerprint. Full doc read: 3,216 lines / 2
pages (§0–§7 in first page; §8 onward pending per-lane consumption).

---

**Binder ruling: brief is BOUND.** No BIND-AT-OPEN slot forces a PARK. Lanes spawn.
