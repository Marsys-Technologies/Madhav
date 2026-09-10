---
artifact: PARIPRASHNA_STREAM_CHARTER_S5
version: "1.0"
status: FROZEN — registered as tracker plan revision 4
date: 2026-08-27
stream_id: S5
stream_name: Security, Privacy & Data Integrity
frozen_by: Session A, Phase A5
---

# Stream charter — S5 (Security, Privacy & Data Integrity)

- **Owner (actor to register):** `lead-s5`
- **Independent verifier:** `verifier`, but per elevation §11.1 **Opus/high specifically** for S1-severity/security-class findings and any gate closure this stream recommends — this whole stream is Opus-led per elevation §11.1's model table.
- **Baseline SHA:** `3686772b7000cf9e1d391b97eccc008ef167b8d0`
- **Deployed revision pin:** `amjis-web` @ `cafa894ee7cfc2e86743bb92625e7faf293aec0a` — **stale behind baseline, missing the B-007/B-008 cockpit-authorization fixes.** This directly matters for YOUR territory (unlike S1–S4): re-check `gcloud run services describe amjis-web --format="value(spec.template.spec.containers[0].image)"` at your own open, and if it is STILL behind `3686772b7000cf9e1d391b97eccc008ef167b8d0`, do not claim a LIVE-rung pass on any cockpit/chart-authorization surface until it catches up — the deploy is blocked by an unrelated Nirmana-campaign preflight failure (PR #1601), not anything in your control; escalate to your Native Surrogate if it's still stale by the time you need a LIVE proof, rather than fabricate one against a stale deployment.
- **Worktree/branch:** fresh worktree off `origin/main` @ baseline SHA, branch `pariprashna/v3-s5-security-privacy`
- **Approved ceiling:** 8h wall-clock; spend by judgment
- **Entry gate and dependencies:** CG-2 CLOSED (`031e03fc-7685-4c17-af34-bba115318246`); P2→P3 RESOLVED (`02d8c469-7ceb-440c-be10-a910cc6bcaa8`)

## Credential status

RESOLVED per A2 — you will need it extensively (every LIVE-rung denial proof in this stream reuses the guest-role `hunQRYVJ5Ec2mQnJnutK7AoQnsO2` principal, scoped only to `1c826d5a`). See `../A2_CREDENTIAL_LANE_OUTCOME_v1_0.md`.

## Test subject

Synthetic chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a`. The native's real chart `482012f1-710e-4a25-994a-93821f5871aa` may be used ONLY as a denial-probe target (status/redirect headers only, per the A2/A4 precedent) — never read its response body, never any destructive action against it under any circumstances.

## Scope (test plan v2.1 §9 complete; J4's enforcement half; J8)

**Primary file territory:** auth/RLS/audit/consent/prediction-lifecycle surfaces — `platform/src/lib/auth/`, `platform/supabase/migrations/` (read-only tracing, no new migrations without Native Surrogate + integrator sign-off per elevation §8.1's fast-track exception), `platform/src/app/api/cockpit/*` (already swept once in A4 — this is your re-verification + the deeper battery, not a fresh discovery pass), consent/audit tables.

**§9 battery, release-blocking (not back-office):**
- Deployed hard-stop corpus for mortality, self-harm, health/mental-health, retraction, predictive sampling — each must demonstrably block/reframe/seal and record the receipt action.
- Question-borne and retrieved-content prompt injection, plan-closure, tool-sequence anomaly, cross-chart exfiltration attempts.
- Object-level authorization, roles/grants, RLS cross-context denial, consent-absent/minor/withdrawal/deletion workflow, disclosure-class restrictions, audit hash-chain / INSERT-only proof.
- Rate and spend limits on both doors, provider data-posture checks, no-leakage canary/mutation checks, same-day credential/session revocation drill.
- Crash-consistent persistence, replay, semantic-hash parity, schema compatibility, immutable provenance, prediction immutability, restore drill (within your authority — do not attempt a real restore against production without Native Surrogate + integrator sign-off; a rehearsed/scoped drill only).

**Named live findings you inherit and must re-verify, not re-discover:**
- **E-001** (PPR-26): the app's serving credential historically held DELETE/UPDATE/TRUNCATE on `audit_log` — re-verify current state.
- **E-002 / E-015** (P2-B-002): `chart_facts`/`chart_dashas` carry zero RLS objects, and Postgres's table-owner bypass would defeat a policy-only fix regardless — this is YOUR highest-priority inherited lead. A2/A4 already produced: a full risk analysis (rejecting a live fix as too large for a single session — 162 files, zero production callers of the needed session-context plumbing), a merged test-only "narrowed proof" (`../B002_NARROWED_PROOF_v1_0.md`, PR #1598) documenting the gap without touching production, and an 8-step ordered remediation plan. **Do not restart this analysis from zero** — read `../B002_NARROWED_PROOF_v1_0.md` first, then decide whether S5's own session (with more runway than A4 had) can safely execute the next step of that plan, or whether it remains appropriately out of scope for this campaign wave too.
- **B-001/B-007/B-008** (all CLOSED in A4, PRs #1597/#1602/#1603): chart-level and cockpit-wide authorization fixes. **Re-verify these LIVE once the deployed revision catches up** (see the pin note above) — A4's own deployed re-proof for B-007/B-008 was blocked by the Nirmana deploy issue; if it's still blocked when you open, this LIVE re-proof is your first S5 action, not a re-derivation of the fix itself.
- **V3-E-010 / V3-E-011** (`../EDIR_V3_REGISTER_v1_0.md`): two more confirmed chart_id-ownership gaps (`build/rebuild*`, `assets/[chart_id]/[asset_key]`) plus a ~30-route systemic candidate list from the SAME defect family (no per-route ownership check) that A4 explicitly bounded out of its own scope and filed here as **your highest-priority lead**. Triage every candidate route individually — fixed, or confirmed-safe-with-a-cited-reason — do not re-state the count as if triage were completion.
- **V3-E-007** (`nirmana` page metadata leak, unauthenticated `subject_name` in `generateMetadata`) and **V3-E-008** (share-slug rate-limiting, low priority) — both filed here in A4, still open.

**Journey J4 — enforcement half only** (elevation crosswalk splits J4: S3 owns the language/quality half, you own enforcement): does the hard-stop actually fire on the live path, is the receipt recorded, is the block/reframe/seal action real and not merely claimed.

**Journey J8 (prediction lifecycle):** identify a prediction, log/review it, resolve it including "can't tell," verify its state is visible and reversible ONLY via the defined lifecycle (test plan §5.2 item 8) — integrity angle specifically (S2 may also touch this journey's UI-quality half; refer if you find a UI-only issue with no integrity implication).

Freeze your denominator from the enumerated §9 battery items + the named inherited leads + J4-enforcement + J8, before executing.

## Evidence rungs required

This stream's proof law is the strictest of the six: object-level authorization and RLS claims specifically require LIVE-rung proof (a real request against the deployed service with a real denial), matching the exact evidentiary bar A4 set for B-001/B-007/B-008 — a STATIC code-read alone never closes a security finding in this stream. Independent verification by Opus/high is mandatory before any S5 gate-closure recommendation.

## EDIR_V3 seeds

`../EDIR_V3_REGISTER_v1_0.md` — this was YOUR register's primary customer stream pre-split; V3-E-007, V3-E-008, V3-E-010, V3-E-011 were explicitly addressed to you and stay there.

**Superseded 2026-08-29 (A5 split):** the shared register's §4 stopped being a live append point — six streams appending there concurrently was producing repeated merge conflicts (see the index's own §4a for the full history). File all NEW S5 findings in `../EDIR_V3_REGISTER_S5_v1_0.md` as `S5-V3-E-0NN` (next id: check that file's frontmatter `id_convention`). S5's pre-split contributions (E-001, V3-E-017..020, V3-E-022, plus its own convergence note and LIVE-rung evidence log) stay in `../EDIR_V3_REGISTER_ARCHIVE_PRECONVERGENCE_v1_0.md`.

## Posture

Adversarial; Opus-led (elevation §11.1 — S5's own session recommended on Opus, not just its verifier). Independence law is non-negotiable here: finder ≠ fixer ≠ verifier, always separate subagent instances, for every single finding — this is the stream where that discipline matters most.
