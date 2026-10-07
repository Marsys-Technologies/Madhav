VERDICT: REJECT

Reviewed `c8f6ebf5da137c34c8e8a0d344759fef1c93f08a` against both supplied ranges. The exclusion override does **not** introduce a persistence bypass through the current callers. Publication and interrupted-build serving remain incomplete.

**P1 — Publication refusal is not atomic with publication.**

[ledger.py:626](platform/python-sidecar/services/gochara_kernel/ledger.py:626) reads the slice stamp without locking. The eventual UPDATE at [ledger.py:685](platform/python-sidecar/services/gochara_kernel/ledger.py:685) filters only by `manifest_id`; it does not recheck the stamp or candidate status.

Concrete failure:

1. A direct `ledger.publish()` caller checks an ordinary candidate.
2. A concurrent slice build replaces that candidate’s vector through `publish_candidate()` at `ledger.py:555`.
3. The publisher updates the same manifest to `published`, now carrying the slice vector.

I reproduced this interleaving with the actual helper and an in-memory connection. The unchanged slice control refused correctly; the interleaved case returned successfully with `status=published`, `stored_scope=test_slice`. This blocks subsequent full rebuilding through `publish_candidate()`.

The SQL boundary does not repair this: [1240:965](platform/migrations/1240_gochara_window_verification_gate.sql:965) protects already-sealed generations. Publication UPDATE remains granted to the builder at [1216:104](platform/migrations/1216_gochara_contract_builder_grants.sql:104), so direct SQL publication also remains possible.

**Required:** protect the check and transition with the established locks and an atomic predicate/recheck. The unconditional database-level “never publish a slice” guarantee still requires database enforcement. The approved seal flow already holds locks; the direct helper does not.

**P2 — An interrupted slice-to-full rebuild still serves slice coverage without its designation.**

The new reader guard checks only the current publication vector at [register_gochara_contact_ledger.ts:328](platform-mcp/src/tools/retrieval/register_gochara_contact_ledger.ts:328).

The writer replaces that manifest at [ka_gochara_v5.py:803](platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:803), but removes the previous chain only in the later snapshot step at `ka_gochara_v5.py:837`. Those steps commit separately at `asset_runner.py:915`.

Concrete failure: finish a slice, start an ordinary full build, then fail after its manifest commits but before snapshot replacement. The manifest now lacks the slice stamp; the old slice coverage remains. The reader passes its new guard, reads coverage at line 441, and returns `status: "ok"` at line 474.

I reproduced that response using the actual transpiled TypeScript function with mocked transport: old slice coverage was returned with no refusal or slice designation. This demonstrates coverage mislabelling, not v5 contact-row leakage.

**Required:** refuse inconsistent manifest/snapshot/coverage identities, including this durable interrupted state, and read them consistently. A later retry repairing the chain does not protect intervening reads.

**A. Round-2 disposition**

| Item | Disposition |
|---|---|
| P1: direct publication | **Partly resolved.** Sequential `ledger.publish()` refuses slices; the mutation-boundary gaps above remain. |
| P1: connection-free planning CI regression | **Resolved.** Dry-run planning returns the default plan; live planning without a connection refuses at `ka_gochara_v5.py:214`. The previously failing test passed. |
| P2: contact-ledger designation | **Partly resolved.** Intact slice manifests receive `not_computed / test_slice_candidate`; interrupted transitions remain exposed. |
| Interrupted manifest/snapshot boundary | **Partly resolved.** The candidate gate detects inconsistency and retry repairs it. The new regression at `test_c46_slice_round2.py:306` tests full→full horizon replacement, not slice→full serving. |
| Test gaps | **Partly resolved.** Better stamp assertions, trigger coverage and discriminating default control were added. The remaining limitations are below. |

The previously resolved round-1 protections remain intact: whole-chain replacement, marker-bound input expectations, malformed-marker refusal, and preservation of explicit-null default horizons.

**B. Exclusion override and downstream authority**

The new parameters are public Python arguments, **not capability-restricted arguments**. Any importing Python caller can supply an empty or incorrect exclusion sequence; the helpers themselves do not validate a slice marker. Such a caller can change a standalone full-build self-check’s expectations.

