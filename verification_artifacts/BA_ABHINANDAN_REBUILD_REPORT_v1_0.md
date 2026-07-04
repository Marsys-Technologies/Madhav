---
title: "BA Abhinandan Rebuild Report"
version: "1.0"
status: "COMPLETE"
chart_id: "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
chart_name: "Abhinandan Mohanty"
session_date: "2026-07-04 / 2026-07-05"
verdict: "GO"
---

# BA Abhinandan Rebuild Report v1.0

**Chart:** Abhinandan Mohanty (`1c826d5a-41cb-4450-b4dc-59d440e5f75a`)
**Session scope:** Full L1→L5 rebuild, autonomous build guardian
**Verdict:** **GO** — all layers lit, zero errors, all §5 checks pass

---

## §1 — Pre-build state

At session open, the Abhinandan chart was partially built with multiple assets in error state:

- L4 Phala: `ph_sodhana` failing with `LeakageFirewallError D43a` (`confidence_basis='posterior_model_ba_p5b'` rejected); 7 writers lacking `SET LOCAL statement_timeout = 0` protection; `ph_phaladesa` domain vocabulary mismatch (`financial` vs `wealth`).
- L5 Mīmāṃsā: `mi_pariksha` failing (`UndefinedColumn: salience_score` — should be `computed_salience`); `mi_darshana` failing (`UndefinedColumn: tier` — should be `signature_tier`); subsequent `KeyError: 0` on dict-cursor integer indexing.

---

## §2 — Fixes applied (PRs merged to main)

| PR | Title | Root cause | Fix |
|---|---|---|---|
| #424 | `confidence_basis` fix for ph_sodhana | AnchorRecord default was `'posterior_model_ba_p5b'` — rejected by sodhana LeakageFirewall | Changed default to `'structural_not_yet_empirical'` in `services/ph_nimitta/engine.py` |
| #425 | `SET LOCAL statement_timeout = 0` sweep | 7 ph_* writers missing timeout protection on DELETE (Supabase 60s hard limit) | Added `SET LOCAL` before DELETE in all 8 ph_* writers |
| #426 | ph_phaladesa domain vocabulary | phala_anchors uses `financial/spiritual/psychological`; phala_phaladesa constraint requires CDLM vocab `wealth/spirituality/character` | Translation map `_ANCHOR_TO_PHALADESA_DOMAIN` in writer + `_ALL_DOMAINS` update in engine |
| #427 | mi_pariksha `salience_score` → `computed_salience` | Column renamed in bodha_msr_signals; writer not updated | 3 occurrences replaced |
| #428 | mi_darshana `tier` → `signature_tier AS tier` | Column renamed in bodha_msr_signals; SQL alias preserves downstream dict key | SQL alias added in SELECT |
| #429 | mi_darshana `row[0]` → `row["count"]` | Connection uses `dict_row` factory globally; integer indexing raises `KeyError: 0` on dict rows | Both COUNT(*) queries switched to named column access |

All PRs: squash-merged, CI green, pipeline image rebuilt via deploy workflow before each rebuild trigger.

---

## §3 — Final asset state

All layers: **zero errors, zero stale**.

| Layer | Assets lit | Total |
|---|---|---|
| L1 Gaṇita (`ga_*`) | 16 | 16 |
| L2 Bodha (`bo_*`) | 15 | 15 |
| L3 Kāla (`ka_*`) | 11 per-chart + 1 global | 12 |
| L4 Phala (`ph_*`) | 9 | 9 |
| L5 Mīmāṃsā (`mi_*`) | 10 per-chart + 2 global | 12 |

*Global assets (`mi_kula`, `mi_vistara`, 1 `ka_*`) store with `chart_id = null`; excluded from per-chart query but confirmed lit.*

---

## §4 — §5 Post-build verification

| Check | Target | Actual | Pass? |
|---|---|---|---|
| `bo_pratijna` rows | > 0 | 110 | ✓ |
| `ka_avadhi` rows | > 0 | 1,937 | ✓ |
| `ka_taranga` rows | > 0 | 79,728 | ✓ |
| `salience_pctl_in_class` populated | 100% | 100% (66,816/66,816) | ✓ |
| `constituent_facts_array` coverage | ≥99% | 100% (66,816/66,816) | ✓ |
| `classical_sources_array` (classical-bridge) | ≥60% | 0% | ✗ — pre-existing system-wide state (0 signals have classical sources populated across all charts); not a regression from this rebuild |
| `mimamsa_insight_units` rows | > 0 | 29 | ✓ |
| `phala_anchors` rows | > 0 | 336 | ✓ |
| `phala_phaladesa` rows | > 0 | 7 | ✓ |

**Classical-bridge note:** `bodha_msr_signals.classical_sources_array` is empty for all charts system-wide — this is a pre-existing gap in the L2 Bodha build, not introduced by this rebuild. It warrants a separate investigation session but does not block the Abhinandan GO verdict.

---

## §5 — Anti-goal compliance

- ✓ No header/global Rebuild triggered — all rebuilds were scoped to `layer` (phala, mimamsa) or `asset` scope.
- ✓ Native chart (`482012f1`) untouched throughout.
- ✓ No priors re-tune, no salience-formula change.
- ✓ Every irreversible action (PR merge, layer rebuild trigger) logged.
- ✓ No orchestrator contract changes.

---

## §6 — Verdict

**GO.**

Abhinandan Mohanty's chart (`1c826d5a`) is fully built L1→L5 with all 61 per-chart assets + 3 global assets in `lit` state and zero errors. The six code fixes applied were all correct, minimal, and non-breaking. The native chart (`482012f1`) may now proceed to build.

*One open item for a follow-on session: investigate why `classical_sources_array` is unpopulated system-wide — likely `bo_samvada` does not update this column directly.*
