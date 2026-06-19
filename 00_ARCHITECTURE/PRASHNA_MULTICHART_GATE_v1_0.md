---
artifact: PRASHNA_MULTICHART_GATE_v1_0.md
document: Prashna multi-chart platform coupling gate
status: CURRENT
version: 1.0
date: 2026-06-18
authored_by: Cowork (Phase 1 Prashna horary implementation; multi-chart activation blocked)
changelog:
  - v1.0 (2026-06-18): initial gate document; single-querent Phase 1 workaround locked in place; multi-chart activation requirements specified.
---

# Prashna multi-chart platform coupling gate

## §1 — What is gated

Full activation of arbitrary-querent Prashna (horary astrology) is blocked until the platform's multi-chart infrastructure is built. Today, only the **native-querent** horary chart can be computed correctly. For any other querent (different birth place, date, or time), the computed chart receives **wrong planetary positions** — they default to the native's hardcoded birth parameters instead of the question-moment parameters.

This gate documents the technical root cause and the Phase 1 workaround. It will be resolved when the multi-chart platform is complete.

## §2 — Root cause: `ga_positions` orchestrator adapter missing `birth_params`

The orchestrator's `ga_positions` adapter (line 24 of `platform/python-sidecar/pipeline/orchestrator/writers/ga_positions.py`) calls:

```python
s = build_ga_positions(
    chart_id=ctx.config['chart_id'],
    build_id=ctx.build_id,
    conn=ctx.db_conn,
    # birth_params NOT passed → falls back to NATIVE_BIRTH in ga_positions_writer.py
)
```

The underlying `build_ga_positions()` function in `ga_writers/ga_positions_writer.py` (line 436) accepts:

```python
def build_ga_positions(
    chart_id: str,
    build_id: str,
    conn: Any,
    birth_params: dict[str, Any] | None = None,
    ...
) -> dict[str, Any]:
    bp = birth_params or NATIVE_BIRTH  # Line 458
```

When `birth_params` is `None`, the function defaults to `NATIVE_BIRTH` — the hardcoded birth parameters of the native (Abhisek Mohanty, 1984-02-05 10:43 IST). This is correct for native charts but **breaks for any non-native chart built through the orchestrator**, because the orchestrator has no way to pass the querent's actual birth parameters into `ctx.config`.

## §3 — Phase 1 workaround (in place)

To enable single-querent Prashna during L1 closure (Phase B), the horary module (`ga_prashna_cast.py`, line 204) **bypasses the orchestrator entirely** and calls `build_ga_positions()` directly:

```python
build_ga_positions(
    chart_id=prashna_chart_id,
    build_id=build_id,
    conn=conn,
    birth_params=birth_params,  # <-- workaround: direct pass of question-moment params
)
```

This path works because:
1. `ga_prashna_cast.py` has access to the question-moment parameters (parsed from the query instant).
2. It needs only `ga_positions` + `bg_prashna_rules` (not the full L1 suite).
3. The direct call bypasses the orchestrator and avoids the `ctx.config` limitation.

**Status: LOCKED IN PLACE for Phase 1.** The workaround is documented here precisely so it can be cleanly removed when multi-chart is ready.

## §4 — What the multi-chart platform must provide

The orchestrator cannot deliver multi-chart support without these changes:

### §4.1 — ContextSpec must carry `birth_params`

Today, `ContextSpec` (the orchestrator's context object) includes only:
- `config['chart_id']` (the chart to build)
- `config['ayanamsha_id']` (the ephemeris mode)

For multi-chart, the orchestrator must **pass the querent's birth parameters through the context**. Options:
1. Extend `config` to include `birth_params` (minimal, backward-compatible).
2. Create a new `ContextSpec.birth_params` field (cleaner, requires orchestrator contract revision).

The birth parameters must come from a **`charts` table** or equivalent multi-chart registry that maps `chart_id` → `{date, time, place, ayanamsha}`.

### §4.2 — All orchestrator adapters must accept and pass `birth_params`

Every writer adapter that currently defaults to `NATIVE_BIRTH` must be updated to:
1. Retrieve `birth_params` from `ctx.config` or `ctx.birth_params`.
2. Pass it downstream to the heavy-lift writer function.

Known adapters affected:
- `ga_positions` (§2 above)
- Any future L2+ writer that computes values relative to a querent's chart.

### §4.3 — Multi-chart governance requirements

Once multi-chart is live:
- The `charts` table must be authoritative for all `(chart_id, birth_params)` pairs.
- The orchestrator must fetch from `charts` before calling any writer.
- No L1+ writer may default to `NATIVE_BIRTH`; that is a gate-violation bug.

## §5 — How to remove the workaround when multi-chart exists

**Sequence:**

1. **Multi-chart infrastructure is complete.** The `charts` table exists; `ContextSpec` carries `birth_params`.

2. **Update `ga_positions` adapter.** Modify line 24-28 in `platform/python-sidecar/pipeline/orchestrator/writers/ga_positions.py` to:
   ```python
   s = build_ga_positions(
       chart_id=ctx.config['chart_id'],
       build_id=ctx.build_id,
       conn=ctx.db_conn,
       birth_params=ctx.config['birth_params'],  # or ctx.birth_params if that field exists
   )
   ```

3. **Audit all other adapters** that have similar hardcoded defaults. Update them the same way.

4. **Delete the direct call in `ga_prashna_cast.py`.** Lines 203-209 can be removed; the orchestrator will handle the full build.

5. **Commit with message:**
   ```
   chore(prashna): remove single-querent workaround — multi-chart orchestrator now active
   ```

6. **Update this gate document** to status `RESOLVED` with a note on the closing PR/commit SHA.

## §6 — Acceptance criteria for multi-chart readiness

Multi-chart is ready to remove this gate when:
- [ ] `charts` table is live and populated with querent birth data.
- [ ] `ContextSpec` carries querent birth parameters (via `config['birth_params']` or new field).
- [ ] Orchestrator fetch path is integrated (calls `charts` before writer invocation).
- [ ] All orchestrator adapters updated to pass `birth_params` downstream.
- [ ] E2E test: non-native Prashna chart built via orchestrator has correct planetary positions.
- [ ] Direct-call path in `ga_prashna_cast.py` deleted; all paths go through orchestrator.

---

*End of PRASHNA_MULTICHART_GATE_v1_0.md — Phase 1 workaround documented; multi-chart activation pending.*
