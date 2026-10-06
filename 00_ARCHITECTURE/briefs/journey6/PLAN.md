# Journey 6 — final reconciliation and delivery plan

Version 1.0 · 6 October 2026 · Owner-review recommendation

Prepared for Abhisek. Planning is complete; Journey 6 design, implementation and deployment have not started under this plan. This document does not ratify a new role, tool taxonomy, publication rule or architecture decision. Journey 5 execution authority (CCD-024) remains scoped to Journey 5.

## 1. Outcome and purpose

Journey 5 manages a person's account, AI configuration, preferences, personas and own activity. Journey 6 manages people and access, portal activity, operational diagnosis and the evidence behind assets and learning. They share records and services while retaining separate authority boundaries.

The recommended Journey 6 has one Administration entry, a compact overview and **four logical blocks**. Every one of the 15 existing prototype screens is accounted for. Contextual details remain accessible without becoming additional competing dashboards. Existing operational capabilities and deep links remain available until their replacements demonstrate complete coverage.

The problems this resolves are duplicated activity views with inconsistent accounting, a misleading all-or-nothing AI access control, scattered operations navigation, and prototype claims that exceed the connected implementation. A screen's presence in a prototype or source file does not establish a working capability.

Goals:

- Give the operator a clear route from access decisions to activity, diagnosis and evidence.
- Reuse Journey 5's preferences, AI identity and accounting contracts; prevent duplicate writers and contradictory totals.
- Preserve useful existing capabilities, including less visible operational controls.
- Show measured, missing and unavailable evidence accurately.
- Produce a design and implementation sequence that can be reviewed and released in bounded increments.

Non-goals: replacing Journey 5; adding a second personal Console; inventing new roles; redesigning chart ownership; rebuilding the calculation or learning engines; resuming superseded programmes; changing learning weights or statistical standards; issuing credentials or deploying as part of this planning session.

## 2. Final page map

Use semantic page identities for feedback. Historical Journey 6 review IDs **25–39** currently appear at Hub positions **26–40**, following the Journey 5 board insertion. Preserve the original identity in the feedback register and show current positions as an annotation; do not renumber prior feedback.

| Original ID / current position | Existing screen | Final home and disposition | Required correction or support |
|---|---|---|---|
| 25 / 26 | Administration | Compact overview of the four blocks | Retain the reviewed visual direction. Show actionable requests and measured status; link to each block without copying full dashboards. |
| 26 / 27 | Access Requests | People and access → Requests | Preserve existing admission decisions. Explain resulting role and chart access; pending or disabled accounts cannot gain operational access. |
| 27 / 28 | Users / User Details | People and access → Users | Retain create, username, status, role and existing account-management actions. User details group grants and activity links around the selected person. |
| 28 / 29 | Chart Management | People and access → Chart access | Reuse the existing chart permission service and grant editor. A user view is a projection of the same grants. Chart ownership and permission checks remain canonical. |
| 29 / 30 | AI Access | People and access → AI access | Replace the prototype's single “Enable AI” switch with the implemented per-product CLI grants. Display Console feature availability, provider configuration and host reachability separately. |
| 30 / 31 | Administration Log | People and access → Administration log | Provide a typed, filtered operator audit view with source provenance. Verify mutation coverage before claiming complete or immutable history. |
| 31 / 32 | MCP / Client Keys | People and access → Client keys | Retain the reviewed layout. Use the existing key service, one-time secret reveal, owner association and revoke semantics; enforce active-account checks. |
| 32 / 33 | System Observatory | Activity and AI accounting → Activity | Reuse the canonical metering contract. Explicitly distinguish portal, selected-user and own scope. Separate transport calls, CLI summaries and legacy records. |
| 33 / 34 | Analytics | Activity and AI accounting → Analytics | Group spending, consumption, reconciliation and existing budget views here. Align filter semantics and source coverage; quality metrics remain unavailable until measured. |
| 34 / 35 | System Foundation | System diagnostics → Foundation | Separate configuration, reachability, recorded deployment/migration evidence and measured health. Table or environment-variable presence is insufficient proof. |
| 35 / 36 | MCP Health | System diagnostics → MCP health | Connect actual tool, coverage, audit and session components through server-authorized adapters. Move calibration detail to the learning block while retaining a health summary link. |
| 36 / 37 | Query Trace | System diagnostics → contextual Trace detail | Retain the full operator trace as a contextual detail reached from failures or activity. Personal usage details use Journey 5's safe owned view. |
| 37 / 38 | Asset Register | Assets, programme and learning → Assets | Read canonical assets and build evidence; link to the chart's existing Nirmāṇa workspace. Preserve the single build writer. |
| 38 / 39 | Programme Record | Assets, programme and learning → Programme record | Present governed current and historical programme evidence. Show superseded/frozen states and provenance; remove fictional programme examples from the release design. |
| 39 / 40 | Learning Review | Assets, programme and learning → Learning review | Start with a read-only operator overview and links to existing chart workflows. Publishing remains blocked until authority, independent co-signing and stale-context protection are proven. |