However, the current production call graph contains only these explicit overrides:

- Writer inventory self-check: `ka_gochara_v5.py:897`.
- Writer P1 anchor self-check: `ka_gochara_v5.py:1079`.

Both obtain their value through `_slice_excluded_agents()` at line 378: no marker returns `None`; a validated marker returns the default scope’s `("moon",)`. Neither configuration nor marker fields select arbitrary excluded bodies.

The helpers return derived results; they do not persist attestations. The writer explicitly leaves persistence to the separate verifier at `ka_gochara_v5.py:949`.

The verification job calls both helpers **without** the override at [verification_job.py:378](platform/python-sidecar/services/gochara_kernel/verification_job.py:378) and line 413. Its CLI argument construction at `pipeline/orchestrator/verification_job.py:56` exposes no exclusion option. `check_preconditions()` positively refuses either slice indicator at line 180 before verification persistence.

The seal flow does not call or forward these arguments. An honest slice cannot obtain an approvable brief: [seal_brief.py:350](platform/python-sidecar/services/gochara_kernel/seal_brief.py:350) requires current persisted attestations and a clean candidate gate. Approved sealing recomputes that payload before publication at `seal_flow.py:37`. The existing SQL seal scope check also rejects `test_slice` at `1232_gochara_search_moon_scope_domain.sql:108`.

Thus, **no current path from the new argument to persisted verification, an approvable brief, or a seal was found**. The publication and serving failures above are separate boundary defects.

For `excluded_agents=None`, both verifier bodies match the supplied base after mechanically selecting the default branch and removing the added parameter/docstring. The 298-step default plan and labels also match. Frozen-input vector serialization matches with either an absent or null `test_slice`.

Actual cross-commit production digests are necessarily different because implementation source is hashed.

**C. Other reviewers’ findings**

- **X: resolved in source.** Both failing self-check sites now receive the default exclusion under a validated marker. Positive integrated P1 coverage remains incomplete.
- **Y: resolved under migration 595’s enforced contract.** [595:39](platform/supabase/migrations/595_nirmana_frozen_run_manifest.sql:39) makes a non-null manifest and its digest immutable; the writer additionally verifies their current agreement at line 256 and raises for out-of-marker grains at line 725. This is not a universal tamper detector if privileged code bypasses the trigger and rewrites both values coherently.
- **Z: resolved.** Verification refusal is now an explicit `test_slice_candidate` check, independent of vocabulary absence.

**D/E. Dry runs and data integrity**

No production path to the connection-free dry-run exception was found. The runner constructs `ContextSpec(db_conn=conn)` at `asset_runner.py:1119`; `dry_run` defaults to false. A directly constructed dry-run context cannot read a stored marker and therefore lists the default plan, but execution returns before solving or writing at `ka_gochara_v5.py:701`.

I found no additional L1/global-data deletion or legitimate full-build blocker beyond the publication failure above. Replacement remains scoped to the unsealed chart×generation chain.

**F. Tests and generated artifacts**

- **172 offline tests passed**, including the previous planning regression; database/file-dependent cases were deselected.
- Implementation lock, both changed writer digests, census content and source hashes, and golden manifest/runner pins match.
- Golden transport checks passed. Decoded changes concern identities, digests and execution metadata.
- CI includes the new suites. No unrelated substantive changes were found.

Tests remain narrower than full execution proof: the positive P1 test replaces the real anchor verifier with a success spy at [test_c46_slice_round2.py:61](platform/python-sidecar/tests/l3/gochara/test_c46_slice_round2.py:61). The class-A→class-B test compares inventory, coverage and vector state, without building its records/windows. The transition helper likewise does not execute window grains. These tests would miss regressions in those omitted paths.

**Not verified:** database execution, deployed migrations/grants, real-ephemeris slice completion, concurrent PostgreSQL execution, full TypeScript/Vitest execution, live CI, or production dispatch. Database conclusions are source inspection; the two reproductions used in-memory doubles. No files were modified and no database or network access occurred.

