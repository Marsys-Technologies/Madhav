---
artifact: TRACK3_README
type: SOURCE-DRAFT INDEX (Track-3 authoring, absorbed into D-2 Lane V-1)
version: 1.0
status: DRAFT — authored by D-2 Lane V-1 implementer, 2026-07-16
---

# Track-3 — Vidhi floors + primitives (absorbed authoring)

Track-3 was chartered to author the acharya-floor content and primitive catalog ahead of
D-2, but was **never launched** (verified at D-2 open — this directory did not exist, no
drafted floors/primitives existed anywhere in the repo). Per BRIEF_D2.md's fallback rule,
D-2 Lane V-1 absorbs this authoring from scratch, into the `vidhi_primitives` /
`vidhi_intent_floors` / `vidhi_floor_items` registry (migration 440) as the system of
record, with this directory holding the human-readable source drafts the registry mirrors.

**Files in this directory:**

- `PRIMITIVES_v1_0.md` — the 37-primitive catalog (design §3 targets "~30"; expanded by 7
  to guarantee full §B0.4 mandatory-surface coverage). Mirrors
  `platform/src/lib/vidhi/registry_data.ts` (`VIDHI_PRIMITIVES`) and
  `platform/python-sidecar/pipeline/orchestrator/writers/bg_vidhi_primitives.py`.
- `FLOORS_v1_0.md` — the 8 intent-class floors (acharya floor + machine band each), incl.
  `floor(wealth_deepdive)` matching DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §3's worked example
  verbatim. Mirrors `registry_data.ts` (`VIDHI_INTENT_FLOORS`) and `bg_vidhi_floors.py`.
- `CR27_MAPPING_v1_0.md` — the CR-27 improvisation-corpus → floor-item prevention map
  (DONE-CHECK item: "the CR-27 corpus is mapped to floor items").

**DONE-CHECK (BRIEF_D2.md §F1 Lane V-1):**
- [x] Every intent class has a floor — 8/8 (`wealth_deepdive`, `career_deepdive`,
  `health_deepdive`, `marriage_deepdive`, `structure_read`, `panoramic_breadth`,
  `retrieval_only`, `general_synthesis`). Asserted by `floor_coverage.test.ts`.
- [x] Every primitive names its live tool + known_gap (or `null` if none) — 37/37.
  Asserted by `registry_completeness.test.ts`, cross-checked against the live-tool
  catalog and the OPEN/LOGGED CR allowlist (`cr_status.ts`).
- [x] The CR-27 corpus is mapped to floor items — see `CR27_MAPPING_v1_0.md`; all four
  Class-9 instances + the CR-36 buried-evidence specimen are each prevented by at least
  one floor item. Asserted by `floor_coverage.test.ts`.

**Known open item for the Binder/verifier:** `platform/src/lib/vidhi/cr_status.ts` documents
a conflict between BRIEF_D2.md §B0.1 (which lists CR-55 as CLOSED) and
POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md v1.5 §G's own CR-55 row (still reading
"OPEN — ELEVATED" as of this lane's read). This lane follows the brief's explicit
instruction and does not cite CR-55 anywhere. Flagged, not silently resolved.

**Also flagged:** `BIND_D-2.md` — the Binder's own bind record this brief's §B (BIND-AT-OPEN
slots, incl. §B.6 migration number allocation) requires — **does not exist in this repo** at
the time this lane was implemented, and the working branch was not `wave/D-2/V-1` as the
task description asserted (see the implementer's session close notes / final report). This
lane proceeded using BRIEF_D2.md's own §B0 PRE-BOUND content as the best-available source of
truth, self-allocated migrations 440-441 (both within the 440-444 block named by the task),
and explicitly flags this gap for the verifier — a real Binder pass should confirm or correct
every choice this README and its sibling files record.
