# Gate III — Intelligent Chat Interface Visual Smoke Screenshots

Captured: 2026-05-13 (CROSS_GATE_VISUAL_SMOKE session)
Chart ID: `362f9f17-95a5-490b-a5a7-027d3e0efda0` (Abhisek Mohanty)
Playwright run: 3/3 PASS

## Screenshots

| File | Content | Reviewer checklist |
|---|---|---|
| `empty_state.png` | Full /clients/[id]/consume page empty state | Welcome heading, "Ask anything", suggestion tabs, composer textarea visible |
| `suggestion_tabs.png` | Tab navigation (By type / By moment) | Two tabs rendered with active state indicator |
| `suggestion_grid.png` | Suggested prompts grid | Class-based suggestions grid visible |
| `moment_tab.png` | "By moment" tab content | Moment-based suggestions or loading/error state |
| `before_submit.png` | Composer with query filled | Textarea populated with golden Jyotish query |
| `streaming_response.png` | 3s after submit | Streaming indicator / partial answer visible |
| `partial_answer.png` | 10s after submit | Partial answer text rendered |

## Selector Notes

No `data-testid` attributes on Gate III consume components. Selectors used:
- Welcome heading: `getByText(/welcome/i)` or `getByText(/ask anything/i)`
- Tab navigation: `[role="tablist"]`
- Sanskrit tooltip: `.cursor-help` + `[role="tooltip"]` (if Sanskrit terms appear in response)
- Provenance pills: `[class*="provenance"], [class*="pill"]`

Sanskrit tooltips and provenance pills require a complete answer with Sanskrit terms — the 10s window may not be long enough for all answers. The `cursor-help` elements will appear when `SanskritTermSpan` renders in streaming text.

## Re-run Command

```
# Write a fresh session cookie to /tmp/smoke_session_cookie.txt, then:
npx playwright test tests/e2e/gate_iii_intelligent_chat_smoke.spec.ts --reporter=list --workers=1
```
