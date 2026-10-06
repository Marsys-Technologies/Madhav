---
artifact: JOURNEY6_CAPABILITY_INVENTORY
version: 1.0
status: CURRENT
changelog:
  - 2026-10-06: Fresh source inventory and explicit compatibility/action dispositions.
---

# Journey 6 capability and route dispositions

Inventory against main b1fe14ef and reviewed delivery source. Prototype paths are design identities; they are not evidence that an application route ever existed. First consolidated analytical/diagnostic/learning surfaces are read-only. Retain canonical controls and services rather than creating a second writer.

| Design / capability | Released application destination and disposition |
|---|---|
| Administration / Requests / Users / Charts / AI Access | `/admin`; existing `?tab=pending`, `users`, `charts`, `ai-access` preserved. Admission/account/status/role/chart/CLI grant mutations remain the existing guarded services and confirmation flows. No replacement grant store or mutation behavior. |
| User details | `/admin/users/[id]`: read account and chart evidence, link canonical grant services and selected-user activity. No personal settings/default editor. |
| Administration Log | `/admin/administration-log`; old `?tab=audit` retained. Typed read union of the existing administrative and AI configuration audit writers; page/filter/keyset pagination. Earlier best-effort coverage stated, no immutable/comprehensive claim. |
| MCP / Client Keys | `/admin/mcp/keys`, existing list/create/revoke APIs. Normalize active-account checks, active target, atomic redacted audit, concurrent revoke idempotency. One-time secret, no hash list; retired audience tier chooser removed because canonical migration090 removed that authority. A disabled account does not automatically invalidate an existing bearer key; lifecycle change requires separate work. |
| System Observatory / Analytics | `/admin/activity`, `/admin/analytics`. Same canonical metering reader as Journey5 with different guards. Portal/My/Selected explicit. Selected-other and portal conversation text suppressed server-side; duplicate authority parameters rejected. Own scope keeps personal derivation. Provider receipts, API estimates, CLI summaries and historical populations stay separate. |
| Older Observatory bookmarks | `/observatory` → active admin `/admin/activity?scope=mine`, regular active user → Journey5 personal Observatory. `/observatory/analytics` and `/observatory/consumption` → equivalent Analytics/personal Consumption. Compatible dates/dimensions retained; personal authority stripped. Other legacy subpages already redirect into these maintained views. No duplicate presentation remains on these three entry routes. |
| Advanced accounting read/write services | Existing `api/admin/observatory/analytics/{cache,cost-arc,cost-per-quality,anomaly,pricing-diff,replay}`, budget-rules/evaluate, metering/manage and reconciliation/history and reconciliation/upload reads/writes plus POST reconciliation route remain unchanged under their current guards/action contracts. Old advanced UI routes already redirected in the verified main; unused drawer components are not removed. New Analytics does not invoke tests/recovery/replay/anomaly, provider invoices or uploads. Old usage-only services are not claimed equivalent to the normalized ledger; any modernized mutation UI is a separate reviewed work order. Quality remains explicitly unavailable. |
| Monthly budget read | `/api/admin/accounting`: active existing monthly rules evaluated via canonical portal ledger over the strict UTC civil month, independent of activity filters. Unsupported pipeline-stage mapping unavailable; daily/weekly rules and alerts still owned by the retained service. No alerts/notifications emitted by the read. |
| Foundation | `/admin/foundation`: separate DB presence, receipts, runtime-declared release identity, configuration and unknown reachability. Replaces empty/healthy inference. No health/storage/build probe triggered. |
| MCP Health | `/admin/mcp/health`: connect readable canonical stored registry/24h measures/session views via new active-admin read adapter. Preserve source/historical grouping; no average of medians or invented time-series. Retired grounding/coverage aggregates explicitly unavailable. Existing internal-token APIs, disconnected dashboard/tool-disable/caveat/threshold component files remain intact; their referenced admin tool-registry/caveats/alert-configs handlers do not exist in the refreshed source and are explicitly deferred; no browser secret bridge or new invocation. Prior route used placeholder tabs and nonexistent calibration URL, not a verified working control path. Calibration links to Learning Review. |
| Query Trace | `/admin/trace` history; existing `/admin/trace/[query_id]`, guarded API/detail/steps preserved. Contextual link from diagnostics; no primary navigation entry. Identifiers remain distinct from personal conversation/turn ids. |
| Asset Register | `/admin/assets`: canonical asset definitions (external six layer names), search/25-row paging, last50 build records; links chart Nirmāṇa for measured counts/readiness/build actions. `/admin/tracker` retained explicitly for legacy active/recent build detail and its old matrix placeholders; no route retired, no build writer added. Earlier fallback/matrix data is not accepted as measured readiness. |
| Programme Record | `/admin/programme`: actual historical Nirmāṇa declarations and provenance, superseded programme labelled; link existing `/admin/nirmana-elevation`, `/cockpit`, `/cockpit/command-center`. Preserve independently owned current campaigns; no invented programmes/campaign advancement. |
| `/audit` / `/performance` | Neither page nor alias exists in the refreshed source. They were legacy prototype labels, not implemented capabilities to delete. No broken links or misleading alias to administrative audit is added. Actual administration log and operational cockpit controls above are retained. |
| Cockpit source / prototype paths | Existing `/cockpit`, command-centre, charts/jobs/SSE/watchdog controls and current retired-section redirect map untouched. No blanket cockpit removal. Prototype `#/cockpit/observatory`, system, tracker, programme and learning labels map to the explicit admin destinations above; use Review Hub mapping, not a guessed application URL. |
| Learning Review | `/admin/learning`: recorded snapshots/outcome groups, stored status/stale flags, chart review links. Existing chart learning/adjudication/follow-up/quarantine handlers retained with chart guards. No operator publish/co-sign control; independent actor/publication protocol remains an explicit prerequisite. |
| Journey5 ownership | Account/profile/security/preferences/personas/connections/four role configurations/exact defaults remain personal and unchanged. Shared layout consumes the actor's same preference provider and signature. Personal endpoint still rejects user override. All admin query caches isolate by authenticated layout actor/role/status; delayed obsolete responses cancelled/discarded. |