The four blocks contain 6, 2, 3 and 3 screens respectively, plus the overview. Query Trace and user details are contextual pages. A block is a navigation grouping, not a new role or service.

Existing authenticated routes such as `/audit`, `/performance`, `/cockpit`, `/cockpit/command-center` and `/admin/nirmana-elevation` require an explicit capability inventory before any navigation consolidation. Preserve their deep links, permission checks and necessary controls. Superseded programme history must not be presented as an active campaign. No route is retired solely because it is absent from the prototype.

## 3. Journey 5 / Journey 6 ownership and synergy

| Shared concern | Journey 5 owns | Journey 6 owns | Shared contract / rule |
|---|---|---|---|
| Preferences | Actor's appearance, language, fonts and motion | Uses the actor's same preferences | One preference provider. Inspecting another user never changes the operator's preferences. |
| AI configuration | Own connections, provider credentials, four role configurations and exact selected defaults | Eligibility decisions, CLI grants and operational availability | One configuration identity. Grant changes do not silently select a fallback model. Preserve a chosen but unavailable default with a clear reason. |
| Usage | Own calls, connections, conversations, costs and exports | Authorized portal and selected-user views, budgets and reconciliation | One normalized ledger and bounded filter contract; different server guards. |
| People and charts | Own profile and entitled charts | Admission, roles, status and grants | One profile and chart permission service; no parallel grant database or editor logic. |
| Security / keys | Own security controls; any supported own-key view | Existing administrative key issuance and portal key oversight | MCP keys are distinct from provider keys, CLI authentication and account sessions. An own-key view confers no new issuance right. |
| Diagnosis | Safe detail of owned usage | System health and full operator trace | Correlate existing identifiers; do not assume one conversation, query and call have the same identity. |
| Assets / learning | Personal chart workspace, review and follow-up workflows | Cross-chart operational evidence and review overview | Read the same asset, programme and learning records; retain chart-level authority and publication gates. |

**Scope is visible and enforced.** Use “My activity”, “Portal activity” and “Selected user activity” with the selected user's identity shown. Changing Journey 6's selected user is inspection, not impersonation. Personal and operator filter state and caches are keyed by actor and scope; privileged results cannot appear after an account or role switch.

“Open my activity” enters Journey 5 with compatible filters and strips portal-only authority parameters. “Open user activity” stays in Journey 6 under the operator guard. Passing `userId` to a personal route must never unlock another person's records. Journey 5's personal endpoint already rejects that parameter.

Keep route compatibility where useful: `/admin?tab=…` currently hosts several functions, `/admin/mcp/keys` is separate, and `/observatory` currently supports personal and administrative scope. Introduce the final map through a route/alias plan that preserves existing bookmarks and explicit scope. Regular users should reach the canonical Journey 5 personal activity view; operator routes retain the appropriate guarded scope.

## 4. Corrections established by the reconciliation

### Accounting: prevent overlap and contradictory totals

