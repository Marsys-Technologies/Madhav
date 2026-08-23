---
lane: F-48 — POINTER STUB (full spec lives in F-47/SPEC.md)
stream: S3_SATYA (spec + build)
stage: S — SPEC
author: SATYA-LEAD (sonnet)
status: DRAFT — awaiting VERIFIER review
fork_status: RESOLVED by conductor, applying PRATINIDHI's standing precedent SP-1 directly
  (NOT PAR-R-8 — see F-47/SPEC.md's frontmatter note for the citation correction) — Option B
  (disclosure) is the shipped fix, Option A (real ephemeris) is out of scope for this campaign.
  Not an open fork.
---

# SPEC — F-48 (see combined spec: `00_ARCHITECTURE/briefs/parisesa/lanes/F-47/SPEC.md`)

F-48 ("`transit_quality` has no real transit computation behind it — a lunar-phase + weekday
approximation, a §N.8 earned-signal violation") is specced together with F-47 ("50% of the
composite muhurta score is action_type-blind") in one document, because both findings' entire
mechanism is the same function, `_transit_quality_for_window`
(`platform/python-sidecar/brahmagyan/phala/muhurta.py:420`) — see F-47/SPEC.md §0 for why.

**Do not spec or build F-48 separately.** The full contract — root-cause statement, files to
change, exit tests, sibling-site coverage, recurrence guard, dependencies/rollback, and the D-2
coverage table for both findings' sub-claims — is in `F-47/SPEC.md`. This stub exists only so
`F-48`'s lane directory has its own `SPEC.md` per the board's per-lane file convention.

**Fork resolution, for anyone reading this file in isolation:** F-48's diagnosis flagged a fork
between (A) building real Swiss-Ephemeris-backed transit computation and (B) disclosing the
existing lunar-phase approximation honestly instead of presenting it as genuine transit strength.
The conductor resolved this **before Stage S closed**, applying PRATINIDHI's standing precedent
SP-1 ("choose the option that discloses more") directly — the same precedent used for F-31, not a
fresh ruling and not PAR-R-8 (an unrelated ruling on F-135; see F-47/SPEC.md's frontmatter for the
citation correction): **Option B ships.** Option A is confirmed
out of scope for this campaign (no ephemeris integration exists anywhere in the sidecar) and is
flagged in F-47/SPEC.md §7 as a candidate for a future, separately-scoped finding. See
`F-47/SPEC.md §3` for the full resolution note and `§2b`/`§2c` for what Option B actually changes.
