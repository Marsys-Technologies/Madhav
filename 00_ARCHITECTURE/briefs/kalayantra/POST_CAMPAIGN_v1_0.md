---
artifact: POST_CAMPAIGN_v1_0.md
version: '1.0'
status: ACTIVE
authority: 'SR-PARKED-OUT-OF-CAMPAIGN (owner surrogate madhav-44, 2026-10-22 ~20:06Z; owner direction OWNER-WRAP-NOW-20261022)'
changelog:
  - '1.0 (2026-10-22): created; thirteen parked items deferred out of the KĀLA-YANTRA v3 campaign, each with its re-entry condition.'
---

# KĀLA-YANTRA v3 — post-campaign list

Work the campaign does not do. Each row is deferred, not closed: the tracker shows it as deferred (triage class `b`, outside the acceptance closure) and never counts it as done. The re-entry condition is the item's own `triage.re_entry` in `00_ARCHITECTURE/control/kalayantra/plan_model.json`; this list carries the same text. Source of the edit: `fleet/kya9plan.py` (`PARKED_OUT_OF_CAMPAIGN`).

## Deferred by SR-PARKED-OUT-OF-CAMPAIGN

| Item | What it is | Re-entry condition |
|---|---|---|
| KR-1 | Contract phase: delete code whose replacement is published (the Saṅgam compatibility shim and the other superseded modules) | after V-J6 is accepted and the served layer has run one week on 5.0 |
| KR-2 | Retire the legacy second writers that write the same tables as `ka_sangam` and `ka_vighnakara` | after V-J6 is accepted and the served layer has run one week on 5.0 |
| J-7a | Phase 12 — legacy retirement: retire the `ka_gochara` writer after the flip; handle the `_v2` / `2.0` rows | after V-J6 is accepted and the served layer has run one week on 5.0 |
| J-7a-pr3099 | Keep inherited PR #3099: migration 1303 revoking `role_orchestrator` writes on the five remaining Gochara tables | after V-J6 is accepted and the served layer has run one week on 5.0 |
| J-7a-a62 | Keep inherited Pravāha A6.2: Century writer retired; registry and seed aligned; Disclosure 3 closed | after V-J6 is accepted and the served layer has run one week on 5.0 |
| J-8 | Pravāha close report written and merged | post-campaign, as documentation (was: at campaign close) |
| J-8a | Remaining Pravāha items dispositioned in their own tracker; on-disk run material archived; Pravāha tracker left read-only | post-campaign, as documentation (was: at campaign close) |
| J-8-b63 | Keep inherited Pravāha B6.3: campaign close report, CURRENT_STATE and session log | post-campaign, as documentation (was: at campaign close) |
| J-8-j3 | Keep inherited Pravāha J3: campaign closed | post-campaign, as documentation (was: at campaign close) |
| J-4a-a25 | Keep inherited Pravāha A2.5: the '4.1' build for chart 482012f1 over the scored horizon (candidate only) | when the owner/surrogate records the approved Q6 disposition of the historical 4.1 build, or a phase brief names the 4.1 build as a measured input |
| J-4a-a26 | Keep inherited Pravāha A2.6: '4.1' evidence (Link-2, gates, PRAMĀṆIN, benchmark metrics) | when J-4a-a25 re-enters and the 4.1 evidence (Link-2, gates, PRAMĀṆIN, benchmark) is wanted by a phase brief |
| J-3a-b44 | Keep inherited Pravāha B4.4: the '4.1' geometric baseline scored under the accepted protocol (needs the 4.1 build of J-4a-a25) | when the owner/surrogate records the approved Q6 disposition of the historical 4.1 build, or a phase brief names the 4.1 build as a measured input |
| L0-K | KP Reader V/VI local OCR ingested into the served corpus, with the custodian's count recorded | post-flip: after V-J6 is accepted and the served layer has run one week on 5.0 (as the J-7a family) |

## Related post-campaign work recorded elsewhere

- **D-T2 admission work.** The decision item closed under SR-DT2-CANDIDATE (2026-10-22): Sudarśana is admitted as a CANDIDATE judge method; Tājaka and KP each wait for their own review and corpus count. The admission work itself is post-campaign (`DECISIONS_SURROGATE.jsonl`, SR-DT2-CANDIDATE).
- **Earlier A9 deferrals** (K9-5, K9-5-NB-01) keep their own re-entry conditions in `FINAL_MESSAGE_DRAFT.md` and the plan model.
- **The materializer-timeout pair** (D-GOCHARA-TIMEOUT, J-GOCHARA-TIMEOUT) ended `not_applicable` by D-GOCHARA-TIMEOUT-NA (SR-AUDIT-NA-TIMEOUT, 2026-10-22); the century's writer timeout is set by migration 1395. Re-entry only if J-4f shows a timeout binding.
