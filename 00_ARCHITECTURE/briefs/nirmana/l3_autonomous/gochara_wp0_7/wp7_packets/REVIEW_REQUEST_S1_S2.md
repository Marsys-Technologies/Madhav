# REVIEW REQUEST — WP7 Packets S-1 / S-2

**Packet:** `PACKET_S1_S2_gochara_transit_service.md`
**Branch:** `l3/gochara-autonomous-wp0-7`
**Owner file:** `platform/python-sidecar/services/ka_gochara/service.py`

## What changed (one file + one test file)

### S-1 — `find_episodes` lands; `find_aspects` untouched

- **`find_aspects` signature/return shape byte-identical** (service.py:63 area; verified
  by `TestEcosystemContract::test_find_aspects_signature_is_the_legacy_shape` and by
  `inspect.signature` at import). The four duck-typed call sites
  (kala_trigger/trigger.py:96,150,199; ka_sangam/engine.py:464;
  scripts/kala_admission/currents.py:59) were not edited.
- New method **`find_episodes(conn, chart_id, targets, horizon, *, bodies, relations, moon)`**
  returning `EpisodeBatch{episodes, coverage}` with the packet §2 shapes
  (`GocharaEpisode`, `EpisodeCoverage`, `TargetRef`, `Horizon` dataclasses).
  - **DB handle is per-call**: the service is otherwise DB-free (constructor takes
    `swe` + new optional `ephe_path` kwarg — additive, duck-type safe). The packet's
    protocol block has no `conn`; flag below.
  - Served from `kala_gochara_contacts` at the **authoritative generation**
    (`kala_gochara_authority`); absent authority row ⇒ `unpublished`: empty episodes +
    full coverage object with honest `unsearched_reason` (N-10, same seam as P-1/P-4).
    Never re-scans the ephemeris for ledger-served relations.
  - Empty interval ⇒ empty `episodes` **with** a synthesized coverage object stating
    what was searched (F06 — never a bare `[]`).
  - Coverage rows are read from `kala_gochara_coverage` and mapped verbatim
    (requested/completed horizon, relations, target counts, unavailable_inputs,
    unsearched_reason).
- **Moon on-demand** (`moon=True`): live solve through `gochara_kernel`
  (`knots.sample_knots` → `arcs.build_arc_index` → `episodes.solve_episodes` /
  `solve_boundary_episodes`) at the WP1 §7 Moon orb rows. Returned episodes carry
  `contact_id=None`, `claim_grain='on_demand_live'`, and a `moon_on_demand` coverage
  partition whose requested == completed == requested interval. Zero-answer searches
  still write the partition (L3-Q08 honesty).

### S-2 — `find_directed_contact_events(conn, chart_id, targets, horizon, *, bodies, direction='to_target')`

- Consumes `find_episodes(relations=['drishti_contact'])`, groups episodes of one
  target with overlapping `[t_in, t_out]` into one event: `planets` = sorted LIST of
  concurrent casters, `aspects` = per-graha `{planet, aspect_deg, strength}`.
- **N-14 enforced on serving**: `drishti_contact` rows with body ∈ {Rahu, Ketu}
  (pre-ruling generations) are excluded everywhere and counted into
  `coverage.unavailable_inputs['n14_excluded_drishti_rows']`. The kernel's own
  `SPECIAL_DRISHTI_DEG` already gives nodes empty angle sets (convention.py:53-54).
- Per-graha classical angles come from the persisted rows (kernel solves Mars
  90/180/210, Jupiter 120/180/240, Saturn 60/180/270, others 180 — never the G-7
  symmetric set).
- Nothing-fires ⇒ zero events + coverage only; never a fabricated 0.0 row (F06).

## Packet-vs-codebase notes (flagged)

- **`conn` parameter**: the packet's TS/Python protocol omits a DB handle, but this
  service is DB-free by construction (live-compute engine). `conn` is an explicit
  first parameter rather than constructor state so the duck-typed legacy contract is
  untouched. If the native prefers constructor injection, that's a one-line change.
- **Strength interim**: packet says the field carries the graduated value under the
  declared orb with the ruled interim being the span-aware legacy ±5 d box. The
  dṛṣṭi-koṇa numeric decay is WP8-gated; at `t_exact` separation is 0 by definition,
  so the served interim strength is `1.0` per aspect at the exact root (documented in
  the method docstring). Any finer graduation waits for WP8 — not invented here.
- **Moon target resolution**: live Moon solving needs target longitudes. The WP1 §2.2
  resolution contract (target_ref → longitude) is the caller's job; `TargetRef`
  carries optional `longitude_deg`, and targets without one are counted
  `targets_unresolved` in the `moon_on_demand` coverage — never fabricated.
- **`truncated_at_horizon='both'`**: the kernel keeps the precise `'both'`; the ledger
  CHECK and the packet type allow only `'start'|'end'|NULL` (WP6 maps at persistence).
  Live Moon episodes map `'both'` → `None` on serving; ledger rows are served verbatim.
- **Reverse direction**: `direction='to_target'` only; the reverse relation
  (natal→transit) is not modeled in the kernel's episode vocabulary — flagged, not
  silently produced.
- `GocharaEpisode.target_longitude_deg` is additive over the packet interface
  (Saṅgam's aggregated form requires it; the ledger column exists as reference copy).

## Verification

- New: `tests/l3/gochara/test_s1_find_episodes.py` — **12 tests, all green**
  (unpublished⇒coverage; N-14 exclusion + count; empty-interval coverage; target/
  relation filters reach SQL; moon contact_id=None + partition; moon unresolved
  target; moon zero-answer partition; concurrent-caster aggregation with
  planets=['Jupiter','Saturn'] + angles 120/60; nothing-fires⇒coverage only;
  Rāhu-only⇒no drishti event + N-14 note; find_aspects signature; legacy 1-arg
  construction).
- Full directory: `pytest tests/l3/gochara/` → **239 passed**.
- Ecosystem suites (the call sites, unchanged): `pytest tests/test_kala_trigger.py
  tests/test_ka_sangam_resumption.py tests/l3/test_ka_sangam.py` → **126 passed**;
  `tests/l3/test_ka_gochara.py::test_router_import` fails with ModuleNotFoundError
  **on the clean tree too** (verified via stash) — pre-existing, unrelated.
- S-2's consumer-side changes inside `services/ka_sangam/**` are sibling-owned and
  deliberately not made (packet §3): `_resolve_transit_planet`/`search_long_horizon`
  bypass retirement is the Saṅgam owner's adoption work against this new interface.
