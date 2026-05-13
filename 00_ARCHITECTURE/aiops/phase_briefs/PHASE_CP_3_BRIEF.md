---
status: OPEN
session_id: AIOPS_CP_3
phase: CP.3
phase_name: "Call-site migration + eval/smoke/checkpoint wiring + Observatory deep links"
next_session: AIOPS_CP_4
authored_at: 2026-05-13
authored_by: AIOPS_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_CP_3
## AIOps Phase 1, Step 3 — Wire AIOps into runtime

---

## §0 — Executor orientation

CP.3 is the integration phase. The Control Panel itself is feature-complete
after CP.2. CP.3 makes the rest of the codebase *consume* from runtime_config
instead of reading STACK_ROUTING directly. After CP.3 closes, flipping
`AIOPS_OVERRIDES_ENABLED=true` (which happens in CP.5) makes every part of
the system honor the Control Panel's choices.

Two flag states to remember during CP.3:
- Flag **off** (default): every call site falls through to the registry —
  byte-identical to today's behavior.
- Flag **on** (CP.5 only): every call site reads DB overrides first.

CP.3 must produce code that works correctly under BOTH flag states. Tests
must cover both.

---

## §1 — Mandatory reads

```
1.  CLAUDE.md
2.  00_ARCHITECTURE/aiops/AIOPS_MASTER_PLAN_v1_0.md §7, §10
3.  00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
4.  platform/src/lib/models/runtime_config.ts  (CP.1 deliverable)
5.  platform/src/lib/synthesis/single_model_strategy.ts
6.  platform/src/lib/synthesis/panel/adjudicator.ts
7.  platform/src/app/api/chat/consume/route.ts  (synthesis call site)
8.  platform/scripts/eval/  — list every eval entry point
9.  platform/scripts/observatory/smoke_test.ts
10. platform/src/lib/checkpoints/  — find checkpoint_4_5/5_5/8_5
11. platform/src/lib/components/observatory/StackBreakdownCards.tsx
```

---

## §2 — Scope

### may_touch
```
platform/src/lib/synthesis/**                                 # call-site migration
platform/src/app/api/chat/consume/**                           # call-site migration
platform/src/lib/checkpoints/**                                # call-site migration
platform/scripts/eval/**                                       # script migration
platform/scripts/observatory/smoke_test.ts                     # script migration
platform/scripts/checkpoint/**                                 # script migration
platform/src/lib/components/observatory/StackBreakdownCards.tsx  # add "Configure" pencil ONLY
platform/src/app/(super-admin)/observatory/page.tsx             # if needed for deep-link query param
platform/src/app/(super-admin)/aiops/control/page.tsx           # accept ?stack= query param
platform/src/lib/aiops/**                                      # supporting helpers
CLAUDECODE_BRIEF.md
```

### must_not_touch
- Everything outside `may_touch`. In particular:
- `platform/src/app/api/admin/observatory/**` — Observatory backend stays sealed.
- Any Observatory component file *except* `StackBreakdownCards.tsx`.
- `00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md`.

---

## §3 — Work plan

### 3.1 — Discover every model-selection call site

Run:
```bash
cd platform
# Direct readers of STACK_ROUTING:
grep -rn "STACK_ROUTING\[" src/ scripts/
# Helper readers:
grep -rn "getPrimaryModel\|getFallbackModel\|getStackModel\|CALL_TYPE_ROUTING" src/ scripts/
# NIM-specific helpers:
grep -rn "getNvidiaPlanner\|getNvidiaContextAssembler\|getNvidiaSynthesisModel" src/ scripts/
```

Capture the full list in a session note at
`00_ARCHITECTURE/aiops/CP3_CALL_SITES_INVENTORY.md`. This is a session
artifact (not a canonical artifact) — useful for audit.

### 3.2 — Migrate runtime pipeline call sites

For each call site found in §3.1 (pipeline / consume / synthesis):

- Replace direct registry reads with `await getEffectiveModel(stack, callType, role, req?)`.
- Where appropriate, also replace inline `maxOutputTokens` / `temperature`
  constants with `await getEffectiveParam(stack, callType, 'max_output_tokens', defaultValue, req?)`.

The migration is mechanical. Confirm each file still typechecks and its
tests still pass before moving to the next.

Special cases:
- **`single_model_strategy.ts`** — synthesis path. Add `req?: Request`
  threading from the route handler if it isn't there already.
- **`adjudicator.ts`** — panel path. Same pattern.
- **NIM helpers** (`getNvidiaPlanner` etc.) — leave the function but rewire
  internals to call `getEffectiveModel('nim', callType, 'primary')`. This
  preserves the existing API for any caller, while routing through
  runtime_config.

### 3.3 — Migrate eval scripts

For each script under `platform/scripts/eval/`:

- Identify the hardcoded model_id (e.g., `claude-opus-4-6` or
  `gemini-2.5-flash-lite`).
