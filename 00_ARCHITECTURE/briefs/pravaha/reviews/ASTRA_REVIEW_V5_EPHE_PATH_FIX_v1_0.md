VERDICT: REJECT

The original missing-`ephe_path` defect is fixed, but the new runner test misdiagnoses a genuine completion blocker, and two claimed path guarantees are not established.

Paths below are relative to `platform/python-sidecar/` unless stated otherwise.

1. **P1 — The new runner test treats a production blocker as an unavoidable fixture failure.**

   [test_c47_ephe_real_runner.py:148][test-runner] attributes the P1 failure to stub L1 data; line 168 explicitly requires that failure.

   However, the selected class is `achievement_recognition` (`test_c47_ephe_real_runner.py:31`). Its signature houses are **always unknown**, regardless of L1 data (`services/gochara_rules/registry.py:107,128`). Consequently, P1 enumeration returns no edges (`services/gochara_kernel/evaluator.py:438–447`), while [ka_gochara_v5.py:1124][writer-p1] still invokes the anchor verifier whenever the anchor-column gate is open. That verifier independently demands transit contacts and rejects their absence (`services/gochara_kernel/record_verifier.py:254–280`).

   **Failure scenario:** a fresh default build, or the all-classes slice, reaches this first class with the intended schema and fails even with production-quality L1. The underlying contradiction predates this diff; the new test incorrectly enshrines it as a fixture limitation.

   I reproduced the contradiction using real pinned ephemeris files and an in-memory store/result facade, without a database. With the same chart fixture, `marriage` produced **572 contacts and 1,538 records**, and passed the actual anchor verifier. Using `marriage` in the existing runner fixture is a cheap way to proceed further. The exclusion handling needs correction; replacing stub L1 does not resolve this particular failure.

2. **P2 — Config precedence is only enforced on the returned string, not on Swiss’s effective directory.**

   [ka_gochara_v5.py:484][resolver] chooses config first. But `services/gochara_kernel/knots.py:166–177` passes it to `swe.set_ephe_path`, which still honors `SE_EPHE_PATH`.

   **Reproduced scenario:** valid config `/tmp/se1`, but `SE_EPHE_PATH` names a nonexistent directory. The resolver accepts `/tmp/se1`; actual Swiss calculations fall back, and `ephemeris_identity` raises `InputDrift`. The new precedence test only asserts the resolver’s string (`test_c47_ephe_real_runner.py:43–45`), so it misses this failure.

   With two valid directories containing different consumed bytes, the independent manifest verifier should reject their disagreement later (`services/gochara_kernel/input_vector_verifier.py:287–296`). That protects against accepting the disagreement, but does not provide the promised precedence or first-substep refusal.

   Enforce the effective-library contract, or refuse incompatible config/environment settings before writing, and test actual calculations.

3. **P2 — Reusing the resolver does not bind one ephemeris corpus across the build.**

   The environment is reread on every call ([ka_gochara_v5.py:484][resolver]). Body writes occur at [ka_gochara_v5.py:799][writer-body], before the manifest binds file digests at line 826. Live-input verification excludes the body phase (lines 784–794).

   **Failure scenario:** an in-process environment change, or a changed directory/symlink target, switches corpus A to B between body substeps or before the manifest. Earlier committed substrate rows came from A; the manifest describes B. The substrate convention records a library-version label, not corpus hashes (`services/gochara_kernel/substrate.py:175–190`), and conflicting existing events retain their old values through `ON CONFLICT … DO NOTHING` (line 429).

   Post-manifest drift checks do not retrospectively establish which files produced earlier substrate rows. Bind and validate the consumed corpus before body computation. An immutable image with stable environment mitigates this residual gap; I did not demonstrate a fully accepted mixed-corpus build.

4. **P3 — An explicitly empty config path silently falls back to the environment.**

   `if configured` at [ka_gochara_v5.py:485][resolver] treats `ephe_path=""` as absent. With a valid environment path, it succeeds rather than refusing the bad supplied value. Distinguish absent/`None` from an explicitly invalid path if the stated “bad config never falls back” contract is intended literally.

