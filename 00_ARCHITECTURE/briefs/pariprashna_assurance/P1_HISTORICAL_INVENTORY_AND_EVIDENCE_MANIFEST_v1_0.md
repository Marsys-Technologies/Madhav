# P1 historical inventory and carry-forward evidence manifest v1.0

Status: **OPEN.** Counts below are read-only derivations from the historical
worktree `/Users/Dev/Vibe-Coding/Apps/Madhav/.clone/worktrees/pariprashna-assurance`.
They are not imported into the Option-B runtime.

| Source | Classification | Reconciled fact |
| --- | --- | --- |
| `PARIPRASHNA_CAMPAIGN_STATUS_AT_SELF_PAUSE_v1_0.md` §0 | ACCEPTED_PRIMARY_EVIDENCE | Zero countersigned gates; P-PORTAL halted; native acceptance untouched; no EDIR entry certified FIXED. |
| `state/CAMPAIGN_STATE.json` | ACCEPTED_PRIMARY_EVIDENCE | `execution_mode=AUTONOMOUS`, `current_stage=SELF_PAUSED`; it expressly disclaims completion, gate advance, release, and acceptance. |
| `state/DECISIONS.jsonl` | VERIFIED_CARRY_FORWARD | 83 append-only rows, 77 distinct D-PP IDs (`D-PP-001`…`D-PP-077`). |
| `state/OBLIGATIONS.jsonl` | VERIFIED_CARRY_FORWARD | 144 rows reduce to 77 latest records by `(ruling_id, clause)`: 53 active, 19 discharged, 1 superseded, 1 amended, 1 discharged-in-practice, 2 reclassified-to-native-remediation. |
| `state/VERDICTS.jsonl` | VERIFIED_CARRY_FORWARD | 53 current verdicts: 33 PASS, 14 FAIL, 1 INCONCLUSIVE, 5 RECUSED. |
| EDIR markdown register | ACCEPTED_PRIMARY_EVIDENCE | 115 findings: 113 OPEN, E-010 CLOSED-AS-CODIFIED, E-012 PARKED; zero certified FIXED. |
| `state/EDIR_ID_CLAIMS.jsonl` | DO_NOT_RELY | 85 append-only allocation claims / 83 latest IDs, all CLAIMED; this is not the 115-finding EDIR population. |
| `state/AUTHORITY_HANDOFF.md`, `VERIFIER_HANDOFF.md` | VERIFIED_CARRY_FORWARD | No countersigned gate or fixed EDIR; P-PORTAL halt and recusals remain carried-forward constraints. |
| `state/PARKED.jsonl` | PARKED | E-012 narrowed-proof question awaits fresh native authority. |
| P0–P5 stand-down audit | SUPERSEDED | Its lane wording cannot reopen or complete the autonomous assurance campaign. |

## Obligation status derivation

The 53 active obligations consist of 18 `open`, 6 `open_blocking`, 3
`open_suspended`, 1 `partially_discharged`, and 25 `open_standing`. Raw
append-only statuses must never be summed as the current population.

## Immutable carry-forward limits

Historical deployed claims are pinned to `84c3c903…` and require fresh
deployment verification before a present-tense claim. The historical material
is evidence for P2 intake only; it is not a credential, a live session, or a
runtime event source.
