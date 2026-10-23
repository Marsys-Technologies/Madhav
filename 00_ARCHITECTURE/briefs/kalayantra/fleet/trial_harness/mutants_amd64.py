"""Planted reversions for the AMD64-DOCKER claims (SR-T24-AMD64-DOCKER) — one per distinct claim (D-OWNER-TESTS-20261016).  (id, claim, file, old, new); `old` must occur exactly once.
The three claims that live in the repository's `equivalence_record.py` (EQ-16) are listed in M64_EQ with the path relative to `fleet/` (`mutation_check.py` copies only this directory;
run them with `tests/test_equivalence_record.py` against a copy of `fleet/`)."""

M64 = [
    ("AD-1a", "the arch is read from an in-container probe; none / one from outside is refused", "amd64_docker.py",
     'if not isinstance(probe, dict) or probe.get("schema") != PROBE_SCHEMA or probe.get("source") != "in_container":', 'if False:'),
    ("AD-1b", "a probe of another run (nonce) is refused", "amd64_docker.py", 'if probe.get("nonce") != nonce:', 'if False:'),
    ("AD-1c", "a container that does not read x86_64 is not an amd64 run", "amd64_docker.py", 'if probe.get("uname_machine") != "x86_64" or probe.get("platform_machine")', 'if probe.get("platform_machine")'),
    ("AD-2", "G-5 does not use the wall time of an emulated run", "gates.py", 'if isinstance(plat, dict) and plat.get("wall_comparable") is not True:', 'if False:'),
    ("AD-3", "emulation is detected from the engine architecture", "amd64_docker.py", '    emulated = server != "amd64"', '    emulated = False'),
    ("AD-4a", "the slice container is linux/amd64", "amd64_docker.py", '"--platform", "linux/amd64", "--network", f"container:{pg}"', '"--network", f"container:{pg}"'),
    ("AD-4b", "the network is private (internal)", "amd64_docker.py", '["network", "create", "--internal", "--label"', '["network", "create", "--label"'),
    ("AD-4c", "PG runs with locale C", "amd64_docker.py", '"POSTGRES_INITDB_ARGS=--locale=C --encoding=UTF8"', '"POSTGRES_INITDB_ARGS=--encoding=UTF8"'),
    ("AD-4d", "the chart data (L1 export) is mounted read-only", "amd64_docker.py", 'f"{ephe}:{ephe}:ro", "-v", f"{l1_export}:{l1_export}:ro"', 'f"{ephe}:{ephe}:ro", "-v", f"{l1_export}:{l1_export}"'),
    ("AD-4e", "the PG container publishes no port", "amd64_docker.py", '"-e", "POSTGRES_HOST_AUTH_METHOD=trust",', '"-p", "55433:55433", "-e", "POSTGRES_HOST_AUTH_METHOD=trust",'),
    ("AD-4f", "the runtime probe runs inside the container before the slice", "amd64_docker.py",
     'python -I /work/harness/amd64_probe.py --nonce {nonce} --out /work/out/runtime_probe.json; ', ''),
    ("AD-5", "the 4-class slice only", "amd64_docker.py", 'or any(c not in SLICE_CLASSES for c in classes)', 'or False'),
    ("AD-6a", "the pinned corpus must match the Dockerfile's own sha256 checks", "amd64_docker.py", '    if wrong:\n', '    if False:\n'),
    ("AD-6b", "the Dockerfile's sha256 checks are kept in the derived Dockerfile", "amd64_docker.py",
     'checks = [f"    echo \'{h}  /app/ephe/{f}\' | sha256sum -c -" for f, h in sorted(declared.items())]', 'checks = ["    true"]'),
    ("AD-6c", "the ephemeris network fetch is replaced", "amd64_docker.py", 'out = "\\n".join(lines[:i] + new + lines[j + 1:])', 'out = "\\n".join(lines)'),
    ("AD-7a", "everything the run created is removed at the end", "amd64_docker.py", 'if rec.get("status") != "resume":\n            rec["teardown"]', 'if False:\n            rec["teardown"]'),
    ("AD-7b", "containers are removed with their volumes", "amd64_docker.py", 'docker("rm", "-f", "-v", cid, check=False)', 'docker("rm", "-f", cid, check=False)'),
    ("AD-7c", "an image asked for by digest is used by digest or not at all", "amd64_docker.py", ' or docker("image", "inspect", image_digest, check=False).returncode != 0:', ':'),
    ("AD-7d", "one amd64 slice per head", "amd64_docker.py", 'if rec["head"] != head:', 'if False:'),
    ("AD-8a", "the finished run attaches the platform block to its report", "trial_slice.py", 'attach_to_report(out, "platform", rb["platform"])', 'pass'),
    ("AD-8b", "the in-container runtime and the emulation note reach the equivalence stage", "trial_slice.py",
     'extra_inline={"runtime": rb["runtime"], "provenance": {"platform_notes": rb["platform_notes"]}})', 'extra_inline=None)'),
    ("AD-10", "a run is finished from its out dir never while the slice container still runs", "trial_slice.py",
     'if rec["names"]["slice"] in docker("ps", "--format", "{{.Names}}", check=False).stdout.split():', 'if False:'),
    ("AD-9", "run_trial.sh TRIAL_AMD64_DOCKER=1 asks for the container slice", "run_trial.sh", 'if [ "${TRIAL_AMD64_DOCKER:-}" = "1" ]; then\n  aargs', 'if false; then\n  aargs'),
]

M64_EQ = [
    ("EQ16-a", "an arch asserted from outside (no in-container probe reading x86_64) is refused", "equivalence_record.py",
     '    if (not isinstance(probe, dict) or probe.get("source") != "in_container" or probe.get("uname_machine") != "x86_64"\n            or probe.get("sys_platform") != "linux" or rt.get("arch") != QUALIFYING_ARCH):',
     '    if False:'),
    ("EQ16-b", "an emulated run without its emulation note is refused", "equivalence_record.py",
     'if not isinstance(note, dict) or note.get("emulated") is not True or note.get("layer") not in EMULATION_LAYERS:', 'if False:'),
    ("EQ16-c", "the emulation note is provenance: it never moves E4", "equivalence_record.py",
     '"platform": {"vector": eph["platform"], "arch": rt["arch"]}', '"platform": {"vector": eph["platform"], "arch": rt["arch"], "emulated": rt.get("emulated")}'),
]