- Replace with:
  ```ts
  const judgeModel = await getEffectiveModel('marsys', 'eval_judge', 'primary')
  ```
  Falling back to `eval_judge`'s registry seed (per Execution Rule R13)
  preserves behavior under flag-off.

Tests under `platform/scripts/eval/__tests__/`: confirm the script picks up
overrides when the flag is on.

### 3.4 — Migrate smoke + checkpoint scripts

Same pattern. `smoke_test.ts` uses `smoke_synth`; checkpoint scripts use
`checkpoint_4_5/5_5/8_5`.

### 3.5 — Observatory "Configure" pencil

The ONLY edit to Observatory in this entire feature.

Edit `platform/src/lib/components/observatory/StackBreakdownCards.tsx`:
- Add a small pencil icon to the top-right of each stack card.
- onClick → `router.push('/aiops/control?stack=<stack>&from=observatory')`.
- No other layout / data change.

In `platform/src/app/(super-admin)/aiops/control/page.tsx`:
- Read `?stack=` query param on mount.
- If present and valid, pre-select that stack in the Stack Picker.
- If `?from=observatory` is also present, show a small inline note: "Came
  from Observatory — back to /observatory".

### 3.6 — Wire `from=control-panel` reverse direction

In `platform/src/lib/components/aiops/StackPickerCards.tsx`:
- Each card already has a "View usage" link (added in CP.2).
- Confirm the href is `/observatory?stack=<stack>&from=aiops`.

In `platform/src/lib/components/observatory/filters/useObservatoryFilters.ts`:
- Honor `?stack=<stack>` from the URL on mount. (This may already work for
  other filters; just confirm + extend.)

### 3.7 — Cache invalidation event

Confirm that the write endpoints from CP.2 call
`invalidateRuntimeConfigCache()` after each write. If they don't yet,
add the call.

The Observatory does not need to invalidate its own state — observability
data is append-only, not config.

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.CP3.1 | No direct `STACK_ROUTING[` reads in `platform/src/` outside of runtime_config.ts and registry.ts itself | grep returns empty |
| AC.CP3.2 | No direct `STACK_ROUTING[` reads in `platform/scripts/` | grep returns empty |
| AC.CP3.3 | Inventory file present | `test -f 00_ARCHITECTURE/aiops/CP3_CALL_SITES_INVENTORY.md` |
| AC.CP3.4 | Flag-off equivalence: with `AIOPS_OVERRIDES_ENABLED=false`, snapshot of `getPrimaryModel('gemini','synthesis')` equals current registry value for all (stack, callType) pairs | parametrized test, ≥35 cases |
| AC.CP3.5 | Flag-on override: set DB override for `gemini.synthesis.primary='gemini-2.5-flash'`; call `getEffectiveModel` with flag on; returns `gemini-2.5-flash`. Reset; returns the registry default. | integration test |
| AC.CP3.6 | Observatory deep-link pencil visible on every stack card | snapshot test of `StackBreakdownCards` |
| AC.CP3.7 | Control Panel honors `?stack=` query param | UI test |
| AC.CP3.8 | Observatory honors `?stack=` query param | existing filter test extended |
| AC.CP3.9 | All eval scripts read judge model from runtime_config | grep + integration test |
| AC.CP3.10 | smoke_test.ts reads model from runtime_config | grep + integration test |
| AC.CP3.11 | Checkpoint scripts read models from runtime_config | grep + integration test |
| AC.CP3.12 | `npm run typecheck` | exit 0 |
| AC.CP3.13 | `npm run lint` | exit 0 |
| AC.CP3.14 | Full test suite green | exit 0 |
| AC.CP3.15 | scope-violation grep | SCOPE_OK |
| AC.CP3.16 | Manual: with flag off, run a real /consume query end-to-end; observed model_id in Observatory matches registry default for the active stack | captured in commit body |

---

## §5 — Test minimums

- Equivalence test (flag-off snapshots): ≥35 cases (6 stacks × ~5-6 call types).
- Override test (flag-on): ≥6 cases per (stack × call_type).
- Deep-link tests: ≥4 cases.
- Eval/smoke/checkpoint integration: ≥3 cases each = ≥15.

Total ≥ 80 new tests.

---

## §6 — Session close

Final commit `feat(aiops-CP.3): call-site migration + script wiring + Observatory deep links`.
Rotate CLAUDECODE_BRIEF.md → PHASE_CP_4_BRIEF.md.

---

## §7 — BAIL OUT triggers (CP.3 specific)

- A call site needs deep refactoring to thread `req` — if the change pulls in
  >5 unrelated files, BAIL OUT and let native scope a smaller alternative.
- The Observatory's `useObservatoryFilters` hook can't accept a new query
  param without invasive changes.
- Flag-off equivalence test fails — there's a hidden bug in CP.1's resolver
  that the new tests surface.

---

*End of PHASE_CP_3_BRIEF.md*