The current System Observatory prototype adds API transport calls and CLI summary records into one “calls” total. Its displayed receipt total and attribution-tree amount also differ without a clear explanation. Journey 5 already distinguishes these populations. Journey 6 must reuse that behavior and explicitly state unit, population, period and coverage for every total.

The existing shared metering query combines attempts and receipts with deduplicated legacy usage. Older operator analytics, summary, budget and export queries still read the older usage table independently. Adapt these views to the canonical normalized read model before claiming agreement. Do not create a second metering ledger or double-write events to satisfy the screens.

- Transport, CLI aggregate and legacy aggregate populations are separately reported; overlapping populations are never summed as calls.
- Use the same date boundaries, channel, purpose, connection, provider/model and population filters across summary, detail and export. Preserve the current bounded range and pagination protections.
- Separate customer activity from validation, administrative tests, evaluation and background work. Probe catalogue entries are not proof of customer usage.
- Identify receipts, estimates, legacy amounts, missing prices and currency. Unknown cost stays unknown. Currency conversion requires an explicit recorded rate.
- Budget accounting has an explicit accounting period; a selected activity window cannot silently redefine a monthly budget.
- Reconciliation states distinguish matched, partial, missing and failed. A missing receipt is not zero spend.
- Cost-per-quality currently reports `quality_probe_wired: false`; release it as unavailable until a real quality source and denominator are connected. Remove the prototype's fictional acceptance percentages.
- Preserve existing receipt import, recomputation, replay and anomaly actions behind their current controls; the first consolidated analytical surface is read-only. Any new mutating workflow needs its own reviewed action contract.

### Access: represent actual authority

Active `super_admin` is the existing operator role; this plan adds no role. Use equivalent authentication and active-profile checks across pages, APIs, details and exports. Current key list/revoke handlers need active-profile guard normalization. Negative direct-request tests are required even when navigation is hidden.

The prototype's all-or-nothing AI access switch does not match the implemented per-CLI grant matrix. Console availability is feature-gated for eligible active users; CLI grants, host reachability and personal provider/model configuration are separate facts. Grant and revoke outcomes must remain auditable and visible without changing personal defaults.

The administration log currently reads a limited administrative history, while AI actions have a separate audit writer and key mutation audit coverage has not been established. Build a typed read adapter over the existing sources, with actor, target, action, time, result and provenance. Close missing mutation coverage once, at the canonical mutation; do not duplicate writes through a second catch-all log. Redact secrets and private provider configuration.

### Diagnostics: connect components and prove health

The shipped MCP health route renders a client with calibration plus four placeholder tabs. A more complete dashboard exists as an unconnected component. The calibration URL used by that client was not found in the checked application route inventory. Available tool/coverage APIs use internal service-token authentication and are unsuitable for direct browser requests.

Resolve route and source wiring explicitly. An active-operator server adapter may call internal services and return a sanitized payload; service credentials never enter the browser. Session and trace links retain the appropriate guards. Existing tool-disable, caveat and threshold controls need a verified action map before consolidation, with no new privilege or automatic invocation.

Tool counts and groups come from the actual descriptor catalogue, including an unmapped group. Names and grouping remain proposed until accepted; hard-coded fictional counts and the prototype's taxonomy are not authoritative. Health charts need labelled time axes, units, legends, actual time buckets and visible missing intervals. A current 24-hour snapshot cannot be drawn as invented historical measurements.

Foundation must separately report configured, reachable, measured and unavailable. Use deployment and migration receipts for those claims. On dependency failure, show unavailable rather than “not built” or a reassuring empty result. Use governed external asset/layer names throughout the operator interface too. Internal layer codes remain implementation identifiers and are not displayed externally; any exception requires a separately ratified decision.

### Assets and learning: preserve provenance and publication boundaries

The asset tracker currently has incomplete projections and can turn query failure into “No builds”. Read canonical asset/build evidence with explicit freshness and failure states. Do not invent a new persistent build status or a second rebuild action. Link to the canonical chart workspace; respect existing orchestration and single-writer boundaries.

