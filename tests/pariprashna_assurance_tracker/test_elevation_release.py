import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TRACKER = Path(__file__).parents[2] / "00_ARCHITECTURE/briefs/pariprashna_assurance/tracker"
sys.path.insert(0, str(TRACKER))
from elevation_release import SHADOW_RELEASE_FILES, attest_shadow_release, assert_shadow_release_attestation  # noqa: E402
from service import CANONICAL_MADHAV_ORIGIN  # noqa: E402


class ElevationReleaseTests(unittest.TestCase):
    @staticmethod
    def _git(repo: Path, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
        return result.stdout.strip()

    def _fixture(self, root: Path) -> tuple[Path, Path, str, Path]:
        source = root / "source"; source.mkdir()
        self._git(source, "init", "-b", "main")
        self._git(source, "config", "user.email", "test@example.invalid")
        self._git(source, "config", "user.name", "Tracker Test")
        tracker = source / "00_ARCHITECTURE/briefs/pariprashna_assurance/tracker"; tracker.mkdir(parents=True)
        for name in SHADOW_RELEASE_FILES:
            (tracker / name).write_text(f"approved:{name}\n")
        self._git(source, "add", "00_ARCHITECTURE")
        self._git(source, "commit", "-m", "approved shadow-sync release")
        source_sha = self._git(source, "rev-parse", "HEAD")
        remote = root / "origin.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True, text=True)
        self._git(source, "remote", "add", "origin", str(remote))
        self._git(source, "push", "-u", "origin", "main")
        self._git(source, "remote", "set-url", "origin", CANONICAL_MADHAV_ORIGIN)
        release_parent = root / "release-parent"; release_parent.mkdir()
        release = release_parent / "release"; release.mkdir()
        for name in SHADOW_RELEASE_FILES:
            (release / name).write_bytes((tracker / name).read_bytes())
        return source, release, source_sha, remote

    def _fresh_remote(self, source_sha: str, local_remote: Path):
        real_run = subprocess.run

        def fresh_remote(command, *args, **kwargs):
            if "ls-remote" in command and CANONICAL_MADHAV_ORIGIN in command:
                return subprocess.CompletedProcess(command, 0, f"{source_sha}\trefs/heads/main\n", "")
            if "fetch" in command and CANONICAL_MADHAV_ORIGIN in command:
                bare = command[command.index("-C") + 1]
                return real_run(["git", "-C", bare, "fetch", "--quiet", str(local_remote), "refs/heads/main:refs/heads/verified-origin-main"], check=False, capture_output=True, text=True)
            return real_run(command, *args, **kwargs)
        return fresh_remote

    def test_shadow_release_attests_and_verifies_a_genuinely_merged_immutable_source(self):
        with tempfile.TemporaryDirectory() as root:
            source, release, source_sha, local_remote = self._fixture(Path(root))
            with patch("service.subprocess.run", side_effect=self._fresh_remote(source_sha, local_remote)):
                manifest = attest_shadow_release(release, source_sha, source)
            self.assertEqual(manifest.stat().st_mode & 0o777, 0o444)
            canonical_release = assert_shadow_release_attestation(release, source_sha)
            self.assertEqual(canonical_release.stat().st_mode & 0o777, 0o555)
            for name in SHADOW_RELEASE_FILES:
                self.assertEqual((canonical_release / name).stat().st_mode & 0o777, 0o444)

    def test_shadow_release_rejects_tampered_content_and_unmerged_source(self):
        with tempfile.TemporaryDirectory() as root:
            source, release, source_sha, local_remote = self._fixture(Path(root))
            (release / "elevation_worker.py").write_text("tampered\n")
            with patch("service.subprocess.run", side_effect=self._fresh_remote(source_sha, local_remote)):
                with self.assertRaises(ValueError) as tampered:
                    attest_shadow_release(release, source_sha, source)
                self.assertIn("does not match", str(tampered.exception))
                (release / "elevation_worker.py").write_bytes((source / "00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/elevation_worker.py").read_bytes())
                (source / "00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/elevation.py").write_text("unmerged change\n")
                self._git(source, "add", "00_ARCHITECTURE")
                self._git(source, "commit", "-m", "unmerged")
                unmerged_sha = self._git(source, "rev-parse", "HEAD")
                with self.assertRaises(ValueError) as unmerged:
                    attest_shadow_release(release, unmerged_sha, source)
                self.assertIn("not an immutable commit", str(unmerged.exception))

    def test_shadow_release_tree_must_be_exactly_the_shadow_worker_files(self):
        with tempfile.TemporaryDirectory() as root:
            source, release, source_sha, local_remote = self._fixture(Path(root))
            (release / "server.py").write_text("must not be present in a shadow-sync release\n")
            with patch("service.subprocess.run", side_effect=self._fresh_remote(source_sha, local_remote)):
                with self.assertRaises(ValueError) as extra_file:
                    attest_shadow_release(release, source_sha, source)
                self.assertIn("exact attested shadow-sync tree", str(extra_file.exception))


if __name__ == "__main__":
    unittest.main()
