---
artifact: WP7_PACKET_V1
packet_id: V-1
version: "1.0"
status: DESIGN_ONLY_NOT_IMPLEMENTED
date: 2026-09-23
owner: "Owner of services/ka_sangam (registry edge + writer)"
executes: GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §6.2 V-1, §6.3 (ka_sangam.depends_on row), finding F-17
authority_note: "Owed to its owner. Anchors read at this checkout: pipeline/orchestrator/writers/ka_sangam.py:1057-1065 (the kala_vedha_gochara read); services/ka_sangam/engine.py:464 (service call), :1363/:1383 (long-horizon bypass)."
---

# V-1 — Saṅgam: declare the Vedha edge, re-type the gochara edge

## The one-paragraph requirement

Saṅgam reads `kala_vedha_gochara` today with **no declared dependency**: the C11 vedha
fetch at `pipeline/orchestrator/writers/ka_sangam.py:1057-1065` runs
`SELECT graha, window_start, window_end FROM kala_vedha_gochara WHERE chart_id = %s AND
ayanamsha_id = 'lahiri_chitrapaksha' AND vedha_kind = 'house_vedha'` against a table
written by `ka_vedha_gochara` — F-17's hidden edge, so a Vedha rebuild ordering change
could serve Saṅgam windows qualified against stale vedha rows and nothing in the
registry would flag it. Declare it, in Saṅgam's own migration (registry changes go by
migration, N-9): add `ka_vedha_gochara` to `ka_sangam.depends_on` with edge role
`counterevidence` — vedha is the necessary-side veto factor (`_c11_vedha_factor`),
which is exactly the counterevidence relation, not a plain input — and **re-type the
existing `ka_gochara` edge as `service`**, because after S-1/S-2 what Saṅgam consumes
from the Gochara stream is the live `GocharaTransitService` computation interface
(`engine.py:464` today; `find_episodes` + the S-2 directed contact events after
adoption) rather than any table `ka_gochara` materializes — the dependency is on the
service's output contract, and the registry should say so. No code change follows from
either declaration beyond ordering semantics the orchestrator already honors; the
undeclared read itself is the defect being closed.

## Acceptance

Registry diff shows both edges; a registry linter (or a `depends_on` closure walk over
the C11 read) finds no undeclared table read in `ka_sangam.py`.

## What this packet does NOT do

- It does not change the C11 query, the vedha factor algebra, or M-8's
  exceptions/vipareeta implementation (WP9's scope, once ruled).
- It does not touch `engine.py:1363/:1383` (the long-horizon bypass retires via S-1's
  adoption, Saṅgam's owner's choice with T-1-style evidence).
- It does not declare the edge for Kṣetra — that is K-1.