Programme records show real governed releases, campaigns, manifests and transitions, including historical and superseded states. Journey 6 does not take ownership of Nirmāṇa, Suvarṇa or Nikāṣa campaign execution.

Learning Review initially aggregates existing evidence and links to chart review, adjudication, follow-up and quarantine flows. Existing chart permission checks remain necessary. The observed co-sign handler can mark publication live under the existing write permission without proving an independent second actor. Therefore an operator “Approve” button cannot be released on the prototype's two-key promise alone. Establish the governed co-sign protocol, actor independence, audit and stale-context rules before publication controls are enabled. Preserve resonance quarantine and prevent review material from affecting weights through an unintended path. Reworking the learning engine or calibration doctrine is outside Journey 6.

## 5. Design and Review Hub work order

After owner acceptance of this plan, use Claude Design against the current portal project, not an archived prototype:

1. Close the page map, shared shell, scope labels and four-block navigation first. Reuse Journey 5's header, preferences and current component vocabulary.
2. Retain the reviewed Administration and Client Keys visual direction. Rework AI Access, activity/analytics population semantics and honest operational states before polishing secondary details.
3. Design all 15 screens, including contextual details, permission-denied, empty, unavailable, loading, partial-evidence and stale-data states. Use clearly marked fictional samples only in the prototype.
4. Cover desktop and narrow widths, keyboard access, readable legends and non-colour status cues. Match the actual menu/control inventory and governed display names.
5. Add a Journey 6 reconciliation board to the same Review Hub. Preserve stable review identities, feedback links and page statuses; attach the plan, per-page disposition, source gaps and revised design links. Do not mark design feedback closed until the revised page answers it.
6. Walk the current organized prototype sequentially, then audit application gaps. Keep Designed, Owner reviewed, Implemented, Tested, Deployed and Live verified as separate states.

Feedback carried forward: F16 and F19–22 (utility placement, overlap and hidden capabilities); F60–68 (asset naming, truthful builds, health charts, tool identity/taxonomy and keys); F82–87 (personal AI placement, real Console, audiences, usage attribution and current Hub discipline). The current file name `FEEDBACK_REGISTER_v1.0.md` contains later revisions; use its recorded content and dates rather than infer version from the filename.

## 6. Requirements and acceptance priorities

**P0 — release blockers**

- All 15 screens and every existing hidden capability have a disposition, canonical source, route and permission rule. No silent deletion and no duplicate grant, configuration, usage or build writer.
- Personal and operator authority are enforced server-side. Missing, disabled and non-operator users fail appropriately on direct requests, detail pages and exports. Account/role switches cannot leak cached privileged data.
- Shared usage views agree for the same population and filters, including the operator inspecting self. Test transport/CLI overlap, legacy deduplication, unknown prices, currency, partial receipts, pagination and boundary dates.
- AI access controls match per-product grants and distinguish configuration from availability. Preserve exact defaults and existing personal role configurations.
- Operational dependencies have real wiring, freshness and unavailable states. Secrets are excluded from browser payloads, logs, prototypes and exports.
- Full trace is operator-only. Safe personal usage detail is bounded to its owner; identifier correlation does not broaden authority.
- Learning publication controls remain gated until the independent co-sign and stale-context protocol is proven. Asset/build mutations retain their current writer and chart permissions.
- Audit coverage supports each released access/key mutation and states its actual limits. A failed action cannot be shown as completed.

**P1 — complete the initial operational journey**

- Four-block overview and navigation, user detail projections, operator activity, aligned analytics, Foundation/MCP health, contextual trace, asset and programme evidence, and read-only Learning Review.
- Filtered/paginated administration log, scope-preserving deep links, compatible old routes and consistent shared preferences.
- Browser evidence at 320, 390 and 1440 widths; no horizontal overflow, readable charts, visible target scope, usable keyboard navigation and loading/error recovery.
- Review Hub traceability from owner feedback through design, source change, verification and release evidence.

**P2 — optional follow-on work**

