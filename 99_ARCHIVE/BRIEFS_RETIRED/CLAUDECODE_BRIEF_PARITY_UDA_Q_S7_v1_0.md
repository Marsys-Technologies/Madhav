---
title: "CLAUDECODE_BRIEF — Parity Campaign UDA-Q-S7: Quality Backport LL.1 calibration → MCP query_signals"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_Q_S7
version: 1.0
status: CURRENT
phase: UDA-Q
session_id: UDA-Q-S7
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
authored_by: Conductor (2026-05-25)
---

# UDA-Q-S7 — Quality Backport: LL.1 calibration → MCP query_signals

## 1. Context

The portal `msr_sql.ts` applies **LL.1 production weights** — a NAP.M4.5-approved calibration
of 30 signal weights (inlined from `ll1_weights_promoted_v1_0.json`) — to adjust raw signal
confidence values. It also applies **domain-specific confidence floors** (e.g. finance/wealth
signals have a lower floor of 0.35 vs global 0.6). Additionally it **deduplicates the
Pancha-Mahapurusha clique** (7 signals collapsed to MAX weight).

The MCP `query_signals.ts` returns raw `confidence` values without any of this calibration,
causing the two channels to disagree when fetching the same signals.

This session backports the LL.1 weights, domain floors, and Pancha-MP clique dedup into
`platform-mcp/src/tools/query_signals.ts`.

**Source of truth:** `platform/src/lib/retrieve/msr_sql.ts` (read-only)
**Target to modify:** `platform-mcp/src/tools/query_signals.ts`

---

## 2. Scope

**may_touch:**
- `platform-mcp/src/tools/query_signals.ts`

**must_not_touch:**
- `platform/src/lib/retrieve/msr_sql.ts` (source reference only)
- `platform-mcp/src/server.ts`
- Any governance files

---

## 3. Acceptance Criteria

- [ ] AC.Q7.1: `platform-mcp/src/tools/query_signals.ts` contains the `LL1_PRODUCTION_WEIGHTS` map (or imports it)
- [ ] AC.Q7.2: The tool applies LL.1 weights to adjust confidence before returning results: `calibrated_confidence = raw_confidence * (ll1_weight ?? 1.0)`
- [ ] AC.Q7.3: Domain-specific confidence floors are applied: finance/wealth domains use floor 0.35, all others 0.6
- [ ] AC.Q7.4: The Pancha-Mahapurusha clique (SIG.MSR.117/118/119/143/145/402/402b) is deduplicated to MAX weight when multiple signals from the clique appear
- [ ] AC.Q7.5: `cd platform-mcp && npx tsc --noEmit` passes with 0 errors
- [ ] AC.Q7.6: Commit message contains `UDA-Q-S7`

---

## 4. Step-by-Step Execution

### Step 1 — Read both tools

```bash
cat platform/src/lib/retrieve/msr_sql.ts
cat platform-mcp/src/tools/query_signals.ts
```

Extract the `LL1_PRODUCTION_WEIGHTS` Map, `FINANCE_WEALTH_CONFIDENCE_FLOOR`, `PANCHA_MP_CLIQUE`
Set, and the calibration application logic from `msr_sql.ts`.

### Step 2 — Copy LL.1 constants into query_signals.ts

Add at the top of `platform-mcp/src/tools/query_signals.ts` (after imports):

```typescript
const LL1_PRODUCTION_WEIGHTS = new Map<string, number>([
  // paste the full 30-entry map from msr_sql.ts
])

const FINANCE_WEALTH_DOMAINS = new Set(['finance', 'wealth'])
const DEFAULT_CONFIDENCE_FLOOR = 0.6
const FINANCE_WEALTH_CONFIDENCE_FLOOR = 0.35

const PANCHA_MP_CLIQUE = new Set([
  'SIG.MSR.117', 'SIG.MSR.118', 'SIG.MSR.119',
  'SIG.MSR.143', 'SIG.MSR.145', 'SIG.MSR.402', 'SIG.MSR.402b',
])
const PANCHA_MP_CONSOLIDATED_ID = 'PANCHA_MP_CLIQUE_CONSOLIDATED'
```

### Step 3 — Apply calibration to returned signals

After receiving signal rows from `callPlatformPrimitive` (or directly from DB), apply:

```typescript
function calibrateSignals(signals: MsrSignalRow[]): MsrSignalRow[] {
  // 1. Apply LL.1 weights
  let calibrated = signals.map(s => ({
    ...s,
    confidence: s.confidence * (LL1_PRODUCTION_WEIGHTS.get(s.signal_id) ?? 1.0),
  }))

  // 2. Apply domain confidence floor
  calibrated = calibrated.filter(s => {
    const floor = FINANCE_WEALTH_DOMAINS.has(s.domain ?? '')
      ? FINANCE_WEALTH_CONFIDENCE_FLOOR
      : DEFAULT_CONFIDENCE_FLOOR
    return s.confidence >= floor
  })

  // 3. Pancha-MP clique dedup: keep only the max-confidence entry
  const cliqueEntries = calibrated.filter(s => PANCHA_MP_CLIQUE.has(s.signal_id))
  if (cliqueEntries.length > 1) {
    const maxEntry = cliqueEntries.reduce((a, b) => a.confidence >= b.confidence ? a : b)
    calibrated = [
      ...calibrated.filter(s => !PANCHA_MP_CLIQUE.has(s.signal_id)),
      { ...maxEntry, signal_id: PANCHA_MP_CONSOLIDATED_ID },
    ]
  }

  return calibrated
}
```

Apply `calibrateSignals(rawSignals)` before building the response.

### Step 4 — TypeScript compile check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
cd platform-mcp && npx tsc --noEmit
```

### Step 5 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform-mcp/src/tools/query_signals.ts
git commit -m "feat(UDA-Q-S7): backport LL.1 calibration, domain floors, Pancha-MP dedup to MCP query_signals

Matches portal msr_sql calibration quality. NAP.M4.5 weights inlined.
tsc: 0 errors."
```

---

## 5. Gate Commands

```bash
grep -q "ll1_weights\|calibrat\|confidence.*floor\|domain_floor" platform-mcp/src/tools/query_signals.ts && echo 'GATE_UDA_Q_S7_LL1: PASS'
git log --oneline -3 | grep -q 'UDA-Q-S7' && echo 'GATE_UDA_Q_S7_COMMIT: PASS'
```

All 2 gates must print PASS.

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_Q_S7_v1_0.md*
