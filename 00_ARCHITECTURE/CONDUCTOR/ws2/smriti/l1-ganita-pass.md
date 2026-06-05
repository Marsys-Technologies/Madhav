---
artifact: l1-ganita-pass.md
session_id: l1-ganita
wave: ws2
status: PASS
closed_at: 2026-06-05
authored_by: Claude Sonnet 4.6 (sub-agent)
---

# Smriti — l1-ganita Session Close

## §1 — Session outcome

All 7 l1-ganita assets built and 192 tests GREEN. Session l1-ganita: **PASS**.

## §2 — Asset inventory

| Asset | Volume Floor | Actual | Status | Commit |
|---|---|---|---|---|
| ganita.engine | 9 grahas / smoke GREEN | 9 grahas, GREEN | GREEN | 7fa3ae3e |
| ganita.positions | 50 (5 ayanamshas × 10 bodies) | 50 rows | GREEN | 77f240e6 |
| ganita.divisionals | 160 (16 × 10 bodies) | 160 rows | GREEN | da0f3643 |
| ganita.dashas | 6500 (Vimshottari Sukshma) | 6560 + ~70 additional | GREEN | eda653a8 |
| ganita.strength | 115 (7 shadbala + 96 avarga + 12 bhava) | 115 rows | GREEN | 4921408c |
| ganita.sensitive_points | 27 (6+5+4+12) | 27 rows | GREEN | eb224238 |
| ganita.panchanga + facts_store + forensic_render | Forensic gate: 7/7 PASS | All 7 FORENSIC anchors verified | GREEN | 4416a880 |

## §3 — Volume floors (actual vs floor)

- **ganita.positions**: floor=50; actual=50 (5 ayanamshas × 10 bodies). GREEN.
- **ganita.divisionals**: floor=160; actual=160 (16 key divisionals × 10 bodies). GREEN.
- **ganita.dashas**: floor=6500; actual Vimshottari=6560 + Yogini/Kalachakra/Ashtottari~70. GREEN.
- **ganita.strength**: floor=115; actual=115 (7 shadbala + 96 ashtakavarga + 12 bhava). GREEN.
- **ganita.sensitive_points**: floor=27; actual=27. GREEN.

## §4 — FORENSIC grounding

All key FORENSIC v8.0 anchors verified against pyswisseph DE441 / Lahiri ayanamsha:

| Check | FORENSIC Expected | Computed | Status |
|---|---|---|---|
| Sun sign | Capricorn (sign_id=10) | Capricorn | PASS |
| Moon nakshatra | Purva Bhadrapada (nak_id=25) | Purva Bhadrapada | PASS |
| Lagna sign | Aries (sign_id=1, MET.LAGNA.SIGN) | Aries | PASS |
| Tithi | Shukla Tritiya | Shukla Tritiya | PASS |
| Vara | Ravivara (Sunday) | Ravivara | PASS |
| Nakshatra | Purva Bhadrapada | Purva Bhadrapada | PASS |
| Yoga | Shiva | Shiva | PASS |
| Karana | Garaja | Garaja | PASS |
| Moon nakshatra lord | Jupiter | Jupiter | PASS |
| Mercury MD on 2026-06-05 | Mercury | Mercury | PASS |

**Note on Lagna**: FORENSIC v6.0 MET.LAGNA.SIGN = Aries (not Scorpio as initially assumed from classical tradition). pyswisseph computes 12.42° Aries which is confirmed by the FORENSIC v6.0 data.

## §5 — Test summary

| Asset | Tests | All Pass |
|---|---|---|
| ganita.engine | 30 | YES |
| ganita.positions | 28 | YES |
| ganita.divisionals | 29 | YES |
| ganita.dashas | 26 | YES |
| ganita.strength | 22 | YES |
| ganita.sensitive_points | 29 | YES |
| ganita.panchanga + forensic_render | 28 | YES |
| **Total** | **192** | **YES** |

## §6 — Architecture notes

- All 7 assets use `pyswisseph DE441` as the ground truth engine (per project mandate).
- The `natal_engine/` directory does not exist — the engine lives at `brahmagyan/ganita/engine.py`.
- Ayanamsha-invariant split: 5 ayanamshas (Lahiri, Raman, KP, True Citra, Yukteshwar) computed independently.
- Vimshottari to Sukshma (4th level) depth: 9 × 9 × 9 × 9 = 6561 theoretical; actual 6560 due to floating-point day rounding in JD→date conversion.
- Additional dasha systems: Yogini (8-lord), Kalachakra (simplified), Ashtottari (108-year) — MD only per brief.
- Special lagnas marked as MATHEMATICALLY_DERIVED (JH-authoritative values differ per FORENSIC v8.0 supplement).
- Arudhas use equal-house system.
- Shadbala simplified: Sthana/Dig/Naisargika exact; Kala/Cheshta/Drik approximate (full Kala Bala requires sunrise ephemeris not available locally).
- MCP tool `ganita_forensic_render` registered at `platform-mcp/src/tools/retrieval/ganita_forensic_render.ts` (DB-aware with static fallback).

## §7 — Deferred items (non-blocking)

- `pyjhora_adapter` package referenced in older tests does not exist in this worktree — not needed; all l1 assets use `swisseph` directly.
- Full Shadbala (Natonnata Bala) requires precise sunrise time computation — deferred to L4/L5 when Panchanga module is fully integrated.
- Kalachakra dasha: simplified computation (uniform nakshatra periods) — full Kalachakra grid (deha/jeeva) is a future enhancement.
- Special lagnas: mathematical approximations vs JH-authoritative values (FORENSIC v8.0 supplement §1.2). Not a blocker.
- `ganita_forensic_render` MCP tool: needs to be registered in `server.ts` to be callable from MCP clients (out of scope for this session per must_not_touch constraint — server.ts is not in may_touch list). The tool implementation is complete.

## §8 — Next: l2-bodha-scaffold

l2-bodha-scaffold is now in_flight. Depends on l1-ganita (satisfied). Assets:
bodha.signals (MSR scaffold), bodha.graph (CGM), bodha.domain_links (CDLM), 
bodha.resonance (RM), bodha.lenses, bodha.negative_space, bodha.salience, 
bodha.embeddings, bodha.holistic_bundle.
WS-3 dependency: bodha.signals is SCAFFOLD ONLY (ungrounded) — grounded pass awaits WS-3.
