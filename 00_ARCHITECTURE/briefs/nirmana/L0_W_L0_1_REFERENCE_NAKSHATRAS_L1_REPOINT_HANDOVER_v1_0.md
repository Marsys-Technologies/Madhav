---
artifact: L0_W_L0_1_REFERENCE_NAKSHATRAS_L1_REPOINT_HANDOVER
version: 1.0
status: CURRENT
packet: W-L0-1 item 4 (block handover)
from: L0 execution session (worktree /Users/Dev/madhav-l3/l0-exec, branch l0/nirmana-elevation-20260921)
to: L1 execution session + consolidation session (madhav-65)
date: 2026-09-25
---

# Handover — reference_nakshatras retirement is gated on an L1 repoint

`reference_nakshatras` (legacy, plural) is the only retirement in the L0 plan and is
retired for **superseded authority** — the canonical table is `reference_nakshatra`
(singular, 28 rows). The drop cannot proceed until L1 code stops reading the legacy
table. L1 has not opened (native ruling: L1 begins only when L0 is wrapped), so this
is a handover, not an execution request to the L0 stream.

## Measured state (live, 2026-09-25)

- `reference_nakshatras`: present, **27 rows**.
- `reference_nakshatra`: present, **28 rows** (28th nakshatra coverage supersedes).
- Lord agreement: **27/27** rows agree on nakshatra lord between the two tables
  (verified during the W-L0-1 session). The legacy table carries no information the
  canonical table lacks for its 27 rows; the canonical adds the missing 28th.

## Live L1 readers that must be repointed (file:line)

1. `platform/python-sidecar/brahmagyan/ganita/ga_dashas_writer.py:139` and `:3142`
2. `platform/python-sidecar/brahmagyan/ganita/ga_sensitive_writer.py:114`, `:3047`,
   `:3151`, `:3154`
3. `platform/python-sidecar/brahmagyan/ganita/_vimshottari_independent_verifier.py:560`

Also named (non-reader references to update when the drop lands):

- `platform/scripts/census/data-plane-ownership-preflight.ts:46` (census preflight
  names the legacy table)
- a check inside `vimarsaka_beta.py` references the legacy table

## Sequence (owners noted)

1. **L1 session:** repoint the three readers (and the two non-reader references) to
   `reference_nakshatra`; run the ganita/vimshottari verification suites.
2. **Consolidation session (madhav-65):** after the repoint is live AND the
   `_migrations_applied` ledger for 1080–1095 is reconciled, author and apply the
   drop migration. Number it by scanning every origin/* head across BOTH
   `platform/migrations/` and `platform/supabase/migrations/` (head was 1091 on
   2026-09-25); never edit an applied migration.
3. **Detector that closes the item:** `to_regclass('reference_nakshatras') IS NULL`.

## Standing guard already in place (L0 side)

`scripts/__tests__/l0_registry_parity.test.ts` asserts no bg_* seed row names the
legacy table — green today (12/12). Do not weaken this or any gate to force the
drop early; the gate refusing is the gate working.
