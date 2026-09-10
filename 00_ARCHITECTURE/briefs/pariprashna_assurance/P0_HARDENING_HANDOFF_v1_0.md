---
artifact: Control-plane P0 hardening handoff
version: "1.0"
status: COMPLETE — DEPLOYED — LIVE-PROVEN
as_of: "2026-08-28T19:39:34Z"
merged_source_sha: 9aed4cb73bd6ec81a8cfed31394e82261cf79512
pr: https://github.com/Marsys-Technologies/Madhav/pull/1638
previous_control_py_sha256: c43c5c84722848f2904339047151b6fa95b3dabc7f51fe7e4eaccbd6d9cc67ad
new_control_py_sha256: 83b8b8726b2f778c8a9c85cb1ed34bab7cb38650ede15df8548c06a79b2899e9
live_projection_hash: 24629f71a392f3a4250c5f0ca056892a17db44d52628478fa8d65a580e8c75ab
event_log_hash: 4e6b9b4e656f7a62f43c1cd7cad0a3a3d00a673c95b279f1a1542c1482160881
---

# Control-plane P0 hardening handoff v1.0

Status: **COMPLETE — hardened, merged, deployed to the live service, re-proven.** This
unblocks safe convergence: the six-stream closure ceremonies can now run through this
control plane without the collision class below repeating.

## The defect

The S5 stream ledger (`S5_CONVERGENCE_HANDOFF_v1_0.md` §2) recorded a real incident: two
concurrent sessions authenticated as `lead-s5` both wrote `scenario_executed` events within
a ~10-minute window, colliding on 8 numeric slots (`S5-SC-14` … `S5-SC-21`) under different
slugs. `DUPLICATE_SCENARIO` keyed on the full slug, not the slot, so both writers' events
were accepted — the raw event count landed on exactly 45, satisfying `REGRESSION_INCOMPLETE`
against a fabricated denominator while true joint coverage was 37 distinct slots. No gate
was actually closed on the fabricated count (S5 was still at `charter` stage) — this was
caught and disclosed by the sessions involved, not by the control plane itself. Three root
causes: (a) no single-writer-per-stream lock, (b) dedup keyed on slug not numeric slot,
(c) the charter denominator is a bare integer with no enumeration, so `executed == planned`
degrades to "N rows exist" — a §N.8-class proxy standing in for a claim.

## What was delivered

1. **Numeric-slot dedup.** `scenario_slot()` extracts the canonical `S{N}-SC-{NN}` slot from
   `scenario_id` (anchored at the start of the string; falls back to the raw id for
   non-conforming historical ids). `DUPLICATE_SCENARIO` and the denominator-exceeded check
   now key on the slot, not the full slug.
2. **Single-writer-per-stream lease.** Every `scenario_executed` event now requires a
   `writer_instance_id` and is leased to one writer instance per stream at a time (new
   `stream_scenario_write_leases` table). A second, different, still-fresh instance is
   rejected with `CONCURRENT_WRITER_LEASE_CONFLICT` (recorded via the existing append-only
   `rejected_events` disclosure path); the fact is also durably persisted inside the stored,
   hash-chain-protected payload of the accepted event. A stale lease
   (`SCENARIO_WRITER_LEASE_TTL_SECONDS` = 1800s, chosen to exceed the real incident's ~392s
   writer gap) may be taken over, so a genuinely dead writer never permanently blocks the
   stream. `writer_instance_id` is deliberately excluded from the idempotency fingerprint,
   so a crash-and-restart retry of the same logical write with a new instance id is still
   recognized as the same request.
4. **Projector fix.** `fold()` now reports `scenarios.executed` as the count of *distinct*
   numeric slots, never the raw recorded-event count (which stays visible separately as
   `scenarios.recorded_scenario_events`, for audit). Applied against the live, still-corrupted
   S5 ledger without touching a single event: **S5 now reads `executed: 37`, was `45`.**

**Item 3 (denominator enumeration — freezing an explicit scenario-id list at charter time
instead of a bare `planned_scenarios` integer) is filed as a scoped follow-on, not attempted
here.** It is a larger, separate charter-schema change (touching `work_started`'s payload
contract and every existing stream's already-frozen denominator); (1)+(2) are a complete,
independently valuable fix for the demonstrated collision on their own, per the session's own
scoping instruction not to half-do a larger change.

All changes are additive/strengthening — no existing gate was weakened. A code review
(subagent, adversarial pass) caught a real regression before merge — folding
`writer_instance_id` into the idempotency fingerprint broke retry-after-restart idempotency —
fixed and covered by a new regression test before the PR went to CI.

## Proof

- Failing tests written first (5), confirmed RED against unmodified `control.py`; fix applied;
  126/126 tracker unit tests green (`tests/pariprashna_assurance_tracker/`), including 7 new
  tests covering: required `writer_instance_id`, slot-based duplicate rejection,
  scope-change slot collision, concurrent-writer rejection, idempotent retry across a new
  writer instance, stale-lease takeover, and distinct-slot projection counting under a
  simulated pre-existing corrupted ledger (16 raw events / 8 true slots).
- Protected PR #1638 → all 5 required status checks + the full repo-wide CI suite green →
  merge queue → merged to `main` at `9aed4cb7`.
- Release built from the merged commit and attested (`service.py --attest-release`) against a
  freshly-fetched, config-isolated clone of the canonical origin — `control.py` hash changed
  `c43c5c84…` → `83b8b872…` (this change is authorized/expected; recorded above).
- **Live runtime re-proof, never mutating the DB except through the governed path:** the
  live projection's `verify_replay()` correctly read `ok:false` ("full replay hash mismatch")
  before rebuilding under the new code (the old stored projection no longer matches the new
  `fold()` shape — expected, not a defect) and `ok:true` after — the same one-time rebuild
  `server.py`'s own startup already performs. `service.py --upgrade-p2-release` then
  atomically swapped the launchd service to the new attested release (pre/post snapshot,
  automatic rollback wired) — no rollback was needed. Post-deploy: `/api/service-identity`
  reports `ok:true`, `source_sha` matches the merge commit, `replay_ok:true`; `/api/integrity`
  reports `ok:true` with `event_log_hash` **identical** to before the whole operation
  (`4e6b9b4e…`), proving no event was ever touched. A **fresh scratch copy** of the live DB,
  taken after deploy, independently reconciles to the same hashes. Live `/api/projection` now
  shows `S5.scenarios.executed = 37` (`recorded_scenario_events = 45` preserved for audit).

## State after this session

- Live service: `com.marsys.pariprashna-assurance-control`, PID bound to `127.0.0.1:8787`,
  release `/Users/Dev/.pariprashna-assurance-control-release-9aed4cb73bd6`, source SHA
  `9aed4cb73bd6ec81a8cfed31394e82261cf79512`.
- Previous release (`…-cc6b1a55e85b`, plist backup
  `com.marsys.pariprashna-assurance-control.plist.p2-backup-9aed4cb73bd6`) retained in place
  as the rollback artifact; not deleted.
- S5's ledger itself is untouched (immutable) — its true coverage is still 37 of 45 chartered
  scenarios; the stream remains at `charter` stage. Nothing about this session changes S5's
  substantive completion status; it only makes the count the control plane reports honest.
- Safe to proceed with Sessions 1–6 (the six parallel convergence-ready checkpoints) and
  Session C (convergence) against this hardened control plane.