- New advanced operational actions, longer historical health series, enhanced quality analytics and any learning publication UX beyond currently proven authority.
- These remain separate work orders with measured sources and accepted contracts. They do not justify expanding the first release or fabricating data.

## 7. Execution sequence and completion gates

| Phase | Concrete output | Gate before proceeding |
|---|---|---|
| A. Finalize scope and contracts | Accepted page/capability map; route aliases; authority matrix; metric/filter definitions; canonical source and gap register | Owner accepts this recommendation. Record any cross-cutting decisions through the existing governance process. |
| B. Claude Design and Hub | Shared layout first, then all 15 revised screens and states; Journey 6 review board and feedback closure evidence | Organized current prototype walkthrough and explicit design disposition. No implementation inferred from a prototype. |
| C. People and access | Reused admission/users/chart-grant services; accurate CLI access; key guard normalization; canonical audit coverage | Direct permission and mutation-result tests; retained existing account actions; exact defaults preserved. |
| D. Activity and diagnostics | Shared metering adapter for operator analytics; scope controls; Foundation and MCP wiring; contextual trace | Accounting parity and overlap tests; source/freshness proof; no browser service secrets; inaccessible full trace for ordinary users. |
| E. Assets, programme and learning | Canonical read projections and deep links; honest history; read-only learning overview | Registry/build provenance; superseded records labelled; original chart workflows preserved; publication gate enforced. |
| F. Release and acceptance | Independent reviews, required source checks, controlled deployment and live browser/API verification | Fresh release authorization and exact reviewed source; owner gates honored; verified target, migration receipts if needed, serving revision and runtime behavior. |

Phase C and the read-only portions of D/E can be scheduled after common contracts close; coordination must assign single writers before parallel implementation. Do not promise dates until the source gaps and accepted design are sized. Release access/accounting corrections before optional advanced analytics or publication workflows.

Each implementation work order must name files/modules, existing dependency/campaign boundaries, action authorization, tests, rollback and evidence. If a database change is necessary, reserve a fresh migration number and use the migration review workflow; never edit or reuse the already applied Journey 5 migration 1310. Required release checks include reviewed changes, applicable CI, migration rehearsal/receipts, deploy identity and post-deploy authenticated tests. Existing provider availability or Consultation smoke failures remain separately recorded limitations; this plan does not certify their resolution.

Completion means the operator can perform the supported access decisions, inspect activity without contradictory totals, diagnose an actual problem and trace its evidence, while Journey 5 retains its owned settings and activity. Evidence must demonstrate those behaviors on the serving release. Design approval, passing CI and deployment success are separate milestones.

## 8. Remaining decisions and authority

The recommended four-block structure, route compatibility and initial read-only learning boundary are the final planning proposal. Owner review is needed to accept that scope and the subsequent design/execution campaign. Tool grouping/display changes and any learning publication protocol must use the existing decision and ratification process; this plan does not settle them by implication.

No additional clarification is needed to deliver this plan. Future work must resolve source gaps through evidence rather than asking the owner to choose technical wiring. If publication requires a policy change, bring back a concrete reviewed protocol for the owner's decision. Existing personal permissions, provider credentials and campaign ownership stay authoritative throughout.

## 9. Evidence and verification status

Reconciled against current `origin/main` **b1fe14efad5fe0d34d458322c6b7c0d7ef640149**, the deployed Journey 5 source and all 15 correctly loaded Journey 6 prototype pages. Application trees in the planning checkout match that main snapshot. Browser observations and source references are recorded in [SOURCE_EVIDENCE.md](SOURCE_EVIDENCE.md). Independent review and disposition are recorded in [REVIEW.md](REVIEW.md).

Current Hub statuses remain: Administration and Client Keys reviewed/retained; System Observatory revised/awaiting re-review; the other 12 pages not yet reviewed in the Hub. Prior walkthrough discussion is not substituted for current acceptance. No Journey 6 source change, design mutation, deployment or owner acceptance is claimed by this planning artifact.
