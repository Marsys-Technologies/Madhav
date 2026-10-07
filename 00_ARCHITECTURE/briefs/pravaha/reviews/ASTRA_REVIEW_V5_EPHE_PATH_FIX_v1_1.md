VERDICT: ACCEPT

Reviewed both requested diffs at `86e34e62c265856bbf95a449292d2a5f4a345e80`. **No new actionable P1/P2/P3 findings within the steward’s scope.** This does not establish a completed production build.

| Round-1 finding | Disposition | Evidence |
|---|---|---|
| **P1 — Runner test mislabels the anchor blocker** | **Resolved as ruled.** The underlying blocker remains assigned separately. | The test selects `marriage`, explicitly explains the structural unknown-house failure, and requires completed events through `record:marriage:P1`. It no longer requires failure: [test_c47_ephe_real_runner.py:238][runner]. |
| **P2 — Config precedence only affects the returned string** | **Resolved.** | Config/environment disagreement is refused using `realpath` comparison: [ka_gochara_v5.py:510][resolver]. The test exercises refusal through rules/body/manifest entry points and a successful real Swiss calculation: [test_c47_ephe_real_runner.py:98][calculations]. |
| **P2 — One corpus across the build is unbound** | **Resolved under the stipulated cache model.** | Every admitted live substep enters the guard before computation or writes: [ka_gochara_v5.py:787][entry]. The guard checks SHA-256 against the shared pins, subject to the cache limitation below: [ka_gochara_v5.py:476][cache]. |
| **P3 — Empty config silently falls back** | **Resolved.** | Only absent/`None` falls back. Empty/whitespace strings and invalid types raise `EphemerisConfigRefusal`: [ka_gochara_v5.py:510][resolver]. All six supplied invalid-value cases passed. |

**Cache residual:** Yes—a file can be replaced at the same real path with different bytes of identical size and its previous `mtime_ns` restored. The key ignores inode/ctime, so [lines 484–486][cache-key] reuse the previous verification. There is also a check-to-use interval during which a file or symlink could change.

I consider this **acceptable for the explicitly prescribed metadata cache with an immutable corpus during execution**. It is not protection against concurrent or metadata-preserving replacement. An in-memory simulation confirmed the unchanged-metadata cache hit; changing mtime by one nanosecond triggered rehashing and named refusal. The comment saying a replaced file is hashed again has this qualification.

The remaining checks:

- **Before Swiss calls:** I supplied corrupted lunar-file bytes in memory and exercised all **298 default substep keys**, with Swiss calls and connection use trapped. Every key refused first. Dry execution returned without ephemeris resolution, as intended.
- **Cost:** The three files total **2,011,836 bytes**. Locally, with a warm filesystem cache, first verification took approximately **0.8 ms**; cached resolution averaged **0.04 ms** over 1,000 calls. Each file was read once. Subsequent calls still perform path/metadata checks.
- **Pin-agreement test is real:** [test_c47_ephe_real_runner.py:160][agreement] reads the actual Dockerfile and CI file and compares the backend/conftest constants. It passed; separately altering Docker, CI or backend pins in memory made it fail. The current Docker/CI matches are executable `sha256sum` checks.
- **Symlinks and trailing slashes:** Actual Swiss calculations succeeded with `/tmp/se1` and `/private/tmp/se1/` aliases, including extra trailing slashes. Config-only, environment-only and equivalent-directory combinations produced identical ephemeris identities.
- **Default, slices and dry planning:** The 298-step default golden, both slice shapes and connection-free dry planning passed. Across the selected C47/vector/slice tests, **129 directly invoked cases passed**, including all 16 frozen vectors.
- **Locks and generated identities:** Swiss calculation locking remains in [knots.py:157][swiss-lock]; the resolver introduces no Swiss setter. Database lock ordering is unchanged. I recomputed and matched the [implementation lock][implementation-lock], [writer digest][writer-digest], census content hash and [writer-inventory reference][census]. The new pin module is included in the governed evaluation stage. Geometry/window stage digests remain unchanged.

**Not verified:** the two database-backed runner tests, full pytest execution, file-writing fixtures, an actual on-disk replacement attack, completed default/slice builds, Linux/container behavior, concurrent writers, or production registry/grants/timeouts. The runner’s reported later window-P3 failure was not independently reproduced. No database or network was accessed; no files were modified.

[runner]: /private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ephe2/platform/python-sidecar/tests/l3/gochara/test_c47_ephe_real_runner.py:238
[resolver]: /private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ephe2/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:510
[calculations]: /private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ephe2/platform/python-sidecar/tests/l3/gochara/test_c47_ephe_real_runner.py:98
[entry]: /private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ephe2/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:787
[cache]: /private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ephe2/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:476
[cache-key]: /private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ephe2/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:484
[agreement]: /private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ephe2/platform/python-sidecar/tests/l3/gochara/test_c47_ephe_real_runner.py:160
[swiss-lock]: /private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ephe2/platform/python-sidecar/services/gochara_kernel/knots.py:157
[implementation-lock]: /private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ephe2/platform/python-sidecar/services/gochara_kernel/implementation_digest.lock.json:2
[writer-digest]: /private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ephe2/platform/src/generated/nirmana-writer-digests.json:90
[census]: /private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ephe2/platform/src/generated/capability_estate_census.json:22446

