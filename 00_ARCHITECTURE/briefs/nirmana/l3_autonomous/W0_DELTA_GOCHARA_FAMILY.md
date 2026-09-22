---
artifact: KALA_W0_DELTA_GOCHARA_FAMILY
version: "1.0"
status: CURRENT
date: 2026-09-22
addressed_to: the Gochara-family brief session
effect: delta to your existing prompt; supersedes anything in it that conflicts; base branch is main
---

# W0 delta — Gochara family

Your prompt was written before the W0 tier beneath the L3 Strategy had been read. Several things
your brief would otherwise assert were **already established, held, or accepted** at W0. Base
branch: **`main`** — it carries the accepted W2 first-frontier source by content (`47131772b`),
including the family's foundation tier. Do not switch branches.

## Read now (asset-relevant sections only)

- `briefs/nirmana/MADHAV_DATA_PLANE_L3_CURRENT_STATE_AND_DISPOSITION_v1_0.md` §4.1 (rows
  `ka_gochara`, `ka_gochara_v3_century_materialize`, `ka_gochara_resonance`, `ka_vedha_gochara`),
  §4.2, §6.3
- `briefs/nirmana/MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md` — census rows #4, #5,
  #6, #20; "Shared-owner fences" items 1–3; "Protected-retired exclusion"
- `briefs/nirmana/MADHAV_DATA_PLANE_L3_W0_FOUNDATION_SAFETY_v1_0.md` §3, §8
- `briefs/nirmana/MADHAV_DATA_PLANE_L3_W2_FIRST_FRONTIER_SOURCE_v1_0.md`
- `l3_autonomous/KALA_ASSET_BRIEF_INSTANTIATION_GUIDE_v1_0.md`

## What W0 already established — inherit, do not re-derive

1. **The table-identity dispute is settled by the physical census.** Register census #4:
   `ka_gochara` → `kala_gochara_windows_v2` (generation 2) + `kala_gochara_v2_build_state`.
   Census #6: the century materialiser → `_v2` *staging* (generation 3) + `kala_gochara_windows`
   *protected production* (generation 3) + shared build state. T5 "Tension 1" is answered here;
   cite these rows rather than re-arguing which instrument is authoritative.
2. **The registry `target_table` mismatch was known and HELD** — CURRENT_STATE §4.1:133 *"after
   resonance; seed target mismatch held."* Your brief cites the hold and states its release
   condition; it does not report the mismatch as a discovery.
3. **Shared-owner fences 1–3 are binding** (register, with evidence): gen2 and century share `_v2`
   — any DELETE/UPSERT must include chart, event class and generation (`ka_gochara.py:59,141-156`;
   century `:503-524`); sweep v1 and century v3 coexist in `kala_gochara_windows` —
   generation-blind mutation forbidden (migrations `542:153-163`, `566`); build state is shared
   on `(chart_id, event_class, generation)` (`541:69-101`). Migration **566** is the origin of the
   century BUILD-PROTECTED guard — that guard is working; it is not yours to weaken.
4. **Declared Kota/Tithi → century edges are not proven consumption** — CURRENT_STATE §4.1
   *"not Kota/Tithi in current source"*; Strategy §6.3 *"Kota/Tithi/Sudarshana→v3 is a proposed
   use relationship."* If v0.3 assumes those integrations exist, it must re-label them proposed.
5. **Sangam does not read materialized `ka_gochara`** — it invokes the on-demand Gochara
   *service* (§4.1, §6.3). So `_v2` generation 2.0's actual consumers must be named explicitly;
   the registry edge materialized-Gochara→Sangam is undemonstrated.
6. **Vedha is read by century v3 and — undeclared — by Sangam** (§4.1 "close hidden edge").
   That closure is an interface obligation your brief names, even though Sangam owns the fix.
7. **W2 first-frontier source is ACCEPTED** for resonance, Vedha, Moorti, Kota, Tithi and
   Sudarshana, including "27-event-class Gochara completeness" (`47131772b`, on `main`). Your
   foundation tier starts from accepted source, not from zero.

## What is genuinely new since W0 — carry forward

- **A live Clear route deletes the protected v1 snapshot** (38,287 rows) — `build_protected_assets`
  is empty for every chart, the route loads the registry with no `is_active` filter, and a
  non-admin chart owner can reach it. The W0 records do not mention this path. The Phase 0/1
  session is closing it; your brief **depends** on that closure and says so.
- A restore drill run as `data_plane_builder` cannot read its own recovery source
  (`kala_gochara_windows_archive_20260805`, no SELECT).
- The Clear route's comment cites a migration-540 guard that migration 588 dropped.

## What changes in your brief

Cite the hold (2); adopt census #4/#6 as the identity answer (1); re-label Kota/Tithi integration
as proposed (4); name `_v2` gen-2.0's real consumers (5); carry the Sangam–Vedha closure as an
interface obligation (6); start the foundation tier from `47131772b` (7); declare the B1 dependency
(new). v0.3's amendments survive where they do not conflict with the above.
