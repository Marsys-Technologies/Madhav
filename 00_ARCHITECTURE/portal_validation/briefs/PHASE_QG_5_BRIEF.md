---
status: OPEN
session_id: PIV_QG_5
phase: QG.5
phase_name: "UX flow validation — Consume UI v2, lifecycle states, AIOps Control Panel"
next_session: PIV_QG_6
authored_at: 2026-05-14
authored_by: PORTAL_INTEGRATION_VALIDATION_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — PIV_QG_5
## Portal Integration Validation, Step 5 — UX Flow Validation

---

## §0 — Executor orientation

QG.5 validates that the Phase 3 Consume UI v2 + AIOps Control Panel
behave end-to-end against live traffic. Audits the 4 named bug fixes
(model-name location, sidebar hover, reasoning-slot stability,
reasoning emission per ProviderQuirks) under real conditions.

This sub-phase is mostly endpoint-based + DOM/HTML inspection (via
SSR fetches). No headless browser. Where visual confirmation is
strictly needed, defer to a human-acceptance checklist appended to the
deliverable.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/aiops/phase_3/CO7_NATIVE_ACCEPTANCE.md (12-item native checklist)
3. 00_ARCHITECTURE/aiops/phase_3/CONSUME_UI_SPEC_v1_0.md
4. 00_ARCHITECTURE/aiops/phase_3/CO6_A11Y_AUDIT.md
5. platform/src/components/consume/lifecycle/** (StatusPip, ReasoningSlot, etc.)
6. platform/src/lib/hooks/useChatLifecycle.ts
7. platform/src/lib/hooks/useSidebarState.ts
8. platform/src/app/(super-admin)/aiops/control/page.tsx
9. platform/src/lib/components/aiops/** (Control Panel widgets)
```

---

## §2 — Scope

### may_touch
```
00_ARCHITECTURE/portal_validation/QG5_UX_FLOW_AUDIT.md             # NEW
00_ARCHITECTURE/portal_validation/qg5_evidence/                      # NEW
CLAUDECODE_BRIEF.md
```

### must_not_touch
- All production code.
- Persistent AIOps state (read-only fetches only).

---

## §3 — Work plan

### 3.1 — Consume UI v2 SSR fetch

```bash
COOKIE=$(npx --prefix platform tsx platform/scripts/dev/mint_session_cookie.ts)
SERVICE_URL=$(gcloud run services describe amjis-web --region asia-south1 --format='value(status.url)')

mkdir -p qg5_evidence

curl -sf -H "Cookie: __session=$COOKIE" \
     "$SERVICE_URL/consume?chart_id=<test-chart-id>" \
     > qg5_evidence/01_consume_html.html
```

Inspect the rendered HTML for:
- Presence of `<StatusPip>` slot DOM element (data-component="status-pip").
- Absence of model-name string in the input panel area
  (Bug 3.1 fix: model name moved to per-message MetadataBadge).
- Presence of sidebar with `data-state="collapsed"` initial (Bug 3.2).
- Reasoning slot DOM element exists from initial render (Bug 3.3:
  anchored from query submission, not added later).

Grep:
```bash
grep -c 'data-component="status-pip"' qg5_evidence/01_consume_html.html
grep -c 'data-component="reasoning-slot"' qg5_evidence/01_consume_html.html
```

### 3.2 — Lifecycle states under live query

Submit a query and capture the SSE stream → parse for the lifecycle
transitions emitted by `useChatLifecycle`:

```bash
RUN_ID="QG5-LIFECYCLE-$(date +%s)"

curl -sN -H "Cookie: __session=$COOKIE" \
     -H "Content-Type: application/json" \
     -H "x-aiops-stack: deepseek" \
     -H "x-aiops-model-synthesis-primary: deepseek-chat" \
     -H "x-piv-test-run: $RUN_ID" \
     -d '{"messages":[{"role":"user","content":"Brief synthesis of my chart"}],"chart_id":"<test-chart-id>"}' \
     "$SERVICE_URL/api/chat/consume" \
     > "qg5_evidence/02_lifecycle_stream.sse"
```

Parse the SSE stream for event types and assert the sequence includes:
`idle → queued → planning → retrieving → reasoning|composing →
complete`. Missing intermediate state = MEDIUM finding (UX flicker
risk).

### 3.3 — Bug 3.4 — reasoning emission per ProviderQuirks

For each of {anthropic-skip, deepseek (markers), gemini (native), gpt
(none), nim (mixed)}:
- Identify the provider's `reasoning_via` value in registry.
- Submit a query.
- Inspect the SSE stream for `reasoning_delta` events.
- Assert:
  - `reasoning_via: 'none'` → zero reasoning events
  - `reasoning_via: 'native'` or `'markers'` → ≥1 reasoning event
- Mismatch = HIGH finding.

(Anthropic skipped — assume from QG.2 results.)

### 3.4 — AIOps Control Panel render

```bash
curl -sf -H "Cookie: __session=$COOKIE" \
     "$SERVICE_URL/aiops/control" \
     > qg5_evidence/03_aiops_control_html.html
```

Verify rendered HTML contains:
- Stack picker cards for all 6 stacks
- Per-call-type routing table
- Param override panel
- Test probe inline widget
- Catalog snapshot reference

Grep:
```bash
for STACK in nim gemini deepseek gpt anthropic marsys; do
  echo "$STACK: $(grep -c "$STACK" qg5_evidence/03_aiops_control_html.html)"
done
```

Assert: all 6 stacks present in DOM. Missing stack = HIGH.

### 3.5 — /observatory + /trace render check

```bash
curl -sf -H "Cookie: __session=$COOKIE" \
     "$SERVICE_URL/observatory" \
     > qg5_evidence/04_observatory_html.html

curl -sf -H "Cookie: __session=$COOKIE" \
     "$SERVICE_URL/trace" \
     > qg5_evidence/05_trace_html.html
```

Quick render checks (HTTP 200, body contains expected chrome strings).

### 3.6 — Author QG5_UX_FLOW_AUDIT.md

Sections:
- §1 — Consume UI v2: 4 bug fixes confirmed (or finding)
- §2 — Lifecycle transitions: observed vs spec'd
- §3 — Reasoning emission: per-provider audit
- §4 — AIOps Control Panel: 6 stacks present, components render
- §5 — Observatory + Trace: 200 OK + chrome present
- §6 — Findings
- §7 — Human-acceptance checklist (visual items not auto-verifiable):
       - Sidebar hover-expand animation smoothness
       - Reasoning slot CLS < 0.05 visually
       - Mobile breakpoint
       - Keyboard shortcuts (Cmd+Enter / Esc / Cmd+K / Cmd+/)
       - MetadataBadge visual position

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.QG5.1 | Consume page returns 200 + status-pip + reasoning-slot DOM | grep |
| AC.QG5.2 | Lifecycle transitions ≥4 distinct states in SSE | parsed |
| AC.QG5.3 | Reasoning emission per `reasoning_via` audited per provider | matrix |
| AC.QG5.4 | AIOps Control Panel: all 6 stacks present in DOM | count = 6 |
| AC.QG5.5 | Observatory + Trace pages return 200 | curl exit code |
| AC.QG5.6 | Human-acceptance checklist appended (§7) | grep |
| AC.QG5.7 | QG5_UX_FLOW_AUDIT.md authored with §1–§7 | grep |
| AC.QG5.8 | Cumulative PIV LLM cost < $0.70 | sum |
| AC.QG5.9 | Scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Commit + rotate to QG.6.

---

## §6 — BAIL OUT

- Consume page returns 5xx (production broken).
- AIOps Control Panel page returns 5xx.
- Reasoning emission mismatches `reasoning_via` for >2 providers
  (indicates adapter routing regression).

---

*End of PHASE_QG_5_BRIEF.md*