## Work orders by page

| Screen | Design and implementation order | Validation / rollback |
|---|---|---|
| Overview | Four blocks and explicit scopes; live request count with loading/unavailable state. | Source component/three widths; source-only rollback. |
| Requests | Retain admission decisions and canonical audit. | Existing mutation tests + full suite; synthetic fixtures only. |
| Users / detail | Retain role/status/account actions; additive read detail and links. | Guard/unit/cache tests; no real-account mutation. |
| Chart Management | Retain canonical owner/grant editor; no second access store. | Existing permission/grant suite; no real grant mutation. |
| AI Access | Retain per-CLI grants, feature gates and host distinction. | Existing eligibility/default suite; cache isolation; no live grant change. |
| Administration Log | Typed/provenance read union, strict filters, microsecond keyset, safe detail. | Injection/secret/cursor tests; live GET; no new writer. |
| MCP / Client Keys | Active boundaries, atomic issue/audit, revoke idempotency, one-time display. | Direct denial/concurrency/transaction tests; no real keys issued/revoked. |
| System Observatory | Shared ledger/filters, populations, labelled units. | Scope/navigation and personal preservation tests; own totals parity live. |
| Analytics | Same scope/details/export; independent monthly read; historical reconciliation/quality caveats. | Calendar/null/unsupported-source tests; live GET; no paid actions. |
| Foundation | Sanitize and connect source evidence; configuration not reachability. | Read-only/unavailable tests + live GET. |
| MCP Health | Connect actual records, preserve populations, unknown retired measures. | Query/schema/source tests + live GET; measured history deferred. |
| Query Trace | Link retained step inspector from contextual history. | Existing trace guard suite + live route; no replay. |
| Asset Register | Canonical names/records/search/paging/chart links; retain tracker detail. | Read-only/count-contract tests + live GET; no rebuild. |
| Programme Record | Historical governed declarations/source links; retain current campaign ownership. | Source/route inventory and live read; no campaign action. |
| Learning Review | Read-only snapshot/outcome sources and chart links. | Stale-context/read-only tests + live GET; no publication. |

All new operational projections are GET-only and private/no-store. No schema migration, engine/workflow/source changes outside scoped portal/adapter work. Rollback is the prior serving image/revision; no data rollback needed for this web-only release. Real credentials, paid provider acceptance and owner design acceptance remain distinct gates.
