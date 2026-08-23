# Budget ledger — Paripraśna P3+P4 overnight run (§0 ruling 10)

**Total authorized: $400 API-cost-equivalent.** Two subtotals, one ledger.
- **P3 half: $250** (the 2026-08-22 re-ruling of DD-5's P3=$80)
- **P4 half: $150** (DD-5's P4 figure, unchanged)

A phase halts cleanly at a lane boundary when its subtotal is reached. **A P3 overrun may NOT eat
P4's allocation or vice versa without a NATIVE-SURROGATE ledger entry explaining why the transfer
was safe.** Raising the $400 total is a MUST-PARK (§3.3) — never decided overnight.

## Accounting method (honest, stated up front)

Build spend tonight is **agent-token cost**, not app-runtime LLM cost. It is **estimated, not
metered** — no per-agent invoice exists at run time. The estimate below is derived from agent
count × model tier × observed turn volume, and is deliberately conservative (rounds up). This
limitation is disclosed rather than hidden; the morning report repeats it. Runtime app caps
($2/turn · $40/day, NCD-8) are a separate, unrelated meter.

| Time (IST) | Phase | Item | Est. $ | P3 running | P4 running | Combined |
|---|---|---|---|---|---|---|
| 03:00 | — | Run open: charter read, orientation, lease, PR #1493 | 3 | — | — | 3 |
| 03:05 | both | Wave-1 spawn: surrogate (Opus) + 9 lane builders | 12 | 6 | 6 | 15 |

**Run-open position: ~$15 of $400. P3 ~$6/$250 · P4 ~$6/$150.**
| 03:20 | both | Wave-1 build turns (P3-A returned 269K subagent tokens; others mid-flight) | 38 | 22 | 24 | 46 |
| 03:20 | P3   | REFUTER on P3-A (Opus, adversarial) + surrogate follow-up rulings | 9 | 28 | 24 | 52 |

**Position ~03:20 IST: ~$52 of $400 (metered $0 + estimated-upper $52). P3 ~$28/$250 · P4 ~$24/$150.**
Measurement tag: **estimated**, basis = subagent token counts reported by the harness × model-class
rates, rounded up. Error direction: **UNDER** — conductor-session tokens are not itemized per lane.
| 03:37 | — | CRASH-RESUME: conductor re-orientation (fetch, PR/CI reads, worktree census, tracker) | 4 | 30 | 26 | 56 |
| 03:45 | both | Wave-R re-dispatch: 10 agents (4 Opus refuters/diagnostician, surrogate, 4 builders) | 58 | 62 | 52 | 114 |
| 04:05 | both | Returns: P4-J closed (PR #1499) · P4-H REFUTED · P3-A REFUTED | — | — | — | 114 |
| 04:10 | P3 | P3-A remediation builder + P4-J refuter dispatched | 14 | 72 | 56 | 128 |

**Position ~04:10 IST: ~$128 of $400. P3 ~$72/$250 · P4 ~$56/$150.**
Measurement tag: **estimated**, basis = subagent token counts reported by the harness × model-class
rates, rounded up. Error direction: **UNDER** — conductor-session tokens are not itemized per lane.
Note the P4 subtotal is over a third spent with the RETIRE train never opened; if the flip does not
fire, P4's remaining allocation has little to buy, and the surrogate has been asked to set the
checkpoint discipline (Q5) rather than the conductor assuming a transfer is safe.
| 04:00 | both | Wave-R2: surrogate r1 (Opus) + P4-K/P4-I/P4-J refuters + P4-G/P3-C/DD1 builders returning | 62 | 105 | 85 | 190 |
| 04:06 | both | Wave-R3 dispatch: P4-J remediation (Opus), P3-C refuter (Opus), DD1 refuter (Opus), surrogate r2 (Opus), P4-I remediation, P4-G refuter+voice (Opus), P3-D prep, rollback pin | 55 | 130 | 115 | 245 |

**Position ~04:10 IST: ~$245 of $400 (estimated). P3 ~$130/$250 · P4 ~$115/$150.**
Measurement tag: **estimated · NOT METERED · error direction UNDER** (per surrogate ruling D-010, the
morning report must use this wording and never the bare word "spend"). Conductor-session tokens are
not itemized per lane and the conductor is plausibly among the night's largest single consumers.
Treat as a **lower bound, not a measurement**.

**Checkpoint status against D-010's binding table:**
- P3 $130 / no-new-lanes at $175 — **headroom, but narrowing**
- P4 $115 / no-new-lanes at $105 — **CHECKPOINT CROSSED. No new P4 lanes may be opened.** In-flight P4
  lanes (P4-J remediation, P4-I remediation, P4-G refuter, DD-1 refuter) continue to their natural
  close, which is exactly what gating on *opening* rather than *spending* is designed to permit
  (§0 ruling 10 — each subtotal halts at a lane boundary, never mid-lane).
- Combined $245 / no-new-lanes at $280, drain-only at $340 — **headroom.**

**Conductor action taken on crossing the P4 checkpoint:** no further P4 lane openings. Remaining
capacity goes to P3 lanes (P3-D prep, the rollback pin) and the governance close. No subtotal transfer
requested — D-010's test for a safe transfer requires a P3-critical-path task blocked *purely* on its
subtotal, and P3's blocker is a credential, not money.
| 05:00 | P3 | Limits enablement canary + V1-V5 (conductor-executed, no subagent) | 6 | 136 | 115 | 251 |
| 05:05 | both | Returns: P4-G REFUTED+panel · DD1 REFUTED · P3-E PARK · P3-C SURVIVES · rollback pin | — | — | — | 251 |
| 05:10 | P4 | DD-1 battery remediation + P4-H park work (both continuing OPEN lanes, permitted) | 22 | 136 | 137 | 273 |

**Position ~05:10 IST: ~$273 of $400 (estimated · NOT METERED · errs UNDER).**
P3 ~$136/$250 · P4 ~$137/$150. **Combined $273 approaching the $280 no-new-lanes checkpoint.**
No new lanes of either phase will be opened. Remaining spend: in-flight lanes draining, small
comment-only remediations on already-open lanes, the merge train, and the governance close.