The remaining requested checks:

| Check | Result and evidence |
|---|---|
| **All former reads / `None`** | All seven former reads now use the resolver: writer lines **546, 555, 799, 818, 979, 1021, 1159**. Normal live execution cannot pass an unresolved `None` through these paths. Bodies now receive an explicit path, subject to findings 2–3. |
| **Identity stability** | The ephemeris component remains content-based: opened filename → SHA-256, plus library/platform/probe identity (`services/gochara_kernel/input_vector.py:306–321`). I confirmed equal identities for config-only and environment-only references to the same corpus. Directory strings are not included. The **whole vector** appropriately changes because the writer’s implementation digest changes. |
| **First-step refusal / planning** | Default and both slice shapes begin with `rules` (writer line 677); its resolver guard precedes writes (line 749). I checked these shapes without a database. `plan_substeps` does not resolve ephemeris; dry execution returns before resolution (lines 746–748). Connection-free dry planning remains supported. A live plan without a connection already raises `TestSliceRefusal` (lines 216–225). |
| **Required files / pins** | The three filenames match Docker’s SHA-verified corpus (`Dockerfile.pipeline:17–24`) and CI (`.github/workflows/ci.yml:1176–1184`). The writer checks **existence, not pinned content hashes or readability**, before computation. Manifest checks bind actual consumed contents and run consistency/absolute probes; they do not compare every file against Docker’s SHA constants. |
| **Is three sufficient?** | Yes for the currently pinned corpus and domain. It is stricter than actual consumption: the kernel’s probes consume `sepl_18` and `semo_18`, not `seas_18` (`services/gochara_kernel/input_vector.py:245–249`). Different bytes solely in unused `seas_18` therefore do not change the ephemeris identity. The downloaded star/leap-second files are not required by this writer’s calculation path. |
| **Swiss state effects** | The resolver itself does not mutate Swiss state. Downstream calls do set ephemeris/sidereal state and do not restore it (`services/gochara_kernel/knots.py:157–181`). Those operations use the existing shared lock (`panchang_engine/swiss_state.py:20–33,49–55`). No new unguarded setter was found; this does not prove isolation from other writers relying on residual state. |
| **Lock, writer digest, census, goldens** | Recomputed implementation registration, writer source digest, census content digest, and census writer-inventory reference matched. Frozen geometry/window stages were unchanged. All **16 frozen input-vector cases**, registry-preimage and component-change assertions passed. No golden update appeared necessary. The seven-file diff contains the fix, tests/CI wiring and generated digest changes; the frozen orchestrator is untouched. |

No other missing required **config key** was found: the runner supplies `chart_id` (`pipeline/orchestrator/asset_runner.py:1119–1122`); horizon and result policy have defaults (writer lines 418–431 and 832). Complete L1 and the pinned dasha build remain prerequisites.

Deployment configuration is still unproved. The runner fixture supplies a handcrafted registry row with substeps, dependencies and a **7,200-second timeout** (`tests/l3/gochara/_runner_world.py:31–35`), whereas the checked-in seed remains an inactive skeleton (`platform/scripts/seed/asset_registry_seed.ts:2318–2341`). This is not evidence that production is misconfigured, but the test cannot establish its registry, grants or timeout readiness. Docker’s absolute `/app/ephe` setting avoids a production working-directory dependency.

**Verification limits:** I directly exercised seven new non-database tests, the frozen-vector checks, planning/refusal cases, real Swiss path/identity probes, and the P1 geometry/anchor reproduction. I did **not** execute the two database-backed runner tests, the temporary-file-writing test, the author’s “8 of 10 fail when reverted” experiment, a completed slice, Linux/container execution, multiwriter concurrency, or production permissions/timeouts. No database or network was used; no files were modified.

[test-runner]: /private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ephe/platform/python-sidecar/tests/l3/gochara/test_c47_ephe_real_runner.py:148
[writer-p1]: /private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ephe/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:1124
[resolver]: /private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ephe/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:484
[writer-body]: /private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ephe/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:799

