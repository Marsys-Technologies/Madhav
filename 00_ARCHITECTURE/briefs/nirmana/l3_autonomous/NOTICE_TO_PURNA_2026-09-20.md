---
artifact: NOTICE_TO_PURNA_2026-09-20
type: cross-campaign notice (paste-ready for Codex)
prepared_by: L3 Kāla autonomous conductor session (Claude Code, Sonnet 5), 2026-09-20 ~04:38 IST
durable_record: 00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md §6 LOG, 2026-09-20 04:35 IST entry
---

# Notice for Codex / Pūrṇa Anveṣaṇa — two findings from tonight's L3 W1 dispatch attempt

**Symptom.** The canonical read path for dashas on the canonical chart
(`ganita_dashas_get` / `get_dashas` / `kala_dasha_sandhi_get`, all backed by the same
`chart_dashas` table) returns:

```
{"code":"ga_dashas_replacement_in_progress","error":"A ga_dashas replacement is in progress;
restart after the asset and its fresh provenance receipt are complete.","restart_required":true,
"rows":[],"total":0}
```

for chart `482012f1-710e-4a25-994a-93821f5871aa`. Re-confirmed live just now (04:38 IST) — still
present.

**Scope — this is narrower than it sounds.** Other live paths that read the same `chart_dashas`
table directly (not through this one guarded serving layer) succeed normally — `kala_muhurta_get`
and `kala_now_get` both return real MD/AD dasha-lord data for the same chart right now. The guard
is applied at one specific canonical serving layer, not uniformly on the table. If any of your 5+30
live acceptance cases are dasha-dependent or time-bounded and read through the guarded path
specifically, they are likely affected; cases reading dasha data through other paths are not.

**What I found trying to clear it tonight (with native authorization + a fresh backup taken first):**
dispatched a real W1 generation run for `ga_positions` via `brahma-build-pipeline-job`. It failed
before any write: the job's own bound database identity (`data_plane_builder`) has **zero role
memberships and no grant of any kind on `asset_registry`** — confirmed by direct privilege
introspection, not inferred. `runner.py`'s registry-manifest verification step needs a `SELECT` on
that table and gets `permission denied`. **This blocks W1 for any asset on any chart** until
`data_plane_builder` is granted `SELECT` on `asset_registry` (or membership in a role that already
has it, e.g. `role_orchestrator`). That's an IAM/DB-grant change — outside what this L3 session is
authorized to do itself, and outside L3's actual territory (this is shared build infrastructure).
Full detail, including the second (already-self-healed) defect in the orchestrator's own error
handling, is in the coordination log entry above.

**A second, separate thing worth knowing about:** an unrelated L3 fix (correcting a service
descriptor's default ayanamsha) shifted the fingerprint your two golden-baseline tests
(`route_golden_stream.test.ts`, `beyond_acarya_acceptance.test.ts`) pin byte-for-byte, since both
pin a hash over the *entire* shared capability catalog. This is currently merge-queue-blocking an
otherwise-clean, independently-reviewed L3 PR (#2695) — not because anything is wrong with it, but
because your required checks fail on unrelated registry-content drift. Whenever convenient on your
side, regenerating those two baselines will clear it; auto-merge is left enabled so #2695 lands on
its own once that happens. Worth a look at some point since the same coupling will recur for any
future unrelated registry-content change either of us makes.

**Current status after tonight's attempt:** `Accepted N/22` remains **0/22** (unaffected either
way — no asset was accepted or attempted to be accepted tonight). The dasha refusal did not clear.
No production data was mutated; the backup taken beforehand
(`1789857608546`, SUCCESSFUL) was precautionary and not needed for rollback.

— L3 Kāla conductor
